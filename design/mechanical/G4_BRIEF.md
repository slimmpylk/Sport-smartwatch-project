# G4 brief — CASE / CASEBACK / SEALING-ARCHITECTURE CLOSURE STUDY (Rev-A)

Status: phase contract finalized with owner decisions OD-G4-RECORD, OD-G4-ENTRY, OD-G4-ENVELOPE and OD-G4-CORNER
(approved 2026-10-14). G4 is provisional, reversible, deterministic mechanical study work. It authorizes **no KiCad
edit**, no RF claim, no 5 ATM qualification claim, no MPN selection, no supplier-request issuance and no later phase
(G5, K1, Q1). This brief is the scope contract for G4. Destination: `design/mechanical/G4_BRIEF.md`.
Work branch: `mechanical/g4-case-sealing-closure`, created from `afb19ac173ce67c7e9599313cc5a0942e026ade9`.

Builds on, and does not reopen:
- G1 `168badbab6de1201bb3209902a53fe1e4b874cc9` (immutable);
- G2 `eea49e447895e574a3f48e0b9777f57880dcd632` — "G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES" (OD-G3-RECORD);
- G3 `afb19ac173ce67c7e9599313cc5a0942e026ade9` — "G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES" (OD-G4-RECORD),
  selected candidate **G3-B-S14**. The generated historical G3 verdict "G3 CONDITIONAL — SUPPLIER/MEASUREMENT GATES
  OPEN" remains unchanged in the G3 record.

Phase 1, G1, G2 and G3 rules apply except where this brief explicitly changes scope.

## 1. Objective

Produce a deterministic, evidence-classed closure study of the Rev-A **case envelope, caseback, pod/window carrier,
cover/display retention, battery carrier, 5 ATM seal architecture, RF radiator-volume keep-outs, buttons, charger
aperture/feedthrough, LRA re-placement, assembly/insertion paths and tolerance closure**, around the frozen G2 stack
and the frozen G3-B-S14 REAR placement, with:

1. a Z-stratified case section (case inner radius per Z level and azimuth, bezel/cover ledge, caseback, pod opening)
   replacing the single planning `R_case_inner` of G1/G2 for G4 evaluations only;
2. the **minimum feasible case-body diameter** within the owner ceiling of 51.0 mm (OD-G4-ENVELOPE);
3. explicit numeric re-evaluation of the inherited conservative radial margin (−0.950 mm) and X25 conservative
   cover fit (−1.100 mm) under OD-G4-CORNER, reported side by side with the unchanged legacy values;
4. a complete seal inventory, seal-path closure and analytical screening — no qualification claim;
5. RF radiator volumes preserved as zero-intrusion keep-outs for new metal and wiring — no RF claim;
6. a valid LRA placement window;
7. a deterministic assembly / insertion / service sequence;
8. a numeric handoff to the later K1 (KiCad), G5 (RF) and Q1 (qualification) phases.

Exit is a recommended case architecture with numeric reservations, rules and gates. It is not case CAD, not a frozen
design, not a material freeze and not a qualification.

## 2. Owner decisions (authoritative)

### 2.1 In force and unchanged

OD-COVER, OD-REAR-SIDED, OD-WATER, OD-U8, OD-DEVACCESS, OD-J202, OD-CONN-SIDE (2026-10-11) and OD-THICK-REVA
(2026-10-12), as recorded in `inputs/input_register.json`; OD-G3-ENTRY, OD-G3-SIDE, OD-G3-RECORD and
OD-G3-MAX86141-PKG (2026-10-13), as recorded in `G3_BRIEF.md` section 2 and `architecture.json.g3.owner_decisions`.
Do not revoke or reinterpret any of them. OD-G3-MAX86141-PKG is not broadened in any way.

### 2.2 New for G4 — APPROVED by the owner 2026-10-14

Record them verbatim in this brief and in `architecture.json.g4.owner_decisions` (date 2026-10-14, source: owner
decision, G4_BRIEF.md section 2), NOT in `input_register.json`.

**OD-G4-RECORD — APPROVED — 2026-10-14**

Record:

G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES

and freeze G3-B-S14 as the authoritative G4 carry-in.

This administrative closure does NOT:
- close any G3 criterion-10 supplier/manufacturer/measurement gate;
- change the generated historical G3 verdict;
- authorize KiCad work;
- authorize G5 or any later implementation phase.

**OD-G4-ENTRY — APPROVED — 2026-10-14**

Reclassify the existing "SR-ANTENNAS before G4" requirement from a G4 ENTRY blocker to a G5 / RF-closure requirement.

G4 may begin with antenna/feed construction unresolved, provided it:

- preserves the frozen radiator volumes;
- permits no new metal/wiring intrusion into those volumes;
- does not invent antenna feed dimensions;
- does not freeze radome dielectric or final case material based on unsupported RF assumptions;
- makes no RF-performance claims.

AE1401 / AE1410 / AE1420 construction and final RF validation remain G5 gates.

G5 is explicitly allowed to reopen G4 case/material/envelope decisions if real RF evidence proves the G4 assumptions
incompatible.

**OD-G4-ENVELOPE — APPROVED — 2026-10-14**

Rev-A case-body outside diameter hard ceiling:

<= 51.0 mm

excluding lugs.

Local functional bosses may extend at most +1.0 mm beyond the case-body envelope where the G4 brief explicitly permits
and validates them.

51.0 mm is a HARD MAXIMUM, not the design target.

The deterministic G4 study must minimize case diameter within all other hard requirements and report:

- selected diameter;
- minimum feasible diameter found;
- margin to the 51.0 mm ceiling.

If no compliant design exists at <=51.0 mm, G4 must stop and report the minimum required diameter rather than silently
exceeding the owner limit.

**OD-G4-CORNER — APPROVED — 2026-10-14**

For dimensions that G4 itself designs, use:

design value + explicitly declared manufacturing tolerance

rather than treating the entire planning range as manufacturing tolerance.

For supplier/manufacturer-gated quantities:
- retain the applicable conservative/worst planning value until qualified;
- do not convert missing supplier data into optimistic tolerances.

Preserve and report the historical G1/G2 conservative calculations unchanged alongside the new G4 calculation.

G4 must report separately:

- legacy carry-in result;
- nominal;
- RSS;
- linear worst;
- governing owner/supplier/manufacturer terms.

No speculative compression, material, adhesive, battery-growth, seal or supplier credit may be used to close a margin.

**Lead application of the approved decisions (binding for G4 unless the owner amends it):**
- OD-G4-ENVELOPE. *Case body* = the case structure at every Z level, excluding lugs and the permitted bosses below;
  `D_case_body` = 2 × the maximum outer radius of the case body over all azimuths and Z levels. *Permitted local
  functional bosses* (the only ones): one button boss per SW1–SW5, confined to that button's azimuth window
  (section 8.7), radial extent ≤ +1.0 mm beyond `D_case_body / 2`, validated by H03/H21. Any other protrusion counts
  in `D_case_body`. Lugs are reserved as envelopes (section 8.11) and excluded from `D_case_body`.
- OD-G4-CORNER. The term roles and the six mandatory evaluations are defined in section 6. Every manufacturing
  tolerance used for a G4-designed dimension is a declared PROVISIONAL_ASSUMPTION per process class until supplier
  data exist; it is never chosen to make a margin pass and it is identical for every candidate using that process
  class.
- OD-G4-ENTRY. Radiator volumes are hard keep-outs (H17). No dielectric, radome thickness or case-material choice may
  be justified by an RF argument in G4; candidate material families are compared only on mechanical, sealing,
  keep-out and magnetic criteria.

### 2.3 Owner decisions required before G4 CLOSURE only (not before start)

G4 proceeds with the stated PROVISIONAL defaults, reports them as such, and invents no choice for them.

- **OD-G4-ATM-STD** — select the 5 ATM qualification standard and test margin (ATM-Q1). Until decided, G4 uses
  `p_test` 0.500 nom / 0.625 max MPa (G1 `inputs/g1_scenarios.json.plate_check.p_test_MPa`, PARAMETRIC).
- **OD-G4-MATERIAL** — choose the case/caseback material family for Rev-A prototypes from the G4 candidates. This
  decision depends on G5 RF evidence; any choice made at G4 closure is recorded as "conditional on G5" and may be
  reopened by G5.
- **OD-G4-STRAP** — strap/lug interface class (lug inner width, spring-bar / quick-release type, conductive or not).
  G4 reports the lug–GNSS_RAD interaction at 12 o'clock as input to this decision.
