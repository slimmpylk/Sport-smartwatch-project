# Rev-A Hierarchy Integration Status

## Current State

- Inventory started from the actual KiCad 10 project on 2026-09-30.
- `sportwatch_revA.kicad_sch` now instantiates all fourteen child sheets with explicit sheet pins and root interconnect stubs for every implemented project interface.
- Normal cross-sheet application and power signals use child hierarchical labels, matching root sheet pins, and root wiring. GND remains KiCad global power; private RF, regulator, reference, SIMO, PPG, and crystal nets remain private.
- Native KiCad netlist export proves all 83 implemented shared interfaces resolve as one project net each, with component membership exactly equal to the union of the corresponding pre-edit child nets.
- Project-wide references are unique: 396 top-level symbols have 396 unique references, and native export has 218 exported components with 218 unique references.
- Project-local symbol tables now resolve all saved custom/imported symbol nicknames; known project footprints are qualified. Final ERC has no missing-library, missing-footprint, or project-local cached-symbol mismatch finding.
- Post-integration symbol corrections are validated: MAX86141 SDO is tri-state, and all 120 eMMC hidden NC/RFU/VSF pins have unique unconnected coordinates. The hierarchy and all native net memberships remain unchanged.
- The project is on branch `fix/revA-hierarchy-integration`.
- A pre-existing uncommitted change in `06_WIFI.kicad_sch` is preserved.
- The stale KiCad lock was removed after confirming no KiCad/eeschema process was running.
- The requested audit and handoff were absent from `docs/project`; the latest recoverable copies in the desktop Trash were read completely before schematic edits.
- Native KiCad XML provides the preservation and before-state baseline at `/tmp/watch_hierarchy/baseline.xml`.

## Completed Work

- Created this mandatory continuation file before hierarchy edits.
- Inspected project file names, root hierarchy, library tables, local library contents, Git state, and akcli/KiCad tool availability.
- Created Git branch `fix/revA-hierarchy-integration` without disturbing the existing `06_WIFI.kicad_sch` edit.
- Confirmed the root resolves all fourteen saved child files through existing sheet instances.
- Read the complete final schematic audit and latest (2026-09-16 09:24) smartwatch handoff.
- Confirmed by native KiCad net membership that the completed POWER, WIFI, STORAGE, and RF local fixes remain present.
- Captured native baseline ERC: 45 errors, 1780 warnings, 1825 total, exit 5.
- Verified the shared MAG_I2C bus uses Apollo IOM0 on GPIO5/GPIO6 and two fitted 10 kΩ pull-up pairs in parallel, or 5 kΩ effective per line. At 400 kHz this meets the NXP rise-time window only when total bus capacitance is at or below about 70.8 pF; actual layout capacitance remains to be checked.
- Converted 83 implemented application and power interfaces to child hierarchical labels and explicit root sheet-pin wiring while preserving sheet and symbol UUIDs.
- Replaced `03_DISPLAY` child global labels with hierarchical labels plus local repeated labels so display nets no longer escape hierarchy globally.
- Exported the saved project to `/tmp/watch_hierarchy/post-hierarchy.xml`; all 83 interface membership comparisons pass with zero mismatches.
- Rendered the integrated root to `/tmp/watch_hierarchy/root-hierarchy.svg` and ran an akcli integrity/net check.
- Re-annotated POWER, MOTION, and STORAGE into stable logical ranges and repaired four duplicate Wi-Fi hidden-power references without changing symbol UUIDs.
- Created registered local `sportwatch_custom` and `nordic-lib-kicad-npm` symbol libraries from exact saved caches and refreshed the seven timestamp-named local libraries from their exact saved definitions.
- Qualified all known matching imported footprints in PPG, GNSS, WIFI, ENVIRONMENT, and HAPTICS; corrected the PCA9306 instance/cache footprint to `Package_SO:VSSOP-8_2.3x2mm_P0.5mm`.
- Reverified all 83 interfaces after annotation/library cleanup: zero membership mismatches.
- Reverified the four protected local-fix groups from final native net membership, including PMIC TWI/pull-ups, Wi-Fi decoupling/diplexer grounds, eMMC supply/ground/pull-up fanout, and all corrected RF through-path/test-point memberships.
- Corrected MAX86141 ball A3 `SDO` from KiCad electrical type `output` to `tri_state` in both the project library and `04_PPG` cache. Pin name, number, geometry, and the shared `PPG_SPI_MISO` net remain unchanged.
- MAX86141-only validation: native ERC improved from 19 errors/1117 warnings to 18 errors/1117 warnings; the shared-SDO output/output error disappeared. Native interface comparison remained `checked=83 mismatches=0`.
- Applied the eMMC geometry-only repair to the project library and `09_STORAGE` cache: 107 NC, 7 RFU, and 6 VSF pins moved from one shared `(0,0)` coordinate to 120 unique 100-mil-grid coordinates. All 153 ball number/name/type/hide signatures remain unchanged against Kingston Table 9.
- Final eMMC validation: `sportwatch_custom` lint now reports 0 errors and 163 pre-existing off-grid warnings; all 373 native net memberships are identical to the pre-eMMC netlist; all 120 hidden balls remain on isolated `unconnected-(U901-...)` nets.
- Final library/cache synchronization check is token-identical for both MAX86141 and eMMC after allowing for the library nickname prefix in schematic caches.

