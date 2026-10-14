# G3 — REAR optical + guarded-analog placement study

**G3 CONDITIONAL — SUPPLIER/MEASUREMENT GATES OPEN**

G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES. No G2 supplier gate is closed; G4 and KiCad implementation are not authorized.

Evidence classes are inherited per object in the JSON. Candidate geometry is PROVISIONAL_ASSUMPTION; computed distances are PROJECT_DERIVED. Manufacturer citations and unresolved data are explicit.

## Selection and hard-rule finding

Selected candidate: G3-B-S14.

OD-G3-MAX86141-PKG is applied only to fixed same-package adjacency within the owning MAX86141 courtyard. No global guard or spacing reduction is applied. D3 PGND reserves via-in-pad escape; PD_IN remains zero-via, guarded, with adjacent ground and NT401/NT402 single-point ties. Package-boundary guard reservations remain continuous outside the courtyard; HDI realization remains SR-REAR-PCB.

Hard aggressor clearance is edge-to-edge: ordered loop reservation plus finite trace width and participating pad extents against the PD shield. Circular/roundrect pads use conservative bounding rectangles, never centre-only clearance. Locality distances are pad-centre-to-ball-centre; optical distances are package-centre-to-package-centre; courtyard, thermal and reservation gaps are edge-to-edge. The package pitch diagnostic is centre-to-centre; the package corridor bound is centre-to-edge and exempt.

Loop hard checks use the ordered cap → anode → cathode → mux → driver → PGND → cap polygon, decomposed with even-odd fill at self crossings. Convex hull is an additional diagnostic only and cannot reject a candidate. All horizontal-first and vertical-first single-elbow orthogonal entry alternatives are evaluated deterministically; hard clearance eligibility precedes maximum gap, then length and orientation tie-break.

The footprint/pin map/orientation is unchanged. Existing 0.254 mm lands remain an AN1891 / 21-100134 manufacturer-evidence gate. A geometry rejection requires placement correction, not an owner waiver.

Optical coverage/symmetry and loop area are ranking metrics, not physiological performance requirements. All nominal hard checks filter eligibility before ranking.

| Candidate | Outcome | In-range measured pairs | Worst PD_IN mm | Min cell gap mm | Pod mm² | Nominal failures |
|---|---|---:|---:|---:|---:|---|
| G3-A — G1 mirrored groups, AFEs toward south tail | REJECTED | 16/24 | 4.450 | 0.781 | 547.555 | outline_containment, pd_in_paths, shield_aggressor_exclusion |
| G3-B — Central emitters with peripheral PDs | REJECTED | 16/24 | 3.250 | 0.781 | 456.667 | shield_aggressor_exclusion |
| G3-C — Staggered north/south AFE groups | REJECTED | 16/24 | 3.250 | 0.781 | 495.381 | decoupling_locality, shield_aggressor_exclusion |
| G3-B-S12 — Central topology: G3-B-S12 | CONDITIONAL | 16/24 | 3.250 | 0.781 | 456.667 | none |
| G3-B-S13 — Central topology: G3-B-S13 | CONDITIONAL | 16/24 | 3.250 | 0.781 | 411.997 | none |
| G3-B-S14 — Central topology: G3-B-S14 | RECOMMENDED | 16/24 | 3.250 | 0.781 | 411.997 | none |

## Placement correction search

Every trial is screened on the same nominal pad/guard and courtyard predicates. Any hard failure rejects it; survivors receive all three-corner optical, thermal, tail, support and stack checks and section 7 ranking. No optimality claimed outside this finite design space.

| Trial | LED5 U12/U13 edge gap mm | Screening failures | Full evaluation failures |
|---|---|---|---|
| G3-B-S01 | 0.265000 / 0.265000 | shield_aggressor_exclusion | not needed: nominal hard failure |
| G3-B-S02 | 0.215000 / 0.215000 | shield_aggressor_exclusion | not needed: nominal hard failure |
| G3-B-S03 | 0.518000 / 0.518000 | courtyard_nonoverlap | not needed: nominal hard failure |
| G3-B-S04 | 0.462000 / 0.462000 | courtyard_nonoverlap, shield_aggressor_exclusion | not needed: nominal hard failure |
| G3-B-S05 | 0.408000 / 0.408000 | courtyard_nonoverlap, shield_aggressor_exclusion | not needed: nominal hard failure |
| G3-B-S06 | 0.717000 / 0.717000 | courtyard_nonoverlap | not needed: nominal hard failure |
| G3-B-S07 | 0.656000 / 0.656000 | courtyard_nonoverlap | not needed: nominal hard failure |
| G3-B-S08 | 0.598000 / 0.598000 | courtyard_nonoverlap | not needed: nominal hard failure |
| G3-B-S09 | 0.912000 / 0.912000 | courtyard_nonoverlap | not needed: nominal hard failure |
| G3-B-S10 | 0.847000 / 0.847000 | courtyard_nonoverlap | not needed: nominal hard failure |
| G3-B-S11 | 0.785000 / 0.785000 | courtyard_nonoverlap | not needed: nominal hard failure |
| G3-B-S12 | 0.518000 / 0.518000 | none | none |
| G3-B-S13 | 0.717000 / 0.717000 | none | none |
| G3-B-S14 | 0.912000 / 0.912000 | none | none |

## Physical optical channel map

| AFE | LED/site | Wavelength nm | Physical chip/package | Cathode pins | Mux/input | AFE driver |
|---|---|---:|---|---|---|---|
| U12 | 1/A | 536 | D401 | 1,7,8 | U402.A1 | D1 |
| U12 | 2/A | 660 | D401 | 5 | U403.A1 | C1 |
| U12 | 3/A | 850 | D405 | 2 | U404.A1 | B1 |
| U12 | 4/B | 536 | D403 | 1,7,8 | U402.C1 | D1 |
| U12 | 5/B | 660 | D403 | 5 | U403.C1 | C1 |
| U12 | 6/B | 850 | D406 | 2 | U404.C1 | B1 |
| U13 | 1/A | 536 | D402 | 1,7,8 | U405.A1 | D1 |
| U13 | 2/A | 660 | D402 | 5 | U406.A1 | C1 |
| U13 | 3/A | 850 | D407 | 2 | U407.A1 | B1 |
| U13 | 4/B | 536 | D404 | 1,7,8 | U405.C1 | D1 |
| U13 | 5/B | 660 | D404 | 5 | U406.C1 | C1 |
| U13 | 6/B | 940 | D402 | 3 | U407.C1 | B1 |

PPG2 LED6 is the IR940 chip in D402, despite its logical site-B role. It is not D404. D401/D403/D404 IR cathodes remain unconnected. All 24 interface positions and 13 nets are compared to the actual netlist; no REAR-local analog net crosses the interface.

- D424.1 → U12.D5 (PD1).
- D414.1 → U12.D4 (PD2).
- D423.1 → U13.D5 (PD1).
- D413.1 → U13.D4 (PD2).

## Candidate placement and checks

### G3-A

| Ref | Face | REAR X,Y mm | Rotation deg | Assembly X,Y mm |
|---|---|---|---:|---|
| C1501 | inner | -6.025, 12.180 | 0.000 | 106.025, 112.180 |
| C403 | inner | -4.200, 9.000 | 180.000 | 104.200, 109.000 |
| C404 | inner | -7.200, 9.000 | 180.000 | 107.200, 109.000 |
| C405 | inner | -10.200, 9.000 | 180.000 | 110.200, 109.000 |
| C406 | inner | 4.200, 9.000 | 0.000 | 95.800, 109.000 |
| C407 | inner | 7.200, 9.000 | 0.000 | 92.800, 109.000 |
| C408 | inner | 10.200, 9.000 | 0.000 | 89.800, 109.000 |
| C4101 | inner | -5.700, 4.500 | 180.000 | 105.700, 104.500 |
| C4102 | inner | -6.800, 3.000 | 270.000 | 106.800, 103.000 |
| C4103 | skin | -9.500, 4.500 | 270.000 | 109.500, 104.500 |
| C4104 | inner | -5.400, 6.000 | 180.000 | 105.400, 106.000 |
| C4201 | inner | 5.700, 4.500 | 0.000 | 94.300, 104.500 |
| C4202 | inner | 6.800, 3.000 | 270.000 | 93.200, 103.000 |
| C4203 | skin | 9.500, 4.500 | 270.000 | 90.500, 104.500 |
| C4204 | inner | 5.400, 6.000 | 0.000 | 94.600, 106.000 |
| C802 | skin | 0.000, -12.000 | 0.000 | 100.000, 88.000 |
| D401 | skin | -3.200, 3.000 | 180.000 | 103.200, 103.000 |
| D402 | skin | 3.200, 3.000 | 0.000 | 96.800, 103.000 |
| D403 | skin | -2.900, -1.500 | 180.000 | 102.900, 98.500 |
| D404 | skin | 2.900, -1.500 | 0.000 | 97.100, 98.500 |
| D405 | skin | -2.400, 6.500 | 180.000 | 102.400, 106.500 |
| D406 | skin | -6.200, 6.000 | 180.000 | 106.200, 106.000 |
| D407 | skin | 2.400, 6.500 | 0.000 | 97.600, 106.500 |
| D413 | skin | 6.700, -1.200 | 90.000 | 93.300, 98.800 |
| D414 | skin | -6.700, -1.200 | 90.000 | 106.700, 98.800 |
| D423 | skin | 10.700, 1.200 | 0.000 | 89.300, 101.200 |
| D424 | skin | -10.700, 1.200 | 180.000 | 110.700, 101.200 |
| J1502 | inner | -3.025, 12.180 | 166.050 | 103.025, 112.180 |
| NT401 | skin | -10.000, 2.900 | 180.000 | 110.000, 102.900 |
| NT402 | skin | 10.000, 2.900 | 0.000 | 90.000, 102.900 |
| R401 | inner | -6.000, -10.000 | 90.000 | 106.000, 90.000 |
| R402 | inner | -4.000, -10.000 | 90.000 | 104.000, 90.000 |
| R403 | inner | -2.000, -10.000 | 90.000 | 102.000, 90.000 |
| R404 | inner | 0.000, -10.000 | 90.000 | 100.000, 90.000 |
| R405 | inner | 2.000, -10.000 | 90.000 | 98.000, 90.000 |
| R408 | inner | 4.000, -10.000 | 90.000 | 96.000, 90.000 |
| R409 | inner | 6.000, -10.000 | 90.000 | 94.000, 90.000 |
| U12 | skin | -7.200, 3.000 | 180.000 | 107.200, 103.000 |
| U13 | skin | 7.200, 3.000 | 0.000 | 92.800, 103.000 |
| U402 | skin | -4.200, 9.000 | 180.000 | 104.200, 109.000 |
| U403 | skin | -7.200, 9.000 | 180.000 | 107.200, 109.000 |
| U404 | skin | -10.200, 9.000 | 180.000 | 110.200, 109.000 |
| U405 | skin | 4.200, 9.000 | 0.000 | 95.800, 109.000 |
| U406 | skin | 7.200, 9.000 | 0.000 | 92.800, 109.000 |
| U407 | skin | 10.200, 9.000 | 0.000 | 89.800, 109.000 |
| U6 | skin | 0.000, -14.000 | 0.000 | 100.000, 86.000 |

Coordinates are authored provisional placements or tool-enumerated reservations, never KiCad changes. Assembly transform is x_a = 100 − x_r, y_a = 100 + y_r; wrist view east is left.

| Nominal hard check | Result |
|---|---|
| ambient_edge_path | PASS |
| cell_barrier_gap | PASS |
| courtyard_nonoverlap | PASS |
| decoupling_locality | PASS |
| face_allocation | PASS |
| height_ceilings | PASS |
| individual_ground_vias | PASS |
| led_loops_clear | PASS |
| lower_web | PASS |
| optical_clearance_suballocation | PASS |
| outline_containment | FAIL |
| outline_rmax | PASS |
| pd_ground_shield_connected | PASS |
| pd_ground_ties | PASS |
| pd_in_paths | FAIL |
| pod_contains_all_skin | PASS |
| shield_aggressor_exclusion | FAIL |
| stack_zero_delta | PASS |
| support_lands | PASS |
| tail_fit | PASS |
| thermal_locality | PASS |
| vref_baseline | PASS |

| Corner | Hard failures | PD corridor width mm |
|---|---|---:|
| conservative | lower_web, courtyard_nonoverlap, outline_containment, cell_barrier_gap, pd_in_paths, shield_aggressor_exclusion, support_lands | 0.600 |
| nominal | outline_containment, pd_in_paths, shield_aggressor_exclusion | 0.512 |
| optimistic | pd_in_paths, shield_aggressor_exclusion | 0.425 |