- **OD-G4-LRA-MAG** — whether the frozen invariant "No watch-side permanent magnet without explicit authorization and
  magnetometer analysis" covers the LRA's internal magnet, and if so whether it is authorized. G4 reports the
  LRA-to-U703 distance and does not reinterpret the invariant.
- **OD-G4-WINDOW** — *only if triggered* by section 8.3: accept a frame/rib-supported pod window (W1 or W2) as the
  Rev-A mechanical baseline before MG-WINDOW-XTALK data exist.
- **OD-G4-STACK** — *only if triggered*: any nonzero G4 Z delta, or compliance on G2-REVA but not G2-REVA-HI.

G3 owner inputs (PPG modalities, MG-WINDOW-XTALK threshold, skin-temperature accuracy target) are not G4 inputs. G4
keeps W0/W1/W2 and the U6 F1/F2/F3 skin-contact options geometrically compatible where the 5 ATM screen allows and
reports any variant it eliminates.

## 3. Frozen carry-ins (do not change)

- **Architecture and invariants:** rigid MAIN; MAIN↔REAR FPC; rigid double-sided skin-facing REAR; separate charger
  flex/harness; `frozen_invariants` of `inputs/input_register.json` verbatim (incl. LPR454440 not replaceable; MAIN
  Ø46 development envelope; 24 positions / 13 nets; REAR-local nets; TPS631000 on MAIN; charger contacts rear east
  ~3 o'clock GND/+5V/+5V/GND with no charger-positive in the sensor FPC; no watch-side permanent magnet without
  explicit authorization and magnetometer analysis).
- **G2 allocation and stack:** J1501-F.Cu, J1502-TAIL0402 (inner-face bonded tail, mated Z 0.68 / 0.70 / 0.73),
  J201-F.Cu, J202-WEST-F.Cu, U7-B.Cu, J1301 / J1 / U8 retained, C901/C903 P-0402. G2-REVA 16.350 / 16.796 / 18.040
  and G2-REVA-HI 16.380 / 16.825 / 18.040 mm (nominal / RSS / linear worst). G3 Z delta 0.000 / 0.000 / 0.000. No
  supplier- or owner-gated lever is credited.
- **G3-B-S14 (authoritative carry-in, OD-G4-RECORD):** every REAR placement, face and rotation; REAR outline circle
  r 16.400 mm about the REAR envelope centre (assembly (100, 100)); pod polygon (411.997 mm²); pod depth 1.35 / 1.85 /
  1.05 mm (nominal / conservative / optimistic); caseback residual before wall 0.55 / 1.05 / 0.25 mm; support lands
  at assembly azimuth 30 / 150 / 270; J1502 tail alternative `radial-r11.3-a166.05` (6.45 × 1.00 mm nominal land;
  7.90 mm conservative width); U6 thermal island at azimuth 45°, r 13.0 mm with skin-contact options F1/F2/F3; per-
  cell seal-land range 0.3 / 0.5 / 0.8 mm (PROVISIONAL); REAR plan clearances CHG_CONTACT 1.100, CHG_LINK 3.600,
  CHG_ROUTE 0.600 mm; U6 plan distance to CHG_CONTACT 8.367 mm; REAR outline overlaps FPC_UNDER 25.492, LRA 28.431,
  MAG_CLEAR 150.586 mm². All values are read from `generated/g3_rear_optical.json.g4_handoff` (candidate
  G3-B-S14, `released: true`) through a pinned hash, never re-typed.
- **G3 conservative-corner failures stay explicit G3 gates:** lower_web, cell_barrier_gap, pd_in_paths, tail_fit,
  support_lands. G4 must not consume volume they need and must not claim to close them.
- **Legacy radial / cover numbers (reproduced, never overwritten or reinterpreted):**
  conservative radial margin **−0.950 mm**; X25 conservative cover fit **−1.100 mm**; X25 nominal fit +0.55 mm with
  bezel wall margin −0.15 mm against t_bezel_min 0.7 mm; edge-crossing margin at land ceiling +0.68 / −0.95 / +1.30 and
  flat exit −0.47 / −2.10 / +0.70 mm; t_allow_straight 0.80 / −0.75 / 1.50 mm; lower-web margin 0.08 / −0.20 / 0.40
  mm; U4 land headroom 0.24 / −0.06 / 0.44 mm (nominal / conservative / optimistic).
- **Untouched:** every KiCad file and library, `design/interfaces/**`, `design/placement/**`, `rear_sensor/**`.

Anything that needs one of these changed is OWNER DECISION REQUIRED, never the recommendation.

### 3.1 Carry-in errata (recorded prospectively; G3 history is not rewritten)

- **E-G4-01 (stale G3 evidence).** The G3 `conflict_status` evidence for C5-SOUTH-CROWDING, X11-POD-FOOTPRINT and
  X12-J1502-FACE states "no recommended topology until nominal hard checks pass". It is superseded by the accepted
  G3-B-S14 selection (OD-G4-RECORD). Record in `architecture.json.g4.errata` and in the G4 report only; the G3 records
  stay byte-identical.
- **E-G4-02 (LRA disposition).** G3 dispositioned the S14 outline × LRA overlap (28.431 mm²) as "C5/SR-FPC-MECH
  lower-web Z separation requires qualified cross-section". That disposition does **not** resolve the conflict: an LRA
  cannot be hidden in the lower web (0.4 mm nominal, 0.3 mm minimum). The historical LRA reservation (az 165–195,
  r 12.65–22.00, REAR level) is therefore **not a valid frozen placement**. G4 must find a valid LRA placement window
  (section 8.9) or stop. The LRA is never silently removed.

## 4. Scope

### 4.1 G4 owns (deterministic mechanical study only)

A. **Case envelope** — Z-stratified case section at levels COVER, DISPLAY / FRONT-GAP, MAIN, BATTERY, REAR,
CASEBACK; `D_case_body` minimized within OD-G4-ENVELOPE; bezel / cover ledge; wrist-facing caseback contour; lug
reservations (envelope only); the **MAIN outline constraint polygon** (maximum permitted MAIN outline incl. notches for
supports, bosses and bores — a constraint for K1, not Edge.Cuts).
B. **Caseback and pod/window carrier** — caseback geometry around the frozen S14 pod; concept P1 (window / pod frame
integral with the caseback) versus P2 (pod frame on the REAR module, sealed into a caseback aperture); REAR support
and hard-stop interface; J1502 tail exit and under-run clearance in the carrier; charger aperture; pod seal land;
`h_pod` as an output.
C. **5 ATM seal architecture** — seal topology and inventory; gasket / O-ring / adhesive candidates as geometry
classes; compression windows; seal and bond lands; caseback retention (screw count and positions); window, charger,
button, vent and U6-F3 seals; analytical screening only.
D. **Cover / display retention** — cover free span and diameter, cover bond land, bezel section, display support land
DISP_LAND (fold interruption, U4 relief), ALS and vent apertures as case features.
E. **Battery carrier** — finished-pack envelope ranges, PCM lobe sweep, growth allowance, insulation, retention, load
path. LPR454440 unchanged.
F. **RF radiator-volume keep-outs** — geometry only (section 8.6).
G. **Buttons SW1–SW5** — bore, boss, pusher and seal-gland envelopes. No switch MPN.
H. **Charger aperture / feedthrough** — contact-block envelope, caseback aperture and separate seal, keying recess
(no magnet), dock force path, charger-corridor clearance.
I. **LRA re-placement** — section 8.9.
J. **Assembly / insertion paths** — deterministic sequence, access directions, rear-insertion collision check, service
and rework, battery isolation states.
K. **Tolerance closure** — section 6 for every radial, axial, seal and insertion check.

### 4.2 G4 does NOT own

KiCad edits of any kind (Edge.Cuts, footprints, placement, zones, stackup, rules, routing); schematic, BOM, net,
value, footprint or interface changes; case CAD / STEP; MPN selection or purchase; supplier-request issuance or
execution; antenna / feed design; radome dielectric design; RF simulation; RF performance claims; FEA execution (G4
only *specifies* load cases); physical qualification (5 ATM, optical, thermal, magnetic, haptic); any change to G3
placements, the G2 allocation or the G1 record; moving J202 (OD-J202 stays open for a placement phase, not G4); U8
relocation; battery replacement; Rev-B thickness optimization (levers are reported, never credited); MAIN-side
electrical items (J201 MPN, C901/C903 DC-bias, U7 allocation review).

### 4.3 Files

**May modify** (tracked files under `design/mechanical/` only):
- `architecture.md` — new G4 section (summary + link, section 4.4); G4 status line; the OD-G4-RECORD status line
  "G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES" outside the immutable G3 section.
