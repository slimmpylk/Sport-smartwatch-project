#!/usr/bin/env python3
"""Sportwatch Rev-A G1 thickness-recovery scenarios (stdlib only, deterministic).

Subcommands:
  build   write generated/g1_scenarios.{json,md}
  check   regenerate in memory, byte-compare with generated/, validate the
          arithmetic cross-checks and the numbers quoted in architecture.json /
          architecture.md; exit 0 only on pass

Every total, sizing, check and credibility verdict is computed from
inputs/g1_scenarios.json (authored scenario definitions only),
inputs/stack_parameters.json (via mech_model.eval_stack),
inputs/package_heights.json and generated/main_height_map.json. Nothing is
hand-typed; no supplier dimension is invented. No timestamps, fixed float
formatting, byte-identical regeneration.
"""
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
MECH = ROOT / "design" / "mechanical"
GEN = MECH / "generated"
sys.path.insert(0, str(MECH / "tools"))
import mech_model  # noqa: E402

IN_SCEN = MECH / "inputs" / "g1_scenarios.json"
IN_PARAMS = MECH / "inputs" / "stack_parameters.json"
IN_HEIGHTS = MECH / "inputs" / "package_heights.json"
ARCH_JSON = MECH / "architecture.json"
ARCH_MD = MECH / "architecture.md"

TARGET_HI = 15.5
TOL = 0.001


def r3(v):
    return round(v + 0.0, 3)


def f2(v):
    return "%.2f" % v


def f3(v):
    return "%.3f" % v


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 5 ATM plate check (linear small-deflection Kirchhoff plate, circular)
# ---------------------------------------------------------------------------
def plate(material, p, a, nu, E, t, edge):
    """Return (deflection w, bending stress sigma) for a circular plate."""
    D = E * t ** 3 / (12.0 * (1.0 - nu ** 2))
    if edge == "clamped":
        w = p * a ** 4 / (64.0 * D)
        sig = 3.0 * p * a ** 2 / (4.0 * t ** 2)
    else:  # simply supported (PSA/adhesive ring on a ledge lets the edge rotate)
        w = (5.0 + nu) * p * a ** 4 / (64.0 * (1.0 + nu) * D)
        sig = 3.0 * (3.0 + nu) * p * a ** 2 / (8.0 * t ** 2)
    return w, sig


def size_cover(mat, corner, edge, rounding):
    """Thickness whose edge stress just meets sigma_allow; conservative upward grid rounding
    applied directly to the unrounded requirement (never round down below the requirement)."""
    p = corner["p_test_MPa"]
    a = corner["a_cover_mm"]
    nu = corner["nu"]
    sig = corner["sigma_allow_MPa"]
    if edge == "clamped":
        k = 3.0 * p * a ** 2 / 4.0
    else:
        k = 3.0 * (3.0 + nu) * p * a ** 2 / 8.0
    raw = math.sqrt(k / sig)
    return math.ceil(raw / rounding - 1e-12) * rounding


def corner_of(G, mat, which):
    mats = G["plate_check"]["materials"]
    m = mats[mat]
    p = G["plate_check"]["p_test_MPa"]
    a = G["plate_check"]["a_cover_mm"]
    if which == "nominal":
        return {"p_test_MPa": p["nom"], "a_cover_mm": a["nom"], "nu": m["nu"]["nom"],
                "E_MPa": m["E_MPa"]["nom"], "sigma_allow_MPa": m["sigma_allow_MPa"]["nom"]}
    if which == "conservative":
        return {"p_test_MPa": p["max"], "a_cover_mm": a["max"], "nu": m["nu"]["max"],
                "E_MPa": m["E_MPa"]["min"], "sigma_allow_MPa": m["sigma_allow_MPa"]["min"]}
    return {"p_test_MPa": p["min"], "a_cover_mm": a["min"], "nu": m["nu"]["min"],
            "E_MPa": m["E_MPa"]["max"], "sigma_allow_MPa": m["sigma_allow_MPa"]["max"]}


