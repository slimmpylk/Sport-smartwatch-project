# design/mechanical - Rev-A multi-board mechanical stack and rear sensor module architecture

**Status: PROVISIONAL, REVERSIBLE architecture study.** Exit means "architecture coherent, conflicts exposed, unknowns tracked", not "mechanics
final". Nothing in this directory authorises KiCad edits, routing, an outline freeze, case CAD, connector/antenna selection, a battery change or an
electrical partition change. Frozen invariants are listed in `inputs/input_register.json` and copied verbatim into `architecture.json`.

## Package index

| File | Content |
|---|---|
| `PHASE_BRIEF.md` | Scope contract (objectives, owner confirmations, deliverables, rules). Input; not edited by the architecture package. |
| `architecture.md` | The architecture document: sections A-J and 11-15 (Z-stack, height map, battery/carrier, REAR board, optical pod, MAX30208 thermal path, FPC path, charger module, reservations, assembly/service/SWD, dimension table, conflicts register, requests, unfrozen list, next gate). |
| `architecture.json` | Machine-readable architecture: reservations (clock, radial, Z, class), tool quotes, REAR envelope derivation, FPC/charger path parameters, assembly steps, conflicts, supplier requests, owner decisions, unfrozen items, next gate. |
| `tools/arch_diagrams.py` | Stdlib-only diagram generator and consistency checker (`build` / `check`). |
| `generated/perimeter_map.svg` | Front-view clock/sector reservation map with Z-level legend, envelopes and conflict markers. |
| `generated/rear_module_concept.svg` | REAR envelope concept: wrist-side top view with the board-to-assembly transform, and a section through the pod with parametric dimensions. |
| `generated/interconnect_paths.svg` | MAIN-REAR FPC path and charger harness paths in plan view plus the south radial section. |
| `inputs/` | `input_register.json`, `package_heights.json`, `stack_parameters.json` (authoritative inputs; read-only for this package). |
| `tools/mech_model.py`, `tools/mech_model_spec.md` | Deterministic height-map / Z-stack / radial model and its specification. |
| `generated/main_height_map.*`, `generated/zstack.*`, `generated/zstack_section.svg` | Outputs of `mech_model.py` (quoted by the architecture package, never hand-edited). |

## Conventions

- Front view from the display: north/12 = -Y, east/3 = +X, south/6 = +Y, west/9 = -X; MAIN origin (100,100). Azimuth = degrees clockwise from north.
- Z positive from the front exterior toward the wrist. T_total = exterior display glass to the deepest wrist-facing pod surface (target 14.0-15.5 mm);
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
```

`arch_diagrams.py check` verifies, among others: source SHA-256 pins; frozen-invariant list identical to the register; quoted stack and radial numbers equal to
`zstack.json`; every reservation has clock range, radial range, Z level(s) and class; every overlapping reservation pair at a shared Z level is listed in a
conflict; every conflict has severity, options and an owner-decision flag; the nine brief candidates are all present; every SUPPLIER_DATA_REQUIRED register id,
stack parameter and package height has a supplier request; no KNOWN value lacks a source; scenario, lever, FPC, REAR-envelope and support arithmetic is
recomputed; the sensor FPC still carries exactly 24 positions / 13 nets with no REAR-local or charger net; LPR454440 unchanged; architecture.md carries every
conflict, request, decision and reservation id.

## Editing rules

`architecture.json` is the authored source for the diagrams and the cross-checks. After editing it, run `arch_diagrams.py build` and then `check`.
If `inputs/` change, re-run `mech_model.py` first (the source SHA-256 pins in `architecture.json` will otherwise fail the check).
