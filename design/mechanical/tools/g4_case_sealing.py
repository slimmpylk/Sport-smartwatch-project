#!/usr/bin/env python3
"""G4 case / caseback / sealing-architecture closure study (Rev-A). Stdlib only, deterministic.

Sub-commands:
  build     write the G4 generated outputs (generated/g4_case_sealing.{json,md}, g4_*.svg)
  check     regenerate in memory; fail on byte difference, source-pin mismatch, LEGACY mismatch,
            an inconsistent selection, an unreported Z delta, scope or budget overrun
  selftest  inject the G4_BRIEF section 11 faults and prove each one is caught

This is a mechanical PARAMETRIC / CLOSURE study. It is not case CAD, not RF work, not FEA and not
5 ATM qualification. It writes no KiCad file. G1 / G2 / G3 functions and tolerance policies are
imported, never re-implemented; G3 data are read through a pinned hash.
"""
import copy
import hashlib
import functools
import html
import json
import math
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
MECH = ROOT / 'design/mechanical'
GEN = MECH / 'generated'
sys.path.insert(0, str(MECH / 'tools'))
import mech_model as mm  # noqa: E402
import g1_scenarios as g1  # noqa: E402
import g2_interconnect as g2  # noqa: E402
import arch_diagrams as ad  # noqa: E402

IN_PATH = MECH / 'inputs/g4_case_sealing.json'
OUT = ('g4_case_sealing.json', 'g4_case_sealing.md', 'g4_plan.svg', 'g4_sections.svg',
       'g4_seal_map.svg', 'g4_assembly.svg', 'g4_sweep.jsonl')
EPS = 1e-9
WALL_MODEL_LIMITATION = ('One scalar side-wall thickness tw is used per design point at MAIN, BATTERY and REAR. '
                          'The r_case(az,z) table adds local feature envelopes and level-specific recesses; it does not '
                          'solve independent t_wall(az,z). No azimuth-resolved wall closure is established.')
CHARGER_CONTAINMENT_ASSUMPTION = ('H20 requires BOTH the 4 x 5 mm contact block AND its modeled continuous '
                                 'bond/seal land inside the authorized aperture/wedge and radial bounds at adverse '
                                 'tolerance. The land is not allowed to extend outside that envelope; this is a '
                                 'planning modeling assumption, not a supplier-qualified block.')
ROLES = ('DESIGN', 'MFG_TOL', 'SUPPLIER_GATED', 'OWNER_GATED', 'FROZEN')
LIMIT_CLASSES = ('OWNER REQUIREMENT', 'MANUFACTURER REQUIREMENT', 'SUPPLIER REQUIREMENT',
                 'PROJECT-DERIVED LIMIT', 'PROVISIONAL PLANNING LIMIT')
HARD = {
    'H01': ('G2-REVA and G2-REVA-HI reproduced; G4 Z delta 0.000', 'exact', 'PROJECT-DERIVED LIMIT'),
    'H02': ('T_total <= 16.5 nominal and <= 17.0 RSS on both baselines', 'nominal, RSS', 'OWNER REQUIREMENT'),
    'H03': ('D_case_body <= 51.00; bosses only as permitted, <= +1.0 mm', 'linear worst', 'OWNER REQUIREMENT'),
    'H04': ('LEGACY numbers of section 3 reproduced exactly', 'exact', 'PROJECT-DERIVED LIMIT'),
    'H05': ('Radial channel and edge-crossing margins >= 0, every crossing', 'linear worst', 'PROJECT-DERIVED LIMIT'),
    'H06': ('X25 cover fit and bezel wall >= t_bezel_min', 'linear worst', 'PROVISIONAL PLANNING LIMIT'),
    'H07': ('Cover plate sizing >= requirement for designed a_cover; air-gap rule', 'G1 conservative', 'PROJECT-DERIVED LIMIT'),
    'H08': ('No case feature proud of the cover unless counted in T_total', 'exact', 'OWNER REQUIREMENT'),
    'H09': ('U4 land headroom >= 0 (relief or local t_land)', 'linear worst', 'PROJECT-DERIVED LIMIT'),
    'H10': ('Pack + growth inside carrier; no pack load path', 'linear worst', 'SUPPLIER REQUIREMENT'),
    'H11': ('Caseback wall fits the pod residual; h_pod >= 0', 'linear worst', 'PROJECT-DERIVED LIMIT'),
    'H12': ('>= 1 window variant passes the simply-supported screen without Z delta', 'G1 conservative', 'PROVISIONAL PLANNING LIMIT'),
    'H13': ('Window / caseback deflection < clearance to optics / REAR at p max', 'linear worst', 'PROJECT-DERIVED LIMIT'),
    'H14': ('Seal inventory complete; seal path closed; separate feedthrough seals', 'exact', 'PROJECT-DERIVED LIMIT'),
    'H15': ('Gland compression and fill inside window', 'linear worst', 'PROVISIONAL PLANNING LIMIT'),
    'H16': ('Seal / bond lands >= planning minimum', 'linear worst', 'PROVISIONAL PLANNING LIMIT'),
    'H17': ('Zero new conductive / wiring intrusion into radiator volumes', 'exact', 'PROJECT-DERIVED LIMIT'),
    'H18': ('No new ferromagnetic material inside MAG_CLEAR', 'exact', 'PROJECT-DERIVED LIMIT'),
    'H19': ('S14 outline, pod, supports, tail exit (incl. conservative corridor), U6 island untouched and unobstructed', 'linear worst', 'PROJECT-DERIVED LIMIT'),
    'H20': ('Charger block, feedthrough and corridors clear', 'linear worst', 'PROJECT-DERIVED LIMIT'),
    'H21': ('Buttons: bore length, body height, radiator / MAG / insertion clearances, boss limits', 'linear worst', 'PROVISIONAL PLANNING LIMIT'),
    'H22': ('LRA placement window non-empty; recommended pose collision-free', 'linear worst', 'PROVISIONAL PLANNING LIMIT'),
    'H23': ('Rear-insertion path collision-free; every operation has an access direction', 'linear worst', 'PROJECT-DERIVED LIMIT'),
    'H24': ('>= 4 case / caseback supports incl. W/NW (X14), all outside the pack (X18)', 'exact', 'PROJECT-DERIVED LIMIT'),
    'H25': ('No KiCad / interface / immutable-file change', 'exact', 'PROJECT-DERIVED LIMIT'),
}
G3_IMMUTABLE = [
    'design/mechanical/inputs/input_register.json', 'design/mechanical/inputs/stack_parameters.json',
    'design/mechanical/inputs/package_heights.json', 'design/mechanical/inputs/g1_scenarios.json',
    'design/mechanical/inputs/g2_interconnect.json', 'design/mechanical/inputs/g3_rear_optical.json',
    'design/mechanical/tools/mech_model.py', 'design/mechanical/tools/mech_model_spec.md',
    'design/mechanical/tools/g1_scenarios.py', 'design/mechanical/tools/g2_interconnect.py',
    'design/mechanical/tools/g3_rear_optical.py', 'design/mechanical/generated/zstack.json',
    'design/mechanical/generated/zstack.md', 'design/mechanical/generated/zstack_section.svg',
    'design/mechanical/generated/main_height_map.json', 'design/mechanical/generated/main_height_map.md',
    'design/mechanical/generated/main_height_map.svg', 'design/mechanical/generated/g1_scenarios.json',
    'design/mechanical/generated/g1_scenarios.md', 'design/mechanical/generated/g2_interconnect.json',
    'design/mechanical/generated/g2_interconnect.md', 'design/mechanical/generated/g2_allocation.svg',
    'design/mechanical/generated/g3_rear_optical.json', 'design/mechanical/generated/g3_rear_optical.md',
    'design/mechanical/generated/g3_rear_faces.svg', 'design/mechanical/generated/g3_rear_section.svg',
    'design/mechanical/generated/perimeter_map.svg', 'design/mechanical/generated/rear_module_concept.svg',
    'design/mechanical/generated/interconnect_paths.svg', 'design/mechanical/PHASE_BRIEF.md',
    'design/mechanical/G1_BRIEF.md', 'design/mechanical/G2_BRIEF.md', 'design/mechanical/G3_BRIEF.md']
ALLOWED_CHANGES = {
    'design/mechanical/architecture.md', 'design/mechanical/architecture.json', 'design/mechanical/README.md',
    'design/mechanical/tools/arch_diagrams.py', 'design/mechanical/inputs/g4_case_sealing.json',
    'design/mechanical/tools/g4_case_sealing.py'} | {'design/mechanical/generated/' + n for n in OUT}


class StudyError(Exception):
    """A STOP condition of the deterministic model (input contradiction or broken invariant)."""


# --------------------------------------------------------------------------------------------
# I/O and formatting
# --------------------------------------------------------------------------------------------
def load(p):
    return g2.load(p)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def chash(o):
    return hashlib.sha256(g2.dumps(o).encode()).hexdigest()


def rounded_g4(o):
    if isinstance(o,float): return round(o,9)+0.0
    if isinstance(o,dict): return {k:rounded_g4(v) for k,v in o.items()}
    if isinstance(o,(list,tuple)): return [rounded_g4(v) for v in o]
    return o

def dumps(o):
    return json.dumps(rounded_g4(o), sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'


def f3(v):
    return 'n/a' if v is None else '%.3f' % (round(v, 3) + 0.0)


def f2(v):
    return 'n/a' if v is None else '%.2f' % (round(v, 2) + 0.0)


def frange(start, stop, step):
    n = int(round((stop - start) / step))
    return [round(start + i * step, 6) for i in range(n + 1)]


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)


# --------------------------------------------------------------------------------------------
# Plane geometry (assembly front view: north = -Y, east = +X, azimuth clockwise from north)
# --------------------------------------------------------------------------------------------
def xy(r, az):
    t = math.radians(az)
    return (100.0 + r * math.sin(t), 100.0 - r * math.cos(t))


def polar(p):
    dx, dy = p[0] - 100.0, p[1] - 100.0
    return math.hypot(dx, dy), math.degrees(math.atan2(dx, -dy)) % 360.0


def arc_has(a, a0, a1):
    span = (a1 - a0) % 360.0
    span = 360.0 if span == 0.0 and a1 != a0 else span
    return (a - a0) % 360.0 <= span + 1e-9


def arc_gap(a, b):
    """Angular gap between two clockwise arcs [a0,a1], [b0,b1] (0 when they overlap)."""
    if arc_has(a[0], *b) or arc_has(a[1], *b) or arc_has(b[0], *a):
        return 0.0
    return min((b[0] - a[1]) % 360.0, (a[0] - b[1]) % 360.0)


def seg_dist(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    v2 = vx * vx + vy * vy
    t = 0.0 if v2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / v2))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


def pip(p, poly):
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > p[1]) != (y1 > p[1]):
            x = x0 + (p[1] - y0) * (x1 - x0) / (y1 - y0)
            if x > p[0]:
                inside = not inside
    return inside


def pt_region(p, g):
    """Distance from a point to a region (0 inside). Region types as architecture.json plus 'poly'."""
    t = g['type']
    if t == 'rect':
        x0, y0, x1, y1 = g['rect']
        return math.hypot(max(x0 - p[0], 0.0, p[0] - x1), max(y0 - p[1], 0.0, p[1] - y1))
    if t == 'circles':
        return min(max(0.0, math.hypot(p[0] - x, p[1] - y) - r) for x, y, r in g['circles'])
    if t == 'poly':
        pts = g['pts']
        if pip(p, pts):
            return 0.0
        return min(seg_dist(p, a, b) for a, b in zip(pts, pts[1:] + pts[:1]))
    a0, a1 = g['az']
    r0, r1 = g['r']
    r, az = polar(p)
    if arc_has(az, a0, a1):
        return max(r0 - r, 0.0, r - r1)
    return min(seg_dist(p, xy(r0, a0), xy(r1, a0)), seg_dist(p, xy(r0, a1), xy(r1, a1)))


def circle_clear(c, rho, g):
    return pt_region(c, g) - rho


def rect_cover(c, length, width, ang):
    """Superset cover of a rectangle by circles on its long axis (bulge <= 3.1 % of half-width)."""
    s = width / 4.0
    rho = math.hypot(width / 2.0, s / 2.0)
    n = max(1, int(math.ceil((length - s) / s)) + 1)
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    half = (length - s) / 2.0
    out = []
    for i in range(n):
        d = -half + (2 * half * i / (n - 1) if n > 1 else 0.0)
        out.append(((c[0] + d * ux, c[1] + d * uy), rho))
    return out


def sector(a0, a1, r0, r1):
    full = (a1 - a0) >= 360.0 - EPS
    return dict(type='sector', az=[0.0, 360.0] if full else [a0 % 360.0, a1 % 360.0], r=[r0, r1])


def boundary_points(g, step=0.05):
    t = g['type']
    pts = []
    if t == 'rect':
        x0, y0, x1, y1 = g['rect']
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        t, g = 'poly', dict(type='poly', pts=poly)
    if t == 'poly':
        p = g['pts']
        for a, b in zip(p, p[1:] + p[:1]):
            n = max(1, int(math.ceil(math.dist(a, b) / step)))
            pts += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
        return pts
    if t == 'circles':
        for x, y, r in g['circles']:
            n = max(8, int(math.ceil(2 * math.pi * r / step)))
            pts += [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        return pts
    a0, a1 = g['az']
    r0, r1 = g['r']
    span = (a1 - a0) % 360.0 or 360.0
    for r in (r0, r1):
        n = max(2, int(math.ceil(math.radians(span) * max(r, 0.1) / step)))
        pts += [xy(r, a0 + span * i / n) for i in range(n + 1)]
    for a in (a0, a1):
        n = max(2, int(math.ceil((r1 - r0) / step)))
        pts += [xy(r0 + (r1 - r0) * i / n, a) for i in range(n + 1)]
    return pts


def region_distance(ga, gb, step=0.05):
    return _region_distance(json.dumps(ga,sort_keys=True),json.dumps(gb,sort_keys=True),step)


@functools.lru_cache(maxsize=25000)
def _region_distance(ja,jb,step):
    ga,gb=json.loads(ja),json.loads(jb)
    """Plan distance between two regions (0 if they touch/overlap); boundary sampled at `step`."""
    pa, pb = boundary_points(ga, step), boundary_points(gb, step)
    if any(pt_region(p, gb) <= 0.0 for p in pa) or any(pt_region(p, ga) <= 0.0 for p in pb):
        return 0.0
    return min(min(pt_region(p, gb) for p in pa), min(pt_region(p, ga) for p in pb))


def segment_intersects(a,b,c,d):
    def cross(p,q,r): return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    if max(a[0],b[0])<min(c[0],d[0])-EPS or max(c[0],d[0])<min(a[0],b[0])-EPS or max(a[1],b[1])<min(c[1],d[1])-EPS or max(c[1],d[1])<min(a[1],b[1])-EPS: return False
    return cross(a,b,c)*cross(a,b,d)<=EPS and cross(c,d,a)*cross(c,d,b)<=EPS


def polygon_overlap(poly,g):
    edges=list(zip(poly,poly[1:]+poly[:1]))
    if any(pt_region(p,g)<=EPS for p in poly): return True
    if g['type']=='circles':
        return any(pip((x,y),poly) or min(seg_dist((x,y),a,b) for a,b in edges)<=r+EPS for x,y,r in g['circles'])
    if g['type'] in ('poly','rect'):
        other=g['pts'] if g['type']=='poly' else [(g['rect'][0],g['rect'][1]),(g['rect'][2],g['rect'][1]),(g['rect'][2],g['rect'][3]),(g['rect'][0],g['rect'][3])]
        return any(pip(p,poly) for p in other) or any(segment_intersects(a,b,c,d) for a,b in edges for c,d in zip(other,other[1:]+other[:1]))
    r0,r1=g['r'];a0,a1=g['az']
    if r1<=r0: return False
    if any(pip(xy(r,a),poly) for r in (r0,r1) for a in (a0,a1)): return True
    for a,b in edges:
        if any(segment_intersects(a,b,xy(r0,az),xy(r1,az)) for az in (a0,a1)): return True
        dx,dy=b[0]-a[0],b[1]-a[1]; ax,ay=a[0]-100,a[1]-100
        aa=dx*dx+dy*dy
        if aa<=EPS: continue
        bb=2*(ax*dx+ay*dy)
        for radius in (r0,r1):
            cc=ax*ax+ay*ay-radius*radius;disc=bb*bb-4*aa*cc
            if disc < -EPS: continue
            for t in ((-bb-math.sqrt(max(0.,disc)))/(2*aa),(-bb+math.sqrt(max(0.,disc)))/(2*aa)):
                if -EPS<=t<=1+EPS and arc_has(polar((a[0]+t*dx,a[1]+t*dy))[1],a0,a1): return True
    return False


def overlaps(ga, gb):
    return _overlaps(json.dumps(ga,sort_keys=True),json.dumps(gb,sort_keys=True))


@functools.lru_cache(maxsize=30000)
def _overlaps(ja,jb):
    ga,gb=json.loads(ja),json.loads(jb)
    # Conservative radial interval prefilter: disjoint intervals cannot overlap.
    def radial_bound(g):
        if g['type']=='sector': return g['r']
        if g['type']=='circles':
            return [min(math.hypot(x-100,y-100)-r for x,y,r in g['circles']),max(math.hypot(x-100,y-100)+r for x,y,r in g['circles'])]
        pts=g['pts'] if g['type']=='poly' else [(x,y) for x in (g['rect'][0],g['rect'][2]) for y in (g['rect'][1],g['rect'][3])]
        return [0.,max(math.hypot(x-100,y-100) for x,y in pts)]
    a,b=radial_bound(ga),radial_bound(gb)
    if a[1]<b[0]-EPS or b[1]<a[0]-EPS: return False
    """Exact interior overlap for rect / sector / circles (arch_diagrams detector); sampled for polygons."""
    if ga['type']=='poly': return polygon_overlap(ga['pts'],gb)
    if gb['type']=='poly': return polygon_overlap(gb['pts'],ga)
    return ad.interiors_overlap(ga, gb, clip=40.0)


def poly_area(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2.0


def poly_perimeter(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:] + pts[:1]))