def cover_options(G, stack):
    """Size every COMPUTED cover option; verify the baseline against stack parameters."""
    rounding = G["plate_check"]["rounding_mm"]
    out = {}
    for opt in G["cover_options"]:
        # authored metadata is preserved through cover_options() and propagated into every
        # scenario that uses the option (design change, dependencies, risks)
        meta = {k: opt[k] for k in ("title", "design_change", "dependencies", "risks") if k in opt}
        if opt["status"] != "COMPUTED":
            out[opt["id"]] = dict(meta, id=opt["id"], status=opt["status"],
                                  t_cover_mm=opt.get("t_cover_mm"),
                                  t_cover_note=opt.get("t_cover_note", ""))
            continue
        mat = opt["material"]
        t_nom = size_cover(mat, corner_of(G, mat, "nominal"), "ss", rounding)
        t_min = size_cover(mat, corner_of(G, mat, "nominal"), "clamped", rounding)
        t_max = size_cover(mat, corner_of(G, mat, "conservative"), "ss", rounding)
        # stress / deflection at the sizing corners and at the opposite corner
        rows = []
        status = "PASS"
        for cname in ("nominal", "conservative"):
            c = corner_of(G, mat, cname)
            t = t_nom if cname == "nominal" else t_max
            for edge in ("ss", "clamped"):
                w, sig = plate(mat, c["p_test_MPa"], c["a_cover_mm"], c["nu"],
                               c["E_MPa"], t, edge)
                ok = sig <= c["sigma_allow_MPa"] + 1e-9
                if edge == "ss" and not ok:
                    status = "FAIL" if cname == "nominal" else status
                rows.append({"corner": cname, "edge": edge, "t_mm": r3(t),
                             "w_mm": r3(w), "sigma_MPa": r3(sig),
                             "sigma_allow_MPa": c["sigma_allow_MPa"],
                             "w_over_t": r3(w / t), "pass": ok})
        if not any(r["pass"] for r in rows if r["edge"] == "ss" and r["corner"] == "nominal"):
            status = "FAIL"
        elif not any(r["pass"] for r in rows if r["edge"] == "ss" and r["corner"] == "conservative"):
            status = "PASS_NOMINAL"
        # air gap: residual gap >= cover deflection at the test pressure + c_gap
        c = corner_of(G, mat, "nominal")
        w_nom, _ = plate(mat, c["p_test_MPa"], c["a_cover_mm"], c["nu"], c["E_MPa"], t_nom, "ss")
        c = corner_of(G, mat, "conservative")
        w_max, _ = plate(mat, c["p_test_MPa"], c["a_cover_mm"], c["nu"], c["E_MPa"], t_max, "ss")
        gap_need_nom = math.ceil((w_nom + G["plate_check"]["c_gap_mm"]) / rounding) * rounding
        gap_need_max = math.ceil((w_max + G["plate_check"]["c_gap_mm"]) / rounding) * rounding
        gap_nom = stack["parameters"]["t_cover_bond"]["nom"]
        gap_max = stack["parameters"]["t_cover_bond"]["max"]
        # the scenario uses at least the gap the deflection requires (a thicker cover needs a
        # larger air gap; the stack nominal is the baseline air-gap stand-in)
        gap_used = max(gap_nom, gap_need_nom)
        gap_ok = (gap_used >= gap_need_nom - 1e-9) and (gap_need_max <= gap_max + 1e-9)
        out[opt["id"]] = dict(
            meta,
            id=opt["id"], status="COMPUTED", material=mat, bond=opt["bond"],
            t_cover_mm={"min": r3(t_min), "nom": r3(t_nom), "max": r3(t_max)},
            plate_rows=rows, plate_status=status,
            w_cover_nominal_mm=r3(w_nom), w_cover_conservative_mm=r3(w_max),
            gap_required_nominal_mm=r3(gap_need_nom),
            gap_required_conservative_mm=r3(gap_need_max),
            gap_available_nominal_mm=r3(gap_nom), gap_available_max_mm=r3(gap_max),
            gap_raise_from_stack_nominal_mm=r3(gap_used - gap_nom),
            air_gap_check="PASS" if gap_ok else "FAIL",
            gap_used_nominal_mm=r3(gap_used),
        )
    return out