## Current Work In Progress

Adjudication and resolution of the 18 native KiCad ERC errors across all 11 review items is complete.
17 errors are cleanly resolved by design intent, datasheet confirmation, symbol semantic correction, and appropriate ERC flags. Exactly 1 error remains intentionally unresolved (`PPG_VLED` source on U12.A1, Class G, awaiting engineering of the LED regulator).

## Remaining Work

1. Engineer the `PPG_VLED` regulator and upstream supply when LED current budget and battery profile are defined (clears remaining Class G ERC error).
2. Continue layout and physical design validation.


## Net Integration Status

Integration mechanism used for normal signals and named power rails: hierarchical labels in children, matching sheet pins in the root, and explicit root wiring. GND remains KiCad global power. Membership was verified from the native KiCad netlist, not by label-name comparison.

| Net name | Source sheet | Consumer sheet(s) | Integration mechanism | Status |
|---|---|---|---|---|
| VBAT | 02_POWER | 06_WIFI, 13_DEBUG | root hierarchy | COMPLETE |
| VSYS | 02_POWER | 03_DISPLAY, 10_HAPTICS, 13_DEBUG | root hierarchy | COMPLETE |
| VOUT1_1V8 | 02_POWER | 01_APOLLO510B, 04_PPG, 05_GNSS, 06_WIFI, 07_MOTION, 08_ENVIRONMENT, 09_STORAGE, 10_HAPTICS, 11_BUTTONS, 13_DEBUG | root hierarchy | COMPLETE |
| VOUT2_3V0_PROVISIONAL | 02_POWER | 05_GNSS, 09_STORAGE, 13_DEBUG | root hierarchy | COMPLETE |
| SYS_3V3 | 02_POWER | 01_APOLLO510B, 03_DISPLAY, 13_DEBUG | root hierarchy | COMPLETE |
| PPG_VLED | regulator TBD | 04_PPG | reserved root hierarchy; source unresolved | BLOCKED |
| MAG_I2C_SDA | 01_APOLLO510B | 02_POWER, 07_MOTION | root hierarchy | COMPLETE |
| MAG_I2C_SCL | 01_APOLLO510B | 02_POWER, 07_MOTION | root hierarchy | COMPLETE |
| DISP_QSPI_CLK | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| DISP_QSPI_CS | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| DISP_QSPI_IO0 | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| DISP_QSPI_IO1 | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| DISP_QSPI_IO2 | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| DISP_QSPI_IO3 | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| DISP_RST | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| DISP_TE | 03_DISPLAY | 01_APOLLO510B | root hierarchy | COMPLETE |
| DISP_VCI_EN | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| TOUCH_SDA | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| TOUCH_SCL | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| TOUCH_INT | 03_DISPLAY | 01_APOLLO510B | root hierarchy | COMPLETE |
| TOUCH_RST | 01_APOLLO510B | 03_DISPLAY | root hierarchy | COMPLETE |
| IMU_SPI_SCK | 01_APOLLO510B | 07_MOTION | root hierarchy | COMPLETE |
| IMU_SPI_MOSI | 01_APOLLO510B | 07_MOTION | root hierarchy | COMPLETE |
| IMU_SPI_MISO | 07_MOTION | 01_APOLLO510B | root hierarchy | COMPLETE |
| IMU_SPI_CS | 01_APOLLO510B | 07_MOTION | root hierarchy | COMPLETE |
| IMU_INT1 | 07_MOTION | 01_APOLLO510B | root hierarchy | COMPLETE |
| IMU_INT2 | 07_MOTION | 01_APOLLO510B | root hierarchy | COMPLETE |
| MAG_INT | 07_MOTION | 01_APOLLO510B | root hierarchy | COMPLETE |
| ENV_I2C_SDA | 01_APOLLO510B | 08_ENVIRONMENT | root hierarchy | COMPLETE |
| ENV_I2C_SCL | 01_APOLLO510B | 08_ENVIRONMENT | root hierarchy | COMPLETE |
| BARO_INT | 08_ENVIRONMENT | 01_APOLLO510B | root hierarchy | COMPLETE |
| ALS_INT | 08_ENVIRONMENT | 01_APOLLO510B | root hierarchy | COMPLETE |
| GNSS_UART_TX | 05_GNSS | 01_APOLLO510B | root hierarchy | COMPLETE |
| GNSS_UART_RX | 01_APOLLO510B | 05_GNSS | root hierarchy | COMPLETE |
| GNSS_TIMEPULSE | 05_GNSS | 01_APOLLO510B | root hierarchy | COMPLETE |
| GNSS_EXTINT | 01_APOLLO510B | 05_GNSS | root hierarchy | COMPLETE |
| GNSS_RF | 05_GNSS | 14_RF | root hierarchy | COMPLETE |
| WIFI_QSPI_CLK | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_QSPI_CS | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_QSPI_IO0 | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_QSPI_IO1 | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_QSPI_IO2 | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_QSPI_IO3 | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_HOST_IRQ | 06_WIFI | 01_APOLLO510B | root hierarchy | COMPLETE |
| WIFI_BUCKEN | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_IOVDD_EN | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_COEX_STATUS | 06_WIFI | 01_APOLLO510B | root hierarchy | COMPLETE |
| WIFI_COEX_REQ | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_COEX_GRANT | 01_APOLLO510B | 06_WIFI | root hierarchy | COMPLETE |
| WIFI_RF | 06_WIFI | 14_RF | root hierarchy | COMPLETE |
| EMMC_CLK | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_CMD | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT0 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT1 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT2 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT3 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT4 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT5 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT6 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_DAT7 | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| EMMC_RST_N | 01_APOLLO510B | 09_STORAGE | root hierarchy | COMPLETE |
| PPG_SPI_SCLK | 01_APOLLO510B | 04_PPG | root hierarchy | COMPLETE |
| PPG_SPI_MOSI | 01_APOLLO510B | 04_PPG | root hierarchy | COMPLETE |
| PPG_SPI_MISO | 04_PPG | 01_APOLLO510B | root hierarchy | COMPLETE |
| PPG1_CS_N | 01_APOLLO510B | 04_PPG | root hierarchy | COMPLETE |
| PPG2_CS_N | 01_APOLLO510B | 04_PPG | root hierarchy | COMPLETE |
| PPG1_INT_N | 04_PPG | 01_APOLLO510B | root hierarchy | COMPLETE |
| PPG2_INT_N | 04_PPG | 01_APOLLO510B | root hierarchy | COMPLETE |
| PPG_SAMPLE_SYNC | 01_APOLLO510B | 04_PPG | root hierarchy | COMPLETE |
| HAPTIC_I2C_SCL | 01_APOLLO510B | 10_HAPTICS | root hierarchy | COMPLETE |
| HAPTIC_I2C_SDA | 01_APOLLO510B | 10_HAPTICS | root hierarchy | COMPLETE |
| HAPTIC_NRST | 01_APOLLO510B | 10_HAPTICS | root hierarchy | COMPLETE |
| HAPTIC_TRIG_INTZ | 10_HAPTICS | 01_APOLLO510B | root hierarchy | COMPLETE |
| BTN_BACK_N | 11_BUTTONS | 01_APOLLO510B | root hierarchy | COMPLETE |
| BTN_UP_N | 11_BUTTONS | 01_APOLLO510B | root hierarchy | COMPLETE |
| BTN_START_N | 11_BUTTONS | 01_APOLLO510B | root hierarchy | COMPLETE |
| BTN_DOWN_N | 11_BUTTONS | 01_APOLLO510B | root hierarchy | COMPLETE |
| BTN_LIGHT_N | 11_BUTTONS | 01_APOLLO510B | root hierarchy | COMPLETE |
| APOLLO_SWCLK | 13_DEBUG | 01_APOLLO510B | root hierarchy | COMPLETE |
| APOLLO_SWDIO | bidirectional 01_APOLLO510B/13_DEBUG | 01_APOLLO510B, 13_DEBUG | root hierarchy | COMPLETE |
| APOLLO_SWO_GPIO28 | 01_APOLLO510B | 13_DEBUG | root hierarchy | COMPLETE |
| APOLLO_RST_N | 13_DEBUG | 01_APOLLO510B | root hierarchy | COMPLETE |
| APOLLO_BLE_ANT | 01_APOLLO510B | 14_RF | root hierarchy | COMPLETE |
| APOLLO_BLE_AVDD_PA | 01_APOLLO510B | 14_RF | root hierarchy | COMPLETE |

