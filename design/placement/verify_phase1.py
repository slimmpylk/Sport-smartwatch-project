#!/usr/bin/env python3
"""Read-only Phase 1 ownership, geometry, and proof audit. Pure Python (zero pcbnew dependency).

Usage: verify_phase1.py MAIN.xml REAR.xml OUTPUT.json [MAIN.kicad_pcb] [REAR.kicad_pcb]
The baseline PCB is obtained directly from the recorded starting Git object (blob 8faaf975774a9927a66488915eb2371c7bf808c3).
This checks implementation geometry and native XML, not routing completion.
"""
import hashlib
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = '37eb4100f946378fbf0998dafba9bd6da3e8737e'
BASELINE_PCB_BLOB = '8faaf975774a9927a66488915eb2371c7bf808c3'

class PhysicalInvariantError(Exception):
    def __init__(self, failure_code: str, message: str, details: dict = None):
        super().__init__(message)
        self.failure_code = failure_code
        self.details = details or {}


class PadInvariantError(PhysicalInvariantError):
    pass


class FoundationInvariantError(PhysicalInvariantError):
    pass


class ProofTrackInvariantError(PhysicalInvariantError):
    pass


class ProofViaInvariantError(PhysicalInvariantError):
    pass


class RoutingInvariantError(PhysicalInvariantError):
    pass


class OwnershipInvariantError(PhysicalInvariantError):
    pass


class MetadataInvariantError(PhysicalInvariantError):
    pass


class EnvelopeInvariantError(PhysicalInvariantError):
    pass


EXPECTED_FIXED_REFS = {
    "C101", "C102", "C103", "C104", "C105", "C106", "C107", "C108", "C109", "C110",
    "C111", "C112", "C113", "C114", "C115", "C116", "C117", "C118", "C119",
    "C1420", "C1421", "C201", "C202", "C203", "C204", "C205", "C207", "C208",
    "C213", "C214", "C215", "C401", "C402", "C601", "C602", "C603", "C604", "C605",
    "C606", "C607", "C608", "C609", "C610", "C611", "C612", "C613", "C614", "C615",
    "C616", "C617", "C618", "C619", "L101", "L201", "L202", "L203", "L401", "L601",
    "NT201", "NT202", "R111", "R1420", "R406", "R407", "U101", "U11", "U201",
    "U202", "U401", "U8", "U9", "U901", "Y1", "Y101", "Y102"
}

EXPECTED_PROOF_TRACK_UUIDS = {
    "0252bed5-9857-4915-a91a-cd3fc09d9355",  # /EMMC_CMD on In2.Cu
    "140b6ad0-7ae7-4373-8b17-a889cd066fb6",  # /EMMC_DAT4 on In2.Cu
    "1ec559ae-f4dd-4f3e-a2bb-85e949bac78b",  # /EMMC_DAT6 on In2.Cu
    "2c49d30c-7659-4d7f-9b06-29676b445d58",  # /EMMC_DAT5 on In2.Cu
    "547a2b28-ba3d-4aa4-8f1c-2cac70d86ae6",  # /01_APOLLO510B/MCU_EMMC_CLK on In2.Cu
    "568d3d22-dc04-4b69-854b-6b7878f80fd9",  # /EMMC_CLK on In2.Cu
    "5ad4042f-198e-4d1c-9592-9b932b988c7c",  # /EMMC_CLK on In2.Cu
    "6ca4c071-b33c-45ce-9835-24ccc8e03ed5",  # /EMMC_DAT4 on In2.Cu
    "73a5722d-7266-42fd-bda8-d072548af3b2",  # /EMMC_CMD on In2.Cu
    "7f508a8c-1f4a-4af8-8958-238ecf4e25a3",  # /EMMC_CLK on In2.Cu
    "c327118c-6dca-46e1-a247-d35ee3b8a374",  # /EMMC_CMD on In2.Cu
    "c9fd4ad1-606c-4f21-afb9-d4b34b1e594e",  # /EMMC_DAT6 on In2.Cu
    "fa685596-2bbd-4f25-bd65-fd627ca2ec8d",  # /EMMC_CLK on In2.Cu
    "fa9d9d43-f71c-42c8-99ee-34cf8b323c76",  # /EMMC_DAT5 on In2.Cu
}

EXPECTED_PROOF_VIA_UUIDS = {
    "0b6ddf3d-cba6-4888-a3fc-baa5610e99e2",  # /EMMC_CMD 0->4
    "2232eefb-582a-49b6-98b5-d757d9842b42",  # /EMMC_CLK 0->4
    "241e1e91-92a9-4d8c-8df1-b837537ee351",  # /EMMC_DAT4 4->6
    "472ebc88-1fd4-45fc-9108-29fc2fd2cc0e",  # /EMMC_CMD 4->6
    "506fd597-25b3-4564-8a28-bb928d6017a7",  # /01_APOLLO510B/MCU_EMMC_CLK 0->4
    "6805f880-6202-47c3-8f37-120d7c7a3d75",  # /EMMC_CLK 4->6
    "7439ef6a-d855-4257-b273-1d6047bc6510",  # /01_APOLLO510B/MCU_EMMC_CLK 4->6
    "757d8ca9-9921-4898-b580-e7abde1dcaa4",  # /EMMC_DAT5 4->6
    "7bbeebd5-68b0-4297-a750-f9bffce29fcf",  # /EMMC_DAT4 0->4
    "8b4163e7-a542-4f75-af98-097bc22ee60d",  # /01_APOLLO510B/MCU_EMMC_CLK 0->4
    "8bd84013-2679-4457-bac3-5fcd9d3fe0d6",  # /EMMC_CMD 0->4
    "8e63ba05-7806-4e15-9a0d-9becc1b9bcd4",  # /EMMC_CLK 0->4
    "9d9a7671-f06e-4e80-8863-dac672f00d9d",  # /EMMC_DAT6 4->6
    "9f8fba43-153b-43fb-9f3c-6399daa20690",  # /EMMC_DAT6 4->6
    "a7c507c2-dfb5-4f24-9823-7e1edd5c6cf9",  # /EMMC_DAT6 0->4
    "b4c5b037-329f-468c-bde0-9212b0b00c0b",  # /EMMC_CMD 4->6
    "b5abe823-6312-4b10-a191-cb844f84f1ac",  # /EMMC_DAT4 4->6
    "b6cd76ca-812c-4957-bf71-deb1a1b0b968",  # /EMMC_DAT4 0->4
    "c6dbf33d-c1d4-4331-aae5-544e5a7a6fb0",  # /EMMC_CLK 4->6
    "d93f2901-e0d5-4702-bcf1-487d8a415340",  # /01_APOLLO510B/MCU_EMMC_CLK 4->6
    "e2345dc2-7016-4d9b-a679-70bfca4277da",  # /EMMC_DAT5 4->6
    "e93173cc-5050-4c8b-baba-9ce8eef4ee35",  # /EMMC_DAT6 0->4
    "ec436650-a838-4706-adbd-04a5da42f981",  # /EMMC_DAT5 0->4
    "ec9d1bb8-1381-4e4e-afc7-c373dd251711",  # /EMMC_DAT5 0->4
}

ENCLOSED_BY_SHIELD = {
    "U101", "Y101", "R101", "R105", "R106", "R111",
    "C111", "C112", "C113", "C114", "C115", "C116", "C117", "C118", "C119"
}

_TOKEN_RE = re.compile(r"""\s*(?:([()])|"((?:[^"\\]|\\.)*)"|([^\s()]+))""")


def parse_sexp(text):
    tokens = []
    for match in _TOKEN_RE.finditer(text):
        lp, qs, uq = match.groups()
        if lp:
            tokens.append(lp)
        elif qs is not None:
            tokens.append(qs.replace('\\"', '"').replace('\\\\', '\\'))
        elif uq is not None:
            tokens.append(uq)
    stack = [[]]
    for tok in tokens:
        if tok == '(':
            new_list = []
            stack[-1].append(new_list)
            stack.append(new_list)
        elif tok == ')':
            if len(stack) > 1:
                stack.pop()
        else:
            stack[-1].append(tok)
    return stack[0][0] if stack[0] else []


def find_git_root(path):
    cur = path.resolve()
    while cur != cur.parent:
        if (cur / '.git').exists():
            return cur
        cur = cur.parent
    return path


def load_xml(path):
    root = ET.parse(path).getroot()
    cs = {c.get('ref'): c for c in root.findall('components/comp')}
    if len(cs) != len(root.findall('components/comp')):
        raise MetadataInvariantError('XML_PARSE_MISMATCH',
                                     f"Parsed component count {len(cs)} does not match XML elements {len(root.findall('components/comp'))}")
    ns = {n.get('name'): {(x.get('ref'), x.get('pin')) for x in n.findall('node')}
          for n in root.findall('nets/net')}
    return cs, ns, {pin: net for net, pins in ns.items() for pin in pins}


