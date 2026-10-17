# G4-R2A amendment — owner decisions, rounds 3 to 6 (PCM envelope, battery alternative, support ring, REAR-side charger)

Status: contract amendment drafted 2026-10-17 and revised the same day for the round-4 to round-6 owner answers, for owner approval and the lead contract commit. It amends
`design/mechanical/G4_R2_BRIEF.md` (contract commit `8f8990450fd2a482ef35c4b0314743261840751e`, immutable) and is read
together with it. Everything in `G4_R2_BRIEF.md` stays in force unless a section below says "replaces", "retires" or
"extends". Provisional, reversible, deterministic mechanical study work. It authorizes **no KiCad edit**, no MPN, no
supplier claim, no supplier-request issuance, no RF / 5 ATM / structural / optical / adhesive qualification claim, no
case CAD and no later phase (G5, K1, K1-A, Q1). It does not reopen G1 or G3 except as section 9 states.
Destination: `design/mechanical/G4_R2A_AMENDMENT.md`. Work branch: `mechanical/g4-r2-package-closure`.

Entry record (read-only, pinned): the committed R2 study at `5d6d493` ("G4-R2 tool and results", verdict **G4-R2
BLOCKED**: S04 LRA, S06 charger vs seal, S08 J1501 / J202 unplaced, S14 PCM / reserved region) and the independent
review (MiMo): RESULT VALID WITH MINOR. The four minor findings (checked against the review text) are section 8.

Ids: `R2A-` is not used; this amendment continues the R2 id spaces (`R2-Hnn`, `R2-Snn`, `R2-Vnn`, `OV-*`, `C-R2-nn`) and
adds `C-R2A-01`, `R2-H29..H32`, `R2-V28..V32`, `Q-R2A-*`. Identifiers it replaces keep their number.

## 1. Authority, files and immutability

1. Round-3 to round-6 owner decisions (section 2) are binding and are recorded verbatim. Section 3 is the binding lead application.
2. `R2_FILES` (R2 section 4.6) gains `design/mechanical/G4_R2A_AMENDMENT.md`. The builder updates **in place** the
   existing R2 paths `tools/g4_r2_closure.py`, `inputs/g4_r2_closure.json` and `generated/g4_r2_closure.{json,md}`,
   `g4_r2_plan.svg`, `g4_r2_sections.svg`, `g4_r2_annulus.svg` (and `g4_r2_sweep.jsonl` only if >2 MB). No other path
   may change. Baseline for R2 section 4.1 immutability is now `5d6d493` for every path outside that set.
3. The R2 record at `5d6d493` is history. Its `generated/g4_r2_closure.json` blob is pinned by SHA-256 in the new
   inputs (`r2_record_sha256`, read from `git show 5d6d493:<path>`, hash-checked) and is the "R2 column" of every
   changed result. Results carry `amendment: "R2A"` and the round-3 to round-6 decisions in `owner_decisions`.
4. R2 section 4.4 historical reproduction is unchanged **plus** one row: R2 at its pin (read-only detached worktree at
   `5d6d493`: `g4_r2_closure.py check` and `selftest` exit 0, counts equal to the counts recorded at that commit).
5. Owner decisions are recorded only in R2A files (as R2 section 3.2): not in `input_register.json`,
   `architecture.*` or `README.md`.

## 2. Owner decisions 2026-10-17, rounds 3 to 6 (verbatim)

Record in `inputs/g4_r2_closure.json.open_question_answers` and `generated/g4_r2_closure.json.owner_decisions`
(date 2026-10-17, source: owner decision, `G4_R2A_AMENDMENT.md` section 2, round 3 to round 6 as labelled).

Round 3:

```text
- OD-BATT-PCM: PCM planning envelope from owner photos and supplier statement
  ("PCM is built to order"): radial protrusion <= 1.5 mm, chord width <= 15 mm,
  Z within cell + 0.3 mm. PCM/lead-exit azimuth is a design variable searched
  0-355 step 5 and becomes part of the battery order spec; the G2 220-240 window
  no longer binds. Evidence class: OWNER_PLANNING_ENVELOPE, gate SR-BATT-PCM.
- OD-BATTERY-ALT: evaluate LPR433736 (585 mAh, Ø37 x 4.3) and LPR443633 (540 mAh,
  3.7 V, 1C, Ø36 x 4.4, catalogue) side by side; LPR443633 replaces LPR403736 as
  the reported alternative. Zero total Z growth (Delta 0.200 / 0.100 mm to the
  REAR band). The tool never selects; the owner chooses after the run.
- Q-R2-SUPPORT-RING: ACCEPTED — case-side battery supports start above the cup
  wall top (Z 4.630 mm, the relieved ledger).
- OD-CHG-REAR: charger contacts pass through the ceramic caseback plate INSIDE the
  main seal, land on the REAR board, and reach MAIN through spare positions of the
  existing 24-position MAIN-REAR FPC (VBUS on >= 2 positions; FPC net count rises
  from 13). J202 and the 3 o'clock charger block/land are retired. REAR may gain
  the charger contact pads/spring contacts only; no existing REAR part moves
  (G3-B-S14 positions frozen). Plate feedthroughs get the hole K_t; the ring stays
  continuous. Gates: SR-CHG-MECH (sealed feedthrough), SR-FPC-MECH (pin current).
```

Round 4 (status DECIDED; each answer is applied by the sections named in 3.1):

```text
- Q-R2A-FPC-SPARE: correction of round 3 — the 24-position FPC has no
  spare positions. Reassign 2 of the 10 GND positions to VBUS (8 GND
  remain; nets 13 -> 14). Connector parts, position count and J1502 are
  unchanged; only the net map changes. VBUS positions adjacent to GND
  positions, never adjacent to an SPI clock position. The tool proves
  >= 3 GND positions remain for VLED return and reports the final map.
- Q-R2A-BLOCK: the 4 x 5 mm contact block rule does not apply to the
  caseback charger. Replace it with two discrete round contacts
  (planning pad Ø2.0 mm; pitch and position are search variables;
  supplier gate SR-CHG-MECH).
- Q-R2A-MAG: contact azimuth is searched 0-355 (not east only). Contacts
  must be non-ferrous (no magnet or ferrous part on the watch side); on
  that condition they are allowed inside MAG_CLEAR, and the distance to
  BMM350 is reported.
- Q-R2A-ESD: REAR may gain exactly one TVS diode (0201 or 0402 class)
  next to the charger pads, inside the charger pad region. This is the
  only component exception to "pads only"; the G3 proof (section 9)
  must allow exactly that one item and nothing else.
- Q-R2A-K1A: confirmed. The charger pads, the TVS and the VBUS net-map
  change are fixed inputs to the future K1-A contract.
```

Round 5 (status DECIDED; applied by 3.1, 6.5, 7.2, 13.1):

```text
- Q-R2A-VBUS-ADJ: VBUS uses FPC positions 19 and 20 (adjacent to each
  other). The "adjacent to GND" requirement is dropped; the rule is only
  "never adjacent to the SPI clock position". Tool proves >= 3 GND
  positions remain for VLED return and reports the final map.
```

Round 6 (status DECIDED):

