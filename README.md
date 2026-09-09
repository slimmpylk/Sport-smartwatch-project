# Sportwatch

**A personal end-to-end smart/sport watch engineering project — custom electronics, PCB design, embedded software and system integration.**

This project is my attempt to design and build a complete sport-focused smartwatch from the ground up rather than assembling an existing development platform.

I am responsible for the full engineering workflow: component selection, datasheet analysis, schematic design, PCB architecture and layout, power design, sensor integration, RF-related design decisions, hardware bring-up, and eventually the embedded software running on the device.

> **Current phase:** hardware development. The schematic architecture is being designed in KiCad and the PCB will follow. Firmware and higher-level software development will begin as the hardware reaches the bring-up stage.

---

## Project goals

The goal is to build a compact wearable platform capable of supporting the core functions expected from a modern sport watch, while using the project as a practical system-level embedded engineering exercise.

The design includes:

- low-power application processor
- battery charging and power management
- AMOLED display
- GNSS
- inertial sensing
- magnetometer
- barometric pressure / altitude sensing
- temperature sensing
- ambient light sensing
- optical heart-rate / PPG hardware
- non-volatile storage
- haptic feedback
- wireless / RF subsystem
- physical buttons, charging and debug interfaces

The project is intentionally developed at component and PCB level rather than around a ready-made smartwatch module.

---

## Hardware architecture

| Subsystem | Main components / focus |
|---|---|
| Application processor | Ambiq Apollo510B |
| Power | Nordic nPM1300 PMIC |
| Display | RM69330-based round AMOLED |
| Motion | ST LSM6DSV16X IMU |
| Magnetometer | Bosch BMM350 |
| Pressure / altitude | Bosch BMP585 |
| Temperature | MAX30208 |
| Ambient light | OPT4001 |
| Optical sensing | MAX86140 / MAX86141 with discrete optical components |
| GNSS | u-blox MAX-F10S |
| Storage | eMMC |
| Haptics | TI DRV2625 |

Component choices and interfaces are verified against manufacturer datasheets as the design progresses.

---

## KiCad design organization

The schematic is divided into functional hierarchical sheets so each subsystem can be developed and reviewed independently.

```text
sportwatch_revA/
├── 01_APOLLO510B.kicad_sch
├── 02_POWER.kicad_sch
├── 03_DISPLAY.kicad_sch
├── 04_PPG.kicad_sch
├── 05_GNSS.kicad_sch
├── 06_WIFI.kicad_sch
├── 07_MOTION.kicad_sch
├── 08_ENVIRONMENT.kicad_sch
├── 09_STORAGE.kicad_sch
├── 10_HAPTICS.kicad_sch
├── 11_BUTTONS.kicad_sch
├── 12_CHARGING.kicad_sch
├── 13_DEBUG.kicad_sch
├── 14_RF.kicad_sch
├── sportwatch_revA.kicad_sch
├── sportwatch_revA.kicad_pcb
├── sportwatch_revA.kicad_pro
├── fp-lib-table
├── sym-lib-table
└── libraries/
```

Custom symbols and footprints are kept with the project so the design remains portable between machines.

---

## Engineering focus

This project is primarily intended to demonstrate practical embedded hardware and system engineering, including:

- schematic capture and PCB design in **KiCad**
- reading and applying semiconductor datasheets
- component selection and interface design
- power-tree and battery-powered system design
- SPI / I²C and other digital interfaces
- mixed-signal sensor integration
- optical sensing / PPG subsystem design
- GNSS and RF integration
- decoupling, grounding and power-integrity considerations
- footprint verification against mechanical package drawings
- hierarchical schematic architecture
- hardware/software interface planning
- design validation before PCB manufacture
- Git-based engineering workflow and documentation

---

## Current development status

### Hardware

- [x] System architecture divided into functional schematic sheets
- [x] Initial power subsystem design
- [x] Application processor integration started
- [x] Motion-sensor integration
- [x] Custom symbols and footprints integrated where required
- [ ] Complete remaining schematic subsystems
- [ ] Full ERC and design review
- [ ] PCB placement
- [ ] PCB routing
- [ ] RF/layout review
- [ ] DRC and manufacturing review
- [ ] Prototype fabrication
- [ ] Hardware bring-up

### Software

Software development will follow the hardware bring-up phase.

Planned work includes:

- board-support and low-level drivers
- sensor acquisition
- power management
- display/UI integration
- GNSS handling
- activity and sport-related data processing
- storage
- device communications
- test and diagnostic tooling

The software side will be developed as part of the same project rather than treated as a separate pre-built platform.

---

## Repository structure

```text
sportwatch_ai/
├── README.md
├── datasheets/
├── docs/
└── sportwatch_revA/
```

`datasheets/` contains component documentation used during design.

`docs/` contains project notes and engineering handoff/documentation material.

`sportwatch_revA/` contains the active KiCad hardware project.

---

## Development philosophy

The project is built around a simple principle: **understand and own the complete system**.

Rather than limiting the work to one layer, I want to work across the boundary between electronics and software — from component datasheets and PCB connectivity to low-level embedded code and final device behaviour.

That means the project evolves through the same stages as a real embedded product:

**requirements → architecture → schematic → PCB → prototype → bring-up → firmware → system integration → testing**

---

## Status

This repository is a work in progress and reflects an actively developed engineering project. The current focus is the PCB and electronics design phase, so incomplete sheets, un-routed PCB content and design changes are expected until the first hardware revision is finalized.
