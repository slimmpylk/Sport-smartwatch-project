# G4-R2 brief — PACKAGE-CLOSURE STUDY (battery / interconnect / LRA / caseback-cup re-allocation) (Rev-A)

Status: phase contract drafted 2026-10-17 from the owner decisions of 2026-10-17 (section 3.2), for owner approval and
the lead contract commit. G4-R2 ("R2") is provisional, reversible, deterministic mechanical study work. It authorizes
**no KiCad edit**, no MPN selection, no supplier claim, no supplier-request issuance, no RF-performance claim, no
5 ATM / structural / optical / adhesive qualification claim, no case CAD and no later phase (G5, K1, K1-A, Q1).
It does not reopen G1 or G3. It supersedes pinned G1 / G2 / G4 / R1 allocations **only** through the explicit,
in-memory overlay of section 4.2. It amends neither `G4_BRIEF.md` nor `G4_R1_BRIEF.md`; both stay immutable.
Destination: `design/mechanical/G4_R2_BRIEF.md`. Work branch: `mechanical/g4-r2-package-closure`.

Baselines (accepted evidence, read-only):

- G1 `168badbab6de1201bb3209902a53fe1e4b874cc9` (immutable);
- G2 `eea49e447895e574a3f48e0b9777f57880dcd632` — "G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES";
- G3 `afb19ac173ce67c7e9599313cc5a0942e026ade9` — "G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES", selected
  candidate **G3-B-S14**;
- G4 contract `935da5ca737ce4cd5b9a2e1245c7d48c8104a592`; **G4 blocked study
  `00e77cbe107a79ac05194f19b674f7ab8d5941c9`** ("G4 OWNER DECISION REQUIRED — BLOCKED / UNRELEASED STUDY");
- G4-R1 contract `2d1d28077e7743b06e1b1802c7ba9e8f4317fedf`; **G4-R1 recorded study
  `27f7a3a0570bb79c27df530cd5d99c7ea7597f9f`** (verdict "R1 OWNER DECISION REQUIRED"). Its generated files are the
  numeric starting point, are pinned by SHA-256 and are never re-typed.

Phase 1, G1, G2, G3, G4 and G4-R1 rules apply except where this brief explicitly changes scope.

**Naming.** Identifiers such as `R2-1`, `R3-3`, `R4-1` and `R5` inside `generated/g4_r1_blockers.*` are R1
correction-pass rule ids. This brief writes them as `R1:R2-1`, `R1:R3-3`, `R1:R4-1` and `R1:R5`. They are unrelated to
this phase's ids `R2-Hnn` (hard checks), `R2-Snn` (stops), `R2-Vnn` (variables), `OV-*` (overlay records) and `C-R2-nn`
(contract clarifications). Hard-check ids of earlier phases always carry their phase prefix: `G4-Hnn` or `G4 Hnn`
(`G4_BRIEF.md`, e.g. G4-H17 radiator volumes, G4-H18 MAG_CLEAR) and `R1-Hnn` (`G4_R1_BRIEF.md`). A bare `Hnn` is never
used as an id; the historical compound names H05-GEOM and H05-LRA-COUPLED (the G4 H05 split) keep their names.

## 1. Purpose

On 2026-10-17 the owner answered the R1 owner questions with one package re-allocation: a smaller battery, the battery
Z saving moved to the REAR band, J1501 / J201 / J202 on MAIN B.Cu, the LRA on MAIN B.Cu in the battery annulus, a
zirconia-class caseback cup with a serviceable radial O-ring, and +3.0 mm button bosses. R2 must decide
deterministically whether this package closes the Rev-A case at `D_case_body <= 51.00 mm` with **exactly zero** total
Z change. Everything that does not close must be quantified as a numeric supplier threshold, a named owner question
or a stop. R2 verifies; it does not assume. In particular, the first-order synthesis of 2026-10-17 (section 2.4) is
context, not evidence.

R2 is organised in lanes. A lane that fails does not invalidate another lane. All lanes are evaluated at **one joint
design point** per battery (R1:R2-1).

| Lane | Driving decision (section 3.2) | R2 question |
|---|---|---|
| L-PKG | OD-BATTERY, OD-G4-STACK, OD-CONN-SIDE, OD-J202, OD-G4-LRA-ARCH | Do both batteries, the offset, carrier, MAIN B.Cu zones, B.Cu connectors, FPC / harness and the joint annulus allocation fit with zero Z and no double-credited volume? |
| L-STR | Q-R1-STRUCTURE / OD-G4-MATERIAL | Does the zirconia cup meet deflection <= 0.050 mm with no forbidden contact, and what allowable does each battery require? |
| L-SEAL | Q-R1-MAIN-SEAL | Does a raised, serviceable radial O-ring on the cup close in the REAR band plus the freed outer annulus? |
| L-CHG | OD-J202 / Q-R1-CHARGER, C-R2-01 | Do block, land and feedthrough, plus the local drop to J202 on B.Cu east, close under the amended C-R1-01 2(v)? |
| L-BTN | Q-R1-BUTTON-ENVELOPE | Which of T1 / T2-F / T2-R close per switch inside its frozen window with bosses <= +3.0 mm? |
| L-LRA | OD-G4-LRA-ARCH | Is there a MAIN B.Cu annulus pose (offset 0-1.5 mm)? If not, is there a Z-neutral F.Cu pose <= 2.70 mm? What is the BMM350 distance? |
| L-RAD | OD-CONN-SIDE, OD-J202 | Are XF / XB / XC (and XL) eliminated by geometry or closed? Do straight runs, walls and insertion close? |
| L-ASM | all | Is the sequence executable with the offset battery, B.Cu connectors, LRA and cup? |
| L-WIN | OD-G4-WINDOW (unchanged) | Does W1 at 0.50 mm still hold? (SUPPLIER_GATED) |

## 2. Entry state

### 2.1 Repository

- Contract authored on `mechanical/g4-r2-package-closure` at HEAD `27f7a3a0570bb79c27df530cd5d99c7ea7597f9f`. The
  R1 record is pinned at that commit. The G4 record is pinned at `00e77cbe107a79ac05194f19b674f7ab8d5941c9`.
- Brief SHA-256 pins carried into R2 inputs: `G4_BRIEF.md`
  `16163137593ac9d4158c051016fd159c9adad51ab05a22518b9ce5cc19334c21`; `G4_R1_BRIEF.md`
  `4d2658d855b227ccf8635a656478c1ad5bac442153b1026b7eb12dbc875bf312`.
- **Entry observation (2026-10-17):** the worktree carried a pre-existing, unstaged modification of
  `rear_sensor/rear_sensor_revA.kicad_pro` (a KiCad `top_level_sheets` auto-insert, file mtime 05:37). The contract
  session did not make it and did not touch it. The owner has since reverted it as a KiCad auto-save (owner answer
  E-1, 2026-10-17, section 17.1).
- **Precondition E-1** (kept as a mandatory check). Implementation starts only on a clean tree whose HEAD is the R2
  contract commit (this brief, parent `27f7a3a…`). The implementer never reverts, stashes, commits or edits a stray
  KiCad or other out-of-scope change; the owner resolves it. Reason: such a change lies outside every mechanical
  allow-list, it turns the G3 / G4 / R1 scope checks red for a non-R2 reason, and it fails the KiCad-immutability
  diff. If E-1 fails, raise R2-S13 and do not start.

### 2.2 Accepted state carried in

- G2-REVA 16.350 / 16.796 / 18.040 mm and G2-REVA-HI 16.380 / 16.825 / 18.040 mm (nominal / RSS / linear worst).
  OD-THICK-REVA headroom is 0.150 / 0.204 and 0.120 / 0.175 mm (nominal / RSS). The G4 / R1 Z delta is 0.000.
- R1 G4-B diagnostic point: D 50.90 mm, bulk wall 1.10 mm, D_radial_core 50.50 mm. R1 dispositions: L-BTN, L-SEAL,
  L-CHG, L-STR and L-ASM OWNER_GATED; L-LRA ARCHITECTURE_GATED; L-WIN and L-RAD SUPPLIER_GATED.

### 2.3 Known documentation debt (recorded; not edited by R2)

- `generated/g4_r1_blockers.md` line 5 and `generated/g4_r1_blockers.json.status` still say "R1 study result
  (uncommitted; independent review pending)" although the files are committed at `27f7a3a`. They are immutable. R2
  lists the debt in its report and never repeats it: the R2 status string must not depend on commit state (P-4).
- `inputs/input_register.json` still carries the frozen invariant "Battery LPR454440 selected; not replaceable without
  owner authorization" and the 2026-10-11 wording of OD-CONN-SIDE / OD-J202. The 2026-10-17 decisions are that
  authorization. R2 records them only in its own files (section 3.2). The register update is a later lead state record
  under its own contract.

### 2.4 Context (not accepted evidence)

A read-only first-order synthesis (2026-10-17) estimated that the package closes all lanes at D 50.9 mm / T_total about
16.35 mm, with thin margins. Its estimates:

- the LPR433736 radial-seal spigot is about 0.30 mm short if confined to the REAR band, so it must use the freed outer
  annulus;
- caseback stress is about 159-186 MPa (LPR433736) and about 141-162 MPa (LPR403736) against the 150 MPa planning
  allowable, with deflection passing.

R2 must verify all of these deterministically. Section 20 lists lead arithmetic that already contests parts of the
synthesis (LRA plan fit, charger radial limit).

## 3. Owner decisions (authoritative)

### 3.1 In force and unchanged

All decisions recorded in `G4_BRIEF.md` sections 2.1-2.2 and `G4_R1_BRIEF.md` section 2.2 stay in force verbatim, and
everything they carry stays with them, except the specific items that section 3.3 lists as superseded for R2. In
particular, these stay binding:

- OD-G4-ENTRY: radiator volumes are hard keep-outs, with no new metal or wiring;
- OD-G4-CORNER: design value plus declared tolerance; no speculative credit;
- the OD-G4-ENVELOPE 51.0 mm hard ceiling and minimization rule (the boss limit is superseded);
- OD-THICK-REVA, OD-WATER, OD-REAR-SIDED, OD-COVER, OD-U8 and OD-DEVACCESS;
- OD-G3-ENTRY, OD-G3-SIDE, OD-G3-RECORD and OD-G3-MAX86141-PKG;
- OD-G4-WINDOW and OD-G4-ASSEMBLY.

### 3.2 New — owner decisions of 2026-10-17 (verbatim)

Record them verbatim (date 2026-10-17, source: owner decision, `G4_R2_BRIEF.md` section 3.2) in
`inputs/g4_r2_closure.json.owner_decisions` and `generated/g4_r2_closure.json.owner_decisions`. Do not record them in
`input_register.json`, `architecture.json` or `README.md`.

```text
- OD-BATTERY: Rev-A battery LPR454440 (870 mAh, Ø44 x 4.5) replaced by
  LPR433736 (585 mAh, 3.7 V, 1C, Ø37 x 4.3 mm, 2.16 Wh), same J201
  connector. Catalogue values pending supplier protected-pack drawing
  (SR-BATT-PACK). If the drawing contradicts the assumed envelope: STOP.
  Fallback LPR403736 (495 mAh, Ø37 x 4.0) only if the caseback
  allowable cannot support LPR433736.
- OD-G4-STACK: zero total Z growth; battery Z saving reallocated to the
  REAR band. OD-THICK-REVA (<= 16.5 mm nominal, <= 17.0 mm RSS)
  unchanged.
- Q-R1-BUTTON-ENVELOPE: proven mechanical buttons: sealed metal pusher
  through the case (stem O-ring or elastomer boot/seal, whichever
  closes), pressing a right-angle side-actuated tactile switch at the
  MAIN board edge; local case bosses <= +3.0 mm (incl. seal and
  tolerance) at the five existing button windows only (10, 9, 8, 2,
  4 o'clock). C-R1-03 ruling not needed. Inductive/force buttons
  deferred to Rev-B. SG: SR-BUTTONS.
- OD-CONN-SIDE: J1501, J201, J202 on MAIN B.Cu; U7 (DRV2625) to B.Cu.
- OD-J202 / Q-R1-CHARGER: J202 on B.Cu toward east; charger contacts on
  the caseback at ~3 o'clock; retire the perimeter conductor band
  except the local charger drop. C-R1-01 2(v) AMENDED to: clear in 3-D,
  i.e. separated in plan OR in Z, with strict 3-D clearance. Record the
  amendment in G4-R2 only; G4_R1_BRIEF.md stays unchanged.
- OD-G4-LRA-ARCH: LRA on MAIN B.Cu in the battery annulus (battery
  offset 0–1.5 mm allowed). Fallback: LRA <= 2.70 mm tall on MAIN F.Cu
  (Z-neutral) if no B.Cu pose exists. Report BMM350 distance.
- Q-R1-MAIN-SEAL: raised, serviceable radial O-ring on a caseback cup.
  Adhesive main seal rejected.
- Q-R1-STRUCTURE / OD-G4-MATERIAL: ceramic (zirconia class) caseback
  cup on the G4-B midcase (metal with dielectric sectors).
- OD-AOD: no always-on display in Rev-A.
- K1-A: authorized in principle, in parallel with G4-R2, under its own
  separate contract (REAR layout + MAIN power-schematic fixes after
  independent verification). Not part of G4-R2.
- OWNER POSITIONS: G5 (antennas) directly after G4-R2; nothing new in
  the reserved GNSS (12), BLE (10–11), Wi-Fi (3:30–4:30) regions. MAIN
  stays shield-ready (§20); shield material decided after Rev-A testing.
```

### 3.3 R2 application of each decision (binding lead application; changes need an owner amendment)

Every interpretation below is a contract reading, not a new decision. It is listed again in section 17.2.

