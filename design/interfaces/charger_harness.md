# Separate charger harness / contact assembly — revision 1

CHARGER/HARNESS ownership: four abstract external contacts C1..C4 and dedicated power/return wiring. Physical order provisionally **GND / +5V / +5V / GND**, two logical nets only. Both +5V contacts join CHG_RAW_5V and both GND contacts join system GND through a dedicated charger return. MAIN endpoint J202 is now on 12_CHARGING: **1=CHG_RAW_5V, 2=GND**. The earlier J202 external-contact role is superseded; pin1 changes from protected VBUSIN to raw input by deliberate protection ECO.

No charging power or routed charging return uses J1501/J1502, PD_GND, NT401/NT402 or optical guards. Returns join common GND at MAIN charging input region. No permanent watch magnet. Rear/east contact assembly is separate from the central optical board.

C1/C4 are common GND, C2/C3 are raw dock +5 V; dock → watch direction, nominal +5 V, default disconnected/off, no pull-ups. Current class is power: qualify supply input including system consumption, battery charge, inrush and shorts, not merely the <=400 mA initial charge-current setting. Keyed/recessed nonmagnetic dock with travel stops and current-limited source is required; symmetric contact order does not protect shifted/partial engagement or wet shorts. Mating convention is looking into each mating face with C1 marked. Physical pad/cable mapping remains TBD until vendor drawings and continuity test.

## Evidence-based provisional protection

Primary evidence: [Nordic nPM1300 PS v1.3](https://docs-be.nordicsemi.com/bundle/nPM1300_PS_v1.3/raw/resource/enus/nPM1300_PS_v1.3.pdf), local source `../datasheets/power/nPM1300_PS_v1.3.pdf`, sections 4, 5 and 6.1. Local SHA-256 recorded in `charger_harness.json`. [Nordic SYSREG documentation](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/vbusin.html) also describes the built-in protection.

VBUS recommended operating range is **4.0–5.5 V** (p18). Absolute VBUS limits relative to ground are **−0.3 to +22 V** (p17); these are stress limits, not normal operating limits. The functional overview describes transient tolerance to 22 V. SYSREG has nominal **5.5 V** OV threshold, UV detection and isolation preventing VSYS→VBUS current when outside valid range (pp20–22). Default VBUS limit is 100 mA; firmware can configure higher supported limits only after establishing source capacity. Its internal current limit protects the downstream PMIC path; it does not protect an upstream wet-contact/harness short.

No guaranteed sustained negative-input tolerance beyond −0.3 V is established. Built-in VSYS backflow isolation is not a reverse-polarity guarantee. Component HBM 2 kV / CDM 500 V ratings (p17) are not exposed-contact system IEC 61000-4-2 qualification. The primary specification does not provide a complete contact-system surge envelope; define dock/cable and system test requirements before selection.

MAIN 12_CHARGING contains **U1201**, an explicit mandatory functional provision for a series OV-disconnect, reverse-polarity/reverse-current blocking and current/fault-limit stage, between CHG_RAW_5V and VBUSIN. Its three pins are functional terminals, **not a silicon package pinout or a selected IC**. Implementation may require a controller and opposed MOSFETs or a qualified integrated device. No wire bypass is allowed. U201.21 and C201.1 remain on protected VBUSIN; C201 stays local to U201, electrically unchanged. **D1201** is a local protected-node TVS provision; final MPN, clamp and footprint remain TBD.

Harness provision **ESD_ENTRY** is mandatory immediately behind exposed feedthroughs, returning locally into the dedicated charger return. It is recorded in the harness BOM/contract, not counted as a KiCad MAIN or REAR component. Its device(s) and package are TBD. It prevents a long unprotected ESD path through the watch. A remote main TVS alone is insufficient to demonstrate this.

Before device freeze, establish maximum normal dock voltage, wrong-adapter maximum/sustained duration, reverse-voltage magnitude/duration, fault current and cable inductance; specify ESD polarity/level and discharge path. Select entry TVS standoff above normal maximum and coordinate its worst-case clamp/overshoot with series stage input ratings. Set guaranteed OV cutoff including tolerance to protect PMIC operation and prevent downstream sustained >5.5 V; ensure protected-node transient stays below +22 V and above −0.3 V with margin. Reverse blocking must withstand the defined negative envelope and PMIC-to-contact backflow with no power present. Verify current-limit/fuse coordination, wet short behavior, thermal SOA, restart policy and inrush. TVS is a transient shunt and is not credited for sustained OV or reverse polarity. An output unidirectional TVS forward drop alone is not guaranteed to keep VBUS above −0.3 V.

Provisions document required architecture and verified PMIC constraints; they are **not selected/populated protection hardware**. No hardware ordering, charging safety, transient immunity or full electrical sign-off is claimed by Phase 1. Independent electrical review must close/approve selection gates before physical implementation.

## Battery and mechanics

MAIN J201 live wiring is 1=GND/BAT−, 2=BAT_NTC, 3=VBAT/BAT+. C206 is 2.2 µF VBAT→GND. The functional battery contract BAT+/NTC/BAT− is independent of future physical connector numbering. Battery MPN/termination/footprint remain mechanical TBD.

Contact spacing, metallurgy, recess, sealing, dock force, contact MPN and any contact PCB/flex outline remain placement gates. If a fabricated contact PCB/flex replaces this purchased harness, create its own schematic project, BOM/rules/stackup and independent ERC/netlist/DRC; do not silently inherit MAIN rules or add it as a MAIN child.
