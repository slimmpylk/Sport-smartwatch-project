# Main / rear sensor interface — revision 1

Source: approved engineering commit `296ba1a13ebc79f6a5c400e4bbd0acb49cc7ed34`.
This tracked contract and `main_rear_interface.json` govern both independent KiCad roots. Positions are abstract IDs, not physical pads. Connector MPN, footprints, cable length/construction, contact ratings and physical mating permutation remain TBD.

## Ownership and authoritative population

MAIN root: `sportwatch_revA.kicad_sch`; sensor endpoint J1501 in 04_PPG. REAR root: `rear_sensor/rear_sensor_revA.kicad_sch`; endpoint J1502. Rear is not a child of MAIN. `source_checkpoint.json` records all original ownership and engineering hashes; current per-root BOMs are in `validation/`. Every schematic component carries `Board=MAIN` or `Board=REAR`. DNP population is explicit and must not satisfy functional requirements.

MAIN retains Apollo U101, eMMC U901, display, nPM1300 U201, TPS63900 U202, Wi-Fi/GNSS/RF, motion, BMP585/OPT4001, haptic/buttons, battery J201 and all support except the listed rear transfers. MAIN 04_PPG retains **U401/L401/C401/C402/R406/R407** as its six existing components. J1501 is a newly added abstract endpoint. Converter feedback remains MAIN-local; PPG_VLED is exported. MAIN 08_ENVIRONMENT retains R801/R802/R803 and U4/U5/support. R801/R802 are the sole ENV bus pull-ups.

REAR receives exactly 44 existing components, preserving references and symbol/pin UUIDs: D401–D407, D413/D414/D423/D424, U12/U13, U402–U407, C403–C408, C4101–C4104, C4201–C4204, NT401/NT402, R401–R405/R408/R409, U6/C802. U6 is the actual ten-pin MAX30208 Thin LGA; pins 7 and 10 remain GND; no IRQ added. New J1502 and DNP C1501 are separate provisions.

CHARGER is a separate purchased harness/contact assembly described in `charger_harness.md` / `.json`, with its own population. No fabricated contact PCB is defined here. MAIN 12_CHARGING owns J202 and input protection provisions. U201 and C201 remain on MAIN 02_POWER. Existing main PCB optics/copper are historical until an explicitly authorized PCB transfer.

## Abstract continuity and mating view

Logical continuity is **J1501 position n → conductor n → J1502 position n**, for n=1..24. This is an abstract identity map only. Neither equal global-label text nor equal physical screen positions connect independent projects. The audit joins actual native netlist connector nodes through this table.

Assembly axes are viewed from display/front: north = −Y, east = +X. The optical face points toward the wrist. Define connector drawings in the **looking into the connector mating face** convention; label position 1 explicitly on each drawing. Opposing mating faces can mirror. No physical flip, rotation, same-side/opposite-side flex contact choice or physical pad number is approved by this logical identity map. Before footprints, record both manufacturer mating-face drawings and measured cable permutation, atomically update both symbols/contract, and rerun continuity/polarity tests.

| Position | Logical net | Position | Logical net |
|---:|---|---:|---|
| 1 | GND | 13 | PPG_SAMPLE_SYNC |
| 2 | PPG_SPI_SCLK | 14 | GND |
| 3 | GND | 15 | ENV_I2C_SCL |
| 4 | PPG_SPI_MOSI | 16 | ENV_I2C_SDA |
| 5 | GND | 17 | GND |
| 6 | PPG_SPI_MISO | 18 | VOUT1_1V8 |
| 7 | GND | 19 | GND |
| 8 | PPG1_CS_N | 20 | GND (power return group) |
| 9 | PPG2_CS_N | 21 | PPG_VLED |
| 10 | GND | 22 | PPG_VLED |
| 11 | PPG1_INT_N | 23 | PPG_VLED |
| 12 | PPG2_INT_N | 24 | GND (power return group) |

Exactly 10 signal positions, one logic supply, three VLED and ten GND. Exactly 13 logical boundary nets including GND. All GND positions belong to common system GND; no isolated analog/digital rails are created.

## Electrical signal contract

Directions below are relative to MAIN. All digital voltage levels are 1.8 V. Current class is low-current logic; cable capacitance, rise time, loading and return continuity require qualification. No digital pin has permission to source power into an unpowered device.

