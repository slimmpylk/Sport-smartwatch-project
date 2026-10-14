# Rev-A multi-board mechanical stack and rear sensor module architecture

**G3 status: G3 CONDITIONAL — SUPPLIER/MEASUREMENT GATES OPEN.** Recommended study topology: G3-B-S14; all nominal hard checks pass. Supplier/measurement gates remain open; G4 and KiCad implementation are not authorized.

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
| Does the stack meet 14.0-15.5 mm (T_total)? | **NO — G1 verdict: THICKNESS OWNER DECISION REQUIRED.** G1 baseline (OD-COVER + OD-REAR-SIDED integrated): nominal 16.75 mm, RSS 17.20 mm, linear worst 18.41 mm; tool thick corner 19.53 mm. No thickness-recovery scenario is credibly <= 15.5 mm (section G1; thinnest all-credible-lever scenario G1-K2 = 16.08 mm nominal / 16.52 RSS). |
| What governs the nominal stack? | battery_zone 5.00, front_gap 2.85 (U8 MAX-F10S), cover 1.25 + cover_bond 0.25 (OD-COVER), display 2.05, rear_inner 0.90 (OD-REAR-SIDED, double-sided), back_zone 1.10 (C901/C903, 0603 on B.Cu), optics 0.85, window 0.50. |
| Controllable levers (G1) | C901/C903 as 0402 (-0.30, credible later task), REAR inner-side flex tail (-0.10) / tail + 0201 cap (-0.37), combinations (G1-K2 -0.67); NOT levers: single-sided REAR (OD-REAR-SIDED decided double-sided), U8 relocation (geometry excludes an F.Cu escape; B.Cu thickens), J1501/J201 to B.Cu (inside the pack projection), h_pod (T_total does not depend on it). |
| Radial / FPC | The tool 180-degree edge wrap fails nominal (-0.47). A 2 x 90-degree out-and-down is bounded by the derived bend geometry: nominal margin -0.47 (flat exit) to +0.68 (exit at the display-land ceiling), positive only with the J1501 mouth at R <= 22.53 and an exit >= 0.10 mm above F.Cu. **No edge crossing passes the conservative corner** (>= 0.95 mm short). The charger riser (XC-J202) and battery tail (XB-J201) share this budget (section G). |
| Largest unknowns | SFH4053B and MAX86141 seated heights (X10), finished-pack drawing, display-FPC fold drawing and permitted display support region (SR-DISPLAY-LAND), FPC connector MPN / height / exit height, charger harness construction, LRA / buttons / antennas. |
| Next gate | G2 acceptance/review first; then separately authorized G3 REAR optical/guarded-analog study, G4 case/outline co-design and later KiCad allocation implementation (section 15). |

---

## A. Z-stack (cover to wrist)

**KNOWN.** Target (owner, 2026-10-10): 14.0-15.5 mm applies to **T_total** = front-most exterior surface (G1: the separate cover lens, OD-COVER) to the deepest normal wrist-facing
surface of the rear optical pod (PHASE_BRIEF 1a; `stack_parameters.json` conventions). T_body = T_total - h_pod; T_total does not depend on h_pod.
Display module 2.05 +/-0.1 (ZC-A1D43W-046 spec pp4-5). MAIN 0.8 mm, 8 Cu layers (live PCB). LPR454440 nominal cell 4.5 mm (catalog).
H_F_under_display 2.7 mm (U8 MAX-F10S, u-blox table), runner-up 1.96 mm (U4 BMP585); H_B_in_battery 0.95 mm (C901, PARAMETRIC typical 0603).

**Layers (quoted from `generated/zstack.md`, mm)**

| Layer | thin | nominal | thick | Class of the governing term |
|---|---:|---:|---:|---|
| cover | 1.0 | 1.25 | 1.70 | PARAMETRIC LOW (OD-COVER; 5 ATM plate sizing, conservative upward grid rounding, SR-COVER-LENS) |
| cover_bond | 0.1 | 0.25 | 0.4 | PARAMETRIC LOW (air gap 0.25 nominal / OCA 0.15 class) |
| display | 1.95 | 2.05 | 2.15 | KNOWN |
| front_gap | 2.8 | 2.85 | 3.0 | KNOWN part height (U8) + PARAMETRIC clearance |
| main_pcb | 0.72 | 0.8 | 0.88 | KNOWN nominal, PARAMETRIC tolerance |
| back_zone | 1.03 | 1.1 | 1.25 | PARAMETRIC (no passive MPN) |
| battery_zone | 4.75 | 5.0 | 5.5 | KNOWN nominal cell + SUPPLIER_DATA_REQUIRED tolerance / growth |
| lower_web | 0.3 | 0.4 | 0.6 | PARAMETRIC LOW |
| rear_inner | 0.65 | 0.9 | 1.2 | SUPPLIER_DATA_REQUIRED (OD-REAR-SIDED double-sided REAR; J1502 mated height, SR-FPC-MECH) |
| rear_pcb | 0.6 | 0.8 | 1.0 | PARAMETRIC (staging file 1.6 mm / 2-layer is a placeholder) |
| optics_zone | 0.75 | 0.85 | 1.05 | KNOWN for MAX30208 / SFH7018A / SFH2703; **assumed** for SFH4053B and MAX86141 (X10) |
| window | 0.3 | 0.5 | 0.8 | PARAMETRIC LOW (material undecided) |
| **T_total** | **14.95** | **16.75** | **19.53** | G1 baseline = OD-COVER + OD-REAR-SIDED integrated |

Tool margins to 14.0 / 15.5: thin +0.95 / +0.55; nominal +2.75 / -1.25; thick +5.53 / -4.03. T_body nominal for h_pod 0 / 0.5 / 0.8 / 1.0 / 1.5 =
16.75 / 16.25 / 15.95 / 15.75 / 15.25 mm (h_pod is PARAMETRIC LOW and cannot be frozen without wrist/strap trials). Tool RSS (informational):
primary 17.598 mm, secondary 17.529 mm; the primary RSS treats design variables (window, REAR PCB, lower web) as tolerances.

**Distinction between RSS metrics and planning envelope:**
- **G1 scenario RSS (17.195 mm):** scenario-specific tolerance policy evaluating actual single-term stack responses for the G1 baseline (G1-S4: nominal 16.750 mm, RSS 17.195 mm, linear worst 18.410 mm); authoritative for the G1 thickness decision.
- **Broad planning RSS (17.598 mm):** broad max-minus-nominal parameter ranges across the model (secondary nominal-active RSS: 17.529 mm), including wider planning ranges and inactive alternatives; an intentionally conservative planning metric.
- **All-maximum planning envelope (19.530 mm):** separate all-maximum planning envelope (linear sum of all thick-corner parameters). These are distinct metrics, not competing values.

**Governing layers.** battery_zone is 30 % of the nominal stack (5.0 / 16.75), front_gap 17 %, display 12 %, back_zone 7 %. Largest contributors to
thick - nominal (tool): battery_zone 0.5, cover 0.45, window 0.3.

**Scenarios (brief candidate 9, G1-relative).** The G1 baseline (S4: separate cover + double-sided REAR, owner decisions 2026-10-11) IS the tool nominal
16.75 mm. Rows are G1-relative configurations: `cover` adds/removes the whole cover stack (t_cover + t_cover_bond, +1.50 nominal / +0.60 tolerance: t_cover 0.45 sizing-bound span + t_cover_bond 0.15),
`double_sided_rear` adds/removes the whole inner-side stack (h_rear_inner + c_rear_inner, +0.90 / +0.30). The tolerance terms are the nominal-to-max
deltas of t_display 0.10, c_front 0.15, t_main 0.08, c_back 0.10, t_insulator 0.05, tol_pack_thick 0.20, g_axial 0.20, c_axial 0.10,
h_optics_max 0.10, c_optics 0.10: 1.18 mm linear, 0.402 mm RSS. Arithmetic: scenario = (tool nominal - cover stack - inner stack) + design deltas +
tolerance stack. Design deltas from the tool layers: window 0.8 +0.3; REAR PCB 1.0 +0.2; lower web 0.6 +0.2. The inner stack carries +0.90 nominal / +0.30 tolerance.

| Scenario | Design choices | T nominal tol. | T RSS tol. | T linear worst | <= 15.5 (nominal / RSS / linear) |
|---|---|---:|---:|---:|---|
| S1 | no separate cover, single-sided REAR (pre-G1 reference) | 14.35 | 14.75 | 15.53 | yes / yes / **no** |
| S2 | double-sided REAR inner stack only, no separate cover | 15.25 | 15.75 | 16.73 | yes / no / **no** |
| S3 | separate cover only, single-sided REAR | 15.85 | 16.57 | 17.63 | no / no / **no** |
| S4 | **G1 baseline: cover (OD-COVER) + double-sided REAR (OD-REAR-SIDED)** | 16.75 | 17.53 | 18.83 | no / no / **no** |
| S5 | no cover, single-sided, window 0.8, REAR PCB 1.0, web 0.6 | 15.05 | 15.45 | 16.23 | yes / yes / **no** |
| S6 | all design choices present and maximal (reproduces the tool thick corner) | 17.45 | 18.23 | 19.53 | no / no / **no** |

The G1 thickness-recovery scenarios (levers, cover ranges, combinations) are computed by `tools/g1_scenarios.py` and reported in section **G1** below
and `generated/g1_scenarios.md`; the two tables use different tolerance policies (this table: corner-based design choices; G1: per-scenario governing
part tolerances), so their S4/G1-S4 rows differ deliberately.

S6 reproduces the tool thick corner (19.53), which is the arithmetic cross-check that the decomposition is complete.

**What must change (G1, current).** The G1 baseline is 16.75 mm nominal (1.25 mm over the 15.5 mm upper target). The G1 thickness-recovery study
(section G1, `tools/g1_scenarios.py`) evaluated every credible lever and their combinations: the thinnest scenario using only credible later-task
levers is G1-K2 (C901/C903 as 0402 + REAR inner-side flex tail with 0201 passives) at 16.08 mm nominal / 16.52 mm RSS - still 0.58 mm over at
nominal. The only sub-15.5-nominal scenario (G1-K4, 15.18 mm) needs a supplier-gated carrier-floor pocket lever and an owner-gated laminated
cover and still fails its RSS (15.67 mm). Per the G1 stop rule the verdict is **THICKNESS OWNER DECISION REQUIRED**: the owner decides the
thickness target versus the credible levers; no requirement is weakened. *To stay at or above 14.0 mm:* the thin corner is 14.95 mm (+0.95).

