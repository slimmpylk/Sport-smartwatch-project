# G4-R1 case / seal / support blocker-resolution study (Rev-A)

**R1 OWNER DECISION REQUIRED**

R1 study result (uncommitted; independent review pending). No G4 verdict is emitted; nothing downstream is authorized.

No 5 ATM, structural, optical, adhesive, RF, MPN or supplier qualification is claimed anywhere.

Leader (diagnostic ranking): **G4-B**. Selection permitted: **false**; selected: n/a; selected D: n/a.

## 1. Lane dispositions (G4-B)

| Lane | Disposition |
| --- | --- |
| L-ASM | OWNER_GATED |
| L-BTN | OWNER_GATED |
| L-CHG | OWNER_GATED |
| L-LRA | ARCHITECTURE_GATED |
| L-RAD | SUPPLIER_GATED |
| L-SEAL | OWNER_GATED |
| L-STR | OWNER_GATED |
| L-WIN | SUPPLIER_GATED |

## 2. Candidates and derived diameters

| Candidate | D_min | D_complete | D_radial_core (radial core only) | study candidate | geometric candidate | owner-decision candidate | geometry closed, supplier gates open | whole-design compliant | D_eval | tw_eval | resolved lanes | verdict if selected | stops raised |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G4-B | n/a | n/a | 50.50 | true | false | true | false | false | 50.90 | 1.10 | 2 | R1 OWNER DECISION REQUIRED | R1-S03, R1-S04, R1-S05, R1-S06, R1-S07, R1-S08, R1-S13 |
| G4-A | n/a | n/a | n/a | true | false | true | false | false | 50.90 | 1.10 | 1 | R1 OWNER DECISION REQUIRED | R1-S03, R1-S04, R1-S05, R1-S06, R1-S07, R1-S08, R1-S13 |
| G4-C1 | n/a | n/a | n/a | true | false | true | false | false | 50.90 | 1.10 | 1 | R1 OWNER DECISION REQUIRED | R1-S03, R1-S04, R1-S05, R1-S06, R1-S07, R1-S08, R1-S13 |

Whole-design compliant (R3-7) requires every lane RESOLVED_GEOMETRICALLY, every hard check PASS, no stop, D_complete <= 51.00, no protrusion and zero Z delta; an architecture-, owner- or supplier-gated mandatory lane is never compliance. Blocking items: G4-B: owner L-BTN, L-SEAL, L-CHG, L-STR, L-ASM, architecture L-LRA, supplier L-WIN, L-RAD, physical failures R1-H05, R1-H08, R1-H09, R1-H11, R1-H12, R1-H13, R1-H14, R1-H19; G4-A: owner L-BTN, L-SEAL, L-CHG, L-STR, L-RAD, L-ASM, architecture L-LRA, supplier L-WIN, physical failures R1-H04, R1-H05, R1-H08, R1-H09, R1-H11, R1-H12, R1-H13, R1-H14, R1-H19; G4-C1: owner L-BTN, L-SEAL, L-CHG, L-STR, L-RAD, L-ASM, architecture L-LRA, supplier L-WIN, physical failures R1-H04, R1-H05, R1-H08, R1-H09, R1-H11, R1-H12, R1-H13, R1-H14, R1-H19.

D_min is the first primary-grid diameter at which every D-dependent non-LRA group passes at ONE (D, bulk wall) point; `n/a` means none at <= 51.00 mm. D_radial_core covers H03-OD, H05-GEOM and insertion only and is never a whole-design statement (R2-7). Every group, STRUCTURE included, is the result of that exact point (R2-1).

- G4-B group first / last pass D: BUTTONS n/a..n/a; CHARGER n/a..n/a; COVER +50.100..+52.500; H03-OD +48.000..+50.900; H05-GEOM +50.350..+52.500; INSERTION +50.050..+52.500; MAIN-SEAL +51.800..+52.500; STRUCTURE n/a..n/a
- G4-A group first / last pass D: BUTTONS n/a..n/a; CHARGER n/a..n/a; COVER +50.100..+52.500; H03-OD +48.000..+50.900; H05-GEOM +51.100..+52.500; INSERTION +50.200..+52.500; MAIN-SEAL +51.800..+52.500; STRUCTURE n/a..n/a
- G4-C1 group first / last pass D: BUTTONS n/a..n/a; CHARGER n/a..n/a; COVER +50.100..+52.500; H03-OD +48.000..+50.900; H05-GEOM +51.100..+52.500; INSERTION +50.200..+52.500; MAIN-SEAL +51.800..+52.500; STRUCTURE n/a..n/a

### 2.1 Structural feasibility by D (per point, R2-1)

| Candidate | points | plate radii screened | methods | D with STRUCTURE passing | minimum deflection bound mm | limit mm |
| --- | --- | --- | --- | --- | --- | --- |
| G4-B | 819 | 2331 | COMPLIANCE_BOUND | none | +0.061 | +0.050 |
| G4-A | 819 | 0 | GEOMETRY | none | n/a | +0.050 |
| G4-C1 | 819 | 1031 | COMPLIANCE_BOUND | none | +0.222 | +0.050 |

COMPLIANCE_BOUND: the Loewner-maximal admissible plate gives a continuum deflection lower bound C / (q pi R^2) >= the limit, so every admissible configuration fails Screen B at that point; GEOMETRY: no admissible caseback thickness window. Coupled thresholds (first D with the named groups at ONE point): G4-B {"charger_with_main_seal": null, "charger_with_od": null, "charger_with_radial_core": null, "charger_with_radial_core_and_main_seal": null, "charger_with_radial_core_and_od": null, "main_seal_with_radial_core": 51.8, "rule": "first grid D (primary or report-only extension to 52.50 mm) with the named groups passing at one common bulk wall; CHARGER is the complete literal C-R1-01 closure of that point (R3-1); null = none on the grid"}; G4-A {"charger_with_main_seal": null, "charger_with_od": null, "charger_with_radial_core": null, "charger_with_radial_core_and_main_seal": null, "charger_with_radial_core_and_od": null, "main_seal_with_radial_core": 51.8, "rule": "first grid D (primary or report-only extension to 52.50 mm) with the named groups passing at one common bulk wall; CHARGER is the complete literal C-R1-01 closure of that point (R3-1); null = none on the grid"}; G4-C1 {"charger_with_main_seal": null, "charger_with_od": null, "charger_with_radial_core": null, "charger_with_radial_core_and_main_seal": null, "charger_with_radial_core_and_od": null, "main_seal_with_radial_core": 51.8, "rule": "first grid D (primary or report-only extension to 52.50 mm) with the named groups passing at one common bulk wall; CHARGER is the complete literal C-R1-01 closure of that point (R3-1); null = none on the grid"}

## 3. Hard checks R1-H01 .. R1-H20 (G4-B)

| ID | study_status | physical_pass | margin | units | governing term | threshold value | threshold units | required delta | required delta units | gate_ids | evidence_complete | owning lane | G4-literal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1-H01 | GATED | true | +0.000 | mm | n/a | +2.250 | mm | n/a | n/a | SR-CHG-MECH | false | L-STR / L-SEAL / L-CHG | H01 fail |
| R1-H02 | PASS | true | +0.000 | mm | n/a | n/a | n/a | n/a | n/a | - | true | L-RAD / L-BTN | H03 pass |
| R1-H03 | PASS | true | +0.000 | exact | n/a | n/a | n/a | n/a | n/a | - | true | cross-cutting | H04 pass |
| R1-H04 | GATED | true | +0.020 | mm | n/a | n/a | n/a | n/a | n/a | SR-FPC-MECH, SR-BATT-PCM, SR-CHG-MECH | true | L-RAD | H05 fail |
| R1-H05 | GATED | false | -1.140 | mm | n/a | n/a | n/a | +1.140 | mm | OD-G4-LRA-ARCH | true | L-LRA | H05 fail |
| R1-H06 | GATED | true | +0.000 | mm | n/a | n/a | n/a | n/a | n/a | SR-COVER-LENS, SR-DISPLAY-LAND | true | L-WIN / regression | H06 pass |
| R1-H07 | GATED | true | +0.047 | mm | n/a | n/a | n/a | n/a | n/a | SR-WINDOW, MG-WINDOW-XTALK | true | L-WIN | H12 pass |
| R1-H08 | FAIL | false | -0.070 | mm | n/a | n/a | n/a | +0.070 | mm | R1-S07, FEA-1, FEA-2 | true | L-STR | H10 pass |
| R1-H09 | FAIL | false | -221.784 | MPa | n/a | +1.836 | mm | +221.784 | MPa | R1-S07, OD-G4-MATERIAL, OD-G4-STACK, FEA-1, FEA-2 | true | L-STR | H13 fail |
| R1-H10 | GATED | true | +20.355 | MPa | n/a | n/a | n/a | n/a | n/a | CASE-SIDE-LOAD-PATH, FEA-3 | false | L-STR | H13 fail |
| R1-H11 | FAIL | false | -0.020 | dimensionless | H11-RADIAL-gland_compression_min | +1.580 | mm (bulk wall tw: smallest owner threshold carrying any main seal, adhesive) | +0.020 | dimensionless (deficit of the governing typed term H11-RADIAL-gland_compression_min) | R1-S06, OD-G4-ENVELOPE (D), OD-G4-STACK, serviceability (adhesive) | true | L-SEAL | H15 fail |
| R1-H12 | FAIL | false | -0.930 | mm | n/a | +54.560 | mm (T2-R zero-margin nominal D) | +0.930 | mm | R1-S03, SR-BUTTONS, OD-G4-ENVELOPE (boss / D) | true | L-BTN | H21 fail |
| R1-H13 | FAIL | false | n/a | exact | n/a | n/a | n/a | n/a | n/a | R1-S06 | true | L-SEAL | H14 pass |
| R1-H14 | FAIL | false | -1.620 | mm | CHG_LAND vs SCREW_NE [plan AND Z] | +24.625 | mm (r_lim, radial / plan prerequisite) | +0.325 | mm (r_lim deficit of the radial / plan prerequisite) | R1-S04, Q-R1-CHARGER | true | L-CHG | H20 fail |
| R1-H15 | PASS | true | n/a | exact | n/a | n/a | n/a | n/a | n/a | - | true | cross-cutting | H17 fail |
| R1-H16 | PASS | true | n/a | exact | n/a | n/a | n/a | n/a | n/a | - | true | cross-cutting | H19 pass |
| R1-H17 | GATED | true | +0.050 | mm | n/a | n/a | n/a | n/a | n/a | SERVICE-COVER-REBOND, A10:Q-R1-CHARGER (R1-S04), A11:Q-R1-CHARGER (R1-S04), A11:Q-R1-MAIN-SEAL (R1-S06), A11:Q-R1-STRUCTURE (R1-S07 / R1-S05), A1:Q-R1-STRUCTURE (R1-S07 / R1-S05), A5:OD-G4-LRA-ARCH (R1-S08), A9:Q-R1-BUTTON-ENVELOPE (R1-S03) | true | L-ASM | H23 fail |
| R1-H18 | PASS | true | +0.400 | mm | n/a | n/a | n/a | n/a | n/a | - | true | L-STR | H24 pass |
| R1-H19 | GATED | false | -2.170 | mm | n/a | +1.030 | mm (authored-grid maximum) | +1.470 | mm | OD-G4-LRA-ARCH, SR-LRA, Q-R1-STRUCTURE | true | L-LRA | H22 fail |
| R1-H20 | PASS | true | n/a | exact | n/a | n/a | n/a | n/a | n/a | - | true | cross-cutting | H25 pass |

Margin, threshold and required delta are separate typed pairs (units per column). R1-H11 and R1-H14 carry individually typed terms (sections 7 and 9); no minimum is taken across units or categories.

