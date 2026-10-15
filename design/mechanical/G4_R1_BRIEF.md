# G4-R1 brief — CASE / SEAL / SUPPORT BLOCKER-RESOLUTION STUDY (Rev-A)

Status: phase contract finalized with owner decisions OD-G4R1-ENTRY, OD-G4-WINDOW and OD-G4-ASSEMBLY (approved
2026-10-15). G4-R1 is provisional, reversible, deterministic mechanical study work. It authorizes **no KiCad edit**,
no RF claim, no 5 ATM / structural / optical / adhesive qualification claim, no MPN selection, no supplier claim, no
supplier-request issuance, no case CAD and no later phase (G5, K1, Q1). It does not reopen G1, G2 or G3 and it does
not amend `G4_BRIEF.md`, which stays immutable. This brief is the scope contract for G4-R1. Destination:
`design/mechanical/G4_R1_BRIEF.md`. Work branch (created by the lead from the contract commit):
`mechanical/g4-r1-blocker-resolution`.

Baselines (accepted evidence, read-only):

- G1 `168badbab6de1201bb3209902a53fe1e4b874cc9` (immutable);
- G2 `eea49e447895e574a3f48e0b9777f57880dcd632` — "G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES";
- G3 `afb19ac173ce67c7e9599313cc5a0942e026ade9` — "G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES", selected
  candidate **G3-B-S14**;
- G4 contract `935da5ca737ce4cd5b9a2e1245c7d48c8104a592` (`G4_BRIEF.md`);
- **G4 blocked study `00e77cbe107a79ac05194f19b674f7ab8d5941c9`** — "G4 OWNER DECISION REQUIRED — BLOCKED /
  UNRELEASED STUDY", independent review PASS AS CORRECT BLOCKED STUDY. Its generated files are the numeric starting
  point, are pinned by SHA-256 and are never re-typed.

Phase 1, G1, G2, G3 and G4 rules apply except where this brief explicitly changes scope.

## 1. Objective

Convert the G4 blockers into either (a) a deterministic geometric resolution inside the frozen G2 stack and the frozen
G3-B-S14 REAR placement, or (b) an isolated, **quantified** owner / supplier / architecture gate with a numeric
threshold. R1 is not a re-run of G4: it adds only the degrees of freedom the blocked study did not search and the
contract clarifications of section 4, and it reports every result beside the unchanged G4-literal result.

R1 is organised in independent **lanes**; a lane that fails does not invalidate another lane.

| Lane | Blocker (G4 ids) | R1 question |
|---|---|---|
| L-WIN | OD-G4-WINDOW, H12 | Does W1 at 0.50 mm hold as the Rev-A baseline with zero Z delta and a valid rib/frame load path? |
| L-BTN | H21, H15 (buttons), H03 | Is there a local button topology whose gland, bore and boss geometry close without moving a switch? |
| L-SEAL | H14, H15, H16, X21 | Which seal topology per aperture is geometrically feasible at linear worst? |
| L-CHG | H20 | Do the 4 x 5 mm contact block and its bond/seal land close under the clarified containment? |
| L-STR | H13, X20, X22 | Is there a manufacturable caseback support / stiffening topology that bypasses PCB, battery and G3 support lands? |
| L-RAD | H05, H06 | Which radial terms close geometrically, separately from LRA coupling? |
| L-ASM | H23, C2 | Is the display-before-cover sequence executable with an access direction for every operation? |
| L-LRA | H22, STOP-LRA | What is the largest REAR-level envelope, and is the OD-G4-LRA-ARCH trigger met? |

## 2. Owner decisions (authoritative)

### 2.1 In force and unchanged

All decisions of `G4_BRIEF.md` sections 2.1 and 2.2 (OD-G4-RECORD, OD-G4-ENTRY, OD-G4-ENVELOPE, OD-G4-CORNER) and
everything they carry remain verbatim and unreinterpreted. R1 uses `<= 51.0 mm`, `+1.0 mm` button bosses, design value
+ declared tolerance for G4-designed dimensions, and no speculative credit of any kind.

### 2.2 New for G4-R1 — APPROVED by the owner 2026-10-15

Record them verbatim in `generated/g4_r1_blockers.json.owner_decisions` (date 2026-10-15, source: owner decision,
G4_R1_BRIEF.md section 2). They are not recorded in `input_register.json`, `architecture.json` or `README.md` by R1.

**OD-G4R1-ENTRY — APPROVED — 2026-10-15**

Authorize:

G4-R1 — CASE / SEAL / SUPPORT BLOCKER-RESOLUTION STUDY

with lanes:

L-WIN, L-BTN, L-SEAL, L-CHG, L-STR, L-RAD, L-ASM, L-LRA

and the contract clarifications / stop conditions C-R1-01…C-R1-09 defined by the technical-lead draft (finalized in
sections 4 and 12 of this brief).

G4-R1 does NOT authorize:
- G5;
- K1 / KiCad;
- G1 / G2 / G3 reopening;
- qualification;
- supplier claims;
- body diameter > 51.0 mm;
- nonzero stack growth without OD-G4-STACK;
- movement of frozen G3-B-S14 placements.

Any such requirement is a STOP.

**OD-G4-WINDOW — APPROVED — 2026-10-15**

Use:

W1 — rib/frame-supported window

as the Rev-A mechanical baseline.

Planning nominal thickness:

0.50 mm

This must preserve zero G4 Z delta.

0.30 mm sapphire remains an optimization / Rev-B lever only and is not credited to Rev-A closure.

Material and supplier qualification remain open.

No structural, optical, adhesive or 5 ATM qualification is implied.

W0 remains rejected under current Rev-A thickness constraints. W2 remains rejected under current seal-land geometry.

**OD-G4-ASSEMBLY — APPROVED — 2026-10-15**

Rev-A assembly clarification:

The display is mated and seated from the open front before the cover is bonded.

This supersedes the prior cover-first ordering only where the latter conflicts with the continuous display support
land.

No allocation, stack, placement or architecture change is authorized.

SERVICE-COVER-REBOND remains OPEN.

### 2.3 Not decided here (engineering resolves, or evidence first)

- **OD-G4-LRA-ARCH is not decided and is not asked now.** R1 raises it only through the stop of section 9.8.
  R1 never chooses among its options.
- OD-G4-ATM-STD, OD-G4-MATERIAL, OD-G4-STRAP, OD-G4-LRA-MAG remain closure decisions with the G4 PROVISIONAL
  defaults. R1 results are inputs to OD-G4-MATERIAL on mechanical / sealing / keep-out / magnetic criteria only and
  stay conditional on G5; no family is recommended on an RF argument.
