# Rev-A multi-board mechanical stack and rear sensor module architecture

**Status: PROVISIONAL, REVERSIBLE architecture study.** Scope contract: `PHASE_BRIEF.md`. This document does not authorise KiCad edits,
routing, outline freeze, case CAD, connector/antenna selection, a battery change or an electrical partition change. Nothing here changes
a frozen invariant (copied verbatim into `architecture.json` and re-checked against `inputs/input_register.json`); every proposal that
would need one is written as an **OWNER DECISION REQUIRED** item (OD-*).

How to read. Numbers carry a class: **KNOWN** (live repository, tracked contract or local primary datasheet), **PARAMETRIC** (planning
assumption with a range; reversible) and **SUPPLIER_DATA_REQUIRED** (cannot be closed by modelling). Quoted tool outputs come from
`generated/zstack.*` and `generated/main_height_map.*` (produced by `tools/mech_model.py`; quoted, never recomputed or edited here).
"Arithmetic" means a shown one-line calculation on those outputs, re-verified by `tools/arch_diagrams.py check`. Optical, thermal and RF
statements are architecture intent only and require prototype measurement.

Generated diagrams (`tools/arch_diagrams.py build`, from `architecture.json` + tool outputs): `generated/perimeter_map.svg`,
`generated/rear_module_concept.svg`, `generated/interconnect_paths.svg`.

Conventions. Front view from the display; north/12 = -Y, east/3 = +X, south/6 = +Y, west/9 = -X; MAIN origin (100,100). Azimuth here = degrees
clockwise from north. Z positive from the front exterior toward the wrist. Reservation Z levels: **FRONT** (display + bond + optional cover),
**MAIN** (front gap + MAIN PCB + back zone), **BATTERY** (pack + carrier web), **REAR** (lower web + REAR board + optics + window).

## Executive summary

| Question | Answer |
|---|---|
| Does the stack meet 14.0-15.5 mm (T_total)? | **Conditionally.** Nominal 14.5 mm (+0.5 to 14.0, +1.0 to 15.5). Tolerance-RSS 14.91 mm for a single-sided REAR (S1). Linear worst case 15.78 mm for the best scenario (S1): **no scenario meets 15.5 mm with linear worst-case tolerances**; the tool thick corner is 17.93 mm. |
| What governs the nominal stack? | battery_zone 5.00, front_gap 2.85 (U8 MAX-F10S), display 2.05, back_zone 1.10 (C901/C903, 0603 on B.Cu), optics 0.85, window 0.50. |
| Controllable levers | single-sided REAR (-0.85 nominal-class / -0.95 thick), glass-exterior cover (-0.5), C901/C903 as 0402 (-0.35), U8 policy (-0.74; protected foundation). |
| Radial / FPC | The tool 180-degree edge wrap fails nominal (-0.47). A 2 x 90-degree out-and-down is bounded by the derived bend geometry: nominal margin -0.47 (flat exit) to +0.68 (exit at the display-land ceiling), positive only with the J1501 mouth at R <= 22.53 and an exit >= 0.10 mm above F.Cu. **No edge crossing passes the conservative corner** (>= 0.95 mm short). The charger riser (XC-J202) and battery tail (XB-J201) share this budget (section G). |
| Largest unknowns | SFH4053B and MAX86141 seated heights (X10), finished-pack drawing, display-FPC fold drawing and permitted display support region (SR-DISPLAY-LAND), FPC connector MPN / height / exit height, charger harness construction, LRA / buttons / antennas. |
| Next gate | G1 owner-decision and supplier-data closure with independent review, then G2 REAR placement and G3 case/outline co-design (section 15). |

---

## A. Z-stack (cover to wrist)

**KNOWN.** Target (owner, 2026-10-10): 14.0-15.5 mm applies to **T_total** = exterior display-glass surface to the deepest normal wrist-facing
surface of the rear optical pod (PHASE_BRIEF 1a; `stack_parameters.json` conventions). T_body = T_total - h_pod; T_total does not depend on h_pod.
Display module 2.05 +/-0.1 (ZC-A1D43W-046 spec pp4-5). MAIN 0.8 mm, 8 Cu layers (live PCB). LPR454440 nominal cell 4.5 mm (catalog).
H_F_under_display 2.7 mm (U8 MAX-F10S, u-blox table), runner-up 1.96 mm (U4 BMP585); H_B_in_battery 0.95 mm (C901, PARAMETRIC typical 0603).

**Layers (quoted from `generated/zstack.md`, mm)**

| Layer | thin | nominal | thick | Class of the governing term |
|---|---:|---:|---:|---|
| front_extra | 0 | 0 | 0.5 | PARAMETRIC LOW (owner decision open) |
| front_bond | 0.1 | 0.15 | 0.25 | PARAMETRIC |
| display | 1.95 | 2.05 | 2.15 | KNOWN |
| front_gap | 2.8 | 2.85 | 3.0 | KNOWN part height (U8) + PARAMETRIC clearance |
| main_pcb | 0.72 | 0.8 | 0.88 | KNOWN nominal, PARAMETRIC tolerance |
| back_zone | 1.03 | 1.1 | 1.25 | PARAMETRIC (no passive MPN) |
| battery_zone | 4.75 | 5.0 | 5.5 | KNOWN nominal cell + SUPPLIER_DATA_REQUIRED tolerance / growth |
| lower_web | 0.3 | 0.4 | 0.6 | PARAMETRIC LOW |
| rear_inner | 0 | 0 | 0.95 | PARAMETRIC (design choice: single- vs double-sided REAR) |
| rear_pcb | 0.6 | 0.8 | 1.0 | PARAMETRIC (staging file 1.6 mm / 2-layer is a placeholder) |
| optics_zone | 0.75 | 0.85 | 1.05 | KNOWN for MAX30208 / SFH7018A / SFH2703; **assumed** for SFH4053B and MAX86141 (X10) |
| window | 0.3 | 0.5 | 0.8 | PARAMETRIC LOW (material undecided) |
| **T_total** | **13.3** | **14.5** | **17.93** | |

Tool margins to 14.0 / 15.5: thin -0.7 / +2.2; nominal +0.5 / +1.0; thick +3.93 / -2.43. T_body nominal for h_pod 0 / 0.5 / 0.8 / 1.0 / 1.5 =
14.5 / 14.0 / 13.7 / 13.5 / 13.0 mm (h_pod is PARAMETRIC LOW and cannot be frozen without wrist/strap trials). Tool RSS (informational):
primary 15.63 mm, secondary 15.269 mm; the primary RSS treats design variables (window, REAR PCB, lower web) as tolerances.

**Governing layers.** battery_zone is 34 % of the nominal stack (5.0 / 14.5), front_gap 20 %, display 14 %, back_zone 8 %. Largest contributors to
thick - nominal (tool): rear_inner 0.95, front_extra 0.5, battery_zone 0.5.

**Scenarios (brief candidate 9).** Design choices are fixed per scenario; tolerance/supplier/clearance terms are then stacked. The tolerance terms
are the nominal-to-max deltas of t_front_bond 0.10, t_display 0.10, c_front 0.15, t_main 0.08, c_back 0.10, t_insulator 0.05, tol_pack_thick 0.20,
g_axial 0.20, c_axial 0.10, h_optics_max 0.10, c_optics 0.10: 1.28 mm linear, 0.414 mm RSS. Arithmetic: scenario = tool nominal 14.5 + design delta +
tolerance stack. Design deltas from the tool layers: added cover +0.5; double-sided REAR +0.85 (h_rear_inner 0.75 + c_rear_inner 0.10, nominal class;
the tool thick corner carries 0.95); window 0.8 +0.3; REAR PCB 1.0 +0.2; lower web 0.6 +0.2 (double-sided adds +0.10 of c_rear_inner tolerance).

| Scenario | Design choices | T nominal tol. | T RSS tol. | T linear worst | <= 15.5 (nominal / RSS / linear) |
|---|---|---:|---:|---:|---|
| S1 | single-sided REAR, glass exterior, nominal web/PCB/window | 14.50 | 14.91 | 15.78 | yes / yes / **no** |
| S2 | S1 but double-sided REAR | 15.35 | 15.78 | 16.73 | yes / no / no |
| S3 | S1 + added cover / bezel lip (0.5) | 15.00 | 15.41 | 16.28 | yes / yes / no |
| S4 | S2 + added cover | 15.85 | 16.28 | 17.23 | no / no / no |
| S5 | S1 with window 0.8, REAR PCB 1.0, web 0.6 | 15.20 | 15.61 | 16.48 | yes / no / no |
| S6 | all design choices maximal | 16.55 | 16.98 | 17.93 | no / no / no |

S6 reproduces the tool thick corner (17.93), which is the arithmetic cross-check that the decomposition is complete.

**What must change.** *To meet 15.5 mm:* at nominal nothing; with RSS tolerances keep the REAR single-sided (S1, or S3 if the owner chooses a lip);
with linear worst-case tolerances remove a further 0.28 mm from S1, for example C901/C903 as 0402 (-0.35: back_zone 0.75 / 0.90 nominal / thick;
S1 linear becomes 15.43 mm) or the U8 policy (-0.74, frozen foundation). *To meet 14.0 mm:* nominal is 0.5 mm above the lower target; the thin
corner is 0.7 mm below it. Nothing has to change to stay at or above 14.0 mm unless the owner intends 14.0 mm as a floor, which is then an owner
clarification (the architecture would add thickness on purpose, not remove it). T_body at nominal h_pod 0.8 is 13.7 mm, i.e. 0.3 mm below the
lower target, which is acceptable only because the target applies to T_total.

**Honest feasibility verdict.** Nominal: feasible with margin. Statistical: feasible only for a single-sided REAR (S1/S3). Worst case: not feasible
without additional levers (0.28 mm for S1). The verdict depends on the unverified assumption that SFH4053B and MAX86141 are not taller than
0.75 mm (X10), on the unselected passives (no MPN), and on pack tolerance/growth numbers that are SUPPLIER_DATA_REQUIRED.
Lever arithmetic was cross-checked once on a throw-away copy of the tool inputs outside the repository (T_total nominal 13.76 / thick 17.19 with
U8 set to zero height; back_zone 0.75 / 0.90 and T_total 14.15 / 17.58 with C901/C903 as 0402); no repository file was changed.

**Not in the tool stack (X22):** window retention adhesive / pod-insert flange, barrier-gasket compression set, caseback gasket compression,
carrier hard-stop ribs, FPC stiffener. Only c_optics (0.05-0.2) can absorb them today.

**Alternatives considered.** Reporting only the thick corner (rejected: hides which terms are decisions); statistical stack only (rejected: no
distribution data). **Risks.** X10, X19-X22. **Unblocks.** The decision between S1/S2/S3 for REAR placement (G2) and case co-design (G3).

## B. MAIN height-risk map

**KNOWN** (`generated/main_height_map.md`). MAIN has 184 footprints (167 F.Cu, 17 B.Cu); all 184 footprint centres lie within R 21.96 (courtyard corners reach R 22.89, C208) so the 43.9 mm display
covers essentially the whole population. F.Cu governing parts: U8 2.7 (R 14.0, az 0), U4 1.96 (R 19.5, az 42), then 1.5 (C402, C705 0805; U11 SOT-23-6;
PARAMETRIC), 1.25 (L203, L401, L601), 1.05 (L101, L201, L202, U102). No unknown-height part lies under the display. **B.Cu:** 17 parts (C206, C901-C906,
R901-R910), all inside the pack projection (R <= 22); tallest C901 / C903 0.95, then 0.6 (C206, C902, C904-C906) and 0.45 (R901-R910).

**Shield-ready clearance.** The provisional U101 can is 0.8-1.0 (nominal 0.85, PARAMETRIC LOW): h_shield_can + c_front = 1.0 mm against a 2.85 mm
front gap, so the shield never governs and has 1.85 mm of headroom; note that a 0.85 mm can over a 0.8 mm BGA is not physically self-consistent
(wall and clearance), which is a shield-design item, not a stack risk. U101 shield polygon 92.95 mm2 (phase1_placement.json).

**Support regions.** Three case-support search windows (SW, SE, NE) centre at az 206.6 / 150.8 / 40.4; the arcs between them are 110.4 / 55.8 /
193.8 degrees, so a 194-degree arc through west and north-west (J1 mating, SW1-SW3, BLE, J202) is unsupported (X14).

**Rim parts under the display support land.** The tallest F.Cu part whose courtyard reaches beyond R_display - w_land is U4 (1.96 mm,
courtyard to R 22.23), then L203 (1.25 mm); the land therefore has 0.24 mm nominal and -0.06 mm conservative headroom over U4 (X24, section G).

**J1301 / TP access.** J1301 (107,114) R 15.65 and TP1301-TP1306 (R 14.8-20.6, NE) are on F.Cu and are covered by the display after seating
(section J, conflict C2).

**Cavity depths.** From the tool rule H_B + c_back: storage pocket needs 0.95 + 0.10 = 1.05 mm nominal (1.15 mm at c_back 0.2) against the Phase-1
planning value >= 1.2; VBAT pocket (C206 0.6) needs 0.70 / 0.80 against >= 0.8. The Phase-1 values are consistent with the thick corner.

**Alternatives.** Stepped pocket (no Z gain: the pack plane is set by the tallest part); re-footprint C901/C903 (X19, -0.35). **Risks.** passive
heights are EIA-typical until MPN freeze. **Unblocks.** carrier pocket design (G3), placement revision decisions.

## C. Battery and carrier

**KNOWN.** LPR454440 selected: nominal Ø44 x 4.5, 870 mAh, 3.7 V, 1C (catalog; not replaceable without owner authorisation). J201 live pinout
1 = GND/BAT-, 2 = BAT_NTC, 3 = VBAT/BAT+ (the stale JBAT1 note must not be used). J201 reservation [94,119,99.5,122]; battery wire exit
[81.5,112.2,84.5,113.2] (SW). B.Cu pocket rectangles: storage [94.3,101.3,105.5,112.3], VBAT [92.6,108.5,94.8,110.1].

**Nominal cell versus finished pack.** The tool carries 4.5 + tol_pack_thick (0-0.3) + g_axial (0.2-0.5) + c_axial (0.05-0.2) = 4.75 / 5.0 / 5.5 mm and
R_pack_max 22.1 / 22.15 / 22.25 (Ø44 + tol_pack_dia 0.2-0.5). All finished-pack data are SUPPLIER_DATA_REQUIRED:

| Missing datum | Request | Used by | Hard gate |
|---|---|---|---|
| finished pack max Ø, thickness, tolerance, edge seal, tape/insulation | SR-BATT-PACK | battery_zone, annulus | before final outline/case |
| PCM envelope and location, tabs, wire/FPC exit, mating connector | SR-BATT-PCM | J201 MPN, carrier pockets, tail path | before J201 MPN / carrier design |
| swelling/growth allowance, restraint/compression limits | SR-BATT-GROWTH | battery_zone, hard stops | before carrier/case freeze |
| NTC presence, curve, placement | SR-BATT-NTC | J201.2 / PMIC config | before J201 MPN |

**Battery tail.** The register's battery wire exit window BATT_EXIT (az 230-237) is 32-55 degrees from J201 (az 181-197), so the tail runs about
22 mm in the annulus beside the pack (BATT_TAIL, edge crossing XB-J201) through the SW support search window and the SW3 button window; SR-BATT-PCM now asks
for a pack exit at the J201 azimuth, which deletes that run (X13).