## Annotation Status

- `02_POWER`: `C1`–`C15` -> `C201`–`C215`; `R1`–`R7` -> `R201`–`R207`; `L1`–`L3` -> `L201`–`L203`; `U1` -> `U201`; `U2` -> `U202`; `NT1` -> `NT201`; `NT2` -> `NT202`; `JBAT1` -> `J201`; `JCHG1` -> `J202`; `#PWR001`–`#PWR018` -> `#PWR0201`–`#PWR0218`.
- `07_MOTION`: `C1`–`C5` -> `C701`–`C705`; `R1`–`R2` -> `R701`–`R702`; `U2` -> `U702`; `U3` -> `U703`.
- `09_STORAGE`: `U1` -> `U901`.
- `06_WIFI` duplicate hidden power symbols, identified by preserved symbol UUID: `#PWR0610` -> `#PWR0622` (`c6c6780e-5110-4b60-a6fc-bcc1ccaa8295`); `#PWR0603` -> `#PWR0623` (`d7db8dc4-a2a8-4e45-9ff5-fb7e97a701eb`); `#PWR0611` -> `#PWR0624` (`db8bd5a9-32b9-4f7c-bd49-9564ed7e243a`); `#PWR0614` -> `#PWR0625` (`f42f5af2-f80e-4000-aa90-6d3f96b1367c`).
- Native preview export contains 218 exported components with 218 unique references. The KiCad export still emits a generic annotation warning that will be rechecked after final cleanup, but no duplicate reference remains in its component list.

