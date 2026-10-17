# G4-R2 package-closure study (battery / interconnect / LRA / caseback-cup re-allocation), Rev-A

Status: R2 study result. No G4 verdict is emitted. Authorizes nothing downstream (no KiCad, K1, K1-A, G5, MPN, supplier request or qualification). The 2026-10-17 owner decisions enter only through the in-memory overlay; all values are PROVISIONAL planning values; no 5 ATM, structural, optical, adhesive, RF, MPN or supplier qualification is claimed.

Verdict (package = LPR433736): **G4-R2 BLOCKED**. LPR403736 (reported, never selected by the model): **G4-R2 BLOCKED**.

No 5 ATM, structural, optical, adhesive, RF, MPN, supplier or catalogue-as-verified claim; ceramic strength is the 150 MPa planning allowable only (SR-CASEBACK-CERAMIC gates anything above it).

Contract: `design/mechanical/G4_R2_BRIEF.md`. R2 contract commit 8f8990450fd2a482ef35c4b0314743261840751e. R2 emits no G4 verdict and authorizes nothing downstream (KiCad, K1, K1-A, G5, MPN, supplier request, qualification).

## 1. Headline numbers (joint design point per battery)

| quantity | LPR433736 | LPR403736 |
|---|---|---|
| Joint D (mm) | 50.60 | 50.60 |
| D margin to 51.00 (mm) | 0.400 | 0.400 |
| bulk wall tw (mm) | 1.10 | 1.10 |
| REAR-band Delta (mm) | 0.200 | 0.500 |
| total Z delta nominal / RSS / linear (mm) | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| chosen pack offset (mm @ deg) | 1.50 @ 60 | 1.50 @ 60 |
| carrier outer radius at linear worst (mm) | 20.250 | 20.250 |
| connectors placed / unplaced | J201 / J1501,J202 | J201 / J1501,J202 |
| clean offsets of 145 | 0 | 0 |
| LRA on MAIN B.Cu (best annulus vs need) | 5.100 mm vs LRA-COIN-D8 9.000, LRA-COIN-D10 11.000, LRA-LIN-RECT 5.300 | 5.100 mm vs LRA-COIN-D8 9.000, LRA-COIN-D10 11.000, LRA-LIN-RECT 5.300 |
| LRA on MAIN F.Cu (plan-feasible poses; largest free disk radius) | {'LRA-COIN-D8': 0, 'LRA-COIN-D10': 0, 'LRA-LIN-RECT': 0}; 2.380 mm | {'LRA-COIN-D8': 0, 'LRA-COIN-D10': 0, 'LRA-LIN-RECT': 0}; 2.380 mm |
| LRA-BMM350 distance | no pose; lower bound for any zone-B pose 5.346 mm (3-D) | no pose; lower bound for any zone-B pose 5.346 mm (3-D) |
| charger r_lim(cup) / required (mm) | 22.230 / 24.031 (deficit 1.801) | 22.620 / 24.031 (deficit 1.411) |
| seal r_lim(cup) (mm); spigot margin, REAR band only (mm) | 22.230; -0.300 | 22.620; +0.000 |
| cup stress sigma_allow_req (MPa) / margin to 150 | 410.645 / -260.6 | 410.645 / -260.6 |
| cup deflection w_max (mm) / limit 0.050 | 0.0491 | 0.0491 |
| periphery shortfall retired / retained band (mm) | +1.380 / +2.030 | +1.080 / +1.730 |
| buttons closed (SW1..SW5) | SW1:Y SW2:Y SW3:Y SW4:Y SW5:Y | SW1:Y SW2:Y SW3:Y SW4:Y SW5:Y |
| stops | R2-S04, R2-S06, R2-S08, R2-S14 | R2-S04, R2-S06, R2-S08, R2-S14 |
| verdict | G4-R2 BLOCKED | G4-R2 BLOCKED |

## 2. Stops raised (every stop with its reason)

**LPR433736**

- **R2-S04** (lane L-LRA): no LRA pose on MAIN B.Cu (zone B) and no plan-feasible Z-neutral F.Cu fallback pose
  - quantities: `{"bcu_max_annulus_mm": 5.1, "bcu_need_by_class_mm": {"LRA-COIN-D10": 11.0, "LRA-COIN-D8": 9.0, "LRA-LIN-RECT": 5.3}, "fcu_plan_feasible_poses": {"LRA-COIN-D10": 0, "LRA-COIN-D8": 0, "LRA-LIN-RECT": 0}}`
- **R2-S06** (lane L-CHG): the charger block / land / feedthrough does not close under the amended C-R1-01 2(v) (C-R2-01) at the joint point
  - quantities: `{"block_margin_mm": -0.680246586, "deficit_mm": 1.801393161, "land_margin_mm": -1.801393161, "r_lim_cup_mm": 22.23, "r_lim_required_min_mm": 24.031393161}`
- **R2-S08** (whole design (lanes completed)): annulus over-allocated: no strict-clearance pose for J1501, J202 in the annulus (MAIN B.Cu zone B); the pack / PCM lobe lies inside a reserved region: GNSS@BATTERY
  - quantities: `{"ledger_B_violations": 0, "reserved_violations": 0, "unplaced": ["J1501", "J202"]}`
- **R2-S14** (lane L-PKG): no admissible offset keeps pack + growth + PCM lobe + carrier out of the reserved regions and clear of the case features, at the PCM exit azimuths 220 / 230 / 240
  - quantities: `{"min_total_violations": 2, "offsets_clean": 0, "offsets_evaluated": 145}`

**LPR403736**

- **R2-S04** (lane L-LRA): no LRA pose on MAIN B.Cu (zone B) and no plan-feasible Z-neutral F.Cu fallback pose
  - quantities: `{"bcu_max_annulus_mm": 5.1, "bcu_need_by_class_mm": {"LRA-COIN-D10": 11.0, "LRA-COIN-D8": 9.0, "LRA-LIN-RECT": 5.3}, "fcu_plan_feasible_poses": {"LRA-COIN-D10": 0, "LRA-COIN-D8": 0, "LRA-LIN-RECT": 0}}`
- **R2-S06** (lane L-CHG): the charger block / land / feedthrough does not close under the amended C-R1-01 2(v) (C-R2-01) at the joint point
  - quantities: `{"block_margin_mm": -0.290246586, "deficit_mm": 1.411393161, "land_margin_mm": -1.411393161, "r_lim_cup_mm": 22.62, "r_lim_required_min_mm": 24.031393161}`
- **R2-S08** (whole design (lanes completed)): annulus over-allocated: no strict-clearance pose for J1501, J202 in the annulus (MAIN B.Cu zone B); the pack / PCM lobe lies inside a reserved region: GNSS@BATTERY
  - quantities: `{"ledger_B_violations": 0, "reserved_violations": 0, "unplaced": ["J1501", "J202"]}`
- **R2-S14** (lane L-PKG): no admissible offset keeps pack + growth + PCM lobe + carrier out of the reserved regions and clear of the case features, at the PCM exit azimuths 220 / 230 / 240
  - quantities: `{"min_total_violations": 2, "offsets_clean": 0, "offsets_evaluated": 145}`

## 3. Lane dispositions

Rule: R2 verdicts follow section 12; a stop makes the verdict BLOCKED and lets every other lane complete with its thresholds.

| lane | LPR433736 | LPR403736 |
|---|---|---|
| L-PKG | BLOCKED | BLOCKED |
| L-STR | OWNER_GATED | OWNER_GATED |
| L-SEAL | OWNER_GATED | SUPPLIER_GATED |
| L-CHG | BLOCKED | BLOCKED |
| L-BTN | SUPPLIER_GATED | SUPPLIER_GATED |
| L-LRA | BLOCKED | BLOCKED |
| L-RAD | BLOCKED | BLOCKED |
| L-ASM | OWNER_GATED | OWNER_GATED |
| L-WIN | SUPPLIER_GATED | SUPPLIER_GATED |

## 4. Hard checks (R2-H01 .. H28), both batteries side by side with the committed R1 column

