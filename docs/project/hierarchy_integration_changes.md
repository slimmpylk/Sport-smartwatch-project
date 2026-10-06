# Rev-A Hierarchy Integration Changes

## Summary

The Rev-A root schematic now explicitly integrates all 83 implemented cross-sheet interfaces through child hierarchical labels, matching root sheet pins, and root wiring. Native KiCad netlist comparison against the pre-edit child nets reports `checked=83 mismatches=0`. The completed POWER, WIFI, STORAGE, and RF local fixes remain present.

Project-wide annotation is unique, project-local symbol libraries are registered and pinned to the saved audited symbol definitions, and all known matching project footprints are qualified. `PPG_VLED` remains intentionally unresolved because its regulator/source is still TBD.

## Files Modified

- `sportwatch_revA.kicad_sch`
- `01_APOLLO510B.kicad_sch`
- `02_POWER.kicad_sch`
- `03_DISPLAY.kicad_sch`
- `04_PPG.kicad_sch`
- `05_GNSS.kicad_sch`
- `06_WIFI.kicad_sch`
- `07_MOTION.kicad_sch`
- `08_ENVIRONMENT.kicad_sch`
- `09_STORAGE.kicad_sch`
- `10_HAPTICS.kicad_sch`
- `11_BUTTONS.kicad_sch`
- `13_DEBUG.kicad_sch`
- `14_RF.kicad_sch`
- `sym-lib-table`
- `libraries/symbols/sportwatch_custom.kicad_sym`
- `libraries/symbols/nordic-lib-kicad-npm.kicad_sym`
- `libraries/symbols/2026-09-16_05-56-22.kicad_sym`
- `libraries/symbols/2026-09-16_05-57-26.kicad_sym`
- `libraries/symbols/2026-09-16_05-59-08.kicad_sym`
- `libraries/symbols/2026-09-16_06-31-04.kicad_sym`
- `libraries/symbols/2026-09-16_06-45-24.kicad_sym`
- `libraries/symbols/2026-09-16_06-57-34.kicad_sym`
- `libraries/symbols/2026-09-16_07-42-39.kicad_sym`
- `docs/project/hierarchy_integration_status.md`
- `docs/project/hierarchy_integration_changes.md`

`12_CHARGING.kicad_sch`, `fp-lib-table`, and the custom footprint files were inspected but did not require edits.

## Hierarchy Strategy

Normal application signals and named power rails use hierarchical labels in child sheets, matching sheet pins in `sportwatch_revA.kicad_sch`, and explicit root wiring. Root local labels join the sheet-pin stubs into one native KiCad net. GND continues to use normal KiCad global power handling.

Private RF matching nodes, internal regulator nodes, analog references, SIMO nodes, PPG photodiode/reference nodes, and crystal nodes remain local. Display global labels were replaced with one hierarchical label per exported net plus local labels for repeated connections inside the display sheet.

## Completed Cross-Sheet Nets

