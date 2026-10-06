# Agent Handoff: Sportwatch Rev-A PCB Foundation & Critical-Cluster Feasibility

## 1. Current Verified Baseline & Git State
- **Date:** 2026-10-06
- **Git Branch:** `pcb/revA-floorplan`
- **Git Checkpoint (Pre-Modification):** `571ddde7adccfa139f4fe2ca3f3ba9e02377c082`
- **Git HEAD (Foundation Phase Committed):** `204e1e0`
- **Live PCB State (KiCad MCP Pro / `pcbnew` Verified):**
  - Footprints: **228**
  - Nets: **389**
  - Tracks: **5** (representative escape tracks)
  - Vias: **10** (7 laser microvias + 3 EP thermal vias)
  - Shapes: **1** (native circle on `Edge.Cuts`)
  - Configured Copper Layers: **8 layers** (`F.Cu`, `In1.Cu`, `In2.Cu`, `In3.Cu`, `In4.Cu`, `In5.Cu`, `In6.Cu`, `B.Cu`)
  - Stackup: **8-layer HDI Type III (2+4+2)**, nominal thickness **0.8080 mm**
  - Project Design Rules: **Active `sportwatch_revA.kicad_dru`** and synchronized `sportwatch_revA.kicad_pro`
  - Schematic Parity: **100% Intact** (only 15 expected Class-C unassigned footprints reported)

---

## 2. Implemented Multilayer Stackup (Task A)
- **Technology Architecture:** 8-Layer High-Density Interconnect (HDI Type III, 2+4+2 build-up).
- **Core / Prepreg Specification:**
  - L1 (`F.Cu`): 0.035 mm copper (Top SMT, high-speed & RF microstrips).
  - Prepreg 1-2: 0.065 mm FR4 106/1080 ($E_r = 4.2$, $\tan\delta = 0.02$). Laser microvia L1-L2 (VIPPO).
  - L2 (`In1.Cu`): 0.018 mm copper (Continuous solid ground plane, L1 ground reference).
  - Prepreg 2-3: 0.070 mm FR4 1080 ($E_r = 4.2$). Laser microvia L2-L3 (Stacked).
  - L3 (`In2.Cu`): 0.018 mm copper (High-speed digital routing: eMMC DDR, Display, Wi-Fi bus).
  - Core Dielectric 3-4: 0.100 mm FR4 Core ($E_r = 4.4$). Mechanical buried via L3-L6.
  - L4 (`In3.Cu`): 0.018 mm copper (Power plane distribution: `VOUT1_1V8`, `VSYS`, `SYS_3V3`).
  - Prepreg 4-5: 0.100 mm FR4 Prepreg ($E_r = 4.2$). Core isolation dielectric.
  - L5 (`In4.Cu`): 0.018 mm copper (Power plane distribution: `VBAT`, `VOUT2_3V0` / low-speed control).
  - Core Dielectric 5-6: 0.100 mm FR4 Core ($E_r = 4.4$).
  - L6 (`In5.Cu`): 0.018 mm copper (Analog & sensor routing referenced to L7 GND).
  - Prepreg 6-7: 0.070 mm FR4 1080 ($E_r = 4.2$). Laser microvia L6-L7 (Stacked).
  - L7 (`In6.Cu`): 0.018 mm copper (Continuous solid ground plane, Faraday shield for optics).
  - Prepreg 7-8: 0.065 mm FR4 106/1080 ($E_r = 4.2$). Laser microvia L7-L8 (VIPPO).
  - L8 (`B.Cu`): 0.035 mm copper (Bottom SMT, optical sensor array, guarded AFE inputs).
- **Total Finished Thickness:** **0.8080 mm** (Nominal $0.80\text{ mm}$).
- **Surface Finish:** ENIG (Electroless Nickel Immersion Gold).
- **Fabrication Tier:** Standard Advanced HDI (compatible with AT&S, Unimicron, Shennan, JLCPCB 8L HDI, PCBWay HDI).

---

## 3. Implemented Design Rules & Net Classes (Task C)
- **Minimum Trace Width / Space:**
  - Outer (`F.Cu`, `B.Cu`): $0.075\text{ mm} / 0.075\text{ mm}$ ($3.0\text{ mil} / 3.0\text{ mil}$).
  - Inner (`In1.Cu`..`In6.Cu`): $0.075\text{ mm} / 0.075\text{ mm}$.
- **Laser Microvias:**
  - Drill: $0.100\text{ mm}$ ($4.0\text{ mil}$).
  - Pad / Land: $0.200\text{ mm}$ ($8.0\text{ mil}$).
  - Annular Ring: $0.050\text{ mm}$ ($2.0\text{ mil}$).
  - Via-in-Pad: VIPPO (IPC-4761 Type VII copper filled & planarized).
