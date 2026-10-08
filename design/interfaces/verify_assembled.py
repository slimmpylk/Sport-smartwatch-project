#!/usr/bin/env python3
"""Audit native per-root XML through the tracked abstract harness contract.

Usage: python3 design/interfaces/verify_assembled.py MAIN.xml REAR.xml OUTPUT.json
No KiCad/akcli Python packages required. Exits nonzero on any failed assertion.
"""
import csv, hashlib, json, sys, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parent.parent

def load(path):
    r=ET.parse(path).getroot()
    cs=r.findall('components/comp')
    refs=[c.get('ref') for c in cs]
    assert len(refs)==len(set(refs)), f'Duplicate references: {path}'
    nets={n.get('name'): {(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in r.findall('nets/net')}
    pin={p:n for n,ps in nets.items() for p in ps}
    return {c.get('ref'):c for c in cs}, nets, pin

def audit(main_path,rear_path):
    source=json.loads((BASE/'source_pin_membership.json').read_text())
    checkpoint=json.loads((BASE/'source_checkpoint.json').read_text())
    contract=json.loads((BASE/'main_rear_interface.json').read_text())
    charger=json.loads((BASE/'charger_harness.json').read_text())
    main,mnets,mpins=load(main_path);rear,rnets,rpins=load(rear_path)
    assert not set(main)&set(rear), 'References reused across roots'
    assert rear['C1501'].find("property[@name='dnp']") is not None, 'C1501 must remain DNP'
    expected_rear={r for r,o in checkpoint['ownership'].items() if o=='REAR'}
    assert len(expected_rear)==44 and expected_rear<=set(rear)
    assert not expected_rear&set(main)
    assert set(source)-expected_rear<=set(main)
    for ref,c in main.items():
        assert c.find("property[@name='Board']").get("value")=='MAIN', (ref,'MAIN Board field missing')
    for ref,c in rear.items():
        assert c.find("property[@name='Board']").get("value")=='REAR', (ref,'REAR Board field missing')
    # Union only actual connector-connected net nodes, not equal text between roots.
    parent={('MAIN',n):('MAIN',n) for n in mnets}|{('REAR',n):('REAR',n) for n in rnets}
    def find(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    def join(a,b):parent[find(b)]=find(a)
    continuity=[]
    for row in contract['positions']:
        p=str(row['position']);m=mpins[('J1501',row['main_pin'])];r=rpins[('J1502',row['rear_pin'])]
        assert m.split('/')[-1]==r.split('/')[-1]==row['net'],(p,m,r,row['net'])
        join(('MAIN',m),('REAR',r))
        continuity.append({'position':int(p),'net':row['net'],'main_net':m,'rear_net':r,'pass':True})
    counts=Counter(x['net'] for x in continuity)
    assert len(counts)==13 and counts['GND']==10 and counts['PPG_VLED']==3 and counts['VOUT1_1V8']==1
    assert sum(v for n,v in counts.items() if n not in ['GND','PPG_VLED','VOUT1_1V8'])==10
    groups=defaultdict(set)
    for board,nets in [('MAIN',mnets),('REAR',rnets)]:
        for net,pins in nets.items():
            groups[find((board,net))].update(p for p in pins if p[0] in source and p[0]!='J202')
    assembled={frozenset(s) for s in groups.values() if s}
    original=defaultdict(set)
    for ref,ps in source.items():
        if ref=='J202':continue  # intentional raw-to-protected charger ECO
        for pin,net in ps.items():original[net].add((ref,pin))
    expected={frozenset(s) for s in original.values() if s}
    assert assembled==expected, {'missing_original_groups':[sorted(s) for s in expected-assembled],'unexpected_groups':[sorted(s) for s in assembled-expected]}
    # Explicit detector and local shield proofs, in addition to the full partition comparison.
    detector=[]
    for d,u,p in [('D424','U12','D5'),('D414','U12','D4'),('D423','U13','D5'),('D413','U13','D4')]:
        members=rnets[rpins[(u,p)]]
        assert any(ref==d for ref,pin in members), (d,u,p)
        detector.append({'detector':d,'afe':u,'pin':p,'members':sorted(members),'pass':True})
    for nt,n in [('NT401','PPG1_PD_GND'),('NT402','PPG2_PD_GND')]:
        assert rpins[(nt,'1')].split('/')[-1]==n and rpins[(nt,'2')].split('/')[-1]=='GND'
    assert {r for r in rear if r in ['R801','R802']}==set()
    assert mpins[('J201','1')]=='GND' and mpins[('J201','2')].endswith('BAT_NTC') and mpins[('J201','3')].endswith('VBAT')
    assert mpins[('C206','1')].endswith('VBAT') and mpins[('C206','2')]=='GND'
    assert mpins[('U201','21')]==mpins[('C201','1')]==mpins[('U1201','2')]==mpins[('D1201','1')]
    assert mpins[('J202','1')]==mpins[('U1201','1')]=='CHG_RAW_5V'
    assert mpins[('U1201','1')]!=mpins[('U1201','2')], 'Protection bypassed'
    assert mpins[('J202','2')]=='GND'
    for row in charger['external_contacts']:
        assert mpins[(row['main_ref'],row['main_pin'])]==row['net']
    for p in ['7','10']:assert rpins[('U6',p)]=='GND'
    # All transferred source symbol UUIDs and pin UUIDs remain intact.
    src,_,_=load(BASE/'source_netlist.xml')
    for ref in source:
        if ref=='J202':continue
        new=(rear if ref in expected_rear else main)[ref]
        assert new.findtext('tstamps')==src[ref].findtext('tstamps'), (ref,'symbol UUID changed')
        assert new.findtext('value')==src[ref].findtext('value'),(ref,'value changed')
        assert new.findtext('footprint')==src[ref].findtext('footprint'),(ref,'footprint changed')
    # Physical PCB and MAIN project/rules/library definitions remain byte-identical.
    protected=[]
    for file,sha in checkpoint['hashes'].items():
        if file.endswith(('.kicad_pcb','.kicad_pro','.kicad_dru','.kicad_sym','.kicad_mod')) or file=='fp-lib-table':
            assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==sha, file+' protected file modified'
            protected.append(file)
    return {'status':'PASS','source_commit':checkpoint['commit'],'counts':{'MAIN':{'components':len(main),'nets':len(mnets)},'REAR':{'components':len(rear),'nets':len(rnets)},'HARNESS':{'contacts':4,'logical_nets':2,'bom_lines':len(charger['population'])}},'transferred_existing_components':44,'boundary_logical_nets':13,'continuity':continuity,'detectors':detector,'all_original_pin_partitions_preserved_except_deliberate_J202_protection_ECO':True,'all_LED_mux_VREF_PD_GND_unused_cathode_memberships_preserved':True,'source_components_checked':len(source)-1,'protected_hashes_verified':protected,'charger_protection':'provisional mandatory block, no selected IC / hardware immunity claim'}

def bom(xml_path,board):
    cs,_,_=load(xml_path)
    with (BASE/'validation'/f'{board.lower()}_bom.csv').open('w') as f:
        w=csv.writer(f, lineterminator="\n");w.writerow(['Reference','Value','Footprint','Board','DNP','SelectionStatus'])
        for ref,c in sorted(cs.items()):
            w.writerow([ref,c.findtext('value'),c.findtext('footprint'),board,c.find('property[@name="dnp"]') is not None,(c.find('property[@name="SelectionStatus"]').get("value") if c.find('property[@name="SelectionStatus"]') is not None else None) or 'BASELINE'])

if __name__=='__main__':
    assert len(sys.argv)==4, __doc__
    result=audit(sys.argv[1],sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
    for file,board in [(sys.argv[1],'MAIN'),(sys.argv[2],'REAR')]:bom(file,board)
    print(json.dumps({'status':result['status'],'counts':result['counts'],'transferred':44,'boundary_nets':13,'original_pin_partitions':'PASS'}))
