# G3 brief — REAR OPTICAL + GUARDED-ANALOG PLACEMENT STUDY (Rev-A)

Status: phase contract finalized with owner decisions OD-G3-ENTRY, OD-G3-SIDE and OD-G3-RECORD (approved
2026-10-13). G3 work is provisional, reversible architecture/placement-study work. It authorizes no KiCad edit
and does not authorize G4. This brief is the scope contract for G3. It
builds on G2 (CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES by independent review; engineering commit
`eea49e4` on `mechanical/g2-interconnect-stack-closure`), G1 (`168badb`) and Phase 1, whose rules still apply
except where this brief explicitly changes scope. Destination: `design/mechanical/G3_BRIEF.md`.
Work branch: `mechanical/g3-rear-optical-guarded-analog`, created from `eea49e4`.

## 1. Objective

Produce a deterministic, evidence-classed REAR placement study: face allocation of every REAR reference,
candidate REAR-frame placements (XY, rotation, face), optical cell / barrier / aperture geometry, guarded-analog
corridors and locality, aggressor exclusions, MAX30208 thermal-island geometry, J1502 tail-land and support
reservations, REAR outline and pod footprint, and the REAR-level Z non-regression against G2. Exit is a
recommended REAR placement topology plus reservations, rules and supplier/measurement gates that a later,
separately authorized KiCad REAR implementation phase can execute, and a numeric handoff to G4. It is not a
KiCad change, not an optical-performance claim and not a frozen design.

## 2. Owner decisions (authoritative)

Already in force and unchanged: OD-COVER, OD-REAR-SIDED, OD-WATER, OD-U8, OD-DEVACCESS, OD-J202, OD-CONN-SIDE
(2026-10-11) and OD-THICK-REVA (2026-10-12), as recorded in `inputs/input_register.json`. Do not revoke or
reinterpret any of them.

New for G3 — **APPROVED by the owner 2026-10-13**. Record them verbatim in this brief and in
`architecture.json.g3.owner_decisions` (date 2026-10-13, source: owner decision, G3_BRIEF.md section 2), NOT in
`input_register.json`:

- **OD-G3-ENTRY — APPROVED.** The existing G3 entry items "close SFH4053B/MAX86141 height and optical evidence
  gaps" and "verify J1502 attach/current/rating/flex-channel geometry" are reclassified from G3 ENTRY requirements
  to G3 CLOSURE gates. G3 may begin as a bounded parametric engineering study before those supplier /
  manufacturer values are closed. G3 may not claim final closure unless its brief-defined numeric closure
  conditions are satisfied (section 11, criteria 5 and 10).
- **OD-G3-SIDE — APPROVED.** G3 face-allocation baseline. Skin-facing REAR: emitters, photodiodes, both MAX86141
  AFEs, MAX30208, and sensitive optical/analog components required by locality. Inner-facing REAR: other
  suitable passives, J1502 tail/support structures, mechanically suitable non-sensitive support components.
  VREF capacitors are skin-facing by default; an inner-face VREF capacitor is permitted only directly under its
  AFE and with no more than one via, if the deterministic G3 study proves the topology. No inner-face AFE
  alternative study is authorized.
- **OD-G3-RECORD — APPROVED.** G3 may update engineering documentation to record "G2 CLOSED — PASS WITH
  SUPPLIER/ENGINEERING GATES". This does not close any remaining G2 supplier gates and does not authorize G4.

**Lead application of OD-G3-SIDE (binding for G3 unless the owner amends it):**
- Skin face, named: D401–D407, D413/D414/D423/D424, U12/U13, U6.
- Skin face, "required by locality" (consistent with the G1 skin-face group in
  `architecture.json.rear_module.envelope_derivation` and the REAR-local net rule): U402–U407 (LED cathode /
  current-sink mux geometry), NT401/NT402 (PD_GND single-point ties), C802 (U6 local decoupling, thermal island).
  Moving any of these to the inner face is OWNER DECISION REQUIRED, not a G3 option.
- Inner face permitted: R401–R405/R408/R409, C403–C408, C4101/C4102/C4104, C4201/C4202/C4204, the J1502 tail land,
  support/hard-stop structures and the C1501 reservation, each subject to the locality limits of section 6.3.
  A part goes to the inner face only if the tool shows that its locality limit is met there.
- VREF C4103/C4203: skin face by default. The inner-face variant is evaluated only as "directly under its AFE":
  capacitor courtyard inside the AFE courtyard projection (+0.5 mm PROVISIONAL), at most one via on the VREF net,
  and the section 6.3.4 VREF limit met. Otherwise it is REJECTED.