**Honest feasibility verdict (G1, current).** Nominal: NOT feasible within 15.5 mm (16.75 mm baseline; best credible-lever scenario 16.08 mm).
Statistical (RSS): not feasible (17.20 mm baseline; 16.52 mm best). Worst case (linear): not feasible (18.41 mm baseline). The verdict depends on
the unverified assumption that SFH4053B and MAX86141 are not taller than 0.75 mm (X10), on the unselected passives (no MPN), and on pack
tolerance/growth numbers that are SUPPLIER_DATA_REQUIRED.

*Historical (pre-G1, retained for traceability - superseded by the G1 baseline above):* on the pre-G1 stack (nominal 14.5 mm) the target was met
at nominal by S1/S2/S3/S5 and by RSS only by S1/S3, and no scenario met 15.5 mm with linear worst-case tolerances (best S1: 15.78 mm); with
C901/C903 as 0402 (-0.35) S1 linear became 15.43 mm. Lever arithmetic was cross-checked once on a throw-away copy of the tool inputs outside
the repository (T_total nominal 13.76 / thick 17.19 with U8 set to zero height; back_zone 0.75 / 0.90 and T_total 14.15 / 17.58 with
C901/C903 as 0402); no repository file was changed.

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
13.4 / 18.4 / 24.4 mm, so area governs. Double-sided (G1, OD-REAR-SIDED 2026-10-11): the skin-facing (optical) group is the larger face group -
optical 167.33 mm2 (frozen: emitters, PDs, U12/U13 AFEs, U402-U407 muxes, NT401/NT402, U6, C802) vs inner 35.68 mm2 (J1502 + passives) - divided by eta
gives Ø 20.5 / 23.2 / 27.1 mm (opt / nom / cons; architecture.json rear_module.envelope_results, recomputed by arch_diagrams.py check), and the span
limit gives 24.4 at the conservative corner; the area-derived diameter 27.13 mm exceeds the 24.4 mm span, so the area governs and the conservative envelope is ≈ 27.1 mm. **Outline class: a compact rounded envelope of about Ø25 mm (22-29), not a
full-battery-size board; far inside the Ø44 pack projection.** The values are sizing, not an outline. (Pre-G1 text quoted inner 103.0 vs optical
100.0 mm2 and Ø 16.4 / 18.8 / 22.4 - superseded by the corrected side allocation.)

**Orientation and transform (proposed).** FPC attach edge at south (az ~167-180, toward J1501); MAX30208 tongue at az ~255 (away from AFEs, FPC edge and
the east charger block); optical cluster at the centre; AFE/mux band on the south half. Transform REAR frame to assembly frame (front view):
x_a = x_c - (x_r - x_rc), y_a = y_c + (y_r - y_rc): the board is turned like a book page about the north-south axis; its optical face (F.Cu in the
current single-sided file) has normal +Z (toward the wrist). Viewed from the wrist, north is up and east is left. J1502 position 1 must be labelled on
the manufacturer mating-face drawing, never read from a mirrored B-side view (interface contract).

**Component-side strategy.** *Pre-G1 comparison (historical - the single-sided column is NOT the current baseline):*

| | Single-sided (pre-G1 S1, superseded) | Double-sided (G1 baseline, OD-REAR-SIDED 2026-10-11) |
|---|---|---|
| rear_inner | 0 | +0.90 nominal (h_rear_inner 0.8 + c_rear_inner 0.1; 1.20 thick), carries c_rear_inner tolerance |
| Pod footprint | must cover every optical-face part: envelope Ø 22-29 | covers the frozen optical group (Ø 20.5-27.1) |
| AFE-to-PD routing | same-side, guarded, short | AFEs / muxes / PD_GND net ties stay on the skin-facing optical face (frozen sensitive PPG/analog geometry, NOT relocated), guarded routing; passives + J1502 on the inner face |
| J1502 | optical face inside the pod, or edge FPC | inner face (costs its mated height + c_rear_inner) |
| Reviewable now | yes | needs J1502 height (SR-FPC-MECH) and pod trial |

Rationale (current, G1): interior depth from the optical face to the skin plane is optics_zone + window = 1.35 mm nominal while the caseback plane is
h_pod (0.8 nominal) above the skin plane, leaving 0.55 mm minus the caseback wall outside the pod; 0.6-0.75 mm parts on the optical face cannot sit there.
*Pre-G1* this implied a single-sided pod as large as the envelope (X11); OD-REAR-SIDED (2026-10-11) decided double-sided, so the pod covers the frozen
optical group and the inner side carries J1502 + passives at rear_inner +0.90 mm nominal.

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
face-sealed to the caseback aperture (pod insert), or a monolithic caseback window; the ingress target is 5 ATM / swim-capable (OD-WATER
2026-10-11; sealing-stack design and qualification are G1/G3 work, see section G1.4). **Hard stops.** Carrier
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

<!-- G2 NOTE G -->
Current allocation, fold and supplier limits are in section G2. The following G1 geometry is retained for comparison; the G2 sensor groove is inside the lower web, and the charger/haptic perimeter channels are below it. No raw analog or charger-positive signal enters the sensor FPC.
<!-- END G2 NOTE -->

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

<!-- G2 NOTE H -->
Section G2 governs the current charger option trade. The separate contact feedthrough remains sealed independently. The selected perimeter channel lies below the intact lower web outside the REAR outline; the original co-planar crossing proposal is superseded.
<!-- END G2 NOTE -->

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

<!-- G2 NOTE I -->
Current supplemental reservations are in architecture.json g2.reservations and generated/g2_allocation.svg. Existing reservations below remain the comparison baseline. New regions are provisional and do not place components or freeze a case.
<!-- END G2 NOTE -->

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
| REAR_ENV | REAR rigid board + pod envelope (max envelope = single-sided nominal; G1 baseline double-sided shrinks it, X11) | 12:00-12:00 | 0.0-360.0 | 0.00-12.65 | REAR | PARAMETRIC | architecture.json rear_module.envelope_results (derivation over live REAR courtyards) |
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

<!-- G2 NOTE J -->
Use the S0–S3 procedure in section G2 for the current allocation. Battery isolation precedes development remating; supplier/fixture service constraints remain open. Earlier assembly variants below are historical alternatives.
<!-- END G2 NOTE -->

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
| D02 | T_total thin / nominal / thick | thin 14.95, nominal 16.75, thick 19.53 | mm | PARAMETRIC | MEDIUM | generated/zstack.json corners (G1 baseline: OD-COVER + OD-REAR-SIDED integrated) |
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
| D14 | h_rear_inner (double-sided REAR inner face, OD-REAR-SIDED) | min 0.6, nom 0.8, max 1.0 | mm | SUPPLIER_DATA_REQUIRED | LOW | stack_parameters.json (J1502 mated-height class, SR-FPC-MECH) |
| D15 | optics_zone | h_optics_max min 0.7, nom 0.75, max 0.85, c_optics min 0.05, nom 0.1, max 0.2 | mm | KNOWN | MEDIUM | h_optics_max anchored on MAX30208 0.75 and SFH7018A/2703 0.6+/-0.1 (stack_parameters.json); SFH4053B/MAX86141 assumed (X10) |
| D16 | t_window | min 0.3, nom 0.5, max 0.8 | mm | PARAMETRIC | LOW | stack_parameters.json; material undecided |
| D17 | h_pod sweep | 0.0 / 0.5 / 0.8 / 1.0 / 1.5 | mm | PARAMETRIC | LOW | stack_parameters.json; needs wrist/strap trials |
| D18 | R_main / R_display / R_pol | 23.0 / 21.95 / 19.45 | mm | KNOWN | HIGH | input_register MAIN-OUTLINE, DISPLAY-MOD |
| D19 | R_case_inner nominal / conservative / optimistic | 24.05 / 23.4 / 24.5 | mm | PARAMETRIC | LOW | zstack.json radial |
| D20 | R_pack_max nominal / conservative | 22.15 / 22.25 | mm | SUPPLIER_DATA_REQUIRED | LOW | zstack.json radial; tol_pack_dia SUPPLIER |
| D21 | Edge-crossing / FPC out-and-down margin, exit at the land ceiling (upper bound) nominal / conservative / optimistic | 0.68 / -0.95 / 1.3 | mm | PARAMETRIC | LOW | edge_crossings.results.budget margin_at_h_max_mm (geometric derivation on zstack.json radial corners + display_land ranges) |
| D22 | REAR parts courtyard area | 203.01 | mm2 | KNOWN | MEDIUM | main_height_map.json rear_footprints (library courtyards; 44 refs) |
| D23 | REAR envelope diameter single-sided opt / nom / cons | optimistic 22.4, nominal 25.3, conservative 29.4 | mm | PARAMETRIC | LOW | rear_module.envelope_derivation |
| D24 | REAR envelope diameter double-sided opt / nom / cons (G1 baseline, OD-REAR-SIDED) | optimistic 20.5, nominal 23.2, conservative 27.1 | mm | PARAMETRIC | LOW | rear_module.envelope_derivation |
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

