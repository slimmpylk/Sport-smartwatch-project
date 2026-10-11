# G1 brief — MECHANICAL ARCHITECTURE: OWNER-DECISION INTEGRATION (Rev-A)

Status: provisional, reversible architecture work. This brief is the scope contract for G1. It builds on the
independently reviewed architecture package at commit `4e80e9e4e943934acb860bdeeb9d36a5582ad43a`
(MULTI-BOARD MECHANICAL STACK + REAR SENSOR MODULE ARCHITECTURE: CLOSED / PASS) and on
[PHASE_BRIEF.md](PHASE_BRIEF.md), whose rules still apply except where this brief explicitly widens scope.

## 1. Objective

Integrate the owner decisions of section 2 into the mechanical inputs, tooling and architecture package;
recompute the stack deterministically; evaluate thickness-recovery scenarios; reassess the gated conflicts;
and turn the supplier requests into an issue-ready set. Exit is a G1 verdict, not a frozen design.

## 2. Owner decisions (authoritative, 2026-10-11)

- **OD-COVER:** a separate exterior cover lens/glass over the display, bonded/sealed as part of the case. The
  display module is not the exterior structural or water barrier. Cover material/thickness PARAMETRIC until the
  case/display integration study.
- **OD-REAR-SIDED:** DOUBLE-SIDED REAR PCB. Emitters, photodiodes and sensitive PPG/analog geometry stay on the
  skin-facing side (frozen architecture); mechanically and electrically appropriate connector/support/passive
  placement is allowed on the inner side.
- **OD-WATER:** 5 ATM / swim-capable sealing is the Rev-A mechanical design target. Sealing-stack design and
  pressure/leak qualification are future validation work.
- **OD-U8:** U8 may move if mechanical AND RF evidence supports it. Replacing the selected GNSS part/module needs
  separate electrical/RF justification and review (not part of G1).
- **OD-DEVACCESS:** SWD/test access is required during development, manufacturing and bring-up; external SWD access
  after final sealing is not required.
- **OD-J202:** the charger entry may move if the mechanical/interconnect study supports it; the frozen electrical
  charger architecture is preserved.
- **OD-CONN-SIDE:** J1501/J201 may move to the opposite PCB side only if stack, assembly and routing evidence supports
  it, not for convenience.

These answer the package's OD-COVER, OD-REAR-SIDED, OD-WATER, OD-U8, OD-DEVACCESS, OD-J202 and OD-CONN-SIDE items.
Record them in `inputs/input_register.json` as owner-decision entries with this date and source. Do not revoke or
reinterpret them; in particular do not revoke OD-COVER or OD-REAR-SIDED because a scenario is over target.

## 3. Scope

**May modify** (tracked files under `design/mechanical/` only): inputs/parameter files, `tools/mech_model.py`,
`tools/mech_model_spec.md`, `tools/arch_diagrams.py`, regenerated outputs in `generated/`, `architecture.md`,
`architecture.json`, `README.md`, and one new deterministic tool `tools/g1_scenarios.py` (see section 4).
Generated files are written only by the tools (never hand-edited) and must reproduce byte-identically.

**May not modify:** anything outside `design/mechanical/`; KiCad PCB/schematic files or geometry; frozen
electrical interfaces (`design/interfaces/**`); electrical architecture; Phase-1 placement ownership
(`design/placement/**`, protected foundation parts including U8); firmware; orchestration tooling; this brief and
`PHASE_BRIEF.md`. KiCad boards/schematics may be **read** for evidence (values, ratings, positions).

**Frozen invariants** (input register `frozen_invariants`) stay verbatim and untouched. Anything that would need
one of them changed is an OWNER DECISION REQUIRED item, never the recommendation.

**Never invent supplier dimensions.** Every value is KNOWN (cited), PARAMETRIC (labelled range with low / nominal /
high and a stated rationale) or SUPPLIER_DATA_REQUIRED. The nominal of a parametric range must not be its best case.

## 4. Thickness integration and recovery scenarios

Target: **T_total 14.0–15.5 mm finished-watch thickness** (definition in PHASE_BRIEF 1a). Starting point: package
scenario S4 (separate cover + double-sided REAR) = 15.85 nominal / 16.28 RSS / 17.23 linear worst (architecture.md A).

1. Integrate OD-COVER and OD-REAR-SIDED into the stack model as the baseline configuration (cover lens and its
   bond/seal layer as explicit parametric layers; double-sided REAR inner-side height as an explicit layer), so
   `mech_model.py stack` / `zstack.*` describe the G1 baseline rather than the old S1.
2. Add `tools/g1_scenarios.py` (stdlib only, deterministic, no timestamps, fixed float formatting) with `build`
   (writes `generated/g1_scenarios.json` and `generated/g1_scenarios.md`) and `check` (regenerates in memory,
   byte-compares, validates; exit 0 only on pass). It must compute every scenario from the inputs and the stack
   model, not from hand-typed totals, and `arch_diagrams.py check` (or `g1_scenarios.py check`) must fail if any
   scenario number quoted in `architecture.json` / `architecture.md` differs from the generated value.
