# G4 corrective engineering study

**G4 OWNER DECISION REQUIRED**

BLOCKED / UNRELEASED STUDY. Independent re-review returned PASS AS CORRECT BLOCKED STUDY (owner-provided record). Uncommitted diagnostic package. No complete candidate is selected. No qualification, RF performance, supplier component availability, or G2/G3 reopening is claimed.

The binding brief is unchanged. G3 CLOSED — PASS WITH SUPPLIER/MEASUREMENT GATES is an administrative record; generated G3 history and open gates remain unchanged.

## Verdict and stops

| ID | Finding |
| --- | --- |
| STOP-DIAMETER | No candidate is feasible at D_case_body <= 51.00 mm; minimum required diameter: none found <= 54.00 mm (diameter-independent hard-check failures). |
| STOP-LRA | No feasible LRA pose exists for any envelope class inside the approved architecture at <= 51.0 mm; the LRA is not removed or shrunk. |
| OD-G4-WINDOW | W0 is mechanically eliminated without a stack delta; owner must decide whether a frame/rib-supported window (W1; W2 fails the G3 seal-land geometry) is the Rev-A baseline. |

No owner decision is a substitute for fixing failed geometry. OD-G4-WINDOW remains triggered. OD-G4-ATM-STD, MATERIAL, STRAP and LRA-MAG remain deferred closure decisions. OD-G4-STACK is not triggered: local failures are explicit, but necessary total stack growth has not been proved.

## Diameter, complete checks and ranking

The complete 47.00–51.00 mm grid uses 0.05 mm steps. A reporting-only extension runs to 54.00 mm. Every retained diagnostic point evaluates H01–H25 before ranking. No threshold for a subset of checks is called a feasible diameter.

The Cartesian design space is rejected by an independently computed H15 certificate: for each architecture, at least one mandatory button fails every authored cross-section with the applicable local process. This certificate is independent of diameter and all other design grids. It is fail-closed: if the certificate stops holding, the tool stops pending expanded search. The retained point at each diameter is only a diagnostic representative; group first-pass results below apply to these retained points, not a claim of global group optimality.

Per-point predicate and geometric evidence: `g4_sweep.jsonl` (423 records). Complete passing candidate set: []. Selected diameter: n/a; minimum feasible diameter: n/a; minimum required diameter found through 54 mm: n/a.

| Candidate | Diagnostic D | Outcome | Failing hard checks |
| --- | --- | --- | --- |
| G4-A | 50.900 | REJECTED | H05, H11, H13, H14, H15, H16, H17, H20, H21, H22, H23 |
| G4-B | 50.900 | REJECTED | H01, H05, H13, H15, H17, H20, H21, H22, H23 |
| G4-C | 50.900 | REJECTED | H05, H10, H11, H13, H14, H15, H16, H17, H20, H21, H22, H23 |

| Independent grid group | G4-A | G4-B | G4-C |
| --- | --- | --- | --- |
| BUTTONS | n/a | n/a | n/a |
| CASEBACK | n/a | 52.100 | n/a |
| COVER | 50.100 | 50.100 | 50.100 |
| H03_OD | 47.000 | 47.000 | 47.000 |
| LAND | n/a | n/a | n/a |
| LOAD_PATH | 47.000 | 47.000 | n/a |
| LRA | n/a | n/a | n/a |
| SCREWS | n/a | 47.000 | n/a |
| SIDE_RADIAL | 51.100 | 51.100 | 51.100 |

Independent group thresholds are partial arithmetic only; full H tables govern eligibility. Polymer side-radial requires approximately >=51.10 mm on the 0.05 mm grid (including the polymer sector of G4-B). G4-B caseback/related geometry first passes its comparison group at approximately >=52.10 mm; that group uses the continuous-inner-support comparison, not the perimeter bypass acceptance. These exceed the owner ceiling and do not make a candidate feasible.

One scalar side-wall thickness tw is used per design point at MAIN, BATTERY and REAR. The r_case(az,z) table adds local feature envelopes and level-specific recesses; it does not solve independent t_wall(az,z). No azimuth-resolved wall closure is established.

| Candidate | H05 radial / edge geometry | LRA-coupled feasibility | Complete H05 |
| --- | --- | --- | --- |
| G4-A | no | no | no |
| G4-B | no | no | no |
| G4-C | no | no | no |

Diagnostic order: G4-B, G4-A, G4-C. No rejected candidate is recommended. Ranking includes owner/frozen impact, both HI headrooms, diameter, worst radial/cover margins, supplier term count and normalized threshold demands, pressure/seal margins and seal count, RF distances, charger/screw/LRA distances, and service operations/blind mating/J1 cycles.

| Hard check | Required evaluation | G4-A | G4-B | G4-C |
| --- | --- | --- | --- | --- |
| H01 | exact | PASS | FAIL | PASS |
| H02 | nominal, RSS | PASS | PASS | PASS |
| H03 | linear worst | PASS | PASS | PASS |
| H04 | exact | PASS | PASS | PASS |
| H05 | linear worst | FAIL | FAIL | FAIL |
| H06 | linear worst | PASS | PASS | PASS |
| H07 | G1 conservative | PASS | PASS | PASS |
| H08 | exact | PASS | PASS | PASS |
| H09 | linear worst | PASS | PASS | PASS |
| H10 | linear worst | PASS | PASS | FAIL |
| H11 | linear worst | FAIL | PASS | FAIL |
| H12 | G1 conservative | PASS | PASS | PASS |
| H13 | linear worst | FAIL | FAIL | FAIL |
| H14 | exact | FAIL | PASS | FAIL |
| H15 | linear worst | FAIL | FAIL | FAIL |
| H16 | linear worst | FAIL | PASS | FAIL |
| H17 | exact | FAIL | FAIL | FAIL |
| H18 | exact | PASS | PASS | PASS |
| H19 | linear worst | PASS | PASS | PASS |
| H20 | linear worst | FAIL | FAIL | FAIL |
| H21 | linear worst | FAIL | FAIL | FAIL |
| H22 | linear worst | FAIL | FAIL | FAIL |
| H23 | linear worst | FAIL | FAIL | FAIL |
| H24 | exact | PASS | PASS | PASS |
| H25 | exact | PASS | PASS | PASS |

| Group | G4-A first pass D | G4-B first pass D | G4-C first pass D |
| --- | --- | --- | --- |
| H01 | 47.000 | 47.000 | 47.000 |
| H02 | 47.000 | 47.000 | 47.000 |
| H03 | 47.000 | 47.000 | 47.000 |
| H04 | 47.000 | 47.000 | 47.000 |
| H05 | n/a | n/a | n/a |
| H06 | 50.100 | 50.100 | 50.100 |
| H07 | 47.000 | 47.000 | 47.000 |
| H08 | 47.000 | 47.000 | 47.000 |
| H09 | 47.000 | 47.000 | 47.000 |
| H10 | 47.000 | 47.000 | n/a |
| H11 | n/a | 49.250 | n/a |
| H12 | 47.000 | 47.000 | 47.000 |
| H13 | n/a | n/a | n/a |
| H14 | n/a | 47.000 | n/a |
| H15 | n/a | n/a | n/a |
| H16 | 52.100 | 47.000 | n/a |
| H17 | n/a | n/a | n/a |
| H18 | 47.000 | 47.000 | 47.000 |
| H19 | 48.050 | 49.350 | 48.050 |
| H20 | n/a | n/a | n/a |
| H21 | n/a | n/a | n/a |
| H22 | n/a | n/a | n/a |
| H23 | n/a | n/a | n/a |
| H24 | 50.150 | 50.150 | 50.150 |
| H25 | 47.000 | 47.000 | 47.000 |

## Pressure domains, physical reaction paths and support evidence

### G4-A

Window/frame and caseback loads enter a caseback shell and perimeter/case-side bearing path. No P1 pressure load is assigned to PCB lands. Perimeter quadrant compression/bearing bound uses twice equal sharing; battery posts locate the carrier and are not the pressure reaction;  shear, buckling and ceramic contact remain numeric manufacturer/FEA gates. The continuous-inner-support annular plate is a comparison screen only; this bypass has not established that boundary. P2 retains a forbidden REAR-board branch. No support capacity or G3 land enlargement is established.

| Domain | Area mm² | Force N |
| --- | --- | --- |
| WINDOW_APERTURE | 412.003 | 257.502 |
| POD_FRAME | 48.317 | 30.198 |
| CASEBACK_REMAINDER | 1410.058 | 881.286 |

Partition sum: 1870.378602 mm²; total load 1168.986626 N; perimeter reaction 1168.986626 N; PCB pressure load 0.000 N. Partition check: True. Reaction geometry: continuous midcase rear-face bearing annulus; four case-side quadrants bounded at twice equal sharing; lug-root screws retain caseback.

No PCB pressure path is needed for P1. P2 retains its physically authored REAR-board branch and fails closed. Any forbidden branch fails even when another branch reaches MIDCASE. No G3 support-land enlargement has been demonstrated.

| Mode | Evidence / numeric assumptions |
| --- | --- |
| bearing | available_mm2 39.911 / evidence_class PROVISIONAL_ASSUMPTION / required_contact_area_mm2 16.700 |
| buckling | effective_length_factor 2.000 / evidence_class MANUFACTURER_DATA_REQUIRED / required_inertia_Euler_surrogate_mm4 2.139 / section_inertia_mm4 n/a / unbraced_length_upper_mm 7.950 |
| ceramic_contact | contact_allowable_MPa n/a / evidence_class MANUFACTURER_DATA_REQUIRED / force_bound_N 584.493 / minimum_area_at_planning_allowable_mm2 16.700 / provisional_contact_edge_factor 2.000 / required_qualified_contact_allowable_MPa 29.290 |
| compression | area_mm2 39.911 / evidence_class PROVISIONAL_ASSUMPTION / margin_MPa 20.355 / planning_allowable_MPa 35.000 / stress_MPa 14.645 |
| shear | evidence_class MANUFACTURER_DATA_REQUIRED / planning_allowable_MPa 17.500 / provided_area_mm2 n/a / required_area_mm2 33.400 |

| Case-side bypass screen | Value |
| --- | --- |
| boundary | Area-equivalent rigid central frame loading the caseback shell; zero inner support reaction, continuous perimeter bearing. Disjoint disc plus annulus; no G3 posts or PCB support. |
| deflection_margin_mm | -2.573 |
| equivalent_loaded_frame_radius_mm | 12.105 |
| evidence_class | PROVISIONAL_ASSUMPTION |
| inner_reaction_N | 0.000 |
| pass_ | no |
| qualification | Planning surrogate only: real polygon, cutouts, frame bending, discrete/partial contact require FEA. |
| sigma | 335.972 |
| stress_margin_MPa | -300.972 |
| w | 2.623 |

H13 uses the perimeter-only bypass stress and deflection margins above, together with the load-path and window checks. The bypass fails numerically for the current design. The annular-plate comparison retains continuous inner/outer support and provisional material properties; its inner boundary is not established by the bypass geometry. Open material, shear, buckling and contact qualification gates remain separately reported; a numerical screen never qualifies them. Failure of a polymer specimen in this model does not eliminate all polymer architectures.

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H13-CASEBACK-STRESS | H13 | n/a | -9.540 | -31.315 | -46.629 | **FAIL** | sigma_allow (SUPPLIER_GATED, -15.000); p_test (SUPPLIER_GATED, -14.885); tol_t_cb (MFG_TOL, -5.234) | sigma_allow = 81.629; p_test = 0.268; nu = n/a | OD-G4-ATM-STD; OD-G4-MATERIAL |
| H13-CASEBACK-DEFLECTION | H13 | n/a | -0.068 | -0.168 | -0.300 | **FAIL** | E (SUPPLIER_GATED, -0.072); c_cb_rear (SUPPLIER_GATED, -0.050); p_test (SUPPLIER_GATED, -0.042) | E = 48955.213; c_cb_rear = 0.350; p_test = 0.089 | OD-G4-ATM-STD; OD-G4-MATERIAL |

### G4-B

Window/frame and caseback loads enter a caseback shell and perimeter/case-side bearing path. No P1 pressure load is assigned to PCB lands. Perimeter quadrant compression/bearing bound uses twice equal sharing; battery posts locate the carrier and are not the pressure reaction;  shear, buckling and ceramic contact remain numeric manufacturer/FEA gates. The continuous-inner-support annular plate is a comparison screen only; this bypass has not established that boundary. P2 retains a forbidden REAR-board branch. No support capacity or G3 land enlargement is established.

| Domain | Area mm² | Force N |
| --- | --- | --- |
| WINDOW_APERTURE | 412.003 | 257.502 |
| POD_FRAME | 48.317 | 30.198 |
| CASEBACK_REMAINDER | 1410.058 | 881.286 |

Partition sum: 1870.378602 mm²; total load 1168.986626 N; perimeter reaction 1168.986626 N; PCB pressure load 0.000 N. Partition check: True. Reaction geometry: continuous midcase rear-face bearing annulus; four case-side quadrants bounded at twice equal sharing; lug-root screws retain caseback.