def inscribed_circle(pts, step=0.05):
    """Largest inscribed circle of a simple polygon: deterministic grid then local refinement."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    best = (0.0, None)

    def edge_d(p):
        return min(seg_dist(p, a, b) for a, b in zip(pts, pts[1:] + pts[:1]))
    x = min(xs)
    while x <= max(xs) + EPS:
        y = min(ys)
        while y <= max(ys) + EPS:
            p = (round(x, 6), round(y, 6))
            if pip(p, pts):
                d = edge_d(p)
                if d > best[0] + 1e-12:
                    best = (d, p)
            y += step
        x += step
    h = step
    d0, c = best
    for _ in range(12):
        h /= 2.0
        for dx in (-h, 0.0, h):
            for dy in (-h, 0.0, h):
                p = (c[0] + dx, c[1] + dy)
                if pip(p, pts):
                    d = edge_d(p)
                    if d > d0 + 1e-12:
                        d0, c = d, p
    return d0, c


# --------------------------------------------------------------------------------------------
# Axisymmetric annular-plate solver (Kirchhoff, closed-form general solution, Roark class)
# --------------------------------------------------------------------------------------------
def _solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        if abs(m[c][c]) < 1e-30:
            raise StudyError('singular plate system')
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for k in range(c, n + 1):
                    m[r][k] -= f * m[c][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def _basis(r, d, nu, q):
    lr = math.log(r)
    w = [1.0, r * r, lr, r * r * lr]
    wp = [0.0, 2 * r, 1 / r, 2 * r * lr + r]
    wpp = [0.0, 2.0, -1 / r ** 2, 2 * lr + 3]
    pw, pwp, pwpp = q * r ** 4 / (64 * d), q * r ** 3 / (16 * d), 3 * q * r * r / (16 * d)
    return dict(w=(w, pw), wp=(wp, pwp),
                Mr=([-d * (wpp[i] + nu * wp[i] / r) for i in range(4)], -d * (pwpp + nu * pwp / r)),
                Mt=([-d * (nu * wpp[i] + wp[i] / r) for i in range(4)], -d * (nu * pwpp + pwp / r)),
                Q=([0.0, 0.0, 0.0, -4 * d / r], -q * r / 2))


@functools.lru_cache(maxsize=30000)
def _annular_plate(regions, q, inner):
    """regions: [(r0, r1, t, E, nu)] contiguous; outer edge simply supported. inner: 'ss' (supported
    at the inner edge) or 'boss' (rigid guided boss carrying its own pressure). Returns max deflection
    relative to the supports, max bending stress and the inner support reaction."""
    n = len(regions)
    ds = [e * t ** 3 / (12 * (1 - nu * nu)) for _, _, t, e, nu in regions]
    rows, rhs = [], []

    def put(k, key, r, sgn=1.0):
        v, p = _basis(r, ds[k], regions[k][4], q)[key]
        row = [0.0] * (4 * n)
        for i in range(4):
            row[4 * k + i] = sgn * v[i]
        return row, sgn * p
    r0 = regions[0][0]
    for key in (('wp', 'Q') if inner in ('boss','loaded_boss') else ('w', 'Mr')):
        row, p = put(0, key, r0)
        rows.append(row)
        rhs.append((-q*r0/2 if inner=='loaded_boss' and key=='Q' else 0.)-p)
    for k in range(n - 1):
        rs = regions[k][1]
        for key in ('w', 'wp', 'Mr', 'Q'):
            a, pa = put(k, key, rs)
            b, pb = put(k + 1, key, rs, -1.0)
            rows.append([x + y for x, y in zip(a, b)])
            rhs.append(-(pa + pb))
    for key in ('w', 'Mr'):
        row, p = put(n - 1, key, regions[-1][1])
        rows.append(row)
        rhs.append(-p)
    x = _solve(rows, rhs)
    wmax = smax = 0.0
    for k, (ra, rb, t, _, nu) in enumerate(regions):
        for j in range(81):
            r = ra + (rb - ra) * j / 80.0
            bs = _basis(r, ds[k], nu, q)

            def val(key):
                return sum(c * v for c, v in zip(x[4 * k:4 * k + 4], bs[key][0])) + bs[key][1]
            wmax = max(wmax, abs(val('w')))
            smax = max(smax, 6.0 * max(abs(val('Mr')), abs(val('Mt'))) / t ** 2)
    bs = _basis(r0, ds[0], regions[0][4], q)
    qb = sum(c * v for c, v in zip(x[0:4], bs['Q'][0])) + bs['Q'][1]
    react = abs(qb * 2 * math.pi * r0) if inner == 'ss' else 0.0
    return dict(w=wmax, sigma=smax, inner_reaction_N=react)


def annular_plate(regions, q, inner):
    # Linear plate homogeneity: normalize common modulus/pressure and scale results exactly.
    if all(r[3]==regions[0][3] for r in regions):
        E=regions[0][3]
        base=_annular_plate(tuple((a,b,t,1.,nu) for a,b,t,e,nu in regions),1.,inner)
        return dict(w=base['w']*q/E,sigma=base['sigma']*q,inner_reaction_N=base['inner_reaction_N']*q)
    return _annular_plate(tuple(tuple(r) for r in regions), q, inner)


# --------------------------------------------------------------------------------------------
# OD-G4-CORNER term engine: LEGACY / NOMINAL / RSS / LINEAR WORST / GOVERNING / OWNER-GATED
# --------------------------------------------------------------------------------------------
class Term:
    __slots__ = ('name', 'role', 'ev', 'nom', 'adv', 'src')

    def __init__(self, name, role, ev, nom, adv=None, src=None):
        if role not in ROLES:
            raise StudyError('unknown term role ' + role)
        self.name, self.role, self.ev, self.nom = name, role, ev, nom
        self.adv = nom if adv is None else adv
        self.src = src

    def row(self):
        return dict(term=self.name, role=self.role, evidence_class=self.ev, nominal=self.nom, adverse=self.adv,
                    planning_range=self.src)


def validate_terms(terms):
    """SUPPLIER_GATED terms must sit at a planning-range extreme (never narrowed); MFG_TOL nominal is 0."""
    for t in terms:
        if t.role == 'SUPPLIER_GATED':
            if not t.src:
                raise StudyError('supplier-gated term without planning range: ' + t.name)
            lo, hi = t.src
            if lo - EPS > t.nom or t.nom > hi + EPS:
                raise StudyError('supplier-gated nominal outside its planning range: ' + t.name)
            if abs(t.adv - lo) > 1e-9 and abs(t.adv - hi) > 1e-9:
                raise StudyError('supplier-gated term narrowed below its planning range: ' + t.name)
        if t.role == 'MFG_TOL' and abs(t.nom) > EPS:
            raise StudyError('MFG_TOL term must have nominal 0: ' + t.name)


def zero_value(func, base, t):
    def g(v):
        d = dict(base)
        d[t.name] = v
        return func(d)
    x0 = t.adv
    f0 = g(x0)
    span = abs(t.adv - t.nom) or 0.01
    direction = (1.0 if t.nom > t.adv else -1.0) * (1.0 if f0 < 0 else -1.0)
    x1 = x0
    for _ in range(40):
        x1 = x1 + direction * span
        f1 = g(x1)
        if (f1 >= 0) != (f0 >= 0):
            break
        span *= 2.0
    else:
        return None
    lo, hi, flo = x0, x1, f0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        fm = g(mid)
        if (fm >= 0) == (flo >= 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2.0


SWEEP_MODE = False


def run_check(spec, full=True):
    """Evaluate one check spec: dict(id, hard, limit_class, required, definition, terms, func, legacy,
    owner_gated). full=False returns the linear-worst margin only (search mode)."""
    terms, func = spec['terms'], spec['func']
    if spec['id'].startswith('H21-BORE-') and 'c_switch_mm' not in {t.name for t in terms}:
        raise StudyError('button bore omits authored switch overhang/travel')
    nomv = {t.name: t.nom for t in terms}
    varying = [t for t in terms if t.role in ('MFG_TOL', 'SUPPLIER_GATED') and abs(t.adv - t.nom) > EPS]
    lw = dict(nomv)
    lw.update({t.name: t.adv for t in varying})
    m_lw = func(lw)
    if not full:
        return m_lw
    validate_terms(terms)
    m_nom = func(nomv)
    sens = []
    for t in varying:
        v = dict(nomv)
        v[t.name] = t.adv
        d = func(v) - m_nom
        if d > 1e-7:
            raise StudyError('%s: term %s is not at its adverse limit' % (spec['id'], t.name))
        sens.append((t, d))
    m_rss = m_nom - math.sqrt(sum(d * d for _, d in sens))
    gov = sorted(sens, key=lambda e: (e[1], e[0].name))
    req = spec.get('required', 'linear worst')
    ok = (m_lw >= -1e-9) if req in ('linear worst', 'G1 conservative') else (m_nom >= -1e-9 and m_rss >= -1e-9)
    return dict(id=spec['id'], hard=spec['hard'], limit_class=spec['limit_class'], required_evaluation=req,
                definition=spec['definition'], legacy=spec.get('legacy'), nominal=m_nom, rss=m_rss,
                linear_worst=m_lw, pass_=ok,
                governing=[dict(t.row(), margin_change=d) for t, d in gov[:6]],
                supplier_zero_margin=[dict(term=t.name, value=zero_value(func, lw, t)) for t, d in gov
                                      if t.role == 'SUPPLIER_GATED' and t.name != 'tol_cs' and not SWEEP_MODE],
                design_terms={t.name: t.nom for t in terms if t.role == 'DESIGN'},
                owner_gated=spec.get('owner_gated', []))


def fix_pass(row):
    row['pass'] = row.pop('pass_')
    return row


# --------------------------------------------------------------------------------------------
# Study: carry-ins
# --------------------------------------------------------------------------------------------
class Study:
    def __init__(self, inp=None, verify=True):
        self.I = copy.deepcopy(inp) if inp is not None else load(IN_PATH)
        self.pin_report = self.verify_pins() if verify else []
        self.S = load(MECH / 'inputs/stack_parameters.json')
        self.G1in = load(MECH / 'inputs/g1_scenarios.json')
        self.G1 = load(GEN / 'g1_scenarios.json')
        self.G2in = load(MECH / 'inputs/g2_interconnect.json')
        self.G2 = load(GEN / 'g2_interconnect.json')
        self.HM = load(GEN / 'main_height_map.json')
        self.ZS = load(GEN / 'zstack.json')
        self.A = load(MECH / 'architecture.json')
        g3 = load(GEN / 'g3_rear_optical.json')
        cv = self.I['contract_values']
        self.s14 = next(c for c in g3['g4_handoff']['candidates'] if c['candidate'] == cv['s14']['candidate'])
        self.s14_cand = next(c for c in g3['candidates'] if c['id'] == cv['s14']['candidate'])
        self.g3_verdict = g3['verdict']
        self.g3_conflicts = {c['id']: c for c in g3['conflict_status']}
        self.g3_gates = g3['g4_handoff']['open_gates']
        del g3
        self.res = {r['id']: r for r in self.A['reservations']}
        self.g2res = {r['id']: r for r in self.G2['reservations']}
        self.P = self.I['parameters']
        self.rp = self.S['radial']['parameters']
        self.sp = self.S['parameters']
        self.R_main = self.rp['R_main']['nom']
        self.R_display = self.HM['summary']['H_F_under_display']['radius_limit_mm']
        self.R_pol = self.A['geometry']['R_pol_mm']
        self.u703 = next((f['x'], f['y']) for f in self.HM['main_footprints'] if f['ref'] == 'U703')
        self.tolpol = {t['param']: t['delta_mm'] for t in self.G1in['tolerance_policy']['g1_added_terms']}
        self.legacy = self.legacy_reproduction()
        self.z = self.z_baselines()
        self.s14geo = self.s14_geometry()

    # ---- pins -------------------------------------------------------------------------------
    def verify_pins(self):
        rep = []
        for rel, want in sorted(self.I['source_sha256'].items()):
            got = sha_file(ROOT / rel)
            rep.append(dict(path=rel, sha256=got, pinned=want, match=got == want))
        a = load(MECH / 'architecture.json')
        proj = {'reservations': a['reservations'], 'rear_module': a['rear_module'],
                'g2.reservations': a['g2']['reservations'], 'edge_crossings': a['edge_crossings']}
        got = chash(proj)
        rep.append(dict(path='design/mechanical/architecture.json#projection', sha256=got,
                        pinned=self.I['architecture_projection']['sha256'],
                        match=got == self.I['architecture_projection']['sha256']))
        bad = [r['path'] for r in rep if not r['match']]
        if bad:
            raise StudyError('STOP: source-hash mismatch: ' + ', '.join(bad))
        return rep

    # ---- H04 legacy reproduction through imported G1 / G2-era functions ----------------------
    def legacy_reproduction(self):
        radial = mm.build_radial(self.S, self.sp)['corners']
        det = g1.deterministic_checks(self.G1in, self.S, self.A, self.ZS)
        ec = ad.derive_edge_crossings(self.A, self.ZS, self.HM)
        corners = ('nominal', 'conservative', 'optimistic')
        got = {
            'conservative_radial_margin_mm': radial['conservative']['checks']['margin_straight_run']['value_mm'],
            'x25_conservative_cover_fit_mm': det['cover_rim']['conservative']['fit_margin_mm'],
            'x25_nominal_fit_mm': det['cover_rim']['nominal']['fit_margin_mm'],
            'x25_nominal_bezel_wall_margin_mm': det['cover_rim']['nominal']['wall_margin_mm'],
            't_bezel_min_nominal_mm': det['cover_rim']['nominal']['t_bezel_min_mm'],
            'edge_margin_at_land_ceiling_mm': {c: ec['budget'][c]['margin_at_h_max_mm'] for c in corners},
            'edge_margin_flat_exit_mm': {c: ec['budget'][c]['margin_flat_exit_mm'] for c in corners},
            't_allow_straight_mm': {c: ec['budget'][c]['t_allow_straight_mm'] for c in corners},
            'lower_web_margin_mm': {c: ec['budget'][c]['lower_web_margin_mm'] for c in corners},
            'u4_land_headroom_mm': {c: ec['land_vs_rim_parts'][c]['margin_mm'] for c in corners},
        }
        rows = []
        for k, want in sorted(self.I['contract_values']['legacy'].items()):
            have = got[k]
            if isinstance(want, dict):
                ok = all(abs(round(have[c], 3) - want[c]) < 5e-4 for c in want)
            else:
                ok = abs(round(have, 3) - want) < 5e-4
            rows.append(dict(id=k, expected=want, reproduced=have, match=ok))
        extra = dict(
            straight_run_mm={c: radial[c]['checks']['margin_straight_run']['value_mm'] for c in corners},
            main_to_case_mm={c: radial[c]['checks']['margin_main_to_case']['value_mm'] for c in corners},
            R_case_inner_mm={c: radial[c]['checks']['R_case_inner']['value_mm'] for c in corners},
            cover_rim=det['cover_rim'], rear_seal_band=det['rear_seal_band'],
            window_plate_unsupported_radius_mm=det['window_plate']['unsupported_radius_mm'],
            edge_budget=ec['budget'], land_vs_rim_parts=ec['land_vs_rim_parts'],
            crossing_parts=ec['crossings'])
        return dict(rows=rows, pass_=all(r['match'] for r in rows), detail=extra,
                    method='mech_model.build_radial, g1_scenarios.deterministic_checks and '
                           'arch_diagrams.derive_edge_crossings imported unchanged; numbers never re-typed')

    # ---- H01 / H02 Z baselines through the imported G2 stack and tolerance policy -------------
    def z_baselines(self):
        st = g2.Study()
        alloc = self.G2['allocation']
        out = {}
        for sid, high in (('G2-REVA', False), ('G2-REVA-HI', True)):
            s = st.stack(alloc, high=high)
            gen = next(x for x in self.G2['stacks'] if x['id'] == sid)
            want = self.I['contract_values']['g2_stacks_mm'][sid]
            have = dict(nominal=g2.r(s['nominal_mm']), rss=g2.r(s['rss_mm']), linear=g2.r(s['linear_mm']))
            out[sid] = dict(reproduced=have, expected=want, generated=dict(nominal=gen['nominal_mm'], rss=gen['rss_mm'],
                                                                         linear=gen['linear_mm']),
                            match=all(abs(have[k] - want[k]) < 5e-4 and abs(gen[k + ('_mm')] - want[k]) < 5e-4
                                      for k in ('nominal', 'rss', 'linear')),
                            layers={l['id']: l['thickness_mm'] for l in s['layers']},
                            sensitivities=s['tolerance_sensitivities_mm'])
        return out

    def layer(self, lid, baseline='G2-REVA'):
        return self.z[baseline]['layers'][lid]

    def rear_alloc_min(self):
        """Allocated Z from the lower-web underside to the window outer plane (both baselines; min)."""
        return min(sum(self.z[b]['layers'][k] for k in ('rear_inner', 'rear_pcb', 'optics_zone', 'window'))
                   for b in self.z)

    # ---- G3-B-S14 carry-in geometry (pinned, never re-derived) ---------------------------------
    def s14_geometry(self):
        h = self.s14
        cv = self.I['contract_values']['s14']
        out = h['outline']['assembly_mm']
        radii = [math.hypot(x - 100, y - 100) for x, y in out]
        frames = []
        for name, obj in (('outline', h['outline']), ('pod', h['pod']), ('u6_island', h['u6']['island']),
                          ('tail_thermode', h['tail_exit']['thermode_keepout'])) + tuple(
                ('support_%d' % s['azimuth_deg'], s['polygon']) for s in h['supports']):
            frames.append(dict(name=name, valid=frame_ok(obj)))
        pod = [tuple(p) for p in h['pod']['assembly_mm']]
        cons = h['tail_exit']['corners']['conservative']
        geo = dict(
            outline_r=max(radii), outline_r_min=min(radii), pod=pod, pod_area=poly_area(pod),
            pod_r_min=min(pt_region((100.0, 100.0), dict(type='poly', pts=pod)) or
                          min(seg_dist((100.0, 100.0), a, b) for a, b in zip(pod, pod[1:] + pod[:1])), 99.0),
            pod_r_max=max(math.hypot(x - 100, y - 100) for x, y in pod),
            supports=[dict(az=s['azimuth_deg'], centre=tuple(s['centre_assembly_mm']),
                           poly=[tuple(p) for p in s['polygon']['assembly_mm']]) for s in h['supports']],
            u6_island=[tuple(p) for p in h['u6']['island']['assembly_mm']],
            tail_cons=[tuple(p) for p in cons['geometry']['assembly_mm']],
            tail_relief_cons=[tuple(p) for p in cons['strain_relief']['assembly_mm']],
            tail_relief_nom=[tuple(p) for p in h['tail_exit']['strain_relief']['assembly_mm']],
            thermode=[tuple(p) for p in h['tail_exit']['thermode_keepout']['assembly_mm']],
            pod_section=h['pod_section'], window_variants=h['window_variants'], seal_land=h['seal_land_mm'],
            clearances={k: v['plan_gap_mm'] for k, v in h['clearances'].items()},
            overlaps={k: v['overlap_area_mm2'] for k, v in h['clearances'].items()},
            u6_chg=h['u6']['charger_plan_gaps_mm']['CHG_CONTACT'], frames=frames,
            tail_id=h['tail_exit']['id'], released=h['released'],
            cells={k: [tuple(p) for p in v['assembly_mm']]
                   for k, v in self.s14_cand['corners']['nominal']['optical']['physical_cells'].items()})
        geo['pod_r_min'] = min(seg_dist((100.0, 100.0), a, b) for a, b in zip(pod, pod[1:] + pod[:1]))
        checks = [
            ('released', geo['released'] is True),
            ('outline_radius', abs(geo['outline_r'] - cv['outline_radius_mm']) < 2e-3 and abs(geo['outline_r_min'] - cv['outline_radius_mm']) < 2e-3),
            ('pod_area', abs(h['pod_area_mm2'] - cv['pod_area_mm2']) < 5e-4),
            ('pod_depth', all(abs(h['pod_section']['corners'][c]['pod_depth_mm'] - v) < 5e-4 for c, v in cv['pod_depth_mm'].items())),
            ('caseback_residual', all(abs(h['pod_section']['corners'][c]['caseback_residual_before_wall_mm'] - v) < 5e-4
                                      for c, v in cv['caseback_residual_before_wall_mm'].items())),
            ('supports', sorted(s['azimuth_deg'] for s in h['supports']) == sorted(cv['support_azimuths_deg'])),
            ('tail_exit', h['tail_exit']['id'] == cv['tail_exit_id']),
            ('tail_widths', abs(h['tail_exit']['corners']['nominal']['land_width_mm'] - cv['tail_land_nominal_mm'][0]) < 5e-4
             and abs(cons['exit_width_mm'] - cv['tail_conservative_width_mm']) < 5e-4),
            ('u6', h['u6']['azimuth_deg'] == cv['u6_azimuth_deg'] and h['u6']['radius_mm'] == cv['u6_radius_mm']),
            ('seal_land', all(abs(h['seal_land_mm'][k] - v) < 5e-4 for k, v in cv['seal_land_mm'].items())),
            ('plan_clearances', all(abs(geo['clearances'][k] - v) < 5e-4 for k, v in cv['plan_clearances_mm'].items())),
            ('u6_to_chg', abs(geo['u6_chg'] - cv['u6_to_chg_contact_mm']) < 5e-4),
            ('outline_overlaps', all(abs(geo['overlaps'][k] - v) < 5e-4 for k, v in cv['outline_overlaps_mm2'].items())),
            ('frames', all(f['valid'] for f in frames)),
        ]
        geo['carry_in_checks'] = [dict(id=k, pass_=v) for k, v in checks]
        return geo


def frame_ok(obj):
    """REAR board-to-assembly transform: assembly = (100 - x_rear, 100 + y_rear) for every vertex."""
    return all(abs(a[0] - (100 - r[0])) < 2e-3 and abs(a[1] - (100 + r[1])) < 2e-3
               for a, r in zip(obj['assembly_mm'], obj['rear_mm'])) and len(obj['assembly_mm']) == len(obj['rear_mm'])


# --------------------------------------------------------------------------------------------
# Check specifications (one per closure metric). Each returns dict(id, hard, limit_class, required,
# definition, terms, func, legacy). Terms carry their role; adverse values are per check.
# --------------------------------------------------------------------------------------------
EVMAP = {'KNOWN': 'MANUFACTURER_VERIFIED', 'PARAMETRIC': 'PROVISIONAL_ASSUMPTION',
         'SUPPLIER_DATA_REQUIRED': 'SUPPLIER_DATA_REQUIRED'}


def spec(sid, hard, definition, terms, func, legacy=None, limit_class=None, required=None, owner_gated=None):
    # Section 6.3: every radial / collision / insertion / seal / land / plate / Z-budget spec passes at LINEAR WORST
    # (plate screens: the linear-worst set equals the G1 conservative sizing case p max, E min, sigma_allow min).
    return dict(id=sid, hard=hard, definition=definition, terms=terms, func=func, legacy=legacy,
                limit_class=limit_class or HARD[hard][2], required=required or 'linear worst',
                owner_gated=owner_gated or [])


class Specs:
    """Spec builders bound to a Study and a candidate."""

    def __init__(self, st, cand):
        self.st, self.c = st, cand
        I = st.I
        self.pc_mid = I['process_classes'][cand['midcase']['process']]
        self.pc_env = dict(self.pc_mid)
        if cand.get('dielectric_sectors'):
            local=I['process_classes'][cand['dielectric_sector_process']]
            for key in ('radius_mm','od_radius_mm','thickness_mm'):
                self.pc_env[key]=max(self.pc_mid[key],local[key])
        self.pc_cb = I['process_classes'][cand['caseback']['process']]
        self.pc_car = I['process_classes']['PC-CARRIER-MOULD']
        self.pc_cov = I['process_classes']['PC-COVER-GRIND']
        self.pc_pcb = I['process_classes']['PC-PCB-ROUT']
        self.m_mid = I['material_classes'][cand['midcase']['material']]
        self.m_cb = I['material_classes'][cand['caseback']['material']]
        self.P = I['parameters']

    def button_process(self, sw):
        if sw == 'SW5' and self.c.get('dielectric_sectors'):
            return self.st.I['process_classes'][self.c['dielectric_sector_process']]
        return self.pc_mid

    def local_wall(self, dp):
        if not self.c.get('dielectric_sectors'):
            return self.wall(dp, dp['tw'])
        local = copy.copy(self)
        local.pc_mid = self.st.I['process_classes'][self.c['dielectric_sector_process']]
        local.m_mid = self.st.I['material_classes'][self.c['dielectric_sector_material']]
        return local.wall(dp, dp['tw'], 'H05-WALL-DIELECTRIC')

    def carrier_wall(self, dp):
        return spec('H10-CARRIER-WALL', 'H10', 'carrier wall at adverse process corner >= binding 0.30 mm minimum',
                    [self.design('t_carrier_wall', dp['tcw']), self.tol('tol_carrier_wall', self.pc_car['thickness_mm'])],
                    lambda v: v['t_carrier_wall'] - v['tol_carrier_wall'] - 0.30,
                    limit_class='PROJECT-DERIVED LIMIT')

    # -- term helpers ------------------------------------------------------------------------
    def radial(self, name, adverse):
        p = self.st.rp[name]
        return Term(name, 'SUPPLIER_GATED', EVMAP[p['class']], p['nom'], p[adverse], (p['min'], p['max']))

    def par(self, name, adverse, d=None):
        p = d if d is not None else self.P[name]
        return Term(name, 'SUPPLIER_GATED', p.get('evidence_class', 'PROVISIONAL_ASSUMPTION'), p['nom'], p[adverse],
                    (p['min'], p['max']))

    def tol(self, name, value, sign=1.0):
        return Term(name, 'MFG_TOL', 'PROVISIONAL_ASSUMPTION', 0.0, sign * value)

    @staticmethod
    def design(name, value, ev='PROJECT_DERIVED'):
        return Term(name, 'DESIGN', ev, value)

    @staticmethod
    def frozen(name, value, ev='PROJECT_DERIVED'):
        return Term(name, 'FROZEN', ev, value)

    # -- H03 body diameter and wall ------------------------------------------------------------
    def od(self, dp):
        return spec('H03-OD', 'H03', 'OWNER ceiling: 51.00 - (D_case_body + 2 x OD radius tolerance) >= 0',
                    [self.design('D', dp['D']), self.tol('tol_od_r', self.pc_env['od_radius_mm'])],
                    lambda v: 51.0 - (v['D'] + 2 * v['tol_od_r']))

    def wall(self, dp, tw, sid='H05-WALL-SIDE'):
        m = self.m_mid['t_wall_min_mm']
        return spec(sid, 'H05', 'side wall (OD - bore) - t_wall_min(material class) >= 0',
                    [self.design('t_wall', tw), self.tol('tol_od_r', self.pc_mid['od_radius_mm']),
                     self.tol('tol_bore_r', self.pc_mid['radius_mm']),
                     Term('t_wall_min', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', m['nom'], m['max'], (m['min'], m['max']))],
                    lambda v: v['t_wall'] - v['tol_od_r'] - v['tol_bore_r'] - v['t_wall_min'],
                    limit_class='PROVISIONAL PLANNING LIMIT')

    # -- H10 pack radial ---------------------------------------------------------------------
    def pack(self, dp):
        return spec('H10-PACK-RADIAL', 'H10', 'carrier inner radius - tol - (pack max radius + radial growth) >= 0; no growth credit',
                    [self.design('R_carrier_inner', dp['rcin']), self.tol('tol_carrier_r', self.pc_car['radius_mm']),
                     self.frozen('D_pack_nom', self.st.rp['D_pack_nom']['nom'], 'MANUFACTURER_VERIFIED'),
                     self.radial('tol_pack_dia', 'max'), self.par('g_radial_mm', 'max')],
                    lambda v: v['R_carrier_inner'] - v['tol_carrier_r'] - ((v['D_pack_nom'] + v['tol_pack_dia']) / 2 + v['g_radial_mm']))

    def _channel_terms(self, dp):
        return [self.design('R_side', dp['D'] / 2 - dp['tw']), self.tol('tol_bore_r', self.pc_env['radius_mm']),
                self.design('R_carrier_inner', dp['rcin']), self.tol('tol_carrier_r', self.pc_car['radius_mm']),
                self.design('t_carrier_wall', dp['tcw']), self.tol('tol_carrier_wall', self.pc_car['thickness_mm']),
                self.radial('t_fpc', 'max'), self.radial('c_fpc', 'max')]

    @staticmethod
    def _rch(v):
        return v['R_carrier_inner'] + v['tol_carrier_r'] + v['t_carrier_wall'] + v['tol_carrier_wall']

    # -- H05 radial channel / edge crossings ---------------------------------------------------
    def straight(self, dp):
        L = self.st.legacy['detail']['straight_run_mm']
        return spec('H05-STRAIGHT', 'H05', 'margin_straight_run at every riser azimuth: bore - (R_channel_inner + t_fpc + c_fpc)',
                    self._channel_terms(dp),
                    lambda v: v['R_side'] - v['tol_bore_r'] - (self._rch(v) + v['t_fpc'] + v['c_fpc']),
                    legacy=dict(L))

    def edge(self, dp, xid):
        h_parts = self.st.legacy['detail']['crossing_parts'].get(xid, {}).get('nominal', {}).get('h_parts_mm', self.st.layer('front_gap') if xid=='XL-LRA' else 0.0)
        ex = self.st.G2in['parameters']['exit_mm']
        L = self.st.legacy['detail']['edge_budget']
        terms = self._channel_terms(dp) + [
            self.frozen('R_main', self.st.R_main, 'MANUFACTURER_VERIFIED'), self.tol('tol_pcb_outline', self.pc_pcb['radius_mm']),
            self.radial('R_bend_min', 'max'),
            Term('h_exit', 'SUPPLIER_GATED', 'SUPPLIER_DATA_REQUIRED', ex['nom'], ex['min'], (ex['min'], ex['max'])),
            self.frozen('h_approach_parts', h_parts)]

        def f(v):
            run = max(v['h_exit'], v['h_approach_parts'] + v['c_fpc'])
            rv = max(v['R_main'] + v['tol_pcb_outline'] + v['R_bend_min'] - ad._bend_inset(v['R_bend_min'], run), self._rch(v))
            return v['R_side'] - v['tol_bore_r'] - (rv + v['t_fpc'] + v['c_fpc'])
        return spec('H05-EDGE-' + xid, 'H05',
                    '%s F.Cu edge crossing at the G2 supplier exit-height range (bend inset model imported from arch_diagrams)' % xid,
                    terms, f, legacy=dict(land_ceiling={c: L[c]['margin_at_h_max_mm'] for c in L},
                                          flat_exit={c: L[c]['margin_flat_exit_mm'] for c in L}))

    def edge_bound(self, dp, kind):
        """Reported bounds of the G1 model with G4 dimensions: flat exit (h=0) and land-ceiling exit."""
        terms = self._channel_terms(dp) + [self.frozen('R_main', self.st.R_main, 'MANUFACTURER_VERIFIED'),
                                           self.tol('tol_pcb_outline', self.pc_pcb['radius_mm']), self.radial('R_bend_min', 'max'),
                                           self.frozen('front_gap', self.st.layer('front_gap')),
                                           self.design('t_land', dp['t_land']), self.tol('tol_t_land', self.pc_mid['thickness_mm']),
                                           self.tol('tol_z_land', self.pc_mid['thickness_mm'])]

        def f(v):
            if kind == 'flat':
                run = 0.0
            else:
                run = max(0.0, v['front_gap'] - v['t_land'] - v['tol_t_land'] - v['tol_z_land'] - v['c_fpc'] - v['t_fpc'])
            rv = max(v['R_main'] + v['tol_pcb_outline'] + v['R_bend_min'] - ad._bend_inset(v['R_bend_min'], run), self._rch(v))
            return v['R_side'] - v['tol_bore_r'] - (rv + v['t_fpc'] + v['c_fpc'])
        L = self.st.legacy['detail']['edge_budget']
        key = 'margin_flat_exit_mm' if kind == 'flat' else 'margin_at_h_max_mm'
        return spec('INFO-EDGE-' + kind.upper(), 'H05', 'G1 edge-crossing bound with G4 dimensions (%s exit); reported, '
                    'the supplier exit height decides the actual margin' % ('flat' if kind == 'flat' else 'land-ceiling'),
                    terms, f, legacy={c: L[c][key] for c in L})

    def edge_z(self, dp, xid):
        h_parts = self.st.legacy['detail']['crossing_parts'].get(xid, {}).get('nominal', {}).get('h_parts_mm', self.st.layer('front_gap') if xid=='XL-LRA' else 0.0)
        ex = self.st.G2in['parameters']['exit_mm']
        terms = [self.frozen('front_gap', self.st.layer('front_gap')), self.design('t_land', dp['t_land']),
                 self.tol('tol_t_land', self.pc_mid['thickness_mm']), self.tol('tol_z_land', self.pc_mid['thickness_mm']),
                 self.radial('t_fpc', 'max'), self.radial('c_fpc', 'max'),
                 Term('h_exit', 'SUPPLIER_GATED', 'SUPPLIER_DATA_REQUIRED', ex['nom'], ex['max'], (ex['min'], ex['max'])),
                 self.frozen('h_approach_parts', h_parts)]
        return spec('H05-EDGE-Z-' + xid, 'H05', '%s run height under the display land ceiling: h_max - max(exit, parts + c) >= 0' % xid,
                    terms, lambda v: (v['front_gap'] - v['t_land'] - v['tol_t_land'] - v['tol_z_land'] - v['c_fpc'] - v['t_fpc'])
                    - max(v['h_exit'], v['h_approach_parts'] + v['c_fpc']))

    def t_allow(self, dp):
        L = self.st.legacy['detail']['edge_budget']
        terms = self._channel_terms(dp)
        return spec('H05-T-ALLOW-XC', 'H05', 'charger riser t_allow_straight - conductor thickness (flat-flex stand-in) >= 0',
                    terms, lambda v: (v['R_side'] - v['tol_bore_r'] - v['c_fpc'] - self._rch(v)) - v['t_fpc'],
                    legacy={c: L[c]['t_allow_straight_mm'] for c in L})

    def main_case(self, dp):
        return spec('H05-MAIN-CASE', 'H05', 'MAIN-to-case clearance: bore - (R_main + PCB outline tol + c_main_case) >= 0',
                    [self.design('R_side', dp['D'] / 2 - dp['tw']), self.tol('tol_bore_r', self.pc_env['radius_mm']),
                     self.frozen('R_main', self.st.R_main, 'MANUFACTURER_VERIFIED'), self.tol('tol_pcb_outline', self.pc_pcb['radius_mm']),
                     self.par('c_main_case_mm', 'max')],
                    lambda v: v['R_side'] - v['tol_bore_r'] - (v['R_main'] + v['tol_pcb_outline'] + v['c_main_case_mm']),
                    legacy=dict(self.st.legacy['detail']['main_to_case_mm']))

    # -- H23 insertion envelopes ---------------------------------------------------------------
    def insert(self, dp, level, r_rear=None):
        base = [self.design('R_side', dp['D'] / 2 - dp['tw']), self.tol('tol_bore_r', self.pc_env['radius_mm']),
                self.par('c_insert_mm', 'max')]
        if level == 'MAIN':
            terms = base + [self.frozen('R_main', self.st.R_main, 'MANUFACTURER_VERIFIED'),
                            self.tol('tol_pcb_outline', self.pc_pcb['radius_mm'])]
            return spec('H23-INSERT-MAIN', 'H23', 'rear insertion at MAIN level: bore - (MAIN outline + tol + c_insert) >= 0',
                        terms, lambda v: v['R_side'] - v['tol_bore_r'] - (v['R_main'] + v['tol_pcb_outline'] + v['c_insert_mm']))
        if level == 'BATTERY':
            terms = base + [t for t in self._channel_terms(dp) if t.name not in ('R_side', 'tol_bore_r', 'c_fpc')]
            return spec('H23-INSERT-BATTERY', 'H23', 'rear insertion at BATTERY level (risers attached): bore - (R_channel_inner + t_fpc + c_insert) >= 0',
                        terms, lambda v: v['R_side'] - v['tol_bore_r'] - (self._rch(v) + v['t_fpc'] + v['c_insert_mm']))
        terms = base + [self.frozen('r_rear_module', r_rear)]
        return spec('H23-INSERT-REAR', 'H23', 'rear insertion at REAR level: bore - (max REAR-level module radius incl. module-carried charger block + c_insert) >= 0',
                    terms, lambda v: v['R_side'] - v['tol_bore_r'] - (v['r_rear_module'] + v['c_insert_mm']))

    # -- H06 / H07 cover ---------------------------------------------------------------------------
    def cover_fit(self, dp):
        pc = self.st.G1in['plate_check']
        w, tb = pc['w_cover_land_mm'], pc['t_bezel_min_mm']
        L = self.st.legacy['detail']['cover_rim']
        terms = [self.design('D', dp['D']), self.tol('tol_od_r', self.pc_env['od_radius_mm']),
                 self.design('a_cover', dp['a_cover']), self.tol('tol_ledge_r', self.pc_env['radius_mm']),
                 Term('w_cover_land', 'SUPPLIER_GATED', 'SUPPLIER_DATA_REQUIRED', w['nom'], w['max'], (w['min'], w['max'])),
                 self.tol('tol_cover_r', self.pc_cov['radius_mm']), self.par('c_cover_recess_mm', 'max'),
                 Term('t_bezel_min', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', tb['nom'], tb['max'], (tb['min'], tb['max']))]
        return spec('H06-X25-BEZEL', 'H06', 'X25 under OD-G4-CORNER: (R_body - tol) - (a_cover + tol + w_cover_land + cover tol + recess gap) - t_bezel_min >= 0',
                    terms, lambda v: (v['D'] / 2 - v['tol_od_r']) - (v['a_cover'] + v['tol_ledge_r'] + v['w_cover_land'] + v['tol_cover_r']
                                                                      + v['c_cover_recess_mm']) - v['t_bezel_min'],
                    legacy=dict(fit_conservative=L['conservative']['fit_margin_mm'], fit_nominal=L['nominal']['fit_margin_mm'],
                                bezel_wall_nominal=L['nominal']['wall_margin_mm'], bezel_wall_conservative=L['conservative']['wall_margin_mm']))

    def cover_ledge(self, dp):
        return spec('H06-DISPLAY-LEDGE', 'H06', 'cover ledge inner edge clears the display: (a_cover - tol) - (R_display + c_display_ledge) >= 0',
                    [self.design('a_cover', dp['a_cover']), self.tol('tol_ledge_r', -self.pc_env['radius_mm']),
                     self.frozen('R_display', self.st.R_display, 'MANUFACTURER_VERIFIED'), self.par('c_display_ledge_mm', 'max')],
                    lambda v: v['a_cover'] + v['tol_ledge_r'] - (v['R_display'] + v['c_display_ledge_mm']))

    def cover_plate(self, dp):
        """H07: imported G1 plate sizing at the designed a_cover (+tol at the conservative corner)."""
        G = self.st.G1in
        mat = next(o['material'] for o in G['cover_options'] if o['id'] == G['baseline_cover_option'])
        rnd = G['plate_check']['rounding_mm']
        cn = g1.corner_of(G, mat, 'nominal')
        cc = g1.corner_of(G, mat, 'conservative')
        cn['a_cover_mm'] = dp['a_cover']
        cc['a_cover_mm'] = dp['a_cover'] + self.pc_env['radius_mm']
        t_nom = g1.size_cover(mat, cn, 'ss', rnd)
        t_cons = g1.size_cover(mat, cc, 'ss', rnd)
        tc = self.st.sp['t_cover']
        w_nom, _ = g1.plate(mat, cn['p_test_MPa'], cn['a_cover_mm'], cn['nu'], cn['E_MPa'], tc['nom'], 'ss')
        w_con, s_con = g1.plate(mat, cc['p_test_MPa'], cc['a_cover_mm'], cc['nu'], cc['E_MPa'], tc['max'], 'ss')
        gap = self.st.sp['t_cover_bond']
        c_gap = G['plate_check']['c_gap_mm']
        rows = dict(material=mat, a_cover_nominal_mm=cn['a_cover_mm'], a_cover_conservative_mm=cc['a_cover_mm'],
                    t_required_nominal_mm=t_nom, t_required_conservative_mm=t_cons, t_cover_stack_mm=dict(nom=tc['nom'], max=tc['max']),
                    sizing_margin_nominal_mm=tc['nom'] - t_nom, sizing_margin_conservative_mm=tc['max'] - t_cons,
                    sigma_conservative_MPa=s_con, sigma_allow_min_MPa=cc['sigma_allow_MPa'],
                    w_nominal_mm=w_nom, w_conservative_mm=w_con,
                    air_gap_margin_nominal_mm=gap['nom'] - (w_nom + c_gap), air_gap_margin_conservative_mm=gap['max'] - (w_con + c_gap),
                    method='g1_scenarios.size_cover / plate imported; stack t_cover 1.00 / 1.25 / 1.70 kept; thinner sizing is a Rev-B lever, never credited')
        rows['pass'] = (rows['sizing_margin_nominal_mm'] >= -EPS and rows['sizing_margin_conservative_mm'] >= -EPS
                        and rows['air_gap_margin_nominal_mm'] >= -EPS and rows['air_gap_margin_conservative_mm'] >= -EPS)
        return rows

    # -- H09 display land / U4 -----------------------------------------------------------------
    def u4(self, dp):
        r_in = self.st.R_display - dp['w_land'] - self.pc_mid['radius_mm']
        parts = ad._rim_parts(self.st.HM, None, r_in, ad.R_CLIP)
        top = parts[0]
        L = self.st.legacy['detail']['land_vs_rim_parts']
        return spec('H09-U4-HEADROOM', 'H09', 'land underside clears the tallest rim part (%s): front gap - t_land - tols - h_rim - c_front >= 0' % top[1],
                    [self.frozen('front_gap', self.st.layer('front_gap')), self.design('t_land', dp['t_land']),
                     self.tol('tol_t_land', self.pc_mid['thickness_mm']), self.tol('tol_z_land', self.pc_mid['thickness_mm']),
                     self.frozen('h_rim', top[0]), self.frozen('c_front', self.st.sp['c_front']['nom'])],
                    lambda v: v['front_gap'] - v['t_land'] - v['tol_t_land'] - v['tol_z_land'] - v['h_rim'] - v['c_front'],
                    legacy={c: L[c]['margin_mm'] for c in L})

    # -- H11 caseback / pod ---------------------------------------------------------------------
    def pod_residual(self, dp):
        L = self.st.s14geo['pod_section']['corners']
        return spec('H11-POD-RESIDUAL', 'H11', 'h_pod_max = pod depth (frame alloc + window) - (t_caseback_in + tol) - c_cb_rear >= 0',
                    [self.frozen('optics_zone_alloc', self.st.layer('optics_zone')), self.tol('tol_frame_h', -self.pc_cb['thickness_mm']),
                     self.design('t_window', dp['t_w']),
                     Term('tol_t_window', 'SUPPLIER_GATED', 'PROJECT_DERIVED', 0.0, -self.st.tolpol['t_window'],
                          (-self.st.tolpol['t_window'], self.st.tolpol['t_window'])),
                     self.design('t_cb_in', dp['t_in']), self.tol('tol_t_cb', self.pc_cb['thickness_mm']),
                     self.par('c_cb_rear_mm', 'max')],
                    lambda v: v['optics_zone_alloc'] + v['tol_frame_h'] + v['t_window'] + v['tol_t_window'] - (v['t_cb_in'] + v['tol_t_cb']) - v['c_cb_rear_mm'],
                    legacy={c: L[c]['caseback_residual_before_wall_mm'] for c in L})

    def rear_periphery(self, dp, h_sp):
        return spec('H01-REAR-PERIPHERY-Z', 'H01', 'REAR-level allocation (lower web to pod plane) - h_pod - REAR conductor channel - caseback rim - spigot >= 0 (zero Z delta)',
                    [self.frozen('rear_alloc', self.st.rear_alloc_min()), self.design('h_pod', dp['h_pod']),
                     self.par('c_rear_route_mm', 'max'), self.design('t_cb_out', dp['t_out']),
                     self.tol('tol_t_cb', self.pc_cb['thickness_mm']), self.design('h_spigot', h_sp),
                     self.tol('tol_spigot_h', self.pc_cb['thickness_mm']),
                     Term('tol_lower_web', 'SUPPLIER_GATED', 'PROJECT_DERIVED', 0.0, self.st.tolpol['t_lower_web'],
                          (-self.st.tolpol['t_lower_web'], self.st.tolpol['t_lower_web']))],
                    lambda v: v['rear_alloc'] - v['h_pod'] - v['c_rear_route_mm'] - v['t_cb_out'] - v['tol_t_cb'] - v['h_spigot']
                    - v['tol_spigot_h'] - v['tol_lower_web'], limit_class='PROJECT-DERIVED LIMIT')

    # -- H15 glands -----------------------------------------------------------------------------
    def gland(self, gid, kind, cs, h, g, tol_h, tol_g):
        o = self.P['oring']
        w = o['windows'][kind]
        ct = o['cs_tolerance_mm']
        base = [self.design('cs', cs), self.design('h', h), self.design('g', g)]

        def cst(adv):
            return Term('tol_cs', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', 0.0, ct[adv], (ct['min'], ct['max']))
        s_min = spec(gid + '-COMP-MIN', 'H15', 'compression (d - h)/d - window minimum >= 0',
                     base + [cst('min'), self.tol('tol_h', tol_h)],
                     lambda v: (v['cs'] + v['tol_cs'] - (v['h'] + v['tol_h'])) / (v['cs'] + v['tol_cs']) - w['compression_min'])
        s_max = spec(gid + '-COMP-MAX', 'H15', 'window maximum - compression >= 0 (over-compression)',
                     base + [cst('max'), self.tol('tol_h', -tol_h)],
                     lambda v: w['compression_max'] - (v['cs'] + v['tol_cs'] - (v['h'] + v['tol_h'])) / (v['cs'] + v['tol_cs']))
        s_fill = spec(gid + '-FILL', 'H15', 'fill maximum - (pi/4 d^2) / (g h) >= 0',
                      base + [cst('max'), self.tol('tol_h', -tol_h), self.tol('tol_g', -tol_g)],
                      lambda v: w['fill_max'] - (math.pi / 4 * (v['cs'] + v['tol_cs']) ** 2) / ((v['g'] + v['tol_g']) * (v['h'] + v['tol_h'])))
        for s in (s_min, s_max, s_fill):
            s['units'] = 'ratio'
        return [s_min, s_max, s_fill]

    # -- H21 buttons ----------------------------------------------------------------------------
    def bore(self, dp, sw, boss):
        lb = self.P['buttons']['L_bore_min_mm']
        pc = self.button_process(sw)
        if sw=='SW5' and self.c.get('dielectric_sectors') and pc != self.st.I['process_classes'][self.c['dielectric_sector_process']]:
            raise StudyError('SW5 local polymer process replaced by global metal process')
        return spec('H21-BORE-' + sw, 'H21', '%s bore length (OD + boss - inner bore) - L_bore_min >= 0' % sw,
                    [self.design('D', dp['D']), self.tol('tol_od_r', pc['od_radius_mm']),
                     self.design('boss', boss), self.tol('tol_boss', -pc['boss_mm']),
                     self.frozen('R_main', self.st.R_main, 'MANUFACTURER_VERIFIED'), self.tol('tol_pcb_outline', self.pc_pcb['radius_mm']),
                     self.par('c_main_case_mm', 'max'), self.par('c_switch_mm', 'max', self.P['buttons']['c_switch_mm']), self.tol('tol_bore_r', pc['radius_mm']),
                     Term('L_bore_min', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', lb['nom'], lb['max'], (lb['min'], lb['max']))],
                    lambda v: (v['D'] / 2 - v['tol_od_r'] + v['boss'] + v['tol_boss'])
                    - (v['R_main'] + v['tol_pcb_outline'] + v['c_main_case_mm'] + v['c_switch_mm'] + v['tol_bore_r']) - v['L_bore_min'])

    def boss(self, sw, boss):
        pc = self.button_process(sw)
        return spec('H03-BOSS-' + sw, 'H03', '%s functional boss: 1.0 - (extension + tol) >= 0' % sw,
                    [self.design('boss', boss), self.tol('tol_boss', pc['boss_mm'])],
                    lambda v: self.st.I['contract_values']['owner_limits']['boss_extension_max_mm'] - (v['boss'] + (v['tol_boss'] if v['boss'] > 0 else 0.0)))

    def btn_height(self, dp):
        b = self.P['buttons']['body_height_max_mm']
        return spec('H21-BODY-HEIGHT', 'H21', 'switch-body ceiling under the land (G4) - G2 conservative body acceptance >= 0',
                    [self.frozen('front_gap', self.st.layer('front_gap')), self.design('t_land', dp['t_land']),
                     self.tol('tol_t_land', self.pc_env['thickness_mm']), self.tol('tol_z_land', self.pc_env['thickness_mm']),
                     self.radial('c_fpc', 'max'), self.frozen('body_height_acceptance', b['conservative'])],
                    lambda v: (v['front_gap'] - v['t_land'] - v['tol_t_land'] - v['tol_z_land'] - v['c_fpc']) - v['body_height_acceptance'])

    # -- H14 caseback screws at the lug roots -----------------------------------------------------
    def screw_seat(self, dp, cls):
        sc = self.P['screw_classes'][cls]
        lug = self.P['lugs']
        edge = self.m_mid['screw_edge_min_mm']
        return spec('H14-SCREW-SEAT', 'H14', 'screw seat in the lug-root arm common to the strap range: half arm band - (hole/2 + edge) >= 0',
                    [Term('lug_inner_width', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', lug['inner_width_mm']['nom'], lug['inner_width_mm']['max'],
                          (lug['inner_width_mm']['min'], lug['inner_width_mm']['max'])),
                     Term('lug_arm_width', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', lug['arm_width_mm']['nom'], lug['arm_width_mm']['min'],
                          (lug['arm_width_mm']['min'], lug['arm_width_mm']['max'])),
                     self.frozen('hole_dia', sc['hole_dia_mm'], 'PROVISIONAL_ASSUMPTION'),
                     self.frozen('edge_min', edge if edge is not None else 99.0, 'PROVISIONAL_ASSUMPTION'),
                     self.tol('tol_hole_pos', self.pc_mid['radius_mm'])],
                    lambda v: ((lug['inner_width_mm']['min'] / 2 + v['lug_arm_width']) - v['lug_inner_width'] / 2) / 2
                    - (v['hole_dia'] / 2 + v['edge_min'] + v['tol_hole_pos']), limit_class='PROVISIONAL PLANNING LIMIT',
                    owner_gated=[dict(decision='OD-G4-STRAP', options='lug inner width 20 / 21 / 22 mm, arm width 2.5-3.5 mm, spring bar or quick release',
                                      credited=False, note='evaluated over the whole strap range (adverse); a fixed strap width is not credited')])

    # -- H20 charger window -------------------------------------------------------------------
    def chg_window(self, r_out_design):
        land = self.P['bond_lands']['charger_feedthrough_land_mm']
        r_in = self.st.s14geo['outline_r'] + self.st.I['contract_values']['s14']['plan_clearances_mm']['CHG_CONTACT']
        return spec('H20-CHG-WINDOW', 'H20', 'charger aperture window radial depth after the feedthrough bond land on both sides > 0',
                    [self.frozen('r_in', r_in), self.design('r_out', r_out_design), self.tol('tol_window_r', -self.pc_cb['radius_mm']),
                     Term('feedthrough_land', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', land['nom'], land['max'], (land['min'], land['max']))],
                    lambda v: (v['r_out'] + v['tol_window_r']) - v['r_in'] - 2 * v['feedthrough_land'])

    # -- H16 window bond land -----------------------------------------------------------------------
    def window_land(self):
        sl = self.st.s14geo['seal_land']
        return spec('H16-WINDOW-LAND', 'H16', 'pod-frame window bond land (G1 frame overlap) - tol - seal-land planning maximum (G3) >= 0',
                    [self.frozen('frame_overlap', self.st.G1in['plate_check']['a_window_frame_mm']),
                     self.tol('tol_frame_r', self.pc_cb['radius_mm']),
                     Term('seal_land', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', sl['nom'], sl['max'], (sl['min'], sl['max']))],
                    lambda v: v['frame_overlap'] - v['tol_frame_r'] - v['seal_land'])

    def adhesive_annulus(self, dp):
        bl = self.P['bond_lands']['caseback_bond_land_mm']
        return spec('H16-CB-BOND-LAND', 'H16', 'caseback adhesive ring: midcase rear-face annulus - tols - bond land >= 0',
                    [self.design('t_wall', dp['tw']), self.tol('tol_od_r', self.pc_mid['od_radius_mm']), self.tol('tol_bore_r', self.pc_mid['radius_mm']),
                     Term('bond_land', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', bl['nom'], bl['max'], (bl['min'], bl['max']))],
                    lambda v: v['t_wall'] - v['tol_od_r'] - v['tol_bore_r'] - v['bond_land'])

    # -- H22 LRA Z -----------------------------------------------------------------------------------
    def lra_z(self, cls, t_out, h_pod_local=0.0):
        hgt = cls['height_mm']
        return spec('H22-LRA-Z-' + cls['id'], 'H22', 'REAR-level Z budget (lower web underside to caseback inner face, caseback locally at the pod plane) - (class max height + mount) >= 0',
                    [self.frozen('rear_alloc', self.st.rear_alloc_min()), self.design('h_pod_local', h_pod_local),
                     self.design('t_cb_out', t_out), self.tol('tol_t_cb', self.pc_cb['thickness_mm']),
                     Term('tol_lower_web', 'SUPPLIER_GATED', 'PROJECT_DERIVED', 0.0, self.st.tolpol['t_lower_web'],
                          (-self.st.tolpol['t_lower_web'], self.st.tolpol['t_lower_web'])),
                     self.par('c_lra_top_mm', 'max'), self.par('lra_mount_mm', 'max'),
                     Term('lra_height', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', hgt['nom'], hgt['max'], (hgt['min'], hgt['max']))],
                    lambda v: v['rear_alloc'] - v['h_pod_local'] - v['t_cb_out'] - v['tol_t_cb'] - v['tol_lower_web'] - v['c_lra_top_mm']
                    - v['lra_mount_mm'] - v['lra_height'],
                    owner_gated=[dict(decision='OD-G4-LRA-MAG', options='LRA magnet covered / not covered by the no-magnet invariant', credited=False,
                                      note='MAG_CLEAR stays an exclusion; U703 distance is a ranking metric only'),
                                 dict(decision='OD-G4-STACK', options='nonzero Rev-A Z delta', credited=False, note='not triggered; no Z delta adopted')])


def fast(sp):
    """Search-mode evaluator: the spec's own function on its linear-worst value set."""
    lw = {t.name: t.adv for t in sp['terms']}
    f = sp['func']

    def ev(**upd):
        v = dict(lw)
        v.update(upd)
        return f(v)
    return ev


