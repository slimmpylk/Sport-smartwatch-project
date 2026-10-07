# Sportwatch Rev-A PCB Foundation Correction Round 3 Report

**Document Revision:** 1.0  
**Date:** 2026-10-07  
**Author:** PCB Foundation Correction Round 3 Implementation Agent  
**Branch:** `pcb/revA-floorplan`  
**Base Commit (Starting HEAD):** `6829ac3c90de973e7885e546163bec655ef145e6`  
**Target Verdict:** **FOUNDATION CORRECTION ROUND 3: PASS — READY FOR INDEPENDENT RE-REVIEW**  

---

## 1. Executive Summary

This report documents the exhaustive, targeted corrective actions executed during Round 3 to resolve the blocking findings identified in `docs/project/pcb_foundation_independent_rereview_round2.md`. 

### Key Accomplishments & Verified Results:
1. **DRC Errors Cleared & Refilled State Committed:**
   - The 24 committed DRC errors (12 clearance + 12 hole-clearance) caused by proof microvias interacting with a stale `In1.Cu` GND fill have been **100% eliminated**.
   - `pcbnew.ZONE_FILLER` was executed across all zones, and the refilled state was **saved and committed directly to `sportwatch_revA.kicad_pcb`**.
   - Direct CLI DRC verification without `--refill-zones` proves: **0 DRC errors, 0 shorts, 0 mask bridges, 0 keepout violations**.
2. **Rebuilt Stackup-Compliant Proof Microvias:**
   - The 12 proof microvias were previously `F.Cu -> In2.Cu` (L1->L3) skip microvias, a construct not supported by the baseline HDI stackup.
   - All 12 proof microvias were completely rebuilt as **stacked microvias**: `L1->L2` (`F.Cu -> In1.Cu`) + `L2->L3` (`In1.Cu -> In2.Cu`) at identical $(X, Y)$ coordinates (24 microvias total).
   - Microvia geometry: 0.220 mm diameter land, 0.100 mm laser drill.
   - All 24 microvias are Via-In-Pad Plated Over (VIPPO), specified per **IPC-4761 Type VII** (epoxy-filled, planarized, and copper-capped) under 0.5 mm BGA balls and 0201 passive pads.
   - Standard 0.200 mm antipads are verified carved in the `In1.Cu` GND plane around the signal microvias.
3. **HighSpeed_50R Track Width Harmonized:**
   - Reconciled the discrepancy between proof track width (0.100 mm) and `HighSpeed_50R` netclass definition (0.120 mm).
   - Harmonized to **0.100 mm** track width across `.kicad_pro`, `.kicad_dru` (min track width 0.10 mm), live proof routing, and documentation.
   - Formally designated: **PROVISIONAL HIGH-SPEED WIDTH — FINAL IMPEDANCE PENDING FABRICATOR FIELD SOLVE**.
4. **PPG Channel Mapping ECO & 4-Channel Guarded Routing:**
   - Evaluated detector geometry and confirmed that detector assignments were crossed, forcing a topological Jordan curve crossing.
   - Executed schematic ECO swapping detector channel assignments:
     - `D413` (North, adjacent to West AFE `U13`) mapped to `PPG2_PD2_IN` / `PPG2_PD_GND`.
     - `D424` (East, adjacent to South AFE `U12`) mapped to `PPG1_PD1_IN` / `PPG1_PD_GND`.
   - Re-exported netlist: 243 components, 389 nets (exact match).
   - Routed all 4 detector channels pad-to-pad on `B.Cu` with continuous dedicated `PD_GND` ground guards:
     - AFE 1 (`U12`, South): Channel 1 (`PPG1_PD1_IN`, 6.31 mm) and Channel 2 (`PPG1_PD2_IN`, 1.80 mm) routed and fully shielded by `PPG1_PD_GND` loop connecting `D414.2`, `D424.2`, `U12.C5`, and `NT401.1`.
     - AFE 2 (`U13`, West): Channel 1 (`PPG2_PD1_IN`, 3.44 mm) and Channel 2 (`PPG2_PD2_IN`, 7.50 mm) routed and fully shielded by `PPG2_PD_GND` guards connecting `D413.2`, `D423.2`, `U13.C5`, and `NT402.1`.
   - Verified 0 track crossings, 0 shorts, 0 mask bridges, and ample clearance ($>0.30\text{ mm}$) to all adjacent optics and thermal fields.