No PCB pressure path is needed for P1. P2 retains its physically authored REAR-board branch and fails closed. Any forbidden branch fails even when another branch reaches MIDCASE. No G3 support-land enlargement has been demonstrated.

| Mode | Evidence / numeric assumptions |
| --- | --- |
| bearing | available_mm2 39.911 / evidence_class PROVISIONAL_ASSUMPTION / required_contact_area_mm2 16.700 |
| buckling | effective_length_factor 2.000 / evidence_class MANUFACTURER_DATA_REQUIRED / required_inertia_Euler_surrogate_mm4 2.139 / section_inertia_mm4 n/a / unbraced_length_upper_mm 7.950 |
| ceramic_contact | contact_allowable_MPa n/a / evidence_class MANUFACTURER_DATA_REQUIRED / force_bound_N 584.493 / minimum_area_at_planning_allowable_mm2 16.700 / provisional_contact_edge_factor 2.000 / required_qualified_contact_allowable_MPa 29.290 |
| compression | area_mm2 39.911 / evidence_class PROVISIONAL_ASSUMPTION / margin_MPa 20.355 / planning_allowable_MPa 35.000 / stress_MPa 14.645 |
| shear | evidence_class MANUFACTURER_DATA_REQUIRED / planning_allowable_MPa 17.500 / provided_area_mm2 n/a / required_area_mm2 33.400 |

| Case-side bypass screen | Value |
| --- | --- |
| boundary | Area-equivalent rigid central frame loading the caseback shell; zero inner support reaction, continuous perimeter bearing. Disjoint disc plus annulus; no G3 posts or PCB support. |
| deflection_margin_mm | -0.233 |
| equivalent_loaded_frame_radius_mm | 12.105 |
| evidence_class | PROVISIONAL_ASSUMPTION |
| inner_reaction_N | 0.000 |
| pass_ | no |
| qualification | Planning surrogate only: real polygon, cutouts, frame bending, discrete/partial contact require FEA. |
| sigma | 622.918 |
| stress_margin_MPa | -472.918 |
| w | 0.283 |

H13 uses the perimeter-only bypass stress and deflection margins above, together with the load-path and window checks. The bypass fails numerically for the current design. The annular-plate comparison retains continuous inner/outer support and provisional material properties; its inner boundary is not established by the bypass geometry. Open material, shear, buckling and contact qualification gates remain separately reported; a numerical screen never qualifies them. Failure of a polymer specimen in this model does not eliminate all polymer architectures.

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H13-CASEBACK-STRESS | H13 | n/a | 93.945 | 37.137 | 10.395 | PASS | sigma_allow (SUPPLIER_GATED, -50.000); p_test (SUPPLIER_GATED, -26.514); tol_t_cb (MFG_TOL, -4.873) | sigma_allow = 139.605; p_test = 0.672; nu = 0.862 | OD-G4-ATM-STD; OD-G4-MATERIAL |
| H13-CASEBACK-DEFLECTION | H13 | n/a | 0.076 | 0.026 | 0.015 | PASS | c_cb_rear (SUPPLIER_GATED, -0.050); p_test (SUPPLIER_GATED, -0.006); E (SUPPLIER_GATED, -0.002) | c_cb_rear = 0.035; p_test = 0.887; E = 133885.498 | OD-G4-ATM-STD; OD-G4-MATERIAL |

### G4-C

Window/frame and caseback loads enter a caseback shell and perimeter/case-side bearing path. No P1 pressure load is assigned to PCB lands. Perimeter quadrant compression/bearing bound uses twice equal sharing; battery posts locate the carrier and are not the pressure reaction;  shear, buckling and ceramic contact remain numeric manufacturer/FEA gates. The continuous-inner-support annular plate is a comparison screen only; this bypass has not established that boundary. P2 retains a forbidden REAR-board branch. No support capacity or G3 land enlargement is established.

| Domain | Area mm² | Force N |
| --- | --- | --- |
| WINDOW_APERTURE | 412.003 | 257.502 |
| POD_FRAME | 48.317 | 30.198 |
| CASEBACK_REMAINDER | 1410.058 | 881.286 |

Partition sum: 1870.378602 mm²; total load 1168.986626 N; perimeter reaction 1168.986626 N; PCB pressure load n/a N. Partition check: True. Reaction geometry: continuous midcase rear-face bearing annulus; four case-side quadrants bounded at twice equal sharing; lug-root screws retain caseback.

No PCB pressure path is needed for P1. P2 retains its physically authored REAR-board branch and fails closed. Any forbidden branch fails even when another branch reaches MIDCASE. No G3 support-land enlargement has been demonstrated.

| Mode | Evidence / numeric assumptions |
| --- | --- |
| bearing | available_mm2 39.911 / evidence_class PROVISIONAL_ASSUMPTION / required_contact_area_mm2 16.700 |
| buckling | effective_length_factor 2.000 / evidence_class MANUFACTURER_DATA_REQUIRED / required_inertia_Euler_surrogate_mm4 2.139 / section_inertia_mm4 n/a / unbraced_length_upper_mm 7.950 |
| ceramic_contact | contact_allowable_MPa n/a / evidence_class MANUFACTURER_DATA_REQUIRED / force_bound_N 584.493 / minimum_area_at_planning_allowable_mm2 16.700 / provisional_contact_edge_factor 2.000 / required_qualified_contact_allowable_MPa 29.290 |
| compression | area_mm2 39.911 / evidence_class PROVISIONAL_ASSUMPTION / margin_MPa 20.355 / planning_allowable_MPa 35.000 / stress_MPa 14.645 |
| shear | evidence_class MANUFACTURER_DATA_REQUIRED / planning_allowable_MPa 17.500 / provided_area_mm2 n/a / required_area_mm2 33.400 |

| Case-side bypass screen | Value |
| --- | --- |
| boundary | Area-equivalent rigid central frame loading the caseback shell; zero inner support reaction, continuous perimeter bearing. Disjoint disc plus annulus; no G3 posts or PCB support. |
| deflection_margin_mm | -2.573 |
| equivalent_loaded_frame_radius_mm | 12.105 |
| evidence_class | PROVISIONAL_ASSUMPTION |
| inner_reaction_N | 0.000 |
| pass_ | no |
| qualification | Planning surrogate only: real polygon, cutouts, frame bending, discrete/partial contact require FEA. |
| sigma | 335.972 |
| stress_margin_MPa | -300.972 |
| w | 2.623 |

H13 uses the perimeter-only bypass stress and deflection margins above, together with the load-path and window checks. The bypass fails numerically for the current design. The annular-plate comparison retains continuous inner/outer support and provisional material properties; its inner boundary is not established by the bypass geometry. Open material, shear, buckling and contact qualification gates remain separately reported; a numerical screen never qualifies them. Failure of a polymer specimen in this model does not eliminate all polymer architectures.

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H13-CASEBACK-STRESS | H13 | n/a | -9.540 | -31.315 | -46.629 | **FAIL** | sigma_allow (SUPPLIER_GATED, -15.000); p_test (SUPPLIER_GATED, -14.885); tol_t_cb (MFG_TOL, -5.234) | sigma_allow = 81.629; p_test = 0.268; nu = n/a | OD-G4-ATM-STD; OD-G4-MATERIAL |
| H13-CASEBACK-DEFLECTION | H13 | n/a | -0.068 | -0.168 | -0.300 | **FAIL** | E (SUPPLIER_GATED, -0.072); c_cb_rear (SUPPLIER_GATED, -0.050); p_test (SUPPLIER_GATED, -0.042) | E = 48955.213; c_cb_rear = 0.350; p_test = 0.089 | OD-G4-ATM-STD; OD-G4-MATERIAL |

## Window minimum-thickness screen

g1_scenarios.plate imported (linear Kirchhoff, circular, simply supported sizing case at p max / E min / nu max / sigma_allow min); W0 span = largest inscribed circle of the S14 pod polygon minus the G1 frame overlap; W1/W2 span = circumscribed circle of the largest physical optical cell (conservative for rectangles)

W0 unsupported radius: 8.358665 mm. Every screen uses nominal thickness minus the imported ±0.05 mm thickness tolerance. Planning allowables are provisional; no supplier-qualified allowable or qualification exists. Positive window deltas apply to both G2 baselines; negative gains are never credited.

| Window / material | Nominal t | Minimum t | Stress MPa | Planning allowable MPa | Deflection mm | Stress pass | Seal land | Z delta | Eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W0-t0p3-sapphire | 0.300 | 0.250 | 864.608 | 150.000 | 0.394 | no | yes | 0.000 | no |
| W0-t0p3-cs_glass | 0.300 | 0.250 | 846.267 | 70.000 | 2.268 | no | yes | 0.000 | no |
| W0-t0p3-pc | 0.300 | 0.250 | 885.568 | 20.000 | 55.509 | no | yes | 0.000 | no |
| W0-t0p5-sapphire | 0.500 | 0.450 | 266.854 | 150.000 | 0.068 | no | yes | 0.000 | no |
| W0-t0p5-cs_glass | 0.500 | 0.450 | 261.194 | 70.000 | 0.389 | no | yes | 0.000 | no |
| W0-t0p5-pc | 0.500 | 0.450 | 273.323 | 20.000 | 9.518 | no | yes | 0.000 | no |
| W0-t0p8-sapphire | 0.800 | 0.750 | 96.068 | 150.000 | 0.015 | yes | yes | 0.300 | no |
| W0-t0p8-cs_glass | 0.800 | 0.750 | 94.030 | 70.000 | 0.084 | no | yes | 0.300 | no |
| W0-t0p8-pc | 0.800 | 0.750 | 98.396 | 20.000 | 2.056 | no | yes | 0.300 | no |
| W1-t0p3-sapphire | 0.300 | 0.250 | 75.797 | 150.000 | 0.003 | yes | yes | 0.000 | yes |
| W1-t0p3-cs_glass | 0.300 | 0.250 | 74.189 | 70.000 | 0.017 | no | yes | 0.000 | no |
| W1-t0p3-pc | 0.300 | 0.250 | 77.634 | 20.000 | 0.427 | no | yes | 0.000 | no |
| W1-t0p5-sapphire | 0.500 | 0.450 | 23.394 | 150.000 | 0.001 | yes | yes | 0.000 | yes |
| W1-t0p5-cs_glass | 0.500 | 0.450 | 22.898 | 70.000 | 0.003 | yes | yes | 0.000 | yes |
| W1-t0p5-pc | 0.500 | 0.450 | 23.961 | 20.000 | 0.073 | no | yes | 0.000 | no |
| W1-t0p8-sapphire | 0.800 | 0.750 | 8.422 | 150.000 | 0.000 | yes | yes | 0.300 | no |
| W1-t0p8-cs_glass | 0.800 | 0.750 | 8.243 | 70.000 | 0.001 | yes | yes | 0.300 | no |
| W1-t0p8-pc | 0.800 | 0.750 | 8.626 | 20.000 | 0.016 | yes | yes | 0.300 | no |
| W2-t0p3-sapphire | 0.300 | 0.250 | 75.797 | 150.000 | 0.003 | yes | no | 0.000 | no |
| W2-t0p3-cs_glass | 0.300 | 0.250 | 74.189 | 70.000 | 0.017 | no | no | 0.000 | no |
| W2-t0p3-pc | 0.300 | 0.250 | 77.634 | 20.000 | 0.427 | no | no | 0.000 | no |
| W2-t0p5-sapphire | 0.500 | 0.450 | 23.394 | 150.000 | 0.001 | yes | no | 0.000 | no |
| W2-t0p5-cs_glass | 0.500 | 0.450 | 22.898 | 70.000 | 0.003 | yes | no | 0.000 | no |
| W2-t0p5-pc | 0.500 | 0.450 | 23.961 | 20.000 | 0.073 | no | no | 0.000 | no |
| W2-t0p8-sapphire | 0.800 | 0.750 | 8.422 | 150.000 | 0.000 | yes | no | 0.300 | no |
| W2-t0p8-cs_glass | 0.800 | 0.750 | 8.243 | 70.000 | 0.001 | yes | no | 0.300 | no |
| W2-t0p8-pc | 0.800 | 0.750 | 8.626 | 20.000 | 0.016 | yes | no | 0.300 | no |

W0: MECHANICALLY ELIMINATED. W0 0.5 mm fails the planning screen; 0.8 mm introduces the reported thickness conflict. W1 0.30 mm chemically strengthened glass fails at its 0.25 mm minimum. W2 retains the G3 seal-land constraint. OD-G4-WINDOW is a decision, not selected here.

## Seal inventory, zero-tolerance feasibility and thresholds

The ±0.05 mm O-ring cross-section tolerance is a PROVISIONAL PLANNING LIMIT, not supplier-qualified evidence. Negative algebraic bounds mean geometry/process redesign. They are never reported as tighter supplier tolerances. Stretch, eccentricity, extrusion, thermal expansion, swelling and compression set remain supplier/process gates.

### G4-A