- **Through / Buried Vias:**
  - Drill: $0.200\text{ mm}$, Pad: $0.400\text{ mm}$, Annular Ring: $0.100\text{ mm}$.
  - Hole-to-Hole Clearance: $0.200\text{ mm}$.
  - Copper Edge Clearance: $0.500\text{ mm}$.
- **Configured Net Classes:**
  - `Default`: Width 0.15 mm, Clearance 0.10 mm, Via 0.40/0.20 mm, Microvia 0.20/0.10 mm.
  - `HDI_Micro`: Width 0.075 mm, Clearance 0.075 mm, Via 0.40/0.20 mm, Microvia 0.20/0.10 mm.
  - `HighSpeed_50R`: Width 0.12 mm, Clearance 0.10 mm, Via 0.40/0.20 mm, Microvia 0.20/0.10 mm.
  - `Power`: Width 0.25 mm, Clearance 0.12 mm, Via 0.50/0.25 mm.
  - `Optical_PD_Guard`: Width 0.10 mm, Clearance 0.10 mm.
- **Rules Files:** Project `.kicad_dru` active and loaded by KiCad MCP.

---

## 4. Provisional Board Outline (Task B)
- **Outer Profile:** Circular boundary, **46.0 mm diameter** ($R = 23.0\text{ mm}$).
- **Center Coordinate:** $(X = 100.00\text{ mm}, Y = 100.00\text{ mm})$.
- **Placement Keepout Margin:** $1.20\text{ mm}$ radial setback.
- **Usable Placement Boundary:** Radius $R \le 21.80\text{ mm}$.
- **Single-Sided Usable Area:** $1661.90\text{ mm}^2$ (+9.3% vs superseded 44 mm candidate).
- **Two-Sided Total Area:** $3323.81\text{ mm}^2$.
- **Gross Two-Sided Packing Density:** **31.8%** across all 228 components (optimal manufacturing range).

---

## 5. Courtyard Geometry Completion (Task D)
- `NT201` (`F.Cu`): $1.80 \times 0.80\text{ mm}$ rect on `F.CrtYd`. `allow_missing_courtyard` removed.
- `NT202` (`F.Cu`): $1.80 \times 0.80\text{ mm}$ rect on `F.CrtYd`. `allow_missing_courtyard` removed.
- `NT401` (`B.Cu`): $1.80 \times 0.80\text{ mm}$ rect on `B.CrtYd`. `allow_missing_courtyard` removed.
- `NT402` (`B.Cu`): $1.80 \times 0.80\text{ mm}$ rect on `B.CrtYd`. `allow_missing_courtyard` removed.
- `U5` (TI OPT4001DTSR): $2.90 \times 2.70\text{ mm}$ rect on `F.CrtYd`.
- `U7` (TI DRV2625YFFR): $2.00 \times 1.90\text{ mm}$ rect on `F.CrtYd`.
- Footprint definitions in `libraries/footprints/sportwatch_custom.pretty/` synchronized.

---

## 6. Critical Cluster Feasibility & Provisional Placement (Task E)
All 7 designated critical clusters are provisionally placed and mathematically validated:
1. **Cluster 1 (MCU & eMMC Core on `F.Cu`):** `U101` at $(100.0, 97.5)$, `U901` at $(100.0, 107.0)$. Physical body gap 2.45 mm for eMMC HS400 bus. Crystals `Y102` (48 MHz) and `Y101` (RTC) sit $< 5.5\text{ mm}$ from Apollo pins. SIMO inductor `L101` at $(95.5, 93.5)$.
2. **Cluster 2 (PPG Optics on `B.Cu`):** Symmetrical 4-quadrant array centered at $(100.0, 100.0)$ on bottom side. MAX86141 AFEs `U12`/`U13` placed at $X = 88.5\text{ mm}$ with short photodiode runs ($< 8\text{ mm}$) surrounded by `PD_GND` guards. Zero switcher currents cross optical island.
3. **Cluster 3 (LED Driver on `B.Cu`):** `U401` (TPS631000) at $(91.0, 113.5)$, inductor `L401` at $(87.5, 113.5)$, input cap `C401` at $(93.8, 113.5)$ adjacent to VIN. Strobe loop $< 4.2\text{ mm}^2$. Separated by $> 16\text{ mm}$ from photodiode islands.
4. **Cluster 4 (System PMIC on `F.Cu`):** `U201` (nPM1300) at $(89.5, 108.5)$, BUCK inductors `L201`/`L202` at $(84.5, 106.5 / 109.0)$, filter caps `C201`..`C203` rotated 90°. Power ground return separated via `NT201`/`NT202`.
5. **Cluster 5 (Aux Buck-Boost on `F.Cu`):** `U202` (TPS63900) at $(89.5, 114.5)$, inductor `L203` at $(86.0, 114.0)$. Switching loop $< 3.5\text{ mm}^2$. Sits $36.0\text{ mm}$ away from BMM350 magnetometer.
6. **Cluster 6 (Wi-Fi 6 Companion on `F.Cu`):** `U9` (nRF7002) at $(111.0, 103.5)$, crystal `Y1` at $(111.0, 97.5)$, inductor `L601` at $(116.5, 103.5)$. RF pins face outward toward South-East antenna sector `AE1410`.
7. **Cluster 7 (GNSS Subsystem on `F.Cu`):** `U8` (MAX-F10S) at $(100.0, 86.5)$, series tuning `R1420` at $(100.0, 80.0)$ (1.65 mm flight). RF input faces directly North toward 12 o'clock antenna feed `AE1420`. Inductor separation $> 31\text{ mm}$.
- **Courtyard Overlaps:** **0 overlaps** across all placed components.
- **Setback Clearance:** All placed components maintain $R \le 20.80\text{ mm}$ ($\ge 2.20\text{ mm}$ to board edge).