<!-- G2 NOTE 12 -->
Each conflict now has one current g2_status and g2_evidence; see the generated G2 conflict table. G1 statuses below preserve history and do not override G2.
<!-- END G2 NOTE -->

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
| X21-INGRESS-UNDEFINED | - | REFINED | MEDIUM | **YES** (OD-WATER, answered 2026-10-11) | Ingress target answered (5 ATM / swim-capable); sealing-stack design and qualification still undefined |
| X22-UNMODELLED-Z | - | NEW | MEDIUM | no | Several Z items are not in the tool stack |
| X23-WINDOW-CROSSTALK | - | NEW | MEDIUM | no | Residual crosstalk through a continuous optical window is unverified |
| X24-DISPLAY-LAND | - | NEW | HIGH | **YES** (OD-COVER, OD-WATER) | Display support land competes with the display-FPC fold, rim parts and every F.Cu edge crossing |
| X25-COVER-CASE-FIT | - | NEW (G1) | MEDIUM | no | Cover free span + bond/seal land + bezel wall vs the provisional case inner radius (G1 integration finding, see section G1) |

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
- **Description:** The gap between the rigid display rear plane and MAIN F.Cu is set by one part: U8 (2.7 mm max, at (100,86), r 14.0, fully under the display). The runner-up is U4 BMP585 at 1.96 mm. front_gap is 2.85 mm of the 16.75 mm nominal T_total (G1 baseline; the pre-G1 stack quoted 14.5 mm here - superseded).
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
- **Description:** PRE-G1 (historical): of the 3.43 mm between nominal and thick on the pre-G1 stack, 2.05 mm were design choices (added cover 0.5, double-sided REAR 0.85 at nominal-class, window 0.3, REAR PCB 0.2, lower web 0.2) and 1.38 mm were tolerance / supplier / clearance terms; the 15.5 mm upper target was met at nominal tolerances by S1/S2/S3/S5 and by RSS only by S1/S3. G1 (current): the baseline is the integrated G1 stack (nominal 16.75, thick 19.53 - cover and double-sided REAR are baseline layers now); the thickness-recovery study (16 scenarios, `tools/g1_scenarios.py`, section G1) finds NO scenario credibly <= 15.5 mm; verdict THICKNESS OWNER DECISION REQUIRED.
- **Evidence:**
  - zstack.md (G1 baseline): thick - nominal = 2.78; top-3 contributors battery_zone 0.5, cover 0.45, window 0.3
  - architecture.json scenario_results (G1-relative, recomputed from tool layer outputs by arch_diagrams.py check; S6 reproduces the tool thick corner 19.53)
  - generated/g1_scenarios.json: 16 G1 scenarios; thinnest all-credible-lever G1-K2 = 16.08 nominal / 16.52 RSS; only sub-15.5-nominal G1-K4 = 15.18 fails its RSS (15.67) and needs gated levers
  - pre-G1 (historical): zstack thick - nominal = 3.43 on the pre-G1 stack; linear worst-case S1 = 14.5 + 1.28 = 15.78 mm; with C901/C903 as 0402 (-0.35, X19) = 15.43 mm
- **Options:**
  - O1: Report scenarios, not one thick number (adopted, both pre-G1 and G1).
  - O2 (pre-G1, historical): take X19 (-0.35) and the U8 policy (C1) to bring S1 below 15.5 at linear worst case - superseded by the G1 scenario study.
  - O3 (G1): owner decides the thickness target versus the credible levers (accept > 15.5 mm, relax a target term with evidence, or authorize a gated lever path).
- **Recommended provisional direction:** G1 verdict: THICKNESS OWNER DECISION REQUIRED - owner decision on the thickness target (see section G1.6).

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
- **Description:** The interior depth from the REAR optical face to the skin plane is optics_zone + window = 1.35 mm nominal; the caseback plane is h_pod (0.8 nominal) above the skin plane, leaving 0.55 mm minus the caseback wall outside the pod. Parts 0.6-0.75 mm tall on the optical face therefore have to sit inside the pod footprint. G1 (OD-REAR-SIDED 2026-10-11): the baseline is double-sided REAR - the pod covers the optical group (double-sided envelope D 20.5-27.1 mm, opt/cons; the frozen skin-facing group is the emitters/PDs + U12/U13 AFEs + U402-U407 muxes + NT401/NT402 PD_GND net ties + U6 + C802) instead of the whole single-sided envelope (D 22.4-29.4 mm), at the cost of rear_inner (0.90 mm nominal). h_pod is not a thickness lever.
- **Evidence:**
  - zstack.md nominal layers optics_zone 0.85, window 0.5; h_pod nominal 0.8 (stack_parameters.json, PARAMETRIC LOW)
  - architecture.json rear_module.envelope_results
- **Options:**
  - O1: Pod covers all optical-face parts (single-sided) - NOT selected (OD-REAR-SIDED decided double-sided; also not a thickness lever in G1).
  - O2: Double-sided REAR with the pod over the optical group - DECIDED baseline (OD-REAR-SIDED 2026-10-11).
  - O3: Lower h_pod to 0-0.5 (wrist trials) - h_pod is not a thickness lever; needs wrist/strap trials.
- **Recommended provisional direction:** O2 (decided baseline); O3 only with wrist-trial evidence; O1 not selected.
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

### X21-INGRESS-UNDEFINED - Ingress target answered (OD-WATER: 5 ATM); sealing-stack design and qualification still undefined

- **Verdict:** REFINED (G1); **severity:** MEDIUM; **owner decision:** YES (OD-WATER, answered 2026-10-11); **gate:** before case co-design
- **Description (G1):** the target is no longer undefined - 5 ATM / swim-capable is the Rev-A mechanical design target. What remains undefined is the sealing-stack design and qualification: front cover seal, caseback seal, optical window, button and charger feedthrough seals, vent membrane, gasket compression and land widths, and caseback/window stiffness under pressure. The G1 axial/radial consequences and deterministic checks are in section G1.4; qualification items ATM-Q1..Q6 are listed there.
- **Evidence:**
  - input_register OD-WATER (owner decision 2026-10-11)
  - architecture.json g1.atm5 (implications, plate checks, qualification items)
  - generated/g1_scenarios.json deterministic_checks (cover plate, window plate, seal band, cover rim)
- **Options:**
  - O1 (pre-G1, historical): owner sets splash / swim / depth class - ANSWERED: 5 ATM / swim-capable.
  - O2 (G1): G3 sealing-stack design against the 5 ATM target with the g1.atm5 implications; run ATM-Q1..Q6 qualification.
- **Recommended provisional direction:** O2.

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
  - O2: Front lip over the display border instead - CLOSED by OD-COVER (2026-10-11): a separate cover lens is the exterior structural and water barrier; the land is support/bond geometry only.
  - O3: Discrete support pads plus a bond to the fold stiffener / J1 region only (needs SR-DISPLAY-LAND).
- **Recommended provisional direction:** O1 as the working assumption for G2/G3 with the fold interruption and the U4 relief (g1_status REMAINS_OPEN: the -0.06 mm conservative U4 clearance, the display-FPC fold interference and the land geometry are unresolved; OD-COVER resolved only the sealing responsibility). Issue SR-DISPLAY-LAND and SR-DISPLAY-FPC.
- **Reservations involved:** DISP_LAND, DISP_FPC, GNSS_RAD, BLE_RAD, WIFI_RAD, J1501, J201, J202, BATT_EXIT, SUP_SW, SUP_SE, SUP_NE, TP, VENT, SW1, SW2, SW3, SW4, SW5, MAG_CLEAR, FPC_CORR, CHG_RISER, CHG_APPROACH, BATT_TAIL

### Owner decisions required

All seven decisions were ANSWERED by the owner on 2026-10-11 (G1_BRIEF.md section 2; recorded in `inputs/input_register.json` and integrated in the
g1 section below). The questions are kept for traceability.

| ID | Question | Blocks | Status |
|---|---|---|---|
| OD-COVER | Exterior cover strategy: display integral glass flush (t_front_extra 0) or an added sapphire/bezel lip (up to +0.5 mm)? | T_total budget (+0.5), assembly order V1/V2, front seal, display support land versus front lip (X24) | **ANSWERED 2026-10-11**: separate exterior cover lens, bonded/sealed as part of the case; display module is not the structural/water barrier; material/thickness PARAMETRIC (SR-COVER-LENS) |
| OD-WATER | Water/ingress resistance target (class, depth, test)? | seal architecture, radial and axial budgets, whether the display land is the front seal (X24) | **ANSWERED 2026-10-11**: 5 ATM / swim-capable is the Rev-A mechanical design target; sealing-stack design and pressure/leak qualification are future validation work (g1.atm5) |
| OD-U8 | May the GNSS part U8 (protected foundation) be replaced or moved to recover up to 0.74 mm? | front gap, T_total | **ANSWERED 2026-10-11**: U8 may move if mechanical AND RF evidence supports it; part replacement needs separate electrical/RF review (not G1). G1 geometry: no F.Cu escape, B.Cu thickens the stack; U8 stays |
| OD-DEVACCESS | Is post-closure SWD/TP access required, and may J1301/TP13xx be relocated in a later placement phase? | assembly/service sequence, MAIN placement | **ANSWERED 2026-10-11**: SWD/test access required during development, manufacturing and bring-up; external access after final sealing not required (all F.Cu mating in build state S1) |
| OD-J202 | May the J202 charger entry (approved placement) move toward the contact block, or is the long harness accepted? | charger path, west-sector crowding, west charger riser XC-J202 | **ANSWERED 2026-10-11**: the charger entry may move if the mechanical/interconnect study supports it; frozen electrical charger architecture preserved; G1 does not move J202 |
| OD-CONN-SIDE | May J1501/J201 move to B.Cu or an edge feature be added to MAIN in the placement/outline phases? | edge crossings, FPC radial budget | **ANSWERED 2026-10-11**: only if stack, assembly and routing evidence supports it, not for convenience. G1 evaluated B.Cu relocation (G1-CB): not a thickness lever |
| OD-REAR-SIDED | Single-sided REAR (baseline) or double-sided REAR / hot-bar FPC tail, given the stack, pod and service trade? | REAR placement, T_total (+0.85 nominal-class), J1502 selection | **ANSWERED 2026-10-11**: DOUBLE-SIDED REAR; emitters, PDs and sensitive PPG/analog geometry stay on the skin-facing side; connector/support/passive placement allowed on the inner side (h_rear_inner, SR-FPC-MECH) |

## 13. Unresolved blockers and supplier / owner requests

<!-- G2 NOTE 13 -->
The G2 draft supplier requests in architecture.json add numerical acceptance requirements. The generated G2 report contains every option-specific limit. The owner issues requests; none have been sent.
<!-- END G2 NOTE -->