- OD-G4-STACK is not triggered; R1-S05 stops on any nonzero total Z need.

## 3. Frozen carry-ins (do not change)

Everything in `G4_BRIEF.md` section 3 (G2 allocation and stacks, G3-B-S14 through the pinned
`generated/g3_rear_optical.json.g4_handoff`, legacy numbers -0.950 / -1.100 / ...) plus:

- G2-REVA 16.350 / 16.796 / 18.040 and G2-REVA-HI 16.380 / 16.825 / 18.040 mm (nominal / RSS / linear worst); total
  Z delta 0.000 / 0.000 / 0.000; window delta 0.000 at 0.50 mm;
- G3-B-S14 REAR placement, faces, rotations, outline r 16.400 mm, pod polygon, support lands at azimuth 30 / 150 / 270,
  J1502 tail exits, U6 island and F1/F2/F3, frozen plan clearances CHG_CONTACT 1.100, CHG_LINK 3.600, CHG_ROUTE
  0.600 mm: **completely frozen**; no G3 reopening, no support-land enlargement claimed;
- MAIN placement and the five switch windows (SW1 292.5-307.5, SW2 262.5-277.5, SW3 232.5-247.5, SW4 52.5-67.5,
  SW5 112.5-127.5 deg): **switches remain frozen**;
- CHG_CONTACT reservation (az 80-100, r 17.5-24.0), separate charger architecture, charger contacts rear east
  GND/+5V/+5V/GND, no watch-side permanent magnet, 24-position / 13-net interface;
- radiator volumes GNSS_RAD, BLE_RAD, WIFI_RAD and MAG_CLEAR as hard keep-outs;
- O-ring planning windows (static radial / static face 15-30 %, dynamic radial 10-20 %, fill <= 0.85) and the
  +/-0.05 mm cross-section tolerance: **not widened, not narrowed**;
- every G4-literal result at `00e77cb`, reproduced exactly (R1-H03).

Anything that needs one of these changed is OWNER DECISION REQUIRED or a STOP, never an R1 result.

## 4. Contract clarifications (R1-only; G4_BRIEF.md unchanged)

Each clarification is reported as a side-by-side column "G4-literal" vs "R1". A clarification never converts a
supplier-gated value into a credit, and never changes a G4 historical result.

**C-R1-01 Charger containment.** The G4 brief (section 8.8, H20) places the *contact block* in the CHG_CONTACT
placeholder (az 80-100, r 17.5-24.0; "block width and depth unknown") and requires block, feedthrough and corridors
"clear". The G4 tool additionally required the whole continuous bond/seal land to lie inside the same 2-D wedge; that
is a G4 modeling assumption (`CHARGER_CONTAINMENT_ASSUMPTION`), not brief text. For R1:

1. the conductive 4 x 5 mm contact block lies inside the authorized wedge, inside the radial bounds
   `r_S14_outline + 1.100 <= r <= r_lim - c_chg_window`, and clear of WIFI_RAD (H17);
2. the **non-conductive** bond/seal land is a caseback-side feature. It need not lie entirely inside the wedge if and
   only if it (i) carries no conductive material, (ii) stays on the caseback side (no REAR-level Z intrusion), (iii)
   stays outside the S14 outline plus 1.100 mm and outside the pod seal land, (iv) stays >= 1.0 mm (report class
   `rf_clearance_report`) from every radiator volume, (v) clears screws, supports, CHG_ROUTE and CHG_LINK in plan and
   in Z, and (vi) clears every neighbouring functional structure (switch bores/bosses, vent, lug and support
   features);
3. the side overshoot beyond a wedge side is **numerically bounded by the contract**: at most 0.75 mm measured
   perpendicular to the wedge side, and the land never leaves the azimuth interval 78.0-102.0 deg. These caps are
   containment bounds, not credits; the result must lie inside them and is reported with margin. (G4 lead arithmetic:
   0.45 mm / about 1.4 deg per side for orientation 0 at G4-A/C limits.)
4. the **strict-wedge** result (land fully inside the wedge) is retained as a diagnostic and as the supplier path:
   R1 reports the largest land width that fits the wedge (lead arithmetic 0.674 mm A/C, 0.589 mm at the G4-B radial
   limit) as the SR-CHG-MECH threshold.

Block size 4 x 5 mm and the land range 0.5-1.0 mm (adverse 1.0) stay PROVISIONAL and are never reduced.

**C-R1-02 Button bore requirement.** `L_bore_min` (PROVISIONAL 1.5-3.0 mm, adverse 3.0) is a blanket planning range
for "pusher seal and guidance". R1 evaluates the bore against an **enumerated stack** for the topology under test
(guide land x 2 at adverse 0.4, groove / rim / flexure width at its own tolerance, stroke at adverse 0.4, wiper or stop
shoulder), every term at its adverse planning value. The blanket 3.0 mm is reported as a legacy column with its
zero-margin threshold; it is never deleted or replaced by a range chosen to pass (OD-G4-CORNER).

**C-R1-03 MAIN-edge gap (reviewer adjudication).** G4 stacks `c_main_case_mm` (MAIN outline to case bore, adverse 0.2)
and `c_switch_mm` (actuator overhang + travel "beyond the MAIN edge to the inner bore face", adverse 0.4) **in
series**. They may bound the same physical gap. Neither term is removed from any output. The implementer **must
evaluate and report both interpretations for every button check that contains them**:

- **I-SUM** (G4-literal, default binding): `R_main + tol_pcb_outline + c_main_case + c_switch + tol_bore_r`;
- **I-MAX**: `R_main + tol_pcb_outline + max(c_main_case, c_switch) + tol_bore_r`.

Disposition rule: a button lane PASS under both is `RESOLVED_GEOMETRICALLY`; a PASS under I-MAX only is
`RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED` and is not counted as closed. The adjudication is
carried as `inputs/g4_r1_blockers.json.c_r1_03_adjudication` (`null` / `"SUM"` / `"MAX"`; default `null`), set only by
a reviewed input change after the independent reviewer rules; it selects the binding column but never hides the other.
Expected effect of I-MAX: +0.20 mm on the bore stack, not sufficient alone (section 6.2).

**C-R1-04 Azimuth-resolved wall.** G4 used one scalar side-wall `tw` per design point (recorded model limitation).
R1 solves `t_wall(az)` as bulk `tw` plus local arcs over the existing corridor reservations (FPC_CORR 152.6-179.5,
BATT_TAIL 181.3-236.6, CHG_RISER 249-259 deg) down to `t_wall_min(max) + tol_bore_r + tol_od_r`. No credit below
that floor; side-wall pressure/hoop screening at p max is reported for every thinned arc.