**Provisional carrier concept (PARAMETRIC LOW).** One insulating moulded carrier carried by MAIN: (1) a web 0.4-0.8 mm with windows/pockets over the 17
B.Cu parts and PI/PET insulator film 0.03-0.1; (2) a perimeter wall 0.3-0.6 that forms the FPC channel and protects the pack edge; (3) a floor ("lower
web", 0.3-0.6) that carries the REAR module and the charger strip and has ribs that act as hard stops; (4) a compliant layer 0.05-0.2 above the pack
for growth; (5) the module extracts rearward as one unit (MAIN + carrier + pack + REAR), the pack is not field-replaceable by design. A metal web is
rejected (conductive next to the GNSS/Wi-Fi radiators and the BMM350). **Alternatives:** pack glued to MAIN (rejected: no rework); open pack with
only tape (rejected: no restraint). **Risks:** X18, X20. **Parametric dependency:** battery_zone, annulus, pocket depths. **Unblocks:** G3 carrier design.

## D. Rigid REAR board

**KNOWN.** 44 refs: emitters D401-D407 (SFH7018A x4, SFH4053B x3), PDs D413 / D414 / D423 / D424 (SFH2703), AFEs U12 / U13 (MAX86141), muxes U402-U407,
U6 MAX30208 + C802, NT401 / NT402, R401-R405 / R408 / R409, C403-C408, C4101-C4104, C4201-C4204. The live file is a 2-layer 1.6 mm placeholder, all parts
on F.Cu, no copper, no approved outline. J1502 and C1501 are footprint-TBD.

**Provisional envelope (derivation, PARAMETRIC LOW).** A_parts = 203.0 mm2 (sum of live library courtyards of the 44 refs; emitters + PDs 92.0). Board
area = A_parts / eta + A_conn + A_lands with eta 0.55 / 0.45 / 0.35, A_conn 15 / 30 / 60 mm2 (J1502 not selected), A_lands 10 / 20 / 40 mm2 (placeholders):
394.1 / 501.1 / 680.0 mm2, disc-equivalent Ø 22.4 / 25.3 / 29.4 mm. Span limit = 2 x s_ED_max (4 / 6 / 8) + 2.4 (SFH7018A width) + 2 x margin (1.5 / 2 / 3) =
13.4 / 18.4 / 24.4 mm, so area governs. Double-sided: the larger face group (inner 103.0 vs optical 100.0 mm2) divided by eta gives Ø 16.4 / 18.8 / 22.4 and the
span limit gives 24.4 at the conservative corner. **Outline class: a compact rounded envelope of about Ø25 mm (22-29), not a full-battery-size board; far
inside the Ø44 pack projection.** The values are sizing, not an outline.

**Orientation and transform (proposed).** FPC attach edge at south (az ~167-180, toward J1501); MAX30208 tongue at az ~255 (away from AFEs, FPC edge and
the east charger block); optical cluster at the centre; AFE/mux band on the south half. Transform REAR frame to assembly frame (front view):
x_a = x_c - (x_r - x_rc), y_a = y_c + (y_r - y_rc): the board is turned like a book page about the north-south axis; its optical face (F.Cu in the
current single-sided file) has normal +Z (toward the wrist). Viewed from the wrist, north is up and east is left. J1502 position 1 must be labelled on
the manufacturer mating-face drawing, never read from a mirrored B-side view (interface contract).

**Component-side strategy.**

| | Single-sided (baseline S1) | Double-sided (S2) |
|---|---|---|
| rear_inner | 0 | +0.85 nominal class (0.95 thick), carries c_rear_inner tolerance |
| Pod footprint | must cover every optical-face part: envelope Ø 22-29 | can shrink to the optical group |
| AFE-to-PD routing | same-side, guarded, short | AFEs under PDs (via-in-pad), shortest PD_IN |
| J1502 | optical face inside the pod, or edge FPC | inner face (costs its mated height + c_rear_inner) |
| Reviewable now | yes | needs J1502 height and pod trial |

Rationale for the baseline: interior depth from the optical face to the skin plane is optics_zone + window = 1.35 mm nominal while the caseback plane is
h_pod (0.8 nominal) above the skin plane, leaving 0.55 mm minus the caseback wall outside the pod; 0.6-0.75 mm parts on the optical face cannot sit there,
so single-sided REAR implies a pod as large as the envelope (X11).

**Support, hard stops, screws, gasket.** REAR rests on three lands of the carrier floor (illustrative az 30 / 150 / 300) outside the optical cluster, is located
by two dowel features and retained by clips or by screws (screws consume land area). Compression and wrist load travel window -> pod frame / hard stops ->
carrier ribs -> case posts, never through optical parts or the pack. Caseback screws and MAIN supports share the SW/SE/NE search windows (their corners reach R 19.7-21.7, inside the Ø44 projection: X18; a usable land starts at R_channel_inner 23.05 / 23.85);
REAR lands are at R < 12.65, so the two systems are mechanically independent except through the carrier. A black barrier gasket sits between the optical
face and the window inner face; its compression is limited by the hard stops (c_optics 0.05-0.2 is the only budget line today). **Relation to battery:**
REAR sits below the pack with the 0.3-0.6 lower web between; PCM / tab lobes of the pack are unknown. **FPC attach region:** south edge, width of the J1502
footprint (24 positions, MPN TBD).

**Alternatives.** Rigid-flex two-island board (optical island + AFE island; rejected for now: more cost, PD_IN would need guarded flex);
full-diameter disc (rejected: no benefit, collides with LRA and charger strip). **Risks.** eta, A_conn and A_lands are placeholders; library courtyards
include margins; barrier area is not separately counted. **Unblocks.** G2 REAR optical / guarded-analog placement study.

## E. Optical pod

**KNOWN functional grouping (frozen membership; live `rear_netlist.xml`).** AFE U12 (PPG1): emitters D401 (green LED1 + red LED2), D403 (green LED4 + red LED5),
D405, D406 (SFH4053B IR850, LED3 / LED6); PDs D424 (PD1), D414 (PD2); muxes U402-U404. AFE U13 (PPG2): D402 (green LED1 + red LED2 + IR940 LED6), D404
(green LED4 + red LED5), D407 (IR850 LED3); PDs D423 (PD1), D413 (PD2); muxes U405-U407. Each 2:1 mux selects between emitter site A (LED1/2/3) and
site B (LED4/5/6) of one colour for one AFE; selects are REAR-local. PD_IN, PD_GND, VREF, LED cathodes and mux selects never cross the FPC. SFH7018A 2.4 x 2.4 x
0.6 and SFH2703 3.2 x 2.0 x 0.6 (+/-0.1) are KNOWN; SFH4053B (1.0 x 0.5 footprint) height and optical data are a **source gap** (SR-SFH4053B-DS):
it blocks only quantitative geometry for D405-D407 and is treated parametrically elsewhere.

**Provisional concept.** One pod, one window plane, cells: every emitter and every PD sits in its own black-walled cell; each AFE's PD pair is placed with
its own emitters; the two AFE groups are mirrored so that AFEs sit on the FPC (south) side. **Window options** (PARAMETRIC LOW, undecided): mineral / chemically
strengthened glass or sapphire 0.3-0.5 mm (scratch resistance, rigid mesa), PC/PMMA 0.5-0.8 mm (moulded mesa, softer). **Barriers.** Black barrier walls run
from the PCB surface (or the barrier gasket) to the **window inner face**; they do not continue through the window, so the window is one continuous
transparent plane above all cells. Wall thickness 0.2-0.5 mm is a study placeholder.

**Window isolation is NOT established (X23, MG-WINDOW-XTALK).** Because the window is continuous, light can travel laterally inside it (and between its two
surfaces) from emitter cells to detector cells without passing through skin. A black ink mask on the window inner face aligned with the walls (baseline
**W0**) can only attenuate part of that path; its effect is not demonstrated, so this package makes no claim of lateral isolation and no claim that skin is
the only emitter-to-detector path. Internal reflection at the window surfaces, adhesive and surface finish are further unquantified contributors.
Matte black cavity walls reduce stray light inside the cells only. Ambient handling is an AFE/firmware feature; the mechanical goal is stray-light
path control, and all of it is architecture intent that requires prototype measurement.

| Variant | Concept | Status |
|---|---|---|
| W0 baseline mask | one window, walls to the inner face, ink mask on the inner face | unverified; residual window path not excluded |
| W1 full-depth opaque isolation | opaque walls continue through the window thickness (segmented or insert-moulded window, opaque ribs) | alternative; costs parts, window area, possibly Z (X22) |
| W2 separate windows | one small window per cell or group in an opaque frame | alternative; more seals (X21) |
| W-ref opaque control | same boards, opaque window blank, no skin | measurement control for the internal (non-skin) floor |

**Measurement gate MG-WINDOW-XTALK (PARAMETRIC; needs prototype boards, not available today).** With identical LED current and AFE settings, record per
emitter-PD pair the PD response with no skin (absorber or open air) and with a skin or phantom load, for W0 against W1 and W2, with W-ref as the control;
reuse the variable-spacing boards below. Decision rule: W0 is retained only if its no-skin floor is below an acceptance threshold that the **owner** derives
from the AFE dynamic range and the required PPG signal quality (no threshold is assumed in this package); otherwise W1 or W2 is adopted and the pod frame,
seals and Z budget (X22) are revised. The gate blocks window material / thickness / retention freeze, G3 pod-insert and caseback-aperture design, and any
statement of optical isolation.

**Emitter-detector spacing study (ranges to be measured, no spacing claimed optimal).** Study range 3-8 mm centre-to-centre (PARAMETRIC LOW placeholder); minimum
geometric pitch 2.2-3.1 mm from KNOWN body sizes plus 0.3-0.5 mm barrier (arithmetic); resulting cluster span 13.4 / 18.4 / 24.4 mm. Build variable-spacing
prototype boards; keep PD_IN short and guarded.

**Pod / mesa and skin contact.** Window flush with the pod frame, pod protruding h_pod 0-1.5 mm beyond the caseback plane (nominal 0.8, to be settled by
wrist/strap trials); pod diameter equals the REAR envelope for single-sided. **Sealing.** Window bonded to a pod frame (PSA or adhesive) and the frame
face-sealed to the caseback aperture (pod insert), or a monolithic caseback window; the ingress target is undefined (OD-WATER, X21). **Hard stops.** Carrier
ribs directly under the window frame carry wrist and gasket load around the optical packages (X20).

**Alternatives.** W1 full-depth opaque isolation and W2 separate small windows (likely better isolation, more parts and seals; to be compared by
MG-WINDOW-XTALK); single window with ink mask W0 (baseline, unverified). **Risks.** X10, X11, X20, X22, X23. **Unblocks.** G2 optical placement (except
D405-D407 numbers); the window concept itself stays open until MG-WINDOW-XTALK.

## F. MAX30208 thermal path

**KNOWN.** U6 MAX30208 2 x 2 x 0.75 thin LGA, 10 pins, polled at 0x50 with no IRQ; pins 7 and 10 grounded; C802 100 nF; schematic note "Thermal island
requires later mechanical review"; ENV_I2C_SCL/SDA reach MAIN on FPC positions 15 / 16 (partition frozen, no change proposed).

**Concept (PARAMETRIC LOW).** A slot-isolated copper peninsula ("tongue") at az ~255 of the REAR envelope carries U6 + C802 with thin bridges to the
board body, away from the LEDs, AFEs, FPC edge and charger. Skin path options: **F1** a thermally conductive, sealed skin-contact feature (metal slug or
filled elastomer) in the pod window region over the tongue; **F2** thin thermal pad under the window only; **F3** no island (baseline risk). Slot width,
bridge width and pad conductivity are study variables, not values.

**Contamination sources.** LED pulses (both-AFE peak 124 mA x ~3.82 V = 0.47 W electrical, duty cycle unknown), AFEs/muxes (REAR-local), the pack and
charging current (0.4 A setting) below the REAR module, MAIN SoC / eMMC / GNSS conduction through carrier and case, the charger block at rear east,
case metal spreading, wrist and strap thermal mass. **Measurement scheduling.** Sample only after LED idle and a settle time, flag or suppress
samples during charging; the settle times are prototype measurements. **Alternatives.** Place U6 on MAIN (rejected: partition frozen); flex tail
(deferred: adds a second fold). **Unblocks.** G2 tongue geometry; G3 skin-contact pad decision.

## G. MAIN to REAR FPC path

**KNOWN contract.** J1501 (MAIN) to J1502 (REAR), 24 abstract positions / 13 nets: 1=GND 2=PPG_SPI_SCLK 3=GND 4=PPG_SPI_MOSI 5=GND 6=PPG_SPI_MISO 7=GND 8=PPG1_CS_N 9=PPG2_CS_N 10=GND 11=PPG1_INT_N 12=PPG2_INT_N 13=PPG_SAMPLE_SYNC 14=GND 15=ENV_I2C_SCL 16=ENV_I2C_SDA 17=GND 18=VOUT1_1V8 19=GND 20=GND 21=PPG_VLED 22=PPG_VLED 23=PPG_VLED 24=GND. Ten GND, three PPG_VLED, SPI x3, CS x2, INT x2,
SAMPLE_SYNC, I2C x2, VOUT1_1V8. MPN, pitch, mated height, orientation and permutation are not frozen. No charger-positive, PD_IN, PD_GND, VREF, LED
cathode or mux-select net is in the FPC. The Ø46 / Ø44 annulus (margin_main_to_case 0.40 / 1.05 / 1.50 mm conservative / nominal / optimistic) is **not a channel**; the radial outputs below are used.

**Radial results (tool, mm).**

| Check | nominal | conservative | optimistic |
|---|---:|---:|---:|
| R_case_inner | 24.05 | 23.40 | 24.50 |
| R_channel_outer_straight | 23.37 | 24.35 | 23.10 |
| margin_straight_run | +0.68 | -0.95 | +1.40 |
| R_edge_wrap_outer (180 deg) | 24.52 | 25.50 | 23.80 |
| margin_edge_wrap | -0.47 | -2.10 | +0.70 |
| margin_main_to_case | +1.05 | +0.40 | +1.50 |

**Edge-crossing geometry (derivation; `architecture.json` edge_crossings, recomputed by `arch_diagrams.py check`).** The earlier out-and-down figure
(+0.58 nominal, bend assumed to start at the display outline R 21.95) is **withdrawn**: a bend that turns *down* (away from the display) is not limited by
the display edge. It is limited by (1) the MAIN edge corner (R_main, F.Cu plane), (2) the height h of the conductor's lower face above F.Cu where it leaves
the connector, and (3) the display support land (DISP_LAND, X24) that sits on top of the front gap behind the display rim. With inner bend radius R_bend
the board corner must stay inside the bend hollow, (R_main - R_start)^2 + (R_bend - h)^2 <= R_bend^2, so the bend may start s(h) = sqrt(R_bend^2 -
(R_bend - h)^2) inboard of the MAIN edge (s = 0 for a flat exit, s = R_bend once h >= R_bend). The vertical run's inner face is R_v = max(R_main + R_bend -
s(h), R_channel_inner) and the margin is R_case_inner - (R_v + t + c). The land caps h at h_max = front_gap - t_land - c - t. Corners: nominal = all
nominal; conservative = tool conservative radial corner with the thin-corner front gap and t_land / w_land at max, t_lower_web at min; optimistic = the mirror
image. Terms: front_gap, R_*, t_fpc, c_fpc, R_bend_min are tool outputs (KNOWN part heights + PARAMETRIC / SUPPLIER ranges); w_land 0.5-1.5 and t_land
0.3-0.8 are PARAMETRIC LOW placeholders (SR-DISPLAY-LAND, case G3); the real exit height and mouth radius are SUPPLIER_DATA_REQUIRED (SR-FPC-MECH,
SR-CHG-MECH, SR-BATT-PCM). Two cross-checks are enforced by `check`: the flat exit reproduces the tool `margin_edge_wrap` at every corner, and the
land-ceiling exit reproduces the tool `margin_straight_run` wherever the channel governs.

| Row | h_max | margin, flat exit (h 0) | margin, exit at land ceiling | bend start at h_max | h_exit for zero margin | h_exit for channel-governed R_v | R_mouth max | t_allow beside pack | lower-web margin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| budget nominal | 2.03 | -0.47 | 0.68 | 21.85 | 0.10 | 0.86 | 22.53 | 0.80 | 0.08 |
| budget conservative | 1.50 | -2.10 | -0.95 | 21.85 | none | 0.36 | 20.90 | -0.75 | -0.20 |
| budget optimistic | 2.50 | 0.70 | 1.30 | 22.40 | 0.00 | 0.60 | 23.70 | 1.50 | 0.40 |

Display support land headroom over the rim parts (F.Cu courtyards reaching beyond R_display - w_land; front_gap - c_front - h_part - t_land, c_front
cancels because front_gap = H_F + c_front):

| Row | R_land_inner | tallest rim part | headroom | next rim part | headroom elsewhere |
|---|---:|---|---:|---|---:|
| land nominal | 20.95 | U4 1.96 | 0.24 | L203 1.25 | 0.95 |
| land conservative | 20.45 | U4 1.96 | -0.06 | L203 1.25 | 0.65 |
| land optimistic | 21.45 | U4 1.96 | 0.44 | L203 1.25 | 1.15 |