# --------------------------------------------------------------------------------------------
# Window (H12 / H13 / H16) - imported G1 Kirchhoff method, spans from the S14 pod polygon
# --------------------------------------------------------------------------------------------
def window_study(st):
    G = st.G1in['plate_check']
    pod = st.s14geo['pod']
    r_ins, c_ins = inscribed_circle(pod)
    overlap = G['a_window_frame_mm']
    cells = st.s14geo['cells']
    dims = {k: (max(p[0] for p in v) - min(p[0] for p in v), max(p[1] for p in v) - min(p[1] for p in v)) for k, v in cells.items()}
    big = max(sorted(dims), key=lambda k: (dims[k][0] * dims[k][1], k))
    r_cell = math.hypot(*dims[big]) / 2.0
    spans = {'W0': r_ins - overlap, 'W1': r_cell, 'W2': r_cell}
    standoff = min(c['optical_clearance_mm'] for c in st.s14geo['pod_section']['corners'].values())
    wv = st.s14geo['window_variants']
    rows = []
    for w in ('W0', 'W1', 'W2'):
        for t in st.I['window_variants']['thicknesses_mm']:
            delta = st.s14geo['pod_section']['window_delta_from_g2_nominal_mm']['%g' % t]
            for mat in G['window_materials']:
                m = G['materials'][mat]
                p, nu, E, sa = G['p_test_MPa']['max'], m['nu']['max'], m['E_MPa']['min'], m['sigma_allow_MPa']['min']
                t_min = t - st.tolpol['t_window']
                w_s, s_s = g1.plate(mat, p, spans[w], nu, E, t_min, 'ss')
                w_c, s_c = g1.plate(mat, p, spans[w], nu, E, t_min, 'clamped')
                land_ok = True
                if w == 'W2':
                    land_ok = bool(wv['%g' % t]['W2']['geometric_seal_land_pass'])
                rows.append(dict(id='%s-t%s-%s' % (w, ('%g' % t).replace('.', 'p'), mat), variant=w, t_window_mm=t, material=mat,
                                 minimum_thickness_mm=t_min, thickness_tolerance_mm=st.tolpol['t_window'],
                                 allowable_evidence='PROVISIONAL_ASSUMPTION', supplier_qualified_allowable_MPa=None,
                                 span_radius_mm=spans[w], sigma_ss_MPa=s_s, sigma_clamped_MPa=s_c, sigma_allow_min_MPa=sa,
                                 w_ss_mm=w_s, w_over_t=w_s / t_min, standoff_mm=standoff,
                                 stress_pass=s_s <= sa + 1e-9, deflection_pass=w_s < standoff - 1e-12,
                                 z_delta_mm=max(0.0, delta), credited_gain_mm=0.0, seal_land_pass=land_ok,
                                 screen_pass_without_z_delta=(s_s <= sa + 1e-9 and max(0.0, delta) <= EPS)))
    w0 = [r for r in rows if r['variant'] == 'W0']
    w0_ok = [r for r in w0 if r['screen_pass_without_z_delta']]
    w0_any = [r for r in w0 if r['stress_pass']]
    eligible = [r for r in rows if r['screen_pass_without_z_delta'] and r['deflection_pass'] and r['seal_land_pass']]
    return dict(method='g1_scenarios.plate imported (linear Kirchhoff, circular, simply supported sizing case at p max / E min / nu max / sigma_allow min); '
                       'W0 span = largest inscribed circle of the S14 pod polygon minus the G1 frame overlap; W1/W2 span = circumscribed '
                       'circle of the largest physical optical cell (conservative for rectangles)',
                inscribed_radius_mm=r_ins, inscribed_centre=c_ins, frame_overlap_mm=overlap, largest_cell=big,
                largest_cell_mm=dims[big], spans_mm=spans, standoff_min_mm=standoff, rows=rows,
                w0_status='PASS' if w0_ok else 'MECHANICALLY ELIMINATED',
                w0_with_z_delta=[dict(id=r['id'], z_delta_mm=r['z_delta_mm']) for r in w0_any],
                od_g4_window_triggered=not w0_ok,
                eligible=[r['id'] for r in eligible], h12_pass=any(r['screen_pass_without_z_delta'] for r in rows),
                eligible_t_max=max([r['t_window_mm'] for r in eligible], default=None),
                eligible_variants=sorted({r['variant'] for r in eligible}),
                g1_reproduction=dict(g1_span_nominal_mm=st.legacy['detail']['window_plate_unsupported_radius_mm']['nominal'],
                                     note='G1 used the double-sided REAR envelope radius (10.6 mm nominal); G4 uses the frozen S14 pod polygon'))