```text
- Q-R2A-BLE-DEPTH: for the new charger items only (two pads, two spring
  contacts, one TVS, their lands), the BLE and Wi-Fi reserved sectors
  apply at ALL Z levels: no charger item may lie inside the plan
  footprint of BLE_RAD or WIFI_RAD or their owner clock sectors. All
  other items keep the frozen reserved Z levels. The excluded sector is
  reported.
- Q-R2A-VERDICT-TIMING: confirmed. The tool emits per-battery verdicts;
  the package verdict is withheld until the owner's battery-selection
  record.
```

## 3. Application and supersession (binding lead application; changes need an owner amendment)

Each reading below is also listed in section 13. None is a new decision.

| Decision | Binding R2A consequence | Superseded / retired (overlay) | Not authorized |
|---|---|---|---|
| OD-BATT-PCM | One adverse PCM lobe at every corner (no nominal credit): a flat-faced lobe, tangential chord width 15.0 mm centred on the exit azimuth, outer face at `R_pack(lw) + g_radial(adverse) + 1.5 mm` from the pack centre (radial protrusion measured from the same envelope radius that R2-V06 contains), Z extent `[Z_pack_bottom, Z_pack_bottom + t_cell + 0.3]`. The report adds a diagnostic column without `g_radial`. Exit azimuth is a design variable `az_pcm` 0-355 step 5, part of the joint design point and of the "battery order spec" in the handoff. Evidence class `OWNER_PLANNING_ENVELOPE` (a labelled sub-class of OWNER_DECISION, never SUPPLIER_DATA); gate SR-BATT-PCM. A recorded SR-BATT-PACK / -PCM document contradicting it raises R2-S09 as before. The lobe solid is the chord rectangle from the pack envelope radius `R_pack(lw) + g_radial(adverse)` out to the outer face; the volume inside the pack envelope belongs to the pack alone (R2 6.8 rule 3). | `inputs.lobe` radial 1.5 / 2.5 / 3.0 and tangential 5.0 / 6.5 / 8.0 (OV-PCM-ENV); `grids.pcm_az_range_deg` 220 / 230 / 240 and the G2 `pcm_az_deg` window as a binding window (OV-PCM-AZ). The G2 BATT_TAIL reservation (az 181.3-236.6) is carried as a corridor **of fixed angular width translated to the chosen `az_pcm`**; any pinned reservation it then overlaps binds (13.2 item 4) | any supplier or capacity claim; ordering the cell |
| OD-BATTERY-ALT | Batteries: LPR433736 (Ø37.0 x 4.3, Delta 0.200) and LPR443633 (Ø36.0 x 4.4, 540 mAh, 3.7 V, 1C, Delta 0.100). Both are `catalogue_value`, OWNER_DECISION, gate SR-BATT-PACK; planning tolerances and growth are the unchanged R2 6.2 values, absolute, not rescaled. LPR403736 is not evaluated in R2A (its R2 values stay in the R2 column). **The tool never selects.** No package verdict is emitted before an owner battery-selection record (section 12). | OV-BATT-ALT (replaces the LPR403736 catalogue row); R2 7.1.6 fallback rule, `fallback_trigger`, Q-R2-BATTERY (all retired, no model switch of any kind); R2 12 "package verdict is the LPR433736 verdict" | energy / runtime claims; choosing a battery |
| Q-R2-SUPPORT-RING | The "relieved" ledger variant is binding: every case-side battery support starts at `Z_support_start = cup wall top + the relieved-ledger offset of R2` (4.630 mm at the R2 joint point; recomputed per battery and cup row, never typed). The as-pinned variant stays as a reported column. The `periphery_shortfall_with_zone_b_supports_relieved_mm` value becomes the headline periphery shortfall. R2-H18 is re-evaluated at the new support Z (>= 4 supports incl. W/NW outside the offset pack envelope) and reports the support Z start `Z_support_start` and the unchanged radial engagement. | OV-SUPPORT-RING (as-pinned support Z) | moving a support in plan |
| OD-CHG-REAR | Section 6 (lane L-CHG-R, `C-R2A-01`), section 7 (FPC), section 9 (G3: pads, spring contacts and one TVS). Refined by the round-4 to round-6 answers (3.1). | OV-CHG-LANE, OV-FPC-CHG, OV-CHG-WEDGE (section 4) | KiCad, interface or REAR-part edits |

### 3.1 Round-4 to round-6 application (binding lead application)

| Answer | Binding R2A consequence | Where |
|---|---|---|
| Q-R2A-FPC-SPARE | Spare positions = 0 (confirmed). Exactly 2 of the 10 GND positions become VBUS (`CHG_RAW_5V`); 8 GND remain; nets 13 -> 14; 24 positions, connectors and J1502 unchanged; adjacency rules (rule 7.2(b) later dropped by Q-R2A-VBUS-ADJ, round 5) and the >= 3 GND proof; final map reported; interface file never written. The earlier append option is removed. | 7.2, 7.3, R2-V30, R2-V31 |
| Q-R2A-BLOCK | The 4 x 5 mm block rule and the four-contact order GND / +5V / +5V / GND are replaced by two discrete round contacts, planning pad Ø2.0 mm; pitch and position are search variables; gate SR-CHG-MECH. | 6.1, 6.2, R2-V28, R2-V29 |
| Q-R2A-MAG | Azimuth searched 0-355 (72 reported bins); non-ferrous contacts allowed inside MAG_CLEAR (no exclusion); distance to BMM350 reported; the non-ferrous class is a supplier-gated declaration. | 6.1, 6.2 pair 11 |
| Q-R2A-ESD | Exactly one REAR TVS (0201 / 0402 class) in the charger pad region; the only component exception; the G3 proof allows exactly it. | 6.1, 9 |
| Q-R2A-K1A | Pads, TVS and the VBUS net-map change are fixed inputs to the future K1-A contract (handoff only). | 7.2, 9.2, 11 |
| Q-R2A-VBUS-ADJ | VBUS positions are the owner-decided pair **19 and 20**; rule 7.2(b) is **dropped**; rules (a), (c), (d) are proved and the final map reported; the relaxation ladder is retired | 6.5, 7.2, 7.3, R2-V30, 13.1 |
| Q-R2A-BLE-DEPTH | For the new charger items only (two pads, two spring contacts, one TVS, their lands), the BLE and Wi-Fi reserved sectors apply at **all Z levels**: no charger item may lie inside the plan footprint of `BLE_RAD` or `WIFI_RAD` or their owner clock sectors; all other items keep the frozen reserved Z levels; the excluded sector is reported | 6.2 pair 7, 13.1, 13.2 |
| Q-R2A-VERDICT-TIMING | Confirmed: per-battery verdicts only; the package verdict is withheld until the owner's battery-selection record (section 12) | 10, 12, 13.2 |

## 4. Overlay additions and retired items

New records of the R2 4.2 form (`{id, pinned_source, authority, r2_value, scope: "G4-R2A only"}`; pinned value read at run time
**from the R2 record at `5d6d493` via `git show 5d6d493:<path>`, hash-checked — never from the updated working file** (same
mechanism as 1 item 3); deep copies; nothing written back). The required record set becomes the R2 set plus:

