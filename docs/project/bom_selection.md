# Sportwatch Rev-A Consolidated BOM & Component Selection

Date: 2026-10-06  
Project: `sportwatch_revA` (Premium Outdoor/Endurance Smartwatch PCBA)  
Baseline: Electrical Schematic Freeze (`7513a3604df232e04ba989ba8716a0611a5fcc08`)  
Native KiCad Engine: KiCad CLI 10.0.5  

---

## 1. Subsystem BOM & Primary MPN Selection

### 1.1 Microcontroller, Storage & Level Translation
| Designator | Value / Function | Exact MPN | Manufacturer | Package / Footprint | Ratings & Key Specifications |
|---|---|---|---|---|---|
| **U101** | Ultra-Low-Power MCU | `AP510BFA-CBR` | Ambiq Micro | WFBGA-153 (5.6x5.6mm, 0.4mm pitch) | Cortex-M55 + Helium + GPU, 250MHz, 3.75MB SRAM, SIMO buck, 1.71–2.2V |
| **U901** | 64GB eMMC 5.1 Storage | `EMMC64G-TB9F-06011` | Kingston Digital | FBGA-153 (8.0x8.5x0.8mm, 0.5mm pitch) | HS400 dual-voltage (1.8V VCCQ / 3.3V VCC), 400MB/s, compact wearable pkg |
| **U102** | 8-Bit Level Translator | `SN74AXC8T245RHLR` | Texas Instruments | VQFN-24 (3.5x5.5mm, 0.5mm pitch, EP) | Dual-supply 0.65–3.6V translator, eMMC bus isolation, tri-state |
| **U103** | 1-Bit Auto-Dir Translator | `TXB0101DRLR` | Texas Instruments | SOT-583-6 / SOT-563 (1.6x1.2mm, 0.5mm) | 1.2–3.6V / 1.65–5.5V auto-direction push-pull translator |
| **U104** | 1-Bit Directional Translator | `SN74AXC1T45DRLR` | Texas Instruments | SOT-583-6 / SOT-563 (1.6x1.2mm, 0.5mm) | 0.65–3.6V dual-rail level shifter |
| **U105** | 1-Bit Directional Translator | `SN74AXC1T45DRLR` | Texas Instruments | SOT-583-6 / SOT-563 (1.6x1.2mm, 0.5mm) | 0.65–3.6V dual-rail level shifter |
| **U106** | Dual Bidirectional I2C Switch | `PCA9306DCUR` | Texas Instruments | VSSOP-8 (2.3x2.0mm, 0.5mm pitch) | Voltage translator / bus repeater for sensor I2C |

### 1.2 Power Management & Voltage Regulators
| Designator | Value / Function | Exact MPN | Manufacturer | Package / Footprint | Ratings & Key Specifications |
|---|---|---|---|---|---|
| **U201** | Advanced Wearable PMIC | `nPM1300-QEAA-R` | Nordic Semi | QFN-32-1EP (5.0x5.0mm, 0.5mm pitch) | Dual 200mA BUCKs, dual 50mA LDOs, 800mA Linear Charger, Fuel Gauge |
| **U202** | High-Efficiency Buck-Boost | `TPS63900DSCR` | Texas Instruments | WSON-10-1EP (2.5x2.5mm, 0.5mm pitch) | 1.8–5.5V in, 400mA out, 75nA ultra-low Iq, dynamic voltage scaling |
| **U401** | High-Current LED Buck-Boost | `TPS631000DRLR` | Texas Instruments | SOT-583-8 (1.6x2.1mm, 0.5mm pitch) | 1.6–5.5V in, up to 1.5A out, 2MHz switching, VOUT=3.82V for PPG LEDs |
| **U11** | Smart Load Switch | `TPS22918DBVR` | Texas Instruments | SOT-23-6 (2.9x1.6mm, 0.95mm pitch) | 2A continuous, 50mΩ Ron, controlled slew-rate for display 3.3V rail |