| Decision | Binding R2 consequence | Superseded for R2 (overlay record) | Not authorized / not decided |
|---|---|---|---|
| OD-BATTERY | Both batteries are evaluated side by side (section 6.1). LPR433736 is primary. Catalogue values carry evidence class OWNER_DECISION with the mandatory label `catalogue_value` and gate SR-BATT-PACK (no local primary document). The fallback is never selected by the model (section 7.1.6). The J201 interface is unchanged (1 GND / 2 BAT_NTC / 3 VBAT). | frozen invariant "Battery LPR454440 selected"; `stack_parameters` `D_pack_nom` 44.0 and `t_pack_nom` 4.5 (OV-BATT-ID, OV-BATT-DIA, OV-BATT-THICK) | energy, runtime or capacity claims; LPR403736 values not given by the owner (voltage, C-rate, Wh) are not invented; MPN or supplier claims |
| OD-G4-STACK | The battery Z saving `Delta = t_pack_nom(LPR454440) - t_pack_nom(battery)` (0.200 / 0.500 mm) leaves `battery_zone` and is added as one fixed REAR-band allocation (section 6.3). T_total is identical. | `battery_zone` / REAR-band split of the G2 stack (OV-Z-REAR-BAND) | any other layer change; any Z credit; any tolerance assigned to Delta |
| Q-R1-BUTTON-ENVELOPE | Bosses <= +3.0 mm beyond `D_case_body/2`, boss plus boot / seal protrusion plus tolerance, only inside the five frozen windows. Topologies: T1 stem O-ring (re-admitted, section 7.4.1), T2-F and T2-R elastomer boot / seal. T3 is not carried (not a sealed pusher). C-R1-03: I-SUM binds, I-MAX is reported, `c_r1_03_adjudication` stays `null`, and no I-MAX-only closure exists. Pusher material per Q-R2-SW5-PUSHER and Q-R2-SW1-BLE (DECIDED, 17.1), which supersede the Q-R1-BUTTON-ENVELOPE clause 'sealed metal pusher' for SW5 and for SW1 respectively (that clause stays binding for SW2-SW4): SW1 and SW5 non-metallic (zirconia or PEEK class); SW2, SW3 and SW4 metal. Boss growth inside a reserved region is non-conductive (Q-R2-BOSS-MATERIAL, DECIDED, 17.1). | OD-G4-ENVELOPE +1.0 mm boss limit (OV-BOSS); R1 "T1 never selectable" (OV-BTN-TOPOLOGY) | moving any switch or window; switch MPN; inductive / force buttons |
| OD-CONN-SIDE | J1501, J201 and J202 on MAIN B.Cu. U7 on B.Cu is the existing G2 `U7-B.Cu` allocation, confirmed. OV-U7 records the no-op confirmation r2_value = pinned U7-B.Cu. | G2 `J1501-F.Cu`, `J201-F.Cu`, `J202-WEST-F.Cu` (OV-CONN-J1501, OV-CONN-J201, OV-CONN-J202) | KiCad moves; connector MPN; interface change. The mirrored physical position order is a recorded K1 requirement only. |
| OD-J202 / Q-R1-CHARGER | J202 sits in the MAIN B.Cu east sector; its mate direction is a design variable. Contacts stay in the CHG_CONTACT wedge (az 80-100) on the caseback. The REAR-level perimeter conductor band is retired except an explicitly pinned local-drop footprint (section 6.6). The amended 2(v) is recorded as C-R2-01 (section 7.3.1). | CHG_ROUTE, CHG_LINK, CHG_RISER, CHG_APPROACH, the LRA lead channel and the LA-Z-2 perimeter band (OV-COND-BAND); C-R1-01 2(v) "in plan and in Z" (OV-C-R1-01-2V) | editing `G4_R1_BRIEF.md`; U1201 / D1201 relocation (recorded as a requirement only) |
| OD-G4-LRA-ARCH | Primary: MAIN B.Cu in zone B (section 6.4), battery offset 0-1.5 mm. Fallback: MAIN F.Cu, evaluated always but selected only if no B.Cu pose exists. "Z-neutral" binds: seated height including mount allowance must be <= the governing front-gap part height 2.70 mm at linear worst. The BMM350 (U703) distance is always reported. | REAR-level LRA allocation and the R1 caseback-pocket search (OV-LRA) | no class authored to fit (C-R1-08). The LRA magnet is authorized by OD-G4-LRA-MAG (DECIDED, 17.1); that does not lift the MAG_CLEAR exclusion (G4 8.9, G4-H18). Magnetometer calibration is a later firmware / test item, not an R2 check. |
| Q-R1-MAIN-SEAL | Radial O-ring in a groove **on the ceramic cup's raised wall**, sealing against the midcase bore, in the static radial window. The caseback is screw-retained and serviceable. The adhesive main seal is not evaluated as an option. The face seal is shown only as the R1 column. | R1 main-seal topology set (OV-SEAL) | any adhesive main-seal closure |
| Q-R1-STRUCTURE / OD-G4-MATERIAL | One architecture, **G4-B-ZC**: the G4-B midcase (MAT-NF-METAL with MAT-GF-POLY dielectric sectors) plus a MAT-CERAMIC (zirconia class, PC-CERAMIC-GRIND) caseback cup. G4-A and G4-C1 are not carried. The material choice stays conditional on G5 (`G4_BRIEF.md` 2.3). | R1 candidate set (OV-MATERIAL) | zirconia strength or supplier data; the 150 MPa planning allowable is unchanged |
| OD-AOD | Recorded. No R2 lane consumes it. | — | power or battery-life claims |
| K1-A | Recorded. Not part of R2. Owner-confirmed scope (Q-R2-K1A correction, DECIDED, 17.1, superseding the first-round Q-R2-K1A text): K1-A = REAR layout / routing with all G3-B-S14 part positions frozen, plus MAIN power-schematic fixes; no MAIN outline, placement or routing. It moves nothing G4-R2 relies on. Isolation rules in section 4.5. | — | any K1 / K1-A work in R2 |
| OWNER POSITIONS | G5 follows R2, but R2 authorizes nothing. Reserved regions follow R2-H15 and the decided rule of section 6.9 (Q-R2-RESERVED-REGION). Shield-ready means the recorded clearance of architecture.md section B, "Shield-ready clearance" paragraph (U101 can 0.8–1.0 mm, nominal 0.85; h_shield_can + c_front = 1.0 mm against the 2.85 mm front gap; U101 shield polygon 92.95 mm2) is preserved; the owner accepted this reading (Q-R2-SHIELD-REF: "§20" is the master handoff's shield-ready policy, not a repo file; the owner text says "section A" after this brief's former mislabel, and the accepted paragraph is the one in section B). | — | G5 work; shield material; RF claims |

### 3.4 Not decided here (unchanged open items)

These remain open with their G4 provisional defaults: OD-G4-ATM-STD (`p_test` 0.500 nom / 0.625 max MPa), OD-G4-STRAP
and SERVICE-COVER-REBOND. OD-G4-LRA-MAG is decided (authorized, section 17.1). The LPR403736 switch remains undecided
(section 7.1.6). The conditional question Q-R2-BATTERY (section 17.1.2) is also not decided here.

## 4. Governance, immutability and the R2 overlay

### 4.1 Immutability

Every file tracked at `27f7a3a0570bb79c27df530cd5d99c7ea7597f9f` stays **byte-for-byte identical on disk**. That
covers the G1, G2, G3, G4 and G4-R1 records, including:

- all briefs;
- `inputs/*.json`, `tools/*.py` and `generated/*`;
- `architecture.md`, `architecture.json`, `README.md`, `PHASE_BRIEF.md`, `tools/arch_diagrams.py` and
  `tools/mech_model_spec.md`;
- every KiCad, interface, placement and library file.

The only permitted repository change is the addition of `R2_FILES` (section 4.6).

### 4.2 The R2 overlay (explicit supersession, in memory only)

The battery change and the bounded G2 re-allocation exist **only** as an overlay in `inputs/g4_r2_closure.json.overlay`.
It is a list of supersession records:

```text
{id, pinned_source (path + JSON pointer or brief section), authority (owner-decision id), r2_value,
 scope: "G4-R2 only"}
```

The required record set is exactly: OV-BATT-ID, OV-BATT-DIA, OV-BATT-THICK, OV-Z-REAR-BAND, OV-CONN-J1501, OV-CONN-J201,
OV-CONN-J202, OV-U7, OV-LRA, OV-COND-BAND, OV-BOSS, OV-BTN-TOPOLOGY, OV-C-R1-01-2V, OV-SEAL and OV-MATERIAL.

Rules:

1. The pinned value of each record is read at run time from its pinned source (hash-checked), never typed as an
   authority. The tool reports pinned value, R2 value and authority side by side.
2. The overlay is applied to deep copies of the parsed pinned inputs. Nothing is written back.
3. No attribute of an imported G1-R1 module is patched, except the prospective `g4_case_sealing.ALLOWED_CHANGES`
   extension of section 4.4.
4. Where an imported function hard-codes a superseded value or reads a pinned file from disk, R2 must do one of two
   things: pass the overlaid copy through the function's parameters, or re-implement the function in R2 with an
   **overlay-off equivalence test** (PA class). The test shows that, at the pinned inputs, the R2 function returns the
   library result exactly.
5. Every R2 result lists the overlay records it depends on. With the overlay switched off, the R2 code path reproduces
   the declared G4 / R1 anchor values (R2-H03).
6. G2 is not reopened as a study. Its record, numbers and allocation remain the accepted G2 history and reproduce
   byte-identically. The overlay only states which G2 allocations R2 evaluates differently, and on whose authority.

### 4.3 G3 is not reopened — exact check (R2-H16)

R2-H16 passes only if every item below holds at nominal, conservative and optimistic corners and at linear worst:

1. **REAR XY.** Every G3-B-S14 REAR placement, face, rotation and the REAR transform are identical to the pinned
   `generated/g3_rear_optical.json.g4_handoff` (candidate G3-B-S14, `released: true`). That includes:
   - outline circle r 16.400 mm about (100, 100);
   - pod polygon 411.997 mm2;
   - apertures;
   - U6 island (az 45, r 13.0) with F1 / F2 / F3;
   - J1502 tail exit `radial-r11.3-a166.05`.

   No overlay record maps into G3 data.
2. **REAR Z relative to the pod plane.** These are unchanged relative to the pod-plane datum (`h_pod` = 0.0, LA-Z-1):
   - the Z of the REAR skin face, `rear_pcb`, `optics_zone` and `window`;
   - `pod_depth` 1.35 / 1.85 / 1.05;
   - the caseback residual before wall 0.55 / 1.05 / 0.25.

   Delta appears **only** frontward of the REAR inner-face parts and support lands. Inside the S14 outline it is
   clearance between the REAR inner face and the carrier lower-web underside. Outside the outline it extends the
   REAR-periphery band.
3. **Support-land plan.** Support lands stay at azimuth 30 / 150 / 270 with their pinned polygons. Nothing is
   enlarged, and no new contact is made on the REAR board.
4. **Carrier pillars.** The carrier hard-stop pillars that bear on the three support lands may be taller by exactly
   Delta (0.200 or 0.500 mm). This is a carrier change only. Footprints stay inside the pinned land polygons, there is
   no new load into the REAR board other than the existing hard-stop function, and zero pressure load passes through
   them (R2-H08).
5. **Zero optical / board mutation.** No change to any REAR part, cell, window variant, barrier, seal land, thermode or
   tail-corridor reservation of G3.
6. **G3 gates.** The G3 conservative-corner gates (lower_web, cell_barrier_gap, pd_in_paths, tail_fit, support_lands)
   stay G3 gates. R2 never claims to close them, even where Delta changes the volume available. R2 may report the
   consequence as a diagnostic.
7. **Retired reservations.** CHG_ROUTE and CHG_LINK are retired by OV-COND-BAND, so their frozen G3 plan clearances
   (1.100 / 3.600 / 0.600 mm) are reported as "retired reservation; S14 unchanged". This is never a G3 edit.

A failure of any item raises R2-S01.

### 4.4 Historical reproduction (R2-H20)

| Record | Mechanism | Required outcome |
|---|---|---|
| G1, G2 | `mech_model.py`, `g1_scenarios.py` and `g2_interconnect.py` `check` in the R2 tree | exit 0 |
| G3 (scope-only) | `g3_rear_optical.py check` and `arch_diagrams.py check`: clean-tree protocol of `G4_R1_BRIEF.md` section 11 | Green on a clean tree after the §21.2 manual commit gate (lead re-run); before that gate it is red on scope only, with a read-only in-process proof that patches only `scope_check`. |
| G4 at its pin | read-only detached worktree at `00e77cb…`: `g4_case_sealing.py check` and `selftest` | exit 0; selftest 32/32 |
| G4 in-process | `g4_r2_closure.py check` sets `g4_case_sealing.ALLOWED_CHANGES |= R1_FILES ∪ R2_FILES` (exactly those paths, no wildcard) and runs the G4 module's own build / validate / self-tests | all seven G4 generated files byte-identical; 32/32 |
| G4-R1 at its pin | read-only detached worktree at `27f7a3a…`: `g4_r1_blockers.py check` and `selftest` | exit 0; every self-test caught; count equal to the count produced at `27f7a3a` (lead-recorded 163 at R1 acceptance; a runtime value not stored in a committed artifact, so the implementer re-verifies it at the pin) |
| Literal G4 / R1 checks in the R2 tree | as committed | **Expected red** (later-phase scope; R1 also embeds its changed-path list in its JSON). Recorded, not evidence, not required green. |

Notes:

- R2 does not run R1's `build_r1_results`, `r1_validate`, scope or self-test entry points in the R2 tree. It may import
  `g4_r1_blockers` as a library for geometric, seal, charger, structural and LRA functions.
- The R1 check has a 90 s runtime gate that measured 81.9-89.4 s under load (lead-recorded runtime values, not stored in
  a committed artifact; verified at implementation). Run the detached R1 check on a quiet host.
  If its only failure is the runtime gate, record both timings and re-run quiet. Any other failure is R2-S10.

### 4.5 K1-A isolation

- R2 reads no live KiCad geometry. It uses only the pinned G1-R1 data (height map, placement-derived reservations,
  G3 handoff).
- R2 never merges, rebases or cherry-picks K1-A work.
- Any KiCad, interface or placement path that differs from `27f7a3a` in the R2 tree raises R2-S10.
- The owner confirmed the K1-A scope (Q-R2-K1A correction, DECIDED 2026-10-17, section 17.1, superseding the
  first-round "MAIN schematic-only" text): K1-A = REAR layout / routing with all G3-B-S14 part positions frozen, plus
  MAIN power-schematic fixes; no MAIN outline, placement or routing. It moves nothing R2 relies on. K1-A REAR routing
  may change REAR copper files, so the KiCad-immutability check of this tree (R2-S10) is what keeps any K1-A work out
  of R2. The checks above stay in force as safeguards. If a
  datum that R2 pins (G3-B-S14 placements, U7 / U703 / U8 / U101 positions, the B.Cu population, the 24 / 13
  interface) differs anyway, R2 results are invalid for that state and need re-validation under a new contract.

