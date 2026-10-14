# design/mechanical - Rev-A multi-board mechanical stack and rear sensor module architecture

**Status: G3 CONDITIONAL — SUPPLIER/MEASUREMENT GATES OPEN.** Recommended study candidate: **G3-B-S14**.
The corrected package exemption, both orthogonal VLED-entry orientations, physical pad/trace clearance,
ordered-loop checks and placement search are recorded in the generated report. All nominal hard checks
pass for the selected candidate; conservative-corner failures and evidence gates remain explicit.

**G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES** (OD-G3-RECORD). This records the accepted review
status without changing any immutable G2 result or closing any supplier gate. G4 and KiCad edits remain
unauthorized. All G3 placements and reservations are reversible study evidence.

## Package index

| File | Content |
|---|---|
| `PHASE_BRIEF.md` | Scope contract (objectives, owner confirmations, deliverables, rules). Input; not edited by the architecture package. |
| `G1_BRIEF.md` | G1 scope contract: owner-decision integration, thickness-recovery scenarios, 5 ATM implications, supplier requests, conflict reassessment. Input; not edited. |
| `architecture.md` | The architecture document: sections A-J and 11-15 plus the G1 section (decisions, scenario table, 5 ATM implications, conflict g1_status table, verdict). |
| `architecture.json` | Machine-readable architecture: reservations (clock, radial, Z, class), tool quotes, REAR envelope derivation, FPC/charger path parameters, edge-crossing model (display support land, bend start, three-corner radial budget of every F.Cu edge crossing), assembly steps, conflicts (each with a `g1_status`), supplier requests, owner decisions (answered 2026-10-11), the g1 section (scenario results, cover options, ATM checks, verdict), unfrozen items, next gate. |
| `tools/arch_diagrams.py` | Stdlib-only diagram generator and consistency checker (`build` / `check`); also enforces the conflict `g1_status` fields and the g1 scenario quotes against `generated/g1_scenarios.json`. |
| `generated/perimeter_map.svg` | Front-view clock/sector reservation map with Z-level legend, envelopes and conflict markers. |
| `generated/rear_module_concept.svg` | REAR envelope concept: wrist-side top view with the board-to-assembly transform, and a section through the pod with parametric dimensions. |
| `generated/interconnect_paths.svg` | MAIN-REAR FPC path and charger harness paths (incl. the west riser) in plan view plus the south radial section with the display land, the derived bend geometry and the edge-crossing budget. |
| `inputs/` | `input_register.json` (incl. the seven owner-decision entries of 2026-10-11), `package_heights.json`, `stack_parameters.json` (G1 baseline: cover + double-sided REAR layers), `g1_scenarios.json` (authored G1 scenario/levers/plate-check definitions). |
| `tools/mech_model.py`, `tools/mech_model_spec.md` | Deterministic height-map / Z-stack / radial model and its specification. |
| `tools/g1_scenarios.py` | Deterministic G1 thickness-recovery scenario tool (`build` / `check`): 5 ATM plate sizing of the cover, air-gap/rim/seal-band/FPC/U8 checks, 16 scenarios with nominal / RSS / linear worst totals and credibility verdicts, legacy S4 arithmetic cross-check. |
| `generated/main_height_map.*`, `generated/zstack.*`, `generated/zstack_section.svg` | Outputs of `mech_model.py` (quoted by the architecture package, never hand-edited). |
| `generated/g1_scenarios.json`, `generated/g1_scenarios.md` | Outputs of `g1_scenarios.py` (quoted by architecture.json / architecture.md section G1, never hand-edited). |

## Conventions

 - Front view from the display: north/12 = -Y, east/3 = +X, south/6 = +Y, west/9 = -X; MAIN origin (100,100). Azimuth = degrees clockwise from north.
 - Z positive from the front exterior toward the wrist. T_total = front-most exterior surface (cover lens) to the deepest wrist-facing pod surface (Rev-A owner limit: nominal ≤16.5 mm, RSS ≤17.0 mm; historical 14.0–15.5 mm is a non-binding production goal);
   T_body = T_total - h_pod. Reservation Z levels: FRONT, MAIN, BATTERY, REAR.
 - Every number is labelled KNOWN / PARAMETRIC / SUPPLIER_DATA_REQUIRED with a source. Missing supplier data is never invented; each gap is a request tied to
   a gate. Anything that would need a frozen invariant to change is an OWNER DECISION REQUIRED item.
 - REAR documents state their board-to-assembly transform explicitly; pin order is never read from a mirrored B-side view.