| AFE/LED | PD | Wavelength nm | Package-centre distance mm | Study range |
|---|---|---:|---:|---|
| U12/1 | D424 | 536 | 7.713 | covered |
| U12/1 | D414 | 536 | 5.467 | covered |
| U12/2 | D424 | 660 | 7.713 | covered |
| U12/2 | D414 | 660 | 5.467 | covered |
| U12/3 | D424 | 850 | 9.848 | outside; ranking only |
| U12/3 | D414 | 850 | 8.819 | outside; ranking only |
| U12/4 | D424 | 536 | 8.254 | outside; ranking only |
| U12/4 | D414 | 536 | 3.812 | covered |
| U12/5 | D424 | 660 | 8.254 | outside; ranking only |
| U12/5 | D414 | 660 | 3.812 | covered |
| U12/6 | D424 | 850 | 6.580 | covered |
| U12/6 | D414 | 850 | 7.217 | covered |
| U13/1 | D423 | 536 | 7.713 | covered |
| U13/1 | D413 | 536 | 5.467 | covered |
| U13/2 | D423 | 660 | 7.713 | covered |
| U13/2 | D413 | 660 | 5.467 | covered |
| U13/3 | D423 | 850 | 9.848 | outside; ranking only |
| U13/3 | D413 | 850 | 8.819 | outside; ranking only |
| U13/4 | D423 | 536 | 8.254 | outside; ranking only |
| U13/4 | D413 | 536 | 3.812 | covered |
| U13/5 | D423 | 660 | 8.254 | outside; ranking only |
| U13/5 | D413 | 660 | 3.812 | covered |
| U13/6 | D423 | 940 | 7.713 | covered |
| U13/6 | D413 | 940 | 5.467 | covered |

Cross-AFE minimum emitter–PD distance: 9.605 mm. Required cell gap: 0.700 mm. Symmetry, per-wavelength bins, apertures and W0/W1/W2 flags are recorded in the JSON at every corner.

| PD path | Length mm | Vias | Foreign pad intrusions | C_PD(0 V) maximum for 0x1 pF |
|---|---:|---:|---|---:|
| D424 → U12.D5 | 2.650 | 0 | none | 64.470 |
| D414 → U12.D4 | 3.250 | 0 | none | 64.350 |
| D423 → U13.D5 | 3.850 | 0 | C4203.1 | 64.230 |
| D413 → U13.D4 | 4.450 | 0 | U13.A4, U13.B4, U13.C4 | 64.110 |

PD_IN zero vias is PROJECT_DERIVED; the 6.0 mm path ceiling and fab dimensions are PROVISIONAL_ASSUMPTION. MAX86141 shielding, adjacent ground, single-point connection and individual capacitor ground-via guidance are MANUFACTURER_VERIFIED (Rev5 pp49–52). Regions/loops are reservation envelopes, not routing verification.

| Tie | Distance to C5 mm | Single-point netlist | Locality |
|---|---:|---|---|
| NT401 | 1.503 | True | True |
| NT402 | 1.530 | True | True |

| Decoupler/passive | Target | Distance mm | Limit mm | Vias | Check |
|---|---|---:|---:|---:|---|
| C4101 | U12.C2 | 2.321 | 3 | 1 | True |
| C4102 | U12.D2 | 0.120 | 2 | 1 | True |
| C4103 | U12.B5 | 1.710 | 2 | 0 | True |
| C4104 | U12.A1 | 2.820 | 4 | 1 | True |
| C4201 | U13.C2 | 2.046 | 3 | 1 | True |
| C4202 | U13.D2 | 1.080 | 2 | 1 | True |
| C4203 | U13.B5 | 1.933 | 2 | 0 | True |
| C4204 | U13.A1 | 3.892 | 4 | 1 | True |
| C403 | U402.C2 | 0.789 | 2 | 1 | True |
| C404 | U403.C2 | 0.789 | 2 | 1 | True |
| C405 | U404.C2 | 0.789 | 2 | 1 | True |
| C406 | U405.C2 | 0.789 | 2 | 1 | True |
| C407 | U406.C2 | 0.789 | 2 | 1 | True |
| C408 | U407.C2 | 0.789 | 2 | 1 | True |
| R401 | U12,U13 | 13.055 | None | 1 | True |
| R402 | U12,U13 | 13.388 | None | 1 | True |
| R403 | U12,U13 | 14.001 | None | 1 | True |
| R404 | U12,U13 | 14.861 | None | 1 | True |
| R405 | U12,U13 | 14.001 | None | 1 | True |
| R408 | U12,U13 | 13.388 | None | 1 | True |
| R409 | U12,U13 | 13.055 | None | 1 | True |

| VREF inner alternative | Direct projection | Vias | Distance mm | Outcome |
|---|---|---:|---:|---|
| C4103 | True | 1 | 1.296 | REJECTED |
| C4203 | True | 1 | 1.296 | REJECTED |

| LED loop | Ordered polygon gap mm | Copper extent gap mm (edge-to-edge) | Convex hull gap mm (diagnostic only) | Hard result |
|---|---:|---:|---:|---|
| U12 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U12 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U12 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U12 LED4 | 1.215000 | 0.825000 | 0.000000 | PASS |
| U12 LED5 | 0.370000 | 0.317000 | 0.000000 | FAIL |
| U12 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED1 | 1.587000 | 1.161000 | 1.587000 | PASS |
| U13 LED2 | 1.273000 | 1.227000 | 1.273000 | PASS |
| U13 LED3 | 0.939000 | 0.879000 | 0.939000 | PASS |
| U13 LED4 | 1.215000 | 0.825000 | 0.000000 | PASS |
| U13 LED5 | 0.783000 | 0.729000 | 0.160000 | PASS |
| U13 LED6 | 0.939000 | 0.879000 | 0.939000 | PASS |

| VLED target | Orientation | Edge-to-edge gap mm | Selected |
|---|---|---:|---|
| U12.A1 | horizontal-first | 2.428000 | True |
| U12.A1 | vertical-first | 2.248000 | False |
| U13.A1 | horizontal-first | 2.065000 | True |
| U13.A1 | vertical-first | 1.524000 | False |

Exact remaining nominal aggressor failures:
- U12-LED5 → U12: 0.317000 mm edge-to-edge < 0.500 mm.
- U12-LED5-discretionary → U12: 0.317000 mm edge-to-edge < 0.500 mm.

J1502 geometric alternative: **two_row-r12.55-a166.05**, 2 row(s), pitch 0.250 mm, land 3.450 × 1.800 mm; single-row tail width 6.450 mm. Sector fit: True; outline/thermode fit: True; inside nominal G2 attach window: False. The full alternative sweep and conservative/optimistic results remain in the JSON. Supplier fanout/land qualification remains open.

U6 selected by thermal-proxy ranking at assembly azimuth 0.000°, radius 14.000 mm: emitter gap 9.493 mm, AFE/mux/entry gap 15.289 mm, tail gap 23.852 mm, isolated perimeter 0.900. Neck carries 4 unique nets. No skin-temperature accuracy claim.

| Reservation | Outline overlap mm² | Plan clearance mm | Disposition |
|---|---:|---:|---|
| CHG_CONTACT | 0.000 | 1.100 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_LINK | 0.000 | 3.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_ROUTE | 0.000 | 0.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| FPC_UNDER | 25.492 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| LRA | 28.431 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| MAG_CLEAR | 150.586 | 0.000 | MEASUREMENT_GATED X16; no magnetic claim |

Curved-reservation overlap areas use disclosed arc tessellation; chord sagitta ≤0.001 mm. Courtyard polygon collisions and tail-sector containment are evaluated directly. Charger 3-D distances are lower bounds equal to plan gaps because qualified corridor Z envelopes are absent.

- U6 to CHG_CONTACT: plan / minimum 3-D distance 18.693 mm.
- U6 to CHG_LINK: plan / minimum 3-D distance 24.736 mm.
- U6 to CHG_ROUTE: plan / minimum 3-D distance 22.047 mm.
### G3-B

| Ref | Face | REAR X,Y mm | Rotation deg | Assembly X,Y mm |
|---|---|---|---:|---|
| C1501 | inner | -5.724, 10.967 | 0.000 | 105.724, 110.967 |
| C403 | inner | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| C404 | inner | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| C405 | inner | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| C406 | inner | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| C407 | inner | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| C408 | inner | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| C4101 | inner | -4.500, 1.500 | 180.000 | 104.500, 101.500 |
| C4102 | inner | -5.600, 0.000 | 270.000 | 105.600, 100.000 |
| C4103 | skin | -8.300, 1.500 | 270.000 | 108.300, 101.500 |
| C4104 | inner | -4.200, 3.000 | 180.000 | 104.200, 103.000 |
| C4201 | inner | 4.500, -1.500 | 0.000 | 95.500, 98.500 |
| C4202 | inner | 5.600, 0.000 | 90.000 | 94.400, 100.000 |
| C4203 | skin | 8.300, -1.500 | 90.000 | 91.700, 98.500 |
| C4204 | inner | 4.200, -3.000 | 0.000 | 95.800, 97.000 |
| C802 | skin | 0.000, -12.000 | 0.000 | 100.000, 88.000 |
| D401 | skin | -2.000, 0.000 | 180.000 | 102.000, 100.000 |
| D402 | skin | 2.000, 0.000 | 0.000 | 98.000, 100.000 |
| D403 | skin | -1.700, -4.500 | 180.000 | 101.700, 95.500 |
| D404 | skin | 1.700, 4.500 | 0.000 | 98.300, 104.500 |
| D405 | skin | -1.200, 3.500 | 180.000 | 101.200, 103.500 |
| D406 | skin | -5.000, 3.000 | 180.000 | 105.000, 103.000 |
| D407 | skin | 1.200, -3.500 | 0.000 | 98.800, 96.500 |
| D413 | skin | 5.500, 4.200 | 270.000 | 94.500, 104.200 |
| D414 | skin | -5.500, -4.200 | 90.000 | 105.500, 95.800 |
| D423 | skin | 9.500, 1.800 | 0.000 | 90.500, 101.800 |
| D424 | skin | -9.500, -1.800 | 180.000 | 109.500, 98.200 |
| J1502 | inner | -2.724, 10.967 | 256.050 | 102.724, 110.967 |
| NT401 | skin | -8.800, -0.100 | 180.000 | 108.800, 99.900 |
| NT402 | skin | 8.800, 0.100 | 0.000 | 91.200, 100.100 |
| R401 | inner | -6.000, -10.000 | 90.000 | 106.000, 90.000 |
| R402 | inner | -4.000, -10.000 | 90.000 | 104.000, 90.000 |
| R403 | inner | -2.000, -10.000 | 90.000 | 102.000, 90.000 |
| R404 | inner | 0.000, -10.000 | 90.000 | 100.000, 90.000 |
| R405 | inner | 2.000, -10.000 | 90.000 | 98.000, 90.000 |
| R408 | inner | 4.000, -10.000 | 90.000 | 96.000, 90.000 |
| R409 | inner | 6.000, -10.000 | 90.000 | 94.000, 90.000 |
| U12 | skin | -6.000, 0.000 | 180.000 | 106.000, 100.000 |
| U13 | skin | 6.000, 0.000 | 0.000 | 94.000, 100.000 |
| U402 | skin | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| U403 | skin | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| U404 | skin | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| U405 | skin | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| U406 | skin | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| U407 | skin | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| U6 | skin | 0.000, -14.000 | 0.000 | 100.000, 86.000 |

Coordinates are authored provisional placements or tool-enumerated reservations, never KiCad changes. Assembly transform is x_a = 100 − x_r, y_a = 100 + y_r; wrist view east is left.

| Nominal hard check | Result |
|---|---|
| ambient_edge_path | PASS |
| cell_barrier_gap | PASS |
| courtyard_nonoverlap | PASS |
| decoupling_locality | PASS |
| face_allocation | PASS |
| height_ceilings | PASS |
| individual_ground_vias | PASS |
| led_loops_clear | PASS |
| lower_web | PASS |
| optical_clearance_suballocation | PASS |
| outline_containment | PASS |
| outline_rmax | PASS |
| pd_ground_shield_connected | PASS |
| pd_ground_ties | PASS |
| pd_in_paths | PASS |
| pod_contains_all_skin | PASS |
| shield_aggressor_exclusion | FAIL |
| stack_zero_delta | PASS |
| support_lands | PASS |
| tail_fit | PASS |
| thermal_locality | PASS |
| vref_baseline | PASS |

| Corner | Hard failures | PD corridor width mm |
|---|---|---:|
| conservative | lower_web, cell_barrier_gap, pd_in_paths, shield_aggressor_exclusion, tail_fit, support_lands | 0.600 |
| nominal | shield_aggressor_exclusion | 0.512 |
| optimistic | shield_aggressor_exclusion | 0.425 |