### 4.6 Files (`R2_FILES`, exact set)

| Path | Role |
|---|---|
| `design/mechanical/G4_R2_BRIEF.md` | this contract (lead; immutable after its contract commit) |
| `design/mechanical/inputs/g4_r2_closure.json` | Authored R2 inputs only: owner decisions verbatim, overlay records, catalogue values (labelled), authored PROVISIONAL envelopes (PCM lobe, cup grids), grids, pins, `lra_supplied`, `supplier_evidence`, `fallback_trigger`, `open_question_answers`, budgets. Never results. |
| `design/mechanical/tools/g4_r2_closure.py` | Stdlib only. Sub-commands `build`, `check`, `selftest`. Imports `g4_case_sealing` and `g4_r1_blockers` as libraries; re-implements only under rule 4.2-4. |
| `design/mechanical/generated/g4_r2_closure.json` | authoritative result, <= 2 MB |
| `design/mechanical/generated/g4_r2_closure.md` | report |
| `design/mechanical/generated/g4_r2_plan.svg` | Plan view: case and bosses; pack envelope with offset; carrier; zones A / B; connectors; FPC / harness / drop; LRA; cup ring; charger block / land; radiator volumes; reserved regions; MAG_CLEAR; MAIN outline columns. |
| `design/mechanical/generated/g4_r2_sections.svg` | Sections: J1501 south; charger / J202 east; LRA pose; worst button and SW5; cup / seal generic; pillar at an S14 land. |
| `design/mechanical/generated/g4_r2_annulus.svg` | joint annulus ledger (azimuth x Z occupancy, per battery) |
| `design/mechanical/generated/g4_r2_sweep.jsonl` | **optional**: only if the JSON would exceed 2 MB; one canonical object per line, sorted |

**May modify:** nothing else. R2 does not modify the state record (`architecture.*`, `README.md`,
`input_register.json`). That record is a later lead commit after independent review.

## 5. Frozen carry-ins (unchanged unless an overlay record of section 4.2 supersedes them)

- **Z stack.** G2-REVA / G2-REVA-HI per section 2.2. OD-THICK-REVA: nominal <= 16.5 and RSS <= 17.0 on both.
- **G3-B-S14.** Exactly as section 4.3.
- **MAIN and switches.** MAIN placement. The five switch windows (SW1 292.5-307.5, SW2 262.5-277.5, SW3 232.5-247.5,
  SW4 52.5-67.5, SW5 112.5-127.5 deg) are **frozen; button azimuths never move**.
- **Azimuth convention (pinned).** `architecture.md` Conventions: front view from the display; north/12 = -Y,
  east/3 = +X, south/6 = +Y, west/9 = -X; MAIN origin (100, 100); azimuth = degrees clockwise from north (0 deg =
  12 o'clock); Z positive from the front exterior toward the wrist (same convention in the imported G4 geometry,
  `tools/g4_case_sealing.py`).
- **Charger.**
  - CHG_CONTACT wedge az 80-100, r 17.5-24.0. Block 4 x 5 mm, never reduced. Land 0.5-1.0 mm, adverse 1.0.
  - C-R1-01 items 1, 2 (i)-(iv), 2 (vi), 3 (caps 0.75 mm and 78.0-102.0 deg) and 4 (strict-wedge diagnostic /
    supplier path), with `c_chg_window`.
  - Contacts GND / +5V / +5V / GND. No charger-positive conductor in the sensor FPC.
- **Magnet and interface.** The frozen "no watch-side permanent magnet without explicit authorization and magnetometer
  analysis" invariant. OD-G4-LRA-MAG (DECIDED, section 17.1) authorizes the LRA's internal magnet only; no other
  watch-side permanent magnet is authorized. The 24-position / 13-net interface.
- **Keep-outs** (read from pinned sources):
  - GNSS_RAD: az 346.4-18.9, r 20.13-24.37, all Z;
  - BLE_RAD: az 304.1-331.8, r 15.80-25.15, MAIN;
  - WIFI_RAD: az 107.7-128.8, r 20.59-25.24, MAIN + REAR;
  - MAG_CLEAR: BMM350 U703 at (113.8, 92.6), az 62, r 15.7, 10 mm placeholder, MAIN + REAR.
- **O-ring rules.** Planning windows: static radial and static face 15-30 %, dynamic radial 10-20 %, fill <= 0.85.
  Cross-section tolerance +/-0.05 mm. Neither is widened nor narrowed.
- **G4 classes.** Material and process classes of `inputs/g4_case_sealing.json`. Notable values:
  - MAT-CERAMIC E 190 / 205 / 215 GPa; `sigma_allow` 150 / 200 / 250 MPa, where **150 MPa is the planning allowable**
    (PROVISIONAL_ASSUMPTION); `t_wall_min` 0.6 / 0.7 / 0.8 mm; no threads in ceramic;
  - PC-CERAMIC-GRIND 0.02 mm;
  - screw class SCR-M1.0-TAPPED in the metal midcase;
  - `p_test` 0.500 / 0.625 MPa;
  - deflection limit 0.050 mm (= `c_cb_rear_mm` min).
- **Window.** W1 at 0.50 mm (OD-G4-WINDOW).
- **Assembly.** C-R1-06 (display before cover). G4 A1-A11 identities.
- **R1 lead adjudications.** LA-STR-1..5, LA-Z-1, LA-LRA-1 (for any residual caseback pocket), LA-BTN-1, LA-BTN-2,
  LA-ASM-1 and LA-HC-1 carry. LA-Z-2 is replaced by OV-COND-BAND only where the band is retired (section 6.6).
  LA-STR-4 keeps denying stiffness credit to circumferential **ribs** on the plate; the cup ring rule is section 7.1.2.
- **Legacy numbers.** -0.950 / -1.100 and every LEGACY value of `G4_BRIEF.md` section 3 are reproduced, never
  overwritten.

Anything that needs one of these changed is OWNER DECISION REQUIRED or a STOP, never an R2 result.

## 6. Package re-allocation model (L-PKG)

### 6.1 Both batteries, side by side

LPR433736 (primary) and LPR403736 (fallback) are always evaluated with identical rules, grids and tolerances. Every
result table shows both columns, with margins and required allowables per battery. No result of one battery is
credited to the other. Each battery has its own joint design point and its own verdict. The package verdict is the
primary battery's (section 12).

### 6.2 Battery envelope assumptions (labelled; lead arithmetic for orientation, the tool recomputes)

| Term | Evidence / role | LPR433736 nominal / linear worst | LPR403736 nominal / linear worst |
|---|---|---|---|
| Cell diameter | OWNER_DECISION, `catalogue_value` (SR-BATT-PACK) | 37.0 | 37.0 |
| `tol_pack_dia` (incl. tape / edge seal) | SUPPLIER_GATED planning, `stack_parameters` unchanged | 0.3 / 0.5 | 0.3 / 0.5 |
| `R_pack = (D + tol)/2` | PROJECT_DERIVED | 18.65 / 18.75 | 18.65 / 18.75 |
| radial growth / pack-to-carrier `g_radial` | SUPPLIER_GATED (G4 `g_radial_mm`, SR-BATT-GROWTH); no growth credit | 0.5 / 1.0 | 0.5 / 1.0 |
| carrier wall `t_cw` + PC-CARRIER-MOULD 0.05 | DESIGN + MFG_TOL (grid) | design | design |
| carrier outer radius at `t_cw` 0.40, centred | PROJECT_DERIVED (orientation) | 19.55 / 20.20 | 19.55 / 20.20 |
| Cell thickness | OWNER_DECISION, `catalogue_value` | 4.3 | 4.0 |
| `tol_pack_thick` (incl. PCM fold) | SUPPLIER_GATED planning, unchanged | 0.1 / 0.3 | 0.1 / 0.3 |
| `g_axial` swelling | SUPPLIER_GATED; absolute planning values kept, **not rescaled to the thinner cell** | 0.3 / 0.5 | 0.3 / 0.5 |
| `c_axial` | PROVISIONAL, unchanged | 0.1 / 0.2 | 0.1 / 0.2 |
| `battery_zone` | PROJECT_DERIVED (was 5.00 / 5.50, thin corner 4.75) | 4.80 / 5.30 (thin 4.55) | 4.50 / 5.00 (thin 4.25) |
| Delta to REAR band | PROJECT_DERIVED, OD-G4-STACK; identical at every evaluation | 0.200 | 0.500 |
| PCM lobe envelope (radial x tangential x Z) | PROVISIONAL_ASSUMPTION authored in R2 inputs (min / nom / max with rationale); never supplier data | authored | authored |
| PCM / tab exit azimuth | PROVISIONAL (G2 `pcm_az_deg` 220 / 230 / 240), plus a full-azimuth admissibility report (0-355 step 5) | sweep | sweep |
| `t_insulator` | G1, unchanged | 0.05 / 0.10 | 0.05 / 0.10 |
| Offset magnitude | OWNER_DECISION range | 0-1.5 | 0-1.5 |
| Capacity / electrical | OWNER_DECISION, `catalogue_value`, recorded only | 585 mAh, 3.7 V, 1C, 2.16 Wh | 495 mAh (nothing else given) |

**Assumed envelope (R2-S09 trigger).** The assumed envelope of each battery is:

- finished-pack diameter <= 37.5 mm at its maximum;
- finished thickness <= cell thickness + 0.3 mm at its maximum;
- supplier-permitted growth <= 0.5 mm axial and <= 1.0 mm radial;
- PCM lobe inside the authored adverse lobe envelope;
- tab / exit inside the swept PCM azimuth window;
- a three-wire exit compatible with J201.

If a recorded SR-BATT-PACK document in `inputs.supplier_evidence` (local primary document with page / table / figure)
contradicts any item, the run raises R2-S09 (owner STOP). It is never re-optimized around. Without that evidence,
every L-PKG and Z margin carries the label "pending SR-BATT-PACK".

### 6.3 Z overlay (OD-G4-STACK, R2-H01, R2-H21)

1. `battery_zone` is recomputed with the overlaid cell thickness through the **imported** G1 / G2 rule and tolerance
   policy.
2. Delta is inserted as one fixed REAR-band allocation (no tolerance term), frontward of the REAR inner face (section
   4.3 item 2).
3. T_total, T_body and every other layer of G2-REVA and G2-REVA-HI must be identical: **total Z delta exactly 0.000 at
   nominal, RSS and linear worst** on both baselines.
4. The REAR-periphery band gains exactly Delta.
5. No credit is taken from a lower zone-A governing height or a thinner cell's tolerance.

### 6.4 MAIN B.Cu height zones (R2-H24)

- **Zone A** is the plan projection of the pack envelope at linear worst: `R_pack` + `g_radial` + carrier wall +
  tolerance, about the offset centre, including the PCM lobe. Every MAIN B.Cu item in zone A must have a seated height
  <= the accepted G2-REVA back-zone governing height (read from the pinned G2 stack). The back zone therefore stays
  byte-identical.
- **Zone B** is MAIN B.Cu outside zone A and inside the binding MAIN outline column (R2-V24). A zone-B item may hang
  from MAIN B.Cu through the back-zone and battery-band Z range. Its Z interval must be strictly 3-D-clear of
  everything below it (R2-H22).

Zones are recomputed for every battery and offset. Existing B.Cu parts (C206, C901-C906, R901-R910, U7) are evaluated
in whichever zone they fall.

### 6.5 Interconnects on B.Cu (R2-H25)

- **J1501** sits on MAIN B.Cu with an **axial mate toward the REAR**: the mating axis is parallel to Z, the mating face
  points to the wrist, and the plug is inserted from the rear. This is a lead design rule (evidence class DESIGN,
  section 17.2 item 19), not a reading of owner text. The sensor FPC path is:
  - J1502 tail (frozen exit) → under-run groove inside the carrier lower web (G2 channel architecture) → annulus
    riser → J1501.

  Report for the FPC:
  - installed length and bend count;
  - `R_bend` >= `R_bend_min` adverse (2.0 mm), else the SR-FPC-MECH zero-margin value;
  - the mating / fold motion and build state;
  - service slack location. Slack is never doubled in an unallocated annulus volume; this G2 channel-architecture rule
    carries. A slack volume is either a pocket below the web or an allocated annulus volume.

  The mirrored physical position order is a K1 requirement. The logical 24 / 13 interface is unchanged.
- **J201** sits on MAIN B.Cu in zone B near the PCM exit. Its mate direction is a DESIGN option. Report battery-tail
  length and the VBAT path estimate (no routing).
- **J202** sits on MAIN B.Cu in the east sector. Its mate direction is a DESIGN option. Its window must exclude:
  - WIFI_RAD and the owner Wi-Fi region (section 6.9);
  - MAG_CLEAR (current-carrying path);
  - the SW4 / SW5 bores;
  - the charger wedge features.

  The **local charger drop** runs from the FT-C feedthrough inner face to J202. Report its length, bend count and
  service length with the caseback in its open (A10) position. The U1201 / D1201 entry-protection relocation is a
  recorded requirement only.
- **U7** stays on B.Cu. LRA leads terminate on B.Cu (section 7.5).

### 6.6 Conductor-band retirement (OV-COND-BAND)

LA-Z-2 is inverted for R2. A REAR-level conductor band exists **only** where a pinned plan footprint plus Z interval
exists in R2 inputs. The local charger drop footprint is mandatory. Any other remaining REAR-level conductor must be
listed explicitly.

The sensor under-run inside the lower web is not part of the band. The battery tail and FPC risers sit at BATTERY
level in the annulus.

CHG_ROUTE, CHG_LINK, CHG_RISER, CHG_APPROACH and the G2 LRA lead channel are retired. Their volumes are released only
where no pinned footprint remains.

### 6.7 Carrier, pillars, offset and supports (R2-H18, R2-H23)