**C-R1-05 Seal inventory.** Topology classes are extended: face O-ring caseback seal, elastomer boot / bonded
diaphragm, case-integral flexure, insert-moulded or bonded sealed feedthrough. No MPN, no supplier capability,
windows and tolerances unchanged.

**C-R1-06 Assembly order.** Per OD-G4-ASSEMBLY, and **only** where cover-first conflicts with the continuous display
support land: A7 (display mated at J1 through the open front and seated on DISP_LAND) precedes A8 (cover bonded to
the bezel ledge). Every other step, direction and battery state of the G4 sequence is unchanged. SERVICE-COVER-REBOND
remains open and is reported as a consequence (display replacement requires cover removal and re-bond).

**C-R1-07 G4-C re-authoring.** P2 (pod frame on the REAR module) routes window pressure through the REAR board and
is retired by X20 with its radial S-POD-FRAME seal. R1 may carry a **G4-C1** fallback: P1 pod frame integral with a
non-ferromagnetic metal centre plate confined to `r <= r_radiator_inner - 1.0 mm`, polymer outer ring retained
mechanically and bonded. G4-A and G4-B definitions are unchanged.

**C-R1-08 LRA lane semantics.** An envelope class defined by the threshold it must meet is circular and is never a
PASS and is never authored. LRA lane PASS requires an authored class (G4 section 8.9 classes) or a class supplied in
`inputs/g4_r1_blockers.json.lra_supplied` with a local primary document and page / table / figure, that fits a pose
at the current G2 allocation. R1 does not move the LRA to another Z allocation.

**C-R1-09 Historical checker handling.** See section 5.1. No accepted G4 engineering logic, input, generated file or
checker file is modified.

## 5. Scope, files and historical reproducibility

R1 owns deterministic mechanical study only. It does not own: KiCad (Edge.Cuts, footprints, placement, zones,
stackup, routing); schematic, BOM, nets, interfaces; case CAD / STEP; MPN selection; supplier-request issuance;
antenna / feed design; RF simulation; FEA execution (R1 specifies load cases only); physical qualification; moving
any switch, J202 or U8; any G2/G3 placement or allocation; any change to `G4_BRIEF.md`.

**New files — exact set (`R1_FILES`):**

| Path | Role |
|---|---|
| `design/mechanical/G4_R1_BRIEF.md` | this contract (lead; immutable after its commit) |
| `design/mechanical/inputs/g4_r1_blockers.json` | authored R1 variables, grids, evidence classes, pins, `c_r1_03_adjudication`, `lra_supplied`; inputs, never results |
| `design/mechanical/tools/g4_r1_blockers.py` | stdlib-only; sub-commands `build`, `check`, `selftest`; imports `g4_case_sealing` as a library, re-implements nothing |
| `design/mechanical/generated/g4_r1_blockers.json` | authoritative result, <= 2 MB |
| `design/mechanical/generated/g4_r1_blockers.md` | report |
| `design/mechanical/generated/g4_r1_plan.svg` | plan: wall map, ribs, split plate, charger block + land + wedge, bosses, LRA envelope, keep-outs |
| `design/mechanical/generated/g4_r1_sections.svg` | sections: button (T2 / T3), caseback rib / plate, charger feedthrough |
| `design/mechanical/generated/g4_r1_sweep.jsonl` | **optional**: only if `g4_r1_blockers.json` would exceed 2 MB; one canonical object per line, sorted |

**May modify:** nothing. In particular R1 does **not** modify `architecture.md`, `architecture.json`, `README.md`,
`tools/arch_diagrams.py`, `tools/g4_case_sealing.py` or any generated G4 / G3 file. The state record
(architecture / README summary, "R1 recorded" lines) is a later lead commit after independent review, as OD-G4-RECORD
was for G3.

**Immutable (byte-identical to `00e77cb`):** every file immutable under `G4_BRIEF.md` section 4.3; `G4_BRIEF.md`;
`inputs/g4_case_sealing.json`; `tools/g4_case_sealing.py`; every `generated/g4_*` evidence file;
`architecture.md`; `architecture.json`; `README.md`; `tools/arch_diagrams.py`; `tools/g3_rear_optical.py`.

**May not modify:** anything outside `design/mechanical/`; `*.kicad_pcb`, `*.kicad_sch`, `*.kicad_pro`,
`*.kicad_prl`, footprint or symbol libraries; `design/interfaces/**`, `design/placement/**`, `rear_sensor/**`,
`libraries/**`, firmware, scripts, docs.

Generated files are written only by the tool and regenerate byte-identically: sorted keys, fixed float formatting,
compact separators `(",", ":")`, no timestamps, final newline. G3 / G4 data are read through pinned hashes, never
re-derived inside the R1 tool; the long G3 check is not re-run inside it.

### 5.1 C-R1-09 — handling of the historical G4 write-scope check (prospective only)

Facts established at `00e77cb`:

- `tools/g4_case_sealing.py` `scope_check()` requires every path changed since the G4 brief commit, plus every
  untracked `design/mechanical/` path, to be a member of the hard-coded set `ALLOWED_CHANGES`; any path outside
  `design/mechanical/` fails `nothing_outside_design_mechanical`. Therefore **any** R1 path — including this brief —
  makes the literal `python3 -B design/mechanical/tools/g4_case_sealing.py check` fail on scope once it exists,
  committed or not.
- The tool's own SHA-256 and the `G4_BRIEF.md` SHA-256 are embedded in
  `generated/g4_case_sealing.json.source_sha256`, which is pinned again in `architecture.json.g4`. **Editing
  `tools/g4_case_sealing.py`, even only its `ALLOWED_CHANGES` literal, would change the G4 generated evidence bytes and
  the architecture summary.** A source edit of the accepted G4 tool is therefore **not permitted** and is not the
  C-R1-09 mechanism.

Contract mechanism (the minimum harness change; no accepted file is edited):

1. The literal historical check is reproduced against the **pinned baseline**: a read-only detached checkout of
   `00e77cb` (for example `git worktree add --detach <scratch>/g4_baseline 00e77cbe107a79ac05194f19b674f7ab8d5941c9`,
   removed afterwards). `g4_case_sealing.py check` and `selftest` must exit 0 there (selftest 32/32). That is the
   historical-reproducibility proof and needs no allow-list change at all.