5. **Critical Support Parts Staged with Formal Engineering Mitigation:**
   - Addressed staged support passives: eMMC interface passives (`R901`–`R910`, `C905`, `C906`), PPG VLED decoupling (`C403`–`C408`), and nPM1300 VBAT capacitor (`C206`).
   - Formally deferred with documented mitigation reserving placement corridors:
     - eMMC: Reserved $4.0 \times 6.0\text{ mm}$ corridor on `F.Cu` / `In3.Cu` between `U101` and `U901` for inline series resistor placement in Phase 4.
     - PPG VLED: Reserved outer peripheral sites ($R > 12.5\text{ mm}$) on `B.Cu` adjacent to driver FETs `U402`–`U407`, avoiding optical and thermal keepouts.
     - VBAT: Reserved battery entry corridor near `J201`.
6. **Schematic Residuals Closed with Primary Sources:**
   - **Y101 MPN & CL:** Finalized to Abracon `ABS07-32.768KHZ-6-T` ($C_L = 6.0\text{ pF}$, ESR max 70 kΩ). Calculated discrete load capacitors $C_{118} = C_{119} = 8.2\text{ pF}$ assuming $C_{stray} \approx 1.9\text{ pF}$.
   - **Y102 Load Capacitance:** Cited Ambiq Apollo510B Reference Manual Table 50 / `MCUCTRL.HFXTALTRIM` register proving on-chip programmable load capacitance bank covers crystals up to $C_L \le 10\text{ pF}$. MPN finalized to NDK `NX1612SA-48M-EXS00A-CS14265` ($C_L = 8\text{ pF}$). No external load caps required.
   - **Y1 Load Capacitance:** Cited Nordic Semiconductor nRF7002 Product Specification v1.1 Section 5.1 and PCA10143 reference design proving `XON`/`XOP` connect directly to 40 MHz crystal without external load caps; frequency trimming is handled via on-chip OTP calibration (`XO_TRIM`). MPN finalized to NDK `NX1612SA-40M-EXS00A-CS14264`.
   - **U8 VCC_RF Pin:** Cited u-blox MAX-F10S Hardware Integration Manual (UBX-22028884) Section 3.1 proving `VCC_RF` is a filtered power output for external active antenna / LNA bias. For the Sportwatch passive antenna (`AE1420`) baseline, `VCC_RF` is intentionally unconnected (NC). Added detailed explanatory note to `05_GNSS.kicad_sch`.

---

## 2. Phase 0 — Authoritative Repository State Verification

At the start of Round 3, the git repository was verified:
- Branch: `pcb/revA-floorplan`
- Starting HEAD: `6829ac3c90de973e7885e546163bec655ef145e6`
- Working tree: clean tracked files, single expected untracked file `opencode.jsonc` (preserved untouched).

---

## 3. Phase 1 & 2 — Proof Microvia Rebuild & Zone Refill

### 3.1 Problem Definition
In Round 2, the Apollo/eMMC proof routing used 12 microvias spanning `F.Cu -> In2.Cu` (layer 0 to layer 6). These were L1->L3 skip microvias piercing the `In1.Cu` GND reference plane. Because the committed `In1.Cu` zone fill predated this routing, no antipads were carved around the via barrels in the copper fill, resulting in:
- 12 × `clearance` violations (0.200 mm required vs 0.000 mm actual)
- 12 × `hole_clearance` violations (0.200 mm required vs 0.000 mm actual)
- Total: 24 DRC errors.

Furthermore, standard 1+N+1 HDI stackups support sequential lamination of L1->L2 microvias and L2->L3 stacked or staggered microvias, but do not support single-operation L1->L3 skip microvias without specialized vendor qualification.

### 3.2 Corrective Implementation
1. Every L1->L3 skip microvia was removed.
2. Replaced each with two stacked microvias at identical $(X, Y)$ coordinates:
   - **L1 -> L2 Microvia:** Spans `F.Cu` (0) to `In1.Cu` (4), diameter 0.220 mm, drill 0.100 mm (`VIATYPE_MICROVIA`).
   - **L2 -> L3 Microvia:** Spans `In1.Cu` (4) to `In2.Cu` (6), diameter 0.220 mm, drill 0.100 mm (`VIATYPE_MICROVIA`).
3. Total microvias on board increased from 12 to 24 (12 stacked pairs).
4. All zones refilled using `pcbnew.ZONE_FILLER`. Antipads of 0.200 mm were carved cleanly in `In1.Cu` GND copper.
5. Saved and committed directly to `sportwatch_revA.kicad_pcb`.

### 3.3 Proof Signal Verification Table
Every proof connection was verified pad-to-pad:

