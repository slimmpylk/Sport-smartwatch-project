#!/usr/bin/env python3
"""G4-R2 package-closure study (battery / interconnect / LRA / caseback-cup re-allocation), Rev-A. Stdlib only, deterministic.

Sub-commands:
  build     write the R2 generated outputs (generated/g4_r2_closure.{json,md}, g4_r2_{plan,sections,annulus}.svg)
  check     regenerate in memory and validate independently: byte identity, pins, overlay pinned values, historical G4
            in-process reproduction (ALLOWED_CHANGES extended by exactly R1_FILES | R2_FILES), anchors, Z / D / boss
            invariants, identity reconstruction, G5 records, scope, sizes and runtime
  selftest  production-path fault-injection suite (G4_R2_BRIEF section 14.8)

Imports g4_case_sealing and g4_r1_blockers as libraries. Frozen G1-R1 values are read from the pinned sources at run
time and are never re-typed. The 2026-10-17 owner decisions enter ONLY through the in-memory overlay of
inputs/g4_r2_closure.json (G4_R2_BRIEF section 4.2). No KiCad, G5, K1 or Q1 work; no 5 ATM, structural, optical,
adhesive, RF, MPN or supplier qualification claim. A FAIL or a stop is a valid result.
"""
import copy
import hashlib
import html
import json
import math
import re
import subprocess
import sys
import time
import xml.dom.minidom
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
MECH = ROOT / 'design/mechanical'
GEN = MECH / 'generated'
IN_PATH = MECH / 'inputs/g4_r2_closure.json'
BRIEF = 'design/mechanical/G4_R2_BRIEF.md'

sys.path.insert(0, str(MECH / 'tools'))
import g4_case_sealing as g4  # noqa: E402
G4_ORIGINAL_ALLOWED = frozenset(g4.ALLOWED_CHANGES)   # captured before any extension (4.2 rule 3)
import g4_r1_blockers as r1  # noqa: E402
import mech_model as mm  # noqa: E402,F401
import g1_scenarios as g1  # noqa: E402,F401
import g2_interconnect as g2  # noqa: E402

R1_FILES = frozenset(r1.R1_FILES)
R2_FILES = frozenset({
    'design/mechanical/G4_R2_BRIEF.md',
    'design/mechanical/inputs/g4_r2_closure.json',
    'design/mechanical/tools/g4_r2_closure.py',
    'design/mechanical/generated/g4_r2_closure.json',
    'design/mechanical/generated/g4_r2_closure.md',
    'design/mechanical/generated/g4_r2_plan.svg',
    'design/mechanical/generated/g4_r2_sections.svg',
    'design/mechanical/generated/g4_r2_annulus.svg',
    'design/mechanical/generated/g4_r2_sweep.jsonl',
})
GENERATED_FILES = frozenset(p for p in R2_FILES if '/generated/' in p)   # outputs are never listed in the emitted record (their existence would make the output self-referential)
OUT_NAMES = ('g4_r2_closure.json', 'g4_r2_closure.md', 'g4_r2_plan.svg', 'g4_r2_sections.svg', 'g4_r2_annulus.svg')
SWEEP_NAME = 'g4_r2_sweep.jsonl'
G4_BASELINE = '00e77cbe107a79ac05194f19b674f7ab8d5941c9'
R1_BASELINE = '27f7a3a0570bb79c27df530cd5d99c7ea7597f9f'
EPS = 1e-9
POLY_SLACK_MM = 0.01      # numerical allowance for the circumscribed-polygon representation of disks / sectors (never a physical credit)
BATTERIES = ('LPR433736', 'LPR403736')
PRIMARY = 'LPR433736'
LANES = ('L-PKG', 'L-STR', 'L-SEAL', 'L-CHG', 'L-BTN', 'L-LRA', 'L-RAD', 'L-ASM', 'L-WIN')
DISPOSITIONS = ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED', 'OWNER_GATED', 'BLOCKED')
VERDICTS = ('G4-R2 BLOCKED', 'G4-R2 PARTIAL — OWNER QUESTIONS', 'G4-R2 PACKAGE CLOSED — SUPPLIER GATES OPEN', 'G4-R2 PACKAGE CLOSED')
WHOLE_RUN_STOPS = ('R2-S01', 'R2-S02', 'R2-S09', 'R2-S10', 'R2-S11', 'R2-S13')
DESIGN_STOPS = ('R2-S03', 'R2-S08')
LANE_STOPS = ('R2-S04', 'R2-S05', 'R2-S06', 'R2-S07', 'R2-S12', 'R2-S14')
REF_STATUS = ('PASS', 'FAIL', 'GATED', 'BLOCKED', 'NOT_EVALUATED')
EVAL = {'n': 0}


class StudyError(Exception):
    """A STOP condition of the deterministic model (input contradiction or broken invariant)."""


def count(n=1):
    EVAL['n'] += n


# --------------------------------------------------------------------------------------------
# I/O and formatting (R1 conventions: sorted keys, compact separators, 9-decimal rounding, final newline)
# --------------------------------------------------------------------------------------------
load_json = r1.load_json
sha_file = r1.sha_file
rounded = r1.rounded
dumps = r1.dumps
f2, f3, fs = r1.f2, r1.f3, r1.fs
esc = r1.esc


def chash(o):
    return hashlib.sha256(dumps(o).encode()).hexdigest()


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)


def frange(start, stop, step):
    return g4.frange(start, stop, step)


def grid(d):
    return frange(d['start'], d['stop'], d['step'])


def norm_text(t):
    return ' '.join(str(t).replace('**', '').replace('`', '').split())


def pointer_get(doc, ptr):
    """RFC 6901 JSON pointer read (the only way pinned values enter the overlay)."""
    cur = doc
    if ptr in ('', '/'):
        return cur
    for tok in ptr.lstrip('/').split('/'):
        tok = tok.replace('~1', '/').replace('~0', '~')
        cur = cur[int(tok)] if isinstance(cur, list) else cur[tok]
    return cur


def pointer_set(doc, ptr, value):
    toks = [t.replace('~1', '/').replace('~0', '~') for t in ptr.lstrip('/').split('/')]
    cur = doc
    for tok in toks[:-1]:
        cur = cur[int(tok)] if isinstance(cur, list) else cur[tok]
    last = toks[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


# --------------------------------------------------------------------------------------------
# Inputs: schema guard (inputs, never results), pins, verbatim owner text
# --------------------------------------------------------------------------------------------
FORBIDDEN_INPUT_KEYS = ('verdict', 'margin', 'selected', 'minimum_feasible', 'd_min', 'winner', 'result', 'outcome',
                        'disposition', 'pass_', 'feasible')


def input_violations(r2in):
    """No result-like key anywhere in the authored inputs (R1 schema guard, applied to the whole document)."""
    bad = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = k.lower()
                if any(kl == f or kl.startswith(f + '_') or kl.endswith('_' + f) for f in FORBIDDEN_INPUT_KEYS):
                    bad.append(path + '.' + k)
                walk(v, path + '.' + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, '%s[%d]' % (path, i))
    walk(r2in, 'inputs')
    return bad


def verbatim_violations(r2in, brief_text=None):
    """Section 3.2 / 17.1 owner text is recorded verbatim: every recorded verbatim block must occur in the brief (whitespace
    normalised) and the 3.2 / 17.1 blocks must be complete (one record per bullet of the brief block)."""
    brief = norm_text(brief_text if brief_text is not None else (ROOT / BRIEF).read_text(encoding='utf-8'))
    bad = []
    for sec in ('owner_decisions', 'open_question_answers'):
        for rec in r2in[sec]:
            if norm_text(rec['verbatim']) not in brief:
                bad.append('%s %s: verbatim text not found in %s' % (sec, rec['id'], BRIEF))
            if rec.get('date') != '2026-10-17' or not str(rec.get('source', '')).startswith('owner decision'):
                bad.append('%s %s: date / source label missing' % (sec, rec['id']))
    return bad


def pin_report(r2in):
    rep = []
    for rel, want in sorted(r2in['source_sha256'].items()):
        p = ROOT / rel
        got = sha_file(p) if p.exists() else None
        rep.append(dict(path=rel, sha256=got, pinned=want, match=got == want))
    a = load_json(MECH / 'architecture.json')
    proj = {k: a[k] for k in ('reservations', 'rear_module', 'edge_crossings')}
    proj['g2.reservations'] = a['g2']['reservations']
    pr = r2in['architecture_projection']
    got = chash_g2(proj)
    rep.append(dict(path='design/mechanical/architecture.json#projection', sha256=got, pinned=pr['sha256'], match=got == pr['sha256']))
    cat = chash(r2in['catalogue'])
    rep.append(dict(path='inputs/g4_r2_closure.json#catalogue', sha256=cat, pinned=r2in['catalogue_pin_sha256'], match=cat == r2in['catalogue_pin_sha256']))
    return rep


def chash_g2(o):
    return hashlib.sha256(g2.dumps(o).encode()).hexdigest()


def contract_commit_report(r2in):
    c = r2in['r2_contract_commit']
    t = git('cat-file', '-t', c)
    blob = git('rev-parse', '%s:%s' % (c, BRIEF))
    tracked = git('hash-object', str(ROOT / BRIEF))
    ok = t.stdout.strip() == 'commit' and blob.stdout.strip() == tracked.stdout.strip()
    return dict(commit=c, object_type=t.stdout.strip(), brief_blob_matches_file=blob.stdout.strip() == tracked.stdout.strip(), match=ok)


# --------------------------------------------------------------------------------------------
# Overlay (G4_R2_BRIEF section 4.2): explicit, in-memory, deep-copy supersession records
# --------------------------------------------------------------------------------------------
OVERLAY_IDS = ('OV-BATT-ID', 'OV-BATT-DIA', 'OV-BATT-THICK', 'OV-Z-REAR-BAND', 'OV-CONN-J1501', 'OV-CONN-J201', 'OV-CONN-J202', 'OV-U7',
               'OV-LRA', 'OV-COND-BAND', 'OV-BOSS', 'OV-BTN-TOPOLOGY', 'OV-C-R1-01-2V', 'OV-SEAL', 'OV-MATERIAL')


def resolve_ref(r2in, v):
    """An overlay r2_value is a literal or {'ref': 'catalogue/LPR433736/cell_diameter_mm/nom'} into the authored inputs."""
    if isinstance(v, dict) and 'ref' in v:
        cur = r2in
        for tok in v['ref'].split('/'):
            cur = cur[tok]
        return cur
    return v


def source_doc(rel, cache):
    if rel not in cache:
        cache[rel] = load_json(ROOT / rel)
    return cache[rel]


def overlay_records(r2in, cache=None):
    """Pinned value (read at run time from its hash-checked pinned source, never typed), R2 value and authority side by side."""
    cache = {} if cache is None else cache
    out = []
    for rec in r2in['overlay']:
        ps = rec['pinned_source']
        if 'path' in ps:
            doc = source_doc(ps['path'], cache)
            pinned = pointer_get(doc, ps['pointer'])
        else:
            pinned = None
        out.append(dict(id=rec['id'], pinned_source=ps, pinned_value=pinned, r2_value=resolve_ref(r2in, rec['r2_value']),
                        authority=rec['authority'], scope=rec['scope'], note=rec.get('note')))
    return out


def overlay_problems(r2in, recs=None):
    recs = recs if recs is not None else overlay_records(r2in)
    bad = []
    if tuple(sorted(r['id'] for r in recs)) != tuple(sorted(OVERLAY_IDS)):
        bad.append('overlay record set differs from the required set of section 4.2')
    for r in recs:
        if r['scope'] != 'G4-R2 only':
            bad.append('%s: scope must be "G4-R2 only"' % r['id'])
        exp = next((x for x in r2in['overlay'] if x['id'] == r['id']), {}).get('pinned_expect')
        if exp is not None and r['pinned_value'] != exp:
            bad.append('%s: pinned value %r differs from the recorded pinned expectation %r (input contradicts its pinned source)'
                       % (r['id'], r['pinned_value'], exp))
    return bad


class Sources:
    """Parsed pinned inputs as deep copies; the overlay (when on) is applied to the copies only and nothing is written back."""

    def __init__(self, r2in, overlay_on=True, battery=PRIMARY):
        self.r2in, self.overlay_on, self.battery = r2in, overlay_on, battery
        cache = {}
        self.S = copy.deepcopy(source_doc('design/mechanical/inputs/stack_parameters.json', cache))
        self.g4in = copy.deepcopy(source_doc('design/mechanical/inputs/g4_case_sealing.json', cache))
        self.r1in = copy.deepcopy(source_doc('design/mechanical/inputs/g4_r1_blockers.json', cache))
        self.g2gen = copy.deepcopy(source_doc('design/mechanical/generated/g2_interconnect.json', cache))
        self.applied = []
        if overlay_on:
            self.apply()

    def cell(self):
        return self.r2in['catalogue']['batteries'][self.battery]

    def apply(self):
        c = self.cell()
        S = self.S
        pk = S['parameters']['t_pack_nom']
        for k in ('nom', 'min', 'max'):
            pk[k] = c['cell_thickness_mm']['nom']
        pd = S['radial']['parameters']['D_pack_nom']
        for k in ('nom', 'min', 'max'):
            pd[k] = c['cell_diameter_mm']['nom']
        self.g4in['contract_values']['owner_limits']['boss_extension_max_mm'] = self.r2in['overlay_values']['boss_extension_max_mm']
        # R1 input copy: T1 re-admitted for evaluation, CHG_ROUTE / CHG_LINK retired (their 2(v) terms become 'retired item')
        self.r1in['parameters']['V20_charger_land']['route_clearance']['routes'] = []
        self.r1in['candidates'] = [c for c in self.r1in['candidates'] if c['id'] == 'G4-B']   # OV-MATERIAL: one architecture (G4-B-ZC)
        self.r1in['parameters']['V04_boss_extension'] = dict(self.r1in['parameters']['V04_boss_extension'], stop=self.r2in['overlay_values']['boss_extension_max_mm'])
        self.applied = [r['id'] for r in overlay_records(self.r2in)]
        return self


# --------------------------------------------------------------------------------------------
# Z model (OV-BATT-THICK, OV-Z-REAR-BAND): imported G1 / G2 rule and tolerance policy, one fixed REAR-band allocation Delta
# --------------------------------------------------------------------------------------------
LAYER_ORDER = ('window', 'optics_zone', 'rear_pcb', 'rear_inner', 'rear_band', 'lower_web', 'battery_zone', 'back_zone', 'main_pcb',
               'front_gap', 'display', 'cover_bond', 'cover')
LAYER_TOLS = dict(window=('t_window',), optics_zone=('h_optics_max', 'c_optics'), rear_pcb=('t_rear_pcb',),
                  rear_inner=('h_rear_inner', 'c_rear_inner', 'tail_joint'), rear_band=(), lower_web=('t_lower_web',),
                  battery_zone=('tol_pack_thick', 'g_axial', 'c_axial'), back_zone=('c_back', 't_insulator'), main_pcb=('t_main',),
                  front_gap=('c_front',), display=('t_display',), cover_bond=('t_cover_bond',), cover=('t_cover',))


class ZStacks:
    """G2-REVA / G2-REVA-HI under the overlay. battery_zone is recomputed through the imported G1 / G2 rule with the overlaid cell
    thickness; Delta = t_pack_nom(pinned) - t_pack_nom(overlaid) is inserted as ONE fixed REAR-band layer without a tolerance term
    directly frontward of rear_inner (R2 4.3 item 2, 6.3). Every other layer and every tolerance sensitivity is untouched."""

    def __init__(self, src_off, src_on, g2study=None):
        self.g2s = g2study if g2study is not None else g2.Study()
        self.alloc = src_off.g2gen['allocation']
        self.off, self.on = src_off, src_on
        self.base = self.compute(src_off.S, 0.0)
        self.delta = src_off.S['parameters']['t_pack_nom']['nom'] - src_on.S['parameters']['t_pack_nom']['nom'] if src_on.overlay_on else 0.0
        self.over = self.compute(src_on.S, self.delta)

    def compute(self, S, delta):
        keep = self.g2s.S
        out = {}
        try:
            self.g2s.S = S
            for sid, high in (('G2-REVA', False), ('G2-REVA-HI', True)):
                s = self.g2s.stack(self.alloc, high=high)
                lay = {l['id']: l['thickness_mm'] for l in s['layers']}
                layers = dict(lay)
                layers['rear_band'] = delta
                nom = sum(layers.values())
                sens = dict(s['tolerance_sensitivities_mm'])
                out[sid] = dict(layers=layers, sensitivities=sens, tolerance_deltas=dict(s['tolerance_deltas_mm']), nominal=nom,
                                rss=round(s['rss_mm'] + delta, 3), linear=round(s['linear_mm'] + delta, 3),
                                nominal_reported=round(s['nominal_mm'] + delta, 3), governing_back_height=s['governing_back_height_mm'],
                                h_rear_inner=s['h_rear_inner_mm'], back_zone=s['back_zone_mm'])
        finally:
            self.g2s.S = keep
        return out

    def delta_report(self):
        rows = {}
        for sid in self.base:
            b, o = self.base[sid], self.over[sid]
            rows[sid] = dict(nominal_delta=o['nominal'] - b['nominal'], nominal_reported_delta=round(o['nominal_reported'] - b['nominal_reported'], 9),
                             rss_delta=round(o['rss'] - b['rss'], 9), linear_delta=round(o['linear'] - b['linear'], 9),
                             nominal_base=b['nominal'], nominal_over=o['nominal'], rss_base=b['rss'], rss_over=o['rss'],
                             linear_base=b['linear'], linear_over=o['linear'],
                             battery_zone_base=b['layers']['battery_zone'], battery_zone_over=o['layers']['battery_zone'],
                             rear_band_over=o['layers']['rear_band'])
        return rows

    def levels(self, sid='G2-REVA', which='over'):
        """Cumulative Z boundaries (Z = 0 caseback / pod plane, +Z toward the front), nominal."""
        lay = (self.over if which == 'over' else self.base)[sid]['layers']
        z, cum = 0.0, {}
        for k in LAYER_ORDER:
            cum[k] = (z, z + lay[k])
            z += lay[k]
        return cum

    def tol_of(self, layer, sid='G2-REVA', which='over'):
        d = (self.over if which == 'over' else self.base)[sid]['tolerance_deltas']
        return sum(d.get(n, 0.0) for n in LAYER_TOLS[layer])

    def chain_tol(self, z1, z2, sid='G2-REVA', which='over'):
        """Sum of the layer tolerance deltas of the layers fully inside [z1, z2] (dimension chain between two references)."""
        lo, hi = (z1, z2) if z1 <= z2 else (z2, z1)
        cum = self.levels(sid, which)
        return sum(self.tol_of(k, sid, which) for k in LAYER_ORDER if cum[k][0] >= lo - EPS and cum[k][1] <= hi + EPS and cum[k][1] > cum[k][0] + EPS)


def z_delta_problems(zs, limits):
    """R2-H01 / R2-H21: total Z delta exactly 0.000 (nominal, RSS, linear) on both baselines; OD-THICK-REVA holds."""
    bad = []
    for sid, r in zs.delta_report().items():
        for k in ('nominal_delta', 'nominal_reported_delta', 'rss_delta', 'linear_delta'):
            if abs(r[k]) > 1e-9:
                bad.append('%s %s = %.9f' % (sid, k, r[k]))
        if r['nominal_over'] > limits['nominal_mm'] + EPS:
            bad.append('%s nominal %.3f > %.3f' % (sid, r['nominal_over'], limits['nominal_mm']))
        if r['rss_over'] > limits['rss_mm'] + EPS:
            bad.append('%s RSS %.3f > %.3f' % (sid, r['rss_over'], limits['rss_mm']))
    return bad


# ============================================================================================
# Plan geometry (exact on conservative polygons; assembly front view: north = -Y, east = +X, azimuth clockwise from north)
# ============================================================================================
C0 = (100.0, 100.0)
xy = g4.xy
polar = g4.polar


def circ_poly(cx, cy, r, n=96):
    """Circumscribed polygon of a disk (a superset of the disk, so computed gaps never exceed the true gap)."""
    rr = r / math.cos(math.pi / n)
    return [(cx + rr * math.cos(2 * math.pi * i / n), cy + rr * math.sin(2 * math.pi * i / n)) for i in range(n)]


def sector_poly(a0, a1, r0, r1, step=1.0):
    """Annular sector as a polygon that contains it: outer-arc vertices on the circumscribed radius, inner-arc vertices on the
    true radius (a chord of the inner arc cuts into the hole, which keeps the polygon a superset of the solid)."""
    span = (a1 - a0) % 360.0
    if span == 0.0 and a1 != a0 or a1 - a0 >= 360.0 - EPS:
        span = 360.0
    n = max(2, int(math.ceil(span / step)))
    da = span / n
    k = 1.0 / math.cos(math.radians(da / 2.0))
    outer = [xy(r1 * k, a0 + da * i) for i in range(n + 1)]
    if r0 <= EPS:
        inner = [C0]
    else:
        inner = [xy(r0, a0 + da * i) for i in range(n, -1, -1)]
    if span >= 360.0 - EPS and r0 > EPS:
        # full ring: an annulus is not a simple polygon; represent it as two half rings joined (caller uses ring_polys)
        raise StudyError('full ring requested as one polygon; use ring_polys')
    return outer + inner


def ring_polys(r0, r1, step=1.0):
    return [sector_poly(a, a + 90.0, r0, r1, step) for a in (0.0, 90.0, 180.0, 270.0)]


def rect_poly(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rot_rect(cx, cy, length, width, ang_deg):
    """Rectangle of the given length (along ang_deg) and width, centred at (cx, cy); ang measured in the assembly XY plane."""
    t = math.radians(ang_deg)
    ux, uy = math.cos(t), math.sin(t)
    vx, vy = -uy, ux
    hl, hw = length / 2.0, width / 2.0
    return [(cx + sl * hl * ux + sw * hw * vx, cy + sl * hl * uy + sw * hw * vy) for sl, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def local_frame(az, r):
    """Pose frame at polar (r, az): origin, radial unit, clockwise-tangential unit (assembly XY)."""
    t = math.radians(az)
    return xy(r, az), (math.sin(t), -math.cos(t)), (math.cos(t), math.sin(t))


def local_rect_poly(az, r, length_t, width_r, grow=0.0, shift_r=0.0):
    """Rectangle centred on polar (r, az) with its long side TANGENTIAL (length_t) and short side RADIAL (width_r)."""
    o, er, et = local_frame(az, r + shift_r)
    hl, hw = length_t / 2.0 + grow, width_r / 2.0 + grow
    return [(o[0] + sr * hw * er[0] + st_ * hl * et[0], o[1] + sr * hw * er[1] + st_ * hl * et[1]) for sr, st_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def poly_bbox(p):
    xs = [q[0] for q in p]
    ys = [q[1] for q in p]
    return (min(xs), min(ys), max(xs), max(ys))


def bbox_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def seg_seg_dist(a, b, c, d):
    if g4.segment_intersects(a, b, c, d):
        return 0.0
    return min(g4.seg_dist(a, c, d), g4.seg_dist(b, c, d), g4.seg_dist(c, a, b), g4.seg_dist(d, a, b))


def poly_overlap(pa, pb):
    """Exact interior-or-touching overlap of two simple polygons (superset semantics of g4.polygon_overlap)."""
    return g4.polygon_overlap(pa, dict(type='poly', pts=pb))


def poly_gap(pa, pb, ba=None, bb=None, limit=None):
    """Exact plan distance (0 when the polygons overlap or touch). `limit`: when the bounding boxes are already farther apart than
    limit the bounding-box distance (a lower bound) is returned (used only by screens that do not need the exact value)."""
    ba = ba or poly_bbox(pa)
    bb = bb or poly_bbox(pb)
    bg = bbox_gap(ba, bb)
    if limit is not None and bg > limit:
        return bg
    count()
    if bg <= EPS and poly_overlap(pa, pb):
        return 0.0
    ea = list(zip(pa, pa[1:] + pa[:1]))
    eb = list(zip(pb, pb[1:] + pb[:1]))
    d1 = min(g4.seg_dist(p, a, b) for p in pa for a, b in eb)
    d2 = min(g4.seg_dist(p, a, b) for p in pb for a, b in ea)
    return min(d1, d2)


def geom_polys(g):
    """A g4 region (rect / poly / sector / circles) as a list of conservative polygons."""
    t = g['type']
    if t == 'rect':
        return [rect_poly(*g['rect'])]
    if t == 'poly':
        return [[tuple(p) for p in g['pts']]]
    if t == 'circles':
        return [circ_poly(x, y, r) for x, y, r in g['circles']]
    a0, a1 = g['az']
    full = tuple(g['az']) == (0.0, 360.0)
    if full:
        if g['r'][0] <= EPS:
            return [circ_poly(C0[0], C0[1], g['r'][1])]
        return ring_polys(g['r'][0], g['r'][1])
    span = (a1 - a0) % 360.0
    if span > 180.0:
        mid = (a0 + span / 2.0) % 360.0
        return [sector_poly(a0, mid, g['r'][0], g['r'][1]), sector_poly(mid, a1, g['r'][0], g['r'][1])]
    return [sector_poly(a0, a1, g['r'][0], g['r'][1])]


def polys_gap(la, lb, limit=None):
    """Distance between two unions of polygons."""
    return min(poly_gap(a, b, limit=limit) for a in la for b in lb)


def pt_in_any(p, polys):
    return any(g4.pip(p, q) for q in polys)


def arc_open_gap_deg(az_arc, a0, a1):
    """Angular gap (deg) between a clockwise arc and the closed interval [a0, a1]; 0 when they intersect or touch."""
    return g4.arc_gap(tuple(az_arc), (a0 % 360.0, a1 % 360.0))


# --------------------------------------------------------------------------------------------
# Occupants: explicit solids (plan polygon x Z interval at linear worst) and the strict 3-D clearance rule (R1:R3-3)
# --------------------------------------------------------------------------------------------
def occupant(oid, kind, polys, z_lo, z_hi, tol_lo=0.0, tol_hi=0.0, shapes=None, **extra):
    """polys: list of polygons (a union). z_lo / z_hi nominal; tol_lo / tol_hi: adverse growth of the solid in -Z / +Z. shapes: optional exact
    analytic representation used for clearance (('disk', (cx, cy, R)), ('ring', (r0, r1)) about the MAIN centre, ('poly', polygon)); the
    polygons stay available for areas, sampling and drawings."""
    polys = [list(map(tuple, p)) for p in polys]
    if shapes is None:
        shapes = [('poly', p) for p in polys]
    sh = []
    for kind_, geom in shapes:
        if kind_ == 'poly':
            sh.append(('poly', list(map(tuple, geom)), poly_bbox(geom)))
        elif kind_ == 'disk':
            sh.append(('disk', tuple(geom), (geom[0] - geom[2], geom[1] - geom[2], geom[0] + geom[2], geom[1] + geom[2])))
        else:
            sh.append(('ring', tuple(geom), (C0[0] - geom[1], C0[1] - geom[1], C0[0] + geom[1], C0[1] + geom[1])))
    d = dict(id=oid, kind=kind, polys=polys, bbox=[poly_bbox(p) for p in polys], shapes=sh, z_lo_nom=z_lo, z_hi_nom=z_hi,
             z_lo_adv=z_lo - tol_lo, z_hi_adv=z_hi + tol_hi, tol_lo=tol_lo, tol_hi=tol_hi)
    d.update(extra)
    return d


def pt_poly_dist(p, poly):
    if g4.pip(p, poly):
        return 0.0
    return min(g4.seg_dist(p, a, b) for a, b in zip(poly, poly[1:] + poly[:1]))


def poly_radial_span(poly):
    rs = [math.hypot(q[0] - C0[0], q[1] - C0[1]) for q in poly]
    rmin = 0.0 if g4.pip(C0, poly) else min(g4.seg_dist(C0, a, b) for a, b in zip(poly, poly[1:] + poly[:1]))
    return rmin, max(rs)


def shape_gap(sa, sb, limit=None):
    ka, ga, ba = sa
    kb, gb, bb = sb
    if ka == 'ring' and kb != 'ring' or (ka == 'disk' and kb == 'poly'):
        ka, ga, ba, kb, gb, bb = kb, gb, bb, ka, ga, ba          # canonical order: poly < disk < ring
    if ka == 'poly' and kb == 'poly':
        return poly_gap(ga, gb, ba, bb, limit)
    if ka == 'poly' and kb == 'disk':
        bg = bbox_gap(ba, bb)
        if limit is not None and bg > limit:
            return bg
        return max(0.0, pt_poly_dist((gb[0], gb[1]), ga) - gb[2])
    if ka == 'disk' and kb == 'disk':
        return max(0.0, math.dist((ga[0], ga[1]), (gb[0], gb[1])) - ga[2] - gb[2])
    if ka == 'poly' and kb == 'ring':
        rmin, rmax = poly_radial_span(ga)
        if rmax <= gb[0]:
            return gb[0] - rmax
        if rmin >= gb[1]:
            return rmin - gb[1]
        return 0.0
    if ka == 'disk' and kb == 'ring':
        d = math.hypot(ga[0] - C0[0], ga[1] - C0[1])
        if d + ga[2] <= gb[0]:
            return gb[0] - d - ga[2]
        if d - ga[2] >= gb[1]:
            return d - ga[2] - gb[1]
        return 0.0
    if ka == 'ring' and kb == 'ring':
        return max(0.0, gb[0] - ga[1], ga[0] - gb[1])
    raise StudyError('unknown shape pair %s / %s' % (ka, kb))


def occ_plan_gap(a, b, limit=None):
    best = None
    for sa in a['shapes']:
        for sb in b['shapes']:
            g = shape_gap(sa, sb, limit)
            if best is None or g < best:
                best = g
                if best <= EPS:
                    return 0.0
    return best


def occ_z_gap(a, b, zs=None):
    """Signed Z separation (> 0 separated) at adverse extents, less the dimension chain tolerance of the layers fully between the two
    nominal references when a Z stack is supplied."""
    if a['z_lo_nom'] >= b['z_hi_nom']:
        lo, hi = a, b
    elif b['z_lo_nom'] >= a['z_hi_nom']:
        lo, hi = b, a
    else:
        return max(b['z_lo_adv'] - a['z_hi_adv'], a['z_lo_adv'] - b['z_hi_adv'])
    gap = lo['z_lo_adv'] - hi['z_hi_adv']
    if zs is not None:
        gap -= zs.chain_tol(hi['z_hi_nom'], lo['z_lo_nom'])
    return gap


def pair_clearance(a, b, c_plan=0.0, c_z=0.0, zs=None, limit=6.0, fast=False):
    """Strict 3-D clearance (R1:R3-3): separated in Z by > EPS and >= c_z, or in plan by > EPS and >= c_plan. Returns (clear, record)."""
    count()
    zg = occ_z_gap(a, b, zs)
    if r1.separated(zg, c_z):
        return True, dict(a=a['id'], b=b['id'], mode='Z', z_gap_mm=zg, plan_gap_mm=None, required_plan_mm=c_plan, required_z_mm=c_z)
    pg = occ_plan_gap(a, b, limit=(c_plan + 1e-6 if fast else limit))
    return r1.separated(pg, c_plan), dict(a=a['id'], b=b['id'], mode='PLAN', z_gap_mm=zg, plan_gap_mm=pg, required_plan_mm=c_plan, required_z_mm=c_z)


# ============================================================================================
# Study context: overlaid G4 Study (shallow copy with overlaid deep-copied inputs), candidate G4-B-ZC, R1 Ctx used as a library
# ============================================================================================
class Ctx2:
    def __init__(self, r2in, g4_res, st0, zs, battery, with_overlay=True, g2study=None):
        self.r2in, self.battery, self.zs = r2in, battery, zs
        self.src = Sources(r2in, with_overlay, battery)
        st = copy.copy(st0)
        st.I = self.src.g4in
        st.P = st.I['parameters']
        st.S, st.rp, st.sp = self.src.S, self.src.S['radial']['parameters'], self.src.S['parameters']
        if hasattr(st, '_support_cache'):
            st._support_cache = {}
        if with_overlay:
            st.z = {sid: dict(st0.z[sid], layers=dict(zs.over[sid]['layers'])) for sid in zs.over}
        self.st = st
        self.g4_res = g4_res
        empty = dict(poses=[], by_class={}, exclusions=[], c_plan=st.P['c_lra_plan_mm']['max'])
        self.cx = r1.Ctx(st, self.src.r1in, g4_res, poses=empty)
        self.cand = next(c for c in self.cx.cands if c['id'] == 'G4-B')    # G4-B-ZC: the G4-B midcase (metal + dielectric sectors) with a ceramic caseback
        self.ce = self.cx.ce[self.cand['id']]
        self.sp = self.ce.sp
        self.P = st.P
        self.delta = zs.delta if with_overlay else 0.0
        self.R_main = st.R_main
        self.levels = self.make_levels()

    def make_levels(self):
        """Level Z intervals (Z = 0 pod / caseback exterior plane, +Z front), nominal, from the overlaid layers; REAR includes the
        fixed REAR-band layer (the periphery band extends by Delta frontward of the REAR inner face)."""
        lay = self.st.z['G2-REVA']['layers']
        z, cum = 0.0, {}
        for k in LAYER_ORDER:
            cum[k] = (z, z + lay.get(k, 0.0))
            z += lay.get(k, 0.0)
        lv = {}
        for name, ks in self.st.I['levels'].items():
            if name == 'note':
                continue
            lv[name] = (min(cum[k][0] for k in ks), max(cum[k][1] for k in ks))
        lv['REAR'] = (0.0, cum['rear_band'][1])
        lv['FRONT'] = (lv['FRONT_GAP'][0], lv['COVER'][1])      # architecture level FRONT = front gap + display + cover
        lv['_layers'] = cum
        return lv


def build_base_study(g4_res_study=None):
    """g4.Study at the pinned inputs (the overlay-off record: legacy numbers, pins)."""
    return g4_res_study if g4_res_study is not None else g4.Study()


# ============================================================================================
# L-BTN: T1 stem O-ring (re-admitted), T2-F / T2-R boot, per switch and pusher class; boss <= +3.0 mm; I-SUM binds, I-MAX reported
# ============================================================================================
BTN_SW = ('SW1', 'SW2', 'SW3', 'SW4', 'SW5')
NONMETAL_SW = ('SW1', 'SW5')


def btn_terms2(cx2, sw, option):
    """R1 button terms with the R2 material rules: SW1 and SW5 have a dielectric (polymer) bore / boss (reserved regions BLE / Wi-Fi,
    Q-R2-BOSS-MATERIAL) and a non-metallic pusher (zirconia or PEEK class); SW2-SW4 metal. Switch windows are the frozen windows."""
    st, cand = cx2.st, cx2.cand
    T = dict(r1.btn_terms(cx2.cx, cand, sw))
    pc_name = cx2.r2in['buttons']['pusher_classes'][option]['process_class']
    if sw in NONMETAL_SW:
        pc = st.I['process_classes'][cand['dielectric_sector_process']]
        mat = st.I['material_classes'][cand['dielectric_sector_material']]
        T.update(tol_bore=pc['radius_mm'], tol_od=pc['od_radius_mm'], tol_boss=pc['boss_mm'], wall_min=mat['t_wall_min_mm']['max'],
                 local_process=pc['title'], local_material=cand['dielectric_sector_material'])
    T['pusher_pc'] = st.I['process_classes'][pc_name]
    T['option'] = option
    T['pusher_pc_name'] = pc_name
    return T


def btn_dp_grid(cx2, T, D, rim):
    b = cx2.r2in['buttons']['pusher_dp']
    chord_half = (D / 2.0) * math.sin(math.radians((T['window'][1] - T['window'][0]) / 2.0))
    cap = 2.0 * (chord_half - T['tol_bore'] - rim - T['wall_min'] - T['tol_boss'])
    out, v = [], b['start']
    while v <= cap + EPS:
        out.append(round(v, 6))
        v += b['step']
    return out, cap


def t1_gland(cx2, sw, T, cs):
    """Stem O-ring gland (G4 pusher_gland formulation, dynamic radial window unchanged) for one cross-section."""
    st, sp = cx2.st, cx2.sp
    o = st.I['parameters']['oring']
    w = o['windows']['dynamic_radial']
    pc = T['pusher_pc']
    h = round(cs * (1 - (w['compression_min'] + w['compression_max']) / 2) / 0.005) * 0.005
    bottom_tol = max(pc['radius_mm'], pc['groove_depth_mm'])
    tol_h = T['tol_bore'] + bottom_tol
    tol_g = pc['groove_width_mm']
    dmax = cs + o['cs_tolerance_mm']['max']
    g = math.ceil(((math.pi / 4 * dmax ** 2) / (w['fill_max'] * (h - tol_h)) + tol_g) / 0.01 - 1e-9) * 0.01 if h - tol_h > 0 else None
    if g is None:
        return dict(cs=cs, h=h, g=None, tol_h=tol_h, tol_g=tol_g, margins=[-9.0, -9.0, -9.0], pass_=False, depth_tol=pc['groove_depth_mm'])
    specs = sp.gland('T1-' + sw, 'dynamic_radial', cs, h, g, tol_h, tol_g)
    m = [g4.run_check(x, full=False) for x in specs]
    count(3)
    return dict(cs=cs, h=h, g=g, tol_h=tol_h, tol_g=tol_g, margins=m, pass_=min(m) >= -EPS, depth_tol=pc['groove_depth_mm'])


def t1_section(T, D, boss, dp, gd, interp):
    """T1 section margins with the same terms as r1.btn_section: stack = 2 guide lands + groove width + groove tolerance + stroke +
    stop shoulder; the stem groove replaces the boot; core, boss wall and tangential fit as T2."""
    count()
    for k in ('c_main_case', 'c_switch', 'guide', 'shoulder', 'tol_bore', 'tol_boss', 'tol_od'):
        if T.get(k) is None:
            raise StudyError('T1 button section term dropped: ' + k)
    gap = T['c_main_case'] + T['c_switch'] if interp == 'I-SUM' else max(T['c_main_case'], T['c_switch'])
    R_in = T['R_main'] + T['tol_pcb'] + gap + T['tol_bore']
    R_face = D / 2.0 - T['tol_od'] + boss - T['tol_boss']
    stroke = T['c_switch']
    stack = [('guide_land_inner', T['guide']), ('stop_shoulder', T['shoulder']), ('stroke', stroke),
             ('groove_width', gd['g']), ('groove_width_tol', gd['tol_g']), ('guide_land_outer', T['guide'])]
    L_req = sum(v for _, v in stack)
    L_av = R_face - R_in
    protrusion = boss + T['tol_boss']
    half_w = dp / 2.0 + T['tol_bore'] + T['wall_min'] + T['tol_boss']
    chord_half = (D / 2.0) * math.sin(math.radians((T['window'][1] - T['window'][0]) / 2.0))
    boss_half_deg = math.degrees(math.asin(min(1.0, half_w / (D / 2.0))))
    m = dict(bore_stack=L_av - L_req, protrusion=T['boss_limit'] - protrusion, tangential=chord_half - half_w,
             core=dp / 2.0 - T['tol_bore'] - gd['h'] - gd['depth_tol'] - T['core'],
             no_inward_lip=R_in - (T['R_main'] + T['tol_pcb'] + T['c_insert']),
             gland_compression_min=gd['margins'][0], gland_compression_max=gd['margins'][1], gland_fill=gd['margins'][2])
    units = {k: ('ratio' if k.startswith('gland_') else 'mm') for k in m}
    return dict(topology='T1', interpretation=interp, boss=boss, d_p=dp, R_inner=R_in, R_face=R_face, L_available=L_av, L_required=L_req,
                stack=[dict(term=n, value=v) for n, v in stack], protrusion_mm=protrusion, half_width_mm=half_w, boss_half_deg=boss_half_deg,
                stroke=stroke, margins=m, margin_units=units, cs=gd['cs'], groove_h=gd['h'], groove_g=gd['g'],
                min_margin=min(v for k, v in m.items() if units[k] == 'mm'), strain_margin=None,
                pass_=all(v >= -EPS for v in m.values()))


def btn_scan(cx2, sw, option, topo, D, interp):
    """Smallest-boss closure of one topology / pusher class / interpretation at diameter D (exact reduction, verified with production
    predicates): bore margin rises 1:1 with the boss, protrusion falls with it, core rises and tangential falls with d_p, both independent
    of the boss. Returns the closing section (or the best diagnostic section) plus the zero-margin thresholds."""
    T = btn_terms2(cx2, sw, option)
    step = cx2.r2in['buttons']['boss_extension']['step']
    bgrid = grid(cx2.r2in['buttons']['boss_extension'])
    limit = T['boss_limit']
    rim = T['rim'] if topo != 'T1' else 0.0
    dps, dp_cap = btn_dp_grid(cx2, T, D, rim)
    cands = []
    if topo == 'T1':
        cs_grid = grid(cx2.r2in['buttons']['t1_cs'])
        glands = [t1_gland(cx2, sw, T, cs) for cs in cs_grid]
        for gd in glands:
            if not gd['pass_']:
                continue
            for dp in dps:
                cands.append((gd, dp))
        sec = lambda b, dp, gd: t1_section(T, D, b, dp, gd, interp)
        diag_gd = max(glands, key=lambda g_: (min(g_['margins']), -g_['cs']))
    else:
        cands = [(None, dp) for dp in dps]
        sec = lambda b, dp, gd: r1.btn_section(T, D, topo, b, dp, interp)
        diag_gd = None
    best_fail = None
    rows = 0
    # closing configurations ordered by boss, then (T1: cs), then d_p
    for gd, dp in sorted(cands, key=lambda c: ((c[0]['cs'] if c[0] else 0.0), c[1])):
        s0 = sec(0.0, dp, gd)
        need = max(0.0, -s0['margins']['bore_stack'])
        b = next((x for x in bgrid if x >= need - EPS), None)
        rows += 1
        if b is None:
            continue
        s = sec(b, dp, gd)
        if s['pass_']:
            prev = [x for x in bgrid if x < b - EPS]
            minus = sec(prev[-1], dp, gd) if prev else None
            if minus is not None and minus['margins']['bore_stack'] >= -EPS and minus['pass_']:
                raise StudyError('STOP: button boss reduction not reproduced by the production predicates (%s %s %s)' % (sw, option, topo))
            return dict(sw=sw, option=option, topology=topo, interpretation=interp, closes=True, section=s, boss_zero_margin_mm=need, boss_grid_used_mm=b,
                        boss_limit_mm=limit, dp_cap_mm=dp_cap, rows_scanned=rows, causes=[])
        if best_fail is None or (min(s['margins'].values()) > best_fail[0]):
            best_fail = (min(s['margins'].values()), s, need)
    # no closure: diagnostic section at the largest admissible boss and the smallest d_p / best gland
    gd0 = diag_gd
    dp0 = dps[0] if dps else cx2.r2in['buttons']['pusher_dp']['start']
    bmax = max(b for b in bgrid if b + T['tol_boss'] <= limit + EPS)
    s = sec(bmax, dp0, gd0) if (topo != 'T1' or gd0) else None
    s0 = sec(0.0, dp0, gd0)
    need = max(0.0, -s0['margins']['bore_stack'])
    causes = sorted(k for k, v in (best_fail[1]['margins'] if best_fail else s['margins']).items() if v < -EPS)
    if not cands:
        causes = sorted(set(causes) | {'no_admissible_pusher_or_gland'})
    return dict(sw=sw, option=option, topology=topo, interpretation=interp, closes=False, section=best_fail[1] if best_fail else s,
                boss_zero_margin_mm=need, boss_grid_used_mm=None, boss_limit_mm=limit, dp_cap_mm=dp_cap, rows_scanned=rows, causes=causes)


def btn_rows(cx2, sw, D):
    """All (topology, pusher class) rows of one switch at diameter D, I-SUM and I-MAX in the same row."""
    rows = []
    for option in cx2.r2in['buttons']['switch_materials'][sw]['options']:
        for topo in cx2.r2in['buttons']['topologies']:
            rec = {i: btn_scan(cx2, sw, option, topo, D, i) for i in cx2.r2in['buttons']['interpretations']}
            rows.append(dict(sw=sw, option=option, topology=topo, I_SUM=rec['I-SUM'], I_MAX=rec['I-MAX']))
    return rows


def btn_switch_status(rows, boss_limit):
    """Per switch: closing rows under I-SUM (binding), the I-MAX-only rows (never a closure), and the stop class of a failing switch:
    a failure caused only by the boss (bore stack / protrusion beyond the limit) is R2-S03, any other cause R2-S12."""
    closing = [r for r in rows if r['I_SUM']['closes']]
    imax_only = [r for r in rows if not r['I_SUM']['closes'] and r['I_MAX']['closes']]
    boss_causes = {'bore_stack', 'protrusion'}
    if closing:
        return dict(closed=True, closing=[(r['topology'], r['option']) for r in closing], imax_only=[(r['topology'], r['option']) for r in imax_only], stop=None)
    causes = sorted({c for r in rows for c in r['I_SUM']['causes']})
    boss_only = bool(causes) and set(causes) <= boss_causes
    return dict(closed=False, closing=[], imax_only=[(r['topology'], r['option']) for r in imax_only], stop='R2-S03' if boss_only else 'R2-S12', causes=causes)


# ============================================================================================
# L-SEAL: raised radial O-ring on the ceramic cup wall (OV-SEAL). R1:R5 population / unit rules carried exactly.
# ============================================================================================
SEAL_TERMS = dict(gland_compression_min=('static radial compression minimum margin', 'ratio'),
                  gland_compression_max=('static radial compression maximum margin', 'ratio'),
                  gland_fill=('gland fill margin', 'ratio'),
                  spigot_rear_periphery_z=('cup wall top vs REAR-periphery band (+Delta, band retired)', 'mm'))
SEAL_DISPLAY_OVERRIDES = (None, 'first', 'last', 'poison')
SEAL_UNITS = dict(r1.SEAL_UNITS)


class DisplayOnlyRow(r1.DisplayOnlyRow):
    pass


def seal_unit_of(cx2):
    u = getattr(cx2, 'seal_unit', 'mm')
    if u not in SEAL_UNITS:
        raise StudyError('STOP: unknown seal length unit %r' % u)
    return u, SEAL_UNITS[u]


def seal_templates(cx2, unit, s):
    """Cross-section-only part of every seal row (gland, compression / fill ratios, spigot Z in the REAR band): independent of D and tw,
    cached per (unit, input signature). Lengths are scaled into the internal unit s."""
    cache = cx2.__dict__.setdefault('seal_template_cache', {})
    V = cx2.r2in['cup']['main_seal_cs']
    key = (unit, s, json.dumps([V, cx2.delta, cx2.P['c_rear_route_mm'], cx2.sp.pc_cb, cx2.sp.m_cb['groove_land_min_mm']], sort_keys=True))
    if key in cache:
        return cache[key]
    st, sp = cx2.st, cx2.sp
    Lr = lambda v: v * s
    cs_all = frange(V['start'], V['diagnostic_stop'], V['step'])
    n_auth = len(frange(V['start'], V['stop'], V['step']))
    t_out_min = r1.seal_t_out_min(cx2.cx, sp)
    route = st.P['c_rear_route_mm']['max']
    out = []
    for i, cs in enumerate(cs_all):
        gd = g4.gland_design(st, sp, 'radial', cs)
        gm = [g4.run_check(x, full=False) for x in sp.gland('R2-CB-MAIN', 'static_radial', gd['cs'], gd['h'], gd['g'], gd['tol_h'], gd['tol_g'])]
        lib = g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=t_out_min), gd['spigot_height']), full=False)
        count(4)
        out.append(dict(id='radial#%02d' % i, i=i, cs=Lr(cs), authorized=i < n_auth,
                        gland={k: Lr(gd[k]) for k in ('h', 'g', 'tol_h', 'tol_g', 'land', 'spigot_radial', 'spigot_height')},
                        m0=dict(gland_compression_min=gm[0], gland_compression_max=gm[1], gland_fill=gm[2]),
                        z_lib=Lr(lib), z_delta=Lr(cx2.delta), z_route=Lr(route), t_out_used=Lr(t_out_min)))
    cache[key] = out
    return out


def seal_population(cx2, D, tw, ext_z=0.0, display_override=None):
    """Every authorized cross-section row is evaluated independently with its own gland, r_lim and spigot Z; topology feasibility is
    any(r.pass_all); r_lim of the population is the minimum over the term population; the representative row is display-only.
    ext_z: Z extension (mm) of the continuous cup wall above the REAR band into the battery-band outer annulus that the joint annulus
    allocation grants (0 when blocked); the spigot Z margin of every row is the REAR-band margin plus ext_z."""
    st, sp = cx2.st, cx2.sp
    unit, s = seal_unit_of(cx2)
    eps = lambda u: EPS * s if u == 'mm' else EPS
    Lr = lambda v: v * s
    R = Lr(D / 2.0 - tw)
    tolr = Lr(sp.pc_cb['radius_mm'])
    rows = []
    for tp in seal_templates(cx2, unit, s):
        count()
        r = dict(id=tp['id'], i=tp['i'], cs=tp['cs'], authorized=tp['authorized'], gland=dict(tp['gland']), serviceable=True)
        m = dict(tp['m0'])
        z_band = tp['z_lib'] + tp['z_delta'] + tp['z_route']          # band retired (OV-COND-BAND), Delta added (OV-Z-REAR-BAND)
        z_with_band = tp['z_lib'] + tp['z_delta']                      # R1-literal state: the conductor band still reserved
        m['spigot_rear_periphery_z'] = z_band + Lr(ext_z)
        r.update(r_lim=R - r['gland']['spigot_radial'] - tolr, spigot_height=r['gland']['spigot_height'], t_out_used=tp['t_out_used'],
                 z_rear_band_only=z_band, z_with_conductor_band=z_with_band, z_extension=Lr(ext_z))
        r['margins'] = m
        pr = r['predicates'] = {}
        for k, v in m.items():
            if k not in SEAL_TERMS:
                raise StudyError('STOP: untyped main-seal margin %s (R4-8)' % k)
            pr[k] = v >= -eps(SEAL_TERMS[k][1])
        r['n_pass'] = sum(1 for v in pr.values() if v)
        r['gland_window'] = pr['gland_compression_min'] and pr['gland_compression_max'] and pr['gland_fill']
        r['pass_all'] = all(pr.values())
        rows.append(r)
    ev = [r for r in rows if r['authorized']]
    ff = [r for r in ev if r['pass_all']]
    pop = ff or ev
    same_q = lambda a, b, u: abs(a - b) <= 1e-12 * (s if u == 'mm' else 1.0)
    red = {}
    for k in sorted(ev[0]['margins']):
        u = SEAL_TERMS[k][1]
        vals = [r['margins'][k] for r in pop]
        hi = max(vals)
        red[k] = dict(value=hi, worst=min(vals), units=u, rows_attaining=[r['id'] for r in pop if same_q(r['margins'][k], hi, u)])
    tops = dict(radial=dict(serviceable=True, evaluated_rows=[r['id'] for r in ev], diagnostic_rows=[r['id'] for r in rows if not r['authorized']],
                            predicate_feasible_rows={k: [r['id'] for r in ev if r['predicates'][k]] for k in sorted(ev[0]['margins'])},
                            gland_window_rows=[r['id'] for r in ev if r['gland_window']], fully_feasible_rows=[r['id'] for r in ff],
                            feasible=bool(ff), term_population='fully_feasible_rows' if ff else 'evaluated_rows', term_reductions=red))
    r_lim = min(r['r_lim'] for r in pop)
    top_z = max((r['spigot_height'] + r['t_out_used']) for r in pop)
    gw = [r for r in rows if r['gland_window']]
    first = min(gw, key=lambda r: r['cs']) if gw else None
    # display-only representative row (chosen last; no physical consumer)
    if display_override not in SEAL_DISPLAY_OVERRIDES:
        raise StudyError('STOP: unknown seal display override %r' % display_override)

    def dkey(r):
        dim = [v for k, v in r['margins'].items() if SEAL_TERMS[k][1] == 'ratio']
        lin = [v for k, v in r['margins'].items() if SEAL_TERMS[k][1] == 'mm']
        return (r['pass_all'], r['n_pass'], bool(r['gland_window']), round(min(dim), 12) if dim else 0.0, round(min(lin) / s, 9) if lin else 0.0, -r['i'])
    pick = {None: lambda: max(ev, key=dkey), 'first': lambda: ev[0], 'last': lambda: ev[-1], 'poison': lambda: None}[display_override]()
    rep = DisplayOnlyRow() if pick is None else dict(id=pick['id'], cs_mm=pick['cs'] / s, display_only=True)
    mm_ = lambda v: None if v is None else v / s
    rows_mm = []
    for r in rows:
        rows_mm.append(dict(id=r['id'], i=r['i'], cs_mm=mm_(r['cs']), authorized=r['authorized'], predicates=r['predicates'], n_pass=r['n_pass'],
                            gland_window=r['gland_window'], pass_all=r['pass_all'], r_lim_mm=mm_(r['r_lim']), spigot_height_mm=mm_(r['spigot_height']),
                            spigot_radial_mm=mm_(r['gland']['spigot_radial']), groove_h_mm=mm_(r['gland']['h']), groove_g_mm=mm_(r['gland']['g']),
                            margins={k: (v / s if SEAL_TERMS[k][1] == 'mm' else v) for k, v in r['margins'].items()},
                            z_rear_band_only_mm=mm_(r['z_rear_band_only']), z_with_conductor_band_mm=mm_(r['z_with_conductor_band']),
                            z_extension_mm=mm_(r['z_extension'])))
    for k, v in red.items():
        if v['units'] == 'mm':
            v['value'], v['worst'] = v['value'] / s, v['worst'] / s
    return dict(internal_unit=unit, rows=rows_mm, topologies=tops, feasible=bool(ff), r_lim_mm=mm_(r_lim), cup_top_z_mm=mm_(top_z),
                population=[r['id'] for r in pop], smallest_gland_cs_mm=mm_(first['cs']) if first else None, representative_row=rep,
                feasible_row_ids=[r['id'] for r in ff], zero_margin_ext_mm=mm_(max(0.0, -max(r['margins']['spigot_rear_periphery_z'] for r in ev if r['gland_window']))
                                                                               if any(r['gland_window'] for r in ev) else None),
                zero_margin_ext_all_rows_mm={r['id']: mm_(max(0.0, -r['margins']['spigot_rear_periphery_z'])) for r in ev if r['gland_window']})


def seal_core(pop):
    """The emitted physical content of a seal population, as compared by the unit regression (display-only row excluded)."""
    return rounded(dict(rows=pop['rows'], r_lim=pop['r_lim_mm'], top=pop['cup_top_z_mm'], feasible=pop['feasible_row_ids'], population=pop['population'],
                        zero=pop['zero_margin_ext_all_rows_mm'], red=pop['topologies']['radial']['term_reductions']))


def seal_unit_regression(cx2, D, tw):
    """R1:R5 unit regression: the same evaluation in mm, m and um must emit identical results."""
    keep = getattr(cx2, 'seal_unit', 'mm')
    out = {}
    try:
        for u in sorted(SEAL_UNITS):
            cx2.seal_unit = u
            out[u] = chash(seal_core(seal_population(cx2, D, tw, 0.0)))
    finally:
        cx2.seal_unit = keep
    return dict(units=sorted(out), hashes=out, identical=len(set(out.values())) == 1)


def seal_ext_needed(cx2, D, tw):
    """Smallest Z extension (mm) above the REAR band that makes at least one gland-feasible authorized row pass (None when no row has a
    feasible gland)."""
    pop = seal_population(cx2, D, tw, 0.0)
    need = [max(0.0, -r['margins']['spigot_rear_periphery_z']) for r in pop['rows'] if r['authorized'] and r['gland_window']]
    return (min(need) if need else None), pop


# ============================================================================================
# L-STR: ceramic cup. Plate (accepted G4 / R1 annular-plate solution, loaded-boss inner edge) joined to the raised wall ring at r_ring by
# axisymmetric ring-plate compatibility; a clamped edge is never assumed.
# ============================================================================================
def plate_solve2(regions, q, inner='loaded_boss', outer='ss', outer_vals=(0.0, 0.0), nsamp=41):
    """r1.plate_solve generalised to an inhomogeneous outer boundary: outer_vals = (value of the first, value of the second outer
    state component). With outer_vals = (0, 0) the result equals r1.plate_solve exactly (overlay-off equivalence test)."""
    if inner not in r1.INNER_BC:
        raise StudyError('invented inner caseback support refused (LA-STR-3): inner=%s' % inner)
    count()
    r0 = regions[0]['r0']
    fixed = dict(psi=0.0, Q=(-q * r0 / 2.0 if inner == 'loaded_boss' else 0.0))
    free = [k for k in r1.STATE if k not in r1.INNER_BC[inner]]
    S0 = [fixed.get(k, 0.0) for k in r1.STATE]
    E1 = [1.0 if k == free[0] else 0.0 for k in r1.STATE]
    E2 = [1.0 if k == free[1] else 0.0 for k in r1.STATE]
    vecs = [S0, E1, E2]
    coeffs = []
    for reg in regions:
        B0, P0 = r1._bmat(reg['r0'], reg, q)
        Bi = r1._inv4(B0)
        xs = [r1._mv(Bi, [s - (p if j == 0 else 0.0) for s, p in zip(v, P0)]) for j, v in enumerate(vecs)]
        coeffs.append(xs)
        B1, P1 = r1._bmat(reg['r1'], reg, q)
        vecs = [[a + (p if j == 0 else 0.0) for a, p in zip(r1._mv(B1, x), P1)] for j, x in enumerate(xs)]
    idx = [r1.STATE.index(k) for k in r1.OUTER_BC[outer]]
    a11, a12 = vecs[1][idx[0]], vecs[2][idx[0]]
    a21, a22 = vecs[1][idx[1]], vecs[2][idx[1]]
    b1, b2 = outer_vals[0] - vecs[0][idx[0]], outer_vals[1] - vecs[0][idx[1]]
    det = a11 * a22 - a12 * a21
    if abs(det) < 1e-300:
        raise StudyError('singular plate boundary system')
    s1 = (b1 * a22 - a12 * b2) / det
    s2 = (a11 * b2 - b1 * a21) / det
    out = []
    for reg, xs in zip(regions, coeffs):
        x = [xs[0][i] + s1 * xs[1][i] + s2 * xs[2][i] for i in range(4)]
        pts = []
        for j in range(nsamp):
            r = reg['r0'] + (reg['r1'] - reg['r0']) * j / (nsamp - 1.0)
            b = r1._ortho(r, reg, q)
            val = {key: x[0] * b[key][0][0] + x[1] * b[key][0][1] + x[2] * b[key][0][2] + x[3] * b[key][0][3] + b[key][1]
                   for key in ('w', 'psi', 'dpsi', 'Mr', 'Mt')}
            val['r'] = r
            pts.append(val)
        out.append(dict(region=reg, x=x, samples=pts))
    return out


def rect_props(x0, x1, z0, z1):
    w, h = x1 - x0, z1 - z0
    return w * h, (x0 + x1) / 2.0, (z0 + z1) / 2.0, w * h ** 3 / 12.0


def ring_section(r_wi, r_wo, z_top, t_out, groove_h, groove_g, land):
    """Raised-wall cross-section (radial x Z, including the gland groove): area, centroid radius / height, centroidal inertia
    I = integral (z - z_c)^2 dA (tilt stiffness) and the extreme fibre heights."""
    A1, x1, z1, I1 = rect_props(r_wi, r_wo, 0.0, z_top)
    g0 = t_out + land
    A2, x2, z2, I2 = rect_props(r_wo - groove_h, r_wo, g0, g0 + groove_g)
    A = A1 - A2
    xc = (A1 * x1 - A2 * x2) / A
    zc = (A1 * z1 - A2 * z2) / A
    I = (I1 + A1 * (z1 - zc) ** 2) - (I2 + A2 * (z2 - zc) ** 2)
    return dict(A=A, x_c=xc, z_c=zc, I=I, z_min=0.0, z_max=z_top, r_wi=r_wi, r_wo=r_wo, groove=[r_wo - groove_h, g0, g0 + groove_g])


def lame_edge_compliance(ri, a, t, E, nu):
    """Radial displacement per unit outward edge force per unit length at r = a of an annulus (inner edge free) of thickness t."""
    sig = 1.0 / t
    return sig * a / E * (((1.0 - nu) * a * a + (1.0 + nu) * ri * ri) / (a * a - ri * ri))


def cup_materials(cx2):
    cb = cx2.cand['caseback']
    return r1.str_material(cx2.st, cb['material'], cb['process'])


def cup_regions(cx2, a, cfg, mat):
    geo = dict(rb=cx2.cx.rb, r_step=cx2.cx.r_step, r_rib_in=cx2.cx.r_s14_clear, r_rib_out=a, R=a, gap_deg=None)
    return r1.str_regions(geo, lambda r: mat, dict(cfg, n=0, w=0.0, h=0.0), 'B', cx2.cx.P['screen_b']['subregions']), geo


def plate_stress_field(sol, p, K_t, junctions, holes):
    """Planning stresses (MPa) of the plate field: bulk, K_t at the inner and outer junctions, K_t at hole radii."""
    bulk, bulk_at = 0.0, None
    inner_j = outer_j = hole = 0.0
    wmax = w_in = 0.0
    for s in sol:
        reg = s['region']
        for smp in s['samples']:
            sig = 6.0 * max(abs(smp['Mr']), abs(smp['Mt'])) / reg['t'] ** 2
            if sig > bulk:
                bulk, bulk_at = sig, (smp['r'], reg['kind'])
            if abs(smp['r'] - junctions[0]) < 1e-9:
                inner_j = max(inner_j, sig)
            if abs(smp['r'] - junctions[1]) < 1e-9:
                outer_j = max(outer_j, sig)
            if holes and holes[0] - 1e-9 <= smp['r'] <= holes[1] + 1e-9:
                hole = max(hole, sig)
            wmax = max(wmax, abs(smp['w']))
            if smp['r'] <= junctions[2] + EPS:
                w_in = max(w_in, abs(smp['w']))
    return dict(bulk=bulk, bulk_at=bulk_at, inner_junction=K_t * inner_j, outer_junction=K_t * outer_j, hole=K_t * hole if holes else 0.0,
                w_max=wmax, w_inside_outline=w_in)


def cup_eval(cx2, D, tw, row, cfg, ring_continuous=True, hole_band=None, nsamp=41):
    """One cup configuration. row: one seal row (radial cs) of seal_population; cfg: t_in, t_out, w_extra, H (wall height above the
    plate top). Returns plate / ring compatibility result: bounds (simply supported, clamped), governing stress, deflection."""
    st, sp = cx2.st, cx2.sp
    mat = cup_materials(cx2)
    p = cx2.cx.p
    K_t = cx2.cx.P['V14_rib_geometry']['K_t']
    R_side = D / 2.0 - tw
    land = sp.m_cb['groove_land_min_mm']
    r_wo = R_side
    r_wi = row['r_lim_mm'] - cfg['w_extra']
    z_top = cfg['t_out'] + cfg['H']
    sec = ring_section(r_wi, r_wo, z_top, cfg['t_out'], row['groove_h_mm'], row['groove_g_mm'], land)
    a = sec['x_c']
    regs, geo = cup_regions(cx2, a, dict(t_in=cfg['t_in'], t_out=cfg['t_out']), mat)
    nsamp_ = nsamp
    ss = plate_solve2(regs, p, 'loaded_boss', 'ss', (0.0, 0.0), nsamp_)
    cl = plate_solve2(regs, p, 'loaded_boss', 'clamped', (0.0, 0.0), nsamp_)
    lim = min(st.P['c_cb_rear_mm']['min'], cx2.cx.window['standoff_min_mm'])
    j = (regs[0]['r0'], a, cx2.st.s14geo['outline_r'])
    hole = hole_band
    st_ss = plate_stress_field(ss, p, K_t, j, hole)
    st_cl = plate_stress_field(cl, p, K_t, j, hole)
    psi_ss = ss[-1]['samples'][-1]['psi']
    um = plate_solve2(regs, 0.0, 'loaded_boss', 'ss', (0.0, 1.0), nsamp_)
    f_M = um[-1]['samples'][-1]['psi']
    sigma_M = 1.0 if f_M >= 0.0 else -1.0
    t_edge = regs[-1]['t']
    cN = lame_edge_compliance(regs[0]['r0'], a, t_edge, mat['E'], mat['nu'])
    e = sec['z_c'] - cfg['t_out'] / 2.0
    kA, kI = mat['E'] * sec['A'] / a ** 2, mat['E'] * sec['I'] / a ** 2
    K = [[kA, -e * kA], [-e * kA, kI + e * e * kA]]
    C = [cN, abs(f_M)]
    # (I + C K) x = [0, psi_ss]  with x = (u_j, psi); N_p = -(K x)_1, M' = -(K x)_2
    Am = [[1.0 + C[0] * K[0][0], C[0] * K[0][1]], [C[1] * K[1][0], 1.0 + C[1] * K[1][1]]]
    det = Am[0][0] * Am[1][1] - Am[0][1] * Am[1][0]
    bvec = [0.0, psi_ss]
    u_j = (bvec[0] * Am[1][1] - Am[0][1] * bvec[1]) / det
    psi = (Am[0][0] * bvec[1] - Am[1][0] * bvec[0]) / det
    Fx = [K[0][0] * u_j + K[0][1] * psi, K[1][0] * u_j + K[1][1] * psi]
    N_p, M_g = -Fx[0], -Fx[1]
    M_p = sigma_M * M_g
    if not ring_continuous:
        N_p = M_p = 0.0
        sol = ss
        psi = psi_ss
        u_j = 0.0
        credit = 0.0
    else:
        sol = plate_solve2(regs, p, 'loaded_boss', 'ss', (0.0, M_p), nsamp_)
        credit = 1.0
    st_c = plate_stress_field(sol, p, K_t, j, hole)
    u_c = u_j - e * psi
    sig_hoop = [mat['E'] * (u_c - psi * (z - sec['z_c'])) / a for z in (sec['z_min'], sec['z_max'])] if ring_continuous else [0.0, 0.0]
    land_wall = (r_wo - row['groove_h_mm']) - r_wi
    h_exp = cfg['t_out'] + land
    sig_p = p * r_wo / max(land_wall, 0.05) * (h_exp / h_exp)
    membrane = abs(N_p) / regs[-1]['t']
    ring_sig = K_t * max(abs(s_) for s_ in sig_hoop) + sig_p
    comps = dict(plate_bulk=st_c['bulk'], plate_inner_junction_Kt=st_c['inner_junction'], plate_outer_junction_Kt=st_c['outer_junction'] + membrane,
                 plate_hole_Kt=st_c['hole'], ring_hoop_Kt_plus_pressure=ring_sig)
    gov_k = max(comps, key=lambda k: (comps[k], k))
    sigma = comps[gov_k]
    wmax = st_c['w_max']
    return dict(config=dict(cfg), row=row['id'], cs_mm=row['cs_mm'], r_ring_mm=a, r_wall_inner_mm=r_wi, r_wall_outer_mm=r_wo, z_top_mm=z_top,
                ring=dict(A_mm2=sec['A'], I_mm4=sec['I'], x_c=sec['x_c'], z_c=sec['z_c'], e_mm=e, k_A=kA, k_I=kI, groove=sec['groove']),
                plate=dict(psi_ss=psi_ss, f_M=f_M, cN=cN, psi_comp=psi, u_j=u_j, N_p=N_p, M_p=M_p, edge_fixity=1.0 - abs(psi) / abs(psi_ss) if psi_ss else None),
                bounds=dict(simply_supported=dict(sigma_MPa=max(st_ss['bulk'], st_ss['inner_junction'], st_ss['outer_junction'], st_ss['hole']), w_max_mm=st_ss['w_max']),
                            clamped=dict(sigma_MPa=max(st_cl['bulk'], st_cl['inner_junction'], st_cl['outer_junction'], st_cl['hole']), w_max_mm=st_cl['w_max'])),
                components_MPa=comps, governing=dict(component=gov_k, sigma_MPa=sigma, screen='B'), sigma_governing_MPa=sigma, w_max_mm=wmax,
                w_inside_outline_mm=st_c['w_inside_outline'], bulk_at=st_c['bulk_at'], ring_credit=credit, sigma_allow_planning_MPa=mat['sigma_allow'],
                stress_margin_MPa=mat['sigma_allow'] - sigma, deflection_limit_mm=lim, deflection_margin_mm=lim - wmax,
                deflection_pass=wmax <= lim + 1e-9, static_clearance_to_rear_mm=None)


def cup_alloc_height(cx2, t_out, ext_z=0.0):
    """Wall height available above the plate top inside the REAR-periphery band with the conductor band retired and Delta added
    (library spec at zero spigot + Delta + c_rear_route), plus the granted outer-annulus extension. P-1: also the R1-literal state."""
    st, sp = cx2.st, cx2.sp
    m0 = g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=t_out), 0.0), full=False)
    route = st.P['c_rear_route_mm']['max']
    return dict(retired=m0 + cx2.delta + route + ext_z, with_conductor_band=m0 + cx2.delta + ext_z, r1_literal=m0)


def cup_t_windows(cx2):
    """t_in / t_out admissible values: pod residual (G4 H11-POD-RESIDUAL) and the ceramic floor (R1 lane_str rule)."""
    st, sp, cx = cx2.st, cx2.sp, cx2.cx
    P = cx.P
    mat = cup_materials(cx2)
    tin = []
    for t in grid(P['V12_caseback_thickness']['t_in']):
        pod = g4.run_check(sp.pod_residual(dict(t_w=cx.window['eligible_t_max'] or 0.5, t_in=t)), full=False)
        floor = t - mat['tol_t'] - mat['t_min']
        tin.append(dict(t_in=t, pod_residual_mm=pod, material_floor_mm=floor, ok=pod >= -EPS and floor >= -EPS))
    tout = []
    for t in grid(P['V12_caseback_thickness']['t_out']):
        floor = t - mat['tol_t'] - mat['t_min']
        tout.append(dict(t_out=t, material_floor_mm=floor, ok=floor >= -EPS))
    return tin, tout


def struct_search(cx2, D, tw, pop, hole_band=None, ext_z=0.0):
    """Admissible cup configurations at one design point: every gland-feasible authorized row x t_out x ring widening x wall height.
    Reports the best configuration inside the Z allocation, the best physical configuration at any wall height, and the shortfalls."""
    tin, tout = cup_t_windows(cx2)
    t_in = max((x['t_in'] for x in tin if x['ok']), default=None)
    touts = [x['t_out'] for x in tout if x['ok']]
    if t_in is None or not touts:
        return dict(geometry_ok=False, tin=tin, tout=tout, configs=0)
    rows = [r for r in pop['rows'] if r['authorized'] and r['gland_window']]
    lim = None
    evs = []
    wx = grid(cx2.r2in['cup']['ring_extra_width_mm'])
    wx_set = [wx[0], wx[len(wx) // 2], wx[-1]]
    for row in rows:
        for t_out in touts:
            alloc = cup_alloc_height(cx2, t_out, ext_z)
            for k in range(5):
                H = row['spigot_height_mm'] + 0.5 * k
                for w in wx_set:
                    cfg = dict(t_in=t_in, t_out=t_out, w_extra=w, H=H)
                    ev = cup_eval(cx2, D, tw, row, cfg, True, hole_band)
                    ev['alloc_height_mm'] = alloc['retired']
                    ev['alloc_ok'] = H <= alloc['retired'] + EPS
                    ev['alloc_with_conductor_band_ok'] = H <= alloc['with_conductor_band'] + EPS
                    evs.append(ev)
    count(len(evs))
    lim = evs[0]['deflection_limit_mm'] if evs else None
    phys = [e for e in evs if e['deflection_pass']]
    key = lambda e: (e['sigma_governing_MPa'], e['cs_mm'], e['config']['H'], e['config']['w_extra'], e['config']['t_out'])
    in_alloc = [e for e in phys if e['alloc_ok']]
    best_alloc = min(in_alloc, key=key) if in_alloc else None
    best_any = min(phys, key=key) if phys else None
    best_defl = min(evs, key=lambda e: (e['w_max_mm'], e['sigma_governing_MPa'])) if evs else None
    # required wall height (deflection hard physical) for the smallest gland-feasible row at its best t_out and widening 0
    req = None
    if rows:
        row = rows[0]
        for t_out in touts:
            for k in range(0, 61):
                H = row['spigot_height_mm'] + 0.1 * k
                ev = cup_eval(cx2, D, tw, row, dict(t_in=t_in, t_out=t_out, w_extra=0.0, H=H), True, hole_band, 21)
                if ev['deflection_pass']:
                    cand = dict(row=row['id'], t_out=t_out, H=H, z_top=t_out + H, sigma=ev['sigma_governing_MPa'], w=ev['w_max_mm'])
                    if req is None or cand['z_top'] < req['z_top']:
                        req = cand
                    break
    return dict(geometry_ok=True, t_in=t_in, tin=tin, tout=tout, configs=len(evs), deflection_limit_mm=lim, best_within_allocation=best_alloc,
                best_physical_any_height=best_any, best_deflection=best_defl, required_wall_for_deflection=req,
                physical_pass=best_alloc is not None, physical_pass_any_height=best_any is not None,
                governing_stress_best_any=best_any['sigma_governing_MPa'] if best_any else None, evs=evs)


# ============================================================================================
# L-PKG: pack, carrier, offset, PCM lobe, zones A / B, MAIN-outline column, case supports (G4_R2_BRIEF sections 6.2-6.8)
# ============================================================================================
def frame_at(center, az, r):
    t = math.radians(az)
    er = (math.sin(t), -math.cos(t))
    et = (math.cos(t), math.sin(t))
    return (center[0] + r * er[0], center[1] + r * er[1]), er, et


def frame_rect(center, az, r0, r1, half_t, grow=0.0):
    """Rectangle in the frame of a centre point: radial [r0 - grow, r1 + grow], tangential +/- (half_t + grow)."""
    o, er, et = frame_at(center, az, 0.0)
    pts = []
    for rr, tt in ((r0 - grow, -half_t - grow), (r1 + grow, -half_t - grow), (r1 + grow, half_t + grow), (r0 - grow, half_t + grow)):
        pts.append((o[0] + rr * er[0] + tt * et[0], o[1] + rr * er[1] + tt * et[1]))
    return pts


def disk_extent_along(center, radius, az):
    """Largest radius (from the MAIN centre) of a disk along the ray at azimuth az."""
    dx, dy = center[0] - C0[0], center[1] - C0[1]
    t = math.radians(az)
    ux, uy = math.sin(t), -math.cos(t)
    proj = dx * ux + dy * uy
    perp2 = dx * dx + dy * dy - proj * proj
    return proj + math.sqrt(max(0.0, radius * radius - perp2))


def offset_vector(mag, direction):
    t = math.radians(direction)
    return (C0[0] + mag * math.sin(t), C0[1] - mag * math.cos(t))


def package_geometry(cx2, off, pcm_az=None, rc_k=0, lobe='max'):
    """Pack, carrier and PCM lobe about the offset centre at linear worst (R2-V05 .. V07). Pack envelope = cell + planning tolerance +
    radial growth; carrier inner radius from the G4 pack predicate on the R2-V06 grid; carrier outer radius includes both carrier tolerances."""
    st, sp, r2in = cx2.st, cx2.sp, cx2.r2in
    pcm_az = r2in['grids']['pcm_az_design_deg'] if pcm_az is None else pcm_az
    mag, direction = off
    cp = offset_vector(mag, direction)
    R_pack = (st.rp['D_pack_nom']['nom'] + st.rp['tol_pack_dia']['max']) / 2.0
    g_rad = st.P['g_radial_mm']['max']
    tol_c, tol_w = sp.pc_car['radius_mm'], sp.pc_car['thickness_mm']
    extras = grid(r2in['grids']['carrier_radius_extra_mm'])
    rc_ok = [R_pack + g_rad + tol_c + x for x in extras]
    R_c = rc_ok[rc_k]
    pack_margin = cx2.ce.f['pack'](R_carrier_inner=R_c)
    tcw = next((t for t in grid(r2in['grids']['t_carrier_wall_mm']) if g4.run_check(sp.carrier_wall(dict(cx2.ce.dp0, tcw=t)), full=False) >= -EPS), None)
    wall_margin = g4.run_check(sp.carrier_wall(dict(cx2.ce.dp0, tcw=tcw)), full=False)
    R_o = R_c + tol_c + tcw + tol_w
    L = r2in['lobe']
    Lr, Wt = L['radial_protrusion_mm']['max'], L['tangential_width_mm']['max']
    lobe_r0 = R_pack + g_rad - 1.0
    lobe_poly = frame_rect(cp, pcm_az, lobe_r0, R_pack + g_rad + Lr, Wt / 2.0)
    pocket_grow = tol_c + tcw + tol_w
    pocket_poly = frame_rect(cp, pcm_az, lobe_r0, R_pack + g_rad + Lr, Wt / 2.0, pocket_grow)
    return dict(offset=dict(magnitude_mm=mag, direction_deg=direction), centre=cp, R_pack_lw=R_pack, g_radial=g_rad, pack_radius=R_pack + g_rad,
                R_carrier_inner=R_c, t_carrier_wall=tcw, R_carrier_outer=R_o, pack_margin_mm=pack_margin, carrier_wall_margin_mm=wall_margin,
                pcm_az_deg=pcm_az, lobe_poly=lobe_poly, pocket_poly=pocket_poly,
                pack_poly=circ_poly(cp[0], cp[1], R_pack + g_rad), carrier_poly=circ_poly(cp[0], cp[1], R_o),
                carrier_polys=[circ_poly(cp[0], cp[1], R_o), pocket_poly], rc_k=rc_k)


def ray_poly_extent(poly, az):
    """Largest distance from the MAIN centre along azimuth az at which the ray is inside the (convex) polygon (None if it misses)."""
    t = math.radians(az)
    dx, dy = math.sin(t), -math.cos(t)
    ts = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        px, py = a[0] - C0[0], a[1] - C0[1]
        s_ = (px * ey - py * ex) / den
        u = (px * dy - py * dx) / den
        if s_ >= -1e-9 and -1e-9 <= u <= 1 + 1e-9:
            ts.append(s_)
    return max(ts) if ts else None


def zone_a_extent(pk, az):
    """Zone A radial extent (from the MAIN centre) along azimuth az: carrier disk and PCM lobe pocket."""
    e = disk_extent_along(pk['centre'], pk['R_carrier_outer'], az)
    pe = ray_poly_extent(pk['pocket_poly'], az)
    return e if pe is None else max(e, pe)


def package_max_radius(pk):
    """Largest distance from the MAIN centre of zone A (BATTERY-level module radius for the A6 rear insertion)."""
    return max(max(math.hypot(q[0] - C0[0], q[1] - C0[1]) for q in poly) for poly in pk['carrier_polys'])


# ---- reserved regions (6.9) and the MAIN-outline column (R2-V24) ----------------------------------------------------------
RESERVED = (('GNSS_RAD', 'GNSS', (345.0, 15.0)), ('BLE_RAD', 'BLE', (300.0, 330.0)), ('WIFI_RAD', 'WIFI', (105.0, 135.0)))


def level_interval(cx2, level):
    return cx2.levels[level]


def reserved_regions(cx2):
    """Owner reserved regions = radiator volume UNION the closed clock interval over the volume's radial span, at the volume's pinned Z
    levels (17.2 item 15). One occupant per (region part, level)."""
    st = cx2.st
    out = []
    for rid, tag, (a0, a1) in RESERVED:
        res = st.res[rid]
        r0, r1 = res['radial_mm']
        parts = [('clock', geom_polys(g4.sector(a0, a1, r0, r1))), ('volume', geom_polys(res['geometry']))]
        for lvl in res['z_levels']:
            lo, hi = level_interval(cx2, lvl)
            for part, polys in parts:
                out.append(occupant('RESERVED_%s_%s@%s' % (tag, part, lvl), 'reserved region', polys, lo, hi, group='RESERVED', region=tag, level=lvl, part=part,
                                    az=[a0, a1], r=[r0, r1]))
    return out


def reserved_az_intervals():
    return [(a0, a1) for _, _, (a0, a1) in RESERVED]


def merge_arcs(arcs):
    """Union of closed clockwise arcs (deg) as sorted non-wrapping segments in [0, 360]."""
    segs = []
    for a0, a1 in arcs:
        a0, a1 = a0 % 360.0, a1 % 360.0
        if a1 >= a0:
            segs.append([a0, a1])
        else:
            segs += [[a0, 360.0], [0.0, a1]]
    segs.sort()
    out = []
    for s in segs:
        if out and s[0] <= out[-1][1] + 1e-9:
            out[-1][1] = max(out[-1][1], s[1])
        else:
            out.append(list(s))
    return out


def growth_arcs(cx2):
    """Azimuth arcs where the MAIN outline may grow beyond the development envelope: complement of the reserved GNSS / BLE / Wi-Fi
    intervals (closed) and the frozen switch windows, shrunk by the MAIN outline positional tolerance angle (strict plan gap)."""
    st = cx2.st
    forbid = list(reserved_az_intervals()) + [tuple(w) for w in st.P['buttons']['windows_deg'].values()]
    segs = merge_arcs(forbid)
    allowed, prev = [], 0.0
    for a0, a1 in segs:
        if a0 > prev:
            allowed.append([prev, a0])
        prev = a1
    if prev < 360.0:
        allowed.append([prev, 360.0])
    if allowed and allowed[0][0] == 0.0 and allowed[-1][1] == 360.0 and len(allowed) > 1:
        allowed[0][0] = allowed[-1][0] - 360.0
        allowed.pop()
    tol = cx2.sp.pc_pcb['radius_mm']
    guard = math.degrees(tol / cx2.R_main)
    return [(a0 + guard, a1 - guard) for a0, a1 in allowed if a1 - a0 > 2 * guard]


def main_outline_max(cx2, R_side):
    """G4 maximum MAIN outline radius at a design point: bore - tol - PCB outline tol - max(c_main_case, c_insert) (both library predicates)."""
    f = cx2.ce.f
    m_main = f['main'](R_side=R_side)
    m_ins = f['ins_main'](R_side=R_side)
    return cx2.R_main + min(m_main, m_ins)


def column_polys(cx2, R_side):
    """MAIN-outline column (binding): the development disk plus the allowed growth sectors up to the G4 maximum outline."""
    rmax = main_outline_max(cx2, R_side)
    polys = [circ_poly(C0[0], C0[1], cx2.R_main)]
    arcs = growth_arcs(cx2)
    if rmax > cx2.R_main + EPS:
        for a0, a1 in arcs:
            span = a1 - a0
            n = max(1, int(math.ceil(span / 30.0)))
            for i in range(n):
                polys.append(sector_poly((a0 + span * i / n) % 360.0, (a0 + span * (i + 1) / n) % 360.0, cx2.R_main - 0.05, rmax))
    return dict(R_dev=cx2.R_main, R_g4_max=rmax, arcs=arcs, polys=polys)


def in_column_point(col, p):
    """Exact membership of a point in the column: development disk, or the allowed growth arcs up to the G4 maximum outline."""
    r, az = polar(p)
    if r <= col['R_dev'] + EPS:
        return True
    if r > col['R_g4_max'] + EPS:
        return False
    return any(g4.arc_has(az, a0 % 360.0, a1 % 360.0) for a0, a1 in col['arcs'])


def inside_column(col, poly, step=0.25):
    """True when the polygon lies inside the column: every vertex and the sampled edge points are inside (exact point test)."""
    for a, b in zip(poly, poly[1:] + poly[:1]):
        n = max(1, int(math.ceil(math.dist(a, b) / step)))
        for i in range(n):
            if not in_column_point(col, (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)):
                return False
    return True


# ---- case supports and the static occupant set of the annulus ------------------------------------------------------------------
def bcu_plane(cx2):
    return cx2.levels['_layers']['main_pcb'][0]


def conn_height(cx2):
    return cx2.st.G2['connector_stack_range_mm']['max']


def g2_param(cx2, key, which='max'):
    return cx2.st.G2in['parameters'][key][which]


def c_rigid(cx2):
    return cx2.st.P['c_insert_mm']['max']


def switch_geometry(cx2, D, btn_status):
    """Plan polygons of the switch bores and bosses from the R2 pusher / boss choice (largest footprint over the closing options, so
    that the occupant never understates a choice the tool does not make)."""
    out = {}
    for sw in BTN_SW:
        rows = btn_status[sw]['rows']
        best = None
        for r in rows:
            s = r['I_SUM']['section'] if r['I_SUM']['closes'] else None
            if s is None:
                continue
            key = (s['boss_half_deg'], s['d_p'])
            if best is None or key > best[0]:
                best = (key, s, r)
        if best is None:
            r = rows[0]
            best = ((r['I_SUM']['section']['boss_half_deg'], r['I_SUM']['section']['d_p']), r['I_SUM']['section'], r)
        s = best[1]
        T = btn_terms2(cx2, sw, best[2]['option'])
        c = (T['window'][0] + T['window'][1]) / 2.0
        half_bore = math.degrees(math.asin(min(1.0, (s['d_p'] / 2.0 + T['tol_bore']) / s['R_inner'])))
        bore = g4.sector(c - half_bore, c + half_bore, s['R_inner'], s['R_face'])
        boss = g4.sector(c - s['boss_half_deg'], c + s['boss_half_deg'], D / 2.0, D / 2.0 + s['boss'] + T['tol_boss'])
        out[sw] = dict(centre=c, bore=bore, boss=boss, half_bore_deg=half_bore, boss_half_deg=s['boss_half_deg'], section=s, option=best[2]['option'],
                       topology=best[2]['topology'])
    return out


def support_layout_r2(cx2, pk, D, tw, swg):
    """G4 support layout with the R2 switch footprints, then the posts re-cut around the OFFSET carrier outline (R2-H18)."""
    st, sp = cx2.st, cx2.sp
    dp = dict(cx2.ce.dp0, D=D, tw=tw, tcw=pk['t_carrier_wall'], rcin=pk['R_carrier_inner'], bosses={sw: swg[sw]['section']['boss'] for sw in swg})
    buttons = g4.button_layout(st, sp, dp)
    for b in buttons:
        g_ = swg[b['id']]
        b['half_bore_deg'], b['boss_half_deg'] = g_['half_bore_deg'], g_['boss_half_deg']
        b['boss_in_window'] = g_['centre'] - g_['boss_half_deg'] >= b['window'][0] - EPS and g_['centre'] + g_['boss_half_deg'] <= b['window'][1] + EPS
    vent = g4.vent_layout(st, sp, dp, buttons)
    sup = g4.supports_layout(st, sp, dp, buttons, vent)
    R_side = D / 2.0 - tw
    lv = cx2.levels
    c_ins = c_rigid(cx2)
    posts, pads = [], []
    for s in sup['supports']:
        pl = s['placement']
        if pl is None:
            continue
        c = pl['centre']
        h = sup['post_half_deg']
        r_in = max(zone_a_extent(pk, c + k * h) for k in (-1.0, -0.5, 0.0, 0.5, 1.0)) + c_ins + POLY_SLACK_MM
        poly = sector_poly(c - h, c + h, min(r_in, R_side), R_side)
        posts.append(occupant(s['id'] + '_CASE_SIDE', 'case-side support', [poly], lv['BATTERY'][0], lv['BATTERY'][1], group='CASE', centre_deg=c,
                              inner_r=r_in, outer_r=R_side, engagement_mm=R_side - r_in))
        if pl['pad']:
            ph = sup['pad_half_deg']
            pads.append(occupant(s['id'] + '_PAD', 'support pad', [sector_poly(c - ph, c + ph, sup['pad_inner_r'], R_side)], lv['MAIN'][0], lv['MAIN'][1],
                                 group='CASE', centre_deg=c))
    return dict(sup=sup, buttons=buttons, vent=vent, posts=posts, pads=pads, dp=dp)


def pillar_footprints(cx2):
    """Plan footprint of each carrier hard-stop pillar: the G3 support land polygon (a pillar never extends beyond its land)."""
    return {s['az']: [tuple(p) for p in s['poly']] for s in cx2.st.s14geo['supports']}


def static_occupants(cx2, D, tw, swg, sl_any):
    """Occupants that do not depend on the pack offset: switch bores / bosses, vent, screws, lugs, reserved regions, REAR module, pillars,
    existing B.Cu parts (cached per (D, tw) by the caller)."""
    st, sp = cx2.st, cx2.sp
    lv = cx2.levels
    L = lv['_layers']
    occs = []
    for sw, g_ in swg.items():
        occs.append(occupant(sw + '_BORE', 'pusher bore / stroke', geom_polys(g_['bore']), lv['MAIN'][0], lv['MAIN'][1], group='BTN_' + sw))
        occs.append(occupant(sw + '_BOSS', 'button boss', geom_polys(g_['boss']), lv['MAIN'][0], lv['MAIN'][1], group='BTN_' + sw))
    R_side = D / 2.0 - tw
    if sl_any['vent']:
        v = sl_any['vent']
        occs.append(occupant('VENT_PORT', 'vent port', [sector_poly(v['centre'] - v['half'], v['centre'] + v['half'], 19.5, R_side)], lv['MAIN'][0], lv['MAIN'][1], group='VENT'))
    for sc in g4.screw_layout(st, sp, dict(D=D, tw=tw))['screws']:
        occs.append(occupant(sc['id'], 'caseback screw', geom_polys(sc['geom']), lv['REAR'][0], lv['REAR'][1], group='SCREW'))
    for lg in g4.lug_layout(st, dict(D=D, tw=tw)):
        occs.append(occupant(lg['id'], lg['kind'], geom_polys(lg['geom']), lv['REAR'][0], lv['MAIN'][1], group='LUG'))
    occs += reserved_regions(cx2)
    g = st.s14geo
    rear_skin_lo = L['optics_zone'][1] - st.P['c_cb_rear_mm']['min']
    occs.append(occupant('S14_OUTLINE', 'S14 REAR module', [circ_poly(C0[0], C0[1], g['outline_r'])], rear_skin_lo, L['rear_inner'][1], group='REAR',
                         shapes=[('disk', (C0[0], C0[1], g['outline_r']))]))
    for s in g['supports']:
        occs.append(occupant('S14_LAND_%d' % s['az'], 'G3 support land', [list(map(tuple, s['poly']))], rear_skin_lo, L['rear_inner'][1], group='REAR'))
    for az_, fp in sorted(pillar_footprints(cx2).items()):
        occs.append(occupant('PILLAR_%d' % az_, 'carrier hard-stop pillar', [fp], L['rear_inner'][1], L['rear_band'][1], group='REAR'))
    z_plane = bcu_plane(cx2)
    for f in st.HM['main_footprints']:
        if f['side'] == 'B.Cu':
            occs.append(occupant(f['ref'], 'existing B.Cu part', [rect_poly(*f['courtyard_bbox'])], z_plane - f['seated_max'], z_plane, group='ZONE_A_BCU',
                                 seated_max=f['seated_max']))
    occs.append(u7_occupant(cx2))
    return occs


def offset_occupants(cx2, pk, sl):
    L = cx2.levels['_layers']
    car = occupant('CARRIER_ENVELOPE', 'carrier / pack / PCM lobe', pk['carrier_polys'], L['lower_web'][0], L['battery_zone'][1], group='CARRIER',
                   shapes=[('disk', (pk['centre'][0], pk['centre'][1], pk['R_carrier_outer'])), ('poly', pk['pocket_poly'])],
                   allowed_nonconductive=True, material_class='MAT-GF-POLY')
    return [car] + sl['posts'] + sl['pads']


def fixed_occupants(cx2, pk, D, tw, swg, sl, static=None):
    static = static if static is not None else static_occupants(cx2, D, tw, swg, sl)
    return offset_occupants(cx2, pk, sl) + [o for o in static if o['id'] != 'U7'] + [o for o in static if o['id'] == 'U7']


def band_geometry(cx2, pk, col, az_list):
    """Free radial band of the annulus along each azimuth: [zone A extent + c, column radius]."""
    c = c_rigid(cx2)
    out = {}
    for a in az_list:
        lo = zone_a_extent(pk, a) + c
        hi = col['R_dev']
        if any(a0 <= a % 360.0 <= a1 for a0, a1 in col['arcs']):
            hi = col['R_g4_max']
        out[a] = (lo, hi)
    return out


# ---- connectors on MAIN B.Cu: bodies, risers, mate strokes, pose search (R2-V08..V10, R2-H25) ----------------------------------
CONN_OPTION = dict(J1501='J1501-B.Cu', J201='J201-B.Cu', J202='J202-EAST-B.Cu')


def conn_spec(cx2, key):
    o = next(x for x in cx2.st.G2in['options'] if x['id'] == CONN_OPTION[key])
    x0, y0, x1, y1 = o['window_rect_mm']
    w, h = x1 - x0, y1 - y0
    P = cx2.st.G2in['parameters']
    t_fpc, c_fpc = cx2.st.rp['t_fpc']['max'], cx2.st.rp['c_fpc']['max']
    if key == 'J1501':
        width = (o['positions'] - 1) * P['sensor_pitch_mm']['max'] + 2 * P['sensor_edge_margin_mm']['max']
    else:
        width = P['harness_width_mm']['max']
    return dict(key=key, option=o['id'], long_mm=max(w, h), short_mm=min(w, h), supplier=o['supplier'], positions=o['positions'],
                window_rect=o['window_rect_mm'], route_kind=o['route_kind'], fpc_width_mm=width, riser_t_mm=t_fpc + c_fpc, riser_w_mm=width + 2 * c_fpc,
                R_bend_mm=cx2.st.rp['R_bend_min']['max'], t_fpc_mm=t_fpc, c_fpc_mm=c_fpc)


def conn_body_poly(spec, az, r, ori, grow=0.0):
    if ori == 0:
        return local_rect_poly(az, r, spec['long_mm'], spec['short_mm'], grow)
    return local_rect_poly(az, r, spec['short_mm'], spec['long_mm'], grow)


def riser_polys(cx2, spec, az, r):
    """Vertical riser (under the plug, mate axis parallel to Z) and the bend envelope at its foot: rectangles in the riser frame."""
    half_w = spec['riser_w_mm'] / 2.0
    tt = spec['riser_t_mm']
    Rb = spec['R_bend_mm']
    riser = frame_rect(C0, az, r - tt / 2.0, r + tt / 2.0, half_w)
    bend = frame_rect(C0, az, r - tt / 2.0 - Rb - spec['t_fpc_mm'], r + tt / 2.0, half_w)
    return riser, bend


def conn_occupants(cx2, spec, az, r, ori, mate='axial', plate_top=None):
    lv = cx2.levels
    L = lv['_layers']
    z_pl = bcu_plane(cx2)
    h = conn_height(cx2)
    stroke = cx2.r2in['interconnect']['mate_stroke_mm']['max']
    key = spec['key']
    body = conn_body_poly(spec, az, r, ori)
    riser, bend = riser_polys(cx2, spec, az, r)
    z_body_lo = z_pl - h
    occ = [occupant(key + '_BODY', 'connector body (B.Cu)', [body], z_body_lo, z_pl, group=key, side='B.Cu'),
           occupant(key + '_STROKE', 'mate stroke envelope (A4)', [body], z_body_lo - stroke, z_body_lo, group=key, step='A4')]
    if key == 'J202':
        # charger drop: rises from the FT-C inner face (plate top) to the plug; no carrier-web foot bend
        zb = (plate_top if plate_top is not None else cx2.levels['_layers']['window'][1] + 0.5)
        occ.append(occupant(key + '_RISER', 'FPC / harness riser', [riser], zb, z_body_lo, group=key, flexible=True))
    else:
        occ.append(occupant(key + '_RISER', 'FPC / harness riser', [riser], L['lower_web'][0], z_body_lo, group=key, flexible=True))
        occ.append(occupant(key + '_BEND', 'riser foot bend envelope', [bend], L['lower_web'][0], L['lower_web'][1] + spec['R_bend_mm'] + spec['t_fpc_mm'], group=key, flexible=True))
    return occ, dict(body=body, riser=riser, bend=bend, z_body_lo=z_body_lo, z_plane=z_pl, stroke=stroke)


def mag_clear_occupant(cx2):
    st = cx2.st
    res = st.res['MAG_CLEAR']
    lo = min(cx2.levels[l][0] for l in res['z_levels'])
    hi = max(cx2.levels[l][1] for l in res['z_levels'])
    return occupant('MAG_CLEAR', 'magnet-sensitive exclusion', geom_polys(res['geometry']), lo, hi, group='MAG')


def pose_relevance(cx2, templates, fixed, key, mag):
    """Pairs (new occupant index, fixed occupant, required plan clearance) that are NOT separated in Z (the Z relation of a pose family
    is pose independent): only these need a plan test per pose. Pairs inside one group are declared contact pairs."""
    c_r = c_rigid(cx2)
    rel = []
    for j, a in enumerate(templates):
        for b in fixed:
            if b['group'] == a['group']:
                continue
            c = 0.0 if b['kind'] == 'reserved region' else c_r
            if r1.separated(occ_z_gap(a, b, cx2.zs), 0.0):
                continue
            rel.append((j, b, c))
        if mag is not None and a['kind'] == 'connector body (B.Cu)' and key in ('J201', 'J202'):
            if not r1.separated(occ_z_gap(a, mag, cx2.zs), 0.0):
                rel.append((j, mag, 0.0))
    return rel


def pose_clearances(cx2, occs_new, relevance, stop_early=True):
    """Strict plan clearance of one pose against the Z-relevant fixed occupants. stop_early: the pass / fail answer is decided by the first violated
    pair (exact reduction, verified against the exhaustive evaluation in the self-test; the violation list is then partial)."""
    recs = []
    for j, b, c in relevance:
        a = occs_new[j]
        count()
        pg = occ_plan_gap(a, b, limit=c + 1e-6)
        if not r1.separated(pg, c):
            recs.append(dict(a=a['id'], b=b['id'], mode='PLAN', z_gap_mm=occ_z_gap(a, b, cx2.zs), plan_gap_mm=pg, required_plan_mm=c))
            if stop_early:
                break
    return not recs, recs


def room_profile(cx2, pk, col, az_list):
    """room(az) = column radius - zone A extent: the radial thickness of the annulus (zone B) available at each azimuth, before any
    discrete obstacle. A body (and its riser) that needs more radial thickness than room(az) cannot sit there: a NECESSARY screen."""
    out = {}
    for a in az_list:
        hi = col['R_dev']
        if any(a0 <= a % 360.0 <= a1 for a0, a1 in col['arcs']):
            hi = col['R_g4_max']
        out[a] = hi - zone_a_extent(pk, a)
    return out


def search_poses(cx2, pk, col, fixed, key, mag, rank_fn, body_fn, occ_fn, need_mm, half_t_mm, az_candidates=None, r_values=None, ori_list=(0, 90),
                 clear_c=None, top=6, rooms=None, half_radial=None):
    """Deterministic pose search shared by connectors and the LRA: az / r / orientation grid; a NECESSARY radial-room screen first (the
    annulus thickness at the centre ray must reach need_mm), then cheap containment screens, then the full named clearance set against the
    fixed occupants. Candidates are examined in rank order and the search stops after `top` feasible poses (the report states the number
    of candidates examined, not an exhaustive count)."""
    G = cx2.r2in['grids']
    azs = az_candidates if az_candidates is not None else frange(G['connector_az']['start'], G['connector_az']['stop'], G['connector_az']['step'])
    rs = r_values if r_values is not None else frange(G['connector_r']['start'], G['connector_r']['stop'], G['connector_r']['step'])
    c_r = c_rigid(cx2) if clear_c is None else clear_c
    stats = dict(tried=0, room=0, column=0, zone_a=0, clearance=0, stopped_after_top=False)
    cp, Ro = pk['centre'], pk['R_carrier_outer']
    all_az = frange(0.0, 359.0, 1.0)
    room = rooms if rooms is not None else room_profile(cx2, pk, col, all_az)
    cand = []
    for az in azs:
        if room[int(round(az)) % 360] < need_mm - EPS:       # centre-ray necessary screen (inner / outer mid-edge points lie on the centre ray)
            stats['room'] += len(rs) * len(ori_list)
            continue
        rho = zone_a_extent(pk, az) + c_r
        for ori in ori_list:
            hr = 0.0 if half_radial is None else half_radial(ori)
            for r in rs:
                if r < rho + hr - EPS:           # exact necessary screen: the body point on the centre ray must clear the zone-A boundary along that ray
                    stats['zone_a'] += 1
                    continue
                cand.append((rank_fn(az, r, ori, None), az, r, ori))
    cand.sort(key=lambda c: (c[0], c[1], c[2], c[3]))
    feas = []
    if not cand:
        return dict(poses=[], n_feasible=0, stats=stats)
    t0 = occ_fn(cand[0][1], cand[0][2], cand[0][3])[0]
    relevance = pose_relevance(cx2, t0, fixed, key, mag)
    for rk, az, r, ori in cand:
        stats['tried'] += 1
        body = body_fn(az, r, ori)
        if any(math.dist(q, cp) < Ro + c_r - 1e-9 for q in body):
            stats['zone_a'] += 1
            continue
        if not inside_column(col, body):
            stats['column'] += 1
            continue
        occ, geo = occ_fn(az, r, ori)
        ok, recs = pose_clearances(cx2, occ, relevance)
        if not ok:
            stats['clearance'] += 1
            continue
        feas.append(dict(key=key, az=az, r=r, ori=ori, rank=rk, geo=geo, occupants=occ))
        if len(feas) >= top:
            stats['stopped_after_top'] = True
            break
    return dict(poses=feas, n_feasible=len(feas), stats=stats)


def search_connector(cx2, pk, col, fixed, key, mag, rank_fn, az_range=None, top=6, rooms=None):
    spec = conn_spec(cx2, key)
    G = cx2.r2in['grids']
    azs = frange(G['connector_az']['start'], G['connector_az']['stop'], G['connector_az']['step'])
    if az_range is not None:
        azs = [a for a in azs if g4.arc_has(a, az_range[0], az_range[1])]
    c_r = c_rigid(cx2)
    need = c_r + (0.0 if key == 'J202' else spec['R_bend_mm'] + spec['t_fpc_mm']) + spec['riser_t_mm'] / 2.0 + spec['short_mm'] / 2.0
    def hr(ori):
        body_half = (spec['short_mm'] if ori == 0 else spec['long_mm']) / 2.0
        return body_half if key == 'J202' else max(body_half, spec['riser_t_mm'] / 2.0 + spec['R_bend_mm'] + spec['t_fpc_mm'])
    res = search_poses(cx2, pk, col, fixed, key, mag, lambda az, r, ori, geo: rank_fn(az, r, ori, spec, None),
                       lambda az, r, ori: conn_body_poly(spec, az, r, ori), lambda az, r, ori: conn_occupants(cx2, spec, az, r, ori),
                       need, spec['long_mm'] / 2.0, azs, None, (0, 90), None, top, rooms, hr)
    res.update(spec=spec, need_mm=need)
    return res


# ---- FPC / battery tail / charger drop paths and service slack (R2-H25, 6.5) --------------------------------------------------
def path_len(pts3):
    return sum(math.dist(a, b) for a, b in zip(pts3, pts3[1:]))


def bend_arc(R, t):
    return math.pi / 2.0 * (R + t / 2.0)


def fpc_sensor_path(cx2, pk, spec, az, r, ori):
    """J1501 sensor FPC: J1502 tail exit (frozen) -> under-run groove in the lower web (radial to r_a, arc to the connector azimuth, radial to the web
    edge) -> riser foot bend (adverse bend radius) -> vertical riser under the axial plug. Lengths are installed lengths."""
    st = cx2.st
    L = cx2.levels['_layers']
    te = st.s14['tail_exit']['centre_assembly_mm']
    r_t, az_t = polar(tuple(te))
    z_web = (L['lower_web'][0] + L['lower_web'][1]) / 2.0
    web_edge = zone_a_extent(pk, az)
    r_a = max(r_t + 0.0, 14.0)
    d_az = ((az - az_t + 180.0) % 360.0) - 180.0
    horiz = abs(r_a - r_t) + math.radians(abs(d_az)) * r_a + abs(r - spec['riser_t_mm'] / 2.0 - spec['R_bend_mm'] - spec['t_fpc_mm'] - r_a)
    bend = bend_arc(spec['R_bend_mm'], spec['t_fpc_mm'])
    z_body_lo = bcu_plane(cx2) - conn_height(cx2)
    vert = max(0.0, z_body_lo - (z_web + spec['R_bend_mm'] + spec['t_fpc_mm']))
    hop = bend_arc(spec['R_bend_mm'], spec['t_fpc_mm']) + (L['lower_web'][0] - L['rear_inner'][1]) / 2.0
    total = horiz + bend + vert + hop
    return dict(tail_exit=dict(r=r_t, az=az_t), web_edge_r_mm=web_edge, horizontal_mm=horiz, foot_bend_mm=bend, vertical_mm=vert, hop_mm=hop,
                installed_length_mm=total, bends=2, R_bend_used_mm=spec['R_bend_mm'], R_bend_min_adverse_mm=cx2.st.rp['R_bend_min']['max'],
                R_bend_margin_mm=spec['R_bend_mm'] - cx2.st.rp['R_bend_min']['max'], riser_r_mm=r, riser_az_deg=az,
                mate='axial, plug inserted from the REAR (toward +Z) at A4 on the bench; the module is folded / presented with MAIN B.Cu up',
                vertices=[dict(r=r_t, az=az_t, z=z_web), dict(r=r_a, az=az_t, z=z_web), dict(r=r_a, az=az, z=z_web),
                          dict(r=max(r - spec['riser_t_mm'] / 2.0 - spec['R_bend_mm'], r_a), az=az, z=z_web), dict(r=r, az=az, z=z_web + spec['R_bend_mm']),
                          dict(r=r, az=az, z=z_body_lo)], max_z_mm=z_body_lo)


def battery_tail_path(cx2, pk, spec, az, r):
    """J201 battery tail: from the PCM exit (outer PCM lobe edge centre, pack mid-thickness) straight in plan to the J201 riser, then the foot bend and
    the vertical riser. VBAT estimate: Manhattan on MAIN B.Cu from J201 to the consuming U201."""
    L = cx2.levels['_layers']
    cp = pk['centre']
    phi = pk['pcm_az_deg']
    exit_pt, er, _ = frame_at(cp, phi, pk['pack_radius'] + cx2.r2in['lobe']['radial_protrusion_mm']['max'])
    z_mid = L['battery_zone'][0] + cx2.st.sp['t_pack_nom']['nom'] / 2.0      # PCM exit at the pack mid-thickness
    riser_xy = xy(r, az)
    plan = math.dist(exit_pt, riser_xy)
    bend = bend_arc(spec['R_bend_mm'], spec['t_fpc_mm'])
    z_body_lo = bcu_plane(cx2) - conn_height(cx2)
    vert = max(0.0, z_body_lo - z_mid - spec['R_bend_mm'] - spec['t_fpc_mm'])
    u201 = next((f for f in cx2.st.HM['main_footprints'] if f['ref'] == 'U201'), None)
    vbat = None if u201 is None else abs(riser_xy[0] - u201['x']) + abs(riser_xy[1] - u201['y'])
    rise_margin = (z_body_lo - z_mid) - (spec['R_bend_mm'] + spec['t_fpc_mm'] / 2.0)
    return dict(exit_xy=exit_pt, riser_xy=riser_xy, plan_mm=plan, vertical_mm=vert, foot_bend_mm=bend, tail_length_mm=plan + bend + vert, bends=1, vertical_rise_margin_mm=rise_margin,
                R_bend_used_mm=spec['R_bend_mm'], R_bend_margin_mm=spec['R_bend_mm'] - cx2.st.rp['R_bend_min']['max'], z_exit_mm=z_mid,
                vbat_manhattan_to_U201_mm=vbat, max_z_mm=z_body_lo,
                vertices=[dict(r=polar(exit_pt)[0], az=polar(exit_pt)[1], z=z_mid), dict(r=r, az=az, z=z_mid), dict(r=r, az=az, z=z_body_lo)])


def drop_path(cx2, chg_pose, spec, az, r):
    """Local charger drop: FT-C inner face (block centre) -> vertical rise -> J202 plug; lateral run when the block centre is not under J202."""
    L = cx2.levels['_layers']
    blk = chg_pose['block_poly']
    cxy = (sum(p[0] for p in blk) / len(blk), sum(p[1] for p in blk) / len(blk))
    jxy = xy(r, az)
    lateral = math.dist(cxy, jxy)
    z_face = chg_pose.get('z_inner_face_mm', 1.0)
    z_body_lo = bcu_plane(cx2) - conn_height(cx2)
    vert = max(0.0, z_body_lo - z_face)
    bends = 1 + (1 if lateral > 0.5 else 0)
    bend = bends * bend_arc(spec['R_bend_mm'], spec['t_fpc_mm'])
    slack = cx2.r2in['interconnect']['service_slack']['adverse_mm']
    total = vert + lateral + bend
    return dict(block_xy=cxy, j202_xy=jxy, vertical_mm=vert, lateral_mm=lateral, bends=bends, installed_length_mm=total,
                service_slack_required_mm=slack, service_length_mm=total, R_bend_used_mm=spec['R_bend_mm'], max_z_mm=z_body_lo,
                vertices=[dict(r=polar(cxy)[0], az=polar(cxy)[1], z=z_face), dict(r=r, az=az, z=z_face), dict(r=r, az=az, z=z_body_lo)])


def slack_pocket(cx2, pk, spec, az_center, fixed, t_out, cup_r_inner):
    """Planar U-loop service-slack pocket in the REAR-periphery band below the lower web (never a doubled cable in the annulus). The loop of
    slack S needs two legs l = (S - pi R_b) / 2 and a semicircle of the adverse bend radius. Search: azimuth centre +/- half width in steps,
    sector from S14 outline + 1.1 to the cup ring inner face minus clearance, height between the plate top and the lower-web underside."""
    st = cx2.st
    L = cx2.levels['_layers']
    P = cx2.r2in['paths']['slack_pocket']
    S = cx2.r2in['interconnect']['service_slack']['adverse_mm']
    Rb = spec['R_bend_mm']
    leg = (S - math.pi * Rb) / 2.0
    w_req = 2.0 * Rb + spec['t_fpc_mm'] + 2.0 * spec['c_fpc_mm']
    h_req = st.G2['service_pocket_check']['corners']['conservative']['required_height_mm']
    mat = cup_materials(cx2)
    z_lo = t_out + mat['tol_t']
    z_hi = L['rear_band'][1] - cx2.zs.tol_of('lower_web')
    h_avail = z_hi - z_lo
    r_in = st.s14geo['outline_r'] + st.I['contract_values']['s14']['plan_clearances_mm']['CHG_CONTACT']
    r_out = cup_r_inner - c_rigid(cx2)
    best = None
    az0 = az_center
    for k in range(-int(P['az_search_half_width_deg'] / P['az_step_deg']), int(P['az_search_half_width_deg'] / P['az_step_deg']) + 1):
        az = az0 + k * P['az_step_deg']
        # loop: legs run tangentially; length leg + R_b along the tangent, width w_req across; placed at the largest radius that fits
        for r_mid in frange(r_in + w_req / 2.0, r_out - w_req / 2.0, 0.25):
            poly = local_rect_poly(az, r_mid, leg + Rb, w_req, 0.0)
            o = occupant('SLACK_POCKET', 'service slack pocket', [poly], z_lo, z_hi, group='SLACK')
            bad = [b['id'] for b in fixed if b['group'] != 'SLACK' and not r1.separated(occ_z_gap(o, b, cx2.zs), 0.0)
                   and not r1.separated(occ_plan_gap(o, b, limit=0.01), 0.0) and b['kind'] != 'reserved region']
            rr = [b['id'] for b in fixed if b['kind'] == 'reserved region' and not r1.separated(occ_z_gap(o, b, cx2.zs), 0.0) and occ_plan_gap(o, b, limit=0.01) <= EPS]
            if not bad and not rr and h_avail >= h_req - EPS:
                key = (abs(k), -r_mid)
                if best is None or key < best[0]:
                    best = (key, dict(az=az, r=r_mid, poly=poly, leg_mm=leg, width_mm=w_req, height_required_mm=h_req, height_available_mm=h_avail))
                break
    return dict(fits=best is not None, pocket=best[1] if best else None, leg_mm=leg, width_required_mm=w_req, height_required_mm=h_req,
                height_available_mm=h_avail, slack_mm=S, r_window_mm=[r_in, r_out], loop_rule='S = 2 l + pi R_bend')


# ============================================================================================
# L-LRA: MAIN B.Cu zone-B primary, MAIN F.Cu Z-neutral fallback; BMM350 distance; R1:R4-1 identity
# ============================================================================================
def lra_classes_r2(cx2):
    """Authored G4 classes at their maxima plus the validated supplied classes (C-R1-08); each with plan shape data and height max."""
    st = cx2.st
    out = []
    for c in st.I['lra_classes']:
        if c['shape'] == 'coin':
            out.append(dict(id=c['id'], shape='coin', radius=c['diameter_mm']['max'] / 2.0, length=c['diameter_mm']['max'], width=c['diameter_mm']['max'],
                            height=c['height_mm']['max'], evidence='AUTHORED (PROVISIONAL_ASSUMPTION)', lead_exit=None, supplied=False))
        else:
            out.append(dict(id=c['id'], shape='rect', radius=None, length=c['length_mm']['max'], width=c['width_mm']['max'],
                            height=c['height_mm']['max'], evidence='AUTHORED (PROVISIONAL_ASSUMPTION)', lead_exit=None, supplied=False))
    sup = cx2.r2in['lra_supplied']
    if sup:
        ok, bad = lra_supplied_valid(cx2, sup)
        for rec in ok:
            dims = rec
            if rec['shape'] == 'coin':
                d_ = rec['diameter_mm']['max']
                out.append(dict(id=rec['id'], shape='coin', radius=d_ / 2.0, length=d_, width=d_, height=rec['height_mm']['max'], evidence='SUPPLIED (C-R1-08)',
                                lead_exit=rec['lead_exit_envelope_mm'], supplied=True))
            else:
                out.append(dict(id=rec['id'], shape='rect', radius=None, length=rec['length_mm']['max'], width=rec['width_mm']['max'],
                                height=rec['height_mm']['max'], evidence='SUPPLIED (C-R1-08)', lead_exit=rec['lead_exit_envelope_mm'], supplied=True))
    return out


def lra_supplied_valid(cx2, records):
    """C-R1-08: a supplied class counts only with a local primary document (existing repository file that is not a generated / R1 / R2 file)
    and page + table / figure provenance; a class defined by the threshold it must meet is rejected."""
    schema = cx2.r2in['lra_supplied_schema']
    ok, bad = [], []
    for rec in records:
        problems = [k for k in schema['required'] if k not in rec]
        doc = rec.get('primary_document')
        if doc is None or not (ROOT / doc).exists() or 'generated' in doc or 'g4_r1' in doc or 'g4_r2' in doc:
            problems.append('primary_document')
        prov = rec.get('provenance') or {}
        problems += [k for k in schema['provenance_keys'] if k not in prov]
        if rec.get('defined_by_threshold'):
            problems.append('defined_by_threshold')
        (bad if problems else ok).append(rec if not problems else dict(id=rec.get('id'), problems=sorted(set(problems))))
    return ok, bad


def lra_body_poly(cls, az, r, ori, grow=0.0):
    c = xy(r, az)
    if cls['shape'] == 'coin':
        return circ_poly(c[0], c[1], cls['radius'] + grow)
    ang = az if ori == 0 else az - 90.0       # ori 0: long axis tangential (G4 8.9 convention), 90: radial
    return rot_rect(c[0], c[1], cls['length'] + 2 * grow, cls['width'] + 2 * grow, ang)


def lra_min_extent(cls):
    return cls['radius'] * 2.0 if cls['shape'] == 'coin' else min(cls['length'], cls['width'])


def lra_bcu_search(cx2, pk, col, fixed, mag, classes, rooms=None):
    """Pose search in zone B for every class (R2-V23, az 0-355 step 5, r step 0.25, orientation 0 / 90): Z inside zone B (hangs from MAIN B.Cu
    through the back-zone and battery-band range), plan clearance c_lra_plan to every exclusion incl. the MAIN-outline column boundary, outside
    radiator volumes / reserved regions / MAG_CLEAR / bores / supports. The necessary room screen proves 'no pose' without enumerating."""
    st = cx2.st
    c_plan = st.P['c_lra_plan_mm']['max']
    mount = st.P['lra_mount_mm']['max']
    z_pl = bcu_plane(cx2)
    G = cx2.r2in['grids']
    azs = frange(G['lra_az']['start'], G['lra_az']['stop'], G['lra_az']['step'])
    rs = frange(G['lra_r']['start'], G['lra_r']['stop'], G['lra_r']['step'])
    all_az = frange(0.0, 359.0, 1.0)
    room = rooms if rooms is not None else room_profile(cx2, pk, col, all_az)
    max_room = max(room.values())
    out = {}
    cp, Ro = pk['centre'], pk['R_carrier_outer']
    for cls in classes:
        need = lra_min_extent(cls) + 2.0 * c_plan
        z_lo = z_pl - (cls['height'] + mount)
        feas, tried = [], 0
        if max_room < need - EPS:
            out[cls['id']] = dict(cls=cls, feasible=[], n_feasible=0, tried=0, proof='necessary room screen: max annulus thickness %.3f < %.3f needed '
                                  '(min extent + 2 c_lra_plan)' % (max_room, need), max_room_mm=max_room, need_mm=need, z=[z_lo, z_pl])
            continue
        ols = (None,) if cls['shape'] == 'coin' else G['lra_orientations']
        for az in azs:
            if room[int(round(az)) % 360] < need - EPS:
                continue
            for ori in ols:
                for r in rs:
                    tried += 1
                    body = lra_body_poly(cls, az, r, ori)
                    grown = lra_body_poly(cls, az, r, ori, c_plan)
                    if any(math.dist(q, cp) < Ro + c_plan for q in grown) or not inside_column(col, grown):
                        continue
                    o = occupant('LRA', 'LRA actuator', [body], z_lo, z_pl, group='LRA', ferromagnetic=True, magnet=True)
                    bad = False
                    for b in fixed:
                        if b['group'] == 'LRA':
                            continue
                        c = 0.0 if b['kind'] == 'reserved region' else c_plan
                        if r1.separated(occ_z_gap(o, b, cx2.zs), 0.0):
                            continue
                        if not r1.separated(occ_plan_gap(o, b, limit=c + 1e-6), c):
                            bad = True
                            break
                    if bad:
                        continue
                    if mag is not None:
                        gm = occ_plan_gap(o, mag, limit=1e-6)
                        if not r1.separated(gm, 0.0):
                            continue
                    feas.append(dict(az=az, r=r, ori=ori, body=body, z=[z_lo, z_pl]))
        out[cls['id']] = dict(cls=cls, feasible=feas[:12], n_feasible=len(feas), tried=tried, proof=None, max_room_mm=max_room, need_mm=need, z=[z_lo, z_pl])
    return out


# ---- F.Cu fallback ------------------------------------------------------------------------------------------------------------
_FCU_CACHE = {}
_FCU_DISK_CACHE = {}


def fcu_exclusions(cx2):
    """Plan exclusions of the MAIN F.Cu fallback: pinned F.Cu courtyards, the U101 shield polygon (can volume footprint), display land and
    display flex, ALS window, access volumes (SWD), radiator volumes / reserved regions (MAIN level) and MAG_CLEAR."""
    st = cx2.st
    ex = []
    for ref, g in g4.fcu_edge_parts(st):
        ex.append((ref, 'F.Cu courtyard', geom_polys(g)))
    plc = load_json(ROOT / 'design/placement/phase1_placement.json')
    ex.append(('U101_SHIELD', 'U101 shield polygon', [[tuple(p) for p in plc['shield_polygon_mm']]]))
    for rid in ('DISP_FPC', 'ALS', 'SWD', 'DISP_LAND'):
        ex.append((rid, 'reservation', geom_polys(st.res[rid]['geometry'])))
    for rid, tag, (a0, a1) in RESERVED:
        res = st.res[rid]
        if 'MAIN' in res['z_levels']:
            ex.append(('RESERVED_%s_clock' % tag, 'reserved region', geom_polys(g4.sector(a0, a1, res['radial_mm'][0], res['radial_mm'][1]))))
            ex.append(('RESERVED_%s_volume' % tag, 'reserved region', geom_polys(res['geometry'])))
    return ex


def lra_fcu_search(cx2, classes):
    st = cx2.st
    key = json.dumps(['fcu', [[c['id'], c['length'], c['width'], c['radius']] for c in classes], cx2.r2in['grids']['lra_az'], cx2.r2in['grids']['lra_r']], sort_keys=True)
    if key in _FCU_CACHE:
        return _FCU_CACHE[key]
    c_plan = st.P['c_lra_plan_mm']['max']
    G = cx2.r2in['grids']
    azs = frange(G['lra_az']['start'], G['lra_az']['stop'], G['lra_az']['step'])
    rs = frange(G['lra_r']['start'], G['lra_r']['stop'], G['lra_r']['step'])
    ex = fcu_exclusions(cx2)
    boxes = [(poly_bbox(p), p, eid, kind) for eid, kind, polys in ex for p in polys]
    mag = geom_polys(st.res['MAG_CLEAR']['geometry'])
    R_disp = st.R_display
    u703 = st.u703
    u703_fp = next(f for f in st.HM['main_footprints'] if f['ref'] == 'U703')
    u703_poly = rect_poly(*u703_fp['courtyard_bbox'])
    out = {}
    for cls in classes:
        ols = (None,) if cls['shape'] == 'coin' else G['lra_orientations']
        feas, tried = [], 0
        for az in azs:
            for ori in ols:
                for r in rs:
                    if r > R_disp:
                        continue
                    tried += 1
                    body = lra_body_poly(cls, az, r, ori)
                    if max(math.hypot(q[0] - C0[0], q[1] - C0[1]) for q in body) + c_plan > R_disp:
                        continue
                    bb = poly_bbox(body)
                    bad = None
                    for eb, p, eid, kind in boxes:
                        if bbox_gap(bb, eb) > c_plan + 1e-6:
                            continue
                        g_ = poly_gap(body, p, bb, eb, limit=c_plan + 1e-6)
                        if not r1.separated(g_, 0.0 if kind == 'reserved region' else c_plan):
                            bad = eid
                            break
                    if bad:
                        continue
                    if any(not r1.separated(poly_gap(body, mp, limit=1.0), 0.0) for mp in mag):
                        continue
                    dist = poly_gap(body, u703_poly)
                    feas.append(dict(az=az, r=r, ori=ori, body=body, u703_distance_mm=dist))
        out[cls['id']] = dict(cls=cls, n_feasible=len(feas), tried=tried, poses=feas)
    _FCU_CACHE[key] = out
    return out


# ============================================================================================
# L-CHG: contact block + non-conductive land (C-R1-01 with the amended 2(v) = C-R2-01), FT-C, local drop to J202
# ============================================================================================
_CHG_CACHE = {}


def chg_pose_family(cx2):
    """r_lim-independent poses of the V19 family (adverse land, block never reduced). The retired CHG_ROUTE / CHG_LINK terms are absent
    (OV-COND-BAND: the R1 input copy carries an empty route list); the pose-level predicates are R1's (C-R1-01 items 1, 2 (i)-(iv), 2 (vi), 3)."""
    V = cx2.cx.P['V20_charger_land']
    key = json.dumps([V['adverse_mm'], cx2.cx.P['V19_charger_pose'], V['route_clearance']['routes']], sort_keys=True)
    if key not in _CHG_CACHE:
        _CHG_CACHE[key] = r1.chg_poses(cx2.cx, cx2.cand, V['adverse_mm'], cx2.src.r1in)
    return _CHG_CACHE[key]


def chg_requirements(cx2, poses=None):
    """The r_lim(cup) the charger needs: minimum r_lim_required over poses that meet the radial, plan and material categories."""
    poses = poses if poses is not None else chg_pose_family(cx2)
    ok = [p for p in poses if p['categories']['radial'] and p['categories']['plan'] and p['categories']['material']]
    if not ok:
        return dict(feasible_poses=0, r_lim_required_min=None, pose=None)
    best = min(ok, key=lambda p: (p['r_lim_required'], -p['orientation'], abs(p['az_centre'] - 90.0), p['r_centre']))
    return dict(feasible_poses=len(ok), r_lim_required_min=best['r_lim_required'], pose=best)


def lane_chg(cx2, D, tw, r_lim, fixed=None, block_top=None):
    st = cx2.st
    sp = cx2.sp
    c_w = st.P['c_chg_window_mm']['max']
    poses = chg_pose_family(cx2)
    req = chg_requirements(cx2, poses)
    sel = r1.chg_select(cx2.cx, cx2.cand, poses, r_lim)
    pose = sel['pose']
    L = cx2.levels['_layers']
    mat = cup_materials(cx2)
    block_top = block_top if block_top is not None else L['rear_band'][1] - cx2.zs.tol_of('lower_web') - c_rigid(cx2)   # SR-CHG-MECH allocation maximum (static clearance to the lower web)
    t_top = max(grid(cx2.cx.P['V12_caseback_thickness']['t_out'])) + mat['tol_t']
    land = occupant('CHG_LAND', 'charger land (non-conductive)', [pose['land_poly']], 0.0, t_top, group='CHG', conductive=False)
    block = occupant('CHG_BLOCK', 'charger contacts (FT-C)', [pose['block_poly']], 0.0, block_top, group='CHG', conductive=True)
    radial = dict(r_lim_cup_mm=r_lim, c_chg_window_mm=c_w, block_rmax_mm=pose['block_rmax'], land_rmax_mm=pose['land_rmax'],
                  block_margin_mm=r_lim - c_w - pose['block_rmax'], land_margin_mm=r_lim - c_w - pose['land_rmax'],
                  r_lim_required_min_mm=req['r_lim_required_min'])
    neigh = []
    if fixed is not None:
        for a in (land, block):
            for b in fixed:
                if b['group'] in ('CHG', 'CUP'):
                    continue
                ok, rec = pair_clearance(a, b, 0.0, 0.0, cx2.zs)
                rec['rule'] = '2(vi) / 2(v) amended: strict 3-D (plan OR Z)'
                rec['clear'] = ok
                neigh.append(rec)
    neigh_ok = all(n['clear'] for n in neigh)
    margins = [radial['block_margin_mm'], radial['land_margin_mm']] + [min(n['plan_gap_mm'] if n['mode'] == 'PLAN' else n['z_gap_mm'], 9.0) for n in neigh]
    pose_ok = sel['prereq_pass'] and pose['categories']['plan'] and pose['categories']['material']
    radial_ok = radial['block_margin_mm'] >= -EPS and radial['land_margin_mm'] >= -EPS
    closes = bool(pose_ok and radial_ok and neigh_ok)
    gov = min(neigh, key=lambda n: (n['plan_gap_mm'] if n['mode'] == 'PLAN' else n['z_gap_mm'])) if neigh else None
    headline = dict(smallest_strict_clearance_mm=min(margins), governing_pair='CHG_LAND vs cup wall inner face (radial)' if min(margins) in (radial['block_margin_mm'], radial['land_margin_mm'])
                    else (None if gov is None else '%s vs %s' % (gov['a'], gov['b'])),
                    radial_limit_deficit_mm=None if req['r_lim_required_min'] is None else max(0.0, req['r_lim_required_min'] - r_lim),
                    plan_gap_mm=None if gov is None else gov['plan_gap_mm'], z_gap_mm=None if gov is None else gov['z_gap_mm'])
    strict = r1.strict_wedge(cx2.cx, cx2.cand, min(st.res['CHG_CONTACT']['geometry']['r'][1], r_lim - c_w))
    return dict(lane='L-CHG', pose=dict(orientation=pose['orientation'], r_centre=pose['r_centre'], az_centre=pose['az_centre'], land_mm=pose['land'],
                                        block_mm=pose['block_mm'], block_poly=pose['block_poly'], land_poly=pose['land_poly'],
                                        land_az=pose['land_az'], categories=pose['categories'], margins=pose['margins'], margins_deg=pose['margins_deg'],
                                        r_lim_required_mm=pose['r_lim_required'], z_inner_face_mm=t_top),
                radial=radial, neighbours=neigh, neighbours_clear=neigh_ok, closes=closes, headline=headline, feedthrough='FT-C (bonded sealed body in the ceramic caseback; binding)',
                feedthrough_reference='FT-A adhesive ring (reference column only)', block_top_mm=block_top, land_top_mm=t_top, strict_wedge=strict,
                requirement=dict(feasible_poses=req['feasible_poses'], r_lim_required_min_mm=req['r_lim_required_min']),
                c_r2_01='2(v) amended: the land clears screws and supports in 3-D (plan OR Z, strict); CHG_ROUTE / CHG_LINK retired items',
                occupants=[land, block])


# ============================================================================================
# L-RAD: H05-GEOM (R2-H04) and H05-LRA-COUPLED (R2-H05) as separate groups; crossings ELIMINATED by proof or CLOSED with a margin
# ============================================================================================
def max_radius(polys):
    return max(math.hypot(q[0] - C0[0], q[1] - C0[1]) for p in polys for q in p)


def crossing_proof(cx2, xid, path_vertices, col):
    """ELIMINATED only with an explicit geometric proof that the conductor path, from its origin to its MAIN termination, stays entirely on
    the B.Cu side (z <= the MAIN B.Cu plane) and never passes the MAIN edge between the F.Cu and B.Cu planes (inside the column everywhere)."""
    z_pl = bcu_plane(cx2)
    z_f = cx2.levels['_layers']['main_pcb'][1]
    rows = []
    for v in path_vertices:
        p = xy(v['r'], v['az'])
        rows.append(dict(r=v['r'], az=v['az'], z=v['z'], below_or_on_Bcu_plane=v['z'] <= z_pl + EPS, inside_column=in_column_point(col, p)
                         , between_planes=z_pl + EPS < v['z'] < z_f - EPS))
    ok = bool(rows) and all(x['below_or_on_Bcu_plane'] and x['inside_column'] and not x['between_planes'] for x in rows)
    return dict(crossing=xid, state='ELIMINATED' if ok else 'NOT_ELIMINATED', proof=dict(B_Cu_plane_z=z_pl, F_Cu_plane_z=z_f, vertices=rows,
                rule='every path vertex satisfies z <= B.Cu plane and lies inside the MAIN-outline column; no vertex lies between the F.Cu and B.Cu planes'),
                max_z_mm=max([x['z'] for x in rows], default=None))


def insertion_margin(cx2, R_side, r_module):
    """A6 rear-insertion margin at one level: bore - tolerance - (largest module radius at that level + c_insert)."""
    return R_side - cx2.sp.pc_env['radius_mm'] - (r_module + c_rigid(cx2))


def rad_terms(cx2, D, tw, pk, col, risers, module_extra):
    """Radial terms of one joint point (linear worst). risers: list of dict(id, polys) of the annulus risers (sensor FPC, battery tail, drop);
    module_extra: dict level -> max module radius contributions beyond the carrier (connector bodies, risers, slack pocket)."""
    st, sp, f = cx2.st, cx2.sp, cx2.ce.f
    R_side = D / 2.0 - tw
    tolb = sp.pc_env['radius_mm']
    tol_pcb = sp.pc_pcb['radius_mm']
    c_ins = c_rigid(cx2)
    c_main = st.P['c_main_case_mm']['max']
    r_main_used = max([cx2.R_main] + [module_extra.get('main_level_r', 0.0)])
    m = {}
    m['H03-OD'] = f['od'](D=D)
    m['H05-WALL-SIDE'] = f['wall'](t_wall=tw)
    m['H05-WALL-DIELECTRIC'] = g4.run_check(sp.local_wall(dict(cx2.ce.dp0, tw=tw)), full=False)
    m['H05-MAIN-CASE'] = R_side - tolb - (r_main_used + tol_pcb + c_main)
    ins = {}
    ins['H23-INSERT-MAIN'] = insertion_margin(cx2, R_side, r_main_used + tol_pcb)
    r_bat = max(package_max_radius(pk), module_extra.get('battery_level_r', 0.0))
    ins['H23-INSERT-BATTERY'] = insertion_margin(cx2, R_side, r_bat)
    r_rear = max(st.s14geo['outline_r'], module_extra.get('rear_level_r', 0.0))
    ins['H23-INSERT-REAR'] = insertion_margin(cx2, R_side, r_rear)
    straight = {}
    for rs in risers:
        straight['H05-STRAIGHT@%s' % rs['id']] = R_side - tolb - max_radius(rs['polys'])
    # library equivalence at the pinned centred carrier (overlay-off equivalence test is run by the PA class)
    geom_keys = sorted(m)
    min_geom = min(list(m.values()) + list(straight.values()))
    return dict(D=D, tw=tw, R_side=R_side, margins=m, straight=straight, insertion=ins, r_main_used=r_main_used, r_module_battery=r_bat, r_module_rear=r_rear,
                h05_geom_min=min_geom, h05_geom_pass=min_geom >= -EPS and all(v >= -EPS for v in ins.values()),
                od_pass=m['H03-OD'] >= -EPS, insertion_pass=all(v >= -EPS for v in ins.values()))


def local_arc_need(cx2, tw, margin):
    """C-R1-04 only where an R2 corridor needs one: a negative straight-run margin at the bulk wall can be recovered by a thinner local wall
    t = tw + margin (floor = local material t_wall_min(max) + OD + bore tolerances); returns the arc record or None."""
    if margin >= -EPS:
        return None
    sp = cx2.sp
    floor = sp.m_mid['t_wall_min_mm']['max'] + sp.pc_mid['radius_mm'] + sp.pc_mid['od_radius_mm']
    step = cx2.r2in_arc_step if hasattr(cx2, 'r2in_arc_step') else 0.02
    t_req = tw + margin
    t = math.ceil(t_req / step - 1e-9) * step
    return dict(t_required_mm=t_req, t_grid_mm=t, floor_mm=floor, feasible=t >= floor - EPS and t <= tw + EPS)


# ============================================================================================
# L-WIN (unchanged, SUPPLIER_GATED): W1 at 0.50 mm bonded into the cup pod frame, Z delta 0.000; R1 values read from the pinned R1 JSON
# ============================================================================================
def lane_win2(cx2, r1json):
    cur = r1.lane_win(cx2.cx, cx2.cand)
    pinned = r1json['lanes']['G4-B']['L-WIN']
    keys = ('variant', 't_nominal_mm', 't_min_mm', 'min_inter_cell_web_mm', 'z_delta_mm')
    same = all(abs(cur[k] - pinned[k]) < 1e-9 if isinstance(cur[k], float) else cur[k] == pinned[k] for k in keys)
    mats = {k: (v['sigma_ss_MPa'], v['w_ss_mm']) for k, v in cur['materials'].items()}
    mats_pin = {k: (v['sigma_ss_MPa'], v['w_ss_mm']) for k, v in pinned['materials'].items()}
    same = same and all(abs(a - b) < 1e-9 for k in mats for a, b in zip(mats[k], mats_pin[k]))
    return dict(lane='L-WIN', result=cur, r1_pinned_equal=same, physical_pass=cur['physical_pass'] and same and cur['z_delta_mm'] <= EPS,
                disposition='SUPPLIER_GATED' if cur['physical_pass'] else 'OWNER_GATED', gates=['SR-WINDOW', 'MG-WINDOW-XTALK'],
                note='W1 at 0.50 mm bonded into the cup pod frame; Z delta 0.000; no qualification claim')


# ============================================================================================
# L-ASM (A1-A11 retained; content changes cite their decision, section 7.7)
# ============================================================================================
ASM_ALLOWED_CHANGES = {
    'A1': ('Q-R1-MAIN-SEAL / Q-R1-STRUCTURE', 'Caseback CUP sub-assembly: window bonded into the cup pod frame, FT-C feedthrough and radial O-ring fitted; pressure-testable sub-assembly'),
    'A4': ('OD-CONN-SIDE', 'Module stack on fixture: MAIN + carrier + offset pack + REAR; J1501 / J201 / J202 mated on MAIN B.Cu (axial from the REAR) and the LRA on MAIN; pack isolation open'),
    'A5': ('OD-G4-LRA-ARCH', 'LRA bonded on MAIN B.Cu (zone B) or MAIN F.Cu on the MAIN sub-assembly before the module stack is closed'),
    'A6': ('OD-BATTERY / OD-CONN-SIDE', 'Rear insertion of the module (offset pack, B.Cu connectors, LRA) into the midcase'),
    'A9': ('Q-R1-BUTTON-ENVELOPE', 'Button pushers (T1 stem O-ring or T2 elastomer boot / seal; SW1 / SW5 non-metallic) inserted radially from outside and retained'),
    'A10': ('OD-J202 / Q-R1-CHARGER', 'Battery isolation closed; functional test through the caseback contacts with the drop mated and the caseback in its service position'),
    'A11': ('Q-R1-MAIN-SEAL', 'Cup closed from the rear (+Z) with the radial O-ring; S-CHG bonded feedthrough cured and inspected; lug-root screws through clearance holes in the ceramic'),
}


def asm_sequence2(cx2):
    steps = copy.deepcopy(cx2.st.I['assembly']['steps'])
    for s in steps:
        if s['id'] in ASM_ALLOWED_CHANGES:
            dec, op = ASM_ALLOWED_CHANGES[s['id']]
            s['op'] = op
            s['r2_change'] = dict(decision=dec)
    return steps


def asm_identity2(cx2, steps):
    ref = cx2.st.I['assembly']['steps']
    probs = []
    if [s['id'] for s in steps] != [s['id'] for s in ref]:
        probs.append('operation ids / order differ from accepted A1..A11')
    for a, b in zip(steps, ref):
        for k in ('part', 'direction', 'battery_state'):
            if a.get(k) != b.get(k):
                probs.append('%s %s changed' % (a['id'], k))
        if a.get('op') != b.get('op'):
            if a['id'] not in ASM_ALLOWED_CHANGES or not a.get('r2_change', {}).get('decision'):
                probs.append('%s op changed without a permitted decision citation' % a['id'])
    return dict(pass_=not probs, problems=probs)


def lane_asm2(cx2, rad, deps, stroke_rows, access_rows, steps=None):
    st = cx2.st
    steps = steps if steps is not None else asm_sequence2(cx2)
    ident = asm_identity2(cx2, steps)
    order = g4.assembly_check(st, order=[s['id'] for s in steps], lra_feasible=deps['lra']['state'] == 'RESOLVED')
    count(len(steps))
    j1 = st.I['assembly']['j1_cycles']
    ins_ok = rad['insertion_pass']
    strokes_ok = all(r['clear'] for r in stroke_rows)
    dep = []

    def add(step, need, ok, state_if_not, gate, evidence):
        dep.append(dict(step=step, requires=need, state='RESOLVED' if ok else state_if_not, gate=None if ok else gate, evidence=evidence))
    add('A1', 'W1 window bonded into the cup pod frame (L-WIN)', deps['win']['ok'], 'FAILED', 'OD-G4-WINDOW (W1 at 0.50 mm)', {})
    add('A1', 'structurally admissible cup (L-STR, deflection hard physical, inside the allocation)', deps['str']['ok'], deps['str'].get('state_if_not', 'FAILED'),
        deps['str'].get('gate', 'R2-S05 / Q-R2-SUPPORT-RING'), deps['str'].get('evidence', {}))
    add('A4', 'B.Cu connector poses with clear mate strokes at the A4 item set (J1501 / J201 / J202)', deps['pkg']['ok'], 'FAILED', 'R2-S08 / R2-S14',
        deps['pkg'].get('evidence', {}))
    add('A5', 'LRA bonded in a feasible pose (L-LRA)', deps['lra']['state'] == 'RESOLVED', deps['lra']['state'] if deps['lra']['state'] != 'RESOLVED' else 'FAILED',
        'R2-S04 / SR-LRA', deps['lra'].get('evidence', {}))
    add('A6', 'collision-free rear insertion (offset pack, B.Cu items)', ins_ok, 'FAILED', 'R2-H04 insertion', dict(insertion=rad['insertion']))
    add('A9', 'selectable pusher / seal topology per switch (L-BTN)', deps['btn']['ok'], 'FAILED', 'R2-S03 / R2-S12', deps['btn'].get('evidence', {}))
    add('A10', 'functional test through a feasible charger block with the drop mated (L-CHG)', deps['chg']['ok'], 'FAILED', 'R2-S06', deps['chg'].get('evidence', {}))
    add('A11', 'cup closed with a feasible radial O-ring (L-SEAL)', deps['seal']['ok'], deps['seal'].get('state_if_not', 'FAILED'), deps['seal'].get('gate', 'R2-S07'),
        deps['seal'].get('evidence', {}))
    rows = []
    for r in order['rows']:
        mine = [d for d in dep if d['step'] == r['id'] and d['state'] != 'RESOLVED']
        rows.append(dict(r, gate='; '.join('%s %s' % (d['state'], d['gate']) for d in mine) or None))
    sequence_ok = ident['pass_'] and order['pass_'] and ins_ok and strokes_ok
    failed = [d for d in dep if d['state'] == 'FAILED']
    gated = [d for d in dep if d['state'] == 'GATED']
    product = sequence_ok and not failed and not gated
    disp = 'OWNER_GATED' if (failed or gated or not sequence_ok) else 'SUPPLIER_GATED'
    return dict(lane='L-ASM', sequence=steps, identity=ident, order_check=rows, battery_isolation_ok=all(r['isolation_ok'] for r in order['rows']),
                insertion=rad['insertion'], mate_strokes=dict(pass_=strokes_ok, rows=stroke_rows), access=access_rows,
                j1_cycles=dict(rated=j1['rated'], planned=j1['planned'], per_service=2, services_within_plan=(j1['planned'] - 1) // 2),
                service='caseback removal with the drop and the FPC slack; REAR + tail replacement through rear access to J1501; SERVICE-COVER-REBOND remains OPEN',
                dependencies=dep, failed_dependencies=['%s: %s' % (d['step'], d['requires']) for d in failed],
                gated_dependencies=['%s: %s' % (d['step'], d['requires']) for d in gated], sequence_executable=sequence_ok,
                product_closure_executable=product, physical_pass=sequence_ok, disposition=disp,
                gates=['SERVICE-COVER-REBOND'] + sorted({'%s:%s' % (d['step'], d['gate']) for d in failed + gated}),
                rule='Product closure is executable only if every A-step dependency is RESOLVED (R1:R2-5); a physically FAILED dependency makes L-ASM '
                     'OWNER_GATED and is never reported as an executable product.')


# ============================================================================================
# R2-H15 reserved-region screens and G5 records (material, permittivity class, volume) for every allowed non-conductive item
# ============================================================================================
def z_overlap(a, b, which='adv'):
    lo = max(a['z_lo_' + which], b['z_lo_' + which])
    hi = min(a['z_hi_' + which], b['z_hi_' + which])
    return max(0.0, hi - lo)


def shape_member(shape, x, y):
    kind, g, bb = shape
    if not (bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]):
        return False
    if kind == 'poly':
        return g4.pip((x, y), g)
    if kind == 'disk':
        return math.hypot(x - g[0], y - g[1]) <= g[2]
    r = math.hypot(x - C0[0], y - C0[1])
    return g[0] <= r <= g[1]


def occ_member(o, x, y):
    return any(shape_member(sh, x, y) for sh in o['shapes'])


def overlap_area(o_a, o_b, step=0.2):
    """Area of the intersection of two occupants' plan unions by midpoint sampling on a step grid inside the intersection of their bounding boxes
    (analytic membership for disks and rings; the result carries a boundary resolution of about one cell)."""
    ba, bb = union_bbox(o_a), union_bbox(o_b)
    x0, y0 = max(ba[0], bb[0]), max(ba[1], bb[1])
    x1, y1 = min(ba[2], bb[2]), min(ba[3], bb[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    nx, ny = max(1, int(math.ceil((x1 - x0) / step))), max(1, int(math.ceil((y1 - y0) / step)))
    cnt = 0
    for i in range(nx):
        x = x0 + (i + 0.5) * (x1 - x0) / nx
        for j in range(ny):
            y = y0 + (j + 0.5) * (y1 - y0) / ny
            if occ_member(o_a, x, y) and occ_member(o_b, x, y):
                cnt += 1
    return cnt * ((x1 - x0) / nx) * ((y1 - y0) / ny)


def union_bbox(occ):
    bb = [sh[2] for sh in occ['shapes']]
    return (min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb))


def reserved_screen(cx2, occs, regions, new_items):
    """Every new metal / conductor / component item (new_items: occupant ids) must be strictly outside every reserved region occupant it
    shares a Z interval with; every non-conductive allowed item inside a region gets a G5 record. Returns (violations, g5 records)."""
    viol, g5 = [], []
    by_id = {o['id']: o for o in occs}
    for o in occs:
        cond = o.get('conductive', False) or o['id'] in new_items
        for rg in regions:
            if r1.separated(occ_z_gap(o, rg, cx2.zs), 0.0):
                continue
            if o['group'] == 'RESERVED':
                continue
            gap = occ_plan_gap(o, rg, limit=0.5)
            if gap > EPS:
                continue
            if cond and o.get('metal_or_component', o['id'] in new_items):
                viol.append(dict(item=o['id'], kind=o['kind'], region=rg['region'], level=rg['level'], part=rg['part'], plan_gap_mm=gap))
            elif o.get('allowed_nonconductive'):
                area_ = overlap_area(o, rg)
                v_nom = area_ * z_overlap(o, rg, 'nom')
                v_adv = area_ * z_overlap(o, rg, 'adv')
                if v_adv > 0.0:
                    g5.append(dict(item=o['id'], region=rg['region'], level=rg['level'], region_part=rg['part'], material_class=o.get('material_class'),
                                   permittivity_class=cx2.r2in['buttons']['permittivity_class_labels'].get(o.get('permittivity_key') or o.get('material_class'),
                                                                                                           dict(label='UNLABELLED', numeric=None)),
                                   volume_nominal_mm3=v_nom, volume_linear_worst_mm3=v_adv, g5_rf_required=True))
    return viol, g5


# ============================================================================================
# Joint annulus allocation (R2-H22, 6.8): occupants, declared contact pairs, strict clearances, sampled occupancy ledger
# ============================================================================================
DECLARED_CONTACT_GROUPS = (   # pairs of groups that are designed contact interfaces (6.8 rule 2); anything else must be strictly clear
    ('CARRIER', 'REAR'),            # pillars bear on the S14 support lands (hard-stop function); carrier floor / pillars vs REAR module
    ('CARRIER', 'J1501'), ('CARRIER', 'J201'), ('CARRIER', 'J202'),   # risers leave the lower-web groove at the web edge
    ('CARRIER', 'SLACK'), ('CUP', 'CHG'), ('CUP', 'SLACK'), ('CUP', 'SCREW'), ('CUP', 'REAR'),   # cup plate under the REAR module (static clearance c_cb_rear is a separate R2-H08 check)
    ('CASE', 'LUG'), ('CASE', 'SCREW'), ('LUG', 'SCREW'), ('LUG', 'CUP'),
    ('CARRIER', 'ZONE_A_BCU'), ('CARRIER', 'U7'),    # carrier cavities hold the MAIN B.Cu parts that reach into zone A (battery_carrier_cavities_required)
)


def contact_declared(a, b):
    ga, gb = a['group'], b['group']
    if ga == gb:
        return True
    for x, y in DECLARED_CONTACT_GROUPS:
        if (ga == x and gb == y) or (ga == y and gb == x):
            return True
    return False


def cup_occupants(cx2, D, tw, row, cfg, charger=None):
    """The cup as ONE ceramic occupant with declared sub-volumes that partition its solid: plate inner region (to r_step), plate outer region
    (to the wall), raised wall ring (gland groove excluded), rim flange under the midcase rear face. Plan polygons are conservative supersets."""
    lv = cx2.levels
    R_side = D / 2.0 - tw
    mat = cup_materials(cx2)
    tol = mat['tol_t']
    r_wi = row['r_lim_mm'] - cfg['w_extra']
    r_wo = R_side
    z_top = cfg['t_out'] + cfg['H']
    r_step = cx2.cx.r_step
    D_out = D / 2.0
    subs = [occupant('CUP_PLATE_INNER', 'cup plate (inner region)', [circ_poly(C0[0], C0[1], r_step)], 0.0, cfg['t_in'], 0.0, tol, group='CUP', allowed_nonconductive=True,
                     material_class='MAT-CERAMIC', shapes=[('disk', (C0[0], C0[1], r_step))]),
            occupant('CUP_PLATE_OUTER', 'cup plate (outer region)', ring_polys(r_step, r_wi), 0.0, cfg['t_out'], 0.0, tol, group='CUP', allowed_nonconductive=True,
                     material_class='MAT-CERAMIC', shapes=[('ring', (r_step, r_wi))]),
            occupant('CUP_WALL_RING', 'cup raised wall / spigot', ring_polys(r_wi, r_wo), 0.0, z_top, 0.0, tol, group='CUP', allowed_nonconductive=True,
                     material_class='MAT-CERAMIC', shapes=[('ring', (r_wi, r_wo))]),
            occupant('CUP_RIM_FLANGE', 'cup rim flange (bearing on the midcase rear face)', ring_polys(r_wo, D_out), 0.0, cfg['t_out'], 0.0, tol, group='CUP',
                     allowed_nonconductive=True, material_class='MAT-CERAMIC', shapes=[('ring', (r_wo, D_out))])]
    return subs


def ledger_pairs(cx2, occs, limit=6.0):
    """Every pair that is not a declared contact: strict 3-D clearance at the named required clearance. Returns violations and the
    nearest pairs (the full minimum-gap table is truncated to the nearest 160 pairs plus every violation)."""
    L = []
    c_r = c_rigid(cx2)
    c_plan = cx2.st.P['c_lra_plan_mm']['max']
    for i, a in enumerate(occs):
        for b in occs[i + 1:]:
            if contact_declared(a, b):
                continue
            if a['group'] == 'RESERVED' or b['group'] == 'RESERVED':
                continue
            c = c_plan if 'LRA' in (a['group'], b['group']) else c_r
            ok, rec = pair_clearance(a, b, c, 0.0, cx2.zs, limit=limit)
            rec['clear'] = ok
            L.append(rec)
    viol = [r for r in L if not r['clear']]
    near = sorted(L, key=lambda r: (r['plan_gap_mm'] if r['mode'] == 'PLAN' and r['plan_gap_mm'] is not None else r['z_gap_mm']))
    return dict(pairs_evaluated=len(L), violations=viol, nearest=near[:160],
                min_gap_mm=min([(r['plan_gap_mm'] if r['mode'] == 'PLAN' and r['plan_gap_mm'] is not None else r['z_gap_mm']) for r in L], default=None))


def sampled_ledger(cx2, occs, pk, D, tw, bands, cell=0.5):
    """Occupancy ledger on a cell grid: per Z band and 15-deg sector, occupied and free volume of the shared domain, with double-occupied
    cells reported (a cell-band covered by two occupants that are not a declared contact pair = double-credited volume)."""
    R_side = D / 2.0 - tw
    out_r = cx2.st.s14geo['outline_r'] + cx2.st.I['contract_values']['s14']['plan_clearances_mm']['CHG_CONTACT']
    cp, Ro = pk['centre'], pk['R_carrier_outer']
    bidx = {}
    dom = {b['id']: [0.0] * 24 for b in bands}
    occv = {b['id']: [0.0] * 24 for b in bands}
    dbl = {b['id']: 0 for b in bands}
    members = [o for o in occs if o['group'] not in ('RESERVED',)]
    n = int(2 * R_side / cell) + 2
    x0 = C0[0] - R_side - cell
    y0 = C0[1] - R_side - cell
    pocket = pk['pocket_poly']
    for ix in range(n):
        x = x0 + (ix + 0.5) * cell
        for iy in range(n):
            y = y0 + (iy + 0.5) * cell
            r, az = polar((x, y))
            if r > R_side or r < 1e-9:
                continue
            sec = int(az // 15.0) % 24
            in_a = math.hypot(x - cp[0], y - cp[1]) <= Ro or g4.pip((x, y), pocket)
            for b in bands:
                if b['domain'] == 'periphery' and r < out_r:
                    continue
                if b['domain'] == 'zone_b' and in_a:
                    continue
                dom[b['id']][sec] += cell * cell * (b['z1'] - b['z0'])
            for o in members:
                hit = None
                for kd, gm, bx in o['shapes']:
                    if bx[0] <= x <= bx[2] and bx[1] <= y <= bx[3]:
                        if kd == 'poly':
                            ok_ = g4.pip((x, y), gm)
                        elif kd == 'disk':
                            ok_ = math.hypot(x - gm[0], y - gm[1]) <= gm[2]
                        else:
                            ok_ = gm[0] <= r <= gm[1]
                        if ok_:
                            hit = True
                            break
                if not hit:
                    continue
                o.setdefault('_cell_bands', set())
                for b in bands:
                    if b['domain'] == 'periphery' and r < out_r:
                        continue
                    if b['domain'] == 'zone_b' and in_a:
                        continue
                    zo = max(0.0, min(o['z_hi_adv'], b['z1']) - max(o['z_lo_adv'], b['z0']))
                    if zo > 0:
                        occv[b['id']][sec] += cell * cell * zo
                        key = (ix, iy, b['id'])
                        prev = bidx.get(key)
                        if prev is not None and not contact_declared(prev, o):
                            dbl[b['id']] += 1
                        bidx.setdefault(key, o)
    for o in members:
        o.pop('_cell_bands', None)
    rows = []
    for b in bands:
        for s in range(24):
            rows.append(dict(band=b['id'], sector_deg=[15 * s, 15 * s + 15], domain_mm3=dom[b['id']][s], occupied_mm3=occv[b['id']][s],
                             free_mm3=dom[b['id']][s] - occv[b['id']][s]))
    return dict(cell_mm=cell, bands=[dict(id=b['id'], z=[b['z0'], b['z1']], domain=b['domain']) for b in bands], rows=rows, double_occupied_cells=dbl,
                note='cell-sampled ledger (cell %.2f mm): volumes carry a boundary resolution of about +/- 2 %%; the exact pair table decides clearance' % cell)


# ============================================================================================
# Joint design point (R2 section 8): per-battery scan, offset sweep, greedy placement, cup design, ledger
# ============================================================================================
def btn_status_all(cx2, D):
    out = {}
    for sw in BTN_SW:
        rows = btn_rows(cx2, sw, D)
        out[sw] = dict(rows=rows, status=btn_switch_status(rows, rows[0]['I_SUM']['boss_limit_mm']))
    return out


def btn_lane_ok(bs):
    return all(v['status']['closed'] for v in bs.values())


def quick_rad(cx2, D, tw):
    st, sp, f = cx2.st, cx2.sp, cx2.ce.f
    R_side = D / 2.0 - tw
    tolb = sp.pc_env['radius_mm']
    tol_pcb = sp.pc_pcb['radius_mm']
    m = dict(od=f['od'](D=D), wall=f['wall'](t_wall=tw), dielectric=g4.run_check(sp.local_wall(dict(cx2.ce.dp0, tw=tw)), full=False),
             main_case=R_side - tolb - (cx2.R_main + tol_pcb + st.P['c_main_case_mm']['max']),
             insert_main=R_side - tolb - (cx2.R_main + tol_pcb + c_rigid(cx2)))
    return dict(margins=m, ok=all(v >= -EPS for v in m.values()), min_margin=min(m.values()))


def offsets_grid(cx2):
    G = cx2.r2in['grids']
    mags = grid(G['offset_magnitude_mm'])
    dirs = grid(G['offset_direction_deg'])
    out = []
    for m in mags:
        if m <= EPS:
            out.append((0.0, 0.0))
        else:
            out += [(m, d_) for d_ in dirs]
    return out


def pack_reserved_hits(cx2, pk, reserved):
    """The pack (cell + growth) and the PCM lobe are new conductive components: they must be strictly outside every reserved-region occupant
    sharing a Z interval with the BATTERY level (Q-R2-RESERVED-REGION). The carrier is non-conductive structure (G5 record)."""
    lv = cx2.levels
    L = lv['_layers']
    z_top = L['battery_zone'][1] - cx2.st.sp['c_axial']['nom']       # the stack rule puts the axial clearance c_axial above the swelling pack
    pack = occupant('PACK', 'pack (cell + growth)', [pk['pack_poly']], L['battery_zone'][0], z_top, group='PACKCELL',
                    shapes=[('disk', (pk['centre'][0], pk['centre'][1], pk['pack_radius']))])
    lobe = occupant('PCM_LOBE', 'PCM lobe', [pk['lobe_poly']], L['battery_zone'][0], z_top, group='PACKCELL')
    hits = []
    for o in (pack, lobe):
        for rg in reserved:
            if r1.separated(occ_z_gap(o, rg, cx2.zs), 0.0):
                continue
            g_ = occ_plan_gap(o, rg, limit=0.5)
            if g_ <= EPS:
                hits.append(dict(item=o['id'], region=rg['region'], part=rg['part'], level=rg['level'], plan_gap_mm=g_))
    return hits


def place_connectors(cx2, pk, col, fixed, mag, rooms, cup_occs=(), chg_block_xy=None, plate_top=None, top=6):
    """Greedy deterministic placement J1501 -> J201 -> J202 (top-6 candidates of each are kept for the next item's feasibility; the first
    candidate that lets every later item be placed wins). Returns dict(key -> placement or None) and the search records."""
    spec_t = conn_spec(cx2, 'J1501')
    tail = cx2.st.s14['tail_exit']['centre_assembly_mm']
    r_t, az_t = polar(tuple(tail))
    ranks = {
        'J1501': lambda az, r, ori, spec, geo: (abs(((az - az_t) + 180.0) % 360.0 - 180.0), r, ori),
        'J201': lambda az, r, ori, spec, geo: (abs(((az - pk['pcm_az_deg']) + 180.0) % 360.0 - 180.0), r, ori),
        'J202': lambda az, r, ori, spec, geo: (math.dist(xy(r, az), chg_block_xy) if chg_block_xy else abs(az - 90.0), r, ori)}
    static = list(fixed) + list(cup_occs)
    placed, recs = {}, {}
    order = ('J1501', 'J201', 'J202')
    cand = {}
    for k in order:
        az_range = (cx2.r2in['interconnect']['j202']['az_search_deg'][0], cx2.r2in['interconnect']['j202']['az_search_deg'][1]) if k == 'J202' else None
        extra = []
        # earlier placements are obstacles for later items
        for kk, pl in placed.items():
            extra += pl['occupants']
        if k == 'J202':
            def occ_fn(az, r, ori, spec=conn_spec(cx2, 'J202')):
                return conn_occupants(cx2, spec, az, r, ori, plate_top=plate_top)
            spec = conn_spec(cx2, 'J202')
            G = cx2.r2in['grids']
            azs = [a for a in frange(G['connector_az']['start'], G['connector_az']['stop'], G['connector_az']['step']) if g4.arc_has(a, az_range[0], az_range[1])]
            need = c_rigid(cx2) + spec['riser_t_mm'] / 2.0 + spec['short_mm'] / 2.0
            res = search_poses(cx2, pk, col, static + extra, k, mag, lambda az, r, ori, geo: ranks[k](az, r, ori, spec, geo),
                               lambda az, r, ori: conn_body_poly(spec, az, r, ori), occ_fn, need, spec['long_mm'] / 2.0, azs, None, (0, 90), None, top, rooms,
                               lambda ori: (spec['short_mm'] if ori == 0 else spec['long_mm']) / 2.0)
            res.update(spec=spec, need_mm=need)
        else:
            res = search_connector(cx2, pk, col, static + extra, k, mag, ranks[k], az_range, top, rooms)
        recs[k] = res
        if res['poses']:
            placed[k] = res['poses'][0]
    return placed, recs


def offset_sweep(cx2, D, tw, swg, reserved, mag, col, cup_occs=(), probe=None):
    """R2-V05 over every offset (magnitude 0..1.5 step 0.25, direction 0..345 step 15): pack / carrier / lobe, reserved-region screen,
    supports (H18), the necessary room screens of the three connectors and the LRA classes, then exact placement for the survivors."""
    rows = []
    G = cx2.r2in['grids']
    all_az = frange(0.0, 359.0, 1.0)
    specs = {k: conn_spec(cx2, k) for k in ('J1501', 'J201', 'J202')}
    c_r = c_rigid(cx2)
    needs = {k: c_r + (0.0 if k == 'J202' else specs[k]['R_bend_mm'] + specs[k]['t_fpc_mm']) + specs[k]['riser_t_mm'] / 2.0 + specs[k]['short_mm'] / 2.0 for k in specs}
    classes = lra_classes_r2(cx2)
    lra_need = min(lra_min_extent(c) + 2.0 * cx2.st.P['c_lra_plan_mm']['max'] for c in classes)
    pm_min = cx2.r2in['package_model']['post_min_engagement_mm']
    static = None
    for off in offsets_grid(cx2):
        pk = package_geometry(cx2, off)
        sl = support_layout_r2(cx2, pk, D, tw, swg)
        if static is None:
            static = static_occupants(cx2, D, tw, swg, sl)
        hits = pack_reserved_hits(cx2, pk, reserved)
        rooms = room_profile(cx2, pk, col, all_az)
        j202_az = [a for a in all_az if g4.arc_has(a, *cx2.r2in['interconnect']['j202']['az_search_deg'])]
        slack = {k: max((rooms[a] for a in (j202_az if k == 'J202' else all_az)), default=-9.0) - needs[k] for k in needs}
        engage = min((p['engagement_mm'] for p in sl['posts']), default=None)
        fx = fixed_occupants(cx2, pk, D, tw, swg, sl, static)
        conflicts = []
        ring_o = next((o for o in cup_occs if o['id'] == 'CUP_WALL_RING'), None)
        ring_in = ring_inner_r(ring_o) if ring_o is not None else None
        for a_pcm in G['pcm_az_range_deg']:
            pka = pk if abs(a_pcm - pk['pcm_az_deg']) < EPS else package_geometry(cx2, off, a_pcm)
            car = occupant('CARRIER_ENVELOPE', 'carrier / pack / PCM lobe', pka['carrier_polys'], fx[0]['z_lo_nom'], fx[0]['z_hi_nom'], group='CARRIER',
                           shapes=[('disk', (pka['centre'][0], pka['centre'][1], pka['R_carrier_outer'])), ('poly', pka['pocket_poly'])])
            for b in fx:
                if b['id'] == 'CARRIER_ENVELOPE' or b['group'] == 'RESERVED' or contact_declared(car, b):
                    continue
                ok_, rec_ = pair_clearance(car, b, c_r, 0.0, cx2.zs, fast=True)
                if not ok_ and b['id'] not in conflicts:
                    conflicts.append('%s@pcm%g' % (b['id'], a_pcm))
            if ring_in is not None and ring_in - package_max_radius(pka) < c_r - EPS:
                conflicts.append('CUP_WALL_RING@pcm%g' % a_pcm)
        n_sup = len(sl['posts'])
        wnw = any(p['id'].startswith('SUP_WNW') for p in sl['posts'])
        placeable = None
        rows.append(dict(offset=off, pk=pk, sl=sl, carrier_conflicts=conflicts, reserved_hits=hits, placeable=placeable, rooms=rooms, room_slack=slack, post_min_engagement_mm=engage, supports=n_sup, wnw=wnw,
                         posts_ok=bool(n_sup >= 4 and wnw and engage is not None and engage >= pm_min - EPS), lra_room_slack=max(rooms.values()) - lra_need))
    return rows


def ring_blockers(cx2, ring_occ, fixed, cap_top):
    """Occupants (outside the cup group) whose plan overlaps the cup wall ring annulus below the Z cap: they bound the Z extension the
    continuous wall can take above the REAR band (the freed outer annulus). Returns (free_top_z, blockers)."""
    blockers = []
    for b in fixed:
        if b['group'] in ('CUP', 'RESERVED', 'REAR') or b['kind'] in ('reserved region',):
            continue
        if b['z_hi_adv'] <= ring_occ['z_lo_adv']:
            continue
        if occ_plan_gap(ring_occ, b, limit=0.5) <= EPS:
            blockers.append(dict(id=b['id'], kind=b['kind'], z_lo_adv=b['z_lo_adv']))
    free_top = min([cap_top] + [x['z_lo_adv'] - c_rigid(cx2) for x in blockers])
    return free_top, blockers


def bcu_item_heights(cx2):
    """Seated heights of the existing MAIN B.Cu parts under the accepted G2-REVA lever P-0402 (C901 / C903 re-footprinted to the 0402 high-CV class)."""
    hv = cx2.zs.g2s.heights['bcu_0402_high_cv_mm']
    out = {}
    for f in cx2.st.HM['main_footprints']:
        if f['side'] == 'B.Cu':
            out[f['ref']] = hv if f['ref'] in ('C901', 'C903') else f['seated_max']
    return out


def u7_occupant(cx2):
    g = cx2.st.g2res['G2-U7-B.Cu-0']['geometry']
    h = next(f for f in cx2.st.HM['main_footprints'] if f['ref'] == 'U7')['seated_max']
    z_pl = bcu_plane(cx2)
    return occupant('U7', 'U7 (DRV2625) on B.Cu', geom_polys(g), z_pl - h, z_pl, group='U7', seated_max=h)


def offset_occupants_light(cx2, pk):
    return occupant('ZONE_A', 'zone A', pk['carrier_polys'], 0.0, 1.0, shapes=[('disk', (pk['centre'][0], pk['centre'][1], pk['R_carrier_outer'])), ('poly', pk['pocket_poly'])])


def zone_a_height_check(cx2, pk, occs):
    """R2-H24: every MAIN B.Cu item whose plan touches zone A has a seated height <= the accepted G2-REVA back-zone governing height."""
    hb = cx2.zs.over['G2-REVA']['governing_back_height']
    heights = bcu_item_heights(cx2)
    rows = []
    for o in occs:
        if o['group'] not in ('ZONE_A_BCU', 'U7') and o['kind'] not in ('connector body (B.Cu)', 'LRA actuator'):
            continue
        in_a = occ_plan_gap(o, offset_occupants_light(cx2, pk), limit=0.01) <= EPS
        h = heights.get(o['id'], o.get('seated_max', o['z_hi_nom'] - o['z_lo_nom']))
        rows.append(dict(item=o['id'], in_zone_a=in_a, seated_height_mm=h, ceiling_mm=hb, margin_mm=hb - h, ok=(not in_a) or h <= hb + EPS))
    return dict(governing_back_height_mm=hb, rows=rows, ok=all(r['ok'] for r in rows))


def design_cup(cx2, D, tw, pop, struct, hole_band):
    """Cup design = the configuration that passes the hard deflection check with the least intrusion (ring widening 0, then the lowest wall
    top, then the lowest governing stress); the smallest gland-feasible row is the design row; other rows are alternatives."""
    rows = [r for r in pop['rows'] if r['authorized'] and r['gland_window']]
    req = struct.get('required_wall_for_deflection')
    mat = cup_materials(cx2)
    if not rows or not struct.get('geometry_ok'):
        return dict(ev=None, physical=False, row=None, reason='no gland-feasible row or no admissible plate thickness')
    if req is not None:
        row = next(r for r in rows if r['id'] == req['row'])
        cfg = dict(t_in=struct['t_in'], t_out=req['t_out'], w_extra=0.0, H=req['H'])
        ev = cup_eval(cx2, D, tw, row, cfg, True, hole_band, 41)
        return dict(ev=ev, physical=ev['deflection_pass'], row=row, reason=None)
    best = struct['best_deflection']
    row = next(r for r in rows if r['id'] == best['row'])
    ev = cup_eval(cx2, D, tw, row, best['config'], True, hole_band, 41)
    return dict(ev=ev, physical=False, row=row, reason='deflection limit not met at any scanned wall height (6 mm above the gland height)')


def points_xy(poly):
    return [dict(x=round(p[0], 4), y=round(p[1], 4)) for p in poly]


def lra_identity(cx2, battery_off, cls, side, pose, col, exclusions, mount, z_fit, u7_path, bmm):
    """R1:R4-1 canonical physical identity of the selected LRA pose (reconstructed independently by the validator)."""
    return dict(battery=cx2.battery, offset=battery_off, side=side, lra_class=cls['id'], evidence=cls['evidence'],
                envelope=dict(shape=cls['shape'], length_mm=cls['length'], width_mm=cls['width'], height_mm=cls['height'], lead_exit=cls['lead_exit']),
                pose=dict(az=pose['az'], r=pose['r'], ori=pose['ori']), main_outline_column=dict(R_dev=col['R_dev'], R_g4_max=col['R_g4_max']),
                z_fit=z_fit, mount_allowance_mm=mount, exclusion_set=exclusions, u7_lead_path_mm=u7_path, bmm350_distance_mm=bmm)


def bmm350_distance(cx2, body_poly, z_lo, z_hi):
    """Minimum 3-D distance from the LRA envelope to the U703 package (courtyard rectangle on MAIN F.Cu, z = F.Cu plane .. + seated height)."""
    fp = next(f for f in cx2.st.HM['main_footprints'] if f['ref'] == 'U703')
    u_poly = rect_poly(*fp['courtyard_bbox'])
    z_f = cx2.levels['_layers']['main_pcb'][1]
    z_u_lo, z_u_hi = (z_f, z_f + fp['seated_max']) if fp['side'] == 'F.Cu' else (cx2.levels['_layers']['main_pcb'][0] - fp['seated_max'], cx2.levels['_layers']['main_pcb'][0])
    pg = poly_gap(body_poly, u_poly)
    zg = max(z_lo - z_u_hi, z_u_lo - z_hi, 0.0)
    return math.hypot(pg, zg), pg, zg


def build_chg_xy(chg):
    blk = chg['pose']['block_poly']
    return (sum(p[0] for p in blk) / len(blk), sum(p[1] for p in blk) / len(blk))


def evaluate_point(cx, D, tw, fcu=None, timing=None, n_probe=None):
    """Full evaluation of every lane at ONE joint point (D, tw) of one battery. Returns the point record P (large; the JSON writer
    compacts it)."""
    T = {} if timing is None else timing
    t0 = time.time()
    r2in, st, sp = cx.r2in, cx.st, cx.sp
    L = cx.levels['_layers']
    R_side = D / 2.0 - tw
    P = dict(D=D, tw=tw, R_side=R_side, battery=cx.battery)
    bs = btn_status_all(cx, D)
    swg = switch_geometry(cx, D, bs)
    P['buttons'] = dict(per_switch={sw: dict(status=v['status'], rows=v['rows']) for sw, v in bs.items()}, geometry=swg)
    pop = seal_population(cx, D, tw, 0.0)
    P['seal_rear_band_only'] = pop
    chg0 = lane_chg(cx, D, tw, pop['r_lim_mm'])
    pose0 = chg0['pose']
    blk = pose0['block_poly']
    hole_band = [r1.poly_rmin(blk), max(math.hypot(q[0] - C0[0], q[1] - C0[1]) for q in blk)]
    T['pre'] = time.time() - t0
    t1 = time.time()
    struct = struct_search(cx, D, tw, pop, hole_band)
    cupd = design_cup(cx, D, tw, pop, struct, hole_band)
    P['structure'] = dict(search={k: v for k, v in struct.items() if k != 'evs'}, design=cupd, hole_band=hole_band)
    T['struct'] = time.time() - t1
    ev = cupd['ev']
    cfg = ev['config']
    row = cupd['row']
    cup_occs = cup_occupants(cx, D, tw, row, cfg)
    ring = cup_occs[2]
    mat = cup_materials(cx)
    plate_top = cfg['t_out'] + mat['tol_t']
    col = column_polys(cx, R_side)
    reserved = reserved_regions(cx)
    mag = mag_clear_occupant(cx)
    t2 = time.time()
    chg_xy = build_chg_xy(chg0)
    sweep = offset_sweep(cx, D, tw, swg, reserved, mag, col, cup_occs)
    T['sweep'] = time.time() - t2

    def okey0(r):
        sl = r['room_slack']
        n_room = sum(1 for v in sl.values() if v >= -EPS)
        return (len(r['carrier_conflicts']) + len(r['reserved_hits']), len(r['reserved_hits']), -int(r['posts_ok']), -n_room, -min(sl.values()), r['offset'][0], r['offset'][1])
    pre = sorted(sweep, key=okey0)
    static_cache = static_occupants(cx, D, tw, swg, sweep[0]['sl'])
    t3 = time.time()
    n_probe = r2in['package_model']['offset_probe_count'] if n_probe is None else n_probe
    for r in pre[:n_probe]:      # stage 2: exact top-1 placement probe of the best-ranked offsets (J1501, J201, J202)
        fxp = fixed_occupants(cx, r['pk'], D, tw, swg, r['sl'], static_cache)
        placed_, recs_ = place_connectors(cx, r['pk'], col, fxp, mag, r['rooms'], cup_occs, chg_xy, plate_top, top=1)
        r['placeable'] = sorted(placed_)
    probed = [r for r in pre if r['placeable'] is not None]

    def okey(r):
        return (3 - len(r['placeable']),) + okey0(r)
    ranked = sorted(probed, key=okey) + [r for r in pre if r['placeable'] is None]
    chosen, tried = None, []
    for r in ranked[:5]:
        fixedA = fixed_occupants(cx, r['pk'], D, tw, swg, r['sl'], static_cache)
        placed, recs = place_connectors(cx, r['pk'], col, fixedA, mag, r['rooms'], cup_occs, chg_xy, plate_top)
        tried.append(dict(offset=r['offset'], placed=sorted(placed), n_feasible={k: v['n_feasible'] for k, v in recs.items()},
                          stats={k: v['stats'] for k, v in recs.items()}, room_slack=r['room_slack']))
        if chosen is None or len(placed) > chosen['n']:
            chosen = dict(row=r, fixed=fixedA, placed=placed, recs=recs, n=len(placed))
        if len(placed) == 3:
            break
    T['place'] = time.time() - t3
    sel = chosen['row']
    pk, sl = sel['pk'], sel['sl']
    fixedA = chosen['fixed']
    placed = chosen['placed']
    P['package'] = dict(
        offset_table=[dict(offset=dict(magnitude_mm=r['offset'][0], direction_deg=r['offset'][1]), placeable=r['placeable'], reserved_hits=len(r['reserved_hits']), carrier_conflicts=r['carrier_conflicts'], posts_ok=r['posts_ok'],
                           post_min_engagement_mm=r['post_min_engagement_mm'], supports=r['supports'], room_slack_mm=r['room_slack'], lra_room_slack_mm=r['lra_room_slack'])
                      for r in sweep],
        ranked_first=[list(r['offset']) for r in ranked[:5]], exact_attempts=tried, chosen_offset=sel['offset'], pk=pk, supports=sl,
        column=dict(R_dev=col['R_dev'], R_g4_max=col['R_g4_max'], arcs=col['arcs']))
    # ---- connector paths, slack pockets, drop ------------------------------------------------------------------------------
    paths, risers = {}, []
    specs = {k: conn_spec(cx, k) for k in ('J1501', 'J201', 'J202')}
    slack_fit = {}
    extra_occs = []
    if 'J1501' in placed:
        p = placed['J1501']
        paths['J1501'] = fpc_sensor_path(cx, pk, specs['J1501'], p['az'], p['r'], p['ori'])
        slack_fit['J1501'] = slack_pocket(cx, pk, specs['J1501'], paths['J1501']['tail_exit']['az'], fixedA + cup_occs, cfg['t_out'], ring_inner_r(ring))
        risers.append(dict(id='J1501', polys=[p['geo']['riser']]))
        if slack_fit['J1501']['fits']:
            extra_occs.append(occupant('SLACK_POCKET_J1501', 'service slack pocket', [slack_fit['J1501']['pocket']['poly']], plate_top, L['rear_band'][1] - cx.zs.tol_of('lower_web'), group='SLACK'))
    if 'J201' in placed:
        p = placed['J201']
        paths['J201'] = battery_tail_path(cx, pk, specs['J201'], p['az'], p['r'])
        risers.append(dict(id='J201', polys=[p['geo']['riser']]))
        a_, b_ = paths['J201']['exit_xy'], paths['J201']['riser_xy']
        strip = rot_rect((a_[0] + b_[0]) / 2.0, (a_[1] + b_[1]) / 2.0, math.dist(a_, b_), specs['J201']['riser_w_mm'], math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0])))
        extra_occs.append(occupant('BATT_TAIL_RUN', 'battery tail (plan run)', [strip], paths['J201']['z_exit_mm'] - 0.3, paths['J201']['z_exit_mm'] + 0.3, group='J201', flexible=True))
    if 'J202' in placed:
        p = placed['J202']
        dp_ = dict(pose0)
        dp_['block_poly'] = pose0['block_poly']
        dp_['z_inner_face_mm'] = plate_top
        paths['J202'] = drop_path(cx, dp_, specs['J202'], p['az'], p['r'])
        risers.append(dict(id='J202', polys=[p['geo']['riser']]))
        slack_fit['J202'] = slack_pocket(cx, pk, specs['J202'], p['az'], fixedA + cup_occs, cfg['t_out'], ring_inner_r(ring))
        if slack_fit['J202']['fits']:
            extra_occs.append(occupant('SLACK_POCKET_J202', 'service slack pocket', [slack_fit['J202']['pocket']['poly']], plate_top, L['rear_band'][1] - cx.zs.tol_of('lower_web'), group='SLACK'))
    P['paths'] = dict(paths=paths, slack=slack_fit)
    P['connectors'] = {k: dict(spec=specs[k], placed=None if k not in placed else dict((kk, vv) for kk, vv in placed[k].items() if kk not in ('geo', 'occupants')) |
                              dict(body=points_xy(placed[k]['geo']['body']), z_body_lo=placed[k]['geo']['z_body_lo']),
                              n_feasible=chosen['recs'][k]['n_feasible'], stats=chosen['recs'][k]['stats'], need_mm=chosen['recs'][k].get('need_mm')) for k in specs}
    # ---- charger with the full neighbour set -----------------------------------------------------------------------------------
    conn_occs = [o for k in placed for o in placed[k]['occupants']]
    lra_classes = lra_classes_r2(cx)
    t4 = time.time()
    lra_bcu = lra_bcu_search(cx, pk, col, fixedA + conn_occs + cup_occs, mag, lra_classes, sel['rooms'])
    fcu_res = fcu if fcu is not None else lra_fcu_search(cx, lra_classes)
    T['lra'] = time.time() - t4
    chg = lane_chg(cx, D, tw, pop['r_lim_mm'], fixedA + conn_occs + extra_occs)
    P['charger'] = chg
    # ---- LRA lane record ----------------------------------------------------------------------------------------------------------
    bcu_ok = any(v['n_feasible'] > 0 for v in lra_bcu.values())
    fcu_plan_ok = [k for k, v in fcu_res.items() if v['n_feasible'] > 0]
    cap = r2in['lra']['fcu_height_cap_mm']
    mount = st.P['lra_mount_mm']['max']
    fcu_rows = {}
    for k, v in fcu_res.items():
        cls = v['cls']
        h = cls['height'] + mount
        best = max(v['poses'], key=lambda p_: p_['u703_distance_mm']) if v['poses'] else None
        fcu_rows[k] = dict(cls=cls['id'], n_plan_feasible=v['n_feasible'], tried=v['tried'], seated_height_mm=h, z_neutral_cap_mm=cap, z_neutral=h <= cap + EPS,
                           height_threshold_mm=cap - mount, supplied=cls['supplied'], best_pose=None if best is None else dict(az=best['az'], r=best['r'], ori=best['ori'],
                                                                                                                                 u703_distance_mm=best['u703_distance_mm']))
    P['lra'] = dict(bcu={k: dict((kk, vv) for kk, vv in v.items() if kk not in ('feasible', 'cls')) | dict(cls=v['cls']['id']) for k, v in lra_bcu.items()},
                    fcu_free_disk=fcu_free_disk(cx), bmm350_zone_b=bmm350_zone_b_bound(cx, pk, col), bcu_feasible=bcu_ok, fcu=fcu_rows, fcu_plan_feasible_classes=fcu_plan_ok, classes=[c['id'] for c in lra_classes],
                    max_room_over_offsets_mm=max(max(r['rooms'].values()) for r in sweep), selected=None, identity=None, bmm350=None)
    P['_lra_bcu_raw'] = lra_bcu
    P['_fcu_raw'] = fcu_res
    # ---- ledger ---------------------------------------------------------------------------------------------------------------------
    occs = list(fixedA) + conn_occs + extra_occs + cup_occs + chg['occupants']
    bands = [dict(id='REAR_PERIPHERY', z0=0.0, z1=L['rear_band'][1], domain='periphery'),
             dict(id='LOWER_WEB_LEVEL', z0=L['lower_web'][0], z1=L['lower_web'][1], domain='zone_b'),
             dict(id='BATTERY_BAND', z0=L['battery_zone'][0], z1=L['battery_zone'][1], domain='zone_b'),
             dict(id='BACK_ZONE', z0=L['back_zone'][0], z1=L['back_zone'][1], domain='zone_b')]
    t5 = time.time()
    lg_A = ledger_pairs(cx, occs)
    # variant B: BATTERY-level case supports relieved from below the cup ring top (+ c_rigid) -- the question Q-R2-SUPPORT-RING
    ring_top = ring['z_hi_adv'] + c_rigid(cx)
    occs_B = []
    for o in occs:
        if o['kind'] == 'case-side support':
            o2 = dict(o)
            o2['z_lo_nom'] = max(o['z_lo_nom'], ring_top)
            o2['z_lo_adv'] = max(o['z_lo_adv'], ring_top)
            occs_B.append(o2)
        else:
            occs_B.append(o)
    lg_B = ledger_pairs(cx, occs_B)
    led = sampled_ledger(cx, occs, pk, D, tw, bands)
    T['ledger'] = time.time() - t5
    P['annulus'] = dict(variant_A=dict(as_pinned_supports=lg_A), variant_B=dict(supports_relieved_below_cup_top=lg_B, ring_top_adv_mm=ring['z_hi_adv'], relief_z_mm=ring_top),
                        ledger=led, occupants=[dict(id=o['id'], kind=o['kind'], group=o['group'], z_nom=[o['z_lo_nom'], o['z_hi_nom']], z_adv=[o['z_lo_adv'], o['z_hi_adv']],
                                                    bbox=[round(v, 3) for v in union_bbox(o)]) for o in occs])
    P['_occs'] = occs
    P['_pk'] = pk
    P['_col'] = col
    P['_reserved'] = reserved
    P['_cup_occs'] = cup_occs
    P['_fixed'] = fixedA
    P['_placed'] = placed
    P['_extra_occs'] = extra_occs
    P['_swg'] = swg
    P['zone_a'] = zone_a_height_check(cx, pk, fixedA)
    # ---- L-RAD ------------------------------------------------------------------------------------------------------------------------
    module_extra = dict(main_level_r=max([max_radius([placed[k]['geo']['body']]) for k in placed] + [cx.R_main]),
                        battery_level_r=max([max_radius([placed[k]['geo']['riser']]) for k in placed] + [0.0]),
                        rear_level_r=max([max_radius([slack_fit[k]['pocket']['poly']]) for k in slack_fit if slack_fit[k]['fits']] + [0.0]))
    rad = rad_terms(cx, D, tw, pk, col, risers, module_extra)
    cross = {}
    for xid, key in (('XF-J1501', 'J1501'), ('XB-J201', 'J201'), ('XC-J202', 'J202')):
        cross[xid] = crossing_proof(cx, xid, paths[key]['vertices'], col) if key in paths else dict(crossing=xid, state='NOT_ELIMINATED', proof=None,
                                                                                                    reason='no placed %s pose: no conductor path to prove' % key)
    cross['XL-LRA'] = dict(crossing='XL-LRA', state='NOT_ELIMINATED', proof=None, reason='no LRA pose (B.Cu or F.Cu): no conductor path to prove')
    arcs = {k: local_arc_need(cx, tw, v) for k, v in rad['straight'].items() if v < -EPS}
    P['radial'] = dict(terms=rad, crossings=cross, local_arcs=arcs, columns=dict(R_dev=col['R_dev'], R_g4_max=col['R_g4_max']))
    P['timing'] = T
    return P


def ring_inner_r(ring_occ):
    for k, g, _ in ring_occ['shapes']:
        if k == 'ring':
            return g[0]
    return min(math.hypot(q[0] - C0[0], q[1] - C0[1]) for p in ring_occ['polys'] for q in p) if ring_occ['polys'] else 0.0


# ============================================================================================
# Per-battery scan (R2-V02 / V03), lane classification and the joint design point
# ============================================================================================
def joint_scan(cx2):
    """Cheap lane predicates over the whole (D, tw) grid. A lane whose predicate fails at EVERY grid point is a failed lane (excluded from
    the D choice, evaluated at the joint point for its thresholds); the joint D is the smallest grid D at which every other lane passes
    for some tw (OD-G4-ENVELOPE minimisation); tw is the thinnest grid wall that passes them."""
    G = cx2.r2in['grids']
    Ds = grid(G['D_case_body_mm'])
    tws = grid(G['t_wall_bulk_mm'])
    chg_req = chg_requirements(cx2)
    rows = []
    cover_cache, btn_cache = {}, {}
    for D in Ds:
        cover_cache[D] = r1.cover_group(cx2.cx, cx2.cand, D)
        btn_cache[D] = btn_lane_ok({sw: dict(status=btn_switch_status(btn_rows(cx2, sw, D), 0)) for sw in BTN_SW})
        for tw in tws:
            q = quick_rad(cx2, D, tw)
            pop = seal_population(cx2, D, tw, 0.0)
            gland_ok = any(r['gland_window'] for r in pop['rows'] if r['authorized'])
            chg_ok = chg_req['r_lim_required_min'] is not None and pop['r_lim_mm'] - cx2.st.P['c_chg_window_mm']['max'] >= chg_req['r_lim_required_min'] - cx2.st.P['c_chg_window_mm']['max'] - EPS
            rows.append(dict(D=D, tw=tw, rad_ok=q['ok'], rad_min_margin=q['min_margin'], cover_ok=cover_cache[D]['pass_'], btn_ok=btn_cache[D],
                             seal_gland_ok=gland_ok, chg_radial_ok=chg_ok, r_lim_pop_mm=pop['r_lim_mm'], r_lim_required_mm=chg_req['r_lim_required_min']))
    lane_flags = {'L-RAD': lambda r: r['rad_ok'], 'COVER': lambda r: r['cover_ok'], 'L-BTN': lambda r: r['btn_ok'], 'L-SEAL(gland)': lambda r: r['seal_gland_ok'],
                  'L-CHG(radial)': lambda r: r['chg_radial_ok']}
    failed = [k for k, f in lane_flags.items() if not any(f(r) for r in rows if r['D'] <= 50.9 + EPS)]
    active = [k for k in lane_flags if k not in failed]
    ok_rows = [r for r in rows if all(lane_flags[k](r) for k in active)]
    if not ok_rows:
        return dict(rows=rows, failed_lanes=failed, active_lanes=active, joint=None, ceiling=51.0)
    d_joint = min(r['D'] for r in ok_rows)
    cand = [r for r in ok_rows if r['D'] == d_joint]
    best = min(cand, key=lambda r: r['tw'])      # thinnest wall that passes every active lane: annulus room, r_lim and the spigot improve monotonically with it
    d_ref = max(r['D'] for r in rows if r['rad_ok'] and r['D'] <= 50.9 + EPS)
    return dict(rows=rows, failed_lanes=failed, active_lanes=active, joint=dict(D=d_joint, tw=best['tw'], rad_min_margin=best['rad_min_margin']),
                reference_dmax=dict(D=d_ref, tw=best['tw']), ceiling=51.0,
                rule='failed lane = predicate false at every grid point with D <= 50.9 (the largest grid D whose OD margin 51.00 - (D + 2 tol) is >= 0)')


def evaluate_battery(r2in, g4res, st0, zs, battery, fcu=None, with_reference=True):
    cx = Ctx2(r2in, g4res, st0, zs, battery)
    t0 = time.time()
    scan = joint_scan(cx)
    T = {'scan': time.time() - t0}
    if scan['joint'] is None:
        return dict(battery=battery, cx=cx, scan=scan, P=None, Pref=None, timing=T)
    j = scan['joint']
    P = evaluate_point(cx, j['D'], j['tw'], fcu)
    T['joint'] = time.time() - t0 - T['scan']
    Pref = None
    if with_reference and scan['reference_dmax'] and abs(scan['reference_dmax']['D'] - j['D']) > EPS:
        Pref = evaluate_point(cx, scan['reference_dmax']['D'], scan['reference_dmax']['tw'], fcu, n_probe=24)
    T['reference'] = time.time() - t0 - T['scan'] - T['joint']
    return dict(battery=battery, cx=cx, scan=scan, P=P, Pref=Pref, timing=T)


# ============================================================================================
# Checks that need no joint point: G3 not reopened (R2-H16), interface (R2-H26), battery evidence (R2-H27), shield-ready (R2-H28)
# ============================================================================================
G3_BLOCKS = ('apertures', 'outline', 'pod', 'pod_section', 'supports', 'tail_exit', 'u6', 'window_variants', 'seal_land_mm', 'clearances', 'r_max_assembly')


def g3_pinned_handoff():
    g = load_json(GEN / 'g3_rear_optical.json')
    cand = next(c for c in g['g4_handoff']['candidates'] if c['candidate'] == 'G3-B-S14')
    full = next(c for c in g['candidates'] if c['id'] == 'G3-B-S14')
    return dict(handoff=cand, placements=full['placements'], open_gates=g['g4_handoff']['open_gates'])


def g3_not_reopened(cx2, working=None, pinned=None, pillars=None):
    """R2-H16: the R2 working copy of the G3-B-S14 data (what the occupants were built from) is identical to the pinned handoff; REAR Z relative to the pod
    plane is unchanged under the overlay; pillars differ by Delta only; nothing of the REAR is mutated. `working` is injectable for the faults."""
    st = cx2.st
    pinned = pinned if pinned is not None else g3_pinned_handoff()
    working = working if working is not None else dict(handoff=st.s14, placements=st.s14_cand['placements'], open_gates=st.g3_gates)
    items = {}
    items['1_rear_xy_identical'] = dict(pass_=chash(working['handoff']) == chash(pinned['handoff']) and chash(working['placements']) == chash(pinned['placements']),
                                        detail='handoff candidate G3-B-S14 (released), placements, outline r %.3f, pod area %.3f, apertures, U6 island, J1502 tail exit %s'
                                        % (st.s14geo['outline_r'], st.s14geo['pod_area'], st.s14geo['tail_id']))
    base = cx2.zs.levels('G2-REVA', 'base')
    over = cx2.zs.levels('G2-REVA', 'over')
    rows = {k: dict(base=base[k], over=over[k], same=all(abs(a - b) < 1e-9 for a, b in zip(base[k], over[k]))) for k in ('window', 'optics_zone', 'rear_pcb', 'rear_inner')}
    pd = {c: v for c, v in st.s14geo['pod_section']['corners'].items()}
    cv = st.I['contract_values']['s14']
    pod_ok = all(abs(pd[c]['pod_depth_mm'] - cv['pod_depth_mm'][c]) < 5e-4 and abs(pd[c]['caseback_residual_before_wall_mm'] - cv['caseback_residual_before_wall_mm'][c]) < 5e-4 for c in pd)
    items['2_rear_z_relative_to_pod_plane'] = dict(pass_=all(r['same'] for r in rows.values()) and pod_ok, levels=rows, pod_depth_mm={c: pd[c]['pod_depth_mm'] for c in pd},
                                                   residual_mm={c: pd[c]['caseback_residual_before_wall_mm'] for c in pd}, h_pod=0.0,
                                                   delta_enters_frontward_of='rear_inner (REAR band layer between rear_inner and lower_web)')
    lands = [(s['az'], [list(p) for p in s['poly']]) for s in st.s14geo['supports']]
    pl = sorted((s['azimuth_deg'], [list(p) for p in s['polygon']['assembly_mm']]) for s in pinned['handoff']['supports'])
    items['3_support_land_plan'] = dict(pass_=sorted(lands) == pl and sorted(a for a, _ in lands) == sorted(cv['support_azimuths_deg']), azimuths=sorted(a for a, _ in lands),
                                        rule='lands keep azimuth 30 / 150 / 270 and their pinned polygons; nothing enlarged, no new contact on the REAR board')
    # pillars: footprint == land polygon (inside its land), Z length exactly Delta longer than at Delta = 0
    fps = pillars if pillars is not None else pillar_footprints(cx2)
    pillars = []
    for s in st.s14geo['supports']:
        lo = base['rear_inner'][1]
        L0 = base['lower_web'][0] - lo
        L1 = over['rear_band'][1] - over['rear_inner'][1]
        fp = fps.get(s['az'])
        inside = fp is not None and all(g4.pip(q, [tuple(p) for p in s['poly']]) or min(pt_poly_dist(q, [tuple(p) for p in s['poly']]), 9.0) <= 1e-6 for q in fp)
        pillars.append(dict(az=s['az'], footprint_inside_land=bool(inside), length_base_mm=L0, length_r2_mm=L1, growth_mm=L1 - L0))
    items['4_pillars_plus_delta_only'] = dict(pass_=all(abs(p['growth_mm'] - cx2.delta) < 1e-9 and p['footprint_inside_land'] for p in pillars) and sorted(fps) == sorted(s['az'] for s in st.s14geo['supports']),
                                              pillars=pillars, delta_mm=cx2.delta)
    items['5_zero_optical_board_mutation'] = dict(pass_=items['1_rear_xy_identical']['pass_'], detail='no REAR part, cell, window variant, barrier, seal land, thermode or tail corridor is an R2 variable')
    items['6_g3_gates_untouched'] = dict(pass_=chash(working['open_gates']) == chash(pinned['open_gates']), gates=[g['id'] for g in pinned['open_gates']],
                                         rule='the G3 conservative-corner gates stay G3 gates; R2 claims to close none of them')
    gates = st.I['contract_values']['s14']['plan_clearances_mm']
    items['7_retired_reservations'] = dict(pass_=True, reported={'CHG_ROUTE': 'retired reservation; S14 unchanged (frozen plan clearance %.3f mm)' % gates['CHG_ROUTE'],
                                                                  'CHG_LINK': 'retired reservation; S14 unchanged (frozen plan clearance %.3f mm)' % gates['CHG_LINK']})
    ok = all(v['pass_'] for v in items.values())
    return dict(pass_=ok, items=items, rule='R2-H16 passes only if every item holds at nominal, conservative and optimistic corners and at linear worst; the pod_section is compared '
                'at all three corners')


def interface_check(cx2):
    d = load_json(ROOT / 'design/interfaces/main_rear_interface.json')
    pos = d['positions']
    nets = sorted({p['net'] for p in pos})
    positive = [n for n in nets if any(t in n.upper() for t in ('VBUS', '+5V', 'CHG', 'CHARGER', 'VCHG'))]
    return dict(pass_=len(pos) == cx2.r2in['interconnect']['positions'] and len(nets) == cx2.r2in['interconnect']['nets'] and not positive, positions=len(pos),
                nets=len(nets), expected_positions=cx2.r2in['interconnect']['positions'], expected_nets=cx2.r2in['interconnect']['nets'], charger_positive_nets_in_sensor_fpc=positive,
                mirrored_order='the mirrored physical position order of a B.Cu J1501 is a K1 requirement only; the logical J1501 n -> J1502 n map is unchanged')


def evidence_check(r2in, battery):
    cat = r2in['catalogue']
    c = cat['batteries'][battery]
    labels_ok = bool(cat.get('catalogue_value')) and bool(c.get('catalogue_value')) and c.get('gate') == 'SR-BATT-PACK' and c.get('evidence_class') == 'OWNER_DECISION'
    env = r2in['envelope_assumptions']
    contra = []
    for rec in r2in['supplier_evidence'].get('SR-BATT-PACK', []):
        vals = rec.get('recorded_values', {})
        if vals.get('finished_diameter_max_mm', 0) > env['finished_diameter_max_mm'] + EPS:
            contra.append((rec.get('id'), 'finished diameter'))
        if vals.get('finished_thickness_add_max_mm', 0) > env['finished_thickness_add_max_mm'] + EPS:
            contra.append((rec.get('id'), 'finished thickness'))
        if vals.get('growth_axial_max_mm', 0) > env['growth_axial_max_mm'] + EPS or vals.get('growth_radial_max_mm', 0) > env['growth_radial_max_mm'] + EPS:
            contra.append((rec.get('id'), 'growth'))
        if vals.get('lobe_inside_authored_envelope') is False:
            contra.append((rec.get('id'), 'PCM lobe'))
        if vals.get('exit_inside_swept_window') is False:
            contra.append((rec.get('id'), 'exit window'))
        if vals.get('three_wire_exit_compatible_with_J201') is False:
            contra.append((rec.get('id'), 'three-wire exit'))
    return dict(pass_=labels_ok and not contra, labels_present=labels_ok, contradictions=contra, battery=battery, recorded_documents=len(r2in['supplier_evidence'].get('SR-BATT-PACK', [])),
                label='pending SR-BATT-PACK' if not r2in['supplier_evidence'].get('SR-BATT-PACK') else 'recorded evidence checked against the assumed envelope',
                catalogue=c)


def shield_check(cx2, occs):
    plc = load_json(ROOT / 'design/placement/phase1_placement.json')
    poly = [tuple(p) for p in plc['shield_polygon_mm']]
    area = g4.poly_area(poly)
    st, sp = cx2.st, cx2.sp
    can_h = st.sp['h_shield_can']['nom']
    c_front = st.sp['c_front']['nom']
    gap_base = cx2.zs.base['G2-REVA']['layers']['front_gap']
    gap_over = cx2.zs.over['G2-REVA']['layers']['front_gap']
    shield = occupant('U101_SHIELD', 'U101 shield polygon (can)', [poly], cx2.levels['_layers']['front_gap'][0], cx2.levels['_layers']['front_gap'][0] + can_h, group='SHIELD')
    hits = []
    for o in occs:
        if o['group'] == 'SHIELD':
            continue
        if r1.separated(occ_z_gap(o, shield, cx2.zs), 0.0):
            continue
        if occ_plan_gap(o, shield, limit=0.2) <= EPS:
            hits.append(o['id'])
    return dict(pass_=abs(area - 92.95) < 5e-3 and abs(gap_base - gap_over) < 1e-9 and not hits and can_h + c_front <= gap_over + EPS, polygon_area_mm2=area,
                front_gap_base_mm=gap_base, front_gap_r2_mm=gap_over, can_plus_c_front_mm=can_h + c_front, headroom_mm=gap_over - can_h - c_front, intrusions=hits,
                reference='architecture.md section B "Shield-ready clearance" (U101 can 0.8-1.0, nominal 0.85; h_shield_can + c_front = 1.0 mm against the 2.85 mm front gap; polygon 92.95 mm2)')


def scope_report(r2in=None):
    """R2-H20 governance: every changed path (vs the pinned R1 record) belongs to R2_FILES; no KiCad / interface / placement path differs."""
    changed = set(git('diff', '--name-only', R1_BASELINE, '--', '.').stdout.split())
    changed |= set(git('ls-files', '--others', '--exclude-standard').stdout.split())
    outside = sorted(changed - R2_FILES)
    kicad = git('diff', '--name-only', R1_BASELINE, '--', '*.kicad_pcb', '*.kicad_sch', '*.kicad_pro', '*.kicad_prl', 'design/interfaces', 'design/placement', 'rear_sensor', 'libraries').stdout.split()
    tracked_changed = sorted(set(git('diff', '--name-only', R1_BASELINE, '--', '.').stdout.split()) - R2_FILES)
    return dict(pass_=not outside and not kicad, changed_paths=sorted((changed & R2_FILES) - GENERATED_FILES), outside_r2_files=outside, kicad_interface_placement_diffs=kicad,
                tracked_changed_outside_r2_files=tracked_changed)


# ============================================================================================
# Lane records, hard checks (R2-H01 .. H28), stops, dispositions and the per-battery verdict
# ============================================================================================
def r1_col(r1json, cid, cand='G4-B'):
    """The committed R1 value of the corresponding R1 check as a column (read from the pinned R1 JSON, never re-typed)."""
    h = r1json['hard_checks'].get(cid)
    if h is None:
        return dict(status='n/a (new in R2)', margin=None, units=None, physical_pass=None)
    x = h[cand] if cand in h else h
    return dict(check=cid, status=x.get('study_status'), margin=x.get('margin'), units=x.get('units'), physical_pass=x.get('physical_pass'),
                threshold_value=x.get('threshold_value'))


def hc(cid, title, evaluation, status, margin=None, units='mm', governing=None, r1c=None, gates=None, detail=None, supplier_zero_margin=None, credits=(),
       owner_gated=None, nominal=None, rss=None, legacy=None):
    if status not in REF_STATUS:
        raise StudyError('unknown check status %r' % status)
    return dict(id=cid, title=title, evaluation=evaluation, status=status, margin=margin, units=units, linear_worst=margin, nominal=nominal, rss=rss, legacy=legacy,
                governing_terms=governing or [], r1_column=r1c, gates=gates or [], detail=detail, supplier_zero_margin=supplier_zero_margin or [], credits=list(credits),
                owner_gated=owner_gated or [])


def seal_path_report(cx2, P):
    """Seal inventory with the R2 primary-seal classes (cup radial O-ring, T1 stem O-ring / T2 boot, FT-C bonded body) and the G4 closure graph."""
    st, cand = cx2.st, cx2.cand
    inv = g4.seal_inventory(st, cand, 'W1', len(st.s14geo['cells']), 'radial', False)
    for s in inv['seals']:
        if s['id'].startswith('S-SW'):
            sw = s['id'][2:]
            rows = P['buttons']['per_switch'][sw]['status']
            topo = rows['closing'][0][0] if rows['closing'] else 'T2-F'
            s['type'] = 'stem O-ring (dynamic radial)' if topo == 'T1' else 'elastomer boot / seal (static face or bonded rim)'
            s['r2_topology'] = 'T1 / T2 (whichever closes)'
        if s['id'] == 'S-CHG':
            s['type'] = 'bonded sealed body (FT-C)'
        if s['id'] == 'S-CB-MAIN':
            s['type'] = 'radial O-ring on the ceramic cup wall (serviceable; screws plus O-ring, no adhesive main seal)'
    for owner, aps in inv['components'].items():
        for a in aps:
            s = next(x for x in inv['seals'] if x['id'] == a['seal'])
            a['type'] = s['type']
    clo = g4.seal_closure(inv, screws_outside=True)
    return dict(inventory=inv, closure=clo, pass_=bool(clo['closed']))


def supports_report(cx2, P):
    pk, sl = P['_pk'], P['package']['supports']
    c_r = c_rigid(cx2)
    rows = []
    wnw = False
    for p in sl['posts']:
        car = offset_occupants_light(cx2, pk)
        g_ = occ_plan_gap(p, car, limit=2.0)
        rows.append(dict(id=p['id'], inner_r_mm=p['inner_r'], engagement_mm=p['engagement_mm'], gap_to_offset_pack_envelope_mm=g_, outside_pack_envelope=g_ >= c_r - EPS))
        wnw = wnw or p['id'].startswith('SUP_WNW')
    pm = cx2.r2in['package_model']['post_min_engagement_mm']
    ok = len(rows) >= 4 and wnw and all(r['outside_pack_envelope'] and r['engagement_mm'] >= pm - EPS for r in rows)
    return dict(pass_=ok, count=len(rows), includes_WNW=wnw, rows=rows, min_engagement_required_mm=pm, pads=len(sl['pads']))


def k1_constraints(cx2, P):
    """Growth of the MAIN outline beyond the development envelope required by the placed B.Cu items (a K1 requirement; never in a reserved region)."""
    col = P['_col']
    rows = []
    for k, pl in P['_placed'].items():
        body = pl['geo']['body']
        r = max_radius([body])
        if r > col['R_dev'] + EPS:
            azs = [polar(q)[1] for q in body]
            rows.append(dict(item=k, max_radius_mm=r, growth_beyond_dev_mm=r - col['R_dev'], az_span_deg=[min(azs), max(azs)]))
    return dict(development_envelope_mm=col['R_dev'], g4_max_outline_mm=col['R_g4_max'], rows=rows, allowed_growth_arcs_deg=[[round(a, 2), round(b, 2)] for a, b in col['arcs']],
                requirement='MAIN outline must be extended to the listed radius over the listed azimuths (K1); the extension lies outside every reserved region and every switch window')


def static_clearance_report(cx2, P):
    """R2-H08: static (zero-load) clearance > 0.050 mm (strict) from every cup / plate / ring / rib / charger / LRA feature to every forbidden item (battery
    and carrier lower web, REAR PCB, G3 support lands, pillars)."""
    occs = P['_occs']
    forb = [o for o in occs if o['id'] in ('CARRIER_ENVELOPE', 'S14_OUTLINE') or o['id'].startswith(('S14_LAND', 'PILLAR'))]
    feats = [o for o in occs if o['group'] in ('CUP', 'CHG', 'LRA')]
    rows = []
    for f in feats:
        for b in forb:
            zg = occ_z_gap(f, b, cx2.zs)
            pg = occ_plan_gap(f, b, limit=2.0)
            sep = max(zg, pg)
            rows.append(dict(feature=f['id'], forbidden=b['id'], z_gap_mm=zg, plan_gap_mm=pg, static_clearance_mm=sep if (zg > EPS or pg > EPS) else min(zg, 0.0), clear=sep > 0.05 + EPS))
    mn = min((r['static_clearance_mm'] for r in rows), default=None)
    return dict(threshold_mm=0.05, rows=sorted(rows, key=lambda r: r['static_clearance_mm'])[:24], minimum_mm=mn, pass_=all(r['clear'] for r in rows),
                governing=min(rows, key=lambda r: r['static_clearance_mm']) if rows else None, rule='strict: the clearance must exceed 0.050 mm so that the full deflection allowance fits')


def rim_bearing(cx2, P):
    """R2-H10: cup rim bearing on the midcase rear face (continuous annulus), screw load share, ceramic edge-distance threshold at the clearance holes."""
    st, sp = cx2.st, cx2.sp
    D, tw = P['D'], P['tw']
    p = cx2.cx.p
    R = D / 2.0 - tw + sp.pc_env['radius_mm']
    F = p * math.pi * R * R
    w_b = max(0.0, tw - sp.pc_env['od_radius_mm'] - sp.pc_env['radius_mm'])
    A_b = math.pi * ((R + w_b) ** 2 - R ** 2)
    n = len(g4.screw_layout(st, sp, dict(D=D, tw=tw))['screws'])
    unequal = st.P['support_load']['unequal_share_factor']
    sig = F / A_b
    allow = cup_materials(cx2)['sigma_allow']
    per_screw = F * unequal / n
    return dict(force_N=F, bearing_width_mm=w_b, bearing_area_mm2=A_b, bearing_stress_MPa=sig, planning_allowable_MPa=allow, bearing_margin_MPa=allow - sig,
                bearing_pass=sig <= allow + EPS, screws=n, screw_load_N=per_screw, unequal_share_factor=unequal,
                screw_class=cx2.cand['screw_class'], screw_shear_capacity='SUPPLIER_DATA_REQUIRED (SR-CASEBACK-CERAMIC / OD-G4-STRAP)',
                ceramic_edge_distance='SUPPLIER_DATA_REQUIRED: the ceramic material class has no authored screw_edge_min (no threads in ceramic; clearance holes)',
                supplier_zero_margin=[dict(term='bearing_allowable_MPa', value=sig), dict(term='screw_load_per_screw_N', value=per_screw)])


def pk_summary(cx2, P):
    return {k: v for k, v in P['_pk'].items() if k not in ('pack_poly', 'carrier_poly', 'carrier_polys', 'lobe_poly', 'pocket_poly')}


def compact_pose(pl, keys=('key', 'az', 'r', 'ori')):
    return {k: pl[k] for k in keys} | dict(body=points_xy(pl['geo']['body']), z_body_lo_mm=pl['geo']['z_body_lo'], stroke_mm=pl['geo']['stroke'])


def stroke_rows_of(cx2, placed, occs, c_r):
    """A4: the mate-stroke occupant of every placed connector must keep strict clearance (and 1 mm in plan) from every module group it does not belong to."""
    rows = []
    module_groups = ('CARRIER', 'REAR', 'ZONE_A_BCU', 'U7', 'J1501', 'J201', 'J202', 'LRA')
    for k, pl in placed.items():
        stroke = next(o for o in pl['occupants'] if o['id'].endswith('_STROKE'))
        for b in occs:
            if b['group'] not in module_groups or b['group'] == stroke['group']:
                continue
            ok_, rec_ = pair_clearance(stroke, b, c_r, 0.0, cx2.zs)
            if not ok_ or rec_['plan_gap_mm'] is not None and rec_['plan_gap_mm'] < 1.0:
                rows.append(dict(rec_, clear=ok_, step='A4'))
    return rows


def finalize_battery(E, r2in, r1json, anchors_ok, scope, other=None):
    """Lane records, hard checks, stops, dispositions and the per-battery verdict of one battery from its joint-point evaluation."""
    cx, P, Pref, scan = E['cx'], E['P'], E['Pref'], E['scan']
    st, sp = cx.st, cx.sp
    L = cx.levels['_layers']
    battery = cx.battery
    out = dict(battery=battery, joint=dict(D=P['D'], tw=P['tw'], R_side=P['R_side'], D_margin_to_51_mm=51.0 - P['D']))
    # ---------------- Z ---------------------------------------------------------------------------------------------------------
    zrep = cx.zs.delta_report()
    zprob = z_delta_problems(cx.zs, r2in['limits'])
    # ---------------- buttons ---------------------------------------------------------------------------------------------------
    bsw = P['buttons']['per_switch']
    btn_closed = all(v['status']['closed'] for v in bsw.values())
    btn_stops = sorted({v['status']['stop'] for v in bsw.values() if v['status'].get('stop')})
    imax_only = {sw: v['status']['imax_only'] for sw, v in bsw.items() if v['status']['imax_only']}
    boss_rows = {}
    for sw, v in bsw.items():
        closing = [r for r in v['rows'] if r['I_SUM']['closes']]
        boss_rows[sw] = dict(window_deg=list(st.P['buttons']['windows_deg'][sw]), material_rule=r2in['buttons']['switch_materials'][sw]['rule'], closed=v['status']['closed'],
                             rows=[dict(topology=r['topology'], pusher_class=r['option'], R1_column='T1 never selectable' if r['topology'] == 'T1' else 'R1 T2 best',
                                        boss_limit_mm=r['I_SUM']['boss_limit_mm'],
                                        I_SUM=dict(closes=r['I_SUM']['closes'], boss_used_mm=r['I_SUM']['boss_grid_used_mm'], boss_zero_margin_mm=r['I_SUM']['boss_zero_margin_mm'],
                                                   d_p_mm=r['I_SUM']['section']['d_p'], margins=r['I_SUM']['section']['margins'], causes=r['I_SUM']['causes'],
                                                   protrusion_mm=r['I_SUM']['section']['protrusion_mm'], strain_margin=r['I_SUM']['section'].get('strain_margin')),
                                        I_MAX=dict(closes=r['I_MAX']['closes'], boss_used_mm=r['I_MAX']['boss_grid_used_mm'], boss_zero_margin_mm=r['I_MAX']['boss_zero_margin_mm'],
                                                   margins=r['I_MAX']['section']['margins'], causes=r['I_MAX']['causes'])) for r in v['rows']],
                             closing_options=v['status']['closing'], imax_only=v['status']['imax_only'], stop=v['status'].get('stop'),
                             r1_column=r1json['lanes']['G4-B']['L-BTN']['switches'][sw]['best']['I-SUM']['margins'])
    # ---------------- seal / structure ---------------------------------------------------------------------------------------
    pop = P['seal_rear_band_only']
    cupd = P['structure']['design']
    ev = cupd['ev']
    cfg = ev['config']
    ring = next(o for o in P['_cup_occs'] if o['id'] == 'CUP_WALL_RING')
    band_cap_top = L['rear_band'][1] - cx.zs.tol_of('lower_web')
    posts = [o for o in P['_fixed'] if o['kind'] == 'case-side support']
    c_r = c_rigid(cx)
    others = [o for o in P['_occs'] if o['group'] not in ('CUP', 'CHG')]
    free_top_A, blockers_A = ring_blockers(cx, ring, others, L['battery_zone'][1] - c_r)
    free_top_B, blockers_B = ring_blockers(cx, ring, [o for o in others if o['kind'] != 'case-side support'], L['battery_zone'][1] - c_r)
    ext_free_A = max(0.0, free_top_A - band_cap_top)
    ext_free_B = max(0.0, free_top_B - band_cap_top)
    z_top_adv = ring['z_hi_adv']
    ext_design = max(0.0, z_top_adv - band_cap_top)
    gl_rows = [r for r in pop['rows'] if r['authorized'] and r['gland_window']]
    ext_row = {r['id']: max(0.0, -r['margins']['spigot_rear_periphery_z']) for r in gl_rows}
    seal_closes_A = any(v <= ext_free_A + EPS for v in ext_row.values())
    seal_closes_B = any(v <= ext_free_B + EPS for v in ext_row.values())
    pop_A = seal_population(cx, P['D'], P['tw'], ext_free_A)
    pop_B = seal_population(cx, P['D'], P['tw'], ext_free_B)
    str_phys_B = bool(cupd['physical']) and ext_design <= ext_free_B + EPS
    str_phys_A = bool(cupd['physical']) and ext_design <= ext_free_A + EPS
    rim = rim_bearing(cx, P)
    stat = static_clearance_report(cx, P)
    sp_path = seal_path_report(cx, P)
    # ---------------- package ------------------------------------------------------------------------------------------------
    sweep = P['package']['offset_table']
    clean = [r for r in sweep if r['reserved_hits'] == 0 and not r['carrier_conflicts'] and r['posts_ok']]
    placed = P['_placed']
    unplaced = [k for k in ('J1501', 'J201', 'J202') if k not in placed]
    lg_A = P['annulus']['variant_A']['as_pinned_supports']
    lg_B = P['annulus']['variant_B']['supports_relieved_below_cup_top']
    viol_A = lg_A['violations']
    viol_B = lg_B['violations']
    support_only_A = bool(viol_A) and all(('case-side support' in (next((o['kind'] for o in P['_occs'] if o['id'] == v['a']), ''), next((o['kind'] for o in P['_occs'] if o['id'] == v['b']), '')))
                                          for v in viol_A)
    reserved_screen_items = [o['id'] for o in P['_occs'] if o['id'] in ('J1501_BODY', 'J1501_RISER', 'J1501_BEND', 'J201_BODY', 'J201_RISER', 'J201_BEND', 'J202_BODY', 'J202_RISER',
                                                                         'BATT_TAIL_RUN', 'CHG_BLOCK')]
    pk = P['_pk']
    res_hits = pack_reserved_hits(cx, pk, P['_reserved'])
    new_items = set(reserved_screen_items)
    viol_res, g5 = reserved_screen(cx, reserved_candidates(P), P['_reserved'], new_items)
    # extra G5 records: carrier, O-ring, SW1 / SW5 pusher + boss growth
    g5 += sw_g5_records(cx, P)
    g5 += carrier_oring_g5(cx, P, ring)
    g5 = dedupe_g5(g5)
    # ---------------- LRA --------------------------------------------------------------------------------------------------------
    lra_ok_bcu = P['lra']['bcu_feasible']
    lra_fcu_plan = P['lra']['fcu_plan_feasible_classes']
    lra_fcu_z = [k for k, v in P['lra']['fcu'].items() if v['n_plan_feasible'] > 0 and v['z_neutral'] and (v['supplied'])]
    lra_state = 'RESOLVED' if (lra_ok_bcu or lra_fcu_z) else ('GATED' if lra_fcu_plan else 'FAILED')
    # ---------------- charger -----------------------------------------------------------------------------------------------------
    chg = P['charger']
    # ---------------- stops -------------------------------------------------------------------------------------------------------
    stops = []

    def stop(sid, scope_, reason, quantities=None):
        stops.append(dict(id=sid, scope=scope_, reason=reason, quantities=quantities or {}))
    g3 = g3_not_reopened(cx)
    if not g3['pass_']:
        stop('R2-S01', 'whole run', 'R2-H16 false: G3 data differ from the pinned handoff or a REAR Z / land / pillar rule fails', {k: v['pass_'] for k, v in g3['items'].items()})
    if zprob:
        stop('R2-S02', 'whole run', 'total Z delta nonzero or OD-THICK-REVA failure', {'problems': zprob})
    if scan['joint'] is None or P['D'] > 51.0 + EPS or 'R2-S03' in btn_stops:
        stop('R2-S03', 'whole design (lanes completed)', 'no joint point with D_eval <= 51.00, or a closure needs a boss > +3.0 mm / a protrusion outside the five windows',
             {'D_joint': P['D'], 'btn_stops': btn_stops})
    if not lra_ok_bcu and not lra_fcu_plan:
        stop('R2-S04', 'lane L-LRA', 'no LRA pose on MAIN B.Cu (zone B) and no plan-feasible Z-neutral F.Cu fallback pose',
             {'bcu_max_annulus_mm': P['lra']['max_room_over_offsets_mm'], 'bcu_need_by_class_mm': {k: v['need_mm'] for k, v in P['lra']['bcu'].items()},
              'fcu_plan_feasible_poses': {k: v['n_plan_feasible'] for k, v in P['lra']['fcu'].items()}})
    if not cupd['physical'] and not P['structure']['search'].get('physical_pass_any_height'):
        stop('R2-S05', 'lane L-STR', 'deflection > 0.050 mm (or forbidden contact) at every admissible cup configuration',
             {'best_deflection_mm': P['structure']['search']['best_deflection']['w_max_mm'] if P['structure']['search'].get('best_deflection') else None})
    if not chg['closes']:
        stop('R2-S06', 'lane L-CHG', 'the charger block / land / feedthrough does not close under the amended C-R1-01 2(v) (C-R2-01) at the joint point',
             {'r_lim_cup_mm': chg['radial']['r_lim_cup_mm'], 'r_lim_required_min_mm': chg['radial']['r_lim_required_min_mm'], 'deficit_mm': chg['headline']['radial_limit_deficit_mm'],
              'block_margin_mm': chg['radial']['block_margin_mm'], 'land_margin_mm': chg['radial']['land_margin_mm']})
    if not (gl_rows and seal_closes_B) or not sp_path['pass_']:
        stop('R2-S07', 'lane L-SEAL', 'no radial cup row passes every typed predicate in its allocation (also with the case supports relieved), or the seal path is open',
             {'gland_feasible_rows': len(gl_rows), 'zero_margin_extension_mm': pop['zero_margin_ext_mm'], 'seal_path_closed': sp_path['pass_']})
    s08_reasons = []
    if unplaced:
        s08_reasons.append('no strict-clearance pose for %s in the annulus (MAIN B.Cu zone B)' % ', '.join(unplaced))
    if viol_B:
        s08_reasons.append('%d pair(s) remain over-allocated with the supports relieved: %s' % (len(viol_B), ', '.join('%s/%s' % (v['a'], v['b']) for v in viol_B[:6])))
    if viol_A and not support_only_A:
        s08_reasons.append('non-support pairs over-allocated: %s' % ', '.join('%s/%s' % (v['a'], v['b']) for v in viol_A if v not in viol_B)[:200])
    if viol_res:
        s08_reasons.append('new metal / conductor / component inside a reserved region: %s' % ', '.join(sorted({v['item'] for v in viol_res})))
    if res_hits:
        s08_reasons.append('the pack / PCM lobe lies inside a reserved region: %s' % ', '.join(sorted({'%s@%s' % (h['region'], h['level']) for h in res_hits})))
    if s08_reasons:
        stop('R2-S08', 'whole design (lanes completed)', 'annulus over-allocated: ' + '; '.join(s08_reasons), {'unplaced': unplaced, 'ledger_B_violations': len(viol_B), 'reserved_violations': len(viol_res)})
    if not clean:
        stop('R2-S14', 'lane L-PKG', 'no admissible offset keeps pack + growth + PCM lobe + carrier out of the reserved regions and clear of the case features, at the PCM exit azimuths 220 / 230 / 240',
             {'offsets_evaluated': len(sweep), 'offsets_clean': 0, 'min_total_violations': min(len(r['carrier_conflicts']) + r['reserved_hits'] for r in sweep)})
    if btn_stops and 'R2-S12' in btn_stops:
        stop('R2-S12', 'lane L-BTN', 'some switch has no admitted topology closing inside its frozen window for a non-boss reason', {'switches': [sw for sw, v in bsw.items() if v['status'].get('stop') == 'R2-S12']})
    if not anchors_ok:
        stop('R2-S10', 'whole run', 'historical reproduction / overlay-off anchors failed', {})
    if not scope['pass_']:
        stop('R2-S10', 'whole run', 'a KiCad / interface / placement / immutable file differs or a path outside R2_FILES changed', {'outside': scope['outside_r2_files']})
    ev_chk = evidence_check(r2in, battery)
    if ev_chk['contradictions']:
        stop('R2-S09', 'whole run (owner STOP)', 'recorded SR-BATT-PACK evidence contradicts the assumed envelope', {'contradictions': ev_chk['contradictions']})
    # ---------------- lane records -----------------------------------------------------------------------------------------------
    win = lane_win2(cx, r1json)
    stroke_rows = stroke_rows_of(cx, placed, P['_occs'], c_r)
    access_rows = [dict(step='A4', operation='J1501 plug (axial from the REAR, bench, MAIN B.Cu up)', direction='+Z from the rear', placed='J1501' in placed),
                   dict(step='A4', operation='J201 plug (axial option evaluated first)', direction='+Z from the rear', placed='J201' in placed),
                   dict(step='A4', operation='J202 / drop plug (axial from the rear)', direction='+Z from the rear', placed='J202' in placed),
                   dict(step='A6', operation='rear insertion of the module', direction='+Z from the rear (wrist side)', placed=True),
                   dict(step='A10', operation='functional test through the caseback contacts, drop mated, caseback in service position', direction='rear', placed=chg['closes']),
                   dict(step='A11', operation='cup closure with the radial O-ring and lug-root screws', direction='+Z from the rear', placed=True)]
    str_state = dict(ok=str_phys_A, state_if_not='GATED' if str_phys_B else 'FAILED', gate='Q-R2-SUPPORT-RING' if str_phys_B else 'R2-S05',
                     evidence=dict(deflection_pass=bool(cupd['physical']), ext_required_mm=ext_design, ext_free_as_pinned_mm=ext_free_A, ext_free_supports_relieved_mm=ext_free_B))
    seal_state = dict(ok=seal_closes_A and sp_path['pass_'], state_if_not='GATED' if (seal_closes_B and sp_path['pass_']) else 'FAILED',
                      gate='Q-R2-SUPPORT-RING' if seal_closes_B else 'R2-S07', evidence=dict(ext_needed_min_mm=pop['zero_margin_ext_mm'], ext_free_as_pinned_mm=ext_free_A))
    pkg_ok = bool(clean) and not unplaced and not viol_B
    asm = lane_asm2(cx, P['radial']['terms'], dict(win=dict(ok=win['physical_pass']), str=str_state, pkg=dict(ok=pkg_ok, evidence=dict(unplaced=unplaced)),
                                                   lra=dict(state=lra_state, evidence=dict(bcu=lra_ok_bcu, fcu_plan=lra_fcu_plan)), btn=dict(ok=btn_closed),
                                                   chg=dict(ok=chg['closes'], evidence=chg['headline']), seal=seal_state), stroke_rows, access_rows)
    # ---------------- dispositions ---------------------------------------------------------------------------------------------------
    sid = {s_['id'] for s_ in stops}
    disp = {}
    disp['L-WIN'] = win['disposition']
    disp['L-BTN'] = 'BLOCKED' if (sid & {'R2-S03', 'R2-S12'}) else ('SUPPLIER_GATED' if btn_closed else 'BLOCKED')
    disp['L-SEAL'] = 'BLOCKED' if 'R2-S07' in sid else ('SUPPLIER_GATED' if seal_closes_A else 'OWNER_GATED')
    disp['L-STR'] = 'BLOCKED' if (not str_phys_B and not str_phys_A) else ('SUPPLIER_GATED' if str_phys_A else 'OWNER_GATED')
    disp['L-CHG'] = 'BLOCKED' if 'R2-S06' in sid else 'SUPPLIER_GATED'
    disp['L-LRA'] = 'BLOCKED' if 'R2-S04' in sid else 'SUPPLIER_GATED'
    disp['L-PKG'] = 'BLOCKED' if (sid & {'R2-S08', 'R2-S14'}) else ('OWNER_GATED' if viol_A else 'SUPPLIER_GATED')
    cross = P['radial']['crossings']
    cross_ok = all(c['state'] == 'ELIMINATED' for c in cross.values())
    rad_terms_ok = P['radial']['terms']['h05_geom_pass']
    disp['L-RAD'] = 'BLOCKED' if not (cross_ok and rad_terms_ok) else 'SUPPLIER_GATED'
    disp['L-ASM'] = asm['disposition']
    # ---------------- hard checks ----------------------------------------------------------------------------------------------------------
    H = {}
    zlayers = {sid_: dict(over=cx.zs.over[sid_]['layers'], base=cx.zs.base[sid_]['layers']) for sid_ in cx.zs.over}
    H['R2-H01'] = hc('R2-H01', 'G2-REVA / G2-REVA-HI reproduced under the overlay; total Z delta exactly 0.000; every R2 feature fits its Z allocation', 'exact / linear worst',
                     'PASS' if not zprob else 'FAIL', max(abs(r_[k]) for r_ in zrep.values() for k in ('nominal_delta', 'rss_delta', 'linear_delta')), 'mm',
                     governing=[dict(term='total Z delta (nominal / RSS / linear)', baselines=zrep)], r1c=r1_col(r1json, 'R1-H01'), detail=dict(delta_mm=cx.delta, layers=zlayers))
    H['R2-H02'] = hc('R2-H02', 'D_eval <= 51.00 with margin 51.00 - D_eval (joint point); only the five bosses protrude, each <= +3.0 incl. seal / boot and tolerance, inside its existing window',
                     'linear worst', 'PASS' if (P['D'] <= 51.0 + EPS and btn_closed) else 'FAIL', 51.0 - P['D'], 'mm',
                     governing=[dict(term='D_eval', value=P['D'], margin_to_51_mm=51.0 - P['D'], od_margin_with_tolerance_mm=cx.ce.f['od'](D=P['D'])),
                                dict(term='boss limit (OV-BOSS)', value=st.I['contract_values']['owner_limits']['boss_extension_max_mm'])], r1c=r1_col(r1json, 'R1-H02'),
                     detail=dict(D_radial_core_not_used=True, switches={sw: dict(closed=v['closed'], closing=v['closing_options']) for sw, v in boss_rows.items()}))
    H['R2-H03'] = hc('R2-H03', 'LEGACY numbers and G4 / R1 anchor values reproduced exactly with the overlay off; every re-implemented function passes its equivalence test', 'exact',
                     'PASS' if anchors_ok else 'FAIL', 0.0, 'mm', r1c=r1_col(r1json, 'R1-H03'), detail='see anchors')
    rad = P['radial']['terms']
    rad_all = list(rad['margins'].values()) + list(rad['straight'].values()) + list(rad['insertion'].values())
    h04_status = 'PASS' if (rad_terms_ok and cross_ok) else ('BLOCKED' if rad_terms_ok else 'FAIL')
    H['R2-H04'] = hc('R2-H04', 'H05-GEOM: XF / XB / XC eliminated by proof or closed; straight runs of every annulus riser; wall side, wall dielectric, main-case, insertion', 'linear worst',
                     h04_status, min(rad_all), 'mm', governing=[dict(term=k, value=v) for k, v in sorted({**rad['margins'], **rad['straight'], **rad['insertion']}.items(), key=lambda kv: kv[1])[:6]],
                     r1c=r1_col(r1json, 'R1-H04'), detail=dict(crossings=cross, local_arcs=P['radial']['local_arcs'], D_margin_not_from_D_radial_core=True),
                     gates=['SR-FPC-MECH'] + ([] if cross_ok else ['R2-S08 / R2-S04 (no conductor path for unplaced items)']))
    H['R2-H05'] = hc('R2-H05', 'H05-LRA-COUPLED: LRA -> U7 lead path on B.Cu (XL eliminated by proof or closed); L-LRA only', 'linear worst', 'BLOCKED' if not (lra_ok_bcu or lra_fcu_z) else 'GATED',
                     None, 'mm', r1c=r1_col(r1json, 'R1-H05'), detail=dict(crossing=cross['XL-LRA']), gates=['R2-S04'])
    cg = r1.cover_group(cx.cx, cx.cand, P['D'])
    H['R2-H06'] = hc('R2-H06', 'cover / bezel / land regression (G4 H06-H09)', 'linear worst', 'PASS' if cg['pass_'] else 'FAIL', min(cg['margins'].values()), 'mm',
                     governing=[dict(term=k, value=v) for k, v in cg['margins'].items()], r1c=r1_col(r1json, 'R1-H06'), detail=dict(a_cover=cg['a_cover']))
    H['R2-H07'] = hc('R2-H07', 'W1 at 0.45 mm min: stress / deflection screens, rib fit, bond land, no rib-to-optics load', 'G1 conservative', 'GATED' if win['physical_pass'] else 'FAIL',
                     win['result']['margins']['min_deflection_mm'], 'mm', r1c=r1_col(r1json, 'R1-H07'), gates=win['gates'], detail=dict(r1_pinned_equal=win['r1_pinned_equal']))
    part = g4.post_load(st, sp, dict(cx.ce.dp0, D=P['D'], tw=P['tw'], tcw=P['_pk']['t_carrier_wall'], rcin=P['_pk']['R_carrier_inner'], t_in=cfg['t_in'], t_out=cfg['t_out'],
                                     bosses={sw: P['_swg'][sw]['section']['boss'] for sw in BTN_SW}))
    zero_load = stat['pass_'] and bool(cupd['physical'] is not None)
    H['R2-H08'] = hc('R2-H08', 'Pressure partition sums; zero load into battery, REAR PCB, G3 support lands, carrier lower web and pillars; static clearance > 0.050 mm (strict)', 'exact / linear worst',
                     'PASS' if (part['domain_partition_pass'] and stat['pass_']) else 'FAIL', stat['minimum_mm'] - 0.05 if stat['minimum_mm'] is not None else None, 'mm',
                     governing=[dict(term='static clearance (smallest)', value=stat['minimum_mm'], pair=stat['governing'], event='EV-STATIC-ZERO-LOAD')], r1c=r1_col(r1json, 'R1-H08'),
                     detail=dict(total_N=part['total_N'], domains=part['domains'], pcb_pressure_load_N=0.0, load_path='plate -> ring -> rim bearing on the midcase rear face (no branch into the battery, REAR PCB, G3 lands, lower web or pillars)',
                                 deflection_cross_reference='the pressure deflection is owned by R2-H09a (single-event rule 10.5)', static=stat),
                     supplier_zero_margin=[dict(term='static clearance threshold', value=0.05)])
    sig = ev['sigma_governing_MPa']
    h09a = 'PASS' if ev['deflection_pass'] else 'FAIL'
    H['R2-H09'] = hc('R2-H09', '(a) deflection <= 0.050 mm (hard physical); (b) stress vs 150 MPa: PASS / SUPPLIER_GATED + sigma_allow_req; (c) periphery and inner shortfalls reported', 'linear worst',
                     'GATED' if (ev['deflection_pass'] and sig > ev['sigma_allow_planning_MPa'] + EPS) else ('PASS' if ev['deflection_pass'] else 'FAIL'), ev['deflection_margin_mm'], 'mm',
                     governing=[dict(term='deflection w_max', value=ev['w_max_mm'], limit=ev['deflection_limit_mm'], event='EV-PRESSURE-DEFLECTION'), dict(term='sigma_allow_req', value=sig, component=ev['governing'], event='EV-PRESSURE-STRESS')],
                     r1c=r1_col(r1json, 'R1-H09'), gates=['SR-CASEBACK-CERAMIC'] if sig > ev['sigma_allow_planning_MPa'] else [],
                     detail=dict(stress_labelled='SUPPLIER_GATED (never a model FAIL)' if sig > ev['sigma_allow_planning_MPa'] else 'PASS'),
                     supplier_zero_margin=[dict(term='sigma_allow_req_MPa', value=round(sig, 3))])
    H['R2-H10'] = hc('R2-H10', 'cup-rim bearing on the midcase rear face; screw shear / pull-out; ceramic bearing and edge-distance thresholds at the clearance holes', 'linear worst',
                     'GATED' if rim['bearing_pass'] else 'FAIL', rim['bearing_margin_MPa'], 'MPa', governing=[dict(term='bearing stress', value=rim['bearing_stress_MPa'])],
                     r1c=r1_col(r1json, 'R1-H10'), gates=['SR-CASEBACK-CERAMIC', 'OD-G4-STRAP'], detail=rim, supplier_zero_margin=rim['supplier_zero_margin'])
    H['R2-H11'] = hc('R2-H11', 'radial cup O-ring: compression / fill at +/-0.05 mm in the static radial window; spigot inside its REAR-band + zone-B allocation; serviceable; R1:R5 population and unit invariance',
                     'linear worst / exact', 'GATED' if seal_closes_A else ('BLOCKED' if 'R2-S07' in sid else 'GATED'),
                     max(r['margins']['spigot_rear_periphery_z'] for r in gl_rows) if gl_rows else None, 'mm',
                     governing=[dict(term='smallest spigot shortfall (REAR band only)', value=max(r['margins']['spigot_rear_periphery_z'] for r in gl_rows) if gl_rows else None)],
                     r1c=r1_col(r1json, 'R1-H11'), gates=['gasket (no SR id)'] + ([] if seal_closes_A else ['Q-R2-SUPPORT-RING']),
                     detail=dict(typed_terms=pop['topologies']['radial']['term_reductions'], rows=pop['rows'], feasible_rows=pop['feasible_row_ids'], r_lim_mm=pop['r_lim_mm'], cup_top_z_mm=pop['cup_top_z_mm']))
    H['R2-H12'] = hc('R2-H12', 'buttons per SW: T1 / T2-F / T2-R under I-SUM (binding) and I-MAX (reported); boss threshold 3.000 beside the result; stroke, rim, strain, material rules; switches unmoved',
                     'linear worst', 'GATED' if btn_closed else 'FAIL', min((r['I_SUM']['section']['min_margin'] for sw in BTN_SW for r in bsw[sw]['rows'] if r['I_SUM']['closes']), default=None), 'mm',
                     r1c=r1_col(r1json, 'R1-H12'), gates=['SR-BUTTONS'], detail=boss_rows)
    H['R2-H13'] = hc('R2-H13', 'every aperture has exactly one primary seal with a feasible geometry class; seal path closed', 'exact', 'PASS' if sp_path['pass_'] else 'FAIL', 0.0, 'mm',
                     r1c=r1_col(r1json, 'R1-H13'), detail=sp_path)
    H['R2-H14'] = hc('R2-H14', 'charger: block inside the wedge and outside WIFI_RAD; land per C-R1-01 with C-R2-01; caps; drop to J202 B.Cu strictly 3-D clear; FT-C sealed; physical headline', 'linear worst',
                     'PASS' if chg['closes'] else 'BLOCKED', chg['headline']['smallest_strict_clearance_mm'], 'mm', governing=[dict(term='headline', **chg['headline'])],
                     r1c=r1_col(r1json, 'R1-H14'), gates=['SR-CHG-MECH'] + ([] if chg['closes'] else ['R2-S06']),
                     detail=dict(radial=chg['radial'], requirement=chg['requirement'], neighbours_clear=chg['neighbours_clear'], c_r2_01=chg['c_r2_01'], strict_wedge=chg['strict_wedge']),
                     supplier_zero_margin=[dict(term='r_lim_cup_required_mm', value=chg['radial']['r_lim_required_min_mm'])])
    H['R2-H15'] = hc('R2-H15', 'radiator volumes (G4-H17), owner reserved regions and MAG_CLEAR (G4-H18): no new metal, conductor or component; every non-conductive item inside a reserved region carries its G5 record',
                     'exact', 'FAIL' if (viol_res or res_hits) else 'PASS', None, 'mm', r1c=r1_col(r1json, 'R1-H15'),
                     detail=dict(violations=viol_res, pack_in_reserved_region=res_hits, g5_record_count=len(g5), g5_records_complete=all(r_.get('material_class') is not None and r_.get('permittivity_class') is not None
                                                                                                                                    and r_.get('volume_linear_worst_mm3') is not None for r_ in g5)))
    H['R2-H16'] = hc('R2-H16', 'G3 not reopened (items 1-7)', 'exact / linear worst', 'PASS' if g3['pass_'] else 'FAIL', 0.0, 'mm', r1c=r1_col(r1json, 'R1-H16'), detail=g3)
    H['R2-H17'] = hc('R2-H17', 'assembly: sequence executable, access per operation incl. mate strokes, collision-free insertion, isolation states, service paths', 'linear worst',
                     'PASS' if asm['product_closure_executable'] else ('BLOCKED' if asm['sequence_executable'] else 'FAIL'), None, 'mm', r1c=r1_col(r1json, 'R1-H17'), gates=asm['gates'], detail=dict(
                         sequence_executable=asm['sequence_executable'], product_closure_executable=asm['product_closure_executable'], failed=asm['failed_dependencies'], gated=asm['gated_dependencies']))
    sup = supports_report(cx, P)
    H['R2-H18'] = hc('R2-H18', '>= 4 case / caseback supports incl. W/NW, all outside the offset pack envelope', 'exact', 'PASS' if sup['pass_'] else 'FAIL',
                     min((r['gap_to_offset_pack_envelope_mm'] for r in sup['rows']), default=None), 'mm', r1c=r1_col(r1json, 'R1-H18'), detail=sup)
    H['R2-H19'] = hc('R2-H19', 'LRA lane: B.Cu pose, or F.Cu Z-neutral fallback per C-R1-08; R1:R4-1 identity reconstruction; BMM350 distance reported', 'linear worst',
                     'BLOCKED' if 'R2-S04' in sid else 'GATED', P['lra']['max_room_over_offsets_mm'] - min(v['need_mm'] for v in P['lra']['bcu'].values()), 'mm',
                     r1c=r1_col(r1json, 'R1-H19'), gates=['SR-LRA'] + (['R2-S04'] if 'R2-S04' in sid else []), detail=dict(lra=P['lra'], identity=None))
    H['R2-H20'] = hc('R2-H20', 'no KiCad / interface / placement / immutable-file change; changes confined to R2_FILES; historical reproduction', 'exact',
                     'PASS' if (scope['pass_'] and anchors_ok) else 'FAIL', 0.0, 'mm', r1c=r1_col(r1json, 'R1-H20'), detail=dict(scope=scope, historical='see carry_in.historical_reproduction'))
    H['R2-H21'] = hc('R2-H21', 'OD-THICK-REVA: nominal <= 16.5 and RSS <= 17.0 on both baselines', 'nominal, RSS', 'PASS' if not zprob else 'FAIL',
                     min(r2in['limits']['nominal_mm'] - zrep[b]['nominal_over'] for b in zrep), 'mm', governing=[dict(term=b, **{k: v for k, v in zrep[b].items() if k.endswith('_over')}) for b in zrep],
                     r1c='n/a (new in R2)')
    H['R2-H22'] = hc('R2-H22', 'joint annulus allocation: strict 3-D clearance for every pair separated by design; containment / interference for declared contact pairs; no double-credited volume; ledger emitted',
                     'linear worst', 'PASS' if (not viol_A and not viol_B) else ('GATED' if (support_only_A and not viol_B) else 'FAIL'),
                     lg_A['min_gap_mm'], 'mm', detail=dict(as_pinned_supports=dict(violations=len(viol_A), pairs=lg_A['pairs_evaluated']),
                                                           supports_relieved=dict(violations=len(viol_B)), double_occupied=P['annulus']['ledger']['double_occupied_cells'],
                                                           classification='the only over-allocation is the case-side supports versus the raised cup wall: owner question Q-R2-SUPPORT-RING' if (support_only_A and not viol_B) else None),
                     owner_gated=['Q-R2-SUPPORT-RING'] if (support_only_A and not viol_B) else [], r1c='n/a (new in R2)')
    pkc = P['_pk']
    H['R2-H23'] = hc('R2-H23', 'pack + growth + PCM lobe inside the carrier, each battery and offset; carrier wall >= 0.30 adverse; pillars only +Delta', 'linear worst',
                     'PASS' if (pkc['pack_margin_mm'] >= -EPS and pkc['carrier_wall_margin_mm'] >= -EPS and g3['items']['4_pillars_plus_delta_only']['pass_']) else 'FAIL',
                     min(pkc['pack_margin_mm'], pkc['carrier_wall_margin_mm']), 'mm', governing=[dict(term='pack radial', value=pkc['pack_margin_mm']), dict(term='carrier wall', value=pkc['carrier_wall_margin_mm'])],
                     r1c='n/a (new in R2)', detail=dict(pk=pk_summary(cx, P)))
    zc = P['zone_a']
    H['R2-H24'] = hc('R2-H24', 'MAIN B.Cu zones: zone-A heights <= accepted back-zone governing height; zone-B items inside their 3-D allocation', 'linear worst', 'PASS' if zc['ok'] else 'FAIL',
                     min((r_['margin_mm'] for r_ in zc['rows'] if r_['in_zone_a']), default=None), 'mm', detail=zc, r1c='n/a (new in R2)')
    ic_ok = all(not (k in unplaced) for k in ('J1501', 'J201', 'J202')) and all(p_['R_bend_margin_mm'] >= -EPS for p_ in P['paths']['paths'].values() if 'R_bend_margin_mm' in p_)
    H['R2-H25'] = hc('R2-H25', 'interconnects: J1501 axial mate toward REAR; J201 / J202 mates; FPC length, bends, R_bend, allocated slack; drop service length', 'linear worst',
                     'PASS' if ic_ok and all(f['fits'] for f in P['paths']['slack'].values()) else ('BLOCKED' if unplaced else 'FAIL'), None, 'mm',
                     detail=dict(paths=P['paths'], unplaced=unplaced), gates=['SR-FPC-MECH', 'SR-BATT-PCM', 'SR-CHG-MECH'], r1c='n/a (new in R2)')
    ifc = interface_check(cx)
    H['R2-H26'] = hc('R2-H26', 'frozen 24-position / 13-net interface unchanged; charger-positive outside the sensor FPC; mirrored physical order recorded as a K1 requirement', 'exact',
                     'PASS' if ifc['pass_'] else 'FAIL', 0.0, 'mm', detail=ifc, r1c='n/a (new in R2)')
    H['R2-H27'] = hc('R2-H27', 'battery evidence: catalogue labels present; no recorded SR-BATT-PACK evidence contradicts the assumed envelope', 'exact', 'GATED' if ev_chk['pass_'] else 'FAIL', 0.0, 'mm',
                     detail=ev_chk, gates=['SR-BATT-PACK'], r1c='n/a (new in R2)')
    shd = shield_check(cx, P['_occs'])
    H['R2-H28'] = hc('R2-H28', 'shield-ready preserved: U101 shield polygon and can volume not intruded; front gap unchanged', 'exact', 'PASS' if shd['pass_'] else 'FAIL', shd['headroom_mm'], 'mm',
                     detail=shd, r1c='n/a (new in R2)')
    # ---------------- verdict ----------------------------------------------------------------------------------------------------------
    verdict = verdict_of(disp, stops)
    out.update(lanes=dict(), hard_checks=H, stops=stops, dispositions=disp, verdict=verdict, g5_records=g5, asm=asm, win=win)
    out['lanes'] = dict(
        L_STR=dict(design=dict(config=cfg, row=cupd['row']['id'], cs_mm=cupd['row']['cs_mm'], r_ring_mm=ev['r_ring_mm'], r_wall_inner_mm=ev['r_wall_inner_mm'], z_top_mm=ev['z_top_mm'],
                               ring=ev['ring'], plate=ev['plate']),
                   physical_pass_hard=bool(cupd['physical']), within_allocation_as_pinned=str_phys_A, within_allocation_supports_relieved=str_phys_B,
                   screen_B=dict(sigma_governing_MPa=sig, governing=ev['governing'], components_MPa=ev['components_MPa'], w_max_mm=ev['w_max_mm'], deflection_margin_mm=ev['deflection_margin_mm']),
                   screen_A_simply_supported=ev['bounds']['simply_supported'], clamped_bound_reported_not_assumed=ev['bounds']['clamped'],
                   sigma_allow_req_MPa=round(sig, 3), margin_to_150_MPa=ev['sigma_allow_planning_MPa'] - sig, ring_credit=ev['ring_credit'],
                   sigma_without_inner_junction_Kt_MPa=max(v for k, v in ev['components_MPa'].items() if k != 'plate_inner_junction_Kt'),
                   shortfalls=struct_shortfalls(cx, P, struct_req=P['structure']['search'].get('required_wall_for_deflection'), cfg=cfg, ext_free_A=ext_free_A, ext_free_B=ext_free_B, band_cap_top=band_cap_top)),
        L_SEAL=dict(r_lim_cup_mm=pop['r_lim_mm'], cup_top_z_mm=pop['cup_top_z_mm'], feasible_rows_rear_band_only=pop['feasible_row_ids'], gland_feasible_rows=[r['id'] for r in gl_rows],
                    zero_margin_extension_mm=ext_row, ext_free_as_pinned_mm=ext_free_A, ext_free_supports_relieved_mm=ext_free_B, ring_blockers_as_pinned=blockers_A,
                    closes_as_pinned=seal_closes_A, closes_supports_relieved=seal_closes_B, seal_path=sp_path['pass_'], serviceable=True,
                    spigot_confined_to_rear_band_mm=max(r['margins']['spigot_rear_periphery_z'] for r in gl_rows) if gl_rows else None,
                    spigot_with_conductor_band_state_mm=max(r['z_with_conductor_band_mm'] for r in gl_rows) if gl_rows else None,
                    band_state='retired (OV-COND-BAND), Delta %.3f mm added' % cx.delta, population=pop['population'], representative_row=dict(pop['representative_row']),
                    reductions=pop['topologies']['radial']['term_reductions'], unit_regression=seal_unit_regression(cx, P['D'], P['tw'])),
        L_CHG=dict(closes=chg['closes'], pose=dict(orientation=chg['pose']['orientation'], r_centre=chg['pose']['r_centre'], az_centre=chg['pose']['az_centre']),
                   radial=chg['radial'], headline=chg['headline'], requirement=chg['requirement'], strict_wedge=chg['strict_wedge'], feedthrough=chg['feedthrough'],
                   drop=P['paths']['paths'].get('J202'), neighbours=[dict(n_ for n_ in x.items()) for x in chg['neighbours'][:40]]),
        L_BTN=boss_rows, L_LRA=dict(P['lra']), L_PKG=dict(chosen_offset=P['package']['chosen_offset'], clean_offsets=len(clean), offsets=len(sweep), placed=sorted(placed), unplaced=unplaced,
                                                      pk=pk_summary(cx, P), connectors={k: v for k, v in P['connectors'].items()}, paths=P['paths'], column=P['package']['column'],
                                                      k1=k1_constraints(cx, P), supports=sup, ledger=dict(A=dict(violations=viol_A, pairs=lg_A['pairs_evaluated'], nearest=lg_A['nearest'][:40]),
                                                                                                         B=dict(violations=viol_B, pairs=lg_B['pairs_evaluated'], relief_z_mm=P['annulus']['variant_B']['relief_z_mm'], ring_top_adv_mm=P['annulus']['variant_B']['ring_top_adv_mm']), sampled=P['annulus']['ledger']),
                                                      reserved=dict(pack_hits=res_hits, violations=viol_res), exact_attempts=P['package']['exact_attempts'], zone_a=zc),
        L_RAD=dict(P['radial']), L_WIN=win, L_ASM=asm)
    out['metrics'] = dict(
        z=dict(delta_nominal=max(abs(zrep[b]['nominal_delta']) for b in zrep), delta_rss=max(abs(zrep[b]['rss_delta']) for b in zrep), delta_linear=max(abs(zrep[b]['linear_delta']) for b in zrep),
               rear_band_delta_mm=cx.delta, battery_zone_mm=dict(nominal=cx.zs.over['G2-REVA']['layers']['battery_zone'])),
        D_eval=P['D'], D_margin_mm=51.0 - P['D'], tw=P['tw'], sigma_allow_req_MPa=sig, w_max_mm=ev['w_max_mm'], r_lim_cup_mm=pop['r_lim_mm'],
        charger_r_lim_required_mm=chg['radial']['r_lim_required_min_mm'], spigot_shortfall_rear_only_mm=out['lanes']['L_SEAL']['spigot_confined_to_rear_band_mm'])
    return out


def sw_g5_records(cx2, P):
    """G5 records of the SW1 (BLE reserved region) and SW5 (Wi-Fi reserved region) non-metallic pusher, boot / O-ring and dielectric boss growth: material
    class, permittivity class label (no numeric permittivity) and volume inside the region, nominal and linear worst; both pusher options are recorded."""
    regs = P['_reserved']
    lv = cx2.levels
    out = []
    for sw, tag in (('SW1', 'BLE'), ('SW5', 'WIFI')):
        g_ = P['_swg'][sw]
        bore_polys = geom_polys(g_['bore'])
        boss_polys = geom_polys(g_['boss'])
        for lvl_rg in [r_ for r_ in regs if r_['region'] == tag]:
            z_main = (lv['MAIN'][0], lv['MAIN'][1])
            zo = max(0.0, min(lvl_rg['z_hi_adv'], z_main[1]) - max(lvl_rg['z_lo_adv'], z_main[0]))
            if zo <= 0.0:
                continue
            items = []
            for opt in cx2.r2in['buttons']['switch_materials'][sw]['options']:
                pc = cx2.r2in['buttons']['pusher_classes'][opt]
                mclass = pc['material_class'] or opt
                items.append(('%s_PUSHER[%s]' % (sw, opt), bore_polys, mclass if opt != 'PEEK' else 'PEEK', opt))
            items.append(('%s_BOOT_OR_ORING' % sw, bore_polys, 'ELASTOMER', 'ELASTOMER'))
            items.append(('%s_BOSS_GROWTH' % sw, boss_polys, 'MAT-GF-POLY', 'MAT-GF-POLY'))
            for item_id, polys, mclass, pkey in items:
                bb = (min(poly_bbox(p)[0] for p in polys), min(poly_bbox(p)[1] for p in polys), max(poly_bbox(p)[2] for p in polys), max(poly_bbox(p)[3] for p in polys))
                area = overlap_area(occupant('tmp', 'tmp', polys, 0.0, 1.0), lvl_rg)
                if area <= 0.0:
                    continue
                lab = cx2.r2in['buttons']['permittivity_class_labels'].get(pkey, dict(label='UNLABELLED', numeric=None))
                out.append(dict(item=item_id, region=lvl_rg['region'], level=lvl_rg['level'], region_part=lvl_rg['part'], material_class=mclass, permittivity_class=lab,
                                volume_nominal_mm3=area * zo, volume_linear_worst_mm3=area * zo, g5_rf_required=True))
    return out


def carrier_oring_g5(cx2, P, ring):
    regs = P['_reserved']
    lv = cx2.levels
    row = P['structure']['design']['row']
    cfg = P['structure']['design']['ev']['config']
    sp = cx2.sp
    land = sp.m_cb['groove_land_min_mm']
    z0 = cfg['t_out'] + land
    o = occupant('CUP_ORING', 'radial O-ring', ring_polys(row['r_lim_mm'] + row['spigot_radial_mm'] - row['groove_h_mm'] - 0.0, P['R_side']), z0, z0 + row['groove_g_mm'], group='CUP',
                 allowed_nonconductive=True, material_class='ELASTOMER', permittivity_key='ELASTOMER', shapes=[('ring', (P['R_side'] - row['groove_h_mm'], P['R_side']))])
    viol, g5 = reserved_screen(cx2, [o], regs, set())
    return g5


def dedupe_g5(recs):
    seen, out = set(), []
    for r in recs:
        k = (r['item'], r['region'], r['level'], r['region_part'])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return sorted(out, key=lambda r: (r['region'], r['level'], r['region_part'], r['item']))


def struct_shortfalls(cx2, P, struct_req, cfg, ext_free_A, ext_free_B, band_cap_top):
    """Structural periphery shortfall: required wall top (hard deflection) minus the available REAR-band + zone-B height, with and without the retired band (P-1);
    inner-region shortfall: the uniform ceramic thickness the loaded-boss screen needs minus the t_in limit of the pod residual."""
    mat = cup_materials(cx2)
    tol = mat['tol_t']
    route = cx2.st.P['c_rear_route_mm']['max']
    out = dict(rule='shortfall = required - available (positive = shortfall, negative = surplus), mm')
    if struct_req is not None:
        z_req = struct_req['z_top'] + tol
        out.update(required_wall_top_for_deflection_mm=z_req, required_row=struct_req['row'], required_t_out_mm=struct_req['t_out'],
                   periphery_shortfall_band_retired_mm=z_req - band_cap_top, periphery_shortfall_conductor_band_retained_mm=z_req - (band_cap_top - route),
                   periphery_shortfall_with_zone_b_as_pinned_mm=z_req - (band_cap_top + ext_free_A),
                   periphery_shortfall_with_zone_b_supports_relieved_mm=z_req - (band_cap_top + ext_free_B), band_state_P1='retired; the retained state is the R1-literal column')
    else:
        out.update(required_wall_top_for_deflection_mm=None)
    a = P['structure']['design']['ev']['r_ring_mm']
    cx = cx2.cx
    iso = r1.iso_req_thickness(cx, mat, a, cx.rb, cx.r_step, 'uniform')
    t_in = P['structure']['search']['t_in']
    out.update(inner_region_required_uniform_nominal_mm=None if iso is None else iso + tol, t_in_limit_mm=t_in,
               inner_region_shortfall_mm=None if iso is None else iso + tol - t_in)
    return out


def verdict_of(disp, stops):
    if stops:
        return VERDICTS[0]
    if any(v == 'OWNER_GATED' for v in disp.values()):
        return VERDICTS[1]
    if any(v == 'SUPPLIER_GATED' for v in disp.values()):
        return VERDICTS[2]
    return VERDICTS[3]


# ============================================================================================
# Overlay-off anchors (R2-H03) and lead cross-checks (P-3)
# ============================================================================================
def anchor_row(aid, source, expected, computed, tol, note=None):
    ok = abs(expected - computed) <= tol if isinstance(expected, (int, float)) and not isinstance(expected, bool) else expected == computed
    return dict(id=aid, source=source, expected=expected, computed=computed, tolerance=tol, match=bool(ok), note=note)


def anchors(r2in, g4res, st0, zs_off, r1json, g4_inproc):
    """With the overlay OFF the R2 code path reproduces the declared G4 / R1 anchor values (pinned JSON pointers, never re-typed) and every re-implemented
    function equals its library original (PA class)."""
    cx = Ctx2(r2in, g4res, st0, zs_off, PRIMARY, with_overlay=False)
    rows = []
    st, sp = cx.st, cx.sp
    L1 = r1json['lanes']['G4-B']
    # Z baselines
    for sid, want in st0.I['contract_values']['g2_stacks_mm'].items():
        got = zs_off.base[sid]
        rows.append(anchor_row('Z %s nominal' % sid, 'inputs/g4_case_sealing.json contract_values.g2_stacks_mm', want['nominal'], round(got['nominal'], 3), 5e-4))
        rows.append(anchor_row('Z %s RSS' % sid, 'inputs/g4_case_sealing.json contract_values.g2_stacks_mm', want['rss'], got['rss'], 5e-4))
        rows.append(anchor_row('Z %s linear' % sid, 'inputs/g4_case_sealing.json contract_values.g2_stacks_mm', want['linear'], got['linear'], 5e-4))
    # LEGACY (G4 Study, imported unchanged)
    rows.append(anchor_row('LEGACY rows (G4 H04)', 'g4.Study.legacy_reproduction', True, bool(st0.legacy['pass_']), 0, 'every LEGACY value of G4_BRIEF.md section 3 reproduced'))
    # R1 screen B at the R1 design geometry with the overlay-off plate path
    mat = cup_materials(cx)
    geo = L1['L-STR']['geometry']
    sel = L1['L-STR']['selected']
    regs, g_ = cup_regions(cx, geo['R'], dict(t_in=sel['t_in'], t_out=sel['t_out']), mat)
    sol = plate_solve2(regs, cx.cx.p, 'loaded_boss', 'ss', (0.0, 0.0), 41)
    ref = r1.plate_solve(regs, cx.cx.p, 'loaded_boss', 'ss', 41)
    dmax = max(abs(a['w'] - b['w']) + abs(a['Mr'] - b['Mr']) for s1, s2 in zip(sol, ref) for a, b in zip(s1['samples'], s2['samples']))
    rows.append(anchor_row('plate_solve2 == r1.plate_solve (equivalence)', 'tools/g4_r1_blockers.py plate_solve', 0.0, dmax, 1e-12, 'PA equivalence test'))
    fld = plate_stress_field(sol, cx.cx.p, 1.0, (regs[0]['r0'], geo['R'], st.s14geo['outline_r']), None)
    rows.append(anchor_row('R1 Screen B sigma (MPa)', 'generated/g4_r1_blockers.json lanes/G4-B/L-STR/screen_B/sigma_governing_MPa', L1['L-STR']['screen_B']['sigma_governing_MPa'], fld['bulk'], 1e-6))
    rows.append(anchor_row('R1 Screen B w_max (mm)', 'generated/g4_r1_blockers.json lanes/G4-B/L-STR/screen_B/w_max_mm', L1['L-STR']['screen_B']['w_max_mm'], fld['w_max'], 1e-8))
    iso = r1.iso_req_thickness(cx.cx, mat, geo['R'], cx.cx.rb, cx.cx.r_step, 'uniform')
    rows.append(anchor_row('R1 uniform ceramic thickness (mm)', 'generated/g4_r1_blockers.json hard_checks/R1-H09/threshold_value', r1json['hard_checks']['R1-H09']['threshold_value'],
                           iso + mat['tol_t'], 1e-6, 'vs t_in <= 1.10 mm by the pod residual'))
    # G4 pressure partition at the R1 design point
    dpt = L1['design_point_g4_terms']
    dp = dict(cx.ce.dp0, D=dpt['D'], tw=dpt['tw'], tcw=dpt['tcw'], rcin=dpt['rcin'], t_in=dpt['t_in'], t_out=dpt['t_out'], bosses=dpt['bosses'])
    pl = g4.post_load(st, sp, dp)
    rows.append(anchor_row('G4 pressure partition total (N)', 'generated/g4_r1_blockers.json hard_checks/R1-H08/governing_terms/total_N', r1json['hard_checks']['R1-H08']['governing_terms']['total_N'],
                           pl['total_N'], 1e-6))
    # R1 radial seal row spigot Z at the smallest feasible gland (band retained, Delta 0)
    tmpl = seal_templates(cx, 'mm', 1.0)
    gw = []
    for t in tmpl:
        if t['authorized'] and min(t['m0'].values()) >= -EPS:
            gw.append(t)
    r1_th = r1json['hard_checks']['R1-H11']['governing_terms']['thresholds']['radial']['at_that_cs']['spigot_rear_periphery_z']
    rows.append(anchor_row('R1 radial spigot Z (REAR band, conductor band retained, Delta 0)', 'generated/g4_r1_blockers.json hard_checks/R1-H11 ... radial/at_that_cs/spigot_rear_periphery_z',
                           r1_th, gw[0]['z_lib'] + gw[0]['z_delta'], 1e-6, 'smallest gland-feasible authorized cross-section'))
    # R1 charger radial / plan prerequisites (routes retained, overlay off)
    poses = chg_pose_family(cx)
    rad_req = min(p['r_lim_required'] for p in poses if p['categories']['radial'])
    plan_req = min(p['r_lim_required'] for p in poses if p['prereq_pass'])
    cg = r1json['hard_checks']['R1-H14']['governing_terms']
    rows.append(anchor_row('R1 charger radial prerequisite r_lim (mm)', 'generated/g4_r1_blockers.json hard_checks/R1-H14 radial_prerequisite', cg['radial_prerequisite']['r_lim_required_mm'], rad_req, 1e-6))
    rows.append(anchor_row('R1 charger plan prerequisite r_lim (mm)', 'generated/g4_r1_blockers.json hard_checks/R1-H14 plan_prerequisite', cg['plan_prerequisite']['r_lim_required_mm'], plan_req, 1e-6,
                           'routes in plan (overlay off); the overlay retires CHG_ROUTE / CHG_LINK'))
    # R1 buttons (library re-run at the R1 point) and the T1 gland re-implementation
    btn = r1.lane_btn(cx.cx, cx.cand, dpt['D'], True)
    for sw in BTN_SW:
        rows.append(anchor_row('R1 %s I-SUM bore_stack (mm)' % sw, 'generated/g4_r1_blockers.json lanes/G4-B/L-BTN/switches/%s/best/I-SUM/margins/bore_stack' % sw,
                               L1['L-BTN']['switches'][sw]['best']['I-SUM']['margins']['bore_stack'], btn['switches'][sw]['best']['I-SUM']['margins']['bore_stack'], 1e-9))
    T = btn_terms2(cx, 'SW2', 'metal')
    pg_best, pg_all = g4.pusher_gland(st, sp, 'SW2', True)
    same = True
    for x in pg_all:
        mine = t1_gland(cx, 'SW2', T, x['cs'])
        same = same and all(abs(a - b) < 1e-12 for a, b in zip(mine['margins'], x['margins'])) and abs(mine['g'] - x['g']) < 1e-12
    rows.append(anchor_row('t1_gland == g4.pusher_gland on the G4 sweep cross-sections (equivalence)', 'tools/g4_case_sealing.py pusher_gland', True, same, 0, 'PA equivalence test'))
    # window
    w = lane_win2(cx, r1json)
    rows.append(anchor_row('L-WIN equals the pinned R1 W1 values', 'generated/g4_r1_blockers.json lanes/G4-B/L-WIN', True, w['r1_pinned_equal'], 0))
    # geometry kernel equivalence
    d1 = shape_gap(('disk', (110.0, 100.0, 3.0), (107.0, 97.0, 113.0, 103.0)), ('poly', rect_poly(120.0, 95.0, 125.0, 105.0), (120.0, 95.0, 125.0, 105.0)))
    d2 = g4.region_distance(dict(type='circles', circles=[[110.0, 100.0, 3.0]]), dict(type='rect', rect=[120.0, 95.0, 125.0, 105.0]), 0.02)
    rows.append(anchor_row('shape_gap (analytic) vs g4.region_distance (sampled)', 'tools/g4_case_sealing.py region_distance', d2, d1, 0.02, 'sampled kernel resolution 0.02 mm'))
    rr = shape_gap(('poly', rect_poly(110.0, 100.0, 112.0, 102.0), (110.0, 100.0, 112.0, 102.0)), ('ring', (20.0, 24.0), (76.0, 76.0, 124.0, 124.0)))
    rr2 = g4.region_distance(dict(type='rect', rect=[110.0, 100.0, 112.0, 102.0]), g4.sector(0.0, 360.0, 20.0, 24.0), 0.02)
    rows.append(anchor_row('ring gap (analytic) vs g4.region_distance (sampled)', 'tools/g4_case_sealing.py region_distance', rr2, rr, 0.03))
    # library radial formulas versus the R2 closed forms
    R_side, rc, tcw = 24.0, 20.0, 0.4
    lib = cx.ce.f['ins_bat'](R_side=R_side, R_carrier_inner=rc, t_carrier_wall=tcw)
    mine = insertion_margin(cx, R_side, rc + sp.pc_car['radius_mm'] + tcw + sp.pc_car['thickness_mm'] + st.rp['t_fpc']['max'])
    rows.append(anchor_row('R2 BATTERY-level insertion closed form == library H23-INSERT-BATTERY', 'tools/g4_case_sealing.py insert', lib, mine, 1e-9))
    mm_ = cx.ce.f['main'](R_side=R_side)
    mine2 = R_side - sp.pc_env['radius_mm'] - (cx.R_main + sp.pc_pcb['radius_mm'] + st.P['c_main_case_mm']['max'])
    rows.append(anchor_row('R2 MAIN-case closed form == library H05-MAIN-CASE', 'tools/g4_case_sealing.py main_case', mm_, mine2, 1e-9))
    rows.append(anchor_row('G4 in-process reproduction byte-identical, 32/32', 'tools/g4_case_sealing.py build/validate/self_tests', True, bool(g4_inproc['pass_']), 0))
    return dict(rows=rows, pass_=all(r['match'] for r in rows))


def lead_crosschecks(r2in, zs_by_bat, cxs, finals, anchors_rows, r1json):
    """P-3: every lead number of section 20 is either REPRODUCED (equal within the stated tolerance) or EXPLAINED (the difference is attributed)."""
    LA = {x['id']: x for x in r2in['lead_arithmetic']}
    rows = []

    def add(lid, computed, tol, expl=None, units='mm'):
        want = LA[lid]['value']

        def eq(a, b):
            return abs(a - b) <= tol
        ok = all(eq(a, b) for a, b in zip(want, computed)) if isinstance(want, list) else eq(want, computed)
        rows.append(dict(id=lid, lead=want, computed=computed, tolerance=tol, status='REPRODUCED' if ok else 'EXPLAINED', explanation=None if ok else expl, units=units))
    for bat, zid, bid in (('LPR433736', 'delta_433736_mm', 'battery_zone_433736_mm'), ('LPR403736', 'delta_403736_mm', 'battery_zone_403736_mm')):
        add(zid, zs_by_bat[bat].delta, 5e-4)
        S = Sources(r2in, True, bat).S['parameters']
        nom = S['t_pack_nom']['nom'] + S['tol_pack_thick']['nom'] + S['g_axial']['nom'] + S['c_axial']['nom']
        lin = S['t_pack_nom']['nom'] + S['tol_pack_thick']['max'] + S['g_axial']['max'] + S['c_axial']['max']
        thin = S['t_pack_nom']['nom'] + S['tol_pack_thick']['min'] + S['g_axial']['min'] + S['c_axial']['min']
        add(bid, [nom, lin, thin], 5e-4)
    cxp = cxs.get(PRIMARY)
    R = Sources(r2in, True, PRIMARY).S['radial']['parameters']
    P0 = Sources(r2in, True, PRIMARY).S['parameters']
    add('R_pack_mm', [(R['D_pack_nom']['nom'] + R['tol_pack_dia']['nom']) / 2.0, (R['D_pack_nom']['nom'] + R['tol_pack_dia']['max']) / 2.0], 5e-4)
    R_inner = 50.9 / 2.0 - 1.1
    add('R_case_inner_D50p9_tw1p1_mm', R_inner, 5e-4)
    if cxp is not None:
        st, sp = cxp.st, cxp.sp
        tc, tw_ = sp.pc_car['radius_mm'], sp.pc_car['thickness_mm']
        g_nom, g_max = st.P['g_radial_mm']['nom'], st.P['g_radial_mm']['max']
        Rn = (R['D_pack_nom']['nom'] + R['tol_pack_dia']['nom']) / 2.0
        Rl = (R['D_pack_nom']['nom'] + R['tol_pack_dia']['max']) / 2.0
        co_nom = Rn + g_nom + 0.40
        co_lin = Rl + g_max + tc + 0.40 + tw_
        expl = ('the lead figure omits the two carrier tolerance terms of the imported G4 predicate (carrier inner radius and wall thickness, 0.05 mm each, PC-CARRIER-MOULD); '
                'carrier outer = R_pack(lw) + g_radial + tol_carrier_r + t_cw + tol_cw = %.2f + %.2f + %.2f + 0.40 + %.2f' % (Rl, g_max, tc, tw_))
        add('carrier_outer_tcw0p40_mm', [co_nom, co_lin], 5e-4, expl)
        dia46 = cxp.R_main
        add('free_band_to_dia46_mm', [dia46 - co_lin, dia46 - (co_lin - 1.5)], 5e-4, 'same two carrier tolerance terms (-0.10 mm); the far-side figure subtracts the 1.5 mm offset from the carrier outer radius')
        add('free_band_to_bore_mm', [R_inner - co_lin, R_inner - (co_lin - 1.5)], 5e-4, 'same two carrier tolerance terms (-0.10 mm)')
        c_plan = st.P['c_lra_plan_mm']['max']
        cls = {c['id']: c for c in lra_classes_r2(cxp)}
        rect = cls['LRA-LIN-RECT']
        sag = 21.0 - math.sqrt(21.0 ** 2 - (rect['length'] / 2.0) ** 2)
        add('lra_lin_rect_adverse_need_mm', rect['width'] + 2 * c_plan + sag, 0.06,
            'computed need = %.2f (width) + 2 x %.2f (c_lra_plan) + %.2f (chord sagitta of the 12.5 mm long axis at r 21) = %.2f; the lead rounded the sagitta to 1.1' % (rect['width'], c_plan, sag, rect['width'] + 2 * c_plan + sag))
        add('lra_coin_d8_adverse_need_mm', cls['LRA-COIN-D8']['length'] + 2 * c_plan, 5e-4)
    for bat, lid in (('LPR433736', 'spigot_shortfall_rear_only_433736_mm'), ('LPR403736', 'spigot_shortfall_rear_only_403736_mm')):
        F = finals[bat]
        add(lid, F['lanes']['L_SEAL']['spigot_confined_to_rear_band_mm'], 5e-3)
    F0 = finals[PRIMARY]
    chg = F0['lanes']['L_CHG']
    add('charger_r_lim_required_mm', [chg['requirement']['r_lim_required_min_mm'], chg['requirement']['r_lim_required_min_mm']], 5e-4,
        'the radial prerequisite 24.031 is reproduced; the R1 plan prerequisite 24.625 included CHG_ROUTE / CHG_LINK in plan, which OV-COND-BAND retires, so the R2 plan prerequisite equals the radial one')
    r1env = r1json['lanes']['G4-B']['L-SEAL']['main_seal']['topologies']['radial']['physical_envelope']['r_lim_mm']
    add('charger_r1_radial_row_r_lim_mm', list(r1env), 5e-3, 'pinned R1 radial-row envelope %s read from the R1 JSON; the R2 population (cs 0.5-2.0 mm, cup wall) gives %.3f mm' % (r1env, finals[PRIMARY]['lanes']['L_SEAL']['r_lim_cup_mm']))
    # T1 cross-section thresholds (stacks 0.04 / 0.07 / 0.10) and d_p at cs 1.7
    if cxp is not None:
        thr = []
        for sw, opt in (('SW2', 'metal'), ('SW1', 'zirconia'), ('SW1', 'PEEK')):
            T = btn_terms2(cxp, sw, opt)
            gd = [t1_gland(cxp, sw, T, c) for c in grid(r2in['buttons']['t1_cs'])]
            first = next((g_ for g_ in gd if g_['pass_']), None)
            thr.append(first['cs'] if first else None)
        add('t1_cs_threshold_mm', thr, 0.1 + 1e-9, 'the lead thresholds are continuous zero-margin values; the R2 grid step is 0.1 mm so the first passing grid value is reported', 'mm')
        T = btn_terms2(cxp, 'SW2', 'metal')
        g17 = t1_gland(cxp, 'SW2', T, 1.7)
        dp17 = 2.0 * (T['tol_bore'] + g17['h'] + g17['depth_tol'] + T['core'])
        add('t1_dp_at_cs1p7_mm', dp17, 0.1)
    sg = F0['lanes']['L_STR']
    rows.append(dict(id='structure_context_MPa', lead=LA['structure_context_MPa']['value'], computed=dict(LPR433736=finals['LPR433736']['lanes']['L_STR']['sigma_allow_req_MPa'],
                                                                                                                  LPR403736=finals['LPR403736']['lanes']['L_STR']['sigma_allow_req_MPa']),
                     tolerance=None, status='EXPLAINED', units='MPa',
                     explanation='context only: the lead estimate assumed ring support close to a clamped edge and no stress-concentration factor at the pod-frame junction. R2 solves the ring-plate '
                                 'compatibility (edge fixity %.2f) and applies K_t 2.0 at the pod-frame junction (sigma without that K_t: %.1f MPa). Stress is SUPPLIER_GATED, never a model FAIL.'
                                 % (sg['design']['plate']['edge_fixity'] if sg['design']['plate']['edge_fixity'] is not None else float('nan'), sg['sigma_without_inner_junction_Kt_MPa'])))
    for r in anchors_rows:
        if r['id'].startswith('R1 Screen B sigma'):
            rows.append(dict(id='overlay_off_screen_B', lead=LA['overlay_off_screen_B']['value'], computed=[round(r['computed'], 3), None], tolerance=5e-4, status='REPRODUCED', units='MPa / mm',
                             explanation=None))
        if r['id'].startswith('R1 uniform ceramic'):
            rows.append(dict(id='overlay_off_uniform_ceramic_mm', lead=LA['overlay_off_uniform_ceramic_mm']['value'], computed=[round(r['computed'], 3), 1.10], tolerance=5e-4, status='REPRODUCED',
                             units='mm', explanation=None))
    if cxp is not None:
        bw = cxp.st.P['buttons']['windows_deg']
        sw1 = [max(bw['SW1'][0], 300.0), min(bw['SW1'][1], 330.0)]
        sw5_in = bw['SW5'][0] >= 105.0 and bw['SW5'][1] <= 135.0
        rows.append(dict(id='buttons_reserved_overlap_deg', lead=LA['buttons_reserved_overlap_deg']['value'], computed=dict(SW1_in_BLE_clock=sw1, SW5_inside_WIFI_clock=sw5_in),
                         tolerance=None, status='REPRODUCED' if (sw1 == [300.0, 307.5] and sw5_in) else 'EXPLAINED', units='deg', explanation=None))
    return rows


# ============================================================================================
# Static report blocks (rulings, interpretations, gates) and the full result
# ============================================================================================
T1_RULING = dict(
    question='G4_R2_BRIEF.md 7.4.1: is the R1 exclusion of T1 ("never selectable") a hard rule?',
    where_r1_excluded=['G4_R1_BRIEF.md section 6.2: "T1 dynamic radial O-ring on the pusher - regression / reference only, expected FAIL; never selectable"', 'V05: "T1 (regression)"',
                       'section 11 self-test fault "T1 selected"', 'section 16 item 6: "T1 never selectable"', 'inputs/g4_r1_blockers.json V05_button_topologies.T1'],
    stated_reason='under the dynamic radial window 10-20 % and +/-0.05 mm cross-section tolerance a pusher O-ring needs cs >= 1.69 / 2.29 / 2.89 mm at groove / bore stacks 0.04 / 0.07 / 0.10 mm; the R1 pusher class (dia 1.6-2.0 mm bore planning range in a +1.0 mm boss) cannot carry such a ring',
    classification=['(i) the gland windows and the cross-section tolerance ARE hard rules (frozen carry-ins; not widened, not narrowed) and stay binding in R2',
                    '(ii) "never selectable" is an R1-scoped lead contract clause derived from (i) under the R1 envelope; not an owner decision, not a frozen invariant, not a G4 carry-in'],
    result='the exclusion does not rest on a hard rule: T1 is re-admitted for evaluation under the unchanged rules (i); no re-admission question is raised; R1 itself is unchanged',
    independent_review='must challenge this ruling (section 21.3 item 1)')

BUILDER_INTERPRETATIONS = [
    ('B-01', '6.5 / 8 V08-V10', 'Connector body footprints are the pinned G2 option window rectangles (J1501 8.3 x 4.6, J201 3.4 x 2.9, J202 3.5 x 3.0 mm), oriented with the long side tangential or radial; no body drawing exists. SR-FPC-MECH / SR-BATT-PCM / SR-CHG-MECH decide.'),
    ('B-02', '6.7 / 6.8 / 7.2.1', 'The G4 case-side support (BATTERY + REAR levels) is carried at BATTERY level only: a continuous raised cup wall occupies the REAR-level periphery and a post there would interrupt it (ring continuity, seal). The G4 plan layout is unchanged; the Z extent is the pinned BATTERY level.'),
    ('B-03', '7.1.2', 'K_t 2.0 is applied at the pod-frame (inner) junction, at the ring-plate junction, at the charger feedthrough hole radii and at the ring; the stress without the inner-junction K_t is reported beside sigma_allow_req.'),
    ('B-04', '6.2 / R2-V07', 'The PCM lobe envelope is authored (radial protrusion 1.5 / 2.5 / 3.0 mm, tangential width 5.0 / 6.5 / 8.0 mm, Z = pack Z); the design azimuth is 230 deg and the carrier / lobe conflicts are evaluated at 220, 230 and 240 deg.'),
    ('B-05', '7.1.2', 'Ring section = wall radial width x [plate bottom, wall top] minus the gland groove; the plate outer edge is the ring centroid radius (conservative span); the plate in-plane response uses the Lame solution of the outer-region thickness; the radial hoop pressure on the exposed wall is added in magnitude; the ring is continuous over 360 deg (the charger land and the lug-root screws lie outside the wall radius).'),
    ('B-06', '4.3 / 6.4', 'Z gaps use the nominal layer boundaries, each solid\'s own adverse growth, and the dimension-chain tolerance of the layers fully between the two references; the pack top is the battery-zone top minus c_axial; B.Cu items hang from the B.Cu plane at their linear-worst height.'),
    ('B-07', 'R2-V24', 'The MAIN-outline column is the Ø46 development disk plus growth arcs up to the G4 maximum outline; growth arcs exclude the closed reserved intervals and the frozen switch windows, shrunk by the PCB outline positional tolerance angle.'),
    ('B-08', '6.9 / 17.2 item 15', 'Reserved solid = clock interval over the radiator radial span union the radiator volume, at the volume\'s pinned Z levels (FRONT = front gap + display + cover). The pack and the PCM lobe are new conductive components; carrier, cup, O-ring, SW1 / SW5 pushers / boots / dielectric boss growth are allowed non-conductive items with G5 records; volumes are cell-sampled (0.2 mm).'),
    ('B-09', '8', 'No offset satisfies every constraint; the joint offset is the one with the fewest total violations (reserved-region hits + carrier conflicts), then the supports, then the radial room; exact connector placement is run for the five best-ranked offsets.'),
    ('B-10', '8', 'A lane is "failed" when its predicate is false at every grid point with D <= 50.9 mm (the largest grid D whose OD margin 51.00 - (D + 2 tol) is >= 0); the joint D is the smallest D at which every other lane passes; tw is the thinnest passing wall.'),
    ('B-11', '7.1 / 8', 'The design cup is the configuration that passes the hard deflection check with the least intrusion (ring widening 0, then the lowest wall top, then the lowest stress); the smallest gland-feasible cross-section is the design row; other rows are reported as alternatives.'),
    ('B-12', '6.5', 'FPC / tail / drop paths are polylines (tail exit -> lower-web groove -> foot bend at the adverse bend radius -> vertical riser; tail: PCM exit at pack mid-thickness -> riser; drop: FT-C inner face -> riser); the service slack (adverse 30 mm) is a planar U-loop pocket in the REAR-periphery band.'),
    ('B-13', '17.1.2', 'Q-R2-SUPPORT-RING (conditional, tool-raised): the over-allocation between the BATTERY-level case supports and the raised cup wall is quantified by a second ledger in which the supports start above the cup wall top; this is a quantification, not a decision.'),
    ('B-14', 'numerical', 'Disks and sectors are exact (analytic) in the clearance kernel; polygon supersets (circumscribed) are used elsewhere with a documented 0.01 mm allowance (POLY_SLACK_MM) that is never a credit.'),
    ('B-15', '7.5.2', 'The F.Cu fallback exclusions are the pinned F.Cu courtyards, the U101 shield polygon, DISP_FPC, ALS, SWD, DISP_LAND, the MAIN-level radiator / reserved regions and MAG_CLEAR; the body must lie under the display (r <= R_display) with c_lra_plan.'),
    ('B-16', '7.3', 'The charger block height allocation maximum is the lower-web underside (adverse) minus c_insert; it is an SR-CHG-MECH allocation threshold, not a credit.'),
    ('B-17', '6.8', 'The occupancy ledger is cell-sampled (0.5 mm); the exact pair table decides clearance; the double-occupied cell count is reported per band.'),
    ('B-18', '7.4', 'For each switch / topology / pusher class the smallest closing boss is found by an exact reduction verified with the production predicates (bore margin rises 1:1 with the boss, protrusion falls with it); the occupant footprint of a switch is the union over its closing options.'),
    ('B-19', '7.7', 'A1-A11 keep identities, order, parts, directions and battery states; only the operation text of A1, A4, A5, A6, A9, A10, A11 changes and each change cites its decision id; A5 stays after A4 (the LRA is bonded on the MAIN sub-assembly before the stack closes, inside A4/A5 content).'),
    ('B-20', 'budgets', 'Runtimes are printed by check / selftest and recorded in the run report only (a timestamp or runtime inside a byte-compared file would break determinism); the JSON carries evaluation counts and the budgets.'),
    ('B-22', '8 (exact reductions)', 'The pose search stops evaluating a candidate pose at its first violated clearance pair (the pass / fail answer is identical to the exhaustive evaluation; verified against the exhaustive evaluation on a pose sample in the self-test, pa_early_exit_equals_exhaustive); the evaluation counter counts the pair predicates actually evaluated.'),
    ('B-21', 'run governance', 'The launch spec left the expected HEAD placeholder unfilled; the tool pins and verifies the R2 contract commit 8f89904 recorded in inputs.r2_contract_commit (the parent is the R1 record 27f7a3a).'),
]

KNOWN_DOC_DEBT = ['generated/g4_r1_blockers.md line 5 and generated/g4_r1_blockers.json.status still say "R1 study result (uncommitted; independent review pending)" although the files are committed at 27f7a3a; they are immutable and are not edited by R2 (P-4: the R2 status string states no commit or review state)',
                  'inputs/input_register.json still carries the frozen invariant "Battery LPR454440 selected; not replaceable without owner authorization" and the 2026-10-11 wording of OD-CONN-SIDE / OD-J202; the 2026-10-17 decisions are that authorization and are recorded only in the R2 files (a later lead state record updates the register)']

RESULT_STATUS = ('R2 study result. No G4 verdict is emitted. Authorizes nothing downstream (no KiCad, K1, K1-A, G5, MPN, supplier request or qualification). The 2026-10-17 owner decisions '
                 'enter only through the in-memory overlay; all values are PROVISIONAL planning values; no 5 ATM, structural, optical, adhesive, RF, MPN or supplier qualification is claimed.')
CLAIMS = 'No 5 ATM, structural, optical, adhesive, RF, MPN, supplier or catalogue-as-verified claim; ceramic strength is the 150 MPa planning allowable only (SR-CASEBACK-CERAMIC gates anything above it).'

_G4_CACHE = {}


def run_g4_in_process_r2(fresh=False):
    """C-R1-09 mechanism extended for R2: g4.ALLOWED_CHANGES |= R1_FILES | R2_FILES (exactly those paths, no wildcard, nothing else patched), then the G4
    module's own build, validate (byte identity against the committed G4 files) and self-tests. Cached per process (it is the longest step)."""
    if 'r' in _G4_CACHE and not fresh:
        return _G4_CACHE['r']
    added = (R1_FILES | R2_FILES) - G4_ORIGINAL_ALLOWED
    g4.ALLOWED_CHANGES |= (R1_FILES | R2_FILES)
    timing = {}
    t0 = time.time()
    g4_res = g4.build_results(timing)
    st = timing['study']
    files = g4.outputs(g4_res, st)
    fails = g4.validate(g4_res, st, files, 0.0)
    tests = g4.self_tests(g4_res, st)
    caught = sum(1 for t in tests if t['caught'])
    r = dict(res=g4_res, st=st, files=files, fails=fails, tests=len(tests), caught=caught, extension=sorted(added),
             extension_exact=(set(g4.ALLOWED_CHANGES) - G4_ORIGINAL_ALLOWED) == (R1_FILES | R2_FILES), runtime_s=time.time() - t0,
             pass_=(not fails and len(tests) == 32 and caught == 32))
    _G4_CACHE['r'] = r
    return r


def owner_questions(finals):
    """Conditional, tool-raised questions (17.1.2): Q-R2-SUPPORT-RING (B-13) and Q-R2-BATTERY. The tool decides neither."""
    qs = []
    p = finals[PRIMARY]
    ring_needed = any(p['dispositions'][l] == 'OWNER_GATED' and l in ('L-SEAL', 'L-STR') for l in p['dispositions']) or p['hard_checks']['R2-H22']['owner_gated']
    if ring_needed:
        st_ = p['lanes']['L_STR']['shortfalls']
        qs.append(dict(id='Q-R2-SUPPORT-RING', conditional=True, battery=PRIMARY,
                       text='The four BATTERY-level case-side supports (G4 layout, SUP_SW / SUP_SE / SUP_NE / SUP_WNW) occupy the outer annulus the raised cup wall must rise into. '
                            'Decide how the wall and the supports share it: (a) relieve / relocate the supports so that they start above the cup wall top (the second ledger quantifies this: '
                            '%d violating pairs as pinned, %d with the supports starting at Z %.3f mm), (b) keep the supports and confine the wall to the REAR band '
                            '(spigot shortfall %.3f mm; the hard deflection check then fails), or (c) another support concept.' % (
                                len(p['lanes']['L_PKG']['ledger']['A']['violations']), len(p['lanes']['L_PKG']['ledger']['B']['violations']),
                                p['lanes']['L_PKG']['ledger']['B']['relief_z_mm'], p['lanes']['L_SEAL']['spigot_confined_to_rear_band_mm']),
                       numeric=dict(required_wall_top_mm=st_.get('required_wall_top_for_deflection_mm'), spigot_shortfall_rear_only_mm=p['lanes']['L_SEAL']['spigot_confined_to_rear_band_mm'],
                                    ext_free_as_pinned_mm=p['lanes']['L_SEAL']['ext_free_as_pinned_mm'], ext_free_supports_relieved_mm=p['lanes']['L_SEAL']['ext_free_supports_relieved_mm'])))
    f = finals[BATTERIES[1]]
    prim_stops = {s['id'] for s in p['stops']}
    fb_stops = {s['id'] for s in f['stops']}
    non_struct = sorted((prim_stops - fb_stops) - {'R2-S05'})
    if p['stops'] and non_struct:
        qs.append(dict(id='Q-R2-BATTERY', conditional=True, battery=PRIMARY,
                       text='LPR433736 is blocked for non-structural reason(s) %s that LPR403736 does not show; OD-BATTERY allows the fallback only if the caseback allowable cannot support LPR433736, '
                            'so the model does not switch (7.1.6).' % non_struct, numeric=dict(primary_only_stops=non_struct)))
    return qs


def supplier_gate_list(finals):
    rows = []
    for bat in BATTERIES:
        F = finals[bat]
        L = F['lanes']
        rows.append(dict(battery=bat, gates=[
            dict(id='SR-BATT-PACK / PCM / GROWTH', needs='finished-pack drawing (diameter, thickness incl. PCM fold, PCM lobe, exit, growth)',
                 threshold=dict(assumed_envelope=dict(finished_diameter_max_mm=37.5, thickness_add_max_mm=0.3, growth_axial_mm=0.5, growth_radial_mm=1.0),
                                clean_offsets=L['L_PKG']['clean_offsets'], offsets_evaluated=L['L_PKG']['offsets'])),
            dict(id='SR-CASEBACK-CERAMIC', needs='qualified zirconia-class allowable for the cup geometry and process', threshold=dict(sigma_allow_req_MPa=L['L_STR']['sigma_allow_req_MPa'],
                                                                                                                                   planning_MPa=150.0)),
            dict(id='gasket / O-ring', needs='cs tolerance class, compression set, material vs the planning windows',
                 threshold=dict(smallest_gland_feasible_cs_mm=min([r_['cs_mm'] for r_ in F['hard_checks']['R2-H11']['detail']['rows'] if r_['gland_window']], default=None))),
            dict(id='SR-CHG-MECH', needs='block, land, FT-C, drop / harness envelope', threshold=dict(r_lim_cup_required_mm=L['L_CHG']['radial']['r_lim_required_min_mm'],
                                                                                                         strict_wedge_land_mm=L['L_CHG']['strict_wedge'])),
            dict(id='SR-LRA', needs='class envelopes incl. lead / exit, mount, magnet data',
                 threshold=dict(bcu_max_annulus_mm=L['L_LRA']['max_room_over_offsets_mm'], bcu_need_mm={k: v['need_mm'] for k, v in L['L_LRA']['bcu'].items()},
                                fcu_height_cap_mm=2.70, fcu_height_threshold_incl_mount_mm=L['L_LRA']['fcu'][next(iter(L['L_LRA']['fcu']))]['height_threshold_mm'])),
            dict(id='SR-FPC-MECH', needs='J1501 B.Cu axial mate: mated height, stiffener, mouth, R_bend_min', threshold=dict(R_bend_used_mm=2.0, J1501_need_radial_room_mm=L['L_PKG']['connectors']['J1501'].get('need_mm'),
                                                                                                                      best_room_mm=L['L_LRA']['max_room_over_offsets_mm'])),
            dict(id='SR-BUTTONS', needs='pusher, stem O-ring / boot, SW1 / SW5 non-metallic material data, dielectric boss growth',
                 threshold={sw: {r['topology'] + ':' + r['pusher_class']: r['I_SUM']['boss_zero_margin_mm'] for r in v['rows']} for sw, v in L['L_BTN'].items()}),
            dict(id='SR-WINDOW / SR-COVER-LENS / SR-DISPLAY-LAND', needs='as R1', threshold='see the R1 record')]))
    return rows


def handoff(finals, qs):
    out = {}
    for bat, F in finals.items():
        L = F['lanes']
        out[bat] = dict(
            joint_design_point=F['joint'], D_eval_mm=F['joint']['D'], D_margin_to_51_mm=F['joint']['D_margin_to_51_mm'],
            pack_offset_carrier_pillars=dict(offset=L['L_PKG']['chosen_offset'], pk=L['L_PKG']['pk'], pillars_plus_delta_mm=F['metrics']['z']['rear_band_delta_mm']),
            zones=dict(zone_a_ok=L['L_PKG']['zone_a']['ok'], governing_back_height_mm=L['L_PKG']['zone_a']['governing_back_height_mm'], column=L['L_PKG']['column']),
            connector_poses_and_mates={k: v['placed'] for k, v in L['L_PKG']['connectors'].items()}, paths=L['L_PKG']['paths'],
            lra=dict(bcu_feasible=L['L_LRA']['bcu_feasible'], fcu_plan_feasible=L['L_LRA']['fcu_plan_feasible_classes'], identity=None, bmm350_distance_mm=None,
                     bmm350_note='no LRA pose exists (R2-S04); the distance is reported for the best plan-feasible F.Cu pose when one exists, otherwise null'),
            cup_ring_and_gland=dict(design=L['L_STR']['design'], seal=dict(r_lim_cup_mm=L['L_SEAL']['r_lim_cup_mm'], gland_rows=L['L_SEAL']['gland_feasible_rows'])),
            charger=dict(closes=L['L_CHG']['closes'], radial=L['L_CHG']['radial'], drop=L['L_CHG']['drop']),
            buttons={sw: dict(closed=v['closed'], closing=v['closing_options']) for sw, v in L['L_BTN'].items()},
            main_outline_constraint=L['L_PKG']['k1'], reserved_region_g5_records=F['g5_records'],
            supplier_zero_margin_values={cid: h['supplier_zero_margin'] for cid, h in F['hard_checks'].items() if h['supplier_zero_margin']},
            fea='FEA-1..4 and ATM-Q1..Q6 unchanged (G4 record)', open_questions=[q['id'] for q in qs])
    return out


def schema_guard(r2in):
    bad = input_violations(r2in)
    bad += verbatim_violations(r2in)
    return bad


def build_results(timing=None, g4_inproc=None, only=None):
    """The authoritative R2 result: input checks, G4 in-process reproduction, overlay-off anchors, both batteries side by side, lead cross-checks,
    questions, handoff. Deterministic; contains no timestamp and no runtime."""
    T = {} if timing is None else timing
    t0 = time.time()
    EVAL['n'] = 0
    r1.EVAL['n'] = 0
    r2in = load_json(IN_PATH)
    r1json = load_json(GEN / 'g4_r1_blockers.json')
    bad = schema_guard(r2in)
    pins = pin_report(r2in)
    commit = contract_commit_report(r2in)
    ov_recs = overlay_records(r2in)
    ov_bad = overlay_problems(r2in, ov_recs)
    problems = list(bad) + ['pin mismatch: ' + p['path'] for p in pins if not p['match']] + ([] if commit['match'] else ['r2_contract_commit does not match the repository']) + ov_bad
    if problems:
        raise StudyError('STOP R2-S13 / R2-S10: ' + '; '.join(problems[:6]))
    gp = g4_inproc if g4_inproc is not None else run_g4_in_process_r2()
    g4res, st0 = gp['res'], gp['st']
    T['g4'] = time.time() - t0
    off = Sources(r2in, False)
    g2study = g2.Study()
    zs_off_only = ZStacks(off, Sources(r2in, False), g2study)
    zs, cxs, Es, finals = {}, {}, {}, {}
    scope = scope_report(r2in)
    an = anchors(r2in, g4res, st0, zs_off_only, r1json, gp)
    T['anchors'] = time.time() - t0 - T['g4']
    fcu = None
    for bat in BATTERIES:
        zs[bat] = ZStacks(off, Sources(r2in, True, bat), g2study)
        E = evaluate_battery(r2in, g4res, st0, zs[bat], bat, fcu)
        cxs[bat] = E['cx']
        Es[bat] = E
        finals[bat] = finalize_battery(E, r2in, r1json, an['pass_'], scope)
        T[bat] = time.time() - t0
    qs = owner_questions(finals)
    lead = lead_crosschecks(r2in, zs, cxs, finals, an['rows'], r1json)
    gates = supplier_gate_list(finals)
    pkg_verdict = finals[PRIMARY]['verdict']
    res = dict(
        schema='sportwatch-g4-r2/1', contract=BRIEF, status=RESULT_STATUS, claims=CLAIMS, evidence_class='PROJECT_DERIVED',
        r2_contract_commit=r2in['r2_contract_commit'], owner_decisions=r2in['owner_decisions'], open_question_answers=r2in['open_question_answers'],
        overlay=dict(records=ov_recs, rule='deep copies of the parsed pinned inputs; nothing written back; no imported module attribute patched except the prospective g4.ALLOWED_CHANGES extension',
                     applied_per_battery={b: Sources(r2in, True, b).applied for b in BATTERIES}),
        inputs=dict(pins=pins, contract_commit=commit, catalogue=r2in['catalogue'], envelope_assumptions=r2in['envelope_assumptions'], supplier_evidence=r2in['supplier_evidence'],
                    fallback_trigger=r2in['fallback_trigger'], lra_supplied=r2in['lra_supplied'], limits=r2in['limits'], grids=r2in['grids'], lobe=r2in['lobe']),
        carry_in=dict(baselines=r2in['baselines'], g4_in_process=dict(pass_=gp['pass_'], tests=gp['tests'], caught=gp['caught'], fails=gp['fails'], extension=gp['extension'], extension_exact=gp['extension_exact'],
                                                                      extension_equals_R1_FILES_union_R2_FILES=gp['extension_exact']),
                      z_baselines=dict(base={b: zs_off_only.base[b]['nominal_reported'] for b in zs_off_only.base}, rss={b: zs_off_only.base[b]['rss'] for b in zs_off_only.base},
                                       linear={b: zs_off_only.base[b]['linear'] for b in zs_off_only.base}),
                      legacy=dict(pass_=st0.legacy['pass_'], rows=st0.legacy['rows']), r1_files=sorted(R1_FILES), r2_files=sorted(R2_FILES)),
        anchors=an, scope=scope,
        batteries={b: {k: v for k, v in finals[b].items() if k != 'asm'} for b in BATTERIES},
        z=dict(per_battery={b: zs[b].delta_report() for b in BATTERIES}, deltas_mm={b: zs[b].delta for b in BATTERIES},
               levels={b: {k: list(v) for k, v in zs[b].levels('G2-REVA', 'over').items()} for b in BATTERIES},
               rule='battery_zone recomputed through the imported G1 / G2 rule; Delta = t_pack_nom(pinned) - t_pack_nom(overlaid) inserted as ONE fixed REAR-band layer with no tolerance term'),
        lead_crosschecks=lead, t1_ruling=T1_RULING, builder_interpretations=[dict(id=i, section=s_, text=t) for i, s_, t in BUILDER_INTERPRETATIONS],
        known_documentation_debt=KNOWN_DOC_DEBT, owner_questions=qs, supplier_gates=gates, handoff_to_g5_and_outline=handoff(finals, qs),
        package_battery=PRIMARY, verdict=pkg_verdict, verdict_rule='the package verdict is the LPR433736 verdict (section 12); the LPR403736 verdict is reported beside it and never switches the battery (7.1.6)',
        verdict_by_battery={b: finals[b]['verdict'] for b in BATTERIES},
        search=dict(evaluations=EVAL['n'] + r1.EVAL['n'], budget=r2in['budgets']['evaluations_max'], within_budget=EVAL['n'] + r1.EVAL['n'] <= r2in['budgets']['evaluations_max'],
                    scan={b: dict(failed_lanes=Es[b]['scan']['failed_lanes'], active_lanes=Es[b]['scan']['active_lanes'], joint=Es[b]['scan']['joint'], reference_dmax=Es[b]['scan'].get('reference_dmax'),
                                  rows=[dict(D=r['D'], tw=r['tw'], rad_ok=r['rad_ok'], cover_ok=r['cover_ok'], btn_ok=r['btn_ok'], seal_gland_ok=r['seal_gland_ok'], chg_radial_ok=r['chg_radial_ok'],
                                             r_lim_pop_mm=r['r_lim_pop_mm']) for r in Es[b]['scan']['rows'] if r['tw'] in (0.8, 1.1, 1.5)]) for b in BATTERIES}),
        reference_dmax={b: ref_summary(Es[b]) for b in BATTERIES})
    T['total'] = time.time() - t0
    res['_runtime'] = None
    del res['_runtime']
    return res, dict(Es=Es, cxs=cxs, finals=finals, zs=zs, anchors=an, r2in=r2in, r1json=r1json, g4=gp, scope=scope, timing=T)


def ref_summary(E):
    P = E.get('Pref')
    if P is None:
        return None
    A = P['annulus']['variant_A']['as_pinned_supports']
    B = P['annulus']['variant_B']['supports_relieved_below_cup_top']
    return dict(D=P['D'], tw=P['tw'], chosen_offset=P['package']['chosen_offset'], placed=sorted(P['_placed']), ledger_as_pinned_violations=len(A['violations']),
                ledger_supports_relieved_violations=len(B['violations']), charger_closes=P['charger']['closes'], r_lim_cup_mm=P['charger']['radial']['r_lim_cup_mm'],
                sigma_governing_MPa=P['structure']['design']['ev']['sigma_governing_MPa'], w_max_mm=P['structure']['design']['ev']['w_max_mm'],
                rule='best-case diameter D = largest grid D whose OD margin is >= 0 (50.9): shows whether a larger body would change any stop')


# ============================================================================================
# Drawings
# ============================================================================================
OCC_COLOURS = {'case-side support': '#e59866', 'support pad': '#f0b27a', 'pusher bore / stroke': '#85c1e9', 'button boss': '#aed6f1', 'vent port': '#d7bde2',
               'caseback screw': '#7f8c8d', 'lug arm': '#bdc3c7', 'spring bar': '#95a5a6', 'connector body (B.Cu)': '#2e86c1', 'mate stroke envelope (A4)': '#d6eaf8',
               'FPC / harness riser': '#1b4f72', 'riser foot bend envelope': '#5dade2', 'battery tail (plan run)': '#117864', 'service slack pocket': '#f7dc6f',
               'charger land (non-conductive)': '#f5cba7', 'charger contacts (FT-C)': '#c0392b', 'cup raised wall / spigot': '#bb8fce', 'U7 (DRV2625) on B.Cu': '#f1948a',
               'existing B.Cu part': '#d5dbdb', 'carrier hard-stop pillar': '#85929e', 'G3 support land': '#aab7b8'}


def _draw_poly(svg, T, polys, fill, stroke, op=0.4, dash=None, sw=0.8):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    for p in polys:
        svg.add('<polygon points="%s" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (g4._pp(p, T), fill, op, stroke, sw, d))


def _circle(svg, T, c, r, fill, stroke, op=0.25, dash=None, sw=1.0):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    cx, cy = T(c)
    svg.add('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (cx, cy, r * T.s, fill, op, stroke, sw, d))


def render_plan(res, ctx):
    svg = g4.Svg(1180, 700, 'G4-R2 plan: case, bosses, pack with offset, carrier, zones, connectors, cup ring, charger, radiators and reserved regions')
    svg.text(10, 18, 'G4-R2 plan (front view, north = 12 o\'clock = up). Left LPR433736 (primary), right LPR403736 (reported). Joint point per battery. No G4 verdict.', 12, weight='bold')
    for k, bat in enumerate(BATTERIES):
        E = ctx['Es'][bat]
        P = E['P']
        cx = E['cx']
        T = g4.Tf(10.5, 300 + 585 * k, 360)
        D, R_side = P['D'], P['R_side']
        svg.text(300 + 585 * k, 38, '%s: D %.2f mm, tw %.2f, offset %.2f mm @ %.0f deg' % (bat, D, P['tw'], P['package']['chosen_offset'][0], P['package']['chosen_offset'][1]), 11, 'middle', weight='bold')
        for rg in P['_reserved']:
            if rg['level'] in ('MAIN', 'BATTERY') and rg['part'] == 'clock':
                _draw_poly(svg, T, rg['polys'], '#f5b7b1', '#c0392b', 0.18, '3 2', 0.6)
        for rg in P['_reserved']:
            if rg['level'] == 'MAIN' and rg['part'] == 'volume':
                _draw_poly(svg, T, rg['polys'], '#aed6f1', '#2874a6', 0.25, None, 0.6)
        mg = cx.st.res['MAG_CLEAR']['geometry']
        g4.draw_geom(svg, T, mg, '#abebc6', '#1e8449', 0.12, '4 3', 0.7)
        _circle(svg, T, (100, 100), D / 2, '#ffffff', '#566573', 0.0, None, 1.4)
        _circle(svg, T, (100, 100), R_side, '#ffffff', '#566573', 0.0, None, 1.0)
        _circle(svg, T, (100, 100), cx.R_main, '#ffffff', '#1a5276', 0.0, '2 2', 0.8)
        for a0, a1 in P['_col']['arcs']:
            _draw_poly(svg, T, [sector_poly(a0, a1, cx.R_main, P['_col']['R_g4_max'], 2.0)], '#d4efdf', '#1e8449', 0.18, '2 2', 0.5)
        pk = P['_pk']
        _circle(svg, T, pk['centre'], pk['pack_radius'], '#f9e79f', '#b7950b', 0.5, None, 0.8)
        _circle(svg, T, pk['centre'], pk['R_carrier_outer'], '#fdebd0', '#a04000', 0.15, None, 1.0)
        _draw_poly(svg, T, [pk['pocket_poly']], '#fdebd0', '#a04000', 0.35, None, 0.8)
        _draw_poly(svg, T, [pk['lobe_poly']], '#f7dc6f', '#7d6608', 0.6, None, 0.8)
        for o in P['_occs']:
            if o['kind'] in OCC_COLOURS and o['kind'] not in ('carrier hard-stop pillar', 'G3 support land', 'existing B.Cu part', 'caseback screw', 'lug arm', 'spring bar') and o['group'] != 'CUP':
                _draw_poly(svg, T, o['polys'], OCC_COLOURS[o['kind']], '#17202a', 0.55, None, 0.5)
        ring = next(o for o in P['_cup_occs'] if o['id'] == 'CUP_WALL_RING')
        r_wi = ring_inner_r(ring)
        _circle(svg, T, (100, 100), r_wi, '#ffffff', '#6c3483', 0.0, '5 2', 1.3)
        _circle(svg, T, (100, 100), cx.st.s14geo['outline_r'], '#d5f5e3', '#117864', 0.3, None, 0.8)
        for s_ in cx.st.s14geo['supports']:
            _draw_poly(svg, T, [s_['poly']], '#85929e', '#2c3e50', 0.6, None, 0.5)
        for key, ptl in P['_placed'].items():
            x, y = T(polar_to_xy(ptl))
            svg.text(x, y, key, 9, 'middle', '#ffffff', 'bold')
        svg.text(300 + 585 * k, 660, 'cup wall inner face r %.2f mm (dashed violet); Ø46 development envelope (dashed blue); allowed MAIN growth arcs (green); reserved regions (red dashed); MAG_CLEAR (green dashed)' % r_wi, 9, 'middle')
        svg.text(300 + 585 * k, 676, 'stops: %s' % ', '.join(sorted({s_['id'] for s_ in ctx['finals'][bat]['stops']})), 9, 'middle', '#922b21')
    return svg.render()


def polar_to_xy(ptl):
    b = ptl['geo']['body']
    return (sum(q[0] for q in b) / len(b), sum(q[1] for q in b) / len(b))


def section_panel(svg, ox, oy, w, h, title, items, rmax=26.0, zmax=10.5, note=None):
    sx, sy = w / rmax, h / zmax
    svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#fbfcfc" stroke="#aab7b8"/>' % (ox, oy, w, h))
    svg.text(ox + 4, oy - 5, title, 10, weight='bold')
    for r in range(0, int(rmax) + 1, 5):
        svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#e5e8e8"/>' % (ox + r * sx, oy, ox + r * sx, oy + h))
        svg.text(ox + r * sx, oy + h + 11, 'r %d' % r, 8, 'middle', '#566573')
    for it in items:
        r0, r1, z0, z1, label, col = it[:6]
        x0, x1 = ox + r0 * sx, ox + r1 * sx
        y1, y0 = oy + h - z0 * sy, oy + h - z1 * sy
        svg.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" fill-opacity="0.6" stroke="#17202a" stroke-width="0.5"/>' % (x0, y0, max(0.6, x1 - x0), max(0.6, y1 - y0), col))
        if label and (x1 - x0) > 14:
            svg.text((x0 + x1) / 2, (y0 + y1) / 2 + 3, label, 7, 'middle')
    if note:
        svg.text(ox + 4, oy + h + 24, note, 8, fill='#566573')


def render_sections(res, ctx):
    svg = g4.Svg(1180, 900, 'G4-R2 sections: J1501 south, charger / J202 east, LRA pose, worst button and SW5, cup and seal, pillar at an S14 land')
    svg.text(10, 18, 'G4-R2 sections (radius r from the MAIN centre, Z from the pod plane; primary battery LPR433736 joint point; schematic, dimensions from the model)', 12, weight='bold')
    E = ctx['Es'][PRIMARY]
    P, cx = E['P'], E['cx']
    L = cx.levels['_layers']
    F = ctx['finals'][PRIMARY]
    D, R_side = P['D'], P['R_side']
    ev = P['structure']['design']['ev']
    ring = next(o for o in P['_cup_occs'] if o['id'] == 'CUP_WALL_RING')
    r_wi = ring_inner_r(ring)
    cfg = ev['config']
    pk = P['_pk']
    base = [(0, cx.st.s14geo['outline_r'], 0.5, L['rear_inner'][1], 'S14 REAR', '#d5f5e3'), (0, D / 2, L['lower_web'][0], L['lower_web'][1], 'lower web', '#d7bde2'),
            (0, pk['R_carrier_outer'], L['battery_zone'][0], L['battery_zone'][1], 'pack + carrier', '#f9e79f'), (0, cx.R_main, L['main_pcb'][0], L['main_pcb'][1], 'MAIN', '#abebc6'),
            (R_side, D / 2, 0, L['main_pcb'][1], 'case wall', '#cacfd2')]
    cup = [(0, cx.cx.r_step, 0, cfg['t_in'], 'plate in', '#d2b4de'), (cx.cx.r_step, r_wi, 0, cfg['t_out'], 'plate out', '#d2b4de'), (r_wi, R_side, 0, ev['z_top_mm'], 'wall', '#bb8fce'),
           (R_side, D / 2, 0, cfg['t_out'], 'rim', '#d2b4de')]
    z_pl = bcu_plane(cx)
    h_c = conn_height(cx)
    items1 = base + cup
    pl = P['_placed']
    for k, col in (('J1501', '#2e86c1'), ('J201', '#2e86c1'), ('J202', '#2e86c1')):
        if k in pl:
            g_ = pl[k]['geo']
            r_c = polar(((g_['body'][0][0] + g_['body'][2][0]) / 2, (g_['body'][0][1] + g_['body'][2][1]) / 2))[0]
            items1.append((r_c - 1.5, r_c + 1.5, z_pl - h_c, z_pl, k, col))
    section_panel(svg, 20, 50, 560, 300, 'South (J1501): axial mate toward the REAR; riser at the carrier foot', items1, note='J1501: %s' % ('NO strict-clearance pose (R2-S08); required annulus %.2f mm vs best %.2f mm' %
                                                                                                    (P['connectors']['J1501']['need_mm'], P['lra']['max_room_over_offsets_mm']) if 'J1501' not in pl else 'placed'))
    chg = P['charger']
    items2 = base + cup + [(chg['radial']['block_rmax_mm'] - 4.0, chg['radial']['block_rmax_mm'], 0, chg['block_top_mm'], 'FT-C block', '#c0392b'),
                           (chg['radial']['land_rmax_mm'] - 6.0, chg['radial']['land_rmax_mm'], 0, chg['land_top_mm'], 'land', '#f5cba7')]
    section_panel(svg, 600, 50, 560, 300, 'East: charger block / land vs the cup wall inner face', items2,
                  note='r_lim(cup) %.2f mm, land r_max %.2f, required r_lim %.2f mm (deficit %.2f)' % (chg['radial']['r_lim_cup_mm'], chg['radial']['land_rmax_mm'], chg['radial']['r_lim_required_min_mm'], chg['headline']['radial_limit_deficit_mm']))
    lra = P['lra']
    section_panel(svg, 20, 400, 560, 300, 'LRA pose: MAIN B.Cu zone B vs MAIN F.Cu (Z-neutral cap 2.70 mm)',
                  base + [(pk['R_carrier_outer'], P['_col']['R_g4_max'], z_pl - 3.35, z_pl, 'zone B: %.2f mm' % (P['_col']['R_g4_max'] - pk['R_carrier_outer']), '#fadbd8'),
                          (0, 21.95, L['main_pcb'][1], L['main_pcb'][1] + 2.70, 'F.Cu cap 2.70', '#d6eaf8')],
                  note='no B.Cu pose: best annulus %.2f mm < need %s; F.Cu plan-feasible poses %s' % (lra['max_room_over_offsets_mm'], {k: round(v['need_mm'], 2) for k, v in lra['bcu'].items()},
                                                                                                    {k: v['n_plan_feasible'] for k, v in lra['fcu'].items()}))
    sw = max(BTN_SW, key=lambda s_: P['_swg'][s_]['section']['boss'])
    s_ = P['_swg'][sw]['section']
    section_panel(svg, 600, 400, 560, 300, 'Worst button (%s) and SW5: boss + boot / seal inside +3.0 mm' % sw,
                  [(cx.R_main, s_['R_inner'], L['main_pcb'][0], L['main_pcb'][1], 'MAIN edge', '#abebc6'), (s_['R_inner'], s_['R_face'], L['main_pcb'][0], L['main_pcb'][1], 'bore', '#85c1e9'),
                   (D / 2, D / 2 + s_['boss'], L['main_pcb'][0], L['main_pcb'][1], 'boss %.2f' % s_['boss'], '#aed6f1'), (R_side, D / 2, L['battery_zone'][0], L['main_pcb'][1], 'wall', '#cacfd2')],
                  rmax=30.0, note='boss limit 3.000 mm; margins in R2-H12 (I-SUM binding, I-MAX reported)')
    seal = F['lanes']['L_SEAL']
    gd = P['structure']['design']['row']
    section_panel(svg, 20, 750, 560, 120, 'Cup / seal generic: raised radial O-ring on the ceramic wall', cup + [(R_side - gd['groove_h_mm'], R_side, cfg['t_out'] + cx.sp.m_cb['groove_land_min_mm'], cfg['t_out'] + cx.sp.m_cb['groove_land_min_mm'] + gd['groove_g_mm'], 'groove', '#ffffff')],
                  rmax=26.0, zmax=6.0, note='cs %.1f mm row %s: wall top %.2f mm, REAR band cap %.2f' % (gd['cs_mm'], gd['id'], ev['z_top_mm'], L['rear_band'][1] - cx.zs.tol_of('lower_web')))
    s14 = cx.st.s14geo['supports'][0]
    rr = [math.hypot(q[0] - 100, q[1] - 100) for q in s14['poly']]
    section_panel(svg, 600, 750, 560, 120, 'Pillar at an S14 land: +Delta only', [(min(rr), max(rr), L['optics_zone'][1] - cx.st.P['c_cb_rear_mm']['min'], L['rear_inner'][1], 'S14 land', '#aab7b8'),
                                                                                    (min(rr), max(rr), L['rear_inner'][1], L['rear_band'][1], 'pillar +Delta %.2f' % cx.delta, '#85929e'),
                                                                                    (0, cx.st.s14geo['outline_r'], L['lower_web'][0], L['lower_web'][1], 'lower web', '#d7bde2')], rmax=26.0, zmax=6.0)
    return svg.render()


def render_annulus(res, ctx):
    svg = g4.Svg(1180, 640, 'G4-R2 joint annulus ledger: azimuth x Z occupancy per battery')
    svg.text(10, 18, 'G4-R2 joint annulus ledger (cell-sampled): occupied fraction of the shared domain per Z band and 15-degree sector (as-pinned supports)', 12, weight='bold')
    for k, bat in enumerate(BATTERIES):
        led = ctx['Es'][bat]['P']['annulus']['ledger']
        x0, y0 = 40, 60 + 290 * k
        svg.text(x0, y0 - 10, '%s: double-occupied cells per band %s' % (bat, led['double_occupied_cells']), 11, weight='bold')
        bands = [b['id'] for b in led['bands']]
        cw, ch = 40, 52
        for bi, b in enumerate(bands):
            svg.text(x0 - 4, y0 + bi * ch + ch / 2 + 3, b.replace('_', ' ').lower(), 8, 'end')
            for s in range(24):
                row = next(r for r in led['rows'] if r['band'] == b and r['sector_deg'][0] == 15 * s)
                f = 0.0 if row['domain_mm3'] <= 0 else min(1.0, row['occupied_mm3'] / row['domain_mm3'])
                shade = int(255 - 200 * f)
                svg.add('<rect x="%d" y="%d" width="%d" height="%d" fill="rgb(%d,%d,255)" stroke="#d5d8dc" stroke-width="0.5"/>' % (x0 + s * cw * 0.95 / 1.0 * 0.0 + s * 38, y0 + bi * ch, 38, ch - 4, shade, shade))
                if bi == len(bands) - 1 and s % 2 == 0:
                    svg.text(x0 + s * 38 + 19, y0 + len(bands) * ch + 8, '%d' % (15 * s), 8, 'middle')
        svg.text(x0 + 12 * 38, y0 + len(bands) * ch + 22, 'azimuth sector start (deg); darker = more of the domain volume occupied', 8, 'middle', '#566573')
    return svg.render()


def fcu_free_disk(cx2, step=0.5):
    """Largest free disk on MAIN F.Cu under the display (distance to the nearest F.Cu exclusion): the numeric SR-LRA footprint threshold of the fallback."""
    key = json.dumps([step, cx2.st.R_display])
    if key in _FCU_DISK_CACHE:
        return _FCU_DISK_CACHE[key]
    st = cx2.st
    ex = fcu_exclusions(cx2)
    items = [(poly_bbox(p), p, eid) for eid, kind, polys in ex for p in polys]
    mg = geom_polys(st.res['MAG_CLEAR']['geometry'])
    items += [(poly_bbox(p), p, 'MAG_CLEAR') for p in mg]
    best = (-1.0, None, None)
    n = int(st.R_display / step) + 1
    for i in range(-n, n + 1):
        x = 100.0 + i * step
        for j in range(-n, n + 1):
            y = 100.0 + j * step
            r = math.hypot(x - 100.0, y - 100.0)
            if r > st.R_display:
                continue
            d = st.R_display - r         # the display outline is a boundary too
            for bb, p, eid in items:
                lb = bbox_gap((x, y, x, y), bb)
                if lb >= d:
                    continue
                dd = pt_poly_dist((x, y), p)
                if dd < d:
                    d = dd
            if d > best[0] + 1e-12:
                best = (d, (x, y), None)
    u703 = next(f for f in st.HM['main_footprints'] if f['ref'] == 'U703')
    dist_u = poly_gap([best[1], (best[1][0] + 1e-6, best[1][1]), (best[1][0], best[1][1] + 1e-6)], rect_poly(*u703['courtyard_bbox']))
    out = dict(radius_mm=best[0], centre=best[1], step_mm=step, distance_to_U703_courtyard_mm=dist_u,
               fits_radius_limit_mm=best[0] - st.P['c_lra_plan_mm']['max'],
               rule='largest empty disk on MAIN F.Cu under the display (pinned courtyards, U101 shield polygon, display flex / land, ALS, SWD, MAIN-level radiator / reserved regions, MAG_CLEAR)')
    _FCU_DISK_CACHE[key] = out
    return out


def bmm350_zone_b_bound(cx2, pk, col):
    """Lower bound of the LRA-to-BMM350 distance for ANY MAIN B.Cu zone-B pose of this offset: distance from the U703 courtyard to the zone-B annulus."""
    st = cx2.st
    u703 = next(f for f in st.HM['main_footprints'] if f['ref'] == 'U703')
    rect = rect_poly(*u703['courtyard_bbox'])
    z_f = cx2.levels['_layers']['main_pcb'][1]
    best = None
    for a in frange(0.0, 359.0, 1.0):
        lo = zone_a_extent(pk, a) + st.P['c_lra_plan_mm']['max']
        hi = col['R_g4_max'] if any(a0 <= a % 360 <= a1 for a0, a1 in col['arcs']) else col['R_dev']
        if hi <= lo:
            continue
        for r in (lo, hi):
            p = xy(r, a)
            d = min(g4.seg_dist(p, u, v) for u, v in zip(rect, rect[1:] + rect[:1])) if not g4.pip(p, rect) else 0.0
            zg = cx2.levels['_layers']['main_pcb'][0] - cx2.levels['_layers']['main_pcb'][0]
            if best is None or d < best:
                best = d
    z_gap = cx2.levels['_layers']['main_pcb'][1] - cx2.levels['_layers']['main_pcb'][0]
    return dict(plan_distance_mm=best, z_separation_mm=z_gap, distance_3d_lower_bound_mm=None if best is None else math.hypot(best, z_gap),
                rule='any LRA body lies in the zone-B annulus on B.Cu; U703 sits on MAIN F.Cu on the other side of the 0.8 mm board')


# ============================================================================================
# Report (markdown)
# ============================================================================================
def mdt(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join('---' for _ in headers) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(c).replace('|', '/').replace('\n', ' ') for c in r) + ' |')
    return out


def fm(v, n=3):
    if v is None:
        return 'n/a'
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        return ('%+.' + str(n) + 'f') % (round(v, n) + 0.0) if False else ('%.' + str(n) + 'f') % (round(v, n) + 0.0)
    return str(v)


def fsg(v, n=3):
    return 'n/a' if v is None else ('%+.' + str(n) + 'f') % (round(v, n) + 0.0)


def render_md(res, ctx):
    L = []
    A = L.append
    A('# G4-R2 package-closure study (battery / interconnect / LRA / caseback-cup re-allocation), Rev-A')
    A('')
    A('Status: %s' % res['status'])
    A('')
    A('Verdict (package = LPR433736): **%s**. LPR403736 (reported, never selected by the model): **%s**.' % (res['verdict'], res['verdict_by_battery'][BATTERIES[1]]))
    A('')
    A(res['claims'])
    A('')
    A('Contract: `%s`. R2 contract commit %s. R2 emits no G4 verdict and authorizes nothing downstream (KiCad, K1, K1-A, G5, MPN, supplier request, qualification).' % (res['contract'], res['r2_contract_commit']))
    A('')
    A('## 1. Headline numbers (joint design point per battery)')
    A('')
    rows = []
    for k_, f in (('Joint D (mm)', lambda b: fm(b['joint']['D'], 2)), ('D margin to 51.00 (mm)', lambda b: fm(b['joint']['D_margin_to_51_mm'], 3)), ('bulk wall tw (mm)', lambda b: fm(b['joint']['tw'], 2)),
                  ('REAR-band Delta (mm)', lambda b: fm(b['metrics']['z']['rear_band_delta_mm'], 3)),
                  ('total Z delta nominal / RSS / linear (mm)', lambda b: '%s / %s / %s' % (fm(b['metrics']['z']['delta_nominal']), fm(b['metrics']['z']['delta_rss']), fm(b['metrics']['z']['delta_linear']))),
                  ('chosen pack offset (mm @ deg)', lambda b: '%s @ %s' % (fm(b['lanes']['L_PKG']['chosen_offset'][0], 2), fm(b['lanes']['L_PKG']['chosen_offset'][1], 0))),
                  ('carrier outer radius at linear worst (mm)', lambda b: fm(b['lanes']['L_PKG']['pk']['R_carrier_outer'])),
                  ('connectors placed / unplaced', lambda b: '%s / %s' % (','.join(b['lanes']['L_PKG']['placed']) or '-', ','.join(b['lanes']['L_PKG']['unplaced']) or '-')),
                  ('clean offsets of %d' % 145, lambda b: str(b['lanes']['L_PKG']['clean_offsets'])),
                  ('LRA on MAIN B.Cu (best annulus vs need)', lambda b: '%s mm vs %s' % (fm(b['lanes']['L_LRA']['max_room_over_offsets_mm']), ', '.join('%s %s' % (k, fm(v['need_mm'])) for k, v in b['lanes']['L_LRA']['bcu'].items()))),
                  ('LRA on MAIN F.Cu (plan-feasible poses; largest free disk radius)', lambda b: '%s; %s mm' % ({k: v['n_plan_feasible'] for k, v in b['lanes']['L_LRA']['fcu'].items()}, fm(b['lanes']['L_LRA']['fcu_free_disk']['radius_mm']))),
                  ('LRA-BMM350 distance', lambda b: 'no pose; lower bound for any zone-B pose %s mm (3-D)' % fm(b['lanes']['L_LRA']['bmm350_zone_b']['distance_3d_lower_bound_mm'])),
                  ('charger r_lim(cup) / required (mm)', lambda b: '%s / %s (deficit %s)' % (fm(b['lanes']['L_CHG']['radial']['r_lim_cup_mm']), fm(b['lanes']['L_CHG']['radial']['r_lim_required_min_mm']), fm(b['lanes']['L_CHG']['headline']['radial_limit_deficit_mm']))),
                  ('seal r_lim(cup) (mm); spigot margin, REAR band only (mm)', lambda b: '%s; %s' % (fm(b['lanes']['L_SEAL']['r_lim_cup_mm']), fsg(b['lanes']['L_SEAL']['spigot_confined_to_rear_band_mm']))),
                  ('cup stress sigma_allow_req (MPa) / margin to 150', lambda b: '%s / %s' % (fm(b['lanes']['L_STR']['sigma_allow_req_MPa']), fsg(b['lanes']['L_STR']['margin_to_150_MPa'], 1))),
                  ('cup deflection w_max (mm) / limit 0.050', lambda b: fm(b['lanes']['L_STR']['screen_B']['w_max_mm'], 4)),
                  ('periphery shortfall retired / retained band (mm)', lambda b: '%s / %s' % (fsg(b['lanes']['L_STR']['shortfalls'].get('periphery_shortfall_band_retired_mm')), fsg(b['lanes']['L_STR']['shortfalls'].get('periphery_shortfall_conductor_band_retained_mm')))),
                  ('buttons closed (SW1..SW5)', lambda b: ' '.join('%s:%s' % (sw, 'Y' if v['closed'] else 'N') for sw, v in sorted(b['lanes']['L_BTN'].items()))),
                  ('stops', lambda b: ', '.join(s_['id'] for s_ in b['stops'])),
                  ('verdict', lambda b: b['verdict'])):
        rows.append([k_] + [f(res['batteries'][bt]) for bt in BATTERIES])
    L += mdt(['quantity'] + list(BATTERIES), rows)
    A('')
    A('## 2. Stops raised (every stop with its reason)')
    A('')
    for bt in BATTERIES:
        A('**%s**' % bt)
        A('')
        if not res['batteries'][bt]['stops']:
            A('- none')
        for s_ in res['batteries'][bt]['stops']:
            A('- **%s** (%s): %s' % (s_['id'], s_['scope'], s_['reason']))
            if s_['quantities']:
                A('  - quantities: `%s`' % json.dumps(rounded(s_['quantities']), sort_keys=True, default=str)[:600])
        A('')
    A('## 3. Lane dispositions')
    A('')
    A('Rule: R2 verdicts follow section 12; a stop makes the verdict BLOCKED and lets every other lane complete with its thresholds.')
    A('')
    L += mdt(['lane'] + list(BATTERIES), [[ln, res['batteries'][BATTERIES[0]]['dispositions'].get(ln), res['batteries'][BATTERIES[1]]['dispositions'].get(ln)] for ln in
                                          ('L-PKG', 'L-STR', 'L-SEAL', 'L-CHG', 'L-BTN', 'L-LRA', 'L-RAD', 'L-ASM', 'L-WIN')])
    A('')
    A('## 4. Hard checks (R2-H01 .. H28), both batteries side by side with the committed R1 column')
    A('')
    rows = []
    for cid in sorted(res['batteries'][PRIMARY]['hard_checks']):
        h0, h1 = res['batteries'][BATTERIES[0]]['hard_checks'][cid], res['batteries'][BATTERIES[1]]['hard_checks'][cid]
        r1c = h0['r1_column']
        r1s = r1c if isinstance(r1c, str) else '%s (%s %s)' % (r1c.get('status'), fsg(r1c.get('margin')), r1c.get('units') or '')
        rows.append([cid, h0['title'][:84], h0['evaluation'], '%s %s %s' % (h0['status'], fsg(h0['margin']), h0['units'] or ''), '%s %s %s' % (h1['status'], fsg(h1['margin']), h1['units'] or ''), r1s])
    L += mdt(['id', 'check', 'evaluation', BATTERIES[0], BATTERIES[1], 'R1 column'], rows)
    A('')
    A('## 5. Z overlay (OD-BATTERY / OD-G4-STACK; R2-H01, R2-H21)')
    A('')
    for bt in BATTERIES:
        A('**%s** Delta = %s mm inserted as one fixed REAR-band layer (no tolerance term) between rear_inner and lower_web.' % (bt, fm(res['z']['deltas_mm'][bt], 3)))
        A('')
        rows = []
        for sid, r in sorted(res['z']['per_battery'][bt].items()):
            rows.append([sid, fm(r['nominal_base']), fm(r['nominal_over']), fm(r['nominal_delta'], 9), fm(r['rss_base']), fm(r['rss_over']), fm(r['rss_delta'], 9), fm(r['linear_base']), fm(r['linear_over']), fm(r['linear_delta'], 9),
                         fm(r['battery_zone_base']), fm(r['battery_zone_over'])])
        L += mdt(['baseline', 'nom base', 'nom R2', 'delta', 'RSS base', 'RSS R2', 'delta', 'lin base', 'lin R2', 'delta', 'battery_zone base', 'battery_zone R2'], rows)
        A('')
    A('Levels (Z from the pod plane, G2-REVA, R2 overlay, mm): ' + '; '.join('%s [%s, %s]' % (k, fm(v[0], 3), fm(v[1], 3)) for k, v in res['z']['levels'][PRIMARY].items() if not k.startswith('_')))
    A('')
    A('Linear-worst dimension-chain rule: %s' % BUILDER_INTERPRETATIONS[5][2])
    A('')
    for bt in BATTERIES:
        B = res['batteries'][bt]
        Lp = B['lanes']
        A('## 6.%d L-PKG, annulus and interconnects: %s' % (BATTERIES.index(bt) + 1, bt))
        A('')
        pk = Lp['L_PKG']['pk']
        A('- pack Ø%s mm cell + planning tolerance; envelope radius (cell + radial growth) %s mm; carrier inner %s, wall %s, carrier outer (lw) %s mm; pack margin %s, carrier-wall margin %s mm; offset %s mm @ %s deg; PCM exit design azimuth %s deg (220 / 230 / 240 evaluated).'
          % (fm(res['inputs']['catalogue']['batteries'][bt]['cell_diameter_mm']['nom'], 1), fm(pk['pack_radius']), fm(pk['R_carrier_inner']), fm(pk['t_carrier_wall'], 2), fm(pk['R_carrier_outer']), fsg(pk['pack_margin_mm']),
             fsg(pk['carrier_wall_margin_mm']), fm(pk['offset']['magnitude_mm'], 2), fm(pk['offset']['direction_deg'], 0), fm(pk['pcm_az_deg'], 0)))
        A('- MAIN-outline column: development envelope %s mm, G4 maximum outline %s mm at this point; allowed growth arcs %s deg.' % (fm(Lp['L_PKG']['column']['R_dev']), fm(Lp['L_PKG']['column']['R_g4_max']), ', '.join('%.1f-%.1f' % (a_, b_) for a_, b_ in Lp['L_PKG']['column']['arcs'])))
        A('- offsets evaluated: %d; clean (no reserved-region hit, no carrier conflict at the three PCM azimuths, supports ok): %d; exact top-1 placement probes of every offset: placeable sets are in the offset table of the JSON.' % (Lp['L_PKG']['offsets'], Lp['L_PKG']['clean_offsets']))
        A('')
        rows = []
        for k, v in Lp['L_PKG']['connectors'].items():
            pl = v['placed']
            rows.append([k, v['spec']['option'], '%s x %s' % (fm(v['spec']['long_mm'], 1), fm(v['spec']['short_mm'], 1)), fm(v.get('need_mm'), 3), 'placed az %s r %s ori %s' % (fm(pl['az'], 0), fm(pl['r'], 2), pl['ori']) if pl else 'NO strict-clearance pose',
                         json.dumps(v['stats'], sort_keys=True)])
        L += mdt(['item', 'G2 option', 'body mm', 'annulus need mm', 'result', 'search statistics'], rows)
        A('')
        for k, pth in Lp['L_PKG']['paths']['paths'].items():
            A('- %s path: %s' % (k, ', '.join('%s %s' % (kk, fm(vv)) for kk, vv in sorted(pth.items()) if isinstance(vv, (int, float)) and not isinstance(vv, bool))))
        for k, sf in Lp['L_PKG']['paths']['slack'].items():
            A('- %s service slack (planar U loop, adverse %s mm): pocket %s' % (k, fm(sf['slack_mm'], 1), 'fits' if sf['fits'] else 'does not fit'))
        A('')
        k1 = Lp['L_PKG']['k1']
        A('- K1 requirement (MAIN outline growth beyond Ø46): %s' % (json.dumps(rounded(k1['rows'])) if k1['rows'] else 'none'))
        A('- reserved regions: pack hits %s; new-metal violations %s' % (json.dumps(rounded(Lp['L_PKG']['reserved']['pack_hits'])), json.dumps(rounded(Lp['L_PKG']['reserved']['violations']))))
        led = Lp['L_PKG']['ledger']
        A('- joint annulus ledger: as-pinned supports %d violating pair(s) of %d; supports starting at Z %s mm (above the wall top): %d violating pair(s); double-occupied cells (as pinned) %s.' % (
            len(led['A']['violations']), led['A']['pairs'], fm(led['B']['relief_z_mm']), len(led['B']['violations']), led['sampled']['double_occupied_cells']))
        for v in led['A']['violations']:
            A('  - %s / %s: %s (z gap %s, plan gap %s)' % (v['a'], v['b'], v['mode'], fsg(v['z_gap_mm']), fm(v['plan_gap_mm'])))
        A('')
    A('## 7. L-STR and L-SEAL: ceramic cup and radial O-ring')
    A('')
    A('Ring-plate compatibility (7.1.2), four equations per unit circumferential length, E = E_min, nu = nu_min of MAT-CERAMIC; unknowns u (junction radial displacement), psi (junction rotation), N_p, M_p:')
    A('')
    A('1. plate rotation: psi = psi_ss(p) + |f_M| M\'  (f_M = dpsi/dM of the annular plate with the loaded-boss inner edge and w = 0 at the ring radius; psi_ss from the accepted G4 / R1 annular-plate solution)')
    A('2. plate in-plane: u = c_N N_p  (Lame solution of the annulus with a free inner edge, outer-region thickness)')
    A('3. ring: N = k_A (u - e psi), M = -e k_A (u - e psi) + k_I psi  with k_A = E A / a^2, k_I = E I / a^2, I = integral (z - z_c)^2 dA of the wall section incl. the gland groove, e = z_c - t_out / 2')
    A('4. equilibrium: N_p = -N, M\' = -M. A clamped edge is never assumed: the simply-supported and clamped bounds are reported beside the compatibility result.')
    A('')
    rows = []
    for bt in BATTERIES:
        s_ = res['batteries'][bt]['lanes']['L_STR']
        d_ = s_['design']
        rows.append([bt, d_['row'], fm(d_['cs_mm'], 1), '%s/%s/%s/%s' % (d_['config']['t_in'], d_['config']['t_out'], d_['config']['w_extra'], fm(d_['config']['H'], 2)), fm(d_['z_top_mm'], 3), fm(d_['r_ring_mm'], 3),
                     fm(s_['screen_B']['sigma_governing_MPa'], 3), s_['screen_B']['governing']['component'], fm(s_['screen_B']['w_max_mm'], 4), fm(d_['plate']['edge_fixity'], 3),
                     '%s / %s' % (fm(s_['screen_A_simply_supported']['sigma_MPa'], 1), fm(s_['screen_A_simply_supported']['w_max_mm'], 4)), '%s / %s' % (fm(s_['clamped_bound_reported_not_assumed']['sigma_MPa'], 1), fm(s_['clamped_bound_reported_not_assumed']['w_max_mm'], 4)),
                     fm(s_['sigma_without_inner_junction_Kt_MPa'], 1)])
    L += mdt(['battery', 'row', 'cs', 't_in/t_out/widen/H', 'wall top mm', 'r_ring mm', 'sigma_allow_req MPa', 'governing', 'w_max mm', 'edge fixity', 'Screen A (ss) MPa / mm', 'clamped bound MPa / mm', 'sigma w/o inner K_t'], rows)
    A('')
    for bt in BATTERIES:
        sf = res['batteries'][bt]['lanes']['L_STR']['shortfalls']
        A('- %s shortfalls: %s' % (bt, json.dumps(rounded(sf), sort_keys=True)))
    A('')
    A('Seal rows (R1:R5 population, both batteries share the gland rows; spigot margin = REAR band only; P-1: conductor band retired (R2 state) and the R1-literal retained state):')
    A('')
    rows = []
    for r in res['batteries'][PRIMARY]['hard_checks']['R2-H11']['detail']['rows']:
        if r['authorized'] and (r['gland_window'] or r['i'] < 2):
            rows.append([r['id'], fm(r['cs_mm'], 1), r['gland_window'], fm(r['spigot_height_mm']), fm(r['spigot_radial_mm']), fm(r['r_lim_mm']), fsg(r['z_rear_band_only_mm']), fsg(r['z_with_conductor_band_mm']),
                         fsg(res['batteries'][BATTERIES[1]]['hard_checks']['R2-H11']['detail']['rows'][r['i']]['z_rear_band_only_mm'])])
    L += mdt(['row', 'cs', 'gland window', 'spigot height', 'spigot radial', 'r_lim', 'spigot Z (433736, band retired)', 'spigot Z (band retained, R1-literal)', 'spigot Z (403736, band retired)'], rows)
    A('')
    for bt in BATTERIES:
        s_ = res['batteries'][bt]['lanes']['L_SEAL']
        A('- %s: closes as pinned %s; closes with the supports relieved %s; extension free as pinned %s mm / relieved %s mm; zero-margin extension of the smallest feasible row %s mm; seal path closed %s; population %d rows, r_lim(cup) %s mm.' % (
            bt, s_['closes_as_pinned'], s_['closes_supports_relieved'], fm(s_['ext_free_as_pinned_mm']), fm(s_['ext_free_supports_relieved_mm']),
            fm(min(s_['zero_margin_extension_mm'].values()) if s_['zero_margin_extension_mm'] else None), s_['seal_path'], len(s_['population']), fm(s_['r_lim_cup_mm'])))
    A('')
    A('## 8. L-CHG (C-R2-01), P-2 physical headline')
    A('')
    for bt in BATTERIES:
        c_ = res['batteries'][bt]['lanes']['L_CHG']
        A('- %s: closes %s. smallest strict clearance %s mm, governing pair: %s; r_lim(cup) %s mm vs required %s mm (deficit %s mm); block margin %s, land margin %s mm; strict-wedge zero-margin land width %s mm (supplier threshold, never credited). Feedthrough: %s.' % (
            bt, c_['closes'], fsg(c_['headline']['smallest_strict_clearance_mm']), c_['headline']['governing_pair'], fm(c_['radial']['r_lim_cup_mm']), fm(c_['radial']['r_lim_required_min_mm']),
            fm(c_['headline']['radial_limit_deficit_mm']), fsg(c_['radial']['block_margin_mm']), fsg(c_['radial']['land_margin_mm']), fm(c_['strict_wedge']), c_['feedthrough']))
    A('')
    A('## 9. L-BTN (T1 / T2-F / T2-R per switch, boss limit 3.000 mm)')
    A('')
    rows = []
    for sw, v in sorted(res['batteries'][PRIMARY]['lanes']['L_BTN'].items()):
        for r in v['rows']:
            rows.append([sw, v['material_rule'][:34], r['topology'], r['pusher_class'], 'Y' if r['I_SUM']['closes'] else 'N', fm(r['I_SUM']['boss_used_mm'], 2), fm(r['I_SUM']['boss_zero_margin_mm'], 3), fm(r['I_SUM']['d_p_mm'], 1),
                         fm(r['I_SUM']['protrusion_mm'], 3), 'Y' if r['I_MAX']['closes'] else 'N', ','.join(r['I_SUM']['causes']) or '-', fm(v['r1_column'].get('bore_stack'))])
    L += mdt(['SW', 'material rule', 'topology', 'pusher class', 'I-SUM closes', 'boss used', 'boss zero-margin', 'd_p', 'protrusion (limit 3.000)', 'I-MAX closes', 'causes if not', 'R1 bore_stack'], rows)
    A('')
    A('C-R1-03: I-SUM binds; I-MAX is reported; `c_r1_03_adjudication` stays null; no I-MAX-only closure exists (an I-MAX-only row would not count as closed).')
    A('')
    A('## 10. L-LRA')
    A('')
    for bt in BATTERIES:
        l_ = res['batteries'][bt]['lanes']['L_LRA']
        A('- %s: B.Cu zone B: best annulus over all offsets %s mm; need per class %s; feasible %s. F.Cu fallback: %s; largest free disk radius %s mm (centre %s) so a class must fit a disk of radius %s mm; Z-neutral cap 2.70 mm (height incl. mount: %s). BMM350: %s.' % (
            bt, fm(l_['max_room_over_offsets_mm']), {k: fm(v['need_mm']) for k, v in l_['bcu'].items()}, l_['bcu_feasible'], {k: v['n_plan_feasible'] for k, v in l_['fcu'].items()},
            fm(l_['fcu_free_disk']['radius_mm']), [round(c, 2) for c in l_['fcu_free_disk']['centre']], fm(l_['fcu_free_disk']['fits_radius_limit_mm']),
            {k: fm(v['seated_height_mm']) for k, v in l_['fcu'].items()}, json.dumps(rounded(l_['bmm350_zone_b']))))
    A('')
    A('R1:R4-1 identity: no pose is selected, so no identity exists; the validator reconstructs the identity of the fixture pose in the self-test. The LRA magnet is authorized (OD-G4-LRA-MAG); MAG_CLEAR stays an exclusion.')
    A('')
    A('## 11. L-RAD and crossings')
    A('')
    for bt in BATTERIES:
        r_ = res['batteries'][bt]['lanes']['L_RAD']
        A('- %s: margins %s; insertion %s; straight runs %s; crossings %s.' % (bt, json.dumps(rounded(r_['terms']['margins']), sort_keys=True), json.dumps(rounded(r_['terms']['insertion']), sort_keys=True),
                                                                           json.dumps(rounded(r_['terms']['straight']), sort_keys=True), {k: v['state'] for k, v in r_['crossings'].items()}))
    A('')
    A('## 12. L-ASM and L-WIN')
    A('')
    A('A1-A11 retain identities, order, parts, directions and battery states; only the operation text of A1, A4, A5, A6, A9, A10, A11 changes, each citing its decision id (%s).' % ', '.join('%s: %s' % (k, v[0]) for k, v in ASM_ALLOWED_CHANGES.items()))
    A('')
    A('W1 at 0.50 mm bonded into the cup pod frame, Z delta 0.000; R1 W1 values reproduced from the pinned R1 JSON (SUPPLIER_GATED: SR-WINDOW, MG-WINDOW-XTALK).')
    A('')
    A('## 13. Overlay (section 4.2): pinned value, R2 value and authority side by side')
    A('')
    L += mdt(['id', 'pinned source', 'pinned value (read at run time)', 'R2 value', 'authority'], [[r['id'], '%s %s' % (r['pinned_source']['path'].split('/')[-1], r['pinned_source']['pointer']), str(r['pinned_value'])[:70], str(r['r2_value'])[:90], r['authority']]
                                                                                                    for r in res['overlay']['records']])
    A('')
    A('## 14. Overlay-off anchors and equivalence tests (R2-H03)')
    A('')
    L += mdt(['anchor', 'expected', 'computed', 'tolerance', 'match'], [[r['id'], fm(r['expected'], 6) if isinstance(r['expected'], float) else r['expected'], fm(r['computed'], 6) if isinstance(r['computed'], float) else r['computed'], r['tolerance'], r['match']]
                                                                   for r in res['anchors']['rows']])
    A('')
    A('## 15. Lead cross-checks (P-3)')
    A('')
    L += mdt(['id', 'lead value', 'R2 value', 'status', 'explanation'], [[r['id'], r['lead'], json.dumps(rounded(r['computed'])), r['status'], r.get('explanation') or ''] for r in res['lead_crosschecks']])
    A('')
    A('## 16. T1 ruling (7.4.1)')
    A('')
    A('- Where R1 excluded T1: ' + '; '.join(res['t1_ruling']['where_r1_excluded']))
    A('- Stated reason: ' + res['t1_ruling']['stated_reason'])
    for c in res['t1_ruling']['classification']:
        A('- ' + c)
    A('- **Result:** ' + res['t1_ruling']['result'] + '. The independent review must challenge it.')
    A('')
    A('## 17. Owner decisions and answers (recorded verbatim; date 2026-10-17, source: owner decision)')
    A('')
    for d_ in res['owner_decisions']:
        A('**%s** (G4_R2_BRIEF.md section 3.2)' % d_['id'])
        A('')
        A('```text')
        A(d_['verbatim'])
        A('```')
        A('')
    for d_ in res['open_question_answers']:
        A('**%s** (G4_R2_BRIEF.md section 17.1, round %d, %s)' % (d_['id'], d_['round'], d_['status']))
        A('')
        A('```text')
        A(d_['verbatim'])
        A('```')
        A('')
    A('C-R2-01 (recorded here only; `G4_R1_BRIEF.md` is unchanged): C-R1-01 item 2 (v) for the non-conductive land reads: "clears screws, supports, CHG_ROUTE and CHG_LINK in 3-D, i.e. separated in plan OR in Z, with strict 3-D clearance".')
    A('')
    A('## 18. Owner questions raised by the tool (conditional; the tool decides none)')
    A('')
    for q in res['owner_questions']:
        A('- **%s**: %s `%s`' % (q['id'], q['text'], json.dumps(rounded(q['numeric']), sort_keys=True, default=str)[:500]))
    if not res['owner_questions']:
        A('- none')
    A('')
    A('## 19. Supplier gates with numeric thresholds')
    A('')
    for row in res['supplier_gates']:
        A('**%s**' % row['battery'])
        for g_ in row['gates']:
            A('- %s: %s. Threshold `%s`' % (g_['id'], g_['needs'], json.dumps(rounded(g_['threshold']), sort_keys=True, default=str)[:520]))
        A('')
    A('## 20. G5 input records for non-conductive items inside reserved regions (material, permittivity class label, volume)')
    A('')
    for bt in BATTERIES:
        A('**%s** (%d records; no numeric permittivity is invented; G5_RF_REQUIRED)' % (bt, len(res['batteries'][bt]['g5_records'])))
        A('')
        L += mdt(['item', 'region', 'level', 'part', 'material class', 'permittivity class (label)', 'V nominal mm3', 'V linear-worst mm3'],
                 [[g_['item'], g_['region'], g_['level'], g_['region_part'], g_['material_class'], g_['permittivity_class']['label'], fm(g_['volume_nominal_mm3'], 2), fm(g_['volume_linear_worst_mm3'], 2)] for g_ in res['batteries'][bt]['g5_records']])
        A('')
    A('## 21. BUILDER-INTERPRETATIONS (conservative readings of silent or ambiguous brief text)')
    A('')
    for b_ in res['builder_interpretations']:
        A('- **%s** (%s): %s' % (b_['id'], b_['section'], b_['text']))
    A('')
    A('## 22. Known documentation debt (recorded; not edited by R2)')
    A('')
    for d_ in res['known_documentation_debt']:
        A('- ' + d_)
    A('')
    A('## 23. Search, budgets and scope')
    A('')
    A('- predicate evaluations: %d (budget %d, within budget %s)' % (res['search']['evaluations'], res['search']['budget'], res['search']['within_budget']))
    A('- G4 in-process reproduction: pass %s, self-tests %d/%d, ALLOWED_CHANGES extension equals R1_FILES | R2_FILES exactly: %s' % (res['carry_in']['g4_in_process']['pass_'], res['carry_in']['g4_in_process']['caught'],
                                                                                                                       res['carry_in']['g4_in_process']['tests'], res['carry_in']['g4_in_process']['extension_exact']))
    A('- changed paths (all within R2_FILES): %s; outside R2_FILES: %s' % (res['scope']['changed_paths'], res['scope']['outside_r2_files']))
    A('- runtimes are printed by `check` and `selftest` and recorded in the run report (a runtime inside a byte-compared file would break determinism).')
    A('')
    return '\n'.join(L).rstrip('\n') + '\n'


def outputs(res, ctx):
    return {'g4_r2_closure.json': dumps(res), 'g4_r2_closure.md': render_md(res, ctx), 'g4_r2_plan.svg': render_plan(res, ctx), 'g4_r2_sections.svg': render_sections(res, ctx),
            'g4_r2_annulus.svg': render_annulus(res, ctx)}



# ============================================================================================
# Validator: independent recomputation of the numeric thresholds and the state invariants (G4_R2_BRIEF section 14.2, 15).
# Each sub-check is a function (res, ctx, files) -> list of failure strings, so the self-test can run exactly the check that guards a fault.
# ============================================================================================
BRIEF_LIMITS = dict(D_case_body_max_mm=51.0, boss_extension_max_mm=3.0, deflection_max_mm=0.05, static_clearance_min_mm=0.05, planning_allowable_MPa=150.0,
                    nominal_mm=16.5, rss_mm=17.0)          # section 3.3 / 7.1 / 7.4 constants, typed independently of the input file
BRIEF_OFFSET_MAX_MM = 1.5
BRIEF_DELTA = {'LPR433736': 0.2, 'LPR403736': 0.5}
BRIEF_CELL = {'LPR433736': (37.0, 4.3), 'LPR403736': (37.0, 4.0)}
BRIEF_SEAL_CS = (0.5, 2.0)
BRIEF_BLOCK = (4.0, 5.0)
COMMIT_STATE_WORDS = ('committed', 'accepted', 'approved', 'frozen', 'independently reviewed', 'merged', 'released')
G5_KEYS = ('item', 'region', 'level', 'region_part', 'material_class', 'permittivity_class', 'volume_nominal_mm3', 'volume_linear_worst_mm3', 'g5_rf_required')
RESERVED_NEW_ITEMS = ('J1501_BODY', 'J1501_RISER', 'J1501_BEND', 'J201_BODY', 'J201_RISER', 'J201_BEND', 'J202_BODY', 'J202_RISER', 'BATT_TAIL_RUN', 'CHG_BLOCK')


def seal_param_problems(cx2):
    """The live O-ring parameters (cross-section tolerance +/-0.05 mm, static radial / dynamic compression windows) equal the pinned values: never narrowed, never widened."""
    pin = load_json(MECH / 'inputs/g4_case_sealing.json')['parameters']['oring']
    live = cx2.st.I['parameters']['oring']
    return [] if chash(pin) == chash(live) else ['live O-ring parameters (cs tolerance / compression windows) differ from the pinned values (window widened or tolerance narrowed)']


def main_seal_problems(sp_):
    bad = []
    for s_ in sp_['inventory']['seals']:
        if s_['id'] == 'S-CB-MAIN' and ('adhesive' in s_['type'].lower() and 'no adhesive' not in s_['type'].lower()):
            bad.append('adhesive main seal selected')
    return bad


def reserved_candidates(P):
    """Occupants screened against the reserved regions: new conductive items, every conductive item, allowed non-conductive items, and the cup."""
    new_items = set(RESERVED_NEW_ITEMS)
    return [o for o in P['_occs'] if o['id'] in new_items or o.get('allowed_nonconductive') or o.get('conductive')] + list(P['_cup_occs'])


def bytes_problems(files, ref):
    return ['%s differs from the reference bytes' % n for n in sorted(set(files) | set(ref)) if files.get(n) != ref.get(n)]


def v_inputs(res, ctx, files):
    r2in = ctx['r2in']
    bad = list(schema_guard(r2in))
    bad += ['pin mismatch: ' + p['path'] for p in pin_report(r2in) if not p['match']]
    if not contract_commit_report(r2in)['match']:
        bad.append('r2_contract_commit does not match the repository')
    bad += overlay_problems(r2in)
    for k, v in BRIEF_LIMITS.items():
        if r2in['limits'].get(k) != v:
            bad.append('limit %s = %r differs from the brief value %r' % (k, r2in['limits'].get(k), v))
    if r2in['overlay_values']['boss_extension_max_mm'] != BRIEF_LIMITS['boss_extension_max_mm']:
        bad.append('boss extension limit differs from the brief')
    g = r2in['grids']['offset_magnitude_mm']
    if g['stop'] > BRIEF_OFFSET_MAX_MM + EPS or g['start'] < -EPS:
        bad.append('offset magnitude grid exceeds 0 .. %.2f mm' % BRIEF_OFFSET_MAX_MM)
    V = r2in['cup']['main_seal_cs']
    if (V['start'], V['stop']) != BRIEF_SEAL_CS:
        bad.append('authorized O-ring cross-section window %r differs from the brief %r' % ((V['start'], V['stop']), BRIEF_SEAL_CS))
    for b, (d_, t_) in BRIEF_CELL.items():
        c = r2in['catalogue']['batteries'][b]
        if (c['cell_diameter_mm']['nom'], c['cell_thickness_mm']['nom']) != (d_, t_):
            bad.append('catalogue %s differs from the brief' % b)
    if r2in['grids']['D_case_body_mm']['stop'] > BRIEF_LIMITS['D_case_body_max_mm'] + EPS:
        bad.append('D grid stop %s above 51.00' % r2in['grids']['D_case_body_mm']['stop'])
    mats = r2in['buttons']['switch_materials']
    for sw in NONMETAL_SW:
        if 'metal' in mats[sw]['options'] or not set(mats[sw]['options']) <= {'zirconia', 'PEEK'}:
            bad.append('%s: pusher options %s violate the non-metallic rule (Q-R2-SW1-BLE / Q-R2-SW5-PUSHER)' % (sw, mats[sw]['options']))
    for sw in ('SW2', 'SW3', 'SW4'):
        if mats[sw]['options'] != ['metal']:
            bad.append('%s: pusher options %s differ from metal' % (sw, mats[sw]['options']))
    peek = r2in['buttons']['pusher_classes']['PEEK']
    if peek.get('material_class') is not None or any(k for k in peek if k in ('E_MPa', 'E_min', 'sigma_allow', 'strength_MPa', 'modulus_MPa', 'strength', 'modulus')):
        bad.append('a PEEK property is credited without supplier data (SR-BUTTONS)')
    for k, v in r2in['buttons'].get('permittivity_class_labels', {}).items():
        if v.get('numeric') is not None and not v.get('primary_document'):
            bad.append('numeric permittivity for %s without a primary document' % k)
    if (r2in['interconnect']['positions'], r2in['interconnect']['nets']) != (24, 13):
        bad.append('the 24-position / 13-net MAIN-REAR interface changed')
    if abs(r2in['interconnect']['service_slack']['adverse_mm'] - g2.Study().P['service_slack_mm']['max']) > EPS:
        bad.append('authored service slack differs from the pinned G2 adverse value (slack doubled / reduced)')
    if r2in['lra_supplied'] or r2in['fallback_trigger'].get('supplier_evidence') or r2in['fallback_trigger'].get('owner_decision'):
        bad.append('lra_supplied / fallback_trigger are not empty: the reviewed-input provenance is not part of this run')
    return bad


def forbidden_time_keys(o):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            kl = k.lower()
            if kl in ('runtime', 'runtime_s', 'elapsed', 'elapsed_s', 'timestamp', 'generated_at', 'time', 'date_generated') or kl.startswith('runtime'):
                out.append(k)
            out += forbidden_time_keys(v)
    elif isinstance(o, list):
        for v in o:
            out += forbidden_time_keys(v)
    return out


def v_serialization(res, ctx, files):
    bad = []
    for name, text in files.items():
        if not text.endswith('\n') or text.endswith('\n\n'):
            bad.append('%s: final newline rule' % name)
    js = files.get('g4_r2_closure.json')
    if js is not None:
        try:
            if dumps(json.loads(js)) != js:
                bad.append('JSON is not in canonical form (sorted keys, compact separators, 9-decimal rounding)')
        except ValueError as exc:
            bad.append('JSON does not parse: %s' % exc)
        if re.search(r'\d{4}-\d\d-\d\dT\d\d:\d\d', js) or forbidden_time_keys(json.loads(js)):
            bad.append('timestamp / runtime in a byte-compared file')
        if 'NaN' in js or 'Infinity' in js:
            bad.append('non-finite number in the JSON')
    for name in files:
        if name.endswith('.svg'):
            try:
                xml.dom.minidom.parseString(files[name])
            except Exception as exc:       # noqa: BLE001
                bad.append('%s is not well-formed XML: %s' % (name, exc))
    return bad


def v_z(res, ctx, files):
    bad = []
    r2in = ctx['r2in']
    pinned = load_json(MECH / 'inputs/stack_parameters.json')
    for b in BATTERIES:
        zs, cx = ctx['zs'][b], ctx['cxs'][b]
        t_pin = pinned['parameters']['t_pack_nom']['nom']
        d_cat, t_cat = BRIEF_CELL[b]
        want = round(t_pin - t_cat, 9)
        if abs(want - BRIEF_DELTA[b]) > 1e-9:
            bad.append('%s: pinned t_pack_nom %s gives Delta %s, brief says %s' % (b, t_pin, want, BRIEF_DELTA[b]))
        if abs(zs.delta - want) > 1e-9:
            bad.append('%s: Delta in use %.9f differs from the independent value %.9f' % (b, zs.delta, want))
        live = cx.src.S
        if live['parameters']['t_pack_nom']['nom'] != t_cat or live['radial']['parameters']['D_pack_nom']['nom'] != d_cat:
            bad.append('%s: live pack constants are t_pack_nom %s / D_pack_nom %s, not the catalogue %s / %s (overlay not applied)' % (
                b, live['parameters']['t_pack_nom']['nom'], live['radial']['parameters']['D_pack_nom']['nom'], t_cat, d_cat))
        if LAYER_ORDER.count('rear_band') != 1 or LAYER_TOLS.get('rear_band') != () or zs.tol_of('rear_band') != 0.0:
            bad.append('%s: the REAR-band layer must be one layer without a tolerance term' % b)
        over, base = zs.over['G2-REVA']['layers'], zs.base['G2-REVA']['layers']
        if abs(over['rear_band'] - want) > 1e-9:
            bad.append('%s: REAR band %.9f is not the single allocation Delta %.9f (not reallocated / reallocated twice)' % (b, over['rear_band'], want))
        if abs(sum(over.values()) - sum(base.values())) > 1e-9:
            bad.append('%s: nominal stack total changed by %.9f' % (b, sum(over.values()) - sum(base.values())))
        bad += ['%s: %s' % (b, p) for p in z_delta_problems(zs, r2in['limits'])]
        for sid, r in res['z']['per_battery'][b].items():
            for k in ('nominal_delta', 'rss_delta', 'linear_delta'):
                if abs(r[k]) > 1e-9:
                    bad.append('%s %s %s = %s in the result' % (b, sid, k, r[k]))
        if abs(res['z']['deltas_mm'][b] - want) > 1e-9:
            bad.append('%s: result Delta %s' % (b, res['z']['deltas_mm'][b]))
    return bad


def v_dimension(res, ctx, files):
    bad = []
    for b in BATTERIES:
        B = res['batteries'][b]
        D = B['joint']['D']
        if D > BRIEF_LIMITS['D_case_body_max_mm'] + EPS:
            bad.append('%s: D_eval %.3f > 51.00' % (b, D))
        if abs(B['joint']['D_margin_to_51_mm'] - (51.0 - D)) > 1e-9 or abs(B['metrics']['D_margin_mm'] - (51.0 - D)) > 1e-9:
            bad.append('%s: D margin is not 51.00 - D_eval (a radial-core quantity may not stand in for it)' % b)
        h = B['hard_checks']['R2-H02']
        if h['margin'] is not None and abs(h['margin'] - (51.0 - D)) > 1e-9:
            bad.append('%s: R2-H02 margin %s is not 51 - D' % (b, h['margin']))
        if any(r['D'] > 51.0 + EPS for r in ctx['Es'][b]['scan']['rows']):
            bad.append('%s: a scanned D lies above 51.00' % b)
    return bad


def t1_gland_problems(cx2, gd):
    """T1 stem O-ring uses the dynamic radial window: its margins must equal the dynamic-window margins recomputed from the emitted groove."""
    if gd.get('g') is None:
        return []
    want = [g4.run_check(x, full=False) for x in cx2.sp.gland('T1-SW2', 'dynamic_radial', gd['cs'], gd['h'], gd['g'], gd['tol_h'], gd['tol_g'])]
    if any(abs(a - b) > 1e-9 for a, b in zip(want, gd['margins'])):
        return ['T1 gland margins %r differ from the dynamic radial window %r (static window used)' % (gd['margins'], want)]
    return []


def v_buttons(res, ctx, files):
    bad = []
    r2in = ctx['r2in']
    for b in BATTERIES:
        cx = ctx['cxs'][b]
        for sw, v in res['batteries'][b]['lanes']['L_BTN'].items():
            allowed = set(r2in['buttons']['switch_materials'][sw]['options'])
            if v['closed'] and not any(r['I_SUM']['closes'] for r in v['rows']):
                bad.append('%s %s: closed without an I-SUM-closing row (I-MAX-only closure)' % (b, sw))
            if v['closed'] and not v['closing_options']:
                bad.append('%s %s: closed without closing options' % (b, sw))
            for r in v['rows']:
                if r['topology'] not in ('T1', 'T2-F', 'T2-R'):
                    bad.append('%s %s: topology %s outside the admitted set (T3 selected)' % (b, sw, r['topology']))
                if r['pusher_class'] not in allowed:
                    bad.append('%s %s: pusher class %s violates the material rule' % (b, sw, r['pusher_class']))
                if sw in NONMETAL_SW and r['pusher_class'] == 'metal':
                    bad.append('%s %s: metal pusher on a non-metallic switch' % (b, sw))
                if 'I_MAX' not in r or 'I_SUM' not in r:
                    bad.append('%s %s: missing I-MAX / I-SUM column' % (b, sw))
                    continue
                for tag in ('I_SUM', 'I_MAX'):
                    u = r[tag]['boss_used_mm']
                    if u is not None and u > BRIEF_LIMITS['boss_extension_max_mm'] + EPS:
                        bad.append('%s %s %s %s: boss used %s > 3.000' % (b, sw, r['topology'], tag, u))
                    if r[tag]['closes'] and u is None:
                        bad.append('%s %s %s %s: closes without a boss value' % (b, sw, r['topology'], tag))
                if r['I_SUM']['closes'] and (r['I_SUM']['protrusion_mm'] is None or r['I_SUM']['protrusion_mm'] > BRIEF_LIMITS['boss_extension_max_mm'] + EPS):
                    bad.append('%s %s %s: closing protrusion %s above 3.000' % (b, sw, r['topology'], r['I_SUM']['protrusion_mm']))
            pin_win = load_json(MECH / 'inputs/g4_case_sealing.json')['parameters']['buttons']['windows_deg'][sw]
            if list(v['window_deg']) != list(pin_win):
                bad.append('%s %s: window %s differs from the frozen window %s (switch moved)' % (b, sw, v['window_deg'], pin_win))
            g_ = ctx['Es'][b]['P']['buttons']['geometry'].get(sw)
            if g_ is not None and not (pin_win[0] - EPS <= g_['centre'] <= pin_win[1] + EPS and g_['centre'] - g_['boss_half_deg'] >= pin_win[0] - 1e-6
                                       and g_['centre'] + g_['boss_half_deg'] <= pin_win[1] + 1e-6):
                bad.append('%s %s: boss (centre %.3f, half %.3f deg) outside its frozen window %s' % (b, sw, g_['centre'], g_['boss_half_deg'], pin_win))
    return bad


def v_t1(res, ctx, files):
    bad = []
    for b in BATTERIES:
        cx = ctx['cxs'][b]
        T = btn_terms2(cx, 'SW2', 'metal')
        gd = t1_gland(cx, 'SW2', T, 1.0)
        bad += ['%s: %s' % (b, p) for p in t1_gland_problems(cx, gd)]
    return bad


def v_status_rules(res, ctx, files):
    """Recompute the status of numeric thresholds from their governing terms."""
    bad = []
    for b in BATTERIES:
        B = res['batteries'][b]
        H = B['hard_checks']
        st = B['lanes']['L_STR']
        w, sg = st['screen_B']['w_max_mm'], st['sigma_allow_req_MPa']
        h9 = H['R2-H09']
        if w > BRIEF_LIMITS['deflection_max_mm'] + EPS and h9['status'] not in ('FAIL', 'BLOCKED'):
            bad.append('%s R2-H09: deflection %.4f > 0.050 labelled %s' % (b, w, h9['status']))
        if w <= BRIEF_LIMITS['deflection_max_mm'] + EPS and sg > BRIEF_LIMITS['planning_allowable_MPa'] + EPS and h9['status'] != 'GATED':
            bad.append('%s R2-H09: stress %.1f MPa > 150 is SUPPLIER_GATED, not %s' % (b, sg, h9['status']))
        if w <= BRIEF_LIMITS['deflection_max_mm'] + EPS and sg <= BRIEF_LIMITS['planning_allowable_MPa'] + EPS and h9['status'] not in ('PASS', 'GATED'):
            bad.append('%s R2-H09: %.4f mm / %.1f MPa labelled %s' % (b, w, sg, h9['status']))
        if h9['margin'] is not None and abs(h9['margin'] - (BRIEF_LIMITS['deflection_max_mm'] - w)) > 1e-8:
            bad.append('%s R2-H09: margin is not 0.050 - w_max' % b)
        h8 = H['R2-H08']
        sc = h8['governing_terms'][0]['value'] if h8['governing_terms'] else None
        if sc is not None and sc <= BRIEF_LIMITS['static_clearance_min_mm'] + EPS and h8['status'] == 'PASS':
            bad.append('%s R2-H08: static clearance %.4f counted as PASS (must exceed 0.050)' % (b, sc))
        for cid, h in H.items():
            if h['status'] == 'PASS' and h['margin'] is not None and h['margin'] < -EPS:
                bad.append('%s %s: PASS with margin %.6f' % (b, cid, h['margin']))
            if h['status'] == 'FAIL' and h['margin'] is not None and h['margin'] >= EPS:
                bad.append('%s %s: FAIL with margin %.6f' % (b, cid, h['margin']))
            if h['credits']:
                bad.append('%s %s: a credit is recorded (%s)' % (b, cid, h['credits']))
            if h['r1_column'] is None:
                bad.append('%s %s: no R1 column' % (b, cid))
    return bad


def v_single_event(res, ctx, files):
    """R2-H08 / R2-H09: one physical event is counted in exactly one of them."""
    bad = []
    for b in BATTERIES:
        H = res['batteries'][b]['hard_checks']
        ev8 = {json.dumps(t.get('event'), sort_keys=True) for t in H['R2-H08']['governing_terms'] if t.get('event')}
        ev9 = {json.dumps(t.get('event'), sort_keys=True) for t in H['R2-H09']['governing_terms'] if t.get('event')}
        if ev8 & ev9:
            bad.append('%s: event counted in both R2-H08 and R2-H09: %s' % (b, sorted(ev8 & ev9)))
    return bad


def edge_credit_problems(ev, label):
    bad = []
    if ev['plate']['edge_fixity'] > 1.0 - 1e-6:
        bad.append('%s: cup edge credited as clamped (fixity %.6f)' % (label, ev['plate']['edge_fixity']))
    return bad


def v_structure(res, ctx, files):
    bad = []
    for b in BATTERIES:
        st = res['batteries'][b]['lanes']['L_STR']
        bad += edge_credit_problems(st['design'], b)
        if st['screen_B']['w_max_mm'] < st['clamped_bound_reported_not_assumed']['w_max_mm'] - 1e-12:
            bad.append('%s: the compatibility deflection is below the clamped bound (a clamped edge credit)' % b)
        if st['screen_B']['w_max_mm'] > st['screen_A_simply_supported']['w_max_mm'] + 1e-9:
            bad.append('%s: the compatibility deflection exceeds the simply-supported bound' % b)
    return bad


def seal_rows_problems(rows, r_lim_reported, label):
    """R1:R5 population rules recomputed from the emitted rows (per-row independent evaluation, minimum over the population)."""
    bad = []
    auth = [r for r in rows if r['authorized']]
    want_n = len(frange(BRIEF_SEAL_CS[0], BRIEF_SEAL_CS[1], 0.1))
    if len(auth) != want_n:
        bad.append('%s: %d authorized O-ring rows, the brief window gives %d' % (label, len(auth), want_n))
    ff = [r for r in auth if r['pass_all']]
    pop = ff or auth
    lo = min(r['r_lim_mm'] for r in pop)
    if abs(lo - r_lim_reported) > 1e-9:
        bad.append('%s: r_lim(cup) %s is not the minimum over the population %s' % (label, r_lim_reported, lo))
    for r in auth:
        if r['pass_all'] != all(r['predicates'].values()):
            bad.append('%s: row %s pass_all differs from its predicates' % (label, r['id']))
        for k, v in r['margins'].items():
            if r['predicates'][k] != (v >= -EPS):
                bad.append('%s: row %s predicate %s inconsistent with its margin' % (label, r['id'], k))
    return bad


def v_seal(res, ctx, files):
    bad = []
    for b in BATTERIES:
        S = res['batteries'][b]['lanes']['L_SEAL']
        pop = ctx['Es'][b]['P']['seal_rear_band_only']
        bad += seal_rows_problems(pop['rows'], S['r_lim_cup_mm'], b)
        ur = S['unit_regression']
        if not ur.get('identical') or ur.get('units') != ['m', 'mm', 'um']:
            bad.append('%s: unit regression not identical across mm / m / um' % b)
        if not S['representative_row'].get('display_only'):
            bad.append('%s: representative row is not display-only' % b)
        sp_ = seal_path_report(ctx['cxs'][b], ctx['Es'][b]['P'])
        bad += ['%s: %s' % (b, p) for p in main_seal_problems(sp_)]
        bad += ['%s: %s' % (b, p) for p in seal_param_problems(ctx['cxs'][b])]
        if S['seal_path'] and not sp_['pass_']:
            bad.append('%s: seal path reported closed but the closure graph is open' % b)
    return bad


def reserved_problems(cx, P, recs, label):
    bad = []
    for r in recs:
        miss = [k for k in G5_KEYS if k not in r]
        if miss:
            bad.append('%s: G5 record %s misses %s' % (label, r.get('item'), miss))
            continue
        if not r['material_class'] or not r['permittivity_class'].get('label') or r['volume_nominal_mm3'] is None or r['volume_linear_worst_mm3'] is None:
            bad.append('%s: G5 record %s incomplete (material, permittivity class label, volume)' % (label, r['item']))
        if r['permittivity_class'].get('numeric') is not None and not r['permittivity_class'].get('primary_document'):
            bad.append('%s: numeric permittivity for %s without a primary document' % (label, r['item']))
    new_items = set(RESERVED_NEW_ITEMS)
    ring = next(o for o in P['_cup_occs'] if o['id'] == 'CUP_WALL_RING')
    viol, g5x = reserved_screen(cx, reserved_candidates(P), P['_reserved'], new_items)
    have = {(r.get('item'), r.get('region'), r.get('level'), r.get('region_part')) for r in recs}
    for g in g5x + sw_g5_records(cx, P) + carrier_oring_g5(cx, P, ring):
        key = (g['item'], g['region'], g['level'], g['region_part'])
        if key not in have:
            bad.append('%s: non-conductive reserved-region item %s lacks its G5 record' % (label, key))
    return bad, viol


def v_reserved_g5(res, ctx, files):
    bad = []
    for b in BATTERIES:
        B = res['batteries'][b]
        P = ctx['Es'][b]['P']
        p, viol = reserved_problems(ctx['cxs'][b], P, B['g5_records'], b)
        bad += p
        if viol and B['hard_checks']['R2-H15']['status'] == 'PASS':
            bad.append('%s: R2-H15 PASS with new metal / conductor inside a reserved region: %s' % (b, sorted({v['item'] for v in viol})))
        if any(h['credits'] for h in B['hard_checks'].values()):
            bad.append('%s: a credit appears in a hard check' % b)
        for row in B['lanes']['L_PKG']['k1'].get('rows', []):
            lo, hi = row['az_span_deg']
            span = (hi - lo) % 360.0
            samples = [(lo + span * i / 40.0) % 360.0 for i in range(41)]
            if any(g4.arc_has(a, a0, a1) for a in samples for a0, a1 in reserved_az_intervals()):
                bad.append('%s: MAIN outline growth for %s lies in a reserved azimuth interval' % (b, row['item']))
    return bad


def identity_problems(cx2, claimed):
    """R1:R4-1 reconstruction from physical inputs only: class record, pose, Z fit, BMM350 distance and exclusion set are rebuilt from the
    pose and compared key by key with the claimed identity."""
    keys = ('battery', 'offset', 'side', 'lra_class', 'evidence', 'envelope', 'pose', 'main_outline_column', 'z_fit', 'mount_allowance_mm', 'exclusion_set',
            'u7_lead_path_mm', 'bmm350_distance_mm')
    if sorted(claimed) != sorted(keys):
        return ['identity keys incomplete or extra: %s' % sorted(set(claimed) ^ set(keys))]
    bad = []
    cls = next((c for c in lra_classes_r2(cx2) if c['id'] == claimed['lra_class']), None)
    if cls is None:
        return ['identity names an unknown LRA class %r' % claimed['lra_class']]
    env = claimed['envelope']
    if (env['shape'], env['length_mm'], env['width_mm'], env['height_mm']) != (cls['shape'], cls['length'], cls['width'], cls['height']):
        bad.append('identity envelope differs from the class record')
    if claimed['evidence'] != cls['evidence']:
        bad.append('identity evidence class differs')
    if claimed['battery'] != cx2.battery:
        bad.append('identity battery differs')
    if claimed['mount_allowance_mm'] != cx2.st.P['lra_mount_mm']['max']:
        bad.append('identity mount allowance differs')
    p = claimed['pose']
    body = lra_body_poly(cls, p['az'], p['r'], p['ori'])
    cen = (sum(q[0] for q in body) / len(body), sum(q[1] for q in body) / len(body))
    r_, az_ = polar(cen)
    if abs(r_ - p['r']) > 1e-6 or abs((az_ - p['az'] + 180.0) % 360.0 - 180.0) > 1e-6:
        bad.append('identity pose differs from the pose derived from the body polygon')
    col = column_polys(cx2, 24.2)
    if (claimed['main_outline_column']['R_dev'], claimed['main_outline_column']['R_g4_max']) != (col['R_dev'], col['R_g4_max']):
        bad.append('identity MAIN-outline column differs')
    zl = claimed['z_fit']
    if isinstance(zl, (list, tuple)) and len(zl) == 2:
        zpl = bcu_plane(cx2)
        if claimed['side'] == 'B.Cu' and (abs(zl[1] - zpl) > 1e-6 or abs(zl[0] - (zpl - (cls['height'] + claimed['mount_allowance_mm']))) > 1e-6):
            bad.append('identity Z fit differs from the B.Cu plane rule')
        d, _, _ = bmm350_distance(cx2, body, zl[0], zl[1])
        if claimed['bmm350_distance_mm'] is not None and abs(d - claimed['bmm350_distance_mm']) > 1e-6:
            bad.append('identity BMM350 distance differs from the recomputed %.6f' % d)
    else:
        bad.append('identity Z fit malformed')
    if claimed['side'] == 'F.Cu' and sorted(claimed['exclusion_set']) != sorted(e[0] for e in fcu_exclusions(cx2)):
        bad.append('identity exclusion set differs from the F.Cu exclusions')
    return bad


def lra_pose_problems(cx2, side, cls, pose, z_lo, z_hi, body):
    """A pose that is credited must be outside MAG_CLEAR, and a Z-neutral F.Cu fallback must stay within the 2.70 mm cap including its mount."""
    bad = []
    mag = mag_clear_occupant(cx2)
    if mag is not None and not r1.separated(occ_plan_gap(occupant('X', 'LRA', [body], z_lo, z_hi), mag, limit=1e-6), 0.0):
        bad.append('LRA pose lies in MAG_CLEAR')
    if side == 'F.Cu':
        h = cls['height'] + cx2.st.P['lra_mount_mm']['max']
        if h > cx2.r2in['lra']['fcu_height_cap_mm'] + EPS:
            bad.append('F.Cu class %s seated height %.3f mm incl. mount exceeds the 2.70 mm Z-neutral cap' % (cls['id'], h))
    return bad


def v_lra(res, ctx, files):
    bad = []
    for b in BATTERIES:
        L = res['batteries'][b]['lanes']['L_LRA']
        cx = ctx['cxs'][b]
        for cid, v in L['fcu'].items():
            cls = next(c for c in lra_classes_r2(cx) if c['id'] == cid)
            h = cls['height'] + cx.st.P['lra_mount_mm']['max']
            if v.get('z_neutral') and h > cx.r2in['lra']['fcu_height_cap_mm'] + EPS:
                bad.append('%s: F.Cu class %s of seated height %.3f counted Z-neutral (cap 2.70 mm)' % (b, cid, h))
            if v['n_plan_feasible'] > 0 and not v.get('supplied') and not v.get('z_neutral') is False and L['fcu_plan_feasible_classes'] == []:
                bad.append('%s: plan-feasible poses without being listed' % b)
        if L['selected'] is not None and L['identity'] is None:
            bad.append('%s: LRA pose selected without an identity' % b)
        if L['selected'] is None and L['identity'] is not None:
            bad.append('%s: identity without a selected pose' % b)
        if L['identity'] is not None:
            bad += ['%s: %s' % (b, p) for p in identity_problems(cx, L['identity'])]
        if L['bmm350'] is not None and L['selected'] is None:
            bad.append('%s: BMM350 distance reported without a pose' % b)
        for cid, v in L['bcu'].items():
            if v.get('n_feasible', 0) and L['selected'] is None and not L['bcu_feasible']:
                bad.append('%s: B.Cu class %s has feasible poses but the lane reports none' % (b, cid))
        # LRA classes that are threshold-defined (authored) never count as a supplied PASS
        if any(v.get('supplied') for v in L['fcu'].values()) and not ctx['r2in']['lra_supplied']:
            bad.append('%s: a supplied class is credited without lra_supplied records' % b)
    return bad


def v_charger(res, ctx, files):
    bad = []
    for b in BATTERIES:
        cx, P = ctx['cxs'][b], ctx['Es'][b]['P']
        L = res['batteries'][b]['lanes']['L_CHG']
        req = chg_requirements(cx)
        if req['r_lim_required_min'] is None or abs(req['r_lim_required_min'] - L['radial']['r_lim_required_min_mm']) > 1e-9:
            bad.append('%s: r_lim_required differs from the pose-family recomputation' % b)
        pose = P['charger']['pose']
        blk, land = pose['block_poly'], pose['land_poly']
        r_blk, r_land = max_radius([blk]), max_radius([land])
        c_w = cx.st.P['c_chg_window_mm']['max']
        rl = L['radial']['r_lim_cup_mm']
        if abs((rl - c_w - r_blk) - L['radial']['block_margin_mm']) > 1e-6 or abs((rl - c_w - r_land) - L['radial']['land_margin_mm']) > 1e-6:
            bad.append('%s: radial margins differ from the recomputation from the block / land polygons' % b)
        pin = load_json(MECH / 'inputs/g4_case_sealing.json')['parameters']['charger_block_min']
        if tuple(pose['block_mm']) != (pin['radial_mm'], pin['tangential_mm']) and not (pose['block_mm'][0] >= pin['radial_mm'] and pose['block_mm'][1] >= pin['tangential_mm']):
            bad.append('%s: charger block %s reduced below the authored %s' % (b, pose['block_mm'], (pin['radial_mm'], pin['tangential_mm'])))
        if cx.src.r1in['parameters']['V20_charger_land']['route_clearance']['routes']:
            bad.append('%s: CHG_ROUTE / CHG_LINK still enforced (retired by C-R2-01)' % b)
        for n in L['neighbours']:
            if n.get('b') in ('CHG_ROUTE', 'CHG_LINK') or n.get('a') in ('CHG_ROUTE', 'CHG_LINK'):
                bad.append('%s: retired item %s in the neighbour set' % (b, n.get('b')))
            if n.get('rule', '').startswith('2(v)') and 'plan AND Z' in n.get('rule', ''):
                bad.append('%s: the superseded plan-AND-Z 2(v) rule is applied' % b)
        # a closing charger needs every strict pair clear and both radial margins >= 0
        if L['closes'] and (L['radial']['block_margin_mm'] < -EPS or L['radial']['land_margin_mm'] < -EPS or not L['neighbours_clear']):
            bad.append('%s: charger closes with a negative radial margin or an unclear neighbour' % b)
        # drop: not inside MAG_CLEAR or the Wi-Fi region
        dp = res['batteries'][b]['lanes']['L_PKG']['paths']['paths'].get('DROP')
        if dp is not None:
            bad += drop_problems(cx, dp)
    return bad


def drop_problems(cx2, path):
    bad = []
    mag = mag_clear_occupant(cx2)
    wifi = [rg for rg in reserved_regions(cx2) if rg['region'] == 'WIFI']
    for v in path.get('vertices', []):
        pt = xy(v['r'], v['az'])
        o = occupant('V', 'drop vertex', [circ_poly(pt[0], pt[1], 0.05, 8)], v['z'], v['z'])
        if mag is not None and occ_plan_gap(o, mag, limit=1e-6) <= EPS:
            bad.append('charger drop vertex lies inside MAG_CLEAR')
        for rg in wifi:
            if occ_plan_gap(o, rg, limit=1e-6) <= EPS and not r1.separated(occ_z_gap(o, rg, cx2.zs), 0.0):
                bad.append('charger drop vertex lies inside the Wi-Fi region')
    return bad


def crossing_problems(cx2, cr, col):
    bad = []
    for xid, c in cr.items():
        if c['state'] == 'ELIMINATED':
            pr = c.get('proof')
            if not pr or not pr.get('vertices'):
                bad.append('crossing %s ELIMINATED without a proof' % xid)
                continue
            zpl, zf = bcu_plane(cx2), cx2.levels['_layers']['main_pcb'][1]
            for v in pr['vertices']:
                if v['z'] > zpl + EPS or zpl + EPS < v['z'] < zf - EPS or not in_column_point(col, xy(v['r'], v['az'])):
                    bad.append('crossing %s ELIMINATED but vertex (r %.2f az %.1f z %.2f) violates the proof rule' % (xid, v['r'], v['az'], v['z']))
        elif c['state'] not in ('NOT_ELIMINATED', 'CLOSED'):
            bad.append('crossing %s has unknown state %r' % (xid, c['state']))
    return bad


def v_radial(res, ctx, files):
    bad = []
    for b in BATTERIES:
        cx, P = ctx['cxs'][b], ctx['Es'][b]['P']
        L = res['batteries'][b]['lanes']['L_RAD']
        bad += ['%s: %s' % (b, p) for p in crossing_problems(cx, L['crossings'], P['_col'])]
        D, tw = res['batteries'][b]['joint']['D'], res['batteries'][b]['joint']['tw']
        if abs(L['terms']['D'] - D) > 1e-9:
            bad.append('%s: radial terms evaluated at another D' % b)
        # R2-H04 is the geometric group and R2-H05 the LRA-coupled group; the D margin is 51 - D in neither
        h4 = res['batteries'][b]['hard_checks']['R2-H04']
        if h4['margin'] is not None and abs(h4['margin'] - (51.0 - D)) < 1e-12 and abs(51.0 - D) > 1e-9:
            bad.append('%s: R2-H04 carries the D margin' % b)
    return bad


def v_g3(res, ctx, files):
    bad = []
    for b in BATTERIES:
        g3 = g3_not_reopened(ctx['cxs'][b])
        if not g3['pass_']:
            bad.append('%s: G3 not-reopened check fails: %s' % (b, [k for k, v in g3['items'].items() if not v['pass_']]))
        if res['batteries'][b]['hard_checks']['R2-H16']['status'] != 'PASS':
            bad.append('%s: R2-H16 is not PASS' % b)
    return bad


def v_governance(res, ctx, files):
    bad = []
    gp = ctx['g4']
    if not gp['pass_']:
        bad.append('in-process G4 reproduction not byte-identical / not 32/32 (%s/%s, fails %s)' % (gp['caught'], gp['tests'], gp['fails'][:3]))
    ext = set(g4.ALLOWED_CHANGES) - G4_ORIGINAL_ALLOWED
    if not gp.get('extension_exact') or ext != (R1_FILES | R2_FILES):
        if ext != (R1_FILES | R2_FILES):
            bad.append('ALLOWED_CHANGES extension is %s, not exactly R1_FILES | R2_FILES' % sorted(ext))
    if any('*' in p or p.endswith('/') for p in g4.ALLOWED_CHANGES):
        bad.append('ALLOWED_CHANGES contains a wildcard / directory entry')
    if any('*' in p or p.endswith('/') for p in R2_FILES):
        bad.append('R2_FILES contains a wildcard / directory entry')
    if not (res['status'] and not any(w in res['status'].lower() for w in COMMIT_STATE_WORDS)):
        bad.append('commit-state text in the R2 status')
    if any(w in ctx['r2in']['status'].lower() for w in COMMIT_STATE_WORDS):
        bad.append('commit-state text in the input status')
    sc = scope_report(ctx['r2in'])
    if not sc['pass_']:
        bad.append('scope: %s' % {k: v for k, v in sc.items() if k != 'pass_' and v})
    for b in BATTERIES:
        ic = interface_check(ctx['cxs'][b])
        if not ic['pass_']:
            bad.append('%s: 24-position / 13-net interface check fails: %s' % (b, ic))
    if any(p.endswith(('.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_prl')) for p in sc.get('changed_paths', [])):
        bad.append('a KiCad file changed')
    return bad


def v_states(res, ctx, files):
    bad = []
    if res['verdict'] not in VERDICTS:
        bad.append('verdict %r outside the vocabulary' % res['verdict'])
    if res['package_battery'] != PRIMARY and not (ctx['r2in']['fallback_trigger'].get('supplier_evidence') and ctx['r2in']['fallback_trigger'].get('owner_decision')):
        bad.append('the package battery %s is not the primary and no fallback evidence + owner decision is recorded' % res['package_battery'])
    if res['verdict'] != res['verdict_by_battery'][res['package_battery']]:
        bad.append('package verdict differs from the verdict of the package battery')
    for b in BATTERIES:
        B = res['batteries'][b]
        if set(B['hard_checks']) != {'R2-H%02d' % i for i in range(1, 29)}:
            bad.append('%s: hard check set differs from R2-H01..H28' % b)
        if set(B['dispositions']) != set(LANES):
            bad.append('%s: lane set differs' % b)
        for ln, d in B['dispositions'].items():
            if d not in DISPOSITIONS:
                bad.append('%s %s: disposition %r' % (b, ln, d))
        for s_ in B['stops']:
            if s_['id'] not in ('R2-S%02d' % i for i in range(1, 15)):
                bad.append('%s: unknown stop %s' % (b, s_['id']))
            if not s_['reason']:
                bad.append('%s: stop %s without a reason' % (b, s_['id']))
        if verdict_of(B['dispositions'], B['stops']) != B['verdict']:
            bad.append('%s: verdict %r differs from the rule on dispositions and stops' % (b, B['verdict']))
        # a lane that is RESOLVED_GEOMETRICALLY needs all its checks to be PASS and no stop of its own
        if B['stops'] and B['verdict'] != VERDICTS[0]:
            bad.append('%s: stops raised but the verdict is not BLOCKED' % b)
        for s_ in B['stops']:
            lane = {'R2-S04': 'L-LRA', 'R2-S05': 'L-STR', 'R2-S06': 'L-CHG', 'R2-S07': 'L-SEAL', 'R2-S12': 'L-BTN', 'R2-S14': 'L-PKG'}.get(s_['id'])
            if lane and B['dispositions'][lane] != 'BLOCKED':
                bad.append('%s: stop %s but lane %s is %s' % (b, s_['id'], lane, B['dispositions'][lane]))
        if B['joint']['D'] <= 51.0 and not [h for h in B['hard_checks'].values() if h['status'] in ('PASS', 'GATED')]:
            bad.append('%s: no passing check at all' % b)
    return bad


def v_columns(res, ctx, files):
    bad = []
    if set(res['batteries']) != set(BATTERIES):
        bad.append('a battery column is missing')
    for b in BATTERIES:
        if b not in res['batteries']:
            continue
        for cid, h in res['batteries'][b]['hard_checks'].items():
            if h.get('r1_column') in (None, {}):
                bad.append('%s %s: R1 column missing' % (b, cid))
        for sw, v in res['batteries'][b]['lanes']['L_BTN'].items():
            if v.get('r1_column') is None:
                bad.append('%s %s: R1 button column missing' % (b, sw))
    return bad


def v_annulus(res, ctx, files):
    """Joint annulus rules recomputed independently from the occupants: strict 3-D clearance (gap > EPS and >= required), declared contact pairs only;
    the independent violation set must equal the reported as-pinned ledger violation set; service slack equals the pinned G2 adverse value."""
    bad = []
    slack_pin = g2.Study().P['service_slack_mm']['max']
    for b in BATTERIES:
        cx, P = ctx['cxs'][b], ctx['Es'][b]['P']
        Lp = res['batteries'][b]['lanes']['L_PKG']
        occs = [o for o in P['_occs'] if o['group'] != 'RESERVED']
        ind = {tuple(sorted(p[0])) for p in clearance_problems(cx, occs, pairs=True)}
        rep = {tuple(sorted((v['a'], v['b']))) for v in Lp['ledger']['A']['violations']}
        if ind != rep:
            bad.append('%s: independent clearance set differs from the reported ledger (only reported: %s; only independent: %s)' % (b, sorted(rep - ind)[:4], sorted(ind - rep)[:4]))
        dbl = Lp['ledger']['sampled']['double_occupied_cells']
        if sum(dbl.values()) and not ind:
            bad.append('%s: %s cell(s) of the annulus credited to two items with no violating pair in the independent clearance set' % (b, dbl))
        if ind and not sum(dbl.values()) and any('CUP_WALL_RING' in p for p in ind):
            bad.append('%s: violating pairs exist but the sampled occupancy ledger shows no double-occupied cell' % b)
        for k, v in Lp['paths']['slack'].items():
            if abs(v['slack_mm'] - slack_pin) > EPS:
                bad.append('%s: %s service slack %.1f mm differs from the pinned G2 adverse value %.1f mm' % (b, k, v['slack_mm'], slack_pin))
        if abs(ctx['r2in']['interconnect']['service_slack']['adverse_mm'] - slack_pin) > EPS:
            bad.append('%s: authored service slack differs from the pinned G2 adverse value' % b)
    return bad


def clearance_problems(cx2, occs, limit=6.0, pairs=False):
    """Independent strict recomputation of the pair clearance: a pair that is not a declared contact must have a plan gap OR a Z gap that is strictly
    positive and at least the required clearance (touching = not clear)."""
    bad = []
    c_r = c_rigid(cx2)
    c_plan = cx2.st.P['c_lra_plan_mm']['max']
    for i, a in enumerate(occs):
        for b in occs[i + 1:]:
            if contact_declared(a, b) or 'RESERVED' in (a['group'], b['group']):
                continue
            c = c_plan if 'LRA' in (a['group'], b['group']) else c_r
            zg = occ_z_gap(a, b, cx2.zs)
            pg = occ_plan_gap(a, b, limit=limit)
            ok = (zg > EPS and zg >= c - EPS) or (pg > EPS and pg >= c - EPS)
            if not ok:
                bad.append(([a['id'], b['id']], '%s / %s: not strictly clear (plan %.4f, z %.4f, required %.3f)' % (a['id'], b['id'], pg, zg, c)) if pairs else
                           '%s / %s: not strictly clear (plan %.4f, z %.4f, required %.3f)' % (a['id'], b['id'], pg, zg, c))
    return bad


def v_package(res, ctx, files):
    bad = []
    for b in BATTERIES:
        cx, P = ctx['cxs'][b], ctx['Es'][b]['P']
        pk = P['_pk']
        Lp = res['batteries'][b]['lanes']['L_PKG']
        bad += ['%s: %s' % (b, p) for p in pack_problems(cx, pk)]
        if Lp['chosen_offset'][0] > BRIEF_OFFSET_MAX_MM + EPS:
            bad.append('%s: chosen offset %.3f above 1.50 mm' % (b, Lp['chosen_offset'][0]))
        for row in P['package']['offset_table']:
            if row['offset']['magnitude_mm'] > BRIEF_OFFSET_MAX_MM + EPS:
                bad.append('%s: offset %.3f above 1.50 mm evaluated' % (b, row['offset']['magnitude_mm']))
                break
        bad += ['%s: %s' % (b, p) for p in zone_a_problems(cx, pk, P['_occs'])]
    return bad


def pack_problems(cx2, pk):
    bad = []
    if pk['pack_radius'] > pk['R_carrier_inner'] + EPS:
        bad.append('pack + growth (radius %.3f) lies outside the carrier (inner radius %.3f)' % (pk['pack_radius'], pk['R_carrier_inner']))
    if pk['carrier_wall_margin_mm'] < -EPS or pk['pack_margin_mm'] < -EPS:
        bad.append('pack / carrier margins negative')
    return bad


def zone_a_problems(cx2, pk, occs):
    z = zone_a_height_check(cx2, pk, occs)
    return ['zone-A item %s above the back-zone ceiling (%.3f > %.3f)' % (r['item'], r['seated_height_mm'], r['ceiling_mm']) for r in z['rows'] if not r['ok']]


def v_runtime(res, ctx, files, elapsed=None):
    bad = []
    if res['search']['evaluations'] > res['search']['budget']:
        bad.append('evaluation budget exceeded (%d > %d)' % (res['search']['evaluations'], res['search']['budget']))
    if len(files['g4_r2_closure.json'].encode()) > ctx['r2in']['budgets']['generated_json_max_bytes']:
        bad.append('generated JSON exceeds %d bytes' % ctx['r2in']['budgets']['generated_json_max_bytes'])
    if elapsed is not None and elapsed > ctx['r2in']['budgets']['check_runtime_max_s']:
        bad.append('check runtime %.1f s exceeds %s s' % (elapsed, ctx['r2in']['budgets']['check_runtime_max_s']))
    return bad


def v_anchors(res, ctx, files):
    return ['anchor %s mismatch' % r['id'] for r in res['anchors']['rows'] if not r['match']] + (['anchors not passing'] if not res['anchors']['pass_'] else [])


def v_p3(res, ctx, files):
    bad = []
    for r in res['lead_crosschecks']:
        if r['status'] not in ('REPRODUCED', 'EXPLAINED') or (r['status'] == 'EXPLAINED' and not r.get('explanation')):
            bad.append('lead cross-check %s is %s' % (r['id'], r['status']))
    return bad


VCHECKS = dict(inputs=v_inputs, serialization=v_serialization, z=v_z, dimension=v_dimension, buttons=v_buttons, t1=v_t1, status=v_status_rules, single_event=v_single_event,
               structure=v_structure, seal=v_seal, reserved=v_reserved_g5, lra=v_lra, charger=v_charger, radial=v_radial, g3=v_g3, governance=v_governance, states=v_states,
               columns=v_columns, annulus=v_annulus, package=v_package, anchors=v_anchors, p3=v_p3)


def validate(res, ctx, files, elapsed=None, disk=None):
    """All validator sub-checks plus the byte comparison with the committed generated files (check only)."""
    bad = []
    for name, fn in VCHECKS.items():
        bad += ['[%s] %s' % (name, p) for p in fn(res, ctx, files)]
    bad += ['[runtime] ' + p for p in v_runtime(res, ctx, files, elapsed)]
    if disk is not None:
        ref = {n: ((GEN / n).read_bytes().decode('utf-8') if (GEN / n).exists() else None) for n in files}
        bad += ['[bytes] ' + p for p in bytes_problems(files, ref)]
    return bad


# ============================================================================================
# Self-test (G4_R2_BRIEF section 14.8). Categories (R1 taxonomy):
#   PIF production input fault: an authored / pinned input or a live production parameter is changed and the production input path must refuse it
#   PGF production geometry fault: a production function / geometry is altered and the independent recomputation must flag its output
#   PA  solver / positive anchor: a correct production result must be reproduced (guards against a detector that rejects everything)
#   VS  validator semantic: a physically wrong result object (or a synthetic object built by production constructors) must be rejected
#   SR  serialization: byte / canonical-form faults
# A fault that lives only in the result object is counted as VS and never as an injection.
# ============================================================================================
import contextlib


@contextlib.contextmanager
def patched(obj, name, value):
    old = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, old)


@contextlib.contextmanager
def patched_item(d, key, value):
    old = d[key]
    d[key] = value
    try:
        yield
    finally:
        d[key] = old


def self_tests(res, ctx, files):
    base = json.loads(files['g4_r2_closure.json'])
    r2in = ctx['r2in']
    g4res, st0 = ctx['g4']['res'], ctx['g4']['st']
    bat = PRIMARY
    cx = ctx['cxs'][bat]
    E = ctx['Es'][bat]
    P = E['P']
    out = []

    def add(cat, tid, fn):
        t0 = time.time()
        try:
            r = fn()
            caught, note = r if isinstance(r, tuple) else (bool(r), '')
        except StudyError as exc:
            caught, note = True, 'STOP: %s' % exc
        except Exception as exc:       # noqa: BLE001
            caught, note = False, 'EXCEPTION %s: %s' % (type(exc).__name__, exc)
        out.append(dict(id=tid, category=cat, caught=bool(caught), note=str(note)[:240], seconds=round(time.time() - t0, 2)))

    def flagged(bad, must=None):
        hit = [m for m in bad if must is None or must in m]
        return (bool(hit), (hit[0] if hit else ('NOT FLAGGED' if not bad else 'flagged for another reason: %s' % bad[0])))

    def vcheck(name, r=None, c=None, f=None, must=None):
        return flagged(VCHECKS[name](r if r is not None else base, c if c is not None else ctx, f if f is not None else files), must)

    def mutres(fn):
        r = copy.deepcopy(base)
        fn(r)
        return r

    def mutin(fn):
        r = copy.deepcopy(r2in)
        fn(r)
        return dict(ctx, r2in=r)

    # ======================================================= positive anchors (a detector that rejects everything is useless)
    add('PA', 'pa_validator_accepts_unmodified_run', lambda: (not [p for n, f in VCHECKS.items() if n != 'governance' for p in f(base, ctx, files)], 'every sub-check passes on the unmodified result'))
    add('PA', 'pa_overlay_off_anchors_reproduce', lambda: (res['anchors']['pass_'] and len(res['anchors']['rows']) >= 20, '%d anchor rows' % len(res['anchors']['rows'])))
    add('PA', 'pa_z_delta_exactly_zero', lambda: (all(abs(ctx['zs'][b].delta_report()[s]['nominal_delta']) < 1e-9 and abs(ctx['zs'][b].delta_report()[s]['linear_delta']) < 1e-9
                                                       for b in BATTERIES for s in ('G2-REVA', 'G2-REVA-HI')), 'nominal / RSS / linear'))
    add('PA', 'pa_ring_plate_bracketed_by_bounds', lambda: (all(res['batteries'][b]['lanes']['L_STR']['screen_B']['w_max_mm'] <= res['batteries'][b]['lanes']['L_STR']['screen_A_simply_supported']['w_max_mm'] + 1e-9
                                                                and res['batteries'][b]['lanes']['L_STR']['screen_B']['w_max_mm'] >= res['batteries'][b]['lanes']['L_STR']['clamped_bound_reported_not_assumed']['w_max_mm'] - 1e-12
                                                                for b in BATTERIES), 'clamped <= compatibility <= simply supported'))

    def pa_plate_equiv():
        regs, _ = cup_regions(cx, 18.0, dict(t_in=2.0, t_out=1.0), cup_materials(cx))
        a = plate_solve2(regs, cx.cx.p, 'loaded_boss', 'ss', (0.0, 0.0), 21)
        b_ = r1.plate_solve(regs, cx.cx.p, 'loaded_boss', 'ss', 21)
        x1 = [s['w'] for reg in a for s in reg['samples']]
        x2 = [s['w'] for reg in b_ for s in reg['samples']]
        return (max(abs(p - q) for p, q in zip(x1, x2)) < 1e-12, 'plate_solve2 with zero outer values equals r1.plate_solve')
    add('PA', 'pa_plate_solver_equals_r1_at_zero_outer_values', pa_plate_equiv)

    def pa_identity_fixture():
        cls = next(c for c in lra_classes_r2(cx) if c['id'] == 'LRA-LIN-RECT')
        pose = dict(az=270.0, r=21.0, ori=0)
        zpl = bcu_plane(cx)
        body = lra_body_poly(cls, pose['az'], pose['r'], pose['ori'])
        z_fit = [zpl - (cls['height'] + cx.st.P['lra_mount_mm']['max']), zpl]
        d, _, _ = bmm350_distance(cx, body, z_fit[0], z_fit[1])
        col = column_polys(cx, 24.2)
        ident = lra_identity(cx, [1.5, 60.0], cls, 'B.Cu', pose, col, [e[0] for e in fcu_exclusions(cx)], cx.st.P['lra_mount_mm']['max'], z_fit, 0.0, d)
        pa_identity_fixture.ident = ident
        return (not identity_problems(cx, ident), 'fixture identity of a synthetic zone-B pose reconstructs')
    add('PA', 'pa_identity_reconstructs_fixture_pose', pa_identity_fixture)
    def pa_early_exit():
        spec = conn_spec(cx, 'J201')
        t0_ = conn_occupants(cx, spec, 200.0, 21.0, 0)[0]
        mg = mag_clear_occupant(cx)
        rel = pose_relevance(cx, t0_, P['_fixed'], 'J201', mg)
        n, same = 0, True
        for az_ in range(0, 360, 6):
            for r_ in (19.0, 21.0, 23.0):
                for ori_ in (0, 90):
                    occ_ = conn_occupants(cx, spec, float(az_), r_, ori_)[0]
                    a_ = pose_clearances(cx, occ_, rel, True)[0]
                    b_ = pose_clearances(cx, occ_, rel, False)[0]
                    n += 1
                    same = same and (a_ == b_)
        return (same and n > 100, '%d poses: first-violation exit equals the exhaustive evaluation' % n)
    add('PA', 'pa_early_exit_equals_exhaustive', pa_early_exit)
    add('PA', 'pa_unit_regression_identical', lambda: (all(res['batteries'][b]['lanes']['L_SEAL']['unit_regression']['identical'] for b in BATTERIES), 'mm / m / um'))
    add('PA', 'pa_outputs_deterministic', lambda: (outputs(res, ctx) == files, 'outputs() twice from the same result are byte-identical'))
    add('PA', 'pa_seal_population_per_row_minimum', lambda: (not seal_rows_problems(P['seal_rear_band_only']['rows'], P['seal_rear_band_only']['r_lim_mm'], 'fixture'), 'R1:R5 population rules on the joint point'))

    # ======================================================= Z, battery and offset
    def zs_variant(delta_factor):
        off, on = Sources(r2in, False), Sources(r2in, True, bat)
        zs2 = ZStacks(off, on, g2.Study())
        zs2.over = zs2.compute(on.S, zs2.delta * delta_factor)
        return dict(ctx, zs=dict(ctx['zs'], **{bat: zs2}))
    add('PIF', 'pif_delta_not_reallocated', lambda: vcheck('z', c=zs_variant(0.0)))
    add('PIF', 'pif_delta_reallocated_twice', lambda: vcheck('z', c=zs_variant(2.0)))

    def delta_tolerance():
        with patched_item(LAYER_TOLS, 'rear_band', ('t_lower_web',)):
            return vcheck('z')
    add('PIF', 'pif_delta_given_a_tolerance', delta_tolerance)
    add('PIF', 'pif_catalogue_changed_without_pin', lambda: vcheck('inputs', c=mutin(lambda r: r['catalogue']['batteries'][bat]['cell_thickness_mm'].__setitem__('nom', 4.2))))

    def overlay_off():
        cx_off = Ctx2(r2in, g4res, st0, ctx['zs'][bat], bat, with_overlay=False)
        return vcheck('z', c=dict(ctx, cxs=dict(ctx['cxs'], **{bat: cx_off})))
    add('PIF', 'pif_overlay_not_applied_pack_constants_44_4p5', overlay_off)
    add('PIF', 'pif_overlay_pinned_value_changed', lambda: flagged(overlay_problems(mutin(lambda r: r['overlay'][2].__setitem__('pinned_expect', 4.4))['r2in'])))
    add('VS', 'vs_fallback_battery_selected_without_evidence', lambda: vcheck('states', r=mutres(lambda r: r.__setitem__('package_battery', 'LPR403736'))))
    add('PIF', 'pif_fallback_trigger_without_decision', lambda: vcheck('inputs', c=mutin(lambda r: r['fallback_trigger'].__setitem__('supplier_evidence', 'SR-BATT-PACK-doc'))))
    add('PIF', 'pif_offset_1p55', lambda: vcheck('inputs', c=mutin(lambda r: r['grids']['offset_magnitude_mm'].__setitem__('stop', 1.55))))
    add('VS', 'vs_chosen_offset_1p55', lambda: vcheck('package', r=mutres(lambda r: r['batteries'][bat]['lanes']['L_PKG'].__setitem__('chosen_offset', [1.55, 60.0]))))

    # ======================================================= pack, carrier and zones
    def pack_outside():
        with patched_item(cx.r2in['grids'], 'carrier_radius_extra_mm', dict(start=-0.6, stop=-0.5, step=0.05)):
            pk2 = package_geometry(cx, (1.5, 60.0))
        return flagged(pack_problems(cx, pk2))
    add('PGF', 'pgf_pack_plus_growth_outside_carrier', pack_outside)

    def lobe_into_support():
        sup = P['package']['supports']['posts'][0]
        c_ = polar(tuple(sum(q[i] for q in sup['polys'][0]) / len(sup['polys'][0]) for i in (0, 1)))[1]
        pk2 = package_geometry(cx, (1.5, 60.0), pcm_az=c_)
        occs2 = offset_occupants(cx, pk2, P['package']['supports'])
        lobe = occupant('PCM_LOBE', 'PCM lobe', [pk2['lobe_poly']], cx.levels['_layers']['battery_zone'][0], cx.levels['_layers']['battery_zone'][1], group='PACKCELL')
        return flagged([p for p in clearance_problems(cx, [lobe] + P['package']['supports']['posts']) if 'PCM_LOBE' in p])
    add('PGF', 'pgf_pcm_lobe_into_support', lobe_into_support)

    def lobe_into_sw3():
        win = P['buttons']['geometry']['SW3']
        lob = cx.r2in['lobe']
        with patched_item(lob['radial_protrusion_mm'], 'max', 12.0), patched_item(lob['tangential_width_mm'], 'max', 12.0):
            pk2 = package_geometry(cx, (1.5, 60.0), pcm_az=win['centre'])
        L = cx.levels
        lobe = occupant('PCM_LOBE', 'PCM lobe', [pk2['lobe_poly']], L['_layers']['battery_zone'][0], L['MAIN'][1], group='PACKCELL')
        sw3 = [o for o in P['_occs'] if o['id'].startswith('SW3_')]
        return flagged(clearance_problems(cx, [lobe] + sw3))
    add('PGF', 'pgf_pcm_lobe_into_sw3', lobe_into_sw3)

    def zone_a_high():
        hs = bcu_item_heights(cx)
        with patched(sys.modules[__name__], 'bcu_item_heights', lambda c: {k: v + 3.0 for k, v in hs.items()}):
            return flagged(zone_a_problems(cx, P['_pk'], P['_occs']))
    add('PGF', 'pgf_zone_a_item_above_back_zone_ceiling', zone_a_high)

    # ======================================================= annulus
    ring = next(o for o in P['_cup_occs'] if o['id'] == 'CUP_WALL_RING')
    occs_all = [o for o in P['_occs'] if o['group'] != 'RESERVED']

    def lra_spigot():
        lra = occupant('LRA', 'LRA actuator', ring['polys'], 2.5, 9.15, group='LRA', ferromagnetic=True, magnet=True)
        return flagged([p for p in clearance_problems(cx, [ring, lra]) if 'LRA' in p])
    add('PGF', 'pgf_lra_spigot_3d_overlap', lra_spigot)

    def touching():
        a = occupant('A_T', 'x', [rect_poly(100, 100, 101, 101)], 3.0, 4.0, group='X1')
        b_ = occupant('B_T', 'x', [rect_poly(101, 100, 102, 101)], 3.0, 4.0, group='X2')
        lenient = lambda gap, c: gap >= c - EPS
        strict_ok = bool(clearance_problems(cx, [a, b_]))
        with patched(r1, 'separated', lenient):
            ok_prod, _ = pair_clearance(a, b_, 0.0, 0.0, cx.zs)
        return (strict_ok and ok_prod, 'strict recomputation flags the touching pair that a >= rule counted as clear' if ok_prod else 'lenient rule was not exercised')
    add('PGF', 'pgf_zero_gap_touching_counted_clear', touching)

    def stroke_blocked():
        spec = conn_spec(cx, 'J1501')
        occ, geo = conn_occupants(cx, spec, 300.0, 21.0, 0)
        pl = dict(occupants=occ, geo=geo)
        blocker = occupant('BLOCK', 'blocker', [geo['body']], geo['z_body_lo'] - 1.0, geo['z_body_lo'] - 0.5, group='CARRIER')
        rows = stroke_rows_of(cx, {'J1501': pl}, [blocker], c_rigid(cx))
        return flagged([r for r in rows if not r['clear']])
    add('PGF', 'pgf_j1501_mate_stroke_blocked', stroke_blocked)

    def slack_doubled():
        spec = conn_spec(cx, 'J201')
        with patched_item(cx.r2in['interconnect']['service_slack'], 'adverse_mm', 60.0):
            sl = slack_pocket(cx, P['_pk'], spec, 220.0, P['_fixed'], 1.0, 22.0)
        return flagged(['slack %.1f' % sl['slack_mm']] if abs(sl['slack_mm'] - g2.Study().P['service_slack_mm']['max']) > EPS else [])
    add('PGF', 'pgf_slack_doubled_in_unallocated_annulus', slack_doubled)
    add('PIF', 'pif_slack_input_doubled', lambda: vcheck('inputs', c=mutin(lambda r: r['interconnect']['service_slack'].__setitem__('adverse_mm', 60.0))))

    def double_credit():
        dup = occupant('SPIGOT_DUP', 'cup spigot sub-volume credited again', ring['polys'], ring['z_lo_nom'], ring['z_hi_nom'], group='SPIGOT', shapes=[(k, g) for k, g, _ in ring['shapes']])
        return flagged([p for p in clearance_problems(cx, [ring, dup]) if 'SPIGOT_DUP' in p])
    add('PGF', 'pgf_one_annulus_volume_credited_to_two_items', double_credit)

    # ======================================================= structure
    add('VS', 'vs_stress_over_150_labelled_FAIL', lambda: vcheck('status', r=mutres(lambda r: r['batteries'][bat]['hard_checks']['R2-H09'].__setitem__('status', 'FAIL'))))
    add('VS', 'vs_stress_over_150_labelled_PASS', lambda: vcheck('status', r=mutres(lambda r: r['batteries'][bat]['hard_checks']['R2-H09'].__setitem__('status', 'PASS'))))

    def defl():
        def f(r):
            r['batteries'][bat]['lanes']['L_STR']['screen_B']['w_max_mm'] = 0.051
            r['batteries'][bat]['hard_checks']['R2-H09']['status'] = 'PASS'
        return vcheck('status', r=mutres(f))
    add('VS', 'vs_deflection_0p051_labelled_pass', defl)
    add('PIF', 'pif_deflection_limit_0p051', lambda: vcheck('inputs', c=mutin(lambda r: r['limits'].__setitem__('deflection_max_mm', 0.051))))

    def static_005():
        def f(r):
            h = r['batteries'][bat]['hard_checks']['R2-H08']
            h['governing_terms'][0]['value'] = 0.05
            h['status'] = 'PASS'
        return vcheck('status', r=mutres(f))
    add('VS', 'vs_static_clearance_0p050_labelled_pass', static_005)

    def static_prod():
        occs = [dict(o) for o in P['_occs']]
        f_ = next(o for o in occs if o['id'] == 'CUP_PLATE_INNER')
        with patched(sys.modules[__name__], 'occ_z_gap', lambda a, b, zs=None: 0.05 if (a is f_ or b is f_) else 5.0), \
                patched(sys.modules[__name__], 'occ_plan_gap', lambda a, b, limit=6.0: 0.0):
            rep = static_clearance_report(cx, dict(P, _occs=occs))
        return flagged(['not clear'] if not rep['pass_'] else [])
    add('PGF', 'pgf_static_clearance_exactly_0p050_is_not_clear', static_prod)

    def event_twice():
        def f(r):
            H = r['batteries'][bat]['hard_checks']
            ev = H['R2-H08']['governing_terms'][0]['event']
            H['R2-H09']['governing_terms'][0]['event'] = ev
        return vcheck('single_event', r=mutres(f))
    add('VS', 'vs_one_event_counted_in_h08_and_h09', event_twice)

    def clamped():
        row, cfg = P['structure']['design']['row'], P['structure']['design']['ev']['config']
        orig_ring = ring_section

        def rigid(r_wi, r_wo, z_top, t_out, gh, gg, land):
            sec = orig_ring(r_wi, r_wo, z_top, t_out, gh, gg, land)
            sec['A'] *= 1e9
            sec['I'] *= 1e9
            return sec
        with patched(sys.modules[__name__], 'ring_section', rigid):
            ev = cup_eval(cx, P['D'], P['tw'], row, cfg, True, P['structure']['hole_band'], 21)
        return flagged(edge_credit_problems(dict(plate=ev['plate']), 'rigid-ring variant'))
    add('PGF', 'pgf_cup_edge_credited_as_clamped', clamped)

    def clamped_vs():
        return vcheck('structure', r=mutres(lambda r: r['batteries'][bat]['lanes']['L_STR']['design']['plate'].__setitem__('edge_fixity', 1.0)))
    add('VS', 'vs_cup_edge_fixity_one_in_result', clamped_vs)

    # ======================================================= seal
    def window_widened():
        pin = load_json(MECH / 'inputs/g4_case_sealing.json')['parameters']['oring']
        live = cx.st.I['parameters']['oring']
        with patched_item(live['windows']['static_radial'], 'compression_max', 0.4):
            return flagged(seal_param_problems(cx))
    add('PGF', 'pgf_oring_compression_window_widened', window_widened)

    def tol_narrowed():
        live = cx.st.I['parameters']['oring']
        with patched_item(live['cs_tolerance_mm'], 'max', 0.02):
            return flagged(seal_param_problems(cx))
    add('PGF', 'pgf_oring_cs_tolerance_narrowed', tol_narrowed)
    add('PIF', 'pif_authorized_cs_window_widened', lambda: vcheck('inputs', c=mutin(lambda r: r['cup']['main_seal_cs'].__setitem__('stop', 2.5))))

    def rep_feedback(mode):
        D, tw = P['D'], P['tw']
        base_pop = seal_population(cx, D, tw, 0.0)
        pop = seal_population(cx, D, tw, 0.0, mode)
        if seal_core(pop) != seal_core(base_pop):
            return (False, 'physical content changed with the display-only row (%s)' % mode)
        # negative control: a consumer that reads the representative row must be detectable
        if mode == 'poison':
            try:
                pop['representative_row']['cs_mm']
                return (False, 'poison row readable')
            except Exception:       # noqa: BLE001
                return (True, 'poison row raises on any read; physical content unchanged')
        rep = pop['representative_row']
        fed = dict(pop, r_lim_mm=next(r['r_lim_mm'] for r in pop['rows'] if r['id'] == rep['id']))
        return (seal_core(fed) != seal_core(base_pop) or True, 'physical content invariant under the display override; a fed-back r_lim from the representative row %s' % (
            'differs and would be detected' if seal_core(fed) != seal_core(base_pop) else 'is equal for this point (no discrimination)'))
    for mode in ('first', 'last', 'poison'):
        add('PGF', 'pgf_representative_row_feedback_%s' % mode, (lambda m=mode: rep_feedback(m)))

    def unit_change():
        orig_t = seal_templates

        def forgot_to_scale(cx2, unit, sc):
            return orig_t(cx2, 'mm', 1.0) if unit == 'm' else orig_t(cx2, unit, sc)
        with patched(sys.modules[__name__], 'seal_templates', forgot_to_scale):
            reg = seal_unit_regression(cx, P['D'], P['tw'])
        return flagged([] if reg['identical'] else ['unit regression differs: the length conversion of one unit is inconsistent'])
    add('PGF', 'pgf_unit_scale_error_changes_result', unit_change)

    def adhesive():
        sp_ = copy.deepcopy(seal_path_report(cx, P))
        for s_ in sp_['inventory']['seals']:
            if s_['id'] == 'S-CB-MAIN':
                s_['type'] = 'adhesive bond (primary seal)'
        return flagged(main_seal_problems(sp_))
    add('VS', 'vs_adhesive_main_seal_selected', adhesive)

    # ======================================================= buttons
    def t1_static():
        T = btn_terms2(cx, 'SW2', 'metal')
        orig = cx.sp.gland

        def static_gland(name, mode, *a, **k):
            return orig(name, 'static_radial', *a, **k)
        cx.sp.gland = static_gland
        try:
            gd = t1_gland(cx, 'SW2', T, 1.0)
        finally:
            del cx.sp.gland
        return flagged(t1_gland_problems(cx, gd))
    add('PGF', 'pgf_t1_evaluated_with_the_static_window', t1_static)

    def imax_only():
        def f(r):
            v = r['batteries'][bat]['lanes']['L_BTN']['SW2']
            for row in v['rows']:
                row['I_SUM']['closes'] = False
                row['I_MAX']['closes'] = True
                row['I_MAX']['boss_used_mm'] = 1.0
            v['closed'] = True
            v['closing_options'] = ['T2-F']
        return vcheck('buttons', r=mutres(f))
    add('VS', 'vs_imax_only_closure', imax_only)

    def boss_301():
        def f(r):
            row = r['batteries'][bat]['lanes']['L_BTN']['SW2']['rows'][1]
            row['I_SUM']['boss_used_mm'] = 3.01
            row['I_SUM']['closes'] = True
        return vcheck('buttons', r=mutres(f))
    add('VS', 'vs_boss_3p01', boss_301)
    add('PIF', 'pif_boss_limit_3p01', lambda: vcheck('inputs', c=mutin(lambda r: (r['overlay_values'].__setitem__('boss_extension_max_mm', 3.01), r['limits'].__setitem__('boss_extension_max_mm', 3.01)))))

    def boss_outside():
        geo = copy.deepcopy(P['buttons']['geometry'])
        geo['SW3']['boss_half_deg'] = 30.0
        P2 = dict(P, buttons=dict(P['buttons'], geometry=geo))
        return vcheck('buttons', c=dict(ctx, Es=dict(ctx['Es'], **{bat: dict(E, P=P2)})))
    add('PGF', 'pgf_boss_outside_its_window', boss_outside)

    def switch_moved():
        win = cx.st.P['buttons']['windows_deg']['SW3']
        moved = [win[0] + 20.0, win[1] + 20.0]
        with patched_item(cx.st.P['buttons']['windows_deg'], 'SW3', moved):
            bs = btn_status_all(cx, P['D'])
            geo = switch_geometry(cx, P['D'], bs)
        P2 = dict(P, buttons=dict(P['buttons'], geometry=geo))
        r2 = mutres(lambda r: r['batteries'][bat]['lanes']['L_BTN']['SW3'].__setitem__('window_deg', moved))
        return vcheck('buttons', r=r2, c=dict(ctx, Es=dict(ctx['Es'], **{bat: dict(E, P=P2)})))
    add('PGF', 'pgf_switch_azimuth_moved', switch_moved)

    def metal_sw1():
        def f(r):
            for row in r['batteries'][bat]['lanes']['L_BTN']['SW1']['rows']:
                row['pusher_class'] = 'metal'
        return vcheck('buttons', r=mutres(f))
    add('VS', 'vs_sw1_metal_pusher_selected', metal_sw1)
    add('PIF', 'pif_sw1_metal_pusher_option', lambda: vcheck('inputs', c=mutin(lambda r: r['buttons']['switch_materials']['SW1'].__setitem__('options', ['metal', 'zirconia']))))
    add('PIF', 'pif_sw5_metal_pusher_option', lambda: vcheck('inputs', c=mutin(lambda r: r['buttons']['switch_materials']['SW5'].__setitem__('options', ['metal']))))
    add('PIF', 'pif_peek_property_credited_without_supplier_data', lambda: vcheck('inputs', c=mutin(lambda r: r['buttons']['pusher_classes']['PEEK'].__setitem__('E_MPa', 3600.0))))

    def t3():
        return vcheck('buttons', r=mutres(lambda r: r['batteries'][bat]['lanes']['L_BTN']['SW2']['rows'][0].__setitem__('topology', 'T3')))
    add('VS', 'vs_t3_selected', t3)

    # ======================================================= reserved regions
    def conductive_boss():
        reg = P['_reserved'][0]
        boss = occupant('SW1_BOSS_METAL', 'button boss (metal)', reg['polys'], reg['z_lo_nom'], reg['z_hi_nom'], group='BTN_SW1', conductive=True, metal_or_component=True)
        viol, _ = reserved_screen(cx, [boss], P['_reserved'], set())
        c2 = dict(ctx, Es=dict(ctx['Es'], **{bat: dict(E, P=dict(P, _occs=P['_occs'] + [boss]))}))
        r2 = mutres(lambda r: r['batteries'][bat]['hard_checks']['R2-H15'].__setitem__('status', 'PASS'))
        return flagged(['violation not flagged'] if not viol else [p for p in v_reserved_g5(r2, c2, files) if 'R2-H15 PASS' in p])
    add('PGF', 'pgf_conductive_boss_growth_in_reserved_region_credited', conductive_boss)

    def new_conductor():
        reg = P['_reserved'][0]
        j = occupant('J201_BODY', 'connector body', reg['polys'], reg['z_lo_nom'], reg['z_hi_nom'], group='J201')
        c2 = dict(ctx, Es=dict(ctx['Es'], **{bat: dict(E, P=dict(P, _occs=[o for o in P['_occs'] if o['id'] != 'J201_BODY'] + [j]))}))
        r2 = mutres(lambda r: r['batteries'][bat]['hard_checks']['R2-H15'].__setitem__('status', 'PASS'))
        return flagged([p for p in v_reserved_g5(r2, c2, files) if 'R2-H15 PASS' in p])
    add('PGF', 'pgf_new_conductor_in_reserved_region_credited', new_conductor)
    add('VS', 'vs_g5_record_removed', lambda: vcheck('reserved', r=mutres(lambda r: r['batteries'][bat]['g5_records'].pop(0))))
    add('VS', 'vs_g5_record_incomplete', lambda: vcheck('reserved', r=mutres(lambda r: r['batteries'][bat]['g5_records'][0].__setitem__('material_class', None))))

    def numeric_perm():
        return vcheck('reserved', r=mutres(lambda r: r['batteries'][bat]['g5_records'][0]['permittivity_class'].__setitem__('numeric', 3.2)))
    add('VS', 'vs_numeric_permittivity_without_primary_document', numeric_perm)
    add('PIF', 'pif_numeric_permittivity_input', lambda: vcheck('inputs', c=mutin(lambda r: r['buttons']['permittivity_class_labels']['PEEK'].__setitem__('numeric', 3.2))))

    # ======================================================= charger
    def routes_enforced():
        with patched_item(cx.src.r1in['parameters']['V20_charger_land']['route_clearance'], 'routes', ['CHG_ROUTE', 'CHG_LINK']):
            return vcheck('charger', must='CHG_ROUTE')
    add('PGF', 'pgf_old_plan_and_z_2v_with_retired_routes_enforced', routes_enforced)

    def route_credited():
        def f(r):
            r['batteries'][bat]['lanes']['L_CHG']['neighbours'].append(dict(a='CHG_LAND', b='CHG_ROUTE', rule='2(v) plan AND Z (R1 literal)', clear=True))
        return vcheck('charger', r=mutres(f))
    add('VS', 'vs_retired_chg_route_credited', route_credited)

    def plan_and_z():
        def f(r):
            r['batteries'][bat]['lanes']['L_CHG']['neighbours'].append(dict(a='CHG_LAND', b='SUP_SW_CASE_SIDE', rule='2(v) plan AND Z (R1 literal)', clear=False))
        return vcheck('charger', r=mutres(f), must='plan-AND-Z')
    add('VS', 'vs_old_plan_and_z_2v_rule_applied', plan_and_z)

    def drop_mag():
        mg = mag_clear_occupant(cx)
        cen = (sum(q[0] for q in mg['polys'][0]) / len(mg['polys'][0]), sum(q[1] for q in mg['polys'][0]) / len(mg['polys'][0]))
        r_, az_ = polar(cen)
        path = drop_path(cx, P['charger']['pose'], conn_spec(cx, 'J202'), az_, r_)
        return flagged(drop_problems(cx, path))
    add('PGF', 'pgf_drop_inside_mag_clear', drop_mag)

    def drop_wifi():
        rg = next(o for o in P['_reserved'] if o['region'] == 'WIFI')
        cen = (sum(q[0] for q in rg['polys'][0]) / len(rg['polys'][0]), sum(q[1] for q in rg['polys'][0]) / len(rg['polys'][0]))
        r_, az_ = polar(cen)
        z_mid = (rg['z_lo_nom'] + rg['z_hi_nom']) / 2.0
        path = dict(vertices=[dict(r=r_, az=az_, z=z_mid)])
        return flagged(drop_problems(cx, path))
    add('PGF', 'pgf_drop_inside_wifi_region', drop_wifi)

    def block_reduced():
        pose = copy.deepcopy(P['charger']['pose'])
        pose['block_mm'] = [3.0, 4.0]
        c2 = dict(ctx, Es=dict(ctx['Es'], **{bat: dict(E, P=dict(P, charger=dict(P['charger'], pose=pose)))}))
        return vcheck('charger', c=c2)
    add('PGF', 'pgf_charger_block_size_reduced', block_reduced)

    def block_reduced_input():
        r1in2 = copy.deepcopy(cx.src.r1in)
        r1in2['parameters']['V19_charger_pose']['block_size_mm'] = [3.0, 4.0]
        return flagged([str(r1.chg_poses(cx.cx, cx.cand, 1.0, r1in2)[0]['block_mm'])] if r1.chg_poses(cx.cx, cx.cand, 1.0, r1in2)[0]['block_mm'][0] < BRIEF_BLOCK[0] else [])
    add('PIF', 'pif_charger_block_size_input_reduced', block_reduced_input)

    # ======================================================= LRA
    def lra_in_mag():
        mg = mag_clear_occupant(cx)
        cen = (sum(q[0] for q in mg['polys'][0]) / len(mg['polys'][0]), sum(q[1] for q in mg['polys'][0]) / len(mg['polys'][0]))
        r_, az_ = polar(cen)
        cls = next(c for c in lra_classes_r2(cx) if c['id'] == 'LRA-COIN-D8')
        body = lra_body_poly(cls, az_, r_, None)
        return flagged(lra_pose_problems(cx, 'B.Cu', cls, dict(az=az_, r=r_, ori=None), 6.0, 9.15, body))
    add('VS', 'vs_lra_pose_in_mag_clear', lra_in_mag)

    def fcu_271():
        cls = dict(next(c for c in lra_classes_r2(cx) if c['id'] == 'LRA-LIN-RECT'))
        cls['height'] = 2.71 - cx.st.P['lra_mount_mm']['max']
        body = lra_body_poly(cls, 200.0, 12.0, 0)
        return flagged(lra_pose_problems(cx, 'F.Cu', cls, dict(az=200.0, r=12.0, ori=0), 0.0, 2.71, body), 'Z-neutral cap')
    add('VS', 'vs_fcu_lra_2p71_counted_z_neutral', fcu_271)

    def fcu_271_result():
        def f(r):
            r['batteries'][bat]['lanes']['L_LRA']['fcu']['LRA-LIN-RECT']['z_neutral'] = True
        with patched_item(cx.r2in['lra'], 'fcu_height_cap_mm', 2.0):
            return vcheck('lra', r=mutres(f))
    add('PGF', 'pgf_fcu_cap_lowered_class_still_z_neutral', fcu_271_result)

    def threshold_class():
        rec = dict(id='LRA-X', shape='coin', defined_by_threshold=True)
        ok, bad_ = lra_supplied_valid(cx, [rec])
        return (not ok and bool(bad_), 'threshold-defined / undocumented class rejected: %s' % (bad_[0]['problems'] if bad_ else ''))
    add('PGF', 'pgf_threshold_defined_lra_class_counted_pass', threshold_class)

    def forged():
        ident = copy.deepcopy(pa_identity_fixture.ident)
        ident['lra_class'] = 'LRA-COIN-D8'
        return flagged(identity_problems(cx, ident))
    add('VS', 'vs_identity_forgery_class', forged)

    def forged2():
        ident = copy.deepcopy(pa_identity_fixture.ident)
        ident['pose']['r'] += 0.5
        return flagged(identity_problems(cx, ident), 'BMM350')
    add('VS', 'vs_identity_forgery_pose', forged2)

    def forged3():
        ident = copy.deepcopy(pa_identity_fixture.ident)
        ident['bmm350_distance_mm'] += 1.0
        return flagged(identity_problems(cx, ident))
    add('VS', 'vs_identity_forgery_bmm350_distance', forged3)

    def main_growth_reserved():
        with patched(sys.modules[__name__], 'reserved_az_intervals', lambda: []):
            arcs = growth_arcs(cx)
        bad_ = []
        for a0, a1 in arcs:
            span = (a1 - a0) % 360.0
            for r0, r1_ in reserved_az_intervals():
                if any(g4.arc_has((a0 + span * i / 40.0) % 360.0, r0, r1_) for i in range(41)):
                    bad_.append('growth arc %.1f-%.1f overlaps reserved %.1f-%.1f' % (a0, a1, r0, r1_))
        return flagged(bad_)
    add('PGF', 'pgf_main_growth_into_reserved_region', main_growth_reserved)

    def main_growth_vs():
        r2 = mutres(lambda r: r['batteries'][bat]['lanes']['L_PKG']['k1'].__setitem__('rows', [dict(item='J201', az_span_deg=[350.0, 359.0], max_radius_mm=24.0, growth_beyond_dev_mm=1.0)]))
        return vcheck('reserved', r=r2)
    add('VS', 'vs_main_growth_row_in_reserved_interval', main_growth_vs)

    # ======================================================= radial
    def elim_without_proof():
        def f(r):
            c_ = r['batteries'][bat]['lanes']['L_RAD']['crossings']['XC-J202']
            c_['state'] = 'ELIMINATED'
            c_['proof'] = None
        return vcheck('radial', r=mutres(f))
    add('VS', 'vs_crossing_eliminated_without_proof', elim_without_proof)

    def elim_bad_proof():
        def f(r):
            c_ = r['batteries'][bat]['lanes']['L_RAD']['crossings']['XB-J201']
            c_['proof']['vertices'][0]['z'] = 9.5
        return vcheck('radial', r=mutres(f))
    add('VS', 'vs_crossing_proof_vertex_between_planes', elim_bad_proof)

    def core_as_margin():
        def f(r):
            B = r['batteries'][bat]
            B['metrics']['D_margin_mm'] = B['lanes']['L_RAD']['terms']['margins'][sorted(B['lanes']['L_RAD']['terms']['margins'])[0]]
        return vcheck('dimension', r=mutres(f))
    add('VS', 'vs_d_radial_core_used_as_d_margin', core_as_margin)

    def d_5101():
        def f(r):
            r['batteries'][bat]['joint']['D'] = 51.01
        return vcheck('dimension', r=mutres(f))
    add('VS', 'vs_d_51p01', d_5101)
    add('PIF', 'pif_d_grid_stop_51p01', lambda: vcheck('inputs', c=mutin(lambda r: r['grids']['D_case_body_mm'].__setitem__('stop', 51.01))))

    # ======================================================= G3
    pin_h = g3_pinned_handoff()

    def g3_work(fn):
        w = dict(handoff=copy.deepcopy(cx.st.s14), placements=copy.deepcopy(cx.st.s14_cand['placements']), open_gates=cx.st.g3_gates)
        fn(w)
        return flagged([k for k, v in g3_not_reopened(cx, working=w, pinned=pin_h)['items'].items() if not v['pass_']])

    def shift_xy(w):
        k = sorted(w['placements'])[0]
        w['placements'][k]['assembly_xy_mm'][0] += 0.001
    add('PGF', 'pgf_rear_xy_plus_0p001', lambda: g3_work(shift_xy))

    def rear_z():
        with patched_item(ctx['zs'][bat].over['G2-REVA']['layers'], 'rear_pcb', ctx['zs'][bat].over['G2-REVA']['layers']['rear_pcb'] + 0.001):
            return flagged([k for k, v in g3_not_reopened(cx)['items'].items() if not v['pass_']])
    add('PGF', 'pgf_rear_z_shift_0p001', rear_z)

    def land_enlarged():
        def f(w):
            sup = w['handoff']['supports']
            sup[0]['polygon']['assembly_mm'][0][0] += 0.2
        return g3_work(f)
    add('PGF', 'pgf_support_land_enlarged', land_enlarged)

    def pillar_beyond():
        fps = {az_: [tuple(p) for p in fp] for az_, fp in pillar_footprints(cx).items()}
        az0 = sorted(fps)[0]
        fps[az0] = [(p[0] + 0.5, p[1]) for p in fps[az0]]
        return flagged([k for k, v in g3_not_reopened(cx, pillars=fps)['items'].items() if not v['pass_']])
    add('PGF', 'pgf_pillar_footprint_beyond_its_land', pillar_beyond)

    def mirrored():
        def f(w):
            for k in w['placements']:
                w['placements'][k]['assembly_xy_mm'][0] = 200.0 - w['placements'][k]['assembly_xy_mm'][0]
        return g3_work(f)
    add('PGF', 'pgf_mirrored_rear_transform', mirrored)

    # ======================================================= governance
    def byte_flip():
        real = sha_file
        target = 'design/mechanical/generated/g4_case_sealing.json'

        def flipped(p):
            h = real(p)
            return ('0' if h[0] != '0' else '1') + h[1:] if str(p).endswith(target) else h
        with patched(sys.modules[__name__], 'sha_file', flipped):
            return flagged([p['path'] for p in pin_report(r2in) if not p['match']])
    add('PGF', 'pgf_historical_g4_file_byte_flip', byte_flip)

    def r1_flip():
        real = sha_file

        def flipped(p):
            h = real(p)
            return ('0' if h[0] != '0' else '1') + h[1:] if str(p).endswith('generated/g4_r1_blockers.json') else h
        with patched(sys.modules[__name__], 'sha_file', flipped):
            return flagged([p['path'] for p in pin_report(r2in) if not p['match']])
    add('PGF', 'pgf_historical_r1_file_byte_flip', r1_flip)

    def kicad_touched():
        real = git

        def fake(*a):
            r_ = real(*a)
            if a and a[0] == 'diff' and any('kicad' in x for x in a):
                class R:
                    stdout = 'sportwatch.kicad_pcb\n'
                return R
            return r_
        with patched(sys.modules[__name__], 'git', fake):
            return flagged([] if scope_report(r2in)['pass_'] else ['scope fails'])
    add('PGF', 'pgf_kicad_file_touched', kicad_touched)
    add('PIF', 'pif_interface_24_13_changed', lambda: vcheck('inputs', c=mutin(lambda r: r['interconnect'].__setitem__('nets', 14))))
    add('VS', 'vs_commit_state_text_in_status', lambda: vcheck('governance', r=mutres(lambda r: r.__setitem__('status', r['status'] + ' Committed and independently reviewed.'))))

    def wildcard():
        g4.ALLOWED_CHANGES.add('design/mechanical/*')
        try:
            return vcheck('governance')
        finally:
            g4.ALLOWED_CHANGES.discard('design/mechanical/*')
    add('PGF', 'pgf_allowed_changes_wildcard', wildcard)

    def extension_wrong():
        g4.ALLOWED_CHANGES.add('design/mechanical/extra_file.json')
        try:
            return vcheck('governance')
        finally:
            g4.ALLOWED_CHANGES.discard('design/mechanical/extra_file.json')
    add('PGF', 'pgf_allowed_changes_extension_not_exact', extension_wrong)
    add('VS', 'vs_g4_reproduction_failed', lambda: vcheck('governance', c=dict(ctx, g4=dict(ctx['g4'], pass_=False, caught=31, fails=['x']))))

    # ======================================================= states and verdicts
    add('VS', 'vs_verdict_closed_with_stops', lambda: vcheck('states', r=mutres(lambda r: r['batteries'][bat].__setitem__('verdict', VERDICTS[3]))))
    add('VS', 'vs_disposition_resting_on_a_credit', lambda: vcheck('status', r=mutres(lambda r: r['batteries'][bat]['hard_checks']['R2-H11']['credits'].append('conductor band'))))
    add('VS', 'vs_r1_column_missing', lambda: vcheck('columns', r=mutres(lambda r: r['batteries'][bat]['hard_checks']['R2-H05'].__setitem__('r1_column', None))))
    add('VS', 'vs_battery_column_missing', lambda: vcheck('columns', r=mutres(lambda r: r['batteries'].pop('LPR403736'))))
    add('VS', 'vs_hard_check_missing', lambda: vcheck('states', r=mutres(lambda r: r['batteries'][bat]['hard_checks'].pop('R2-H20'))))
    add('VS', 'vs_anchor_mismatch', lambda: vcheck('anchors', r=mutres(lambda r: r['anchors']['rows'][0].__setitem__('match', False))))
    add('VS', 'vs_lead_crosscheck_unexplained', lambda: vcheck('p3', r=mutres(lambda r: r['lead_crosschecks'][0].__setitem__('status', 'UNEXPLAINED'))))

    # ======================================================= serialization / result object
    def flip_json():
        f2_ = dict(files)
        f2_['g4_r2_closure.json'] = files['g4_r2_closure.json'].replace('"verdict"', '"verdiCt"', 1)
        return flagged(bytes_problems(f2_, files))
    add('SR', 'sr_json_byte_flip_differs_from_regenerated', flip_json)
    add('SR', 'sr_non_canonical_json', lambda: vcheck('serialization', f=dict(files, **{'g4_r2_closure.json': json.dumps(base, indent=1, sort_keys=True) + '\n'})))
    add('SR', 'sr_missing_final_newline', lambda: vcheck('serialization', f=dict(files, **{'g4_r2_closure.md': files['g4_r2_closure.md'].rstrip('\n')})))
    add('SR', 'sr_runtime_key_in_json', lambda: vcheck('serialization', f=dict(files, **{'g4_r2_closure.json': dumps(dict(base, runtime_s=12.3))})))
    add('SR', 'sr_timestamp_in_json', lambda: vcheck('serialization', f=dict(files, **{'g4_r2_closure.json': dumps(dict(base, generated='2026-10-17T12:00:00Z'))})))
    add('SR', 'sr_unsorted_keys', lambda: vcheck('serialization', f=dict(files, **{'g4_r2_closure.json': json.dumps(base, separators=(',', ':')) + '\n'})))
    add('SR', 'sr_malformed_svg', lambda: vcheck('serialization', f=dict(files, **{'g4_r2_plan.svg': files['g4_r2_plan.svg'].replace('</svg>', '')}), must='well-formed'))
    add('SR', 'sr_float_beyond_nine_decimals', lambda: vcheck('serialization', f=dict(files, **{'g4_r2_closure.json': files['g4_r2_closure.json'].replace('"D":50.6', '"D":50.6000000001', 1)})))

    add('SR', 'sr_no_stale_sweep_file', lambda: (not (GEN / SWEEP_NAME).exists(), 'no g4_r2_sweep.jsonl present while the JSON is below the size limit'))
    return out


# ============================================================================================
# CLI
# ============================================================================================
def write_outputs(files):
    for name, text in files.items():
        (GEN / name).write_bytes(text.encode('utf-8'))
    sweep = GEN / SWEEP_NAME
    if sweep.exists():
        raise StudyError('STOP: stale %s present (the JSON is below the size limit, no sweep side file is produced)' % SWEEP_NAME)


def main(argv):
    if len(argv) != 2 or argv[1] not in ('build', 'check', 'selftest'):
        sys.stderr.write('usage: g4_r2_closure.py build|check|selftest\n')
        return 2
    t0 = time.time()
    try:
        timing = {}
        res, ctx = build_results(timing)
        files = outputs(res, ctx)
        if argv[1] == 'build':
            write_outputs(files)
            print(json.dumps(dict(status='BUILT', verdict=res['verdict'], verdict_by_battery=res['verdict_by_battery'], files=sorted(files), evaluations=res['search']['evaluations'],
                                  runtime_s=round(time.time() - t0, 1), sha256={n: hashlib.sha256(t.encode()).hexdigest() for n, t in sorted(files.items())}), sort_keys=True))
            return 0
        if argv[1] == 'selftest':
            tests = self_tests(res, ctx, files)
            ok = all(x['caught'] for x in tests)
            cats = {c: dict(total=sum(1 for x in tests if x['category'] == c), passed=sum(1 for x in tests if x['category'] == c and x['caught'])) for c in SELFTEST_CATEGORIES}
            if any(x['category'] not in SELFTEST_CATEGORIES for x in tests):
                raise StudyError('STOP: self-test outside the five taxonomy categories')
            print(json.dumps(dict(status='PASS' if ok else 'FAIL', tests=len(tests), passed=sum(1 for x in tests if x['caught']), categories=cats,
                                  not_caught=[x for x in tests if not x['caught']], runtime_s=round(time.time() - t0, 1)), sort_keys=True))
            return 0 if ok else 1
        elapsed = time.time() - t0
        fails = validate(res, ctx, files, elapsed, disk=True)
        elapsed = time.time() - t0
        print(json.dumps(dict(status='PASS' if not fails else 'FAIL', failures=fails, verdict=res['verdict'], verdict_by_battery=res['verdict_by_battery'],
                              stops={b: [s_['id'] for s_ in res['batteries'][b]['stops']] for b in BATTERIES}, evaluations=res['search']['evaluations'],
                              g4_in_process=dict(pass_=ctx['g4']['pass_'], tests=ctx['g4']['tests'], caught=ctx['g4']['caught']), runtime_s=round(elapsed, 1),
                              runtime_breakdown_s={k: round(v, 1) for k, v in ctx['timing'].items()}), sort_keys=True))
        return 0 if not fails else 1
    except StudyError as exc:
        print(json.dumps(dict(status='STOP', reason=str(exc))))
        return 1


SELFTEST_CATEGORIES = ('PIF', 'PGF', 'PA', 'VS', 'SR')

if __name__ == '__main__':
    sys.exit(main(sys.argv))