2. `g4_r1_blockers.py check` additionally performs an **in-process prospective allow-list extension**: after
   importing `g4_case_sealing` it sets `g4_case_sealing.ALLOWED_CHANGES |= R1_FILES` (the exact paths of the table in
   section 5, nothing else, no wildcard, no other module attribute patched) and calls the G4 module's own `check` and
   `selftest` entry points. Required outcome: exit 0, all seven G4 generated files byte-identical to the committed
   files, selftest 32/32.
3. The extension is **prospective only**: it adds names that did not exist when G4 was accepted, takes effect only
   inside the R1 process, never rewrites a file, and cannot change a historical G4 engineering result because the
   scope result is a set of booleans that is identical for the baseline file set (`since <= ALLOWED_CHANGES` stays
   true for every pre-R1 path).
4. The literal command in the R1 working tree is **expected to be red**; its failure must be fully explained by the
   scope result (the in-process run of item 2 is green and byte-identical). This is the same documented class of
   later-phase incompatibility as the G3 scope check (the G3 check passes only on a clean tree). A red literal check
   caused by anything else is a failure of R1.
5. A later lead decision may, by its own reviewed contract, replace this mechanism (for example by a controlled
   regeneration of G4 evidence). R1 does not do that and does not propose it.

## 6. Strategy per lane

### 6.1 L-WIN — window (OD-G4-WINDOW)

Carry W1 only, `t_window` 0.50 mm nominal / 0.45 mm minimum, material classes sapphire and chemically strengthened
glass; polycarbonate is reported eliminated at 0.50 mm (stress 24.0 vs planning 20 MPa). W0, W2 and the 0.30 / 0.80 mm
rows are reproduced from G4 and reported, never re-opened; 0.30 mm sapphire is a Rev-B lever and is not credited.
R1 additionally checks: rib width fits the frozen S14 inter-cell webs (read from the pinned G3 handoff), window bond /
seal land >= 0.3 mm (G3 minimum), rib load goes to the pod frame and caseback and never to optics or the REAR board
(X20). Z delta 0.000. No supplier-qualified allowable, optical, adhesive or 5 ATM claim is made.

### 6.2 L-BTN — buttons

G4 facts (00e77cb): bore margin at linear worst -0.480 (G4-A / G4-C, all five), -0.410 SW1-SW4 and -0.480 SW5
(G4-B); zero-margin `L_bore_min` 2.52 / 2.59 mm; bore-only closure by diameter would need D >= 51.9 mm. The axial
gland-plus-guide stack already passes (+0.30 to +0.51 mm), so the bore blocker is the blanket 3.0 mm, not physical
length. The H15 certificate fails every authored cross-section at +/-0.05 mm.

Lead arithmetic (read-only, formulas of `gland_design` / `pusher_gland`): with a 10-20 % dynamic window and +/-0.05 mm
cross-section tolerance, a dynamic radial pusher O-ring needs `cs >= 1.69 mm` at the metal-class groove/bore stack
(0.04), `>= 2.29` at 0.07 and `>= 2.89` at 0.10; Ø1.6-2.0 mm pushers cannot carry such a ring. The impossibility is a
**topology** result, not a grid artifact and not a supplier tolerance request.

Topologies carried per button:

- **T1** dynamic radial O-ring on the pusher — **regression / reference only**, expected FAIL; never selectable;
- **T2** rigid plunger in an **unsealed** guide bore plus an elastomer boot / bonded diaphragm whose rim is a static
  face or bonded seal on the boss; no dynamic squeeze window;
- **T3** metal case-integral flexure web (non-ferromagnetic metal midcase only, SW1-SW4); no sliding part, no seal.

Design variables: pusher diameter `d_p` — a DESIGN variable **only inside the existing switch windows** (boss
transverse extent must lie inside the frozen azimuth window at the evaluated D; the 1.6-2.0 mm planning range stays
as a legacy column); boss extension; rim land; local wall; boot / flexure free height. Hard geometry: guide stack
(C-R1-02, both C-R1-03 interpretations), plunger core, boss transverse wall, rim land >= bond-land planning minimum,
strain screen, stroke >= `c_switch` adverse (buttons physically actuate through travel), boss + tolerance <= 1.0 mm
including any boot protrusion, SW5 plunger and boot non-conductive (WIFI_RAD), SW4 non-ferromagnetic (MAG_CLEAR),
SW1 conductive parts outside BLE_RAD, bore clear of the rear-insertion path. **Switch positions are never moved.**
Boot life, force, stroke curve, permeation and flexure fatigue are SUPPLIER_DATA_REQUIRED (SR-BUTTONS) with
R1-computed numeric thresholds; R1 claims none of them. If no topology closes for a button inside its window and
boss limit, that is R1-S03, never a switch move.

### 6.3 L-SEAL — sealing

- **Caseback main seal: face O-ring baseline** in a caseback-flange groove. Lead arithmetic at +/-0.05 mm and the
  15-30 % static window: face passes at `cs >= 0.9 mm` (groove-depth tolerance 0.02) / `>= 1.0 mm` (0.03); the
  radial spigot topology needs `cs >= 1.08-1.88 mm` and 1.3-1.9 mm of spigot height (Z fails). Adhesive ring
  (non-serviceable) is kept for comparison; radial is regression only. Plate deflection between screws is not modeled
  and is carried as an FEA load case, not credited.
- **Buttons:** T2 boot / diaphragm or T3 flexure (L-BTN).
- **Charger feedthrough:** FT-A adhesive ring (reference), FT-B insert-moulded block in a polymer caseback, FT-C
  bonded sealed body in a ceramic / metal caseback; a compressed charger face seal stays out of the inventory.
- **U6-F3:** conditional; a radial ring is impossible at zero tolerance; F1/F2 retained; F3 only with a face /
  bonded flange topology, otherwise reported eliminated.
- **S-POD-FRAME (P2):** retired with P2 (C-R1-07).
- Seal-path closure graph, exactly one primary seal per aperture, screws outside the seal line or separately sealed.

No supplier capability, gasket performance or MPN is invented; every gland result stays a PROVISIONAL PLANNING
LIMIT result and ATM-Q1…Q6 stay open.

### 6.4 L-CHG — charger

G4 facts: H20-RECT-90 -0.846 (A/C) / -1.417 (B); orientation 0 radial margin +0.349 (A/C) / -0.221 (B, radial
topology), centre containment -2.548. Lead arithmetic: the block alone passes by +2.21 mm; the 1.0 mm adverse land is
containable in the 20-degree wedge only up to 0.674 mm (A/C) / 0.589 mm (B); with the land at 1.0 mm the rectangle
overshoots the wedge sides by about 0.45 mm per side, at the inner corners only. Orientation 0 (4 mm radial x 5 mm
tangential) is the only radially possible orientation. G4-B's lower outer limit (23.34 mm) comes from the radial
caseback seal topology; with the face seal it equals G4-A's. C-R1-01 governs containment; the strict-wedge result and
its supplier threshold are always reported.

