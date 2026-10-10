# Phase brief — MULTI-BOARD MECHANICAL STACK + REAR SENSOR MODULE ARCHITECTURE (Rev-A)

Status: provisional, reversible architecture study. This brief is the scope contract for the
architecture package in `design/mechanical/`. It does not authorize KiCad edits, routing, outline
freeze, case CAD, connector/antenna selection, battery change or electrical partition change.

## 1. Objective

Define a reversible, evidence-backed mechanical architecture for the complete watch stack and the
rigid REAR sensor module, sufficient to enable (later, separately authorized) detailed REAR optical /
guarded-analog placement, case + final MAIN outline co-design, outline freeze and routing.
Exit means "architecture coherent, conflicts exposed, unknowns tracked", never "mechanics final".

## 1a. Owner confirmations (2026-10-10)

- **Thickness target:** 14–15.5 mm is the **total finished-watch thickness**, from the exterior
  display-glass surface to the deepest normal wrist-facing surface of the rear optical pod
  (`T_total` in `stack_parameters.json`). Track separately: case/body thickness excluding pod
  (`T_body`), pod protrusion beyond the surrounding caseback (`h_pod`), and `T_total`. Do not force
  the design into the target if stack, clearance, sealing, tolerance, battery or optical needs make
  it infeasible; report the parametric result honestly.
- **Missing supplier data is not available.** For each missing dimension: identify it, define a
  named parameter/range where useful, state what it affects, and state when it becomes a hard
  blocker. Never invent dimensions.
- **SFH4053B:** the datasheet is a source gap. Do not infer its mechanical/optical values from another
  LED. It may block final quantitative geometry involving that part only; treat it parametrically
  in the broader optical-module architecture.

## 2. Authoritative inputs (read these, cite them)

- `design/mechanical/inputs/input_register.json` — KNOWN / PARAMETRIC / SUPPLIER_DATA_REQUIRED facts,
  frozen invariants, coordinate convention.
- `design/mechanical/inputs/stack_parameters.json`, `package_heights.json`.
- `design/mechanical/generated/main_height_map.{md,json,svg}`, `zstack.{md,json}`,
  `zstack_section.svg` — deterministic outputs of `tools/mech_model.py` (re-run, never hand-edit).
- `design/interfaces/main_rear_interface.{md,json}`, `design/interfaces/charger_harness.{md,json}`.
- `design/placement/phase1_placement.json` (reservations, B.Cu list, cavities, shield polygon).
- Live boards (read-only): `sportwatch_revA.kicad_pcb`, `rear_sensor/rear_sensor_revA.kicad_pcb`,
  `rear_sensor/04_PPG.kicad_sch`, `rear_sensor/08_TEMPERATURE.kicad_sch`.

Never invent a supplier dimension. Where data is missing: name it, use a labelled parametric range,
state whether work can continue reversibly, and list the supplier/owner request.

## 3. Frozen — do not change or propose as a done deal

All `frozen_invariants` in the input register. In particular: raw PD_IN / PD_GND / VREF / LED
cathode / mux-select nets stay REAR-local; 24-position / 13-net sensor boundary; TPS631000 on MAIN;
no charger-positive in the sensor FPC; LPR454440; no watch-side permanent magnet; MAIN Ø46 is a
development envelope. Proposals that would need any of these changed must be written as an
**OWNER DECISION REQUIRED** item, not as the recommendation.

## 4. Required deliverables (files)