- Pack + growth + PCM lobe stay inside the carrier at linear worst, for each battery and offset.
- Carrier wall >= 0.30 mm adverse.
- Pillars per section 4.3 item 4.
- The MAIN carrier pockets (storage, VBAT) are preserved.
- >= 4 case / caseback supports including W/NW, all outside the offset pack envelope (G4 H24, X18).
- Offset grid per R2-V05.

### 6.8 Joint annulus allocation (R2-H22)

The shared domain is the union of three volumes:

- zone B from MAIN B.Cu down to the lower-web level;
- the battery-band outer annulus between the carrier and `r_case_inner(az, z)`;
- the REAR-periphery band outside the S14 outline + 1.1 mm, down to the caseback.

Occupants include at least:

- the pack envelope with PCM lobe and growth; the carrier wall and floor; pillars;
- case-side supports and stop pads;
- J1501, J201 and J202, each with body, mated plug and mate-stroke envelope;
- the sensor FPC riser, bends and service slack; the battery tail; the local charger drop;
- U7; the LRA with lead / exit and mount;
- the cup as one ceramic occupant (plate + ring + raised spigot wall with gland) with declared sub-volumes that
  partition its solid; the structural periphery shortfall (7.1.4) and the spigot shortfall (7.2.1) are two demands on
  this one allocation and are never independently credited (rule 3); caseback ring and ribs where disjoint from the
  cup wall;
- the charger block, land and feedthrough;
- screws and screw bosses;
- switch bodies, bores, bosses and pusher strokes; lug roots; the vent.

Rules:

1. Every occupant is an explicit solid (plan polygon x Z interval) at linear worst, grown by its positional tolerance.
2. Every pair of occupants that is separated by design must have strict 3-D clearance (R1:R3-3: a gap separates only
   when > EPS) at its named required clearance. Designed contact interfaces (pack seated in carrier, screw in boss,
   mated connector pairs, integral cup plate/ring/spigot, bonded LRA mount, block-to-drop attachment) are declared
   contact pairs: they are checked by containment/interference at linear worst (grown by their positional tolerances)
   with the R1:R3-3 margin >= 0 allocation convention, never by the separation rule. No volume of a contact pair is
   credited twice (rule 3).
3. **No volume is credited to two items**, and no item's volume counts inside another item's clearance allowance.
4. Step-dependent envelopes (mate strokes, tool access, insertion sweeps) are checked against the items present at that
   assembly step (L-ASM).
5. The tool emits a ledger per battery: occupied and free volume per Z band and 15-deg sector, plus every pair's
   minimum gap.

Over-allocation raises R2-S08.

### 6.9 Radiator volumes, owner reserved regions and MAG_CLEAR (R2-H15)

An owner reserved region is the union of the frozen radiator volume and the owner clock interval taken over that
volume's radial span and Z levels (exact boundary: section 17.2 item 15):

- GNSS: 11:30-12:30, i.e. 345-15 deg, per the SECTORS register entry "GNSS N 11:30-12:30" (owner text: "GNSS (12)");
- BLE: 10-11, i.e. 300-330 deg;
- Wi-Fi: 3:30-4:30, i.e. 105-135 deg.

**Decided rule (Q-R2-RESERVED-REGION, section 17.1).** In a reserved region R2 places no new metal, no conductor and
no component. That covers connectors, harnesses, FPC, wiring, any conductive or ferromagnetic material, the pack, the
LRA, screws, metal pushers and any MAIN-outline growth. R2 also places no new conductive material or wiring in a
radiator volume (G4-H17) and no new ferromagnetic material in MAG_CLEAR (G4-H18).

Non-conductive structure is allowed. Examples: the continuous zirconia cup plate / ring / spigot, the O-ring and
boots, the SW1 and SW5 dielectric pushers, the dielectric sectors. Boss growth inside a frozen window is allowed inside
a reserved region only as non-conductive (dielectric-class) material; conductive boss growth is new metal and fails
R2-H15 (Q-R2-BOSS-MATERIAL, DECIDED, section 17.1: dielectric sector material or dielectric insert). Existing frozen
midcase metal is not "new". **Every allowed item inside a reserved region is recorded as a G5 input** in
`generated/g4_r2_closure.json`, per battery, with:

- item id and reserved region;
- material class (G4 material-class id, or the SW1 / SW5 pusher class of 7.4.2);
- permittivity class: a material-family label authored in R2 inputs with its evidence class. No numeric
  permittivity is invented; a value appears only from a local primary document, otherwise it is G5_RF_REQUIRED;
- volume inside the region in mm3, at nominal and at the linear-worst envelope.

An allowed item without a complete record fails R2-H15.

## 7. Lanes

### 7.1 L-STR — zirconia caseback cup

#### 7.1.1 Architecture and load

- The plate inner region `t_in` stays limited by the G3-frozen pod residual. Its shortfall (R1: uniform 1.836 mm
  required vs `t_in` <= 1.10 mm) is reported per battery.
- The ring / cup wall uses the REAR-periphery band, including Delta and the retired band where it is retired, and may
  extend into zone-B volume subject to R2-H22.
- Loaded-boss / bypass semantics (LA-STR-3). Screen A is reported; Screen B governs (LA-STR-2). Ribs follow LA-STR-1,
  LA-STR-4 and LA-STR-5.
- Load case: `p_max` 0.625 MPa, E min, `K_t` 2.0 at junctions and holes (R1 §6.5, PROVISIONAL, reported).
- Support: the cup rim bears axially on the midcase rear face, with >= 3, nominally 4, lug-root screws through
  clearance holes in the ceramic. The radial O-ring transmits no axial load and receives no credit.

#### 7.1.2 Cup-ring boundary

The ring is an axisymmetric member of section S_ring = the cup raised-wall cross-section (radial × Z, including the
gland groove) at the ring centroid radius r_ring, with area A and centroidal inertia I computed from that section;
properties use E = E_min(MAT-CERAMIC) and nu = nu_min(MAT-CERAMIC) from inputs/g4_case_sealing.json. The plate is the
accepted G4 annular-plate solution of the cup inner region (inner edge at the pod frame per LA-STR-3 semantics, outer
edge at r_ring) under p_max 0.625 MPa. Ring and plate are joined at r_ring by continuity of radial displacement and
rotation and by equilibrium of edge moment and radial force (the standard axisymmetric ring–plate compatibility
system; the tool documents its four equations in generated/g4_r2_closure.md). Screen A is the G4 t_eq annular-plate
screen (LA-STR-2). Screen B for the cup is the same compatibility solution evaluated at the composite ring+plate
section with K_t 2.0 applied at junctions and holes; it governs (LA-STR-2). A clamped edge is **never assumed**. The
simply-supported and clamped bounds are reported beside the compatibility result. Ring credit is 100 % only where the
ring is continuous over 360 deg at r_ring; any feedthrough or screw interruption in the ring gives zero ring stiffness
credit (LA-STR-5, continuous-only rule), and the plate is then evaluated alone.

#### 7.1.3 Checks

- **R2-H09a (hard physical):** `w_max(p_max)` <= 0.050 mm.
- **R2-H08 (hard physical):** load-path and static-clearance check (section 10.5).
- **R2-H09b:** stress against the 150 MPa planning allowable.
  - <= 150 MPa: PASS.
  - > 150 MPa with R2-H09a and R2-H08 passing: **SUPPLIER_GATED (SR-CASEBACK-CERAMIC)**, never a model-decided FAIL.
  - The tool emits `sigma_allow_req` for each battery: the governing stress in MPa to 3 decimals, with screen,
    location and governing terms. This is the allowable at which the stress margin reaches zero.

#### 7.1.4 Required report (per battery)

- governing stress and `sigma_allow_req`;
- margin to 150 MPa;
- deflection and margin;
- Screen A / B;
- the simply-supported and clamped bounds;
- **structural periphery shortfall**: the required ring / periphery thickness minus the available REAR-band +
  zone-B height. It is reported as a positive shortfall or a negative surplus, in mm, with and without the retired
  band (P-1).
- inner-region shortfall.

#### 7.1.5 Stop and carried gates

- A deflection or forbidden-contact failure at every admissible cup configuration raises R2-S05.
- FEA-1..FEA-4 and ATM-Q5 are carried unchanged. These results are planning screens, never qualification.

#### 7.1.6 LPR403736 fallback rule

The model never switches battery. `inputs.fallback_trigger` stays `{supplier_evidence: null, owner_decision: null}`.
The primary battery changes only through a reviewed input change that carries both:

- a local primary SR-CASEBACK-CERAMIC document whose qualified allowable is < `sigma_allow_req(LPR433736)`; and
- the owner decision text.

Otherwise the run raises R2-S13.

If LPR433736 is blocked for a **non-structural** reason that LPR403736 resolves, the tool raises the conditional
question Q-R2-BATTERY and does not switch. That case lies outside the OD-BATTERY fallback condition.

### 7.2 L-SEAL — raised radial O-ring on the cup

#### 7.2.1 Gland and spigot

- The groove is on the cup's raised wall and seals against the midcase bore. Use the imported G4 `gland_design`
  (radial) with the static radial window, +/-0.05 mm cross-section tolerance, and the ceramic / metal process
  tolerances.
- The cs rows of R2-V15 are each evaluated independently.
- The spigot occupies the REAR-periphery band (including Delta and the retired band where it is retired). It **may
  extend into the zone-B outer annulus**, subject to R2-H22.
- Report the shortfall if the spigot is confined to the REAR band, per battery. Lead arithmetic: about -0.30 mm for
  LPR433736 and about 0.00 mm for LPR403736 (section 20).

#### 7.2.2 Population and unit rules (R1:R5, carried exactly)

- Every authorized row is evaluated independently in an internal length unit. Unit-scaled EPS; mm / m / um regression.
- Topology feasibility = `any(r.pass_all)`.
- `r_lim` (cup interior radial limit) = min over the population. The cup-top Z = max over the population.
- R2-H11 terms (as R1:R5 defined them for R1-H11) are per-predicate max reductions over fully feasible rows, else over all authorized rows, plus a boolean
  joint-row term.
- **No representative-row feedback.** The display row is chosen last and is tested with first / last / poison
  overrides.
- **No min / max across units or predicates** (R1:R4-8).

#### 7.2.3 Seal path and serviceability

- The seal path is closed. Every aperture has exactly one primary seal.
- Screws lie outside the seal line or carry their own seal.
- S-CHG is the FT-C bonded body. Button seals follow L-BTN. The vent, cover and pod seals are as R1. U6-F3 is
  conditional.
- Serviceable: screws plus O-ring, no adhesive main seal.
- Non-closure raises R2-S07.

### 7.3 L-CHG — charger, amended 2(v), local drop

#### 7.3.1 C-R2-01 (records the owner amendment; `G4_R1_BRIEF.md` unchanged)

C-R1-01 item 2 (v) for the non-conductive land reads, for R2:

> clears screws, supports, CHG_ROUTE and CHG_LINK in 3-D, i.e. separated in plan OR in Z, with strict 3-D clearance

"Strict" is R1:R3-3: a gap separates only when > EPS. CHG_ROUTE and CHG_LINK are retired (OV-COND-BAND); their 2(v)
terms are reported as `retired item`. The local drop is a 2(vi) neighbour (strict 3-D), except at its designed
attachment to the block. Items 1, 2 (i)-(iv), 2 (vi), 3 and 4 are unchanged. Item 1's radial bound uses
`r_lim(cup) - c_chg_window`. The strict-wedge zero-margin land width stays a supplier threshold only (SR-CHG-MECH),
never credited.

#### 7.3.2 Local drop and closure

- The drop and J202 are clear of WIFI_RAD, the reserved regions, MAG_CLEAR, the SW4 / SW5 bores, the cup wall / spigot,
  the LRA and the supports.
- FT-C is binding (ceramic caseback); FT-A is a reference column.
- Charger closure is the complete physical predicate set at one pose of the joint point. Failure raises R2-S06.

#### 7.3.3 Presentation (P-2)

The headline result is physical:

- the smallest strict 3-D clearance in mm and its governing physical pair;
- the plan and Z gaps;
- `r_lim(cup)` against the radial / plan prerequisites.

Contract-category tags are secondary columns. An unsatisfiable-clause result must never be the headline.

### 7.4 L-BTN — buttons

#### 7.4.1 T1 ruling (required by the contract request)

**Where R1 excluded T1:**

- `G4_R1_BRIEF.md` section 6.2: "**T1** dynamic radial O-ring on the pusher — **regression / reference only**,
  expected FAIL; never selectable";
- V05: "T1 (regression)";
- section 11, self-test fault "T1 selected";
- section 16 item 6: "T1 never selectable";
- `inputs/g4_r1_blockers.json` `V05_button_topologies.T1`, which repeats it.

**Stated reason** (section 6.2 lead arithmetic): under the dynamic radial window 10-20 % and the +/-0.05 mm
cross-section tolerance, a pusher O-ring needs cs >= 1.69 / 2.29 / 2.89 mm at groove / bore stacks 0.04 / 0.07 /
0.10 mm. The R1 pusher class (Ø1.6-2.0 mm bore planning range inside a +1.0 mm boss) cannot carry such a ring.

**Classification:**

- (i) The gland windows and the cs tolerance **are hard rules**: frozen carry-ins (G4 `parameters.oring`; R1 section 3
  "not widened, not narrowed"). They stay binding in R2.
- (ii) "Never selectable" is an **R1-scoped lead contract clause** derived from (i) under the R1 envelope. It is not an
  owner decision, not a frozen invariant and not a G4 carry-in.

Q-R1-BUTTON-ENVELOPE changes the envelope (+3.0 mm) and explicitly names the stem O-ring.

**Result: the exclusion does not rest on a hard rule. T1 is re-admitted for evaluation under the unchanged rules (i).**
No re-admission question is raised. R1 itself is unchanged; its T1 stays non-selectable at `27f7a3a`. The independent
review must challenge this ruling (section 21).

#### 7.4.2 Topologies per switch

- **T1:** stem O-ring = groove on the pusher stem (G4 `pusher_gland` formulation), dynamic radial window. cs per
  R2-V20. Pusher core >= `core_radius_min` adverse 0.4 mm. `d_p` per R2-V18.
- **T2-F / T2-R:** as R1, including the LA-BTN-1 rim term, rim land adverse 1.0 mm and boot strain hard 0.25.
- **T3:** not carried. It is not a sealed pusher, and inductive / force buttons are deferred.