Owner inputs needed before G3 *closure* (not before start): PPG modalities Rev-A must support (green HR;
red/IR SpO2; IR850 vs IR940 purpose) and any spacing bins that follow; the MG-WINDOW-XTALK acceptance threshold;
the skin-temperature accuracy target. Until supplied, G3 uses the PROVISIONAL values in section 6 and reports
them as such.

## 3. Frozen (do not change)

- Architecture: rigid MAIN; MAIN↔REAR FPC; rigid double-sided skin-facing REAR; separate charger flex/harness.
- `frozen_invariants` in `inputs/input_register.json`, verbatim. In particular: REAR 46/44/44/2 TBD; 44
  transferred refs; 24 positions / 13 nets in `design/interfaces/main_rear_interface.json`; REAR-local only:
  PD_IN, PD_GND, VREF, LED cathode/current-sink nets, LED mux selects; TPS631000 on MAIN; no charger-positive in
  the sensor FPC.
- REAR optical/analog membership from `design/interfaces/validation/rear_netlist.xml`, including the
  channel map (PPG2 LED6 = IR940 chip inside D402; D401/D403/D404 IR pads unconnected). No net, value,
  footprint or membership change.
- G2 allocation, including J1502 = J1502-TAIL0402 (inner-face bonded tail, mated Z 0.68/0.70/0.73), the
  sensor under-run in the lower web, and G2-REVA 16.350 / 16.796 / 18.040 and G2-REVA-HI 16.380 / 16.825 /
  18.040. No supplier-gated or owner-gated lever may be credited.
- Conservative radial margin −0.950 mm and X25 conservative cover fit −1.100 mm are carried unchanged; G3 does
  not solve them and must not consume annulus volume.
- Anything that needs one of these changed is OWNER DECISION REQUIRED, never the recommendation.

## 4. Scope

**May modify** (tracked files under `design/mechanical/` only): `architecture.md` (new section G3; G3 status
lines; label erratum below), `architecture.json` (new `g3` block; one `g3_status` per conflict; erratum),
`README.md`, `tools/arch_diagrams.py` (extend `check` to the G3 block only). New files:
`inputs/g3_rear_optical.json`, `tools/g3_rear_optical.py` (`build` / `check`), `generated/g3_rear_optical.json`,
`generated/g3_rear_optical.md`, `generated/g3_rear_faces.svg`, `generated/g3_rear_section.svg`.
Generated files are written only by the tool and must regenerate byte-identically.

**Erratum (label only).** `architecture.json` / `architecture.md` call NT401/NT402 "NTCs". They are
PD_GND net ties (`NetTie-2_SMD_Pad0.5mm`, values PPG1_PD_GND_TIE / PPG2_PD_GND_TIE). Correct the label; no
numeric change.

**Immutable** (byte-identical to `eea49e4`): every G1-immutable file of G2_BRIEF section 4 plus
`generated/zstack.json` and `generated/main_height_map.json`; `inputs/input_register.json`;
`inputs/stack_parameters.json`; `inputs/package_heights.json`; `inputs/g1_scenarios.json`;
`inputs/g2_interconnect.json`; `tools/mech_model.py`, `tools/mech_model_spec.md`, `tools/g1_scenarios.py`,
`tools/g2_interconnect.py`; `generated/g1_scenarios.*`, `generated/g2_interconnect.*`,
`generated/g2_allocation.svg`, `generated/perimeter_map.svg`, `generated/rear_module_concept.svg`,
`generated/interconnect_paths.svg`; `PHASE_BRIEF.md`, `G1_BRIEF.md`, `G2_BRIEF.md`, this brief.
The existing `architecture.md` G2 section and `architecture.json.g2` block stay byte/semantically identical.

**May not modify:** anything outside `design/mechanical/`; any KiCad file (`*.kicad_pcb`, `*.kicad_sch`,
`*.kicad_pro`, `*.kicad_prl`), footprint or symbol library; `rear_sensor/**`, `libraries/**`,
`design/interfaces/**`, `design/placement/**`, firmware, scripts, docs. KiCad files, library footprints,
netlists and the local datasheets in `../datasheets/` may be **read** for evidence.

**Tool rules.** `tools/g3_rear_optical.py` is stdlib-only, deterministic (no timestamps, fixed float
formatting, sorted keys), and may import `mech_model`, `g1_scenarios` and `g2_interconnect` functions and their
tolerance policy (imported, never re-implemented). It reads, read-only and SHA-256-pinned:
`rear_netlist.xml`, the REAR footprint `.kicad_mod` files (pad and courtyard geometry), `main_rear_interface.json`,
`architecture.json` (reservations, rear_module), `generated/g2_interconnect.json`, `inputs/stack_parameters.json`,
`inputs/package_heights.json` and `inputs/g3_rear_optical.json`. Any G3 parameter lives in
`inputs/g3_rear_optical.json`; candidate placements there are authored PROVISIONAL inputs, never results.