| AFE/LED | PD | Wavelength nm | Package-centre distance mm | Study range |
|---|---|---:|---:|---|
| U12/1 | D424 | 536 | 7.713 | covered |
| U12/1 | D414 | 536 | 5.467 | covered |
| U12/2 | D424 | 660 | 7.713 | covered |
| U12/2 | D414 | 660 | 5.467 | covered |
| U12/3 | D424 | 850 | 9.848 | outside; ranking only |
| U12/3 | D414 | 850 | 8.819 | outside; ranking only |
| U12/4 | D424 | 536 | 8.254 | outside; ranking only |
| U12/4 | D414 | 536 | 3.812 | covered |
| U12/5 | D424 | 660 | 8.254 | outside; ranking only |
| U12/5 | D414 | 660 | 3.812 | covered |
| U12/6 | D424 | 850 | 6.580 | covered |
| U12/6 | D414 | 850 | 7.217 | covered |
| U13/1 | D423 | 536 | 7.713 | covered |
| U13/1 | D413 | 536 | 5.467 | covered |
| U13/2 | D423 | 660 | 7.713 | covered |
| U13/2 | D413 | 660 | 5.467 | covered |
| U13/3 | D423 | 850 | 9.848 | outside; ranking only |
| U13/3 | D413 | 850 | 8.819 | outside; ranking only |
| U13/4 | D423 | 536 | 8.254 | outside; ranking only |
| U13/4 | D413 | 536 | 3.812 | covered |
| U13/5 | D423 | 660 | 8.254 | outside; ranking only |
| U13/5 | D413 | 660 | 3.812 | covered |
| U13/6 | D423 | 940 | 7.713 | covered |
| U13/6 | D413 | 940 | 5.467 | covered |

Cross-AFE minimum emitter–PD distance: 6.736 mm. Required cell gap: 0.700 mm. Symmetry, per-wavelength bins, apertures and W0/W1/W2 flags are recorded in the JSON at every corner.

| PD path | Length mm | Vias | Foreign pad intrusions | C_PD(0 V) maximum for 0x1 pF |
|---|---:|---:|---|---:|
| D424 → U12.D5 | 2.650 | 0 | none | 64.470 |
| D414 → U12.D4 | 3.250 | 0 | none | 64.350 |
| D423 → U13.D5 | 2.650 | 0 | none | 64.470 |
| D413 → U13.D4 | 3.250 | 0 | none | 64.350 |

PD_IN zero vias is PROJECT_DERIVED; the 6.0 mm path ceiling and fab dimensions are PROVISIONAL_ASSUMPTION. MAX86141 shielding, adjacent ground, single-point connection and individual capacitor ground-via guidance are MANUFACTURER_VERIFIED (Rev5 pp49–52). Regions/loops are reservation envelopes, not routing verification.

| Tie | Distance to C5 mm | Single-point netlist | Locality |
|---|---:|---|---|
| NT401 | 1.503 | True | True |
| NT402 | 1.503 | True | True |

| Decoupler/passive | Target | Distance mm | Limit mm | Vias | Check |
|---|---|---:|---:|---:|---|
| C4101 | U12.C2 | 2.321 | 3 | 1 | True |
| C4102 | U12.D2 | 0.120 | 2 | 1 | True |
| C4103 | U12.B5 | 1.710 | 2 | 0 | True |
| C4104 | U12.A1 | 2.820 | 4 | 1 | True |
| C4201 | U13.C2 | 2.321 | 3 | 1 | True |
| C4202 | U13.D2 | 0.120 | 2 | 1 | True |
| C4203 | U13.B5 | 1.710 | 2 | 0 | True |
| C4204 | U13.A1 | 2.820 | 4 | 1 | True |
| C403 | U402.C2 | 0.789 | 2 | 1 | True |
| C404 | U403.C2 | 0.789 | 2 | 1 | True |
| C405 | U404.C2 | 0.789 | 2 | 1 | True |
| C406 | U405.C2 | 0.789 | 2 | 1 | True |
| C407 | U406.C2 | 0.789 | 2 | 1 | True |
| C408 | U407.C2 | 0.789 | 2 | 1 | True |
| R401 | U12,U13 | 10.000 | None | 1 | True |
| R402 | U12,U13 | 10.198 | None | 1 | True |
| R403 | U12,U13 | 10.770 | None | 1 | True |
| R404 | U12,U13 | 11.662 | None | 1 | True |
| R405 | U12,U13 | 10.770 | None | 1 | True |
| R408 | U12,U13 | 10.198 | None | 1 | True |
| R409 | U12,U13 | 10.000 | None | 1 | True |

| VREF inner alternative | Direct projection | Vias | Distance mm | Outcome |
|---|---|---:|---:|---|
| C4103 | True | 1 | 1.296 | REJECTED |
| C4203 | True | 1 | 1.296 | REJECTED |

| LED loop | Ordered polygon gap mm | Copper extent gap mm (edge-to-edge) | Convex hull gap mm (diagnostic only) | Hard result |
|---|---:|---:|---:|---|
| U12 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U12 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U12 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U12 LED4 | 1.215000 | 0.825000 | 0.000000 | PASS |
| U12 LED5 | 0.370000 | 0.317000 | 0.000000 | FAIL |
| U12 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U13 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U13 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED4 | 1.215000 | 0.825000 | 0.000000 | PASS |
| U13 LED5 | 0.370000 | 0.317000 | 0.000000 | FAIL |
| U13 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |

| VLED target | Orientation | Edge-to-edge gap mm | Selected |
|---|---|---:|---|
| U12.A1 | horizontal-first | 2.428000 | True |
| U12.A1 | vertical-first | 2.248000 | False |
| U13.A1 | horizontal-first | 0.000000 | False |
| U13.A1 | vertical-first | 2.084000 | True |

Exact remaining nominal aggressor failures:
- U12-LED5 → U12: 0.317000 mm edge-to-edge < 0.500 mm.
- U12-LED5-discretionary → U12: 0.317000 mm edge-to-edge < 0.500 mm.
- U13-LED5 → U13: 0.317000 mm edge-to-edge < 0.500 mm.
- U13-LED5-discretionary → U13: 0.317000 mm edge-to-edge < 0.500 mm.

J1502 geometric alternative: **radial-r11.3-a166.05**, 1 row(s), pitch 0.250 mm, land 6.450 × 1.000 mm; single-row tail width 6.450 mm. Sector fit: True; outline/thermode fit: True; inside nominal G2 attach window: False. The full alternative sweep and conservative/optimistic results remain in the JSON. Supplier fanout/land qualification remains open.

U6 selected by thermal-proxy ranking at assembly azimuth 0.000°, radius 14.000 mm: emitter gap 6.493 mm, AFE/mux/entry gap 5.175 mm, tail gap 20.493 mm, isolated perimeter 0.900. Neck carries 4 unique nets. No skin-temperature accuracy claim.

| Reservation | Outline overlap mm² | Plan clearance mm | Disposition |
|---|---:|---:|---|
| CHG_CONTACT | 0.000 | 1.100 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_LINK | 0.000 | 3.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_ROUTE | 0.000 | 0.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| FPC_UNDER | 25.492 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| LRA | 28.431 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| MAG_CLEAR | 150.586 | 0.000 | MEASUREMENT_GATED X16; no magnetic claim |

Curved-reservation overlap areas use disclosed arc tessellation; chord sagitta ≤0.001 mm. Courtyard polygon collisions and tail-sector containment are evaluated directly. Charger 3-D distances are lower bounds equal to plan gaps because qualified corridor Z envelopes are absent.

- U6 to CHG_CONTACT: plan / minimum 3-D distance 18.693 mm.
- U6 to CHG_LINK: plan / minimum 3-D distance 24.736 mm.
- U6 to CHG_ROUTE: plan / minimum 3-D distance 22.047 mm.
### G3-C

| Ref | Face | REAR X,Y mm | Rotation deg | Assembly X,Y mm |
|---|---|---|---:|---|
| C1501 | inner | -5.555, 10.287 | 0.000 | 105.555, 110.287 |
| C403 | inner | -9.000, -3.500 | 90.000 | 109.000, 96.500 |
| C404 | inner | -9.000, -6.500 | 90.000 | 109.000, 93.500 |
| C405 | inner | -9.000, -9.500 | 90.000 | 109.000, 90.500 |
| C406 | inner | 9.000, 3.500 | 270.000 | 91.000, 103.500 |
| C407 | inner | 9.000, 6.500 | 270.000 | 91.000, 106.500 |
| C408 | inner | 9.000, 9.500 | 270.000 | 91.000, 109.500 |
| C4101 | inner | -4.500, -5.000 | 90.000 | 104.500, 95.000 |
| C4102 | inner | -3.000, -6.100 | 180.000 | 103.000, 93.900 |
| C4103 | skin | -4.500, -8.800 | 180.000 | 104.500, 91.200 |
| C4104 | inner | -6.000, -4.700 | 90.000 | 106.000, 95.300 |
| C4201 | inner | 4.500, 5.000 | 270.000 | 95.500, 105.000 |
| C4202 | inner | 3.000, 6.100 | 0.000 | 97.000, 106.100 |
| C4203 | skin | 4.500, 8.800 | 0.000 | 95.500, 108.800 |
| C4204 | inner | 6.000, 4.700 | 270.000 | 94.000, 104.700 |
| C802 | skin | 11.258, -4.500 | 0.000 | 88.742, 95.500 |
| D401 | skin | -3.000, -2.500 | 90.000 | 103.000, 97.500 |
| D402 | skin | 3.000, 2.500 | 270.000 | 97.000, 102.500 |
| D403 | skin | 1.500, -2.200 | 90.000 | 98.500, 97.800 |
| D404 | skin | -1.500, 2.200 | 270.000 | 101.500, 102.200 |
| D405 | skin | -6.500, -1.700 | 90.000 | 106.500, 98.300 |
| D406 | skin | -6.000, -5.500 | 90.000 | 106.000, 94.500 |
| D407 | skin | 6.500, 1.700 | 270.000 | 93.500, 101.700 |
| D413 | skin | -1.200, 6.000 | 180.000 | 101.200, 106.000 |
| D414 | skin | 1.200, -6.000 | 0.000 | 98.800, 94.000 |
| D423 | skin | 1.200, 10.000 | 270.000 | 98.800, 110.000 |
| D424 | skin | -1.200, -10.000 | 90.000 | 101.200, 90.000 |
| J1502 | inner | -2.555, 10.287 | 256.050 | 102.555, 110.287 |
| NT401 | skin | -2.900, -9.300 | 90.000 | 102.900, 90.700 |
| NT402 | skin | 2.900, 9.300 | 270.000 | 97.100, 109.300 |
| R401 | inner | -6.000, -10.000 | 90.000 | 106.000, 90.000 |
| R402 | inner | -4.000, -10.000 | 90.000 | 104.000, 90.000 |
| R403 | inner | -2.000, -10.000 | 90.000 | 102.000, 90.000 |
| R404 | inner | 0.000, -10.000 | 90.000 | 100.000, 90.000 |
| R405 | inner | 2.000, -10.000 | 90.000 | 98.000, 90.000 |
| R408 | inner | 4.000, -10.000 | 90.000 | 96.000, 90.000 |
| R409 | inner | 6.000, -10.000 | 90.000 | 94.000, 90.000 |
| U12 | skin | -3.000, -6.500 | 90.000 | 103.000, 93.500 |
| U13 | skin | 3.000, 6.500 | 270.000 | 97.000, 106.500 |
| U402 | skin | -9.000, -3.500 | 90.000 | 109.000, 96.500 |
| U403 | skin | -9.000, -6.500 | 90.000 | 109.000, 93.500 |
| U404 | skin | -9.000, -9.500 | 90.000 | 109.000, 90.500 |
| U405 | skin | 9.000, 3.500 | 270.000 | 91.000, 103.500 |
| U406 | skin | 9.000, 6.500 | 270.000 | 91.000, 106.500 |
| U407 | skin | 9.000, 9.500 | 270.000 | 91.000, 109.500 |
| U6 | skin | 11.258, -6.500 | 0.000 | 88.742, 93.500 |

Coordinates are authored provisional placements or tool-enumerated reservations, never KiCad changes. Assembly transform is x_a = 100 − x_r, y_a = 100 + y_r; wrist view east is left.

| Nominal hard check | Result |
|---|---|
| ambient_edge_path | PASS |
| cell_barrier_gap | PASS |
| courtyard_nonoverlap | PASS |
| decoupling_locality | FAIL |
| face_allocation | PASS |
| height_ceilings | PASS |
| individual_ground_vias | PASS |
| led_loops_clear | PASS |
| lower_web | PASS |
| optical_clearance_suballocation | PASS |
| outline_containment | PASS |
| outline_rmax | PASS |
| pd_ground_shield_connected | PASS |
| pd_ground_ties | PASS |
| pd_in_paths | PASS |
| pod_contains_all_skin | PASS |
| shield_aggressor_exclusion | FAIL |
| stack_zero_delta | PASS |
| support_lands | PASS |
| tail_fit | PASS |
| thermal_locality | PASS |
| vref_baseline | PASS |