| id | pinned source | authority | R2A value |
|---|---|---|---|
| OV-PCM-ENV | `git show 5d6d493:inputs/g4_r2_closure.json /lobe` | OD-BATT-PCM | lobe of section 3 row 1 |
| OV-PCM-AZ | `git show 5d6d493:inputs/g4_r2_closure.json /grids/pcm_az_range_deg`, `/pcm_admissibility` | OD-BATT-PCM | `az_pcm` 0-355 step 5 as a joint-point variable |
| OV-BATT-ALT | `git show 5d6d493:inputs/g4_r2_closure.json /catalogue` (LPR403736 row) | OD-BATTERY-ALT | LPR443633 row (Ø36.0, 4.4, 540 mAh, 3.7 V, 1C) |
| OV-SUPPORT-RING | R2 relieved-ledger variant (`git show 5d6d493:generated/g4_r2_closure.json`, ledger) | Q-R2-SUPPORT-RING | relieved variant binding |
| OV-CHG-LANE | R2 sections 6.5 (J202, local drop), 6.6, 7.3, V10 / V12 / V22; OV-CONN-J202; OV-C-R1-01-2V; the R1 V19 / V20 4 x 5 block | OD-CHG-REAR, Q-R2A-BLOCK, Q-R2A-ESD | section 6 (two round contacts, one TVS) |
| OV-CHG-WEDGE | `g4_case_sealing.json` CHG_CONTACT wedge r 17.5-24.0, azimuth 80-100 and R1 V19 `r_centre` | OD-CHG-REAR, Q-R2A-MAG | radial window and azimuth wedge replaced by the feedthrough region of section 6.1 (azimuth 0-355) |
| OV-FPC-CHG | `design/interfaces/main_rear_interface.json /positions` (24 / 13) | OD-CHG-REAR, Q-R2A-FPC-SPARE | two GND positions -> `CHG_RAW_5V`, 24 positions kept, 14 nets (section 7) |

**Retired:** J202 (MAIN B.Cu east allocation `J202-EAST-B.Cu`, R2-V10, XC-J202); the local charger drop (R2-V12, "drop
service length", drop band); the cup-wall charger land and R2-S06 **as written** (charger `r_lim(cup)` against the
24.031 mm radial prerequisite); C-R1-01 items 1-4 and C-R2-01 (replaced as a whole by `C-R2A-01`, section 6.2);
`CHG_CONTACT` radial window 17.5-24.0, the 80-100 deg wedge and the 78-102 deg / 0.75 mm overshoot caps (wedge
diagnostics only); the 4 x 5 mm contact-block rule and the four-contact order GND / +5V / +5V / GND; every 3 o'clock
charger block / land / lane; the J202 exclusions of R2 6.5 (they are replaced by section 6.2 pairs); the
"charger-positive outside the sensor FPC" half of R2-H26; the J202 and drop occupants of the R2-H22 ledger and the
J202 / drop terms of R2-H25. CHG_ROUTE, CHG_LINK, CHG_RISER, CHG_APPROACH stay retired (OV-COND-BAND); with the drop
gone there is **no remaining REAR-level conductor band**: the band state in P-1 reads `retired (no drop footprint)`.

## 5. Variables, checks and stops

**Variables (R2 section 8):**

| ID | Change |
|---|---|
| R2-V01 | battery: LPR433736, LPR443633 (both reported, none preferred) |
| R2-V07 | **replaced**: `az_pcm` 0-355 step 5 (72 values) x authored OD-BATT-PCM lobe; admissibility reported in full (8.1). Evidence OWNER_PLANNING_ENVELOPE; gate SR-BATT-PCM |
| R2-V09 | J201 pose / mate near the chosen PCM exit, otherwise unchanged |
| R2-V10, R2-V12 | **retired** |
| R2-V22 | **replaced** by R2-V28 / V29 |
| R2-V28 | pad-pair pose: two pad centres on a 0.25 mm Cartesian grid inside `Omega_ft` (6.1), no azimuth restriction (midpoint azimuth 0-355 reported in 72 bins), pitch 2.5-12.0 step 0.25, pad Ø2.0 (PROVISIONAL, SR-CHG-MECH) |
| R2-V29 | feedthrough topology FT-C2: two round bonded sealed bodies, hole `d_h` 0.8-2.0 step 0.1 (<= pad Ø); land width 0.5-1.0 step 0.1, adverse 1.0. All PROVISIONAL, gate SR-CHG-MECH. FT-A is a reference column. |
| R2-V30 | VBUS position pair: the owner-decided pair (19, 20) (Q-R2A-VBUS-ADJ, round 5); the 45 pairs of the ten GND positions under rules 7.2 (a), (c), (d) are report-only |
| R2-V31 | `N_VBUS` = 2 (decided, fixed) |
| R2-V32 | charger TVS: class {0201, 0402}, face {skin, inner}, pose inside `PR` (6.1) |

**Checks.** Each reports per battery with the R2 column.

| ID | Revision |
|---|---|
| R2-H14 | **replaced**: charger lane L-CHG-R, `C-R2A-01` (6.2), physical headline (6.5) |
| R2-H15 | extended: the charger column is checked against reserved regions (it is outside them by geometry, reported); MAG_CLEAR per 6.2 pair 11 |
| R2-H16 | extended by item 8 (section 9): REAR additions = two pads, two spring contacts and exactly one TVS, with the proof of 9.2 |
| R2-H18 | re-evaluated at `Z_support_start` (Q-R2-SUPPORT-RING) |
| R2-H22 | occupants: remove J202 and the drop; add the FT bodies, lands and contact columns, the TVS, the PCM chord lobe and the corridor of 3 row 1 |
| R2-H23 | contains pack + growth + chord lobe (3 row 1) at linear worst; Z per 8.3 |
| R2-H25 | J202 / drop terms removed; FPC terms per section 7 |
| R2-H26 | **replaced** by 7.3 |
| R2-H29 | PCM admissibility: the 72-azimuth report of 8.1 is complete and every row is derived from production predicates |
| R2-H30 | plate feedthrough structure: hole K_t, stiffness knock-down, ring continuity, `sigma_allow_req` with holes (6.3) |
| R2-H31 | FPC charger net change: reassignment rules 7.2 (a)-(d), final map, pin current (7) |
| R2-H32 | pack / carrier Z extents grown by the adverse terms (8.3) |

**Stops.** The R2 table stays, with these changes:

- **R2-S01** extended: the REAR addition manifest differs from the two-pad / two-spring-contact / one-TVS manifest of 9.2, or any
  pinned G3 object digest changes.
- **R2-S04** wording and evaluation per 8.4.
- **R2-S06** **redefined**: no pad-pair / feedthrough pose in R2-V28 / V29 / V32 (with the TVS) closes the complete `C-R2A-01`
  predicate set at the joint point (lane stop). The old `r_lim(cup)` deficit is not a stop condition any more.
- **R2-S08** unchanged in form; J202 is no longer an occupant, so it can name J1501, J201, the LRA and the cup only.
- **R2-S09** applies to the OD-BATT-PCM envelope as well (recorded document contradicts it).
- **R2-S14** re-scoped to the joint variable: no admissible `(offset, az_pcm)` pair of the 145 x 72 grid keeps pack + growth + chord lobe + carrier out of the reserved regions and clear of the case features. The stop quantities report the clean-pair count and the best margin.
- No stop is added. A closure that needs an unrecorded owner decision is OWNER_GATED with a named question (R2 11).

## 6. Charger lane L-CHG-R

### 6.1 Contact columns, feedthrough region and TVS region