**Radial table of every edge crossing** (flat-exit / land-ceiling margin per corner; z window = h_max - c - tallest F.Cu part under the approach between
R_display - w_land and R_main; riser arc = width of the reserved annulus run at R_channel_inner nominal):

| Crossing | nominal | conservative | optimistic | tallest approach part | z window nom / cons / opt | riser arc mm | REAR-level link |
|---|---|---|---|---|---|---:|---|
| XF-J1501 | -0.47 / 0.68 | -2.10 / -0.95 | 0.70 / 1.30 | none | 1.83 / 1.20 / 2.40 | 10.82 | yes |
| XC-J202 | -0.47 / 0.68 | -2.10 / -0.95 | 0.70 / 1.30 | C207 0.95 | 0.88 / 0.25 / 1.45 | 4.02 | yes |
| XB-J201 | -0.47 / 0.68 | -2.10 / -0.95 | 0.70 / 1.30 | none | 1.83 / 1.20 / 2.40 | 22.25 | no |
| XL-LRA | -0.47 / 0.68 | -2.10 / -0.95 | 0.70 / 1.30 | n/a | n/a | n/a | yes |

XF-J1501 = sensor FPC (FPC_CORR), XC-J202 = charger riser (CHG_LINK, CHG_RISER, CHG_APPROACH; section H), XB-J201 = battery tail (BATT_TAIL), XL-LRA = LRA
leads (exists only if the LRA stays at REAR level and DRV2625 U7 stays on F.Cu; azimuth open). All use the flat-flex stand-in, so their radial numbers
coincide; what differs is the azimuth slot, the approach parts and the lower-web link. **Reading.** Nominal: the out-and-down margin lies between -0.47 and
+0.68 mm depending on the J1501 exit height; zero margin needs the mouth (bend start) at R <= 22.53, i.e. not in the outer 0.13 mm of the J1501 window
(raw r max 22.66), and an exit >= 0.10 mm above F.Cu; the full +0.68 needs h >= 0.86 mm (bend start R 21.85). Conservative: every crossing is >= 0.95 mm
short whatever the bend (channel-governed) and the lower web is 0.20 mm too thin for the under-run; only a local case relief or the C3 levers recover it.

**Provisional concept.** J1501 on F.Cu at south with the mouth facing outward at R <= 22.53; the FPC leaves outward above F.Cu under the display support
land and bends 90 degrees down with R_bend 0.6-2.0 (nominal 1.2, SUPPLIER), starting between R 21.85 (exit 0.86 mm) and R 22.53 (exit 0.10 mm), so that
the vertical run (inner face R 23.05-23.73 nominal) sits in the carrier-wall channel beside the pack; a second 90-degree bend leads inward into the lower
web; the under-run (10.4 mm to the REAR envelope edge) ends at J1502 or a hot-bar tail. Nominal length excluding service loop: 10.4 + 7.3 (lower_web +
battery_zone + back_zone + main_pcb) + 4.6 (connector run) + 3.96 (two bend arcs) = 26.3 mm. Stiffener at the connector mouth; adhesive tack and strain
relief at the vertical run; battery-edge protection by the carrier wall (0.3-0.6) and coverlay. Service-loop slack 10-30 mm is a PARAMETRIC placeholder;
**there is no volume for a loop in a 0.3-0.6 mm lower web**, so slack must live beside the vertical run (width direction) or the S1 state must work without
it (section J).

**GND, reference and VLED.** Positions alternate GND between signals (1, 3, 5, 7, ... 24); a single common GND, no isolated rails. VLED: three positions share
the 124 mA both-AFE policy, 41.3 mA each (arithmetic, not a rating) plus recharge of the DNP C1501 reservoir; the "power return group" GND positions 20 and 24
must carry the matching return. Conductor widths are not quoted: contact ratings are SUPPLIER_DATA_REQUIRED (SR-FPC-MECH).

**Alternatives.** 180-degree wrap or flat exit (fails nominal); MAIN edge notch or slot (outline change, G3); J1501 on B.Cu (placement phase, OD-CONN-SIDE);
hot-bar tail (OD-REAR-SIDED). **Risks.** C3, X12, X13, X24. **Unblocks.** connector MPN selection (with the exit-height and mouth-radius requirement), G2/G3.

## H. Charger contact module

