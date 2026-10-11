# design/mechanical - Rev-A multi-board mechanical stack and rear sensor module architecture

**Status: PROVISIONAL, REVERSIBLE architecture study.** G1 (owner-decision integration, 2026-10-11) is COMPLETE with verdict **THICKNESS OWNER
DECISION REQUIRED** (architecture.md section G1): the seven owner decisions are integrated, the thickness-recovery scenarios and the 5 ATM
implications are computed by `tools/g1_scenarios.py`, and no scenario is credibly <= 15.5 mm. Exit means "architecture coherent, conflicts
exposed, unknowns tracked", not "mechanics final". Nothing in this directory authorises KiCad edits, routing, an outline freeze, case CAD,
connector/antenna selection, a battery change or an electrical partition change. Frozen invariants are listed in `inputs/input_register.json`
and copied verbatim into `architecture.json`.

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
 - Z positive from the front exterior toward the wrist. T_total = front-most exterior surface (cover lens) to the deepest wrist-facing pod surface (target 14.0-15.5 mm);
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
If `inputs/` change, re-run `mech_model.py` first (the source SHA-256 pins in `architecture.json` will otherwise fail the check). G1 scenario
definitions live in `inputs/g1_scenarios.json`; all totals are computed by `tools/g1_scenarios.py` - never hand-edit `generated/`.