| Corner | Hard failures | PD corridor width mm |
|---|---|---:|
| conservative | lower_web, cell_barrier_gap, pd_in_paths, decoupling_locality, shield_aggressor_exclusion, tail_fit | 0.600 |
| nominal | decoupling_locality, shield_aggressor_exclusion | 0.512 |
| optimistic | decoupling_locality, shield_aggressor_exclusion | 0.425 |

| AFE/LED | PD | Wavelength nm | Package-centre distance mm | Study range |
|---|---|---:|---:|---|
| U12/1 | D424 | 536 | 7.713 | covered |
| U12/1 | D414 | 536 | 5.467 | covered |
| U12/2 | D424 | 660 | 7.713 | covered |
| U12/2 | D414 | 660 | 5.467 | covered |
| U12/3 | D424 | 850 | 9.848 | outside; ranking only |
| U12/3 | D414 | 850 | 8.819 | outside; ranking only |
| U12/4 | D424 | 536 | 8.254 | outside; ranking only |
| U12/4 | D414 | 536 | 3.812 | covered |
| U12/5 | D424 | 660 | 8.254 | outside; ranking only |
| U12/5 | D414 | 660 | 3.812 | covered |
| U12/6 | D424 | 850 | 6.580 | covered |
| U12/6 | D414 | 850 | 7.217 | covered |
| U13/1 | D423 | 536 | 7.713 | covered |
| U13/1 | D413 | 536 | 5.467 | covered |
| U13/2 | D423 | 660 | 7.713 | covered |
| U13/2 | D413 | 660 | 5.467 | covered |
| U13/3 | D423 | 850 | 9.848 | outside; ranking only |
| U13/3 | D413 | 850 | 8.819 | outside; ranking only |
| U13/4 | D423 | 536 | 8.254 | outside; ranking only |
| U13/4 | D413 | 536 | 3.812 | covered |
| U13/5 | D423 | 660 | 8.254 | outside; ranking only |
| U13/5 | D413 | 660 | 3.812 | covered |
| U13/6 | D423 | 940 | 7.713 | covered |
| U13/6 | D413 | 940 | 5.467 | covered |

Cross-AFE minimum emitter–PD distance: 8.633 mm. Required cell gap: 0.700 mm. Symmetry, per-wavelength bins, apertures and W0/W1/W2 flags are recorded in the JSON at every corner.

| PD path | Length mm | Vias | Foreign pad intrusions | C_PD(0 V) maximum for 0x1 pF |
|---|---:|---:|---|---:|
| D424 → U12.D5 | 2.650 | 0 | none | 64.470 |
| D414 → U12.D4 | 3.250 | 0 | none | 64.350 |
| D423 → U13.D5 | 2.650 | 0 | none | 64.470 |
| D413 → U13.D4 | 3.250 | 0 | none | 64.350 |

PD_IN zero vias is PROJECT_DERIVED; the 6.0 mm path ceiling and fab dimensions are PROVISIONAL_ASSUMPTION. MAX86141 shielding, adjacent ground, single-point connection and individual capacitor ground-via guidance are MANUFACTURER_VERIFIED (Rev5 pp49–52). Regions/loops are reservation envelopes, not routing verification.

| Tie | Distance to C5 mm | Single-point netlist | Locality |
|---|---:|---|---|
| NT401 | 1.503 | True | True |
| NT402 | 1.503 | True | True |

| Decoupler/passive | Target | Distance mm | Limit mm | Vias | Check |
|---|---|---:|---:|---:|---|
| C4101 | U12.C2 | 2.321 | 3 | 1 | True |
| C4102 | U12.D2 | 0.120 | 2 | 1 | True |
| C4103 | U12.B5 | 1.710 | 2 | 0 | True |
| C4104 | U12.A1 | 2.820 | 4 | 1 | True |
| C4201 | U13.C2 | 2.321 | 3 | 1 | True |
| C4202 | U13.D2 | 0.120 | 2 | 1 | True |
| C4203 | U13.B5 | 1.710 | 2 | 0 | True |
| C4204 | U13.A1 | 2.820 | 4 | 1 | True |
| C403 | U402.C2 | 0.789 | 2 | 1 | True |
| C404 | U403.C2 | 0.789 | 2 | 1 | True |
| C405 | U404.C2 | 0.789 | 2 | 1 | True |
| C406 | U405.C2 | 0.789 | 2 | 1 | True |
| C407 | U406.C2 | 0.789 | 2 | 1 | True |
| C408 | U407.C2 | 0.789 | 2 | 1 | True |
| R401 | U12,U13 | 4.610 | None | 1 | True |
| R402 | U12,U13 | 3.640 | None | 1 | True |
| R403 | U12,U13 | 3.640 | None | 1 | False |
| R404 | U12,U13 | 4.610 | None | 1 | False |
| R405 | U12,U13 | 6.103 | None | 1 | True |
| R408 | U12,U13 | 7.826 | None | 1 | True |
| R409 | U12,U13 | 9.657 | None | 1 | True |

| VREF inner alternative | Direct projection | Vias | Distance mm | Outcome |
|---|---|---:|---:|---|
| C4103 | True | 1 | 1.296 | REJECTED |
| C4203 | True | 1 | 1.296 | REJECTED |

| LED loop | Ordered polygon gap mm | Copper extent gap mm (edge-to-edge) | Convex hull gap mm (diagnostic only) | Hard result |
|---|---:|---:|---:|---|
| U12 LED1 | 2.310000 | 2.044000 | 1.601000 | PASS |
| U12 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U12 LED3 | 1.266000 | 1.250000 | 1.266000 | PASS |
| U12 LED4 | 1.215000 | 0.825000 | 0.000000 | PASS |
| U12 LED5 | 0.370000 | 0.317000 | 0.000000 | FAIL |
| U12 LED6 | 1.266000 | 1.250000 | 1.266000 | PASS |
| U13 LED1 | 2.310000 | 2.044000 | 1.601000 | PASS |
| U13 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U13 LED3 | 1.266000 | 1.250000 | 1.266000 | PASS |
| U13 LED4 | 1.215000 | 0.825000 | 0.000000 | PASS |
| U13 LED5 | 0.370000 | 0.317000 | 0.000000 | FAIL |
| U13 LED6 | 1.266000 | 1.250000 | 1.266000 | PASS |

| VLED target | Orientation | Edge-to-edge gap mm | Selected |
|---|---|---:|---|
| U12.A1 | horizontal-first | 0.381000 | True |
| U12.A1 | vertical-first | 0.000000 | False |
| U13.A1 | horizontal-first | 0.000000 | True |
| U13.A1 | vertical-first | 0.000000 | False |

Exact remaining nominal aggressor failures:
- U12-LED5 → U12: 0.317000 mm edge-to-edge < 0.500 mm.
- U12-LED5-discretionary → U12: 0.317000 mm edge-to-edge < 0.500 mm.
- U13-LED5 → U13: 0.317000 mm edge-to-edge < 0.500 mm.
- U13-LED5-discretionary → U13: 0.317000 mm edge-to-edge < 0.500 mm.
- U12.A2 → U13: 0.381000 mm edge-to-edge < 0.500 mm.
- U12.A3 → U13: 0.381000 mm edge-to-edge < 0.500 mm.
- U12.A4 → U13: 0.381000 mm edge-to-edge < 0.500 mm.
- U12.A5 → U13: 0.381000 mm edge-to-edge < 0.500 mm.
- U12.B2 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U12.B3 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U12-VLED-entry → U13: 0.381000 mm edge-to-edge < 0.500 mm.
- U13.A2 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U13.A3 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U13.A4 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U13.A5 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U13.B2 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U13.B3 → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- U13-VLED-entry → U13: 0.000000 mm edge-to-edge < 0.500 mm.
- J1502 → U13: 0.000000 mm edge-to-edge < 0.500 mm.

J1502 geometric alternative: **radial-r10.6-a166.05**, 1 row(s), pitch 0.250 mm, land 6.450 × 1.000 mm; single-row tail width 6.450 mm. Sector fit: True; outline/thermode fit: True; inside nominal G2 attach window: False. The full alternative sweep and conservative/optimistic results remain in the JSON. Supplier fanout/land qualification remains open.

U6 selected by thermal-proxy ranking at assembly azimuth 300.000°, radius 13.000 mm: emitter gap 6.657 mm, AFE/mux/entry gap 7.363 mm, tail gap 16.862 mm, isolated perimeter 0.900. Neck carries 4 unique nets. No skin-temperature accuracy claim.

| Reservation | Outline overlap mm² | Plan clearance mm | Disposition |
|---|---:|---:|---|
| CHG_CONTACT | 0.000 | 1.100 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_LINK | 0.000 | 3.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_ROUTE | 0.000 | 0.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| FPC_UNDER | 25.492 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| LRA | 28.431 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| MAG_CLEAR | 150.586 | 0.000 | MEASUREMENT_GATED X16; no magnetic claim |

Curved-reservation overlap areas use disclosed arc tessellation; chord sagitta ≤0.001 mm. Courtyard polygon collisions and tail-sector containment are evaluated directly. Charger 3-D distances are lower bounds equal to plan gaps because qualified corridor Z envelopes are absent.

- U6 to CHG_CONTACT: plan / minimum 3-D distance 27.324 mm.
- U6 to CHG_LINK: plan / minimum 3-D distance 11.520 mm.
- U6 to CHG_ROUTE: plan / minimum 3-D distance 9.220 mm.
### G3-B-S12

| Ref | Face | REAR X,Y mm | Rotation deg | Assembly X,Y mm |
|---|---|---|---:|---|
| C1501 | inner | -5.724, 10.967 | 0.000 | 105.724, 110.967 |
| C403 | inner | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| C404 | inner | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| C405 | inner | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| C406 | inner | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| C407 | inner | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| C408 | inner | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| C4101 | inner | -4.500, 1.500 | 180.000 | 104.500, 101.500 |
| C4102 | inner | -5.600, 0.000 | 270.000 | 105.600, 100.000 |
| C4103 | skin | -8.300, 1.500 | 270.000 | 108.300, 101.500 |
| C4104 | inner | -4.200, 3.000 | 180.000 | 104.200, 103.000 |
| C4201 | inner | 4.500, -1.500 | 0.000 | 95.500, 98.500 |
| C4202 | inner | 5.600, 0.000 | 90.000 | 94.400, 100.000 |
| C4203 | skin | 8.300, -1.500 | 90.000 | 91.700, 98.500 |
| C4204 | inner | 4.200, -3.000 | 0.000 | 95.800, 97.000 |
| C802 | skin | 0.000, -12.000 | 0.000 | 100.000, 88.000 |
| D401 | skin | -2.000, 0.000 | 180.000 | 102.000, 100.000 |
| D402 | skin | 2.000, 0.000 | 0.000 | 98.000, 100.000 |
| D403 | skin | -1.400, -4.500 | 180.000 | 101.400, 95.500 |
| D404 | skin | 1.400, 4.500 | 0.000 | 98.600, 104.500 |
| D405 | skin | -1.500, 3.500 | 180.000 | 101.500, 103.500 |
| D406 | skin | -5.000, 3.000 | 180.000 | 105.000, 103.000 |
| D407 | skin | 1.500, -3.500 | 0.000 | 98.500, 96.500 |
| D413 | skin | 5.500, 4.200 | 270.000 | 94.500, 104.200 |
| D414 | skin | -5.500, -4.200 | 90.000 | 105.500, 95.800 |
| D423 | skin | 9.500, 1.800 | 0.000 | 90.500, 101.800 |
| D424 | skin | -9.500, -1.800 | 180.000 | 109.500, 98.200 |
| J1502 | inner | -2.724, 10.967 | 256.050 | 102.724, 110.967 |
| NT401 | skin | -8.800, -0.100 | 180.000 | 108.800, 99.900 |
| NT402 | skin | 8.800, 0.100 | 0.000 | 91.200, 100.100 |
| R401 | inner | -6.000, -10.000 | 90.000 | 106.000, 90.000 |
| R402 | inner | -4.000, -10.000 | 90.000 | 104.000, 90.000 |
| R403 | inner | -2.000, -10.000 | 90.000 | 102.000, 90.000 |
| R404 | inner | 0.000, -10.000 | 90.000 | 100.000, 90.000 |
| R405 | inner | 2.000, -10.000 | 90.000 | 98.000, 90.000 |
| R408 | inner | 4.000, -10.000 | 90.000 | 96.000, 90.000 |
| R409 | inner | 6.000, -10.000 | 90.000 | 94.000, 90.000 |
| U12 | skin | -6.000, 0.000 | 180.000 | 106.000, 100.000 |
| U13 | skin | 6.000, 0.000 | 0.000 | 94.000, 100.000 |
| U402 | skin | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| U403 | skin | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| U404 | skin | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| U405 | skin | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| U406 | skin | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| U407 | skin | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| U6 | skin | 0.000, -14.000 | 0.000 | 100.000, 86.000 |

