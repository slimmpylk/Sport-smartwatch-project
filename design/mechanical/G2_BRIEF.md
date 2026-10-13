# G2 brief — INTERCONNECT SIDE-ALLOCATION, FLEX PATH AND REV-A STACK CLOSURE (Rev-A)

Status: provisional, reversible architecture work. This brief is the scope contract for G2. It builds on the
G1 owner-decision integration, CLOSED / PASS at engineering commit `168badbab6de1201bb3209902a53fe1e4b874cc9`
(original accepted G1 checkpoint `666c547`), and on [PHASE_BRIEF.md](PHASE_BRIEF.md) and
[G1_BRIEF.md](G1_BRIEF.md), whose rules still apply except where this brief explicitly changes scope.
Destination in the engineering worktree: `design/mechanical/G2_BRIEF.md`.

## 1. Objective

Decide, from deterministic 3-D geometry and stated manufacturer/supplier constraints, the PCB side, XY/azimuth
window, mating direction, cable/FPC exit direction and flex path of every mechanically significant MAIN / REAR
interface. Then close the Rev-A thickness stack against the owner-approved Rev-A limit, using only credible levers.
Exit is an interconnect allocation and a Rev-A stack baseline that a later KiCad placement phase can implement. It
is not a KiCad change and not a frozen design.

## 2. Owner decisions (authoritative)

**New, 2026-10-12 — OD-THICK-REVA.** Rev-A finished-watch thickness engineering limit:
**T_total <= 16.5 mm nominal and <= 17.0 mm RSS**, with the existing convention (front exterior structural/sealing
cover to the deepest normal wrist-facing surface of the rear optical pod). 14.0–15.5 mm is kept as the non-binding
Rev-B / production optimization goal. The approval covers Rev-A engineering/prototype integration only. It does
NOT authorize weakening the 5 ATM requirement, PPG architecture, battery safety, RF performance, optical
performance, sealing, assembly robustness or frozen electrical boundaries to meet thickness.

**Already in force (2026-10-11, unchanged):** OD-COVER, OD-REAR-SIDED, OD-WATER, OD-U8, OD-DEVACCESS, OD-J202,
OD-CONN-SIDE, as recorded in `inputs/input_register.json`. Do not revoke or reinterpret any of them.

Record OD-THICK-REVA in `inputs/input_register.json` as an owner-decision entry with this date and source.
Recording it changes that file's SHA-256, which `mech_model.py` embeds as provenance in two G1 generated
JSON files; the single permitted consequence of that is the provenance-only exception defined in section 4.

## 3. Frozen (do not change)

- Rigid MAIN; rigid double-sided REAR sensor daughterboard; MAIN↔REAR FPC; separate charger-contact
  flex/sub-PCB/harness.
- MAIN↔REAR logical interface: 24 positions / 13 logical nets, exactly as in
  `design/interfaces/main_rear_interface.json`. The FPC carries approved power + digital/control only.
  Charger-positive stays outside the sensor FPC. A connector side change may require a mirrored *physical*
  position order (the physical permutation was never frozen). Record that as a requirement for the later placement
  phase. Do not edit the interface file.
- PD_IN, PD_GND, VREF, sensitive mux geometry, LED cathode/current-sink paths, photodiodes and both MAX86141 stay
  REAR-local on the skin-facing side.
- Battery LPR454440. U8 = MAX-F10S stays on MAIN F.Cu at its current north position. **No GNSS part change in G2.**
- MAIN Ø46 mm stays a provisional development envelope (not Edge.Cuts). General routing is not authorized.
- Input register `frozen_invariants` stay verbatim. Anything that would need one of them changed is an OWNER
  DECISION REQUIRED item, never the recommendation.

## 4. Scope

**May modify** (tracked files under `design/mechanical/` only): `architecture.md`, `architecture.json`,
`README.md`, `inputs/input_register.json`, `tools/arch_diagrams.py`, `generated/interconnect_paths.svg`,
`generated/perimeter_map.svg`, `generated/rear_module_concept.svg`. Plus these new files:
`inputs/g2_interconnect.json`, `tools/g2_interconnect.py` (build/check) and its generated outputs
`generated/g2_interconnect.json`, `generated/g2_interconnect.md` and optionally `generated/g2_allocation.svg`.
Generated files are written only by the tools and must regenerate byte-identically (the G1
provenance-only exception below excepted).