- Power: `VBAT`, `VSYS`, `VOUT1_1V8`, `VOUT2_3V0_PROVISIONAL`, `SYS_3V3`.
- Shared PMIC/magnetometer bus: `MAG_I2C_SDA`, `MAG_I2C_SCL`; motion interrupt `MAG_INT`.
- Display/touch: `DISP_QSPI_CLK`, `DISP_QSPI_CS`, `DISP_QSPI_IO0`–`IO3`, `DISP_RST`, `DISP_TE`, `DISP_VCI_EN`, `TOUCH_SDA`, `TOUCH_SCL`, `TOUCH_INT`, `TOUCH_RST`.
- Motion: `IMU_SPI_SCK`, `IMU_SPI_MOSI`, `IMU_SPI_MISO`, `IMU_SPI_CS`, `IMU_INT1`, `IMU_INT2`.
- Environment: `ENV_I2C_SDA`, `ENV_I2C_SCL`, `BARO_INT`, `ALS_INT`.
- GNSS: `GNSS_UART_TX`, `GNSS_UART_RX`, `GNSS_TIMEPULSE`, `GNSS_EXTINT`, `GNSS_RF`.
- Wi-Fi: `WIFI_QSPI_CLK`, `WIFI_QSPI_CS`, `WIFI_QSPI_IO0`–`IO3`, `WIFI_HOST_IRQ`, `WIFI_BUCKEN`, `WIFI_IOVDD_EN`, `WIFI_COEX_STATUS`, `WIFI_COEX_REQ`, `WIFI_COEX_GRANT`, `WIFI_RF`.
- eMMC: `EMMC_CLK`, `EMMC_CMD`, `EMMC_DAT0`–`DAT7`, `EMMC_RST_N`.
- PPG host: `PPG_SPI_SCLK`, `PPG_SPI_MOSI`, `PPG_SPI_MISO`, `PPG1_CS_N`, `PPG2_CS_N`, `PPG1_INT_N`, `PPG2_INT_N`, `PPG_SAMPLE_SYNC`.
- Haptics: `HAPTIC_I2C_SCL`, `HAPTIC_I2C_SDA`, `HAPTIC_NRST`, `HAPTIC_TRIG_INTZ`.
- Buttons: `BTN_BACK_N`, `BTN_UP_N`, `BTN_START_N`, `BTN_DOWN_N`, `BTN_LIGHT_N`.
- Debug: `APOLLO_SWCLK`, `APOLLO_SWDIO`, `APOLLO_SWO_GPIO28`, `APOLLO_RST_N`.
- BLE RF: `APOLLO_BLE_ANT`, `APOLLO_BLE_AVDD_PA`.

`PPG_VLED` was not exported because its regulator/source remains intentionally TBD. Optional PMIC IRQ/control signals were not allocated without a defined firmware or power-state requirement.

The nPM1300 and BMM350 share Apollo IOM0 on GPIO5/GPIO6. Their two fitted 10 kΩ pull-up pairs produce 5 kΩ effective pull-ups to 1.8 V. That value meets the 400 kHz rise-time window only when total bus capacitance is no more than about 70.8 pF, so layout capacitance remains a later validation item.

## Annotation Changes

- POWER: `C1`–`C15` -> `C201`–`C215`; `R1`–`R7` -> `R201`–`R207`; `L1`–`L3` -> `L201`–`L203`; `U1`/`U2` -> `U201`/`U202`; `NT1`/`NT2` -> `NT201`/`NT202`; `JBAT1`/`JCHG1` -> `J201`/`J202`; `#PWR001`–`#PWR018` -> `#PWR0201`–`#PWR0218`.
- MOTION: `C1`–`C5` -> `C701`–`C705`; `R1`/`R2` -> `R701`/`R702`; `U2`/`U3` -> `U702`/`U703`.
- STORAGE: `U1` -> `U901`.
- WIFI duplicate hidden power symbols: `#PWR0610` -> `#PWR0622`, `#PWR0603` -> `#PWR0623`, `#PWR0611` -> `#PWR0624`, and `#PWR0614` -> `#PWR0625` for the later UUID-qualified occurrences.

All symbol UUIDs were preserved. Direct enumeration finds 396 top-level symbols and 396 unique references; native export finds 218 exported components and 218 unique references.

## Library Changes

`sym-lib-table` now registers `sportwatch_custom`, `nordic-lib-kicad-npm`, `APOLLO510B_custom_symbols`, and all seven timestamp-named imported symbol libraries. The registered project libraries were regenerated from the exact saved schematic caches so audited pin mappings remain unchanged and native ERC reports no project-local missing-library or cached-symbol mismatch finding.

Known footprint IDs were qualified with `sportwatch_custom:` for the existing MAX86141, MAX-F10S, nRF7002, BMP585, MAX30208, OPT4001, and DRV2625 land patterns. The PCA9306 footprint was corrected to the installed `Package_SO:VSSOP-8_2.3x2mm_P0.5mm`. Components intentionally marked TBD retain blank/TBD footprints.