Coordinates are authored provisional placements or tool-enumerated reservations, never KiCad changes. Assembly transform is x_a = 100 − x_r, y_a = 100 + y_r; wrist view east is left.

| Nominal hard check | Result |
|---|---|
| ambient_edge_path | PASS |
| cell_barrier_gap | PASS |
| courtyard_nonoverlap | PASS |
| decoupling_locality | PASS |
| face_allocation | PASS |
| height_ceilings | PASS |
| individual_ground_vias | PASS |
| led_loops_clear | PASS |
| lower_web | PASS |
| optical_clearance_suballocation | PASS |
| outline_containment | PASS |
| outline_rmax | PASS |
| pd_ground_shield_connected | PASS |
| pd_ground_ties | PASS |
| pd_in_paths | PASS |
| pod_contains_all_skin | PASS |
| shield_aggressor_exclusion | PASS |
| stack_zero_delta | PASS |
| support_lands | PASS |
| tail_fit | PASS |
| thermal_locality | PASS |
| vref_baseline | PASS |

| Corner | Hard failures | PD corridor width mm |
|---|---|---:|
| conservative | lower_web, cell_barrier_gap, pd_in_paths, shield_aggressor_exclusion, tail_fit, support_lands | 0.600 |
| nominal | none | 0.512 |
| optimistic | none | 0.425 |

| AFE/LED | PD | Wavelength nm | Package-centre distance mm | Study range |
|---|---|---:|---:|---|
| U12/1 | D424 | 536 | 7.713 | covered |
| U12/1 | D414 | 536 | 5.467 | covered |
| U12/2 | D424 | 660 | 7.713 | covered |
| U12/2 | D414 | 660 | 5.467 | covered |
| U12/3 | D424 | 850 | 9.596 | outside; ranking only |
| U12/3 | D414 | 850 | 8.677 | outside; ranking only |
| U12/4 | D424 | 536 | 8.538 | outside; ranking only |
| U12/4 | D414 | 536 | 4.111 | covered |
| U12/5 | D424 | 660 | 8.538 | outside; ranking only |
| U12/5 | D414 | 660 | 4.111 | covered |
| U12/6 | D424 | 850 | 6.580 | covered |
| U12/6 | D414 | 850 | 7.217 | covered |
| U13/1 | D423 | 536 | 7.713 | covered |
| U13/1 | D413 | 536 | 5.467 | covered |
| U13/2 | D423 | 660 | 7.713 | covered |
| U13/2 | D413 | 660 | 5.467 | covered |
| U13/3 | D423 | 850 | 9.596 | outside; ranking only |
| U13/3 | D413 | 850 | 8.677 | outside; ranking only |
| U13/4 | D423 | 536 | 8.538 | outside; ranking only |
| U13/4 | D413 | 536 | 4.111 | covered |
| U13/5 | D423 | 660 | 8.538 | outside; ranking only |
| U13/5 | D413 | 660 | 4.111 | covered |
| U13/6 | D423 | 940 | 7.713 | covered |
| U13/6 | D413 | 940 | 5.467 | covered |

Cross-AFE minimum emitter–PD distance: 7.035 mm. Required cell gap: 0.700 mm. Symmetry, per-wavelength bins, apertures and W0/W1/W2 flags are recorded in the JSON at every corner.

| PD path | Length mm | Vias | Foreign pad intrusions | C_PD(0 V) maximum for 0x1 pF |
|---|---:|---:|---|---:|
| D424 → U12.D5 | 2.650 | 0 | none | 64.470 |
| D414 → U12.D4 | 3.250 | 0 | none | 64.350 |
| D423 → U13.D5 | 2.650 | 0 | none | 64.470 |
| D413 → U13.D4 | 3.250 | 0 | none | 64.350 |

PD_IN zero vias is PROJECT_DERIVED; the 6.0 mm path ceiling and fab dimensions are PROVISIONAL_ASSUMPTION. MAX86141 shielding, adjacent ground, single-point connection and individual capacitor ground-via guidance are MANUFACTURER_VERIFIED (Rev5 pp49–52). Regions/loops are reservation envelopes, not routing verification.

| Tie | Distance to C5 mm | Single-point netlist | Locality |
|---|---:|---|---|
| NT401 | 1.503 | True | True |
| NT402 | 1.503 | True | True |

| Decoupler/passive | Target | Distance mm | Limit mm | Vias | Check |
|---|---|---:|---:|---:|---|
| C4101 | U12.C2 | 2.321 | 3 | 1 | True |
| C4102 | U12.D2 | 0.120 | 2 | 1 | True |
| C4103 | U12.B5 | 1.710 | 2 | 0 | True |
| C4104 | U12.A1 | 2.820 | 4 | 1 | True |
| C4201 | U13.C2 | 2.321 | 3 | 1 | True |
| C4202 | U13.D2 | 0.120 | 2 | 1 | True |
| C4203 | U13.B5 | 1.710 | 2 | 0 | True |
| C4204 | U13.A1 | 2.820 | 4 | 1 | True |
| C403 | U402.C2 | 0.789 | 2 | 1 | True |
| C404 | U403.C2 | 0.789 | 2 | 1 | True |
| C405 | U404.C2 | 0.789 | 2 | 1 | True |
| C406 | U405.C2 | 0.789 | 2 | 1 | True |
| C407 | U406.C2 | 0.789 | 2 | 1 | True |
| C408 | U407.C2 | 0.789 | 2 | 1 | True |
| R401 | U12,U13 | 10.000 | None | 1 | True |
| R402 | U12,U13 | 10.198 | None | 1 | True |
| R403 | U12,U13 | 10.770 | None | 1 | True |
| R404 | U12,U13 | 11.662 | None | 1 | True |
| R405 | U12,U13 | 10.770 | None | 1 | True |
| R408 | U12,U13 | 10.198 | None | 1 | True |
| R409 | U12,U13 | 10.000 | None | 1 | True |

| VREF inner alternative | Direct projection | Vias | Distance mm | Outcome |
|---|---|---:|---:|---|
| C4103 | True | 1 | 1.296 | REJECTED |
| C4203 | True | 1 | 1.296 | REJECTED |

| LED loop | Ordered polygon gap mm | Copper extent gap mm (edge-to-edge) | Convex hull gap mm (diagnostic only) | Hard result |
|---|---:|---:|---:|---|
| U12 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U12 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U12 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U12 LED4 | 1.515000 | 1.125000 | 0.000000 | PASS |
| U12 LED5 | 0.573000 | 0.518000 | 0.000000 | PASS |
| U12 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U13 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U13 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED4 | 1.515000 | 1.125000 | 0.000000 | PASS |
| U13 LED5 | 0.573000 | 0.518000 | 0.000000 | PASS |
| U13 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |

| VLED target | Orientation | Edge-to-edge gap mm | Selected |
|---|---|---:|---|
| U12.A1 | horizontal-first | 2.428000 | True |
| U12.A1 | vertical-first | 2.248000 | False |
| U13.A1 | horizontal-first | 0.000000 | False |
| U13.A1 | vertical-first | 2.084000 | True |

Exact remaining nominal aggressor failures:
- None.

J1502 geometric alternative: **radial-r11.3-a166.05**, 1 row(s), pitch 0.250 mm, land 6.450 × 1.000 mm; single-row tail width 6.450 mm. Sector fit: True; outline/thermode fit: True; inside nominal G2 attach window: False. The full alternative sweep and conservative/optimistic results remain in the JSON. Supplier fanout/land qualification remains open.

U6 selected by thermal-proxy ranking at assembly azimuth 0.000°, radius 14.000 mm: emitter gap 6.493 mm, AFE/mux/entry gap 5.175 mm, tail gap 20.493 mm, isolated perimeter 0.900. Neck carries 4 unique nets. No skin-temperature accuracy claim.

| Reservation | Outline overlap mm² | Plan clearance mm | Disposition |
|---|---:|---:|---|
| CHG_CONTACT | 0.000 | 1.100 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_LINK | 0.000 | 3.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_ROUTE | 0.000 | 0.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| FPC_UNDER | 25.492 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| LRA | 28.431 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| MAG_CLEAR | 150.586 | 0.000 | MEASUREMENT_GATED X16; no magnetic claim |

Curved-reservation overlap areas use disclosed arc tessellation; chord sagitta ≤0.001 mm. Courtyard polygon collisions and tail-sector containment are evaluated directly. Charger 3-D distances are lower bounds equal to plan gaps because qualified corridor Z envelopes are absent.

- U6 to CHG_CONTACT: plan / minimum 3-D distance 18.693 mm.
- U6 to CHG_LINK: plan / minimum 3-D distance 24.736 mm.
- U6 to CHG_ROUTE: plan / minimum 3-D distance 22.047 mm.
### G3-B-S13

| Ref | Face | REAR X,Y mm | Rotation deg | Assembly X,Y mm |
|---|---|---|---:|---|
| C1501 | inner | -5.724, 10.967 | 0.000 | 105.724, 110.967 |
| C403 | inner | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| C404 | inner | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| C405 | inner | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| C406 | inner | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| C407 | inner | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| C408 | inner | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| C4101 | inner | -4.500, 1.500 | 180.000 | 104.500, 101.500 |
| C4102 | inner | -5.600, 0.000 | 270.000 | 105.600, 100.000 |
| C4103 | skin | -8.300, 1.500 | 270.000 | 108.300, 101.500 |
| C4104 | inner | -4.200, 3.000 | 180.000 | 104.200, 103.000 |
| C4201 | inner | 4.500, -1.500 | 0.000 | 95.500, 98.500 |
| C4202 | inner | 5.600, 0.000 | 90.000 | 94.400, 100.000 |
| C4203 | skin | 8.300, -1.500 | 90.000 | 91.700, 98.500 |
| C4204 | inner | 4.200, -3.000 | 0.000 | 95.800, 97.000 |
| C802 | skin | -9.192, -7.192 | 0.000 | 109.192, 92.808 |
| D401 | skin | -2.000, 0.000 | 180.000 | 102.000, 100.000 |
| D402 | skin | 2.000, 0.000 | 0.000 | 98.000, 100.000 |
| D403 | skin | -1.100, -4.500 | 180.000 | 101.100, 95.500 |
| D404 | skin | 1.100, 4.500 | 0.000 | 98.900, 104.500 |
| D405 | skin | -1.800, 3.500 | 180.000 | 101.800, 103.500 |
| D406 | skin | -5.000, 3.000 | 180.000 | 105.000, 103.000 |
| D407 | skin | 1.800, -3.500 | 0.000 | 98.200, 96.500 |
| D413 | skin | 5.500, 4.200 | 270.000 | 94.500, 104.200 |
| D414 | skin | -5.500, -4.200 | 90.000 | 105.500, 95.800 |
| D423 | skin | 9.500, 1.800 | 0.000 | 90.500, 101.800 |
| D424 | skin | -9.500, -1.800 | 180.000 | 109.500, 98.200 |
| J1502 | inner | -2.724, 10.967 | 256.050 | 102.724, 110.967 |
| NT401 | skin | -8.800, -0.100 | 180.000 | 108.800, 99.900 |
| NT402 | skin | 8.800, 0.100 | 0.000 | 91.200, 100.100 |
| R401 | inner | -6.000, -10.000 | 90.000 | 106.000, 90.000 |
| R402 | inner | -4.000, -10.000 | 90.000 | 104.000, 90.000 |
| R403 | inner | -2.000, -10.000 | 90.000 | 102.000, 90.000 |
| R404 | inner | 0.000, -10.000 | 90.000 | 100.000, 90.000 |
| R405 | inner | 2.000, -10.000 | 90.000 | 98.000, 90.000 |
| R408 | inner | 4.000, -10.000 | 90.000 | 96.000, 90.000 |
| R409 | inner | 6.000, -10.000 | 90.000 | 94.000, 90.000 |
| U12 | skin | -6.000, 0.000 | 180.000 | 106.000, 100.000 |
| U13 | skin | 6.000, 0.000 | 0.000 | 94.000, 100.000 |
| U402 | skin | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| U403 | skin | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| U404 | skin | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| U405 | skin | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| U406 | skin | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| U407 | skin | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| U6 | skin | -9.192, -9.192 | 0.000 | 109.192, 90.808 |

Coordinates are authored provisional placements or tool-enumerated reservations, never KiCad changes. Assembly transform is x_a = 100 − x_r, y_a = 100 + y_r; wrist view east is left.