Each request names who, what, what it affects, the hard gate and the parametric stand-in used until the data arrive. Work continues reversibly
with the stand-in until the gate.

| ID | Register id | Who | What | Affects | Hard gate | Parametric stand-in |
|---|---|---|---|---|---|---|
| SR-DISPLAY-FPC | DISPLAY-FPC | Display supplier (ZC-A1D43W-046) | Folded-FPC envelope drawing: thickness, fold exit direction/width, plug location and alignment float, bend radius, border/ink window for ALS; manufacturer drawing constraint component area <= 1.2 mm applies to the local FPC component area, is not the panel/module thickness, and does NOT establish a thickness-saving lever (assembled/folded FPC overlap and height still require supplier/mechanical confirmation; do not infer removable integral glass or subtract display glass from the stack) | front gap (local), west corridor, J1 blind mate, ALS aperture, SW1/SW2 position | before case/outline co-design | t_display_fpc_fold 0.3-0.6; fold footprint +0.7 beyond outline |
| SR-DISPLAY-LAND | DISPLAY-MOD | Display supplier (ZC-A1D43W-046) | Permitted rear support / bond region under the rim (minimum and maximum land width), flatness and allowed pressure, whether the rear border is free of FPC / stiffener, bond material guidance; whether any display-front lamination pressure is permitted (COVER-*-OCA options). G1 (OD-COVER 2026-10-11): the land is support/bond geometry only, NOT the primary water seal - the separate cover lens seals (SR-COVER-LENS) | display support land DISP_LAND (w_land, t_land), cover-to-case seal concept (SR-COVER-LENS), edge-crossing land ceiling | before case co-design (G3) | w_land 0.5-1.5 (< 2.5 POL border); t_land 0.3-0.8 |
| SR-COVER-LENS | COVER-STRATEGY | Cover lens supplier (material/mechanical; owner selects) | Cover lens material, thickness and tolerances, OD/geometry, edge treatment, bonding method, adhesive/seal stack, pressure/water-sealing constraints (5 ATM, OD-WATER), optical requirements (display transmission, ALS aperture). G1 sizes the baseline sapphire-class cover by the 5 ATM plate check (t_cover 1.0-1.65); planning allowables, not supplier data | t_cover, t_cover_bond, cover plate sizing and air gap, front cover seal, G1 baseline thickness, X25-COVER-CASE-FIT | before case co-design (G3) and cover freeze | t_cover 1.0-1.65 (5 ATM plate sizing, COVER-SAP-AIR); t_cover_bond 0.1-0.4 (air gap 0.25 nominal / OCA 0.15 class) |
| SR-BATT-PACK | BATT-PACK | Battery supplier (LPR454440) | Finished protected-pack drawing: max Ø and thickness, tolerance, edge seal, tape/insulation | battery_zone, R_pack_max, annulus | before final outline/case | tol_pack_thick 0-0.3; tol_pack_dia 0.2-0.5 |
| SR-BATT-PCM | BATT-PCM | Battery supplier | PCM envelope and location, tabs, wire/FPC exit, mating connector; tail exit azimuth (preferably at the J201 azimuth 181-197) and tail thickness / bend radius | J201 MPN, carrier pockets, battery tail path, battery tail annulus run (BATT_TAIL, XB-J201) | before J201 MPN and carrier design | BATT_EXIT window [81.5,112.2,84.5,113.2] |
| SR-BATT-GROWTH | BATT-GROWTH | Battery supplier | Permitted swelling/growth allowance and restraint/compression limits | battery_zone, hard stops, optical load path | before carrier/case freeze | g_axial 0.2-0.5; c_axial 0.05-0.2 |
| SR-BATT-NTC | BATT-NTC | Battery supplier | NTC presence, curve and placement (PMIC needs NTC on J201.2) | J201 pin map, PMIC config | before J201 MPN | none (BAT_NTC pin reserved) |
| SR-FPC-MECH | FPC-MECH | Connector and FPC fabricator | J1501/J1502 MPN, pitch, rating, latch/mated height, bend radius, stiffener, length; FPC exit height above F.Cu at the mouth and mouth position relative to the footprint (edge-crossing bend start). G1 (OD-REAR-SIDED 2026-10-11): the authorized double-sided REAR needs the J1502 face and mated height on the inner side, or a hot-bar / ACF flex-tail construction (tail land pattern, bonding process, rework rule) - h_rear_inner is gated on this request | edge wrap, rear_inner, lower web, GND/VLED conductor width, bend start / J1501 mouth radius | before final outline / REAR placement freeze | R_bend_min 0.6-2.0; h_rear_inner 0.6-1.0 (J1502 mated-height class); t_fpc 0.1-0.2; connector run 4.6; exit height >= 0.10 mm and mouth R <= 22.53 required at nominal (edge_crossings) |
| SR-CHG-MECH | CHG-MECH | Contact/dock supplier | Contact geometry, metallurgy, dock force/travel, keying, protection silicon; harness construction (flat flex or wires), conductor thickness and width, bend radius, current rating, exit height at J202. G1 (OD-WATER 2026-10-11): explicit 5 ATM feedthrough/sealing requirement - the sealed contact feedthrough must be pressure-tested to the 5 ATM test pressure (ATM-Q3); the contact block crosses the caseback seal band and cannot share the face seal | contact block envelope, caseback aperture, ESD entry, charger riser radial budget (XC-J202), caseback seal band | before contact-module selection | block az 80-100, r 17.5-24 placeholder; riser slot az 249-259 (CHG_RISER); flat-flex stand-in t 0.1-0.2, R_bend 0.6-2.0; conductor <= 0.80 mm thick beside the pack (nominal) |
| SR-LRA | LRA | LRA supplier (owner selects) | Actuator envelope and mounting method; lead exit and mounting (decides whether the XL-LRA edge crossing exists). G1: kept gated pending supplier/component selection; no supplier invented | LRA pocket, south sector | before perimeter freeze | pocket az 165-195, r 12.65-22 (REAR) |
| SR-BUTTONS | BUTTONS | Switch/pusher supplier (owner selects) | Switch footprint, height, mechanism and seal. G1 (OD-WATER 2026-10-11): explicit 5 ATM sealing requirement - O-ring / membrane button seal pressure and cycling tested to the 5 ATM test pressure (ATM-Q2) | SW1-SW5 windows, wall thickness, west corridor, case wall bores | before perimeter freeze | half-width 7.5 deg, r 21-25.25 placeholder |
| SR-ANTENNAS | ANTENNAS | Antenna supplier / RF consultant | Radiator concepts and keep-outs for GNSS, BLE, Wi-Fi, diplexer U10. G1: kept gated pending supplier/component selection; no supplier invented | radome volumes, display shadowing, caseback metal | before case co-design | reservation rectangles as published |
| SR-SFH4053B-DS | SFH4053B-DS | OSRAM / ams OSRAM | SFH 4053B datasheet: seated height, optical axis, radiant pattern | optics_zone, D405-D407 placement | before REAR optical placement | h_optics_max 0.7-0.85 (assumed) |
| SR-MAX86141-HEIGHT | (package/stack input) | Analog Devices | MAX86141 WLP package outline 21-100134 (seated height) | optics_zone | before REAR optical placement | h_optics_max 0.7-0.85 (assumed) |
| SR-TAGCONNECT | (package/stack input) | Tag-Connect | TC2030-IDC-NL probe engagement volume and retaining clip envelope | J1301 access volume, assembly state S1 | before development fixture design | vertical volume above F.Cu as a labelled reservation |
| SR-J1-ALIGN | (package/stack input) | OCN (OK-23GF/GM-04) | Blind-mate float/lead-in, insertion force and re-mating guidance | V1 assembly (Z-push mating), 50-cycle budget | before assembly order is fixed | none; V1 flagged risk |

Additional blockers that are not supplier data: the owner decisions above, the SFH4053B datasheet source gap (blocks D405-D407 quantitative geometry
only), and the absence of any approved REAR outline, stackup or rules.

## 14. What remains intentionally unfrozen

<!-- G2 NOTE 14 -->
G2 chooses a reversible nominal planning allocation. Actual supplier parts, mirrored physical mating map, processes, RF validation, case geometry and all downstream implementation remain unfrozen.
<!-- END G2 NOTE -->

- REAR outline, stackup, placement, optical spacing, barrier design, window isolation concept (W0/W1/W2, X23), window material/thickness
- J1502 MPN/orientation and the inner-side termination choice (connector vs flex tail, SR-FPC-MECH); J1501 MPN/pitch/orientation
- h_pod, T_body, caseback plane, pod footprint, window retention
- case outline, wall, bosses, screws, gaskets, ingress class
- display support land (width, thickness, interruptions, material); the front-lip alternative is CLOSED by OD-COVER (the cover lens seals)
- MAIN final outline (R 23 is a development envelope), supports, notches
- cover lens material/thickness and bond stack (SR-COVER-LENS, PARAMETRIC; OD-COVER strategy decided 2026-10-11), assembly order V1/V2
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

G2 remains subject to its recorded acceptance gaps and independent review. No later phase is authorized.

- **G3 — REAR optical + guarded-analog placement study:** close G2 review and sensor/attach data gates, component-height evidence and the optical measurement plan. Preserve all sensitive paths on the skin-facing REAR side. Carry the conservative channel deficit forward explicitly.
- **G4 — case + final MAIN outline co-design:** close pack, PCM, growth, display fold/land, cover, actuator/button/antenna and sealing inputs. Resolve X25 and the conservative radial deficit; establish pressure/leak qualification.
- **Later KiCad allocation implementation:** requires explicit authorization, independent G2 acceptance, supplier-confirmed envelopes/processes, verified physical mating permutation, passive DC-bias evidence, reviewed U7 control/power/decoupling allocation, and validated assembly/isolation fixtures. General routing remains separately gated.

The G1 section below is the historical owner-decision and calculation record. Its old gate names and thickness verdict are historical; the current gate mapping above and OD-THICK-REVA govern this study.

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

---
---
---

## G1. Owner-decision integration (2026-10-11)