## How to regenerate and check

```
python3 design/mechanical/tools/mech_model.py heights   # only when inputs change
python3 design/mechanical/tools/mech_model.py stack
python3 design/mechanical/tools/mech_model.py check      # exit 0 only if tool outputs are current
python3 design/mechanical/tools/arch_diagrams.py build   # writes the three SVGs
python3 design/mechanical/tools/arch_diagrams.py check   # byte-compares SVGs and runs the consistency checks; never writes
python3 design/mechanical/tools/g1_scenarios.py build    # writes generated/g1_scenarios.{json,md}
python3 design/mechanical/tools/g1_scenarios.py check    # byte-compares and validates the G1 arithmetic + the quotes in architecture.json/.md
```

`arch_diagrams.py check` verifies, among others: source SHA-256 pins; frozen-invariant list identical to the register; **numeric-leaf coverage** - every
int/float in `architecture.json` is compared against its generated / register / placement / derived source (tool quotes with the complete expected key set,
geometry incl. case outer min/max/nominal, reservation geometry ties, every dimension D01-D43, scenario, lever, edge-crossing, REAR-envelope, support,
pack-edge and charger arithmetic, and every g1 scenario / cover / check number against `generated/g1_scenarios.json`) or is listed in the
`COVERAGE_EXEMPT` table of `arch_diagrams.py` with a reason (study placeholders, diagram anchors);
any other numeric leaf, or a stale exemption, fails the check, and a built-in self-test proves that an injected leaf or a mutated case radius is caught;
every reservation has clock range, radial range, Z level(s) and class; every overlapping reservation pair at a shared Z level - found by an exact analytic
strip-sweep detector (slivers, thin, coincident and contained shapes found; merely abutting boundaries excluded; built-in self-test cases fail the check if
the detector regresses) - is listed in a conflict; every conflict has severity, options, an owner-decision flag and exactly one valid `g1_status` with
evidence/dependency; the nine brief candidates are all present; every SUPPLIER_DATA_REQUIRED register id, stack parameter and package height has a
supplier request; no KNOWN value lacks a source; the edge-crossing flat exit reproduces the tool 180-degree wrap margin; the sensor FPC still carries
exactly 24 positions / 13 nets with no REAR-local or charger net; LPR454440 unchanged; architecture.md carries every conflict, request, decision,
reservation and edge-crossing id and the generated rows (dimensions, reservations, edge-crossing budget, land headroom, crossing radial table, overlap
register) verbatim.

`g1_scenarios.py check` additionally verifies: the cover plate sizing reproduces `inputs/stack_parameters.json` t_cover exactly; the legacy S4
arithmetic cross-check (15.85 / 16.276 / 17.23) passes; every scenario number quoted in `architecture.json` (g1 section) and `architecture.md`
(section G1) equals the generated value; the G1 verdict is quoted consistently.

## Editing rules

`architecture.json` is the authored source for the diagrams and the cross-checks. After editing it, run `arch_diagrams.py build` and then `check`.
For the authorized G2 input-register provenance change only, re-run `mech_model.py` first (the source SHA-256 pins in `architecture.json` will otherwise fail the check). G1 scenario
definitions live in `inputs/g1_scenarios.json`; all totals are computed by `tools/g1_scenarios.py` - never hand-edit `generated/`.

## G2 interconnect and Rev-A stack study

The current interconnect allocation, stack and open gates are in
[`generated/g2_interconnect.md`](generated/g2_interconnect.md) and
[`generated/g2_allocation.svg`](generated/g2_allocation.svg). `architecture.md` section G2 and
`architecture.json.g2` quote the generated result exactly. The original three diagrams retain the
G1 comparison geometry; current G2 corridors are supplemental reservations in `g2.reservations`.

- Contract: `G2_BRIEF.md` (current corrected provenance exception).
- Authored planning ranges/options: `inputs/g2_interconnect.json`. These are budgets, not supplier dimensions.
- Generator/checker: `tools/g2_interconnect.py`.
- Outputs: `generated/g2_interconnect.json`, `generated/g2_interconnect.md`, `generated/g2_allocation.svg`.
- `arch_diagrams.py check` validates the complete G2 block, numeric supplier requirements, exact generated
  Markdown section and exactly one current conflict status/evidence pair. Duplicate JSON keys fail parsing.