| Nominal hard check | Result |
|---|---|
| ambient_edge_path | PASS |
| cell_barrier_gap | PASS |
| courtyard_nonoverlap | PASS |
| decoupling_locality | PASS |
| face_allocation | PASS |
| height_ceilings | PASS |
| individual_ground_vias | PASS |
| led_loops_clear | PASS |
| lower_web | PASS |
| optical_clearance_suballocation | PASS |
| outline_containment | PASS |
| outline_rmax | PASS |
| pd_ground_shield_connected | PASS |
| pd_ground_ties | PASS |
| pd_in_paths | PASS |
| pod_contains_all_skin | PASS |
| shield_aggressor_exclusion | PASS |
| stack_zero_delta | PASS |
| support_lands | PASS |
| tail_fit | PASS |
| thermal_locality | PASS |
| vref_baseline | PASS |

| Corner | Hard failures | PD corridor width mm |
|---|---|---:|
| conservative | lower_web, cell_barrier_gap, pd_in_paths, tail_fit, support_lands | 0.600 |
| nominal | none | 0.512 |
| optimistic | none | 0.425 |

| AFE/LED | PD | Wavelength nm | Package-centre distance mm | Study range |
|---|---|---:|---:|---|
| U12/1 | D424 | 536 | 7.713 | covered |
| U12/1 | D414 | 536 | 5.467 | covered |
| U12/2 | D424 | 660 | 7.713 | covered |
| U12/2 | D414 | 660 | 5.467 | covered |
| U12/3 | D424 | 850 | 9.348 | outside; ranking only |
| U12/3 | D414 | 850 | 8.543 | outside; ranking only |
| U12/4 | D424 | 536 | 8.823 | outside; ranking only |
| U12/4 | D414 | 536 | 4.410 | covered |
| U12/5 | D424 | 660 | 8.823 | outside; ranking only |
| U12/5 | D414 | 660 | 4.410 | covered |
| U12/6 | D424 | 850 | 6.580 | covered |
| U12/6 | D414 | 850 | 7.217 | covered |
| U13/1 | D423 | 536 | 7.713 | covered |
| U13/1 | D413 | 536 | 5.467 | covered |
| U13/2 | D423 | 660 | 7.713 | covered |
| U13/2 | D413 | 660 | 5.467 | covered |
| U13/3 | D423 | 850 | 9.348 | outside; ranking only |
| U13/3 | D413 | 850 | 8.543 | outside; ranking only |
| U13/4 | D423 | 536 | 8.823 | outside; ranking only |
| U13/4 | D413 | 536 | 4.410 | covered |
| U13/5 | D423 | 660 | 8.823 | outside; ranking only |
| U13/5 | D413 | 660 | 4.410 | covered |
| U13/6 | D423 | 940 | 7.713 | covered |
| U13/6 | D413 | 940 | 5.467 | covered |

Cross-AFE minimum emitter–PD distance: 7.333 mm. Required cell gap: 0.700 mm. Symmetry, per-wavelength bins, apertures and W0/W1/W2 flags are recorded in the JSON at every corner.

| PD path | Length mm | Vias | Foreign pad intrusions | C_PD(0 V) maximum for 0x1 pF |
|---|---:|---:|---|---:|
| D424 → U12.D5 | 2.650 | 0 | none | 64.470 |
| D414 → U12.D4 | 3.250 | 0 | none | 64.350 |
| D423 → U13.D5 | 2.650 | 0 | none | 64.470 |
| D413 → U13.D4 | 3.250 | 0 | none | 64.350 |

PD_IN zero vias is PROJECT_DERIVED; the 6.0 mm path ceiling and fab dimensions are PROVISIONAL_ASSUMPTION. MAX86141 shielding, adjacent ground, single-point connection and individual capacitor ground-via guidance are MANUFACTURER_VERIFIED (Rev5 pp49–52). Regions/loops are reservation envelopes, not routing verification.

| Tie | Distance to C5 mm | Single-point netlist | Locality |
|---|---:|---|---|
| NT401 | 1.503 | True | True |
| NT402 | 1.503 | True | True |

| Decoupler/passive | Target | Distance mm | Limit mm | Vias | Check |
|---|---|---:|---:|---:|---|
| C4101 | U12.C2 | 2.321 | 3 | 1 | True |
| C4102 | U12.D2 | 0.120 | 2 | 1 | True |
| C4103 | U12.B5 | 1.710 | 2 | 0 | True |
| C4104 | U12.A1 | 2.820 | 4 | 1 | True |
| C4201 | U13.C2 | 2.321 | 3 | 1 | True |
| C4202 | U13.D2 | 0.120 | 2 | 1 | True |
| C4203 | U13.B5 | 1.710 | 2 | 0 | True |
| C4204 | U13.A1 | 2.820 | 4 | 1 | True |
| C403 | U402.C2 | 0.789 | 2 | 1 | True |
| C404 | U403.C2 | 0.789 | 2 | 1 | True |
| C405 | U404.C2 | 0.789 | 2 | 1 | True |
| C406 | U405.C2 | 0.789 | 2 | 1 | True |
| C407 | U406.C2 | 0.789 | 2 | 1 | True |
| C408 | U407.C2 | 0.789 | 2 | 1 | True |
| R401 | U12,U13 | 10.000 | None | 1 | True |
| R402 | U12,U13 | 10.198 | None | 1 | True |
| R403 | U12,U13 | 10.770 | None | 1 | True |
| R404 | U12,U13 | 11.662 | None | 1 | True |
| R405 | U12,U13 | 10.770 | None | 1 | True |
| R408 | U12,U13 | 10.198 | None | 1 | True |
| R409 | U12,U13 | 10.000 | None | 1 | True |

| VREF inner alternative | Direct projection | Vias | Distance mm | Outcome |
|---|---|---:|---:|---|
| C4103 | True | 1 | 1.296 | REJECTED |
| C4203 | True | 1 | 1.296 | REJECTED |

| LED loop | Ordered polygon gap mm | Copper extent gap mm (edge-to-edge) | Convex hull gap mm (diagnostic only) | Hard result |
|---|---:|---:|---:|---|
| U12 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U12 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U12 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U12 LED4 | 1.769000 | 1.425000 | 0.000000 | PASS |
| U12 LED5 | 0.772000 | 0.717000 | 0.000000 | PASS |
| U12 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U13 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U13 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED4 | 1.769000 | 1.425000 | 0.000000 | PASS |
| U13 LED5 | 0.772000 | 0.717000 | 0.000000 | PASS |
| U13 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |

| VLED target | Orientation | Edge-to-edge gap mm | Selected |
|---|---|---:|---|
| U12.A1 | horizontal-first | 2.428000 | True |
| U12.A1 | vertical-first | 2.248000 | False |
| U13.A1 | horizontal-first | 0.000000 | False |
| U13.A1 | vertical-first | 2.084000 | True |

Exact remaining nominal aggressor failures:
- None.

J1502 geometric alternative: **radial-r11.3-a166.05**, 1 row(s), pitch 0.250 mm, land 6.450 × 1.000 mm; single-row tail width 6.450 mm. Sector fit: True; outline/thermode fit: True; inside nominal G2 attach window: False. The full alternative sweep and conservative/optimistic results remain in the JSON. Supplier fanout/land qualification remains open.

U6 selected by thermal-proxy ranking at assembly azimuth 45.000°, radius 13.000 mm: emitter gap 5.357 mm, AFE/mux/entry gap 6.785 mm, tail gap 16.591 mm, isolated perimeter 0.900. Neck carries 4 unique nets. No skin-temperature accuracy claim.

| Reservation | Outline overlap mm² | Plan clearance mm | Disposition |
|---|---:|---:|---|
| CHG_CONTACT | 0.000 | 1.100 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_LINK | 0.000 | 3.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_ROUTE | 0.000 | 0.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| FPC_UNDER | 25.492 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| LRA | 28.431 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| MAG_CLEAR | 150.586 | 0.000 | MEASUREMENT_GATED X16; no magnetic claim |

Curved-reservation overlap areas use disclosed arc tessellation; chord sagitta ≤0.001 mm. Courtyard polygon collisions and tail-sector containment are evaluated directly. Charger 3-D distances are lower bounds equal to plan gaps because qualified corridor Z envelopes are absent.

- U6 to CHG_CONTACT: plan / minimum 3-D distance 8.367 mm.
- U6 to CHG_LINK: plan / minimum 3-D distance 29.968 mm.
- U6 to CHG_ROUTE: plan / minimum 3-D distance 12.575 mm.
### G3-B-S14

| Ref | Face | REAR X,Y mm | Rotation deg | Assembly X,Y mm |
|---|---|---|---:|---|
| C1501 | inner | -5.724, 10.967 | 0.000 | 105.724, 110.967 |
| C403 | inner | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| C404 | inner | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| C405 | inner | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| C406 | inner | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| C407 | inner | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| C408 | inner | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| C4101 | inner | -4.500, 1.500 | 180.000 | 104.500, 101.500 |
| C4102 | inner | -5.600, 0.000 | 270.000 | 105.600, 100.000 |
| C4103 | skin | -8.300, 1.500 | 270.000 | 108.300, 101.500 |
| C4104 | inner | -4.200, 3.000 | 180.000 | 104.200, 103.000 |
| C4201 | inner | 4.500, -1.500 | 0.000 | 95.500, 98.500 |
| C4202 | inner | 5.600, 0.000 | 90.000 | 94.400, 100.000 |
| C4203 | skin | 8.300, -1.500 | 90.000 | 91.700, 98.500 |
| C4204 | inner | 4.200, -3.000 | 0.000 | 95.800, 97.000 |
| C802 | skin | -9.192, -7.192 | 0.000 | 109.192, 92.808 |
| D401 | skin | -2.000, 0.000 | 180.000 | 102.000, 100.000 |
| D402 | skin | 2.000, 0.000 | 0.000 | 98.000, 100.000 |
| D403 | skin | -0.800, -4.500 | 180.000 | 100.800, 95.500 |
| D404 | skin | 0.800, 4.500 | 0.000 | 99.200, 104.500 |
| D405 | skin | -2.100, 3.500 | 180.000 | 102.100, 103.500 |
| D406 | skin | -5.000, 3.000 | 180.000 | 105.000, 103.000 |
| D407 | skin | 2.100, -3.500 | 0.000 | 97.900, 96.500 |
| D413 | skin | 5.500, 4.200 | 270.000 | 94.500, 104.200 |
| D414 | skin | -5.500, -4.200 | 90.000 | 105.500, 95.800 |
| D423 | skin | 9.500, 1.800 | 0.000 | 90.500, 101.800 |
| D424 | skin | -9.500, -1.800 | 180.000 | 109.500, 98.200 |
| J1502 | inner | -2.724, 10.967 | 256.050 | 102.724, 110.967 |
| NT401 | skin | -8.800, -0.100 | 180.000 | 108.800, 99.900 |
| NT402 | skin | 8.800, 0.100 | 0.000 | 91.200, 100.100 |
| R401 | inner | -6.000, -10.000 | 90.000 | 106.000, 90.000 |
| R402 | inner | -4.000, -10.000 | 90.000 | 104.000, 90.000 |
| R403 | inner | -2.000, -10.000 | 90.000 | 102.000, 90.000 |
| R404 | inner | 0.000, -10.000 | 90.000 | 100.000, 90.000 |
| R405 | inner | 2.000, -10.000 | 90.000 | 98.000, 90.000 |
| R408 | inner | 4.000, -10.000 | 90.000 | 96.000, 90.000 |
| R409 | inner | 6.000, -10.000 | 90.000 | 94.000, 90.000 |
| U12 | skin | -6.000, 0.000 | 180.000 | 106.000, 100.000 |
| U13 | skin | 6.000, 0.000 | 0.000 | 94.000, 100.000 |
| U402 | skin | -3.000, 6.000 | 180.000 | 103.000, 106.000 |
| U403 | skin | -6.000, 6.000 | 180.000 | 106.000, 106.000 |
| U404 | skin | -9.000, 6.000 | 180.000 | 109.000, 106.000 |
| U405 | skin | 3.000, -6.000 | 0.000 | 97.000, 94.000 |
| U406 | skin | 6.000, -6.000 | 0.000 | 94.000, 94.000 |
| U407 | skin | 9.000, -6.000 | 0.000 | 91.000, 94.000 |
| U6 | skin | -9.192, -9.192 | 0.000 | 109.192, 90.808 |

Coordinates are authored provisional placements or tool-enumerated reservations, never KiCad changes. Assembly transform is x_a = 100 − x_r, y_a = 100 + y_r; wrist view east is left.

| Nominal hard check | Result |
|---|---|
| ambient_edge_path | PASS |
| cell_barrier_gap | PASS |
| courtyard_nonoverlap | PASS |
| decoupling_locality | PASS |
| face_allocation | PASS |
| height_ceilings | PASS |
| individual_ground_vias | PASS |
| led_loops_clear | PASS |
| lower_web | PASS |
| optical_clearance_suballocation | PASS |
| outline_containment | PASS |
| outline_rmax | PASS |
| pd_ground_shield_connected | PASS |
| pd_ground_ties | PASS |
| pd_in_paths | PASS |
| pod_contains_all_skin | PASS |
| shield_aggressor_exclusion | PASS |
| stack_zero_delta | PASS |
| support_lands | PASS |
| tail_fit | PASS |
| thermal_locality | PASS |
| vref_baseline | PASS |