### 6.5 L-STR — structure and load path (H13, X20, X22)

G4 facts: pressure partition 1168.99 N at 0.625 MPa (window 257.5, frame 30.2, caseback remainder 881.3 N), PCB load
0.000 N; perimeter reaction PASS (bearing 39.9 mm² vs 16.7 mm² required, 14.6 vs 35 MPa planning). The failing
mechanism is **plate bending** between pod frame and perimeter: bypass screen 336 MPa / 2.62 mm (polymer) and
623 MPa / 0.283 mm (ceramic) against planning allowables of 35-150 MPa and a 0.05-0.15 mm REAR clearance.

Required Rev-A load path and primary study: **window / frame -> stiffened caseback -> midcase rear-face bearing
(>= 3, nominally 4 lug-root screws) -> case-side supports -> midcase.** The pressure load must bypass the battery,
the REAR PCB and the frozen G3 support lands: R1 assigns zero pressure to them, and no rib, post or plate land may
bear on them or on the carrier lower web (`c_rib_top >= 0.10 mm`). Studied topologies: integral ribs (spokes and
rings) in the REAR-periphery Z band outside S14 outline + 1.1 mm; case-side supports; an allowed metal centre plate
confined below the radiator inner radius; the **G4-C1 fallback** of C-R1-07. A case-side *inward* shelf is not
carried: it would block rear insertion of the module. Structural feasibility is credited only after the numeric checks
R1-H08 … R1-H10 pass; a passing screen is never a qualification.

Variables: spoke count, ring count / radius, rib width / height, plate `t_in` / `t_out`, split radius (C1), caseback
material class. Surrogate: smeared stiffness `D_eff = D_plate + E I_T / s(r)` with effective flange
`b_f = min(s, w_rib + 12 t)`; the imported annular-plate solution with `t_eq`; rib and plate fibre stresses from the
composite section; stress-concentration factor 2.0 (PROVISIONAL, reported); split-plate bond shear
`tau = q_line / w_bond`. Numbers are planning screens; FEA-1…FEA-4 (Q1) govern. Stiffening that needs a caseback
thicker than the REAR-periphery residual is a Z delta -> R1-S05. If no topology passes at planning allowables the
lane reports the required equivalent thickness and stops (R1-S07).

### 6.6 L-RAD — radial / H05 (reported in separate groups, never blended)

| Term group | G4 value (linear worst) | R1 treatment |
|---|---|---|
| Body diameter D | 50.90 diagnostic; polymer side-radial first passes at 51.10 | swept <= 51.00; required D reported |
| Side wall | scalar 1.1 mm; WALL-SIDE +0.02 (polymer) / +0.36 (metal) | azimuth-resolved (C-R1-04) |
| Connector crossings | XF-J1501 -0.100, XB-J201 -0.100, XC-J202 +0.050, straight +0.050 | local wall over corridor arcs; supplier zero-margin `c_fpc` 0.20, `t_fpc` 0.10, `R_bend_min` 1.848 reported |
| Caseback geometry | H11 / H01 local Z | L-SEAL face topology, rib Z |
| LRA coupling | XL-LRA lateral +0.050, **Z -1.14 to -1.20** | L-LRA only; excluded from the radial geometry verdict |
| Polymer-sector assumptions | tol_bore_r 0.05 (polymer) vs 0.02 (metal) | declared per process class, identical across candidates |

**H05-GEOM** (R1-H04) and **H05-LRA-COUPLED** (R1-H05) are separate checks with separate verdicts. LRA existence or
non-existence must not obscure radial / connector geometry reporting. Lead arithmetic: polymer cannot reach 51.00 mm
with positive crossing margin (needs 51.10; wall floor 1.08 mm gives +0.02 mm); a metal midcase with the crossing arcs
thinned toward the planning minimum plus tolerances gains up to about 0.3 mm.

### 6.7 L-ASM — assembly

Evaluate the C-R1-06 sequence with the G4 access-direction and insertion-collision functions; add caseback ribs,
charger block and face-seal flange to the insertion envelope. Report J1 cycles (rated 50 / planned 25), battery
isolation state before every manipulation, and the SERVICE-COVER-REBOND consequence.

### 6.8 L-LRA — actuator

G4 facts: periphery band lower-web underside to pod plane is 2.95 mm nominal (0.75 + 1.6 + 0.6 and 1.35 + 1.0 + 0.6,
including the 0.6 mm conductor channel); diagnostic maximum envelope G4-B Ø6.28 mm x 1.58 mm, G4-A / C Ø6.80 mm x
0.95 mm; authored classes have minimum height 2.5 mm; plan survivors exist only for the rectangular class (32-45
poses) and fail Z by 1.6-2.3 mm. **The current G2 allocation is kept.** R1 studies only authorized REAR-level
solutions: pose / orientation re-search and the **bounded local caseback-pocket** option (residual plate >= material
minimum, H13 re-evaluated, pocket depth 0-0.6 mm). Lead estimate of the pocketed ceiling:
`2.95 - t_cb_local(>= 0.5) - 0.30 - 0.07 ~ 2.1 mm`, still about 0.4 mm below the authored minimum class. A local
bulge below the caseback plane is a T_total increase (OD-G4-STACK) and is not carried. R1 does not move the LRA to
another Z allocation and does not author a class to fit (C-R1-08).

## 7. Search space (deterministic; no Cartesian explosion)

Shared outer variables are swept on the 0.05 mm grid; lanes are evaluated independently per shared point and combined
by intersection. Budget: <= 2,000,000 predicate evaluations; `g4_r1_blockers.py check` <= 90 s. Every variable
carries source, range, evidence class, hard stop and gate.

