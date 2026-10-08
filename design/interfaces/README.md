# Multi-board Phase 1 engineering contract and validation

Read `main_rear_interface.md` and `charger_harness.md` before editing either project. MAIN retains the existing root name; REAR is an independent root in `rear_sensor/`. Source checkpoint, original native netlist, original pin memberships and ownership are tracked here. Native counts exclude power-symbol/flag markers and include DNP provisions.

Final Phase 1 population: **MAIN 202 components / 359 nets; REAR 46 components / 44 nets** (44 existing + J1502 + DNP C1501). Harness has four physical contacts, two logical nets and three provisional assembly BOM lines; it has no KiCad root or fabricated PCB in this phase. MAIN has baseline 199 remaining components plus J1501/U1201/D1201. Existing J202 becomes the MAIN charging harness endpoint.

## Reproduce electrical validation

Use installed native KiCad 10.0.5 or compatible native CLI:

```sh
kicad-cli sch erc --severity-all --format json -o design/interfaces/validation/main_erc.json sportwatch_revA.kicad_sch
kicad-cli sch erc --severity-all --format json -o design/interfaces/validation/rear_erc.json rear_sensor/rear_sensor_revA.kicad_sch
kicad-cli sch export netlist --format kicadxml -o design/interfaces/validation/main_netlist.xml sportwatch_revA.kicad_sch
kicad-cli sch export netlist --format kicadxml -o design/interfaces/validation/rear_netlist.xml rear_sensor/rear_sensor_revA.kicad_sch
python3 design/interfaces/verify_assembled.py design/interfaces/validation/main_netlist.xml design/interfaces/validation/rear_netlist.xml design/interfaces/validation/assembled_audit.json
akcli check sportwatch_revA.kicad_sch --integrity --fail-on never --json
akcli check rear_sensor/rear_sensor_revA.kicad_sch --integrity --fail-on never --json
```

The session's Flatpak launcher could not allocate an instance. Validation used the pre-existing `/tmp/sportwatch-review-r3/native` native runtime launcher. It emits a missing API-schema-path diagnostic; MAIN netlist export also emits the inherited annotation warning. Commands nevertheless exit 0 with valid native outputs. These runtime messages are not concealed or counted as ERC findings.

## Results and warning disposition

MAIN native ERC: **0 errors, 991 warnings**: 962 endpoint-off-grid, 14 same-local/global-label, 7 isolated-pin-label, 3 pin-to-pin, 2 label-multiple-wires, 2 library-symbol-mismatch and 1 unconnected-wire-endpoint. REAR: **0 errors, 225 warnings**: 223 endpoint-off-grid and 2 pin-to-pin. Source baseline: 0 errors / 1172 warnings. These are raw counts; no new ERC exclusions or waiver changes were added.

Off-grid warnings reflect inherited/imported geometry and the new schematic-only symbol/stub organization; they remain schematic cleanup work, not proof of physical pin disconnection. Same-local/global-label warnings arise from intentionally exporting existing root nets via global labels on the interface leaves; the full joined native-node audit proves their membership. Native pin-to-pin warnings describe baseline strapped bidirectional pins and photodiode/current-input relationships; all source pin partitions are preserved. The remaining tiny root wire endpoint and isolated labels/library mismatches are inherited from the approved source. Native rendering was inspected for the modified sheets. This is not a zero-warning claim.

Both akcli integrity reports have **zero findings**. Its reported component counts include power symbols/flags and are not authoritative physical BOM counts. MAIN metadata includes 72 inherited No-ERC points; REAR 3. No new No-ERC suppression is added. Native netlists and the full source-membership join provide electrical evidence beyond ERC's limitations.

`assembled_audit.json` proves 24-position continuity on the 13 allowed logical nets; all original functional component pin partitions, references, values and footprints remain intact except the deliberate J202 protection ECO. Detector membership, every LED/mux/VREF/PD_GND net, unused cathodes, U6 GPIOs, main ENV pull-ups and battery polarity are checked. `uuid_audit.json` records zero duplicate object UUIDs across actual project schematics and preserved pin UUID maps for the 242 unchanged physical source components. Cached library definitions are not schematic instances.

49 original PCB/project/rule/library/footprint-table files are byte-identical to the approved checkpoint. No PCB transfer, refill, routing, placement, new PCB outline or physical stackup has been performed. MAIN's existing PCB is intentionally out of population parity with the new schematic until the later authorized transfer phase.

## Design provisions and execution records

The `.ops.json` files record the akcli validate → plan/render → dry-run → apply sequence for new interface/protection parts. They are authoring records for the added blocks, not a complete replay of the UUID-preserving transfer or later schematic presentation adjustments. The saved KiCad schematics and contracts are authoritative. In particular C1501's native DNP status is checked by the audit and must remain DNP until its sizing gate closes.

Protection MPNs/footprints, reservoir sizing, source-damping insertion/values, physical mating permutation, battery/contact hardware and rear outline/stackup remain explicit later gates. The abstract U1201 provision represents required OV/reverse/current protection functions, not a selected package or validated device. A separate harness-local ESD entry provision is mandatory. Phase 1 readiness means ready for independent electrical review; it does not authorize fabrication or charging an unqualified physical assembly.


## Correction Round 1 metadata finalization

The new charging and REAR-root saved instances must use their owning project and actual hierarchy path. The two corresponding authoring op-lists carry explicit `instance_designators` and the corrected PMIC-side qualification. After any replay of `charging.ops.json` or `rear_interface.ops.json`, the mandatory finalization/check is:

```sh
python3 design/interfaces/correct_round1_metadata.py --apply
python3 design/interfaces/correct_round1_metadata.py
```

The tool changes only J202/U1201/D1201/#FLG1201 on MAIN and J1502/C1501/#FLG1501–#FLG1503 on REAR, plus D1201's qualification field. It preserves UUIDs, pins, references, values, wiring and all inherited instance metadata. A replay is incomplete until this saved-record check and the native/assembled gates above pass. The op-lists remain block authoring records, not a complete replay of prior transfer/presentation/native DNP work.

PMIC VBUS recommended normal operation is 4.0–5.5 V; absolute stress limits are −0.3..22 V. Negative transient/reverse protection must keep VBUS at or above −0.3 V with design margin; sustained reverse voltage requires series blocking. Final devices/clamps require the qualified dock/fault envelope. No selected part or guaranteed protection level is implied.