## ERC Status

- Native KiCad ERC actually ran against the current saved files.
- Exact command: `env XDG_CACHE_HOME=/tmp/watch_hierarchy/kicad/cache XDG_CONFIG_HOME=/tmp/watch_hierarchy/kicad/config XDG_DATA_HOME=/tmp/watch_hierarchy/kicad/data KICAD10_SYMBOL_DIR=/var/lib/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/stable/active/files/symbols KICAD10_FOOTPRINT_DIR=/var/lib/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/stable/active/files/footprints KICAD10_3RD_PARTY=/home/sapy/.var/app/org.kicad.KiCad/data/kicad/10.0/3rdparty KICAD=/var/lib/flatpak/app/org.kicad.KiCad/current/active/files/share/kicad /tmp/display-kicad-bin/ld-linux-x86-64.so.2 --library-path /var/lib/flatpak/app/org.kicad.KiCad/current/active/files/lib:/var/lib/flatpak/runtime/org.gnome.Sdk/x86_64/50/active/files/lib/x86_64-linux-gnu /var/lib/flatpak/app/org.kicad.KiCad/current/active/files/bin/kicad-cli sch erc --format json --exit-code-violations -o /tmp/watch_hierarchy/erc-baseline.json sportwatch_revA.kicad_sch`
- Error count: 45.
- Warning count: 1780.
- Important unresolved baseline: absent hierarchy integration, duplicate references, library/footprint resolution findings, PPG_VLED source, and audit confirmation items.
- Native hierarchy-preview ERC actually ran after integration: 19 errors, 1658 warnings, 1677 total. A saved-project post-hierarchy ERC and final post-cleanup ERC remain to be recorded.
- Native saved-project post-hierarchy ERC actually ran: 19 errors, 1652 warnings, 1671 total, exit 5. Report: `/tmp/watch_hierarchy/erc-post-hierarchy.json`.
- Native final ERC actually ran with the Flatpak KiCad 10 global symbol/footprint tables redirected to their installed host paths.
- Final exact command: `env XDG_CACHE_HOME=/tmp/watch_hierarchy/kicad/cache XDG_CONFIG_HOME=/tmp/watch_hierarchy/kicad/config XDG_DATA_HOME=/tmp/watch_hierarchy/kicad/data KICAD10_SYMBOL_DIR=/var/lib/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/stable/active/files/symbols KICAD10_FOOTPRINT_DIR=/var/lib/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/stable/active/files/footprints KICAD10_3RD_PARTY=/home/sapy/.var/app/org.kicad.KiCad/data/kicad/10.0/3rdparty KICAD=/var/lib/flatpak/app/org.kicad.KiCad/current/active/files/share/kicad /tmp/display-kicad-bin/ld-linux-x86-64.so.2 --library-path /var/lib/flatpak/app/org.kicad.KiCad/current/active/files/lib:/var/lib/flatpak/runtime/org.gnome.Sdk/x86_64/50/active/files/lib/x86_64-linux-gnu /var/lib/flatpak/app/org.kicad.KiCad/current/active/files/bin/kicad-cli sch erc --format json --exit-code-violations -o /tmp/watch_hierarchy/erc-final-native-libs.json sportwatch_revA.kicad_sch`.
- Final error count: 19.
- Final warning count: 1117.
- Final report: `/tmp/watch_hierarchy/erc-final-native-libs.json`; exit 5 because violations remain.
- Important unresolved errors: 10 power-input-not-driven, 4 input-not-driven, 3 physically unconnected pins, one dual-MAX86141 SDO output/output connection, and one nRF7002 PAVDD power-output/power-output connection. These are existing local design/ERC issues, not hierarchy failures.
- Important unresolved warnings: 1096 existing off-grid endpoints, 10 intentionally isolated PMIC provisional labels, 4 existing unconnected wire endpoints, 2 bidirectional/power-output classifications, 2 existing Wi-Fi VBAT multi-wire-label warnings, and 3 standard-library cached-symbol version mismatches.
- Native netlist export continues to print a generic annotation warning, but native component enumeration and direct schematic enumeration both prove that no duplicate reference remains.
- Local symbol lint: all timestamp and nPM1300 libraries have zero errors/warnings; `sportwatch_custom` preserves one inherited eMMC stacked-hidden-pin error plus 163 off-grid warnings from the audited cached symbols.
- MAX86141 interim ERC report: `/tmp/watch_hierarchy/erc-max86141.json`, 18 errors and 1117 warnings. Netlist: `/tmp/watch_hierarchy/max86141.xml`. The `PPG_SPI_MISO` nodes export as U101.L7 bidirectional plus U12.A3/U13.A3 tri-state.
- Final symbol-fix ERC report: `/tmp/watch_hierarchy/erc-final-symbol-fixes.json`, 18 errors and 1117 warnings, exit 5. Final netlist: `/tmp/watch_hierarchy/final-symbol-fixes.xml`.
- Adjudication and resolution of the 18 ERC errors (starting from commit `cb6430a` at 18 errors, 1117 warnings):
  - Final native ERC: 1 error, 1119 warnings, exit 5. Report: `/tmp/erc-item9.json`.
  - Netlist interface check: 83/83 interface nets match pre-edit baseline (`checked=83 mismatches=0`).
  - Full-net comparison (`compare_nets.py`): exactly 0 unintended net changes; only verified D401.7 / D402.7 green cathode connections and removal of unused isolated TBD stubs (SHPHLD, LSIN1, LSIN2) are reflected in netlist.
  - Exactly 1 error remains: `U12.A1 [VLED, Power input]` on net `/04_PPG/PPG_VLED` (Class G, intentionally TBD pending LED regulator engineering).