def extract_pad_signature(pad_ast, net_table=None):
    number = pad_ast[1]
    pad_type = pad_ast[2]
    shape = pad_ast[3]
    local_pos = [0.0, 0.0]
    local_rot = 0.0
    size = [0.0, 0.0]
    layers = []
    roundrect_rratio = None
    chamfer_ratio = None
    chamfer_corners = ()
    drill_shape = None
    drill_size = None
    drill_offset = [0.0, 0.0]
    rect_delta = None
    zone_connect = None
    thermal_bridge_angle = None
    remove_unused_layers = None
    clearance = None
    solder_mask_margin = None
    solder_paste_margin = None
    uuid_val = None
    net_name = None

    for sub in pad_ast[4:]:
        if not isinstance(sub, list) or not sub:
            continue
        tag = sub[0]
        if tag == 'at':
            local_pos = [round(float(sub[1]), 6), round(float(sub[2]), 6)]
            if len(sub) > 3:
                local_rot = round(float(sub[3]) % 360.0, 4)
        elif tag == 'size':
            size = [round(float(sub[1]), 6), round(float(sub[2]), 6)]
        elif tag == 'layers':
            layers = sorted(str(x) for x in sub[1:])
        elif tag == 'roundrect_rratio':
            roundrect_rratio = round(float(sub[1]), 6)
        elif tag == 'chamfer_ratio':
            chamfer_ratio = round(float(sub[1]), 6)
        elif tag == 'chamfer':
            chamfer_corners = tuple(sorted(str(x) for x in sub[1:]))
        elif tag == 'drill':
            drill_offset = [0.0, 0.0]
            idx_sub = 1
            if idx_sub < len(sub) and sub[idx_sub] == 'oval':
                drill_shape = 'oval'
                idx_sub += 1
                if idx_sub + 1 < len(sub) and not isinstance(sub[idx_sub], list) and not isinstance(sub[idx_sub+1], list):
                    drill_size = [round(float(sub[idx_sub]), 6), round(float(sub[idx_sub+1]), 6)]
                    idx_sub += 2
            elif idx_sub < len(sub) and not isinstance(sub[idx_sub], list):
                drill_shape = 'circle'
                d = round(float(sub[idx_sub]), 6)
                drill_size = [d, d]
                idx_sub += 1
            while idx_sub < len(sub):
                dsub = sub[idx_sub]
                if isinstance(dsub, list) and dsub:
                    if dsub[0] == 'offset' and len(dsub) >= 3:
                        drill_offset = [round(float(dsub[1]), 6), round(float(dsub[2]), 6)]
                idx_sub += 1
        elif tag == 'rect_delta':
            rect_delta = [round(float(sub[1]), 6), round(float(sub[2]), 6)]
        elif tag == 'zone_connect':
            zone_connect = sub[1]
        elif tag == 'thermal_bridge_angle':
            thermal_bridge_angle = round(float(sub[1]), 4)
        elif tag == 'remove_unused_layers':
            remove_unused_layers = str(sub[1])
        elif tag == 'clearance':
            clearance = round(float(sub[1]), 6)
        elif tag == 'solder_mask_margin':
            solder_mask_margin = round(float(sub[1]), 6)
        elif tag == 'solder_paste_margin':
            solder_paste_margin = round(float(sub[1]), 6)
        elif tag in ('uuid', 'tstamp'):
            uuid_val = str(sub[1])
        elif tag == 'net':
            if len(sub) >= 3:
                net_name = str(sub[2])
            elif len(sub) == 2:
                v = str(sub[1])
                net_name = net_table.get(v, v) if net_table else v

    return {
        'uuid': uuid_val,
        'number': number,
        'pad_type': pad_type,
        'shape': shape,
        'local_pos': local_pos,
        'local_rot': local_rot,
        'size': size,
        'layers': tuple(layers),
        'roundrect_rratio': roundrect_rratio,
        'chamfer_ratio': chamfer_ratio,
        'chamfer_corners': chamfer_corners,
        'drill_shape': drill_shape,
        'drill_size': drill_size,
        'drill_offset': drill_offset,
        'rect_delta': rect_delta,
        'zone_connect': zone_connect,
        'thermal_bridge_angle': thermal_bridge_angle,
        'remove_unused_layers': remove_unused_layers,
        'clearance': clearance,
        'solder_mask_margin': solder_mask_margin,
        'solder_paste_margin': solder_paste_margin,
        'net_name': net_name
    }


def compute_footprint_bbox(item):
    fp_pos = [0.0, 0.0]
    fp_rot = 0.0
    for s in item:
        if isinstance(s, list) and s and s[0] == 'at':
            fp_pos = [float(s[1]), float(s[2])]
            if len(s) > 3:
                fp_rot = float(s[3])
            break

    rad = math.radians(fp_rot)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    xs, ys = [], []
    has_crtyd = False

    for s in item:
        if isinstance(s, list) and s and s[0] == 'fp_line':
            is_cr = any(isinstance(e, list) and e and e[0] == 'layer' and 'CrtYd' in e[1] for e in s)
            if is_cr:
                has_crtyd = True
                p1, p2 = None, None
                for e in s:
                    if isinstance(e, list) and e:
                        if e[0] == 'start':
                            p1 = (float(e[1]), float(e[2]))
                        elif e[0] == 'end':
                            p2 = (float(e[1]), float(e[2]))
                for p in [p1, p2]:
                    if p:
                        wx = fp_pos[0] + p[0] * cos_r - p[1] * sin_r
                        wy = fp_pos[1] + p[0] * sin_r + p[1] * cos_r
                        xs.append(wx)
                        ys.append(wy)
        elif isinstance(s, list) and s and s[0] == 'fp_rect':
            is_cr = any(isinstance(e, list) and e and e[0] == 'layer' and 'CrtYd' in e[1] for e in s)
            if is_cr:
                has_crtyd = True
                p1, p2 = None, None
                for e in s:
                    if isinstance(e, list) and e:
                        if e[0] == 'start':
                            p1 = (float(e[1]), float(e[2]))
                        elif e[0] == 'end':
                            p2 = (float(e[1]), float(e[2]))
                if p1 and p2:
                    for px in [p1[0], p2[0]]:
                        for py in [p1[1], p2[1]]:
                            wx = fp_pos[0] + px * cos_r - py * sin_r
                            wy = fp_pos[1] + px * sin_r + py * cos_r
                            xs.append(wx)
                            ys.append(wy)

    if not has_crtyd:
        for s in item:
            if isinstance(s, list) and s and s[0] == 'pad':
                p_at, p_size, p_rot = [0.0, 0.0], [0.0, 0.0], 0.0
                for e in s[4:]:
                    if isinstance(e, list) and e:
                        if e[0] == 'at':
                            p_at = [float(e[1]), float(e[2])]
                            if len(e) > 3:
                                p_rot = float(e[3])
                        elif e[0] == 'size':
                            p_size = [float(e[1]), float(e[2])]
                total_rot = fp_rot + p_rot
                t_rad = math.radians(total_rot)
                t_cos, t_sin = math.cos(t_rad), math.sin(t_rad)
                p_wx = fp_pos[0] + p_at[0] * cos_r - p_at[1] * sin_r
                p_wy = fp_pos[1] + p_at[0] * sin_r + p_at[1] * cos_r
                hw, hh = p_size[0] / 2.0, p_size[1] / 2.0
                for dx, dy in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
                    cx = p_wx + dx * t_cos - dy * t_sin
                    cy = p_wy + dx * t_sin + dy * t_cos
                    xs.append(cx)
                    ys.append(cy)

    if not xs:
        return [fp_pos[0], fp_pos[1], fp_pos[0], fp_pos[1]]
    return [round(min(xs), 6), round(min(ys), 6), round(max(xs), 6), round(max(ys), 6)]