### 1.3 Power Inductors
| Designator | Nominal Inductance | Exact MPN | Manufacturer | Package / Footprint | Saturation Current | Max DCR | Switching Freq / Role |
|---|---|---|---|---|---|---|---|
| **L101** | 2.2 µH | `LSCND1608HKT2R2MF` | Taiyo Yuden | 0603 (1.6x0.8x0.8mm) | 1.30 A | 250 mΩ | Apollo510B SIMO Core Buck (Ambiq Table 34) |
| **L201** | 2.2 µH | `LSCND1608HKT2R2MF` | Taiyo Yuden | 0603 (1.6x0.8x0.8mm) | 1.30 A | 250 mΩ | nPM1300 BUCK1 (1.8V System Core Rail) |
| **L202** | 2.2 µH | `LSCND1608HKT2R2MF` | Taiyo Yuden | 0603 (1.6x0.8x0.8mm) | 1.30 A | 250 mΩ | nPM1300 BUCK2 (3.0V Sensor/Provisional Rail) |
| **L203** | 2.2 µH | `DFE201612E-2R2M=P2` | Murata | 2016 (2.0x1.6x1.2mm) | 2.40 A | 116 mΩ | TPS63900 Buck-Boost (SYS_3V3 System Rail) |
| **L401** | 1.0 µH | `HTEK20161T-1R0MSR` | Cyntec | 2016 (2.0x1.6x1.0mm) | 4.20 A | 43 mΩ | TPS631000 PPG_VLED (High-current LED Strobe) |
| **L601** | 3.3 µH | `DFE201612E-3R3M=P2` | Murata | 2016 (2.0x1.6x1.2mm) | 1.70 A | 180 mΩ | nRF7002 Internal Buck (Nordic BOM Table 14.3) |
| **L1401** | 1.5 nH | `LQP03TN1N5B02D` | Murata | 0201 (0.6x0.3x0.3mm) | 850 mA | 100 mΩ | BLE RF Matching Network (High-Q, SRF > 15GHz) |
| **L1402** | 1.8 nH | `LQP03TN1N8B02D` | Murata | 0201 (0.6x0.3x0.3mm) | 800 mA | 120 mΩ | BLE RF Matching Network (High-Q, SRF > 14GHz) |

### 1.4 Optical Front-End & PPG Emitters / Detectors
| Designator | Value / Function | Exact MPN | Manufacturer | Package / Footprint | Ratings & Key Specifications |
|---|---|---|---|---|---|
| **U12, U13** | Dual Optical AFE | `MAX86141ENP+T` | Analog Devices / Maxim | 20-WLP (2.05x1.85mm, 0.4mm pitch) | Dual optical readout, 3 LED drivers up to 250mA, 19-bit ADC |
| **U402..U407** | SPDT Analog Mux (6x) | `TS5A12301EYFPR` | Texas Instruments | 6-DSBGA (0.76x1.16mm, 0.4mm pitch) | 0.75Ω Ron, break-before-make, low distortion, LED bank multiplexing |
| **D401..D404** | BIOFY Multi-Emitter (4x) | `SFH 7018A` (Q65113A6157) | ams OSRAM | Custom 8-Pad (2.4x2.4x0.6mm) | 3x Green (530nm), 1x Red (660nm), 1x IR (940nm) high-radiance dies |
| **D405..D407** | Discrete IR Emitter (3x) | `SFH 4053B` (Q65115A1586) | ams OSRAM | 0402 SMD (1.0x0.5x0.45mm) | 850 nm high-efficiency IR ChipLED for optical path diversity |
| **D413, D414, D423, D424** | PIN Photodiode (4x) | `SFH 2703H` (Q65115A2199) | ams OSRAM | 2-Pad SMD (3.2x2.0x0.6mm) | High sensitivity, radiant sensitive area 2.72mm², 400–1100nm |