| Net / positions | Direction / endpoint | Default state | Pull-up owner | Sequencing / current class |
|---|---|---|---|---|
| PPG_SPI_SCLK / 2 | OUT U101.K5 → U12/U13.A2 | Host Hi-Z until rail valid; idle per configured SPI mode | None added | Low-current push-pull; start conservatively, validate <=4 MHz |
| PPG_SPI_MOSI / 4 | OUT U101.L5 → U12/U13.A4 | Host Hi-Z until rail valid | None | Low-current push-pull |
| PPG_SPI_MISO / 6 | IN U101.L7 ← U12/U13.A3 | Both slaves deselected; selected slave alone drives | None | Verify tri-state; never assert both CS |
| PPG1_CS_N / 8 | OUT U101.D9 → U12.A5 | High/deselected | REAR R401 → 1.8 V | Low-current; Hi-Z during startup/off |
| PPG2_CS_N / 9 | OUT U101.M5 → U13.A5 | High/deselected | REAR R402 → 1.8 V | Same |
| PPG1_INT_N / 11 | IN U101.D8 ← U12.B2 | Pulled high, active low | REAR R403 → 1.8 V | Open-drain interrupt |
| PPG2_INT_N / 12 | IN U101.C8 ← U13.B2 | Pulled high, active low | REAR R404 → 1.8 V | Open-drain interrupt |
| PPG_SAMPLE_SYNC / 13 | OUT U101.H13 → U12/U13.B3 | Pulled high; host Hi-Z until configuration | REAR R405 → 1.8 V | Existing AFE GPIO1 synchronization behavior preserved |
| ENV_I2C_SCL / 15 | OUT/open-drain U101.K3 → U6.9; shared main U4/U5 | Pulled high when supply valid | MAIN R802 4.7k → 1.8 V | No rear pull-up; qualify total bus C/rise time |
| ENV_I2C_SDA / 16 | BIDIRECTIONAL U101.J4 ↔ U6.8; shared main U4/U5 | Pulled high when supply valid | MAIN R801 4.7k → 1.8 V | Open drain; no rear pull-up |
| VOUT1_1V8 / 18 | MAIN nPM1300 BUCK1 → REAR | Absent until MAIN supply valid | Not applicable | Low-current AFE analog/digital + U6; qualify actual peak/inrush |
| PPG_VLED / 21–23 | MAIN TPS631000 → REAR | Follows existing EN from VOUT1_1V8 | Not applicable | ~3.82 V nominal existing converter; pulsed LED/mux power, rating TBD |
| GND / ten positions | Common reference / bidirectional current return | Always common before signals/power enabled | Not applicable | Returns rated with supply conductors; grouping is physical only |

No power gating/regulator is added on REAR. Source flags on REAR represent external supply through J1502, not internally generated rails. No VBAT/VSYS/SYS_3V3/VOUT2_3V0 is exported. Both boards share the existing 1.8 V rail; host pins must stay Hi-Z before it is valid and whenever REAR is disconnected/unpowered. Assemble cable with power off; hot-plug is not qualified. Firmware must disable bus drive before rail removal. Any independently gated rear power requires an explicit isolation/back-power ECO. Verify clamp-injection current and both directions of off-state leakage on assembled hardware.

## Rear-local optical contract

D424 → U12 PD1/D5, D414 → U12 PD2/D4, D423 → U13 PD1/D5, D413 → U13 PD2/D4. Preserve every baseline LED/mux/cathode net membership, VREF relationship and intentional unused cathode NC. R408/R409 and AFE GPIO2 mux selection remain local.

**MUST NOT cross boards:** any PD_IN, PPG1_PD_GND/PPG2_PD_GND, VREF, LED cathode/current-sink nets, PPG1_LED_MUX_SEL/PPG2_LED_MUX_SEL, converter FB/switching nodes. NT401 ties PPG1_PD_GND to local common GND; NT402 does the same for PPG2. Future layout rebuilds guards locally. Charger current and optical power returns must not flow through either tie or guard copper.

## Power and signal provisions / freeze gates

C402 remains at MAIN converter. Retain all per-AFE and mux bypass capacitors on REAR. C1501 is an additional **DNP, value/footprint TBD rear-entry VLED reservoir**, not credited as working decoupling. Size with cable/contact resistance, cable inductance, actual LED pulse width, both-AFE overlap/current, effective C under DC bias, allowable droop/headroom, converter transient response, ESR/ESL, recharge, inrush and stability. Estimate residual-current droop `I_residual*t/C_eff + I*ESR + L*di/dt`, plus DC loop drop; validate at temperature and battery extremes.

Preserve one current path per AFE per exposure, red <=31 mA and green/IR <=62 mA initial firmware policy. Two AFEs can request about 124 mA LED current under that policy; this is not a cable/contact rating. Qualify current sharing among three VLED positions and comparable GND return capacity; size to full authorized pulse/recharge/fault envelope before population/connector freeze.

Schematic notes reserve optional source-series damping on MAIN SCLK/MOSI/CS1/CS2 and REAR MISO. Phase 1 retains direct nets and fits no arbitrary resistors. Measurement ECO must insert selected source resistors, update the audit's explicit series-element policy and preserve Apollo allocations. Scope actual cable edges/reflections and SPI setup/hold before values or population are chosen. No rear outline/stackup/rules/placement is frozen; rear gets independent future rules/DRC and placement approval.