- `architecture.json` — new `g4` summary block (section 4.4); exactly one `g4_status` per conflict; `g4.errata`.
- `README.md` — G4 tool and outputs; the OD-G4-RECORD status line.
- `tools/arch_diagrams.py` — extend `check` to the g4 block only.

**New files (exact set):**
- `inputs/g4_case_sealing.json` — authored G4 parameters, ranges, process-class tolerances, candidates, sweep grids,
  evidence pins. Authored PROVISIONAL inputs, never results.
- `tools/g4_case_sealing.py` — stdlib-only; sub-commands `build`, `check`, `selftest`.
- `generated/g4_case_sealing.json` — authoritative result: summary, verdict, selected candidate full detail, every
  candidate's outcome and per-check results at every evaluation of section 6.3, diameter minimization record, LRA
  window, handoff. Target ≤ 2 MB.
- `generated/g4_sweep.jsonl` — only if the exhaustive sweep does not fit the 2 MB target: one canonical JSON object
  per line, sorted by candidate id then sweep key.
- `generated/g4_case_sealing.md` — report.
- `generated/g4_plan.svg` — plan: case body and bosses, reservations, radiator keep-outs, MAG_CLEAR, S14 outline and
  pod, LRA window, seal lines, MAIN outline constraint polygon.
- `generated/g4_sections.svg` — radial sections at stations CENTER, GNSS_N, FPC_S, CHG_E, SW2_W, POD.
- `generated/g4_seal_map.svg` — seal inventory and seal path.
- `generated/g4_assembly.svg` — sequence, access directions and insertion envelopes.

Generated files are written only by the tool and must regenerate byte-identically.

**Immutable** (byte-identical to `afb19ac`): every file immutable under G3_BRIEF section 4; plus `G3_BRIEF.md`,
`inputs/g3_rear_optical.json`, `tools/g3_rear_optical.py`, `generated/g3_rear_optical.json`,
`generated/g3_rear_optical.md`, `generated/g3_rear_faces.svg`, `generated/g3_rear_section.svg`. This brief is
immutable after its own commit. The existing `architecture.md` G1/G2/G3 sections and the `architecture.json`
`g1` / `g2` / `g3` blocks stay byte/semantically identical; conflicts gain only a `g4_status` field.

**May not modify:** anything outside `design/mechanical/`; any KiCad file (`*.kicad_pcb`, `*.kicad_sch`,
`*.kicad_pro`, `*.kicad_prl`), footprint or symbol library; `design/interfaces/**`, `design/placement/**`,
`rear_sensor/**`, `libraries/**`, firmware, scripts, docs. KiCad files, netlists and local datasheets may be **read**.

### 4.4 State-format rule (prospective; accepted G3 state is not rewritten)

- `architecture.json.g4` is a concise authoritative **summary**, target ≤ 100 KB: schema, verdict, owner decisions,
  errata, selected candidate id, selected / minimum feasible `D_case_body` and margin to 51.0, the key numbers of
  sections 6 and 8 quoted from the generated JSON, open gates, conflict statuses, handoff summary, and the SHA-256 of
  every G4 generated file. It must not embed candidate geometry, sweeps or per-corner tables.
- `architecture.md` G4 section ≤ 300 lines: summary tables quoted exactly from the tool's `architecture_section()`
  plus a link to `generated/g4_case_sealing.md`. The full report is not copied.
- Generated JSON: sorted keys, fixed float formatting, compact separators `(",", ":")`, no timestamps, final newline.
- `arch_diagrams.py check` verifies the g4 summary against the generated JSON by hash and key-wise equality, exactly
  one `g4_status` per conflict, and that the G1/G2/G3 sections and blocks are unchanged.
- `g4_case_sealing.py check` runtime target ≤ 60 s on the development host. G3 data are read through a pinned hash,
  never re-derived; the 143 s G3 check is not re-run inside the G4 tool.

## 5. Gate classification (carry-in)

Classes: **G4_PARAMETRIC** (enters as a bounded planning range; never credited; blocks only a final G4 PASS),
**CLOSURE** (must close, or be gated with a numeric threshold, for any G4 closure), **KICAD_IMPL**, **FABRICATION**,
**MEASUREMENT** (prototype), **G5** (RF phase), **N/A** (not a G4 concern). No G4 ENTRY blocker remains after the
section 2.2 approvals.

| Gate | G4 class | Why |
|---|---|---|
| SR-SFH4053B-DS (height / package / optics) | G4_PARAMETRIC (seated ≤ 0.75 stack-neutral; OD-THICK limits 0.90 / 0.954 on G2-REVA, 0.87 / 0.925 on G2-REVA-HI) + KICAD_IMPL | Height moves T_total 1:1 above 0.75; D405–D407 geometry rerun is K1/REAR work. |
| SR-MAX86141-HEIGHT | G4_PARAMETRIC (same thresholds) + KICAD_IMPL | Same mechanism. |
| SR-MAX86141-LAND (0.254 mm; AN1891 / 21-100134) | KICAD_IMPL + FABRICATION; N/A for G4 | Footprint evidence; no case effect. |
| SR-TS5A12301E-HEIGHT | G4_PARAMETRIC (≤ 0.75) + KICAD_IMPL | Skin-face ceiling. |
| SR-PD-CAPACITANCE (C_PD at 0 V) | N/A; KICAD_IMPL + MEASUREMENT (MG-GUARD) | Electrical. |
| SR-FPC-MECH: J1502 land geometry / pitch / rows | KICAD_IMPL + FABRICATION; G4_PARAMETRIC for the tail-exit / strain-relief corridor (6.45 nom / 7.90 cons) | Carrier and lower-web clearance is G4; the land is K1. |
| SR-FPC-MECH: joint thickness | G4_PARAMETRIC (0.03 / 0.05 / 0.08, G2 model) | Inside the frozen G2 stack. |
| SR-FPC-MECH: current (≥ 41.3 mA per VLED position) | N/A; FABRICATION / KICAD_IMPL | Electrical. |
| SR-FPC-MECH: bonding process (hot-bar / ACF) | G4 assembly-sequence input; FABRICATION | Thermode access precedes carrier insertion. |
| J1502 conservative tail fit (fails; C403 thermode intrusion) | KICAD_IMPL (G3 gate); G4 reserves the conservative tail corridor | Not solvable by the case. |
| SR-FPC-MECH: R_bend_min, t_fpc, exit height, J1501 mouth radius | G4_PARAMETRIC (planning max in conservative / linear worst) | Governs radial edge crossings. |
| SR-C1501 | N/A (≤ 0.65 reservation inside stack); KICAD_IMPL | — |
| SR-REAR-PCB (HDI, 0.6–1.0 mm) | G4_PARAMETRIC (0.8 nom / 1.0 max) + FABRICATION + KICAD_IMPL | > 1.0 mm is a stack delta. |
| SR-WINDOW (material / thickness) | G4_PARAMETRIC → CLOSURE (H12) | Window is a 5 ATM pressure boundary. |
| SR-BARRIER | G4_PARAMETRIC (compression 0.025–0.10 inside c_optics) + MEASUREMENT | Must not become a window prop (X20). |
| SR-ADHESIVE (retention 0.025–0.10) | G4_PARAMETRIC; bond strength SUPPLIER | Window / cover bond is a seal. |
| MG-SPACING, MG-GUARD | N/A; MEASUREMENT | Optical / electrical. |
| MG-WINDOW-XTALK | MEASUREMENT; G4 keeps W-variant compatibility subject to the 5 ATM screen | Owner threshold null. |
| MG-THERMAL | MEASUREMENT; G4 provides U6 F1/F2/F3 seal and contact geometry | — |
| MG-MAG / MAG_CLEAR (X16) | G4 hard material rule (H18) + MEASUREMENT | Field closure is measurement. |
| AE1401 / AE1410 / AE1420 feed construction; SR-ANTENNAS | G5 (OD-G4-ENTRY); G4 zero-intrusion keep-outs (H17) | No feed dimension may be invented. |
| RF validation; radome dielectric; case-material RF | G5 | — |
| SR-BATT-PACK | G4_PARAMETRIC (supplier max in linear worst) | Radial channel, battery_zone. |
| SR-BATT-PCM | G4_PARAMETRIC (G2 pcm_sweep az 220–240) | J201 MPN is K1 / electrical. |
| SR-BATT-GROWTH | G4_PARAMETRIC (g_axial 0.2–0.5; radial growth inside c_radial, planning max 1.0) | Load path, X20. |
| SR-BATT-NTC | N/A | Electrical. |
| SR-DISPLAY-FPC | G4_PARAMETRIC (fold 0.3–0.6; footprint +0.7 beyond outline) | Land interruption. |
| SR-DISPLAY-LAND | G4_PARAMETRIC (w_land 0.5–1.5; t_land 0.3–0.8) | Land geometry, U4 relief. |
| SR-COVER-LENS | G4_PARAMETRIC (stack t_cover 1.00 / 1.25 / 1.70 unchanged; w_cover_land 0.8–1.5) | X25. |
| Conservative radial margin −0.950 | CLOSURE (H05, section 6) | Case / carrier owned. |
| X25 conservative cover fit −1.100 | CLOSURE (H06, section 6) | Case owned. |
| SR-CHG-MECH / C4 charger geometry | G4_PARAMETRIC for contact / harness data; CLOSURE for case aperture, seal and corridor clearance (H20) | The contact block is a case penetration. |
| SR-BUTTONS | G4_PARAMETRIC (body ≤ 2.03 nom / 1.50 cons; ±7.5° placeholder windows) | Case bores. |
| SR-LRA / E-G4-02 | CLOSURE (valid placement window, H22) with G4_PARAMETRIC envelope classes | Historical position invalid. |
| X21, X22, X24, X14, X15, C7 (DEFERRED_G4) | CLOSURE | Core G4 scope. |
| ATM-Q1…ATM-Q6 | MEASUREMENT (qualification gates, section 8.4) | Geometry cannot qualify. |
| SR-TAGCONNECT, SR-J1-ALIGN | G4 assembly inputs; FABRICATION | Fixtures. |
| P-0402 DC-bias, U7 allocation review | N/A; KICAD_IMPL | — |