def parse_board_data(ast):
    net_table = {}
    for item in ast[1:]:
        if isinstance(item, list) and item and item[0] == 'net':
            if len(item) >= 3:
                net_table[str(item[1])] = str(item[2])

    def resolve_net(sub):
        if len(sub) >= 3:
            return str(sub[2])
        if len(sub) == 2:
            val = str(sub[1])
            return net_table.get(val, val)
        return None

    footprints = {}
    tracks = {}
    arcs = {}
    vias = {}
    drawings = {
        'edge_cuts_circles': [],
        'edge_cuts_others': [],
        'user3_polys': [],
        'user2_rects': [],
        'user2_texts': []
    }
    zones = []

    for item in ast[1:]:
        if not isinstance(item, list) or not item:
            continue
        tag = item[0]

        if tag == 'footprint':
            ref = None
            val = None
            uuid_val = None
            fpid_lib = ''
            fpid_name = ''
            fp_pos = [0.0, 0.0]
            fp_rot = 0.0
            layer = 'F.Cu'
            properties = {}
            sheetpath = ''

            for s in item:
                if not isinstance(s, list) or not s:
                    continue
                stag = s[0]
                if stag == 'layer':
                    layer = str(s[1])
                elif stag == 'at':
                    fp_pos = [round(float(s[1]), 6), round(float(s[2]), 6)]
                    if len(s) > 3:
                        fp_rot = round(float(s[3]) % 360.0, 4)
                elif stag in ('uuid', 'tstamp'):
                    uuid_val = str(s[1])
                elif stag == 'property' and len(s) >= 3:
                    properties[s[1]] = s[2]
                    if s[1] == 'Reference':
                        ref = s[2]
                    elif s[1] == 'Value':
                        val = s[2]
                elif stag == 'fp_text' and len(s) >= 3:
                    if s[1] == 'reference':
                        ref = s[2]
                    elif s[1] == 'value':
                        val = s[2]
                elif stag == 'path':
                    sheetpath = str(s[1])
                elif stag == 'sheetpath':
                    tst = ''
                    for e in s:
                        if isinstance(e, list) and e and e[0] == 'tstamps':
                            tst = str(e[1])
                    sheetpath = tst

            # FPID from second token of footprint
            if len(item) > 1 and isinstance(item[1], str) and ':' in item[1]:
                parts = item[1].split(':', 1)
                fpid_lib, fpid_name = parts[0], parts[1]

            pads = {}
            for s in item:
                if isinstance(s, list) and s and s[0] == 'pad':
                    sig = extract_pad_signature(s, net_table)
                    pads[sig['uuid']] = sig

            bbox = compute_footprint_bbox(item)

            if ref:
                footprints[ref] = {
                    'ref': ref,
                    'value': val,
                    'uuid': uuid_val,
                    'fpid': (fpid_lib, fpid_name),
                    'pos': fp_pos,
                    'rot': fp_rot,
                    'layer': layer,
                    'properties': properties,
                    'sheetpath': sheetpath,
                    'pads': pads,
                    'bbox': bbox,
                    'ast': item
                }

        elif tag == 'segment':
            uuid_val, start, end, width, layer, net_name = None, None, None, None, None, None
            for s in item[1:]:
                if isinstance(s, list) and s:
                    if s[0] in ('uuid', 'tstamp'):
                        uuid_val = str(s[1])
                    elif s[0] == 'start':
                        start = [round(float(s[1]), 6), round(float(s[2]), 6)]
                    elif s[0] == 'end':
                        end = [round(float(s[1]), 6), round(float(s[2]), 6)]
                    elif s[0] == 'width':
                        width = round(float(s[1]), 6)
                    elif s[0] == 'layer':
                        layer = str(s[1])
                    elif s[0] == 'net':
                        net_name = resolve_net(s)
            tracks[uuid_val] = {
                'uuid': uuid_val, 'start': start, 'end': end,
                'width': width, 'layer': layer, 'net': net_name
            }

        elif tag == 'arc':
            uuid_val, start, mid, end, width, layer, net_name = None, None, None, None, None, None, None
            for s in item[1:]:
                if isinstance(s, list) and s:
                    if s[0] in ('uuid', 'tstamp'):
                        uuid_val = str(s[1])
                    elif s[0] == 'start':
                        start = [round(float(s[1]), 6), round(float(s[2]), 6)]
                    elif s[0] == 'mid':
                        mid = [round(float(s[1]), 6), round(float(s[2]), 6)]
                    elif s[0] == 'end':
                        end = [round(float(s[1]), 6), round(float(s[2]), 6)]
                    elif s[0] == 'width':
                        width = round(float(s[1]), 6)
                    elif s[0] == 'layer':
                        layer = str(s[1])
                    elif s[0] == 'net':
                        net_name = resolve_net(s)
            arc_key = uuid_val or f"arc_{len(arcs)}"
            arcs[arc_key] = {
                'uuid': uuid_val, 'start': start, 'mid': mid, 'end': end,
                'width': width, 'layer': layer, 'net': net_name
            }

        elif tag == 'via':
            via_type = 'default'
            uuid_val, pos, size, drill, layers, net_name = None, None, None, None, None, None
            for elem in item[1:]:
                if isinstance(elem, str) and elem in ('micro', 'microvia', 'blind'):
                    via_type = elem
                elif isinstance(elem, list) and elem:
                    if elem[0] in ('uuid', 'tstamp'):
                        uuid_val = str(elem[1])
                    elif elem[0] == 'at':
                        pos = [round(float(elem[1]), 6), round(float(elem[2]), 6)]
                    elif elem[0] == 'size':
                        size = round(float(elem[1]), 6)
                    elif elem[0] == 'drill':
                        drill = round(float(elem[1]), 6)
                    elif elem[0] == 'layers':
                        layers = [str(elem[1]), str(elem[2])]
                    elif elem[0] == 'net':
                        net_name = resolve_net(elem)
            vias[uuid_val] = {
                'uuid': uuid_val, 'via_type': via_type, 'pos': pos,
                'size': size, 'drill': drill, 'layers': layers, 'net': net_name
            }

        elif tag == 'gr_circle':
            is_ec = any(isinstance(s, list) and s and s[0] == 'layer' and s[1] == 'Edge.Cuts' for s in item)
            if is_ec:
                c, r, w = [0.0, 0.0], 0.0, 0.1
                for s in item:
                    if isinstance(s, list) and s:
                        if s[0] == 'center':
                            c = [round(float(s[1]), 6), round(float(s[2]), 6)]
                        elif s[0] == 'end':
                            ep = [float(s[1]), float(s[2])]
                            r = round(math.hypot(ep[0] - c[0], ep[1] - c[1]), 6)
                        elif s[0] == 'stroke':
                            for e in s:
                                if isinstance(e, list) and e and e[0] == 'width':
                                    w = round(float(e[1]), 6)
                drawings['edge_cuts_circles'].append({'center': c, 'radius': r, 'width': w})

        elif tag in ('gr_line', 'gr_arc', 'gr_poly', 'gr_rect'):
            is_ec = any(isinstance(s, list) and s and s[0] == 'layer' and s[1] == 'Edge.Cuts' for s in item)
            if is_ec:
                drawings['edge_cuts_others'].append(tag)

            is_u3 = any(isinstance(s, list) and s and s[0] == 'layer' and s[1] == 'User.3' for s in item)
            if is_u3 and tag == 'gr_poly':
                pts = []
                for s in item:
                    if isinstance(s, list) and s and s[0] == 'pts':
                        for pt in s[1:]:
                            if isinstance(pt, list) and pt and pt[0] == 'xy':
                                pts.append((round(float(pt[1]), 6), round(float(pt[2]), 6)))
                drawings['user3_polys'].append(pts)

            is_u2 = any(isinstance(s, list) and s and s[0] == 'layer' and s[1] == 'User.2' for s in item)
            if is_u2 and tag == 'gr_rect':
                st, en = [0.0, 0.0], [0.0, 0.0]
                for s in item:
                    if isinstance(s, list) and s:
                        if s[0] == 'start':
                            st = [float(s[1]), float(s[2])]
                        elif s[0] == 'end':
                            en = [float(s[1]), float(s[2])]
                drawings['user2_rects'].append([min(st[0], en[0]), min(st[1], en[1]),
                                                max(st[0], en[0]), max(st[1], en[1])])

        elif tag == 'gr_text':
            is_u2 = any(isinstance(s, list) and s and s[0] == 'layer' and s[1] == 'User.2' for s in item)
            if is_u2 and len(item) > 1 and isinstance(item[1], str):
                drawings['user2_texts'].append(item[1])

        elif tag == 'zone':
            net_name = None
            layer_set = []
            is_keepout = False
            for s in item[1:]:
                if isinstance(s, list) and s:
                    if s[0] == 'net':
                        net_name = resolve_net(s)
                    elif s[0] == 'net_name':
                        net_name = s[1]
                    elif s[0] == 'layer':
                        layer_set.append(s[1])
                    elif s[0] == 'layers':
                        layer_set.extend(s[1:])
                    elif s[0] == 'keepout':
                        is_keepout = True
            zones.append({
                'is_keepout': is_keepout,
                'net_name': net_name,
                'layers': layer_set
            })

    return {
        'net_table': net_table,
        'footprints': footprints,
        'tracks': tracks,
        'arcs': arcs,
        'vias': vias,
        'drawings': drawings,
        'zones': zones
    }


def cross_2d(ox, oy, ax, ay, bx, by):
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)


def on_segment(px, py, ax, ay, bx, by, eps=1e-5):
    return (min(ax, bx) - eps <= px <= max(ax, bx) + eps and
            min(ay, by) - eps <= py <= max(ay, by) + eps and
            abs(cross_2d(ax, ay, bx, by, px, py)) <= eps)


def segments_intersect(p1, p2, q1, q2, eps=1e-5):
    d1 = cross_2d(p1[0], p1[1], p2[0], p2[1], q1[0], q1[1])
    d2 = cross_2d(p1[0], p1[1], p2[0], p2[1], q2[0], q2[1])
    d3 = cross_2d(q1[0], q1[1], q2[0], q2[1], p1[0], p1[1])
    d4 = cross_2d(q1[0], q1[1], q2[0], q2[1], p2[0], p2[1])
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
       ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    if abs(d1) <= eps and on_segment(q1[0], q1[1], p1[0], p1[1], p2[0], p2[1], eps):
        return True
    if abs(d2) <= eps and on_segment(q2[0], q2[1], p1[0], p1[1], p2[0], p2[1], eps):
        return True
    if abs(d3) <= eps and on_segment(p1[0], p1[1], q1[0], q1[1], q2[0], q2[1], eps):
        return True
    if abs(d4) <= eps and on_segment(p2[0], p2[1], q1[0], q1[1], q2[0], q2[1], eps):
        return True
    return False