- **R1-H01** GATED: G2-REVA / G2-REVA-HI reproduced, total Z delta 0.000; every R1 feature fits the REAR-periphery band Threshold: charger block height above Z=0 <= 2.250 mm fits the REAR-periphery allocation (allocation-fit semantics, SR-CHG-MECH; equality allowed). At that height the block has a zero Z gap to the CHG_ROUTE / CHG_LINK band; it is plan-separated from them, so the common 3-D predicate holds (R4-7); only the conservative block-AND-Z screen needs < 2.250 mm strictly (R1-H14 diagnostic, not contract text).
- **R1-H02** PASS: D_case_body <= 51.00; only the five button bosses protrude, <= +1.0 mm incl. boot and tolerance
- **R1-H03** PASS: LEGACY numbers and every G4-literal result at 00e77cb reproduced exactly
- **R1-H04** GATED: H05-GEOM: straight, XF, XB, XC, wall side, wall dielectric, main-case, t_allow >= 0 with azimuth-resolved wall
- **R1-H05** GATED: H05-LRA-COUPLED (XL lateral and Z) - separate; part of the L-LRA verdict only Threshold: H05-LRA-COUPLED terms >= 0 (XL-LRA run height under the display-land ceiling).
- **R1-H06** GATED: Cover / bezel / land regression (G4 H06-H09) Threshold: supplier zero-margin values of the X25 cover fit (G4 H06 spec).
- **R1-H07** GATED: W1 @ 0.45 mm minimum: stress and deflection screens, rib fit, bond land, no rib-to-optics load Threshold: supplier allowable >= the W1 planning stress of each carried material; rib width + tol <= inter-cell web.
- **R1-H08** FAIL: Pressure partition sums; no forbidden branch (battery, REAR PCB, G3 support lands, carrier lower web); PCB load 0.000 N Threshold: zero load on battery / REAR PCB / G3 support lands / carrier lower web.
- **R1-H09** FAIL: Stiffened caseback: stress <= sigma_allow(min); deflection <= min(c_cb_rear min, window standoff) at p max (Screen B governs, Screen A reported) Threshold: uniform isotropic caseback >= 1.836 mm nominal (MAT-CERAMIC) vs t_in <= 1.10 mm by the pod residual.
- **R1-H10** GATED: Perimeter bearing, screw shear / pull-out and split-plate bond-shear thresholds with supplier zero-margin
- **R1-H11** FAIL: Main seal gland compression and fill inside window at +/-0.05 mm; seal path closed; no impossible gland remains Threshold: typed predicates per topology (face / adhesive / radial; R4-8); owner thresholds: adhesive bulk wall >= +1.580 mm, face bulk wall >= +2.130 mm, radial cross-section >= +1.500 mm with REAR-periphery Z -1.150 mm.
- **R1-H12** FAIL: Buttons per SW: guide stack under I-SUM and I-MAX, core, boss wall, rim land, stroke >= c_switch, tangential fit, material constraints
- **R1-H13** FAIL: Every aperture has exactly one primary seal with a feasible geometry class
- **R1-H14** FAIL: Charger: block inside wedge and outside WIFI_RAD; land per C-R1-01 with overshoot <= caps; corridors clear in plan and Z Threshold: contract-mandated C-R1-01 predicates (item 1 block; item 2 (i)-(vi) land with 2(v) plan AND Z; item 3 caps) and the physical predicates required elsewhere (land seal-flange clearance c_chg_window, frozen U6 island, block strict 3-D clearance) at one pose of one design point; the block-AND-Z screen and the supplier thresholds are diagnostics and never decide. Numeric prerequisite threshold: caseback radial limit r_lim >= 24.624973 mm (radial / plan prerequisite of the land-flange and block-flange terms only, not a closure). The land 2(v) Z separation from the screws / supports is unsatisfiable under the retained Z model (Q-R1-CHARGER).
- **R1-H15** PASS: H17 zero conductive / wiring intrusion in radiators (ribs, split plate, screws, plungers, charger); H18 MAG_CLEAR
- **R1-H16** PASS: H19: S14 outline, pod, supports, tail corridors, U6 island untouched; no G3 support-land enlargement claimed
- **R1-H17** GATED: Assembly sequence (C-R1-06) executable, access direction per operation, rear-insertion collision-free Threshold: operation sequence executable on its own geometry (c_insert zero-margin value); product closure requires every A-step dependency RESOLVED.
- **R1-H18** PASS: >= 4 case / caseback supports incl. W/NW outside the pack (G4 H24)
- **R1-H19** GATED: LRA lane: PASS only with an authored / supplied class fitting a pose at the current allocation; else quantified maximum envelope and deficit Threshold: authored / supplied class (C-R1-08, lead / exit included) with envelope height <= 1.030 mm on a plan-feasible pose and a structurally feasible caseback.
- **R1-H20** PASS: No KiCad / interface / immutable-file change; historical reproduction of section 5.1

## 4. Stops R1-S01 .. R1-S13

| Stop | raised | scope | derivation |
| --- | --- | --- | --- |
| R1-S01 | false | whole run | OD-G4-WINDOW recorded: True; W1 row passes without Z delta: True |
| R1-S02 | false | whole run | OD-G4-ASSEMBLY recorded: True; own sequence geometry / order / identity executable: True |
| R1-S03 | true | lane | button topologies closing per SW (I-SUM / I-MAX): {'SW1': (False, False), 'SW2': (False, False), 'SW3': (False, False), 'SW4': (False, False), 'SW5': (False, False)} |
| R1-S04 | true | lane | complete C-R1-01 charger closure (contract-mandated + physical predicates, same-point neighbours) at the design point: False (governing contract term CHG_LAND vs SCREW_NE [plan AND Z] -1.620 mm); first D (any wall) with the radial prerequisite 49.80, the plan prerequisite 50.95 (r_lim 24.625 mm vs 24.300 mm here), the LAND 2(v) Z prerequisite n/a, the complete closure n/a; complete closure with H03-OD at one point: n/a |
| R1-S05 | true | lane | required uniform MAT-CERAMIC caseback 1.836 mm nominal vs t_in 1.10 (pod residual) / Z 2.230 available: thicker caseback / Z needed = True |
| R1-S06 | true | lane | main seal topologies feasible: []; seal path closed: True; apertures feasible: False |
| R1-S07 | true | lane | Screen B 371.8 MPa / 0.1198 mm, Screen A 371.8 MPa vs allowable 150 MPa / limit 0.050 mm |
| R1-S08 | true | lane | no authored / supplied class fits any pose (pocket included, structural re-screen applied): delta_Z 1.470 mm vs the authored-grid maximum 1.030 mm (before structural qualification; continuous upper bound 1.110 mm, not a search result); structurally feasible searched envelope: n/a |
| R1-S09 | false | whole run | S14 untouched / switches frozen: True; KiCad / interfaces unchanged: True |
| R1-S10 | false | whole run | whole-design rule: some candidate closes the radial core (H03-OD, H05-GEOM, insertion) at one D <= 51.00 mm: True; unpermitted protrusions: 0. Lane D thresholds above 51.00 mm (e.g. main seal) are owner-question numbers, not a selected diameter. |
| R1-S11 | false | whole run | PASS checks resting on a credit: [] |
| R1-S12 | false | whole run | pins / brief / immutables / historical G4: scope True, in-process G4 True |
| R1-S13 | true | lane | lanes needing an unrecorded owner decision or C-R1-03 adjudication: ['L-BTN', 'L-SEAL', 'L-CHG', 'L-STR', 'L-ASM'] |

## 5. Structure (L-STR, G4-B)

| Screen | governing sigma MPa | region | r mm | stress margin MPa | w max mm | deflection margin mm | pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Screen B (governs) | +371.784 | inner | +12.105 | -221.784 | +0.120 | -0.070 | false |
| Screen A (reported) | +371.784 | inner | +12.105 | -221.784 | +0.120 | -0.070 | false |

Selected configuration: {'h': 0.0, 'n': 0, 't_in': 1.1, 't_out': 1.6, 'w': 0.0}; rib layout gap n/a deg; configurations evaluated: 344.
Design-point bound (R2-1): COMPLIANCE_BOUND, deflection lower bound 0.077 mm vs limit 0.050 mm; relaxed model dominance verified on 1032 admissible configurations; maximum deflection at the rigid boss on every searched configuration: true.
Best ribbed configuration: {'h': 0.4, 'n': 8, 't_in': 1.1, 't_out': 1.6, 'w': 0.8}, Screen B +371.994 MPa / +0.120 mm, Screen A +370.505 MPa; D_r / D_plate at the outer rib radius +1.021.
| Material | required uniform nominal t mm | required outer t (t_in max) mm | rigid annulus clamped / ss MPa |
| --- | --- | --- | --- |
| MAT-CERAMIC | +1.836 | +3.611 | +51.865 / +113.724 |
| MAT-GF-POLY | +4.757 | n/a | +54.871 / +118.711 |
| MAT-NF-METAL | +1.976 | +3.963 | +51.865 / +113.210 |

Forbidden branches: BATTERY contact false load +0.000; CARRIER_LOWER_WEB contact false load +0.000; G3_SUPPORT_LANDS contact true load n/a; REAR_PCB contact true load n/a.

Anchors: isotropic limit max rel 5.20e-08 (allowed 1e-06); no-rib 622.918 MPa / 0.282746 mm; h_rib = 0 gives D_r == D_plate: true; N vs 2N rel 6.25e-06 / 3.31e-06; exact compliance integral vs 1201-point trapezoid rel 1.1e-08.

## 6. Radial and V03 local walls (L-RAD, G4-B)

| Arc | material | Z extent | grid mm | own-feasible t_lo..t_hi | selected t | rule | wall | edge | straight | insertion | edge at floor | hoop margin MPa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FPC_CORR | MAT-NF-METAL | MAIN_BATTERY | 0.74..1.10 | 0.74..1.02 | +0.880 | MAIN_BATTERY | +0.140 | +0.150 | +0.300 | +0.050 | +0.290 | +131.064 |
| BATT_TAIL | MAT-NF-METAL | MAIN_BATTERY | 0.74..1.10 | 0.74..1.02 | +0.880 | MAIN_BATTERY | +0.140 | +0.150 | +0.300 | +0.050 | +0.290 | +131.064 |
| CHG_RISER | MAT-NF-METAL | MAIN_BATTERY | 0.74..1.10 | 0.74..1.10 | +0.960 | MAIN_BATTERY | +0.220 | +0.220 | +0.220 | +0.200 | +0.440 | +132.711 |

H05-GEOM min +0.020 (pass true); H05-LRA-COUPLED {"H05-EDGE-XL-LRA": 0.05, "H05-EDGE-Z-XL-LRA": -1.14, "H05-STRAIGHT@U7-RISER": 0.05}; carrier rcin +23.300 / tcw +0.350 (pack +0.000).

## 7. Main seal (L-SEAL, G4-B)

