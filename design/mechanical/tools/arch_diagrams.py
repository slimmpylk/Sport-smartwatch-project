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
CELL = 0.25               # overlap grid step, mm
MIN_OVERLAP_MM2 = 0.3
CLASSES = ("KNOWN", "PARAMETRIC", "SUPPLIER_DATA_REQUIRED")
Z_LEVELS = ("FRONT", "MAIN", "BATTERY", "REAR")
SEVERITIES = ("HIGH", "MEDIUM", "LOW")
Z_COLOR = {"FRONT": "#4e79a7", "MAIN": "#59a14f", "BATTERY": "#f28e2b", "REAR": "#b07aa1"}
Z_BADGE = {"FRONT": "F", "MAIN": "M", "BATTERY": "B", "REAR": "R"}


# --------------------------------------------------------------------------- io
def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


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
        a0, a1, r0, r1, area, mx, my = cell_ranges(cells)
        out[r["id"]] = {"cells": cells, "az": [a0, a1], "r": [r0, r1], "area": area, "centroid": [mx, my]}
    return out


def overlap_pairs(reservations, derived):
    pairs = []
    ids = [r["id"] for r in reservations]
    zs = {r["id"]: set(r["z_levels"]) for r in reservations}
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            common = zs[ids[i]] & zs[ids[j]]
            if not common:
                continue
            n = len(derived[ids[i]]["cells"] & derived[ids[j]]["cells"])
            if n * CELL * CELL >= MIN_OVERLAP_MM2:
                pairs.append((ids[i], ids[j], sorted(common), round(n * CELL * CELL, 1)))
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
SCEN_TOL_PARAMS = ("t_front_bond", "t_display", "c_front", "t_main", "c_back", "t_insulator",
                   "tol_pack_thick", "g_axial", "c_axial", "h_optics_max", "c_optics")


def tolerance_deltas(zs):
    return {p: round(stack_param(zs, p, "max") - stack_param(zs, p, "nom"), 4) for p in SCEN_TOL_PARAMS}


def derive_scenarios(arch, zs):
    """Scenario totals from tool layer outputs; design choices fixed, tolerances stacked."""
    nom = zs["corners"]["nominal"]["T_total_mm"]
    thick = zs["corners"]["thick"]["T_total_mm"]
    tol = tolerance_deltas(zs)
    tol_lin = sum(tol.values())
    tol_rss = math.sqrt(sum(v * v for v in tol.values()))
    d_inner_nom = stack_param(zs, "h_rear_inner", "max") + stack_param(zs, "c_rear_inner", "nom")
    d_inner_tol = stack_param(zs, "c_rear_inner", "max") - stack_param(zs, "c_rear_inner", "nom")
    cl = {c: corner_layers(zs, c) for c in ("nominal", "thick")}
    d_cover = cl["thick"]["front_extra"] - cl["nominal"]["front_extra"]
    d_window = cl["thick"]["window"] - cl["nominal"]["window"]
    d_pcb = cl["thick"]["rear_pcb"] - cl["nominal"]["rear_pcb"]
    d_web = cl["thick"]["lower_web"] - cl["nominal"]["lower_web"]
    lo, hi = zs["conventions"]["target_thickness_mm"]
    rows = []
    for s in arch["scenarios"]:
        design = 0.0
        tol_l = tol_lin
        tol_r2 = sum(v * v for v in tol.values())
        if s["double_sided_rear"]:
            design += d_inner_nom
            tol_l += d_inner_tol
            tol_r2 += d_inner_tol ** 2
        if s["added_cover"]:
            design += d_cover
        if s["window_max"]:
            design += d_window
        if s["rear_pcb_max"]:
            design += d_pcb
        if s["lower_web_max"]:
            design += d_web
        t_nom = nom + design
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
        "design_delta_double_sided_nominal_class_mm": round(d_inner_nom, 3),
        "design_delta_added_cover_mm": round(d_cover, 3),
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