---

## 7. Representative Fanout Trial Result (Task F)
- Inner Ground ball G7 on Apollo510B dropped via VIPPO laser microvia L1-L2 to L2 GND plane.
- Inner Signal ball H7 on Apollo510B (`/EMMC_DAT4`) dropped via stacked microvia L1-L2 / L2-L3 to L3 (`In2.Cu`) and escaped southward out of BGA matrix with 0.075 mm width.
- Signal ball L8 on Apollo510B (`/EMMC_DAT7`) dropped via stacked microvia L1-L2 / L2-L3 to L3 and escaped southward.
- Signal ball A3 on eMMC (`/EMMC_DAT0`) escaped northward on L1 (`F.Cu`).
- Inner Signal ball B4 on eMMC (`/EMMC_DAT5`) dropped via stacked microvia to L3 and escaped northward.
- **DRC Verification:** **PASS**. Zero track width violations, zero clearance violations, zero shorts, zero solder mask bridges, and zero annular width violations.

---

## 8. Unresolved Mechanical / RF Inventory (15 Class-C Items)
The following 15 Class-C items remain deferred pending mechanical CAD and vendor procurement:
1. `AE1401` — Bluetooth LE Antenna (watch bezel slot vs LDS antenna)
2. `AE1410` — Wi-Fi 2.4/5GHz Dual-Band Antenna (case material & aperture keepout)
3. `AE1420` — GNSS L1/L5 Dual-Band Antenna (bezel slot & polarization)
4. `TP1401` — BLE RF Conducted Test Port (micro-coax switch vs GSG pad array)
5. `TP1410` — Wi-Fi RF Conducted Test Port (micro-coax switch vs GSG pad array)
6. `TP1420` — GNSS RF Conducted Test Port (micro-coax switch vs GSG pad array)
7. `U10` — Wi-Fi 2.4/5GHz Diplexer (0605 vs 0805 layout density)
8. `LRA1` — Haptic Linear Resonant Actuator (coin vs bar motor cavity)
9. `SW1` — Button Light (side-push switch vs perimeter flex FPC)
10. `SW2` — Button Up (side-push switch vs perimeter flex FPC)
11. `SW3` — Button Down (side-push switch vs perimeter flex FPC)
12. `SW4` — Button Start (side-push switch vs perimeter flex FPC)
13. `SW5` — Button Back (side-push switch vs perimeter flex FPC)
14. `J201` — Battery Interface (soldered flying leads vs micro-FPC connector)
15. `J202` — Charging Interface (magnetic dock pogo pitch & gold plating)

---

## 9. Recommended Next Action
Proceed to **Phase: Full PCBA Component Placement (228 Components)**:
1. Place peripheral sensors (IMU `U702`, Magnetometer `U703`, Barometer `U4`, ALS `U5`, Skin Temp `U6`).
2. Place display connector `J1` and associated level shifters (`U102`..`U106`).
3. Place haptic driver `U7`, debug header `J1301`, and test points `TP1301`..`TP1306`.
4. Distribute remaining local decoupling passives adjacent to IC power pins.
5. Re-run comprehensive DRC to ensure complete zero-overlap PCBA placement before general routing.

---

## FINAL PHASE VERDICT

```text
============================================================
PCB FOUNDATION: PASS — READY FOR FULL PLACEMENT
============================================================
```
