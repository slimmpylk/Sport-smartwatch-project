# Final Pre-PCB Electrical Schematic Gate

Date: 2026-10-06  
Project: `sportwatch_revA`  
Branch / baseline: `fix/revA-hierarchy-integration` / `7513a3604df232e04ba989ba8716a0611a5fcc08`  
Native engine: KiCad CLI 10.0.5

## Gate decision

**PASS — proceed to the controlled footprint-assignment/audit phase.**

The complete project has zero native ERC errors. The native netlist exports successfully, all original hierarchy interfaces compare exactly (`checked=83 mismatches=0`), the revised PPG circuitry passes the electrical/topology audit, and the HEAD-to-final netlist comparison contains no changed component membership outside `04_PPG`.

This is not approval to begin PCB layout. Eighty-one native-netlist components still have blank footprints, including 27 PPG parts; these are intentionally left for the requested footprint audit. No guessed footprints were assigned.

## Native KiCad ERC and netlist

The complete root project was checked and exported with native KiCad, using the project symbol/footprint tables and the KiCad 10 system libraries.

| State | Errors | Warnings | Total |
|---|---:|---:|---:|
| Candidate as received, before gate repairs | 38 | 1172 | 1210 |
| Final | **0** | **1170** | **1170** |

Final native artifacts:

- ERC: `/tmp/final_gate/erc-final-gate.json`
- KiCad XML netlist: `/tmp/final_gate/netlist-final-gate.xml`
- Both native commands exited 0.
- The Flatpak runtime printed a harmless missing runtime-lock inspection message. Netlist export also printed KiCad's generic “schematic has annotation errors” warning; exact checks contradict any duplicate/unannotated-reference interpretation: the native export has 243 components / 243 unique references / 0 duplicates, and the full normalized hierarchy has 446 symbols / 446 unique references / 0 undesignated references.

Final remaining native warnings are:

| ERC type | Count | Classification | Disposition |
|---|---:|---|---|
| `endpoint_off_grid` | 1152 | F | Existing cosmetic/grid cleanup; not an electrical-connectivity failure. |
| `isolated_pin_label` | 7 | E | `PMIC_GPIO0..4`, `PMIC_LSOUT1_TBD`, and `PMIC_LSOUT2_TBD`; intentional provisioning/TBD. |
| `pin_to_pin` | 5 | C | Existing symbol-semantic warnings: U702 pins 2/3 on VOUT1 and U4/U6 bidirectional pins on the power-flagged net. Net membership is intentional. |
| `lib_symbol_mismatch` | 3 | C | Existing cached-standard-symbol differences on J201, J202, and U202; all symbols resolve and their connectivity is unchanged. |
| `label_multiple_wires` | 2 | F | Existing root VBAT short-wire geometry. |
| `unconnected_wire_endpoint` | 1 | F | Existing 0.0018 mm graphical wire stub. |

### Findings resolved during this gate

| Finding | Class | Resolution |
|---|---|---|
| `04_PPG` used VBAT without a matching root sheet pin, leaving U401 VIN on a private child net | A | Added the `VBAT` sheet pin and root connection. This removed `hier_label_mismatch` and `power_pin_not_driven`. |
| Embedded SFH4053B and TS5A12301E cache identifiers did not match their `sportwatch_custom:` instance IDs; KiCad dropped nine components from the native netlist and produced 21 dangling-label plus 15 pin-not-connected errors | C, justified | Corrected the cache IDs and added exact project-library definitions. All nine components now appear with their real pins and nets. |
| U401 claimed `sportwatch_custom:TI_DRL0008A_SOT-583`, but that footprint did not exist | C, justified | Cleared the false footprint assignment. U401 is explicitly pending the footprint audit; no replacement was guessed. |
| The two GPIO2 LED-mux select banks had no pull-ups even though MAX86141 GPIO2 is open-drain in the implemented mux-control mode | A | Added R408 and R409, 10 kΩ from each mux-select net to `VOUT1_1V8`. The calculated 19 pF bank load gives 190 ns RC and approximately 874 ns to 99%. |

After the actual circuit changes, the native netlist was exported again and the hierarchy comparison was rerun.

**Exact remaining electrical errors: none.**

## Hierarchy and unintended-net-change gate

The established comparison was rerun using the union of the 14 independently exported child netlists against the final complete-project native netlist:

```text
checked=83 mismatches=0
```

The original 83 implemented cross-sheet interfaces therefore retain exact component/pin membership. Normal cross-sheet signals use hierarchical labels and matching root sheet pins. Private PPG nets remain sheet-qualified as `/04_PPG/...`; GND remains the intentional global power net. No accidental local-label cross-sheet assumption was found.

The final native netlist was also compared with native netlist export of HEAD `7513a36`:

- changed nets: 32
- changed nets with any altered non-PPG component member: **0**
- all additions/removals are on `04_PPG` components; the root VBAT edit only connects the intended new PPG load into the existing `/VBAT` interface