Scope: `design/mechanical/G1_BRIEF.md`. The seven owner decisions of 2026-10-11 (section 2 of the brief) are recorded in `inputs/input_register.json` and integrated below. The G1 baseline stack is the tool nominal: OD-COVER (separate exterior cover lens, stack layers `t_cover` + `t_cover_bond`) + OD-REAR-SIDED (double-sided REAR, inner-side layer `h_rear_inner`). Every number in this section is computed by `tools/g1_scenarios.py` (`generated/g1_scenarios.json` / `.md`, byte-identical regeneration enforced by `g1_scenarios.py check`); `arch_diagrams.py check` fails if any number quoted here differs from the generated value.

### G1.1 Owner decisions integrated

| ID | Decision (2026-10-11) | Integrated as |
|---|---|---|
| OD-COVER | Separate exterior cover lens/glass over the display, bonded/sealed as part of the case; the display module is not the exterior structural or water barrier; material/thickness PARAMETRIC until the case/display integration study. Integrated as stack layers t_cover + t_cover_bond (G1 baseline, SR-COVER-LENS). | stack layers t_cover + t_cover_bond (G1 baseline); SR-COVER-LENS; X24 sealing responsibility resolved (geometry REMAINS_OPEN) |
| OD-REAR-SIDED | Double-sided REAR PCB; emitters, photodiodes and sensitive PPG/analog geometry stay on the skin-facing side; connector/support/passive placement allowed on the inner side. Integrated as h_rear_inner (J1502 + passives; G1 baseline, SR-FPC-MECH). | stack layer h_rear_inner (J1502 + passives on the inner face); frozen skin-facing group incl. U12/U13, U402-U407, NT401/NT402; SR-FPC-MECH |
| OD-WATER | 5 ATM / swim-capable sealing is the Rev-A mechanical design target; sealing-stack design and pressure/leak qualification are future validation work. Recorded in g1.atm5 (implications + qualification items ATM-Q1..Q6). | 5 ATM implications (G1.4) + qualification items ATM-Q1..Q6; SR-CHG-MECH / SR-BUTTONS sealing requirements |
| OD-U8 | U8 may move if mechanical AND RF evidence supports it; part replacement needs separate electrical/RF review (not G1). G1 evaluated relocation geometrically: no F.Cu escape (g1_scenarios u8 check), B.Cu thickens the stack; U8 placement unchanged in G1. | deterministic U8 relocation geometry check (G1.3); scenarios G1-U8F / G1-U8B |
| OD-DEVACCESS | SWD/test access required during development, manufacturing and bring-up; external SWD access after final sealing not required. All F.Cu mating stays in build state S1. | assembly build state S1 (all F.Cu mating before display install) |
| OD-J202 | The charger entry may move if the mechanical/interconnect study supports it; the frozen electrical charger architecture is preserved. G1 does not move J202. | charger entry unchanged in G1; option open for a later placement phase |
| OD-CONN-SIDE | J1501/J201 may move to the opposite PCB side only if stack, assembly and routing evidence supports it. G1 evaluated B.Cu relocation (G1-CB): connectors land inside the pack projection and do not thin the stack; not a lever. | scenario G1-CB (B.Cu connectors): not a thickness lever |

OD-COVER and OD-REAR-SIDED are NOT revoked or reinterpreted because scenarios are over target (G1_BRIEF.md section 2).

### G1.2 Thickness-recovery scenarios

Target T_total 14.0-15.5 mm. Credibility rule (no optimistic/best-case supplier assumptions): nominal <= 15.5 AND RSS <= 15.5, every lever CREDIBLE_LATER_TASK (a later task inside existing authority), cover sized by the 5 ATM plate check with a passing air-gap check, no failed deterministic check, heights from package_heights max + solder (+ high-CV allowance), never nominal/minimum supplier values; h_pod is not a lever (T_total does not depend on it). The linear worst case is reported, not required. RSS uses each parameter's ACTUAL single-term sensitivity through the scenario rules (nesting can zero the lower-web sensitivity or double-count the insulator).

| Scenario | T nominal | T RSS | T linear worst | T_body (h_pod 0.8) | <= 15.5 credible | Blocking reasons |
|---|---:|---:|---:|---:|---|---|
| G1-S4 | 16.750 | 17.195 | 18.410 | 15.950 | no | nominal T_total 16.75 > 15.5; RSS T_total 17.19 > 15.5 |
| G1-P1 | 16.450 | 16.895 | 18.110 | 15.650 | no | nominal T_total 16.45 > 15.5; RSS T_total 16.89 > 15.5 |
| G1-U8F | 16.750 | 17.195 | 18.410 | 15.950 | no | nominal T_total 16.75 > 15.5; RSS T_total 17.19 > 15.5; lever U8-F status NOT_A_LEVER; u8_relocation_fcu_geometry fails |
| G1-U8B | 17.760 | 18.205 | 19.420 | 16.960 | no | nominal T_total 17.76 > 15.5; RSS T_total 18.20 > 15.5; lever U8-B status NOT_A_LEVER |
| G1-CVG | 17.350 | 17.795 | 19.010 | 16.550 | no | nominal T_total 17.35 > 15.5; RSS T_total 17.79 > 15.5 |
| G1-CVL | 16.200 | 16.685 | 18.010 | 15.400 | no | nominal T_total 16.20 > 15.5; RSS T_total 16.69 > 15.5; cover option COVER-SAP-OCA status OWNER_DECISION_GATED |
| G1-CVGL | 16.200 | 16.685 | 18.010 | 15.400 | no | nominal T_total 16.20 > 15.5; RSS T_total 16.69 > 15.5; cover option COVER-GLS-OCA status OWNER_DECISION_GATED |
| G1-IT | 16.650 | 17.095 | 18.310 | 15.850 | no | nominal T_total 16.65 > 15.5; RSS T_total 17.09 > 15.5 |
| G1-I0 | 16.380 | 16.825 | 18.040 | 15.580 | no | nominal T_total 16.38 > 15.5; RSS T_total 16.82 > 15.5 |
| G1-IS | 16.650 | 17.086 | 18.260 | 15.850 | no | nominal T_total 16.65 > 15.5; RSS T_total 17.09 > 15.5; lever INNER-SKINCONN status SUPPLIER_DATA_GATED |
| G1-IN | 16.030 | 16.480 | 17.690 | 15.230 | no | nominal T_total 16.03 > 15.5; RSS T_total 16.48 > 15.5; lever INNER-NEST status SUPPLIER_DATA_GATED |
| G1-CB | 16.750 | 17.195 | 18.410 | 15.950 | no | nominal T_total 16.75 > 15.5; RSS T_total 17.19 > 15.5; lever CONN-SIDE-B status NOT_A_LEVER |
| G1-K1 | 16.350 | 16.795 | 18.010 | 15.550 | no | nominal T_total 16.35 > 15.5; RSS T_total 16.79 > 15.5 |
| G1-K2 | 16.080 | 16.525 | 17.740 | 15.280 | no | nominal T_total 16.08 > 15.5; RSS T_total 16.52 > 15.5 |
| G1-K3 | 15.730 | 16.180 | 17.390 | 14.930 | no | nominal T_total 15.73 > 15.5; RSS T_total 16.18 > 15.5; lever INNER-NEST status SUPPLIER_DATA_GATED |
| G1-K4 | 15.180 | 15.670 | 16.990 | 14.380 | no | RSS T_total 15.67 > 15.5; lever INNER-NEST status SUPPLIER_DATA_GATED; cover option COVER-SAP-OCA status OWNER_DECISION_GATED |

Cover options (5 ATM plate sizing, linear Kirchhoff plate, simply-supported sizing case, conservative upward grid rounding):

| Option | Material | Bond | t_cover min/nom/max | Plate | Air gap | Gap used |
|---|---|---|---|---|---|---|
| COVER-GLS-AIR | cs_glass | air_gap | 1.400 / 1.750 / 2.400 | PASS | PASS | 0.350 |
| COVER-GLS-OCA | - | oca | 0.600 / 0.800 / 1.000 | n/a (laminate not computable) | n/a | 0.150 |
| COVER-SAP-AIR | sapphire | air_gap | 1.000 / 1.250 / 1.700 | PASS | PASS | 0.250 |
| COVER-SAP-OCA | - | oca | 0.600 / 0.800 / 1.000 | n/a (laminate not computable) | n/a | 0.150 |

Baseline cover sizing vs `inputs/stack_parameters.json` t_cover: PASS (stack 1.000/1.250/1.700, sized 1.000/1.250/1.700; the unrounded conservative requirement is ~1.6516 mm and the conservative upward 0.05 mm grid rounding gives 1.70 mm).

Legacy arithmetic cross-check (package scenario S4 reproduced with the package tolerance terms): LEGACY-S4 nominal 15.850 / RSS 16.276 / linear 17.230 vs expected 15.850 / 16.276 / 17.230 - PASS.

Passive-height optimisation evidence (P-0402, C901/C903 0603 -> 0402): 0402 MLCC in 4.7 uF and 2.2 uF exist as a class (no MPN invented). At 3.0 V a 6.3 V-class 0402 4.7 uF part loses a large share of its capacitance to DC bias; the effective capacitance must be checked against eMMC VCC guidance and, if short, C901 split into two 0402 parts (same height) or C902/C901 re-balanced. C903 at 1.8 V has less derating. Electrically valid in principle; requires the later MAIN BOM/placement task. G1 changes no schematic or footprint.

### G1.3 Deterministic checks (5 ATM and geometry)