**KNOWN.** Four contacts C1..C4 = GND / +5V / +5V / GND at rear east (~3 o'clock), separate assembly; J202 on MAIN F.Cu west [79.5-82.0, 100.35-103.25]
(az 260-269) near PMIC U201 (1 = CHG_RAW_5V, 2 = GND); U1201 and D1201 on MAIN, mandatory ESD_ENTRY at the feedthrough; no charger-positive in the
sensor FPC; no watch-side magnet. 0.4 A charge-current setting.

**Provisional concept.** A module-carried contact block (carried by the carrier / REAR module, face-sealed to a caseback aperture) so the harness stays
connected to J202 when the case is opened (a flying harness would have to be unplugged from a connector that lies under the display). Envelope placeholder
az 80-100, R 17.5-24, REAR level (SR-CHG-MECH). Dock force path: caseback rim and hard stops, never through the pack or REAR optics. Keying by mechanical
recess and retention; no magnet. Cable-side pogo geometry is SUPPLIER_DATA_REQUIRED.

**Route.** R1 (recommended): REAR-level strip along the south chord at R 18.5, az 100-260, arc 51.7 mm, outside the REAR envelope (4.35 mm clearance
to the nominal envelope edge, 2.3 mm to the conservative one) and inside the pack projection. The strip itself does not use the annulus, but **the riser to
J202 does** (edge crossing XC-J202, explicit reservations): CHG_LINK carries the strip outward under the pack edge in the lower web (az 249-259, R 20-23.05;
lower-web margin +0.08 / -0.20 / +0.40 mm nominal / conservative / optimistic), CHG_RISER rises beside the pack in a 10-degree annulus slot (az 249-259,
between the SW3 and SW2 placeholders, 4.02 mm wide at R_channel_inner nominal) and CHG_APPROACH bends over the MAIN edge into the front gap under the
display support land to J202 (az 249-262). Its three-corner radial budget is the section G table: flat-exit / land-ceiling margin -0.47 / +0.68 nominal,
-2.10 / -0.95 conservative, +0.70 / +1.30 optimistic (flat-flex stand-in, harness construction unknown, SR-CHG-MECH); the harness conductor may be at most
0.80 mm thick beside the pack at nominal (none fits conservative); over C207 (0.95 mm) the approach has a 0.88 / 0.25 / 1.45 mm z window, so the harness
must leave J202 at least 1.15 mm above F.Cu (0.95 + c). R1 is therefore preferred over R2 (annulus R 23.6, arc 65.9 mm) because it uses 10 degrees of
annulus instead of 160, not because it avoids the annulus; R3 via north (61.3 mm) is rejected (BMM350, GNSS, BLE). It must
avoid the optical region (REAR_ENV), antennas (Wi-Fi window starts 7.7 degrees away) and the BMM350 (NE): route +5V/GND as a tightly coupled pair
(single-conductor field at 10 mm about 8 uT, physics not measurement). J202 sits at west under the display with the display fold, J1 and SW1-SW3
(conflict C6): a placement-phase move of J202 toward the contact block is OD-J202 and would delete the west riser. **Alternatives.** Fabricated contact flex
as its own project (charger_harness.md). **Risks.** C4, X13, X16, X24. **Unblocks.** contact-module and harness selection (with the riser budget as a requirement).

## I. Structural and perimeter reservations

Reservations are volumes reserved by function; a PCB footprint that merely fits does not entitle use of perimeter that a seal, boss, radiator, button or
vent needs. Table generated from `architecture.json` (az clockwise from north; R from the watch centre; rectangles from the register are clipped at the
case outer radius 25.25 for overlap tests).

| ID | Item | Clock (from-to) | Az deg | R mm | Z levels | Class | Source |
|---|---|---|---|---|---|---|---|
| DISPLAY | Display module (rigid slab) | 12:00-12:00 | 0.0-360.0 | 0.00-21.95 | FRONT | KNOWN | input_register DISPLAY-MOD (ZC-A1D43W-046 spec V1.0 pp4-5; bounding 43.9); stack_parameters rules.front_gap (r<=21.95) |
| PACK | Battery pack, nominal Ø44 projection | 12:00-12:00 | 0.0-360.0 | 0.00-22.00 | BATTERY | KNOWN | input_register BATT-CELL (LPR454440 nominal Ø44 x 4.5); tolerance/PCM lobe SUPPLIER_DATA_REQUIRED |
| GNSS_RAD | GNSS radiator / feed opportunity | 11:33-12:38 | 346.4-18.9 | 20.13-24.37 | FRONT+MAIN+BATTERY+REAR | KNOWN | phase1_placement.json reservations[0]; input_register MAIN-RES (coarse, not final) |
| BLE_RAD | BLE radiator opportunity | 10:08-11:04 | 304.1-331.8 | 15.80-25.15 | MAIN | KNOWN | phase1_placement.json reservations[1] |
| WIFI_RAD | Wi-Fi radiator opportunity | 3:35-4:18 | 107.7-128.8 | 20.59-25.24 | MAIN+REAR | KNOWN | phase1_placement.json reservations[2]; input_register MAIN-RES |
| J1501 | J1501 sensor FPC connector window | 5:07-5:58 | 153.3-179.0 | 16.63-22.49 | MAIN | KNOWN | phase1_placement.json reservations[3] |
| J201 | J201 battery termination window | 6:03-6:34 | 181.6-197.1 | 19.14-22.65 | MAIN | KNOWN | phase1_placement.json reservations[9] |
| J202 | J202 charger entry window (west) | 8:40-8:58 | 260.2-268.9 | 18.13-20.61 | MAIN | KNOWN | phase1_placement.json j202_reservation / reservations[5] |
| BATT_EXIT | Battery wire exit / strain relief | 7:40-7:52 | 230.0-236.0 | 19.93-22.58 | MAIN+BATTERY | KNOWN | phase1_placement.json reservations[4] |
| SUP_SW | Support search SW | 6:41-7:07 | 200.3-213.3 | 21.44-25.24 | MAIN+BATTERY | KNOWN | phase1_placement.json reservations[6] |
| SUP_SE | Support search SE | 4:48-5:14 | 143.9-157.1 | 19.85-25.17 | MAIN+BATTERY | KNOWN | phase1_placement.json reservations[7] |
| SUP_NE | Support search north-east | 1:09-1:32 | 34.4-46.2 | 21.88-25.24 | MAIN+BATTERY | KNOWN | phase1_placement.json reservations[8] |
| DISP_FPC | Display FPC fold / J1 corridor | 8:58-9:50 | 269.0-295.0 | 17.05-22.65 | MAIN | SUPPLIER_DATA_REQUIRED | input_register DISPLAY-FPC (fold up to 0.7 beyond outline; connector location on fold not dimensioned) + J1 courtyard az range (main_height_map.json J1) |
| SWD | J1301 Tag-Connect + probe volume | 4:39-5:34 | 139.4-167.1 | 12.66-18.96 | FRONT+MAIN | SUPPLIER_DATA_REQUIRED | main_height_map.json J1301 courtyard; input_register J1301-SWD (probe body needs vertical volume above F.Cu; no local Tag-Connect drawing) |
| TP | Power test points TP1301-TP1306 (probe access) | 12:36-1:40 | 18.2-49.9 | 13.82-21.52 | FRONT+MAIN | KNOWN | main_height_map.json access list (pad positions); probe margin 1.0 mm radius PARAMETRIC |
| VENT | Barometer vent route (NE) | 1:00-2:00 | 30.0-60.0 | 19.50-25.25 | MAIN | PARAMETRIC | input_register SECTORS (vent NE 1-2 o'clock); BMP585 U4 at az 42, r 19.5 (main_height_map.json) |
| ALS | Ambient-light aperture (front NE) | 1:30-2:30 | 45.0-75.0 | 19.45-21.95 | FRONT | PARAMETRIC | input_register SECTORS (ALS front NE 1:30-2:30); OPT4001 U5 at az 56, r 20.8 (main_height_map.json) |
| SW1 | Button SW1 (10 o'clock) | 9:45-10:15 | 292.5-307.5 | 21.00-25.25 | MAIN | SUPPLIER_DATA_REQUIRED | input_register SECTORS (SW1-3 left 10/9/8, SW4-5 right 2/4) + BUTTONS (mechanism unselected); half-width 7.5 deg is a PARAMETRIC placeholder |
| SW2 | Button SW2 (9 o'clock) | 8:45-9:15 | 262.5-277.5 | 21.00-25.25 | MAIN | SUPPLIER_DATA_REQUIRED | input_register SECTORS (SW1-3 left 10/9/8, SW4-5 right 2/4) + BUTTONS (mechanism unselected); half-width 7.5 deg is a PARAMETRIC placeholder |
| SW3 | Button SW3 (8 o'clock) | 7:45-8:15 | 232.5-247.5 | 21.00-25.25 | MAIN | SUPPLIER_DATA_REQUIRED | input_register SECTORS (SW1-3 left 10/9/8, SW4-5 right 2/4) + BUTTONS (mechanism unselected); half-width 7.5 deg is a PARAMETRIC placeholder |
| SW4 | Button SW4 (2 o'clock) | 1:45-2:15 | 52.5-67.5 | 21.00-25.25 | MAIN | SUPPLIER_DATA_REQUIRED | input_register SECTORS (SW1-3 left 10/9/8, SW4-5 right 2/4) + BUTTONS (mechanism unselected); half-width 7.5 deg is a PARAMETRIC placeholder |
| SW5 | Button SW5 (4 o'clock) | 3:45-4:15 | 112.5-127.5 | 21.00-25.25 | MAIN | SUPPLIER_DATA_REQUIRED | input_register SECTORS (SW1-3 left 10/9/8, SW4-5 right 2/4) + BUTTONS (mechanism unselected); half-width 7.5 deg is a PARAMETRIC placeholder |
| MAG_CLEAR | BMM350 magnetic-clean zone (placeholder) | 12:44-3:23 | 22.1-101.3 | 5.76-25.24 | MAIN+REAR | PARAMETRIC | BMM350 U703 at (113.8,92.6) (main_height_map.json); input_register frozen invariant "no watch-side permanent magnet"; 10 mm radius is a placeholder to be set by measurement |
| REAR_ENV | REAR rigid board + pod envelope (nominal, single-sided) | 12:00-12:00 | 0.0-360.0 | 0.00-12.65 | REAR | PARAMETRIC | architecture.json rear_module.envelope_results (derivation over live REAR courtyards) |
| LRA | LRA pocket (south, REAR level) | 5:30-6:30 | 165.0-195.0 | 12.65-22.00 | REAR | SUPPLIER_DATA_REQUIRED | input_register SECTORS (LRA S 5:30-6:30) + LRA (footprint TBD); REAR-level placement is an architecture proposal |
| FPC_UNDER | Sensor FPC under-run (carrier lower web) | 5:05-5:59 | 152.6-179.5 | 12.65-22.66 | REAR | PARAMETRIC | architecture proposal; azimuth = J1501 reservation range (derived), radial from REAR envelope edge to R 22.66 |
| FPC_CORR | Sensor FPC vertical run (annulus) | 5:05-5:59 | 152.6-179.5 | 22.66-24.05 | MAIN+BATTERY | PARAMETRIC | architecture proposal; stack_parameters radial R_channel / R_case_inner (zstack radial) |
| CHG_CONTACT | Charger contact block (rear east) | 2:40-3:20 | 80.0-100.0 | 17.50-24.00 | REAR | SUPPLIER_DATA_REQUIRED | frozen invariant (charger contacts rear east ~3 o'clock, GND/+5V/+5V/GND); input_register CHG-MECH; width/radial extent are PARAMETRIC placeholders |
| CHG_ROUTE | Charger harness strip (REAR level, south chord) | 3:20-8:40 | 100.0-260.0 | 17.00-20.00 | REAR | PARAMETRIC | architecture proposal (charger_path.routes R1); outside REAR envelope, inside pack projection |
| DISP_LAND | Display support / bond land behind the rim (top of front gap) | 12:00-12:00 | 0.0-360.0 | 20.45-24.05 | MAIN | PARAMETRIC | architecture proposal (brief section 9 L1); edge_crossings.display_land: r from R_display - w_land max to R_case_inner nominal; w_land / t_land PARAMETRIC; permitted support region SUPPLIER_DATA_REQUIRED (SR-DISPLAY-LAND) |
| CHG_LINK | Charger strip link to the riser (REAR level, under the pack edge) | 8:18-8:38 | 249.0-259.0 | 20.00-23.05 | REAR | PARAMETRIC | architecture proposal (brief section 9 L2); edge_crossings XC-J202; azimuth slot between the SW3 (247.5) and SW2 (262.5) placeholder windows; r from the CHG_ROUTE outer edge to R_channel_inner nominal |
| CHG_RISER | Charger harness riser in the annulus (west, beside the pack) | 8:18-8:38 | 249.0-259.0 | 23.05-24.05 | MAIN+BATTERY | PARAMETRIC | architecture proposal (brief section 9 L2); edge_crossings XC-J202; r = R_channel_inner .. R_case_inner nominal (zstack radial); azimuth = CHG_LINK slot |
| CHG_APPROACH | Charger harness approach over the MAIN edge to J202 (front gap, under the land) | 8:18-8:44 | 249.0-262.0 | 19.00-23.05 | MAIN | PARAMETRIC | architecture proposal (brief section 9 L2); edge_crossings XC-J202; from the riser slot to the J202 window; stops before the SW2 placeholder (262.5) |
| BATT_TAIL | Battery tail run in the annulus (BATT_EXIT to the J201 azimuth) | 6:03-7:53 | 181.3-236.6 | 23.05-24.05 | MAIN+BATTERY | PARAMETRIC | architecture proposal; interconnect P3 path; az from the J201 window (exact corner az) to the BATT_EXIT window (exact corner az); r = R_channel_inner .. R_case_inner nominal |

Notes. Screws / bosses coincide with SUP_SW / SUP_SE / SUP_NE (search windows whose inner corners reach R 19.7-21.7, i.e. into the Ø44 projection, X18; usable land from R_channel_inner; no boss geometry approved) and a fourth W/NW support is
recommended (X14). MAIN supports touch the MAIN edge region; battery supports are carrier ribs. Gasket lands live in the 23.0-24.05 band (nominal) and are
undimensioned. Buttons SW1-SW5 use +/-7.5 degree placeholder arcs (pusher + bore + land about 6.3 mm at R 24; not a supplier dimension). The LRA pocket is
placed at the REAR level south (az 165-195, R 12.65-22) because the MAIN level has no free radial room and the front gap is used by the display; its leads then
add a fourth rear-to-front crossing if DRV2625 U7 stays on F.Cu (X13). The barometer vent starts at U4 (R 19.5, az 42) and runs outward; the ALS aperture is
the cover-glass border annulus R 19.45-21.95 (POL 38.9) at az 45-75 and needs the display supplier drawing. GNSS / BLE / Wi-Fi radome volumes are the
register rectangles clipped to the case; Wi-Fi's raw rectangle reaches R 28.6 (C7). J201 / PCM / wire exit, sensor FPC corridor (FPC_UNDER, FPC_CORR),
charger module (CHG_CONTACT, CHG_ROUTE, CHG_LINK, CHG_RISER, CHG_APPROACH), battery tail (BATT_TAIL), tool and SWD access (SWD, TP) are listed above.
MAG_CLEAR is a 10 mm placeholder exclusion for new high-current or ferromagnetic items around the BMM350. **Display support land (DISP_LAND, X24).** The
rigid display rests on a case land behind its rim; it occupies the top t_land (0.3-0.8, PARAMETRIC) of the front gap from R_display - w_land (w_land 0.5-1.5,
PARAMETRIC, below the 2.5 mm POL border) to the case wall and is drawn with the widest land. It is interrupted at the display-FPC fold, must be <= 0.74 mm
thick (or relieved) over U4, and every F.Cu edge crossing passes under it (h_max, section G). **Battery tail (BATT_TAIL).** Because the pack wire exit
(BATT_EXIT, az 230-237) is 32-55 degrees from J201, the tail runs about 22 mm in the annulus and crosses the SW support window and the SW3 button window
(X13); a pack exit at the J201 azimuth (SR-BATT-PCM) deletes it.

## J. Assembly, service and SWD sequence

**Build states.** S0 bare MAIN on the bench; S1 MAIN + battery + REAR module open, display absent; S2 display seated, caseback open; S3 closed.

| Item | S0 bare MAIN | S1 module open, display absent | S2 display seated, caseback open | S3 closed |
|---|---|---|---|---|
| J1301 SWD | yes | yes | no | no |
| TP1301-TP1306 | yes | yes | no | no |
| J1 display connector | yes (display not mated) | yes | mated (V1: blind) | mated |
| J1501 sensor FPC | yes | yes | no | no |
| J201 battery | yes | yes | no | no |
| J202 charger harness | yes | yes | no | no |
| REAR optics / PPG test | n/a | yes (open face) | yes | window only |

**Sequence (provisional).**

1. [S0] MAIN bring-up: first-boot SWD at J1301 and rail check at TP13xx (display absent, battery absent).
2. [S0] Mount battery in carrier (B.Cu pockets for C901..C906, R901..R910, C206; insulation film); mate J201 from the south-west edge.
3. [S1] REAR module sub-assembly: REAR board + barrier + window/pod insert tested on its own; FPC attached at J1502 / tail.
4. [S1] Mate J1501 (mouth outward) and the charger strip to J202; fold FPC out-and-down into the carrier channel; seat REAR in the lower web.
5. [S1] Module functional test: SWD, PPG, MAX30208, charge entry via test dock - all F.Cu items still reachable.
6. [S2] Install MAIN on the case supports (SW/SE/NE and a W/NW support) and seat the display on its support land DISP_LAND (V1: module into the display-bonded case, J1 Z-push; V2: hinge closed after J1 mating). Counts one J1 cycle.
7. [S3] Caseback with gasket and screws; hard stops carry load; contact block face-seal; vent membrane and button seals checked.

**Orders.** *V1 display-first:* display bonded into a front pocket (glass exterior, t_front_extra 0), the module installed from the rear, J1 mates by Z-push
as the module seats (blind; 0.8 mm mated height; plug alignment float unknown; the face-to-face Z-push is an inference from the register and `package_heights.json`). *V2 module-first:* display hinged on its FPC, J1 / J1501 / J201 mated in
view, display closed onto MAIN; requires a lip/bezel or a front-load pocket and costs up to t_front_extra 0.5. The order is coupled to the cover
strategy (OD-COVER). **First-boot SWD** happens in S0 at J1301 (Tag-Connect TC2030-IDC-NL, no-legs, needs a retaining clip and clear vertical probe volume,
SR-TAGCONNECT). **Rework rule:** anything that needs F.Cu returns the unit to S1; J1 is rated 50 cycles and 25 planned seatings is the budget.
**Service-loop consequence:** S1 needs no slack because the REAR optical face is exposed from the wrist side; slack is only needed to hold the J1501
plug at a comfortable mating position. **Edge-wrap consequence:** every F.Cu mating (J1501, J201, J202) is made before the display is seated, so each of
those flexes already wraps the edge in S1. **Display land:** the display support land is a case feature; in V1 it is the floor of the front pocket that the
display is bonded to before the module goes in, so each crossing's conductor must already lie below h_max when the module is pushed home (X24).

**Relocation or outline feature required?** Not for build and test (S1). Post-closure SWD would need a new feature (OD-DEVACCESS): relocate J1301 / TP pads
(later placement phase) or add a probe-through feature in the outline co-design.

## 11. Key dimensional assumptions

| ID | Quantity | Value / range | Unit | Class | Conf. | Source |
|---|---|---|---|---|---|---|
| D01 | T_total target | 14.0 / 15.5 | mm | KNOWN | HIGH | PHASE_BRIEF.md 1a owner confirmation 2026-10-10 (exterior display glass to deepest wrist-facing pod surface) |
| D02 | T_total thin / nominal / thick | thin 13.3, nominal 14.5, thick 17.93 | mm | PARAMETRIC | MEDIUM | generated/zstack.json corners |
| D03 | H_F_under_display | 2.7 | mm | KNOWN | HIGH | main_height_map.json U8 (u-blox MAX-F10S mechanical table) |
| D04 | H_F runner-up | 1.96 | mm | KNOWN | HIGH | main_height_map.json U4 (Bosch BMP585) |
| D05 | H_B_in_battery | 0.95 | mm | PARAMETRIC | MEDIUM | main_height_map.json C901/C903 (0603 typical 0.9 + 0.05 solder; no MPN) |
| D06 | front_gap (thin/nom/thick) | thin 2.8, nominal 2.85, thick 3.0 | mm | PARAMETRIC | MEDIUM | zstack.json layers; H_F_under_display + c_front |
| D07 | t_display | min 1.95, nom 2.05, max 2.15 | mm | KNOWN | HIGH | ZC-A1D43W-046 spec V1.0 p4-5 |
| D08 | t_main | min 0.72, nom 0.8, max 0.88 | mm | KNOWN | MEDIUM | sportwatch_revA.kicad_pcb thickness 0.8; tolerance PARAMETRIC |
| D09 | back_zone (thin/nom/thick) | thin 1.03, nominal 1.1, thick 1.25 | mm | PARAMETRIC | MEDIUM | zstack.json layers |
| D10 | battery nominal cell | diameter 44.0, thickness 4.5 | mm | KNOWN | HIGH | input_register BATT-CELL (LPR454440 catalog) |
| D11 | battery_zone (thin/nom/thick) | thin 4.75, nominal 5.0, thick 5.5 | mm | SUPPLIER_DATA_REQUIRED | LOW | zstack.json; tol_pack_thick, g_axial are SUPPLIER |
| D12 | lower_web | min 0.3, nom 0.4, max 0.6 | mm | PARAMETRIC | LOW | stack_parameters.json |
| D13 | t_rear_pcb | min 0.6, nom 0.8, max 1.0 | mm | PARAMETRIC | MEDIUM | stack_parameters.json (staging file 1.6 mm/2-layer is placeholder) |
| D14 | h_rear_inner (single / double-sided) | min 0.0, nom 0.0, max 0.75 | mm | PARAMETRIC | MEDIUM | stack_parameters.json |
| D15 | optics_zone | h_optics_max min 0.7, nom 0.75, max 0.85, c_optics min 0.05, nom 0.1, max 0.2 | mm | KNOWN | MEDIUM | h_optics_max anchored on MAX30208 0.75 and SFH7018A/2703 0.6+/-0.1 (stack_parameters.json); SFH4053B/MAX86141 assumed (X10) |
| D16 | t_window | min 0.3, nom 0.5, max 0.8 | mm | PARAMETRIC | LOW | stack_parameters.json; material undecided |
| D17 | h_pod sweep | 0.0 / 0.5 / 0.8 / 1.0 / 1.5 | mm | PARAMETRIC | LOW | stack_parameters.json; needs wrist/strap trials |
| D18 | R_main / R_display / R_pol | 23.0 / 21.95 / 19.45 | mm | KNOWN | HIGH | input_register MAIN-OUTLINE, DISPLAY-MOD |
| D19 | R_case_inner nominal / conservative / optimistic | 24.05 / 23.4 / 24.5 | mm | PARAMETRIC | LOW | zstack.json radial |
| D20 | R_pack_max nominal / conservative | 22.15 / 22.25 | mm | SUPPLIER_DATA_REQUIRED | LOW | zstack.json radial; tol_pack_dia SUPPLIER |
| D21 | Edge-crossing / FPC out-and-down margin, exit at the land ceiling (upper bound) nominal / conservative / optimistic | 0.68 / -0.95 / 1.3 | mm | PARAMETRIC | LOW | edge_crossings.results.budget margin_at_h_max_mm (geometric derivation on zstack.json radial corners + display_land ranges) |
| D22 | REAR parts courtyard area | 203.01 | mm2 | KNOWN | MEDIUM | main_height_map.json rear_footprints (library courtyards; 44 refs) |
| D23 | REAR envelope diameter single-sided opt / nom / cons | optimistic 22.4, nominal 25.3, conservative 29.4 | mm | PARAMETRIC | LOW | rear_module.envelope_derivation |
| D24 | REAR envelope diameter double-sided opt / nom / cons | optimistic 16.4, nominal 18.8, conservative 24.4 | mm | PARAMETRIC | LOW | rear_module.envelope_derivation |
| D25 | Emitter-detector spacing study range | 3.0 / 8.0 | mm | PARAMETRIC | LOW | study placeholder; to be measured; no spacing claimed optimal |
| D26 | Minimum geometric emitter-PD pitch | 2.2 / 3.1 | mm | PARAMETRIC | LOW | half-bodies of SFH7018A 2.4 + SFH2703 2.0 or 3.2 plus 0.3-0.5 barrier (arithmetic on KNOWN OPT-PKG sizes; barrier thickness PARAMETRIC) |
| D27 | FPC length excl. service loop | 26.3 | mm | PARAMETRIC | LOW | fpc_path.length_estimate |
| D28 | Per-VLED-position current share | 41.3 | mA | PARAMETRIC | MEDIUM | 124 mA / 3 positions (PPG-LOAD); not a connector rating |
| D29 | Charger route R1 arc | 51.7 | mm | PARAMETRIC | LOW | R 18.5 az 100-260 |
| D30 | Largest unsupported arc | 193.8 | deg | KNOWN | MEDIUM | phase1_placement.json support windows (centres) |
| D31 | J1 mating cycles rated / planned | 50 / 25 | cycles | KNOWN | MEDIUM | OCN OK-23GF024-04 (50, input_register J1-DISPLAY); planned 25 is a PARAMETRIC allowance |
| D32 | Charge current setting | 0.4 | A | KNOWN | HIGH | design/interfaces/charger_harness.md (<=400 mA initial) |
| D33 | LED peak electrical (both AFEs) | 0.47 | W | PARAMETRIC | MEDIUM | 124 mA x ~3.82 V (main_rear_interface.md converter nominal); duty cycle unknown |
| D34 | Edge-crossing margin, flat exit (lower bound; equals the tool 180-degree wrap) nominal / conservative / optimistic | -0.47 / -2.1 / 0.7 | mm | PARAMETRIC | LOW | edge_crossings.results.budget margin_flat_exit_mm; equals zstack.json margin_edge_wrap (checked) |
| D35 | Minimum conductor exit height above F.Cu for zero margin nominal / conservative / optimistic (none = infeasible) | 0.096 / none / 0.0 | mm | PARAMETRIC | LOW | edge_crossings.results.budget h_exit_min_for_zero_margin_mm |
| D36 | Maximum mouth / bend-start radius for zero margin nominal / conservative / optimistic | 22.53 / 20.9 / 23.7 | mm | PARAMETRIC | LOW | edge_crossings.results.budget R_mouth_max_mm = R_case_inner - c - t - R_bend |
| D37 | Display support land width under the rim w_land | min 0.5, nom 1.0, max 1.5 | mm | PARAMETRIC | LOW | edge_crossings.display_land.w_land_mm (planning placeholder < 2.5 mm POL border; SR-DISPLAY-LAND) |
| D38 | Display support land thickness t_land | min 0.3, nom 0.5, max 0.8 | mm | PARAMETRIC | LOW | edge_crossings.display_land.t_land_mm (planning placeholder; case G3) |
| D39 | Land headroom over the tallest rim part (U4 BMP585) nominal / conservative / optimistic | 0.24 / -0.06 / 0.44 | mm | PARAMETRIC | LOW | edge_crossings.results.land_vs_rim_parts margin_mm (main_height_map.json courtyards and seated heights) |
| D40 | Land ceiling h_max for a conductor lower face above F.Cu nominal / conservative / optimistic | 2.03 / 1.5 / 2.5 | mm | PARAMETRIC | LOW | edge_crossings.results.budget h_max_mm = front_gap - t_land - c_fpc - t_fpc |
| D41 | Maximum conductor thickness beside the pack (t_allow) nominal / conservative / optimistic | 0.8 / -0.75 / 1.5 | mm | PARAMETRIC | LOW | edge_crossings.results.budget t_allow_straight_mm = R_case_inner - c_fpc - R_channel_inner |
| D42 | Lower-web under-run margin (sensor FPC, charger link) nominal / conservative / optimistic | 0.08 / -0.2 / 0.4 | mm | PARAMETRIC | LOW | edge_crossings.results.budget lower_web_margin_mm = t_lower_web - (t_fpc + c_fpc) |
| D43 | Charger approach z window over C207 nominal / conservative / optimistic | 0.88 / 0.25 / 1.45 | mm | PARAMETRIC | LOW | edge_crossings.results.crossings XC-J202 z_window_mm = h_max - c_fpc - h_parts |

## 12. Conflicts register

Verdicts: CONFIRMED / REFINED / REFUTED for the nine lead-identified candidates (brief section 7), NEW for items found during this study. Overlapping
reservations at the same Z level are enumerated by the generator and each pair is listed in at least one conflict. The detector is analytic: it cuts the
plane into vertical strips at every boundary intersection and evaluates the exact cross-section length of both interiors in each strip, so any
intersection of positive area is found (slivers, thin, coincident and contained shapes included; built-in self-tests in `check` cover these cases) and
boundaries that merely abut are not an overlap. Area is estimated separately for reporting only.

| ID | Brief | Verdict | Severity | Owner decision | Title |
|---|---|---|---|---|---|
| C1-FRONT-GAP | 1 | CONFIRMED | HIGH | **YES** (OD-U8) | Front gap governed by U8 MAX-F10S (2.7 mm max) |
| C2-DISPLAY-SIDE-CONNECTORS | 2 | REFINED | HIGH | **YES** (OD-DEVACCESS, OD-COVER) | J1 / J1301 / TP13xx / J1501 / J201 / J202 all face the display |
| C3-EDGE-WRAP | 3 | REFINED | HIGH | no | FPC edge-wrap versus case inner radius |
| C4-CHARGER-PATH | 4 | CONFIRMED | HIGH | **YES** (OD-J202) | Charger contacts rear east, J202 west, harness must avoid optics, antennas and BMM350 |
| C5-SOUTH-CROWDING | 5 | REFINED | MEDIUM | no | South sector crowding |
| C6-DISPLAY-FPC-FOLD | 6 | REFINED | MEDIUM | no | Display FPC fold up to 0.7 mm beyond the 43.9 outline |
| C7-WIFI-BEYOND-BOARD | 7 | CONFIRMED | MEDIUM | no | Wi-Fi reservation extends beyond the Ø46 board |
| C8-GNSS-OCCUPIED | 8 | REFUTED | LOW | no | GNSS radiator reservation already holds C1420, C1421, R1420 |
| C9-THICK-CORNER | 9 | CONFIRMED | HIGH | **YES** (OD-COVER, OD-REAR-SIDED) | Thick corner mixes design choices with tolerances |
| X10-OPTICS-HEIGHT-UNKNOWN | - | NEW | HIGH | no | SFH4053B and MAX86141 seated heights are unknown (hidden dependence in optics_zone) |
| X11-POD-FOOTPRINT | - | NEW | MEDIUM | **YES** (OD-REAR-SIDED) | Optical-face population dictates pod footprint (single- vs double-sided REAR) |
| X12-J1502-FACE | - | NEW | MEDIUM | **YES** (OD-REAR-SIDED) | J1502 face and mated height drive the single-/double-sided decision |
| X13-EDGE-CROSSINGS | - | NEW | HIGH | **YES** (OD-CONN-SIDE) | Four conductors rise through one thin annulus and cross the MAIN edge under the display land |
| X14-SUPPORT-GAP | - | NEW | MEDIUM | no | Three support windows leave a 194-degree unsupported arc on the west/north-west |
| X15-NE-CROWDING | - | NEW | MEDIUM | no | North-east sector: vent, ALS, SW4, support, TP13xx and BMM350 compete |
| X16-MAGNETOMETER | - | NEW | MEDIUM | no | BMM350 exposure to charge current, LED pulses and ferromagnetic pushers |
| X17-GNSS-ALL-HEIGHTS | - | NEW | MEDIUM | no | GNSS radiator "all assembly heights" volume overlaps display and pack |
| X18-PACK-EDGE | - | NEW | LOW | no | Support search windows and battery exit overlap the nominal pack disc |
| X19-BCU-0603 | - | NEW | LOW | no | Two 0603 B.Cu capacitors govern the back zone |
| X20-GROWTH-VS-OPTICS | - | NEW | MEDIUM | no | Pack growth / compression must never load the optical stack |
| X21-INGRESS-UNDEFINED | - | NEW | MEDIUM | **YES** (OD-WATER) | No ingress / water-resistance target is defined |
| X22-UNMODELLED-Z | - | NEW | MEDIUM | no | Several Z items are not in the tool stack |
| X23-WINDOW-CROSSTALK | - | NEW | MEDIUM | no | Residual crosstalk through a continuous optical window is unverified |
| X24-DISPLAY-LAND | - | NEW | HIGH | **YES** (OD-COVER, OD-WATER) | Display support land competes with the display-FPC fold, rim parts and every F.Cu edge crossing |

**Overlap register (generated; exact analytic detector).** Every pair of reservations whose open interiors intersect at a shared Z level (clipped at the nominal case outer radius 25.25), with the area estimate (Gauss-Legendre, reporting only) and the conflicts that list both. Areas shown as 0.00 are real slivers below 0.005 mm2.

| Pair | Z level(s) | Area mm2 | Conflicts listing both |
|---|---|---:|---|
| DISPLAY x GNSS_RAD | FRONT | 21.00 | X17-GNSS-ALL-HEIGHTS |
| DISPLAY x SWD | FRONT | 28.00 | C2-DISPLAY-SIDE-CONNECTORS |
| DISPLAY x TP | FRONT | 18.85 | C2-DISPLAY-SIDE-CONNECTORS, X15-NE-CROWDING |
| DISPLAY x ALS | FRONT | 27.10 | X15-NE-CROWDING |
| PACK x GNSS_RAD | BATTERY | 21.61 | X17-GNSS-ALL-HEIGHTS |
| PACK x BATT_EXIT | BATTERY | 2.46 | X18-PACK-EDGE |
| PACK x SUP_SW | BATTERY | 0.69 | X18-PACK-EDGE |
| PACK x SUP_SE | BATTERY | 6.02 | X18-PACK-EDGE |
| PACK x SUP_NE | BATTERY | 0.09 | X18-PACK-EDGE |
| GNSS_RAD x DISP_LAND | MAIN | 39.30 | X24-DISPLAY-LAND |
| BLE_RAD x SW1 | MAIN | 1.51 | C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| BLE_RAD x DISP_LAND | MAIN | 29.40 | C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| WIFI_RAD x SW5 | MAIN | 19.50 | C7-WIFI-BEYOND-BOARD, X24-DISPLAY-LAND |
| WIFI_RAD x DISP_LAND | MAIN | 15.88 | C4-CHARGER-PATH, X24-DISPLAY-LAND |
| J1501 x DISP_LAND | MAIN | 9.71 | C3-EDGE-WRAP, X24-DISPLAY-LAND |
| J201 x DISP_LAND | MAIN | 10.31 | X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| J202 x DISP_FPC | MAIN | 0.00 | C2-DISPLAY-SIDE-CONNECTORS, C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| J202 x DISP_LAND | MAIN | 0.43 | C4-CHARGER-PATH, C6-DISPLAY-FPC-FOLD, X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| J202 x CHG_APPROACH | MAIN | 0.85 | C4-CHARGER-PATH, X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| BATT_EXIT x SW3 | MAIN | 1.60 | C5-SOUTH-CROWDING, X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| BATT_EXIT x DISP_LAND | MAIN | 2.48 | X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| SUP_SW x DISP_LAND | MAIN | 8.84 | X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| SUP_SW x BATT_TAIL | BATTERY+MAIN | 4.91 | X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| SUP_SE x FPC_CORR | BATTERY+MAIN | 2.38 | C5-SOUTH-CROWDING, X24-DISPLAY-LAND |
| SUP_SE x DISP_LAND | MAIN | 14.39 | X24-DISPLAY-LAND |
| SUP_NE x VENT | MAIN | 10.67 | X15-NE-CROWDING, X16-MAGNETOMETER, X24-DISPLAY-LAND |
| SUP_NE x MAG_CLEAR | MAIN | 0.87 | X15-NE-CROWDING, X16-MAGNETOMETER, X24-DISPLAY-LAND |
| SUP_NE x DISP_LAND | MAIN | 5.43 | X24-DISPLAY-LAND |
| DISP_FPC x SW1 | MAIN | 1.57 | C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| DISP_FPC x SW2 | MAIN | 5.34 | C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| DISP_FPC x DISP_LAND | MAIN | 21.51 | C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| TP x VENT | MAIN | 0.18 | X15-NE-CROWDING, X16-MAGNETOMETER, X24-DISPLAY-LAND |
| TP x MAG_CLEAR | MAIN | 9.78 | X15-NE-CROWDING, X16-MAGNETOMETER, X24-DISPLAY-LAND |
| TP x DISP_LAND | MAIN | 1.86 | X24-DISPLAY-LAND |
| VENT x SW4 | MAIN | 12.86 | X15-NE-CROWDING, X16-MAGNETOMETER, X24-DISPLAY-LAND |
| VENT x MAG_CLEAR | MAIN | 44.05 | X15-NE-CROWDING, X16-MAGNETOMETER, X24-DISPLAY-LAND |
| VENT x DISP_LAND | MAIN | 41.94 | X24-DISPLAY-LAND |
| SW1 x DISP_LAND | MAIN | 17.99 | C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| SW2 x DISP_LAND | MAIN | 17.99 | C4-CHARGER-PATH, C6-DISPLAY-FPC-FOLD, X24-DISPLAY-LAND |
| SW3 x DISP_LAND | MAIN | 17.99 | C4-CHARGER-PATH, X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| SW3 x BATT_TAIL | MAIN | 1.69 | X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| SW4 x MAG_CLEAR | MAIN | 25.70 | X15-NE-CROWDING, X16-MAGNETOMETER, X24-DISPLAY-LAND |
| SW4 x DISP_LAND | MAIN | 17.99 | X24-DISPLAY-LAND |
| SW5 x DISP_LAND | MAIN | 17.99 | X24-DISPLAY-LAND |
| MAG_CLEAR x REAR_ENV | REAR | 78.15 | X16-MAGNETOMETER |
| MAG_CLEAR x CHG_CONTACT | REAR | 19.65 | C4-CHARGER-PATH, X16-MAGNETOMETER |
| MAG_CLEAR x DISP_LAND | MAIN | 63.65 | C4-CHARGER-PATH, X24-DISPLAY-LAND |
| LRA x FPC_UNDER | REAR | 40.99 | C4-CHARGER-PATH, C5-SOUTH-CROWDING |
| LRA x CHG_ROUTE | REAR | 29.06 | C4-CHARGER-PATH, C5-SOUTH-CROWDING, X13-EDGE-CROSSINGS |
| FPC_UNDER x CHG_ROUTE | REAR | 26.06 | C4-CHARGER-PATH, C5-SOUTH-CROWDING |
| FPC_CORR x DISP_LAND | MAIN | 15.24 | C3-EDGE-WRAP, X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| DISP_LAND x CHG_RISER | MAIN | 4.11 | C4-CHARGER-PATH, X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| DISP_LAND x CHG_APPROACH | MAIN | 12.83 | C4-CHARGER-PATH, X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |
| DISP_LAND x BATT_TAIL | MAIN | 22.73 | X13-EDGE-CROSSINGS, X24-DISPLAY-LAND |

### C1-FRONT-GAP - Front gap governed by U8 MAX-F10S (2.7 mm max)

- **Verdict:** CONFIRMED; **severity:** HIGH; **owner decision:** YES (OD-U8); **gate:** before case + final MAIN outline co-design
- **Description:** The gap between the rigid display rear plane and MAIN F.Cu is set by one part: U8 (2.7 mm max, at (100,86), r 14.0, fully under the display). The runner-up is U4 BMP585 at 1.96 mm. front_gap is 2.85 mm of the 14.5 mm nominal T_total.
- **Evidence:**
  - generated/zstack.md layer table: front_gap 2.80 / 2.85 / 3.00 mm (thin / nominal / thick), governing term H_F_under_display + c_front
  - generated/main_height_map.md: H_F_under_display 2.7 (U8), runner-up 1.96 (U4); next three F.Cu parts are 1.5 (C402, C705, U11, PARAMETRIC)
  - inputs/package_heights.json MAX-F10S_UBL: 2.5 nom / 2.7 max (u-blox mechanical table, KNOWN); phase1_placement.json fixed_main_refs contains U8 (protected foundation)
  - Cost of U8 over U4 = 2.7 - 1.96 = 0.74 mm at every corner (c_front cancels); 1.20 mm if U4 is also removed (next 1.5). Cross-checked on a throw-away tool copy (T_total nominal 13.76, thick 17.19).
  - mech_model applies the package max (2.7) at all corners; at the 2.5 nominal height the front gap would shrink by 0.20 mm - usable only with the u-blox drawing and a stated tolerance policy
- **Options:**
  - O1: Accept; carry 0.74 mm as a named line in the budget (reversible, no change).
  - O2: Close the tolerance policy against the u-blox package drawing (at most 0.20 mm, SUPPLIER).
  - O3: Alternative GNSS part or B.Cu relocation of U8 (frozen foundation; 0.74 mm; RF feed re-plan).
  - O4: Display with a rear relief (custom supplier part; unlikely).
- **Recommended provisional direction:** O1 for this phase. Re-open O3 only if the owner makes the 15.5 mm upper target a hard worst-case requirement (see C9).

### C2-DISPLAY-SIDE-CONNECTORS - J1 / J1301 / TP13xx / J1501 / J201 / J202 all face the display

- **Verdict:** REFINED; **severity:** HIGH; **owner decision:** YES (OD-DEVACCESS, OD-COVER); **gate:** before MAIN placement revision / case co-design
- **Description:** Confirmed and refined. All 167 F.Cu parts face the display; 166 lie under its outline. No assembly order keeps J1301 / TP1301-TP1306 reachable after the display is seated. J1501 and J201 mouths (reservation r up to 22.66 / 22.80) sit in the 21.95-23.0 band beyond the display outline, but can only be mated before the display is seated. J202 (r <= 20.76) is wholly under the display. Therefore every F.Cu mating and the SWD session must happen in build state S1 (MAIN + battery + REAR module, display absent).
- **Evidence:**
  - input_register J1-DISPLAY: OK-23GF024-04 at (81.2,96.25), mated 0.8 mm, 50 mating cycles
  - input_register J1301-SWD, TP13xx: F.Cu faces the display; no-legs Tag-Connect needs a retaining clip and a clear vertical probe volume (no local drawing)
  - architecture.json reservations: J1501 raw r max 22.66, J201 22.80, J202 20.76; DISPLAY r 21.95
  - INFERENCE: the display FPC folds behind the panel (input_register DISPLAY-FPC) and the J1 mated height is board-to-FPC-stiffener 0.8 mm (package_heights.json OK-23GF024-04), so J1 is mated face to face between display rear and MAIN F.Cu, i.e. by a Z-push when display and MAIN are brought together; fold exit and plug location are not dimensioned
  - Overlaps listed by the generator: DISPLAY x SWD 28.0 mm2, DISPLAY x TP 18.85 mm2 (FRONT level access volumes)
- **Options:**
  - O1: S1 test state + development fixture: mate and test every F.Cu connector with the display absent (no change).
  - O2: Development-only hinged display on its FPC (needs fold exit direction and length, SUPPLIER).
  - O3: Relocate J1301 / TP pads to an edge-accessible or B.Cu position in a later placement phase (OWNER).
  - O4: No post-closure SWD; update by BLE/DFU only (firmware policy).
- **Recommended provisional direction:** O1 now. Plan the 50-cycle J1 budget as at most 25 planned display seatings (PARAMETRIC planning allowance). Decide O3 at the placement phase.
- **Reservations involved:** DISPLAY, SWD, TP, J1501, J201, J202, DISP_FPC

### C3-EDGE-WRAP - FPC edge-wrap versus case inner radius

- **Verdict:** REFINED; **severity:** HIGH; **owner decision:** no; **gate:** before outline freeze
- **Description:** The tool 180-degree wrap fails at the nominal corner (margin -0.47). The earlier out-and-down figure (+0.58 nominal with the bend assumed to start at the display outline R 21.95) is withdrawn: a downward bend is not limited by the display edge but by the MAIN edge corner, the height h of the FPC lower face above F.Cu at the mouth and the display support land above it (X24). Geometric derivation (section G, architecture.json edge_crossings): the margin lies between a flat exit (h = 0) of -0.47 / -2.10 / +0.70 mm, identical to the tool wrap, and an exit at the land ceiling (h = h_max 2.03 / 1.50 / 2.50) of +0.68 / -0.95 / +1.30 mm, identical to the straight run (nominal / conservative / optimistic). Nominal zero margin needs the J1501 mouth (bend start) at R <= 22.53 and an exit height >= 0.10 mm; the full channel-governed margin needs h >= 0.86 mm (bend start R 21.85). The conservative corner fails by at least 0.95 mm whatever the bend, so it is a case-wall / channel budget issue, not a bend-type issue. The exit height and mouth radius are connector data (SR-FPC-MECH).
- **Evidence:**
  - zstack.md radial table: margin_edge_wrap -0.47 / -2.10 / 0.70, margin_straight_run 0.68 / -0.95 / 1.40 (nominal / conservative / optimistic)
  - edge_crossings.model: bend may start s(h) = sqrt(R_bend^2 - (R_bend - h)^2) inboard of the MAIN edge; R_v = max(R_main + R_bend - s(h), R_channel_inner); margin = R_case_inner - (R_v + t_fpc + c_fpc)
  - edge_crossings.results.budget: flat exit -0.47 / -2.10 / 0.70; land ceiling 0.68 / -0.95 / 1.30; h_exit for zero margin 0.10 / none / 0.00; R_mouth max 22.53 / 20.90 / 23.70 (arch_diagrams.py check recomputes these and asserts flat exit == tool margin_edge_wrap)
  - display support land (X24): h_max = front_gap - t_land - c_fpc - t_fpc = 2.03 / 1.50 / 2.50 mm caps the exit height
  - J1501 window raw r max 22.66 (phase1_placement.json reservations[3]) exceeds R_mouth max 22.53: the outer 0.13 mm of the window cannot hold the mouth at nominal
  - Recovery needed at the conservative corner: 0.95 mm (channel-governed). Candidate levers by parameter range: local case wall 1.6 -> 1.0 (+0.6), c_radial 1.0 -> 0.5 (+0.5), t_carrier_wall 0.6 -> 0.3 (+0.3)
- **Options:**
  - O1: Out-and-down 2 x 90 deg with J1501 mouth outward at R <= 22.53 and exit height >= 0.10 mm (nominal margin -0.47 .. +0.68 by exit height).
  - O2: Local case relief / wall thinning at the FPC station (case co-design).
  - O3: MAIN edge notch or slot for the FPC (outline change, later co-design).
  - O4: J1501 on B.Cu (placement phase; avoids the F.Cu wrap).
- **Recommended provisional direction:** O1 plus O2 as the design target: J1501 mouth at R <= 22.53 with an FPC exit height >= 0.10 mm (>= 0.86 mm for the full +0.68 mm), confirmed by the connector drawing (SR-FPC-MECH); do not rely on a 180-degree wrap or a flat exit. Close the conservative 0.95 mm with a local case relief at the FPC station (O2).
- **Reservations involved:** J1501, FPC_CORR, FPC_UNDER, DISP_LAND

### C4-CHARGER-PATH - Charger contacts rear east, J202 west, harness must avoid optics, antennas and BMM350

- **Verdict:** CONFIRMED; **severity:** HIGH; **owner decision:** YES (OD-J202); **gate:** before MAIN placement revision and contact-module selection
- **Description:** Contacts sit at az 80-100 (rear east); J202 is at az 260-269 on F.Cu west under the display. The harness needs about 175 degrees of travel. Recommended provisional route R1 is a REAR-level strip along the south chord at R 18.5 (arc 51.7 mm). R1 still has to rise past the pack to J202: link under the pack edge in the lower web (CHG_LINK), riser in a 10-degree annulus slot at az 249-259 between the SW3 and SW2 placeholders (CHG_RISER, 4.02 mm arc at R_channel_inner nominal) and an approach under the display support land over C207 (CHG_APPROACH). Its radial budget is edge crossing XC-J202 (section G): flat-exit / land-ceiling margin -0.47 / +0.68 nominal, -2.10 / -0.95 conservative, +0.70 / +1.30 optimistic with a flat-flex stand-in; maximum conductor thickness beside the pack 0.80 / none / 1.50; lower-web link margin +0.08 / -0.20 / +0.40; front-gap z window over C207 0.88 / 0.25 / 1.45. R1 is preferred over R2 (annulus R 23.6, arc 65.9 mm) because it uses 10 degrees of annulus instead of 160, not because it avoids the annulus; R3 via north (arc 61.3 mm) passes BMM350/GNSS/BLE.
- **Evidence:**
  - charger_harness.md: contacts GND/+5V/+5V/GND, raw 5 V never in J1501/J1502; J202 on MAIN west; no magnet
  - main_height_map.json: BMM350 U703 at (113.8,92.6), az 62, r 15.7 - 10.3 mm in plan from a contact block centred at (121,100) (arithmetic)
  - Wi-Fi reservation az 107.7-128.8 begins 7.7 deg (about 3 mm at R 22) from the placeholder contact block edge at az 100
  - Generator overlaps: CHG_ROUTE x FPC_UNDER 26.06 mm2, CHG_ROUTE x LRA 29.06 mm2 (REAR level), MAG_CLEAR x CHG_CONTACT 19.65 mm2
  - Annulus available for crossings: margin_main_to_case 1.05 / 0.40 / 1.50 (nominal / conservative / optimistic)
  - edge_crossings.results.budget and crossings XC-J202 (recomputed by arch_diagrams.py check): riser radial budget per corner as quoted above
  - Riser slot az 249-259 lies inside the 247.5-262.5 gap between the SW3 and SW2 placeholder windows (checked); J202 window exact az 259.8-269.0
  - C207 (0.95 mm, main_height_map.json) is the tallest F.Cu part under the approach (az 249-262, r from the land inner edge to R_main)
- **Options:**
  - R1: REAR-level strip along the south chord with a 10-degree riser slot at az 249-259 to J202 (recommended).
  - R2: Annulus route (R 23.6).
  - R3: North route (rejected: BMM350 / GNSS / BLE sectors).
  - R4: Relocate J202 toward the south-east in a later placement phase (OWNER).
  - R5: Fabricated contact flex as its own project (charger_harness.md clause).
- **Recommended provisional direction:** R1 with a module-carried, face-sealed contact block and the explicit riser CHG_LINK / CHG_RISER / CHG_APPROACH; route +5V/GND as a tightly coupled pair; harness conductor <= 0.80 mm thick beside the pack (nominal) and exit >= 1.15 mm above F.Cu over C207; the conservative corner needs the same local case relief as the sensor FPC (C3, X13); characterise the BMM350 on a prototype. OD-J202 (J202 toward the contact block) would remove the west riser.
- **Reservations involved:** CHG_CONTACT, CHG_ROUTE, CHG_LINK, CHG_RISER, CHG_APPROACH, J202, MAG_CLEAR, WIFI_RAD, FPC_UNDER, LRA, DISP_LAND, SW2, SW3

### C5-SOUTH-CROWDING - South sector crowding

- **Verdict:** REFINED; **severity:** MEDIUM; **owner decision:** no; **gate:** before perimeter freeze (LRA)
- **Description:** At reservation level the MAIN-level windows do not overlap each other (J201 and J1501 are 0.7 mm apart; the J1301 courtyard is 0.4 mm below the J1501 window). The real crowding is at the REAR level and in the annulus: LRA pocket, sensor FPC under-run and the charger strip share az 150-195, and the SE support search window crosses the FPC channel.
- **Evidence:**
  - Reservation windows: J1501 x 100.2-108.5, y 116.4-121.0; J201 x 94-99.5, y 119-122; J1301 courtyard y 112-116 (phase1_placement.json, main_height_map.json)
  - Generator overlaps: LRA x FPC_UNDER 40.99 mm2, LRA x CHG_ROUTE 29.06 mm2, FPC_UNDER x CHG_ROUTE 26.06 mm2, SUP_SE x FPC_CORR 2.38 mm2, BATT_EXIT x SW3 1.60 mm2
  - LRA footprint unknown (input_register LRA); MAIN-level placement is not available inside the annulus (0.40-1.50 mm) and the front gap is fully used under the display
- **Options:**
  - O1: Keep FPC at az 153-167, move LRA pocket to az 180-195, charger strip passes outside the LRA radius.
  - O2: Put the LRA on MAIN F.Cu in a free south-centre region in the placement phase (needs LRA height <= front-gap headroom).
  - O3: Shift the SE support to az 143-152 and keep the FPC channel clear.
- **Recommended provisional direction:** O1 and O3 at the REAR-level co-design; LRA size is the gate.
- **Reservations involved:** J1501, J201, SWD, BATT_EXIT, LRA, SUP_SW, SUP_SE, SW3, WIFI_RAD, CHG_ROUTE, FPC_UNDER, FPC_CORR

### C6-DISPLAY-FPC-FOLD - Display FPC fold up to 0.7 mm beyond the 43.9 outline

- **Verdict:** REFINED; **severity:** MEDIUM; **owner decision:** no; **gate:** before case co-design
- **Description:** The fold reaches R 21.95 + 0.7 = 22.65, which is inside the MAIN envelope (R 23.0) and 1.40 / 0.75 mm inside R_case_inner (nominal / conservative). The real issue is the crowded west corridor: J1 (az 269-294), J202 (az 260-269), NT201 and the SW1-SW3 pusher windows share it, and the fold exit direction and width are not dimensioned. The display support land (X24) cannot pass under the fold, so the land is interrupted over the fold arc.
- **Evidence:**
  - input_register DISPLAY-FPC (SUPPLIER_DATA_REQUIRED, LOW): footprint up to 0.7 MAX beyond outline; fold thickness 0.3-0.6 (t_display_fpc_fold) not in the stack
  - Generator overlaps: DISP_FPC x SW1 1.57 mm2, DISP_FPC x SW2 5.34 mm2, BLE_RAD x SW1 1.51 mm2, J202 x DISP_FPC < 0.01 mm2 (J202 window corner at az 269.0 touches the fold sector), DISP_FPC x DISP_LAND 21.51 mm2
  - Fold lives in the front gap; with front_gap 2.85 mm nominal and parts under the fold <= 1.05 mm (L201/L202) it does not govern the gap
- **Options:**
  - O1: Offset SW1/SW2 pusher bores away from az 269-295 (case co-design).
  - O2: Request fold exit direction / width / plug alignment float from the display supplier (blocking for the J1 corridor).
- **Recommended provisional direction:** O2 first; O1 at case co-design.
- **Reservations involved:** DISP_FPC, SW1, SW2, BLE_RAD, J202, DISP_LAND

### C7-WIFI-BEYOND-BOARD - Wi-Fi reservation extends beyond the Ø46 board

- **Verdict:** CONFIRMED; **severity:** MEDIUM; **owner decision:** no; **gate:** before antenna selection / case co-design
- **Description:** Confirmed and tightened: the register states r up to about 24.5; the rectangle corner at (124,115.5) is at r 28.57, beyond the case outer radius (25.0-25.5). The rectangle is therefore not a valid volume: the usable radiator space is the arc sector az 107.7-128.8, r 20.6-25.25, a case/radome volume.
- **Evidence:**
  - phase1_placement.json reservations[2] [119,107.5,124,115.5]
  - input_register MAIN-RES note (r up to ~24.5)
  - Generator overlap WIFI_RAD x SW5 19.5 mm2
- **Options:**
  - O1: Radome / antenna carrier in the case wall at az 108-129.
  - O2: Antenna on a flex in the caseback; contact block must stay > 3 mm away.
- **Recommended provisional direction:** O1; clip the volume to the annular sector and let the antenna selection set depth.
- **Reservations involved:** WIFI_RAD, SW5

### C8-GNSS-OCCUPIED - GNSS radiator reservation already holds C1420, C1421, R1420

- **Verdict:** REFUTED; **severity:** LOW; **owner decision:** no; **gate:** before antenna selection
- **Description:** Refuted as an intrusion: the three 0201 parts are the antenna feed network. R1420 (0R) is in series between /GNSS_RF and GNSS_ANT_50R; C1420 and C1421 (both DNP) are shunt-to-GND at each side; AE1420 and TP1420 hang on GNSS_ANT_50R. They belong inside the "radiator / feed opportunity". Residual issue: the feed network (r 20.9-21.4) lies under the display outline and the "all heights" volume overlaps the display and the pack (see X17).
- **Evidence:**
  - design/interfaces/validation/main_netlist.xml: R1420 pins /GNSS_RF, /14_RF/GNSS_ANT_50R; C1420 /GNSS_RF-GND; C1421 /14_RF/GNSS_ANT_50R-GND; AE1420 and TP1420 on /14_RF/GNSS_ANT_50R
  - main_height_map.md reservation table: C1420 0.38, C1421 0.38, R1420 0.33 mm seated
  - phase1_placement.json fixed_main_refs contains C1420, C1421, R1420 (protected foundation)
- **Options:**
  - O1: Treat as feed network; keep the radiator keep-out starting at the feed (no relocation).
- **Recommended provisional direction:** O1.
- **Reservations involved:** GNSS_RAD

### C9-THICK-CORNER - Thick corner mixes design choices with tolerances

- **Verdict:** CONFIRMED; **severity:** HIGH; **owner decision:** YES (OD-COVER, OD-REAR-SIDED); **gate:** before case co-design
- **Description:** Of the 3.43 mm between nominal and thick, 2.05 mm are design choices (added cover 0.5, double-sided REAR 0.85 at nominal-class, window 0.3, REAR PCB 0.2, lower web 0.2) and 1.38 mm are tolerance / supplier / clearance terms (1.28 linear + 0.10 for c_rear_inner). With design choices fixed per scenario the 15.5 mm upper target is met at nominal tolerances by S1, S2, S3 and S5, by RSS tolerances only by S1 and S3, and by no scenario with linear worst-case tolerances (best, S1: 15.78 mm).
- **Evidence:**
  - zstack.md: thick - nominal = 3.43; top-3 contributors rear_inner 0.95, front_extra 0.5, battery_zone 0.5
  - architecture.json scenario_results (recomputed from tool layer outputs by arch_diagrams.py check; S6 reproduces the tool thick corner 17.93)
  - Linear worst-case S1 = 14.5 + 1.28 = 15.78 mm; with C901/C903 as 0402 (-0.35, X19) = 15.43 mm
- **Options:**
  - O1: Report scenarios, not one thick number (adopted).
  - O2: Take X19 (-0.35) and the U8 policy (C1) to bring S1 below 15.5 at linear worst case.
- **Recommended provisional direction:** Baseline architecture = S1; S3 only if the owner selects a lip/bezel; S2 only with levers X19 / C1 closed.

### X10-OPTICS-HEIGHT-UNKNOWN - SFH4053B and MAX86141 seated heights are unknown (hidden dependence in optics_zone)

- **Verdict:** NEW; **severity:** HIGH; **owner decision:** no; **gate:** before REAR optical placement
- **Description:** optics_zone = h_optics_max (0.75 nom, 0.85 max) + c_optics. The 0.75 value is anchored on MAX30208 and on SFH7018A/SFH2703 (0.6 +/-0.1); D405-D407 (SFH4053B) and U12/U13 (MAX86141 WLP) have no local height. If either exceeds the assumption the window plane moves 1:1 in T_total.
- **Evidence:**
  - package_heights.json: OSRAM_SFH4053B_1.0x0.5mm and 21-100134_N201A2-1_MXM max_mm = null (SUPPLIER_DATA_REQUIRED)
  - stack_parameters.json h_optics_max source: assumed <= MAX30208
  - main_height_map.md unknown-height REAR refs: D405, D406, D407, U12, U13
- **Options:**
  - O1: Per-device windows / spacers so only the tall part raises its own window.
  - O2: Obtain datasheet / package outline (gate before REAR optical placement).
- **Recommended provisional direction:** O2; keep h_optics_max a named assumption in every total.

### X11-POD-FOOTPRINT - Optical-face population dictates pod footprint (single- vs double-sided REAR)

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** YES (OD-REAR-SIDED); **gate:** before REAR placement / case co-design
- **Description:** The interior depth from the REAR optical face to the skin plane is optics_zone + window = 1.35 mm nominal; the caseback plane is h_pod (0.8 nominal) above the skin plane, leaving 0.55 mm minus the caseback wall outside the pod. Parts 0.6-0.75 mm tall on the optical face therefore have to sit inside the pod footprint. Single-sided REAR means the pod covers the whole envelope (D 22.4-29.4 mm); double-sided can shrink it to the optical group but costs rear_inner (0.85 mm nominal-class).
- **Evidence:**
  - zstack.md nominal layers optics_zone 0.85, window 0.5; h_pod nominal 0.8 (stack_parameters.json, PARAMETRIC LOW)
  - architecture.json rear_module.envelope_results
- **Options:**
  - O1: Pod covers all optical-face parts (single-sided).
  - O2: Double-sided REAR with a small pod.
  - O3: Lower h_pod to 0-0.5 (wrist trials).
- **Recommended provisional direction:** O1 as baseline; evaluate O3 with wrist trials before choosing O2.
- **Reservations involved:** REAR_ENV

### X12-J1502-FACE - J1502 face and mated height drive the single-/double-sided decision

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** YES (OD-REAR-SIDED); **gate:** before connector MPN and REAR placement freeze
- **Description:** J1502 is a footprint-TBD provision. On the inner face it costs its mated height + c_rear_inner in rear_inner; on the optical face it is stack-neutral only if its mated height fits optics_zone (0.85 mm nominal) and the pod covers it. The FPC under-run needs t_lower_web >= t_fpc + c_fpc = 0.32 mm nominal (lower_web nominal 0.40, range 0.3-0.6); at t_fpc 0.2 + c_fpc 0.3 the 0.3 mm minimum web fails.
- **Evidence:**
  - main_rear_interface.md: connector MPN, mated height, permutation TBD
  - stack_parameters.json t_lower_web 0.3-0.6, t_fpc 0.1-0.2, c_fpc 0.1-0.3
  - input_register J1-DISPLAY: 0.8 mm is the OK-23 class mated height (not a J1502 value)
- **Options:**
  - O1: Inner-face J1502 (double-sided).
  - O2: Optical-face J1502 inside the pod, FPC wraps the REAR edge.
  - O3: Hot-bar FPC tail without J1502 (changes service model).
- **Recommended provisional direction:** O2 if the connector mated height is <= 0.85 mm; otherwise O1 with the cost carried in S2.
- **Reservations involved:** FPC_UNDER, REAR_ENV

### X13-EDGE-CROSSINGS - Four conductors rise through one thin annulus and cross the MAIN edge under the display land

- **Verdict:** NEW; **severity:** HIGH; **owner decision:** YES (OD-CONN-SIDE); **gate:** before MAIN placement revision / outline freeze
- **Description:** Edge crossings (section G table): sensor FPC XF-J1501 (FPC_CORR, az 153-180), charger riser XC-J202 (CHG_RISER, az 249-259), battery tail XB-J201 (BATT_TAIL, az 181-237: the pack exit BATT_EXIT at az 230-237 is 32-55 degrees from the J201 window at az 181-197, so the tail runs about 22 mm in the annulus and crosses the SW support search window and the SW3 button window) and, only if the LRA stays at the REAR level and DRV2625 U7 stays on F.Cu, the LRA leads XL-LRA (azimuth open). The annulus beyond MAIN is 1.05 / 0.40 / 1.50 mm (nominal / conservative / optimistic). With the flat-flex stand-in every crossing has the same radial budget: flat-exit margin -0.47 / -2.10 / +0.70 and land-ceiling margin +0.68 / -0.95 / +1.30 mm; nominal feasibility needs each conductor <= 0.80 mm thick beside the pack, its bend start at R <= 22.53 and its exit >= 0.10 mm above F.Cu (and above the tallest approach part: C207 0.95 for XC-J202). They are tangentially separated, so nominally feasible under those conditions; at the conservative corner no crossing fits (>= 0.95 mm short) without a local case relief.
- **Evidence:**
  - zstack.md margin_main_to_case 1.05 / 0.40 / 1.50; margin_straight_run 0.68 / -0.95 / 1.40
  - edge_crossings.results (budget, crossings): recomputed by arch_diagrams.py check; flat exit equals the tool margin_edge_wrap at every corner
  - input_register J201-PIN (J201 on F.Cu), J202-LOC, FPC-CONTRACT; BATT-PCM 'preferred exit toward south-west PMIC sector'
  - main_height_map.json: U7 DRV2625 at (113.3,114.0); C207 0.95 under the XC-J202 approach
  - Overlap register: SUP_SW x BATT_TAIL 4.91 mm2, SW3 x BATT_TAIL 1.69 mm2 (battery tail in the annulus)
- **Options:**
  - O1: Keep crossings tangentially separated; one local case relief per crossing for the conservative corner.
  - O2: Move J201/J1501 to B.Cu so battery and sensor never bend over the F.Cu edge (placement phase, OD-CONN-SIDE).
  - O3: Edge notches in MAIN (outline co-design).
  - O4: Pack wire exit at the J201 azimuth (SR-BATT-PCM) to delete the 22 mm BATT_TAIL annulus run.
  - O5: J202 toward the contact block (OD-J202) to delete the west riser XC-J202.
- **Recommended provisional direction:** O1 now with O4 requested from the pack supplier; O2 and O5 evaluated in the placement phase; LRA position decides whether XL-LRA exists.
- **Reservations involved:** FPC_CORR, BATT_EXIT, BATT_TAIL, J201, J202, CHG_ROUTE, CHG_LINK, CHG_RISER, CHG_APPROACH, LRA, DISP_LAND, SUP_SW, SW3

### X14-SUPPORT-GAP - Three support windows leave a 194-degree unsupported arc on the west/north-west

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** no; **gate:** before case co-design
- **Description:** The SW/SE/NE support-search windows centre at az [206.6, 150.8, 40.4]; the arcs between them are [110.4, 55.8, 193.8] degrees. The 193.8-degree arc through west/north-west carries J1 (Z-push mating), SW1-SW3, BLE and J202 on a 0.8 mm MAIN.
- **Evidence:**
  - phase1_placement.json support search SW/SE/NE rectangles (centres computed)
  - input_register MAIN-STACKUP 0.8 mm 8-layer
- **Options:**
  - O1: Add a fourth case support at W/NW in the co-design phase.
  - O2: Use the carrier web as distributed support (t_carrier_web 0.4-0.8).
- **Recommended provisional direction:** O1; verify J1 mating and button-load deflection by test.
- **Reservations involved:** SUP_SW, SUP_SE, SUP_NE, DISP_FPC

### X15-NE-CROWDING - North-east sector: vent, ALS, SW4, support, TP13xx and BMM350 compete

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** no; **gate:** before case co-design
- **Description:** Barometer vent (az 30-60), ALS aperture (az 45-75, through the cover-glass border annulus r 19.45-21.95), SW4 (az 52.5-67.5), the NE support window, TP1301-TP1306 and BMM350 all sit in az 20-80.
- **Evidence:**
  - Generator overlaps: VENT x SUP_NE 10.67, VENT x SW4 12.86, VENT x MAG_CLEAR 44.05, SW4 x MAG_CLEAR 25.70, TP x MAG_CLEAR 9.78, TP x VENT 0.18, SUP_NE x MAG_CLEAR 0.87, DISPLAY x ALS 27.10 (mm2)
  - main_height_map.json: U4 r 19.55 az 42, U5 r 20.8 az 56, U703 r 15.7 az 62
- **Options:**
  - O1: Move SW4 to az 70-85 (register says right 2/4).
  - O2: Vent and ALS share one case aperture strip, support moved to az 0-20.
- **Recommended provisional direction:** Resolve in case co-design with the display border drawing (SUPPLIER).
- **Reservations involved:** VENT, ALS, SW4, SUP_NE, TP, MAG_CLEAR, DISPLAY

### X16-MAGNETOMETER - BMM350 exposure to charge current, LED pulses and ferromagnetic pushers

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** no; **gate:** before charger module selection
- **Description:** BMM350 U703 is 10.3 mm in plan from the charger block and sits above the NE part of the REAR envelope (78 mm2 inside the 10 mm placeholder zone). A lone 0.4 A conductor at 10 mm gives about 8 uT (physics, not measurement). No watch-side magnet is allowed (frozen).
- **Evidence:**
  - charger_harness.md (0.4 A charge-current setting); main_height_map.json U703
  - Generator overlaps MAG_CLEAR x REAR_ENV 78.15, x CHG_CONTACT 19.65, x SW4 25.70, x SUP_NE 0.87
- **Options:**
  - O1: Route supply/return as a tight pair; keep LED return and charger away from NE.
  - O2: Gate magnetometer use while charging / during LED bursts (firmware).
  - O3: Non-ferromagnetic pusher/switch cap at SW4.
- **Recommended provisional direction:** O1 + O2; characterise on prototype.
- **Reservations involved:** MAG_CLEAR, CHG_CONTACT, REAR_ENV, SW4, VENT, TP, SUP_NE

### X17-GNSS-ALL-HEIGHTS - GNSS radiator "all assembly heights" volume overlaps display and pack

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** no; **gate:** before antenna selection
- **Description:** Read literally, the GNSS reservation (az 346-19, r 20.1-24.5) overlaps the display slab (21.00 mm2) and the pack (21.61 mm2); only r > 22.0-22.25 is free at the battery level.
- **Evidence:**
  - phase1_placement.json reservations[0] scope text
  - Generator overlaps DISPLAY x GNSS_RAD, PACK x GNSS_RAD
- **Options:**
  - O1: Radiator in the case wall / radome beyond R 22.25; feed under display edge only.
  - O2: Move the feed north to r > 21.95 (protected foundation C1420/C1421/R1420: not allowed here).
- **Recommended provisional direction:** O1; antenna supplier data needed.
- **Reservations involved:** GNSS_RAD, DISPLAY, PACK

### X18-PACK-EDGE - Support search windows and battery exit overlap the nominal pack disc

- **Verdict:** NEW; **severity:** LOW; **owner decision:** no; **gate:** before case co-design
- **Description:** SUP_SE, SUP_SW and SUP_NE (support search windows, Z levels MAIN + BATTERY) and BATT_EXIT enter the Ø44 nominal projection (R 22.0) at the BATTERY level: SUP_SE by 2.32 mm (closest point R 19.68), BATT_EXIT by 2.27 mm (R 19.73), SUP_SW by 0.73 mm (R 21.27) and SUP_NE by 0.29 mm (R 21.71, corner (113.5, 83.0); intersection 0.09 mm2, a sliver). Against the tolerance-inclusive pack (R_pack_max 22.15 nominal / 22.25 conservative) the SUP_NE corner penetrates 0.44 / 0.54 mm. No support or boss geometry is approved: the three windows are search regions, so the overlap is a constraint on the later case design, not a built interference. A usable support land must start at R_channel_inner (R_pack_max + c_radial + carrier wall: 23.05 nominal / 23.85 conservative) or be recessed around the pack; of the in-case window areas 14.8 / 17.0 / 10.7 mm2 (SW / SE / NE) 10.8 / 6.1 / 8.9 mm2 remain at the nominal and 6.9 / 2.6 / 6.1 mm2 at the conservative R_channel_inner, and the NE remainder still competes with the NE sector (X15). BATT_EXIT is the pack's own wire-exit zone (entirely inside R_channel_inner) and is resolved by the finished-pack / PCM drawing (SR-BATT-PCM), not by clipping.
- **Evidence:**
  - arch_diagrams.py overlap detector (no area threshold): PACK x BATT_EXIT 2.46, PACK x SUP_SW 0.69, PACK x SUP_SE 6.02, PACK x SUP_NE 0.09 mm2 (BATTERY level)
  - architecture.json pack_edge.results: exact closest approach R 19.68 (SUP_SE), 19.73 (BATT_EXIT), 21.27 (SUP_SW), 21.71 (SUP_NE) against R 22.0
  - zstack.md R_pack_max 22.15 / 22.25 / 22.10; R_channel_inner 23.05 / 23.85 / 22.90
  - phase1_placement.json reservations[6..8] are support search windows (no boss geometry approved)
- **Options:**
  - O1: Clip the three support search windows to r >= R_channel_inner (23.05 nominal / 23.85 conservative); remaining areas are in architecture.json pack_edge.results.
  - O2: Keep a window shape and recess the carrier / pack edge locally at its corner (needs the finished-pack drawing, SR-BATT-PACK); decide at case co-design.
- **Recommended provisional direction:** O1 as the provisional constraint. Disposition: REGISTERED, not suppressed - SUP_NE x PACK is a small sliver at a search-window corner resolved by the same clip as SUP_SW / SUP_SE; no owner decision. Re-open if the NE window is reduced below what X14 / X15 need or if the finished pack adds a lobe near az 40.
- **Reservations involved:** PACK, BATT_EXIT, SUP_SW, SUP_SE, SUP_NE

### X19-BCU-0603 - Two 0603 B.Cu capacitors govern the back zone

- **Verdict:** NEW; **severity:** LOW; **owner decision:** no; **gate:** MAIN placement revision
- **Description:** C901 and C903 (0.95 mm seated) set back_zone = max(web, 0.95 + c_back) + t_insulator = 1.10 mm; the next B.Cu part is 0.60 mm. Re-footprinting only these two as 0402 would give back_zone 0.75 mm (-0.35 at every corner).
- **Evidence:**
  - main_height_map.md B.Cu table: C901 0.95, C903 0.95, others <= 0.6
  - Throw-away tool run: back_zone 0.75 / 0.90 (nominal / thick); T_total 14.15 / 17.58
- **Options:**
  - O1: 0402 equivalents for C901/C903 (value, derating and availability review).
  - O2: Local pocket depth only; web unchanged (no gain).
- **Recommended provisional direction:** O1 at the placement/BOM phase.

### X20-GROWTH-VS-OPTICS - Pack growth / compression must never load the optical stack

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** no; **gate:** before carrier/case freeze
- **Description:** battery_zone is 4.75 / 5.00 / 5.50 mm (thin / nominal / thick); tol_pack_thick, g_axial and c_axial are SUPPLIER/PARAMETRIC. The pack bears on the carrier web above the REAR module; hard stops must route all compression and wrist load around the optical packages.
- **Evidence:**
  - stack_parameters.json g_axial 0.2-0.5 SUPPLIER_DATA_REQUIRED
  - input_register BATT-GROWTH
- **Options:**
  - O1: Carrier ribs / hard stops plus compliant foam above the pack.
- **Recommended provisional direction:** O1; restraint rules from the pack supplier.
- **Reservations involved:** PACK, REAR_ENV

### X21-INGRESS-UNDEFINED - No ingress / water-resistance target is defined

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** YES (OD-WATER); **gate:** before case co-design
- **Description:** Seal count is large (display bond, caseback, pod window, five buttons, vent membrane, charger contacts) and each consumes radial or axial budget. No requirement exists in the register or brief.
- **Evidence:**
  - input_register: no ingress entry
  - PHASE_BRIEF.md section 5-E (sealing)
- **Options:**
  - O1: Owner sets splash / swim / depth class; seal architecture follows.
- **Recommended provisional direction:** Owner decision OD-WATER before case co-design.

### X22-UNMODELLED-Z - Several Z items are not in the tool stack

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** no; **gate:** next gate
- **Description:** Window retention adhesive/flange, barrier-gasket compression, caseback gasket stack, carrier hard-stop ribs and FPC stiffener have no layer; only c_optics (0.05-0.2) can absorb them.
- **Evidence:**
  - stack_parameters.json z_layers (12 layers)
- **Options:**
  - O1: Add named budget lines at the next gate.
- **Recommended provisional direction:** O1.

### X23-WINDOW-CROSSTALK - Residual crosstalk through a continuous optical window is unverified

- **Verdict:** NEW; **severity:** MEDIUM; **owner decision:** no; **gate:** before window / pod-insert concept freeze (G3) and any optical-isolation claim
- **Description:** The baseline pod has black barrier walls that end at the window inner face (section E, rear_module_concept.svg), leaving one continuous transparent window above all cells. Light can travel laterally inside the window (and across its two surfaces) from emitter cells to detector cells without going through skin; an ink mask on the inner face only attenuates part of that path and its effect is not demonstrated. The earlier claim that no non-skin optical path exists is withdrawn. The magnitude depends on window material and thickness (0.3-0.8 mm, PARAMETRIC), surface finish, adhesive and mask geometry, none of which is fixed.
- **Evidence:**
  - architecture.json rear_module.section_barrier_frac / unmodelled_z_items: barriers end at the optics-zone top; window layer is a single plane in rear_module_concept.svg
  - zstack.md layer window 0.3 / 0.5 / 0.8 mm continuous across the pod envelope
  - No prototype, supplier or simulation data in the repository (architecture intent, PHASE_BRIEF 8)
- **Options:**
  - O1: W0 baseline mask: one window, walls to the inner face, ink mask (cheapest; unverified).
  - O2: W1 full-depth opaque isolation: walls through the window thickness (segmented / insert-moulded window; more parts, window area and Z budget impact).
  - O3: W2 separate small windows in an opaque frame (intended to give the strongest isolation, unverified; more seals and parts; see X21).
- **Recommended provisional direction:** Plan MG-WINDOW-XTALK (rear_module.window_isolation) on the first prototype comparing W0 against W1/W2 with the W-ref control; keep the pod frame and carrier ribs compatible with W1/W2 meanwhile; no isolation level is claimed in this package.
- **Reservations involved:** REAR_ENV

### X24-DISPLAY-LAND - Display support land competes with the display-FPC fold, rim parts and every F.Cu edge crossing

- **Verdict:** NEW; **severity:** HIGH; **owner decision:** YES (OD-COVER, OD-WATER); **gate:** before case co-design (G3); land thickness over U4 before MAIN placement revision
- **Description:** The rigid display needs a case support / bond land behind its rim (DISP_LAND: R 20.45-24.05 with the widest planning land, top t_land 0.3-0.8 mm of the front gap). It occupies the same Z band as the display-FPC fold (DISP_FPC, az 269-295, up to R 22.65, fold 0.3-0.6 thick), so the land must be interrupted over at least that arc (about 10 mm of unsupported rim) unless the display supplier permits bonding to the fold stiffener. Over U4 (BMP585, 1.96 mm, courtyard to R 22.23) the land leaves 0.24 mm nominal, -0.06 mm conservative and 0.44 mm optimistic headroom: t_land must stay <= 0.74 mm there or the land is relieved over U4 (elsewhere the next rim part L203 1.25 mm leaves 0.65-1.15 mm). Every F.Cu edge crossing (XF-J1501, XC-J202, XB-J201, XL-LRA) passes under the land, whose underside caps the conductor at h_max 2.03 / 1.50 / 2.50 mm above F.Cu and so caps how far inboard a bend can start (section G). The ring also overlaps the GNSS / BLE / Wi-Fi radiator volumes (land material near radiators), the barometer vent route, the five button windows, the support search windows (both are case features: a shared design), MAG_CLEAR (non-ferromagnetic land near the BMM350) and the TP13xx access circles (access happens in build state S1 without the case, so there is no service conflict).
- **Evidence:**
  - PHASE_BRIEF.md section 9 L1 (lead finding); input_register DISPLAY-MOD (43.9 rigid module, POL 38.9) and DISPLAY-FPC (fold up to 0.7 beyond the outline, stiffener T0.15/T0.2)
  - edge_crossings.display_land: w_land 0.5 / 1.0 / 1.5, t_land 0.3 / 0.5 / 0.8 (PARAMETRIC LOW placeholders; w_land max < 2.5 mm POL border, checked)
  - edge_crossings.results.land_vs_rim_parts: U4 1.96 -> margin 0.24 / -0.06 / 0.44; next L203 1.25 -> 0.95 / 0.65 / 1.15 (front_gap - c_front - h - t_land; c_front cancels because front_gap = H_F + c_front)
  - edge_crossings.results.budget h_max 2.03 / 1.50 / 2.50 (front_gap - t_land - c_fpc - t_fpc)
  - Overlap register (MAIN level): DISP_FPC x DISP_LAND 21.51, VENT x DISP_LAND 41.94, MAG_CLEAR x DISP_LAND 63.65, GNSS_RAD x DISP_LAND 39.30, SW1-SW5 x DISP_LAND 17.99 each, BATT_TAIL x DISP_LAND 22.73 mm2 and the other pairs listed in section 12
- **Options:**
  - O1: Rear support land (DISP_LAND), interrupted at the fold, relieved or <= 0.74 mm thick over U4, non-conductive near radiators and non-ferromagnetic near the BMM350.
  - O2: Front lip over the display border instead (OD-COVER: +0.5 mm t_front_extra); removes the ledge from the front gap.
  - O3: Discrete support pads plus a bond to the fold stiffener / J1 region only (needs SR-DISPLAY-LAND).
- **Recommended provisional direction:** O1 as the working assumption for G2/G3 with the fold interruption and the U4 relief; decide O1 against O2 together with OD-COVER (and OD-WATER if the land is also the front seal); issue SR-DISPLAY-LAND.
- **Reservations involved:** DISP_LAND, DISP_FPC, GNSS_RAD, BLE_RAD, WIFI_RAD, J1501, J201, J202, BATT_EXIT, SUP_SW, SUP_SE, SUP_NE, TP, VENT, SW1, SW2, SW3, SW4, SW5, MAG_CLEAR, FPC_CORR, CHG_RISER, CHG_APPROACH, BATT_TAIL

### Owner decisions required

| ID | Question | Blocks | Status |
|---|---|---|---|
| OD-COVER | Exterior cover strategy: display integral glass flush (t_front_extra 0) or an added sapphire/bezel lip (up to +0.5 mm)? | T_total budget (+0.5), assembly order V1/V2, front seal, display support land versus front lip (X24) | OWNER DECISION REQUIRED |
| OD-WATER | Water/ingress resistance target (class, depth, test)? | seal architecture, radial and axial budgets, whether the display land is the front seal (X24) | OWNER DECISION REQUIRED |
| OD-U8 | May the GNSS part U8 (protected foundation) be replaced or moved to recover up to 0.74 mm? | front gap, T_total | OWNER DECISION REQUIRED (touches frozen foundation) |
| OD-DEVACCESS | Is post-closure SWD/TP access required, and may J1301/TP13xx be relocated in a later placement phase? | assembly/service sequence, MAIN placement | OWNER DECISION REQUIRED |
| OD-J202 | May the J202 charger entry (approved placement) move toward the contact block, or is the long harness accepted? | charger path, west-sector crowding, west charger riser XC-J202 | OWNER DECISION REQUIRED |
| OD-CONN-SIDE | May J1501/J201 move to B.Cu or an edge feature be added to MAIN in the placement/outline phases? | edge crossings, FPC radial budget | OWNER DECISION REQUIRED |
| OD-REAR-SIDED | Single-sided REAR (baseline) or double-sided REAR / hot-bar FPC tail, given the stack, pod and service trade? | REAR placement, T_total (+0.85 nominal-class), J1502 selection | OWNER DECISION REQUIRED |

## 13. Unresolved blockers and supplier / owner requests

Each request names who, what, what it affects, the hard gate and the parametric stand-in used until the data arrive. Work continues reversibly
with the stand-in until the gate.

| ID | Register id | Who | What | Affects | Hard gate | Parametric stand-in |
|---|---|---|---|---|---|---|
| SR-DISPLAY-FPC | DISPLAY-FPC | Display supplier (ZC-A1D43W-046) | Folded-FPC envelope drawing: thickness, fold exit direction/width, plug location and alignment float, bend radius, border/ink window for ALS | front gap (local), west corridor, J1 blind mate, ALS aperture, SW1/SW2 position | before case/outline co-design | t_display_fpc_fold 0.3-0.6; fold footprint +0.7 beyond outline |
| SR-DISPLAY-LAND | DISPLAY-MOD | Display supplier (ZC-A1D43W-046) | Permitted rear support / bond region under the rim (minimum and maximum land width), flatness and allowed pressure, whether the rear border is free of FPC / stiffener, bond material guidance | display support land DISP_LAND (w_land, t_land), front seal concept, edge-crossing land ceiling | before case co-design (G3) | w_land 0.5-1.5 (< 2.5 POL border); t_land 0.3-0.8 |
| SR-BATT-PACK | BATT-PACK | Battery supplier (LPR454440) | Finished protected-pack drawing: max Ø and thickness, tolerance, edge seal, tape/insulation | battery_zone, R_pack_max, annulus | before final outline/case | tol_pack_thick 0-0.3; tol_pack_dia 0.2-0.5 |
| SR-BATT-PCM | BATT-PCM | Battery supplier | PCM envelope and location, tabs, wire/FPC exit, mating connector; tail exit azimuth (preferably at the J201 azimuth 181-197) and tail thickness / bend radius | J201 MPN, carrier pockets, battery tail path, battery tail annulus run (BATT_TAIL, XB-J201) | before J201 MPN and carrier design | BATT_EXIT window [81.5,112.2,84.5,113.2] |
| SR-BATT-GROWTH | BATT-GROWTH | Battery supplier | Permitted swelling/growth allowance and restraint/compression limits | battery_zone, hard stops, optical load path | before carrier/case freeze | g_axial 0.2-0.5; c_axial 0.05-0.2 |
| SR-BATT-NTC | BATT-NTC | Battery supplier | NTC presence, curve and placement (PMIC needs NTC on J201.2) | J201 pin map, PMIC config | before J201 MPN | none (BAT_NTC pin reserved) |
| SR-FPC-MECH | FPC-MECH | Connector and FPC fabricator | J1501/J1502 MPN, pitch, rating, latch/mated height, bend radius, stiffener, length; FPC exit height above F.Cu at the mouth and mouth position relative to the footprint (edge-crossing bend start) | edge wrap, rear_inner, lower web, GND/VLED conductor width, bend start / J1501 mouth radius | before final outline / REAR placement freeze | R_bend_min 0.6-2.0; t_fpc 0.1-0.2; connector run 4.6; exit height >= 0.10 mm and mouth R <= 22.53 required at nominal (edge_crossings) |
| SR-CHG-MECH | CHG-MECH | Contact/dock supplier | Contact geometry, metallurgy, feedthrough seal, dock force/travel, keying, protection silicon; harness construction (flat flex or wires), conductor thickness and width, bend radius, current rating, exit height at J202 | contact block envelope, caseback aperture, ESD entry, charger riser radial budget (XC-J202) | before contact-module selection | block az 80-100, r 17.5-24 placeholder; riser slot az 249-259 (CHG_RISER); flat-flex stand-in t 0.1-0.2, R_bend 0.6-2.0; conductor <= 0.80 mm thick beside the pack (nominal) |
| SR-LRA | LRA | LRA supplier (owner selects) | Actuator envelope and mounting method; lead exit and mounting (decides whether the XL-LRA edge crossing exists) | LRA pocket, south sector | before perimeter freeze | pocket az 165-195, r 12.65-22 (REAR) |
| SR-BUTTONS | BUTTONS | Switch/pusher supplier (owner selects) | Switch footprint, height, mechanism and seal | SW1-SW5 windows, wall thickness, west corridor | before perimeter freeze | half-width 7.5 deg, r 21-25.25 placeholder |
| SR-ANTENNAS | ANTENNAS | Antenna supplier / RF consultant | Radiator concepts and keep-outs for GNSS, BLE, Wi-Fi, diplexer U10 | radome volumes, display shadowing, caseback metal | before case co-design | reservation rectangles as published |
| SR-SFH4053B-DS | SFH4053B-DS | OSRAM / ams OSRAM | SFH 4053B datasheet: seated height, optical axis, radiant pattern | optics_zone, D405-D407 placement | before REAR optical placement | h_optics_max 0.7-0.85 (assumed) |
| SR-MAX86141-HEIGHT | (package/stack input) | Analog Devices | MAX86141 WLP package outline 21-100134 (seated height) | optics_zone | before REAR optical placement | h_optics_max 0.7-0.85 (assumed) |
| SR-TAGCONNECT | (package/stack input) | Tag-Connect | TC2030-IDC-NL probe engagement volume and retaining clip envelope | J1301 access volume, assembly state S1 | before development fixture design | vertical volume above F.Cu as a labelled reservation |
| SR-J1-ALIGN | (package/stack input) | OCN (OK-23GF/GM-04) | Blind-mate float/lead-in, insertion force and re-mating guidance | V1 assembly (Z-push mating), 50-cycle budget | before assembly order is fixed | none; V1 flagged risk |

Additional blockers that are not supplier data: the owner decisions above, the SFH4053B datasheet source gap (blocks D405-D407 quantitative geometry
only), and the absence of any approved REAR outline, stackup or rules.

## 14. What remains intentionally unfrozen

- REAR outline, stackup, placement, optical spacing, barrier design, window isolation concept (W0/W1/W2, X23), window material/thickness
- single- vs double-sided REAR; J1502 face/MPN/orientation; J1501 MPN/pitch/orientation
- h_pod, T_body, caseback plane, pod footprint, window retention
- case outline, wall, bosses, screws, gaskets, ingress class
- display support land (width, thickness, interruptions, material) and the front-lip alternative
- MAIN final outline (R 23 is a development envelope), supports, notches
- cover strategy (glass exterior vs lip), assembly order V1/V2
- battery carrier geometry, pockets, restraint, wire exit, PCM location
- charger riser slot (az 249-259), battery tail annulus run, J1501 mouth radius and every edge-crossing exit height
- charger contact block geometry, seal, dock, key; J202 location
- buttons, LRA, vent, ALS aperture, antennas and radomes
- development access strategy for SWD/TP
- all PARAMETRIC ranges in section 11

Frozen and untouched: the ten invariants in `inputs/input_register.json` (MAIN 202 / 359 / 184 / 18; REAR 46 / 44 / 44 / 2; 44 transferred refs; 75
protected foundation footprints; 24 positions / 13 nets; REAR-local PD_IN / PD_GND / VREF / cathodes / mux selects; TPS631000 on MAIN; charger contacts
and no charger-positive in the sensor FPC; LPR454440; MAIN Ø46 development envelope; no watch-side permanent magnet).

## 15. Next engineering gate

**Recommendation: G1 first.** (1) Independent review of this package and of `architecture.json`; (2) owner answers to OD-COVER, OD-REAR-SIDED and
OD-WATER (the three that change the stack and the assembly order) and, at least as a direction, OD-DEVACCESS, OD-J202, OD-CONN-SIDE and OD-U8;
(3) issue the supplier requests of section 13. Then run G2 (REAR optical + guarded-analog placement study) and G3 (case + final MAIN outline
co-design) in parallel where their entry criteria are met. All work stays reversible until outline freeze.

- **G1 entry:** independent review of this package passes; OD-COVER, OD-REAR-SIDED, OD-WATER answered; supplier requests SR-* issued
- **G2 entry:** SR-SFH4053B-DS and SR-MAX86141-HEIGHT closed; SR-FPC-MECH closed (J1502 face/height known); OD-REAR-SIDED answered; h_pod trial plan agreed; J1501 mouth radius <= 22.53 and exit height known from SR-FPC-MECH (edge crossing XF-J1501)
- **G3 entry:** SR-BATT-PACK, SR-BATT-PCM, SR-BATT-GROWTH closed; SR-DISPLAY-LAND closed (display support land) and OD-COVER answered for land versus lip; SR-DISPLAY-FPC closed; OD-COVER, OD-WATER, OD-DEVACCESS answered; LRA, button and antenna selections made; MG-WINDOW-XTALK result (X23) or an explicit owner acceptance of the unverified W0 baseline

Exit criteria for G1: every conflict has an owner/reviewer disposition; every HIGH item has either a closed datum or an agreed stand-in range.

---

## Appendix: reviewer challenge map

| Challenge | Where addressed |
|---|---|
| Z-stack feasibility | section A scenarios and verdict; C1, C9, X10, X19, X22 |
| Battery / FPC interference | C3, X13, X24; section G edge-crossing derivation and radial table (sensor FPC, charger riser, battery tail, LRA leads); section C carrier wall and battery tail |
| REAR support | section D support / hard stops; X14, X20 |
| Optical crosstalk architecture | section E: barriers end at the window inner face, residual window path unverified (X23, MG-WINDOW-XTALK), spacing study; X10, X11 |
| Thermal path | section F; X16 for heat/field contamination of other sensors |
| Sealing | section E sealing; section H face seal; X21 |
| Charger separation | section H; C4; frozen: no charger-positive in the FPC (checked by the generator) |
| SWD / assembly / service sequence | section J; C2 |
| RF / vent / button / LRA reservations | section I; C5-C8, X15, X17, X24 (display land against radiators, vent and buttons) |
| Hidden dependence on unknown supplier dimensions | X10 and every SR-* request (incl. exit height / mouth radius SR-FPC-MECH, harness SR-CHG-MECH, display land SR-DISPLAY-LAND); `arch_diagrams.py check` lists all SUPPLIER ids and fails on any numeric value that is neither validated against a source nor an exempted placeholder |
| Accidental violation of frozen electrical boundaries | `arch_diagrams.py check` verifies 24 positions / 13 nets, no REAR-local or charger net in the sensor FPC, battery LPR454440, invariants copied verbatim |