**Evidence classes** (exactly one per material value/claim): MANUFACTURER_VERIFIED (local primary document +
page/table/figure), PROJECT_DERIVED (computed by a G1/G2/G3 tool), PROVISIONAL_ASSUMPTION (min/nom/max with
rationale; nominal not the best case), MANUFACTURER_DATA_REQUIRED (component maker's datasheet/outline not
local), SUPPLIER_DATA_REQUIRED (custom supplier: FPC/PCB fab, window, adhesive, barrier, pod), MEASUREMENT_REQUIRED
(closable only by prototype measurement), OWNER_DECISION. Never invent a dimension or optical/thermal value.

**Evidence inventory (lead-verified, to be re-cited by the tool):**
- MANUFACTURER_VERIFIED: SFH7018A 2.4×2.4×0.6 ±0.1 (v1.1 p15), chip areas green 0.75×0.75, red/IR 0.3×0.3,
  half angle 60°, 2-cavity (green | red+IR); SFH2703(H) 3.2×2.0×0.6 ±0.1 (v1.2 p8), radiant sensitive area
  3.27 mm², chip 2.8×1.4, half angle 65°, C = 9 pF typ at VR = 5 V; MAX86141 WLP 2.048×1.848, 5×4 @0.4,
  outline 21-100134, PD input capacitance limits 65/130/260/520 pF per PDBIAS 0x1/0x5/0x6/0x7, layout
  guidelines (p49–51); MAX30208 2×2×0.75 thin LGA, θJA 241.3 °C/W, θJC 53.9 °C/W, measurement considerations
  (p7).
- Figure-only manufacturer data (must be read from the drawing and cited with page before use, else
  PROVISIONAL): SFH7018A die/cavity positions; SFH2703 capacitance at 0 V bias.
- MANUFACTURER_DATA_REQUIRED: SFH4053B (all mechanical/optical data); MAX86141 seated height
  (outline 21-100134); TS5A12301E YFP height (0.5 max is PARAMETRIC). The 0.45 mm SFH4053B height and the
  "drawing E062.3010.122" provenance in the library footprint / `docs/project` are NOT verifiable locally and
  must not be used.
- Known documentation discrepancy: `docs/project/bom_selection.md` gives SFH2703H area 2.72 mm²; the local
  datasheet gives 3.27 mm². Use the datasheet.

## 5. Coordinate frames

REAR frame = REAR KiCad frame, viewed on the skin face (F.Cu), origin at the REAR envelope centre. Assembly
frame per `architecture.json.rear_module.transform`: x_a = x_c − (x_r − x_rc), y_a = y_c + (y_r − y_rc); the
wrist view has north up, east left. Every geometric result is reported in both frames; every assembly-frame
reservation imported from G1/G2 (LRA, FPC_UNDER, CHG_ROUTE, CHG_LINK, CHG_CONTACT, MAG_CLEAR, J1502 attach window)
is transformed by the tool, never hand-converted. Pin order is never read from a mirrored view.

## 6. Evaluations (deterministic, in `tools/g3_rear_optical.py`)

Evaluate each check at nominal and report conservative / optimistic where a parameter has a range.

### 6.1 Integrity and allocation
1. Netlist reproduction: 44 transferred refs + J1502/C1501 provisions; the per-AFE channel map (each LED chip →
   mux → AFE driver; each PD → AFE input) is derived from `rear_netlist.xml` and must equal
   `architecture.json.rear_module.optical_grouping` and input_register REAR-PD-MAP. No REAR-local net appears in
   the interface file.
2. Face allocation: every ref has exactly one face; the OD-G3-SIDE skin-face set (named + locality-required,
   section 2) is complete; every inner-face part carries the locality check that justifies it; an inner-face VREF
   capacitor passes the "directly under its AFE, ≤ 1 via" test or the candidate fails.
3. Heights. Skin face: every part's max seated height ≤ h_optics_max nominal 0.75 (stack-neutral); unknowns
   (D405–D407, U12/U13) are reported with derived thresholds: stack-neutral ≤ 0.75; within G1 range ≤ 0.85;
   OD-THICK-REVA nominal compliance on G2-REVA-HI ≤ 0.87 (lead arithmetic 0.75 + (16.50 − 16.38)); RSS limits
   computed by the tool. Inner face: every part ≤ 0.65 (TAIL0402 h_rear_inner 0.70 incl. 0.05 joint);
   C1501 reservation height ≤ 0.65 or the stack delta is reported. The tool recomputes all thresholds.