| Signal Net Name | Transmit Pad (F.Cu) | Transmit Vias | Routing Layer | Receive Vias | Receive Pad (F.Cu) | DRC Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `/01_APOLLO510B/MCU_EMMC_CLK` | `U101.K9` $(100.800, 98.700)$ | L1-L2 + L2-L3 | `In2.Cu` (0.100 mm) | L1-L2 + L2-L3 | `R111.1` $(101.180, 101.475)$ | **PASS (0 errors)** |
| `/EMMC_CLK` | `R111.2` $(101.820, 101.475)$ | L1-L2 + L2-L3 | `In2.Cu` (0.100 mm) | L1-L2 + L2-L3 | `U901.M6` $(99.250, 109.250)$ | **PASS (0 errors)** |
| `/EMMC_CMD` | `U101.K8` $(100.400, 98.700)$ | L1-L2 + L2-L3 | `In2.Cu` (0.100 mm) | L1-L2 + L2-L3 | `U901.M5` $(98.750, 109.250)$ | **PASS (0 errors)** |
| `/EMMC_DAT4` | `U101.H7` $(100.000, 97.900)$ | L1-L2 + L2-L3 | `In2.Cu` (0.100 mm) | L1-L2 + L2-L3 | `U901.B3` $(97.750, 104.250)$ | **PASS (0 errors)** |
| `/EMMC_DAT5` | `U101.J7` $(100.000, 98.300)$ | L1-L2 + L2-L3 | `In2.Cu` (0.100 mm) | L1-L2 + L2-L3 | `U901.B4` $(98.250, 104.250)$ | **PASS (0 errors)** |
| `/EMMC_DAT6` | `U101.K7` $(100.000, 98.700)$ | L1-L2 + L2-L3 | `In2.Cu` (0.100 mm) | L1-L2 + L2-L3 | `U901.B5` $(98.750, 104.250)$ | **PASS (0 errors)** |

---

## 4. Phase 3 — HighSpeed_50R Track Width Harmonization

The independent review noted that proof tracks were routed at 0.100 mm width, whereas `HighSpeed_50R` in `.kicad_pro` and `.kicad_dru` specified 0.120 mm width.
- For 0.5 mm pitch BGA fanout (Apollo510B and eMMC), 0.100 mm trace with 0.100 mm clearance fits comfortably within escape corridors, whereas 0.120 mm trace constrains BGA breakout.
- In `.kicad_dru`: Rule `"High-Speed 50R Netclass Clearance"` updated: `(constraint track_width (min 0.10mm))`.
- In `.kicad_pro`: Netclass `HighSpeed_50R` `"track_width"` updated to `0.1`.
- Live tracks: Verified routed at 0.100 mm.
- Classification label applied: **PROVISIONAL HIGH-SPEED WIDTH — FINAL IMPEDANCE PENDING FABRICATOR FIELD SOLVE**.

---

## 5. Phase 4 — PPG Channel Mapping ECO & 4-Channel Guarded Routing

### 5.1 Architectural Problem & ECO Decision
Independent measurements in Round 2 revealed:
- `D413` (North) $\to$ `U12` (South) = 8.19 mm
- `D414` (South) $\to$ `U12` (South) = 1.80 mm
- `D423` (West) $\to$ `U13` (West) = 3.44 mm
- `D424` (East) $\to$ `U13` (West) = 9.66 mm

Because AFE 1 (`U12`) is placed South and AFE 2 (`U13`) is placed West:
- Mapping `D413` (North) to `U12` (South) forced a North-to-South trace.
- Mapping `D424` (East) to `U13` (West) forced an East-to-West trace.
These two paths intersected in the central optical aperture ($X=100, Y=100$), creating a Jordan curve crossing that prevented planar routing on `B.Cu` without layer hopping through optical keepouts.

### 5.2 Controlled Schematic ECO
Swapping detector channel assignments between `D413` and `D424`:
- `D413` (North) $\to$ connects to `U13` (West AFE) via `PPG2_PD2_IN` / `PPG2_PD_GND` (distance ~7.5 mm).
- `D424` (East) $\to$ connects to `U12` (South AFE) via `PPG1_PD1_IN` / `PPG1_PD_GND` (distance ~6.3 mm).
- `D414` (South) $\to$ remains on `U12` via `PPG1_PD2_IN` / `PPG1_PD_GND` (distance 1.8 mm).
- `D423` (West) $\to$ remains on `U13` via `PPG2_PD1_IN` / `PPG2_PD_GND` (distance 3.4 mm).

This completely untangles the layout into two independent quadrants:
- Northwest Quadrant: `U13` serves `D423` (West) and `D413` (North).
- Southeast Quadrant: `U12` serves `D414` (South) and `D424` (East).

### 5.3 Physical Implementation & Guarding
All 4 detector channels and their dedicated analog ground guards were routed pad-to-pad on `B.Cu`:

1. **AFE 1 (`U12`, South Quadrant):**
   - `PPG1_PD1_IN`: `D424.1` $(101.950, 100.000) \to (101.200, 100.750) \to (101.200, 105.800) \to U12.D5$ $(100.800, 106.200)$.
   - `PPG1_PD2_IN`: `D414.1` $(100.000, 104.450) \to (100.400, 104.850) \to U12.D4$ $(100.400, 106.200)$.
   - `PPG1_PD_GND` Guard: Continuous ground shield connecting `D414.2` $(100.000, 101.950)$ around the north of `D424` to `D424.2` $(104.450, 100.000)$, down along $X=101.800$ to `U12.C5` $(100.800, 106.600)$ and net tie `NT401.1` $(101.300, 108.500)$.
2. **AFE 2 (`U13`, West Quadrant):**
   - `PPG2_PD1_IN`: `D423.1` $(95.550, 100.000) \to (94.500, 100.000) \to (93.500, 99.000) \to (92.500, 98.500) \to U13.D5$ $(92.500, 98.400)$.
   - `PPG2_PD2_IN`: `D413.1` $(100.000, 98.050) \to (99.500, 98.000) \to U13.D4$ $(92.500, 98.000)$.
   - `PPG2_PD_GND` Guard: Dual-shield system:
     - North guard: `D413.2` $(100.000, 95.550) \to (99.150, 96.400) \to (90.200, 96.400) \to NT402.1$ $(91.400, 94.500)$ and `U13.C5` $(92.100, 98.400)$.
     - South guard: `D423.2` $(98.050, 100.000) \to (98.050, 101.200) \to (91.500, 101.200) \to (91.500, 98.700) \to (92.100, 98.700) \to U13.C5$.

---

## 6. Phase 5 — Critical Support Parts Staging & Formal Deferral Mitigation

Per Review Section 21 item 5 and task directives, the support passives currently in staging are formally deferred with the following explicit engineering mitigations:

1. **eMMC Interface Resistors (`R901`–`R910`) and VDDI Capacitors (`C905`, `C906`):**
   - *Rationale:* Placing discrete 0201/0402 components into the central corridor ($X \in [96.0, 104.5]$, $Y \in [98.5, 103.5]$) before final datapath assignment would block routing channels for the remaining unrouted bus signals (`DAT0`–`DAT3`, `DAT7`, `DS`, `RST_N`) and cause courtyard collisions.
   - *Mitigation:* A $4.0 \times 6.0\text{ mm}$ placement corridor on `F.Cu` / `In3.Cu` between `U101` and `U901` is reserved. Resistors and VDDI capacitors will be placed inline simultaneously with full datapath routing in Phase 4.
2. **PPG VLED Decoupling Capacitors (`C403`–`C408`):**
   - *Rationale:* Placing `C403`–`C408` inside the optical core on `B.Cu` would violate optical keepouts and cross-side thermal keepout fields under `U201`/`U202`. Placing them on `F.Cu` without display connector allocation risks collisions with display level shifters (`U102`–`U106`).
   - *Mitigation:* Peripheral 0402 sites on `B.Cu` at radius $R > 12.5\text{ mm}$ adjacent to LED drive FETs (`U402`–`U407`) are reserved and will be placed during LED drive routing.
3. **nPM1300 VBAT Decoupling Capacitor (`C206`):**
   - *Rationale:* `U201` already has all critical buck switching capacitors (`C201`–`C205`, `C207`, `C208`) placed in tight island formation. Attempting to squeeze bulk capacitor `C206` adjacent to `L201` encroaches on thermal keepouts.
   - *Mitigation:* `C206` is reserved for placement along the battery entrance corridor adjacent to `J201`.

---

## 7. Phase 6 — Schematic Residuals Closure

1. **Y101 MPN & Load Capacitors:**
   - MPN: Abracon `ABS07-32.768KHZ-6-T` (32.768 kHz, $C_L = 6.0\text{ pF}$, ESR max 70 kΩ, 3.2 × 1.5 mm).
   - $C_L$ Formula: $C_L = \frac{C_{118} \cdot C_{119}}{C_{118} + C_{119}} + C_{stray} = \frac{C_{ext}}{2} + C_{stray}$.
   - For $C_L = 6.0\text{ pF}$ and estimated PCB stray capacitance $C_{stray} \approx 1.9\text{ pF}$ (2.0 mm traces on F.Cu adjacent to MCU balls): $C_{ext} = 2 \cdot (6.0 - 1.9) = 8.2\text{ pF}$.
   - Schematic updated: `Y101` = `ABS07-32.768KHZ-6-T`, `C118` = `8.2pF`, `C119` = `8.2pF`.
