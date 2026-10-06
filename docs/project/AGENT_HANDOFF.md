# Agent Handoff: Sportwatch Rev-A PCB Foundation & Critical-Cluster Feasibility

## Current Verified Baseline (Mandatory Start)
- **Date:** 2026-10-06
- **Git Branch:** `pcb/revA-floorplan`
- **Git HEAD:** `91cfae0341107fb2096bf857d8ebe3208f8be40b`
- **Working Tree:** Clean
- **Live PCB Status (KiCad MCP Pro Inspection):**
  - Footprints: 228
  - Nets: 390
  - Tracks: 0
  - Vias: 0
  - Zones: 0
  - Graphic shapes: 0 (No `Edge.Cuts` defined)
  - Configured copper layers: 2 (`F.Cu`, `B.Cu`)
  - Stackup: Default 2-layer FR4 (2.32 mm nominal)
  - Project Design Rules (`.kicad_dru`): None
  - Envelope Status: 44.0 mm circular envelope classified MARGINAL and superseded.
  - Floorplan Gate Status: BLOCKED pending physical/manufacturing foundation.

## Target Objectives (Current Phase)
1. **Task A — HDI / Fabrication Feasibility:**
   - Analyze escape requirements for Ambiq Apollo510B (WFBGA153, 0.40 mm pitch, 0.22 mm NSMD pad, ~0.18 mm gap) and Kingston eMMC 5.1 (FBGA153, 0.50 mm pitch).
   - Establish realistic candidate HDI technology (layer count, core/prepreg, board thickness, min trace/space, laser microvia drill/pad, via-in-pad VIPPO, stacked vs staggered, buried vias).
   - Document manufacturer capability matrix.
2. **Task B — Mechanical Envelope Update:**
   - Update provisional circular PCB outline to 46.0 mm outer diameter ($R = 23.0\text{ mm}$), targeting 49–52 mm smartwatch casing.
   - Re-evaluate area and perimeter density with mechanical, optical, and RF keepouts.
3. **Task C — KiCad Board Foundation:**
   - Commit git checkpoint before PCB modification.
   - Create provisional `Edge.Cuts` (46.0 mm circle).
   - Configure candidate multilayer HDI stackup.
   - Establish net classes and design rules (`.kicad_dru`).
   - Preserve netlist and schematic exactly.
4. **Task D — Courtyard Completion:**
   - Investigate and add missing courtyards for `NT201`, `NT202`, `NT401`, `NT402`, `U5`, `U7`.
5. **Task E — Critical Cluster Feasibility:**
   - Develop and validate provisional placement for the 7 designated critical clusters.
6. **Task F — Fanout Trial:**
   - Perform representative escape fanout for Apollo510B and eMMC to prove microvia geometry and layer routability.
7. **Task G — Documentation & Final Gate Determination:**
   - Create `docs/project/pcb_foundation_revA.md` and `docs/project/critical_cluster_feasibility.md`.
   - Update this handoff with final verdict (`PASS` or `BLOCKED`).