Conflicts handed in: DEFERRED_G4 from G3 (C7, X14, X15, X21, X22, X24, X25); REMAINS_OPEN (C1–C4, C6, C8, C9 history,
X13, X17–X19, G2-CROSSING-HEIGHT, G2-BOOK-FOLD, G2-PROBE-RELIEF, G2-BACK-STACK, G2-DISCOVERED-INTERFACES as recorded);
SUPPLIER_DATA_GATED (C5, X10–X12, X20); MEASUREMENT_GATED (X16, X23). Each gains exactly one `g4_status` from:
RESOLVED_BY_G4, REMAINS_OPEN, SUPPLIER_DATA_GATED, MEASUREMENT_GATED, DEFERRED_G5, DEFERRED_K1, OWNER_DECISION_GATED,
with evidence.

## 6. Corner policy and evidence (OD-G4-CORNER)

### 6.1 Evidence classes

Exactly one per material value or claim: OWNER_REQUIREMENT, OWNER_DECISION, MANUFACTURER_VERIFIED (local primary
document + page/table/figure), MANUFACTURER_DATA_REQUIRED, SUPPLIER_DATA_REQUIRED, PROJECT_DERIVED (computed by a
G1–G4 tool), PROVISIONAL_ASSUMPTION (min/nom/max + rationale; the nominal is not the best case; handbook-class seal and
material planning values belong here, never as requirements), MEASUREMENT_REQUIRED, G5_RF_REQUIRED. Never invent a
supplier, manufacturer, RF or material value.

Each limit used by a hard check carries one limit class: **OWNER REQUIREMENT**, **MANUFACTURER REQUIREMENT**,
**SUPPLIER REQUIREMENT**, **PROJECT-DERIVED LIMIT**, **PROVISIONAL PLANNING LIMIT**. A PROVISIONAL PLANNING LIMIT
failure is reported as a planning failure with its threshold; it is never relabelled as a requirement.

### 6.2 Term roles

Every term of every G4 stack (radial, axial, seal, insertion) is tagged exactly one of:
- **DESIGN** — a value G4 chooses; carries a declared **MFG_TOL**;
- **MFG_TOL** — ± manufacturing tolerance of a DESIGN term, PROVISIONAL per process class (declared once in
  `inputs/g4_case_sealing.json.process_classes`, with rationale), until supplier data;
- **SUPPLIER_GATED** — supplier/manufacturer-gated quantity at its planning range; the conservative/worst planning value
  is used in RSS-adverse and linear-worst evaluations until qualified; never narrowed;
- **OWNER_GATED** — options shown, never credited;
- **FROZEN** — G1/G2/G3 values.

Planning ranges of quantities G4 now designs (`D_case_outer` 50.0–51.0, `t_case_wall` 1.0–1.6, `t_carrier_wall`
0.3–0.6, `a_cover` 22.15–23.0, `t_land`, `w_land` as land design) become DESIGN + MFG_TOL **only in G4
evaluations**; the legacy evaluation keeps them as G1/G2 defined them.

### 6.3 Mandatory evaluations (side by side for every check)

1. **LEGACY** — the G1/G2 radial corner, edge-crossing budget and cover-rim checks reproduced through imported
   `mech_model` / `g1_scenarios` / `g2_interconnect` functions. Must equal section 3 exactly, else `check` fails.
2. **NOMINAL** — DESIGN nominal; every other term nominal.
3. **RSS** — nominal + sqrt(Σ (adverse − nominal)²) over MFG_TOL and SUPPLIER_GATED terms (Z using the imported G2
   tolerance policy; radial / seal / insertion using the same single-term-sensitivity method).
4. **LINEAR WORST** — every MFG_TOL and SUPPLIER_GATED term at its adverse limit simultaneously.
5. **GOVERNING TERMS** — per check: the ranked terms governing its linear-worst margin, each with role and evidence
   class, and for each SUPPLIER_GATED term the supplier value at which the margin reaches 0.
6. **OWNER-GATED** — options shown, never credited.

Pass rules: radial, collision and insertion checks pass at **LINEAR WORST** (a collision is binary). Z compliance
follows OD-THICK-REVA (nominal ≤ 16.5 and RSS ≤ 17.0) on both G2-REVA and G2-REVA-HI; linear worst Z is reported.
Seal compression and gland fill pass at **LINEAR WORST**. Plate / stress screens use the G1 conservative sizing case
(simply supported; p max, E min, σ_allow min). No speculative compression, material, adhesive, battery-growth, seal or
supplier credit is used to close any margin.

## 7. Candidates and diameter minimization

Author at least three materially different case architectures in `inputs/g4_case_sealing.json`, evaluated on equal
terms. No outcome may be an input constant.

- **G4-A — polymer midcase** (glass-filled polymer class, PROVISIONAL properties); bonded cover on a bezel ledge;
  screw-retained caseback carrying an integral pod-window frame (P1); radiator volumes metal-free by construction.
- **G4-B — metal midcase with dielectric sectors** covering the complete GNSS_RAD, BLE_RAD and WIFI_RAD azimuth /
  radial / Z volumes; non-metal caseback (P1). Metal only outside the radiator volumes. The dielectric sector geometry
  is a keep-out envelope only; no dielectric material or thickness is selected on RF grounds.
- **G4-C — polymer midcase + split caseback** — metal or ceramic centre plate confined to r below the minimum radiator
  inner radius minus the reported clearance; polymer outer ring; pod frame on the REAR module sealed into the caseback
  aperture (P2).

Property values are PROVISIONAL_ASSUMPTION planning ranges with rationale; none is presented as supplier data. No
family is recommended on an RF argument.

**Diameter minimization (OD-G4-ENVELOPE).** For each candidate the tool sweeps `D_case_body` on a 0.05 mm grid from
47.00 mm to 51.00 mm inclusive, and at each D the candidate's other DESIGN variables over their authored grids. A D
value is feasible if at least one design point passes every hard check of section 9 at the required evaluations.
Per candidate it reports `D_min_feasible` (or "none ≤ 51.0") and the governing check / terms at the next lower grid
value. The tool reports:
- **minimum feasible diameter found** = minimum `D_min_feasible` over all candidates (with its candidate);
- **selected diameter** = the RECOMMENDED candidate's `D_min_feasible`;
- **margin to the 51.0 mm ceiling** = 51.00 − selected diameter;
- if the selected and minimum feasible diameters differ, the ranking reason.
If no candidate is feasible at ≤ 51.00 mm, the tool continues the sweep above 51.00 mm (reporting only, up to 54.00 mm)
to report the **minimum required diameter**, and the verdict is G4 OWNER DECISION REQUIRED (section 13).

## 8. Evaluations (deterministic, in `tools/g4_case_sealing.py`)

### 8.1 Case section and radial closure (conservative radial margin −0.950)