### 1.5 Motion, Environmental & Thermal Sensors
| Designator | Value / Function | Exact MPN | Manufacturer | Package / Footprint | Ratings & Key Specifications |
|---|---|---|---|---|---|
| **U702** | 6-Axis IMU (Acc + Gyro) | `LSM6DSV16XTR` | STMicroelectronics | 14-LGA (2.5x3.0x0.83mm, 0.5mm) | Qvar electrostatic sensor, sensor fusion, 0.65mA high-perf mode |
| **U703** | 3-Axis Magnetometer | `BMM350` | Bosch Sensortec | 9-WLCSP (1.28x1.28x0.5mm, 0.4mm) | TMR technology, field range ±2000µT, autonomous flux guide reset |
| **U4** | Barometric Pressure Sensor | `BMP585` | Bosch Sensortec | 9-LGA (3.25x3.25x0.8mm, 0.8mm) | Gel-filled water resistant, ±0.08 hPa relative accuracy |
| **U5** | Ambient Light Sensor (ALS) | `OPT4001DTS` | Texas Instruments | 8-SOT-5X3 (0.84x1.05x0.45mm, 0.4mm) | Human eye matching, 28-bit dynamic range (312µlux to 83klux) |
| **U6** | High-Accuracy Skin Temp | `MAX30208ECL+T` | Analog Devices / Maxim | 6-LGA (2.0x2.0x0.75mm, 0.65mm) | Clinical temperature accuracy ±0.1°C (35.8°C to 41.0°C), thermal pad contact |

### 1.6 Wireless Companions & Crystals
| Designator | Value / Function | Exact MPN | Manufacturer | Package / Footprint | Ratings & Key Specifications |
|---|---|---|---|---|---|
| **U8** | Multi-Band GNSS Receiver | `MAX-F10S-00B` | u-blox | 18-LGA (9.7x10.1x2.5mm, 1.1mm) | Dual-band L1/L5 concurrent GNSS (GPS, GLONASS, Galileo, BeiDou, NavIC) |
| **U9** | Wi-Fi 6 Companion IC | `NRF7002-QFAA-R7` | Nordic Semi | QFN-48-1EP (6.0x6.0mm, 0.4mm pitch) | 2.4/5GHz dual-band Wi-Fi 6 companion, Station/AP, OFDMA, TWT |
| **Y1** | 40.000 MHz Wi-Fi Crystal | `NX1612SA-40M-EXS00A-CS14264` | NDK | 1612-4Pin (1.6x1.2mm, lid grounded) | 40 MHz, CL=8 pF, ESR <= 100 Ω, ±10 ppm stability (Nordic Table 14.3) |
| **Y101** | 32.768 kHz RTC Crystal | `ABS07-32.768KHZ-T` / `FC-12M` | Abracon / Epson | 2012-2Pin (2.0x1.2x0.6mm) | 32.768 kHz, CL=6 pF, ESR <= 90 kΩ (Ambiq Table 49) |
| **Y102** | 48.000 MHz MCU Crystal | `NX1612SA-48M-EXS00A-CS14265` | NDK | 1612-4Pin (1.6x1.2mm, lid grounded) | 48 MHz, CL=10 pF, ESR <= 60 Ω, on-chip trim (Ambiq Table 50) |

### 1.7 User Interface, Haptics & Connectors
| Designator | Value / Function | Exact MPN | Manufacturer | Package / Footprint | Ratings & Key Specifications |
|---|---|---|---|---|---|
| **J1** | 24-Pin AMOLED FPC Header | `OK-23GF024-04` | Jinlong / Oupiin | 24-Pin SMD Header (0.35mm pitch) | Jiangxi Huaersheng ZC-A1D43W-046 1.43" AMOLED display interface |
| **J1301** | SWD Debug Programming | `TC2030-CTX-NL` | Tag-Connect | 6-Pin No-Legs Target (P1.27mm) | 6-pin zero-component-cost SWD footprint with alignment pins |
| **J201** | Battery Power Interface | `BATTERY_3PIN` (Class C candidate) | Wearable SMT Pad / FPC | (Blank / TBD) | Candidate: `sportwatch_custom:BatteryPad_3Pin_SMD`; deferred to pouch cell procurement |
| **J202** | Magnetic Pogo Charge Interface | `POGO_2PIN` (Class C candidate) | Wearable SMT Pad | (Blank / TBD) | Candidate: `sportwatch_custom:PogoPad_2Pin_SMD`; deferred to dock puck tooling |
| **SW1..SW5** | 5x Tactile Push Buttons | `EVQP7A04M` (Class C candidate) | Panasonic | (Blank / TBD) | Candidate: `Button_Switch_SMD:SW_SPST_EVQP7A`; deferred to 3D enclosure CAD & plunger specs |
| **U7** | LRA Haptic Driver | `DRV2625YFFR` | Texas Instruments | 9-DSBGA (1.5x1.5mm, 0.5mm pitch) | Ultra-low latency closed-loop LRA/ERM driver with smart-loop waveform |
| **LRA1** | Linear Resonant Actuator | `LRA_TBD` (Class C) | TBD | Chassis Bracket Mount | Deferred to chassis mechanical envelope (docs/project/footprint_tbd.md) |
| **NT201..NT402** | Ground / Shield Net Ties | `NetTie-2_SMD_Pad0.5mm` | PCB Copper Tie | 2-Pad SMD 0.5mm | Galvanic isolation / controlled single-point tie between GND & PD_GND |