**G1 record is immutable** (engineering content). These must stay byte-identical to `168badb`:
- `inputs/stack_parameters.json`, `inputs/package_heights.json`, `inputs/g1_scenarios.json`;
- `tools/mech_model.py`, `tools/mech_model_spec.md`, `tools/g1_scenarios.py`;
- `generated/zstack.md`, `generated/zstack_section.svg`, `generated/main_height_map.md`,
  `generated/main_height_map.svg`, `generated/g1_scenarios.*`.

**Provenance-only exception (the ONLY one).** `mech_model.py` records the SHA-256 of
`inputs/input_register.json` in the `inputs_sha256` field of `generated/zstack.json` and
`generated/main_height_map.json`. Recording OD-THICK-REVA (section 2) therefore legitimately changes
exactly that one provenance value in each of those two files. They are writable ONLY to regenerate
that provenance: after recording OD-THICK-REVA, run
`python3 -B design/mechanical/tools/mech_model.py heights` and
`python3 -B design/mechanical/tools/mech_model.py stack`. With respect to `168badb`, the ONLY
permitted semantic difference in each of `generated/zstack.json` and
`generated/main_height_map.json` is the value of
`inputs_sha256["design/mechanical/inputs/input_register.json"]`. No other field may change. This
exception does NOT authorize changes to: any calculated geometry; any thickness value; any
tolerance; any component count; any scenario result; any other `inputs_sha256` entry;
`tools/mech_model.py`, `tools/mech_model_spec.md` or `tools/g1_scenarios.py`;
`inputs/stack_parameters.json`, `inputs/package_heights.json` or `inputs/g1_scenarios.json`; any
other G1 generated output; any KiCad/interface/placement file. Section 9 validates this semantically
(the files are not removed from validation). The invariant is: G1 ENGINEERING CONTENT IMMUTABLE + G1
PROVENANCE MAY ACKNOWLEDGE THE NEW OWNER-DECISION REGISTER HASH.

`tools/g2_interconnect.py` may import `mech_model` / `g1_scenarios` functions and their tolerance policy. Any new
G2 parameter (connector stack, stiffener, flex, bend, pack-edge geometry) lives in `inputs/g2_interconnect.json`.

**May not modify:** anything outside `design/mechanical/`; any KiCad file (`*.kicad_pcb`, `*.kicad_sch`,
`*.kicad_pro`, `*.kicad_prl`) or KiCad geometry; `rear_sensor/**`, `libraries/**`, `design/interfaces/**`,
`design/placement/**`, firmware, scripts, tests, docs; `PHASE_BRIEF.md`, `G1_BRIEF.md` and this brief. KiCad boards
and schematics may be **read** for evidence (positions, courtyards, sides, nets).

**Evidence classes** (every material value and claim carries exactly one): MANUFACTURER_VERIFIED (primary-source
document id + page/figure, already cited in the repo or newly cited with id), PROJECT_DERIVED (computed by a G1/G2
tool from cited inputs), PROVISIONAL_ASSUMPTION (labelled range min / nom / max with rationale; the nominal must
not be the best case), SUPPLIER_DATA_REQUIRED, OWNER_DECISION. **Never invent supplier dimensions.** A candidate
connector family may be named only as a PROVISIONAL class example, never as a selection.

## 5. Evaluations (deterministic, in `tools/g2_interconnect.py`)

Physical convention: MAIN F.Cu = front/display-facing; MAIN B.Cu = rear/battery/wrist-facing. REAR lies behind the
pack and the carrier lower web. Evaluate every check at the three G1 corners (nominal / conservative / optimistic)
unless stated otherwise.

The **lead hypotheses below come from the pre-G2 review. They are hypotheses to test, not results to hard-code.**
Every option listed is evaluated on equal terms, and selection uses only the rule in section 6.

### 5.1 Common checks for every interface option