4. G2 non-regression: re-evaluate G2-REVA and G2-REVA-HI through imported G2/G1 functions with the G3
   allocation; delta must be 0.000 for the recommended candidate. Any non-zero delta is reported, never hidden.

### 6.2 Optical geometry (per candidate)
1. Courtyard non-overlap per face (exact polygon/rectangle intersection; abutting allowed) and containment
   inside the candidate REAR outline minus edge margin.
2. Per measured channel (LED chip, PD) on the same AFE: centre-to-centre distance (package centre; die centre
   only if the die offset is MANUFACTURER_VERIFIED and cited), grouped by wavelength (green 536, red 660,
   IR850, IR940). Report coverage of the PROVISIONAL study range 3–8 mm and per-wavelength bins.
3. Symmetry: per PD, |d(site A) − d(site B)| per wavelength; AFE1↔AFE2 mirror residual; report PPG2 LED6
   (IR940 in D402) geometry explicitly against its site-B role.
4. Non-measured pairs: minimum emitter→PD distance across AFEs (simultaneous-sampling aggressors).
5. Cells and barriers: each emitter and each PD in its own cell; courtyard gap between any emitter cell and any
   PD cell ≥ t_barrier_max + 2·c_wall (PROVISIONAL 0.5 + 2×0.1 = 0.7 mm).
6. Apertures: per cell, aperture centred on the active area; aperture size as a function of window thickness
   (0.3/0.5/0.8) and stack depth, reported parametrically; compatibility flags for W0, W1 (rib width ≥ barrier
   width) and W2 (per-cell window + seal land ≥ PROVISIONAL width). No isolation level is claimed.
7. Pod: pod footprint = hull of all skin-face cells + frame wall (PROVISIONAL 0.5–1.0); every skin-face part
   inside the pod (X11); ambient-light path rule: no transparent path from the pod edge to a PD cell shorter
   than the frame wall (geometric proxy only).

### 6.3 Guarded-analog locality (corridor-based; no routing)
0. MANUFACTURER_VERIFIED rules (MAX86140/MAX86141 data sheet, "Layout Guidelines", pp. 49–51), carried as
   requirements into the later KiCad phase and checked geometrically here where possible:
   - PD_IN fully shielded by PD_GND: coplanar PD_GND guard on the layer that carries the AFE; PD_GND shield
     extended beneath the photodiode; no traces next to any PD_IN via; no other traces or vias through PD_GND.
   - The PCB GND plane on the layer adjacent to PD_GND; no traces routed over PD_GND.
   - PD_GND connected to PCB GND at one point only. In this design that is NT401 (PPG1_PD_GND) and NT402
     (PPG2_PD_GND) (`rear_netlist.xml`; interface contract: charger current and optical power returns must not
     flow through either tie or guard copper).
   - VDD_ANA and VDD_DIG shorted at the PCB and decoupled with 22 µF 0402 + 0.1 µF (C4101/C4102,
     C4201/C4202). VREF decoupled to GND with 1.0 µF, 6.3 V class (C4103/C4203). Each decoupling capacitor gets
     its own vias to GND. GND_ANA, GND_DIG and PGND shorted at the WLP edge with a single via to the GND plane
     close to the AFE.
   - Photodiode input capacitance limits 65 / 130 / 260 / 520 pF for PDBIAS 0x1 / 0x5 / 0x6 / 0x7, with the
     lowest suitable PDBIAS recommended (lowest noise).
1. PD_IN: same face as AFE (skin) → 0 vias (hard; PROJECT rule derived from the OD-G3-SIDE same-face allocation
   and the guidance above, not a manufacturer requirement). Manhattan pad-centre to ball-centre length ≤ PROVISIONAL
   6.0 mm; corridor width ≥ w_trace + 2·(s + w_guard) with fab classes PROVISIONAL (0.075–0.10 / 0.075–0.10 /
   0.10–0.15) pending SUPPLIER_DATA_REQUIRED fab rules; corridor free of non-PD_IN/PD_GND pads.
2. Capacitance budget (MANUFACTURER_VERIFIED limit): C_PD(0 V) + C_corridor ≤ 65 pF keeps PDBIAS 0x1. C_PD(0 V)
   is read from the SFH2703 curve or carried as MANUFACTURER_DATA_REQUIRED; C_corridor per mm PROVISIONAL.