2. **Y102 Load Capacitance (Apollo510B 48 MHz HFXTAL):**
   - Primary Source: Ambiq Apollo510B Reference Manual Table 50 / `MCUCTRL.HFXTALTRIM` register.
   - Finding: The Apollo510B incorporates an internal programmable load capacitance bank on `HFXIN` and `HFXOUT` that can tune load capacitance up to 12 pF per pin, specifically designed to eliminate discrete external load capacitors for crystals with $C_L \le 10\text{ pF}$.
   - Selected Crystal: NDK `NX1612SA-48M-EXS00A-CS14265` ($C_L = 8\text{ pF}$, ESR max 60 Ω). External discrete capacitors are not required. Value updated in `01_APOLLO510B.kicad_sch`.
3. **Y1 Load Capacitance (Nordic nRF7002 40 MHz XTAL):**
   - Primary Source: Nordic Semiconductor nRF7002 Product Specification v1.1 Section 5.1 and PCA10143 Hardware Reference Design.
   - Finding: `XON` and `XOP` pins connect directly to the 40 MHz crystal without external load capacitors; frequency offset calibration is performed via internal OTP capacitive tuning (`XO_TRIM`).
   - Selected Crystal: NDK `NX1612SA-40M-EXS00A-CS14264` ($C_L = 8\text{ pF}$, ESR max 60 Ω). Value updated in `06_WIFI.kicad_sch`.
4. **U8 VCC_RF Pin Connection:**
   - Primary Source: u-blox MAX-F10S Hardware Integration Manual (UBX-22028884) Section 3.1 / MAX-M10S Datasheet (UBX-20035208).
   - Finding: Pin 14 `VCC_RF` is a filtered `VCC` power output intended solely to power an external active antenna or external LNA. For passive antennas (`AE1420` baseline), `VCC_RF` and `LNA_EN` must remain unconnected (NC).
   - Schematic Annotation: Updated explanatory text note in `05_GNSS.kicad_sch` explicitly citing UBX-22028884 Section 3.1.

---

## 8. Final Live Verification Evidence

All tests below were executed against the live committed repository state:

### 8.1 Native KiCad DRC Verification
```bash
flatpak run --command=kicad-cli org.kicad.KiCad pcb drc --severity-all sportwatch_revA.kicad_pcb
```
- **DRC Errors:** **0**
- **DRC Warnings:** **389** (385 cosmetic silkscreen clipping/overlaps + 4 NetTie library mismatches)
- **Unconnected Items:** **499** (expected for foundation stage; remaining unrouted staging nets)
- **Clearance Errors:** 0
- **Hole Clearance Errors:** 0
- **Shorting Items:** 0
- **Solder Mask Bridges:** 0
- **Keepout Violations:** 0
- **Starved Thermals:** 0

### 8.2 Native KiCad ERC Verification
```bash
flatpak run --command=kicad-cli org.kicad.KiCad sch erc --severity-error sportwatch_revA.kicad_sch
```
- **ERC Errors:** **0**

### 8.3 Schematic↔PCB Netlist Parity Audit
```bash
flatpak run --command=kicad-cli org.kicad.KiCad sch export netlist -o netlist.net sportwatch_revA.kicad_sch
```
- **Exit Code:** 0
- **Schematic Components:** 243
- **PCB Footprints:** 228
- **Difference (Schematic Only):** 15 components (exactly the expected Class-C deferred set: `AE1401`, `AE1410`, `AE1420`, `J201`, `J202`, `LRA1`, `SW1`–`SW5`, `TP1401`, `TP1410`, `TP1420`, `U10`).
- **PCB-Only Components:** 0
- **Schematic Named Nets:** 389
- **PCB Named Nets:** 389
- **Net Set Difference:** **0 (Exact match, 389 = 389)**

### 8.4 Live Copper Element Counts
- **Footprints:** 228 (96 inside board outline, 132 in staging)
- **Tracks:** 46 (15 proof tracks on `In2.Cu`, 31 PPG signal and guard tracks on `B.Cu`)
- **Vias:** 24 (12 stacked pairs: 12 `F.Cu -> In1.Cu` L1-L2 + 12 `In1.Cu -> In2.Cu` L2-L3)
- **Zones:** 4 (2 filled copper zones on `In1.Cu` and `In6.Cu`, 2 `B.Cu` thermal keepout rule areas)

---

## 9. Verdict

**FOUNDATION CORRECTION ROUND 3: PASS — READY FOR INDEPENDENT RE-REVIEW**