## ERC Before and After

- Baseline native ERC: 45 errors, 1780 warnings, 1825 total.
- After hierarchy only: 19 errors, 1652 warnings, 1671 total.
- Final native ERC with installed KiCad global tables: 19 errors, 1117 warnings, 1136 total.
- Final report: `/tmp/watch_hierarchy/erc-final-native-libs.json`.
- Final native netlist: `/tmp/watch_hierarchy/final.xml`.

Native ERC did run. It exits 5 because findings remain. The Flatpak binary also prints a host-loader schema-path warning for `/app/share/kicad/schemas/api.v1.schema.json`; it still completes and writes the ERC report.

## Unresolved Issues

- `PPG_VLED` regulator/source is TBD.
- Existing ERC errors: 10 power-input-not-driven, 4 input-not-driven, 3 unconnected pins, the shared dual-MAX86141 SDO output/output connection, and the nRF7002 PAVDD power-output/power-output connection.
- Existing ERC warnings: 1096 off-grid endpoints, 10 isolated provisional PMIC labels, 4 unconnected wire endpoints, 2 bidirectional/power-output classifications, 2 Wi-Fi VBAT multi-wire-label warnings, and 3 standard-library version mismatches.
- The project-local eMMC symbol preserves hidden NC/RFU/VSF pins stacked at `(0,0)`. Akcli symbol lint flags this as one error; changing it needs a separate, pin-map-controlled library repair.
- Antenna MPNs and several mechanical/RF footprints remain TBD.
- Power/current/startup budget, protected-VBAT Wi-Fi behavior during charging, and MAG_I2C layout capacitance remain engineering validation items.

## Exact Next Recommended Task

Review and resolve the remaining local circuit/ERC items without changing the completed hierarchy. Start with the dual-MAX86141 shared SDO topology because native ERC identifies two output pins on one net, then repair the eMMC hidden-pin library geometry against its audited pin map. After either change, rerun the native netlist comparison and native ERC commands recorded in `hierarchy_integration_status.md`.

## Post-Integration Symbol Corrections

The intentional shared `PPG_SPI_MISO` topology is retained. MAX86141 ball A3 `SDO` changed only from KiCad electrical type `output` to `tri_state` in `libraries/symbols/2026-09-16_07-42-39.kicad_sym` and the `04_PPG.kicad_sch` cache. Pin number, name, geometry, and net membership did not change. Native ERC removed the output/output conflict.

The Kingston FBGA153 mapping was checked against datasheet Table 9: 153 expected balls match 153 symbol pins with no missing or extra ball. In `libraries/symbols/sportwatch_custom.kicad_sym` and the `09_STORAGE.kicad_sch` cache, 107 NC, 7 RFU, and 6 VSF hidden pins moved from the shared `(0,0)` coordinate to 120 unique 100-mil-grid coordinates. Ball numbers, names, electrical types, visibility, and all connected power/SDIO nets are unchanged. Every hidden pin remains on its own native unconnected net.

Final results after both corrections:

- Native hierarchy comparison: `checked=83 mismatches=0`.
- Full native topology: all 373 nets identical to the pre-eMMC netlist.
- MAX86141 library lint: 0 errors, 0 warnings.
- `sportwatch_custom` lint: 0 errors, 163 pre-existing off-grid warnings.
- Native ERC: 18 errors and 1117 warnings, improved from 19 errors and 1117 warnings.
- Final netlist: `/tmp/watch_hierarchy/final-symbol-fixes.xml`.
- Final ERC report: `/tmp/watch_hierarchy/erc-final-symbol-fixes.json`.

The next task is the remaining 18 local ERC errors recorded exactly in `hierarchy_integration_status.md`; the hierarchy and corrected symbols should remain unchanged.

Validated project commit: `cb6430a` (`fix(kicad): correct PPG tri-state and eMMC hidden pins`) on branch `fix/revA-hierarchy-integration`.
