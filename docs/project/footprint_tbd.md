# Sportwatch Rev-A Intentionally Deferred Footprints (Class C)

Date: 2026-10-06  
Project: `sportwatch_revA` (Premium Outdoor/Endurance Smartwatch PCBA)  
Baseline: Electrical Schematic Freeze (`7513a3604df232e04ba989ba8716a0611a5fcc08`)  
Native KiCad Engine: KiCad CLI 10.0.5  

---

## 1. Executive Summary

In strict compliance with the project footprint selection policy:
> **"SMALLEST RELIABLE PACKAGE THAT STILL MEETS ELECTRICAL, THERMAL, MECHANICAL, RF, AND MANUFACTURER REQUIREMENTS. Missing/TBD is strictly preferred over guessing unverified footprints."**

Exactly eight (8) components out of 243 have been classified as **Class C (Intentionally TBD)** and retain blank footprint fields in the frozen electrical schematic. None of these blanks represents an overlooked part; every one is an intentional physical boundary item whose exact land pattern depends directly on watch casing mechanics, antenna physical form factors, or RF test chamber tooling.

| Ref | Value | Sheet | Subsystem | Reason for Deferred Footprint Selection |
|---|---|---|---|---|
| **AE1401** | `ANT_BLE_2G4_TBD` | `14_RF` | Bluetooth LE RF | Antenna physical form factor dependent on watch bezel / housing |
| **AE1410** | `ANT_WIFI_2G4_5G_TBD`| `14_RF` | Wi-Fi 2.4/5GHz RF | Dual-band Wi-Fi antenna dependent on case material & bezel slot |
| **AE1420** | `ANT_GNSS_L1_L5_TBD` | `14_RF` | Dual-Band GNSS | GNSS L1/L5 antenna dependent on metal bezel aperture & polarization |
| **TP1401** | `BLE_RF_TEST_TBD` | `14_RF` | Bluetooth LE RF | Test connector vs test pad dependent on lab fixture & production line |
| **TP1410** | `WIFI_RF_TEST_TBD`| `14_RF` | Wi-Fi RF | Test connector vs test pad dependent on lab fixture & production line |
| **TP1420** | `GNSS_RF_TEST_TBD`| `14_RF` | GNSS RF | Test connector vs test pad dependent on lab fixture & production line |
| **U10** | `2.4/5GHz_DIPLEXER_TBD`| `06_WIFI` | Wi-Fi RF Frontend | Exact diplexer package (0605 vs 0805) dependent on RF layout density |
| **LRA1** | `LRA_TBD` | `10_HAPTICS` | Haptic Driver | Actuator motor dimensions dependent on case mechanical cavity & bracket |

---

## 2. Detailed Technical Breakdown & Resolution Plan

### 2.1 Antennas (AE1401, AE1410, AE1420)
- **Circuit Context:**
  - `AE1401`: 2.4 GHz Bluetooth Low Energy antenna port on Ambiq Apollo510B (pin N1).
  - `AE1410`: Dual-band 2.4 GHz / 5 GHz Wi-Fi 6 antenna port on Nordic nRF7002 (via diplexer U10).
  - `AE1420`: Dual-band L1 (1575.42 MHz) and L5 (1176.45 MHz) GNSS antenna port on u-blox MAX-F10S.
- **Why Footprint is Deferred:**
  In a 49–52 mm outdoor sports watch with a metallic bezel or titanium case ring, antennas are rarely off-the-shelf ceramic chip antennas placed arbitrarily on the main PCB. Wearable endurance antennas typically take one of three mechanical architectures:
  1. **Laser Direct Structuring (LDS) or Flex PCB Antenna:** Antenna radiator is plated directly onto the inside of the composite watch chassis or an FPC adhering to the bezel, contacted via spring finger / pogo pins to PCB feed pads.
  2. **Slot / Bezel Antenna:** The external metallic bezel itself serves as the antenna element, fed via a matching contact pad at the board periphery.
  3. **Miniature Ceramic / Virtual Antenna:** SMD components like Ignion NN01-105 (Virtual Antenna) or Johanson 2450AT series, requiring specific board clearance (keepout) zones.
- **Candidate Solutions:**
  - If LDS / Bezel Contact: 2-pad SMD spring-finger contact land pattern (e.g. `sportwatch_custom:Antenna_FeedContact_1.5x2.0mm`).
  - If SMD Chip Antenna: Ignion `ROUTER` (40x10mm virtual) or Johanson `2450AT18D0100` (3.2x1.6mm) / Taoglas `WLA.01` (3.2x1.6mm).