| Variable | Nominal / range | Role / class | Source | Hard stop | Final closure needs |
|---|---|---|---|---|---|
| D_case_body | swept 47.00–51.00 | DESIGN; OWNER REQUIREMENT ceiling | OD-G4-ENVELOPE | > 51.00 | — |
| t_wall(az, z) at MAIN, BATTERY, REAR | grid 0.8–1.6 | DESIGN + MFG_TOL (process class) | stack_parameters `t_case_wall` planning | < t_wall_min(material class) PROVISIONAL | supplier process / FEA |
| t_carrier_wall | grid 0.3–0.6 | DESIGN + MFG_TOL | stack_parameters | < 0.3 | carrier process |
| c_radial (pack → carrier) | planning 0.5–1.0 | SUPPLIER_GATED (1.0 adverse) | stack_parameters | < radial growth | SR-BATT-GROWTH |
| tol_pack_dia | 0.2–0.5 | SUPPLIER_GATED (0.5 adverse) | stack_parameters | — | SR-BATT-PACK |
| t_fpc / c_fpc / R_bend_min | 0.10–0.20 / 0.10–0.30 / 0.6–2.0 | SUPPLIER_GATED | stack_parameters | — | SR-FPC-MECH, SR-CHG-MECH, SR-BATT-PCM |
| front_gap / c_front | G1 thin–thick | FROZEN | zstack | — | — |
| t_land / w_land | 0.3–0.8 / 0.5–1.5 | DESIGN within SUPPLIER_GATED permission | edge_crossings | U4 headroom < 0 | SR-DISPLAY-LAND |

Checks (every evaluation of 6.3): margin_straight_run; edge-crossing margin at land ceiling and at flat exit for
XF-J1501, XC-J202, XB-J201 and XL-LRA (with the re-placed LRA); t_allow_straight for the charger riser; MAIN-to-case
clearance; support bosses at SUP_SW, SUP_SE, SUP_NE and a W/NW support (X14), clipped to r ≥ R_channel_inner (X18);
U4 land headroom with relief or local t_land ≤ 0.74. Outputs: r_case(az, z); the MAIN outline constraint polygon.

Lead arithmetic, for orientation only (the tool recomputes; not a result): the legacy −0.950 is channel-governed —
R_case_inner 23.40 (D 50.0, wall 1.6) − (R_channel_inner 23.85 + t_fpc 0.20 + c_fpc 0.30). With a designed
BATTERY-level wall of 1.00 ± 0.05 and every supplier term adverse (tol_pack_dia 0.5, c_radial 1.0, t_fpc 0.2, c_fpc
0.3, carrier wall 0.40 + 0.05), the linear-worst margin is ≈ +0.25 mm at D 51.0 and ≈ 0.00 mm at D 50.5. Closure
therefore depends on the wall the material class can support and on SR-BATT-GROWTH; no growth credit may be taken.

### 8.2 Cover, bezel and display land (X24, X25 −1.100)

Variables: a_cover (free span; DESIGN ≥ R_display 21.95 + assembly clearance, clearance PROVISIONAL ≥ 0.2);
w_cover_land 0.8–1.5 (SUPPLIER_GATED; 1.5 adverse); cover Ø tolerance (PROVISIONAL, SR-COVER-LENS); t_bezel_min
0.5 / 0.7 / 1.0 (PROVISIONAL PLANNING LIMIT; 1.0 adverse); bezel ledge height.

Checks: cover_outer = a_cover + w_cover_land + cover tolerance ≤ r_bezel_outer − t_bezel_min at linear worst (X25
under OD-G4-CORNER); cover plate re-check for the designed a_cover through the **imported** G1 plate method — the stack
keeps t_cover 1.00 / 1.25 / 1.70 unchanged; any thinner sizing is reported as a Rev-B lever and not credited; air gap
≥ deflection + 0.05 (G1 rule); no case feature proud of the cover outer surface unless it is added to T_total; display
land: unsupported rim arc at the DISP_FPC fold (az 269–295), U4 relief; ALS aperture (az 45–75) and VENT (az 30–60) as
case features with seal ownership.

### 8.3 Caseback, pod and window (ATM-2, ATM-3, ATM-7, X20, X22, X23)

- The caseback outer plane is DESIGNED relative to the REAR skin-face datum; `h_pod` is an output. Constraint:
  t_caseback (outside the pod) + clearance ≤ pod_depth − h_pod (S14 residual before wall 0.55 / 1.05 / 0.25). The
  `h_pod` range is reported per candidate; its closure is MEASUREMENT (wrist / strap trials). T_total is independent
  of `h_pod`.
- Window screen for every variant W0 / W1 / W2 × t_window 0.3 / 0.5 / 0.8 × material class, using the **imported** G1
  Kirchhoff method with unsupported spans taken from the S14 pod polygon (W0: largest inscribed circle of the pod
  opening minus frame overlap; W1: largest cell between ribs; W2: largest per-cell window). The window delta from G2
  nominal (0.3: −0.2, 0.5: 0.0, 0.8: +0.3 mm) is applied to both G2 baselines; a thinner window is not credited as a
  thickness gain.
  Lead finding to verify (not a result): in G1 only 0.8 mm sapphire passes the simply-supported bound at a 10.6 mm span,
  and +0.3 mm puts G2-REVA at 16.65 mm > 16.5, so W0 at 0.5 mm is not expected to pass. If no W0 configuration passes
  without a stack delta, W0 is reported as mechanically eliminated and **OD-G4-WINDOW** is triggered.
- Any rib or frame that supports the window carries load to the pod frame / caseback and hard stops, never to optical
  parts or the REAR board (X20).
- Window deflection at p max < standoff to optics (G3 c_optics sub-allocation) at linear worst.
- Caseback annular-plate screen (Roark closed form; PROVISIONAL properties) between case wall and pod frame:
  deflection < clearance to REAR, charger block and support stops; stress ≤ allowable. Screening only (ATM-Q5).
- P1 versus P2: seal land around the pod ≥ w_seal_min (G3 0.3 / 0.5 / 0.8 PROVISIONAL); a P2 load path through the
  REAR module must be rejected or explicitly justified.
- X22 named budget lines: window retention + barrier compression ≤ c_optics (G3 sub-allocation; overrun → stack
  delta); caseback gasket compression; carrier hard-stop ribs; FPC stiffener — each assigned to an existing layer or
  reported as a Z delta.

### 8.4 5 ATM seal architecture (OD-WATER)

Kept strictly separate in the report:
1. **Deterministic geometry (G4 checks):**
   - seal inventory — every boundary aperture (cover, caseback main seal, pod window(s), charger feedthrough(s),
     SW1–SW5, vent membrane, U6-F3 stud if used, any screw inside the seal line) has exactly one primary seal ID, type
     (adhesive ring / face O-ring / radial O-ring / gasket / membrane), land and seal-band reservation;
   - **seal-path closure** — the enclosure boundary decomposes into sealed interfaces with no gap (graph check);
     every reservation crossing the caseback seal band (G1 `rear_seal_band`: CHG_CONTACT, VENT, any new one) is sealed
     separately; screws lie outside the primary seal line or carry their own seal;
   - gland geometry — cross-section and groove tolerances → compression % and gland fill at linear worst against
     PROVISIONAL planning windows (handbook class, cited as PROVISIONAL_ASSUMPTION pending supplier gasket data);
   - adhesive / bond lands ≥ planning minimum at linear worst (SR-COVER-LENS, SR-ADHESIVE);
   - pressure load path — caseback → case at ≥ 3 screw supports; never through the pack or optics.
2. **Analytical screening (G4, not qualification):** cover, window and caseback plate screens (8.2, 8.3).
3. **Supplier material / process evidence (closure-final):** gasket material and compression set, adhesive strength,
   cover lens, window, vent-membrane water-entry pressure, button seals, contact feedthrough.
4. **Later FEA (specified by G4, executed in Q1):** load cases — p_test nom / max, support conditions, material
   classes, pass metrics for midcase, caseback, cover bond and window bond.
5. **Prototype pressure testing (Q1)** — qualification gates carried exactly from G1 (`architecture.md` G1.4):
   - **ATM-Q1** select the 5 ATM test standard and margin (owner / qualification plan);
   - **ATM-Q2** button seal pressure / cycling test after SR-BUTTONS selection (window variant under 5 ATM - the G1.3
     window plate calculation is analytical only and any clamped-only pass is conditional on verified bond restraint);
   - **ATM-Q3** sealed charger contact feedthrough pressure test (SR-CHG-MECH);
   - **ATM-Q4** vent membrane water-entry pressure >= test pressure and barometer response;
   - **ATM-Q5** caseback deflection analysis once the caseback material/thickness exist (G3), then a pressure test with
     the REAR module fitted;
   - **ATM-Q6** swim / dynamic exposure as stated by the selected standard.

