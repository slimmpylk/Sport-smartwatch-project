# Rev-A display implementation — 2026-09-16

The DISPLAY sheet is implemented and locally validated. **System integration is still required before PCB release:** 02_POWER uses local VSYS and SYS_3V3 labels, which do not connect across sheets. DISPLAY exports global nets of those names; the later integration pass must export the actual power sources and allocate Apollo pins. No other schematic was changed. No artificial power flags or ERC exclusions were added.

## Deliverables

- ../../03_DISPLAY.kicad_sch — 24-pin module interface, QSPI, I2C, power, defaults and engineering notes.
- ../../03_DISPLAY.kicad_sch.pre-display-20260916.bak — exact original sheet before editing.
- ../../libraries/symbols/sportwatch_display.kicad_sym — named, electrically typed module-interface symbol.
- ../../sym-lib-table — registers sportwatch_display; existing libraries preserved.
- ../../libraries/footprints/sportwatch_custom.pretty/OK-23GF024-04.kicad_mod — motherboard socket. Existing fp-lib-table already registers sportwatch_custom.
- This directory: authoring op-list, pin specification, intended nets, read-only verification script and validation artifacts.

The active J1 value is ZC-A1D43W-046; its PCB/BOM part is OCN OK-23GF024-04, identified in the MPN property. The display assembly itself must also be ordered as ZC-A1D43W-046. CO5300AF-08, CHSC6417 and BV6802W are internal to that assembly, not separate motherboard components.

## Sources and decisions

Source PDFs are fingerprinted in validation/sources.sha256.

- Module production specification P9 defines all 24 electrical connections. Pin 6 is spelled SPI_I01 on P9 (SPI_SI01 on P5); it maps to DISP_QSPI_IO1.
- P5 specifies OK-23GM024-04 male on the module. P6 specifies VDD 3.15/3.3/3.45 V and battery supply 2.9/3.7/5.5 V min/typ/max.
- Pin 16 P5/P9 discrepancy is retained verbatim on the sheet, with P9 TP_VDD naming as authorized. Pins 15 and 16 both connect to SYS_3V3.
- P9 specifies IM1 NC and MTP NC/Ground. NC is used for both pins 9 and 10, consistent with P5 MTP/NC.
- CO5300 pp14,100,101,116 establish active-low reset, no internal reset pull-high, power/reset ordering and command delays. The sheet uses timing bounds satisfying both reset and power-sequence sections, including 120 ms before Sleep Out following reset.
- CHSC6417 v1.3.1 and v1.3.0 sections 6/8 and Table 8-1 were checked: reset low before power changes, >=500 us reset pulse, up to 200 ms readiness, <=5 ms supply rise, and >=2 ms below 0.3 V for a power cycle. The narrative says >1 ms; >=2 ms satisfies both statements. Shared I2C must remain idle during touch reset; an unpowered touch controller can load the bus.
- The supplied module PDF does not state VCI_EN polarity/delays, internal host-pin bias, or a complete initialization sequence. These remain supplier/bring-up checks; R306 is DNP. Bare-chip internal analog rail circuitry and reference passives were not copied onto the motherboard.

## Passives

All resistors have 0402 metric-1005 footprints, 1% tolerance, >=25 V / 0.063 W requirements.

| References | Value / assembly | Purpose and basis |
|---|---|---|
| R301, R302 | 3.6 kohm, native KiCad DNP | Optional SDA/SCL pull-ups to SYS_3V3; fit only if the final bus lacks suitable pull-ups. |
| R303, R304 | 10 kohm, fitted | Hold display/touch active-low reset low while host pins are high impedance. |
| R305 | 10 kohm, fitted | Keep active-low QSPI CS deselected at startup. |
| R306 | 10 kohm, native KiCad DNP | Optional VCI_EN pull-down, conditional on supplier confirmation of polarity and internal bias. |

The touch documents supply no resistor value or quantified I2C sink-current limit. The pull-up provisions are an engineering calculation, not a supplier-prescribed value: akcli i2c-pullup, 3.3 V, provisional 100 pF, standard mode (100 kHz), NXP UM10204 Rev.7 section 7.1, yields 966.7 ohm to 11.8 kohm and suggests E24 3.6 kohm. At 100 pF, nominal rise time is about 305 ns; sink current at 0.4 V is about 0.806 mA. The calculation assumes the standard 3 mA sink capability, which must be confirmed for the module and chosen host. Recalculate for the actual bus capacitance, speed and existing parallel pull-ups before fitting.