| id | check | evaluation | LPR433736 | LPR403736 | R1 column |
|---|---|---|---|---|---|
| R2-H01 | G2-REVA / G2-REVA-HI reproduced under the overlay; total Z delta exactly 0.000; ever | exact / linear worst | PASS +0.000 mm | PASS +0.000 mm | GATED (+0.000 mm) |
| R2-H02 | D_eval <= 51.00 with margin 51.00 - D_eval (joint point); only the five bosses protr | linear worst | PASS +0.400 mm | PASS +0.400 mm | PASS (+0.000 mm) |
| R2-H03 | LEGACY numbers and G4 / R1 anchor values reproduced exactly with the overlay off; ev | exact | PASS +0.000 mm | PASS +0.000 mm | PASS (+0.000 exact) |
| R2-H04 | H05-GEOM: XF / XB / XC eliminated by proof or closed; straight runs of every annulus | linear worst | BLOCKED +0.020 mm | BLOCKED +0.020 mm | GATED (+0.020 mm) |
| R2-H05 | H05-LRA-COUPLED: LRA -> U7 lead path on B.Cu (XL eliminated by proof or closed); L-L | linear worst | BLOCKED n/a mm | BLOCKED n/a mm | GATED (-1.140 mm) |
| R2-H06 | cover / bezel / land regression (G4 H06-H09) | linear worst | PASS +0.270 mm | PASS +0.270 mm | GATED (+0.000 mm) |
| R2-H07 | W1 at 0.45 mm min: stress / deflection screens, rib fit, bond land, no rib-to-optics | G1 conservative | GATED +0.047 mm | GATED +0.047 mm | GATED (+0.047 mm) |
| R2-H08 | Pressure partition sums; zero load into battery, REAR PCB, G3 support lands, carrier | exact / linear worst | PASS +0.130 mm | PASS +0.130 mm | FAIL (-0.070 mm) |
| R2-H09 | (a) deflection <= 0.050 mm (hard physical); (b) stress vs 150 MPa: PASS / SUPPLIER_G | linear worst | GATED +0.001 mm | GATED +0.001 mm | FAIL (-221.784 MPa) |
| R2-H10 | cup-rim bearing on the midcase rear face; screw shear / pull-out; ceramic bearing an | linear worst | GATED +142.723 MPa | GATED +142.723 MPa | GATED (+20.355 MPa) |
| R2-H11 | radial cup O-ring: compression / fill at +/-0.05 mm in the static radial window; spi | linear worst / exact | GATED -0.300 mm | GATED +0.000 mm | FAIL (-0.020 dimensionless) |
| R2-H12 | buttons per SW: T1 / T2-F / T2-R under I-SUM (binding) and I-MAX (reported); boss th | linear worst | GATED +0.000 mm | GATED +0.000 mm | FAIL (-0.930 mm) |
| R2-H13 | every aperture has exactly one primary seal with a feasible geometry class; seal pat | exact | PASS +0.000 mm | PASS +0.000 mm | FAIL (n/a exact) |
| R2-H14 | charger: block inside the wedge and outside WIFI_RAD; land per C-R1-01 with C-R2-01; | linear worst | BLOCKED -1.801 mm | BLOCKED -1.411 mm | FAIL (-1.620 mm) |
| R2-H15 | radiator volumes (G4-H17), owner reserved regions and MAG_CLEAR (G4-H18): no new met | exact | FAIL n/a mm | FAIL n/a mm | PASS (n/a exact) |
| R2-H16 | G3 not reopened (items 1-7) | exact / linear worst | PASS +0.000 mm | PASS +0.000 mm | PASS (n/a exact) |
| R2-H17 | assembly: sequence executable, access per operation incl. mate strokes, collision-fr | linear worst | BLOCKED n/a mm | BLOCKED n/a mm | GATED (+0.050 mm) |
| R2-H18 | >= 4 case / caseback supports incl. W/NW, all outside the offset pack envelope | exact | PASS +0.160 mm | PASS +0.160 mm | PASS (+0.400 mm) |
| R2-H19 | LRA lane: B.Cu pose, or F.Cu Z-neutral fallback per C-R1-08; R1:R4-1 identity recons | linear worst | BLOCKED -0.200 mm | BLOCKED -0.200 mm | GATED (-2.170 mm) |
| R2-H20 | no KiCad / interface / placement / immutable-file change; changes confined to R2_FIL | exact | PASS +0.000 mm | PASS +0.000 mm | PASS (n/a exact) |
| R2-H21 | OD-THICK-REVA: nominal <= 16.5 and RSS <= 17.0 on both baselines | nominal, RSS | PASS +0.120 mm | PASS +0.120 mm | n/a (new in R2) |
| R2-H22 | joint annulus allocation: strict 3-D clearance for every pair separated by design; c | linear worst | GATED +0.000 mm | GATED +0.000 mm | n/a (new in R2) |
| R2-H23 | pack + growth + PCM lobe inside the carrier, each battery and offset; carrier wall > | linear worst | PASS +0.000 mm | PASS +0.000 mm | n/a (new in R2) |
| R2-H24 | MAIN B.Cu zones: zone-A heights <= accepted back-zone governing height; zone-B items | linear worst | PASS +0.000 mm | PASS +0.000 mm | n/a (new in R2) |
| R2-H25 | interconnects: J1501 axial mate toward REAR; J201 / J202 mates; FPC length, bends, R | linear worst | BLOCKED n/a mm | BLOCKED n/a mm | n/a (new in R2) |
| R2-H26 | frozen 24-position / 13-net interface unchanged; charger-positive outside the sensor | exact | PASS +0.000 mm | PASS +0.000 mm | n/a (new in R2) |
| R2-H27 | battery evidence: catalogue labels present; no recorded SR-BATT-PACK evidence contra | exact | GATED +0.000 mm | GATED +0.000 mm | n/a (new in R2) |
| R2-H28 | shield-ready preserved: U101 shield polygon and can volume not intruded; front gap u | exact | PASS +1.850 mm | PASS +1.850 mm | n/a (new in R2) |

## 5. Z overlay (OD-BATTERY / OD-G4-STACK; R2-H01, R2-H21)

**LPR433736** Delta = 0.200 mm inserted as one fixed REAR-band layer (no tolerance term) between rear_inner and lower_web.

| baseline | nom base | nom R2 | delta | RSS base | RSS R2 | delta | lin base | lin R2 | delta | battery_zone base | battery_zone R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G2-REVA | 16.350 | 16.350 | 0.000000000 | 16.796 | 16.796 | 0.000000000 | 18.040 | 18.040 | 0.000000000 | 5.000 | 4.800 |
| G2-REVA-HI | 16.380 | 16.380 | 0.000000000 | 16.825 | 16.825 | 0.000000000 | 18.040 | 18.040 | 0.000000000 | 5.000 | 4.800 |

**LPR403736** Delta = 0.500 mm inserted as one fixed REAR-band layer (no tolerance term) between rear_inner and lower_web.

| baseline | nom base | nom R2 | delta | RSS base | RSS R2 | delta | lin base | lin R2 | delta | battery_zone base | battery_zone R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G2-REVA | 16.350 | 16.350 | 0.000000000 | 16.796 | 16.796 | 0.000000000 | 18.040 | 18.040 | 0.000000000 | 5.000 | 4.500 |
| G2-REVA-HI | 16.380 | 16.380 | 0.000000000 | 16.825 | 16.825 | 0.000000000 | 18.040 | 18.040 | 0.000000000 | 5.000 | 4.500 |

Levels (Z from the pod plane, G2-REVA, R2 overlay, mm): window [0.000, 0.500]; optics_zone [0.500, 1.350]; rear_pcb [1.350, 2.150]; rear_inner [2.150, 2.950]; rear_band [2.950, 3.150]; lower_web [3.150, 3.550]; battery_zone [3.550, 8.350]; back_zone [8.350, 9.150]; main_pcb [9.150, 9.950]; front_gap [9.950, 12.800]; display [12.800, 14.850]; cover_bond [14.850, 15.100]; cover [15.100, 16.350]

Linear-worst dimension-chain rule: Z gaps use the nominal layer boundaries, each solid's own adverse growth, and the dimension-chain tolerance of the layers fully between the two references; the pack top is the battery-zone top minus c_axial; B.Cu items hang from the B.Cu plane at their linear-worst height.

## 6.1 L-PKG, annulus and interconnects: LPR433736

- pack Ø37.0 mm cell + planning tolerance; envelope radius (cell + radial growth) 19.750 mm; carrier inner 19.800, wall 0.35, carrier outer (lw) 20.250 mm; pack margin +0.000, carrier-wall margin +0.000 mm; offset 1.50 mm @ 60 deg; PCM exit design azimuth 230 deg (220 / 230 / 240 evaluated).
- MAIN-outline column: development envelope 23.000 mm, G4 maximum outline 23.850 mm at this point; allowed growth arcs 15.2-52.3, 67.7-104.8, 135.2-232.3, 247.7-262.3, 277.7-292.3, 330.2-344.8 deg.
- offsets evaluated: 145; clean (no reserved-region hit, no carrier conflict at the three PCM azimuths, supports ok): 0; exact top-1 placement probes of every offset: placeable sets are in the offset table of the JSON.

| item | G2 option | body mm | annulus need mm | result | search statistics |
|---|---|---|---|---|---|
| J1501 | J1501-B.Cu | 8.3 x 4.6 | 4.900 | NO strict-clearance pose | {"clearance": 0, "column": 501, "room": 22308, "stopped_after_top": false, "tried": 501, "zone_a": 951} |
| J201 | J201-B.Cu | 3.4 x 2.9 | 4.050 | placed az 211 r 21.75 ori 0 | {"clearance": 26, "column": 351, "room": 17490, "stopped_after_top": true, "tried": 383, "zone_a": 3684} |
| J202 | J202-EAST-B.Cu | 3.5 x 3.0 | 1.900 | NO strict-clearance pose | {"clearance": 0, "column": 525, "room": 528, "stopped_after_top": false, "tried": 527, "zone_a": 1917} |

- J201 path: R_bend_margin_mm 0.000, R_bend_used_mm 2.000, bends 1.000, foot_bend_mm 3.299, max_z_mm 7.750, plan_mm 6.857, tail_length_mm 10.156, vbat_manhattan_to_U201_mm 10.845, vertical_mm 0.000, vertical_rise_margin_mm -0.050, z_exit_mm 5.700

- K1 requirement (MAIN outline growth beyond Ø46): [{"item": "J201", "max_radius_mm": 23.2622011, "growth_beyond_dev_mm": 0.2622011, "az_span_deg": [206.213000879, 215.786999121]}]
- reserved regions: pack hits [{"item": "PACK", "region": "GNSS", "part": "clock", "level": "BATTERY", "plan_gap_mm": 0.0}, {"item": "PACK", "region": "GNSS", "part": "volume", "level": "BATTERY", "plan_gap_mm": 0.0}]; new-metal violations []
- joint annulus ledger: as-pinned supports 4 violating pair(s) of 1595; supports starting at Z 4.630 mm (above the wall top): 0 violating pair(s); double-occupied cells (as pinned) {'REAR_PERIPHERY': 0, 'LOWER_WEB_LEVEL': 36, 'BATTERY_BAND': 45, 'BACK_ZONE': 0}.
  - SUP_SW_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.330, plan gap 0.000)
  - SUP_SE_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.330, plan gap 0.000)
  - SUP_NE_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.330, plan gap 0.000)
  - SUP_WNW_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.330, plan gap 0.000)

## 6.2 L-PKG, annulus and interconnects: LPR403736