Contacts are **two discrete round vertical columns** (Q-R2A-BLOCK, DECIDED; the 4 x 5 mm contact-block rule of C-R1-01 /
G4 8.8 does not apply): exterior contact, spring contact, bonded feedthrough body in the ceramic plate, REAR pad of
planning diameter **Ø2.0 mm** (PROVISIONAL, gate SR-CHG-MECH). Pitch (centre to centre) and position are search
variables (R2-V28). For each column, exterior contact plan = feedthrough plan = REAR pad plan. The contact polarity
(VBUS / GND) is a dock and K1 decision; the geometry is polarity-symmetric and the tool assigns no polarity. Work in
assembly coordinates; the REAR frame appears only in the handoff and uses the pinned transform
`x_rear = 100 - x_assembly`, `y_rear = y_assembly - 100`.

The conductive column (spring contact + pad) lies in

`Omega_ft = Disk((100, 100), r_S14 - c_edge)  minus  union(E1..E8)`

with `r_S14 = 16.400` (pinned S14 outline circle, read from `g3_rear_optical.json.g4_handoff`) and `c_edge` = 0.500 mm
(the pinned S14 tail-exit `edge_margin_mm`; reported, not tuned). Each pad disc (Ø2.0) lies fully inside `Omega_ft`.
**There is no azimuth restriction**: the pair is searched over 0-355 deg (Q-R2A-MAG, DECIDED), which supersedes the
80-100 deg wedge and the "about 3 o'clock" reading of OD-J202. The result reports the pair-midpoint azimuth and an
admissibility record for each of the 72 five-degree bins (best margin and binding constraint per bin). Each exclusion
is a pinned object grown by the **strict** clearance of 6.2 (no extra margin invented):

| E | Object (pinned, G3-B-S14) |
|---|---|
| E1 | pod polygon grown by `seal_land_mm.max` (0.8 pinned); the W1 bond land and pod frame lie inside it |
| E2 | apertures, optical cells and barriers of the candidate |
| E3 | the courtyards of all 44 REAR parts, C1501 (DNP) and J1502 |
| E4 | the guarded-analog keep-out: the stored PD_IN corridor / PD_GND guard polygons if the pinned data carries them; otherwise the convex hull of each AFE (U12, U13) with its photodiodes (D413 / D414 / D423 / D424) and NT401 / NT402, grown by `rf_clearance_report_mm` (1.0 pinned). The tool states which form it used. |
| E5 | U6 island and F1 / F2 / F3 contact features |
| E6 | the three support lands (az 30 / 150 / 270) |
| E7 | the J1502 tail-exit corridor and tail reservation |
| E8 | caseback screws, case-side supports and the pod seal land |

Pose parameterization (exact reduction, documented): admissible single-pad centres on a 0.25 mm Cartesian grid inside
`Omega_ft` eroded by the pad radius; a pose is a pair of such centres with pitch `p` on the R2-V28 grid. The
(az, r, orientation) product is not enumerated; az and r are derived from the pair midpoint. Two equivalent forms are
allowed and the tool states which it uses: (i) pairs of grid centres whose centre-to-centre distance lies on the
R2-V28 pitch grid (only axial and Pythagorean pair vectors hit the grid exactly; the achieved pair directions are
reported), or (ii) midpoint on the 0.25 mm grid x pitch on the R2-V28 grid x pair direction 0-180 deg step 5, with the
two pad centres derived from the pose (the centres then need not lie on the Cartesian grid).

The non-conductive bond / seal land around each feedthrough (0.5-1.0 mm, adverse 1.0, caseback side, no REAR-level Z
intrusion) may overhang the S14 outline radially because the plate extends there, but it must clear E1 and E5-E8 and
the cup features strictly. The cup ring at `r_ring` is never touched (6.3).

**Charger TVS (Q-R2A-ESD, DECIDED).** REAR gains **exactly one** TVS diode, 0201 or 0402 class, in the charger pad
region `PR` = convex hull of the two pad discs grown by `r_tvs` = 2.0 mm (PROVISIONAL "next to the pads"; the
zero-margin value is reported). Its courtyard is taken from the pinned REAR placements if an 0201- or 0402-class part
is identified there (the tool states the source); otherwise authored PROVISIONAL class values, SUPPLIER_DATA_REQUIRED:
0402 courtyard 1.6 x 1.1 mm, height <= 0.60 mm; 0201 courtyard 1.0 x 0.7 mm, height <= 0.35 mm. Face (skin or inner) and
class are variables (R2-V32); the TVS must lie in `PR`, clear E1-E8 strictly (E3 excludes its own footprint), and fit
its Z: on the skin face the available gap is `Z_pad_face - t_loc` at each G3 corner; on the inner face it must clear the
lower-web underside. No TVS rating is claimed.

### 6.2 Predicate set `C-R2A-01` (replaces C-R1-01 and C-R2-01)

All gaps are 3-D strict gaps (R1:R3-3: separated only when > EPS), at linear worst, with positional tolerances grown.

1. Both pad discs inside `Omega_ft`; pitch `p` >= 2.5 mm (pad Ø2.0 + 0.5 edge-to-edge, PROVISIONAL). If no pose closes,
   the tool reports numeric thresholds, never credits: the largest pad diameter that closes at the best pose, the
   `Omega_ft` area and largest inscribed disc, and the admissibility per azimuth bin (6.1).
2. Land width 0.5-1.0 (adverse 1.0) clears pairs 5-9 below.
3. Strict 3-D clearance of each conductive column (including spring working length and travel) to: every REAR part,
   the guarded-analog keep-out E4, the U6 island, the pod and its seal land, the support lands, the J1502 tail
   corridor, and the REAR copper of PD_IN / PD_GND (no shared plane or guard region).
4. Contact spring free length: required length = `Z_pad_face - t_loc + travel`, with `Z_pad_face` the REAR skin-face Z
   at each G3 corner and `t_loc` the local plate thickness (`t_in`); reported as the SR-CHG-MECH working-length threshold.
   `travel` is an authored dock-contact travel allowance: 0.5 mm (PROVISIONAL, gate SR-CHG-MECH; the zero-margin value is
   reported), in the same class as the pad Ø and `r_tvs` planning values of 13.2 item 13.
5. Bond land to screws, supports and the cup spigot / wall.
6. Land and body to the switch bores and bosses, the vent and lug features (2(vi) neighbours).
7. Land to every radiator volume >= `rf_clearance_report_mm` (1.0), evaluated as a 3-D strict gap per the 6.2 preamble
   (plan **or** Z); the plan gap is reported beside. The columns and lands lie at r <= 16.4 + land <= 17.4 mm. Pinned
   radiator radial spans: GNSS 20.13-24.37 mm, BLE 15.8-25.15 mm (plan corners az 303.7-332.2 deg, nearest point
   r 15.62 mm at az 320.2 deg), WIFI 20.59-25.24 mm. BLE reaches inside the pad band in plan and is excluded in 3-D by
   Z (its reserved Z level is MAIN only; the columns, lands and TVS are REAR / caseback). The tool proves the 3-D
   separation and the gap from each radiator **volume**, never assumes a radial start. **Q-R2A-BLE-DEPTH, round 6
   (DECIDED), supersedes the Z exclusion for the new charger items only:** the two pads, the two spring contacts, the
   one TVS and their lands may lie in no plan footprint of `BLE_RAD` or `WIFI_RAD` and in neither owner clock sector
   (BLE 300-330 deg, Wi-Fi 105-135 deg) at **any** Z level; GNSS keeps the frozen reserved Z levels (its radial span
   starts at 20.13 mm, outside the pad band). The excluded pad-sector azimuths are reported.
