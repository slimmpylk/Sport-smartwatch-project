"""Read-only audit: run with Python that provides akcli, after native XML export.

Usage: python verify_display.py path/to/display-netlist.xml
Checks the delivered file, not the authoring op-list.
"""
from collections import Counter
from pathlib import Path
import json
import math
import sys
import xml.etree.ElementTree as ET
from akcli.sexpr import parse

project = Path(__file__).resolve().parents[2]
sch = parse((project / "03_DISPLAY.kicad_sch").read_text())
lib = parse((project / "libraries/symbols/sportwatch_display.kicad_sym").read_text())
fp = parse((project / "libraries/footprints/sportwatch_custom.pretty/OK-23GF024-04.kicad_mod").read_text())
assert sch.tag == "kicad_sch" and lib.tag == "kicad_symbol_lib" and fp.tag == "footprint"
expected = {
    1: "DISP_RST", 2: "GND", 3: "DISP_TE", 4: "DISP_QSPI_CS",
    5: "DISP_QSPI_CLK", 6: "DISP_QSPI_IO1", 7: "DISP_QSPI_IO0",
    8: "GND", 9: None, 10: None, 11: "VSYS", 12: "VSYS", 13: "GND",
    14: "GND", 15: "SYS_3V3", 16: "SYS_3V3", 17: "TOUCH_INT",
    18: "TOUCH_RST", 19: "TOUCH_SDA", 20: "TOUCH_SCL", 21: "GND",
    22: "DISP_QSPI_IO3", 23: "DISP_QSPI_IO2", 24: "DISP_VCI_EN",
}
names = {
    1: "LCD_RST", 2: "GND", 3: "TE", 4: "SPI_CS", 5: "SPI_CLK",
    6: "SPI_I01", 7: "SPI_SI00", 8: "GND", 9: "IM1/NC",
    10: "MTP/NC", 11: "VBAT", 12: "VBAT", 13: "GND", 14: "GND",
    15: "VDD", 16: "TP_VDD", 17: "TP_INT", 18: "TP_RST",
    19: "TP_SDA", 20: "TP_SCL", 21: "GND", 22: "SPI_SI03",
    23: "SPI_SI02", 24: "VCI_EN",
}
def xy(node):
    return tuple(round(float(node[i].value), 6) for i in (1, 2))

def props(node):
    return {p[1].value: p[2].value for p in node.find_all("property")}

embedded = {s[1].value: s for s in sch.find("lib_symbols").find_all("symbol")}
pins = {}
dnps = set()
for instance in sch.find_all("symbol"):
    properties = props(instance)
    ref = properties["Reference"]
    if instance.find("dnp") is not None and instance.find("dnp")[1].value == "yes":
        dnps.add(ref)
    origin = xy(instance.find("at"))
    assert float(instance.find("at")[3].value) == 0, "Audit supports this sheet's zero-degree placements"
    definition = embedded[instance.find("lib_id")[1].value]
    for unit in definition.find_all("symbol"):
        for pin in unit.find_all("pin"):
            point = xy(pin.find("at"))
            number = pin.find("number")[1].value
            pins[ref + "." + number] = (
                round(origin[0] + point[0], 6), round(origin[1] - point[1], 6)
            )
            if ref == "J1":
                assert pin.find("name")[1].value == names[int(number)]
    if ref == "J1":
        assert properties["Value"] == "ZC-A1D43W-046"
        assert properties["Footprint"] == "sportwatch_custom:OK-23GF024-04"
assert dnps == {"R301", "R302", "R306"}
assert len([p for p in pins if p.startswith("J1.")]) == 24
nc = {xy(n.find("at")) for n in sch.find_all("no_connect")}
assert nc == {pins["J1.9"], pins["J1.10"]}, "Accidental or missing NC"
ends = Counter()
for wire in sch.find_all("wire"):
    points = [xy(p) for p in wire.find("pts").find_all("xy")]
    assert len(points) == 2 and points[0] != points[1]
    assert points[0][0] == points[1][0] or points[0][1] == points[1][1]
    ends.update(points)
labels = {xy(n.find("at")) for kind in ("label", "global_label", "hierarchical_label")
          for n in sch.find_all(kind)}
assert labels <= (set(ends) | set(pins.values())), "Floating label"
assert not (nc & set(ends)), "Wire on NC pin"
for point, degree in ends.items():
    assert degree >= 2 or point in labels or point in pins.values(), ("Dangling wire", point)
for key, point in pins.items():
    if point not in nc:
        assert point in ends or point in labels, ("Unattached pin", key, point)
native = ET.parse(sys.argv[1]).getroot()
actual = {}
members = {}
for net in native.findall("./nets/net"):
    members[net.attrib["name"]] = {(n.attrib["ref"], n.attrib["pin"]) for n in net.findall("node")}
    for node in net.findall("node"):
        if node.attrib["ref"] == "J1":
            actual[int(node.attrib["pin"])] = net.attrib["name"]
for number, wanted in expected.items():
    got = actual.get(number)
    if wanted is None:
        assert got is None or got.startswith("unconnected-"), (number, got)
    else:
        assert got == wanted, (number, wanted, got)
expected_passives = {
    "R301": ("SYS_3V3", "TOUCH_SDA"), "R302": ("SYS_3V3", "TOUCH_SCL"),
    "R303": ("DISP_RST", "GND"), "R304": ("TOUCH_RST", "GND"),
    "R305": ("SYS_3V3", "DISP_QSPI_CS"), "R306": ("DISP_VCI_EN", "GND"),
}
for ref, pair in expected_passives.items():
    for number, net in enumerate(pair, 1):
        assert (ref, str(number)) in members[net], (ref, number, net)
pad_nodes = fp.find_all("pad")
numbered = {int(p[1].value): p for p in pad_nodes if p[1].value}
assert sorted(numbered) == list(range(1, 25))
assert len(pad_nodes) == 28
for number, pad in numbered.items():
    i = number - 1 if number <= 12 else 24 - number
    x, y = xy(pad.find("at"))
    assert math.isclose(x, -2.2 + i * .4, abs_tol=1e-6)
    assert y == (1.2 if number <= 12 else -1.2)
    assert xy(pad.find("size")) == (.23, .5)
for pad in pad_nodes:
    if not pad[1].value:
        assert tuple(abs(v) for v in xy(pad.find("at"))) == (3.03, 1.0575)
        assert xy(pad.find("size")) == (.6, .785)
        assert math.isclose(float(pad.find("chamfer_ratio")[1].value) * .6, .2, abs_tol=1e-6)
assert len(fp.find_all("zone")) == 2, "Manufacturer insulation regions"
symbol_numbers = {int(p.find("number")[1].value)
                  for unit in lib.find("symbol").find_all("symbol") for p in unit.find_all("pin")}
assert symbol_numbers == set(numbered)
print("PASS: schematic, library and footprint S-expressions parsed.")
print("PASS: native KiCad XML agrees with all 24 module pins and all passive endpoints.")
print("PASS: every pin/label/wire attached exactly; only J1.9/J1.10 are NC.")
print("PASS: DNP flags R301/R302/R306; footprint pads 1..24 plus four unnumbered hold-downs.")
print("PASS: 0.40mm pitch, 0.23x0.50mm lands, hold-down dimensions/chamfers and symbol-pad numbers.")
print("\n| Pin | Module function | Net |\n|---|---|---|")
for number in range(1, 25):
    print(f"| {number} | {names[number]} | {expected[number] or 'NC'} |")