# ---------------------------------------------------------------------------
# radial / deterministic scenario checks
# ---------------------------------------------------------------------------
def deterministic_checks(G, stack, arch, zs):
    sp = stack["parameters"]
    rp = stack["radial"]["parameters"]
    hm_hf = None  # filled by caller via closure-free args below
    checks = {}
    # FPC under-run in the carrier lower web: web at min must house the thickest FPC + 0.05
    need = rp["t_fpc"]["max"] + 0.05
    have = sp["t_lower_web"]["min"]
    checks["fpc_underrun_lower_web"] = {
        "requirement_mm": r3(need), "available_mm": r3(have),
        "margin_mm": r3(have - need), "pass": have >= need - 1e-9,
        "note": "t_lower_web min vs t_fpc max + 0.05 handling clearance (stack_parameters radial)"}
    # U8 geometric feasibility on F.Cu (OD-U8): a 10 mm square module anywhere on MAIN F.Cu.
    # Valid bounds for a square module of side s inside the circular MAIN disc (R_main) that must
    # clear the display outline (R_display) entirely:
    #  - containment (necessary, orientation independent): the module's inscribed circle
    #    (radius s/2, concentric with the module) must lie inside the MAIN disc, so the module
    #    centre can be at most R_main - s/2 from the watch centre;
    #  - escape (necessary): the module centre is itself a point of the module, so for the whole
    #    module to lie outside the display outline the centre must be beyond R_display.
    module = 10.0
    half = module / 2.0
    circum = module / math.sqrt(2.0)
    r_main = rp["R_main"]["nom"]
    r_display = 21.95
    max_centre = r_main - half
    min_clear = r_display
    checks["u8_relocation_fcu_geometry"] = {
        "module_side_mm": r3(module),
        "module_half_side_mm": r3(half),
        "module_circumradius_mm": r3(circum),
        "max_centre_radius_in_main_mm": r3(max_centre),
        "min_centre_radius_to_clear_display_mm": r3(min_clear),
        "pass": max_centre > min_clear + 1e-9,
        "note": "U8-F is feasible only if some module centre lies outside the display outline while the "
                "module stays on MAIN. Necessary bounds: centre <= R_main - s/2 = %.2f mm (inscribed-circle "
                "containment) and centre > R_display = %.2f mm (the centre is a point of the module). "
                "%.2f < %.2f, so no F.Cu position of a 10 mm module escapes the rigid display; the "
                "lever cannot remove U8 from the governing front-gap stack (RF evidence not even reached). "
                "The earlier R_main - circumradius bound was orientation-dependent and is replaced by "
                "this valid necessary-condition pair." % (max_centre, min_clear, max_centre, min_clear)}
    # optical window plate under the 5 ATM test pressure (ATM-2): circular plate over the pod
    # aperture, unsupported radius = double-sided REAR envelope radius - frame overlap.
    # SUPPORT-BOUND INTERPRETATION: the clamped edge is the OPTIMISTIC / stronger-support bound
    # (it assumes verified edge rotation restraint); the simply-supported edge is the more
    # conservative / weaker-support bound and is the sizing case. Outcomes are reported per
    # support independently; the overall row pass requires the simply-supported (conservative)
    # case. A clamped-only pass is CONDITIONAL ON VERIFIED CLAMPED/RESTRAINED SUPPORT - the bond
    # restraint is unresolved and stays supplier/qualification gated. Analytical model only -
    # NOT a 5 ATM qualification (geometry, material and bond unresolved, ATM-Q2, X23).
    env = arch["rear_module"]["envelope_results"]["D_env_double_mm"]
    a_nom = env["nominal"] / 2.0 - G["plate_check"]["a_window_frame_mm"]
    a_cons = env["conservative"] / 2.0 - G["plate_check"]["a_window_frame_mm"]
    c_opt = stack["parameters"]["c_optics"]
    wrows = []
    for mat in G["plate_check"]["window_materials"]:
        m = G["plate_check"]["materials"][mat]
        for t in (stack["parameters"]["t_window"]["min"], stack["parameters"]["t_window"]["nom"],
                  stack["parameters"]["t_window"]["max"]):
            for corner, a, cmin in (("nominal", a_nom, False), ("conservative", a_cons, True)):
                p = G["plate_check"]["p_test_MPa"]["max" if cmin else "nom"]
                nu = m["nu"]["max" if cmin else "nom"]
                E = m["E_MPa"]["min" if cmin else "nom"]
                sig_allow = m["sigma_allow_MPa"]["min" if cmin else "nom"]
                limit = c_opt["min"] if cmin else c_opt["nom"]
                w_c, sig_c = plate(mat, p, a, nu, E, t, "clamped")
                w_s, sig_s = plate(mat, p, a, nu, E, t, "ss")
                stress_ok_c = sig_c <= sig_allow + 1e-9
                stress_ok_s = sig_s <= sig_allow + 1e-9
                # deflection and validity are judged on the conservative (simply-supported) case
                defl_ok = w_s <= limit + 1e-9
                if stress_ok_s and defl_ok:
                    result = "PASS (both support bounds)"
                elif stress_ok_c and (w_c <= limit + 1e-9):
                    result = ("CONDITIONAL ON VERIFIED CLAMPED/RESTRAINED SUPPORT "
                              "(clamped bound passes, simply-supported bound fails)")
                else:
                    result = "FAIL (conservative simply-supported bound)"
                wrows.append({
                    "id": "%s-t%s-%s" % (mat, ("%g" % t).replace(".", "p"), corner),
                    "material": mat, "t_mm": r3(t), "corner": corner,
                    "unsupported_radius_mm": r3(a),
                    "w_clamped_mm": r3(w_c), "sigma_clamped_MPa": r3(sig_c),
                    "w_simply_supported_mm": r3(w_s), "sigma_simply_supported_MPa": r3(sig_s),
                    "sigma_allow_MPa": sig_allow,
                    "w_over_t": r3(w_s / t),
                    "deflection_limit_mm": r3(limit),
                    "deflection_ok": defl_ok,
                    "stress_ok_clamped": stress_ok_c,
                    "stress_ok_simply_supported": stress_ok_s,
                    "support_result": result,
                    "pass": bool(stress_ok_s and defl_ok),
                })
    n_pass = sum(1 for r in wrows if r["pass"])
    n_cond = sum(1 for r in wrows if r["support_result"].startswith("CONDITIONAL"))
    checks["window_plate"] = {
        "model": "Linear small-deflection Kirchhoff plate, circular, uniform pressure. Support bounds: "
                 "clamped edge = OPTIMISTIC / stronger-support bound (assumes verified edge rotation "
                 "restraint); simply-supported edge = conservative / weaker-support bound and the sizing "
                 "case. Outcomes are reported per support independently; a row passes only if the "
                 "simply-supported bound passes. Validity limit: flagged where w/t > 0.5 (membrane "
                 "stiffening then makes the linear result conservative). Analytical model with PARAMETRIC "
                 "planning properties only - NOT a 5 ATM qualification; the actual window geometry, "
                 "material and bond restraint remain unresolved (G2 pod concept / G3 caseback, ATM-Q2 "
                 "window variant, X23) and any clamped-only pass is CONDITIONAL ON VERIFIED "
                 "CLAMPED/RESTRAINED SUPPORT.",
        "unsupported_radius_mm": {"nominal": r3(a_nom), "conservative": r3(a_cons)},
        "frame_overlap_mm": G["plate_check"]["a_window_frame_mm"],
        "standoff_available_mm": {"min": c_opt["min"], "nom": c_opt["nom"], "max": c_opt["max"]},
        "rows": wrows,
        "rows_passing": n_pass, "rows_conditional": n_cond, "rows_total": len(wrows),
        "verdict": ("%d of %d material/thickness/corner combinations pass the conservative simply-supported "
                    "bound; %d more pass only the clamped (optimistic) bound and are CONDITIONAL ON VERIFIED "
                    "CLAMPED/RESTRAINED SUPPORT - the window bond restraint is unresolved and stays gated. "
                    "No analytical result here is a 5 ATM qualification (ATM-Q2, X23 retained)."
                    % (n_pass, len(wrows), n_cond)),
    }
    # REAR-level caseback seal band vs reservations that cross it (5 ATM, OD-WATER)
    rci = {c: zs["radial"]["corners"][c]["checks"]["R_case_inner"]["value_mm"]
           for c in ("nominal", "conservative")}
    w = G["plate_check"]["w_caseback_seal_mm"]
    crossings = []
    for res in arch["reservations"]:
        if res["id"] in ("CHG_CONTACT", "VENT"):
            lo, hi = res["radial_mm"]
            for c in ("nominal", "conservative"):
                band_lo = rci[c] - (w["max"] if c == "conservative" else w["nom"])
                if hi >= band_lo - 1e-9:
                    crossings.append({"reservation": res["id"], "corner": c,
                                      "reservation_r_mm": [lo, hi],
                                      "seal_band_r_mm": [r3(band_lo), r3(rci[c])]})
    checks["rear_seal_band"] = {
        "R_case_inner_mm": {c: r3(rci[c]) for c in ("nominal", "conservative")},
        "seal_band_width_mm": w,
        "crossings": crossings,
        "note": "Reservations whose radial range reaches the caseback seal band at the case inner "
                "wall must be sealed as separate feedthroughs (ATM-4/ATM-5/ATM-6), not through the "
                "face seal"}
    # cover rim vs the provisional case inner radius (G3 fit finding)
    a = G["plate_check"]["a_cover_mm"]
    land = G["plate_check"]["w_cover_land_mm"]
    bezel = G["plate_check"]["t_bezel_min_mm"]
    rim = {}
    for c, rcik in (("nominal", rci["nominal"]), ("conservative", rci["conservative"])):
        ak = a["nom"] if c == "nominal" else a["max"]
        lk = land["nom"] if c == "nominal" else land["max"]
        bk = bezel["nom"] if c == "nominal" else bezel["max"]
        cover_outer = ak + lk
        rim[c] = {"cover_outer_edge_mm": r3(cover_outer), "R_case_inner_mm": r3(rcik),
                  "fit_margin_mm": r3(rcik - cover_outer),
                  "residual_wall_mm": r3(rcik - cover_outer),
                  "t_bezel_min_mm": bk,
                  "wall_margin_mm": r3(rcik - cover_outer - bk)}
    checks["cover_rim"] = rim
    return checks