8. The plate region has `t_in` <= 1.10 (G3 pod residual); no REAR-level Z intrusion.
9. No ferromagnetic material in MAG_CLEAR: see pair 11 (G4-H18 stays exact for everything except the declared
   non-ferrous charger parts).
10. Seal: FT-C (bonded sealed body in the ceramic plate) is binding; FT-A reference; FT-B not applicable (ceramic).
    Each feedthrough has exactly one primary seal; the seal path stays closed (R2 7.2.3).
11. **MAG_CLEAR (Q-R2A-MAG, DECIDED).** Contacts must be **non-ferrous** (no magnet or ferrous part on the watch side).
    On that condition they are **allowed inside MAG_CLEAR**. The tool therefore applies no MAG_CLEAR exclusion to the
    columns, the lands or the TVS, and reports: overlap area (the pinned S14 outline already overlaps MAG_CLEAR by
    150.586 mm2), the plan and 3-D distance of each contact, each pad and the TVS to the BMM350 (U703), and the
    pose-wise maximum. The non-ferrous condition is a declared material class (input `chg_contact_material_class`,
    `non_ferrous_required`), closes only as SUPPLIER_GATED (SR-CHG-MECH; TVS termination plating included as
    SUPPLIER_DATA_REQUIRED) and is never credited as PASS. A ferrous class in MAG_CLEAR fails G4-H18. The charge-current
    field effect on the BMM350 is MEASUREMENT_GATED (X16, MG-MAG).
12. Plate structure per 6.3.
13. TVS per 6.1: inside `PR`, strict clearance to E1-E8 and to both pads, Z fit.

### 6.3 Plate stress with feedthrough holes (R2-H30)

- Ring continuity: all holes are at `r <= 16.4 + land < r_ring`. The ring remains continuous over 360 deg and keeps
  its LA-STR-5 credit; the tool asserts this per pose.
- Hole `K_t` = 2.0 (the R2 7.1.1 PROVISIONAL value for "holes"), applied to the **maximum local nominal plate stress
  over `[rho_h - a, rho_h + a]`** from the same ring-plate compatibility solution (nominal means without the
  pod-frame junction `K_t`), with `rho_h = max(r_h, r_in_eq)` (`r_in_eq` = the equivalent inner radius of the R2 plate
  model; `r_h` = the larger of the two hole-centre radii from the plate axis, or the merged-pair centre radius). Here
  `a` is the half-width of the sampling window: `a = d_h/2` for two separate round holes, `a = (p + d_h)/2` for the
  merged elongated hole.
- Two round holes of diameter `d_h` (0.8-2.0, `d_h` <= pad Ø) at pitch `p`: if the ligament `p - d_h` is < 2 `d_h`, the pair
  is treated as one elongated hole with the Inglis closed form `K_t = 1 + 2 a/b` on the circumscribed ellipse
  (`a = (p + d_h)/2`, `b = d_h/2`), evaluated for both principal stress directions, floored at 2.0, taking the larger;
  otherwise each is a round hole. A hole whose ligament to the pod-frame junction is < 2 `d_h` compounds with the
  junction `K_t` (product). These are LEAD / MODEL CONSERVATISM rules.
- Reported only, never credited: the Kirsch bound `3 sigma_1 - sigma_2` at the hole.
- Deflection (R2-H09a) is recomputed with the net-section flexural-stiffness knock-down `D_plate,eff = D_plate (1 - phi)` (`D_plate` = plate flexural rigidity, **not** `D_case_body`), applied to the plate region containing the holes (the outer `t_out` region of the R2 plate model), with `phi = 2 d_h / (2 pi r_h) = d_h / (pi r_h)` (`d_h` removed per hole) and `r_h = min(r_h1, r_h2)`, the smaller of the two hole-centre radii from the plate axis.
- `sigma_allow_req` = max(junction value, hole value), each with screen, location and governing terms. Stress > 150 MPa
  with R2-H09a and R2-H08 passing stays SUPPLIER_GATED (SR-CASEBACK-CERAMIC), never a model FAIL.

### 6.4 Sealing requirement as supplier gate (SR-CHG-MECH)

No qualification claim. Report as numeric thresholds: leak-tight at `p_test` 0.625 MPa (planning), body-to-plate bond
gap and land width (zero-margin values), body wall, spring working length and travel (6.2 pair 4), per-contact
`K_t` hole size, and the maximum `d_h` for which R2-H09a still passes.

### 6.5 Presentation and disposition

Headline (P-2): the smallest strict 3-D clearance and its governing pair; `Omega_ft` area and the largest inscribed
disc; the pad pair (pitch, midpoint azimuth, positions); `c_edge` margin; BMM350 distance; deflection headroom. Tags
are secondary. Disposition: `BLOCKED` (R2-S06) if no pose closes; otherwise SUPPLIER_GATED (SR-CHG-MECH, SR-FPC-MECH,
non-ferrous material). J202 and the drop are not evaluated.

## 7. FPC net change and the frozen 24-position interface

### 7.1 Pinned facts (read from `design/interfaces/main_rear_interface.json`, hash-checked)

All 24 positions are assigned: 10 signal, 1 logic supply (VOUT1_1V8), 3 PPG_VLED, 10 GND (positions 1, 3, 5, 7, 10, 14,
17, 19, 20, 24; 20 and 24 are the "power return group"). **Spare positions in the pinned map = 0**, which the owner
confirmed in round 4 (Q-R2A-FPC-SPARE correction). The interface has 13 logical nets including GND. The SPI clock is
position 2 (`PPG_SPI_SCLK`). `charger_harness.{md,json}` still says "no charging power uses J1501 / J1502", lists `J202`
and four contacts C1..C4; all are superseded for R2A by OD-CHG-REAR and the round-4 answers and are recorded as known
documentation debt (not edited).

### 7.2 Decided reassignment (Q-R2A-FPC-SPARE, DECIDED; pair fixed by Q-R2A-VBUS-ADJ, round 5) and its rules

Two of the ten GND positions become `CHG_RAW_5V` (VBUS): **positions 19 and 20** (Q-R2A-VBUS-ADJ, round 5). 8 GND
remain; nets 13 -> 14 (the charger return joins the existing GND net). Connector parts, the 24-position count and J1502
are unchanged; only the net map changes. The tool applies, in the **final** map (adjacency is logical `n +/- 1`,
mirror-invariant; positions 1 and 24 are not adjacent):

- (a) **never adjacent to an SPI clock position**: neither VBUS position is 1, 2 or 3 — proved for 19 and 20;
- (b) [**DROPPED** by Q-R2A-VBUS-ADJ, round 5] "adjacent to GND positions" is not a rule any more;
- (c) **>= 3 GND positions remain for VLED return**: the tool proves `count(GND) >= 3` (8 remain: 1, 3, 5, 7, 10, 14,
  17, 24) and reports which of the power-return-group positions 20 / 24 remain (24 remains GND; 20 becomes
  `CHG_RAW_5V`);
- (d) `N_VBUS` = 2 exactly (R2-V31); no position other than 19 and 20 changes net.