| ID | Variable | Range / grid | Source | Evidence class | Hard stop | Gate |
|---|---|---|---|---|---|---|
| V01 | D_case_body | 48.00-51.00 step 0.05 (report-only to 52.50 if nothing feasible) | OD-G4-ENVELOPE | OWNER REQUIREMENT | > 51.00 | owner |
| V02 | tw bulk | 0.8-1.6 step 0.1 | G4 sweep | DESIGN + MFG_TOL | < material min + tol | supplier |
| V03 | t_wall local, 3 arcs | floor .. tw step 0.02 | C-R1-04 | DESIGN + MFG_TOL | below floor; arc narrower than corridor + 1.5 deg | supplier / FEA |
| V04 | boss extension per SW | 0.00-0.95 step 0.05 | OD-G4-ENVELOPE | DESIGN | boss + tol > 1.0 | owner |
| V05 | button topology per SW | T1 (regression) / T2 / T3 (metal only) | C-R1-05 | DESIGN | none passes | SR-BUTTONS |
| V06 | pusher d_p per SW | 2.0-3.6 step 0.2 | R1 | DESIGN | boss leaves switch window; wall < min | supplier |
| V07 | boot rim land | 0.5 / 0.6 / 0.8 / 1.0 | G4 bond-land class | PROVISIONAL, adverse 1.0 | < planning minimum | SR-BUTTONS |
| V08 | boot strain screen eps | report 0.15 / 0.25 / 0.35; hard at 0.25 | R1 | PROVISIONAL | free height > envelope | supplier fatigue |
| V09 | guide land, c_switch, c_main_case | 0.2-0.4 / 0.2-0.4 / 0.1-0.2 (G4 ranges, adverse max) | G4 | SUPPLIER_GATED | never narrowed | SR-BUTTONS |
| V10 | caseback main seal | face / adhesive / radial (regression) | G4 seal_types | DESIGN | gland impossible | supplier gasket |
| V11 | main seal cs | 0.5-1.2 step 0.1 | G4 sweep extended | PROVISIONAL, tol +/-0.05 | fill / squeeze window | supplier |
| V12 | caseback t_in / t_out | G4 grids 0.4-1.2 / 0.6-1.6 | G4 | DESIGN + MFG_TOL | exceeds residual -> Z delta | owner (STACK) |
| V13 | rib ring count / spoke count | 0-2 / {0, 8, 12, 16, 24} | R1 | DESIGN | rib in forbidden zone | FEA |
| V14 | rib width / height | 0.6, 0.8, 1.0 / 0.4-1.4 step 0.2 | R1 | DESIGN + MFG_TOL | tip < c_rib_top 0.10 below lower web; over conductor channel height <= band - 0.65 | FEA |
| V15 | ring radius | 17.5-23.5 step 0.5 | S14 outline 16.4 + 1.1 | DESIGN | inside outline + 1.1; CHG_ROUTE zone in Z | — |
| V16 | split radius (C1) | 17.0-19.1 step 0.5 | min radiator inner 20.13 - 1.0 | DESIGN | > 19.13 (H17) | — |
| V17 | caseback material class | MAT-GF-POLY / MAT-NF-METAL / MAT-CERAMIC | G4 | PROVISIONAL | allowable | OD-G4-MATERIAL |
| V18 | window | W1, 0.50 mm, sapphire / strengthened glass | OD-G4-WINDOW | PROVISIONAL | stress / Z | SR-WINDOW |
| V19 | charger orientation / centre r / centre az | {0, 90} / 17.5-23.5 step 0.05 / 85-95 step 1 | frozen wedge | DESIGN | block outside wedge or in WIFI_RAD | — |
| V20 | charger land / containment | 0.5-1.0 step 0.1; WEDGE_STRICT and CASEBACK_EXT | C-R1-01 | PROVISIONAL, adverse 1.0 | land conductive; overshoot > caps; < clearances | SR-CHG-MECH |
| V21 | feedthrough topology | FT-A / FT-B / FT-C | C-R1-05 | DESIGN | no separate seal | SR-CHG-MECH |
| V22 | LRA class, pose, pocket depth | G4 classes + supplied; az 0-355 step 5; r step 0.25; ori 0 / 90; pocket 0-0.6 step 0.1 | G4 8.9, C-R1-08 | PROVISIONAL / SUPPLIER | residual plate < min; Z | SR-LRA |
| V23 | carrier wall, carrier radius | 0.30-0.60 / 22.75-23.60 (G4) | G4 | DESIGN + MFG_TOL | < 0.30 at adverse | — |
| V24 | screws | 3-4 at lug roots | G4 | PROVISIONAL | inside seal line unsealed | OD-G4-STRAP |
| V25 | cover, land (regression) | a_cover 22.30, t_land 0.3, w_land 1.5 (G4 retained) | G4 | DESIGN | H06-H09 regress | — |
| V26 | C-R1-03 interpretation | I-SUM and I-MAX, both always evaluated | C-R1-03 | reviewer-gated | — | reviewer |

## 8. Hard checks (R1)

R1 re-evaluates every G4 check H01-H25 (G4-literal column) and adds the R1 column below. Required evaluations follow
`G4_BRIEF.md` section 6.3 (LEGACY, NOMINAL, RSS, LINEAR WORST, GOVERNING TERMS, OWNER-GATED).

| ID | Check | Evaluation |
|---|---|---|
| R1-H01 | G2-REVA / G2-REVA-HI reproduced, total Z delta 0.000; every R1 feature fits the REAR-periphery band at linear worst | exact / linear worst |
| R1-H02 | D_case_body <= 51.00; only the five button bosses protrude, <= +1.0 mm incl. boot and tolerance | linear worst |
| R1-H03 | LEGACY numbers and every G4-literal result at `00e77cb` reproduced exactly (pinned hash + recomputation) | exact |
| R1-H04 | **H05-GEOM**: straight, XF, XB, XC, wall side, wall dielectric, main-case, t_allow >= 0 with azimuth-resolved wall | linear worst |
| R1-H05 | **H05-LRA-COUPLED** (XL lateral and Z) — separate; part of the L-LRA verdict only | linear worst |
| R1-H06 | Cover / bezel / land regression (G4 H06-H09) | linear worst |
| R1-H07 | W1 @ 0.45 mm minimum: stress and deflection screens (G1 conservative), rib fit, bond land, no rib-to-optics load | G1 conservative |
| R1-H08 | Pressure partition sums; no forbidden branch (battery, REAR PCB, G3 support lands, carrier lower web); PCB load 0.000 N | exact |
| R1-H09 | Stiffened caseback: stress <= sigma_allow(min); deflection <= min(c_cb_rear min, window standoff) at p max | linear worst |
| R1-H10 | Perimeter bearing, screw shear / pull-out and split-plate bond-shear thresholds reported with supplier zero-margin | linear worst |
| R1-H11 | Main seal gland compression and fill inside window at +/-0.05 mm; seal path closed; no impossible gland remains | linear worst / exact |
| R1-H12 | Buttons per SW: guide stack under I-SUM and I-MAX, core, boss wall, rim land, stroke >= c_switch, tangential fit inside the frozen window, material constraints | linear worst |
| R1-H13 | Every aperture has exactly one primary seal with a feasible geometry class | exact |
| R1-H14 | Charger: block inside wedge and outside WIFI_RAD; land per C-R1-01 with overshoot <= caps; corridors clear in plan and Z | linear worst |
| R1-H15 | H17 zero conductive / wiring intrusion in radiators (ribs, split plate, screws, plungers, charger); H18 MAG_CLEAR | exact |
| R1-H16 | H19: S14 outline, pod, supports, tail corridors, U6 island untouched; no G3 support-land enlargement claimed | linear worst |
| R1-H17 | Assembly sequence (C-R1-06) executable, access direction per operation, rear-insertion collision-free | linear worst |
| R1-H18 | >= 4 case / caseback supports incl. W/NW outside the pack (G4 H24) | exact |
| R1-H19 | LRA lane: PASS only with an authored / supplied class fitting a pose at the current allocation; else quantified maximum envelope and deficit | linear worst |
| R1-H20 | No KiCad / interface / immutable-file change; historical reproduction of section 5.1 | exact |

