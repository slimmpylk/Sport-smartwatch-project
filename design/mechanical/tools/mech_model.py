#!/usr/bin/env python3
"""Sportwatch Rev-A mechanical stack model (stdlib only, deterministic).

Subcommands (see design/mechanical/tools/mech_model_spec.md):
  heights  write generated/main_height_map.{json,md,svg}
  stack    write generated/zstack.{json,md} and generated/zstack_section.svg
  check    regenerate in memory, byte-compare with generated/, assert invariants

Inputs are read-only. Only design/mechanical/generated/ is ever written, and
never by `check`.
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
GEN_DIR = ROOT / "design" / "mechanical" / "generated"

IN_HEIGHTS = "design/mechanical/inputs/package_heights.json"
IN_PARAMS = "design/mechanical/inputs/stack_parameters.json"
IN_REGISTER = "design/mechanical/inputs/input_register.json"
IN_PLACEMENT = "design/placement/phase1_placement.json"
IN_MAIN = "sportwatch_revA.kicad_pcb"
IN_REAR = "rear_sensor/rear_sensor_revA.kicad_pcb"
INPUT_FILES = [IN_HEIGHTS, IN_PARAMS, IN_REGISTER, IN_PLACEMENT, IN_MAIN, IN_REAR]

ORIGIN = (100.0, 100.0)
R_DISPLAY = 21.95        # display outline radius (43.9 / 2)
R_BATTERY = 22.0         # battery nominal projection radius
R_MAIN_OUTLINE = 23.0
EXPECT_MAIN = {"total": 184, "F.Cu": 167, "B.Cu": 17}
EXPECT_REAR = 44
CLASSES = {"KNOWN", "PARAMETRIC", "SUPPLIER_DATA_REQUIRED"}
H_POD_SWEEP = [0.0, 0.5, 0.8, 1.0, 1.5]
PX_PER_MM = 8

BANDS = [  # (id, label, fill)
    ("lt0.5", "< 0.5 mm", "#d9ead3"),
    ("0.5-1.0", "0.5 - 1.0 mm", "#fff2cc"),
    ("1.0-2.0", "1.0 - 2.0 mm", "#f9cb9c"),
    ("ge2.0", ">= 2.0 mm", "#ea9999"),
    ("unknown", "unknown", "#b4a7d6"),
]
BAND_FILL = {b[0]: b[2] for b in BANDS}

# Rule / check text this tool implements. `check` fails if the input differs, so
# a silent edit of stack_parameters.json cannot leave stale formulas in the code.
EXPECTED_RULES = {
    "front_gap": "max(H_F_under_display + c_front, h_shield_can + c_front, h_j1_mated). H_F_under_display = max seated F.Cu height (package max + solder_allowance for PARAMETRIC parts) of MAIN footprints whose centre lies within r <= 21.95 mm (display outline radius 43.9/2) - the display is a rigid flat module, so its rear plane must clear the tallest part anywhere beneath it. Also report the governing reference designator and the second-tallest value with its reference.",
    "back_zone": "max(t_carrier_web, H_B_in_battery + c_back) + t_insulator. H_B_in_battery = max seated B.Cu height of MAIN footprints whose centre lies within r <= 22.0 mm (battery nominal projection).",
    "battery_zone": "t_pack_nom + tol_pack_thick + g_axial + c_axial",
    "rear_inner": "0 if h_rear_inner == 0 else h_rear_inner + c_rear_inner",
    "optics_zone": "h_optics_max + c_optics",
}
EXPECTED_RADIAL_CHECKS = {
    "R_case_inner": "D_case_outer/2 - t_case_wall",
    "R_pack_max": "(D_pack_nom + tol_pack_dia)/2",
    "R_channel_inner": "R_pack_max + c_radial + t_carrier_wall",
    "R_channel_outer_straight": "R_channel_inner + t_fpc + c_fpc",
    "margin_straight_run": "R_case_inner - R_channel_outer_straight  (vertical FPC run beside the pack)",
    "R_edge_wrap_outer": "R_main + max(R_bend_min, t_main/2) + t_fpc + c_fpc  (180-degree wrap of an FPC from a MAIN F.Cu connector around the MAIN edge)",
    "margin_edge_wrap": "R_case_inner - R_edge_wrap_outer",
    "margin_main_to_case": "R_case_inner - R_main  (bare MAIN edge clearance, before any FPC)",
}
EXPECTED_Z_ORDER = ["front_extra", "front_bond", "display", "front_gap", "main_pcb", "back_zone",
                    "battery_zone", "lower_web", "rear_inner", "rear_pcb", "optics_zone", "window"]


# --------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------
def r3(v):
    return round(v, 3) + 0.0


def rnd(obj):
    if isinstance(obj, float):
        return r3(obj)
    if isinstance(obj, dict):
        return {k: rnd(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v) for v in obj]
    return obj


def dumps(obj):
    return json.dumps(rnd(obj), indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def nat_key(ref):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", ref)]


def fmt(v, nd=3):
    if v is None:
        return "-"
    s = f"{r3(v):.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def sn(v):
    """SVG number."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def md_cell(s):
    return str(s).replace("|", "/")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# KiCad S-expression parsing
# --------------------------------------------------------------------------
_TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def parse_sexpr(text):
    stack = [[]]
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            stack[-1].append(node)
        elif t[0] == '"':
            stack[-1].append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            stack[-1].append(t)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError("unbalanced S-expression")
    return stack[0][0]


def child(node, head):
    for c in node:
        if isinstance(c, list) and c and c[0] == head:
            return c
    return None


def children(node, head):
    return [c for c in node if isinstance(c, list) and c and c[0] == head]


def _xy(node):
    return float(node[1]), float(node[2])


def courtyard_points(fp):
    pts = []
    for c in fp:
        if not (isinstance(c, list) and c and isinstance(c[0], str) and c[0].startswith("fp_")):
            continue
        layer = child(c, "layer")
        if layer is None or not layer[1].endswith("CrtYd"):
            continue
        kind = c[0]
        if kind in ("fp_line", "fp_rect"):
            pts += [_xy(child(c, "start")), _xy(child(c, "end"))]
        elif kind == "fp_poly":
            pts += [_xy(p) for p in child(c, "pts") if isinstance(p, list) and p and p[0] == "xy"]
        elif kind == "fp_circle":
            cx, cy = _xy(child(c, "center"))
            ex, ey = _xy(child(c, "end"))
            rad = math.hypot(ex - cx, ey - cy)
            pts += [(cx - rad, cy - rad), (cx + rad, cy + rad)]
        elif kind == "fp_arc":
            pts += [_xy(child(c, k)) for k in ("start", "mid", "end") if child(c, k)]
    return pts


