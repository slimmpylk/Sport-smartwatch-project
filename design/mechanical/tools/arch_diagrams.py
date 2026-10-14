#!/usr/bin/env python3
"""Deterministic diagram generator and consistency checker for the Rev-A
multi-board mechanical architecture package (design/mechanical/).

Stdlib only.  Inputs (read-only): design/mechanical/architecture.json plus the
deterministic outputs of tools/mech_model.py (generated/zstack.json,
generated/main_height_map.json) and the input register / placement / interface
contracts used for cross-checks.

    arch_diagrams.py build   write the three SVGs into design/mechanical/generated/
    arch_diagrams.py check   regenerate in memory, byte-compare, run the
                             consistency checks; never writes; exit 0 only on pass

Determinism: fixed float formatting, no timestamps, LF endings, trailing newline.
"""
import hashlib
import json
import math
import re
import sys
import xml.dom.minidom
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[3]
MECH = ROOT / "design" / "mechanical"
GEN = MECH / "generated"
ARCH = MECH / "architecture.json"
ARCH_MD = MECH / "architecture.md"
README = MECH / "README.md"
REGISTER = MECH / "inputs" / "input_register.json"
ZSTACK = GEN / "zstack.json"
HEIGHTS = GEN / "main_height_map.json"
PLACEMENT = ROOT / "design" / "placement" / "phase1_placement.json"
IFACE = ROOT / "design" / "interfaces" / "main_rear_interface.json"
CHARGER_MD = ROOT / "design" / "interfaces" / "charger_harness.md"

SVG_FILES = {
    "perimeter_map": GEN / "perimeter_map.svg",
    "rear_module_concept": GEN / "rear_module_concept.svg",
    "interconnect_paths": GEN / "interconnect_paths.svg",
}
SOURCE_FILES = {
    "design/mechanical/inputs/input_register.json": REGISTER,
    "design/mechanical/generated/zstack.json": ZSTACK,
    "design/mechanical/generated/main_height_map.json": HEIGHTS,
    "design/placement/phase1_placement.json": PLACEMENT,
    "design/interfaces/main_rear_interface.json": IFACE,
}

CX = CY = 100.0           # MAIN origin (front view; north = -Y, east = +X)
R_CLIP = 25.25            # nominal case outer radius: reservations are clipped here
CELL = 0.25               # grid step for derived ranges / centroids / areas, mm
AREA_STEP = 0.05          # sampling step for the pack-edge support-window areas, mm
CLASSES = ("KNOWN", "PARAMETRIC", "SUPPLIER_DATA_REQUIRED")
Z_LEVELS = ("FRONT", "MAIN", "BATTERY", "REAR")
SEVERITIES = ("HIGH", "MEDIUM", "LOW")
Z_COLOR = {"FRONT": "#4e79a7", "MAIN": "#59a14f", "BATTERY": "#f28e2b", "REAR": "#b07aa1"}
Z_BADGE = {"FRONT": "F", "MAIN": "M", "BATTERY": "B", "REAR": "R"}


# --------------------------------------------------------------------------- io
def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh, object_pairs_hook=_unique_pairs)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def f2(v):
    return "%.2f" % (0.0 if abs(v) < 0.005 else v)


def f1(v):
    return "%.1f" % (0.0 if abs(v) < 0.05 else v)


# ------------------------------------------------------------------- geometry
def az_of(x, y):
    return math.degrees(math.atan2(x - CX, -(y - CY))) % 360.0


def in_arc(a, lo, hi):
    if hi - lo >= 360.0:
        return True
    lo %= 360.0
    hi %= 360.0
    return (lo <= a <= hi) if lo <= hi else (a >= lo or a <= hi)


def contains(g, x, y):
    t = g["type"]
    if t == "rect":
        x0, y0, x1, y1 = g["rect"]
        return x0 <= x <= x1 and y0 <= y <= y1
    if t == "sector":
        r = math.hypot(x - CX, y - CY)
        return g["r"][0] <= r <= g["r"][1] and in_arc(az_of(x, y), g["az"][0], g["az"][1])
    if t == "circles":
        return any(math.hypot(x - c[0], y - c[1]) <= c[2] for c in g["circles"])
    raise ValueError("unknown geometry type %r" % t)


def grid_points():
    n = int(round(2 * R_CLIP / CELL))
    for i in range(n):
        x = CX - R_CLIP + (i + 0.5) * CELL
        for j in range(n):
            y = CY - R_CLIP + (j + 0.5) * CELL
            if math.hypot(x - CX, y - CY) <= R_CLIP:
                yield x, y


_GRID = None


def grid():
    global _GRID
    if _GRID is None:
        _GRID = list(grid_points())
    return _GRID


def sample_cells(g):
    return frozenset((x, y) for x, y in grid() if contains(g, x, y))


def cell_ranges(cells):
    """az_from, az_to (wrapped through north when from > to), r_min, r_max, area, centroid."""
    azs = sorted(az_of(x, y) for x, y in cells)
    rs = [math.hypot(x - CX, y - CY) for x, y in cells]
    gaps = [(azs[(i + 1) % len(azs)] - azs[i]) % 360.0 for i in range(len(azs))]
    i = max(range(len(gaps)), key=lambda k: gaps[k])
    if gaps[i] < 1e-9:
        a0, a1 = 0.0, 360.0
    else:
        a0, a1 = azs[(i + 1) % len(azs)], azs[i]
    mx = sum(x for x, _ in cells) / len(cells)
    my = sum(y for _, y in cells) / len(cells)
    return a0, a1, min(rs), max(rs), len(cells) * CELL * CELL, mx, my