The 10 kohm biases are explicit board design choices, snapped with akcli eseries (IEC 60063); 0.33 mA / 1.09 mW at 3.3 V. Verify module internal bias and GPIO drive at bring-up. No external decoupling requirement is specified in the supplied module interface documentation; bare-controller capacitor networks were not duplicated. Check connector rail transients on hardware before release.

## Connector footprint

The OCN family PDF P1/P3 mating section explicitly mates GM header with GF socket at 0.8 mm mating height. P3 names GF as SOCKET; the 24-contact row gives A=7.32 mm, B=4.40 mm.

| Feature | Implemented dimensions |
|---|---|
| Body | 7.32 x 2.54 mm nominal |
| Signals | 2 rows of 12, exactly 0.40 mm pitch |
| Signal lands | 0.23 x 0.50 mm; centers y=+/-1.20 mm |
| Signal row span | 2.90 mm outside / 1.90 mm inside |
| Hold-down lands | Four unnumbered pads, 0.60 x 0.785 mm |
| Hold-down centers | x=+/-3.03 mm, y=+/-1.0575 mm |
| Hold-down inner gap | 1.33 mm; outside span 2.90 mm |
| Hold-down corner cuts | Four 0.20 mm outside chamfers |
| Insulation areas | Two F.Cu keepouts, x=-2.315..+2.315 mm, y=0.10..0.95 and -0.95..-0.10 mm |
| Courtyard | x=+/-4.00 mm, y=+/-1.75 mm |

Land lengths and centers are derived from the manufacturer's dimensioned outside/inside spans, not image scaling. Keepouts conservatively prohibit exposed conductive features/copper on the mounting-side insulation areas.

Numbering is defined by the display assembly P5, because the generic OCN footprint drawing does not enumerate all 24 contacts. With the P5 male front-view layout 1..12 above and 24..13 below, reflect across the long axis to view the mating motherboard socket: **F.Cu view bottom row 1..12 left-to-right; top row 24..13 left-to-right**. Fab corner and silk triangle identify pin 1 at lower left. Do not substitute an odd/even numbered two-row footprint. Mechanical placement must match this numbering to the actual folded FPC pin-1 corner; a 180-degree assembly placement swaps ends.

## Validation

- KiCad **10.0.5** parsed and exported the schematic SVG, XML netlist and footprint SVG.
- verify_display.py passed all 24 native KiCad pin-to-net comparisons, all passive endpoints, exact pin/wire/label attachment, NC only on pins 9/10, DNP flags, footprint pad numbering and dimension assertions.
- akcli integrity + layout + intended-net assertions: **0 findings**. Its separate net-hygiene check reports seven single-pin host nets; these await Apollo allocation.
- Native KiCad ERC **ran but did not pass**: exit 5, **4 errors + 7 warnings**, retained without exclusions in validation/erc.json. Errors: undriven SPI_CLK and three undriven power nets (VSYS, SYS_3V3, GND) when checking DISPLAY alone. Warnings: isolated labels for QSPI clock/data, TE and TOUCH_INT awaiting host connections. There are no library-link warnings with the installed/project libraries loaded.
- All 14 non-DISPLAY schematics, including the root, 01_APOLLO510B and 02_POWER, matched pre-edit SHA-256 hashes. Existing unrelated work was preserved.
- This is a module interface; no behavioral SPICE model was supplied for the assembly. No module simulation or physical bring-up is claimed.

The installed Flatpak launcher failed in this execution environment. Native checks used the installed KiCad 10.0.5 binary with its matching runtime libraries and temporary library configuration; a missing API-schema-path startup message did not prevent ERC/netlist/SVG generation.

Useful normal-workstation commands:

```sh
kicad-cli sch erc --format json --exit-code-violations -o erc.json 03_DISPLAY.kicad_sch
kicad-cli sch export netlist --format kicadxml -o display-netlist.xml 03_DISPLAY.kicad_sch
python design/03_DISPLAY/verify_display.py display-netlist.xml
akcli check 03_DISPLAY.kicad_sch --integrity --layout --intent design/03_DISPLAY/intent.json
```

The Python audit requires the akcli package. ops.json records geometry authoring, not an unrestricted replay command: final native DNP flags, actual project instance paths, unique power-symbol references, label direction types and J1 field placement were applied after authoring. Use the delivered sheet as the baseline for future edits.

## Visual / integration handoff

Open the root KiCad project and reload/revert the schematic from disk before saving an already-open editor. Inspect J1 pin-1 orientation against the physically folded FPC and the socket placement side. Review DNP population for R301/R302/R306, then export power nets and allocate a 3.3 V Apollo interface bank in the later global integration pass. Check reset/enable sequencing and rail transients on a real module before PCB release.

The complete final 24-pin mapping is in validation/pin-audit.md, independently checked against validation/display-netlist.xml.