3. Evaluate separately, at minimum:
   - **G1-S4 baseline** (integrated decisions, no levers);
   - **passive-height optimization:** C901/C903 (and any other governing B.Cu or inner-side part) at a lower package
     only where it is electrically valid (read capacitance, voltage rating and role from the schematic; account for
     DC-bias derating and available 0402 parts in principle, without inventing an MPN) and manufacturable; state the
     later electrical/placement task this would require (G1 does not change the schematic or footprints);
   - **U8 relocation** only where OD-U8 permits it: evaluate geometrically (display Ø43.9 footprint, MAIN Ø46, B.Cu
     battery projection, RF feed / antenna region) whether any relocation actually removes U8 from the governing
     front-gap stack; state the RF evidence needed; U8 placement itself is not changed in G1;
   - **cover-lens thickness / bond-stack ranges:** realistic parametric ranges for a 5 ATM-capable exterior cover
     (material class, thickness, bond/adhesive or gasket stack, optical air gap or optical bond), with the rationale
     and the supplier data that would close them;
   - **double-sided REAR inner-side height:** connector vs hot-bar / flex-tail termination and inner-side part-height
     cap as levers, with J1502/FPC dependencies (SR-FPC-MECH);
   - **combinations** of the above.
4. For each scenario report: nominal T_total, RSS and linear worst-case T_total (same tolerance terms as the
   package unless G1 adds terms, which must be listed), T_body and h_pod used, design changes required, dependencies
   (supplier data, owner decisions, later tasks), new risks, and whether **<= 15.5 mm is credible**.
5. "Credible" means without relying on best-case supplier dimensions and without violating battery clearance or
   growth allowance, 5 ATM sealing needs, optical geometry, FPC bend requirements, RF keep-outs/performance,
   structural support or assembly/service requirements. Low h_pod values that need wrist trials are not a lever by
   themselves.
6. **Stop rule:** if no scenario is credibly <= 15.5 mm, the G1 verdict is THICKNESS OWNER DECISION REQUIRED: present
   the tradeoff table and stop there. Do not weaken requirements to reach the target.

## 5. 5 ATM implications

Record the axial and radial consequences of the 5 ATM target (front cover seal, caseback seal, optical window,
button and charger feedthrough seals, vent membrane, gasket compression and land widths, caseback/window
stiffness under pressure). Where a simple deterministic check is possible (for example clamped-plate deflection of
the optical window or cover under the 5 ATM test pressure with labelled parametric material properties), add it
to a tool; otherwise list it as a qualification item with the gate that needs it.

## 6. Supplier requests

Update `architecture.json` `supplier_requests` and architecture.md section 13 into an issue-ready set:

- **SR-DISPLAY-LAND:** the display land is support/bond geometry, not the primary water seal (the cover lens seals).
- **SR-FPC-MECH:** the authorized double-sided REAR (J1502 face and mated height on the inner side, or a flex tail).
- **SR-CHG-MECH:** explicit 5 ATM feedthrough/sealing requirement.
- **SR-BUTTONS:** explicit 5 ATM sealing requirement.
- **New SR for the cover lens** (supplier/mechanical): material, thickness and tolerances, OD/geometry, edge
  treatment, bonding method, adhesive/seal stack, pressure/water-sealing constraints, optical requirements (display
  transmission, ALS aperture).
- Review every other SR for consistency with section 2; keep **SR-LRA** and **SR-ANTENNAS** gated pending
  supplier/component selection (no invented supplier). Each SR states who, what, why, the gate it blocks and the
  parametric stand-in used meanwhile.

## 7. Conflict reassessment

Reassess against the integrated decisions: C1-FRONT-GAP, C2-DISPLAY-SIDE-CONNECTORS, C4-CHARGER-PATH,
C9-THICK-CORNER, X11-POD-FOOTPRINT, X12-J1502-FACE, X13-EDGE-CROSSINGS, X21-INGRESS-UNDEFINED, X24-DISPLAY-LAND,
and the already gated C3-EDGE-WRAP, X10-OPTICS-HEIGHT-UNKNOWN, X23-WINDOW-CROSSTALK. Each ends G1 with exactly one
`g1_status`: **CLOSED** (deterministic evidence cited), **REMAINS_OPEN** (explicit dependency), **SUPPLIER_DATA_GATED**,
**OWNER_DECISION_GATED**, or **DEFERRED** (to an explicitly named later phase). Add any new conflict the integration
exposes. `arch_diagrams.py check` must enforce that every conflict carries a valid `g1_status` and its
evidence/dependency field.

## 8. Deliverables and validation

- Updated inputs, tools, generated outputs, `architecture.md` (new section **G1** with the decisions, the scenario
  table, the 5 ATM section, the conflict status table and the G1 verdict, plus consistent updates to A-J and 11-15),
  `architecture.json`, `README.md`.
- These commands must exit 0: `python3 design/mechanical/tools/mech_model.py check`,
  `python3 design/mechanical/tools/arch_diagrams.py check`, `python3 design/mechanical/tools/g1_scenarios.py check`.
- The existing structural guarantees stay in force (overlap detector and self-tests, numeric-leaf coverage).

## 9. Independent review must challenge

Thickness arithmetic and tolerance stacking; whether any <= 15.5 mm scenario relies on hidden optimistic
assumptions; 5 ATM implications; double-sided REAR feasibility; U8 relocation assumptions; cover-lens/seal
assumptions; supplier-request completeness; and whether any frozen electrical boundary was changed.

## 10. Not in G1

G2 (REAR optical + guarded-analog placement), G3 (case + final MAIN outline co-design), detailed optical placement,
case CAD, KiCad geometry, part selection, schematic or footprint changes.