Report: the **final map** (24 rows: position, old net, new net, neighbours), the (a)/(c)/(d) proofs, and — report-only —
the table of all 45 pairs under rules (a), (c), (d). For the pair: `I_pin_req = I_in / 2` at the pinned initial charge
setting `I_in = 0.400 A` (`charger_harness.md`) = 0.200 A, the return share `I_in / count(GND)` = 0.050 A over 8, and
the supplier requirement `I_pin_rating_req` (SR-FPC-MECH, no rating invented).

**Lead arithmetic (the tool reproduces it):** under the dropped rule (b) read in the final map the admissible set was
**empty** (only positions 19 and 20 had a GND neighbour, each other; every other GND position — 5, 7, 10, 14, 17, 24 —
has only signal, supply or VLED neighbours, and 1 / 3 are excluded by (a)). Round 5 drops (b) and fixes the pair at
19 and 20, which satisfies (a) (not 1, 2 or 3), (c) (8 GND remain) and (d). The relaxation ladder (R-final /
R-pinned / R-weak) is retired. Nothing is written to the interface file.

K1 / K1-A requirements recorded (decided as inputs by Q-R2A-K1A, not R2A work): the charger pads, the TVS and the VBUS
net-map change are fixed inputs to the future K1-A contract; the charger GND pad returns to the J1502 GND positions by a
REAR-local route that avoids NT401 / NT402 and the PD_GND guard copper; `CHG_RAW_5V` enters MAIN through J1501, so MAIN
12_CHARGING loses J202; the MAIN U1201 / D1201 entry protection is unchanged by R2A; the mirrored physical position order
stays a K1 requirement.

### 7.3 Replacement of R2-H26

R2-H26 now means: the pinned logical map of positions 1-24 is unchanged **except** the two VBUS positions of 7.2
(positions 19 and 20), listed
explicitly with their old and new net; the J1501 and J1502 connector counts are 24; no other net changes; the logical
identity map `J1501 n -> J1502 n` holds for every n; the `local_only` nets (PD_IN, PD_GND, VREF, LED cathodes, mux
selects) still do not cross; the net count is 14; rules 7.2 (a), (c), (d) hold. The tool **never writes** the interface
file (R2-S10 if the file differs). The result is a proposal for a later interface revision under its own contract.

## 8. The four MiMo minor fixes

Checked against the MiMo review text (received with the round-4 answers). Each fix below also lists the review's own
evidence as a regression case; the review's verdict is RESULT VALID WITH MINOR and no stop or margin inside the pinned
grids changes because of them.

### 8.1 Full 0-355 PCM admissibility report (R2-H29)

For every battery, offset (R2-V05 grid, 145 values) and `az_pcm` (72 values) emit one admissibility record from the
production predicates: pack + growth + chord lobe inside the carrier; carrier wall >= 0.30 adverse; no hit of a
reserved region, radiator volume or MAG_CLEAR; clear of the switch bores / bosses, supports and corridors; lobe Z
inside the allocation (8.3); the translated BATT_TAIL corridor (3 row 1) clear. Each record holds `admissible`,
the binding constraint id and its margin (mm). Encode compactly (one 72-character string per battery and offset plus a
constraint-code table; `g4_r2_sweep.jsonl` only if >2 MB). The report states per azimuth the number of admissible
offsets and the best offset, and flags the azimuths at which the R2 azimuths 220 / 230 / 240 sit. Joint-point ranking
(R2 8) is unchanged; `az_pcm` is chosen only by it. The tool reads `grids.pcm_admissibility` (0-355 step 5; the R2 tool
never read it, a test proves it is read now) and the R2 "all of 220 / 230 / 240" window semantics are replaced by one
`az_pcm` per joint point. Regression case (review): with the superseded authored lobe (3.0 x 8.0) the in-memory sweep
had 124 clean (offset, azimuth) pairs, none inside 220-240.

### 8.2 Binding constraint and margin per unplaced connector

For every connector that is not placed (J1501 expected, others if any), report: the funnel counts (as R2), the
**best pose** (the one maximizing the minimum constraint margin) with every constraint margin at that pose, and the
**binding constraint** (smallest margin at the best pose) as `{constraint, margin_mm, occupant}`, plus the best-case
margin of each constraint class when all others are relaxed (zone A, room, MAIN column, reserved region, named
occupant clearance, Z fit, mate stroke). MAIN-outline column containment (R2-V24) is its own constraint class with its
overrun in mm, and the first violated pairs are listed with `gap` against `required`. The best-pose report re-evaluates
exhaustively (no first-violation early exit) so that pair records exist; the B-22 early exit stays valid for pass / fail.
The stop reason names the stage ("no pose inside the MAIN-outline column" versus "no strict-clearance pose"). The
report states only what the JSON carries: the full per-offset table is emitted (all offsets, not 145 plus 5 exact
attempts). A connector without a stated binding constraint and margin fails R2-H25. Regression case (review, R2 state):
J1501 best pose az 214, r 21.50, column overrun 0.309 mm; with the column waived the binding pairs are body versus
CARRIER_ENVELOPE / SUP_SW_CASE_SIDE / SUP_SW_PAD, 0.000 against 0.150 required.

### 8.3 Pack / carrier Z grown by adverse terms (R2-H32)

All ledger and R2-H22 occupants use `Z_pack_top_lw = Z_bz_bottom + t_cell + tol_pack_thick(adverse) + g_axial(adverse)`
and `Z_carrier_wall_top >= Z_pack_top_lw`, instead of the nominal-based extent. Lead arithmetic: this is **+0.40 mm**
over the nominal-based extent for both cells (`(0.3 + 0.5) - (0.1 + 0.3)`); the tool recomputes it, and the margin to the
battery-zone top stays `c_axial` (0.2 adverse). Regression case (review): the R2 pack solid top was battery-zone top
minus nominal `c_axial` (8.25) against the linear-worst `3.55 + 4.3 + 0.3 + 0.5 = 8.65`; zone-A B.Cu parts near the nominal
zone top would have been cleared falsely. The same growth applies to the pack and to the carrier-envelope capsule. The chord lobe Z top is `Z_pack_bottom + t_cell + 0.3` (no extra
growth; the owner envelope is a finished-pack maximum). A ledger that uses the nominal extent is a fault.

### 8.4 S04 Z-neutral qualifier

R2-S04 reads: "no LRA pose on MAIN B.Cu (zone B) **and** no F.Cu fallback pose that is plan-feasible **and** Z-neutral
(seated height including `lra_mount_mm` adverse <= 2.70 mm at linear worst)". The tool evaluates the two F.Cu
predicates separately per class and reports for each: plan-feasible pose count, Z-neutral yes / no with the height
margin (`2.70 - height`), their intersection, and which predicate is binding. A class defined by its threshold
stays SUPPLIER_GATED (C-R1-08) and never PASSes. The stop text names the failing predicate(s). The R2 code fired on the plan predicate alone; it must evaluate
plan AND Z-neutral jointly. Two LRA need figures appear in one output and are labelled: the necessary screen need (5.3 mm,
smallest class, straight strip) and the adverse need with chord sagitta (6.252 mm, LRA-LIN-RECT); both exceed the best
annulus, so neither changes the proof.

## 9. G3 reopening: pads and one TVS only

### 9.1 What is allowed