No statement in any G4 output may claim 5 ATM water resistance or qualification.

### 8.5 Battery carrier

LPR454440 unchanged. Finished-pack envelope as SUPPLIER_GATED ranges (Ø44 + 0.2–0.5; battery_zone 4.75 / 5.00 / 5.50;
g_axial 0.2–0.5; c_axial 0.05–0.2). PCM lobe sweep az 220–240 (G2 `pcm_sweep`) clear of SW3 and supports; insulation
layer; carrier retention. Checks: pack + growth inside the carrier at linear worst; no load path through the pack
(X20); BATT_EXIT / tail clearance; insertion path.

### 8.6 RF radiator-volume keep-outs (geometry only; OD-G4-ENTRY)

GNSS_RAD (az 346.4–18.9, r 20.13–24.37, all Z), BLE_RAD (az 304.1–331.8, r 15.80–25.15, MAIN), WIFI_RAD (az
107.7–128.8, r 20.59–25.24, MAIN+REAR), clipped to the G4 case. Hard (H17): zero intrusion of new conductive material
(metal case or caseback, screws, inserts, button pushers, lugs / spring bars, charger hardware, display-land metal)
and of any new wiring / interconnect; feed spans left reserved up to the G2 upper bounds (AE1420 12.528, AE1401 10.630,
AE1410 9.434 mm) without inventing any feed construction. Reported, not required: distance from every conductive
feature to each radiator volume; lug ↔ GNSS_RAD interaction at 12 o'clock (input to OD-G4-STRAP). No RF performance,
efficiency, detuning or dielectric statement is made; final case material and radome dielectric are not frozen
(OD-G4-MATERIAL, G5).

### 8.7 Buttons SW1–SW5