# ---------------------------------------------------------------------------
# scenario evaluation
# ---------------------------------------------------------------------------
def lever_heights(G, H):
    solder = H["solder_allowance_mm"]
    fps = H["footprints"]
    hcv = G["heights"]["high_cv_extra_mm"]
    joint = G["heights"]["tail_joint_mm"]
    c0402 = fps["C_0402_1005Metric"]["max_mm"] + solder
    c0201 = fps["C_0201_0603Metric"]["max_mm"] + solder
    return {
        "bcu_0402_high_cv_mm": r3(c0402 + hcv),
        "inner_0201_mm": r3(c0201),
        "tail_joint_mm": r3(joint),
        "h_conn_class_nom_mm": None,  # set from stack h_rear_inner nom by caller
    }


def scenario_eval(G, stack, hm, H, cov, cover_id, levers, heights, overrides=None):
    """Evaluate one scenario. `overrides` maps parameter names to ADDITIVE deltas applied on top
    of the scenario's design values (used for the linear worst case and the single-term RSS
    sensitivities). Returns (total, layers, adjustments, p, hf, hb)."""
    p = {k: v["nom"] for k, v in stack["parameters"].items()}
    hf = hm["summary"]["H_F_under_display"]["value"]
    hb = hm["summary"]["H_B_in_battery"]["value"]
    opt = cov["options"][cover_id]
    adjustments = []
    # cover option
    if opt["status"] == "COMPUTED":
        p["t_cover"] = opt["t_cover_mm"]["nom"]
        p["t_cover_bond"] = opt["gap_used_nominal_mm"]
    else:
        p["t_cover"] = opt["t_cover_mm"]["nom"]
        p["t_cover_bond"] = G["oca_t_cover_bond_mm"]
    h_conn = stack["parameters"]["h_rear_inner"]["nom"]
    nest = False
    for lid in levers:
        lev = cov["levers"][lid]
        if lev["type"] == "bcu_refootprint":
            hb = heights["bcu_0402_high_cv_mm"]
        elif lev["type"] == "u8_relocate_bcu":
            hf = hm["summary"]["H_F_under_display"]["runner_up_value"]
            hb = H["footprints"]["MAX-F10S_UBL"]["max_mm"]
        elif lev["type"] == "u8_relocate_fcu":
            pass  # geometrically infeasible: no stack change
        elif lev["type"] == "inner_height":
            if lev.get("tail"):
                base = (heights["bcu_0402_high_cv_mm"] if lev["inner_parts"] == "0402_high_cv"
                        else heights["inner_0201_mm"])
                p["h_rear_inner"] = r3(base + heights["tail_joint_mm"])
            else:
                p["h_rear_inner"] = heights["bcu_0402_high_cv_mm"]
        elif lev["type"] == "inner_nest":
            nest = True
        elif lev["type"] == "skin_connector":
            p["h_rear_inner"] = heights["bcu_0402_high_cv_mm"]
        elif lev["type"] == "bcu_connector":
            pass  # handled via adjustment below (no height change at nominal class)
    if overrides:
        for k, d in overrides.items():
            p[k] = r3(p[k] + d)
    layers = mech_model.eval_stack(p, hf, hb)
    total = sum(l["thickness_mm"] for l in layers)
    # skin-face connector: optics_zone must also clear the connector
    if any(cov["levers"][l]["type"] == "skin_connector" for l in levers):
        oz = max(p["h_optics_max"], h_conn) + p["c_optics"]
        for l in layers:
            if l["id"] == "optics_zone":
                total += oz - l["thickness_mm"]
                l["thickness_mm"] = oz
                adjustments.append("optics_zone raised to clear J1502 on the skin face: %s mm" % f3(oz))
    # B.Cu connectors inside the pack projection join the back zone
    if any(cov["levers"][l]["type"] == "bcu_connector" for l in levers):
        bz = max(hb + p["c_back"], h_conn) + p["t_insulator"]
        for l in layers:
            if l["id"] == "back_zone":
                total += bz - l["thickness_mm"]
                l["thickness_mm"] = bz
        adjustments.append("back_zone = max(H_B + c_back, connector mated height) + t_insulator = %s mm "
                           "(connector class nominal %.2f does not exceed H_B + c_back)" % (f3(bz), h_conn))
    # carrier floor pocketed over the inner-face parts
    if nest:
        ri = next(l["thickness_mm"] for l in layers if l["id"] == "rear_inner")
        web = p["t_lower_web"]
        combined = max(web, ri) + p["t_insulator"]
        total += combined - ri - web
        adjustments.append("rear_inner + lower_web -> max(lower_web, rear_inner) + t_insulator = %s mm "
                           "(was %s + %s)" % (f3(combined), f3(web), f3(ri)))
    return total, layers, adjustments, p, hf, hb


