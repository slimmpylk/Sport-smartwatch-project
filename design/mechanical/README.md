# design/mechanical - Rev-A multi-board mechanical stack and rear sensor module architecture

**Status: G3 CONDITIONAL — SUPPLIER/MEASUREMENT GATES OPEN.** Recommended study candidate: **G3-B-S14**.
The corrected package exemption, both orthogonal VLED-entry orientations, physical pad/trace clearance,
ordered-loop checks and placement search are recorded in the generated report. All nominal hard checks
pass for the selected candidate; conservative-corner failures and evidence gates remain explicit.

**G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES** (OD-G3-RECORD). This records the accepted review
status without changing any immutable G2 result or closing any supplier gate. G4 and KiCad edits remain
unauthorized. All G3 placements and reservations are reversible study evidence.

**G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES** (OD-G4-RECORD, 2026-10-14). This records the accepted
review status and freezes G3-B-S14 as the G4 carry-in; the generated G3 verdict and every G3 criterion-10
supplier/manufacturer/measurement gate are unchanged. **G4 status: G4 OWNER DECISION REQUIRED** (see the G4
section below). No KiCad, G5, K1 or Q1 work is authorized.

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

## G4 case / caseback / sealing-architecture closure study

**G4 OWNER DECISION REQUIRED — BLOCKED / UNRELEASED STUDY**. Uncommitted. Independent re-review: **PASS AS CORRECT BLOCKED STUDY** (owner-provided record).

- Binding contract: `G4_BRIEF.md`; authored geometry/process inputs: `inputs/g4_case_sealing.json`.
- Generator: `tools/g4_case_sealing.py build|check|selftest` (stdlib only).
- Results: `generated/g4_case_sealing.json`, report `generated/g4_case_sealing.md`, full retained-point evidence `generated/g4_sweep.jsonl`.
- Drawings: `generated/g4_plan.svg`, `g4_sections.svg`, `g4_seal_map.svg`, `g4_assembly.svg`.
- `architecture.json.g4` is a compact summary with hashes; conflicts gain exactly one `g4_status`. Evidence resides in the generated G4 report/JSON.
- Complete passing candidate set: []; no selected diameter. Diagnostic thresholds do not imply feasibility.
- Legacy radial −0.950 mm and X25 −1.100 mm remain unchanged. Corrected local process, carrier, button, charger, window and pressure checks are reported.
- LRA stop and OD-G4-WINDOW remain. No G3 reopening demonstrated; OD-G4-STACK is not triggered without proof of necessary total growth.
- Binding cover-first assembly conflict: CONTRACT INTERPRETATION / CLARIFICATION REQUIRED; SERVICE-COVER-REBOND remains open.
- Unsatisfied acceptance criteria: 5, 8, 9, 10, 11, 12, 13, 15. Criterion 13 includes the literal legacy later-phase scope incompatibility.

`build` regenerates the G4 files and permitted summaries. `check` regenerates in memory, verifies pins/hashes, complete check coverage, scope and budgets, and runs mutation tests. A consistency PASS is not engineering acceptance.

No KiCad, G5, K1 or Q1 work is authorized. No RF performance, structural qualification, 5 ATM qualification or supplier availability claim.

<!-- G4 RUN RECORD BEGIN -->

### G4 non-blocking review-hardening run record — 2026-10-15

Branch `mechanical/g4-case-sealing-closure`; HEAD `935da5ca737ce4cd5b9a2e1245c7d48c8104a592`. No commit or push.

Independent re-review returned **PASS AS CORRECT BLOCKED STUDY** (owner-provided record). Engineering verdict remains **G4 OWNER DECISION REQUIRED — BLOCKED / UNRELEASED STUDY**. Complete passing candidate set `[]`; no selected diameter. Safe to commit as a blocked study: **YES**. This is not G4 closure or engineering acceptance.

Hardening changes:

- H13 now uses the existing perimeter-only bypass stress and deflection margins instead of requiring a closed evidence-class literal. Material/support qualification remains open; all current H13 results remain FAIL.
- H05 reports radial/edge geometry and LRA-coupled feasibility separately. The recomputed partial grid thresholds are approximately >=51.10 mm for polymer side-radial geometry and >=52.10 mm for G4-B caseback/related comparison geometry. They do not establish feasibility.
- Generated evidence discloses one scalar side-wall thickness per design point; the local r_case(az,z) feature table does not establish independent t_wall(az,z) closure.
- fmtv renders full dictionary keys; numerical calculations are unchanged.
- H20 explicitly requires BOTH the 4 x 5 mm contact block AND its modeled continuous bond/seal land inside the authorized aperture/wedge at adverse tolerance. H20 is not weakened.
- PCM-lobe clearance to SW3/supports, the insulation envelope, carrier retention and BATT_EXIT/tail clearance are explicit OPEN gates. Existing planning insulation thickness is reported; missing dimensions, loads and supplier values remain missing.
- Diagnostic geometric successes remain REMAINS_OPEN, with explicit unreleased diagnostic evidence, instead of RESOLVED_BY_G4. The supplied independent review verdict is recorded without calling G4 CLOSED or PASS.

PASS: original numerical checks, design points, H01-H25 results, ranking, verdict, and all 423 sweep records unchanged; H13 numeric bypass fails throughout; H05 thresholds 51.10 / 52.10 mm reproduced; all four battery gates OPEN; four SVGs parse; arch_diagrams.py untouched by hardening.

At the retained diagnostic D = 50.90 mm:

| Candidate | Bypass stress margin MPa | Bypass deflection margin mm | H13 |
| --- | --- | --- | --- |
| G4-A | -300.971654783 | -2.572921584 | FAIL |
| G4-B | -472.918150691 | -0.232746475 | FAIL |
| G4-C | -300.971654783 | -2.572921584 | FAIL |

Two successive builds regenerated all seven G4 outputs plus architecture.json, architecture.md and the generated README summary. All ten files were byte-identical. This run record was written after that comparison; the build snapshots below include the previous run record in README. The generator preserves the run-record text verbatim.

| Validation | Actual exit | Seconds |
| --- | --- | --- |
| `deterministic_build_1` | 0 | 52.88 |
| `deterministic_build_2` | 0 | 55.76 |
| `g4_check` | 0 | 56.69 |
| `g4_selftest` | 0 | 53.79 |
| `G1_G2_G3_immutable_bytes` | 0 | 0.00 |
| `G4_brief_expected_HEAD` | 0 | 0.00 |
| `G1_immutable_bytes` | 0 | 0.00 |
| `G2_section9B_semantic_provenance` | 0 | 0.05 |
| `architecture_semantic_and_section_bytes` | 0 | 0.60 |
| `KiCad_interfaces_placement_libraries` | 0 | 0.00 |
| `interfaces_diff` | 0 | 0.00 |
| `placement_diff` | 0 | 0.00 |
| `outside_mechanical_tracked_scope` | 0 | 0.03 |
| `tracked_untracked_write_scope` | 0 | 1.33 |
| `diff_check` | 0 | 0.21 |
| `g3_rear_optical_check` | 1 | 156.42 |
| `mech_model_check` | 0 | 0.14 |
| `g1_scenarios_check` | 0 | 0.35 |
| `g2_interconnect_check` | 0 | 1.61 |
| `arch_diagrams_check` | 1 | 9.28 |
| `git_status` | 0 | 0.00 |

The historical G3 check exits 1 because its scope whitelist excludes uncommitted G4 files. arch_diagrams.py check also exits 1 for G3 package consistency. Both failures remain literal; no historical tool was changed by this hardening pass. Acceptance criterion 13 remains unmet.

Exact validation commands and observed output follow. G1/G2/G3 immutability, semantic provenance, KiCad, interfaces, placement and scope checks all passed.

**deterministic_build_1 — exit 0**

```bash
python3 -B design/mechanical/tools/g4_case_sealing.py build
```

```text
{"files": ["g4_assembly.svg", "g4_case_sealing.json", "g4_case_sealing.md", "g4_plan.svg", "g4_seal_map.svg", "g4_sections.svg", "g4_sweep.jsonl"], "runtime_s": 52.6, "status": "BUILT", "stops": ["STOP-DIAMETER", "STOP-LRA", "OD-G4-WINDOW"], "verdict": "G4 OWNER DECISION REQUIRED"}
```

**deterministic_build_2 — exit 0**

```bash
python3 -B design/mechanical/tools/g4_case_sealing.py build
```

```text
{"files": ["g4_assembly.svg", "g4_case_sealing.json", "g4_case_sealing.md", "g4_plan.svg", "g4_seal_map.svg", "g4_sections.svg", "g4_sweep.jsonl"], "runtime_s": 55.48, "status": "BUILT", "stops": ["STOP-DIAMETER", "STOP-LRA", "OD-G4-WINDOW"], "verdict": "G4 OWNER DECISION REQUIRED"}
```