Only two charger contact pads with their two spring contacts and **exactly one TVS diode** (0201 / 0402 class) in the
charger pad region (Q-R2A-ESD, DECIDED). The TVS is the only component exception to "pads only": no other REAR
component, no net-tie, no outline change. Nothing else in G3-B-S14 may differ: placements, faces, rotations, the REAR
transform, outline, pod, apertures, U6 island, J1502 and the tail exit, support lands, window variants, seal land,
barriers, thermode, tail-corridor reservations, the Z relations of R2 4.3 item 2. The G3 conservative-corner gates stay
G3 gates. REAR routing of the pads and the TVS is K1-A work, not an R2A object.

### 9.2 Proof that nothing else in G3 moved (extends R2-H16)

1. **Digest.** Canonical-JSON SHA-256 (sorted keys, compact separators, 9-decimal rounding) of the G3-B-S14 object set
   (the `g4_handoff` candidate plus its `placements`) is computed **before** and **after** the overlay and must equal the
   pinned digest recorded in the inputs. The additions live in a separate container, never inside a G3 dictionary.
2. **Addition manifest.** The REAR additions are exactly: two pads (plan polygons, Z intervals, nets
   `CHG_RAW_5V` / GND assigned later by the dock), two spring contacts, and one TVS (class, face, courtyard, height).
   Any further object, a second TVS, any non-listed component, or a pad or TVS outside its region raises R2-S01.
3. **Disjointness.** For every pinned REAR object and the three support lands, the tool emits the minimum strict 3-D
   gap to every pad, spring contact and the TVS (all objects listed, not only the minimum), each >= the named clearance
   of 6.2.
4. **Relative Z.** `h_pod`, `pod_depth` 1.35 / 1.85 / 1.05, the caseback residual before wall and the REAR face / board /
   window / optics Z are unchanged relative to the pod-plane datum; Delta stays frontward of the REAR inner face.
5. **No live KiCad.** R2A reads no KiCad file. The pads, the TVS and the VBUS net-map change are a one-way handoff to
   K1-A (REAR layout / routing with part positions frozen; Q-R2A-K1A, DECIDED); R2 4.5 isolation rules stay. Any K1-A
   state that disagrees invalidates the R2A result for that state.

## 10. Validation and self-test additions

**Commands.** R2 section 15 stands, with: HEAD = R2A contract commit (parent `5d6d493`); entry tree clean (E-1);
`git diff --exit-code 5d6d493 -- . ':(exclude)design/mechanical/G4_R2A_AMENDMENT.md' ':(exclude)design/mechanical/tools/g4_r2_closure.py' ':(exclude)design/mechanical/inputs/g4_r2_closure.json' ':(exclude)design/mechanical/generated/g4_r2_closure.json' ':(exclude)design/mechanical/generated/g4_r2_closure.md' ':(exclude)design/mechanical/generated/g4_r2_plan.svg' ':(exclude)design/mechanical/generated/g4_r2_sections.svg' ':(exclude)design/mechanical/generated/g4_r2_annulus.svg'`;
the validator constants `BRIEF_CELL` / `BRIEF_DELTA` **in `tools/g4_r2_closure.py`** are updated in place (1.2) to `BRIEF_CELL = {'LPR433736': (37.0, 4.3), 'LPR443633': (36.0, 4.4)}` and `BRIEF_DELTA = {'LPR433736': 0.2, 'LPR443633': 0.1}` (LPR403736 removed) — they are tool constants, not inputs;
the detached R2 baseline of 1 item 4; `PYTHONHASHSEED=0` and `4242` `check`; two consecutive `build` runs give identical SHA-256.
**Overlay-off regression (R2-H03):** with every R2A overlay record switched off, the tool reproduces the pinned R2 JSON
(canonical compare) on every key except the keys R2A adds (listed in the report). Budgets: the PCM variable grows from 3
to 72 values and a different second battery is run, so the evaluation budget rises to 6,000,000 and `check` to
240 s; exact reductions per R2 section 8 only, never coarser grids; overruns are reported, not hidden.

**Expected vocabulary unchanged:** the four R2 verdict tokens of section 12. Rule change only: verdicts are per battery
(LPR433736, LPR443633); no package verdict until the owner records the battery selection; G5 eligibility attaches to the
selected battery after independent review PASS, the manual commit gate and that record.

**Minimum injected faults added (each must be caught; classes as R2 14.8):**

- PCM and batteries: lobe with the superseded 3.0 / 8.0 values; `az_pcm` restricted to 220-240; an `az_pcm` of 360 or step 7;
  chord width 15.01; radial protrusion 1.51; lobe Z top at cell + 0.31; LPR403736 evaluated or selected; any battery
  selected by tool logic; LPR443633 Delta 0.2 or Delta with a tolerance; nominal-based pack Z (-0.40) in the ledger;
  supports at the as-pinned Z used as binding.
- Charger: J202 or the drop still an occupant; old R2-S06 radial deficit used as a stop; the 4 x 5 block rule or the
  four-contact order applied; azimuth restricted to the east; pad centre outside `Omega_ft` (r 16.401); `c_edge`
  ignored; pad pitch below 2.5; pad in E1-E8 (one fault each); zero-gap touching counted as clear; ring interrupted but
  credited; hole `K_t` omitted or 1.0; deflection without the knock-down; hole ligament < 2 `d_h` treated as separate
  holes; Kirsch value credited; MAG_CLEAR exclusion still applied to the contacts; BMM350 distance missing; a ferrous
  contact class accepted in MAG_CLEAR; non-ferrous condition credited as PASS; a second TVS, a TVS outside `PR`, a
  non-TVS component, or a TVS that does not fit its Z; mirrored REAR transform on the pad handoff.
- FPC: spare count assumed > 0; interface file written; position count or J1502 changed; a position appended;
  `N_VBUS` other than 2; VBUS at position 1, 2 or 3; fewer than 3 GND positions remaining; net count left 13 or made
  15; VBUS pair other than (19, 20); rule 7.2(b) still applied; final map or the >= 3 GND proof missing;
  power-return-group report missing; return path through PD_GND or NT401 /
  NT402.
- G3 and governance: a REAR addition outside the manifest of 9.2; a pad inside the S14 object set; digest drift of
  `placements`; REAR XY +0.001; the R2 fallback trigger still active; commit-state text in status.
- MiMo fixes: PCM report with fewer than 72 azimuths or without a binding constraint; unplaced connector without binding
  constraint and margin; S04 text without the Z-neutral qualifier or without separate predicates; pack top at the
  nominal-based 8.25 instead of 8.65; `grids.pcm_admissibility` unread.

Self-test counts are recorded as R2 requires.

## 11. Handoff additions (`handoff_to_g5_and_outline`)

Per battery: the battery order spec (cell, `az_pcm`, lobe envelope with evidence class, Z, exit, J201-compatible
three-wire exit); the charger pair (pad centres, pitch, midpoint azimuth, land, hole `d_h`, topology, spring working length, pad polygons
in the REAR frame), the TVS (class, face, pose) and the VBUS final net map (7.2, positions 19 and 20, with the (a)/(c)/(d) proofs) as fixed
K1-A inputs; `I_pin_req`; the BMM350 distance of each contact; the
`sigma_allow_req` with holes; the MAG_CLEAR overlap record; the 72-azimuth admissibility; the binding constraint per
unplaced connector; the supports' `Z_support_start`; the retired list of section 4; open questions of section 13.

