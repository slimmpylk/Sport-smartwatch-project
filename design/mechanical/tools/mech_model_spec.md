# mech_model.py specification

Implement ONE deterministic stdlib-only Python 3 tool design/mechanical/tools/mech_model.py and commit-ready generated outputs for the Sportwatch Rev-A mechanical-stack phase.

Inputs (read-only): design/mechanical/inputs/package_heights.json, design/mechanical/inputs/stack_parameters.json, design/mechanical/inputs/input_register.json, design/placement/phase1_placement.json (key 'reservations', 'shield_polygon_mm'), sportwatch_revA.kicad_pcb (MAIN), rear_sensor/rear_sensor_revA.kicad_pcb (REAR).

Parse KiCad S-expression text yourself (top-level '(footprint "lib:name"' blocks: reference property, layer F.Cu/B.Cu, (at x y [rot]), footprint name after the colon; courtyard bbox from F.CrtYd/B.CrtYd fp_line/fp_rect/fp_poly if present, rotated by footprint rotation, else null).

Subcommands:

(1) `heights`: join every MAIN and REAR footprint with package_heights.json by footprint name; seated_max = max_mm + solder_allowance_mm when class PARAMETRIC, = max_mm when KNOWN, null when max_mm is null (list as unknown). Compute r = hypot(x-100, y-100) for MAIN. Write design/mechanical/generated/main_height_map.json containing: per-footprint records (ref, side, x, y, rot, r, footprint, value, seated_max, height_class, courtyard_bbox), summaries: counts by side; F.Cu top-15 tallest; H_F_under_display = max seated F.Cu with r <= 21.95 plus governing ref and runner-up ref; H_B_in_battery = max seated B.Cu with r <= 22.0 plus ref; full B.Cu list with r and in_battery flag; unknown-height list; for each reservation rect in phase1_placement.json the list of MAIN footprints whose centre or courtyard bbox intersects it; access list for J1301 and TP* refs (side, xy, r); REAR: count, max known seated height, unknown-height refs. Also write main_height_map.md (concise tables) and main_height_map.svg (top/front view, 1 mm = 8 px, SVG y = PCB Y so north is up; draw Ø46 MAIN outline, Ø43.9 display outline, Ø44 battery nominal projection dashed, the reservation rects labelled, U101 shield polygon, each MAIN footprint as its courtyard bbox (or 1 mm square) filled by height band <0.5 / 0.5-1.0 / 1.0-2.0 / >=2.0 / unknown with a legend, B.Cu parts drawn hatched or outlined distinctly, label parts >=1.0 mm and J1301/TP*; include a north arrow and the text 'front view from display; north = -Y').

(2) `stack`: implement exactly the rules, z_layers, conventions, corners, RSS and radial checks/corner_rule written in stack_parameters.json, using H_F_under_display and H_B_in_battery from the height map. Report per corner every z-layer thickness with its governing term, T_total, and T_body for each h_pod sweep value {0.0,0.5,0.8,1.0,1.5} (h_pod is a sweep, not a corner variable: T_body = T_total - h_pod), margin to 14.0 and 15.5 for both T_body and T_total, the RSS value, the three largest contributors to (thick - nominal), and every radial check at nominal / conservative / optimistic corners with pass/fail sign. Write generated/zstack.json, generated/zstack.md and generated/zstack_section.svg (left: centre-station cross-section as stacked labelled bars at nominal with thickness annotations, front at top; right: south radial section sketch showing R_main, R_pack_max, carrier wall, FPC straight-run channel, edge-wrap requirement and R_case_inner at nominal with margins printed).

(3) `check`: regenerate all outputs in memory and byte-compare with the files in design/mechanical/generated/; also assert MAIN footprints == 184 (F.Cu 167, B.Cu 17), REAR == 44, every MAIN/REAR footprint name exists in package_heights.json, every stack/radial parameter has min <= nom <= max and class in {KNOWN, PARAMETRIC, SUPPLIER_DATA_REQUIRED}; print one JSON summary line and exit 0 only if all pass, else exit 1.

Determinism: sorted keys, floats rounded to 3 decimals, no timestamps, no absolute paths in outputs, LF endings, trailing newline.

Resolve repo root from the script location (parents[3]).

The tool must never write when run as `check`, and must never write outside design/mechanical/generated/.

Run `python3 design/mechanical/tools/mech_model.py heights`, then `stack`, then `check`, and report the key numbers (H_F_under_display + ref, H_B_in_battery + ref, T_total nominal/thick, all radial margins) in evidence.