## 9. Evidence rules and numeric outputs

9.1 Every value carries one evidence class (`G4_BRIEF.md` section 6.1). No MPN, no supplier performance, no RF claim,
no 5 ATM or structural qualification claim. 9.2 Every failing check lists governing terms with role and the supplier
zero-margin value. 9.3 Each blocker ends in exactly one disposition: `RESOLVED_GEOMETRICALLY` (with margins),
`SUPPLIER_GATED` (numeric threshold), `OWNER_GATED` (named decision), `ARCHITECTURE_GATED` (named phase),
`RESOLVED_UNDER_I-MAX_ONLY — REVIEWER ADJUDICATION REQUIRED` (C-R1-03). 9.4 No `RESOLVED_GEOMETRICALLY` may rely on a
credit listed in `G4_BRIEF.md` section 6.3, on a widened gland window, or on a narrowed supplier tolerance.

9.8 **OD-G4-LRA-ARCH trigger (exact).** R1-S08 is raised when L-LRA reports that no authored class and no supplied
class (C-R1-08) fits any pose at the current G2 allocation, including the pocket variant, with the quantified
`delta_Z = H_class_min - H_max_pocket > 0` (lead estimate 0.4-0.5 mm against the 2.5 mm authored minimum). R1 then
**stops the lane with the OD-G4-LRA-ARCH / G2-reopening question** and reports: the numeric envelope, the deficit,
that T_total headroom is 0.150 / 0.120 mm nominal (so any REAR-driven growth needs OD-G4-STACK and a G2 allocation
study) and the option set (supplier evidence of a class with `H <= H_max_pocket` and a footprint fitting a reported
pose window; G2 REAR-band reallocation study; haptic-free Rev-A). R1 does not choose and does not reopen G2.
Additional supplied classes may be introduced only by a reviewed input change that carries primary-document evidence.

## 10. Verdict vocabulary

One of: **R1 RESOLVED** (all lanes PASS); **R1 RESOLVED — SUPPLIER/RF/QUALIFICATION GATES OPEN** (all geometry
closed, every remainder is supplier / measurement / G5 with a numeric threshold); **R1 PARTIAL — LRA ARCHITECTURE
GATE** (all non-LRA lanes resolved or supplier-gated; L-LRA stopped per 9.8); **R1 OWNER DECISION REQUIRED** (names
it, including C-R1-03 adjudication); **R1 FAIL**. R1 never emits a G4 verdict; G4 status changes only by a later lead
record after independent review. Expected from the lead arithmetic above: PARTIAL — LRA ARCHITECTURE GATE.

## 11. Validation

All commands must exit 0 on a clean committed tree except where marked.

```
python3 -B design/mechanical/tools/mech_model.py check
python3 -B design/mechanical/tools/g1_scenarios.py check
python3 -B design/mechanical/tools/g2_interconnect.py check
python3 -B design/mechanical/tools/g3_rear_optical.py check          # clean-tree protocol, see below
python3 -B design/mechanical/tools/arch_diagrams.py check            # clean-tree protocol, see below
# historical G4 reproduction, pinned baseline, read-only detached checkout (section 5.1 item 1)
git worktree add --detach <scratch>/g4_baseline 00e77cbe107a79ac05194f19b674f7ab8d5941c9
( cd <scratch>/g4_baseline && python3 -B design/mechanical/tools/g4_case_sealing.py check \
  && python3 -B design/mechanical/tools/g4_case_sealing.py selftest )
git worktree remove <scratch>/g4_baseline
# literal G4 check in the R1 tree: EXPECTED RED on scope only (section 5.1 item 4); recorded, not required green
python3 -B design/mechanical/tools/g4_case_sealing.py check
python3 -B design/mechanical/tools/g4_r1_blockers.py check           # includes the in-process reproduction, item 2
python3 -B design/mechanical/tools/g4_r1_blockers.py selftest
git diff --exit-code 00e77cbe107a79ac05194f19b674f7ab8d5941c9 -- design/mechanical/architecture.md \
  design/mechanical/architecture.json design/mechanical/README.md design/mechanical/tools/arch_diagrams.py \
  design/mechanical/tools/g4_case_sealing.py design/mechanical/inputs/g4_case_sealing.json \
  design/mechanical/G4_BRIEF.md design/mechanical/generated
git diff --exit-code <R1 contract commit> -- design/mechanical/G4_R1_BRIEF.md
git diff --exit-code 168badbab6de1201bb3209902a53fe1e4b874cc9 -- <G1-immutable file list of G4_BRIEF.md section 11>
git diff --exit-code 00e77cbe107a79ac05194f19b674f7ab8d5941c9 -- '*.kicad_pcb' '*.kicad_sch' '*.kicad_pro' \
  '*.kicad_prl' design/interfaces design/placement rear_sensor libraries
git diff --name-only 00e77cbe107a79ac05194f19b674f7ab8d5941c9 -- .        # must be a subset of R1_FILES
git diff --check
```

The G3 and `arch_diagrams.py` scope checks pass only on a clean tree (known protocol): the implementer runs every
other command on the working tree, records the literal exit codes of the clean-tree-sensitive commands with a
read-only in-process proof that patches only `scope_check`, and the lead re-runs them after the review commit.

`g4_r1_blockers.py check` regenerates every output in memory and fails on: any byte difference; a pin mismatch; a
G4-literal mismatch; the in-process G4 reproduction not byte-identical or selftest below 32/32; an unreported nonzero Z
delta; D above 51.00; a disposition resting on a credit; both C-R1-03 interpretations not reported; a changed
immutable file; a changed `ALLOWED_CHANGES` beyond `R1_FILES`; size (> 2 MB) or runtime (> 90 s) overrun.