1. **Back-zone ceiling (B.Cu options).** Connector stack h_stack = mated height + t_fpc + t_stiffener (+ solder
   allowance), as a PROVISIONAL range. Back zone = max(B.Cu governing part height, h_stack) + c_back (+ t_insulator),
   with the B.Cu governing part taken from the scenario (0603 baseline 0.95, or P-0402 0.65 seated). Report the
   T_total delta against G1-S4 and against G1-K2. Derive the **numeric maximum h_stack** that is (a) neutral to K2
   and (b) still compliant with OD-THICK-REVA. Evaluate the pack edge-seal / shoulder zone as a separate
   SUPPLIER_DATA_REQUIRED variant (SR-BATT-PACK). Never assume it is thinner.
2. **Bend geometry.** B.Cu entry: the vertical channel run turns inward into the back zone over the pack top corner.
   Check that the pack corner stays inside the bend hollow, that the flex fits between the pack/insulator and MAIN
   B.Cu, and that it clears B.Cu courtyards. Derive the maximum permissible R_bend per corner. F.Cu entry: reuse
   the G1 edge-crossing model (flat exit / land ceiling, display-land h_max) unchanged.
3. **Radial.** Straight-run channel margin (unchanged by side). The conservative failure (-0.95 mm) is reported
   and handed to G3 with numbers; it is not solved in G2.
4. **XY / azimuth window.** The candidate window lies inside MAIN, avoids live courtyards on the chosen side (read
   from the PCB / height map), carrier pockets (storage, VBAT), SUP_SW / SUP_SE / SUP_NE, GNSS_RAD, BLE_RAD,
   WIFI_RAD, MAG_CLEAR (for current-carrying paths), button windows and the caseback seal band. Each overlap is
   recorded and dispositioned.
5. **Path.** Flex length (excluding the service loop), bend count, MAIN-edge crossings, crossings under the display
   support land (DISP_LAND), annulus arc used, and 5 ATM seal-band / button-bore crossings.
6. **Assembly and service.** Build states S0–S3. Mating access per state; for B.Cu options, the book-fold (MAIN
   mated B.Cu-up, then folded onto the carrier): hinge axis, required fold length and slack location. Re-mate path,
   battery-isolation procedure during development, J1 cycle budget (50 rated / 25 planned).
7. **Routing consequence (estimate only, no routing).** Pad side, via transitions needed, escape region occupancy,
   current-carrying positions, Manhattan length estimate for any new on-board run.

### 5.2 Interface options

| Interface | Options to evaluate | Lead hypothesis | Must establish |
|---|---|---|---|
| J1501 (MAIN end, sensor FPC) | F.Cu (G1 baseline window S) / B.Cu | B.Cu preferred, conditional on the verified connector + FPC + stiffener stack and the battery/channel geometry | 5.1 items 1–7; numeric h_stack and R_bend requirements for SR-FPC-MECH; mirrored-position requirement |
| J1502 (REAR end) | inner-face hot-bar/ACF tail (INNER-TAIL / INNER-0201) / inner-face connector | evaluate both | h_rear_inner per option; service model (J1501 the only demountable joint for a tail); tail exit toward the J1501 azimuth; under-run length |
| J201 (battery) | F.Cu (G1 baseline window S) / B.Cu at the PCM exit azimuth (sweep the plausible SW exit range; actual exit is SR-BATT-PCM) | B.Cu near the actual PCM exit | battery tail length and BATT_TAIL deletion; seal/button crossings; VBAT path to U201; numeric requirements for SR-BATT-PCM |
| J202 (charger entry) | west F.Cu (baseline) / west B.Cu / east B.Cu near the contact block | B.Cu preferred; west vs east traded | harness length; riser azimuth slot vs SW2/SW3/SW5, WIFI_RAD, MAG_CLEAR (X16); edge crossing XC-J202; U1201/D1201 entry-protection relocation requirement; +5V on-board length estimate; seal-band crossing. Frozen charger electrical architecture preserved |
| J1301 (SWD, TC2030-IDC-NL) | retain F.Cu | retain unless evidence changes | access per build state; guide-pin through-board protrusion → B.Cu/carrier relief requirement (SR-TAGCONNECT); no Z change |
| J1 (display BTB, OK-23GF024-04) | retain F.Cu | retain | fold envelope (parametric, SR-DISPLAY-FPC), DISP_LAND interruption, blind-mate order, west crowding after the J202 decision |
| U7 DRV2625 / LRA leads | U7 F.Cu (baseline) / U7 B.Cu with LRA leads terminating on B.Cu | evaluate B.Cu for interconnect simplification | XL-LRA crossing deletion; U7 seated height vs back-zone ceiling; separation of the LRA pocket (az 165–195) from the FPC under-run (az ~152–180) |
| U8 MAX-F10S | retained (no evaluation of relocation or part change) | retained | list of RF verification items (feed C1420/C1421/R1420, GNSS_RAD, display/case shadowing, X17, C8) |
| C901 / C903 | P-0402 (0603 → 0402) | adopt as the Rev-A baseline lever | carry the G1 electrical evidence requirement (DC-bias effective capacitance at 3.0 V / 1.8 V); no schematic/footprint change in G2 |