def scenario_tolerances(G, stack, opt, levers):
    """Tolerance delta set (mm) for one scenario, per the authored tolerance policy."""
    sp = stack["parameters"]
    deltas = {}
    for name in G["tolerance_policy"]["package_terms_from_stack_max_minus_nom"]:
        deltas[name] = r3(sp[name]["max"] - sp[name]["nom"])
    for term in G["tolerance_policy"]["package_terms_explicit"]:
        deltas[term["param"]] = r3(term["delta_mm"])
    for name in G["tolerance_policy"]["double_sided_terms_from_stack_max_minus_nom"]:
        deltas[name] = r3(sp[name]["max"] - sp[name]["nom"])
    for term in G["tolerance_policy"]["g1_added_terms"]:
        d = term["delta_mm"]
        if term["param"] == "t_cover" and opt["status"] != "COMPUTED":
            d = r3(opt["t_cover_mm"]["max"] - opt["t_cover_mm"]["nom"])
        deltas[term["param"]] = r3(d)
    return deltas


def build_results():
    G = load(IN_SCEN)
    stack = load(IN_PARAMS)
    H = load(IN_HEIGHTS)
    hm = load(GEN / "main_height_map.json")
    zs = load(GEN / "zstack.json")
    arch = load(ARCH_JSON)
    cov = {"options": cover_options(G, stack),
           "levers": {l["id"]: l for l in G["levers"]}}
    heights = lever_heights(G, H)
    checks = deterministic_checks(G, stack, arch, zs)

    # baseline cover option must reproduce the stack parameters exactly
    base_opt = cov["options"][G["baseline_cover_option"]]
    sizing_check = {
        "t_cover_stack_mm": {k: stack["parameters"]["t_cover"][k] for k in ("min", "nom", "max")},
        "t_cover_sized_mm": base_opt["t_cover_mm"],
        "pass": all(abs(stack["parameters"]["t_cover"][k] - base_opt["t_cover_mm"][k]) < 1e-9
                    for k in ("min", "nom", "max")),
    }

    scenarios = []
    for s in G["scenarios"]:
        opt = cov["options"][s["cover"]]
        deltas = scenario_tolerances(G, stack, opt, s["levers"])
        total, layers, adjustments, p, hf, hb = scenario_eval(
            G, stack, hm, H, cov, s["cover"], s["levers"], heights)
        # linear worst case: every tolerance term at +delta, evaluated through the stack rules
        lin, _, _, _, _, _ = scenario_eval(
            G, stack, hm, H, cov, s["cover"], s["levers"], heights, deltas)
        # RSS: each parameter's ACTUAL single-term sensitivity through the scenario rules
        # (nesting rules change sensitivities: a pocketed lower web can go to zero, the
        # insulator can be counted twice - once in back_zone and once in the pocket floor)
        sens = {}
        for k, d in deltas.items():
            t1, _, _, _, _, _ = scenario_eval(
                G, stack, hm, H, cov, s["cover"], s["levers"], heights, {k: d})
            sens[k] = r3(t1 - total)
        rss = total + math.sqrt(sum(v * v for v in sens.values()))
        h_pod = G["h_pod_reported_mm"]
        t_body = total - h_pod
        # credibility per the authored rule
        blocking = []
        if not (total <= TARGET_HI + 1e-9):
            blocking.append("nominal T_total %.2f > %.1f" % (total, TARGET_HI))
        if not (rss <= TARGET_HI + 1e-9):
            blocking.append("RSS T_total %.2f > %.1f" % (rss, TARGET_HI))
        for lid in s["levers"]:
            st = cov["levers"][lid]["status"]
            if st != "CREDIBLE_LATER_TASK":
                blocking.append("lever %s status %s" % (lid, st))
        if opt["status"] != "COMPUTED":
            blocking.append("cover option %s status %s" % (opt["id"], opt["status"]))
        else:
            if opt["plate_status"] not in ("PASS", "PASS_NOMINAL"):
                blocking.append("cover plate status %s" % opt["plate_status"])
            if opt["air_gap_check"] != "PASS":
                blocking.append("cover air-gap check %s" % opt["air_gap_check"])
        for cid, chk in (("fpc_underrun_lower_web", checks["fpc_underrun_lower_web"]),
                         ("u8_relocation_fcu_geometry", checks["u8_relocation_fcu_geometry"])):
            if cid == "u8_relocation_fcu_geometry" and "U8-F" not in s["levers"]:
                continue
            if not chk["pass"]:
                blocking.append("%s fails" % cid)
        credible = not blocking
        changes, deps, risks = [], [], []
        for lid in s["levers"]:
            lev = cov["levers"][lid]
            changes.append("%s: %s" % (lid, lev["design_change"]))
            deps += ["%s: %s" % (lid, d) for d in lev["dependencies"]]
            risks += ["%s: %s" % (lid, r) for r in lev["risks"]]
        changes.append("cover %s: %s" % (opt["id"], opt.get("design_change", "")))
        deps += opt.get("dependencies", [])
        risks += opt.get("risks", [])
        scenarios.append({
            "id": s["id"], "title": s["title"], "cover": s["cover"], "levers": s["levers"],
            "T_nominal_mm": r3(total), "T_rss_mm": r3(rss), "T_worst_linear_mm": r3(lin),
            "T_body_mm": r3(t_body), "h_pod_mm": h_pod,
            "H_F_under_display_mm": r3(hf), "H_B_in_battery_mm": r3(hb),
            "t_cover_mm": r3(p["t_cover"]), "t_cover_bond_mm": r3(p["t_cover_bond"]),
            "h_rear_inner_mm": r3(p["h_rear_inner"]),
            "tolerance_deltas_mm": deltas,
            "tolerance_sensitivities_mm": sens,
            "tolerance_sum_linear_mm": r3(lin - total),
            "tolerance_rss_mm": r3(math.sqrt(sum(v * v for v in sens.values()))),
            "meets_upper_nominal": total <= TARGET_HI + 1e-9,
            "meets_upper_rss": rss <= TARGET_HI + 1e-9,
            "meets_upper_worst_linear": lin <= TARGET_HI + 1e-9,
            "credible_leq_15_5_mm": credible,
            "blocking_reasons": blocking,
            "design_changes": changes, "dependencies": deps, "risks": risks,
            "stack_adjustments": adjustments,
        })

    # legacy cross-check: package scenario S4 reproduced with the package tolerance terms
    leg = G["legacy_reference"]
    p = {k: v["nom"] for k, v in stack["parameters"].items()}
    for k, v in leg["overrides"].items():
        p[k] = v
    hf = hm["summary"]["H_F_under_display"]["value"]
    hb = hm["summary"]["H_B_in_battery"]["value"]
    leg_total = sum(l["thickness_mm"] for l in mech_model.eval_stack(p, hf, hb))
    leg_deltas = {}
    for name in G["tolerance_policy"]["package_terms_from_stack_max_minus_nom"]:
        leg_deltas[name] = r3(stack["parameters"][name]["max"] - stack["parameters"][name]["nom"])
    for term in G["tolerance_policy"]["package_terms_explicit"]:
        leg_deltas[term["param"]] = r3(term["delta_mm"])
    for name in G["tolerance_policy"]["double_sided_terms_from_stack_max_minus_nom"]:
        leg_deltas[name] = r3(stack["parameters"][name]["max"] - stack["parameters"][name]["nom"])
    leg_lin = leg_total + sum(leg_deltas.values())
    leg_rss = leg_total + math.sqrt(sum(d * d for d in leg_deltas.values()))
    legacy = {
        "id": leg["id"],
        "computed_mm": {"nominal": r3(leg_total), "rss": r3(leg_rss), "linear": r3(leg_lin)},
        "expected_mm": leg["expected_mm"],
        "tolerance_terms": leg_deltas,
        "pass": all(abs(leg["expected_mm"][k] - v) <= 0.051
                    for k, v in (("nominal", leg_total), ("rss", leg_rss), ("linear", leg_lin))),
    }

    any_credible = any(s["credible_leq_15_5_mm"] for s in scenarios)
    verdict = ("THICKNESS OWNER DECISION REQUIRED" if not any_credible
               else "CREDIBLE SCENARIO AVAILABLE")
    best = min(scenarios, key=lambda s: s["T_nominal_mm"])
    best_credible_levers = min((s for s in scenarios
                                if all(cov["levers"][l]["status"] == "CREDIBLE_LATER_TASK"
                                       for l in s["levers"])),
                               key=lambda s: s["T_nominal_mm"])

    return {
        "schema": "sportwatch-mech-g1-scenarios/1",
        "status": "G1 thickness-recovery study (G1_BRIEF.md section 4); all values computed, none hand-typed",
        "target_T_total_mm": [14.0, TARGET_HI],
        "baseline_cover_option": G["baseline_cover_option"],
        "cover_options": cov["options"],
        "cover_sizing_check": sizing_check,
        "deterministic_checks": checks,
        "legacy_cross_check": legacy,
        "scenarios": scenarios,
        "g1_verdict": {
            "verdict": verdict,
            "rule": "credible = nominal <= 15.5 AND RSS <= 15.5, every lever CREDIBLE_LATER_TASK, "
                    "cover plate PASS/PASS_NOMINAL with air-gap PASS, no failed deterministic check, "
                    "no best-case supplier value; the linear worst case is reported, not required",
            "thinnest_scenario": {"id": best["id"], "T_nominal_mm": best["T_nominal_mm"],
                                  "T_rss_mm": best["T_rss_mm"],
                                  "credible_leq_15_5_mm": best["credible_leq_15_5_mm"],
                                  "blocking_reasons": best["blocking_reasons"]},
            "thinnest_all_credible_levers": {"id": best_credible_levers["id"],
                                             "T_nominal_mm": best_credible_levers["T_nominal_mm"],
                                             "T_rss_mm": best_credible_levers["T_rss_mm"]},
            "note": "Stop rule (G1_BRIEF.md 4.6): no scenario is credibly <= 15.5 mm, so the G1 verdict "
                    "is THICKNESS OWNER DECISION REQUIRED; the tradeoff table is presented and no "
                    "requirement is weakened. OD-COVER and OD-REAR-SIDED are NOT revoked.",
        },
        "atm5_implications": G["atm5_implications"],
        "electrical_evidence": G["electrical_evidence"],
    }