`selftest` must prove each injected fault is caught: widened O-ring window; narrowed cross-section tolerance; blanket
`L_bore_min` silently replaced; `c_main_case` or `c_switch` silently dropped; I-MAX counted as closed without
adjudication; T1 selected; pusher outside its switch window; switch moved; conductive land; land overshoot beyond
cap; land inside S14 outline + 1.1; land inside a radiator volume; rib through the conductor channel; rib tip bearing
on the REAR board or lower web; any load on a G3 support land; PCB pressure load > 0; polymer wall below floor;
boss + tol > 1.0; unpermitted protrusion; D 51.01; nonzero Z delta; open seal path; a class defined by its threshold
counted as LRA PASS; LRA moved to another Z allocation; H05-GEOM merged with H05-LRA-COUPLED; frozen S14 feature
obstructed; mirrored REAR transform; historical G4 file edited; any KiCad file touched.

## 12. Stop conditions

| ID | Stop |
|---|---|
| R1-S01 | OD-G4-WINDOW is revoked, or no W1 row passes without a Z delta |
| R1-S02 | OD-G4-ASSEMBLY is revoked, or no executable sequence exists |
| R1-S03 | No button topology (T2 / T3) closes for some SW inside its frozen window and boss limit without moving a switch |
| R1-S04 | No charger feedthrough closes (block, land per C-R1-01, seal, corridors) at <= 51.00 mm |
| R1-S05 | A support / stiffening topology needs a thicker caseback, a new Z layer or nonzero total Z (OD-G4-STACK) |
| R1-S06 | No seal architecture yields a continuous closed path with feasible glands |
| R1-S07 | No structural topology passes R1-H09 at planning allowables (report required equivalent thickness; OD-G4-MATERIAL / OD-G4-STACK question) |
| R1-S08 | LRA lane trigger of section 9.8 met: OD-G4-LRA-ARCH / G2 reopening **question** raised, not decided |
| R1-S09 | Any required G3-B-S14 placement move, G2 allocation change, G1/G2/G3 reopening, KiCad or interface change |
| R1-S10 | `D_case_body > 51.00` or a protrusion outside the five permitted bosses is required |
| R1-S11 | A margin can be closed only with a speculative compression, material, adhesive, growth, seal or supplier credit |
| R1-S12 | Live repository disagrees with this brief, a pin mismatches, an immutable file would change, or historical G4 reproduction fails |
| R1-S13 | Owner decision required that is not recorded in section 2 (including unresolved C-R1-03 adjudication for a claimed PASS) |

R1-S03 … R1-S08 and R1-S13 (adjudication case) stop only the affected lane's resolution claim; independent lanes
are still completed and reported. R1-S01, R1-S02, R1-S09, R1-S10 (as a whole-design requirement), R1-S11 and R1-S12
stop the whole run.

## 13. Acceptance criteria

1. OD-G4R1-ENTRY, OD-G4-WINDOW and OD-G4-ASSEMBLY recorded verbatim in the R1 generated JSON; G4 decisions unchanged.
2. G4-literal and R1 columns for every check; LEGACY reproduced exactly.
3. Every blocker A-H has exactly one disposition with margins or thresholds and governing terms.
4. Button, charger, seal, structure and radial lanes each report geometry separately from supplier gates; C-R1-03
   reported under both interpretations.
5. H05 reported as H05-GEOM and H05-LRA-COUPLED with no blending.
6. L-LRA reports envelope, deficit and the 9.8 trigger state; no class authored to fit; no Z reallocation.
7. Z delta 0.000 on both baselines or an R1-S05 verdict; D <= 51.00.
8. No claim of 5 ATM, structural, optical, adhesive, RF or supplier qualification anywhere.
9. Section 11 satisfied, including historical G4 reproduction; changes confined to `R1_FILES`; budgets met.
10. Verdict from section 10 only.

## 14. Handoff and later phases

`generated/g4_r1_blockers.json.handoff_to_g4_closure` (numeric): per-lane dispositions; leading case architecture
family with D and margin to 51.0 mm; wall map; rib / plate geometry with equivalent stiffness; button topology and
boss / bore windows; seal inventory with gland geometry; charger block / land geometry and overshoot; LRA envelope /
deficit; supplier zero-margin values; FEA load cases and ATM-Q1…Q6 unchanged; open owner decisions including C-R1-03.
R1 authorizes nothing downstream: G4 closure, G5 (RF), K1 (KiCad) and Q1 (qualification) remain separately gated
exactly as in `G4_BRIEF.md` sections 15-16.

## 15. Execution roles

- Primary implementer: **Astra, High effort**, fresh session; contract = this brief.
- Independent reviewer (different family): **`codex-sol` lane, High effort**; resolve the concrete model id from the
  routing configuration at review time. The reviewer must in particular challenge section 16 items 1-5.
- The lead does not implement R1 in the contract session. Pushing is done by the owner.

## 16. Independent review must challenge

1. **C-R1-03:** do `c_main_case` and `c_switch` bound the same gap? Is the I-SUM / I-MAX disposition rule honoured,
   and is neither term silently removed?
2. **Structural surrogate / rib / load-path modeling:** no bearing on carrier, REAR board, battery or G3 support
   lands; rib Z inside the REAR band at linear worst; smeared-stiffness flange width and stress-concentration factor;
   split-plate bond not credited beyond its numeric threshold; side-wall screens for thinned arcs.
3. **Charger wedge clarification:** non-conductive, caseback-side, overshoot within the contract caps, radiators and
   neighbouring structures clear, wedge / frozen clearances / block size / land range untouched; strict-wedge result
   still reported.
4. **LRA trigger:** no authored class defined by its threshold counted as PASS; pocket residual plate; E-G4-02
   disposition unchanged; OD-G4-LRA-MAG left open; no Z reallocation.
5. **No accidental G2 / G3 reopening:** G3-B-S14 unchanged (H19), Z delta 0.000, switches unmoved, no KiCad change.
6. The dynamic-gland impossibility: windows and tolerances not widened; T2 / T3 really remove the dynamic window;
   T1 never selectable.
7. Face-seal feasibility versus plate deflection between screws (carried as FEA, not credited).
8. Azimuth-resolved wall floors at material minimum + tolerances; H05 split reporting; polymer vs metal process
   tolerances identical across candidates.
9. C-R1-09: no accepted G4 file edited; the in-process extension adds exactly `R1_FILES`; historical G4 reproduction
   byte-identical at `00e77cb`; literal red check fully explained by scope.
10. No MPN, supplier capability or qualification claim; G1 / G2 / G3 / G4 immutability.