**g4_check — exit 0**

```bash
python3 -B design/mechanical/tools/g4_case_sealing.py check
```

```text
{"engineering_verdict": "G4 OWNER DECISION REQUIRED", "failures": [], "runtime_s": 56.3, "selected_candidate": null, "status": "PASS", "stops": ["STOP-DIAMETER", "STOP-LRA", "OD-G4-WINDOW"], "unsatisfied_acceptance": [5, 8, 9, 10, 11, 12, 13, 15]}
```

**g4_selftest — exit 0**

```bash
python3 -B design/mechanical/tools/g4_case_sealing.py selftest
```

```text
{"caught": 32, "mutations": 32, "status": "PASS", "tests": [{"caught": true, "id": "radial_collision_linear_worst"}, {"caught": true, "id": "legacy_value_mutated"}, {"caught": true, "id": "t_total_16_501_nominal"}, {"caught": true, "id": "d_case_body_51_01"}, {"caught": true, "id": "unpermitted_boss"}, {"caught": true, "id": "aperture_without_seal"}, {"caught": true, "id": "oring_overcompression"}, {"caught": true, "id": "conductive_part_in_gnss_rad"}, {"caught": true, "id": "new_wiring_in_wifi_rad"}, {"caught": true, "id": "ferromagnetic_screw_in_mag_clear"}, {"caught": true, "id": "obstructed_s14_support_land"}, {"caught": true, "id": "lra_pose_inside_rear_outline"}, {"caught": true, "id": "lra_hidden_in_lower_web"}, {"caught": true, "id": "rear_insertion_collision"}, {"caught": true, "id": "mirrored_rear_transform"}, {"caught": true, "id": "window_thickness_gain_credited"}, {"caught": true, "id": "supplier_gated_term_narrowed"}, {"caught": true, "id": "pressure_domains_nonoverlap_accounting"}, {"caught": true, "id": "forbidden_pressure_branch_alongside_valid_path"}, {"caught": true, "id": "omitted_button_travel"}, {"caught": true, "id": "wrong_local_polymer_process"}, {"caught": true, "id": "carrier_wall_below_minimum"}, {"caught": true, "id": "charger_4x5_containment_failure"}, {"caught": true, "id": "zero_tolerance_infeasible_oring"}, {"caught": true, "id": "window_minimum_thickness_failure"}, {"caught": true, "id": "vacuous_H07_H08"}, {"caught": true, "id": "incomplete_lra_exclusion"}, {"caught": true, "id": "partial_candidate_without_all_hard_checks"}, {"caught": true, "id": "cover_feature_proud"}, {"caught": true, "id": "assembly_cover_first_not_silently_replaced"}, {"caught": true, "id": "H13_bypass_numeric_not_evidence_literal"}, {"caught": true, "id": "polygon_contact_not_missed"}]}
```

**G1_G2_G3_immutable_bytes — exit 0**

```bash
git diff --exit-code afb19ac173ce67c7e9599313cc5a0942e026ade9 -- design/mechanical/inputs/input_register.json design/mechanical/inputs/stack_parameters.json design/mechanical/inputs/package_heights.json design/mechanical/inputs/g1_scenarios.json design/mechanical/inputs/g2_interconnect.json design/mechanical/inputs/g3_rear_optical.json design/mechanical/tools/mech_model.py design/mechanical/tools/mech_model_spec.md design/mechanical/tools/g1_scenarios.py design/mechanical/tools/g2_interconnect.py design/mechanical/tools/g3_rear_optical.py design/mechanical/generated/zstack.json design/mechanical/generated/zstack.md design/mechanical/generated/zstack_section.svg design/mechanical/generated/main_height_map.json design/mechanical/generated/main_height_map.md design/mechanical/generated/main_height_map.svg design/mechanical/generated/g1_scenarios.json design/mechanical/generated/g1_scenarios.md design/mechanical/generated/g2_interconnect.json design/mechanical/generated/g2_interconnect.md design/mechanical/generated/g2_allocation.svg design/mechanical/generated/g3_rear_optical.json design/mechanical/generated/g3_rear_optical.md design/mechanical/generated/g3_rear_faces.svg design/mechanical/generated/g3_rear_section.svg design/mechanical/generated/perimeter_map.svg design/mechanical/generated/rear_module_concept.svg design/mechanical/generated/interconnect_paths.svg design/mechanical/PHASE_BRIEF.md design/mechanical/G1_BRIEF.md design/mechanical/G2_BRIEF.md design/mechanical/G3_BRIEF.md
```