- FPC under-run in the lower web: PASS (need 0.250 mm, have 0.300 mm, margin 0.050 mm).
- U8 relocation on F.Cu (OD-U8): INFEASIBLE. Valid necessary bounds for a 10 mm square module: centre <= R_main - s/2 = 18.000 mm (inscribed-circle containment in MAIN) and centre > R_display = 21.950 mm (the module centre is a point of the module, so clearing the display outline requires the centre beyond it). 18.000 < 21.950, so no F.Cu position escapes the rigid display; the earlier orientation-dependent R_main - circumradius bound is replaced by this valid pair.
- Caseback seal band (5 ATM, radial band at the case inner wall at REAR level): R_case_inner 24.050 mm nominal / 23.400 mm conservative; reservations crossing the band and needing separate feedthrough seals: CHG_CONTACT, VENT.
- Cover rim vs the provisional case inner radius: nominal fit margin 0.550 mm with residual wall -0.150 mm (below the 0.7 mm bezel minimum); conservative fit margin -1.100 mm - the cover assembly does not fit the provisional mid-wall inner radius at the conservative corner. New conflict X25-COVER-CASE-FIT; gate G3 case co-design.
- Optical window plate under 5 ATM (ATM-2, analytical model only, NOT a qualification): unsupported radius 10.600 / 12.550 mm (nominal / conservative = double-sided REAR envelope radius - 1.0 mm frame overlap); standoff available 0.100 mm nominal (c_optics). Support bounds: clamped = OPTIMISTIC / stronger-support bound, simply-supported = conservative / weaker-support bound (sizing case); outcomes are reported per support independently. 1 of 18 combinations pass the simply-supported bound; 3 more pass only the clamped bound and are CONDITIONAL ON VERIFIED CLAMPED/RESTRAINED SUPPORT (bond restraint unresolved, gated). 1 of 18 material/thickness/corner combinations pass the conservative simply-supported bound; 3 more pass only the clamped (optimistic) bound and are CONDITIONAL ON VERIFIED CLAMPED/RESTRAINED SUPPORT - the window bond restraint is unresolved and stays gated. No analytical result here is a 5 ATM qualification (ATM-Q2, X23 retained).
  - Model validity: Linear small-deflection Kirchhoff plate, circular, uniform pressure. Support bounds: clamped edge = OPTIMISTIC / stronger-support bound (assumes verified edge rotation restraint); simply-supported edge = conservative / weaker-support bound and the sizing case. Outcomes are reported per support independently; a row passes only if the simply-supported bound passes. Validity limit: flagged where w/t > 0.5 (membrane stiffening then makes the linear result conservative). Analytical model with PARAMETRIC planning properties only - NOT a 5 ATM qualification; the actual window geometry, material and bond restraint remain unresolved (G2 pod concept / G3 caseback, ATM-Q2 window variant, X23) and any clamped-only pass is CONDITIONAL ON VERIFIED CLAMPED/RESTRAINED SUPPORT.

### G1.4 5 ATM implications (OD-WATER)

Axial and radial consequences of the 5 ATM / swim-capable target. Where a simple deterministic check was possible it is in `tools/g1_scenarios.py` (cover plate sizing + air gap + rim, window plate, seal-band crossings, FPC under-run); everything else is a qualification item with its gate. The analytical models are NOT 5 ATM qualification. Sealing-stack design and pressure/leak qualification are future validation work.

| ID | Item | Axial consequence | Radial consequence | Check / qualification | Gate |
|---|---|---|---|---|---|
| ATM-1 | Front cover seal and cover strength | cover lens t_cover (sized 5 ATM) + air gap t_cover_bond in the centre stack | cover bond / seal land w_cover_land beyond the free span a; bezel wall outside the cover edge | cover_plate, cover_rim | G3 case co-design; SR-COVER-LENS |
| ATM-2 | Optical window strength and seal | t_window and window retention flange (X22); the window must not deflect onto the optics or be propped by the barrier walls (X20) | window bond overlap a_window_frame | window_plate | G2 pod concept / G3 caseback; MG-WINDOW-XTALK window variant |
| ATM-3 | Caseback seal, gasket compression and land width | gasket compression set and caseback stiffness are not in the stack (X22) | seal band at the case inner wall at REAR level must clear every REAR-level reservation or that item is sealed separately | rear_seal_band | G3 case co-design |
| ATM-4 | Button seals SW1-SW5 | none in the centre stack | O-ring / membrane bore per button in the case wall (r 21-25.25 placeholders) | ATM-Q2 button seal pressure / cycling test after SR-BUTTONS selection | before perimeter freeze (SR-BUTTONS) |
| ATM-5 | Charger contact feedthrough seal | contact block face seal compression at REAR level | CHG_CONTACT r 17.5-24.0 crosses the caseback seal band (rear_seal_band check) | rear_seal_band | before contact-module selection (SR-CHG-MECH) |
| ATM-6 | Barometer vent membrane (U4) | membrane + support in the NE wall | VENT reservation az 30-60, r 19.5-25.25 | ATM-Q4 membrane water-entry pressure >= test pressure and barometer response (supplier membrane data) | G3 case co-design |
| ATM-7 | Caseback / window stiffness under pressure | caseback and pod deflection must not load the REAR optical stack or the pack (X20) | none | ATM-Q5 caseback deflection analysis once the caseback material and thickness exist (G3), then a pressure test with the REAR module fitted | G3 case co-design |
| ATM-8 | Leak / pressure qualification of the closed watch | none | none | ATM-Q1 select the 5 ATM test standard and margin (owner / qualification plan), then pressure + leak test of closed prototypes; ATM-Q6 swim / dynamic exposure as stated by that standard | before Rev-A sealing qualification |

Qualification items: ATM-Q1 select the 5 ATM test standard and margin (owner / qualification plan); ATM-Q2 button seal pressure / cycling test after SR-BUTTONS selection (window variant under 5 ATM - the G1.3 window plate calculation is analytical only and any clamped-only pass is conditional on verified bond restraint); ATM-Q3 sealed charger contact feedthrough pressure test (SR-CHG-MECH); ATM-Q4 vent membrane water-entry pressure >= test pressure and barometer response; ATM-Q5 caseback deflection analysis once the caseback material/thickness exist (G3), then a pressure test with the REAR module fitted; ATM-Q6 swim / dynamic exposure as stated by the selected standard.

### G1.5 Conflict reassessment (g1_status)

Every conflict of section 12 now carries exactly one `g1_status` with evidence/dependency (`arch_diagrams.py check` enforces this). New conflict exposed by the integration: X25-COVER-CASE-FIT.

| Conflict | g1_status | Evidence / dependency |
|---|---|---|
| C1-FRONT-GAP | REMAINS_OPEN | G1 evaluated U8 relocation (g1_scenarios G1-U8F/G1-U8B): the deterministic u8_relocation_fcu_geometry check shows no F.Cu position of a 10 mm module escapes the display outline (max centre radius 18.00 < 21.95), and B.Cu relocation thickens the stack to 17.76 nominal (G1-U8B). U8 stays in G1. Dependency: RF evidence for any move (OD-U8) and a later placement phase; owner thickness decision (C9). |
| C2-DISPLAY-SIDE-CONNECTORS | REMAINS_OPEN | OD-DEVACCESS (2026-10-11) removes the post-sealing external-access requirement; all F.Cu mating (J1, J1301 SWD, TP13xx, J1501, J201, J202) stays in build state S1 (display absent). G1 changes no connector face. Dependency: assembly-order freeze, SR-FPC-MECH and SR-TAGCONNECT. |
| C3-EDGE-WRAP | SUPPLIER_DATA_GATED | Already gated. Dependency: SR-FPC-MECH (R_bend_min, FPC exit heights, mouth radii) before outline freeze. |
| C4-CHARGER-PATH | REMAINS_OPEN | OD-J202 permits moving the charger entry with mechanical/interconnect evidence; G1 does not move J202. Dependency: later placement phase plus SR-CHG-MECH (5 ATM feedthrough, ATM-Q3). |
| C5-SOUTH-CROWDING | DEFERRED | Deferred to G2 (REAR optical + guarded-analog placement); unchanged by G1. |
| C6-DISPLAY-FPC-FOLD | SUPPLIER_DATA_GATED | Dependency: SR-DISPLAY-FPC folded-FPC envelope drawing (t_display_fpc_fold is SUPPLIER_DATA_REQUIRED). |
| C7-WIFI-BEYOND-BOARD | DEFERRED | Deferred to G3 case co-design (Wi-Fi radiator volume extends beyond the Ø46 development envelope). |
| C8-GNSS-OCCUPIED | REMAINS_OPEN | OD-U8 allows a move only with mechanical AND RF evidence; the G1 geometry check excludes an F.Cu escape and B.Cu thickens the stack. Dependency: RF evidence (GNSS feed, antenna region) + placement phase. |
| C9-THICK-CORNER | OWNER_DECISION_GATED | G1 scenario study (16 scenarios, tools/g1_scenarios.py, generated/g1_scenarios.json): no scenario is credibly <= 15.5 mm. Thinnest all-credible-lever scenario G1-K2 = 16.08 nominal / 16.53 RSS; the only sub-15.5-nominal scenario G1-K4 = 15.18 fails its RSS (15.67) and needs a supplier-gated pocket lever and an owner-gated laminated cover. Verdict: THICKNESS OWNER DECISION REQUIRED (G1_BRIEF.md 4.6 stop rule). |
| X10-OPTICS-HEIGHT-UNKNOWN | SUPPLIER_DATA_GATED | Already gated. Dependency: SR-SFH4053B-DS and SR-MAX86141-HEIGHT before REAR optical placement. |
| X11-POD-FOOTPRINT | REMAINS_OPEN | h_pod is not a lever (T_total does not depend on it; G1_BRIEF.md 4.5). Dependency: wrist/strap trials and the G2/G3 pod concept. |
| X12-J1502-FACE | REMAINS_OPEN | OD-REAR-SIDED authorizes the inner-side J1502 with passives. G1 scenarios: G1-IT (flex tail, 0.70 mm inner height) and G1-I0 (tail + 0201 cap, 0.43 mm) are credible later tasks; G1-IS (skin-face connector) is supplier-gated. Dependency: SR-FPC-MECH (J1502 mated height or tail construction) + G2. |
| X13-EDGE-CROSSINGS | SUPPLIER_DATA_GATED | Dependency: SR-FPC-MECH / SR-CHG-MECH / SR-BATT-PCM exit heights and mouth radii (unchanged by G1). |
| X14-SUPPORT-GAP | DEFERRED | Deferred to G3 case co-design (case supports). |
| X15-NE-CROWDING | DEFERRED | Deferred to G3 case co-design (NE vent/ALS crowding). |
| X16-MAGNETOMETER | REMAINS_OPEN | Dependency: magnetometer interference analysis with the frozen charger-contact position; not addressed by G1 (no watch-side magnet introduced). |
| X17-GNSS-ALL-HEIGHTS | REMAINS_OPEN | OD-U8: relocation needs RF evidence; the G1 geometry check excludes an F.Cu escape; U8 placement is not changed in G1. |
| X18-PACK-EDGE | SUPPLIER_DATA_GATED | Dependency: SR-BATT-PACK finished-pack drawing (diameter/tolerance). |
| X19-BCU-0603 | REMAINS_OPEN | G1 lever P-0402 (C901/C903 0603 -> 0402, 0.65 mm high-CV seated incl. solder and high-CV allowance) is a credible later task (-0.30 mm nominal, G1-P1). Dependency: later MAIN BOM/placement task - 0402 parts with >= 6.3 V rating, DC-bias effective capacitance at 3.0 V / 1.8 V vs eMMC guidance (electrical evidence in inputs/g1_scenarios.json); G1 changes no schematic or footprint. |
| X20-GROWTH-VS-OPTICS | SUPPLIER_DATA_GATED | Dependency: SR-BATT-GROWTH permitted growth/restraint; the INNER-NEST carrier-floor pocket lever is gated on it (pack bulge into a window must never load the REAR stack). |
| X21-INGRESS-UNDEFINED | REMAINS_OPEN | OD-WATER (2026-10-11) sets 5 ATM / swim-capable as the Rev-A mechanical design target. G1 records the 5 ATM implications (g1.atm5: cover plate sizing, seal bands, feedthrough seals, qualification items ATM-Q1..Q6). Dependency: G3 sealing-stack design + pressure/leak qualification (future validation work). |
| X22-UNMODELLED-Z | REMAINS_OPEN | Gasket compression and caseback stiffness are not in the stack. Dependency: G3 caseback design and ATM-Q5 deflection analysis under the 5 ATM test pressure. |
| X23-WINDOW-CROSSTALK | SUPPLIER_DATA_GATED | Already gated on MG-WINDOW-XTALK. The 5 ATM window plate check is added as qualification item ATM-Q2 window variant (g1.atm5). |
| X24-DISPLAY-LAND | REMAINS_OPEN | OD-COVER (2026-10-11) resolves only the sealing responsibility: the separate cover lens is the exterior structural/water barrier and the display land is support/bond geometry. The conflict's geometry scope is NOT resolved: the -0.06 mm conservative U4 clearance (t_land must stay <= 0.74 mm over U4 or be relieved), the display-FPC fold interference (~10 mm of unsupported rim unless the supplier permits bonding to the fold stiffener) and the support-land geometry itself remain open. Dependencies: SR-DISPLAY-LAND (permitted support region, flatness, allowed pressure), SR-DISPLAY-FPC (fold envelope), G3 case co-design for the U4 relief / land interruption. |
| X25-COVER-CASE-FIT | REMAINS_OPEN | G1 integration exposes the radial cover stack vs the provisional case: deterministic check cover_rim fails at the conservative corner (-1.10 mm) and the nominal residual wall (0.55) is below t_bezel_min (0.7). Dependency: G3 case co-design (front aperture / case outer / land width) + SR-COVER-LENS + SR-DISPLAY-LAND. |