Also discover and register any further interface or component that materially affects 3-D integration (e.g.
SW1–SW5 switch side and height vs display-land headroom, antenna feeds AE14xx). Record a requirement; do not
expand scope into placement.

## 6. Selection rule (per interface)

An option is **ACCEPTABLE** if every deterministic check passes at nominal and every remaining unknown is
SUPPLIER_DATA_REQUIRED with a numeric acceptance value. Rank acceptable options lexicographically:
1. no frozen-invariant or owner-decision impact;
2. the Rev-A stack meets OD-THICK-REVA (nominal and RSS);
3. fewer MAIN-edge crossings and display-land interactions;
4. fewer 5 ATM seal-band / button-bore crossings;
5. shorter flex and fewer bends;
6. assembly and service robustness;
7. lower routing consequence.

Outcome per interface: RECOMMENDED, CONDITIONAL (names the discriminating supplier value and threshold) or
REJECTED, each with reasons. If the ranking depends on supplier data, keep both options and state the threshold.

## 7. Rev-A stack closure

Using the G1 tolerance policy unchanged (imported, not re-implemented), compute through `tools/g2_interconnect.py`:
- **G2-K2-REF:** reproduces G1-K2 exactly (16.080 / 16.525 / 17.740). This is a cross-check that must pass.
- **G2-REVA:** the Rev-A baseline. P-0402 + the J1502 option chosen in 5.2 + the side allocation chosen in 6, with
  connector stacks at their PROVISIONAL ranges. Report nominal, RSS, linear worst and T_body (h_pod 0.8).
- **G2-REVA-HI:** the same, with every connector stack at its range maximum.

Compliance with OD-THICK-REVA (nominal <= 16.5 AND RSS <= 17.0) is computed by the tool, using only
CREDIBLE_LATER_TASK levers. SUPPLIER_DATA_GATED and OWNER_DECISION_GATED levers may be reported as Rev-B options
but are never counted. Linear worst is reported, not required.

## 8. Package updates

- `architecture.md`: new section **G2** containing the allocation table, a per-interface option table with
  evidence classes, the Rev-A stack table, the assembly/service sequence (S0–S3, book-fold), the RF verification
  list for U8, and a conflict status table. Make consistent updates to sections G, H, I, J, 12–15.
- `architecture.json`: a `g2` block (allocation, options, stack, assembly); reservations for the chosen B.Cu
  windows and flex corridors (class PARAMETRIC); every conflict gains exactly one `g2_status` (RESOLVED_BY_G2 /
  REMAINS_OPEN / SUPPLIER_DATA_GATED / DEFERRED_G3 / OWNER_DECISION_GATED) with evidence; new conflicts registered.
- Supplier requests amended with **numeric** requirements: SR-FPC-MECH (max h_stack incl. FPC + stiffener, max
  R_bend, pitch class, per-position current for PPG_VLED, exit orientation, tail process), SR-BATT-PCM, SR-BATT-PACK
  (edge seal), SR-CHG-MECH, SR-TAGCONNECT, SR-LRA, SR-BUTTONS, SR-DISPLAY-FPC. Drafted / issue-ready only; the owner
  issues them.
- Next-gate renumbering in section 15 / `next_gate`: G3 = REAR optical + guarded-analog placement study; G4 = case
  + final MAIN outline co-design; plus a KiCad placement-implementation phase for the G2 allocation, with entry
  criteria. Nothing is authorized by this renumbering.
- Fix the G1 documentation residue: the C1-FRONT-GAP g1_status evidence (architecture.md and architecture.json)
  quotes the superseded U8 bound "max centre radius 15.93". Replace it with the valid pair (18.00 < 21.95) from G1.3.