def clock_str(az):
    minutes = int(round((az % 360.0) * 2.0)) % 720
    h = (minutes // 60) % 12
    return "%d:%02d" % (12 if h == 0 else h, minutes % 60)


def derive_reservations(reservations):
    """Return {id: derived dict} for every reservation (ranges, centroid, cells)."""
    out = {}
    for r in reservations:
        cells = sample_cells(r["geometry"])
        if not cells:
            # thinner than the sampling grid: use the bounding-box centre so ranges stay defined (area ~ 0)
            b = geom_bbox(r["geometry"])
            cells = frozenset([((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)])
            a0, a1, r0, r1, _, mx, my = cell_ranges(cells)
            out[r["id"]] = {"cells": frozenset(), "az": [a0, a1], "r": [r0, r1], "area": 0.0, "centroid": [mx, my]}
            continue
        a0, a1, r0, r1, area, mx, my = cell_ranges(cells)
        out[r["id"]] = {"cells": cells, "az": [a0, a1], "r": [r0, r1], "area": area, "centroid": [mx, my]}
    return out


def geom_bbox(g):
    t = g["type"]
    if t == "rect":
        return tuple(g["rect"])
    if t == "circles":
        return (min(c[0] - c[2] for c in g["circles"]), min(c[1] - c[2] for c in g["circles"]),
                max(c[0] + c[2] for c in g["circles"]), max(c[1] + c[2] for c in g["circles"]))
    r0, r1 = g["r"]
    a0, a1 = g["az"]
    if a1 - a0 >= 360.0:
        return (CX - r1, CY - r1, CX + r1, CY + r1)
    pts = []
    n = 360
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        for r in (r0, r1):
            pts.append((CX + r * math.sin(a), CY - r * math.cos(a)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------- analytic overlap detection
# Every reservation is a union of "pieces"; a piece is the intersection of open atoms:
#   ("box", x0, y0, x1, y1)  open rectangle
#   ("disc", cx, cy, r)      open disc
#   ("out", cx, cy, r)       complement of the closed disc
#   ("half", az, +1 / -1)    open half-plane through the watch centre: azimuths (az, az+180) / (az-180, az)
# For a fixed x every atom's cross-section is an exact union of open y-intervals.  The
# x-axis is cut at every x where any two boundary curves (lines / circles, extended)
# meet, at circle extremes and at vertical lines; between two consecutive cuts the
# order of all interval end-point functions is fixed, so the cross-section length of
# A n B n case-clip is either positive everywhere or zero everywhere in that strip.
# Two interiors therefore overlap iff the length is positive at some strip midpoint.
# Coincident boundaries give identical floats (same formula), so abutting shapes give
# length exactly 0; thin, contained and coincident shapes give a positive length.
INF = float("inf")
LEN_NOISE = 1e-9          # mm: float noise floor of a cross-section length (not an area threshold)
X_GAP_MIN = 1e-12         # mm: strips narrower than this carry no area
GL_SUB = 4                # area: sub-strips per strip
GL_N = 12                 # area: Gauss-Legendre points per sub-strip


def _sc(a):
    """sin / cos of an azimuth in degrees, exact at multiples of 90."""
    a = a % 360.0
    exact = {0.0: (0.0, 1.0), 90.0: (1.0, 0.0), 180.0: (0.0, -1.0), 270.0: (-1.0, 0.0)}
    if a in exact:
        return exact[a]
    t = math.radians(a)
    return math.sin(t), math.cos(t)


def geom_pieces(g):
    t = g["type"]
    if t == "rect":
        return [[("box",) + tuple(g["rect"])]]
    if t == "circles":
        return [[("disc", c[0], c[1], c[2])] for c in g["circles"]]
    if t != "sector":
        raise ValueError("unknown geometry type %r" % t)
    r0, r1 = g["r"]
    a0, a1 = g["az"]
    if r1 <= r0:
        return []
    base = [("disc", CX, CY, r1)] + ([("out", CX, CY, r0)] if r0 > 0.0 else [])
    span = a1 - a0
    if span >= 360.0:
        return [base]
    if span < 0.0:
        span += 360.0
    if span <= 0.0:
        return []
    if span < 180.0:
        return [base + [("half", a0, 1), ("half", a1, -1)]]
    if span == 180.0:
        return [base + [("half", a0, 1)]]
    return [base + [("half", a0, 1)], base + [("half", a1, -1)]]


def _atom_ivals(atom, x):
    k = atom[0]
    if k == "box":
        _, x0, y0, x1, y1 = atom
        return [(y0, y1)] if (x0 < x < x1 and y0 < y1) else []
    if k in ("disc", "out"):
        _, cx, cy, r = atom
        dd = r * r - (x - cx) ** 2
        if k == "disc":
            if dd <= 0.0:
                return []
            s = math.sqrt(dd)
            return [(cy - s, cy + s)]
        if dd <= 0.0:
            return [(-INF, INF)]
        s = math.sqrt(dd)
        return [(-INF, cy - s), (cy + s, INF)]
    _, a, sign = atom
    sa, ca = _sc(a)
    if sa == 0.0:
        return [(-INF, INF)] if sign * ca * (x - CX) > 0.0 else []
    yb = CY - ca * (x - CX) / sa
    return [(yb, INF)] if sign * sa > 0.0 else [(-INF, yb)]


def _isect(a, b):
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if lo < hi:
            out.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def _union(lists):
    out = []
    for lo, hi in sorted(iv for lst in lists for iv in lst):
        if out and lo < out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def _shape_ivals(pieces, x):
    lists = []
    for p in pieces:
        iv = [(-INF, INF)]
        for atom in p:
            iv = _isect(iv, _atom_ivals(atom, x))
            if not iv:
                break
        lists.append(iv)
    return _union(lists)


def _pieces_xrange(pieces):
    lo, hi = INF, -INF
    for p in pieces:
        plo, phi = -INF, INF
        for atom in p:
            if atom[0] == "box":
                plo, phi = max(plo, atom[1]), min(phi, atom[3])
            elif atom[0] == "disc":
                plo, phi = max(plo, atom[1] - atom[3]), min(phi, atom[1] + atom[3])
        if phi > plo:
            lo, hi = min(lo, plo), max(hi, phi)
    return lo, hi


def _critical_x(all_pieces):
    lines, circles, xs = [], [], []
    for pieces in all_pieces:
        for p in pieces:
            for atom in p:
                if atom[0] == "box":
                    _, x0, y0, x1, y1 = atom
                    xs += [x0, x1]
                    lines += [(0.0, 1.0, y0), (0.0, 1.0, y1)]
                elif atom[0] in ("disc", "out"):
                    _, cx, cy, r = atom
                    circles.append((cx, cy, r))
                    xs += [cx - r, cx + r]
                else:
                    sa, ca = _sc(atom[1])
                    if sa == 0.0:
                        xs.append(CX)
                    else:
                        lines.append((ca, sa, ca * CX + sa * CY))
    lines, circles = sorted(set(lines)), sorted(set(circles))
    for i, (a1, b1, c1) in enumerate(lines):
        for a2, b2, c2 in lines[i + 1:]:
            det = a1 * b2 - a2 * b1
            if abs(det) > 1e-15:
                xs.append((c1 * b2 - c2 * b1) / det)
        for cx, cy, r in circles:
            k, m = -a1 / b1, c1 / b1 - cy
            qa, qb, qc = 1.0 + k * k, 2.0 * (k * m - cx), cx * cx + m * m - r * r
            xs.append(-qb / (2.0 * qa))
            disc = qb * qb - 4.0 * qa * qc
            if disc >= 0.0:
                s = math.sqrt(disc)
                xs += [(-qb - s) / (2.0 * qa), (-qb + s) / (2.0 * qa)]
    for i, (x1, y1, r1) in enumerate(circles):
        for x2, y2, r2 in circles[i + 1:]:
            dd = math.hypot(x2 - x1, y2 - y1)
            if dd < 1e-15:
                continue
            a = (dd * dd + r1 * r1 - r2 * r2) / (2.0 * dd)
            px = x1 + a * (x2 - x1) / dd
            h = math.sqrt(max(0.0, r1 * r1 - a * a))
            xs += [px, px + h * (y2 - y1) / dd, px - h * (y2 - y1) / dd]
    return xs


def _sweep(ga, gb, clip):
    """Shared set-up: piece lists and the sorted strip cuts inside the common x-range."""
    pa, pb = geom_pieces(ga), geom_pieces(gb)
    pc = [[("disc", CX, CY, clip)]]
    ra, rb = _pieces_xrange(pa), _pieces_xrange(pb)
    lo, hi = max(ra[0], rb[0], CX - clip), min(ra[1], rb[1], CX + clip)
    if not (hi - lo > X_GAP_MIN):
        return pa, pb, pc, []
    cuts = sorted({v for v in _critical_x((pa, pb, pc)) if lo < v < hi} | {lo, hi})
    return pa, pb, pc, cuts


def _xlen(pa, pb, pc, x):
    iv = _isect(_isect(_shape_ivals(pa, x), _shape_ivals(pb, x)), _shape_ivals(pc, x))
    return sum(h - l for l, h in iv)


def interiors_overlap(ga, gb, clip=R_CLIP):
    """Exact overlap predicate of the open interiors (clipped at `clip`); abutting is not an overlap."""
    pa, pb, pc, cuts = _sweep(ga, gb, clip)
    for u, v in zip(cuts, cuts[1:]):
        if v - u > X_GAP_MIN and _xlen(pa, pb, pc, 0.5 * (u + v)) > LEN_NOISE:
            return True
    return False


_GL = None


def _gauss_legendre():
    global _GL
    if _GL is None:
        nodes, weights = [], []
        for i in range(1, GL_N + 1):
            x = math.cos(math.pi * (i - 0.25) / (GL_N + 0.5))
            for _ in range(100):
                p0, p1 = 1.0, x
                for k in range(2, GL_N + 1):
                    p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
                dp = GL_N * (x * p1 - p0) / (x * x - 1.0)
                step = p1 / dp
                x -= step
                if abs(step) < 1e-15:
                    break
            nodes.append(x)
            weights.append(2.0 / ((1.0 - x * x) * dp * dp))
        _GL = (nodes, weights)
    return _GL


def overlap_area(ga, gb, clip=R_CLIP):
    """Area estimate of the overlap (Gauss-Legendre over the same strips); reporting only, never a detector."""
    pa, pb, pc, cuts = _sweep(ga, gb, clip)
    nodes, weights = _gauss_legendre()
    total = 0.0
    for u, v in zip(cuts, cuts[1:]):
        if v - u <= X_GAP_MIN:
            continue
        h = (v - u) / GL_SUB
        for k in range(GL_SUB):
            a = u + k * h
            for t, w in zip(nodes, weights):
                total += 0.5 * h * w * _xlen(pa, pb, pc, a + 0.5 * h * (t + 1.0))
    return total


def _t_rect(x0, y0, x1, y1):
    return {"type": "rect", "rect": [x0, y0, x1, y1]}


def _t_sec(a0, a1, r0, r1):
    return {"type": "sector", "az": [a0, a1], "r": [r0, r1]}


def _t_circ(*cs):
    return {"type": "circles", "circles": [list(c) for c in cs]}


# Built-in regression cases for the detector (run by `check`): (name, A, B, overlap?, exact area or None).
OVERLAP_SELF_TESTS = (
    ("identical thin rects (review F1 case)", _t_rect(99, 99, 109, 99.02), _t_rect(99, 99, 109, 99.02), True, 0.2),
    ("thin rect inside a rect", _t_rect(99, 99, 109, 99.02), _t_rect(98, 98, 110, 100), True, 0.2),
    ("0.001 mm sliver", _t_rect(95, 95, 100, 100), _t_rect(99.999, 95, 105, 100), True, 0.005),
    ("contained rect", _t_rect(96, 96, 97, 97), _t_rect(95, 95, 100, 100), True, 1.0),
    ("rects abutting on x", _t_rect(95, 95, 100, 100), _t_rect(100, 95, 105, 100), False, None),
    ("rects abutting on y", _t_rect(95, 95, 100, 100), _t_rect(95, 100, 100, 105), False, None),
    ("rects touching at a corner", _t_rect(95, 95, 100, 100), _t_rect(100, 100, 105, 105), False, None),
    ("zero-width rect", _t_rect(97, 95, 97, 100), _t_rect(95, 95, 100, 100), False, None),
    ("sectors sharing a ray", _t_sec(80, 100, 10, 20), _t_sec(100, 260, 10, 20), False, None),
    ("sectors sharing a radius", _t_sec(0, 360, 0, 12.65), _t_sec(150, 180, 12.65, 22), False, None),
    ("sectors overlapping by 0.01 deg", _t_sec(80, 100.01, 10, 20), _t_sec(100, 260, 10, 20), True,
     math.radians(0.01) * (20 ** 2 - 10 ** 2) / 2.0),
    ("0.01 deg sector across a rect", _t_sec(90, 90.01, 10, 20), _t_rect(105, 95, 125, 105), True, None),
    ("rect abutting the south ray of a sector", _t_sec(90, 180, 5, 20), _t_rect(97, 106, 100, 108), False, None),
    ("rect crossing the south ray by 0.001 mm", _t_sec(90, 180, 5, 20), _t_rect(97, 106, 100.001, 108), True, 0.002),
    ("sector wrapped through north", _t_sec(350, 10, 10, 20), _t_rect(99, 82, 101, 85), True, 6.0),
    ("circles tangent", _t_circ((95, 100, 2)), _t_circ((99, 100, 2)), False, None),
    ("circles overlapping by 0.002 mm", _t_circ((95, 100, 2)), _t_circ((98.998, 100, 2)), True, None),
    ("circle tangent to a rect edge", _t_circ((100, 100, 2)), _t_rect(102, 95, 105, 105), False, None),
    ("circle inside an annulus hole", _t_circ((100, 100, 5)), _t_sec(0, 360, 5, 10), False, None),
    ("circle inside an annulus ring", _t_circ((107.5, 100, 1)), _t_sec(0, 360, 5, 10), True, math.pi),
    ("full disc versus identical circle", _t_sec(0, 360, 0, 3), _t_circ((100, 100, 3)), True, 9.0 * math.pi),
    ("zero-thickness annulus", _t_sec(0, 360, 5, 5), _t_sec(0, 360, 0, 10), False, None),
    ("overlap only outside the case clip", _t_rect(126, 95, 130, 105), _t_rect(127, 95, 131, 105), False, None),
)


def overlap_self_test():
    fails = []
    for name, ga, gb, want, area in OVERLAP_SELF_TESTS:
        for g1, g2 in ((ga, gb), (gb, ga)):
            got = interiors_overlap(g1, g2)
            if got != want:
                fails.append("overlap self-test '%s': detector returned %s, expected %s" % (name, got, want))
        if area is not None:
            est = overlap_area(ga, gb)
            if abs(est - area) > max(1e-4, 1e-3 * area):
                fails.append("overlap self-test '%s': area %.6f, expected %.6f" % (name, est, area))
    return fails


def overlap_pairs(reservations):
    pairs = []
    n = len(reservations)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = reservations[i], reservations[j]
            common = sorted(set(a["z_levels"]) & set(b["z_levels"]))
            if common and interiors_overlap(a["geometry"], b["geometry"]):
                pairs.append((a["id"], b["id"], common, round(overlap_area(a["geometry"], b["geometry"]), 2)))
    return pairs


# ------------------------------------------------------- tool-output accessors
def corner_layers(zs, corner):
    return {l["id"]: l["thickness_mm"] for l in zs["corners"][corner]["layers"]}


def radial_corner(zs, corner):
    c = zs["radial"]["corners"][corner]
    vals = {k: v["value_mm"] if isinstance(v, dict) else v for k, v in c["checks"].items()}
    return c["parameters"], vals


def check_value(zs, corner, name):
    chk = zs["radial"]["corners"][corner]["checks"][name]
    return chk["value_mm"] if isinstance(chk, dict) else chk


def stack_param(zs, name, which):
    return zs["parameters"][name][which]


# --------------------------------------------------------- derived quantities
SCEN_TOL_PARAMS = ("t_display", "c_front", "t_main", "c_back", "t_insulator",
                   "tol_pack_thick", "g_axial", "c_axial", "h_optics_max", "c_optics")


def tolerance_deltas(zs):
    return {p: round(stack_param(zs, p, "max") - stack_param(zs, p, "nom"), 4) for p in SCEN_TOL_PARAMS}


def derive_scenarios(arch, zs):
    """Scenario totals from tool layer outputs; design choices fixed, tolerances stacked.

    G1 (2026-10-11): the tool nominal IS the G1 baseline (OD-COVER separate cover lens
    + OD-REAR-SIDED double-sided REAR integrated as explicit stack layers). The rows are
    therefore G1-relative configurations: `cover` adds/removes the whole cover stack
    (t_cover + t_cover_bond), `double_sided_rear` adds/removes the whole inner-side stack
    (h_rear_inner + c_rear_inner); window / REAR PCB / lower web stay max-design choices.
    """
    nom = zs["corners"]["nominal"]["T_total_mm"]
    thick = zs["corners"]["thick"]["T_total_mm"]
    tol = tolerance_deltas(zs)
    tol_lin = sum(tol.values())
    tol_rss = math.sqrt(sum(v * v for v in tol.values()))
    d_cover_nom = stack_param(zs, "t_cover", "nom") + stack_param(zs, "t_cover_bond", "nom")
    d_cover_tol = ((stack_param(zs, "t_cover", "max") - stack_param(zs, "t_cover", "nom"))
                   + (stack_param(zs, "t_cover_bond", "max") - stack_param(zs, "t_cover_bond", "nom")))
    d_inner_nom = stack_param(zs, "h_rear_inner", "nom") + stack_param(zs, "c_rear_inner", "nom")
    d_inner_tol = ((stack_param(zs, "h_rear_inner", "max") - stack_param(zs, "h_rear_inner", "nom"))
                   + (stack_param(zs, "c_rear_inner", "max") - stack_param(zs, "c_rear_inner", "nom")))
    cl = {c: corner_layers(zs, c) for c in ("nominal", "thick")}
    d_window = cl["thick"]["window"] - cl["nominal"]["window"]
    d_pcb = cl["thick"]["rear_pcb"] - cl["nominal"]["rear_pcb"]
    d_web = cl["thick"]["lower_web"] - cl["nominal"]["lower_web"]
    lo, hi = zs["conventions"]["target_thickness_mm"]
    base = nom - d_cover_nom - d_inner_nom
    rows = []
    for s in arch["scenarios"]:
        design = 0.0
        tol_l = tol_lin
        tol_r2 = sum(v * v for v in tol.values())
        if s.get("cover", s.get("added_cover", False)):
            design += d_cover_nom
            tol_l += d_cover_tol
            tol_r2 += d_cover_tol ** 2
        if s["double_sided_rear"]:
            design += d_inner_nom
            tol_l += d_inner_tol
            tol_r2 += d_inner_tol ** 2
        if s["window_max"]:
            design += d_window
        if s["rear_pcb_max"]:
            design += d_pcb
        if s["lower_web_max"]:
            design += d_web
        t_nom = base + design
        t_lin = t_nom + tol_l
        t_rss = t_nom + math.sqrt(tol_r2)
        rows.append({
            "id": s["id"],
            "T_nominal_tolerances_mm": round(t_nom, 3),
            "T_worst_linear_mm": round(t_lin, 3),
            "T_rss_mm": round(t_rss, 3),
            "meets_upper_nominal": t_nom <= hi + 1e-9,
            "meets_upper_rss": t_rss <= hi + 1e-9,
            "meets_upper_worst_linear": t_lin <= hi + 1e-9,
        })
    return {
        "tolerance_deltas_mm": tol,
        "tolerance_sum_linear_mm": round(tol_lin, 3),
        "tolerance_rss_mm": round(tol_rss, 3),
        "design_delta_cover_nominal_class_mm": round(d_cover_nom, 3),
        "design_delta_double_sided_nominal_class_mm": round(d_inner_nom, 3),
        "design_delta_window_max_mm": round(d_window, 3),
        "design_delta_rear_pcb_max_mm": round(d_pcb, 3),
        "design_delta_lower_web_max_mm": round(d_web, 3),
        "tool_thick_total_mm": thick,
        "tool_nominal_total_mm": nom,
        "rows": rows,
    }


def derive_levers(arch, zs, hm):
    """Single-parameter lever savings on tool outputs (no tool re-run)."""
    s = hm["summary"]
    h_f = s["H_F_under_display"]["value"]
    h_f2 = s["H_F_under_display"]["runner_up_value"]
    top5 = s["H_F_under_display"]["top5"]
    third = None
    for t in top5:
        if t["seated_max"] < h_f2 - 1e-9:
            third = t["seated_max"]
            break
    c_nom = stack_param(zs, "c_front", "nom")
    gap_nom = corner_layers(zs, "nominal")["front_gap"]
    bcu = [f for f in hm["main_footprints"] if f["side"] == "B.Cu" and f["r"] <= s["H_B_in_battery"]["radius_limit_mm"]]
    hb = sorted(f["seated_max"] for f in bcu)
    tall = [f for f in bcu if f["seated_max"] == max(hb)]
    rest = [f["seated_max"] for f in bcu if f["seated_max"] != max(hb)]
    hb_next = max(rest)
    web = stack_param(zs, "t_carrier_web", "nom")
    cb_nom = stack_param(zs, "c_back", "nom")
    ins = stack_param(zs, "t_insulator", "nom")
    back_nom = corner_layers(zs, "nominal")["back_zone"]
    back_alt = max(web, hb_next + cb_nom) + ins
    back_thick = corner_layers(zs, "thick")["back_zone"]
    back_alt_thick = max(stack_param(zs, "t_carrier_web", "max"), hb_next + stack_param(zs, "c_back", "max")) \
        + stack_param(zs, "t_insulator", "max")
    return {
        "front_gap_nominal_mm": gap_nom,
        "front_gap_without_U8_nominal_mm": round(max(h_f2 + c_nom, 0.0), 3),
        "saving_without_U8_mm": round(h_f - h_f2, 3),
        "front_gap_without_U8_and_U4_nominal_mm": round(third + c_nom, 3),
        "saving_without_U8_and_U4_mm": round(h_f - third, 3),
        "U8_nominal_height_mm": arch["levers"]["U8_nominal_height_mm"],
        "front_gap_with_U8_at_nominal_height_mm": round(arch["levers"]["U8_nominal_height_mm"] + c_nom, 3),
        "saving_if_U8_nominal_height_mm": round(h_f - arch["levers"]["U8_nominal_height_mm"], 3),
        "bcu_tallest_refs": sorted(f["ref"] for f in tall),
        "bcu_tallest_mm": max(hb),
        "bcu_next_mm": hb_next,
        "back_zone_nominal_mm": back_nom,
        "back_zone_alt_nominal_mm": round(back_alt, 3),
        "back_zone_saving_nominal_mm": round(back_nom - back_alt, 3),
        "back_zone_thick_mm": back_thick,
        "back_zone_alt_thick_mm": round(back_alt_thick, 3),
        "back_zone_saving_thick_mm": round(back_thick - back_alt_thick, 3),
    }


def rect_corner_az(rect):
    """Exact azimuth range (from, to) of a rectangle that does not contain the watch centre."""
    x0, y0, x1, y1 = rect
    s = sorted(az_of(x, y) for x in (x0, x1) for y in (y0, y1))
    gaps = [(s[(i + 1) % 4] - s[i]) % 360.0 for i in range(4)]
    i = max(range(4), key=lambda k: gaps[k])
    return s[(i + 1) % 4], s[i]


def rect_r_max(rect):
    x0, y0, x1, y1 = rect
    return max(math.hypot(x - CX, y - CY) for x in (x0, x1) for y in (y0, y1))


def reservation_az(res):
    g = res["geometry"]
    return tuple(g["az"]) if g["type"] == "sector" else rect_corner_az(g["rect"])


# Radial corner -> (tool layer corner for front_gap, stack-parameter key consistent with that layer,
# PARAMETRIC key of the land / lower web taken at its unfavourable end for that corner).
EC_CORNERS = {
    "nominal": ("nominal", "nom", "nom", "nom"),
    "conservative": ("thin", "min", "max", "min"),
    "optimistic": ("thick", "max", "min", "max"),
}


def _bend_inset(rb, h):
    """How far inboard of the MAIN edge a 90-deg bend of inner radius rb may start when the
    conductor's lower face is h above F.Cu: the board corner must stay inside the bend hollow,
    (R_main - R_start)^2 + (rb - h)^2 <= rb^2."""
    if h <= 0.0:
        return 0.0
    if h >= rb:
        return rb
    return math.sqrt(rb * rb - (rb - h) ** 2)


def _rim_parts(hm, az_range, r_in, r_out):
    """F.Cu parts whose courtyard interior overlaps the annular sector (exact detector), tallest first."""
    a0, a1 = az_range if az_range else (0.0, 360.0)
    region = {"type": "sector", "az": [a0, a1], "r": [r_in, r_out]}
    hits = []
    for f in hm["main_footprints"]:
        if f["side"] != "F.Cu":
            continue
        if interiors_overlap({"type": "rect", "rect": f["courtyard_bbox"]}, region):
            if f["seated_max"] is None:
                raise ValueError("F.Cu part %s under the support land has no height" % f["ref"])
            hits.append((f["seated_max"], f["ref"]))
    return sorted(hits, key=lambda t: (-t[0], t[1]))


def derive_edge_crossings(arch, zs, hm):
    """Geometric edge-crossing model (display support land, bend start, three-corner radial budget)."""
    ec = arch["edge_crossings"]
    land = ec["display_land"]
    res = {r["id"]: r for r in arch["reservations"]}
    r_disp = hm["summary"]["H_F_under_display"]["radius_limit_mm"]
    budget, rim, cross = {}, {}, {}
    for corner, (lay_c, pkey, ukey, wkey) in EC_CORNERS.items():
        par, _ = radial_corner(zs, corner)
        rb, t, c, r_main = par["R_bend_min"], par["t_fpc"], par["c_fpc"], par["R_main"]
        r_ci = check_value(zs, corner, "R_case_inner")
        r_ch = check_value(zs, corner, "R_channel_inner")
        fg = corner_layers(zs, lay_c)["front_gap"]
        c_front = stack_param(zs, "c_front", pkey)
        t_land = land["t_land_mm"][ukey]
        w_land = land["w_land_mm"][ukey]
        web = stack_param(zs, "t_lower_web", wkey)
        h_max = fg - t_land - c - t
        if h_max >= 0.0:
            r_v = max(r_main + rb - _bend_inset(rb, h_max), r_ch)
            m_ceil = r_ci - (r_v + t + c)
        else:
            r_v = m_ceil = None
        s_req = r_main + rb + t + c - r_ci
        if r_ch + t + c > r_ci or s_req > rb:
            h_min = None
        elif s_req <= 0.0:
            h_min = 0.0
        else:
            h_min = rb - math.sqrt(rb * rb - s_req * s_req)
            if h_max < 0.0 or h_min > h_max:
                h_min = None
        s_full = min(r_main + rb - r_ch, rb)
        h_full = 0.0 if s_full <= 0.0 else rb - math.sqrt(rb * rb - s_full * s_full)
        rnd = lambda v: None if v is None else round(v, 3)  # noqa: E731
        budget[corner] = {
            "front_gap_mm": fg, "t_land_mm": t_land, "R_bend_min_mm": rb, "t_conductor_mm": t, "c_mm": c,
            "R_main_mm": r_main, "R_case_inner_mm": r_ci, "R_channel_inner_mm": r_ch,
            "h_max_mm": rnd(h_max),
            "R_vertical_inner_at_h_max_mm": rnd(r_v),
            "R_bend_start_at_h_max_mm": rnd(None if r_v is None else r_v - rb),
            "margin_at_h_max_mm": rnd(m_ceil),
            "margin_flat_exit_mm": rnd(r_ci - (max(r_main + rb, r_ch) + t + c)),
            "h_exit_min_for_zero_margin_mm": rnd(h_min),
            "h_exit_for_channel_governed_mm": rnd(h_full if h_full <= h_max else None),
            "R_mouth_max_mm": rnd(r_ci - c - t - rb),
            "t_allow_straight_mm": rnd(r_ci - c - r_ch),
            "lower_web_margin_mm": rnd(web - (t + c)),
        }
        r_in = r_disp - w_land
        parts = _rim_parts(hm, None, r_in, R_CLIP)
        top = parts[0]
        nxt = next(p for p in parts if p[0] < top[0])
        rim[corner] = {
            "R_land_inner_mm": round(r_in, 3), "h_rim_mm": top[0], "h_rim_ref": top[1],
            "margin_mm": round(fg - c_front - top[0] - t_land, 3),
            "h_next_mm": nxt[0], "h_next_ref": nxt[1],
            "margin_elsewhere_mm": round(fg - c_front - nxt[0] - t_land, 3),
        }
        for x in ec["crossings"]:
            row = {}
            if x["approach_from"]:
                hits = _rim_parts(hm, reservation_az(res[x["approach_from"]]), r_in, r_main)
                h_p, ref = hits[0] if hits else (0.0, "none")
                row.update({"h_parts_mm": h_p, "h_parts_ref": ref,
                            "z_window_mm": rnd(None if h_max < 0.0 else h_max - c - h_p)})
            if x["riser_reservation"]:
                g = res[x["riser_reservation"]]["geometry"]
                span = (g["az"][1] - g["az"][0]) % 360.0
                row["riser_arc_at_R_channel_inner_mm"] = round(math.radians(span) * r_ch, 2)
            cross.setdefault(x["id"], {})[corner] = row
    return {"budget": budget, "land_vs_rim_parts": rim, "crossings": cross}


def derive_fpc_length(arch, zs):
    nomc = zs["radial"]["corners"]["nominal"]["parameters"]
    lay = corner_layers(zs, "nominal")
    r_chan = check_value(zs, "nominal", "R_channel_inner")
    r_att = arch["rear_module"]["envelope_results"]["D_env_single_mm"]["nominal"] / 2.0
    l_under = r_chan - r_att
    l_vert = lay["lower_web"] + lay["battery_zone"] + lay["back_zone"] + lay["main_pcb"]
    l_conn = arch["fpc_path"]["connector_run_mm"]
    l_arcs = 2.0 * (math.pi / 2.0) * (nomc["R_bend_min"] + nomc["t_fpc"] / 2.0)
    return {
        "L_underrun_mm": round(l_under, 2),
        "L_vertical_mm": round(l_vert, 2),
        "L_connector_run_mm": l_conn,
        "L_bend_arcs_mm": round(l_arcs, 2),
        "L_total_excl_service_mm": round(l_under + l_vert + l_conn + l_arcs, 1),
    }


def derive_rear_envelope(arch, hm):
    ed = arch["rear_module"]["envelope_derivation"]
    optical_face = set(ed["optical_face_refs"])
    a_all = 0.0
    a_opt = 0.0
    a_cl = 0.0
    for f in hm["rear_footprints"]:
        bb = f["courtyard_bbox"]
        a = (bb[2] - bb[0]) * (bb[3] - bb[1])
        a_all += a
        if f["ref"] in optical_face:
            a_opt += a
        else:
            a_cl += a
    a_emit_pd = sum((f["courtyard_bbox"][2] - f["courtyard_bbox"][0]) *
                    (f["courtyard_bbox"][3] - f["courtyard_bbox"][1])
                    for f in hm["rear_footprints"] if f["ref"].startswith("D4"))
    out = {"A_parts_mm2": round(a_all, 2), "A_optical_face_group_mm2": round(a_opt, 2),
           "A_inner_group_mm2": round(a_cl, 2), "A_emitters_pds_courtyard_mm2": round(a_emit_pd, 2),
           "A_board_single_mm2": {}, "D_area_single_mm": {}, "D_span_mm": {}, "D_env_single_mm": {},
           "A_board_double_mm2": {}, "D_area_double_mm": {}, "D_env_double_mm": {}}
    for c in ("optimistic", "nominal", "conservative"):
        eta = ed["eta"][c]
        a_s = a_all / eta + ed["A_conn_mm2"][c] + ed["A_lands_mm2"][c]
        d_s = 2.0 * math.sqrt(a_s / math.pi)
        span = 2.0 * ed["s_ED_max_mm"][c] + ed["w_emitter_mm"] + 2.0 * ed["m_edge_mm"][c]
        a_d = max(a_opt, a_cl) / eta + ed["A_conn_mm2"][c] + ed["A_lands_mm2"][c]
        d_d = 2.0 * math.sqrt(a_d / math.pi)
        out["A_board_single_mm2"][c] = round(a_s, 1)
        out["D_area_single_mm"][c] = round(d_s, 1)
        out["D_span_mm"][c] = round(span, 1)
        out["D_env_single_mm"][c] = round(max(d_s, span), 1)
        out["A_board_double_mm2"][c] = round(a_d, 1)
        out["D_area_double_mm"][c] = round(d_d, 1)
        out["D_env_double_mm"][c] = round(max(d_d, span), 1)
    return out


def derive_supports(arch):
    azs = []
    for rid in arch["supports"]["support_reservation_ids"]:
        r = next(x for x in arch["reservations"] if x["id"] == rid)
        x0, y0, x1, y1 = r["geometry"]["rect"]
        azs.append(round(az_of((x0 + x1) / 2.0, (y0 + y1) / 2.0), 1))
    s = sorted(azs)
    gaps = [(s[(i + 1) % len(s)] - s[i]) % 360.0 for i in range(len(s))]
    return {"centre_az_deg": azs, "arc_gaps_deg": [round(g, 1) for g in gaps],
            "largest_unsupported_arc_deg": round(max(gaps), 1)}


def derive_pack_edge(arch, zs):
    """Exact closest approach of the support / exit rectangles to the pack and the area left outside
    R_channel_inner (0.05 mm sampling, clipped at the nominal case outer radius)."""
    r_nom = arch["geometry"]["R_pack_nom_mm"]
    rpm = {c: check_value(zs, c, "R_pack_max") for c in ("nominal", "conservative")}
    rch = {c: check_value(zs, c, "R_channel_inner") for c in ("nominal", "conservative")}
    out = {}
    for rid in arch["pack_edge"]["reservation_ids"]:
        r = next(x for x in arch["reservations"] if x["id"] == rid)
        x0, y0, x1, y1 = r["geometry"]["rect"]
        r_min = math.hypot(min(max(CX, x0), x1) - CX, min(max(CY, y0), y1) - CY)
        nx, ny = int((x1 - x0) / AREA_STEP), int((y1 - y0) / AREA_STEP)
        rs = [math.hypot(x0 + (i + 0.5) * AREA_STEP - CX, y0 + (j + 0.5) * AREA_STEP - CY)
              for i in range(nx) for j in range(ny)]
        rs = [v for v in rs if v <= R_CLIP]
        a2 = AREA_STEP * AREA_STEP
        out[rid] = {
            "r_min_mm": round(r_min, 2),
            "enters_nominal_pack_mm": round(max(0.0, r_nom - r_min), 2),
            "enters_R_pack_max_nominal_mm": round(max(0.0, rpm["nominal"] - r_min), 2),
            "enters_R_pack_max_conservative_mm": round(max(0.0, rpm["conservative"] - r_min), 2),
            "area_in_case_mm2": round(len(rs) * a2, 1),
            "area_outside_R_channel_inner_nominal_mm2": round(sum(1 for v in rs if v >= rch["nominal"]) * a2, 1),
            "area_outside_R_channel_inner_conservative_mm2": round(sum(1 for v in rs if v >= rch["conservative"]) * a2, 1),
        }
    return out


def derive_all(arch, zs, hm):
    d = {}
    d["reservations"] = derive_reservations(arch["reservations"])
    d["overlaps"] = overlap_pairs(arch["reservations"])
    d["scenarios"] = derive_scenarios(arch, zs)
    d["levers"] = derive_levers(arch, zs, hm)
    d["edge_crossings"] = derive_edge_crossings(arch, zs, hm)
    d["rear_envelope"] = derive_rear_envelope(arch, hm)
    d["supports"] = derive_supports(arch)
    d["pack_edge"] = derive_pack_edge(arch, zs)
    return d


# ------------------------------------------------------------------------ svg
class Svg:
    def __init__(self, width, height, title, desc):
        self.w, self.h = width, height
        self.parts = []
        self.title, self.desc = title, desc

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke="#222", sw=1.0, dash=None, op=None, extra=""):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        o = ' fill-opacity="%s"' % op if op is not None else ""
        self.add('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"%s stroke="%s" stroke-width="%s"%s%s/>'
                 % (f2(x), f2(y), f2(w), f2(h), fill, o, stroke, f2(sw), d, extra))

    def circle(self, x, y, r, fill="none", stroke="#222", sw=1.0, dash=None, op=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        o = ' fill-opacity="%s"' % op if op is not None else ""
        self.add('<circle cx="%s" cy="%s" r="%s" fill="%s"%s stroke="%s" stroke-width="%s"%s/>'
                 % (f2(x), f2(y), f2(r), fill, o, stroke, f2(sw), d))

    def line(self, x0, y0, x1, y1, stroke="#222", sw=1.0, dash=None, marker=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        m = ' marker-end="url(#%s)"' % marker if marker else ""
        self.add('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s%s/>'
                 % (f2(x0), f2(y0), f2(x1), f2(y1), stroke, f2(sw), d, m))

    def path(self, d, fill="none", stroke="#222", sw=1.0, dash=None, op=None):
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        o = ' fill-opacity="%s"' % op if op is not None else ""
        self.add('<path d="%s" fill="%s"%s stroke="%s" stroke-width="%s"%s/>' % (d, fill, o, stroke, f2(sw), da))

    def poly(self, pts, fill="none", stroke="#222", sw=1.0, dash=None, op=None):
        d = "M" + " L".join("%s %s" % (f2(x), f2(y)) for x, y in pts) + " Z"
        self.path(d, fill, stroke, sw, dash, op)

    def text(self, x, y, s, size=10, fill="#111", anchor="start", weight="normal", rot=None):
        r = ' transform="rotate(%s %s %s)"' % (f2(rot), f2(x), f2(y)) if rot is not None else ""
        self.add('<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s" font-weight="%s"%s>%s</text>'
                 % (f2(x), f2(y), f2(size), fill, anchor, weight, r, escape(s)))

    def render(self):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
                'font-family="DejaVu Sans, Verdana, sans-serif">' % (self.w, self.h, self.w, self.h))
        defs = ('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#222"/></marker>'
                '<marker id="arrr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#c0392b"/></marker></defs>')
        body = "\n".join(self.parts)
        return "%s\n<title>%s</title>\n<desc>%s</desc>\n%s\n<rect width=\"%d\" height=\"%d\" fill=\"#ffffff\"/>\n%s\n</svg>\n" % (
            head, escape(self.title), escape(self.desc), defs, self.w, self.h, body)


def class_dash(cls):
    return {"KNOWN": None, "PARAMETRIC": "5 3", "SUPPLIER_DATA_REQUIRED": "1.5 2.5"}[cls]


def sector_path(cx, cy, s, r0, r1, a0, a1):
    span = (a1 - a0) % 360.0
    if span == 0.0:
        span = 360.0

    def pt(r, a):
        t = math.radians(a)
        return cx + r * s * math.sin(t), cy - r * s * math.cos(t)
    xo0, yo0 = pt(r1, a0)
    xo1, yo1 = pt(r1, a0 + span)
    xi1, yi1 = pt(r0, a0 + span)
    xi0, yi0 = pt(r0, a0)
    large = 1 if span > 180.0 else 0
    if r0 <= 0.01:
        return "M%s %s A%s %s 0 %d 1 %s %s L%s %s Z" % (
            f2(xo0), f2(yo0), f2(r1 * s), f2(r1 * s), large, f2(xo1), f2(yo1), f2(cx), f2(cy))
    return "M%s %s A%s %s 0 %d 1 %s %s L%s %s A%s %s 0 %d 0 %s %s Z" % (
        f2(xo0), f2(yo0), f2(r1 * s), f2(r1 * s), large, f2(xo1), f2(yo1),
        f2(xi1), f2(yi1), f2(r0 * s), f2(r0 * s), large, f2(xi0), f2(yi0))


def draw_reservation(svg, cx, cy, s, r, label_size=9):
    g = r["geometry"]
    col = Z_COLOR[r["z_levels"][0]]
    dash = class_dash(r["class"])
    if r["kind"] == "body":
        return
    if g["type"] == "rect":
        x0, y0, x1, y1 = g["rect"]
        pts = [(cx + (x0 - CX) * s, cy + (y0 - CY) * s), (cx + (x1 - CX) * s, cy + (y0 - CY) * s),
               (cx + (x1 - CX) * s, cy + (y1 - CY) * s), (cx + (x0 - CX) * s, cy + (y1 - CY) * s)]
        svg.poly(pts, col, col, 1.4, dash, 0.30)
    elif g["type"] == "sector":
        if g["az"][1] - g["az"][0] >= 360.0 and g["r"][0] > 0.0:
            r0, r1 = g["r"][0] * s, g["r"][1] * s
            svg.path("M%s %s A%s %s 0 1 1 %s %s A%s %s 0 1 1 %s %s Z M%s %s A%s %s 0 1 0 %s %s A%s %s 0 1 0 %s %s Z" % (
                f2(cx), f2(cy - r1), f2(r1), f2(r1), f2(cx), f2(cy + r1), f2(r1), f2(r1), f2(cx), f2(cy - r1),
                f2(cx), f2(cy - r0), f2(r0), f2(r0), f2(cx), f2(cy + r0), f2(r0), f2(r0), f2(cx), f2(cy - r0)),
                col, col, 1.0, dash, 0.10)
        elif g["az"][1] - g["az"][0] >= 360.0:
            svg.circle(cx, cy, g["r"][1] * s, col, col, 1.2, dash, 0.12)
        else:
            svg.path(sector_path(cx, cy, s, g["r"][0], g["r"][1], g["az"][0], g["az"][1]), col, col, 1.4, dash, 0.30)
    elif g["type"] == "circles":
        op = 0.08 if r["kind"] == "exclusion" else 0.30
        for c in g["circles"]:
            svg.circle(cx + (c[0] - CX) * s, cy + (c[1] - CY) * s, c[2] * s, col, col, 1.2, dash, op)


# ------------------------------------------------------------- diagram 1
def build_perimeter_map(arch, zs, hm, d):
    S = 14.0
    W, H = 1240, 930
    cx, cy = 430.0, 430.0
    svg = Svg(W, H, "Rev-A perimeter / Z-level reservation map (front view)",
              "Front view from display; north = -Y, east = +X. Provisional reversible architecture study; not a frozen outline.")
    svg.text(20, 26, "Rev-A perimeter reservation map - front view from display; north = -Y (up), east = +X (right)", 14, weight="bold")
    svg.text(20, 44, "G1 comparison reservations; current G2 allocation is in g2_allocation.svg. Provisional, no geometry approval.", 10, "#555")
    g = arch["geometry"]
    # clock face
    for h in range(12):
        a = math.radians(h * 30.0)
        x0, y0 = cx + 25.6 * S * math.sin(a), cy - 25.6 * S * math.cos(a)
        x1, y1 = cx + 26.4 * S * math.sin(a), cy - 26.4 * S * math.cos(a)
        svg.line(x0, y0, x1, y1, "#777", 1.0)
        svg.text(cx + 27.3 * S * math.sin(a), cy - 27.3 * S * math.cos(a) + 4, str(12 if h == 0 else h), 12, "#444", "middle")
    # envelopes
    svg.circle(cx, cy, g["R_case_outer_max_mm"] * S, "none", "#999", 1.0, "2 3")
    svg.circle(cx, cy, g["R_case_outer_min_mm"] * S, "none", "#999", 1.0, "2 3")
    svg.circle(cx, cy, g["R_case_outer_nom_mm"] * S, "none", "#555", 2.0)
    svg.circle(cx, cy, g["R_case_inner_nom_mm"] * S, "none", "#555", 1.0, "6 3")
    svg.circle(cx, cy, g["R_case_inner_conservative_mm"] * S, "none", "#c0392b", 1.0, "1.5 3")
    svg.circle(cx, cy, g["R_main_mm"] * S, "none", "#1f5fbf", 2.0)
    svg.circle(cx, cy, g["R_display_mm"] * S, "none", "#2e7d32", 1.8)
    svg.circle(cx, cy, g["R_pack_nom_mm"] * S, "none", "#e08a00", 1.5, "7 3")
    svg.circle(cx, cy, g["R_pol_mm"] * S, "none", "#2e7d32", 0.8, "2 3")
    # reservations (bigger first so small ones stay visible)
    for r in sorted(arch["reservations"], key=lambda q: -d["reservations"][q["id"]]["area"]):
        draw_reservation(svg, cx, cy, S, r)
    # key parts
    keep = arch["diagram"]["perimeter_parts"]
    byref = {f["ref"]: f for f in hm["main_footprints"]}
    for ref in keep:
        f = byref[ref]
        px, py = cx + (f["x"] - CX) * S, cy + (f["y"] - CY) * S
        svg.rect(px - 2.5, py - 2.5, 5, 5, "#111", "#111", 0.5)
        dx = 5 if f["x"] >= CX else -5
        svg.text(px + dx, py + 3, ref, 8, "#111", "start" if dx > 0 else "end")
    # reservation labels
    for r in arch["reservations"]:
        if r["kind"] == "body":
            continue
        c = r.get("label_xy") or d["reservations"][r["id"]]["centroid"]
        lx, ly = cx + (c[0] - CX) * S, cy + (c[1] - CY) * S
        svg.text(lx, ly + 3, r["short_label"], 8, "#000", "middle", "bold")
    # conflict markers (offset from the locus; pushed down when they collide)
    placed = []
    for c in arch["conflicts"]:
        loc = c.get("locus_xy")
        if not loc:
            continue
        px, py = cx + (loc[0] - CX) * S, cy + (loc[1] - CY) * S
        mx, my = px + 14.0, py - 14.0
        while any(abs(mx - ox) < 20.0 and abs(my - oy) < 20.0 for ox, oy in placed):
            my += 20.0
        placed.append((mx, my))
        col = {"HIGH": "#c0392b", "MEDIUM": "#d35400", "LOW": "#7f8c8d"}.get(c.get("severity"), "#000000")
        svg.line(px, py, mx, my, col, 1.0)
        svg.circle(px, py, 2.0, col, col, 1.0)
        svg.circle(mx, my, 9.5, "#ffffff", col, 1.8, None, 0.9)
        svg.text(mx, my + 3.2, c["short_id"], 8, col, "middle", "bold")
    # north arrow
    svg.line(60, 120, 60, 70, "#111", 2.0, None, "arr")
    svg.text(60, 62, "N (-Y)", 11, "#111", "middle", "bold")
    # legend panel
    lx = 880
    svg.text(lx, 92, "Z levels (fill colour)", 12, weight="bold")
    desc = {"FRONT": "display + bond (+cover)", "MAIN": "front gap + MAIN PCB + back zone",
            "BATTERY": "pack + carrier web", "REAR": "lower web + REAR + optics + window"}
    y = 112
    for z in Z_LEVELS:
        svg.rect(lx, y - 10, 16, 12, Z_COLOR[z], "#333", 0.8, None, 0.5)
        svg.text(lx + 24, y, "%s (%s): %s" % (z, Z_BADGE[z], desc[z]), 10)
        y += 18
    y += 8
    svg.text(lx, y, "Class (outline style)", 12, weight="bold")
    y += 20
    for cls, dash in (("KNOWN", None), ("PARAMETRIC", "5 3"), ("SUPPLIER_DATA_REQUIRED", "1.5 2.5")):
        svg.line(lx, y - 4, lx + 30, y - 4, "#333", 2.0, dash)
        svg.text(lx + 38, y, cls, 10)
        y += 18
    y += 8
    svg.text(lx, y, "Envelopes (nominal unless stated)", 12, weight="bold")
    y += 20
    env = [("#1f5fbf", None, "MAIN dev. envelope Ø%s (R %s)" % (f1(2 * g["R_main_mm"]), f1(g["R_main_mm"]))),
           ("#2e7d32", None, "Display outline Ø%s (R %s)" % (f1(2 * g["R_display_mm"]), f2(g["R_display_mm"]))),
           ("#e08a00", "7 3", "Battery Ø%s nominal (R %s)" % (f1(2 * g["R_pack_nom_mm"]), f1(g["R_pack_nom_mm"]))),
           ("#555", None, "Case outer Ø%s nom (band %s-%s)" % (f1(2 * g["R_case_outer_nom_mm"]),
                                                              f1(2 * g["R_case_outer_min_mm"]), f1(2 * g["R_case_outer_max_mm"]))),
           ("#555", "6 3", "Case inner R %s nominal" % f2(g["R_case_inner_nom_mm"])),
           ("#c0392b", "1.5 3", "Case inner R %s conservative" % f2(g["R_case_inner_conservative_mm"]))]
    for col, dash, txt in env:
        svg.line(lx, y - 4, lx + 30, y - 4, col, 2.0, dash)
        svg.text(lx + 38, y, txt, 10)
        y += 18
    y += 8
    svg.text(lx, y, "Conflict markers (severity colour)", 12, weight="bold")
    y += 18
    for c in arch["conflicts"]:
        if y > H - 20:
            break
        col = {"HIGH": "#c0392b", "MEDIUM": "#d35400", "LOW": "#7f8c8d"}.get(c.get("severity"), "#000000")
        svg.text(lx, y, "%s %s" % (c["short_id"], c["title"][:58]), 9, col)
        y += 13
    svg.text(20, H - 14, "Clock faces: az = degrees clockwise from north; z-levels per architecture.json reservations. "
             "Black squares: key MAIN parts from main_height_map.json.", 9, "#555")
    return svg.render()


# ------------------------------------------------------------- diagram 2
def build_rear_module(arch, zs, hm, d):
    S = 11.0
    W, H = 1400, 760
    svg = Svg(W, H, "REAR rigid-board envelope concept: wrist-side view and section",
              "Provisional envelope class derived from live REAR courtyards; not an outline, stackup or placement.")
    rm = arch["rear_module"]
    env = d["rear_envelope"]
    svg.text(20, 26, "G1 REAR envelope comparison - current G2 attach and channels: g2_allocation.svg", 14, weight="bold")
    svg.text(20, 44, "Top view = looking at the optical face from the wrist; north up, EAST LEFT (mirrored vs front view). "
             "Section = E-W cut through the pod.", 10, "#555")
    cx, cy = 330.0, 420.0

    def vx(dx):   # assembly offset east(+) -> wrist view x (east is left)
        return cx - dx * S

    def vy(dy):
        return cy + dy * S
    # pack outline for context
    svg.circle(cx, cy, arch["geometry"]["R_pack_nom_mm"] * S, "none", "#e08a00", 1.2, "7 3")
    svg.text(vx(0), vy(-arch["geometry"]["R_pack_nom_mm"]) - 6, "battery Ø44 nominal (above, hidden)", 9, "#e08a00", "middle")
    # envelope corners (single-sided)
    dn = env["D_env_single_mm"]
    for c, col, dash, w in (("conservative", "#999", "4 3", 1.0), ("optimistic", "#999", "4 3", 1.0), ("nominal", "#1b1b1b", None, 2.0)):
        svg.circle(cx, cy, dn[c] / 2.0 * S, "none", col, w, dash)
    dd = env["D_env_double_mm"]["nominal"]
    svg.circle(cx, cy, dd / 2.0 * S, "none", "#6a1b9a", 1.2, "2 3")
    # zones
    zr = rm["zones"]
    rn = dn["nominal"] / 2.0
    r_cl = env["D_span_mm"]["nominal"] / 2.0
    svg.circle(cx, cy, r_cl * S, Z_COLOR["REAR"], Z_COLOR["REAR"], 1.5, None, 0.28)
    svg.text(cx, cy - 4, "optical cluster", 10, "#000", "middle", "bold")
    svg.text(cx, cy + 9, "7 emitters + 4 PDs + barriers", 9, "#000", "middle")
    # AFE / mux band (south half annular sector)
    def az_to_xy(r, a):
        t = math.radians(a)
        return vx(r * math.sin(t)), vy(-r * math.cos(t))
    # sector path in wrist view: mirror x
    def view_sector(r0, r1, a0, a1, fill, stroke, op):
        pts = []
        n = 24
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            pts.append(az_to_xy(r1, a))
        for i in range(n, -1, -1):
            a = a0 + (a1 - a0) * i / n
            pts.append(az_to_xy(r0, a))
        svg.poly(pts, fill, stroke, 1.2, None, op)
    view_sector(r_cl, rn, zr["afe_band_az"][0], zr["afe_band_az"][1], Z_COLOR["MAIN"], "#2e7d32", 0.28)
    x, y = az_to_xy((r_cl + rn) / 2.0, 150)
    svg.text(x, y, "AFE x2 + mux x6 + decoupling", 9, "#000", "middle")
    # MAX30208 tongue
    ta = zr["tongue_az"]
    view_sector(r_cl, rn, ta - 12, ta + 12, "#f1c40f", "#9a7d0a", 0.45)
    x, y = az_to_xy((r_cl + rn) / 2.0, ta)
    svg.text(x, y - 3, "MAX30208", 9, "#000", "middle", "bold")
    svg.text(x, y + 8, "thermal island", 9, "#000", "middle")
    # J1502 attach edge at south
    x0, y0 = az_to_xy(rn, 180)
    svg.rect(x0 - 3.2 * S, y0 - 1.6 * S, 6.4 * S, 1.6 * S, "#c0392b", "#7b241c", 1.2, None, 0.35)
    svg.text(x0, y0 + 16, "J1502 / FPC attach (S edge, position 1 label TBD)", 9, "#7b241c", "middle")
    # support lands
    for a in zr["land_az"]:
        x, y = az_to_xy(rn - 0.9, a)
        svg.rect(x - 7, y - 7, 14, 14, "#555", "#111", 1.0, None, 0.5)
        svg.text(x, y + 20, "land", 8, "#111", "middle")
    # compass (wrist view)
    svg.text(cx, cy - 23.0 * S, "N", 12, "#111", "middle", "bold")
    svg.text(cx, cy + 23.8 * S, "S (FPC side)", 12, "#111", "middle", "bold")
    svg.text(cx - 23.6 * S, cy + 4, "E", 12, "#111", "middle", "bold")
    svg.text(cx + 23.6 * S, cy + 4, "W", 12, "#111", "middle", "bold")
    # dimension notes
    ty = 70
    notes = [
        "Envelope Ø (disc-equivalent), single-sided REAR: %s / %s / %s mm (opt / nom / cons)" % (
            f1(dn["optimistic"]), f1(dn["nominal"]), f1(dn["conservative"])),
        "Double-sided REAR nominal Ø %s mm (purple dotted), but + rear_inner in the Z stack" % f1(dd),
        "A_parts = %s mm² of live library courtyards (REAR, 44 refs, no J1502/C1501)" % f1(env["A_parts_mm2"]),
    ]
    for n in notes:
        svg.text(20, ty, n, 10)
        ty += 14
    # transform box
    tx = rm["transform"]
    bx, by = 20, 700
    svg.rect(bx, by - 16, 660, 62, "#fdfdfd", "#555", 1.0)
    svg.text(bx + 8, by, "Board-to-assembly transform (PROPOSED, not frozen):", 10, weight="bold")
    svg.text(bx + 8, by + 14, tx["x_a"] + "      " + tx["y_a"], 10)
    svg.text(bx + 8, by + 28, "optical face = " + tx["optical_face"] + "; normal = " + tx["optical_normal"], 10)
    svg.text(bx + 8, by + 42, "J1502 pin order: label from mating-face drawing, never from a mirrored B-side view.", 10)
    # ---- section (right) ----
    sx0, sy0 = 740, 90
    hs, vs = 11.0, 38.0
    svg.text(sx0, sy0 - 28, "Section through pod (E-W; vertical scale x%s exaggerated vs horizontal)" % f1(vs / hs), 11, weight="bold")
    lay = corner_layers(zs, "nominal")
    par = zs["parameters"]
    wpx = dn["nominal"] * hs
    xl = sx0 + 40
    ytop = sy0 + 10
    # battery slab (cut)
    bat_h = 1.2
    svg.rect(xl - 30, ytop, wpx + 60, bat_h * vs, "#f6c58a", "#e08a00", 1.2, "6 3", 0.7)
    svg.text(xl + wpx / 2, ytop + 22, "battery_zone %s mm (cut)" % f2(lay["battery_zone"]), 10, "#000", "middle")
    y = ytop + bat_h * vs
    # lower web
    svg.rect(xl - 30, y, wpx + 60, lay["lower_web"] * vs, "#d9d9d9", "#555", 1.0)
    svg.text(xl + wpx + 36, y + 11, "lower_web %s (%s-%s)" % (f2(lay["lower_web"]), f2(par["t_lower_web"]["min"]), f2(par["t_lower_web"]["max"])), 9)
    y += lay["lower_web"] * vs
    # rear_inner (G1 baseline: double-sided REAR, OD-REAR-SIDED - J1502 + passives on the inner face)
    ri = lay["rear_inner"]
    if ri > 0:
        svg.rect(xl - 30, y, wpx + 60, ri * vs, "#e8d8ee", "#6a1b9a", 1.0, "3 2", 0.6)
        svg.text(xl + wpx + 36, y + 11, "rear_inner %s (G1 baseline: double-sided, OD-REAR-SIDED; h_rear_inner %s + c_rear_inner %s)" % (
            f2(ri), f2(par["h_rear_inner"]["nom"]), f2(par["c_rear_inner"]["nom"])), 9)
        y += ri * vs
    else:
        svg.text(xl + wpx + 36, y + 11, "rear_inner 0 (single-sided)", 9)
    # PCB
    svg.rect(xl, y, wpx, lay["rear_pcb"] * vs, "#7fb77e", "#2e7d32", 1.2)
    svg.text(xl + wpx + 36, y + 20, "rear_pcb %s (%s-%s)" % (f2(lay["rear_pcb"]), f2(par["t_rear_pcb"]["min"]), f2(par["t_rear_pcb"]["max"])), 9)
    y += lay["rear_pcb"] * vs
    # optics zone with parts and barriers
    oz = lay["optics_zone"] * vs
    hopt = par["h_optics_max"]["nom"] * vs
    svg.rect(xl, y, wpx, oz, "#fbeee0", "#b07aa1", 0.8, "3 2", 0.8)
    # components (blocks hanging below PCB)
    comps = rm["section_blocks"]
    for b in comps:
        bx0 = xl + wpx * b["x_frac"] - b["w_mm"] * hs / 2.0
        svg.rect(bx0, y, b["w_mm"] * hs, hopt, b["fill"], "#333", 0.8)
        svg.text(bx0 + b["w_mm"] * hs / 2.0, y + hopt - 4, b["label"], 7, "#000", "middle")
    for fr in rm["section_barrier_frac"]:
        bx0 = xl + wpx * fr - rm["t_barrier_study_mm"][1] * hs / 2.0
        svg.rect(bx0, y, rm["t_barrier_study_mm"][1] * hs, oz, "#111", "#111", 0.5)
    svg.text(xl + wpx + 36, y + oz / 2 + 3, "optics_zone %s = h_optics_max %s + c_optics %s" % (
        f2(lay["optics_zone"]), f2(par["h_optics_max"]["nom"]), f2(par["c_optics"]["nom"])), 9)
    y += oz
    # window: one continuous transparent plane; barriers end at its inner face (X23)
    wy = lay["window"] * vs
    svg.rect(xl, y, wpx, wy, "#cfe8ff", "#1f5fbf", 1.2, None, 0.8)
    t_b = rm["t_barrier_study_mm"][1] * hs
    for fr in rm["section_barrier_frac"]:
        bx = xl + wpx * fr
        svg.line(bx - t_b / 2.0, y + 1, bx + t_b / 2.0, y + 1, "#111", 2.0)
        svg.line(bx, y + 2, bx, y + wy, "#111", 0.8, "2 2")
    svg.text(xl + wpx / 2, y + wy / 2 + 3, "window %s (%s-%s) - continuous" % (f2(lay["window"]), f2(par["t_window"]["min"]), f2(par["t_window"]["max"])), 9, "#000", "middle")
    wi = rm["window_isolation"]
    svg.text(xl + wpx + 36, y + wy / 2 + 3, "ink mask (solid, window inner face) = baseline W0", 9, "#111")
    svg.text(xl + wpx + 36, y + wy / 2 + 15, "dashed = W1 walls through window (alternative)", 9, "#111")
    y += wy
    svg.line(xl - 30, y, xl + wpx + 30, y, "#c0392b", 1.5)
    svg.text(xl - 30, y + 14, "skin-contact plane = T_total", 9, "#c0392b")
    # caseback plane outside pod, h_pod above skin plane
    hp = par["h_pod"]["nom"] * vs
    svg.line(xl - 90, y - hp, xl - 4, y - hp, "#555", 2.0)
    svg.line(xl + wpx + 4, y - hp, xl + wpx + 90, y - hp, "#555", 2.0)
    svg.text(xl - 90, y - hp - 12, "caseback outer plane (T_body)", 9, "#555")
    svg.line(xl - 20, y, xl - 20, y - hp, "#555", 1.0, None, "arr")
    svg.text(xl - 26, y - hp / 2, "h_pod %s nom (0-1.5)" % f1(par["h_pod"]["nom"]), 9, "#555", "end")
    # hard stops
    for hx in (xl - 4, xl + wpx - 2):
        svg.rect(hx, y - lay["window"] * vs - 2, 6, 10, "#555", "#111", 0.8)
    svg.text(xl + wpx / 2, y + 30, "hard stops at window perimeter carry wrist load; no load on optical parts", 9, "#555", "middle")
    svg.text(sx0, y + 48, "X23: walls end at the window inner face; lateral light in the window is NOT excluded (%s)." % wi["status"].split(" - ")[0].lower(), 9, "#c0392b")
    svg.text(sx0, y + 60, "Gate %s: compare W0 with W1 / W2 and an opaque control on prototypes." % wi["measurement_gate"]["id"], 9, "#c0392b")
    # text block of unmodelled
    yy = y + 84
    svg.text(sx0, yy, "Not in the tool Z-stack (must be added before freeze):", 10, weight="bold")
    yy += 14
    for item in rm["unmodelled_z_items"]:
        svg.text(sx0 + 8, yy, "- " + item, 9)
        yy += 12
    svg.text(sx0, H - 28, "Values: nominal tool layers (zstack.json); ranges PARAMETRIC (stack_parameters.json).", 9, "#555")
    svg.text(sx0, H - 14, "SFH4053B / MAX86141 heights unknown: h_optics_max is an assumption (conflict X10).", 9, "#555")
    return svg.render()


# ------------------------------------------------------------- diagram 3
def build_interconnect(arch, zs, hm, d):
    S = 14.0
    W, H = 1420, 800
    cx, cy = 360.0, 400.0
    svg = Svg(W, H, "MAIN-REAR FPC path and charger harness path (plan + south radial section)",
              "Provisional routing architecture; connector MPN, pitch and orientation are not frozen.")
    g = arch["geometry"]
    svg.text(20, 26, "G1 interconnect comparison - current G2 paths and section-channel allocation are in g2_interconnect.md", 14, weight="bold")
    svg.text(20, 44, "Solid = MAIN F.Cu level; dashed = REAR level (hidden behind battery). north = -Y, east = +X.", 10, "#555")
    for r, col, w, dash in ((g["R_case_outer_nom_mm"], "#555", 2.0, None), (g["R_case_inner_nom_mm"], "#555", 1.0, "6 3"),
                            (g["R_main_mm"], "#1f5fbf", 2.0, None), (g["R_display_mm"], "#2e7d32", 1.5, None),
                            (g["R_pack_nom_mm"], "#e08a00", 1.2, "7 3")):
        svg.circle(cx, cy, r * S, "none", col, w, dash)
    ids = arch["diagram"]["interconnect_reservations"]
    for r in arch["reservations"]:
        if r["id"] in ids:
            draw_reservation(svg, cx, cy, S, r)
            c = r.get("label_xy") or d["reservations"][r["id"]]["centroid"]
            svg.text(cx + (c[0] - CX) * S, cy + (c[1] - CY) * S + 3, r["short_label"], 8, "#000", "middle", "bold")
    # BMM350 marker
    byref = {f["ref"]: f for f in hm["main_footprints"]}
    for ref in ("U703", "J1", "U201", "U7"):
        f = byref[ref]
        px, py = cx + (f["x"] - CX) * S, cy + (f["y"] - CY) * S
        svg.rect(px - 3, py - 3, 6, 6, "#111", "#111", 0.5)
        svg.text(px + 6, py + 3, ref, 8)
    # paths
    legend = []
    paths = arch["interconnect"]["plan_paths"]
    for p in paths:
        pts = [(cx + (x - CX) * S, cy + (y - CY) * S) for x, y in p["points_xy"]]
        d_attr = "M" + " L".join("%s %s" % (f2(x), f2(y)) for x, y in pts)
        svg.path(d_attr, "none", p["color"], 2.4, p.get("dash"))
        legend.append((p["color"], p.get("dash"), 2.4, p["label"]))
    # charger arc routes (computed)
    ch = arch["charger_path"]
    for route in ch["routes"]:
        r = route["r_mm"]
        a0, a1 = route["az_from_deg"], route["az_to_deg"]
        pts = []
        n = 48
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + r * S * math.sin(a), cy - r * S * math.cos(a)))
        d_attr = "M" + " L".join("%s %s" % (f2(x), f2(y)) for x, y in pts)
        svg.path(d_attr, "none", route["color"], 2.4 if route["recommended"] else 1.4, route["dash"])
        legend.append((route["color"], route["dash"], 2.4 if route["recommended"] else 1.4,
                       "%s - arc %s mm at R %s" % (route["label"], f1(route["length_arc_mm"]), f1(route["r_mm"]))))
    svg.text(20, H - 30, "FPC: out-and-down 2 x 90 deg at south (J1501 mouth faces outward); bend start derived from exit height and MAIN edge, "
             "vertical run beside the pack, under-run in the lower web.", 9, "#555")
    svg.text(20, H - 16, "Charger: contact block rear east -> REAR strip (CHG_ROUTE) -> link under the pack edge (CHG_LINK) -> riser in the annulus "
             "(CHG_RISER, az 249-259) -> approach under the land (CHG_APPROACH) -> J202.", 9, "#555")
    # ---- south radial section ----
    ox, oy = 790.0, 90.0
    hs = 62.0        # px per mm radial
    r_lo = 21.0
    vs = 17.0        # px per mm axial
    lay = corner_layers(zs, "nominal")
    svg.text(ox, oy - 30, "South radial section at J1501, nominal (z downward; XC-J202 riser: same section)", 11, weight="bold")

    def rx(r):
        return ox + (r - r_lo) * hs
    z = 0.0
    zpos = {}
    for lid in ("cover", "cover_bond", "display", "front_gap", "main_pcb", "back_zone", "battery_zone",
                "lower_web", "rear_inner", "rear_pcb", "optics_zone", "window"):
        zpos[lid] = (z, z + lay[lid])
        z += lay[lid]
    ztot = z

    def zy(zv):
        return oy + zv * vs
    xmax = 26.0
    # layers drawn where they exist radially
    def band(lid, r_in, r_out, fill, stroke="#333", op=0.8):
        a, b = zpos[lid]
        if b - a <= 0:
            return
        svg.rect(rx(r_in), zy(a), (r_out - r_in) * hs, (b - a) * vs, fill, stroke, 0.8, None, op)
    rdisp, rmain, rpack = g["R_display_mm"], g["R_main_mm"], g["R_pack_nom_mm"]
    rpmax = check_value(zs, "nominal", "R_pack_max")
    rci = check_value(zs, "nominal", "R_case_inner")
    rco = g["R_case_outer_nom_mm"]
    rchi = check_value(zs, "nominal", "R_channel_inner")
    rcho = check_value(zs, "nominal", "R_channel_outer_straight")
    rwrap = check_value(zs, "nominal", "R_edge_wrap_outer")
    band("display", r_lo, rdisp, "#cfe0f1")
    band("front_gap", r_lo, rmain, "#ffffff", "#bbb", 0.5)
    band("main_pcb", r_lo, rmain, "#7fb77e")
    band("back_zone", r_lo, rmain, "#eeeeee")
    band("battery_zone", r_lo, rpmax, "#f6c58a")
    band("lower_web", r_lo, rchi, "#d9d9d9")
    # case wall
    a0, b0 = 0.0, ztot
    svg.rect(rx(rci), zy(a0), (rco - rci) * hs, (b0 - a0) * vs, "#bbbbbb", "#555", 1.0, None, 0.8)
    svg.line(rx(g["R_case_inner_conservative_mm"]), zy(0), rx(g["R_case_inner_conservative_mm"]), zy(ztot), "#c0392b", 1.2, "2 3")
    svg.text(rx(g["R_case_inner_conservative_mm"]) - 3, zy(0) - 6, "R_case_inner conservative %s" % f2(g["R_case_inner_conservative_mm"]),
             8, "#c0392b", "end")
    # display support land (DISP_LAND, nominal w_land / t_land) at the top of the front gap
    land = arch["edge_crossings"]["display_land"]
    bud = d["edge_crossings"]["budget"]
    r_land = rdisp - land["w_land_mm"]["nom"]
    z_fg = zpos["front_gap"][0]
    t_land = land["t_land_mm"]["nom"]
    svg.rect(rx(max(r_land, r_lo)), zy(z_fg), (rci - max(r_land, r_lo)) * hs, t_land * vs, "#8e44ad", "#5b2c6f", 0.8, None, 0.55)
    svg.text(rx(r_lo) - 3, zy(z_fg) + 9, "DISP_LAND t %s (from R %s)" % (f2(t_land), f2(r_land)), 8, "#5b2c6f", "end")
    # conductor lower face for two exit heights: channel-governed exit (solid) and flat exit (dashed)
    b = bud["nominal"]
    rb, t_c = b["R_bend_min_mm"], b["t_conductor_mm"]
    z_fcu = zpos["main_pcb"][0]
    z_end = zpos["lower_web"][1]

    leg_y = [oy + ztot * vs + 34]

    def conductor(h, dash, col, label):
        r_v = max(rmain + rb - _bend_inset(rb, h), rchi)
        r_bs = r_v - rb
        zh = z_fcu - h
        d_attr = "M%s %s L%s %s A%s %s 0 0 1 %s %s L%s %s" % (
            f2(rx(r_lo)), f2(zy(zh)), f2(rx(r_bs)), f2(zy(zh)), f2(rb * hs), f2(rb * vs),
            f2(rx(r_v)), f2(zy(zh + rb)), f2(rx(r_v)), f2(zy(z_end)))
        svg.path(d_attr, "none", col, max(1.2, t_c * hs), dash)
        svg.line(ox, leg_y[0] - 4, ox + 34, leg_y[0] - 4, col, 2.4, dash)
        svg.text(ox + 42, leg_y[0], label % (f2(h), f2(r_bs), f2(r_v)), 9, col)
        leg_y[0] += 14
        return r_v
    conductor(0.0, "4 3", "#c0392b", "flat exit h %s above F.Cu: bend start R %s, vertical inner face R %s (= tool 180-deg wrap)")
    conductor(b["h_exit_for_channel_governed_mm"], None, "#7b241c",
              "exit h %s above F.Cu: bend start R %s, vertical inner face R %s (= R_channel_inner)")
    svg.line(rx(rmain), zy(z_fcu), rx(rmain), zy(z_fcu + lay["main_pcb"]), "#1f5fbf", 2.5)
    svg.text(rx(rci) + 3, zy(z_fg) + 9, "h_max %s (land ceiling)" % f2(b["h_max_mm"]), 8, "#5b2c6f")
    # edge-wrap 180 deg model outer extent
    svg.line(rx(rwrap), zy(zpos["main_pcb"][0] - 0.6), rx(rwrap), zy(zpos["main_pcb"][1] + 0.6), "#c0392b", 2.0, "4 2")
    svg.text(rx(rwrap) + 4, zy(zpos["main_pcb"][1]) + 12, "180° wrap outer %s" % f2(rwrap), 8, "#c0392b")
    # labels
    svg.text(rx(rdisp) - 4, zy(zpos["display"][0] + 1.0), "display", 8, "#333", "end")
    svg.text(rx(rmain) - 4, zy(zpos["main_pcb"][1]) + 9, "MAIN R %s" % f1(rmain), 8, "#1f5fbf", "end")
    svg.text(rx(rpmax) - 4, zy(zpos["battery_zone"][0] + 1.2), "pack R_max %s" % f2(rpmax), 8, "#a35f00", "end")
    svg.text(rx(rci) + 3, zy(0) - 6, "R_case_inner %s" % f2(rci), 8)
    svg.text(rx(rco) + 3, zy(0) + 12, "R_case_outer %s" % f2(rco), 8)
    # radial axis ticks
    for rt in (21, 22, 23, 24, 25):
        svg.line(rx(rt), zy(ztot), rx(rt), zy(ztot) + 5, "#444", 1.0)
        svg.text(rx(rt), zy(ztot) + 17, "R %d" % rt, 8, "#444", "middle")
    # edge-crossing budget table (edge_crossings.results.budget)
    ty = leg_y[0] + 14
    svg.text(ox, ty, "Edge-crossing radial budget (mm; margin = R_case_inner - (R_v + t + c); flat-flex stand-in)", 10, weight="bold")
    cols = (("corner", 0, "start"), ("straight", 110, "end"), ("flat exit", 175, "end"), ("land ceil.", 240, "end"),
            ("h_exit min", 305, "end"), ("R_mouth max", 380, "end"), ("t_allow", 435, "end"), ("lower web", 495, "end"))
    ty += 14
    for lab, dx, anc in cols:
        svg.text(ox + dx, ty, lab, 9, "#444", anc)
    for corner in ("nominal", "conservative", "optimistic"):
        ty += 13
        bb = bud[corner]
        vals = (corner, f2(check_value(zs, corner, "margin_straight_run")), _mm(bb["margin_flat_exit_mm"]),
                _mm(bb["margin_at_h_max_mm"]), _mm(bb["h_exit_min_for_zero_margin_mm"]), _mm(bb["R_mouth_max_mm"]),
                _mm(bb["t_allow_straight_mm"]), _mm(bb["lower_web_margin_mm"]))
        for (lab, dx, anc), v in zip(cols, vals):
            svg.text(ox + dx, ty, v, 9, "#111", anc)
    ty += 22
    svg.text(ox, ty, "Crossings: front-gap z window nominal / conservative / optimistic (mm)", 10, weight="bold")
    for x in arch["edge_crossings"]["crossings"]:
        per = d["edge_crossings"]["crossings"][x["id"]]
        ty += 13
        if "z_window_mm" in per["nominal"]:
            ref = per["nominal"]["h_parts_ref"]
            zt = "%s: z window %s" % ("no F.Cu part under the approach" if ref == "none" else "over %s %s" % (ref, _mm(per["nominal"]["h_parts_mm"])),
                                      " / ".join(_mm(per[c]["z_window_mm"]) for c in ("nominal", "conservative", "optimistic")))
        else:
            zt = "crossing azimuth open: radial budget only"
        svg.text(ox, ty, "%s  %s" % (x["id"], zt), 9)
    # path legend
    ly = ty + 26
    svg.text(ox, ly, "Paths in the plan view", 10, weight="bold")
    for col, dash, w, lab in legend:
        ly += 15
        svg.line(ox, ly - 4, ox + 34, ly - 4, col, w, dash)
        svg.text(ox + 42, ly, lab, 9)
    return svg.render()


BUILDERS = {
    "perimeter_map": build_perimeter_map,
    "rear_module_concept": build_rear_module,
    "interconnect_paths": build_interconnect,
}


def render_all(arch, zs, hm, d):
    return {k: BUILDERS[k](arch, zs, hm, d) for k in BUILDERS}


# ---------------------------------------------------------------------- checks
def close(a, b, tol=0.006):
    return abs(a - b) <= tol


REQUIRED_QUOTE_KEYS = ("T_total_mm", "T_total_margin_to_14_0_mm", "T_total_margin_to_15_5_mm", "layers_mm",
                       "H_F_under_display_mm", "H_F_under_display_ref", "H_F_runner_up_mm", "H_F_runner_up_ref",
                       "H_B_in_battery_mm", "H_B_in_battery_ref", "RSS_primary_mm", "RSS_secondary_mm",
                       "radial_mm", "T_body_nominal_by_h_pod_mm")


def numeric_diffs(exp, got, path, out, tol=0.006):
    """Structural + numeric comparison: identical key sets / lengths, numbers within tol."""
    if isinstance(exp, dict):
        if not isinstance(got, dict) or set(exp) != set(got):
            out.append("%s: keys %s != expected %s" % (path, sorted(got) if isinstance(got, dict) else got, sorted(exp)))
            return
        for k in exp:
            numeric_diffs(exp[k], got[k], "%s.%s" % (path, k), out, tol)
    elif isinstance(exp, (list, tuple)):
        if not isinstance(got, list) or len(got) != len(exp):
            out.append("%s: length/type differs from expected %s" % (path, list(exp)))
            return
        for i, (e, g) in enumerate(zip(exp, got)):
            numeric_diffs(e, g, "%s[%d]" % (path, i), out, tol)
    elif exp is None or isinstance(exp, (str, bool)):
        if got != exp or type(got) is not type(exp):
            out.append("%s: %r != expected %r" % (path, got, exp))
    elif isinstance(got, bool) or not isinstance(got, (int, float)) or abs(exp - got) > tol:
        out.append("%s: %r != expected %r" % (path, got, exp))


# ------------------------------------------------- numeric-leaf coverage (F3)
# Every int/float leaf of architecture.json must be either compared by `check` against its
# generated / register / placement / derived source (Coverage.cmp) or listed below with a reason.
# Paths use the "id" of list items that have one, otherwise the list index; "*" matches any element.
COVERAGE_EXEMPT = (
    (("rear_module", "envelope_derivation", "*", "*"),
     "REAR envelope study inputs (eta, A_conn, A_lands, s_ED_max, m_edge per corner): PARAMETRIC placeholders that feed the derivation"),
    (("rear_module", "zones", "afe_band_az", "*"), "illustrative AFE-band azimuths of the proposed REAR orientation (diagram, not a dimension)"),
    (("rear_module", "zones", "tongue_az"), "illustrative MAX30208 tongue azimuth of the proposed REAR orientation (diagram)"),
    (("rear_module", "zones", "land_az", "*"), "illustrative REAR support-land azimuths (section D: 'illustrative az 30 / 150 / 300')"),
    (("rear_module", "section_blocks", "*", "x_frac"), "section-diagram layout fraction (drawing position only)"),
    (("rear_module", "section_barrier_frac", "*"), "section-diagram barrier positions (drawing position only)"),
    (("rear_module", "t_barrier_study_mm", "*"), "barrier wall thickness study placeholder 0.2-0.5 (PARAMETRIC LOW, section E)"),
    (("fpc_path", "service_loop_mm", "*"), "service-loop slack placeholder 10-30 (PARAMETRIC LOW)"),
    (("charger_path", "routes", "R2", "r_mm"), "rejected alternative R2: placeholder radius in the annulus"),
    (("charger_path", "routes", "R3", "r_mm"), "rejected alternative R3: placeholder radius (north route)"),
    (("charger_path", "routes", "R3", "az_from_deg"), "rejected alternative R3: placeholder azimuth (north route)"),
    (("charger_path", "routes", "R3", "az_to_deg"), "rejected alternative R3: placeholder azimuth (north route)"),
    (("interconnect", "plan_paths", "*", "points_xy", "*", "*"), "illustrative plan polyline vertices of the interconnect diagram"),
    (("conflicts", "*", "locus_xy", "*"), "diagram anchor of the conflict marker (plan position), not a dimension"),
    (("reservations", "*", "label_xy", "*"), "diagram anchor of the reservation label, not a dimension"),
    (("reservations", "TP", "geometry", "circles", "*", 2), "probe-margin radius 1.0 mm (PARAMETRIC placeholder; centres validated)"),
    (("reservations", "MAG_CLEAR", "geometry", "circles", 0, 2), "10 mm magnetic-clean placeholder radius, to be set by measurement (centre validated)"),
    (("reservations", "VENT", "geometry", "r", 0), "vent start placeholder at U4 (main_height_map r 19.55)"),
    (("reservations", "SW1", "geometry", "az", "*"), "button arc: +/-7.5 deg placeholder about the register clock position (centre validated)"),
    (("reservations", "SW2", "geometry", "az", "*"), "button arc: +/-7.5 deg placeholder about the register clock position (centre validated)"),
    (("reservations", "SW3", "geometry", "az", "*"), "button arc: +/-7.5 deg placeholder about the register clock position (centre validated)"),
    (("reservations", "SW4", "geometry", "az", "*"), "button arc: +/-7.5 deg placeholder about the register clock position (centre validated)"),
    (("reservations", "SW5", "geometry", "az", "*"), "button arc: +/-7.5 deg placeholder about the register clock position (centre validated)"),
    (("reservations", "SW1", "geometry", "r", 0), "button inner radius 21.0 placeholder (mechanism unselected, SR-BUTTONS)"),
    (("reservations", "SW2", "geometry", "r", 0), "button inner radius 21.0 placeholder (mechanism unselected, SR-BUTTONS)"),
    (("reservations", "SW3", "geometry", "r", 0), "button inner radius 21.0 placeholder (mechanism unselected, SR-BUTTONS)"),
    (("reservations", "SW4", "geometry", "r", 0), "button inner radius 21.0 placeholder (mechanism unselected, SR-BUTTONS)"),
    (("reservations", "SW5", "geometry", "r", 0), "button inner radius 21.0 placeholder (mechanism unselected, SR-BUTTONS)"),
    (("reservations", "CHG_CONTACT", "geometry", "az", "*"), "contact block +/-10 deg placeholder about the register 3 o'clock (centre validated)"),
    (("reservations", "CHG_CONTACT", "geometry", "r", "*"), "contact block radial extent placeholder (SR-CHG-MECH)"),
    (("reservations", "CHG_ROUTE", "geometry", "az", 1), "strip end placeholder at the J202 window azimuth"),
    (("reservations", "CHG_ROUTE", "geometry", "r", "*"), "strip width placeholder 17-20 (R1 radius = its mean, validated)"),
    (("reservations", "CHG_LINK", "geometry", "az", "*"), "riser slot placeholder; containment in the SW3-SW2 gap is validated"),
    (("reservations", "CHG_APPROACH", "geometry", "az", 1), "approach end placeholder: reaches the J202 window, stops before the SW2 placeholder (validated)"),
    (("reservations", "CHG_APPROACH", "geometry", "r", 0), "approach inner placeholder at the J202 window (r 18.1-20.8)"),
    (("edge_crossings", "display_land", "w_land_mm", "*"), "display support land width: PARAMETRIC planning range (brief section 9 L1, SR-DISPLAY-LAND)"),
    (("edge_crossings", "display_land", "t_land_mm", "*"), "display support land thickness: PARAMETRIC planning range (brief section 9 L1, case G3)"),
)


def fmt_path(path):
    return "".join("[%s]" % p if isinstance(p, int) else "." + str(p) for p in path).lstrip(".")


def numeric_leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from numeric_leaves(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            key = v["id"] if isinstance(v, dict) and isinstance(v.get("id"), str) else i
            yield from numeric_leaves(v, path + (key,))
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield path, o


def get_path(o, path):
    for k in path:
        if isinstance(o, list) and not isinstance(k, int):
            o = next(x for x in o if isinstance(x, dict) and x.get("id") == k)
        else:
            o = o[k]
    return o


def _pattern_match(pat, path):
    return len(pat) == len(path) and all(p == "*" or p == q for p, q in zip(pat, path))


class Coverage:
    """Records which numeric leaves were compared against an independent source."""

    def __init__(self, arch):
        self.arch, self.done, self.fails = arch, set(), []

    def cmp(self, path, expected, tol=0.006):
        try:
            got = get_path(self.arch, path)
        except (KeyError, IndexError, TypeError, StopIteration):
            self.fails.append("%s missing" % fmt_path(path))
            return
        diffs = []
        numeric_diffs(expected, got, fmt_path(path), diffs, tol)
        self.fails.extend(diffs)
        self.done.update(p for p, _ in numeric_leaves(got, path))

    def mark(self, path):
        self.done.update(p for p, _ in numeric_leaves(get_path(self.arch, path), path))

    def report(self):
        out = list(self.fails)
        used = set()
        for path, v in numeric_leaves(self.arch):
            if path in self.done:
                continue
            hit = [i for i, (pat, _) in enumerate(COVERAGE_EXEMPT) if _pattern_match(pat, path)]
            if hit:
                used.update(hit)
            else:
                out.append("numeric leaf %s = %r is neither validated nor exempted" % (fmt_path(path), v))
        for i, (pat, _) in enumerate(COVERAGE_EXEMPT):
            if i not in used:
                out.append("coverage exemption %s matches no unvalidated leaf (stale)" % fmt_path(pat))
        return out


def coverage_self_test(arch, zs, hm, reg, d):
    """Fail if an injected unvalidated numeric leaf or a mutated case radius would pass."""
    fails = []
    probe = json.loads(json.dumps(arch))
    probe["geometry"]["coverage_probe_mm"] = 1.0
    cov = Coverage(probe)
    validate_numbers(cov, probe, zs, hm, reg, d)
    if not any("coverage_probe_mm" in f for f in cov.report()):
        fails.append("coverage self-test: an injected unvalidated leaf was not reported")
    for key in ("R_case_outer_min_mm", "R_case_outer_max_mm"):
        probe = json.loads(json.dumps(arch))
        probe["geometry"][key] = 99.0
        cov = Coverage(probe)
        validate_numbers(cov, probe, zs, hm, reg, d)
        if not any(key in f for f in cov.report()):
            fails.append("coverage self-test: mutated geometry.%s was not reported" % key)
    return fails


def quote_checks(cov, arch, zs, hm):
    """Every tool quote against zstack.json / main_height_map.json, with the COMPLETE expected key set."""
    q = arch.get("tool_quotes")
    if not isinstance(q, dict):
        cov.fails.append("tool_quotes missing")
        return
    missing = [k for k in REQUIRED_QUOTE_KEYS if k not in q]
    for k in missing:
        cov.fails.append("tool_quotes lacks required key %s" % k)
    for k in q:
        if k not in REQUIRED_QUOTE_KEYS and not isinstance(q[k], str):
            cov.fails.append("tool_quotes has unexpected non-text key %s" % k)
    if missing:
        return
    corners = list(zs["corners"])
    margins = {c: zs["corners"][c]["T_total_margins_mm"] for c in corners}
    tq = ("tool_quotes",)
    cov.cmp(tq + ("T_total_mm",), {c: zs["corners"][c]["T_total_mm"] for c in corners})
    cov.cmp(tq + ("T_total_margin_to_14_0_mm",), {c: margins[c]["to_14.0"] for c in corners})
    cov.cmp(tq + ("T_total_margin_to_15_5_mm",), {c: margins[c]["to_15.5"] for c in corners})
    layer_ids = [l["id"] for l in zs["corners"][corners[0]]["layers"]]
    cov.cmp(tq + ("layers_mm",), {lid: {c: corner_layers(zs, c)[lid] for c in corners} for lid in layer_ids})
    hmi, sm = zs["height_map_inputs"], hm["summary"]
    for key, a_, b_ in (("H_F_under_display_mm", hmi["H_F_under_display_mm"], sm["H_F_under_display"]["value"]),
                        ("H_F_under_display_ref", hmi["H_F_under_display_ref"], sm["H_F_under_display"]["ref"]),
                        ("H_F_runner_up_mm", hmi["H_F_second_mm"], sm["H_F_under_display"]["runner_up_value"]),
                        ("H_F_runner_up_ref", hmi["H_F_second_ref"], sm["H_F_under_display"]["runner_up_ref"]),
                        ("H_B_in_battery_mm", hmi["H_B_in_battery_mm"], sm["H_B_in_battery"]["value"]),
                        ("H_B_in_battery_ref", hmi["H_B_in_battery_ref"], sm["H_B_in_battery"]["ref"])):
        cov.cmp(tq + (key,), a_)
        cov.cmp(tq + (key,), b_)
    rss = zs["rss_info_only"]
    cov.cmp(tq + ("RSS_primary_mm",), rss["primary_all_stack_parameters"]["T_total_rss_mm"])
    cov.cmp(tq + ("RSS_secondary_mm",), rss["secondary_nominal_active_path_only"]["T_total_rss_mm"])
    rc = zs["radial"]["corners"]
    cov.cmp(tq + ("radial_mm",), {c: {n: check_value(zs, c, n) for n in rc[c]["checks"]} for c in rc})
    got = q["T_body_nominal_by_h_pod_mm"]
    want = {s["h_pod_mm"]: s["T_body_mm"] for s in zs["corners"]["nominal"]["h_pod_sweep"]}
    try:
        keys = {float(k): k for k in got}
    except (TypeError, ValueError, AttributeError):
        cov.fails.append("tool_quotes.T_body_nominal_by_h_pod_mm keys are not numbers")
        return
    if set(keys) != set(want):
        cov.fails.append("tool_quotes.T_body_nominal_by_h_pod_mm h_pod keys %s != %s" % (sorted(keys), sorted(want)))
        return
    for hv, k in keys.items():
        cov.cmp(tq + ("T_body_nominal_by_h_pod_mm", k), want[hv])


def register_numbers(reg):
    rege = {e["id"]: e["value"] for e in reg["entries"]}

    def num(rid, pattern, group=1):
        m = re.search(pattern, rege[rid])
        if m is None:
            raise ValueError("register %s does not match %r" % (rid, pattern))
        return float(m.group(group))
    sec = rege["SECTORS"]
    vent = re.search(r"vent NE (\d+)-(\d+)", sec)
    als = re.search(r"ALS front NE (\d+):(\d+)-(\d+):(\d+)", sec)
    lra = re.search(r"LRA S (\d+):(\d+)-(\d+):(\d+)", sec)
    sw = re.search(r"SW1-3 left (\d+)/(\d+)/(\d+); SW4-5 right (\d+)/(\d+)", sec)
    chg = re.search(r"charger rear E (\d+)", sec)
    if None in (vent, als, lra, sw, chg):
        raise ValueError("register SECTORS text no longer parses")

    def clk(h, m=0):
        return (int(h) % 12) * 30.0 + int(m) * 0.5
    return {
        "cell_d": num("BATT-CELL", "Ø(\\d+\\.?\\d*) x"), "cell_t": num("BATT-CELL", "Ø\\d+\\.?\\d* x (\\d+\\.?\\d*)"),
        "pol": num("DISPLAY-MOD", "POL (\\d+\\.?\\d*)"), "fold": num("DISPLAY-FPC", "up to (\\d+\\.?\\d*) MAX"),
        "cycles": num("J1-DISPLAY", "(\\d+) mating cycles"), "i_led": num("PPG-LOAD", "~(\\d+) mA"),
        "u8_nom": num("GNSS-H", "(\\d+\\.?\\d*) nom"),
        "sfh7018a_w": num("OPT-PKG", "SFH7018A (\\d+\\.?\\d*)x"), "sfh2703_l": num("OPT-PKG", "SFH2703 (\\d+\\.?\\d*)x"),
        "vent_az": [clk(vent.group(1)), clk(vent.group(2))],
        "als_az": [clk(als.group(1), als.group(2)), clk(als.group(3), als.group(4))],
        "lra_az": [clk(lra.group(1), lra.group(2)), clk(lra.group(3), lra.group(4))],
        "sw_az": {"SW%d" % (i + 1): clk(sw.group(i + 1)) for i in range(5)},
        "chg_az": clk(chg.group(1)),
    }


# placement reservation index of every register / placement rectangle
PLACEMENT_RECTS = {"GNSS_RAD": 0, "BLE_RAD": 1, "WIFI_RAD": 2, "J1501": 3, "BATT_EXIT": 4, "J202": 5,
                   "SUP_SW": 6, "SUP_SE": 7, "SUP_NE": 8, "J201": 9}


def reservation_checks(cov, need, arch, zs, hm, regn, d):
    res = {r["id"]: r for r in arch["reservations"]}
    place = load_json(PLACEMENT)
    geo = arch["geometry"]
    byref = {f["ref"]: f for f in hm["main_footprints"]}
    r_disp = hm["summary"]["H_F_under_display"]["radius_limit_mm"]
    r_ci = check_value(zs, "nominal", "R_case_inner")
    r_ch = check_value(zs, "nominal", "R_channel_inner")
    r_env = d["rear_envelope"]["D_env_single_mm"]["nominal"] / 2.0
    r_case_out = zs["radial"]["corners"]["nominal"]["parameters"]["D_case_outer"] / 2.0
    land = arch["edge_crossings"]["display_land"]
    full = [0.0, 360.0]

    def g(rid, *rest):
        return ("reservations", rid, "geometry") + rest
    for rid, idx in PLACEMENT_RECTS.items():
        cov.cmp(g(rid, "rect"), place["reservations"][idx]["rect"], 1e-9)
    cov.cmp(g("J202", "rect"), place["j202_reservation"]["expected_bbox"], 1e-9)
    cov.cmp(g("SWD", "rect"), byref["J1301"]["courtyard_bbox"], 1e-9)
    tps = sorted((a for a in hm["summary"]["access"] if a["ref"].startswith("TP13")), key=lambda a: a["ref"])
    for i, a in enumerate(tps):
        cov.cmp(g("TP", "circles", i, 0), a["x"], 1e-9)
        cov.cmp(g("TP", "circles", i, 1), a["y"], 1e-9)
    need(len(res["TP"]["geometry"]["circles"]) == len(tps), "TP circles != TP13xx access list")
    cov.cmp(g("MAG_CLEAR", "circles", 0, 0), byref["U703"]["x"], 1e-9)
    cov.cmp(g("MAG_CLEAR", "circles", 0, 1), byref["U703"]["y"], 1e-9)
    j1 = byref["J1"]["courtyard_bbox"]
    j1_az = rect_corner_az(j1)
    j1_rmin = math.hypot(min(max(CX, j1[0]), j1[2]) - CX, min(max(CY, j1[1]), j1[3]) - CY)
    j1501_az = [round(v, 1) for v in rect_corner_az(res["J1501"]["geometry"]["rect"])]
    j1501_r = round(rect_r_max(res["J1501"]["geometry"]["rect"]), 2)
    ties = {
        "DISPLAY": (full, [0.0, r_disp]),
        "PACK": (full, [0.0, regn["cell_d"] / 2.0]),
        "REAR_ENV": (full, [0.0, r_env]),
        "DISP_LAND": (full, [r_disp - land["w_land_mm"]["max"], r_ci]),
        "DISP_FPC": ([math.floor(j1_az[0]), math.ceil(j1_az[1])], [round(j1_rmin, 2), r_disp + regn["fold"]]),
        "ALS": (regn["als_az"], [regn["pol"] / 2.0, r_disp]),
        "LRA": (regn["lra_az"], [r_env, regn["cell_d"] / 2.0]),
        "FPC_UNDER": (j1501_az, [r_env, j1501_r]),
        "FPC_CORR": (j1501_az, [j1501_r, r_ci]),
        "CHG_RISER": (res["CHG_LINK"]["geometry"]["az"], [r_ch, r_ci]),
        "BATT_TAIL": ([round(rect_corner_az(res["J201"]["geometry"]["rect"])[0], 1),
                       round(rect_corner_az(res["BATT_EXIT"]["geometry"]["rect"])[1], 1)], [r_ch, r_ci]),
    }
    for rid, (az, rr) in ties.items():
        cov.cmp(g(rid, "az"), az)
        cov.cmp(g(rid, "r"), rr)
    cov.cmp(g("VENT", "az"), regn["vent_az"])
    cov.cmp(g("VENT", "r", 1), r_case_out)
    for k in ("SW1", "SW2", "SW3", "SW4", "SW5"):
        cov.cmp(g(k, "r", 1), r_case_out)
        a0, a1 = res[k]["geometry"]["az"]
        need(close((a0 + a1) / 2.0, regn["sw_az"][k], 1e-9), "reservation %s centre != register SECTORS clock" % k)
    a0, a1 = res["CHG_CONTACT"]["geometry"]["az"]
    need(close((a0 + a1) / 2.0, regn["chg_az"], 1e-9), "CHG_CONTACT centre != register charger clock")
    cov.cmp(g("CHG_ROUTE", "az", 0), a1)
    cov.cmp(g("CHG_LINK", "r"), [res["CHG_ROUTE"]["geometry"]["r"][1], r_ch])
    cov.cmp(g("CHG_APPROACH", "az", 0), res["CHG_LINK"]["geometry"]["az"][0])
    cov.cmp(g("CHG_APPROACH", "r", 1), r_ch)
    sw3_end, sw2_start = res["SW3"]["geometry"]["az"][1], res["SW2"]["geometry"]["az"][0]
    link = res["CHG_LINK"]["geometry"]["az"]
    need(sw3_end < link[0] < link[1] < sw2_start, "charger riser slot not inside the SW3-SW2 gap")
    need(res["CHG_APPROACH"]["geometry"]["az"][1] < sw2_start, "charger approach reaches the SW2 placeholder")
    need(land["w_land_mm"]["max"] < r_disp - regn["pol"] / 2.0, "display land wider than the POL border")
    # derived columns of every reservation
    for r in arch["reservations"]:
        rid = r["id"]
        dv = d["reservations"][rid]
        gg = r["geometry"]
        if gg["type"] == "sector":
            fl = gg["az"][1] - gg["az"][0] >= 360.0
            cov.cmp(("reservations", rid, "az_deg"), full if fl else [gg["az"][0] % 360.0, gg["az"][1] % 360.0], 0.06)
            cov.cmp(("reservations", rid, "radial_mm"), list(gg["r"]))
        else:
            cov.cmp(("reservations", rid, "az_deg"), dv["az"], 0.06)
            cov.cmp(("reservations", rid, "radial_mm"), dv["r"])
        if gg["type"] == "rect":
            cov.cmp(("reservations", rid, "raw_r_max_mm"), rect_r_max(gg["rect"]))
        else:
            need("raw_r_max_mm" not in r, "reservation %s: raw_r_max_mm only for rectangles" % rid)
        cov.cmp(("reservations", rid, "area_mm2"), dv["area"], 0.06)
        need(r["clock"]["from"] == clock_str(r["az_deg"][0]) and r["clock"]["to"] == clock_str(r["az_deg"][1]),
             "reservation %s clock text != az" % rid)


def dimension_expectations(arch, zs, hm, regn, d, charger_text):
    """Expected value of every architecture.json `dimensions` entry, derived from generated outputs."""
    corners = ("thin", "nominal", "thick")
    rcorn = ("nominal", "conservative", "optimistic")

    def prm(n):
        return {k: stack_param(zs, n, k) for k in ("min", "nom", "max")}

    def lay(lid):
        return {c: corner_layers(zs, c)[lid] for c in corners}
    r1 = next(r for r in arch["charger_path"]["routes"] if r["id"] == "R1")
    lo, hi = zs["conventions"]["target_thickness_mm"]
    h_f = hm["summary"]["H_F_under_display"]
    sed_max = max(arch["rear_module"]["envelope_derivation"]["s_ED_max_mm"].values())
    ec = d["edge_crossings"]
    bud = ec["budget"]
    land = arch["edge_crossings"]["display_land"]
    return {
        "D01": [lo, hi],
        "D02": {c: zs["corners"][c]["T_total_mm"] for c in corners},
        "D03": h_f["value"],
        "D04": h_f["runner_up_value"],
        "D05": hm["summary"]["H_B_in_battery"]["value"],
        "D06": lay("front_gap"),
        "D07": prm("t_display"),
        "D08": prm("t_main"),
        "D09": lay("back_zone"),
        "D10": {"diameter": regn["cell_d"], "thickness": regn["cell_t"]},
        "D11": lay("battery_zone"),
        "D12": prm("t_lower_web"),
        "D13": prm("t_rear_pcb"),
        "D14": prm("h_rear_inner"),
        "D15": {"h_optics_max": prm("h_optics_max"), "c_optics": prm("c_optics")},
        "D16": prm("t_window"),
        "D17": [s["h_pod_mm"] for s in zs["corners"]["nominal"]["h_pod_sweep"]],
        "D18": [zs["radial"]["corners"]["nominal"]["parameters"]["R_main"], h_f["radius_limit_mm"], round(regn["pol"] / 2.0, 3)],
        "D19": [check_value(zs, c, "R_case_inner") for c in rcorn],
        "D20": [check_value(zs, c, "R_pack_max") for c in ("nominal", "conservative")],
        "D21": [bud[c]["margin_at_h_max_mm"] for c in rcorn],
        "D22": d["rear_envelope"]["A_parts_mm2"],
        "D23": {c: d["rear_envelope"]["D_env_single_mm"][c] for c in ("optimistic", "nominal", "conservative")},
        "D24": {c: d["rear_envelope"]["D_env_double_mm"][c] for c in ("optimistic", "nominal", "conservative")},
        "D25": [3.0, sed_max],
        "D26": [round(regn["sfh7018a_w"] / 2.0 + 2.0 / 2.0, 1), round(regn["sfh7018a_w"] / 2.0 + regn["sfh2703_l"] / 2.0 + 0.3, 1)],
        "D27": derive_fpc_length(arch, zs)["L_total_excl_service_mm"],
        "D28": round(regn["i_led"] / 3.0, 1),
        "D29": round(r1["r_mm"] * math.radians(r1["az_to_deg"] - r1["az_from_deg"]), 1),
        "D30": d["supports"]["largest_unsupported_arc_deg"],
        "D31": [int(regn["cycles"]), 25],
        "D32": 0.4 if "400 mA" in charger_text else None,
        "D33": round(regn["i_led"] / 1000.0 * 3.82, 2),
        "D34": [bud[c]["margin_flat_exit_mm"] for c in rcorn],
        "D35": [bud[c]["h_exit_min_for_zero_margin_mm"] for c in rcorn],
        "D36": [bud[c]["R_mouth_max_mm"] for c in rcorn],
        "D37": {k: land["w_land_mm"][k] for k in ("min", "nom", "max")},
        "D38": {k: land["t_land_mm"][k] for k in ("min", "nom", "max")},
        "D39": [ec["land_vs_rim_parts"][c]["margin_mm"] for c in rcorn],
        "D40": [bud[c]["h_max_mm"] for c in rcorn],
        "D41": [bud[c]["t_allow_straight_mm"] for c in rcorn],
        "D42": [bud[c]["lower_web_margin_mm"] for c in rcorn],
        "D43": [ec["crossings"]["XC-J202"][c]["z_window_mm"] for c in rcorn],
    }


def md_row_cells(md, ident):
    for line in md.splitlines():
        if line.startswith("| %s |" % ident):
            return [c.strip() for c in line.strip().strip("|").split(" | ")]
    return None


def md_value_text(v):
    if isinstance(v, dict):
        if all(isinstance(x, dict) for x in v.values()):
            return ", ".join("%s %s" % (k, md_value_text(x)) for k, x in v.items())
        return ", ".join("%s %s" % (k, x) for k, x in v.items())
    if isinstance(v, list):
        return " / ".join("none" if x is None else str(x) for x in v)
    return str(v)


def _mm(v):
    return "none" if v is None else "%.2f" % v


def md_expected_rows(arch, d):
    """Rows architecture.md must carry verbatim (generated tables in sections G, H, I and 12)."""
    rows = []
    for c in ("nominal", "conservative", "optimistic"):
        b = d["edge_crossings"]["budget"][c]
        rows.append("| budget %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            c, _mm(b["h_max_mm"]), _mm(b["margin_flat_exit_mm"]), _mm(b["margin_at_h_max_mm"]),
            _mm(b["R_bend_start_at_h_max_mm"]), _mm(b["h_exit_min_for_zero_margin_mm"]), _mm(b["h_exit_for_channel_governed_mm"]),
            _mm(b["R_mouth_max_mm"]), _mm(b["t_allow_straight_mm"]), _mm(b["lower_web_margin_mm"])))
        lr = d["edge_crossings"]["land_vs_rim_parts"][c]
        rows.append("| land %s | %s | %s %s | %s | %s %s | %s |" % (
            c, _mm(lr["R_land_inner_mm"]), lr["h_rim_ref"], _mm(lr["h_rim_mm"]), _mm(lr["margin_mm"]),
            lr["h_next_ref"], _mm(lr["h_next_mm"]), _mm(lr["margin_elsewhere_mm"])))
    for x in arch["edge_crossings"]["crossings"]:
        per = d["edge_crossings"]["crossings"][x["id"]]
        cells = []
        for c in ("nominal", "conservative", "optimistic"):
            b = d["edge_crossings"]["budget"][c]
            cells.append("%s / %s" % (_mm(b["margin_flat_exit_mm"]), _mm(b["margin_at_h_max_mm"])))
        n = per["nominal"]
        has_z = "z_window_mm" in n
        rows.append("| %s | %s | %s | %s | %s | %s |" % (
            x["id"], " | ".join(cells),
            ("none" if n["h_parts_ref"] == "none" else "%s %s" % (n["h_parts_ref"], _mm(n["h_parts_mm"]))) if has_z else "n/a",
            " / ".join(_mm(per[c]["z_window_mm"]) for c in ("nominal", "conservative", "optimistic")) if has_z else "n/a",
            _mm(n["riser_arc_at_R_channel_inner_mm"]) if "riser_arc_at_R_channel_inner_mm" in n else "n/a",
            "yes" if x["rear_link"] else "no"))
    for r in arch["reservations"]:
        rows.append("| %s | %s | %s-%s | %s-%s | %s-%s | %s | %s | %s |" % (
            r["id"], r["label"], r["clock"]["from"], r["clock"]["to"], f1(r["az_deg"][0]), f1(r["az_deg"][1]),
            f2(r["radial_mm"][0]), f2(r["radial_mm"][1]), "+".join(r["z_levels"]), r["class"], r["source"]))
    for a, b, zl, area in d["overlaps"]:
        cids = [c["id"] for c in arch["conflicts"] if a in c.get("reservations", []) and b in c.get("reservations", [])]
        rows.append("| %s x %s | %s | %s | %s |" % (a, b, "+".join(zl), "%.2f" % area, ", ".join(cids)))
    return rows


def validate_numbers(cov, arch, zs, hm, reg, d):
    """Every numeric value of architecture.json against its independent source (see COVERAGE_EXEMPT)."""
    fails = []

    def need(cond, msg):
        if not cond:
            fails.append(msg)
    # G2 is independently regenerated by g2_interconnect.py check. Compare the entire
    # block (including strings, outcomes and all numerical leaves), not an allowlist.
    g2_path = GEN / "g2_interconnect.json"
    if "g2" in arch and g2_path.exists():
        g2gen = load_json(g2_path)
        cov.cmp(("g2",), g2gen, 0)
        need(arch["g2"] == g2gen, "g2 block differs from generated output")
        reqs = {q["id"]: q for q in g2gen["supplier_requests"]}
        for q in arch["supplier_requests"]:
            if q["id"] in reqs:
                cov.cmp(("supplier_requests", q["id"], "g2_numeric_acceptance"), reqs[q["id"]]["numeric_acceptance"], 0)
                need(q.get("g2_numeric_acceptance") == reqs[q["id"]]["numeric_acceptance"], "G2 supplier requirements differ: " + q["id"])
        statuses = {c["id"]: c for c in g2gen["conflict_status"]}
        need(set(statuses) == {c["id"] for c in arch["conflicts"]}, "G2 conflict set differs")
        for c in arch["conflicts"]:
            expected = statuses.get(c["id"], {})
            need(c.get("g2_status") in ("RESOLVED_BY_G2", "REMAINS_OPEN", "SUPPLIER_DATA_GATED", "DEFERRED_G3", "OWNER_DECISION_GATED"), "invalid g2_status: " + c["id"])
            need(c.get("g2_status") == expected.get("g2_status") and c.get("g2_evidence") == expected.get("g2_evidence"), "G2 conflict evidence differs: " + c["id"])
    else:
        need(False, "G2 package/generated output missing")
    # G3 is an independent deterministic study. Cover the entire quoted block,
    # including every number, and preserve the G2 quotation byte-for-byte.
    g3_path = GEN / "g3_rear_optical.json"
    if "g3" in arch and g3_path.exists():
        import g3_rear_optical
        g3gen = load_json(g3_path)
        cov.cmp(("g3",), g3gen, 0)
        need(arch["g3"] == g3gen, "G3 block differs from generated output")
        try:
            g3_rear_optical.check_architecture(g3gen)
        except (AssertionError, KeyError, ValueError) as exc:
            need(False, "G3 package consistency: " + str(exc))
    elif "g3" in arch or g3_path.exists():
        need(False, "G3 package/generated output missing")
    regn = register_numbers(reg)
    stack_in = load_json(MECH / "inputs" / "stack_parameters.json")
    quote_checks(cov, arch, zs, hm)
    # geometry block
    rc = zs["radial"]["corners"]
    dco = stack_in["radial"]["parameters"]["D_case_outer"]
    need(rc["conservative"]["parameters"]["D_case_outer"] == dco["min"] and rc["optimistic"]["parameters"]["D_case_outer"] == dco["max"],
         "zstack radial corners no longer take D_case_outer at min / max")
    gp = ("geometry",)
    cov.cmp(gp + ("R_main_mm",), rc["nominal"]["parameters"]["R_main"])
    cov.cmp(gp + ("R_display_mm",), hm["summary"]["H_F_under_display"]["radius_limit_mm"])
    cov.cmp(gp + ("R_pol_mm",), regn["pol"] / 2.0)
    cov.cmp(gp + ("R_pack_nom_mm",), regn["cell_d"] / 2.0)
    cov.cmp(gp + ("R_case_outer_nom_mm",), rc["nominal"]["parameters"]["D_case_outer"] / 2.0)
    cov.cmp(gp + ("R_case_outer_min_mm",), rc["conservative"]["parameters"]["D_case_outer"] / 2.0)
    cov.cmp(gp + ("R_case_outer_max_mm",), rc["optimistic"]["parameters"]["D_case_outer"] / 2.0)
    cov.cmp(gp + ("R_case_inner_nom_mm",), check_value(zs, "nominal", "R_case_inner"))
    cov.cmp(gp + ("R_case_inner_conservative_mm",), check_value(zs, "conservative", "R_case_inner"))
    need(close(R_CLIP, rc["nominal"]["parameters"]["D_case_outer"] / 2.0, 1e-9), "R_CLIP != nominal case outer radius")
    reservation_checks(cov, need, arch, zs, hm, regn, d)
    # REAR module
    rm = ("rear_module",)
    cov.cmp(rm + ("envelope_derivation", "w_emitter_mm"), regn["sfh7018a_w"])
    for k, v in d["rear_envelope"].items():
        cov.cmp(rm + ("envelope_results", k), v)
    for i, b in enumerate(arch["rear_module"]["section_blocks"]):
        cov.cmp(rm + ("section_blocks", i, "w_mm"), {"E": regn["sfh7018a_w"], "PD": regn["sfh2703_l"]}[b["label"]])
    # levers, scenarios
    cov.cmp(("levers", "U8_nominal_height_mm"), regn["u8_nom"])
    sc = d["scenarios"]
    for k, v in sc.items():
        if k == "rows":
            for row in v:
                for kk in ("T_nominal_tolerances_mm", "T_worst_linear_mm", "T_rss_mm", "meets_upper_nominal",
                           "meets_upper_rss", "meets_upper_worst_linear"):
                    cov.cmp(("scenario_results", "rows", row["id"], kk), row[kk])
        else:
            cov.cmp(("scenario_results", k), v)
    need([r["id"] for r in arch["scenario_results"]["rows"]] == [r["id"] for r in sc["rows"]], "scenario order")
    full_ = next(r for r in sc["rows"] if r["id"] == arch["scenario_results"]["full_thick_reproduction_scenario"])
    need(close(full_["T_worst_linear_mm"], zs["corners"]["thick"]["T_total_mm"]), "all-max scenario != tool thick corner")
    # G1 quotes (G1_BRIEF.md 4.2): every g1 number in architecture.json must equal generated/g1_scenarios.json
    g1gen = load_json(MECH / "generated" / "g1_scenarios.json")
    g1 = arch.get("g1")
    need(isinstance(g1, dict), "architecture.json lacks the g1 section")
    if isinstance(g1, dict):
        grows = {r["id"]: r for r in g1.get("scenario_results", [])}
        for s in g1gen["scenarios"]:
            r = grows.get(s["id"])
            need(r is not None, "g1.scenario_results lacks %s" % s["id"])
            if r is not None:
                for k in ("T_nominal_mm", "T_rss_mm", "T_worst_linear_mm", "T_body_mm", "h_pod_mm",
                          "t_cover_mm", "t_cover_bond_mm", "h_rear_inner_mm",
                          "tolerance_sum_linear_mm", "tolerance_rss_mm"):
                    cov.cmp(("g1", "scenario_results", s["id"], k), s[k])
        for oid, opt in g1gen["cover_options"].items():
            if "t_cover_mm" in opt:
                for k in ("min", "nom", "max"):
                    cov.cmp(("g1", "cover_options", oid, "t_cover_mm", k), opt["t_cover_mm"][k])
            if opt["status"] == "COMPUTED":
                cov.cmp(("g1", "cover_options", oid, "gap_used_nominal_mm"), opt["gap_used_nominal_mm"])
                cov.cmp(("g1", "cover_options", oid, "gap_raise_from_stack_nominal_mm"),
                        opt["gap_raise_from_stack_nominal_mm"])
                cov.cmp(("g1", "cover_options", oid, "w_cover_nominal_mm"), opt["w_cover_nominal_mm"])
                cov.cmp(("g1", "cover_options", oid, "gap_required_nominal_mm"), opt["gap_required_nominal_mm"])
        cov.cmp(("g1", "cover_sizing_check", "t_cover_stack_mm"), g1gen["cover_sizing_check"]["t_cover_stack_mm"])
        cov.cmp(("g1", "cover_sizing_check", "t_cover_sized_mm"), g1gen["cover_sizing_check"]["t_cover_sized_mm"])
        cov.cmp(("g1", "legacy_cross_check", "computed_mm"), g1gen["legacy_cross_check"]["computed_mm"])
        cov.cmp(("g1", "legacy_cross_check", "expected_mm"), g1gen["legacy_cross_check"]["expected_mm"])
        dc = g1gen["deterministic_checks"]
        cov.cmp(("g1", "deterministic_checks", "fpc_underrun_lower_web", "requirement_mm"),
                dc["fpc_underrun_lower_web"]["requirement_mm"])
        cov.cmp(("g1", "deterministic_checks", "fpc_underrun_lower_web", "available_mm"),
                dc["fpc_underrun_lower_web"]["available_mm"])
        cov.cmp(("g1", "deterministic_checks", "fpc_underrun_lower_web", "margin_mm"),
                dc["fpc_underrun_lower_web"]["margin_mm"])
        for k in ("module_side_mm", "module_half_side_mm", "module_circumradius_mm",
                  "max_centre_radius_in_main_mm", "min_centre_radius_to_clear_display_mm"):
            cov.cmp(("g1", "deterministic_checks", "u8_relocation_fcu_geometry", k),
                    dc["u8_relocation_fcu_geometry"][k])
        for c in ("nominal", "conservative"):
            cov.cmp(("g1", "deterministic_checks", "rear_seal_band", "R_case_inner_mm", c),
                    dc["rear_seal_band"]["R_case_inner_mm"][c])
            for k in ("fit_margin_mm", "wall_margin_mm"):
                cov.cmp(("g1", "deterministic_checks", "cover_rim", c, k), dc["cover_rim"][c][k])
        wp = dc["window_plate"]
        cov.cmp(("g1", "deterministic_checks", "window_plate", "frame_overlap_mm"), wp["frame_overlap_mm"])
        cov.cmp(("g1", "deterministic_checks", "window_plate", "rows_passing"), wp["rows_passing"])
        cov.cmp(("g1", "deterministic_checks", "window_plate", "rows_conditional"), wp["rows_conditional"])
        cov.cmp(("g1", "deterministic_checks", "window_plate", "rows_total"), wp["rows_total"])
        for c in ("nominal", "conservative"):
            cov.cmp(("g1", "deterministic_checks", "window_plate", "unsupported_radius_mm", c),
                    wp["unsupported_radius_mm"][c])
        for k in ("min", "nom", "max"):
            cov.cmp(("g1", "deterministic_checks", "window_plate", "standoff_available_mm", k),
                    wp["standoff_available_mm"][k])
        for row in wp["rows"]:
            for k in ("t_mm", "unsupported_radius_mm", "w_clamped_mm", "sigma_clamped_MPa",
                      "w_simply_supported_mm", "sigma_simply_supported_MPa", "sigma_allow_MPa",
                      "w_over_t", "deflection_limit_mm"):
                cov.cmp(("g1", "deterministic_checks", "window_plate", "rows", row["id"], k), row[k])
        for k in ("T_nominal_mm", "T_rss_mm"):
            cov.cmp(("g1", "tradeoff", "thinnest_scenario", k), g1gen["g1_verdict"]["thinnest_scenario"][k])
            cov.cmp(("g1", "tradeoff", "thinnest_all_credible_levers", k),
                    g1gen["g1_verdict"]["thinnest_all_credible_levers"][k])
        need(g1.get("verdict") == g1gen["g1_verdict"]["verdict"],
             "g1 verdict %r != generated %r" % (g1.get("verdict"), g1gen["g1_verdict"]["verdict"]))
        for row in g1.get("conflict_status", []):
            src = next((c for c in arch["conflicts"] if c["id"] == row["id"]), None)
            need(src is not None and src.get("g1_status") == row.get("g1_status"),
                 "g1.conflict_status %s disagrees with the conflict register" % row.get("id"))
    for k, v in d["levers"].items():
        cov.cmp(("lever_results", k), v)
    # FPC path
    iface = load_json(IFACE)
    fp = ("fpc_path",)
    cov.cmp(fp + ("positions",), len(iface["positions"]))
    j1501 = load_json(PLACEMENT)["reservations"][PLACEMENT_RECTS["J1501"]]["rect"]
    cov.cmp(fp + ("connector_run_mm",), round(j1501[3] - j1501[1], 3))
    cov.cmp(fp + ("per_position_vled_current_mA",), round(regn["i_led"] / 3.0, 1))
    for k, v in derive_fpc_length(arch, zs).items():
        cov.cmp(fp + ("length_estimate", k), v)
    # edge crossings: results recomputed; the flat exit must reproduce the tool 180-degree wrap
    for k, v in d["edge_crossings"].items():
        cov.cmp(("edge_crossings", "results", k), v)
    for c, b in d["edge_crossings"]["budget"].items():
        par, _ = radial_corner(zs, c)
        if par["R_bend_min"] >= par["t_main"] / 2.0:
            need(close(b["margin_flat_exit_mm"], check_value(zs, c, "margin_edge_wrap"), 1e-6),
                 "edge-crossing flat exit (%s) != tool margin_edge_wrap" % c)
        need(close(b["margin_at_h_max_mm"], check_value(zs, c, "margin_straight_run"), 1e-6) or
             b["R_vertical_inner_at_h_max_mm"] > check_value(zs, c, "R_channel_inner"),
             "edge-crossing land-ceiling margin (%s) inconsistent with the tool straight run" % c)
    # charger path
    res = {r["id"]: r for r in arch["reservations"]}
    cg = res["CHG_ROUTE"]["geometry"]
    for route in arch["charger_path"]["routes"]:
        rp = ("charger_path", "routes", route["id"])
        if route["id"] in ("R1", "R2"):
            cov.cmp(rp + ("az_from_deg",), cg["az"][0])
            cov.cmp(rp + ("az_to_deg",), cg["az"][1])
        if route["id"] == "R1":
            cov.cmp(rp + ("r_mm",), (cg["r"][0] + cg["r"][1]) / 2.0)
        cov.cmp(rp + ("length_arc_mm",), round(route["r_mm"] * math.radians(abs(route["az_to_deg"] - route["az_from_deg"])), 1), 0.051)
    charger_text = CHARGER_MD.read_text(encoding="utf-8") if CHARGER_MD.exists() else ""
    i_chg = 0.4 if "400 mA" in charger_text else float("nan")
    d_mag = res["MAG_CLEAR"]["geometry"]["circles"][0][2]
    cov.cmp(("charger_path", "magnetometer_single_conductor_uT"), round(2e-7 * i_chg / (d_mag / 1000.0) * 1e6, 1))
    # supports, pack edge
    for k, v in d["supports"].items():
        cov.cmp(("supports", "results", k), v, 1e-9)
    for rid, v in d["pack_edge"].items():
        cov.cmp(("pack_edge", "results", rid), v)
    # conflicts: brief candidate numbers (checked as the set 1..9 in run_checks), assembly step numbers
    for c in arch["conflicts"]:
        if isinstance(c.get("brief_candidate"), int):
            need(1 <= c["brief_candidate"] <= 9, "conflict %s brief_candidate out of range" % c["id"])
            cov.mark(("conflicts", c["id"], "brief_candidate"))
    # conflicts: G1 status (G1_BRIEF.md section 7) - exactly one valid g1_status with evidence
    for c in arch["conflicts"]:
        if c.get("introduced_in") == "G2":
            continue  # G2 findings have no retroactively invented G1 verdict.
        st = c.get("g1_status")
        need(st in ("CLOSED", "REMAINS_OPEN", "SUPPLIER_DATA_GATED", "OWNER_DECISION_GATED", "DEFERRED"),
             "conflict %s lacks a valid g1_status (got %r)" % (c["id"], st))
        ev = c.get("g1_evidence")
        need(isinstance(ev, str) and len(ev) >= 10,
             "conflict %s lacks g1 evidence/dependency text" % c["id"])
    for i, st in enumerate(arch["assembly"]["steps"]):
        cov.cmp(("assembly", "steps", i, "n"), i + 1, 0)
    # dimensions
    exp_dims = dimension_expectations(arch, zs, hm, regn, d, charger_text)
    have = [dm.get("id") for dm in arch["dimensions"]]
    need(len(set(have)) == len(have), "duplicate dimension id")
    need(set(have) == set(exp_dims), "dimension ids differ from the expected set: %s" % sorted(set(have) ^ set(exp_dims)))
    for did, ev in sorted(exp_dims.items()):
        if did in have:
            cov.cmp(("dimensions", did, "value"), ev)
    cov.fails.extend(fails)
    return exp_dims


def run_checks(arch, zs, hm, reg, d, svgs, files_on_disk=True):
    fails = []

    def need(cond, msg):
        if not cond:
            fails.append(msg)

    need(arch.get("schema") == "sportwatch-mech-architecture/1", "schema id")
    # 0. detector self-tests
    fails.extend(overlap_self_test())
    # 1. source sha256 pins
    for rel, p in SOURCE_FILES.items():
        want = arch.get("source_sha256", {}).get(rel)
        need(want == sha256(p), "source sha256 stale or missing: %s" % rel)
    # 2. frozen invariants copied verbatim
    need(arch.get("frozen_invariants") == reg["frozen_invariants"], "frozen_invariants differ from input register")
    need(arch.get("coordinate_convention") == reg["coordinate_convention"], "coordinate_convention differs from register")
    # 3. every numeric leaf validated against its source or explicitly exempted (F3), with self-test
    cov = Coverage(arch)
    exp_dims = validate_numbers(cov, arch, zs, hm, reg, d)
    fails.extend("number: " + m for m in cov.report())
    fails.extend(coverage_self_test(arch, zs, hm, reg, d))
    # 4. reservation fields
    ids = set()
    for r in arch["reservations"]:
        rid = r.get("id")
        need(rid not in ids, "duplicate reservation id %s" % rid)
        ids.add(rid)
        need(r.get("class") in CLASSES, "reservation %s class" % rid)
        need(bool(r.get("z_levels")) and set(r["z_levels"]) <= set(Z_LEVELS), "reservation %s z_levels" % rid)
        need(isinstance(r.get("clock"), dict) and r["clock"].get("from") and r["clock"].get("to"), "reservation %s clock range" % rid)
        need(isinstance(r.get("radial_mm"), list) and len(r["radial_mm"]) == 2 and r["radial_mm"][0] < r["radial_mm"][1],
             "reservation %s radial range" % rid)
        need(bool(r.get("source")), "reservation %s source" % rid)
        need(r.get("kind") in ("body", "reservation", "corridor", "access", "exclusion"), "reservation %s kind" % rid)
    for x in arch["edge_crossings"]["crossings"]:
        for k in ("approach_from", "riser_reservation"):
            need(x[k] is None or x[k] in ids, "edge crossing %s %s unknown" % (x["id"], k))
        for rq in x["requests"]:
            need(any(s["id"] == rq for s in arch["supplier_requests"]), "edge crossing %s unknown request %s" % (x["id"], rq))
    # 5. overlaps listed as conflicts
    cids = set()
    covered = []
    brief = set()
    for c in arch["conflicts"]:
        cid = c.get("id")
        need(cid not in cids, "duplicate conflict id %s" % cid)
        cids.add(cid)
        need(c.get("severity") in SEVERITIES, "conflict %s severity" % cid)
        need(isinstance(c.get("options"), list) and len(c["options"]) >= 1, "conflict %s options" % cid)
        need(isinstance(c.get("owner_decision"), bool), "conflict %s owner_decision bool" % cid)
        need(bool(c.get("evidence")) and bool(c.get("description")) and bool(c.get("recommended_direction")),
             "conflict %s evidence/description/direction" % cid)
        need(isinstance(c.get("reservations"), list), "conflict %s reservations list" % cid)
        for rid in c.get("reservations", []):
            need(rid in ids, "conflict %s references unknown reservation %s" % (cid, rid))
        covered.append(set(c.get("reservations", [])))
        if c.get("brief_candidate") is not None:
            brief.add(c["brief_candidate"])
        need(c.get("verdict") in ("CONFIRMED", "REFINED", "REFUTED", "NEW"), "conflict %s verdict" % cid)
    for a, b, zs_, area in d["overlaps"]:
        need(any(a in s and b in s for s in covered), "overlap %s x %s (%s, %.2f mm2) not listed in any conflict" % (a, b, "+".join(zs_), area))
    need(brief == set(range(1, 10)), "brief section-7 candidates 1..9 not all present: %s" % sorted(brief))
    # 6. supplier requests cover register + tool SUPPLIER data
    reqs = arch["supplier_requests"]
    rids = set()
    for rq in reqs:
        need(rq.get("id") not in rids, "duplicate supplier request %s" % rq.get("id"))
        rids.add(rq.get("id"))
        for k in ("who", "what", "affects", "gate", "parametric_stand_in", "reversible_until"):
            need(bool(rq.get(k)), "supplier request %s lacks %s" % (rq.get("id"), k))
    reg_sup = [e["id"] for e in reg["entries"] if e["class"] == "SUPPLIER_DATA_REQUIRED"]
    have = {rq.get("register_id") for rq in reqs}
    for rid in reg_sup:
        need(rid in have, "SUPPLIER_DATA_REQUIRED register id %s has no supplier request" % rid)
    for pname, pv in zs["parameters"].items():
        if pv["class"] == "SUPPLIER_DATA_REQUIRED":
            need(any(pname in rq.get("parameters", []) for rq in reqs), "supplier parameter %s has no request" % pname)
    stack_in = load_json(MECH / "inputs" / "stack_parameters.json")
    for pname, pv in stack_in["radial"]["parameters"].items():
        if pv["class"] == "SUPPLIER_DATA_REQUIRED":
            need(any(pname in rq.get("parameters", []) for rq in reqs), "radial supplier parameter %s has no request" % pname)
    pk = load_json(MECH / "inputs" / "package_heights.json")
    for fpn, pv in pk["footprints"].items():
        if pv["class"] == "SUPPLIER_DATA_REQUIRED":
            need(any(fpn in rq.get("footprints", []) for rq in reqs), "package height %s has no request" % fpn)
    # 7. KNOWN needs a source (walk whole document)
    def walk(o, path):
        if isinstance(o, dict):
            if o.get("class") == "KNOWN" and not o.get("source"):
                fails.append("KNOWN without source at %s" % path)
            for k, v in o.items():
                walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, "%s[%d]" % (path, i))
    walk(arch, "")
    # 8. dimension table labels and architecture.md rows
    md_text = ARCH_MD.read_text(encoding="utf-8") if files_on_disk and ARCH_MD.exists() else None
    for dm in arch["dimensions"]:
        did = dm.get("id")
        need(dm.get("class") in CLASSES, "dimension %s class" % did)
        need(bool(dm.get("source")), "dimension %s source" % did)
        if md_text is not None and did in exp_dims:
            cells = md_row_cells(md_text, did)
            need(cells is not None and len(cells) >= 4 and cells[2] == md_value_text(dm.get("value")),
                 "architecture.md row %s value differs from architecture.json" % did)
    if md_text is not None:
        import g2_interconnect
        g2gen = load_json(GEN / "g2_interconnect.json")
        want = g2_interconnect.architecture_section(g2gen)
        need(want in md_text, "architecture.md G2 section is not the exact generated section")
        need(md_text.count("<!-- G2 GENERATED BEGIN -->") == 1 and md_text.count("<!-- G2 GENERATED END -->") == 1,
             "architecture.md must contain exactly one G2 section")
        need("15.93" not in md_text, "C1 superseded geometry residue remains")
        lines = set(md_text.splitlines())
        for row in md_expected_rows(arch, d):
            need(row in lines, "architecture.md lacks generated row: %s" % row)
    # 9. frozen electrical boundary guards
    iface = load_json(IFACE)
    pos = iface["positions"]
    nets = sorted({p["net"] for p in pos})
    need(len(pos) == 24 and len(nets) == 13, "interface must stay 24 positions / 13 nets")
    need(arch["fpc_path"]["positions"] == 24 and sorted(arch["fpc_path"]["nets"]) == nets, "architecture fpc nets != interface")
    bad_sub = ("PD_IN", "PD_GND", "VREF", "CATHODE", "_K", "MUX_SEL", "CHG", "VBUS", "VBAT", "VSYS", "RAW_5V")
    for n in arch["fpc_path"]["nets"]:
        need(not any(b in n.upper() for b in bad_sub), "forbidden net %s in sensor FPC" % n)
    need(arch["fpc_path"]["rear_local_nets_stay_rear_local"] is True, "rear-local statement")
    need(arch["charger_path"]["uses_sensor_fpc"] is False, "charger path must not use the sensor FPC")
    need(arch["charger_path"]["contacts"] == "GND/+5V/+5V/GND", "charger contact order")
    need(arch["battery"]["selected_cell"] == "LPR454440", "battery must remain LPR454440")
    need(arch["invariants_touched"] == [], "invariants_touched must be empty")
    need(arch["magnet_in_watch"] is False, "no watch-side permanent magnet")
    # 10. cross-references
    for od in arch["owner_decisions"]:
        need(bool(od.get("id")) and bool(od.get("question")) and bool(od.get("blocks")), "owner decision fields")
    for c in arch["conflicts"]:
        for od in c.get("owner_decision_ids", []):
            need(any(o["id"] == od for o in arch["owner_decisions"]), "conflict %s unknown owner decision %s" % (c["id"], od))
        if c["owner_decision"]:
            need(len(c.get("owner_decision_ids", [])) >= 1, "conflict %s owner_decision true without ids" % c["id"])
    # 11. documents mention every id they must carry
    if files_on_disk:
        need(ARCH_MD.exists(), "architecture.md missing")
        need(README.exists(), "README.md missing")
        if ARCH_MD.exists():
            md = ARCH_MD.read_text(encoding="utf-8")
            for sec in ("## A.", "## B.", "## C.", "## D.", "## E.", "## F.", "## G.", "## H.", "## I.", "## J.",
                        "## 11.", "## 12.", "## 13.", "## 14.", "## 15."):
                need(sec in md, "architecture.md lacks section %s" % sec)
            ids_ = ([c["id"] for c in arch["conflicts"]] + [s_["id"] for s_ in arch["supplier_requests"]]
                    + [o["id"] for o in arch["owner_decisions"]] + [r["id"] for r in arch["reservations"]]
                    + [x["id"] for x in arch["edge_crossings"]["crossings"]])
            for i in ids_:
                need(i in md, "architecture.md does not mention %s" % i)
            for kw in ("KNOWN", "PARAMETRIC", "SUPPLIER_DATA_REQUIRED", "OWNER DECISION REQUIRED"):
                need(kw in md, "architecture.md lacks label %s" % kw)
        if README.exists():
            rd = README.read_text(encoding="utf-8")
            for fn in ("architecture.md", "architecture.json", "arch_diagrams.py", "perimeter_map.svg",
                       "rear_module_concept.svg", "interconnect_paths.svg", "mech_model.py", "PHASE_BRIEF.md"):
                need(fn in rd, "README.md does not list %s" % fn)
    # 12. svgs well-formed and (optionally) on disk
    for name, text in svgs.items():
        try:
            xml.dom.minidom.parseString(text.encode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - report any parser error
            fails.append("svg %s not well-formed: %s" % (name, exc))
        need(text.endswith("\n") and "\r" not in text, "svg %s line endings" % name)
        if files_on_disk:
            p = SVG_FILES[name]
            need(p.exists(), "svg %s missing on disk" % name)
            if p.exists():
                need(p.read_bytes() == text.encode("utf-8"), "svg %s differs from regenerated output" % name)
    return fails


def load_all():
    arch = load_json(ARCH)
    zs = load_json(ZSTACK)
    hm = load_json(HEIGHTS)
    reg = load_json(REGISTER)
    return arch, zs, hm, reg


def cmd_build():
    arch, zs, hm, reg = load_all()
    d = derive_all(arch, zs, hm)
    svgs = render_all(arch, zs, hm, d)
    GEN.mkdir(parents=True, exist_ok=True)
    for name, text in svgs.items():
        SVG_FILES[name].write_bytes(text.encode("utf-8"))
    print(json.dumps({"status": "BUILT", "files": sorted(p.name for p in SVG_FILES.values())}, sort_keys=True))
    return 0


def cmd_check():
    fails = []
    try:
        arch, zs, hm, reg = load_all()
        d = derive_all(arch, zs, hm)
        svgs = render_all(arch, zs, hm, d)
        fails = run_checks(arch, zs, hm, reg, d, svgs)
        counts = {"reservations": len(arch["reservations"]), "overlap_pairs": len(d["overlaps"]),
                  "conflicts": len(arch["conflicts"]), "supplier_requests": len(arch["supplier_requests"])}
    except Exception as exc:  # noqa: BLE001 - a malformed document is a check failure, not a crash
        fails.append("check aborted: %s: %s" % (type(exc).__name__, exc))
        counts = {}
    summary = {"status": "PASS" if not fails else "FAIL", "svgs": sorted(p.name for p in SVG_FILES.values()),
               "failures": fails}
    summary.update(counts)
    print(json.dumps(summary, sort_keys=True))
    return 0 if not fails else 1


def main(argv):
    if len(argv) != 2 or argv[1] not in ("build", "check"):
        sys.stderr.write("usage: arch_diagrams.py build|check\n")
        return 2
    return cmd_build() if argv[1] == "build" else cmd_check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