| Primary seal | Type | Interface |
| --- | --- | --- |
| S-COVER | adhesive ring | MIDCASE / COVER |
| S-CB-MAIN | adhesive ring | MIDCASE / CASEBACK |
| S-SW1 | radial O-ring | MIDCASE / PUSHER_SW1 |
| S-SW2 | radial O-ring | MIDCASE / PUSHER_SW2 |
| S-SW3 | radial O-ring | MIDCASE / PUSHER_SW3 |
| S-SW4 | radial O-ring | MIDCASE / PUSHER_SW4 |
| S-SW5 | radial O-ring | MIDCASE / PUSHER_SW5 |
| S-VENT | membrane | MIDCASE / VENT_MEMBRANE |
| S-POD | adhesive ring | CASEBACK / WINDOW |
| S-CHG | adhesive ring | CASEBACK / CHG_BLOCK |

| Seal | Feasible at ±0 | Maximum symmetric ±delta mm | Classification |
| --- | --- | --- | --- |
| SW1 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW2 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW3 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW4 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW5 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| S-U6F3 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |

| Conditional option | Required geometry / result |
| --- | --- |
| S-U6F3 | available_radius_mm 1.657 / conditional F3 only; F1/F2 retained / gland cs 0.600 / face_annulus 0.000 / g 1.000 / h 0.465 / land 0.400 / process_basis caseback bore + non-ferromagnetic stud groove; main midcase dielectric-sector tolerance does not apply at U6 / spigot_height 1.400 / spigot_radial 0.865 / tol_g 0.010 / tol_h 0.070 / topology radial / id S-U6F3 / land_margin_mm 0.242 / pass_ no / required_radius_mm 1.415 / threshold classification IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE / limit_class PROVISIONAL PLANNING LIMIT / mathematical_bounds_mm fill 0.051 / max_squeeze -0.036 / min_squeeze -0.029 / maximum_symmetric_cs_tolerance_mm n/a / note A negative bound means geometry/process redesign, never a tighter supplier tolerance. / open_effects ['stretch', 'eccentricity', 'extrusion gap', 'thermal expansion', 'swelling', 'compression set'] / planning_tolerance_mm 0.050 / supplier_qualified no / zero_cs_tolerance_feasible no |

S-U6F3 is evaluated only for F3; F1/F2 do not create this penetration. S-POD-FRAME is mandatory for P2. Adhesive caseback seals are adhesive rings, not face O-rings. S-CHG is a continuous bonded feedthrough; there is no compressed charger face seal in the inventory.

### G4-B

| Primary seal | Type | Interface |
| --- | --- | --- |
| S-COVER | adhesive ring | MIDCASE / COVER |
| S-CB-MAIN | radial O-ring | MIDCASE / CASEBACK |
| S-SW1 | radial O-ring | MIDCASE / PUSHER_SW1 |
| S-SW2 | radial O-ring | MIDCASE / PUSHER_SW2 |
| S-SW3 | radial O-ring | MIDCASE / PUSHER_SW3 |
| S-SW4 | radial O-ring | MIDCASE / PUSHER_SW4 |
| S-SW5 | radial O-ring | MIDCASE / PUSHER_SW5 |
| S-VENT | membrane | MIDCASE / VENT_MEMBRANE |
| S-POD | adhesive ring | CASEBACK / WINDOW |
| S-CHG | adhesive ring | CASEBACK / CHG_BLOCK |

| Seal | Feasible at ±0 | Maximum symmetric ±delta mm | Classification |
| --- | --- | --- | --- |
| S-CB-MAIN | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW1 | yes | 0.011 | FINITE_TOLERANCE_BOUND |
| SW2 | yes | 0.011 | FINITE_TOLERANCE_BOUND |
| SW3 | yes | 0.011 | FINITE_TOLERANCE_BOUND |
| SW4 | yes | 0.011 | FINITE_TOLERANCE_BOUND |
| SW5 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| S-U6F3 | yes | 0.006 | FINITE_TOLERANCE_BOUND |

| Conditional option | Required geometry / result |
| --- | --- |
| S-U6F3 | available_radius_mm 1.657 / conditional F3 only; F1/F2 retained / gland cs 0.600 / face_annulus 0.000 / g 0.930 / h 0.465 / land 0.400 / process_basis caseback bore + non-ferromagnetic stud groove; main midcase dielectric-sector tolerance does not apply at U6 / spigot_height 1.330 / spigot_radial 0.865 / tol_g 0.010 / tol_h 0.040 / topology radial / id S-U6F3 / land_margin_mm 0.272 / pass_ no / required_radius_mm 1.385 / threshold classification FINITE_TOLERANCE_BOUND / limit_class PROVISIONAL PLANNING LIMIT / mathematical_bounds_mm fill 0.051 / max_squeeze 0.007 / min_squeeze 0.006 / maximum_symmetric_cs_tolerance_mm 0.006 / note A negative bound means geometry/process redesign, never a tighter supplier tolerance. / open_effects ['stretch', 'eccentricity', 'extrusion gap', 'thermal expansion', 'swelling', 'compression set'] / planning_tolerance_mm 0.050 / supplier_qualified no / zero_cs_tolerance_feasible yes |

S-U6F3 is evaluated only for F3; F1/F2 do not create this penetration. S-POD-FRAME is mandatory for P2. Adhesive caseback seals are adhesive rings, not face O-rings. S-CHG is a continuous bonded feedthrough; there is no compressed charger face seal in the inventory.

### G4-C

| Primary seal | Type | Interface |
| --- | --- | --- |
| S-COVER | adhesive ring | MIDCASE / COVER |
| S-CB-MAIN | adhesive ring | MIDCASE / CASEBACK |
| S-SW1 | radial O-ring | MIDCASE / PUSHER_SW1 |
| S-SW2 | radial O-ring | MIDCASE / PUSHER_SW2 |
| S-SW3 | radial O-ring | MIDCASE / PUSHER_SW3 |
| S-SW4 | radial O-ring | MIDCASE / PUSHER_SW4 |
| S-SW5 | radial O-ring | MIDCASE / PUSHER_SW5 |
| S-VENT | membrane | MIDCASE / VENT_MEMBRANE |
| S-POD-FRAME | radial O-ring | CASEBACK / POD_FRAME |
| S-POD | adhesive ring | POD_FRAME / WINDOW |
| S-CHG | adhesive ring | CASEBACK / CHG_BLOCK |
| S-CB-SPLIT | adhesive ring | CASEBACK / CB_CENTRE |

| Seal | Feasible at ±0 | Maximum symmetric ±delta mm | Classification |
| --- | --- | --- | --- |
| SW1 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW2 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW3 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW4 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| SW5 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| S-U6F3 | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |
| S-POD-FRAME | no | n/a | IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE |

| Conditional option | Required geometry / result |
| --- | --- |
| S-U6F3 | available_radius_mm 1.657 / conditional F3 only; F1/F2 retained / gland cs 0.600 / face_annulus 0.000 / g 1.000 / h 0.465 / land 0.400 / process_basis caseback bore + non-ferromagnetic stud groove; main midcase dielectric-sector tolerance does not apply at U6 / spigot_height 1.400 / spigot_radial 0.865 / tol_g 0.010 / tol_h 0.070 / topology radial / id S-U6F3 / land_margin_mm 0.242 / pass_ no / required_radius_mm 1.415 / threshold classification IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE / limit_class PROVISIONAL PLANNING LIMIT / mathematical_bounds_mm fill 0.051 / max_squeeze -0.036 / min_squeeze -0.029 / maximum_symmetric_cs_tolerance_mm n/a / note A negative bound means geometry/process redesign, never a tighter supplier tolerance. / open_effects ['stretch', 'eccentricity', 'extrusion gap', 'thermal expansion', 'swelling', 'compression set'] / planning_tolerance_mm 0.050 / supplier_qualified no / zero_cs_tolerance_feasible no |
| S-POD-FRAME | conditional mandatory for P2 / gland cs 0.600 / face_annulus 0.000 / g 1.100 / h 0.465 / land 0.400 / spigot_height 1.500 / spigot_radial 0.865 / tol_g 0.030 / tol_h 0.100 / topology radial / id S-POD-FRAME / land_margin_mm -0.954 / pass_ no / threshold classification IMPOSSIBLE_EVEN_AT_ZERO_CS_TOLERANCE / limit_class PROVISIONAL PLANNING LIMIT / mathematical_bounds_mm fill 0.050 / max_squeeze -0.079 / min_squeeze -0.065 / maximum_symmetric_cs_tolerance_mm n/a / note A negative bound means geometry/process redesign, never a tighter supplier tolerance. / open_effects ['stretch', 'eccentricity', 'extrusion gap', 'thermal expansion', 'swelling', 'compression set'] / planning_tolerance_mm 0.050 / supplier_qualified no / zero_cs_tolerance_feasible no |

S-U6F3 is evaluated only for F3; F1/F2 do not create this penetration. S-POD-FRAME is mandatory for P2. Adhesive caseback seals are adhesive rings, not face O-rings. S-CHG is a continuous bonded feedthrough; there is no compressed charger face seal in the inventory.

## Buttons, bosses, carrier, charger and local REAR stack

### G4-A

Diagnostic dimensions: D 50.900 / a_cover 22.300 / bosses SW1 0.900 / SW2 0.900 / SW3 0.900 / SW4 0.900 / SW5 0.900 / chg_r_out 24.000 / h_pod 0.000 / r_lim 24.300 / rcin 23.300 / seal_cs 0.000 / seal_topology adhesive / t_in 1.200 / t_land 0.300 / t_out 1.600 / t_w 0.500 / tcw 0.350 / tw 1.100 / w_land 1.500 / window_variant W1

SW5 nonconductive and SW4 non-ferromagnetic are material constraints only. No compliant pusher or switch is claimed available. Local polymer bore, wall, boss, gland and metal/polymer interface tolerances are applied. The 0.4 mm switch overhang/travel term enters the bore stack; axial gland, core and transverse boss wall are separately screened.

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H03-BOSS-SW1 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW1 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW2 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW2 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW3 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW3 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW4 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW4 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW5 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW5 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H10-CARRIER-WALL | H10 | n/a | 0.050 | 0.000 | 0.000 | PASS | tol_carrier_wall (MFG_TOL, -0.050) | n/a | - |
| H21-BODY-HEIGHT | H21 | n/a | 0.850 | 0.728 | 0.650 | PASS | c_fpc (SUPPLIER_GATED, -0.100); tol_t_land (MFG_TOL, -0.050); tol_z_land (MFG_TOL, -0.050) | c_fpc = 0.950 | - |
| H10-PACK-RADIAL | H10 | n/a | 0.650 | 0.138 | 0.000 | PASS | g_radial_mm (SUPPLIER_GATED, -0.500); tol_pack_dia (SUPPLIER_GATED, -0.100); tol_carrier_r (MFG_TOL, -0.050) | g_radial_mm = 1.000; tol_pack_dia = 0.500 | - |
| H01-REAR-PERIPHERY-Z | H01 | n/a | 0.750 | 0.650 | 0.550 | PASS | tol_lower_web (SUPPLIER_GATED, -0.050); tol_spigot_h (MFG_TOL, -0.050); tol_t_cb (MFG_TOL, -0.050) | tol_lower_web = 0.600; c_rear_route_mm = 1.200 | - |
| H20-CHG-WINDOW | H20 | n/a | 4.899 | 4.496 | 4.449 | PASS | feedthrough_land (SUPPLIER_GATED, -0.400); tol_window_r (MFG_TOL, -0.050) | feedthrough_land = 3.225 | - |
| H21-GLAND-AXIAL-SW1 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW1 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW1 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW2 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW2 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW2 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW3 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW3 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW3 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW4 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW4 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW4 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW5 | H21 | n/a | 0.910 | 0.647 | 0.300 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.550; c_switch_mm = 0.700; c_main_case_mm = 0.500 | - |
| H21-PUSHER-CORE-SW5 | H21 | n/a | -0.250 | -0.403 | -0.530 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.130; bore_dia = 2.660 | - |
| H21-BOSS-WALL-SW5 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H20-RECT-90 | H20 | n/a | -0.265 | -0.705 | -0.846 | **FAIL** | land (SUPPLIER_GATED, -0.424); position_tol (MFG_TOL, -0.106); outer_tol (MFG_TOL, -0.050) | land = 0.601 | - |

| Charger orientation | Radial block | Tangential block | Continuous land each side | Radial margin | Centre containment margin | Tangential available | Pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 4.000 | 5.000 | 1.000 | 0.349 | -2.548 | 4.102 | no |
| 90.000 | 5.000 | 4.000 | 1.000 | -0.651 | -0.846 | 3.773 | no |

H20 requires BOTH the 4 x 5 mm contact block AND its modeled continuous bond/seal land inside the authorized aperture/wedge and radial bounds at adverse tolerance. The land is not allowed to extend outside that envelope; this is a planning modeling assumption, not a supplier-qualified block. The contact block and its entire land must fit simultaneously. The outer boundary already excludes the caseback seal/spigot and clearance. Dock loads enter the caseback/perimeter. Charger pass: False.

Carrier wall minimum is 0.30 mm at adverse process tolerance. The selected diagnostic 0.35 ±0.05 mm meets that minimum with zero wall reserve; 0.30 ±0.05 mm is rejected. Pack radial equality, where present, is a ZERO_RESERVE_SUPPLIER_THRESHOLD permitted by the brief, not a positive-margin requirement.