- `README.md` updated for the new tool and outputs.

## 9. Validation (all must exit 0)

```
python3 -B design/mechanical/tools/mech_model.py check
python3 -B design/mechanical/tools/g1_scenarios.py check
python3 -B design/mechanical/tools/arch_diagrams.py check
python3 -B design/mechanical/tools/g2_interconnect.py check
git diff --exit-code 168badbab6de1201bb3209902a53fe1e4b874cc9 -- design/mechanical/inputs/stack_parameters.json design/mechanical/inputs/package_heights.json design/mechanical/inputs/g1_scenarios.json design/mechanical/tools/mech_model.py design/mechanical/tools/mech_model_spec.md design/mechanical/tools/g1_scenarios.py design/mechanical/generated/zstack.md design/mechanical/generated/zstack_section.svg design/mechanical/generated/main_height_map.md design/mechanical/generated/main_height_map.svg design/mechanical/generated/g1_scenarios.json design/mechanical/generated/g1_scenarios.md
git diff --exit-code 168badbab6de1201bb3209902a53fe1e4b874cc9 -- '*.kicad_pcb' '*.kicad_sch' '*.kicad_pro' '*.kicad_prl' design/interfaces design/placement rear_sensor libraries
python3 -B -c '<semantic provenance check, see below>'
git diff --check
```

Validation rules:

- **A. Byte-identity.** Every G1-immutable file OTHER than `generated/zstack.json` and
  `generated/main_height_map.json` must remain byte-identical to `168badb` (the first `git diff`).
- **B. Semantic provenance check.** `generated/zstack.json` and `generated/main_height_map.json` are
  NOT removed from validation. For each of them, the check loads the file from commit `168badb`
  (`git show`) and the current working-tree JSON, normalizes ONLY
  `inputs_sha256["design/mechanical/inputs/input_register.json"]` (set to a fixed sentinel in both),
  and fails if any other semantic difference exists. Every other JSON field — all calculated
  geometry, thickness values, tolerances, component counts and scenario results — must compare
  equal. The check:

  ```python
  import json, subprocess, sys
  BASE = "168badbab6de1201bb3209902a53fe1e4b874cc9"
  REG = "design/mechanical/inputs/input_register.json"
  FILES = ["design/mechanical/generated/zstack.json",
           "design/mechanical/generated/main_height_map.json"]
  def normalize(doc, path):
      hashes = doc.get("inputs_sha256")
      if not isinstance(hashes, dict) or REG not in hashes:
          sys.exit("FAIL: %s lacks inputs_sha256[%s]" % (path, REG))
      hashes[REG] = None  # the one provenance-only field, exempt from comparison
      return doc
  bad = []
  for path in FILES:
      old = json.loads(subprocess.run(
          ["git", "show", BASE + ":" + path],
          capture_output=True, check=True).stdout)
      with open(path) as fh:
          new = json.load(fh)
      if old != new and normalize(old, path) != normalize(new, path):
          bad.append(path)
  if bad:
      sys.exit("FAIL: vs " + BASE + " only inputs_sha256[input_register.json] may differ in: "
               + ", ".join(bad))
  print("PASS: zstack.json / main_height_map.json differ from " + BASE
        + " only in inputs_sha256[input_register.json]")
  ```

- **C. After regenerating the two provenance records** (section 4: `mech_model.py heights` and
  `mech_model.py stack` run once after OD-THICK-REVA is recorded),
  `python3 -B design/mechanical/tools/mech_model.py check` must exit 0. This also proves the new
  register hash is the correct current one.
- **D.** All G1 numerical/model outputs remain identical: this follows from B (normalized equality
  with `168badb` covers every numeric field) plus C (the working tree equals a fresh regeneration
  from the current inputs).
- **E.** KiCad/interface/placement immutability is unchanged, including `*.kicad_prl` (the second
  `git diff`).

`arch_diagrams.py check` is extended so that every G2 number quoted in `architecture.md` / `architecture.json` is
checked against `generated/g2_interconnect.json`, and every conflict carries exactly one `g2_status`.
`g2_interconnect.py check` regenerates its outputs, fails on any byte difference, and fails if G2-K2-REF does not
reproduce G1-K2.

## 10. Acceptance criteria

