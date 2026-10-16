#!/usr/bin/env python3
"""G4-R1 case / seal / support blocker-resolution study (Rev-A). Stdlib only, deterministic.

Sub-commands:
  build     write the R1 generated outputs (generated/g4_r1_blockers.{json,md}, g4_r1_*.svg)
  check     regenerate in memory and validate independently: byte identity, pins, historical G4
            in-process reproduction (C-R1-09), scope, hard-check state invariants, recomputed
            selection / Z / pack / PASS predicates, sizes, XML and runtime
  selftest  production-path mutation suite (G4_R1_BRIEF section 11 and the correction pass list)

Imports g4_case_sealing (and through it mech_model / g1_scenarios / g2_interconnect) as a library.
Frozen G1-G4 values are read from the pinned sources at run time. No KiCad, G5, K1 or Q1 work; no
5 ATM, structural, optical, adhesive, RF or supplier qualification claim.
"""
import bisect
import copy
import hashlib
import html
import json
import math
import subprocess
import sys
import time
import xml.dom.minidom
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
MECH = ROOT / 'design/mechanical'
GEN = MECH / 'generated'
IN_PATH = MECH / 'inputs/g4_r1_blockers.json'
BRIEF = 'design/mechanical/G4_R1_BRIEF.md'

sys.path.insert(0, str(MECH / 'tools'))
import g4_case_sealing as g4  # noqa: E402
import mech_model as mm  # noqa: E402,F401  (imported through g4; kept explicit per the R1 contract)
import g1_scenarios as g1  # noqa: E402
import g2_interconnect as g2  # noqa: E402,F401

R1_FILES = frozenset({
    'design/mechanical/G4_R1_BRIEF.md',
    'design/mechanical/inputs/g4_r1_blockers.json',
    'design/mechanical/tools/g4_r1_blockers.py',
    'design/mechanical/generated/g4_r1_blockers.json',
    'design/mechanical/generated/g4_r1_blockers.md',
    'design/mechanical/generated/g4_r1_plan.svg',
    'design/mechanical/generated/g4_r1_sections.svg',
    'design/mechanical/generated/g4_r1_sweep.jsonl',
})
OUT_NAMES = ('g4_r1_blockers.json', 'g4_r1_blockers.md', 'g4_r1_plan.svg', 'g4_r1_sections.svg')
SWEEP_NAME = 'g4_r1_sweep.jsonl'
G4_BASELINE = '00e77cbe107a79ac05194f19b674f7ab8d5941c9'
G4_ORIGINAL_ALLOWED = frozenset(g4.ALLOWED_CHANGES)
EPS = 1e-9
STATUSES = ('PASS', 'FAIL', 'GATED', 'BLOCKED', 'NOT_EVALUATED')
DISPOSITIONS = ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED', 'OWNER_GATED', 'ARCHITECTURE_GATED',
                'RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED')
LANES = ('L-WIN', 'L-BTN', 'L-SEAL', 'L-CHG', 'L-STR', 'L-RAD', 'L-ASM', 'L-LRA')
VERDICTS = ('R1 RESOLVED', 'R1 RESOLVED — SUPPLIER/RF/QUALIFICATION GATES OPEN', 'R1 PARTIAL — LRA ARCHITECTURE GATE',
            'R1 OWNER DECISION REQUIRED', 'R1 FAIL')
FATAL_STOPS = ('R1-S01', 'R1-S02', 'R1-S09', 'R1-S10', 'R1-S11', 'R1-S12')
LANE_STOPS = ('R1-S03', 'R1-S04', 'R1-S05', 'R1-S06', 'R1-S07', 'R1-S08', 'R1-S13')
EVAL = {'n': 0}


class StudyError(Exception):
    """A STOP condition of the deterministic model (input contradiction or broken invariant)."""


def count(n=1):
    EVAL['n'] += n


# --------------------------------------------------------------------------------------------
# I/O and formatting (kept from the first R1 pass)
# --------------------------------------------------------------------------------------------
def load_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rounded(o):
    if isinstance(o, float):
        return round(o, 9) + 0.0
    if isinstance(o, dict):
        return {k: rounded(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [rounded(v) for v in o]
    return o


def dumps(o):
    return json.dumps(rounded(o), sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'


def f2(v):
    return 'n/a' if v is None else '%.2f' % (round(v, 2) + 0.0)


def f3(v):
    return 'n/a' if v is None else '%.3f' % (round(v, 3) + 0.0)


def fs(v):
    """Signed fixed 3-decimal format; never prints a negative margin without its sign."""
    return 'n/a' if v is None else '%+.3f' % (round(v, 3) + 0.0)


def frange(start, stop, step):
    return g4.frange(start, stop, step)


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)


def esc(s):
    return html.escape(str(s), quote=True)


# --------------------------------------------------------------------------------------------
# C-R1-09: in-process historical G4 execution with the prospective R1_FILES extension
# --------------------------------------------------------------------------------------------
def run_g4_in_process():
    """Prospective allow-list extension (only R1_FILES, nothing else patched), then the G4 module's own
    build, validate (byte identity against the committed G4 files) and self-tests."""
    added = R1_FILES - G4_ORIGINAL_ALLOWED
    g4.ALLOWED_CHANGES |= R1_FILES
    timing = {}
    t0 = time.time()
    g4_res = g4.build_results(timing)
    st = timing['study']
    files = g4.outputs(g4_res, st)
    fails = g4.validate(g4_res, st, files, 0.0)
    tests = g4.self_tests(g4_res, st)
    caught = sum(1 for t in tests if t['caught'])
    return dict(res=g4_res, st=st, files=files, fails=fails, tests=len(tests), caught=caught,
                extension=sorted(added), extension_exact=(set(g4.ALLOWED_CHANGES) - G4_ORIGINAL_ALLOWED) == set(R1_FILES),
                runtime_s=time.time() - t0,
                pass_=(not fails and len(tests) == 32 and caught == 32))


# --------------------------------------------------------------------------------------------
# Inputs: schema guard (inputs, never results) and candidate construction (no re-typing)
# --------------------------------------------------------------------------------------------
FORBIDDEN_INPUT_KEYS = ('verdict', 'margin', 'selected', 'minimum_feasible', 'd_min', 'winner', 'result', 'outcome',
                        'disposition', 'pass_', 'feasible')


def input_violations(r1in):
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
    walk(r1in.get('parameters', {}), 'parameters')
    walk(r1in.get('candidates', []), 'candidates')
    return bad


C_R1_01_V_TEXT = '(v) clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z'


def input_contract_violations(r1in, brief_text=None):
    """R5-2 (build STOP and check): the literal contract transcriptions of the R1 input are cross-checked against the brief's C-R1-01
    scope. The brief must carry 2(v) "in plan and in Z" inside item 2 (subject: the non-conductive land) and not in item 1 (the
    conductive block). Every input record whose evidence class is a literal CONTRACT transcription must not attribute anything to the
    (conductive) block; a literal C-R1-01 item 2 (v) record must name the non-conductive land, carry the (v) text verbatim from item 2,
    and may mention the block only inside a nested record labelled lead / model conservatism (not contract text)."""
    bad = []
    norm = lambda t: ' '.join(str(t).replace('**', '').replace('`', '').split())
    brief = norm(brief_text if brief_text is not None else (ROOT / BRIEF).read_text(encoding='utf-8'))
    i1, i2, i3 = (brief.find('1. the conductive 4 x 5 mm contact block'), brief.find('2. the non-conductive bond/seal land'),
                  brief.find('3. the side overshoot'))
    if not (0 <= i1 < i2 < i3) or C_R1_01_V_TEXT not in brief[i2:i3] or 'in plan and in Z' in brief[i1:i2]:
        bad.append('brief C-R1-01 scope: 2(v) "in plan and in Z" is not item 2 (non-conductive land) text, or item 1 (block) carries it')
    item2 = brief[i2:i3] if 0 <= i2 < i3 else ''
    found = []

    def walk(o, path):
        if isinstance(o, dict):
            ec = norm(o.get('evidence_class', '')).upper()
            if 'CONTRACT' in ec and 'LITERAL' in ec:
                for k, v in o.items():
                    if isinstance(v, str) and k != 'evidence_class' and 'block' in v.lower():
                        bad.append('%s.%s: literal contract transcription attributes the clause to the (conductive) block' % (path, k))
                    elif isinstance(v, dict) and 'block' in json.dumps(v).lower():
                        sec = norm(v.get('evidence_class', '')).upper()
                        if 'CONTRACT' in sec.replace('NOT CONTRACT TEXT', '') or 'CONSERVATISM' not in sec or 'NOT CONTRACT TEXT' not in sec:
                            bad.append('%s.%s: block plan-AND-Z screen inside a literal contract record is not labelled lead / model '
                                       'conservatism (not contract text)' % (path, k))
                if 'C-R1-01 ITEM 2 (V)' in ec:
                    found.append(path)
                    if not o.get('contract_text') or norm(o['contract_text']) not in item2 or C_R1_01_V_TEXT not in norm(o['contract_text']):
                        bad.append('%s.contract_text: not the verbatim C-R1-01 item 2 (v) text of the brief' % path)
                    rule = norm(o.get('rule', ''))
                    if 'non-conductive' not in rule or 'land' not in rule or C_R1_01_V_TEXT.split(') ', 1)[1] not in rule:
                        bad.append('%s.rule: literal 2(v) transcription does not attribute the clause to the non-conductive land' % path)
                    if 'non-conductive' not in norm(o.get('subject', '')) or 'land' not in norm(o.get('subject', '')):
                        bad.append('%s.subject: the 2(v) subject is not the non-conductive land' % path)
            for k, v in o.items():
                walk(v, '%s.%s' % (path, k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, '%s[%d]' % (path, i))
    walk(r1in, 'inputs')
    if not found:
        bad.append('inputs: no literal C-R1-01 item 2 (v) transcription found')
    return bad


def build_candidates(st, r1in):
    g4c = {c['id']: c for c in st.I['candidates']}
    out = []
    for c in r1in['candidates']:
        if 'base' in c:
            base = copy.deepcopy(g4c[c['base']])
            base.update(copy.deepcopy(c['overrides']))
            base['id'] = c['id']
            base['r1_definition'] = c['definition']
            out.append(base)
        else:
            d = copy.deepcopy(g4c[c['id']])
            d['r1_definition'] = c['definition']
            out.append(d)
    return out


# --------------------------------------------------------------------------------------------
# Common Z model (Z = 0 window / caseback exterior plane, +Z toward the front; LA-Z-1 / LA-Z-2)
# --------------------------------------------------------------------------------------------
def z_model(st):
    """REAR-periphery Z datums from the G2-REVA / G2-REVA-HI stacks (governing minimum band)."""
    per = {b: sum(st.z[b]['layers'][k] for k in ('rear_inner', 'rear_pcb', 'optics_zone', 'window')) for b in st.z}
    alloc = st.rear_alloc_min()
    if abs(alloc - min(per.values())) > EPS:
        raise StudyError('REAR allocation mismatch against g4 rear_alloc_min')
    tol_lw = st.tolpol['t_lower_web']
    route = st.P['c_rear_route_mm']['max']
    lay = st.z['G2-REVA']['layers']
    return dict(datum='Z=0 caseback / window exterior plane (pod plane, h_pod = 0.0 per LA-Z-1); +Z toward the front',
                rear_alloc_by_baseline=per, governing_baseline=min(per, key=lambda b: (per[b], b)),
                z_lower_web_underside_nom=alloc, z_lower_web_underside_adv=alloc - tol_lw, tol_lower_web=tol_lw,
                conductor_band_height=route, z_band_lo_adv=alloc - tol_lw - route, z_band_hi_nom=alloc,
                z_rear_skin_nom=lay['window'] + lay['optics_zone'], pod_depth_nom=lay['window'] + lay['optics_zone'],
                h_pod=0.0, lower_web=lay['lower_web'],
                rule='LA-Z-2: the REAR conductor band (c_rear_route max) lies directly below the lower web over the entire '
                     'periphery; every caseback-side feature (ribs, flange, charger block, LRA) must stay below z_band_lo_adv.')


def zfeat(z_lo_nom, z_hi_nom, tol_lo=0.0, tol_hi=0.0):
    return dict(z_lo_nom=z_lo_nom, z_hi_nom=z_hi_nom, z_lo_adv=z_lo_nom - tol_lo, z_hi_adv=z_hi_nom + tol_hi)


def feature(fid, lane, material, conductive, ferro, geom, levels, z, kind, **extra):
    """Common physical feature record (S5)."""
    d = dict(id=fid, lane=lane, material=material, conductive=bool(conductive), ferromagnetic=bool(ferro), geom=geom,
             z=list(levels), kind=kind)
    d.update(z)
    d.update(extra)
    return d


def z_gap(a, b):
    """Signed Z separation of two feature Z intervals at adverse extent (> 0 separated)."""
    return max(b['z_lo_adv'] - a['z_hi_adv'], a['z_lo_adv'] - b['z_hi_adv'])


def separated(gap, c=0.0):
    """R3-3: the one strict clearance rule of every physical clearance predicate (plan or Z). A gap separates two bodies only
    when it is strictly positive beyond the numerical tolerance EPS and meets the required clearance c: gap > EPS separated;
    |gap| <= EPS (touching) a collision; gap < -EPS an overlap. Allocation-fit checks (a feature inside its Z allocation,
    D <= ceiling, margins against a required clearance c > 0) keep the accepted G4 margin >= 0 convention."""
    return gap > EPS and gap >= c - EPS


def clear(a, b, c_plan, c_z):
    """Common 3-D clearance predicate: separated in plan by > 0 and >= c_plan, or in Z by > 0 and >= c_z (adverse extents,
    strict rule `separated`; touching in plan or Z is a collision)."""
    count()
    zg = z_gap(a, b)
    if separated(zg, c_z):
        return True, dict(mode='Z', z_gap_mm=zg, plan_gap_mm=None)
    touching = g4.overlaps(a['geom'], b['geom'])
    pg = 0.0 if touching else poly_distance(a['geom'], b['geom'])
    return (not touching and separated(pg, c_plan)), dict(mode='PLAN', z_gap_mm=zg, plan_gap_mm=pg)


def wedge_disjoint(ga, gb):
    """Exact prefilter: a convex polygon that does not contain the centre lies inside the cone spanned by its vertices
    (span < 180 deg); a sector whose azimuth interval is strictly disjoint from that cone cannot touch it."""
    if ga['type'] != 'poly' or gb['type'] != 'sector' or tuple(gb['az']) == (0.0, 360.0):
        return False
    pts = [tuple(q) for q in ga['pts']]
    if g4.pip((100.0, 100.0), pts):
        return False
    azs = sorted(g4.polar(q)[1] for q in pts)
    gmax, i = max(((azs[(j + 1) % len(azs)] - azs[j]) % 360.0, j) for j in range(len(azs)))
    lo, hi = azs[(i + 1) % len(azs)], azs[i]
    return (hi - lo) % 360.0 < 180.0 - 1e-6 and g4.arc_gap((lo, hi), tuple(gb['az'])) > 1e-6


def plan_overlap(ga, gb):
    """Exact plan collision (touching counts): the wedge prefilter, then g4.overlaps."""
    return False if wedge_disjoint(ga, gb) else g4.overlaps(ga, gb)


def clear_both(a, b, c_plan, c_z, report_gap=True):
    """C-R1-01 (v) literal predicate: clear in plan AND in Z. A Z separation never waives a plan collision; the plan test is
    the exact g4.overlaps (touching counts as a collision); the Z test is the strict rule `separated` (a zero Z gap is a
    collision, R3-3)."""
    count()
    zg = z_gap(a, b)
    touching = plan_overlap(a['geom'], b['geom'])
    pg = 0.0 if touching else (poly_distance(a['geom'], b['geom']) if report_gap else None)
    plan_ok = not touching and (pg is None or separated(pg, c_plan))
    z_ok = separated(zg, c_z)
    return plan_ok and z_ok, dict(mode='PLAN_AND_Z', z_gap_mm=zg, plan_gap_mm=pg, plan_clear=plan_ok, z_clear=z_ok)


# --------------------------------------------------------------------------------------------
# Exact convex-polygon geometry (cross-checked against g4.region_distance / g4.overlaps in selftest)
# --------------------------------------------------------------------------------------------
def geom_poly(g):
    if g['type'] == 'poly':
        return [tuple(p) for p in g['pts']]
    if g['type'] == 'rect':
        x0, y0, x1, y1 = g['rect']
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return None


def poly_distance(ga, gb):
    """Plan distance for rect/poly pairs (exact, vertex-edge); falls back to g4.region_distance otherwise."""
    pa, pb = geom_poly(ga), geom_poly(gb)
    if pa is None or pb is None:
        return g4.region_distance(ga, gb, 0.05)
    ax0, ax1 = min(p[0] for p in pa), max(p[0] for p in pa)
    ay0, ay1 = min(p[1] for p in pa), max(p[1] for p in pa)
    bx0, bx1 = min(p[0] for p in pb), max(p[0] for p in pb)
    by0, by1 = min(p[1] for p in pb), max(p[1] for p in pb)
    disjoint = ax1 < bx0 - EPS or bx1 < ax0 - EPS or ay1 < by0 - EPS or by1 < ay0 - EPS
    if not disjoint and g4.polygon_overlap(pa, gb):
        return 0.0
    ea = list(zip(pa, pa[1:] + pa[:1]))
    eb = list(zip(pb, pb[1:] + pb[:1]))
    d_ab = min(g4.seg_dist(p, a, b) for p in pa for a, b in eb)
    d_ba = min(g4.seg_dist(p, a, b) for p in pb for a, b in ea)
    return min(d_ab, d_ba)


def local_rect(azc, u0, u1, v0, v1):
    """Rectangle in the local frame of azimuth azc (u radial, v clockwise tangential) as an assembly polygon."""
    t = math.radians(azc)
    er = (math.sin(t), -math.cos(t))
    et = (math.cos(t), math.sin(t))
    pts = []
    for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        pts.append((100.0 + u * er[0] + v * et[0], 100.0 + u * er[1] + v * et[1]))
    return pts


def side_overshoot(p, az_side, outward):
    """Signed perpendicular distance of p beyond the wedge side line through (100,100) at az_side; outward=+1 for
    the clockwise (larger-az) side, -1 for the counter-clockwise side."""
    t = math.radians(az_side)
    er = (math.sin(t), -math.cos(t))
    et = (math.cos(t), math.sin(t))
    dx, dy = p[0] - 100.0, p[1] - 100.0
    return outward * (dx * et[0] + dy * et[1])


# --------------------------------------------------------------------------------------------
# L-STR plate solver: axisymmetric polar-orthotropic Kirchhoff annulus (transfer form)
#   state S = [w, psi=w', M_r, Q]; per region constants x = [c0, c1, c2, A]
#   -D_r (psi'' + psi'/r - k^2 psi/r^2) = Q,  Q = A/r - q r/2,  k^2 = D_theta / D_r
#   M_r = -(D_r psi' + D_1 psi / r),  M_theta = -(D_1 psi' + D_theta psi / r),  D_1 = nu D_theta
# Reduces to the accepted g4._basis isotropic solution for k = 1 (anchor-tested).
# --------------------------------------------------------------------------------------------
def _ortho(r, reg, q):
    """Basis rows (coefficient vectors over [c0, c1, c2, A]) and particular values for w, psi, dpsi, M_r,
    M_theta, Q at radius r. Exact isotropic limit forms when k == 1 (k^2 = D_theta / D_r)."""
    Dr, Dt, D1, k, rr = reg['Dr'], reg['Dt'], reg['D1'], reg['k'], reg['r0']
    if abs(1.0 - k) < 1e-12:
        ln = math.log(r / rr)
        psi = [0.0, r, 1.0 / r, -(r * ln / 2.0) / Dr]
        w = [1.0, r * r / 2.0, ln, -(r * r * (2.0 * ln - 1.0) / 8.0) / Dr]
        dpsi = [0.0, 1.0, -1.0 / (r * r), -((ln + 1.0) / 2.0) / Dr]
    else:
        rk, rr1k, den = r ** k, rr ** (1.0 - k), 1.0 - k * k
        psi = [0.0, rk, 1.0 / rk, -((r - rr1k * rk) / den) / Dr]
        w = [1.0, r * rk / (k + 1.0), (r / rk - rr1k) / (1.0 - k), -((r * r / 2.0 - rr1k * r * rk / (k + 1.0)) / den) / Dr]
        dpsi = [0.0, k * rk / r, -k / (rk * r), -((1.0 - k * rr1k * rk / r) / den) / Dr]
    c = q / (2.0 * Dr * (9.0 - k * k))
    ppsi, pw, pdpsi = c * r ** 3, c * r ** 4 / 4.0, 3.0 * c * r * r
    Mr = [-(Dr * dpsi[i] + D1 * psi[i] / r) for i in range(4)]
    Mt = [-(D1 * dpsi[i] + Dt * psi[i] / r) for i in range(4)]
    return dict(w=(w, pw), psi=(psi, ppsi), dpsi=(dpsi, pdpsi), Mr=(Mr, -(Dr * pdpsi + D1 * ppsi / r)),
                Mt=(Mt, -(D1 * pdpsi + Dt * ppsi / r)), Q=([0.0, 0.0, 0.0, 1.0 / r], -q * r / 2.0))


STATE = ('w', 'psi', 'Mr', 'Q')


def _bmat(r, reg, q):
    b = _ortho(r, reg, q)
    return [b[k][0] for k in STATE], [b[k][1] for k in STATE]


def _inv4(m):
    n = 4
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[p] = a[p], a[c]
        if abs(a[c][c]) < 1e-300:
            raise StudyError('singular plate region basis')
        piv = a[c][c]
        a[c] = [x / piv for x in a[c]]
        for r in range(n):
            if r != c and a[r][c] != 0.0:
                f = a[r][c]
                a[r] = [x - f * y for x, y in zip(a[r], a[c])]
    return [row[n:] for row in a]


def _mv(m, v):
    return [sum(a * b for a, b in zip(row, v)) for row in m]


INNER_BC = {'loaded_boss': ('psi', 'Q'), 'boss': ('psi', 'Q')}
OUTER_BC = {'ss': ('w', 'Mr'), 'clamped': ('w', 'psi')}


def plate_solve(regions, q, inner='loaded_boss', outer='ss', nsamp=41):
    """regions: list of dicts (r0, r1, Dr, Dt, D1, k, kind, ...). Inner edge: loaded rigid boss (accepted G4 bypass
    semantics, LA-STR-3); 'ss' at the inner edge is an invented support and is refused. Returns the coefficient
    vectors and sampled w / psi / dpsi / M_r / M_theta."""
    if inner not in INNER_BC:
        raise StudyError('invented inner caseback support refused (LA-STR-3): inner=%s' % inner)
    count()
    r0 = regions[0]['r0']
    # Unknown inner state components (the two not fixed by the inner BC), propagated affinely.
    fixed = dict(psi=0.0, Q=(-q * r0 / 2.0 if inner == 'loaded_boss' else 0.0))
    free = [k for k in STATE if k not in INNER_BC[inner]]
    S0 = [fixed.get(k, 0.0) for k in STATE]
    E1 = [1.0 if k == free[0] else 0.0 for k in STATE]
    E2 = [1.0 if k == free[1] else 0.0 for k in STATE]
    vecs = [S0, E1, E2]
    coeffs = []
    for i, reg in enumerate(regions):
        B0, P0 = _bmat(reg['r0'], reg, q)
        Bi = _inv4(B0)
        xs = [_mv(Bi, [s - (p if j == 0 else 0.0) for s, p in zip(v, P0)]) for j, v in enumerate(vecs)]
        coeffs.append(xs)
        B1, P1 = _bmat(reg['r1'], reg, q)
        vecs = [[a + (p if j == 0 else 0.0) for a, p in zip(_mv(B1, x), P1)] for j, x in enumerate(xs)]
    idx = [STATE.index(k) for k in OUTER_BC[outer]]
    a11, a12 = vecs[1][idx[0]], vecs[2][idx[0]]
    a21, a22 = vecs[1][idx[1]], vecs[2][idx[1]]
    b1, b2 = -vecs[0][idx[0]], -vecs[0][idx[1]]
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
            b = _ortho(r, reg, q)
            val = {key: x[0] * b[key][0][0] + x[1] * b[key][0][1] + x[2] * b[key][0][2] + x[3] * b[key][0][3] + b[key][1]
                   for key in ('w', 'psi', 'dpsi', 'Mr', 'Mt')}
            val['r'] = r
            pts.append(val)
        out.append(dict(region=reg, x=x, samples=pts))
    return out


def iso_region(r0, r1, t, E, nu, kind='plate'):
    D = E * t ** 3 / (12.0 * (1.0 - nu * nu))
    return dict(r0=r0, r1=r1, Dr=D, Dt=D, D1=nu * D, k=1.0, t=t, E=E, nu=nu, kind=kind)


def iso_compare(regions_g4, q, inner='loaded_boss', nsamp=81):
    """Isotropic-limit run on the G4 region tuple format; returns (w_max, sigma_max) like g4._annular_plate."""
    regs = [iso_region(a, b, t, e, nu) for a, b, t, e, nu in regions_g4]
    sol = plate_solve(regs, q, inner, 'ss', nsamp)
    wmax = max(abs(p['w']) for s in sol for p in s['samples'])
    smax = max(6.0 * max(abs(p['Mr']), abs(p['Mt'])) / s['region']['t'] ** 2 for s in sol for p in s['samples'])
    return dict(w=wmax, sigma=smax)


def rib_section(t, w, h, s):
    """T-section per rib pitch. b_f = min(s, w + 12 t). I_T is the composite inertia about its own neutral axis;
    LA-STR-1: the credited increment I_inc = I_T - b_f t^3 / 12 (flange self-inertia removed), so h -> 0 gives
    I_inc -> 0 and D_r -> D_plate exactly."""
    b_f = min(s, w + 12.0 * t)
    if h <= 0.0 or w <= 0.0 or s <= 0.0:
        return dict(b_f=b_f, y_c=t / 2.0, I_T=b_f * t ** 3 / 12.0, I_inc=0.0, A=b_f * t)
    A_f, A_w = b_f * t, w * h
    y_c = (A_f * t / 2.0 + A_w * (t + h / 2.0)) / (A_f + A_w)
    I_T = b_f * t ** 3 / 12.0 + A_f * (y_c - t / 2.0) ** 2 + w * h ** 3 / 12.0 + A_w * (t + h / 2.0 - y_c) ** 2
    return dict(b_f=b_f, y_c=y_c, I_T=I_T, I_inc=I_T - b_f * t ** 3 / 12.0, A=A_f + A_w)


def rib_D(E, nu, t, w, h, s):
    """(D_plate, D_r) per unit circumferential width, LA-STR-1 smeared formulation."""
    Dp = E * t ** 3 / (12.0 * (1.0 - nu * nu))
    sec = rib_section(t, w, h, s)
    return Dp, Dp + (E * sec['I_inc'] / s if s > 0.0 else 0.0), sec


def str_regions(geo, mats, cfg, screen, N):
    """Radial regions from project geometry at adverse dimensions. geo: rb, r_step, r_rib_in, r_rib_out, R,
    r_split (optional), gap_deg (largest credited angular gap; None = no credited ribs), pocket (optional band
    [r0, r1, t_res]). mats(r) -> material dict (E min, nu max, sigma_allow min, tol_t, tol_w). screen: 'A' (isotropic
    equivalent t_eq, LA-STR-2) or 'B' (polar orthotropic, D_theta = plate only, LA-STR-4)."""
    bps = {geo['rb'], geo['r_step'], geo['r_rib_in'], geo['r_rib_out'], geo['R']}
    if geo.get('r_split'):
        bps.add(geo['r_split'])
    if geo.get('pocket'):
        bps.update(geo['pocket'][:2])
    ribbed = cfg['n'] > 0 and geo['gap_deg'] is not None and cfg['h'] > 0.0
    if ribbed:
        for j in range(1, N):
            bps.add(geo['r_rib_in'] + (geo['r_rib_out'] - geo['r_rib_in']) * j / N)
    bps = sorted(b for b in bps if geo['rb'] - EPS <= b <= geo['R'] + EPS)
    regs = []
    for a, b in zip(bps, bps[1:]):
        if b - a < 1e-9:
            continue
        mid = (a + b) / 2.0
        m = mats(mid)
        E, nu = m['E'], m['nu']
        if mid < geo['r_step']:
            t_nom, kind = cfg['t_in'], 'inner'
        else:
            t_nom, kind = cfg['t_out'], 'outer'
        t = t_nom - m['tol_t']
        pocket = geo.get('pocket')
        if pocket and pocket[0] - EPS <= a and b <= pocket[1] + EPS:
            t, kind = pocket[2] - m['tol_t'], 'pocket'
        reg = iso_region(a, b, t, E, nu, kind)
        reg.update(sigma_allow=m['sigma_allow'], material=m['id'], t_plate=t)
        in_ribs = ribbed and geo['r_rib_in'] - EPS <= a and b <= geo['r_rib_out'] + EPS and kind != 'pocket'
        if in_ribs:
            s = b * math.radians(geo['gap_deg'])
            w_a, h_a = cfg['w'] - m['tol_w'], cfg['h'] - m['tol_t']
            Dp, Dr, sec = rib_D(E, nu, t, w_a, h_a, s)
            reg.update(kind='ribbed', s=s, w_a=w_a, h_a=h_a, y_c=sec['y_c'], b_f=sec['b_f'], I_inc=sec['I_inc'],
                       Dp=Dp, Dr_rib=Dr)
            if screen == 'A':
                t_eq = (12.0 * (1.0 - nu * nu) * Dr / E) ** (1.0 / 3.0)
                reg.update(Dr=Dr, Dt=Dr, D1=nu * Dr, k=1.0, t=t_eq, t_eq=t_eq)
            else:
                reg.update(Dr=Dr, Dt=Dp, D1=nu * Dp, k=math.sqrt(Dp / Dr), t=t)
        regs.append(reg)
    return regs


def recover(smp, reg, p, K_t):
    """Physical planning stresses at a sample (MPa). Ribbed: rib tip, rib root (x K_t), skin radial / hoop at both
    faces, panel between ribs (clamped strip + global hoop skin). Plate: 6 max(|M_r|, |M_t|) / t^2."""
    if reg['kind'] != 'ribbed':
        s = 6.0 * max(abs(smp['Mr']), abs(smp['Mt'])) / reg['t'] ** 2
        return dict(plate=s, governing=s)
    E, nu, t, yc, h = reg['E'], reg['nu'], reg['t_plate'], reg['y_c'], reg['h_a']
    kr, kt = smp['dpsi'], smp['psi'] / smp['r']
    Eb = E / (1.0 - nu * nu)
    tip = E * abs(kr) * (t + h - yc)
    root_nom = max(E * abs(kr * (t - yc)), Eb * abs(kr * (t - yc) + nu * kt * (t / 2.0)))
    skin_r = Eb * max(abs(kr * (0.0 - yc) + nu * kt * (0.0 - t / 2.0)), abs(kr * (t - yc) + nu * kt * (t / 2.0)))
    skin_t = Eb * max(abs(kt * (0.0 - t / 2.0) + nu * kr * (0.0 - yc)), abs(kt * (t / 2.0) + nu * kr * (t - yc)))
    L = max(0.0, reg['s'] - reg['w_a'])
    panel = p * L * L / (2.0 * t * t) + skin_t
    out = dict(rib_tip=tip, rib_root=K_t * root_nom, rib_root_nominal=root_nom, skin_radial=skin_r, skin_hoop=skin_t,
               panel=panel)
    out['governing'] = max(tip, K_t * root_nom, skin_r, skin_t, panel)
    if 't_eq' in reg:
        out['equivalent_plate'] = 6.0 * max(abs(smp['Mr']), abs(smp['Mt'])) / reg['t'] ** 2
    return out


def screen_eval(geo, mats, cfg, screen, N, p, K_t, limits, nsamp=21):
    """One structural screen at one configuration. limits: c_defl (deflection limit), outline_r, z_band_lo,
    rib_top_adv. Returns governing physical stress margin, deflection margins and forbidden-path clearances."""
    regs = str_regions(geo, mats, cfg, screen, N)
    sol = plate_solve(regs, p, 'loaded_boss', 'ss', nsamp)
    worst, wmax, w_in, w_rib, comp, eq = None, 0.0, 0.0, 0.0, {}, 0.0
    for s in sol:
        reg = s['region']
        for smp in s['samples']:
            rec = recover(smp, reg, p, K_t)
            m = reg['sigma_allow'] - rec['governing']
            if worst is None or m < worst[0]:
                worst = (m, rec['governing'], reg['kind'], smp['r'], reg['material'])
            for k, v in rec.items():
                if k != 'governing' and v > comp.get(k, (-1.0,))[0]:
                    comp[k] = (v, smp['r'])
            eq = max(eq, rec.get('equivalent_plate', 0.0))
            aw = abs(smp['w'])
            wmax = max(wmax, aw)
            if smp['r'] <= limits['outline_r'] + EPS:
                w_in = max(w_in, aw)
            if reg['kind'] == 'ribbed':
                w_rib = max(w_rib, aw)
    # rigid pod frame + window boss moves with w(rb): included as the inner-edge sample of the first region
    return dict(screen=screen, N=N, regions=len(regs), stress_margin_MPa=worst[0], sigma_governing_MPa=worst[1],
                governing_region=worst[2], governing_radius_mm=worst[3], governing_material=worst[4],
                components_MPa={k: dict(value=v[0], r_mm=v[1]) for k, v in sorted(comp.items())},
                equivalent_plate_sigma_MPa=eq if screen == 'A' else None,
                w_max_mm=wmax, w_boss_mm=abs(sol[0]['samples'][0]['w']), deflection_margin_mm=limits['c_defl'] - wmax,
                w_inside_outline_mm=w_in, rear_contact_margin_mm=limits['c_defl'] - w_in,
                w_rib_band_mm=w_rib, rib_band_margin_mm=(limits['z_band_lo'] - (limits['rib_top_adv'] + w_rib))
                if limits.get('rib_top_adv') is not None else None,
                pass_=worst[0] >= -EPS and limits['c_defl'] - wmax > EPS)


# --------------------------------------------------------------------------------------------
# Study context: shared geometry, candidates and G4 evaluators (no frozen value re-typed)
# --------------------------------------------------------------------------------------------
class Ctx:
    def __init__(self, st, r1in, g4_res, poses=None):
        self.st, self.I, self.P = st, r1in, r1in['parameters']
        self.g4_res = g4_res
        self.zm = z_model(st)
        self.p = st.G1in['plate_check']['p_test_MPa']['max']
        self.window = g4_res['window']
        self.poses = g4.lra_poses(st) if poses is None else poses
        count(len(self.poses['poses']))
        self.cands = build_candidates(st, r1in)
        self.ce = {}
        for c in self.cands:
            self.ce[c['id']] = g4.CandidateEval(st, c, dict(window=self.window, lra=self.poses))
        pod = st.s14geo['pod_area']
        wf = st.P['w_pod_frame_mm']['nom']
        frame = g4.poly_perimeter(st.s14geo['pod']) * wf + math.pi * wf ** 2
        self.rb = math.sqrt((pod + frame) / math.pi)
        self.r_step = st.s14geo['outline_r'] + st.P['c_hard_stop_mm']['nom']
        cv = st.I['contract_values']['s14']['plan_clearances_mm']
        self.r_s14_clear = st.s14geo['outline_r'] + cv['CHG_CONTACT']
        self.diel_cache = {}

    def diel(self, cand):
        if cand['id'] not in self.diel_cache:
            out = []
            if cand.get('dielectric_sectors'):
                m = cand['dielectric_sector_az_margin_deg']
                for rid in ('GNSS_RAD', 'BLE_RAD', 'WIFI_RAD'):
                    a = g4.res_az(self.st, rid)
                    out.append((rid, ((a[0] - m) % 360.0, (a[1] + m) % 360.0)))
            self.diel_cache[cand['id']] = out
        return self.diel_cache[cand['id']]


def grid(d):
    return frange(d['start'], d['stop'], d['step'])


# --------------------------------------------------------------------------------------------
# L-WIN (OD-G4-WINDOW): verified W1 material screen kept; rib width / tolerance from inputs
# --------------------------------------------------------------------------------------------
def lane_win(cx, cand):
    st, P = cx.st, cx.P['V18_window']
    sp = cx.ce[cand['id']].sp
    G = st.G1in['plate_check']
    p = G['p_test_MPa']['max']
    cells = st.s14geo['cells']
    dims = {k: (max(q[0] for q in v) - min(q[0] for q in v), max(q[1] for q in v) - min(q[1] for q in v)) for k, v in cells.items()}
    big = max(sorted(dims), key=lambda k: (dims[k][0] * dims[k][1], k))
    r_cell = math.hypot(*dims[big]) / 2.0
    standoff = min(c['optical_clearance_mm'] for c in st.s14geo['pod_section']['corners'].values())
    t_nom = P['t_nom_mm']
    t_min = t_nom - st.tolpol['t_window']
    gaps = st.s14_cand['corners']['nominal']['optical']['cell_gaps']
    web = min(g['gap_mm'] for g in gaps)
    rib_nom, rib_tol = P['rib_width_mm'], P['rib_width_tol_mm']
    land = g4.run_check(sp.window_land(), full=False)
    count(4)
    mats = {}
    for mat, g1m in (('sapphire', 'sapphire'), ('cs_glass', 'cs_glass'), ('polycarbonate', 'pc')):
        m = G['materials'][g1m]
        nu, E, sa = m['nu']['max'], m['E_MPa']['min'], m['sigma_allow_MPa']['min']
        w_s, s_s = g1.plate(g1m, p, r_cell, nu, E, t_min, 'ss')
        count()
        mats[mat] = dict(material=mat, t_nominal_mm=t_nom, t_min_mm=t_min, span_radius_mm=r_cell, sigma_ss_MPa=s_s,
                         sigma_allow_min_MPa=sa, stress_margin_MPa=sa - s_s, w_ss_mm=w_s, standoff_mm=standoff,
                         deflection_margin_mm=standoff - w_s, stress_pass=s_s <= sa + 1e-9, deflection_pass=w_s < standoff - 1e-12,
                         planning_screen='PASS' if (s_s <= sa + 1e-9 and w_s < standoff - 1e-12) else 'FAIL')
    zdelta = max(0.0, st.s14geo['pod_section']['window_delta_from_g2_nominal_mm']['%g' % t_nom])
    path = g4.load_paths(cand)
    carried = [mats[m] for m in P['materials']]
    eliminated = [mats[m] for m in P['eliminated_materials']]
    phys = (all(m['stress_pass'] and m['deflection_pass'] for m in carried) and web - rib_nom - rib_tol >= -EPS
            and land >= -EPS and zdelta <= EPS and path['pass_'] and not any(e['stress_pass'] and e['deflection_pass'] for e in eliminated))
    margins = dict(rib_fit_nominal_mm=web - rib_nom, rib_fit_adverse_mm=web - rib_nom - rib_tol, window_bond_land_mm=land,
                   min_stress_MPa=min(m['stress_margin_MPa'] for m in carried),
                   min_deflection_mm=min(m['deflection_margin_mm'] for m in carried), z_delta_mm=zdelta)
    return dict(lane='L-WIN', owner_decision='OD-G4-WINDOW', variant=P['baseline'], t_nominal_mm=t_nom, t_min_mm=t_min,
                largest_cell=big, span_radius_mm=r_cell, min_inter_cell_web_mm=web, rib_width_mm=rib_nom, rib_width_tol_mm=rib_tol,
                materials=mats, margins=margins, z_delta_mm=zdelta, load_path=path,
                rib_load_to_optics_or_rear='none: window ribs are pod-frame ribs; POD_FRAME -> CASEBACK edges only (g4.load_paths)',
                rev_b_lever='0.30 mm sapphire not credited', physical_pass=phys,
                disposition='SUPPLIER_GATED' if phys else 'OWNER_GATED', gates=['SR-WINDOW', 'MG-WINDOW-XTALK'],
                qualification='No structural, optical, adhesive or 5 ATM qualification is implied; material and supplier qualification remain open.')


# --------------------------------------------------------------------------------------------
# L-RAD: rcin / tcw solved from their predicates; azimuth-resolved wall (C-R1-04); H05-GEOM vs H05-LRA-COUPLED
# --------------------------------------------------------------------------------------------
def solve_carrier(cx, ce):
    """Smallest grid R_carrier_inner with H10-PACK-RADIAL >= 0 and smallest grid carrier wall with H10-CARRIER-WALL
    >= 0, with the monotonicity used for the solve tested on the whole grid."""
    V = cx.P['V23_carrier']
    rc_grid, tcw_grid = grid(V['R_carrier_inner']), grid(V['t_carrier_wall'])
    pack = [(r, ce.f['pack'](R_carrier_inner=r)) for r in rc_grid]
    wall = [(t, g4.run_check(ce.sp.carrier_wall(dict(ce.dp0, tcw=t)), full=False)) for t in tcw_grid]
    count(len(pack) + len(wall))
    mono = all(b[1] > a[1] for a, b in zip(pack, pack[1:])) and all(b[1] > a[1] for a, b in zip(wall, wall[1:]))
    if not mono:
        raise StudyError('pack / carrier-wall monotonicity assumption violated')
    rcin = next((r for r, m in pack if m >= -EPS), None)
    tcw = next((t for t, m in wall if m >= -EPS), None)
    if rcin is None or tcw is None:
        raise StudyError('no carrier radius / wall satisfies the G4 pack-growth predicate on the grid')
    return dict(rcin=rcin, tcw=tcw, pack_rows=[dict(R_carrier_inner=r, margin_mm=m) for r, m in pack],
                wall_rows=[dict(t_carrier_wall=t, margin_mm=m) for t, m in wall], monotone=mono,
                pack_margin_mm=dict(pack)[rcin], wall_margin_mm=dict(wall)[tcw],
                grids_equal_g4=(rc_grid == ce.grid['rcin'] and tcw_grid == ce.grid['tcw']))


def arc_defs(cx, cand):
    """Local arcs over the frozen corridor reservations; local material / process from the dielectric-sector map."""
    st, V = cx.st, cx.P['V03_corridor_arcs']
    sp = cx.ce[cand['id']].sp
    out = []
    for rid in V['reservations']:
        a0, a1 = st.res[rid]['geometry']['az']
        arc = ((a0 - V['arc_extension_deg']) % 360.0, (a1 + V['arc_extension_deg']) % 360.0)
        in_diel = any(g4.arc_gap(arc, d[1]) <= 0.0 for d in cx.diel(cand))
        if in_diel:
            pc = st.I['process_classes'][cand['dielectric_sector_process']]
            m = st.I['material_classes'][cand['dielectric_sector_material']]
            mat = cand['dielectric_sector_material']
        else:
            pc, m, mat = sp.pc_mid, sp.m_mid, cand['midcase']['material']
        floor = m['t_wall_min_mm']['max'] + pc['radius_mm'] + pc['od_radius_mm']
        out.append(dict(reservation=rid, crossing=V['crossing_by_reservation'][rid], corridor_az=[a0, a1], arc_az=list(arc),
                        span_deg=(arc[1] - arc[0]) % 360.0, local_material=mat, local_process=pc['title'], in_dielectric_sector=in_diel,
                        tol_bore_r=pc['radius_mm'], tol_od_r=pc['od_radius_mm'], t_wall_min=m['t_wall_min_mm']['max'],
                        floor_mm=floor, sigma_allow_min=m['sigma_allow_MPa']['min'], pc=pc, m=m))
    return out


def arc_eval(cx, cand, D, a, t, R, rc, tcw):
    """Production predicates of one local arc (C-R1-04) at local wall thickness t (V03). Own predicates:
    decreasing in t (radial room: edge, straight, t_allow, insertion through the arc) and increasing in t (local wall,
    hoop and panel screens). The crossing envelope and the Z extent do not depend on t."""
    st = cx.st
    ce = cx.ce[cand['id']]
    sp, f = ce.sp, ce.f
    tolb = sp.pc_env['radius_mm']
    c_fpc, c_ins = st.rp['c_fpc']['max'], st.P['c_insert_mm']['max']
    Ra = D / 2.0 - t
    loc = copy.copy(sp)
    loc.pc_mid, loc.m_mid = a['pc'], a['m']
    wall = g4.run_check(loc.wall(dict(ce.dp0, tw=t), t, 'R1-WALL-ARC-' + a['reservation']), full=False)
    edge = f['edge_' + a['crossing']](R_side=Ra, tol_bore_r=a['tol_bore_r'], R_carrier_inner=rc, t_carrier_wall=tcw)
    straight = f['straight'](R_side=Ra, tol_bore_r=a['tol_bore_r'], R_carrier_inner=rc, t_carrier_wall=tcw)
    tallow = f['tallow'](R_side=Ra, tol_bore_r=a['tol_bore_r'], R_carrier_inner=rc, t_carrier_wall=tcw) if a['crossing'] == 'XC-J202' else None
    env = Ra - a['tol_bore_r'] - c_fpc - edge
    ins_mb = (R - tolb) - (env + c_ins)
    ins_mbr = (Ra - a['tol_bore_r']) - (env + c_ins)
    extent = 'MAIN_BATTERY' if ins_mb >= -EPS else 'THROUGH_REAR_FACE'
    t_adv = t - a['tol_od_r'] - a['tol_bore_r']
    hoop = cx.p * (D / 2.0) / t_adv
    b_panel = min(2.0 * (D / 2.0) * math.sin(math.radians(a['span_deg'] / 2.0)),
                  sum(st.layer(k) for k in ('main_pcb', 'back_zone', 'battery_zone', 'lower_web')))
    panel = cx.p * b_panel ** 2 / (2.0 * t_adv ** 2)
    count(5)
    ins = ins_mb if extent == 'MAIN_BATTERY' else ins_mbr
    dec = dict(edge=edge, straight=straight, **({'t_allow': tallow} if tallow is not None else {}),
               **({'insertion': ins_mbr} if extent == 'THROUGH_REAR_FACE' else {}))
    return dict(reservation=a['reservation'], crossing=a['crossing'], arc_az=a['arc_az'], t_arc_mm=t, floor_mm=a['floor_mm'],
                local_material=a['local_material'], in_dielectric_sector=a['in_dielectric_sector'], R_bore_arc_mm=Ra,
                wall_margin_mm=wall, edge_margin_mm=edge, straight_margin_mm=straight, t_allow_margin_mm=tallow,
                crossing_envelope_r_mm=env, insertion_through_bulk_rear_mm=ins_mb, insertion_through_arc_rear_mm=ins_mbr,
                z_extent=extent, insertion_margin_mm=ins,
                hoop_stress_MPa=hoop, hoop_margin_MPa=a['sigma_allow_min'] - hoop, panel_span_mm=b_panel,
                panel_stress_MPa=panel, panel_margin_MPa=a['sigma_allow_min'] - panel,
                panel_model='clamped strip p b^2 / (2 t^2), b = min(arc chord, MAIN + BATTERY Z span)',
                own_decreasing_mm=dec, own_min_mm=min([wall, ins] + list(dec.values())),
                own_pass=wall >= -EPS and ins >= -EPS and all(v >= -EPS for v in dec.values())
                and a['sigma_allow_min'] - hoop >= -EPS and a['sigma_allow_min'] - panel >= -EPS)


def arc_grid(cx, a, tw):
    """V03 grid: floor .. tw step 0.02 (floor included); a bulk wall thinner than the floor leaves the arc at tw."""
    step = cx.P['V03_corridor_arcs']['step_mm']
    if a['floor_mm'] > tw + EPS:
        return [tw]
    n = int(math.floor((tw - a['floor_mm']) / step + 1e-9))
    return [round(a['floor_mm'] + k * step, 9) for k in range(n + 1)]


def arc_search(cx, cand, D, tw, a, R, rc, tcw):
    """R2-2 / V03 local-wall search with an exact reduction. Every decreasing own predicate is affine in t with slope -1
    (R_side = D/2 - t enters each with coefficient +1: edge, straight, t_allow, insertion through the arc) and the wall
    predicate is affine with slope +1 (t - tolerances - t_min); hoop and panel stresses fall strictly with t. Hence the own-
    feasible set on the V03 grid is the interval [t_lo, t_hi] with t_hi from the decreasing minimum at the first grid point
    and t_lo the first grid point where wall / hoop / panel pass. Coupled predicates are monotone in t: the rear-face seal
    annulus (t - tolerances) and the radial spigot's continuous bore rise with t, and the structural plate radius
    D/2 - t + tol falls with t (exhaustively re-screened over the admissible interval by struct_point). Selection: an arc
    running through the rear face takes t_hi (coupling-optimal); an arc inside MAIN / BATTERY has no coupled predicate and
    takes the grid maximum of its minimum own mm margin (ties to the thinner wall); with an empty interval the arc is
    diagnostic (same max-min rule over the whole grid) and H05-GEOM fails at that point for every arc thickness. The affine
    model is verified with production predicates at the last grid point, the selected point and the t_hi bracket; any
    disagreement is a STOP."""
    G = arc_grid(cx, a, tw)
    step = cx.P['V03_corridor_arcs']['step_mm']
    r0 = arc_eval(cx, cand, D, a, G[0], R, rc, tcw)
    w0, d0 = r0['wall_margin_mm'], min(r0['own_decreasing_mm'].values())
    s_all = r0['own_decreasing_mm']

    def model(k):
        return dict(wall=w0 + (G[k] - G[0]), dec=d0 - (G[k] - G[0]))

    def stress_ok(t):
        t_adv = t - a['tol_od_r'] - a['tol_bore_r']
        hoop = cx.p * (D / 2.0) / t_adv
        panel = cx.p * r0['panel_span_mm'] ** 2 / (2.0 * t_adv ** 2)
        return a['sigma_allow_min'] - hoop >= -EPS and a['sigma_allow_min'] - panel >= -EPS
    ins_c = r0['insertion_margin_mm'] if r0['z_extent'] == 'MAIN_BATTERY' else None
    lo = next((k for k in range(len(G)) if model(k)['wall'] >= -EPS and stress_ok(G[k])), None)
    hi = max((k for k in range(len(G)) if model(k)['dec'] >= -EPS), default=None)
    feasible = lo is not None and hi is not None and lo <= hi and (ins_c is None or ins_c >= -EPS)

    def mm_min(k):
        v = model(k)
        return min(v['wall'], v['dec'])   # the bulk-path insertion of a MAIN_BATTERY arc is t-independent (feasibility only)
    if feasible and r0['z_extent'] == 'THROUGH_REAR_FACE':
        sel, rule = hi, 'THROUGH_REAR_FACE: t_hi (coupled seal annulus / continuous bore rise and the plate radius falls with t)'
    else:
        rng = range(lo, hi + 1) if feasible else range(len(G))
        sel = max(rng, key=lambda k: (round(mm_min(k), 9), -k))
        rule = ('MAIN_BATTERY: grid max-min own mm margin (no coupled predicate)' if feasible else
                'DIAGNOSTIC: empty own-feasible interval; H05-GEOM fails for every arc thickness at this point')
    rs = r0 if sel == 0 else arc_eval(cx, cand, D, a, G[sel], R, rc, tcw)
    checks = [(sel, rs)]
    if len(G) > 1 and sel != len(G) - 1:
        checks.append((len(G) - 1, arc_eval(cx, cand, D, a, G[-1], R, rc, tcw)))
    if hi is not None and hi + 1 < len(G) and hi + 1 not in (k for k, _ in checks):
        checks.append((hi + 1, arc_eval(cx, cand, D, a, G[hi + 1], R, rc, tcw)))
    for k, rk in checks:
        mk = model(k)
        if abs(rk['wall_margin_mm'] - mk['wall']) > 1e-9 or any(abs(rk['own_decreasing_mm'][n] - (s_all[n] - (G[k] - G[0]))) > 1e-9
                                                                for n in s_all) \
                or abs(rk['crossing_envelope_r_mm'] - r0['crossing_envelope_r_mm']) > 1e-9 or rk['z_extent'] != r0['z_extent']:
            raise StudyError('STOP: V03 affine reduction not reproduced by the production predicates (%s, t %.3f)' % (a['reservation'], G[k]))
        if hi is not None and k == hi + 1 and min(rk['own_decreasing_mm'].values()) >= -EPS:
            raise StudyError('STOP: V03 t_hi bracket not confirmed by the production predicates (%s)' % a['reservation'])
    out = dict(rs)
    out['search'] = dict(grid_n=len(G), grid_mm=[G[0], G[-1]], step_mm=step if len(G) > 1 else None, feasible=feasible,
                         t_lo_mm=G[lo] if lo is not None else None, t_hi_mm=G[hi] if hi is not None else None, t_selected_mm=G[sel],
                         admissible_mm=[G[k] for k in range(lo, hi + 1)] if feasible else [],
                         rule=rule, diagnostic=not feasible,
                         at_floor=dict(t_mm=G[0], wall_margin_mm=w0, edge_margin_mm=r0['edge_margin_mm'], straight_margin_mm=r0['straight_margin_mm'],
                                       t_allow_margin_mm=r0['t_allow_margin_mm'], insertion_margin_mm=r0['insertion_margin_mm']),
                         verified_points_mm=sorted(G[k] for k, _ in checks))
    return out


def rad_point(cx, cand, D, tw, carrier, arcs=None, chk=None):
    """Radial / core predicates at (D, tw): H05-GEOM terms at the bulk wall and at the local arcs (V03 search), H05-LRA-
    COUPLED terms, insertion envelopes (bulk, arc crossing envelopes through the REAR level) and side-wall screens."""
    st = cx.st
    ce = cx.ce[cand['id']]
    sp, f = ce.sp, ce.f
    arcs = arcs if arcs is not None else arc_defs(cx, cand)
    rc, tcw = carrier['rcin'], carrier['tcw']
    R = D / 2.0 - tw
    tolb = sp.pc_env['radius_mm']
    lw = ce.land['t_land']
    m = {}
    m['H03-OD'] = f['od'](D=D)
    m['H05-WALL-SIDE'] = f['wall'](t_wall=tw)
    if cand.get('dielectric_sectors'):
        m['H05-WALL-DIELECTRIC'] = g4.run_check(sp.local_wall(dict(ce.dp0, tw=tw)), full=False)
    m['H05-MAIN-CASE'] = f['main'](R_side=R)
    for x in ('XF-J1501', 'XB-J201', 'XC-J202'):
        m['H05-EDGE-Z-' + x] = f['edgez_' + x](t_land=lw)
    ins = dict(MAIN=f['ins_main'](R_side=R), BATTERY=f['ins_bat'](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw))
    r_rear = max([st.s14geo['outline_r']] + [st.g2res[k]['geometry']['r'][1] for k in st.g2res
                                             if 'REAR' in st.g2res[k]['z_levels'] and st.g2res[k]['geometry']['type'] == 'sector']
                 + [st.res[k]['geometry']['r'][1] for k in ('CHG_ROUTE', 'CHG_LINK')])
    ins['REAR'] = f['ins_rear'](R_side=R, r_rear_module=r_rear)
    g4_literal = dict(straight_bulk=f['straight'](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw),
                      **{'edge_bulk_' + x: f['edge_' + x](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw) for x in ('XF-J1501', 'XB-J201', 'XC-J202')},
                      ins_rear_charger_module_carried=f['ins_rear'](R_side=R, r_rear_module=max(st.s14geo['outline_r'], min(st.res['CHG_CONTACT']['radial_mm'][1], R - tolb))))
    arc_rows = [arc_search(cx, cand, D, tw, a, R, rc, tcw) for a in arcs]
    for a in arc_rows:
        m['R1-WALL-ARC-' + a['reservation']] = a['wall_margin_mm']
        m['H05-EDGE-' + a['crossing']] = a['edge_margin_mm']
        m['H05-STRAIGHT@' + a['reservation']] = a['straight_margin_mm']
        if a['t_allow_margin_mm'] is not None:
            m['H05-T-ALLOW-XC'] = a['t_allow_margin_mm']
    screens = {}
    for r_ in arc_rows:
        screens['R1-ARC-HOOP-' + r_['reservation']] = r_['hoop_margin_MPa']
        screens['R1-ARC-PANEL-' + r_['reservation']] = r_['panel_margin_MPa']
    lra = {'H05-STRAIGHT@U7-RISER': f['straight'](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw),
           'H05-EDGE-XL-LRA': f['edge_XL-LRA'](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw),
           'H05-EDGE-Z-XL-LRA': f['edgez_XL-LRA'](t_land=lw)}
    insm = dict(('H23-INSERT-' + k, v) for k, v in ins.items())
    insm.update({'R1-INSERT-ARC-' + r['reservation']: r['insertion_margin_mm'] for r in arc_rows})
    count(len(m) + len(lra) + len(insm) + len(g4_literal))
    geom_keys = sorted(k for k in m if k != 'H03-OD')
    return dict(D=D, tw=tw, R_side=R, rcin=rc, tcw=tcw, margins=m, lra_coupled=lra, insertion=insm, arcs=arc_rows,
                g4_literal=g4_literal, r_rear_module_mm=r_rear, wall_screens_MPa=screens,
                h05_geom_terms=geom_keys, h05_geom_min=min(m[k] for k in geom_keys),
                h05_geom_pass=all(m[k] >= -EPS for k in geom_keys) and all(v >= -EPS for v in screens.values()),
                od_pass=m['H03-OD'] >= -EPS, insertion_pass=all(v >= -EPS for v in insm.values()),
                lra_coupled_min=min(lra.values()))


def rad_tw(cx, cand, D, carrier, arcs):
    """Bulk-wall choice (pure ranking): every non-LRA radial / insertion predicate passing first; then the LRA-coupled
    lateral terms (straight at the U7 riser, XL lateral) passing where geometry allows, so the L-LRA lane is not
    penalised by the wall choice; then the thickest wall (seal annulus / plate span). Without a passing wall the row
    with the largest minimum non-LRA margin is kept as a diagnostic."""
    rows = [rad_point(cx, cand, D, tw, carrier, arcs) for tw in grid(cx.P['V02_tw_bulk'])]
    ok = [r for r in rows if r['h05_geom_pass'] and r['insertion_pass']]
    if ok:
        lat = lambda r: r['lra_coupled']['H05-STRAIGHT@U7-RISER'] >= -EPS and r['lra_coupled']['H05-EDGE-XL-LRA'] >= -EPS
        return max(ok, key=lambda r: (lat(r), r['tw'])), rows
    return max(rows, key=lambda r: (min(r['h05_geom_min'], min(r['insertion'].values())), -r['tw'])), rows


# --------------------------------------------------------------------------------------------
# L-BTN: one common radial section per switch (C-R1-02 enumerated stack, both C-R1-03 interpretations)
# --------------------------------------------------------------------------------------------
def btn_terms(cx, cand, sw):
    st, P = cx.st, cx.P
    sp = cx.ce[cand['id']].sp
    B = st.P['buttons']
    pc = sp.button_process(sw)
    poly = sw == 'SW5' and cand.get('dielectric_sectors')
    mat = st.I['material_classes'][cand['dielectric_sector_material']] if poly else sp.m_mid
    return dict(sw=sw, R_main=st.R_main, tol_pcb=sp.pc_pcb['radius_mm'], c_main_case=st.P['c_main_case_mm']['max'],
                c_switch=B['c_switch_mm']['max'], tol_bore=pc['radius_mm'], tol_od=pc['od_radius_mm'], tol_boss=pc['boss_mm'],
                guide=B['guide_land_each_mm']['max'], core=B['core_radius_min_mm']['max'], wall_min=mat['t_wall_min_mm']['max'],
                window=tuple(B['windows_deg'][sw]), shoulder=P['V09_guide_stack']['shoulder_mm'], rim=P['V07_boot_rim_land']['adverse_mm'],
                h_boot=P['V08_boot']['free_height_mm'], strain_max=P['V08_boot']['strain_hard_max'], c_insert=st.P['c_insert_mm']['max'],
                boss_limit=st.I['contract_values']['owner_limits']['boss_extension_max_mm'], local_process=pc['title'],
                local_material=cand['dielectric_sector_material'] if poly else cand['midcase']['material'])


def btn_section(T, D, topo, boss, dp, interp):
    """Common radial / Z button section at linear worst. Terms are never omitted: c_main_case and c_switch are both
    required (I-SUM in series, I-MAX as max); the rim / groove term is always in the bore stack (LA-BTN-1)."""
    count()
    for k in ('c_main_case', 'c_switch', 'rim', 'guide', 'shoulder', 'tol_bore', 'tol_boss', 'tol_od'):
        if T.get(k) is None:
            raise StudyError('button section term dropped: ' + k)
    if topo not in ('T2-R', 'T2-F'):
        raise StudyError('T2 section requested for ' + topo)
    gap = T['c_main_case'] + T['c_switch'] if interp == 'I-SUM' else max(T['c_main_case'], T['c_switch'])
    R_in = T['R_main'] + T['tol_pcb'] + gap + T['tol_bore']
    R_face = D / 2.0 - T['tol_od'] + boss - T['tol_boss']
    stroke = T['c_switch']
    stack = [('guide_land_inner', T['guide'], 'SUPPLIER_GATED'), ('stop_shoulder', T['shoulder'], 'DESIGN'),
             ('stroke', stroke, 'SUPPLIER_GATED'), ('guide_land_outer', T['guide'], 'SUPPLIER_GATED'),
             ('rim_groove', T['rim'], 'PROVISIONAL')]
    if topo == 'T2-R':
        stack.append(('boot_free_height_in_counterbore', T['h_boot'], 'PROVISIONAL'))
    L_req = sum(v for _, v, _ in stack)
    L_av = R_face - R_in
    protrusion = boss + T['tol_boss'] + (T['h_boot'] if topo == 'T2-F' else 0.0)
    half_w = dp / 2.0 + T['tol_bore'] + T['rim'] + T['wall_min'] + T['tol_boss']
    w_half = (T['window'][1] - T['window'][0]) / 2.0
    chord_half = (D / 2.0) * math.sin(math.radians(w_half))
    boss_half_deg = math.degrees(math.asin(min(1.0, half_w / (D / 2.0))))
    profile = [('guide_bore', R_in, R_face - T['rim'] - (T['h_boot'] if topo == 'T2-R' else 0.0), dp + 2 * T['tol_bore']),
               ('rim_seat', R_face - T['rim'] - (T['h_boot'] if topo == 'T2-R' else 0.0), R_face, dp + 2 * T['rim'])]
    monotone = a9_insertable(profile)
    m = dict(bore_stack=L_av - L_req, protrusion=T['boss_limit'] - protrusion, strain=T['strain_max'] - stroke / T['h_boot'],
             stroke_vs_c_switch=stroke - T['c_switch'], tangential=chord_half - half_w,
             core=dp / 2.0 - T['tol_bore'] - T['core'],
             no_inward_lip=R_in - (T['R_main'] + T['tol_pcb'] + T['c_insert']))
    pred = dict(a9_radial_insertion_from_outside=monotone)
    return dict(topology=topo, interpretation=interp, boss=boss, d_p=dp, R_inner=R_in, R_face=R_face, L_available=L_av, L_required=L_req,
                stack=[dict(term=n, value=v, role=r) for n, v, r in stack], protrusion_mm=protrusion, half_width_mm=half_w,
                boss_half_deg=boss_half_deg, window_half_deg=w_half, stroke=stroke, boot_strain=stroke / T['h_boot'],
                a9_profile=[dict(segment=s, r0=a, r1=b, dia=d) for s, a, b, d in profile], margins=m, predicates=pred,
                margin_units=dict((k, BTN_MARGIN_UNITS.get(k, 'mm')) for k in m), min_margin=min(v for k, v in m.items() if BTN_MARGIN_UNITS.get(k, 'mm') == 'mm'),
                min_margin_units='mm', strain_margin=m['strain'], pass_=all(v >= -EPS for v in m.values()) and all(pred.values()))


# R5 audit (no cross-unit minimum anywhere): every T2 section margin is a length except the dimensionless boot strain; min_margin is the
# minimum over the mm margins, the strain margin is carried and ranked as its own component; pass_ still needs every margin >= 0
BTN_MARGIN_UNITS = dict(strain='dimensionless')


def a9_insertable(profile):
    """A9: the stepped bore profile (inside -> outside) must be non-decreasing in diameter so the plunger enters radially
    from outside and no inward lip blocks it."""
    return all(b[3] >= a[3] - EPS for a, b in zip(profile, profile[1:])) and all(p[2] >= p[1] - EPS for p in profile)


def btn_grid(cx, T):
    bosses = [b for b in grid(cx.P['V04_boss_extension']) if b + T['tol_boss'] <= T['boss_limit'] + EPS]
    return bosses, grid(cx.P['V06_pusher_dp'])


def btn_best(cx, T, D, topo, interp, full):
    """Best (max min-margin) section. full=False uses the monotone reduction (tested against the full grid at the
    evaluated point): bore margin rises with boss, tangential margin falls with d_p, T2-F protrusion rises with boss."""
    bosses, dps = btn_grid(cx, T)
    if full:
        cand = [(b, d) for b in bosses for d in dps]
    elif topo == 'T2-R':
        cand = [(bosses[-1], dps[0])]
    else:
        cand = [(b, dps[0]) for b in bosses]
    best = None
    for b, d in cand:
        s = btn_section(T, D, topo, b, d, interp)
        key = (s['pass_'], s['min_margin'], s['strain_margin'], -b, -d)
        if best is None or key > best[0]:
            best = (key, s)
    return best[1]


def t3_flexure(cx, cand, T, D):
    """LA-BTN-2: T3 only with a complete flexure model and authored minimum-web evidence; otherwise NOT_SELECTABLE
    with the governing threshold sigma = 2 E delta t / ((1 - nu^2) a^2) <= sigma_allow -> t_web_max."""
    st = cx.st
    eligible = cand['midcase']['material'] == 'MAT-NF-METAL' and not (T['sw'] == 'SW5' and cand.get('dielectric_sectors'))
    if not eligible:
        return dict(status='NOT_ELIGIBLE', reason='T3 requires a non-ferromagnetic metal midcase at the switch (SW1-SW4 of a metal midcase only)')
    m = st.I['material_classes']['MAT-NF-METAL']
    E, nu, sa = m['E_MPa']['max'], m['nu']['max'], m['sigma_allow_MPa']['min']
    chord_half = (D / 2.0) * math.sin(math.radians((T['window'][1] - T['window'][0]) / 2.0))
    a = chord_half - T['wall_min'] - T['tol_boss']
    delta = T['c_switch']
    t_max = sa * (1.0 - nu * nu) * a * a / (2.0 * E * delta)
    ev = cx.P['T3_flexure']
    if ev['min_web_mm'] is None or ev['min_web_evidence'] is None:
        return dict(status='NOT_SELECTABLE', reason='no authored machining minimum web (inputs T3_flexure.min_web_mm = null); topology unproven',
                    flexure_radius_max_mm=a, stroke_mm=delta, E_max_MPa=E, nu_max=nu, sigma_allow_min_MPa=sa,
                    required_web_thickness_max_mm=t_max, physical_pass=None,
                    threshold='a manufacturable web must be <= %.4f mm thick to keep sigma <= %.0f MPa at the %.2f mm stroke' % (t_max, sa, delta))
    t = ev['min_web_mm']
    sigma = 2.0 * E * delta * t / ((1.0 - nu * nu) * a * a)
    return dict(status='SELECTABLE' if sigma <= sa else 'FAIL', sigma_MPa=sigma, margin_MPa=sa - sigma, web_mm=t,
                required_web_thickness_max_mm=t_max, physical_pass=sigma <= sa)


def btn_materials(cx, cand, T, D, sec):
    """Plunger / boot / boss feature records; material choice follows the keep-out rules and is verified by
    g4.rf_mag_check (SW5 WIFI_RAD non-conductive, SW4 MAG_CLEAR non-ferromagnetic, SW1 conductive parts outside BLE_RAD)."""
    st = cx.st
    c = (T['window'][0] + T['window'][1]) / 2.0
    half_bore = math.degrees(math.asin(min(1.0, (sec['d_p'] / 2.0 + T['tol_bore']) / sec['R_inner'])))
    bore = g4.sector(c - half_bore, c + half_bore, sec['R_inner'], sec['R_face'])
    boss = g4.sector(c - sec['boss_half_deg'], c + sec['boss_half_deg'], D / 2.0 - 0.0, D / 2.0 + sec['boss'] + T['tol_boss'])
    rad = [r for r in ('GNSS_RAD', 'BLE_RAD', 'WIFI_RAD') if 'MAIN' in st.res[r]['z_levels'] and g4.overlaps(bore, st.res[r]['geometry'])]
    in_mag = g4.overlaps(bore, st.res['MAG_CLEAR']['geometry'])
    count(4)
    nonc = bool(rad)
    poly_boss = T['sw'] == 'SW5' and cand.get('dielectric_sectors')
    metal_mid = cand.get('conductive_midcase', False)
    lvl = ['MAIN']
    zf = zfeat(*level_z(st)['MAIN'])
    feats = [feature(T['sw'] + '_PLUNGER', 'L-BTN', 'POLYMER (non-conductive)' if nonc else 'MAT-NF-METAL', not nonc, False, bore, lvl, zf, 'pusher'),
             feature(T['sw'] + '_BOOT', 'L-BTN', 'ELASTOMER (non-conductive)', False, False, boss, lvl, zf, 'button boot'),
             feature(T['sw'] + '_BOSS', 'L-BTN', T['local_material'], metal_mid and not poly_boss, False, boss, lvl, zf, 'button boss')]
    # Material rule (a requirement, verified by g4.rf_mag_check over these records): every plunger / boot is specified
    # non-ferromagnetic; plungers in a radiator volume are specified non-conductive.
    return dict(rule=dict(radiators=rad, mag_clear=in_mag, plunger_nonconductive=nonc, nonferromagnetic_specified=all(not f['ferromagnetic'] for f in feats)),
                features=feats)


def btn_disposition(sum_ok, max_ok, adj):
    """C-R1-03 rule: PASS under both -> closed (supplier-gated); I-MAX only -> reviewer adjudication required and not
    closed unless the reviewed input selects MAX; otherwise owner-gated (R1-S03)."""
    if sum_ok and max_ok:
        return 'SUPPLIER_GATED'
    if max_ok and adj == 'MAX':
        return 'SUPPLIER_GATED'
    if max_ok and adj is None:
        return 'RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED'
    return 'OWNER_GATED'


def lane_btn(cx, cand, D, full=True):
    st = cx.st
    adj = cx.I.get('c_r1_03_adjudication')
    if adj not in (None, 'SUM', 'MAX'):
        raise StudyError('c_r1_03_adjudication must be null / "SUM" / "MAX"')
    sp = cx.ce[cand['id']].sp
    rows = {}
    for sw in sorted(st.P['buttons']['windows_deg']):
        T = btn_terms(cx, cand, sw)
        res = {}
        for topo in ('T2-R', 'T2-F'):
            res[topo] = {i: btn_best(cx, T, D, topo, i, full) for i in ('I-SUM', 'I-MAX')}
        best = {i: max((res[t][i] for t in res), key=lambda s: (s['pass_'], s['min_margin'], s['strain_margin'], s['topology'] == 'T2-R'))
                for i in ('I-SUM', 'I-MAX')}
        bosses, _ = btn_grid(cx, T)
        legacy = g4.fast(sp.bore(dict(D=D), sw, bosses[-1]))(D=D, boss=bosses[-1])
        count()
        mats = btn_materials(cx, cand, T, D, best['I-SUM'])
        pg_best, _ = g4.pusher_gland(st, sp, sw, not mats['rule']['plunger_nonconductive'])
        t3 = t3_flexure(cx, cand, T, D) if full else None
        thr = {}
        for topo in ('T2-R', 'T2-F'):
            s = res[topo]['I-SUM']
            if topo == 'T2-R':
                thr[topo] = dict(required_D_mm=D + 2.0 * max(0.0, -s['margins']['bore_stack']),
                                 required_boss_mm=s['boss'] + max(0.0, -s['margins']['bore_stack']))
            else:
                b_need = s['boss'] + max(0.0, -s['margins']['bore_stack'])
                thr[topo] = dict(boss_needed_for_bore_mm=b_need,
                                 max_boot_free_height_mm=T['boss_limit'] - T['tol_boss'] - b_need,
                                 required_strain_allowance=T['c_switch'] / max(1e-9, T['boss_limit'] - T['tol_boss'] - b_need)
                                 if T['boss_limit'] - T['tol_boss'] - b_need > 0 else None)
        rows[sw] = dict(sw=sw, window_deg=list(T['window']), local_process=T['local_process'], local_material=T['local_material'],
                        terms={k: v for k, v in T.items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
                        T2=res, best=best, pass_I_SUM=best['I-SUM']['pass_'], pass_I_MAX=best['I-MAX']['pass_'],
                        legacy_G4_bore_margin_mm=legacy, legacy_zero_margin_L_bore_mm=legacy + st.P['buttons']['L_bore_min_mm']['max'],
                        T1=dict(selectable=False, regression='dynamic radial pusher O-ring (g4.pusher_gland)', cs=pg_best['cs'],
                                margins=pg_best['margins'], pass_=pg_best['pass_']),
                        T3=t3, materials=mats, thresholds=thr)
    sum_ok = all(r['pass_I_SUM'] for r in rows.values())
    max_ok = all(r['pass_I_MAX'] for r in rows.values())
    t3_sel = [sw for sw, r in rows.items() if r['T3'] and r['T3']['status'] == 'SELECTABLE']
    disp = btn_disposition(sum_ok, max_ok, adj)
    closed = disp == 'SUPPLIER_GATED'
    return dict(lane='L-BTN', D=D, c_r1_03_adjudication=adj, binding_interpretation='I-MAX' if adj == 'MAX' else 'I-SUM',
                switches=rows, all_pass_I_SUM=sum_ok, all_pass_I_MAX=max_ok, t1_selectable=False, t3_selectable=t3_sel,
                closed=closed, disposition=disp, physical_pass=closed,
                selected_topology={sw: (r['best']['I-SUM']['topology'] if closed else None) for sw, r in rows.items()},
                gates=['SR-BUTTONS'] if closed else ['SR-BUTTONS', 'R1-S03'],
                note='Switches frozen at their G2 windows; T1 regression only; T3 requires authored minimum-web evidence (LA-BTN-2).')


def frozen_switches_ok(st):
    """Switch windows equal the frozen architecture SW1-SW5 reservations (switches never move)."""
    return all(list(st.P['buttons']['windows_deg'][sw]) == list(st.res[sw]['geometry']['az']) for sw in st.P['buttons']['windows_deg'])


def frozen_seal_windows_ok(st, g4_input):
    """O-ring planning windows and the +/-0.05 cross-section tolerance equal the accepted G4 values (never widened or
    narrowed)."""
    o, ref = st.P['oring'], g4_input['parameters']['oring']
    return o['windows'] == ref['windows'] and o['cs_tolerance_mm'] == ref['cs_tolerance_mm']


# --------------------------------------------------------------------------------------------
# L-SEAL: main caseback seal topology search (face / adhesive / radial) with explicit flange and Z
# --------------------------------------------------------------------------------------------
def annulus_rows(cx, cand, row):
    """Azimuth-resolved midcase rear-face annulus (bulk, dielectric sectors, arcs that run through the rear face)."""
    sp = cx.ce[cand['id']].sp
    st = cx.st
    out = [dict(where='bulk %s' % cand['midcase']['material'], value=row['tw'] - sp.pc_mid['od_radius_mm'] - sp.pc_mid['radius_mm'])]
    if cand.get('dielectric_sectors'):
        pc = st.I['process_classes'][cand['dielectric_sector_process']]
        out.append(dict(where='dielectric sectors', value=row['tw'] - pc['od_radius_mm'] - pc['radius_mm']))
    for a in row['arcs']:
        if a['z_extent'] == 'THROUGH_REAR_FACE':
            pc = st.I['process_classes']['PC-POLY-MOULD' if a['local_material'] == 'MAT-GF-POLY' else
                                         ('PC-METAL-MACH' if a['local_material'] == 'MAT-NF-METAL' else cand['midcase']['process'])]
            out.append(dict(where='arc ' + a['reservation'], value=a['t_arc_mm'] - pc['od_radius_mm'] - pc['radius_mm']))
    return out


def seal_t_out_min(cx, sp):
    tmin = sp.m_cb['t_wall_min_mm']['max'] + sp.pc_cb['thickness_mm']
    return next(t for t in grid(cx.P['V12_caseback_thickness']['t_out']) if t >= tmin - EPS)


def gland_cached(cx, cand, sp, topo, cs):
    """g4.gland_design + g4 gland specs (independent of D and tw); cached per context."""
    cache = cx.__dict__.setdefault('gland_cache', {})
    key = (cand['id'], topo, round(cs, 6))
    if key not in cache:
        gd = g4.gland_design(cx.st, sp, topo, cs)
        gm = [g4.run_check(x, full=False) for x in sp.gland('R1-CB-MAIN', 'static_radial' if topo == 'radial' else 'static_face',
                                                             gd['cs'], gd['h'], gd['g'], gd['tol_h'], gd['tol_g'])]
        cache[key] = (gd, gm)
    return cache[key]


# R5: the seal / flange population is evaluated in an internal length unit (canonical mm; a regression test may set cx.seal_unit to
# 'm' or 'um'): every length enters scaled, every length predicate tolerance scales with it, every reduction is taken on one quantity
# at a time, and the record leaves in mm. Physical results never depend on a single "representative" / "best" row.
SEAL_UNITS = {'mm': 1.0, 'm': 1e-3, 'um': 1e3}
SEAL_PREFERENCE = ('face', 'radial', 'adhesive')  # serviceable topologies first (face = brief 6.3 baseline), then the adhesive ring
SEAL_DISPLAY_OVERRIDES = (None, 'first', 'last', 'poison')
SEAL_REDUCTION_RULES = dict(
    evaluated_rows='every authorized cross-section row of the topology (V11 grid start..stop; adhesive: its one bond-land row), each '
                   'evaluated independently through every typed predicate with its own gland, flange, r_lim and flange top',
    diagnostic_rows='rows above the V11 stop up to diagnostic_stop: they only locate the owner zero-margin thresholds and are never coupled',
    predicate_feasible_rows='per typed predicate k: {r in evaluated_rows | predicate k of r holds} (boolean subsets)',
    gland_window_rows='R_gland = {r in evaluated_rows | every gland_* predicate of r holds} (O-ring topologies only)',
    fully_feasible_rows='{r in evaluated_rows | every typed predicate of r holds}; topology feasible = any(r.pass_all over evaluated_rows)',
    term_population='fully_feasible_rows when non-empty, else evaluated_rows (boolean rule)',
    term_reductions='per typed predicate k: value = max over the term population of m_k(r) (one quantity, one units group: the best margin '
                    'some row of the population attains; deficit = -value); worst = min; never across predicates or units',
    physical_envelope='per topology over evaluated_rows: r_lim [min, max] and flange thickness [min, max] (one length quantity each)',
    coupled_topology='the first closing topology in the fixed order face, radial, adhesive (serviceable first); when none closes, the face '
                     'topology (brief 6.3 baseline; the accepted R4 fallback, reported not closed) - boolean predicates and a fixed order only',
    coupled_population='fully_feasible_rows of the coupled topology when it closes, else every evaluated row of the face fallback',
    r_lim='coupled caseback radial limit = min over the coupled population of r_lim(r) (adverse; face / adhesive rows share R_side - '
          'tol, so it is unique there); every r_lim consumer of the point (structure, charger, LRA, G4 design terms) uses it',
    flange_top='coupled adverse flange top = max over the coupled population of flange_top(r) = (flange thickness of r, or the plate t_out '
               'for a row without a flange) + thickness tolerance; every flange Z relation of the point (charger neighbour, feature set, '
               'closure clearances) uses it, i.e. the most negative flange Z gap of the population',
    h14_flange_rows='per row of the coupled population: CHG_LAND / CHG_BLOCK vs the flange of that row at the design pose; the H14 flange '
                    'terms are the envelope (effective clearance = min over the rows, clear = all rows clear), checked row by row',
    charger_by_topology='per topology, per distinct (r_lim(r), flange_top(r)) of its evaluated rows: the complete same-point charger '
                        'predicate; topology result = any / all over its rows (both reported)',
    radial_supplier_land='per authorized radial row: strict-wedge zero-margin land width at chg_r_out = min(CHG_CONTACT r1, r_lim(r) - '
                         'c_chg_window); governing supplier threshold = min over the rows (land < value strictly for every authorized radial '
                         'row); envelope [min, max]',
    owner_thresholds='smallest gland-feasible cs = min cs over {r in evaluated + diagnostic rows | gland window holds}; its typed terms and '
                     'required bulk wall are those of that specific row; adhesive: its one row',
    representative_row='DISPLAY ONLY, chosen after every physical result: key (pass_all, number of passing predicates, gland window, minimum '
                       'dimensionless margin, minimum mm margin on the canonical 1e-9 mm grid, smallest cs) - booleans and a count first, '
                       'then one homogeneous quantity per component; never read by a physical, hard-check, stop, threshold, owner-question '
                       'or disposition path')


class DisplayOnlyRow(dict):
    """R5 zero-feedback fixture: a representative row that refuses every keyed read (a physical path reading it is a STOP)."""
    def __getitem__(self, k):
        raise StudyError('STOP: display-only representative seal row read by a physical path (%s)' % k)

    def get(self, k, d=None):
        raise StudyError('STOP: display-only representative seal row read by a physical path (%s)' % k)


def seal_unit(cx):
    u = getattr(cx, 'seal_unit', 'mm')
    if u not in SEAL_UNITS:
        raise StudyError('STOP: unknown seal length unit %r' % u)
    return u, SEAL_UNITS[u]


def h11_units(k):
    if k not in H11_TERM_TYPES:
        raise StudyError('STOP: untyped main-seal margin %s (R4-8)' % k)
    return H11_TERM_TYPES[k][1]


SEAL_ROW_LENGTHS = ('cs', 'r_lim', 'required_tw', 'bulk_only_margin', 'g4_literal_bulk_margin', 'spigot_height', 't_out_used')
SEAL_FLANGE_LENGTHS = ('thickness', 'groove_depth', 'groove_depth_tol', 'thickness_tol', 'residual_floor', 'required_thickness')


def seal_row_mm(r, s):
    """One internal-unit seal row converted to the canonical mm record (lengths suffixed _mm, typed mm margins converted)."""
    out = dict((k, r[k]) for k in ('id', 'topology', 'i', 'authorized', 'serviceable', 'predicates', 'n_pass', 'gland_window', 'pass_all'))
    for k in SEAL_ROW_LENGTHS:
        if k in r:
            out[k + '_mm'] = None if r[k] is None else r[k] / s
    out['margins'] = {k: (v / s if h11_units(k) == 'mm' else v) for k, v in r['margins'].items()}
    out['gland'] = None if r.get('gland') is None else {k: v / s for k, v in r['gland'].items()}
    fl = r.get('flange')
    out['flange'] = None if fl is None else dict(
        {k + '_mm': (None if fl[k] is None else fl[k] / s) for k in SEAL_FLANGE_LENGTHS},
        radial_extent_mm=[v / s for v in fl['radial_extent']],
        note='flange lies under the midcase rear-face annulus (outside the bore); no module Z volume used')
    return out


def seal_row_templates(cx, cand, sp, cs_grid, cs_diag, unit, s):
    """The cross-section-only part of every seal row of a candidate in internal unit s (gland, compression / fill ratios, flange search
    against the V12b grid with the unit-scaled tolerance, radial spigot REAR-periphery Z); independent of D and tw, cached per
    (candidate, unit). The point-dependent terms (annulus, bore, r_lim, required wall) are added per point by main_seal."""
    st, P = cx.st, cx.P
    cache = cx.__dict__.setdefault('seal_template_cache', {})
    key = (cand['id'], unit, json.dumps([P['V10_main_seal_topologies'], cs_grid, cs_diag, P['V12b_flange_thickness'], P['V12_caseback_thickness'],
                                         st.P['bond_lands']['caseback_bond_land_mm'], sp.m_cb['t_wall_min_mm'], sp.pc_cb], sort_keys=True))
    if key in cache:
        return cache[key]
    Lr = lambda v: v * s
    tmin, tol_t = Lr(sp.m_cb['t_wall_min_mm']['max']), Lr(sp.pc_cb['thickness_mm'])
    fl_grid = [Lr(t) for t in grid(P['V12b_flange_thickness'])]
    t_out_min = seal_t_out_min(cx, sp)
    out = []
    for topo in P['V10_main_seal_topologies']:
        for i, cs in (enumerate(cs_diag) if topo != 'adhesive' else [(0, None)]):
            fixed = dict(id='%s#%02d' % (topo, i), topology=topo, i=i, cs=None if cs is None else Lr(cs),
                         authorized=topo == 'adhesive' or i < len(cs_grid), gland=None, flange=None, serviceable=topo != 'adhesive',
                         spigot_height=0.0)
            tp = dict(fixed=fixed, m0={})
            if topo == 'adhesive':
                tp['bond_land'] = Lr(st.P['bond_lands']['caseback_bond_land_mm']['max'])
            else:
                gd, gm = gland_cached(cx, cand, sp, topo, cs)
                tp['m0'] = dict(gland_compression_min=gm[0], gland_compression_max=gm[1], gland_fill=gm[2])
                g = fixed['gland'] = dict((k, Lr(gd[k])) for k in ('h', 'g', 'tol_h', 'tol_g', 'land', 'face_annulus', 'spigot_radial', 'spigot_height'))
                if topo == 'face':
                    need = tol_t + g['h'] + g['tol_h'] + tmin
                    t_fl = next((t for t in fl_grid if t - need >= -EPS * s), None)
                    tp['m0']['flange_groove_residual'] = (t_fl if t_fl is not None else fl_grid[-1]) - need
                    tp['flange'] = dict(thickness=t_fl, groove_depth=g['h'], groove_depth_tol=g['tol_h'], thickness_tol=tol_t, residual_floor=tmin,
                                        required_thickness=need)
                else:
                    tp['m0']['spigot_rear_periphery_z'] = Lr(g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=t_out_min), gd['spigot_height']),
                                                                         full=False))
                    fixed['spigot_height'] = g['spigot_height']
            out.append(tp)
    cache[key] = out
    return out


def main_seal(cx, cand, row):
    """R5 seal population evaluation at one design point. Every authorized cross-section row of every topology is evaluated
    independently (typed predicates, its own gland, flange, r_lim); topology feasibility, the coupled r_lim / flange envelope, the
    per-predicate term reductions and the owner thresholds are explicit set reductions (SEAL_REDUCTION_RULES) over the row population
    or boolean-predicate subsets of it, taken in the internal length unit with unit-scaled tolerances and never across units. A
    representative row is chosen afterwards for display only (cx.seal_display_override exercises the zero-feedback regression)."""
    st, P = cx.st, cx.P
    unit, s = seal_unit(cx)
    Lr = lambda v: v * s
    eps = lambda u: EPS * s if u == 'mm' else EPS
    sp = cx.ce[cand['id']].sp
    ann = annulus_rows(cx, cand, row)
    avail_mm = min(a['value'] for a in ann)
    avail, bulk, tw, R = Lr(avail_mm), Lr(ann[0]['value']), Lr(row['tw']), Lr(row['R_side'])
    tolr = Lr(sp.pc_env['radius_mm'])
    V = P['V11_main_seal_cs']
    cs_grid = grid(dict(start=V['start'], stop=V['stop'], step=V['step']))
    cs_diag = grid(dict(start=V['start'], stop=V['diagnostic_stop'], step=V['step']))
    if cs_diag[:len(cs_grid)] != cs_grid:
        raise StudyError('STOP: V11 authorized cross-section grid is not the head of the diagnostic grid')
    t_out_min = seal_t_out_min(cx, sp)
    breaks = [Lr(a['R_bore_arc_mm']) - R for a in row['arcs'] if a['z_extent'] == 'THROUGH_REAR_FACE']
    bore = -max(breaks, default=0.0)
    rows = []
    for tp in seal_row_templates(cx, cand, sp, cs_grid, cs_diag, unit, s):
        count()
        r = dict(tp['fixed'])
        m = dict(tp['m0'])
        topo = r['topology']
        if topo == 'adhesive':
            bl = tp['bond_land']
            m['bond_land_annulus'] = avail - bl
            r.update(g4_literal_bulk_margin=Lr(g4.run_check(sp.adhesive_annulus(dict(tw=row['tw'])), full=False)), bulk_only_margin=bulk - bl,
                     r_lim=R - tolr, required_tw=bl + (tw - avail))
        elif topo == 'face':
            g = r['gland']
            m['face_annulus'] = avail - g['face_annulus']
            r.update(r_lim=R - tolr, bulk_only_margin=bulk - g['face_annulus'], required_tw=g['face_annulus'] + (tw - avail),
                     flange=dict(tp['flange'], radial_extent=[R, Lr(row['D'] / 2.0)]))
        else:
            m['continuous_bore'] = bore
            r.update(r_lim=R - r['gland']['spigot_radial'] - Lr(sp.pc_cb['radius_mm']), t_out_used=Lr(t_out_min))
        r['margins'] = m
        pr = r['predicates'] = {}
        for k, v in m.items():
            pr[k] = v >= -eps(H11_UNITS_OF.get(k) or h11_units(k))  # h11_units: STOP for an untyped margin key
        r['n_pass'] = sum(1 for v in pr.values() if v)
        r['gland_window'] = None if topo == 'adhesive' else (pr['gland_compression_min'] and pr['gland_compression_max'] and pr['gland_fill'])
        r['pass_all'] = all(pr.values())
        rows.append(r)
    by = {t: [r for r in rows if r['topology'] == t] for t in P['V10_main_seal_topologies']}
    if set(by) != set(SEAL_ORDER):
        raise StudyError('STOP: V10 main-seal topologies differ from %s' % (SEAL_ORDER,))
    same_q = lambda a, b, u: abs(a - b) <= 1e-12 * (s if u == 'mm' else 1.0)
    span = lambda vs: [min(vs), max(vs)] if vs else None
    tops = {}
    for t in SEAL_ORDER:
        ev = [r for r in by[t] if r['authorized']]
        ff = [r for r in ev if r['pass_all']]
        pop = ff or ev
        red = {}
        for k in sorted(ev[0]['margins']):
            u = h11_units(k)
            vals = [r['margins'][k] for r in pop]
            hi = max(vals)
            red[k] = dict(value=hi, worst=min(vals), units=u, rows_attaining=[r['id'] for r in pop if same_q(r['margins'][k], hi, u)])
        thick = [r['flange']['thickness'] for r in ev if r['flange'] is not None and r['flange']['thickness'] is not None]
        tops[t] = dict(role=H11_ROLES[t], serviceable=ev[0]['serviceable'], evaluated_rows=[r['id'] for r in ev],
                       diagnostic_rows=[r['id'] for r in by[t] if not r['authorized']],
                       predicate_feasible_rows={k: [r['id'] for r in ev if r['predicates'][k]] for k in sorted(ev[0]['margins'])},
                       gland_window_rows=None if t == 'adhesive' else [r['id'] for r in ev if r['gland_window']],
                       fully_feasible_rows=[r['id'] for r in ff], feasible=bool(ff), term_population='fully_feasible_rows' if ff else 'evaluated_rows',
                       term_reductions=red, physical_envelope=dict(r_lim=span([r['r_lim'] for r in ev]), flange_thickness=span(thick),
                                                                   rows_without_grid_flange=[r['id'] for r in ev if t == 'face' and r['flange']['thickness'] is None]))
    thresholds = {}
    for t in ('face', 'radial'):
        gw = [r for r in by[t] if r['gland_window']]
        first = min(gw, key=lambda r: r['cs']) if gw else None
        thresholds[t] = dict(smallest_feasible_gland_cs=first['cs'] if first else None, row=first['id'] if first else None,
                             at_that_cs=dict(first['margins']) if first else None, required_tw_mm=first.get('required_tw') if first else None)
    thresholds['adhesive'] = dict(required_tw_mm=by['adhesive'][0]['required_tw'], row=by['adhesive'][0]['id'])
    feasible = [t for t in P['V10_main_seal_topologies'] if tops[t]['feasible']]
    closing = [t for t in SEAL_PREFERENCE if t in feasible]
    ct = closing[0] if closing else 'face'
    cpop = [r for r in by[ct] if r['authorized'] and (r['pass_all'] or not closing)]
    cthick = [r['flange']['thickness'] for r in cpop if r['flange'] is not None and r['flange']['thickness'] is not None]
    coupled = dict(topology=ct, closed=bool(closing), population=[r['id'] for r in cpop], r_lim=min(r['r_lim'] for r in cpop),
                   r_lim_envelope=span([r['r_lim'] for r in cpop]), flange_thickness=span(cthick),
                   rows_without_flange=[r['id'] for r in cpop if r['flange'] is None or r['flange']['thickness'] is None])
    # ---- every physical result above is final; the representative row below is display-only (no physical consumer) ----
    ovr = getattr(cx, 'seal_display_override', None)
    if ovr not in SEAL_DISPLAY_OVERRIDES:
        raise StudyError('STOP: unknown seal display override %r' % ovr)

    def dkey(r):
        dim = [v for k, v in r['margins'].items() if h11_units(k) == 'dimensionless']
        lin = [v for k, v in r['margins'].items() if h11_units(k) == 'mm']
        return (r['pass_all'], r['n_pass'], bool(r['gland_window']), round(min(dim), 12) if dim else 0.0,
                round(min(lin) / s, 9) if lin else 0.0, -r['i'])
    for t in SEAL_ORDER:
        ev = [r for r in by[t] if r['authorized']]
        pick = {None: lambda: max(ev, key=dkey), 'first': lambda: ev[0], 'last': lambda: ev[-1], 'poison': lambda: None}[ovr]()
        tops[t]['representative_row'] = DisplayOnlyRow() if pick is None else dict(
            id=pick['id'], cs=pick['cs'], display_only=True, rule=SEAL_REDUCTION_RULES['representative_row'] if ovr is None else
            'display override %s (zero-feedback regression)' % ovr)
    # ---- canonical mm record ----
    mm = lambda v: None if v is None else v / s
    mmv = lambda d: {k: (v / s if h11_units(k) == 'mm' else v) for k, v in d.items()}
    for t in SEAL_ORDER:
        o = tops[t]
        o['term_reductions'] = {k: dict(d, value=mm(d['value']) if d['units'] == 'mm' else d['value'],
                                        worst=mm(d['worst']) if d['units'] == 'mm' else d['worst']) for k, d in o['term_reductions'].items()}
        env = o.pop('physical_envelope')
        o['physical_envelope'] = dict(r_lim_mm=[mm(v) for v in env['r_lim']],
                                      flange_thickness_mm=None if env['flange_thickness'] is None else [mm(v) for v in env['flange_thickness']],
                                      rows_without_grid_flange=env['rows_without_grid_flange'])
        rep = o['representative_row']
        if not isinstance(rep, DisplayOnlyRow):
            rep['cs_mm'] = mm(dict.get(rep, 'cs'))
            del rep['cs']
    for t in ('face', 'radial'):
        th = thresholds[t]
        th.update(smallest_feasible_gland_cs=mm(th['smallest_feasible_gland_cs']), required_tw_mm=mm(th['required_tw_mm']),
                  at_that_cs=None if th['at_that_cs'] is None else mmv(th['at_that_cs']))
    thresholds['adhesive']['required_tw_mm'] = mm(thresholds['adhesive']['required_tw_mm'])
    coupled = dict(topology=ct, closed=coupled['closed'], population=coupled['population'], r_lim_mm=mm(coupled['r_lim']),
                   r_lim_envelope_mm=[mm(v) for v in coupled['r_lim_envelope']],
                   flange_thickness_mm=None if coupled['flange_thickness'] is None else [mm(v) for v in coupled['flange_thickness']],
                   rows_without_flange=coupled['rows_without_flange'],
                   rule=SEAL_REDUCTION_RULES['coupled_topology'] + '; ' + SEAL_REDUCTION_RULES['coupled_population'])
    return dict(internal_unit=unit, annulus=ann, annulus_min_mm=avail_mm, rows=[seal_row_mm(r, s) for r in rows], topologies=tops,
                thresholds=thresholds, feasible_topologies=feasible, physical_pass=bool(feasible), coupled=coupled,
                closed_topology=ct if closing else None, reduction_rules=SEAL_REDUCTION_RULES,
                coupling='Arcs that run through the rear face (C-R1-04 crossings that must pass the REAR-level bore at rear '
                         'insertion) reduce the rear-face annulus and break the continuous bore of a radial spigot.')


def seal_rows(seal, ids):
    by = {r['id']: r for r in seal['rows']}
    return [by[i] for i in ids]


def row_flange_top(cx, cand, r, t_out=None):
    """Adverse Z top of the caseback seal flange that seal row r induces: its flange thickness (face row with a grid flange), else the
    plate t_out (the selected plate; the thickest V12 plate when none is selected), plus the caseback thickness tolerance."""
    fl = r.get('flange') or {}
    t = fl.get('thickness_mm')
    if t is None:
        t = t_out if t_out is not None else max(grid(cx.P['V12_caseback_thickness']['t_out']))
    return t + cx.ce[cand['id']].sp.pc_cb['thickness_mm']


def seal_r_lim(seal):
    """Coupled caseback radial limit of the point (SEAL_REDUCTION_RULES['r_lim'])."""
    return seal['coupled']['r_lim_mm']


def seal_inventory_r1(cx, cand, btn, seal_topology, ft, f3_used=False):
    """Accepted G4 inventory format (g4.seal_inventory) with the R1 primary-seal classes per aperture."""
    st = cx.st
    inv = g4.seal_inventory(st, cand, 'W1', len(st.s14geo['cells']), seal_topology if seal_topology else 'adhesive', f3_used)
    for s in inv['seals']:
        if s['id'].startswith('S-SW'):
            topo = btn['selected_topology'].get(s['id'][2:]) or btn['switches'][s['id'][2:]]['best']['I-SUM']['topology']
            s['type'] = 'elastomer boot / bonded diaphragm (static face / bonded rim)' if topo.startswith('T2') else 'case-integral flexure'
            s['r1_topology'] = topo
        if s['id'] == 'S-CHG':
            s['type'] = dict(FT_A='adhesive ring', FT_B='insert-moulded feedthrough', FT_C='bonded sealed body').get(ft.replace('-', '_'), 'adhesive ring')
            s['r1_topology'] = ft
    for owner, aps in inv['components'].items():
        for a in aps:
            s = next(x for x in inv['seals'] if x['id'] == a['seal'])
            a['type'] = s['type']
    if seal_topology is None:
        inv['note'] = 'S-CB-MAIN carries no feasible topology; adhesive placeholder type recorded for graph closure only'
    return inv


def screws_outside(cx, cand, D, seal_line_outer_r):
    st = cx.st
    sp = cx.ce[cand['id']].sp
    scr = g4.screw_layout(st, sp, dict(D=D))
    hole = st.P['screw_classes'][cand['screw_class']]['hole_dia_mm']
    m = min(s['radius'] - hole / 2.0 for s in scr['screws']) - seal_line_outer_r
    return dict(margin_mm=m, outside=m >= -EPS, screws=scr, seal_line_outer_r_mm=seal_line_outer_r)


# --------------------------------------------------------------------------------------------
# L-CHG: contact block (conductive, strict wedge) + non-conductive land (C-R1-01 caps), pose search
# --------------------------------------------------------------------------------------------
def chg_block_dims(cx, ori, r1in=None):
    I = r1in or cx.I
    rad, tan = I['parameters']['V19_charger_pose']['block_size_mm']
    return (rad, tan) if ori == 0 else (tan, rad)


def poly_rmin(poly):
    if g4.pip((100.0, 100.0), poly):
        return 0.0
    return min(g4.seg_dist((100.0, 100.0), a, b) for a, b in zip(poly, poly[1:] + poly[:1]))


CHG_RADIAL_TERMS = ('block_inner', 'block_reservation_outer', 'land_inner_s14')
CHG_PLAN_TERMS = ('block_in_wedge', 'land_overshoot_cap', 'land_radiators', 'land_u6')


def chg_pose(cx, cand, ori, rc, azc, land, r1in=None, block_top=None):
    """r_lim-independent geometry of one pose. Conductive block strictly inside the CHG_CONTACT wedge; the
    non-conductive land outside S14 + 1.1, overshoot <= cap perpendicular to a wedge side, azimuth inside the cap,
    >= rf_clearance from every radiator volume. R3-1: the pose-level predicates are grouped into the radial, plan, Z and
    material categories; prereq_pass = radial + plan + material (no Z), pass_ = every pose-level contract / physical predicate
    including the land's (v) Z part and the block's 3-D route clearance (R4-3; the block-AND-Z screen is a diagnostic only).
    block_top: block Z top (default: the SR-CHG-MECH allocation maximum z_band_lo_adv)."""
    count()
    st = cx.st
    sp = cx.ce[cand['id']].sp
    V = (r1in or cx.I)['parameters']['V20_charger_land']
    w0, w1 = st.res[V['wedge_reservation']]['geometry']['az']
    r_res_out = st.res[V['wedge_reservation']]['geometry']['r'][1]
    rad, tan = chg_block_dims(cx, ori, r1in)
    tp = sp.pc_cb['radius_mm']
    ab, bb = rad / 2.0 + tp, tan / 2.0 + tp
    al, bl = rad / 2.0 + land + tp, tan / 2.0 + land + tp
    block = local_rect(azc, rc - ab, rc + ab, -bb, bb)
    landp = local_rect(azc, rc - al, rc + al, -bl, bl)
    b_side = max(max(side_overshoot(p, w1, 1.0), side_overshoot(p, w0, -1.0)) for p in block)
    l_side = max(max(side_overshoot(p, w1, 1.0), side_overshoot(p, w0, -1.0)) for p in landp)
    azs = [g4.polar(p)[1] for p in landp]
    b_rmin, b_rmax = poly_rmin(block), max(math.hypot(p[0] - 100.0, p[1] - 100.0) for p in block)
    l_rmin, l_rmax = poly_rmin(landp), max(math.hypot(p[0] - 100.0, p[1] - 100.0) for p in landp)
    rf = st.P['rf_clearance_report_mm']
    rad_d = {rid: poly_distance(dict(type='poly', pts=landp), st.res[rid]['geometry']) for rid in ('GNSS_RAD', 'BLE_RAD', 'WIFI_RAD')}
    block_wifi = poly_distance(dict(type='poly', pts=block), st.res['WIFI_RAD']['geometry']) <= 0.0
    u6 = poly_distance(dict(type='poly', pts=landp), dict(type='poly', pts=st.s14geo['u6_island']))
    m = dict(block_in_wedge=-b_side, block_inner=b_rmin - cx.r_s14_clear, block_reservation_outer=r_res_out - b_rmax,
             land_inner_s14=l_rmin - cx.r_s14_clear, land_overshoot_cap=V['overshoot_cap_mm'] - max(0.0, l_side),
             land_radiators=min(rad_d.values()) - rf, land_u6=u6)
    m_deg = dict(land_azimuth_cap=min(min(azs) - V['azimuth_cap_deg'][0], V['azimuth_cap_deg'][1] - max(azs)))
    cb = cand['caseback']
    land_mat = cb['centre_material'] if cb.get('split') and l_rmax <= (st.res['GNSS_RAD']['radial_mm'][0] - cb['centre_rf_clearance_mm']) else cb['material']
    t_top = max(grid(cx.P['V12_caseback_thickness']['t_out'])) + sp.pc_cb['thickness_mm']
    # R4-3: C-R1-01 2(v) is a LAND rule: the non-conductive land clears CHG_ROUTE and CHG_LINK in plan AND in Z (authoritative
    # conductor records, R2-4; a Z separation never waives a plan collision). C-R1-01 item 1 states no plan-AND-Z rule for the
    # conductive block: the block is held to the common strict 3-D clearance (plan OR Z, R3-3; G4 H20 "block ... clear"), and the
    # block-AND-Z screen (block strictly below the conductor band) is reported as R1 model conservatism only.
    RC = V['route_clearance']
    b_top = cx.zm['z_band_lo_adv'] if block_top is None else block_top
    land_f = feature('CHG_LAND', 'L-CHG', 'land', False, False, dict(type='poly', pts=landp), ['REAR'], zfeat(0.0, t_top), 'charger land')
    block_f = feature('CHG_BLOCK', 'L-CHG', 'block', True, False, dict(type='poly', pts=block), ['REAR'], zfeat(0.0, b_top), 'charger contacts')
    routes = []
    for rid in RC['routes']:
        for part in (land_f, block_f):
            _, info = clear_both(part, conductor(cx, rid), RC['plan_mm'], RC['z_mm'], report_gap=False)
            land_part = part['id'] == 'CHG_LAND'
            routes.append(dict(part=part['id'], route=rid, plan_clear=info['plan_clear'], z_clear=info['z_clear'], z_gap_mm=info['z_gap_mm'],
                               predicate='plan AND Z' if land_part else '3-D (plan OR Z)',
                               category='contract_mandated' if land_part else 'physical_required_elsewhere',
                               clear=(info['plan_clear'] and info['z_clear']) if land_part else (info['plan_clear'] or info['z_clear']),
                               plan_and_z=info['plan_clear'] and info['z_clear']))
    lr = [x for x in routes if x['part'] == 'CHG_LAND']
    br = [x for x in routes if x['part'] == 'CHG_BLOCK']
    pred = dict(block_outside_wifi=not block_wifi, land_non_conductive=not st.I['material_classes'][land_mat]['conductive'],
                land_caseback_side=t_top <= cx.zm['z_band_lo_adv'] + EPS, land_clear_of_u6=separated(u6),
                routes_clear_in_plan=all(x['plan_clear'] for x in routes), land_routes_clear_in_z=all(x['z_clear'] for x in lr),
                block_routes_clear_3d=all(x['plan_clear'] or x['z_clear'] for x in br),
                block_routes_clear_in_z=all(x['z_clear'] for x in br))
    cat = dict(radial=all(m[k] >= -EPS for k in CHG_RADIAL_TERMS),
               plan=all(m[k] >= -EPS for k in CHG_PLAN_TERMS) and m_deg['land_azimuth_cap'] >= -EPS and pred['block_outside_wifi']
               and pred['land_clear_of_u6'] and pred['routes_clear_in_plan'],
               z=pred['land_caseback_side'] and pred['land_routes_clear_in_z'],
               material=pred['land_non_conductive'], block_3d=pred['block_routes_clear_3d'])
    prereq = cat['radial'] and cat['plan'] and cat['material']
    return dict(orientation=ori, r_centre=rc, az_centre=azc, land=land, block_mm=[rad, tan], position_tol=tp,
                block_poly=block, land_poly=landp, block_rmax=b_rmax, land_rmax=l_rmax, land_rmin=l_rmin, block_top_mm=b_top, land_top_mm=t_top,
                land_side_overshoot_mm=l_side, land_az=[min(azs), max(azs)], radiator_distance_mm=rad_d,
                margins=m, margins_deg=m_deg, predicates=pred, route_rows=routes, own_min_margin=min(m.values()),
                r_lim_required=max(b_rmax, l_rmax) + st.P['c_chg_window_mm']['max'], categories=cat,
                diagnostics=dict(block_and_z_routes=pred['block_routes_clear_in_z'] and pred['routes_clear_in_plan']),
                prereq_pass=prereq, pass_=prereq and cat['z'] and cat['block_3d'])


def chg_poses(cx, cand, land, r1in=None):
    V = (r1in or cx.I)['parameters']['V19_charger_pose']
    out = []
    for ori in V['orientations']:
        for rc in grid(V['r_centre']):
            for azc in grid(V['az_centre']):
                out.append(chg_pose(cx, cand, ori, rc, azc, land, r1in))
    return out


def chg_select(cx, cand, poses, r_lim):
    """Pose ranking at a caseback radial limit (structural land interrupter and reported pose): the best pose meeting the radial
    and plan prerequisites (r_lim-independent radial / plan / material categories and the seal-flange limit at r_lim), ranked by
    minimum mm margin, azimuth closest to the wedge centre, radius, orientation; without such a pose, the closest pose meeting
    every r_lim-independent prerequisite (its minimum margin is the governing flange / r_lim deficit). R3-1: the ranking never
    labels a pose a charger closure; prereq_pass is the radial + plan prerequisite at r_lim only (Z and the same-point
    neighbour set are evaluated by chg_point_eval)."""
    st = cx.st
    c = st.P['c_chg_window_mm']['max']
    best = None
    for i, p in enumerate(poses):
        fb, fl = (r_lim - c) - p['block_rmax'], (r_lim - c) - p['land_rmax']
        mm_ = min(p['own_min_margin'], fb, fl)
        ok = p['prereq_pass'] and fb >= -EPS and fl >= -EPS
        e = ((ok, p['prereq_pass'], mm_, -abs(p['az_centre'] - 90.0), -p['r_centre'], -p['orientation']), -i, mm_, p,
             dict(block_flange=fb, land_flange=fl), ok)
        if best is None or e[:2] > best[:2]:
            best = e
    _, _, mm_, p, m_out, ok = best
    return dict(pose=p, flange_margins=m_out, min_margin=mm_, prereq_pass=ok, r_lim=r_lim)


# --------------------------------------------------------------------------------------------
# R3-1 / R3-2: same-point charger evaluation. Every charger pose is evaluated against the complete neighbour set of ONE
# physical design point (candidate, D, bulk / local wall, seal r_lim and flange, plate, screws, supports, pads, vent, buttons,
# lugs, local arcs, routes, ribs) in five separate categories; only the literal category is a charger closure.
# --------------------------------------------------------------------------------------------
CHG_CATEGORIES = ('radial', 'plan', 'z', 'neighbours', 'literal')


def plan_descriptor(g):
    """Exact azimuth span (smallest covering clockwise arc; None when the region contains the centre or is a full ring) and radial
    range of a plan region (sector / circles / rect / poly)."""
    t = g['type']
    if t == 'sector':
        full = tuple(g['az']) == (0.0, 360.0)
        return dict(az=None if full else [g['az'][0], g['az'][1]], r=[g['r'][0], g['r'][1]])
    if t == 'circles':
        spans, rs = [], []
        for x, y, rho in g['circles']:
            d, a = g4.polar((x, y))
            rs.append((max(0.0, d - rho), d + rho))
            spans.append(None if d <= rho + EPS else ((a - math.degrees(math.asin(rho / d))) % 360.0, (a + math.degrees(math.asin(rho / d))) % 360.0))
        az = spans[0] if len(spans) == 1 else None
        return dict(az=None if az is None else [az[0], az[1]], r=[min(r[0] for r in rs), max(r[1] for r in rs)])
    pts = geom_poly(g)
    if g4.pip((100.0, 100.0), pts):
        return dict(az=None, r=[0.0, max(math.hypot(p[0] - 100.0, p[1] - 100.0) for p in pts)])
    it = poly_interrupter('x', pts)
    return dict(az=it['az'], r=it['r'])


def plan_clear_of_charger(cx, desc, r_hi):
    """Exact sufficient plan test (R3-1): every charger land / block polygon that meets the radial and pose-level plan
    prerequisites lies inside the C-R1-01 azimuth cap and inside r_S14 + 1.1 .. r_hi (convex polygons not containing the centre).
    A neighbour region whose azimuth span is disjoint from the cap, or whose radial range is disjoint from that interval, is at
    a strictly positive plan distance from every such pose (distance >= (r_S14 + 1.1) sin(gap) > 0 for an angular gap)."""
    cap = tuple(cx.P['V20_charger_land']['azimuth_cap_deg'])
    if desc['az'] is not None and g4.arc_gap(tuple(desc['az']), cap) > 1e-6:
        return True
    return desc['r'][0] > r_hi + EPS or desc['r'][1] < cx.r_s14_clear - EPS


def nb_record(cx, f, rule, envelope=None):
    """Neighbour record for the same-point charger evaluation: the exact feature (geometry, Z) or, for features whose exact plan
    position is chosen inside a frozen azimuth window at every point (supports, pads, vent), the window superset envelope. Z is
    the feature's own adverse interval or, for a level-only record, the with_z() level interval (same rule, cached levels)."""
    if 'z_lo_adv' in f:
        zlo, zhi = f['z_lo_adv'], f['z_hi_adv']
    else:
        lv = cx.__dict__.setdefault('level_z_cache', level_z(cx.st))
        zs = [lv[l] for l in f['z'] if l in lv]
        zlo, zhi = (min(a for a, _ in zs), max(b for _, b in zs)) if zs else (0.0, 0.0)
    return dict(id=f['id'], kind=f['kind'], rule=rule, z_lo_adv=zlo, z_hi_adv=zhi, z=list(f['z']), exact=envelope is None,
                geom=f.get('geom'), desc=plan_descriptor(f['geom']) if envelope is None else envelope)


def chg_rule(cx, f):
    """C-R1-01 (v) items (CHG_ROUTE, CHG_LINK, screws, supports: plan AND Z) vs (vi) neighbours (strict 3-D clearance)."""
    RC = cx.P['V20_charger_land']['route_clearance']
    return 'v' if (f['id'] in RC['routes'] or f['kind'] in RC['plan_and_z_kinds']) else 'vi'


def chg_static_envelopes(cx, cand):
    """Candidate-constant window envelopes (exact supersets valid at every grid point) of the neighbours whose plan position
    g4.supports_layout / g4.vent_layout choose inside a frozen azimuth window: SUP_SW / SUP_SE / SUP_NE case-side posts lie inside
    their reservation window (placement rule: both post edges inside the window), their MAIN stop pads inside the window widened
    by the pad half-angle; SUP_WNW centres lie in the W/NW search window (post half-angle at the smallest bulk-wall radius of the
    grid, pad half-angle added); the vent lies inside its search window (both edges inside, g4.place_on_arc). Z from the feature
    levels (posts BATTERY + REAR, pads / vent MAIN). The exact design-point features are checked to lie inside these envelopes."""
    cache = cx.__dict__.setdefault('chg_env_cache', {})
    if cand['id'] in cache:
        return cache[cand['id']]
    st = cx.st
    sp = cx.ce[cand['id']].sp
    S = st.I['parameters']['supports']
    V1, V2 = cx.P['V01_D_case_body'], cx.P['V02_tw_bulk']
    r_bore_min = V1['start'] / 2.0 - V2['stop']
    r_out = V1['report_stop'] / 2.0
    pad_in = st.R_main - sp.pc_pcb['radius_mm'] - S['pad_radial_mm']['max']
    pad_half = math.degrees(math.asin((S['pad_tangential_mm'] / 2.0) / pad_in))
    post_half_max = math.degrees(math.asin((S['post_tangential_mm'] / 2.0) / r_bore_min))
    out = []
    for rid in ('SUP_SW', 'SUP_SE', 'SUP_NE'):
        w = g4.res_az(st, rid)
        out.append((dict(id=rid + '_CASE_SIDE', kind='case-side support', z=['BATTERY', 'REAR']),
                    dict(az=[w[0] % 360.0, w[1] % 360.0], r=[0.0, r_out], window=list(w), half_deg=0.0)))
        out.append((dict(id=rid + '_PAD', kind='support pad', z=['MAIN']),
                    dict(az=[(w[0] - pad_half) % 360.0, (w[1] + pad_half) % 360.0], r=[pad_in, r_out], window=list(w), half_deg=pad_half)))
    wn = tuple(S['w_nw_search_deg'])
    for sid, kind, z, h in (('SUP_WNW_CASE_SIDE', 'case-side support', ['BATTERY', 'REAR'], post_half_max),
                            ('SUP_WNW_PAD', 'support pad', ['MAIN'], pad_half)):
        out.append((dict(id=sid, kind=kind, z=z), dict(az=[(wn[0] - h) % 360.0, (wn[1] + h) % 360.0], r=[0.0, r_out], window=list(wn), half_deg=h)))
    vw = tuple(st.I['parameters']['vent']['search_deg'])
    out.append((dict(id='VENT_PORT', kind='vent port', z=['MAIN']), dict(az=[vw[0] % 360.0, vw[1] % 360.0], r=[r_bore_min, r_out], window=list(vw),
                                                                    half_deg=0.0)))
    recs = [nb_record(cx, f, chg_rule(cx, f), env) for f, env in out]
    cache[cand['id']] = recs
    return recs


def chg_neighbours_at(cx, cand, D, tw, row, flange_top, exact_feats=None, rib_feats=()):
    """The neighbour set of ONE design point (R3-1). exact_feats (design point): the exact feature records of that point (screws,
    case-side supports, pads, lugs, spring bars, R1 button plungers / boots / bosses, vent), used as they are. Otherwise (sweep
    points): exact screws, lug arms / spring bars and button bores / bosses of this (D, tw) (g4 layouts) and the window envelopes of
    the supports / pads / vent. Always added: the caseback seal flange of this point (sector R_side .. D/2, Z 0 .. flange_top),
    the V03 local arcs of this point, the CHG_ROUTE / CHG_LINK conductor records and the credited ribs (design point; at sweep
    points no structural configuration is selected and the charger land interrupts every spoke it crosses, LA-STR-5)."""
    st = cx.st
    sp = cx.ce[cand['id']].sp
    RC = cx.P['V20_charger_land']['route_clearance']
    if exact_feats is not None:
        out = [nb_record(cx, f, chg_rule(cx, f)) for f in exact_feats]
    else:
        dp = dict(cx.ce[cand['id']].dp0, D=D, tw=tw)
        fs_ = [dict(id=s['id'], geom=s['geom'], z=['REAR'], kind='caseback screw') for s in g4.screw_layout(st, sp, dp)['screws']]
        fs_ += [dict(id=lg['id'], geom=lg['geom'], z=['MAIN', 'BATTERY', 'REAR'], kind=lg['kind']) for lg in g4.lug_layout(st, dp)]
        for b in g4.button_layout(st, sp, dp):
            fs_ += [dict(id=b['id'] + '_PUSHER', geom=b['bore_geom'], z=['MAIN'], kind='pusher'),
                    dict(id=b['id'] + '_BOSS', geom=b['boss_geom'], z=['MAIN'], kind='button boss')]
        out = [nb_record(cx, f, chg_rule(cx, f)) for f in fs_] + chg_static_envelopes(cx, cand)
    out.append(flange_neighbour(cx, cand, row, D, flange_top))
    lv = cx.__dict__.setdefault('level_z_cache', level_z(st))
    for a in row['arcs']:
        thru = a['z_extent'] == 'THROUGH_REAR_FACE'
        out.append(nb_record(cx, feature('ARC_' + a['reservation'], 'L-RAD', a['local_material'], True, False,
                                         g4.sector(a['arc_az'][0], a['arc_az'][1], a['R_bore_arc_mm'], D / 2.0),
                                         ['MAIN', 'BATTERY'] + (['REAR'] if thru else []),
                                         zfeat(lv['REAR'][0] if thru else lv['BATTERY'][0], lv['MAIN'][1]), 'local wall arc'), 'vi'))
    out += [nb_record(cx, conductor(cx, rid), 'v') for rid in RC['routes']]
    out += [nb_record(cx, f, 'vi') for f in rib_feats]
    return out


def flange_neighbour(cx, cand, row, D, flange_top):
    """The caseback seal flange of a point as a charger neighbour (sector R_side .. D/2, Z 0 .. flange_top adverse, rule (vi))."""
    tol_t = cx.ce[cand['id']].sp.pc_cb['thickness_mm']
    return nb_record(cx, feature('CB_SEAL_FLANGE', 'L-SEAL', cand['caseback']['material'], False, False,
                                 g4.sector(0.0, 360.0, row['R_side'], D / 2.0), ['REAR'], zfeat(0.0, flange_top - tol_t, 0.0, tol_t),
                                 'caseback seal flange'), 'vi')


def chg_pose_ctx(poses):
    """Per-candidate pose index for the same-point evaluation: radially admissible poses (r_lim-independent radial category)
    sorted by the caseback radial limit each requires (then orientation 0 first, azimuth closest to 90, radius), the first index
    of a pose that also meets the plan and material categories, and the first index of a pose clear of every route in plan."""
    key = lambda p: (p['r_lim_required'], -p['orientation'], abs(p['az_centre'] - 90.0), p['r_centre'])
    rad = sorted([p for p in poses if p['categories']['radial']], key=key)
    first = lambda f: next((i for i, p in enumerate(rad) if f(p)), len(rad))
    return dict(poses=poses, rad=rad, r=[p['r_lim_required'] for p in rad],
                first_pre=first(lambda p: p['categories']['plan'] and p['categories']['material']),
                first_route_plan=first(lambda p: all(x['plan_clear'] for x in p['route_rows'])))


def chg_point_eval(cx, pctx, r_lim, t_top, nbrs, strict=None):
    """R3-1 same-point charger evaluation over every V19 pose (adverse land) at one design point; R4-3 contract attribution.
      radial      C-R1-01 item 1 radial bounds of the block (incl. r_lim - c_chg_window) and the land (S14 + 1.1; the G4
                  c_chg_window seal-flange clearance applied to the land outer edge, a physical requirement from G4 8.8 / H20)
      plan        radial + every plan bound (wedge, WIFI_RAD, overshoot / azimuth caps, radiator rf clearance, U6, routes in plan)
                  + strictly positive plan clearance of the land (and the block inside it) from every C-R1-01 2(v) item
      z           contract Z bounds of the LAND: caseback side (2(ii)) and strictly Z-separated (R3-3) from CHG_ROUTE / CHG_LINK
                  and every other 2(v) item (C-R1-01 2(v) is plan AND Z for the land)
      neighbours  one radially admissible pose with every neighbour of the point cleared: the land under its contract rule ((v)
                  plan AND Z, (vi) strict 3-D), the block under the common strict 3-D clearance (plan OR Z) against every
                  neighbour (C-R1-01 states no plan-AND-Z rule for the block)
      literal     one pose meeting radial, plan, Z, neighbours and the material rule (contract + physical; the charger closure)
    Diagnostics (never a closure): block_and_z - the block strictly Z-separated from every (v) item (R1 model conservatism, not
    contract text); literal_v_z_waived - the literal predicate with only the conjunctive Z part of 2(v) waived for a land that is
    plan-disjoint from the item (consequence quantification for Q-R1-CHARGER; C-R1-01 is not amended).
    Neighbour relations are exact: Z from the feature Z intervals; plan by the exact sufficient test plan_clear_of_charger,
    otherwise by the exact polygon overlap of each admissible pose (routes: the pose's own exact route rows). An envelope-only
    neighbour that the exact test cannot decide is a STOP (fail-closed). strict: the strict-wedge supplier-path pose of this
    point (R3-2), judged with the same neighbour relations, with 2(v) applied to its land (R1 reading, Q-R1-CHARGER (b)) and
    with the 2(v) Z part waived (diagnostic)."""
    st = cx.st
    RC = cx.P['V20_charger_land']['route_clearance']
    r_hi = r_lim - st.P['c_chg_window_mm']['max']
    land_z, block_z = zfeat(0.0, t_top), zfeat(0.0, cx.zm['z_band_lo_adv'])
    k = bisect.bisect_right(pctx['r'], r_lim + EPS)
    rad = pctx['rad'][:k]
    rel = []
    for n in nbrs:
        count(3)
        zl, zb = z_gap(land_z, n), z_gap(block_z, n)
        rel.append(dict(n=n, zl=zl, zb=zb, z_land_ok=separated(zl), z_block_ok=separated(zb), route=n['id'] in RC['routes'],
                        plan_all=n['id'] not in RC['routes'] and plan_clear_of_charger(cx, n['desc'], r_hi)))
    caseback_side = t_top <= cx.zm['z_band_lo_adv'] + EPS
    v_rel = [r_ for r_ in rel if r_['n']['rule'] == 'v']
    z_ok = caseback_side and all(r_['z_land_ok'] for r_ in v_rel)
    block_and_z = all(r_['z_block_ok'] for r_ in v_rel)
    undecided = [r_ for r_ in rel if not r_['plan_all'] and not r_['route']]
    for r_ in undecided:
        if not r_['n']['exact']:
            raise StudyError('STOP: charger neighbour %s (window envelope) not decidable in plan; exact geometry required' % r_['n']['id'])

    def judge(p):
        """(every (v) item plan-clear, every neighbour cleared under its rule, the same with the 2(v) Z part waived for a
        plan-disjoint land) for one radially admissible pose."""
        pv, nb, nbw = True, True, True
        for r_ in rel:
            n = r_['n']
            if r_['route']:
                rows = [x for x in p['route_rows'] if x['route'] == n['id']]
                pl = next(x['plan_clear'] for x in rows if x['part'] == 'CHG_LAND')
                pb = next(x['plan_clear'] for x in rows if x['part'] == 'CHG_BLOCK')
            elif r_['plan_all']:
                pl = pb = True
            else:
                count(2)
                pl = not plan_overlap(dict(type='poly', pts=p['land_poly']), n['geom'])
                pb = not plan_overlap(dict(type='poly', pts=p['block_poly']), n['geom'])
            block3d = pb or r_['z_block_ok']
            if n['rule'] == 'v':
                pv = pv and pl and pb
                nb = nb and pl and r_['z_land_ok'] and block3d
                nbw = nbw and pl and block3d
            else:
                nb = nb and (pl or r_['z_land_ok']) and block3d
                nbw = nbw and (pl or r_['z_land_ok']) and block3d
        return pv, nb, nbw
    plan_ok = nb_ok = nbw_ok = lit = litw = False
    lit_pose = None
    if undecided:
        for p in rad:
            pv, nb, nbw = judge(p)
            pre = p['categories']['plan'] and p['categories']['material'] and pv
            plan_ok, nb_ok, nbw_ok = plan_ok or pre, nb_ok or nb, nbw_ok or nbw
            litw = litw or (pre and nbw and caseback_side)
            if pre and nb and z_ok and lit_pose is None:
                lit, lit_pose = True, p
    elif rad:
        # every non-route neighbour is cleared in plan for every admissible pose at once (exact sufficient test), so its
        # relation is pose-independent: the land still needs its contract (v) Z separation, a (vi) item and the block's 3-D
        # relation are cleared; routes are judged per pose from the pose's own exact route rows (plan; the block lies inside the
        # land, so a plan-clear land implies a plan-clear block) and the point's Z gaps
        nz_v = all(r_['z_land_ok'] for r_ in v_rel)
        plan_ok = pctx['first_pre'] < k
        nb_ok = nz_v and pctx['first_route_plan'] < k
        nbw_ok = pctx['first_route_plan'] < k
        lit_pose = rad[pctx['first_pre']] if (plan_ok and nz_v and z_ok) else None
        lit = lit_pose is not None
        litw = plan_ok and caseback_side
    out = dict(radial=bool(rad), plan=plan_ok, z=z_ok, neighbours=nb_ok, literal=lit, land_caseback_side=caseback_side,
               block_and_z=block_and_z, neighbours_v_z_waived=nbw_ok, literal_v_z_waived=litw,
               z_min_v_land_mm=min([r_['zl'] for r_ in v_rel]), z_min_v_block_mm=min([r_['zb'] for r_ in v_rel]), literal_pose=lit_pose,
               neighbours_evaluated=len(rel), undecided_in_plan=[r_['n']['id'] for r_ in undecided])
    if strict is not None:
        sp_ = strict.get('pose')
        ok_w = strict['width_mm'] is not None and strict['width_mm'] >= strict['land_min_mm'] - EPS
        s_rad = bool(sp_) and ok_w and strict['contained'] and sp_['categories']['radial'] and sp_['r_lim_required'] <= r_lim + EPS
        s_pv, s_nb, s_nbw = judge(sp_) if s_rad else (False, False, False)
        s_plan = s_rad and sp_['categories']['plan'] and sp_['categories']['material'] and s_pv
        out['strict_wedge'] = dict(width_mm=strict['width_mm'], chg_r_out_mm=strict['chg_r_out_mm'], in_land_range=s_rad, plan=s_plan,
                                   neighbours=s_rad and s_nb, z=z_ok, complete=s_plan and s_nb and z_ok,
                                   neighbours_v_z_waived=s_rad and s_nbw, complete_v_z_waived=s_plan and s_nbw and caseback_side)
    return out


CHG_SWEEP_FLAGS = ('radial', 'plan', 'z', 'neighbours', 'literal', 'sw_in_land_range', 'sw_plan', 'sw_neighbours', 'sw_complete',
                   'literal_v_z_waived', 'sw_complete_v_z_waived')
CHG_DIAGNOSTIC_FLAGS = ('literal_v_z_waived', 'sw_complete_v_z_waived')


def chg_sweep_flags(ch):
    s = ch['strict_wedge']
    return dict(radial=ch['radial'], plan=ch['plan'], z=ch['z'], neighbours=ch['neighbours'], literal=ch['literal'],
                sw_in_land_range=s['in_land_range'], sw_plan=s['plan'], sw_neighbours=s['neighbours'], sw_complete=s['complete'],
                literal_v_z_waived=ch['literal_v_z_waived'], sw_complete_v_z_waived=s['complete_v_z_waived'])


def chg_land_top(cx, cand, t_out=None):
    """Adverse Z top of the non-conductive land (caseback plate): the selected plate, else the thickest V12 plate (the
    chg_pose default), plus the caseback process thickness tolerance."""
    t = t_out if t_out is not None else max(grid(cx.P['V12_caseback_thickness']['t_out']))
    return t + cx.ce[cand['id']].sp.pc_cb['thickness_mm']


def flange_top(cx, cand, seal, t_out=None):
    """R5: adverse Z top of the caseback seal flange of a point = max over the coupled seal population of row_flange_top(r)
    (SEAL_REDUCTION_RULES['flange_top']); one reduction of one length quantity, never a representative row."""
    return max(row_flange_top(cx, cand, r, t_out) for r in seal_rows(seal, seal['coupled']['population']))


def ft_topology(cand, r_split=None, land_rmin=None):
    """C-R1-05 feedthrough class from the caseback material at the charger location (FT-A is the reference)."""
    cb = cand['caseback']
    mat = cb['material']
    if cb.get('split') and r_split is not None and land_rmin is not None and land_rmin < r_split:
        mat = cb['centre_material']
    return 'FT-B' if mat == 'MAT-GF-POLY' else 'FT-C'


# --------------------------------------------------------------------------------------------
# L-STR: rib layout (LA-STR-5), Screen B governing / Screen A reported, thresholds and FEA handoff
# --------------------------------------------------------------------------------------------
def str_material(st, mat_id, proc_id):
    m = st.I['material_classes'][mat_id]
    pc = st.I['process_classes'][proc_id]
    return dict(id=mat_id, E=m['E_MPa']['min'], nu=m['nu']['max'], sigma_allow=m['sigma_allow_MPa']['min'],
                tol_t=pc['thickness_mm'], tol_w=pc.get('groove_width_mm', pc['thickness_mm']), t_min=m['t_wall_min_mm']['max'],
                conductive=m['conductive'], ferromagnetic=m['ferromagnetic'], process=proc_id)


def str_mats(cx, cand, r_split=None):
    cb = cand['caseback']
    outer = str_material(cx.st, cb['material'], cb['process'])
    if cb.get('split'):
        centre = str_material(cx.st, cb['centre_material'], cb['centre_process'])
        return (lambda r: centre if r <= r_split + EPS else outer), dict(centre=centre, outer=outer)
    return (lambda r: outer), dict(outer=outer)


def c1_split(cx, cand, land_rmin):
    """G4-C1: metal centre plate confined to r <= minimum radiator inner radius - clearance; the polymer ring laps
    inward over the plate edge by the caseback bond land, so the joint [r_split - bond, r_split] must clear the charger
    land. Largest grid split radius satisfying both (most metal), else the smallest grid value as a diagnostic."""
    st = cx.st
    cb = cand['caseback']
    lim = min(st.res[r]['radial_mm'][0] for r in ('GNSS_RAD', 'WIFI_RAD')) - cb['centre_rf_clearance_mm']
    bl = st.P['bond_lands']['caseback_bond_land_mm']['max']
    rows = []
    for r in grid(cx.P['V16_split_radii_C1']):
        rows.append(dict(r_split=r, radiator_margin_mm=lim - r, charger_land_margin_mm=land_rmin - r, joint=[r - bl, r],
                         ok=lim - r >= -EPS and land_rmin - r >= -EPS))
    ok = [x for x in rows if x['ok']]
    sel = max(ok, key=lambda x: x['r_split']) if ok else min(rows, key=lambda x: x['r_split'])
    return dict(limit_mm=lim, rows=rows, selected=sel, feasible=bool(ok))


def str_geo(cx, cand, row, r_lim, chg_pose, r_split=None, pocket=None, extra_interrupters=()):
    st = cx.st
    sp = cx.ce[cand['id']].sp
    R = row['R_side'] + sp.pc_env['radius_mm']
    for a in row['arcs']:
        if a['z_extent'] == 'THROUGH_REAR_FACE':
            R = max(R, a['R_bore_arc_mm'] + sp.pc_env['radius_mm'])
    post_in = row['rcin'] + sp.pc_car['radius_mm'] + row['tcw'] + sp.pc_car['thickness_mm'] + st.P['c_insert_mm']['max']
    r_rib_out = min(r_lim, post_in) - st.P['c_insert_mm']['max']
    inter = []
    if chg_pose is not None:
        inter.append(dict(id='CHARGER_LAND', az=chg_pose['land_az'], r=[chg_pose['land_rmin'], chg_pose['land_rmax']]))
    if getattr(cx, 's14_interrupters', None) is None:
        g = st.s14geo
        cx.s14_interrupters = [it for it in (poly_interrupter(name, pts) for name, pts in
                                             [('S14_TAIL_CONSERVATIVE', g['tail_cons']), ('S14_TAIL_RELIEF', g['tail_relief_cons']),
                                              ('S14_THERMODE', g['thermode']), ('S14_U6_ISLAND', g['u6_island'])] +
                                             [('S14_SUPPORT_%d' % s['az'], s['poly']) for s in g['supports']]) if it is not None]
    inter += [dict(it) for it in cx.s14_interrupters]     # frozen S14 polygons: computed once per context
    inter += list(extra_interrupters)
    return dict(rb=cx.rb, r_step=cx.r_step, r_rib_in=cx.r_s14_clear, r_rib_out=r_rib_out, R=R, post_inner_r=post_in,
                r_split=r_split, pocket=pocket, interrupters=inter, gap_deg=None)


def poly_interrupter(name, pts):
    """Azimuth span (smallest covering arc) and radial range of a frozen plan polygon; None if it contains the centre."""
    if g4.pip((100.0, 100.0), list(pts)):
        return None
    azs = sorted(g4.polar(p)[1] for p in pts)
    gaps = [((azs[(i + 1) % len(azs)] - azs[i]) % 360.0, i) for i in range(len(azs))]
    gmax, i = max(gaps)
    a0, a1 = azs[(i + 1) % len(azs)], azs[i]
    return dict(id=name, az=[a0, a1], r=[poly_rmin(list(pts)), max(math.hypot(p[0] - 100.0, p[1] - 100.0) for p in pts)])


def rib_layout(geo, n, w, divisions):
    """Equally spaced spokes; a spoke is interrupted when its strip (half-width w/2) crosses an interrupter inside the
    structural radial interval. Phase chosen (pure function) to minimise the largest angular gap between credited
    spokes (LA-STR-5); with < 2 credited spokes no rib credit exists."""
    if n == 0:
        return dict(n=0, phase_deg=0.0, credited=[], interrupted=[], gap_deg=None)
    pitch = 360.0 / n
    best = None
    for k in range(divisions):
        phi0 = k * pitch / divisions
        cred, intr = [], []
        for i in range(n):
            a = (phi0 + i * pitch) % 360.0
            hit = None
            for it in geo['interrupters']:
                if it['r'][1] < geo['r_rib_in'] - EPS or it['r'][0] > geo['r_rib_out'] + EPS:
                    continue
                delta = math.degrees(math.asin(min(1.0, (w / 2.0) / max(it['r'][0], 1.0))))
                if g4.arc_has(a, (it['az'][0] - delta) % 360.0, (it['az'][1] + delta) % 360.0):
                    hit = it['id']
                    break
            (intr if hit else cred).append((a, hit))
        az = sorted(c[0] for c in cred)
        gap = max(((az[(j + 1) % len(az)] - az[j]) % 360.0) or 360.0 for j in range(len(az))) if len(az) >= 2 else None
        key = (gap is None, gap if gap is not None else 999.0, k)
        if best is None or key < best[0]:
            best = (key, dict(n=n, phase_deg=phi0, credited=[c[0] for c in cred], interrupted=[dict(az=a, by=h) for a, h in intr], gap_deg=gap))
    return best[1]


def str_limits(cx, cfg, mat_outer):
    zm = cx.zm
    top = cfg['t_out'] + mat_outer['tol_t'] + (cfg['h'] + mat_outer['tol_t'] if cfg['n'] > 0 and cfg['h'] > 0 else 0.0)
    st = cx.st
    c_defl = min(st.P['c_cb_rear_mm']['min'], cx.window['standoff_min_mm'])
    return dict(c_defl=c_defl, outline_r=st.s14geo['outline_r'], z_band_lo=zm['z_band_lo_adv'],
                rib_top_adv=top if cfg['n'] > 0 and cfg['h'] > 0 else None)


def str_key(s, sa):
    return (s['pass_'], min(s['stress_margin_MPa'] / sa, s['deflection_margin_mm'] / 0.05))


def lane_str(cx, cand, row, r_lim, chg_pose, full=True, only_cfg=None):
    st, P = cx.st, cx.P
    ce = cx.ce[cand['id']]
    sp = ce.sp
    split = c1_split(cx, cand, chg_pose['land_rmin']) if cand['caseback'].get('split') else None
    r_split = split['selected']['r_split'] if split else None
    mats, mset = str_mats(cx, cand, r_split)
    outer = mset['outer']
    inner_m = mset.get('centre', outer)
    K_t = P['V14_rib_geometry']['K_t']
    N = P['screen_b']['subregions']
    geo0 = str_geo(cx, cand, row, r_lim, chg_pose, r_split)
    # t_in window: pod residual (G4 H11-POD-RESIDUAL, inner material tolerance) and material floor
    tin_rows = []
    for t in grid(P['V12_caseback_thickness']['t_in']):
        pod = g4.run_check(sp.pod_residual(dict(t_w=cx.window['eligible_t_max'] or 0.5, t_in=t)), full=False)
        floor = t - inner_m['tol_t'] - inner_m['t_min']
        tin_rows.append(dict(t_in=t, pod_residual_mm=pod, material_floor_mm=floor, ok=pod >= -EPS and floor >= -EPS))
    count(len(tin_rows))
    tins = [x['t_in'] for x in tin_rows if x['ok']]
    tout_rows = []
    for t in grid(P['V12_caseback_thickness']['t_out']):
        per = g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=t), 0.0), full=False)
        floor = t - outer['tol_t'] - outer['t_min']
        tout_rows.append(dict(t_out=t, periphery_z_mm=per, material_floor_mm=floor, ok=per >= -EPS and floor >= -EPS))
    count(len(tout_rows))
    touts = [x['t_out'] for x in tout_rows if x['ok']]
    geometry_ok = bool(tins) and bool(touts)
    t_in_sel = max(tins) if tins else max(tin_rows, key=lambda x: min(x['pod_residual_mm'], x['material_floor_mm']))['t_in']
    t_outs = touts or [max(tout_rows, key=lambda x: min(x['periphery_z_mm'], x['material_floor_mm']))['t_out']]
    V13, V14 = P['V13_rib_counts'], P['V14_rib_geometry']
    configs = []
    for t_out in t_outs:
        configs.append(dict(t_in=t_in_sel, t_out=t_out, n=0, w=0.0, h=0.0))
        for n in [x for x in V13['spoke_options'] if x > 0]:
            for w in V14['width_options']:
                for h in V14['height_options']:
                    cfg = dict(t_in=t_in_sel, t_out=t_out, n=n, w=w, h=h)
                    lim = str_limits(cx, cfg, outer)
                    if lim['rib_top_adv'] > lim['z_band_lo'] + EPS:
                        continue
                    configs.append(cfg)
    if only_cfg is not None:
        configs = [dict(only_cfg)]
    evals = []
    for cfg in configs:
        lay = rib_layout(geo0, cfg['n'], cfg['w'], V13['phase_divisions'])
        geo = dict(geo0, gap_deg=lay['gap_deg'])
        s = screen_eval(geo, mats, cfg, 'B', N, cx.p, K_t, str_limits(cx, cfg, outer), 13)
        evals.append((cfg, lay, s))
    sa = outer['sigma_allow']
    rank = lambda e: (str_key(e[2], sa), -e[0]['n'], -e[0]['h'], -e[0]['w'], -e[0]['t_out'])
    best_cfg, best_lay, best_b = max(evals, key=rank)
    ribbed = [e for e in evals if e[0]['n'] > 0 and e[1]['gap_deg'] is not None]
    best_rib = max(ribbed, key=rank) if ribbed else None
    geo = dict(geo0, gap_deg=best_lay['gap_deg'])
    lim = str_limits(cx, best_cfg, outer)
    out = dict(lane='L-STR', geometry=geo, geometry_ok=geometry_ok, t_in_rows=tin_rows, t_out_rows=tout_rows, split=split,
               materials=mset, K_t=K_t, configs_evaluated=len(evals), selected=best_cfg, rib_layout=best_lay,
               screen_B=best_b, limits=lim,
               w_max_at_boss_all_configs=all(e[2]['w_max_mm'] - e[2]['w_boss_mm'] <= 1e-12 for e in evals),
               search=dict(t_in_selected=t_in_sel, t_out_values=t_outs, spoke_options=V13['spoke_options'], widths=V14['width_options'],
                           heights=V14['height_options'], ring_credit='none (LA-STR-4)', phases=V13['phase_divisions'],
                           objective='Screen B: pass, then min(stress margin / allowable, deflection margin / limit)'))
    if best_rib is not None and full:
        rc, rl, rs = best_rib
        rgeo = dict(geo0, gap_deg=rl['gap_deg'])
        rlim = str_limits(cx, rc, outer)
        rB = screen_eval(rgeo, mats, rc, 'B', N, cx.p, K_t, rlim, 41)
        rB2 = screen_eval(rgeo, mats, rc, 'B', 2 * N, cx.p, K_t, rlim, 41)
        rA = screen_eval(rgeo, mats, rc, 'A', N, cx.p, K_t, rlim, 41)
        sec = rib_D(outer['E'], outer['nu'], rc['t_out'] - outer['tol_t'], rc['w'] - outer['tol_w'], rc['h'] - outer['tol_t'],
                    rgeo['r_rib_out'] * math.radians(rl['gap_deg']))
        out['best_ribbed'] = dict(config=rc, rib_layout=rl, screen_B=rB, screen_A=rA,
                                  convergence=dict(sigma_N=rB['sigma_governing_MPa'], sigma_2N=rB2['sigma_governing_MPa'],
                                                   w_N=rB['w_max_mm'], w_2N=rB2['w_max_mm'],
                                                   rel_sigma=abs(rB['sigma_governing_MPa'] - rB2['sigma_governing_MPa']) / max(rB2['sigma_governing_MPa'], EPS),
                                                   rel_w=abs(rB['w_max_mm'] - rB2['w_max_mm']) / max(rB2['w_max_mm'], EPS)),
                                  stiffness_at_r_rib_out=dict(D_plate=sec[0], D_r=sec[1], ratio=sec[1] / sec[0], b_f=sec[2]['b_f'],
                                                              I_T=sec[2]['I_T'], I_inc=sec[2]['I_inc'], y_c=sec[2]['y_c']))
        if max(out['best_ribbed']['convergence']['rel_sigma'], out['best_ribbed']['convergence']['rel_w']) >= cx.P['screen_b']['convergence_max_rel']:
            raise StudyError('STOP: Screen-B N vs 2N convergence failure on the best ribbed configuration')
    if not full:
        out['physical_pass'] = geometry_ok and best_b['pass_']
        return out
    nb = 41
    sB = screen_eval(geo, mats, best_cfg, 'B', N, cx.p, K_t, lim, nb)
    sB2 = screen_eval(geo, mats, best_cfg, 'B', 2 * N, cx.p, K_t, lim, nb)
    sA = screen_eval(geo, mats, best_cfg, 'A', N, cx.p, K_t, lim, nb)
    conv = dict(N=N, sigma_N=sB['sigma_governing_MPa'], sigma_2N=sB2['sigma_governing_MPa'], w_N=sB['w_max_mm'], w_2N=sB2['w_max_mm'],
                rel_sigma=abs(sB['sigma_governing_MPa'] - sB2['sigma_governing_MPa']) / max(abs(sB2['sigma_governing_MPa']), EPS),
                rel_w=abs(sB['w_max_mm'] - sB2['w_max_mm']) / max(abs(sB2['w_max_mm']), EPS))
    conv['pass_'] = conv['rel_sigma'] < P['screen_b']['convergence_max_rel'] and conv['rel_w'] < P['screen_b']['convergence_max_rel']
    if not conv['pass_']:
        raise StudyError('STOP: Screen-B N vs 2N convergence failure (%.4f / %.4f)' % (conv['rel_sigma'], conv['rel_w']))
    mono = []
    for t in sorted(tins):
        c2 = dict(best_cfg, t_in=t)
        s2 = screen_eval(geo, mats, c2, 'B', N, cx.p, K_t, str_limits(cx, c2, outer))
        mono.append(dict(t_in=t, sigma=s2['sigma_governing_MPa'], w=s2['w_max_mm']))
    mono_ok = all(b['sigma'] <= a['sigma'] + 1e-9 and b['w'] <= a['w'] + 1e-12 for a, b in zip(mono, mono[1:]))
    if not mono_ok:
        raise StudyError('STOP: structural t_in pruning monotonicity violated')
    zband = (lim['z_band_lo'] - lim['rib_top_adv']) if lim['rib_top_adv'] is not None else None
    forb = dict(rear_pcb_and_g3_support_lands=dict(clearance_mm=lim['c_defl'], deflection_inside_outline_mm=sB['w_inside_outline_mm'],
                                                   margin_mm=sB['rear_contact_margin_mm'], contact=sB['rear_contact_margin_mm'] <= EPS),
                battery_and_lower_web=dict(rib_top_adv_mm=lim['rib_top_adv'], rib_band_deflection_mm=sB['w_rib_band_mm'],
                                           static_margin_mm=zband, loaded_margin_mm=sB['rib_band_margin_mm'],
                                           lower_web_clearance_mm=(cx.zm['z_lower_web_underside_adv'] - (lim['rib_top_adv'] + sB['w_rib_band_mm']))
                                           if lim['rib_top_adv'] is not None else None,
                                           contact=(sB['rib_band_margin_mm'] is not None and sB['rib_band_margin_mm'] < -EPS)))
    a_pass = sA['pass_']
    b_pass = sB['pass_']
    phys = geometry_ok and a_pass and b_pass
    out.update(screen_B=sB, screen_B_2N=sB2, screen_A=sA, convergence=conv, t_in_monotonicity=dict(rows=mono, pass_=mono_ok),
               forbidden_paths=forb, physical_pass=phys,
               thresholds=str_thresholds(cx, cand, geo, mats, best_cfg, mset, lim),
               fea_handoff=[x['id'] for x in st.I['fea_load_cases']],
               qualification='Planning screens only; FEA-1..FEA-4 (Q1) govern; no structural qualification claimed.')
    if split:
        q_line = cx.p * r_split / 2.0
        bl = st.P['bond_lands']['caseback_bond_land_mm']['max']
        out['split_bond'] = dict(r_split=r_split, shear_per_length_N_per_mm=q_line, bond_width_mm=bl, required_bond_shear_MPa=q_line / bl,
                                 credited=False, gate='SR-ADHESIVE',
                                 joint_check=g4.run_check(g4.spec('H16-SPLIT-JOINT', 'H16', 'split joint bond height', [
                                     sp.design('t_joint', best_cfg['t_in'] if r_split < cx.r_step else best_cfg['t_out']),
                                     sp.tol('thickness_tol', outer['tol_t']), sp.par('bond_land', 'max', st.P['bond_lands']['caseback_bond_land_mm'])],
                                     lambda v: v['t_joint'] - v['thickness_tol'] - v['bond_land']), full=False))
    return out


def iso_req_thickness(cx, mat, R, rb, r_step, which='uniform', t_in_fixed=None):
    """Smallest effective thickness for the loaded-boss isotropic screen to pass (stress <= allowable and deflection
    < clearance) with g4.annular_plate; 'uniform' both regions, 'outer' with the inner region fixed."""
    lim = min(cx.st.P['c_cb_rear_mm']['min'], cx.window['standoff_min_mm'])

    def ok(t):
        regs = [(rb, r_step, t if which == 'uniform' else t_in_fixed, mat['E'], mat['nu']), (r_step, R, t, mat['E'], mat['nu'])]
        r = g4.annular_plate(regs, cx.p, 'loaded_boss')
        count()
        return r['sigma'] <= mat['sigma_allow'] + 1e-9 and r['w'] < lim - 1e-12
    lo, hi = 0.2, 40.0
    if not ok(hi):
        return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi


def str_thresholds(cx, cand, geo, mats, cfg, mset, lim):
    st = cx.st
    out = {}
    for mid, proc in (('MAT-CERAMIC', 'PC-CERAMIC-GRIND'), ('MAT-NF-METAL', 'PC-METAL-MACH'), ('MAT-GF-POLY', 'PC-POLY-MOULD')):
        m = str_material(st, mid, proc)
        out[mid] = dict(required_uniform_effective_thickness_mm=iso_req_thickness(cx, m, geo['R'], geo['rb'], geo['r_step']),
                        tolerance_mm=m['tol_t'])
        t_eff = out[mid]['required_uniform_effective_thickness_mm']
        out[mid]['required_uniform_nominal_thickness_mm'] = None if t_eff is None else t_eff + m['tol_t']
        t_in_eff = cfg['t_in'] - m['tol_t']
        out[mid]['required_outer_effective_thickness_with_t_in_max_mm'] = iso_req_thickness(cx, m, geo['R'], geo['rb'], geo['r_step'], 'outer', t_in_eff)
        sol_c = plate_solve([iso_region(geo['rb'], geo['r_step'], t_in_eff, m['E'], m['nu'])], cx.p, 'loaded_boss', 'clamped', 81)
        sol_s = plate_solve([iso_region(geo['rb'], geo['r_step'], t_in_eff, m['E'], m['nu'])], cx.p, 'loaded_boss', 'ss', 81)
        out[mid]['rigid_outer_annulus_bound_MPa'] = dict(
            clamped_at_r_step=max(6.0 * max(abs(x['Mr']), abs(x['Mt'])) / t_in_eff ** 2 for x in sol_c[0]['samples']),
            simply_supported_at_r_step=max(6.0 * max(abs(x['Mr']), abs(x['Mt'])) / t_in_eff ** 2 for x in sol_s[0]['samples']),
            t_in_effective_mm=t_in_eff, allowable_MPa=m['sigma_allow'])
    outer = mset['outer']
    z_avail = cx.zm['z_band_lo_adv'] - outer['tol_t']
    t_req = out[outer['id']]['required_uniform_nominal_thickness_mm']
    out['z_available_for_uniform_plate_mm'] = z_avail
    out['z_shortfall_mm'] = None if t_req is None else max(0.0, t_req - z_avail)
    t_in_max = max([x for x in grid(cx.P['V12_caseback_thickness']['t_in'])], default=None)
    out['inner_region_z_cap'] = 'H11-POD-RESIDUAL (G4) limits t_in; t_in_selected=%.2f' % cfg['t_in']
    out['inner_region_requirement_exceeds_pod_residual'] = (t_req is not None and t_req > cfg['t_in'] + EPS)
    del t_in_max
    return out


def pocket_interrupter(env):
    """Radial band and azimuth span (circle radii included) of an LRA pocket footprint (circle-cover envelope)."""
    rs = [math.hypot(p[0] - 100.0, p[1] - 100.0) for p, _ in env]
    azs = [g4.polar(p)[1] for p, _ in env]
    span = max(math.degrees(math.asin(min(1.0, rho / max(r, 1.0)))) for r, (_, rho) in zip(rs, env))
    return dict(id='LRA_POCKET', az=[(min(azs) - span) % 360.0, (max(azs) + span) % 360.0],
                r=[min(r - rho for r, (_, rho) in zip(rs, env)), max(r + rho for r, (_, rho) in zip(rs, env))])


def str_lra_rescreen(cx, cand, out, pose_env, t_res, rel=None, configs=()):
    """Explicit structural re-screen of a pocketed LRA variant: conservative axisymmetric band at the residual thickness over
    the pocket radial extent, ribs crossing the pocket azimuth span interrupted (Screen B at the selected configuration).
    With the design-point relaxed model, the production check that it dominates the pocketed model of every given
    configuration (the dominance the joint-search re-screen relies on)."""
    if pose_env is None:
        return None
    it = pocket_interrupter(pose_env)
    r0, r1 = it['r']
    geo = dict(out['geometry'], pocket=[max(r0, out['geometry']['r_step']), min(r1, out['geometry']['R']), t_res],
               interrupters=out['geometry']['interrupters'] + [it])
    cfg = out['selected']
    lay = rib_layout(geo, cfg['n'], cfg['w'], cx.P['V13_rib_counts']['phase_divisions'])
    geo['gap_deg'] = lay['gap_deg']
    mats, mset = str_mats(cx, cand, (out['split'] or {}).get('selected', {}).get('r_split'))
    N = cx.P['screen_b']['subregions']
    s = screen_eval(geo, mats, cfg, 'B', N, cx.p, cx.P['V14_rib_geometry']['K_t'], str_limits(cx, cfg, mset['outer']))
    dom = None
    if rel is not None:
        bad, n = [], 0
        lays = {}
        m_out = mset['outer']
        for c in configs:
            if (c['n'], c['w']) not in lays:
                lays[(c['n'], c['w'])] = rib_layout(geo, c['n'], c['w'], cx.P['V13_rib_counts']['phase_divisions'])['gap_deg']
            for d in cx.P['V22_lra_pocket']['pocket_depths_mm']:
                if c['t_out'] - d < m_out['t_min'] + m_out['tol_t'] - EPS:
                    continue
                g = dict(geo, gap_deg=lays[(c['n'], c['w'])], pocket=[geo['pocket'][0], geo['pocket'][1], c['t_out'] - d])
                bad += loewner_violations(rel, str_regions(g, mats, c, 'B', N), geo['R'])
                n += 1
        count(n)
        if bad:
            raise StudyError('STOP: design-point relaxed model does not dominate a pocketed configuration: %s' % bad[:2])
        dom = dict(configs_checked=n, dominated=True)
    return dict(pocket_band_mm=geo['pocket'], interrupter=it, rib_layout=lay, screen_B=s, relaxed_dominates_pocketed=dom,
                model='conservative axisymmetric smear of the pocket over its radial band; ribs crossing the pocket span interrupted')


# --------------------------------------------------------------------------------------------
# R2-1: per-design-point structural feasibility (no endpoint flattening). Minimum-potential-energy bound:
#   for a linear elastic plate with fixed kinematic constraints, compliance C = f.u = sup_v [2 f.v - a(v, v)] is
#   non-increasing in the stiffness form a(.,.) (Loewner order). The relaxed model takes, region by region, the Loewner
#   maximum over EVERY admissible configuration (t_in, t_out, spokes, width, height, phase) of the Screen-B constitutive
#   matrix [[D_r, D_1], [D_1, D_theta]]; the smeared rib stiffness of a subregion is evaluated at its INNER radius, the
#   largest value inside it because D_r(s) = D_p + E (w h^3 / (12 s) + d^2 t w h / (s t + w h)) (b_f = s) or
#   D_p + E I_inc / s (b_f = w + 12 t) is strictly decreasing in the rib spacing s = r * gap. With all pressure in one
#   direction, C <= w_max * P (P = q pi R^2), so every admissible configuration has a continuum deflection
#   w_max >= C_cfg / P >= C_relaxed / P. If C_relaxed / P >= the deflection limit, Screen B (hence R1-H09) fails for
#   every configuration at that point; otherwise the exact configuration search decides that point.
# --------------------------------------------------------------------------------------------
def struct_context(cx, cand):
    """Admissible caseback plate thicknesses (G4 pod residual / rear periphery and material floors, as lane_str) and the
    complete admissible configuration set of V12 x V13 x V14 (rib top below the LA-Z-2 band). Candidate constant."""
    cache = cx.__dict__.setdefault('sctx_cache', {})
    if cand['id'] in cache:
        return cache[cand['id']]
    st, P = cx.st, cx.P
    sp = cx.ce[cand['id']].sp
    _, mset = str_mats(cx, cand, 18.0 if cand['caseback'].get('split') else None)
    outer = mset['outer']
    inner_m = mset.get('centre', outer)
    tins = [t for t in grid(P['V12_caseback_thickness']['t_in'])
            if g4.run_check(sp.pod_residual(dict(t_w=cx.window['eligible_t_max'] or 0.5, t_in=t)), full=False) >= -EPS
            and t - inner_m['tol_t'] - inner_m['t_min'] >= -EPS]
    touts = [t for t in grid(P['V12_caseback_thickness']['t_out'])
             if g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=t), 0.0), full=False) >= -EPS and t - outer['tol_t'] - outer['t_min'] >= -EPS]
    count(len(grid(P['V12_caseback_thickness']['t_in'])) + len(grid(P['V12_caseback_thickness']['t_out'])))
    V13, V14 = P['V13_rib_counts'], P['V14_rib_geometry']
    cfgs = []
    for t_in in tins:
        for t_out in touts:
            cfgs.append(dict(t_in=t_in, t_out=t_out, n=0, w=0.0, h=0.0))
            for n in [x for x in V13['spoke_options'] if x > 0]:
                for w in V14['width_options']:
                    for h in V14['height_options']:
                        cfg = dict(t_in=t_in, t_out=t_out, n=n, w=w, h=h)
                        if str_limits(cx, cfg, outer)['rib_top_adv'] <= cx.zm['z_band_lo_adv'] + EPS:
                            cfgs.append(cfg)
    out = dict(t_in=tins, t_out=touts, configs=cfgs, geometry_ok=bool(tins) and bool(touts),
               c_defl=min(st.P['c_cb_rear_mm']['min'], cx.window['standoff_min_mm']))
    cache[cand['id']] = out
    return out


def relaxed_model(cx, cand, sctx, geo, mats):
    """Loewner-maximal (stiffest admissible) Screen-B model over sctx['configs'] at one structural geometry, regions
    rb .. r_rib_out; the outer plate r_rib_out .. R is appended per R (isotropic, thickest admissible t_out)."""
    P = cx.P
    N = P['screen_b']['subregions']
    bps = {geo['rb'], geo['r_step'], geo['r_rib_in'], geo['r_rib_out']}
    if geo.get('r_split'):
        bps.add(geo['r_split'])
    for j in range(1, N):
        bps.add(geo['r_rib_in'] + (geo['r_rib_out'] - geo['r_rib_in']) * j / N)
    bps = sorted(b for b in bps if geo['rb'] - EPS <= b <= geo['r_rib_out'] + EPS)
    gaps = {}
    for c in sctx['configs']:
        if (c['n'], c['w']) not in gaps:
            gaps[(c['n'], c['w'])] = rib_layout(geo, c['n'], c['w'], P['V13_rib_counts']['phase_divisions'])['gap_deg'] if c['n'] > 0 else None
    t_in_max, t_out_max = max(sctx['t_in']), max(sctx['t_out'])
    regs = []
    for a, b in zip(bps, bps[1:]):
        if b - a < 1e-9:
            continue
        m = mats((a + b) / 2.0)
        E, nu = m['E'], m['nu']
        Dof = lambda t: E * t ** 3 / (12.0 * (1.0 - nu * nu))
        if (a + b) / 2.0 < geo['r_step']:
            D = Dof(t_in_max - m['tol_t'])
            regs.append(dict(r0=a, r1=b, Dr=D, Dt=D, D1=nu * D, k=1.0, E=E, nu=nu, t=t_in_max - m['tol_t'], kind='relaxed inner', material=m['id']))
            continue
        Dp_star = Dof(t_out_max - m['tol_t'])
        Dr_star = Dp_star
        if geo['r_rib_in'] - EPS <= a and b <= geo['r_rib_out'] + EPS:
            for c in sctx['configs']:
                gap = gaps[(c['n'], c['w'])]
                if c['n'] == 0 or gap is None or c['h'] <= 0.0:
                    continue
                t = c['t_out'] - m['tol_t']
                Dp, Dr, _ = rib_D(E, nu, t, c['w'] - m['tol_w'], c['h'] - m['tol_t'], a * math.radians(gap))
                Dr_star = max(Dr_star, Dr + nu * nu * (Dp_star - Dp))
            count(len(sctx['configs']))
        regs.append(dict(r0=a, r1=b, Dr=Dr_star, Dt=Dp_star, D1=nu * Dp_star, k=math.sqrt(Dp_star / Dr_star), E=E, nu=nu,
                         t=t_out_max - m['tol_t'], kind='relaxed outer', material=m['id']))
    mo = mats((geo['r_rib_out'] + geo['R']) / 2.0)
    Do = mo['E'] * (t_out_max - mo['tol_t']) ** 3 / (12.0 * (1.0 - mo['nu'] ** 2))
    return dict(regions=regs, outer=dict(Dr=Do, Dt=Do, D1=mo['nu'] * Do, k=1.0, E=mo['E'], nu=mo['nu'], t=t_out_max - mo['tol_t'],
                                         kind='relaxed outer plate', material=mo['id']), r_rib_out=geo['r_rib_out'],
                gaps={'%d/%.1f' % k: v for k, v in sorted(gaps.items())})


def w_rint(reg, x, q, a, b):
    """Exact integral of r w(r) over [a, b] for one region solution x (closed forms of _ortho's w basis and particular)."""
    Dr, k, rr = reg['Dr'], reg['k'], reg['r0']
    c = q / (2.0 * Dr * (9.0 - k * k))

    def F(r):
        if abs(1.0 - k) < 1e-12:
            ln = math.log(r / rr)
            basis = [r * r / 2.0, r ** 4 / 8.0, r * r / 2.0 * ln - r * r / 4.0, -((r ** 4 * ln / 2.0 - 3.0 * r ** 4 / 8.0) / 8.0) / Dr]
        else:
            rr1k, den = rr ** (1.0 - k), 1.0 - k * k
            basis = [r * r / 2.0, r ** (k + 3.0) / ((k + 1.0) * (k + 3.0)), (r ** (3.0 - k) / (3.0 - k) - rr1k * r * r / 2.0) / (1.0 - k),
                     -((r ** 4 / 8.0 - rr1k * r ** (k + 3.0) / ((k + 1.0) * (k + 3.0))) / den) / Dr]
        return sum(xi * bi for xi, bi in zip(x, basis)) + c * r ** 6 / 24.0
    return F(b) - F(a)


def compliance(sol, q):
    """C = F_boss w(rb) + integral q w dA (exact) for a loaded-boss / simply-supported plate_solve solution."""
    reg0, x0 = sol[0]['region'], sol[0]['x']
    rb = reg0['r0']
    b0 = _ortho(rb, reg0, q)
    w_rb = sum(xi * bi for xi, bi in zip(x0, b0['w'][0])) + b0['w'][1]
    C = q * math.pi * rb * rb * w_rb
    for s in sol:
        C += 2.0 * math.pi * q * w_rint(s['region'], s['x'], q, s['region']['r0'], s['region']['r1'])
    return C, w_rb


def bound_ratio(cx, rel, R):
    """Lower bound (mm) on the continuum deflection of every admissible configuration at outer support radius R."""
    regs = [dict(x) for x in rel['regions']] + [dict(rel['outer'], r0=rel['r_rib_out'], r1=R)]
    sol = plate_solve(regs, cx.p, 'loaded_boss', 'ss', 2)
    C, _ = compliance(sol, cx.p)
    return C / (cx.p * math.pi * R * R)


def loewner_violations(rel, regs, R):
    """Every region of a configuration model lies below the relaxed model (2x2 Loewner order) at its midpoint."""
    allr = rel['regions'] + [dict(rel['outer'], r0=rel['r_rib_out'], r1=R)]
    bad = []
    for rg in regs:
        over = [x for x in allr if x['r0'] < rg['r1'] - 1e-9 and x['r1'] > rg['r0'] + 1e-9]   # every relaxed region it overlaps
        if not over or min(x['r0'] for x in over) > rg['r0'] + 1e-9 or max(x['r1'] for x in over) < rg['r1'] - 1e-9:
            bad.append('relaxed model does not cover r %.4f .. %.4f' % (rg['r0'], rg['r1']))
            continue
        for rr in over:
            dr, dt, d1 = rr['Dr'] - rg['Dr'], rr['Dt'] - rg['Dt'], rr['D1'] - rg['D1']
            tol = 1e-9 * max(1.0, rr['Dr'])
            if dr < -tol or dt < -tol or dr * dt - d1 * d1 < -tol * max(1.0, rr['Dr']):
                bad.append('relaxed model not stiffer on r %.4f .. %.4f (dDr %.3e dDt %.3e dD1 %.3e)' % (
                    max(rr['r0'], rg['r0']), min(rr['r1'], rg['r1']), dr, dt, d1))
    return bad


def struct_R_values(cx, cand, row, geo):
    """Plate radii reachable by the admissible V03 arc thicknesses at this point: the selected arcs first. A point whose
    arcs are all inside MAIN / BATTERY, or with an arc lacking any own-feasible thickness (H05-GEOM fails for every arc
    choice there), has the single selected geometry."""
    sp = cx.ce[cand['id']].sp
    tol = sp.pc_env['radius_mm']
    through = [a for a in row['arcs'] if a['z_extent'] == 'THROUGH_REAR_FACE']
    if not through or any(a['search']['diagnostic'] for a in row['arcs']):
        return [geo['R']]
    m_max = min(a['search']['t_hi_mm'] for a in through)
    ms = sorted({t for a in through for t in a['search']['admissible_mm'] if t <= m_max + EPS}, reverse=True)
    Rs = [geo['R']] + [max(row['R_side'] + tol, row['D'] / 2.0 - m + tol) for m in ms]
    out = []
    for R in Rs:
        if all(abs(R - x) > 1e-9 for x in out):
            out.append(R)
    return out


def struct_exact(cx, cand, sctx, geo, mats, R, pocket=None, configs=None):
    """Exact Screen-B / Screen-A configuration search at one geometry (used only where the bound is inconclusive and for
    pocketed LRA variants in the same case): PASS iff some configuration of `configs` (default: every admissible configuration
    of the point) passes both screens. Returns the configuration, its rib layout and the (t_in, t_out) pairs evaluated."""
    P = cx.P
    outer = mats(R - 1e-6)
    g0 = dict(geo, R=R, pocket=pocket)
    if pocket:
        g0['interrupters'] = list(geo['interrupters']) + [pocket[3]]
        g0['pocket'] = pocket[:3]
    cfgs = sctx['configs'] if configs is None else configs
    lays = {}
    best = None
    pairs = sorted({(c['t_in'], c['t_out']) for c in cfgs})
    # R4-1: the structural geometry this search actually used (plate radius, rib radii, split radius, pocket band / residual and
    # every rib interrupter, pocket included), returned so that an evaluated identity is derived from it, never from a claim
    used = dict(R=R, rb=g0['rb'], r_step=g0['r_step'], r_rib_in=g0['r_rib_in'], r_rib_out=g0['r_rib_out'], r_split=g0.get('r_split'),
                pocket=list(g0['pocket']) if g0.get('pocket') else None,
                interrupters=[dict(id=i['id'], az=list(i['az']), r=list(i['r'])) for i in g0['interrupters']])
    for cfg in cfgs:
        if (cfg['n'], cfg['w']) not in lays:
            lays[(cfg['n'], cfg['w'])] = rib_layout(g0, cfg['n'], cfg['w'], P['V13_rib_counts']['phase_divisions'])
        g = dict(g0, gap_deg=lays[(cfg['n'], cfg['w'])]['gap_deg'])
        lim = str_limits(cx, cfg, outer)
        sB = screen_eval(g, mats, cfg, 'B', P['screen_b']['subregions'], cx.p, P['V14_rib_geometry']['K_t'], lim, 13)
        key = str_key(sB, outer['sigma_allow'])
        if best is None or key > best[0]:
            best = (key, cfg, sB)
        if sB['pass_']:
            sA = screen_eval(g, mats, cfg, 'A', P['screen_b']['subregions'], cx.p, P['V14_rib_geometry']['K_t'], lim, 13)
            if sA['pass_']:
                return dict(pass_=True, config=cfg, sigma_B=sB['sigma_governing_MPa'], w_B=sB['w_max_mm'], sigma_A=sA['sigma_governing_MPa'],
                            rib_layout=lays[(cfg['n'], cfg['w'])], pairs_evaluated=pairs, configs_evaluated=len(cfgs), geometry_used=used)
    if best is None:
        raise StudyError('STOP: exact structural search without any admissible configuration')
    return dict(pass_=False, config=best[1], sigma_B=best[2]['sigma_governing_MPa'], w_B=best[2]['w_max_mm'], sigma_A=None,
                rib_layout=lays[(best[1]['n'], best[1]['w'])], pairs_evaluated=pairs, configs_evaluated=len(cfgs), geometry_used=used)


# --------------------------------------------------------------------------------------------
# R4-1: canonical LRA physical-combination identity. One constructor (lra_identity) is fed either by the CLAIMED objects of a
# fit (class record, pose, plate at the design point) or by what the structural fallback ACTUALLY evaluated (the circles it
# consumed, the structural geometry struct_exact used, the plate pair it searched, the materials under the band it modelled,
# the exclusion set and r_lim of its plan re-check); pose and class of the evaluated identity are derived from the circles.
# --------------------------------------------------------------------------------------------
LRA_IDENTITY_KEYS = ('candidate', 'plate', 'pocket', 'r_lim_mm', 'pose', 'lra_class', 'body_envelope', 'lead_envelope', 'exit_envelope',
                     'z_fit', 'plan_fit', 'structure', 'charger', 'seal_flange', 'plan_exclusions')
LRA_ENV_TOL = 1e-5


def canon(o):
    return json.dumps(rounded(o), sort_keys=True)


def circ_list(env):
    return [[q[0], q[1], rho] for q, rho in env]


def same(a, b, tol=1e-7):
    """Canonical identity equality: equal keys / lengths / strings / booleans, numbers within tol (identity values are mm / deg;
    every adversarial change of interest is orders of magnitude larger)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(same(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same(x, y, tol) for x, y in zip(a, b))
    return a == b


def lra_class_physical(cls):
    """Physical record of an LRA class from its authoritative definition: shape, body plan dimensions, body and envelope height,
    lead / exit envelope (supplied classes, C-R1-08)."""
    dims = ['diameter_mm'] if cls['shape'] == 'coin' else ['length_mm', 'width_mm']
    le = cls.get('lead_exit_envelope_mm')
    return dict(id=cls['id'], supplied=bool(cls.get('supplied')), shape=cls['shape'], body_mm={f: cls[f]['max'] for f in dims},
                body_height_mm=cls['height_mm']['max'], envelope_height_mm=lra_class_height(cls),
                lead_exit_mm=None if not le else dict(length=le['length_mm']['max'], width=le['width_mm']['max'],
                                                      height=le['height_mm']['max'], exit=le['exit']))


def lra_class_envelope(st, cls, pose):
    """(body, lead) plan circles of a class record at a pose: g4.pose_envelope for an authored class, supplied_envelope (body + lead /
    exit) for a supplied class."""
    if cls.get('supplied'):
        return supplied_envelope(cls, pose)
    if not any(c['id'] == cls['id'] for c in st.I['lra_classes']):
        raise StudyError('STOP: LRA class %s is neither authored nor supplied' % cls['id'])
    return g4.pose_envelope(st, dict(cls=cls['id'], az=pose['az'], r=pose['r'], ori=pose.get('ori'))), []


def env_equal(a, b):
    return len(a) == len(b) and all(math.dist(p, q) <= LRA_ENV_TOL and abs(r - s) <= LRA_ENV_TOL for (p, r), (q, s) in zip(a, b))


def centroid(env):
    return (sum(q[0] for q, _ in env) / len(env), sum(q[1] for q, _ in env) / len(env))


def lra_pose_from_body(body):
    """R4-1: pose of a body plan envelope derived from its circles alone: centre = centroid of the circle centres (radius / azimuth by
    g4.polar); orientation from the long axis of a multi-circle (rectangle) cover: 0 = long axis tangential, 90 = radial; a single
    circle carries no orientation."""
    r, az = g4.polar(centroid(body))
    ori = None
    if len(body) > 1:
        (x0, y0), (x1, y1) = body[0][0], body[-1][0]
        rel = (math.degrees(math.atan2(y1 - y0, x1 - x0)) - (az - 90.0)) % 180.0
        ori = 90 if min(rel, 180.0 - rel) < 1e-6 else (0 if abs(rel - 90.0) < 1e-6 else 'off-grid %.6f deg' % rel)
    return dict(r_mm=round(r, 6) + 0.0, az_deg=round(az, 6) % 360.0 + 0.0, orientation=ori)


def lra_exit_from(body, lead):
    """Lead / exit direction derived from the circles: the direction of the lead cover centroid from the body centroid in the pose
    frame (radial_out / radial_in / cw / ccw) and that distance; None without a lead / exit envelope."""
    if not lead:
        return None
    bc, lc = centroid(body), centroid(lead)
    dist = math.dist(bc, lc)
    d = ((lc[0] - bc[0]) / dist, (lc[1] - bc[1]) / dist)
    t = math.radians(g4.polar(bc)[1])
    a = d[0] * math.sin(t) - d[1] * math.cos(t)
    b = d[0] * math.cos(t) + d[1] * math.sin(t)
    name = next((k for k, (x, y) in sorted(LRA_EXIT_DIRS.items()) if abs(a - x) < 1e-6 and abs(b - y) < 1e-6), 'off-axis')
    return dict(direction=name, body_to_lead_centre_mm=dist)


def lra_plate(t_in, t_out, residual, mats):
    return dict(t_in_mm=t_in, t_out_mm=t_out, depth_mm=None if t_out is None else round(t_out - residual, 9) + 0.0, residual_mm=residual,
                materials=[m['id'] for m in mats], processes=[m['process'] for m in mats], tol_t_mm=[m['tol_t'] for m in mats],
                t_min_mm=[m['t_min'] for m in mats])


def lra_z_fit(cx, residual, mats, cphys):
    """LA-Z-2 ceiling over the pocket floor (mount allowance, top clearance, residual + the largest thickness tolerance under the
    pocket) against the class envelope height."""
    st, zm = cx.st, cx.zm
    c_top, mount = st.P['c_lra_top_mm']['max'], st.P['lra_mount_mm']['max']
    tol = max(m['tol_t'] for m in mats)
    H = zm['z_band_lo_adv'] - c_top - mount - (residual + tol)
    h = (cphys or {}).get('envelope_height_mm')
    return dict(band_lo_adv_mm=zm['z_band_lo_adv'], c_lra_top_mm=c_top, lra_mount_mm=mount, residual_mm=residual, residual_tol_mm=tol,
                ceiling_mm=H, class_envelope_height_mm=h, fits=None if h is None else h <= H + EPS)


def lra_plan_check(cx, cand, env, lctx):
    """Plan feasibility of a physical envelope at the design point: outer limit r_lim, S14 outline, the global G4 LRA exclusions and
    the local exclusion set (screws, case-side supports, bores / bosses, seal structure, pod frame, U7 lead exit, charger block /
    land, conductor records, credited ribs)."""
    st = cx.st
    count()
    c_plan = cx.poses['c_plan']
    rmax = max(math.hypot(q[0] - 100.0, q[1] - 100.0) + rho for q, rho in env)
    rmin = min(math.hypot(q[0] - 100.0, q[1] - 100.0) - rho for q, rho in env)
    viol = ['OUTER_LIMIT'] if rmax + c_plan > lctx['r_lim'] + EPS else []
    if rmin < st.s14geo['outline_r'] + c_plan:
        viol.append('S14_OUTLINE')
    viol += g4.lra_pose_violations(st, env, cx.poses) + g4.local_pose_violations(st, cx.ce[cand['id']], lctx['dp_g4'], env, lctx['ex'])
    return sorted(set(viol))


def lra_identity(cx, cand, plate, pocket, r_lim, pose, cphys, body, lead, zfit, viol, used, ex):
    """The canonical physical identity (LRA_IDENTITY_KEYS) from physical inputs only."""
    exd = {}
    for n, g in ex:
        exd.setdefault(n, g)
    seal = exd.get('CASEBACK_SEAL_STRUCTURE')
    chg_it = next((i for i in used['interrupters'] if i['id'] == 'CHARGER_LAND'), None)
    poly = lambda g: None if g is None else [list(q) for q in g['pts']]
    return dict(
        candidate=cand['id'], plate=plate, pocket=pocket, r_lim_mm=r_lim, pose=pose, lra_class=cphys,
        body_envelope=dict(circles=circ_list(body)), lead_envelope=dict(circles=circ_list(lead)), exit_envelope=lra_exit_from(body, lead),
        z_fit=zfit, plan_fit=dict(violations=sorted(viol)),
        structure=dict(R_mm=used['R'], rb_mm=used['rb'], r_step_mm=used['r_step'], r_rib_in_mm=used['r_rib_in'], r_rib_out_mm=used['r_rib_out'],
                       r_split_mm=used.get('r_split'), pocket_band_residual=list(used['pocket']) if used.get('pocket') else None,
                       interrupters=[[i['id'], list(i['az']), list(i['r'])] for i in used['interrupters']]),
        charger=dict(block_poly=poly(exd.get('CHG_CONTACT_BLOCK')), land_poly=poly(exd.get('CHG_LAND')),
                     land_interrupter=None if chg_it is None else [list(chg_it['az']), list(chg_it['r'])]),
        seal_flange=dict(r_lim_mm=r_lim, plate_R_mm=used['R'], seal_structure_r_mm=None if seal is None else list(seal['r'])),
        plan_exclusions=dict(supports=sorted(n for n, _ in ex if 'SUP' in n or 'SCREW' in n), items=[[n, g] for n, g in ex]))


def lra_claimed_identity(cx, cand, cls, pose, plate, mats_fn, geo, lctx):
    """R4-1: the identity a fit claims - the claimed class record, pose and plate at the design point (structural geometry `geo`,
    exclusions, r_lim), through the same constructors as the evaluated identity; plan_fit claims no violation."""
    body, lead = lra_class_envelope(cx.st, cls, pose)
    env = body + lead
    it = pocket_interrupter(env)
    band = [max(it['r'][0], geo['r_step']), min(it['r'][1], geo['R'])]
    t_in, t_out, _, residual = plate
    mats = lra_materials_at(mats_fn, env)
    cphys = lra_class_physical(cls)
    used = dict(R=geo['R'], rb=geo['rb'], r_step=geo['r_step'], r_rib_in=geo['r_rib_in'], r_rib_out=geo['r_rib_out'], r_split=geo.get('r_split'),
                pocket=[band[0], band[1], residual], interrupters=list(geo['interrupters']) + [it])
    return lra_identity(cx, cand, lra_plate(t_in, t_out, residual, mats),
                        dict(footprint_r_mm=list(it['r']), footprint_az_deg=list(it['az']), band_mm=band, residual_mm=residual), lctx['r_lim'],
                        dict(r_mm=round(float(pose['r']), 6) + 0.0, az_deg=round(float(pose['az']), 6) % 360.0 + 0.0, orientation=pose.get('ori')),
                        cphys, body, lead, lra_z_fit(cx, residual, mats, cphys), [], used, lctx['ex'])


def lra_evaluated_identity(cx, cand, body, lead, ex_res, mats_fn, lctx, viol):
    """R4-1: the identity of what the fallback ACTUALLY evaluated: the circles it consumed (pose and class derived from them: the
    unique authoritative class whose envelope at the derived pose reproduces the circles), the structural geometry struct_exact used
    (pocket band / residual / interrupter included), the single plate pair it searched, the materials under the band it modelled,
    and the r_lim / exclusion set of its plan re-check."""
    used = ex_res['geometry_used']
    pairs = ex_res['pairs_evaluated']
    t_in, t_out = (pairs[0][0], pairs[0][1]) if len(pairs) == 1 else (None, None)
    b0, b1, residual = used['pocket']
    m0, m1 = mats_fn(max(b0, 1e-3)), mats_fn(b1)
    mats = [m0] if m0['id'] == m1['id'] else [m0, m1]
    it = next(i for i in used['interrupters'] if i['id'] == 'LRA_POCKET')
    pose = lra_pose_from_body(body)
    rp = dict(r=pose['r_mm'], az=pose['az_deg'], ori=pose['orientation'])
    matches = []
    for c in lctx['classes']:
        try:
            cb_, cl_ = lra_class_envelope(cx.st, c, rp)
        except (StudyError, TypeError, KeyError):
            continue
        if env_equal(cb_, body) and env_equal(cl_, lead):
            matches.append(c)
    cphys = lra_class_physical(matches[0]) if len(matches) == 1 else dict(id=None, matches=sorted(c['id'] for c in matches))
    return lra_identity(cx, cand, lra_plate(t_in, t_out, residual, mats),
                        dict(footprint_r_mm=list(it['r']), footprint_az_deg=list(it['az']), band_mm=[b0, b1], residual_mm=residual),
                        lctx['r_lim'], pose, cphys, body, lead, lra_z_fit(cx, residual, mats, cphys if len(matches) == 1 else None), viol,
                        used, lctx['ex'])


def lra_struct_fallback(cx, cand, sctx, strl, mats_fn, claimed, phys, plate, lctx):
    """R4-1 exact structural fallback of ONE credited LRA combination. It evaluates the PHYSICAL inputs it is given - the body / lead
    circles `phys`, the plate `plate` = (t_in, t_out, depth, residual), the design-point structural geometry strl['geometry'] and the
    plan context lctx (classes, exclusion set, dp, r_lim) - with only the rib configuration free; the evaluated identity is derived
    from what it consumed (lra_evaluated_identity) and must equal the claimed identity key by key, else STOP."""
    body, lead = list(phys['body']), list(phys['lead'])
    env = body + lead
    t_in, t_out, depth, residual = plate
    if t_in not in sctx['t_in'] or t_out not in sctx['t_out'] or abs(t_out - depth - residual) > 1e-9:
        raise StudyError('STOP: LRA combination outside the admissible plate set or with an inconsistent residual')
    cfgs = [c for c in sctx['configs'] if c['t_in'] == t_in and c['t_out'] == t_out]
    g = strl['geometry']
    it = pocket_interrupter(env)
    pocket = (max(it['r'][0], g['r_step']), min(it['r'][1], g['R']), residual, it)
    ex_ = struct_exact(cx, cand, sctx, g, mats_fn, g['R'], pocket=pocket, configs=cfgs)
    viol = lra_plan_check(cx, cand, env, lctx)
    cfg = ex_['config']
    rec = dict(pass_=ex_['pass_'], combination=claimed, evaluated=lra_evaluated_identity(cx, cand, body, lead, ex_, mats_fn, lctx, viol),
               structural=dict(rib_config=dict((k, cfg[k]) for k in ('n', 'w', 'h')), credited_spokes=ex_['rib_layout']['credited'],
                               interrupted_spokes=ex_['rib_layout']['interrupted'], pairs_evaluated=[list(x) for x in ex_['pairs_evaluated']],
                               configs_evaluated=ex_['configs_evaluated']),
               sigma_B=ex_['sigma_B'], w_B=ex_['w_B'], sigma_A=ex_['sigma_A'])
    bad = lra_binding_problems(rec)
    if bad:
        raise StudyError('STOP: LRA structural fallback not bound to its physical combination: %s' % '; '.join(bad))
    return rec


def lra_binding_problems(rec):
    """R4-1: claimed identity == evaluated identity key by key (canonical rounding); only the claimed (t_in, t_out) plate evaluated."""
    c, e = rec['combination'], rec['evaluated']
    bad = []
    if set(c) != set(LRA_IDENTITY_KEYS) or set(e) != set(LRA_IDENTITY_KEYS):
        bad.append('identity keys incomplete')
    for k in LRA_IDENTITY_KEYS:
        if not same(c.get(k), e.get(k)):
            bad.append('%s: claimed %s, evaluated %s' % (k, canon(c.get(k))[:120], canon(e.get(k))[:120]))
    pl = c.get('plate') or {}
    if rec['structural']['pairs_evaluated'] != [[pl.get('t_in_mm'), pl.get('t_out_mm')]]:
        bad.append('plate pairs evaluated %s differ from the claimed (t_in, t_out)' % rec['structural']['pairs_evaluated'])
    return bad


def lra_authoritative_classes(cx, L_lra, r1in):
    """Authored G4 classes and the accepted supplied classes (C-R1-08 validation with the candidate's envelope thresholds), as the
    class records lane_lra uses."""
    ev = L_lra['envelopes']
    recs = r1in.get('lra_supplied', [])
    v = validate_lra_supplied(cx, recs, (ev['continuous_upper_bound']['value_mm'], ev['authored_grid_maximum']['value_mm'],
                                         ev['selected_design_point']['value_mm']))
    acc = [r for r, x in zip(recs, v) if x['accepted']]
    return [dict(c, supplied=False) for c in cx.st.I['lra_classes']] + \
        [dict(id=r['id'], shape=r['shape'], height_mm=r['height_mm'], lead_exit_envelope_mm=r['lead_exit_envelope_mm'], supplied=True,
              **{f: r[f] for f in cx.I['lra_supplied_schema']['dimension_fields'][r['shape']]}) for r in acc]


def lra_phys_of(cls, p, env):
    """(body, lead) circles of a joint-search pose as lane_lra tests them in plan."""
    if cls.get('supplied'):
        return env[:len(env) - len(p['lead'])], list(p['lead'])
    return env, []


def chg_for_rlim(cx, cand, poses, r_lim):
    cache = cx.__dict__.setdefault('chg_rlim_cache', {})
    key = (cand['id'], round(r_lim, 9), id(poses))
    if key not in cache:
        cache[key] = chg_select(cx, cand, poses, r_lim)
    return cache[key]


def struct_geometry(cx, cand, sctx, row, r_lim, poses=None, pose=None):
    """Structural geometry of one design point (seal r_lim, charger pose -> land interrupter and C1 split) and its
    Loewner-maximal relaxed model (cached on the R-independent geometry)."""
    if pose is None:
        pose = chg_for_rlim(cx, cand, poses, r_lim)['pose']
    split = c1_split(cx, cand, pose['land_rmin']) if cand['caseback'].get('split') else None
    r_split = split['selected']['r_split'] if split else None
    mats, _ = str_mats(cx, cand, r_split)
    geo = str_geo(cx, cand, row, r_lim, pose, r_split)
    cache = cx.__dict__.setdefault('relaxed_cache', {})
    key = (cand['id'], round(geo['r_rib_out'], 9), r_split,
           json.dumps([[i['id'], [round(x, 9) for x in i['az']], [round(x, 9) for x in i['r']]] for i in geo['interrupters']]))
    if key not in cache:
        cache[key] = relaxed_model(cx, cand, sctx, geo, mats)
    return dict(geo=geo, mats=mats, rel=cache[key], r_split=r_split, pose=pose)


def struct_point(cx, cand, sctx, row, r_lim, poses=None, pose=None):
    """R2-1: STRUCTURE at one exact design point (candidate, D, bulk wall, V03 arcs, seal r_lim, charger pose, rib
    interruptions, split radius). Every admissible configuration is covered: the compliance bound proves failure for all of
    them at once, otherwise the exact search decides. All plate radii reachable by admissible arc thicknesses are covered;
    a pass only at a non-selected arc thickness would contradict the V03 coupling reduction and STOPs."""
    if not sctx['geometry_ok']:
        return dict(method='GEOMETRY', pass_=False, R_mm=None, bound_mm=None, limit_mm=sctx['c_defl'], n_R=0, bound_min_mm=None,
                    reason='no admissible caseback thickness window (t_in: pod residual vs material floor; t_out: rear periphery vs floor)')
    sg = struct_geometry(cx, cand, sctx, row, r_lim, poses, pose)
    geo, mats, rel, r_split = sg['geo'], sg['mats'], sg['rel'], sg['r_split']
    chg = dict(pose=sg['pose'])
    evals = []
    for R in struct_R_values(cx, cand, row, geo):
        ratio = bound_ratio(cx, rel, R)
        if ratio >= sctx['c_defl'] - EPS:
            evals.append(dict(R=R, ratio=ratio, method='COMPLIANCE_BOUND', pass_=False))
        else:
            ex = struct_exact(cx, cand, sctx, geo, mats, R)
            evals.append(dict(R=R, ratio=ratio, method='EXACT_SEARCH', pass_=ex['pass_'], exact=ex))
    sel = evals[0]
    if not sel['pass_'] and any(e['pass_'] for e in evals[1:]):
        raise StudyError('STOP: structure passes only at a non-selected V03 arc thickness (%s D %.2f tw %.2f): coupling reduction violated'
                         % (cand['id'], row['D'], row['tw']))
    return dict(method=sel['method'], pass_=sel['pass_'], R_mm=sel['R'], bound_mm=sel['ratio'], limit_mm=sctx['c_defl'], n_R=len(evals),
                bound_min_mm=min(e['ratio'] for e in evals), exact=sel.get('exact'), r_split=r_split,
                charger_pose=[chg['pose']['orientation'], chg['pose']['r_centre'], chg['pose']['az_centre']])


# --------------------------------------------------------------------------------------------
# L-LRA (R2-3): five separately labelled envelopes; joint search over caseback material x authored plate thickness x
# pocket depth x class x pose x orientation x lead / exit envelope against the charger, ribs, supports, seal flange,
# CHG_ROUTE / G2 corridors, buttons and keep-outs; every combination receives the structural re-screen, whose result
# feeds LRA feasibility and the gate classification; 9.8 trigger.
# --------------------------------------------------------------------------------------------
def validate_lra_supplied(cx, records, thresholds=()):
    """C-R1-08: a supplied class counts only with complete evidence, including its lead / exit envelope (R2-3); a rejected
    record never suppresses the gate; a class whose height equals an R1 threshold is circular and rejected."""
    sch = cx.I['lra_supplied_schema']
    out = []
    for rec in records:
        prob = []
        for k in sch['required']:
            if rec.get(k) in (None, '', [], {}):
                prob.append('missing ' + k)
        shape = rec.get('shape')
        fields = sch['dimension_fields'].get(shape)
        if fields is None:
            prob.append('unknown shape')
            fields = []
        for f in fields + ['height_mm']:
            d = rec.get(f)
            if not isinstance(d, dict) or any(not isinstance(d.get(k), (int, float)) for k in sch['range_keys']):
                prob.append('incomplete min/nom/max ' + f)
            elif not d['min'] <= d['nom'] <= d['max']:
                prob.append('inconsistent range ' + f)
        le = rec.get('lead_exit_envelope_mm')
        if isinstance(le, dict):
            for f in sch['lead_exit_fields']:
                d = le.get(f)
                if not isinstance(d, dict) or any(not isinstance(d.get(k), (int, float)) for k in sch['range_keys']):
                    prob.append('incomplete min/nom/max lead_exit ' + f)
                elif not 0.0 <= d['min'] <= d['nom'] <= d['max']:
                    prob.append('inconsistent range lead_exit ' + f)
            if le.get('exit') not in sch['lead_exit_directions']:
                prob.append('lead / exit direction not in %s' % sch['lead_exit_directions'])
        doc = rec.get('primary_document')
        if isinstance(doc, str) and doc:
            p = (ROOT / doc).resolve()
            if not str(p).startswith(str(ROOT)) or not p.is_file():
                prob.append('primary document not a local file')
            if doc in R1_FILES or doc.startswith('design/mechanical/generated/') or 'g4_r1' in doc:
                prob.append('primary document is an R1 / generated file (threshold-defined class)')
        prov = rec.get('provenance') or {}
        if not isinstance(prov, dict) or any(not prov.get(k) for k in sch['provenance_keys']):
            prob.append('missing page / table-or-figure provenance')
        hmax = rec['height_mm'].get('max', -1) if isinstance(rec.get('height_mm'), dict) else None
        if hmax is not None and any(t is not None and abs(hmax - t) < 1e-6 for t in thresholds):
            prob.append('class height equals an R1 envelope threshold (C-R1-08 circular class)')
        out.append(dict(id=rec.get('id'), accepted=not prob, problems=prob))
    return out


LRA_EXIT_DIRS = {'radial_out': (1.0, 0.0), 'radial_in': (-1.0, 0.0), 'cw': (0.0, 1.0), 'ccw': (0.0, -1.0)}


def supplied_envelope(cls, p):
    """Physical plan envelope of a supplied class at a pose: the body (same construction as g4.pose_envelope) plus the
    lead / exit rectangle attached to the body edge in the declared exit direction (pose frame: radial / clockwise)."""
    c = g4.xy(p['r'], p['az'])
    t = math.radians(p['az'])
    er, et = (math.sin(t), -math.cos(t)), (math.cos(t), math.sin(t))
    if cls['shape'] == 'coin':
        body = [(c, cls['diameter_mm']['max'] / 2.0)]
        half = lambda d: cls['diameter_mm']['max'] / 2.0
    else:
        ang = p['az'] - 90.0 + (90.0 if p['ori'] == 0 else 0.0)
        L, W = cls['length_mm']['max'], cls['width_mm']['max']
        body = g4.rect_cover(c, L, W, ang)
        u = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        half = lambda d: abs(d[0] * u[0] + d[1] * u[1]) * L / 2.0 + abs(-d[0] * u[1] + d[1] * u[0]) * W / 2.0
    le = cls.get('lead_exit_envelope_mm')
    if not le:
        return body, []
    a, b = LRA_EXIT_DIRS[le['exit']]
    d = (a * er[0] + b * et[0], a * er[1] + b * et[1])
    Ll, Wl = le['length_mm']['max'], le['width_mm']['max']
    if Ll <= EPS or Wl <= EPS:
        return body, []     # a declared zero-size lead / exit adds no plan area
    h = half(d)
    lc = (c[0] + (h + Ll / 2.0) * d[0], c[1] + (h + Ll / 2.0) * d[1])
    dang = math.degrees(math.atan2(d[1], d[0]))
    lead = g4.rect_cover(lc, Ll, Wl, dang) if Ll >= Wl else g4.rect_cover(lc, Wl, Ll, dang + 90.0)
    return body, lead


def lra_class_height(cls):
    """Height of the physical envelope: body and (supplied) lead / exit."""
    le = cls.get('lead_exit_envelope_mm')
    return max(cls['height_mm']['max'], le['height_mm']['max'] if le else 0.0)


def lra_supplied_poses(cx, cls, r_lim):
    """The authored V22 pose grid (az 0-355 step 5, r 12-26 step 0.25, orientations) for a supplied class with its lead /
    exit included in every plan test (global G4 exclusions, S14 outline, outer limit)."""
    st = cx.st
    P = st.I['lra_search']
    c_plan = cx.poses['c_plan']
    oris = [None] if cls['shape'] == 'coin' else P['orientations_deg']
    out = []
    for az in range(0, P['az_stop_deg'] + 1, P['az_step_deg']):
        for r in frange(12.0, 26.0, P['r_step_mm']):
            for o in oris:
                p = dict(cls=cls['id'], az=az, r=r, ori=o)
                body, lead = supplied_envelope(cls, p)
                env = body + lead
                rmax = max(math.hypot(q[0] - 100.0, q[1] - 100.0) + rho for q, rho in env)
                rmin = min(math.hypot(q[0] - 100.0, q[1] - 100.0) - rho for q, rho in env)
                if rmax + c_plan > r_lim + EPS:
                    viol = ['OUTER_LIMIT']
                elif rmin < st.s14geo['outline_r'] + c_plan:
                    viol = ['S14_OUTLINE']
                else:
                    viol = g4.lra_pose_violations(st, env, cx.poses)
                count()
                out.append(dict(p, rmax=rmax, rmin=rmin, viol=viol, env=env, lead=lead,
                                u703=min(math.dist(q, st.u703) - rho for q, rho in env)))
    return out


def lra_materials_at(mats_fn, env):
    """Caseback material class(es) under a pocket footprint (C1: centre / outer by radius; a straddling pocket takes both)."""
    r0 = min(math.hypot(q[0] - 100.0, q[1] - 100.0) - rho for q, rho in env)
    r1 = max(math.hypot(q[0] - 100.0, q[1] - 100.0) + rho for q, rho in env)
    m0, m1 = mats_fn(max(r0, 1e-3)), mats_fn(r1)
    return [m0] if m0['id'] == m1['id'] else [m0, m1]


def lra_exclusion_set(cx, cand, dp_g4, chg_sel, strl):
    """Local LRA plan exclusions: the accepted G4 set (lra_local_exclusions: case-side supports, screws, switch bores /
    bosses, seal flange, pod frame, U7 lead exit) with the R1 charger block / land, every conductor record and the credited
    ribs of the selected structural configuration."""
    st = cx.st
    sp = cx.ce[cand['id']].sp
    ex = [(n, g) for n, g in g4.lra_local_exclusions(st, cx.ce[cand['id']], dp_g4) if n not in ('CHG_CONTACT_BLOCK', 'CHG_4X5_WITH_LAND')]
    vent = g4.vent_layout(st, sp, dp_g4, g4.button_layout(st, sp, dp_g4))
    if vent:
        ex.append(('VENT_PORT', g4.sector(vent['centre'] - vent['half'], vent['centre'] + vent['half'], dp_g4['D'] / 2.0 - dp_g4['tw'], dp_g4['D'] / 2.0)))
    pose = chg_sel['pose']
    ex.append(('CHG_CONTACT_BLOCK', dict(type='poly', pts=pose['block_poly'])))
    ex.append(('CHG_LAND', dict(type='poly', pts=pose['land_poly'])))
    for k in conductor_ids(st):
        ex.append((k, conductor(cx, k)['geom']))
    for a in (strl['rib_layout']['credited'] if strl['selected']['n'] > 0 else []):
        g = strl['geometry']
        hw = math.degrees(math.asin(min(1.0, (strl['selected']['w'] / 2.0) / g['r_rib_in'])))
        ex.append(('RIB_%05.1f' % a, g4.sector(a - hw, a + hw, g['r_rib_in'], g['r_rib_out'])))
    return ex


def lane_lra(cx, cand, row, dp_g4, r_lim, chg_sel, strl, sdp, sctx):
    st, zm, P = cx.st, cx.zm, cx.P['V22_lra_pocket']
    ce = cx.ce[cand['id']]
    sp = ce.sp
    r_split = (strl.get('split') or {}).get('selected', {}).get('r_split')
    mats_fn, mset = str_mats(cx, cand, r_split)
    mat = mset['outer']
    c_top, mount = st.P['c_lra_top_mm']['max'], st.P['lra_mount_mm']['max']
    alloc, tol_lw = zm['z_lower_web_underside_nom'], zm['tol_lower_web']
    depths = P['pocket_depths_mm']
    tout_grid = grid(cx.P['V12_caseback_thickness']['t_out'])

    def H_of(t_res, m):
        """LA-Z-2 ceiling over a pocket floor of nominal residual t_res (thickness tolerance on the pocket floor Z)."""
        return zm['z_band_lo_adv'] - c_top - mount - (t_res + m['tol_t'])

    def combos(ms, touts):
        floor = max(m['t_min'] + m['tol_t'] for m in ms)
        return [(t, d, round(t - d, 9)) for t in touts for d in depths if t - d >= floor - EPS]
    periphery_ok = {t: g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=t), 0.0), full=False) >= -EPS for t in tout_grid}
    count(len(tout_grid))
    # 1-3 per material class (owner information)
    table = {}
    for mid, proc in (('MAT-CERAMIC', 'PC-CERAMIC-GRIND'), ('MAT-NF-METAL', 'PC-METAL-MACH'), ('MAT-GF-POLY', 'PC-POLY-MOULD')):
        m = str_material(st, mid, proc)
        touts_m = [t for t in tout_grid if periphery_ok[t] and t - m['tol_t'] - m['t_min'] >= -EPS]
        cb = combos([m], touts_m)
        best = max(cb, key=lambda c: (H_of(c[2], m), -c[0], -c[1])) if cb else None
        table[mid] = dict(floor_mm=m['t_min'], tol_mm=m['tol_t'], residual_floor_mm=m['t_min'] + m['tol_t'],
                          continuous_upper_bound_mm=H_of(m['t_min'] + m['tol_t'], m),
                          authored_grid_maximum_mm=H_of(best[2], m) if best else None,
                          authored_grid_argmax=dict(t_out_mm=best[0], depth_mm=best[1], residual_mm=best[2]) if best else None,
                          continuous_without_band_mm=zm['z_lower_web_underside_adv'] - c_top - mount - (m['t_min'] + 2.0 * m['tol_t']),
                          lead_formula_without_band_mm=alloc - tol_lw - c_top - mount - (m['t_min'] + m['tol_t']),
                          historical_0p5_residual_without_band_mm=alloc - P['historical_residual_mm'] - m['tol_t'] - tol_lw - c_top - mount)
    t_out_sel = strl['selected']['t_out']
    adm_sel = [d for d in depths if t_out_sel - d >= mat['t_min'] + mat['tol_t'] - EPS]
    d_sel = max(adm_sel) if adm_sel else None
    env_sel = H_of(t_out_sel - d_sel, mat) if d_sel is not None else None
    cand_grid = table[mat['id']]
    # joint search
    supplied_v = validate_lra_supplied(cx, cx.I.get('lra_supplied', []),
                                       (cand_grid['continuous_upper_bound_mm'], cand_grid['authored_grid_maximum_mm'], env_sel))
    acc = [r for r, v in zip(cx.I.get('lra_supplied', []), supplied_v) if v['accepted']]
    classes = [dict(c, supplied=False) for c in st.I['lra_classes']] + \
              [dict(id=r['id'], shape=r['shape'], height_mm=r['height_mm'], lead_exit_envelope_mm=r['lead_exit_envelope_mm'], supplied=True,
                    **{f: r[f] for f in cx.I['lra_supplied_schema']['dimension_fields'][r['shape']]}) for r in acc]
    ex = lra_exclusion_set(cx, cand, dp_g4, chg_sel, strl)
    lctx = dict(classes=classes, ex=ex, dp_g4=dp_g4, r_lim=r_lim)
    c_plan = cx.poses['c_plan']
    srec = sdp['record']
    s_method = srec['method']
    rows, best_pose, struct_H = [], None, None
    n_combo = n_rescreen = 0
    for cls in classes:
        if cls['supplied']:
            cand_poses = lra_supplied_poses(cx, cls, r_lim)
        else:
            cand_poses = cx.poses['by_class'].get(cls['id'], [])
        h_need = lra_class_height(cls)
        plan = []
        for p in cand_poses:
            if p['viol'] or p['rmax'] + c_plan > r_lim + EPS:
                continue
            env = p['env'] if cls['supplied'] else g4.pose_envelope(st, p)
            count()
            if g4.local_pose_violations(st, ce, dp_g4, env, ex):
                continue
            plan.append((p, env))
        z_poses, fits, H_cls = 0, [], None
        for p, env in plan:
            ms = lra_materials_at(mats_fn, env)
            # the Z ceiling depends on the residual only: Z-only combinations (t_out, depth, residual)
            zcomb = combos(ms, sctx['t_out'])
            mt = max(ms, key=lambda m: m['tol_t'])
            Hs = [(H_of(c[2], mt), c) for c in zcomb]
            Hp = max((h for h, _ in Hs), default=None)
            if Hp is not None:
                H_cls = Hp if H_cls is None else max(H_cls, Hp)
            zc = {c for h, c in Hs if h_need <= h + EPS}
            z_poses += bool(zc)
            # R3-4 / R4-1: a structural joint-search combination is (t_in, t_out, depth, residual) of this pose / class / material
            cb = [(ti,) + c for ti in sctx['t_in'] for c in zcomb]
            n_combo += len(cb)
            for c in cb:      # every combination of this pose receives the structural re-screen
                n_rescreen += 1
                if s_method == 'EXACT_SEARCH' and c[1:] in zc:
                    body, lead = lra_phys_of(cls, p, env)
                    fb = lra_struct_fallback(cx, cand, sctx, strl, mats_fn, lra_claimed_identity(cx, cand, cls, p, c, mats_fn, strl['geometry'], lctx),
                                             dict(body=body, lead=lead), c, lctx)
                    ok = fb['pass_'] and fb['evaluated']['z_fit']['fits'] and not fb['evaluated']['plan_fit']['violations']
                else:
                    fb, ok = None, False      # COMPLIANCE_BOUND / GEOMETRY: every pocketed variant fails (design-point relaxed model dominates it)
                if ok and c[1:] in zc:
                    fits.append(dict(az=p['az'], r=p['r'], ori=p['ori'], t_in=c[0], t_out=c[1], depth=c[2], residual=c[3], H=H_of(c[3], mt),
                                     combination=fb['combination'], evaluated=fb['evaluated'], structural=fb['structural'], pass_=fb['pass_'],
                                     sigma_B=fb['sigma_B'], w_B=fb['w_B']))
                    struct_H = H_of(c[3], mt) if struct_H is None else max(struct_H, H_of(c[3], mt))
        if plan:
            cb_best = max(plan, key=lambda e: (e[0]['u703'], -e[0]['az'], -e[0]['r']))
            if best_pose is None or cb_best[0]['u703'] > best_pose[0]['u703']:
                best_pose = cb_best
        rows.append(dict(id=cls['id'], shape=cls['shape'], supplied=cls['supplied'], height_min_mm=cls['height_mm']['min'],
                         height_max_mm=cls['height_mm']['max'], envelope_height_mm=h_need,
                         lead_exit=cls.get('lead_exit_envelope_mm'), poses_evaluated=len(cand_poses), plan_feasible_poses=len(plan),
                         plan_windows=sorted({p['az'] for p, _ in plan}),
                         H_before_structure_mm=H_cls, z_margin_before_structure_mm=(H_cls - h_need) if H_cls is not None else None,
                         z_feasible_poses=z_poses, structurally_feasible_fits=len(fits), fits=bool(fits), fit_examples=fits[:3]))
    fitting = [r['id'] for r in rows if r['fits']]
    authored_min = min(c['height_mm']['min'] for c in st.I['lra_classes'])
    trigger = not fitting
    struct_ok_any = srec['pass_']
    hdr = cx.g4_res['z']['rows']
    env = dict(
        historical_optimistic=dict(value_mm=table[mat['id']]['historical_0p5_residual_without_band_mm'], searched=False,
                                   label='historical optimistic bound: 0.5 mm residual, no LA-LRA-1 floor, no LA-Z-2 band; never a search result'),
        continuous_upper_bound=dict(value_mm=cand_grid['continuous_upper_bound_mm'], searched=False, material=mat['id'],
                                    label='continuous mathematical upper bound: residual exactly t_wall_min(max) + thickness tol (LA-LRA-1) '
                                          'under the LA-Z-2 band; not reachable on the authored grids; not a search result'),
        authored_grid_maximum=dict(value_mm=cand_grid['authored_grid_maximum_mm'], searched=True, material=mat['id'], argmax=cand_grid['authored_grid_argmax'],
                                   label='authored-grid maximum: V12 t_out x V22 pocket depth, residual >= LA-LRA-1 floor, LA-Z-2 band; Z only, '
                                         'BEFORE structural qualification'),
        selected_design_point=dict(value_mm=env_sel, searched=True, t_out_mm=t_out_sel, depth_mm=d_sel,
                                   residual_mm=(t_out_sel - d_sel) if d_sel is not None else None,
                                   label='selected structural plate (t_out %.2f) with its deepest admissible pocket; before structural qualification' % t_out_sel),
        structurally_feasible_searched=dict(value_mm=struct_H, searched=True, structural_method=s_method,
                                            label='maximum over the joint search of combinations that pass the structural re-screen; '
                                                  'null = no structurally feasible combination'))
    dz = {k: (authored_min - v['value_mm']) if v['value_mm'] is not None else None for k, v in env.items()}
    gates = (['OD-G4-LRA-ARCH', 'SR-LRA'] if trigger else ['SR-LRA']) + ([] if struct_ok_any else ['Q-R1-STRUCTURE'])
    return dict(lane='L-LRA', current_g2_allocation_kept=True, caseback_material=mat['id'],
                residual_floor_mm=mat['t_min'] + mat['tol_t'], residual_rule='LA-LRA-1: t_wall_min(max) + caseback thickness tolerance',
                envelopes=env, material_table=table, delta_Z_mm=dz, delta_Z_rule='authored minimum class height %.2f mm minus each labelled envelope' % authored_min,
                pocket=dict(t_out_mm=t_out_sel, admissible_depths_mm=adm_sel, depth_mm=d_sel,
                            residual_mm=(t_out_sel - d_sel) if d_sel is not None else t_out_sel,
                            residual_check_mm=((t_out_sel - d_sel) if d_sel is not None else t_out_sel) - mat['tol_t'] - mat['t_min']),
                band_rule='LA-Z-2 (accepted as conservative): the REAR conductor band (c_rear_route max) is deducted for every envelope except the '
                          'labelled historical / without-band columns',
                structural_rescreen=dict(method=s_method, combinations=n_rescreen, design_point_bound_mm=srec.get('bound_mm'),
                                         limit_mm=srec.get('limit_mm'), structurally_feasible_caseback=struct_ok_any,
                                         rule='every (class, pose, t_in, t_out, depth) combination is re-screened; a pocket only thins the plate '
                                              '(isotropic D below the relaxed model) and its interrupter only enlarges rib gaps (D_r falls with spacing), '
                                              'so the design-point relaxed model dominates every pocketed variant and the compliance bound covers all; '
                                              'otherwise the exact pocketed search decides, bound to the credited physical combination (R4-1: '
                                              'only the rib configuration is free; the evaluated identity - plate, materials, pocket band / '
                                              'footprint / interrupter, r_lim, pose and class derived from the evaluated circles, body / lead / '
                                              'exit envelopes, Z fit incl. mount allowance, plan re-check, structural geometry and rib '
                                              'interrupters, charger, seal flange and plan exclusions - must equal the claimed identity; the '
                                              'validator reconstructs it independently)'),
                joint_search=dict(combinations=n_combo, classes=len(classes), exclusions=[n for n, _ in ex]),
                supplied=supplied_v, classes=rows, plan_feasible_classes=[r['id'] for r in rows if r['plan_feasible_poses']],
                fitting_classes=fitting, authored_min_height_mm=authored_min, od_g4_lra_arch_triggered=trigger,
                best_plan_pose=None if best_pose is None else dict(cls=best_pose[0]['cls'], az=best_pose[0]['az'], r=best_pose[0]['r'],
                                                                   ori=best_pose[0]['ori'], u703_mm=best_pose[0]['u703']),
                best_plan_env=None if best_pose is None else best_pose[1],
                t_total_headroom_nominal_mm={k: v['headroom_nominal'] for k, v in sorted(hdr.items())},
                option_set=['supplier evidence (C-R1-08, lead / exit included) of a class with envelope height <= %.3f mm (authored-grid maximum, '
                            '%s, before structural qualification; continuous upper bound %.3f mm) and a footprint fitting a reported pose window, '
                            'together with a structurally feasible caseback (Q-R1-STRUCTURE)'
                            % (cand_grid['authored_grid_maximum_mm'], mat['id'], cand_grid['continuous_upper_bound_mm']),
                            'G2 REAR-band reallocation study (any REAR-driven growth needs OD-G4-STACK; T_total headroom %s)' %
                            ' / '.join('%.3f' % v['headroom_nominal'] for _, v in sorted(hdr.items())),
                            'haptic-free Rev-A'],
                decided=False, physical_pass=bool(fitting),
                disposition='ARCHITECTURE_GATED' if trigger else 'SUPPLIER_GATED', gates=gates)


# --------------------------------------------------------------------------------------------
# L-ASM: accepted G4 A1..A11 identities (LA-ASM-1), C-R1-06, geometric executability
# --------------------------------------------------------------------------------------------
def asm_sequence(cx, btn):
    steps = copy.deepcopy(cx.st.I['assembly']['steps'])
    for s in steps:
        if s['id'] == 'A9':
            sel = btn['selected_topology'] if btn['closed'] else None
            if sel:
                s['op'] = 'Button plungers and elastomer boots (%s) inserted radially from outside and retained' % \
                          ', '.join('%s %s' % (k, v) for k, v in sorted(sel.items()))
                s['r1_part_content'] = sel
            else:
                s['r1_part_content'] = 'GATED by L-BTN (R1-S03): no selectable button topology'
    return steps


def asm_identity(cx, steps):
    """LA-ASM-1: ids, order, part, direction and battery state equal the accepted G4 A1..A11 records; only A9's op /
    part content may follow the selected button topology."""
    ref = cx.st.I['assembly']['steps']
    probs = []
    if [s['id'] for s in steps] != [s['id'] for s in ref]:
        probs.append('operation ids / order differ from accepted A1..A11')
    for a, b in zip(steps, ref):
        for k in ('part', 'direction', 'battery_state'):
            if a.get(k) != b.get(k):
                probs.append('%s %s changed' % (a['id'], k))
        if a['id'] != 'A9' and a.get('op') != b.get('op'):
            probs.append('%s op changed' % a['id'])
    return dict(pass_=not probs, problems=probs)


def asm_dependencies(btn, lra, deps):
    """R2-5: product-closure dependencies of the accepted A1..A11 operations on other lanes' physical results at the same
    design point. A dependency is RESOLVED (physical pass), GATED (architecture / reviewer / supplier gate, not a physical
    failure) or FAILED (the required part does not physically exist at this point)."""
    seal, chg, strl, win = deps['seal'], deps['chg'], deps['strl'], deps['win']
    out = []

    def add(step, need, ok, state_if_not, gate, evidence):
        out.append(dict(step=step, requires=need, state='RESOLVED' if ok else state_if_not, gate=None if ok else gate, evidence=evidence))
    add('A1', 'W1 window bonded into the caseback pod frame (L-WIN)', win['physical_pass'], 'FAILED', 'R1-S01',
        dict(window_physical_pass=win['physical_pass']))
    add('A1', 'structurally feasible caseback sub-assembly (L-STR, R1-H09)', strl['physical_pass'], 'FAILED', 'Q-R1-STRUCTURE (R1-S07 / R1-S05)',
        dict(screen_B_sigma_MPa=strl['screen_B']['sigma_governing_MPa'], screen_B_w_mm=strl['screen_B']['w_max_mm'], geometry_ok=strl['geometry_ok']))
    add('A5', 'LRA bonded into a feasible pocket pose (L-LRA)', lra['physical_pass'], 'GATED', 'OD-G4-LRA-ARCH (R1-S08)',
        dict(fitting_classes=lra['fitting_classes'], od_g4_lra_arch_triggered=lra['od_g4_lra_arch_triggered']))
    imax = btn['disposition'].startswith('RESOLVED_UNDER_I-MAX_ONLY')
    add('A9', 'selectable button topology per switch (L-BTN)', btn['closed'], 'GATED' if imax else 'FAILED',
        'C-R1-03 adjudication (R1-S13)' if imax else 'Q-R1-BUTTON-ENVELOPE (R1-S03)', dict(disposition=btn['disposition']))
    add('A10', 'functional test through a feasible charger contact block (L-CHG, complete C-R1-01 closure)', chg['pass_'], 'FAILED', 'Q-R1-CHARGER (R1-S04)',
        dict(charger_pass=chg['pass_'], r_lim_mm=chg['r_lim']))
    add('A11', 'caseback closed with a feasible S-CB-MAIN seal (L-SEAL)', seal['physical_pass'], 'FAILED', 'Q-R1-MAIN-SEAL (R1-S06)',
        dict(feasible_topologies=seal['feasible_topologies'], closed_topology=seal['closed_topology'],
             coupled_population=seal['coupled']['population']))
    add('A11', 'S-CHG bonded feedthrough of a feasible charger (L-CHG)', chg['pass_'], 'FAILED', 'Q-R1-CHARGER (R1-S04)',
        dict(charger_pass=chg['pass_']))
    add('A11', 'structurally feasible caseback closing the pressure boundary (L-STR, R1-H09)', strl['physical_pass'], 'FAILED',
        'Q-R1-STRUCTURE (R1-S07 / R1-S05)', dict(physical_pass=strl['physical_pass']))
    return out


def lane_asm(cx, cand, row, btn, lra, closure_rows, steps=None, deps=None):
    st = cx.st
    steps = steps if steps is not None else asm_sequence(cx, btn)
    ident = asm_identity(cx, steps)
    order = g4.assembly_check(st, order=[s['id'] for s in steps], lra_feasible=lra['physical_pass'])
    count(len(steps))
    a9 = {sw: r['best'][btn['binding_interpretation']] for sw, r in btn['switches'].items()}
    a9_geom = all(s['predicates']['a9_radial_insertion_from_outside'] and s['margins']['no_inward_lip'] >= -EPS for s in a9.values())
    ins_ok = all(v >= -EPS for v in row['insertion'].values())
    clos_ok = all(r['clear'] for r in closure_rows)
    j1 = st.I['assembly']['j1_cycles']
    dep = asm_dependencies(btn, lra, deps) if deps is not None else []
    rows = []
    for r in order['rows']:
        mine = [d for d in dep if d['step'] == r['id'] and d['state'] != 'RESOLVED']
        gate = '; '.join('%s %s' % (d['state'], d['gate']) for d in mine) or None
        rows.append(dict(r, gate=gate, dependency_states=[d['state'] for d in dep if d['step'] == r['id']]))
    sequence_ok = ident['pass_'] and order['pass_'] and ins_ok and a9_geom and clos_ok
    failed = [d for d in dep if d['state'] == 'FAILED']
    gated = [d for d in dep if d['state'] == 'GATED']
    product = sequence_ok and not failed and not gated
    if not sequence_ok or failed:
        disp = 'OWNER_GATED'
    elif any(d['gate'].startswith('OD-G4-LRA-ARCH') for d in gated) and len(gated) == 1:
        disp = 'ARCHITECTURE_GATED'
    elif gated:
        disp = 'OWNER_GATED'
    else:
        disp = 'SUPPLIER_GATED'
    gates = ['SERVICE-COVER-REBOND'] + sorted({'%s:%s' % (d['step'], d['gate']) for d in failed + gated})
    return dict(lane='L-ASM', clarification='C-R1-06 / OD-G4-ASSEMBLY: A7 display seated from the open front precedes A8 cover bond',
                sequence=steps, identity=ident, order_check=rows, battery_isolation_ok=all(r['isolation_ok'] for r in order['rows']),
                insertion=row['insertion'], a9_geometry=dict(pass_=a9_geom, sections={k: dict(topology=v['topology'], profile=v['a9_profile'],
                                                                                            no_inward_lip=v['margins']['no_inward_lip']) for k, v in a9.items()}),
                caseback_closure=dict(pass_=clos_ok, rows=closure_rows),
                j1_cycles=dict(rated=j1['rated'], planned=j1['planned'], per_service=2, services_within_plan=(j1['planned'] - 1) // 2),
                service='SERVICE-COVER-REBOND remains OPEN: display replacement requires cover removal and re-bond',
                dependencies=dep, failed_dependencies=['%s: %s' % (d['step'], d['requires']) for d in failed],
                gated_dependencies=['%s: %s' % (d['step'], d['requires']) for d in gated],
                gated_operations=sorted({d['step'] for d in failed + gated}),
                sequence_executable=sequence_ok, executable=sequence_ok, product_closure_executable=product,
                physical_pass=sequence_ok, disposition=disp, gates=gates,
                rule='The operation sequence (identity, order, access directions, battery isolation, insertion, A9 geometry, caseback '
                     'closure clearances) is evaluated on its own geometry; the complete product closes only when every A-step dependency '
                     'is RESOLVED. A physically FAILED dependency makes L-ASM OWNER_GATED (the named owner question of that lane); it is '
                     'never reported as an executable product.')


def study_with_land(st, w):
    """Read-only Study view whose charger feedthrough land planning range is the single width w (the accepted inputs and every
    other parameter object are shared, never mutated)."""
    s2 = copy.copy(st)
    s2.P = dict(st.P)
    s2.P['bond_lands'] = dict(st.P['bond_lands'], charger_feedthrough_land_mm=dict(min=w, nom=w, max=w))
    return s2


def strict_wedge(cx, cand, chg_r_out):
    """C-R1-01 item 4 diagnostic: largest land width with the whole land inside the wedge (exact g4.charger_fit wedge geometry,
    orientation 0, land bisected on [0, 1] mm)."""
    sp = cx.ce[cand['id']].sp

    def margin(w):
        count()
        return g4.charger_fit(study_with_land(cx.st, w), sp, dict(chg_r_out=chg_r_out), orientation=0)['best']['margin_mm']
    lo, hi = 0.0, 1.0
    if margin(lo) < 0:
        return None
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if margin(mid) >= 0:
            lo = mid
        else:
            hi = mid
    return lo


def strict_wedge_path(cx, cand, r_lim):
    """R3-2 strict-wedge supplier path at one caseback radial limit: chg_r_out = min(CHG_CONTACT outer radius, r_lim -
    c_chg_window); the strict-wedge zero-margin land width w (strict_wedge) and its unique zero-margin pose - orientation 0,
    azimuth 90, centre at the admissible centre interval of g4.charger_fit at width w (the interval collapses at zero margin) -
    built with the production chg_pose (block inside the wedge, land inside the wedge: side overshoot <= 0, outer corners at
    chg_r_out - position tolerance). w is a SUPPLIER zero-margin threshold only (SR-CHG-MECH, land < w strictly once touching is
    a collision): never a credit and never the authored land (adverse 1.0 mm); the pose is judged against the complete same-point
    neighbour set by chg_point_eval exactly like every other pose."""
    st = cx.st
    sp = cx.ce[cand['id']].sp
    chg_r_out = min(st.res['CHG_CONTACT']['geometry']['r'][1], r_lim - st.P['c_chg_window_mm']['max'])
    cache = cx.__dict__.setdefault('strict_path_cache', {})
    key = (cand['id'], round(chg_r_out, 9))
    if key in cache:
        return cache[key]
    land_min = st.P['bond_lands']['charger_feedthrough_land_mm']['min']
    w = strict_wedge(cx, cand, chg_r_out)
    out = dict(chg_r_out_mm=chg_r_out, width_mm=w, land_min_mm=land_min, land_adverse_mm=cx.P['V20_charger_land']['adverse_mm'],
               pose=None, contained=False, centre_interval_mm=None)
    if w is not None:
        fit = g4.charger_fit(study_with_land(st, w), sp, dict(chg_r_out=chg_r_out), orientation=0)['best']
        lo, hi = fit['centre_interval_mm']
        p = chg_pose(cx, cand, 0, (lo + hi) / 2.0, 90.0, w)
        out.update(pose=p, centre_interval_mm=[lo, hi],
                   contained=p['land_side_overshoot_mm'] <= EPS and p['margins']['block_in_wedge'] >= -EPS
                   and p['land_rmax'] <= chg_r_out - p['position_tol'] + 1e-9)
    cache[key] = out
    return out


# --------------------------------------------------------------------------------------------
# Stage 1 / 2: D sweep with lane decomposition; stage 3: intersection, D-dependence, D_min
# --------------------------------------------------------------------------------------------
TW_GROUPS = ('H05-GEOM', 'INSERTION', 'MAIN-SEAL', 'CHARGER', 'STRUCTURE')
D_GROUPS = ('H03-OD', 'COVER', 'BUTTONS')
ALL_GROUPS = ('H03-OD', 'H05-GEOM', 'INSERTION', 'COVER', 'BUTTONS', 'MAIN-SEAL', 'CHARGER', 'STRUCTURE')


def cover_group(cx, cand, D):
    """H06-H09 regression: X25 cover fit at the best permitted a_cover (G4 cover_ok set: ledge + plate), U4 land
    headroom and switch-body ceiling at the G4 land choice. The land group's edge-Z crossing terms are H05 terms
    (XF / XB / XC in H05-GEOM, XL in H05-LRA-COUPLED) and are not counted twice here."""
    ce = cx.ce[cand['id']]
    fits = [(ce.f['cfit'](D=D, a_cover=a), -a) for a in ce.cover_ok]
    count(len(fits))
    best = max(fits) if fits else (-99.0, None)
    lm = ce.land['margins']
    reg = dict(cover_fit=best[0], u4=lm['u4'], btn_h=lm['btn_h'])
    return dict(a_cover=-best[1] if best[1] is not None else None, cover_fit_mm=best[0], land=ce.land, margins=reg,
                pass_=all(v >= -EPS for v in reg.values()) and ce.land['permitted'])


def btn_pass(cx, cand, D, Ts):
    """Pruned per-D button pass under the binding interpretation (pruning equality is tested at the design point)."""
    interp = 'I-MAX' if cx.I.get('c_r1_03_adjudication') == 'MAX' else 'I-SUM'
    ok = True
    worst = None
    for T in Ts:
        s = max((btn_best(cx, T, D, t, interp, False) for t in ('T2-R', 'T2-F')), key=lambda s: (s['pass_'], s['min_margin'], s['strain_margin']))
        ok = ok and s['pass_']
        worst = s['min_margin'] if worst is None else min(worst, s['min_margin'])
    return ok, worst


def sweep_candidate(cx, cand):
    """Stage 1/2 over D x bulk wall: every lane group is evaluated at the SAME design point (D, tw, V03 arcs, seal r_lim,
    charger pose, rib interruptions); STRUCTURE is the per-point struct_point result (R2-1), never an endpoint OR."""
    ce = cx.ce[cand['id']]
    carrier = solve_carrier(cx, ce)
    arcs = arc_defs(cx, cand)
    V = cx.P['V01_D_case_body']
    d_main = frange(V['start'], V['stop'], V['step'])
    d_ext = frange(V['stop'] + V['step'], V['report_stop'], V['step'])
    poses = chg_poses(cx, cand, cx.P['V20_charger_land']['adverse_mm'])
    pctx = chg_pose_ctx(poses)
    rkey = lambda p: (p['r_lim_required'], -p['orientation'], abs(p['az_centre'] - 90.0), p['r_centre'])
    pre_p = [p for p in poses if p['prereq_pass']]
    req_pose = min(pre_p, key=rkey) if pre_p else None
    chg_req = req_pose['r_lim_required'] if req_pose else None
    rad_pose = pctx['rad'][0] if pctx['rad'] else None
    t_top = chg_land_top(cx, cand)
    sctx = struct_context(cx, cand)
    Ts = [btn_terms(cx, cand, sw) for sw in sorted(cx.st.P['buttons']['windows_deg'])]
    rows = []
    pt = dict(sctx=sctx, poses=poses, pctx=pctx, t_top=t_top, chg_req=chg_req)
    for D in d_main + d_ext:
        best, allrows = rad_tw(cx, cand, D, carrier, arcs)
        cov = cover_group(cx, cand, D)
        bok, bmin = btn_pass(cx, cand, D, Ts)
        tws = [sweep_point(cx, cand, pt, D, r) for r in allrows]
        dg = {'H03-OD': best['od_pass'], 'COVER': cov['pass_'], 'BUTTONS': bok}
        rows.append(dict(D=D, primary=D <= V['ceiling_mm'] + EPS, tw_rows=tws, d_groups=dg, best_tw=best['tw'], od_margin=best['margins']['H03-OD'],
                         cover=cov['cover_fit_mm'], button_min=bmin,
                         any_tw={g: any(t['groups'][g] for t in tws) for g in TW_GROUPS}))
    return dict(carrier=carrier, arcs=arcs, poses=poses, pose_ctx=pctx, chg_r_lim_required=chg_req, chg_required_pose=req_pose,
                chg_r_lim_required_radial=rad_pose['r_lim_required'] if rad_pose else None, chg_radial_pose=rad_pose, chg_land_top=t_top,
                rows=rows, d_main=d_main, d_ext=d_ext, sctx=sctx)


def seal_typed_column(ms):
    """Sweep seal column (R5): per topology, per units group, the minimum over the topology's typed predicates of its population
    reduction (max over the term population of that predicate's margin) - never across units, never a representative row."""
    return {t: typed_minima({k: d['value'] for k, d in o['term_reductions'].items()}) for t, o in ms['topologies'].items()}


def sweep_point(cx, cand, pt, D, r):
    """One (D, bulk wall) point of the sweep: every lane group at the SAME point (V03 arcs, the coupled seal r_lim and flange envelope
    of the seal row population, charger pose set, rib interruptions); STRUCTURE is the per-point struct_point result (R2-1)."""
    ms = main_seal(cx, cand, r)
    r_lim = seal_r_lim(ms)
    sp_ = struct_point(cx, cand, pt['sctx'], r, r_lim, pt['poses'])
    # R3-1: the charger of THIS point against the complete neighbour set of THIS point; CHARGER = literal closure only
    ft = flange_top(cx, cand, ms)
    ch = chg_point_eval(cx, pt['pctx'], r_lim, pt['t_top'], chg_neighbours_at(cx, cand, D, r['tw'], r, ft), strict_wedge_path(cx, cand, r_lim))
    g = {'H05-GEOM': r['h05_geom_pass'], 'INSERTION': r['insertion_pass'], 'MAIN-SEAL': ms['physical_pass'],
         'CHARGER': ch['literal'], 'STRUCTURE': sp_['pass_']}
    chg_req = pt['chg_req']
    return dict(tw=r['tw'], groups=g, geom_min=r['h05_geom_min'], ins_min=min(r['insertion'].values()),
                seal_typed=seal_typed_column(ms), seal_feasible=ms['feasible_topologies'], seal_topology_for_r_lim=ms['coupled']['topology'],
                seal_r_lim_fallback=not ms['coupled']['closed'], seal_flange_top=ft, r_lim=r_lim,
                charger_plan_prereq_r_lim_margin=(r_lim - chg_req) if chg_req is not None else None,
                charger=chg_sweep_flags(ch), charger_strict_width=ch['strict_wedge']['width_mm'],
                structure=dict((k, sp_[k]) for k in ('method', 'pass_', 'R_mm', 'bound_mm', 'limit_mm', 'n_R', 'bound_min_mm')),
                arcs_t={a['reservation']: [a['t_arc_mm'], 'T' if a['z_extent'] == 'THROUGH_REAR_FACE' else 'M', a['search']['feasible']]
                        for a in r['arcs']},
                lra_lateral=min(r['lra_coupled']['H05-STRAIGHT@U7-RISER'], r['lra_coupled']['H05-EDGE-XL-LRA']))


def coupled_first_D(sw, groups, d_groups=(), primary_only=False):
    """First grid D (primary or extension) at which every named TW group passes at ONE common bulk wall and every named
    D group passes (same-point intersection)."""
    for r in sw['rows']:
        if primary_only and not r['primary']:
            continue
        if not all(r['d_groups'][g] for g in d_groups):
            continue
        if any(all(t['groups'][g] for g in groups) for t in r['tw_rows']):
            return r['D']
    return None


def charger_first_D(sw):
    """R3-8: first grid D (primary or report-only extension) per charger category at ONE (D, bulk wall) point, alone and coupled
    with the radial core (H05-GEOM + insertion) and the main seal. A prerequisite pass is never a charger closure; only
    'literal' (the complete C-R1-01 predicate against the complete same-point neighbour set) closes the charger."""
    def first(pred, d_pred=None):
        for r in sw['rows']:
            if d_pred is not None and not d_pred(r):
                continue
            if any(pred(t) for t in r['tw_rows']):
                return r['D']
        return None
    core = lambda t: t['groups']['H05-GEOM'] and t['groups']['INSERTION']
    out = {('first_' + k): first(lambda t, k=k: t['charger'][k]) for k in CHG_SWEEP_FLAGS}
    for k in ('radial', 'plan', 'literal', 'sw_plan', 'sw_complete') + CHG_DIAGNOSTIC_FLAGS:
        out['first_%s_with_radial_core' % k] = first(lambda t, k=k: t['charger'][k] and core(t))
        out['first_%s_with_radial_core_and_main_seal' % k] = first(lambda t, k=k: t['charger'][k] and core(t) and t['groups']['MAIN-SEAL'])
    out['first_plan_with_radial_core_and_od'] = first(lambda t: t['charger']['plan'] and core(t), lambda r: r['d_groups']['H03-OD'])
    out['first_literal_v_z_waived_with_radial_core_and_od'] = first(lambda t: t['charger']['literal_v_z_waived'] and core(t),
                                                                    lambda r: r['d_groups']['H03-OD'])
    out['rule'] = ('radial: C-R1-01 item 1 radial bounds (block) and the land radial bounds incl. the seal-flange limit; plan: + every plan '
                   'bound and plan clearance from the 2(v) items; z: the LAND\'s contract Z bounds (caseback side, strict Z separation from '
                   'CHG_ROUTE / CHG_LINK / screws / supports, C-R1-01 2(v)); neighbours: complete same-point neighbour set (land under its '
                   'contract rule, block under the strict 3-D clearance); literal: one pose meeting all (charger closure). sw_*: strict-wedge '
                   'supplier path at its zero-margin land width (in_land_range: width >= the authored land minimum, land and block inside the '
                   'wedge, radial at the point), 2(v) applied to its land (R1 reading pending Q-R1-CHARGER (b)). *_v_z_waived: DIAGNOSTIC ONLY - '
                   'the same predicate with only the conjunctive Z part of 2(v) waived for a plan-disjoint land (consequence quantification for '
                   'Q-R1-CHARGER, never a closure, never credited; C-R1-01 is not amended). null = none through %.2f mm.' % sw['rows'][-1]['D'])
    return out


def classify(cx, cand, sw):
    """Group states and diameters from the per-point results only (R2-1: no group is overwritten or flattened)."""
    rows = sw['rows']
    state = {}
    for g in ALL_GROUPS:
        vals = [(r['any_tw'][g] if g in TW_GROUPS else r['d_groups'][g]) for r in rows]
        first = next((r['D'] for r, v in zip(rows, vals) if v), None)
        last = max((r['D'] for r, v in zip(rows, vals) if v), default=None)
        state[g] = dict(d_dependent=len(set(vals)) > 1, first_pass_D=first, last_pass_D=last, always=all(vals), never=not any(vals))
    dep = [g for g in ALL_GROUPS if state[g]['d_dependent']]
    indep_fail = [g for g in ALL_GROUPS if state[g]['never']]

    def ok_at(r, groups):
        if not all(r['d_groups'][g] for g in groups if g not in TW_GROUPS):
            return None
        tw_need = [g for g in groups if g in TW_GROUPS]
        good = [t for t in r['tw_rows'] if all(t['groups'][g] for g in tw_need)]
        return good or None
    d_min = next((r['D'] for r in rows if r['primary'] and ok_at(r, dep)), None)
    d_min_ext = next((r['D'] for r in rows if ok_at(r, dep)), None)
    d_complete = next((r['D'] for r in rows if r['primary'] and ok_at(r, ALL_GROUPS)), None)
    core = ('H03-OD', 'H05-GEOM', 'INSERTION')
    d_core = next((r['D'] for r in rows if r['primary'] and ok_at(r, core)), None)
    # per-D structural feasibility (R2-1 report): same-point results over every bulk wall at that D
    by_d = []
    for r in rows:
        st_ = [t['structure'] for t in r['tw_rows']]
        by_d.append(dict(D=r['D'], primary=r['primary'], pass_any_tw=any(s['pass_'] for s in st_),
                         methods=sorted({s['method'] for s in st_}), walls_passing=[t['tw'] for t in r['tw_rows'] if t['structure']['pass_']],
                         bound_min_mm=min([s['bound_min_mm'] for s in st_ if s['bound_mm'] is not None], default=None),
                         limit_mm=st_[0]['limit_mm'], points=len(st_), R_values=sum(s['n_R'] for s in st_)))
    # first main-seal closure with the topology that closes there (labelled)
    ms_first = None
    for r in rows:
        tt = [t for t in r['tw_rows'] if t['groups']['MAIN-SEAL']]
        if tt:
            ms_first = dict(D=r['D'], tw=tt[0]['tw'], topologies=tt[0]['seal_feasible'],
                            label=' / '.join('%s%s' % (x, ' (non-serviceable)' if x == 'adhesive' else '') for x in tt[0]['seal_feasible']))
            break
    coupled = dict(
        charger_with_radial_core=coupled_first_D(sw, ('CHARGER', 'H05-GEOM', 'INSERTION')),
        charger_with_radial_core_and_main_seal=coupled_first_D(sw, ('CHARGER', 'H05-GEOM', 'INSERTION', 'MAIN-SEAL')),
        charger_with_radial_core_and_od=coupled_first_D(sw, ('CHARGER', 'H05-GEOM', 'INSERTION'), ('H03-OD',)),
        charger_with_od=coupled_first_D(sw, ('CHARGER',), ('H03-OD',)),
        charger_with_main_seal=coupled_first_D(sw, ('CHARGER', 'MAIN-SEAL')),
        main_seal_with_radial_core=coupled_first_D(sw, ('MAIN-SEAL', 'H05-GEOM', 'INSERTION')),
        rule='first grid D (primary or report-only extension to %.2f mm) with the named groups passing at one common bulk wall; '
             'CHARGER is the complete literal C-R1-01 closure of that point (R3-1); null = none on the grid' % sw['rows'][-1]['D'])
    chg_first = charger_first_D(sw)
    return dict(groups=state, d_dependent=dep, d_independent_failures=indep_fail, D_min=d_min, D_min_including_extension=d_min_ext,
                D_complete=d_complete, D_radial_core=d_core, structure_by_D=by_d, main_seal_first=ms_first, coupled_first_D=coupled,
                charger_first_D=chg_first,
                rule='D_min = first primary-grid D at which every D-dependent non-LRA group passes at one common bulk wall; '
                     'D-independent failures are listed separately; D_complete additionally requires every group. Every group, '
                     'STRUCTURE included, is the result of that exact (D, bulk wall, V03 arcs, seal r_lim, charger pose) point. '
                     'D_radial_core (H03-OD, H05-GEOM, insertion) is a radial-core statement only, never whole-design compliance.')


def design_choice(cx, sw, cls):
    rows = {r['D']: r for r in sw['rows']}
    if cls['D_complete'] is not None:
        d, rule = cls['D_complete'], 'D_complete'
    elif cls['D_min'] is not None:
        d, rule = cls['D_min'], 'D_min (D-dependent closure; D-independent failures remain)'
    else:
        ok = [r['D'] for r in sw['rows'] if r['primary'] and r['d_groups']['H03-OD']]
        d, rule = (max(ok) if ok else sw['d_main'][-1]), 'largest primary-grid D passing H03-OD (diagnostic, no D-dependent closure <= 51.00)'
    r = rows[d]
    key = lambda t: (sum(t['groups'].values()), t['groups']['H05-GEOM'] and t['groups']['INSERTION'], t['lra_lateral'] >= -EPS, t['tw'])
    t = max(r['tw_rows'], key=key)
    return d, t['tw'], rule


# --------------------------------------------------------------------------------------------
# Common feature set (S5): G4 production features + R1 features with explicit Z; one set for RF/MAG, S14,
# assembly, forbidden-load and SVG use
# --------------------------------------------------------------------------------------------
LEVEL_ORDER = ('window', 'optics_zone', 'rear_pcb', 'rear_inner', 'lower_web', 'battery_zone', 'back_zone', 'main_pcb',
               'front_gap', 'display', 'cover_bond', 'cover')


def level_z(st):
    lay = st.z['G2-REVA']['layers']
    z, cum = 0.0, {}
    for k in LEVEL_ORDER:
        cum[k] = (z, z + lay[k])
        z += lay[k]
    lv = {}
    for name, ks in st.I['levels'].items():
        if name == 'note':
            continue
        lv[name] = (min(cum[k][0] for k in ks), max(cum[k][1] for k in ks))
    lv['REAR'] = (0.0, cum['rear_inner'][1])
    return lv


def with_z(st, f):
    if 'z_lo_adv' in f:
        return f
    lv = level_z(st)
    zs = [lv[l] for l in f['z'] if l in lv]
    lo, hi = (min(a for a, _ in zs), max(b for _, b in zs)) if zs else (0.0, 0.0)
    g = dict(f)
    g.update(zfeat(lo, hi))
    g.setdefault('lane', 'G4')
    g.setdefault('material', 'conductive' if f.get('conductive') else 'non-conductive')
    return g


def build_features(cx, cand, dp_g4, btn, chg_sel, strl, seal, row):
    st, zm = cx.st, cx.zm
    sp = cx.ce[cand['id']].sp
    buttons = g4.button_layout(st, sp, dp_g4)
    vent = g4.vent_layout(st, sp, dp_g4, buttons)
    supports = g4.supports_layout(st, sp, dp_g4, buttons, vent)
    screws = g4.screw_layout(st, sp, dp_g4)
    lugs = g4.lug_layout(st, dp_g4)
    F0, diel = g4.features(st, sp, dp_g4, buttons, supports, screws, lugs, dp_g4['chg_r_out'])
    drop = ('charger contacts', 'charger aperture and land', 'pusher', 'button boss', 'caseback centre plate', 'new wiring')
    F = [with_z(st, f) for f in F0 if f['kind'] not in drop]
    # retained G4 wiring: the authoritative conductor records (R2-4), same objects as the module-side view
    F += [conductor(cx, f['id']) for f in F0 if f['kind'] == 'new wiring']
    for sw, r in sorted(btn['switches'].items()):
        F += [with_z(st, f) for f in r['materials']['features']]
    pose = chg_sel['pose']
    mat_cb = cand['caseback']['material']
    t_out = strl['selected']['t_out']
    tol_t = strl['materials']['outer']['tol_t']
    F.append(feature('CHG_BLOCK', 'L-CHG', 'contact block (SR-CHG-MECH)', True, False, dict(type='poly', pts=pose['block_poly']), ['REAR'],
                     zfeat(0.0, zm['z_band_lo_adv']), 'charger contacts'))
    F.append(feature('CHG_LAND', 'L-CHG', mat_cb + ' (non-conductive bond / seal land)', False, False, dict(type='poly', pts=pose['land_poly']),
                     ['REAR'], zfeat(0.0, t_out, 0.0, tol_t), 'charger land'))
    cfg, g = strl['selected'], strl['geometry']
    if cfg['n'] > 0 and strl['rib_layout']['gap_deg'] is not None:
        hw = math.degrees(math.asin(min(1.0, (cfg['w'] / 2.0) / g['r_rib_in'])))
        for a in strl['rib_layout']['credited']:
            rm = str_mats(cx, cand, (strl['split'] or {}).get('selected', {}).get('r_split'))[0](g['r_rib_in'])
            F.append(feature('RIB_%05.1f' % a, 'L-STR', rm['id'], rm['conductive'], rm['ferromagnetic'],
                             g4.sector(a - hw, a + hw, g['r_rib_in'], g['r_rib_out']), ['REAR'],
                             zfeat(t_out, t_out + cfg['h'], 0.0, 2 * tol_t), 'caseback rib'))
    # R5: the flange Z extent is the coupled population envelope (flange_top), never a representative row
    F.append(feature('CB_SEAL_FLANGE', 'L-SEAL', mat_cb, st.I['material_classes'][mat_cb]['conductive'], False,
                     g4.sector(0.0, 360.0, row['R_side'], dp_g4['D'] / 2.0), ['REAR'],
                     zfeat(0.0, flange_top(cx, cand, seal, t_out) - tol_t, 0.0, tol_t), 'caseback seal flange'))
    if cand['caseback'].get('split') and strl['split']:
        rs = strl['split']['selected']['r_split']
        F.append(feature('CASEBACK_CENTRE_PLATE', 'L-STR', cand['caseback']['centre_material'], True, False,
                         dict(type='circles', circles=[[100.0, 100.0, rs]]), ['REAR'], zfeat(0.0, t_out, 0.0, tol_t), 'caseback centre plate'))
    return dict(features=F, dielectric=diel, buttons=buttons, vent=vent, supports=supports, screws=screws, lugs=lugs)


CONDUCTOR_RESERVATIONS = ('CHG_ROUTE', 'CHG_LINK', 'FPC_UNDER')


def conductor(cx, rid):
    """R2-4: the ONE authoritative physical record of a conductor / wiring reservation. Its REAR portion occupies the LA-Z-2
    conductor band (z_band_lo_adv .. lower-web underside); any other level it spans adds that level's Z. Every view (the
    retained G4 'new wiring' entries of the feature set, the module-side clearance set, the charger route predicates) is this
    same object, so the conductor Z interval cannot differ between views."""
    cache = cx.__dict__.setdefault('conductor_cache', {})
    if rid not in cache:
        st, zm = cx.st, cx.zm
        src = st.g2res[rid] if rid in st.g2res else st.res[rid]
        levels = list(src['z_levels'])
        lv = level_z(st)
        lo = zm['z_band_lo_adv'] if 'REAR' in levels else min(lv[l][0] for l in levels if l in lv)
        hi = max(lv[l][1] for l in levels if l in lv)
        cache[rid] = feature(rid, 'G2' if rid in st.g2res else 'G1/G2 reservation', 'conductor', True, False, src['geometry'], levels,
                             zfeat(lo, hi), 'conductor', wiring=True,
                             z_rule='REAR portion in the LA-Z-2 band (z_band_lo_adv %.3f .. %.3f); single authoritative record' % (lo, hi))
    return cache[rid]


def conductor_ids(st):
    return list(CONDUCTOR_RESERVATIONS) + [k for k in sorted(st.g2res) if 'REAR' in st.g2res[k]['z_levels']]


def module_features(cx):
    """Module-side REAR features that caseback-side features must clear (frozen S14 / G2 / reservation geometry). The
    conductor entries are the authoritative conductor() records (R2-4), not copies."""
    st, zm = cx.st, cx.zm
    g = st.s14geo
    rear_skin = zfeat(zm['z_rear_skin_nom'] - st.P['c_cb_rear_mm']['min'], zm['z_lower_web_underside_nom'])
    out = [feature('S14_OUTLINE', 'G3', 'REAR module', True, False, dict(type='circles', circles=[[100.0, 100.0, g['outline_r']]]),
                   ['REAR'], rear_skin, 'S14 outline')]
    out += [feature('S14_SUPPORT_%d' % s['az'], 'G3', 'G3 support land', False, False, dict(type='poly', pts=s['poly']), ['REAR'],
                    rear_skin, 'G3 support land') for s in g['supports']]
    out += [conductor(cx, k) for k in conductor_ids(st)]
    return out


def feature_view_violations(F, mod):
    """R2-4: a feature id present in more than one view must be one physical record (identical geometry and Z interval)."""
    bad = []
    seen = {}
    for f in list(F) + list(mod):
        key = (json.dumps(f['geom'], sort_keys=True), f['z_lo_adv'], f['z_hi_adv'], tuple(f['z']))
        if f['id'] in seen and seen[f['id']] != key:
            bad.append('%s: inconsistent physical record across views (geometry / Z interval)' % f['id'])
        seen.setdefault(f['id'], key)
    return bad


def closure_rows(cx, F, mod):
    """A11 caseback closure (+Z from rear) and static caseback-feature clearances with the common clear() predicate."""
    cb = [f for f in F if f['kind'] in ('caseback rib', 'charger land', 'caseback seal flange')]
    rows = []
    for a in cb:
        targets = mod if a['kind'] == 'caseback seal flange' else mod + [f for f in F if f['kind'] == 'case-side support']
        for b in targets:
            if a['kind'] == 'caseback seal flange' and b['kind'] in ('S14 outline', 'G3 support land'):
                continue
            ok, info = clear(a, b, 0.0, 0.0)
            rows.append(dict(a=a['id'], b=b['id'], clear=ok, **info))
    return rows


def forbidden_loads(cx, cand, strl, F, mod, path):
    """Pressure must bypass battery, REAR PCB, G3 support lands and the carrier lower web: each branch load is derived
    from contact (feature clearance at adverse Z plus the plate deflection), never asserted."""
    zm = cx.zm
    fp = strl.get('forbidden_paths') or {}
    rear = fp.get('rear_pcb_and_g3_support_lands', dict(margin_mm=None, contact=True))
    bat = fp.get('battery_and_lower_web', dict(loaded_margin_mm=None, contact=False))
    w_rib = (strl.get('screen_B') or {}).get('w_rib_band_mm', 0.0)
    feat_hits = []
    for f in F:
        if f['kind'] not in ('caseback rib', 'charger land', 'caseback seal flange', 'caseback centre plate'):
            continue
        for b in mod:
            if b['kind'] not in ('G3 support land', 'S14 outline'):
                continue
            if g4.overlaps(f['geom'], b['geom']) and f['z_hi_adv'] + w_rib >= b['z_lo_adv'] - EPS:
                feat_hits.append(dict(feature=f['id'], target=b['id']))
        if f['kind'] == 'caseback rib' and f['z_hi_adv'] + w_rib > zm['z_lower_web_underside_adv'] + EPS:
            feat_hits.append(dict(feature=f['id'], target='LOWER_WEB'))
    rear_contact = bool(rear.get('contact')) or any(h['target'].startswith(('S14_', 'S14')) for h in feat_hits)
    g3_contact = bool(rear.get('contact')) or any(h['target'].startswith('S14_SUPPORT') for h in feat_hits)
    lw_contact = bool(bat.get('contact')) or any(h['target'] == 'LOWER_WEB' for h in feat_hits)
    branches = dict(
        BATTERY=dict(contact=lw_contact, load_N=None if lw_contact else 0.0, margin_mm=bat.get('loaded_margin_mm')),
        REAR_PCB=dict(contact=rear_contact, load_N=None if rear_contact else 0.0, margin_mm=rear.get('margin_mm')),
        G3_SUPPORT_LANDS=dict(contact=g3_contact, load_N=None if g3_contact else 0.0, margin_mm=rear.get('margin_mm')),
        CARRIER_LOWER_WEB=dict(contact=lw_contact, load_N=None if lw_contact else 0.0, margin_mm=bat.get('lower_web_clearance_mm')))
    return dict(branches=branches, feature_contacts=feat_hits, load_path_graph=path,
                all_zero=path['pass_'] and not any(b['contact'] for b in branches.values()),
                rule='load_N = 0.000 only when no contact closes (deflection < clearance and no feature overlap at adverse Z); '
                     'a closing contact makes the branch nonzero (magnitude statically indeterminate, not credited).')


def point_core(cx, cand, sw, D, tw, full, only_cfg=None):
    """Cheap lanes and structure at one design point (seal-coupled r_lim and charger pose)."""
    row = rad_point(cx, cand, D, tw, sw['carrier'], sw['arcs'])
    seal = main_seal(cx, cand, row)
    r_lim = seal_r_lim(seal)
    chg = chg_select(cx, cand, sw['poses'], r_lim)
    strl = lane_str(cx, cand, row, r_lim, chg['pose'], full, only_cfg)
    return dict(row=row, seal=seal, seal_topology=seal['coupled']['topology'], r_lim=r_lim, chg=chg, strl=strl)


def design_point_structure(cx, cand, sw, row, r_lim, pose, strl):
    """Design-point structural record: the per-point bound with the final charger pose, the production verification that
    the relaxed model dominates every admissible configuration model (Loewner order of the str_regions matrices), the
    exact search result (lane_str) and the observed boss location of the maximum deflection on every searched config."""
    sctx = sw['sctx']
    rec = struct_point(cx, cand, sctx, row, r_lim, pose=pose)
    out = dict(record=rec, loewner_violations=[], configs_checked=0)
    if sctx['geometry_ok']:
        sg = struct_geometry(cx, cand, sctx, row, r_lim, pose=pose)
        N = cx.P['screen_b']['subregions']
        lays = {}
        for cfg in sctx['configs']:
            if (cfg['n'], cfg['w']) not in lays:
                lays[(cfg['n'], cfg['w'])] = rib_layout(sg['geo'], cfg['n'], cfg['w'], cx.P['V13_rib_counts']['phase_divisions'])
            regs = str_regions(dict(sg['geo'], gap_deg=lays[(cfg['n'], cfg['w'])]['gap_deg']), sg['mats'], cfg, 'B', N)
            out['loewner_violations'] += loewner_violations(sg['rel'], regs, sg['geo']['R'])
            out['configs_checked'] += 1
        count(out['configs_checked'])
        if out['loewner_violations']:
            raise StudyError('STOP: relaxed structural model does not dominate a configuration: %s' % out['loewner_violations'][:2])
        out['relaxed_regions'] = len(sg['rel']['regions']) + 1
        out['relaxed_gaps_deg'] = sg['rel']['gaps']
    out['exact_search'] = dict(physical_pass=strl['physical_pass'], screen_B_sigma=strl['screen_B']['sigma_governing_MPa'],
                               screen_B_w=strl['screen_B']['w_max_mm'], configs=strl['configs_evaluated'],
                               w_max_at_boss_all_configs=strl.get('w_max_at_boss_all_configs'))
    out['consistent'] = not (rec['method'] == 'COMPLIANCE_BOUND' and strl['physical_pass'])
    if not out['consistent']:
        raise StudyError('STOP: compliance bound proves failure but the exact design-point search passes')
    return out


def dp_for_g4(cx, cand, D, tw, row, seal, chg, strl, btn):
    ce = cx.ce[cand['id']]
    cov = cover_group(cx, cand, D)
    cp = seal['coupled']
    r_lim = seal_r_lim(seal)
    cs_pop = sorted({r['cs_mm'] for r in seal_rows(seal, cp['population']) if r.get('cs_mm') is not None})
    bosses = {sw: (r['best']['I-SUM']['boss']) for sw, r in btn['switches'].items()}
    # R5: seal_cs is a single number only when the coupled population has exactly one cross-section; otherwise the population is
    # reported (no selected cs is created to preserve the G4 design-term schema; no G4 function used by R1 reads it)
    return dict(D=D, tw=tw, tcw=row['tcw'], rcin=row['rcin'], a_cover=cov['a_cover'] if cov['a_cover'] is not None else ce.dp0['a_cover'],
                t_land=ce.land['t_land'], w_land=ce.land['w_land'], t_w=cx.window['eligible_t_max'] or 0.5, h_pod=0.0,
                t_in=strl['selected']['t_in'], t_out=strl['selected']['t_out'], seal_topology=cp['topology'], seal_closed=cp['closed'],
                seal_cs=cs_pop[0] if len(cs_pop) == 1 else None, seal_cs_population_mm=cs_pop,
                r_lim=r_lim, chg_r_out=min(cx.st.res['CHG_CONTACT']['geometry']['r'][1], r_lim - cx.st.P['c_chg_window_mm']['max']),
                bosses=bosses, window_variant='W1')


CHG_NEIGHBOUR_KINDS = ('caseback screw', 'case-side support', 'support pad', 'lug arm', 'spring bar', 'button boss', 'button boot', 'pusher')


def chg_flange(cx, pose, r_lim):
    c = cx.st.P['c_chg_window_mm']['max']
    fb, fl = (r_lim - c) - pose['block_rmax'], (r_lim - c) - pose['land_rmax']
    return dict(block_flange=fb, land_flange=fl), min(pose['own_min_margin'], fb, fl)


def chg_pose_rows(cx, pose, nbrs, t_top):
    """R3-9 / R4-3 / R4-6: exact rows of ONE pose against every neighbour of the point (H14 terms) with the plan gap (exact polygon
    distance; a full-ring neighbour - the seal flange - by its radial gap, negative = radial penetration; an overlapping polygon pair
    as 0.000 with plan_overlap true) and the Z gap (adverse intervals). The LAND is judged under its contract rule (C-R1-01 2(v):
    plan AND Z, effective min(plan, Z); 2(vi): strict 3-D, effective max(plan, Z)) - contract_mandated. The BLOCK is judged under
    the common strict 3-D clearance against every neighbour - physical_required_elsewhere (C-R1-01 item 1 states no plan-AND-Z rule
    for the block) - and, against the 2(v) items only, additionally under the block-AND-Z screen - conservative_model_diagnostic
    (R1 model conservatism, not contract text). clear uses the strict rule (R3-3)."""
    land = feature('CHG_LAND', 'L-CHG', 'non-conductive land', False, False, dict(type='poly', pts=pose['land_poly']), ['REAR'], zfeat(0.0, t_top),
                   'charger land')
    block = feature('CHG_BLOCK', 'L-CHG', 'contact block', True, False, dict(type='poly', pts=pose['block_poly']), ['REAR'],
                    zfeat(0.0, cx.zm['z_band_lo_adv']), 'charger contacts')
    rows = []
    for n in nbrs:
        if n['geom'] is None:
            raise StudyError('STOP: governing rows need exact neighbour geometry (%s)' % n['id'])
        for a, rmax in ((land, pose['land_rmax']), (block, pose['block_rmax'])):
            count()
            zg = z_gap(a, n)
            if n['geom']['type'] == 'sector' and n['desc']['az'] is None:
                pg = n['desc']['r'][0] - rmax
                touching = pg <= EPS
            else:
                touching = plan_overlap(a['geom'], n['geom'])
                pg = 0.0 if touching else poly_distance(a['geom'], n['geom'])
            p_ok, z_ok = (not touching) and separated(pg), separated(zg)
            v = n['rule'] == 'v'
            base = dict(a=a['id'], b=n['id'], kind=n['kind'], item_rule='2(v)' if v else '2(vi)', plan_gap_mm=pg, plan_overlap=touching,
                        z_gap_mm=zg, plan_clear=p_ok, z_clear=z_ok)
            if a is land:
                rows.append(dict(base, category='contract_mandated', predicate='plan AND Z' if v else '3-D (plan OR Z)',
                                 clause_id='land_v' if v else 'land_vi',
                                 clear=(p_ok and z_ok) if v else (p_ok or z_ok), effective_clearance_mm=min(pg, zg) if v else max(pg, zg)))
            else:
                rows.append(dict(base, category='physical_required_elsewhere', predicate='3-D (plan OR Z)', clause_id='block_3d',
                                 clear=p_ok or z_ok, effective_clearance_mm=max(pg, zg)))
                if v:
                    rows.append(dict(base, category='conservative_model_diagnostic', predicate='plan AND Z', clause_id='block_and_z',
                                     clear=p_ok and z_ok, effective_clearance_mm=min(pg, zg)))
    return rows


# R4-3 / R4-6: attribution of every charger term (contract text verified verbatim against the briefs, CHG_CONTRACT_QUOTES)
CHG_TERM_CATEGORIES = ('contract_mandated', 'physical_required_elsewhere', 'conservative_model_diagnostic', 'supplier_diagnostic')
CHG_CLAUSES = dict(
    block_inner='C-R1-01 1: block r >= r_S14_outline + 1.100',
    block_reservation_outer='C-R1-01 1: block inside the authorized wedge (reservation r <= 24.0)',
    block_flange='C-R1-01 1: block r <= r_lim - c_chg_window',
    block_in_wedge='C-R1-01 1: block inside the authorized wedge (sides)',
    block_outside_wifi='C-R1-01 1: block clear of WIFI_RAD (H17)',
    land_non_conductive='C-R1-01 2(i): land carries no conductive material',
    land_caseback_side='C-R1-01 2(ii): land on the caseback side (no REAR-level Z intrusion)',
    land_inner_s14='C-R1-01 2(iii): land outside the S14 outline + 1.100 mm',
    land_radiators='C-R1-01 2(iv): land >= 1.0 mm (rf_clearance_report) from every radiator volume',
    routes_clear_in_plan='C-R1-01 2(v), plan part: land (and the block inside it) plan-clear of CHG_ROUTE / CHG_LINK',
    land_routes_clear_in_z='C-R1-01 2(v), Z part: land Z-separated from CHG_ROUTE / CHG_LINK',
    land_overshoot_cap='C-R1-01 3: side overshoot <= 0.75 mm perpendicular to a wedge side',
    land_azimuth_cap='C-R1-01 3: land inside az 78.0-102.0 deg',
    land_v='C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z',
    land_vi='C-R1-01 2(vi): the land clears every neighbouring functional structure (strict 3-D clearance)',
    land_flange='G4 c_chg_window_mm (charger aperture / feedthrough land to the caseback seal; G4 8.8 / H20 feedthrough clear) applied to '
                'the land outer edge; C-R1-01 1 names r_lim - c_chg_window for the block only',
    land_u6='brief section 3 frozen G3 U6 island (R1-H16); not a C-R1-01 clause',
    block_3d='G4 8.8 / H20 "Charger block, feedthrough and corridors clear": common strict 3-D clearance (R3-3); C-R1-01 states no '
             'plan-AND-Z rule for the block',
    block_routes_clear_3d='G4 8.8 / H20: block strictly 3-D clear of CHG_ROUTE / CHG_LINK (plan OR Z, R3-3)',
    block_and_z='R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether '
                'C-R1-01 intends it is Q-R1-CHARGER (a)',
    block_routes_clear_in_z='R1 model conservatism, NOT literal contract text: block strictly below the CHG_ROUTE / CHG_LINK conductor band',
    strict_wedge_land='C-R1-01 4 / SR-CHG-MECH supplier zero-margin threshold (land < value strictly); never credited',
    block_height_allocation='SR-CHG-MECH: block height allocation above Z = 0 (allocation fit, R1-H01)')
CHG_TERM_ATTRIBUTION = dict(
    block_inner='contract_mandated', block_reservation_outer='contract_mandated', block_flange='contract_mandated',
    block_in_wedge='contract_mandated', block_outside_wifi='contract_mandated', land_non_conductive='contract_mandated',
    land_caseback_side='contract_mandated', land_inner_s14='contract_mandated', land_radiators='contract_mandated',
    routes_clear_in_plan='contract_mandated', land_routes_clear_in_z='contract_mandated', land_overshoot_cap='contract_mandated',
    land_azimuth_cap='contract_mandated', land_flange='physical_required_elsewhere', land_u6='physical_required_elsewhere',
    block_routes_clear_3d='physical_required_elsewhere', block_routes_clear_in_z='conservative_model_diagnostic',
    strict_wedge_land='supplier_diagnostic', block_height_allocation='supplier_diagnostic')
# verbatim contract text (normalized: '**' removed, whitespace collapsed) that the attribution rests on; the validator requires each
# quote inside its brief
CHG_CONTRACT_QUOTES = [
    dict(source=BRIEF, clause='C-R1-01 1 (block)', text='the conductive 4 x 5 mm contact block lies inside the authorized wedge, inside the '
         'radial bounds `r_S14_outline + 1.100 <= r <= r_lim - c_chg_window`, and clear of WIFI_RAD (H17);'),
    dict(source=BRIEF, clause='C-R1-01 2 (land subject)', text='the non-conductive bond/seal land is a caseback-side feature. It need not lie '
         'entirely inside the wedge if and only if it (i) carries no conductive material,'),
    dict(source=BRIEF, clause='C-R1-01 2(v) / 2(vi) (land)', text='(v) clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z, and '
         '(vi) clears every neighbouring functional structure (switch bores/bosses, vent, lug and support features);'),
    dict(source=BRIEF, clause='C-R1-01 4 (strict wedge)', text='the strict-wedge result (land fully inside the wedge) is retained as a '
         'diagnostic and as the supplier path:'),
    dict(source=BRIEF, clause='hard-check row R1-H14', text='Charger: block inside wedge and outside WIFI_RAD; land per C-R1-01 with overshoot <= caps; '
         'corridors clear in plan and Z'),
    dict(source='design/mechanical/G4_BRIEF.md', clause='G4 H20 row', text='Charger block, feedthrough and corridors clear')]
CHG_ATTRIBUTION_NOTE = (
    'C-R1-01 2(v) applies "in plan and in Z" to the NON-CONDUCTIVE LAND (item 2 subject). C-R1-01 item 1 (block) states no plan-AND-Z rule; '
    'the R1-H14 row reads "corridors clear in plan and Z" without naming the block, and G4 H20 reads "Charger block, feedthrough and '
    'corridors clear". R1 therefore holds the block to the common strict 3-D clearance (physical) and reports the block-AND-Z screen as '
    'model conservatism only; whether the conjunctive rule applies to the block (a) or to the strict-wedge alternative (b) is asked in '
    'Q-R1-CHARGER, not assumed.')


def chg_term(tid, value, units, passed, clause_key=None, category=None, **extra):
    cid = clause_key or tid
    if cid not in CHG_CLAUSES:
        raise StudyError('STOP: charger term %s without a contract / model clause' % tid)
    return dict(dict(id=tid, category=category or CHG_TERM_ATTRIBUTION[tid], clause_id=cid, value=value, units=units, pass_=passed), **extra)


def chg_governing_summary(gv):
    """Serialized summary of a typed charger term set (the full typed terms live once in the R1-H14 record): categories, governing
    term, failing terms, physical pass."""
    if gv is None:
        return None
    return dict((k, v) for k, v in gv.items() if k not in ('terms', 'attribution_note'))


def chg_governing(cx, pose, flange, rows, extra_terms=()):
    """R3-9 / R4-6: complete typed term list of one pose (radial / plan / Z / material predicates and every neighbour row), each term in
    exactly one category (CHG_TERM_CATEGORIES) with its clause, value and units. No minimum is ever taken across units or categories:
    minima are reported per (category, units) group, booleans as failing predicates, degrees separately. The check-level governing
    term is the minimum mm term of the contract-mandated category (ties broken by term id); physical pass = every
    contract_mandated and physical_required_elsewhere term passes (diagnostics never decide)."""
    m, md = pose['margins'], pose['margins_deg']
    pr = pose['predicates']
    terms = [chg_term(k, m[k], 'mm', m[k] >= -EPS) for k in ('block_inner', 'block_reservation_outer', 'block_in_wedge', 'land_inner_s14',
                                                             'land_radiators', 'land_overshoot_cap')]
    terms.append(chg_term('land_u6', m['land_u6'], 'mm', separated(m['land_u6'])))
    terms += [chg_term(k, v, 'mm', v >= -EPS) for k, v in sorted(flange.items())]
    terms.append(chg_term('land_azimuth_cap', md['land_azimuth_cap'], 'deg', md['land_azimuth_cap'] >= -EPS))
    for k in ('block_outside_wifi', 'land_non_conductive', 'land_caseback_side', 'routes_clear_in_plan', 'land_routes_clear_in_z',
              'block_routes_clear_3d', 'block_routes_clear_in_z'):
        terms.append(chg_term(k, bool(pr[k]), 'bool', bool(pr[k])))
    for r in rows:
        tag = ' [plan AND Z]' if r['predicate'] == 'plan AND Z' else ' [3-D]'
        terms.append(dict(id='%s vs %s%s' % (r['a'], r['b'], tag), category=r['category'], clause_id=r['clause_id'], value=r['effective_clearance_mm'],
                          units='mm', pass_=r['clear'], predicate=r['predicate'], item_rule=r['item_rule'], plan_gap_mm=r['plan_gap_mm'],
                          plan_overlap=r['plan_overlap'], z_gap_mm=r['z_gap_mm']))
    terms += list(extra_terms)
    ids = [t['id'] for t in terms]
    if len(set(ids)) != len(ids) or any(t['category'] not in CHG_TERM_CATEGORIES for t in terms):
        raise StudyError('STOP: charger term ids not unique or category outside %s' % (CHG_TERM_CATEGORIES,))
    groups = {}
    for t in terms:
        if t['pass_'] is None or t['units'] == 'bool':
            continue
        key = (t['category'], t['units'])
        if key not in groups or (t['value'], t['id']) < (groups[key]['value'], groups[key]['id']):
            groups[key] = dict(id=t['id'], value=t['value'], units=t['units'])
    cats = {}
    for c in CHG_TERM_CATEGORIES:
        mine = [t for t in terms if t['category'] == c]
        decides = c in ('contract_mandated', 'physical_required_elsewhere')
        cats[c] = dict(decides_physical_pass=decides, terms=len(mine),
                       pass_=all(t['pass_'] for t in mine if t['pass_'] is not None) if decides else None,
                       failing=sorted(t['id'] for t in mine if t['pass_'] is False),
                       minimum_by_units={u: dict((k, v) for k, v in g.items() if k != 'units') for (cc, u), g in sorted(groups.items()) if cc == c})
    gov = groups.get(('contract_mandated', 'mm'))
    return dict(terms=terms, categories=cats, physical_pass=cats['contract_mandated']['pass_'] and cats['physical_required_elsewhere']['pass_'],
                failing_terms=[t for t in terms if t['pass_'] is False],
                governing=dict(category='contract_mandated', term_id=gov['id'], value=gov['value'], units='mm'),
                azimuth_cap_margin_deg=md['land_azimuth_cap'], attribution_note=CHG_ATTRIBUTION_NOTE,
                rule='typed terms in four categories; physical pass = every contract_mandated and physical_required_elsewhere term passes at '
                     'one pose; conservative / supplier diagnostics never decide; no minimum across units or categories (per (category, '
                     'units) minima only); governing = minimum contract_mandated mm term (ties by id); 2(v) land rows: min(plan, Z), 3-D '
                     'rows: max(plan, Z)')


def envelope_containment_violations(cx, cand, exact_feats):
    """The exact design-point supports / pads / vent lie inside the window envelopes used at the sweep points (az span inside the
    envelope span, identical Z interval)."""
    env = {e['id']: e for e in chg_static_envelopes(cx, cand)}
    bad = []
    for f in exact_feats:
        e = env.get(f['id'])
        if e is None:
            continue
        r = nb_record(cx, f, chg_rule(cx, f))
        a, w = r['desc']['az'], e['desc']['az']
        inside = a is not None and g4.arc_has(a[0], *w) and g4.arc_has(a[1], *w) and \
            (a[1] - a[0]) % 360.0 <= (w[1] - w[0]) % 360.0 + 1e-9 and (a[0] - w[0]) % 360.0 <= (w[1] - w[0]) % 360.0 + 1e-9
        if not inside or abs(r['z_lo_adv'] - e['z_lo_adv']) > 1e-12 or abs(r['z_hi_adv'] - e['z_hi_adv']) > 1e-12:
            bad.append('%s %s: exact feature outside its sweep window envelope' % (cand['id'], f['id']))
    return bad


def charger_report(cx, cand, sw, chg, tw):
    """R3-8 / R3-2: charger thresholds by category at the design point and on the D grid. A radial or plan prerequisite is never
    a charger closure; only the literal category (complete C-R1-01 predicate against the complete same-point neighbour set) is."""
    st, zm = cx.st, cx.zm
    tol = cx.ce[cand['id']].sp.pc_env['radius_mm']
    cls = sw['classification']
    F = cls['charger_first_D']
    E_rlim = chg['r_lim']
    RC = cx.P['V20_charger_land']['route_clearance']
    P = lambda p: None if p is None else dict(orientation=p['orientation'], r_centre=p['r_centre'], az_centre=p['az_centre'], land=p['land'])

    def need(req, pose, keys):
        return dict(r_lim_required_mm=req, pose=P(pose), r_lim_available_mm=E_rlim, deficit_mm=None if req is None else req - E_rlim,
                    required_bore_radius_mm=None if req is None else req + tol,
                    required_D_at_design_wall_mm=None if req is None else 2.0 * (req + tol + tw), **{k: F[k] for k in keys})
    rows = chg['neighbours']['rows']
    v_rows = [r for r in rows if r['item_rule'] == '2(v)' and r['b'] not in RC['routes'] and r['predicate'] == 'plan AND Z']
    r_rows = [r for r in rows if r['b'] in RC['routes'] and r['category'] != 'conservative_model_diagnostic']
    lvz = chg['land_v_z']
    s = chg['strict_wedge']
    dg = chg['diagnostics']
    by_cat = lambda rr: {c: sorted({'%s vs %s' % (r['a'], r['b']) for r in rr if not r['clear'] and r['category'] == c})
                         for c in CHG_TERM_CATEGORIES if c != 'supplier_diagnostic'}
    s_failing_pose = {k for k in ('routes_clear_in_plan', 'land_clear_of_u6', 'block_outside_wifi') if s.get('pose') and not s['pose']['predicates'][k]}
    return dict(
        rule='R3-1 / R3-8 / R4-3: radial and plan prerequisites, the LAND\'s contract Z prerequisite, the complete same-point neighbour set '
             'and the literal closure are separate categories; only literal (contract-mandated + physical predicates at one pose) closes the '
             'charger. C-R1-01 2(v) "in plan and in Z" is applied to the non-conductive LAND (its subject); the conductive block is held to '
             'item 1 and the common strict 3-D clearance (R3-3: a zero gap is a collision); the block-AND-Z screen is R1 model '
             'conservatism (diagnostic, not contract text).',
        attribution=dict(note=CHG_ATTRIBUTION_NOTE, quotes=CHG_CONTRACT_QUOTES, categories=list(CHG_TERM_CATEGORIES),
                         contract_land_predicate='C-R1-01 2(i)-(vi) and item 3 for the land: (v) plan AND Z against screws, supports, CHG_ROUTE, '
                                                 'CHG_LINK; (vi) strict 3-D against every other neighbouring functional structure',
                         block_physical_predicates='C-R1-01 item 1 (wedge, radial bounds incl. r_lim - c_chg_window, WIFI_RAD) and the common '
                                                   'strict 3-D clearance against every neighbour (G4 8.8 / H20)',
                         block_and_z_diagnostic='optional conservative screen: block plan AND Z against the 2(v) items and strictly below the '
                                                'conductor band - lead / model conservatism, NOT literal contract text; never decides'),
        categories_at_design_point=dict(chg['categories']),
        radial_prerequisite=need(sw['chg_r_lim_required_radial'], sw['chg_radial_pose'], ('first_radial', 'first_radial_with_radial_core')),
        plan_prerequisite=need(sw['chg_r_lim_required'], sw['chg_required_pose'],
                               ('first_plan', 'first_plan_with_radial_core', 'first_plan_with_radial_core_and_main_seal', 'first_plan_with_radial_core_and_od')),
        z_prerequisite=dict(pass_=chg['categories']['z'], first_D=F['first_z'], land_top_mm=chg['land_top_mm'],
                            route_z_gaps_mm={'%s vs %s' % (r['a'], r['b']): r['z_gap_mm'] for r in r_rows},
                            v_item_min_z_gap_mm=dict(land=min([r['z_gap_mm'] for r in v_rows if r['a'] == 'CHG_LAND'], default=None)),
                            z_unsatisfiable_items=lvz['unsatisfiable_items'], land_unsatisfiability=lvz,
                            threshold='C-R1-01 2(v) Z part (contract, LAND): the land [0, %.3f] mm strictly Z-separated from CHG_ROUTE / CHG_LINK '
                                      '(gap %s mm) and from every 2(v) screw / support; those items share the Z = 0 caseback datum, so '
                                      'Z_gap = max(z_lo - h_land, -H) <= -min(h_land, H) <= 0 and the land\'s conjunctive (v) clause is '
                                      'unsatisfiable for every pose, D and land width under the retained G4 Z model (contract / owner question '
                                      'Q-R1-CHARGER); not generalized to the block or the strict-wedge alternative' % (
                                          chg['land_top_mm'], fs(min([r['z_gap_mm'] for r in r_rows if r['a'] == 'CHG_LAND'], default=None)))),
        block_and_z_diagnostic=dict(
            label='lead / model conservatism - NOT literal contract text; never decides R1-H14', pass_=dg['block_and_z'],
            block_top_mm=zm['z_band_lo_adv'], conductor_band_floor_mm=zm['z_band_lo_adv'], v_item_min_z_gap_mm=dg['z_min_v_block_mm'],
            route_z_gaps_mm={'%s vs %s' % (r['a'], r['b']): r['z_gap_mm'] for r in r_rows if r['a'] == 'CHG_BLOCK'},
            route_plan_gaps_mm={'%s vs %s' % (r['a'], r['b']): r['plan_gap_mm'] for r in r_rows if r['a'] == 'CHG_BLOCK'},
            block_3d_clear_of_routes=all(r['clear'] for r in r_rows if r['a'] == 'CHG_BLOCK'),
            note='at the SR-CHG-MECH allocation height (%.3f mm, the conductor band floor) the block has a zero Z gap to CHG_ROUTE / CHG_LINK; '
                 'it is plan-separated from them, so the common 3-D predicate holds (not a 3-D collision). The zero allocation margin is '
                 'the separate R1-H01 allocation check.' % zm['z_band_lo_adv']),
        v_z_waived_diagnostic=dict(
            label='DIAGNOSTIC ONLY - consequence quantification for Q-R1-CHARGER: the literal predicate with only the conjunctive Z part of '
                  'C-R1-01 2(v) waived for a land that is plan-disjoint from the item; never a closure, never credited; C-R1-01 is not amended',
            design_point=dg['literal_v_z_waived'], first_D=F['first_literal_v_z_waived'],
            first_D_with_radial_core=F['first_literal_v_z_waived_with_radial_core'],
            first_D_with_radial_core_and_od=F['first_literal_v_z_waived_with_radial_core_and_od'],
            first_D_with_radial_core_and_main_seal=F['first_literal_v_z_waived_with_radial_core_and_main_seal']),
        neighbour_complete=dict(pass_=chg['categories']['neighbours'], first_D=F['first_neighbours'], failing_by_category=by_cat(rows)),
        literal=dict(pass_=chg['pass_'], first_D=F['first_literal'], first_D_with_radial_core=F['first_literal_with_radial_core'],
                     first_D_with_radial_core_and_main_seal=F['first_literal_with_radial_core_and_main_seal']),
        strict_wedge_supplier_path=dict(
            width_mm=s['width_mm'], chg_r_out_mm=s['chg_r_out_mm'], centre_interval_mm=s['centre_interval_mm'],
            pose=P(s['pose']) if s.get('pose') else None, contained_in_wedge=s['contained'], in_land_range=s['in_land_range'], plan=s['plan'],
            neighbours=s['neighbours'], z=s['z'], complete=s['complete'],
            neighbours_v_z_waived=s['neighbours_v_z_waived'], complete_v_z_waived=s['complete_v_z_waived'],
            failing_terms_by_category=dict(by_cat(s['rows']), pose_predicates=sorted(s_failing_pose)),
            first_D_in_land_range=F['first_sw_in_land_range'], first_D_plan=F['first_sw_plan'], first_D_complete=F['first_sw_complete'],
            first_D_complete_v_z_waived=F['first_sw_complete_v_z_waived'],
            first_D_complete_v_z_waived_with_radial_core=F['first_sw_complete_v_z_waived_with_radial_core'],
            land_min_mm=s['land_min_mm'], adverse_authored_land_mm=s['land_adverse_mm'],
            v_applicability='C-R1-01 2(v) applied to the strict-wedge land is the R1 reading pending Q-R1-CHARGER (b) (item 2 conditions govern '
                            'a land that leaves the wedge; item 4 names the strict wedge a diagnostic / supplier path); the v_z_waived columns '
                            'show the other reading; neither is a closure',
            threshold='SUPPLIER ZERO-MARGIN THRESHOLD only (SR-CHG-MECH): land < %s mm strictly (at zero margin the inner land corners lie on '
                      'the wedge sides); never credited as a physical pass; the authored adverse land stays %.3f mm' % (
                          f3(s['width_mm']), s['land_adverse_mm'])),
        poses_evaluated=len(sw['poses']), poses_meeting_r_lim_independent_prerequisites=sum(1 for p in sw['poses'] if p['prereq_pass']),
        poses_meeting_every_pose_level_predicate=sum(1 for p in sw['poses'] if p['pass_']),
        first_D=F, coupled_first_D=cls['coupled_first_D'])


def charger_design_point(cx, cand, sw, row, seal, strl, core, pre, vent_feat, D, tw):
    """R3-1 / R3-9: the charger at the design point - the same chg_point_eval as every sweep point, with the EXACT neighbour
    features of this point (screws, case-side supports, pads, lugs, spring bars, R1 button plungers / boots / bosses, vent, the
    selected plate's ribs) instead of the window envelopes (which must contain them), the selected plate for the land top and
    the coupled seal flange; the reported pose is a literal-closure pose if one exists, otherwise the chg_select pose (the
    structural land interrupter); its complete governing failure is listed term by term."""
    zm = cx.zm
    t_top = chg_land_top(cx, cand, strl['selected']['t_out'])
    exact = [f for f in pre['features'] if f['kind'] in CHG_NEIGHBOUR_KINDS] + ([vent_feat] if vent_feat else [])
    ribs = [f for f in pre['features'] if f['kind'] == 'caseback rib']
    bad = envelope_containment_violations(cx, cand, exact)
    if bad:
        raise StudyError('STOP: ' + '; '.join(bad))
    fl_top = flange_top(cx, cand, seal, strl['selected']['t_out'])
    nbrs = chg_neighbours_at(cx, cand, D, tw, row, fl_top, exact_feats=exact, rib_feats=ribs)
    fl_pre = next(f for f in pre['features'] if f['kind'] == 'caseback seal flange')
    fl_nb = next(n for n in nbrs if n['id'] == 'CB_SEAL_FLANGE')
    if json.dumps(fl_pre['geom'], sort_keys=True) != json.dumps(fl_nb['geom'], sort_keys=True) or abs(fl_pre['z_hi_adv'] - fl_nb['z_hi_adv']) > 1e-12:
        raise StudyError('STOP: charger seal-flange neighbour differs from the design-point flange feature')
    strict = strict_wedge_path(cx, cand, core['r_lim'])
    pe = chg_point_eval(cx, sw['pose_ctx'], core['r_lim'], t_top, nbrs, strict)
    sel = chg_select(cx, cand, sw['poses'], core['r_lim'])
    pose = pe['literal_pose'] or sel['pose']
    flange, mm_ = chg_flange(cx, pose, core['r_lim'])
    rows = chg_pose_rows(cx, pose, nbrs, t_top)
    s_rows = chg_pose_rows(cx, strict['pose'], nbrs, t_top) if strict['pose'] else []
    supp = [chg_term('strict_wedge_land', strict['width_mm'], 'mm', None,
                     quantity='largest land width fitting the wedge strictly (supplier zero-margin threshold; land < value strictly)'),
            chg_term('block_height_allocation', zm['z_band_lo_adv'], 'mm', None,
                     quantity='block height allocation above Z = 0 (SR-CHG-MECH; R1-H01 allocation fit)')]
    gov = chg_governing(cx, pose, flange, rows, supp)
    if gov['physical_pass'] != pe['literal']:
        raise StudyError('STOP: typed H14 terms (contract + physical) disagree with the same-point literal charger closure')
    sfr = seal_flange_rows(cx, cand, seal, row, D, pose, t_top, strl['selected']['t_out'], rows)
    s_gov = chg_governing(cx, strict['pose'], chg_flange(cx, strict['pose'], core['r_lim'])[0], s_rows, supp) if strict['pose'] else None
    v_items = [n for n in nbrs if n['rule'] == 'v' and n['id'] not in cx.P['V20_charger_land']['route_clearance']['routes']]
    return dict(pose=pose, flange_margins=flange, min_margin=mm_, r_lim=core['r_lim'], prereq_pass=sel['prereq_pass'],
                categories={k: pe[k] for k in CHG_CATEGORIES}, pass_=pe['literal'], land_top_mm=t_top, block_top_mm=zm['z_band_lo_adv'],
                diagnostics=dict(block_and_z=pe['block_and_z'], neighbours_v_z_waived=pe['neighbours_v_z_waived'],
                                 literal_v_z_waived=pe['literal_v_z_waived'], z_min_v_land_mm=pe['z_min_v_land_mm'],
                                 z_min_v_block_mm=pe['z_min_v_block_mm']),
                flange_top_mm=fl_top, seal_flange_rows=sfr, neighbours=dict(pass_=pe['neighbours'], rows=rows, evaluated=len(nbrs)), governing=gov,
                strict_wedge=dict(pe['strict_wedge'], contained=strict['contained'], centre_interval_mm=strict['centre_interval_mm'],
                                  pose=strict['pose'], land_min_mm=strict['land_min_mm'], land_adverse_mm=strict['land_adverse_mm'],
                                  rows=s_rows, governing=s_gov),
                v_items=[dict(id=n['id'], kind=n['kind'], z_lo_adv=n['z_lo_adv'], z_hi_adv=n['z_hi_adv']) for n in v_items],
                land_v_z=land_v_z_unsatisfiability(t_top, v_items),
                nbrs=nbrs)


def seal_flange_rows(cx, cand, seal, row, D, pose, t_top, t_out, env_rows):
    """R5: the H14 seal-flange rows of EVERY row r of the coupled seal population at the design pose (CHG_LAND / CHG_BLOCK vs the
    flange r induces: plan gap, Z gap, effective clearance, clear) and their reduction; the H14 flange terms (evaluated on the
    envelope flange_top) must equal min effective clearance / all clear over the rows (STOP otherwise)."""
    out = []
    for r in seal_rows(seal, seal['coupled']['population']):
        ft = row_flange_top(cx, cand, r, t_out)
        for x in chg_pose_rows(cx, pose, [flange_neighbour(cx, cand, row, D, ft)], t_top):
            out.append(dict(seal_row=r['id'], cs_mm=r.get('cs_mm'), flange_top_mm=ft, a=x['a'], b=x['b'], category=x['category'],
                            clause_id=x['clause_id'], plan_gap_mm=x['plan_gap_mm'], z_gap_mm=x['z_gap_mm'],
                            effective_clearance_mm=x['effective_clearance_mm'], clear=x['clear']))
    red = {}
    for a in ('CHG_LAND', 'CHG_BLOCK'):
        mine = [x for x in out if x['a'] == a and x['category'] != 'conservative_model_diagnostic']
        env = next(x for x in env_rows if x['a'] == a and x['b'] == 'CB_SEAL_FLANGE' and x['category'] != 'conservative_model_diagnostic')
        red[a] = dict(effective_clearance_min_mm=min(x['effective_clearance_mm'] for x in mine), z_gap_min_mm=min(x['z_gap_mm'] for x in mine),
                      clear_all_rows=all(x['clear'] for x in mine), clear_any_row=any(x['clear'] for x in mine),
                      envelope_effective_clearance_mm=env['effective_clearance_mm'], envelope_z_gap_mm=env['z_gap_mm'], envelope_clear=env['clear'])
        if abs(red[a]['effective_clearance_min_mm'] - env['effective_clearance_mm']) > 1e-9 or red[a]['clear_all_rows'] != env['clear'] or \
                abs(red[a]['z_gap_min_mm'] - env['z_gap_mm']) > 1e-9:
            raise StudyError('STOP: H14 seal-flange envelope term differs from the reduction over the seal population rows (%s)' % a)
    return dict(rows=out, reduction=red, population=seal['coupled']['population'], rule=SEAL_REDUCTION_RULES['h14_flange_rows'])


def seal_supplier_thresholds(cx, cand, seal):
    """R5: strict-wedge supplier zero-margin land widths per seal row (C-R1-01 item 4; SR-CHG-MECH threshold, never credited). Face /
    adhesive rows share one r_lim (unique width, checked); radial rows each carry their own r_lim(r): governing threshold = min over the
    authorized radial rows (taken in the seal internal unit), envelope [min, max] (SEAL_REDUCTION_RULES['radial_supplier_land'])."""
    st = cx.st
    unit, s = seal_unit(cx)
    r1, c = st.res['CHG_CONTACT']['geometry']['r'][1], st.P['c_chg_window_mm']['max']
    fa = [r for t in ('face', 'adhesive') for r in seal_rows(seal, seal['topologies'][t]['evaluated_rows'])]
    fa_r = sorted({round(r['r_lim_mm'], 9) for r in fa})
    if len(fa_r) != 1:
        raise StudyError('STOP: face / adhesive seal rows do not share one caseback radial limit (%s)' % fa_r)
    rad = []
    for r in seal_rows(seal, seal['topologies']['radial']['evaluated_rows']):
        p = strict_wedge_path(cx, cand, r['r_lim_mm'])
        rad.append(dict(row=r['id'], cs_mm=r['cs_mm'], r_lim_mm=r['r_lim_mm'], chg_r_out_mm=p['chg_r_out_mm'], width_mm=p['width_mm']))
    w_int = [x['width_mm'] * s for x in rad if x['width_mm'] is not None]
    gov = min(w_int) if w_int else None
    return dict(at_face_adhesive_r_lim=strict_wedge_path(cx, cand, fa[0]['r_lim_mm'])['width_mm'], face_adhesive_r_lim_mm=fa[0]['r_lim_mm'],
                at_radial_r_lim=dict(rows=rad, governing_threshold_mm=None if gov is None else gov / s,
                                     governing_rows=[x['row'] for x in rad if x['width_mm'] is not None and abs(x['width_mm'] * s - gov) <= 1e-12 * s],
                                     envelope_mm=None if not w_int else [min(w_int) / s, max(w_int) / s],
                                     rows_without_fit=[x['row'] for x in rad if x['width_mm'] is None]),
                rule=SEAL_REDUCTION_RULES['radial_supplier_land'])


def charger_by_topology(cx, cand, sw, seal, chg, row, D, t_out):
    """R5: the complete same-point charger predicate per seal topology, evaluated for EVERY evaluated row r of that topology with its
    own r_lim(r) and flange_top(r) (distinct pairs evaluated once); topology result = any / all over its rows (both reported)."""
    out = {}
    for t in SEAL_ORDER:
        groups = {}
        for r in seal_rows(seal, seal['topologies'][t]['evaluated_rows']):
            ft = row_flange_top(cx, cand, r, t_out)
            groups.setdefault((round(r['r_lim_mm'], 9), round(ft, 9)), (r['r_lim_mm'], ft, []))[2].append(r['id'])
        recs = []
        for _, (rl, ft, ids) in sorted(groups.items()):
            nb = [flange_neighbour(cx, cand, row, D, ft) if n['id'] == 'CB_SEAL_FLANGE' else n for n in chg['nbrs']]
            sel_t = chg_select(cx, cand, sw['poses'], rl)
            pe_t = chg_point_eval(cx, sw['pose_ctx'], rl, chg['land_top_mm'], nb, strict_wedge_path(cx, cand, rl))
            recs.append(dict(rows=ids, r_lim=rl, flange_top_mm=ft, pose=sel_t['pose'], min_margin=sel_t['min_margin'], prereq_pass=sel_t['prereq_pass'],
                             categories={k: pe_t[k] for k in CHG_CATEGORIES}, pass_=pe_t['literal']))
        out[t] = dict(evaluations=recs, r_lim_envelope_mm=[min(x['r_lim'] for x in recs), max(x['r_lim'] for x in recs)],
                      pass_any_row=any(x['pass_'] for x in recs), pass_all_rows=all(x['pass_'] for x in recs),
                      categories_any_row={k: any(x['categories'][k] for x in recs) for k in CHG_CATEGORIES},
                      categories_all_rows={k: all(x['categories'][k] for x in recs) for k in CHG_CATEGORIES},
                      rule=SEAL_REDUCTION_RULES['charger_by_topology'])
    return out


def land_v_z_unsatisfiability(h_land, v_items):
    """R4-4: the contracted LAND predicate C-R1-01 2(v) requires a strictly positive Z gap between the land [0, h_land] and every
    screw / support item [z_lo, H] (retained G4 common-Z model, shared datum Z = 0 at the caseback plane). For z_lo <= 0:
    Z_gap = max(z_lo - h_land, 0 - H) <= max(-h_land, -H) = -min(h_land, H) <= 0, so strict-positive Z separation is impossible
    whatever the pose, D or land width. Scope: the LAND only - never generalized to the conductive block, the strict-wedge alternative
    or other charger structures."""
    land = zfeat(0.0, h_land)
    items = []
    for n in v_items:
        zg = z_gap(land, n)
        shared = n['z_lo_adv'] <= EPS
        items.append(dict(id=n['id'], kind=n['kind'], z_lo_adv_mm=n['z_lo_adv'], H_mm=n['z_hi_adv'], z_gap_mm=zg,
                          closed_form_mm=max(n['z_lo_adv'] - h_land, -n['z_hi_adv']), bound_mm=-min(h_land, n['z_hi_adv']) if shared else None,
                          shares_datum=shared, unsatisfiable=shared and not separated(zg)))
    return dict(h_land_mm=h_land, items=items, unsatisfiable_items=sorted(x['id'] for x in items if x['unsatisfiable']),
                unsatisfiable=bool(items) and any(x['unsatisfiable'] for x in items),
                rule='land [0, h_land], screw / support [z_lo, H] with z_lo <= 0 (shared Z = 0 datum): Z_gap = max(z_lo - h_land, -H) <= '
                     '-min(h_land, H) <= 0; a strictly positive Z gap (R3-3) is impossible, so the conjunctive plan AND Z clause 2(v) cannot '
                     'hold for the land for any pose, D or land width under the retained G4 Z model (contract / owner question)',
                scope='LAND (C-R1-01 2(v) subject) only; not generalized to the conductive block, the strict-wedge alternative or other '
                      'charger structures')


def evaluate_candidate(cx, cand, sw=None, point=None):
    """One candidate: the full sweep / classification (or a supplied sweep, reused read-only), the design point (or an explicit (D, tw)
    point, for the R5 end-to-end regression) and every lane at that point."""
    st = cx.st
    ce = cx.ce[cand['id']]
    sp = ce.sp
    if sw is None:
        sw = sweep_candidate(cx, cand)
        sw['classification'] = classify(cx, cand, sw)
    cls = sw['classification']
    D, tw, rule = design_choice(cx, sw, cls) if point is None else (point[0], point[1], 'explicit point (R5 regression)')
    core = point_core(cx, cand, sw, D, tw, True)
    row, seal, strl = core['row'], core['seal'], core['strl']
    btn = lane_btn(cx, cand, D, True)
    prune_eq = all(btn_best(cx, btn_terms(cx, cand, s), D, t, i, False)['min_margin'] == btn['switches'][s]['T2'][t][i]['min_margin']
                   for s in btn['switches'] for t in ('T2-R', 'T2-F') for i in ('I-SUM', 'I-MAX'))
    win = lane_win(cx, cand)
    dp = dp_for_g4(cx, cand, D, tw, row, seal, core['chg'], strl, btn)
    mod = module_features(cx)
    pre = build_features(cx, cand, dp, btn, core['chg'], strl, seal, row)
    vent_feat = None
    if pre['vent']:
        v = pre['vent']
        vent_feat = feature('VENT_PORT', 'L-SEAL', 'membrane port', False, False,
                            g4.sector(v['centre'] - v['half'], v['centre'] + v['half'], row['R_side'], D / 2.0), ['MAIN'], zfeat(*level_z(st)['MAIN']),
                            'vent port')
    chg = charger_design_point(cx, cand, sw, row, seal, strl, core, pre, vent_feat, D, tw)
    if chg['pose'] is not core['chg']['pose']:
        strl = lane_str(cx, cand, row, core['r_lim'], chg['pose'], True)
    sdp = design_point_structure(cx, cand, sw, row, core['r_lim'], chg['pose'], strl)
    feats = build_features(cx, cand, dp, btn, chg, strl, seal, row)
    F = feats['features'] + ([vent_feat] if vent_feat else [])
    view_bad = feature_view_violations(F, mod)
    if view_bad:
        raise StudyError('STOP: ' + '; '.join(view_bad))
    rfm = g4.rf_mag_check(st, F)
    s14 = g4.s14_untouched(st, [f for f in F if f['kind'] not in ('caseback seal flange',)], dp)
    sup = g4.support_check(st, sp, dp, feats['supports'])
    post = g4.post_load(st, sp, dp)
    path = g4.load_paths(cand)
    forb = forbidden_loads(cx, cand, strl, F, mod, path)
    clos = closure_rows(cx, F, mod)
    ft = ft_topology(cand, (strl.get('split') or {}).get('selected', {}).get('r_split'), chg['pose']['land_rmin'])
    inv = seal_inventory_r1(cx, cand, btn, seal['closed_topology'], ft)
    seal_outer = D / 2.0 if seal['coupled']['topology'] in ('face', 'adhesive') else row['R_side']
    scr = screws_outside(cx, cand, D, seal_outer)
    closure = g4.seal_closure(inv, screws_outside=scr['outside'])
    vent_land = None
    if pre['vent']:
        bv = st.P['bond_lands']
        terms = [sp.design('membrane_radius', pre['vent']['membrane_dia_mm'] / 2), sp.par('port_dia', 'max', bv['vent_port_dia_mm']),
                 sp.par('bond_land', 'max', bv['vent_membrane_land_mm']), sp.tol('local_radius_tol', sp.pc_env['radius_mm'])]
        vent_land = g4.run_check(g4.spec('H16-VENT-LAND', 'H16', 'vent membrane bond land', terms,
                                         lambda v: v['membrane_radius'] - v['port_dia'] / 2 - v['local_radius_tol'] - v['bond_land']), full=False)
    win_land = g4.run_check(sp.window_land(), full=False)
    cover = dict(fit=g4.fix_pass(g4.run_check(sp.cover_fit(dp))), ledge=g4.fix_pass(g4.run_check(sp.cover_ledge(dp))),
                 u4=g4.fix_pass(g4.run_check(sp.u4(dp))), body=g4.fix_pass(g4.run_check(sp.btn_height(dp))),
                 plate=sp.cover_plate(dp), proud=g4.cover_proud(st, sp, dp))
    feas = {
        'S-COVER': cover['fit']['pass'] and cover['ledge']['pass'],
        'S-CB-MAIN': seal['physical_pass'],
        'S-VENT': pre['vent'] is not None and vent_land is not None and vent_land >= -EPS,
        'S-POD': win_land >= -EPS,
        'S-CHG': chg['pass_'],
    }
    for s_ in btn['switches']:
        feas['S-' + s_] = btn['closed'] or (btn['switches'][s_]['pass_I_SUM'] and btn['switches'][s_]['pass_I_MAX'])
    split_bond = strl.get('split_bond')
    if cand['caseback'].get('split'):
        feas['S-CB-SPLIT'] = bool(split_bond) and split_bond['joint_check'] >= -EPS and strl['split']['feasible']
    cond = g4.conditional_seals(st, sp, dp)
    lra = lane_lra(cx, cand, row, dp, core['r_lim'], chg, strl, sdp, sw['sctx'])
    rel = struct_geometry(cx, cand, sw['sctx'], row, core['r_lim'], pose=chg['pose'])['rel'] if sw['sctx']['geometry_ok'] else None
    resc = str_lra_rescreen(cx, cand, strl, lra['best_plan_env'], lra['pocket']['residual_mm'], rel, sw['sctx']['configs']) \
        if lra['best_plan_env'] else None
    strict = seal_supplier_thresholds(cx, cand, seal)
    chg_lit = charger_report(cx, cand, sw, chg, tw)
    asm = lane_asm(cx, cand, row, btn, lra, clos, deps=dict(seal=seal, chg=chg, strl=strl, win=win))
    rcase = g4.r_case_table(st, sp, dp, feats['buttons'], feats['supports'])
    protr = g4.bosses_permitted(st, rcase, D, sp.pc_mid['boss_mm'])
    chg_by_topo = charger_by_topology(cx, cand, sw, seal, chg, row, D, strl['selected']['t_out'])
    return dict(id=cand['id'], cand=cand, sweep=sw, classification=cls, D=D, tw=tw, design_rule=rule, row=row,
                seal=seal, btn=btn, btn_prune_equal=prune_eq, win=win, chg=chg, chg_by_topology=chg_by_topo, strict_wedge=strict,
                chg_literal=chg_lit, ft=ft, strl=strl, structure_design_point=sdp, dp=dp, features=F, layout=feats, module=mod, rf=rfm,
                s14=s14, supports=sup, post=post, path=path, forbidden=forb, closure=clos, inventory=inv, seal_closure=closure, screws=scr,
                vent_land=vent_land, window_land=win_land, aperture_feasible=feas, conditional=cond, cover=cover, lra=lra,
                lra_rescreen=resc, asm=asm, r_case=rcase, protrusions=protr, split_bond=split_bond)


# --------------------------------------------------------------------------------------------
# Scope (H20 / R1-S12): changed paths, immutables, KiCad / interfaces, brief pin, allow-list extension
# --------------------------------------------------------------------------------------------
G4_IMMUTABLE = sorted(set(g4.G3_IMMUTABLE) | {
    'design/mechanical/G4_BRIEF.md', 'design/mechanical/inputs/g4_case_sealing.json', 'design/mechanical/tools/g4_case_sealing.py',
    'design/mechanical/architecture.md', 'design/mechanical/architecture.json', 'design/mechanical/README.md',
    'design/mechanical/tools/arch_diagrams.py'} | {'design/mechanical/generated/' + n for n in g4.OUT})
KICAD_PATHS = ('*.kicad_pcb', '*.kicad_sch', '*.kicad_pro', '*.kicad_prl', 'design/interfaces', 'design/placement', 'rear_sensor', 'libraries')
G1_IMMUTABLE = ('design/mechanical/inputs/stack_parameters.json', 'design/mechanical/inputs/package_heights.json',
                'design/mechanical/inputs/g1_scenarios.json', 'design/mechanical/tools/mech_model.py', 'design/mechanical/tools/mech_model_spec.md',
                'design/mechanical/tools/g1_scenarios.py', 'design/mechanical/generated/zstack.md', 'design/mechanical/generated/zstack_section.svg',
                'design/mechanical/generated/main_height_map.md', 'design/mechanical/generated/main_height_map.svg',
                'design/mechanical/generated/g1_scenarios.json', 'design/mechanical/generated/g1_scenarios.md')  # G4_BRIEF section 11


def changed_paths():
    diff = [p for p in git('diff', '--name-only', G4_BASELINE).stdout.split() if p]
    untracked = [p for p in git('ls-files', '--others', '--exclude-standard').stdout.split() if p]
    return sorted(set(diff) | set(untracked))


def r1_scope(r1in, changed=None):
    changed = changed_paths() if changed is None else changed
    kicad_hit = [p for p in changed if p.endswith(('.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_prl'))
                 or p.startswith(('design/interfaces/', 'design/placement/', 'rear_sensor/', 'libraries/'))]
    res = dict(
        changed_subset_of_R1_FILES=all(p in R1_FILES for p in changed),
        kicad_interfaces_placement_unchanged=not kicad_hit and git('diff', '--quiet', G4_BASELINE, '--', *KICAD_PATHS).returncode == 0,
        g1_g4_immutables_unchanged=git('diff', '--quiet', G4_BASELINE, '--', *G4_IMMUTABLE).returncode == 0
        and not [p for p in changed if p in G4_IMMUTABLE],
        brief_unchanged_since_contract=git('diff', '--quiet', r1in['baselines']['r1_contract_commit'], '--', BRIEF).returncode == 0,
        brief_pin=sha_file(ROOT / BRIEF) == r1in['source_sha256'][BRIEF],
        allowed_extension_exact=(set(g4.ALLOWED_CHANGES) - set(G4_ORIGINAL_ALLOWED)) == set(R1_FILES) or
        set(g4.ALLOWED_CHANGES) == set(G4_ORIGINAL_ALLOWED),
        g1_baseline_files_unchanged=git('diff', '--quiet', r1in['baselines']['g1'], '--', *G1_IMMUTABLE).returncode == 0)
    pins = []
    for rel, want in sorted(r1in['source_sha256'].items()):
        got = sha_file(ROOT / rel)
        pins.append(dict(path=rel, match=got == want))
    res['source_pins_match'] = all(p['match'] for p in pins)
    return dict(checks=res, changed=changed, kicad_hits=kicad_hit, pins=pins, pass_=all(res.values()))


# --------------------------------------------------------------------------------------------
# Hard checks R1-H01 .. R1-H20 (S6 state model)
# --------------------------------------------------------------------------------------------
HC_TITLES = {
    'R1-H01': ('G2-REVA / G2-REVA-HI reproduced, total Z delta 0.000; every R1 feature fits the REAR-periphery band', 'exact / linear worst', 'PROJECT-DERIVED LIMIT', 'L-STR / L-SEAL / L-CHG'),
    'R1-H02': ('D_case_body <= 51.00; only the five button bosses protrude, <= +1.0 mm incl. boot and tolerance', 'linear worst', 'OWNER REQUIREMENT', 'L-RAD / L-BTN'),
    'R1-H03': ('LEGACY numbers and every G4-literal result at 00e77cb reproduced exactly', 'exact', 'PROJECT-DERIVED LIMIT', 'cross-cutting'),
    'R1-H04': ('H05-GEOM: straight, XF, XB, XC, wall side, wall dielectric, main-case, t_allow >= 0 with azimuth-resolved wall', 'linear worst', 'PROJECT-DERIVED LIMIT', 'L-RAD'),
    'R1-H05': ('H05-LRA-COUPLED (XL lateral and Z) - separate; part of the L-LRA verdict only', 'linear worst', 'PROJECT-DERIVED LIMIT', 'L-LRA'),
    'R1-H06': ('Cover / bezel / land regression (G4 H06-H09)', 'linear worst', 'PROVISIONAL PLANNING LIMIT', 'L-WIN / regression'),
    'R1-H07': ('W1 @ 0.45 mm minimum: stress and deflection screens, rib fit, bond land, no rib-to-optics load', 'G1 conservative', 'PROVISIONAL PLANNING LIMIT', 'L-WIN'),
    'R1-H08': ('Pressure partition sums; no forbidden branch (battery, REAR PCB, G3 support lands, carrier lower web); PCB load 0.000 N', 'exact', 'PROJECT-DERIVED LIMIT', 'L-STR'),
    'R1-H09': ('Stiffened caseback: stress <= sigma_allow(min); deflection <= min(c_cb_rear min, window standoff) at p max (Screen B governs, Screen A reported)', 'linear worst', 'PROVISIONAL PLANNING LIMIT', 'L-STR'),
    'R1-H10': ('Perimeter bearing, screw shear / pull-out and split-plate bond-shear thresholds with supplier zero-margin', 'linear worst', 'PROVISIONAL PLANNING LIMIT', 'L-STR'),
    'R1-H11': ('Main seal gland compression and fill inside window at +/-0.05 mm; seal path closed; no impossible gland remains', 'linear worst / exact', 'PROVISIONAL PLANNING LIMIT', 'L-SEAL'),
    'R1-H12': ('Buttons per SW: guide stack under I-SUM and I-MAX, core, boss wall, rim land, stroke >= c_switch, tangential fit, material constraints', 'linear worst', 'PROVISIONAL PLANNING LIMIT', 'L-BTN'),
    'R1-H13': ('Every aperture has exactly one primary seal with a feasible geometry class', 'exact', 'PROJECT-DERIVED LIMIT', 'L-SEAL'),
    'R1-H14': ('Charger: block inside wedge and outside WIFI_RAD; land per C-R1-01 with overshoot <= caps; corridors clear in plan and Z', 'linear worst', 'PROVISIONAL PLANNING LIMIT', 'L-CHG'),
    'R1-H15': ('H17 zero conductive / wiring intrusion in radiators (ribs, split plate, screws, plungers, charger); H18 MAG_CLEAR', 'exact', 'PROJECT-DERIVED LIMIT', 'cross-cutting'),
    'R1-H16': ('H19: S14 outline, pod, supports, tail corridors, U6 island untouched; no G3 support-land enlargement claimed', 'linear worst', 'PROJECT-DERIVED LIMIT', 'cross-cutting'),
    'R1-H17': ('Assembly sequence (C-R1-06) executable, access direction per operation, rear-insertion collision-free', 'linear worst', 'PROJECT-DERIVED LIMIT', 'L-ASM'),
    'R1-H18': ('>= 4 case / caseback supports incl. W/NW outside the pack (G4 H24)', 'exact', 'PROJECT-DERIVED LIMIT', 'L-STR'),
    'R1-H19': ('LRA lane: PASS only with an authored / supplied class fitting a pose at the current allocation; else quantified maximum envelope and deficit', 'linear worst', 'PROVISIONAL PLANNING LIMIT', 'L-LRA'),
    'R1-H20': ('No KiCad / interface / immutable-file change; historical reproduction of section 5.1', 'exact', 'PROJECT-DERIVED LIMIT', 'cross-cutting'),
}
G4_LITERAL_MAP = {'R1-H01': 'H01', 'R1-H02': 'H03', 'R1-H03': 'H04', 'R1-H04': 'H05', 'R1-H05': 'H05', 'R1-H06': 'H06', 'R1-H07': 'H12',
                  'R1-H08': 'H10', 'R1-H09': 'H13', 'R1-H10': 'H13', 'R1-H11': 'H15', 'R1-H12': 'H21', 'R1-H13': 'H14',
                  'R1-H14': 'H20', 'R1-H15': 'H17', 'R1-H16': 'H19', 'R1-H17': 'H23', 'R1-H18': 'H24', 'R1-H19': 'H22', 'R1-H20': 'H25'}


def state_of(executed, phys, complete, gates, lra_isolated=False, blocked=None):
    if not executed:
        return 'BLOCKED' if blocked else 'NOT_EVALUATED'
    if phys is True and complete and not gates:
        return 'PASS'
    if phys is False:
        return 'GATED' if (lra_isolated and gates) else 'FAIL'
    if phys is True:
        return 'GATED'
    return 'GATED' if gates else 'BLOCKED'


# Checks with a computable numeric boundary (mm / MPa / ratio margins): GATED or FAIL records of these must carry it (R2-6)
NUMERIC_CHECKS = ('R1-H01', 'R1-H02', 'R1-H04', 'R1-H05', 'R1-H06', 'R1-H07', 'R1-H08', 'R1-H09', 'R1-H10', 'R1-H11', 'R1-H12',
                  'R1-H14', 'R1-H17', 'R1-H18', 'R1-H19')


# R3-5: the ONLY checks the contract isolates to the L-LRA lane (G4_R1_BRIEF R1-H05 "part of the L-LRA verdict only" and R1-H19
# "LRA lane"); immutable; never inferred from serialized data. The validator enforces its own copy with the expected semantics.
LRA_ISOLATION_ALLOWED = frozenset(('R1-H05', 'R1-H19'))


def hc(cid, executed, phys, margin, units, gov, szm, gates, missing, g4lit, lra_isolated=False, blocked=None, threshold=None, credits=(),
       threshold_value=None, required_delta=None, threshold_units=None, categorical_evidence=None, required_delta_units=None, typed=None):
    """S6 record. evidence_complete is derived from the explicit list of missing evidence items; threshold_value /
    required_delta / supplier_zero_margin carry the numeric boundary (R2-6); a categorical gate carries categorical_evidence
    instead of a dummy number (R3-6). L-LRA isolation only for LRA_ISOLATION_ALLOWED (R3-5). R4-6 / R4-8: margin / units,
    threshold_value / threshold_units and required_delta / required_delta_units are separate typed pairs (required_delta defaults
    to the margin units); `typed` carries individually typed terms where a check has unlike quantities (R1-H11, R1-H14)."""
    if lra_isolated and cid not in LRA_ISOLATION_ALLOWED:
        raise StudyError('%s: L-LRA isolation is reserved for %s (R3-5); a physical failure of this check cannot be isolated' % (
            cid, ', '.join(sorted(LRA_ISOLATION_ALLOWED))))
    title, ev_type, ev_class, lane = HC_TITLES[cid]
    complete = not missing
    if margin is not None and margin < -EPS and phys:
        raise StudyError('%s: physical PASS with negative margin %.6f' % (cid, margin))
    if typed is not None and (typed['governing']['value'] != margin or typed['governing']['units'] != units or typed['physical_pass'] != phys):
        raise StudyError('%s: check margin / units / physical pass differ from the typed governing term' % cid)
    return dict(id=cid, title=title, owning_lane=lane, evaluation_type=ev_type, evidence_class=ev_class, check_executed=bool(executed),
                physical_pass=phys, margin=margin, units=units, governing_terms=gov, supplier_zero_margin=szm,
                gate_raised=bool(gates), gate_ids=list(gates), evidence_complete=bool(complete), missing_evidence=list(missing),
                study_status=state_of(executed, phys, complete, gates, lra_isolated, blocked), g4_literal=g4lit,
                isolation='L-LRA' if lra_isolated else None, numeric_boundary=cid in NUMERIC_CHECKS,
                threshold=threshold, threshold_value=threshold_value, threshold_units=threshold_units, required_delta=required_delta,
                required_delta_units=(required_delta_units or units) if required_delta is not None else None, typed=typed,
                categorical_evidence=categorical_evidence, credits=list(credits), blocked_reason=blocked)


# R4-8: individually typed main-seal terms; the key set is closed (an unknown margin key is a STOP, never an untyped number)
H11_TERM_TYPES = {
    'gland_compression_min': ('O-ring compression ratio minus the static-window minimum (adverse cs -0.05 mm, groove depth tolerance)',
                              'dimensionless'),
    'gland_compression_max': ('static-window maximum minus the O-ring compression ratio (adverse cs +0.05 mm)', 'dimensionless'),
    'gland_fill': ('gland fill-ratio maximum minus the fill ratio (adverse cs +0.05 mm)', 'dimensionless'),
    'face_annulus': ('midcase rear-face annulus minus the face-gland annulus', 'mm'),
    'flange_groove_residual': ('caseback flange thickness minus groove depth, tolerances and residual floor', 'mm'),
    'bond_land_annulus': ('midcase rear-face annulus minus the adhesive bond land', 'mm'),
    'spigot_rear_periphery_z': ('REAR-periphery Z residual with the radial spigot (G4 H01 specification)', 'mm'),
    'continuous_bore': ('continuous radial-spigot bore (through-rear-face arc break)', 'mm'),
}
H11_UNITS_OF = {k: v[1] for k, v in H11_TERM_TYPES.items()}
H11_ROLES = dict(face='face O-ring (brief 6.3 baseline)', adhesive='adhesive ring (non-serviceable; comparison)',
                 radial='radial spigot O-ring (regression)')
H11_UNITS_ORDER = ('dimensionless', 'mm')


def typed_minima(margins):
    """Minimum main-seal margin per units group (H11_UNITS_ORDER), never across units (R4-8); None for an absent group."""
    return [min([v for k, v in margins.items() if H11_TERM_TYPES[k][1] == u], default=None) for u in H11_UNITS_ORDER]


def h11_typed(seal, path_closed):
    """R4-8 / R5: R1-H11 as individually typed predicates derived from the seal ROW POPULATION (never a representative row). Per
    topology, one term per typed predicate k: value = the population reduction of that predicate (max over the term population of m_k:
    fully feasible rows if any, else every authorized row; SEAL_REDUCTION_RULES) with its units, threshold (>= 0), pass (some row of the
    population meets k) and delta; plus the boolean joint term (one authorized row meets every predicate). Topology feasibility = the
    conjunction of its terms = any(r.pass_all). Check predicates (booleans): seal path closed; some carried topology closes;
    physical_pass = their conjunction. No minimum across units: per-units governing terms only (most adverse failing numeric term of the
    failing topologies; when a topology closes, the tightest term of the closing topologies); the check-level margin / units are those
    of the dimensionless gland-window group (the quantity the R1-H11 title names first) when present, else mm."""
    tops = {}
    for t in SEAL_ORDER:
        o = seal['topologies'][t]
        n_pop = len(o['fully_feasible_rows'] if o['term_population'] == 'fully_feasible_rows' else o['evaluated_rows'])
        terms = []
        for k, red in sorted(o['term_reductions'].items()):
            q, u = H11_TERM_TYPES[k] if k in H11_TERM_TYPES else (None, None)
            if u is None or red['units'] != u:
                raise StudyError('STOP: untyped / mistyped main-seal margin %s (R4-8)' % k)
            v = red['value']
            terms.append(dict(id='H11-%s-%s' % (t.upper(), k), topology=t, quantity=q, value=v, units=u, threshold=0.0,
                              threshold_rule='typed margin >= 0', reduction='max over %s (%d rows)' % (o['term_population'], n_pop),
                              rows_attaining=red['rows_attaining'], rows_meeting=o['predicate_feasible_rows'][k], pass_=v >= -EPS,
                              delta=max(0.0, -v)))
            if terms[-1]['pass_'] != bool(o['predicate_feasible_rows'][k]):
                raise StudyError('STOP: %s %s population reduction disagrees with its predicate-feasible row set' % (t, k))
        terms.append(dict(id='H11-%s-joint_row' % t.upper(), topology=t, quantity='one authorized cross-section row meets every typed predicate '
                          '(any r.pass_all)', value=bool(o['fully_feasible_rows']), units='bool', threshold=True, threshold_rule='true',
                          reduction='any over evaluated_rows (%d rows)' % len(o['evaluated_rows']), rows_attaining=list(o['fully_feasible_rows']),
                          rows_meeting=list(o['fully_feasible_rows']), pass_=bool(o['fully_feasible_rows']), delta=None))
        feas = all(x['pass_'] for x in terms)
        if feas != o['feasible'] or feas != (t in seal['feasible_topologies']):
            raise StudyError('STOP: %s typed-term conjunction differs from any(r.pass_all) over its authorized rows' % t)
        tops[t] = dict(role=H11_ROLES[t], serviceable=o['serviceable'], term_population=o['term_population'], evaluated_rows=o['evaluated_rows'],
                       fully_feasible_rows=o['fully_feasible_rows'], terms=terms, feasible=feas)
    preds = [dict(id='H11-SEAL-PATH-CLOSED', quantity='seal path closure (G4 seal_closure graph)', value=bool(path_closed), units='bool',
                  pass_=bool(path_closed)),
             dict(id='H11-SOME-TOPOLOGY-CLOSES', quantity='some carried main-seal topology closes every typed predicate on the cs grid',
                  value=bool(seal['feasible_topologies']), units='bool', pass_=bool(seal['feasible_topologies']))]
    phys = all(p['pass_'] for p in preds)
    closing = [t for t in SEAL_ORDER if tops[t]['feasible']]
    numeric = lambda ts, failing: [x for t in ts for x in tops[t]['terms'] if x['units'] != 'bool' and (not failing or not x['pass_'])]
    pool = numeric(closing, False) if closing else (numeric(SEAL_ORDER, True) or numeric(SEAL_ORDER, False))
    by_units = {}
    for x in pool:
        g = by_units.get(x['units'])
        if g is None or (x['value'], x['id']) < (g['value'], g['term_id']):
            by_units[x['units']] = dict(term_id=x['id'], value=x['value'], units=x['units'], topology=x['topology'], quantity=x['quantity'])
    gu = next(u for u in H11_UNITS_ORDER if u in by_units)
    return dict(topologies=tops, check_predicates=preds, physical_pass=phys, governing_by_units=by_units,
                governing=dict(by_units[gu]), closed_topology=seal['closed_topology'], coupled_topology=seal['coupled']['topology'],
                rule='physical_pass = conjunction of the check predicates (seal path closed AND some carried topology closes); each typed '
                     'term is a population reduction of one predicate (max over the term population; SEAL_REDUCTION_RULES); topology '
                     'feasibility = conjunction of its terms incl. the joint-row term = any(r.pass_all); no cross-unit ranking: governing '
                     'terms per units group (most adverse failing numeric term of the failing topologies, or the tightest term of the '
                     'closing topologies); the check-level margin / units are the dimensionless gland-window group\'s (the R1-H11 title '
                     'quantity) when present, else mm')


def g4_lit(cx, cid, cand_id):
    gid = 'G4-C' if cand_id == 'G4-C1' else cand_id
    c = next(c for c in cx.g4_res['candidates'] if c['id'] == gid)
    h = c['hard_checks'][G4_LITERAL_MAP[cid]]
    return dict(g4_candidate=gid, g4_check=G4_LITERAL_MAP[cid], pass_=h['pass'], failing=h['failing'],
                note='G4-C (P2) is the literal reference for G4-C1' if cand_id == 'G4-C1' else None)


def zero_terms(spec_):
    r = g4.run_check(spec_, full=True)
    return [dict(term=z['term'], value=z['value']) for z in r['supplier_zero_margin']]


def hard_checks(cx, E, in_proc, scope):
    st, zm = cx.st, cx.zm
    cid = E['id']
    sp = cx.ce[cid].sp
    row, strl, btn, seal = E['row'], E['strl'], E['btn'], E['seal']
    H = {}
    ch0 = E['chg']
    miss = {h: [] for h in HC_TITLES}
    miss['R1-H01'] = ['charger contact-block height (SR-CHG-MECH)']
    miss['R1-H10'] = ['screw pull-out / shear capacity and seal preload (supplier)'] + \
        (['split-plate bond shear strength (SR-ADHESIVE)'] if E.get('split_bond') else [])
    miss['R1-H14'] = ['charger contact-block height and contact data (SR-CHG-MECH)'] if ch0['pass_'] else []
    miss['R1-H19'] = ['supplied LRA class rejected: %s' % v['id'] for v in E['lra']['supplied'] if not v['accepted']]
    # R1-H01 Z
    cbf = [f for f in E['features'] if f['kind'] in ('caseback rib', 'charger land', 'caseback seal flange', 'caseback centre plate', 'charger contacts')]
    z_below = max([0.0] + [-f['z_lo_adv'] for f in cbf])
    z_above = max([0.0] + [f['z_hi_adv'] - zm['z_band_lo_adv'] for f in cbf if f['kind'] != 'caseback seal flange'])
    per = g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=strl['selected']['t_out']), 0.0), full=False)
    rib_m = (zm['z_band_lo_adv'] - strl['limits']['rib_top_adv']) if strl['limits']['rib_top_adv'] is not None else None
    m01 = min([per, -z_below, -z_above] + ([rib_m] if rib_m is not None else []))
    z_ok = all(v['match'] for v in st.z.values())
    H['R1-H01'] = hc('R1-H01', True, z_ok and m01 >= -EPS, m01, 'mm',
                     dict(rear_periphery_plate_mm=per, rib_band_mm=rib_m, protrusion_below_Z0_mm=z_below, above_band_mm=z_above,
                          g2_reproduced=z_ok, total_z_delta_mm=z_below + z_above),
                     [dict(term='charger_block_height_max_mm', value=zm['z_band_lo_adv'])], ['SR-CHG-MECH'], miss['R1-H01'],
                     g4_lit(cx, 'R1-H01', cid), threshold='charger block height above Z=0 <= %.3f mm fits the REAR-periphery allocation (allocation-fit '
                                                          'semantics, SR-CHG-MECH; equality allowed). At that height the block has a zero Z gap to the '
                                                          'CHG_ROUTE / CHG_LINK band; it is plan-separated from them, so the common 3-D predicate holds '
                                                          '(R4-7); only the conservative block-AND-Z screen needs < %.3f mm strictly (R1-H14 '
                                                          'diagnostic, not contract text)' % (zm['z_band_lo_adv'], zm['z_band_lo_adv']),
                     threshold_value=zm['z_band_lo_adv'], threshold_units='mm')
    # R1-H02 envelope / bosses: the selected button topology's protrusion (boot included); with no selected topology
    # only the boss envelope exists in the design and the T2-F boot protrusion is reported under R1-H12.
    if btn['closed']:
        bossm = min(btn['switches'][s]['best'][btn['binding_interpretation']]['margins']['protrusion'] for s in btn['switches'])
    else:
        bossm = min(btn['switches'][s]['T2']['T2-R'][btn['binding_interpretation']]['margins']['protrusion'] for s in btn['switches'])
    m02 = min(row['margins']['H03-OD'], bossm)
    H['R1-H02'] = hc('R1-H02', True, m02 >= -EPS and not E['protrusions'], m02, 'mm',
                     dict(od_margin_mm=row['margins']['H03-OD'], boss_protrusion_margin_mm=bossm, D_mm=E['D'], unpermitted=E['protrusions']),
                     [], [], miss['R1-H02'], g4_lit(cx, 'R1-H02', cid))
    # R1-H03 historical reproduction
    leg = st.legacy['pass_']
    H['R1-H03'] = hc('R1-H03', True, in_proc['pass_'] and leg, 0.0, 'exact',
                     dict(legacy_rows_match=leg, g4_validate_failures=in_proc['fails'], g4_selftests='%d/%d' % (in_proc['caught'], in_proc['tests']),
                          extension=in_proc['extension']), [], [], miss['R1-H03'], g4_lit(cx, 'R1-H03', cid))
    # R1-H04 H05-GEOM
    geom_terms = {k: row['margins'][k] for k in row['h05_geom_terms']}
    szm04 = zero_terms(sp.edge(dict(D=E['D'], tw=E['tw'], rcin=row['rcin'], tcw=row['tcw']), 'XF-J1501'))
    H['R1-H04'] = hc('R1-H04', True, row['h05_geom_pass'], row['h05_geom_min'], 'mm',
                     dict(margins=geom_terms, wall_screens_MPa=row['wall_screens_MPa'], arcs=[dict((k, a[k]) for k in ('reservation', 't_arc_mm', 'floor_mm', 'z_extent', 'local_material')) for a in row['arcs']]),
                     szm04, ['SR-FPC-MECH', 'SR-BATT-PCM', 'SR-CHG-MECH'] if row['h05_geom_pass'] else ['OD-G4-ENVELOPE (D)'], miss['R1-H04'],
                     g4_lit(cx, 'R1-H04', cid))
    # R1-H05 H05-LRA-COUPLED (isolated to L-LRA)
    lm = min(row['lra_coupled'].values())
    szm05 = zero_terms(sp.edge_z(dict(t_land=cx.ce[cid].land['t_land']), 'XL-LRA'))
    H['R1-H05'] = hc('R1-H05', True, lm >= -EPS, lm, 'mm', dict(row['lra_coupled']), szm05,
                     ['OD-G4-LRA-ARCH'] if lm < -EPS else ['SR-LRA'], miss['R1-H05'], g4_lit(cx, 'R1-H05', cid), lra_isolated=True,
                     required_delta=max(0.0, -lm), threshold='H05-LRA-COUPLED terms >= 0 (XL-LRA run height under the display-land ceiling)')
    # R1-H06 cover regression
    cv = E['cover']
    m06 = min(cv['fit']['linear_worst'], cv['ledge']['linear_worst'], cv['u4']['linear_worst'], cv['body']['linear_worst'])
    p06 = m06 >= -EPS and cv['plate']['pass'] and cv['proud']['pass_']
    H['R1-H06'] = hc('R1-H06', True, p06, m06, 'mm', dict(x25=cv['fit']['linear_worst'], ledge=cv['ledge']['linear_worst'], u4=cv['u4']['linear_worst'],
                                                          body_height=cv['body']['linear_worst'], cover_plate=cv['plate']['pass'], cover_proud=cv['proud']['pass_']),
                     cv['fit']['supplier_zero_margin'], ['SR-COVER-LENS', 'SR-DISPLAY-LAND'] if p06 else [], miss['R1-H06'], g4_lit(cx, 'R1-H06', cid),
                     threshold='supplier zero-margin values of the X25 cover fit (G4 H06 spec)')
    # R1-H07 window
    w = E['win']
    m07 = min(w['margins']['rib_fit_adverse_mm'], w['margins']['window_bond_land_mm'], w['margins']['min_deflection_mm'])
    szm07 = [dict(term='sigma_allow_required_MPa_' + k, value=w['materials'][k]['sigma_ss_MPa']) for k in cx.P['V18_window']['materials']] + \
        [dict(term='rib_width_incl_tol_max_mm', value=w['min_inter_cell_web_mm'])]
    H['R1-H07'] = hc('R1-H07', True, w['physical_pass'], m07, 'mm', dict(w['margins'], materials={k: v['planning_screen'] for k, v in w['materials'].items()}),
                     szm07, ['SR-WINDOW', 'MG-WINDOW-XTALK'], miss['R1-H07'], g4_lit(cx, 'R1-H07', cid),
                     threshold='supplier allowable >= the W1 planning stress of each carried material; rib width + tol <= inter-cell web')
    # R1-H08 partition / forbidden branches
    post = E['post']
    R_bear = row['R_side'] + sp.pc_env['radius_mm']
    tot_ok = g4.pressure_domains_valid(post['domains'], post['total_area_mm2']) and abs(post['total_N'] - cx.p * math.pi * R_bear ** 2) < 1e-6
    fb = E['forbidden']
    m08 = min([v['margin_mm'] for v in fb['branches'].values() if v['margin_mm'] is not None] or [0.0])
    H['R1-H08'] = hc('R1-H08', True, tot_ok and fb['all_zero'], m08, 'mm',
                     dict(total_N=post['total_N'], domains={d['id']: d['force_N'] for d in post['domains']}, branches=fb['branches'],
                          feature_contacts=fb['feature_contacts'], partition_valid=tot_ok, bearing_radius_mm=R_bear),
                     [], [] if (tot_ok and fb['all_zero']) else ['R1-S07', 'FEA-1', 'FEA-2'], miss['R1-H08'], g4_lit(cx, 'R1-H08', cid),
                     required_delta=max(0.0, -m08), threshold='zero load on battery / REAR PCB / G3 support lands / carrier lower web')
    # R1-H09 structure
    sA, sB = strl['screen_A'], strl['screen_B']
    m09 = min(sB['stress_margin_MPa'], sA['stress_margin_MPa'])
    th = strl['thresholds']
    mat = strl['materials']['outer']['id']
    H['R1-H09'] = hc('R1-H09', True, strl['physical_pass'], m09, 'MPa',
                     dict(screen_B=dict(sigma=sB['sigma_governing_MPa'], w=sB['w_max_mm'], deflection_margin=sB['deflection_margin_mm'], region=sB['governing_region']),
                          screen_A=dict(sigma=sA['sigma_governing_MPa'], w=sA['w_max_mm'], deflection_margin=sA['deflection_margin_mm']),
                          selected=strl['selected'], geometry_ok=strl['geometry_ok'],
                          design_point_bound=dict((k, E['structure_design_point']['record'][k]) for k in ('method', 'bound_mm', 'limit_mm', 'pass_'))),
                     [dict(term='required_uniform_nominal_thickness_mm', value=th[mat]['required_uniform_nominal_thickness_mm'])],
                     [] if strl['physical_pass'] else ['R1-S07', 'OD-G4-MATERIAL', 'OD-G4-STACK', 'FEA-1', 'FEA-2'], miss['R1-H09'], g4_lit(cx, 'R1-H09', cid),
                     threshold='uniform isotropic caseback >= %.3f mm nominal (%s) vs t_in <= %.2f mm by the pod residual' %
                     (th[mat]['required_uniform_nominal_thickness_mm'] or -1, mat, strl['selected']['t_in']),
                     threshold_value=th[mat]['required_uniform_nominal_thickness_mm'], threshold_units='mm', required_delta=max(0.0, -m09))
    # R1-H10 bearing / screws / split bond
    comp = post['modes']['compression']
    gates10 = ['CASE-SIDE-LOAD-PATH', 'FEA-3'] + (['SR-ADHESIVE'] if E['split_bond'] else [])
    szm10 = [dict(term='bearing_planning_allowable_MPa', value=comp['stress_MPa'])]
    if E['split_bond']:
        szm10.append(dict(term='split_bond_shear_strength_MPa', value=E['split_bond']['required_bond_shear_MPa']))
    H['R1-H10'] = hc('R1-H10', True, comp['margin_MPa'] >= -EPS, comp['margin_MPa'], 'MPa',
                     dict(bearing=comp, screws='no hydrostatic load assigned (g4 load path: CASEBACK -> PERIMETER_BEARING); preload >= seal reaction is a supplier threshold',
                          split_bond=E['split_bond']), szm10, gates10, miss['R1-H10'], g4_lit(cx, 'R1-H10', cid),
                     categorical_evidence=dict(numeric=['bearing planning allowable'] + (['split-plate bond shear'] if E['split_bond'] else []),
                                               not_computable=['screw pull-out / shear capacity (no screw supplier data; no hydrostatic screw load '
                                                               'assigned by the accepted G4 load path)',
                                                               'seal preload >= gasket reaction (no gasket compression-force data)'],
                                               gate='supplier evidence (CASE-SIDE-LOAD-PATH / FEA-3); no number authored for them'))
    # R1-H11 main seal
    t11 = h11_typed(seal, E['seal_closure']['closed'])
    g11 = t11['governing']
    p11 = t11['physical_pass']
    if p11 != (seal['physical_pass'] and E['seal_closure']['closed']):
        raise StudyError('STOP: typed R1-H11 conjunction differs from the main-seal / seal-path result')
    H['R1-H11'] = hc('R1-H11', True, p11, g11['value'], g11['units'],
                     dict(closed_topology=seal['closed_topology'], coupled=seal['coupled'], governing_term=g11['term_id'],
                          governing_by_units=t11['governing_by_units'], topology_feasible={t: o['feasible'] for t, o in t11['topologies'].items()},
                          fully_feasible_rows={t: o['fully_feasible_rows'] for t, o in seal['topologies'].items()},
                          thresholds=seal['thresholds'], annulus=seal['annulus'], seal_path_closed=E['seal_closure']['closed']),
                     [dict(term='required_tw_face_mm', value=seal['thresholds']['face']['required_tw_mm']),
                      dict(term='required_tw_adhesive_mm', value=seal['thresholds']['adhesive']['required_tw_mm']),
                      dict(term='radial_min_feasible_cs_mm', value=seal['thresholds']['radial']['smallest_feasible_gland_cs'])],
                     ['ATM-Q1'] if p11 else ['R1-S06', 'OD-G4-ENVELOPE (D)', 'OD-G4-STACK', 'serviceability (adhesive)'], miss['R1-H11'], g4_lit(cx, 'R1-H11', cid),
                     threshold='typed predicates per topology (face / adhesive / radial; R4-8); owner thresholds: adhesive bulk wall >= %s mm, face '
                               'bulk wall >= %s mm, radial cross-section >= %s mm with REAR-periphery Z %s mm' % (
                                   fs(seal['thresholds']['adhesive']['required_tw_mm']), fs(seal['thresholds']['face']['required_tw_mm']),
                                   fs(seal['thresholds']['radial']['smallest_feasible_gland_cs']),
                                   fs((seal['thresholds']['radial']['at_that_cs'] or {}).get('spigot_rear_periphery_z'))),
                     threshold_value=seal['thresholds']['adhesive']['required_tw_mm'], threshold_units='mm (bulk wall tw: smallest owner threshold carrying any main seal, adhesive)',
                     required_delta=max(0.0, -g11['value']),
                     required_delta_units='%s (deficit of the governing typed term %s)' % (g11['units'], g11['term_id']),
                     typed=t11)
    # R1-H12 buttons
    bm = min(btn['switches'][s]['best'][btn['binding_interpretation']]['min_margin'] for s in btn['switches'])
    H['R1-H12'] = hc('R1-H12', True, btn['closed'], bm, 'mm',
                     dict(disposition=btn['disposition'], I_SUM={s: r['best']['I-SUM']['min_margin'] for s, r in btn['switches'].items()},
                          I_MAX={s: r['best']['I-MAX']['min_margin'] for s, r in btn['switches'].items()},
                          T3={s: (r['T3'] or {}).get('status') for s, r in btn['switches'].items()}),
                     [dict(term='T2-R_required_D_mm', value=max(r['thresholds']['T2-R']['required_D_mm'] for r in btn['switches'].values()))],
                     ['SR-BUTTONS'] if btn['closed'] else ['R1-S03', 'SR-BUTTONS', 'OD-G4-ENVELOPE (boss / D)'], miss['R1-H12'], g4_lit(cx, 'R1-H12', cid),
                     threshold_value=max(r['thresholds']['T2-R']['required_D_mm'] for r in btn['switches'].values()), threshold_units='mm (T2-R zero-margin nominal D)',
                     required_delta=max(0.0, -bm))
    # R1-H13 apertures
    feas = E['aperture_feasible']
    p13 = E['seal_closure']['closed'] and all(feas.values())
    H['R1-H13'] = hc('R1-H13', True, p13, None, 'exact', dict(apertures=feas, closure=E['seal_closure']), [],
                     ['ATM-Q1', 'ATM-Q2', 'ATM-Q3', 'ATM-Q4'] if p13 else ['R1-S06'], miss['R1-H13'], g4_lit(cx, 'R1-H13', cid),
                     categorical_evidence=dict(apertures_infeasible=sorted(k for k, v in feas.items() if not v),
                                               seal_path_closed=E['seal_closure']['closed']))
    # R1-H14 charger (R3-1 / R3-9): physical pass = the literal C-R1-01 closure at the design point against the complete
    # same-point neighbour set; governing scalar = minimum mm clearance over every comparable term; the radial / plan
    # prerequisite r_lim is the numeric threshold of that prerequisite only (it never closes the charger by itself)
    ch = E['chg']
    lit = E['chg_literal']
    gv = ch['governing']
    pp = lit['plan_prerequisite']
    sw_ = lit['strict_wedge_supplier_path']
    H['R1-H14'] = hc('R1-H14', True, ch['pass_'], gv['governing']['value'], 'mm',
                     dict(categories=dict(ch['categories']), governing_term=gv['governing']['term_id'], governing_category=gv['governing']['category'],
                          azimuth_cap_margin_deg=gv['azimuth_cap_margin_deg'], typed_terms='see typed (R4-6)', attribution_note=gv['attribution_note'],
                          pose=dict((k, ch['pose'][k]) for k in ('orientation', 'r_centre', 'az_centre', 'land', 'block_mm', 'land_side_overshoot_mm', 'land_az')),
                          flange=ch['flange_margins'], coupled_seal_topology=seal['coupled']['topology'] + ('' if seal['coupled']['closed'] else ' (fallback, not closed)'),
                          coupled_seal_population=seal['coupled']['population'], seal_flange_rows=ch['seal_flange_rows']['reduction'],
                          radial_prerequisite=dict((k, lit['radial_prerequisite'][k]) for k in ('r_lim_required_mm', 'pose', 'deficit_mm')),
                          plan_prerequisite=dict((k, pp[k]) for k in ('r_lim_required_mm', 'pose', 'deficit_mm', 'required_D_at_design_wall_mm')),
                          land_v_z=dict((k, lit['z_prerequisite']['land_unsatisfiability'][k]) for k in ('h_land_mm', 'unsatisfiable', 'unsatisfiable_items',
                                                                                                          'rule', 'scope')),
                          block_and_z_diagnostic=dict((k, lit['block_and_z_diagnostic'][k]) for k in ('label', 'pass_', 'v_item_min_z_gap_mm',
                                                                                                    'route_z_gaps_mm', 'block_3d_clear_of_routes')),
                          strict_wedge_supplier_path=dict((k, sw_[k]) for k in ('width_mm', 'contained_in_wedge', 'in_land_range', 'plan', 'neighbours', 'z',
                                                                                'complete', 'complete_v_z_waived', 'failing_terms_by_category')),
                          first_D=dict((k, v) for k, v in lit['first_D'].items() if k != 'rule')),
                     [dict(term='strict_wedge_land_mm (supplier zero-margin threshold, land < value strictly; not credited)', value=sw_['width_mm']),
                      dict(term='block_height_max_mm (allocation; the conservative block-AND-Z screen needs < value strictly)', value=zm['z_band_lo_adv']),
                      dict(term='caseback_r_lim_required_mm (radial / plan prerequisite only)', value=pp['r_lim_required_mm'])],
                     ['SR-CHG-MECH', 'ATM-Q3'] if ch['pass_'] else ['R1-S04', 'Q-R1-CHARGER'], miss['R1-H14'], g4_lit(cx, 'R1-H14', cid),
                     threshold='contract-mandated C-R1-01 predicates (item 1 block; item 2 (i)-(vi) land with 2(v) plan AND Z; item 3 caps) and the '
                               'physical predicates required elsewhere (land seal-flange clearance c_chg_window, frozen U6 island, block strict 3-D '
                               'clearance) at one pose of one design point; the block-AND-Z screen and the supplier thresholds are diagnostics and '
                               'never decide. Numeric prerequisite threshold: caseback radial limit r_lim >= %.6f mm (radial / plan prerequisite of '
                               'the land-flange and block-flange terms only, not a closure). The land 2(v) Z separation from the screws / supports '
                               'is unsatisfiable under the retained Z model (Q-R1-CHARGER)' % (pp['r_lim_required_mm'] or -1),
                     threshold_value=pp['r_lim_required_mm'], threshold_units='mm (r_lim, radial / plan prerequisite)',
                     required_delta=max(0.0, pp['deficit_mm']) if pp['deficit_mm'] is not None else None,
                     required_delta_units='mm (r_lim deficit of the radial / plan prerequisite)',
                     typed=dict(terms=gv['terms'], categories=gv['categories'], governing=gv['governing'], physical_pass=gv['physical_pass'],
                                rule=gv['rule'], clauses=CHG_CLAUSES))
    # R1-H15 RF / MAG
    rf = E['rf']
    H['R1-H15'] = hc('R1-H15', True, rf['h17_pass'] and rf['h18_pass'], None, 'exact',
                     dict(rf_intrusions=rf['rf_intrusions'], mag_violations=rf['mag_violations'],
                          button_rules={s: r['materials']['rule'] for s, r in btn['switches'].items()}), [], [], miss['R1-H15'], g4_lit(cx, 'R1-H15', cid))
    # R1-H16 S14 untouched
    s14 = E['s14']
    p16 = s14['pass_'] and all(c['pass_'] for c in st.s14geo['carry_in_checks']) and frozen_switches_ok(st)
    H['R1-H16'] = hc('R1-H16', True, p16, None, 'exact', dict(intrusions=s14['intrusions'], frames_valid=s14['frames_valid'],
                                                              switches_frozen=frozen_switches_ok(st)), [], [], miss['R1-H16'], g4_lit(cx, 'R1-H16', cid))
    # R1-H17 assembly
    a = E['asm']
    m17 = min(row['insertion'].values())
    H['R1-H17'] = hc('R1-H17', True, a['sequence_executable'], m17, 'mm',
                     dict(identity=a['identity'], insertion=row['insertion'], a9=a['a9_geometry']['pass_'], closure=a['caseback_closure']['pass_'],
                          gated_operations=a['gated_operations'], product_closure_executable=a['product_closure_executable'],
                          failed_dependencies=a['failed_dependencies'], gated_dependencies=a['gated_dependencies']),
                     [dict(term='c_insert_zero_margin_mm', value=st.P['c_insert_mm']['max'] + m17)],
                     a['gates'] if a['sequence_executable'] else ['R1-S02'] + a['gates'], miss['R1-H17'], g4_lit(cx, 'R1-H17', cid),
                     threshold='operation sequence executable on its own geometry (c_insert zero-margin value); product closure requires every '
                               'A-step dependency RESOLVED',
                     categorical_evidence=dict(dependencies=[dict((k, d[k]) for k in ('step', 'requires', 'state', 'gate')) for d in a['dependencies']],
                                               service='SERVICE-COVER-REBOND'))
    # R1-H18 supports
    s = E['supports']
    H['R1-H18'] = hc('R1-H18', True, s['pass_'], s['post_radial_room_mm'], 'mm', dict(count=s['count'], pads=s['pads'], w_nw=s['w_nw'],
                                                                                     largest_pad_arc_deg=s['largest_pad_arc_deg']), [], [], miss['R1-H18'], g4_lit(cx, 'R1-H18', cid))
    # R1-H19 LRA
    L = E['lra']
    Eg = L['envelopes']['authored_grid_maximum']['value_mm']
    zms = [c['z_margin_before_structure_mm'] for c in L['classes'] if c['z_margin_before_structure_mm'] is not None]
    m19 = max(zms) if zms else Eg - L['authored_min_height_mm']
    H['R1-H19'] = hc('R1-H19', True, L['physical_pass'], m19 if L['physical_pass'] else min(m19, -L['delta_Z_mm']['authored_grid_maximum']), 'mm',
                     dict(envelopes=L['envelopes'], delta_Z=L['delta_Z_mm'], classes=[dict((k, c[k]) for k in ('id', 'plan_feasible_poses', 'H_before_structure_mm',
                                                                                                            'z_margin_before_structure_mm', 'structurally_feasible_fits', 'fits'))
                                                                                     for c in L['classes']],
                          structural_rescreen=L['structural_rescreen'], supplied=L['supplied']),
                     [dict(term='class_envelope_height_max_mm (authored-grid maximum, before structural qualification)', value=Eg),
                      dict(term='class_envelope_height_max_mm (continuous upper bound, not a search result)', value=L['envelopes']['continuous_upper_bound']['value_mm'])],
                     L['gates'], miss['R1-H19'], g4_lit(cx, 'R1-H19', cid), lra_isolated=True,
                     threshold='authored / supplied class (C-R1-08, lead / exit included) with envelope height <= %.3f mm on a plan-feasible pose and a '
                               'structurally feasible caseback' % Eg, threshold_value=Eg, threshold_units='mm (authored-grid maximum)',
                     required_delta=L['delta_Z_mm']['authored_grid_maximum'])
    # R1-H20 scope
    H['R1-H20'] = hc('R1-H20', True, scope['pass_'] and in_proc['pass_'], None, 'exact', dict(scope['checks'], historical=in_proc['pass_']),
                     [], [], miss['R1-H20'], g4_lit(cx, 'R1-H20', cid))
    return H


# --------------------------------------------------------------------------------------------
# Lane dispositions, stops (derived), verdict (pure)
# --------------------------------------------------------------------------------------------
def lane_dispositions(E, H):
    def disp(phys, gates):
        if phys:
            return 'SUPPLIER_GATED' if gates else 'RESOLVED_GEOMETRICALLY'
        return 'OWNER_GATED'
    d = {}
    d['L-WIN'] = disp(H['R1-H07']['physical_pass'], H['R1-H07']['gate_ids'])
    d['L-BTN'] = E['btn']['disposition']
    d['L-SEAL'] = disp(H['R1-H11']['physical_pass'] and H['R1-H13']['physical_pass'], H['R1-H11']['gate_ids'])
    d['L-CHG'] = disp(H['R1-H14']['physical_pass'], H['R1-H14']['gate_ids'])
    d['L-STR'] = disp(H['R1-H09']['physical_pass'] and H['R1-H08']['physical_pass'] and H['R1-H10']['physical_pass'], ['FEA-1..4'])
    d['L-RAD'] = disp(H['R1-H04']['physical_pass'] and H['R1-H02']['physical_pass'], H['R1-H04']['gate_ids'])
    d['L-ASM'] = E['asm']['disposition']   # R2-5: product-closure dependencies decide (sequence geometry alone never closes the product)
    d['L-LRA'] = E['lra']['disposition'] if not E['lra']['physical_pass'] else 'SUPPLIER_GATED'
    return d


def stops_of(cx, E, H, disp, all_E, in_proc, scope):
    st = cx.st
    odw = any(o['id'] == 'OD-G4-WINDOW' for o in cx.I['owner_decisions'])
    oda = any(o['id'] == 'OD-G4-ASSEMBLY' for o in cx.I['owner_decisions'])
    asm = E['asm']
    own_asm = asm['identity']['pass_'] and all(r['pass_'] for r in asm['order_check']) and asm['a9_geometry']['pass_'] \
        and asm['caseback_closure']['pass_'] and all(v >= -EPS for v in E['row']['insertion'].values())
    th = E['strl']['thresholds']
    mat = E['strl']['materials']['outer']['id']
    z_need = (th['z_shortfall_mm'] or 0.0) > EPS or th['inner_region_requirement_exceeds_pod_residual']
    any_d = any(x['classification']['D_radial_core'] is not None for x in all_E)
    credited_pass = [h['id'] for h in H.values() if h['study_status'] == 'PASS' and h['credits']]
    owner_lanes = [l for l, v in disp.items() if v in ('OWNER_GATED', 'RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED')]
    S = [
        ('R1-S01', not (odw and H['R1-H07']['physical_pass']), 'OD-G4-WINDOW recorded: %s; W1 row passes without Z delta: %s' % (odw, H['R1-H07']['physical_pass'])),
        ('R1-S02', not (oda and own_asm), 'OD-G4-ASSEMBLY recorded: %s; own sequence geometry / order / identity executable: %s' % (oda, own_asm)),
        ('R1-S03', not E['btn']['closed'] and E['btn']['disposition'] != 'RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED',
         'button topologies closing per SW (I-SUM / I-MAX): %s' % {s: (r['pass_I_SUM'], r['pass_I_MAX']) for s, r in E['btn']['switches'].items()}),
        ('R1-S04', not H['R1-H14']['physical_pass'] and E['classification']['coupled_first_D']['charger_with_od'] is None,
         'complete C-R1-01 charger closure (contract-mandated + physical predicates, same-point neighbours) at the design point: %s '
         '(governing contract term %s %s mm); first D (any wall) with the radial prerequisite %s, the plan prerequisite %s (r_lim %s mm vs '
         '%.3f mm here), the LAND 2(v) Z prerequisite %s, the complete closure %s; complete closure with H03-OD at one point: %s' % (
             E['chg']['pass_'], H['R1-H14']['typed']['governing']['term_id'], fs(H['R1-H14']['typed']['governing']['value']),
             f2(E['chg_literal']['first_D']['first_radial']), f2(E['chg_literal']['first_D']['first_plan']),
             f3(E['chg_literal']['plan_prerequisite']['r_lim_required_mm']), E['chg']['r_lim'], f2(E['chg_literal']['first_D']['first_z']),
             f2(E['chg_literal']['first_D']['first_literal']), f2(E['classification']['coupled_first_D']['charger_with_od']))),
        ('R1-S05', (not H['R1-H09']['physical_pass']) and z_need,
         'required uniform %s caseback %.3f mm nominal vs t_in %.2f (pod residual) / Z %.3f available: thicker caseback / Z needed = %s' %
         (mat, th[mat]['required_uniform_nominal_thickness_mm'] or -1, E['strl']['selected']['t_in'], th['z_available_for_uniform_plate_mm'], z_need)),
        ('R1-S06', not (H['R1-H11']['physical_pass'] and H['R1-H13']['physical_pass']), 'main seal topologies feasible: %s; seal path closed: %s; apertures feasible: %s'
         % (E['seal']['feasible_topologies'], E['seal_closure']['closed'], all(E['aperture_feasible'].values()))),
        ('R1-S07', not H['R1-H09']['physical_pass'], 'Screen B %.1f MPa / %.4f mm, Screen A %.1f MPa vs allowable %.0f MPa / limit %.3f mm' %
         (E['strl']['screen_B']['sigma_governing_MPa'], E['strl']['screen_B']['w_max_mm'], E['strl']['screen_A']['sigma_governing_MPa'],
          E['strl']['materials']['outer']['sigma_allow'], E['strl']['limits']['c_defl'])),
        ('R1-S08', E['lra']['od_g4_lra_arch_triggered'], 'no authored / supplied class fits any pose (pocket included, structural re-screen applied): '
         'delta_Z %.3f mm vs the authored-grid maximum %.3f mm (before structural qualification; continuous upper bound %.3f mm, not a search '
         'result); structurally feasible searched envelope: %s' % (
             E['lra']['delta_Z_mm']['authored_grid_maximum'], E['lra']['envelopes']['authored_grid_maximum']['value_mm'],
             E['lra']['envelopes']['continuous_upper_bound']['value_mm'], f3(E['lra']['envelopes']['structurally_feasible_searched']['value_mm']))),
        ('R1-S09', not H['R1-H16']['physical_pass'] or not scope['checks']['kicad_interfaces_placement_unchanged'],
         'S14 untouched / switches frozen: %s; KiCad / interfaces unchanged: %s' % (H['R1-H16']['physical_pass'], scope['checks']['kicad_interfaces_placement_unchanged'])),
        ('R1-S10', (not any_d) or bool(E['protrusions']),
         'whole-design rule: some candidate closes the radial core (H03-OD, H05-GEOM, insertion) at one D <= 51.00 mm: %s; unpermitted '
         'protrusions: %d. Lane D thresholds above 51.00 mm (e.g. main seal) are owner-question numbers, not a selected diameter.'
         % (any_d, len(E['protrusions']))),
        ('R1-S11', bool(credited_pass), 'PASS checks resting on a credit: %s' % credited_pass),
        ('R1-S12', not (scope['pass_'] and in_proc['pass_'] and st.legacy['pass_']), 'pins / brief / immutables / historical G4: scope %s, in-process G4 %s'
         % (scope['pass_'], in_proc['pass_'])),
        ('R1-S13', bool(owner_lanes), 'lanes needing an unrecorded owner decision or C-R1-03 adjudication: %s' % owner_lanes),
    ]
    return [dict(id=i, raised=bool(r), fatal=i in FATAL_STOPS, lane_local=i in LANE_STOPS, detail=t) for i, r, t in S]


def verdict_of(disp, stops):
    raised = {s['id'] for s in stops if s['raised']}
    fatal = {s['id'] for s in stops if s['raised'] and s['fatal']}
    if fatal:
        return 'R1 FAIL'
    non = [disp[l] for l in LANES if l != 'L-LRA']
    if all(v == 'RESOLVED_GEOMETRICALLY' for v in non) and disp['L-LRA'] == 'RESOLVED_GEOMETRICALLY':
        return 'R1 RESOLVED'
    if all(v in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED') for v in non):
        if disp['L-LRA'] in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED'):
            return 'R1 RESOLVED — SUPPLIER/RF/QUALIFICATION GATES OPEN'
        if disp['L-LRA'] == 'ARCHITECTURE_GATED' and 'R1-S08' in raised:
            return 'R1 PARTIAL — LRA ARCHITECTURE GATE'
    open_lanes = [l for l in LANES if disp[l] not in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED')]
    lane_stop = {'L-BTN': ('R1-S03', 'R1-S13'), 'L-CHG': ('R1-S04', 'R1-S13'), 'L-STR': ('R1-S05', 'R1-S07'), 'L-SEAL': ('R1-S06',),
                 'L-LRA': ('R1-S08',), 'L-RAD': ('R1-S13',), 'L-WIN': ('R1-S13',), 'L-ASM': ('R1-S13',)}
    if open_lanes and all(any(s in raised for s in lane_stop[l]) for l in open_lanes):
        return 'R1 OWNER DECISION REQUIRED'
    return 'R1 FAIL'


# --------------------------------------------------------------------------------------------
# S20 lead cross-checks and solver anchors (computed with production functions; expected values are review
# references only and never feed a result)
# --------------------------------------------------------------------------------------------
def old_teq(t, w, h, r, n, nu):
    """First-pass (rejected) R1 formula: composite I_T including the flange self-inertia (LA-STR-1 violation)."""
    s = 2.0 * math.pi * r / n
    b_f = min(s, w + 12.0 * t)
    A_f, A_w = b_f * t, w * h
    y = (A_f * t / 2.0 + A_w * (t + h / 2.0)) / (A_f + A_w)
    I_T = b_f * t ** 3 / 12.0 + A_f * (y - t / 2.0) ** 2 + w * h ** 3 / 12.0 + A_w * (t + h / 2.0 - y) ** 2
    return (t ** 3 + 12.0 * (1.0 - nu * nu) * I_T / s) ** (1.0 / 3.0)


def xc(rows, cid, expected, computed, tol, explanation=None, alternative=None, units='mm'):
    ok = computed is not None and abs(computed - expected) <= tol
    if not ok and not explanation:
        raise StudyError('STOP: lead cross-check %s not reproduced (%.6f vs %.6f) and unexplained' % (cid, computed if computed is not None else float('nan'), expected))
    rows.append(dict(id=cid, expected=expected, computed=computed, tolerance=tol, units=units,
                     status='REPRODUCED' if ok else 'EXPLAINED', explanation=None if ok else explanation, alternative=alternative))


def lead_crosschecks(cx, Es):
    st = cx.st
    by = {c['id']: c for c in cx.cands}
    B, A = by['G4-B'], by['G4-A']
    spB, spA = cx.ce['G4-B'].sp, cx.ce['G4-A'].sp
    car = Es['G4-B']['sweep']['carrier']
    rows = []
    pk = {x['R_carrier_inner']: x['margin_mm'] for x in car['pack_rows']}
    xc(rows, 'PACK rcin 23.10', -0.200, pk[23.1], 5e-4)
    xc(rows, 'PACK rcin 23.30', 0.000, pk[23.3], 5e-4)
    xc(rows, 'carrier wall solved', 0.35, car['tcw'], 1e-9)
    r = rad_point(cx, B, 50.9, 1.1, car, Es['G4-B']['sweep']['arcs'])
    xc(rows, 'H05-STRAIGHT (bulk) D50.90 tw1.10 rcin23.30', 0.05, r['g4_literal']['straight_bulk'], 5e-4)
    xc(rows, 'H23-INSERT-BATTERY D50.90 tw1.10', 0.20, r['insertion']['H23-INSERT-BATTERY'], 5e-4)
    dp = dict(D=50.9, tw=1.1, rcin=23.3, tcw=0.35, t_in=0.9, t_out=1.0, bosses={s: 0.9 for s in st.P['buttons']['windows_deg']})
    post = g4.post_load(st, spB, dp)
    xc(rows, 'total caseback reaction', 1168.99, post['total_N'], 5e-3, units='N')
    xc(rows, 'no-rib bypass stress (G4-B)', 622.918, post['case_side_bypass_screen']['sigma'], 5e-4, units='MPa')
    xc(rows, 'no-rib bypass deflection (G4-B)', 0.282746, post['case_side_bypass_screen']['w'], 5e-7)
    cb = spB.m_cb
    te = old_teq(0.8, 0.8, 1.0, 20.5, 16, cb['nu']['max'])
    xc(rows, 'old invalid t_eq (16 spokes, w0.8, h1.0, t0.8)', 1.22566, te, 5e-5)
    R = 50.9 / 2.0 - 1.1 + spB.pc_env['radius_mm']
    oldr = g4.annular_plate([(cx.rb, cx.r_step, round(te, 5), cb['E_MPa']['min'], cb['nu']['max']),
                             (cx.r_step, R, round(te, 5), cb['E_MPa']['min'], cb['nu']['max'])], cx.p, 'loaded_boss')
    xc(rows, 'old invalid t_eq stress (diagnostic)', 329.33, oldr['sigma'], 5e-3, units='MPa')
    xc(rows, 'old invalid t_eq deflection (diagnostic)', 0.11618, oldr['w'], 5e-6)
    for mid, proc, exp in (('MAT-CERAMIC', 'PC-CERAMIC-GRIND', 1.82), ('MAT-NF-METAL', 'PC-METAL-MACH', 1.96), ('MAT-GF-POLY', 'PC-POLY-MOULD', 4.71)):
        m = str_material(st, mid, proc)
        xc(rows, 'required uniform isotropic thickness %s' % mid, exp, iso_req_thickness(cx, m, R, cx.rb, cx.r_step), 6e-3)
    for mid, proc, exp in (('MAT-CERAMIC', 'PC-CERAMIC-GRIND', 118.0), ('MAT-NF-METAL', 'PC-METAL-MACH', 118.6), ('MAT-GF-POLY', 'PC-POLY-MOULD', 126.0)):
        m = str_material(st, mid, proc)
        t = 0.9 - m['tol_t']
        sc = plate_solve([iso_region(cx.rb, cx.r_step, t, m['E'], m['nu'])], cx.p, 'loaded_boss', 'clamped', 81)
        ss = plate_solve([iso_region(cx.rb, cx.r_step, t, m['E'], m['nu'])], cx.p, 'loaded_boss', 'ss', 81)
        vc = max(6.0 * max(abs(x['Mr']), abs(x['Mt'])) / t ** 2 for x in sc[0]['samples'])
        vs = max(6.0 * max(abs(x['Mr']), abs(x['Mt'])) / t ** 2 for x in ss[0]['samples'])
        xc(rows, 'rigid outer annulus lower bound %s (t_in 0.9)' % mid, exp, vc, 0.5,
           'Not reproduced exactly: the idealisation is not specified. The inner region (rb..r_step, t_in 0.9 - tol, loaded boss) gives '
           '%.1f MPa clamped and %.1f MPa simply supported at r_step; the lead value lies between these bounds. Every bound exceeds the '
           'polymer 35 MPa allowable; the corrected Screen B result governs.' % (vc, vs), dict(clamped=vc, simply_supported=vs), 'MPa')
    # main seal at G4-B D = 51.0 with the lead tw 1.35 (bulk metal tolerances as in G4) and the R1 azimuth-resolved annulus
    gd = g4.gland_design(st, spB, 'face', 0.9)
    bulk_tol = spB.pc_mid['od_radius_mm'] + spB.pc_mid['radius_mm']
    xc(rows, 'face seal required tw (smallest feasible gland cs 0.9)', 2.09, gd['face_annulus'] + bulk_tol, 5e-4)
    xc(rows, 'face seal margin at tw 1.35', -0.74, 1.35 - bulk_tol - gd['face_annulus'], 5e-4)
    bl = st.P['bond_lands']['caseback_bond_land_mm']['max']
    xc(rows, 'adhesive required tw', 1.54, bl + bulk_tol, 5e-4)
    xc(rows, 'adhesive margin at tw 1.35', -0.19, 1.35 - bulk_tol - bl, 5e-4)
    rad = min(cs for cs in grid(dict(start=0.5, stop=2.0, step=0.1))
              if min(g4.run_check(s, False) for s in spB.gland('X', 'static_radial', *[g4.gland_design(st, spB, 'radial', cs)[k] for k in ('cs', 'h', 'g', 'tol_h', 'tol_g')])) >= -EPS)
    xc(rows, 'radial gland smallest feasible cs', 1.5, rad, 1e-9)
    gr = g4.gland_design(st, spB, 'radial', rad)
    z08 = g4.run_check(spB.rear_periphery(dict(h_pod=0.0, t_out=0.8), gr['spigot_height']), False)
    z_floor = g4.run_check(spB.rear_periphery(dict(h_pod=0.0, t_out=seal_t_out_min(cx, spB)), gr['spigot_height']), False)
    xc(rows, 'radial spigot rear-periphery Z at cs 1.5', -1.05, z08, 5e-3,
       alternative=dict(t_out_material_floor=seal_t_out_min(cx, spB), margin_at_floor=z_floor,
                        note='-1.05 uses t_out 0.8 (below the ceramic floor 0.8 + 0.02); at the floor-compliant t_out the margin is %.3f' % z_floor))
    # charger
    xc(rows, 'strict-wedge land A/C (chg_r_out 24.0)', 0.674, strict_wedge(cx, A, 24.0), 5e-4)
    spB2 = copy.copy(spB)
    spB2.pc_cb = dict(spB.pc_cb, radius_mm=0.05)
    ceB2 = copy.copy(cx.ce['G4-B'])
    ceB2.sp = spB2
    cx2 = copy.copy(cx)
    cx2.ce = dict(cx.ce, **{'G4-B': ceB2})
    sw_b = strict_wedge(cx, B, 23.34)
    xc(rows, 'strict-wedge land B (radial chg_r_out 23.34)', 0.589, sw_b, 5e-4,
       'The accepted g4.charger_fit applies the caseback process position tolerance (ceramic grind 0.02 mm) and gives %.4f mm; the '
       'lead value is reproduced with a 0.05 mm (polymer) position tolerance: %.4f mm.' % (sw_b, strict_wedge(cx2, B, 23.34)),
       dict(polymer_tolerance=strict_wedge(cx2, B, 23.34)))
    xc(rows, 'charger ori-0 minimum centre radius for the continuous 1.0 land (G4-B)', 20.52,
       cx.r_s14_clear + chg_block_dims(cx, 0)[0] / 2.0 + cx.P['V20_charger_land']['adverse_mm'] + spB.pc_cb['radius_mm'], 5e-3,
       alternative=dict(grid_value=min(p['r_centre'] for p in Es['G4-B']['sweep']['poses'] if p['prereq_pass'] and p['orientation'] == 0)))
    # buttons
    for sw, boss, exp_s, exp_m in (('SW1', 0.95, 0.04, 0.24), ('SW5', 0.90, -0.08, 0.12)):
        T = btn_terms(cx, B, sw)
        s_sum = btn_section(T, 50.9, 'T2-F', boss, 2.0, 'I-SUM')['margins']['bore_stack']
        s_max = btn_section(T, 50.9, 'T2-F', boss, 2.0, 'I-MAX')['margins']['bore_stack']
        xc(rows, 'button %s I-SUM before boot height (boss %.2f)' % (sw, boss), exp_s, s_sum, 5e-4,
           alternative=dict(boss_0p95=btn_section(T, 50.9, 'T2-F', 0.95, 2.0, 'I-SUM')['margins']['bore_stack']) if sw == 'SW5' else None)
        xc(rows, 'button %s I-MAX before boot height (boss %.2f)' % (sw, boss), exp_m, s_max, 5e-4)
    # LRA (R2-3): labelled envelopes, never a bound presented as a search result
    L = Es['G4-B']['lra']
    xc(rows, 'LRA historical optimistic bound (0.5 residual, no band; not a search result)', 2.08, L['envelopes']['historical_optimistic']['value_mm'], 5e-4)
    for mid, exp in (('MAT-CERAMIC', 1.78), ('MAT-NF-METAL', 1.88), ('MAT-GF-POLY', 1.55)):
        m = L['material_table'][mid]
        xc(rows, 'LRA lead formula without LA-Z-2 band %s (historical, not a search result)' % mid, exp, m['lead_formula_without_band_mm'], 5e-4,
           alternative=dict(continuous_without_band=m['continuous_without_band_mm'], continuous_upper_bound_with_band=m['continuous_upper_bound_mm'],
                            note='lead formula uses residual = floor; LA-LRA-1 residual = floor + tol and the thickness tolerance again on '
                                 'the pocket floor Z; LA-Z-2 deducts the conductor band'))
    for mid, cont, gridv in (('MAT-CERAMIC', 1.110, 1.030), ('MAT-NF-METAL', 1.210, 1.130), ('MAT-GF-POLY', 0.850, 0.800)):
        m = L['material_table'][mid]
        xc(rows, 'LRA continuous upper bound LA-LRA-1 + LA-Z-2 %s (not a search result)' % mid, cont, m['continuous_upper_bound_mm'], 5e-4)
        xc(rows, 'LRA authored-grid maximum %s (searched, before structural qualification)' % mid, gridv, m['authored_grid_maximum_mm'], 5e-4)
    xc(rows, 'LRA selected design-point envelope G4-B (ceramic plate / deepest admissible pocket)', 0.930,
       L['envelopes']['selected_design_point']['value_mm'], 5e-4)
    xc(rows, 'LRA structurally feasible searched envelope G4-B (null = none; encoded -1)', -1.0,
       -1.0 if L['envelopes']['structurally_feasible_searched']['value_mm'] is None else L['envelopes']['structurally_feasible_searched']['value_mm'], 1e-12)
    # charger (R3-8): radial / plan PREREQUISITE thresholds (never closures), strict-wedge supplier zero-margin widths
    for cid, r_exp, rc_exp in (('G4-B', 24.624973, 21.15), ('G4-A', 24.856896, 21.35), ('G4-C1', 24.856896, 21.35)):
        pp = Es[cid]['chg_literal']['plan_prerequisite']
        xc(rows, 'charger plan-prerequisite r_lim required (%s; prerequisite only, not a closure)' % cid, r_exp, pp['r_lim_required_mm'], 5e-6)
        xc(rows, 'charger plan-prerequisite pose r_centre (%s)' % cid, rc_exp, pp['pose']['r_centre'], 1e-9)
        xc(rows, 'charger plan-prerequisite pose az_centre (%s)' % cid, 89.0, pp['pose']['az_centre'], 1e-9)
    for cid, w_exp in (('G4-B', 0.707852), ('G4-A', 0.673974), ('G4-C1', 0.673974)):
        xc(rows, 'strict-wedge supplier zero-margin land width at the design point (%s; threshold only, not credited)' % cid, w_exp,
           Es[cid]['chg_literal']['strict_wedge_supplier_path']['width_mm'], 5e-6)
    # structure selected point / main seal labels
    B = Es['G4-B']
    xc(rows, 'selected-point Screen B stress (G4-B design point)', 371.783850, B['strl']['screen_B']['sigma_governing_MPa'], 5e-6, units='MPa')
    xc(rows, 'selected-point Screen B deflection (G4-B design point)', 0.119816560, B['strl']['screen_B']['w_max_mm'], 5e-9)
    xc(rows, 'first main-seal grid closure D (G4-B, adhesive option)', 51.80, (B['classification']['main_seal_first'] or {}).get('D'), 1e-9)
    xc(rows, 'first main-seal closure is the adhesive option only (1 = adhesive alone)', 1.0,
       1.0 if (B['classification']['main_seal_first'] or {}).get('topologies') == ['adhesive'] else 0.0, 1e-12)
    xc(rows, 'button zero-margin nominal D (T2-R)', 54.56, max(r['thresholds']['T2-R']['required_D_mm'] for r in B['btn']['switches'].values()), 5e-3)
    xc(rows, 'T3 flexure web threshold (not manufacturability evidence)', 0.009762,
       min((r['T3'] or {}).get('required_web_thickness_max_mm', 9.0) for r in B['btn']['switches'].values() if r['T3']), 5e-6)
    fa = {a['reservation']: a['search']['at_floor'] for a in B['row']['arcs']}
    xc(rows, 'H05 metal arc floor (G4-B)', 0.740, fa['FPC_CORR']['t_mm'], 1e-9)
    xc(rows, 'XF edge margin at the arc floor (G4-B)', 0.290, fa['FPC_CORR']['edge_margin_mm'], 5e-4)
    xc(rows, 'XB edge margin at the arc floor (G4-B)', 0.290, fa['BATT_TAIL']['edge_margin_mm'], 5e-4)
    xc(rows, 'G4-A H05-GEOM minimum at D50.90 (bulk XF / XB)', -0.080, Es['G4-A']['row']['h05_geom_min'], 5e-4)
    # window
    W = Es['G4-A']['win']
    for mat, sv, wv in (('sapphire', 23.3941, 0.0005188), ('cs_glass', 22.8979, 0.0029891), ('polycarbonate', 23.9612, 0.0731488)):
        xc(rows, 'W1 %s stress' % mat, sv, W['materials'][mat]['sigma_ss_MPa'], 5e-4, units='MPa')
        xc(rows, 'W1 %s deflection' % mat, wv, W['materials'][mat]['w_ss_mm'], 5e-7)
    xc(rows, 'W1 nominal web comparison', 0.181, W['margins']['rib_fit_nominal_mm'], 5e-4)
    xc(rows, 'W1 bond-land arithmetic (polymer frame)', 0.150, W['margins']['window_bond_land_mm'], 5e-4)
    xc(rows, 'W1 Z delta', 0.0, W['z_delta_mm'], 1e-12)
    # face O-ring arithmetic
    s3 = spB.gland('XC', 'static_face', 1.0, 0.77, 1.40, 0.02, 0.03)
    o = st.P['oring']['windows']['static_face']
    v = [g4.run_check(x, False) for x in s3]
    xc(rows, 'face O-ring compression min %', 16.8421, 100.0 * (v[0] + o['compression_min']), 5e-4, units='%')
    xc(rows, 'face O-ring compression max %', 28.5714, 100.0 * (o['compression_max'] - v[1]), 5e-4, units='%')
    xc(rows, 'face O-ring fill %', 84.2726, 100.0 * (o['fill_max'] - v[2]), 5e-4, units='%')
    xc(rows, 'polymer required diameter (H05-GEOM, G4-A)', 51.10, Es['G4-A']['classification']['groups']['H05-GEOM']['first_pass_D'], 1e-9)
    return rows


def solver_anchors(cx, Es):
    st = cx.st
    spB = cx.ce['G4-B'].sp
    cb = spB.m_cb
    tol = spB.pc_cb['thickness_mm']
    R = 50.9 / 2.0 - 1.1 + spB.pc_env['radius_mm']
    cases = [[(cx.rb, cx.r_step, 0.9 - tol, cb['E_MPa']['min'], cb['nu']['max']), (cx.r_step, R, 1.0 - tol, cb['E_MPa']['min'], cb['nu']['max'])],
             [(cx.rb, cx.r_step, 0.85, 7000.0, 0.4), (cx.r_step, 24.4, 0.95, 7000.0, 0.4)],
             [(cx.rb, 15.0, 0.7, 105000.0, 0.34), (15.0, 19.0, 1.2, 105000.0, 0.34), (19.0, 24.0, 0.9, 105000.0, 0.34)]]
    iso = []
    for regs in cases:
        a = iso_compare(regs, cx.p)
        b = g4._annular_plate(tuple(regs), cx.p, 'loaded_boss')
        r2 = [iso_region(*x) for x in regs]
        for rg in r2:
            rg['k'] = 1.0 - 1e-7
        sol = plate_solve(r2, cx.p, 'loaded_boss', 'ss', 81)
        wk = max(abs(s['w']) for x in sol for s in x['samples'])
        sk = max(6.0 * max(abs(s['Mr']), abs(s['Mt'])) / x['region']['t'] ** 2 for x in sol for s in x['samples'])
        iso.append(dict(regions=len(regs), rel_w=abs(a['w'] - b['w']) / b['w'], rel_sigma=abs(a['sigma'] - b['sigma']) / b['sigma'],
                        orthotropic_k_to_1_rel_w=abs(wk - b['w']) / b['w'], orthotropic_k_to_1_rel_sigma=abs(sk - b['sigma']) / b['sigma']))
    lim = cx.P['screen_b']['isotropic_limit_max_rel']
    iso_ok = all(max(x.values()) <= lim for x in [{k: v for k, v in d.items() if k != 'regions'} for d in iso])
    geo = dict(rb=cx.rb, r_step=cx.r_step, r_rib_in=cx.r_s14_clear, r_rib_out=R - 0.5, R=R, gap_deg=None)
    m = str_material(st, 'MAT-CERAMIC', 'PC-CERAMIC-GRIND')
    nr = screen_eval(geo, lambda r: m, dict(t_in=0.9, t_out=1.0, n=0, w=0.0, h=0.0), 'B', 8, cx.p, 2.0,
                     dict(c_defl=0.05, outline_r=st.s14geo['outline_r'], z_band_lo=cx.zm['z_band_lo_adv'], rib_top_adv=None), 81)
    nr_ok = abs(nr['sigma_governing_MPa'] - 622.918) <= 5e-4 and abs(nr['w_max_mm'] - 0.282746) <= 5e-7
    Dp, Dr, _ = rib_D(m['E'], m['nu'], 0.98, 0.8, 0.0, 9.0)
    br = Es['G4-B']['strl'].get('best_ribbed')
    conv = br['convergence'] if br else Es['G4-B']['strl']['convergence']
    if not (iso_ok and nr_ok):
        raise StudyError('STOP: Screen-B isotropic / no-rib anchor failure')
    # exact compliance integral (R2-1 bound) vs a fine trapezoid on an orthotropic ribbed solution
    regs = str_regions(dict(geo, r_rib_out=R - 0.5, gap_deg=22.5), lambda r: m, dict(t_in=1.1, t_out=1.6, n=16, w=0.8, h=0.8), 'B', 8)
    sol = plate_solve(regs, cx.p, 'loaded_boss', 'ss', 1201)
    C, _ = compliance(sol, cx.p)
    Ct = cx.p * math.pi * cx.rb ** 2 * sol[0]['samples'][0]['w'] + 2.0 * math.pi * cx.p * sum(
        0.5 * (a_['w'] * a_['r'] + b_['w'] * b_['r']) * (b_['r'] - a_['r']) for x in sol for a_, b_ in zip(x['samples'], x['samples'][1:]))
    integ = dict(exact=C, trapezoid_1201=Ct, rel=abs(C - Ct) / C, pass_=abs(C - Ct) / C < 1e-6)
    if not integ['pass_']:
        raise StudyError('STOP: exact compliance integral not reproduced by the fine trapezoid')
    sb = {c: dict(design_point_method=Es[c]['structure_design_point']['record']['method'],
                  design_point_bound_mm=Es[c]['structure_design_point']['record']['bound_mm'],
                  configs_dominance_checked=Es[c]['structure_design_point']['configs_checked'],
                  w_max_at_boss_all_searched_configs=Es[c]['strl'].get('w_max_at_boss_all_configs'),
                  exact_search_pass=Es[c]['strl']['physical_pass']) for c in Es}
    return dict(isotropic_limit=iso, isotropic_limit_pass=iso_ok, max_rel_allowed=lim,
                compliance_integral=integ, structure_bound=sb,
                no_rib_anchor=dict(sigma_MPa=nr['sigma_governing_MPa'], w_mm=nr['w_max_mm'], expected=[622.918, 0.282746], pass_=nr_ok),
                h_rib_zero=dict(D_plate=Dp, D_r=Dr, equal=Dr == Dp),
                convergence_best_ribbed=conv, convergence_pass=max(conv['rel_sigma'], conv['rel_w']) < cx.P['screen_b']['convergence_max_rel'],
                monotonicity=dict(
                    pack_and_carrier_wall={c: Es[c]['sweep']['carrier']['monotone'] for c in Es},
                    structural_t_in={c: Es[c]['strl']['t_in_monotonicity']['pass_'] for c in Es},
                    button_pruning_equals_full_grid={c: Es[c]['btn_prune_equal'] for c in Es}))


# --------------------------------------------------------------------------------------------
# Result assembly (stage 3 ranking / selection, owner questions, handoff)
# --------------------------------------------------------------------------------------------
def charger_question_text(E):
    """Q-R1-CHARGER wording (R4-5) derived from the computed charger categories and the typed H14 attribution (no fixed claim, no
    assumed answer, no contract amendment)."""
    lit = E['chg_literal']
    F, zp = lit['first_D'], lit['z_prerequisite']
    lu = zp['land_unsatisfiability']
    bd, vw, swp = lit['block_and_z_diagnostic'], lit['v_z_waived_diagnostic'], lit['strict_wedge_supplier_path']
    d_end = E['sweep']['rows'][-1]['D']
    parts = []
    if lu['unsatisfiable']:
        plan_gaps = [r['plan_gap_mm'] for r in E['chg']['neighbours']['rows'] if r['a'] == 'CHG_LAND' and r['b'] in lu['unsatisfiable_items']]
        parts.append('(1) Does C-R1-01 2(v) intentionally require positive PLAN AND positive Z separation of the non-conductive charger land from '
                     'screws / supports even when they are already disjoint in plan? Under the retained G4 common-Z geometry (land Z 0..%s mm; %s '
                     'occupy Z from the same Z = 0 caseback datum) Z_gap = max(-h_land, -H) = -min(h_land, H) <= 0, so the land condition is '
                     'unsatisfiable for every pose, D and land width (land Z gap %s mm while the plan gaps are %s..%s mm).' % (
                         f3(lu['h_land_mm']), ', '.join(lu['unsatisfiable_items']), fs(min(x['z_gap_mm'] for x in lu['items'])),
                         fs(min(plan_gaps, default=None)), fs(max(plan_gaps, default=None))))
    parts.append('(2) Does the same conjunctive plan-AND-Z condition apply (a) to the conductive charger block - C-R1-01 item 1 states no '
                 'plan-AND-Z rule for the block; R1 holds it to the common strict 3-D clearance (met at the design point: %s) and reports the '
                 'block-AND-Z screen as model conservatism only (block Z gap %s mm to the 2(v) items, %s mm to CHG_ROUTE / CHG_LINK at its '
                 'SR-CHG-MECH allocation height) - and (b) to the strict-wedge supplier alternative of C-R1-01 item 4 (land < %s mm strictly, '
                 'never credited)?' % (cellv(bd['block_3d_clear_of_routes']), fs(bd['v_item_min_z_gap_mm']),
                                       fs(min(bd['route_z_gaps_mm'].values(), default=None)), f3(swp['width_mm'])))
    parts.append('R1 does not assume the answers, does not amend the contract and does not choose geometry; a formal clarification / amendment '
                 'is required before any charger closure is claimed under different semantics.')
    dd = lambda v: 'none through %.2f mm' % d_end if v is None else 'D %.2f mm' % v
    parts.append('Quantified consequences (diagnostics, not closures): under the literal contract the complete predicate closes at %s; with '
                 'only the conjunctive Z part of 2(v) waived for a plan-disjoint land the remaining predicates first hold at %s (with the radial '
                 'core %s; with the radial core and the main seal %s); the strict-wedge path completes at %s with 2(v) applied to its land and '
                 'at %s without its Z part (with the radial core %s).' % (
                     dd(F['first_literal']), dd(vw['first_D']), dd(vw['first_D_with_radial_core']), dd(vw['first_D_with_radial_core_and_main_seal']),
                     dd(swp['first_D_complete']), dd(swp['first_D_complete_v_z_waived']), dd(swp['first_D_complete_v_z_waived_with_radial_core'])))
    parts.append('Independently of 2(v): the radial / plan prerequisites first hold at %s (with the radial core %s; r_lim >= %s mm); at the '
                 'design point the land\'s 2(vi) 3-D clearance to the caseback seal flange is %s mm and the land-flange radial term is %s mm.' % (
                     dd(F['first_plan']), dd(F['first_plan_with_radial_core']), f3(lit['plan_prerequisite']['r_lim_required_mm']),
                     fs(min([r['effective_clearance_mm'] for r in E['chg']['neighbours']['rows'] if r['a'] == 'CHG_LAND' and r['b'] == 'CB_SEAL_FLANGE'],
                            default=None)), fs(E['chg']['flange_margins']['land_flange'])))
    return ' '.join(parts)


def owner_questions(E, disp, stops):
    raised = {s['id'] for s in stops if s['raised']}
    seal, btn, strl, lra = E['seal'], E['btn'], E['strl'], E['lra']
    th = strl['thresholds']
    mat = strl['materials']['outer']['id']
    q = []
    if 'R1-S03' in raised or disp['L-BTN'] != 'SUPPLIER_GATED':
        r = min(btn['switches'].values(), key=lambda x: x['best']['I-SUM']['min_margin'])
        q.append(dict(id='Q-R1-BUTTON-ENVELOPE', related=['OD-G4-ENVELOPE', 'SR-BUTTONS', 'R1-S03'], decided=False,
                      question='No T2 / T3 button topology closes inside the frozen switch windows and the +1.0 mm boss limit. Options to be '
                               'decided by the owner (not by R1): relax the boss limit / body diameter, supply boot or flexure evidence, or accept '
                               'another button architecture.',
                      thresholds=dict(T2_R_required_D_mm=max(x['thresholds']['T2-R']['required_D_mm'] for x in btn['switches'].values()),
                                      T2_R_required_boss_mm=max(x['thresholds']['T2-R']['required_boss_mm'] for x in btn['switches'].values()),
                                      T2_F_max_boot_free_height_mm=min(x['thresholds']['T2-F']['max_boot_free_height_mm'] for x in btn['switches'].values()),
                                      T3_web_max_mm=min([(x['T3'] or {}).get('required_web_thickness_max_mm') for x in btn['switches'].values()
                                                         if (x['T3'] or {}).get('required_web_thickness_max_mm') is not None] or [None]) if any(
                                          (x['T3'] or {}).get('required_web_thickness_max_mm') is not None for x in btn['switches'].values()) else None,
                                      worst_switch=r['sw'])))
    if 'R1-S06' in raised:
        q.append(dict(id='Q-R1-MAIN-SEAL', related=['OD-G4-ENVELOPE', 'OD-G4-STACK', 'serviceability', 'R1-S06'], decided=False,
                      question='No caseback main-seal topology closes at <= 51.00 mm with zero Z delta: face / adhesive need a wider midcase '
                               'rear-face annulus (diameter), the radial spigot needs Z (OD-G4-STACK); adhesive is non-serviceable.',
                      thresholds=dict(face_required_tw_mm=seal['thresholds']['face']['required_tw_mm'],
                                      adhesive_required_tw_mm=seal['thresholds']['adhesive']['required_tw_mm'],
                                      radial_min_cs_mm=seal['thresholds']['radial']['smallest_feasible_gland_cs'],
                                      radial_z_margin_mm=(seal['thresholds']['radial']['at_that_cs'] or {}).get('spigot_rear_periphery_z'),
                                      main_seal_first_pass_D_mm=E['classification']['groups']['MAIN-SEAL']['first_pass_D'],
                                      main_seal_first_pass=E['classification']['main_seal_first'],
                                      main_seal_with_radial_core_first_D_mm=E['classification']['coupled_first_D']['main_seal_with_radial_core'],
                                      charger_with_main_seal_first_D_mm=E['classification']['coupled_first_D']['charger_with_main_seal'],
                                      note='first closures are report-only extension diameters above the 51.00 mm owner ceiling; quantified, not decided')))
    if 'R1-S07' in raised or 'R1-S05' in raised:
        q.append(dict(id='Q-R1-STRUCTURE', related=['OD-G4-MATERIAL', 'OD-G4-STACK', 'FEA-1..FEA-4', 'R1-S05', 'R1-S07'], decided=False,
                      question='No stiffened caseback passes the loaded-boss planning screens with no ring credit; the inner region is limited '
                               'by the pod residual. Material class / Z allocation / load-path architecture are owner decisions.',
                      thresholds=dict(material=mat, required_uniform_nominal_thickness_mm=th[mat]['required_uniform_nominal_thickness_mm'],
                                      t_in_max_mm=strl['selected']['t_in'], screen_B_sigma_MPa=strl['screen_B']['sigma_governing_MPa'],
                                      screen_B_w_mm=strl['screen_B']['w_max_mm'], allowable_MPa=strl['materials']['outer']['sigma_allow'],
                                      deflection_limit_mm=strl['limits']['c_defl'],
                                      other_materials={k: v['required_uniform_nominal_thickness_mm'] for k, v in th.items() if isinstance(v, dict) and 'required_uniform_nominal_thickness_mm' in v})))
    if 'R1-S04' in raised or disp['L-CHG'] not in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED'):
        lit = E['chg_literal']
        zp, sw_ = lit['z_prerequisite'], lit['strict_wedge_supplier_path']
        q.append(dict(id='Q-R1-CHARGER', related=['SR-CHG-MECH', 'OD-G4-ENVELOPE', 'C-R1-01 2(v)', 'C-R1-01 1', 'C-R1-01 4', 'R1-S04'], decided=False,
                      question=charger_question_text(E),
                      contract_scope=dict(subquestions=['(1) LAND: does C-R1-01 2(v) intend plan AND Z for a land already plan-disjoint from the '
                                                        'screws / supports (unsatisfiable under the retained common-Z model)?',
                                                        '(2a) BLOCK: does the conjunctive condition apply to the conductive block (no such text in '
                                                        'C-R1-01 item 1)?',
                                                        '(2b) STRICT WEDGE: does it apply to the strict-wedge supplier alternative (C-R1-01 item 4)?'],
                                          answers_assumed=False, contract_amended=False, attribution_note=CHG_ATTRIBUTION_NOTE,
                                          quotes=CHG_CONTRACT_QUOTES),
                      thresholds=dict(radial_prerequisite=dict((k, lit['radial_prerequisite'][k]) for k in ('r_lim_required_mm', 'pose', 'deficit_mm', 'required_D_at_design_wall_mm',
                                                                                                        'first_radial', 'first_radial_with_radial_core')),
                                      plan_prerequisite=dict((k, lit['plan_prerequisite'][k]) for k in ('r_lim_required_mm', 'pose', 'deficit_mm', 'required_D_at_design_wall_mm',
                                                                                                    'first_plan', 'first_plan_with_radial_core',
                                                                                                    'first_plan_with_radial_core_and_main_seal', 'first_plan_with_radial_core_and_od')),
                                      z_prerequisite=dict((k, zp[k]) for k in ('pass_', 'first_D', 'land_top_mm', 'route_z_gaps_mm', 'v_item_min_z_gap_mm',
                                                                               'z_unsatisfiable_items', 'threshold')),
                                      land_v_z_unsatisfiability=dict((k, zp['land_unsatisfiability'][k]) for k in ('h_land_mm', 'unsatisfiable', 'items', 'rule',
                                                                                                                  'scope')),
                                      block_and_z_diagnostic=lit['block_and_z_diagnostic'], v_z_waived_diagnostic=lit['v_z_waived_diagnostic'],
                                      complete_closure=dict(lit['literal'], neighbour_complete_first_D=lit['neighbour_complete']['first_D']),
                                      strict_wedge_supplier_path=dict((k, sw_[k]) for k in ('width_mm', 'contained_in_wedge', 'in_land_range', 'plan', 'neighbours',
                                                                                            'z', 'complete', 'complete_v_z_waived', 'failing_terms_by_category',
                                                                                            'first_D_in_land_range', 'first_D_plan', 'first_D_complete',
                                                                                            'first_D_complete_v_z_waived', 'v_applicability', 'threshold')),
                                      strict_wedge_widths_mm=E['strict_wedge'], adverse_land_mm=sw_['adverse_authored_land_mm'],
                                      coupled_first_D_mm=lit['coupled_first_D'])))
    if lra['od_g4_lra_arch_triggered']:
        ev = lra['envelopes']
        q.append(dict(id='OD-G4-LRA-ARCH', related=['R1-S08', 'OD-G4-STACK', 'G2 reallocation study', 'Q-R1-STRUCTURE'], decided=False,
                      question='No authored or supplied LRA class fits any pose at the current G2 allocation (pocket included; structural re-screen '
                               'applied). Raised as a question; R1 does not choose among the options.',
                      thresholds=dict(authored_grid_maximum_mm=ev['authored_grid_maximum']['value_mm'], authored_grid_label=ev['authored_grid_maximum']['label'],
                                      continuous_upper_bound_mm=ev['continuous_upper_bound']['value_mm'],
                                      selected_design_point_mm=ev['selected_design_point']['value_mm'],
                                      structurally_feasible_searched_mm=ev['structurally_feasible_searched']['value_mm'],
                                      historical_optimistic_mm=ev['historical_optimistic']['value_mm'],
                                      delta_Z_mm=lra['delta_Z_mm'], option_set=lra['option_set'])))
    if disp['L-BTN'] == 'RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED':
        q.append(dict(id='C-R1-03-ADJUDICATION', related=['R1-S13'], decided=False, question='Reviewer must rule SUM / MAX for the MAIN-edge gap.'))
    return q


def owner_question_readiness(E, oq, H, stops):
    """R4-12: decision readiness of each raised owner question and of the OD-G4-STACK sub-questions - numeric thresholds present,
    contract scope represented honestly, nothing decided or adopted. A readiness record never chooses an answer."""
    raised = {s['id'] for s in stops if s['raised']}
    by = {q['id']: q for q in oq}
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    out = []

    def rec(qid, ready, basis, open_items=()):
        out.append(dict(id=qid, raised=qid in by, decided=False, answer_adopted=False, ready=bool(ready), basis=basis, open_items=list(open_items)))
    b = by.get('Q-R1-BUTTON-ENVELOPE')
    if b:
        t = b['thresholds']
        rec(b['id'], num(t['T2_R_required_D_mm']) and num(t['T2_R_required_boss_mm']),
            'T2-R zero-margin D %s mm / boss %s mm; T2-F boot free height %s mm; T3 web %s mm; worst switch %s' % (
                fs(t['T2_R_required_D_mm']), fs(t['T2_R_required_boss_mm']), fs(t['T2_F_max_boot_free_height_mm']), fs(t['T3_web_max_mm']),
                t['worst_switch']), ['owner: boss limit / body diameter / button architecture; SR-BUTTONS evidence'])
    m = by.get('Q-R1-MAIN-SEAL')
    if m:
        t = m['thresholds']
        rec(m['id'], num(t['adhesive_required_tw_mm']) and num(t['face_required_tw_mm']) and num(t['radial_min_cs_mm']) and num(t['radial_z_margin_mm']),
            'typed R1-H11 terms; adhesive wall %s mm, face wall %s mm, radial cs >= %s mm with REAR-periphery Z %s mm; first grid closure D %s mm '
            '(%s)' % (fs(t['adhesive_required_tw_mm']), fs(t['face_required_tw_mm']), fs(t['radial_min_cs_mm']), fs(t['radial_z_margin_mm']),
                      f2(t['main_seal_first_pass_D_mm']), (t['main_seal_first_pass'] or {}).get('label')),
            ['owner: diameter / Z (OD-G4-STACK) / serviceability trade-off'])
    s_ = by.get('Q-R1-STRUCTURE')
    if s_:
        t = s_['thresholds']
        rec(s_['id'], num(t['required_uniform_nominal_thickness_mm']) and num(t['screen_B_sigma_MPa']),
            'uniform %s caseback %s mm nominal vs t_in %s mm; Screen B %s MPa / %s mm vs %s MPa / %s mm' % (
                t['material'], fs(t['required_uniform_nominal_thickness_mm']), fs(t['t_in_max_mm']), fs(t['screen_B_sigma_MPa']),
                fs(t['screen_B_w_mm']), fs(t['allowable_MPa']), fs(t['deflection_limit_mm'])), ['owner: OD-G4-MATERIAL / OD-G4-STACK / load path; FEA-1..4'])
    c = by.get('Q-R1-CHARGER')
    if c:
        h = H['R1-H14']
        ty = h['typed']
        honest = (ty['governing']['category'] == 'contract_mandated' and not ty['categories']['contract_mandated']['pass_']
                  and not any(t['category'] == 'contract_mandated' and t['id'].startswith('CHG_BLOCK') and t.get('predicate') == 'plan AND Z'
                              for t in ty['terms'])
                  and len((c.get('contract_scope') or {}).get('subquestions') or []) == 3 and not c['contract_scope']['answers_assumed'])
        rec(c['id'], honest and num(c['thresholds']['plan_prerequisite']['r_lim_required_mm']),
            'contract scope represented: LAND 2(v) failure (%s mm, %s) decides R1-H14; block / strict-wedge applicability asked, not assumed; '
            'block-AND-Z screen labelled model conservatism; prerequisite r_lim %s mm; consequences quantified as diagnostics' % (
                fs(ty['governing']['value']), ty['governing']['term_id'], fs(c['thresholds']['plan_prerequisite']['r_lim_required_mm'])),
            ['owner / contract: C-R1-01 2(v) semantics (1), block (2a), strict wedge (2b); SR-CHG-MECH evidence'])
    a = by.get('OD-G4-LRA-ARCH')
    if a:
        t = a['thresholds']
        rec(a['id'], E['lra']['od_g4_lra_arch_triggered'] and num(t['authored_grid_maximum_mm']) and num(t['delta_Z_mm']['authored_grid_maximum']),
            '9.8 trigger met: no authored / supplied class fits (structurally feasible searched envelope %s); authored-grid maximum %s mm, '
            'delta_Z %s mm; continuous bound %s mm; option set listed, none chosen' % (
                cellv(t['structurally_feasible_searched_mm']), fs(t['authored_grid_maximum_mm']), fs(t['delta_Z_mm']['authored_grid_maximum']),
                fs(t['continuous_upper_bound_mm'])), ['architecture: OD-G4-LRA-ARCH option (R1 does not choose)'])
    seal_t = (by.get('Q-R1-MAIN-SEAL') or {}).get('thresholds') or {}
    str_t = (by.get('Q-R1-STRUCTURE') or {}).get('thresholds') or {}
    th = E['strl']['thresholds']
    hdr = E['lra']['t_total_headroom_nominal_mm']
    subs = [dict(id='STACK-SEAL-RADIAL', question='Z for the radial spigot main seal', value_mm=seal_t.get('radial_z_margin_mm'),
                 basis='REAR-periphery Z margin at the smallest feasible radial cs'),
            dict(id='STACK-STRUCTURE', question='caseback thickness / Z over the pod (inner region) for a uniform plate',
                 value_mm=None if str_t.get('required_uniform_nominal_thickness_mm') is None else
                 str_t['required_uniform_nominal_thickness_mm'] - str_t['t_in_max_mm'],
                 basis='required uniform nominal %s mm vs t_in <= %s mm by the pod residual (inner region); periphery Z available %s mm '
                       '(shortfall there %s mm)' % (fs(str_t.get('required_uniform_nominal_thickness_mm')), fs(str_t.get('t_in_max_mm')),
                                                    fs(th.get('z_available_for_uniform_plate_mm')), fs(th.get('z_shortfall_mm')))),
            dict(id='STACK-LRA', question='REAR Z for an authored LRA class', value_mm=E['lra']['delta_Z_mm']['authored_grid_maximum'],
                 basis='delta_Z vs the authored-grid maximum; T_total headroom %s' % ' / '.join('%.3f' % v for _, v in sorted(hdr.items())))]
    out.append(dict(id='OD-G4-STACK', raised='R1-S05' in raised, decided=False, answer_adopted=False, ready=all(num(x['value_mm']) for x in subs),
                    basis='quantified sub-questions only; no decision adopted; any nonzero total Z needs OD-G4-STACK and a G2 allocation study',
                    subquestions=subs, open_items=['owner: OD-G4-STACK (not triggered by R1; R1-S05 records the Z need)']))
    return out


def compliance_state(E, H, disp, stops, verdict, z_delta, ceiling=51.0):
    """R3-7: separate, non-overloaded study states of one candidate (never one boolean for everything).
      study_candidate                      evaluated R1 candidate, design point <= the ceiling, no whole-run stop raised
      geometric_candidate                  every lane group closes at ONE (D, bulk wall) point with D_complete <= the ceiling, the
                                           design point <= the ceiling, no unauthorized protrusion, zero Z delta (geometry only)
      owner_decision_candidate             study candidate whose verdict names owner / architecture questions (R1 OWNER DECISION
                                           REQUIRED or R1 PARTIAL - LRA ARCHITECTURE GATE); a decision basis, not a compliance claim
      geometry_closed_supplier_gates_open  the brief's 'R1 RESOLVED - SUPPLIER/RF/QUALIFICATION GATES OPEN' state: geometric
                                           candidate, every lane RESOLVED_GEOMETRICALLY or SUPPLIER_GATED, no physical failure, no
                                           owner / architecture gate, no stop raised; still NOT whole-design compliant
      whole_design_compliant               strictly: geometric candidate, every mandatory lane RESOLVED_GEOMETRICALLY (no supplier,
                                           owner or architecture gate open), every hard check PASS (no failed, gated or isolated
                                           physical failure), no stop raised, verdict R1 RESOLVED, no above-limit diagnostic geometry"""
    c = E['classification']
    raised = sorted(s['id'] for s in stops if s['raised'])
    fatal = sorted(s['id'] for s in stops if s['raised'] and s['fatal'])
    protr = bool(E['protrusions'])
    dc = c['D_complete']
    geo = dc is not None and dc <= ceiling + EPS and E['D'] <= ceiling + EPS and not protr and z_delta <= EPS
    owner = [l for l in LANES if disp[l] in ('OWNER_GATED', DISPOSITIONS[4])]
    arch = [l for l in LANES if disp[l] == 'ARCHITECTURE_GATED']
    supp = [l for l in LANES if disp[l] == 'SUPPLIER_GATED']
    phys_fail = sorted(k for k, h in H.items() if h['physical_pass'] is False)
    not_pass = sorted(k for k, h in H.items() if h['study_status'] != 'PASS')
    study = E['D'] <= ceiling + EPS and not fatal
    gcs = geo and study and not owner and not arch and not phys_fail and not raised and \
        all(disp[l] in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED') for l in LANES)
    whole = geo and study and not owner and not arch and not supp and all(disp[l] == 'RESOLVED_GEOMETRICALLY' for l in LANES) \
        and not phys_fail and not not_pass and not raised and verdict == VERDICTS[0]
    return dict(study_candidate=study, geometric_candidate=geo, owner_decision_candidate=study and verdict in (VERDICTS[2], VERDICTS[3]),
                geometry_closed_supplier_gates_open=gcs, whole_design_compliant=whole,
                blocking=dict(owner_gated_lanes=owner, architecture_gated_lanes=arch, supplier_gated_lanes=supp, physical_failures=phys_fail,
                              checks_not_pass=not_pass, stops_raised=raised, D_complete=dc, D_eval=E['D'], unauthorized_protrusions=protr,
                              z_delta_mm=z_delta))


def candidate_summary(E, H, disp, stops, verdict, z_delta, ceiling=51.0):
    resolved = sum(1 for l in LANES if disp[l] in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED'))
    cs = compliance_state(E, H, disp, stops, verdict, z_delta, ceiling)
    return dict(id=E['id'], title=E['cand']['title'], r1_definition=E['cand'].get('r1_definition'), D_eval=E['D'], tw_eval=E['tw'],
                design_rule=E['design_rule'], D_min=E['classification']['D_min'], D_complete=E['classification']['D_complete'],
                D_radial_core=E['classification']['D_radial_core'], D_min_including_extension=E['classification']['D_min_including_extension'],
                D_radial_core_scope='radial core only (H03-OD, H05-GEOM, insertion); never a whole-design compliance statement',
                study_candidate=cs['study_candidate'], geometric_candidate=cs['geometric_candidate'],
                owner_decision_candidate=cs['owner_decision_candidate'],
                geometry_closed_supplier_gates_open=cs['geometry_closed_supplier_gates_open'],
                whole_design_compliant=cs['whole_design_compliant'], compliance_blocking=cs['blocking'],
                unpermitted_protrusions=len(E['protrusions']), z_delta_mm=z_delta,
                resolved_lanes=resolved, dispositions=disp, verdict_if_selected=verdict,
                stops_raised=[s['id'] for s in stops if s['raised']])


SWEEP_TW_COLUMNS = ('tw', 'groups', 'geom_min', 'insertion_min', 'r_lim', 'seal_typed', 'seal_feasible', 'seal_r_lim_fallback', 'seal_flange_top',
                    'charger_plan_prereq_r_lim_margin', 'structure', 'arcs_t', 'lra_lateral', 'charger', 'charger_strict_width')
SWEEP_STRUCTURE_FIELDS = ('method', 'pass_', 'R_mm', 'bound_mm', 'limit_mm', 'n_R', 'bound_min_mm')
SWEEP_SEAL_COLUMNS = ('r_lim', 'seal_flange_top', 'seal_typed', 'seal_feasible', 'seal_r_lim_fallback')
SEAL_ORDER = ('face', 'adhesive', 'radial')


def flags(d, keys):
    return ''.join('1' if d[k] else '0' for k in keys)


def compact_sweep(E):
    """Column-encoded per-point sweep (every (D, tw) point, every group, the per-point structural record and the V03 arc
    choice); decoded by sweep_rows()."""
    rows = []
    arcs = [a['reservation'] for a in E['sweep']['arcs']]
    for r in E['sweep']['rows']:
        tws = []
        for t in r['tw_rows']:
            s_ = t['structure']
            tws.append([t['tw'], flags(t['groups'], TW_GROUPS), t['geom_min'], t['ins_min'], t['r_lim'], [t['seal_typed'][k] for k in SEAL_ORDER],
                        t['seal_feasible'], t['seal_r_lim_fallback'], t['seal_flange_top'], t['charger_plan_prereq_r_lim_margin'],
                        [s_[k] for k in SWEEP_STRUCTURE_FIELDS],
                        [t['arcs_t'][k] for k in arcs], t['lra_lateral'], flags(t['charger'], CHG_SWEEP_FLAGS), t['charger_strict_width']])
        rows.append(dict(D=r['D'], primary=r['primary'], best_tw=r['best_tw'], od_margin=r['od_margin'], cover_fit=r['cover'],
                         button_min_margin=r['button_min'], groups=flags(dict(r['d_groups'], **r['any_tw']), ALL_GROUPS), tw=tws))
    return dict(encoding=dict(tw_columns=list(SWEEP_TW_COLUMNS), groups_order_tw=list(TW_GROUPS), groups_order_D=list(ALL_GROUPS),
                              charger_flags=list(CHG_SWEEP_FLAGS),
                              seal_typed_order=list(SEAL_ORDER), seal_typed_units=list(H11_UNITS_ORDER),
                              seal_typed_rule='R5: per topology, per units group, the minimum over its typed predicates of the population '
                                              'reduction of each predicate (max over the term population of that margin; SEAL_REDUCTION_RULES); '
                                              'never across units, never a representative row; null = no term of that units group',
                              seal_r_lim_rule=SEAL_REDUCTION_RULES['r_lim'], seal_flange_top_rule=SEAL_REDUCTION_RULES['flange_top'],
                              structure_fields=list(SWEEP_STRUCTURE_FIELDS), arcs_order=arcs,
                              arc_fields=['t_arc_mm', 'z_extent (M = MAIN_BATTERY, T = THROUGH_REAR_FACE)', 'own-feasible interval non-empty']),
                rows=rows)


def sweep_rows(sw):
    """Decode compact_sweep() into per-point dicts."""
    enc = sw['encoding']
    out = []
    for r in sw['rows']:
        tws = []
        for row in r['tw']:
            t = dict(zip(enc['tw_columns'], row))
            t['groups'] = {g: c == '1' for g, c in zip(enc['groups_order_tw'], t['groups'])}
            t['structure'] = dict(zip(enc['structure_fields'], t['structure']))
            t['seal_typed'] = dict(zip(enc['seal_typed_order'], t['seal_typed']))
            t['arcs_t'] = dict(zip(enc['arcs_order'], t['arcs_t']))
            t['charger'] = {k: c == '1' for k, c in zip(enc['charger_flags'], t['charger'])}
            tws.append(t)
        out.append(dict(r, groups={g: c == '1' for g, c in zip(enc['groups_order_D'], r['groups'])}, tw=tws))
    return out


def lane_report(E):
    btn, seal, strl, chg, lra = E['btn'], E['seal'], E['strl'], E['chg'], E['lra']
    feats = [dict(id=f['id'], lane=f.get('lane'), material=f.get('material'), conductive=f['conductive'], ferromagnetic=f['ferromagnetic'],
                  kind=f['kind'], z=f['z'], z_lo_nom=f['z_lo_nom'], z_hi_nom=f['z_hi_nom'], z_lo_adv=f['z_lo_adv'], z_hi_adv=f['z_hi_adv'],
                  geom=f['geom']) for f in E['features']]
    return {
        'L-WIN': E['win'],
        'L-RAD': dict(design_point=dict(D=E['D'], tw=E['tw']), carrier=dict((k, v) for k, v in E['sweep']['carrier'].items()),
                      arcs=E['row']['arcs'], margins=E['row']['margins'], wall_screens_MPa=E['row']['wall_screens_MPa'],
                      h05_geom=dict(terms=E['row']['h05_geom_terms'], min=E['row']['h05_geom_min'], pass_=E['row']['h05_geom_pass']),
                      h05_lra_coupled=E['row']['lra_coupled'], g4_literal=E['row']['g4_literal'], insertion=E['row']['insertion'],
                      classification=E['classification']),
        'L-BTN': btn,
        'L-SEAL': dict(main_seal=seal, flange_top_mm=E['chg']['flange_top_mm'], seal_flange_rows_h14=E['chg']['seal_flange_rows'],
                       inventory=E['inventory'], closure=E['seal_closure'], aperture_feasible=E['aperture_feasible'], screws=dict(
                           (k, v) for k, v in E['screws'].items() if k != 'screws'), vent_land_mm=E['vent_land'], window_land_mm=E['window_land'],
                       conditional_U6F3=[dict((k, v) for k, v in c.items() if k not in ('gland',)) for c in E['conditional']],
                       retired=['S-POD-FRAME (P2 retired by C-R1-07)']),
        'L-CHG': dict(selected=dict(pose=dict((k, chg['pose'][k]) for k in ('orientation', 'r_centre', 'az_centre', 'land', 'block_mm', 'position_tol',
                                                                             'block_poly', 'land_poly', 'block_rmax', 'land_rmax', 'land_rmin', 'block_top_mm',
                                                                             'land_top_mm', 'land_side_overshoot_mm', 'land_az', 'radiator_distance_mm',
                                                                             'margins', 'margins_deg', 'predicates', 'categories', 'diagnostics',
                                                                             'prereq_pass')),
                                    flange_margins=chg['flange_margins'], min_margin=chg['min_margin'], categories=chg['categories'], pass_=chg['pass_'],
                                    diagnostics=chg['diagnostics'], land_v_z=chg['land_v_z'],
                                    r_lim=chg['r_lim'], land_top_mm=chg['land_top_mm'], block_top_mm=chg['block_top_mm'], flange_top_mm=chg['flange_top_mm'],
                                    neighbours=dict(pass_=chg['neighbours']['pass_'], evaluated=chg['neighbours']['evaluated'],
                                                    rows='typed terms of R1-H14 (candidate_hard_checks)'),
                                    governing=chg_governing_summary(chg['governing']),
                                    strict_wedge=dict(dict((k, v) for k, v in chg['strict_wedge'].items() if k not in ('pose', 'rows', 'governing')),
                                                      governing=chg_governing_summary(chg['strict_wedge']['governing']))),
                      by_seal_topology={t: dict(dict((k, v) for k, v in s.items() if k != 'evaluations'),
                                                evaluations=[dict(rows=x['rows'], r_lim=x['r_lim'], flange_top_mm=x['flange_top_mm'], min_margin=x['min_margin'],
                                                                  prereq_pass=x['prereq_pass'], categories=x['categories'], pass_=x['pass_'],
                                                                  pose=[x['pose']['orientation'], x['pose']['r_centre'], x['pose']['az_centre']])
                                                             for x in s['evaluations']])
                                        for t, s in E['chg_by_topology'].items()},
                      poses_evaluated=len(E['sweep']['poses']), literal_c_r1_01=E['chg_literal'], route_rows=chg['pose']['route_rows'],
                      strict_wedge_diagnostic=E['strict_wedge'], feedthrough=E['ft'], truncation='none (land never truncated)'),
        'L-STR': dict(dict((k, v) for k, v in strl.items()),
                      design_point_bound=dict((k, v) for k, v in E['structure_design_point'].items()),
                      structure_by_D=E['classification']['structure_by_D']),
        'L-ASM': E['asm'],
        'L-LRA': dict((k, v) for k, v in lra.items() if k != 'best_plan_env'),
        'features': feats,
        'rf_mag': dict(rf_intrusions=E['rf']['rf_intrusions'], mag_violations=E['rf']['mag_violations'],
                       conductive_distances=E['rf']['conductive_distances']),
        's14_untouched': E['s14'], 'supports': E['supports'], 'post_load': E['post'], 'forbidden_loads': E['forbidden'],
        'closure_clearances': E['closure'], 'lra_structural_rescreen': E['lra_rescreen'], 'r_case_unpermitted': E['protrusions'],
        'design_point_g4_terms': E['dp'], 'sweep': compact_sweep(E),
        'module_features': [dict(id=f['id'], kind=f['kind'], z=f['z'], z_lo_adv=f['z_lo_adv'], z_hi_adv=f['z_hi_adv']) for f in E['module']],
    }


def study_rank_key(Es, per):
    return lambda cid: (-sum(1 for l in LANES if per[cid]['disp'][l] in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED')),
                        Es[cid]['classification']['D_min'] if Es[cid]['classification']['D_min'] is not None else 99.0,
                        Es[cid]['classification']['D_radial_core'] if Es[cid]['classification']['D_radial_core'] is not None else 99.0, cid)


def study_core(cx, in_proc, scope, Es=None):
    """The production study of every candidate in one context: candidate evaluation (sweep, classification, design point, lanes),
    hard checks, lane dispositions, stops, per-candidate verdicts, ranking and the study verdict (G4_R1_BRIEF section 10)."""
    Es = Es if Es is not None else {c['id']: evaluate_candidate(cx, c) for c in cx.cands}
    per = {}
    for cid, E in Es.items():
        H = hard_checks(cx, E, in_proc, scope)
        per[cid] = dict(H=H, disp=lane_dispositions(E, H))
    for cid, E in Es.items():
        per[cid]['stops'] = stops_of(cx, E, per[cid]['H'], per[cid]['disp'], list(Es.values()), in_proc, scope)
        per[cid]['verdict'] = verdict_of(per[cid]['disp'], per[cid]['stops'])
    order = sorted(Es, key=study_rank_key(Es, per))
    return Es, per, order, order[0], per[order[0]]['verdict']


def build_r1_results(timing=None):
    t0 = time.time()
    EVAL['n'] = 0
    r1in = load_json(IN_PATH)
    bad = input_violations(r1in)
    if bad:
        raise StudyError('STOP: R1 inputs contain result-like keys: ' + ', '.join(bad))
    bad = input_contract_violations(r1in)
    if bad:
        raise StudyError('STOP: R1 input contract transcription: ' + '; '.join(bad))
    in_proc = run_g4_in_process()
    st = in_proc['st']
    if not frozen_seal_windows_ok(st, load_json(MECH / 'inputs/g4_case_sealing.json')):
        raise StudyError('STOP: O-ring windows / cross-section tolerance differ from the accepted G4 values')
    cx = Ctx(st, r1in, in_proc['res'])
    scope = r1_scope(r1in)
    Es, per, order, lead, verdict = study_core(cx, in_proc, scope)
    ceiling = r1in['parameters']['V01_D_case_body']['ceiling_mm']
    for cid in Es:
        per[cid]['z_delta'] = z_delta_of(cx, Es[cid]['features'])
        per[cid]['compliance'] = compliance_state(Es[cid], per[cid]['H'], per[cid]['disp'], per[cid]['stops'], per[cid]['verdict'],
                                                  per[cid]['z_delta'], ceiling)
    cl = per[lead]['compliance']
    selectable = cl['whole_design_compliant'] or cl['geometry_closed_supplier_gates_open']
    xchk = lead_crosschecks(cx, Es)
    anchors = solver_anchors(cx, Es)
    E = Es[lead]
    oq = owner_questions(E, per[lead]['disp'], per[lead]['stops'])
    readiness = owner_question_readiness(E, oq, per[lead]['H'], per[lead]['stops'])
    res = dict(
        schema='sportwatch-g4-r1/2', contract=BRIEF, evidence_class='PROJECT_DERIVED',
        status='R1 study result (uncommitted; independent review pending). No G4 verdict is emitted; nothing downstream is authorized.',
        verdict=verdict, verdict_rule='verdict_of(lane dispositions, stops) of the ranking leader (G4_R1_BRIEF section 10)',
        owner_decisions=r1in['owner_decisions'],
        lead_adjudications=r1in['lead_adjudications'],
        g4_owner_decisions_unchanged=[o['id'] for o in st.I['owner_decisions']],
        decisions_not_taken=['OD-G4-LRA-ARCH', 'OD-G4-STACK', 'OD-G4-MATERIAL', 'serviceability tradeoff', 'case-diameter relaxation',
                             'G2 reopening', 'G3 reopening'],
        carry_in=dict(baselines=r1in['baselines'], legacy=dict(rows=st.legacy['rows'], pass_=st.legacy['pass_']),
                      g2_stacks={k: v['reproduced'] for k, v in st.z.items()}, z_model=cx.zm,
                      g4_in_process=dict(pass_=in_proc['pass_'], failures=in_proc['fails'], selftests=in_proc['tests'], caught=in_proc['caught'],
                                         allowed_changes_extension=in_proc['extension'], extension_exact=in_proc['extension_exact']),
                      r1_files=sorted(R1_FILES)),
        scope=scope,
        z=dict(g4_z_delta_mm=dict(nominal=0.0, rss=0.0, linear=0.0),
               r1_added_layers=[], rule='R1 adds no Z layer; every caseback-side feature is checked against Z=0 and the LA-Z-2 band (R1-H01)',
               headroom=cx.g4_res['z']['rows']),
        search=dict(primary_grid=dict(start=r1in['parameters']['V01_D_case_body']['start'], stop=r1in['parameters']['V01_D_case_body']['stop'],
                                      step=r1in['parameters']['V01_D_case_body']['step']),
                    report_extension_stop=r1in['parameters']['V01_D_case_body']['report_stop'],
                    stages=['stage 1: radial / core over D x tw with rcin, tcw solved from their predicates and the V03 local-wall search '
                            '(affine interval reduction verified with production predicates)',
                            'stage 2: lane searches per (D, tw) point (seal topology x cs x flange, literal C-R1-01 charger pose grid, button boss x '
                            'd_p x topology x interpretation, STRUCTURE per point over every admissible t_in x t_out x spokes x width x height x '
                            'phase by the compliance bound or the exact search, LRA material x t_out x pocket x class x pose x lead / exit)',
                            'stage 3: intersection of every group at one (D, tw) point; ranking (resolved lanes desc, D_min asc, '
                            'D_radial_core asc, id); selection only for a whole-design-compliant candidate'],
                    structure=dict(points={c: sum(len(r['tw_rows']) for r in Es[c]['sweep']['rows']) for c in Es},
                                   methods={c: sorted({t['structure']['method'] for r in Es[c]['sweep']['rows'] for t in r['tw_rows']}) for c in Es},
                                   R_values_evaluated={c: sum(t['structure']['n_R'] for r in Es[c]['sweep']['rows'] for t in r['tw_rows']) for c in Es},
                                   relaxed_models={c: len([k for k in cx.relaxed_cache if k[0] == c]) for c in Es} if hasattr(cx, 'relaxed_cache') else {},
                                   min_bound_mm={c: min([t['structure']['bound_min_mm'] for r in Es[c]['sweep']['rows'] for t in r['tw_rows']
                                                         if t['structure']['bound_min_mm'] is not None], default=None) for c in Es}),
                    evaluations=EVAL['n'], budget=r1in['budgets']['evaluations_budget']),
        candidates=[candidate_summary(Es[c], per[c]['H'], per[c]['disp'], per[c]['stops'], per[c]['verdict'], per[c]['z_delta'], ceiling)
                    for c in order],
        ranking=dict(order=order, leader=lead, selection_permitted=selectable, selected=lead if selectable else None,
                     selected_D=Es[lead]['classification']['D_complete'] if selectable else None,
                     selection_basis=('whole-design compliant' if cl['whole_design_compliant'] else
                                      ('geometry closed, supplier gates open (NOT whole-design compliant)' if selectable else None)),
                     rule='R3-7: selection only for a leader that is whole-design compliant or in the brief\'s geometry-closed / supplier-'
                          'gates-open state (every lane resolved or supplier-gated at D_complete <= 51.00, no physical failure, no owner / '
                          'architecture gate, no stop); an architecture-, owner- or supplier-gated mandatory lane is never whole-design '
                          'compliance'),
        dispositions=per[lead]['disp'], hard_checks=per[lead]['H'], stops=per[lead]['stops'],
        candidate_hard_checks={c: per[c]['H'] for c in order}, candidate_stops={c: per[c]['stops'] for c in order},
        lanes={c: lane_report(Es[c]) for c in order},
        owner_questions=oq, owner_question_readiness=readiness, lead_crosschecks=xchk, solver_anchors=anchors,
        model_decisions=MODEL_DECISIONS,
        handoff_to_g4_closure=dict(
            status='DIAGNOSTIC; R1 authorizes nothing downstream', leader=lead, dispositions=per[lead]['disp'],
            D=dict(eval=E['D'], D_min=E['classification']['D_min'], D_radial_core=E['classification']['D_radial_core'],
                   margin_to_51=(51.0 - E['classification']['D_radial_core']) if E['classification']['D_radial_core'] else None),
            wall_map=E['row']['arcs'], rib_plate=dict(selected=E['strl']['selected'], best_ribbed=(E['strl'].get('best_ribbed') or {}).get('config'),
                                                     stiffness=(E['strl'].get('best_ribbed') or {}).get('stiffness_at_r_rib_out')),
            buttons={s: dict(I_SUM=r['best']['I-SUM']['min_margin'], I_MAX=r['best']['I-MAX']['min_margin'], T3=(r['T3'] or {}).get('status'))
                     for s, r in E['btn']['switches'].items()},
            seals=E['inventory']['seals'], charger=dict(pose=[E['chg']['pose']['orientation'], E['chg']['pose']['r_centre'], E['chg']['pose']['az_centre']],
                                                        categories=E['chg']['categories'], closed=E['chg']['pass_'],
                                                        overshoot_mm=E['chg']['pose']['land_side_overshoot_mm'], strict_wedge=E['strict_wedge']),
            lra=dict(envelopes=E['lra']['envelopes'], delta_Z_mm=E['lra']['delta_Z_mm'], trigger=E['lra']['od_g4_lra_arch_triggered']),
            charger_literal=E['chg_literal'], assembly_dependencies=E['asm']['dependencies'],
            fea=st.I['fea_load_cases'], atm_q=st.I['atm_q'], open_owner_questions=[q['id'] for q in oq],
            c_r1_03_adjudication=r1in.get('c_r1_03_adjudication')),
        claims='No 5 ATM, structural, optical, adhesive, RF, MPN or supplier qualification is claimed anywhere.')
    if timing is not None:
        timing['study_s'] = time.time() - t0
        timing['in_proc'] = in_proc
        timing['cx'] = cx
        timing['Es'] = Es
    return json.loads(dumps(res)), cx, in_proc, Es


MODEL_DECISIONS = [
    'Local arcs (C-R1-04) span the corridor reservation Z levels (MAIN, BATTERY); when the crossing envelope cannot pass the bulk '
    'REAR-level bore at rear insertion the arc is extended through the rear face, reducing the rear-face seal annulus there.',
    'V03 (R2-2): the local wall is searched on the contracted grid floor .. tw step 0.02 by an exact reduction. Every decreasing own predicate '
    '(edge, straight, t_allow, insertion through the arc) is affine in t with slope -1 (R_side = D/2 - t), the wall predicate affine with '
    'slope +1, hoop and panel stresses fall strictly with t; the own-feasible set is therefore the interval [t_lo, t_hi]. Coupled predicates '
    'are monotone: the rear-face seal annulus and the radial spigot bore rise with t and the structural plate radius falls with t. A '
    'through-rear-face arc takes t_hi; a MAIN / BATTERY arc (no coupled predicate) takes the grid max-min of its own mm margins; an empty '
    'interval is diagnostic (H05-GEOM fails there for every thickness). The floor is NOT claimed optimal for every predicate (wall, hoop, '
    'panel, annulus and plate radius all favour a thicker arc). The affine model is verified against production predicates at the selected '
    'point, the last grid point and the t_hi bracket; STRUCTURE is re-screened at every plate radius reachable by an admissible arc thickness.',
    'H05 straight-run and edge crossings are evaluated at the non-LRA risers inside the local arcs; the U7 riser straight run and XL-LRA '
    'lateral / Z terms are H05-LRA-COUPLED (R1-H05), never blended into H05-GEOM.',
    'The charger contact block is a caseback feedthrough (FT-B / FT-C), not module-carried; the REAR insertion envelope uses the S14 outline '
    'and the REAR conductor reservations (the G4-literal module-carried value is reported beside it).',
    'R4-3: C-R1-01 2(v) "in plan and in Z" is applied to its subject, the NON-CONDUCTIVE LAND (contract-mandated; a Z separation never '
    'waives a plan collision, exact g4.overlaps, touching counts). The conductive block is held to C-R1-01 item 1 and to the common strict '
    '3-D clearance (plan OR Z; G4 8.8 / H20 "block ... clear"), because no contract clause states a plan-AND-Z rule for it; the block-AND-Z '
    'screen is reported as R1 model conservatism and never decides. Every H14 term carries one category (contract_mandated, '
    'physical_required_elsewhere, conservative_model_diagnostic, supplier_diagnostic); the contract is not amended or reinterpreted.',
    'R3-3: one strict clearance rule for every physical clearance predicate (plan or Z): a gap separates only when > EPS; a zero gap '
    '(touching) is a collision, a negative gap an overlap. Allocation-fit checks (a feature inside its Z allocation, D <= 51.00, margins '
    'against a required clearance c > 0) keep the accepted G4 margin >= 0 convention. The charger block modelled at its SR-CHG-MECH '
    'allocation height therefore fits its allocation (R1-H01) with a zero Z gap to the CHG_ROUTE / CHG_LINK conductor band; it is plan-'
    'separated from them, so it is not a 3-D collision (R4-7); the zero Z gap fails only the conservative block-AND-Z screen.',
    'R4-4: under the retained G4 Z model the land [0, h_land] and every 2(v) screw / support [z_lo <= 0, H] share the Z = 0 datum, so '
    'Z_gap = max(z_lo - h_land, -H) <= -min(h_land, H) <= 0: the land\'s conjunctive 2(v) clause is unsatisfiable for every pose, D and land '
    'width - a contract / owner question (Q-R1-CHARGER), not generalized to the block or the strict-wedge alternative.',
    'R4-8: R1-H11 is a set of individually typed terms (dimensionless compression / fill ratios, mm annuli / residuals / Z, booleans); '
    'physical pass is the boolean conjunction of its predicates; no minimum or ranking is ever taken across units (per-units governing '
    'terms only; the sweep seal column is per units group).',
    'R5: no physical result depends on a single representative / best seal row. Every authorized cross-section row of every topology is '
    'evaluated independently (its own typed predicates, gland, flange, r_lim, flange top, H14 flange rows and radial supplier land '
    'width); topology feasibility = any(r.pass_all); the coupled topology is a boolean / fixed-order rule (first closing topology face, '
    'radial, adhesive; else the face fallback, not closed); the coupled r_lim is the min and the adverse flange top the max over the '
    'coupled population; R1-H11 terms are per-predicate max reductions over the fully feasible rows (else every authorized row); the '
    'radial supplier land threshold is the min over the authorized radial rows; owner thresholds are the rows a boolean predicate '
    'defines. The reductions run in the seal internal length unit (mm / m / um regression) with unit-scaled tolerances. A representative '
    'row is chosen afterwards for display only (booleans, a count, then one homogeneous quantity per key component) and has no '
    'physical consumer (zero-feedback regression with first / last / refusing rows).',
    'R3-1: the charger is evaluated at EVERY (D, bulk wall) point against the complete neighbour set of that point (screws, lug arms, spring '
    'bars and button bores / bosses of that D and wall; seal flange and local arcs of that point; CHG_ROUTE / CHG_LINK; case-side supports, '
    'stop pads and vent by their exact frozen-window envelopes, re-checked against the exact g4 placements at the design point and sampled '
    'points; ribs at the design point) in five separate categories - radial prerequisite, plan prerequisite, Z prerequisite, complete '
    'neighbour set, literal closure. Only the literal category closes the charger; a prerequisite is never labelled a closure.',
    'R3-2: the strict-wedge supplier path is the exact g4.charger_fit wedge geometry at its zero-margin land width (orientation 0, azimuth '
    '90, unique zero-margin centre), judged like every pose against the complete same-point neighbour set; its width is a supplier '
    'zero-margin threshold only (land < width strictly) and is never credited; the authored adverse land stays 1.000 mm.',
    'R4-1: an exact LRA structural fallback is bound to a canonical physical identity (candidate, plate t_in / t_out / depth / residual, '
    'materials and process tolerances, pocket band / footprint / angular interrupter, r_lim, pose and class derived from the evaluated '
    'circles, body / lead / exit envelopes, Z fit incl. mount allowance, plan re-check, structural geometry and rib interrupters, charger '
    'block / land, seal flange, plan exclusions incl. supports); only the rib configuration is free; the evaluated identity is derived '
    'from what the fallback consumed, must equal the claimed identity, and the validator reconstructs it independently from the emitted '
    'design point and the authoritative inputs and re-runs the fallback.',
    'R3-5: only R1-H05 and R1-H19 may be isolated to L-LRA (immutable allow-set; the validator enforces its own copy with the LRA-coupled '
    'semantics); R3-6: every numeric threshold of a GATED / FAIL numeric check is recomputed by the validator from the inputs and fresh '
    'predicates; R3-7: whole-design compliance is strict and kept apart from the study / geometric / owner-decision / supplier-gates-open states.',
    'Conductor / wiring reservations have ONE authoritative physical record each (R2-4): the REAR portion lies in the LA-Z-2 band; the '
    'retained G4 wiring entries, the module-side clearance set and the charger route predicates are views of that record (checked).',
    'Structural spokes end at min(seal r_lim, case-side post inner radius) - c_insert; S14 tail / thermode / U6 / support polygons and the '
    'charger land interrupt spokes; ring stiffness is never credited (LA-STR-4).',
    'STRUCTURE is evaluated at every (D, tw) point with that point\'s plate radius, rib interruptions, charger pose and split radius (R2-1); '
    'no endpoint result is propagated. Minimum-potential-energy bound: the relaxed model is the Loewner maximum over every admissible '
    'configuration of the Screen-B constitutive matrix (smeared rib stiffness at the subregion inner radius; D_r falls strictly with rib '
    'spacing), so every configuration has compliance >= C_relaxed and continuum deflection >= C_relaxed / (q pi R^2); where that is >= the '
    'deflection limit the point fails Screen B for every configuration, otherwise the exact configuration search decides. The dominance is '
    'verified with production regions at every design point; the Screen-A / Screen-B equations are unchanged.',
    'LRA envelopes are reported separately and labelled (R2-3): historical optimistic bound, continuous mathematical upper bound, authored-'
    'grid maximum, selected design-point envelope and structurally feasible searched envelope; only the last three are search results and '
    'only the last is structurally qualified. Every joint-search combination receives the structural re-screen (a pocket only thins the '
    'plate and only enlarges rib gaps, so the design-point relaxed model dominates every pocketed variant); supplied classes carry their lead '
    '/ exit envelope in every plan and Z test.',
    'Assembly (R2-5): the A1..A11 sequence geometry is evaluated on its own; A1 / A5 / A9 / A10 / A11 product-closure dependencies on other '
    'lanes are reported per step and a physically failed dependency makes L-ASM owner-gated; the product is never reported executable then.',
    'The LRA ceiling deducts the LA-Z-2 conductor band (accepted as conservative); the lead / brief formulas without the band are reported beside it.',
    'R1-S10 (whole-design) is evaluated on the radial core (H03-OD, H05-GEOM, insertion); D thresholds of other lanes above 51.00 mm are '
    'owner-question numbers and are never selected. Whole-design guard (R2-7): no selected / recommended / compliant candidate may have '
    'D > 51.00, an unauthorized protrusion or an above-limit diagnostic geometry; radial-core feasibility is never whole-design compliance.',
]


# --------------------------------------------------------------------------------------------
# Markdown report (derived only from the result object)
# --------------------------------------------------------------------------------------------
def cellv(v):
    if v is None:
        return 'n/a'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float):
        return ('%+.3e' % v) if (v != 0.0 and abs(v) < 0.01) else fs(v)
    if isinstance(v, (list, tuple)):
        return ', '.join(cellv(x) for x in v) or '-'
    return str(v).replace('|', '/').replace('\n', ' ')


def md_table(o, headers, rows):
    o.append('| ' + ' | '.join(headers) + ' |')
    o.append('| ' + ' | '.join('---' for _ in headers) + ' |')
    for r in rows:
        o.append('| ' + ' | '.join(cellv(x) for x in r) + ' |')
    o.append('')


def d_ranges(rows, key):
    """Compress a per-D boolean into 'a..b' runs."""
    runs, cur = [], None
    for r in rows:
        if r[key]:
            cur = [r['D'], r['D']] if cur is None else [cur[0], r['D']]
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    return ', '.join('%.2f..%.2f' % (a, b) for a, b in runs) or 'none'


def render_md(res):
    lead = res['ranking']['leader']
    L = res['lanes'][lead]
    o = ['# G4-R1 case / seal / support blocker-resolution study (Rev-A)', '', '**%s**' % res['verdict'], '',
         res['status'], '', res['claims'], '',
         'Leader (diagnostic ranking): **%s**. Selection permitted: **%s**; selected: %s; selected D: %s.' % (
             lead, cellv(res['ranking']['selection_permitted']), cellv(res['ranking']['selected']), cellv(res['ranking']['selected_D'])), '',
         '## 1. Lane dispositions (%s)' % lead, '']
    md_table(o, ['Lane', 'Disposition'], [(k, v) for k, v in sorted(res['dispositions'].items())])
    o += ['## 2. Candidates and derived diameters', '']
    md_table(o, ['Candidate', 'D_min', 'D_complete', 'D_radial_core (radial core only)', 'study candidate', 'geometric candidate',
                 'owner-decision candidate', 'geometry closed, supplier gates open', 'whole-design compliant', 'D_eval', 'tw_eval', 'resolved lanes',
                 'verdict if selected', 'stops raised'],
             [(c['id'], f2(c['D_min']), f2(c['D_complete']), f2(c['D_radial_core']), c['study_candidate'], c['geometric_candidate'],
               c['owner_decision_candidate'], c['geometry_closed_supplier_gates_open'], c['whole_design_compliant'], f2(c['D_eval']), f2(c['tw_eval']),
               c['resolved_lanes'], c['verdict_if_selected'], c['stops_raised']) for c in res['candidates']])
    o += ['Whole-design compliant (R3-7) requires every lane RESOLVED_GEOMETRICALLY, every hard check PASS, no stop, D_complete <= 51.00, no '
          'protrusion and zero Z delta; an architecture-, owner- or supplier-gated mandatory lane is never compliance. Blocking items: ' +
          '; '.join('%s: owner %s, architecture %s, supplier %s, physical failures %s' % (
              c['id'], ', '.join(c['compliance_blocking']['owner_gated_lanes']) or '-', ', '.join(c['compliance_blocking']['architecture_gated_lanes']) or '-',
              ', '.join(c['compliance_blocking']['supplier_gated_lanes']) or '-', ', '.join(c['compliance_blocking']['physical_failures']) or '-')
              for c in res['candidates']) + '.', '']
    o += ['D_min is the first primary-grid diameter at which every D-dependent non-LRA group passes at ONE (D, bulk wall) point; `n/a` '
          'means none at <= 51.00 mm. D_radial_core covers H03-OD, H05-GEOM and insertion only and is never a whole-design statement '
          '(R2-7). Every group, STRUCTURE included, is the result of that exact point (R2-1).', '']
    for c in res['candidates']:
        g = res['lanes'][c['id']]['L-RAD']['classification']['groups']
        o.append('- %s group first / last pass D: %s' % (c['id'], '; '.join('%s %s..%s' % (k, cellv(v['first_pass_D']), cellv(v['last_pass_D']))
                                                                          for k, v in sorted(g.items()))))
    o += ['', '### 2.1 Structural feasibility by D (per point, R2-1)', '']
    md_table(o, ['Candidate', 'points', 'plate radii screened', 'methods', 'D with STRUCTURE passing', 'minimum deflection bound mm', 'limit mm'],
             [(cid, sum(x['points'] for x in res['lanes'][cid]['L-STR']['structure_by_D']),
               sum(x['R_values'] for x in res['lanes'][cid]['L-STR']['structure_by_D']),
               sorted({m for x in res['lanes'][cid]['L-STR']['structure_by_D'] for m in x['methods']}),
               d_ranges(res['lanes'][cid]['L-STR']['structure_by_D'], 'pass_any_tw'),
               min([x['bound_min_mm'] for x in res['lanes'][cid]['L-STR']['structure_by_D'] if x['bound_min_mm'] is not None], default=None),
               res['lanes'][cid]['L-STR']['structure_by_D'][0]['limit_mm']) for cid in res['ranking']['order']])
    o += ['COMPLIANCE_BOUND: the Loewner-maximal admissible plate gives a continuum deflection lower bound C / (q pi R^2) >= the limit, so '
          'every admissible configuration fails Screen B at that point; GEOMETRY: no admissible caseback thickness window. Coupled '
          'thresholds (first D with the named groups at ONE point): ' + '; '.join(
              '%s %s' % (cid, cellv(json.dumps(res['lanes'][cid]['L-RAD']['classification']['coupled_first_D'], sort_keys=True)))
              for cid in res['ranking']['order']), '']
    o += ['## 3. Hard checks R1-H01 .. R1-H20 (%s)' % lead, '']
    md_table(o, ['ID', 'study_status', 'physical_pass', 'margin', 'units', 'governing term', 'threshold value', 'threshold units', 'required delta',
                 'required delta units', 'gate_ids', 'evidence_complete', 'owning lane', 'G4-literal'],
             [(h['id'], h['study_status'], h['physical_pass'], h['margin'], h['units'],
               (h['typed'] or {}).get('governing', {}).get('term_id') if h.get('typed') else (h['governing_terms'] or {}).get('governing_term'),
               h['threshold_value'], h['threshold_units'], h['required_delta'], h['required_delta_units'], h['gate_ids'],
               h['evidence_complete'], h['owning_lane'], '%s %s' % (h['g4_literal']['g4_check'], 'pass' if h['g4_literal']['pass_'] else 'fail'))
              for h in sorted(res['hard_checks'].values(), key=lambda x: x['id'])])
    o.append('Margin, threshold and required delta are separate typed pairs (units per column). R1-H11 and R1-H14 carry individually typed '
             'terms (sections 7 and 9); no minimum is taken across units or categories.')
    o.append('')
    for h in sorted(res['hard_checks'].values(), key=lambda x: x['id']):
        o.append('- **%s** %s: %s' % (h['id'], h['study_status'], h['title']) + (' Threshold: %s.' % h['threshold'] if h.get('threshold') else ''))
    o += ['', '## 4. Stops R1-S01 .. R1-S13', '']
    md_table(o, ['Stop', 'raised', 'scope', 'derivation'], [(s['id'], s['raised'], 'whole run' if s['fatal'] else 'lane', s['detail']) for s in res['stops']])
    o += ['## 5. Structure (L-STR, %s)' % lead, '']
    S = L['L-STR']
    md_table(o, ['Screen', 'governing sigma MPa', 'region', 'r mm', 'stress margin MPa', 'w max mm', 'deflection margin mm', 'pass'],
             [(x, S[k]['sigma_governing_MPa'], S[k]['governing_region'], S[k]['governing_radius_mm'], S[k]['stress_margin_MPa'], S[k]['w_max_mm'],
               S[k]['deflection_margin_mm'], S[k]['pass_']) for x, k in (('Screen B (governs)', 'screen_B'), ('Screen A (reported)', 'screen_A'))])
    o.append('Selected configuration: %s; rib layout gap %s deg; configurations evaluated: %d.' % (
        cellv(S['selected']), cellv(S['rib_layout']['gap_deg']), S['configs_evaluated']))
    db = S['design_point_bound']
    o.append('Design-point bound (R2-1): %s, deflection lower bound %s mm vs limit %s mm; relaxed model dominance verified on %d admissible '
             'configurations; maximum deflection at the rigid boss on every searched configuration: %s.' % (
                 db['record']['method'], f3(db['record']['bound_mm']), f3(db['record']['limit_mm']), db['configs_checked'],
                 cellv(db['exact_search']['w_max_at_boss_all_configs'])))
    if S.get('best_ribbed'):
        br = S['best_ribbed']
        o.append('Best ribbed configuration: %s, Screen B %s MPa / %s mm, Screen A %s MPa; D_r / D_plate at the outer rib radius %s.' % (
            cellv(br['config']), fs(br['screen_B']['sigma_governing_MPa']), fs(br['screen_B']['w_max_mm']), fs(br['screen_A']['sigma_governing_MPa']),
            fs(br['stiffness_at_r_rib_out']['ratio'])))
    th = S['thresholds']
    md_table(o, ['Material', 'required uniform nominal t mm', 'required outer t (t_in max) mm', 'rigid annulus clamped / ss MPa'],
             [(k, v['required_uniform_nominal_thickness_mm'], v['required_outer_effective_thickness_with_t_in_max_mm'],
               '%s / %s' % (fs(v['rigid_outer_annulus_bound_MPa']['clamped_at_r_step']), fs(v['rigid_outer_annulus_bound_MPa']['simply_supported_at_r_step'])))
              for k, v in sorted(th.items()) if isinstance(v, dict)])
    o.append('Forbidden branches: %s.' % '; '.join('%s contact %s load %s' % (k, cellv(v['contact']), cellv(v['load_N']))
                                                 for k, v in sorted(L['forbidden_loads']['branches'].items())))
    an = res['solver_anchors']
    o += ['', 'Anchors: isotropic limit max rel %.2e (allowed %.0e); no-rib %.3f MPa / %.6f mm; h_rib = 0 gives D_r == D_plate: %s; N vs 2N rel %.2e / %.2e; '
          'exact compliance integral vs 1201-point trapezoid rel %.1e.' % (
              max(max(v for k, v in d.items() if k != 'regions') for d in an['isotropic_limit']), an['max_rel_allowed'],
              an['no_rib_anchor']['sigma_MPa'], an['no_rib_anchor']['w_mm'], cellv(an['h_rib_zero']['equal']),
              an['convergence_best_ribbed']['rel_sigma'], an['convergence_best_ribbed']['rel_w'], an['compliance_integral']['rel']), '']
    o += ['## 6. Radial and V03 local walls (L-RAD, %s)' % lead, '']
    R = L['L-RAD']
    md_table(o, ['Arc', 'material', 'Z extent', 'grid mm', 'own-feasible t_lo..t_hi', 'selected t', 'rule', 'wall', 'edge', 'straight', 'insertion',
                 'edge at floor', 'hoop margin MPa'],
             [(a['reservation'], a['local_material'], a['z_extent'], '%s..%s' % (f2(a['search']['grid_mm'][0]), f2(a['search']['grid_mm'][1])),
               '%s..%s' % (f2(a['search']['t_lo_mm']), f2(a['search']['t_hi_mm'])) if a['search']['feasible'] else 'empty',
               a['t_arc_mm'], a['search']['rule'].split(':')[0], a['wall_margin_mm'], a['edge_margin_mm'], a['straight_margin_mm'],
               a['insertion_margin_mm'], a['search']['at_floor']['edge_margin_mm'], a['hoop_margin_MPa']) for a in R['arcs']])
    o.append('H05-GEOM min %s (pass %s); H05-LRA-COUPLED %s; carrier rcin %s / tcw %s (pack %s).' % (
        fs(R['h05_geom']['min']), cellv(R['h05_geom']['pass_']), cellv(json.dumps(R['h05_lra_coupled'], sort_keys=True)),
        fs(R['carrier']['rcin']), fs(R['carrier']['tcw']), fs(R['carrier']['pack_margin_mm'])))
    o += ['', '## 7. Main seal (L-SEAL, %s)' % lead, '']
    ms = L['L-SEAL']['main_seal']
    o.append('R5 population evaluation: every authorized cross-section row is evaluated independently; every physical result is an explicit '
             'set reduction over the row population or a boolean subset of it (no representative / best row; internal unit %s, emitted mm). '
             'Rules: %s' % (ms['internal_unit'], '; '.join('%s: %s' % (k, v) for k, v in sorted(ms['reduction_rules'].items()))))
    o.append('')
    rid = lambda ids: ', '.join(ids) if ids else 'none'
    md_table(o, ['Topology', 'evaluated_rows', 'gland_window_rows (R_gland)', 'fully_feasible_rows', 'feasible', 'term population',
                 'physical envelope (r_lim / flange thickness mm)', 'representative row (display only)'],
             [(t, rid(x['evaluated_rows']), rid(x['gland_window_rows']) if x['gland_window_rows'] is not None else 'n/a', rid(x['fully_feasible_rows']),
               x['feasible'], x['term_population'],
               'r_lim %s..%s; flange %s' % (f3(x['physical_envelope']['r_lim_mm'][0]), f3(x['physical_envelope']['r_lim_mm'][1]),
                                            '%s..%s' % tuple(f3(v) for v in x['physical_envelope']['flange_thickness_mm'])
                                            if x['physical_envelope']['flange_thickness_mm'] else 'none'),
               '%s (cs %s)' % (x['representative_row']['id'], f2(x['representative_row']['cs_mm'])))
              for t, x in ((t, ms['topologies'][t]) for t in SEAL_ORDER)])
    md_table(o, ['Topology', 'predicate', 'units', 'predicate_feasible_rows', 'population reduction (max)', 'rows attaining', 'worst (min)'],
             [(t, k, d['units'], rid(ms['topologies'][t]['predicate_feasible_rows'][k]), d['value'], rid(d['rows_attaining']), d['worst'])
              for t in SEAL_ORDER for k, d in sorted(ms['topologies'][t]['term_reductions'].items())])
    cp = ms['coupled']
    sfr = L['L-SEAL']['seal_flange_rows_h14']['reduction']
    o.append('Coupled seal of the point: topology %s (%s), population %s; caseback r_lim = min over the population %s mm (envelope %s..%s); '
             'adverse flange top = max over the population %s mm (flange thickness %s). H14 seal-flange rows over the population: land '
             'effective clearance min %s mm (envelope term %s), Z gap min %s mm, clear on every row %s; block effective clearance min %s mm, '
             'clear on every row %s.' % (
                 cp['topology'], 'closed' if cp['closed'] else 'fallback, not closed', rid(cp['population']), f3(cp['r_lim_mm']),
                 f3(cp['r_lim_envelope_mm'][0]), f3(cp['r_lim_envelope_mm'][1]), f3(L['L-SEAL']['flange_top_mm']),
                 '%s..%s mm' % tuple(f3(v) for v in cp['flange_thickness_mm']) if cp['flange_thickness_mm'] else 'none (plate)',
                 fs(sfr['CHG_LAND']['effective_clearance_min_mm']), fs(sfr['CHG_LAND']['envelope_effective_clearance_mm']),
                 fs(sfr['CHG_LAND']['z_gap_min_mm']), cellv(sfr['CHG_LAND']['clear_all_rows']), fs(sfr['CHG_BLOCK']['effective_clearance_min_mm']),
                 cellv(sfr['CHG_BLOCK']['clear_all_rows'])))
    o.append('')
    mf = R['classification']['main_seal_first']
    thr = ms['thresholds']
    atc = lambda t: ', '.join('%s %s %s' % (k, fs(v), H11_TERM_TYPES[k][1]) for k, v in sorted((thr[t]['at_that_cs'] or {}).items())) or 'n/a'
    o.append('Owner thresholds: adhesive bulk wall tw >= %s mm; face bulk wall tw >= %s mm at the smallest gland-feasible cs %s mm (typed terms '
             'there: %s); radial smallest gland-feasible cs %s mm (typed terms there: %s). Rear-face annulus (mm): %s. First main-seal grid '
             'closure: %s.' % (
        fs(thr['adhesive']['required_tw_mm']), fs(thr['face']['required_tw_mm']), fs(thr['face']['smallest_feasible_gland_cs']), atc('face'),
        fs(thr['radial']['smallest_feasible_gland_cs']), atc('radial'), '; '.join('%s %s' % (a['where'], fs(a['value'])) for a in ms['annulus']),
        ('D %.2f mm, tw %.2f mm, %s' % (mf['D'], mf['tw'], mf['label'])) if mf else 'none on the grid'))
    o += ['', 'Aperture feasibility: %s. Seal graph closed: %s.' % (cellv(json.dumps(L['L-SEAL']['aperture_feasible'], sort_keys=True)),
                                                                 cellv(L['L-SEAL']['closure']['closed'])), '']
    t11 = res['hard_checks']['R1-H11']['typed']
    o += ['### 7.1 R1-H11 typed terms (R4-8)', '']
    md_table(o, ['Term', 'topology', 'quantity', 'reduction', 'value', 'units', 'threshold', 'pass', 'delta'],
             [(x['id'], x['topology'], x['quantity'], x['reduction'], x['value'], x['units'],
               ('>= %s' % fs(x['threshold'])) if x['units'] != 'bool' else 'true', x['pass_'], x['delta'])
              for t in SEAL_ORDER for x in t11['topologies'][t]['terms']] +
             [(x['id'], '-', x['quantity'], '-', x['value'], x['units'], 'true', x['pass_'], 'n/a') for x in t11['check_predicates']])
    o.append('Topology feasibility (conjunction of its typed terms = any(r.pass_all)): %s. physical_pass = %s (conjunction of the check '
             'predicates). Governing term per units group (no cross-unit ranking): %s. Check-level margin: %s %s (%s).' % (
                 ', '.join('%s %s (fully feasible rows: %s)' % (t, cellv(t11['topologies'][t]['feasible']),
                                                               ', '.join(t11['topologies'][t]['fully_feasible_rows']) or 'none') for t in SEAL_ORDER),
                 cellv(t11['physical_pass']),
                 '; '.join('%s: %s %s %s' % (u, g['term_id'], fs(g['value']), u) for u, g in sorted(t11['governing_by_units'].items())),
                 fs(t11['governing']['value']), t11['governing']['units'], t11['governing']['term_id']))
    o.append('')
    o += ['## 8. Buttons (L-BTN, %s): both C-R1-03 interpretations' % lead, '']
    B = L['L-BTN']
    md_table(o, ['SW', 'T2-R I-SUM', 'T2-R I-MAX', 'T2-F I-SUM', 'T2-F I-MAX', 'legacy G4 bore', 'T1', 'T3'],
             [(sw, r['T2']['T2-R']['I-SUM']['min_margin'], r['T2']['T2-R']['I-MAX']['min_margin'], r['T2']['T2-F']['I-SUM']['min_margin'],
               r['T2']['T2-F']['I-MAX']['min_margin'], r['legacy_G4_bore_margin_mm'], 'regression only (pass %s)' % cellv(r['T1']['pass_']),
               (r['T3'] or {}).get('status')) for sw, r in sorted(B['switches'].items())])
    o.append('Disposition: %s (adjudication %s, binding %s).' % (B['disposition'], cellv(B['c_r1_03_adjudication']), B['binding_interpretation']))
    o += ['', '## 9. Charger (L-CHG, %s): same-point categories (R3-1) and contract attribution (R4-3)' % lead, '']
    C = L['L-CHG']
    lit = C['literal_c_r1_01']
    sel = C['selected']
    p = sel['pose']
    o.append(lit['rule'])
    o.append('')
    o.append('Attribution: ' + lit['attribution']['note'])
    o.append('')
    md_table(o, ['Contract text relied on', 'source', 'verbatim'], [(q['clause'], q['source'], q['text']) for q in lit['attribution']['quotes']])
    swp = lit['strict_wedge_supplier_path']
    vw = lit['v_z_waived_diagnostic']
    md_table(o, ['Category', 'design point', 'first D (any wall)', 'with radial core', 'with radial core + main seal', 'threshold / note'],
             [('radial prerequisite', sel['categories']['radial'], f2(lit['first_D']['first_radial']), f2(lit['first_D']['first_radial_with_radial_core']),
               f2(lit['first_D']['first_radial_with_radial_core_and_main_seal']),
               'r_lim >= %s mm (pose ori %s r %s az %s); prerequisite only' % (
                   f3(lit['radial_prerequisite']['r_lim_required_mm']), cellv((lit['radial_prerequisite']['pose'] or {}).get('orientation')),
                   fs((lit['radial_prerequisite']['pose'] or {}).get('r_centre')), fs((lit['radial_prerequisite']['pose'] or {}).get('az_centre')))),
              ('plan prerequisite', sel['categories']['plan'], f2(lit['first_D']['first_plan']), f2(lit['first_D']['first_plan_with_radial_core']),
               f2(lit['first_D']['first_plan_with_radial_core_and_main_seal']),
               'r_lim >= %s mm (pose ori %s r %s az %s), deficit here %s mm, D at the design wall %s mm; prerequisite only' % (
                   f3(lit['plan_prerequisite']['r_lim_required_mm']), cellv((lit['plan_prerequisite']['pose'] or {}).get('orientation')),
                   fs((lit['plan_prerequisite']['pose'] or {}).get('r_centre')), fs((lit['plan_prerequisite']['pose'] or {}).get('az_centre')),
                   fs(lit['plan_prerequisite']['deficit_mm']), f2(lit['plan_prerequisite']['required_D_at_design_wall_mm']))),
              ('LAND Z prerequisite (contract 2(v))', sel['categories']['z'], f2(lit['first_D']['first_z']), 'n/a', 'n/a', lit['z_prerequisite']['threshold']),
              ('complete neighbour set', sel['categories']['neighbours'], f2(lit['first_D']['first_neighbours']), 'n/a', 'n/a',
               'land: 2(v) plan AND Z, 2(vi) strict 3-D; block: strict 3-D against every neighbour; %d neighbours of the point' % sel['neighbours']['evaluated']),
              ('literal closure (charger closed)', sel['categories']['literal'], f2(lit['first_D']['first_literal']),
               f2(lit['first_D']['first_literal_with_radial_core']), f2(lit['first_D']['first_literal_with_radial_core_and_main_seal']),
               'contract-mandated + physical predicates at one pose'),
              ('DIAGNOSTIC: literal with the 2(v) Z part waived', vw['design_point'], f2(vw['first_D']), f2(vw['first_D_with_radial_core']),
               f2(vw['first_D_with_radial_core_and_main_seal']), vw['label']),
              ('DIAGNOSTIC: block-AND-Z screen (model conservatism)', lit['block_and_z_diagnostic']['pass_'], 'n/a', 'n/a', 'n/a',
               lit['block_and_z_diagnostic']['label']),
              ('strict-wedge supplier path (in land range)', swp['in_land_range'], f2(lit['first_D']['first_sw_in_land_range']), 'n/a', 'n/a', swp['threshold']),
              ('strict-wedge supplier path (plan)', swp['plan'], f2(lit['first_D']['first_sw_plan']),
               f2(lit['first_D']['first_sw_plan_with_radial_core']), f2(lit['first_D']['first_sw_plan_with_radial_core_and_main_seal']),
               'failing: %s' % cellv(json.dumps(swp['failing_terms_by_category'], sort_keys=True))),
              ('strict-wedge supplier path (complete, 2(v) applied to its land)', swp['complete'], f2(lit['first_D']['first_sw_complete']),
               f2(lit['first_D']['first_sw_complete_with_radial_core']), f2(lit['first_D']['first_sw_complete_with_radial_core_and_main_seal']),
               swp['v_applicability']),
              ('DIAGNOSTIC: strict-wedge complete, 2(v) Z part waived', swp['complete_v_z_waived'], f2(lit['first_D']['first_sw_complete_v_z_waived']),
               f2(lit['first_D']['first_sw_complete_v_z_waived_with_radial_core']),
               f2(lit['first_D']['first_sw_complete_v_z_waived_with_radial_core_and_main_seal']), 'supplier threshold path; never a closure')])
    gv = sel['governing']
    o.append('Reported design-point pose (structural land interrupter; closest pose meeting every r_lim-independent radial / plan '
             'prerequisite): ori %s, r %s, az %s, land %s, overshoot %s mm; charger closed: %s. R1-H14 governing term (contract-mandated, mm): '
             '%s %s mm; azimuth-cap margin %s deg (separate units).' % (
                 p['orientation'], fs(p['r_centre']), fs(p['az_centre']), fs(p['land']), fs(p['land_side_overshoot_mm']), cellv(sel['pass_']),
                 gv['governing']['term_id'], fs(gv['governing']['value']), fs(gv['azimuth_cap_margin_deg'])))
    o.append('')
    md_table(o, ['H14 category', 'decides physical pass', 'pass', 'terms', 'minimum by units (term, value)', 'failing terms'],
             [(c_, v['decides_physical_pass'], v['pass_'], v['terms'],
               '; '.join('%s: %s %s' % (u, g['id'], fs(g['value'])) for u, g in sorted(v['minimum_by_units'].items())) or '-',
               ', '.join(v['failing']) or 'none') for c_, v in gv['categories'].items()])
    md_table(o, ['Failing term (design point)', 'category', 'clause', 'value', 'units', 'plan gap mm', 'Z gap mm'],
             [(t['id'], t['category'], res['hard_checks']['R1-H14']['typed']['clauses'][t['clause_id']], t['value'], t['units'], t.get('plan_gap_mm'),
               t.get('z_gap_mm')) for t in gv['failing_terms']])
    lu = lit['z_prerequisite']['land_unsatisfiability']
    bd = lit['block_and_z_diagnostic']
    o.append('R4-4 land 2(v) Z unsatisfiability: %s Scope: %s. Items (z_lo / H / Z gap / -min(h_land, H), mm): %s.' % (
        lu['rule'], lu['scope'], '; '.join('%s %s / %s / %s / %s' % (x['id'], fs(x['z_lo_adv_mm']), fs(x['H_mm']), fs(x['z_gap_mm']), fs(x['bound_mm']))
                                           for x in lu['items'])))
    o.append('')
    swd = C['strict_wedge_diagnostic']
    swr = swd['at_radial_r_lim']
    o.append('R4-7 block / route: %s Block route plan gaps %s; Z gaps %s; strict 3-D clear of the routes: %s. Strict-wedge zero-margin land '
             'widths (supplier thresholds, not credited; R5 per seal row): face / adhesive rows (shared r_lim %s mm) %s mm; radial rows %s; '
             'radial governing supplier threshold = min over the authorized radial rows %s mm (%s), envelope %s..%s mm; adverse authored land '
             '%s mm. Poses: %d evaluated, %d meet every r_lim-independent prerequisite, %d meet every pose-level contract / physical predicate. '
             'Feedthrough %s.' % (
                 bd['note'], cellv(json.dumps(bd['route_plan_gaps_mm'], sort_keys=True)), cellv(json.dumps(bd['route_z_gaps_mm'], sort_keys=True)),
                 cellv(bd['block_3d_clear_of_routes']), f3(swd['face_adhesive_r_lim_mm']), f3(swd['at_face_adhesive_r_lim']),
                 '; '.join('%s cs %s r_lim %s -> %s' % (x['row'], f2(x['cs_mm']), f3(x['r_lim_mm']), f3(x['width_mm'])) for x in swr['rows']),
                 f3(swr['governing_threshold_mm']), ', '.join(swr['governing_rows']), f3((swr['envelope_mm'] or [None])[0]),
                 f3((swr['envelope_mm'] or [None, None])[1]), f3(swp['adverse_authored_land_mm']), lit['poses_evaluated'],
                 lit['poses_meeting_r_lim_independent_prerequisites'], lit['poses_meeting_every_pose_level_predicate'], C['feedthrough']))
    o += ['', '## 10. LRA (L-LRA, %s)' % lead, '']
    Lr = L['L-LRA']
    md_table(o, ['Envelope', 'value mm', 'search result', 'delta_Z to the authored minimum class mm', 'label'],
             [(k, v['value_mm'], v['searched'], Lr['delta_Z_mm'][k], v['label']) for k, v in Lr['envelopes'].items()])
    md_table(o, ['Material', 'residual floor mm', 'continuous upper bound mm', 'authored-grid maximum mm', 'argmax t_out / depth', 'continuous without band',
                 'lead formula without band', 'historical 0.5 residual'],
             [(k, v['residual_floor_mm'], v['continuous_upper_bound_mm'], v['authored_grid_maximum_mm'],
               '%s / %s' % (f2((v['authored_grid_argmax'] or {}).get('t_out_mm')), f2((v['authored_grid_argmax'] or {}).get('depth_mm'))),
               v['continuous_without_band_mm'], v['lead_formula_without_band_mm'], v['historical_0p5_residual_without_band_mm'])
              for k, v in sorted(Lr['material_table'].items())])
    md_table(o, ['Class', 'supplied', 'plan poses', 'envelope height', 'H before structure', 'Z margin before structure', 'structurally feasible fits', 'fits'],
             [(c['id'], c['supplied'], c['plan_feasible_poses'], c['envelope_height_mm'], c['H_before_structure_mm'], c['z_margin_before_structure_mm'],
               c['structurally_feasible_fits'], c['fits']) for c in Lr['classes']])
    o.append('Structural re-screen: %s on %d combinations (design-point bound %s mm vs %s mm). OD-G4-LRA-ARCH triggered: %s (question raised, not decided).' % (
        Lr['structural_rescreen']['method'], Lr['structural_rescreen']['combinations'], f3(Lr['structural_rescreen']['design_point_bound_mm']),
        f3(Lr['structural_rescreen']['limit_mm']), cellv(Lr['od_g4_lra_arch_triggered'])))
    o += ['', '## 11. Assembly (L-ASM, %s)' % lead, '']
    A = L['L-ASM']
    md_table(o, ['Op', 'direction', 'battery', 'sequence pass', 'dependency gate'],
             [(r['id'], r['direction'], r['battery_state'], r['pass_'], r['gate']) for r in A['order_check']])
    md_table(o, ['Step', 'requires', 'state', 'gate'], [(d['step'], d['requires'], d['state'], d['gate']) for d in A['dependencies']])
    o.append('Identity vs accepted A1..A11: %s. Sequence executable on its own geometry: %s. Product closure executable: %s. Disposition %s. %s' % (
        cellv(A['identity']['pass_']), cellv(A['sequence_executable']), cellv(A['product_closure_executable']), A['disposition'], A['service']))
    o += ['', '## 12. Lead cross-checks (S20)', '']
    md_table(o, ['Check', 'expected', 'computed', 'status', 'explanation'],
             [(x['id'], x['expected'], x['computed'], x['status'], x['explanation'] or '') for x in res['lead_crosschecks']])
    o += ['## 13. Owner questions (named, not decided)', '']
    for q in res['owner_questions']:
        o.append('- **%s** (%s): %s Thresholds: %s' % (q['id'], ', '.join(q['related']), q['question'], cellv(json.dumps(q.get('thresholds'), sort_keys=True))))
    o += ['', '### 13.1 Owner-question readiness (R4-12; nothing decided or adopted)', '']
    md_table(o, ['Question', 'raised', 'ready', 'decided', 'basis', 'open'],
             [(r['id'], r['raised'], r['ready'], r['decided'], r['basis'], '; '.join(r['open_items'])) for r in res['owner_question_readiness']])
    st_ = next(r for r in res['owner_question_readiness'] if r['id'] == 'OD-G4-STACK')
    md_table(o, ['OD-G4-STACK sub-question', 'question', 'value mm', 'basis'],
             [(x['id'], x['question'], x['value_mm'], x['basis']) for x in st_['subquestions']])
    o += ['', '## 14. Model decisions', ''] + ['- ' + d for d in res['model_decisions']]
    o += ['', '## 15. Lead adjudications (recorded verbatim in the JSON)', ''] + ['- %s (%s)' % (a['id'], a['source']) for a in res['lead_adjudications']]
    o += ['', 'Evaluations: %d (budget %d). Scope: %s.' % (res['search']['evaluations'], res['search']['budget'], cellv(res['scope']['pass_']))]
    return '\n'.join(o) + '\n'


# --------------------------------------------------------------------------------------------
# SVG (rendered from the result object; every text node escaped through g4.Svg.text / esc)
# --------------------------------------------------------------------------------------------
def render_plan(res, st):
    lead = res['ranking']['leader']
    L = res['lanes'][lead]
    svg = g4.Svg(1180, 1000, 'G4-R1 plan')
    T = g4.Tf(13.0, 470.0, 500.0)
    D = L['L-RAD']['design_point']['D']
    svg.text(20, 26, 'G4-R1 plan (front view, north up) - %s at D %s mm - %s' % (lead, f2(D), res['verdict']), 13, weight='bold')
    for rid, col in (('GNSS_RAD', '#2e86c1'), ('BLE_RAD', '#8e44ad'), ('WIFI_RAD', '#16a085')):
        g4.draw_geom(svg, T, st.res[rid]['geometry'], col, col, 0.25)
    g4.draw_geom(svg, T, st.res['MAG_CLEAR']['geometry'], '#e67e22', '#e67e22', 0.08, '6 4')
    g4.draw_geom(svg, T, st.res['CHG_CONTACT']['geometry'], '#f1c40f', '#b7950b', 0.10, '3 2')
    for rid in ('CHG_ROUTE', 'CHG_LINK'):
        g4.draw_geom(svg, T, st.res[rid]['geometry'], 'none', '#c0392b', 0.0, '2 2', sw=1.2)
    g4.draw_geom(svg, T, dict(type='circles', circles=[[100, 100, D / 2.0]]), 'none', '#222', 0.0, sw=2.0)
    g4.draw_geom(svg, T, dict(type='circles', circles=[[100, 100, L['L-RAD']['design_point']['D'] / 2.0 - L['L-RAD']['design_point']['tw']]]),
                 'none', '#555', 0.0, '4 3')
    g = st.s14geo
    g4.draw_geom(svg, T, dict(type='circles', circles=[[100, 100, g['outline_r']]]), '#f9e79f', '#b7950b', 0.20, sw=1.4)
    g4.draw_geom(svg, T, dict(type='poly', pts=g['pod']), '#d6eaf8', '#2471a3', 0.5, sw=1.2)
    for s_ in g['supports']:
        g4.draw_geom(svg, T, dict(type='poly', pts=s_['poly']), '#000', '#000', 0.8)
    colors = {'caseback rib': '#7f8c8d', 'charger contacts': '#d35400', 'charger land': '#f5cba7', 'caseback seal flange': '#aed6f1',
              'pusher': '#566573', 'button boot': '#1c2833', 'button boss': '#bfc9ca', 'caseback screw': '#212f3d', 'case-side support': '#5d6d7e',
              'support pad': '#85929e', 'lug arm': '#cacfd2', 'spring bar': '#909497', 'dielectric sector': '#a3e4d7', 'midcase': '#d5d8dc',
              'display land': '#ebedef', 'conductor': '#c0392b', 'vent port': '#48c9b0', 'caseback centre plate': '#aab7b8'}
    order = ['midcase', 'display land', 'dielectric sector', 'caseback seal flange', 'caseback centre plate', 'lug arm', 'spring bar', 'support pad',
             'case-side support', 'caseback rib', 'charger land', 'charger contacts', 'button boss', 'button boot', 'pusher', 'caseback screw',
             'conductor', 'vent port']
    for kind in order:
        for f in L['features']:
            if f['kind'] == kind:
                g4.draw_geom(svg, T, f['geom'], colors.get(kind, '#999'), '#333', 0.55 if kind not in ('caseback seal flange', 'midcase') else 0.15)
    for a in L['L-RAD']['arcs']:
        g4.draw_geom(svg, T, g4.sector(a['arc_az'][0], a['arc_az'][1], a['R_bore_arc_mm'] - 0.05, D / 2.0 - a['t_arc_mm'] + 0.05), '#c71585', '#c71585', 0.8)
    bp = L['L-LRA']['best_plan_pose']
    if bp:
        x, y = T(g4.xy(bp['r'], bp['az']))
        svg.add('<circle cx="%.2f" cy="%.2f" r="5" fill="none" stroke="#8e44ad" stroke-width="2" stroke-dasharray="3 2"/>' % (x, y))
        svg.text(x + 8, y, 'LRA plan pose (%s) - Z gated' % bp['cls'], 10, fill='#8e44ad')
    y0 = 950
    svg.text(820, 80, 'Legend', 12, weight='bold')
    for i, (k, c) in enumerate(sorted(colors.items())):
        svg.add('<rect x="820" y="%d" width="12" height="10" fill="%s" stroke="#333"/>' % (92 + 16 * i, c))
        svg.text(838, 101 + 16 * i, k, 10)
    svg.text(20, y0, 'Dispositions: ' + '; '.join('%s %s' % (k, v) for k, v in sorted(res['dispositions'].items())), 10)
    svg.text(20, y0 + 18, 'Charger pose (prerequisite pose; closed %s): ori %s r %s az %s; land overshoot %s mm (cap 0.75); plan prerequisite needs '
             'r_lim %s mm (dashed red: CHG_ROUTE / CHG_LINK); local wall arcs magenta; keep-outs shaded.' % (
                 cellv(L['L-CHG']['selected']['pass_']), L['L-CHG']['selected']['pose']['orientation'], f2(L['L-CHG']['selected']['pose']['r_centre']),
                 f2(L['L-CHG']['selected']['pose']['az_centre']), f3(L['L-CHG']['selected']['pose']['land_side_overshoot_mm']),
                 f3(L['L-CHG']['literal_c_r1_01']['plan_prerequisite']['r_lim_required_mm'])), 10)
    svg.text(820, 400, 'Rendered from the result feature records;', 10)
    svg.text(820, 414, 'no KiCad geometry.', 10)
    return svg.render()


def render_sections(res, st):
    lead = res['ranking']['leader']
    L = res['lanes'][lead]
    svg = g4.Svg(1180, 1000, 'G4-R1 sections')
    svg.text(20, 26, 'G4-R1 sections - %s - %s' % (lead, res['verdict']), 13, weight='bold')
    sw1 = L['L-BTN']['switches']['SW1']
    for row, topo in enumerate(('T2-R', 'T2-F')):
        s = sw1['T2'][topo]['I-SUM']
        sc, ox, y = 110.0, 40, 70 + row * 110
        svg.text(ox, y - 18, '%s SW1 common section (I-SUM): available %s mm, required %s mm, bore margin %s mm, protrusion %s mm' % (
            topo, f3(s['L_available']), f3(s['L_required']), fs(s['margins']['bore_stack']), f3(s['protrusion_mm'])), 11, weight='bold')
        svg.add('<line x1="%d" y1="%d" x2="%.1f" y2="%d" stroke="#1a5276" stroke-width="2"/>' % (ox, y - 6, ox + s['L_available'] * sc, y - 6))
        x = ox
        for i, term in enumerate(s['stack']):
            wpx = term['value'] * sc
            svg.add('<rect x="%.1f" y="%d" width="%.1f" height="26" fill="%s" stroke="#333"/>' % (
                x, y, wpx, '#d5dbdb' if 'guide' in term['term'] else ('#f5b7b1' if 'rim' in term['term'] or 'boot' in term['term'] else '#fdebd0')))
            svg.text(x + 2, y + 40 + 11 * (i % 3), '%s %s' % (term['term'], f2(term['value'])), 8)
            x += wpx
        svg.text(ox + max(x - ox, s['L_available'] * sc) + 12, y + 18, 'blue line = available bore length (inner bore face to boss face)', 9, fill='#1a5276')
    t3 = sw1['T3'] or {}
    svg.text(40, 290, 'T3 (case-integral flexure): %s' % t3.get('status'), 11, weight='bold')
    svg.text(40, 306, t3.get('threshold') or t3.get('reason', ''), 10)
    zm = res['carry_in']['z_model']
    S = L['L-STR']
    ox, oy, sc = 40, 720, 120.0
    svg.text(ox, 340, 'Caseback periphery section, common Z datums', 12, weight='bold')
    svg.text(ox, 356, '(Z = 0 caseback outer / pod plane, +Z to the front; LA-Z-2 conductor band shaded)', 10)
    has_rib = S['selected']['n'] > 0 and S['limits']['rib_top_adv'] is not None
    datums = [('Z = 0 caseback / pod plane', 0.0), ('t_out', S['selected']['t_out'])]
    if has_rib:
        datums.append(('rib top (adverse)', S['limits']['rib_top_adv']))
    datums += [('conductor band bottom (adverse)', zm['z_band_lo_adv']), ('lower web underside (nominal)', zm['z_lower_web_underside_nom'])]
    for name, z in datums:
        yy = oy - z * sc
        svg.add('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#555" stroke-dasharray="4 3"/>' % (ox, yy, ox + 430, yy))
        svg.text(ox + 435, yy + 4, '%s %s' % (name, f3(z)), 9)
    svg.add('<rect x="%d" y="%.1f" width="400" height="%.1f" fill="#f9e79f" fill-opacity="0.6" stroke="#b7950b"/>' % (
        ox, oy - zm['z_lower_web_underside_nom'] * sc, (zm['z_lower_web_underside_nom'] - zm['z_band_lo_adv']) * sc))
    svg.add('<rect x="%d" y="%.1f" width="400" height="%.1f" fill="#aed6f1" stroke="#333"/>' % (ox, oy - S['selected']['t_out'] * sc, S['selected']['t_out'] * sc))
    if has_rib:
        svg.add('<rect x="%d" y="%.1f" width="%.1f" height="%.1f" fill="#7f8c8d" stroke="#333"/>' % (
            ox + 190, oy - (S['selected']['t_out'] + S['selected']['h']) * sc, S['selected']['w'] * sc, S['selected']['h'] * sc))
    svg.text(ox, oy + 20, 'Selected: t_in %s, t_out %s, spokes %d, w %s, h %s' % (
        f2(S['selected']['t_in']), f2(S['selected']['t_out']), S['selected']['n'], f2(S['selected']['w']), f2(S['selected']['h'])), 10)
    svg.text(ox, oy + 36, 'Screen B %s MPa / %s mm (pass %s); Screen A %s MPa' % (
        fs(S['screen_B']['sigma_governing_MPa']), fs(S['screen_B']['w_max_mm']), cellv(S['screen_B']['pass_']), fs(S['screen_A']['sigma_governing_MPa'])), 10)
    if S.get('best_ribbed'):
        br = S['best_ribbed']
        svg.text(ox, oy + 52, 'Best ribbed: spokes %d, w %s, h %s: Screen B %s MPa (no ring credit, LA-STR-4)' % (
            br['config']['n'], f2(br['config']['w']), f2(br['config']['h']), fs(br['screen_B']['sigma_governing_MPa'])), 10)
    ms = L['L-SEAL']['main_seal']
    by_id = {r['id']: r for r in ms['rows']}
    # display only: the smallest gland-feasible face row (owner threshold row), else the post-hoc representative face row
    face = by_id[ms['thresholds']['face']['row'] or ms['topologies']['face']['representative_row']['id']]
    fx, fy, fsc = 660, 560, 100.0
    svg.text(fx, 340, 'Main seal: caseback flange + face groove (smallest feasible face gland; display only)', 12, weight='bold')
    fl = face.get('flange') or {}
    if fl:
        t_fl = fl.get('thickness_mm') or fl['required_thickness_mm']
        svg.add('<rect x="%d" y="%.1f" width="420" height="%.1f" fill="#aed6f1" stroke="#333"/>' % (fx, fy - t_fl * fsc, t_fl * fsc))
        svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#ffffff" stroke="#c0392b"/>' % (
            fx + 150, fy - t_fl * fsc, face['gland']['g'] * fsc, face['gland']['h'] * fsc))
        svg.text(fx, fy + 18, 'flange t %s mm; groove h %s x g %s mm (cs %s)' % (f3(t_fl), f3(face['gland']['h']), f3(face['gland']['g']), f2(face['cs_mm'])), 10)
        svg.text(fx, fy + 34, 'groove residual margin %s mm; rear-face annulus margin %s mm' % (
            fs(face['margins']['flange_groove_residual']), fs(face['margins']['face_annulus'])), 10)
        svg.text(fx, fy + 50, 'coupled flange envelope (all face rows): thickness %s mm, adverse top %s mm' % (
            '..'.join(f3(v) for v in ms['coupled']['flange_thickness_mm'] or []) or 'plate', f3(L['L-SEAL']['flange_top_mm'])), 10)
    C = L['L-CHG']['selected']
    cx_, cy_, csc = 700, 900, 60.0
    svg.text(660, 640, 'Charger feedthrough (%s)' % L['L-CHG']['feedthrough'], 12, weight='bold')
    svg.text(660, 656, 'block Z 0 .. %s mm (SR-CHG-MECH allocation): zero Z gap to the conductor band, plan-separated from CHG_ROUTE / CHG_LINK '
                       '(3-D clear: %s); fails only the block-AND-Z screen (model conservatism)' % (
                           f3(zm['z_band_lo_adv']), cellv(L['L-CHG']['literal_c_r1_01']['block_and_z_diagnostic']['block_3d_clear_of_routes'])), 10)
    svg.text(660, 672, 'land Z 0 .. %s mm: C-R1-01 2(v) plan AND Z vs screws / supports unsatisfiable (shared Z = 0 datum; land Z gap %s mm)' % (
        f3(C['land_top_mm']), fs(L['L-CHG']['literal_c_r1_01']['z_prerequisite']['v_item_min_z_gap_mm']['land'])), 10)
    w_land = C['pose']['land']
    svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#f5cba7" stroke="#333"/>' % (
        cx_ - w_land * csc, cy_ - S['selected']['t_out'] * csc, (C['pose']['block_mm'][0] + 2 * w_land) * csc, S['selected']['t_out'] * csc))
    svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#d35400" stroke="#333"/>' % (
        cx_, cy_ - zm['z_band_lo_adv'] * csc, C['pose']['block_mm'][0] * csc, zm['z_band_lo_adv'] * csc))
    pp = L['L-CHG']['literal_c_r1_01']['plan_prerequisite']
    svg.text(660, cy_ + 20, 'block %s x %s mm, land %s mm, charger closed %s (plan prerequisite: r_lim %s mm required, %s available)' % (
        f2(C['pose']['block_mm'][0]), f2(C['pose']['block_mm'][1]), f2(w_land), cellv(C['pass_']),
        f3(pp['r_lim_required_mm']), f3(pp['r_lim_available_mm'])), 10)
    return svg.render()


def r1_outputs(res, st):
    return {'g4_r1_blockers.json': dumps(res), 'g4_r1_blockers.md': render_md(res), 'g4_r1_plan.svg': render_plan(res, st),
            'g4_r1_sections.svg': render_sections(res, st)}


# --------------------------------------------------------------------------------------------
# Independent validation (check): recomputes predicates through fresh production calls
# --------------------------------------------------------------------------------------------
def numeric_evidence(h):
    """A meaningful numeric boundary: a finite threshold_value, a finite required_delta or a supplier zero-margin entry with a
    finite numeric value (a gate id alone is never one)."""
    vals = [h.get('threshold_value'), h.get('required_delta')] + [z.get('value') for z in (h.get('supplier_zero_margin') or []) if isinstance(z, dict)]
    return any(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in vals)


def state_violations(H):
    """R2-6 hard-check / gate semantics. Rejected: unknown state; negative margin with physical_pass true; PASS unless physical
    pass, complete evidence, no gate and no credit; GATED without execution, gate ids or (numeric checks) governing terms and
    a real numeric boundary; a physical failure shown as PASS / GATED outside the isolated L-LRA lane; FAIL without
    physical_pass false or (numeric checks) without margin and governing terms."""
    bad = []
    for h in H.values():
        s, cid, phys = h['study_status'], h['id'], h['physical_pass']
        numeric = cid in NUMERIC_CHECKS
        if s not in STATUSES:
            bad.append('%s: unknown study_status %s' % (cid, s))
        if h['margin'] is not None and h['margin'] < -EPS and phys is True:
            bad.append('%s: negative margin with physical_pass true' % cid)
        is_pass = phys is True and h['evidence_complete'] and not h['gate_raised']
        if (s == 'PASS') != is_pass:
            bad.append('%s: PASS iff (physical_pass and evidence_complete and no gate) violated' % cid)
        if s == 'PASS' and h['gate_raised']:
            bad.append('%s: PASS with a gate raised' % cid)
        if h['gate_raised'] != bool(h['gate_ids']) or any(not isinstance(g, str) or not g.strip() for g in h['gate_ids']):
            bad.append('%s: gate_raised inconsistent with gate_ids' % cid)
        if s == 'GATED':
            if not h['check_executed']:
                bad.append('%s: GATED without an executed check' % cid)
            if not (h['gate_raised'] and h['gate_ids']):
                bad.append('%s: GATED without gate ids' % cid)
            if numeric and not h.get('governing_terms'):
                bad.append('%s: GATED without governing terms' % cid)
            if numeric and not numeric_evidence(h):
                bad.append('%s: GATED without a meaningful numeric threshold (gate id alone)' % cid)
            if numeric and not isinstance(h['margin'], (int, float)):
                bad.append('%s: GATED numeric check without a margin' % cid)
        if phys is False and s in ('PASS', 'GATED') and not (h.get('isolation') == 'L-LRA' and cid in VALIDATOR_LRA_ISOLATION):
            bad.append('%s: physical failure hidden as study %s' % (cid, s))
        if s == 'GATED' and not numeric and not h.get('categorical_evidence'):
            bad.append('%s: categorical GATED check without explicit categorical evidence' % cid)
        if phys is False and s == 'GATED' and not numeric_evidence(h):
            bad.append('%s: isolated physical failure without a numeric threshold' % cid)
        if s == 'FAIL':
            if phys is not False:
                bad.append('%s: FAIL without physical_pass false' % cid)
            if numeric and (not isinstance(h['margin'], (int, float)) or not h.get('governing_terms')):
                bad.append('%s: FAIL without margin / governing terms' % cid)
        if s == 'BLOCKED' and (h['check_executed'] or not h.get('blocked_reason')):
            bad.append('%s: BLOCKED without a blocking condition' % cid)
        if s == 'PASS' and h.get('credits'):
            bad.append('%s: PASS resting on a credit' % cid)
    return bad


def whole_design_violations(res, ceiling=51.0):
    """R2-7 / R3-7 whole-design guard: no selected / recommended / compliant candidate with D > 51.00, an unauthorized protrusion
    or an above-limit diagnostic geometry; radial-core feasibility is never whole-design compliance; a selected candidate must be
    whole-design compliant or in the brief's geometry-closed / supplier-gates-open state, with the basis named."""
    bad = []
    rk = res['ranking']
    by = {c['id']: c for c in res['candidates']}
    lead = by.get(rk['leader'])
    permitted = bool(lead) and (bool(lead['whole_design_compliant']) or bool(lead['geometry_closed_supplier_gates_open']))
    if bool(rk['selection_permitted']) != permitted:
        bad.append('selection_permitted inconsistent with the leader compliance states')
    if rk['selected'] is not None:
        c = by.get(rk['selected'])
        if c is None:
            bad.append('selected candidate not in the candidate list')
        else:
            if rk['selected_D'] is None or rk['selected_D'] > ceiling + EPS or rk['selected_D'] != c['D_complete']:
                bad.append('selected diameter missing, above %.2f mm or not the complete-closure diameter' % ceiling)
            if not (c['whole_design_compliant'] or c['geometry_closed_supplier_gates_open']):
                bad.append('selected candidate neither whole-design compliant nor geometry-closed with supplier gates open')
            exp = 'whole-design compliant' if c['whole_design_compliant'] else 'geometry closed, supplier gates open (NOT whole-design compliant)'
            if rk.get('selection_basis') != exp:
                bad.append('selection basis label differs from the selected candidate state')
        if not rk['selection_permitted']:
            bad.append('candidate selected although selection is not permitted')
    elif rk.get('selection_basis') is not None:
        bad.append('selection basis without a selected candidate')
    for c in res['candidates']:
        if c['D_eval'] > ceiling + EPS:
            bad.append('%s: diagnostic design point above %.2f mm' % (c['id'], ceiling))
        if c['whole_design_compliant'] or c['geometry_closed_supplier_gates_open'] or c['geometric_candidate']:
            if c['D_complete'] is None or c['D_complete'] > ceiling + EPS:
                bad.append('%s: compliant / closed without a complete closure <= %.2f mm' % (c['id'], ceiling))
            if c['unpermitted_protrusions']:
                bad.append('%s: compliant / closed with an unauthorized protrusion' % c['id'])
            if c['D_complete'] is None and c['D_radial_core'] is not None:
                bad.append('%s: radial-core feasibility described as whole-design compliance' % c['id'])
    for cid, L in res['lanes'].items():
        if L['L-RAD']['design_point']['D'] > ceiling + EPS:
            bad.append('%s: lane results rest on an above-limit geometry' % cid)
    return bad


def compliance_violations(cx, res, ceiling=51.0):
    """R3-7 (validator): every candidate's study states are reconstructed independently - from its own hard checks, stops, lane
    dispositions, diameters, protrusions and a recomputed Z delta - and must equal the reported states. An architecture-, owner- or
    supplier-gated mandatory lane, a physical failure (isolated or not), a non-PASS check or a raised stop is never whole-design
    compliance; an architecture- or owner-gated lane is never the geometry-closed / supplier-gates-open state."""
    bad = []
    for c in res['candidates']:
        cid = c['id']
        H, stops, disp = res['candidate_hard_checks'][cid], res['candidate_stops'][cid], c['dispositions']
        raised = [s for s in stops if s['raised']]
        zd = z_delta_of(cx, res['lanes'][cid]['features'])
        dc = c['D_complete']
        geo = dc is not None and dc <= ceiling + EPS and c['D_eval'] <= ceiling + EPS and not c['unpermitted_protrusions'] and zd <= EPS
        study = c['D_eval'] <= ceiling + EPS and not any(s['fatal'] for s in raised)
        strict_lanes = all(disp[l] == 'RESOLVED_GEOMETRICALLY' for l in ('L-WIN', 'L-BTN', 'L-SEAL', 'L-CHG', 'L-STR', 'L-RAD', 'L-ASM', 'L-LRA'))
        supp_lanes = all(disp[l] in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED') for l in ('L-WIN', 'L-BTN', 'L-SEAL', 'L-CHG', 'L-STR', 'L-RAD', 'L-ASM', 'L-LRA'))
        no_phys_fail = all(h['physical_pass'] is not False for h in H.values())
        all_pass = all(h['study_status'] == 'PASS' for h in H.values())
        exp = dict(study_candidate=study, geometric_candidate=geo,
                   owner_decision_candidate=study and c['verdict_if_selected'] in ('R1 PARTIAL — LRA ARCHITECTURE GATE', 'R1 OWNER DECISION REQUIRED'),
                   geometry_closed_supplier_gates_open=geo and study and supp_lanes and no_phys_fail and not raised,
                   whole_design_compliant=geo and study and strict_lanes and no_phys_fail and all_pass and not raised
                   and c['verdict_if_selected'] == 'R1 RESOLVED')
        for k, v in exp.items():
            if bool(c.get(k)) != v:
                bad.append('%s: reported %s %s, reconstructed %s' % (cid, k, c.get(k), v))
        if abs((c.get('z_delta_mm') or 0.0) - zd) > 1e-12:
            bad.append('%s: reported Z delta differs from the feature recomputation' % cid)
    return bad


# R3-5: the validator's own L-LRA isolation policy - expected check ids and their LRA-coupled semantics - enforced independently of
# the builder constant (which must be identical).
VALIDATOR_LRA_ISOLATION = {
    'R1-H05': 'H05-LRA-COUPLED: exactly the XL-LRA lateral / Z and U7-riser straight-run terms, owning lane L-LRA',
    'R1-H19': 'LRA class fit / envelope deficit: owning lane L-LRA, gates OD-G4-LRA-ARCH or SR-LRA (Q-R1-STRUCTURE allowed), envelopes reported',
}
VALIDATOR_H05_LRA_TERMS = frozenset(('H05-STRAIGHT@U7-RISER', 'H05-EDGE-XL-LRA', 'H05-EDGE-Z-XL-LRA'))


def isolation_violations(H):
    """R3-5 (validator): only R1-H05 and R1-H19 may carry the L-LRA isolation, each only with its LRA-coupled semantics; any other
    check id, any other isolation value or a semantic mismatch is rejected (an isolated physical failure is the only physical
    failure that may be GATED instead of FAIL)."""
    bad = []
    if set(VALIDATOR_LRA_ISOLATION) != set(LRA_ISOLATION_ALLOWED):
        bad.append('builder L-LRA isolation policy %s differs from the validator policy %s' % (sorted(LRA_ISOLATION_ALLOWED), sorted(VALIDATOR_LRA_ISOLATION)))
    for cid, h in sorted(H.items()):
        iso = h.get('isolation')
        if iso is None:
            continue
        if iso != 'L-LRA':
            bad.append('%s: unknown isolation %r' % (cid, iso))
            continue
        if cid not in VALIDATOR_LRA_ISOLATION:
            bad.append('%s: forged L-LRA isolation (only %s are LRA-coupled)' % (cid, ', '.join(sorted(VALIDATOR_LRA_ISOLATION))))
            continue
        if h.get('owning_lane') != 'L-LRA':
            bad.append('%s: L-LRA isolation on a check not owned by L-LRA' % cid)
        gt = h.get('governing_terms') or {}
        if cid == 'R1-H05' and set(gt.keys()) != VALIDATOR_H05_LRA_TERMS:
            bad.append('R1-H05: isolated terms are not exactly the H05-LRA-COUPLED terms')
        if cid == 'R1-H19':
            g = set(h.get('gate_ids') or [])
            if not (g & {'OD-G4-LRA-ARCH', 'SR-LRA'}) or not g <= {'OD-G4-LRA-ARCH', 'SR-LRA', 'Q-R1-STRUCTURE'} or 'envelopes' not in gt:
                bad.append('R1-H19: isolation without the LRA class-fit semantics (gates / envelopes)')
    return bad


def lra_reconstruct(cx, res, cid, fit, r1in):
    """R4-1 (validator): the physical identity a credited LRA fit must have, reconstructed independently - from the emitted design
    point (design_point_g4_terms, the reported charger pose parameters and the selected structural configuration), fresh production
    predicates (rad_point, main_seal, chg_pose, c1_split, str_geo, rib_layout, lra_exclusion_set, the plan re-check) and the
    authoritative inputs (G4 classes, R1 supplied classes, G4 parameters, materials) - for the fit's claimed class id, pose and plate.
    Never built from the claimed or evaluated physical fields. Returns (None, reason) if it cannot be reconstructed."""
    L = res['lanes'][cid]
    cand = next(c for c in cx.cands if c['id'] == cid)
    cb = fit.get('combination') or {}
    try:
        classes = lra_authoritative_classes(cx, L['L-LRA'], r1in)
        cls = next((c for c in classes if c['id'] == (cb.get('lra_class') or {}).get('id')), None)
        if cls is None:
            return None, 'claimed class is not an authored / accepted supplied class'
        pose = dict(r=cb['pose']['r_mm'], az=cb['pose']['az_deg'], ori=cb['pose']['orientation'])
        pl = cb['plate']
        plate = (pl['t_in_mm'], pl['t_out_mm'], pl['depth_mm'], pl['residual_mm'])
        dp = dict(L['design_point_g4_terms'])
        row = rad_point(cx, cand, dp['D'], dp['tw'], solve_carrier(cx, cx.ce[cid]), arc_defs(cx, cand))
        r_lim = seal_r_lim(main_seal(cx, cand, row))
        q = L['L-CHG']['selected']['pose']
        chg = chg_pose(cx, cand, q['orientation'], q['r_centre'], q['az_centre'], q['land'])
        split = c1_split(cx, cand, chg['land_rmin']) if cand['caseback'].get('split') else None
        r_split = split['selected']['r_split'] if split else None
        mats_fn, _ = str_mats(cx, cand, r_split)
        geo = str_geo(cx, cand, row, r_lim, chg, r_split)
        sel = L['L-STR']['selected']
        strl_like = dict(selected=sel, geometry=geo, rib_layout=rib_layout(geo, sel['n'], sel['w'], cx.P['V13_rib_counts']['phase_divisions']))
        lctx = dict(classes=classes, ex=lra_exclusion_set(cx, cand, dp, dict(pose=chg), strl_like), dp_g4=dp, r_lim=r_lim)
        exp = lra_claimed_identity(cx, cand, cls, pose, plate, mats_fn, geo, lctx)
        body, lead = lra_class_envelope(cx.st, cls, pose)
        exp['plan_fit'] = dict(violations=lra_plan_check(cx, cand, body + lead, lctx))
    except (KeyError, TypeError, ValueError, StudyError, StopIteration) as exc:
        return None, 'identity not reconstructible (%s: %s)' % (type(exc).__name__, exc)
    return dict(identity=exp, cand=cand, cls=cls, pose=pose, plate=plate, mats_fn=mats_fn, strl=strl_like, lctx=lctx, body=body, lead=lead), None


def lra_binding_violations(cx, res, r1in=None):
    """R4-1 (validator): every credited LRA fit carries its claimed and its evaluated physical identity (LRA_IDENTITY_KEYS); the two
    are equal key by key, and both equal the identity reconstructed independently by lra_reconstruct (a fit whose identity cannot be
    reconstructed is rejected); only the claimed plate pair was evaluated; the fit row agrees with its claim; and a fresh run of the
    structural fallback on the reconstructed combination reproduces the recorded structural result (no stale deflection survives)."""
    r1in = r1in if r1in is not None else load_json(IN_PATH)
    bad = []
    for cid, L in res['lanes'].items():
        for c in L['L-LRA']['classes']:
            if c['fits'] and not c['fit_examples']:
                bad.append('%s %s: fit counted without a recorded combination' % (cid, c['id']))
            for f in c['fit_examples']:
                cb, ev = f.get('combination'), f.get('evaluated')
                if not isinstance(cb, dict) or not isinstance(ev, dict) or not isinstance(f.get('structural'), dict):
                    bad.append('%s %s: fit without its claimed / evaluated identity or structural record' % (cid, c['id']))
                    continue
                mine = []
                if set(cb) != set(LRA_IDENTITY_KEYS) or set(ev) != set(LRA_IDENTITY_KEYS):
                    mine.append('identity keys incomplete')
                for k in LRA_IDENTITY_KEYS:
                    if not same(cb.get(k), ev.get(k)):
                        mine.append('claimed %s differs from the structurally evaluated %s' % (k, k))
                rec, why = lra_reconstruct(cx, res, cid, f, r1in)
                if rec is None:
                    mine.append(why)
                else:
                    for k in LRA_IDENTITY_KEYS:
                        if not same(rec['identity'][k], cb.get(k)):
                            mine.append('claimed %s differs from its independent reconstruction' % k)
                        if not same(rec['identity'][k], ev.get(k)):
                            mine.append('evaluated %s differs from the independent reconstruction' % k)
                pl = cb.get('plate') or {}
                if f['structural'].get('pairs_evaluated') != [[pl.get('t_in_mm'), pl.get('t_out_mm')]]:
                    mine.append('structural fallback evaluated plate pairs %s, claimed %s' % (f['structural'].get('pairs_evaluated'),
                                                                                              [pl.get('t_in_mm'), pl.get('t_out_mm')]))
                if not same([f.get('t_in'), f.get('t_out'), f.get('depth'), f.get('residual')],
                            [pl.get('t_in_mm'), pl.get('t_out_mm'), pl.get('depth_mm'), pl.get('residual_mm')]) or \
                        not same([f.get('r'), f.get('az'), f.get('ori')], [(cb.get('pose') or {}).get(k) for k in ('r_mm', 'az_deg', 'orientation')]) \
                        or (cb.get('lra_class') or {}).get('id') != c['id']:
                    mine.append('fit row differs from its claimed combination')
                if not mine:
                    fresh = lra_struct_fallback(cx, rec['cand'], struct_context(cx, rec['cand']), rec['strl'], rec['mats_fn'], rec['identity'],
                                                dict(body=rec['body'], lead=rec['lead']), rec['plate'], rec['lctx'])
                    if fresh['pass_'] != f.get('pass_') or not same([fresh['sigma_B'], fresh['w_B']], [f.get('sigma_B'), f.get('w_B')], 1e-9):
                        mine.append('recorded structural result not reproduced by the fallback on the reconstructed combination')
                bad += ['%s %s: %s' % (cid, c['id'], m) for m in mine]
    return bad


# R4-9: the validator's own unit table for the typed R1-H11 terms (independent of the builder's H11_TERM_TYPES)
VALIDATOR_H11_UNITS = dict(gland_compression_min='dimensionless', gland_compression_max='dimensionless', gland_fill='dimensionless',
                           face_annulus='mm', flange_groove_residual='mm', bond_land_annulus='mm', spigot_rear_periphery_z='mm',
                           continuous_bore='mm', joint_row='bool')


def h11_violations(cx, res):
    """R4-9 (validator): every candidate's typed R1-H11 record is recomputed independently - a fresh main_seal at the reported design
    point and the seal-path closure recomputed from the reported inventory - and must equal the report term by term (id, quantity,
    value, units, threshold, pass, delta), with the per-topology feasibility, the check predicates, the physical pass (boolean
    conjunction) and the per-units governing terms; every term's units must equal the validator's own unit table; the check margin /
    units / required delta / physical pass must be those of the typed governing term and conjunction."""
    bad = []
    for cid, H in res['candidate_hard_checks'].items():
        h = H['R1-H11']
        ty = h.get('typed')
        if not isinstance(ty, dict):
            bad.append('%s R1-H11: no typed record' % cid)
            continue
        L = res['lanes'][cid]
        cand = next(c for c in cx.cands if c['id'] == cid)
        dp = L['design_point_g4_terms']
        row = rad_point(cx, cand, dp['D'], dp['tw'], solve_carrier(cx, cx.ce[cid]), arc_defs(cx, cand))
        clo = g4.seal_closure(L['L-SEAL']['inventory'], screws_outside=L['L-SEAL']['screws']['outside'])['closed']
        exp = h11_typed(main_seal(cx, cand, row), clo)
        rep = {x['id']: x for o in (ty.get('topologies') or {}).values() for x in o.get('terms', [])}
        for x in rep.values():
            if VALIDATOR_H11_UNITS.get(x['id'].split('-', 2)[-1]) != x.get('units'):
                bad.append('%s R1-H11 %s: units %r, the quantity is %r' % (cid, x['id'], x.get('units'), VALIDATOR_H11_UNITS.get(x['id'].split('-', 2)[-1])))
        for t in SEAL_ORDER:
            for x in exp['topologies'][t]['terms']:
                r = rep.get(x['id'])
                if r is None or not same(r, x, 1e-9):
                    bad.append('%s R1-H11 %s: reported typed term differs from its recomputation' % (cid, x['id']))
            if (ty.get('topologies') or {}).get(t, {}).get('feasible') is not exp['topologies'][t]['feasible']:
                bad.append('%s R1-H11 %s: topology feasibility is not the conjunction of its typed terms' % (cid, t))
        if set(rep) != {x['id'] for t in SEAL_ORDER for x in exp['topologies'][t]['terms']}:
            bad.append('%s R1-H11: typed term set differs from the recomputation' % cid)
        if not same(ty.get('check_predicates'), exp['check_predicates']):
            bad.append('%s R1-H11: check predicates differ from the recomputation' % cid)
        if ty.get('physical_pass') is not exp['physical_pass'] or h['physical_pass'] is not exp['physical_pass'] or \
                (h['study_status'] == 'PASS' and not all(x['pass_'] for x in exp['check_predicates'])):
            bad.append('%s R1-H11: overall pass is not the conjunction of its mandatory typed predicates' % cid)
        g = exp['governing']
        if not same(ty.get('governing'), g, 1e-9) or not same(ty.get('governing_by_units'), exp['governing_by_units'], 1e-9):
            bad.append('%s R1-H11: governing term %s differs from the recomputed %s (%s)' % (cid, (ty.get('governing') or {}).get('term_id'),
                                                                                      g['term_id'], g['units']))
        if not same([h['margin'], h['units'], h['required_delta']], [g['value'], g['units'], max(0.0, -g['value'])], 1e-9) or \
                not str(h.get('required_delta_units') or '').startswith(g['units']):
            bad.append('%s R1-H11: margin / units / required delta are not those of the typed governing term (%s %s)' % (cid, fs(g['value']), g['units']))
    return bad


VALIDATOR_SEAL_PREFERENCE = ('face', 'radial', 'adhesive')


def seal_population_violations(cx, res):
    """R5 (validator): for every candidate (1) a fresh main_seal at the reported design point equals the emitted seal record (rows, sets,
    reductions, thresholds, coupled population; the display-only representative rows excluded); (2) every population reduction is
    re-derived here from the emitted rows with the validator's own rules and unit table (predicates, evaluated / predicate-feasible /
    fully feasible rows, term reductions, coupled topology / population / r_lim / flange envelope); (3) every seal-dependent consumer
    equals its reduction (flange feature Z, charger flange top and r_lim, G4 design terms, H14 seal-flange rows, radial supplier
    threshold) and no representative row is marked anything but display-only."""
    bad = []
    strip = lambda m: dict(m, topologies={t: {k: v for k, v in o.items() if k != 'representative_row'} for t, o in m['topologies'].items()})
    for cid, L in res['lanes'].items():
        ms = L['L-SEAL']['main_seal']
        cand = next(c for c in cx.cands if c['id'] == cid)
        dp = L['design_point_g4_terms']
        row = rad_point(cx, cand, dp['D'], dp['tw'], solve_carrier(cx, cx.ce[cid]), arc_defs(cx, cand))
        if not same(rounded(strip(main_seal(cx, cand, row))), strip(ms), 2e-9):
            bad.append('%s L-SEAL: emitted seal population record differs from its fresh recomputation' % cid)
        tol_cb = g4.Specs(cx.st, cand).pc_cb['thickness_mm']
        for r in ms['rows']:
            exp = {k: v >= -EPS for k, v in r['margins'].items() if VALIDATOR_H11_UNITS.get(k) in ('mm', 'dimensionless')}
            if set(exp) != set(r['margins']) or exp != r['predicates'] or r['pass_all'] is not all(exp.values()):
                bad.append('%s L-SEAL %s: row predicates are not the typed margins >= 0' % (cid, r['id']))
        feasible = []
        for t in SEAL_ORDER:
            o = ms['topologies'][t]
            ev = [r for r in ms['rows'] if r['topology'] == t and r['authorized']]
            ff = [r for r in ev if r['pass_all']]
            pop = ff or ev
            if o['evaluated_rows'] != [r['id'] for r in ev] or o['fully_feasible_rows'] != [r['id'] for r in ff] or o['feasible'] is not bool(ff):
                bad.append('%s L-SEAL %s: evaluated / fully feasible rows or feasibility not the reduction over its rows' % (cid, t))
            if o['term_population'] != ('fully_feasible_rows' if ff else 'evaluated_rows'):
                bad.append('%s L-SEAL %s: term population is not the boolean rule' % (cid, t))
            for k, d in o['term_reductions'].items():
                if o['predicate_feasible_rows'].get(k) != [r['id'] for r in ev if r['predicates'][k]]:
                    bad.append('%s L-SEAL %s %s: predicate-feasible rows differ from the rows meeting the predicate' % (cid, t, k))
                if abs(d['value'] - max(r['margins'][k] for r in pop)) > 1e-9 or abs(d['worst'] - min(r['margins'][k] for r in pop)) > 1e-9 \
                        or d['units'] != VALIDATOR_H11_UNITS.get(k):
                    bad.append('%s L-SEAL %s %s: term reduction is not the max / min over the term population' % (cid, t, k))
            rep = o.get('representative_row') or {}
            if rep.get('display_only') is not True:
                bad.append('%s L-SEAL %s: representative row not marked display-only' % (cid, t))
            if ff:
                feasible.append(t)
        if feasible != ms['feasible_topologies'] or ms['physical_pass'] is not bool(feasible):
            bad.append('%s L-SEAL: feasible topologies / physical pass are not any(r.pass_all) per topology' % cid)
        closing = [t for t in VALIDATOR_SEAL_PREFERENCE if t in feasible]
        ct = closing[0] if closing else 'face'
        cpop = [r for r in ms['rows'] if r['topology'] == ct and r['authorized'] and (r['pass_all'] or not closing)]
        cp = ms['coupled']
        if cp['topology'] != ct or cp['closed'] is not bool(closing) or cp['population'] != [r['id'] for r in cpop] or \
                abs(cp['r_lim_mm'] - min(r['r_lim_mm'] for r in cpop)) > 1e-9 or ms['closed_topology'] != (ct if closing else None):
            bad.append('%s L-SEAL: coupled topology / population / r_lim is not the boolean / fixed-order rule and the min reduction' % cid)
        ft = max(((r.get('flange') or {}).get('thickness_mm') if (r.get('flange') or {}).get('thickness_mm') is not None else dp['t_out']) + tol_cb
                 for r in cpop)
        fl = [f for f in L['features'] if f['id'] == 'CB_SEAL_FLANGE']
        if abs(L['L-SEAL']['flange_top_mm'] - ft) > 1e-9 or abs(L['L-CHG']['selected']['flange_top_mm'] - ft) > 1e-9 or len(fl) != 1 or \
                abs(fl[0]['z_hi_adv'] - ft) > 1e-9:
            bad.append('%s L-SEAL: flange top / flange feature Z is not the max over the coupled population (%.6f)' % (cid, ft))
        if abs(dp['r_lim'] - cp['r_lim_mm']) > 1e-9 or abs(L['L-CHG']['selected']['r_lim'] - cp['r_lim_mm']) > 1e-9:
            bad.append('%s L-SEAL: design-point r_lim consumers differ from the coupled population reduction' % cid)
        cs_pop = sorted({r['cs_mm'] for r in cpop if r.get('cs_mm') is not None})
        if dp.get('seal_cs') != (cs_pop[0] if len(cs_pop) == 1 else None) or not same(dp.get('seal_cs_population_mm'), cs_pop):
            bad.append('%s L-SEAL: G4 design-term seal_cs is a representative choice, not the coupled population' % cid)
        sfr = L['L-SEAL']['seal_flange_rows_h14']
        for a in ('CHG_LAND', 'CHG_BLOCK'):
            mine = [x for x in sfr['rows'] if x['a'] == a and x['category'] != 'conservative_model_diagnostic']
            red = sfr['reduction'][a]
            if sorted({x['seal_row'] for x in mine}) != sorted(cp['population']) or \
                    abs(red['effective_clearance_min_mm'] - min(x['effective_clearance_mm'] for x in mine)) > 1e-9 or \
                    red['clear_all_rows'] is not all(x['clear'] for x in mine) or \
                    abs(red['envelope_effective_clearance_mm'] - red['effective_clearance_min_mm']) > 1e-9:
                bad.append('%s H14 %s: seal-flange term is not the reduction over every coupled seal row' % (cid, a))
        swr = L['L-CHG']['strict_wedge_diagnostic']['at_radial_r_lim']
        ws = [x['width_mm'] for x in swr['rows'] if x['width_mm'] is not None]
        if [x['row'] for x in swr['rows']] != ms['topologies']['radial']['evaluated_rows'] or \
                (ws and abs(swr['governing_threshold_mm'] - min(ws)) > 1e-9):
            bad.append('%s L-CHG: radial supplier land threshold is not the min over every authorized radial row' % cid)
    return bad


VALIDATOR_CHG_ATTRIBUTION = dict(
    block_inner=('contract_mandated', 'mm'), block_reservation_outer=('contract_mandated', 'mm'), block_flange=('contract_mandated', 'mm'),
    block_in_wedge=('contract_mandated', 'mm'), block_outside_wifi=('contract_mandated', 'bool'), land_non_conductive=('contract_mandated', 'bool'),
    land_caseback_side=('contract_mandated', 'bool'), land_inner_s14=('contract_mandated', 'mm'), land_radiators=('contract_mandated', 'mm'),
    routes_clear_in_plan=('contract_mandated', 'bool'), land_routes_clear_in_z=('contract_mandated', 'bool'),
    land_overshoot_cap=('contract_mandated', 'mm'), land_azimuth_cap=('contract_mandated', 'deg'), land_flange=('physical_required_elsewhere', 'mm'),
    land_u6=('physical_required_elsewhere', 'mm'), block_routes_clear_3d=('physical_required_elsewhere', 'bool'),
    block_routes_clear_in_z=('conservative_model_diagnostic', 'bool'), strict_wedge_land=('supplier_diagnostic', 'mm'),
    block_height_allocation=('supplier_diagnostic', 'mm'))


def h14_violations(cx, res):
    """R4-6 (validator): the typed R1-H14 record. Every term is in exactly one category under the validator's own attribution (named
    predicates by table; a LAND row is contract-mandated - 2(v) plan AND Z or 2(vi) 3-D -, a BLOCK 3-D row physical, a BLOCK plan-AND-Z
    row a conservative diagnostic: never contract); every row's pass / value is re-derived from its plan / Z gaps under its predicate
    and its Z gap from the reported feature Z intervals; minima only per (category, units), never across units; the governing term is
    the minimum contract-mandated mm term; physical pass = contract AND physical; the land 2(v) unsatisfiability is recomputed and, when
    it holds, a failing contract land 2(v) term must be visible and decides the check."""
    bad = []
    for cid, H in res['candidate_hard_checks'].items():
        h = H['R1-H14']
        ty = h.get('typed')
        if not isinstance(ty, dict):
            bad.append('%s R1-H14: no typed record' % cid)
            continue
        L = res['lanes'][cid]
        sel = L['L-CHG']['selected']
        feats = {f['id']: f for f in L['features']}
        land_z, block_z = zfeat(0.0, sel['land_top_mm']), zfeat(0.0, sel['block_top_mm'])
        terms = ty.get('terms') or []
        if len({t['id'] for t in terms}) != len(terms):
            bad.append('%s R1-H14: term ids not unique' % cid)
        for t in terms:
            if t.get('category') not in CHG_TERM_CATEGORIES:
                bad.append('%s R1-H14 %s: unknown category %r' % (cid, t.get('id'), t.get('category')))
                continue
            if ' vs ' in t['id']:
                a = t['id'].split(' vs ')[0]
                b = t['id'].split(' vs ')[1].split(' [')[0]
                pz = t['id'].endswith('[plan AND Z]')
                want = ('contract_mandated' if a == 'CHG_LAND' else ('conservative_model_diagnostic' if pz else 'physical_required_elsewhere'))
                if a == 'CHG_LAND' and pz and t.get('item_rule') != '2(v)':
                    bad.append('%s R1-H14 %s: plan-AND-Z land row outside C-R1-01 2(v)' % (cid, t['id']))
                if t['category'] != want or t.get('units') != 'mm':
                    bad.append('%s R1-H14 %s: category %s, the contract attribution is %s (a block plan-AND-Z row is never contract text)'
                               % (cid, t['id'], t['category'], want))
                p_ok, z_ok = (not t['plan_overlap']) and separated(t['plan_gap_mm']), separated(t['z_gap_mm'])
                ep = (p_ok and z_ok) if pz else (p_ok or z_ok)
                ev = min(t['plan_gap_mm'], t['z_gap_mm']) if pz else max(t['plan_gap_mm'], t['z_gap_mm'])
                if t['pass_'] is not ep or abs(t['value'] - ev) > 1e-9:
                    bad.append('%s R1-H14 %s: pass / value not re-derived from its plan / Z gaps' % (cid, t['id']))
                if b in feats and 'z_lo_adv' in feats[b] and abs(z_gap(land_z if a == 'CHG_LAND' else block_z, feats[b]) - t['z_gap_mm']) > 1e-9:
                    bad.append('%s R1-H14 %s: Z gap not reproduced from the feature Z intervals' % (cid, t['id']))
            else:
                want = VALIDATOR_CHG_ATTRIBUTION.get(t['id'])
                if want is None or (t['category'], t['units']) != want:
                    bad.append('%s R1-H14 %s: (category, units) %s, the attribution is %s' % (cid, t['id'], (t['category'], t['units']), want))
        groups = {}
        for t in terms:
            if t.get('pass_') is None or t.get('units') == 'bool' or t.get('category') not in CHG_TERM_CATEGORIES:
                continue
            key = (t['category'], t['units'])
            if key not in groups or (t['value'], t['id']) < (groups[key]['value'], groups[key]['id']):
                groups[key] = dict(id=t['id'], value=t['value'])
        cats = ty.get('categories') or {}
        for c in CHG_TERM_CATEGORIES:
            want = {u: g for (cc, u), g in groups.items() if cc == c}
            if not same((cats.get(c) or {}).get('minimum_by_units'), want, 1e-9):
                bad.append('%s R1-H14 %s: per-units minima not recomputed (a minimum across units or categories is never allowed)' % (cid, c))
        gov = groups.get(('contract_mandated', 'mm'))
        if gov is None or not same(ty.get('governing'), dict(category='contract_mandated', term_id=gov['id'], value=gov['value'], units='mm'), 1e-9) \
                or not same([h['margin'], h['units']], [gov['value'], 'mm'], 1e-9):
            bad.append('%s R1-H14: governing term / margin is not the minimum contract-mandated mm term' % cid)
        cpass = all(t['pass_'] for t in terms if t.get('category') == 'contract_mandated')
        ppass = all(t['pass_'] for t in terms if t.get('category') == 'physical_required_elsewhere')
        if any(x is not (cpass and ppass) for x in (ty.get('physical_pass'), h['physical_pass'], sel['pass_'])) or \
                (cats.get('contract_mandated') or {}).get('pass_') is not cpass:
            bad.append('%s R1-H14: physical pass is not contract-mandated AND physical-required (diagnostics never decide)' % cid)
        lu = L['L-CHG']['literal_c_r1_01']['z_prerequisite']['land_unsatisfiability']
        unsat = []
        for x in lu['items']:
            f = feats.get(x['id'])
            if f is None or 'z_lo_adv' not in f:
                bad.append('%s R1-H14: 2(v) item %s not among the reported features' % (cid, x['id']))
                continue
            zg = z_gap(zfeat(0.0, lu['h_land_mm']), f)
            if abs(zg - x['z_gap_mm']) > 1e-9 or abs(zg - max(f['z_lo_adv'] - lu['h_land_mm'], -f['z_hi_adv'])) > 1e-9:
                bad.append('%s R1-H14: land 2(v) Z gap of %s not reproduced' % (cid, x['id']))
            if f['z_lo_adv'] <= EPS and not separated(zg):
                unsat.append(x['id'])
        if sorted(unsat) != lu['unsatisfiable_items'] or bool(unsat) != lu['unsatisfiable'] or abs(lu['h_land_mm'] - sel['land_top_mm']) > 1e-12:
            bad.append('%s R1-H14: land 2(v) unsatisfiability not reproduced' % cid)
        if unsat:
            vis = [t for t in terms if t['category'] == 'contract_mandated' and t['id'].startswith('CHG_LAND vs ') and t['id'].endswith('[plan AND Z]')
                   and t['id'].split(' vs ')[1].split(' [')[0] in unsat and t['pass_'] is False]
            if not vis or cpass or h['physical_pass'] is not False:
                bad.append('%s R1-H14: the contracted land 2(v) failure is not visible / not sufficient to fail the check' % cid)
    return bad


def charger_contract_violations(res):
    """R4-3 / R4-5 (validator): every contract quote the attribution rests on is verbatim in its brief (normalized); the charger owner
    question asks the land, block and strict-wedge scope separately and assumes no answer."""
    bad = []
    norm = lambda t: ' '.join(t.replace('**', '').split())
    for q in CHG_CONTRACT_QUOTES:
        if norm(q['text']) not in norm((ROOT / q['source']).read_text(encoding='utf-8')):
            bad.append('contract quote %s not verbatim in %s' % (q['clause'], q['source']))
    for q in res['owner_questions']:
        if q['id'] != 'Q-R1-CHARGER':
            continue
        t = q['question']
        sc = q.get('contract_scope') or {}
        if not all(k in t for k in ('PLAN AND positive Z', 'non-conductive charger land', 'conductive charger block', 'strict-wedge',
                                    'does not assume')) or 'land and block must be Z-separated' in t or \
                len(sc.get('subquestions') or []) != 3 or sc.get('answers_assumed') is not False or sc.get('contract_amended') is not False:
            bad.append('Q-R1-CHARGER does not represent the C-R1-01 scope (land / block / strict wedge) honestly')
    return bad


def charger_category_violations(cx, res):
    """R3-1 / R3-2 / R3-8 (validator): no charger prerequisite is labelled a closure. Every sweep point: CHARGER group == literal
    category, literal => radial, plan, Z and neighbours, plan => radial, supplier-path implications; the reported first-D thresholds
    are re-derived from the decoded sweep; the design-point H14 / L-CHG pass equals the literal category; a pose reported plan-clear
    is re-tested against CHG_ROUTE / CHG_LINK (fresh exact overlap); the plan-prerequisite r_lim reproduces at its pose (fresh
    chg_pose); the strict-wedge width reproduces by a fresh bisection and its supplier path never claims more than its categories."""
    bad = []
    RC = cx.P['V20_charger_land']['route_clearance']
    for cid, L in res['lanes'].items():
        cand = next(c for c in cx.cands if c['id'] == cid)
        C = L['L-CHG']
        rep = C['literal_c_r1_01']
        rows = sweep_rows(L['sweep'])
        for r in rows:
            for t in r['tw']:
                ch = t['charger']
                if t['groups']['CHARGER'] != ch['literal']:
                    bad.append('%s D %.2f tw %.2f: CHARGER group is not the literal closure (prerequisite labelled closure)' % (cid, r['D'], t['tw']))
                if ch['literal'] and not (ch['radial'] and ch['plan'] and ch['z'] and ch['neighbours']):
                    bad.append('%s D %.2f tw %.2f: literal charger closure without every category' % (cid, r['D'], t['tw']))
                if ch['plan'] and not ch['radial']:
                    bad.append('%s D %.2f tw %.2f: plan prerequisite without the radial prerequisite' % (cid, r['D'], t['tw']))
                if ch['sw_complete'] and not (ch['sw_plan'] and ch['sw_neighbours'] and ch['z']):
                    bad.append('%s D %.2f tw %.2f: strict-wedge supplier path complete without its categories' % (cid, r['D'], t['tw']))
                if ch['sw_plan'] and not ch['sw_in_land_range']:
                    bad.append('%s D %.2f tw %.2f: strict-wedge plan without an in-range width' % (cid, r['D'], t['tw']))
                if (ch['literal'] and not ch['literal_v_z_waived']) or (ch['literal_v_z_waived'] and not (ch['radial'] and ch['plan'])) or \
                        (ch['sw_complete'] and not ch['sw_complete_v_z_waived']) or (ch['sw_complete_v_z_waived'] and not ch['sw_plan']):
                    bad.append('%s D %.2f tw %.2f: 2(v)-Z-waived diagnostic inconsistent with its categories' % (cid, r['D'], t['tw']))
        F = rep['first_D']
        for k in CHG_SWEEP_FLAGS:
            first = next((r['D'] for r in rows if any(t['charger'][k] for t in r['tw'])), None)
            if F.get('first_' + k) != first:
                bad.append('%s: reported first D of charger category %s (%s) not the sweep result (%s)' % (cid, k, F.get('first_' + k), first))
        sel = C['selected']
        cats = sel['categories']
        dpt = L['L-RAD']['design_point']
        rr = next((r for r in rows if abs(r['D'] - dpt['D']) < 1e-9), None)
        tt = None if rr is None else next((t for t in rr['tw'] if abs(t['tw'] - dpt['tw']) < 1e-9), None)
        sws = sel['strict_wedge']
        dg = sel['diagnostics']
        if tt is None or any(tt['charger'][k] != cats[k] for k in CHG_CATEGORIES) or \
                (tt['charger']['sw_in_land_range'], tt['charger']['sw_plan'], tt['charger']['sw_neighbours'], tt['charger']['sw_complete'],
                 tt['charger']['literal_v_z_waived'], tt['charger']['sw_complete_v_z_waived']) != \
                (sws['in_land_range'], sws['plan'], sws['neighbours'], sws['complete'], dg['literal_v_z_waived'], sws['complete_v_z_waived']):
            bad.append('%s: design-point charger categories (exact neighbours) differ from the sweep point (window envelopes)' % cid)
        if sel['pass_'] != cats['literal'] or res['candidate_hard_checks'][cid]['R1-H14']['physical_pass'] != cats['literal'] \
                or rep['literal']['pass_'] != cats['literal']:
            bad.append('%s: charger pass / R1-H14 physical pass is not the literal category' % cid)
        if cats['literal'] and not all(cats[k] for k in ('radial', 'plan', 'z', 'neighbours')):
            bad.append('%s: design-point literal charger closure without every category' % cid)
        p = sel['pose']
        if cats['plan'] or cats['literal'] or p['predicates'].get('routes_clear_in_plan'):
            for rid in RC['routes']:
                for poly in (p['land_poly'], p['block_poly']):
                    if g4.overlaps(dict(type='poly', pts=poly), conductor(cx, rid)['geom']):
                        bad.append('%s: reported charger pose collides in plan with %s (Z separation does not waive it)' % (cid, rid))
        for key in ('radial_prerequisite', 'plan_prerequisite'):
            q = rep[key]['pose']
            if q is not None:
                fp = chg_pose(cx, cand, q['orientation'], q['r_centre'], q['az_centre'], q['land'])
                ok = fp['categories']['radial'] and (fp['prereq_pass'] if key == 'plan_prerequisite' else True)
                if not ok or abs(fp['r_lim_required'] - rep[key]['r_lim_required_mm']) > 1e-9:
                    bad.append('%s: %s r_lim requirement not reproduced at its pose' % (cid, key))
        sw_ = rep['strict_wedge_supplier_path']
        if sw_['complete'] and not (sw_['plan'] and sw_['neighbours'] and sw_['z'] and cats['z']):
            bad.append('%s: strict-wedge supplier path claims closure without its categories' % cid)
        if sw_['plan'] and not (sw_['in_land_range'] and sw_['contained_in_wedge']):
            bad.append('%s: strict-wedge supplier plan without the strict containment' % cid)
        if sw_['width_mm'] is not None and abs(strict_wedge(cx, cand, sw_['chg_r_out_mm']) - sw_['width_mm']) > 1e-9:
            bad.append('%s: strict-wedge zero-margin width not reproduced by a fresh bisection' % cid)
        if any(k in rep for k in ('strict_wedge_literal_check', 'r_lim_required_mm', 'required_pose')):
            bad.append('%s: legacy single-number charger claim present (prerequisite presented as the literal requirement)' % cid)
    return bad


def structure_point_violations(res):
    """R2-1: every reported (D, tw) point carries its own STRUCTURE result, group states are derived from those point
    results, and no structural pass is propagated across points (endpoint-OR)."""
    bad = []
    for cid, L in res['lanes'].items():
        sw = sweep_rows(L['sweep'])
        for r in sw:
            for t in r['tw']:
                if 'STRUCTURE' not in t['groups'] or t['groups']['STRUCTURE'] != t['structure']['pass_']:
                    bad.append('%s D %.2f tw %.2f: STRUCTURE group not the point result' % (cid, r['D'], t['tw']))
                if t['structure']['method'] == 'COMPLIANCE_BOUND' and (t['structure']['pass_'] or t['structure']['bound_mm'] < t['structure']['limit_mm'] - EPS):
                    bad.append('%s D %.2f tw %.2f: compliance-bound record inconsistent' % (cid, r['D'], t['tw']))
            if r['groups']['STRUCTURE'] != any(t['structure']['pass_'] for t in r['tw']):
                bad.append('%s D %.2f: per-D STRUCTURE not the OR over its own walls' % (cid, r['D']))
        g = L['L-RAD']['classification']['groups']['STRUCTURE']
        vals = [r['groups']['STRUCTURE'] for r in sw]
        first = next((r['D'] for r in sw if r['groups']['STRUCTURE']), None)
        if g['first_pass_D'] != first or g['always'] != all(vals) or g['never'] != (not any(vals)):
            bad.append('%s: STRUCTURE group state not derived from the per-point results' % cid)
    return bad


def lra_envelope_violations(res):
    """R2-3: labelled envelopes are ordered, never mislabelled and the searched values are reproducible from the authored grids."""
    bad = []
    for cid, L in res['lanes'].items():
        e = L['L-LRA']['envelopes']
        cont, gridv, sel, stv = (e['continuous_upper_bound']['value_mm'], e['authored_grid_maximum']['value_mm'],
                                 e['selected_design_point']['value_mm'], e['structurally_feasible_searched']['value_mm'])
        if e['continuous_upper_bound']['searched'] or e['historical_optimistic']['searched']:
            bad.append('%s: a bound labelled as a search result' % cid)
        if gridv is not None and gridv > cont + EPS:
            bad.append('%s: authored-grid maximum above the continuous bound' % cid)
        if sel is not None and gridv is not None and sel > gridv + EPS:
            bad.append('%s: selected envelope above the authored-grid maximum' % cid)
        if stv is not None and (gridv is None or stv > gridv + EPS):
            bad.append('%s: structurally feasible envelope above the authored-grid maximum' % cid)
        if stv is not None and not L['L-LRA']['structural_rescreen']['structurally_feasible_caseback']:
            bad.append('%s: structurally feasible envelope without a structurally feasible caseback' % cid)
        if L['L-LRA']['fitting_classes'] and stv is None:
            bad.append('%s: LRA fit counted without a structurally feasible combination' % cid)
        for c in L['L-LRA']['classes']:
            for f in c['fit_examples']:
                ev = f.get('evaluated') or {}
                if not (f.get('pass_') is True and (ev.get('z_fit') or {}).get('fits') is True and (ev.get('plan_fit') or {}).get('violations') == []):
                    bad.append('%s %s: credited fit whose evaluated combination fails structure, Z fit or plan' % (cid, c['id']))
        m = L['L-LRA']['material_table'][L['L-LRA']['caseback_material']]
        if gridv is None or abs(m['authored_grid_maximum_mm'] - gridv) > 1e-9 or abs(m['continuous_upper_bound_mm'] - cont) > 1e-9:
            bad.append('%s: candidate envelopes differ from the material table' % cid)
        am = m['authored_grid_argmax']
        if am is not None and abs(am['t_out_mm'] - am['depth_mm'] - am['residual_mm']) > 1e-9:
            bad.append('%s: authored-grid argmax inconsistent' % cid)
    return bad


def arc_search_violations(cx, res):
    """R2-2: the reported design-point local walls are recomputed with the production predicates and must agree with the V03
    reduction (on the floor .. tw grid, inside [t_lo, t_hi] when feasible, t_hi for a through-rear-face arc, the t_hi bracket
    confirmed, an empty interval genuinely infeasible at every grid thickness)."""
    bad = []
    step = cx.P['V03_corridor_arcs']['step_mm']
    for cid, L in res['lanes'].items():
        cand = next(c for c in cx.cands if c['id'] == cid)
        dpt, car = L['L-RAD']['design_point'], L['L-RAD']['carrier']
        D, tw = dpt['D'], dpt['tw']
        defs = {a['reservation']: a for a in arc_defs(cx, cand)}
        for a in L['L-RAD']['arcs']:
            ad_, sr = defs[a['reservation']], a['search']
            G = arc_grid(cx, ad_, tw)
            t = a['t_arc_mm']
            if all(abs(t - g) > 1e-9 for g in G):
                bad.append('%s %s: local wall %.3f not on the V03 grid' % (cid, a['reservation'], t))
                continue
            fresh = arc_eval(cx, cand, D, ad_, t, D / 2.0 - tw, car['rcin'], car['tcw'])
            if any(abs(fresh[k] - a[k]) > 1e-9 for k in ('wall_margin_mm', 'edge_margin_mm', 'straight_margin_mm', 'insertion_margin_mm')):
                bad.append('%s %s: reported arc margins not reproduced' % (cid, a['reservation']))
            if sr['feasible']:
                if not fresh['own_pass'] or not (sr['t_lo_mm'] - EPS <= t <= sr['t_hi_mm'] + EPS):
                    bad.append('%s %s: selected local wall outside its own-feasible interval' % (cid, a['reservation']))
                if a['z_extent'] == 'THROUGH_REAR_FACE' and abs(t - sr['t_hi_mm']) > 1e-9:
                    bad.append('%s %s: through-rear-face arc not at t_hi (coupling reduction)' % (cid, a['reservation']))
                fh = arc_eval(cx, cand, D, ad_, sr['t_hi_mm'], D / 2.0 - tw, car['rcin'], car['tcw'])
                fl = arc_eval(cx, cand, D, ad_, sr['t_lo_mm'], D / 2.0 - tw, car['rcin'], car['tcw'])
                if min(fh['own_decreasing_mm'].values()) < -EPS or not fl['own_pass']:
                    bad.append('%s %s: reported own-feasible interval end not feasible' % (cid, a['reservation']))
                if sr['t_lo_mm'] - step >= G[0] - EPS and arc_eval(cx, cand, D, ad_, round(sr['t_lo_mm'] - step, 9), D / 2.0 - tw,
                                                                    car['rcin'], car['tcw'])['own_pass']:
                    bad.append('%s %s: t_lo bracket not confirmed' % (cid, a['reservation']))
                nxt = sr['t_hi_mm'] + step
                if nxt <= G[-1] + EPS:
                    fn = arc_eval(cx, cand, D, ad_, round(nxt, 9), D / 2.0 - tw, car['rcin'], car['tcw'])
                    if min(fn['own_decreasing_mm'].values()) >= -EPS:
                        bad.append('%s %s: t_hi bracket not confirmed' % (cid, a['reservation']))
            else:
                if any(arc_eval(cx, cand, D, ad_, g, D / 2.0 - tw, car['rcin'], car['tcw'])['own_pass'] for g in (G[0], G[-1], t)):
                    bad.append('%s %s: arc reported infeasible but a grid thickness passes its own predicates' % (cid, a['reservation']))
    return bad


THRESHOLD_TOL = 1e-6


def threshold_expectations(cx, res, cid, cx2, fresh_poses=None):
    """R3-6 (validator): the numeric thresholds of one candidate recomputed independently - from the pinned inputs and fresh
    production / accepted-G4 predicates at the reported design point, never from the reported numbers. Keys: 'threshold_value',
    'required_delta' and 'szm:<term>' (supplier zero-margin entries), per check id. cx2: a fresh context (no cached state)."""
    st = cx.st
    L = res['lanes'][cid]
    cand = next(c for c in cx2.cands if c['id'] == cid)
    sp = g4.Specs(st, cand)
    dp = dict(L['design_point_g4_terms'])
    D, tw = dp['D'], dp['tw']
    ce2 = cx2.ce[cid]
    carrier = solve_carrier(cx2, ce2)
    row = rad_point(cx2, cand, D, tw, carrier, arc_defs(cx2, cand))
    exp = {}
    # H01: REAR allocation minus the lower-web tolerance minus the conductor band (LA-Z-2), from the G2 stacks and G4 parameters
    zb = st.rear_alloc_min() - st.tolpol['t_lower_web'] - st.P['c_rear_route_mm']['max']
    exp['R1-H01'] = {'threshold_value': zb, 'szm:charger_block_height_max_mm': zb}
    # H04: supplier zero-margin terms of the XF edge crossing at the design point
    exp['R1-H04'] = {'szm:' + z['term']: z['value'] for z in zero_terms(sp.edge(dict(D=D, tw=tw, rcin=dp['rcin'], tcw=dp['tcw']), 'XF-J1501'))}
    # H05: H05-LRA-COUPLED terms from fresh G4 specs (U7 straight run, XL-LRA lateral / Z)
    dpr = dict(D=D, tw=tw, rcin=dp['rcin'], tcw=dp['tcw'], t_land=dp['t_land'])
    lm = min(g4.run_check(sp.straight(dpr), False), g4.run_check(sp.edge(dpr, 'XL-LRA'), False), g4.run_check(sp.edge_z(dpr, 'XL-LRA'), False))
    exp['R1-H05'] = dict({'required_delta': max(0.0, -lm)}, **{'szm:' + z['term']: z['value'] for z in zero_terms(sp.edge_z(dict(t_land=dp['t_land']), 'XL-LRA'))})
    # H06: X25 cover fit supplier zero-margin values at the design point
    exp['R1-H06'] = {'szm:' + z['term']: z['value'] for z in g4.fix_pass(g4.run_check(sp.cover_fit(dp)))['supplier_zero_margin']}
    # H07: W1 planning stress per carried material (G1 plate at t_min over the largest S14 cell) and the inter-cell web
    G, V = st.G1in['plate_check'], cx.P['V18_window']
    cells = st.s14geo['cells']
    dims = {k: (max(q[0] for q in v) - min(q[0] for q in v), max(q[1] for q in v) - min(q[1] for q in v)) for k, v in cells.items()}
    big = max(sorted(dims), key=lambda k: (dims[k][0] * dims[k][1], k))
    r_cell = math.hypot(*dims[big]) / 2.0
    t_min = V['t_nom_mm'] - st.tolpol['t_window']
    e7 = {}
    for mat in V['materials']:
        g1m = dict(sapphire='sapphire', cs_glass='cs_glass', polycarbonate='pc')[mat]
        m = G['materials'][g1m]
        e7['szm:sigma_allow_required_MPa_' + mat] = g1.plate(g1m, G['p_test_MPa']['max'], r_cell, m['nu']['max'], m['E_MPa']['min'], t_min, 'ss')[1]
    e7['szm:rib_width_incl_tol_max_mm'] = min(g['gap_mm'] for g in st.s14_cand['corners']['nominal']['optical']['cell_gaps'])
    exp['R1-H07'] = e7
    # H08 / H09: Screen B / A of the reported selected plate re-run; isotropic required thickness by an own bisection on the accepted
    # g4.annular_plate (loaded boss, simply supported edge)
    S = L['L-STR']
    mats, mset = str_mats(cx2, cand, (S.get('split') or {}).get('selected', {}).get('r_split'))
    cfg = S['selected']
    geo = dict(S['geometry'], gap_deg=S['rib_layout']['gap_deg'])
    lim = str_limits(cx2, cfg, mset['outer'])
    sB = screen_eval(geo, mats, cfg, 'B', cx.P['screen_b']['subregions'], cx.p, cx.P['V14_rib_geometry']['K_t'], lim, 41)
    sA = screen_eval(geo, mats, cfg, 'A', cx.P['screen_b']['subregions'], cx.p, cx.P['V14_rib_geometry']['K_t'], lim, 41)
    br = [lim['c_defl'] - sB['w_inside_outline_mm']]
    if lim['rib_top_adv'] is not None:
        br += [sB['rib_band_margin_mm'], cx.zm['z_lower_web_underside_adv'] - (lim['rib_top_adv'] + sB['w_rib_band_mm'])]
    exp['R1-H08'] = {'required_delta': max(0.0, -min(br))}
    R = D / 2.0 - tw + sp.pc_env['radius_mm']
    for a in L['L-RAD']['arcs']:
        if a['z_extent'] == 'THROUGH_REAR_FACE':
            R = max(R, a['R_bore_arc_mm'] + sp.pc_env['radius_mm'])
    mid = cand['caseback']['material']
    m = str_material(st, mid, {'MAT-CERAMIC': 'PC-CERAMIC-GRIND', 'MAT-NF-METAL': 'PC-METAL-MACH', 'MAT-GF-POLY': 'PC-POLY-MOULD'}[mid])
    c_defl = min(st.P['c_cb_rear_mm']['min'], cx.window['standoff_min_mm'])

    def ok(t):
        r_ = g4.annular_plate([(cx.rb, cx.r_step, t, m['E'], m['nu']), (cx.r_step, R, t, m['E'], m['nu'])], cx.p, 'loaded_boss')
        return r_['sigma'] <= m['sigma_allow'] + 1e-9 and r_['w'] < c_defl - 1e-12
    lo, hi = 0.2, 40.0
    t_req = None
    if ok(hi):
        for _ in range(60):
            mid = (lo + hi) / 2.0
            lo, hi = (lo, mid) if ok(mid) else (mid, hi)
        t_req = hi + m['tol_t']
    exp['R1-H09'] = {'threshold_value': t_req, 'szm:required_uniform_nominal_thickness_mm': t_req,
                     'required_delta': max(0.0, -min(sB['stress_margin_MPa'], sA['stress_margin_MPa']))}
    # H10: perimeter bearing stress (accepted g4.post_load) and the split-plate bond shear p r_split / 2 / bond land
    e10 = {'szm:bearing_planning_allowable_MPa': g4.post_load(st, sp, dp)['modes']['compression']['stress_MPa']}
    if (S.get('split') or {}).get('selected'):
        e10['szm:split_bond_shear_strength_MPa'] = cx.p * S['split']['selected']['r_split'] / 2.0 / st.P['bond_lands']['caseback_bond_land_mm']['max']
    exp['R1-H10'] = e10
    # H11: rear-face annulus (bulk / dielectric / through-rear-face arcs), adhesive bond land, smallest feasible face / radial glands
    ann = [tw - sp.pc_mid['od_radius_mm'] - sp.pc_mid['radius_mm']]
    if cand.get('dielectric_sectors'):
        pc = st.I['process_classes'][cand['dielectric_sector_process']]
        ann.append(tw - pc['od_radius_mm'] - pc['radius_mm'])
    for a in L['L-RAD']['arcs']:
        if a['z_extent'] == 'THROUGH_REAR_FACE':
            pc = st.I['process_classes']['PC-POLY-MOULD' if a['local_material'] == 'MAT-GF-POLY' else
                                         ('PC-METAL-MACH' if a['local_material'] == 'MAT-NF-METAL' else cand['midcase']['process'])]
            ann.append(a['t_arc_mm'] - pc['od_radius_mm'] - pc['radius_mm'])
    avail = min(ann)
    V11 = cx.P['V11_main_seal_cs']

    def first_cs(topo):
        for cs in grid(dict(start=V11['start'], stop=V11['diagnostic_stop'], step=V11['step'])):
            gd = g4.gland_design(st, sp, topo, cs)
            if all(g4.run_check(x, False) >= -EPS for x in sp.gland('X', 'static_radial' if topo == 'radial' else 'static_face',
                                                                     gd['cs'], gd['h'], gd['g'], gd['tol_h'], gd['tol_g'])):
                return gd
        return None
    gf, gr = first_cs('face'), first_cs('radial')
    adh = st.P['bond_lands']['caseback_bond_land_mm']['max'] + (tw - avail)
    seal = main_seal(cx2, cand, row)
    g11 = h11_typed(seal, L['L-SEAL']['closure']['closed'])['governing']
    exp['R1-H11'] = {'threshold_value': adh, 'szm:required_tw_adhesive_mm': adh,
                     'szm:required_tw_face_mm': None if gf is None else gf['face_annulus'] + (tw - avail),
                     'szm:radial_min_feasible_cs_mm': None if gr is None else gr['cs'], 'required_delta': max(0.0, -g11['value'])}
    # H12: T2-R zero-margin nominal D per switch (enumerated C-R1-02 stack, I-SUM) and the binding button deficit
    btn = lane_btn(cx2, cand, D, True)
    rD = max(D + 2.0 * max(0.0, -r['T2']['T2-R']['I-SUM']['margins']['bore_stack']) for r in btn['switches'].values())
    exp['R1-H12'] = {'threshold_value': rD, 'szm:T2-R_required_D_mm': rD,
                     'required_delta': max(0.0, -min(r['best'][btn['binding_interpretation']]['min_margin'] for r in btn['switches'].values()))}
    # H14: plan-prerequisite r_lim (fresh pose grid), deficit at the fresh seal r_lim, fresh strict-wedge width, block allocation height
    poses = fresh_poses if fresh_poses is not None else chg_poses(cx2, cand, cx.P['V20_charger_land']['adverse_mm'])
    req = min((p['r_lim_required'] for p in poses if p['prereq_pass']), default=None)
    r_lim = seal_r_lim(seal)
    w_sw = strict_wedge(cx2, cand, min(st.res['CHG_CONTACT']['geometry']['r'][1], r_lim - st.P['c_chg_window_mm']['max']))
    exp['R1-H14'] = {'threshold_value': req, 'required_delta': None if req is None else max(0.0, req - r_lim),
                     'szm:strict_wedge_land_mm (supplier zero-margin threshold, land < value strictly; not credited)': w_sw,
                     'szm:block_height_max_mm (allocation; the conservative block-AND-Z screen needs < value strictly)': zb,
                     'szm:caseback_r_lim_required_mm (radial / plan prerequisite only)': req}
    # H17: c_insert zero-margin value from the fresh insertion margins of the design point
    exp['R1-H17'] = {'szm:c_insert_zero_margin_mm': st.P['c_insert_mm']['max'] + min(row['insertion'].values())}
    # H19: LRA ceiling over a pocket floor, LA-LRA-1 residual floor, LA-Z-2 band (own arithmetic from G2 / G4 parameters)
    c_top, mount = st.P['c_lra_top_mm']['max'], st.P['lra_mount_mm']['max']
    H_of = lambda res_: zb - c_top - mount - (res_ + m['tol_t'])
    hs = [H_of(t - d) for t in grid(cx.P['V12_caseback_thickness']['t_out'])
          if g4.run_check(sp.rear_periphery(dict(h_pod=0.0, t_out=t), 0.0), False) >= -EPS and t - m['tol_t'] - m['t_min'] >= -EPS
          for d in cx.P['V22_lra_pocket']['pocket_depths_mm'] if t - d >= m['t_min'] + m['tol_t'] - EPS]
    eg = max(hs) if hs else None
    amin = min(c['height_mm']['min'] for c in st.I['lra_classes'])
    exp['R1-H19'] = {'threshold_value': eg, 'required_delta': None if eg is None else amin - eg,
                     'szm:class_envelope_height_max_mm (authored-grid maximum, before structural qualification)': eg,
                     'szm:class_envelope_height_max_mm (continuous upper bound, not a search result)': H_of(m['t_min'] + m['tol_t'])}
    return exp


def threshold_violations(cx, res, cx2, fresh_poses=None, candidates=None):
    """R3-6 (validator): every numeric field of every GATED / FAIL numeric check (threshold_value, required_delta, each supplier
    zero-margin value) must equal its independent recomputation within THRESHOLD_TOL; a numeric field that cannot be recomputed is a
    violation (no fabricated or stale number survives); a categorical gate must carry categorical evidence instead."""
    bad = []
    for cid in (candidates or sorted(res['candidate_hard_checks'])):
        H = res['candidate_hard_checks'][cid]
        exp = threshold_expectations(cx, res, cid, cx2, (fresh_poses or {}).get(cid))
        for hid, h in sorted(H.items()):
            if h['study_status'] not in ('GATED', 'FAIL') or hid not in NUMERIC_CHECKS:
                continue
            e = exp.get(hid, {})
            got = {}
            for k in ('threshold_value', 'required_delta'):
                if h.get(k) is not None:
                    got[k] = h[k]
            for z in h.get('supplier_zero_margin') or []:
                if isinstance(z, dict) and isinstance(z.get('value'), (int, float)) and not isinstance(z.get('value'), bool):
                    got['szm:' + str(z['term'])] = z['value']
            for k, v in sorted(got.items()):
                if k not in e:
                    bad.append('%s %s: emitted numeric threshold %s = %s is not independently recomputable' % (cid, hid, k, v))
                elif e[k] is None or abs(v - e[k]) > THRESHOLD_TOL * max(1.0, abs(e[k])):
                    bad.append('%s %s: numeric threshold %s = %s differs from its recomputation %s' % (cid, hid, k, v, e[k]))
            for k, v in sorted(e.items()):
                if v is not None and k not in got:
                    bad.append('%s %s: recomputable numeric threshold %s missing from the record' % (cid, hid, k))
    return bad


def envelope_sample_violations(cx, res):
    """R3-1 (validator): at sampled points of the D x bulk-wall grid (its four corners, report extension included, and each design
    point) the exact g4 placements of the case-side supports, stop pads and vent lie inside the window envelopes the sweep's
    same-point charger evaluation uses (the placement rules guarantee it at every point; this re-checks the implementation)."""
    st = cx.st
    bad = []
    V1, V2 = cx.P['V01_D_case_body'], cx.P['V02_tw_bulk']
    for cand in cx.cands:
        L = res['lanes'][cand['id']]
        car = L['L-RAD']['carrier']
        sp = cx.ce[cand['id']].sp
        pts = [(V1['start'], V2['start']), (V1['start'], V2['stop']), (V1['report_stop'], V2['start']), (V1['report_stop'], V2['stop']),
               (L['L-RAD']['design_point']['D'], L['L-RAD']['design_point']['tw'])]
        for D, tw in pts:
            dp = dict(cx.ce[cand['id']].dp0, D=D, tw=tw, rcin=car['rcin'], tcw=car['tcw'])
            b = g4.button_layout(st, sp, dp)
            v = g4.vent_layout(st, sp, dp, b)
            sup = g4.supports_layout(st, sp, dp, b, v)
            F, _ = g4.features(st, sp, dp, b, sup, dict(screws=[]), [], st.res['CHG_CONTACT']['geometry']['r'][1])
            exact = [f for f in F if f['kind'] in ('case-side support', 'support pad')]
            if v:
                exact.append(dict(id='VENT_PORT', kind='vent port', z=['MAIN'],
                                  geom=g4.sector(v['centre'] - v['half'], v['centre'] + v['half'], D / 2.0 - tw, D / 2.0)))
            bad += ['D %.2f tw %.2f: %s' % (D, tw, x) for x in envelope_containment_violations(cx, cand, exact)]
    return bad


def asm_dependency_violations(res):
    """R2-5: a physically failed closure dependency never coexists with an executable product or a closed L-ASM lane."""
    bad = []
    for cid, L in res['lanes'].items():
        A = L['L-ASM']
        failed = [d for d in A['dependencies'] if d['state'] == 'FAILED']
        gated = [d for d in A['dependencies'] if d['state'] == 'GATED']
        if failed and A['product_closure_executable']:
            bad.append('%s: product closure executable with failed dependencies' % cid)
        if (failed or gated) and A['disposition'] in ('RESOLVED_GEOMETRICALLY', 'SUPPLIER_GATED'):
            bad.append('%s: L-ASM closed while a closure dependency is failed / gated' % cid)
        seal_ok = L['L-SEAL']['main_seal']['physical_pass'] is True
        a11 = [d for d in A['dependencies'] if d['step'] == 'A11' and 'S-CB-MAIN' in d['requires']]
        if not a11 or (a11[0]['state'] == 'RESOLVED') != seal_ok:
            bad.append('%s: A11 main-seal dependency missing or inconsistent with L-SEAL' % cid)
        if res['dispositions'] and cid == res['ranking']['leader'] and res['dispositions']['L-ASM'] != A['disposition']:
            bad.append('%s: reported L-ASM disposition differs from the dependency rule' % cid)
    return bad


def md_status_violations(md, H):
    """Every hard-check row of the report: status equals the record; never PASS for a non-PASS check; the margin units cell equals the
    record's typed units (R4-8: a dimensionless margin is never printed as mm)."""
    bad = []
    for line in md.splitlines():
        if line.startswith('| R1-H'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            h = H.get(cells[0])
            if h is None or cells[1] != h['study_status']:
                bad.append('markdown status mismatch for ' + cells[0])
            if cells[1] != 'PASS' and 'PASS' in cells[1]:
                bad.append('markdown prints PASS for a non-PASS check ' + cells[0])
            if h is not None and (len(cells) < 5 or cells[4] != cellv(h['units'])):
                bad.append('markdown units mismatch for ' + cells[0])
    return bad


def xml_ok(text):
    try:
        xml.dom.minidom.parseString(text.encode('utf-8'))
        return True
    except Exception:  # noqa: BLE001 - any parse error is a validation failure
        return False


def legacy_column_violations(cx, res):
    """The legacy column must be the accepted G4 bore spec (blanket L_bore_min at its adverse 3.0 mm) at the reported boss."""
    bad = []
    for cid, L in res['lanes'].items():
        sp = g4.Specs(cx.st, next(c for c in cx.cands if c['id'] == cid))
        for sw, r in L['L-BTN']['switches'].items():
            boss = r['T2']['T2-R']['I-SUM']['boss']
            legacy = g4.fast(sp.bore(dict(D=L['L-BTN']['D']), sw, boss))(D=L['L-BTN']['D'], boss=boss)
            if abs(legacy - r['legacy_G4_bore_margin_mm']) > 1e-9:
                bad.append('%s %s: legacy blanket L_bore_min column not the G4 bore spec at 3.0 mm' % (cid, sw))
    return bad


def feats_from_res(st, L):
    return [dict(f, geom=f['geom']) for f in L['features']]


def recompute_pass(cx, res, in_proc, scope):
    """Fresh production-call recomputation of every check reported PASS for the leader."""
    st = cx.st
    lead = res['ranking']['leader']
    L = res['lanes'][lead]
    cand = next(c for c in build_candidates(st, load_json(IN_PATH)) if c['id'] == lead)
    sp = g4.Specs(st, cand)
    dp = dict(L['design_point_g4_terms'])
    feats = feats_from_res(st, L)
    fns = {}
    fns['R1-H02'] = lambda: g4.fast(sp.od(dp))(D=dp['D']) >= -EPS and all(
        g4.run_check(sp.boss(sw, r['T2']['T2-R'][L['L-BTN']['binding_interpretation']]['boss']), False) >= -EPS
        for sw, r in L['L-BTN']['switches'].items())
    fns['R1-H03'] = lambda: in_proc['pass_'] and st.legacy['pass_'] and in_proc['tests'] == 32 and in_proc['caught'] == 32
    fns['R1-H15'] = lambda: (lambda r: r['h17_pass'] and r['h18_pass'])(g4.rf_mag_check(st, feats))
    fns['R1-H16'] = lambda: g4.s14_untouched(st, [f for f in feats if f['kind'] != 'caseback seal flange'], dp)['pass_'] and \
        all(c['pass_'] for c in st.s14geo['carry_in_checks']) and frozen_switches_ok(st)
    fns['R1-H18'] = lambda: (lambda b: g4.support_check(st, sp, dp, g4.supports_layout(st, sp, dp, b, g4.vent_layout(st, sp, dp, b)))['pass_'])(
        g4.button_layout(st, sp, dp))
    fns['R1-H20'] = lambda: r1_scope(load_json(IN_PATH))['pass_'] and in_proc['pass_']
    bad = []
    for hid, h in sorted(res['hard_checks'].items()):
        if h['study_status'] != 'PASS':
            continue
        f = fns.get(hid)
        if f is None:
            bad.append('%s reported PASS without an independent recomputation' % hid)
        elif not f():
            bad.append('%s reported PASS but recomputes as not passing' % hid)
    return bad


def recompute_structure(cx, res):
    """Screen B of the reported selected and best ribbed configurations recomputed from their reported inputs."""
    bad = []
    for cid, L in res['lanes'].items():
        S = L['L-STR']
        cand = next(c for c in cx.cands if c['id'] == cid)
        mats, mset = str_mats(cx, cand, (S.get('split') or {}).get('selected', {}).get('r_split'))
        for key, cfg, lay, rep in [('selected', S['selected'], S['rib_layout'], S['screen_B'])] + (
                [('best_ribbed', S['best_ribbed']['config'], S['best_ribbed']['rib_layout'], S['best_ribbed']['screen_B'])] if S.get('best_ribbed') else []):
            geo = dict(S['geometry'], gap_deg=lay['gap_deg'])
            lay2 = rib_layout(geo, cfg['n'], cfg['w'], cx.P['V13_rib_counts']['phase_divisions'])
            if lay2['gap_deg'] != lay['gap_deg']:
                bad.append('%s %s: rib layout gap not reproduced' % (cid, key))
            s = screen_eval(geo, mats, cfg, 'B', cx.P['screen_b']['subregions'], cx.p, cx.P['V14_rib_geometry']['K_t'],
                            str_limits(cx, cfg, mset['outer']), 41)
            if abs(s['sigma_governing_MPa'] - rep['sigma_governing_MPa']) > 1e-6 * max(1.0, abs(rep['sigma_governing_MPa'])) or \
                    abs(s['w_max_mm'] - rep['w_max_mm']) > 1e-9 * max(1.0, abs(rep['w_max_mm'])):
                bad.append('%s %s: Screen B not reproduced from the reported configuration' % (cid, key))
            top = str_limits(cx, cfg, mset['outer'])['rib_top_adv']
            if top is not None and top > cx.zm['z_band_lo_adv'] + EPS:
                bad.append('%s %s: rib enters the conductor band' % (cid, key))
    return bad


def recompute_diameters(st, in_proc, res, poses=None, cx2=None):
    """Fresh context and fresh sweep of the leader: D_min / D_complete / D_radial_core recomputed; every (D, tw) point's groups,
    structural record and charger categories compared with the report."""
    cx2 = cx2 if cx2 is not None else Ctx(st, load_json(IN_PATH), in_proc['res'], poses=poses)
    lead = res['ranking']['leader']
    cand = next(c for c in cx2.cands if c['id'] == lead)
    sw = sweep_candidate(cx2, cand)
    cls = classify(cx2, cand, sw)
    rep = next(c for c in res['candidates'] if c['id'] == lead)
    bad = []
    for k in ('D_min', 'D_complete', 'D_radial_core'):
        if cls[k] != rep[k]:
            bad.append('%s: reported %s %s, recomputed %s' % (lead, k, rep[k], cls[k]))
    # every (D, tw) point: fresh per-point groups (STRUCTURE included) equal the reported ones (R2-1)
    rsw = {round(r['D'], 6): r for r in sweep_rows(res['lanes'][lead]['sweep'])}
    for r in sw['rows']:
        rr = rsw.get(round(r['D'], 6))
        if rr is None:
            bad.append('%s D %.2f: point missing from the report' % (lead, r['D']))
            continue
        for t, tt in zip(r['tw_rows'], rr['tw']):
            fs_ = t['structure']
            if t['groups'] != tt['groups'] or abs(t['tw'] - tt['tw']) > 1e-9:
                bad.append('%s D %.2f tw %.2f: reported point groups differ from the fresh evaluation' % (lead, r['D'], t['tw']))
            elif t['charger'] != tt['charger'] or (t['charger_strict_width'] is None) != (tt['charger_strict_width'] is None) or \
                    (t['charger_strict_width'] is not None and abs(t['charger_strict_width'] - tt['charger_strict_width']) > 1e-9):
                bad.append('%s D %.2f tw %.2f: reported charger categories differ from the fresh same-point evaluation' % (lead, r['D'], t['tw']))
            elif fs_['method'] != tt['structure']['method'] or (fs_['bound_mm'] is not None and abs(fs_['bound_mm'] - tt['structure']['bound_mm']) > 1e-9):
                bad.append('%s D %.2f tw %.2f: per-point structural result not reproduced' % (lead, r['D'], t['tw']))
            elif not same([t[k] for k in SWEEP_SEAL_COLUMNS], [tt[k] for k in SWEEP_SEAL_COLUMNS], 2e-9):
                bad.append('%s D %.2f tw %.2f: per-point seal population columns (r_lim, flange top, typed reductions) not reproduced' % (
                    lead, r['D'], t['tw']))
    if res['ranking']['selected_D'] is not None and res['ranking']['selected_D'] > 51.0 + EPS:
        bad.append('selected diameter above 51.00 mm')
    if res['ranking']['selected_D'] is not None and res['ranking']['selected_D'] != cls['D_complete']:
        bad.append('selected diameter differs from the recomputed D_complete')
    # pack predicate recomputed with a fresh Specs object
    sp = g4.Specs(st, cand)
    pm = g4.run_check(sp.pack(dict(rcin=sw['carrier']['rcin'])), False)
    if pm < -EPS or abs(pm - res['lanes'][lead]['L-RAD']['carrier']['pack_margin_mm']) > 1e-9:
        bad.append('pack predicate not reproduced')
    return bad, dict(cls, poses=sw['poses'])


def z_delta_of(cx, feats):
    cb = [f for f in feats if f['kind'] in ('caseback rib', 'charger land', 'caseback seal flange', 'caseback centre plate', 'charger contacts')]
    below = max([0.0] + [-f['z_lo_adv'] for f in cb])
    above = max([0.0] + [f['z_hi_adv'] - cx.zm['z_band_lo_adv'] for f in cb if f['kind'] != 'caseback seal flange'])
    return below + above


def r1_validate(res, files, cx, in_proc, elapsed, run_heavy=True):
    st = cx.st
    fails = []
    r1in = load_json(IN_PATH)
    for name, text in files.items():
        p = GEN / name
        if not p.is_file() or p.read_bytes() != text.encode('utf-8'):
            fails.append('%s: missing or differs from in-memory regeneration' % name)
        if len(text.encode('utf-8')) > r1in['budgets']['generated_file_max_bytes']:
            fails.append('%s exceeds the 2 MB budget' % name)
    if (GEN / SWEEP_NAME).exists() and SWEEP_NAME not in files:
        fails.append('stale optional sweep file present')
    for name in ('g4_r1_plan.svg', 'g4_r1_sections.svg'):
        if not xml_ok(files[name]):
            fails.append(name + ': not well-formed XML')
    scope = r1_scope(r1in)
    fails += ['scope: %s failed' % k for k, v in scope['checks'].items() if not v]
    fails += ['input contract: %s' % b for b in input_contract_violations(r1in)]
    if (set(g4.ALLOWED_CHANGES) - set(G4_ORIGINAL_ALLOWED)) != set(R1_FILES):
        fails.append('in-process ALLOWED_CHANGES extension differs from R1_FILES')
    if not in_proc['pass_'] or in_proc['tests'] != 32 or in_proc['caught'] != 32 or in_proc['fails']:
        fails.append('historical G4 in-process reproduction failed: %s' % in_proc['fails'])
    for cid, H in res['candidate_hard_checks'].items():
        fails += ['%s %s' % (cid, b) for b in state_violations(H)]
    fails += md_status_violations(files['g4_r1_blockers.md'], res['hard_checks'])
    if verdict_of(res['dispositions'], res['stops']) != res['verdict']:
        fails.append('verdict is not the pure function of dispositions and stops')
    if res['verdict'] not in VERDICTS:
        fails.append('verdict outside the brief vocabulary')
    fails += legacy_column_violations(cx, res)
    for cid, L in res['lanes'].items():
        for sw, r in L['L-BTN']['switches'].items():
            if set(r['best']) != {'I-SUM', 'I-MAX'} or any(set(r['T2'][t]) != {'I-SUM', 'I-MAX'} for t in r['T2']):
                fails.append('%s %s: C-R1-03 columns missing' % (cid, sw))
        if any(v == 'T1' for v in L['L-BTN']['selected_topology'].values() if v):
            fails.append('%s: T1 selected' % cid)
        if L['L-BTN']['disposition'].startswith('RESOLVED_UNDER_I-MAX_ONLY') and L['L-BTN']['closed']:
            fails.append('%s: I-MAX-only button closure counted as closed' % cid)
        if set(L['L-RAD']['h05_geom']['terms']) & set(L['L-RAD']['h05_lra_coupled']) or any('XL' in t for t in L['L-RAD']['h05_geom']['terms']):
            fails.append('%s: H05-GEOM blended with H05-LRA-COUPLED' % cid)
        if z_delta_of(cx, L['features']) > EPS:
            fails.append('%s: nonzero R1 Z delta' % cid)
    if any(v > EPS for v in res['z']['g4_z_delta_mm'].values()):
        fails.append('nonzero total Z delta reported')
    if res['search']['evaluations'] > r1in['budgets']['evaluations_budget']:
        fails.append('evaluation budget exceeded')
    if any(x['status'] not in ('REPRODUCED', 'EXPLAINED') for x in res['lead_crosschecks']):
        fails.append('lead cross-check not reproduced or explained')
    an = res['solver_anchors']
    if not (an['isotropic_limit_pass'] and an['no_rib_anchor']['pass_'] and an['h_rib_zero']['equal'] and an['convergence_pass']):
        fails.append('solver anchor failure')
    ids = [a['id'] for a in res['lead_adjudications']]
    if sorted(ids) != sorted(['LA-STR-1', 'LA-STR-2', 'LA-STR-3', 'LA-STR-4', 'LA-STR-5', 'LA-Z-1', 'LA-Z-2', 'LA-BTN-1', 'LA-BTN-2', 'LA-LRA-1',
                              'LA-ASM-1', 'LA-HC-1']) or any(a['source'] != 'G4-R1 correction adjudication 2026-10-15' for a in res['lead_adjudications']):
        fails.append('lead adjudications not recorded verbatim with source')
    norm = lambda t: ' '.join(t.replace('**', '').split())
    brief = norm((ROOT / BRIEF).read_text(encoding='utf-8'))
    if any(norm(o['verbatim']) not in brief for o in res['owner_decisions']):
        fails.append('owner decisions not verbatim from the brief')
    ceiling = r1in['parameters']['V01_D_case_body']['ceiling_mm']
    for cid, H in res['candidate_hard_checks'].items():
        fails += ['%s %s' % (cid, b) for b in isolation_violations(H)]
    fails += recompute_pass(cx, res, in_proc, scope)
    fails += recompute_structure(cx, res)
    fails += whole_design_violations(res, ceiling)
    fails += compliance_violations(cx, res, ceiling)
    fails += structure_point_violations(res)
    fails += lra_envelope_violations(res)
    fails += lra_binding_violations(cx, res, r1in)
    fails += h11_violations(cx, res)
    fails += seal_population_violations(cx, res)
    fails += h14_violations(cx, res)
    fails += charger_contract_violations(res)
    fails += asm_dependency_violations(res)
    fails += arc_search_violations(cx, res)
    fails += charger_category_violations(cx, res)
    if run_heavy:
        cx2 = Ctx(st, r1in, in_proc['res'], poses=cx.poses)
        bad, fresh = recompute_diameters(st, in_proc, res, cx.poses, cx2)
        fails += bad
        fails += threshold_violations(cx, res, cx2, {res['ranking']['leader']: fresh['poses']})
        fails += envelope_sample_violations(cx2, res)
    if elapsed() > r1in['budgets']['check_runtime_max_s']:
        fails.append('check runtime %.1f s exceeds %d s' % (elapsed(), r1in['budgets']['check_runtime_max_s']))
    return fails


# --------------------------------------------------------------------------------------------
# Self-test: production-path mutations (every mutation drives the functions used by build / check)
# --------------------------------------------------------------------------------------------
TEST_CATEGORIES = dict(
    PIF='production_input_fault_injections: an authored input / parameter / record (r1in, G4 parameters, reservations, candidate '
        'definitions, supplied classes, term sets, scope path lists) is mutated and a production function detects it',
    PGF='production_geometry_fault_injections: a physical geometry / feature / pose / plate / gap / state object is injected into a '
        'production predicate, solver or rule function and that production function detects it',
    PA='solver / positive anchors: a known value or property is reproduced by the production path; nothing is injected',
    VS='validator_semantic_tests: a tampered result object (states, thresholds, isolation, compliance, sweep flags, reported '
       'geometry) is rejected by the independent validator rules or its fresh recomputation',
    SR='serialization / result-object tests: output bytes, XML or report format')


def r1_self_tests(res, files, cx, in_proc, Es):
    """Production-path self-tests in five explicitly separated categories (R3-10, TEST_CATEGORIES): PIF production input fault
    injection, PGF production geometry fault injection, PA solver / positive anchor, VS validator semantic test, SR serialization /
    result-object test. A test whose fault lives only in the result object is never counted as a fault injection."""
    st = cx.st
    lead = res['ranking']['leader']
    E = Es[lead]
    cand = E['cand']
    ce = cx.ce[lead]
    sp = ce.sp
    r1in = load_json(IN_PATH)
    T = []

    def t(name, fn, cat, notes=None):
        try:
            caught = bool(fn())
            err = None
        except StudyError as exc:
            caught, err = cat != 'PA', 'StudyError: ' + str(exc)
        except Exception as exc:  # noqa: BLE001 - an unexpected exception is a test failure, recorded
            caught, err = False, '%s: %s' % (type(exc).__name__, exc)
        if not caught and notes:
            err = '; '.join(([err] if err else []) + notes[:6])
        T.append(dict(id=name, category=cat, caught=caught, note=err))

    car, arcs = E['sweep']['carrier'], E['sweep']['arcs']
    geom_first = E['classification']['groups']['H05-GEOM']['first_pass_D']
    t('d_below_true_h05_requirement', lambda: not rad_tw(cx, cand, round(geom_first - 0.05, 2), car, arcs)[0]['h05_geom_pass'], 'PGF')
    t('d_51_01', lambda: ce.f['od'](D=51.01) < 0 and fresh_h02_fails(cx, cand, 51.01), 'PGF')
    t('false_d48_with_positive_h05', lambda: bool(reported_d_mismatch(cx, in_proc, res, 'D_radial_core', 48.0)), 'VS')
    t('caseback_thickness_0p10', lambda: not lane_str(cx, cand, E['row'], E['chg']['r_lim'], E['chg']['pose'], False)['physical_pass']
      and thin_caseback_fails(cx, cand, 0.10), 'PGF')
    br = E['strl'].get('best_ribbed') or dict(config=dict(E['strl']['selected'], n=12, w=0.8, h=0.8))
    t('rib_height_mutation', lambda: rib_mutation_caught(cx, res, lead, 'h', br['config']['h'] + 0.2), 'VS')
    t('rib_width_mutation', lambda: rib_mutation_caught(cx, res, lead, 'w', br['config']['w'] - 0.2), 'VS')
    t('rib_count_mutation', lambda: rib_mutation_caught(cx, res, lead, 'n', 8 if br['config']['n'] != 8 else 24), 'VS')
    t('h_rib_zero_gives_D_plate', lambda: rib_D(190000.0, 0.31, 0.98, 0.8, 0.0, 9.0)[1] == rib_D(190000.0, 0.31, 0.98, 0.8, 0.0, 9.0)[0]
      and abs(rib_D(190000.0, 0.31, 0.98, 0.8, 1e-6, 9.0)[1] / rib_D(190000.0, 0.31, 0.98, 0.8, 0.0, 9.0)[0] - 1.0) < 1e-6, 'PA')
    t('invented_inner_support', lambda: plate_solve([iso_region(cx.rb, 24.0, 1.0, 190000.0, 0.31)], cx.p, 'ss'), 'PGF')
    t('pressure_domain_cover_radius', lambda: not partition_valid(cx, sp, E['dp'], radius=E['dp']['a_cover']) and partition_valid(cx, sp, E['dp']), 'PGF')
    t('nonzero_battery_load', lambda: forbidden_mutation(cx, E, 'LOWER_WEB'), 'PGF')
    t('nonzero_rear_pcb_load', lambda: forbidden_mutation(cx, E, 'S14_OUTLINE'), 'PGF')
    t('nonzero_g3_support_land_load', lambda: forbidden_mutation(cx, E, 'S14_SUPPORT'), 'PGF')
    t('nonzero_lower_web_load', lambda: forbidden_mutation(cx, E, 'LOWER_WEB', branch='CARRIER_LOWER_WEB'), 'PGF')
    t('rcin_23p10_pack_failure', lambda: ce.f['pack'](R_carrier_inner=23.10) < -EPS, 'PA')
    t('charger_40x50_evaluated', lambda: charger_size_mutation(cx, cand, r1in, E), 'PIF')
    t('charger_centre_r20_inner_land', lambda: not chg_pose(cx, cand, 0, 20.0, 90.0, 1.0)['prereq_pass']
      and chg_pose(cx, cand, 0, 20.0, 90.0, 1.0)['margins']['land_inner_s14'] < 0, 'PGF')
    t('boot_rim_2p0_evaluated', lambda: rim_mutation(cx, cand), 'PIF')
    t('conductive_sw5_button', lambda: feature_flag_mutation(st, E, 'SW5_PLUNGER', 'conductive', 'h17'), 'PGF')
    t('ferromagnetic_sw4', lambda: feature_flag_mutation(st, E, 'SW4_PLUNGER', 'ferromagnetic', 'h18'), 'PGF')
    t('t1_selected', lambda: t1_selection_caught(cx, res, lead), 'VS')
    t('pusher_outside_frozen_window', lambda: btn_section(btn_terms(cx, cand, 'SW1'), E['D'], 'T2-R', 0.5, 8.0, 'I-SUM')['margins']['tangential'] < 0, 'PGF')
    t('switch_moved', lambda: switch_moved_caught(st), 'PIF')
    t('missing_vent', lambda: missing_vent_caught(cx, cand, E), 'PGF')
    t('broken_seal_graph', lambda: not g4.seal_closure(drop_seal(E['inventory'], 'S-SW1'))['closed'], 'PGF')
    t('duplicate_primary_seal', lambda: not g4.seal_closure(dup_seal(E['inventory'], 'S-COVER'))['closed'], 'PGF')
    t('impossible_flange_residual', lambda: flange_mutation(cx, cand, E), 'PIF')
    t('face_annulus_wider_than_wall', lambda: (lambda o: not o['feasible'] and not o['predicate_feasible_rows']['face_annulus']
                                                         and o['term_reductions']['face_annulus']['value'] < 0)(
        main_seal(cx, cand, rad_point(cx, cand, E['D'], 0.8, car, arcs))['topologies']['face']), 'PGF')
    t('assembly_order_changed', lambda: assembly_mutation(cx, E, 'order'), 'PIF')
    t('assembly_direction_reversed', lambda: assembly_mutation(cx, E, 'direction'), 'PIF')
    t('a5_lra_operation_deleted', lambda: assembly_mutation(cx, E, 'drop:A5'), 'PIF')
    t('a2_vent_operation_deleted', lambda: assembly_mutation(cx, E, 'drop:A2'), 'PIF')
    t('fake_lra_supplied_no_document', lambda: lra_supplied_mutation(cx, cand, E, 'nodoc'), 'PIF')
    t('lra_pocket_too_deep', lambda: pocket_residual_check(cx, cand, E, deepest_bad_pocket(cx, cand, E)) < -EPS
      and E['lra']['pocket']['residual_check_mm'] >= -EPS, 'PGF')
    t('residual_plate_below_material_minimum', lambda: pocket_residual_check(cx, cand, E, None, residual=0.5) < -EPS, 'PGF')
    t('lra_pose_in_chg_route', lambda: 'CHG_ROUTE' in g4.lra_pose_violations(st, [(g4.xy(18.5, 180.0), 0.5)], cx.poses), 'PGF')
    t('lra_pose_in_frozen_g2_corridor', lambda: lra_g2_mutation(cx, cand, E), 'PGF')
    t('nonzero_total_z', lambda: z_delta_of(cx, [dict(f, z_lo_adv=-0.1) if f['kind'] == 'charger land' else f for f in E['features']]) > EPS, 'PGF')
    t('g2_g3_geometry_change', lambda: g2g3_mutation(st, r1in), 'PIF')
    t('mirrored_rear_transform', lambda: mirrored_caught(st), 'PGF')
    t('historical_g4_mutation', lambda: historical_mutation(in_proc), 'SR')
    t('invalid_svg_xml', lambda: not xml_ok(files['g4_r1_plan.svg'].replace('</svg>', '<text>a<b</text></svg>')) and xml_ok(files['g4_r1_plan.svg']), 'SR')
    t('markdown_status_mismatch', lambda: bool(md_status_violations(files['g4_r1_blockers.md'].replace('| R1-H14 | FAIL |', '| R1-H14 | PASS |'),
                                                                    res['hard_checks'])) and not md_status_violations(files['g4_r1_blockers.md'], res['hard_checks']), 'SR')
    t('physical_pass_true_negative_margin', lambda: state_mutation(res, 'neg') and hc_raises(), 'VS')
    t('gated_without_gate_id', lambda: state_mutation(res, 'gate'), 'VS')
    t('structural_failure_affects_verdict', lambda: verdict_mutation(), 'PA')
    t('imax_only_without_adjudication', lambda: btn_disposition(False, True, None).startswith('RESOLVED_UNDER_I-MAX_ONLY')
      and btn_disposition(False, True, 'MAX') == 'SUPPLIER_GATED' and btn_disposition(False, True, 'SUM') == 'OWNER_GATED'
      and imax_closed_caught(cx, res, lead), 'VS')
    t('widened_oring_window', lambda: window_mutation(st, 'widen'), 'PIF')
    t('narrowed_cs_tolerance', lambda: window_mutation(st, 'narrow'), 'PIF')
    t('blanket_L_bore_min_substitution', lambda: legacy_bore_mutation(cx, res, lead), 'VS')
    t('dropping_c_main_case', lambda: btn_section(dict(btn_terms(cx, cand, 'SW1'), c_main_case=None), E['D'], 'T2-R', 0.9, 2.0, 'I-SUM'), 'PIF')
    t('dropping_c_switch', lambda: btn_section(dict(btn_terms(cx, cand, 'SW1'), c_switch=None), E['D'], 'T2-R', 0.9, 2.0, 'I-SUM'), 'PIF')
    t('conductive_charger_land', lambda: conductive_land_caught(cx, cand), 'PIF')
    t('charger_land_overshoot_above_cap', lambda: overshoot_mutation(cx, cand), 'PGF')
    t('charger_land_inside_s14_plus_1p1', lambda: chg_pose(cx, cand, 0, 20.3, 90.0, 1.0)['margins']['land_inner_s14'] < 0, 'PGF')
    t('charger_land_in_radiator_keepout', lambda: radiator_mutation(cx, cand, E), 'PIF')
    t('rib_entering_conductor_band', lambda: str_limits(cx, dict(E['strl']['selected'], n=12, w=0.8, h=1.6, t_out=1.0),
                                                        E['strl']['materials']['outer'])['rib_top_adv'] > cx.zm['z_band_lo_adv'], 'PGF')
    t('polymer_wall_below_floor', lambda: polymer_wall_mutation(cx), 'PGF')
    t('boss_plus_tol_gt_1p0', lambda: g4.run_check(g4.Specs(st, next(c for c in cx.cands if c['id'] == 'G4-A')).boss('SW1', 0.96), False) < 0, 'PGF')
    t('unpermitted_protrusion', lambda: protrusion_mutation(cx, cand, E), 'PGF')
    t('lra_class_from_threshold', lambda: lra_supplied_mutation(cx, cand, E, 'threshold'), 'PIF')
    t('lra_moved_to_other_z_allocation', lambda: not g4.lra_z_band(st, -st.layer('lower_web'), 0.3, st.rear_alloc_min()), 'PGF')
    t('h05_geom_merged_with_lra_coupled', lambda: h05_merge_caught(res, lead), 'VS')
    t('kicad_touched', lambda: not r1_scope(r1in, changed=sorted(set(changed_paths()) | {'rear_sensor/rear_sensor.kicad_pcb'}))['checks']['kicad_interfaces_placement_unchanged'], 'PIF')
    an = res['solver_anchors']
    t('anchor_isotropic_limit', lambda: an['isotropic_limit_pass'] and all(max(v for k, v in d.items() if k != 'regions') <= 1e-6 for d in an['isotropic_limit']), 'PA')
    t('anchor_no_rib_bypass', lambda: an['no_rib_anchor']['pass_'], 'PA')
    t('anchor_n_vs_2n_convergence', lambda: an['convergence_pass'], 'PA')
    t('anchor_monotonicity_tests', lambda: all(all(v.values()) for v in an['monotonicity'].values()), 'PA')
    t('geometry_closed_form_vs_g4', lambda: closed_form_crosscheck(cx, E), 'PA')
    # ---- R2 regressions (kept; recategorised by where the fault lives) ----
    t('r2_01a_point_structure_flag_tampered', lambda: structure_tamper(res, lead, 'flag'), 'VS')
    t('r2_01b_point_structure_record_tampered_fresh_recompute', lambda: structure_tamper_fresh(cx, in_proc, res, lead), 'VS')
    t('r2_01c_selected_point_anchors', lambda: abs(Es['G4-B']['strl']['screen_B']['sigma_governing_MPa'] - 371.783850) < 5e-6
      and abs(Es['G4-B']['strl']['screen_B']['w_max_mm'] - 0.119816560) < 5e-9, 'PA')
    t('r2_01d_bound_below_every_configuration_compliance', lambda: bound_vs_configs(cx, Es['G4-B']), 'PA')
    t('r2_01e_non_dominating_relaxed_model_rejected', lambda: relaxed_mutation_caught(cx, Es['G4-B']), 'PGF')
    t('r2_02a_single_point_pass_not_propagated', lambda: endpoint_or_classify(cx, E), 'PGF')
    t('r2_02b_endpoint_or_flattening_rejected', lambda: structure_tamper(res, lead, 'flatten'), 'VS')
    t('r2_03a_charger_z_separation_does_not_waive_plan', lambda: charger_plan_overlap_caught(cx, cand), 'PGF')
    t('r2_03b_reported_overlapping_pose_rejected', lambda: charger_report_tamper(cx, res, lead), 'VS')
    t('r2_03c_plan_prerequisite_threshold_reproduced', lambda: abs(Es['G4-B']['chg_literal']['plan_prerequisite']['r_lim_required_mm'] - 24.624973) < 5e-6
      and Es['G4-B']['chg_literal']['plan_prerequisite']['pose']['r_centre'] == 21.15
      and Es['G4-B']['chg_literal']['plan_prerequisite']['pose']['az_centre'] == 89.0
      and abs(Es['G4-A']['chg_literal']['plan_prerequisite']['r_lim_required_mm'] - 24.856896) < 5e-6, 'PA')
    t('r2_03d_conductor_views_unified', lambda: conductor_view_tamper(cx, E), 'PGF')
    t('r2_04a_lra_bounds_grid_selected', lambda: lra_bound_anchor(Es['G4-B']), 'PA')
    t('r2_04b_bound_mislabelled_as_search', lambda: lra_label_tamper(res, lead), 'VS')
    t('r2_05a_struct_infeasible_pocket_not_fit', lambda: lra_struct_gate(cx, cand, E), 'PIF')
    t('r2_05b_reported_fit_without_structure_rejected', lambda: lra_fit_tamper(res, lead), 'VS')
    t('r2_06_supplied_lead_exit_collision', lambda: lra_lead_exit_collision(cx, cand, E), 'PIF')
    t('r2_07a_gated_without_numeric_threshold', lambda: gate_threshold_tamper(res), 'VS')
    t('r2_07b_pass_with_gate_raised', lambda: hc_state_tamper(res, 'pass_gate'), 'VS')
    t('r2_07c_physical_failure_hidden_as_gated', lambda: hc_state_tamper(res, 'hide_gated'), 'VS')
    t('r2_07d_physical_failure_hidden_as_pass', lambda: hc_state_tamper(res, 'hide_pass'), 'VS')
    t('r2_08a_a11_main_seal_dependency_production', lambda: a11_dependency_production(cx, E), 'PGF')
    t('r2_08b_product_closure_claim_rejected', lambda: asm_tamper(res, lead), 'VS')
    t('r2_09a_above_limit_candidate_selected_rejected', lambda: selection_tamper(res, lead, 'above'), 'VS')
    t('r2_09b_radial_core_as_compliance_rejected', lambda: selection_tamper(res, lead, 'core'), 'VS')
    t('r2_09c_whole_design_rule_production', lambda: whole_design_production(E, res, lead), 'PGF')
    t('r2_10a_v03_reduction_equals_exhaustive_grid', lambda: v03_exhaustive(cx, Es), 'PA')
    t('r2_10b_v03_reported_wall_off_reduction_rejected', lambda: v03_tamper(cx, res, lead), 'VS')
    # ---- R3 regressions (the thirteen required items, production path where applicable) ----
    cx2 = Ctx(st, r1in, in_proc['res'], poses=cx.poses)
    t('r3_01_zero_z_touching_strict', lambda: zero_gap_semantics(cx, E), 'PGF')
    t('r3_02_charger_screw_collision', lambda: charger_neighbour_case(cx, E, 'caseback screw'), 'PGF')
    t('r3_03_charger_support_collision', lambda: charger_neighbour_case(cx, E, 'case-side support'), 'PGF')
    t('r3_04_strict_wedge_supplier_neighbour_collision', lambda: strict_wedge_neighbour_case(cx, E), 'PGF')
    t('r3_05_lra_fallback_plate_substitution', lambda: lra_fallback_binding_case(cx, E, res, lead, 'plate'), 'PGF')
    t('r3_06_lra_fallback_material_substitution', lambda: lra_fallback_binding_case(cx, E, res, lead, 'material'), 'PGF')
    t('r3_07_forged_h08_isolation', lambda: forged_isolation_case(res, 'R1-H08'), 'VS')
    t('r3_08_forged_non_lra_isolation', lambda: forged_isolation_case(res, None), 'VS')
    t('r3_09_fabricated_h01_threshold', lambda: fabricated_threshold_case(cx, cx2, res, lead, 'R1-H01', 999.0), 'VS')
    t('r3_10_fabricated_h19_threshold', lambda: fabricated_threshold_case(cx, cx2, res, lead, 'R1-H19', 1.5), 'VS')
    t('r3_11_architecture_gated_lra_not_compliant', lambda: compliance_case(cx, E, res, lead, 'architecture'), 'PGF')
    t('r3_12_supplier_owner_gated_lane_not_compliant', lambda: compliance_case(cx, E, res, lead, 'supplier_owner'), 'PGF')
    t('r3_13_charger_radial_prerequisite_not_closure', lambda: radial_prereq_not_closure(cx, E, res, lead), 'PA')
    t('r3_14_charger_prerequisite_labelled_closure_rejected', lambda: charger_label_tamper(cx, res, lead), 'VS')
    t('r3_15_charger_envelope_superset_of_exact_supports', lambda: not envelope_sample_violations(cx, res) and bool(envelope_tamper(cx, E)), 'PGF')
    t('r3_16_charger_same_point_sweep_recomputed', lambda: charger_sweep_tamper_fresh(cx, in_proc, res, lead), 'VS')
    # ---- R4 regressions (classified by where the fault lives; identity tampering of a serialized LRA result is VS) ----
    for i, kind in enumerate(('pose', 'class', 'lead', 'exit', 'pocket_interrupter', 'r_lim', 'depth', 't_out', 'material', 'rib_interruptions'), 1):
        t('r4_%02d_lra_identity_forgery_%s' % (i, kind), lambda kind=kind: lra_identity_forgery(cx, E, res, lead, kind), 'VS')
    t('r4_11_lra_identity_positive_control', lambda: lra_identity_positive(cx, E, res, lead), 'PA')
    t('r4_12_lra_fallback_refuses_physical_mismatch', lambda: lra_production_physical_mismatch(cx, E, res, lead), 'PGF')
    t('r4_13_lra_fallback_derives_pose_and_class', lambda: lra_production_claim_forgery(cx, E, res, lead), 'PGF')
    for i, kind in enumerate(('ratio_as_mm', 'mm_as_ratio', 'value_changed', 'governing_changed', 'pass_with_failing_predicate'), 14):
        t('r4_%02d_h11_typed_%s' % (i, kind), lambda kind=kind: h11_tamper(cx, res, lead, kind), 'VS')
    t('r4_19_h11_typed_positive_control', lambda: not h11_violations(cx, res) and r5_h11_anchor(cx, res, E), 'PA')
    for i, kind in enumerate(('block_as_contract', 'block_governs', 'deg_in_mm_minimum', 'land_v_hidden'), 20):
        t('r4_%02d_h14_typed_%s' % (i, kind), lambda kind=kind: h14_tamper(cx, res, lead, kind), 'VS')
    t('r4_24_block_and_z_never_decides', lambda: block_and_z_never_decides(cx, E), 'PGF')
    t('r4_25_block_route_zero_z_gap_is_not_3d_collision', lambda: block_route_3d_not_collision(cx, E), 'PA')
    t('r4_26_land_v_z_unsatisfiability_closed_form', lambda: land_unsat_closed_form(cx), 'PGF')
    t('r4_27_charger_contract_scope_wording', lambda: charger_scope_tamper(res), 'VS')
    h11_cells = '| R1-H11 | FAIL | false | %s | dimensionless |' % fs(res['hard_checks']['R1-H11']['margin'])
    t('r4_28_markdown_h11_units', lambda: h11_cells in files['g4_r1_blockers.md'] and bool(md_status_violations(files['g4_r1_blockers.md'].replace(
        h11_cells, h11_cells.replace('| dimensionless |', '| mm |')), res['hard_checks'])), 'SR')
    # ---- R5 regressions (seal population evaluation; unit invariance end to end; zero representative-row feedback; input contract) ----
    scope = r1_scope(r1in)
    nt = {}
    msf = E['classification']['main_seal_first'] or {}
    t('r5_01_seal_population_unit_invariance_every_sweep_point', lambda: r5_sweep_population_invariance(cx, cand, E['sweep'], nt.setdefault('r5_01', [])),
      'PA', nt.setdefault('r5_01', []))
    for i, u in enumerate(R5_UNITS, 2):
        t('r5_%02d_end_to_end_study_unit_invariance_%s' % (i, u), lambda u=u, i=i: r5_study_unit_invariance(
            cx, in_proc, Es, scope, u, nt.setdefault('r5_%02d' % i, [])), 'PA', nt.setdefault('r5_%02d' % i, []))
    t('r5_04_end_to_end_unit_invariance_g4b_design_point', lambda: r5_point_unit_invariance(
        cx, in_proc, Es, scope, 'G4-B', (Es['G4-B']['D'], Es['G4-B']['tw']), nt.setdefault('r5_04', [])), 'PA', nt.setdefault('r5_04', []))
    t('r5_05_end_to_end_unit_invariance_first_main_seal_closure_point', lambda: bool(msf) and r5_point_unit_invariance(
        cx, in_proc, Es, scope, lead, (msf['D'], msf['tw']), nt.setdefault('r5_05', [])), 'PA', nt.setdefault('r5_05', []))
    t('r5_06_zero_representative_row_feedback', lambda: r5_zero_feedback(cx, in_proc, Es, scope, nt.setdefault('r5_06', [])), 'PA',
      nt.setdefault('r5_06', []))
    t('r5_07_r4_mixed_unit_key_varies_r5_reductions_do_not', lambda: r5_mixed_unit_key_would_vary(cx, cand, E), 'PA')
    for i, kind in enumerate(('rule_conductive_block', 'r4_rule_text', 'subject_block', 'contract_text_not_verbatim', 'screen_relabelled_contract',
                              'brief_v_in_block_item'), 8):
        t('r5_%02d_input_contract_%s' % (i, kind), lambda kind=kind: r5_input_contract_tamper(r1in, kind), 'PIF')
    for i, kind in enumerate(('flange_top_from_one_row', 'r_lim_from_one_radial_row', 'h11_term_from_one_row', 'supplier_threshold_from_one_row',
                              'representative_physical', 'seal_cs_representative', 'feasible_from_one_row'), 14):
        t('r5_%02d_seal_validator_%s' % (i, kind), lambda kind=kind: r5_seal_validator_tamper(cx, res, lead, kind), 'VS')
    t('r5_21_seal_population_and_input_contract_positive_control', lambda: not seal_population_violations(cx, res)
      and not input_contract_violations(r1in), 'PA')
    t('r5_22_sweep_seal_columns_tampered_fresh_recompute', lambda: r5_sweep_seal_tamper_fresh(cx, in_proc, res, lead), 'VS')
    t('r5_23_button_min_margin_never_mixes_units', lambda: r5_button_margins_unit_typed(res), 'PA')
    return T


def zero_gap_semantics(cx, E):
    """R3-3 on the production predicates: clear() (plan overlapping, Z decides), clear_both() (plan clear, Z decides) and the charger
    route Z predicate of chg_pose (block top just below / at / just above the conductor band floor): +eps gap PASS, exactly zero FAIL,
    -eps overlap FAIL."""
    eps = 1e-6
    poly = E['chg']['pose']['land_poly']
    a = feature('A', 'T', 'x', False, False, dict(type='poly', pts=poly), ['REAR'], zfeat(0.0, 1.0), 'test')

    def b(dz, dx=0.0):
        return feature('B', 'T', 'x', False, False, dict(type='poly', pts=[(x + dx, y) for x, y in poly]), ['REAR'], zfeat(1.0 + dz, 2.0), 'test')
    c3 = [clear(a, b(d), 0.0, 0.0)[0] for d in (eps, 0.0, -eps)]
    b3 = [clear_both(a, b(d, 40.0), 0.0, 0.0)[0] for d in (eps, 0.0, -eps)]
    p, zb = E['chg']['pose'], cx.zm['z_band_lo_adv']
    r3 = [chg_pose(cx, E['cand'], p['orientation'], p['r_centre'], p['az_centre'], p['land'], block_top=zb + s)['predicates']['block_routes_clear_in_z']
          for s in (-eps, 0.0, eps)]
    return c3 == [True, False, False] and b3 == [True, False, False] and r3 == [True, False, False] and separated(eps) and not separated(0.0) \
        and not separated(-eps)


def charger_neighbour_case(cx, E, kind):
    """Production chg_point_eval at a radially / plan admissible caseback limit with a one-neighbour set of the design point: (a) the
    exact neighbour of that kind at its real place and Z: C-R1-01 (v) Z collision (Z, neighbours and literal fail although plan
    passes); (b) the same neighbour raised in Z above the block: cleared, the predicate can close; (c) raised but laid over the whole
    charger wedge in plan: (v) plan collision - plan and literal fail."""
    n0 = next(n for n in E['chg']['nbrs'] if n['kind'] == kind)
    pctx = E['sweep']['pose_ctx']
    rl = E['sweep']['chg_r_lim_required'] + 0.05
    t_top = E['chg']['land_top_mm']
    zb = cx.zm['z_band_lo_adv']
    up = dict(n0, z_lo_adv=zb + 0.05, z_hi_adv=zb + 1.0)
    wedge = g4.sector(77.0, 103.0, 16.0, 26.0)
    over = dict(up, geom=wedge, desc=plan_descriptor(wedge), exact=True)
    a = chg_point_eval(cx, pctx, rl, t_top, [n0])
    b = chg_point_eval(cx, pctx, rl, t_top, [up])
    c = chg_point_eval(cx, pctx, rl, t_top, [over])
    return n0['rule'] == 'v' and a['radial'] and a['plan'] and not a['z'] and not a['neighbours'] and not a['literal'] \
        and b['z'] and b['neighbours'] and b['literal'] and not c['plan'] and not c['literal']


def strict_wedge_neighbour_case(cx, E):
    """R3-2: (a) the production design-point strict-wedge supplier path is not complete and lists the screw / support Z collisions;
    (b) at the first sweep point where its zero-margin pose is plan-admissible, the path with one cleared far neighbour closes, and the
    same path with a support laid over the charger wedge fails in plan and is not complete."""
    s = E['chg']['strict_wedge']
    a = (not s['complete']) and any(r['kind'] == 'caseback screw' and not r['clear'] for r in s['rows']) \
        and any(r['kind'] == 'case-side support' and not r['clear'] for r in s['rows'])
    pt = next(t for r in E['sweep']['rows'] for t in r['tw_rows'] if t['charger']['sw_plan'])
    sp_ = strict_wedge_path(cx, E['cand'], pt['r_lim'])
    n0 = next(n for n in E['chg']['nbrs'] if n['kind'] == 'case-side support')
    zb = cx.zm['z_band_lo_adv']
    up = dict(n0, z_lo_adv=zb + 0.05, z_hi_adv=zb + 1.0)
    wedge = g4.sector(77.0, 103.0, 16.0, 26.0)
    over = dict(up, geom=wedge, desc=plan_descriptor(wedge), exact=True)
    b1 = chg_point_eval(cx, E['sweep']['pose_ctx'], pt['r_lim'], E['chg']['land_top_mm'], [up], sp_)['strict_wedge']
    b2 = chg_point_eval(cx, E['sweep']['pose_ctx'], pt['r_lim'], E['chg']['land_top_mm'], [over], sp_)['strict_wedge']
    return a and sp_['contained'] and b1['plan'] and b1['complete'] and not b2['plan'] and not b2['complete']


def lra_fixture_record(**kw):
    """Self-test supplied class (never an R1 input): a 4 mm coin body with a short lead / exit envelope (0.8 x 0.6 x 0.3 mm, exit cw)."""
    return supplied_record(id='SR4-TEST', lead_exit_envelope_mm=dict(length_mm=dict(min=0.8, nom=0.8, max=0.8), width_mm=dict(min=0.6, nom=0.6, max=0.6),
                                                                    height_mm=dict(min=0.3, nom=0.3, max=0.3), exit=kw.pop('exit', 'cw')), **kw)


def lra_fixture(cx, E, res, lead):
    """R4-1 fixture at the leader's design point: the fixture class in a copied R1 input (authoritative for the validator), two fully
    plan-feasible poses, a non-default admissible plate (depth 0), the production claimed identity, the production fallback record
    and the fit row credited with it. Cached per context."""
    cache = cx.__dict__.setdefault('lra_fixture_cache', {})
    if lead in cache:
        return cache[lead]
    cand, sctx, strl = E['cand'], E['sweep']['sctx'], E['strl']
    r1fx = dict(load_json(IN_PATH), lra_supplied=[lra_fixture_record()])
    classes = lra_authoritative_classes(cx, res['lanes'][lead]['L-LRA'], r1fx)
    cls = next(c for c in classes if c['id'] == 'SR4-TEST')
    mats_fn, _ = str_mats(cx, cand, (strl.get('split') or {}).get('selected', {}).get('r_split'))
    lctx = dict(classes=classes, ex=lra_exclusion_set(cx, cand, E['dp'], E['chg'], strl), dp_g4=E['dp'], r_lim=E['chg']['r_lim'])
    poses = []
    for p in lra_supplied_poses(cx, cls, E['chg']['r_lim']):
        if not p['viol'] and not lra_plan_check(cx, cand, p['env'], lctx):
            poses.append(p)
            if len(poses) == 2:
                break
    p, p2 = poses
    t_in = max(sctx['t_in'])
    t_out = min(t for t in sctx['t_out'] if t < max(sctx['t_out']))
    plate = (t_in, t_out, 0.0, t_out)
    claimed = lra_claimed_identity(cx, cand, cls, p, plate, mats_fn, strl['geometry'], lctx)
    body, lead_c = lra_phys_of(cls, p, p['env'])
    rec = lra_struct_fallback(cx, cand, sctx, strl, mats_fn, claimed, dict(body=body, lead=lead_c), plate, lctx)
    fit = dict(az=p['az'], r=p['r'], ori=p['ori'], t_in=t_in, t_out=t_out, depth=0.0, residual=t_out, H=rec['evaluated']['z_fit']['ceiling_mm'],
               combination=rec['combination'], evaluated=rec['evaluated'], structural=rec['structural'], pass_=rec['pass_'],
               sigma_B=rec['sigma_B'], w_B=rec['w_B'])
    out = dict(cand=cand, sctx=sctx, strl=strl, r1fx=r1fx, classes=classes, cls=cls, mats_fn=mats_fn, lctx=lctx, p=p, p2=p2, plate=plate,
               claimed=claimed, body=body, lead=lead_c, rec=rec, fit=fit)
    cache[lead] = out
    return out


def lra_fit_res(res, lead, fit):
    mut = copy.deepcopy(res)
    mut['lanes'][lead]['L-LRA']['classes'].append(dict(id=(fit['combination'].get('lra_class') or {}).get('id'), fits=True,
                                                       structurally_feasible_fits=1, fit_examples=[fit]))
    return mut


def lra_identity_forgery(cx, E, res, lead, kind):
    """R4-2 (validator): a serialized credited fit is tampered in one physical-identity field; every variant must be rejected by
    lra_binding_violations with a message naming the field, and the untampered fit must pass. Variants per kind: (a) the claim (or the
    evaluated record) changed while the other side remains old; (b) claim and evaluated record changed consistently while the
    physical record they rest on (circles / gaps / geometry) remains old - caught by the independent reconstruction."""
    fx = lra_fixture(cx, E, res, lead)
    st = cx.st
    fit = fx['fit']
    cb, ev = fit['combination'], fit['evaluated']

    def mutate(side_fn, both=False, row=None):
        f = copy.deepcopy(fit)
        side_fn(f['evaluated'] if not both else f['combination'])
        if both:
            side_fn(f['evaluated'])
        if row:
            row(f)
        return f
    shift = lambda xs, d: [[x[0] + d, x[1], x[2]] for x in xs]
    if kind == 'pose':
        new = dict(cb['pose'], az_deg=(cb['pose']['az_deg'] + 5.0) % 360.0)
        a = copy.deepcopy(fit)
        a['combination']['pose'] = new
        a['az'] = new['az_deg']
        b = copy.deepcopy(a)
        b['evaluated']['pose'] = dict(new)
        variants, keys = [a, b], ('pose', 'body_envelope')
    elif kind == 'class':
        coin = lra_class_physical(dict(next(c for c in st.I['lra_classes'] if c['id'] == 'LRA-COIN-D8'), supplied=False))
        a = copy.deepcopy(fit)
        a['combination']['lra_class'] = coin
        b = copy.deepcopy(fit)
        b['combination']['lra_class'] = dict(cb['lra_class'], id='LRA-COIN-D8')
        b['evaluated']['lra_class'] = dict(ev['lra_class'], id='LRA-COIN-D8')
        variants, keys = [a, b], ('lra_class',)
    elif kind == 'lead':
        variants = [mutate(lambda d: d['lead_envelope'].update(circles=shift(d['lead_envelope']['circles'], 0.2))),
                    mutate(lambda d: d['lead_envelope'].update(circles=shift(d['lead_envelope']['circles'], 0.2)), both=True)]
        keys = ('lead_envelope',)
    elif kind == 'exit':
        variants = [mutate(lambda d: d['exit_envelope'].update(direction='ccw')), mutate(lambda d: d['exit_envelope'].update(direction='ccw'), both=True)]
        keys = ('exit_envelope',)
    elif kind == 'pocket_interrupter':
        def it(d):
            d['pocket']['footprint_az_deg'] = [(x + 3.0) % 360.0 for x in d['pocket']['footprint_az_deg']]
            for i in d['structure']['interrupters']:
                if i[0] == 'LRA_POCKET':
                    i[1] = [(x + 3.0) % 360.0 for x in i[1]]
        variants, keys = [mutate(it), mutate(it, both=True)], ('pocket',)
    elif kind == 'r_lim':
        def rl(d):
            d['r_lim_mm'] += 0.5
            d['seal_flange']['r_lim_mm'] += 0.5
        variants, keys = [mutate(rl), mutate(rl, both=True)], ('r_lim_mm',)
    elif kind == 'depth':
        def dep(d):
            d['plate'].update(depth_mm=d['plate']['depth_mm'] + 0.1, residual_mm=d['plate']['residual_mm'] - 0.1)
        variants = [mutate(dep), mutate(dep, both=True, row=lambda f: f.update(depth=f['depth'] + 0.1, residual=f['residual'] - 0.1))]
        keys = ('plate', 'pocket', 'z_fit')
    elif kind == 't_out':
        t2 = max(fx['sctx']['t_out'])
        variants = [mutate(lambda d: d['plate'].update(t_out_mm=t2)), mutate(lambda d: d['plate'].update(t_out_mm=t2), both=True,
                                                                           row=lambda f: f.update(t_out=t2))]
        keys = ('plate',)
    elif kind == 'material':
        other = 'MAT-NF-METAL' if cb['plate']['materials'] != ['MAT-NF-METAL'] else 'MAT-CERAMIC'
        variants = [mutate(lambda d: d['plate'].update(materials=[other])), mutate(lambda d: d['plate'].update(materials=[other]), both=True)]
        keys = ('plate',)
    elif kind == 'rib_interruptions':
        def ri(d):
            d['structure']['interrupters'] = [i for i in d['structure']['interrupters'] if i[0] != 'CHARGER_LAND']
        variants, keys = [mutate(ri), mutate(ri, both=True)], ('structure',)
    else:
        raise StudyError('unknown forgery kind %s' % kind)
    ok = not lra_binding_violations(cx, lra_fit_res(res, lead, fit), fx['r1fx'])
    for v in variants:
        bad = lra_binding_violations(cx, lra_fit_res(res, lead, v), fx['r1fx'])
        ok = ok and any(any(k in b for k in keys) for b in bad)
    return ok


def lra_identity_positive(cx, E, res, lead):
    """R4-2 positive control: the unchanged, correctly reconstructed physical combination passes (claimed == evaluated == reconstructed,
    fresh fallback re-run reproduces the recorded structural result) and its derived pose / class are the claimed ones."""
    fx = lra_fixture(cx, E, res, lead)
    ev = fx['fit']['evaluated']
    return not lra_binding_violations(cx, lra_fit_res(res, lead, fx['fit']), fx['r1fx']) and ev['lra_class']['id'] == 'SR4-TEST' \
        and ev['exit_envelope']['direction'] == 'cw' and ev['pose']['az_deg'] == float(fx['p']['az']) and not ev['plan_fit']['violations']


def lra_production_physical_mismatch(cx, E, res, lead):
    """R4-2 (production): the exact fallback, given the claimed identity of the fixture and PHYSICAL inputs that differ from it, refuses
    every one: lead circles moved, lead / exit regenerated on another side, body moved (pocket footprint / angular interrupter), r_lim
    of the plan context, pocket depth, t_out, the plate material function, and an extra rib interrupter. The unmodified call binds."""
    fx = lra_fixture(cx, E, res, lead)
    cand, sctx, strl, mats_fn, lctx, plate = fx['cand'], fx['sctx'], fx['strl'], fx['mats_fn'], fx['lctx'], fx['plate']
    p = fx['p']
    st = cx.st

    def refused(phys=None, plate_=None, lctx_=None, mats_=None, strl_=None):
        try:
            lra_struct_fallback(cx, cand, sctx, strl_ or strl, mats_ or mats_fn, fx['claimed'], phys or dict(body=fx['body'], lead=fx['lead']),
                                plate_ or plate, lctx_ or lctx)
            return False
        except StudyError:
            return True
    ok = not refused()
    ok = ok and refused(phys=dict(body=fx['body'], lead=[((q[0] + 0.2, q[1]), r) for q, r in fx['lead']]))
    cls_ccw = dict(fx['cls'], lead_exit_envelope_mm=dict(fx['cls']['lead_exit_envelope_mm'], exit='ccw'))
    b2, l2 = supplied_envelope(cls_ccw, p)
    ok = ok and refused(phys=dict(body=b2, lead=l2))
    b3, l3 = supplied_envelope(fx['cls'], dict(p, az=p['az'] + 5))
    ok = ok and refused(phys=dict(body=b3, lead=l3))
    ok = ok and refused(lctx_=dict(lctx, r_lim=lctx['r_lim'] - 0.3))
    ok = ok and refused(plate_=(plate[0], plate[1], 0.1, round(plate[1] - 0.1, 9)))
    t2 = max(sctx['t_out'])
    ok = ok and refused(plate_=(plate[0], t2, 0.0, t2))
    metal = str_material(st, 'MAT-NF-METAL', 'PC-METAL-MACH')
    alt = str_material(st, 'MAT-CERAMIC', 'PC-CERAMIC-GRIND') if fx['claimed']['plate']['materials'] == ['MAT-NF-METAL'] else metal
    ok = ok and refused(mats_=lambda r: alt)
    g = dict(strl['geometry'], interrupters=list(strl['geometry']['interrupters']) + [dict(id='FAKE_RIB_STOP', az=[10.0, 20.0], r=[17.0, 23.0])])
    ok = ok and refused(strl_=dict(strl, geometry=g))
    return ok


def lra_production_claim_forgery(cx, E, res, lead):
    """R4-2 (production): a claim whose pose or class differs from the physical circles the fallback evaluates is refused - the
    evaluated pose / class are derived from the circles, never copied from the claim."""
    fx = lra_fixture(cx, E, res, lead)
    cand, sctx, strl, mats_fn, lctx, plate = fx['cand'], fx['sctx'], fx['strl'], fx['mats_fn'], fx['lctx'], fx['plate']
    phys = dict(body=fx['body'], lead=fx['lead'])
    out = []
    coin = dict(next(c for c in cx.st.I['lra_classes'] if c['id'] == 'LRA-COIN-D8'), supplied=False)
    for claim in (lra_claimed_identity(cx, cand, fx['cls'], fx['p2'], plate, mats_fn, strl['geometry'], lctx),
                  lra_claimed_identity(cx, cand, coin, fx['p'], plate, mats_fn, strl['geometry'], lctx)):
        try:
            lra_struct_fallback(cx, cand, sctx, strl, mats_fn, claim, phys, plate, lctx)
            out.append(False)
        except StudyError as exc:
            out.append('pose' in str(exc) or 'lra_class' in str(exc))
    return all(out)


def h11_tamper(cx, res, lead, kind):
    """R4-9 (validator): one tampered typed R1-H11 record per kind is rejected by h11_violations; the unmodified result passes."""
    mut = copy.deepcopy(res)
    h = mut['candidate_hard_checks'][lead]['R1-H11']
    ty = h['typed']
    terms = {x['id']: x for o in ty['topologies'].values() for x in o['terms']}
    if kind == 'ratio_as_mm':
        terms['H11-RADIAL-gland_compression_min']['units'] = 'mm'
    elif kind == 'mm_as_ratio':
        terms['H11-ADHESIVE-bond_land_annulus']['units'] = 'dimensionless'
    elif kind == 'value_changed':
        terms['H11-FACE-face_annulus']['value'] = terms['H11-FACE-face_annulus']['value'] + 0.16
    elif kind == 'governing_changed':
        ty['governing'] = dict(ty['governing'], term_id='H11-FACE-gland_compression_min')
    elif kind == 'pass_with_failing_predicate':
        h.update(physical_pass=True, study_status='PASS', gate_raised=False, gate_ids=[])
        ty['physical_pass'] = True
    else:
        raise StudyError('unknown H11 tamper %s' % kind)
    return bool(h11_violations(cx, mut)) and not h11_violations(cx, res)


def h14_tamper(cx, res, lead, kind):
    """R4-6 (validator): a typed R1-H14 record tampered so that the block plan-AND-Z screen is presented as contract text, or the
    governing term / margin is taken from it, or a degree term enters an mm minimum, or the contracted land 2(v) failure is hidden;
    every variant is rejected by h14_violations; the unmodified result passes."""
    mut = copy.deepcopy(res)
    h = mut['candidate_hard_checks'][lead]['R1-H14']
    ty = h['typed']
    blk = next(t for t in ty['terms'] if t['id'].startswith('CHG_BLOCK vs SCREW') and t['id'].endswith('[plan AND Z]'))
    if kind == 'block_as_contract':
        blk['category'] = 'contract_mandated'
    elif kind == 'block_governs':
        ty['governing'] = dict(ty['governing'], term_id=blk['id'], value=blk['value'])
        h['margin'] = blk['value']
    elif kind == 'deg_in_mm_minimum':
        ty['categories']['contract_mandated']['minimum_by_units']['mm'] = dict(id='land_azimuth_cap', value=-2.0)
    elif kind == 'land_v_hidden':
        for t in ty['terms']:
            if t['id'].startswith('CHG_LAND vs') and t['id'].endswith('[plan AND Z]'):
                t['pass_'] = True
    else:
        raise StudyError('unknown H14 tamper %s' % kind)
    return bool(h14_violations(cx, mut)) and not h14_violations(cx, res)


def block_and_z_never_decides(cx, E):
    """R4-3 (production): with one 2(v) screw raised above the land top but below the block top (plan far from the charger), the land's
    contract Z separation holds, the block is 3-D clear (plan), the conservative block-AND-Z screen fails - and the literal charger
    closure still holds; with the screw back at Z = 0 the contracted land clause fails the closure."""
    n0 = next(n for n in E['chg']['nbrs'] if n['kind'] == 'caseback screw')
    rl = E['sweep']['chg_r_lim_required'] + 0.05
    t_top = E['chg']['land_top_mm']
    mid = dict(n0, z_lo_adv=t_top + 0.1, z_hi_adv=t_top + 1.0)
    a = chg_point_eval(cx, E['sweep']['pose_ctx'], rl, t_top, [mid])
    b = chg_point_eval(cx, E['sweep']['pose_ctx'], rl, t_top, [n0])
    return a['z'] and not a['block_and_z'] and a['neighbours'] and a['literal'] and not b['z'] and not b['literal']


def block_route_3d_not_collision(cx, E):
    """R4-7 (production anchor): at the reported pose the block has a zero Z gap and a positive plan gap to CHG_ROUTE / CHG_LINK: the
    common 3-D predicate holds (not a collision), only the conservative block-AND-Z screen fails; R1-H01 stays an allocation fit."""
    p = E['chg']['pose']
    rows = [r for r in E['chg']['neighbours']['rows'] if r['a'] == 'CHG_BLOCK' and r['b'] in ('CHG_ROUTE', 'CHG_LINK')]
    d3 = [r for r in rows if r['category'] == 'physical_required_elsewhere']
    dz = [r for r in rows if r['category'] == 'conservative_model_diagnostic']
    return len(d3) == 2 and len(dz) == 2 and all(r['clear'] and r['plan_gap_mm'] > 1.0 and abs(r['z_gap_mm']) <= EPS for r in d3) \
        and not any(r['clear'] for r in dz) and p['predicates']['block_routes_clear_3d'] and not p['predicates']['block_routes_clear_in_z']


def land_unsat_closed_form(cx):
    """R4-4 (production rule): land [0, h] against an item [0, H] gives Z_gap = -min(h, H) <= 0 and is reported unsatisfiable for every
    tested h / H; an item raised above the land (z_lo > h) is satisfiable (positive control); a non-shared-datum item has no bound."""
    ok = True
    for h in (0.5, 1.0, 1.62, 2.5):
        for H in (0.3, 1.62, 2.95, 8.35):
            r = land_v_z_unsatisfiability(h, [dict(id='X', kind='caseback screw', z_lo_adv=0.0, z_hi_adv=H)])
            x = r['items'][0]
            ok = ok and r['unsatisfiable'] and abs(x['z_gap_mm'] + min(h, H)) <= 1e-12 and abs(x['bound_mm'] + min(h, H)) <= 1e-12
    r = land_v_z_unsatisfiability(1.62, [dict(id='Y', kind='support pad', z_lo_adv=1.7, z_hi_adv=3.0)])
    return ok and not r['unsatisfiable'] and r['items'][0]['bound_mm'] is None and r['items'][0]['z_gap_mm'] > 0


def charger_scope_tamper(res):
    """R4-5 (validator): a Q-R1-CHARGER wording that states the block / strict-wedge rule as settled, or drops a sub-question, and a
    contract quote that is not verbatim in its brief, are rejected; the reported question passes."""
    a = copy.deepcopy(res)
    q = next(x for x in a['owner_questions'] if x['id'] == 'Q-R1-CHARGER')
    q['question'] = q['question'].replace('does not assume', 'assumes').replace('conductive charger block', 'block')
    b = copy.deepcopy(res)
    next(x for x in b['owner_questions'] if x['id'] == 'Q-R1-CHARGER')['contract_scope']['subquestions'].pop()
    bad_q = dict(CHG_CONTRACT_QUOTES[2], text=CHG_CONTRACT_QUOTES[2]['text'].replace('the land', 'land and block').replace('(v) clears', '(v) land and block clear'))
    CHG_CONTRACT_QUOTES.append(bad_q)
    try:
        c = bool(charger_contract_violations(res))
    finally:
        CHG_CONTRACT_QUOTES.pop()
    return bool(charger_contract_violations(a)) and bool(charger_contract_violations(b)) and c and not charger_contract_violations(res)


def lra_fallback_binding_case(cx, E, res, lead, kind):
    """R3-4 on the production fallback (R4-1 API): 'plate' - the fallback evaluates only the claimed (t_in, t_out) plate while an
    unrestricted plate search would credit a different plate, and a fit whose evaluated plate is substituted is rejected by the
    validator; 'material' - a claim whose material differs from the plate under its pocket is refused by the fallback (STOP) and a fit
    record with a substituted evaluated material is rejected by the validator."""
    fx = lra_fixture(cx, E, res, lead)
    rec, sctx, plate = fx['rec'], fx['sctx'], fx['plate']
    fit = fx['fit']
    if kind == 'plate':
        ok1 = rec['structural']['pairs_evaluated'] == [[plate[0], plate[1]]] and not lra_binding_problems(rec) and \
            rec['structural']['configs_evaluated'] == sum(1 for c in sctx['configs'] if c['t_in'] == plate[0] and c['t_out'] == plate[1])
        it = pocket_interrupter(fx['body'] + fx['lead'])
        g = fx['strl']['geometry']
        free = struct_exact(cx, fx['cand'], sctx, g, fx['mats_fn'], g['R'], pocket=(max(it['r'][0], g['r_step']), min(it['r'][1], g['R']), plate[3], it),
                            configs=[c for c in sctx['configs'] if c['n'] == 0])
        ok2 = free['config']['t_out'] != plate[1]
        sub = copy.deepcopy(fit)
        sub['evaluated']['plate'].update(t_out_mm=free['config']['t_out'])
        sub['structural']['pairs_evaluated'] = [[free['config']['t_in'], free['config']['t_out']]]
        ok3 = bool(lra_binding_violations(cx, lra_fit_res(res, lead, sub), fx['r1fx'])) and \
            not lra_binding_violations(cx, lra_fit_res(res, lead, fit), fx['r1fx'])
        return ok1 and ok2 and ok3
    other = 'MAT-NF-METAL' if fx['claimed']['plate']['materials'] != ['MAT-NF-METAL'] else 'MAT-CERAMIC'
    forged = copy.deepcopy(fx['claimed'])
    forged['plate']['materials'] = [other]
    try:
        lra_struct_fallback(cx, fx['cand'], sctx, fx['strl'], fx['mats_fn'], forged, dict(body=fx['body'], lead=fx['lead']), plate, fx['lctx'])
        refused = False
    except StudyError:
        refused = True
    sub = copy.deepcopy(fit)
    sub['evaluated']['plate']['materials'] = [other]
    return refused and bool(lra_binding_violations(cx, lra_fit_res(res, lead, sub), fx['r1fx'])) and \
        not lra_binding_violations(cx, lra_fit_res(res, lead, fit), fx['r1fx'])


def forged_isolation_case(res, cid):
    """R3-5: the builder refuses an L-LRA isolation outside the allow-set (production hc) and the validator rejects a forged
    isolation - for R1-H08 (cid) or for every non-LRA check plus an unknown isolation value (cid None)."""
    H = res['hard_checks']
    if cid is not None:
        try:
            hc(cid, True, False, -0.07, 'mm', dict(x=1.0), [], ['FEA-1'], [], {}, lra_isolated=True, required_delta=0.07)
            built = True
        except StudyError:
            built = False
        mut = copy.deepcopy(H)
        mut[cid].update(isolation='L-LRA', study_status='GATED', gate_raised=True, gate_ids=mut[cid]['gate_ids'] or ['FEA-1'])
        return not built and bool(isolation_violations(mut)) and any('hidden' in b for b in state_violations(mut)) and not isolation_violations(H)
    ok = True
    for k in sorted(H):
        if k in ('R1-H05', 'R1-H19'):
            continue
        mut = copy.deepcopy(H)
        mut[k]['isolation'] = 'L-LRA'
        ok = ok and any(k in b and 'forged' in b for b in isolation_violations(mut))
    mut = copy.deepcopy(H)
    mut['R1-H05']['isolation'] = 'L-WIN'
    ok = ok and any('unknown isolation' in b for b in isolation_violations(mut))
    mut = copy.deepcopy(H)
    mut['R1-H05']['governing_terms'] = dict(mut['R1-H05']['governing_terms'], **{'H05-EDGE-XF-J1501': -0.1})
    return ok and any('R1-H05' in b for b in isolation_violations(mut)) and not isolation_violations(H)


def fabricated_threshold_case(cx, cx2, res, lead, cid, value):
    """R3-6: a fabricated numeric threshold is rejected by the independent recomputation; the reported one is not."""
    mut = copy.deepcopy(res)
    mut['candidate_hard_checks'][lead][cid]['threshold_value'] = value
    base = threshold_violations(cx, res, cx2, candidates=[lead])
    return not base and any(cid in b and 'threshold_value' in b for b in threshold_violations(cx, mut, cx2, candidates=[lead]))


def compliance_case(cx, E, res, lead, kind):
    """R3-7 on the production compliance_state: a clean candidate (every lane resolved, every check PASS, no stop, D_complete 50.90,
    verdict R1 RESOLVED) is the positive control; 'architecture' - an ARCHITECTURE_GATED L-LRA (with or without its isolated physical
    failure) is never whole-design compliant nor geometry-closed, and a reported compliance claim for it is rejected by the validator;
    'supplier_owner' - a SUPPLIER_GATED lane is not whole-design compliant (only geometry-closed with supplier gates open) and an
    OWNER_GATED lane is neither."""
    H = res['candidate_hard_checks'][lead]
    clean = {k: dict(h, study_status='PASS', physical_pass=True, gate_raised=False, gate_ids=[]) for k, h in H.items()}
    st0 = [dict(s, raised=False) for s in res['candidate_stops'][lead]]
    E2 = dict(E, classification=dict(E['classification'], D_complete=50.90), protrusions=[], D=50.90)
    allr = {l: 'RESOLVED_GEOMETRICALLY' for l in LANES}
    pos = compliance_state(E2, clean, allr, st0, 'R1 RESOLVED', 0.0)
    if not (pos['whole_design_compliant'] and pos['geometric_candidate']):
        return False
    if kind == 'architecture':
        d = dict(allr, **{'L-LRA': 'ARCHITECTURE_GATED'})
        H2 = dict(clean, **{'R1-H19': dict(clean['R1-H19'], physical_pass=False, study_status='GATED', gate_raised=True, gate_ids=['OD-G4-LRA-ARCH'])})
        s2 = [dict(s, raised=s['id'] == 'R1-S08') for s in st0]
        a = compliance_state(E2, H2, d, s2, 'R1 PARTIAL — LRA ARCHITECTURE GATE', 0.0)
        b = compliance_state(E2, clean, d, st0, 'R1 PARTIAL — LRA ARCHITECTURE GATE', 0.0)
        mut = copy.deepcopy(res)
        c = next(x for x in mut['candidates'] if x['id'] == lead)
        c.update(whole_design_compliant=True)
        return not a['whole_design_compliant'] and not a['geometry_closed_supplier_gates_open'] and a['geometric_candidate'] \
            and a['owner_decision_candidate'] and not b['whole_design_compliant'] and not b['geometry_closed_supplier_gates_open'] \
            and bool(compliance_violations(cx, mut)) and not compliance_violations(cx, res)
    sup = compliance_state(E2, clean, dict(allr, **{'L-CHG': 'SUPPLIER_GATED'}), st0, VERDICTS[1], 0.0)
    own = compliance_state(E2, clean, dict(allr, **{'L-BTN': 'OWNER_GATED'}), st0, VERDICTS[3], 0.0)
    return not sup['whole_design_compliant'] and sup['geometry_closed_supplier_gates_open'] and not own['whole_design_compliant'] \
        and not own['geometry_closed_supplier_gates_open']


def radial_prereq_not_closure(cx, E, res, lead):
    """R3-1 / R3-8 on the production same-point evaluation: at a caseback limit above the plan-prerequisite threshold, with the exact
    design-point neighbour set, the radial and plan prerequisites pass but the charger is not closed (Z / neighbours fail)."""
    rl = E['sweep']['chg_r_lim_required'] + 0.05
    pe = chg_point_eval(cx, E['sweep']['pose_ctx'], rl, E['chg']['land_top_mm'], E['chg']['nbrs'])
    return pe['radial'] and pe['plan'] and not pe['z'] and not pe['neighbours'] and not pe['literal']


def charger_label_tamper(cx, res, lead):
    """A sweep point whose radial prerequisite passes, relabelled as a charger closure (CHARGER group set from the radial flag), is
    rejected by the validator."""
    mut = copy.deepcopy(res)
    enc = mut['lanes'][lead]['sweep']['encoding']
    gi, ci = enc['groups_order_tw'].index('CHARGER'), enc['charger_flags'].index('radial')
    col_g, col_c = enc['tw_columns'].index('groups'), enc['tw_columns'].index('charger')
    hit = False
    for r in mut['lanes'][lead]['sweep']['rows']:
        for tw in r['tw']:
            if tw[col_c][ci] == '1' and not hit:
                tw[col_g] = tw[col_g][:gi] + '1' + tw[col_g][gi + 1:]
                hit = True
    return hit and bool(charger_category_violations(cx, mut)) and not charger_category_violations(cx, res)


def envelope_tamper(cx, E):
    """A support placed outside its frozen window is outside the sweep envelope (the containment check detects it)."""
    f = next(f for f in E['features'] if f['kind'] == 'case-side support')
    g = dict(f['geom'], az=[(f['geom']['az'][0] + 60.0) % 360.0, (f['geom']['az'][1] + 60.0) % 360.0])
    return envelope_containment_violations(cx, E['cand'], [dict(f, geom=g)])


def charger_sweep_tamper_fresh(cx, in_proc, res, lead):
    """A sweep point's charger categories changed consistently (flags only, groups untouched) are caught only by the fresh same-point
    re-evaluation of the leader's sweep."""
    mut = copy.deepcopy(res)
    enc = mut['lanes'][lead]['sweep']['encoding']
    ci, col_c = enc['charger_flags'].index('radial'), enc['tw_columns'].index('charger')
    tw = mut['lanes'][lead]['sweep']['rows'][0]['tw'][0]
    tw[col_c] = tw[col_c][:ci] + ('0' if tw[col_c][ci] == '1' else '1') + tw[col_c][ci + 1:]
    tw[col_c] = tw[col_c][:enc['charger_flags'].index('plan')] + '0' + tw[col_c][enc['charger_flags'].index('plan') + 1:]
    bad, _ = recompute_diameters(cx.st, in_proc, mut, cx.poses)
    return any('charger categories' in b for b in bad)


def structure_tamper(res, lead, kind):
    mut = copy.deepcopy(res)
    rows = mut['lanes'][lead]['sweep']['rows']
    gi = mut['lanes'][lead]['sweep']['encoding']['groups_order_tw'].index('STRUCTURE')
    if kind == 'flag':
        row = rows[len(rows) // 2]['tw'][0]
        row[1] = row[1][:gi] + '1' + row[1][gi + 1:]
    else:   # the rejected endpoint-OR: every D marked passing from one endpoint, per-point records untouched
        di = mut['lanes'][lead]['sweep']['encoding']['groups_order_D'].index('STRUCTURE')
        for r in rows:
            r['groups'] = r['groups'][:di] + '1' + r['groups'][di + 1:]
        mut['lanes'][lead]['L-RAD']['classification']['groups']['STRUCTURE'].update(always=True, never=False, first_pass_D=rows[0]['D'])
    return bool(structure_point_violations(mut)) and not structure_point_violations(res)


def structure_tamper_fresh(cx, in_proc, res, lead):
    """Flag AND record of one point both changed consistently: only the fresh per-point recomputation can catch it."""
    mut = copy.deepcopy(res)
    enc = mut['lanes'][lead]['sweep']['encoding']
    gi = enc['groups_order_tw'].index('STRUCTURE')
    row = mut['lanes'][lead]['sweep']['rows'][len(mut['lanes'][lead]['sweep']['rows']) // 2]['tw'][0]
    row[1] = row[1][:gi] + '1' + row[1][gi + 1:]
    si = enc['tw_columns'].index('structure')
    row[si][enc['structure_fields'].index('pass_')] = True
    row[si][enc['structure_fields'].index('method')] = 'EXACT_SEARCH'
    bad, _ = recompute_diameters(cx.st, in_proc, mut, cx.poses)
    return any('per-point' in b or 'point groups' in b for b in bad)


def bound_vs_configs(cx, E):
    """Minimum-potential-energy anchor at the design point: every admissible configuration's exact compliance is >= the
    relaxed compliance, and its sampled Screen-B deflection is >= the bound."""
    sw = E['sweep']
    sctx = sw['sctx']
    sg = struct_geometry(cx, E['cand'], sctx, E['row'], E['chg']['r_lim'], pose=E['chg']['pose'])
    R = sg['geo']['R']
    rel = sg['rel']
    regs = [dict(x) for x in rel['regions']] + [dict(rel['outer'], r0=rel['r_rib_out'], r1=R)]
    C_rel, _ = compliance(plate_solve(regs, cx.p, 'loaded_boss', 'ss', 2), cx.p)
    ratio = C_rel / (cx.p * math.pi * R * R)
    lays = {}
    for cfg in sctx['configs']:
        if (cfg['n'], cfg['w']) not in lays:
            lays[(cfg['n'], cfg['w'])] = rib_layout(sg['geo'], cfg['n'], cfg['w'], cx.P['V13_rib_counts']['phase_divisions'])['gap_deg']
        g = dict(sg['geo'], gap_deg=lays[(cfg['n'], cfg['w'])])
        sol = plate_solve(str_regions(g, sg['mats'], cfg, 'B', cx.P['screen_b']['subregions']), cx.p, 'loaded_boss', 'ss', 13)
        C, _ = compliance(sol, cx.p)
        wmax = max(abs(s_['w']) for x in sol for s_ in x['samples'])
        if C < C_rel * (1.0 - 1e-9) or wmax < ratio - 1e-12:
            return False
    return True


def relaxed_mutation_caught(cx, E):
    sctx = E['sweep']['sctx']
    sg = struct_geometry(cx, E['cand'], sctx, E['row'], E['chg']['r_lim'], pose=E['chg']['pose'])
    weak = copy.deepcopy(sg['rel'])
    for rg in weak['regions']:
        if rg['kind'] == 'relaxed outer':
            rg['Dr'] = rg['Dt'] = 0.5 * rg['Dt']
            rg['D1'] = rg['nu'] * rg['Dt']
    cfg = max(sctx['configs'], key=lambda c: (c['t_out'], c['n'], c['h'], c['w']))
    lay = rib_layout(sg['geo'], cfg['n'], cfg['w'], cx.P['V13_rib_counts']['phase_divisions'])
    regs = str_regions(dict(sg['geo'], gap_deg=lay['gap_deg']), sg['mats'], cfg, 'B', cx.P['screen_b']['subregions'])
    return bool(loewner_violations(weak, regs, sg['geo']['R'])) and not loewner_violations(sg['rel'], regs, sg['geo']['R'])


def endpoint_or_classify(cx, E):
    """Inject a structural pass at ONE point (smallest primary D, one wall) into a copy of the production sweep: classify must
    keep it at that point only (no propagation to any other D)."""
    sw = copy.deepcopy(dict((k, v) for k, v in E['sweep'].items() if k != 'classification'))
    r0 = next(r for r in sw['rows'] if r['primary'])
    r0['tw_rows'][0]['groups']['STRUCTURE'] = True
    r0['any_tw']['STRUCTURE'] = True
    g = classify(cx, E['cand'], sw)['groups']['STRUCTURE']
    others = [r for r in sw['rows'] if r is not r0 and r['any_tw']['STRUCTURE']]
    return g['first_pass_D'] == r0['D'] and g['last_pass_D'] == r0['D'] and not g['always'] and not others


def charger_plan_overlap_caught(cx, cand):
    """The first-pass R1 pose (ori 0, r 20.65, az 90, land 1.0) overlaps CHG_ROUTE in plan with ~0.63 mm Z separation: the
    rejected Z-or-plan predicate accepts it, the literal predicate rejects it."""
    p = chg_pose(cx, cand, 0, 20.65, 90.0, 1.0)
    land = feature('L', 'L-CHG', 'land', False, False, dict(type='poly', pts=p['land_poly']), ['REAR'],
                   zfeat(0.0, max(grid(cx.P['V12_caseback_thickness']['t_out'])) + cx.ce[cand['id']].sp.pc_cb['thickness_mm']), 'charger land')
    or_ok, info = clear(land, conductor(cx, 'CHG_ROUTE'), 0.0, 0.0)
    return or_ok and info['z_gap_mm'] > 0.5 and not p['predicates']['routes_clear_in_plan'] and not p['pass_']


def charger_report_tamper(cx, res, lead):
    """The first-pass R1 pose (overlapping CHG_ROUTE in plan) reported as a plan-clear, closed charger is rejected (fresh exact
    route overlap; closure without its categories)."""
    mut = copy.deepcopy(res)
    cand = next(c for c in cx.cands if c['id'] == lead)
    p = chg_pose(cx, cand, 0, 20.65, 90.0, 1.0)
    sel = mut['lanes'][lead]['L-CHG']['selected']
    sel['pose'].update(land_poly=p['land_poly'], block_poly=p['block_poly'], predicates=dict(p['predicates'], routes_clear_in_plan=True))
    sel['categories'] = dict(sel['categories'], plan=True)
    bad = charger_category_violations(cx, mut)
    return any('collides in plan' in b for b in bad) and not charger_category_violations(cx, res)


def conductor_view_tamper(cx, E):
    F = [dict(f) for f in E['features']]
    for f in F:
        if f['id'] == 'CHG_LINK':
            f.update(zfeat(0.0, f['z_hi_nom']))
    return bool(feature_view_violations(F, E['module'])) and not feature_view_violations(E['features'], E['module'])


def lra_bound_anchor(E):
    tab = E['lra']['material_table']
    exp = {'MAT-CERAMIC': (1.110, 1.030), 'MAT-NF-METAL': (1.210, 1.130), 'MAT-GF-POLY': (0.850, 0.800)}
    ok = all(abs(tab[m]['continuous_upper_bound_mm'] - c) < 5e-4 and abs(tab[m]['authored_grid_maximum_mm'] - g) < 5e-4 for m, (c, g) in exp.items())
    ev = E['lra']['envelopes']
    return ok and abs(ev['selected_design_point']['value_mm'] - 0.930) < 5e-4 and not ev['continuous_upper_bound']['searched'] \
        and ev['authored_grid_maximum']['searched'] and ev['continuous_upper_bound']['value_mm'] > ev['authored_grid_maximum']['value_mm'] \
        >= ev['selected_design_point']['value_mm']


def lra_label_tamper(res, lead):
    a = copy.deepcopy(res)
    e = a['lanes'][lead]['L-LRA']['envelopes']
    e['authored_grid_maximum']['value_mm'] = e['continuous_upper_bound']['value_mm']
    b = copy.deepcopy(res)
    b['lanes'][lead]['L-LRA']['envelopes']['continuous_upper_bound']['searched'] = True
    return bool(lra_envelope_violations(a)) and bool(lra_envelope_violations(b)) and not lra_envelope_violations(res)


def supplied_record(**kw):
    rec = dict(id='SR2-TEST', shape='coin', diameter_mm=dict(min=3.9, nom=4.0, max=4.0), height_mm=dict(min=0.5, nom=0.55, max=0.6),
               lead_exit_envelope_mm=dict(length_mm=dict(min=0.0, nom=0.0, max=0.0), width_mm=dict(min=0.0, nom=0.0, max=0.0),
                                          height_mm=dict(min=0.0, nom=0.0, max=0.0), exit='radial_in'),
               primary_document='design/mechanical/G4_BRIEF.md', provenance=dict(page='1', table_or_figure='T-selftest'))
    rec.update(kw)
    return rec


def lra_struct_gate(cx, cand, E):
    """A supplied class small enough to pass plan and Z must still not fit: every pocketed combination fails the structural
    re-screen (design-point compliance bound)."""
    cx2 = copy.copy(cx)
    cx2.I = dict(cx.I, lra_supplied=[supplied_record()])
    L = lane_lra(cx2, cand, E['row'], E['dp'], E['chg']['r_lim'], E['chg'], E['strl'], E['structure_design_point'], E['sweep']['sctx'])
    row = next(c for c in L['classes'] if c['id'] == 'SR2-TEST')
    return row['plan_feasible_poses'] > 0 and row['z_feasible_poses'] > 0 and not row['fits'] and row['structurally_feasible_fits'] == 0 \
        and not L['physical_pass'] and L['od_g4_lra_arch_triggered'] and L['structural_rescreen']['combinations'] > 0


def lra_fit_tamper(res, lead):
    mut = copy.deepcopy(res)
    mut['lanes'][lead]['L-LRA']['fitting_classes'] = ['LRA-LIN-RECT']
    return bool(lra_envelope_violations(mut)) and not lra_envelope_violations(res)


def lra_lead_exit_collision(cx, cand, E):
    """Same body, lead / exit included or not: a pose that is plan-feasible without the lead becomes infeasible when its
    declared lead / exit envelope reaches an exclusion; poses are only lost, never gained."""
    rl = E['chg']['r_lim']
    cls0 = supplied_record()
    cls1 = supplied_record(lead_exit_envelope_mm=dict(length_mm=dict(min=6.0, nom=6.0, max=6.0), width_mm=dict(min=1.0, nom=1.0, max=1.0),
                                                      height_mm=dict(min=0.3, nom=0.3, max=0.3), exit='radial_in'))
    st = cx.st
    ce = cx.ce[cand['id']]
    ex = lra_exclusion_set(cx, cand, E['dp'], E['chg'], E['strl'])
    ok = lambda p: not p['viol'] and p['rmax'] + cx.poses['c_plan'] <= rl + EPS and not g4.local_pose_violations(st, ce, E['dp'], p['env'], ex)
    P0 = {(p['az'], p['r']): ok(p) for p in lra_supplied_poses(cx, cls0, rl)}
    P1 = {(p['az'], p['r']): ok(p) for p in lra_supplied_poses(cx, cls1, rl)}
    lost = [k for k in P0 if P0[k] and not P1[k]]
    gained = [k for k in P0 if P1[k] and not P0[k]]
    v = validate_lra_supplied(cx, [cls1])[0]
    return bool(lost) and not gained and v['accepted'] and lra_class_height(cls1) == 0.6


def gate_threshold_tamper(res):
    H = copy.deepcopy(res['hard_checks'])
    gid = next(k for k, h in sorted(H.items()) if h['study_status'] == 'GATED' and k in NUMERIC_CHECKS)
    H[gid].update(threshold_value=None, required_delta=None, supplier_zero_margin=[dict(term='x', value=None)])
    return any('numeric threshold' in b for b in state_violations(H)) and not state_violations(res['hard_checks'])


def hc_state_tamper(res, kind):
    H = copy.deepcopy(res['hard_checks'])
    if kind == 'pass_gate':
        h = next(h for k, h in sorted(H.items()) if h['study_status'] == 'PASS')
        h.update(gate_raised=True, gate_ids=['SR-TEST'])
    elif kind == 'hide_gated':
        h = next(h for k, h in sorted(H.items()) if h['study_status'] == 'FAIL')
        h.update(study_status='GATED', gate_raised=True, gate_ids=h['gate_ids'] or ['SR-TEST'])
    else:
        h = next(h for k, h in sorted(H.items()) if h['study_status'] == 'FAIL')
        h.update(study_status='PASS', gate_raised=False, gate_ids=[])
    return bool(state_violations(H)) and not state_violations(res['hard_checks'])


def a11_dependency_production(cx, E):
    """lane_asm on the production path: with no feasible main seal A11 is FAILED and L-ASM is owner-gated; with a feasible seal
    (and every other dependency resolved) the same sequence closes the product."""
    deps = dict(seal=E['seal'], chg=E['chg'], strl=E['strl'], win=E['win'])
    a = lane_asm(cx, E['cand'], E['row'], E['btn'], E['lra'], E['closure'], deps=deps)
    a11 = next(d for d in a['dependencies'] if d['step'] == 'A11' and 'S-CB-MAIN' in d['requires'])
    ok_dep = dict(seal=dict(E['seal'], physical_pass=True, closed_topology='face', feasible_topologies=['face']), chg=dict(E['chg'], pass_=True),
                  strl=dict(E['strl'], physical_pass=True), win=dict(E['win'], physical_pass=True))
    btn_ok = dict(E['btn'], closed=True, disposition='SUPPLIER_GATED')
    lra_ok = dict(E['lra'], physical_pass=True, fitting_classes=['X'])
    b = lane_asm(cx, E['cand'], E['row'], btn_ok, lra_ok, E['closure'], deps=ok_dep)
    return a11['state'] == 'FAILED' and not a['product_closure_executable'] and a['disposition'] == 'OWNER_GATED' \
        and a['sequence_executable'] and b['product_closure_executable'] == b['sequence_executable']


def asm_tamper(res, lead):
    mut = copy.deepcopy(res)
    A = mut['lanes'][lead]['L-ASM']
    A.update(product_closure_executable=True, disposition='SUPPLIER_GATED')
    return bool(asm_dependency_violations(mut)) and not asm_dependency_violations(res)


def selection_tamper(res, lead, kind):
    mut = copy.deepcopy(res)
    c = next(x for x in mut['candidates'] if x['id'] == lead)
    if kind == 'above':
        c.update(D_complete=51.8, whole_design_compliant=True, geometric_candidate=True)
        mut['ranking'].update(selection_permitted=True, selected=lead, selected_D=51.8, selection_basis='whole-design compliant')
    else:
        c.update(whole_design_compliant=True, D_complete=None)
    return bool(whole_design_violations(mut)) and not whole_design_violations(res)


def whole_design_production(E, res, lead):
    """compliance_state() on the production path: the leader's radial core closes but the candidate is not compliant; a fabricated
    complete closure above 51.00 mm is still not compliant (nor geometric)."""
    c = next(x for x in res['candidates'] if x['id'] == lead)
    H = res['candidate_hard_checks'][lead]
    clean = {k: dict(h, study_status='PASS', physical_pass=True, gate_raised=False, gate_ids=[]) for k, h in H.items()}
    st0 = [dict(s, raised=False) for s in res['candidate_stops'][lead]]
    E2 = dict(E, classification=dict(E['classification'], D_complete=51.8), protrusions=[])
    a = compliance_state(E, H, c['dispositions'], res['candidate_stops'][lead], c['verdict_if_selected'], 0.0)
    b = compliance_state(E2, clean, {l: 'RESOLVED_GEOMETRICALLY' for l in LANES}, st0, 'R1 RESOLVED', 0.0)
    return not a['whole_design_compliant'] and not b['whole_design_compliant'] and not b['geometric_candidate'] \
        and (c['D_radial_core'] is None or not c['whole_design_compliant'])


def v03_exhaustive(cx, Es):
    """V03 reduction vs the exhaustive contracted grid with production predicates at the design points and at points where
    arcs run through the rear face: identical own-feasible interval and the selection rule reproduced."""
    pts = [(c, Es[c]['D'], Es[c]['tw']) for c in sorted(Es)] + [('G4-B', 50.05, 1.3), ('G4-A', 50.85, 1.6), ('G4-B', 48.0, 0.8)]
    for cid, D, tw in pts:
        cand = next(c for c in cx.cands if c['id'] == cid)
        car = Es[cid]['sweep']['carrier']
        for a in arc_defs(cx, cand):
            got = arc_search(cx, cand, D, tw, a, D / 2.0 - tw, car['rcin'], car['tcw'])
            G = arc_grid(cx, a, tw)
            rows = [arc_eval(cx, cand, D, a, g, D / 2.0 - tw, car['rcin'], car['tcw']) for g in G]
            feas = [g for g, r in zip(G, rows) if r['own_pass']]
            if feas != got['search']['admissible_mm'] or bool(feas) != got['search']['feasible']:
                return False
            if feas and got['z_extent'] == 'THROUGH_REAR_FACE' and got['t_arc_mm'] != max(feas):
                return False
            if feas and got['z_extent'] == 'MAIN_BATTERY':
                best = max(feas, key=lambda g: (round(min(rows[G.index(g)]['wall_margin_mm'], min(rows[G.index(g)]['own_decreasing_mm'].values())), 9), -g))
                if abs(best - got['t_arc_mm']) > 1e-9:
                    return False
    return True


def v03_tamper(cx, res, lead):
    mut = copy.deepcopy(res)
    a = mut['lanes'][lead]['L-RAD']['arcs'][0]
    a['t_arc_mm'] = round(a['search']['grid_mm'][0] - 0.02, 9)
    b = copy.deepcopy(res)
    ab = b['lanes'][lead]['L-RAD']['arcs'][0]
    if ab['search']['feasible'] and ab['search']['t_hi_mm'] + 0.02 <= ab['search']['grid_mm'][1] + EPS:
        ab['search']['t_hi_mm'] = round(ab['search']['t_hi_mm'] + 0.02, 9)
        ok_b = bool(arc_search_violations(cx, b))
    else:
        ok_b = True
    return bool(arc_search_violations(cx, mut)) and ok_b and not arc_search_violations(cx, res)


def fresh_h02_fails(cx, cand, D):
    sp = g4.Specs(cx.st, cand)
    return g4.run_check(sp.od(dict(D=D)), False) < 0


def reported_d_mismatch(cx, in_proc, res, key, value):
    mut = copy.deepcopy(res)
    for c in mut['candidates']:
        if c['id'] == mut['ranking']['leader']:
            c[key] = value
    bad, _ = recompute_diameters(cx.st, in_proc, mut, cx.poses)
    return bad


def thin_caseback_fails(cx, cand, t):
    m = str_mats(cx, cand)[1]['outer']
    return t - m['tol_t'] - m['t_min'] < 0


def rib_mutation_caught(cx, res, lead, key, value):
    mut = copy.deepcopy(res)
    S = mut['lanes'][lead]['L-STR']
    tgt = S.get('best_ribbed')
    if tgt is None:
        tgt = dict(config=dict(S['selected'], n=12, w=0.8, h=0.8), rib_layout=dict(gap_deg=30.0), screen_B=S['screen_B'])
        S['best_ribbed'] = tgt
    tgt['config'][key] = value
    return bool(recompute_structure(cx, mut))


def partition_valid(cx, sp, dp, radius=None):
    """Pressure partition over the bearing disc (g4 post_load semantics): domains must sum to pi R_bear^2."""
    R_bear = dp['D'] / 2.0 - dp['tw'] + sp.pc_env['radius_mm']
    post = g4.post_load(cx.st, sp, dp)
    doms = copy.deepcopy(post['domains'])
    if radius is not None:
        doms[-1]['area_mm2'] = math.pi * radius ** 2 - sum(d['area_mm2'] for d in doms[:-1])
    return g4.pressure_domains_valid(doms, math.pi * R_bear ** 2)


def forbidden_mutation(cx, E, target, branch=None):
    st, zm = cx.st, cx.zm
    F = [dict(f) for f in E['features']]
    if target == 'LOWER_WEB':
        F.append(feature('MUT_RIB', 'L-STR', 'mut', False, False, g4.sector(10.0, 12.0, 18.0, 22.0), ['REAR'],
                         zfeat(1.0, zm['z_lower_web_underside_nom'] + 0.1), 'caseback rib'))
        b = branch or 'BATTERY'
    elif target == 'S14_OUTLINE':
        F.append(feature('MUT_PLATE', 'L-STR', 'mut', False, False, dict(type='circles', circles=[[100.0, 100.0, 14.0]]), ['REAR'],
                         zfeat(0.0, zm['z_rear_skin_nom']), 'caseback rib'))
        b = 'REAR_PCB'
    else:
        land = st.s14geo['supports'][0]
        F.append(feature('MUT_POST', 'L-STR', 'mut', False, False, dict(type='circles', circles=[[land['centre'][0], land['centre'][1], 0.3]]),
                         ['REAR'], zfeat(0.0, zm['z_rear_skin_nom']), 'caseback rib'))
        b = 'G3_SUPPORT_LANDS'
    clear_fp = dict(rear_pcb_and_g3_support_lands=dict(margin_mm=1.0, contact=False),
                    battery_and_lower_web=dict(loaded_margin_mm=1.0, lower_web_clearance_mm=1.0, contact=False))
    strl0 = dict(E['strl'], forbidden_paths=clear_fp, screen_B=dict(E['strl']['screen_B'], w_rib_band_mm=0.0))
    base = forbidden_loads(cx, E['cand'], strl0, E['features'], E['module'], E['path'])
    mut = forbidden_loads(cx, E['cand'], strl0, F, E['module'], E['path'])
    return mut['branches'][b]['contact'] and mut['branches'][b]['load_N'] is None and not base['branches'][b]['contact']


def charger_size_mutation(cx, cand, r1in, E):
    """The authored 4 x 5 block replaced by 40 x 50: the production pose at the plan-prerequisite location loses its radial / plan
    prerequisites (the authored block meets them there)."""
    mut = copy.deepcopy(r1in)
    mut['parameters']['V19_charger_pose']['block_size_mm'] = [40.0, 50.0]
    q = E['chg_literal']['plan_prerequisite']['pose']
    p = chg_pose(cx, cand, q['orientation'], q['r_centre'], q['az_centre'], q['land'], mut)
    p0 = chg_pose(cx, cand, q['orientation'], q['r_centre'], q['az_centre'], q['land'])
    return p['block_mm'] == [40.0, 50.0] and not p['prereq_pass'] and p0['prereq_pass']


def rim_mutation(cx, cand):
    T = btn_terms(cx, cand, 'SW1')
    a = btn_section(T, 50.9, 'T2-R', 0.9, 2.0, 'I-SUM')
    b = btn_section(dict(T, rim=2.0), 50.9, 'T2-R', 0.9, 2.0, 'I-SUM')
    return abs((a['margins']['bore_stack'] - b['margins']['bore_stack']) - 1.0) < 1e-9 and not b['pass_']


def feature_flag_mutation(st, E, fid, flag, which):
    F = [dict(f, **{flag: True}) if f['id'] == fid else f for f in E['features']]
    r = g4.rf_mag_check(st, F)
    base = g4.rf_mag_check(st, E['features'])
    return not r[which + '_pass'] and base[which + '_pass']


def t1_selection_caught(cx, res, lead):
    mut = copy.deepcopy(res)
    mut['lanes'][lead]['L-BTN']['selected_topology']['SW1'] = 'T1'
    return any('T1 selected' in f for f in quick_lane_checks(mut))


def quick_lane_checks(res):
    out = []
    for cid, L in res['lanes'].items():
        if any(v == 'T1' for v in L['L-BTN']['selected_topology'].values() if v):
            out.append('%s: T1 selected' % cid)
        if L['L-BTN']['disposition'].startswith('RESOLVED_UNDER_I-MAX_ONLY') and L['L-BTN']['closed']:
            out.append('%s: I-MAX-only button closure counted as closed' % cid)
        if set(L['L-RAD']['h05_geom']['terms']) & set(L['L-RAD']['h05_lra_coupled']) or any('XL' in t for t in L['L-RAD']['h05_geom']['terms']):
            out.append('%s: H05-GEOM blended with H05-LRA-COUPLED' % cid)
    return out


def switch_moved_caught(st):
    s2 = copy.copy(st)
    s2.P = copy.deepcopy(st.P)
    s2.P['buttons']['windows_deg']['SW1'] = [293.5, 308.5]
    return frozen_switches_ok(st) and not frozen_switches_ok(s2)


def missing_vent_caught(cx, cand, E):
    st = cx.st
    sp = cx.ce[cand['id']].sp
    b = copy.deepcopy(E['layout']['buttons'])
    for x in b:
        if x['id'] == 'SW4':
            x['centre'], x['boss_half_deg'] = 45.0, 30.0
    v = g4.vent_layout(st, sp, E['dp'], b)
    inv = copy.deepcopy(E['inventory'])
    if v is None:
        inv['components']['MIDCASE'] = [a for a in inv['components']['MIDCASE'] if a['aperture'] != 'VENT_PORT']
        inv['seals'] = [s for s in inv['seals'] if s['id'] != 'S-VENT']
    complete = any(s['id'] == 'S-VENT' for s in inv['seals'])
    return v is None and not complete


def drop_seal(inv, sid):
    inv = copy.deepcopy(inv)
    inv['seals'] = [s for s in inv['seals'] if s['id'] != sid]
    return inv


def dup_seal(inv, sid):
    inv = copy.deepcopy(inv)
    inv['seals'].append(dict(next(s for s in inv['seals'] if s['id'] == sid)))
    return inv


def flange_mutation(cx, cand, E):
    cx2 = copy.copy(cx)
    cx2.P = copy.deepcopy(cx.P)
    cx2.P['V12b_flange_thickness'] = dict(start=0.5, stop=0.5, step=0.1)
    ms = main_seal(cx2, cand, E['row'])
    return all(o['margins']['flange_groove_residual'] < 0 for o in ms['rows'] if o['topology'] == 'face') and \
        not ms['topologies']['face']['predicate_feasible_rows']['flange_groove_residual']


def assembly_mutation(cx, E, kind):
    steps = copy.deepcopy(asm_sequence(cx, E['btn']))
    if kind == 'order':
        i, j = [s['id'] for s in steps].index('A7'), [s['id'] for s in steps].index('A8')
        steps[i], steps[j] = steps[j], steps[i]
        r = lane_asm(cx, E['cand'], E['row'], E['btn'], E['lra'], E['closure'], steps)
        return not r['executable'] and not all(x['pass_'] for x in r['order_check'])
    if kind == 'direction':
        for s in steps:
            if s['id'] == 'A6':
                s['direction'] = '-Z from front'
    else:
        steps = [s for s in steps if s['id'] != kind.split(':')[1]]
    r = lane_asm(cx, E['cand'], E['row'], E['btn'], E['lra'], E['closure'], steps)
    return not r['identity']['pass_'] and not r['executable']


def lra_supplied_mutation(cx, cand, E, kind):
    thr = E['lra']['envelopes']['authored_grid_maximum']['value_mm']
    rec = dict(id='MUT-LRA', shape='coin', diameter_mm=dict(min=5.0, nom=5.5, max=6.0), height_mm=dict(min=0.8, nom=0.9, max=1.0),
               lead_exit_envelope_mm=dict(length=2.0), provenance=dict(page='1', table_or_figure='T1'))
    if kind == 'threshold':
        rec = supplied_record(id='MUT-LRA', height_mm=dict(min=thr - 0.1, nom=thr - 0.05, max=thr))
    v = validate_lra_supplied(cx, [rec], (thr,))[0]
    cx2 = copy.copy(cx)
    cx2.I = dict(cx.I, lra_supplied=[rec])
    L = lane_lra(cx2, cand, E['row'], E['dp'], E['chg']['r_lim'], E['chg'], E['strl'], E['structure_design_point'], E['sweep']['sctx'])
    return not v['accepted'] and L['od_g4_lra_arch_triggered'] and 'MUT-LRA' not in [c['id'] for c in L['classes']]


def pocket_residual_check(cx, cand, E, depth, residual=None):
    m = str_mats(cx, cand)[1]['outer']
    t_res = (E['strl']['selected']['t_out'] - depth) if residual is None else residual
    return t_res - m['tol_t'] - m['t_min']


def deepest_bad_pocket(cx, cand, E):
    m = str_mats(cx, cand)[1]['outer']
    return round(E['strl']['selected']['t_out'] - m['t_min'] - m['tol_t'] + 0.05, 6)


def lra_g2_mutation(cx, cand, E):
    st = cx.st
    ex = [(n, g) for n, g in g4.lra_local_exclusions(st, cx.ce[cand['id']], E['dp']) if n not in ('CHG_CONTACT_BLOCK', 'CHG_4X5_WITH_LAND')]
    ex.append(('CHG_CONTACT_BLOCK', dict(type='poly', pts=E['chg']['pose']['block_poly'])))
    for k in sorted(st.g2res):
        if 'REAR' in st.g2res[k]['z_levels']:
            ex.append((k, st.g2res[k]['geometry']))
    v = g4.local_pose_violations(st, cx.ce[cand['id']], E['dp'], [(g4.xy(18.5, 200.0), 0.4)], ex)
    return 'G2-J202-WEST-F.Cu-2' in v


def g2g3_mutation(st, r1in):
    a = copy.deepcopy(st.A)
    a['g2']['reservations'][0]['geometry'] = copy.deepcopy(a['g2']['reservations'][0]['geometry'])
    g = a['g2']['reservations'][0]['geometry']
    if g['type'] == 'sector':
        g['r'] = [g['r'][0] + 0.1, g['r'][1]]
    else:
        g['rect'] = [g['rect'][0] + 0.1] + list(g['rect'][1:])
    proj = {'reservations': a['reservations'], 'rear_module': a['rear_module'], 'g2.reservations': a['g2']['reservations'],
            'edge_crossings': a['edge_crossings']}
    base = {'reservations': st.A['reservations'], 'rear_module': st.A['rear_module'], 'g2.reservations': st.A['g2']['reservations'],
            'edge_crossings': st.A['edge_crossings']}
    return g4.chash(base) == r1in['architecture_projection']['sha256'] and g4.chash(proj) != r1in['architecture_projection']['sha256']


def mirrored_caught(st):
    mir = copy.deepcopy(st.s14['supports'][0]['polygon'])
    mir['assembly_mm'] = [[100 + p[0], 100 + p[1]] for p in mir['rear_mm']]
    return not g4.frame_ok(mir) and g4.frame_ok(st.s14['supports'][0]['polygon'])


def historical_mutation(in_proc):
    res = copy.deepcopy(in_proc['res'])
    res['verdict'] = res['verdict'] + ' (mutated)'
    files = g4.outputs(res, in_proc['st'])
    return (GEN / 'g4_case_sealing.json').read_bytes() != files['g4_case_sealing.json'].encode('utf-8') and \
        (GEN / 'g4_case_sealing.json').read_bytes() == in_proc['files']['g4_case_sealing.json'].encode('utf-8')


def state_mutation(res, kind):
    H = copy.deepcopy(res['hard_checks'])
    h = H['R1-H09']
    if kind == 'neg':
        h.update(physical_pass=True, study_status='PASS', margin=-1.0, gate_raised=False, gate_ids=[])
        return any('negative margin' in b for b in state_violations(H)) and not state_violations(res['hard_checks'])
    h.update(study_status='GATED', gate_raised=False, gate_ids=[])
    return any('GATED without gate ids' in b for b in state_violations(H)) and not state_violations(res['hard_checks'])


def hc_raises():
    try:
        hc('R1-H09', True, True, -1.0, 'MPa', {}, [], [], [], {})
        return False
    except StudyError:
        return True


def verdict_mutation():
    disp = {l: 'SUPPLIER_GATED' for l in LANES}
    stops = [dict(id=i, raised=False, fatal=i in FATAL_STOPS) for i in ['R1-S%02d' % k for k in range(1, 14)]]
    ok = verdict_of(disp, stops) == 'R1 RESOLVED — SUPPLIER/RF/QUALIFICATION GATES OPEN'
    d2 = dict(disp, **{'L-STR': 'OWNER_GATED'})
    s2 = [dict(s, raised=s['id'] in ('R1-S07', 'R1-S13')) for s in stops]
    d3 = dict(disp, **{'L-LRA': 'ARCHITECTURE_GATED'})
    s3 = [dict(s, raised=s['id'] == 'R1-S08') for s in stops]
    return ok and verdict_of(d2, s2) == 'R1 OWNER DECISION REQUIRED' and verdict_of(d3, s3) == 'R1 PARTIAL — LRA ARCHITECTURE GATE' \
        and verdict_of(d2, [dict(s, raised=s['id'] == 'R1-S12') for s in stops]) == 'R1 FAIL'


def imax_closed_caught(cx, res, lead):
    mut = copy.deepcopy(res)
    mut['lanes'][lead]['L-BTN']['disposition'] = 'RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED'
    mut['lanes'][lead]['L-BTN']['closed'] = True
    return any('I-MAX-only' in f for f in quick_lane_checks(mut))


def window_mutation(st, kind):
    s2 = copy.copy(st)
    s2.P = copy.deepcopy(st.P)
    if kind == 'widen':
        s2.P['oring']['windows']['static_face']['compression_min'] = 0.10
    else:
        s2.P['oring']['cs_tolerance_mm'] = dict(s2.P['oring']['cs_tolerance_mm'], min=-0.02, max=0.02)
    g4in = load_json(MECH / 'inputs/g4_case_sealing.json')
    return frozen_seal_windows_ok(st, g4in) and not frozen_seal_windows_ok(s2, g4in)


def legacy_bore_mutation(cx, res, lead):
    mut = copy.deepcopy(res)
    L = mut['lanes'][lead]['L-BTN']
    L['switches']['SW1']['legacy_G4_bore_margin_mm'] += 1.5
    return bool(legacy_column_violations(cx, mut)) and not legacy_column_violations(cx, res)


def conductive_land_caught(cx, cand):
    c2 = copy.deepcopy(cand)
    c2['caseback'] = dict(c2['caseback'], material='MAT-NF-METAL', process='PC-METAL-MACH', split=False)
    cx2 = copy.copy(cx)
    cx2.ce = dict(cx.ce)
    ce2 = copy.copy(cx.ce[cand['id']])
    ce2.sp = g4.Specs(cx.st, c2)
    cx2.ce[c2['id']] = ce2
    p = chg_pose(cx2, c2, 0, 20.6, 90.0, 1.0)
    return not p['predicates']['land_non_conductive'] and not p['pass_']


def overshoot_mutation(cx, cand):
    p = chg_pose(cx, cand, 0, 20.6, 85.0, 1.0)
    return p['margins']['land_overshoot_cap'] < 0 and not p['pass_'] and chg_pose(cx, cand, 0, 20.6, 90.0, 1.0)['margins']['land_overshoot_cap'] >= 0


def radiator_mutation(cx, cand, E):
    st = cx.st
    pose = E['chg']['pose']
    x0, y0 = pose['land_poly'][1]
    st2 = copy.copy(st)
    st2.res = dict(st.res)
    st2.res['WIFI_RAD'] = dict(st.res['WIFI_RAD'], geometry=dict(type='rect', rect=[x0 + 0.2, y0 - 1.0, x0 + 4.0, y0 + 1.0]))
    cx2 = copy.copy(cx)
    cx2.st = st2
    p = chg_pose(cx2, cand, pose['orientation'], pose['r_centre'], pose['az_centre'], pose['land'])
    return p['margins']['land_radiators'] < 0 and not p['pass_']


def polymer_wall_mutation(cx):
    candA = next(c for c in cx.cands if c['id'] == 'G4-A')
    a = arc_defs(cx, candA)[0]
    sp = cx.ce['G4-A'].sp
    loc = copy.copy(sp)
    loc.pc_mid, loc.m_mid = a['pc'], a['m']
    return g4.run_check(loc.wall(dict(tw=a['floor_mm'] - 0.02), a['floor_mm'] - 0.02), False) < 0 and \
        abs(g4.run_check(loc.wall(dict(tw=a['floor_mm']), a['floor_mm']), False)) < 1e-9


def protrusion_mutation(cx, cand, E):
    rc = copy.deepcopy(E['r_case'])
    rc['rows'][0]['MAIN'][1] = E['D'] / 2.0 + 0.5
    return not g4.bosses_permitted(cx.st, E['r_case'], E['D'], cx.ce[cand['id']].sp.pc_mid['boss_mm']) and \
        bool(g4.bosses_permitted(cx.st, rc, E['D'], cx.ce[cand['id']].sp.pc_mid['boss_mm']))


def h05_merge_caught(res, lead):
    mut = copy.deepcopy(res)
    mut['lanes'][lead]['L-RAD']['h05_geom']['terms'].append('H05-EDGE-XL-LRA')
    return any('blended' in f for f in quick_lane_checks(mut)) and not any('blended' in f for f in quick_lane_checks(res))


def closed_form_crosscheck(cx, E):
    """Exact polygon geometry used in the charger / clearance predicates vs the production g4 functions."""
    p = E['chg']['pose']
    land = dict(type='poly', pts=p['land_poly'])
    ok = True
    for rid in ('GNSS_RAD', 'BLE_RAD', 'WIFI_RAD'):
        d1 = poly_distance(land, cx.st.res[rid]['geometry'])
        d2 = g4.region_distance(land, cx.st.res[rid]['geometry'], 0.02)
        ok = ok and abs(d1 - d2) <= 0.03
    ok = ok and abs(poly_rmin(p['land_poly']) - p['land_rmin']) < 1e-12
    ok = ok and g4.overlaps(land, cx.st.res['CHG_CONTACT']['geometry'])
    return ok


# --------------------------------------------------------------------------------------------
# R5 regressions: seal population unit invariance (mm / m / um internal representation, end to end), zero representative-row
# feedback, input contract transcription
# --------------------------------------------------------------------------------------------
R5_UNITS = ('m', 'um')
R5_TOL = 1e-9


def seal_canonical(seal):
    """The physical content of a seal record: the display-only representative rows and the internal-unit tag removed (never read)."""
    out = dict((k, v) for k, v in seal.items() if k not in ('topologies', 'internal_unit'))
    out['topologies'] = {t: dict((k, v) for k, v in o.items() if k != 'representative_row') for t, o in seal['topologies'].items()}
    return out


def diff_paths(a, b, tol=R5_TOL, path='', out=None, limit=6):
    """Differing paths of two canonical records (numbers within tol); for the self-test notes."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append('%s.%s (missing)' % (path, k))
            else:
                diff_paths(a[k], b[k], tol, '%s.%s' % (path, k), out, limit)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff_paths(x, y, tol, '%s[%d]' % (path, i), out, limit)
    elif not same(a, b, tol):
        out.append('%s: %r != %r' % (path, a, b))
    return out


def seal_point_evidence(cx, cand, row, t_out=None):
    """Production seal path of ONE point: the population record and every physical quantity derived from it there."""
    ms = main_seal(cx, cand, row)
    return dict(seal=seal_canonical(ms), r_lim=seal_r_lim(ms), flange_top=flange_top(cx, cand, ms, t_out), seal_typed=seal_typed_column(ms),
                h11_open=h11_typed(ms, True), h11_closed_path=h11_typed(ms, False))


def candidate_seal_evidence(cx, E, H, disp, stops, verdict):
    """Every seal-dependent physical result of one evaluated candidate (canonical mm): seal population record, coupled r_lim / flange
    envelope and its consumers (flange feature, closure clearances, G4 design terms, H14 seal-flange rows), radial supplier land
    thresholds, charger per seal topology, apertures (H13), every hard check (status, pass, margin, units, thresholds, typed terms),
    lane dispositions, stops, verdict, owner-question thresholds (Q-R1-MAIN-SEAL, Q-R1-CHARGER), sweep seal / charger / structure
    columns and the D classification."""
    oq = {x['id']: x.get('thresholds') for x in owner_questions(E, disp, stops) if x['id'] in ('Q-R1-MAIN-SEAL', 'Q-R1-CHARGER')}
    sweep = [[r['D'], [[t['tw'], t['groups'], t['r_lim'], t['seal_typed'], t['seal_feasible'], t['seal_r_lim_fallback'], t['seal_flange_top'],
                        t['charger'], t['charger_strict_width'], t['structure']['pass_'], t['structure']['bound_mm']] for t in r['tw_rows']]]
             for r in E['sweep']['rows']]
    return dict(
        D=E['D'], tw=E['tw'], seal=seal_canonical(E['seal']), dp=E['dp'], flange_top=E['chg']['flange_top_mm'], r_lim=E['chg']['r_lim'],
        seal_flange_rows=E['chg']['seal_flange_rows'], flange_feature=[f for f in E['features'] if f['id'] == 'CB_SEAL_FLANGE'],
        closure=E['closure'], strict_wedge=E['strict_wedge'], aperture=E['aperture_feasible'], seal_closure=E['seal_closure'],
        chg_by_topology={t: dict((k, v) for k, v in s.items() if k != 'evaluations') for t, s in E['chg_by_topology'].items()},
        chg_by_topology_rows={t: [dict((k, x[k]) for k in ('rows', 'r_lim', 'flange_top_mm', 'categories', 'pass_', 'min_margin')) for x in s['evaluations']]
                              for t, s in E['chg_by_topology'].items()},
        charger=dict(pass_=E['chg']['pass_'], categories=E['chg']['categories'], pose=[E['chg']['pose'][k] for k in ('orientation', 'r_centre', 'az_centre')]),
        hard_checks={h: dict((k, x[k]) for k in ('study_status', 'physical_pass', 'margin', 'units', 'threshold_value', 'required_delta', 'gate_ids',
                                                 'typed', 'governing_terms', 'supplier_zero_margin')) for h, x in H.items()},
        dispositions=disp, stops=sorted(s['id'] for s in stops if s['raised']), verdict=verdict, owner_question_thresholds=oq,
        asm=E['asm']['dependencies'], sweep=sweep,
        classification=dict((k, E['classification'][k]) for k in ('main_seal_first', 'coupled_first_D', 'charger_first_D', 'D_min', 'D_complete',
                                                                  'D_radial_core', 'groups')))


def study_seal_evidence(cx, Es, per, order, lead, verdict):
    return dict(order=order, lead=lead, verdict=verdict,
                candidates={cid: candidate_seal_evidence(cx, Es[cid], per[cid]['H'], per[cid]['disp'], per[cid]['stops'], per[cid]['verdict'])
                            for cid in Es})


def study_under(cx, in_proc, scope, **attrs):
    """The complete production study in a fresh context with the given seal attributes (seal_unit / seal_display_override)."""
    cx2 = Ctx(cx.st, cx.I, in_proc['res'], poses=cx.poses)
    for k, v in attrs.items():
        setattr(cx2, k, v)
    return (cx2,) + study_core(cx2, in_proc, scope)


def point_e2e(cx2, cand, Es2, in_proc, scope, point):
    """Production path at one explicit (D, tw) point: candidate lanes at that point (study sweep reused read-only), hard checks, lane
    dispositions, stops (against the context's other candidates) and the verdict of that point."""
    E = evaluate_candidate(cx2, cand, sw=Es2[cand['id']]['sweep'], point=point)
    H = hard_checks(cx2, E, in_proc, scope)
    disp = lane_dispositions(E, H)
    stops = stops_of(cx2, E, H, disp, [E if e['id'] == cand['id'] else e for e in Es2.values()], in_proc, scope)
    return E, candidate_seal_evidence(cx2, E, H, disp, stops, verdict_of(disp, stops))


def r5_cache(cx, in_proc, Es, scope):
    """Production studies under the m / um internal seal unit and under a refusing display row, computed once for the R5 tests."""
    c = cx.__dict__.setdefault('r5_cache', {})
    if not c:
        Es0, per0, order0, lead0, verdict0 = study_core(cx, in_proc, scope, Es=Es)
        c['base'] = dict(Es=Es0, ev=study_seal_evidence(cx, Es0, per0, order0, lead0, verdict0))
        for u in R5_UNITS:
            cxu, Esu, peru, orderu, leadu, verdictu = study_under(cx, in_proc, scope, seal_unit=u)
            c[u] = dict(cx=cxu, Es=Esu, ev=study_seal_evidence(cxu, Esu, peru, orderu, leadu, verdictu))
    return c


def r5_study_unit_invariance(cx, in_proc, Es, scope, u, notes):
    """End-to-end: the complete production study (sweeps, classification, design points, every lane, hard checks, dispositions, stops,
    ranking, verdict, owner-question thresholds) with the seal / flange population evaluated in internal unit u equals the mm study
    after canonical conversion, and the internal unit really was u."""
    c = r5_cache(cx, in_proc, Es, scope)
    d = diff_paths(c['base']['ev'], c[u]['ev'])
    notes.extend(d)
    used = {E['seal']['internal_unit'] for E in c[u]['Es'].values()} == {u}
    return used and not d


def r5_point_unit_invariance(cx, in_proc, Es, scope, cid, point, notes):
    """End-to-end at one explicit point (production seal / H11 / H13 / H14 / charger / disposition / verdict path): mm vs m vs um."""
    c = r5_cache(cx, in_proc, Es, scope)
    cand = next(x for x in cx.cands if x['id'] == cid)
    E0, ev0 = point_e2e(cx, cand, c['base']['Es'], in_proc, scope, point)
    ok = True
    for u in R5_UNITS:
        Eu, evu = point_e2e(c[u]['cx'], cand, c[u]['Es'], in_proc, scope, point)
        d = diff_paths(ev0, evu)
        notes.extend('%s %s: %s' % (u, point, x) for x in d)
        ok = ok and not d and Eu['seal']['internal_unit'] == u
    return ok


def r5_sweep_population_invariance(cx, cand, sw, notes):
    """Every (D, bulk wall) point of the candidate's sweep: the production seal population record and every physical quantity derived
    from it (coupled r_lim, flange envelope, sweep seal column, R1-H11 typed record) are identical under the m / um internal units."""
    ok = True
    V = cx.P['V01_D_case_body']
    cxs = {}
    for u in ('mm',) + R5_UNITS:
        cxs[u] = copy.copy(cx)
        cxs[u].seal_unit = u
    n = 0
    for D in frange(V['start'], V['report_stop'], V['step']):
        for r in rad_tw(cx, cand, D, sw['carrier'], sw['arcs'])[1]:
            base = seal_point_evidence(cxs['mm'], cand, r)
            for u in R5_UNITS:
                d = diff_paths(base, seal_point_evidence(cxs[u], cand, r))
                if d:
                    ok = False
                    notes.extend('D %.2f tw %.2f %s: %s' % (D, r['tw'], u, x) for x in d[:2])
            n += 1
    return ok and n == sum(len(x['tw_rows']) for x in sw['rows'])


def r5_zero_feedback(cx, in_proc, Es, scope, notes):
    """Zero representative-row feedback: (a) the complete production study with a display row that REFUSES every read (any physical,
    hard-check, stop, threshold, owner-question or disposition path that read it would STOP) equals the default study; (b) the
    design point of every candidate with the display row forced to the first and to the last evaluated row of each topology (the forced
    rows really differ from the default somewhere) gives identical physical results, flange_top, r_lim, H01..H20, thresholds,
    dispositions, stops and verdicts."""
    c = r5_cache(cx, in_proc, Es, scope)
    cxp, Esp, perp, orderp, leadp, verdictp = study_under(cx, in_proc, scope, seal_display_override='poison')
    if not all(isinstance(E['seal']['topologies'][t]['representative_row'], DisplayOnlyRow) for E in Esp.values() for t in SEAL_ORDER):
        notes.append('poison display row not installed')
        return False
    d = diff_paths(c['base']['ev'], study_seal_evidence(cxp, Esp, perp, orderp, leadp, verdictp))
    notes.extend('poison: ' + x for x in d)
    ok = not d
    changed = False
    for ovr in ('first', 'last'):
        cxo = Ctx(cx.st, cx.I, in_proc['res'], poses=cx.poses)
        cxo.seal_display_override = ovr
        for cid, E0 in c['base']['Es'].items():
            cand = E0['cand']
            Eo, evo = point_e2e(cxo, cand, c['base']['Es'], in_proc, scope, (E0['D'], E0['tw']))
            _, ev0 = point_e2e(cx, cand, c['base']['Es'], in_proc, scope, (E0['D'], E0['tw']))
            dd = diff_paths(ev0, evo)
            notes.extend('%s %s: %s' % (ovr, cid, x) for x in dd)
            ok = ok and not dd
            for t in SEAL_ORDER:
                o = Eo['seal']['topologies'][t]
                want = o['evaluated_rows'][0 if ovr == 'first' else -1]
                ok = ok and o['representative_row']['id'] == want
                changed = changed or want != E0['seal']['topologies'][t]['representative_row']['id']
    if not changed:
        notes.append('forced display rows never differ from the default rows (vacuous)')
    return ok and changed


def r5_mixed_unit_key_would_vary(cx, cand, E):
    """Positive anchor of the defect R5 removes: the R4 mixed-unit row key (pass, min over dimensionless AND mm margins, -cs) applied to
    the production rows picks a different face / radial cross-section under the m / um representations, while every R5 population
    reduction, the coupled r_lim and the flange envelope stay identical (R5 never uses such a key)."""
    picks, evs = {}, {}
    for u in ('mm',) + R5_UNITS:
        cxu = copy.copy(cx)
        cxu.seal_unit = u
        ms = main_seal(cxu, cand, E['row'])
        s = SEAL_UNITS[u]
        key = lambda r: (r['pass_all'], min((v * s if H11_UNITS_OF[k] == 'mm' else v) for k, v in r['margins'].items()), -(r['cs_mm'] or 0.0))
        picks[u] = tuple(max((r for r in ms['rows'] if r['topology'] == t and r['authorized']), key=key)['id'] for t in ('face', 'radial'))
        evs[u] = seal_point_evidence(cxu, cand, E['row'], E['strl']['selected']['t_out'])
    return len(set(picks.values())) > 1 and all(not diff_paths(evs['mm'], evs[u]) for u in R5_UNITS)


def r5_input_contract_tamper(r1in, kind):
    """R5-2 (production input fault injection): the literal C-R1-01 2(v) transcription of the R1 input (or the brief scope it is checked
    against) is tampered; input_contract_violations - the build STOP guard and a check rule - rejects it; the authored input passes."""
    mut = copy.deepcopy(r1in)
    rc = mut['parameters']['V20_charger_land']['route_clearance']
    brief = None
    if kind == 'rule_conductive_block':
        rc['rule'] = rc['rule'].replace('bond/seal land', 'bond/seal land (and the conductive block)')
    elif kind == 'r4_rule_text':
        rc['rule'] = ('C-R1-01 (v): the land (and the conductive block) clears screws, supports, CHG_ROUTE and CHG_LINK in plan AND in Z; a Z '
                      'separation never waives a plan collision (touching counts as a collision). C-R1-01 (vi) neighbours use the common 3-D clearance.')
    elif kind == 'subject_block':
        rc['subject'] = 'the conductive contact block (C-R1-01 item 1)'
    elif kind == 'contract_text_not_verbatim':
        rc['contract_text'] = '(v) the land and the block clear screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z'
    elif kind == 'screen_relabelled_contract':
        rc['block_and_z_screen']['evidence_class'] = 'CONTRACT (C-R1-01 item 1, literal)'
    elif kind == 'brief_v_in_block_item':
        txt = (ROOT / BRIEF).read_text(encoding='utf-8')
        brief = txt.replace('and clear of WIFI_RAD (H17);', 'clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z, and clear of WIFI_RAD (H17);', 1)
    else:
        raise StudyError('unknown input contract tamper %s' % kind)
    return bool(input_contract_violations(mut, brief)) and not input_contract_violations(r1in)


def r5_seal_validator_tamper(cx, res, lead, kind):
    """R5 (validator): a result whose seal-dependent physical quantity is taken from one representative row (the R4 choices) instead of
    the population reduction is rejected by seal_population_violations; the reported result passes."""
    mut = copy.deepcopy(res)
    L = mut['lanes'][lead]
    ms = L['L-SEAL']['main_seal']
    rows = {r['id']: r for r in ms['rows']}
    tol_cb = g4.Specs(cx.st, next(c for c in cx.cands if c['id'] == lead)).pc_cb['thickness_mm']
    if kind == 'flange_top_from_one_row':
        ft = rows['face#00']['flange']['thickness_mm'] + tol_cb
        L['L-SEAL']['flange_top_mm'] = L['L-CHG']['selected']['flange_top_mm'] = ft
        for f in L['features']:
            if f['id'] == 'CB_SEAL_FLANGE':
                f['z_hi_adv'] = ft
    elif kind == 'r_lim_from_one_radial_row':
        rl = rows['radial#01']['r_lim_mm']
        ms['coupled']['r_lim_mm'] = L['design_point_g4_terms']['r_lim'] = L['L-CHG']['selected']['r_lim'] = rl
    elif kind == 'h11_term_from_one_row':
        ms['topologies']['radial']['term_reductions']['gland_compression_min']['value'] = rows['radial#01']['margins']['gland_compression_min']
    elif kind == 'supplier_threshold_from_one_row':
        swr = L['L-CHG']['strict_wedge_diagnostic']['at_radial_r_lim']
        swr['governing_threshold_mm'] = next(x['width_mm'] for x in swr['rows'] if x['row'] == 'radial#01')
    elif kind == 'representative_physical':
        ms['topologies']['face']['representative_row']['display_only'] = False
    elif kind == 'seal_cs_representative':
        L['design_point_g4_terms']['seal_cs'] = rows['face#00']['cs_mm']
    elif kind == 'feasible_from_one_row':
        ms['topologies']['face']['feasible'] = True
    else:
        raise StudyError('unknown seal validator tamper %s' % kind)
    return bool(seal_population_violations(cx, mut)) and not seal_population_violations(cx, res)


def r5_sweep_seal_tamper_fresh(cx, in_proc, res, lead):
    """A sweep point's seal population columns replaced by single-row values (the R4 representative flange top, a radial row's r_lim)
    consistently - flags untouched - are caught only by the fresh per-point re-evaluation of the leader's sweep."""
    mut = copy.deepcopy(res)
    enc = mut['lanes'][lead]['sweep']['encoding']
    rows = mut['lanes'][lead]['sweep']['rows']
    tw = rows[len(rows) // 2]['tw'][0]
    tw[enc['tw_columns'].index('seal_flange_top')] -= 0.5
    tw[enc['tw_columns'].index('r_lim')] -= 0.8
    bad, _ = recompute_diameters(cx.st, in_proc, mut, cx.poses)
    return any('seal population columns' in b for b in bad)


def r5_button_margins_unit_typed(res):
    """R5 file-wide audit anchor: every reported T2 button section's min_margin is the minimum over its mm margins only (the dimensionless
    boot strain is typed and carried separately), and pass_ still requires every margin >= 0."""
    n = 0
    for L in res['lanes'].values():
        for r in L['L-BTN']['switches'].values():
            for s in [r['best'][i] for i in ('I-SUM', 'I-MAX')] + [r['T2'][t][i] for t in r['T2'] for i in ('I-SUM', 'I-MAX')]:
                u = s['margin_units']
                lin = [v for k, v in s['margins'].items() if u[k] == 'mm']
                if u.get('strain') != 'dimensionless' or abs(s['min_margin'] - min(lin)) > 1e-12 or s['strain_margin'] != s['margins']['strain'] or \
                        s['pass_'] != (all(v >= -EPS for v in s['margins'].values()) and all(s['predicates'].values())):
                    return False
                n += 1
    return n > 0


def r5_h11_anchor(cx, res, E):
    """Positive anchor: the reported R1-H11 margin of the leader is the max over the authorized V11 rows of the radial compression-minimum
    margin, recomputed here directly from the accepted G4 gland specifications (no main_seal call)."""
    cand = E['cand']
    sp = g4.Specs(cx.st, cand)
    V = cx.P['V11_main_seal_cs']
    vals = []
    for cs in grid(dict(start=V['start'], stop=V['stop'], step=V['step'])):
        gd = g4.gland_design(cx.st, sp, 'radial', cs)
        vals.append(g4.run_check(sp.gland('X', 'static_radial', gd['cs'], gd['h'], gd['g'], gd['tol_h'], gd['tol_g'])[0], False))
    h = res['hard_checks']['R1-H11']
    return h['units'] == 'dimensionless' and h['typed']['governing']['term_id'] == 'H11-RADIAL-gland_compression_min' and \
        abs(h['margin'] - max(vals)) < 5e-9 and max(vals) < 0


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------
def main(argv):
    if len(argv) != 2 or argv[1] not in ('build', 'check', 'selftest'):
        sys.stderr.write('usage: g4_r1_blockers.py build|check|selftest\n')
        return 2
    t0 = time.time()
    try:
        timing = {}
        res, cx, in_proc, Es = build_r1_results(timing)
        files = r1_outputs(res, cx.st)
        if argv[1] == 'build':
            for name, text in files.items():
                (GEN / name).write_bytes(text.encode('utf-8'))
            print(json.dumps(dict(status='BUILT', verdict=res['verdict'], files=sorted(files), evaluations=res['search']['evaluations'],
                                  runtime_s=round(time.time() - t0, 1)), sort_keys=True))
            return 0
        if argv[1] == 'selftest':
            tests = r1_self_tests(res, files, cx, in_proc, Es)
            ok = all(x['caught'] for x in tests)
            names = dict(PIF='production_input_fault_injections', PGF='production_geometry_fault_injections', PA='solver_positive_anchors',
                         VS='validator_semantic_tests', SR='serialization_result_object_tests')
            if any(x['category'] not in names for x in tests):
                raise StudyError('STOP: self-test outside the five R3-10 categories')
            cats = {names[c]: dict(total=sum(1 for x in tests if x['category'] == c), passed=sum(1 for x in tests if x['category'] == c and x['caught']))
                    for c in names}
            print(json.dumps(dict(status='PASS' if ok else 'FAIL', tests=len(tests), passed=sum(x['caught'] for x in tests), categories=cats,
                                  r2_regressions=[x['id'] for x in tests if x['id'].startswith('r2_')],
                                  r3_regressions=[x['id'] for x in tests if x['id'].startswith('r3_')],
                                  r4_regressions=[x['id'] for x in tests if x['id'].startswith('r4_')],
                                  r5_regressions=[x['id'] for x in tests if x['id'].startswith('r5_')],
                                  not_caught=[x for x in tests if not x['caught']], runtime_s=round(time.time() - t0, 1)), sort_keys=True))
            return 0 if ok else 1
        fails = r1_validate(res, files, cx, in_proc, lambda: time.time() - t0)
        print(json.dumps(dict(status='PASS' if not fails else 'FAIL', failures=fails, verdict=res['verdict'],
                              stops_raised=[s['id'] for s in res['stops'] if s['raised']], selected=res['ranking']['selected'],
                              evaluations=res['search']['evaluations'], runtime_s=round(time.time() - t0, 1)), sort_keys=True))
        return 0 if not fails else 1
    except StudyError as exc:
        print(json.dumps(dict(status='STOP', reason=str(exc))))
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