| File | Content |
|---|---|
| `design/mechanical/README.md` | Package index, status line, conventions, how to regenerate, list of files. |
| `design/mechanical/architecture.md` | The architecture document, sections A–J + 11–15 below. |
| `design/mechanical/architecture.json` | Machine-readable: perimeter/Z reservations, REAR envelope parameters, FPC/charger path parameters, assembly steps, conflicts, supplier requests, unfrozen items, owner decisions, next-gate recommendation. |
| `design/mechanical/tools/arch_diagrams.py` | Stdlib-only generator of the SVG diagrams below **from architecture.json + generated outputs**. Subcommand `build` writes the SVGs; `check` regenerates in memory, byte-compares, and runs the consistency checks in §6 without writing; exit 0 only on pass. Deterministic output (no timestamps, fixed float formatting). |
| `design/mechanical/generated/perimeter_map.svg` | Front-view clock/sector reservation map with Z-level legend (front / MAIN / battery / rear), MAIN Ø46, display Ø43.9, battery Ø44 nominal, case Ø50–51 band, all reservations and conflicts marked. |
| `design/mechanical/generated/rear_module_concept.svg` | REAR rigid-board envelope concept: top view (optical face, explicit board-to-assembly transform), and a section through pod/window/barriers/board/carrier/battery with labelled parametric dimensions. |
| `design/mechanical/generated/interconnect_paths.svg` | MAIN↔REAR FPC path and charger-contact harness path in plan view plus the south radial section. |

## 5. Required content (architecture.md)

Each section: KNOWN facts (cited), PARAMETRIC assumptions (range + confidence), SUPPLIER-DATA gaps,
the provisional concept, alternatives considered with reasons, risks, and what it unblocks.

- **A. Z-stack** — from cover to wrist using the `zstack` output; the target applies to T_total; also
  report T_body and h_pod; governing layers; RSS vs linear; what must change to meet 14.0 and 15.5,
  and an honest feasibility verdict. Do not hand-compute numbers that the tool produces; quote them.
- **B. MAIN height-risk map** — F.Cu heights under the display (governing parts), B.Cu population and
  battery-overlap risk, shield-ready clearance, support regions, J1301/TP access.
- **C. Battery / carrier** — nominal cell vs finished pack; list every missing pack datum (PCM
  envelope/location, tabs, wire exit, tolerance, growth, insulation/tape, NTC, restraint/compression);
  carrier concept (web, pockets, walls, insulation, restraint, removal path); parametric dependency.
- **D. Rigid REAR board** — provisional envelope / outline class with a derivation (optical cluster +
  barriers + AFE/mux + MAX30208 island + J1502 + support land), orientation and transform, optical-side
  orientation, component-side strategy (single- vs double-sided trade), support / hard stops,
  screw-boss/support interaction, gasket interaction, relation to battery/carrier, FPC attach region.
- **E. Optical pod** — emitter/PD functional grouping consistent with the frozen membership, window
  and clear material options, black barriers through the full optical stack, crosstalk / internal
  reflection / ambient control, provisional emitter–detector spacing study as **ranges to be measured**
  (no copied spacing claimed optimal), pod/mesa concept, skin-contact geometry, sealing, hard stops
  protecting the optical stack from compression.
- **F. MAX30208 thermal path** — isolated tongue/island or equivalent, skin path, contamination
  sources (LEDs, AFEs, battery, MAIN, charging, case spreading), measurement scheduling; no partition
  change.
- **G. MAIN↔REAR FPC path** — the ~1 mm Ø46/Ø44 annulus is not a channel; use the radial outputs;
  connector region/orientation, route beside battery, carrier channel, fold geometry, bend radius,
  stiffener, strain relief, service loop, assembly order, battery-edge protection, GND/reference
  implications of 10 GND positions, VLED conductor width needs (3 positions, ~124 mA pulse plus
  recharge). 24 positions / 13 nets unchanged; MPN/pitch/orientation not frozen.
- **H. Charger contact module** — envelope at rear east ~3 o'clock, case mounting and force path,
  sealing/feedthrough, dedicated +5 V/GND path to MAIN J202 (note: J202 window is at MAIN **west**),
  routing around the REAR optical architecture, keying, cable-side pogo, nonmagnetic alignment.
