#!/usr/bin/env python3
"""
apply_pcb_foundation.py
Establishes the KiCad PCB foundation:
1. Multilayer 8-layer HDI stackup
2. 46.0 mm circular Edge.Cuts
3. Courtyard geometry completion for NT201, NT202, NT401, NT402, U5, U7
4. Provisional placement for 7 critical clusters
5. Representative fanout trial for Apollo510B and eMMC
"""

import sys
import os
import json
import pcbnew

def main():
    pcb_path = 'sportwatch_revA.kicad_pcb'
    print(f'Loading board: {pcb_path}')
    board = pcbnew.LoadBoard(pcb_path)

    # 1. Configure 8 copper layers
    print('Setting copper layer count to 8...')
    board.SetCopperLayerCount(8)
    l_fcu = pcbnew.F_Cu
    l_in1 = board.GetLayerID('In1.Cu')
    l_in2 = board.GetLayerID('In2.Cu')
    l_in3 = board.GetLayerID('In3.Cu')
    l_in4 = board.GetLayerID('In4.Cu')
    l_in5 = board.GetLayerID('In5.Cu')
    l_in6 = board.GetLayerID('In6.Cu')
    l_bcu = pcbnew.B_Cu

    print(f'Layer IDs: F.Cu={l_fcu}, In1={l_in1}, In2={l_in2}, In3={l_in3}, In4={l_in4}, In5={l_in5}, In6={l_in6}, B.Cu={l_bcu}')

    # 2. Design Settings
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.075)
    ds.m_MinClearance = pcbnew.FromMM(0.075)
    ds.m_MicroViasMinDrill = pcbnew.FromMM(0.100)
    ds.m_MicroViasMinSize = pcbnew.FromMM(0.200)
    ds.m_ViasMinSize = pcbnew.FromMM(0.400)
    ds.m_ViasMinAnnularWidth = pcbnew.FromMM(0.050)  # 50 um laser microvia annular ring
    ds.m_CopperEdgeClearance = pcbnew.FromMM(0.500)
    ds.m_HoleClearance = pcbnew.FromMM(0.200)

    # 3. Add 46.0 mm circular Edge.Cuts
    print('Adding 46.0 mm circular Edge.Cuts...')
    for drawing in list(board.GetDrawings()):
        if drawing.GetLayer() == pcbnew.Edge_Cuts:
            board.Delete(drawing)

    circle = pcbnew.PCB_SHAPE(board)
    circle.SetShape(pcbnew.SHAPE_T_CIRCLE)
    circle.SetCenter(pcbnew.VECTOR2I(pcbnew.FromMM(100.0), pcbnew.FromMM(100.0)))
    circle.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(123.0), pcbnew.FromMM(100.0)))
    circle.SetWidth(pcbnew.FromMM(0.1))
    circle.SetLayer(pcbnew.Edge_Cuts)
    board.Add(circle)

    # 4. Courtyard completion helper
    def add_courtyard(fp, w_mm, h_mm, layer):
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                fp.Delete(item)
        shape = pcbnew.PCB_SHAPE(fp)
        shape.SetShape(pcbnew.SHAPE_T_RECT)
        pos = fp.GetPosition()
        shape.SetStart(pos + pcbnew.VECTOR2I(pcbnew.FromMM(-w_mm / 2.0), pcbnew.FromMM(-h_mm / 2.0)))
        shape.SetEnd(pos + pcbnew.VECTOR2I(pcbnew.FromMM(w_mm / 2.0), pcbnew.FromMM(h_mm / 2.0)))
        shape.SetWidth(pcbnew.FromMM(0.05))
        shape.SetLayer(layer)
        fp.Add(shape)

    # 5. Place 7 Critical Clusters with validated non-overlapping coordinates
    critical_placements = {
        # Cluster 1 (F.Cu)
        'U101':  (100.0, 97.5, 0.0, False),
        'U901':  (100.0, 107.0, 0.0, False),
        'Y102':  (94.5, 98.5, 0.0, False),
        'Y101':  (94.5, 95.5, 0.0, False),
        'C118':  (91.5, 94.8, 0.0, False),
        'C119':  (91.5, 96.2, 0.0, False),
        'L101':  (95.5, 93.5, 0.0, False),
        # Cluster 2 (B.Cu)
        'D413':  (100.0, 96.8, 90.0, True),
        'D414':  (100.0, 103.2, 90.0, True),
        'D423':  (96.8, 100.0, 0.0, True),
        'D424':  (103.2, 100.0, 0.0, True),
        'D401':  (95.0, 95.0, 0.0, True),
        'D402':  (105.0, 95.0, 0.0, True),
        'D403':  (95.0, 105.0, 0.0, True),
        'D404':  (105.0, 105.0, 0.0, True),
        'D405':  (92.2, 100.0, 90.0, True),
        'D406':  (100.0, 92.8, 0.0, True),
        'D407':  (107.8, 100.0, 90.0, True),
        'U12':   (88.5, 96.5, 0.0, True),
        'U13':   (88.5, 103.5, 0.0, True),
        'U402':  (89.0, 92.0, 0.0, True),
        'U403':  (92.5, 91.5, 0.0, True),
        'U404':  (96.0, 91.0, 0.0, True),
        'U405':  (89.0, 108.0, 0.0, True),
        'U406':  (92.5, 108.5, 0.0, True),
        'U407':  (96.0, 109.0, 0.0, True),
        'NT401': (85.5, 96.5, 0.0, True),
        'NT402': (85.5, 103.5, 0.0, True),
        # Cluster 3 (B.Cu)
        'U401':  (91.0, 113.5, 0.0, True),
        'L401':  (87.5, 113.5, 0.0, True),
        'C401':  (93.8, 113.5, 90.0, True),
        'C402':  (91.0, 116.5, 0.0, True),
        # Cluster 4 (F.Cu)
        'U201':  (89.5, 108.5, 0.0, False),
        'L201':  (84.5, 106.5, 0.0, False),
        'L202':  (84.5, 109.0, 0.0, False),
        'C201':  (85.5, 103.5, 90.0, False),
        'C202':  (87.5, 103.5, 90.0, False),
        'C203':  (89.5, 103.5, 90.0, False),
        'C204':  (81.5, 106.5, 0.0, False),
        'C205':  (81.5, 108.5, 0.0, False),
        'NT201': (82.5, 104.5, 0.0, False),
        'NT202': (82.5, 110.5, 0.0, False),
        # Cluster 5 (F.Cu)
        'U202':  (89.5, 114.5, 0.0, False),
        'L203':  (86.0, 114.0, 0.0, False),
        'C213':  (86.5, 116.0, 0.0, False),
        'C214':  (89.5, 116.8, 0.0, False),
        # Cluster 6 (F.Cu)
        'U9':    (111.0, 103.5, 0.0, False),
        'Y1':    (111.0, 97.5, 0.0, False),
        'L601':  (116.5, 103.5, 0.0, False),
        'U11':   (111.0, 110.0, 0.0, False),
        'C601':  (106.0, 102.0, 90.0, False),
        'C602':  (106.0, 105.0, 90.0, False),
        'C603':  (108.0, 98.5, 0.0, False),
        'C604':  (114.0, 98.5, 0.0, False),
        'C605':  (116.5, 101.0, 0.0, False),
        'C606':  (116.5, 106.0, 0.0, False),
        'C607':  (116.5, 107.5, 0.0, False),
        # Cluster 7 (F.Cu)
        'U8':    (100.0, 86.5, 0.0, False),
        'R1420': (100.0, 80.0, 90.0, False),
        'C1420': (98.7, 80.0, 0.0, False),
        'C1421': (101.3, 80.0, 0.0, False),
    }

    print('Applying provisional placement for 7 critical clusters...')
    for ref, (x_mm, y_mm, rot_deg, is_back) in critical_placements.items():
        fp = board.FindFootprintByReference(ref)
        if not fp:
            print(f'Warning: footprint {ref} not found!')
            continue
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
        fp.SetOrientationDegrees(rot_deg)
        if is_back and not fp.IsFlipped():
            fp.Flip(fp.GetPosition(), False)
        elif not is_back and fp.IsFlipped():
            fp.Flip(fp.GetPosition(), False)

    # Apply courtyard additions after positioning
    print('Updating courtyards for NT201, NT202, NT401, NT402, U5, U7...')
    for nt_ref, l_crt in [('NT201', pcbnew.F_CrtYd), ('NT202', pcbnew.F_CrtYd),
                          ('NT401', pcbnew.B_CrtYd), ('NT402', pcbnew.B_CrtYd)]:
        nt = board.FindFootprintByReference(nt_ref)
        if nt:
            nt.SetAllowMissingCourtyard(False)
            add_courtyard(nt, 1.8, 0.8, l_crt)

    u5 = board.FindFootprintByReference('U5')
    if u5:
        add_courtyard(u5, 2.9, 2.7, pcbnew.F_CrtYd)

    u7 = board.FindFootprintByReference('U7')
    if u7:
        add_courtyard(u7, 2.0, 1.9, pcbnew.F_CrtYd)

    # 6. Task F: Representative Fanout Trial
    print('Generating representative fanout trial for Apollo510B and eMMC...')
    for t in list(board.GetTracks()):
        board.Delete(t)

    net_gnd = board.FindNet('GND')
    net_emmc_dat4 = board.FindNet('/EMMC_DAT4')
    net_emmc_dat7 = board.FindNet('/EMMC_DAT7')
    net_emmc_dat0 = board.FindNet('/EMMC_DAT0')
    net_emmc_dat5 = board.FindNet('/EMMC_DAT5')

    def add_microvia(x_mm, y_mm, l_start, l_end, net):
        via = pcbnew.PCB_VIA(board)
        via.SetViaType(pcbnew.VIATYPE_MICROVIA)
        via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
        via.SetWidth(pcbnew.FromMM(0.200))
        via.SetDrill(pcbnew.FromMM(0.100))
        via.SetLayerPair(l_start, l_end)
        if net:
            via.SetNet(net)
        board.Add(via)
        return via

    def add_track(x1, y1, x2, y2, layer, width_mm, net):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        tr.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        tr.SetLayer(layer)
        tr.SetWidth(pcbnew.FromMM(width_mm))
        if net:
            tr.SetNet(net)
        board.Add(tr)
        return tr

    # Trial 1: Inner Ground Ball G7 on Apollo510B at (100.0, 97.5) -> VIPPO L1 to L2
    if net_gnd:
        add_microvia(100.0, 97.5, l_fcu, l_in1, net_gnd)
        add_track(100.0, 97.5, 100.0, 97.6, l_in1, 0.100, net_gnd)

    # Trial 2: Inner Signal Ball H7 on Apollo510B at (100.0, 97.9) (/EMMC_DAT4)
    # Stacked microvia L1-L2, L2-L3, escape trace on L3 (In2.Cu) southwards
    if net_emmc_dat4:
        add_microvia(100.0, 97.9, l_fcu, l_in1, net_emmc_dat4)
        add_microvia(100.0, 97.9, l_in1, l_in2, net_emmc_dat4)
        add_track(100.0, 97.9, 100.0, 100.5, l_in2, 0.075, net_emmc_dat4)

    # Trial 3: Signal Ball L8 on Apollo510B at (100.4, 99.1) (/EMMC_DAT7)
    # Stacked microvia L1-L2, L2-L3 to L3, escape trace on L3 southwards
    if net_emmc_dat7:
        add_microvia(100.4, 99.1, l_fcu, l_in1, net_emmc_dat7)
        add_microvia(100.4, 99.1, l_in1, l_in2, net_emmc_dat7)
        add_track(100.4, 99.1, 100.4, 100.5, l_in2, 0.075, net_emmc_dat7)

    # Trial 4: Outer Signal Ball A3 on eMMC at (97.75, 103.75) (/EMMC_DAT0)
    # Direct escape trace on L1 (F.Cu) northwards
    if net_emmc_dat0:
        add_track(97.75, 103.75, 97.75, 102.5, l_fcu, 0.075, net_emmc_dat0)

    # Trial 5: Inner Signal Ball B4 on eMMC at (98.25, 104.25) (/EMMC_DAT5)
    # Stacked microvia L1-L2, L2-L3, escape trace on L3 (In2.Cu) northwards
    if net_emmc_dat5:
        add_microvia(98.25, 104.25, l_fcu, l_in1, net_emmc_dat5)
        add_microvia(98.25, 104.25, l_in1, l_in2, net_emmc_dat5)
        add_track(98.25, 104.25, 98.25, 102.5, l_in2, 0.075, net_emmc_dat5)

    print('Saving board...')
    pcbnew.SaveBoard(pcb_path, board)
    print('Board saved successfully via pcbnew!')

if __name__ == '__main__':
    main()