Local deficit remains a failed hard check where negative. Face/adhesive topology removes spigot height without thinner parts; these are diagnostic alternatives and do not close the complete design. No necessary nonzero total stack growth has been demonstrated.

| Battery item | Status | Known planning evidence | Missing input / evaluation | Closure |
| --- | --- | --- | --- | --- |
| PCM-lobe clearance to SW3 and supports | OPEN | pcm_sweep_az_deg [220, 240] | Supplier PCM lobe dimensions, radial/Z envelope and tolerances; full swept clearance against SW3 and case supports | SR-BATT-PCM plus G4 clearance evaluation |
| Insulation envelope | OPEN | source Frozen stack_parameters t_insulator; already included in back_zone, not added again / t_insulator_mm max 0.100 / min 0.030 / nom 0.050 | Finished insulation coverage, edge wrap, overlaps and their radial/axial tolerance envelope; allocation within finished-pack envelope unconfirmed | SR-BATT-PACK / SR-BATT-PCM and carrier insulation drawing |
| Carrier retention | OPEN |  | Retention feature geometry, engagement/tolerances, required loads and allowable retention capacity; support placement alone does not establish retention | Carrier design/manufacturer retention evidence |
| BATT_EXIT / tail clearance | OPEN | related_checks ['H05-EDGE-XB-J201', 'H05-EDGE-Z-XB-J201'] / reservation area_mm2 3.000 / az_deg [230.0, 236.0] / class KNOWN / clock from 7:40 / to 7:52 / confidence LOW / geometry rect [81.5, 112.2, 84.5, 113.2] / type rect / id BATT_EXIT / kind reservation / label Battery wire exit / strain relief / note Coarse side-channel exit only; NOT a connector-body reservation. / radial_mm [19.93, 22.58] / raw_r_max_mm 22.730 / short_label Bat.exit / source phase1_placement.json reservations[4] / z_levels ['MAIN', 'BATTERY'] | Supplier exit/strain-relief envelope and complete tail route with bend/clearance against SW3, supports and insulation; generic XB crossing is partial evidence only | SR-BATT-PCM / SR-FPC-MECH plus routed-tail clearance evaluation |

Battery items above are explicit open gates; missing numeric clearance or retention inputs are not assigned passing margins.

Reviewed geometry reproduction: n/a

| Local seal topology | CS | Spigot height | Local REAR-edge Z margin |
| --- | --- | --- | --- |
| adhesive | 0.000 | 0.000 | 0.550 |
| face | 0.500 | 0.000 | 0.550 |
| face | 0.600 | 0.000 | 0.550 |
| face | 0.700 | 0.000 | 0.550 |
| face | 0.800 | 0.000 | 0.550 |
| face | 1.000 | 0.000 | 0.550 |
| radial | 0.500 | 1.400 | -0.850 |
| radial | 0.600 | 1.500 | -0.950 |
| radial | 0.700 | 1.620 | -1.070 |
| radial | 0.800 | 1.720 | -1.170 |
| radial | 1.000 | 1.940 | -1.390 |

### G4-B

Diagnostic dimensions: D 50.900 / a_cover 22.300 / bosses SW1 0.900 / SW2 0.900 / SW3 0.900 / SW4 0.900 / SW5 0.900 / chg_r_out 23.340 / h_pod 0.000 / r_lim 23.540 / rcin 23.300 / seal_cs 0.500 / seal_topology radial / t_in 0.900 / t_land 0.300 / t_out 1.000 / t_w 0.500 / tcw 0.350 / tw 1.100 / w_land 1.500 / window_variant W1

SW5 nonconductive and SW4 non-ferromagnetic are material constraints only. No compliant pusher or switch is claimed available. Local polymer bore, wall, boss, gland and metal/polymer interface tolerances are applied. The 0.4 mm switch overhang/travel term enters the bore stack; axial gland, core and transverse boss wall are separately screened.

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H03-BOSS-SW1 | H03 | n/a | 0.100 | 0.080 | 0.080 | PASS | tol_boss (MFG_TOL, -0.020) | n/a | - |
| H21-BORE-SW1 | H21 | n/a | 0.900 | -0.112 | -0.410 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.590; c_switch_mm = -0.010; c_main_case_mm = -0.210 | - |
| H03-BOSS-SW2 | H03 | n/a | 0.100 | 0.080 | 0.080 | PASS | tol_boss (MFG_TOL, -0.020) | n/a | - |
| H21-BORE-SW2 | H21 | n/a | 0.900 | -0.112 | -0.410 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.590; c_switch_mm = -0.010; c_main_case_mm = -0.210 | - |
| H03-BOSS-SW3 | H03 | n/a | 0.100 | 0.080 | 0.080 | PASS | tol_boss (MFG_TOL, -0.020) | n/a | - |
| H21-BORE-SW3 | H21 | n/a | 0.900 | -0.112 | -0.410 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.590; c_switch_mm = -0.010; c_main_case_mm = -0.210 | - |
| H03-BOSS-SW4 | H03 | n/a | 0.100 | 0.080 | 0.080 | PASS | tol_boss (MFG_TOL, -0.020) | n/a | - |
| H21-BORE-SW4 | H21 | n/a | 0.900 | -0.112 | -0.410 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.590; c_switch_mm = -0.010; c_main_case_mm = -0.210 | - |
| H03-BOSS-SW5 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW5 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H10-CARRIER-WALL | H10 | n/a | 0.050 | 0.000 | 0.000 | PASS | tol_carrier_wall (MFG_TOL, -0.050) | n/a | - |
| H21-BODY-HEIGHT | H21 | n/a | 0.850 | 0.728 | 0.650 | PASS | c_fpc (SUPPLIER_GATED, -0.100); tol_t_land (MFG_TOL, -0.050); tol_z_land (MFG_TOL, -0.050) | c_fpc = 0.950 | - |
| H10-PACK-RADIAL | H10 | n/a | 0.650 | 0.138 | 0.000 | PASS | g_radial_mm (SUPPLIER_GATED, -0.500); tol_pack_dia (SUPPLIER_GATED, -0.100); tol_carrier_r (MFG_TOL, -0.050) | g_radial_mm = 1.000; tol_pack_dia = 0.500 | - |
| H01-REAR-PERIPHERY-Z | H01 | n/a | 0.050 | -0.026 | -0.090 | **FAIL** | tol_lower_web (SUPPLIER_GATED, -0.050); c_rear_route_mm (SUPPLIER_GATED, -0.050); tol_t_cb (MFG_TOL, -0.020) | tol_lower_web = -0.040; c_rear_route_mm = 0.560 | - |
| H20-CHG-WINDOW | H20 | n/a | 4.239 | 3.839 | 3.819 | PASS | feedthrough_land (SUPPLIER_GATED, -0.400); tol_window_r (MFG_TOL, -0.020) | feedthrough_land = 2.910 | - |
| H21-GLAND-AXIAL-SW1 | H21 | n/a | 1.030 | 0.777 | 0.510 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.655; c_switch_mm = 0.910; c_main_case_mm = 0.710 | - |
| H21-PUSHER-CORE-SW1 | H21 | n/a | -0.250 | -0.393 | -0.480 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020) | core_radius_min = -0.080; bore_dia = 2.560 | - |
| H21-BOSS-WALL-SW1 | H21 | n/a | 0.140 | 0.036 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020); boss_width_tol (MFG_TOL, -0.020) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW2 | H21 | n/a | 1.030 | 0.777 | 0.510 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.655; c_switch_mm = 0.910; c_main_case_mm = 0.710 | - |
| H21-PUSHER-CORE-SW2 | H21 | n/a | -0.250 | -0.393 | -0.480 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020) | core_radius_min = -0.080; bore_dia = 2.560 | - |
| H21-BOSS-WALL-SW2 | H21 | n/a | 0.140 | 0.036 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020); boss_width_tol (MFG_TOL, -0.020) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW3 | H21 | n/a | 1.030 | 0.777 | 0.510 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.655; c_switch_mm = 0.910; c_main_case_mm = 0.710 | - |
| H21-PUSHER-CORE-SW3 | H21 | n/a | -0.250 | -0.393 | -0.480 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020) | core_radius_min = -0.080; bore_dia = 2.560 | - |
| H21-BOSS-WALL-SW3 | H21 | n/a | 0.140 | 0.036 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020); boss_width_tol (MFG_TOL, -0.020) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW4 | H21 | n/a | 1.030 | 0.777 | 0.510 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.655; c_switch_mm = 0.910; c_main_case_mm = 0.710 | - |
| H21-PUSHER-CORE-SW4 | H21 | n/a | -0.250 | -0.393 | -0.480 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020) | core_radius_min = -0.080; bore_dia = 2.560 | - |
| H21-BOSS-WALL-SW4 | H21 | n/a | 0.140 | 0.036 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.020); boss_width_tol (MFG_TOL, -0.020) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW5 | H21 | n/a | 0.910 | 0.647 | 0.300 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.550; c_switch_mm = 0.700; c_main_case_mm = 0.500 | - |
| H21-PUSHER-CORE-SW5 | H21 | n/a | -0.250 | -0.403 | -0.530 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.130; bore_dia = 2.660 | - |
| H21-BOSS-WALL-SW5 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H20-RECT-90 | H20 | n/a | -0.929 | -1.357 | -1.417 | **FAIL** | land (SUPPLIER_GATED, -0.425); position_tol (MFG_TOL, -0.042); outer_tol (MFG_TOL, -0.020) | land = 0.330 | - |

| Charger orientation | Radial block | Tangential block | Continuous land each side | Radial margin | Centre containment margin | Tangential available | Pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 4.000 | 5.000 | 1.000 | -0.221 | -2.950 | 3.960 | no |
| 90.000 | 5.000 | 4.000 | 1.000 | -1.221 | -1.417 | 3.632 | no |

H20 requires BOTH the 4 x 5 mm contact block AND its modeled continuous bond/seal land inside the authorized aperture/wedge and radial bounds at adverse tolerance. The land is not allowed to extend outside that envelope; this is a planning modeling assumption, not a supplier-qualified block. The contact block and its entire land must fit simultaneously. The outer boundary already excludes the caseback seal/spigot and clearance. Dock loads enter the caseback/perimeter. Charger pass: False.

Carrier wall minimum is 0.30 mm at adverse process tolerance. The selected diagnostic 0.35 ±0.05 mm meets that minimum with zero wall reserve; 0.30 ±0.05 mm is rejected. Pack radial equality, where present, is a ZERO_RESERVE_SUPPLIER_THRESHOLD permitted by the brief, not a positive-margin requirement.

Local deficit remains a failed hard check where negative. Face/adhesive topology removes spigot height without thinner parts; these are diagnostic alternatives and do not close the complete design. No necessary nonzero total stack growth has been demonstrated.

| Battery item | Status | Known planning evidence | Missing input / evaluation | Closure |
| --- | --- | --- | --- | --- |
| PCM-lobe clearance to SW3 and supports | OPEN | pcm_sweep_az_deg [220, 240] | Supplier PCM lobe dimensions, radial/Z envelope and tolerances; full swept clearance against SW3 and case supports | SR-BATT-PCM plus G4 clearance evaluation |
| Insulation envelope | OPEN | source Frozen stack_parameters t_insulator; already included in back_zone, not added again / t_insulator_mm max 0.100 / min 0.030 / nom 0.050 | Finished insulation coverage, edge wrap, overlaps and their radial/axial tolerance envelope; allocation within finished-pack envelope unconfirmed | SR-BATT-PACK / SR-BATT-PCM and carrier insulation drawing |
| Carrier retention | OPEN |  | Retention feature geometry, engagement/tolerances, required loads and allowable retention capacity; support placement alone does not establish retention | Carrier design/manufacturer retention evidence |
| BATT_EXIT / tail clearance | OPEN | related_checks ['H05-EDGE-XB-J201', 'H05-EDGE-Z-XB-J201'] / reservation area_mm2 3.000 / az_deg [230.0, 236.0] / class KNOWN / clock from 7:40 / to 7:52 / confidence LOW / geometry rect [81.5, 112.2, 84.5, 113.2] / type rect / id BATT_EXIT / kind reservation / label Battery wire exit / strain relief / note Coarse side-channel exit only; NOT a connector-body reservation. / radial_mm [19.93, 22.58] / raw_r_max_mm 22.730 / short_label Bat.exit / source phase1_placement.json reservations[4] / z_levels ['MAIN', 'BATTERY'] | Supplier exit/strain-relief envelope and complete tail route with bend/clearance against SW3, supports and insulation; generic XB crossing is partial evidence only | SR-BATT-PCM / SR-FPC-MECH plus routed-tail clearance evaluation |

Battery items above are explicit open gates; missing numeric clearance or retention inputs are not assigned passing margins.

Reviewed geometry reproduction: corrected_local_interface_margin_mm -0.090 / note Counterfactual reproduction of the reviewed local deficit only; old global-metal interface tolerance is not credited. / old_global_metal_interface_margin_mm -0.010 / old_spigot_height_mm 1.220