## 12. Battery selection record

After the run the owner may record, in a later lead state record under its own contract, which battery (LPR433736 or
LPR443633) proceeds. The tool consumes no such record in R2A and contains no code path that chooses. `fallback_trigger`
is removed from the inputs (its presence is a fault).

## 13. Interpretations, open questions and what could not be contracted

### 13.1 Questions

**DECIDED, round 4 (section 2; applied in sections 3.1, 6, 7, 9, 11):** Q-R2A-FPC-SPARE (correction: reassign 2 of 10
GND positions), Q-R2A-BLOCK (two Ø2.0 round contacts), Q-R2A-MAG (azimuth 0-355; non-ferrous contacts allowed in
MAG_CLEAR; BMM350 distance reported), Q-R2A-ESD (exactly one REAR TVS), Q-R2A-K1A (confirmed; fixed inputs to K1-A).

**DECIDED, round 5 (section 2; applied in sections 3.1, 6.5, 7.2, 13.1):** Q-R2A-VBUS-ADJ (VBUS uses positions 19 and
20; the "adjacent to GND" requirement is dropped; the rule is only "never adjacent to the SPI clock position"; the tool
proves >= 3 GND positions remain for VLED return and reports the final map).

**DECIDED, round 6 (section 2; applied in sections 6.2 pair 7, 13.2):** Q-R2A-BLE-DEPTH (for the new charger items
only — two pads, two spring contacts, one TVS, their lands — the BLE and Wi-Fi reserved sectors apply at ALL Z levels;
no charger item may lie inside the plan footprint of BLE_RAD or WIFI_RAD or their owner clock sectors; all other items
keep the frozen reserved Z levels; the excluded sector is reported), Q-R2A-VERDICT-TIMING (confirmed: per-battery
verdicts are emitted; the package verdict is withheld until the owner's battery-selection record).

**Still open (named; does not block the run):** none (Q-R2A-VBUS-ADJ decided in round 5).

### 13.2 Interpretations (reviewable; none a new decision)

1. `OWNER_PLANNING_ENVELOPE` is a labelled sub-class of OWNER_DECISION for the one evidence class column of R2 10.1.
2. The lobe is a flat-faced chord of 15 mm whose outer face lies 1.5 mm beyond `R_pack(lw) + g_radial(adverse)`.
3. "Z within cell + 0.3 mm" is the finished-pack Z maximum `t_cell + 0.3` from the pack bottom, with no further
   tolerance or swelling.
4. The G2 BATT_TAIL corridor travels with `az_pcm` at fixed angular width.
5. "Case-side battery supports start above the cup wall top" fixes the relieved ledger as binding; their plan is not moved.
6. "Inside the main seal" means radius < the cup O-ring seal line; by construction the conductive columns are at r <= 16.4.
7. "Plate feedthroughs get the hole K_t" is `K_t` 2.0 for round holes and the Inglis form for a closely spaced hole pair (6.3).
8. The guarded-analog keep-out E4 uses the pinned `rf_clearance_report_mm` as its growth when no stored polygon exists.
9. "Nets 13 -> 14" is `CHG_RAW_5V` as the one new net, with the charger return on the existing GND net.
10. I-MAX, C-R1-03, T1 and all R2 button, seal, structure and LRA rules are unchanged.
11. "Adjacent" means logical position `n +/- 1` in the final map; mirroring does not change adjacency.
12. "Next to the charger pads, inside the charger pad region" is `PR` of 6.1. "Contacts must be non-ferrous" is a
    declared material class, not a measured property.
13. The pad Ø2.0 is given; the hole diameter `d_h`, the 0.5 mm edge-to-edge spacing and `r_tvs` are PROVISIONAL planning
    values whose zero-margin values are reported (SR-CHG-MECH).
14. "Contact azimuth is searched 0-355" is the pair-midpoint azimuth, reported per 5-degree bin; the earlier "about
    3 o'clock" preference of OD-J202 no longer restricts the search.
15. `c_edge` = 0.500 mm reuses the pinned S14 tail-exit `edge_margin_mm` as the pad-to-outline margin (reported, not
    tuned).
16. Withholding a package verdict until the owner's battery-selection record (section 12) is the conservative reading of
    'the owner chooses after the run'; per-battery verdicts are still emitted. Confirmed by Q-R2A-VERDICT-TIMING
    (round 6).
17. Q-R2A-BLE-DEPTH (round 6) reads "plan footprint" as the pinned radiator geometry union its owner clock interval
    over that volume's radial span (the R2 6.9 / 17.2 item 15 boundary), evaluated at every Z for the new charger items
    only; all other items keep the frozen pinned Z levels. The excluded sector (azimuth span and area) is reported.

### 13.3 What could not be fully contracted

- The TVS courtyard, height and the region radius `r_tvs` are authored planning values unless the pinned REAR data
  identifies an 0201 / 0402-class part.
- The MiMo review text was received with the round-4 answers; section 8 is aligned with its minor fixes 1-4 and with
  the file and line evidence it cites. Where its arithmetic is used (pack top 8.65 against 8.25) it is the reviewer's
  in-memory result, to be reproduced by the tool, not an input.

## 14. Lead arithmetic (orientation only; not results)

- Deltas 0.200 (LPR433736) and 0.100 (LPR443633). `battery_zone` for LPR443633 = 4.90 / 5.40 / 4.65 (nominal / linear / thin).
  `R_pack` LPR443633 = 18.15 / 18.25. REAR-band-only spigot Z for LPR443633 = -1.150 + 0.100 + 0.65 = -0.40 (LPR433736 -0.30).
- PCM chord lobe on-axis outer face (LPR433736) = 18.75 + 1.0 + 1.5 = 21.25 mm; corner at the 7.5 mm half-chord =
  `sqrt(21.25^2 + 7.5^2)` = 22.54 mm (R2 lobe max corner 23.1 mm).
- Pad band: east pod edge x = 112.1 (r 12.1) to the S14 outline r 16.4 = 4.3 mm; less 0.8 seal land and 0.5 edge margin
  = 3.0 mm of radial room against a Ø2.0 pad (the 4 x 5 block no longer applies), so a pad pair can fit there; the
  azimuth is searched 0-355 and the east band is inside the MAG_CLEAR placeholder (allowed, distance reported).
- Deflection headroom of the R2 cup is 0.0491 against 0.050 mm (1.8 %). Two holes of `d_h` 0.8 / 1.0 / 2.0 at r about 14
  give `phi` about 1.8 / 2.3 / 4.5 %: the stiffness knock-down is expected to bind and to favour small `d_h`.
- Pin current: `I_in / 2` = 0.200 A per VBUS position at 0.400 A; return share 0.050 A per GND position over 8.
- Reviewer what-if (MiMo, in memory only, not evidence): with the owner-photo PCM envelope and the azimuth searched, R2-S14
  clears (best `az_pcm` about 320 deg for LPR433736, 55 deg for LPR443633); J1501 stays unplaced for LPR433736 (best
  column overrun 1.159 mm) and is placed at az 93, r 21.0 for LPR443633; R2-S04 persists (best annulus 5.1 / 5.6 mm
  against the 5.3 mm screen need, 0 of 570 exact LRA-LIN-RECT poses). The tool reproduces or explains these (P-3).