### G1.6 G1 verdict

**THICKNESS OWNER DECISION REQUIRED**

Stop rule (G1_BRIEF.md 4.6): no scenario is credibly <= 15.5 mm, so the G1 verdict is THICKNESS OWNER DECISION REQUIRED; the tradeoff table is presented and no requirement is weakened. OD-COVER and OD-REAR-SIDED are NOT revoked.

- Thinnest scenario: G1-K4 at 15.180 mm nominal / 15.670 mm RSS (credible <= 15.5: no).
- Thinnest scenario using only CREDIBLE_LATER_TASK levers: G1-K2 at 16.080 mm nominal / 16.525 mm RSS (still over target).

Per the stop rule (G1_BRIEF.md 4.6) the tradeoff table above is presented and G1 stops here: no requirement is weakened to reach 15.5 mm, and OD-COVER / OD-REAR-SIDED stand. The owner decision needed (C9): accept > 15.5 mm, relax a target term with evidence, or authorize a gated lever path (INNER-NEST pocketing needs SR-BATT-GROWTH unsupported-span data; a laminated cover needs OD-COVER-LOADPATH + SR-DISPLAY-LAND + SR-COVER-LENS) - noting G1-K4 (15.18 nominal) still fails its RSS (15.67) and is not credible as it stands.

<!-- G2 GENERATED BEGIN -->
## G2

**G2 CONDITIONAL — ENGINEERING GATES OPEN**

OD-THICK-REVA governs this provisional integration: nominal ≤ 16.5 mm and RSS ≤ 17.0 mm. The earlier 14.0–15.5 mm target is a non-binding production goal. Source: owner decision 2026-10-12.

All numbers below are PROJECT_DERIVED from generated/g2_interconnect.json unless labelled otherwise. No supplier dimension is asserted. Full three-corner calculations, overlaps, routing estimates, numeric acceptance requirements and alternative options are in [the generated G2 report](generated/g2_interconnect.md).

| Interface option | Outcome | Selected | Side | XY window / azimuth | Length excluding service mm | Bends |
|---|---|---|---|---|---:|---:|
| J1501-F.Cu | CONDITIONAL | True | F.Cu | [100.2, 116.4, 108.5, 121] / [152.603, 179.454] | 27.081 | 2 |
| J1501-B.Cu | CONDITIONAL | False | B.Cu | [100.2, 116.4, 108.5, 121] / [152.603, 179.454] | 24.659 | 2 |
| J1502-TAIL0402 | CONDITIONAL | True | REAR-inner | None / [158, 178] | 11.450 | 0 |
| J1502-TAIL0201 | REJECTED | False | REAR-inner | None / [158, 178] | 11.450 | 0 |
| J1502-CONNECTOR | CONDITIONAL | False | REAR-inner | None / [158, 178] | 11.450 | 0 |
| J201-F.Cu | CONDITIONAL | True | F.Cu | [94, 119, 99.5, 122] / [181.302, 197.526] | 29.698 | 6 |
| J201-B.Cu | CONDITIONAL | False | B.Cu | [84.5, 112.5, 87.9, 115.4] / [218.157, 231.116] | 13.117 | 4 |
| J202-WEST-F.Cu | CONDITIONAL | True | F.Cu | [79.5, 100.35, 82, 103.25] / [259.765, 269.022] | 78.016 | 6 |
| J202-WEST-B.Cu | REJECTED | False | B.Cu | [79.5, 100.35, 82, 103.25] / [259.765, 269.022] | 71.307 | 4 |
| J202-EAST-B.Cu | CONDITIONAL | False | B.Cu | [118, 103.8, 121.5, 106.8] / [100.023, 110.695] | 21.921 | 4 |
| U7-F.Cu | REJECTED | False | F.Cu | [112.3, 113.05, 114.3, 114.95] / [132.383, 140.554] | 46.786 | 6 |
| U7-B.Cu | CONDITIONAL | True | B.Cu | [112.3, 113.05, 114.3, 114.95] / [132.383, 140.554] | 40.391 | 4 |
| J1301-RETAIN | CONDITIONAL | True | F.Cu | [103.5, 112.0, 110.5, 116.0] / [138.814, 167.661] | 0.000 | 0 |
| J1-RETAIN | CONDITIONAL | True | F.Cu | [79.45, 92.25, 82.95, 100.25] / [269.16, 294.444] | 7.190 | 1 |
| U8-RETAIN | RECOMMENDED | True | F.Cu | [94.399, 80.394, 105.601, 91.606] / [326.286, 33.714] | 0.000 | 0 |
| C901-C903-P0402 | RECOMMENDED | True | B.Cu | [96.77, 105.02, 100.73, 109.98] / [171.726, 212.758] | 0.000 | 0 |

| Selected interface | mating / exit | mated Z range mm | path |
|---|---|---|---|
| J1501 | Insert radially inward into outward-facing mouth; actuate latch from F.Cu / Radially outward toward riser azimuth; inward-facing branch at REAR/pack end | {"max": 1.4, "min": 0.77, "nom": 1.05} | Generated path_regions; corner length excludes service slack |
| J1502 | Bond under process fixture / toward J1501 south riser | {"max": 0.73, "min": 0.68, "nom": 0.7} | radially outward in lower-web groove to the common sensor riser; counted once in J1501 installed length |
| J201 | Insert radially outward into inward-facing J201 mouth; actuate from F.Cu / Inboard toward the raised front-gap arc, then SW riser; no long annulus tail | {"max": 1.4, "min": 0.77, "nom": 1.05} | Generated path_regions; corner length excludes service slack |
| J202 | Insert radially inward into outward-facing mouth; actuate latch from F.Cu / Radially outward toward riser azimuth; inward-facing branch at REAR/pack end | {"max": 1.4, "min": 0.77, "nom": 1.05} | Generated path_regions; corner length excludes service slack |
| U7/LRA | Solder insulated lead pair on B.Cu with strain relief; no demountable latch / Radially outward toward the allocated LRA riser | {"max": 0.625, "min": 0.625, "nom": 0.625} | Generated path_regions; corner length excludes service slack |
| J1301 | Z insertion from F.Cu in S0/S1 / not applicable: probe or soldered component | {"max": 0.0, "min": 0.0, "nom": 0.0} | not applicable |
| J1 | Z insertion from F.Cu in S0/S1 / west display fold | {"max": 0.8, "min": 0.8, "nom": 0.8} | west DISP_FPC envelope |
| U8 | soldered; no mating operation / not applicable: probe or soldered component | {"max": 2.7, "min": 2.7, "nom": 2.7} | not applicable |
| C901/C903 | soldered; no mating operation / not applicable: probe or soldered component | {"max": 0.65, "min": 0.65, "nom": 0.65} | not applicable |