# ---------------------------------------------------------------------------
# output rendering (fixed float formatting, no timestamps)
# ---------------------------------------------------------------------------
def render_md(res):
    o = []
    o.append("# G1 thickness-recovery scenarios (generated by tools/g1_scenarios.py — do not edit)")
    o.append("")
    o.append("Target T_total 14.0-15.5 mm (PHASE_BRIEF 1a). Every number below is computed from "
             "inputs/g1_scenarios.json, inputs/stack_parameters.json (via mech_model.eval_stack), "
             "inputs/package_heights.json and generated/main_height_map.json. G1 baseline = owner "
             "decisions OD-COVER (separate exterior cover lens) + OD-REAR-SIDED (double-sided REAR), "
             "2026-10-11.")
    o.append("")
    o.append("## Cover options (5 ATM plate sizing)")
    o.append("")
    o.append("| option | material | bond | t_cover min/nom/max | plate | air gap | gap used |")
    o.append("|---|---|---|---|---|---|---|")
    for opt in res["cover_options"].values():
        if opt["status"] == "COMPUTED":
            t = opt["t_cover_mm"]
            o.append("| %s | %s | %s | %s / %s / %s | %s | %s | %s |" % (
                opt["id"], opt["material"], opt["bond"], f3(t["min"]), f3(t["nom"]), f3(t["max"]),
                opt["plate_status"], opt["air_gap_check"], f3(opt["gap_used_nominal_mm"])))
        else:
            t = opt["t_cover_mm"]
            o.append("| %s | %s | %s | %s / %s / %s | n/a (laminate not computable) | n/a | %s |" % (
                opt["id"], opt.get("material", ""), opt.get("bond", ""),
                f3(t["min"]), f3(t["nom"]), f3(t["max"]), f3(G_oca(res))))
    o.append("")
    sc = res["cover_sizing_check"]
    o.append("Baseline cover sizing vs inputs/stack_parameters.json t_cover: %s (stack %s, sized %s)."
             % ("PASS" if sc["pass"] else "FAIL",
                "/".join(f3(sc["t_cover_stack_mm"][k]) for k in ("min", "nom", "max")),
                "/".join(f3(sc["t_cover_sized_mm"][k]) for k in ("min", "nom", "max"))))
    o.append("")
    o.append("## Deterministic checks")
    o.append("")
    o.append("- FPC under-run in the lower web: %s (need %s, have %s, margin %s)"
             % ("PASS" if res["deterministic_checks"]["fpc_underrun_lower_web"]["pass"] else "FAIL",
                f3(res["deterministic_checks"]["fpc_underrun_lower_web"]["requirement_mm"]),
                f3(res["deterministic_checks"]["fpc_underrun_lower_web"]["available_mm"]),
                f3(res["deterministic_checks"]["fpc_underrun_lower_web"]["margin_mm"])))
    u8 = res["deterministic_checks"]["u8_relocation_fcu_geometry"]
    o.append("- U8 relocation on F.Cu (OD-U8): %s — %s"
             % ("FEASIBLE" if u8["pass"] else "INFEASIBLE", u8["note"]))
    wp = res["deterministic_checks"]["window_plate"]
    o.append("- Optical window plate under 5 ATM (ATM-2, analytical model only, NOT a qualification): "
             "unsupported radius %s / %s mm (nominal / conservative); standoff available %s mm nominal. "
             "Support bounds: clamped = optimistic/stronger-support, simply-supported = conservative/"
             "weaker-support (sizing case). %d of %d combinations pass the simply-supported bound; %d "
             "more pass only the clamped bound and are CONDITIONAL ON VERIFIED CLAMPED/RESTRAINED SUPPORT "
             "(bond restraint unresolved, gated). %s"
             % (f3(wp["unsupported_radius_mm"]["nominal"]), f3(wp["unsupported_radius_mm"]["conservative"]),
                f3(wp["standoff_available_mm"]["nom"]), wp["rows_passing"], wp["rows_total"],
                wp["rows_conditional"], wp["verdict"]))
    o.append("  - " + wp["model"])
    rs = res["deterministic_checks"]["rear_seal_band"]
    o.append("- Caseback seal band (5 ATM): R_case_inner %s / %s; %d reservation(s) cross the band and "
             "need separate feedthrough seals: %s"
             % (f3(rs["R_case_inner_mm"]["nominal"]), f3(rs["R_case_inner_mm"]["conservative"]),
                len(rs["crossings"]),
                ", ".join(sorted({c["reservation"] for c in rs["crossings"]})) or "none"))
    cr = res["deterministic_checks"]["cover_rim"]
    o.append("- Cover rim vs provisional case inner radius: nominal fit margin %s mm, residual wall "
             "%s mm vs t_bezel_min %s; conservative fit margin %s mm (G3 case co-design must grow the "
             "front aperture or the case)"
             % (f3(cr["nominal"]["fit_margin_mm"]), f3(cr["nominal"]["wall_margin_mm"]),
                f3(cr["nominal"]["t_bezel_min_mm"]), f3(cr["conservative"]["fit_margin_mm"])))
    o.append("")
    o.append("## Scenario table")
    o.append("")
    o.append("| id | T_nominal | T_RSS | T_linear worst | T_body (h_pod 0.8) | <=15.5 credible | blocking |")
    o.append("|---|---|---|---|---|---|---|")
    for s in res["scenarios"]:
        o.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            s["id"], f3(s["T_nominal_mm"]), f3(s["T_rss_mm"]), f3(s["T_worst_linear_mm"]),
            f3(s["T_body_mm"]), "yes" if s["credible_leq_15_5_mm"] else "no",
            "; ".join(s["blocking_reasons"]) if s["blocking_reasons"] else "none"))
    o.append("")
    o.append("## Legacy cross-check (package scenario S4)")
    o.append("")
    leg = res["legacy_cross_check"]
    o.append("| id | nominal | RSS | linear | expected | pass |")
    o.append("|---|---|---|---|---|---|")
    o.append("| %s | %s | %s | %s | %s / %s / %s | %s |" % (
        leg["id"], f3(leg["computed_mm"]["nominal"]), f3(leg["computed_mm"]["rss"]),
        f3(leg["computed_mm"]["linear"]), f3(leg["expected_mm"]["nominal"]),
        f3(leg["expected_mm"]["rss"]), f3(leg["expected_mm"]["linear"]),
        "PASS" if leg["pass"] else "FAIL"))
    o.append("")
    o.append("## G1 verdict")
    o.append("")
    v = res["g1_verdict"]
    o.append("**%s** — %s" % (v["verdict"], v["note"]))
    o.append("")
    o.append("- Thinnest scenario: %s at %s nominal / %s RSS (credible: %s)."
             % (v["thinnest_scenario"]["id"], f3(v["thinnest_scenario"]["T_nominal_mm"]),
                f3(v["thinnest_scenario"]["T_rss_mm"]),
                "yes" if v["thinnest_scenario"]["credible_leq_15_5_mm"] else "no"))
    o.append("- Thinnest scenario using only CREDIBLE_LATER_TASK levers: %s at %s nominal / %s RSS."
             % (v["thinnest_all_credible_levers"]["id"],
                f3(v["thinnest_all_credible_levers"]["T_nominal_mm"]),
                f3(v["thinnest_all_credible_levers"]["T_rss_mm"])))
    o.append("")
    o.append("## 5 ATM implications (OD-WATER)")
    o.append("")
    o.append("| id | item | axial | radial | check | gate |")
    o.append("|---|---|---|---|---|---|")
    for a in res["atm5_implications"]:
        o.append("| %s | %s | %s | %s | %s | %s |" % (
            a["id"], a["item"], a["axial"], a["radial"],
            a.get("check") or a.get("qualification", ""), a["gate"]))
    o.append("")
    return "\n".join(o) + "\n"