Result: **no unintended net change outside the PPG modification scope.**

## Detailed `04_PPG` audit

### MAX86141 interfaces

Both MAX86141 devices remain present and fully connected:

| Function | U12 / PPG1 | U13 / PPG2 | Result |
|---|---|---|---|
| SPI clock | A2 `PPG_SPI_SCLK` | A2 `PPG_SPI_SCLK` | Shared as intended |
| SPI MOSI | A4 `PPG_SPI_MOSI` | A4 `PPG_SPI_MOSI` | Shared as intended |
| SPI MISO | A3 `PPG_SPI_MISO`, tri-state | A3 `PPG_SPI_MISO`, tri-state | Valid shared three-node bus with U101.L7 |
| Chip select | A5 `PPG1_CS_N` | A5 `PPG2_CS_N` | Separate, each with its own pull-up and MCU pin |
| Interrupt | B2 `PPG1_INT_N` | B2 `PPG2_INT_N` | Separate open-drain nets, each with its own pull-up and MCU pin |
| Sample sync | B3 `PPG_SAMPLE_SYNC` | B3 `PPG_SAMPLE_SYNC` | Shared GPIO1 sample-trigger input |
| Mux control | B4 `PPG1_LED_MUX_SEL` | B4 `PPG2_LED_MUX_SEL` | Separate GPIO2 banks with R408/R409 pull-ups |

For the implemented shared-sample-trigger plus external-mux topology, firmware must select `GPIO_CTRL[3:0] = 0010`. In that mode GPIO1 is the sample-trigger input and GPIO2 is the open-drain mux control. GPIO2 is low during LED4/5/6 exposures and high during LED1/2/3 exposures; when inactive it can be tri-stated, which is why R408/R409 are required. This now matches the implemented hardware.

### Receivers

The four SFH2703 photodiodes have the datasheet polarity required by MAX86141:

| Receiver | Cathode, pin 1 | Anode, pin 2 |
|---|---|---|
| D413 | `PPG1_PD1_IN` | `PPG1_PD_GND` |
| D414 | `PPG1_PD2_IN` | `PPG1_PD_GND` |
| D423 | `PPG2_PD1_IN` | `PPG2_PD_GND` |
| D424 | `PPG2_PD2_IN` | `PPG2_PD_GND` |

Result: **PASS**.

### SFH7018A emitters and discrete IR emitters

The four SFH7018A pin maps match the datasheet: green cathodes are pins 1/7/8, IR cathode is pin 3, red cathode is pin 5, and common anodes are pins 2/4/6.

| Device | Green cathodes 1/7/8 | Red cathode 5 | IR cathode 3 | Anodes 2/4/6 |
|---|---|---|---|---|
| D401 | PPG1 LED1 | PPG1 LED2 | explicit NC | `PPG_VLED` |
| D402 | PPG2 LED1 | PPG2 LED2 | PPG2 LED6 IR940 | `PPG_VLED` |
| D403 | PPG1 LED4 | PPG1 LED5 | explicit NC | `PPG_VLED` |
| D404 | PPG2 LED4 | PPG2 LED5 | explicit NC | `PPG_VLED` |

The three added SFH4053B 850-nm-class emitters also have correct polarity:

| Device | Anode, pin 1 | Cathode, pin 2 |
|---|---|---|
| D405 | `PPG_VLED` | PPG1 LED3 IR850 |
| D406 | `PPG_VLED` | PPG1 LED6 IR850 |
| D407 | `PPG_VLED` | PPG2 LED3 IR850 |

D401.3, D403.3, and D404.3 are the deliberately unused SFH7018A IR dies and are explicitly no-connected. Result: **PASS**.

### External LED multiplexers

For TS5A12301E, B2 is COM, A1 is NO, C1 is NC, A2 is control, C2 is VCC, and B1 is GND. High control connects COM-to-NO; low or floating control connects COM-to-NC. The device specifies break-before-make operation.

| Switch | COM B2 | NO A1, GPIO2 high | NC C1, GPIO2 low | Control A2 |
|---|---|---|---|---|
| U402 | PPG1 green driver | D401 LED1 green | D403 LED4 green | PPG1 mux select |
| U403 | PPG1 red driver | D401 LED2 red | D403 LED5 red | PPG1 mux select |
| U404 | PPG1 IR driver | D405 LED3 IR850 | D406 LED6 IR850 | PPG1 mux select |
| U405 | PPG2 green driver | D402 LED1 green | D404 LED4 green | PPG2 mux select |
| U406 | PPG2 red driver | D402 LED2 red | D404 LED5 red | PPG2 mux select |
| U407 | PPG2 IR driver | D407 LED3 IR850 | D402 LED6 IR940 | PPG2 mux select |

All six switches have C2 on `PPG_VLED`, B1 on GND, and their A2 controls on the appropriate AFE's GPIO2 bank. Each of the six driver-output nets contains exactly one MAX86141 LED driver and one mux COM; no driver output is shorted to another driver.