- **Resolution Gate:**
  Resolve once watch housing CAD and bezel material selection (titanium vs composite) are frozen with mechanical engineering.

---

### 2.2 RF Test Points / Coaxial Switches (TP1401, TP1410, TP1420)
- **Circuit Context:**
  RF conducted testing points inserted between the matching networks and the antenna feed lines for BLE, Wi-Fi, and GNSS.
- **Why Footprint is Deferred:**
  The physical footprint depends directly on the manufacturing test methodology:
  1. **Option A (Conducted RF Micro-Coaxial Switch):** Murata `MM8030-2610` (SWF series) or Hirose `MS-156NB`. These switches automatically disconnect the internal antenna and route RF energy into a connected probe during production calibration and certification. Footprint is ~2.0 x 2.0 mm.
  2. **Option B (RF Test Pad Array):** Ground-Signal-Ground (GSG) surface pads for manual micro-coax pigtail soldering or high-frequency automated spring probes. Footprint is ~1.5 x 1.0 mm.
- **Resolution Gate:**
  Resolve upon agreement with PCBA test engineering on the factory RF calibration fixture and probe station.

---

### 2.3 Wi-Fi 2.4/5GHz Diplexer (U10)
- **Circuit Context:**
  Nordic nRF7002 dual-band Wi-Fi companion IC frontend. Separates/combines 2.4 GHz (802.11b/g/n/ax) and 5 GHz (802.11a/n/ac/ax) RF paths into a single antenna port (AE1410).
- **Why Footprint is Deferred:**
  - Candidate parts exist in two primary standard miniature packages:
    - **0605 Metric (1.6 x 0.8 x 0.6 mm, 6-pad):** Murata `LFD182G45DP3C223` / TDK `DPX165950DT-8126A1`.
    - **0805 Metric (2.0 x 1.25 x 0.95 mm, 6-pad):** Murata `LFD212G45DP1A220`.
  - The electrical symbol in `06_WIFI.kicad_sch` provides standard 6-pin connectivity (Pin 1: GND, Pin 2: COM/ANT, Pin 3: GND, Pin 4: 5GHz, Pin 5: GND, Pin 6: 2.4GHz).
  - Pinout is uniform across both packages; footprint assignment is deferred until RF layout density and keepout spacing around the nRF7002 QFN48 are established during preliminary PCB floorplanning.
- **Candidate Footprints:**
  - `sportwatch_custom:Diplexer_0605_1.6x0.8mm_6Pad`
  - `sportwatch_custom:Diplexer_0805_2.0x1.25mm_6Pad`

---

### 2.4 Linear Resonant Actuator (LRA1)
- **Circuit Context:**
  Haptic feedback actuator driven by TI DRV2625 (U7).
- **Why Footprint is Deferred:**
  - LRAs are electro-mechanical vibration motors that deliver premium haptic sensation in endurance watches.
  - Form factors vary widely depending on available internal chassis volume:
    - **Coin / Disc Type (Z-axis vibration):** e.g., Jinlong Z-axis 0832 (D8.0 x 3.2 mm) or 1030 (D10.0 x 3.0 mm), typically mounted into a chassis pocket and connected to the PCB via 2 spring contacts or a flexible lead wire soldered to surface pads.
    - **Bar / Rectangular Type (X/Y-axis vibration):** e.g., KEMET / AAC linear vibrator (12.0 x 4.0 x 3.5 mm), offering stronger lateral g-force.
- **Candidate Footprint:**
  - 2-pad SMD spring contact pad array (e.g. `sportwatch_custom:HapticContact_2Pad_1.5x2.0mm_P3.0mm`) or 2-pin SMD FPC connector.
- **Resolution Gate:**
  Resolve upon completion of industrial design haptic feel evaluations and battery/chassis internal cavity layout.

---

## 3. Summary of Design Readiness

With exactly 235 components assigned and verified, and only these 8 Class C components intentionally deferred, the PCBA is in an optimal state for physical floorplanning:
- All critical ICs, optics, sensors, power converters, crystals, connectors, and switching inductors have 100% verified footprint geometry.
- The 8 Class C components are documented with clear boundary conditions and candidate footprints, ready to be resolved seamlessly without requiring any schematic topology or netlist changes.