**G4_brief_expected_HEAD — exit 0**

```bash
git diff --exit-code 935da5ca737ce4cd5b9a2e1245c7d48c8104a592 -- design/mechanical/G4_BRIEF.md
```

**G1_immutable_bytes — exit 0**

```bash
git diff --exit-code 168badbab6de1201bb3209902a53fe1e4b874cc9 -- design/mechanical/inputs/stack_parameters.json design/mechanical/inputs/package_heights.json design/mechanical/inputs/g1_scenarios.json design/mechanical/tools/mech_model.py design/mechanical/tools/mech_model_spec.md design/mechanical/tools/g1_scenarios.py design/mechanical/generated/zstack.md design/mechanical/generated/zstack_section.svg design/mechanical/generated/main_height_map.md design/mechanical/generated/main_height_map.svg design/mechanical/generated/g1_scenarios.json design/mechanical/generated/g1_scenarios.md
```

**G2_section9B_semantic_provenance — exit 0**

```bash
python3 -B -c 'import json,subprocess,sys
BASE='"'"'168badbab6de1201bb3209902a53fe1e4b874cc9'"'"'
REG='"'"'design/mechanical/inputs/input_register.json'"'"'
FILES=['"'"'design/mechanical/generated/zstack.json'"'"','"'"'design/mechanical/generated/main_height_map.json'"'"']
def normalize(doc,path):
    hashes=doc.get('"'"'inputs_sha256'"'"')
    if not isinstance(hashes,dict) or REG not in hashes: sys.exit('"'"'FAIL: missing provenance '"'"'+path)
    hashes[REG]=None
    return doc
for path in FILES:
    old=json.loads(subprocess.run(['"'"'git'"'"','"'"'show'"'"',BASE+'"'"':'"'"'+path],capture_output=True,check=True).stdout)
    new=json.load(open(path))
    assert normalize(old,path)==normalize(new,path),path
print('"'"'PASS: only input_register provenance normalized'"'"')
'
```

```text
PASS: only input_register provenance normalized
```

**architecture_semantic_and_section_bytes — exit 0**

```bash
python3 -B -c 'import json,subprocess
from pathlib import Path
BASE='"'"'afb19ac173ce67c7e9599313cc5a0942e026ade9'"'"'
def old(path): return subprocess.run(['"'"'git'"'"','"'"'show'"'"',BASE+'"'"':'"'"'+path],capture_output=True,check=True).stdout.decode()
a=json.loads(old('"'"'design/mechanical/architecture.json'"'"'));b=json.load(open('"'"'design/mechanical/architecture.json'"'"'))
for key in ('"'"'g1'"'"','"'"'g2'"'"','"'"'g3'"'"'): assert a[key]==b[key],key
assert [{k:v for k,v in c.items() if k!='"'"'g4_status'"'"'} for c in b['"'"'conflicts'"'"']]==a['"'"'conflicts'"'"']
assert all([k for k in c if k.startswith('"'"'g4_'"'"')]==['"'"'g4_status'"'"'] for c in b['"'"'conflicts'"'"'])
assert {k:v for k,v in b.items() if k not in ('"'"'g4'"'"','"'"'conflicts'"'"')}=={k:v for k,v in a.items() if k!='"'"'conflicts'"'"'}
x=old('"'"'design/mechanical/architecture.md'"'"');y=Path('"'"'design/mechanical/architecture.md'"'"').read_text()
for start,end in [('"'"'## G1.'"'"','"'"'<!-- G2 GENERATED BEGIN -->'"'"'),('"'"'<!-- G2 GENERATED BEGIN -->'"'"','"'"'<!-- G2 GENERATED END -->'"'"'),('"'"'<!-- G3 GENERATED BEGIN -->'"'"','"'"'<!-- G3 GENERATED END -->'"'"')]:
    assert x[x.index(start):x.index(end,x.index(start))]==y[y.index(start):y.index(end,y.index(start))],start
print('"'"'PASS: G1/G2/G3 blocks and sections unchanged; conflicts only gain g4_status'"'"')
'
```

```text
PASS: G1/G2/G3 blocks and sections unchanged; conflicts only gain g4_status
```

**KiCad_interfaces_placement_libraries — exit 0**