3. PD_GND: shield region per AFE = PD courtyards + PD_IN corridors + guard; NT401/NT402 ≤ 2.0 mm from its
   AFE PD_GND ball (U12.C5 / U13.C5) and on the AFE side; shield regions must not intersect any LED-current,
   VLED, digital or tail-land region (plan, both faces projected).
4. VREF C4103/C4203 ≤ 2.0 mm to B5; VDD 0.1 µF (C4102/C4202) ≤ 2.0 mm and 22 µF (C4101/C4201) ≤ 3.0 mm to
   C2/D2; VLED caps C403–C408 ≤ 2.0 mm to their mux; C4104/C4204 ≤ 4.0 mm to their AFE A1 (all PROVISIONAL).
   Opposite-face placement counts the via and is reported.
5. LED current loops: for every LED chip, loop polygon VLED cap → anode → cathode → mux → AFE LED_DRV → PGND →
   cap; loop area reported (ranking), and no loop may intersect a PD_GND shield region (hard).
6. Aggressor separation: ≥ 0.5 mm plan gap (PROVISIONAL) from any shield region to LED-current, VLED, SPI/INT/CS
   corridors and the tail land; digital corridors from the tail to AFEs must not cross shield regions.
7. MAX86141 escape: the six inner balls (B2, B3, B4, C2, C3, C4) need via-in-pad/microvia escape → REAR
   stackup requirement (HDI, ≥4 layers, layer roles L1 PD_IN + coplanar PD_GND; L2 PD_GND shield islands;
   L3 solid GND adjacent; L4 inner face). Fab feasibility within t_rear_pcb 0.6–1.0 is SUPPLIER_DATA_REQUIRED;
   > 1.0 mm is reported as a stack delta.

### 6.4 REAR mechanical stack and outline
1. REAR outline candidate (polygon, REAR frame): report r_max(az) in the assembly frame; overlap areas with
   LRA, FPC_UNDER, CHG_ROUTE, CHG_LINK, CHG_CONTACT and MAG_CLEAR; every overlap is registered with disposition.
   Hard limit r ≤ 16.5 (CHG_ROUTE inner 17.0 − 0.5 PROVISIONAL).
   MAG_CLEAR (BMM350 U703, 10 mm PARAMETRIC placeholder radius) already overlaps REAR_ENV by 78.15 mm² (G1
   overlap register, X16). For each candidate the tool reports the MAG_CLEAR overlap of: the REAR outline, every
   LED current loop polygon, the VLED entry and the tail land. Required: no LED current loop, VLED entry or tail
   land inside MAG_CLEAR, or a registered OWNER/measurement disposition (X16 O1/O2). Field closure is
   MEASUREMENT_REQUIRED; no magnetic claim is made.
2. J1502 tail land (inner face): width W = 23·p + 2·m from G2 inputs (5.00 / 6.45 / 7.90); must fit inside the
   FPC_UNDER azimuth band at its radius or a recorded alternative (two-row land, radial land orientation,
   re-dispositioned C5/LRA azimuths) is evaluated. Lead arithmetic: the 26.9° band gives 5.45 mm of arc at
   r 11.6 and 5.94 mm at r 12.65, so the nominal 6.45 mm tail does not fit tangentially inside REAR_ENV.
   Report land position vs the G2 radial attach window (9.6–11.6 nominal; 11.55–13.55 conservative), thermode
   keepout (PROVISIONAL ≥ 1.0 mm), strain-relief zone, VLED/GND entry adjacent to C1501/C4x04.
3. Support lands / hard stops: ≥ 3 inner-face keepouts at the REAR periphery outside optical cells, none
   within 1.0 mm (PROVISIONAL) of a WLP/DSBGA footprint projection; load path window → pod frame → hard stops →
   carrier, never through optical parts or the pack (X20).
4. Section: lower web ≥ t_fpc + c_fpc; inner ceiling; pod depth = optics_zone + window (1.35 nominal); residual
   outside the pod 0.55 − caseback wall; sub-allocation of c_optics (0.05–0.2) to barrier-gasket compression and
   window retention (X22); any overrun is a reported stack delta.