### ERC Error Adjudication Table

| Item | Net / Pin | Violation Type | Class | Datasheet / Engineering Evidence | Action Taken | Topology Changed? | Final Status |
|---|---|---|---|---|---|---|---|
| 1 | `D401.7` (`K_GREEN_2`) | `pin_not_connected` | A | OSRAM SFH 7018A datasheet p15 pinout confirms pins 1, 7, 8 are all green cathode terminals (D1, D2, D3). Pin 7 was unconnected due to incomplete bus wiring. | Connected D401.7 to net `/04_PPG/PPG1_LED_GREEN_DRV` alongside pins 1 and 8. | Yes (fixed circuit error) | CLEARED |
| 1 | `D402.7` (`K_GREEN_2`) | `pin_not_connected` | A | OSRAM SFH 7018A datasheet p15 pinout confirms pins 1, 7, 8 are all green cathode terminals. Pin 7 was unconnected. | Connected D402.7 to net `/04_PPG/PPG2_LED_GREEN_DRV` alongside pins 1 and 8. | Yes (fixed circuit error) | CLEARED |
| 11 | `U11.5` (`QOD`) | `pin_not_connected` | B | TI TPS22918 datasheet §9.2 confirms QOD may be left floating when quick output discharge is not used. | Removed dangling unconnected stub wires; placed deliberate `no_connect` marker at U11 pin 5; updated schematic text note. | No | CLEARED |
| 9 | `U201.15` (`SHPHLD`) | `pin_not_driven` | B | Nordic nPM1300 PS v1.3 §7.4 Table 32 specifies an internal 50 kΩ pull-up resistor (`RSHPHLD`) on SHPHLD. Push-button ship exit is optional; pin may be left floating when unused as in Nordic reference configuration. | Removed isolated wire stub and provisional label `PMIC_SHPHLD`; placed deliberate `no_connect` marker at U201 pin 15; updated schematic text note. | No | CLEARED |
| 9 | `U201.28` (`LSIN1/VINLDO1`) | `pin_not_driven` | B | Nordic nPM1300 PS v1.3 §9.1 Table 35 & §9.3 Reference Circuitry (Configurations 2 & 3 / Figure 63). Unused LDO/load-switch channels are left open/unconnected in reference designs. Rev-A architecture only uses Buck 1 (1.8 V) and Buck 2 (3.0 V). | Removed isolated wire stub and provisional label `PMIC_LSIN1_TBD`; placed deliberate `no_connect` marker at U201 pin 28. | No | CLEARED |
| 9 | `U201.30` (`LSIN2/VINLDO2`) | `pin_not_driven` | B | Nordic nPM1300 PS v1.3 §9.1 Table 35 & §9.3 Reference Circuitry (Configurations 2 & 3 / Figure 63). Unused LDO/load-switch channels left open. | Removed isolated wire stub and provisional label `PMIC_LSIN2_TBD`; placed deliberate `no_connect` marker at U201 pin 30. | No | CLEARED |
| 4 | `U201.21` (`VBUS`) | `power_pin_not_driven` | C | Dock connector J202 delivers external 5 V VBUS power to the PMIC. J202 is a passive connector symbol, not an active power output. | Placed `#FLG0201` (`power:PWR_FLAG`) on `VBUSIN` at J202 pin 1 in `02_POWER.kicad_sch`. | No | CLEARED |
| 4 | `U9.13` (`VBAT`) | `power_pin_not_driven` | C | Battery connector J201 supplies `VBAT` to PMIC and downstream consumers (including nRF7002 U9.13). J201 is a passive connector symbol. | Placed `#FLG0202` (`power:PWR_FLAG`) on `VBAT` at J201 pin 3 in `02_POWER.kicad_sch`. | No | CLEARED |
| 4 | `#PWR1G001.1` (`GND`) | `power_pin_not_driven` | C | System ground reference originates from external battery return at J201 pin 1. Connector pin is passive. | Placed `#FLG0203` (`power:PWR_FLAG`) on `GND` at J201 pin 1 in `02_POWER.kicad_sch`. | No | CLEARED |
| 5 | `U201.2` (`PVSS1`) | `power_pin_not_driven` | D | Nordic nPM1300 PS v1.3 §9.3 Reference Circuitry specifies separate PVSS1 power ground island joined to PCB GND through net tie NT201 for noise isolation. Net ties isolate power domains in KiCad. | Placed `#FLG0204` (`power:PWR_FLAG`) on `PVSS1` at net tie NT201 pin 1 in `02_POWER.kicad_sch`. | No | CLEARED |
| 5 | `U201.6` (`PVSS2`) | `power_pin_not_driven` | D | Nordic nPM1300 PS v1.3 §9.3 Reference Circuitry specifies separate PVSS2 power ground island joined to PCB GND through net tie NT202. | Placed `#FLG0205` (`power:PWR_FLAG`) on `PVSS2` at net tie NT202 pin 1 in `02_POWER.kicad_sch`. | No | CLEARED |
| 6 | `U12.C5` (`PD_GND`) | `power_pin_not_driven` | D | Maxim MAX86141 datasheet Fig 37 & layout guidelines recommend dedicated photodiode analog ground islands (PD_GND) tied once to system ground via net tie NT401. Net tie isolates domain in KiCad. | Placed `#FLG0401` (`power:PWR_FLAG`) on `PPG1_PD_GND` at net tie NT401 pin 1 in `04_PPG.kicad_sch`. | No | CLEARED |
| 6 | `U13.C5` (`PD_GND`) | `power_pin_not_driven` | D | Maxim MAX86141 datasheet Fig 37. Dedicated photodiode analog ground island for AFE2 tied to GND via net tie NT402. | Placed `#FLG0402` (`power:PWR_FLAG`) on `PPG2_PD_GND` at net tie NT402 pin 1 in `04_PPG.kicad_sch`. | No | CLEARED |
| 7 | `U9.15` (`RFBUCKVDD`) | `power_pin_not_driven` | D | Nordic nRF7002 PS v1.2 §7.1 Figure 19 shows BUCKOUT driving external inductor L601, whose output supplies RFBUCKVDD (pin 15) and PWRBUCKVDD (pin 32) via net `WIFI_VDD_BUCK`. Inductor L601 is a passive element, blocking KiCad power-out propagation. | Placed `#FLG0601` (`power:PWR_FLAG`) on `WIFI_VDD_BUCK` at inductor L601 pin 2 in `06_WIFI.kicad_sch`. | No | CLEARED |
| 3 | `U9.8` (`PAVDD<1>`) / `U9.10` (`PAVDD<0>`) | `pin_to_pin` | E | Nordic nRF7002 PS v1.2 Table 24 and Fig 19 show PAVDD<1> (pin 8) and PAVDD<0> (pin 10) are internal supply/decoupling pins tied together and decoupled to GND via C12. They are internal nodes, not independent external regulators. Modeling both as `power_out` created a false ERC conflict. | Changed electrical type of pin 8 and pin 10 from `power_out` to `passive` in `libraries/symbols/2026-09-16_06-57-34.kicad_sym` and `06_WIFI.kicad_sch` cache. | No | CLEARED |
| 8 | `U106.7` (`VREF2`) | `power_pin_not_driven` | E | TI PCA9306 datasheet Figure 9-1. VREF2 is an internal gate bias reference pin biased through a 200 kΩ pull-up resistor to SYS_3V3; it is not a power supply rail input. Modeling pin 7 as `power_in` was a symbol error. | Corrected Pin 7 electrical type from `power_in` to `passive` in `libraries/symbols/sportwatch_custom.kicad_sym` and `01_APOLLO510B.kicad_sch` cache. | No | CLEARED |
| 10 | `J1301.3` (`nRESET`) | `pin_not_driven` | E | Tag-Connect TC2030-CTX-NL debug connector J1301 is a debug interface header where an external debugger drives the target MCU reset (`APOLLO_RST_N`). Modeling the connector pin as `input` caused KiCad to treat it as an un-driven internal consumer. | Corrected Pin 3 electrical type from `input` to `passive` on `TC2030-CTX-NL_TARGET` in `libraries/symbols/sportwatch_custom.kicad_sym` and `13_DEBUG.kicad_sch` cache. | No | CLEARED |
| 2 | `U12.A1` (`VLED`) / `U13.A1` (`VLED`) | `power_pin_not_driven` | G | MAX86141 AFE requires LED anode driver supply (3.1 V – 5.5 V). Project architecture intentionally leaves `PPG_VLED` regulator design TBD pending LED current/power budgeting. | None (retained as documented TBD per explicit user instruction; no artificial regulator added). | No | RETAINED (1 error, intentional TBD) |