| Local seal topology | CS | Spigot height | Local REAR-edge Z margin |
| --- | --- | --- | --- |
| adhesive | 0.000 | 0.000 | 1.210 |
| face | 0.500 | 0.000 | 1.210 |
| face | 0.600 | 0.000 | 1.210 |
| face | 0.700 | 0.000 | 1.210 |
| face | 0.800 | 0.000 | 1.210 |
| face | 1.000 | 0.000 | 1.210 |
| radial | 0.500 | 1.300 | -0.090 |
| radial | 0.600 | 1.410 | -0.200 |
| radial | 0.700 | 1.530 | -0.320 |
| radial | 0.800 | 1.640 | -0.430 |
| radial | 1.000 | 1.870 | -0.660 |

### G4-C

Diagnostic dimensions: D 50.900 / a_cover 22.300 / bosses SW1 0.900 / SW2 0.900 / SW3 0.900 / SW4 0.900 / SW5 0.900 / chg_r_out 24.000 / h_pod 0.000 / r_lim 24.300 / rcin 23.300 / seal_cs 0.000 / seal_topology adhesive / t_in 1.200 / t_land 0.300 / t_out 1.600 / t_w 0.500 / tcw 0.350 / tw 1.100 / w_land 1.500 / window_variant W1

SW5 nonconductive and SW4 non-ferromagnetic are material constraints only. No compliant pusher or switch is claimed available. Local polymer bore, wall, boss, gland and metal/polymer interface tolerances are applied. The 0.4 mm switch overhang/travel term enters the bore stack; axial gland, core and transverse boss wall are separately screened.

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H03-BOSS-SW1 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW1 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW2 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW2 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW3 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW3 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW4 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW4 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H03-BOSS-SW5 | H03 | n/a | 0.100 | 0.050 | 0.050 | PASS | tol_boss (MFG_TOL, -0.050) | n/a | - |
| H21-BORE-SW5 | H21 | n/a | 0.900 | -0.114 | -0.480 | **FAIL** | L_bore_min (SUPPLIER_GATED, -1.000); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | L_bore_min = 2.520; c_switch_mm = -0.080; c_main_case_mm = -0.280 | - |
| H10-CARRIER-WALL | H10 | n/a | 0.050 | 0.000 | 0.000 | PASS | tol_carrier_wall (MFG_TOL, -0.050) | n/a | - |
| H21-BODY-HEIGHT | H21 | n/a | 0.850 | 0.728 | 0.650 | PASS | c_fpc (SUPPLIER_GATED, -0.100); tol_t_land (MFG_TOL, -0.050); tol_z_land (MFG_TOL, -0.050) | c_fpc = 0.950 | - |
| H10-PACK-RADIAL | H10 | n/a | 0.650 | 0.138 | 0.000 | PASS | g_radial_mm (SUPPLIER_GATED, -0.500); tol_pack_dia (SUPPLIER_GATED, -0.100); tol_carrier_r (MFG_TOL, -0.050) | g_radial_mm = 1.000; tol_pack_dia = 0.500 | - |
| H01-REAR-PERIPHERY-Z | H01 | n/a | 0.750 | 0.650 | 0.550 | PASS | tol_lower_web (SUPPLIER_GATED, -0.050); tol_spigot_h (MFG_TOL, -0.050); tol_t_cb (MFG_TOL, -0.050) | tol_lower_web = 0.600; c_rear_route_mm = 1.200 | - |
| H20-CHG-WINDOW | H20 | n/a | 4.899 | 4.496 | 4.449 | PASS | feedthrough_land (SUPPLIER_GATED, -0.400); tol_window_r (MFG_TOL, -0.050) | feedthrough_land = 3.225 | - |
| H21-GLAND-AXIAL-SW1 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW1 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW1 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW2 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW2 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW2 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW3 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW3 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW3 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW4 | H21 | n/a | 0.980 | 0.718 | 0.390 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.595; c_switch_mm = 0.790; c_main_case_mm = 0.590 | - |
| H21-PUSHER-CORE-SW4 | H21 | n/a | -0.250 | -0.400 | -0.510 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.110; bore_dia = 2.620 | - |
| H21-BOSS-WALL-SW4 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H21-GLAND-AXIAL-SW5 | H21 | n/a | 0.910 | 0.647 | 0.300 | PASS | guide_land (SUPPLIER_GATED, -0.200); tol_pcb_outline (MFG_TOL, -0.100); c_switch_mm (SUPPLIER_GATED, -0.100) | guide_land = 0.550; c_switch_mm = 0.700; c_main_case_mm = 0.500 | - |
| H21-PUSHER-CORE-SW5 | H21 | n/a | -0.250 | -0.403 | -0.530 | **FAIL** | core_radius_min (SUPPLIER_GATED, -0.100); bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050) | core_radius_min = -0.130; bore_dia = 2.660 | - |
| H21-BOSS-WALL-SW5 | H21 | n/a | 0.200 | 0.078 | 0.000 | PASS | bore_dia (SUPPLIER_GATED, -0.100); bore_radius_tol (MFG_TOL, -0.050); boss_width_tol (MFG_TOL, -0.050) | bore_dia = 2.000 | - |
| H20-RECT-90 | H20 | n/a | -0.265 | -0.705 | -0.846 | **FAIL** | land (SUPPLIER_GATED, -0.424); position_tol (MFG_TOL, -0.106); outer_tol (MFG_TOL, -0.050) | land = 0.601 | - |

| Charger orientation | Radial block | Tangential block | Continuous land each side | Radial margin | Centre containment margin | Tangential available | Pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 4.000 | 5.000 | 1.000 | 0.349 | -2.548 | 4.102 | no |
| 90.000 | 5.000 | 4.000 | 1.000 | -0.651 | -0.846 | 3.773 | no |

H20 requires BOTH the 4 x 5 mm contact block AND its modeled continuous bond/seal land inside the authorized aperture/wedge and radial bounds at adverse tolerance. The land is not allowed to extend outside that envelope; this is a planning modeling assumption, not a supplier-qualified block. The contact block and its entire land must fit simultaneously. The outer boundary already excludes the caseback seal/spigot and clearance. Dock loads enter the caseback/perimeter. Charger pass: False.

Carrier wall minimum is 0.30 mm at adverse process tolerance. The selected diagnostic 0.35 ±0.05 mm meets that minimum with zero wall reserve; 0.30 ±0.05 mm is rejected. Pack radial equality, where present, is a ZERO_RESERVE_SUPPLIER_THRESHOLD permitted by the brief, not a positive-margin requirement.

Local deficit remains a failed hard check where negative. Face/adhesive topology removes spigot height without thinner parts; these are diagnostic alternatives and do not close the complete design. No necessary nonzero total stack growth has been demonstrated.

| Battery item | Status | Known planning evidence | Missing input / evaluation | Closure |
| --- | --- | --- | --- | --- |
| PCM-lobe clearance to SW3 and supports | OPEN | pcm_sweep_az_deg [220, 240] | Supplier PCM lobe dimensions, radial/Z envelope and tolerances; full swept clearance against SW3 and case supports | SR-BATT-PCM plus G4 clearance evaluation |
| Insulation envelope | OPEN | source Frozen stack_parameters t_insulator; already included in back_zone, not added again / t_insulator_mm max 0.100 / min 0.030 / nom 0.050 | Finished insulation coverage, edge wrap, overlaps and their radial/axial tolerance envelope; allocation within finished-pack envelope unconfirmed | SR-BATT-PACK / SR-BATT-PCM and carrier insulation drawing |
| Carrier retention | OPEN |  | Retention feature geometry, engagement/tolerances, required loads and allowable retention capacity; support placement alone does not establish retention | Carrier design/manufacturer retention evidence |
| BATT_EXIT / tail clearance | OPEN | related_checks ['H05-EDGE-XB-J201', 'H05-EDGE-Z-XB-J201'] / reservation area_mm2 3.000 / az_deg [230.0, 236.0] / class KNOWN / clock from 7:40 / to 7:52 / confidence LOW / geometry rect [81.5, 112.2, 84.5, 113.2] / type rect / id BATT_EXIT / kind reservation / label Battery wire exit / strain relief / note Coarse side-channel exit only; NOT a connector-body reservation. / radial_mm [19.93, 22.58] / raw_r_max_mm 22.730 / short_label Bat.exit / source phase1_placement.json reservations[4] / z_levels ['MAIN', 'BATTERY'] | Supplier exit/strain-relief envelope and complete tail route with bend/clearance against SW3, supports and insulation; generic XB crossing is partial evidence only | SR-BATT-PCM / SR-FPC-MECH plus routed-tail clearance evaluation |

Battery items above are explicit open gates; missing numeric clearance or retention inputs are not assigned passing margins.

Reviewed geometry reproduction: n/a

| Local seal topology | CS | Spigot height | Local REAR-edge Z margin |
| --- | --- | --- | --- |
| adhesive | 0.000 | 0.000 | 0.550 |
| face | 0.500 | 0.000 | 0.550 |
| face | 0.600 | 0.000 | 0.550 |
| face | 0.700 | 0.000 | 0.550 |
| face | 0.800 | 0.000 | 0.550 |
| face | 1.000 | 0.000 | 0.550 |
| radial | 0.500 | 1.400 | -0.850 |
| radial | 0.600 | 1.500 | -0.950 |
| radial | 0.700 | 1.620 | -1.070 |
| radial | 0.800 | 1.720 | -1.170 |
| radial | 1.000 | 1.940 | -1.390 |

## Legacy radial / X25 and frozen total stacks

| Legacy metric | Expected | Reproduced | Match |
| --- | --- | --- | --- |
| conservative_radial_margin_mm | -0.950 | -0.950 | yes |
| edge_margin_at_land_ceiling_mm | conservative -0.950 / nominal 0.680 / optimistic 1.300 | conservative -0.950 / nominal 0.680 / optimistic 1.300 | yes |
| edge_margin_flat_exit_mm | conservative -2.100 / nominal -0.470 / optimistic 0.700 | conservative -2.100 / nominal -0.470 / optimistic 0.700 | yes |
| lower_web_margin_mm | conservative -0.200 / nominal 0.080 / optimistic 0.400 | conservative -0.200 / nominal 0.080 / optimistic 0.400 | yes |
| t_allow_straight_mm | conservative -0.750 / nominal 0.800 / optimistic 1.500 | conservative -0.750 / nominal 0.800 / optimistic 1.500 | yes |
| t_bezel_min_nominal_mm | 0.700 | 0.700 | yes |
| u4_land_headroom_mm | conservative -0.060 / nominal 0.240 / optimistic 0.440 | conservative -0.060 / nominal 0.240 / optimistic 0.440 | yes |
| x25_conservative_cover_fit_mm | -1.100 | -1.100 | yes |
| x25_nominal_bezel_wall_margin_mm | -0.150 | -0.150 | yes |
| x25_nominal_fit_mm | 0.550 | 0.550 | yes |

### G4-A

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H05-STRAIGHT | H05 | conservative -0.950 / nominal 0.680 / optimistic 1.400 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250 | - |
| H05-EDGE-XF-J1501 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | -0.100 | **FAIL** | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.200; t_fpc = 0.100; R_bend_min = 1.848 | - |
| H05-EDGE-XC-J202 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250; R_bend_min = 3.273 | - |
| H05-EDGE-XB-J201 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | -0.100 | **FAIL** | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.200; t_fpc = 0.100; R_bend_min = 1.848 | - |
| H05-EDGE-XL-LRA | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250; R_bend_min = 5.950 | - |
| H06-X25-BEZEL | H06 | bezel_wall_conservative -2.100 / bezel_wall_nominal -0.150 / fit_conservative -1.100 / fit_nominal 0.550 | 1.400 | 0.810 | 0.420 | PASS | w_cover_land (SUPPLIER_GATED, -0.500); t_bezel_min (SUPPLIER_GATED, -0.300); c_cover_recess_mm (SUPPLIER_GATED, -0.050) | w_cover_land = 1.920; t_bezel_min = 1.420; c_cover_recess_mm = 0.520 | - |

### G4-B

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H05-WALL-DIELECTRIC | H05 | n/a | 0.200 | 0.084 | 0.020 | PASS | t_wall_min (SUPPLIER_GATED, -0.100); tol_bore_r (MFG_TOL, -0.050); tol_od_r (MFG_TOL, -0.030) | t_wall_min = 1.020 | - |
| H05-STRAIGHT | H05 | conservative -0.950 / nominal 0.680 / optimistic 1.400 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250 | - |
| H05-EDGE-XF-J1501 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | -0.100 | **FAIL** | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.200; t_fpc = 0.100; R_bend_min = 1.848 | - |
| H05-EDGE-XC-J202 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250; R_bend_min = 3.273 | - |
| H05-EDGE-XB-J201 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | -0.100 | **FAIL** | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.200; t_fpc = 0.100; R_bend_min = 1.848 | - |
| H05-EDGE-XL-LRA | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250; R_bend_min = 5.950 | - |
| H06-X25-BEZEL | H06 | bezel_wall_conservative -2.100 / bezel_wall_nominal -0.150 / fit_conservative -1.100 / fit_nominal 0.550 | 1.400 | 0.810 | 0.420 | PASS | w_cover_land (SUPPLIER_GATED, -0.500); t_bezel_min (SUPPLIER_GATED, -0.300); c_cover_recess_mm (SUPPLIER_GATED, -0.050) | w_cover_land = 1.920; t_bezel_min = 1.420; c_cover_recess_mm = 0.520 | - |