R5 population evaluation: every authorized cross-section row is evaluated independently; every physical result is an explicit set reduction over the row population or a boolean subset of it (no representative / best row; internal unit mm, emitted mm). Rules: charger_by_topology: per topology, per distinct (r_lim(r), flange_top(r)) of its evaluated rows: the complete same-point charger predicate; topology result = any / all over its rows (both reported); coupled_population: fully_feasible_rows of the coupled topology when it closes, else every evaluated row of the face fallback; coupled_topology: the first closing topology in the fixed order face, radial, adhesive (serviceable first); when none closes, the face topology (brief 6.3 baseline; the accepted R4 fallback, reported not closed) - boolean predicates and a fixed order only; diagnostic_rows: rows above the V11 stop up to diagnostic_stop: they only locate the owner zero-margin thresholds and are never coupled; evaluated_rows: every authorized cross-section row of the topology (V11 grid start..stop; adhesive: its one bond-land row), each evaluated independently through every typed predicate with its own gland, flange, r_lim and flange top; flange_top: coupled adverse flange top = max over the coupled population of flange_top(r) = (flange thickness of r, or the plate t_out for a row without a flange) + thickness tolerance; every flange Z relation of the point (charger neighbour, feature set, closure clearances) uses it, i.e. the most negative flange Z gap of the population; fully_feasible_rows: {r in evaluated_rows | every typed predicate of r holds}; topology feasible = any(r.pass_all over evaluated_rows); gland_window_rows: R_gland = {r in evaluated_rows | every gland_* predicate of r holds} (O-ring topologies only); h14_flange_rows: per row of the coupled population: CHG_LAND / CHG_BLOCK vs the flange of that row at the design pose; the H14 flange terms are the envelope (effective clearance = min over the rows, clear = all rows clear), checked row by row; owner_thresholds: smallest gland-feasible cs = min cs over {r in evaluated + diagnostic rows | gland window holds}; its typed terms and required bulk wall are those of that specific row; adhesive: its one row; physical_envelope: per topology over evaluated_rows: r_lim [min, max] and flange thickness [min, max] (one length quantity each); predicate_feasible_rows: per typed predicate k: {r in evaluated_rows | predicate k of r holds} (boolean subsets); r_lim: coupled caseback radial limit = min over the coupled population of r_lim(r) (adverse; face / adhesive rows share R_side - tol, so it is unique there); every r_lim consumer of the point (structure, charger, LRA, G4 design terms) uses it; radial_supplier_land: per authorized radial row: strict-wedge zero-margin land width at chg_r_out = min(CHG_CONTACT r1, r_lim(r) - c_chg_window); governing supplier threshold = min over the rows (land < value strictly for every authorized radial row); envelope [min, max]; representative_row: DISPLAY ONLY, chosen after every physical result: key (pass_all, number of passing predicates, gland window, minimum dimensionless margin, minimum mm margin on the canonical 1e-9 mm grid, smallest cs) - booleans and a count first, then one homogeneous quantity per component; never read by a physical, hard-check, stop, threshold, owner-question or disposition path; term_population: fully_feasible_rows when non-empty, else evaluated_rows (boolean rule); term_reductions: per typed predicate k: value = max over the term population of m_k(r) (one quantity, one units group: the best margin some row of the population attains; deficit = -value); worst = min; never across predicates or units

| Topology | evaluated_rows | gland_window_rows (R_gland) | fully_feasible_rows | feasible | term population | physical envelope (r_lim / flange thickness mm) | representative row (display only) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| face | face#00, face#01, face#02, face#03, face#04, face#05, face#06, face#07 | face#04, face#05, face#06, face#07 | none | false | evaluated_rows | r_lim 24.300..24.300; flange 1.300..1.800 | face#06 (cs 1.10) |
| adhesive | adhesive#00 | n/a | none | false | evaluated_rows | r_lim 24.300..24.300; flange none | adhesive#00 (cs n/a) |
| radial | radial#00, radial#01, radial#02, radial#03, radial#04, radial#05, radial#06, radial#07 | none | none | false | evaluated_rows | r_lim 23.000..23.540; flange none | radial#00 (cs 0.50) |

| Topology | predicate | units | predicate_feasible_rows | population reduction (max) | rows attaining | worst (min) |
| --- | --- | --- | --- | --- | --- | --- |
| face | face_annulus | mm | none | -0.560 | face#00 | -1.390 |
| face | flange_groove_residual | mm | face#00, face#01, face#02, face#03, face#04, face#05, face#06, face#07 | +0.095 | face#01 | +5.000e-03 |
| face | gland_compression_max | dimensionless | face#03, face#04, face#05, face#06, face#07 | +0.028 | face#07 | -0.027 |
| face | gland_compression_min | dimensionless | face#04, face#05, face#06, face#07 | +0.024 | face#07 | -0.061 |
| face | gland_fill | dimensionless | face#00, face#01, face#02, face#03, face#04, face#05, face#06, face#07 | +5.580e-03 | face#03 | +4.106e-04 |
| adhesive | bond_land_annulus | mm | none | -0.480 | adhesive#00 | -0.480 |
| radial | continuous_bore | mm | radial#00, radial#01, radial#02, radial#03, radial#04, radial#05, radial#06, radial#07 | +0.000 | radial#00, radial#01, radial#02, radial#03, radial#04, radial#05, radial#06, radial#07 | +0.000 |
| radial | gland_compression_max | dimensionless | none | -0.012 | radial#07 | -0.118 |
| radial | gland_compression_min | dimensionless | none | -0.020 | radial#07 | -0.172 |
| radial | gland_fill | dimensionless | radial#00, radial#01, radial#02, radial#03, radial#04, radial#05, radial#06, radial#07 | +6.311e-03 | radial#00 | +6.197e-04 |
| radial | spigot_rear_periphery_z | mm | radial#00 | +0.010 | radial#00 | -0.790 |

Coupled seal of the point: topology face (fallback, not closed), population face#00, face#01, face#02, face#03, face#04, face#05, face#06, face#07; caseback r_lim = min over the population 24.300 mm (envelope 24.300..24.300); adverse flange top = max over the population 1.820 mm (flange thickness 1.300..1.800 mm). H14 seal-flange rows over the population: land effective clearance min -0.075 mm (envelope term -0.075), Z gap min -1.620 mm, clear on every row false; block effective clearance min +1.043 mm, clear on every row true.

Owner thresholds: adhesive bulk wall tw >= +1.580 mm; face bulk wall tw >= +2.130 mm at the smallest gland-feasible cs +0.900 mm (typed terms there: face_annulus -1.030 mm, flange_groove_residual +0.060 mm, gland_compression_max +0.016 dimensionless, gland_compression_min +0.003 dimensionless, gland_fill +0.003 dimensionless); radial smallest gland-feasible cs +1.500 mm (typed terms there: continuous_bore +0.000 mm, gland_compression_max +0.003 dimensionless, gland_compression_min +0.002 dimensionless, gland_fill +0.001 dimensionless, spigot_rear_periphery_z -1.150 mm). Rear-face annulus (mm): bulk MAT-NF-METAL +1.060; dielectric sectors +1.020. First main-seal grid closure: D 51.80 mm, tw 1.60 mm, adhesive (non-serviceable).

Aperture feasibility: {"S-CB-MAIN": false, "S-CHG": false, "S-COVER": true, "S-POD": true, "S-SW1": false, "S-SW2": false, "S-SW3": false, "S-SW4": false, "S-SW5": false, "S-VENT": true}. Seal graph closed: true.

### 7.1 R1-H11 typed terms (R4-8)

| Term | topology | quantity | reduction | value | units | threshold | pass | delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H11-FACE-face_annulus | face | midcase rear-face annulus minus the face-gland annulus | max over evaluated_rows (8 rows) | -0.560 | mm | >= +0.000 | false | +0.560 |
| H11-FACE-flange_groove_residual | face | caseback flange thickness minus groove depth, tolerances and residual floor | max over evaluated_rows (8 rows) | +0.095 | mm | >= +0.000 | true | +0.000 |
| H11-FACE-gland_compression_max | face | static-window maximum minus the O-ring compression ratio (adverse cs +0.05 mm) | max over evaluated_rows (8 rows) | +0.028 | dimensionless | >= +0.000 | true | +0.000 |
| H11-FACE-gland_compression_min | face | O-ring compression ratio minus the static-window minimum (adverse cs -0.05 mm, groove depth tolerance) | max over evaluated_rows (8 rows) | +0.024 | dimensionless | >= +0.000 | true | +0.000 |
| H11-FACE-gland_fill | face | gland fill-ratio maximum minus the fill ratio (adverse cs +0.05 mm) | max over evaluated_rows (8 rows) | +5.580e-03 | dimensionless | >= +0.000 | true | +0.000 |
| H11-FACE-joint_row | face | one authorized cross-section row meets every typed predicate (any r.pass_all) | any over evaluated_rows (8 rows) | false | bool | true | false | n/a |
| H11-ADHESIVE-bond_land_annulus | adhesive | midcase rear-face annulus minus the adhesive bond land | max over evaluated_rows (1 rows) | -0.480 | mm | >= +0.000 | false | +0.480 |
| H11-ADHESIVE-joint_row | adhesive | one authorized cross-section row meets every typed predicate (any r.pass_all) | any over evaluated_rows (1 rows) | false | bool | true | false | n/a |
| H11-RADIAL-continuous_bore | radial | continuous radial-spigot bore (through-rear-face arc break) | max over evaluated_rows (8 rows) | +0.000 | mm | >= +0.000 | true | +0.000 |
| H11-RADIAL-gland_compression_max | radial | static-window maximum minus the O-ring compression ratio (adverse cs +0.05 mm) | max over evaluated_rows (8 rows) | -0.012 | dimensionless | >= +0.000 | false | +0.012 |
| H11-RADIAL-gland_compression_min | radial | O-ring compression ratio minus the static-window minimum (adverse cs -0.05 mm, groove depth tolerance) | max over evaluated_rows (8 rows) | -0.020 | dimensionless | >= +0.000 | false | +0.020 |
| H11-RADIAL-gland_fill | radial | gland fill-ratio maximum minus the fill ratio (adverse cs +0.05 mm) | max over evaluated_rows (8 rows) | +6.311e-03 | dimensionless | >= +0.000 | true | +0.000 |
| H11-RADIAL-spigot_rear_periphery_z | radial | REAR-periphery Z residual with the radial spigot (G4 H01 specification) | max over evaluated_rows (8 rows) | +0.010 | mm | >= +0.000 | true | +0.000 |
| H11-RADIAL-joint_row | radial | one authorized cross-section row meets every typed predicate (any r.pass_all) | any over evaluated_rows (8 rows) | false | bool | true | false | n/a |
| H11-SEAL-PATH-CLOSED | - | seal path closure (G4 seal_closure graph) | - | true | bool | true | true | n/a |
| H11-SOME-TOPOLOGY-CLOSES | - | some carried main-seal topology closes every typed predicate on the cs grid | - | false | bool | true | false | n/a |

Topology feasibility (conjunction of its typed terms = any(r.pass_all)): face false (fully feasible rows: none), adhesive false (fully feasible rows: none), radial false (fully feasible rows: none). physical_pass = false (conjunction of the check predicates). Governing term per units group (no cross-unit ranking): dimensionless: H11-RADIAL-gland_compression_min -0.020 dimensionless; mm: H11-FACE-face_annulus -0.560 mm. Check-level margin: -0.020 dimensionless (H11-RADIAL-gland_compression_min).

## 8. Buttons (L-BTN, G4-B): both C-R1-03 interpretations

| SW | T2-R I-SUM | T2-R I-MAX | T2-F I-SUM | T2-F I-MAX | legacy G4 bore | T1 | T3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SW1 | -1.760 | -1.560 | -0.870 | -0.820 | -0.360 | regression only (pass false) | NOT_SELECTABLE |
| SW2 | -1.760 | -1.560 | -0.870 | -0.820 | -0.360 | regression only (pass false) | NOT_SELECTABLE |
| SW3 | -1.760 | -1.560 | -0.870 | -0.820 | -0.360 | regression only (pass false) | NOT_SELECTABLE |
| SW4 | -1.760 | -1.560 | -0.870 | -0.820 | -0.360 | regression only (pass false) | NOT_SELECTABLE |
| SW5 | -1.830 | -1.630 | -0.930 | -0.850 | -0.430 | regression only (pass false) | NOT_ELIGIBLE |

Disposition: OWNER_GATED (adjudication n/a, binding I-SUM).

## 9. Charger (L-CHG, G4-B): same-point categories (R3-1) and contract attribution (R4-3)

R3-1 / R3-8 / R4-3: radial and plan prerequisites, the LAND's contract Z prerequisite, the complete same-point neighbour set and the literal closure are separate categories; only literal (contract-mandated + physical predicates at one pose) closes the charger. C-R1-01 2(v) "in plan and in Z" is applied to the non-conductive LAND (its subject); the conductive block is held to item 1 and the common strict 3-D clearance (R3-3: a zero gap is a collision); the block-AND-Z screen is R1 model conservatism (diagnostic, not contract text).