## Open Design Decisions

- `PPG_VLED` regulator/source remains intentionally TBD.
- PMIC IRQ/SHPHLD or other optional control signals are not allocated until a defined firmware/power-state requirement exists.
- Antenna MPNs and several mechanical/RF footprints remain TBD.
- Power/current/startup budget and protected-VBAT Wi-Fi charging behavior remain engineering validation items.

## Files Modified

- `/home/sapy/sportwatch_ai/docs/project/hierarchy_integration_status.md`
- Git branch metadata in `/home/sapy/sportwatch_ai/sportwatch_revA/.git` (new branch only)
- Pre-existing and preserved: `/home/sapy/sportwatch_ai/sportwatch_revA/06_WIFI.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/sportwatch_revA.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/01_APOLLO510B.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/02_POWER.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/03_DISPLAY.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/04_PPG.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/05_GNSS.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/07_MOTION.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/08_ENVIRONMENT.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/09_STORAGE.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/10_HAPTICS.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/11_BUTTONS.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/13_DEBUG.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/14_RF.kicad_sch`
- `/home/sapy/sportwatch_ai/sportwatch_revA/sym-lib-table`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/sportwatch_custom.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/nordic-lib-kicad-npm.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_05-56-22.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_05-57-26.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_05-59-08.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_06-31-04.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_06-45-24.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_06-57-34.kicad_sym`
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_07-42-39.kicad_sym`
- `/home/sapy/sportwatch_ai/docs/project/hierarchy_integration_changes.md`