### G4-C

| check | hard | legacy | nominal | RSS | linear worst | pass | governing terms (role, margin change) | supplier value for zero margin | owner-gated (not credited) |
|---|---|---|---|---|---|---|---|---|---|
| H05-STRAIGHT | H05 | conservative -0.950 / nominal 0.680 / optimistic 1.400 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250 | - |
| H05-EDGE-XF-J1501 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | -0.100 | **FAIL** | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.200; t_fpc = 0.100; R_bend_min = 1.848 | - |
| H05-EDGE-XC-J202 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250; R_bend_min = 3.273 | - |
| H05-EDGE-XB-J201 | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | -0.100 | **FAIL** | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.200; t_fpc = 0.100; R_bend_min = 1.848 | - |
| H05-EDGE-XL-LRA | H05 | flat_exit conservative -2.100 / nominal -0.470 / optimistic 0.700 / land_ceiling conservative -0.950 / nominal 0.680 / optimistic 1.300 | 0.380 | 0.225 | 0.050 | PASS | c_fpc (SUPPLIER_GATED, -0.100); t_fpc (SUPPLIER_GATED, -0.080); tol_bore_r (MFG_TOL, -0.050) | c_fpc = 0.350; t_fpc = 0.250; R_bend_min = 5.950 | - |
| H06-X25-BEZEL | H06 | bezel_wall_conservative -2.100 / bezel_wall_nominal -0.150 / fit_conservative -1.100 / fit_nominal 0.550 | 1.400 | 0.810 | 0.420 | PASS | w_cover_land (SUPPLIER_GATED, -0.500); t_bezel_min (SUPPLIER_GATED, -0.300); c_cover_recess_mm (SUPPLIER_GATED, -0.050) | w_cover_land = 1.920; t_bezel_min = 1.420; c_cover_recess_mm = 0.520 | - |

| Baseline | Nominal | RSS | Linear worst | Adopted global G4 delta |
| --- | --- | --- | --- | --- |
| G2-REVA | 16.350 | 16.796 | 18.040 | 0.000 |
| G2-REVA-HI | 16.380 | 16.825 | 18.040 | 0.000 |

H01 also checks the local stack. Reporting adopted global delta 0.000 does not conceal a negative local result.

## LRA finite-grid search and maximum compatible envelope

### G4-A

Coins exact; rectangles use a superset union of circles (bulge <=3.1% of half width); plan false negatives possible, no impossibility proof beyond finite classes/grid.

Exclusions: S14_OUTLINE, S14_POD, S14_TAIL_CONSERVATIVE, S14_TAIL_STRAIN_RELIEF_CONSERVATIVE, S14_THERMODE_KEEPOUT, S14_U6_ISLAND, S14_SUPPORT_30, S14_SUPPORT_270, S14_SUPPORT_150, FPC_UNDER, CHG_ROUTE, CHG_LINK, CHG_CONTACT, GNSS_RAD, WIFI_RAD, MAG_CLEAR, G2-J202-WEST-F.Cu-2, G2-U7-B.Cu-2, G2-U7-SERVICE-POCKET, SCREW_NW, SCREW_NE, SCREW_SW, SCREW_SE, SUP_SW_CASE_SIDE, SUP_SE_CASE_SIDE, SUP_NE_CASE_SIDE, SUP_WNW_CASE_SIDE, CHG_CONTACT_BLOCK, CHG_4X5_WITH_LAND, G2-J202-WEST-F.Cu-2, CHG_LINK, SW1_BORE, SW2_BORE, SW3_BORE, SW4_BORE, SW5_BORE, SW1_BOSS, SW2_BOSS, SW3_BOSS, SW4_BOSS, SW5_BOSS, CASEBACK_SEAL_STRUCTURE, POD_SEAL_FRAME, LRA_LEAD_EXIT_RESERVED

| Class | Grid poses | Plan survivors | Height margin | Maximum height at diagnostic caseback | Feasible poses |
| --- | --- | --- | --- | --- | --- |
| LRA-COIN-D8 | 4104.000 | 0.000 | -2.250 | 0.950 | 0.000 |
| LRA-COIN-D10 | 4104.000 | 0.000 | -2.650 | 0.950 | 0.000 |
| LRA-LIN-RECT | 8208.000 | 45.000 | -2.250 | 0.950 | 0.000 |

Maximum compatible geometric envelope: domain maximum coin over authorized azimuth/radius grid for this candidate geometry; square is a guaranteed inscribed rectangle, not maximum rectangle / existence_claim no / height_mm 0.950 / inscribed_square_side_mm 4.808 / lead_status Existing U7 lead/exit reservations excluded; a connecting lead route has not been qualified / maximum_coin_diameter_mm 6.800 / pose az 285.000 / r 20.500 / u703_distance_mm 30.267

This is not an existing actuator class or supplier availability claim. Lead routing remains unqualified. No current class survives; no architecture-wide impossibility is proved. The actuator stays at REAR level. Moving it to another Z allocation would require G2 scope reopening.

### G4-B

Coins exact; rectangles use a superset union of circles (bulge <=3.1% of half width); plan false negatives possible, no impossibility proof beyond finite classes/grid.

Exclusions: S14_OUTLINE, S14_POD, S14_TAIL_CONSERVATIVE, S14_TAIL_STRAIN_RELIEF_CONSERVATIVE, S14_THERMODE_KEEPOUT, S14_U6_ISLAND, S14_SUPPORT_30, S14_SUPPORT_270, S14_SUPPORT_150, FPC_UNDER, CHG_ROUTE, CHG_LINK, CHG_CONTACT, GNSS_RAD, WIFI_RAD, MAG_CLEAR, G2-J202-WEST-F.Cu-2, G2-U7-B.Cu-2, G2-U7-SERVICE-POCKET, SCREW_NW, SCREW_NE, SCREW_SW, SCREW_SE, SUP_SW_CASE_SIDE, SUP_SE_CASE_SIDE, SUP_NE_CASE_SIDE, SUP_WNW_CASE_SIDE, CHG_CONTACT_BLOCK, CHG_4X5_WITH_LAND, G2-J202-WEST-F.Cu-2, CHG_LINK, SW1_BORE, SW2_BORE, SW3_BORE, SW4_BORE, SW5_BORE, SW1_BOSS, SW2_BOSS, SW3_BOSS, SW4_BOSS, SW5_BOSS, CASEBACK_SEAL_STRUCTURE, POD_SEAL_FRAME, LRA_LEAD_EXIT_RESERVED

| Class | Grid poses | Plan survivors | Height margin | Maximum height at diagnostic caseback | Feasible poses |
| --- | --- | --- | --- | --- | --- |
| LRA-COIN-D8 | 4104.000 | 0.000 | -1.620 | 1.580 | 0.000 |
| LRA-COIN-D10 | 4104.000 | 0.000 | -2.020 | 1.580 | 0.000 |
| LRA-LIN-RECT | 8208.000 | 32.000 | -1.620 | 1.580 | 0.000 |

Maximum compatible geometric envelope: domain maximum coin over authorized azimuth/radius grid for this candidate geometry; square is a guaranteed inscribed rectangle, not maximum rectangle / existence_claim no / height_mm 1.580 / inscribed_square_side_mm 4.441 / lead_status Existing U7 lead/exit reservations excluded; a connecting lead route has not been qualified / maximum_coin_diameter_mm 6.280 / pose az 275.000 / r 20.000 / u703_distance_mm 31.055

This is not an existing actuator class or supplier availability claim. Lead routing remains unqualified. No current class survives; no architecture-wide impossibility is proved. The actuator stays at REAR level. Moving it to another Z allocation would require G2 scope reopening.

### G4-C

Coins exact; rectangles use a superset union of circles (bulge <=3.1% of half width); plan false negatives possible, no impossibility proof beyond finite classes/grid.

Exclusions: S14_OUTLINE, S14_POD, S14_TAIL_CONSERVATIVE, S14_TAIL_STRAIN_RELIEF_CONSERVATIVE, S14_THERMODE_KEEPOUT, S14_U6_ISLAND, S14_SUPPORT_30, S14_SUPPORT_270, S14_SUPPORT_150, FPC_UNDER, CHG_ROUTE, CHG_LINK, CHG_CONTACT, GNSS_RAD, WIFI_RAD, MAG_CLEAR, G2-J202-WEST-F.Cu-2, G2-U7-B.Cu-2, G2-U7-SERVICE-POCKET, SCREW_NW, SCREW_NE, SCREW_SW, SCREW_SE, SUP_SW_CASE_SIDE, SUP_SE_CASE_SIDE, SUP_NE_CASE_SIDE, SUP_WNW_CASE_SIDE, CHG_CONTACT_BLOCK, CHG_4X5_WITH_LAND, G2-J202-WEST-F.Cu-2, CHG_LINK, SW1_BORE, SW2_BORE, SW3_BORE, SW4_BORE, SW5_BORE, SW1_BOSS, SW2_BOSS, SW3_BOSS, SW4_BOSS, SW5_BOSS, CASEBACK_SEAL_STRUCTURE, POD_SEAL_FRAME, LRA_LEAD_EXIT_RESERVED

| Class | Grid poses | Plan survivors | Height margin | Maximum height at diagnostic caseback | Feasible poses |
| --- | --- | --- | --- | --- | --- |
| LRA-COIN-D8 | 4104.000 | 0.000 | -2.250 | 0.950 | 0.000 |
| LRA-COIN-D10 | 4104.000 | 0.000 | -2.650 | 0.950 | 0.000 |
| LRA-LIN-RECT | 8208.000 | 45.000 | -2.250 | 0.950 | 0.000 |

Maximum compatible geometric envelope: domain maximum coin over authorized azimuth/radius grid for this candidate geometry; square is a guaranteed inscribed rectangle, not maximum rectangle / existence_claim no / height_mm 0.950 / inscribed_square_side_mm 4.808 / lead_status Existing U7 lead/exit reservations excluded; a connecting lead route has not been qualified / maximum_coin_diameter_mm 6.800 / pose az 285.000 / r 20.500 / u703_distance_mm 30.267

This is not an existing actuator class or supplier availability claim. Lead routing remains unqualified. No current class survives; no architecture-wide impossibility is proved. The actuator stays at REAR level. Moving it to another Z allocation would require G2 scope reopening.

## Assembly, service and RF

CONTRACT INTERPRETATION / CLARIFICATION REQUIRED

A cover bonded before the display cannot coexist with DISP_LAND behind the display: the display must be seated from the front (A7) before the cover is bonded (A8). Front insertion before cover bonding is geometrically possible with frozen allocations but changes the binding sequence; clarification required.

The proposed front-display-before-cover alternative preserves the frozen plan and stack allocation and is geometrically evaluated; it is not substituted for the binding sequence. SERVICE-COVER-REBOND remains open. Full execution also depends on the missing LRA pose and failed insertion/sealing checks.

| Binding step | Blocked by | Missing prerequisite | Access direction | Pass |
| --- | --- | --- | --- | --- |
| C0 | [] | [] | -Z from front | yes |
| A1 | [] | [] | bench | yes |
| A2 | [] | [] | interior (rear opening) | yes |
| A3 | [] | [] | bench | yes |
| A4 | [] | [] | bench | yes |
| A5 | [] | [] | per placement window | yes |
| A6 | [] | [] | +Z from rear (wrist side) toward front | yes |
| A7 | ['COVER'] | [] | -Z from front | no |
| A8 | [] | [] | -Z from front | yes |
| A9 | [] | [] | radial inward from outside | yes |
| A10 | [] | [] | rear (caseback open) | yes |
| A11 | [] | [] | +Z from rear | yes |

| Candidate | Modeled RF intrusions | Complete H17 | H18 |
| --- | --- | --- | --- |
| G4-A | [] | no | yes |
| G4-B | [] | no | yes |
| G4-C | [] | no | yes |

Modeled inventory includes dielectric boundaries, final bosses/pushers, case-side supports, charger and defined lead/exit reservations. Missing compatible LRA and connecting lead geometry keeps full H17 closure open. No RF performance claim.

## Acceptance, gates and validation

| Criterion | Satisfied | Reason |
| --- | --- | --- |
| 1 | yes | Approved decisions recorded; frozen carry-ins and scope checks enforced |
| 10 | no | Modeled feature keepouts checked; unresolved LRA/lead prevents complete H17 closure; no RF claim |
| 11 | no | No complete LRA pose |
| 12 | no | Numeric diagnostic handoff exists; selected geometry and LRA recommendation are absent |
| 13 | no | legacy later-phase scope incompatibility: immutable g3_rear_optical.py check rejects uncommitted G4 files; arch_diagrams.py check inherits this. Actual exits recorded in README; no future commit credited |
| 14 | yes | Contract verdict vocabulary |
| 15 | no | Supplier confirmations and closure owner decisions remain open |
| 2 | yes | Both prospective errata recorded |
| 3 | yes | Equal finite grids; universal H15 rejection certificates plus full H01-H25 retained diagnostics |
| 4 | yes | Legacy and per-check evaluations retained; binary/exact checks expose actual predicate evidence |
| 5 | no | No complete recommended candidate |
| 6 | yes | Selected/minimum/margin explicitly null when no complete candidate exists |
| 7 | yes | Numeric revised radial/X25 plus unchanged legacy and thresholds |
| 8 | no | Global zero delta is insufficient when the local REAR stack fails; no necessary stack growth demonstrated |
| 9 | no | Inventory and screens reported; failed seals and unestablished physical support boundary prevent closure |