def derive_fpc_variants(arch, zs):
    """Out-and-down (2 x 90 deg) FPC routing margin per radial corner, from tool outputs."""
    r_disp = arch["geometry"]["R_display_mm"]
    out = {}
    for corner in ("nominal", "conservative", "optimistic"):
        par, _ = radial_corner(zs, corner)
        r_case_inner = check_value(zs, corner, "R_case_inner")
        r_chan_in = check_value(zs, corner, "R_channel_inner")
        r_main = par["R_main"]
        inner = max(r_disp + par["R_bend_min"], r_chan_in, r_main)
        outer = inner + par["t_fpc"] + par["c_fpc"]
        out[corner] = {
            "R_bend_min": par["R_bend_min"], "t_fpc": par["t_fpc"], "c_fpc": par["c_fpc"],
            "R_case_inner": r_case_inner, "R_channel_inner": r_chan_in,
            "R_vertical_inner": round(inner, 3), "R_vertical_outer": round(outer, 3),
            "margin_out_and_down": round(r_case_inner - outer, 3),
            "margin_straight_run_tool": check_value(zs, corner, "margin_straight_run"),
            "margin_edge_wrap_180_tool": check_value(zs, corner, "margin_edge_wrap"),
        }
    return out


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


def derive_all(arch, zs, hm):
    d = {}
    d["reservations"] = derive_reservations(arch["reservations"])
    d["overlaps"] = overlap_pairs(arch["reservations"], d["reservations"])
    d["scenarios"] = derive_scenarios(arch, zs)
    d["levers"] = derive_levers(arch, zs, hm)
    d["fpc_variants"] = derive_fpc_variants(arch, zs)
    d["rear_envelope"] = derive_rear_envelope(arch, hm)
    d["supports"] = derive_supports(arch)
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
        if g["az"][1] - g["az"][0] >= 360.0:
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
    W, H = 1240, 860
    cx, cy = 430.0, 430.0
    svg = Svg(W, H, "Rev-A perimeter / Z-level reservation map (front view)",
              "Front view from display; north = -Y, east = +X. Provisional reversible architecture study; not a frozen outline.")
    svg.text(20, 26, "Rev-A perimeter reservation map - front view from display; north = -Y (up), east = +X (right)", 14, weight="bold")
    svg.text(20, 44, "PROVISIONAL / REVERSIBLE architecture study. Reservations are coarse planning volumes, not geometry approvals.", 10, "#555")
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
    svg.text(20, 26, "REAR rigid sensor module - envelope concept (PROVISIONAL, PARAMETRIC, not a placement)", 14, weight="bold")
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
    # rear_inner
    ri = lay["rear_inner"]
    svg.text(xl + wpx + 36, y + 11, "rear_inner %s (single-sided; +%s if double-sided)" % (
        f2(ri), f2(d["scenarios"]["design_delta_double_sided_nominal_class_mm"])), 9)
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
    # window
    wy = lay["window"] * vs
    svg.rect(xl, y, wpx, wy, "#cfe8ff", "#1f5fbf", 1.2, None, 0.8)
    svg.text(xl + wpx / 2, y + wy / 2 + 3, "window %s (%s-%s)" % (f2(lay["window"]), f2(par["t_window"]["min"]), f2(par["t_window"]["max"])), 9, "#000", "middle")
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
    # text block of unmodelled
    yy = y + 56
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
    W, H = 1300, 800
    cx, cy = 360.0, 400.0
    svg = Svg(W, H, "MAIN-REAR FPC path and charger harness path (plan + south radial section)",
              "Provisional routing architecture; connector MPN, pitch and orientation are not frozen.")
    g = arch["geometry"]
    svg.text(20, 26, "Interconnect paths - front-view plan (left) and south radial section (right); PROVISIONAL", 14, weight="bold")
    svg.text(20, 44, "Solid = MAIN F.Cu level; dashed = REAR level (hidden behind battery). north = -Y, east = +X.", 10, "#555")
    for r, col, w, dash in ((g["R_case_outer_nom_mm"], "#555", 2.0, None), (g["R_case_inner_nom_mm"], "#555", 1.0, "6 3"),
                            (g["R_main_mm"], "#1f5fbf", 2.0, None), (g["R_display_mm"], "#2e7d32", 1.5, None),
                            (g["R_pack_nom_mm"], "#e08a00", 1.2, "7 3")):
        svg.circle(cx, cy, r * S, "none", col, w, dash)
    ids = arch["diagram"]["interconnect_reservations"]
    for r in arch["reservations"]:
        if r["id"] in ids:
            draw_reservation(svg, cx, cy, S, r)
            c = d["reservations"][r["id"]]["centroid"]
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
    svg.text(20, H - 30, "FPC: out-and-down 2 x 90 deg at south (J1501 mouth faces outward), vertical run in the annulus beside the pack, "
             "under-run in the carrier lower web to the REAR attach edge.", 9, "#555")
    svg.text(20, H - 16, "Charger: contact block (module-carried) rear east -> REAR-level strip along the south chord (outside REAR envelope) -> "
             "crosses MAIN edge at west -> J202 (F.Cu).", 9, "#555")
    # ---- south radial section ----
    ox, oy = 790.0, 90.0
    hs = 62.0        # px per mm radial
    r_lo = 21.0
    vs = 17.0        # px per mm axial
    lay = corner_layers(zs, "nominal")
    svg.text(ox, oy - 30, "South radial section (nominal; z from front exterior at top)", 11, weight="bold")

    def rx(r):
        return ox + (r - r_lo) * hs
    z = 0.0
    zpos = {}
    for lid in ("front_extra", "front_bond", "display", "front_gap", "main_pcb", "back_zone", "battery_zone",
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
    # FPC vertical run (out-and-down) nominal
    fv = d["fpc_variants"]["nominal"]
    ytop = zpos["front_gap"][0]
    ybot = zpos["lower_web"][1]
    svg.rect(rx(fv["R_vertical_inner"]), zy(ytop + 0.5), (fv["R_vertical_outer"] - fv["R_vertical_inner"]) * hs,
             (ybot - ytop - 0.5) * vs, "#c0392b", "#7b241c", 0.8, None, 0.55)
    # edge-wrap 180 deg model outer extent
    svg.line(rx(rwrap), zy(zpos["main_pcb"][0] - 0.6), rx(rwrap), zy(zpos["main_pcb"][1] + 0.6), "#c0392b", 2.0, "4 2")
    svg.text(rx(rwrap) + 4, zy(zpos["main_pcb"][0]) + 3, "180° wrap outer %s" % f2(rwrap), 8, "#c0392b")
    # labels
    svg.text(rx(rdisp) - 4, zy(zpos["display"][0] + 1.0) , "display", 8, "#333", "end")
    svg.text(rx(rmain) - 4, zy(zpos["main_pcb"][0]) - 2, "MAIN R %s" % f1(rmain), 8, "#1f5fbf", "end")
    svg.text(rx(rpmax) - 4, zy(zpos["battery_zone"][0] + 1.2), "pack R_max %s" % f2(rpmax), 8, "#a35f00", "end")
    svg.text(rx(rci) + 3, zy(0) - 6, "R_case_inner %s" % f2(rci), 8)
    svg.text(rx(rco) + 3, zy(0) + 12, "R_case_outer %s" % f2(rco), 8)
    svg.text(rx(fv["R_vertical_inner"]) - 36, zy(ytop + 1.6) , "FPC vertical run", 8, "#7b241c", "end")
    svg.text(rx(fv["R_vertical_inner"]) - 36, zy(ytop + 1.6) + 10, "%s-%s" % (f2(fv["R_vertical_inner"]), f2(fv["R_vertical_outer"])), 8, "#7b241c", "end")
    # path legend
    ly = oy + ztot * vs + 150
    svg.text(ox, ly, "Paths in the plan view", 10, weight="bold")
    for col, dash, w, lab in legend:
        ly += 15
        svg.line(ox, ly - 4, ox + 34, ly - 4, col, w, dash)
        svg.text(ox + 42, ly, lab, 9)
    # radial axis ticks
    for rt in (21, 22, 23, 24, 25):
        svg.line(rx(rt), zy(ztot), rx(rt), zy(ztot) + 5, "#444", 1.0)
        svg.text(rx(rt), zy(ztot) + 17, "R %d" % rt, 8, "#444", "middle")
    # margin table
    ty = oy + ztot * vs + 56
    svg.text(ox, ty, "Radial margins (tool output, mm; margin = R_case_inner - requirement)", 10, weight="bold")
    ty += 14
    svg.text(ox, ty, "corner", 9, "#444")
    svg.text(ox + 120, ty, "straight run", 9, "#444", "end")
    svg.text(ox + 210, ty, "180° wrap", 9, "#444", "end")
    svg.text(ox + 320, ty, "out-and-down", 9, "#444", "end")
    svg.text(ox + 420, ty, "MAIN->case", 9, "#444", "end")
    for corner in ("nominal", "conservative", "optimistic"):
        ty += 13
        fvv = d["fpc_variants"][corner]
        svg.text(ox, ty, corner, 9)
        svg.text(ox + 120, ty, f2(fvv["margin_straight_run_tool"]), 9, "#111", "end")
        svg.text(ox + 210, ty, f2(fvv["margin_edge_wrap_180_tool"]), 9, "#111", "end")
        svg.text(ox + 320, ty, f2(fvv["margin_out_and_down"]), 9, "#111", "end")
        svg.text(ox + 420, ty, f2(check_value(zs, corner, "margin_main_to_case")), 9, "#111", "end")
    ty += 18
    svg.text(ox, ty, "out-and-down = architecture arithmetic on tool outputs: max(R_display + R_bend, R_channel_inner, R_main) + t_fpc + c_fpc", 8, "#555")
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


def run_checks(arch, zs, hm, reg, d, svgs, files_on_disk=True):
    fails = []

    def need(cond, msg):
        if not cond:
            fails.append(msg)

    need(arch.get("schema") == "sportwatch-mech-architecture/1", "schema id")
    # 1. source sha256 pins
    for rel, p in SOURCE_FILES.items():
        want = arch.get("source_sha256", {}).get(rel)
        need(want == sha256(p), "source sha256 stale or missing: %s" % rel)
    # 2. frozen invariants copied verbatim
    need(arch.get("frozen_invariants") == reg["frozen_invariants"], "frozen_invariants differ from input register")
    need(arch.get("coordinate_convention") == reg["coordinate_convention"], "coordinate_convention differs from register")
    # 3. tool quotes == zstack.json
    q = arch["tool_quotes"]
    for corner in ("thin", "nominal", "thick"):
        need(close(q["T_total_mm"][corner], zs["corners"][corner]["T_total_mm"]), "T_total %s != zstack" % corner)
        m = zs["corners"][corner]["T_total_margins_mm"]
        need(close(q["T_total_margin_to_14_0_mm"][corner], m["to_14.0"]), "margin to 14.0 %s" % corner)
        need(close(q["T_total_margin_to_15_5_mm"][corner], m["to_15.5"]), "margin to 15.5 %s" % corner)
    for lid, vals in q["layers_mm"].items():
        for corner in ("thin", "nominal", "thick"):
            need(close(vals[corner], corner_layers(zs, corner)[lid]), "layer %s %s != zstack" % (lid, corner))
    hmi = zs["height_map_inputs"]
    need(close(q["H_F_under_display_mm"], hmi["H_F_under_display_mm"]), "H_F_under_display")
    need(q["H_F_under_display_ref"] == hmi["H_F_under_display_ref"], "H_F ref")
    need(close(q["H_F_runner_up_mm"], hmi["H_F_second_mm"]), "H_F runner-up")
    need(q["H_F_runner_up_ref"] == hmi["H_F_second_ref"], "H_F runner-up ref")
    need(close(q["H_B_in_battery_mm"], hmi["H_B_in_battery_mm"]), "H_B")
    need(q["H_B_in_battery_ref"] == hmi["H_B_in_battery_ref"], "H_B ref")
    need(close(q["RSS_primary_mm"], zs["rss_info_only"]["primary_all_stack_parameters"]["T_total_rss_mm"]), "RSS primary")
    need(close(q["RSS_secondary_mm"], zs["rss_info_only"]["secondary_nominal_active_path_only"]["T_total_rss_mm"]), "RSS secondary")
    for corner in ("nominal", "conservative", "optimistic"):
        for chk, val in q["radial_mm"][corner].items():
            need(close(val, check_value(zs, corner, chk)), "radial %s %s != zstack" % (corner, chk))
    sweep = {(s["h_pod_mm"]): s for s in zs["corners"]["nominal"]["h_pod_sweep"]}
    for hp, tb in q["T_body_nominal_by_h_pod_mm"].items():
        need(close(tb, sweep[float(hp)]["T_body_mm"]), "T_body nominal h_pod=%s" % hp)
    # 4. reservations
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
        if r["class"] == "KNOWN":
            need(bool(r.get("source")), "KNOWN reservation %s lacks source" % rid)
    for r in arch["reservations"]:
        dv = d["reservations"][r["id"]]
        g = r["geometry"]
        if g["type"] == "sector":
            full = g["az"][1] - g["az"][0] >= 360.0
            want_az = [0.0, 360.0] if full else [g["az"][0] % 360.0, g["az"][1] % 360.0]
            need(close(r["az_deg"][0], want_az[0], 0.06) and close(r["az_deg"][1], want_az[1], 0.06),
                 "reservation %s az_deg != sector geometry" % r["id"])
            need(close(r["radial_mm"][0], g["r"][0], 0.006) and close(r["radial_mm"][1], g["r"][1], 0.006),
                 "reservation %s radial_mm != sector geometry" % r["id"])
        else:
            need(close(r["az_deg"][0], dv["az"][0], 0.06) and close(r["az_deg"][1], dv["az"][1], 0.06),
                 "reservation %s az_deg stale (%s vs %s-%s)" % (r["id"], r["az_deg"], f1(dv["az"][0]), f1(dv["az"][1])))
            need(close(r["radial_mm"][0], dv["r"][0], 0.006) and close(r["radial_mm"][1], dv["r"][1], 0.006),
                 "reservation %s radial_mm stale" % r["id"])
        need(close(r["area_mm2"], dv["area"], 0.06), "reservation %s area stale" % r["id"])
        need(r["clock"]["from"] == clock_str(r["az_deg"][0]) and r["clock"]["to"] == clock_str(r["az_deg"][1]),
             "reservation %s clock text != az" % r["id"])
    # geometry block vs tool outputs; REAR-envelope-derived radii vs derivation
    geo = arch["geometry"]
    need(close(geo["R_case_inner_nom_mm"], check_value(zs, "nominal", "R_case_inner")), "geometry R_case_inner nominal")
    need(close(geo["R_case_inner_conservative_mm"], check_value(zs, "conservative", "R_case_inner")), "geometry R_case_inner conservative")
    need(close(geo["R_main_mm"], zs["radial"]["corners"]["nominal"]["parameters"]["R_main"]), "geometry R_main")
    need(close(geo["R_display_mm"], hm["summary"]["H_F_under_display"]["radius_limit_mm"]), "geometry R_display")
    need(close(geo["R_pol_mm"] * 2.0, 38.9), "geometry R_pol (POL 38.9)")
    need(close(geo["R_case_outer_nom_mm"] * 2.0, zs["radial"]["corners"]["nominal"]["parameters"]["D_case_outer"]), "geometry R_case_outer nominal")
    res = {r["id"]: r for r in arch["reservations"]}
    r_env = arch["rear_module"]["envelope_results"]["D_env_single_mm"]["nominal"] / 2.0
    need(close(res["REAR_ENV"]["geometry"]["r"][1], r_env, 0.006), "REAR_ENV radius != envelope nominal / 2")
    need(close(res["LRA"]["geometry"]["r"][0], r_env, 0.006), "LRA inner radius != REAR envelope")
    need(close(res["FPC_UNDER"]["geometry"]["r"][0], r_env, 0.006), "FPC_UNDER inner radius != REAR envelope")
    need(close(res["FPC_CORR"]["geometry"]["r"][1], geo["R_case_inner_nom_mm"], 0.006), "FPC_CORR outer radius != R_case_inner nominal")
    need(close(res["DISP_FPC"]["geometry"]["r"][1], geo["R_display_mm"] + 0.7, 0.006), "DISP_FPC outer radius != display + 0.7")
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
        need(any(a in s and b in s for s in covered), "overlap %s x %s (%s, %.1f mm2) not listed in any conflict" % (a, b, "+".join(zs_), area))
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
    for pname, pv in zs["radial"]["corners"]["nominal"]["parameters"].items():
        pass
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
    # 8. dimension table labels
    for dm in arch["dimensions"]:
        need(dm.get("class") in CLASSES, "dimension %s class" % dm.get("id"))
        need(bool(dm.get("source")), "dimension %s source" % dm.get("id"))
    # 9. scenarios recomputed
    sc = d["scenarios"]
    for row, stored in zip(sc["rows"], arch["scenario_results"]["rows"]):
        need(row["id"] == stored["id"], "scenario order")
        for k in ("T_nominal_tolerances_mm", "T_worst_linear_mm", "T_rss_mm"):
            need(close(row[k], stored[k]), "scenario %s %s stale (%s vs %s)" % (row["id"], k, stored[k], row[k]))
        for k in ("meets_upper_nominal", "meets_upper_rss", "meets_upper_worst_linear"):
            need(row[k] == stored[k], "scenario %s %s flag" % (row["id"], k))
    for k in ("tolerance_sum_linear_mm", "tolerance_rss_mm"):
        need(close(sc[k], arch["scenario_results"][k]), "scenario %s stale" % k)
    # the all-max-design scenario must reproduce the tool thick corner
    full = next(r for r in sc["rows"] if r["id"] == arch["scenario_results"]["full_thick_reproduction_scenario"])
    need(close(full["T_worst_linear_mm"], zs["corners"]["thick"]["T_total_mm"]), "all-max scenario != tool thick corner")
    # 10. levers recomputed
    lv = d["levers"]
    for k, v in lv.items():
        sv = arch["lever_results"].get(k)
        if isinstance(v, (int, float)):
            need(sv is not None and close(v, sv), "lever %s stale (%s vs %s)" % (k, sv, v))
        else:
            need(sv == v, "lever %s stale" % k)
    # 11. FPC variants
    for corner, v in d["fpc_variants"].items():
        sv = arch["fpc_path"]["variants"][corner]
        for k, val in v.items():
            need(close(sv[k], val), "fpc variant %s %s stale" % (corner, k))
    fl = derive_fpc_length(arch, zs)
    for k, v in fl.items():
        need(close(arch["fpc_path"]["length_estimate"][k], v), "fpc length %s stale" % k)
    # 12. REAR envelope
    for k, v in d["rear_envelope"].items():
        sv = arch["rear_module"]["envelope_results"][k]
        if isinstance(v, dict):
            for c, val in v.items():
                need(close(sv[c], val), "rear envelope %s %s stale" % (k, c))
        else:
            need(close(sv, v), "rear envelope %s stale" % k)
    # 13. supports
    for k, v in d["supports"].items():
        need(arch["supports"]["results"][k] == v, "supports %s stale" % k)
    # 14. frozen electrical boundary guards
    iface = load_json(IFACE)
    pos = iface["positions"]
    nets = sorted({p["net"] for p in pos})
    need(len(pos) == 24 and len(nets) == 13, "interface must stay 24 positions / 13 nets")
    need(arch["fpc_path"]["positions"] == 24 and sorted(arch["fpc_path"]["nets"]) == nets, "architecture fpc nets != interface")
    local = [s.upper() for s in iface["local_only"]]
    bad_sub = ("PD_IN", "PD_GND", "VREF", "CATHODE", "_K", "MUX_SEL", "CHG", "VBUS", "VBAT", "VSYS", "RAW_5V")
    for n in arch["fpc_path"]["nets"]:
        need(not any(b in n.upper() for b in bad_sub), "forbidden net %s in sensor FPC" % n)
    need(arch["fpc_path"]["rear_local_nets_stay_rear_local"] is True, "rear-local statement")
    need(arch["charger_path"]["uses_sensor_fpc"] is False, "charger path must not use the sensor FPC")
    need(arch["charger_path"]["contacts"] == "GND/+5V/+5V/GND", "charger contact order")
    need(arch["battery"]["selected_cell"] == "LPR454440", "battery must remain LPR454440")
    need(arch["invariants_touched"] == [], "invariants_touched must be empty")
    need(arch["magnet_in_watch"] is False, "no watch-side permanent magnet")
    # 15. cross-references
    for od in arch["owner_decisions"]:
        need(bool(od.get("id")) and bool(od.get("question")) and bool(od.get("blocks")), "owner decision fields")
    for c in arch["conflicts"]:
        for od in c.get("owner_decision_ids", []):
            need(any(o["id"] == od for o in arch["owner_decisions"]), "conflict %s unknown owner decision %s" % (c["id"], od))
        if c["owner_decision"]:
            need(len(c.get("owner_decision_ids", [])) >= 1, "conflict %s owner_decision true without ids" % c["id"])
    # 15b. documents mention every id they must carry
    if files_on_disk:
        need(ARCH_MD.exists(), "architecture.md missing")
        need(README.exists(), "README.md missing")
        if ARCH_MD.exists():
            md = ARCH_MD.read_text(encoding="utf-8")
            for sec in ("## A.", "## B.", "## C.", "## D.", "## E.", "## F.", "## G.", "## H.", "## I.", "## J.",
                        "## 11.", "## 12.", "## 13.", "## 14.", "## 15."):
                need(sec in md, "architecture.md lacks section %s" % sec)
            ids = ([c["id"] for c in arch["conflicts"]] + [s_["id"] for s_ in arch["supplier_requests"]]
                   + [o["id"] for o in arch["owner_decisions"]] + [r["id"] for r in arch["reservations"]])
            for i in ids:
                need(i in md, "architecture.md does not mention %s" % i)
            for kw in ("KNOWN", "PARAMETRIC", "SUPPLIER_DATA_REQUIRED", "OWNER DECISION REQUIRED"):
                need(kw in md, "architecture.md lacks label %s" % kw)
        if README.exists():
            rd = README.read_text(encoding="utf-8")
            for fn in ("architecture.md", "architecture.json", "arch_diagrams.py", "perimeter_map.svg",
                       "rear_module_concept.svg", "interconnect_paths.svg", "mech_model.py", "PHASE_BRIEF.md"):
                need(fn in rd, "README.md does not list %s" % fn)
    # 16. svgs well-formed and (optionally) on disk
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