---

## 2. Capacitor Policy & DC-Bias Derating Verification

Per project policy, all ceramic capacitors were audited for effective capacitance at nominal operating bias:

| Rail | Nominal Voltage | Cap Ref | Nominal Value | Case Size | Dielectric & Voltage Rating | Derating at DC Bias | Effective Capacitance | Requirement & Margin |
|---|---|---|---|---|---|---|---|---|
| **VBAT / Input** | 3.8 V | C401 | 22 µF | 0603 | X5R 10V (Murata GRM188R61A226M) | -48% @ 3.8V | **~11.4 µF** | TPS631000 VIN requires >= 4.7µF (Margin: 242%) |
| **PPG_VLED** | 3.82 V | C402 | 47 µF | 0805 | X5R 10V (Murata GRM21BR61A476M) | -52% @ 3.82V | **~22.5 µF** | TPS631000 VOUT requires >= 15µF (Margin: 150%) |
| **VSYS (PMIC)** | 3.8 V | C202, C203, C204 | 10 µF (3x) | 0603 | X5R 10V (Murata GRM188R61A106K) | -42% @ 3.8V | **~5.8 µF ea (17.4 µF tot)** | nPM1300 VSYS requires >= 10µF (Margin: 174%) |
| **VOUT1_1V8** | 1.8 V | C207 | 10 µF | 0603 | X5R 10V (Murata GRM188R61A106K) | -22% @ 1.8V | **~7.8 µF** | nPM1300 BUCK1 requires >= 4.0µF (Margin: 195%) |
| **VOUT2_3V0** | 3.0 V | C208 | 10 µF | 0603 | X5R 10V (Murata GRM188R61A106K) | -35% @ 3.0V | **~6.5 µF** | nPM1300 BUCK2 requires >= 4.0µF (Margin: 162%) |
| **BMM_CRST** | 2.5 V pulse | C705 | 2.2 µF | 0805 | X7R 6.3V (TDK CGB4B3X7R0J225K) | -15% @ 2.5V | **~1.87 µF** | BMM350 Ch.13 requires low-ESR 0805 non-magnetic |
| **SYS_3V3** | 3.3 V | C215 | 22 µF | 0603 | X5R 10V (Murata GRM188R61A226M) | -45% @ 3.3V | **~12.1 µF** | TPS63900 VOUT requires >= 10µF (Margin: 121%) |
| **VBUSIN** | 5.0 V | C201 | 1.0 µF | 0402 | X7R 16V (Murata GRM155R71C105K) | -38% @ 5.0V | **~0.62 µF** | nPM1300 VBUS input requires >= 0.47µF |
| **VOUT1_1V8** | 1.8 V | C206 | 2.2 µF | 0402 | X5R 10V (Murata GRM155R61A225K) | -25% @ 1.8V | **~1.65 µF** | General decoupling |
| **Local Bypass**| 1.8V / 3.3V| 100 nF (60x) | 100 nF | 0402 | X7R 16V (Murata GRM155R71C104K) | -8% @ 3.3V | **~92 nF** | High-frequency IC decoupling |
| **RF Decoupling**| 1.8V / 3.3V| 0201 caps (24x)| Various | 0201 | X5R/C0G 10V (Murata GRM033) | RF tuned | **Tuned** | Low-parasitic RF decoupling / matching |