Per-switch rules:

- guide stack C-R1-02 under **I-SUM (binding)** with I-MAX reported;
- stroke >= `c_switch` adverse;
- bore clear of the rear-insertion path;
- the boss transverse extent lies inside the frozen window at the evaluated D;
- boss + seal / boot + tolerance <= 3.0 mm.

Material rules (Q-R2-SW5-PUSHER, Q-R2-SW1-BLE, Q-R2-RESERVED-REGION and Q-R2-BOSS-MATERIAL, DECIDED, section 17.1):

- SW2, SW3 and SW4: metal pushers.
- SW4: non-ferromagnetic metal (MAG_CLEAR).
- **SW1 and SW5:** non-metallic pushers, window and position unchanged. SW1 is evaluated exactly like SW5 and is not
  pre-ordained to R2-S12. For each of the two switches, two options are evaluated and both are reported:
  - zirconia class: MAT-CERAMIC with PC-CERAMIC-GRIND;
  - PEEK class: the authored polymer process tolerance PC-POLY-MOULD. No PEEK property is invented; strength and
    stiffness are SUPPLIER_DATA_REQUIRED (SR-BUTTONS) and never credited.

  Each of SW1 and SW5 closes geometrically if either option closes every predicate. R2 does not choose between them.
- **Boss growth** inside a reserved region is non-conductive (dielectric sector material or dielectric insert);
  conductive boss growth there is new metal and fails R2-H15. Outside every reserved region the boss may be midcase
  metal. Existing frozen midcase metal is not "new".
- **G5 records (6.9):** the SW1 pusher, boot / O-ring and boss growth inside BLE_RAD and the BLE reserved region, and
  the SW5 pusher, boot / O-ring and boss growth inside WIFI_RAD and the Wi-Fi reserved region.

#### 7.4.3 Report

Each SW x topology row shows, **in the same row**:

- the boss limit 3.000 mm, the boss used, and the zero-margin boss required;
- I-SUM and I-MAX margins;
- strain and stroke margins;
- the material rule;
- the R1 column.

A topology failure that has no boss / D cause, for some switch, raises R2-S12. A closure needing a boss > 3.0 mm raises
R2-S03.

### 7.5 L-LRA — actuator

#### 7.5.1 B.Cu primary

- Pose search in zone B for every class: authored G4 classes at their maxima plus `lra_supplied` with lead / exit
  envelopes. Run it per battery and per offset.
- Plan inside the binding MAIN outline column: the G4 maximum MAIN outline at the evaluated point. Report the Ø46
  development-envelope column beside it. Any growth beyond Ø46 is reported as a K1 constraint and is never placed in
  a reserved region.
- Z inside zone B. Strictly clear of every R2-H22 occupant.
- Leads to U7 on B.Cu.
- Outside radiator volumes, reserved regions, MAG_CLEAR, button bores and supports.

#### 7.5.2 F.Cu fallback

- Evaluated always; selected only if no B.Cu pose exists.
- Under the display only. Clear of pinned F.Cu courtyards, the U101 shield polygon and can volume, and MAG_CLEAR.
- Z-neutral: seated height including `lra_mount_mm` adverse must be <= 2.70 mm at linear worst, so the front gap is
  unchanged.
- C-R1-08 applies:
  - PASS only with a supplied class;
  - an authored plan footprint whose height is capped by the threshold is SUPPLIER_GATED (SR-LRA threshold), never
    PASS.

#### 7.5.3 Identity, BMM350 and stop

- R1:R4-1 identity binding. The canonical physical identity of the selected pose is:
  - battery and offset vector;
  - side, class, evidence and envelope (body + lead / exit);
  - pose (az, r, orientation);
  - MAIN outline column used, the zone-B or front-gap Z fit, and the mount allowance;
  - the plan exclusion set with its clearances;
  - the U7 lead path;
  - the BMM350 distance.

  The validator reconstructs the identity independently from the emitted pose and authoritative inputs and re-runs the
  predicates.
- BMM350 (U703): minimum 3-D distance from the LRA envelope to the U703 package, for the selected pose and for every
  reported pose window. OD-G4-LRA-MAG is decided (authorized, section 17.1); it does not lift the MAG_CLEAR exclusion
  (G4 8.9, G4-H18). Magnetometer calibration is a later firmware / test item, not an R2 check.
- Neither a B.Cu pose nor a plan-feasible F.Cu pose raises R2-S04.

### 7.6 L-RAD — radial and crossings

#### 7.6.1 Crossings

XF-J1501, XB-J201, XC-J202 and XL-LRA each end in one of two states:

- **ELIMINATED:** only with an explicit geometric proof that the conductor path, from origin to MAIN termination,
  stays entirely on the B.Cu side and never passes the MAIN edge between the F.Cu and B.Cu planes.
- **CLOSED:** with a linear-worst margin.

No crossing check is deleted without that proof.

#### 7.6.2 Other radial terms

- Straight-run margins of every annulus riser: sensor FPC, battery tail, drop.
- C-R1-04 local arcs only where an R2 corridor needs one (floor rule unchanged).
- Dielectric-sector walls.
- MAIN-to-case clearance, including any MAIN-outline growth.
- Insertion.

#### 7.6.3 Separation and D margin

H05-GEOM (R2-H04) and H05-LRA-COUPLED (R2-H05) stay separate. The D margin is always `51.00 - D_eval` at the joint
design point, **never** from `D_radial_core`.

### 7.7 L-ASM — assembly

#### 7.7.1 Sequence rules

A1-A11 identities and directions are retained (LA-ASM-1 analogue). Content may change only where a 2026-10-17 decision
causes it, and each change cites its decision id. Allowed changes:

- A1: cup sub-assembly with window, FT-C and O-ring fitted;
- A4: module stack with B.Cu mating of J1501 / J201 / J202 and the LRA on MAIN;
- A5: LRA bonded on MAIN B.Cu or F.Cu, before the module stack;
- A6: rear insertion with the offset pack and B.Cu items;
- A9: T1 / T2 pushers;
- A10: functional test through the caseback contacts, with the drop mated and the caseback in its service position;
- A11: cup closure in +Z with the radial O-ring and lug-root screws.

Sub-steps (A4a …) are allowed. Every other step is unchanged.

#### 7.7.2 Checks

- an access direction per operation, including mate strokes;
- a collision-free rear-insertion path;
- battery isolation state before every manipulation;
- J1 cycles (50 rated / 25 planned);
- service: caseback removal with drop and FPC slack, and REAR + tail replacement through rear access to J1501;
- SERVICE-COVER-REBOND remains OPEN.

Product closure is executable only if every A-step dependency is resolved (R1:R2-5).

### 7.8 L-WIN — window (unchanged)

W1 at 0.50 mm, bonded into the cup's pod frame, Z delta 0.000. R1 W1 values are reproduced from the pinned R1 JSON,
never re-typed. SUPPLIER_GATED (SR-WINDOW, MG-WINDOW-XTALK). No qualification claim.

## 8. Search space (deterministic; no Cartesian explosion)

Lanes are evaluated per shared point and combined by intersection. The joint design point is one tuple per battery.
The tuple holds:

- D and bulk wall;
- offset and carrier;
- connector poses and mates;
- cup and seal row;
- charger pose;
- button rows;
- LRA pose.

Joint-point ranking, lexicographic:

1. no stop or physical failure;
2. fewer OWNER_GATED, then fewer SUPPLIER_GATED lanes;
3. smaller D (OD-G4-ENVELOPE minimization);
4. larger minimum linear-worst margin per units group (never across units);
5. lower `sigma_allow_req`;
6. larger BMM350 distance;
7. assembly simplicity.

Ids break exact ties only.

Exact reductions (dominance / monotonicity) are allowed only when documented and verified against production predicates
(R1 model-decision style).

Budget: <= 3,000,000 predicate evaluations. `check` <= 150 s on the quiet development host, including the in-process G4
reproduction; the loaded-host time is also reported. `selftest` <= 1,200 s. Each generated file <= 2 MB.

| ID | Variable | Range / grid | Source | Evidence class | Hard stop | Gate |
|---|---|---|---|---|---|---|
| R2-V01 | battery | LPR433736 (primary), LPR403736 (reported) | OD-BATTERY | OWNER_DECISION (catalogue) | evidence contradicts 6.2 | SR-BATT-PACK |
| R2-V02 | D_case_body | 48.00-51.00 step 0.05; report-only to 52.50 | OD-G4-ENVELOPE | OWNER REQUIREMENT | > 51.00 | owner |
| R2-V03 | bulk wall tw | 0.8-1.6 step 0.1 | R1 V02 | DESIGN + MFG_TOL | < floor | supplier |
| R2-V04 | local arcs | only where an R2 corridor needs one; floor .. tw step 0.02 | C-R1-04 | DESIGN + MFG_TOL | below floor | supplier / FEA |
| R2-V05 | battery offset | magnitude 0.00-1.50 step 0.25; direction 0-345 step 15 | OD-G4-LRA-ARCH | OWNER_DECISION range | > 1.50 | — |
| R2-V06 | carrier inner radius / wall | from R_pack(lw) + g_radial(adverse), +0.50 step 0.05; t_cw 0.30-0.60 step 0.05 | G4 V23 rule | DESIGN + MFG_TOL | pack or lobe outside; t_cw < 0.30 adverse | SR-BATT-PACK / -GROWTH |
| R2-V07 | PCM lobe | authored envelope x az 220-240 step 5; admissibility 0-355 step 5 | G2 `pcm_az_deg`; R2 inputs | PROVISIONAL_ASSUMPTION | outside carrier / allocation | SR-BATT-PACK / -PCM |
| R2-V08 | J1501 pose | B.Cu, az step 1, r step 0.25; mate axial toward REAR (fixed) | 6.5 lead design rule (OD-CONN-SIDE for side) | DESIGN; G2 stack ranges SUPPLIER_GATED | zone / allocation | SR-FPC-MECH |
| R2-V09 | J201 pose / mate | B.Cu zone B near PCM exit; mate axial / radial / tangential | OD-CONN-SIDE | DESIGN | — | SR-BATT-PCM |
| R2-V10 | J202 pose / mate | B.Cu east sector, az step 1, r step 0.25; mate axial / radial / tangential | OD-J202 | DESIGN | WIFI_RAD / reserved / MAG_CLEAR | SR-CHG-MECH |
| R2-V11 | sensor FPC route / bend / slack | path family per J1501 pose; R_bend_min 0.6-2.0 adverse 2.0 | G2 | SUPPLIER_GATED | bend < adverse; unallocated slack | SR-FPC-MECH |
| R2-V12 | local charger drop | footprint and Z band per J202 pose | OD-J202 | DESIGN (harness SUPPLIER_GATED) | intrusion | SR-CHG-MECH |
| R2-V13 | cup: t_in / ring / wall width and height / fillet | t_in R1 V12 (<= pod residual); ring, wall and fillet grids authored in R2 inputs, step <= 0.1 mm | Q-R1-STRUCTURE | DESIGN + MFG_TOL (PC-CERAMIC-GRIND) | Z / allocation; < 0.8 + tol | SR-CASEBACK-CERAMIC |
| R2-V14 | ribs | R1 V13 / V14 (no circumferential-rib credit) | R1 | DESIGN | forbidden zone | FEA |
| R2-V15 | main-seal cs | 0.5-2.0 step 0.1 authorized; diagnostic to 2.5 | R1 V11 extended (larger cs is a design choice; windows unchanged) | PROVISIONAL, tol +/-0.05 | window / fill | gland / O-ring |
| R2-V16 | screws | 3-4 at lug roots; clearance holes in ceramic; SCR-M1.0-TAPPED in metal | G4 | PROVISIONAL | inside seal line unsealed | OD-G4-STRAP |
| R2-V17 | button topology | T1, T2-F, T2-R | Q-R1-BUTTON-ENVELOPE | DESIGN | none closes | SR-BUTTONS |
| R2-V18 | pusher d_p | 2.0 .. largest value whose boss fits the frozen window at the evaluated D, step 0.2 | R1 V06 + computed limit | DESIGN | boss leaves window | SR-BUTTONS |
| R2-V19 | boss extension | 0.00-3.00 step 0.05, incl. seal / boot and tolerance | Q-R1-BUTTON-ENVELOPE | DESIGN | > 3.00 | owner |
| R2-V20 | T1 cs | 0.5-3.0 step 0.1, dynamic radial window | G4 `oring` | PROVISIONAL, tol +/-0.05 | window / fill / core | gland / O-ring |
| R2-V21 | rim land, strain, guide stack | R1 V07-V09 unchanged | R1 | PROVISIONAL / SUPPLIER_GATED | — | SR-BUTTONS |
| R2-V22 | charger pose / land / FT | R1 V19-V21; FT-C binding, FT-A reference | R1, C-R2-01 | PROVISIONAL | caps / clearances | SR-CHG-MECH |
| R2-V23 | LRA class / side / pose | G4 classes at max + `lra_supplied`; B.Cu primary, F.Cu fallback; az 0-355 step 5, r step 0.25, ori 0 / 90 | G4 8.9, C-R1-08 | PROVISIONAL / SUPPLIER | — | SR-LRA |
| R2-V24 | MAIN outline column | Ø46 development envelope (reported); G4 maximum MAIN outline at the point (binding) | G4 4.1 A | PROJECT_DERIVED | growth into a reserved region | K1 |
| R2-V25 | window | W1, 0.50 mm | OD-G4-WINDOW | PROVISIONAL | — | SR-WINDOW |
| R2-V26 | cover / land regression | R1 V25 | R1 | DESIGN | regression | — |
| R2-V27 | C-R1-03 | I-SUM binding; I-MAX reported | Q-R1-BUTTON-ENVELOPE | owner | — | — |

## 9. Hard checks (R2)

Every check reports LEGACY, NOMINAL, RSS, LINEAR WORST, GOVERNING TERMS and OWNER-GATED evaluations where applicable
(`G4_BRIEF.md` 6.3). It also reports the committed R1 value of the corresponding R1 check as a column, read from the
pinned R1 JSON. Each check reports per battery.