Actual validation commands, exit codes, deterministic byte comparison, immutable comparisons and exact worktree status are recorded in the G4 run record in `../README.md`. Criterion 13 remains failed for the literal historical later-phase scope incompatibility; no future commit is credited.

Selftests retain the original 17 faults and add pressure partition, forbidden alternate branch, button travel/local polymer, carrier minimum, rectangular charger containment, impossible-zero-tolerance gland, minimum window thickness, missing H07/H08, missing LRA exclusions, partial acceptance, proud cover, assembly conflict and polygon-contact regressions.

| Gate class | Open items |
| --- | --- |
| battery_carrier | [{'closure': 'SR-BATT-PCM plus G4 clearance evaluation', 'evidence_class': 'PROJECT_DERIVED', 'id': 'BATT-PCM-CLEARANCE', 'known': {'pcm_sweep_az_deg': [220, 240]}, 'margin_mm': None, 'missing': 'Supplier PCM lobe dimensions, radial/Z envelope and tolerances; full swept clearance against SW3 and case supports', 'requirement': 'PCM-lobe clearance to SW3 and supports', 'status': 'OPEN'}, {'closure': 'SR-BATT-PACK / SR-BATT-PCM and carrier insulation drawing', 'evidence_class': 'PROJECT_DERIVED', 'id': 'BATT-INSULATION-ENVELOPE', 'known': {'source': 'Frozen stack_parameters t_insulator; already included in back_zone, not added again', 't_insulator_mm': {'max': 0.1, 'min': 0.03, 'nom': 0.05}}, 'margin_mm': None, 'missing': 'Finished insulation coverage, edge wrap, overlaps and their radial/axial tolerance envelope; allocation within finished-pack envelope unconfirmed', 'requirement': 'Insulation envelope', 'status': 'OPEN'}, {'closure': 'Carrier design/manufacturer retention evidence', 'evidence_class': 'PROJECT_DERIVED', 'id': 'BATT-CARRIER-RETENTION', 'known': {}, 'margin_mm': None, 'missing': 'Retention feature geometry, engagement/tolerances, required loads and allowable retention capacity; support placement alone does not establish retention', 'requirement': 'Carrier retention', 'status': 'OPEN'}, {'closure': 'SR-BATT-PCM / SR-FPC-MECH plus routed-tail clearance evaluation', 'evidence_class': 'PROJECT_DERIVED', 'id': 'BATT-EXIT-TAIL', 'known': {'related_checks': ['H05-EDGE-XB-J201', 'H05-EDGE-Z-XB-J201'], 'reservation': {'area_mm2': 3.0, 'az_deg': [230.0, 236.0], 'class': 'KNOWN', 'clock': {'from': '7:40', 'to': '7:52'}, 'confidence': 'LOW', 'geometry': {'rect': [81.5, 112.2, 84.5, 113.2], 'type': 'rect'}, 'id': 'BATT_EXIT', 'kind': 'reservation', 'label': 'Battery wire exit / strain relief', 'note': 'Coarse side-channel exit only; NOT a connector-body reservation.', 'radial_mm': [19.93, 22.58], 'raw_r_max_mm': 22.73, 'short_label': 'Bat.exit', 'source': 'phase1_placement.json reservations[4]', 'z_levels': ['MAIN', 'BATTERY']}}, 'margin_mm': None, 'missing': 'Supplier exit/strain-relief envelope and complete tail route with bend/clearance against SW3, supports and insulation; generic XB crossing is partial evidence only', 'requirement': 'BATT_EXIT / tail clearance', 'status': 'OPEN'}] |
| closure | ['CASE-SIDE-LOAD-PATH (bearing, shear, buckling, ceramic contact / FEA thresholds)', 'SERVICE-COVER-REBOND', 'FEA-1..FEA-4 (Q1)'] |
| g3_carried | ['SR-SFH4053B-DS', 'SR-MAX86141-LAND', 'SR-MAX86141-HEIGHT', 'SR-TS5A12301E-HEIGHT', 'SR-FPC-MECH', 'SR-C1501', 'SR-REAR-PCB', 'SR-WINDOW', 'SR-BARRIER', 'SR-ADHESIVE', 'SR-PD-CAPACITANCE', 'MG-SPACING', 'MG-WINDOW-XTALK', 'MG-GUARD', 'MG-THERMAL', 'MG-MAG'] |
| g5 | ['AE1401 / AE1410 / AE1420 feed construction', 'radome / dielectric design', 'RF simulation and validation', 'case-material RF validation'] |
| manufacturer | ['SR-SFH4053B-DS', 'SR-MAX86141-LAND', 'SR-MAX86141-HEIGHT', 'SR-TS5A12301E-HEIGHT', 'SR-PD-CAPACITANCE'] |
| measurement | ['MG-SPACING', 'MG-WINDOW-XTALK', 'MG-GUARD', 'MG-THERMAL', 'MG-MAG', 'ATM-Q1', 'ATM-Q2', 'ATM-Q3', 'ATM-Q4', 'ATM-Q5', 'ATM-Q6', 'h_pod wrist / strap trials'] |
| owner | ['OD-G4-ATM-STD', 'OD-G4-MATERIAL', 'OD-G4-STRAP', 'OD-G4-LRA-MAG'] |
| supplier | ['SR-COVER-LENS', 'SR-DISPLAY-LAND', 'SR-DISPLAY-FPC', 'SR-BATT-PACK', 'SR-BATT-GROWTH', 'SR-BATT-PCM', 'SR-BUTTONS', 'SR-CHG-MECH', 'SR-LRA', 'SR-WINDOW', 'SR-ADHESIVE', 'SR-FPC-MECH', 'gasket / O-ring supplier data (cross-section tolerance, compression set; no supplier request exists or is issued by G4)', 'SR-TAGCONNECT', 'SR-J1-ALIGN'] |

Numeric supplier zero-margin values (diagnostic, never silently adopted):

| Term | Check / threshold |
| --- | --- |
| E | [{'check': 'H13-CASEBACK-DEFLECTION', 'value': 133885.498303261}] |
| L_bore_min | [{'check': 'H21-BORE-SW1', 'value': 2.59}, {'check': 'H21-BORE-SW2', 'value': 2.59}, {'check': 'H21-BORE-SW3', 'value': 2.59}, {'check': 'H21-BORE-SW4', 'value': 2.59}, {'check': 'H21-BORE-SW5', 'value': 2.52}] |
| R_bend_min | [{'check': 'H05-EDGE-XF-J1501', 'value': 1.848331477}, {'check': 'H05-EDGE-XC-J202', 'value': 3.272875656}, {'check': 'H05-EDGE-XB-J201', 'value': 1.848331477}, {'check': 'H05-EDGE-XL-LRA', 'value': 5.95}, {'check': 'INFO-EDGE-FLAT', 'value': 0.7}, {'check': 'INFO-EDGE-CEILING', 'value': 4.387498137}] |
| bond_land | [{'check': 'H16-VENT-LAND', 'value': 0.8}] |
| bore_dia | [{'check': 'H21-PUSHER-CORE-SW1', 'value': 2.56}, {'check': 'H21-BOSS-WALL-SW1', 'value': 2.0}, {'check': 'H21-PUSHER-CORE-SW2', 'value': 2.56}, {'check': 'H21-BOSS-WALL-SW2', 'value': 2.0}, {'check': 'H21-PUSHER-CORE-SW3', 'value': 2.56}, {'check': 'H21-BOSS-WALL-SW3', 'value': 2.0}, {'check': 'H21-PUSHER-CORE-SW4', 'value': 2.56}, {'check': 'H21-BOSS-WALL-SW4', 'value': 2.0}, {'check': 'H21-PUSHER-CORE-SW5', 'value': 2.66}, {'check': 'H21-BOSS-WALL-SW5', 'value': 2.0}] |
| c_cb_rear | [{'check': 'H13-CASEBACK-DEFLECTION', 'value': 0.035233026}] |
| c_cb_rear_mm | [{'check': 'H11-POD-RESIDUAL', 'value': 0.36}] |
| c_cover_recess_mm | [{'check': 'H06-X25-BEZEL', 'value': 0.52}] |
| c_display_ledge_mm | [{'check': 'H06-DISPLAY-LEDGE', 'value': 0.3}] |
| c_fpc | [{'check': 'H05-STRAIGHT', 'value': 0.35}, {'check': 'H05-EDGE-XF-J1501', 'value': 0.2}, {'check': 'H05-EDGE-Z-XF-J1501', 'value': 1.155}, {'check': 'H05-EDGE-XC-J202', 'value': 0.35}, {'check': 'H05-EDGE-Z-XC-J202', 'value': 0.68}, {'check': 'H05-EDGE-XB-J201', 'value': 0.2}, {'check': 'H05-EDGE-Z-XB-J201', 'value': 1.155}, {'check': 'H05-EDGE-XL-LRA', 'value': 0.35}, {'check': 'H05-EDGE-Z-XL-LRA', 'value': -0.27}, {'check': 'H05-T-ALLOW-XC', 'value': 0.35}, {'check': 'INFO-EDGE-FLAT', 'value': -1.0}, {'check': 'INFO-EDGE-CEILING', 'value': 0.35}, {'check': 'H21-BODY-HEIGHT', 'value': 0.95}] |
| c_insert_mm | [{'check': 'H23-INSERT-MAIN', 'value': 1.2}, {'check': 'H23-INSERT-BATTERY', 'value': 0.35}, {'check': 'H23-INSERT-REAR', 'value': 0.96}] |
| c_lra_top_mm | [{'check': 'H22-LRA-Z-LRA-COIN-D8', 'value': -1.47}, {'check': 'H22-LRA-Z-LRA-COIN-D10', 'value': -1.87}, {'check': 'H22-LRA-Z-LRA-LIN-RECT', 'value': -1.47}] |
| c_main_case_mm | [{'check': 'H21-BORE-SW1', 'value': -0.21}, {'check': 'H21-BORE-SW2', 'value': -0.21}, {'check': 'H21-BORE-SW3', 'value': -0.21}, {'check': 'H21-BORE-SW4', 'value': -0.21}, {'check': 'H21-BORE-SW5', 'value': -0.28}, {'check': 'H05-MAIN-CASE', 'value': 1.2}, {'check': 'H21-GLAND-AXIAL-SW1', 'value': 0.71}, {'check': 'H21-GLAND-AXIAL-SW2', 'value': 0.71}, {'check': 'H21-GLAND-AXIAL-SW3', 'value': 0.71}, {'check': 'H21-GLAND-AXIAL-SW4', 'value': 0.71}, {'check': 'H21-GLAND-AXIAL-SW5', 'value': 0.5}] |
| c_rear_route_mm | [{'check': 'H01-REAR-PERIPHERY-Z', 'value': 0.56}] |
| c_switch_mm | [{'check': 'H21-BORE-SW1', 'value': -0.01}, {'check': 'H21-BORE-SW2', 'value': -0.01}, {'check': 'H21-BORE-SW3', 'value': -0.01}, {'check': 'H21-BORE-SW4', 'value': -0.01}, {'check': 'H21-BORE-SW5', 'value': -0.08}, {'check': 'H21-GLAND-AXIAL-SW1', 'value': 0.91}, {'check': 'H21-GLAND-AXIAL-SW2', 'value': 0.91}, {'check': 'H21-GLAND-AXIAL-SW3', 'value': 0.91}, {'check': 'H21-GLAND-AXIAL-SW4', 'value': 0.91}, {'check': 'H21-GLAND-AXIAL-SW5', 'value': 0.7}] |
| core_radius_min | [{'check': 'H21-PUSHER-CORE-SW1', 'value': -0.08}, {'check': 'H21-PUSHER-CORE-SW2', 'value': -0.08}, {'check': 'H21-PUSHER-CORE-SW3', 'value': -0.08}, {'check': 'H21-PUSHER-CORE-SW4', 'value': -0.08}, {'check': 'H21-PUSHER-CORE-SW5', 'value': -0.13}] |
| feedthrough_land | [{'check': 'H20-CHG-WINDOW', 'value': 2.909682659}] |
| g_radial_mm | [{'check': 'H10-PACK-RADIAL', 'value': 1.0}] |
| guide_land | [{'check': 'H21-GLAND-AXIAL-SW1', 'value': 0.655}, {'check': 'H21-GLAND-AXIAL-SW2', 'value': 0.655}, {'check': 'H21-GLAND-AXIAL-SW3', 'value': 0.655}, {'check': 'H21-GLAND-AXIAL-SW4', 'value': 0.655}, {'check': 'H21-GLAND-AXIAL-SW5', 'value': 0.55}] |
| h_exit | [{'check': 'H05-EDGE-XF-J1501', 'value': 0.480131585}, {'check': 'H05-EDGE-Z-XF-J1501', 'value': 2.01}, {'check': 'H05-EDGE-Z-XC-J202', 'value': 2.01}, {'check': 'H05-EDGE-XB-J201', 'value': 0.480131585}, {'check': 'H05-EDGE-Z-XB-J201', 'value': 2.01}] |
| land | [{'check': 'H20-RECT-90', 'value': 0.330312298}] |
| lra_height | [{'check': 'H22-LRA-Z-LRA-COIN-D8', 'value': 1.58}, {'check': 'H22-LRA-Z-LRA-COIN-D10', 'value': 1.58}, {'check': 'H22-LRA-Z-LRA-LIN-RECT', 'value': 1.58}] |
| lra_mount_mm | [{'check': 'H22-LRA-Z-LRA-COIN-D8', 'value': -1.47}, {'check': 'H22-LRA-Z-LRA-COIN-D10', 'value': -1.87}, {'check': 'H22-LRA-Z-LRA-LIN-RECT', 'value': -1.47}] |
| lug_arm_width | [{'check': 'H14-SCREW-SEAT', 'value': 2.39}] |
| lug_inner_width | [{'check': 'H14-SCREW-SEAT', 'value': 22.22}] |
| nu | [{'check': 'H13-CASEBACK-STRESS', 'value': 0.861947413}, {'check': 'H13-CASEBACK-DEFLECTION', 'value': -1.490076397}] |
| p_test | [{'check': 'H13-CASEBACK-STRESS', 'value': 0.671535816}, {'check': 'H13-CASEBACK-DEFLECTION', 'value': 0.886951922}] |
| port_dia | [{'check': 'H16-VENT-LAND', 'value': 2.0}] |
| seal_land | [{'check': 'H16-WINDOW-LAND', 'value': 0.98}] |
| sigma_allow | [{'check': 'H13-CASEBACK-STRESS', 'value': 139.60536088}] |
| t_bezel_min | [{'check': 'H06-X25-BEZEL', 'value': 1.42}] |
| t_fpc | [{'check': 'H05-STRAIGHT', 'value': 0.25}, {'check': 'H05-EDGE-XF-J1501', 'value': 0.1}, {'check': 'H05-EDGE-Z-XF-J1501', 'value': 1.41}, {'check': 'H05-EDGE-XC-J202', 'value': 0.25}, {'check': 'H05-EDGE-Z-XC-J202', 'value': 0.96}, {'check': 'H05-EDGE-XB-J201', 'value': 0.1}, {'check': 'H05-EDGE-Z-XB-J201', 'value': 1.41}, {'check': 'H05-EDGE-XL-LRA', 'value': 0.25}, {'check': 'H05-EDGE-Z-XL-LRA', 'value': -0.94}, {'check': 'H05-T-ALLOW-XC', 'value': 0.25}, {'check': 'INFO-EDGE-FLAT', 'value': -1.1}, {'check': 'INFO-EDGE-CEILING', 'value': 0.25}, {'check': 'H23-INSERT-BATTERY', 'value': 0.4}] |
| t_min_cb | [{'check': 'H11-CB-MIN-IN', 'value': 0.88}, {'check': 'H11-CB-MIN-OUT', 'value': 0.98}] |
| t_wall_min | [{'check': 'H05-WALL-SIDE', 'value': 1.06}, {'check': 'H05-WALL-DIELECTRIC', 'value': 1.02}] |
| tol_lower_web | [{'check': 'H01-REAR-PERIPHERY-Z', 'value': -0.04}, {'check': 'H22-LRA-Z-LRA-COIN-D8', 'value': -1.57}, {'check': 'H22-LRA-Z-LRA-COIN-D10', 'value': -1.97}, {'check': 'H22-LRA-Z-LRA-LIN-RECT', 'value': -1.57}] |
| tol_pack_dia | [{'check': 'H10-PACK-RADIAL', 'value': 0.5}] |
| tol_t_window | [{'check': 'H11-POD-RESIDUAL', 'value': -0.26}] |
| w_cover_land | [{'check': 'H06-X25-BEZEL', 'value': 1.92}] |