def point_in_polygon(px, py, pts, eps=1e-5):
    n = len(pts)
    inside = False
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        cp = (p2[0] - p1[0]) * (py - p1[1]) - (p2[1] - p1[1]) * (px - p1[0])
        if abs(cp) <= eps and min(p1[0], p2[0]) - eps <= px <= max(p1[0], p2[0]) + eps and min(p1[1], p2[1]) - eps <= py <= max(p1[1], p2[1]) + eps:
            return True
        if (p1[1] > py) != (p2[1] > py):
            x_inters = p1[0] + (py - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
            if px < x_inters:
                inside = not inside
    return inside


def polygon_area(pts):
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return abs(area) / 2.0


def audit(main_xml, rear_xml, main_pcb_path=None, rear_pcb_path=None):
    git_root = find_git_root(ROOT)

    # 1. Authoritative baseline check from Git
    rev_parse = subprocess.run(['git', 'rev-parse', '--verify', f'{START}^{{commit}}'],
                               cwd=git_root, capture_output=True, text=True)
    if rev_parse.returncode != 0:
        raise FoundationInvariantError('START_COMMIT_NOT_FOUND', f"START baseline commit {START} not found in Git repository", {'returncode': rev_parse.returncode})

    # Verify baseline blob ID
    blob_verify = subprocess.run(['git', 'cat-file', '-e', BASELINE_PCB_BLOB],
                                 cwd=git_root, capture_output=True, text=True)
    if blob_verify.returncode != 0:
        raise FoundationInvariantError('BASELINE_PCB_BLOB_NOT_FOUND', f"Baseline PCB blob {BASELINE_PCB_BLOB} not found in Git", {'returncode': blob_verify.returncode})

    baseline_pcb_bytes = subprocess.check_output(['git', 'cat-file', '-p', BASELINE_PCB_BLOB], cwd=git_root)
    # Confirm SHA-1 object ID matches
    actual_blob_sha1 = hashlib.sha1(f"blob {len(baseline_pcb_bytes)}\0".encode() + baseline_pcb_bytes).hexdigest()
    if actual_blob_sha1 != BASELINE_PCB_BLOB:
        raise FoundationInvariantError('BASELINE_BLOB_MISMATCH', f"Baseline blob mismatch: {actual_blob_sha1} vs {BASELINE_PCB_BLOB}", {'actual': actual_blob_sha1, 'expected': BASELINE_PCB_BLOB})

    # Parse baseline PCB
    baseline_ast = parse_sexp(baseline_pcb_bytes.decode('utf-8'))
    baseline_data = parse_board_data(baseline_ast)

    # 2. Parse live/scratch target PCBs
    main_target = Path(main_pcb_path or (ROOT / 'sportwatch_revA.kicad_pcb'))
    rear_target = Path(rear_pcb_path or (ROOT / 'rear_sensor/rear_sensor_revA.kicad_pcb'))

    if not main_target.is_file():
        raise FoundationInvariantError('MISSING_PCB_FILE', f"MAIN PCB file not found: {main_target}", {'file': str(main_target)})
    if not rear_target.is_file():
        raise FoundationInvariantError('MISSING_PCB_FILE', f"REAR PCB file not found: {rear_target}", {'file': str(rear_target)})

    main_ast = parse_sexp(main_target.read_text(encoding='utf-8'))
    rear_ast = parse_sexp(rear_target.read_text(encoding='utf-8'))

    main_data = parse_board_data(main_ast)
    rear_data = parse_board_data(rear_ast)

    # 3. Schematic XML audits
    mc, mn, mp = load_xml(main_xml)
    rc, rn, rp = load_xml(rear_xml)

    if len(mc) != 202 or len(mn) != 359:
        raise OwnershipInvariantError('XML_COMPONENT_COUNT_MISMATCH', f"MAIN XML component/net count mismatch: {len(mc)} / {len(mn)}", {'components': len(mc), 'nets': len(mn)})
    if len(rc) != 46 or len(rn) != 44:
        raise OwnershipInvariantError('XML_COMPONENT_COUNT_MISMATCH', f"REAR XML component/net count mismatch: {len(rc)} / {len(rn)}", {'components': len(rc), 'nets': len(rn)})

    contract = json.loads((ROOT / 'design/interfaces/main_rear_interface.json').read_text())
    if len(contract['positions']) != 24 or len({p['net'] for p in contract['positions']}) != 13:
        raise MetadataInvariantError('INTERFACE_CONTRACT_MISMATCH', f"Contract mismatch: {len(contract['positions'])} positions / {len({p['net'] for p in contract['positions']})} nets")

    parent = {('MAIN', n): ('MAIN', n) for n in mn} | {('REAR', n): ('REAR', n) for n in rn}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def join(a, b):
        parent[find(b)] = find(a)

    for row in contract['positions']:
        m = mp[('J1501', str(row['main_pin']))]
        r = rp[('J1502', str(row['rear_pin']))]
        join(('MAIN', m), ('REAR', r))

    source = json.loads((ROOT / 'design/interfaces/source_pin_membership.json').read_text())
    checkpoint = json.loads((ROOT / 'design/interfaces/source_checkpoint.json').read_text())
    transferred = {r for r, o in checkpoint['ownership'].items() if o == 'REAR'}
    if len(transferred) != 44:
        raise OwnershipInvariantError('TRANSFERRED_REF_COUNT_MISMATCH', f"Expected 44 transferred refs, got {len(transferred)}", {'transferred_count': len(transferred)})

    groups = {}
    for board, nets in [('MAIN', mn), ('REAR', rn)]:
        for net, pins in nets.items():
            root = find((board, net))
            groups.setdefault(root, set()).update(p for p in pins if p[0] in source and p[0] != 'J202')
    assembled = {frozenset(s) for s in groups.values() if s}

    original = {}
    for ref, ps in source.items():
        if ref == 'J202':
            continue
        for pin, net in ps.items():
            original.setdefault(net, set()).add((ref, pin))
    expected = {frozenset(s) for s in original.values() if s}
    if assembled != expected:
        raise OwnershipInvariantError('ASSEMBLED_GROUP_MISMATCH', f"Assembled groups mismatch: {len(assembled)} vs {len(expected)}", {'assembled': len(assembled), 'expected': len(expected)})

    # 4. Footprint ownership and parity
    mf = main_data['footprints']
    rf = rear_data['footprints']
    of = baseline_data['footprints']

    if len(mf) != 184:
        raise OwnershipInvariantError('DUP_OWNER_DETECTED' if len(mf) > 184 else 'MAIN_FP_COUNT_MISMATCH',
                                      f"Expected 184 placed footprints on MAIN, found {len(mf)}")
    if len(rf) != 44:
        raise OwnershipInvariantError('REAR_FP_MISSING',
                                      f"Expected 44 placed footprints on REAR, found {len(rf)}")
    expected_mf = {ref for ref, c in mc.items() if c.findtext('footprint')}
    if set(mf) != expected_mf:
        raise OwnershipInvariantError('MAIN_FOOTPRINT_SET_MISMATCH', "MAIN footprints do not match schematic comps with footprint", {'diff': list(set(mf) ^ expected_mf)})
    if set(rf) != transferred:
        raise OwnershipInvariantError('REAR_FOOTPRINT_SET_MISMATCH', f"REAR footprints do not match exact 44 transferred set: {set(rf) ^ transferred}", {'diff': list(set(rf) ^ transferred)})
    if set(mf) & set(rf):
        raise OwnershipInvariantError('DUP_OWNER_DETECTED',
                                      f"Duplicate footprint ownership detected across MAIN and REAR: {set(mf) & set(rf)}")

    # UUID collision check
    all_uuids = [f['uuid'] for f in mf.values()] + [f['uuid'] for f in rf.values()]
    for f in list(mf.values()) + list(rf.values()):
        all_uuids.extend(p['uuid'] for p in f['pads'].values() if p['uuid'])
    if len(all_uuids) != len(set(all_uuids)):
        raise OwnershipInvariantError('DUPLICATE_UUID', "Duplicate footprint or pad UUIDs across boards")

    # Board property & net connectivity against schematic
    for b_data, cs, pins, owner in [(main_data, mc, mp, 'MAIN'), (rear_data, rc, rp, 'REAR')]:
        for ref, f in b_data['footprints'].items():
            c = cs[ref]
            if f['value'] != c.findtext('value'):
                raise MetadataInvariantError('VALUE_MISMATCH', f"Value mismatch for {ref}: {f['value']} vs {c.findtext('value')}", {'ref': ref, 'actual': f['value'], 'expected': c.findtext('value')})
            expected_fpid = (c.findtext('footprint').split(':', 1)[0], c.findtext('footprint').split(':', 1)[1])
            if f['fpid'] != expected_fpid:
                raise MetadataInvariantError('FPID_MISMATCH', f"FPID mismatch for {ref}: {f['fpid']} vs {expected_fpid}", {'ref': ref, 'actual': f['fpid'], 'expected': expected_fpid})
            if f['properties'].get('Board') != owner:
                raise OwnershipInvariantError('BOARD_PROPERTY_MISMATCH', f"Board property mismatch for {ref}: {f['properties'].get('Board')} vs {owner}", {'ref': ref, 'actual': f['properties'].get('Board'), 'expected': owner})
            for pad_uid, pad in f['pads'].items():
                pad_num = pad['number']
                if not pad_num:
                    continue
                if (ref, pad_num) == ('U102', '25'):
                    if pad['net_name']:
                        raise PadInvariantError('UNMODELED_PAD_NET_ASSIGNED', "U102.25 unmodeled EP pad must not have net assigned", {'ref': ref, 'pad': pad_num, 'net': pad['net_name']})
                    continue
                expected_net = pins.get((ref, pad_num))
                actual_net = (pad['net_name'] or '').replace('{slash}', '/')
                if actual_net != expected_net:
                    raise PadInvariantError('PAD_NUM_MISMATCH' if expected_net is None else 'PAD_NET_MISMATCH',
                                            f"Net mismatch on {ref}.{pad_num}: actual='{actual_net}' vs expected='{expected_net}'",
                                            {'ref': ref, 'pad': pad_num, 'actual_net': actual_net, 'expected_net': expected_net})

    # 5. MAIN Edge.Cuts Circle Invariant
    circles = main_data['drawings']['edge_cuts_circles']
    others = main_data['drawings']['edge_cuts_others']
    orig_circles = baseline_data['drawings']['edge_cuts_circles']
    orig_others = baseline_data['drawings']['edge_cuts_others']

    if len(circles) != 1 or others:
        raise EnvelopeInvariantError('EDGE_CUTS_MISMATCH', f"MAIN Edge.Cuts must be exactly 1 circle, got {len(circles)} circles and {len(others)} other shapes", {'circles': len(circles), 'others': len(others)})
    if circles[0]['center'] != [100.0, 100.0]:
        raise EnvelopeInvariantError('EDGE_CUTS_MISMATCH', f"MAIN Edge.Cuts center altered: {circles[0]['center']}", {'actual': circles[0]['center'], 'expected': [100.0, 100.0]})
    if circles[0]['radius'] != 23.0:
        raise EnvelopeInvariantError('EDGE_CUTS_MISMATCH', f"MAIN Edge.Cuts radius altered: {circles[0]['radius']}", {'actual': circles[0]['radius'], 'expected': 23.0})
    if circles != orig_circles:
        raise EnvelopeInvariantError('EDGE_CUTS_MISMATCH', f"MAIN Edge.Cuts changed: {circles} vs baseline {orig_circles}", {'actual': circles, 'baseline': orig_circles})

    # 6. Plan metadata synchronization
    plan_path = Path.cwd() / 'design/placement/phase1_placement.json'
    if not plan_path.is_file():
        plan_path = ROOT / 'design/placement/phase1_placement.json'
    if not plan_path.is_file():
        plan_path = git_root / 'design/placement/phase1_placement.json'
    plan = json.loads(plan_path.read_text())
    plan_fixed = set(plan.get('fixed_main_refs', []))
    if len(plan_fixed) != 75:
        raise MetadataInvariantError('META_FIXED_MISMATCH', f"Expected 75 fixed refs in plan, got {len(plan_fixed)}",
                                     {'actual': len(plan_fixed), 'expected': 75})
    if plan_fixed != EXPECTED_FIXED_REFS:
        raise MetadataInvariantError('META_FIXED_MISMATCH', f"Plan fixed refs mismatch: {plan_fixed ^ EXPECTED_FIXED_REFS}")
    if plan.get('source_HEAD') != START:
        raise MetadataInvariantError('META_HEAD_MISMATCH', f"Plan source_HEAD mismatch: {plan.get('source_HEAD')} vs {START}",
                                     {'actual': plan.get('source_HEAD'), 'expected': START})
    if set(plan.get('transferred', [])) != transferred:
        raise MetadataInvariantError('META_TRANSFERRED_MISMATCH', "Plan transferred refs mismatch")
    if len(plan.get('removed_copper', [])) != 36:
        raise MetadataInvariantError('META_REMOVED_COPPER_MISMATCH', "Plan removed_copper count mismatch")

    # 7. 75 Foundation Footprints & Complete Pad Copper-Land Geometry
    verified_fixed_count = 0
    for ref in sorted(EXPECTED_FIXED_REFS):
        if ref not in of:
            raise FoundationInvariantError('FP_MISSING_BASELINE', f"Protected reference {ref} missing from baseline board", {'ref': ref})
        if ref not in mf:
            raise FoundationInvariantError('FP_MISSING_MAIN', f"Protected reference {ref} missing from main board", {'ref': ref})
        a = of[ref]
        b = mf[ref]

        if a['uuid'] != b['uuid']:
            raise FoundationInvariantError('FP_UUID_MISMATCH', f"Protected foundation footprint {ref} UUID mismatch", {'ref': ref, 'baseline': a['uuid'], 'actual': b['uuid']})
        if a['fpid'] != b['fpid']:
            raise FoundationInvariantError('FP_FPID_MISMATCH', f"Protected foundation footprint {ref} FPID altered: {b['fpid']} vs {a['fpid']}", {'ref': ref, 'baseline': a['fpid'], 'actual': b['fpid']})
        if a['pos'] != b['pos']:
            raise FoundationInvariantError('FP_POS_MISMATCH', f"Protected foundation footprint {ref} moved: {b['pos']} vs {a['pos']}", {'ref': ref, 'baseline': a['pos'], 'actual': b['pos']})
        if a['rot'] != b['rot']:
            raise FoundationInvariantError('FP_ROT_MISMATCH', f"Protected foundation footprint {ref} rotated: {b['rot']} vs {a['rot']}", {'ref': ref, 'baseline': a['rot'], 'actual': b['rot']})
        if a['layer'] != b['layer']:
            raise FoundationInvariantError('FP_LAYER_MISMATCH', f"Protected foundation footprint {ref} layer altered: {b['layer']} vs {a['layer']}", {'ref': ref, 'baseline': a['layer'], 'actual': b['layer']})

        a_pads = a['pads']
        b_pads = b['pads']

        if len(a_pads) != len(b_pads):
            raise PadInvariantError('PAD_COUNT_MISMATCH', f"Protected footprint {ref} pad count mismatch: {len(b_pads)} vs {len(a_pads)}", {'ref': ref, 'baseline_count': len(a_pads), 'actual_count': len(b_pads)})
        if set(a_pads) != set(b_pads):
            raise PadInvariantError('PAD_UUID_MISMATCH', f"Protected footprint {ref} pad UUIDs mismatch: {set(b_pads) ^ set(a_pads)}", {'ref': ref})

        for pad_uid, ap in a_pads.items():
            bp = b_pads[pad_uid]
            pad_num = ap['number']

            if ap['uuid'] != bp['uuid']:
                raise PadInvariantError('PAD_UUID_MISMATCH', f"Protected footprint {ref} pad {pad_num} UUID altered", {'ref': ref, 'pad': pad_num})
            if ap['number'] != bp['number']:
                raise PadInvariantError('PAD_NUM_MISMATCH', f"Protected footprint {ref} pad {pad_num} number altered", {'ref': ref, 'pad': pad_num})
            if ap['pad_type'] != bp['pad_type']:
                raise PadInvariantError('PAD_TYPE_MISMATCH', f"Protected footprint {ref} pad {pad_num} type altered: {bp['pad_type']} vs {ap['pad_type']}", {'ref': ref, 'pad': pad_num})
            if ap['shape'] != bp['shape']:
                raise PadInvariantError('PAD_SHAPE_MISMATCH', f"Protected footprint {ref} pad {pad_num} shape altered: {bp['shape']} vs {ap['shape']}", {'ref': ref, 'pad': pad_num})
            if ap['local_pos'] != bp['local_pos']:
                raise PadInvariantError('PAD_POS_MISMATCH', f"Protected footprint {ref} pad {pad_num} moved: {bp['local_pos']} vs {ap['local_pos']}", {'ref': ref, 'pad': pad_num})
            if ap['local_rot'] != bp['local_rot']:
                raise PadInvariantError('PAD_ROT_MISMATCH', f"Protected footprint {ref} pad {pad_num} rotated: {bp['local_rot']} vs {ap['local_rot']}", {'ref': ref, 'pad': pad_num})
            if ap['size'] != bp['size']:
                raise PadInvariantError('PAD_SIZE_MISMATCH', f"Protected footprint {ref} pad {pad_num} resized: {bp['size']} vs {ap['size']}", {'ref': ref, 'pad': pad_num})
            if ap['layers'] != bp['layers']:
                raise PadInvariantError('PAD_LAYERS_MISMATCH', f"Protected footprint {ref} pad {pad_num} layer set altered: {bp['layers']} vs {ap['layers']}", {'ref': ref, 'pad': pad_num})
            if ap['roundrect_rratio'] != bp['roundrect_rratio']:
                raise PadInvariantError('PAD_ROUNDRECT_RATIO_MISMATCH', f"Protected footprint {ref} pad {pad_num} roundrect ratio altered: {bp['roundrect_rratio']} vs {ap['roundrect_rratio']}", {'ref': ref, 'pad': pad_num})
            if ap['chamfer_ratio'] != bp['chamfer_ratio']:
                raise PadInvariantError('PAD_CHAMFER_RATIO_MISMATCH', f"Protected footprint {ref} pad {pad_num} chamfer ratio altered: {bp['chamfer_ratio']} vs {ap['chamfer_ratio']}", {'ref': ref, 'pad': pad_num})
            if ap['chamfer_corners'] != bp['chamfer_corners']:
                raise PadInvariantError('PAD_CHAMFER_CORNERS_MISMATCH', f"Protected footprint {ref} pad {pad_num} chamfer corners altered: {bp['chamfer_corners']} vs {ap['chamfer_corners']}", {'ref': ref, 'pad': pad_num})
            if ap['drill_shape'] != bp['drill_shape']:
                raise PadInvariantError('PAD_DRILL_SHAPE_MISMATCH', f"Protected footprint {ref} pad {pad_num} drill shape altered: {bp['drill_shape']} vs {ap['drill_shape']}", {'ref': ref, 'pad': pad_num})
            if ap['drill_size'] != bp['drill_size']:
                raise PadInvariantError('PAD_DRILL_SIZE_MISMATCH', f"Protected footprint {ref} pad {pad_num} drill altered: {bp['drill_size']} vs {ap['drill_size']}", {'ref': ref, 'pad': pad_num})
            if ap['drill_offset'] != bp['drill_offset']:
                raise PadInvariantError('PAD_DRILL_OFFSET_MISMATCH', f"Protected footprint {ref} pad {pad_num} drill offset altered: {bp['drill_offset']} vs {ap['drill_offset']}", {'ref': ref, 'pad': pad_num})
            if ap['rect_delta'] != bp['rect_delta']:
                raise PadInvariantError('PAD_RECT_DELTA_MISMATCH', f"Protected footprint {ref} pad {pad_num} rect delta altered: {bp['rect_delta']} vs {ap['rect_delta']}", {'ref': ref, 'pad': pad_num})

        verified_fixed_count += 1
    if verified_fixed_count != 75:
        raise FoundationInvariantError('VERIFIED_FIXED_COUNT_MISMATCH', f"Expected 75 verified fixed footprints, got {verified_fixed_count}", {'actual': verified_fixed_count, 'expected': 75})

    # Verify transferred footprints against baseline
    for ref in transferred:
        if of[ref]['uuid'] != rf[ref]['uuid']:
            raise OwnershipInvariantError('TRANSFERRED_UUID_MISMATCH', f"Transferred footprint {ref} UUID mismatch with baseline", {'ref': ref, 'actual': rf[ref]['uuid'], 'baseline': of[ref]['uuid']})
        if set(of[ref]['pads']) != set(rf[ref]['pads']):
            raise OwnershipInvariantError('TRANSFERRED_PADS_MISMATCH', f"Transferred footprint {ref} pad sets mismatch with baseline", {'ref': ref})

    # 8. Protected Proof Copper (14 tracks, 24 microvias) & Raw Saved-Net Invariant
    orig_tracks = baseline_data['tracks']
    orig_vias = baseline_data['vias']
    live_tracks = main_data['tracks']
    live_vias = main_data['vias']

    # Forbidden ordinary copper arcs check on MAIN
    main_copper_arcs = [a for a in main_data.get('arcs', {}).values() if a.get('layer') and 'Cu' in a.get('layer')]
    if main_copper_arcs:
        raise RoutingInvariantError('ROUTING_ARC_ADDED',
                                    f"Ordinary copper arc detected on MAIN: {len(main_copper_arcs)} arc(s) found",
                                    {'arcs': [a['uuid'] for a in main_copper_arcs]})

    if len(live_tracks) > 14:
        raise ProofTrackInvariantError('ROUTING_TRACK_ADDED', f"Expected exactly 14 tracks on MAIN, got {len(live_tracks)} (unauthorized track added)", {'actual': len(live_tracks), 'expected': 14})
    if len(live_tracks) < 14:
        raise ProofTrackInvariantError('TR_DEL_MISMATCH', f"Expected exactly 14 tracks on MAIN, got {len(live_tracks)} (proof track deleted)", {'actual': len(live_tracks), 'expected': 14})
    if set(live_tracks) != EXPECTED_PROOF_TRACK_UUIDS:
        diff_added = set(live_tracks) - EXPECTED_PROOF_TRACK_UUIDS
        if diff_added:
            raise ProofTrackInvariantError('ROUTING_TRACK_ADDED', f"Proof track set mismatch: unauthorized tracks {diff_added}", {'added': list(diff_added)})
        else:
            raise ProofTrackInvariantError('TR_DEL_MISMATCH', f"Proof track set mismatch: missing tracks {EXPECTED_PROOF_TRACK_UUIDS - set(live_tracks)}")

    if len(live_vias) > 24:
        raise ProofViaInvariantError('ROUTING_VIA_ADDED', f"Expected exactly 24 vias on MAIN, got {len(live_vias)} (unauthorized via added)", {'actual': len(live_vias), 'expected': 24})
    if len(live_vias) < 24:
        raise ProofViaInvariantError('VIA_DEL_MISMATCH', f"Expected exactly 24 vias on MAIN, got {len(live_vias)} (proof via deleted)", {'actual': len(live_vias), 'expected': 24})
    if set(live_vias) != EXPECTED_PROOF_VIA_UUIDS:
        diff_added = set(live_vias) - EXPECTED_PROOF_VIA_UUIDS
        if diff_added:
            raise ProofViaInvariantError('ROUTING_VIA_ADDED', f"Proof via set mismatch: unauthorized vias {diff_added}", {'added': list(diff_added)})
        else:
            raise ProofViaInvariantError('VIA_DEL_MISMATCH', f"Proof via set mismatch: missing vias {EXPECTED_PROOF_VIA_UUIDS - set(live_vias)}")

    for track_uid, lt in live_tracks.items():
        if track_uid not in orig_tracks:
            raise ProofTrackInvariantError('ROUTING_TRACK_ADDED', f"Track {track_uid} missing from baseline board")
        ot = orig_tracks[track_uid]
        if lt['net'] != ot['net']:
            raise ProofTrackInvariantError('TR_NET_MISMATCH', f"Proof track {track_uid} net altered: '{lt['net']}' vs '{ot['net']}'", {'track_uuid': track_uid, 'baseline': ot['net'], 'actual': lt['net']})
        if lt['layer'] != ot['layer']:
            raise ProofTrackInvariantError('TR_LAYER_MISMATCH', f"Proof track {track_uid} layer altered: {lt['layer']} vs {ot['layer']}", {'track_uuid': track_uid, 'baseline': ot['layer'], 'actual': lt['layer']})
        if lt['start'] != ot['start']:
            raise ProofTrackInvariantError('TR_MOVE_MISMATCH', f"Proof track {track_uid} start moved: {lt['start']} vs {ot['start']}", {'track_uuid': track_uid, 'baseline': ot['start'], 'actual': lt['start']})
        if lt['end'] != ot['end']:
            raise ProofTrackInvariantError('TR_MOVE_MISMATCH', f"Proof track {track_uid} end moved: {lt['end']} vs {ot['end']}", {'track_uuid': track_uid, 'baseline': ot['end'], 'actual': lt['end']})
        if lt['width'] != ot['width']:
            raise ProofTrackInvariantError('TR_WIDTH_MISMATCH', f"Proof track {track_uid} width altered: {lt['width']} vs {ot['width']}", {'track_uuid': track_uid, 'baseline': ot['width'], 'actual': lt['width']})

    for via_uid, lv in live_vias.items():
        if via_uid not in orig_vias:
            raise ProofViaInvariantError('ROUTING_VIA_ADDED', f"Via {via_uid} missing from baseline board")
        ov = orig_vias[via_uid]
        if lv['pos'] != ov['pos']:
            raise ProofViaInvariantError('VIA_MOVE_MISMATCH', f"Proof via {via_uid} position moved: {lv['pos']} vs {ov['pos']}", {'via_uuid': via_uid, 'baseline': ov['pos'], 'actual': lv['pos']})
        if lv['net'] != ov['net']:
            raise ProofViaInvariantError('VIA_NET_MISMATCH', f"Proof via {via_uid} net altered: '{lv['net']}' vs '{ov['net']}'", {'via_uuid': via_uid, 'baseline': ov['net'], 'actual': lv['net']})
        if lv['via_type'] != ov['via_type']:
            raise ProofViaInvariantError('VIA_TYPE_MISMATCH', f"Proof via {via_uid} type altered: {lv['via_type']} vs {ov['via_type']}", {'via_uuid': via_uid, 'baseline': ov['via_type'], 'actual': lv['via_type']})
        if lv['layers'] != ov['layers']:
            raise ProofViaInvariantError('VIA_LAYERS_MISMATCH', f"Proof via {via_uid} layer span altered: {lv['layers']} vs {ov['layers']}", {'via_uuid': via_uid, 'baseline': ov['layers'], 'actual': lv['layers']})
        if lv['size'] != ov['size']:
            raise ProofViaInvariantError('VIA_DIAM_MISMATCH', f"Proof via {via_uid} diameter altered: {lv['size']} vs {ov['size']}", {'via_uuid': via_uid, 'baseline': ov['size'], 'actual': lv['size']})
        if lv['drill'] != ov['drill']:
            raise ProofViaInvariantError('VIA_DRILL_MISMATCH', f"Proof via {via_uid} drill altered: {lv['drill']} vs {ov['drill']}", {'via_uuid': via_uid, 'baseline': ov['drill'], 'actual': lv['drill']})

    # Removed copper audit: exactly 36 items removed from baseline
    all_orig_copper = set(orig_tracks) | set(orig_vias)
    all_live_copper = set(live_tracks) | set(live_vias)
    deleted = all_orig_copper - all_live_copper
    if len(deleted) != 36:
        raise RoutingInvariantError('REMOVED_COPPER_COUNT_MISMATCH', f"Expected 36 removed copper items, got {len(deleted)}", {'actual': len(deleted), 'expected': 36})
    if not deleted.isdisjoint(EXPECTED_PROOF_TRACK_UUIDS):
        raise ProofTrackInvariantError('PROOF_TRACK_REMOVED', "Proof track removed from MAIN!", {'tracks': list(deleted & EXPECTED_PROOF_TRACK_UUIDS)})
    if not deleted.isdisjoint(EXPECTED_PROOF_VIA_UUIDS):
        raise ProofViaInvariantError('PROOF_VIA_REMOVED', "Proof via removed from MAIN!", {'vias': list(deleted & EXPECTED_PROOF_VIA_UUIDS)})

    for del_uid in deleted:
        item = orig_tracks.get(del_uid) or orig_vias.get(del_uid)
        del_net = item['net'] or ''
        if not ('PPG' in del_net or del_net == 'GND'):
            raise RoutingInvariantError('UNEXPECTED_COPPER_REMOVED', f"Unexpected non-optical copper item removed: {del_uid} net={del_net}", {'uuid': del_uid, 'net': del_net})

    # 9. Copper planes and keepouts
    planes = [z for z in main_data['zones'] if not z['is_keepout']]
    keepouts = [z for z in main_data['zones'] if z['is_keepout']]
    if len(planes) != 2:
        raise RoutingInvariantError('ZONE_PLANE_COUNT_MISMATCH', f"Expected 2 copper planes, got {len(planes)}", {'actual': len(planes), 'expected': 2})
    if len(keepouts) != 2:
        raise RoutingInvariantError('ZONE_KEEPOUT_COUNT_MISMATCH', f"Expected 2 keepout zones, got {len(keepouts)}", {'actual': len(keepouts), 'expected': 2})

    plane_layers = set()
    for z in planes:
        if len(z['layers']) != 1:
            raise RoutingInvariantError('ZONE_PLANE_LAYERS_MISMATCH', f"Plane assigned to multiple layers: {z['layers']}", {'layers': z['layers']})
        if z['net_name'] != 'GND':
            raise RoutingInvariantError('ZONE_PLANE_NET_MISMATCH', f"Plane net is '{z['net_name']}', expected 'GND'", {'actual': z['net_name'], 'expected': 'GND'})
        plane_layers.add(z['layers'][0])
    if plane_layers != {'In1.Cu', 'In6.Cu'}:
        raise RoutingInvariantError('ZONE_PLANE_LAYERS_MISMATCH', f"Expected In1.Cu and In6.Cu planes, got {plane_layers}", {'actual': sorted(plane_layers)})

    for z in keepouts:
        if z['layers'] != ['B.Cu']:
            raise RoutingInvariantError('ZONE_KEEPOUT_LAYER_MISMATCH', f"Keepout assigned to layers {z['layers']}, expected ['B.Cu']", {'layers': z['layers']})
        if z['net_name']:
            raise RoutingInvariantError('ZONE_KEEPOUT_NET_ASSIGNED', f"Keepout zone has unexpected net assignment: '{z['net_name']}'", {'net': z['net_name']})

    # 10. User.3 EMI Shield Polygon
    user3_polys = main_data['drawings']['user3_polys']
    if len(user3_polys) != 1:
        code = 'SHIELD_RESERVATION_MISSING' if len(user3_polys) == 0 else 'SHIELD_RESERVATION_DUPLICATE'
        raise EnvelopeInvariantError(code, f"Expected exactly 1 User.3 shield polygon, got {len(user3_polys)}", {'count': len(user3_polys)})
    s_pts = user3_polys[0]
    if len(s_pts) != 10:
        raise EnvelopeInvariantError('SHIELD_POLYGON_INVALID', f"Expected 10-point stepped shield perimeter, got {len(s_pts)}", {'point_count': len(s_pts)})
    area = polygon_area(s_pts)
    if not (80.0 <= area <= 110.0):
        raise EnvelopeInvariantError('SHIELD_AREA_OUT_OF_RANGE', f"Shield polygon area {area:.2f} mm2 outside expected range [80, 110]", {'area': area})

    s_edges = list(zip(s_pts, s_pts[1:] + [s_pts[0]]))
    for i in range(len(s_edges)):
        for j in range(i + 2, len(s_edges)):
            if i == 0 and j == len(s_edges) - 1:
                continue
            if segments_intersect(s_edges[i][0], s_edges[i][1], s_edges[j][0], s_edges[j][1]):
                raise EnvelopeInvariantError('SHIELD_SELF_INTERSECTION', f"Shield polygon self-intersects between edges {i} and {j}", {'edge_i': i, 'edge_j': j})

    for ref, f in mf.items():
        if f['layer'] != 'F.Cu':
            continue
        bx = f['bbox']
        rect_pts = [(bx[0], bx[1]), (bx[2], bx[1]), (bx[2], bx[3]), (bx[0], bx[3])]
        rect_edges = list(zip(rect_pts, rect_pts[1:] + [rect_pts[0]]))

        for e1 in s_edges:
            for e2 in rect_edges:
                if segments_intersect(e1[0], e1[1], e2[0], e2[1]):
                    raise EnvelopeInvariantError('SHIELD_COURTYARD_CROSSING', f"Shield perimeter intersects/overlaps courtyard of {ref}", {'ref': ref})

        if ref in ENCLOSED_BY_SHIELD:
            for cpt in rect_pts:
                if not point_in_polygon(cpt[0], cpt[1], s_pts):
                    raise EnvelopeInvariantError('SHIELD_ENCLOSED_VIOLATION', f"Enclosed component {ref} corner {cpt} not inside shield", {'ref': ref, 'corner': cpt})
        else:
            for spt in s_pts:
                if bx[0] < spt[0] < bx[2] and bx[1] < spt[1] < bx[3]:
                    raise EnvelopeInvariantError('SHIELD_EXCLUDED_VIOLATION', f"Shield vertex {spt} inside courtyard of excluded {ref}", {'ref': ref, 'vertex': spt})
            for cpt in rect_pts:
                if point_in_polygon(cpt[0], cpt[1], s_pts):
                    raise EnvelopeInvariantError('SHIELD_EXCLUDED_VIOLATION', f"Excluded component {ref} corner inside shield polygon", {'ref': ref, 'corner': cpt})

    # 11. User.2 J202 Harness Reservation
    j202_meta = plan.get('j202_reservation', {})
    if not j202_meta:
        raise MetadataInvariantError('J202_METADATA_MISSING', "Missing j202_reservation metadata in plan")
    if not (j202_meta.get('layer') == 'User.2' and j202_meta.get('shape') == 'rect'):
        raise MetadataInvariantError('J202_METADATA_INVALID', "Invalid j202_reservation metadata structure")
    expected_bbox = j202_meta['expected_bbox']
    tol = j202_meta.get('tolerance_mm', 0.05)

    j202_candidates = []
    for cand_bx in main_data['drawings']['user2_rects']:
        if all(abs(cand_bx[i] - expected_bbox[i]) <= tol for i in range(4)):
            j202_candidates.append(cand_bx)
    if len(j202_candidates) != 1:
        code = 'J202_RESERVATION_MISSING' if len(j202_candidates) == 0 else 'J202_RESERVATION_DUPLICATE'
        raise EnvelopeInvariantError(code, f"Expected exactly 1 J202 reservation matching {expected_bbox}, found {len(j202_candidates)}", {'found': len(j202_candidates), 'expected_bbox': expected_bbox})
    j202_rect = j202_candidates[0]

    j202_texts = [t for t in main_data['drawings']['user2_texts'] if 'J202' in t]
    if len(j202_texts) != 1:
        code = 'J202_TEXT_ANNOTATION_MISSING' if len(j202_texts) == 0 else 'J202_TEXT_ANNOTATION_DUPLICATE'
        raise EnvelopeInvariantError(code, f"Expected exactly 1 J202 text annotation on User.2, found {len(j202_texts)}", {'found': len(j202_texts)})

    for ref, f in mf.items():
        if f['layer'] != 'F.Cu':
            continue
        bx = f['bbox']
        overlap = not (j202_rect[2] <= bx[0] or j202_rect[0] >= bx[2] or j202_rect[3] <= bx[1] or j202_rect[1] >= bx[3])
        if overlap:
            raise EnvelopeInvariantError('J202_COURTYARD_OVERLAP', f"J202 harness window overlaps {ref}", {'ref': ref})

    # 12. Board settings & design rules against Git baseline
    oldpro = json.loads(subprocess.check_output(['git', 'show', f'{START}:sportwatch_revA.kicad_pro'], cwd=git_root))
    newpro = json.loads((ROOT / 'sportwatch_revA.kicad_pro').read_text())
    if newpro['board'] != oldpro['board']:
        raise MetadataInvariantError('HDI_SETTINGS_CHANGED', 'MAIN HDI/DRC settings changed')
    oldclasses = {x['name']: x for x in oldpro['net_settings']['classes']}
    newclasses = {x['name']: x for x in newpro['net_settings']['classes']}
    if set(oldclasses) - set(newclasses) != {'Optical_PD_Guard'} or not all(x == oldclasses[k] for k, x in newclasses.items()):
        raise MetadataInvariantError('NETCLASSES_CHANGED', 'MAIN netclass settings altered')

    oldrules = subprocess.check_output(['git', 'show', f'{START}:sportwatch_revA.kicad_dru'], cwd=git_root).decode()
    expected_dru_text = oldrules[:oldrules.index('(rule "Optical PD Guard Netclass Rules"')].rstrip() + '\n'
    if (ROOT / 'sportwatch_revA.kicad_dru').read_text() != expected_dru_text:
        raise MetadataInvariantError('DRU_RULES_CHANGED', 'MAIN custom DRC rules altered')

    # 13. Envelope compliance & placements
    placed = []
    partial = []
    outside = []
    for ref, f in sorted(mf.items()):
        z = f['bbox']
        r = max(math.hypot(x - 100, y - 100) for x in [z[0], z[2]] for y in [z[1], z[3]])
        row = {
            'ref': ref,
            'xy_mm': f['pos'],
            'orientation_deg': f['rot'],
            'side': f['layer'],
            'bbox_mm': z,
            'max_corner_radius_mm': round(r, 3)
        }
        (placed if r < 23 else partial if math.hypot(f['pos'][0] - 100, f['pos'][1] - 100) < 23 else outside).append(row)
    if len(placed) != 184 or partial or outside:
        raise EnvelopeInvariantError('ENVELOPE_PLACEMENT_VIOLATION', f"Envelope placement violation: {len(placed)} placed, {len(partial)} partial, {len(outside)} outside",
                                     {'placed': len(placed), 'partial': len(partial), 'outside': len(outside)})

    expected_bcu_refs = {f'R{i}' for i in range(901, 911)} | {f'C{i}' for i in range(901, 907)} | {'C206'}
    actual_bcu_refs = {ref for ref, f in mf.items() if f['layer'] == 'B.Cu'}
    if actual_bcu_refs != expected_bcu_refs:
        raise OwnershipInvariantError('BOTTOM_LAYER_COMPONENTS_MISMATCH', f"Bottom layer component set mismatch: {actual_bcu_refs ^ expected_bcu_refs}",
                                      {'diff': list(actual_bcu_refs ^ expected_bcu_refs)})
    rear_copper_arcs = [a for a in rear_data.get('arcs', {}).values() if a.get('layer') and 'Cu' in a.get('layer')]
    if rear_data.get('tracks') or rear_data.get('vias') or rear_data.get('zones') or rear_copper_arcs:
        raise RoutingInvariantError('REAR_ROUTING_ADDED',
                                    f"Rear staging shell routed: tracks={len(rear_data.get('tracks', {}))}, vias={len(rear_data.get('vias', {}))}, arcs={len(rear_copper_arcs)}, zones={len(rear_data.get('zones', []))}",
                                    {'tracks': len(rear_data.get('tracks', {})), 'vias': len(rear_data.get('vias', {})), 'arcs': len(rear_copper_arcs), 'zones': len(rear_data.get('zones', []))})

    forbidden = ('PD1_IN', 'PD2_IN', 'PD_GND', 'VREF', 'LED_MUX_SEL')
    forbidden_ppg = [n for n in main_data['net_table'].values() if 'PPG' in n and any(s in n for s in forbidden)]
    if forbidden_ppg:
        raise RoutingInvariantError('FORBIDDEN_PPG_NET_FOUND', f"Forbidden optical net found on MAIN: {forbidden_ppg}", {'nets': forbidden_ppg})

    cap_owner = {
        'C120': 'U102', 'C121': 'U102', 'C122': 'U103', 'C123': 'U103',
        'C124': 'U104', 'C125': 'U104', 'C126': 'U105', 'C127': 'U105',
        'C128': 'U106', 'C701': 'U702', 'C702': 'U702', 'C703': 'U702',
        'C704': 'U702', 'C705': 'U703', 'C801': 'U5', 'C803': 'U4',
        'C804': 'U4', 'C1001': 'U7', 'C1002': 'U7', 'C206': 'U201'
    } | {f'C{i}': 'U901' for i in range(901, 907)}

    distances = []
    for ref, owner in cap_owner.items():
        pairs = []
        for a_pad in mf[ref]['pads'].values():
            for c_pad in mf[owner]['pads'].values():
                if a_pad['net_name'] and a_pad['net_name'] != 'GND' and a_pad['net_name'] == c_pad['net_name']:
                    # Calculate world pad centers
                    a_rad = math.radians(mf[ref]['rot'])
                    a_wx = mf[ref]['pos'][0] + a_pad['local_pos'][0] * math.cos(a_rad) - a_pad['local_pos'][1] * math.sin(a_rad)
                    a_wy = mf[ref]['pos'][1] + a_pad['local_pos'][0] * math.sin(a_rad) + a_pad['local_pos'][1] * math.cos(a_rad)
                    c_rad = math.radians(mf[owner]['rot'])
                    c_wx = mf[owner]['pos'][0] + c_pad['local_pos'][0] * math.cos(c_rad) - c_pad['local_pos'][1] * math.sin(c_rad)
                    c_wy = mf[owner]['pos'][1] + c_pad['local_pos'][0] * math.sin(c_rad) + c_pad['local_pos'][1] * math.cos(c_rad)
                    pairs.append((a_wx, a_wy, c_wx, c_wy))
        if pairs:
            d = min(math.hypot(p[0] - p[2], p[1] - p[3]) for p in pairs)
            distances.append({
                'ref': ref,
                'owner': owner,
                'side': mf[ref]['layer'],
                'nearest_same_supply_pin_mm': round(d, 3),
                'meaning': 'XY pad distance; not routed loop length or validated inductance'
            })

    return {
        'decoupling_distances': distances,
        'status': 'PASS',
        'source_HEAD': START,
        'baseline_blob': BASELINE_PCB_BLOB,
        'MAIN': {
            'schematic_components': 202,
            'schematic_nets': 359,
            'footprints': 184,
            'placed': 184,
            'staged_unplaced': 0,
            'partial_intersecting': 0,
            'B_Cu_components': 17,
            'footprint_TBD': sorted(set(mc) - set(mf))
        },
        'REAR': {
            'schematic_components': 46,
            'schematic_nets': 44,
            'staging_footprints': 44,
            'footprint_TBD': sorted(set(rc) - set(rf)),
            'routing_items': 0
        },
        'transferred_refs': sorted(transferred),
        'proof': {
            'assembled_connector_positions': 24,
            'logical_boundary_nets': 13,
            'original_components_verified': 242,
            'intentional_source_exception': 'J202 protection ECO',
            'retained_fixed_footprints': verified_fixed_count,
            'preserved_tracks': 14,
            'preserved_vias': 24,
            'preserved_arcs': 0,
            'removed_tracks': 34,
            'removed_vias': 2,
            'MAIN_outline_unchanged': True,
            'MAIN_HDI_rules_preserved': True,
            'inherited_unmodeled_blank_pad': 'U102.25; preserved, no invented net'
        },
        'placements': placed
    }


if __name__ == '__main__':
    if not (4 <= len(sys.argv) <= 6):
        sys.stderr.write(f"Usage error: invalid arguments\n{__doc__}\n")
        sys.exit(2)
    main_pcb_arg = sys.argv[4] if len(sys.argv) >= 5 else None
    rear_pcb_arg = sys.argv[5] if len(sys.argv) >= 6 else None
    out_file = Path(sys.argv[3])
    try:
        result = audit(sys.argv[1], sys.argv[2], main_pcb_arg, rear_pcb_arg)
        out_file.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: v for k, v in result.items() if k != 'placements'}))
    except PhysicalInvariantError as e:
        err_dict = {
            'status': 'FAIL',
            'error_type': e.__class__.__name__,
            'failure_code': e.failure_code,
            'message': str(e),
            'details': e.details
        }
        try:
            out_file.write_text(json.dumps(err_dict, indent=2) + '\n')
        except Exception:
            pass
        print(f"PhysicalInvariantError [{e.failure_code}]: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        err_dict = {
            'status': 'ERROR',
            'error_type': e.__class__.__name__,
            'message': str(e)
        }
        try:
            out_file.write_text(json.dumps(err_dict, indent=2) + '\n')
        except Exception:
            pass
        print(f"InternalError [{e.__class__.__name__}]: {e}", file=sys.stderr)
        sys.exit(1)