# --------------------------------------------------------------------------------------------
# Caseback plate screen (H13) and hard-stop post load (analytical, reported)
# --------------------------------------------------------------------------------------------
def caseback_plate_spec(st, sp, dp, kind):
    G = st.G1in['plate_check']
    m = sp.m_cb
    b = st.s14geo['pod_r_min'] + st.I['parameters']['w_pod_frame_mm']['nom']
    r_step = st.s14geo['outline_r'] + st.I['parameters']['c_hard_stop_mm']['nom']
    terms = [Term('p_test', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', G['p_test_MPa']['nom'], G['p_test_MPa']['max'],
                  (G['p_test_MPa']['min'], G['p_test_MPa']['max'])),
             Term('E', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', m['E_MPa']['nom'], m['E_MPa']['min'], (m['E_MPa']['min'], m['E_MPa']['max'])),
             Term('nu', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', m['nu']['nom'], m['nu']['max' if kind == 'stress' else 'min'],
                  (m['nu']['min'], m['nu']['max'])),
             Specs.design('t_cb_in', dp['t_in']), Specs.design('t_cb_out', dp['t_out']),
             sp.tol('tol_t_cb', -sp.pc_cb['thickness_mm']),
             Specs.design('R_bear', dp['D'] / 2 - dp['tw']), sp.tol('tol_bore_r', sp.pc_env['radius_mm']),
             Specs.frozen('b_frame', b), Specs.frozen('r_step', r_step)]
    if kind == 'stress':
        terms.append(Term('sigma_allow', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', m['sigma_allow_MPa']['nom'], m['sigma_allow_MPa']['min'],
                          (m['sigma_allow_MPa']['min'], m['sigma_allow_MPa']['max'])))
    else:
        c = st.I['parameters']['c_cb_rear_mm']
        terms.append(Term('c_cb_rear', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', c['nom'], c['min'], (c['min'], c['max'])))

    def f(v):
        regs = [(v['b_frame'], v['r_step'], v['t_cb_in'] + v['tol_t_cb'], v['E'], v['nu']),
                (v['r_step'], v['R_bear'] + v['tol_bore_r'], v['t_cb_out'] + v['tol_t_cb'], v['E'], v['nu'])]
        r = annular_plate(regs, v['p_test'], 'ss')
        return (v['sigma_allow'] - r['sigma']) if kind == 'stress' else (v['c_cb_rear'] - r['w'])
    og = [dict(decision='OD-G4-ATM-STD', options='5 ATM test standard and margin (p_test 0.500 nom / 0.625 max planning)', credited=False,
               note='p max used'),
          dict(decision='OD-G4-MATERIAL', options='caseback / midcase material family (conditional on G5)', credited=False,
               note='candidate material class at its minimum planning properties')]
    sid = 'H13-CASEBACK-' + ('STRESS' if kind == 'stress' else 'DEFLECTION')
    s = spec(sid, 'H13', 'stepped annular caseback plate (Roark-class closed form): PROVISIONAL continuous inner bearing at the pod frame; not established by discrete '
                         'case supports; outer edge on the case; %s' % ('allowable - bending stress >= 0' if kind == 'stress'
                                                                          else 'clearance to the REAR skin face - deflection > 0'),
             terms, f, owner_gated=og)
    s['units'] = 'MPa' if kind == 'stress' else 'mm'
    return s


def pressure_domains_valid(domains, total_area):
    return (all(d['area_mm2'] >= 0 for d in domains)
            and abs(sum(d['area_mm2'] for d in domains) - total_area) < 1e-6
            and len({d['id'] for d in domains}) == len(domains))


def bypass_structural_pass(bypass):
    # H13 planning screen uses actual margins, independently of qualification labels.
    return bypass['stress_margin_MPa'] >= 0. and bypass['deflection_margin_mm'] > 0.


def post_load(st, sp, dp):
    """Disjoint projected areas; whole-body equilibrium is independent of the plate surrogate."""
    p = st.G1in['plate_check']['p_test_MPa']['max']
    radius = dp['D'] / 2 - dp['tw'] + sp.pc_env['radius_mm']
    total_area = math.pi * radius ** 2
    pod = st.s14geo['pod_area']
    # Offset of convex pod polygon by frame width: exact Steiner area, separate from pod aperture.
    width = st.P['w_pod_frame_mm']['nom']
    frame = poly_perimeter(st.s14geo['pod']) * width + math.pi * width ** 2
    domains = [dict(id='WINDOW_APERTURE', area_mm2=pod, boundary='frozen S14 polygon'),
               dict(id='POD_FRAME', area_mm2=frame, boundary='offset polygon minus S14 polygon'),
               dict(id='CASEBACK_REMAINDER', area_mm2=total_area-pod-frame,
                    boundary='bearing disc minus offset pod polygon; feedthrough area replaces caseback material')]
    for d in domains:
        d['force_N'] = p * d['area_mm2']
    total = p * total_area
    # Four actual case-side posts; worst sharing bound declares one post carrying twice the mean.
    buttons=button_layout(st,sp,dp)
    sup = supports_layout(st, sp, dp, buttons, vent_layout(st,sp,dp,buttons))
    count = sum(x['placement'] is not None for x in sup['supports'])
    rin = dp['rcin'] + sp.pc_car['radius_mm'] + dp['tcw'] + sp.pc_car['thickness_mm'] + st.P['c_insert_mm']['max']
    bearing_width = max(0., dp['tw'] - sp.pc_env['od_radius_mm'] - sp.pc_env['radius_mm'])
    tangent = st.P['supports']['post_tangential_mm'] - 2*sp.pc_env['radius_mm']
    rim_area=math.pi*((dp['D']/2-sp.pc_env['od_radius_mm'])**2-radius**2)
    area = max(0.,rim_area)/max(1,count)
    unequal = st.P['support_load']['unequal_share_factor']
    force = total * unequal / max(1, count)
    allowable = min(sp.m_mid['sigma_allow_MPa']['min'],st.I['material_classes'][sp.c.get('dielectric_sector_material',sp.c['midcase']['material'])]['sigma_allow_MPa']['min'])
    compression = force/area if area > 0 else None
    path = load_paths(sp.c)
    rb=math.sqrt((pod+frame)/math.pi)
    step=st.s14geo['outline_r']+st.P['c_hard_stop_mm']['nom']
    cb=sp.m_cb;tol=sp.pc_cb['thickness_mm']
    bypass=annular_plate([(rb,step,dp['t_in']-tol,cb['E_MPa']['min'],cb['nu']['max']),
                         (step,radius,dp['t_out']-tol,cb['E_MPa']['min'],cb['nu']['max'])],p,'loaded_boss')
    bypass.update(evidence_class='PROVISIONAL_ASSUMPTION',equivalent_loaded_frame_radius_mm=rb,
                  stress_margin_MPa=cb['sigma_allow_MPa']['min']-bypass['sigma'],
                  deflection_margin_mm=st.P['c_cb_rear_mm']['min']-bypass['w'],
                  boundary='Area-equivalent rigid central frame loading the caseback shell; zero inner support reaction, continuous perimeter bearing. Disjoint disc plus annulus; no G3 posts or PCB support.',
                  qualification='Planning surrogate only: real polygon, cutouts, frame bending, discrete/partial contact require FEA.')
    bypass['pass_'] = bypass_structural_pass(bypass)
    modes = dict(compression=dict(area_mm2=area, stress_MPa=compression, planning_allowable_MPa=allowable,
                                 margin_MPa=allowable-compression if compression is not None else None,
                                 evidence_class='PROVISIONAL_ASSUMPTION'),
                 bearing=dict(required_contact_area_mm2=force/allowable, available_mm2=area,
                              evidence_class='PROVISIONAL_ASSUMPTION'),
                 shear=dict(required_area_mm2=force/(allowable/2), planning_allowable_MPa=allowable/2,
                            provided_area_mm2=None, evidence_class='MANUFACTURER_DATA_REQUIRED'),
                 buckling=dict(unbraced_length_upper_mm=st.rear_alloc_min()+st.layer('battery_zone'),
                               effective_length_factor=2.,
                               required_inertia_Euler_surrogate_mm4=force*(2*(st.rear_alloc_min()+st.layer('battery_zone')))**2/(math.pi**2*min(sp.m_mid['E_MPa']['min'],st.I['material_classes']['MAT-GF-POLY']['E_MPa']['min'])),
                               section_inertia_mm4=None,
                               evidence_class='MANUFACTURER_DATA_REQUIRED'),
                 ceramic_contact=dict(force_bound_N=force, minimum_area_at_planning_allowable_mm2=force/allowable,
                                      required_qualified_contact_allowable_MPa=2*force/area if area>0 else None,
                                      provisional_contact_edge_factor=2., contact_allowable_MPa=None, evidence_class='MANUFACTURER_DATA_REQUIRED'))
    return dict(evidence_class='PROJECT_DERIVED', p_test_MPa=p, domains=domains,
                domain_partition_pass=pressure_domains_valid(domains,total_area), total_area_mm2=total_area,
                pressure_domain_scope='caseback projected area inside outer bearing radius; peripheral case material reacts directly at midcase, cover screened separately',
                total_N=total, perimeter_reaction_N=total, case_side_bypass_screen=bypass, pcb_pressure_load_N=0. if path['pass_'] else None,
                pcb_pressure_load_bound_N=[0.,0.] if path['pass_'] else [0.,p*(pod+frame)],
                posts=count, perimeter_contact_area_mm2=rim_area, bearing_width_mm=bearing_width,
                reaction_geometry='continuous midcase rear-face bearing annulus; four case-side quadrants bounded at twice equal sharing; lug-root screws retain caseback',
                unequal_share_factor=unequal, per_post_N=force, modes=modes,
                pass_=path['pass_'] and all(v.get('margin_MPa',-1.)>=0 for v in modes.values()),
                support_evidence_closed=all(v['evidence_class']!='MANUFACTURER_DATA_REQUIRED' for v in modes.values()), required_area_mm2=force/allowable,
                pin_capacity_N_at_sigma_allow_min=None, pin_dia_max_mm=None,
                no_g3_reopening_demonstrated=True,
                note='Window/frame and caseback loads enter a caseback shell and perimeter/case-side bearing path. '
                     'No P1 pressure load is assigned to PCB lands. Perimeter quadrant compression/bearing bound uses twice equal sharing; battery posts locate the carrier and are not the pressure reaction;  '
                     'shear, buckling and ceramic contact remain numeric manufacturer/FEA gates. The continuous-inner-support '
                     'annular plate is a comparison screen only; this bypass has not established that boundary. '
                     'P2 retains a forbidden REAR-board branch. No support capacity or G3 land enlargement is established.')


def plate_amax(st, sp, t_in, t_out, cache):
    """Largest outer bearing radius for which both caseback screens pass at linear worst (monotone in span)."""
    key = (sp.c['id'], t_in, t_out)
    if key in cache:
        return cache[key]
    dp = dict(D=50.0, tw=1.0, t_in=t_in, t_out=t_out)
    fs = fast(caseback_plate_spec(st, sp, dp, 'stress'))
    fd = fast(caseback_plate_spec(st, sp, dp, 'deflection'))
    tolr = sp.pc_env['radius_mm']

    def ok(a):
        return fs(R_bear=a - tolr) >= -1e-9 and fd(R_bear=a - tolr) > 1e-12
    lo, hi = st.s14geo['outline_r'] + 0.5, 27.0
    if not ok(lo):
        cache[key] = None
        return None
    if ok(hi):
        cache[key] = hi
        return hi
    for _ in range(20):
        mid = (lo + hi) / 2
        if ok(mid):
            lo = mid
        else:
            hi = mid
    cache[key] = lo
    return lo


# --------------------------------------------------------------------------------------------
# LRA placement search (section 8.9) - plan exclusions are shared; Z and outer bound per design
# --------------------------------------------------------------------------------------------
def lra_exclusions(st):
    g = st.s14geo
    ex = [('S14_OUTLINE', dict(type='circles', circles=[[100.0, 100.0, g['outline_r']]])),
          ('S14_POD', dict(type='poly', pts=g['pod'])),
          ('S14_TAIL_CONSERVATIVE', dict(type='poly', pts=g['tail_cons'])),
          ('S14_TAIL_STRAIN_RELIEF_CONSERVATIVE', dict(type='poly', pts=g['tail_relief_cons'])),
          ('S14_THERMODE_KEEPOUT', dict(type='poly', pts=g['thermode'])),
          ('S14_U6_ISLAND', dict(type='poly', pts=g['u6_island']))]
    ex += [('S14_SUPPORT_%d' % s['az'], dict(type='poly', pts=s['poly'])) for s in g['supports']]
    for rid in ('FPC_UNDER', 'CHG_ROUTE', 'CHG_LINK', 'CHG_CONTACT', 'GNSS_RAD', 'WIFI_RAD', 'MAG_CLEAR'):
        ex.append((rid, st.res[rid]['geometry']))
    for rid in ('G2-J202-WEST-F.Cu-2', 'G2-U7-B.Cu-2', 'G2-U7-SERVICE-POCKET'):
        ex.append((rid, st.g2res[rid]['geometry']))
    return ex


def lra_poses(st):
    P = st.I['lra_search']
    c_plan = st.I['parameters']['c_lra_plan_mm']['max']
    ex = lra_exclusions(st)
    out_r = st.s14geo['outline_r']
    radii = frange(12.0, 26.0, P['r_step_mm'])
    poses = []
    for cls in st.I['lra_classes']:
        oris = [None] if cls['shape'] == 'coin' else P['orientations_deg']
        for az in range(0, P['az_stop_deg'] + 1, P['az_step_deg']):
            for r in radii:
                c = xy(r, az)
                for o in oris:
                    if o is None:
                        env = [(c, cls['diameter_mm']['max'] / 2)]
                    else:
                        ang = math.degrees(math.atan2(c[1] - 100.0, c[0] - 100.0)) + (90.0 if o == 0 else 0.0)
                        env = rect_cover(c, cls['length_mm']['max'], cls['width_mm']['max'], ang)
                    rmax = max(math.hypot(p[0] - 100, p[1] - 100) + rho for p, rho in env)
                    rmin = min(math.hypot(p[0] - 100, p[1] - 100) - rho for p, rho in env)
                    if rmin < out_r + c_plan:
                        viol = ['S14_OUTLINE']
                    else:
                        viol = [eid for eid, gg in ex if min(circle_clear(p, rho, gg) for p, rho in env) < c_plan - 1e-9]
                    u703 = min(math.dist(p, st.u703) - rho for p, rho in env)
                    poses.append(dict(cls=cls['id'], az=az, r=r, ori=o, rmax=rmax, rmin=rmin, viol=viol, u703=u703))
    return dict(poses=poses, by_class={c['id']:[p for p in poses if p['cls']==c['id']] for c in st.I['lra_classes']}, exclusions=[e[0] for e in ex], c_plan=c_plan)


# --------------------------------------------------------------------------------------------
# Perimeter features: buttons, supports, vent, screws, lugs, charger, conductive / magnetic rules
# --------------------------------------------------------------------------------------------
def res_az(st, rid):
    if rid in st.g2res:
        return tuple(st.g2res[rid]['azimuth_deg'])
    g = st.res[rid]['geometry']
    if g['type'] == 'sector':
        return tuple(g['az'])
    return tuple(ad.derive_reservations([st.res[rid]])[rid]['az'])


def fcu_edge_parts(st):
    out = []
    for f in st.HM['main_footprints']:
        if f['side'] == 'F.Cu' and f['courtyard_bbox']:
            out.append((f['ref'], dict(type='rect', rect=f['courtyard_bbox'])))
    return out


def button_layout(st, sp, dp):
    B = st.P['buttons']
    out = []
    for sw, (a0,a1) in sorted(B['windows_deg'].items()):
        pc = sp.button_process(sw)
        mat = st.I['material_classes'][sp.c['dielectric_sector_material']] if sw == 'SW5' and sp.c.get('dielectric_sectors') else sp.m_mid
        bd = B['bore_dia_mm']['max'] + 2*pc['radius_mm']
        rin = st.R_main + sp.pc_pcb['radius_mm'] + st.P['c_main_case_mm']['max'] + B['c_switch_mm']['max'] + pc['radius_mm']
        boss = dp.get('bosses', {}).get(sw, max(st.I['sweep']['boss_extension_mm']))
        rout = dp['D']/2 + boss + pc['boss_mm']
        centre = (a0+a1)/2
        half = math.degrees(math.asin(min(1., bd/2/rin)))
        bh = math.degrees(math.asin(min(1., (bd/2+mat['t_wall_min_mm']['max']+pc['thickness_mm'])/(dp['D']/2))))
        out.append(dict(id=sw,window=(a0,a1),centre=centre,r_in=rin,bore_dia=bd,half_bore_deg=half,boss_half_deg=bh,
                        boss_in_window=centre-bh >= a0-EPS and centre+bh <= a1+EPS,
                        local_process=pc['title'], local_wall_min_mm=mat['t_wall_min_mm']['max'],
                        switch_overhang_travel_mm=B['c_switch_mm']['max'],
                        bore_geom=sector(centre-half,centre+half,rin,max(rin,rout)),
                        boss_geom=sector(centre-bh,centre+bh,dp['D']/2-dp['tw'],rout)))
    return out


def place_on_arc(st, window, half, exclusions, step=0.5, prefer=None):
    """Deterministic placement of an arc feature of half-width `half` inside `window` avoiding exclusions
    (each an arc); maximises the clearance, ties broken by distance to `prefer` then azimuth."""
    a0, a1 = window
    span = (a1 - a0) % 360.0
    best = None
    n = int(round(span / step))
    for i in range(n + 1):
        c = a0 + i * step
        arc = ((c - half) % 360.0, (c + half) % 360.0)
        if not (arc_has(arc[0], a0, a1) and arc_has(arc[1], a0, a1)):
            continue
        gap = min([arc_gap(arc, e) for e in exclusions] + [999.0])
        if gap <= 0.0:
            continue
        key = (-min(gap, 3.0), abs(((c - prefer + 180) % 360) - 180) if prefer is not None else 0.0, c % 360.0)
        if best is None or key < best[0]:
            best = (key, c % 360.0, gap)
    return None if best is None else dict(centre=best[1], half=half, clearance_deg=best[2])


def supports_layout(st,sp,dp,buttons,vent):
    cache=getattr(st,'_support_cache',None)
    if cache is None: st._support_cache=cache={}
    key=(sp.c['id'],json.dumps(dp,sort_keys=True),json.dumps([{k:v for k,v in b.items() if k!='pusher_requirement'} for b in buttons],sort_keys=True),json.dumps(vent,sort_keys=True))
    if key not in cache: cache[key]=_supports_layout(st,sp,dp,buttons,vent)
    return cache[key]


def _supports_layout(st, sp, dp, buttons, vent):
    """Case supports = BATTERY-level posts outside R_channel_inner and every G2 riser (H24, X14, X18); a front-gap MAIN stop pad is
    added at the post azimuth where the MAIN F.Cu edge is free. >= 3 pads must enclose the board centre."""
    S = st.I['parameters']['supports']
    pad_in = st.R_main - sp.pc_pcb['radius_mm'] - S['pad_radial_mm']['max']
    half = math.degrees(math.asin((S['pad_tangential_mm'] / 2) / pad_in))
    post_half = math.degrees(math.asin((S['post_tangential_mm'] / 2) / (dp['D'] / 2 - dp['tw'])))
    pad_ex = []
    for ref, g in fcu_edge_parts(st):
        x0, y0, x1, y1 = g['rect']
        rmax = max(math.hypot(x - 100, y - 100) for x in (x0, x1) for y in (y0, y1))
        if rmax > pad_in - S['fcu_clearance_mm']:
            azs = [polar((x, y))[1] for x in (x0, x1) for y in (y0, y1)]
            lo, hi = min(azs), max(azs)
            arc = (lo, hi) if hi - lo < 180 else (min(a for a in azs if a >= 180), max(a for a in azs if a < 180))
            pad_ex.append(('F.Cu ' + ref, arc))
    pad_ex.append(('DISP_FPC', tuple(st.res['DISP_FPC']['geometry']['az'])))
    for b in buttons:
        pad_ex.append((b['id'] + ' bore', ((b['centre'] - b['half_bore_deg']) % 360, (b['centre'] + b['half_bore_deg']) % 360)))
    if vent:
        pad_ex.append(('VENT port', ((vent['centre'] - vent['half']) % 360, (vent['centre'] + vent['half']) % 360)))
    post_ex = [(rid + ' riser', res_az(st, rid)) for rid in ('G2-J1501-F.Cu-1', 'G2-J201-F.Cu-1', 'G2-J202-WEST-F.Cu-1', 'G2-U7-B.Cu-1')]
    post_ex.append(('FPC_CORR', tuple(st.res['FPC_CORR']['geometry']['az'])))

    def clear(c, h, ex):
        arc = ((c - h) % 360, (c + h) % 360)
        return min([arc_gap(arc, e[1]) for e in ex] + [999.0])

    def max_gap(az):
        a = sorted(x % 360 for x in az)
        return max(((a[(k + 1) % len(a)] - a[k]) % 360) or 360.0 for k in range(len(a))) if a else 360.0
    out = []
    for rid in ('SUP_SW', 'SUP_SE', 'SUP_NE'):
        w = res_az(st, rid)
        span = (w[1] - w[0]) % 360
        mid = w[0] + span / 2
        best = None
        for k in range(int(round(span / 0.5)) + 1):
            c = (w[0] + 0.5 * k) % 360
            if not (arc_has((c - post_half) % 360, *w) and arc_has((c + post_half) % 360, *w)):
                continue
            pc = clear(c, post_half, post_ex)
            if pc <= 0:
                continue
            pd = clear(c, half, pad_ex)
            key = (pd <= 0, -min(pd, 3.0), abs(((c - mid + 180) % 360) - 180), c)
            if best is None or key < best[0]:
                best = (key, dict(centre=c, post_clearance_deg=pc, pad=pd > 0, pad_clearance_deg=pd))
        out.append(dict(id=rid, window=w, placement=None if best is None else best[1]))
    posts = [s['placement']['centre'] for s in out if s['placement']]
    pads = [s['placement']['centre'] for s in out if s['placement'] and s['placement']['pad']]
    wn = tuple(S['w_nw_search_deg'])
    best = None
    for k in range(int(round((wn[1] - wn[0]) / 0.5)) + 1):
        c = wn[0] + 0.5 * k
        pc = clear(c, post_half, post_ex)
        if pc <= 0:
            continue
        pd = clear(c, half, pad_ex)
        pad = pd > 0
        key = (not pad, max_gap(pads + ([c] if pad else [])) >= 180.0, max_gap(posts + [c]), max_gap(pads + ([c] if pad else [])), c)
        if best is None or key < best[0]:
            best = (key, dict(centre=c, post_clearance_deg=pc, pad=pad, pad_clearance_deg=pd))
    out.append(dict(id='SUP_WNW', window=wn, placement=None if best is None else best[1]))
    posts = [s['placement']['centre'] for s in out if s['placement']]
    pads = [s['placement']['centre'] for s in out if s['placement'] and s['placement']['pad']]
    return dict(pad_inner_r=pad_in, pad_half_deg=half, post_half_deg=post_half, supports=out, largest_unsupported_arc_deg=max_gap(posts),
                largest_pad_arc_deg=max_gap(pads), pads=len(pads),
                legacy_largest_unsupported_arc_deg=st.A['supports']['results']['largest_unsupported_arc_deg'],
                exclusions=[dict(id=e[0], arc=e[1], applies='pad') for e in pad_ex] + [dict(id=e[0], arc=e[1], applies='post') for e in post_ex])


def vent_layout(st, sp, dp, buttons):
    V = st.I['parameters']['bond_lands']
    d = V['vent_port_dia_mm']['max'] + 2 * (V['vent_membrane_land_mm']['max'] + sp.pc_env['radius_mm'])
    r = dp['D'] / 2 - dp['tw']
    half = math.degrees(math.asin((d / 2) / r))
    ex = [((b['centre'] - b['boss_half_deg']) % 360, (b['centre'] + b['boss_half_deg']) % 360) for b in buttons]
    sup = res_az(st, 'SUP_NE')
    pl = place_on_arc(st, tuple(st.I['parameters']['vent']['search_deg']), half, ex + [sup], prefer=None)
    if pl:
        pl['membrane_dia_mm'] = d
    return pl


def lug_layout(st, dp):
    L = st.I['parameters']['lugs']
    R = dp['D'] / 2
    wmin, wmax = L['inner_width_mm']['min'], L['inner_width_mm']['max']
    arm_min, arm_max = L['arm_width_mm']['min'], L['arm_width_mm']['max']
    lmax = L['arm_length_mm']['max']
    out = []
    for name, sgn in (('LUG_N', -1.0), ('LUG_S', 1.0)):
        for side in (-1.0, 1.0):
            xa, xb = sorted((100 + side * wmin / 2, 100 + side * (wmax / 2 + arm_max)))
            yc = math.sqrt(max(0.0, R * R - (wmin / 2) ** 2))
            ya, yb = sorted((100 + sgn * (R + lmax), 100 + sgn * yc))
            out.append(dict(id='%s_%s' % (name, 'E' if side > 0 else 'W'), geom=dict(type='rect', rect=[xa, ya, xb, yb]), kind='lug arm'))
        off = L['spring_bar_offset_mm']
        rb = L['spring_bar_dia_mm'] / 2
        ya, yb = sorted((100 + sgn * (R + off['min'] - rb), 100 + sgn * (R + off['max'] + rb)))
        out.append(dict(id=name + '_SPRING_BAR', geom=dict(type='rect', rect=[100 - wmax / 2, ya, 100 + wmax / 2, yb]), kind='spring bar'))
    return out


def screw_layout(st, sp, dp):
    L = st.I['parameters']['lugs']
    sc = st.I['parameters']['screw_classes'][sp.c['screw_class']]
    edge = sp.m_mid['screw_edge_min_mm'] or 0.0
    band = (L['inner_width_mm']['max'] / 2, L['inner_width_mm']['min'] / 2 + L['arm_width_mm']['min'])
    xc = sum(band) / 2
    r_s = dp['D'] / 2 + sc['hole_dia_mm'] / 2 + edge
    out = []
    for name, sgn in (('N', -1.0), ('S', 1.0)):
        for side in (-1.0, 1.0):
            x = 100 + side * xc
            y = 100 + sgn * math.sqrt(max(0.0, r_s * r_s - xc * xc))
            out.append(dict(id='SCREW_%s%s' % (name, 'E' if side > 0 else 'W'), centre=(x, y),
                            geom=dict(type='circles', circles=[[x, y, sc['hole_dia_mm'] / 2]]),
                            radius=math.hypot(x - 100, y - 100), azimuth=polar((x, y))[1]))
    return dict(cls=sp.c['screw_class'], band_x_mm=band, screws=out, outside_body=all(s['radius'] - sc['hole_dia_mm'] / 2 >= dp['D'] / 2 - 1e-9 for s in out))


def features(st, sp, dp, buttons, supports, screws, lugs, chg_r_out, lra_pose=None, extra=None):
    """Every new conductive / ferromagnetic part and every new wire, with Z levels (H17 / H18)."""
    c = sp.c
    F = []
    metal_mid = c.get('conductive_midcase', False)
    diel = []
    if c.get('dielectric_sectors'):
        m = c['dielectric_sector_az_margin_deg']
        for rid in ('GNSS_RAD', 'BLE_RAD', 'WIFI_RAD'):
            a = res_az(st, rid)
            diel.append((rid, ((a[0] - m) % 360, (a[1] + m) % 360)))
    R = dp['D'] / 2
    if metal_mid:
        # metal midcase = complement of the dielectric sectors at every level
        arcs = sorted(d[1] for d in diel)
        cuts = sorted(((a % 360, b % 360) for a, b in arcs), key=lambda e: e[0])
        for i, (a0, a1) in enumerate(cuts):
            n0 = cuts[(i + 1) % len(cuts)][0]
            F.append(dict(id='MIDCASE_METAL_%d' % i, geom=sector(a1, n0, R - dp['tw'], R), z=['FRONT', 'MAIN', 'BATTERY', 'REAR'],
                          conductive=True, ferromagnetic=sp.m_mid['ferromagnetic'], kind='midcase'))
            F.append(dict(id='DISP_LAND_METAL_%d' % i, geom=sector(a1, n0, st.R_display - dp['w_land'], R - dp['tw']), z=['MAIN'],
                          conductive=True, ferromagnetic=sp.m_mid['ferromagnetic'], kind='display land'))
    for s in screws['screws']:
        F.append(dict(id=s['id'], geom=s['geom'], z=['REAR'], conductive=True, ferromagnetic=False, kind='caseback screw'))
    for lg in lugs:
        cond = True if lg['kind'] == 'spring bar' else metal_mid
        F.append(dict(id=lg['id'], geom=lg['geom'], z=['MAIN', 'BATTERY', 'REAR'], conductive=cond, ferromagnetic=False, kind=lg['kind']))
    rad = {rid: st.res[rid] for rid in ('GNSS_RAD', 'BLE_RAD', 'WIFI_RAD')}
    mag = st.res['MAG_CLEAR']
    for b in buttons:
        in_rad = any(overlaps(b['bore_geom'], r['geometry']) for r in rad.values() if 'MAIN' in r['z_levels'])
        in_mag = overlaps(b['bore_geom'], mag['geometry'])
        b['pusher_requirement'] = dict(conductive=not in_rad, ferromagnetic=False,
                                       rule='non-conductive pusher' if in_rad else 'metal permitted (non-ferromagnetic)',
                                       mag_clear=in_mag)
        F.append(dict(id=b['id'] + '_PUSHER', geom=b['bore_geom'], z=['MAIN'], conductive=not in_rad, ferromagnetic=False, kind='pusher'))
    for s in supports['supports']:
        if not s['placement'] or not s['placement']['pad']:
            continue
        a = s['placement']['centre']
        h = supports['pad_half_deg']
        inside_diel = any(arc_has(a, *d[1]) for d in diel)
        cond = metal_mid and not inside_diel
        F.append(dict(id=s['id'] + '_PAD', geom=sector(a - h, a + h, supports['pad_inner_r'], R - dp['tw']), z=['MAIN'],
                      conductive=cond, ferromagnetic=False, kind='support pad'))
    for b in buttons:
        pc = sp.button_process(b['id'])
        is_poly = b['id']=='SW5' and c.get('dielectric_sectors')
        F.append(dict(id=b['id']+'_BOSS', geom=b['boss_geom'], z=['MAIN'],
                      conductive=metal_mid and not is_poly, ferromagnetic=False, kind='button boss'))
    for s_ in supports['supports']:
        if s_['placement']:
            a=s_['placement']['centre']; half=supports['post_half_deg']
            rch=dp['rcin']+sp.pc_car['radius_mm']+dp['tcw']+sp.pc_car['thickness_mm']+st.P['c_insert_mm']['max']
            inside_diel=any(arc_has(a,*d[1]) for d in diel)
            F.append(dict(id=s_['id']+'_CASE_SIDE',geom=sector(a-half,a+half,rch,max(rch,R-dp['tw'])),
                          z=['BATTERY','REAR'],conductive=metal_mid and not inside_diel,ferromagnetic=False,kind='case-side support'))
    for rid,arc in diel:
        F.append(dict(id='DIELECTRIC_'+rid,geom=sector(*arc,R-dp['tw'],R),z=['MAIN','BATTERY','REAR'],
                      conductive=False,ferromagnetic=False,kind='dielectric sector'))
    F.append(dict(id='CHG_CONTACT_BLOCK', geom=sector(80.0, 100.0, st.s14geo['outline_r'] + 1.1, chg_r_out), z=['REAR'],
                  conductive=True, ferromagnetic=False, kind='charger contacts'))
    chg=charger_fit(st,sp,dict(dp,chg_r_out=chg_r_out))['best']
    F.append(dict(id='CHG_4X5_WITH_LAND',geom=chg['geom'],z=['REAR'],conductive=True,ferromagnetic=False,kind='charger aperture and land'))
    if c['caseback'].get('split'):
        rmin = min(st.res[r]['radial_mm'][0] for r in ('GNSS_RAD', 'WIFI_RAD'))
        rc = rmin - c['caseback']['centre_rf_clearance_mm']
        F.append(dict(id='CASEBACK_CENTRE_PLATE', geom=dict(type='circles', circles=[[100.0, 100.0, rc]]), z=['REAR'],
                      conductive=True, ferromagnetic=False, kind='caseback centre plate'))
    for rid in ('G2-J202-WEST-F.Cu-2', 'G2-J202-WEST-F.Cu-1'):
        F.append(dict(id=rid, geom=st.g2res[rid]['geometry'], z=st.g2res[rid]['z_levels'], conductive=True, ferromagnetic=False,
                      kind='new wiring', wiring=True))
    F.append(dict(id='CHG_LINK', geom=st.res['CHG_LINK']['geometry'], z=['REAR'], conductive=True, ferromagnetic=False, kind='new wiring', wiring=True))
    if lra_pose is not None:
        F.append(dict(id='LRA', geom=dict(type='circles', circles=[[p[0], p[1], rho] for p, rho in lra_pose['env']]), z=['REAR'],
                      conductive=True, ferromagnetic=True, kind='LRA'))
    for e in extra or []:
        F.append(e)
    return F, diel


def rf_mag_check(st, F):
    rad = {rid: st.res[rid] for rid in ('GNSS_RAD', 'BLE_RAD', 'WIFI_RAD')}
    mag = st.res['MAG_CLEAR']
    rf, mg, dist = [], [], []
    for f in F:
        for rid, r in rad.items():
            if not set(f['z']) & set(r['z_levels']):
                continue
            if (f['conductive'] or f.get('wiring')) and overlaps(f['geom'], r['geometry']):
                rf.append(dict(feature=f['id'], kind=f['kind'], radiator=rid))
        if f['ferromagnetic'] and set(f['z']) & set(mag['z_levels']) and overlaps(f['geom'], mag['geometry']):
            mg.append(dict(feature=f['id'], kind=f['kind']))
    for f in ([] if SWEEP_MODE else F):
        if f['conductive'] and f['kind'] in ('caseback screw', 'spring bar', 'lug arm', 'charger contacts', 'pusher', 'LRA',
                                              'caseback centre plate', 'support pad'):
            for rid, r in sorted(rad.items()):
                if set(f['z']) & set(r['z_levels']):
                    dist.append(dict(feature=f['id'], radiator=rid, plan_distance_mm=region_distance(f['geom'], r['geometry'], 0.1)))
    return dict(rf_intrusions=rf, mag_violations=mg, conductive_distances=dist,
                h17_pass=not rf, h18_pass=not mg)


# --------------------------------------------------------------------------------------------
# H14 seal inventory and seal-path closure (graph check)
# --------------------------------------------------------------------------------------------
def seal_inventory(st, cand, window_variant, n_cells, seal_topology, f3_used=False):
    comps = {'MIDCASE': [], 'COVER': [], 'CASEBACK': [], 'CHG_BLOCK': [], 'VENT_MEMBRANE': []}
    seals = []

    def ap(owner, aid, filler, sid, stype):
        comps[owner].append(dict(aperture=aid, filler=filler, seal=sid, type=stype))
        comps.setdefault(filler, [])
        seals.append(dict(id=sid, type=stype, interface=[owner, filler], aperture=aid))
    ap('MIDCASE', 'FRONT_OPENING', 'COVER', 'S-COVER', 'adhesive ring')
    ap('MIDCASE', 'REAR_OPENING', 'CASEBACK', 'S-CB-MAIN', {'radial': 'radial O-ring', 'face': 'face O-ring', 'adhesive': 'adhesive ring'}[seal_topology])
    for k in range(1, 6):
        ap('MIDCASE', 'BORE_SW%d' % k, 'PUSHER_SW%d' % k, 'S-SW%d' % k, 'radial O-ring')
    ap('MIDCASE', 'VENT_PORT', 'VENT_MEMBRANE', 'S-VENT', 'membrane')
    if cand['pod_concept'] == 'P1':
        holder = 'CASEBACK'
    else:
        ap('CASEBACK', 'POD_APERTURE', 'POD_FRAME', 'S-POD-FRAME', 'radial O-ring')
        holder = 'POD_FRAME'
    if window_variant == 'W2':
        for i in range(n_cells):
            ap(holder, 'POD_CELL_%02d' % (i + 1), 'WINDOW_%02d' % (i + 1), 'S-POD-%02d' % (i + 1), 'adhesive ring')
    else:
        ap(holder, 'POD_OPENING', 'WINDOW', 'S-POD', 'adhesive ring')
    ap('CASEBACK', 'CHG_APERTURE', 'CHG_BLOCK', 'S-CHG', 'adhesive ring')
    if cand['caseback'].get('split'):
        ap('CASEBACK', 'CENTRE_OPENING', 'CB_CENTRE', 'S-CB-SPLIT', 'adhesive ring')
    if f3_used:
        ap('CASEBACK', 'U6_F3_APERTURE', 'U6_STUD', 'S-U6F3', 'radial O-ring')
    return dict(components=comps, seals=seals)


def seal_closure(inv, screws_outside=True):
    comps, seals = inv['components'], inv['seals']
    problems = []
    by_id={s['id']:s for s in seals}
    for owner, aps in comps.items():
        for a in aps:
            if not a.get('seal') or not a.get('filler'):
                problems.append('aperture %s of %s has no primary seal/filler' % (a['aperture'], owner))
            primary=by_id.get(a.get('seal'))
            if primary is None or primary['interface']!=[owner,a.get('filler')] or primary['aperture']!=a['aperture'] or primary['type']!=a['type']:
                problems.append('aperture primary-seal identity mismatch: '+a['aperture'])
    ids = [s['id'] for s in seals]
    if len(ids) != len(set(ids)):
        problems.append('duplicate seal id')
    per_ap = {}
    for s in seals:
        per_ap.setdefault((s['interface'][0], s['aperture']), []).append(s['id'])
    for k, v in per_ap.items():
        if len(v) != 1:
            problems.append('aperture %s/%s has %d primary seals' % (k[0], k[1], len(v)))
    adj = {}
    for s in seals:
        if s.get('id'):
            a, b = s['interface']
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
    seen, todo = set(), ['MIDCASE']
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        todo += sorted(adj.get(n, ()))
    for n in comps:
        if n not in seen:
            problems.append('component %s not connected to the sealed boundary' % n)
    if not screws_outside:
        problems.append('caseback screws inside the primary seal line without own seals')
    return dict(closed=not problems, problems=problems, seal_count=len(seals), component_count=len(comps))


# --------------------------------------------------------------------------------------------
# X20 pressure load-path graph (H10 / H13)
# --------------------------------------------------------------------------------------------
def load_paths(cand):
    edges = [('WINDOW', 'POD_FRAME'), ('POD_FRAME', 'CASEBACK'),
             ('CASEBACK', 'PERIMETER_BEARING'), ('PERIMETER_BEARING', 'CASE_SIDE_SUPPORTS'),
             ('CASE_SIDE_SUPPORTS', 'MIDCASE'), ('COVER', 'MIDCASE'),
             ('PUSHERS', 'MIDCASE'), ('CHG_BLOCK', 'CASEBACK')]
    if cand['pod_concept'] == 'P2':
        # Authored P2 carries its frame on REAR: keep the real forbidden branch until a bypass is established.
        edges.append(('POD_FRAME', 'REAR_BOARD'))
    return path_check(edges)


def path_check(edges):
    forbidden = {'PACK', 'OPTICS', 'REAR_BOARD', 'MAIN', 'DISPLAY', 'UNSUPPORTED_PCB',
                 'OPTICAL_BARRIER', 'PD', 'LED', 'U6'}
    allowed={'WINDOW','COVER','CASEBACK','PUSHERS','CHG_BLOCK','POD_FRAME','PERIMETER_BEARING','CASE_SIDE_SUPPORTS','MIDCASE'}
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
    loaded = ['WINDOW', 'COVER', 'CASEBACK', 'PUSHERS', 'CHG_BLOCK']
    paths, bad, rejected = {}, [], []
    for source in loaded:
        stack, found, failed = [(source, [source])], None, False
        while stack:
            node, path = stack.pop()
            if node in forbidden or node not in allowed:
                rejected.append(path)
                failed = True
                continue
            if node == 'MIDCASE':
                found = found or path
                continue
            if not adj.get(node):
                failed = True
                rejected.append(path)
            for dest in sorted(adj.get(node, []), reverse=True):
                if dest in path:
                    failed = True
                    rejected.append(path + [dest])
                else:
                    stack.append((dest, path + [dest]))
        paths[source] = found
        if failed or found is None:
            bad.append(source)
    return dict(edges=edges, paths=paths, violations=bad, rejected_branches=rejected,
                pass_=not bad, forbidden=sorted(forbidden), allowed=sorted(allowed))


# --------------------------------------------------------------------------------------------
# Diameter sweep and design search (section 7). A D value is feasible if at least one design point
# passes every hard check. Design groups are searched exhaustively over their authored grids.
# --------------------------------------------------------------------------------------------
XS = ('XF-J1501', 'XC-J202', 'XB-J201', 'XL-LRA')


def gland_design(st, sp, topo, cs):
    """Groove geometry centred in the planning compression window; tolerances from the process classes."""
    o = st.I['parameters']['oring']
    w = o['windows']['static_radial' if topo == 'radial' else 'static_face']
    h = round(cs * (1 - (w['compression_min'] + w['compression_max']) / 2) / 0.005) * 0.005
    if topo == 'radial':
        tol_h = max(sp.pc_mid['radius_mm'], st.I['process_classes'][sp.c.get('dielectric_sector_process', sp.c['midcase']['process'])]['radius_mm']) + sp.pc_cb['radius_mm']
    else:
        tol_h = sp.pc_cb['groove_depth_mm']
    tol_g = sp.pc_cb.get('groove_width_mm', sp.pc_cb['thickness_mm'])
    dmax = cs + o['cs_tolerance_mm']['max']
    g = math.ceil(((math.pi / 4 * dmax ** 2) / (w['fill_max'] * (h - tol_h)) + tol_g) / 0.01 - 1e-9) * 0.01
    land = sp.m_cb['groove_land_min_mm']
    return dict(topology=topo, cs=cs, h=h, g=g, tol_h=tol_h, tol_g=tol_g, land=land,
                spigot_radial=(h + land) if topo == 'radial' else 0.0,
                spigot_height=(g + land) if topo == 'radial' else 0.0,
                face_annulus=(2 * land + g) if topo == 'face' else 0.0)


def pusher_gland(st, sp, sw, sw_req_conductive):
    """Dynamic radial pusher O-ring: groove in the pusher (metal machined where a metal pusher is permitted, moulded polymer where
    the bore lies in a radiator volume); bore radius tolerance from the midcase process class."""
    o = st.I['parameters']['oring']
    w = o['windows']['dynamic_radial']
    pcls = 'PC-METAL-MACH' if sw_req_conductive else 'PC-POLY-MOULD'
    pc = st.I['process_classes'][pcls]
    out = []
    for cs in st.I['sweep']['oring_cs_mm']:
        h = round(cs * (1 - (w['compression_min'] + w['compression_max']) / 2) / 0.005) * 0.005
        bottom_tol=max(pc['radius_mm'],pc['groove_depth_mm'])
        tol_h = sp.button_process(sw)['radius_mm'] + bottom_tol
        tol_g = pc['groove_width_mm']
        dmax = cs + o['cs_tolerance_mm']['max']
        g = math.ceil(((math.pi / 4 * dmax ** 2) / (w['fill_max'] * (h - tol_h)) + tol_g) / 0.01 - 1e-9) * 0.01
        specs = sp.gland('H15-' + sw, 'dynamic_radial', cs, h, g, tol_h, tol_g)
        m = [run_check(x, full=False) for x in specs]
        out.append(dict(cs=cs, h=h, g=g, tol_h=tol_h, tol_g=tol_g, pusher_process=pcls,
                        depth_tolerance_mm=pc['groove_depth_mm'], bottom_radius_tolerance_mm=bottom_tol,
                        tolerance_basis='Absolute groove-bottom radius control conservatively bounds radius/depth process limits; independent local bore radius added. Core check separately uses groove-depth tolerance.', margins=m, pass_=min(m) >= -1e-9, specs=specs))
    best = next((x for x in out if x['pass_']), max(out, key=lambda x: (min(x['margins']), -x['cs'])))
    return best, out


def cover_proud(st, sp, dp):
    recess = st.P['cover_recess_depth_mm']['nom']
    tops = dict(bezel=-recess + sp.pc_env['thickness_mm'],
                display_land=-st.layer('cover')-st.layer('cover_bond')-st.layer('display'),
                button_boss=-st.layer('cover')-st.layer('cover_bond')-st.layer('display'))
    return dict(pass_=max(tops.values()) <= EPS, maximum_proud_mm=max(tops.values()),
                feature_top_relative_to_cover_mm=tops, counted_delta_mm=0., evidence_class='PROJECT_DERIVED')


def charger_fit(st, sp, dp, orientation=None):
    """Axis-aligned rectangle plus continuous rectangular seal land contained in CHG_CONTACT sector.
    Centre on 90 degrees; exact corner/edge inequalities for the symmetric convex 20-degree wedge.
    """
    block=st.P['charger_block_min']; land=st.P['bond_lands']['charger_feedthrough_land_mm']
    out=[]
    for ori in ([orientation] if orientation is not None else [0,90]):
        radial,tangent=(block['radial_mm'],block['tangential_mm']) if ori==0 else (block['tangential_mm'],block['radial_mm'])
        corners={}
        def measure(v):
            a=radial/2+v['land']+v['position_tol']
            b=tangent/2+v['land']+v['position_tol']
            lo=max(st.s14geo['outline_r']+1.1+a, b/math.tan(math.radians(10))+a)
            hi=math.sqrt(max(0., (dp['chg_r_out']-v['outer_tol'])**2-b*b))-a
            return hi-lo
        terms=[Term('land','SUPPLIER_GATED','PROVISIONAL_ASSUMPTION',land['nom'],land['max'],(land['min'],land['max'])),
               sp.tol('position_tol',sp.pc_cb['radius_mm']),sp.tol('outer_tol',sp.pc_cb['radius_mm'])]
        row=fix_pass(run_check(spec('H20-RECT-%d'%ori,'H20','4 x 5 aperture plus continuous S-CHG adhesive land: admissible radial centre interval width',terms,measure)))
        a=radial/2+land['max']+sp.pc_cb['radius_mm']; b=tangent/2+land['max']+sp.pc_cb['radius_mm']
        lo=max(st.s14geo['outline_r']+1.1+a,b/math.tan(math.radians(10))+a)
        hi=math.sqrt(max(0.,(dp['chg_r_out']-sp.pc_cb['radius_mm'])**2-b*b))-a
        centre=(lo+hi)/2
        geom=dict(type='rect',rect=[100+centre-a,100-b,100+centre+a,100+b])
        out.append(dict(orientation_deg=ori, radial_mm=radial,tangential_mm=tangent,land_each_side_mm=land['max'],
                        centre_interval_mm=[lo,hi], margin_mm=hi-lo,check=row,geom=geom,
                        radial_fit_mm=dp['chg_r_out']-sp.pc_cb['radius_mm']-(st.s14geo['outline_r']+1.1)-2*a,
                        tangential_available_at_outer_feasible_centre_mm=2*(hi-a)*math.tan(math.radians(10))-2*(land['max']+sp.pc_cb['radius_mm']),
                        seal='S-CHG adhesive ring; no compressed charger seal',
                        feedthrough_interaction='outer boundary already excludes caseback spigot/seal and c_chg_window; bond ring wholly inside sector required',
                        pass_=row['pass']))
    best=max(out,key=lambda x:(x['margin_mm'],-x['orientation_deg']))
    return dict(pass_=best['pass_'], best=best, orientations=out,
                planning_only=True, qualified_contact_block=False, containment_assumption=CHARGER_CONTAINMENT_ASSUMPTION)


def seal_threshold(st, kind, gd):
    w=st.P['oring']['windows'][kind]
    cs,h,g,th,tg=(gd[k] for k in ('cs','h','g','tol_h','tol_g'))
    limits=dict(min_squeeze=cs-(h+th)/(1-w['compression_min']),
                max_squeeze=(h-th)/(1-w['compression_max'])-cs,
                fill=math.sqrt(max(0.,w['fill_max']*4/math.pi*(h-th)*(g-tg)))-cs)
    bound=min(limits.values())
    feasible=bound >= -EPS
    return dict(zero_cs_tolerance_feasible=feasible,
                classification='FINITE_TOLERANCE_BOUND' if feasible else 'IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE',
                maximum_symmetric_cs_tolerance_mm=max(0.,bound) if feasible else None,
                mathematical_bounds_mm=limits, planning_tolerance_mm=st.P['oring']['cs_tolerance_mm']['max'],
                limit_class='PROVISIONAL PLANNING LIMIT',
                supplier_qualified=False,
                open_effects=['stretch','eccentricity','extrusion gap','thermal expansion','swelling','compression set'],
                note='A negative bound means geometry/process redesign, never a tighter supplier tolerance.')


def button_stack_specs(st,sp,dp,button,gd):
    sw=button['id'];pc=sp.button_process(sw)
    pp=st.I['process_classes'][gd['pusher_process']]
    base=sp.bore(dp,sw,dp['bosses'][sw])
    guide=st.P['buttons']['guide_land_each_mm']
    core=st.P['buttons']['core_radius_min_mm']
    bore=st.P['buttons']['bore_dia_mm']
    # Bore stack includes the switch travel term; gland axial width and both guide lands must also fit.
    axial=spec('H21-GLAND-AXIAL-'+sw,'H21','available bore length after switch travel minus groove width and two guide lands',
               base['terms']+[sp.design('groove_width',gd['g']),sp.tol('groove_width_tol',gd['tol_g']),sp.par('guide_land','max',guide)],
               lambda v:base['func'](v)+v['L_bore_min']-v['groove_width']-v['groove_width_tol']-2*v['guide_land'])
    core_spec=spec('H21-PUSHER-CORE-'+sw,'H21','pusher minimum radius minus radial groove depth and core planning minimum',
                  [sp.par('bore_dia','min',bore),sp.design('groove_depth',gd['h']),sp.tol('depth_tol',pp['groove_depth_mm']),
                   sp.tol('bore_radius_tol',pc['radius_mm']),sp.par('core_radius_min','max',core)],
                  lambda v:v['bore_dia']/2-v['bore_radius_tol']-v['groove_depth']-v['depth_tol']-v['core_radius_min'])
    material=st.I['material_classes'][sp.c['dielectric_sector_material']] if sw=='SW5' and sp.c.get('dielectric_sectors') else sp.m_mid
    wall=spec('H21-BOSS-WALL-'+sw,'H21','boss transverse wall after local bore/position tolerances minus local material minimum',
              [sp.design('boss_halfwidth',math.sin(math.radians(button['boss_half_deg']))*dp['D']/2),
               sp.par('bore_dia','max',bore),sp.tol('boss_width_tol',pc['boss_mm']),sp.tol('bore_radius_tol',pc['radius_mm']),
               sp.frozen('wall_min',material['t_wall_min_mm']['max'],'PROVISIONAL_ASSUMPTION')],
              lambda v:v['boss_halfwidth']-v['boss_width_tol']-v['bore_dia']/2-v['bore_radius_tol']-v['wall_min'])
    return [axial,core_spec,wall]


def conditional_seals(st, sp, dp):
    # Evaluate F3 as a geometric option; F1/F2 do not penetrate the boundary.
    cs=st.P['conditional_seals']['U6F3_cs_mm']
    gd=gland_design(st,sp,'radial',cs)
    stud_pc=st.I['process_classes'][st.P['conditional_seals']['U6F3_stud_process']]
    gd['tol_h']=sp.pc_cb['radius_mm']+max(stud_pc['radius_mm'],stud_pc['groove_depth_mm'])
    gd['tol_g']=stud_pc['groove_width_mm']
    gd['g']=math.ceil(((math.pi/4*(cs+st.P['oring']['cs_tolerance_mm']['max'])**2)/(st.P['oring']['windows']['static_radial']['fill_max']*(gd['h']-gd['tol_h']))+gd['tol_g'])/0.01-EPS)*0.01
    gd['spigot_height']=gd['g']+gd['land']
    gd['process_basis']='caseback bore + non-ferromagnetic stud groove; main midcase dielectric-sector tolerance does not apply at U6'
    island=st.s14geo['u6_island']
    centre=xy(st.I['contract_values']['s14']['u6_radius_mm'],st.I['contract_values']['s14']['u6_azimuth_deg'])
    available=min(seg_dist(centre,a,b) for a,b in zip(island,island[1:]+island[:1]))
    required=st.P['conditional_seals']['U6F3_stud_radius_mm']+gd['h']+gd['land']+sp.pc_cb['radius_mm']
    rows=[dict(id='S-U6F3', conditional='F3 only; F1/F2 retained', gland=gd,
               threshold=seal_threshold(st,'static_radial',gd), available_radius_mm=available,
               required_radius_mm=required, land_margin_mm=available-required,
               pass_=available>=required-EPS and min(run_check(x,False) for x in sp.gland('F3','static_radial',cs,gd['h'],gd['g'],gd['tol_h'],gd['tol_g']))>=-EPS)]
    if sp.c['pod_concept']=='P2':
        pg=gland_design(st,sp,'radial',st.P['conditional_seals']['P2_cs_mm'])
        avail=st.s14geo['outline_r']-st.s14geo['pod_r_max']-st.P['w_pod_frame_mm']['nom']
        need=pg['h']+pg['land']+sp.pc_cb['radius_mm']
        rows.append(dict(id='S-POD-FRAME',conditional='mandatory for P2',gland=pg,
                         threshold=seal_threshold(st,'static_radial',pg),land_margin_mm=avail-need,
                         pass_=avail>=need-EPS and min(run_check(x,False) for x in sp.gland('P2','static_radial',pg['cs'],pg['h'],pg['g'],pg['tol_h'],pg['tol_g']))>=-EPS))
    return rows


def complete_candidate(hard):
    return set(hard)==set(HARD) and all(v.get('pass',v.get('pass_',False)) and bool(v.get('evidence',v.get('margins'))) for v in hard.values())


def universal_seal_rejection(st, ce):
    proof=[]
    for sw in sorted(st.P['buttons']['windows_deg']):
        conductive=sw!='SW5'
        _,options=pusher_gland(st,ce.sp,sw,conductive)
        proof.append(dict(button=sw, alternatives=[dict(cs=x['cs'],margins=x['margins'],pass_=x['pass_']) for x in options],
                          all_fail=not any(x['pass_'] for x in options)))
    return dict(hard='H15',proven=any(p['all_fail'] for p in proof),proof=proof,
                independent_of=['diameter','side wall','carrier dimensions','cover','land','caseback','boss'],
                rule='At least one required button fails every authored cross-section with its local process. '
                     'Therefore every Cartesian combination is rejected by H15; no untested complete candidate is accepted. '
                     'Retained diagnostic points at every diameter still evaluate all H01-H25.')


class CandidateEval:
    def __init__(self, st, cand, ctx):
        self.st, self.c, self.ctx = st, cand, ctx
        self.sp = sp = Specs(st, cand)
        SW = st.I['sweep']
        self.window = ctx['window']
        self.t_w = self.window['eligible_t_max'] or 0.5
        self.dp0 = dict(D=50.0, tw=1.0, tcw=0.4, rcin=23.3, a_cover=22.5, t_land=0.5, w_land=1.0, t_in=1.0, t_out=1.0,
                        t_w=self.t_w, h_pod=0.0)
        dp0 = self.dp0
        self.f = dict(od=fast(sp.od(dp0)), wall=fast(sp.wall(dp0, 1.0)), pack=fast(sp.pack(dp0)), straight=fast(sp.straight(dp0)),
                      tallow=fast(sp.t_allow(dp0)), main=fast(sp.main_case(dp0)), ins_main=fast(sp.insert(dp0, 'MAIN')),
                      ins_bat=fast(sp.insert(dp0, 'BATTERY')), ins_rear=fast(sp.insert(dp0, 'REAR', r_rear=16.4)),
                      cfit=fast(sp.cover_fit(dp0)), cled=fast(sp.cover_ledge(dp0)), pod=fast(sp.pod_residual(dp0)),
                      chg=fast(sp.chg_window(23.0)), btn_h=fast(sp.btn_height(dp0)),
                      cbmin=fast(self.cb_min_spec(1.0, 'H11-CB-MIN-IN')))
        self.f.update({'edge_' + x: fast(sp.edge(dp0, x)) for x in XS})
        self.f.update({'edgez_' + x: fast(sp.edge_z(dp0, x)) for x in XS})
        self.grid = dict(tw=SW['t_wall_side_mm'], tcw=SW['t_carrier_wall_mm'],
                         rcin=frange(SW['R_carrier_inner_mm']['start'], SW['R_carrier_inner_mm']['stop'], SW['R_carrier_inner_mm']['step']),
                         a=frange(SW['a_cover_mm']['start'], SW['a_cover_mm']['stop'], SW['a_cover_mm']['step']),
                         t_land=SW['t_land_mm'], w_land=SW['w_land_mm'], t_in=SW['t_caseback_in_mm'], t_out=SW['t_caseback_out_mm'],
                         cs=SW['oring_cs_mm'], boss=SW['boss_extension_mm'])
        self.rcin_ok = [r for r in self.grid['rcin'] if self.f['pack'](R_carrier_inner=r) >= -1e-9]
        self.cover_ok = [a for a in self.grid['a'] if self.f['cled'](a_cover=a) >= -1e-9 and sp.cover_plate(dict(dp0, a_cover=a))['pass']]
        self.land = self.land_group()
        self.glands = {}
        for topo in ('radial', 'face'):
            for cs in self.grid['cs']:
                gd = gland_design(st, sp, topo, cs)
                specs = sp.gland('H15-CB', 'static_radial' if topo == 'radial' else 'static_face', gd['cs'], gd['h'], gd['g'], gd['tol_h'], gd['tol_g'])
                gd['margins'] = [run_check(x, full=False) for x in specs]
                gd['pass_'] = min(gd['margins']) >= -1e-9
                self.glands[(topo, cs)] = gd
        bl = st.I['parameters']['bond_lands']['caseback_bond_land_mm']
        self.glands[('adhesive', 0.0)] = dict(topology='adhesive', cs=0.0, h=0.0, g=0.0, tol_h=0.0, tol_g=0.0, land=0.0, spigot_radial=0.0,
                                              spigot_height=0.0, face_annulus=bl['max'], margins=[0.0], pass_=True,
                                              note='bond land requirement (adverse planning max) must fit the midcase rear-face annulus; non-serviceable')
        self.f_per = {h: fast(sp.rear_periphery(dict(dp0, h_pod=0.0), h)) for h in sorted({g['spigot_height'] for g in self.glands.values()})}
        self.pod = {t: self.f['pod'](t_cb_in=t, t_window=self.t_w) for t in self.grid['t_in']}
        self.cbmin = {t: self.f['cbmin'](t_cb=t) for t in sorted(set(self.grid['t_in']) | set(self.grid['t_out']))}
        self.plate_cache = {}
        self.screw_seat = run_check(sp.screw_seat(dp0, cand['screw_class']), full=False)
        self.load_path = load_paths(cand)
        self.btn_f = {sw: fast(sp.bore(dp0, sw, 0.0)) for sw in sorted(st.I['parameters']['buttons']['windows_deg'])}
        bl = button_layout(st, sp, dp0)
        features(st, sp, dict(dp0, w_land=1.0), bl, dict(supports=[], pad_half_deg=0.0, pad_inner_r=23.0), dict(screws=[]), [], 20.0)
        self.pusher_ok = {b['id']: pusher_gland(st, sp, b['id'], b['pusher_requirement']['conductive'])[0]['pass_'] for b in bl}
        self.boss_m = {(sw,b): run_check(sp.boss(sw, b), full=False) for sw in self.btn_f for b in self.grid['boss']}
        P = ctx['lra']
        self.lra_minr = {}
        for cls in st.I['lra_classes']:
            ok = [p['rmax'] for p in P['poses'] if p['cls'] == cls['id'] and not p['viol']]
            self.lra_minr[cls['id']] = min(ok) + P['c_plan'] if ok else None
        self.lra_z = {(cls['id'], t): run_check(sp.lra_z(cls, t), full=False) for cls in st.I['lra_classes'] for t in self.grid['t_out']}
        self.cb_cache = {}

    def cb_min_spec(self, t, sid):
        m = self.sp.m_cb['t_wall_min_mm']
        return spec(sid, 'H11', 'caseback thickness - tol - t_min(caseback material class) >= 0',
                    [Specs.design('t_cb', t), self.sp.tol('tol_t_cb', self.sp.pc_cb['thickness_mm']),
                     Term('t_min_cb', 'SUPPLIER_GATED', 'PROVISIONAL_ASSUMPTION', m['nom'], m['max'], (m['min'], m['max']))],
                    lambda v: v['t_cb'] - v['tol_t_cb'] - v['t_min_cb'], limit_class='PROVISIONAL PLANNING LIMIT')

    def land_group(self):
        best = None
        sp = self.sp
        for w in self.grid['w_land']:
            fu4 = fast(sp.u4(dict(self.dp0, w_land=w)))
            permitted = (0.5 - EPS <= w <= 1.5 + EPS) and (self.st.R_display - w - sp.pc_mid['radius_mm'] >= self.st.R_pol - EPS)
            for t in self.grid['t_land']:
                m = dict(u4=fu4(t_land=t), btn_h=self.f['btn_h'](t_land=t), **{'edgez_' + x: self.f['edgez_' + x](t_land=t) for x in XS})
                ok = permitted and min(m.values()) >= -1e-9
                key = (not ok, -min(m.values()), t, -w)
                if best is None or key < best[0]:
                    best = (key, dict(t_land=t, w_land=w, ok=ok, margins=m, permitted=permitted))
        return best[1]

    def side(self, D):
        rows = {}
        for tw in self.grid['tw']:
            wall = min(self.f['wall'](t_wall=tw), run_check(self.sp.local_wall(dict(self.dp0, tw=tw)), full=False))
            R = D / 2 - tw
            best = None
            for tcw in self.grid['tcw']:
                if run_check(self.sp.carrier_wall(dict(self.dp0, tcw=tcw)), full=False) < -EPS:
                    continue
                for rc in self.rcin_ok:
                    m = dict(straight=self.f['straight'](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw),
                             tallow=self.f['tallow'](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw),
                             main=self.f['main'](R_side=R), ins_main=self.f['ins_main'](R_side=R),
                             ins_bat=self.f['ins_bat'](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw))
                    m.update({'edge_' + x: self.f['edge_' + x](R_side=R, R_carrier_inner=rc, t_carrier_wall=tcw) for x in XS})
                    key = (-min(m.values()), tcw, rc)
                    if best is None or key < best[0]:
                        best = (key, dict(tcw=tcw, rcin=rc, margins=m))
            b = best[1]
            b['wall'] = wall
            b['min_margin'] = min(list(b['margins'].values()) + [wall])
            b['ok'] = b['min_margin'] >= -1e-9
            rows[tw] = b
        return rows

    def caseback_R(self, R):
        """Caseback group at bore radius R (independent of D otherwise, except the face-seal annulus)."""
        key = round(R, 6)
        if key in self.cb_cache:
            return self.cb_cache[key]
        st, sp = self.st, self.sp
        tolr = sp.pc_env['radius_mm']
        recs = []
        for (topo, cs), gd in sorted(self.glands.items()):
            r_lim = (R - tolr) if topo in ('face', 'adhesive') else (R - gd['spigot_radial'] - sp.pc_cb['radius_mm'])
            r_out = min(st.res['CHG_CONTACT']['radial_mm'][1], r_lim - st.I['parameters']['c_chg_window_mm']['max'])
            chg = self.f['chg'](r_out=r_out)
            ins_rear = self.f['ins_rear'](R_side=R, r_rear_module=max(st.s14geo['outline_r'], r_out))
            for t_in in self.grid['t_in']:
                for t_out in self.grid['t_out']:
                    amax = plate_amax(st, sp, t_in, t_out, self.plate_cache)
                    plate = (amax - (R + tolr)) if amax is not None else -99.0
                    m = dict(pod=self.pod[t_in], periphery=self.f_per[gd['spigot_height']](t_cb_out=t_out), gland=(min(gd['margins']) * cs) if topo != 'adhesive' else 0.0,
                             cb_min_in=self.cbmin[t_in], cb_min_out=self.cbmin[t_out], plate=plate, chg=chg, ins_rear=ins_rear)
                    lra = {c: (self.lra_z[(c, t_out)] >= -1e-9 and self.lra_minr[c] is not None and self.lra_minr[c] <= r_lim + 1e-9)
                           for c in self.lra_minr}
                    recs.append(dict(topology=topo, cs=cs, t_in=t_in, t_out=t_out, margins=m, r_lim=r_lim, chg_r_out=r_out, plate_amax=amax,
                                     lra=lra, lra_ok=any(lra.values()), h_pod_max=min(self.pod[t_in], m['periphery'])))
        self.cb_cache[key] = recs
        return recs

    def caseback(self, D, tw):
        sp = self.sp
        R = D / 2 - tw
        best = bestx = None
        for rec in self.caseback_R(R):
            m = dict(rec['margins'])
            if rec['topology'] in ('face', 'adhesive'):
                m['annulus'] = tw - sp.pc_mid['od_radius_mm'] - sp.pc_mid['radius_mm'] - self.glands[(rec['topology'], rec['cs'])]['face_annulus']
            ok = min(m.values()) >= -1e-9
            key = (not ok, -min(m.values()), rec['t_in'], rec['t_out'], rec['cs'], rec['topology'])
            r = dict(rec, margins=m, ok=ok)
            if ok and rec['lra_ok'] and (best is None or key < best[0]):
                best = (key, r)
            if bestx is None or key < bestx[0]:
                bestx = (key, r)
        return (best[1] if best else None), bestx[1]

    def buttons(self, D):
        out = {}
        for sw, fb in self.btn_f.items():
            chosen = None
            for b in self.grid['boss']:
                bore = fb(D=D, boss=b)
                if bore >= -1e-9 and self.boss_m[(sw,b)] >= -1e-9:
                    chosen = dict(boss=b, bore_margin=bore, boss_margin=self.boss_m[(sw,b)], ok=True)
                    break
            if chosen is None:
                cand = [(min(fb(D=D, boss=b), self.boss_m[(sw,b)]), b) for b in self.grid['boss'] if self.boss_m[(sw,b)]>=-EPS]
                m, b = max(cand)
                chosen = dict(boss=b, bore_margin=fb(D=D, boss=b), boss_margin=self.boss_m[(sw,b)], ok=False)
            out[sw] = chosen
        return out

    def at(self, D):
        od = self.f['od'](D=D)
        side = self.side(D)
        cover = max([(self.f['cfit'](D=D, a_cover=a), -a) for a in self.cover_ok], default=(-99.0, 0.0))
        ok_tw = [tw for tw in sorted(side) if side[tw]['ok']]
        wall_valid=[tw for tw in sorted(side) if side[tw]['wall']>=-EPS]
        tws = ok_tw or [max(wall_valid or sorted(side), key=lambda t: (side[t]['min_margin'], -t))]
        full = bestx = None
        for tw in tws:
            a, b = self.caseback(D, tw)
            if a is not None and full is None:
                full = (tw, a)
            if bestx is None or (not bestx[1]['ok'] and b['ok']) or \
                    (b['ok'] == bestx[1]['ok'] and min(b['margins'].values()) > min(bestx[1]['margins'].values()) + 1e-12):
                bestx = (tw, b)
        btn = self.buttons(D)
        groups = dict(H03_OD=od >= -1e-9, SIDE_RADIAL=bool(ok_tw), COVER=cover[0] >= -1e-9, LAND=self.land['ok'],
                      CASEBACK=bestx[1]['ok'], LRA=full is not None, BUTTONS=all(v['ok'] for v in btn.values()) and all(self.pusher_ok.values()),
                      SCREWS=self.screw_seat >= -1e-9, LOAD_PATH=self.load_path['pass_'])
        return dict(D=D, feasible=False, feasible_excluding_H22=False, pre_screen_groups=dict(groups),
                    screen_groups_pass=all(groups.values()),
                    groups=groups, failing_groups=sorted(k for k, v in groups.items() if not v), od_margin=od,
                    side=side, tw_feasible=ok_tw, cover_fit=cover[0], a_cover=-cover[1] if self.cover_ok else None,
                    caseback=bestx, caseback_full=full, buttons=btn)

    def sweep(self, d_values):
        return [self.at(D) for D in d_values]


# --------------------------------------------------------------------------------------------
# Full evaluation of one design point (every check at every section 6.3 evaluation)
# --------------------------------------------------------------------------------------------
def design_point(ce, row):
    tw, cb = row['caseback']
    s = row['side'][tw]
    return dict(D=row['D'], tw=tw, tcw=s['tcw'], rcin=s['rcin'], a_cover=row['a_cover'], t_land=ce.land['t_land'], w_land=ce.land['w_land'],
                t_w=ce.t_w, h_pod=0.0, t_in=cb['t_in'], t_out=cb['t_out'], seal_topology=cb['topology'], seal_cs=cb['cs'],
                r_lim=cb['r_lim'], chg_r_out=cb['chg_r_out'], bosses={k: v['boss'] for k, v in row['buttons'].items()},
                window_variant=(ce.window['eligible_variants'] or ['none'])[0])


def evaluate_design(st, ce, dp, poses):
    sp, c = ce.sp, ce.c
    checks = []

    def add(s):
        checks.append(fix_pass(run_check(s, full=True)))
    add(sp.od(dp))
    for sw, b in sorted(dp['bosses'].items()):
        s = sp.boss(sw, b)
        add(s)
        add(sp.bore(dp, sw, b))
    add(sp.wall(dp, dp['tw']))
    if c.get('dielectric_sectors'):
        add(sp.local_wall(dp))
    add(sp.carrier_wall(dp))
    add(sp.straight(dp))
    for x in XS:
        add(sp.edge(dp, x))
        add(sp.edge_z(dp, x))
    add(sp.t_allow(dp))
    add(sp.main_case(dp))
    for kind in ('flat', 'ceiling'):
        r = fix_pass(run_check(sp.edge_bound(dp, kind), full=True))
        r['hard'] = 'INFO'
        r['pass'] = None
        checks.append(r)
    add(sp.insert(dp, 'MAIN'))
    add(sp.insert(dp, 'BATTERY'))
    add(sp.insert(dp, 'REAR', r_rear=max(st.s14geo['outline_r'], dp['chg_r_out'])))
    add(sp.cover_fit(dp))
    add(sp.cover_ledge(dp))
    add(sp.u4(dp))
    add(sp.btn_height(dp))
    add(sp.pack(dp))
    add(sp.pod_residual(dp))
    add(ce.cb_min_spec(dp['t_in'], 'H11-CB-MIN-IN'))
    add(ce.cb_min_spec(dp['t_out'], 'H11-CB-MIN-OUT'))
    gd = ce.glands[(dp['seal_topology'], dp['seal_cs'])]
    add(sp.rear_periphery(dp, gd['spigot_height']))
    if dp['seal_topology'] != 'adhesive':
        for s in sp.gland('H15-CB-MAIN', 'static_radial' if dp['seal_topology'] == 'radial' else 'static_face',
                          gd['cs'], gd['h'], gd['g'], gd['tol_h'], gd['tol_g']):
            add(s)
    if dp['seal_topology'] == 'adhesive':
        add(sp.adhesive_annulus(dp))
    add(sp.window_land())
    for kind in ('stress', 'deflection'):
        add(caseback_plate_spec(st, sp, dp, kind))
    add(sp.chg_window(dp['chg_r_out']))
    add(sp.screw_seat(dp, c['screw_class']))
    for cls in st.I['lra_classes']:
        r=fix_pass(run_check(sp.lra_z(cls,dp['t_out']),full=True))
        r['hard']='INFO'
        checks.append(r)
    return checks


def candidate_report(st, ce, rows, ext_rows, poses, window, retained=None):
    c, sp = ce.c, ce.sp
    allrows = rows + ext_rows
    feas = [r['D'] for r in rows if r['feasible']]
    d_min = feas[0] if feas else None
    od_ok = [r['D'] for r in rows if r['groups']['H03_OD']]
    d_eval = retained['D'] if retained is not None else (d_min if d_min is not None else (od_ok[-1] if od_ok else rows[-1]['D']))
    row = retained if retained is not None else next(r for r in rows if abs(r['D'] - d_eval) < 1e-9)
    dp = design_point(ce, row)
    checks = evaluate_design(st, ce, dp, poses)
    below = next((r for r in rows if abs(r['D'] - (d_eval - 0.05)) < 1e-9), None)
    thresholds = {}
    for g in ([] if retained is not None else rows[0]['groups']):
        ok = [r['D'] for r in allrows if r['groups'][g]]
        thresholds[g] = dict(first_pass_D=ok[0] if ok else None, last_pass_D=ok[-1] if ok else None,
                             d_dependent=len(ok) not in (0, len(allrows)))
    dep = [g for g, t in thresholds.items() if t['d_dependent'] and g != 'H03_OD']
    indep_fail = sorted(g for g, t in thresholds.items() if t['first_pass_D'] is None)
    closure_d = max([thresholds[g]['first_pass_D'] for g in dep if thresholds[g]['first_pass_D'] is not None] + [47.0])
    buttons = button_layout(st, sp, dp)
    vent = vent_layout(st, sp, dp, buttons)
    supports = supports_layout(st, sp, dp, buttons, vent)
    screws = screw_layout(st, sp, dp)
    lugs = lug_layout(st, dp)
    F, diel = features(st, sp, dp, buttons, supports, screws, lugs, dp['chg_r_out'])
    rfm = rf_mag_check(st, F)
    inv = seal_inventory(st, c, dp['window_variant'], len(st.s14geo['cells']), dp['seal_topology'])
    closure = seal_closure(inv, screws_outside=screws['outside_body'])
    charger = charger_fit(st, sp, dp)
    conditionals = conditional_seals(st, sp, dp)
    if vent:
        bv=st.P['bond_lands']
        terms=[sp.design('membrane_radius',vent['membrane_dia_mm']/2),sp.par('port_dia','max',bv['vent_port_dia_mm']),
               sp.par('bond_land','max',bv['vent_membrane_land_mm']),sp.tol('local_radius_tol',sp.pc_env['radius_mm'])]
        checks.append(fix_pass(run_check(spec('H16-VENT-LAND','H16','continuous vent membrane bond land after local process tolerance',terms,
                         lambda v:v['membrane_radius']-v['port_dia']/2-v['local_radius_tol']-v['bond_land']))))
    if c['caseback'].get('split'):
        terms=[sp.design('t_joint',dp['t_in']),sp.tol('thickness_tol',sp.pc_cb['thickness_mm']),
               sp.par('bond_land','max',st.P['bond_lands']['caseback_bond_land_mm'])]
        checks.append(fix_pass(run_check(spec('H16-SPLIT-JOINT','H16','split caseback radial butt-joint available bond height minus planning bond land; no unmodeled lap credited',terms,
                         lambda v:v['t_joint']-v['thickness_tol']-v['bond_land']))))
    h19 = s14_untouched(st, F, dp)
    h24 = support_check(st, sp, dp, supports)
    btn_x = button_extras(st, dp, buttons)
    pusher = {}
    for b in buttons:
        best, _ = pusher_gland(st, sp, b['id'], b['pusher_requirement']['conductive'])
        for x in best['specs']+button_stack_specs(st,sp,dp,b,best):
            checks.append(fix_pass(run_check(x, full=True)))
        pusher[b['id']] = dict((k, v) for k, v in best.items() if k != 'specs')
        pusher[b['id']]['threshold'] = seal_threshold(st, 'dynamic_radial', best)
    checks.append(charger['best']['check'])
    plate_post = post_load(st, sp, dp)
    lra = lra_report(st, ce, poses, dp)
    r_case_tab = r_case_table(st, sp, dp, buttons, supports)
    h05_geometry = dict(
        radial_edge_geometry_pass=all(x['pass'] for x in checks if x['hard']=='H05'),
        radial_edge_margins_lw={x['id']:x['linear_worst'] for x in checks if x['hard']=='H05'},
        lra_coupled_feasibility=bool(lra['feasible_classes']),
        wall_model_limitation=WALL_MODEL_LIMITATION,
        scope='Geometric margins include the XL-LRA planning crossing; its actual pose/lead route remains LRA-gated. Complete H05 requires both geometry and LRA feasibility.')
    hard = summarize_hard(st, checks, extra=dict(
        H01=st.z_ok and all(x['pass'] for x in checks if x['id'] == 'H01-REAR-PERIPHERY-Z'),
        H02=st.h02['pass'], H04=st.legacy['pass_'], H07=sp.cover_plate(dp)['pass'],
        H08=cover_proud(st, sp, dp)['pass_'], H12=window['h12_pass'],
        H13=ce.load_path['pass_'] and plate_post['case_side_bypass_screen']['pass_'] and bool(window['eligible']) and all(r['deflection_pass'] for r in window['rows'] if r['id'] in window['eligible']),
        H10=ce.load_path['pass_'], H05=bool(lra['feasible_classes']),
        H14=closure['closed'] and screws['outside_body'] and len(screws['screws']) >= st.I['parameters']['screw_count']['min'],
        H16=bool(vent) and bool(window['eligible']) and all(x['land_margin_mm']>=-EPS for x in conditionals if x['id']=='S-POD-FRAME'),
        H17=rfm['h17_pass'] and bool(lra['feasible_classes']), H18=rfm['h18_pass'], H19=h19['pass_'], H20=charger['pass_'],
        H15=all(x['pass_'] for x in conditionals if x['id']=='S-POD-FRAME'),
        H03=not bosses_permitted(st, r_case_tab, dp['D'], sp.pc_mid['boss_mm']),
        H21=all(b['boss_in_window'] for b in buttons) and btn_x['pass_'],
        H22=bool(lra['feasible_classes']), H23=st.assembly['pass_'], H24=h24['pass_'], H25=st.scope['pass_']))
    evidence = dict(H01=dict(baselines=st.z_ok, local_stack=next(x for x in checks if x['id']=='H01-REAR-PERIPHERY-Z')),
                    H02=st.h02, H04=st.legacy['rows'], H05=h05_geometry, H07=sp.cover_plate(dp), H08=cover_proud(st,sp,dp),
                    H10=ce.load_path, H12=dict(eligible=window['eligible']), H13=plate_post,
                    H14=closure, H15=dict(conditionals=conditionals), H16=dict(vent=vent,window=window['eligible']),
                    H17=rfm, H18=rfm, H19=h19, H20=charger,
                    H21=btn_x, H22=lra, H23=st.assembly, H24=h24, H25=st.scope)
    for hid in hard:
        hard[hid]['evidence']['geometry'] = evidence.get(hid, dict(source='metric rows'))
    if retained is not None:
        # Every retained point records every predicate before any eligibility/ranking decision.
        hard_compact={h:dict(pass_=v['pass'], failing=v['failing'],
                            margins={x['id']:[x['nominal'],x['rss'],x['linear_worst']] for x in checks if x['hard']==h},
                            predicate=v['evidence']['additional_predicate']) for h,v in hard.items()}
        return dict(candidate=c['id'],D=dp['D'],design_point=dp,hard_checks=hard_compact,
                    feasible=complete_candidate(hard),geometry_evidence={k:v for k,v in evidence.items() if k not in ('H01','H02','H04','H23','H25')},
                    shared_evidence={'H01':'carry_in.g2_stacks + H01-REAR margin','H02':'z','H04':'carry_in.legacy','H23':'assembly','H25':'scope'},
                    evaluation_policy='LEGACY in carry_in; numeric vectors NOMINAL/RSS/LINEAR WORST; terms/limits in candidate detail; owner options uncredited')
    gd=ce.glands[(dp['seal_topology'],dp['seal_cs'])]
    acceptable = d_min is not None and all(h['pass'] for h in hard.values())
    return dict(id=c['id'], title=c['title'], pod_concept=c['pod_concept'], midcase=c['midcase'], caseback=c['caseback'],
                dielectric_sectors=diel, D_min_feasible=d_min, D_eval=d_eval,
                D_eval_rule='D_min_feasible' if d_min is not None else 'largest grid diameter passing H03 (most favourable permitted diameter; diagnostic)',
                governing_below=None if below is None else dict(D=below['D'], failing_groups=below['failing_groups']),
                independent_group_thresholds={g:min((r['D'] for r in allrows if r['pre_screen_groups'][g]),default=None) for g in allrows[0]['pre_screen_groups']},
                button_bore_only_threshold_D=min((r['D'] for r in allrows if all(b['ok'] for b in r['buttons'].values())),default=None),
                group_thresholds=thresholds, d_dependent_closure_D=closure_d, d_independent_failures=indep_fail,
                design_point=dp, checks=checks, hard_checks=hard, acceptable=acceptable,
                h05_diagnostics=h05_geometry, battery_carrier_gates=battery_carrier_gates(st),
                rear_z=rear_z_investigation(st,ce,dp), cover_plate=sp.cover_plate(dp), cover_top=cover_proud(st,sp,dp), charger=charger, conditional_seals=conditionals,
                layout=dict(buttons=buttons, vent=vent, supports=supports, screws=screws, lugs=lugs, button_checks=btn_x,
                            pusher_glands=pusher, features=[dict(id=f['id'], kind=f['kind'], z=f['z'], conductive=f['conductive'],
                                                                ferromagnetic=f['ferromagnetic'], geom=f['geom']) for f in F]),
                rf_mag=rfm, seal_inventory=inv, seal_closure=closure, s14_untouched=h19, supports_check=h24,
                load_path=ce.load_path, post_load=plate_post, lra=lra,
                caseback_seal=dict(threshold=seal_threshold(st,'static_radial' if dp['seal_topology']=='radial' else 'static_face',gd) if dp['seal_topology']!='adhesive' else None, topology=dp['seal_topology'], gland=dict((k, v) for k, v in ce.glands[(dp['seal_topology'], dp['seal_cs'])].items() if k != 'margins'),
                                   options=[dict(topology=k[0], cs=k[1], h=v['h'], g=v['g'], tol_h=v['tol_h'], min_margin=min(v['margins']),
                                                 pass_=v['pass_'], spigot_height=v['spigot_height'], face_annulus=v['face_annulus'])
                                            for k, v in sorted(ce.glands.items())]),
                h_pod=dict(nominal=next(x['nominal'] for x in checks if x['id'] == 'H11-POD-RESIDUAL'),
                           linear_worst_max=min(next(x['linear_worst'] for x in checks if x['id'] == 'H11-POD-RESIDUAL'),
                                                next(x['linear_worst'] for x in checks if x['id'] == 'H01-REAR-PERIPHERY-Z')),
                           note='h_pod is an output: range [0, max] with the caseback plane designed from the REAR skin-face datum; closure is MEASUREMENT (wrist / strap trials)'),
                sweep=[dict(D=r['D'], feasible=r['feasible'], feasible_excluding_H22=r['feasible_excluding_H22'], failing_groups=r['failing_groups'],
                            hard_results={h:v['pass_'] for h,v in r.get('full_hard_checks',{}).items()},
                            od_margin=r['od_margin'], tw_feasible=r['tw_feasible'], cover_fit=r['cover_fit'],
                            caseback_min_margin=min(r['caseback'][1]['margins'].values()), caseback_plate_ok=r['caseback'][1]['margins']['plate'] >= -1e-9,
                            buttons_min_bore=min(v['bore_margin'] for v in r['buttons'].values()))
                       for r in allrows],
                r_case=r_case_tab, unpermitted_protrusions=bosses_permitted(st, r_case_tab, dp['D'], sp.pc_mid['boss_mm']),
                main_outline=main_outline(st, sp, dp, supports))


def summarize_hard(st, checks, extra):
    out = {}
    for hid, (title, req, lim) in sorted(HARD.items()):
        mine = [x for x in checks if x['hard'] == hid]
        ok = all(x['pass'] for x in mine) if mine else hid in extra
        if hid in extra:
            ok = ok and bool(extra[hid])
        failing = [x['id'] for x in mine if not x['pass']]
        out[hid] = dict(title=title, required_evaluation=req, limit_class=lim, pass_=ok, failing=failing,
                        spec_checks=[x['id'] for x in mine],
                        evidence=dict(metrics=[dict(id=x['id'], nominal=x['nominal'], rss=x['rss'], linear_worst=x['linear_worst'], pass_=x['pass']) for x in mine],
                                      additional_predicate=extra.get(hid), source='candidate geometry and pinned carry-ins'))
    for v in out.values():
        v['pass'] = v.pop('pass_')
    return out


def button_extras(st, dp, buttons):
    rows = []
    riser = res_az(st, 'G2-J202-WEST-F.Cu-1')
    appr = tuple(st.res['CHG_APPROACH']['geometry']['az'])
    for b in buttons:
        arc = ((b['centre'] - b['half_bore_deg']) % 360, (b['centre'] + b['half_bore_deg']) % 360)
        r = dict(id=b['id'], centre_deg=b['centre'], bore_arc_deg=arc, boss_half_deg=b['boss_half_deg'], boss_in_window=b['boss_in_window'],
                 gap_chg_riser_deg=arc_gap(arc, riser), gap_chg_approach_deg=arc_gap(arc, appr),
                 radial_gap_disp_fpc_mm=b['r_in'] - st.res['DISP_FPC']['geometry']['r'][1],
                 pusher=b.get('pusher_requirement'), installed_after_module=True)
        r['pass_'] = r['boss_in_window'] and r['gap_chg_riser_deg'] > 0 and r['radial_gap_disp_fpc_mm'] > 0
        rows.append(r)
    return dict(rows=rows, pass_=all(r['pass_'] for r in rows),
                note='Bores at the centre of the frozen G2 azimuth windows; bosses confined to their own window; no generic boss-width rule; '
                     'pushers inserted radially after module insertion (H23); pusher material requirement derived from radiator / MAG_CLEAR overlap.')


def s14_untouched(st, F, dp):
    g = st.s14geo
    regions = [('S14_OUTLINE', dict(type='circles', circles=[[100.0, 100.0, g['outline_r']]])),
               ('S14_POD', dict(type='poly', pts=g['pod'])), ('S14_TAIL_CONSERVATIVE', dict(type='poly', pts=g['tail_cons'])),
               ('S14_TAIL_RELIEF', dict(type='poly', pts=g['tail_relief_cons'])), ('S14_THERMODE', dict(type='poly', pts=g['thermode'])),
               ('S14_U6_ISLAND', dict(type='poly', pts=g['u6_island']))] + \
              [('S14_SUPPORT_%d' % s['az'], dict(type='poly', pts=s['poly'])) for s in g['supports']]
    hits = []
    for f in F:
        if 'REAR' not in f['z'] or f['kind'] in ('hard-stop post', 'caseback centre plate'):
            continue
        for rid, rg in regions:
            if overlaps(f['geom'], rg):
                hits.append(dict(feature=f['id'], region=rid))
    gap = (dp['r_lim'] - g['outline_r'])
    return dict(pass_=not hits and all(x['valid'] for x in g['frames']), intrusions=hits, frames_valid=all(x['valid'] for x in g['frames']),
                spigot_or_bore_gap_to_outline_mm=gap,
                posts=[dict(az=s['az'], land=s['poly'], note='frozen reservation preserved; no global pressure assigned') for s in g['supports']],
                note='REAR-level G4 features vs the frozen S14 outline, pod, conservative tail corridor, strain relief, thermode keepout, U6 '
                     'island and support lands. Caseback plate and pod frame lie below the REAR skin face (c_cb_rear) and are Z-separated.')


def support_check(st, sp, dp, sup):
    placed = [s for s in sup['supports'] if s['placement']]
    rch = dp['rcin'] + sp.pc_car['radius_mm'] + dp['tcw'] + sp.pc_car['thickness_mm']
    post_r_in = rch + st.I['parameters']['c_insert_mm']['max']
    wn = next(s for s in sup['supports'] if s['id'] == 'SUP_WNW')
    radial_room=dp['D']/2-dp['tw']-sp.pc_env['radius_mm']-post_r_in
    ok = radial_room > EPS and len(placed) >= 4 and wn['placement'] is not None and post_r_in >= rch - EPS and sup['pads'] >= 3 and sup['largest_pad_arc_deg'] < 180.0
    return dict(pass_=ok, post_radial_room_mm=radial_room, count=len(placed), pads=sup['pads'], largest_pad_arc_deg=sup['largest_pad_arc_deg'],
                pad_less=[s['id'] for s in placed if not s['placement']['pad']], w_nw=wn['placement'], post_inner_radius_mm=post_r_in, R_channel_inner_lw_mm=rch,
                pad_inner_radius_mm=sup['pad_inner_r'], largest_unsupported_arc_deg=sup['largest_unsupported_arc_deg'],
                legacy_largest_unsupported_arc_deg=sup['legacy_largest_unsupported_arc_deg'],
                note='Front-gap stop pads engage the MAIN F.Cu edge (F.Cu keep-out arcs for K1); carrier / case support posts at BATTERY level '
                     'stay outside R_channel_inner (X18) and outside every G2 riser.')


def lra_local_exclusions(st, ce, dp):
    sp=ce.sp
    buttons=button_layout(st,sp,dp)
    vent=vent_layout(st,sp,dp,buttons)
    supports=supports_layout(st,sp,dp,buttons,vent)
    F,_=features(st,sp,dp,buttons,supports,screw_layout(st,sp,dp),lug_layout(st,dp),dp['chg_r_out'])
    ex=[(f['id'],f['geom']) for f in F if 'REAR' in f['z'] and f['kind'] in ('case-side support','charger contacts','charger aperture and land','caseback screw','new wiring')]
    # Bores are excluded in plan conservatively even when their final Z lies above the actuator.
    ex += [(b['id']+'_BORE',b['bore_geom']) for b in buttons]
    ex += [(b['id']+'_BOSS',b['boss_geom']) for b in buttons]
    ex.append(('CASEBACK_SEAL_STRUCTURE',sector(0,360,dp['r_lim'],dp['D']/2)))
    ex.append(('POD_SEAL_FRAME',dict(type='circles',circles=[[100,100,st.s14geo['pod_r_max']+st.P['w_pod_frame_mm']['nom']+sp.pc_cb['radius_mm']]])))
    ex.append(('LRA_LEAD_EXIT_RESERVED',st.g2res['G2-U7-B.Cu-1']['geometry']))
    return ex


def pose_envelope(st, pose):
    cls=next(c for c in st.I['lra_classes'] if c['id']==pose['cls'])
    centre=xy(pose['r'],pose['az'])
    if cls['shape']=='coin': return [(centre,cls['diameter_mm']['max']/2)]
    ang=pose['az']-90+(90 if pose['ori']==0 else 0)
    return rect_cover(centre,cls['length_mm']['max'],cls['width_mm']['max'],ang)


def local_pose_violations(st, ce, dp, env, ex=None):
    ex=lra_local_exclusions(st,ce,dp) if ex is None else ex
    clearance=st.P['c_lra_plan_mm']['max']
    required={'SW%d_BORE'%i for i in range(1,6)} | {'CHG_CONTACT_BLOCK','CASEBACK_SEAL_STRUCTURE','POD_SEAL_FRAME','LRA_LEAD_EXIT_RESERVED'}
    missing=sorted(required-{name for name,g in ex})
    if missing: return ['MISSING_EXCLUSION:'+name for name in missing]
    return [name for name,g in ex if min(circle_clear(p,rho,g) for p,rho in env)<clearance-EPS]


def maximum_actuator(st,ce,dp):
    """Maximum circular envelope on the authorized centre grid, no actuator existence claim."""
    ex=lra_exclusions(st)+lra_local_exclusions(st,ce,dp)
    clearance=st.P['c_lra_plan_mm']['max']
    best=None
    for az in range(0,356,st.I['lra_search']['az_step_deg']):
        for radius in frange(12,26,st.I['lra_search']['r_step_mm']):
            if radius>=dp['r_lim']-clearance or radius<=st.s14geo['outline_r']+clearance: continue
            centre=xy(radius,az)
            rho=min([dp['r_lim']-radius]+[pt_region(centre,g) for _,g in ex])-clearance
            key=(rho,math.dist(centre,st.u703),-az,-radius)
            if best is None or key>best[0]: best=(key,centre,az,radius)
    z=st.rear_alloc_min()-dp['t_out']-ce.sp.pc_cb['thickness_mm']-st.tolpol['t_lower_web']-st.P['c_lra_top_mm']['max']-st.P['lra_mount_mm']['max']
    if best is None or best[0][0]<=0: return dict(maximum_coin_diameter_mm=0.,height_mm=z,pose=None,existence_claim=False)
    return dict(maximum_coin_diameter_mm=2*best[0][0],height_mm=z,
                pose=dict(az=best[2],r=best[3],u703_distance_mm=math.dist(best[1],st.u703)-best[0][0]),
                inscribed_square_side_mm=math.sqrt(2)*best[0][0],
                domain='maximum coin over authorized azimuth/radius grid for this candidate geometry; square is a guaranteed inscribed rectangle, not maximum rectangle',
                lead_status='Existing U7 lead/exit reservations excluded; a connecting lead route has not been qualified',
                existence_claim=False)


def lra_report(st, ce, poses, dp):
    c_plan = poses['c_plan']
    r_lim = dp['r_lim']
    local_ex=lra_local_exclusions(st,ce,dp)
    out = dict(classes=[], feasible_classes=[], exclusions=poses['exclusions']+[e[0] for e in local_ex],
               approximation='Coins exact; rectangles use a superset union of circles (bulge <=3.1% of half width); plan false negatives possible, no impossibility proof beyond finite classes/grid.',
               c_plan_mm=c_plan, r_limit_mm=r_lim,
               t_cb_out_mm=dp['t_out'], z_model='REAR allocation (lower-web underside to the pod outer plane, caseback locally flush with '
                                                 'the pod plane = most permissive geometry without a T_total change) minus caseback, clearances and mount',
               historical='az 165-195, r 12.65-22.00 REAR (invalid, E-G4-02)',
               battery_projection=dict(z_overlapping=False, minimum_separation_mm=st.layer('lower_web')-st.tolpol['t_lower_web']+st.P['c_lra_top_mm']['min'],
                                       reason='Pack ends above lower web; actuator top remains below lower-web underside; negative Z mutation rejected'))
    for cls in st.I['lra_classes']:
        mine = poses.get('by_class',{}).get(cls['id'])
        if mine is None: mine=[p for p in poses['poses'] if p['cls']==cls['id']]
        plan = [p for p in mine if not p['viol'] and p['rmax'] + c_plan <= r_lim + 1e-9
                and not local_pose_violations(st,ce,dp,pose_envelope(st,p),local_ex)]
        z = fix_pass(run_check(ce.sp.lra_z(cls, dp['t_out']), full=True))
        P = st.I['parameters']
        budget = st.rear_alloc_min() - dp['t_out'] - ce.sp.pc_cb['thickness_mm'] - st.tolpol['t_lower_web']
        band_ok = lra_z_band(st, P['c_lra_top_mm']['max'], cls['height_mm']['max'] + P['lra_mount_mm']['max'], budget)
        feas = plan if (z['pass'] and band_ok) else []
        by_az = {}
        for p in ([] if SWEEP_MODE else mine):
            if p['viol'] == ['S14_OUTLINE'] or p['rmin'] > r_lim:
                continue
            extra = ['OUTER_LIMIT (seal spigot / bore)'] if p['rmax'] + c_plan > r_lim + 1e-9 else []
            if not p['viol'] and not extra:
                extra += local_pose_violations(st,ce,dp,pose_envelope(st,p),local_ex)
            by_az.setdefault(p['az'], set()).update(p['viol'] + extra)
        windows = {}
        for p in plan:
            w = windows.setdefault(p['az'], [p['r'], p['r']])
            w[0], w[1] = min(w[0], p['r']), max(w[1], p['r'])
        best = None
        for p in feas:
            key = (-p['u703'], p['az'], p['r'], p['ori'] or 0)
            if best is None or key < best[0]:
                best = (key, p)
        tmin = ce.sp.m_cb['t_wall_min_mm']['max'] + ce.sp.pc_cb['thickness_mm']
        best_z = fix_pass(run_check(ce.sp.lra_z(cls, tmin), full=True))
        rec = dict(id=cls['id'], shape=cls['shape'], envelope_max={k: v['max'] for k, v in cls.items() if isinstance(v, dict)},
                   z_margin_lw_at_material_minimum_caseback=best_z['linear_worst'],
                   max_height_for_zero_margin_at_material_minimum_caseback_mm=next((x['value'] for x in best_z['supplier_zero_margin']
                                                                                  if x['term'] == 'lra_height'), None),
                   poses_evaluated=len(mine), plan_feasible_poses=len(plan), z_check=z, z_margin_lw=z['linear_worst'], z_band_below_lower_web=band_ok,
                   max_height_for_zero_margin_mm=next((x['value'] for x in z['supplier_zero_margin'] if x['term'] == 'lra_height'), None),
                   plan_window_az_r=[dict(az=a, r_min=v[0], r_max=v[1]) for a, v in sorted(windows.items())],
                   feasible_poses=len(feas), recommended_pose=None if best is None else dict(az=best[1]['az'], r=best[1]['r'], orientation=best[1]['ori'],
                                                                                              u703_distance_mm=best[1]['u703']),
                   blocking_per_azimuth=[dict(az=a, blockers=sorted(v)) for a, v in sorted(by_az.items())])
        out['classes'].append(rec)
        if feas:
            out['feasible_classes'].append(cls['id'])
    if not SWEEP_MODE:
        out['maximum_compatible_envelope']=maximum_actuator(st,ce,dp)
    return out


def r_case_table(st, sp, dp, buttons, supports):
    R = dp['D'] / 2
    side = R - dp['tw']
    pc = st.G1in['plate_check']
    rec = dp['a_cover'] + pc['w_cover_land_mm']['max'] + sp.pc_cov['radius_mm'] + st.I['parameters']['c_cover_recess_mm']['max']
    land_in = st.R_display - dp['w_land']
    rows = []
    for az in range(0, 360, 5):
        boss = 0.0
        for b in buttons:
            if arc_has(az, b['centre'] - b['boss_half_deg'], b['centre'] + b['boss_half_deg']):
                boss = dp['bosses'][b['id']]
        stop = post = False
        for s_ in supports['supports']:
            pl = s_['placement']
            if pl and arc_has(az, pl['centre'] - supports['pad_half_deg'], pl['centre'] + supports['pad_half_deg']):
                post = True
                stop = stop or pl['pad']
        rch = dp['rcin'] + sp.pc_car['radius_mm'] + dp['tcw'] + sp.pc_car['thickness_mm'] + st.I['parameters']['c_insert_mm']['max']
        rows.append(dict(az=az, COVER=[rec, R], DISPLAY=[dp['a_cover'], R], LAND=[land_in, R], FRONT_GAP=[supports['pad_inner_r'] if stop else side, R + boss],
                         MAIN=[side, R], BATTERY=[rch if post else side, R], REAR=[side, R], CASEBACK=[dp['r_lim'], R]))
    return dict(wall_model_limitation=WALL_MODEL_LIMITATION, levels=['COVER', 'DISPLAY', 'LAND', 'FRONT_GAP', 'MAIN', 'BATTERY', 'REAR', 'CASEBACK'], rows=rows,
                note='[inner, outer] design radii per Z level: COVER = cover recess, DISPLAY = cover-ledge / display pocket, LAND = display support land '
                     '(t_land at the top of the front gap), FRONT_GAP = bore or MAIN stop pad; outer includes the permitted button bosses (pusher axis in '
                     'the front gap) only; BATTERY = bore or support post; CASEBACK = seal-spigot / bore limit.')


def main_outline(st, sp, dp, supports):
    side_lw = dp['D'] / 2 - dp['tw'] - sp.pc_mid['radius_mm']
    lim = side_lw - sp.pc_pcb['radius_mm'] - st.I['parameters']['c_main_case_mm']['max']
    r = min(st.R_main, lim)
    pts = [xy(r, a) for a in range(0, 360, 2)]
    keep = []
    for s in supports['supports']:
        if s['placement'] and s['placement']['pad']:
            a = s['placement']['centre']
            keep.append(dict(id=s['id'] + '_PAD', az=[a - supports['pad_half_deg'], a + supports['pad_half_deg']],
                             r=[supports['pad_inner_r'] - st.I['parameters']['supports']['fcu_clearance_mm'], st.R_main],
                             rule='F.Cu keep-out (no component) under the front-gap stop pad'))
    return dict(radius_mm=r, polygon=pts, capped_by_development_envelope=r >= st.R_main - EPS, fcu_keepouts=keep,
                note='MAXIMUM permitted MAIN outline for K1 (constraint polygon, not Edge.Cuts); notches are not required by the evaluated '
                     'case section; K1 outline + routing tolerance must stay inside.')


# --------------------------------------------------------------------------------------------
# Global analyses: Z (H01 / H02), assembly (H23), scope (H25)
# --------------------------------------------------------------------------------------------
def z_compliance(st, window, extra_delta=0.0):
    lim = st.I['contract_values']['owner_limits']
    rows = {}
    for b, z in sorted(st.z.items()):
        d = extra_delta
        rows[b] = dict(nominal=z['reproduced']['nominal'] + d, rss=z['reproduced']['rss'] + d, linear=z['reproduced']['linear'] + d,
                       g4_delta=d, headroom_nominal=lim['nominal_mm'] - z['reproduced']['nominal'] - d,
                       headroom_rss=lim['rss_mm'] - z['reproduced']['rss'] - d)
        rows[b]['pass'] = rows[b]['nominal'] <= lim['nominal_mm'] + 1e-9 and rows[b]['rss'] <= lim['rss_mm'] + 1e-9
    w0 = [r for r in window['rows'] if r['variant'] == 'W0' and r['stress_pass']]
    w0_case = None
    if w0:
        dz = min(r['z_delta_mm'] for r in w0)
        w0_case = {b: dict(nominal=st.z[b]['reproduced']['nominal'] + dz, rss=st.z[b]['reproduced']['rss'] + dz,
                           pass_=st.z[b]['reproduced']['nominal'] + dz <= lim['nominal_mm'] + 1e-9) for b in st.z}
    return dict(rows=rows, pass_=all(r['pass'] for r in rows.values()), g4_z_delta_mm=dict(nominal=extra_delta, rss=extra_delta, linear=extra_delta),
                g3_delta_mm=st.I['contract_values']['g3_delta_mm'], w0_thick_window_case=w0_case,
                rule='G4 adds no Z layer; window deltas are applied only when positive (a thinner window is never credited); every X22 budget '
                     'line is assigned to an existing layer (H01-REAR-PERIPHERY-Z) or reported as a Z delta.')


ASSEMBLY_RULES = {
    'A2': dict(not_installed=['MODULE'], installed=[]),
    'A4': dict(not_installed=[], installed=['REAR']),
    'A5': dict(not_installed=['CASEBACK'], installed=[]),
    'A6': dict(not_installed=['CASEBACK', 'PUSHER'], installed=['MODULE_BUILT']),
    'A7': dict(not_installed=['COVER'], installed=['MODULE']),
    'A8': dict(not_installed=[], installed=['DISPLAY']),
    'A9': dict(not_installed=[], installed=['MODULE']),
    'A10': dict(not_installed=['CASEBACK'], installed=['MODULE']),
    'A11': dict(not_installed=[], installed=['MODULE', 'COVER', 'PUSHER']),
}


def assembly_check(st, order=None, lra_feasible=False):
    steps = {s['id']: s for s in st.I['assembly']['steps']}
    order = order or [s['id'] for s in st.I['assembly']['steps']]
    done = set()
    issues = []
    rows = []
    produced = {'A1': ['CASEBACK_SUB'], 'A2': ['VENT'], 'A3': ['REAR'], 'A4': ['MODULE_BUILT'], 'A5': ['LRA'], 'A6': ['MODULE'],
                'A7': ['DISPLAY'], 'A8': ['COVER'], 'A9': ['PUSHER'], 'A10': ['BATTERY_CONNECTED'], 'A11': ['CASEBACK'],
                'C0': ['COVER']}
    for sid in order:
        s = steps.get(sid, dict(id=sid, op='cover bonded in the case sub-assembly (brief-listed order)', part='COVER', direction='-Z from front',
                                battery_state='absent'))
        rule = ASSEMBLY_RULES.get(sid, dict(not_installed=[], installed=[]))
        blocked = [p for p in rule['not_installed'] if p in done]
        missing = [p for p in rule['installed'] if p not in done]
        direction = s['direction']
        dep = None
        if sid == 'A5' and not lra_feasible:
            dep = 'H22: no feasible LRA pose, so the LRA access direction is undefined (counted under H22, not H23)'
            direction = 'undefined (no feasible LRA pose)'
        manip = s['part'] in ('MODULE', 'LRA', 'DISPLAY')
        iso_ok = (not manip) or s['battery_state'] in ('isolated', 'absent')
        ok = not blocked and not missing and iso_ok
        rows.append(dict(id=sid, op=s['op'], direction=direction, battery_state=s['battery_state'], blocked_by=blocked,
                         prerequisites_missing=missing, isolation_ok=iso_ok, dependency=dep, pass_=ok))
        if not ok:
            issues.append(sid)
        done.update(produced.get(sid, []))
    return dict(rows=rows, issues=issues, pass_=not issues)


def assembly_study(st, lra_feasible):
    base = assembly_check(st, lra_feasible=lra_feasible)
    brief_order = ['C0'] + [s['id'] for s in st.I['assembly']['steps']]
    alt = assembly_check(st, order=brief_order, lra_feasible=True)
    j1 = st.I['assembly']['j1_cycles']
    service = ['open caseback (reverse A11)', 'isolate battery (reverse A10)', 'withdraw pushers (reverse A9)',
               'debond cover (reverse A8; bonded pressure boundary, re-bond and re-test required)', 'unmate display at J1 (reverse A7; one J1 cycle)',
               'withdraw module to the rear (reverse A6)', 'demate J1501; replace REAR + bonded tail as one unit', 'reassemble A6-A11 (one J1 cycle)']
    return dict(sequence=base, brief_listed_cover_first=dict(order=brief_order, result=alt,
                finding='A cover bonded before the display cannot coexist with DISP_LAND behind the display: the display must be seated from the '
                        'front (A7) before the cover is bonded (A8). Front insertion before cover bonding is geometrically possible with frozen allocations but changes the binding sequence; clarification required.'),
                service=dict(steps=service, j1_cycles_per_service=2, j1_rated=j1['rated'], j1_planned=j1['planned'],
                             services_within_plan=(j1['planned'] - 1) // 2, gate='SERVICE-COVER-REBOND'),
                pass_=alt['pass_'] and base['pass_'], alternative=base,
                disposition='CONTRACT INTERPRETATION / CLARIFICATION REQUIRED',
                frozen_architecture_change_required=False)


def scope_check(st):
    brief = st.I['baselines']['g4_brief_path']
    intro = git('log', '--diff-filter=A', '--format=%H', '--', brief).stdout.split()
    base3 = st.I['baselines']['g3']
    res = {}
    res['g4_brief_commit_found'] = bool(intro)
    res['g4_brief_unchanged'] = bool(intro) and git('diff', '--quiet', intro[-1], '--', brief).returncode == 0
    res['g1_g2_g3_immutables_unchanged'] = git('diff', '--quiet', base3, '--', *G3_IMMUTABLE).returncode == 0
    res['kicad_interfaces_placement_unchanged'] = git('diff', '--quiet', base3, '--', '*.kicad_pcb', '*.kicad_sch', '*.kicad_pro',
                                                      '*.kicad_prl', 'design/interfaces', 'design/placement', 'rear_sensor',
                                                      'libraries').returncode == 0
    outside = [p for p in git('diff', '--name-only', base3, '--', '.', ':(exclude)design/mechanical/**').stdout.split() if p]
    untracked = [p for p in git('ls-files', '--others', '--exclude-standard').stdout.split() if p]
    res['nothing_outside_design_mechanical'] = not outside and not [p for p in untracked if not p.startswith('design/mechanical/')]
    since = set(git('diff', '--name-only', intro[-1]).stdout.split()) if intro else set()
    since |= {p for p in untracked if p.startswith('design/mechanical/')}
    res['g4_changes_within_section_4_3'] = since <= ALLOWED_CHANGES
    return dict(checks=res, pass_=all(res.values()), baselines=dict(g3=base3, g4_brief='introducing commit of ' + brief))


# --------------------------------------------------------------------------------------------
# Ranking (section 10), verdict (section 13), conflicts, handoff (section 14), acceptance (section 12)
# --------------------------------------------------------------------------------------------
def rear_z_investigation(st,ce,dp):
    rows=[]
    for (topo,cs),gd in sorted(ce.glands.items()):
        check=fix_pass(run_check(ce.sp.rear_periphery(dp,gd['spigot_height'])))
        rows.append(dict(topology=topo,cs_mm=cs,spigot_height_mm=gd['spigot_height'],
                         margin_mm=check['linear_worst'],check=check,
                         full_candidate_pass=False,
                         other_limits='Main seal squeeze/land, charger, button seals, support boundary and LRA remain independent checks'))
    review=None
    if ce.c.get('dielectric_sectors') and dp['seal_topology']=='radial':
        old_sp=copy.copy(ce.sp);old_sp.c=dict(ce.c,dielectric_sectors=False)
        old_sp.c.pop('dielectric_sector_process',None)
        old_gd=gland_design(st,old_sp,'radial',dp['seal_cs'])
        old_margin=run_check(ce.sp.rear_periphery(dp,old_gd['spigot_height']),False)
        review=dict(old_global_metal_interface_margin_mm=old_margin,
                    corrected_local_interface_margin_mm=next(r['margin_mm'] for r in rows if r['topology']==dp['seal_topology'] and r['cs_mm']==dp['seal_cs']),
                    old_spigot_height_mm=old_gd['spigot_height'],
                    note='Counterfactual reproduction of the reviewed local deficit only; old global-metal interface tolerance is not credited.')
    return dict(review_geometry_reproduction=review, current_margin_mm=next(r['margin_mm'] for r in rows if r['topology']==dp['seal_topology'] and r['cs_mm']==dp['seal_cs']),
                alternatives=rows, zero_growth_local_option_exists=any(r['margin_mm']>=-EPS for r in rows),
                thinner_parts_credited=False, stack_growth_proven_necessary=False,
                disposition='Local deficit remains a failed hard check where negative. Face/adhesive topology removes spigot height without thinner parts; these are diagnostic alternatives and do not close the complete design. No necessary nonzero total stack growth has been demonstrated.')


def rank_key(st, rep, z):
    fails=sum(not h['pass'] for h in rep['hard_checks'].values())
    rad=[x['linear_worst'] for x in rep['checks'] if x['hard'] in ('H05','H06')]
    suppliers={g['term'] for x in rep['checks'] for g in x['governing'] if g['role']=='SUPPLIER_GATED'}
    # Compare dimensionless required relaxation of planning ranges; greater demand ranks later.
    demands=[]
    for x in rep['checks']:
        for threshold in x['supplier_zero_margin']:
            term=next((g for g in x['governing'] if g['term']==threshold['term']),None)
            if term and threshold['value'] is not None and term['planning_range']:
                lo,hi=term['planning_range'];span=max(hi-lo,0.001)
                demands.append(abs(threshold['value']-term['adverse'])/span if x['linear_worst']<0 else 0.)
    atm=[x['linear_worst'] for x in rep['checks'] if x['hard'] in ('H12','H13','H15','H16')]
    distances=[x['plan_distance_mm'] for x in rep['rf_mag']['conductive_distances']]
    mag=[math.dist(x['centre'],st.u703) for x in rep['layout']['screws']['screws']]
    charger=rep['charger']['best']['geom']['rect']
    mag.append(pt_region(st.u703,dict(type='rect',rect=charger)))
    lra=[x['recommended_pose']['u703_distance_mm'] for x in rep['lra']['classes'] if x['recommended_pose']]
    mag+=lra
    service=st.assembly['service']
    owner_impact=int(not rep['load_path']['pass_'])+int(not st.assembly['pass_'])
    return [fails, owner_impact, [z['g4_z_delta_mm']['nominal'],-z['rows']['G2-REVA-HI']['headroom_nominal'],-z['rows']['G2-REVA-HI']['headroom_rss']],
            rep['D_min_feasible'] if rep['D_min_feasible'] is not None else 99., -min(rad),
            len(suppliers),max(demands,default=0.),sum(demands),-min(atm,default=0.),rep['seal_closure']['seal_count'],
            -min(distances,default=0.),-min(mag,default=0.),-min(lra,default=-999.),
            int(rep['design_point']['seal_topology']=='adhesive'),len(st.I['assembly']['steps']),
            sum('blind' in x['op'].lower() for x in st.I['assembly']['steps']),service['j1_cycles_per_service'],rep['id']]


def conflict_status(st, reps, leader, window, lra_any, z):
    L = leader
    chk = {x['id']: x for x in L['checks']}

    def lw(cid):
        return chk[cid]['linear_worst'] if cid in chk else None
    sup = L['supports_check']
    vent = L['layout']['vent']
    ev = {}
    ev['C1-FRONT-GAP'] = ('REMAINS_OPEN', 'G4 adds no front-gap layer; U8 still governs the front gap (G2/G3 unchanged).')
    ev['C2-DISPLAY-SIDE-CONNECTORS'] = ('REMAINS_OPEN', 'Assembly A6-A8: J1501/J201/J202 mated on the bench (A4), display mated at J1 through the open '
                                        'front (A7) before cover bond (A8) is only a proposed alternative: CONTRACT INTERPRETATION / CLARIFICATION REQUIRED; SERVICE-COVER-REBOND remains.')
    ev['C3-EDGE-WRAP'] = ('SUPPLIER_DATA_GATED', 'H05 at the G2 supplier exit-height range (%s): XF %s / XB %s / XC %s mm linear worst; flat-exit bound %s mm '
                          'reported; SR-FPC-MECH / SR-BATT-PCM / SR-CHG-MECH exit heights and R_bend decide.'
                          % (L['id'], f3(lw('H05-EDGE-XF-J1501')), f3(lw('H05-EDGE-XB-J201')), f3(lw('H05-EDGE-XC-J202')), f3(lw('INFO-EDGE-FLAT'))))
    ev['C4-CHARGER-PATH'] = ('REMAINS_OPEN', 'J202 stays west (OD-J202 open for a placement phase); charger aperture window r %s-%s mm at az 80-100 '
                             'with a separate feedthrough seal (S-CHG); corridor clearance via H05-T-ALLOW-XC.'
                             % (f3(st.s14geo['outline_r'] + 1.1), f3(L['design_point']['chg_r_out'])))
    ev['C5-SOUTH-CROWDING'] = ('OWNER_DECISION_GATED', 'E-G4-01 supersedes the stale G3 wording; E-G4-02: the historical LRA reservation is invalid and '
                               'the section 8.9 search finds no LRA pose for any envelope class (REAR Z deficit) - section 13 LRA stop.')
    ev['C6-DISPLAY-FPC-FOLD'] = ('SUPPLIER_DATA_GATED', 'DISP_LAND interrupted at az 269-295 (unsupported display-rim arc %s mm); SR-DISPLAY-FPC fold data required.'
                                 % f3(math.radians(26.0) * st.R_display))
    ev['C7-WIFI-BEYOND-BOARD'] = ('DEFERRED_G5', 'WIFI_RAD is a zero-intrusion keep-out for new metal and wiring (H17); SW5 pusher must be non-conductive; '
                                  'feed / radome / RF closure belongs to G5 (OD-G4-ENTRY).')
    ev['C8-GNSS-OCCUPIED'] = ('DEFERRED_G5', 'GNSS_RAD kept across all Z; lug / spring-bar distances reported for OD-G4-STRAP; feed construction is G5.')
    ev['C9-THICK-CORNER'] = ('REMAINS_OPEN', 'G4 Z delta 0.000; G2-REVA %s / %s and G2-REVA-HI %s / %s mm nominal / RSS reproduced unchanged.'
                             % (f3(z['rows']['G2-REVA']['nominal']), f3(z['rows']['G2-REVA']['rss']), f3(z['rows']['G2-REVA-HI']['nominal']),
                                f3(z['rows']['G2-REVA-HI']['rss'])))
    ev['X10-OPTICS-HEIGHT-UNKNOWN'] = ('SUPPLIER_DATA_GATED', 'Pod frame uses the frozen optics allocation; SR-SFH4053B-DS / SR-MAX86141-HEIGHT unchanged (G3 gates).')
    ev['X11-POD-FOOTPRINT'] = ('OWNER_DECISION_GATED', 'E-G4-01 applies. S14 pod frozen; W0 mechanically eliminated (OD-G4-WINDOW triggered); W1 eligible.')
    ev['X12-J1502-FACE'] = ('SUPPLIER_DATA_GATED', 'E-G4-01 applies. Conservative 7.90 mm tail corridor and thermode keepout reserved untouched (H19).')
    ev['X13-EDGE-CROSSINGS'] = ('SUPPLIER_DATA_GATED', 'See C3: edge crossings evaluated per crossing with governing terms and supplier zero-margin values.')
    ev['X14-SUPPORT-GAP'] = ('REMAINS_OPEN',
                             'Diagnostic geometry only; handoff unreleased. W/NW support at az %s; largest unsupported arc %s deg (legacy %s deg).'
                             % (f2(sup['w_nw']['centre']) if sup['w_nw'] else 'none', f2(sup['largest_unsupported_arc_deg']), f2(sup['legacy_largest_unsupported_arc_deg'])))
    ev['X15-NE-CROWDING'] = ('REMAINS_OPEN',
                             'Diagnostic geometry only; handoff unreleased. NE sector allocated deterministically: SUP_NE support post (MAIN stop pad blocked by the U4 courtyard, r 22.23 mm), vent '
                             'membrane port at az %s, SW4 bore at its window centre; ALS stays FRONT level; MAIN located by %d stop pads (largest pad arc %s deg).'
                             % (f2(vent['centre']) if vent else 'none', sup['pads'], f2(sup['largest_pad_arc_deg'])))
    ev['X16-MAGNETOMETER'] = ('MEASUREMENT_GATED', 'H18 %s: no new ferromagnetic part inside MAG_CLEAR; field closure MG-MAG; LRA magnet question OD-G4-LRA-MAG open.'
                              % ('PASS' if L['rf_mag']['h18_pass'] else 'FAIL'))
    ev['X17-GNSS-ALL-HEIGHTS'] = ('DEFERRED_G5', 'Radiator volumes enforced at every Z level with no new conductor (H17 %s).' % ('PASS' if L['hard_checks']['H17']['pass'] else 'FAIL (complete LRA/lead closure absent or modeled intrusion)'))
    ev['X18-PACK-EDGE'] = ('SUPPLIER_DATA_GATED', 'Support posts outside R_channel_inner %s mm (linear worst); finished pack SR-BATT-PACK / SR-BATT-GROWTH still gate.'
                           % f3(sup['R_channel_inner_lw_mm']))
    ev['X19-BCU-0603'] = ('REMAINS_OPEN', 'Electrical P-0402 gate; no G4 effect.')
    ev['X20-GROWTH-VS-OPTICS'] = ('REMAINS_OPEN', 'Disjoint pressure partition: %s N total; case/perimeter path %s, PCB pressure load %s N. '
                                  'Discrete support/contact boundary unqualified; no G3 support-land enlargement demonstrated.'
                                  % (f2(L['post_load']['total_N']),'PASS' if L['load_path']['pass_'] else 'FAIL',f2(L['post_load']['pcb_pressure_load_N'])))
    ev['X21-INGRESS-UNDEFINED'] = ('REMAINS_OPEN', 'Seal path %s; H15 %s, H16 %s. Impossible zero-tolerance glands require geometry/process correction; '
                                  'they are not tighter supplier-tolerance requests.' % ('closed' if L['seal_closure']['closed'] else 'open',
                                  L['hard_checks']['H15']['pass'],L['hard_checks']['H16']['pass']))
    ev['X22-UNMODELLED-Z'] = ('REMAINS_OPEN' if lw('H01-REAR-PERIPHERY-Z') < -EPS else 'SUPPLIER_DATA_GATED',
                             'Local REAR-edge stack margin %s mm; topology alternatives evaluated separately. Global delta 0 does not close a negative local margin. '
                             'Nonzero total stack growth has not been proved necessary; OD-G4-STACK not triggered.' % f3(lw('H01-REAR-PERIPHERY-Z')))
    ev['X23-WINDOW-CROSSTALK'] = ('OWNER_DECISION_GATED', 'W0 mechanically eliminated at the 5 ATM screen without Z delta; OD-G4-WINDOW triggered; MG-WINDOW-XTALK open.')
    ev['X24-DISPLAY-LAND'] = ('SUPPLIER_DATA_GATED', 'U4 land headroom %s mm linear worst (legacy %s / %s / %s); SR-DISPLAY-LAND / SR-DISPLAY-FPC.'
                              % (f3(lw('H09-U4-HEADROOM')), *[f3(v) for v in st.I['contract_values']['legacy']['u4_land_headroom_mm'].values()]))
    ev['X25-COVER-CASE-FIT'] = ('REMAINS_OPEN',
                                'Diagnostic geometry only; handoff unreleased. X25 under OD-G4-CORNER at D %s: bezel-wall margin %s mm linear worst (legacy conservative fit -1.100 unchanged).'
                                % (f2(L['D_eval']), f3(lw('H06-X25-BEZEL'))))
    ev['G2-CROSSING-HEIGHT'] = ('SUPPLIER_DATA_GATED', 'Unchanged G2 shared-corridor gate.')
    ev['G2-BOOK-FOLD'] = ('REMAINS_OPEN', 'No B.Cu connector in the G2 allocation except U7 leads; G4 adds no fold.')
    ev['G2-PROBE-RELIEF'] = ('REMAINS_OPEN', 'G4 adds no seated Z; probe relief unchanged.')
    ev['G2-BACK-STACK'] = ('REMAINS_OPEN', 'Back stack unchanged by G4.')
    ev['G2-DISCOVERED-INTERFACES'] = ('SUPPLIER_DATA_GATED', 'SW1-SW5 bores / bosses / pusher rules defined (SR-BUTTONS); antenna feeds are G5.')
    out = []
    for c in st.A['conflicts']:
        s, e = ev.get(c['id'], ('REMAINS_OPEN', 'Carried unchanged; no G4 evidence changes it.'))
        out.append(dict(id=c['id'], g4_status=s, g4_evidence=e, evidence_class='PROJECT_DERIVED'))
    return out


def battery_carrier_gates(st):
    """Brief 8.5 items not closed by circular pack or generic riser arithmetic."""
    pcm=st.G2in['parameters']['pcm_az_deg']
    insulation=load(MECH/'inputs/stack_parameters.json')['parameters']['t_insulator']
    rows=[
        dict(id='BATT-PCM-CLEARANCE', requirement='PCM-lobe clearance to SW3 and supports',
             known=dict(pcm_sweep_az_deg=[pcm['min'],pcm['max']]),
             missing='Supplier PCM lobe dimensions, radial/Z envelope and tolerances; full swept clearance against SW3 and case supports',
             closure='SR-BATT-PCM plus G4 clearance evaluation'),
        dict(id='BATT-INSULATION-ENVELOPE', requirement='Insulation envelope',
             known=dict(t_insulator_mm={k:insulation[k] for k in ('min','nom','max')},
                        source='Frozen stack_parameters t_insulator; already included in back_zone, not added again'),
             missing='Finished insulation coverage, edge wrap, overlaps and their radial/axial tolerance envelope; allocation within finished-pack envelope unconfirmed',
             closure='SR-BATT-PACK / SR-BATT-PCM and carrier insulation drawing'),
        dict(id='BATT-CARRIER-RETENTION', requirement='Carrier retention', known={},
             missing='Retention feature geometry, engagement/tolerances, required loads and allowable retention capacity; support placement alone does not establish retention',
             closure='Carrier design/manufacturer retention evidence'),
        dict(id='BATT-EXIT-TAIL', requirement='BATT_EXIT / tail clearance',
             known=dict(reservation=st.res['BATT_EXIT'], related_checks=['H05-EDGE-XB-J201','H05-EDGE-Z-XB-J201']),
             missing='Supplier exit/strain-relief envelope and complete tail route with bend/clearance against SW3, supports and insulation; generic XB crossing is partial evidence only',
             closure='SR-BATT-PCM / SR-FPC-MECH plus routed-tail clearance evaluation')]
    return [dict(r, status='OPEN', margin_mm=None, evidence_class='PROJECT_DERIVED') for r in rows]


def open_gates(st, reps):
    sup = ['SR-COVER-LENS', 'SR-DISPLAY-LAND', 'SR-DISPLAY-FPC', 'SR-BATT-PACK', 'SR-BATT-GROWTH', 'SR-BATT-PCM', 'SR-BUTTONS', 'SR-CHG-MECH',
           'SR-LRA', 'SR-WINDOW', 'SR-ADHESIVE', 'SR-FPC-MECH', 'gasket / O-ring supplier data (cross-section tolerance, compression set; no supplier request exists or is issued by G4)',
           'SR-TAGCONNECT', 'SR-J1-ALIGN']
    return dict(battery_carrier=battery_carrier_gates(st), supplier=sup, manufacturer=[g['id'] for g in st.g3_gates if g['evidence_class'] == 'MANUFACTURER_DATA_REQUIRED'],
                measurement=[g['id'] for g in st.g3_gates if g['evidence_class'] == 'MEASUREMENT_REQUIRED'] + [a['id'] for a in st.I['atm_q']] +
                ['h_pod wrist / strap trials'],
                g5=['AE1401 / AE1410 / AE1420 feed construction', 'radome / dielectric design', 'RF simulation and validation', 'case-material RF validation'],
                owner=[d['id'] for d in st.I['deferred_owner_decisions'] if d['kind'] == 'closure'],
                g3_carried=[g['id'] for g in st.g3_gates],
                closure=['CASE-SIDE-LOAD-PATH (bearing, shear, buckling, ceramic contact / FEA thresholds)', 'SERVICE-COVER-REBOND', 'FEA-1..FEA-4 (Q1)'])


def build_results(timing=None):
    t0 = time.time()
    st = Study()
    window = window_study(st)
    poses = lra_poses(st)
    st.z_ok = all(v['match'] for v in st.z.values())
    z = z_compliance(st, window)
    st.h02 = dict(pass_=z['pass_'])
    st.h02['pass'] = st.h02['pass_']
    st.scope = scope_check(st)
    ctx = dict(window=window, lra=poses)
    SW = st.I['sweep']
    d_main = frange(SW['D_case_body_mm']['start'], SW['D_case_body_mm']['stop'], SW['D_case_body_mm']['step'])
    d_ext = frange(SW['D_report_extension_mm']['start'], SW['D_report_extension_mm']['stop'], SW['D_report_extension_mm']['step'])
    evals = [CandidateEval(st, c, ctx) for c in st.I['candidates']]
    st.assembly = assembly_study(st, False)
    main_rows = [ce.sweep(d_main) for ce in evals]
    ext_rows = [ce.sweep(d_ext) for ce in evals]
    certificates = {ce.c['id']:universal_seal_rejection(st,ce) for ce in evals}
    if not all(x['proven'] for x in certificates.values()):
        raise StudyError('Universal H15 pruning certificate invalid: expanded Cartesian search required before acceptance')
    global SWEEP_MODE
    sweep_records=[]
    SWEEP_MODE=True
    try:
        for ce,rows,ext in zip(evals,main_rows,ext_rows):
            for row in rows+ext:
                full=candidate_report(st,ce,rows,ext,poses,window,retained=row)
                row['full_hard_checks']=full['hard_checks']
                row['feasible']=full['feasible']
                row['feasible_excluding_H22']=all(v['pass_'] for h,v in full['hard_checks'].items() if h!='H22')
                row['groups']={h:v['pass_'] for h,v in full['hard_checks'].items()}
                row['groups']['H03_OD']=row['od_margin']>=-EPS
                row['failing_groups']=[h for h,v in full['hard_checks'].items() if not v['pass_']]
                # Detail source contains the actual point geometry; JSONL avoids the compact JSON budget.
                sweep_records.append(full)
    finally:
        SWEEP_MODE=False
    st.sweep_records=sweep_records
    any_le51=any(r['feasible'] for rows in main_rows for r in rows)
    lra_any=any(r['full_hard_checks']['H22']['pass_'] for rows in main_rows for r in rows)
    reps = [candidate_report(st, ce, rows, ext, poses, window) for ce, rows, ext in zip(evals, main_rows, ext_rows)]
    keys = {r['id']: rank_key(st, r, z) for r in reps}
    order = sorted(reps, key=lambda r: keys[r['id']])
    acceptable = [r for r in order if r['acceptable']]
    owner_pending = window['od_g4_window_triggered']
    for r in reps:
        if r['acceptable'] and r is acceptable[0] and not owner_pending:
            r['outcome'] = 'RECOMMENDED'
        elif r['acceptable']:
            r['outcome'] = 'CONDITIONAL'
        else:
            r['outcome'] = 'REJECTED'
        r['rank_key'] = keys[r['id']]
        r['reasons'] = ['%s failed: %s' % (h, ', '.join(v['failing']) or v['title']) for h, v in sorted(r['hard_checks'].items()) if not v['pass']]
    rec = next((r for r in reps if r['outcome'] == 'RECOMMENDED'), None)
    min_feas = min((r['D_min_feasible'] for r in reps if r['D_min_feasible'] is not None), default=None)
    ext_feas = [rw['D'] for ext in ext_rows for rw in ext if rw['feasible']]
    stops = []
    if min_feas is None:
        stops.append(dict(id='STOP-DIAMETER', rule='section 13 Diameter', text='No candidate is feasible at D_case_body <= 51.00 mm; minimum required diameter: %s.'
                           % ('%.2f mm' % min(ext_feas) if ext_feas else 'none found <= 54.00 mm (diameter-independent hard-check failures)')))
    if not lra_any:
        stops.append(dict(id='STOP-LRA', rule='section 13 LRA', text='No feasible LRA pose exists for any envelope class inside the approved architecture '
                                                                     'at <= 51.0 mm; the LRA is not removed or shrunk.'))
    if window['od_g4_window_triggered']:
        stops.append(dict(id='OD-G4-WINDOW', rule='section 8.3 / 2.3 trigger', text='W0 is mechanically eliminated without a stack delta; owner must decide '
                                                                                     'whether a frame/rib-supported window (W1; W2 fails the G3 seal-land geometry) is the Rev-A baseline.'))
    if any(z['g4_z_delta_mm'][k] > EPS for k in z['g4_z_delta_mm']):
        stops.append(dict(id='OD-G4-STACK', rule='section 13', text='Nonzero G4 Z delta.'))
    verdict = 'G4 OWNER DECISION REQUIRED' if stops else ('G4 CONDITIONAL — SUPPLIER/RF/QUALIFICATION GATES OPEN' if rec else 'G4 FAIL')
    leader = order[0]
    conflicts = conflict_status(st, reps, leader, window, lra_any, z)
    res = dict(
        search_certificates=certificates, sweep_record_count=len(sweep_records), sweep_evidence_file='g4_sweep.jsonl',
        schema='sportwatch-g4-result/2', evidence_class='PROJECT_DERIVED', evidence_policy=st.I['evidence_policy'],
        verdict=verdict, study_status='BLOCKED / UNRELEASED STUDY',
        independent_review=dict(verdict='PASS AS CORRECT BLOCKED STUDY', source='Owner-provided independent re-review record; not engineering acceptance'),
        model_limitations=[WALL_MODEL_LIMITATION], stops=stops, owner_decisions=st.I['owner_decisions'], deferred_owner_decisions=st.I['deferred_owner_decisions'],
        g3_record='G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES', g3_generated_verdict_unchanged=st.g3_verdict, errata=st.I['errata'],
        carry_in=dict(s14=dict((k, v) for k, v in st.s14geo.items() if k in ('outline_r', 'pod_area', 'pod_r_min', 'pod_r_max', 'carry_in_checks',
                                                                              'clearances', 'overlaps', 'u6_chg', 'tail_id', 'frames')),
                      pins=st.pin_report, legacy=dict(rows=st.legacy['rows'], pass_=st.legacy['pass_'], method=st.legacy['method']),
                      g2_stacks={k: dict((kk, vv) for kk, vv in v.items() if kk != 'sensitivities') for k, v in st.z.items()}),
        z=z, window=window, assembly=st.assembly, scope=st.scope,
        diameter=dict(grid=dict(start=d_main[0], stop=d_main[-1], step=SW['D_case_body_mm']['step']), extension_used=not any_le51,
                      minimum_feasible_D=min_feas, minimum_feasible_candidate=next((r['id'] for r in reps if r['D_min_feasible'] == min_feas), None) if min_feas else None,
                      selected_D=rec['D_min_feasible'] if rec else None, selected_candidate=rec['id'] if rec else None,
                      margin_to_ceiling_mm=(51.0 - rec['D_min_feasible']) if rec else None,
                      minimum_required_D=min(ext_feas) if ext_feas else None,
                      minimum_required_D_excluding_H22=min([rw['D'] for rows in main_rows + ext_rows for rw in rows if rw['feasible_excluding_H22']], default=None),
                      minimum_required_D_excluding_H22_candidate=next((reps_id for reps_id, rows in zip([c['id'] for c in st.I['candidates']], [a + b for a, b in zip(main_rows, ext_rows)])
                                                                      if any(rw['feasible_excluding_H22'] and rw['D'] == min([x['D'] for rr in main_rows + ext_rows for x in rr if x['feasible_excluding_H22']], default=None) for rw in rows)), None),
                      d_dependent_closure_D={r['id']: r['d_dependent_closure_D'] for r in reps},
                      d_independent_failures={r['id']: r['d_independent_failures'] for r in reps},
                      rule='Universal H15 certificate rejects all authored Cartesian combinations. Every retained D has all H01-H25 evaluated before ranking. A D value is feasible if at least one design point passes every hard check at the required evaluations; selected D = the '
                           'RECOMMENDED candidate D_min_feasible; nothing is selected above 51.00 mm.'),
        candidates=reps, ranking=dict(order=[r['id'] for r in order], keys={r['id']: keys[r['id']] for r in reps},
                                      acceptable=[r['id'] for r in acceptable], leader_is_selection=bool(rec),
                                      rule=['owner-decision / frozen impact', 'G4 Z delta and G2-REVA-HI headroom', 'D_min_feasible',
                                            'min linear-worst radial / cover margin', 'supplier-gated governing terms', '5 ATM screening margins and seal count',
                                            'conductive distance to radiators', 'MAG_CLEAR / U703 distances', 'assembly simplicity', 'id (exact ties only)'],
                                      note='Failing hard checks are counted first; with no acceptable candidate the order is diagnostic only, never a selection.'),
        conflict_status=conflicts, open_gates=open_gates(st, reps), fea_load_cases=st.I['fea_load_cases'], atm_q=st.I['atm_q'],
        atm5_tracks=dict(geometry='H11, H14, H15, H16 deterministic geometry (this study)', analytical='cover / window / caseback plate screens and post load (this study)',
                         supplier='gasket, adhesive, cover lens, window, vent membrane, button seal, contact feedthrough data (open)',
                         fea='FEA-1..FEA-4 specified, executed in Q1', qualification='ATM-Q1..ATM-Q6 (Q1)',
                         claim='No G4 output claims 5 ATM water resistance or qualification.'),
        rf_boundary=dict(owner_decision='OD-G4-ENTRY', keepouts=['GNSS_RAD', 'BLE_RAD', 'WIFI_RAD'],
                         feed_span_upper_bounds_mm={x['id']: x['acceptance']['feed_span_upper_bound_mm'] for x in st.G2['discovered_interfaces'] if x['id'].startswith('AE')},
                         claim='No RF performance, efficiency, detuning or dielectric statement; final case material and radome dielectric are not frozen; '
                               'G5 may reopen case material, local envelope and radiator-adjacent geometry.'),
        k1_entry=k1_entry(), g5_handoff='G5 owns AE1401 / AE1410 / AE1420 feeds, radome, RF simulation and validation; G5 may require G4 re-entry.',
        source_sha256=dict({r['path']: r['sha256'] for r in st.pin_report},
                           **{'design/mechanical/inputs/g4_case_sealing.json': sha_file(IN_PATH),
                              'design/mechanical/tools/g4_case_sealing.py': sha_file(Path(__file__)),
                              'design/mechanical/G4_BRIEF.md': sha_file(MECH/'G4_BRIEF.md')}))
    res['handoff'] = handoff(st, res, leader)
    res['acceptance'] = acceptance(st, res)
    res['unsatisfied_acceptance'] = [int(k) for k, v in sorted(res['acceptance'].items(), key=lambda e: int(e[0])) if not v['satisfied']]
    out = json.loads(dumps(res))
    if timing is not None:
        timing['build_s'] = time.time() - t0
        timing['study'] = st
    return out


def k1_entry():
    return ['explicit owner authorization of K1 and an independently reviewed K1 contract',
            'G4 closed (>= CONDITIONAL) and independently reviewed, with its MAIN outline constraint polygon, REAR transform, LRA placement window and keep-outs accepted',
            'SR-REAR-PCB HDI stackup supplier-qualified', 'SR-MAX86141-LAND resolved against AN1891 / 21-100134',
            'SR-SFH4053B-DS footprint / seated height / emitting area verified and D405-D407 geometry re-run',
            'SR-MAX86141-HEIGHT and SR-TS5A12301E-HEIGHT within the G3 thresholds',
            'SR-FPC-MECH J1501 / J1502 MPN, land, pitch, rows and verified mirrored mating map (24 positions / 13 nets unchanged)',
            'J1502 conservative tail fit resolved', 'C1501 qualified or DNP retained', 'P-0402 DC-bias / effective-capacitance evidence',
            'U7 control / power / decoupling allocation review', 'SR-BATT-PCM sufficient for the J201 MPN',
            'G5 acceptance of any MAIN-edge or feed-region change near AE1420 / AE1401 / AE1410', 'assembly / isolation fixtures validated',
            'routing remains separately gated']


def handoff(st, res, leader):
    L = leader
    dp = L['design_point']
    chk = {x['id']: x for x in L['checks']}
    zero = {}
    for x in L['checks']:
        for z in x['supplier_zero_margin']:
            if z['value'] is not None:
                zero.setdefault(z['term'], []).append(dict(check=x['id'], value=z['value']))
    return dict(
        status='DIAGNOSTIC — NOT RELEASED (verdict %s); G4 authorizes nothing downstream' % res['verdict'],
        design_basis=L['id'], design_basis_rule='ranking leader (diagnostic order); not a selection',
        selected_D=res['diameter']['selected_D'], minimum_feasible_D=res['diameter']['minimum_feasible_D'],
        margin_to_51=res['diameter']['margin_to_ceiling_mm'], d_dependent_closure_D=res['diameter']['d_dependent_closure_D'],
        evaluated_D=L['D_eval'], r_case=L['r_case'], main_outline=L['main_outline'],
        transforms=dict(MAIN='assembly frame, origin (100, 100), north = -Y (unchanged G2)', REAR='assembly = (100 - x_rear, 100 + y_rear) (unchanged G3 S14)'),
        caseback=dict(pod_concept=L['pod_concept'], t_in=dp['t_in'], t_out=dp['t_out'], seal=L['caseback_seal'], h_pod=L['h_pod'],
                      window_eligible=res['window']['eligible'], w0=res['window']['w0_status']),
        seals=L['seal_inventory'], screws=L['layout']['screws'], supports=L['supports_check'], battery_carrier=dict(
            R_carrier_inner=dp['rcin'], t_carrier_wall=dp['tcw'], pcm_window_deg=[st.G2in['parameters']['pcm_az_deg']['min'], st.G2in['parameters']['pcm_az_deg']['max']],
            pack_radial_lw=chk['H10-PACK-RADIAL']['linear_worst'],
            reserve_class='ZERO_RESERVE_SUPPLIER_THRESHOLD' if abs(chk['H10-PACK-RADIAL']['linear_worst'])<EPS else 'NUMERIC_MARGIN',
            carrier_minimum_wall_mm=dp['tcw']-st.I['process_classes']['PC-CARRIER-MOULD']['thickness_mm'],
            open_gates=L['battery_carrier_gates']),
        corridor_margins_lw={k: chk[k]['linear_worst'] for k in chk if k.startswith(('H05-', 'H23-'))},
        keepouts=['GNSS_RAD', 'BLE_RAD', 'WIFI_RAD', 'MAG_CLEAR', 'S14 U6 island', 'S14 optical apertures / pod', 'S14 thermode / conservative tail corridors',
                  'S14 support lands (no pressure path allocated)'],
        charger_window=dict(az=[80.0, 100.0], r=[st.s14geo['outline_r'] + 1.1, dp['chg_r_out']], seal='S-CHG separate feedthrough', magnet='none'),
        buttons=L['layout']['button_checks'], lra=L['lra'], lugs=L['layout']['lugs'], supplier_zero_margin=zero,
        tolerance_stacks=[dict(id=x['id'], legacy=x['legacy'], nominal=x['nominal'], rss=x['rss'], linear_worst=x['linear_worst'],
                               governing=[g['term'] for g in x['governing'][:3]]) for x in L['checks']],
        assembly=res['assembly']['sequence'], fea=res['fea_load_cases'], atm_q=res['atm_q'], open_gates=res['open_gates'])


def acceptance(st,res):
    reps=res['candidates'];rec=[r for r in reps if r['outcome']=='RECOMMENDED']
    def all_h(*ids): return all(r['hard_checks'][h]['pass'] for r in reps for h in ids)
    decisions=all(o['verbatim'] in (MECH/'G4_BRIEF.md').read_text() for o in st.I['owner_decisions'])
    # Brief text uses Markdown emphasis in the owner blocks; compare extracted paragraphs via whitespace normalization.
    norm=lambda text:' '.join(text.replace('**','').split())
    decisions=all(norm(o['verbatim']) in norm((MECH/'G4_BRIEF.md').read_text()) and o['date']=='2026-10-14' for o in st.I['owner_decisions']) and len(st.I['owner_decisions'])==4
    rows=[
      (decisions and st.scope['pass_'],'Approved decisions recorded; frozen carry-ins and scope checks enforced'),
      ({e['id'] for e in res['errata']}=={'E-G4-01','E-G4-02'},'Both prospective errata recorded'),
      (len(reps)>=3 and all(r.get('outcome') for r in reps) and len(st.sweep_records)==len(reps)*141,'Equal finite grids; universal H15 rejection certificates plus full H01-H25 retained diagnostics'),
      (res['carry_in']['legacy']['pass_'] and all(len(r['hard_checks'])==25 for r in reps),'Legacy and per-check evaluations retained; binary/exact checks expose actual predicate evidence'),
      (bool(rec) and all(all(h['pass'] for h in r['hard_checks'].values()) for r in rec),'No complete recommended candidate'),
      (all(k in res['diameter'] for k in ('selected_D','minimum_feasible_D','margin_to_ceiling_mm')),'Selected/minimum/margin explicitly null when no complete candidate exists'),
      (all(any(x['id']=='H05-STRAIGHT' for x in r['checks']) and any(x['id']=='H06-X25-BEZEL' for x in r['checks']) for r in reps),'Numeric revised radial/X25 plus unchanged legacy and thresholds'),
      (all_h('H01'),'Global zero delta is insufficient when the local REAR stack fails; no necessary stack growth demonstrated'),
      (all_h('H14','H15','H16','H13'),'Inventory and screens reported; failed seals and unestablished physical support boundary prevent closure'),
      (all_h('H17'),'Modeled feature keepouts checked; unresolved LRA/lead prevents complete H17 closure; no RF claim'),
      (any(r['lra']['feasible_classes'] for r in reps),'No complete LRA pose'),
      (bool(rec) and bool(res['handoff']['lra']['feasible_classes']),'Numeric diagnostic handoff exists; selected geometry and LRA recommendation are absent'),
      (False,'legacy later-phase scope incompatibility: immutable g3_rear_optical.py check rejects uncommitted G4 files; arch_diagrams.py check inherits this. Actual exits recorded in README; no future commit credited'),
      (res['verdict'] in ('G4 PASS','G4 CONDITIONAL — SUPPLIER/RF/QUALIFICATION GATES OPEN','G4 OWNER DECISION REQUIRED','G4 FAIL'),'Contract verdict vocabulary'),
      (not res['open_gates']['supplier'] and not res['open_gates']['owner'],'Supplier confirmations and closure owner decisions remain open')]
    return {str(i):dict(satisfied=bool(ok),reason=why) for i,(ok,why) in enumerate(rows,1)}


# --------------------------------------------------------------------------------------------
# Report (Markdown)
# --------------------------------------------------------------------------------------------
def fmtv(v):
    if v is None:
        return 'n/a'
    if isinstance(v, bool):
        return 'yes' if v else 'no'
    if isinstance(v, (int, float)):
        return f3(v)
    if isinstance(v, dict):
        return ' / '.join('%s %s' % (k, fmtv(x)) for k, x in sorted(v.items()))
    return str(v)


def cell(s):
    return str(s).replace('|', '/').replace('\n', ' ')


def check_table(checks, ids=None):
    o = ['| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |',
         '|---|---|---|---|---|---|---|---|---|---|']
    for x in checks:
        if ids and x['id'] not in ids:
            continue
        gov = '; '.join('%s (%s, %+.3f)' % (g['term'], g['role'], g['margin_change']) for g in x['governing'][:3]) or 'none'
        zm = '; '.join('%s = %s' % (z['term'], f3(z['value'])) for z in x['supplier_zero_margin'][:3]) or 'n/a'
        p = 'INFO' if x['pass'] is None else ('PASS' if x['pass'] else '**FAIL**')
        og = '; '.join(g['decision'] for g in x.get('owner_gated', [])) or '-'
        o.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (x['id'], x['hard'], cell(fmtv(x['legacy'])), f3(x['nominal']), f3(x['rss']),
                                                                        f3(x['linear_worst']), p, cell(gov), cell(zm), og))
    return o


def compress_az(rows):
    """Group consecutive azimuths that share the same blocker set."""
    out = []
    for r in rows:
        key = tuple(r['blockers'])
        if out and out[-1][2] == key and r['az'] - out[-1][1] <= 5:
            out[-1][1] = r['az']
        else:
            out.append([r['az'], r['az'], key])
    return out


def render_md(res):
    o=['# G4 corrective engineering study', '', '**'+res['verdict']+'**', '',
       'BLOCKED / UNRELEASED STUDY. Independent re-review returned PASS AS CORRECT BLOCKED STUDY (owner-provided record). Uncommitted diagnostic package. No complete candidate is selected. No qualification, RF performance, supplier component availability, or G2/G3 reopening is claimed.', '',
       'The binding brief is unchanged. G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES is an administrative record; generated G3 history and open gates remain unchanged.', '']
    def table(headers,rows):
        o.append('| '+' | '.join(headers)+' |');o.append('| '+' | '.join(['---']*len(headers))+' |')
        o.extend('| '+' | '.join(cell(fmtv(x)) for x in row)+' |' for row in rows);o.append('')
    o+=['## Verdict and stops','']
    table(['ID','Finding'],[(x['id'],x['text']) for x in res['stops']])
    o+=['No owner decision is a substitute for fixing failed geometry. OD-G4-WINDOW remains triggered. OD-G4-ATM-STD, MATERIAL, STRAP and LRA-MAG remain deferred closure decisions. OD-G4-STACK is not triggered: local failures are explicit, but necessary total stack growth has not been proved.', '',
        '## Diameter, complete checks and ranking','',
        'The complete 47.00–51.00 mm grid uses 0.05 mm steps. A reporting-only extension runs to 54.00 mm. Every retained diagnostic point evaluates H01–H25 before ranking. No threshold for a subset of checks is called a feasible diameter.', '',
        'The Cartesian design space is rejected by an independently computed H15 certificate: for each architecture, at least one mandatory button fails every authored cross-section with the applicable local process. This certificate is independent of diameter and all other design grids. It is fail-closed: if the certificate stops holding, the tool stops pending expanded search. The retained point at each diameter is only a diagnostic representative; group first-pass results below apply to these retained points, not a claim of global group optimality.', '',
        'Per-point predicate and geometric evidence: `g4_sweep.jsonl` (%d records). Complete passing candidate set: %s. Selected diameter: %s; minimum feasible diameter: %s; minimum required diameter found through 54 mm: %s.' % (res['sweep_record_count'],str(res['ranking']['acceptable']),fmtv(res['diameter']['selected_D']),fmtv(res['diameter']['minimum_feasible_D']),fmtv(res['diameter']['minimum_required_D'])), '']
    table(['Candidate','Diagnostic D','Outcome','Failing hard checks'],[(c['id'],c['D_eval'],c['outcome'],', '.join(h for h,v in c['hard_checks'].items() if not v['pass'])) for c in res['candidates']])
    table(['Independent grid group']+[c['id'] for c in res['candidates']],[(g,)+tuple(c['independent_group_thresholds'][g] for c in res['candidates']) for g in sorted(res['candidates'][0]['independent_group_thresholds'])])
    o+=['Independent group thresholds are partial arithmetic only; full H tables govern eligibility. Polymer side-radial requires approximately >=%s mm on the 0.05 mm grid (including the polymer sector of G4-B). G4-B caseback/related geometry first passes its comparison group at approximately >=%s mm; that group uses the continuous-inner-support comparison, not the perimeter bypass acceptance. These exceed the owner ceiling and do not make a candidate feasible.' % (f2(next(c for c in res['candidates'] if c['id']=='G4-A')['independent_group_thresholds']['SIDE_RADIAL']), f2(next(c for c in res['candidates'] if c['id']=='G4-B')['independent_group_thresholds']['CASEBACK'])), '',
        WALL_MODEL_LIMITATION, '']
    table(['Candidate','H05 radial / edge geometry','LRA-coupled feasibility','Complete H05'],
          [(c['id'],c['h05_diagnostics']['radial_edge_geometry_pass'],c['h05_diagnostics']['lra_coupled_feasibility'],c['hard_checks']['H05']['pass']) for c in res['candidates']])
    o+=['Diagnostic order: '+', '.join(res['ranking']['order'])+'. No rejected candidate is recommended. Ranking includes owner/frozen impact, both HI headrooms, diameter, worst radial/cover margins, supplier term count and normalized threshold demands, pressure/seal margins and seal count, RF distances, charger/screw/LRA distances, and service operations/blind mating/J1 cycles.', '']
    table(['Hard check','Required evaluation']+[c['id'] for c in res['candidates']],[(h,HARD[h][1])+tuple('PASS' if c['hard_checks'][h]['pass'] else 'FAIL' for c in res['candidates']) for h in sorted(HARD)])
    table(['Group']+[c['id']+' first pass D' for c in res['candidates']],[(h,)+tuple(c['group_thresholds'][h]['first_pass_D'] for c in res['candidates']) for h in sorted(HARD)])
    o+=['## Pressure domains, physical reaction paths and support evidence','']
    for c in res['candidates']:
        p=c['post_load'];o+=['### '+c['id'],'',p['note'],'']
        table(['Domain','Area mm²','Force N'],[(d['id'],d['area_mm2'],d['force_N']) for d in p['domains']])
        o+=['Partition sum: %.6f mm²; total load %.6f N; perimeter reaction %.6f N; PCB pressure load %s N. Partition check: %s. Reaction geometry: %s.' % (p['total_area_mm2'],p['total_N'],p['perimeter_reaction_N'],fmtv(p['pcb_pressure_load_N']),p['domain_partition_pass'],p['reaction_geometry']), '',
            'No PCB pressure path is needed for P1. P2 retains its physically authored REAR-board branch and fails closed. Any forbidden branch fails even when another branch reaches MIDCASE. No G3 support-land enlargement has been demonstrated.', '']
        table(['Mode','Evidence / numeric assumptions'],[(k,v) for k,v in p['modes'].items()])
        table(['Case-side bypass screen','Value'],list(p['case_side_bypass_screen'].items()))
        o+=['H13 uses the perimeter-only bypass stress and deflection margins above, together with the load-path and window checks. The bypass fails numerically for the current design. The annular-plate comparison retains continuous inner/outer support and provisional material properties; its inner boundary is not established by the bypass geometry. Open material, shear, buckling and contact qualification gates remain separately reported; a numerical screen never qualifies them. Failure of a polymer specimen in this model does not eliminate all polymer architectures.', '']
        o+=check_table(c['checks'],['H13-CASEBACK-STRESS','H13-CASEBACK-DEFLECTION']);o.append('')
    o+=['## Window minimum-thickness screen','',res['window']['method'], '',
        'W0 unsupported radius: %.6f mm. Every screen uses nominal thickness minus the imported ±0.05 mm thickness tolerance. Planning allowables are provisional; no supplier-qualified allowable or qualification exists. Positive window deltas apply to both G2 baselines; negative gains are never credited.' % res['window']['spans_mm']['W0'],'']
    table(['Window / material','Nominal t','Minimum t','Stress MPa','Planning allowable MPa','Deflection mm','Stress pass','Seal land','Z delta','Eligible'],[(r['id'],r['t_window_mm'],r['minimum_thickness_mm'],r['sigma_ss_MPa'],r['sigma_allow_min_MPa'],r['w_ss_mm'],r['stress_pass'],r['seal_land_pass'],r['z_delta_mm'],r['id'] in res['window']['eligible']) for r in res['window']['rows']])
    o+=['W0: '+res['window']['w0_status']+'. W0 0.5 mm fails the planning screen; 0.8 mm introduces the reported thickness conflict. W1 0.30 mm chemically strengthened glass fails at its 0.25 mm minimum. W2 retains the G3 seal-land constraint. OD-G4-WINDOW is a decision, not selected here.', '',
        '## Seal inventory, zero-tolerance feasibility and thresholds','',
        'The ±0.05 mm O-ring cross-section tolerance is a PROVISIONAL PLANNING LIMIT, not supplier-qualified evidence. Negative algebraic bounds mean geometry/process redesign. They are never reported as tighter supplier tolerances. Stretch, eccentricity, extrusion, thermal expansion, swelling and compression set remain supplier/process gates.', '']
    for c in res['candidates']:
        o+=['### '+c['id'],'']
        table(['Primary seal','Type','Interface'],[(x['id'],x['type'],' / '.join(x['interface'])) for x in c['seal_inventory']['seals']])
        rows=[]
        if c['caseback_seal']['threshold']:rows.append(('S-CB-MAIN',c['caseback_seal']['threshold']))
        rows += [(k,v['threshold']) for k,v in c['layout']['pusher_glands'].items()]
        rows += [(x['id'],x['threshold']) for x in c['conditional_seals']]
        table(['Seal','Feasible at ±0','Maximum symmetric ±delta mm','Classification'],[(k,v['zero_cs_tolerance_feasible'],v['maximum_symmetric_cs_tolerance_mm'],v['classification']) for k,v in rows])
        table(['Conditional option','Required geometry / result'],[(x['id'],x) for x in c['conditional_seals']])
        o+=['S-U6F3 is evaluated only for F3; F1/F2 do not create this penetration. S-POD-FRAME is mandatory for P2. Adhesive caseback seals are adhesive rings, not face O-rings. S-CHG is a continuous bonded feedthrough; there is no compressed charger face seal in the inventory.', '']
    o+=['## Buttons, bosses, carrier, charger and local REAR stack','']
    for c in res['candidates']:
        o+=['### '+c['id'],'', 'Diagnostic dimensions: '+fmtv(c['design_point']), '',
            'SW5 nonconductive and SW4 non-ferromagnetic are material constraints only. No compliant pusher or switch is claimed available. Local polymer bore, wall, boss, gland and metal/polymer interface tolerances are applied. The 0.4 mm switch overhang/travel term enters the bore stack; axial gland, core and transverse boss wall are separately screened.', '']
        ids=[x['id'] for x in c['checks'] if x['id'].startswith(('H21-','H03-BOSS','H10-','H20-','H01-REAR'))]
        o+=check_table(c['checks'],ids);o.append('')
        table(['Charger orientation','Radial block','Tangential block','Continuous land each side','Radial margin','Centre containment margin','Tangential available','Pass'],[(v['orientation_deg'],v['radial_mm'],v['tangential_mm'],v['land_each_side_mm'],v['radial_fit_mm'],v['margin_mm'],v['tangential_available_at_outer_feasible_centre_mm'],v['pass_']) for v in c['charger']['orientations']])
        o+=[c['charger']['containment_assumption']+' The contact block and its entire land must fit simultaneously. The outer boundary already excludes the caseback seal/spigot and clearance. Dock loads enter the caseback/perimeter. Charger pass: '+str(c['charger']['pass_'])+'.', '',
            'Carrier wall minimum is 0.30 mm at adverse process tolerance. The selected diagnostic 0.35 ±0.05 mm meets that minimum with zero wall reserve; 0.30 ±0.05 mm is rejected. Pack radial equality, where present, is a ZERO_RESERVE_SUPPLIER_THRESHOLD permitted by the brief, not a positive-margin requirement.', '', c['rear_z']['disposition'], '']
        table(['Battery item','Status','Known planning evidence','Missing input / evaluation','Closure'],
              [(g['requirement'],g['status'],g['known'],g['missing'],g['closure']) for g in c['battery_carrier_gates']])
        o+=['Battery items above are explicit open gates; missing numeric clearance or retention inputs are not assigned passing margins.', '']
        o+=['Reviewed geometry reproduction: '+fmtv(c['rear_z']['review_geometry_reproduction']), '']
        table(['Local seal topology','CS','Spigot height','Local REAR-edge Z margin'],[(x['topology'],x['cs_mm'],x['spigot_height_mm'],x['margin_mm']) for x in c['rear_z']['alternatives']])
    o+=['## Legacy radial / X25 and frozen total stacks','']
    table(['Legacy metric','Expected','Reproduced','Match'],[(x['id'],x['expected'],x['reproduced'],x['match']) for x in res['carry_in']['legacy']['rows']])
    for c in res['candidates']:
        o+=['### '+c['id'],''];o+=check_table(c['checks'],['H05-STRAIGHT','H05-EDGE-XF-J1501','H05-EDGE-XC-J202','H05-EDGE-XB-J201','H05-EDGE-XL-LRA','H06-X25-BEZEL','H05-WALL-DIELECTRIC']);o.append('')
    table(['Baseline','Nominal','RSS','Linear worst','Adopted global G4 delta'],[(k,v['nominal'],v['rss'],v['linear'],v['g4_delta']) for k,v in res['z']['rows'].items()])
    o+=['H01 also checks the local stack. Reporting adopted global delta 0.000 does not conceal a negative local result.', '', '## LRA finite-grid search and maximum compatible envelope','']
    for c in res['candidates']:
        o+=['### '+c['id'],'',c['lra']['approximation'],'','Exclusions: '+', '.join(c['lra']['exclusions']), '']
        table(['Class','Grid poses','Plan survivors','Height margin','Maximum height at diagnostic caseback','Feasible poses'],[(x['id'],x['poses_evaluated'],x['plan_feasible_poses'],x['z_margin_lw'],x['max_height_for_zero_margin_mm'],x['feasible_poses']) for x in c['lra']['classes']])
        o+=['Maximum compatible geometric envelope: '+fmtv(c['lra']['maximum_compatible_envelope']), '',
            'This is not an existing actuator class or supplier availability claim. Lead routing remains unqualified. No current class survives; no architecture-wide impossibility is proved. The actuator stays at REAR level. Moving it to another Z allocation would require G2 scope reopening.', '']
    o+=['## Assembly, service and RF','',res['assembly']['disposition'], '',res['assembly']['brief_listed_cover_first']['finding'], '',
        'The proposed front-display-before-cover alternative preserves the frozen plan and stack allocation and is geometrically evaluated; it is not substituted for the binding sequence. SERVICE-COVER-REBOND remains open. Full execution also depends on the missing LRA pose and failed insertion/sealing checks.', '']
    table(['Binding step','Blocked by','Missing prerequisite','Access direction','Pass'],[(x['id'],x['blocked_by'],x['prerequisites_missing'],x['direction'],x['pass_']) for x in res['assembly']['brief_listed_cover_first']['result']['rows']])
    table(['Candidate','Modeled RF intrusions','Complete H17','H18'],[(c['id'],c['rf_mag']['rf_intrusions'],c['hard_checks']['H17']['pass'],c['hard_checks']['H18']['pass']) for c in res['candidates']])
    o+=['Modeled inventory includes dielectric boundaries, final bosses/pushers, case-side supports, charger and defined lead/exit reservations. Missing compatible LRA and connecting lead geometry keeps full H17 closure open. No RF performance claim.', '', '## Acceptance, gates and validation','']
    table(['Criterion','Satisfied','Reason'],[(k,v['satisfied'],v['reason']) for k,v in res['acceptance'].items()])
    o+=['Actual validation commands, exit codes, deterministic byte comparison, immutable comparisons and exact worktree status are recorded in the G4 run record in `../README.md`. Criterion 13 remains failed for the literal historical later-phase scope incompatibility; no future commit is credited.', '',
        'Selftests retain the original 17 faults and add pressure partition, forbidden alternate branch, button travel/local polymer, carrier minimum, rectangular charger containment, impossible-zero-tolerance gland, minimum window thickness, missing H07/H08, missing LRA exclusions, partial acceptance, proud cover, assembly conflict and polygon-contact regressions.', '']
    table(['Gate class','Open items'],list(res['open_gates'].items()))
    o+=['Numeric supplier zero-margin values (diagnostic, never silently adopted):','']
    table(['Term','Check / threshold'],list(res['handoff']['supplier_zero_margin'].items()))
    table(['Q1 gate','Requirement'],[(x['id'],x['text']) for x in res['atm_q']])
    table(['FEA load case','Load','Support','Pass metrics'],[(x['id'],x['load'],x['support'],x['pass']) for x in res['fea_load_cases']])
    o+=['## Conflict evidence and handoff','']
    table(['Conflict','Status','Evidence'],[(x['id'],x['g4_status'],x['g4_evidence']) for x in res['conflict_status']])
    o+=['Handoff is diagnostic and unreleased. No selected architecture, LRA pose, qualified load boundary, or complete sealing solution exists. No G3 reopening is demonstrated. G4 authorizes no KiCad edit, G5, K1 or Q1 execution. The package remains uncommitted. Independent re-review returned PASS AS CORRECT BLOCKED STUDY; final state remains G4 OWNER DECISION REQUIRED — BLOCKED / UNRELEASED STUDY.','']
    return '\n'.join(o)+'\n'
class Svg:
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="sans-serif">' % (w, h, w, h),
                  '<title>%s</title>' % html.escape(title), '<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (w, h)]

    def add(self, s):
        self.o.append(s)

    def text(self, x, y, s, size=11, anchor='start', fill='#111', weight='normal'):
        self.o.append('<text x="%.2f" y="%.2f" font-size="%g" text-anchor="%s" fill="%s" font-weight="%s">%s</text>'
                      % (x, y, size, anchor, fill, weight, html.escape(str(s))))

    def render(self):
        return '\n'.join(self.o + ['</svg>']) + '\n'


def _pp(pts, T):
    return ' '.join('%.2f,%.2f' % T(p) for p in pts)


def _sector_path(T, g, n=64):
    a0, a1 = g['az']
    r0, r1 = g['r']
    span = (a1 - a0) % 360.0 or 360.0
    outer = [xy(r1, a0 + span * i / n) for i in range(n + 1)]
    inner = [xy(r0, a0 + span * (n - i) / n) for i in range(n + 1)] if r0 > 0 else [(100.0, 100.0)]
    return _pp(outer + inner, T)


def draw_geom(svg, T, g, fill, stroke, op=0.35, dash=None, sw=1.0):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    if g['type'] == 'rect':
        x0, y0, x1, y1 = g['rect']
        svg.add('<polygon points="%s" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.2f"%s/>'
                % (_pp([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], T), fill, op, stroke, sw, d))
    elif g['type'] == 'circles':
        for x, y, r in g['circles']:
            cx, cy = T((x, y))
            svg.add('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.2f"%s/>'
                    % (cx, cy, r * T.s, fill, op, stroke, sw, d))
    elif g['type'] == 'poly':
        svg.add('<polygon points="%s" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (_pp(g['pts'], T), fill, op, stroke, sw, d))
    else:
        svg.add('<polygon points="%s" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (_sector_path(T, g), fill, op, stroke, sw, d))


class Tf:
    def __init__(self, s, ox, oy):
        self.s, self.ox, self.oy = s, ox, oy

    def __call__(self, p):
        return (self.ox + (p[0] - 100.0) * self.s, self.oy + (p[1] - 100.0) * self.s)


def render_plan(res, st):
    lead = next(c for c in res['candidates'] if c['id'] == res['ranking']['order'][0])
    dp = lead['design_point']
    svg = Svg(1180, 980, 'G4 plan')
    T = Tf(13.0, 430.0, 490.0)
    svg.text(20, 26, 'G4 plan (front view from the display; north up = -Y). Design basis %s at D %s mm — DIAGNOSTIC, verdict %s'
             % (lead['id'], f2(dp['D']), res['verdict']), 13, weight='bold')
    R = dp['D'] / 2
    for rid, col in (('GNSS_RAD', '#2e86c1'), ('BLE_RAD', '#8e44ad'), ('WIFI_RAD', '#16a085')):
        draw_geom(svg, T, st.res[rid]['geometry'], col, col, 0.28)
    draw_geom(svg, T, st.res['MAG_CLEAR']['geometry'], '#e67e22', '#e67e22', 0.08, '6 4')
    draw_geom(svg, T, dict(type='circles', circles=[[100, 100, R]]), 'none', '#222', 0.0, sw=2.0)
    draw_geom(svg, T, dict(type='circles', circles=[[100, 100, R - dp['tw']]]), 'none', '#555', 0.0, '4 3')
    draw_geom(svg, T, dict(type='circles', circles=[[100, 100, dp['r_lim']]]), 'none', '#c0392b', 0.0, '2 2', 1.4)
    for lg in lead['layout']['lugs']:
        draw_geom(svg, T, lg['geom'], '#bbbbbb', '#777', 0.4)
    for sc in lead['layout']['screws']['screws']:
        draw_geom(svg, T, sc['geom'], '#7f8c8d', '#222', 0.9)
    g = st.s14geo
    draw_geom(svg, T, dict(type='circles', circles=[[100, 100, g['outline_r']]]), '#f9e79f', '#b7950b', 0.25, sw=1.5)
    draw_geom(svg, T, dict(type='poly', pts=g['pod']), '#d6eaf8', '#2471a3', 0.6, sw=1.5)
    for s_ in g['supports']:
        draw_geom(svg, T, dict(type='poly', pts=s_['poly']), '#000', '#000', 0.9)
    draw_geom(svg, T, dict(type='poly', pts=g['u6_island']), '#f5b7b1', '#922b21', 0.6)
    draw_geom(svg, T, dict(type='poly', pts=g['tail_cons']), '#d7bde2', '#6c3483', 0.5)
    draw_geom(svg, T, st.res['LRA']['geometry'], 'none', '#c0392b', 0.0, '3 3')
    draw_geom(svg, T, sector(80, 100, g['outline_r'] + 1.1, dp['chg_r_out']), '#f0b27a', '#a04000', 0.6)
    for f in lead['layout']['features']:
        if f['kind'] in ('button boss','case-side support','dielectric sector','charger aperture and land'):
            draw_geom(svg,T,f['geom'],'none','#c0392b' if f['kind']=='charger aperture and land' else '#555',0.,'2 2')
    for b in lead['layout']['buttons']:
        draw_geom(svg, T, b['bore_geom'], '#58d68d', '#1e8449', 0.7)
    v = lead['layout']['vent']
    if v:
        draw_geom(svg, T, sector(v['centre'] - v['half'], v['centre'] + v['half'], R - dp['tw'], R), '#5dade2', '#1b4f72', 0.8)
    svg.add('<polygon points="%s" fill="none" stroke="#1abc9c" stroke-width="1.2" stroke-dasharray="8 3"/>' % _pp(lead['main_outline']['polygon'], T))
    for k in lead['lra']['classes']:
        for w_ in k['plan_window_az_r'][:40]:
            p = xy((w_['r_min'] + w_['r_max']) / 2, w_['az'])
            cx, cy = T(p)
            svg.add('<circle cx="%.2f" cy="%.2f" r="3" fill="none" stroke="#c0392b"/>' % (cx, cy))
    ly = 70
    for col, txt in (('#222', 'case body D_case_body (OD)'), ('#555', 'side bore (MAIN / BATTERY / REAR upper)'), ('#c0392b', 'caseback seal spigot / LRA outer limit'),
                     ('#2e86c1', 'GNSS_RAD (all Z)'), ('#8e44ad', 'BLE_RAD (MAIN)'), ('#16a085', 'WIFI_RAD (MAIN + REAR)'), ('#e67e22', 'MAG_CLEAR (dashed)'),
                     ('#b7950b', 'S14 REAR outline r 16.4'), ('#2471a3', 'S14 pod / window'), ('#000', 'S14 support lands (no pressure path allocated)'),
                     ('#922b21', 'U6 island'), ('#6c3483', 'tail corridor (conservative)'), ('#a04000', 'charger aperture window'),
                     ('#1e8449', 'button bores SW1-SW5'), ('#34495e', 'case support posts / pads'), ('#1b4f72', 'vent membrane port'),
                     ('#1abc9c', 'MAIN outline constraint polygon (K1)'), ('#7f8c8d', 'caseback screws in lug roots'),
                     ('#c0392b', 'historical LRA sector (invalid, dashed) / plan-only LRA poses (circles, Z infeasible)')):
        svg.add('<rect x="870" y="%d" width="14" height="10" fill="%s" fill-opacity="0.7"/>' % (ly - 9, col))
        svg.text(890, ly, txt, 10)
        ly += 18
    svg.text(870, ly + 10, 'No feasible LRA pose; no RF claim; not case CAD.', 10, fill='#c0392b')
    return svg.render()


def render_sections(res, st):
    lead = next(c for c in res['candidates'] if c['id'] == res['ranking']['order'][0])
    dp = lead['design_point']
    lay = st.z['G2-REVA']['layers']
    order = ['cover', 'cover_bond', 'display', 'front_gap', 'main_pcb', 'back_zone', 'battery_zone', 'lower_web', 'rear_inner', 'rear_pcb', 'optics_zone', 'window']
    zs, z = {}, 0.0
    for k in order:
        zs[k] = (z, z + lay[k])
        z += lay[k]
    tl = dp['t_land']
    level_z = dict(COVER=(zs['cover'][0], zs['cover_bond'][1]), DISPLAY=zs['display'], LAND=(zs['front_gap'][0], zs['front_gap'][0] + tl),
                   FRONT_GAP=(zs['front_gap'][0] + tl, zs['front_gap'][1]), MAIN=(zs['main_pcb'][0], zs['back_zone'][1]),
                   BATTERY=(zs['battery_zone'][0], zs['lower_web'][1]), REAR=(zs['rear_inner'][0], zs['optics_zone'][1]), CASEBACK=zs['window'])
    stations = [('CENTER', 0), ('GNSS_N', 0), ('FPC_S', 168), ('CHG_E', 90), ('SW2_W', 270), ('POD', 45)]
    svg = Svg(1200, 820, 'G4 radial sections')
    svg.text(20, 24, 'G4 radial sections at six stations (r horizontal 0-27 mm, Z down from the cover). Basis %s D %s — diagnostic' % (lead['id'], f2(dp['D'])), 13, weight='bold')
    rows = {r['az']: r for r in lead['r_case']['rows']}
    cols = {'cover': '#d6eaf8', 'display': '#d5f5e3', 'front_gap': '#fdfefe', 'main_pcb': '#a9dfbf', 'back_zone': '#fcf3cf', 'battery_zone': '#f9e79f',
            'lower_web': '#e5e7e9', 'rear_inner': '#e8daef', 'rear_pcb': '#a9cce3', 'optics_zone': '#fad7a0', 'window': '#aed6f1', 'cover_bond': '#ffffff'}
    for i, (name, az) in enumerate(stations):
        ox, oy = 30 + (i % 3) * 390, 60 + (i // 3) * 380
        sx, sz = 13.0, 18.0
        svg.add('<rect x="%d" y="%d" width="370" height="330" fill="none" stroke="#999"/>' % (ox - 10, oy - 18))
        svg.text(ox, oy - 4, '%s (az %d)' % (name, az), 12, weight='bold')
        r_ext = {'cover': st.R_display + 1.0, 'cover_bond': st.R_display + 1.0, 'display': st.R_display, 'front_gap': st.R_main, 'main_pcb': st.R_main,
                 'back_zone': 22.25, 'battery_zone': 22.25, 'lower_web': 22.25, 'rear_inner': st.s14geo['outline_r'], 'rear_pcb': st.s14geo['outline_r'],
                 'optics_zone': st.s14geo['pod_r_min'], 'window': st.s14geo['pod_r_min']}
        for k in order:
            z0, z1 = zs[k]
            svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#888" stroke-width="0.4"/>'
                    % (ox, oy + z0 * sz, r_ext[k] * sx, (z1 - z0) * sz, cols[k]))
        rw = rows[az - az % 5]
        for lvl, (z0, z1) in level_z.items():
            ri, ro = rw[lvl]
            svg.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#566573" fill-opacity="0.75"/>' % (ox + ri * sx, oy + z0 * sz, (ro - ri) * sx, (z1 - z0) * sz))
        svg.text(ox, oy + 312, 'scalar side wall; local feature/level envelopes only; no azimuth-resolved wall closure', 9)
    svg.text(20, 806, 'Nominal schematic sections; local REAR-edge margin %s mm is separately checked. Global zero delta does not close it.' % f3(lead['rear_z']['current_margin_mm']), 10)
    return svg.render()


def render_seal_map(res, st):
    lead = next(c for c in res['candidates'] if c['id'] == res['ranking']['order'][0])
    inv = lead['seal_inventory']
    svg = Svg(1180, 720, 'G4 seal map')
    svg.text(20, 26, 'G4 seal inventory and seal-path graph (%s, window %s): %s' % (lead['id'], lead['design_point']['window_variant'],
                                                                               'path CLOSED' if lead['seal_closure']['closed'] else 'path OPEN'), 13, weight='bold')
    comps = sorted(inv['components'])
    pos = {}
    for i, c in enumerate(comps):
        a = 2 * math.pi * i / len(comps)
        pos[c] = (300 + 220 * math.sin(a), 370 - 220 * math.cos(a))
    for s in inv['seals']:
        a, b = s['interface']
        (x0, y0), (x1, y1) = pos[a], pos[b]
        svg.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#2471a3" stroke-width="2"/>' % (x0, y0, x1, y1))
        svg.text((x0 + x1) / 2, (y0 + y1) / 2 - 3, s['id'], 9, 'middle', '#2471a3')
    for c, (x, y) in pos.items():
        svg.add('<rect x="%.1f" y="%.1f" width="120" height="24" rx="5" fill="#fdebd0" stroke="#a04000"/>' % (x - 60, y - 12))
        svg.text(x, y + 4, c, 10, 'middle')
    ly = 70
    svg.text(640, 50, 'seal | type | aperture', 11, weight='bold')
    for s in inv['seals']:
        svg.text(640, ly, '%s | %s | %s' % (s['id'], s['type'], s['aperture']), 10)
        ly += 16
    g = lead['caseback_seal']['gland']
    svg.text(640, ly + 12, 'Caseback main seal: %s cs %s, h %s, g %s, gland tol %s (PROVISIONAL window)' % (g['topology'], f2(g['cs']), f3(g['h']), f2(g['g']), f3(g['tol_h'])), 10)
    svg.text(640, ly + 30, 'Screws outside the seal line (lug roots). No 5 ATM qualification claim (ATM-Q1..Q6 open).', 10, fill='#c0392b')
    return svg.render()


def render_assembly(res, st):
    lead = next(c for c in res['candidates'] if c['id'] == res['ranking']['order'][0])
    a = res['assembly']
    svg = Svg(1180, 760, 'G4 assembly')
    svg.text(20, 26, 'G4 assembly / insertion / service sequence (deterministic; %s)' % ('PASS' if a['pass_'] else 'issues: ' + ', '.join(a['sequence']['issues'])), 13, weight='bold')
    y = 60
    for r in a['sequence']['rows']:
        col = '#1e8449' if r['pass_'] else '#c0392b'
        svg.add('<rect x="20" y="%d" width="760" height="30" rx="4" fill="#fbfcfc" stroke="%s"/>' % (y - 18, col))
        svg.text(30, y, '%s  %s' % (r['id'], r['op'][:110]), 10)
        svg.text(30, y + 9, 'direction: %s | battery: %s%s' % (r['direction'], r['battery_state'], (' | ' + r['dependency'][:60]) if r['dependency'] else ''), 8, fill='#555')
        y += 38
    dp = lead['design_point']
    chk = {x['id']: x for x in lead['checks']}
    svg.text(820, 60, 'Rear-insertion envelope (linear worst margins, mm)', 11, weight='bold')
    yy = 90
    for k in ('H23-INSERT-MAIN', 'H23-INSERT-BATTERY', 'H23-INSERT-REAR'):
        m = chk[k]['linear_worst']
        w_ = max(2.0, min(300.0, abs(m) * 150))
        svg.add('<rect x="820" y="%d" width="%.1f" height="16" fill="%s"/>' % (yy, w_, '#58d68d' if m >= 0 else '#e74c3c'))
        svg.text(830 + w_, yy + 12, '%s %s' % (k, f3(m)), 10)
        yy += 30
    svg.text(800, yy + 20, 'Service: cover debond needed to reach J1', 10, fill='#c0392b')
    svg.text(800, yy + 36, '(gate %s).' % a['service']['gate'], 10, fill='#c0392b')
    svg.text(800, yy + 56, 'Cover-first case sub-assembly is not executable:', 10)
    svg.text(800, yy + 72, 'DISP_LAND lies behind display; clarification required.', 10)
    return svg.render()


# --------------------------------------------------------------------------------------------
# Architecture quotation (architecture.json.g4 summary + architecture.md G4 section)
# --------------------------------------------------------------------------------------------
RECORD_LINE = 'G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES'
KEY_CHECKS = ['H05-STRAIGHT', 'H05-EDGE-XF-J1501', 'H05-EDGE-XB-J201', 'H05-EDGE-XC-J202', 'H05-WALL-SIDE', 'H06-X25-BEZEL', 'H09-U4-HEADROOM',
              'H10-PACK-RADIAL', 'H11-POD-RESIDUAL', 'H01-REAR-PERIPHERY-Z', 'H13-CASEBACK-STRESS', 'H13-CASEBACK-DEFLECTION', 'H15-CB-MAIN-COMP-MIN',
              'H15-CB-MAIN-COMP-MAX', 'H14-SCREW-SEAT', 'H21-BORE-SW1', 'H03-OD', 'H22-LRA-Z-LRA-COIN-D8', 'H22-LRA-Z-LRA-COIN-D10', 'H22-LRA-Z-LRA-LIN-RECT']


def architecture_summary(res, file_sha):
    def key(c):
        chk = {x['id']: x for x in c['checks']}
        return {k: dict(legacy=chk[k]['legacy'], nominal=chk[k]['nominal'], rss=chk[k]['rss'], linear_worst=chk[k]['linear_worst'], pass_=chk[k]['pass'])
                for k in KEY_CHECKS if k in chk}
    d = res['diameter']
    return json.loads(dumps(dict(
        schema='sportwatch-g4-summary/1', verdict=res['verdict'], study_status=res['study_status'],
        independent_review=res['independent_review'], model_limitations=res['model_limitations'], stops=[dict(id=x['id'], text=x['text']) for x in res['stops']],
        g3_record=res['g3_record'], g3_generated_verdict_unchanged=res['g3_generated_verdict_unchanged'],
        owner_decisions=[dict(id=o['id'], date=o['date'], source=o['source'], verbatim=o['verbatim']) for o in res['owner_decisions']],
        deferred_owner_decisions=[o['id'] for o in res['deferred_owner_decisions']], errata=res['errata'],
        selected_candidate=d['selected_candidate'], diameter={k: d[k] for k in ('selected_D', 'minimum_feasible_D', 'margin_to_ceiling_mm', 'minimum_required_D',
                                                                               'minimum_required_D_excluding_H22', 'd_dependent_closure_D', 'd_independent_failures')},
        legacy=dict(conservative_radial_margin_mm=-0.95, x25_conservative_cover_fit_mm=-1.1, reproduced=res['carry_in']['legacy']['pass_']),
        z={b: dict(nominal=r['nominal'], rss=r['rss'], linear=r['linear'], g4_delta=r['g4_delta']) for b, r in res['z']['rows'].items()},
        window=dict(w0=res['window']['w0_status'], od_g4_window_triggered=res['window']['od_g4_window_triggered'], eligible=res['window']['eligible'],
                    w0_span_mm=res['window']['spans_mm']['W0']),
        candidates=[dict(id=c['id'], outcome=c['outcome'], D_eval=c['D_eval'], failing_hard_checks=[h for h, v in sorted(c['hard_checks'].items()) if not v['pass']],
                         key_checks=key(c), h_pod=c['h_pod'], case_side_quadrant_force_bound_N=c['post_load']['per_post_N'],
                         lra_max_height_for_zero_margin_mm={k['id']: k['max_height_for_zero_margin_mm'] for k in c['lra']['classes']})
                    for c in res['candidates']],
        ranking=dict(order=res['ranking']['order'], leader_is_selection=res['ranking']['leader_is_selection']),
        conflict_status={x['id']: x['g4_status'] for x in res['conflict_status']},
        open_gates=res['open_gates'], unsatisfied_acceptance=res['unsatisfied_acceptance'],
        handoff=dict(status=res['handoff']['status'], design_basis=res['handoff']['design_basis']),
        generated_sha256=file_sha, report='design/mechanical/generated/g4_case_sealing.md')))


def architecture_section(res):
    d = res['diameter']
    o = ['<!-- G4 GENERATED BEGIN -->', '## G4 — Case / caseback / sealing-architecture closure study', '',
         '**%s**' % res['verdict'], '', '%s (OD-G4-RECORD); the generated G3 verdict "%s" is unchanged.' % (res['g3_record'], res['g3_generated_verdict_unchanged']), '',
         'Full report: [`generated/g4_case_sealing.md`](generated/g4_case_sealing.md). Generator: `tools/g4_case_sealing.py` (build / check / selftest). '
         'Mechanical parametric / closure study only: no KiCad edit, no RF claim, no FEA claim, no 5 ATM qualification claim.', '',
         '### Stops and owner decisions', '', '| id | finding |', '|---|---|']
    o += ['| %s | %s |' % (x['id'], cell(x['text'])) for x in res['stops']]
    o += ['', 'Deferred (not chosen): ' + ', '.join(x['id'] for x in res['deferred_owner_decisions']) + '.', '',
          '### Diameter (OD-G4-ENVELOPE)', '',
          '- Selected: %s; minimum feasible found: %s; margin to 51.0: %s; minimum required (all hard checks): %s; excluding H22: %s.'
          % (f2(d['selected_D']) if d['selected_D'] else 'none', f2(d['minimum_feasible_D']) if d['minimum_feasible_D'] else 'none',
             f2(d['margin_to_ceiling_mm']) if d['margin_to_ceiling_mm'] is not None else 'n/a',
             f2(d['minimum_required_D']) if d['minimum_required_D'] else 'none <= 54.00', f2(d['minimum_required_D_excluding_H22']) if d['minimum_required_D_excluding_H22'] else 'none <= 54.00'),
          '', '| candidate | outcome | evaluated D | partial group threshold (diagnostic only) | diameter-independent failures | failing hard checks |', '|---|---|---|---|---|---|']
    for c in res['candidates']:
        o.append('| %s | %s | %s | %s | %s | %s |' % (c['id'], c['outcome'], f2(c['D_eval']), f2(c['d_dependent_closure_D']), ', '.join(c['d_independent_failures']) or 'none',
                                                   ', '.join(h for h, v in sorted(c['hard_checks'].items()) if not v['pass']) or 'none'))
    o += ['', '### Legacy vs OD-G4-CORNER (linear worst at the evaluated diameter)', '',
          '| candidate | radial legacy -0.950 -> nominal / RSS / linear worst | X25 legacy -1.100 -> nominal / RSS / linear worst | U4 headroom linear worst | caseback seal comp-min linear worst |',
          '|---|---|---|---|---|']
    for c in res['candidates']:
        chk = {x['id']: x for x in c['checks']}
        r, x = chk['H05-STRAIGHT'], chk['H06-X25-BEZEL']
        cb = chk.get('H15-CB-MAIN-COMP-MIN') or chk.get('H16-CB-BOND-LAND')
        o.append('| %s | %s / %s / %s | %s / %s / %s | %s | %s |' % (c['id'], f3(r['nominal']), f3(r['rss']), f3(r['linear_worst']), f3(x['nominal']), f3(x['rss']),
                                                                   f3(x['linear_worst']), f3(chk['H09-U4-HEADROOM']['linear_worst']), f3(cb['linear_worst']) if cb else 'n/a'))
    z = res['z']
    w = res['window']
    lead = next(c for c in res['candidates'] if c['id'] == res['ranking']['order'][0])
    o += ['', '### Z, window, LRA, seals', '',
          '- Z: ' + '; '.join('%s %s / %s / %s mm' % (b, f3(v['nominal']), f3(v['rss']), f3(v['linear'])) for b, v in sorted(z['rows'].items())) +
          '; G4 delta %s.' % f3(z['g4_z_delta_mm']['nominal']),
          '- Window: W0 %s (span %s mm); OD-G4-WINDOW triggered: %s; eligible: %s.' % (w['w0_status'], f3(w['spans_mm']['W0']), fmtv(w['od_g4_window_triggered']), ', '.join(w['eligible'])),
          '- LRA (%s): ' % lead['id'] + '; '.join('%s Z margin %s mm, max height for zero margin %s mm, feasible poses %d' % (k['id'], f3(k['z_margin_lw']), f3(k['max_height_for_zero_margin_mm']),
                                                                                                                       k['feasible_poses']) for k in lead['lra']['classes']) + '.',
          '- Seal inventory (%s): %d seals, path %s; caseback screws in the lug roots outside the seal line; ATM-Q1..ATM-Q6 carried; no 5 ATM claim.'
          % (lead['id'], lead['seal_closure']['seal_count'], 'closed' if lead['seal_closure']['closed'] else 'open'), '',
          '### Conflict g4_status', '', '| conflict | g4_status |', '|---|---|']
    o += ['| %s | %s |' % (x['id'], x['g4_status']) for x in res['conflict_status']]
    o += ['', 'Errata: ' + '; '.join('%s %s' % (e['id'], e['title']) for e in res['errata']) + '. Unsatisfied acceptance criteria: %s.'
          % ', '.join(str(x) for x in res['unsatisfied_acceptance']), '', 'G4 authorizes no K1, G5 or Q1 work.', '<!-- G4 GENERATED END -->']
    return '\n'.join(o) + '\n'


def outputs(res, st):
    return {'g4_sweep.jsonl': ''.join(dumps(r) for r in sorted(st.sweep_records,key=lambda r:(r['candidate'],r['D']))), 'g4_case_sealing.json': dumps(res), 'g4_case_sealing.md': render_md(res), 'g4_plan.svg': render_plan(res, st),
            'g4_sections.svg': render_sections(res, st), 'g4_seal_map.svg': render_seal_map(res, st), 'g4_assembly.svg': render_assembly(res, st)}


def file_hashes(files):
    return {'design/mechanical/generated/' + k: hashlib.sha256(v.encode()).hexdigest() for k, v in sorted(files.items())}


def readme_section(res):
    return '\n'.join(['## G4 case / caseback / sealing-architecture closure study','',
      '**'+res['verdict']+' — BLOCKED / UNRELEASED STUDY**. Uncommitted. Independent re-review: **PASS AS CORRECT BLOCKED STUDY** (owner-provided record).', '',
      '- Binding contract: `G4_BRIEF.md`; authored geometry/process inputs: `inputs/g4_case_sealing.json`.',
      '- Generator: `tools/g4_case_sealing.py build|check|selftest` (stdlib only).',
      '- Results: `generated/g4_case_sealing.json`, report `generated/g4_case_sealing.md`, full retained-point evidence `generated/g4_sweep.jsonl`.',
      '- Drawings: `generated/g4_plan.svg`, `g4_sections.svg`, `g4_seal_map.svg`, `g4_assembly.svg`.',
      '- `architecture.json.g4` is a compact summary with hashes; conflicts gain exactly one `g4_status`. Evidence resides in the generated G4 report/JSON.',
      '- Complete passing candidate set: '+str(res['ranking']['acceptable'])+'; no selected diameter. Diagnostic thresholds do not imply feasibility.',
      '- Legacy radial −0.950 mm and X25 −1.100 mm remain unchanged. Corrected local process, carrier, button, charger, window and pressure checks are reported.',
      '- LRA stop and OD-G4-WINDOW remain. No G3 reopening demonstrated; OD-G4-STACK is not triggered without proof of necessary total growth.',
      '- Binding cover-first assembly conflict: CONTRACT INTERPRETATION / CLARIFICATION REQUIRED; SERVICE-COVER-REBOND remains open.',
      '- Unsatisfied acceptance criteria: '+', '.join(str(x) for x in res['unsatisfied_acceptance'])+'. Criterion 13 includes the literal legacy later-phase scope incompatibility.',
      '', '`build` regenerates the G4 files and permitted summaries. `check` regenerates in memory, verifies pins/hashes, complete check coverage, scope and budgets, and runs mutation tests. A consistency PASS is not engineering acceptance.',
      '', 'No KiCad, G5, K1 or Q1 work is authorized. No RF performance, structural qualification, 5 ATM qualification or supplier availability claim.', ''])


def update_summaries(res,files):
    path=MECH/'architecture.json';a=load(path)
    a['g4']=architecture_summary(res,file_hashes(files))
    statuses={x['id']:x['g4_status'] for x in res['conflict_status']}
    for c in a['conflicts']:
        c.pop('g4_evidence',None)
        c['g4_status']=statuses[c['id']]
    path.write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n')
    path=MECH/'architecture.md';md=path.read_text()
    begin=md.index('<!-- G4 GENERATED BEGIN -->');end=md.index('<!-- G4 GENERATED END -->',begin)+len('<!-- G4 GENERATED END -->')
    md=md[:begin]+architecture_section(res).rstrip()+md[end:]
    path.write_text(md)
    path=MECH/'README.md';md=path.read_text();begin=md.index('## G4 case / caseback / sealing-architecture closure study')
    record=md[md.index('<!-- G4 RUN RECORD BEGIN -->'):] if '<!-- G4 RUN RECORD BEGIN -->' in md else ''
    path.write_text(md[:begin]+readme_section(res)+'\n'+record)


def check_architecture(res, files):
    fails = []
    a = load(MECH / 'architecture.json')
    want = architecture_summary(res, file_hashes(files))
    if a.get('g4') != want:
        fails.append('architecture.json g4 summary differs from the generated result')
    if len(json.dumps(a.get('g4', {}), indent=2)) > res_budget('architecture_g4_max_bytes'):
        fails.append('architecture.json g4 summary exceeds the size budget')
    if readme_section(res) not in (MECH/'README.md').read_text():
        fails.append('README G4 summary differs from generated result')
    st = {x['id']: x for x in res['conflict_status']}
    for c in a['conflicts']:
        keys = [k for k in c if k.startswith('g4_')]
        if keys != ['g4_status'] or c.get('g4_status') != st.get(c['id'], {}).get('g4_status'):
            fails.append('conflict must gain exactly one g4_status equal to the generated status: ' + c['id'])
    md = (MECH / 'architecture.md').read_text()
    sec = architecture_section(res)
    if sec not in md or md.count('<!-- G4 GENERATED BEGIN -->') != 1 or md.count('<!-- G4 GENERATED END -->') != 1:
        fails.append('architecture.md lacks the exact generated G4 section')
    if len(sec.splitlines()) > res_budget('architecture_md_g4_max_lines'):
        fails.append('architecture.md G4 section exceeds 300 lines')
    if RECORD_LINE not in md.split('<!-- G3 GENERATED BEGIN -->')[0] or RECORD_LINE not in (MECH / 'README.md').read_text():
        fails.append('OD-G4-RECORD status line missing from architecture.md (outside the G3 section) or README.md')
    return fails


def res_budget(key):
    return load(IN_PATH)['budgets'][key]


# --------------------------------------------------------------------------------------------
# Self-test: every section 11 fault injection must be caught by the production predicates
# --------------------------------------------------------------------------------------------
def lra_pose_violations(st, env, poses_ctx):
    ex = lra_exclusions(st)
    c_plan = poses_ctx['c_plan']
    rmin = min(math.hypot(p[0] - 100, p[1] - 100) - rho for p, rho in env)
    viol = ['S14_OUTLINE'] if rmin < st.s14geo['outline_r'] + c_plan else []
    viol += [eid for eid, gg in ex if min(circle_clear(p, rho, gg) for p, rho in env) < c_plan - 1e-9 and eid not in viol]
    return viol


def lra_z_band(st, z_top_from_lower_web_underside, height, budget):
    """An LRA must lie entirely below the lower-web underside (z_top >= 0) and inside the REAR budget."""
    return z_top_from_lower_web_underside >= -1e-9 and z_top_from_lower_web_underside + height <= budget + 1e-9


def bosses_permitted(st, r_case, D, tol):
    """Every radial protrusion beyond D/2 in the case section must be a permitted SW1-SW5 boss (H03)."""
    bad = []
    for row in r_case['rows']:
        for lvl in r_case['levels']:
            ext = row[lvl][1] - D / 2
            if ext > 1e-9 and not (lvl == 'FRONT_GAP' and boss_permitted(st, row['az'], ext, tol)):
                bad.append(dict(az=row['az'], level=lvl, extension_mm=ext))
    return bad


def boss_permitted(st, az, ext, tol):
    w = st.I['parameters']['buttons']['windows_deg']
    inside = any(arc_has(az, a0, a1) for a0, a1 in w.values())
    return inside and ext + tol <= st.I['contract_values']['owner_limits']['boss_extension_max_mm'] + 1e-9


def validate_window_rows(rows):
    return all(r['z_delta_mm'] >= -1e-12 and abs(r['credited_gain_mm']) < 1e-12 for r in rows)


def self_tests(res, st):
    lead = next(c for c in res['candidates'] if c['id'] == res['ranking']['order'][0])
    cand = next(c for c in st.I['candidates'] if c['id'] == lead['id'])
    sp = Specs(st, cand)
    dp = dict(lead['design_point'])
    poses_ctx = dict(c_plan=st.I['parameters']['c_lra_plan_mm']['max'])
    T = []

    def t(name, caught):
        T.append(dict(id=name, caught=bool(caught)))
    bad = dict(dp, tw=dp['tw'] + 0.6)
    t('radial_collision_linear_worst', run_check(sp.straight(bad), full=False) < 0 and not fix_pass(run_check(sp.straight(bad)))['pass'])
    inp = copy.deepcopy(st.I)
    inp['contract_values']['legacy']['conservative_radial_margin_mm'] = -0.94
    t('legacy_value_mutated', not Study(inp, verify=False).legacy['pass_'])
    lim = st.I['contract_values']['owner_limits']['nominal_mm']
    zc = z_compliance(st, res['window'], extra_delta=lim + 0.001 - st.z['G2-REVA']['reproduced']['nominal'])
    t('t_total_16_501_nominal', not zc['pass_'] and abs(zc['rows']['G2-REVA']['nominal'] - 16.501) < 1e-9)
    t('d_case_body_51_01', run_check(sp.od(dict(dp, D=51.01)), full=False) < 0)
    rc = copy.deepcopy(lead['r_case'])
    clean = not bosses_permitted(st, rc, dp['D'], sp.pc_mid['boss_mm'])
    rc['rows'][0]['MAIN'][1] = dp['D'] / 2 + 0.5
    t('unpermitted_boss', clean and bool(bosses_permitted(st, rc, dp['D'], sp.pc_mid['boss_mm'])))
    inv = copy.deepcopy(lead['seal_inventory'])
    inv['components']['MIDCASE'][2]['seal'] = None
    t('aperture_without_seal', not seal_closure(inv)['closed'])
    gd = lead['caseback_seal']['gland']
    over = sp.gland('MUT', 'static_radial', gd['cs'] or 0.6, (gd['h'] or 0.45) * 0.7, gd['g'] or 1.0, gd['tol_h'] or 0.04, gd['tol_g'] or 0.02)[1]
    t('oring_overcompression', run_check(over, full=False) < 0)
    F = [dict(id='MUT_METAL', geom=dict(type='circles', circles=[[101.0, 78.3, 0.5]]), z=['MAIN'], conductive=True, ferromagnetic=False, kind='mutant')]
    t('conductive_part_in_gnss_rad', not rf_mag_check(st, F)['h17_pass'])
    F = [dict(id='MUT_WIRE', geom=sector(115.0, 120.0, 21.0, 22.0), z=['REAR'], conductive=True, ferromagnetic=False, kind='new wiring', wiring=True)]
    t('new_wiring_in_wifi_rad', not rf_mag_check(st, F)['h17_pass'])
    F = [dict(id='MUT_SCREW', geom=dict(type='circles', circles=[[st.u703[0], st.u703[1] + 3.0, 0.4]]), z=['REAR'], conductive=True, ferromagnetic=True,
              kind='caseback screw')]
    t('ferromagnetic_screw_in_mag_clear', not rf_mag_check(st, F)['h18_pass'])
    land = st.s14geo['supports'][0]
    F = [dict(id='MUT_BLOCK', geom=dict(type='circles', circles=[[land['centre'][0], land['centre'][1], 0.3]]), z=['REAR'], conductive=False,
              ferromagnetic=False, kind='mutant')]
    t('obstructed_s14_support_land', not s14_untouched(st, F, dp)['pass_'])
    cls = st.I['lra_classes'][0]
    env = [(xy(10.0, 200.0), cls['diameter_mm']['max'] / 2)]
    t('lra_pose_inside_rear_outline', 'S14_OUTLINE' in lra_pose_violations(st, env, poses_ctx))
    web = st.layer('lower_web')
    t('lra_hidden_in_lower_web', not lra_z_band(st, -web, 0.3, st.rear_alloc_min()))
    t('rear_insertion_collision', run_check(sp.insert(dp, 'REAR', r_rear=dp['D'] / 2 - dp['tw']), full=False) < 0)
    s14 = st.s14
    mir = copy.deepcopy(s14['supports'][0]['polygon'])
    mir['assembly_mm'] = [[100 + p[0], 100 + p[1]] for p in mir['rear_mm']]
    t('mirrored_rear_transform', not frame_ok(mir) and frame_ok(s14['supports'][0]['polygon']))
    rows = copy.deepcopy(res['window']['rows'])
    thin = next(r for r in rows if r['t_window_mm'] < 0.5)
    thin['credited_gain_mm'] = -0.2
    t('window_thickness_gain_credited', validate_window_rows(res['window']['rows']) and not validate_window_rows(rows))
    s_ = sp.straight(dp)
    for term in s_['terms']:
        if term.name == 't_fpc':
            term.adv = 0.15
    try:
        validate_terms(s_['terms'])
        caught = False
    except StudyError:
        caught = True
    t('supplier_gated_term_narrowed', caught)
    domains=copy.deepcopy(lead['post_load']['domains'])
    t('pressure_domains_nonoverlap_accounting',pressure_domains_valid(domains,lead['post_load']['total_area_mm2']) and
      not pressure_domains_valid(domains+[domains[0]],lead['post_load']['total_area_mm2']))
    edges=list(load_paths(st.I['candidates'][0])['edges'])
    t('forbidden_pressure_branch_alongside_valid_path',path_check(edges)['pass_'] and not path_check(edges+[('WINDOW','PACK'),('PACK','MIDCASE')])['pass_'])
    omitted=sp.bore(dp,'SW1',0.9); omitted['terms']=[x for x in omitted['terms'] if x.name!='c_switch_mm']
    try: run_check(omitted); caught=False
    except StudyError: caught=True
    t('omitted_button_travel',caught)
    bsp=Specs(st,st.I['candidates'][1]);bsp.button_process=lambda sw:bsp.pc_mid
    try: bsp.bore(dp,'SW5',0.9);caught=False
    except StudyError:caught=True
    t('wrong_local_polymer_process',caught)
    t('carrier_wall_below_minimum',run_check(sp.carrier_wall(dict(dp,tcw=0.30)),False)<0 and abs(run_check(sp.carrier_wall(dict(dp,tcw=0.35)),False))<EPS)
    t('charger_4x5_containment_failure',not charger_fit(st,sp,dict(dp,chg_r_out=22.0))['pass_'])
    impossible=dict(cs=0.5,h=0.39,g=1.,tol_h=0.10,tol_g=0.03)
    zero=seal_threshold(st,'static_radial',impossible)
    t('zero_tolerance_infeasible_oring',not zero['zero_cs_tolerance_feasible'] and zero['maximum_symmetric_cs_tolerance_mm'] is None)
    glass=next(x for x in res['window']['rows'] if x['id']=='W1-t0p3-cs_glass')
    t('window_minimum_thickness_failure',glass['minimum_thickness_mm']<glass['t_window_mm'] and not glass['stress_pass'])
    empty=summarize_hard(st,[],{})
    t('vacuous_H07_H08',not empty['H07']['pass'] and not empty['H08']['pass'])
    ce=CandidateEval(st,cand,dict(window=res['window'],lra=dict(poses=[],c_plan=poses_ctx['c_plan'])))
    t('incomplete_lra_exclusion',bool(local_pose_violations(st,ce,dp,[(xy(20,200),0.1)],ex=[])))
    fake={h:dict(pass_=True,margins={'test':1}) for h in HARD}
    fake.pop('H07')
    t('partial_candidate_without_all_hard_checks',not complete_candidate(fake))
    proud=copy.copy(st);proud.P=copy.deepcopy(st.P);proud.P['cover_recess_depth_mm']['nom']=-0.10
    t('cover_feature_proud',not cover_proud(proud,sp,dp)['pass_'])
    t('assembly_cover_first_not_silently_replaced',not st.assembly['pass_'] and st.assembly['disposition']=='CONTRACT INTERPRETATION / CLARIFICATION REQUIRED')
    bypass=lead['post_load']['case_side_bypass_screen']
    passing=dict(bypass,stress_margin_MPa=1.,deflection_margin_mm=0.01,evidence_class='MANUFACTURER_DATA_REQUIRED')
    t('H13_bypass_numeric_not_evidence_literal',not bypass_structural_pass(bypass) and bypass_structural_pass(passing)
      and not bypass_structural_pass(dict(passing,stress_margin_MPa=-0.01))
      and not bypass_structural_pass(dict(passing,deflection_margin_mm=0.)))
    t('polygon_contact_not_missed',polygon_overlap([(0,0),(1,0),(1,1),(0,1)],dict(type='rect',rect=[0.99,0.4,1.5,0.5])))
    return T


# --------------------------------------------------------------------------------------------
# check / build / selftest
# --------------------------------------------------------------------------------------------
def validate(res, st, files, elapsed):
    fails = []
    for name, text in files.items():
        p = GEN / name
        if not p.is_file() or p.read_bytes() != text.encode('utf-8'):
            fails.append(name + ': missing or differs from regeneration')
    if not res['carry_in']['legacy']['pass_']:
        fails.append('LEGACY mismatch')
    if not all(c['pass_'] for c in st.s14geo['carry_in_checks']):
        fails.append('G3-B-S14 carry-in mismatch')
    rec = [c for c in res['candidates'] if c['outcome'] == 'RECOMMENDED']
    for c in rec:
        if not all(h['pass'] for h in c['hard_checks'].values()):
            fails.append('RECOMMENDED candidate has a failing hard check')
    d = res['diameter']
    if (rec and d['selected_D'] != rec[0]['D_min_feasible']) or (not rec and d['selected_D'] is not None):
        fails.append('selected diameter is not the RECOMMENDED candidate D_min_feasible')
    if d['selected_D'] is not None and d['selected_D'] > 51.0 + 1e-9:
        fails.append('selected diameter above the 51.0 mm ceiling')
    if any(v > EPS for v in res['z']['g4_z_delta_mm'].values()) and not any(s['id'] == 'OD-G4-STACK' for s in res['stops']):
        fails.append('unreported nonzero Z delta')
    for row in st.sweep_records:
        if set(row['hard_checks'])!=set(HARD) or row['feasible'] != all(x['pass_'] for x in row['hard_checks'].values()):
            fails.append('incomplete or inconsistent hard-check sweep record')
    if not validate_window_rows(res['window']['rows']):
        fails.append('window thickness gain credited')
    if len(files['g4_case_sealing.json'].encode()) > res_budget('generated_json_max_bytes'):
        fails.append('generated JSON exceeds 2 MB')
    if elapsed > res_budget('check_runtime_max_s'):
        fails.append('check runtime %.1f s exceeds budget' % elapsed)
    if not res['scope']['pass_']:
        fails.append('scope check failed: ' + ', '.join(k for k, v in res['scope']['checks'].items() if not v))
    fails += check_architecture(res, files)
    return fails


def main(argv):
    if len(argv) != 2 or argv[1] not in ('build', 'check', 'selftest'):
        sys.stderr.write('usage: g4_case_sealing.py build|check|selftest\n')
        return 2
    t0 = time.time()
    try:
        timing = {}
        res = build_results(timing)
        st = timing['study']
        files = outputs(res, st)
        if argv[1] == 'build':
            for name, text in files.items():
                (GEN / name).write_bytes(text.encode('utf-8'))
            update_summaries(res,files)
            print(json.dumps(dict(status='BUILT', verdict=res['verdict'], files=sorted(files), stops=[s['id'] for s in res['stops']], runtime_s=round(time.time()-t0,2)), sort_keys=True))
            return 0
        if argv[1] == 'selftest':
            tests = self_tests(res, st)
            ok = all(x['caught'] for x in tests) and len(tests) >= 28
            print(json.dumps(dict(status='PASS' if ok else 'FAIL', mutations=len(tests), caught=sum(x['caught'] for x in tests), tests=tests), sort_keys=True))
            return 0 if ok else 1
        tests = self_tests(res, st)
        fails = validate(res, st, files, time.time() - t0)
        fails += ['self-test not caught: ' + x['id'] for x in tests if not x['caught']]
        print(json.dumps(dict(status='PASS' if not fails else 'FAIL', failures=fails, engineering_verdict=res['verdict'],
                              stops=[s['id'] for s in res['stops']], selected_candidate=res['diameter']['selected_candidate'],
                              unsatisfied_acceptance=res['unsatisfied_acceptance'], runtime_s=round(time.time() - t0, 1)), sort_keys=True))
        return 0 if not fails else 1
    except StudyError as exc:
        print(json.dumps(dict(status='STOP', reason=str(exc))))
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