### 6.5 MAX30208 thermal island (geometric proxies; no performance claim)
U6 courtyard gap ≥ 4.0 mm to the nearest emitter, ≥ 3.0 mm to AFE/mux, tail land, C1501 and VLED entry
(PROVISIONAL); tongue slot-isolated perimeter fraction ≥ 0.6 (PROVISIONAL); U6 traces counted (MAX30208 p7: thin
traces, good contact to package top). The G1 illustrative tongue azimuth (~255, assembly frame) lies inside the
CHG_LINK azimuth slot (249–259, r 20.0–23.05) next to CHG_ROUTE (az 100–260, r 17.0–20.0). The tool reports the
plan and 3-D distance from U6 to both corridors and to CHG_CONTACT. Required: the tongue azimuth is chosen by the
tool's ranking, not copied from G1, and U6 is ≥ 4.0 mm in plan (PROVISIONAL) from any charger corridor.
Otherwise the conflict is registered as an X16/F-section thermal disposition; skin-contact
option F1/F2/F3 geometry compatible with W0/W1/W2. Closure is MEASUREMENT_REQUIRED.

### 6.6 Manufacturing and bring-up
Double-sided assembly order and reflow-cycle limits (read from OSRAM/ADI docs where local, else
MANUFACTURER_DATA_REQUIRED); underfill/flux keepouts from optical apertures; hot-bar/ACF after SMT; REAR+tail
replaced as a unit (G2). No test point on any REAR-local net; any REAR test pad is a schematic ECO (OWNER).
Bring-up through J1501 digital/power only.

## 7. Candidates and selection rule

Author at least three materially different topologies in `inputs/g3_rear_optical.json`, evaluated on equal
terms, including the G1 concept (mirrored AFE groups, AFEs toward the south tail edge) and a central-emitter /
peripheral-PD variant. No candidate outcome may be an input constant.

A candidate is ACCEPTABLE if every hard check in section 6 passes at nominal and every remaining unknown is
MANUFACTURER/SUPPLIER_DATA_REQUIRED or MEASUREMENT_REQUIRED with a numeric threshold. Rank lexicographically:
1. no frozen-invariant / owner-decision impact; 2. G2 non-regression delta 0; 3. optical channel coverage of the
study bins and symmetry; 4. PD_IN worst-case length and guard margin; 5. aggressor separation and LED loop area;
6. U6 thermal proxies; 7. smaller pod/outline and larger clearance to LRA / FPC_UNDER / charger corridors;
8. manufacturability and rework. Outcome per candidate: RECOMMENDED / CONDITIONAL (names the discriminating value
and threshold) / REJECTED, with reasons.

## 8. Measurement and supplier plan (drafted, owner issues)

- MG-SPACING: variable-spacing coupon REAR covering 3–8 mm per wavelength.
- MG-WINDOW-XTALK: W0/W1/W2 with W-ref, no-skin floor per pair; owner sets the threshold.
- MG-GUARD: dark, LEDs-off input-referred noise per PD input vs MAX86141 table at the same PPG_TINT;
  PROVISIONAL acceptance ≤ 1.5× datasheet; delta with SPI active ≤ 10 %.
- MG-THERMAL: MAX30208 vs reference on a skin phantom across LED duty and charging; owner sets accuracy.
- Requests with numeric acceptance: SR-SFH4053B-DS, SR-MAX86141-HEIGHT (thresholds from 6.1.3), SR-FPC-MECH tail
  land (width, pitch, rows, thermode keepout), SR-REAR-PCB (HDI stackup within 0.6–1.0 mm, microvia-in-pad at
  0.4 mm pitch), SR-WINDOW / SR-BARRIER / SR-ADHESIVE (thickness, opacity, compression) as PROVISIONAL ranges.

## 9. Package updates

- `architecture.md`: new section **G3** (allocation table, candidate table, checks, selection, measurement plan,
  conflict status, G4 handoff), quoting the generated report exactly; G3 status lines; erratum.
- `architecture.json`: `g3` block (owner decisions, allocation, candidates, selection, reservations, handoff);
  every conflict gains exactly one `g3_status` (RESOLVED_BY_G3 / REMAINS_OPEN / SUPPLIER_DATA_GATED /
  MEASUREMENT_GATED / DEFERRED_G4 / OWNER_DECISION_GATED) with evidence. C5, X11, X12 (DEFERRED_G3) must be
  dispositioned; X10, X16, X20, X22, X23 must be updated.
- `README.md`: G3 tool and outputs.

## 10. Validation (all must exit 0)