- pack Ø37.0 mm cell + planning tolerance; envelope radius (cell + radial growth) 19.750 mm; carrier inner 19.800, wall 0.35, carrier outer (lw) 20.250 mm; pack margin +0.000, carrier-wall margin +0.000 mm; offset 1.50 mm @ 60 deg; PCM exit design azimuth 230 deg (220 / 230 / 240 evaluated).
- MAIN-outline column: development envelope 23.000 mm, G4 maximum outline 23.850 mm at this point; allowed growth arcs 15.2-52.3, 67.7-104.8, 135.2-232.3, 247.7-262.3, 277.7-292.3, 330.2-344.8 deg.
- offsets evaluated: 145; clean (no reserved-region hit, no carrier conflict at the three PCM azimuths, supports ok): 0; exact top-1 placement probes of every offset: placeable sets are in the offset table of the JSON.

| item | G2 option | body mm | annulus need mm | result | search statistics |
|---|---|---|---|---|---|
| J1501 | J1501-B.Cu | 8.3 x 4.6 | 4.900 | NO strict-clearance pose | {"clearance": 0, "column": 501, "room": 22308, "stopped_after_top": false, "tried": 501, "zone_a": 951} |
| J201 | J201-B.Cu | 3.4 x 2.9 | 4.050 | placed az 211 r 21.75 ori 0 | {"clearance": 26, "column": 351, "room": 17490, "stopped_after_top": true, "tried": 383, "zone_a": 3684} |
| J202 | J202-EAST-B.Cu | 3.5 x 3.0 | 1.900 | NO strict-clearance pose | {"clearance": 0, "column": 525, "room": 528, "stopped_after_top": false, "tried": 527, "zone_a": 1917} |

- J201 path: R_bend_margin_mm 0.000, R_bend_used_mm 2.000, bends 1.000, foot_bend_mm 3.299, max_z_mm 7.750, plan_mm 6.857, tail_length_mm 10.156, vbat_manhattan_to_U201_mm 10.845, vertical_mm 0.000, vertical_rise_margin_mm -0.200, z_exit_mm 5.850

- K1 requirement (MAIN outline growth beyond Ø46): [{"item": "J201", "max_radius_mm": 23.2622011, "growth_beyond_dev_mm": 0.2622011, "az_span_deg": [206.213000879, 215.786999121]}]
- reserved regions: pack hits [{"item": "PACK", "region": "GNSS", "part": "clock", "level": "BATTERY", "plan_gap_mm": 0.0}, {"item": "PACK", "region": "GNSS", "part": "volume", "level": "BATTERY", "plan_gap_mm": 0.0}]; new-metal violations []
- joint annulus ledger: as-pinned supports 4 violating pair(s) of 1595; supports starting at Z 4.630 mm (above the wall top): 0 violating pair(s); double-occupied cells (as pinned) {'REAR_PERIPHERY': 0, 'LOWER_WEB_LEVEL': 36, 'BATTERY_BAND': 45, 'BACK_ZONE': 0}.
  - SUP_SW_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.030, plan gap 0.000)
  - SUP_SE_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.030, plan gap 0.000)
  - SUP_NE_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.030, plan gap 0.000)
  - SUP_WNW_CASE_SIDE / CUP_WALL_RING: PLAN (z gap -1.030, plan gap 0.000)

## 7. L-STR and L-SEAL: ceramic cup and radial O-ring

Ring-plate compatibility (7.1.2), four equations per unit circumferential length, E = E_min, nu = nu_min of MAT-CERAMIC; unknowns u (junction radial displacement), psi (junction rotation), N_p, M_p:

1. plate rotation: psi = psi_ss(p) + |f_M| M'  (f_M = dpsi/dM of the annular plate with the loaded-boss inner edge and w = 0 at the ring radius; psi_ss from the accepted G4 / R1 annular-plate solution)
2. plate in-plane: u = c_N N_p  (Lame solution of the annulus with a free inner edge, outer-region thickness)
3. ring: N = k_A (u - e psi), M = -e k_A (u - e psi) + k_I psi  with k_A = E A / a^2, k_I = E I / a^2, I = integral (z - z_c)^2 dA of the wall section incl. the gland groove, e = z_c - t_out / 2
4. equilibrium: N_p = -N, M' = -M. A clamped edge is never assumed: the simply-supported and clamped bounds are reported beside the compatibility result.

| battery | row | cs | t_in/t_out/widen/H | wall top mm | r_ring mm | sigma_allow_req MPa | governing | w_max mm | edge fixity | Screen A (ss) MPa / mm | clamped bound MPa / mm | sigma w/o inner K_t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LPR433736 | radial#10 | 1.5 | 1.1/1.2/0.0/3.26 | 4.460 | 23.302 | 410.645 | plate_inner_junction_Kt | 0.0491 | 0.733 | 731.3 / 0.1158 | 293.6 / 0.0247 | 258.5 |
| LPR403736 | radial#10 | 1.5 | 1.1/1.2/0.0/3.26 | 4.460 | 23.302 | 410.645 | plate_inner_junction_Kt | 0.0491 | 0.733 | 731.3 / 0.1158 | 293.6 / 0.0247 | 258.5 |

- LPR433736 shortfalls: {"band_state_P1": "retired; the retained state is the R1-literal column", "inner_region_required_uniform_nominal_mm": 1.721509006, "inner_region_shortfall_mm": 0.621509006, "periphery_shortfall_band_retired_mm": 1.38, "periphery_shortfall_conductor_band_retained_mm": 2.03, "periphery_shortfall_with_zone_b_as_pinned_mm": 1.38, "periphery_shortfall_with_zone_b_supports_relieved_mm": -0.12, "required_row": "radial#10", "required_t_out_mm": 1.2, "required_wall_top_for_deflection_mm": 4.48, "rule": "shortfall = required - available (positive = shortfall, negative = surplus), mm", "t_in_limit_mm": 1.1}
- LPR403736 shortfalls: {"band_state_P1": "retired; the retained state is the R1-literal column", "inner_region_required_uniform_nominal_mm": 1.721509006, "inner_region_shortfall_mm": 0.621509006, "periphery_shortfall_band_retired_mm": 1.08, "periphery_shortfall_conductor_band_retained_mm": 1.73, "periphery_shortfall_with_zone_b_as_pinned_mm": 1.08, "periphery_shortfall_with_zone_b_supports_relieved_mm": -0.12, "required_row": "radial#10", "required_t_out_mm": 1.2, "required_wall_top_for_deflection_mm": 4.48, "rule": "shortfall = required - available (positive = shortfall, negative = surplus), mm", "t_in_limit_mm": 1.1}

Seal rows (R1:R5 population, both batteries share the gland rows; spigot margin = REAR band only; P-1: conductor band retired (R2 state) and the R1-literal retained state):

| row | cs | gland window | spigot height | spigot radial | r_lim | spigot Z (433736, band retired) | spigot Z (band retained, R1-literal) | spigot Z (403736, band retired) |
|---|---|---|---|---|---|---|---|---|
| radial#00 | 0.5 | False | 1.300 | 0.790 | 23.390 | +0.860 | +0.210 | +1.160 |
| radial#01 | 0.6 | False | 1.410 | 0.865 | 23.315 | +0.750 | +0.100 | +1.050 |
| radial#10 | 1.5 | True | 2.460 | 1.560 | 22.620 | -0.300 | -0.950 | +0.000 |
| radial#11 | 1.6 | True | 2.580 | 1.640 | 22.540 | -0.420 | -1.070 | -0.120 |
| radial#12 | 1.7 | True | 2.690 | 1.720 | 22.460 | -0.530 | -1.180 | -0.230 |
| radial#13 | 1.8 | True | 2.810 | 1.795 | 22.385 | -0.650 | -1.300 | -0.350 |
| radial#14 | 1.9 | True | 2.930 | 1.870 | 22.310 | -0.770 | -1.420 | -0.470 |
| radial#15 | 2.0 | True | 3.050 | 1.950 | 22.230 | -0.890 | -1.540 | -0.590 |

- LPR433736: closes as pinned False; closes with the supports relieved True; extension free as pinned 0.000 mm / relieved 1.500 mm; zero-margin extension of the smallest feasible row 0.300 mm; seal path closed True; population 16 rows, r_lim(cup) 22.230 mm.
- LPR403736: closes as pinned True; closes with the supports relieved True; extension free as pinned 0.000 mm / relieved 1.200 mm; zero-margin extension of the smallest feasible row 0.000 mm; seal path closed True; population 1 rows, r_lim(cup) 22.620 mm.

## 8. L-CHG (C-R2-01), P-2 physical headline

- LPR433736: closes False. smallest strict clearance -1.801 mm, governing pair: CHG_LAND vs cup wall inner face (radial); r_lim(cup) 22.230 mm vs required 24.031 mm (deficit 1.801 mm); block margin -0.680, land margin -1.801 mm; strict-wedge zero-margin land width 0.153 mm (supplier threshold, never credited). Feedthrough: FT-C (bonded sealed body in the ceramic caseback; binding).
- LPR403736: closes False. smallest strict clearance -1.411 mm, governing pair: CHG_LAND vs cup wall inner face (radial); r_lim(cup) 22.620 mm vs required 24.031 mm (deficit 1.411 mm); block margin -0.290, land margin -1.411 mm; strict-wedge zero-margin land width 0.338 mm (supplier threshold, never credited). Feedthrough: FT-C (bonded sealed body in the ceramic caseback; binding).

## 9. L-BTN (T1 / T2-F / T2-R per switch, boss limit 3.000 mm)