```bash
python3 -B design/mechanical/tools/g2_interconnect.py build
python3 -B design/mechanical/tools/g2_interconnect.py check
python3 -B design/mechanical/tools/arch_diagrams.py build
python3 -B design/mechanical/tools/arch_diagrams.py check
python3 -B design/mechanical/tools/mech_model.py check
python3 -B design/mechanical/tools/g1_scenarios.py check
```

`build` writes only the G2 generated outputs. Architecture quotations must be updated to the exact
`architecture_section()` output and result JSON when the inputs change; the checks detect stale quotations.
A generator consistency PASS is **not** G2 engineering acceptance: inspect `acceptance_complete`,
`unsatisfied_acceptance`, supplier gates and the overall verdict. Unknown antenna feed construction remains
explicitly unallocated instead of receiving invented flex length, bend count or mated height.

The Rev-A owner limit is nominal ≤16.5 mm and RSS ≤17.0 mm, measured from the exterior structural/sealing
cover to the deepest normal wrist-facing pod surface. The historical 14.0–15.5 mm figure is now a
non-binding Rev-B/production goal. Linear worst is reported separately. No supplier-gated or owner-gated
thickness lever is credited. P-0402 keeps its electrical/DC-bias evidence gate.

G1 engineering content is immutable against `168badbab6de1201bb3209902a53fe1e4b874cc9`. The only exception
is the register hash in `generated/zstack.json` and `generated/main_height_map.json`; the existing
`mech_model.py heights` and `stack` interfaces regenerate it, with every other semantic value unchanged.
Do not regenerate or edit G1 scenario inputs or outputs to accommodate G2. Run both immutable-tree git
checks and the positive semantic provenance comparison exactly as given in `G2_BRIEF.md` section 9.

G3 means REAR optical + guarded-analog placement; G4 means case + final MAIN outline co-design. A later
KiCad allocation implementation phase needs explicit authorization, supplier-confirmed envelopes and
mating map, electrical evidence and independent review. No downstream work or routing is authorized.

## G3 REAR optical and guarded-analog placement study

- Contract: `G3_BRIEF.md`, including OD-G3-MAX86141-PKG and the J1502 joint erratum.
- Authored geometry, ranges and evidence pins: `inputs/g3_rear_optical.json`.
- Stdlib-only generator/checker: `tools/g3_rear_optical.py`.
- Generated results: `generated/g3_rear_optical.json`, `generated/g3_rear_optical.md`.
- Generated drawings: `generated/g3_rear_faces.svg`, `generated/g3_rear_section.svg`.
- Exact quotations: `architecture.json.g3` and the marked G3 section in `architecture.md`.

```bash
python3 -B design/mechanical/tools/g3_rear_optical.py build
python3 -B design/mechanical/tools/g3_rear_optical.py check
python3 -B design/mechanical/tools/arch_diagrams.py check
```

G3 `build` writes only its four generated outputs. Synchronize the architecture quotations to the generated
JSON and `architecture_section()` before checking. Do not regenerate or edit G1/G2 records for G3.
`check` regenerates in memory, compares exact bytes, verifies source pins, all physical channel associations,
the quoted documents and mutation tests. Architecture provenance hashes the exact read-only
`reservations`, `rear_module` and `g2.reservations` projection to avoid a circular hash of its G3 quotation.
Available project `.kicad_mod` originals are pinned; standard-library footprints use the pinned immutable
PCB's embedded geometry because standalone system libraries are absent locally.

A consistency PASS does not mean engineering acceptance. Rejected candidates and all their failures are
retained; no score can override a hard failure. The complete section 10 validation command set remains
mandatory. Review `acceptance`, `unsatisfied_acceptance`, closure gates and the overall verdict.

The correction retains the three original topologies and evaluates 14 authored placement trials.
Nominal hard failures screen out trials; survivors receive the complete three-corner study.
Hard aggressor gaps are edge-to-edge using pad bounding extents and finite-width trace reservations;
ordered polygons control loop acceptance and convex hulls are diagnostic only. Package exemptions
apply only within the owning MAX86141 courtyard to fixed pads/terminal escapes. Nonterminal copper
and foreign aggressors retain full exclusions. VLED alternatives are ranked deterministically and
the selected paths feed the thermal study. The 0.254 mm MAX86141 lands are unchanged and remain
an AN1891 / 21-100134 evidence gate. G3 build/check also exercise these correction regressions.