Post-`cb6430a` files changed for 18-ERC adjudication:

- `/home/sapy/sportwatch_ai/sportwatch_revA/01_APOLLO510B.kicad_sch` (PCA9306 VREF2 passive symbol cache)
- `/home/sapy/sportwatch_ai/sportwatch_revA/02_POWER.kicad_sch` (PWR_FLAG on VBUSIN, VBAT, GND, PVSS1, PVSS2; no-connects on SHPHLD, LSIN1, LSIN2)
- `/home/sapy/sportwatch_ai/sportwatch_revA/04_PPG.kicad_sch` (D401.7 / D402.7 green cathode connections; PWR_FLAG on PPG1_PD_GND, PPG2_PD_GND)
- `/home/sapy/sportwatch_ai/sportwatch_revA/06_WIFI.kicad_sch` (PWR_FLAG on WIFI_VDD_BUCK; no-connect on U11.5 QOD; PAVDD<0>/<1> passive symbol cache)
- `/home/sapy/sportwatch_ai/sportwatch_revA/13_DEBUG.kicad_sch` (TC2030-CTX-NL nRESET passive symbol cache)
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/2026-09-16_06-57-34.kicad_sym` (nRF7002 PAVDD<0>/<1> passive)
- `/home/sapy/sportwatch_ai/sportwatch_revA/libraries/symbols/sportwatch_custom.kicad_sym` (PCA9306 VREF2 passive, TC2030-CTX-NL nRESET passive)
- `/home/sapy/sportwatch_ai/docs/project/hierarchy_integration_status.md`

## Last Safe Resume Point

All 18 ERC errors adjudicated and resolved (17 resolved cleanly, 1 intentionally unresolved Class G `PPG_VLED` error retained). Native interface check passes with 83/83 matches (`checked=83 mismatches=0`). Zero unintended net changes across all 371 project nets.

Validated symbol-correction commit: `cb6430a` (`fix(kicad): correct PPG tri-state and eMMC hidden pins`) on `fix/revA-hierarchy-integration`.
Validated ERC-adjudication commit: `dcbca3e` (`fix(kicad): adjudicate and resolve native ERC errors`) on `fix/revA-hierarchy-integration`. The native commit gate was `checked=83 mismatches=0` and 1 intentional Class G ERC error (`PPG_VLED`).


## Commands Used

- `git status --short --branch`
- `git switch -c fix/revA-hierarchy-integration`
- `akcli doctor --json`
- `akcli read <sheet>.kicad_sch --summary --json`
- `rg -n '\\(sheet_instances|\\(hierarchical_label|\\(label |\\(global_label' ...`
- Native netlist export through the Flatpak runtime loader to `/tmp/watch_hierarchy/baseline.xml`.
- Native ERC through the Flatpak runtime loader to `/tmp/watch_hierarchy/erc-baseline.json`.
- `akcli calc i2c-pullup vdd=1.8 cb=50p mode=fast --json`
- `akcli calc i2c-pullup vdd=1.8 cb=70p mode=fast --json`
- `akcli render sportwatch_revA.kicad_sch -o /tmp/watch_hierarchy/root-hierarchy.svg`
- Native post-hierarchy netlist export through the Flatpak runtime loader to `/tmp/watch_hierarchy/post-hierarchy.xml`.
- Native final netlist export to `/tmp/watch_hierarchy/final.xml`.
- Final 83-interface native membership comparison: `checked=83 mismatches=0`.
- `akcli library lint-symbols <library>.kicad_sym --json --fail-on never`
- `git diff --check`
- `git diff --cached --check`
- `git commit -m "refactor(kicad): integrate Rev-A hierarchy and libraries"`
- `akcli library lint-symbols libraries/symbols/2026-09-16_07-42-39.kicad_sym --json --fail-on never`
- `akcli library lint-symbols libraries/symbols/sportwatch_custom.kicad_sym --json --fail-on never`
- Native final symbol-fix netlist export to `/tmp/watch_hierarchy/final-symbol-fixes.xml`.
- Native final symbol-fix ERC to `/tmp/watch_hierarchy/erc-final-symbol-fixes.json`.
- Final full-net comparison: 373 native nets unchanged from the pre-eMMC state.
- Final hierarchy comparison: `checked=83 mismatches=0`.
- `git commit -m "fix(kicad): correct PPG tri-state and eMMC hidden pins"`
