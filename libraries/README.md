# Project KiCad libraries

The project library tables in the parent directory register these assets with paths relative to `${KIPRJMOD}`.

- `symbols/` contains separate BMM350 and LSM6DSV16X libraries. They were inspected before relocation and contain distinct symbol names, so they remain separate and descriptive.
- `footprints/sportwatch_custom.pretty/` contains the project-specific KiCad footprints.
- `3dmodels/` is the home for project-specific STEP/WRL models. No custom 3D models were present during this cleanup.

The `-L`, `-M`, and nominal footprint files are preserved vendor variants. Some carry the same internal footprint name; do not merge, delete, or substitute them without checking the component datasheet and land-pattern dimensions. Existing schematic assignments intentionally select the nominal filenames.

The nPM1300 symbol used by `02_POWER.kicad_sch` remains embedded in that schematic. Its standalone source library was not present in the original repository, so this cleanup did not synthesize or alter one.