Each driver reaches only one cathode branch at a time. The TS5A12301E break-before-make behavior prevents a transfer overlap, and the shared GPIO2 state consistently selects either the LED1/2/3 bank or the LED4/5/6 bank for that AFE. No unintended simultaneous hardwired LED-current path exists. Firmware remains responsible for programming the intended exposure/current sequence.

Result: **PASS**.

### PPG_VLED distribution

`PPG_VLED` has 34 native-netlist members. It reaches:

- U401 output and feedback divider
- U12.A1 and U13.A1 MAX86141 VLED inputs
- all six TS5A12301E VCC pins
- all twelve SFH7018A common-anode pins
- all three SFH4053B anodes
- the intended bulk/local decoupling capacitors

No missing VLED consumer or foreign load was found. Result: **PASS**.

## TPS631000 audit

U401 is correctly connected:

| Pin | Function | Implemented connection |
|---|---|---|
| 1 | VOUT | `PPG_VLED` |
| 2 | LX2 | L401.2 |
| 3 | LX1 | L401.1 |
| 4 | VIN | `/VBAT` |
| 5 | EN | `/VOUT1_1V8` |
| 6 | MODE | GND, selecting power-save mode |
| 7 | GND | GND |
| 8 | FB | R406/R407 midpoint |

L401 is 1 µH. C401 is 22 µF from VBAT to GND and C402 is 47 µF from PPG_VLED to GND, matching the TI nominal input/output recommendations. The footprint audit must still choose parts whose effective capacitance under DC bias satisfies the datasheet and must validate the inductor saturation-current/DCR rating.

The feedback divider is R406 = 604 kΩ high side and R407 = 91 kΩ low side:

```text
VOUT = 0.500 V × (1 + 604 kΩ / 91 kΩ) = 3.8187 V nominal
```

Using the datasheet 0.495–0.505 V feedback reference and 1% resistors gives 3.715–3.925 V worst-case. This is inside the TPS631000 1.2–5.3 V output range and the MAX86141 3.1–5.5 V VLED range.

Result: **PASS**.

## Project-wide audit

- Duplicate references: **none**. Native export is 243/243 unique; normalized complete hierarchy is 446/446 unique with zero undesignated symbols.
- Unresolved symbol libraries: **none newly present**. Final native ERC has no `lib_symbol_issues`. The project custom library lint has 0 errors.
- False assigned footprints: **none remaining**. Final native ERC has no `footprint_link_issues`; all 162 assigned footprints resolve. U401's false assignment was removed.
- Blank footprints: 81 total, intentionally deferred to the footprint audit. The 27 PPG blanks are C403–C408, D401–D407, D413/D414/D423/D424, L401, NT401/NT402, U401, and U402–U407.
- Unconnected pins: native ERC has no `pin_not_connected`. The netlist contains 195 explicitly isolated pins on 13 references: D401/D403/D404 (3 deliberate unused IR dies), J1 (2), U101 (36), U11 (2), U201 (8), U4 (1), U5 (2), U702 (2), U8 (7), U9 (11), and U901 (121). These are established NC, unused option, RFU, or intentional TBD cases; none is an accidental new open electrical pin.
- Integrity check: `akcli check --integrity` reports zero findings; metadata is 446 components, 1294 pins, 221 unnamed/private nets, and 75 explicit ERC suppressions/no-connect semantics.
- Repository scope: only `04_PPG.kicad_sch`, the root `sportwatch_revA.kicad_sch`, and `libraries/symbols/sportwatch_custom.kicad_sym` are modified. No PCB file was changed.

## Classification summary

- **A — REAL ELECTRICAL ERROR:** missing PPG VBAT hierarchy connection and missing GPIO2 mux-control pull-ups; fixed and revalidated.
- **B — INTENTIONAL NC:** explicit unused dies/NC/option/RFU pins, including the three unused SFH7018A IR dies; retained.
- **C — SYMBOL SEMANTIC/ERC FALSE POSITIVE:** malformed new cache/library IDs and false U401 footprint were fixed; five existing pin-type warnings and three resolved-but-cache-different standard symbols remain non-electrical.
- **D — PCB-LAYOUT CONCERN:** regulator hot-loop/capacitor placement, FB isolation, LED-current routing, photodiode guarding, thermal performance, and actual capacitor derating/inductor current rating belong to the next physical audit; none changes this schematic result.
- **E — INTENTIONAL TBD:** seven PMIC labels and the blank footprint fields remain explicit inputs to later audits.
- **F — COSMETIC/OFF-GRID CLEANUP:** 1152 off-grid endpoints, two short-wire label geometry warnings, one microscopic graphical stub, and one pre-existing trailing-whitespace line; not changed because they do not alter connectivity.

## Final disposition

Electrical schematic gate: **PASS**  
Authorized next phase: **footprint assignment and footprint audit only**  
PCB layout: **not started and not authorized by this gate**

SCHEMATIC STATUS: ELECTRICALLY FROZEN FOR FOOTPRINT AUDIT