| ID | Check | Evaluation | Revision vs R1 |
|---|---|---|---|
| R2-H01 | G2-REVA / G2-REVA-HI reproduced under the overlay; **total Z delta exactly 0.000** at nominal, RSS and linear; every R2 feature fits its Z allocation (zone A, zone B, battery-band annulus, REAR band + Delta, drop band) | exact / linear worst | R1-H01 + Delta overlay, band retirement, zones |
| R2-H02 | `D_eval` <= 51.00 with margin `51.00 - D_eval` (joint point, never `D_radial_core`); only the five bosses protrude, each <= +3.0 incl. seal / boot and tolerance, inside its existing window | linear worst | R1-H02: +1.0 → +3.0; D-margin source |
| R2-H03 | LEGACY numbers, G4-literal and R1-literal anchor values reproduced exactly with the overlay off (pinned JSON pointers, never re-typed); every re-implemented function passes its equivalence test | exact | R1-H03 + R1 anchors + rule 4.2-4 |
| R2-H04 | **H05-GEOM**: XF / XB / XC eliminated by proof or closed; straight runs of every annulus riser; wall side, wall dielectric, main-case, insertion | linear worst | R1-H04: new crossing set; elimination needs proof |
| R2-H05 | **H05-LRA-COUPLED**: LRA → U7 lead path on B.Cu (XL eliminated by proof or closed); L-LRA only | linear worst | R1-H05: REAR-level Z term replaced by zone-B fit |
| R2-H06 | cover / bezel / land regression (G4 H06-H09) | linear worst | unchanged |
| R2-H07 | W1 at 0.45 mm min: stress / deflection screens, rib fit, bond land, no rib-to-optics load | G1 conservative | unchanged |
| R2-H08 | Pressure partition sums (G4 1168.99 N at 0.625 MPa reproduced). **Zero load** into battery, REAR PCB, G3 support lands, carrier lower web and pillars. **Static (zero-load) clearance > 0.050 mm** (strict) from every cup / plate / ring / rib / charger / LRA feature to every forbidden item. | exact / linear worst | R1-H08 + single-event rule 10.5 |
| R2-H09 | (a) **deflection <= 0.050 mm (hard physical)**; (b) stress vs 150 MPa: PASS / SUPPLIER_GATED + `sigma_allow_req`; (c) periphery and inner shortfalls reported | linear worst | R1-H09 split; stress never a model FAIL |
| R2-H10 | Cup-rim bearing on the midcase rear face; screw shear / pull-out; ceramic bearing and edge-distance thresholds at clearance holes with supplier zero-margin | linear worst | R1-H10 → cup |
| R2-H11 | Radial cup O-ring: compression / fill at +/-0.05 mm in the static radial window; spigot inside its REAR-band + zone-B allocation; serviceable; R1:R5 population and unit invariance | linear worst / exact | R1-H11: topology fixed by owner; adhesive not an option |
| R2-H12 | Buttons per SW: T1 / T2-F / T2-R under I-SUM (binding) and I-MAX (reported); boss threshold 3.000 beside the result; stroke, rim, strain, material rules; switches unmoved | linear worst | R1-H12: +3.0 bosses; T1 re-admitted; T3 not carried; no I-MAX-only closure |
| R2-H13 | Every aperture has exactly one primary seal with a feasible geometry class; seal path closed | exact | unchanged (+ cup) |
| R2-H14 | Charger: block inside the wedge and outside WIFI_RAD; land per C-R1-01 with C-R2-01; caps; drop to J202 B.Cu strictly 3-D clear; FT-C sealed; physical headline (P-2) | linear worst | R1-H14 → C-R2-01, drop, retired routes |
| R2-H15 | Radiator volumes (G4-H17), owner reserved regions (6.9, decided rule) and MAG_CLEAR (G4-H18): no new metal, conductor or component (pack, LRA, harness / FPC / drop, connectors, screws, metal pushers, conductive boss growth, MAIN growth); every non-conductive item inside a reserved region carries its G5 record (material, permittivity class, volume) | exact | R1-H15 + new items + reserved regions + G5 record |
| R2-H16 | G3 not reopened (section 4.3, items 1-7) | exact / linear worst | R1-H16 made explicit; pillars +Delta only |
| R2-H17 | Assembly (7.7): sequence executable, access per operation incl. mate strokes, collision-free insertion, isolation states, service paths | linear worst | R1-H17 → R2 sequence |
| R2-H18 | >= 4 case / caseback supports incl. W/NW, all outside the offset pack envelope | exact | R1-H18 + offset |
| R2-H19 | LRA lane: B.Cu pose, or F.Cu Z-neutral fallback per C-R1-08; R1:R4-1 identity reconstruction; BMM350 distance reported | linear worst | R1-H19 → MAIN B.Cu / F.Cu |
| R2-H20 | No KiCad / interface / placement / immutable-file change; changes confined to `R2_FILES`; historical reproduction of 4.4 | exact | R1-H20 + R1 record |
| R2-H21 | OD-THICK-REVA: nominal <= 16.5 and RSS <= 17.0 on both baselines (values unchanged) | nominal, RSS | new (G4 H02) |
| R2-H22 | Joint annulus allocation (6.8): strict 3-D clearance for every pair separated by design; containment / interference for declared contact pairs (6.8 rule 2); no double-credited volume; ledger emitted | linear worst | new |
| R2-H23 | Pack + growth + PCM lobe inside the carrier, each battery and offset; carrier wall >= 0.30 adverse; pillars only +Delta | linear worst | new (G4 H10 extended) |
| R2-H24 | MAIN B.Cu zones (6.4): zone-A heights <= accepted back-zone governing height; zone-B items inside their 3-D allocation | linear worst | new |
| R2-H25 | Interconnects (6.5): J1501 axial mate toward REAR; J201 / J202 mates; FPC length, bends, `R_bend`, allocated slack; drop service length | linear worst | new |
| R2-H26 | Frozen 24-position / 13-net interface unchanged; charger-positive outside the sensor FPC; mirrored physical order recorded as a K1 requirement | exact | new |
| R2-H27 | Battery evidence: catalogue labels present; no recorded SR-BATT-PACK evidence contradicts 6.2 | exact | new |
| R2-H28 | Shield-ready preserved: U101 shield polygon and can volume not intruded; front gap unchanged | exact | new |

## 10. Evidence, single-event and presentation rules

### 10.1 Evidence classes

Each value carries exactly one `G4_BRIEF.md` 6.1 evidence class. Catalogue values use OWNER_DECISION with
`catalogue_value: true` and gate SR-BATT-PACK; they are never MANUFACTURER_VERIFIED. No supplier, manufacturer,
material (including zirconia strength), RF or MPN value is invented.

### 10.2 Governing terms

Each failing or gated check lists its governing terms, with role and the supplier zero-margin value.

### 10.3 Dispositions

Each lane ends in exactly one disposition:

- `RESOLVED_GEOMETRICALLY` (margins);
- `SUPPLIER_GATED` (numeric threshold);
- `OWNER_GATED` (named question, section 17.1);
- `BLOCKED` (named stop).

### 10.4 No credit

Nothing closes on any of the following:

- a `G4_BRIEF.md` 6.3 credit;
- a widened window or narrowed tolerance;
- a clamped cup edge;
- thinner-cell tolerance or growth;
- catalogue-as-verified;
- I-MAX alone;
- a class defined by its threshold;
- Delta tolerance.

A margin that closes only that way raises R2-S11.

### 10.5 Single-event rule (R2-H08 / R2-H09)

One physical event is charged to exactly one check.

- **R2-H09a** owns pressure deflection: `w_max(p_max)` > 0.050 mm.
- **R2-H08** owns load-path topology (partition, forbidden branches) and **static** geometry. Static clearance to each
  forbidden item must be > 0.050 mm, so the full deflection allowance fits.

When R2-H09a and R2-H08 both pass, deflected contact is impossible. A deflection exceedance appears in R2-H08 only as a
cross-reference to R2-H09a, with no margin of its own, and is never counted twice in tallies, dispositions or stops.

### 10.6 Carried R1 rules

- strict clearance (R1:R3-3);
- per-point evaluation (R1:R2-1);
- validator recomputation of every numeric threshold (R1:R3-6);
- strict whole-design compliance kept apart from study / gated states (R1:R3-7);
- typed units (R1:R4-8);
- the input schema guard (no result-like keys in inputs).

### 10.7 Presentation fixes in R2 outputs (R1 files are not edited)

- **P-1 Conductor-band dependence.** Every result whose margin depends on the REAR-level band states `band: retired /
  retained (drop footprint) / not applicable`. It shows the margin with the band (R1-literal state) and without it.
- **P-2 Charger in physical terms** (7.3.3).
- **P-3 Lead cross-checks.** Every lead number of this brief (section 20) is either `REPRODUCED` or `EXPLAINED`, never
  silently adopted.
- **P-4 Commit-state neutrality.** The R2 status text never states commit or review state. The R1 debt of 2.3 is listed
  under "known documentation debt".

## 11. Stop conditions

| ID | Stop | Scope |
|---|---|---|
| R2-S01 | Any G3 change (R2-H16 false) | whole run |
| R2-S02 | Nonzero total Z (nominal, RSS or linear, either baseline) or an OD-THICK-REVA failure | whole run |
| R2-S03 | No joint point with `D_eval` <= 51.00, or a closure needing a boss > +3.0 mm or a protrusion outside the five windows | whole design (lanes completed) |
| R2-S04 | No LRA pose on MAIN B.Cu and no plan-feasible Z-neutral F.Cu fallback pose | lane |
| R2-S05 | Deflection > 0.050 mm or forbidden contact at every admissible cup configuration | lane |
| R2-S06 | Charger fails under C-R2-01 (no pose closes the complete physical predicate set) | lane |
| R2-S07 | Main seal does not close (no radial cup row passes all typed predicates in its allocation), or the seal path is open | lane |
| R2-S08 | Annulus over-allocated (no allocation without double credit / with strict clearance) | whole design (lanes completed) |
| R2-S09 | Recorded SR-BATT-PACK evidence contradicts the 6.2 assumed envelope | whole run (owner STOP) |
| R2-S10 | Any need to touch KiCad / interfaces / placement; a KiCad, interface or immutable file differs; a pin mismatches; historical reproduction fails | whole run |
| R2-S11 | A margin closes only with a speculative credit (10.4) | whole run |
| R2-S12 | Some switch has no admitted topology closing inside its frozen window for a non-boss reason | lane |
| R2-S13 | Live repository disagrees with this brief, precondition E-1 fails, an input contradicts a pinned source, or a battery switch / decision is entered without the required evidence | whole run |
| R2-S14 | Pack + growth + PCM lobe cannot be contained in the carrier at any admissible offset | lane (L-PKG) |

- **Whole-run stops** record the triggering quantities and end the evaluation.
- **Lane and whole-design stops** let every other lane complete and report thresholds.

A closure that needs an unrecorded owner decision is **not** a stop. It makes the lane OWNER_GATED with a named
question (section 17.1).

## 12. Verdict vocabulary and what each verdict authorizes

The rule is applied per battery. The **package verdict is the LPR433736 verdict**. The LPR403736 verdict is reported
and never switches the battery (7.1.6).

1. **G4-R2 BLOCKED**: any stop of section 11. All non-halted lanes are reported with deficits.
   - Authorizes nothing.
   - Next step: an owner / lead decision on the named stop.
2. **G4-R2 PARTIAL — OWNER QUESTIONS**: no stop, and at least one lane is OWNER_GATED.
   - Authorizes owner questions with numeric thresholds and nothing else.
   - G5 entry waits for the answers or an explicit owner decision.
3. **G4-R2 PACKAGE CLOSED — SUPPLIER GATES OPEN**: no stop, no OWNER_GATED lane, and at least one SUPPLIER_GATED lane.
   Each gate carries a numeric threshold, for example `sigma_allow_req` vs SR-CASEBACK-CERAMIC, the F.Cu LRA class,
   SR-BATT-PACK and SR-WINDOW.
   - After independent review PASS, the manual commit gate and an owner record, the package becomes eligible for
     **G5 entry and outline planning** (MAIN outline constraint, case envelope) under their own contracts.
4. **G4-R2 PACKAGE CLOSED**: every lane RESOLVED_GEOMETRICALLY and every hard check PASS. Same eligibility as 3.

No R2 verdict authorizes KiCad, K1 or K1-A work, MPN selection, supplier-request issuance or qualification. R2 never
emits a G4 verdict; G4 status changes only by a later lead record.

## 13. Forbidden actions

- KiCad edits of any kind.
- MPN selection.
- Supplier credits, supplier claims or supplier-request issuance.
- RF-performance claims, or 5 ATM / structural / optical / adhesive qualification claims.
- Any G5, K1 or K1-A work.
- Editing or regenerating any accepted G1-G4 or R1 artifact, including `G4_R1_BRIEF.md` (C-R2-01 lives here only).
- Moving a button azimuth, switch or window.
- Switching the battery by model logic.
- Changing or reinterpreting an owner decision beyond section 3.3.
- Inventing supplier, material or catalogue data.
- Editing `input_register.json`, `architecture.*` or `README.md`.
- Committing, pushing, stashing, resetting or cleaning by the implementer.
- Merging K1-A work.

## 14. Deterministic implementation requirements (for the builder)

1. **Files and paths.** Exactly `R2_FILES` (4.6). Scratch only outside the repository. Always run Python with `-B`, so
   no `__pycache__` appears (a stray untracked file turns scope checks red).
2. **CLI.** `g4_r2_closure.py build|check|selftest`.
   - `build` writes the generated files.
   - `check` regenerates in memory and fails on any of:
     - a byte difference, a pin or overlay pinned-value mismatch, or a schema-guard hit;
     - an R2-H03 anchor mismatch;
     - an in-process G4 reproduction that is not byte-identical or not 32/32;
     - an `ALLOWED_CHANGES` extension other than exactly `R1_FILES ∪ R2_FILES`;
     - a nonzero Z delta, or `D_eval` > 51.00;
     - a boss > 3.0;
     - a disposition resting on a credit;
     - a missing battery column, a missing I-MAX column or a missing R1 column;
     - an identity reconstruction mismatch;
     - a non-conductive reserved-region item without its complete G5 record (6.9);
     - a changed immutable file;
     - a budget overrun.