Attribution: C-R1-01 2(v) applies "in plan and in Z" to the NON-CONDUCTIVE LAND (item 2 subject). C-R1-01 item 1 (block) states no plan-AND-Z rule; the R1-H14 row reads "corridors clear in plan and Z" without naming the block, and G4 H20 reads "Charger block, feedthrough and corridors clear". R1 therefore holds the block to the common strict 3-D clearance (physical) and reports the block-AND-Z screen as model conservatism only; whether the conjunctive rule applies to the block (a) or to the strict-wedge alternative (b) is asked in Q-R1-CHARGER, not assumed.

| Contract text relied on | source | verbatim |
| --- | --- | --- |
| C-R1-01 1 (block) | design/mechanical/G4_R1_BRIEF.md | the conductive 4 x 5 mm contact block lies inside the authorized wedge, inside the radial bounds `r_S14_outline + 1.100 <= r <= r_lim - c_chg_window`, and clear of WIFI_RAD (H17); |
| C-R1-01 2 (land subject) | design/mechanical/G4_R1_BRIEF.md | the non-conductive bond/seal land is a caseback-side feature. It need not lie entirely inside the wedge if and only if it (i) carries no conductive material, |
| C-R1-01 2(v) / 2(vi) (land) | design/mechanical/G4_R1_BRIEF.md | (v) clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z, and (vi) clears every neighbouring functional structure (switch bores/bosses, vent, lug and support features); |
| C-R1-01 4 (strict wedge) | design/mechanical/G4_R1_BRIEF.md | the strict-wedge result (land fully inside the wedge) is retained as a diagnostic and as the supplier path: |
| hard-check row R1-H14 | design/mechanical/G4_R1_BRIEF.md | Charger: block inside wedge and outside WIFI_RAD; land per C-R1-01 with overshoot <= caps; corridors clear in plan and Z |
| G4 H20 row | design/mechanical/G4_BRIEF.md | Charger block, feedthrough and corridors clear |

| Category | design point | first D (any wall) | with radial core | with radial core + main seal | threshold / note |
| --- | --- | --- | --- | --- | --- |
| radial prerequisite | true | 49.80 | 50.50 | 51.80 | r_lim >= 24.031 mm (pose ori 0 r +20.550 az +90.000); prerequisite only |
| plan prerequisite | false | 50.95 | 51.55 | n/a | r_lim >= 24.625 mm (pose ori 0 r +21.150 az +89.000), deficit here +0.325 mm, D at the design wall 51.55 mm; prerequisite only |
| LAND Z prerequisite (contract 2(v)) | false | n/a | n/a | n/a | C-R1-01 2(v) Z part (contract, LAND): the land [0, 1.620] mm strictly Z-separated from CHG_ROUTE / CHG_LINK (gap +0.630 mm) and from every 2(v) screw / support; those items share the Z = 0 caseback datum, so Z_gap = max(z_lo - h_land, -H) <= -min(h_land, H) <= 0 and the land's conjunctive (v) clause is unsatisfiable for every pose, D and land width under the retained G4 Z model (contract / owner question Q-R1-CHARGER); not generalized to the block or the strict-wedge alternative |
| complete neighbour set | false | n/a | n/a | n/a | land: 2(v) plan AND Z, 2(vi) strict 3-D; block: strict 3-D against every neighbour; 39 neighbours of the point |
| literal closure (charger closed) | false | n/a | n/a | n/a | contract-mandated + physical predicates at one pose |
| DIAGNOSTIC: literal with the 2(v) Z part waived | false | 50.95 | 51.55 | n/a | DIAGNOSTIC ONLY - consequence quantification for Q-R1-CHARGER: the literal predicate with only the conjunctive Z part of C-R1-01 2(v) waived for a land that is plan-disjoint from the item; never a closure, never credited; C-R1-01 is not amended |
| DIAGNOSTIC: block-AND-Z screen (model conservatism) | false | n/a | n/a | n/a | lead / model conservatism - NOT literal contract text; never decides R1-H14 |
| strict-wedge supplier path (in land range) | true | 48.00 | n/a | n/a | SUPPLIER ZERO-MARGIN THRESHOLD only (SR-CHG-MECH): land < 0.708 mm strictly (at zero margin the inner land corners lie on the wedge sides); never credited as a physical pass; the authored adverse land stays 1.000 mm |
| strict-wedge supplier path (plan) | false | 48.00 | n/a | n/a | failing: {"conservative_model_diagnostic": ["CHG_BLOCK vs CHG_LINK", "CHG_BLOCK vs CHG_ROUTE", "CHG_BLOCK vs SCREW_NE", "CHG_BLOCK vs SCREW_NW", "CHG_BLOCK vs SCREW_SE", "CHG_BLOCK vs SCREW_SW", "CHG_BLOCK vs SUP_NE_CASE_SIDE", "CHG_BLOCK vs SUP_SE_CASE_SIDE", "CHG_BLOCK vs SUP_SW_CASE_SIDE", "CHG_BLOCK vs SUP_WNW_CASE_SIDE"], "contract_mandated": ["CHG_LAND vs CHG_ROUTE", "CHG_LAND vs SCREW_NE", "CHG_LAND vs SCREW_NW", "CHG_LAND vs SCREW_SE", "CHG_LAND vs SCREW_SW", "CHG_LAND vs SUP_NE_CASE_SIDE", "CHG_LAND vs SUP_SE_CASE_SIDE", "CHG_LAND vs SUP_SW_CASE_SIDE", "CHG_LAND vs SUP_WNW_CASE_SIDE"], "physical_required_elsewhere": [], "pose_predicates": ["routes_clear_in_plan"]} |
| strict-wedge supplier path (complete, 2(v) applied to its land) | false | n/a | n/a | n/a | C-R1-01 2(v) applied to the strict-wedge land is the R1 reading pending Q-R1-CHARGER (b) (item 2 conditions govern a land that leaves the wedge; item 4 names the strict wedge a diagnostic / supplier path); the v_z_waived columns show the other reading; neither is a closure |
| DIAGNOSTIC: strict-wedge complete, 2(v) Z part waived | false | 48.00 | n/a | n/a | supplier threshold path; never a closure |

Reported design-point pose (structural land interrupter; closest pose meeting every r_lim-independent radial / plan prerequisite): ori 0, r +21.150, az +89.000, land +1.000, overshoot +0.641 mm; charger closed: false. R1-H14 governing term (contract-mandated, mm): CHG_LAND vs SCREW_NE [plan AND Z] -1.620 mm; azimuth-cap margin +0.013 deg (separate units).

| H14 category | decides physical pass | pass | terms | minimum by units (term, value) | failing terms |
| --- | --- | --- | --- | --- | --- |
| conservative_model_diagnostic | false | n/a | 14 | mm: CHG_BLOCK vs SCREW_NE [plan AND Z] -2.250 | CHG_BLOCK vs CHG_LINK [plan AND Z], CHG_BLOCK vs CHG_ROUTE [plan AND Z], CHG_BLOCK vs SCREW_NE [plan AND Z], CHG_BLOCK vs SCREW_NW [plan AND Z], CHG_BLOCK vs SCREW_SE [plan AND Z], CHG_BLOCK vs SCREW_SW [plan AND Z], CHG_BLOCK vs SUP_NE_CASE_SIDE [plan AND Z], CHG_BLOCK vs SUP_SE_CASE_SIDE [plan AND Z], CHG_BLOCK vs SUP_SW_CASE_SIDE [plan AND Z], CHG_BLOCK vs SUP_WNW_CASE_SIDE [plan AND Z], block_routes_clear_in_z |
| contract_mandated | true | false | 52 | deg: land_azimuth_cap +0.013; mm: CHG_LAND vs SCREW_NE [plan AND Z] -1.620 | CHG_LAND vs CB_SEAL_FLANGE [3-D], CHG_LAND vs SCREW_NE [plan AND Z], CHG_LAND vs SCREW_NW [plan AND Z], CHG_LAND vs SCREW_SE [plan AND Z], CHG_LAND vs SCREW_SW [plan AND Z], CHG_LAND vs SUP_NE_CASE_SIDE [plan AND Z], CHG_LAND vs SUP_SE_CASE_SIDE [plan AND Z], CHG_LAND vs SUP_SW_CASE_SIDE [plan AND Z], CHG_LAND vs SUP_WNW_CASE_SIDE [plan AND Z] |
| physical_required_elsewhere | true | false | 42 | mm: land_flange -0.325 | land_flange |
| supplier_diagnostic | false | n/a | 2 | - | none |