```bash
git diff --exit-code afb19ac173ce67c7e9599313cc5a0942e026ade9 -- '*.kicad_pcb' '*.kicad_sch' '*.kicad_pro' '*.kicad_prl' design/interfaces design/placement rear_sensor libraries
```

**interfaces_diff — exit 0**

```bash
git diff --exit-code afb19ac173ce67c7e9599313cc5a0942e026ade9 -- design/interfaces
```

**placement_diff — exit 0**

```bash
git diff --exit-code afb19ac173ce67c7e9599313cc5a0942e026ade9 -- design/placement
```

**outside_mechanical_tracked_scope — exit 0**

```bash
python3 -B -c 'import subprocess; p=subprocess.run(['"'"'git'"'"','"'"'diff'"'"','"'"'--name-only'"'"','"'"'afb19ac173ce67c7e9599313cc5a0942e026ade9'"'"','"'"'--'"'"','"'"'.'"'"','"'"':(exclude)design/mechanical/**'"'"'],capture_output=True,text=True,check=True); assert not p.stdout.strip(),p.stdout; print('"'"'PASS'"'"')'
```

```text
PASS
```

**tracked_untracked_write_scope — exit 0**

```bash
python3 -B -c 'import sys;sys.path.insert(0,'"'"'design/mechanical/tools'"'"');import g4_case_sealing as g; s=g.scope_check(g.Study()); print(s); assert s['"'"'pass_'"'"']'
```

```text
{'checks': {'g4_brief_commit_found': True, 'g4_brief_unchanged': True, 'g1_g2_g3_immutables_unchanged': True, 'kicad_interfaces_placement_unchanged': True, 'nothing_outside_design_mechanical': True, 'g4_changes_within_section_4_3': True}, 'pass_': True, 'baselines': {'g3': 'afb19ac173ce67c7e9599313cc5a0942e026ade9', 'g4_brief': 'introducing commit of design/mechanical/G4_BRIEF.md'}}
```

**diff_check — exit 0**

```bash
git diff --check
```

**g3_rear_optical_check — exit 1**

```bash
python3 -B design/mechanical/tools/g3_rear_optical.py check
```

```text
Traceback (most recent call last):
  File "/home/sapy/sportwatch_ai/sportwatch_revA-engineering/design/mechanical/tools/g3_rear_optical.py", line 944, in <module>
    if __name__=='__main__':main()
                            ~~~~^^
  File "/home/sapy/sportwatch_ai/sportwatch_revA-engineering/design/mechanical/tools/g3_rear_optical.py", line 941, in main
    check_architecture(res)
    ~~~~~~~~~~~~~~~~~~^^^^^
  File "/home/sapy/sportwatch_ai/sportwatch_revA-engineering/design/mechanical/tools/g3_rear_optical.py", line 932, in check_architecture
    scope_check()
    ~~~~~~~~~~~^^
  File "/home/sapy/sportwatch_ai/sportwatch_revA-engineering/design/mechanical/tools/g3_rear_optical.py", line 918, in scope_check
    assert all(p.startswith('design/mechanical/') and p[len('design/mechanical/'):] in allowed for p in files),files
           ~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ['design/mechanical/README.md', 'design/mechanical/architecture.json', 'design/mechanical/architecture.md', 'design/mechanical/tools/arch_diagrams.py', 'design/mechanical/generated/g4_assembly.svg', 'design/mechanical/generated/g4_case_sealing.json', 'design/mechanical/generated/g4_case_sealing.md', 'design/mechanical/generated/g4_plan.svg', 'design/mechanical/generated/g4_seal_map.svg', 'design/mechanical/generated/g4_sections.svg', 'design/mechanical/generated/g4_sweep.jsonl', 'design/mechanical/inputs/g4_case_sealing.json', 'design/mechanical/tools/g4_case_sealing.py']
```

**mech_model_check — exit 0**

```bash
python3 -B design/mechanical/tools/mech_model.py check
```

```text
{"H_B_in_battery": 0.95, "H_F_under_display": 2.7, "T_total_nominal": 16.75, "T_total_thick": 19.53, "counts": {"main_B.Cu": 17, "main_F.Cu": 167, "main_total": 184, "rear_total": 44}, "failures": [], "files_checked": ["main_height_map.json", "main_height_map.md", "main_height_map.svg", "zstack.json", "zstack.md", "zstack_section.svg"], "status": "PASS"}
```

**g1_scenarios_check — exit 0**

```bash
python3 -B design/mechanical/tools/g1_scenarios.py check
```