3. **Determinism.** Sorted keys, compact separators `(",", ":")`, fixed float rounding (R1 `rounded` convention, 9
   decimals), no timestamps, final newline. Two consecutive `build` runs give identical SHA-256 for every output.
   `check` passes under `PYTHONHASHSEED=0` and `PYTHONHASHSEED=4242`.
4. **Inputs.** Inputs carry no results. Pins in `source_sha256` cover:
   - every G1-R1 input and generated file read;
   - the three mechanical briefs G4_BRIEF.md, G4_R1_BRIEF.md, G4_R2_BRIEF.md, plus any G1–G3 brief the tool reads;
   - the `architecture.json` projection (R1 method).

   `r2_contract_commit` is pinned. `open_question_answers` carries the section 17.1 owner answers verbatim (date
   2026-10-17, source: owner decision, `G4_R2_BRIEF.md` section 17.1). `lra_supplied`, `supplier_evidence` and
   `fallback_trigger` carry their schemas and are empty / `null` until a reviewed input change fills them with
   primary-document provenance.
5. **R1:R5 rules** (7.2.2) for every seal row. Unit regression mm / m / um must give identical emitted results.
6. **R1:R4-1 identity** (7.5.3), reconstructed by the validator.
7. **Overlay-off equivalence** (4.2-4) for every wrapped or re-implemented library function.
8. **Self-test classes (R1 taxonomy):** PIF production input fault, PGF production geometry fault, PA solver / positive
   anchor, VS validator semantic, SR serialization. A fault that lives only in the result object is never counted as an
   injection.

   **Minimum injected faults** (each must be caught):

   Z, battery and offset
   - Delta not reallocated, reallocated twice, or given a tolerance;
   - a catalogue value changed without a pin change;
   - the overlay not applied — stack_parameters D_pack_nom 44.0 / t_pack_nom 4.5 used as live pack constants;
   - fallback battery selected without evidence + decision;
   - offset 1.55.

   Pack, carrier and zones
   - pack + growth outside the carrier;
   - PCM lobe into SW3 / support;
   - zone-A item above the back-zone ceiling.

   Annulus
   - LRA / spigot 3-D overlap;
   - zero-gap touching counted as clear;
   - J1501 mate stroke blocked at its step;
   - slack doubled in unallocated annulus;
   - one annulus volume credited to two items (e.g. the cup's spigot and ring sub-volumes).

   Structure
   - stress > 150 labelled FAIL;
   - stress > 150 labelled PASS;
   - deflection 0.051;
   - static clearance 0.050 to a forbidden item;
   - one event counted in R2-H08 and R2-H09;
   - cup edge credited as clamped.

   Seal
   - widened O-ring window; narrowed cs tolerance;
   - representative-row feedback (first / last / poison);
   - unit change altering a result;
   - adhesive main seal selected.

   Buttons
   - T1 with the static window;
   - I-MAX-only closure;
   - boss 3.01;
   - boss outside its window;
   - switch azimuth moved;
   - SW1 or SW5 metal pusher selected or credited;
   - PEEK-class property credited without supplier data;
   - conductive boss growth inside a reserved region credited;
   - T3 selected.

   Reserved regions
   - new conductor or component inside a reserved region credited;
   - non-conductive item without its G5 record (material, permittivity class, volume);
   - numeric permittivity emitted without a primary document.

   Charger
   - old plan-AND-Z 2(v) applied;
   - retired CHG_ROUTE credited / still enforced;
   - drop inside MAG_CLEAR or the Wi-Fi region;
   - block size reduced.

   LRA
   - LRA in MAG_CLEAR;
   - F.Cu LRA 2.71 counted Z-neutral;
   - threshold-defined class counted PASS;
   - identity forgery;
   - MAIN growth into a reserved region.

   Radial
   - a crossing marked ELIMINATED without proof;
   - `D_radial_core` used as the D margin;
   - D 51.01.

   G3
   - REAR XY +0.001;
   - REAR Z shift;
   - support land enlarged;
   - pillar footprint beyond its land;
   - mirrored REAR transform.

   Governance
   - historical G4 / R1 file byte-flip;
   - KiCad file touched;
   - 24 / 13 interface changed;
   - commit-state text in R2 status;
   - an `ALLOWED_CHANGES` wildcard.

9. **Budgets.** Section 8. Evaluations and runtimes are emitted in the JSON and report.
10. **Lead cross-checks.** Section 20 values are emitted as `REPRODUCED` or `EXPLAINED` (P-3).

## 15. Validation

All commands exit 0 except where marked. `<scratch>` lies outside the repository.

```
git branch --show-current                      # mechanical/g4-r2-package-closure
git rev-parse HEAD                             # R2 contract commit (parent 27f7a3a0570bb79c27df530cd5d99c7ea7597f9f)
git status --short --branch                    # entry: clean (E-1)
python3 -B design/mechanical/tools/mech_model.py check
python3 -B design/mechanical/tools/g1_scenarios.py check
python3 -B design/mechanical/tools/g2_interconnect.py check
python3 -B design/mechanical/tools/g3_rear_optical.py check     # clean-tree protocol (4.4)
python3 -B design/mechanical/tools/arch_diagrams.py check       # clean-tree protocol (4.4)
git worktree add --detach <scratch>/g4_baseline 00e77cbe107a79ac05194f19b674f7ab8d5941c9
( cd <scratch>/g4_baseline && python3 -B design/mechanical/tools/g4_case_sealing.py check \
  && python3 -B design/mechanical/tools/g4_case_sealing.py selftest )             # 32/32
git worktree remove <scratch>/g4_baseline
git worktree add --detach <scratch>/r1_baseline 27f7a3a0570bb79c27df530cd5d99c7ea7597f9f
( cd <scratch>/r1_baseline && python3 -B design/mechanical/tools/g4_r1_blockers.py check \
  && python3 -B design/mechanical/tools/g4_r1_blockers.py selftest )              # all caught; quiet host (4.4)
git worktree remove <scratch>/r1_baseline
python3 -B design/mechanical/tools/g4_case_sealing.py check     # EXPECTED RED (scope); recorded only
python3 -B design/mechanical/tools/g4_r1_blockers.py check      # EXPECTED RED (scope); recorded only
python3 -B design/mechanical/tools/g4_r2_closure.py build
sha256sum design/mechanical/generated/g4_r2_*
python3 -B design/mechanical/tools/g4_r2_closure.py build
sha256sum design/mechanical/generated/g4_r2_*                   # identical to the previous listing
PYTHONHASHSEED=0 python3 -B design/mechanical/tools/g4_r2_closure.py check
PYTHONHASHSEED=4242 python3 -B design/mechanical/tools/g4_r2_closure.py check
python3 -B design/mechanical/tools/g4_r2_closure.py selftest
git diff --exit-code 27f7a3a0570bb79c27df530cd5d99c7ea7597f9f -- . ':(exclude)design/mechanical/G4_R2_BRIEF.md'
git diff --exit-code <R2 contract commit> -- design/mechanical/G4_R2_BRIEF.md
git diff --exit-code 00e77cbe107a79ac05194f19b674f7ab8d5941c9 -- '*.kicad_pcb' '*.kicad_sch' '*.kicad_pro' \
  '*.kicad_prl' design/interfaces design/placement rear_sensor libraries
git ls-files --others --exclude-standard        # every untracked path is in R2_FILES; every R2_FILES path (except the tracked brief) exists
git diff --check
```

The implementer records every command, exit code, runtime and selftest category count in the run report. A red
literal G4 / R1 check is acceptable only as documented in 4.4. Any other red result is a failure of R2.

## 16. Supplier evidence

None of these blocks the study run. Each enters as a planning range with a numeric threshold, unless the "Study
status" column says otherwise.

| Evidence | R2 needs | R2 reports | Study status |
|---|---|---|---|
| SR-BATT-PACK (with SR-BATT-PCM, SR-BATT-GROWTH) | finished-pack drawing: Ø, thickness incl. tape / PCM fold, PCM lobe, exit / tabs, permitted growth | 6.2 envelope margins; admissible PCM window and lobe threshold | **Non-blocking** to run (catalogue + planning). **STOP trigger** (R2-S09) if recorded and contradicting. Blocking for K1. |
| SR-CASEBACK-CERAMIC | qualified zirconia-class allowable for the cup geometry and process | `sigma_allow_req` per battery | **Non-blocking** (stress > 150 → SUPPLIER_GATED). **Blocking for any LPR403736 switch** (with an owner decision). |
| gland / O-ring (G4 / R1 "supplier gasket" gate; no SR id exists) | cs tolerance class, compression set, material vs the planning windows (static radial; dynamic for T1) | zero-margin cs and gland values | non-blocking |
| SR-CHG-MECH | block, land, FT-C, drop / harness envelope | strict-wedge land width, block height allocation, drop envelope | non-blocking |
| SR-LRA | class envelopes incl. lead / exit, mount, magnet data | B.Cu pose window; F.Cu height / footprint threshold | Non-blocking for B.Cu with authored classes. **Blocking for crediting the F.Cu fallback** (PASS needs a supplied class, C-R1-08). |
| SR-FPC-MECH | J1501 B.Cu axial mate: mated height, stiffener, mouth, `R_bend_min`, exit; tail process | zero-margin `R_bend`, `h_stack` and length | non-blocking |
| SR-BUTTONS | right-angle side-actuated switch, pusher, stem O-ring / boot data, stroke / force; SW1 and SW5 non-metallic pusher material data (zirconia or PEEK class); dielectric boss-growth material data | boss, bore, cs and strain thresholds | non-blocking |
| SR-WINDOW / SR-COVER-LENS / SR-DISPLAY-LAND (carried) | as R1 | as R1 | non-blocking |

## 17. Open questions and interpretations

### 17.1 Owner answers and remaining open questions

#### 17.1.1 DECIDED — owner answers of 2026-10-17 (verbatim)

Record both rounds verbatim (date 2026-10-17, source: owner decision, `G4_R2_BRIEF.md` section 17.1, with the round
and the `status` of the table below) in `inputs/g4_r2_closure.json.open_question_answers` and
`generated/g4_r2_closure.json.owner_decisions`. A SUPERSEDED text is recorded for history and is never applied.
Sections 2.1, 3.3, 3.4, 4.5, 5, 6.9, 7.4.2, 7.5.3, 9, 14, 16, 17.2, 18, 19, 20 and 21.3 apply them.

First round:

```text
- Q-R2-SW5-PUSHER: SW5 uses a non-metallic pusher (zirconia or PEEK
  class); SW1–SW4 stay metal. SW5 position unchanged.
- Q-R2-RESERVED-REGION: in the reserved GNSS/BLE/Wi-Fi regions, new
  metal, conductors and components are forbidden. Non-conductive
  structure (ceramic cup ring, dielectric pusher, boss growth) is
  allowed but must be recorded with material, permittivity class and
  volume as a G5 input.
- Q-R2-SHIELD-REF: "§20" means the master handoff's shield-ready policy,
  not a repo file; your architecture.md section A reading is accepted.
- Q-R2-K1A: confirmed. K1-A keeps G3-B-S14 REAR placement unchanged and
  is MAIN schematic-only; it moves nothing G4-R2 relies on.
- OD-G4-LRA-MAG: authorized. Report LRA-to-BMM350 distance; magnetometer
  calibration is a later firmware/test item.
- E-1: the rear_sensor .kicad_pro change was KiCad auto-save and has
  been reverted by the owner; keep E-1 as a precondition check.
```

Second round (answers to the independent-review questions OQ-1 to OQ-3):

```text
- Q-R2-SW1-BLE (OQ-1): SW1 uses a non-metallic pusher (zirconia or PEEK
  class), same rule as SW5. SW2, SW3, SW4 keep metal pushers. SW1 window
  and position unchanged. The F-03 lead note is therefore replaced: SW1
  is evaluated like SW5 and is not pre-ordained to R2-S12.
- Q-R2-BOSS-MATERIAL (OQ-2): boss growth inside a reserved region must be
  non-conductive (dielectric sector material or dielectric insert) and is
  recorded as a G5 input. Conductive boss growth inside a reserved region
  is new metal and fails R2-H15. Existing frozen midcase metal is not
  "new".
- Q-R2-K1A correction (OQ-3): the earlier answer "MAIN schematic-only" was
  wrong. Correct scope: K1-A = REAR layout/routing with all G3-B-S14 part
  positions frozen, plus MAIN power-schematic fixes; no MAIN outline,
  placement or routing. It moves nothing G4-R2 relies on.
```

| Item | Status | Where applied |
|---|---|---|
| Q-R2-SW5-PUSHER | DECIDED; SW5 is no longer OWNER_GATED. Its "SW1–SW4 stay metal" is superseded for SW1 by Q-R2-SW1-BLE | 3.3, 7.4.2, 14, 16, 17.2 item 22, 21.3 |
| Q-R2-RESERVED-REGION | DECIDED; replaces the former readings (a) / (b) | 3.3, 6.9, 7.4.2, 9 (R2-H15), 14, 17.2 items 15 / 23 / 24, 18, 19, 21.3 |
| Q-R2-SHIELD-REF | DECIDED; the reading is accepted. The owner text cites "section A" after this brief's former mislabel; the accepted "Shield-ready clearance" paragraph lies in `architecture.md` section B (review F-07) | 3.3, 17.2 item 16 |
| Q-R2-K1A (first round) | SUPERSEDED by Q-R2-K1A correction; its "MAIN schematic-only" text is withdrawn by the owner and is not applied | — |
| Q-R2-SW1-BLE | DECIDED (second round); SW1 non-metallic like SW5; SW2-SW4 metal; SW1 not pre-ordained to R2-S12 | 3.3, 6.9, 7.4.2, 14, 16, 17.2 items 22 / 23, 20, 21.3 |
| Q-R2-BOSS-MATERIAL | DECIDED (second round); boss growth inside a reserved region non-conductive and a G5 input; conductive growth fails R2-H15; existing frozen midcase metal is not new | 3.3, 6.9, 7.4.2, 9 (R2-H15), 14, 16, 17.2 item 23, 20, 21.3 |
| Q-R2-K1A correction | DECIDED (second round); K1-A = REAR layout / routing with G3-B-S14 part positions frozen + MAIN power-schematic fixes; no MAIN outline, placement or routing. Consistent with section 3.2 | 3.3, 4.5 |
| OD-G4-LRA-MAG | DECIDED; LRA magnet authorized | 3.3, 3.4, 5, 7.5.3, 17.2 item 21, 19, 21.3 |
| E-1 | DECIDED; file reverted by the owner; E-1 stays a precondition check | 2.1 |

#### 17.1.2 Still open

- **Q-R2-BATTERY (conditional, tool-raised).** Raised if LPR433736 is blocked for a non-structural reason that
  LPR403736 resolves. That case lies outside the OD-BATTERY fallback condition (7.1.6).

### 17.2 Interpretations made by this contract (each is reviewable; none is a new decision)

1. **REAR band.** "REAR band" means REAR level. Delta goes frontward of the REAR inner face inside the S14 outline and
   into the periphery band outside it. Delta carries no tolerance. Supplier planning ranges are unchanged for the new
   cells.
2. **Catalogue values.** These are OWNER_DECISION values labelled `catalogue_value`. The cell dimensions are nominal,
   with planning tolerances added (G1 practice). The STOP envelope of 6.2 is this contract's numeric definition of
   "assumed envelope".
3. **Fallback trigger.** The trigger is recorded SR-CASEBACK-CERAMIC evidence that the allowable is
   < `sigma_allow_req(LPR433736)`, plus an owner decision. Non-structural blockers do not trigger it.
4. **C-R1-03.** "C-R1-03 ruling not needed" means I-SUM binds, I-MAX is reported, and no I-MAX-only closure exists.
5. **Stem O-ring.** "Stem O-ring" means a groove on the pusher stem with the dynamic window. T3 is excluded as not a
   sealed pusher.
6. **Boss.** "+3.0 incl. seal and tolerance" means boss + boot / seal protrusion + tolerance beyond `D_case_body/2`.
7. **J202 location.** "J202 on B.Cu toward east" means located in the east sector. The mate direction is a design
   variable.
8. **Band retirement.** LA-Z-2 is inverted. The routes and the LRA lead channel are retired. The drop is a 2(vi)
   neighbour.
9. **C-R2-01.** It keeps the 2(v) item list. "Strict" means R1:R3-3.
10. **LRA fallback.** "LRA <= 2.70 mm tall … (Z-neutral)" means seated height including mount <= 2.70 at linear
    worst. The fallback is evaluated always and selected only without a B.Cu pose.
11. **LRA plan.** "LRA on MAIN B.Cu" means the body lies within the MAIN outline. The G4 maximum MAIN outline is
    binding, the Ø46 column is reported, and growth is a K1 constraint.
12. **Offset.** The offset direction is free (15-deg grid) and its magnitude runs 0-1.5 mm in 0.25 mm steps.
13. **Cup seal.** "Raised … radial O-ring on a caseback cup" means a frontward cup wall with the groove on the cup.
    Adhesive is excluded and the face seal is not carried.
14. **Cup structure.** Cup-ring structural credit comes only through computed compatibility, never a clamped edge.
    LA-STR-4 still governs ribs.
15. **Reserved regions.** A reserved region is the union of (a) the frozen radiator volume (pinned az/r/Z of section 5)
    and (b) the closed clock interval [345,15] / [300,330] / [105,135] deg taken over that volume's radial span and its
    pinned Z levels (GNSS all Z; BLE MAIN; Wi-Fi MAIN+REAR), Z bands read from generated/zstack.json. Angular bounds are
    closed; wrap through 0 deg. 'Outside the region' means a strict gap > EPS from the region solid (R1:R3-3). The
    material scope is decided (Q-R2-RESERVED-REGION, Q-R2-BOSS-MATERIAL); this boundary definition remains the
    contract's reading.
16. **Shield-ready.** 'Shield-ready' means the 'Shield-ready clearance' paragraph of architecture.md section B: U101 can
    0.8–1.0 (nom 0.85) + c_front = 1.0 mm against the 2.85 mm front gap and the U101 shield polygon 92.95 mm²
    (phase1_placement.json), preserved by R2-H28. (Accepted by the owner, Q-R2-SHIELD-REF.)
17. **Material choice.** The OD-G4-MATERIAL choice is conditional on G5 (`G4_BRIEF.md` 2.3).
18. **U7.** "U7 (DRV2625) to B.Cu" confirms the existing G2 `U7-B.Cu` allocation.
19. **J1501 mate.** J1501's mating axis is fixed parallel to Z (mating face toward the wrist, plug inserted from the
    rear). This is a lead design rule of section 6.5 derived from the frozen J1502 tail exit and rear insertion
    (evidence class DESIGN), not a reading of owner text; OD-CONN-SIDE fixes only the PCB side.