| Corner | Hard failures | PD corridor width mm |
|---|---|---:|
| conservative | lower_web, cell_barrier_gap, pd_in_paths, tail_fit, support_lands | 0.600 |
| nominal | none | 0.512 |
| optimistic | none | 0.425 |

| AFE/LED | PD | Wavelength nm | Package-centre distance mm | Study range |
|---|---|---:|---:|---|
| U12/1 | D424 | 536 | 7.713 | covered |
| U12/1 | D414 | 536 | 5.467 | covered |
| U12/2 | D424 | 660 | 7.713 | covered |
| U12/2 | D414 | 660 | 5.467 | covered |
| U12/3 | D424 | 850 | 9.102 | outside; ranking only |
| U12/3 | D414 | 850 | 8.417 | outside; ranking only |
| U12/4 | D424 | 536 | 9.109 | outside; ranking only |
| U12/4 | D414 | 536 | 4.710 | covered |
| U12/5 | D424 | 660 | 9.109 | outside; ranking only |
| U12/5 | D414 | 660 | 4.710 | covered |
| U12/6 | D424 | 850 | 6.580 | covered |
| U12/6 | D414 | 850 | 7.217 | covered |
| U13/1 | D423 | 536 | 7.713 | covered |
| U13/1 | D413 | 536 | 5.467 | covered |
| U13/2 | D423 | 660 | 7.713 | covered |
| U13/2 | D413 | 660 | 5.467 | covered |
| U13/3 | D423 | 850 | 9.102 | outside; ranking only |
| U13/3 | D413 | 850 | 8.417 | outside; ranking only |
| U13/4 | D423 | 536 | 9.109 | outside; ranking only |
| U13/4 | D413 | 536 | 4.710 | covered |
| U13/5 | D423 | 660 | 9.109 | outside; ranking only |
| U13/5 | D413 | 660 | 4.710 | covered |
| U13/6 | D423 | 940 | 7.713 | covered |
| U13/6 | D413 | 940 | 5.467 | covered |

Cross-AFE minimum emitter–PD distance: 7.632 mm. Required cell gap: 0.700 mm. Symmetry, per-wavelength bins, apertures and W0/W1/W2 flags are recorded in the JSON at every corner.

| PD path | Length mm | Vias | Foreign pad intrusions | C_PD(0 V) maximum for 0x1 pF |
|---|---:|---:|---|---:|
| D424 → U12.D5 | 2.650 | 0 | none | 64.470 |
| D414 → U12.D4 | 3.250 | 0 | none | 64.350 |
| D423 → U13.D5 | 2.650 | 0 | none | 64.470 |
| D413 → U13.D4 | 3.250 | 0 | none | 64.350 |

PD_IN zero vias is PROJECT_DERIVED; the 6.0 mm path ceiling and fab dimensions are PROVISIONAL_ASSUMPTION. MAX86141 shielding, adjacent ground, single-point connection and individual capacitor ground-via guidance are MANUFACTURER_VERIFIED (Rev5 pp49–52). Regions/loops are reservation envelopes, not routing verification.

| Tie | Distance to C5 mm | Single-point netlist | Locality |
|---|---:|---|---|
| NT401 | 1.503 | True | True |
| NT402 | 1.503 | True | True |

| Decoupler/passive | Target | Distance mm | Limit mm | Vias | Check |
|---|---|---:|---:|---:|---|
| C4101 | U12.C2 | 2.321 | 3 | 1 | True |
| C4102 | U12.D2 | 0.120 | 2 | 1 | True |
| C4103 | U12.B5 | 1.710 | 2 | 0 | True |
| C4104 | U12.A1 | 2.820 | 4 | 1 | True |
| C4201 | U13.C2 | 2.321 | 3 | 1 | True |
| C4202 | U13.D2 | 0.120 | 2 | 1 | True |
| C4203 | U13.B5 | 1.710 | 2 | 0 | True |
| C4204 | U13.A1 | 2.820 | 4 | 1 | True |
| C403 | U402.C2 | 0.789 | 2 | 1 | True |
| C404 | U403.C2 | 0.789 | 2 | 1 | True |
| C405 | U404.C2 | 0.789 | 2 | 1 | True |
| C406 | U405.C2 | 0.789 | 2 | 1 | True |
| C407 | U406.C2 | 0.789 | 2 | 1 | True |
| C408 | U407.C2 | 0.789 | 2 | 1 | True |
| R401 | U12,U13 | 10.000 | None | 1 | True |
| R402 | U12,U13 | 10.198 | None | 1 | True |
| R403 | U12,U13 | 10.770 | None | 1 | True |
| R404 | U12,U13 | 11.662 | None | 1 | True |
| R405 | U12,U13 | 10.770 | None | 1 | True |
| R408 | U12,U13 | 10.198 | None | 1 | True |
| R409 | U12,U13 | 10.000 | None | 1 | True |

| VREF inner alternative | Direct projection | Vias | Distance mm | Outcome |
|---|---|---:|---:|---|
| C4103 | True | 1 | 1.296 | REJECTED |
| C4203 | True | 1 | 1.296 | REJECTED |

| LED loop | Ordered polygon gap mm | Copper extent gap mm (edge-to-edge) | Convex hull gap mm (diagnostic only) | Hard result |
|---|---:|---:|---:|---|
| U12 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U12 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U12 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U12 LED4 | 2.002000 | 1.725000 | 0.000000 | PASS |
| U12 LED5 | 0.968000 | 0.912000 | 0.000000 | PASS |
| U12 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED1 | 2.365000 | 2.044000 | 1.601000 | PASS |
| U13 LED2 | 1.618000 | 1.161000 | 1.422000 | PASS |
| U13 LED3 | 1.363000 | 1.347000 | 1.363000 | PASS |
| U13 LED4 | 2.002000 | 1.725000 | 0.000000 | PASS |
| U13 LED5 | 0.968000 | 0.912000 | 0.000000 | PASS |
| U13 LED6 | 1.363000 | 1.347000 | 1.363000 | PASS |

| VLED target | Orientation | Edge-to-edge gap mm | Selected |
|---|---|---:|---|
| U12.A1 | horizontal-first | 2.428000 | True |
| U12.A1 | vertical-first | 2.248000 | False |
| U13.A1 | horizontal-first | 0.000000 | False |
| U13.A1 | vertical-first | 2.084000 | True |

Exact remaining nominal aggressor failures:
- None.

J1502 geometric alternative: **radial-r11.3-a166.05**, 1 row(s), pitch 0.250 mm, land 6.450 × 1.000 mm; single-row tail width 6.450 mm. Sector fit: True; outline/thermode fit: True; inside nominal G2 attach window: False. The full alternative sweep and conservative/optimistic results remain in the JSON. Supplier fanout/land qualification remains open.

U6 selected by thermal-proxy ranking at assembly azimuth 45.000°, radius 13.000 mm: emitter gap 5.643 mm, AFE/mux/entry gap 6.785 mm, tail gap 16.591 mm, isolated perimeter 0.900. Neck carries 4 unique nets. No skin-temperature accuracy claim.

| Reservation | Outline overlap mm² | Plan clearance mm | Disposition |
|---|---:|---:|---|
| CHG_CONTACT | 0.000 | 1.100 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_LINK | 0.000 | 3.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| CHG_ROUTE | 0.000 | 0.600 | DEFERRED_G4: preserve charger reservations and reported clearance |
| FPC_UNDER | 25.492 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| LRA | 28.431 | 0.000 | C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section |
| MAG_CLEAR | 150.586 | 0.000 | MEASUREMENT_GATED X16; no magnetic claim |

Curved-reservation overlap areas use disclosed arc tessellation; chord sagitta ≤0.001 mm. Courtyard polygon collisions and tail-sector containment are evaluated directly. Charger 3-D distances are lower bounds equal to plan gaps because qualified corridor Z envelopes are absent.

- U6 to CHG_CONTACT: plan / minimum 3-D distance 8.367 mm.
- U6 to CHG_LINK: plan / minimum 3-D distance 29.968 mm.
- U6 to CHG_ROUTE: plan / minimum 3-D distance 12.575 mm.

## Stack and fabrication

| G2 baseline | Nominal mm | RSS mm | Linear worst mm | G3 nominal delta mm |
|---|---:|---:|---:|---:|
| G2-REVA | 16.350 | 16.796 | 18.040 | 0.000 |
| G2-REVA-HI | 16.380 | 16.825 | 18.040 | 0.000 |

These are conditional height-reservation calculations; zero Z delta does not make a rejected XY topology acceptable. C1501 stays DNP, with a ≤0.650 mm reservation ceiling; no thinned MPN is assumed.

```json
{
  "evidence_class": "PROJECT_DERIVED",
  "g1_range_max_mm": 0.85,
  "inner_max_mm": 0.65,
  "note": "RSS threshold uses imported G2 tolerance sensitivities with the G3 envelope; baseline +0.1 optics uncertainty retained. Nonzero delta still requires owner acceptance.",
  "od_thick_limits": [
    {
      "id": "G2-REVA",
      "nominal_height_limit_mm": 0.9,
      "rss_height_limit_mm": 0.954,
      "rss_threshold_resolution_mm": 0.001
    },
    {
      "id": "G2-REVA-HI",
      "nominal_height_limit_mm": 0.87,
      "rss_height_limit_mm": 0.925,
      "rss_threshold_resolution_mm": 0.001
    }
  ],
  "stack_neutral_skin_max_mm": 0.75
}
```

HDI / filled microvia-in-pad escape is required for B2/B3/B4/C2/C3/C4. At 0.4 mm pitch and 0.254 mm pads, the interpad gap is 0.146 mm; even the optimistic 0.075 mm trace plus two 0.075 mm clearances needs 0.225 mm. Reserve ≥4 layers: L1 PD_IN/coplanar guard, L2 PD_GND islands, L3 solid adjacent GND, L4 inner face. Supplier stackup/drill/fill/plating are unqualified.

```json
{
  "caseback": "Numeric residual handoff only; no caseback/seal design",
  "corners": {
    "conservative": {
      "caseback_residual_after_study_wall_mm": 0.25,
      "caseback_residual_before_wall_mm": 1.05,
      "fpc_plus_clearance_mm": 0.5,
      "lower_web_margin_mm": -0.2,
      "lower_web_mm": 0.3,
      "optical_clearance_mm": 0.2,
      "optical_suballocation_overrun_mm": 0,
      "pod_depth_mm": 1.85,
      "retention_plus_compression_mm": 0.2
    },
    "nominal": {
      "caseback_residual_after_study_wall_mm": 0.05,
      "caseback_residual_before_wall_mm": 0.55,
      "fpc_plus_clearance_mm": 0.32,
      "lower_web_margin_mm": 0.08,
      "lower_web_mm": 0.4,
      "optical_clearance_mm": 0.1,
      "optical_suballocation_overrun_mm": 0,
      "pod_depth_mm": 1.35,
      "retention_plus_compression_mm": 0.1
    },
    "optimistic": {
      "caseback_residual_after_study_wall_mm": -0.05,
      "caseback_residual_before_wall_mm": 0.25,
      "fpc_plus_clearance_mm": 0.2,
      "lower_web_margin_mm": 0.4,
      "lower_web_mm": 0.6,
      "optical_clearance_mm": 0.05,
      "optical_suballocation_overrun_mm": 0,
      "pod_depth_mm": 1.05,
      "retention_plus_compression_mm": 0.05
    }
  },
  "evidence_class": "PROJECT_DERIVED",
  "load_path": "Window → pod frame → three or more stops → carrier; no optical-part or battery compression load",
  "window_delta_from_g2_nominal_mm": {
    "0.3": -0.2,
    "0.5": 0.0,
    "0.8": 0.3
  }
}
```

G3→G4 carries every candidate outline/r_max, pod, aperture/window flags, support positions, U6 contact alternatives, tail and reservation clearances numerically in JSON. No rejected candidate is released. Conservative radial margin **−0.950 mm** and X25 cover fit **−1.100 mm** remain unchanged.

## Supplier and measurement gates

### SR-SFH4053B-DS — OPEN

MANUFACTURER_DATA_REQUIRED. Final G3 closure criterion 10a/b; no 0.45 mm height credited.

```json
{
  "body_and_emitting_area": "Primary package/active-area drawing; rerun all D405–D407 geometry against verified outline, pads and emission position",
  "minimum_emitter_pd_cell_gap_mm": 0.7,
  "seated_max_mm": 0.75
}
```

### SR-MAX86141-LAND — OPEN

MANUFACTURER_DATA_REQUIRED. Land-pattern evidence; footprint geometry and pin map unchanged.