```text
{"cover_sizing_check": "PASS", "failures": [], "legacy_cross_check": "PASS", "scenarios": 16, "status": "PASS", "verdict": "THICKNESS OWNER DECISION REQUIRED"}
```

**g2_interconnect_check — exit 0**

```bash
python3 -B design/mechanical/tools/g2_interconnect.py check
```

```text
{
  "acceptance_complete": false,
  "failures": [],
  "status": "PASS",
  "verdict": "G2 CONDITIONAL — ENGINEERING GATES OPEN"
}
```

**arch_diagrams_check — exit 1**

```bash
python3 -B design/mechanical/tools/arch_diagrams.py check
```

```text
{"conflicts": 30, "failures": ["number: G3 package consistency: ['design/mechanical/README.md', 'design/mechanical/architecture.json', 'design/mechanical/architecture.md', 'design/mechanical/tools/arch_diagrams.py', 'design/mechanical/generated/g4_assembly.svg', 'design/mechanical/generated/g4_case_sealing.json', 'design/mechanical/generated/g4_case_sealing.md', 'design/mechanical/generated/g4_plan.svg', 'design/mechanical/generated/g4_seal_map.svg', 'design/mechanical/generated/g4_sections.svg', 'design/mechanical/generated/g4_sweep.jsonl', 'design/mechanical/inputs/g4_case_sealing.json', 'design/mechanical/tools/g4_case_sealing.py']"], "overlap_pairs": 54, "reservations": 34, "status": "FAIL", "supplier_requests": 16, "svgs": ["interconnect_paths.svg", "perimeter_map.svg", "rear_module_concept.svg"]}
```

**git_status — exit 0**

```bash
git status --short
```

```text
M design/mechanical/README.md
 M design/mechanical/architecture.json
 M design/mechanical/architecture.md
 M design/mechanical/tools/arch_diagrams.py
?? design/mechanical/generated/g4_assembly.svg
?? design/mechanical/generated/g4_case_sealing.json
?? design/mechanical/generated/g4_case_sealing.md
?? design/mechanical/generated/g4_plan.svg
?? design/mechanical/generated/g4_seal_map.svg
?? design/mechanical/generated/g4_sections.svg
?? design/mechanical/generated/g4_sweep.jsonl
?? design/mechanical/inputs/g4_case_sealing.json
?? design/mechanical/tools/g4_case_sealing.py
```

All four G4 SVGs parse as XML. Main generated JSON: 1256564 bytes. Compact architecture.g4: 31533 bytes. Retained-point evidence: 423 JSONL rows.

SHA-256 from both byte-identical build snapshots (README measured before this run record was written):

| File | SHA-256 |
| --- | --- |
| `design/mechanical/generated/g4_assembly.svg` | `399390a3e1bbec850337705aaae7f915a2faa92a957952829e68a74a0cd48250` |
| `design/mechanical/generated/g4_case_sealing.json` | `2af9d2d149e4c95803d0dfbb56b20d8fde63d5c9a2b5118587632b4bb2acd9ad` |
| `design/mechanical/generated/g4_case_sealing.md` | `eb3afc85d2fe93d6490303a22de77da61cd1f6a8f8451cf0adba408a450fc539` |
| `design/mechanical/generated/g4_plan.svg` | `b635703cbcf836ee77a742bebf3c7541ea69c1571abda98a2c51dc38a6a43e49` |
| `design/mechanical/generated/g4_seal_map.svg` | `c5917a3831ca537810dac2a900b822a11ee5dae72bdb1b41220ea2217d59f90e` |
| `design/mechanical/generated/g4_sections.svg` | `33a9a6f27dc07ca8ef2aa6b8fa985746b63143a6805f59950a94b111b38d143b` |
| `design/mechanical/generated/g4_sweep.jsonl` | `a889d341cac28e9b3f7358b058cf7efb4cb6fe313547e2f5004d6f938777b34a` |
| `design/mechanical/architecture.json` | `751a3be77dc5632c0503f2d45c774d09b2f0dcb2b95d3069d3413283bc48dec6` |
| `design/mechanical/architecture.md` | `6c58bf2b8d4c5b084d005297b1c989fca9adca82c3c576130e04815a9af21afa` |
| `design/mechanical/README.md` | `194d3664ebad1ac7da21dc53fdce3446363e3e9c5485c580044c1109c66d1bf5` |

<!-- G4 RUN RECORD END -->