20. **Main-seal cs grid.** The authorized main-seal cs grid is extended to 2.0 mm. That is a design-size choice; the
    windows and tolerance are unchanged.
21. **LRA magnet.** The OD-G4-LRA-MAG authorization covers the frozen magnet invariant for the LRA only. The G4 8.9
    MAG_CLEAR exclusion and G4-H18 stay binding.
22. **SW1 / SW5 pusher class.** "Zirconia class" means MAT-CERAMIC with PC-CERAMIC-GRIND. "PEEK class" uses the
    authored polymer process tolerance PC-POLY-MOULD, with no PEEK property invented. Either option may close SW1, and
    either may close SW5 (Q-R2-SW5-PUSHER, Q-R2-SW1-BLE).
23. **SW1 and boss growth in reserved regions.** SW1 uses a non-metallic pusher (Q-R2-SW1-BLE), so the former reading
    "SW1 metal pusher outside the BLE reserved region" is withdrawn. Inside a reserved region (boundary per item 15)
    boss growth is non-conductive and recorded as a G5 input (Q-R2-BOSS-MATERIAL). The SW1 switch body at its frozen
    MAIN position and the existing frozen midcase metal are not new items; only what R2 adds is checked against the
    no-new-metal rule.
24. **Permittivity class.** A material-family label with its evidence class. No numeric permittivity is invented.

## 18. Acceptance criteria

1. Section 3.2 is recorded verbatim. Earlier decisions and invariants are unchanged except through the listed overlay
   records. C-R2-01 is recorded in R2 only.
2. Both batteries are reported side by side with margins and required allowables. The model performs no battery
   switch.
3. Total Z delta is exactly 0.000 (nominal / RSS / linear, both baselines). OD-THICK-REVA holds. Otherwise the verdict
   is BLOCKED (R2-S02).
4. `D_eval` <= 51.00 with its margin reported, and bosses <= 3.0 inside the windows. Otherwise BLOCKED (R2-S03).
5. G3 is not reopened (4.3). Historical reproduction is green (4.4). Changes are confined to `R2_FILES`.
6. Every lane has exactly one disposition with margins, thresholds and governing terms. H05-GEOM and H05-LRA-COUPLED are
   separate. The single-event rule is honoured.
7. `sigma_allow_req`, the deflection result and both shortfalls are reported per battery.
8. The joint annulus ledger is emitted, with no double-credited volume.
9. The LRA identity is reconstructed. The BMM350 distance is reported.
10. Presentation rules P-1 to P-4 are met. No claim of 5 ATM, structural, optical, adhesive, RF, MPN or supplier
    qualification appears anywhere.
11. Section 15 is satisfied and budgets are met. The verdict comes from section 12 only.
12. The section 17.1 owner answers are recorded verbatim. Every non-conductive item inside a reserved region carries
    its G5 record (material, permittivity class, volume).

## 19. Handoff (numeric; `generated/g4_r2_closure.json.handoff_to_g5_and_outline`)

Per battery:

- the joint design point, `D_eval` and margin to 51.00;
- pack, offset, carrier and pillars;
- zones A / B;
- connector poses and mates;
- FPC / tail / drop paths with lengths and bends;
- LRA pose, identity and BMM350 distance;
- cup, ring and seal gland geometry;
- charger block / land / drop;
- button topology, bore, boss and margins per switch;
- the MAIN outline constraint, including any growth beyond Ø46 as a K1 requirement;
- radiator-volume material map and the reserved-region record (6.9: material, permittivity class, volume) for G5;
- LRA-to-BMM350 distance as the input to the later magnetometer calibration (firmware / test item);
- supplier zero-margin values;
- FEA-1..4 and ATM-Q1..Q6, unchanged;
- open questions.

R2 authorizes nothing downstream (section 12).

## 20. Lead arithmetic to reproduce or explain (orientation only; not results)

- **Delta:** 0.200 / 0.500 mm. `battery_zone` 4.80 / 5.30 / 4.55 (LPR433736) and 4.50 / 5.00 / 4.25 (LPR403736)
  (nominal / linear / thin). `R_pack` 18.65 / 18.75.
- **Annulus at D 50.90 / tw 1.10:** `R_case_inner` 24.35. Carrier outer at `t_cw` 0.40 is 20.20 centred at linear
  worst. Free radial band:
  - to the Ø46 MAIN edge: 2.80 mm centred, 4.30 mm on the far side at 1.5 mm offset;
  - to the bore: 4.15 / 5.65 mm.

  LRA-LIN-RECT adverse (12.5 x 4.5 + 2 x 0.4, tangential, sagitta about 1.1 at r 21) needs about 6.4 mm. LRA-COIN-D8
  adverse needs 9.0 mm. **No authored class is expected to fit zone B at linear worst.** The likely outcome is the F.Cu
  fallback, which is SUPPLIER_GATED (SR-LRA), or R2-S04. This contests the synthesis.
- **Spigot:** R1 radial cs >= 1.5 with REAR-periphery Z -1.150. Adding Delta and the retired band (0.65, the R1 V14
  "band - 0.65" reservation = conductor channel 0.6 + 0.05) gives -1.150 + 0.200 + 0.65 = -0.30 (LPR433736) and
  -1.150 + 0.500 + 0.65 = 0.00 (LPR403736). The rest must come from zone B.
- **Buttons in reserved regions:** the SW1 window 292.5-307.5 deg overlaps the BLE reserved region from 300 deg; the
  SW5 window 112.5-127.5 deg lies inside the Wi-Fi reserved region 105-135 deg. Both pushers are non-metallic
  (Q-R2-SW5-PUSHER, Q-R2-SW1-BLE); boss growth inside the regions is non-conductive (Q-R2-BOSS-MATERIAL) and each
  in-region item is a G5 record (6.9).
- **Charger:** R1 radial-row `r_lim` 23.00-23.54 against the R1 charger radial / plan prerequisites (`r_lim` >= 24.031
  / 24.625 mm). The radial cup is expected to stress L-CHG even under C-R2-01 (R2-S06 risk). The east sector is
  congested:
  - contacts at 80-100 deg;
  - U703 10.3 mm in plan from the block centre;
  - WIFI_RAD from 107.7 deg; the Wi-Fi region from 105 deg;
  - SW5 at 112.5-127.5 deg.
- **T1:** cs >= 1.69 / 2.29 / 2.89 at stacks 0.04 / 0.07 / 0.10. A pusher groove with core >= 0.4 implies `d_p` >= about
  3.8 mm at cs 1.7.
- **Structure (context):** 159-186 MPa (LPR433736) and 141-162 MPa (LPR403736) against 150. Overlay-off anchors:
  Screen B 371.784 MPa / 0.120 mm; uniform ceramic 1.836 mm vs `t_in` 1.10.

## 21. Execution roles, independent review and manual commit gate

### 21.1 Roles

- **Owner** approves this contract. The **lead** commits it as the R2 contract commit on
  `mechanical/g4-r2-package-closure`. After that commit the brief is immutable.
- **Implementer:** a fresh session with shell access (for example Claude Opus 5.5 in Claude Code, high or xhigh
  effort). The contract is this brief. The implementer does not commit, push, stash, reset or clean; the R2 files stay
  untracked for review. The lead does not implement R2 in the contract session.
- **Independent reviewer (different family):** the **`codex-sol` lane, High effort, read-only**. Resolve the concrete
  model id from the routing configuration at review time. The reviewer may run every section 15 command and read every
  file. It edits nothing and commits nothing. Its verdict is one of:
  - `PASS AS CORRECT <R2 verdict> STUDY`;
  - `CORRECTION REQUIRED` (numbered findings);
  - `REJECT`.

### 21.2 Manual commit gate

After the review and lead adjudication:

- corrections, if any, run under this brief (no amendment without the owner);
- the lead or owner then commits **exactly** the remaining `R2_FILES` by hand on this branch;
- the owner pushes (pushes fail from the sandbox);
- the state record (`architecture.*`, `README.md`, `input_register.json`, including the stale LPR454440 invariant
  text) is a later lead commit under its own contract.

### 21.3 Independent review must challenge

1. **T1 ruling** (7.4.1): is "never selectable" really R1-scoped? Are the dynamic window and the cs tolerance
   untouched?
2. **Z overlay:** exact 0.000 on both baselines. Delta carries no tolerance. No thinner-cell credit. The REAR stays
   fixed relative to the pod plane.
3. **G3 check** (4.3): pillars change by +Delta only; S14 is byte-identical; no G3 gate is claimed.
4. **Cup-ring structural model:** no clamped assumption; ring continuity; the single-event rule;
   `sigma_allow_req` correctness; stress never a model FAIL; no battery switch.
5. **Joint annulus allocation:** completeness of the occupant list; step-dependent envelopes; no double credit.
6. **LRA:** zone-B fit at linear worst; the MAIN-outline column choice; F.Cu Z-neutrality; C-R1-08; R1:R4-1 identity;
   BMM350 distance (OD-G4-LRA-MAG authorized; MAG_CLEAR exclusion retained).
7. **Charger:** C-R2-01 applied exactly; retired routes neither credited nor enforced; `r_lim(cup)`; physical headline;
   east-sector keep-outs.
8. **SW1 / SW5 and reserved regions:** SW1 and SW5 non-metallic (zirconia or PEEK class, no PEEK property invented);
   boss growth inside a reserved region non-conductive; no new metal, conductor or component in any reserved region;
   every non-conductive item carries its G5 record (material, permittivity class, volume).
9. **R1:R5 population / unit rules** and R1:R4-8 typed units.
10. **Historical reproduction:** detached G4 / R1 runs; the in-process extension equals exactly `R1_FILES ∪ R2_FILES`;
    no accepted file edited.
11. **Claims and invention:** no MPN, supplier, catalogue-as-verified, zirconia-strength, RF or qualification claim.
    Catalogue labels present.