| SW | material rule | topology | pusher class | I-SUM closes | boss used | boss zero-margin | d_p | protrusion (limit 3.000) | I-MAX closes | causes if not | R1 bore_stack |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SW1 | non-metallic (Q-R2-SW1-BLE) | T1 | zirconia | N | n/a | 3.320 | 4.4 | 2.950 | N | core | -0.860 |
| SW1 | non-metallic (Q-R2-SW1-BLE) | T2-F | zirconia | Y | 1.15 | 1.130 | 2.0 | 3.000 | Y | - | -0.860 |
| SW1 | non-metallic (Q-R2-SW1-BLE) | T2-R | zirconia | Y | 2.95 | 2.930 | 2.0 | 3.000 | Y | - | -0.860 |
| SW1 | non-metallic (Q-R2-SW1-BLE) | T1 | PEEK | N | n/a | 3.700 | 2.0 | 3.000 | N | bore_stack,core | -0.860 |
| SW1 | non-metallic (Q-R2-SW1-BLE) | T2-F | PEEK | Y | 1.15 | 1.130 | 2.0 | 3.000 | Y | - | -0.860 |
| SW1 | non-metallic (Q-R2-SW1-BLE) | T2-R | PEEK | Y | 2.95 | 2.930 | 2.0 | 3.000 | Y | - | -0.860 |
| SW2 | metal (Q-R1-BUTTON-ENVELOPE) | T1 | metal | Y | 2.10 | 2.100 | 3.8 | 2.120 | Y | - | -0.860 |
| SW2 | metal (Q-R1-BUTTON-ENVELOPE) | T2-F | metal | Y | 1.10 | 1.060 | 2.0 | 2.920 | Y | - | -0.860 |
| SW2 | metal (Q-R1-BUTTON-ENVELOPE) | T2-R | metal | Y | 2.90 | 2.860 | 2.0 | 2.920 | Y | - | -0.860 |
| SW3 | metal (Q-R1-BUTTON-ENVELOPE) | T1 | metal | Y | 2.10 | 2.100 | 3.8 | 2.120 | Y | - | -0.860 |
| SW3 | metal (Q-R1-BUTTON-ENVELOPE) | T2-F | metal | Y | 1.10 | 1.060 | 2.0 | 2.920 | Y | - | -0.860 |
| SW3 | metal (Q-R1-BUTTON-ENVELOPE) | T2-R | metal | Y | 2.90 | 2.860 | 2.0 | 2.920 | Y | - | -0.860 |
| SW4 | non-ferromagnetic metal (MAG_CLEAR | T1 | metal | Y | 2.10 | 2.100 | 3.8 | 2.120 | Y | - | -0.860 |
| SW4 | non-ferromagnetic metal (MAG_CLEAR | T2-F | metal | Y | 1.10 | 1.060 | 2.0 | 2.920 | Y | - | -0.860 |
| SW4 | non-ferromagnetic metal (MAG_CLEAR | T2-R | metal | Y | 2.90 | 2.860 | 2.0 | 2.920 | Y | - | -0.860 |
| SW5 | non-metallic (Q-R2-SW5-PUSHER) | T1 | zirconia | N | n/a | 3.320 | 4.4 | 2.950 | N | core | -0.930 |
| SW5 | non-metallic (Q-R2-SW5-PUSHER) | T2-F | zirconia | Y | 1.15 | 1.130 | 2.0 | 3.000 | Y | - | -0.930 |
| SW5 | non-metallic (Q-R2-SW5-PUSHER) | T2-R | zirconia | Y | 2.95 | 2.930 | 2.0 | 3.000 | Y | - | -0.930 |
| SW5 | non-metallic (Q-R2-SW5-PUSHER) | T1 | PEEK | N | n/a | 3.700 | 2.0 | 3.000 | N | bore_stack,core | -0.930 |
| SW5 | non-metallic (Q-R2-SW5-PUSHER) | T2-F | PEEK | Y | 1.15 | 1.130 | 2.0 | 3.000 | Y | - | -0.930 |
| SW5 | non-metallic (Q-R2-SW5-PUSHER) | T2-R | PEEK | Y | 2.95 | 2.930 | 2.0 | 3.000 | Y | - | -0.930 |

C-R1-03: I-SUM binds; I-MAX is reported; `c_r1_03_adjudication` stays null; no I-MAX-only closure exists (an I-MAX-only row would not count as closed).

## 10. L-LRA

- LPR433736: B.Cu zone B: best annulus over all offsets 5.100 mm; need per class {'LRA-COIN-D8': '9.000', 'LRA-COIN-D10': '11.000', 'LRA-LIN-RECT': '5.300'}; feasible False. F.Cu fallback: {'LRA-COIN-D8': 0, 'LRA-COIN-D10': 0, 'LRA-LIN-RECT': 0}; largest free disk radius 2.380 mm (centre [101.5, 118.0]) so a class must fit a disk of radius 1.980 mm; Z-neutral cap 2.70 mm (height incl. mount: {'LRA-COIN-D8': '3.350', 'LRA-COIN-D10': '3.750', 'LRA-LIN-RECT': '3.350'}). BMM350: {"plan_distance_mm": 5.28543754, "z_separation_mm": 0.8, "distance_3d_lower_bound_mm": 5.345638408, "rule": "any LRA body lies in the zone-B annulus on B.Cu; U703 sits on MAIN F.Cu on the other side of the 0.8 mm board"}.
- LPR403736: B.Cu zone B: best annulus over all offsets 5.100 mm; need per class {'LRA-COIN-D8': '9.000', 'LRA-COIN-D10': '11.000', 'LRA-LIN-RECT': '5.300'}; feasible False. F.Cu fallback: {'LRA-COIN-D8': 0, 'LRA-COIN-D10': 0, 'LRA-LIN-RECT': 0}; largest free disk radius 2.380 mm (centre [101.5, 118.0]) so a class must fit a disk of radius 1.980 mm; Z-neutral cap 2.70 mm (height incl. mount: {'LRA-COIN-D8': '3.350', 'LRA-COIN-D10': '3.750', 'LRA-LIN-RECT': '3.350'}). BMM350: {"plan_distance_mm": 5.28543754, "z_separation_mm": 0.8, "distance_3d_lower_bound_mm": 5.345638408, "rule": "any LRA body lies in the zone-B annulus on B.Cu; U703 sits on MAIN F.Cu on the other side of the 0.8 mm board"}.

R1:R4-1 identity: no pose is selected, so no identity exists; the validator reconstructs the identity of the fixture pose in the self-test. The LRA magnet is authorized (OD-G4-LRA-MAG); MAG_CLEAR stays an exclusion.

## 11. L-RAD and crossings

- LPR433736: margins {"H03-OD": 0.34, "H05-MAIN-CASE": 0.5877989, "H05-WALL-DIELECTRIC": 0.02, "H05-WALL-SIDE": 0.36}; insertion {"H23-INSERT-BATTERY": 1.77235767, "H23-INSERT-MAIN": 0.6377989, "H23-INSERT-REAR": 7.599365317}; straight runs {"H05-STRAIGHT@J201": 2.111624379}; crossings {'XF-J1501': 'NOT_ELIMINATED', 'XB-J201': 'ELIMINATED', 'XC-J202': 'NOT_ELIMINATED', 'XL-LRA': 'NOT_ELIMINATED'}.
- LPR403736: margins {"H03-OD": 0.34, "H05-MAIN-CASE": 0.5877989, "H05-WALL-DIELECTRIC": 0.02, "H05-WALL-SIDE": 0.36}; insertion {"H23-INSERT-BATTERY": 1.77235767, "H23-INSERT-MAIN": 0.6377989, "H23-INSERT-REAR": 7.599365317}; straight runs {"H05-STRAIGHT@J201": 2.111624379}; crossings {'XF-J1501': 'NOT_ELIMINATED', 'XB-J201': 'ELIMINATED', 'XC-J202': 'NOT_ELIMINATED', 'XL-LRA': 'NOT_ELIMINATED'}.

## 12. L-ASM and L-WIN

A1-A11 retain identities, order, parts, directions and battery states; only the operation text of A1, A4, A5, A6, A9, A10, A11 changes, each citing its decision id (A1: Q-R1-MAIN-SEAL / Q-R1-STRUCTURE, A4: OD-CONN-SIDE, A5: OD-G4-LRA-ARCH, A6: OD-BATTERY / OD-CONN-SIDE, A9: Q-R1-BUTTON-ENVELOPE, A10: OD-J202 / Q-R1-CHARGER, A11: Q-R1-MAIN-SEAL).

W1 at 0.50 mm bonded into the cup pod frame, Z delta 0.000; R1 W1 values reproduced from the pinned R1 JSON (SUPPLIER_GATED: SR-WINDOW, MG-WINDOW-XTALK).

## 13. Overlay (section 4.2): pinned value, R2 value and authority side by side

| id | pinned source | pinned value (read at run time) | R2 value | authority |
|---|---|---|---|---|
| OV-BATT-ID | input_register.json /frozen_invariants/7 | Battery LPR454440 selected; not replaceable without owner authorizatio | LPR433736 (primary, 585 mAh, 3.7 V, 1C, 2.16 Wh); LPR403736 (495 mAh) reported as the fall | OD-BATTERY |
| OV-BATT-DIA | stack_parameters.json /radial/parameters/D_pack_nom/nom | 44.0 | 37.0 | OD-BATTERY |
| OV-BATT-THICK | stack_parameters.json /parameters/t_pack_nom/nom | 4.5 | 4.3 | OD-BATTERY |
| OV-Z-REAR-BAND | stack_parameters.json /rules/battery_zone | t_pack_nom + tol_pack_thick + g_axial + c_axial | battery_zone recomputed with the overlaid t_pack_nom through the imported G1 / G2 rule; De | OD-G4-STACK |
| OV-CONN-J1501 | g2_interconnect.json /allocation/J1501 | J1501-F.Cu | J1501-B.Cu | OD-CONN-SIDE |
| OV-CONN-J201 | g2_interconnect.json /allocation/J201 | J201-F.Cu | J201-B.Cu | OD-CONN-SIDE |
| OV-CONN-J202 | g2_interconnect.json /allocation/J202 | J202-WEST-F.Cu | J202-B.Cu (east sector; mate direction is a design variable) | OD-CONN-SIDE / OD-J202 |
| OV-U7 | g2_interconnect.json /allocation/U7~1LRA | U7-B.Cu | U7-B.Cu | OD-CONN-SIDE |
| OV-LRA | g4_r1_blockers.json /parameters/V22_lra_pocket/pocket_depths_mm | [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6] | MAIN B.Cu zone B (battery annulus) primary; MAIN F.Cu <= 2.70 mm Z-neutral fallback; the R | OD-G4-LRA-ARCH |
| OV-COND-BAND | g4_case_sealing.json /parameters/c_rear_route_mm/max | 0.65 | REAR-level perimeter conductor band retired (CHG_ROUTE, CHG_LINK, CHG_RISER, CHG_APPROACH, | OD-J202 / Q-R1-CHARGER |
| OV-BOSS | g4_case_sealing.json /contract_values/owner_limits/boss_extension_max_mm | 1.0 | 3.0 | Q-R1-BUTTON-ENVELOPE |
| OV-BTN-TOPOLOGY | g4_r1_blockers.json /parameters/V05_button_topologies/T1 | dynamic radial pusher O-ring (G4 pusher_gland); regression only, never | T1 stem O-ring re-admitted for evaluation under the unchanged dynamic radial window and cr | Q-R1-BUTTON-ENVELOPE |
| OV-C-R1-01-2V | g4_r1_blockers.json /parameters/V20_charger_land/route_clearance/contract_text | (v) clears screws, supports, CHG_ROUTE and CHG_LINK in plan and in Z,  | (v) clears screws, supports, CHG_ROUTE and CHG_LINK in 3-D, i.e. separated in plan OR in Z | OD-J202 / Q-R1-CHARGER (C-R2-01) |
| OV-SEAL | g4_r1_blockers.json /parameters/V10_main_seal_topologies | ['face', 'adhesive', 'radial'] | ['radial'] | Q-R1-MAIN-SEAL |
| OV-MATERIAL | g4_r1_blockers.json /candidates | [{'id': 'G4-A', 'source': 'g4_case_sealing.json candidates G4-A', 'def | G4-B-ZC | Q-R1-STRUCTURE / OD-G4-MATERIAL |

## 14. Overlay-off anchors and equivalence tests (R2-H03)

| anchor | expected | computed | tolerance | match |
|---|---|---|---|---|
| Z G2-REVA nominal | 16.350000 | 16.350000 | 0.0005 | True |
| Z G2-REVA RSS | 16.796000 | 16.796000 | 0.0005 | True |
| Z G2-REVA linear | 18.040000 | 18.040000 | 0.0005 | True |
| Z G2-REVA-HI nominal | 16.380000 | 16.380000 | 0.0005 | True |
| Z G2-REVA-HI RSS | 16.825000 | 16.825000 | 0.0005 | True |
| Z G2-REVA-HI linear | 18.040000 | 18.040000 | 0.0005 | True |
| LEGACY rows (G4 H04) | True | True | 0 | True |
| plate_solve2 == r1.plate_solve (equivalence) | 0.000000 | 0.000000 | 1e-12 | True |
| R1 Screen B sigma (MPa) | 371.783850 | 371.783850 | 1e-06 | True |
| R1 Screen B w_max (mm) | 0.119817 | 0.119817 | 1e-08 | True |
| R1 uniform ceramic thickness (mm) | 1.836113 | 1.836113 | 1e-06 | True |
| G4 pressure partition total (N) | 1168.986626 | 1168.986626 | 1e-06 | True |
| R1 radial spigot Z (REAR band, conductor band retained, Delta 0) | -1.150000 | -1.150000 | 1e-06 | True |
| R1 charger radial prerequisite r_lim (mm) | 24.031393 | 24.031393 | 1e-06 | True |
| R1 charger plan prerequisite r_lim (mm) | 24.624973 | 24.624973 | 1e-06 | True |
| R1 SW1 I-SUM bore_stack (mm) | -0.860000 | -0.860000 | 1e-09 | True |
| R1 SW2 I-SUM bore_stack (mm) | -0.860000 | -0.860000 | 1e-09 | True |
| R1 SW3 I-SUM bore_stack (mm) | -0.860000 | -0.860000 | 1e-09 | True |
| R1 SW4 I-SUM bore_stack (mm) | -0.860000 | -0.860000 | 1e-09 | True |
| R1 SW5 I-SUM bore_stack (mm) | -0.930000 | -0.930000 | 1e-09 | True |
| t1_gland == g4.pusher_gland on the G4 sweep cross-sections (equivalence) | True | True | 0 | True |
| L-WIN equals the pinned R1 W1 values | True | True | 0 | True |
| shape_gap (analytic) vs g4.region_distance (sampled) | 7.000000 | 7.000000 | 0.02 | True |
| ring gap (analytic) vs g4.region_distance (sampled) | 7.834475 | 7.834475 | 0.03 | True |
| R2 BATTERY-level insertion closed form == library H23-INSERT-BATTERY | 3.100000 | 3.100000 | 1e-09 | True |
| R2 MAIN-case closed form == library H05-MAIN-CASE | 0.650000 | 0.650000 | 1e-09 | True |
| G4 in-process reproduction byte-identical, 32/32 | True | True | 0 | True |

## 15. Lead cross-checks (P-3)

| id | lead value | R2 value | status | explanation |
|---|---|---|---|---|
| delta_433736_mm | 0.2 | 0.2 | REPRODUCED |  |
| battery_zone_433736_mm | [4.8, 5.3, 4.55] | [4.8, 5.3, 4.55] | REPRODUCED |  |
| delta_403736_mm | 0.5 | 0.5 | REPRODUCED |  |
| battery_zone_403736_mm | [4.5, 5.0, 4.25] | [4.5, 5.0, 4.25] | REPRODUCED |  |
| R_pack_mm | [18.65, 18.75] | [18.65, 18.75] | REPRODUCED |  |
| R_case_inner_D50p9_tw1p1_mm | 24.35 | 24.35 | REPRODUCED |  |
| carrier_outer_tcw0p40_mm | [19.55, 20.2] | [19.55, 20.25] | EXPLAINED | the lead figure omits the two carrier tolerance terms of the imported G4 predicate (carrier inner radius and wall thickness, 0.05 mm each, PC-CARRIER-MOULD); carrier outer = R_pack(lw) + g_radial + tol_carrier_r + t_cw + tol_cw = 18.75 + 1.00 + 0.05 + 0.40 + 0.05 |
| free_band_to_dia46_mm | [2.8, 4.3] | [2.75, 4.25] | EXPLAINED | same two carrier tolerance terms (-0.10 mm); the far-side figure subtracts the 1.5 mm offset from the carrier outer radius |
| free_band_to_bore_mm | [4.15, 5.65] | [4.1, 5.6] | EXPLAINED | same two carrier tolerance terms (-0.10 mm) |
| lra_lin_rect_adverse_need_mm | 6.4 | 6.251621013 | EXPLAINED | computed need = 4.50 (width) + 2 x 0.40 (c_lra_plan) + 0.95 (chord sagitta of the 12.5 mm long axis at r 21) = 6.25; the lead rounded the sagitta to 1.1 |
| lra_coin_d8_adverse_need_mm | 9.0 | 9.0 | REPRODUCED |  |
| spigot_shortfall_rear_only_433736_mm | -0.3 | -0.3 | REPRODUCED |  |
| spigot_shortfall_rear_only_403736_mm | 0.0 | 0.0 | REPRODUCED |  |
| charger_r_lim_required_mm | [24.031, 24.625] | [24.031393161, 24.031393161] | EXPLAINED | the radial prerequisite 24.031 is reproduced; the R1 plan prerequisite 24.625 included CHG_ROUTE / CHG_LINK in plan, which OV-COND-BAND retires, so the R2 plan prerequisite equals the radial one |
| charger_r1_radial_row_r_lim_mm | [23.0, 23.54] | [23.0, 23.54] | REPRODUCED |  |
| t1_cs_threshold_mm | [1.69, 2.29, 2.89] | [1.7, 2.3, 2.9] | REPRODUCED |  |
| t1_dp_at_cs1p7_mm | 3.8 | 3.75 | REPRODUCED |  |
| structure_context_MPa | {'LPR433736': [159.0, 186.0], 'LPR403736': [141.0, 162.0]} | {"LPR433736": 410.645, "LPR403736": 410.645} | EXPLAINED | context only: the lead estimate assumed ring support close to a clamped edge and no stress-concentration factor at the pod-frame junction. R2 solves the ring-plate compatibility (edge fixity 0.73) and applies K_t 2.0 at the pod-frame junction (sigma without that K_t: 258.5 MPa). Stress is SUPPLIER_GATED, never a model FAIL. |
| overlay_off_screen_B | [371.784, 0.12] | [371.784, null] | REPRODUCED |  |
| overlay_off_uniform_ceramic_mm | [1.836, 1.1] | [1.836, 1.1] | REPRODUCED |  |
| buttons_reserved_overlap_deg | {'SW1': [292.5, 307.5, 'BLE 300-330'], 'SW5': [112.5, 127.5, 'Wi-Fi 105-135']} | {"SW1_in_BLE_clock": [300.0, 307.5], "SW5_inside_WIFI_clock": true} | REPRODUCED |  |

## 16. T1 ruling (7.4.1)

- Where R1 excluded T1: G4_R1_BRIEF.md section 6.2: "T1 dynamic radial O-ring on the pusher - regression / reference only, expected FAIL; never selectable"; V05: "T1 (regression)"; section 11 self-test fault "T1 selected"; section 16 item 6: "T1 never selectable"; inputs/g4_r1_blockers.json V05_button_topologies.T1
- Stated reason: under the dynamic radial window 10-20 % and +/-0.05 mm cross-section tolerance a pusher O-ring needs cs >= 1.69 / 2.29 / 2.89 mm at groove / bore stacks 0.04 / 0.07 / 0.10 mm; the R1 pusher class (dia 1.6-2.0 mm bore planning range in a +1.0 mm boss) cannot carry such a ring
- (i) the gland windows and the cross-section tolerance ARE hard rules (frozen carry-ins; not widened, not narrowed) and stay binding in R2
- (ii) "never selectable" is an R1-scoped lead contract clause derived from (i) under the R1 envelope; not an owner decision, not a frozen invariant, not a G4 carry-in
- **Result:** the exclusion does not rest on a hard rule: T1 is re-admitted for evaluation under the unchanged rules (i); no re-admission question is raised; R1 itself is unchanged. The independent review must challenge it.

## 17. Owner decisions and answers (recorded verbatim; date 2026-10-17, source: owner decision)

**OD-BATTERY** (G4_R2_BRIEF.md section 3.2)

```text
- OD-BATTERY: Rev-A battery LPR454440 (870 mAh, Ø44 x 4.5) replaced by
  LPR433736 (585 mAh, 3.7 V, 1C, Ø37 x 4.3 mm, 2.16 Wh), same J201
  connector. Catalogue values pending supplier protected-pack drawing
  (SR-BATT-PACK). If the drawing contradicts the assumed envelope: STOP.
  Fallback LPR403736 (495 mAh, Ø37 x 4.0) only if the caseback
  allowable cannot support LPR433736.
```

**OD-G4-STACK** (G4_R2_BRIEF.md section 3.2)

```text
- OD-G4-STACK: zero total Z growth; battery Z saving reallocated to the
  REAR band. OD-THICK-REVA (<= 16.5 mm nominal, <= 17.0 mm RSS)
  unchanged.
```

**Q-R1-BUTTON-ENVELOPE** (G4_R2_BRIEF.md section 3.2)

```text
- Q-R1-BUTTON-ENVELOPE: proven mechanical buttons: sealed metal pusher
  through the case (stem O-ring or elastomer boot/seal, whichever
  closes), pressing a right-angle side-actuated tactile switch at the
  MAIN board edge; local case bosses <= +3.0 mm (incl. seal and
  tolerance) at the five existing button windows only (10, 9, 8, 2,
  4 o'clock). C-R1-03 ruling not needed. Inductive/force buttons
  deferred to Rev-B. SG: SR-BUTTONS.
```

**OD-CONN-SIDE** (G4_R2_BRIEF.md section 3.2)

```text
- OD-CONN-SIDE: J1501, J201, J202 on MAIN B.Cu; U7 (DRV2625) to B.Cu.
```

**OD-J202 / Q-R1-CHARGER** (G4_R2_BRIEF.md section 3.2)

```text
- OD-J202 / Q-R1-CHARGER: J202 on B.Cu toward east; charger contacts on
  the caseback at ~3 o'clock; retire the perimeter conductor band
  except the local charger drop. C-R1-01 2(v) AMENDED to: clear in 3-D,
  i.e. separated in plan OR in Z, with strict 3-D clearance. Record the
  amendment in G4-R2 only; G4_R1_BRIEF.md stays unchanged.
```

**OD-G4-LRA-ARCH** (G4_R2_BRIEF.md section 3.2)

```text
- OD-G4-LRA-ARCH: LRA on MAIN B.Cu in the battery annulus (battery
  offset 0–1.5 mm allowed). Fallback: LRA <= 2.70 mm tall on MAIN F.Cu
  (Z-neutral) if no B.Cu pose exists. Report BMM350 distance.
```

**Q-R1-MAIN-SEAL** (G4_R2_BRIEF.md section 3.2)

```text
- Q-R1-MAIN-SEAL: raised, serviceable radial O-ring on a caseback cup.
  Adhesive main seal rejected.
```

**Q-R1-STRUCTURE / OD-G4-MATERIAL** (G4_R2_BRIEF.md section 3.2)

```text
- Q-R1-STRUCTURE / OD-G4-MATERIAL: ceramic (zirconia class) caseback
  cup on the G4-B midcase (metal with dielectric sectors).
```

**OD-AOD** (G4_R2_BRIEF.md section 3.2)

```text
- OD-AOD: no always-on display in Rev-A.
```

**K1-A** (G4_R2_BRIEF.md section 3.2)

```text
- K1-A: authorized in principle, in parallel with G4-R2, under its own
  separate contract (REAR layout + MAIN power-schematic fixes after
  independent verification). Not part of G4-R2.
```

**OWNER POSITIONS** (G4_R2_BRIEF.md section 3.2)

```text
- OWNER POSITIONS: G5 (antennas) directly after G4-R2; nothing new in
  the reserved GNSS (12), BLE (10–11), Wi-Fi (3:30–4:30) regions. MAIN
  stays shield-ready (§20); shield material decided after Rev-A testing.
```

**Q-R2-SW5-PUSHER** (G4_R2_BRIEF.md section 17.1, round 1, DECIDED (first round); "SW1-SW4 stay metal" superseded for SW1 by Q-R2-SW1-BLE)

```text
- Q-R2-SW5-PUSHER: SW5 uses a non-metallic pusher (zirconia or PEEK
  class); SW1–SW4 stay metal. SW5 position unchanged.
```

**Q-R2-RESERVED-REGION** (G4_R2_BRIEF.md section 17.1, round 1, DECIDED (first round))

```text
- Q-R2-RESERVED-REGION: in the reserved GNSS/BLE/Wi-Fi regions, new
  metal, conductors and components are forbidden. Non-conductive
  structure (ceramic cup ring, dielectric pusher, boss growth) is
  allowed but must be recorded with material, permittivity class and
  volume as a G5 input.
```

**Q-R2-SHIELD-REF** (G4_R2_BRIEF.md section 17.1, round 1, DECIDED (first round))

```text
- Q-R2-SHIELD-REF: "§20" means the master handoff's shield-ready policy,
  not a repo file; your architecture.md section A reading is accepted.
```

**Q-R2-K1A** (G4_R2_BRIEF.md section 17.1, round 1, SUPERSEDED by Q-R2-K1A correction; recorded for history, never applied)

```text
- Q-R2-K1A: confirmed. K1-A keeps G3-B-S14 REAR placement unchanged and
  is MAIN schematic-only; it moves nothing G4-R2 relies on.
```

**OD-G4-LRA-MAG** (G4_R2_BRIEF.md section 17.1, round 1, DECIDED (first round))

```text
- OD-G4-LRA-MAG: authorized. Report LRA-to-BMM350 distance; magnetometer
  calibration is a later firmware/test item.
```

**E-1** (G4_R2_BRIEF.md section 17.1, round 1, DECIDED (first round))

```text
- E-1: the rear_sensor .kicad_pro change was KiCad auto-save and has
  been reverted by the owner; keep E-1 as a precondition check.
```

**Q-R2-SW1-BLE (OQ-1)** (G4_R2_BRIEF.md section 17.1, round 2, DECIDED (second round))

```text
- Q-R2-SW1-BLE (OQ-1): SW1 uses a non-metallic pusher (zirconia or PEEK
  class), same rule as SW5. SW2, SW3, SW4 keep metal pushers. SW1 window
  and position unchanged. The F-03 lead note is therefore replaced: SW1
  is evaluated like SW5 and is not pre-ordained to R2-S12.
```

**Q-R2-BOSS-MATERIAL (OQ-2)** (G4_R2_BRIEF.md section 17.1, round 2, DECIDED (second round))

```text
- Q-R2-BOSS-MATERIAL (OQ-2): boss growth inside a reserved region must be
  non-conductive (dielectric sector material or dielectric insert) and is
  recorded as a G5 input. Conductive boss growth inside a reserved region
  is new metal and fails R2-H15. Existing frozen midcase metal is not
  "new".
```

**Q-R2-K1A correction (OQ-3)** (G4_R2_BRIEF.md section 17.1, round 2, DECIDED (second round))

```text
- Q-R2-K1A correction (OQ-3): the earlier answer "MAIN schematic-only" was
  wrong. Correct scope: K1-A = REAR layout/routing with all G3-B-S14 part
  positions frozen, plus MAIN power-schematic fixes; no MAIN outline,
  placement or routing. It moves nothing G4-R2 relies on.
```

C-R2-01 (recorded here only; `G4_R1_BRIEF.md` is unchanged): C-R1-01 item 2 (v) for the non-conductive land reads: "clears screws, supports, CHG_ROUTE and CHG_LINK in 3-D, i.e. separated in plan OR in Z, with strict 3-D clearance".

## 18. Owner questions raised by the tool (conditional; the tool decides none)

- **Q-R2-SUPPORT-RING**: The four BATTERY-level case-side supports (G4 layout, SUP_SW / SUP_SE / SUP_NE / SUP_WNW) occupy the outer annulus the raised cup wall must rise into. Decide how the wall and the supports share it: (a) relieve / relocate the supports so that they start above the cup wall top (the second ledger quantifies this: 4 violating pairs as pinned, 0 with the supports starting at Z 4.630 mm), (b) keep the supports and confine the wall to the REAR band (spigot shortfall -0.300 mm; the hard deflection check then fails), or (c) another support concept. `{"ext_free_as_pinned_mm": 0.0, "ext_free_supports_relieved_mm": 1.5, "required_wall_top_mm": 4.48, "spigot_shortfall_rear_only_mm": -0.3}`

## 19. Supplier gates with numeric thresholds

**LPR433736**
- SR-BATT-PACK / PCM / GROWTH: finished-pack drawing (diameter, thickness incl. PCM fold, PCM lobe, exit, growth). Threshold `{"assumed_envelope": {"finished_diameter_max_mm": 37.5, "growth_axial_mm": 0.5, "growth_radial_mm": 1.0, "thickness_add_max_mm": 0.3}, "clean_offsets": 0, "offsets_evaluated": 145}`
- SR-CASEBACK-CERAMIC: qualified zirconia-class allowable for the cup geometry and process. Threshold `{"planning_MPa": 150.0, "sigma_allow_req_MPa": 410.645}`
- gasket / O-ring: cs tolerance class, compression set, material vs the planning windows. Threshold `{"smallest_gland_feasible_cs_mm": 1.5}`
- SR-CHG-MECH: block, land, FT-C, drop / harness envelope. Threshold `{"r_lim_cup_required_mm": 24.031393161, "strict_wedge_land_mm": 0.153212696}`
- SR-LRA: class envelopes incl. lead / exit, mount, magnet data. Threshold `{"bcu_max_annulus_mm": 5.1, "bcu_need_mm": {"LRA-COIN-D10": 11.0, "LRA-COIN-D8": 9.0, "LRA-LIN-RECT": 5.3}, "fcu_height_cap_mm": 2.7, "fcu_height_threshold_incl_mount_mm": 2.55}`
- SR-FPC-MECH: J1501 B.Cu axial mate: mated height, stiffener, mouth, R_bend_min. Threshold `{"J1501_need_radial_room_mm": 4.9, "R_bend_used_mm": 2.0, "best_room_mm": 5.1}`
- SR-BUTTONS: pusher, stem O-ring / boot, SW1 / SW5 non-metallic material data, dielectric boss growth. Threshold `{"SW1": {"T1:PEEK": 3.7, "T1:zirconia": 3.32, "T2-F:PEEK": 1.13, "T2-F:zirconia": 1.13, "T2-R:PEEK": 2.93, "T2-R:zirconia": 2.93}, "SW2": {"T1:metal": 2.1, "T2-F:metal": 1.06, "T2-R:metal": 2.86}, "SW3": {"T1:metal": 2.1, "T2-F:metal": 1.06, "T2-R:metal": 2.86}, "SW4": {"T1:metal": 2.1, "T2-F:metal": 1.06, "T2-R:metal": 2.86}, "SW5": {"T1:PEEK": 3.7, "T1:zirconia": 3.32, "T2-F:PEEK": 1.13, "T2-F:zirconia": 1.13, "T2-R:PEEK": 2.93, "T2-R:zirconia": 2.93}}`
- SR-WINDOW / SR-COVER-LENS / SR-DISPLAY-LAND: as R1. Threshold `"see the R1 record"`

**LPR403736**
- SR-BATT-PACK / PCM / GROWTH: finished-pack drawing (diameter, thickness incl. PCM fold, PCM lobe, exit, growth). Threshold `{"assumed_envelope": {"finished_diameter_max_mm": 37.5, "growth_axial_mm": 0.5, "growth_radial_mm": 1.0, "thickness_add_max_mm": 0.3}, "clean_offsets": 0, "offsets_evaluated": 145}`
- SR-CASEBACK-CERAMIC: qualified zirconia-class allowable for the cup geometry and process. Threshold `{"planning_MPa": 150.0, "sigma_allow_req_MPa": 410.645}`
- gasket / O-ring: cs tolerance class, compression set, material vs the planning windows. Threshold `{"smallest_gland_feasible_cs_mm": 1.5}`
- SR-CHG-MECH: block, land, FT-C, drop / harness envelope. Threshold `{"r_lim_cup_required_mm": 24.031393161, "strict_wedge_land_mm": 0.338137227}`
- SR-LRA: class envelopes incl. lead / exit, mount, magnet data. Threshold `{"bcu_max_annulus_mm": 5.1, "bcu_need_mm": {"LRA-COIN-D10": 11.0, "LRA-COIN-D8": 9.0, "LRA-LIN-RECT": 5.3}, "fcu_height_cap_mm": 2.7, "fcu_height_threshold_incl_mount_mm": 2.55}`
- SR-FPC-MECH: J1501 B.Cu axial mate: mated height, stiffener, mouth, R_bend_min. Threshold `{"J1501_need_radial_room_mm": 4.9, "R_bend_used_mm": 2.0, "best_room_mm": 5.1}`
- SR-BUTTONS: pusher, stem O-ring / boot, SW1 / SW5 non-metallic material data, dielectric boss growth. Threshold `{"SW1": {"T1:PEEK": 3.7, "T1:zirconia": 3.32, "T2-F:PEEK": 1.13, "T2-F:zirconia": 1.13, "T2-R:PEEK": 2.93, "T2-R:zirconia": 2.93}, "SW2": {"T1:metal": 2.1, "T2-F:metal": 1.06, "T2-R:metal": 2.86}, "SW3": {"T1:metal": 2.1, "T2-F:metal": 1.06, "T2-R:metal": 2.86}, "SW4": {"T1:metal": 2.1, "T2-F:metal": 1.06, "T2-R:metal": 2.86}, "SW5": {"T1:PEEK": 3.7, "T1:zirconia": 3.32, "T2-F:PEEK": 1.13, "T2-F:zirconia": 1.13, "T2-R:PEEK": 2.93, "T2-R:zirconia": 2.93}}`
- SR-WINDOW / SR-COVER-LENS / SR-DISPLAY-LAND: as R1. Threshold `"see the R1 record"`

## 20. G5 input records for non-conductive items inside reserved regions (material, permittivity class label, volume)

**LPR433736** (32 records; no numeric permittivity is invented; G5_RF_REQUIRED)

| item | region | level | part | material class | permittivity class (label) | V nominal mm3 | V linear-worst mm3 |
|---|---|---|---|---|---|---|---|
| SW1_BOOT_OR_ORING | BLE | MAIN | clock | ELASTOMER | elastomer (boot / O-ring) | 2.49 | 2.49 |
| SW1_PUSHER[PEEK] | BLE | MAIN | clock | PEEK | PEEK class thermoplastic | 2.49 | 2.49 |
| SW1_PUSHER[zirconia] | BLE | MAIN | clock | MAT-CERAMIC | UNLABELLED | 2.49 | 2.49 |
| CARRIER_ENVELOPE | GNSS | BATTERY | clock | MAT-GF-POLY | glass-filled engineering polymer | 47.05 | 47.05 |
| CUP_ORING | GNSS | BATTERY | clock | ELASTOMER | elastomer (boot / O-ring) | 7.33 | 7.33 |
| CUP_WALL_RING | GNSS | BATTERY | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 25.38 | 25.77 |
| CARRIER_ENVELOPE | GNSS | BATTERY | volume | MAT-GF-POLY | glass-filled engineering polymer | 50.15 | 50.15 |
| CUP_ORING | GNSS | BATTERY | volume | ELASTOMER | elastomer (boot / O-ring) | 4.41 | 4.41 |
| CUP_WALL_RING | GNSS | BATTERY | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 18.03 | 18.30 |
| CUP_ORING | GNSS | REAR | clock | ELASTOMER | elastomer (boot / O-ring) | 22.28 | 22.28 |
| CUP_PLATE_OUTER | GNSS | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 33.90 | 34.46 |
| CUP_RIM_FLANGE | GNSS | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 2.70 | 2.75 |
| CUP_WALL_RING | GNSS | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 61.03 | 61.03 |
| CUP_ORING | GNSS | REAR | volume | ELASTOMER | elastomer (boot / O-ring) | 13.39 | 13.39 |
| CUP_PLATE_OUTER | GNSS | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 34.97 | 35.55 |
| CUP_RIM_FLANGE | GNSS | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 0.24 | 0.24 |
| CUP_WALL_RING | GNSS | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 43.34 | 43.34 |
| SW5_BOOT_OR_ORING | WIFI | MAIN | clock | ELASTOMER | elastomer (boot / O-ring) | 5.25 | 5.25 |
| SW5_PUSHER[PEEK] | WIFI | MAIN | clock | PEEK | PEEK class thermoplastic | 5.25 | 5.25 |
| SW5_PUSHER[zirconia] | WIFI | MAIN | clock | MAT-CERAMIC | UNLABELLED | 5.25 | 5.25 |
| SW5_BOOT_OR_ORING | WIFI | MAIN | volume | ELASTOMER | elastomer (boot / O-ring) | 9.35 | 9.35 |
| SW5_BOSS_GROWTH | WIFI | MAIN | volume | MAT-GF-POLY | glass-filled engineering polymer | 11.64 | 11.64 |
| SW5_PUSHER[PEEK] | WIFI | MAIN | volume | PEEK | PEEK class thermoplastic | 9.35 | 9.35 |
| SW5_PUSHER[zirconia] | WIFI | MAIN | volume | MAT-CERAMIC | UNLABELLED | 9.35 | 9.35 |
| CUP_ORING | WIFI | REAR | clock | ELASTOMER | elastomer (boot / O-ring) | 22.42 | 22.42 |
| CUP_PLATE_OUTER | WIFI | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 27.61 | 28.07 |
| CUP_RIM_FLANGE | WIFI | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 16.30 | 16.57 |
| CUP_WALL_RING | WIFI | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 61.21 | 61.21 |
| CUP_ORING | WIFI | REAR | volume | ELASTOMER | elastomer (boot / O-ring) | 13.21 | 13.21 |
| CUP_PLATE_OUTER | WIFI | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 7.41 | 7.53 |
| CUP_RIM_FLANGE | WIFI | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 11.90 | 12.10 |
| CUP_WALL_RING | WIFI | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 34.65 | 34.65 |

**LPR403736** (32 records; no numeric permittivity is invented; G5_RF_REQUIRED)

| item | region | level | part | material class | permittivity class (label) | V nominal mm3 | V linear-worst mm3 |
|---|---|---|---|---|---|---|---|
| SW1_BOOT_OR_ORING | BLE | MAIN | clock | ELASTOMER | elastomer (boot / O-ring) | 2.49 | 2.49 |
| SW1_PUSHER[PEEK] | BLE | MAIN | clock | PEEK | PEEK class thermoplastic | 2.49 | 2.49 |
| SW1_PUSHER[zirconia] | BLE | MAIN | clock | MAT-CERAMIC | UNLABELLED | 2.49 | 2.49 |
| CARRIER_ENVELOPE | GNSS | BATTERY | clock | MAT-GF-POLY | glass-filled engineering polymer | 44.33 | 44.33 |
| CUP_ORING | GNSS | BATTERY | clock | ELASTOMER | elastomer (boot / O-ring) | 3.02 | 3.02 |
| CUP_WALL_RING | GNSS | BATTERY | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 19.57 | 19.96 |
| CARRIER_ENVELOPE | GNSS | BATTERY | volume | MAT-GF-POLY | glass-filled engineering polymer | 47.25 | 47.25 |
| CUP_ORING | GNSS | BATTERY | volume | ELASTOMER | elastomer (boot / O-ring) | 1.81 | 1.81 |
| CUP_WALL_RING | GNSS | BATTERY | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 13.90 | 14.17 |
| CUP_ORING | GNSS | REAR | clock | ELASTOMER | elastomer (boot / O-ring) | 26.59 | 26.59 |
| CUP_PLATE_OUTER | GNSS | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 33.90 | 34.46 |
| CUP_RIM_FLANGE | GNSS | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 2.70 | 2.75 |
| CUP_WALL_RING | GNSS | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 66.84 | 66.84 |
| CUP_ORING | GNSS | REAR | volume | ELASTOMER | elastomer (boot / O-ring) | 15.98 | 15.98 |
| CUP_PLATE_OUTER | GNSS | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 34.97 | 35.55 |
| CUP_RIM_FLANGE | GNSS | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 0.24 | 0.24 |
| CUP_WALL_RING | GNSS | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 47.47 | 47.47 |
| SW5_BOOT_OR_ORING | WIFI | MAIN | clock | ELASTOMER | elastomer (boot / O-ring) | 5.25 | 5.25 |
| SW5_PUSHER[PEEK] | WIFI | MAIN | clock | PEEK | PEEK class thermoplastic | 5.25 | 5.25 |
| SW5_PUSHER[zirconia] | WIFI | MAIN | clock | MAT-CERAMIC | UNLABELLED | 5.25 | 5.25 |
| SW5_BOOT_OR_ORING | WIFI | MAIN | volume | ELASTOMER | elastomer (boot / O-ring) | 9.35 | 9.35 |
| SW5_BOSS_GROWTH | WIFI | MAIN | volume | MAT-GF-POLY | glass-filled engineering polymer | 11.64 | 11.64 |
| SW5_PUSHER[PEEK] | WIFI | MAIN | volume | PEEK | PEEK class thermoplastic | 9.35 | 9.35 |
| SW5_PUSHER[zirconia] | WIFI | MAIN | volume | MAT-CERAMIC | UNLABELLED | 9.35 | 9.35 |
| CUP_ORING | WIFI | REAR | clock | ELASTOMER | elastomer (boot / O-ring) | 26.76 | 26.76 |
| CUP_PLATE_OUTER | WIFI | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 27.61 | 28.07 |
| CUP_RIM_FLANGE | WIFI | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 16.30 | 16.57 |
| CUP_WALL_RING | WIFI | REAR | clock | MAT-CERAMIC | technical ceramic (zirconia class) | 67.04 | 67.04 |
| CUP_ORING | WIFI | REAR | volume | ELASTOMER | elastomer (boot / O-ring) | 15.76 | 15.76 |
| CUP_PLATE_OUTER | WIFI | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 7.41 | 7.53 |
| CUP_RIM_FLANGE | WIFI | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 11.90 | 12.10 |
| CUP_WALL_RING | WIFI | REAR | volume | MAT-CERAMIC | technical ceramic (zirconia class) | 37.95 | 37.95 |

## 21. BUILDER-INTERPRETATIONS (conservative readings of silent or ambiguous brief text)

- **B-01** (6.5 / 8 V08-V10): Connector body footprints are the pinned G2 option window rectangles (J1501 8.3 x 4.6, J201 3.4 x 2.9, J202 3.5 x 3.0 mm), oriented with the long side tangential or radial; no body drawing exists. SR-FPC-MECH / SR-BATT-PCM / SR-CHG-MECH decide.
- **B-02** (6.7 / 6.8 / 7.2.1): The G4 case-side support (BATTERY + REAR levels) is carried at BATTERY level only: a continuous raised cup wall occupies the REAR-level periphery and a post there would interrupt it (ring continuity, seal). The G4 plan layout is unchanged; the Z extent is the pinned BATTERY level.
- **B-03** (7.1.2): K_t 2.0 is applied at the pod-frame (inner) junction, at the ring-plate junction, at the charger feedthrough hole radii and at the ring; the stress without the inner-junction K_t is reported beside sigma_allow_req.
- **B-04** (6.2 / R2-V07): The PCM lobe envelope is authored (radial protrusion 1.5 / 2.5 / 3.0 mm, tangential width 5.0 / 6.5 / 8.0 mm, Z = pack Z); the design azimuth is 230 deg and the carrier / lobe conflicts are evaluated at 220, 230 and 240 deg.
- **B-05** (7.1.2): Ring section = wall radial width x [plate bottom, wall top] minus the gland groove; the plate outer edge is the ring centroid radius (conservative span); the plate in-plane response uses the Lame solution of the outer-region thickness; the radial hoop pressure on the exposed wall is added in magnitude; the ring is continuous over 360 deg (the charger land and the lug-root screws lie outside the wall radius).
- **B-06** (4.3 / 6.4): Z gaps use the nominal layer boundaries, each solid's own adverse growth, and the dimension-chain tolerance of the layers fully between the two references; the pack top is the battery-zone top minus c_axial; B.Cu items hang from the B.Cu plane at their linear-worst height.
- **B-07** (R2-V24): The MAIN-outline column is the Ø46 development disk plus growth arcs up to the G4 maximum outline; growth arcs exclude the closed reserved intervals and the frozen switch windows, shrunk by the PCB outline positional tolerance angle.
- **B-08** (6.9 / 17.2 item 15): Reserved solid = clock interval over the radiator radial span union the radiator volume, at the volume's pinned Z levels (FRONT = front gap + display + cover). The pack and the PCM lobe are new conductive components; carrier, cup, O-ring, SW1 / SW5 pushers / boots / dielectric boss growth are allowed non-conductive items with G5 records; volumes are cell-sampled (0.2 mm).
- **B-09** (8): No offset satisfies every constraint; the joint offset is the one with the fewest total violations (reserved-region hits + carrier conflicts), then the supports, then the radial room; exact connector placement is run for the five best-ranked offsets.
- **B-10** (8): A lane is "failed" when its predicate is false at every grid point with D <= 50.9 mm (the largest grid D whose OD margin 51.00 - (D + 2 tol) is >= 0); the joint D is the smallest D at which every other lane passes; tw is the thinnest passing wall.
- **B-11** (7.1 / 8): The design cup is the configuration that passes the hard deflection check with the least intrusion (ring widening 0, then the lowest wall top, then the lowest stress); the smallest gland-feasible cross-section is the design row; other rows are reported as alternatives.
- **B-12** (6.5): FPC / tail / drop paths are polylines (tail exit -> lower-web groove -> foot bend at the adverse bend radius -> vertical riser; tail: PCM exit at pack mid-thickness -> riser; drop: FT-C inner face -> riser); the service slack (adverse 30 mm) is a planar U-loop pocket in the REAR-periphery band.
- **B-13** (17.1.2): Q-R2-SUPPORT-RING (conditional, tool-raised): the over-allocation between the BATTERY-level case supports and the raised cup wall is quantified by a second ledger in which the supports start above the cup wall top; this is a quantification, not a decision.
- **B-14** (numerical): Disks and sectors are exact (analytic) in the clearance kernel; polygon supersets (circumscribed) are used elsewhere with a documented 0.01 mm allowance (POLY_SLACK_MM) that is never a credit.
- **B-15** (7.5.2): The F.Cu fallback exclusions are the pinned F.Cu courtyards, the U101 shield polygon, DISP_FPC, ALS, SWD, DISP_LAND, the MAIN-level radiator / reserved regions and MAG_CLEAR; the body must lie under the display (r <= R_display) with c_lra_plan.
- **B-16** (7.3): The charger block height allocation maximum is the lower-web underside (adverse) minus c_insert; it is an SR-CHG-MECH allocation threshold, not a credit.
- **B-17** (6.8): The occupancy ledger is cell-sampled (0.5 mm); the exact pair table decides clearance; the double-occupied cell count is reported per band.
- **B-18** (7.4): For each switch / topology / pusher class the smallest closing boss is found by an exact reduction verified with the production predicates (bore margin rises 1:1 with the boss, protrusion falls with it); the occupant footprint of a switch is the union over its closing options.
- **B-19** (7.7): A1-A11 keep identities, order, parts, directions and battery states; only the operation text of A1, A4, A5, A6, A9, A10, A11 changes and each change cites its decision id; A5 stays after A4 (the LRA is bonded on the MAIN sub-assembly before the stack closes, inside A4/A5 content).
- **B-20** (budgets): Runtimes are printed by check / selftest and recorded in the run report only (a timestamp or runtime inside a byte-compared file would break determinism); the JSON carries evaluation counts and the budgets.
- **B-22** (8 (exact reductions)): The pose search stops evaluating a candidate pose at its first violated clearance pair (the pass / fail answer is identical to the exhaustive evaluation; verified against the exhaustive evaluation on a pose sample in the self-test, pa_early_exit_equals_exhaustive); the evaluation counter counts the pair predicates actually evaluated.
- **B-21** (run governance): The launch spec left the expected HEAD placeholder unfilled; the tool pins and verifies the R2 contract commit 8f89904 recorded in inputs.r2_contract_commit (the parent is the R1 record 27f7a3a).

## 22. Known documentation debt (recorded; not edited by R2)

- generated/g4_r1_blockers.md line 5 and generated/g4_r1_blockers.json.status still say "R1 study result (uncommitted; independent review pending)" although the files are committed at 27f7a3a; they are immutable and are not edited by R2 (P-4: the R2 status string states no commit or review state)
- inputs/input_register.json still carries the frozen invariant "Battery LPR454440 selected; not replaceable without owner authorization" and the 2026-10-11 wording of OD-CONN-SIDE / OD-J202; the 2026-10-17 decisions are that authorization and are recorded only in the R2 files (a later lead state record updates the register)

## 23. Search, budgets and scope

- predicate evaluations: 2438800 (budget 3000000, within budget True)
- G4 in-process reproduction: pass True, self-tests 32/32, ALLOWED_CHANGES extension equals R1_FILES | R2_FILES exactly: True
- changed paths (all within R2_FILES): ['design/mechanical/G4_R2_BRIEF.md', 'design/mechanical/inputs/g4_r2_closure.json', 'design/mechanical/tools/g4_r2_closure.py']; outside R2_FILES: []
- runtimes are printed by `check` and `selftest` and recorded in the run report (a runtime inside a byte-compared file would break determinism).