def parse_board(path):
    root = parse_sexpr(Path(path).read_text(encoding="utf-8"))
    out = []
    for fp in children(root, "footprint"):
        lib_name = fp[1]
        name = lib_name.split(":", 1)[1] if ":" in lib_name else lib_name
        layer = child(fp, "layer")[1]
        at = child(fp, "at")
        x, y = float(at[1]), float(at[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
        ref = value = ""
        for p in children(fp, "property"):
            if p[1] == "Reference":
                ref = p[2]
            elif p[1] == "Value":
                value = p[2]
        bbox = None
        pts = courtyard_points(fp)
        if pts:
            a = math.radians(rot)
            c, s = math.cos(a), math.sin(a)
            gp = [(x + lx * c + ly * s, y - lx * s + ly * c) for lx, ly in pts]
            xs = [p[0] for p in gp]
            ys = [p[1] for p in gp]
            bbox = [r3(min(xs)), r3(min(ys)), r3(max(xs)), r3(max(ys))]
        out.append({"ref": ref, "side": layer, "x": x, "y": y, "rot": rot,
                    "footprint": name, "value": value, "courtyard_bbox": bbox})
    out.sort(key=lambda f: nat_key(f["ref"]))
    return out


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------
def load_inputs(root=ROOT):
    def jload(rel):
        return json.loads((root / rel).read_text(encoding="utf-8"))
    return {
        "heights": jload(IN_HEIGHTS),
        "params": jload(IN_PARAMS),
        "placement": jload(IN_PLACEMENT),
        "main": parse_board(root / IN_MAIN),
        "rear": parse_board(root / IN_REAR),
        "sha": {rel: sha256(root / rel) for rel in INPUT_FILES},
    }


# --------------------------------------------------------------------------
# heights
# --------------------------------------------------------------------------
def band_of(h):
    if h is None:
        return "unknown"
    if h < 0.5:
        return "lt0.5"
    if h < 1.0:
        return "0.5-1.0"
    if h < 2.0:
        return "1.0-2.0"
    return "ge2.0"


def join_heights(fps, heights, board):
    table = heights["footprints"]
    allowance = heights["solder_allowance_mm"]
    recs = []
    for f in fps:
        e = table.get(f["footprint"])
        if e is None:
            raise KeyError(f"footprint {f['footprint']!r} ({board} {f['ref']}) missing from package_heights.json")
        if e["max_mm"] is None:
            seated = None
        elif e["class"] == "PARAMETRIC":
            seated = e["max_mm"] + allowance
        else:
            seated = e["max_mm"]
        rec = {"ref": f["ref"], "side": f["side"], "x": f["x"], "y": f["y"], "rot": f["rot"],
               "footprint": f["footprint"], "value": f["value"], "seated_max": seated,
               "height_class": e["class"], "height_band": band_of(seated),
               "courtyard_bbox": f["courtyard_bbox"]}
        rec["r"] = math.hypot(f["x"] - ORIGIN[0], f["y"] - ORIGIN[1]) if board == "MAIN" else None
        recs.append(rec)
    return recs


def _tall_key(rec):
    return (-rec["seated_max"], nat_key(rec["ref"]))


def _brief(rec):
    return {"ref": rec["ref"], "footprint": rec["footprint"], "seated_max": rec["seated_max"],
            "r": rec["r"], "x": rec["x"], "y": rec["y"]}


def _intersects(rec, rect):
    x0, y0, x1, y1 = rect
    centre = x0 <= r3(rec["x"]) <= x1 and y0 <= r3(rec["y"]) <= y1
    bb = rec["courtyard_bbox"]
    box = bb is not None and bb[0] <= x1 and bb[2] >= x0 and bb[1] <= y1 and bb[3] >= y0
    if centre and box:
        return "centre+bbox"
    if centre:
        return "centre"
    if box:
        return "bbox"
    return None


def build_heights(inp):
    main = join_heights(inp["main"], inp["heights"], "MAIN")
    rear = join_heights(inp["rear"], inp["heights"], "REAR")
    eps = 1e-9

    f_cu = [m for m in main if m["side"] == "F.Cu"]
    b_cu = [m for m in main if m["side"] == "B.Cu"]
    f_known = sorted([m for m in f_cu if m["seated_max"] is not None], key=_tall_key)
    f_under = [m for m in f_known if m["r"] <= R_DISPLAY + eps]
    b_under = sorted([m for m in b_cu if m["seated_max"] is not None and m["r"] <= R_BATTERY + eps], key=_tall_key)

    h_f = {"value": f_under[0]["seated_max"], "ref": f_under[0]["ref"],
           "runner_up_value": f_under[1]["seated_max"], "runner_up_ref": f_under[1]["ref"],
           "radius_limit_mm": R_DISPLAY, "parts_considered": len(f_under),
           "top5": [_brief(m) for m in f_under[:5]],
           "unknown_height_refs_in_region": [m["ref"] for m in f_cu
                                             if m["seated_max"] is None and m["r"] <= R_DISPLAY + eps]}
    h_b = {"value": b_under[0]["seated_max"], "ref": b_under[0]["ref"],
           "radius_limit_mm": R_BATTERY, "parts_considered": len(b_under),
           "unknown_height_refs_in_region": [m["ref"] for m in b_cu
                                             if m["seated_max"] is None and m["r"] <= R_BATTERY + eps]}

    reservations = []
    for res in inp["placement"]["reservations"]:
        members = []
        for m in main:
            hit = _intersects(m, res["rect"])
            if hit:
                members.append({"ref": m["ref"], "side": m["side"], "hit": hit,
                                "seated_max": m["seated_max"], "footprint": m["footprint"]})
        reservations.append({"name": res["name"], "rect": res["rect"], "scope": res.get("scope", ""),
                             "footprints": members})

    access = [{"ref": m["ref"], "side": m["side"], "x": m["x"], "y": m["y"], "r": m["r"],
               "footprint": m["footprint"]}
              for m in main if m["ref"] == "J1301" or m["ref"].startswith("TP")]

    rear_known = sorted([m for m in rear if m["seated_max"] is not None], key=_tall_key)
    rear_sum = {"count": len(rear),
                "max_known_seated_mm": rear_known[0]["seated_max"] if rear_known else None,
                "max_known_ref": rear_known[0]["ref"] if rear_known else None,
                "unknown_height_refs": [m["ref"] for m in rear if m["seated_max"] is None]}

    summary = {
        "counts_by_side": {"MAIN": {"F.Cu": len(f_cu), "B.Cu": len(b_cu), "total": len(main)},
                           "REAR": {"F.Cu": sum(1 for m in rear if m["side"] == "F.Cu"),
                                    "B.Cu": sum(1 for m in rear if m["side"] == "B.Cu"),
                                    "total": len(rear)}},
        "f_cu_top15": [_brief(m) for m in f_known[:15]],
        "H_F_under_display": h_f,
        "H_B_in_battery": h_b,
        "b_cu_list": [{"ref": m["ref"], "footprint": m["footprint"], "value": m["value"], "x": m["x"],
                       "y": m["y"], "r": m["r"], "seated_max": m["seated_max"],
                       "in_battery": m["r"] <= R_BATTERY + eps}
                      for m in sorted(b_cu, key=lambda m: nat_key(m["ref"]))],
        "unknown_height": [{"board": b, "ref": m["ref"], "side": m["side"], "footprint": m["footprint"]}
                           for b, lst in (("MAIN", main), ("REAR", rear)) for m in lst
                           if m["seated_max"] is None],
        "reservations": reservations,
        "access": access,
        "rear": rear_sum,
    }
    return {
        "schema": "sportwatch-mech-height-map/1",
        "inputs_sha256": inp["sha"],
        "seated_max_rule": "PARAMETRIC: max_mm + solder_allowance_mm; KNOWN: max_mm; null if max_mm is null",
        "solder_allowance_mm": inp["heights"]["solder_allowance_mm"],
        "origin_mm": list(ORIGIN),
        "main_footprints": main,
        "rear_footprints": rear,
        "summary": summary,
    }


def heights_md(hm):
    s = hm["summary"]
    c = s["counts_by_side"]
    hf, hb = s["H_F_under_display"], s["H_B_in_battery"]
    L = ["# MAIN / REAR height map", "",
         "Generated by `design/mechanical/tools/mech_model.py heights`; do not edit by hand.", "",
         f"- MAIN footprints: {c['MAIN']['total']} (F.Cu {c['MAIN']['F.Cu']}, B.Cu {c['MAIN']['B.Cu']}); "
         f"REAR footprints: {c['REAR']['total']}",
         f"- seated_max rule: {hm['seated_max_rule']} (solder_allowance_mm = {fmt(hm['solder_allowance_mm'])})", "",
         "## Governing heights", "",
         "| Quantity | Value (mm) | Governing ref | Region | Parts considered |", "|---|---|---|---|---|",
         f"| H_F_under_display | {fmt(hf['value'])} | {hf['ref']} | F.Cu, r <= {fmt(hf['radius_limit_mm'])} | {hf['parts_considered']} |",
         f"| H_F_under_display runner-up | {fmt(hf['runner_up_value'])} | {hf['runner_up_ref']} | same | |",
         f"| H_B_in_battery | {fmt(hb['value'])} | {hb['ref']} | B.Cu, r <= {fmt(hb['radius_limit_mm'])} | {hb['parts_considered']} |",
         "",
         f"Unknown-height parts inside the F.Cu region: {', '.join(hf['unknown_height_refs_in_region']) or 'none'}; "
         f"inside the B.Cu region: {', '.join(hb['unknown_height_refs_in_region']) or 'none'}.", "",
         "## F.Cu top 15 tallest (MAIN)", "",
         "| # | Ref | Footprint | seated_max | r |", "|---|---|---|---|---|"]
    for i, m in enumerate(s["f_cu_top15"], 1):
        L.append(f"| {i} | {m['ref']} | {md_cell(m['footprint'])} | {fmt(m['seated_max'])} | {fmt(m['r'])} |")
    L += ["", "## B.Cu parts (MAIN)", "",
          "| Ref | Footprint | Value | seated_max | r | in_battery (r <= 22.0) |", "|---|---|---|---|---|---|"]
    for m in s["b_cu_list"]:
        L.append(f"| {m['ref']} | {md_cell(m['footprint'])} | {md_cell(m['value'])} | {fmt(m['seated_max'])} | "
                 f"{fmt(m['r'])} | {'yes' if m['in_battery'] else 'no'} |")
    L += ["", "## Unknown seated height", "", "| Board | Ref | Side | Footprint |", "|---|---|---|---|"]
    for u in s["unknown_height"]:
        L.append(f"| {u['board']} | {u['ref']} | {u['side']} | {md_cell(u['footprint'])} |")
    if not s["unknown_height"]:
        L.append("| - | none | | |")
    L += ["", "## Reservation rectangles vs MAIN footprints", "",
          "Hit = footprint centre inside the rect and/or courtyard bbox overlapping or touching it.", "",
          "| Reservation | Rect (x0,y0,x1,y1) | Footprints (ref:side:hit:seated_max) |", "|---|---|---|"]
    for r in s["reservations"]:
        mem = ", ".join(f"{m['ref']}:{m['side']}:{m['hit']}:{fmt(m['seated_max'])}" for m in r["footprints"]) or "none"
        L.append(f"| {md_cell(r['name'])} | {', '.join(fmt(v) for v in r['rect'])} | {mem} |")
    L += ["", "## Access items (J1301, TP*)", "", "| Ref | Side | x | y | r | Footprint |", "|---|---|---|---|---|---|"]
    for a in s["access"]:
        L.append(f"| {a['ref']} | {a['side']} | {fmt(a['x'])} | {fmt(a['y'])} | {fmt(a['r'])} | {md_cell(a['footprint'])} |")
    rr = s["rear"]
    L += ["", "## REAR", "",
          f"- footprints: {rr['count']}",
          f"- max known seated height: {fmt(rr['max_known_seated_mm'])} mm ({rr['max_known_ref']})",
          f"- unknown-height refs: {', '.join(rr['unknown_height_refs']) or 'none'}", ""]
    return "\n".join(L)


def heights_svg(hm, inp):
    X0, Y0, X1, Y1 = 70.0, 70.0, 130.0, 127.0
    top = 56
    plot_w = (X1 - X0) * PX_PER_MM
    legend_w = 230
    W = int(plot_w + legend_w)
    H = int((Y1 - Y0) * PX_PER_MM + top + 24)

    def px(x):
        return (x - X0) * PX_PER_MM

    def py(y):
        return (y - Y0) * PX_PER_MM + top

    cx, cy = px(ORIGIN[0]), py(ORIGIN[1])
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="DejaVu Sans, Arial, sans-serif">',
         '<defs><pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" '
         'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="#1155cc" stroke-width="1"/>'
         '</pattern></defs>',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
         '<text x="8" y="18" font-size="14" font-weight="bold">Sportwatch Rev-A MAIN height map</text>',
         '<text x="8" y="36" font-size="11">front view from display; north = -Y</text>']
    # outlines
    o.append(f'<circle cx="{sn(cx)}" cy="{sn(cy)}" r="{sn(23 * PX_PER_MM)}" fill="none" stroke="#000000" stroke-width="1.5"/>')
    o.append(f'<circle cx="{sn(cx)}" cy="{sn(cy)}" r="{sn(R_DISPLAY * PX_PER_MM)}" fill="none" stroke="#38761d" stroke-width="1"/>')
    o.append(f'<circle cx="{sn(cx)}" cy="{sn(cy)}" r="{sn(R_BATTERY * PX_PER_MM)}" fill="none" stroke="#cc0000" '
             'stroke-width="1" stroke-dasharray="6 3"/>')
    # reservations
    for r in hm["summary"]["reservations"]:
        x0, y0, x1, y1 = r["rect"]
        o.append(f'<rect x="{sn(px(x0))}" y="{sn(py(y0))}" width="{sn((x1 - x0) * PX_PER_MM)}" '
                 f'height="{sn((y1 - y0) * PX_PER_MM)}" fill="#3d85c6" fill-opacity="0.08" stroke="#3d85c6" '
                 'stroke-width="1" stroke-dasharray="3 2"/>')
        o.append(f'<text x="{sn(px(x0) + 2)}" y="{sn(py(y0) - 2)}" font-size="7" fill="#0b5394">{esc(r["name"])}</text>')
    # shield polygon
    poly = " ".join(f"{sn(px(x))},{sn(py(y))}" for x, y in inp["placement"]["shield_polygon_mm"])
    o.append(f'<polygon points="{poly}" fill="none" stroke="#a64d79" stroke-width="1.5"/>')
    sx = px(inp["placement"]["shield_polygon_mm"][0][0])
    o.append(f'<text x="{sn(sx)}" y="{sn(py(91.75) - 3)}" font-size="8" fill="#a64d79">U101 shield</text>')
    # parts: F.Cu first, B.Cu on top (hatched / dashed outline)
    labels = []
    ordered = sorted(hm["main_footprints"], key=lambda m: (m["side"] == "B.Cu", nat_key(m["ref"])))
    for m in ordered:
        bb = m["courtyard_bbox"] or [r3(m["x"] - 0.5), r3(m["y"] - 0.5), r3(m["x"] + 0.5), r3(m["y"] + 0.5)]
        fill = BAND_FILL[m["height_band"]]
        w, h = (bb[2] - bb[0]) * PX_PER_MM, (bb[3] - bb[1]) * PX_PER_MM
        rect = f'x="{sn(px(bb[0]))}" y="{sn(py(bb[1]))}" width="{sn(w)}" height="{sn(h)}"'
        if m["side"] == "B.Cu":
            o.append(f'<rect {rect} fill="{fill}" fill-opacity="0.7" stroke="#1155cc" stroke-width="1" '
                     'stroke-dasharray="3 2"/>')
            o.append(f'<rect {rect} fill="url(#hatch)" stroke="none"/>')
        else:
            o.append(f'<rect {rect} fill="{fill}" stroke="#444444" stroke-width="0.5"/>')
        special = m["ref"] == "J1301" or m["ref"].startswith("TP")
        if special or (m["seated_max"] is not None and m["seated_max"] >= 1.0):
            labels.append((m, special))
    for m, special in labels:
        o.append(f'<text x="{sn(px(m["x"]))}" y="{sn(py(m["y"]) + 2.5)}" font-size="7" text-anchor="middle" '
                 f'font-weight="{"bold" if special else "normal"}" fill="#000000">{esc(m["ref"])}</text>')
    # north arrow
    ax, ay = px(126), py(76)
    o.append(f'<line x1="{sn(ax)}" y1="{sn(ay + 30)}" x2="{sn(ax)}" y2="{sn(ay)}" stroke="#000000" stroke-width="2"/>')
    o.append(f'<polygon points="{sn(ax)},{sn(ay - 8)} {sn(ax - 5)},{sn(ay + 2)} {sn(ax + 5)},{sn(ay + 2)}" fill="#000000"/>')
    o.append(f'<text x="{sn(ax)}" y="{sn(ay - 12)}" font-size="11" text-anchor="middle" font-weight="bold">N (-Y)</text>')
    # legend
    lx = plot_w + 12
    ly = top
    o.append(f'<text x="{sn(lx)}" y="{sn(ly)}" font-size="11" font-weight="bold">Seated height band</text>')
    for i, (_, label, fill) in enumerate(BANDS):
        y = ly + 10 + i * 18
        o.append(f'<rect x="{sn(lx)}" y="{sn(y)}" width="16" height="12" fill="{fill}" stroke="#444444" stroke-width="0.5"/>')
        o.append(f'<text x="{sn(lx + 22)}" y="{sn(y + 10)}" font-size="10">{esc(label)}</text>')
    y = ly + 10 + len(BANDS) * 18 + 6
    o.append(f'<rect x="{sn(lx)}" y="{sn(y)}" width="16" height="12" fill="#ffffff" stroke="#1155cc" stroke-dasharray="3 2"/>')
    o.append(f'<rect x="{sn(lx)}" y="{sn(y)}" width="16" height="12" fill="url(#hatch)"/>')
    o.append(f'<text x="{sn(lx + 22)}" y="{sn(y + 10)}" font-size="10">B.Cu part (hatched)</text>')
    items = [("#000000", None, "MAIN outline D46"), ("#38761d", None, "display outline D43.9"),
             ("#cc0000", "6 3", "battery nominal D44"), ("#3d85c6", "3 2", "reservation"),
             ("#a64d79", None, "U101 shield polygon")]
    for i, (col, dash, label) in enumerate(items):
        yy = y + 30 + i * 18
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<line x1="{sn(lx)}" y1="{sn(yy + 6)}" x2="{sn(lx + 16)}" y2="{sn(yy + 6)}" stroke="{col}" stroke-width="1.5"{d}/>')
        o.append(f'<text x="{sn(lx + 22)}" y="{sn(yy + 10)}" font-size="10">{esc(label)}</text>')
    yy = y + 30 + len(items) * 18 + 8
    hf, hb = hm["summary"]["H_F_under_display"], hm["summary"]["H_B_in_battery"]
    for i, t in enumerate([f"H_F_under_display {fmt(hf['value'])} mm ({hf['ref']})",
                           f"H_B_in_battery {fmt(hb['value'])} mm ({hb['ref']})",
                           "labels: parts >= 1.0 mm, J1301, TP*", "scale: 1 mm = 8 px"]):
        o.append(f'<text x="{sn(lx)}" y="{sn(yy + i * 15)}" font-size="9">{esc(t)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# --------------------------------------------------------------------------
# z-stack
# --------------------------------------------------------------------------
def _pick(params, which):
    return {k: v[which] for k, v in params.items()}


def eval_stack(p, hf, hb):
    """Evaluate the z_layers for one parameter set; returns ordered layer dicts."""
    layers = []

    def add(lid, value, governing, terms, active):
        layers.append({"id": lid, "thickness_mm": value, "governing_term": governing,
                       "terms": terms, "active_params": active})

    def direct(lid, name):
        add(lid, p[name], name, {name: p[name]}, [name])

    direct("front_extra", "t_front_extra")
    direct("front_bond", "t_front_bond")
    direct("display", "t_display")
    # front_gap
    t = [("H_F_under_display + c_front", hf + p["c_front"], ["c_front"]),
         ("h_shield_can + c_front", p["h_shield_can"] + p["c_front"], ["h_shield_can", "c_front"]),
         ("h_j1_mated", p["h_j1_mated"], ["h_j1_mated"])]
    g = max(t, key=lambda e: e[1])  # first wins on ties
    add("front_gap", g[1], g[0], {e[0]: e[1] for e in t}, g[2])
    direct("main_pcb", "t_main")
    # back_zone
    t = [("H_B_in_battery + c_back", hb + p["c_back"], ["c_back"]),
         ("t_carrier_web", p["t_carrier_web"], ["t_carrier_web"])]
    g = max(t, key=lambda e: e[1])
    terms = {e[0]: e[1] for e in t}
    terms["t_insulator"] = p["t_insulator"]
    add("back_zone", g[1] + p["t_insulator"], f"{g[0]} (+ t_insulator)", terms, g[2] + ["t_insulator"])
    # battery_zone
    names = ["t_pack_nom", "tol_pack_thick", "g_axial", "c_axial"]
    add("battery_zone", sum(p[n] for n in names), "sum(" + " + ".join(names) + ")",
        {n: p[n] for n in names}, names)
    direct("lower_web", "t_lower_web")
    # rear_inner
    if p["h_rear_inner"] == 0:
        add("rear_inner", 0.0, "h_rear_inner == 0", {"h_rear_inner": p["h_rear_inner"]}, [])
    else:
        add("rear_inner", p["h_rear_inner"] + p["c_rear_inner"], "h_rear_inner + c_rear_inner",
            {"h_rear_inner": p["h_rear_inner"], "c_rear_inner": p["c_rear_inner"]},
            ["h_rear_inner", "c_rear_inner"])
    direct("rear_pcb", "t_rear_pcb")
    add("optics_zone", p["h_optics_max"] + p["c_optics"], "h_optics_max + c_optics",
        {"h_optics_max": p["h_optics_max"], "c_optics": p["c_optics"]}, ["h_optics_max", "c_optics"])
    direct("window", "t_window")
    return layers


RULE_PARAMS = {  # every parameter referenced by a rule (for the literal RSS set)
    "front_gap": ["c_front", "h_shield_can", "h_j1_mated"],
    "back_zone": ["t_carrier_web", "c_back", "t_insulator"],
    "battery_zone": ["t_pack_nom", "tol_pack_thick", "g_axial", "c_axial"],
    "rear_inner": ["h_rear_inner", "c_rear_inner"],
    "optics_zone": ["h_optics_max", "c_optics"],
}


def stack_params_in_layers(z_layers):
    names = []
    for z in z_layers:
        if "param" in z:
            names.append(z["param"])
        else:
            names += RULE_PARAMS[z["rule"]]
    return names


def _margins(t, lo, hi):
    return {f"to_{lo}": t - lo, f"to_{hi}": hi - t}


def build_stack(inp, hm):
    P = inp["params"]
    params = P["parameters"]
    lo, hi = P["conventions"]["target_thickness_mm"]
    hf = hm["summary"]["H_F_under_display"]["value"]
    hb = hm["summary"]["H_B_in_battery"]["value"]
    corner_which = {"nominal": "nom", "thin": "min", "thick": "max"}

    corners = {}
    for cname, which in corner_which.items():
        layers = eval_stack(_pick(params, which), hf, hb)
        total = sum(l["thickness_mm"] for l in layers)
        sweep = []
        for hp in H_POD_SWEEP:
            tb = total - hp
            sweep.append({"h_pod_mm": hp, "T_body_mm": tb,
                          "T_body_margins_mm": _margins(r3(tb), lo, hi)})
        corners[cname] = {
            "parameter_set": which,
            "layers": [{k: v for k, v in l.items() if k != "active_params"} for l in layers],
            "T_total_mm": total,
            "T_total_margins_mm": _margins(r3(total), lo, hi),
            "h_pod_sweep": sweep,
        }

    nom_layers = eval_stack(_pick(params, "nom"), hf, hb)
    thick_layers = eval_stack(_pick(params, "max"), hf, hb)
    t_nom = sum(l["thickness_mm"] for l in nom_layers)

    in_layers = [n for n in dict.fromkeys(stack_params_in_layers(P["z_layers"]))]
    active = [n for n in dict.fromkeys(sum((l["active_params"] for l in nom_layers), []))]

    def rss(names):
        sq = [(n, params[n]["max"] - params[n]["nom"]) for n in names if params[n]["max"] > params[n]["nom"]]
        return {"parameters": [n for n, _ in sq],
                "root_sum_square_mm": math.sqrt(sum(d * d for _, d in sq)),
                "T_total_rss_mm": t_nom + math.sqrt(sum(d * d for _, d in sq))}

    rss_all = rss(in_layers)
    rss_active = rss(active)
    rss_all["T_total_margins_mm"] = _margins(r3(rss_all["T_total_rss_mm"]), lo, hi)
    rss_active["T_total_margins_mm"] = _margins(r3(rss_active["T_total_rss_mm"]), lo, hi)

    contrib = []
    for i, (a, b) in enumerate(zip(nom_layers, thick_layers)):
        contrib.append((b["thickness_mm"] - a["thickness_mm"], i, a, b))
    contrib.sort(key=lambda e: (-e[0], e[1]))
    top3 = [{"layer": a["id"], "delta_mm": d, "nominal_mm": a["thickness_mm"], "thick_mm": b["thickness_mm"],
             "governing_nominal": a["governing_term"], "governing_thick": b["governing_term"]}
            for d, _, a, b in contrib[:3]]

    radial = build_radial(P, params)
    return {
        "schema": "sportwatch-mech-zstack/1",
        "status": P["status"],
        "inputs_sha256": inp["sha"],
        "conventions": {"T_total": P["conventions"]["T_total"], "T_body": P["conventions"]["T_body"],
                        "target_thickness_mm": [lo, hi],
                        "margin_definition": f"to_{lo} = T - {lo} (>= 0: not thinner than lower target); "
                                             f"to_{hi} = {hi} - T (>= 0: within upper target)",
                        "target_applies_to": P["conventions"]["target_applies_to"],
                        "h_pod": "sweep variable, not a corner variable: T_body = T_total - h_pod; "
                                 "T_total does not depend on h_pod"},
        "height_map_inputs": {"H_F_under_display_mm": hf,
                              "H_F_under_display_ref": hm["summary"]["H_F_under_display"]["ref"],
                              "H_F_second_mm": hm["summary"]["H_F_under_display"]["runner_up_value"],
                              "H_F_second_ref": hm["summary"]["H_F_under_display"]["runner_up_ref"],
                              "H_B_in_battery_mm": hb,
                              "H_B_in_battery_ref": hm["summary"]["H_B_in_battery"]["ref"]},
        "rules": P["rules"],
        "parameters": params,
        "corners": corners,
        "top3_thick_minus_nominal": top3,
        "thick_minus_nominal_mm": corners["thick"]["T_total_mm"] - corners["nominal"]["T_total_mm"],
        "rss_info_only": {
            "formula": P["conventions"]["rss_note"],
            "primary_all_stack_parameters": rss_all,
            "secondary_nominal_active_path_only": rss_active,
            "note": "primary = every parameter referenced by a z_layer/rule (h_pod excluded: sweep, not in T_total); "
                    "secondary = only parameters that govern at nominal. Informational only.",
        },
        "radial": radial,
        "stations": P["stations"],
    }




def eval_radial(v):
    c = {}
    c["R_case_inner"] = (v["D_case_outer"] / 2 - v["t_case_wall"],
                         {"D_case_outer": v["D_case_outer"], "t_case_wall": v["t_case_wall"]}, None)
    c["R_pack_max"] = ((v["D_pack_nom"] + v["tol_pack_dia"]) / 2,
                       {"D_pack_nom": v["D_pack_nom"], "tol_pack_dia": v["tol_pack_dia"]}, None)
    c["R_channel_inner"] = (c["R_pack_max"][0] + v["c_radial"] + v["t_carrier_wall"],
                            {"R_pack_max": c["R_pack_max"][0], "c_radial": v["c_radial"],
                             "t_carrier_wall": v["t_carrier_wall"]}, None)
    c["R_channel_outer_straight"] = (c["R_channel_inner"][0] + v["t_fpc"] + v["c_fpc"],
                                     {"R_channel_inner": c["R_channel_inner"][0], "t_fpc": v["t_fpc"],
                                      "c_fpc": v["c_fpc"]}, None)
    c["margin_straight_run"] = (c["R_case_inner"][0] - c["R_channel_outer_straight"][0],
                                {"R_case_inner": c["R_case_inner"][0],
                                 "R_channel_outer_straight": c["R_channel_outer_straight"][0]}, None)
    bend = [("R_bend_min", v["R_bend_min"]), ("t_main/2", v["t_main"] / 2)]
    gb = max(bend, key=lambda e: e[1])
    c["R_edge_wrap_outer"] = (v["R_main"] + gb[1] + v["t_fpc"] + v["c_fpc"],
                              {"R_main": v["R_main"], "R_bend_min": v["R_bend_min"],
                               "t_main/2": v["t_main"] / 2, "t_fpc": v["t_fpc"], "c_fpc": v["c_fpc"]},
                              gb[0])
    c["margin_edge_wrap"] = (c["R_case_inner"][0] - c["R_edge_wrap_outer"][0],
                             {"R_case_inner": c["R_case_inner"][0],
                              "R_edge_wrap_outer": c["R_edge_wrap_outer"][0]}, None)
    c["margin_main_to_case"] = (c["R_case_inner"][0] - v["R_main"],
                                {"R_case_inner": c["R_case_inner"][0], "R_main": v["R_main"]}, None)
    return c


def build_radial(P, params):
    rp = P["radial"]["parameters"]
    names = list(rp) + ["t_main"]
    src = {**rp, "t_main": params["t_main"]}

    def corner_a(case_d, case_wall, other):
        v = {n: src[n][other] for n in names}
        v["D_case_outer"] = src["D_case_outer"][case_d]
        v["t_case_wall"] = src["t_case_wall"][case_wall]
        return v

    defs = [
        ("nominal", {n: src[n]["nom"] for n in names},
         "every parameter at nom"),
        ("conservative", corner_a("min", "max", "max"),
         "D_case_outer at min; t_case_wall at max (reading A: only the case diameter is the 'case dim'; "
         "wall is an 'other term' at max, so R_case_inner is genuinely minimal); all other terms (incl. t_main) at max"),
        ("optimistic", corner_a("max", "min", "min"),
         "D_case_outer at max; t_case_wall at min (reading A); all other terms (incl. t_main) at min"),
    ]
    out = {}
    for cname, v, desc in defs:
        ch = eval_radial(v)
        checks = {}
        for k, (val, terms, gov) in ch.items():
            e = {"value_mm": val, "formula": EXPECTED_RADIAL_CHECKS[k], "terms": terms}
            if gov is not None:
                e["governing_term"] = gov
            if k.startswith("margin_"):
                e["sign"] = "+" if r3(val) > 0 else ("0" if r3(val) == 0 else "-")
                e["result"] = "PASS" if r3(val) >= 0 else "FAIL"
            checks[k] = e
        out[cname] = {"definition": desc, "parameters": v, "checks": checks}
    return {
        "note": P["radial"]["note"],
        "corner_rule": P["radial"]["corner_rule"],
        "corner_resolution": "Reading A (lead-confirmed): the conservative corner minimises R_case_inner "
                             "(D_case_outer at min, t_case_wall at max) with all other terms at max; the "
                             "optimistic corner is the mirror image.",
        "pass_rule": "margin >= 0 -> PASS (sign '+' or '0'), margin < 0 -> FAIL (sign '-')",
        "corners": out,
    }


def stack_md(zs):
    lo, hi = zs["conventions"]["target_thickness_mm"]
    hin = zs["height_map_inputs"]
    cs = zs["corners"]
    L = ["# Z-stack and radial budget (PROVISIONAL PARAMETRIC STUDY)", "",
         "Generated by `design/mechanical/tools/mech_model.py stack`; do not edit by hand.", "",
         f"Status: {zs['status']}", "",
         f"- H_F_under_display = {fmt(hin['H_F_under_display_mm'])} mm ({hin['H_F_under_display_ref']}); "
         f"runner-up {fmt(hin['H_F_second_mm'])} mm ({hin['H_F_second_ref']})",
         f"- H_B_in_battery = {fmt(hin['H_B_in_battery_mm'])} mm ({hin['H_B_in_battery_ref']})",
         f"- T_total = {zs['conventions']['T_total']}",
         f"- T_body = {zs['conventions']['T_body']}",
         f"- target {lo} - {hi} mm applies to: {zs['conventions']['target_applies_to']}",
         f"- {zs['conventions']['margin_definition']}",
         f"- {zs['conventions']['h_pod']}", "",
         "## Layers per corner (mm)", "",
         "| Layer | thin | nominal | thick | Governing term (nominal) | Governing term (thick) |",
         "|---|---|---|---|---|---|"]
    for i, l in enumerate(cs["nominal"]["layers"]):
        L.append(f"| {l['id']} | {fmt(cs['thin']['layers'][i]['thickness_mm'])} | {fmt(l['thickness_mm'])} | "
                 f"{fmt(cs['thick']['layers'][i]['thickness_mm'])} | {md_cell(l['governing_term'])} | "
                 f"{md_cell(cs['thick']['layers'][i]['governing_term'])} |")
    L.append(f"| **T_total** | **{fmt(cs['thin']['T_total_mm'])}** | **{fmt(cs['nominal']['T_total_mm'])}** | "
             f"**{fmt(cs['thick']['T_total_mm'])}** | | |")
    L += ["", f"## T_total margins (to {lo} / to {hi})", "",
          "| Corner | T_total | margin to lower | margin to upper |", "|---|---|---|---|"]
    for k in ("thin", "nominal", "thick"):
        m = cs[k]["T_total_margins_mm"]
        L.append(f"| {k} | {fmt(cs[k]['T_total_mm'])} | {fmt(m[f'to_{lo}'])} | {fmt(m[f'to_{hi}'])} |")
    L += ["", "## T_body sweep (T_body = T_total - h_pod)", "",
          f"| h_pod | corner | T_body | margin to {lo} | margin to {hi} |", "|---|---|---|---|---|"]
    for i, hp in enumerate(H_POD_SWEEP):
        for k in ("thin", "nominal", "thick"):
            e = cs[k]["h_pod_sweep"][i]
            m = e["T_body_margins_mm"]
            L.append(f"| {fmt(hp)} | {k} | {fmt(e['T_body_mm'])} | {fmt(m[f'to_{lo}'])} | {fmt(m[f'to_{hi}'])} |")
    rs = zs["rss_info_only"]
    L += ["", "## RSS (informational only)", "",
          f"- primary (all stack parameters with max > nom): T_total = {fmt(rs['primary_all_stack_parameters']['T_total_rss_mm'])} mm "
          f"(sqrt-sum {fmt(rs['primary_all_stack_parameters']['root_sum_square_mm'])})",
          f"- secondary (nominal active path only): T_total = {fmt(rs['secondary_nominal_active_path_only']['T_total_rss_mm'])} mm "
          f"(sqrt-sum {fmt(rs['secondary_nominal_active_path_only']['root_sum_square_mm'])})",
          f"- thick - nominal = {fmt(zs['thick_minus_nominal_mm'])} mm", "",
          "## Three largest contributors to (thick - nominal)", "",
          "| # | Layer | delta | nominal | thick | governing (nominal) | governing (thick) |", "|---|---|---|---|---|---|---|"]
    for i, t in enumerate(zs["top3_thick_minus_nominal"], 1):
        L.append(f"| {i} | {t['layer']} | {fmt(t['delta_mm'])} | {fmt(t['nominal_mm'])} | {fmt(t['thick_mm'])} | "
                 f"{md_cell(t['governing_nominal'])} | {md_cell(t['governing_thick'])} |")
    rad = zs["radial"]
    L += ["", "## Radial budget", "", f"Corner resolution: {rad['corner_resolution']}", "",
          f"Pass rule: {rad['pass_rule']}", ""]
    cnames = list(rad["corners"])
    L.append("| Check | " + " | ".join(cnames) + " |")
    L.append("|---|" + "---|" * len(cnames))
    for k in EXPECTED_RADIAL_CHECKS:
        row = []
        for cn in cnames:
            e = rad["corners"][cn]["checks"][k]
            row.append(fmt(e["value_mm"]) + (f" {e['sign']} {e['result']}" if "result" in e else ""))
        L.append(f"| {k} | " + " | ".join(row) + " |")
    L += ["", "Corner definitions:", ""]
    for cn in cnames:
        L.append(f"- **{cn}**: {rad['corners'][cn]['definition']}")
    gov = {cn: rad['corners'][cn]['checks']['R_edge_wrap_outer'].get('governing_term') for cn in cnames}
    L += ["", "Governing term of max(R_bend_min, t_main/2) in R_edge_wrap_outer: " +
          ", ".join(f"{cn}: {g}" for cn, g in gov.items()), ""]
    return "\n".join(L)


Z_COLORS = ["#fce5cd", "#f4cccc", "#cfe2f3", "#ead1dc", "#d9d2e9", "#d0e0e3", "#fff2cc", "#d9ead3",
            "#e6b8af", "#c9daf8", "#ffe599", "#a2c4c9"]


def stack_svg(zs):
    nom = zs["corners"]["nominal"]
    rad = zs["radial"]["corners"]["nominal"]["checks"]
    W, H = 1290, 760
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="DejaVu Sans, Arial, sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
         '<text x="10" y="20" font-size="14" font-weight="bold">Z-stack CENTER station (nominal) - '
         'front at top</text>',
         '<text x="10" y="36" font-size="10">front view from display; north = -Y; PROVISIONAL PARAMETRIC STUDY</text>']
    scale, bx, bw, y0 = 36.0, 70.0, 110.0, 80.0
    o.append(f'<text x="{sn(bx)}" y="{sn(y0 - 8)}" font-size="10">FRONT (display exterior)</text>')
    z = 0.0
    prev_label_y = y0 - 4
    for i, l in enumerate(nom["layers"]):
        t = l["thickness_mm"]
        ya = y0 + z * scale
        hgt = t * scale
        fill = Z_COLORS[i % len(Z_COLORS)]
        if hgt < 1.0:
            o.append(f'<line x1="{sn(bx)}" y1="{sn(ya)}" x2="{sn(bx + bw)}" y2="{sn(ya)}" stroke="#444444" stroke-width="1"/>')
        else:
            o.append(f'<rect x="{sn(bx)}" y="{sn(ya)}" width="{sn(bw)}" height="{sn(hgt)}" fill="{fill}" '
                     'stroke="#444444" stroke-width="0.8"/>')
        mid = ya + hgt / 2
        ly = max(prev_label_y + 17, mid)
        prev_label_y = ly
        o.append(f'<polyline points="{sn(bx + bw)},{sn(mid)} {sn(bx + bw + 20)},{sn(ly)} {sn(bx + bw + 32)},{sn(ly)}" '
                 'fill="none" stroke="#888888" stroke-width="0.7"/>')
        o.append(f'<text x="{sn(bx + bw + 36)}" y="{sn(ly + 4)}" font-size="10">{esc(l["id"])} '
                 f'{fmt(t)} mm  [{esc(l["governing_term"])}]</text>')
        z += t
    yb = y0 + z * scale
    o.append(f'<text x="{sn(bx)}" y="{sn(yb + 16)}" font-size="10">REAR (skin contact / window outer face)</text>')
    # T_total dimension
    dx = bx - 18
    o.append(f'<line x1="{sn(dx)}" y1="{sn(y0)}" x2="{sn(dx)}" y2="{sn(yb)}" stroke="#000000" stroke-width="1"/>')
    o.append(f'<line x1="{sn(dx - 4)}" y1="{sn(y0)}" x2="{sn(dx + 4)}" y2="{sn(y0)}" stroke="#000000"/>')
    o.append(f'<line x1="{sn(dx - 4)}" y1="{sn(yb)}" x2="{sn(dx + 4)}" y2="{sn(yb)}" stroke="#000000"/>')
    o.append(f'<text x="{sn(dx - 6)}" y="{sn((y0 + yb) / 2)}" font-size="11" text-anchor="middle" '
             f'transform="rotate(-90 {sn(dx - 6)} {sn((y0 + yb) / 2)})">T_total = {fmt(nom["T_total_mm"])} mm</text>')
    hp = zs["parameters"]["h_pod"]["nom"]
    yt = yb - hp * scale
    o.append(f'<line x1="{sn(bx - 6)}" y1="{sn(yt)}" x2="{sn(bx + bw + 6)}" y2="{sn(yt)}" stroke="#cc0000" '
             'stroke-width="1" stroke-dasharray="4 2"/>')
    o.append(f'<text x="{sn(bx)}" y="{sn(yb + 34)}" font-size="10" fill="#cc0000">dashed: T_body plane at '
             f'h_pod = {fmt(hp)} nominal (T_body = {fmt(nom["T_total_mm"] - hp)} mm)</text>')
    o.append(f'<text x="{sn(bx)}" y="{sn(yb + 52)}" font-size="10">nominal margins: T_total to 14.0 = '
             f'{fmt(nom["T_total_margins_mm"]["to_14.0"])}, to 15.5 = {fmt(nom["T_total_margins_mm"]["to_15.5"])}</text>')

    # ---- radial section ----
    rx0, rx1 = 21.5, 25.5
    ox, sc = 700.0, 135.0

    def rx(r):
        return ox + (r - rx0) * sc

    o.append(f'<text x="{sn(ox)}" y="20" font-size="14" font-weight="bold">South radial section (nominal) - '
             'r from watch centre</text>')
    o.append(f'<text x="{sn(ox)}" y="36" font-size="10">radius axis in mm; margins = R_case_inner - requirement</text>')
    v = zs["radial"]["corners"]["nominal"]["parameters"]
    r_case_in = rad["R_case_inner"]["value_mm"]
    r_case_out = v["D_case_outer"] / 2
    rows = []

    def seg(y, r0, r1, fill, label, stagger):
        o.append(f'<rect x="{sn(rx(r0))}" y="{sn(y)}" width="{sn((r1 - r0) * sc)}" height="40" fill="{fill}" '
                 'stroke="#444444" stroke-width="0.8"/>')
        o.append(f'<text x="{sn(rx((r0 + r1) / 2))}" y="{sn(y + 52 + stagger * 11)}" font-size="9" '
                 f'text-anchor="middle">{esc(label)}</text>')

    def margin(y, r0, r1, name):
        m = r1 - r0
        if m >= 0:
            o.append(f'<rect x="{sn(rx(r0))}" y="{sn(y)}" width="{sn(m * sc)}" height="40" fill="#b6d7a8" '
                     'stroke="#38761d" stroke-width="0.8"/>')
        else:
            o.append(f'<rect x="{sn(rx(r1))}" y="{sn(y)}" width="{sn(-m * sc)}" height="40" fill="#ea9999" '
                     'fill-opacity="0.6" stroke="#cc0000" stroke-width="1" stroke-dasharray="3 2"/>')
        col = "#38761d" if m >= 0 else "#cc0000"
        o.append(f'<text x="{sn(rx(r1) - 4 if m >= 0 else rx(r1) + 4)}" y="{sn(y - 6)}" font-size="10" '
                 f'font-weight="bold" text-anchor="{"end" if m >= 0 else "start"}" fill="{col}">{esc(name)} = {"+" if m >= 0 else ""}{fmt(m)} mm {"PASS" if m >= 0 else "FAIL"}</text>')

    # row A: straight run
    yA = 80
    o.append(f'<text x="{sn(ox)}" y="{sn(yA - 22)}" font-size="10">A. straight FPC run beside pack</text>')
    r = rx0
    steps = [("R_pack_max", rad["R_pack_max"]["value_mm"], "#bdbdbd", "pack (R_pack_max)"),
             ("c_radial", v["c_radial"], "#eeeeee", "c_radial"),
             ("t_carrier_wall", v["t_carrier_wall"], "#9fc5e8", "carrier wall"),
             ("t_fpc", v["t_fpc"], "#f6b26b", "FPC"),
             ("c_fpc", v["c_fpc"], "#fff2cc", "c_fpc")]
    cur = rx0
    for i, (n, val, col, lab) in enumerate(steps):
        nxt = val if n == "R_pack_max" else cur + val
        seg(yA, cur, nxt, col, lab, i % 2)
        cur = nxt
    margin(yA, cur, r_case_in, "margin_straight_run")
    seg(yA, r_case_in, r_case_out, "#999999", "case wall", 0)
    # row B: edge wrap
    yB = 230
    o.append(f'<text x="{sn(ox)}" y="{sn(yB - 22)}" font-size="10">B. 180-degree edge wrap of FPC around MAIN edge</text>')
    bend = max(v["R_bend_min"], v["t_main"] / 2)
    cur = rx0
    steps = [("MAIN", v["R_main"], "#93c47d", "MAIN (R_main)"),
             ("bend", bend, "#f9cb9c", "max(R_bend_min, t_main/2)"),
             ("t_fpc", v["t_fpc"], "#f6b26b", "FPC"),
             ("c_fpc", v["c_fpc"], "#fff2cc", "c_fpc")]
    for i, (n, val, col, lab) in enumerate(steps):
        nxt = val if n == "MAIN" else cur + val
        seg(yB, cur, nxt, col, lab, i % 2)
        cur = nxt
    margin(yB, cur, r_case_in, "margin_edge_wrap")
    o.append(f'<line x1="{sn(rx(r_case_in))}" y1="{sn(yB)}" x2="{sn(rx(r_case_in))}" y2="{sn(yB + 40)}" '
             'stroke="#000000" stroke-width="1.5"/>')
    # row C: bare MAIN
    yC = 380
    o.append(f'<text x="{sn(ox)}" y="{sn(yC - 22)}" font-size="10">C. bare MAIN edge to case</text>')
    seg(yC, rx0, v["R_main"], "#93c47d", "MAIN (R_main)", 0)
    margin(yC, v["R_main"], r_case_in, "margin_main_to_case")
    seg(yC, r_case_in, r_case_out, "#999999", "case wall", 0)
    # R_case_inner marker across rows
    o.append(f'<line x1="{sn(rx(r_case_in))}" y1="{sn(yA - 14)}" x2="{sn(rx(r_case_in))}" y2="{sn(yC + 46)}" '
             'stroke="#000000" stroke-width="1" stroke-dasharray="5 3"/>')
    o.append(f'<text x="{sn(rx(r_case_in))}" y="{sn(yC + 62)}" font-size="10" text-anchor="middle">'
             f'R_case_inner {fmt(r_case_in)}</text>')
    # axis
    ya = 470
    o.append(f'<line x1="{sn(rx(rx0))}" y1="{ya}" x2="{sn(rx(rx1))}" y2="{ya}" stroke="#000000"/>')
    t = rx0
    while t <= rx1 + 1e-9:
        o.append(f'<line x1="{sn(rx(t))}" y1="{ya}" x2="{sn(rx(t))}" y2="{ya + 5}" stroke="#000000"/>')
        o.append(f'<text x="{sn(rx(t))}" y="{ya + 18}" font-size="9" text-anchor="middle">{fmt(t, 2)}</text>')
        t += 0.5
    o.append(f'<text x="{sn(rx((rx0 + rx1) / 2))}" y="{ya + 34}" font-size="10" text-anchor="middle">r from watch '
             'centre (mm)</text>')
    # numbers
    lines = [f"R_main = {fmt(v['R_main'])}   R_pack_max = {fmt(rad['R_pack_max']['value_mm'])}   "
             f"R_case_inner = {fmt(r_case_in)}   R_case_outer = {fmt(r_case_out)}",
             f"R_channel_inner = {fmt(rad['R_channel_inner']['value_mm'])}   "
             f"R_channel_outer_straight = {fmt(rad['R_channel_outer_straight']['value_mm'])}",
             f"R_edge_wrap_outer = {fmt(rad['R_edge_wrap_outer']['value_mm'])} "
             f"(bend term: {rad['R_edge_wrap_outer']['governing_term']})",
             f"margin_straight_run = {fmt(rad['margin_straight_run']['value_mm'])} {rad['margin_straight_run']['result']}   "
             f"margin_edge_wrap = {fmt(rad['margin_edge_wrap']['value_mm'])} {rad['margin_edge_wrap']['result']}   "
             f"margin_main_to_case = {fmt(rad['margin_main_to_case']['value_mm'])} {rad['margin_main_to_case']['result']}",
             "conservative / optimistic corner margins: see zstack.md"]
    for i, s in enumerate(lines):
        o.append(f'<text x="{sn(ox)}" y="{ya + 62 + i * 16}" font-size="10">{esc(s)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# --------------------------------------------------------------------------
# generation / commands
# --------------------------------------------------------------------------
def generate_heights(inp):
    hm = build_heights(inp)
    return hm, {"main_height_map.json": dumps(hm),
                "main_height_map.md": heights_md(hm).rstrip("\n") + "\n",
                "main_height_map.svg": heights_svg(hm, inp)}


def generate_stack(inp, hm):
    zs = build_stack(inp, hm)
    return zs, {"zstack.json": dumps(zs),
                "zstack.md": stack_md(zs).rstrip("\n") + "\n",
                "zstack_section.svg": stack_svg(zs)}


def generate_all(root=ROOT):
    inp = load_inputs(root)
    hm, hf = generate_heights(inp)
    zs, zf = generate_stack(inp, hm)
    return inp, hm, zs, {**hf, **zf}


def write_files(files):
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (GEN_DIR / name).write_bytes(text.encode("utf-8"))
        print(f"wrote design/mechanical/generated/{name}")


def validate(inp, files):
    """Return (failures, details)."""
    fails = []
    P = inp["params"]
    main, rear = inp["main"], inp["rear"]
    nf = sum(1 for f in main if f["side"] == "F.Cu")
    nb = sum(1 for f in main if f["side"] == "B.Cu")
    counts = {"main_total": len(main), "main_F.Cu": nf, "main_B.Cu": nb, "rear_total": len(rear)}
    if (len(main), nf, nb) != (EXPECT_MAIN["total"], EXPECT_MAIN["F.Cu"], EXPECT_MAIN["B.Cu"]):
        fails.append(f"MAIN counts {len(main)}/{nf}/{nb} != 184/167/17")
    if len(rear) != EXPECT_REAR:
        fails.append(f"REAR count {len(rear)} != {EXPECT_REAR}")
    known = inp["heights"]["footprints"]
    missing = sorted({f["footprint"] for f in main + rear if f["footprint"] not in known})
    if missing:
        fails.append(f"footprints missing from package_heights.json: {missing}")
    bad = []
    groups = [("parameters", P["parameters"]), ("radial.parameters", P["radial"]["parameters"])]
    for gname, grp in groups:
        for k, v in grp.items():
            if not (v["min"] <= v["nom"] <= v["max"]):
                bad.append(f"{gname}.{k}: min<=nom<=max violated")
            if v["class"] not in CLASSES:
                bad.append(f"{gname}.{k}: class {v['class']!r} invalid")
    fails += bad
    hp = P["parameters"]["h_pod"]
    if not all(hp["min"] <= s <= hp["max"] for s in H_POD_SWEEP):
        fails.append("h_pod sweep outside [min,max]")
    if P["rules"] != EXPECTED_RULES:
        fails.append("stack_parameters.json rules differ from the formulas implemented in mech_model.py")
    if P["radial"]["checks"] != EXPECTED_RADIAL_CHECKS:
        fails.append("stack_parameters.json radial checks differ from the formulas implemented in mech_model.py")
    if [z["id"] for z in P["z_layers"]] != EXPECTED_Z_ORDER:
        fails.append("stack_parameters.json z_layers differ from the layer order implemented in mech_model.py")
    for z in P["z_layers"]:
        if "param" in z and z["param"] not in P["parameters"]:
            fails.append(f"z_layer {z['id']}: unknown param {z['param']}")
    mism = []
    for name, text in files.items():
        p = GEN_DIR / name
        if not p.is_file():
            mism.append(f"{name}: missing")
        elif p.read_bytes() != text.encode("utf-8"):
            mism.append(f"{name}: differs from regenerated output")
    fails += mism
    return fails, counts


def main_cli(argv):
    if len(argv) != 2 or argv[1] not in ("heights", "stack", "check"):
        print("usage: mech_model.py {heights|stack|check}", file=sys.stderr)
        return 2
    cmd = argv[1]
    try:
        if cmd == "check":
            inp, hm, zs, files = generate_all()
            fails, counts = validate(inp, files)
            summary = {"status": "PASS" if not fails else "FAIL", "counts": counts,
                       "files_checked": sorted(files), "failures": fails,
                       "H_F_under_display": hm["summary"]["H_F_under_display"]["value"],
                       "H_B_in_battery": hm["summary"]["H_B_in_battery"]["value"],
                       "T_total_nominal": zs["corners"]["nominal"]["T_total_mm"],
                       "T_total_thick": zs["corners"]["thick"]["T_total_mm"]}
            print(json.dumps(rnd(summary), sort_keys=True))
            return 0 if not fails else 1
        inp = load_inputs()
        hm, hfiles = generate_heights(inp)
        if cmd == "heights":
            write_files(hfiles)
        else:
            _, zfiles = generate_stack(inp, hm)
            write_files(zfiles)
        return 0
    except (KeyError, ValueError, OSError) as e:
        print(f"mech_model.py: error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main_cli(sys.argv))