| Failing term (design point) | category | clause | value | units | plan gap mm | Z gap mm |
| --- | --- | --- | --- | --- | --- | --- |
| land_flange | physical_required_elsewhere | G4 c_chg_window_mm (charger aperture / feedthrough land to the caseback seal; G4 8.8 / H20 feedthrough clear) applied to the land outer edge; C-R1-01 1 names r_lim - c_chg_window for the block only | -0.325 | mm | n/a | n/a |
| block_routes_clear_in_z | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: block strictly below the CHG_ROUTE / CHG_LINK conductor band | false | bool | n/a | n/a |
| CHG_LAND vs SCREW_NW [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +35.250 | -1.620 |
| CHG_BLOCK vs SCREW_NW [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +36.640 | -2.250 |
| CHG_LAND vs SCREW_NE [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +20.120 | -1.620 |
| CHG_BLOCK vs SCREW_NE [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +21.378 | -2.250 |
| CHG_LAND vs SCREW_SW [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +35.702 | -1.620 |
| CHG_BLOCK vs SCREW_SW [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +37.086 | -2.250 |
| CHG_LAND vs SCREW_SE [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +20.760 | -1.620 |
| CHG_BLOCK vs SCREW_SE [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +22.037 | -2.250 |
| CHG_LAND vs SUP_SW_CASE_SIDE [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +32.760 | -1.620 |
| CHG_BLOCK vs SUP_SW_CASE_SIDE [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +34.152 | -2.250 |
| CHG_LAND vs SUP_SE_CASE_SIDE [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +18.124 | -1.620 |
| CHG_BLOCK vs SUP_SE_CASE_SIDE [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +19.410 | -2.250 |
| CHG_LAND vs SUP_NE_CASE_SIDE [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +14.015 | -1.620 |
| CHG_BLOCK vs SUP_NE_CASE_SIDE [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +15.158 | -2.250 |
| CHG_LAND vs SUP_WNW_CASE_SIDE [plan AND Z] | contract_mandated | C-R1-01 2(v): the land clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z | -1.620 | mm | +33.939 | -1.620 |
| CHG_BLOCK vs SUP_WNW_CASE_SIDE [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | -2.250 | mm | +35.317 | -2.250 |
| CHG_LAND vs CB_SEAL_FLANGE [3-D] | contract_mandated | C-R1-01 2(vi): the land clears every neighbouring functional structure (strict 3-D clearance) | -0.075 | mm | -0.075 | -1.620 |
| CHG_BLOCK vs CHG_ROUTE [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | +0.000 | mm | +1.176 | +0.000 |
| CHG_BLOCK vs CHG_LINK [plan AND Z] | conservative_model_diagnostic | R1 model conservatism, NOT literal contract text: the block treated like the land under 2(v) (plan AND Z); whether C-R1-01 intends it is Q-R1-CHARGER (a) | +0.000 | mm | +38.169 | +0.000 |

R4-4 land 2(v) Z unsatisfiability: land [0, h_land], screw / support [z_lo, H] with z_lo <= 0 (shared Z = 0 datum): Z_gap = max(z_lo - h_land, -H) <= -min(h_land, H) <= 0; a strictly positive Z gap (R3-3) is impossible, so the conjunctive plan AND Z clause 2(v) cannot hold for the land for any pose, D or land width under the retained G4 Z model (contract / owner question) Scope: LAND (C-R1-01 2(v) subject) only; not generalized to the conductive block, the strict-wedge alternative or other charger structures. Items (z_lo / H / Z gap / -min(h_land, H), mm): SCREW_NW +0.000 / +2.950 / -1.620 / -1.620; SCREW_NE +0.000 / +2.950 / -1.620 / -1.620; SCREW_SW +0.000 / +2.950 / -1.620 / -1.620; SCREW_SE +0.000 / +2.950 / -1.620 / -1.620; SUP_SW_PAD +8.350 / +9.950 / +6.730 / n/a; SUP_SE_PAD +8.350 / +9.950 / +6.730 / n/a; SUP_WNW_PAD +8.350 / +9.950 / +6.730 / n/a; SUP_SW_CASE_SIDE +0.000 / +8.350 / -1.620 / -1.620; SUP_SE_CASE_SIDE +0.000 / +8.350 / -1.620 / -1.620; SUP_NE_CASE_SIDE +0.000 / +8.350 / -1.620 / -1.620; SUP_WNW_CASE_SIDE +0.000 / +8.350 / -1.620 / -1.620.

R4-7 block / route: at the SR-CHG-MECH allocation height (2.250 mm, the conductor band floor) the block has a zero Z gap to CHG_ROUTE / CHG_LINK; it is plan-separated from them, so the common 3-D predicate holds (not a 3-D collision). The zero allocation margin is the separate R1-H01 allocation check. Block route plan gaps {"CHG_BLOCK vs CHG_LINK": 38.169155911, "CHG_BLOCK vs CHG_ROUTE": 1.176475579}; Z gaps {"CHG_BLOCK vs CHG_LINK": 0.0, "CHG_BLOCK vs CHG_ROUTE": 0.0}; strict 3-D clear of the routes: true. Strict-wedge zero-margin land widths (supplier thresholds, not credited; R5 per seal row): face / adhesive rows (shared r_lim 24.300 mm) 0.708 mm; radial rows radial#00 cs 0.50 r_lim 23.540 -> 0.623; radial#01 cs 0.60 r_lim 23.465 -> 0.613; radial#02 cs 0.70 r_lim 23.390 -> 0.603; radial#03 cs 0.80 r_lim 23.310 -> 0.593; radial#04 cs 0.90 r_lim 23.230 -> 0.582; radial#05 cs 1.00 r_lim 23.155 -> 0.573; radial#06 cs 1.10 r_lim 23.075 -> 0.553; radial#07 cs 1.20 r_lim 23.000 -> 0.518; radial governing supplier threshold = min over the authorized radial rows 0.518 mm (radial#07), envelope 0.518..0.623 mm; adverse authored land 1.000 mm. Poses: 2662 evaluated, 35 meet every r_lim-independent prerequisite, 35 meet every pose-level contract / physical predicate. Feedthrough FT-C.

## 10. LRA (L-LRA, G4-B)

| Envelope | value mm | search result | delta_Z to the authored minimum class mm | label |
| --- | --- | --- | --- | --- |
| authored_grid_maximum | +1.030 | true | +1.470 | authored-grid maximum: V12 t_out x V22 pocket depth, residual >= LA-LRA-1 floor, LA-Z-2 band; Z only, BEFORE structural qualification |
| continuous_upper_bound | +1.110 | false | +1.390 | continuous mathematical upper bound: residual exactly t_wall_min(max) + thickness tol (LA-LRA-1) under the LA-Z-2 band; not reachable on the authored grids; not a search result |
| historical_optimistic | +2.080 | false | +0.420 | historical optimistic bound: 0.5 mm residual, no LA-LRA-1 floor, no LA-Z-2 band; never a search result |
| selected_design_point | +0.930 | true | +1.570 | selected structural plate (t_out 1.60) with its deepest admissible pocket; before structural qualification |
| structurally_feasible_searched | n/a | true | n/a | maximum over the joint search of combinations that pass the structural re-screen; null = no structurally feasible combination |

| Material | residual floor mm | continuous upper bound mm | authored-grid maximum mm | argmax t_out / depth | continuous without band | lead formula without band | historical 0.5 residual |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MAT-CERAMIC | +0.820 | +1.110 | +1.030 | 0.90 / 0.00 | +1.760 | +1.780 | +2.080 |
| MAT-GF-POLY | +1.050 | +0.850 | +0.800 | 1.10 / 0.00 | +1.500 | +1.550 | +2.050 |
| MAT-NF-METAL | +0.720 | +1.210 | +1.130 | 0.80 / 0.00 | +1.860 | +1.880 | +2.080 |

| Class | supplied | plan poses | envelope height | H before structure | Z margin before structure | structurally feasible fits | fits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LRA-COIN-D8 | false | 0 | +3.200 | n/a | n/a | 0 | false |
| LRA-COIN-D10 | false | 0 | +3.600 | n/a | n/a | 0 | false |
| LRA-LIN-RECT | false | 44 | +3.200 | +1.030 | -2.170 | 0 | false |

Structural re-screen: COMPLIANCE_BOUND on 4620 combinations (design-point bound 0.077 mm vs 0.050 mm). OD-G4-LRA-ARCH triggered: true (question raised, not decided).

## 11. Assembly (L-ASM, G4-B)

| Op | direction | battery | sequence pass | dependency gate |
| --- | --- | --- | --- | --- |
| A1 | bench | absent | true | FAILED Q-R1-STRUCTURE (R1-S07 / R1-S05) |
| A2 | interior (rear opening) | absent | true | n/a |
| A3 | bench | absent | true | n/a |
| A4 | bench | isolated | true | n/a |
| A5 | undefined (no feasible LRA pose) | isolated | true | GATED OD-G4-LRA-ARCH (R1-S08) |
| A6 | +Z from rear (wrist side) toward front | isolated | true | n/a |
| A7 | -Z from front | isolated | true | n/a |
| A8 | -Z from front | isolated | true | n/a |
| A9 | radial inward from outside | isolated | true | FAILED Q-R1-BUTTON-ENVELOPE (R1-S03) |
| A10 | rear (caseback open) | connected | true | FAILED Q-R1-CHARGER (R1-S04) |
| A11 | +Z from rear | connected | true | FAILED Q-R1-MAIN-SEAL (R1-S06); FAILED Q-R1-CHARGER (R1-S04); FAILED Q-R1-STRUCTURE (R1-S07 / R1-S05) |

| Step | requires | state | gate |
| --- | --- | --- | --- |
| A1 | W1 window bonded into the caseback pod frame (L-WIN) | RESOLVED | n/a |
| A1 | structurally feasible caseback sub-assembly (L-STR, R1-H09) | FAILED | Q-R1-STRUCTURE (R1-S07 / R1-S05) |
| A5 | LRA bonded into a feasible pocket pose (L-LRA) | GATED | OD-G4-LRA-ARCH (R1-S08) |
| A9 | selectable button topology per switch (L-BTN) | FAILED | Q-R1-BUTTON-ENVELOPE (R1-S03) |
| A10 | functional test through a feasible charger contact block (L-CHG, complete C-R1-01 closure) | FAILED | Q-R1-CHARGER (R1-S04) |
| A11 | caseback closed with a feasible S-CB-MAIN seal (L-SEAL) | FAILED | Q-R1-MAIN-SEAL (R1-S06) |
| A11 | S-CHG bonded feedthrough of a feasible charger (L-CHG) | FAILED | Q-R1-CHARGER (R1-S04) |
| A11 | structurally feasible caseback closing the pressure boundary (L-STR, R1-H09) | FAILED | Q-R1-STRUCTURE (R1-S07 / R1-S05) |

Identity vs accepted A1..A11: true. Sequence executable on its own geometry: true. Product closure executable: false. Disposition OWNER_GATED. SERVICE-COVER-REBOND remains OPEN: display replacement requires cover removal and re-bond

## 12. Lead cross-checks (S20)

| Check | expected | computed | status | explanation |
| --- | --- | --- | --- | --- |
| PACK rcin 23.10 | -0.200 | -0.200 | REPRODUCED |  |
| PACK rcin 23.30 | +0.000 | +0.000 | REPRODUCED |  |
| carrier wall solved | +0.350 | +0.350 | REPRODUCED |  |
| H05-STRAIGHT (bulk) D50.90 tw1.10 rcin23.30 | +0.050 | +0.050 | REPRODUCED |  |
| H23-INSERT-BATTERY D50.90 tw1.10 | +0.200 | +0.200 | REPRODUCED |  |
| total caseback reaction | +1168.990 | +1168.987 | REPRODUCED |  |
| no-rib bypass stress (G4-B) | +622.918 | +622.918 | REPRODUCED |  |
| no-rib bypass deflection (G4-B) | +0.283 | +0.283 | REPRODUCED |  |
| old invalid t_eq (16 spokes, w0.8, h1.0, t0.8) | +1.226 | +1.226 | REPRODUCED |  |
| old invalid t_eq stress (diagnostic) | +329.330 | +329.334 | REPRODUCED |  |
| old invalid t_eq deflection (diagnostic) | +0.116 | +0.116 | REPRODUCED |  |
| required uniform isotropic thickness MAT-CERAMIC | +1.820 | +1.816 | REPRODUCED |  |
| required uniform isotropic thickness MAT-NF-METAL | +1.960 | +1.956 | REPRODUCED |  |
| required uniform isotropic thickness MAT-GF-POLY | +4.710 | +4.707 | REPRODUCED |  |
| rigid outer annulus lower bound MAT-CERAMIC (t_in 0.9) | +118.000 | +78.119 | EXPLAINED | Not reproduced exactly: the idealisation is not specified. The inner region (rb..r_step, t_in 0.9 - tol, loaded boss) gives 78.1 MPa clamped and 171.3 MPa simply supported at r_step; the lead value lies between these bounds. Every bound exceeds the polymer 35 MPa allowable; the corrected Screen B result governs. |
| rigid outer annulus lower bound MAT-NF-METAL (t_in 0.9) | +118.600 | +78.119 | EXPLAINED | Not reproduced exactly: the idealisation is not specified. The inner region (rb..r_step, t_in 0.9 - tol, loaded boss) gives 78.1 MPa clamped and 170.5 MPa simply supported at r_step; the lead value lies between these bounds. Every bound exceeds the polymer 35 MPa allowable; the corrected Screen B result governs. |
| rigid outer annulus lower bound MAT-GF-POLY (t_in 0.9) | +126.000 | +83.730 | EXPLAINED | Not reproduced exactly: the idealisation is not specified. The inner region (rb..r_step, t_in 0.9 - tol, loaded boss) gives 83.7 MPa clamped and 181.1 MPa simply supported at r_step; the lead value lies between these bounds. Every bound exceeds the polymer 35 MPa allowable; the corrected Screen B result governs. |
| face seal required tw (smallest feasible gland cs 0.9) | +2.090 | +2.090 | REPRODUCED |  |
| face seal margin at tw 1.35 | -0.740 | -0.740 | REPRODUCED |  |
| adhesive required tw | +1.540 | +1.540 | REPRODUCED |  |
| adhesive margin at tw 1.35 | -0.190 | -0.190 | REPRODUCED |  |
| radial gland smallest feasible cs | +1.500 | +1.500 | REPRODUCED |  |
| radial spigot rear-periphery Z at cs 1.5 | -1.050 | -1.050 | REPRODUCED |  |
| strict-wedge land A/C (chg_r_out 24.0) | +0.674 | +0.674 | REPRODUCED |  |
| strict-wedge land B (radial chg_r_out 23.34) | +0.589 | +0.623 | EXPLAINED | The accepted g4.charger_fit applies the caseback process position tolerance (ceramic grind 0.02 mm) and gives 0.6225 mm; the lead value is reproduced with a 0.05 mm (polymer) position tolerance: 0.5887 mm. |
| charger ori-0 minimum centre radius for the continuous 1.0 land (G4-B) | +20.520 | +20.521 | REPRODUCED |  |
| button SW1 I-SUM before boot height (boss 0.95) | +0.040 | +0.040 | REPRODUCED |  |
| button SW1 I-MAX before boot height (boss 0.95) | +0.240 | +0.240 | REPRODUCED |  |
| button SW5 I-SUM before boot height (boss 0.90) | -0.080 | -0.080 | REPRODUCED |  |
| button SW5 I-MAX before boot height (boss 0.90) | +0.120 | +0.120 | REPRODUCED |  |
| LRA historical optimistic bound (0.5 residual, no band; not a search result) | +2.080 | +2.080 | REPRODUCED |  |
| LRA lead formula without LA-Z-2 band MAT-CERAMIC (historical, not a search result) | +1.780 | +1.780 | REPRODUCED |  |
| LRA lead formula without LA-Z-2 band MAT-NF-METAL (historical, not a search result) | +1.880 | +1.880 | REPRODUCED |  |
| LRA lead formula without LA-Z-2 band MAT-GF-POLY (historical, not a search result) | +1.550 | +1.550 | REPRODUCED |  |
| LRA continuous upper bound LA-LRA-1 + LA-Z-2 MAT-CERAMIC (not a search result) | +1.110 | +1.110 | REPRODUCED |  |
| LRA authored-grid maximum MAT-CERAMIC (searched, before structural qualification) | +1.030 | +1.030 | REPRODUCED |  |
| LRA continuous upper bound LA-LRA-1 + LA-Z-2 MAT-NF-METAL (not a search result) | +1.210 | +1.210 | REPRODUCED |  |
| LRA authored-grid maximum MAT-NF-METAL (searched, before structural qualification) | +1.130 | +1.130 | REPRODUCED |  |
| LRA continuous upper bound LA-LRA-1 + LA-Z-2 MAT-GF-POLY (not a search result) | +0.850 | +0.850 | REPRODUCED |  |
| LRA authored-grid maximum MAT-GF-POLY (searched, before structural qualification) | +0.800 | +0.800 | REPRODUCED |  |
| LRA selected design-point envelope G4-B (ceramic plate / deepest admissible pocket) | +0.930 | +0.930 | REPRODUCED |  |
| LRA structurally feasible searched envelope G4-B (null = none; encoded -1) | -1.000 | -1.000 | REPRODUCED |  |
| charger plan-prerequisite r_lim required (G4-B; prerequisite only, not a closure) | +24.625 | +24.625 | REPRODUCED |  |
| charger plan-prerequisite pose r_centre (G4-B) | +21.150 | +21.150 | REPRODUCED |  |
| charger plan-prerequisite pose az_centre (G4-B) | +89.000 | +89.000 | REPRODUCED |  |
| charger plan-prerequisite r_lim required (G4-A; prerequisite only, not a closure) | +24.857 | +24.857 | REPRODUCED |  |
| charger plan-prerequisite pose r_centre (G4-A) | +21.350 | +21.350 | REPRODUCED |  |
| charger plan-prerequisite pose az_centre (G4-A) | +89.000 | +89.000 | REPRODUCED |  |
| charger plan-prerequisite r_lim required (G4-C1; prerequisite only, not a closure) | +24.857 | +24.857 | REPRODUCED |  |
| charger plan-prerequisite pose r_centre (G4-C1) | +21.350 | +21.350 | REPRODUCED |  |
| charger plan-prerequisite pose az_centre (G4-C1) | +89.000 | +89.000 | REPRODUCED |  |
| strict-wedge supplier zero-margin land width at the design point (G4-B; threshold only, not credited) | +0.708 | +0.708 | REPRODUCED |  |
| strict-wedge supplier zero-margin land width at the design point (G4-A; threshold only, not credited) | +0.674 | +0.674 | REPRODUCED |  |
| strict-wedge supplier zero-margin land width at the design point (G4-C1; threshold only, not credited) | +0.674 | +0.674 | REPRODUCED |  |
| selected-point Screen B stress (G4-B design point) | +371.784 | +371.784 | REPRODUCED |  |
| selected-point Screen B deflection (G4-B design point) | +0.120 | +0.120 | REPRODUCED |  |
| first main-seal grid closure D (G4-B, adhesive option) | +51.800 | +51.800 | REPRODUCED |  |
| first main-seal closure is the adhesive option only (1 = adhesive alone) | +1.000 | +1.000 | REPRODUCED |  |
| button zero-margin nominal D (T2-R) | +54.560 | +54.560 | REPRODUCED |  |
| T3 flexure web threshold (not manufacturability evidence) | +9.762e-03 | +9.762e-03 | REPRODUCED |  |
| H05 metal arc floor (G4-B) | +0.740 | +0.740 | REPRODUCED |  |
| XF edge margin at the arc floor (G4-B) | +0.290 | +0.290 | REPRODUCED |  |
| XB edge margin at the arc floor (G4-B) | +0.290 | +0.290 | REPRODUCED |  |
| G4-A H05-GEOM minimum at D50.90 (bulk XF / XB) | -0.080 | -0.080 | REPRODUCED |  |
| W1 sapphire stress | +23.394 | +23.394 | REPRODUCED |  |
| W1 sapphire deflection | +5.188e-04 | +5.188e-04 | REPRODUCED |  |
| W1 cs_glass stress | +22.898 | +22.898 | REPRODUCED |  |
| W1 cs_glass deflection | +2.989e-03 | +2.989e-03 | REPRODUCED |  |
| W1 polycarbonate stress | +23.961 | +23.961 | REPRODUCED |  |
| W1 polycarbonate deflection | +0.073 | +0.073 | REPRODUCED |  |
| W1 nominal web comparison | +0.181 | +0.181 | REPRODUCED |  |
| W1 bond-land arithmetic (polymer frame) | +0.150 | +0.150 | REPRODUCED |  |
| W1 Z delta | +0.000 | +0.000 | REPRODUCED |  |
| face O-ring compression min % | +16.842 | +16.842 | REPRODUCED |  |
| face O-ring compression max % | +28.571 | +28.571 | REPRODUCED |  |
| face O-ring fill % | +84.273 | +84.273 | REPRODUCED |  |
| polymer required diameter (H05-GEOM, G4-A) | +51.100 | +51.100 | REPRODUCED |  |

## 13. Owner questions (named, not decided)

- **Q-R1-BUTTON-ENVELOPE** (OD-G4-ENVELOPE, SR-BUTTONS, R1-S03): No T2 / T3 button topology closes inside the frozen switch windows and the +1.0 mm boss limit. Options to be decided by the owner (not by R1): relax the boss limit / body diameter, supply boot or flexure evidence, or accept another button architecture. Thresholds: {"T2_F_max_boot_free_height_mm": -0.03, "T2_R_required_D_mm": 54.56, "T2_R_required_boss_mm": 2.78, "T3_web_max_mm": 0.009761815, "worst_switch": "SW5"}
- **Q-R1-MAIN-SEAL** (OD-G4-ENVELOPE, OD-G4-STACK, serviceability, R1-S06): No caseback main-seal topology closes at <= 51.00 mm with zero Z delta: face / adhesive need a wider midcase rear-face annulus (diameter), the radial spigot needs Z (OD-G4-STACK); adhesive is non-serviceable. Thresholds: {"adhesive_required_tw_mm": 1.58, "charger_with_main_seal_first_D_mm": null, "face_required_tw_mm": 2.13, "main_seal_first_pass": {"D": 51.8, "label": "adhesive (non-serviceable)", "topologies": ["adhesive"], "tw": 1.6}, "main_seal_first_pass_D_mm": 51.8, "main_seal_with_radial_core_first_D_mm": 51.8, "note": "first closures are report-only extension diameters above the 51.00 mm owner ceiling; quantified, not decided", "radial_min_cs_mm": 1.5, "radial_z_margin_mm": -1.15}
- **Q-R1-STRUCTURE** (OD-G4-MATERIAL, OD-G4-STACK, FEA-1..FEA-4, R1-S05, R1-S07): No stiffened caseback passes the loaded-boss planning screens with no ring credit; the inner region is limited by the pod residual. Material class / Z allocation / load-path architecture are owner decisions. Thresholds: {"allowable_MPa": 150, "deflection_limit_mm": 0.05, "material": "MAT-CERAMIC", "other_materials": {"MAT-CERAMIC": 1.836113015, "MAT-GF-POLY": 4.756778589, "MAT-NF-METAL": 1.976283312}, "required_uniform_nominal_thickness_mm": 1.836113015, "screen_B_sigma_MPa": 371.783849756, "screen_B_w_mm": 0.11981656, "t_in_max_mm": 1.1}
- **Q-R1-CHARGER** (SR-CHG-MECH, OD-G4-ENVELOPE, C-R1-01 2(v), C-R1-01 1, C-R1-01 4, R1-S04): (1) Does C-R1-01 2(v) intentionally require positive PLAN AND positive Z separation of the non-conductive charger land from screws / supports even when they are already disjoint in plan? Under the retained G4 common-Z geometry (land Z 0..1.620 mm; SCREW_NE, SCREW_NW, SCREW_SE, SCREW_SW, SUP_NE_CASE_SIDE, SUP_SE_CASE_SIDE, SUP_SW_CASE_SIDE, SUP_WNW_CASE_SIDE occupy Z from the same Z = 0 caseback datum) Z_gap = max(-h_land, -H) = -min(h_land, H) <= 0, so the land condition is unsatisfiable for every pose, D and land width (land Z gap -1.620 mm while the plan gaps are +14.015..+35.702 mm). (2) Does the same conjunctive plan-AND-Z condition apply (a) to the conductive charger block - C-R1-01 item 1 states no plan-AND-Z rule for the block; R1 holds it to the common strict 3-D clearance (met at the design point: true) and reports the block-AND-Z screen as model conservatism only (block Z gap -2.250 mm to the 2(v) items, +0.000 mm to CHG_ROUTE / CHG_LINK at its SR-CHG-MECH allocation height) - and (b) to the strict-wedge supplier alternative of C-R1-01 item 4 (land < 0.708 mm strictly, never credited)? R1 does not assume the answers, does not amend the contract and does not choose geometry; a formal clarification / amendment is required before any charger closure is claimed under different semantics. Quantified consequences (diagnostics, not closures): under the literal contract the complete predicate closes at none through 52.50 mm; with only the conjunctive Z part of 2(v) waived for a plan-disjoint land the remaining predicates first hold at D 50.95 mm (with the radial core D 51.55 mm; with the radial core and the main seal none through 52.50 mm); the strict-wedge path completes at none through 52.50 mm with 2(v) applied to its land and at D 48.00 mm without its Z part (with the radial core none through 52.50 mm). Independently of 2(v): the radial / plan prerequisites first hold at D 50.95 mm (with the radial core D 51.55 mm; r_lim >= 24.625 mm); at the design point the land's 2(vi) 3-D clearance to the caseback seal flange is -0.075 mm and the land-flange radial term is -0.325 mm. Thresholds: {"adverse_land_mm": 1.0, "block_and_z_diagnostic": {"block_3d_clear_of_routes": true, "block_top_mm": 2.25, "conductor_band_floor_mm": 2.25, "label": "lead / model conservatism - NOT literal contract text; never decides R1-H14", "note": "at the SR-CHG-MECH allocation height (2.250 mm, the conductor band floor) the block has a zero Z gap to CHG_ROUTE / CHG_LINK; it is plan-separated from them, so the common 3-D predicate holds (not a 3-D collision). The zero allocation margin is the separate R1-H01 allocation check.", "pass_": false, "route_plan_gaps_mm": {"CHG_BLOCK vs CHG_LINK": 38.169155911, "CHG_BLOCK vs CHG_ROUTE": 1.176475579}, "route_z_gaps_mm": {"CHG_BLOCK vs CHG_LINK": 0.0, "CHG_BLOCK vs CHG_ROUTE": 0.0}, "v_item_min_z_gap_mm": -2.25}, "complete_closure": {"first_D": null, "first_D_with_radial_core": null, "first_D_with_radial_core_and_main_seal": null, "neighbour_complete_first_D": null, "pass_": false}, "coupled_first_D_mm": {"charger_with_main_seal": null, "charger_with_od": null, "charger_with_radial_core": null, "charger_with_radial_core_and_main_seal": null, "charger_with_radial_core_and_od": null, "main_seal_with_radial_core": 51.8, "rule": "first grid D (primary or report-only extension to 52.50 mm) with the named groups passing at one common bulk wall; CHARGER is the complete literal C-R1-01 closure of that point (R3-1); null = none on the grid"}, "land_v_z_unsatisfiability": {"h_land_mm": 1.62, "items": [{"H_mm": 2.95, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SCREW_NW", "kind": "caseback screw", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}, {"H_mm": 2.95, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SCREW_NE", "kind": "caseback screw", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}, {"H_mm": 2.95, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SCREW_SW", "kind": "caseback screw", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}, {"H_mm": 2.95, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SCREW_SE", "kind": "caseback screw", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}, {"H_mm": 9.95, "bound_mm": null, "closed_form_mm": 6.73, "id": "SUP_SW_PAD", "kind": "support pad", "shares_datum": false, "unsatisfiable": false, "z_gap_mm": 6.73, "z_lo_adv_mm": 8.35}, {"H_mm": 9.95, "bound_mm": null, "closed_form_mm": 6.73, "id": "SUP_SE_PAD", "kind": "support pad", "shares_datum": false, "unsatisfiable": false, "z_gap_mm": 6.73, "z_lo_adv_mm": 8.35}, {"H_mm": 9.95, "bound_mm": null, "closed_form_mm": 6.73, "id": "SUP_WNW_PAD", "kind": "support pad", "shares_datum": false, "unsatisfiable": false, "z_gap_mm": 6.73, "z_lo_adv_mm": 8.35}, {"H_mm": 8.35, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SUP_SW_CASE_SIDE", "kind": "case-side support", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}, {"H_mm": 8.35, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SUP_SE_CASE_SIDE", "kind": "case-side support", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}, {"H_mm": 8.35, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SUP_NE_CASE_SIDE", "kind": "case-side support", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}, {"H_mm": 8.35, "bound_mm": -1.62, "closed_form_mm": -1.62, "id": "SUP_WNW_CASE_SIDE", "kind": "case-side support", "shares_datum": true, "unsatisfiable": true, "z_gap_mm": -1.62, "z_lo_adv_mm": 0.0}], "rule": "land [0, h_land], screw / support [z_lo, H] with z_lo <= 0 (shared Z = 0 datum): Z_gap = max(z_lo - h_land, -H) <= -min(h_land, H) <= 0; a strictly positive Z gap (R3-3) is impossible, so the conjunctive plan AND Z clause 2(v) cannot hold for the land for any pose, D or land width under the retained G4 Z model (contract / owner question)", "scope": "LAND (C-R1-01 2(v) subject) only; not generalized to the conductive block, the strict-wedge alternative or other charger structures", "unsatisfiable": true}, "plan_prerequisite": {"deficit_mm": 0.324972876, "first_plan": 50.95, "first_plan_with_radial_core": 51.55, "first_plan_with_radial_core_and_main_seal": null, "first_plan_with_radial_core_and_od": null, "pose": {"az_centre": 89.0, "land": 1.0, "orientation": 0, "r_centre": 21.15}, "r_lim_required_mm": 24.624972876, "required_D_at_design_wall_mm": 51.549945752}, "radial_prerequisite": {"deficit_mm": -0.268606839, "first_radial": 49.8, "first_radial_with_radial_core": 50.5, "pose": {"az_centre": 90.0, "land": 1.0, "orientation": 0, "r_centre": 20.55}, "r_lim_required_mm": 24.031393161, "required_D_at_design_wall_mm": 50.362786322}, "strict_wedge_supplier_path": {"complete": false, "complete_v_z_waived": false, "contained_in_wedge": true, "failing_terms_by_category": {"conservative_model_diagnostic": ["CHG_BLOCK vs CHG_LINK", "CHG_BLOCK vs CHG_ROUTE", "CHG_BLOCK vs SCREW_NE", "CHG_BLOCK vs SCREW_NW", "CHG_BLOCK vs SCREW_SE", "CHG_BLOCK vs SCREW_SW", "CHG_BLOCK vs SUP_NE_CASE_SIDE", "CHG_BLOCK vs SUP_SE_CASE_SIDE", "CHG_BLOCK vs SUP_SW_CASE_SIDE", "CHG_BLOCK vs SUP_WNW_CASE_SIDE"], "contract_mandated": ["CHG_LAND vs CHG_ROUTE", "CHG_LAND vs SCREW_NE", "CHG_LAND vs SCREW_NW", "CHG_LAND vs SCREW_SE", "CHG_LAND vs SCREW_SW", "CHG_LAND vs SUP_NE_CASE_SIDE", "CHG_LAND vs SUP_SE_CASE_SIDE", "CHG_LAND vs SUP_SW_CASE_SIDE", "CHG_LAND vs SUP_WNW_CASE_SIDE"], "physical_required_elsewhere": [], "pose_predicates": ["routes_clear_in_plan"]}, "first_D_complete": null, "first_D_complete_v_z_waived": 48.0, "first_D_in_land_range": 48.0, "first_D_plan": 48.0, "in_land_range": true, "neighbours": false, "plan": false, "threshold": "SUPPLIER ZERO-MARGIN THRESHOLD only (SR-CHG-MECH): land < 0.708 mm strictly (at zero margin the inner land corners lie on the wedge sides); never credited as a physical pass; the authored adverse land stays 1.000 mm", "v_applicability": "C-R1-01 2(v) applied to the strict-wedge land is the R1 reading pending Q-R1-CHARGER (b) (item 2 conditions govern a land that leaves the wedge; item 4 names the strict wedge a diagnostic / supplier path); the v_z_waived columns show the other reading; neither is a closure", "width_mm": 0.707852056, "z": false}, "strict_wedge_widths_mm": {"at_face_adhesive_r_lim": 0.707852056, "at_radial_r_lim": {"envelope_mm": [0.517943168, 0.622537418], "governing_rows": ["radial#07"], "governing_threshold_mm": 0.517943168, "rows": [{"chg_r_out_mm": 23.34, "cs_mm": 0.5, "r_lim_mm": 23.54, "row": "radial#00", "width_mm": 0.622537418}, {"chg_r_out_mm": 23.265, "cs_mm": 0.6, "r_lim_mm": 23.465, "row": "radial#01", "width_mm": 0.612842568}, {"chg_r_out_mm": 23.19, "cs_mm": 0.7, "r_lim_mm": 23.39, "row": "radial#02", "width_mm": 0.603147717}, {"chg_r_out_mm": 23.11, "cs_mm": 0.8, "r_lim_mm": 23.31, "row": "radial#03", "width_mm": 0.592806542}, {"chg_r_out_mm": 23.03, "cs_mm": 0.9, "r_lim_mm": 23.23, "row": "radial#04", "width_mm": 0.582465366}, {"chg_r_out_mm": 22.955, "cs_mm": 1.0, "r_lim_mm": 23.155, "row": "radial#05", "width_mm": 0.572770512}, {"chg_r_out_mm": 22.875, "cs_mm": 1.1, "r_lim_mm": 23.075, "row": "radial#06", "width_mm": 0.55338904}, {"chg_r_out_mm": 22.8, "cs_mm": 1.2, "r_lim_mm": 23.0, "row": "radial#07", "width_mm": 0.517943168}], "rows_without_fit": []}, "face_adhesive_r_lim_mm": 24.3, "rule": "per authorized radial row: strict-wedge zero-margin land width at chg_r_out = min(CHG_CONTACT r1, r_lim(r) - c_chg_window); governing supplier threshold = min over the rows (land < value strictly for every authorized radial row); envelope [min, max]"}, "v_z_waived_diagnostic": {"design_point": false, "first_D": 50.95, "first_D_with_radial_core": 51.55, "first_D_with_radial_core_and_main_seal": null, "first_D_with_radial_core_and_od": null, "label": "DIAGNOSTIC ONLY - consequence quantification for Q-R1-CHARGER: the literal predicate with only the conjunctive Z part of C-R1-01 2(v) waived for a land that is plan-disjoint from the item; never a closure, never credited; C-R1-01 is not amended"}, "z_prerequisite": {"first_D": null, "land_top_mm": 1.62, "pass_": false, "route_z_gaps_mm": {"CHG_BLOCK vs CHG_LINK": 0.0, "CHG_BLOCK vs CHG_ROUTE": 0.0, "CHG_LAND vs CHG_LINK": 0.63, "CHG_LAND vs CHG_ROUTE": 0.63}, "threshold": "C-R1-01 2(v) Z part (contract, LAND): the land [0, 1.620] mm strictly Z-separated from CHG_ROUTE / CHG_LINK (gap +0.630 mm) and from every 2(v) screw / support; those items share the Z = 0 caseback datum, so Z_gap = max(z_lo - h_land, -H) <= -min(h_land, H) <= 0 and the land's conjunctive (v) clause is unsatisfiable for every pose, D and land width under the retained G4 Z model (contract / owner question Q-R1-CHARGER); not generalized to the block or the strict-wedge alternative", "v_item_min_z_gap_mm": {"land": -1.62}, "z_unsatisfiable_items": ["SCREW_NE", "SCREW_NW", "SCREW_SE", "SCREW_SW", "SUP_NE_CASE_SIDE", "SUP_SE_CASE_SIDE", "SUP_SW_CASE_SIDE", "SUP_WNW_CASE_SIDE"]}}
- **OD-G4-LRA-ARCH** (R1-S08, OD-G4-STACK, G2 reallocation study, Q-R1-STRUCTURE): No authored or supplied LRA class fits any pose at the current G2 allocation (pocket included; structural re-screen applied). Raised as a question; R1 does not choose among the options. Thresholds: {"authored_grid_label": "authored-grid maximum: V12 t_out x V22 pocket depth, residual >= LA-LRA-1 floor, LA-Z-2 band; Z only, BEFORE structural qualification", "authored_grid_maximum_mm": 1.03, "continuous_upper_bound_mm": 1.11, "delta_Z_mm": {"authored_grid_maximum": 1.47, "continuous_upper_bound": 1.39, "historical_optimistic": 0.42, "selected_design_point": 1.57, "structurally_feasible_searched": null}, "historical_optimistic_mm": 2.08, "option_set": ["supplier evidence (C-R1-08, lead / exit included) of a class with envelope height <= 1.030 mm (authored-grid maximum, MAT-CERAMIC, before structural qualification; continuous upper bound 1.110 mm) and a footprint fitting a reported pose window, together with a structurally feasible caseback (Q-R1-STRUCTURE)", "G2 REAR-band reallocation study (any REAR-driven growth needs OD-G4-STACK; T_total headroom 0.150 / 0.120)", "haptic-free Rev-A"], "selected_design_point_mm": 0.93, "structurally_feasible_searched_mm": null}

### 13.1 Owner-question readiness (R4-12; nothing decided or adopted)

| Question | raised | ready | decided | basis | open |
| --- | --- | --- | --- | --- | --- |
| Q-R1-BUTTON-ENVELOPE | true | true | false | T2-R zero-margin D +54.560 mm / boss +2.780 mm; T2-F boot free height -0.030 mm; T3 web +0.010 mm; worst switch SW5 | owner: boss limit / body diameter / button architecture; SR-BUTTONS evidence |
| Q-R1-MAIN-SEAL | true | true | false | typed R1-H11 terms; adhesive wall +1.580 mm, face wall +2.130 mm, radial cs >= +1.500 mm with REAR-periphery Z -1.150 mm; first grid closure D 51.80 mm (adhesive (non-serviceable)) | owner: diameter / Z (OD-G4-STACK) / serviceability trade-off |
| Q-R1-STRUCTURE | true | true | false | uniform MAT-CERAMIC caseback +1.836 mm nominal vs t_in +1.100 mm; Screen B +371.784 MPa / +0.120 mm vs +150.000 MPa / +0.050 mm | owner: OD-G4-MATERIAL / OD-G4-STACK / load path; FEA-1..4 |
| Q-R1-CHARGER | true | true | false | contract scope represented: LAND 2(v) failure (-1.620 mm, CHG_LAND vs SCREW_NE [plan AND Z]) decides R1-H14; block / strict-wedge applicability asked, not assumed; block-AND-Z screen labelled model conservatism; prerequisite r_lim +24.625 mm; consequences quantified as diagnostics | owner / contract: C-R1-01 2(v) semantics (1), block (2a), strict wedge (2b); SR-CHG-MECH evidence |
| OD-G4-LRA-ARCH | true | true | false | 9.8 trigger met: no authored / supplied class fits (structurally feasible searched envelope n/a); authored-grid maximum +1.030 mm, delta_Z +1.470 mm; continuous bound +1.110 mm; option set listed, none chosen | architecture: OD-G4-LRA-ARCH option (R1 does not choose) |
| OD-G4-STACK | true | true | false | quantified sub-questions only; no decision adopted; any nonzero total Z needs OD-G4-STACK and a G2 allocation study | owner: OD-G4-STACK (not triggered by R1; R1-S05 records the Z need) |

| OD-G4-STACK sub-question | question | value mm | basis |
| --- | --- | --- | --- |
| STACK-SEAL-RADIAL | Z for the radial spigot main seal | -1.150 | REAR-periphery Z margin at the smallest feasible radial cs |
| STACK-STRUCTURE | caseback thickness / Z over the pod (inner region) for a uniform plate | +0.736 | required uniform nominal +1.836 mm vs t_in <= +1.100 mm by the pod residual (inner region); periphery Z available +2.230 mm (shortfall there +0.000 mm) |
| STACK-LRA | REAR Z for an authored LRA class | +1.470 | delta_Z vs the authored-grid maximum; T_total headroom 0.150 / 0.120 |


## 14. Model decisions

- Local arcs (C-R1-04) span the corridor reservation Z levels (MAIN, BATTERY); when the crossing envelope cannot pass the bulk REAR-level bore at rear insertion the arc is extended through the rear face, reducing the rear-face seal annulus there.
- V03 (R2-2): the local wall is searched on the contracted grid floor .. tw step 0.02 by an exact reduction. Every decreasing own predicate (edge, straight, t_allow, insertion through the arc) is affine in t with slope -1 (R_side = D/2 - t), the wall predicate affine with slope +1, hoop and panel stresses fall strictly with t; the own-feasible set is therefore the interval [t_lo, t_hi]. Coupled predicates are monotone: the rear-face seal annulus and the radial spigot bore rise with t and the structural plate radius falls with t. A through-rear-face arc takes t_hi; a MAIN / BATTERY arc (no coupled predicate) takes the grid max-min of its own mm margins; an empty interval is diagnostic (H05-GEOM fails there for every thickness). The floor is NOT claimed optimal for every predicate (wall, hoop, panel, annulus and plate radius all favour a thicker arc). The affine model is verified against production predicates at the selected point, the last grid point and the t_hi bracket; STRUCTURE is re-screened at every plate radius reachable by an admissible arc thickness.
- H05 straight-run and edge crossings are evaluated at the non-LRA risers inside the local arcs; the U7 riser straight run and XL-LRA lateral / Z terms are H05-LRA-COUPLED (R1-H05), never blended into H05-GEOM.
- The charger contact block is a caseback feedthrough (FT-B / FT-C), not module-carried; the REAR insertion envelope uses the S14 outline and the REAR conductor reservations (the G4-literal module-carried value is reported beside it).
- R4-3: C-R1-01 2(v) "in plan and in Z" is applied to its subject, the NON-CONDUCTIVE LAND (contract-mandated; a Z separation never waives a plan collision, exact g4.overlaps, touching counts). The conductive block is held to C-R1-01 item 1 and to the common strict 3-D clearance (plan OR Z; G4 8.8 / H20 "block ... clear"), because no contract clause states a plan-AND-Z rule for it; the block-AND-Z screen is reported as R1 model conservatism and never decides. Every H14 term carries one category (contract_mandated, physical_required_elsewhere, conservative_model_diagnostic, supplier_diagnostic); the contract is not amended or reinterpreted.
- R3-3: one strict clearance rule for every physical clearance predicate (plan or Z): a gap separates only when > EPS; a zero gap (touching) is a collision, a negative gap an overlap. Allocation-fit checks (a feature inside its Z allocation, D <= 51.00, margins against a required clearance c > 0) keep the accepted G4 margin >= 0 convention. The charger block modelled at its SR-CHG-MECH allocation height therefore fits its allocation (R1-H01) with a zero Z gap to the CHG_ROUTE / CHG_LINK conductor band; it is plan-separated from them, so it is not a 3-D collision (R4-7); the zero Z gap fails only the conservative block-AND-Z screen.
- R4-4: under the retained G4 Z model the land [0, h_land] and every 2(v) screw / support [z_lo <= 0, H] share the Z = 0 datum, so Z_gap = max(z_lo - h_land, -H) <= -min(h_land, H) <= 0: the land's conjunctive 2(v) clause is unsatisfiable for every pose, D and land width - a contract / owner question (Q-R1-CHARGER), not generalized to the block or the strict-wedge alternative.
- R4-8: R1-H11 is a set of individually typed terms (dimensionless compression / fill ratios, mm annuli / residuals / Z, booleans); physical pass is the boolean conjunction of its predicates; no minimum or ranking is ever taken across units (per-units governing terms only; the sweep seal column is per units group).
- R5: no physical result depends on a single representative / best seal row. Every authorized cross-section row of every topology is evaluated independently (its own typed predicates, gland, flange, r_lim, flange top, H14 flange rows and radial supplier land width); topology feasibility = any(r.pass_all); the coupled topology is a boolean / fixed-order rule (first closing topology face, radial, adhesive; else the face fallback, not closed); the coupled r_lim is the min and the adverse flange top the max over the coupled population; R1-H11 terms are per-predicate max reductions over the fully feasible rows (else every authorized row); the radial supplier land threshold is the min over the authorized radial rows; owner thresholds are the rows a boolean predicate defines. The reductions run in the seal internal length unit (mm / m / um regression) with unit-scaled tolerances. A representative row is chosen afterwards for display only (booleans, a count, then one homogeneous quantity per key component) and has no physical consumer (zero-feedback regression with first / last / refusing rows).
- R3-1: the charger is evaluated at EVERY (D, bulk wall) point against the complete neighbour set of that point (screws, lug arms, spring bars and button bores / bosses of that D and wall; seal flange and local arcs of that point; CHG_ROUTE / CHG_LINK; case-side supports, stop pads and vent by their exact frozen-window envelopes, re-checked against the exact g4 placements at the design point and sampled points; ribs at the design point) in five separate categories - radial prerequisite, plan prerequisite, Z prerequisite, complete neighbour set, literal closure. Only the literal category closes the charger; a prerequisite is never labelled a closure.
- R3-2: the strict-wedge supplier path is the exact g4.charger_fit wedge geometry at its zero-margin land width (orientation 0, azimuth 90, unique zero-margin centre), judged like every pose against the complete same-point neighbour set; its width is a supplier zero-margin threshold only (land < width strictly) and is never credited; the authored adverse land stays 1.000 mm.
- R4-1: an exact LRA structural fallback is bound to a canonical physical identity (candidate, plate t_in / t_out / depth / residual, materials and process tolerances, pocket band / footprint / angular interrupter, r_lim, pose and class derived from the evaluated circles, body / lead / exit envelopes, Z fit incl. mount allowance, plan re-check, structural geometry and rib interrupters, charger block / land, seal flange, plan exclusions incl. supports); only the rib configuration is free; the evaluated identity is derived from what the fallback consumed, must equal the claimed identity, and the validator reconstructs it independently from the emitted design point and the authoritative inputs and re-runs the fallback.
- R3-5: only R1-H05 and R1-H19 may be isolated to L-LRA (immutable allow-set; the validator enforces its own copy with the LRA-coupled semantics); R3-6: every numeric threshold of a GATED / FAIL numeric check is recomputed by the validator from the inputs and fresh predicates; R3-7: whole-design compliance is strict and kept apart from the study / geometric / owner-decision / supplier-gates-open states.
- Conductor / wiring reservations have ONE authoritative physical record each (R2-4): the REAR portion lies in the LA-Z-2 band; the retained G4 wiring entries, the module-side clearance set and the charger route predicates are views of that record (checked).
- Structural spokes end at min(seal r_lim, case-side post inner radius) - c_insert; S14 tail / thermode / U6 / support polygons and the charger land interrupt spokes; ring stiffness is never credited (LA-STR-4).
- STRUCTURE is evaluated at every (D, tw) point with that point's plate radius, rib interruptions, charger pose and split radius (R2-1); no endpoint result is propagated. Minimum-potential-energy bound: the relaxed model is the Loewner maximum over every admissible configuration of the Screen-B constitutive matrix (smeared rib stiffness at the subregion inner radius; D_r falls strictly with rib spacing), so every configuration has compliance >= C_relaxed and continuum deflection >= C_relaxed / (q pi R^2); where that is >= the deflection limit the point fails Screen B for every configuration, otherwise the exact configuration search decides. The dominance is verified with production regions at every design point; the Screen-A / Screen-B equations are unchanged.
- LRA envelopes are reported separately and labelled (R2-3): historical optimistic bound, continuous mathematical upper bound, authored-grid maximum, selected design-point envelope and structurally feasible searched envelope; only the last three are search results and only the last is structurally qualified. Every joint-search combination receives the structural re-screen (a pocket only thins the plate and only enlarges rib gaps, so the design-point relaxed model dominates every pocketed variant); supplied classes carry their lead / exit envelope in every plan and Z test.
- Assembly (R2-5): the A1..A11 sequence geometry is evaluated on its own; A1 / A5 / A9 / A10 / A11 product-closure dependencies on other lanes are reported per step and a physically failed dependency makes L-ASM owner-gated; the product is never reported executable then.
- The LRA ceiling deducts the LA-Z-2 conductor band (accepted as conservative); the lead / brief formulas without the band are reported beside it.
- R1-S10 (whole-design) is evaluated on the radial core (H03-OD, H05-GEOM, insertion); D thresholds of other lanes above 51.00 mm are owner-question numbers and are never selected. Whole-design guard (R2-7): no selected / recommended / compliant candidate may have D > 51.00, an unauthorized protrusion or an above-limit diagnostic geometry; radial-core feasibility is never whole-design compliance.

## 15. Lead adjudications (recorded verbatim in the JSON)

- LA-STR-1 (G4-R1 correction adjudication 2026-10-15)
- LA-STR-2 (G4-R1 correction adjudication 2026-10-15)
- LA-STR-3 (G4-R1 correction adjudication 2026-10-15)
- LA-STR-4 (G4-R1 correction adjudication 2026-10-15)
- LA-STR-5 (G4-R1 correction adjudication 2026-10-15)
- LA-Z-1 (G4-R1 correction adjudication 2026-10-15)
- LA-Z-2 (G4-R1 correction adjudication 2026-10-15)
- LA-BTN-1 (G4-R1 correction adjudication 2026-10-15)
- LA-BTN-2 (G4-R1 correction adjudication 2026-10-15)
- LA-LRA-1 (G4-R1 correction adjudication 2026-10-15)
- LA-ASM-1 (G4-R1 correction adjudication 2026-10-15)
- LA-HC-1 (G4-R1 correction adjudication 2026-10-15)

Evaluations: 1573990 (budget 2000000). Scope: true.