```
python3 -B design/mechanical/tools/mech_model.py check
python3 -B design/mechanical/tools/g1_scenarios.py check
python3 -B design/mechanical/tools/g2_interconnect.py check
python3 -B design/mechanical/tools/arch_diagrams.py check
python3 -B design/mechanical/tools/g3_rear_optical.py check
git diff --exit-code eea49e4 -- design/mechanical/inputs/input_register.json design/mechanical/inputs/stack_parameters.json design/mechanical/inputs/package_heights.json design/mechanical/inputs/g1_scenarios.json design/mechanical/inputs/g2_interconnect.json design/mechanical/tools/mech_model.py design/mechanical/tools/mech_model_spec.md design/mechanical/tools/g1_scenarios.py design/mechanical/tools/g2_interconnect.py design/mechanical/generated/zstack.json design/mechanical/generated/zstack.md design/mechanical/generated/zstack_section.svg design/mechanical/generated/main_height_map.json design/mechanical/generated/main_height_map.md design/mechanical/generated/main_height_map.svg design/mechanical/generated/g1_scenarios.json design/mechanical/generated/g1_scenarios.md design/mechanical/generated/g2_interconnect.json design/mechanical/generated/g2_interconnect.md design/mechanical/generated/g2_allocation.svg design/mechanical/generated/perimeter_map.svg design/mechanical/generated/rear_module_concept.svg design/mechanical/generated/interconnect_paths.svg design/mechanical/PHASE_BRIEF.md design/mechanical/G1_BRIEF.md design/mechanical/G2_BRIEF.md
git diff --exit-code 168badbab6de1201bb3209902a53fe1e4b874cc9 -- design/mechanical/inputs/stack_parameters.json design/mechanical/inputs/package_heights.json design/mechanical/inputs/g1_scenarios.json design/mechanical/tools/mech_model.py design/mechanical/tools/mech_model_spec.md design/mechanical/tools/g1_scenarios.py design/mechanical/generated/zstack.md design/mechanical/generated/zstack_section.svg design/mechanical/generated/main_height_map.md design/mechanical/generated/main_height_map.svg design/mechanical/generated/g1_scenarios.json design/mechanical/generated/g1_scenarios.md
python3 -B -c '<G2_BRIEF.md section 9 B semantic provenance check, unchanged>'
git diff --exit-code eea49e4 -- '*.kicad_pcb' '*.kicad_sch' '*.kicad_pro' '*.kicad_prl' design/interfaces design/placement rear_sensor libraries
test -z "$(git diff --name-only eea49e4 -- . ':(exclude)design/mechanical/**')"
git diff --check
```

`g3_rear_optical.py check` regenerates in memory and fails on any byte difference, on a source-hash mismatch,
on a channel map differing from the netlist, on a hard check failing for the RECOMMENDED candidate, or on a
non-zero G2 non-regression delta that is not reported. It includes self-tests proving that an injected courtyard
overlap, a PD_IN via, an LED loop crossing a shield region and a mirrored transform are each caught.
`arch_diagrams.py check` verifies every G3 number quoted in `architecture.md/json` against the generated JSON,
exactly one `g3_status` per conflict, and that the G2 section is unchanged.

## 11. Acceptance criteria

1. Owner decisions of section 2 recorded; all earlier decisions and invariants unchanged; interface unchanged.
2. Every REAR ref has a face, REAR-frame XY/rotation and assembly-frame XY in the RECOMMENDED candidate, each with
   an evidence class; ≥ 3 candidates evaluated under section 7.
3. Hard checks pass for the RECOMMENDED candidate at nominal: non-overlap, containment, cells/barrier gap,
   PD_IN 0 vias and ≤ limit, NT40x locality, shield-region exclusions, LED loops clear of shields, inner ceiling,
   r_max limit, tail-land fit (or recorded alternative), support keepouts.
4. G2-REVA / G2-REVA-HI reproduced exactly; G3 delta 0.000 for the RECOMMENDED candidate, or the verdict is
   OWNER DECISION REQUIRED.
5. Numeric thresholds stated for SFH4053B and MAX86141 seated height, C1501 height, tail-land width/pitch,
   REAR stackup, and every PROVISIONAL rule; no invented supplier/manufacturer value.
6. Measurement gates MG-SPACING / MG-WINDOW-XTALK / MG-GUARD / MG-THERMAL drafted with metrics.
7. G4 handoff (section 13) complete and numeric. −0.950 and −1.100 carried unchanged.
8. All section 10 commands exit 0; changes confined to the files of section 4.
9. Verdict exactly one of: G3 PASS; G3 CONDITIONAL — SUPPLIER/MEASUREMENT GATES OPEN; G3 OWNER DECISION
   REQUIRED; G3 FAIL.
