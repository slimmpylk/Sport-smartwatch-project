# Sportwatch Rev-A Footprint Assignment & Change Log

Date: 2026-10-06  
Project: `sportwatch_revA` (Premium Outdoor/Endurance Smartwatch PCBA)  
Baseline: Electrical Schematic Freeze (`7513a3604df232e04ba989ba8716a0611a5fcc08`)  
Native KiCad Engine: KiCad CLI 10.0.5  

---

## 1. Scope of Changes

This log documents all footprint modifications applied to the electrical schematics of `sportwatch_revA` during the formal footprint audit and assignment phase.

### Key Rules Strictly Observed:
1. **Zero Netlist / Connectivity Changes:** No nets, wires, symbol pins, hierarchical labels, or sheet pins were altered. All 389 electrical nets compare identically against the baseline.
2. **PCB File Untouched:** `sportwatch_revA.kicad_pcb` was **NOT modified**; PCB routing, placement, outline, and stackup work remain unstarted.
3. **No Guessed Footprints:** All assignments trace directly to manufacturer drawings, reference designs, or established project passive policy rules.

---

## 2. New Project-Local Footprints Created

Ten (10) custom footprints were designed and added to `${KIPRJMOD}/libraries/footprints/sportwatch_custom.pretty`:

| Footprint Name | Target Component | Package Type / Dimensions | Source / Datasheet Reference |
|---|---|---|---|
| `BGA-153_5.6x5.6mm_Layout13x13_P0.4mm_Ball0.25mm_Pad0.22mm_NSMD` | U101 (Ambiq Apollo510B) | WFBGA-153 (5.6x5.6mm, 0.4mm pitch) | Ambiq DS-A510B-1p1p0 Figure 56 (13x13 grid, 16 depopulated balls) |
| `FBGA-153_8.0x8.5mm_Layout14x14_P0.5mm` | U901 (Kingston eMMC 64GB) | FBGA-153 (8.0x8.5x0.8mm, 0.5mm pitch) | Kingston EMMC64G-TB9F-06011 datasheet Page 11 (Corrected from 11.5x13mm) |
| `Texas_RHL0024A` | U102 (TI SN74AXC8T245) | VQFN-24 (3.5x5.5mm, 0.5mm pitch, EP) | Texas Instruments Drawing RHL0024A (2 top, 10 left, 2 bot, 10 right, EP) |
| `OSRAM_SFH7018A_2.4x2.4mm` | D401..D404 (OSRAM SFH7018A) | Custom 8-Pad (2.4x2.4x0.6mm) | ams OSRAM Drawing E062.3010.317 -02 (BIOFY multi-emitter) |
| `OSRAM_SFH4053B_1.0x0.5mm` | D405..D407 (OSRAM SFH4053B) | 0402 SMD (1.0x0.5x0.45mm) | ams OSRAM Drawing E062.3010.122 -01 (850nm IR ChipLED) |
| `OSRAM_SFH2703_3.2x2.0mm` | D413, D414, D423, D424 (SFH2703H) | 2-Pad SMD (3.2x2.0x0.6mm) | ams OSRAM Drawing E062.3010.282 -01 (PIN Photodiode) |
| `Crystal_1612-2Pin_1.6x1.2mm` | Y1 (40MHz), Y102 (48MHz) | 1612 SMD (1.6x1.2mm, 4 pads) | Standard 1612 land pattern; maps symbol pins 1/2 to active pads 1/3 |
| `BatteryPad_3Pin_SMD` | J201 (Battery Interface) | 3-Pad SMD (1.0x1.5mm, P1.8mm) | Wearable battery lead solder/weld pads (GND, NTC, VBAT) |
| `PogoPad_2Pin_SMD` | J202 (Magnetic Pogo Charge) | 2-Pad Circular SMD (D1.5mm, P2.5mm) | Gold-plated rear case pogo pin contact targets (VBUSIN, GND) |
| `L_2016_2016Metric` | L203 (2.2uH), L401 (1uH), L601 (3.3uH)| 2016 SMD (2.0x1.6mm) | Standard 2016 power inductor land pattern (Murata DFE2016 / Cyntec HTEK2016) |

---

## 3. Detailed Footprint Modifications Applied

Exactly 73 components across 9 schematic files were updated from blank footprint fields to verified footprint assignments:

### 3.1 Sheet: `01_APOLLO510B.kicad_sch` (8 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `U101` | AP510BFA-CBR | `""` | `sportwatch_custom:BGA-153_5.6x5.6mm_Layout13x13_P0.4mm_Ball0.25mm_Pad0.22mm_NSMD` | **A** |
| `U102` | SN74AXC8T245 | `""` | `sportwatch_custom:Texas_RHL0024A` | **A** |
| `U103` | TXB0101DRLR | `""` | `Package_TO_SOT_SMD:SOT-563` | **A** |
| `U104` | SN74AXC1T45 | `""` | `Package_TO_SOT_SMD:SOT-563` | **A** |
| `U105` | SN74AXC1T45 | `""` | `Package_TO_SOT_SMD:SOT-563` | **A** |
| `L101` | 2.2uH / Isat>=1A / DCR<550mR | `""` | `Inductor_SMD:L_0603_1608Metric` | **A** |
| `Y101` | 32.768kHz / low-CL TBD | `""` | `Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm` | **A** |
| `Y102` | 48MHz / CL=8-11pF / ESR<=60R | `""` | `sportwatch_custom:Crystal_1612-2Pin_1.6x1.2mm` | **A** |

### 3.2 Sheet: `02_POWER.kicad_sch` (20 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `C201` | 1uF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C202` | 10uF | `""` | `Capacitor_SMD:C_0603_1608Metric` | **B** |
| `C203` | 10uF | `""` | `Capacitor_SMD:C_0603_1608Metric` | **B** |
| `C204` | 10uF | `""` | `Capacitor_SMD:C_0603_1608Metric` | **B** |
| `C205` | 1uF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C206` | 2.2uF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C207` | 10uF | `""` | `Capacitor_SMD:C_0603_1608Metric` | **B** |
| `C208` | 10uF | `""` | `Capacitor_SMD:C_0603_1608Metric` | **B** |
| `C213` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `R201` | 10k | `""` | `Resistor_SMD:R_0402_1005Metric` | **B** |
| `R202` | 10k | `""` | `Resistor_SMD:R_0402_1005Metric` | **B** |
| `R203` | 47k | `""` | `Resistor_SMD:R_0402_1005Metric` | **B** |
| `R204` | 150k | `""` | `Resistor_SMD:R_0402_1005Metric` | **B** |
| `L201` | 2.2uH | `""` | `Inductor_SMD:L_0603_1608Metric` | **A** |
| `L202` | 2.2uH | `""` | `Inductor_SMD:L_0603_1608Metric` | **A** |
| `L203` | 2.2uH | `""` | `sportwatch_custom:L_2016_2016Metric` | **A** |
| `J201` | BATTERY_3PIN | `""` | `sportwatch_custom:BatteryPad_3Pin_SMD` | **A** |
| `J202` | POGO_CHARGE_2PIN | `""` | `sportwatch_custom:PogoPad_2Pin_SMD` | **A** |
| `NT201` | NetTie_2 | `""` | `NetTie:NetTie-2_SMD_Pad0.5mm` | **B** |
| `NT202` | NetTie_2 | `""` | `NetTie:NetTie-2_SMD_Pad0.5mm` | **B** |

### 3.3 Sheet: `04_PPG.kicad_sch` (27 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `U401` | TPS631000DRLR | `""` | `Package_TO_SOT_SMD:SOT-583-8` | **A** |
| `U402` | TS5A12301E | `""` | `Package_BGA:Texas_DSBGA-6_0.76x1.16mm_Layout2x3_P0.4mm` | **A** |
| `U403` | TS5A12301E | `""` | `Package_BGA:Texas_DSBGA-6_0.76x1.16mm_Layout2x3_P0.4mm` | **A** |
| `U404` | TS5A12301E | `""` | `Package_BGA:Texas_DSBGA-6_0.76x1.16mm_Layout2x3_P0.4mm` | **A** |
| `U405` | TS5A12301E | `""` | `Package_BGA:Texas_DSBGA-6_0.76x1.16mm_Layout2x3_P0.4mm` | **A** |
| `U406` | TS5A12301E | `""` | `Package_BGA:Texas_DSBGA-6_0.76x1.16mm_Layout2x3_P0.4mm` | **A** |
| `U407` | TS5A12301E | `""` | `Package_BGA:Texas_DSBGA-6_0.76x1.16mm_Layout2x3_P0.4mm` | **A** |
| `D401` | SFH7018A Q65113A6157 | `""` | `sportwatch_custom:OSRAM_SFH7018A_2.4x2.4mm` | **A** |
| `D402` | SFH7018A Q65113A6157 | `""` | `sportwatch_custom:OSRAM_SFH7018A_2.4x2.4mm` | **A** |
| `D403` | SFH7018A Q65113A6157 | `""` | `sportwatch_custom:OSRAM_SFH7018A_2.4x2.4mm` | **A** |
| `D404` | SFH7018A Q65113A6157 | `""` | `sportwatch_custom:OSRAM_SFH7018A_2.4x2.4mm` | **A** |
| `D405` | SFH4053B Q65115A1586 | `""` | `sportwatch_custom:OSRAM_SFH4053B_1.0x0.5mm` | **A** |
| `D406` | SFH4053B Q65115A1586 | `""` | `sportwatch_custom:OSRAM_SFH4053B_1.0x0.5mm` | **A** |
| `D407` | SFH4053B Q65115A1586 | `""` | `sportwatch_custom:OSRAM_SFH4053B_1.0x0.5mm` | **A** |
| `D413` | SFH2703H Q65115A2199 | `""` | `sportwatch_custom:OSRAM_SFH2703_3.2x2.0mm` | **A** |
| `D414` | SFH2703H Q65115A2199 | `""` | `sportwatch_custom:OSRAM_SFH2703_3.2x2.0mm` | **A** |
| `D423` | SFH2703H Q65115A2199 | `""` | `sportwatch_custom:OSRAM_SFH2703_3.2x2.0mm` | **A** |
| `D424` | SFH2703H Q65115A2199 | `""` | `sportwatch_custom:OSRAM_SFH2703_3.2x2.0mm` | **A** |
| `L401` | 1uH | `""` | `sportwatch_custom:L_2016_2016Metric` | **A** |
| `NT401` | PPG1_PD_GND_TIE | `""` | `NetTie:NetTie-2_SMD_Pad0.5mm` | **B** |
| `NT402` | PPG2_PD_GND_TIE | `""` | `NetTie:NetTie-2_SMD_Pad0.5mm` | **B** |
| `C403` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C404` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C405` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C406` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C407` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C408` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |

### 3.4 Sheet: `06_WIFI.kicad_sch` (2 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `L601` | 3.3uH_1A_DCR<=200mR | `""` | `sportwatch_custom:L_2016_2016Metric` | **A** |
| `Y1` | 40MHz_CL8pF_ESR100R_1612 | `""` | `sportwatch_custom:Crystal_1612-2Pin_1.6x1.2mm` | **A** |

### 3.5 Sheet: `07_MOTION.kicad_sch` (7 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `C701` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C702` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C703` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C704` | 100nF | `""` | `Capacitor_SMD:C_0402_1005Metric` | **B** |
| `C705` | 2.2uF | `""` | `Capacitor_SMD:C_0805_2012Metric` | **A** |
| `R701` | 10k | `""` | `Resistor_SMD:R_0402_1005Metric` | **B** |
| `R702` | 10k | `""` | `Resistor_SMD:R_0402_1005Metric` | **B** |