```json
{
  "evidence": "AN1891 / 21-100134 land pattern must verify the existing land geometry; any discrepancy requires a separately authorized footprint review",
  "existing_land_diameter_mm": 0.254,
  "pitch_mm": 0.4
}
```

### SR-MAX86141-HEIGHT — OPEN

MANUFACTURER_DATA_REQUIRED. Criterion 10a.

```json
{
  "outline": "21-100134",
  "seated_max_mm": 0.75
}
```

### SR-TS5A12301E-HEIGHT — OPEN

MANUFACTURER_DATA_REQUIRED. Skin ceiling qualification; 0.5 mm historical placeholder is not manufacturer evidence.

```json
{
  "seated_max_mm": 0.75
}
```

### SR-FPC-MECH — OPEN

SUPPLIER_DATA_REQUIRED. Criterion 10c; >0.05 through 0.08 keeps G2 valid but G3 at most CONDITIONAL; >0.08 outside G2 model.

```json
{
  "arithmetic_ma": 41.333,
  "g2_joint_max_mm": 0.08,
  "g3_joint_max_mm": 0.05,
  "geometry": "Confirm evaluated land width/pitch/rows, physical pin-order drawing, fanout into unchanged FPC_UNDER, tail attachment, strain relief and electrical current rating basis. G2 supplier current requirements remain unchanged.",
  "logical_nets": 13,
  "per_vled_position_continuous_equivalent_min_ma": 41.3,
  "pitch_range_mm": {
    "max": 0.3,
    "min": 0.2,
    "nom": 0.25
  },
  "positions": 24,
  "thermode_keepout_min_mm": 1
}
```

### SR-C1501 — OPEN

SUPPLIER_DATA_REQUIRED. Reservoir population; no thinned part assumed.

```json
{
  "electrical": "DNP remains; qualify effective capacitance/droop/recharge/DC-bias within this envelope before fitting",
  "height_max_mm": 0.65,
  "reservation_depth_mm": 1.2,
  "reservation_width_mm": 2
}
```

### SR-REAR-PCB — OPEN

SUPPLIER_DATA_REQUIRED. Fabrication; any >1.0 mm reported as stack overrun; no qualified stackup exists.

```json
{
  "guard_fab_classes": {
    "evidence_class": "PROVISIONAL_ASSUMPTION",
    "max": 0.1,
    "min": 0.075,
    "nom": 0.087,
    "rationale": "Brief provisional fab class."
  },
  "inner_ball_escape": "Qualified filled/capped microvia-in-pad; supplier supplies drill, dielectric, copper, fill/plating and layer stack",
  "min_layers": 4,
  "stack_neutral_nominal_mm": 0.8,
  "thickness_mm": [
    0.6,
    1.0
  ],
  "wlp_pitch_mm": 0.4
}
```

### SR-WINDOW — OPEN

SUPPLIER_DATA_REQUIRED. Window freeze and MG-WINDOW-XTALK.

```json
{
  "active_area_alignment": "Register active areas to apertures before cutting/moulding",
  "nominal_stack_neutral_mm": 0.5,
  "seal_land_mm": {
    "evidence_class": "PROVISIONAL_ASSUMPTION",
    "max": 0.8,
    "min": 0.3,
    "nom": 0.5,
    "rationale": "Unqualified per-cell seal-land reservation; supplier must qualify."
  },
  "thickness_study_mm": [
    0.3,
    0.5,
    0.8
  ]
}
```

### SR-BARRIER — OPEN

SUPPLIER_DATA_REQUIRED. Barrier/isolation qualification.

```json
{
  "compression_mm": {
    "evidence_class": "PROVISIONAL_ASSUMPTION",
    "max": 0.1,
    "min": 0.025,
    "nom": 0.05,
    "rationale": "Barrier-gasket compression suballocation of c_optics."
  },
  "opacity": "No transmission number invented; measured no-skin pair floor must meet owner MG-WINDOW-XTALK threshold",
  "wall_clearance_mm": {
    "evidence_class": "PROVISIONAL_ASSUMPTION",
    "max": 0.15,
    "min": 0.05,
    "nom": 0.1,
    "rationale": "Brief nominal wall clearance; alignment sensitivity."
  },
  "wall_mm": {
    "evidence_class": "PROVISIONAL_ASSUMPTION",
    "max": 0.5,
    "min": 0.2,
    "nom": 0.35,
    "rationale": "Brief section 6.2 bounded opaque-wall study."
  }
}
```

### SR-ADHESIVE — OPEN

SUPPLIER_DATA_REQUIRED. X22 Z/retention qualification.

```json
{
  "combined_retention_and_compression_max_nominal_mm": 0.1,
  "retention_mm": {
    "evidence_class": "PROVISIONAL_ASSUMPTION",
    "max": 0.1,
    "min": 0.025,
    "nom": 0.05,
    "rationale": "Window retention suballocation of c_optics; no qualified adhesive."
  }
}
```

### SR-PD-CAPACITANCE — OPEN

MANUFACTURER_DATA_REQUIRED. PD bias/noise qualification; 9 pF at 5 V is not a zero-bias value.

```json
{
  "formula": "C_PD(0 V) <= 65 - modelled corridor parasitic; see each path",
  "pdbias": "0x1",
  "total_pd_plus_corridor_max_pf": 65
}
```

### MG-SPACING — OPEN

MEASUREMENT_REQUIRED. Optical spacing/modalities freeze.

```json
{
  "decision": "Owner first specifies green HR, red/IR SpO2 and IR850/IR940 use. Compare wavelength-specific spacing coupons at equal current/timing/phantom and representative wrist loads; choose bins meeting modality criteria; no invented physiological threshold.",
  "metrics": [
    "AC/DC ratio",
    "input-referred SNR",
    "saturation fraction",
    "motion artefact",
    "LED energy per accepted sample"
  ],
  "spacing_mm": [
    3,
    8
  ],
  "wavelengths_nm": [
    536,
    660,
    850,
    940
  ]
}
```

### MG-WINDOW-XTALK — OPEN

MEASUREMENT_REQUIRED. Optical-isolation/window closure.

```json
{
  "decision": "At equal LED current and PPG_TINT compare absorber/open-air floor against phantom and opaque W-ref. Retain W0 only below owner threshold, else test W1/W2 and rerun their geometry/Z.",
  "metrics": [
    "dark-subtracted no-skin input current per physical LED/PD pair",
    "no-skin to phantom response ratio",
    "repeatability across temperature and assembly"
  ],
  "owner_threshold": null,
  "variants": [
    "W0",
    "W1",
    "W2",
    "W-ref"
  ]
}
```

### MG-GUARD — OPEN

MEASUREMENT_REQUIRED. Guarded-analog qualification.

```json
{
  "dark_noise_max_datasheet_multiplier": 1.5,
  "decision": "LEDs off, matched PPG_TINT/PDBIAS/temperature/sample count; compare MAX86141 electrical-characteristics row for that timing. Reject if either provisional threshold fails; investigate shield/return paths. No result fabricated.",
  "metrics": [
    "RMS input-referred dark current at each PD_IN",
    "SPI-active minus SPI-idle RMS noise",
    "PD_GND single-point continuity and return-current verification"
  ],
  "spi_active_noise_increase_max_fraction": 0.1
}
```

### MG-THERMAL — OPEN

MEASUREMENT_REQUIRED. Skin-temperature accuracy.

```json
{
  "decision": "Sweep ambient, phantom temperature, LED duty, idle/active electronics and charger states with repeated mountings. Accept only after owner accuracy target is set and met; otherwise revise island/contact/scheduling.",
  "metrics": [
    "U6 minus calibrated skin-phantom reference steady-state error",
    "temperature shift across LED duty",
    "charging-on/off shift",
    "settling time and hysteresis"
  ],
  "owner_accuracy_target_c": null
}
```

### MG-MAG — OPEN

MEASUREMENT_REQUIRED. MAG_CLEAR closure.

```json
{
  "decision": "X16 O1/O2 disposition; geometry overlap is disclosed, not magnetic qualification.",
  "metrics": [
    "BMM350 field delta by LED duty and charging state",
    "heading error with assembled case"
  ],
  "owner_threshold": null
}
```

## Manufacturing and bring-up

1. Qualify reflow peak/cycle budget for every MPN; MAX30208 local maximum 220 C must be respected.
2. Fixture both sides; populate qualified inner passives first, then skin optical/analog parts subject to component reflow limits.
3. Keep flux and any underfill out of every active-area/window aperture and PD_GND isolation reservation; qualify cleaning.
4. Hot-bar/ACF bond tail after SMT with reserved thermode access.
5. Inspect continuity and guarded-net isolation, then assemble carrier/hard stops.
6. Service by replacing REAR plus tail as one unit through J1501.

MANUFACTURER_DATA_REQUIRED: no complete local all-component cycle qualification.
J1501 approved power/digital only; no REAR-local test pads; new test pad requires schematic ECO/owner authorization.

## Conflict status

| Conflict | G3 status | Evidence |
|---|---|---|
| C1-FRONT-GAP | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| C2-DISPLAY-SIDE-CONNECTORS | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| C3-EDGE-WRAP | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| C4-CHARGER-PATH | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| C5-SOUTH-CROWDING | SUPPLIER_DATA_GATED | Candidate geometry is in g3.candidates; no recommended topology until nominal hard checks pass. Tail alternatives do not change G2 allocation. |
| C6-DISPLAY-FPC-FOLD | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| C7-WIFI-BEYOND-BOARD | DEFERRED_G4 | Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized. |
| C8-GNSS-OCCUPIED | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| C9-THICK-CORNER | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| X10-OPTICS-HEIGHT-UNKNOWN | SUPPLIER_DATA_GATED | Manufacturer height gates remain open; stack-neutral skin maximum and OD-THICK limits are computed in g3.height_thresholds. |
| X11-POD-FOOTPRINT | SUPPLIER_DATA_GATED | Candidate geometry is in g3.candidates; no recommended topology until nominal hard checks pass. Tail alternatives do not change G2 allocation. |
| X12-J1502-FACE | SUPPLIER_DATA_GATED | Candidate geometry is in g3.candidates; no recommended topology until nominal hard checks pass. Tail alternatives do not change G2 allocation. |
| X13-EDGE-CROSSINGS | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| X14-SUPPORT-GAP | DEFERRED_G4 | Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized. |
| X15-NE-CROWDING | DEFERRED_G4 | Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized. |
| X16-MAGNETOMETER | MEASUREMENT_GATED | Computed projected overlaps / window proxies disclosed; MG-MAG, MG-WINDOW-XTALK and thermal measurement cannot be closed by geometry. |
| X17-GNSS-ALL-HEIGHTS | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| X18-PACK-EDGE | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| X19-BCU-0603 | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| X20-GROWTH-VS-OPTICS | SUPPLIER_DATA_GATED | Support reservations and load path computed; carrier load and pack-growth qualification remain open. |
| X21-INGRESS-UNDEFINED | DEFERRED_G4 | Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized. |
| X22-UNMODELLED-Z | DEFERRED_G4 | Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized. |
| X23-WINDOW-CROSSTALK | MEASUREMENT_GATED | Computed projected overlaps / window proxies disclosed; MG-MAG, MG-WINDOW-XTALK and thermal measurement cannot be closed by geometry. |
| X24-DISPLAY-LAND | DEFERRED_G4 | Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized. |
| X25-COVER-CASE-FIT | DEFERRED_G4 | Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized. |
| G2-CROSSING-HEIGHT | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| G2-BOOK-FOLD | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| G2-PROBE-RELIEF | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| G2-BACK-STACK | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |
| G2-DISCOVERED-INTERFACES | REMAINS_OPEN | G3 preserves G2 status and gates; no closure inferred. |

## Acceptance record

| Criterion | Satisfied | Evidence |
|---|---|---|
| 1 | True | Owner decisions copied verbatim; immutable boundary and prior decisions validated |
| 2 | True | Recommended candidate has every nominal hard check passing and all 46 placements recorded |
| 3 | True | Recommended candidate has every nominal hard check passing and all 46 placements recorded |
| 4 | True | Recommended candidate has zero stack delta |
| 5 | True | Numeric height/reservation/process thresholds and missing-data classes stated |
| 6 | True | Four required MG plans and decision logic drafted; no measurements claimed |
| 7 | True | Numeric per-candidate diagnostic handoffs provided; none released if no recommendation |
| 8 | True | Tool enforces source pins, deterministic regeneration and authorized diff scope; run all §10 external validation commands |
| 9 | True | Exact contract verdict used |
| 10 | False | Primary SFH4053B/MAX86141 height, SFH4053B optical/package evidence and supplier-qualified J1502 dimensions/joint/current remain absent |
| 11 | True | G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES recorded outside immutable G2 records |

Generator consistency and mutation self-tests are separate from engineering acceptance. Run all G3_BRIEF §10 commands. No supplier request has been issued. No measurement result has been invented.