Azimuth windows fixed by G2 discovered interfaces (SW1 292.5–307.5, SW2 262.5–277.5, SW3 232.5–247.5, SW4 52.5–67.5,
SW5 112.5–127.5); body height ≤ 2.03 nom / 1.50 cons; bore length ≥ L_bore_min (PROVISIONAL 1.5–3.0, SR-BUTTONS)
achieved by wall thickness or a permitted boss (≤ +1.0 mm radial, inside the button's azimuth window, section 2.2).
Checks: bore vs radiators (SW5 × WIFI_RAD, C7); SW4 × MAG_CLEAR (non-ferromagnetic pusher); SW2 / SW3 vs the CHG_RISER
slot (az 249–259); SW1–SW3 vs DISP_FPC / J1; bore vs rear-insertion path (pushers installed after module insertion or
flush); pusher travel envelope (SUPPLIER).

### 8.8 Charger aperture / feedthrough

CHG_CONTACT block (az 80–100, r 17.5–24.0 placeholder, SR-CHG-MECH): inside the caseback, outside the S14 REAR outline
(≥ 1.100 mm plan, frozen) and the pod seal land; separate feedthrough seal (ATM-5 / ATM-Q3); keying recess, no magnet;
dock force path via the caseback rim and stops; U6 distance (8.367 mm, frozen) reported; MAG_CLEAR overlap reported
with no new ferromagnetic material; CHG_ROUTE / CHG_LINK / CHG_RISER / CHG_APPROACH clearance to the case section at
linear worst (t_allow_straight). J202 stays west (G2).

### 8.9 LRA re-placement (E-G4-02)

The historical LRA reservation is invalid (section 3.1). The tool searches deterministically, at REAR level, for an
LRA placement window:
- envelope classes: coin and linear LRA envelopes as PROVISIONAL_ASSUMPTION ranges with rationale (SR-LRA), each
  evaluated at its maximum; no MPN;
- search grid: azimuth 0–355° step 5°, radius in 0.25 mm steps, orientation 0 / 90° for linear classes;
- feasible window = every pose whose envelope (plus PROVISIONAL clearance) stays outside, at linear worst: the S14
  REAR outline and pod, U6 island and tail corridor (incl. conservative tail corridor), FPC_UNDER, CHG_ROUTE,
  CHG_LINK, CHG_CONTACT, caseback seal band and pod seal land, the case inner wall r_case(az, REAR), battery pack +
  growth projection where Z-overlapping, button bores, radiator volumes (as conductive material), support stops, and
  fits the REAR-level Z budget (lower web to caseback);
- MAG_CLEAR: an LRA envelope inside MAG_CLEAR is not feasible; outside it, the distance to U703 is a ranking metric
  (OD-G4-LRA-MAG pending);
- reported: the numeric placement window (azimuth / radius ranges per envelope class), the ranked recommended pose,
  distance to U703, lead path to U7 (G2 U7-B.Cu allocation) and its edge crossing (XL-LRA, section 8.1).

No KiCad movement occurs. If no feasible pose exists for any envelope class inside the approved architecture and
`D_case_body` ≤ 51.0 mm: **STOP** (section 13). The LRA is never silently removed or shrunk below its envelope class.

### 8.10 Assembly / insertion paths

Deterministic sequence (extends G2 S0–S3): case sub-assembly (cover bond, vent membrane, window into caseback for P1 as
a pressure-testable sub-assembly); REAR + tail bonded and tested (thermode access before carrier); module stack (MAIN
+ carrier + pack + REAR; display hinged and mated visibly per G2 S2); rear insertion into the case; display seated on
DISP_LAND; buttons; charger block; caseback + gasket + screws. Checks: rear-insertion path — module maximum radius at
each Z vs the case's minimum bore radius rearward of DISP_LAND at linear worst; an access direction for every
operation; battery isolation state before each manipulation; service / rework reversal (REAR + tail replaced as one
unit; J1 budget 50 rated / 25 planned cycles).

### 8.11 Lugs (envelope only)

Lug reservations at 12 and 6 o'clock with inner width parameter 20–22 mm (PROVISIONAL, OD-G4-STRAP), excluded from
`D_case_body`; checked against GNSS_RAD (conductive material rule H17), buttons and caseback screws. No strap
interface is chosen.

## 9. Hard checks (candidate eligibility)

| ID | Check | Required evaluation | Limit class |
|---|---|---|---|
| H01 | G2-REVA and G2-REVA-HI reproduced; G4 Z delta 0.000 | exact | PROJECT-DERIVED LIMIT |
| H02 | T_total ≤ 16.5 nominal and ≤ 17.0 RSS on both baselines | nominal, RSS | OWNER REQUIREMENT |
| H03 | D_case_body ≤ 51.00; bosses only as permitted, ≤ +1.0 mm | linear worst | OWNER REQUIREMENT |
| H04 | LEGACY numbers of section 3 reproduced exactly | exact | PROJECT-DERIVED LIMIT |
| H05 | Radial channel and edge-crossing margins ≥ 0, every crossing | linear worst | PROJECT-DERIVED LIMIT |
| H06 | X25 cover fit and bezel wall ≥ t_bezel_min | linear worst | PROVISIONAL PLANNING LIMIT (bezel) |
| H07 | Cover plate sizing ≥ requirement for designed a_cover; air-gap rule | G1 conservative | PROJECT-DERIVED LIMIT |
| H08 | No case feature proud of the cover unless counted in T_total | exact | OWNER REQUIREMENT (T_total convention) |
| H09 | U4 land headroom ≥ 0 (relief or local t_land) | linear worst | PROJECT-DERIVED LIMIT |
| H10 | Pack + growth inside carrier; no pack load path | linear worst | SUPPLIER REQUIREMENT (pending) / PROJECT-DERIVED |
| H11 | Caseback wall fits the pod residual; h_pod ≥ 0 | linear worst | PROJECT-DERIVED LIMIT |
| H12 | ≥ 1 window variant passes the simply-supported screen without Z delta | G1 conservative | PROVISIONAL PLANNING LIMIT |
| H13 | Window / caseback deflection < clearance to optics / REAR at p max | linear worst | PROJECT-DERIVED LIMIT |
| H14 | Seal inventory complete; seal path closed; separate feedthrough seals | exact | PROJECT-DERIVED LIMIT |
| H15 | Gland compression and fill inside window | linear worst | PROVISIONAL PLANNING LIMIT |
| H16 | Seal / bond lands ≥ planning minimum | linear worst | PROVISIONAL PLANNING LIMIT |
| H17 | Zero new conductive / wiring intrusion into radiator volumes | exact | PROJECT-DERIVED LIMIT (G2 acceptance, OD-G4-ENTRY) |
| H18 | No new ferromagnetic material inside MAG_CLEAR | exact | PROJECT-DERIVED LIMIT (invariant, X16) |
| H19 | S14 outline, pod, supports, tail exit (incl. conservative corridor), U6 island untouched and unobstructed | linear worst | PROJECT-DERIVED LIMIT (frozen) |
| H20 | Charger block, feedthrough and corridors clear | linear worst | PROJECT-DERIVED LIMIT |
| H21 | Buttons: bore length, body height, radiator / MAG / insertion clearances, boss limits | linear worst | PROVISIONAL / SUPPLIER REQUIREMENT (pending) |
| H22 | LRA placement window non-empty; recommended pose collision-free | linear worst | PROVISIONAL / SUPPLIER REQUIREMENT (pending) |
| H23 | Rear-insertion path collision-free; every operation has an access direction | linear worst | PROJECT-DERIVED LIMIT |
| H24 | ≥ 4 case / caseback supports incl. W/NW (X14), all outside the pack (X18) | exact | PROJECT-DERIVED LIMIT |
| H25 | No KiCad / interface / immutable-file change | exact | PROJECT-DERIVED LIMIT |

## 10. Selection and ranking

A candidate is ACCEPTABLE if every hard check passes at its required evaluation at its `D_min_feasible` and every
remaining unknown is SUPPLIER_DATA_REQUIRED, MANUFACTURER_DATA_REQUIRED, MEASUREMENT_REQUIRED or G5_RF_REQUIRED with a
numeric threshold. Rank lexicographically:

1. no frozen-invariant / owner-decision impact;
2. G4 Z delta 0 and larger OD-THICK-REVA headroom on G2-REVA-HI;
3. smaller `D_min_feasible` (OD-G4-ENVELOPE minimization);
4. larger minimum linear-worst radial / cover margin at that diameter (H05, H06);
5. fewer SUPPLIER_GATED terms governing a linear-worst margin, and less demanding supplier zero-margin values;
6. 5 ATM screening margins (H12–H16) and fewer seals;
7. larger distance of conductive features to radiator volumes (no RF claim);
8. larger MAG_CLEAR / U703 distances (LRA, charger, screws);
9. assembly / service simplicity (operations, blind matings, J1 cycles).

ID breaks exact ties only. Outcome per candidate: RECOMMENDED / CONDITIONAL (names the discriminating value and
threshold) / REJECTED, with reasons. No optimality is claimed outside the finite design space.

## 11. Validation (all must exit 0)

```
python3 -B design/mechanical/tools/mech_model.py check
python3 -B design/mechanical/tools/g1_scenarios.py check
python3 -B design/mechanical/tools/g2_interconnect.py check
python3 -B design/mechanical/tools/g3_rear_optical.py check
python3 -B design/mechanical/tools/arch_diagrams.py check
python3 -B design/mechanical/tools/g4_case_sealing.py check
python3 -B design/mechanical/tools/g4_case_sealing.py selftest
git diff --exit-code afb19ac173ce67c7e9599313cc5a0942e026ade9 -- design/mechanical/inputs/input_register.json design/mechanical/inputs/stack_parameters.json design/mechanical/inputs/package_heights.json design/mechanical/inputs/g1_scenarios.json design/mechanical/inputs/g2_interconnect.json design/mechanical/inputs/g3_rear_optical.json design/mechanical/tools/mech_model.py design/mechanical/tools/mech_model_spec.md design/mechanical/tools/g1_scenarios.py design/mechanical/tools/g2_interconnect.py design/mechanical/tools/g3_rear_optical.py design/mechanical/generated/zstack.json design/mechanical/generated/zstack.md design/mechanical/generated/zstack_section.svg design/mechanical/generated/main_height_map.json design/mechanical/generated/main_height_map.md design/mechanical/generated/main_height_map.svg design/mechanical/generated/g1_scenarios.json design/mechanical/generated/g1_scenarios.md design/mechanical/generated/g2_interconnect.json design/mechanical/generated/g2_interconnect.md design/mechanical/generated/g2_allocation.svg design/mechanical/generated/g3_rear_optical.json design/mechanical/generated/g3_rear_optical.md design/mechanical/generated/g3_rear_faces.svg design/mechanical/generated/g3_rear_section.svg design/mechanical/generated/perimeter_map.svg design/mechanical/generated/rear_module_concept.svg design/mechanical/generated/interconnect_paths.svg design/mechanical/PHASE_BRIEF.md design/mechanical/G1_BRIEF.md design/mechanical/G2_BRIEF.md design/mechanical/G3_BRIEF.md
git diff --exit-code <G4_BRIEF commit> -- design/mechanical/G4_BRIEF.md
git diff --exit-code 168badbab6de1201bb3209902a53fe1e4b874cc9 -- design/mechanical/inputs/stack_parameters.json design/mechanical/inputs/package_heights.json design/mechanical/inputs/g1_scenarios.json design/mechanical/tools/mech_model.py design/mechanical/tools/mech_model_spec.md design/mechanical/tools/g1_scenarios.py design/mechanical/generated/zstack.md design/mechanical/generated/zstack_section.svg design/mechanical/generated/main_height_map.md design/mechanical/generated/main_height_map.svg design/mechanical/generated/g1_scenarios.json design/mechanical/generated/g1_scenarios.md
python3 -B -c '<G2_BRIEF.md section 9 B semantic provenance check, unchanged>'
python3 -B -c '<architecture.json g1/g2/g3 blocks semantically equal to afb19ac; conflicts differ only by an added g4_status; architecture.md G1/G2/G3 sections byte-identical>'
git diff --exit-code afb19ac173ce67c7e9599313cc5a0942e026ade9 -- '*.kicad_pcb' '*.kicad_sch' '*.kicad_pro' '*.kicad_prl' design/interfaces design/placement rear_sensor libraries
test -z "$(git diff --name-only afb19ac173ce67c7e9599313cc5a0942e026ade9 -- . ':(exclude)design/mechanical/**')"
git diff --check
```

The two `python3 -B -c '<…>'` lines are semantic checks the implementer writes out in full in the G4 run record; their
logic is fixed by their description here and may not be weakened.

`g4_case_sealing.py check` regenerates every output in memory and fails on: any byte difference; a source-hash
mismatch (pins: `inputs/stack_parameters.json`, `inputs/package_heights.json`, `inputs/input_register.json`,
`inputs/g1_scenarios.json`, `generated/g1_scenarios.json`, `inputs/g2_interconnect.json`,
`generated/g2_interconnect.json`, `inputs/g3_rear_optical.json`, `generated/g3_rear_optical.json`,
`generated/zstack.json`, `generated/main_height_map.json`, the `architecture.json` projection of `reservations`,
`rear_module`, `g2.reservations` and `edge_crossings`, and `inputs/g4_case_sealing.json`); a LEGACY mismatch; a hard
check failing for the RECOMMENDED candidate; an unreported nonzero Z delta; a selected diameter that is not the
RECOMMENDED candidate's `D_min_feasible`; or a size / runtime budget overrun (section 4.4). Imported G1/G2/G3
functions and tolerance policies are used, never re-implemented.

`selftest` proves that each injected fault is caught: radial collision at linear worst; a LEGACY value mutated;
T_total 16.501 nominal; D_case_body 51.01; an unpermitted boss; an aperture without a seal (open seal path); O-ring
overcompression; a conductive part inside GNSS_RAD; new wiring inside WIFI_RAD; a ferromagnetic screw inside
MAG_CLEAR; an obstructed S14 support land; an LRA pose inside the REAR outline; an LRA hidden in the lower web; a
rear-insertion collision; a mirrored REAR transform; a window variant credited with a thickness gain; a supplier-gated
term narrowed below its planning range.

`arch_diagrams.py check` verifies the g4 summary against the generated JSON (hash + key-wise), exactly one
`g4_status` per conflict, the OD-G4-RECORD status line, and that the G1/G2/G3 sections and blocks are unchanged.

## 12. Acceptance criteria

1. Section 2.2 decisions recorded verbatim; all earlier decisions and invariants unchanged; interface unchanged;
   "G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES" recorded in `README.md` / `architecture.md` without editing the
   generated G3 verdict or closing any G3 gate.
2. Errata E-G4-01 and E-G4-02 recorded in `architecture.json.g4.errata` and the report.
3. ≥ 3 candidates (section 7) evaluated on equal terms; every candidate has an outcome with reasons.
4. LEGACY numbers reproduced exactly; LEGACY / NOMINAL / RSS / LINEAR WORST / GOVERNING TERMS / OWNER-GATED reported
   per check.
5. RECOMMENDED candidate passes H01–H25 at the evaluations of section 9.
6. Selected diameter, minimum feasible diameter found, and margin to 51.0 mm reported.
7. Conservative radial margin and X25 dispositioned numerically under OD-G4-CORNER with governing terms and the
   supplier values for zero margin; the legacy −0.950 / −1.100 shown unchanged beside them.
8. G4 Z delta 0.000 on G2-REVA and G2-REVA-HI, or verdict OWNER DECISION REQUIRED (OD-G4-STACK).
9. Seal inventory, seal path, gland / land / plate screens complete; FEA load cases and ATM-Q1…ATM-Q6 carried; no 5 ATM
   claim.
10. Radiator keep-outs enforced; G5 handoff complete; no RF claim; final material not frozen.
11. LRA placement window numeric and non-empty, with a recommended pose.
12. Handoff (section 14) complete and numeric.
13. All section 11 commands exit 0; changes confined to section 4.3 files; size and runtime budgets met.
14. Verdict exactly one of: **G4 PASS**; **G4 CONDITIONAL — SUPPLIER/RF/QUALIFICATION GATES OPEN**; **G4 OWNER DECISION
    REQUIRED**; **G4 FAIL**.
15. G4 PASS (final) additionally requires SR-COVER-LENS, SR-DISPLAY-LAND, SR-DISPLAY-FPC, SR-BATT-PACK, SR-BATT-GROWTH,
    SR-BATT-PCM, SR-BUTTONS, SR-CHG-MECH, SR-LRA, SR-WINDOW / SR-ADHESIVE and the SR-FPC-MECH bend / exit data
    supplier-confirmed within the evaluated ranges, and OD-G4-ATM-STD, OD-G4-MATERIAL, OD-G4-STRAP and OD-G4-LRA-MAG
    decided. Otherwise the verdict is at most CONDITIONAL, with each open item and threshold listed. G5 RF acceptance
    is never a G4 criterion; G4 PASS remains subject to G5 re-entry.

## 13. Stop conditions

- A candidate needs a frozen-invariant, G2-allocation, G3-placement, net, footprint, schematic or interface change:
  mark it OWNER DECISION REQUIRED and continue; if no candidate is acceptable without one, verdict G4 OWNER DECISION
  REQUIRED and stop.
- **Diameter:** no candidate is feasible at `D_case_body` ≤ 51.00 mm: report the minimum required diameter (section
  7) and its governing checks / terms; verdict G4 OWNER DECISION REQUIRED; stop. Never exceed 51.0 silently.
- **LRA:** no feasible LRA pose exists for any envelope class inside the approved architecture at ≤ 51.0 mm: report
  the blocking reservations per azimuth; verdict G4 OWNER DECISION REQUIRED; stop. Do not remove the LRA.
- No window variant passes H12 without a Z delta: report variants, deltas and OD-THICK-REVA headroom; verdict G4 OWNER
  DECISION REQUIRED (OD-G4-WINDOW / OD-G4-STACK); stop.
- Any nonzero Z delta: report; verdict G4 OWNER DECISION REQUIRED (OD-G4-STACK).
- A margin can be closed only with a speculative compression, material, adhesive, growth, seal or supplier credit: do
  not take it; report the deficit.
- A required input is missing or contradictory, or the live repository disagrees with this brief: stop and report.
- Any immutable file would have to change, or a deterministic check fails and cannot be fixed in scope: stop.

## 14. G4 handoff (numeric, in `generated/g4_case_sealing.json.handoff`)

To K1, G5 and Q1: selected `D_case_body`, minimum feasible diameter and margin to 51.0; Z-stratified r_case(az, z);
**MAIN outline constraint polygon** with support / boss / bore notches; MAIN and REAR placement transforms (unchanged
from G2 / G3, restated); caseback / pod envelope and the P1/P2 result; `h_pod` range; seal lines and lands (cover,
caseback, pod, feedthroughs, buttons, vent); screw / support positions; battery carrier envelope and PCM lobe window;
sensor-FPC / charger / battery-tail / LRA-lead paths with linear-worst margins; hard keep-outs (radiator volumes,
MAG_CLEAR, U6 island, optical apertures, thermode / tail corridors); charger contact geometry window; button bore
windows and bosses; **LRA placement window and recommended pose**; lug envelopes; tolerance stacks per check with
governing terms; assembly directions and sequence; supplier values needed for zero margin; FEA load cases; ATM-Q1…Q6;
explicit open gates (supplier, G5, measurement, owner). G4 authorizes nothing downstream.

## 15. Later phases (defined here; not authorized by G4)

- **G5 — RF / antenna integration:** SR-ANTENNAS data; AE1420 / AE1401 / AE1410 feed construction and its Z / length /
  bend allocation; radome / dielectric design and validation; RF simulation; case-material RF validation; RF
  acceptance. **G5 may require G4 re-entry** (envelope, radiator volumes, case material, lugs) if real RF evidence
  proves the G4 assumptions incompatible (OD-G4-ENTRY).
- **K1 — KiCad allocation implementation:** entry criteria in section 16.
- **Q1 — qualification:** ATM-Q1…ATM-Q6; FEA execution; MG-SPACING, MG-WINDOW-XTALK, MG-GUARD, MG-THERMAL, MG-MAG;
  wrist / strap `h_pod` trials.

## 16. K1 entry criteria (for the record; not authorized by G4)

K1 may start only when all of the following hold:
1. explicit owner authorization of K1 and an independently reviewed K1 contract;
2. G4 closed (≥ CONDITIONAL) and independently reviewed, with its MAIN outline constraint polygon, REAR transform,
   LRA placement window and keep-outs accepted;
3. SR-REAR-PCB HDI stackup supplier-qualified (≥ 4 layers; filled / capped microvia-in-pad at 0.4 mm pitch;
   0.6–1.0 mm);
4. SR-MAX86141-LAND resolved against AN1891 / 21-100134 (a footprint review separately authorized if it differs);
5. SR-SFH4053B-DS footprint / seated height / emitting area verified and the D405–D407 geometry re-run;
6. SR-MAX86141-HEIGHT and SR-TS5A12301E-HEIGHT within the G3 thresholds;
7. SR-FPC-MECH: J1501 / J1502 MPN, land, pitch, rows and a verified mirrored physical mating map, with the 24-position
   / 13-net interface unchanged;
8. J1502 conservative tail fit resolved;
9. C1501 qualified or DNP retained;
10. P-0402 DC-bias / effective-capacitance evidence;
11. U7 control / power / decoupling allocation review;
12. SR-BATT-PCM sufficient for the J201 MPN;
13. G5 acceptance of any MAIN-edge or feed-region change near AE1420 / AE1401 / AE1410 (protected C1420 / C1421 /
    R1420 untouched);
14. assembly / isolation fixtures validated.

K1 is limited to outline, placement, stackup and rules; general routing stays separately gated.

## 17. Execution roles (recommendation recorded with the contract)

- Primary G4 implementer: **Claude Opus 5.5, fresh session** (repo lane `opus-fresh`), contract = this brief.
- Independent reviewer (different family): **`codex-sol` lane** (high effort). Resolve the concrete model ID from the
  current routing configuration at review time. Currently observed mapping (`docs/ai/routing.json`, 2026-10-14):
  `gpt-6.1-sol` — an observation, not a permanent contract requirement.
- The lead does not implement G4 in the contract session.

## 18. Independent review must challenge

- LEGACY reproduction, and that no negative margin disappeared by relabelling; DESIGN vs SUPPLIER_GATED tagging of
  every radial term; MFG_TOL values declared per process class and identical across candidates; c_radial vs radial
  growth with no growth credit.
- Diameter minimization: grid, feasibility rule, selected vs minimum feasible diameter, 51.0 ceiling, boss rule.
- X25 closure: cover free span, land, tolerance, bezel; cover stack not thinned or credited.
- Window / caseback screening inputs (spans from the S14 pod polygon), support assumptions, X20 load path, W0 status.
- Seal-path completeness (every aperture), gland arithmetic, PROVISIONAL limits not presented as requirements; ATM-Q1…Q6
  carried exactly; no 5 ATM claim.
- Radiator keep-outs against every conductive feature and new wire (screws, pushers, lugs, charger, land); no RF claim;
  no material freeze on RF grounds.
- MAG_CLEAR material rule; LRA search completeness, envelope classes, the E-G4-02 disposition, OD-G4-LRA-MAG left open.
- Insertion path and access directions; battery isolation; rework.
- G1 / G2 / G3 immutability; Z delta 0; no KiCad change; state-format size and runtime budgets.