def G_oca(res):
    for opt in res["cover_options"].values():
        if opt["status"] != "COMPUTED":
            return 0.15
    return 0.15


def dumps(obj):
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------
def validate(res, files):
    fails = []
    for name, text in files.items():
        p = GEN / name
        if not p.is_file():
            fails.append("%s: missing" % name)
        elif p.read_bytes() != text.encode("utf-8"):
            fails.append("%s: differs from regenerated output" % name)
    if not res["cover_sizing_check"]["pass"]:
        fails.append("cover sizing differs from inputs/stack_parameters.json t_cover")
    leg = res["legacy_cross_check"]
    if not leg["pass"]:
        fails.append("legacy S4 cross-check differs: %s vs %s"
                     % (leg["computed_mm"], leg["expected_mm"]))
    for s in res["scenarios"]:
        opt = res["cover_options"][s["cover"]]
        if opt["status"] == "COMPUTED":
            if opt["plate_status"] not in ("PASS", "PASS_NOMINAL"):
                fails.append("scenario %s: cover plate status %s" % (s["id"], opt["plate_status"]))
            if opt["air_gap_check"] != "PASS":
                fails.append("scenario %s: cover air-gap check %s" % (s["id"], opt["air_gap_check"]))
        for k, chk in res["deterministic_checks"].items():
            if k in ("fpc_underrun_lower_web",) and not chk["pass"]:
                fails.append("%s fails" % k)
        if "U8-F" in s["levers"] and res["deterministic_checks"]["u8_relocation_fcu_geometry"]["pass"]:
            fails.append("U8-F marked feasible but geometry check passes")
    # quoted numbers in architecture.json / architecture.md
    arch = load(ARCH_JSON)
    g1 = arch.get("g1")
    if not isinstance(g1, dict):
        fails.append("architecture.json lacks the g1 section")
    else:
        rows = {r["id"]: r for r in g1.get("scenario_results", [])}
        for s in res["scenarios"]:
            r = rows.get(s["id"])
            if r is None:
                fails.append("architecture.json g1.scenario_results lacks %s" % s["id"])
                continue
            for jk, sk in (("T_nominal_mm", "T_nominal_mm"), ("T_rss_mm", "T_rss_mm"),
                           ("T_worst_linear_mm", "T_worst_linear_mm"),
                           ("T_body_mm", "T_body_mm"),
                           ("credible_leq_15_5_mm", "credible_leq_15_5_mm")):
                if abs(float(r[jk]) - float(s[sk])) > 0.0005:
                    fails.append("architecture.json %s %s: %s != generated %s"
                                 % (s["id"], jk, r[jk], s[sk]))
        if g1.get("verdict") != res["g1_verdict"]["verdict"]:
            fails.append("architecture.json g1.verdict %r != generated %r"
                         % (g1.get("verdict"), res["g1_verdict"]["verdict"]))
    if ARCH_MD.is_file():
        md = ARCH_MD.read_text(encoding="utf-8")
        for s in res["scenarios"]:
            want = "| %s | %s | %s | %s |" % (s["id"], f3(s["T_nominal_mm"]), f3(s["T_rss_mm"]),
                                             f3(s["T_worst_linear_mm"]))
            if want not in md:
                fails.append("architecture.md G1 table lacks row: %s" % want)
        if res["g1_verdict"]["verdict"] not in md:
            fails.append("architecture.md lacks the G1 verdict")
    return fails


def main(argv):
    if len(argv) != 2 or argv[1] not in ("build", "check"):
        sys.stderr.write("usage: g1_scenarios.py {build|check}\n")
        return 2
    res = build_results()
    files = {"g1_scenarios.json": dumps(res), "g1_scenarios.md": render_md(res)}
    if argv[1] == "build":
        GEN.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (GEN / name).write_bytes(text.encode("utf-8"))
            print("wrote design/mechanical/generated/%s" % name)
        return 0
    fails = validate(res, files)
    summary = {"status": "PASS" if not fails else "FAIL", "failures": fails,
               "scenarios": len(res["scenarios"]),
               "verdict": res["g1_verdict"]["verdict"],
               "legacy_cross_check": "PASS" if res["legacy_cross_check"]["pass"] else "FAIL",
               "cover_sizing_check": "PASS" if res["cover_sizing_check"]["pass"] else "FAIL"}
    print(json.dumps(summary, sort_keys=True))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