- **I. Structural / perimeter reservations** — screws/bosses, MAIN supports, battery supports/hard
  stops, gasket lands, five buttons, LRA pocket, barometer vent, ALS aperture, GNSS/BLE/Wi-Fi radome
  volumes, J201/PCM/wire exit, sensor FPC corridor, charger module, tool and SWD access. Do not consume
  perimeter volume merely because PCB parts fit.
- **J. Assembly / service / SWD sequence** — first-boot SWD, display install, MAIN install/support,
  battery, FPC mating, REAR module, charger module, gasket/compression closure; development/rework
  access before final closure; re-mating cycle limits.
- **11.** Key dimensional assumptions table (value/range, class, confidence, source).
- **12.** Conflicts register (id, description, evidence, severity, options, recommended provisional
  direction, owner-decision flag).
- **13.** Unresolved blockers and supplier/owner data requests (who, what, which gate it blocks).
- **14.** Explicit list of what remains intentionally unfrozen.
- **15.** Recommendation for the next engineering gate, with entry criteria.

## 6. Deterministic consistency checks (`arch_diagrams.py check`)

At minimum: every `SUPPLIER_DATA_REQUIRED` register id appears in architecture.json supplier
requests; every conflict has severity, options and an owner_decision boolean; every reservation has
clock range, radial range, Z level(s) and class; overlapping reservations at the same Z level must be
listed as conflicts; no architecture.json value marked KNOWN lacks a source; the frozen-invariant list
is copied verbatim from the register; numbers quoted in architecture.json for the stack/radial
margins equal the `zstack.json` values.

## 7. Lead-identified candidate conflicts (evaluate with evidence; confirm, refine or refute)

1. **Front gap governed by U8 MAX-F10S (2.7 max)** under a rigid Ø43.9 display; next-tallest is far
   lower. Quantify the cost and the options (none may move frozen-foundation parts in this phase).
2. **Display-side connectors.** J1 (display), J1301 (SWD Tag-Connect, no-legs), TP1301–TP1306 and the
   planned J1501 (sensor FPC) and J201 (battery) windows are all on MAIN **F.Cu, which faces the
   display**. Determine which assembly orders keep each one matable/accessible, the service-loop and
   edge-wrap consequences, and whether a relocation (later placement phase) or outline feature (later
   co-design phase) is required.
3. **Edge-wrap radial conflict.** An FPC from an F.Cu connector at r≈21 wrapping around the Ø46 edge
   versus case inner radius (see radial margins).
4. **Charger path.** Contacts at rear east; MAIN entry J202 window at west near the PMIC; the harness
   must avoid the optical region, antennas and the BMM350 (NE) sector.
5. **South-sector crowding.** J1501, J201, J1301, battery wire exit (SW), LRA pocket (5:30–6:30),
   supports SW/SE, Wi-Fi (SE) and the charger path.
6. **Display FPC fold** extends up to 0.7 mm beyond the 43.9 outline; check against case radius and
   the west button/J1 corridor.
7. **Wi-Fi reservation** extends beyond the Ø46 board (x up to 124) — it is a case/radome volume.
8. **GNSS radiator reservation is already occupied** by F.Cu parts C1420, C1421, R1420 (see height
   map reservation table); classify whether they are part of the GNSS feed network or an intrusion.
9. **Thick-corner interpretation.** The linear `thick` corner mixes *design-choice* variables
   (`h_rear_inner` single- vs double-sided REAR, `t_front_extra` cover strategy, window thickness)
   with *tolerance/supplier* variables. Present scenario-based totals (design choices fixed per
   scenario, tolerances stacked) using only tool outputs and simple, shown arithmetic on them, and
   state which scenarios can meet 15.5 mm.

## 8. Rules

- Label every number KNOWN / PARAMETRIC / SUPPLIER_DATA_REQUIRED with source. No false precision.
- Optical/thermal performance claims require later prototype measurement; say so.
- Do not modify inputs, KiCad files, interfaces, placement data or `tools/mech_model.py`.
- Diagrams must be generated by `tools/arch_diagrams.py`; no hand-written SVG.