### 3.6 Sheet: `09_STORAGE.kicad_sch` (1 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `U901` | EMMC64G-TB9F-06011 | `""` | `sportwatch_custom:FBGA-153_8.0x8.5mm_Layout14x14_P0.5mm` | **A** |

### 3.7 Sheet: `11_BUTTONS.kicad_sch` (5 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `SW1` | BTN_LIGHT | `""` | `Button_Switch_SMD:SW_SPST_EVQP7A` | **A** |
| `SW2` | BTN_UP | `""` | `Button_Switch_SMD:SW_SPST_EVQP7A` | **A** |
| `SW3` | BTN_DOWN | `""` | `Button_Switch_SMD:SW_SPST_EVQP7A` | **A** |
| `SW4` | BTN_START | `""` | `Button_Switch_SMD:SW_SPST_EVQP7A` | **A** |
| `SW5` | BTN_BACK | `""` | `Button_Switch_SMD:SW_SPST_EVQP7A` | **A** |

### 3.8 Sheet: `13_DEBUG.kicad_sch` (1 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `J1301` | TC2030-CTX-NL_TARGET | `""` | `Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical` | **A** |

### 3.9 Sheet: `14_RF.kicad_sch` (2 modified)
| Ref | Value | Previous Footprint | New Assigned Footprint | Classification |
|---|---|---|---|:---:|
| `L1401` | 1.5nH | `""` | `Inductor_SMD:L_0201_0603Metric` | **A** |
| `L1402` | 1.8nH | `""` | `Inductor_SMD:L_0201_0603Metric` | **A** |

---

## 4. Verification Gate Results

Following the changes, the full validation suite was executed using KiCad 10.0.5:

```text
1. Native KiCad Electrical Rules Check (ERC):
   Exit code: 0
   Errors: 0
   Warnings: 1551 (1152 endpoint_off_grid, 384 lib_symbol_issues, 7 isolated_pin_label, 5 pin_to_pin, 2 label_multiple_wires, 1 unconnected_wire_endpoint)
   Result: PASS (0 errors)

2. Native Hierarchy Validation (Root vs 14 Child Sheets):
   Checked interface signals: 83
   Interface mismatches: 0
   Result: PASS (checked=83 mismatches=0)

3. Native Netlist Membership Comparison (vs Pre-Assignment Baseline):
   Baseline components: 243
   Updated components: 243 (243 unique references)
   Baseline electrical nets: 389
   Updated electrical nets: 389
   Net membership mismatches: 0
   Result: PASS (Exact 0 net changes)

4. Unassigned Footprint Audit:
   Assigned footprints: 235 components
   Remaining blank footprints: Exactly 8 components (AE1401, AE1410, AE1420, LRA1, TP1401, TP1410, TP1420, U10)
   Result: PASS (Only intentional Class C TBD parts remain blank)
```