10. OD-G3-ENTRY closure conditions. G3 PASS (final closure) requires all of the following. Otherwise the verdict is at
    most CONDITIONAL and each open item is listed with its threshold:
    a. SFH4053B and MAX86141 max seated heights MANUFACTURER_VERIFIED (cited) and ≤ 0.75 mm (stack-neutral), or
       the resulting G2-REVA / G2-REVA-HI totals recomputed by the tool and still meeting OD-THICK-REVA, with
       the owner accepting the delta;
    b. SFH4053B footprint/package and emitting-area data MANUFACTURER_VERIFIED and the D405–D407 geometry
       re-run with it;
    c. J1502 tail: land width/pitch/rows, joint thickness ≤ 0.05 mm (a G3 supplier-qualification closure
       requirement, stricter than the immutable G2 range; G2 tail_joint remains 0.03 / 0.05 / 0.08 mm
       min / nominal / max and is not altered), per-position current
       ≥ 41.3 mA continuous-equivalent for PPG_VLED (124 mA / 3, G1 arithmetic, the rating basis to be
       confirmed by the supplier) and the land fit of section 6.4.2 SUPPLIER-confirmed. A supplier-confirmed
       joint thickness > 0.05 mm but ≤ 0.08 mm does not invalidate G2, but criterion 10 is then not satisfied
       and the verdict is at most CONDITIONAL; the requirement is not relaxed.
11. `README.md` / `architecture.md` record "G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES" (OD-G3-RECORD)
    without changing any G2 gate status and without any statement that authorizes G4.

## 12. Stop conditions

- A candidate needs a frozen-invariant, membership, net, footprint, schematic, interface or G2-allocation change:
  mark that candidate OWNER DECISION REQUIRED and continue; if no candidate is acceptable without one, finish
  with verdict G3 OWNER DECISION REQUIRED and stop.
- No candidate keeps the G2 stack delta at 0.000 with credible assumptions: report the delta and the
  OD-THICK-REVA headroom; verdict G3 OWNER DECISION REQUIRED.
- The 24-position tail cannot be placed on the inner face under any evaluated land arrangement: stop and report
  (G2 J1502 allocation is affected).
- J1502 supplier/process cannot demonstrate joint thickness ≤ 0.05 mm: this prevents G3 final closure
  (criterion 10c) but is not a violation of the immutable G2 tail_joint maximum of 0.08 mm and does not change
  G2-REVA or G2-REVA-HI.
- A required input is missing or contradictory, or the live repo disagrees with this brief: stop and report.
- Any immutable file would have to change, or a deterministic check fails and cannot be fixed in scope: stop.

## 13. G3 → G4 handoff (numeric, in `generated/g3_rear_optical.json.g4_handoff`)

REAR outline polygon and r_max(az) (assembly frame); pod footprint polygon, pod depth stack and caseback residual;
window variant compatibility (W0/W1/W2) and aperture set; hard-stop / support land positions and loads path;
U6 skin-contact feature location and type; tail exit position/width and under-run corridor; REAR-level clearances
to LRA, CHG_ROUTE, CHG_LINK, CHG_CONTACT, MAG_CLEAR; the conservative radial margin −0.950 and X25 −1.100
unchanged; open SR/MG gates with thresholds; seal-land width requirement around the pod as a PROVISIONAL range.

## 14. Independent review must challenge

- Channel map vs netlist (incl. PPG2 IR940 in D402); transform/mirroring; any face swap of frozen skin-face parts.
- Optical geometry: emitter–PD distances, symmetry, cross-AFE aggressors, cell gaps; no optimality claimed.
- PD_IN: 0 vias, lengths, corridor width vs fab classes, shield regions, NT40x single-point ground, LED loops.
- VREF/decoupling locality and any inner-face placement; MAX86141 inner-ball escape / HDI requirement.
- U6 thermal contamination (LEDs, AFEs, VLED entry, tail, charger corridors) and skin-contact concept.
- Double-sided stack: inner ceiling 0.65, C1501, tail joint, support lands vs WLP, c_optics sub-allocation.
- Tail-land width vs FPC_UNDER azimuth; LRA/C5 overlap disposition; MAG_CLEAR overlap.
- G2 reproduction and zero delta; immutability of G1/G2/KiCad/interface; no credited gated lever.
- Hidden supplier/manufacturer assumptions (SFH4053B 0.45, MAX86141 height, die positions, C_PD(0 V)).
- Manufacturability/rework: reflow count, underfill keepouts, hot-bar keepout, REAR+tail replacement.

## 15. Not in G3

KiCad edits of any kind (footprints, placement, Edge.Cuts, zones, stackup, rules, routing); schematic, BOM,
value, footprint or net changes; MPN selection or purchase; supplier request issuance; optical or thermal
performance claims; window/pod material freeze; case CAD, caseback and sealing design, final MAIN outline (G4);
antenna feed construction (G4 gate); MAIN-side items (J201 clearance, C901/C903 DC-bias, U7, U8 RF); any change to
G1/G2 records or `input_register.json`.