| Q1 gate | Requirement |
| --- | --- |
| ATM-Q1 | select the 5 ATM test standard and margin (owner / qualification plan) |
| ATM-Q2 | button seal pressure / cycling test after SR-BUTTONS selection (window variant under 5 ATM - the G1.3 window plate calculation is analytical only and any clamped-only pass is conditional on verified bond restraint) |
| ATM-Q3 | sealed charger contact feedthrough pressure test (SR-CHG-MECH) |
| ATM-Q4 | vent membrane water-entry pressure >= test pressure and barometer response |
| ATM-Q5 | caseback deflection analysis once the caseback material/thickness exist (G3), then a pressure test with the REAR module fitted |
| ATM-Q6 | swim / dynamic exposure as stated by the selected standard |

| FEA load case | Load | Support | Pass metrics |
| --- | --- | --- | --- |
| FEA-1 | uniform external pressure p_test nom 0.500 MPa on cover, caseback and window | Physical perimeter rear-face bearing and lug-root retention; window/frame loads through caseback shell, no PCB/optics support. Include actual sector interfaces and missing/unequal contact; compare continuous-inner-bearing analytical surrogate separately. | stress <= allowable class min; deflection < clearance to REAR, charger block, display (air gap) and support stops |
| FEA-2 | uniform external pressure p_test max 0.625 MPa (OD-G4-ATM-STD margin) | as FEA-1, bond modelled as hinged (simply supported) and as bonded (clamped) separately | as FEA-1 at the simply-supported bound |
| FEA-3 | Candidate seal preload (radial/face O-ring or bonded interface), contact tolerances and screw preload; no compressed charger seal is assumed | midcase rear face, screws at lug roots | no yield; gland deformation within the planning window |
| FEA-4 | pusher actuation force (SR-BUTTONS) and boss bending | midcase wall | stress <= allowable; bore deformation keeps the dynamic compression window |

## Conflict evidence and handoff

| Conflict | Status | Evidence |
| --- | --- | --- |
| C1-FRONT-GAP | REMAINS_OPEN | G4 adds no front-gap layer; U8 still governs the front gap (G2/G3 unchanged). |
| C2-DISPLAY-SIDE-CONNECTORS | REMAINS_OPEN | Assembly A6-A8: J1501/J201/J202 mated on the bench (A4), display mated at J1 through the open front (A7) before cover bond (A8) is only a proposed alternative: CONTRACT INTERPRETATION / CLARIFICATION REQUIRED; SERVICE-COVER-REBOND remains. |
| C3-EDGE-WRAP | SUPPLIER_DATA_GATED | H05 at the G2 supplier exit-height range (G4-B): XF -0.100 / XB -0.100 / XC 0.050 mm linear worst; flat-exit bound -1.300 mm reported; SR-FPC-MECH / SR-BATT-PCM / SR-CHG-MECH exit heights and R_bend decide. |
| C4-CHARGER-PATH | REMAINS_OPEN | J202 stays west (OD-J202 open for a placement phase); charger aperture window r 17.501-23.340 mm at az 80-100 with a separate feedthrough seal (S-CHG); corridor clearance via H05-T-ALLOW-XC. |
| C5-SOUTH-CROWDING | OWNER_DECISION_GATED | E-G4-01 supersedes the stale G3 wording; E-G4-02: the historical LRA reservation is invalid and the section 8.9 search finds no LRA pose for any envelope class (REAR Z deficit) - section 13 LRA stop. |
| C6-DISPLAY-FPC-FOLD | SUPPLIER_DATA_GATED | DISP_LAND interrupted at az 269-295 (unsupported display-rim arc 9.961 mm); SR-DISPLAY-FPC fold data required. |
| C7-WIFI-BEYOND-BOARD | DEFERRED_G5 | WIFI_RAD is a zero-intrusion keep-out for new metal and wiring (H17); SW5 pusher must be non-conductive; feed / radome / RF closure belongs to G5 (OD-G4-ENTRY). |
| C8-GNSS-OCCUPIED | DEFERRED_G5 | GNSS_RAD kept across all Z; lug / spring-bar distances reported for OD-G4-STRAP; feed construction is G5. |
| C9-THICK-CORNER | REMAINS_OPEN | G4 Z delta 0.000; G2-REVA 16.350 / 16.796 and G2-REVA-HI 16.380 / 16.825 mm nominal / RSS reproduced unchanged. |
| X10-OPTICS-HEIGHT-UNKNOWN | SUPPLIER_DATA_GATED | Pod frame uses the frozen optics allocation; SR-SFH4053B-DS / SR-MAX86141-HEIGHT unchanged (G3 gates). |
| X11-POD-FOOTPRINT | OWNER_DECISION_GATED | E-G4-01 applies. S14 pod frozen; W0 mechanically eliminated (OD-G4-WINDOW triggered); W1 eligible. |
| X12-J1502-FACE | SUPPLIER_DATA_GATED | E-G4-01 applies. Conservative 7.90 mm tail corridor and thermode keepout reserved untouched (H19). |
| X13-EDGE-CROSSINGS | SUPPLIER_DATA_GATED | See C3: edge crossings evaluated per crossing with governing terms and supplier zero-margin values. |
| X14-SUPPORT-GAP | REMAINS_OPEN | Diagnostic geometry only; handoff unreleased. W/NW support at az 330.50; largest unsupported arc 128.25 deg (legacy 193.80 deg). |
| X15-NE-CROWDING | REMAINS_OPEN | Diagnostic geometry only; handoff unreleased. NE sector allocated deterministically: SUP_NE support post (MAIN stop pad blocked by the U4 courtyard, r 22.23 mm), vent membrane port at az 51.00, SW4 bore at its window centre; ALS stays FRONT level; MAIN located by 3 stop pads (largest pad arc 179.85 deg). |
| X16-MAGNETOMETER | MEASUREMENT_GATED | H18 PASS: no new ferromagnetic part inside MAG_CLEAR; field closure MG-MAG; LRA magnet question OD-G4-LRA-MAG open. |
| X17-GNSS-ALL-HEIGHTS | DEFERRED_G5 | Radiator volumes enforced at every Z level with no new conductor (H17 FAIL (complete LRA/lead closure absent or modeled intrusion)). |
| X18-PACK-EDGE | SUPPLIER_DATA_GATED | Support posts outside R_channel_inner 23.750 mm (linear worst); finished pack SR-BATT-PACK / SR-BATT-GROWTH still gate. |
| X19-BCU-0603 | REMAINS_OPEN | Electrical P-0402 gate; no G4 effect. |
| X20-GROWTH-VS-OPTICS | REMAINS_OPEN | Disjoint pressure partition: 1168.99 N total; case/perimeter path PASS, PCB pressure load 0.00 N. Discrete support/contact boundary unqualified; no G3 support-land enlargement demonstrated. |
| X21-INGRESS-UNDEFINED | REMAINS_OPEN | Seal path closed; H15 False, H16 True. Impossible zero-tolerance glands require geometry/process correction; they are not tighter supplier-tolerance requests. |
| X22-UNMODELLED-Z | REMAINS_OPEN | Local REAR-edge stack margin -0.090 mm; topology alternatives evaluated separately. Global delta 0 does not close a negative local margin. Nonzero total stack growth has not been proved necessary; OD-G4-STACK not triggered. |
| X23-WINDOW-CROSSTALK | OWNER_DECISION_GATED | W0 mechanically eliminated at the 5 ATM screen without Z delta; OD-G4-WINDOW triggered; MG-WINDOW-XTALK open. |
| X24-DISPLAY-LAND | SUPPLIER_DATA_GATED | U4 land headroom 0.400 mm linear worst (legacy 0.240 / -0.060 / 0.440); SR-DISPLAY-LAND / SR-DISPLAY-FPC. |
| X25-COVER-CASE-FIT | REMAINS_OPEN | Diagnostic geometry only; handoff unreleased. X25 under OD-G4-CORNER at D 50.90: bezel-wall margin 0.420 mm linear worst (legacy conservative fit -1.100 unchanged). |
| G2-CROSSING-HEIGHT | SUPPLIER_DATA_GATED | Unchanged G2 shared-corridor gate. |
| G2-BOOK-FOLD | REMAINS_OPEN | No B.Cu connector in the G2 allocation except U7 leads; G4 adds no fold. |
| G2-PROBE-RELIEF | REMAINS_OPEN | G4 adds no seated Z; probe relief unchanged. |
| G2-BACK-STACK | REMAINS_OPEN | Back stack unchanged by G4. |
| G2-DISCOVERED-INTERFACES | SUPPLIER_DATA_GATED | SW1-SW5 bores / bosses / pusher rules defined (SR-BUTTONS); antenna feeds are G5. |

Handoff is diagnostic and unreleased. No selected architecture, LRA pose, qualified load boundary, or complete sealing solution exists. No G3 reopening is demonstrated. G4 authorizes no KiCad edit, G5, K1 or Q1 execution. The package remains uncommitted. Independent re-review returned PASS AS CORRECT BLOCKED STUDY; final state remains G4 OWNER DECISION REQUIRED — BLOCKED / UNRELEASED STUDY.