1. OD-THICK-REVA is recorded verbatim in `input_register.json`. All previous owner decisions and frozen invariants
   are unchanged; the 24-position / 13-net interface file is unchanged.
2. Every interface in 5.2 (plus any discovered in-scope interface) has exactly one outcome per option
   (RECOMMENDED / CONDITIONAL / REJECTED), and a final side, XY/azimuth window, mating direction, exit direction,
   flex path, mated Z range, bend count and flex length. Each value carries an evidence class.
3. Each outcome follows from the tool outputs under the section 6 rule. No lead hypothesis appears as an input
   constant or a hand-typed verdict.
4. For every chosen B.Cu connector: numeric max h_stack (K2-neutral and OD-THICK-REVA-compliant), numeric max
   R_bend, a book-fold assembly sequence with fold length, and the mirrored-position requirement are stated.
5. Each rear-to-front conductor (sensor FPC, battery, charger, LRA) either has its MAIN-edge crossing deleted, or
   has a positive nominal margin with the stated exit requirement. Display-land interactions are listed.
6. G2-K2-REF reproduces G1-K2 exactly. G2-REVA meets nominal <= 16.5 and RSS <= 17.0 using CREDIBLE_LATER_TASK
   levers only. G2-REVA-HI is reported, and its compliance or non-compliance is stated, not hidden.
7. U8 stays on F.Cu / north with no part change, and the RF verification list is recorded. P-0402 is adopted
   with its electrical evidence requirement.
8. Every conflict carries exactly one `g2_status` with evidence; new conflicts are registered. The conservative
   radial failure and X25 are handed to G3/G4 with numbers.
9. The supplier requests in section 8 carry numeric acceptance values and are drafted / issue-ready. No supplier
   dimension is invented.
10. All section 9 commands exit 0, including the semantic provenance check. G2 generated files
    regenerate byte-identically. Every G1-immutable file OTHER than `generated/zstack.json` and
    `generated/main_height_map.json` is byte-identical to `168badb`; those two differ from `168badb`
    only in `inputs_sha256["design/mechanical/inputs/input_register.json"]`, `mech_model.py check`
    exits 0 after their provenance regeneration, and all G1 numerical/model outputs are identical.
    The KiCad files and the interface/placement trees are unchanged. Changes stay inside
    `design/mechanical/**`.
11. The C1-FRONT-GAP "15.93" residue is fixed.

## 11. Stop conditions

- An option needs a frozen invariant, an owner-decision reversal, a KiCad edit, a schematic change, an interface
  change or a GNSS part change: record OWNER DECISION REQUIRED for that option and continue the rest.
- No allocation meets OD-THICK-REVA with credible levers: finish the package with verdict **REV-A STACK OWNER
  DECISION REQUIRED**, show the tradeoff, and stop. Never weaken a requirement.
- A required input is missing or contradictory, or the live state disagrees with this brief: stop and report.
- A G1-immutable file other than the two provenance-only JSONs would have to change, or either of
  `generated/zstack.json` / `generated/main_height_map.json` would have to change in any field other
  than `inputs_sha256["design/mechanical/inputs/input_register.json"]`: stop and report.
- A deterministic check fails and cannot be fixed inside scope: stop and report.

## 12. Independent review must challenge

- Re-derive independently the B.Cu back-zone interaction for J1501/J201/J202 against G1-S4 and G1-K2, and the
  pack-corner bend geometry.
- Whether any outcome was hard-coded from a lead hypothesis rather than computed under section 6.
- Whether any supplier or manufacturer value was invented, or a parametric nominal set to its best case.
- Whether the book-fold assembly is physically achievable with the stated fold length and build states, including
  battery isolation during development.
- Fairness of the J202 west/east trade (X16 magnetometer, Wi-Fi, seal band, entry protection).
- G2-K2-REF reproduction, and the RSS / credible-lever-only compliance computation.
- Immutability of the G1 record, KiCad files and the 24/13 interface. No change to PPG / electrical boundaries.

## 13. Not in G2

KiCad edits of any kind (footprints, moving parts, Edge.Cuts, zones, routing); schematic or BOM changes; MPN
selection or purchase; REAR optical placement (G3); case CAD, final MAIN outline and sealing-stack design (G4);
GNSS part change; revoking any owner decision; issuing supplier requests externally; Rev-B thickness optimization
beyond reporting gated levers.