| Stack | nominal | RSS | linear worst | T_body (h_pod 0.8) | compliance |
|---|---:|---:|---:|---:|---|
| G2-K2-REF | 16.080 | 16.525 | 17.740 | 15.280 | reference PASS |
| G2-REVA | 16.350 | 16.796 | 18.040 | 15.550 | True |
| G2-REVA-HI | 16.380 | 16.825 | 18.040 | 15.580 | True |

| B.Cu option | K2-neutral h_stack max | Rev-A nominal h_stack max | R_bend max nominal | fold length required |
|---|---:|---:|---:|---:|
| J1501-B.Cu | 0.650 | 0.800 | 1.773 | 11.602 |
| J201-B.Cu | 0.650 | 0.800 | 1.773 | 11.145 |
| J202-WEST-B.Cu | 0.650 | 0.800 | 1.773 | 14.688 |
| J202-EAST-B.Cu | 0.650 | 0.800 | 1.773 | 9.076 |

RSS additionally limits positive stack variation; the generated joint-acceptance table is mandatory, not optional. A side change requires a verified mirrored physical mating map with the logical interface unchanged.

P-0402 is adopted as a CREDIBLE_LATER_TASK. C901/C903 retain the electrical evidence gate: ≥6.3 V class, effective capacitance at 3.0 V / 1.8 V against eMMC requirements; a second same-height passive may be needed. No footprint/schematic edit is made. No supplier-gated nesting, cover lamination or reduced pod height is credited.

Assembly/service (PROVISIONAL_ASSUMPTION):

- **S0**: Battery isolated at accessible external development break/fixture; charger detached. Probe bare MAIN F.Cu and TP1301-TP1306. Mate no live battery connector.
- **S1**: Bond/test REAR tail on its inner face before carrier insertion. Fit carrier, pack insulation and independent charger module. For B.Cu options hold MAIN B.Cu-up on a jig, mate cold, rotate about the single common tangent hinge in joint_book_fold with computed joint slack (isolated option hinges are lower bounds only) in the OUTSIDE assembly jig, then capture slack in its reserved pocket. F.Cu connectors mate visibly before the display. Connect battery last for bring-up; isolate again before any manipulation.
- **S2**: Remove SWD probe/clip; verify carrier guide-pin relief. Connect J1 visibly with display hinged; close display onto support land without trapping the fold. Blind Z-mating is allowed only after SR-J1-ALIGN fixture verification. Caseback remains open; connectors beneath the display cannot be accessed directly.
- **S3**: Inspect strain relief, separated charger feedthrough and seals; close caseback using hard stops. No external SWD requirement. Rework reverses S3 to S1 with battery isolation BEFORE moving MAIN/display; log every J1 cycle. A bonded REAR tail is serviced by replacing the REAR+tail unit through J1501, not repeated tail peeling.
- **isolation**: Use an external development battery disconnect in the test fixture before closing the stack; for a sealed unit detach charger and open caseback, isolate pack at a supplier-provided accessible pack-tail break before lifting MAIN. If no accessible isolation break can be provided, the remating process is SUPPLIER_DATA_REQUIRED and not release-ready; never hot-unplug under the display.

The rigid MAIN folds about the single common tangent hinge in joint_book_fold; isolated option hinges provide lower bounds only. Required slack and pocket requirements are recorded per option and for the joint fold. Slack stays outside the case during rotation and never doubles inside the annulus. J1 budget: 50 rated / 25 planned mating cycles.

U8 RF verification:

- Retain live U8 MAX-F10S at (100,86) on F.Cu; no relocation/part-change study.
- Verify C1420/C1421/R1420 are the intended feed/matching network inside GNSS_RAD (C8), with tuned matching on the assembled case.
- Verify GNSS_RAD through every Z level (X17), display shielding, cover/case shadowing, battery/carrier metal and radome dielectric.
- Measure antenna efficiency, sensitivity and detuning with wrist/strap, charge dock, buttons, display activity, BLE/Wi-Fi coexistence. No RF improvement is credited to thickness.

G3 must carry the unchanged conservative radial margin -0.950 mm to G4. X25 remains: conservative cover fit -1.100 mm; nominal wall margin -0.150 mm. No downstream phase is authorized.

| Conflict | g2_status | Evidence |
|---|---|---|
| C1-FRONT-GAP | REMAINS_OPEN | U8 retained F.Cu north. G1 valid necessary bound 18.00 < 21.95; no relocation or GNSS change studied. RF list remains required. |
| C2-DISPLAY-SIDE-CONNECTORS | REMAINS_OPEN | G2 allocation is provisional; prior geometry/qualification dependency remains. See generated option checks and supplier requirements. |
| C3-EDGE-WRAP | SUPPLIER_DATA_GATED | Numeric supplier acceptance requirements in G2 supplier requests; conservative geometry/qualification is not closed. |
| C4-CHARGER-PATH | REMAINS_OPEN | G2 allocation is provisional; prior geometry/qualification dependency remains. See generated option checks and supplier requirements. |
| C5-SOUTH-CROWDING | DEFERRED_G3 | G3 REAR optical/guarded-analog integration, including inner-face attach and lower-web crossings, remains separately authorized work. |
| C6-DISPLAY-FPC-FOLD | SUPPLIER_DATA_GATED | Numeric supplier acceptance requirements in G2 supplier requests; conservative geometry/qualification is not closed. |
| C7-WIFI-BEYOND-BOARD | REMAINS_OPEN | Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable. |
| C8-GNSS-OCCUPIED | REMAINS_OPEN | G2 allocation is provisional; prior geometry/qualification dependency remains. See generated option checks and supplier requirements. |
| C9-THICK-CORNER | RESOLVED_BY_G2 | OD-THICK-REVA applied; see generated G2-REVA nominal/RSS compliance. HI result separately reported; no gated lever credited. |
| X10-OPTICS-HEIGHT-UNKNOWN | SUPPLIER_DATA_GATED | Numeric supplier acceptance requirements in G2 supplier requests; conservative geometry/qualification is not closed. |
| X11-POD-FOOTPRINT | DEFERRED_G3 | G3 REAR optical/guarded-analog integration, including inner-face attach and lower-web crossings, remains separately authorized work. |
| X12-J1502-FACE | DEFERRED_G3 | G3 REAR optical/guarded-analog integration, including inner-face attach and lower-web crossings, remains separately authorized work. |
| X13-EDGE-CROSSINGS | REMAINS_OPEN | G2 allocation is provisional; prior geometry/qualification dependency remains. See generated option checks and supplier requirements. |
| X14-SUPPORT-GAP | REMAINS_OPEN | Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable. |
| X15-NE-CROWDING | REMAINS_OPEN | Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable. |
| X16-MAGNETOMETER | REMAINS_OPEN | G2 allocation is provisional; prior geometry/qualification dependency remains. See generated option checks and supplier requirements. |
| X17-GNSS-ALL-HEIGHTS | REMAINS_OPEN | G2 allocation is provisional; prior geometry/qualification dependency remains. See generated option checks and supplier requirements. |
| X18-PACK-EDGE | SUPPLIER_DATA_GATED | Numeric supplier acceptance requirements in G2 supplier requests; conservative geometry/qualification is not closed. |
| X19-BCU-0603 | RESOLVED_BY_G2 | P-0402 adopted as a credible later task. DC-bias/effective capacitance evidence remains mandatory before electrical implementation. |
| X20-GROWTH-VS-OPTICS | SUPPLIER_DATA_GATED | Numeric supplier acceptance requirements in G2 supplier requests; conservative geometry/qualification is not closed. |
| X21-INGRESS-UNDEFINED | REMAINS_OPEN | Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable. |
| X22-UNMODELLED-Z | REMAINS_OPEN | Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable. |
| X23-WINDOW-CROSSTALK | SUPPLIER_DATA_GATED | Numeric supplier acceptance requirements in G2 supplier requests; conservative geometry/qualification is not closed. |
| X24-DISPLAY-LAND | REMAINS_OPEN | Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable. |
| X25-COVER-CASE-FIT | REMAINS_OPEN | Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable. |
| G2-CROSSING-HEIGHT | SUPPLIER_DATA_GATED | Shared lower-web crossing heights computed in shared_corridors; no unverified thin flex is credited. |
| G2-BOOK-FOLD | SUPPLIER_DATA_GATED | B.Cu options need quantified tangent-hinge slack, remating space and accessible battery isolation. Requirements in each option. |
| G2-PROBE-RELIEF | SUPPLIER_DATA_GATED | Tag-Connect through-board guide pins must fit the derived clearance or use carrier relief / S0 fixture. No added seated Z. |
| G2-BACK-STACK | SUPPLIER_DATA_GATED | Full connector + flex + stiffener + solder stack and its positive uncertainty must meet both nominal and RSS limits. |
| G2-DISCOVERED-INTERFACES | SUPPLIER_DATA_GATED | SW1-SW5, antenna feeds and TP access registered; supplier feed construction remains unknown. |

Drafted / issue-ready supplier requests (owner issues): SR-FPC-MECH, SR-BATT-PCM, SR-BATT-PACK, SR-CHG-MECH, SR-TAGCONNECT, SR-LRA, SR-BUTTONS, SR-DISPLAY-FPC, SR-ANTENNAS. Numeric requirements are incorporated into architecture.json and the generated report.

G2 reservations: G2-J1501-F.Cu-0, G2-J1501-F.Cu-1, G2-J1501-F.Cu-2, G2-J201-F.Cu-0, G2-J201-F.Cu-1, G2-J201-F.Cu-2, G2-J202-WEST-F.Cu-0, G2-J202-WEST-F.Cu-1, G2-J202-WEST-F.Cu-2, G2-U7-B.Cu-0, G2-U7-B.Cu-1, G2-U7-B.Cu-2, G2-U7-SERVICE-POCKET.

Remaining acceptance gaps:

- AE1420: supplier-controlled feed construction prevents a final length/bend/Z allocation (acceptance 2).
- AE1401: supplier-controlled feed construction prevents a final length/bend/Z allocation (acceptance 2).
- AE1410: supplier-controlled feed construction prevents a final length/bend/Z allocation (acceptance 2).

<!-- G2 GENERATED END -->

<!-- G3 GENERATED BEGIN -->
## G3 — REAR optical + guarded-analog placement study

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
<!-- G3 GENERATED END -->
