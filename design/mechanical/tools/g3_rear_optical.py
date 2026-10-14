#!/usr/bin/env python3
"""G3 placement/reservation study, never a KiCad writer. Python standard library only.

A consistency PASS is not an engineering PASS. Rejected candidate geometry is retained
in full. Only the explicit OD-G3-MAX86141-PKG exception is applied. Project pad geometry is
not manufacturer package qualification. Build writes only the four G3 generated files.
"""
import copy
import hashlib
import html
import itertools
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
MECH = ROOT / 'design/mechanical'
GEN = MECH / 'generated'
sys.path.insert(0, str(MECH / 'tools'))
import mech_model as mm
import g2_interconnect as g2

EPS = 1e-9
CORNERS = {'optimistic':'min', 'nominal':'nom', 'conservative':'max'}
EMITTERS = ['D401','D402','D403','D404','D405','D406','D407']
PDS = ['D413','D414','D423','D424']
AFES = ['U12','U13']
MUXES = ['U'+str(n) for n in range(402,408)]
REQUIRED_SKIN = set(EMITTERS+PDS+AFES+MUXES+['U6','C802','NT401','NT402'])
RES_IDS = ['LRA','FPC_UNDER','CHG_ROUTE','CHG_LINK','CHG_CONTACT','MAG_CLEAR']
CLASSES = {'MANUFACTURER_VERIFIED','PROJECT_DERIVED','PROVISIONAL_ASSUMPTION','MANUFACTURER_DATA_REQUIRED','SUPPLIER_DATA_REQUIRED','MEASUREMENT_REQUIRED','OWNER_DECISION'}

def load(p): return g2.load(p)
def dumps(o): return g2.dumps(o)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical_hash(o): return hashlib.sha256(dumps(o).encode()).hexdigest()
def add(a,b): return [a[0]+b[0],a[1]+b[1]]
def sub(a,b): return [a[0]-b[0],a[1]-b[1]]
def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def manhattan(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
def area(poly): return abs(sum(cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1]))/2) if len(poly)>2 else 0.
def union_area(polys):
    """Exact piecewise-linear strip integration of polygon unions (no raster grid)."""
    edges=[(a,b) for poly in polys for a,b in zip(poly,poly[1:]+poly[:1])]
    cuts={p[0] for poly in polys for p in poly}
    for (a,b),(c,d) in itertools.combinations(edges,2):
        v,w=sub(b,a),sub(d,c);den=cross(v,w)
        if abs(den)<EPS:continue
        t=cross(sub(c,a),w)/den;u=cross(sub(c,a),v)/den
        if 0<t<1 and 0<u<1:cuts.add(a[0]+t*v[0])
    xs=sorted(cuts);total=0.
    for x0,x1 in zip(xs,xs[1:]):
        x=(x0+x1)/2;intervals=[]
        for poly in polys:
            ys=[a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(poly,poly[1:]+poly[:1]) if min(a[0],b[0])<x<max(a[0],b[0])]
            if ys:intervals.append((min(ys),max(ys)))
        end=-math.inf;span=0.
        for lo,hi in sorted(intervals):span+=max(0,hi-max(lo,end));end=max(end,hi)
        total+=(x1-x0)*span
    return total
def ccw(poly):
    return poly if sum(cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1]))>=0 else list(reversed(poly))
def hull(points):
    ps=sorted(set(tuple(p) for p in points))
    if len(ps)<3:return [list(p) for p in ps]
    def half(seq):
        h=[]
        for p in seq:
            while len(h)>1 and cross(sub(h[-1],h[-2]),sub(p,h[-1]))<=EPS:h.pop()
            h.append(p)
        return h
    return [list(p) for p in half(ps)[:-1]+half(ps[::-1])[:-1]]
def rect(x0,y0,x1,y1):return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
def box(points):return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def grow(poly,d):return hull([[x+dx,y+dy] for x,y in poly for dx,dy in [(-d,-d),(-d,d),(d,-d),(d,d)]])
def inside(p,poly):return len(poly)>=3 and all(cross(sub(b,a),sub(p,a))>=-EPS for a,b in zip(ccw(poly),ccw(poly)[1:]+ccw(poly)[:1]))
def clip(poly,other):
    if len(poly)<3 or len(other)<3:return []
    out=ccw(poly)
    for a,b in zip(ccw(other),ccw(other)[1:]+ccw(other)[:1]):
        old,out=out,[]
        if not old:break
        for s,e in zip(old[-1:]+old[:-1],old):
            ds=cross(sub(b,a),sub(s,a));de=cross(sub(b,a),sub(e,a))
            if (ds>=-EPS)!=(de>=-EPS):
                t=ds/(ds-de);out.append([s[0]+t*(e[0]-s[0]),s[1]+t*(e[1]-s[1])])
            if de>=-EPS:out.append(e)
    return out

def overlap(a,b):return area(clip(a,b))>EPS

def point_seg(p,a,b):
    v=sub(b,a);v2=v[0]**2+v[1]**2
    t=max(0,min(1,sum(x*y for x,y in zip(sub(p,a),v))/v2)) if v2 else 0
    return dist(p,[a[0]+t*v[0],a[1]+t*v[1]])
def gap(a,b):
    if overlap(a,b) or any(inside(p,b) for p in a) or any(inside(p,a) for p in b):return 0.
    return min([point_seg(p,s,e) for p in a for s,e in zip(b,b[1:]+b[:1])]+[point_seg(p,s,e) for p in b for s,e in zip(a,a[1:]+a[:1])])
def polygon_pieces(poly):
    """Even-odd filled ordered polygon, decomposed exactly into convex trapezoids.

    Cuts include every vertex and proper edge intersection, so concave and
    self-crossing waypoint loops never acquire the extra area of their hull.
    """
    edges=[(a,b) for a,b in zip(poly,poly[1:]+poly[:1]) if dist(a,b)>EPS]
    cuts={p[0] for p in poly}
    for (a,b),(c,d) in itertools.combinations(edges,2):
        v,w=sub(b,a),sub(d,c);den=cross(v,w)
        if abs(den)<EPS:continue
        t=cross(sub(c,a),w)/den;u=cross(sub(c,a),v)/den
        if EPS<t<1-EPS and EPS<u<1-EPS:cuts.add(a[0]+t*v[0])
    pieces=[];xs=sorted(cuts)
    for x0,x1 in zip(xs,xs[1:]):
        if x1-x0<EPS:continue
        xm=(x0+x1)/2
        active=[(a,b) for a,b in edges if min(a[0],b[0])<xm<max(a[0],b[0])]
        def y(edge,x):
            a,b=edge;return a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0])
        active.sort(key=lambda e:y(e,xm))
        assert len(active)%2==0
        for lo,hi in zip(active[::2],active[1::2]):
            q=hull([[x0,y(lo,x0)],[x1,y(lo,x1)],[x1,y(hi,x1)],[x0,y(hi,x0)]])
            if area(q)>EPS:pieces.append(q)
    return pieces

def outside_court(poly,court):
    """Disjoint convex pieces outside an orthogonal package courtyard."""
    x0,y0,x1,y1=box(court);px0,py0,px1,py1=box(poly)
    bounds=[rect(px0-1,py0-1,x0,py1+1),rect(x1,py0-1,px1+1,py1+1),
            rect(x0,py0-1,x1,y0),rect(x0,y1,x1,py1+1)]
    # Empty/reversed rectangles must not turn into unintended clipping regions.
    return [q for b in bounds if b[2][0]>b[0][0]+EPS and b[2][1]>b[0][1]+EPS
            for q in [clip(poly,b)] if area(q)>EPS]

def clearance(regions,shields,court=None):
    """Edge-to-edge reservation/copper gap; exemption only for same AFE package.

    Both regions retain their complete physical extents outside the owning
    courtyard. Foreign-package comparisons are never clipped. Terminal escape
    to a fixed ball is package-local; all board-level copper remains checked.
    """
    if court is None:return min(gap(p,q) for p in regions for q in shields)
    outer_p=[r for p in regions for r in outside_court(p,court)]
    outer_q=[r for q in shields for r in outside_court(q,court)]
    values=[gap(p,q) for p in outer_p for q in outer_q]
    return min(values,default=1e6)

def rotate(p,angle):
    t=math.radians(angle);c,s=math.cos(t),math.sin(t)
    return [p[0]*c+p[1]*s,-p[0]*s+p[1]*c]
def world(p,placement):return add(placement['xy'],rotate(p,placement['rotation_deg']))
def assembly(p):return [100-p[0],100+p[1]]
def rear(p):return [100-p[0],p[1]-100]
def framed(poly):return dict(rear_mm=poly,assembly_mm=[assembly(p) for p in poly])
def polar(r,az):return [-r*math.sin(math.radians(az)),-r*math.cos(math.radians(az))]
def azimuth(p):return math.degrees(math.atan2(-p[0],-p[1]))%360

def corridor(points,width):
    return [grow(hull([a,b]),width/2) for a,b in zip(points,points[1:]) if dist(a,b)>EPS]
def length(points):return sum(dist(a,b) for a,b in zip(points,points[1:]))
def path_valid(path,limit):return path['vias']==0 and path['length_mm']<=limit+EPS and not path['non_pd_pad_intrusions']
def frame_valid(placement):return max(abs(a-b) for a,b in zip(placement['assembly_xy_mm'],assembly(placement['xy'])))<.002
def polyline(a,b,vertical_first=False):
    return [a,[a[0],b[1]] if vertical_first else [b[0],a[1]],b]
def rmax(poly,az):
    d=polar(1,az);hits=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        v=sub(b,a);den=cross(d,v)
        if abs(den)<EPS:continue
        t=cross(a,v)/den;u=cross(a,d)/den
        if t>=0 and -EPS<=u<=1+EPS:hits.append(t)
    return max(hits) if hits else 0.

def reservation_pieces(g,step):
    """Inscribed convex pieces for area reporting. Hard radius/sector fits are analytic.
    Maximum chord sagitta is reported with every reservation, never hidden as exact area.
    """
    if g['type']=='rect':return [ccw([rear(p) for p in rect(*g['rect'])])]
    if g['type']=='circles':
        return [hull([rear([x+r*math.cos(math.radians(a)),y+r*math.sin(math.radians(a))]) for a in range(0,360)]) for x,y,r in g['circles']]
    a0,a1=g['az'];r0,r1=g['r'];n=math.ceil((a1-a0)/step)
    return [hull([polar(r,a0+(a1-a0)*k/n) for r,k in [(r0,i),(r1,i),(r1,i+1),(r0,i+1)]]) for i in range(n)]

class Study:
    def __init__(self):
        self.I=load(MECH/'inputs/g3_rear_optical.json');self.A=load(MECH/'architecture.json')
        assert self.I['search']['entry_vertical_first']==[False,True], 'Both orthogonal entry orientations required'
        self.P=self.I['parameters'];self.L=self.I['limits'];self.S=load(MECH/'inputs/stack_parameters.json')
        self.H=load(MECH/'inputs/package_heights.json');self.G2=load(GEN/'g2_interconnect.json')
        self.g2=g2.Study()
        for path,want in self.I['source_sha256'].items():
            assert sha(ROOT/path)==want,'Source-hash mismatch: '+path
        self.arch_input={k:self.A[k] for k in ['reservations','rear_module']}
        self.arch_input['g2_reservations']=self.A['g2']['reservations']
        pin=self.I['architecture_projection_sha256']
        assert canonical_hash(self.arch_input)==pin,'Architecture input projection hash mismatch'
        self.nets={};self.pin_net={};self.components={}
        root=ET.parse(ROOT/'design/interfaces/validation/rear_netlist.xml')
        for c in root.findall('.//components/comp'):
            self.components[c.get('ref')]={'value':c.findtext('value'),'footprint':c.findtext('footprint')}
        for n in root.findall('.//nets/net'):
            nodes=[(p.get('ref'),p.get('pin')) for p in n.findall('node')];self.nets[n.get('name')]=nodes
            for p in nodes:self.pin_net[p]=n.get('name')
        assert len(self.components)==46
        board=mm.parse_sexpr((ROOT/'rear_sensor/rear_sensor_revA.kicad_pcb').read_text())
        self.fp={};self.footprint_sources={}
        for fp in mm.children(board,'footprint'):
            ref=next(p[2] for p in mm.children(fp,'property') if p[1]=='Reference')
            lib=fp[1]; original=ROOT/('libraries/footprints/sportwatch_custom.pretty/'+lib.split(':')[-1]+'.kicad_mod')
            source=mm.parse_sexpr(original.read_text()) if original.exists() else fp
            # Installed system .kicad_mod absent: immutable embedded library snapshot is authoritative.
            pts=mm.courtyard_points(source);bounds=box(pts)
            pads=[]
            for p in mm.children(source,'pad'):
                xy=list(map(float,mm.child(p,'at')[1:3]));size=list(map(float,mm.child(p,'size')[1:3]))
                pads.append(dict(pin=p[1],xy=xy,size_mm=size))
            assert pads and pts,ref
            self.fp[ref]=dict(court=rect(*bounds),pads=pads,footprint=lib)
            self.footprint_sources[ref]=str(original.relative_to(ROOT)) if original.exists() else 'rear_sensor/rear_sensor_revA.kicad_pcb#'+ref
            assert self.components[ref]['footprint']==lib
        assert set(self.fp)==set(self.components)-{'C1501','J1502'}
        self.res={r['id']:r for r in self.A['reservations'] if r['id'] in RES_IDS}
        self.respieces={rid:reservation_pieces(r['geometry'],self.I['search']['reservation_arc_step_deg']) for rid,r in self.res.items()}
        self.channels,self.detectors=self.channel_map()

    def value(self,name,corner='nominal'):return self.P[name][CORNERS[corner]]
    def court(self,ref,pl):return hull([world(p,pl[ref]) for p in self.fp[ref]['court']])
    def pad(self,ref,pin,pl):
        ps=[world(p['xy'],pl[ref]) for p in self.fp[ref]['pads'] if p['pin']==pin]
        assert ps,(ref,pin)
        return [sum(p[i] for p in ps)/len(ps) for i in [0,1]]
    def pad_polys(self,ref,pl):
        return [(p['pin'],hull([world(q,pl[ref]) for q in rect(p['xy'][0]-p['size_mm'][0]/2,p['xy'][1]-p['size_mm'][1]/2,p['xy'][0]+p['size_mm'][0]/2,p['xy'][1]+p['size_mm'][1]/2)])) for p in self.fp[ref]['pads']]

    def channel_map(self):
        channels=[];detectors=[]
        for afe,prefix in zip(AFES,['C410','C420']):
            assert self.pin_net[(afe,'C2')]==self.pin_net[(afe,'D2')]=='VOUT1_1V8'
            for suffix,value,net in [('1','22uF','VOUT1_1V8'),('2','100nF','VOUT1_1V8'),('3','1.0uF',self.pin_net[(afe,'B5')]),('4','10uF','PPG_VLED')]:
                ref=prefix+suffix
                assert self.components[ref]['value']==value and self.pin_net[(ref,'1')]==net and self.pin_net[(ref,'2')]=='GND'
        for net,nodes in sorted(self.nets.items()):
            m=re.search(r'PPG([12])_LED([1-6])_(GREEN|RED|IR850|IR940)_K$',net)
            if m:
                group,led,color=m.groups();emitters=sorted({r for r,p in nodes if r in EMITTERS});muxes=sorted({r for r,p in nodes if r in MUXES})
                assert len(emitters)==len(muxes)==1
                e,mux=emitters[0],muxes[0];driver_net=self.pin_net[(mux,'B2')]
                driver=next((r,p) for r,p in self.nets[driver_net] if r in AFES)
                assert driver[0]==('U12' if group=='1' else 'U13')
                wavelength={'GREEN':536,'RED':660,'IR850':850,'IR940':940}[color]
                channels.append(dict(afe=driver[0],led=int(led),site='A' if int(led)<=3 else 'B',wavelength_nm=wavelength,emitter=e,cathode_pins=[p for r,p in nodes if r==e],anode_pins=['1'] if e in ['D405','D406','D407'] else ['6'] if color=='GREEN' else ['2','4'],mux=mux,mux_input=next(p for r,p in nodes if r==mux),driver_pin=driver[1],net=net,driver_net=driver_net,evidence_class='PROJECT_DERIVED'))
            m=re.search(r'PPG([12])_PD([12])_IN$',net)
            if m:
                pd=next((r,p) for r,p in nodes if r in PDS);afe=next((r,p) for r,p in nodes if r in AFES)
                detectors.append(dict(pd=pd[0],pd_pin=pd[1],afe=afe[0],afe_pin=afe[1],channel=int(m[2]),net=net,evidence_class='PROJECT_DERIVED'))
        assert len(channels)==12 and len(detectors)==4
        grouping=self.A['rear_module']['optical_grouping']
        for gi,afe in enumerate(AFES,1):
            group=grouping[f'AFE{gi}_{afe}']
            expected=[]
            for text in group['emitters']:
                ref=text.split()[0]
                for color,num in re.findall(r'(green|red|IR850|IR940) LED([1-6])',text):expected.append((ref,int(num),{'green':536,'red':660,'IR850':850,'IR940':940}[color]))
            assert sorted(expected)==sorted((c['emitter'],c['led'],c['wavelength_nm']) for c in channels if c['afe']==afe)
            assert sorted(group['mux'])==sorted({c['mux'] for c in channels if c['afe']==afe})
            assert sorted((x.split()[0],int(re.search(r'PD([12])',x)[1])) for x in group['detectors'])==sorted((d['pd'],d['channel']) for d in detectors if d['afe']==afe)
        reg=load(MECH/'inputs/input_register.json');pdmap=next(x['value'] for x in reg['entries'] if x['id']=='REAR-PD-MAP')
        assert sorted(re.findall(r'(D\d+)->(U\d+) PD([12])',pdmap))==sorted((d['pd'],d['afe'],str(d['channel'])) for d in detectors)
        assert next(c for c in channels if c['afe']=='U13' and c['led']==6)['emitter']=='D402'
        for ref in ['D401','D403','D404']:
            ns=self.nets.get(self.pin_net.get((ref,'3')),[])
            assert ns==[] or ns==[(ref,'3')],(ref,ns)
        iface=load(ROOT/'design/interfaces/main_rear_interface.json');assert len(iface['positions'])==24
        boundary={p['net'] for p in iface['positions']};assert len(boundary)==13
        for p in iface['positions']:assert self.pin_net[('J1502',str(p['position']))]==p['net']
        assert not any(any(token in n for token in ['PD1_IN','PD2_IN','PD_GND','VREF','_K','MUX_SEL','_DRV']) for n in boundary)
        return channels,detectors

    def res_metrics(self,poly):
        out={}
        for rid,pieces in self.respieces.items():
            out[rid]=dict(overlap_area_mm2=sum(area(clip(poly,p)) for p in pieces),plan_gap_mm=min(gap(poly,p) for p in pieces),area_method='inscribed arc tessellation; radial containment and tail-sector tests analytic',chord_sagitta_max_mm=.001)
        return out

    def tail_study(self,outline,occupied):
        band=self.res['FPC_UNDER']['geometry']['az'];half=math.radians((band[1]-band[0])/2)
        p=self.g2.P['sensor_pitch_mm'];m=self.g2.P['sensor_edge_margin_mm'];rows=[]
        attach=self.g2.rear_geometry(self.g2.options['J1502-TAIL0402'])['corners']
        for kind,r,az in itertools.product(self.I['search']['tail_arrangements'],self.I['search']['tail_centres_r_mm'],self.I['search']['tail_azimuth_deg']):
            corners={};polys={}
            for corner,k in CORNERS.items():
                width=23*p[k]+2*m[k];rows_n=2 if kind=='two_row' else 1
                land_width=(12-1)*p[k]+2*m[k] if rows_n==2 else width
                depth=self.value('land_depth_mm',corner)+(self.value('row_spacing_mm',corner) if rows_n==2 else 0)
                # Local X tangential, Y radial at azimuth; radial arrangement rotates the land by 90°.
                shape=rect(-land_width/2,-depth/2,land_width/2,depth/2)
                pl=dict(xy=polar(r,az),rotation_deg=az+(90 if kind=='radial' else 0))
                poly=hull([world(q,pl) for q in shape]);polys[corner]=poly
                sector_fit=all(band[0]-EPS<=azimuth(q)<=band[1]+EPS for q in poly)
                edgefit=all(inside(q,outline) for q in grow(poly,self.L['thermode_mm']))
                ar=attach[corner]['radial_attach_window_mm'];rr=[min(math.hypot(*q) for q in poly),max(math.hypot(*q) for q in poly)]
                collisions=[ref for ref,court in occupied.items() if overlap(grow(poly,self.L['thermode_mm']),court)]
                corners[corner]=dict(single_row_tail_width_mm=width,land_width_mm=land_width,land_depth_mm=depth,rows=rows_n,pitch_mm=p[k],edge_margin_mm=m[k],band_arc_width_mm=r*2*half,band_chord_width_mm=2*r*math.sin(half),sector_fit=sector_fit,outline_and_thermode_fit=edgefit,inner_thermode_intrusions=collisions,radial_extent_mm=rr,g2_radial_attach_window_mm=ar,inside_g2_attach_window=rr[0]>=ar[0]-EPS and rr[1]<=ar[1]+EPS,geometry=framed(poly))
                relief=self.value('strain_relief_mm',corner)
                radial_land_span=land_width if kind=='radial' else depth
                exit_r=r+radial_land_span/2
                strain_pose=dict(xy=polar(exit_r+relief/2,az),rotation_deg=az)
                strain_poly=hull([world(q,strain_pose) for q in rect(-land_width/2,-relief/2,land_width/2,relief/2)])
                strain_fit=all(band[0]-EPS<=azimuth(q)<=band[1]+EPS for q in strain_poly)
                corners[corner].update(strain_relief=framed(strain_poly),strain_relief_sector_fit=strain_fit,exit_radius_mm=exit_r,exit_width_mm=land_width,full_single_row_width_min_centred_radius_mm=width/(2*math.sin(half)))
            nom=corners['nominal'];passed=nom['sector_fit'] and nom['outline_and_thermode_fit'] and nom['strain_relief_sector_fit'] and not nom['inner_thermode_intrusions']
            rows.append(dict(id=f'{kind}-r{r:g}-a{az:g}',arrangement=kind,centre_rear_mm=polar(r,az),centre_assembly_mm=assembly(polar(r,az)),corners=corners,nominal_fit=passed,thermode_keepout=framed(grow(polys['nominal'],self.L['thermode_mm'])),supplier_confirmed=False,rank=[not passed,not nom['inside_g2_attach_window'],nom['rows'],nom['land_width_mm'],abs(r-10.6),abs(az-sum(band)/2)],evidence_class='PROJECT_DERIVED'))
        feasible=[x for x in rows if x['nominal_fit']]
        selected=min(feasible,key=lambda x:(x['rank'],x['id'])) if feasible else None
        if selected:
            selected=copy.deepcopy(selected)
            poly=selected['corners']['nominal']['geometry']['rear_mm'];c=selected['centre_rear_mm'];az=azimuth(c)
            exit_c=polar(math.hypot(*c)+selected['corners']['nominal']['land_depth_mm']/2+self.value('strain_relief_mm')/2,az)
            selected['strain_relief']=selected['corners']['nominal']['strain_relief']
            selected['disposition']='Local land reservation alternative permitted by §6.4.2; no G2 input/corridor change. Two-row tail fanout and its continued under-run width require supplier drawing; not qualified.'
        return dict(alternatives=rows,selected=selected,all_arrangements_evaluated=True,under_run_geometry=self.res['FPC_UNDER']['geometry'],joint_range_g2_mm=self.g2.P['tail_joint_mm'],g3_joint_closure_max_mm=self.I['contract_values']['g3_joint_closure_max_mm'],evidence_class='PROJECT_DERIVED')

    def thermal(self,pl,courts,tail,outline,entry_regions):
        options=[]
        for r,az in itertools.product(self.I['search']['thermal_radii_mm'],self.I['search']['thermal_azimuth_deg']):
            pose=dict(xy=polar(r,az),rotation_deg=0,face='skin',evidence_class='PROVISIONAL_ASSUMPTION')
            pp=dict(pl,U6=pose);court=self.court('U6',pp)
            pp['C802']=dict(xy=add(pose['xy'],self.I['search']['c802_offset_mm']),rotation_deg=0,face='skin',evidence_class='PROVISIONAL_ASSUMPTION')
            cap=self.court('C802',pp);island=grow(hull(court+cap),self.value('slot_width_mm'))
            perimeter=sum(dist(a,b) for a,b in zip(island,island[1:]+island[:1]));fraction=1-self.value('neck_width_mm')/perimeter
            emitter_gap=min(gap(court,courts[e]) for e in EMITTERS)
            other_gap=min(gap(court,courts[e]) for e in AFES+MUXES+['C1501'])
            if entry_regions:other_gap=min(other_gap,min(gap(court,p) for p in entry_regions))
            tail_gap=gap(court,tail) if tail else 0
            chargers={rid:min(gap(court,p) for p in self.respieces[rid]) for rid in ['CHG_ROUTE','CHG_LINK','CHG_CONTACT']}
            nearest=min(chargers.values());contained=all(inside(q,outline) for q in grow(island,self.value('edge_mm')))
            nonoverlap=not any(overlap(island,v) for k,v in courts.items() if pl[k]['face']=='skin')
            hard=emitter_gap>=self.L['thermal_emitter_mm'] and min(other_gap,tail_gap)>=self.L['thermal_other_mm'] and nearest>=self.L['thermal_charger_mm'] and fraction>=self.L['isolation_fraction'] and contained and nonoverlap
            options.append(dict(azimuth_deg=az,radius_mm=r,placement=pose,c802_placement=pp['C802'],island=framed(island),isolated_perimeter_fraction=fraction,slot_width_mm=self.value('slot_width_mm'),neck_width_mm=self.value('neck_width_mm'),emitter_gap_mm=emitter_gap,afe_mux_entry_gap_mm=other_gap,tail_gap_mm=tail_gap,charger_plan_gaps_mm=chargers,charger_3d_distance_lower_bounds_mm=chargers,three_d_basis='Z ranges not supplier-qualified: minimum vertical separation 0; Euclidean lower bound equals plan gap. No invented corridor height.',nominal_pass=hard,isolation_fraction_corners={cn:1-self.value('neck_width_mm',cn)/perimeter for cn in CORNERS},contained=contained,nonoverlap=nonoverlap,rank=[not hard,-min(emitter_gap,other_gap,tail_gap,nearest),-fraction,area(island),az]))
        chosen=min(options,key=lambda x:x['rank'])
        island=chosen['island']['rear_mm'];edges=list(zip(island,island[1:]+island[:1]));neck_edge=min(range(len(edges)),key=lambda i:dist([(edges[i][0][j]+edges[i][1][j])/2 for j in [0,1]],[0,0]))
        segments=[]
        for i,(a,b) in enumerate(edges):
            if i!=neck_edge:segments.append([a,b]);continue
            edge_length=dist(a,b);f=(edge_length-self.value('neck_width_mm'))/(2*edge_length)
            n0=[a[j]+f*(b[j]-a[j]) for j in [0,1]];n1=[b[j]-f*(b[j]-a[j]) for j in [0,1]]
            segments.extend([[a,n0],[n1,b]]);chosen['neck_segment']=framed([n0,n1])
        chosen['slot_centrelines']=[framed(x) for x in segments]
        chosen['contact_feature_reservation']=dict(package_top_centre_rear_mm=chosen['placement']['xy'],package_top_centre_assembly_mm=assembly(chosen['placement']['xy']),package_top_to_skin_nominal_mm=self.S['parameters']['h_optics_max']['nom']+self.S['parameters']['c_optics']['nom']+self.S['parameters']['t_window']['nom']-self.I['manufacturer_facts']['MAX30208']['height_max_mm'],F1='Package-top thermal contact within reserved island; conductivity/compression qualified by MG-THERMAL',F2='Local insert/window over island; seal land follows SR-WINDOW range',F3='Opaque insulated skin-contact feature over island; sealing retained as G4 handoff')
        u6nets=sorted({n for (ref,p),n in self.pin_net.items() if ref=='U6'})
        return dict(selected=chosen,alternatives=options,traces_across_neck=len(u6nets),trace_nets=u6nets,skin_contact_options=[dict(id='F1',concept='Direct package-top compliant thermal contact to dedicated opaque contact feature',compatible_windows=['W0','W1','W2']),dict(id='F2',concept='Local thin window/contact insert over U6; thermal impedance qualification required',compatible_windows=['W0','W1','W2']),dict(id='F3',concept='Separate electrically insulated skin-contact stud; G4 sealing and spreading design required',compatible_windows=['W0','W1','W2'])],accuracy='MEASUREMENT_REQUIRED; owner target not supplied',evidence_class='PROJECT_DERIVED')

    def guarded(self,pl,courts,tail,candidate,corner):
        w=self.value('guard_trace_mm',corner)+2*(self.value('guard_space_mm',corner)+self.value('guard_copper_mm',corner))
        paths=[];shields={a:[] for a in AFES};blocked=[]
        for d in self.detectors:
            start=self.pad(d['afe'],d['afe_pin'],pl);end=self.pad(d['pd'],d['pd_pin'],pl)
            permitted={d['net'],self.pin_net[(d['afe'],'C5')]}
            obstacles=[]
            for ref in self.fp:
                if pl[ref]['face']!='skin' or ref not in courts:continue
                for pin,poly in self.pad_polys(ref,pl):
                    if self.pin_net.get((ref,pin)) not in permitted:obstacles.append((ref+'.'+pin,poly))
            alts=[]
            for orient in [False,True]:
                line=polyline(start,end,orient);regions=corridor(line,w)
                conflicts=sorted({name for name,poly in obstacles if any(overlap(poly,s) for s in regions)})
                alts.append((len(conflicts),length(line),orient,line,regions,conflicts))
            best=min(alts,key=lambda x:x[:3]);n,l,_,line,regions,conflicts=best
            shields[d['afe']]+=regions+[grow(courts[d['pd']],self.value('guard_copper_mm',corner))]
            paths.append(dict(**d,minimum_foreign_pad_gap_mm=min(gap(reg,poly) for reg in regions for name,poly in obstacles),points=framed(line),length_mm=l,manhattan_lower_bound_mm=manhattan(start,end),vias=candidate['pd_vias'],corridor_width_mm=w,corridors=[framed(p) for p in regions],non_pd_pad_intrusions=conflicts,path_pass=l<=self.L['pd_path_mm']+EPS and candidate['pd_vias']==0 and not conflicts,capacitance=dict(evidence_class='MANUFACTURER_DATA_REQUIRED',c_pd_zero_v_pf=None,corridor_budget_pf=l*self.value('corridor_pf_per_mm',corner),c_pd_zero_v_max_for_pdbias_0x1_pf=self.I['manufacturer_facts']['MAX86141']['pdbias_limits_pf'][0]-l*self.value('corridor_pf_per_mm',corner),formula='C_PD(0 V) + length*C_per_mm <= 65 pF; 9 pF at 5 V is not substituted')))
        # Ties are the only netlist connection from PD_GND to PCB GND.
        ties=[]
        for afe,tie in zip(AFES,['NT401','NT402']):
            nodes=self.nets[self.pin_net[(afe,'C5')]]
            tie_members=[r for r,p in nodes if r.startswith('NT')]
            single=tie_members==[tie] and self.pin_net[(tie,'2')]=='GND'
            dd=dist(self.pad(tie,'1',pl),self.pad(afe,'C5',pl))
            ties.append(dict(afe=afe,tie=tie,distance_mm=dd,limit_mm=self.L['nt_mm'],single_point_netlist=single,same_face=pl[tie]['face']==pl[afe]['face'],pass_check=single and dd<=self.L['nt_mm']+EPS and pl[tie]['face']=='skin'))
            shields[afe]+=corridor(polyline(self.pad(afe,'C5',pl),self.pad(afe,'D5',pl)),self.value('guard_copper_mm',corner))
            shields[afe]+=corridor(polyline(self.pad(afe,'C5',pl),self.pad(tie,'1',pl)),self.value('guard_copper_mm',corner))
        locality=[]
        for ai,afe in enumerate(AFES):
            prefix='C410' if ai==0 else 'C420'
            for suffix,ball,lim in [('1','C2','vdd_bulk_mm'),('2','D2','vdd_small_mm'),('3','B5','vref_mm'),('4','A1','vled_afe_mm')]:
                ref=prefix+suffix;dd=dist(self.pad(ref,'1',pl),self.pad(afe,ball,pl))
                locality.append(dict(ref=ref,target=afe+'.'+ball,distance_mm=dd,limit_mm=self.L[lim],signal_vias=int(pl[ref]['face']=='inner'),ground_via_id=ref+'-GND',individual_ground_via=True,pass_check=dd<=self.L[lim]+EPS))
        for mux,cap in zip(MUXES,['C'+str(n) for n in range(403,409)]):
            dd=dist(self.pad(cap,'1',pl),self.pad(mux,'C2',pl))
            locality.append(dict(ref=cap,target=mux+'.C2',distance_mm=dd,limit_mm=self.L['vled_mux_mm'],signal_vias=int(pl[cap]['face']=='inner'),ground_via_id=cap+'-GND',individual_ground_via=True,pass_check=dd<=self.L['vled_mux_mm']+EPS))
        # Resistor nets have no numeric §6.3.4 limit: report both geometric distance and no shield intrusion.
        for ref in sorted(r for r in pl if r.startswith('R')):
            nets={self.pin_net.get((ref,p['pin'])) for p in self.fp[ref]['pads']}
            afes=sorted({r for n in nets for r,p in self.nets.get(n,[]) if r in AFES})
            conflict=any(overlap(courts[ref],s) for regs in shields.values() for s in regs)
            locality.append(dict(ref=ref,targets=afes,nearest_afe_centre_mm=min(dist(pl[ref]['xy'],pl[a]['xy']) for a in afes),signal_vias=1,limit_mm=None,limit_basis='Brief supplies no pull-up distance limit; projected exclusion is mandatory.',pass_check=not conflict))
        ground_vias=[]
        for item in locality:
            if not item.get('individual_ground_via'):continue
            xy=self.pad(item['ref'],'2',pl)
            intrusions=[afe for afe,regions in shields.items() if any(inside(xy,p) for p in regions)]
            ground_vias.append(dict(id=item['ground_via_id'],rear_xy_mm=xy,assembly_xy_mm=assembly(xy),shield_intrusions=intrusions,evidence_class='PROVISIONAL_ASSUMPTION',requirement='Dedicated GND transition reserved at capacitor ground pad; supplier via-in-pad/assembly feasibility unqualified'))
        via_unique=len({tuple(v['rear_xy_mm']) for v in ground_vias})==len(ground_vias)
        connected={}
        for afe,regions in shields.items():
            reached={0}
            while True:
                new={i for i,p in enumerate(regions) if any(gap(p,regions[j])<EPS for j in reached)}
                if new<=reached:break
                reached|=new
            connected[afe]=len(reached)==len(regions)
        for path in paths:path['path_pass']=path_valid(path,self.L['pd_path_mm'])
        loops=[];aggressors=[];trace=self.value('guard_trace_mm',corner)
        for ch in self.channels:
            cap='C'+str(403+MUXES.index(ch['mux']));afe=ch['afe'];e=ch['emitter']
            nodes=[(cap,'1'),(e,ch['anode_pins'][0]),(e,ch['cathode_pins'][0]),
                   (ch['mux'],ch['mux_input']),(ch['mux'],'B2'),(afe,ch['driver_pin']),(afe,'D3'),(cap,'2')]
            points=[self.pad(r,p,pl) for r,p in nodes]
            poly=points;pieces=polygon_pieces(poly)
            # Ordered filled polygon is the hard no-intersection reservation.
            # Spacing also includes finite trace width and every participating pad.
            copper=pieces+corridor(points+points[:1],trace)
            pad_nodes=nodes+[(e,p) for p in ch['anode_pins'][1:]+ch['cathode_pins'][1:]]
            copper += [q for r,p in pad_nodes for pin,q in self.pad_polys(r,pl) if pin==p]
            # Multi-pad common anodes retain every physical pad extent and branch.
            branches=[q for pins in [ch['anode_pins'],ch['cathode_pins']] for pin in pins[1:]
                      for q in corridor([self.pad(e,pins[0],pl),self.pad(e,pin,pl)],trace)]
            copper += branches
            discretionary=[q for (ra,pa),(rb,pb) in zip(nodes,nodes[1:]+nodes[:1]) if ra!=afe and rb!=afe
                           for q in corridor([self.pad(ra,pa,pl),self.pad(rb,pb,pl)],trace)]
            discretionary += branches+[q for r,p in pad_nodes if r!=afe for pin,q in self.pad_polys(r,pl) if pin==p]
            gaps={a:min(clearance(copper,ss,courts[afe] if a==afe else None),clearance(discretionary,ss)) for a,ss in shields.items()}
            hits=[a for a,ss in shields.items() if clearance(pieces,ss,courts[afe] if a==afe else None)<EPS]
            mingap=min(gaps.values())
            loops.append(dict(afe=afe,led=ch['led'],emitter=e,mux=ch['mux'],waypoints=framed(points),polygon=framed(poly),
                pieces=[framed(p) for p in pieces],area_mm2=sum(area(p) for p in pieces),
                shield_intersections=hits,shield_gap_mm=mingap,shield_gaps_mm=gaps,spacing_metric='edge-to-edge',
                ordered_polygon_gap_mm=min(clearance(pieces,ss,courts[afe] if a==afe else None) for a,ss in shields.items()),
                passes_no_intersection=not hits,passes_aggressor_gap=mingap>=self.L['aggressor_mm']-EPS,
                polygon_policy='Ordered cap/anode/cathode/mux/driver/PGND/cap, even-odd fill; copper includes pad bounding extents and trace half-width. Same-package exemption ends at courtyard.',
                convex_hull_diagnostic=dict(area_mm2=area(hull(points)),shield_gap_mm=min(clearance([hull(points)],ss,courts[afe] if a==afe else None) for a,ss in shields.items()),hard_acceptance=False),
                mag_clear_overlap_mm2=union_area([clip(q,p) for q in pieces for p in self.respieces['MAG_CLEAR']])))
            aggressors.append((f'{afe}-LED{ch["led"]}',copper,afe))
            aggressors.append((f'{afe}-LED{ch["led"]}-discretionary',discretionary,None))
        digital=[];vled=[]
        if tail:
            entry=[sum(p[i] for p in tail)/len(tail) for i in [0,1]]
            for afe in AFES:
                for ball in ['A2','A3','A4','A5','B2','B3','A1']:
                    alts=self.entry_options(entry,afe,ball,pl,courts,shields,corner)
                    chosen=min(alts,key=lambda x:x['rank'])
                    item=dict(target=afe+'.'+ball,alternatives=alts,selected_orientation=chosen['orientation'],
                              path=chosen['path'],gap_mm=chosen['gap_mm'],spacing_metric='edge-to-edge',pass_check=chosen['pass_check'])
                    (vled if ball=='A1' else digital).append(item)
                    name=afe+'-VLED-entry' if ball=='A1' else afe+'.'+ball
                    aggressors.append((name,[p['rear_mm'] for p in chosen['regions']],afe))
            aggressors.append(('J1502',[tail],None))
        for ref in ['C1501','C4104','C4204']+['C'+str(n) for n in range(403,409)]:
            aggressors.append((ref,[courts[ref]],None))
        exclusion=[];all_gaps=[]
        for name,polys,package in aggressors:
            for afe,ss in shields.items():
                gg=clearance(polys,ss,courts[afe] if package==afe else None);all_gaps.append(gg)
                if gg<self.L['aggressor_mm']-EPS:exclusion.append(dict(aggressor=name,shield=afe,gap_mm=gg,required_mm=self.L['aggressor_mm'],spacing_metric='edge-to-edge'))
        vref_variants=[]
        for afe,ref in zip(AFES,['C4103','C4203']):
            alt=copy.deepcopy(pl);alt[ref]=dict(xy=pl[afe]['xy'],rotation_deg=pl[afe]['rotation_deg'],face='inner',evidence_class='PROVISIONAL_ASSUMPTION')
            poly=self.court(ref,alt);dd=dist(self.pad(ref,'1',alt),self.pad(afe,'B5',alt));projection=grow(courts[afe],self.L['vref_projection_mm']);contained=all(inside(p,projection) for p in poly)
            count=candidate['vref_inner_variant']['via_count'];intrusions=[r for r,c in courts.items() if r!=ref and pl[r]['face']=='inner' and overlap(poly,c)]
            shield_hit=any(overlap(poly,s) for ss in shields.values() for s in ss)
            passed=contained and count<=1 and dd<=self.L['vref_mm'] and not intrusions and not shield_hit
            vref_variants.append(dict(ref=ref,placement=alt[ref],courtyard=framed(poly),inside_afe_projection_plus_margin=contained,vref_vias=count,distance_mm=dd,inner_courtyard_intrusions=intrusions,shield_intrusion=shield_hit,outcome='CONDITIONAL' if passed else 'REJECTED',baseline_remains_skin=True))
        return dict(evidence_class='PROJECT_DERIVED',paths=paths,shield_regions={a:[framed(p) for p in ss] for a,ss in shields.items()},ties=ties,shield_connected=connected,ground_vias=ground_vias,individual_ground_vias_pass=via_unique and not any(v['shield_intrusions'] for v in ground_vias),locality=locality,vref_inner_variants=vref_variants,led_loops=loops,digital_corridors=digital,vled_entries=vled,package_boundary_guards=[dict(afe=a,courtyard=framed(courts[a]),outside_guard_regions=[framed(q) for p in shields[a] for q in outside_court(p,courts[a])],package_escape_regions=[framed(clip(p,courts[a])) for p in shields[a] if area(clip(p,courts[a]))>EPS],guard_interruption_outside_courtyard=False,inside_courtyard='Fixed ball escape only; no board-level guard reduction',pgnd_escape='D3 via-in-pad to local ground plane; no discretionary PD corridor entry',supplier_gate='SR-REAR-PCB') for a in AFES],vled_entry_regions=[framed(poly) for name,polys,pkg in aggressors if 'VLED-entry' in name for poly in polys],aggressor_failures=exclusion,min_aggressor_gap_mm=min(all_gaps,default=0),spacing_metric='edge-to-edge; circular/roundrect pads use conservative bounding rectangles; trace uses square-ended width reservation',corridor_width_mm=w,topology_requirements=dict(coplanar_guard='L1 PD_GND fully surrounds each PD_IN; extend L2 shield below PD courtyard',adjacent_ground='L3 solid PCB GND adjacent to L2 PD_GND islands; no signals over/through islands',ground_edge='C3/C4/D3 short at WLP edge to one local GND via per AFE; individual capacitor ground vias',verification='Reservation study only; copper continuity, via count and absence of signal crossings must be verified in separately authorized implementation',source='MAX86140/MAX86141 Rev5 p49–52',evidence_class='MANUFACTURER_VERIFIED'))

    def entry_options(self,entry,afe,ball,pl,courts,shields,corner):
        options=[]
        for vf in self.I['search']['entry_vertical_first']:
            line=polyline(entry,self.pad(afe,ball,pl),vf)
            regs=corridor(line,self.value('guard_trace_mm',corner))
            regs += [p for pin,p in self.pad_polys(afe,pl) if pin==ball]
            gg=min(clearance(regs,ss,courts[afe] if a==afe else None) for a,ss in shields.items())
            options.append(dict(orientation='vertical-first' if vf else 'horizontal-first',path=framed(line),
                regions=[framed(p) for p in regs],gap_mm=gg,spacing_metric='edge-to-edge',pass_check=gg>=self.L['aggressor_mm']-EPS,
                rank=[gg<self.L['aggressor_mm']-EPS,-gg,length(line),vf]))
        return options

    def package_escape(self):
        pads={p['pin']:p for p in self.fp['U12']['pads']};pitch=dist(pads['D3']['xy'],pads['D4']['xy']);diam=pads['D4']['size_mm'][0]
        corners={}
        for corner in CORNERS:
            t=self.value('guard_trace_mm',corner);s=self.value('guard_space_mm',corner);w=t+2*(s+self.value('guard_copper_mm',corner))
            corners[corner]=dict(pitch_mm=pitch,pad_diameter_mm=diam,interpad_gap_mm=pitch-diam,trace_plus_two_clearances_mm=t+2*s,ordinary_inner_ball_escape_fits=t+2*s<=pitch-diam+EPS,guard_corridor_width_mm=w,pgnd_centre_to_pd2_corridor_upper_bound_mm=pitch-w/2,aggressor_required_mm=self.L['aggressor_mm'],spacing_metric='centre-to-edge diagnostic inside package; exempt, not hard acceptance')
        return dict(evidence_class='PROJECT_DERIVED',corners=corners,inner_balls=['B2','B3','B4','C2','C3','C4'],hdi_required=not corners['optimistic']['ordinary_inner_ball_escape_fits'],min_layers=4,layer_roles=['L1 components / PD_IN / coplanar PD_GND','L2 PD_GND shielding islands','L3 solid GND adjacent to shielding','L4 inner face'],pcb_thickness_mm={k:self.S['parameters']['t_rear_pcb'][k] for k in ['min','nom','max']},supplier_stackup=None,supplier_gate='SR-REAR-PCB: microvia-in-pad, dielectric/drill/fill/plating and process qualification unprovided; no supplier stackup invented',package_exemption=dict(decision='OD-G3-MAX86141-PKG',scope='Fixed same-package pad/terminal escape only within that AFE courtyard. Both compared regions are clipped at the boundary for that scoped comparison. Nonterminal loop segments and non-AFE pads receive no exemption. Foreign shields, tail and capacitors remain unmasked. Outside remains >=0.500 mm edge-to-edge',centre_to_centre_mm=pitch,edge_to_edge_pad_gap_mm=pitch-diam,land_diameter_mm=diam,land_pattern_evidence='MANUFACTURER_DATA_REQUIRED: AN1891 / 21-100134 land pattern; existing 0.254 mm library land retained unchanged',hard_failure=False))

    def optical(self,pl,courts,corner):
        pairs=[]
        for c in self.channels:
            for d in self.detectors:
                if c['afe']!=d['afe']:continue
                dd=dist(pl[c['emitter']]['xy'],pl[d['pd']]['xy']);lo,hi=self.I['optics']['range_mm']
                pairs.append(dict(afe=c['afe'],led=c['led'],site=c['site'],emitter=c['emitter'],pd=d['pd'],wavelength_nm=c['wavelength_nm'],distance_mm=dd,in_study_range=lo<=dd<=hi,bin_indices=[i for i,(a,b) in enumerate(self.I['optics']['bins_mm']) if a<=dd<=b],basis='physical package centres; die offsets not asserted'))
        sym=[]
        for d in self.detectors:
            for color in [536,660,850,940]:
                ps=[p for p in pairs if p['pd']==d['pd'] and p['wavelength_nm']==color]
                if len(ps)==2:sym.append(dict(pd=d['pd'],wavelength_nm=color,residual_mm=abs(ps[0]['distance_mm']-ps[1]['distance_mm'])))
        mirror=[]
        for a,b in [('D401','D402'),('D403','D404'),('D405','D407'),('D424','D423'),('D414','D413'),('U12','U13')]:
            mirror.append(dict(refs=[a,b],residual_mm=dist([-pl[a]['xy'][0],pl[a]['xy'][1]],pl[b]['xy'])))
        crosspairs=[dict(emitter=c['emitter'],pd=d['pd'],wavelength_nm=c['wavelength_nm'],distance_mm=dist(pl[c['emitter']]['xy'],pl[d['pd']]['xy'])) for c in self.channels for d in self.detectors if c['afe']!=d['afe']]
        cellgaps=[dict(emitter=e,pd=p,gap_mm=gap(courts[e],courts[p])) for e,p in itertools.product(EMITTERS,PDS)]
        required=self.P['barrier_mm']['max']+2*self.value('wall_clearance_mm',corner)
        apertures=[]
        for ref in EMITTERS+PDS:
            facts=self.I['manufacturer_facts']['SFH2703H' if ref in PDS else 'SFH7018A'] if ref not in ['D405','D406','D407'] else None
            for window in self.I['optics']['window_mm']:
                if facts:
                    active=facts['chip_mm'] if ref in PDS else [max(v[i] for v in facts['chip_mm'].values()) for i in [0,1]]
                    # Centres are unresolved: candidate cells are package based; W flags cannot close alignment.
                    height=facts['height_nom_mm'];depth=self.S['parameters']['h_optics_max']['nom']+self.S['parameters']['c_optics'][CORNERS[corner]]-height
                    size=[v+2*(depth+window)*math.tan(math.radians(facts['half_angle_deg'])) for v in active]
                    shape=hull([world(q,pl[ref]) for q in rect(-size[0]/2,-size[1]/2,size[0]/2,size[1]/2)])
                    fits=all(inside(q,courts[ref]) for q in shape)
                    apertures.append(dict(ref=ref,window_mm=window,depth_above_emitter_mm=depth,unrefracted_cone_size_mm=size,package_centred_envelope=framed(shape),fits_cell=fits,active_area_centred_qualification='MANUFACTURER_DATA_REQUIRED: register top-view active-area position to frozen footprint pin orientation; dimensions shown are an envelope, not a released aperture',evidence_class='PROJECT_DERIVED'))
                else:apertures.append(dict(ref=ref,window_mm=window,unrefracted_cone_size_mm=None,fits_cell=None,active_area_centred_qualification='MANUFACTURER_DATA_REQUIRED: SFH4053B active area, position and half angle',evidence_class='MANUFACTURER_DATA_REQUIRED'))
        variants={}
        mingap=min(g['gap_mm'] for g in cellgaps)
        for w in self.I['optics']['window_mm']:
            known=[a for a in apertures if a['window_mm']==w and a['fits_cell'] is not None]
            variants[str(w)]=dict(W0='CONDITIONAL: common transparent window, residual lateral path; MG-WINDOW-XTALK',W1=dict(geometric_rib_gap_pass=mingap>=self.P['barrier_mm']['max'],all_known_full_cones_fit=all(a['fits_cell'] for a in known),qualified=False),W2=dict(geometric_seal_land_pass=mingap>=self.P['barrier_mm']['max']+2*self.value('seal_land_mm',corner),all_known_full_cones_fit=all(a['fits_cell'] for a in known),qualified=False),decision='Cone clipping is a ranking/measurement tradeoff, not a new hard optical-performance requirement.')
        coverage={str(w):dict(total=sum(p['wavelength_nm']==w for p in pairs),in_range=sum(p['wavelength_nm']==w and p['in_study_range'] for p in pairs),bins_occupied=sorted({i for p in pairs if p['wavelength_nm']==w for i in p['bin_indices']})) for w in self.I['optics']['wavelength_labels_nm']}
        return dict(evidence_class='PROJECT_DERIVED',pairs=pairs,coverage=coverage,symmetry=sym,mirror_residuals=mirror,cross_afe_pairs=crosspairs,cross_afe_min_mm=min(p['distance_mm'] for p in crosspairs),physical_cells={r:framed(courts[r]) for r in EMITTERS+PDS},cell_gaps=cellgaps,minimum_cell_gap_mm=mingap,required_cell_gap_mm=required,active_area_centre_parameters=self.I['optics']['active_area_offsets'],cell_gap_pass=mingap>=required-EPS,apertures=apertures,window_variants=variants,ppg2_led6=[p for p in pairs if p['afe']=='U13' and p['led']==6],interpretation='Coverage, symmetry, cross-AFE distance, cone clipping and window proxies are RANKING metrics only. No physiological PPG performance is inferred.')

    def support_study(self,pl,courts,outline,tail,corner='nominal',fixed=None):
        options=[];size=self.value('support_size_mm',corner);clear=self.L['support_chip_mm']
        sites=[(math.hypot(*x['centre_rear_mm']),x['azimuth_deg']) for x in fixed] if fixed is not None else itertools.product(self.I['search']['support_radii_mm'],self.I['search']['support_azimuth_deg'])
        for r,az in sites:
            c=polar(r,az);poly=rect(c[0]-size/2,c[1]-size/2,c[0]+size/2,c[1]+size/2)
            chipgap=min(gap(poly,courts[k]) for k in AFES+MUXES)
            hits=[ref for ref,p in courts.items() if overlap(poly,p)]
            passed=all(inside(p,outline) for p in grow(poly,self.value('edge_mm'))) and chipgap>=clear and not hits and (not tail or gap(poly,tail)>=self.L['thermode_mm'])
            options.append(dict(azimuth_deg=az,centre_rear_mm=c,centre_assembly_mm=assembly(c),polygon=framed(poly),chip_gap_mm=chipgap,intrusions=hits,pass_check=passed))
        valid=[x for x in options if x['pass_check']];best=[];score=None
        for triple in itertools.combinations(valid,3):
            angles=sorted(x['azimuth_deg'] for x in triple);maxgap=max(b-a for a,b in zip(angles,angles[1:]+[angles[0]+360]))
            sc=(maxgap,-min(x['chip_gap_mm'] for x in triple),tuple(angles))
            if score is None or sc<score:score=sc;best=list(triple)
        return dict(selected=best,alternatives=options,minimum_count=3,pass_check=len(best)>=3,load_path='window → pod frame → hard stops → carrier; never through optical parts or pack',loads='SUPPLIER_DATA_REQUIRED: compression/deflection proof at OD-WATER qualification; no load capacity invented',evidence_class='PROJECT_DERIVED')

    def heights(self,pl):
        rows=[]
        for ref in sorted(pl):
            if ref=='J1502':continue
            face=pl[ref]['face'];limit=self.L['inner_ceiling_mm'] if face=='inner' else self.S['parameters']['h_optics_max']['nom']
            if ref=='C1501':
                h=self.P['c1501_height_mm']['max'];cls='PROVISIONAL_ASSUMPTION';source='G3 DNP space reservation; not an electrically sized/selected part'
            else:
                name=self.components[ref]['footprint'].split(':')[-1];entry=self.H['footprints'][name];h=entry['max_mm'];cls={'KNOWN':'MANUFACTURER_VERIFIED','PARAMETRIC':'PROVISIONAL_ASSUMPTION','SUPPLIER_DATA_REQUIRED':'MANUFACTURER_DATA_REQUIRED'}[entry['class']];source=entry['source']
                if h is not None and name.startswith(('C_','R_')):h+=self.H['solder_allowance_mm'];cls='PROVISIONAL_ASSUMPTION'
                if ref in MUXES:cls='MANUFACTURER_DATA_REQUIRED';h=None;source='TS5A12301E YFP: local seated-height evidence absent; historical 0.5 is parametric only'
                if ref.startswith('NT'):cls='PROJECT_DERIVED';source='Immutable NetTie copper-only footprint; no component body'
            rows.append(dict(ref=ref,face=face,max_seated_mm=h,qualification_ceiling_mm=limit,within_budget=h is None or h<=limit+EPS,evidence_class=cls,source=source,unknown=h is None))
        return rows

    def stacks(self,heights):
        base=[self.g2.stack(self.G2['allocation'],high=hi) for hi in [False,True]]
        for name,row in zip(['G2-REVA','G2-REVA-HI'],base):
            expected=next(x for x in self.G2['stacks'] if x['id']==name)
            for key in ['nominal_mm','rss_mm','linear_mm']:assert row[key]==expected[key]
            row['id']=name
        skin=max(r['max_seated_mm'] if r['max_seated_mm'] is not None else r['qualification_ceiling_mm'] for r in heights if r['face']=='skin')
        inner=max(r['max_seated_mm'] if r['max_seated_mm'] is not None else r['qualification_ceiling_mm'] for r in heights if r['face']=='inner')
        derived=[]
        for hi,b in zip([False,True],base):
            study=G3Stack(self.g2,skin,inner);out=study.stack(self.G2['allocation'],high=hi)
            derived.append(dict(id=b['id'],nominal_mm=out['nominal_mm'],rss_mm=out['rss_mm'],linear_mm=out['linear_mm'],delta_nominal_mm=out['nominal_mm']-b['nominal_mm'],delta_rss_mm=out['rss_mm']-b['rss_mm'],delta_linear_mm=out['linear_mm']-b['linear_mm']))
        return dict(baseline=base,with_g3_height_reservations=derived,skin_ceiling_used_mm=skin,inner_ceiling_used_mm=inner,zero_delta=all(abs(r[k])<EPS for r in derived for k in ['delta_nominal_mm','delta_rss_mm','delta_linear_mm']),qualification='Conditional height-reservation calculation, not qualification of unknown packages or acceptance of XY topology.',evidence_class='PROJECT_DERIVED')

    def candidate(self,c):
        pl=copy.deepcopy(c['placements']);n=self.I['search']['outline_vertices'];outline=hull([polar(c['outline_radius_mm'],i*360/n) for i in range(n)])
        occupied={ref:self.court(ref,pl) for ref in pl if pl[ref]['face']=='inner'}
        tail=self.tail_study(outline,occupied);ts=tail['selected'];tailpoly=ts['corners']['nominal']['geometry']['rear_mm'] if ts else []
        pl['J1502']=dict(xy=ts['centre_rear_mm'] if ts else [0,0],rotation_deg=(azimuth(ts['centre_rear_mm'])+(90 if ts['arrangement']=='radial' else 0))%360 if ts else 0,face='inner',evidence_class='PROVISIONAL_ASSUMPTION')
        # C1501 follows the tail entry, with an explicit provisional courtyard reservation.
        pl['C1501']=dict(xy=add(pl['J1502']['xy'],self.I['search']['c1501_offset_mm']),rotation_deg=0,face='inner',evidence_class='PROVISIONAL_ASSUMPTION')
        courts={r:self.court(r,pl) for r in pl if r in self.fp}
        cx,cy=pl['C1501']['xy'];courts['C1501']=rect(cx-self.value('c1501_width_mm')/2,cy-self.value('c1501_depth_mm')/2,cx+self.value('c1501_width_mm')/2,cy+self.value('c1501_depth_mm')/2)
        courts['J1502']=tailpoly
        # U6 is absent from the provisional placement until the thermal ranking.
        provisional=dict(pl,**{r:dict(xy=[0,0],rotation_deg=0,face='skin') for r in ['U6','C802']})
        preview=self.guarded(provisional,courts,tailpoly,c,'nominal')
        thermal=self.thermal(pl,courts,tailpoly,outline,[p['rear_mm'] for p in preview['vled_entry_regions']])
        pl['U6']=thermal['selected']['placement'];pl['C802']=thermal['selected']['c802_placement']
        for ref in ['U6','C802']:courts[ref]=self.court(ref,pl)
        assert set(pl)==set(self.components)
        heights=self.heights(pl);stacks=self.stacks(heights);corners={};base_courts=copy.deepcopy(courts)
        nominal_supports=self.support_study(pl,courts,outline,tailpoly)
        for corner in CORNERS:
            courts=copy.deepcopy(base_courts)
            cx,cy=pl['C1501']['xy'];courts['C1501']=rect(cx-self.value('c1501_width_mm',corner)/2,cy-self.value('c1501_depth_mm',corner)/2,cx+self.value('c1501_width_mm',corner)/2,cy+self.value('c1501_depth_mm',corner)/2)
            tailpoly=ts['corners'][corner]['geometry']['rear_mm'] if ts else []
            courts['J1502']=tailpoly
            optical=self.optical(pl,courts,corner);analog=self.guarded(pl,courts,tailpoly,c,corner)
            collisions=[dict(refs=[a,b],area_mm2=area(clip(courts[a],courts[b]))) for a,b in itertools.combinations(sorted(courts),2) if pl[a]['face']==pl[b]['face'] and overlap(courts[a],courts[b])]
            outside=[r for r,p in courts.items() if not all(inside(q,outline) for q in grow(p,self.value('edge_mm',corner)))]
            # All skin reservations, including AFEs and U6, are cells within one pod hull.
            skin_hull=hull([p for r,poly in courts.items() if pl[r]['face']=='skin' for p in poly]);pod=grow(skin_hull,self.value('frame_wall_mm',corner))
            ambient=min(point_seg(q,a,b) for p in PDS for q in courts[p] for a,b in zip(pod,pod[1:]+pod[:1]))
            supports=nominal_supports if corner=='nominal' else self.support_study(pl,courts,outline,tailpoly,corner,nominal_supports['selected'])
            section_corner=section(self)['corners'][corner]
            checks=dict(lower_web=section_corner['lower_web_margin_mm']>=-EPS,optical_clearance_suballocation=section_corner['optical_suballocation_overrun_mm']<=EPS,face_allocation=all(pl[r]['face']=='skin' for r in REQUIRED_SKIN),height_ceilings=all(r['within_budget'] for r in heights),courtyard_nonoverlap=not collisions,outline_containment=not outside,cell_barrier_gap=optical['cell_gap_pass'],pd_in_paths=all(p['path_pass'] for p in analog['paths']),pd_ground_ties=all(t['pass_check'] for t in analog['ties']),pd_ground_shield_connected=all(analog['shield_connected'].values()),individual_ground_vias=analog['individual_ground_vias_pass'],vref_baseline=all(pl[ref]['face']=='skin' or (c['vref_vias']<=1 and all(inside(p,grow(courts[afe],self.L['vref_projection_mm'])) for p in courts[ref]) and dist(self.pad(ref,'1',pl),self.pad(afe,'B5',pl))<=self.L['vref_mm']) for afe,ref in zip(AFES,['C4103','C4203'])),decoupling_locality=all(t['pass_check'] for t in analog['locality']),shield_aggressor_exclusion=not analog['aggressor_failures'],led_loops_clear=all(l['passes_no_intersection'] for l in analog['led_loops']),tail_fit=bool(ts and ts['corners'][corner]['sector_fit'] and ts['corners'][corner]['outline_and_thermode_fit'] and ts['corners'][corner]['strain_relief_sector_fit'] and not ts['corners'][corner]['inner_thermode_intrusions']),outline_rmax=max(math.hypot(*q) for q in outline)<=self.L['outline_radius_mm']+EPS,pod_contains_all_skin=all(inside(p,pod) for r,poly in courts.items() if pl[r]['face']=='skin' for p in poly),ambient_edge_path=ambient>=self.value('frame_wall_mm',corner)-EPS,thermal_locality=thermal['selected']['nominal_pass'],stack_zero_delta=stacks['zero_delta'])
            if supports:checks['support_lands']=supports['pass_check']
            corners[corner]=dict(hard_checks=checks,hard_failures=[k for k,v in checks.items() if not v],collisions=collisions,outside_outline=outside,optical=optical,analog=analog,pod=framed(pod),pod_area_mm2=area(pod),ambient_edge_path_proxy_mm=ambient,supports=supports)
        courts=base_courts;tailpoly=ts['corners']['nominal']['geometry']['rear_mm'] if ts else []
        nominal=corners['nominal'];op=nominal['optical'];an=nominal['analog']
        footprints={r:dict(**p,assembly_xy_mm=assembly(p['xy']),courtyard=framed(courts[r]),value=self.components[r]['value'],footprint=self.components[r]['footprint']) for r,p in pl.items()}
        interference=self.res_metrics(outline)
        for rid,result in interference.items():result['disposition']='MEASUREMENT_GATED X16; no magnetic claim' if rid=='MAG_CLEAR' else 'C5/SR-FPC-MECH lower-web Z separation requires qualified cross-section' if rid in ['LRA','FPC_UNDER'] else 'DEFERRED_G4: preserve charger reservations and reported clearance'
        score=[0,abs(stacks['with_g3_height_reservations'][0]['delta_nominal_mm']),-sum(x['in_range'] for x in op['coverage'].values()),sum(s['residual_mm'] for s in op['symmetry']),max(p['length_mm'] for p in an['paths']),-min(p['minimum_foreign_pad_gap_mm'] for p in an['paths']),-an['min_aggressor_gap_mm'],sum(l['area_mm2'] for l in an['led_loops']),thermal['selected']['rank'][1],nominal['pod_area_mm2'],area(outline),-min(x['plan_gap_mm'] for k,x in interference.items() if k in ['LRA','FPC_UNDER','CHG_ROUTE','CHG_LINK','CHG_CONTACT']),ts['corners']['nominal']['rows'] if ts else 99]
        return dict(id=c['id'],name=c['name'],evidence_class='PROJECT_DERIVED',placements=footprints,corners=corners,heights=heights,stacks=stacks,tail=tail,thermal=thermal,outline=framed(outline),outline_area_mm2=area(outline),usable_area_mm2=area(outline)-union_area([clip(p,outline) for r,p in courts.items() if pl[r]['face']=='skin']),area_note='Outline area minus exact union of contained skin courtyard intersections; does not claim routable area after shields/pod/slots.',r_max_assembly=[dict(azimuth_deg=a,r_mm=rmax(outline,a)) for a in range(0,360,self.I['search']['rmax_step_deg'])],interactions=interference,pod_interactions=self.res_metrics(nominal['pod']['rear_mm']),mag_current_regions=dict(tail_land_overlap_mm2=sum(area(clip(tailpoly,p)) for p in self.respieces['MAG_CLEAR']),vled_entry_overlap_mm2=union_area([clip(poly,p) for poly in [courts['C1501']]+[v['rear_mm'] for v in an['vled_entry_regions']] for p in self.respieces['MAG_CLEAR']]),led_loops=[dict(afe=l['afe'],led=l['led'],area_mm2=l['mag_clear_overlap_mm2']) for l in an['led_loops']],disposition='MEASUREMENT_GATED X16 O1/O2: quantify BMM350 field/error versus LED duty/charging before accepting any projected overlap; no magnetic closure'),nominal_acceptable=not nominal['hard_failures'],rank=score,outcome='CONDITIONAL' if not nominal['hard_failures'] else 'REJECTED',reasons=nominal['hard_failures'])

class G3Stack(g2.Study):
    """Use G2's tolerance and stack evaluation, altering only requested G3 envelopes."""
    def __init__(self,base,skin,inner):
        self.__dict__=copy.deepcopy(base.__dict__);self.g3_skin=skin;self.g3_inner=inner
    def g1_eval(self,levers,delta=None):
        vals=list(super().g1_eval(levers,delta));p=vals[3]
        p['h_optics_max']=max(p['h_optics_max'],self.g3_skin+(delta or {}).get('h_optics_max',0))
        p['h_rear_inner']=max(p['h_rear_inner'],self.g3_inner+self.P['tail_joint_mm']['nom']+(delta or {}).get('h_rear_inner',0))
        return tuple(vals)

def gates(study,thresholds):
    return [
        dict(id='SR-SFH4053B-DS',evidence_class='MANUFACTURER_DATA_REQUIRED',status='OPEN',acceptance=dict(seated_max_mm=thresholds['stack_neutral_skin_max_mm'],body_and_emitting_area='Primary package/active-area drawing; rerun all D405–D407 geometry against verified outline, pads and emission position',minimum_emitter_pd_cell_gap_mm=study.P['barrier_mm']['max']+2*study.value('wall_clearance_mm')),blocks='Final G3 closure criterion 10a/b; no 0.45 mm height credited'),
        dict(id='SR-MAX86141-LAND',evidence_class='MANUFACTURER_DATA_REQUIRED',status='OPEN',acceptance=dict(existing_land_diameter_mm=study.package_escape()['package_exemption']['land_diameter_mm'],pitch_mm=study.I['manufacturer_facts']['MAX86141']['pitch_mm'],evidence='AN1891 / 21-100134 land pattern must verify the existing land geometry; any discrepancy requires a separately authorized footprint review'),blocks='Land-pattern evidence; footprint geometry and pin map unchanged'),
        dict(id='SR-MAX86141-HEIGHT',evidence_class='MANUFACTURER_DATA_REQUIRED',status='OPEN',acceptance=dict(seated_max_mm=thresholds['stack_neutral_skin_max_mm'],outline='21-100134'),blocks='Criterion 10a'),
        dict(id='SR-TS5A12301E-HEIGHT',evidence_class='MANUFACTURER_DATA_REQUIRED',status='OPEN',acceptance=dict(seated_max_mm=thresholds['stack_neutral_skin_max_mm']),blocks='Skin ceiling qualification; 0.5 mm historical placeholder is not manufacturer evidence'),
        dict(id='SR-FPC-MECH',evidence_class='SUPPLIER_DATA_REQUIRED',status='OPEN',acceptance=dict(positions=24,logical_nets=13,g3_joint_max_mm=study.I['contract_values']['g3_joint_closure_max_mm'],g2_joint_max_mm=study.g2.P['tail_joint_mm']['max'],per_vled_position_continuous_equivalent_min_ma=study.I['contract_values']['vled_per_position_threshold_ma'],arithmetic_ma=study.I['contract_values']['vled_current_ma']/study.I['contract_values']['vled_positions'],thermode_keepout_min_mm=study.L['thermode_mm'],pitch_range_mm={k:study.g2.P['sensor_pitch_mm'][k] for k in ['min','nom','max']},geometry='Confirm evaluated land width/pitch/rows, physical pin-order drawing, fanout into unchanged FPC_UNDER, tail attachment, strain relief and electrical current rating basis. G2 supplier current requirements remain unchanged.'),blocks='Criterion 10c; >0.05 through 0.08 keeps G2 valid but G3 at most CONDITIONAL; >0.08 outside G2 model'),
        dict(id='SR-C1501',evidence_class='SUPPLIER_DATA_REQUIRED',status='OPEN',acceptance=dict(height_max_mm=study.L['inner_ceiling_mm'],reservation_width_mm=study.value('c1501_width_mm'),reservation_depth_mm=study.value('c1501_depth_mm'),electrical='DNP remains; qualify effective capacitance/droop/recharge/DC-bias within this envelope before fitting'),blocks='Reservoir population; no thinned part assumed'),
        dict(id='SR-REAR-PCB',evidence_class='SUPPLIER_DATA_REQUIRED',status='OPEN',acceptance=dict(thickness_mm=[study.S['parameters']['t_rear_pcb']['min'],study.S['parameters']['t_rear_pcb']['max']],stack_neutral_nominal_mm=study.S['parameters']['t_rear_pcb']['nom'],min_layers=4,wlp_pitch_mm=study.I['manufacturer_facts']['MAX86141']['pitch_mm'],inner_ball_escape='Qualified filled/capped microvia-in-pad; supplier supplies drill, dielectric, copper, fill/plating and layer stack',guard_fab_classes=study.P['guard_trace_mm']),blocks='Fabrication; any >1.0 mm reported as stack overrun; no qualified stackup exists'),
        dict(id='SR-WINDOW',evidence_class='SUPPLIER_DATA_REQUIRED',status='OPEN',acceptance=dict(thickness_study_mm=study.I['optics']['window_mm'],nominal_stack_neutral_mm=study.S['parameters']['t_window']['nom'],active_area_alignment='Register active areas to apertures before cutting/moulding',seal_land_mm=study.P['seal_land_mm']),blocks='Window freeze and MG-WINDOW-XTALK'),
        dict(id='SR-BARRIER',evidence_class='SUPPLIER_DATA_REQUIRED',status='OPEN',acceptance=dict(wall_mm=study.P['barrier_mm'],wall_clearance_mm=study.P['wall_clearance_mm'],compression_mm=study.P['compression_mm'],opacity='No transmission number invented; measured no-skin pair floor must meet owner MG-WINDOW-XTALK threshold'),blocks='Barrier/isolation qualification'),
        dict(id='SR-ADHESIVE',evidence_class='SUPPLIER_DATA_REQUIRED',status='OPEN',acceptance=dict(retention_mm=study.P['adhesive_mm'],combined_retention_and_compression_max_nominal_mm=study.S['parameters']['c_optics']['nom']),blocks='X22 Z/retention qualification'),
        dict(id='SR-PD-CAPACITANCE',evidence_class='MANUFACTURER_DATA_REQUIRED',status='OPEN',acceptance=dict(total_pd_plus_corridor_max_pf=65,pdbias='0x1',formula='C_PD(0 V) <= 65 - modelled corridor parasitic; see each path'),blocks='PD bias/noise qualification; 9 pF at 5 V is not a zero-bias value'),
        dict(id='MG-SPACING',evidence_class='MEASUREMENT_REQUIRED',status='OPEN',acceptance=dict(spacing_mm=[3,8],wavelengths_nm=study.I['optics']['wavelength_labels_nm'],metrics=['AC/DC ratio','input-referred SNR','saturation fraction','motion artefact','LED energy per accepted sample'],decision='Owner first specifies green HR, red/IR SpO2 and IR850/IR940 use. Compare wavelength-specific spacing coupons at equal current/timing/phantom and representative wrist loads; choose bins meeting modality criteria; no invented physiological threshold.'),blocks='Optical spacing/modalities freeze'),
        dict(id='MG-WINDOW-XTALK',evidence_class='MEASUREMENT_REQUIRED',status='OPEN',acceptance=dict(variants=['W0','W1','W2','W-ref'],metrics=['dark-subtracted no-skin input current per physical LED/PD pair','no-skin to phantom response ratio','repeatability across temperature and assembly'],owner_threshold=None,decision='At equal LED current and PPG_TINT compare absorber/open-air floor against phantom and opaque W-ref. Retain W0 only below owner threshold, else test W1/W2 and rerun their geometry/Z.'),blocks='Optical-isolation/window closure'),
        dict(id='MG-GUARD',evidence_class='MEASUREMENT_REQUIRED',status='OPEN',acceptance=dict(dark_noise_max_datasheet_multiplier=1.5,spi_active_noise_increase_max_fraction=.1,metrics=['RMS input-referred dark current at each PD_IN','SPI-active minus SPI-idle RMS noise','PD_GND single-point continuity and return-current verification'],decision='LEDs off, matched PPG_TINT/PDBIAS/temperature/sample count; compare MAX86141 electrical-characteristics row for that timing. Reject if either provisional threshold fails; investigate shield/return paths. No result fabricated.'),blocks='Guarded-analog qualification'),
        dict(id='MG-THERMAL',evidence_class='MEASUREMENT_REQUIRED',status='OPEN',acceptance=dict(owner_accuracy_target_c=None,metrics=['U6 minus calibrated skin-phantom reference steady-state error','temperature shift across LED duty','charging-on/off shift','settling time and hysteresis'],decision='Sweep ambient, phantom temperature, LED duty, idle/active electronics and charger states with repeated mountings. Accept only after owner accuracy target is set and met; otherwise revise island/contact/scheduling.'),blocks='Skin-temperature accuracy'),
        dict(id='MG-MAG',evidence_class='MEASUREMENT_REQUIRED',status='OPEN',acceptance=dict(metrics=['BMM350 field delta by LED duty and charging state','heading error with assembled case'],owner_threshold=None,decision='X16 O1/O2 disposition; geometry overlap is disclosed, not magnetic qualification.'),blocks='MAG_CLEAR closure')]

def height_thresholds(study):
    h=study.S['parameters']['h_optics_max'];rows=[]
    for high in [False,True]:
        base=study.g2.stack(study.G2['allocation'],high=high);lo,hi=h['nom'],h['nom']+1
        for _ in range(24):
            mid=(lo+hi)/2;out=G3Stack(study.g2,mid,study.L['inner_ceiling_mm']).stack(study.G2['allocation'],high=high)
            if out['rss_mm']<=study.g2.I['limits']['rss_mm']:lo=mid
            else:hi=mid
        rows.append(dict(id='G2-REVA-HI' if high else 'G2-REVA',nominal_height_limit_mm=h['nom']+study.g2.I['limits']['nominal_mm']-base['nominal_mm'],rss_height_limit_mm=math.floor(lo*1000)/1000,rss_threshold_resolution_mm=.001))
    return dict(evidence_class='PROJECT_DERIVED',stack_neutral_skin_max_mm=h['nom'],g1_range_max_mm=h['max'],inner_max_mm=study.L['inner_ceiling_mm'],od_thick_limits=rows,note='RSS threshold uses imported G2 tolerance sensitivities with the G3 envelope; baseline +0.1 optics uncertainty retained. Nonzero delta still requires owner acceptance.')

def section(study):
    p=study.S['parameters'];rp=study.S['radial']['parameters'];rows={}
    for corner,k in CORNERS.items():
        depth=p['h_optics_max'][k]+p['c_optics'][k]+p['t_window'][k]
        rows[corner]=dict(pod_depth_mm=depth,caseback_residual_before_wall_mm=depth-p['h_pod']['nom'],caseback_residual_after_study_wall_mm=depth-p['h_pod']['nom']-study.value('caseback_wall_mm',corner),lower_web_mm=p['t_lower_web']['min' if corner=='conservative' else 'max' if corner=='optimistic' else 'nom'],fpc_plus_clearance_mm=rp['t_fpc'][k]+rp['c_fpc'][k],optical_clearance_mm=p['c_optics'][k],retention_plus_compression_mm=study.value('adhesive_mm',corner)+study.value('compression_mm',corner))
        rows[corner]['lower_web_margin_mm']=rows[corner]['lower_web_mm']-rows[corner]['fpc_plus_clearance_mm']
        rows[corner]['optical_suballocation_overrun_mm']=max(0,rows[corner]['retention_plus_compression_mm']-p['c_optics'][k])
    return dict(corners=rows,window_delta_from_g2_nominal_mm={str(w):w-p['t_window']['nom'] for w in study.I['optics']['window_mm']},load_path='Window → pod frame → three or more stops → carrier; no optical-part or battery compression load',caseback='Numeric residual handoff only; no caseback/seal design',evidence_class='PROJECT_DERIVED')

def conflict_status(study,selected):
    statuses=[]
    for c in study.A['conflicts']:
        cid=c['id'];status='REMAINS_OPEN';evidence='G3 preserves G2 status and gates; no closure inferred.'
        if cid.startswith(('C5','X11','X12')):status='REMAINS_OPEN' if selected is None else 'SUPPLIER_DATA_GATED';evidence='Candidate geometry is in g3.candidates; no recommended topology until nominal hard checks pass. Tail alternatives do not change G2 allocation.'
        if cid.startswith('X10'):status='SUPPLIER_DATA_GATED';evidence='Manufacturer height gates remain open; stack-neutral skin maximum and OD-THICK limits are computed in g3.height_thresholds.'
        if cid.startswith(('X16','X23')):status='MEASUREMENT_GATED';evidence='Computed projected overlaps / window proxies disclosed; MG-MAG, MG-WINDOW-XTALK and thermal measurement cannot be closed by geometry.'
        if cid.startswith('X20'):status='SUPPLIER_DATA_GATED';evidence='Support reservations and load path computed; carrier load and pack-growth qualification remain open.'
        if cid.startswith(('X22','X25','X21','X14','X15','X24','C7')):status='DEFERRED_G4';evidence='Numeric section/residual and unchanged radial/cover margins handed off; G4 not authorized.'
        statuses.append(dict(id=cid,g3_status=status,g3_evidence=evidence,evidence_class='PROJECT_DERIVED'))
    return statuses

def candidate_search(study):
    candidates=[study.candidate(c) for c in study.I['candidates']]
    spec=study.I['search']['placement_trials'];base=next(c for c in study.I['candidates'] if c['id']==spec['base_candidate'])
    baseline=next(c for c in candidates if c['id']==spec['base_candidate']);trials=[]
    for trial in spec['trials']:
        authored=copy.deepcopy(base);authored['id']=trial['id'];authored['name']='Central topology: '+trial['id']
        authored['rationale']=trial['rationale']
        for ref,offset in trial['offsets_mm'].items():authored['placements'][ref]['xy']=add(base['placements'][ref]['xy'],offset)
        pl=copy.deepcopy(authored['placements'])
        for ref in ['U6','C802','J1502','C1501']:pl[ref]=copy.deepcopy(baseline['placements'][ref])
        courts={r:study.court(r,pl) for r in pl if r in study.fp}
        for ref in ['J1502','C1501']:courts[ref]=baseline['placements'][ref]['courtyard']['rear_mm']
        an=study.guarded(pl,courts,courts['J1502'],authored,'nominal')
        collisions=[dict(refs=[a,b],area_mm2=area(clip(courts[a],courts[b]))) for a,b in itertools.combinations(sorted(courts),2)
                    if a not in ['U6','C802'] and b not in ['U6','C802'] and pl[a]['face']==pl[b]['face'] and overlap(courts[a],courts[b])]
        # U6 is re-ranked in a full study; never reject a trial on the old thermal location.
        failures=[]
        if collisions:failures.append('courtyard_nonoverlap')
        if an['aggressor_failures']:failures.append('shield_aggressor_exclusion')
        row=dict(id=trial['id'],offsets_mm=trial['offsets_mm'],collisions=collisions,aggressor_failures=an['aggressor_failures'],
                 led5_gaps_mm={a:next(l['shield_gap_mm'] for l in an['led_loops'] if l['afe']==a and l['led']==5) for a in AFES},
                 screening_failures=failures,full_evaluation=not failures)
        if not failures:
            result=study.candidate(authored);candidates.append(result);row['final_hard_failures']=result['reasons']
        trials.append(row)
    return candidates,dict(evidence_class='PROJECT_DERIVED',policy=spec['policy'],base_candidate=spec['base_candidate'],
                           trial_count=len(trials),trials=trials)

def build_results():
    s=Study();candidates,search=candidate_search(s)
    acceptable=sorted([c for c in candidates if c['nominal_acceptable']],key=lambda c:(c['rank'],c['id']))
    selected=acceptable[0] if acceptable else None
    if selected:selected['outcome']='RECOMMENDED'
    escape=s.package_escape();thresholds=height_thresholds(s);sec=section(s);requests=gates(s,thresholds)
    verdict='G3 CONDITIONAL — SUPPLIER/MEASUREMENT GATES OPEN' if selected else 'G3 FAIL'
    handoffs=[]
    for c in candidates:
        n=c['corners']['nominal']
        handoffs.append(dict(candidate=c['id'],released=c is selected,outline=c['outline'],r_max_assembly=c['r_max_assembly'],pod=n['pod'],pod_area_mm2=n['pod_area_mm2'],pod_section=sec,window_variants=n['optical']['window_variants'],apertures=n['optical']['apertures'],supports=n['supports']['selected'],u6=c['thermal']['selected'],skin_contact_options=c['thermal']['skin_contact_options'],tail_exit=c['tail']['selected'],clearances=c['interactions'],pod_clearances=c['pod_interactions'],seal_land_mm=s.P['seal_land_mm']))
    acceptance={str(i):dict(satisfied=False,reason='No acceptable recommended candidate') for i in range(1,12)}
    for i,reason in [(1,'Owner decisions copied verbatim; immutable boundary and prior decisions validated'),(5,'Numeric height/reservation/process thresholds and missing-data classes stated'),(6,'Four required MG plans and decision logic drafted; no measurements claimed'),(9,'Exact contract verdict used'),(11,'G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES recorded outside immutable G2 records')]:acceptance[str(i)]=dict(satisfied=True,reason=reason)
    for i in [2,3]:acceptance[str(i)]=dict(satisfied=selected is not None,reason='Recommended candidate has every nominal hard check passing and all 46 placements recorded' if selected else 'No acceptable recommended candidate')
    acceptance['4']=dict(satisfied=selected is not None,reason='All candidate height budgets reproduce exact G2 stacks at zero delta; no geometry-acceptable recommendation exists' if not selected else 'Recommended candidate has zero stack delta')
    acceptance['7']=dict(satisfied=selected is not None,reason='Numeric per-candidate diagnostic handoffs provided; none released if no recommendation')
    acceptance['8']=dict(satisfied=True,reason='Tool enforces source pins, deterministic regeneration and authorized diff scope; run all §10 external validation commands')
    acceptance['10']=dict(satisfied=False,reason='Primary SFH4053B/MAX86141 height, SFH4053B optical/package evidence and supplier-qualified J1502 dimensions/joint/current remain absent')
    arch_hash=canonical_hash(s.arch_input)
    result=dict(schema='sportwatch-g3-result/1',evidence_class='PROJECT_DERIVED',evidence_policy=s.I['evidence_policy'],verdict=verdict,placement_search=search,spacing_metrics=dict(aggressor='edge-to-edge of physical pad/trace reservation and shield, outside the owning MAX86141 courtyard only for fixed package escapes',optical='centre-to-centre of packages',locality='centre-to-centre of named pads/balls; resistor fallback uses package centres',courtyard_thermal_reservation='edge-to-edge',pd_in_length='pad-centre-to-ball-centre along orthogonal path',package_pitch='centre-to-centre',package_corridor_bound='centre-to-edge diagnostic only'),owner_decisions=s.I['owner_decisions'],g2_record='G2 CLOSED — PASS WITH SUPPLIER/ENGINEERING GATES',selection=dict(selected_candidate=selected['id'] if selected else None,rule='Filter every nominal hard check, then lexicographic §7 ranking. ID only breaks exact ties.',ranking_order=['frozen/owner impact','G2 delta','optical coverage and symmetry','PD_IN length and guard width','aggressor gap and LED loop area','thermal','pod/outline/clearance','manufacturability'],eligible_candidates=[c['id'] for c in acceptable],no_selection_reason={c['id']:c['reasons'] for c in candidates} if selected is None else None),allocation=selected['placements'] if selected else None,candidates=candidates,optical_channel_map=s.channels,detector_map=s.detectors,channel_reproduction_pass=True,footprint_sources=s.footprint_sources,manufacturer_facts=s.I['manufacturer_facts'],manufacturer_unknowns=s.I['manufacturer_unknowns'],height_thresholds=thresholds,fabrication=escape,section=sec,supplier_measurement_gates=requests,conflict_status=conflict_status(s,selected),reservations=dict(g2_shared_corridors=s.G2['shared_corridors'],g2_lra_numeric_gate=next(q for q in s.G2['supplier_requests'] if q['id']=='SR-LRA'),imported_assembly=s.res,imported_rear={rid:[framed(p) for p in pieces] for rid,pieces in s.respieces.items()},g2_attach_windows=s.g2.rear_geometry(s.g2.options['J1502-TAIL0402'])['corners']),g4_handoff=dict(status='DIAGNOSTIC ONLY — no topology released' if selected is None else 'PROVISIONAL RESERVATION HANDOFF — G4 NOT AUTHORIZED',conservative_radial_margin_mm=s.I['contract_values']['conservative_radial_margin_mm'],x25_conservative_cover_fit_mm=s.I['contract_values']['cover_fit_mm'],candidates=handoffs,open_gates=requests),acceptance=acceptance,unsatisfied_acceptance=[int(k) for k,v in acceptance.items() if not v['satisfied']],manufacturing=dict(evidence_class='PROJECT_DERIVED',assembly_order=['Qualify reflow peak/cycle budget for every MPN; MAX30208 local maximum 220 C must be respected','Fixture both sides; populate qualified inner passives first, then skin optical/analog parts subject to component reflow limits','Keep flux and any underfill out of every active-area/window aperture and PD_GND isolation reservation; qualify cleaning','Hot-bar/ACF bond tail after SMT with reserved thermode access','Inspect continuity and guarded-net isolation, then assemble carrier/hard stops','Service by replacing REAR plus tail as one unit through J1501'],reflow_cycles='MANUFACTURER_DATA_REQUIRED: no complete local all-component cycle qualification',test_access='J1501 approved power/digital only; no REAR-local test pads; new test pad requires schematic ECO/owner authorization'),source_sha256=dict(s.I['source_sha256'],**{'design/mechanical/inputs/g3_rear_optical.json':sha(MECH/'inputs/g3_rear_optical.json'),'design/mechanical/tools/g3_rear_optical.py':sha(Path(__file__))}),architecture_source=dict(path='design/mechanical/architecture.json',projection=['reservations','rear_module','g2.reservations'],sha256=arch_hash,reason='Hash exact read-only source projection, excluding generated g3 quotation and conflict g3 statuses to avoid circular hashes'))
    return json.loads(dumps(result))

def render_md(res):
    out=['# G3 — REAR optical + guarded-analog placement study','', '**'+res['verdict']+'**','',res['g2_record']+'. No G2 supplier gate is closed; G4 and KiCad implementation are not authorized.','', 'Evidence classes are inherited per object in the JSON. Candidate geometry is PROVISIONAL_ASSUMPTION; computed distances are PROJECT_DERIVED. Manufacturer citations and unresolved data are explicit.','', '## Selection and hard-rule finding','']
    selected=res['selection']['selected_candidate'];out.append('Selected candidate: '+(selected or '**none**')+'.')
    out += ['', 'OD-G3-MAX86141-PKG is applied only to fixed same-package adjacency within the owning MAX86141 courtyard. No global guard or spacing reduction is applied. D3 PGND reserves via-in-pad escape; PD_IN remains zero-via, guarded, with adjacent ground and NT401/NT402 single-point ties. Package-boundary guard reservations remain continuous outside the courtyard; HDI realization remains SR-REAR-PCB.',
        '', 'Hard aggressor clearance is edge-to-edge: ordered loop reservation plus finite trace width and participating pad extents against the PD shield. Circular/roundrect pads use conservative bounding rectangles, never centre-only clearance. Locality distances are pad-centre-to-ball-centre; optical distances are package-centre-to-package-centre; courtyard, thermal and reservation gaps are edge-to-edge. The package pitch diagnostic is centre-to-centre; the package corridor bound is centre-to-edge and exempt.',
        '', 'Loop hard checks use the ordered cap → anode → cathode → mux → driver → PGND → cap polygon, decomposed with even-odd fill at self crossings. Convex hull is an additional diagnostic only and cannot reject a candidate. All horizontal-first and vertical-first single-elbow orthogonal entry alternatives are evaluated deterministically; hard clearance eligibility precedes maximum gap, then length and orientation tie-break.',
        '', 'The footprint/pin map/orientation is unchanged. Existing 0.254 mm lands remain an AN1891 / 21-100134 manufacturer-evidence gate. A geometry rejection requires placement correction, not an owner waiver.','']
    out += ['Optical coverage/symmetry and loop area are ranking metrics, not physiological performance requirements. All nominal hard checks filter eligibility before ranking.','', '| Candidate | Outcome | In-range measured pairs | Worst PD_IN mm | Min cell gap mm | Pod mm² | Nominal failures |','|---|---|---:|---:|---:|---:|---|']
    for c in res['candidates']:
        n=c['corners']['nominal'];a=n['analog'];o=n['optical'];out.append(f"| {c['id']} — {c['name']} | {c['outcome']} | {sum(p['in_study_range'] for p in o['pairs'])}/{len(o['pairs'])} | {max(p['length_mm'] for p in a['paths']):.3f} | {o['minimum_cell_gap_mm']:.3f} | {n['pod_area_mm2']:.3f} | {', '.join(c['reasons']) or 'none'} |")
    out += ['', '## Placement correction search', '', res['placement_search']['policy'], '',
        '| Trial | LED5 U12/U13 edge gap mm | Screening failures | Full evaluation failures |',
        '|---|---|---|---|']
    for t in res['placement_search']['trials']:
        out.append(f"| {t['id']} | {t['led5_gaps_mm']['U12']:.6f} / {t['led5_gaps_mm']['U13']:.6f} | {', '.join(t['screening_failures']) or 'none'} | {', '.join(t.get('final_hard_failures',[])) or ('none' if t['full_evaluation'] else 'not needed: nominal hard failure')} |")
    out += ['', '## Physical optical channel map','', '| AFE | LED/site | Wavelength nm | Physical chip/package | Cathode pins | Mux/input | AFE driver |','|---|---|---:|---|---|---|---|']
    for ch in res['optical_channel_map']:out.append(f"| {ch['afe']} | {ch['led']}/{ch['site']} | {ch['wavelength_nm']} | {ch['emitter']} | {','.join(ch['cathode_pins'])} | {ch['mux']}.{ch['mux_input']} | {ch['driver_pin']} |")
    out += ['','PPG2 LED6 is the IR940 chip in D402, despite its logical site-B role. It is not D404. D401/D403/D404 IR cathodes remain unconnected. All 24 interface positions and 13 nets are compared to the actual netlist; no REAR-local analog net crosses the interface.','']
    for d in res['detector_map']:out.append(f"- {d['pd']}.{d['pd_pin']} → {d['afe']}.{d['afe_pin']} (PD{d['channel']}).")
    out += ['', '## Candidate placement and checks','']
    for c in res['candidates']:
        n=c['corners']['nominal'];a=n['analog'];o=n['optical']
        out += ['### '+c['id'], '', '| Ref | Face | REAR X,Y mm | Rotation deg | Assembly X,Y mm |','|---|---|---|---:|---|']
        for ref,p in sorted(c['placements'].items()):out.append(f"| {ref} | {p['face']} | {p['xy'][0]:.3f}, {p['xy'][1]:.3f} | {p['rotation_deg']:.3f} | {p['assembly_xy_mm'][0]:.3f}, {p['assembly_xy_mm'][1]:.3f} |")
        out += ['','Coordinates are authored provisional placements or tool-enumerated reservations, never KiCad changes. Assembly transform is x_a = 100 − x_r, y_a = 100 + y_r; wrist view east is left.','', '| Nominal hard check | Result |','|---|---|']
        out += [f'| {k} | {"PASS" if v else "FAIL"} |' for k,v in n['hard_checks'].items()]
        out += ['', '| Corner | Hard failures | PD corridor width mm |','|---|---|---:|']
        for corner,x in c['corners'].items():out.append(f"| {corner} | {', '.join(x['hard_failures']) or 'none'} | {x['analog']['corridor_width_mm']:.3f} |")
        out += ['', '| AFE/LED | PD | Wavelength nm | Package-centre distance mm | Study range |','|---|---|---:|---:|---|']
        for p in o['pairs']:out.append(f"| {p['afe']}/{p['led']} | {p['pd']} | {p['wavelength_nm']} | {p['distance_mm']:.3f} | {'covered' if p['in_study_range'] else 'outside; ranking only'} |")
        out += ['',f"Cross-AFE minimum emitter–PD distance: {o['cross_afe_min_mm']:.3f} mm. Required cell gap: {o['required_cell_gap_mm']:.3f} mm. Symmetry, per-wavelength bins, apertures and W0/W1/W2 flags are recorded in the JSON at every corner.",'', '| PD path | Length mm | Vias | Foreign pad intrusions | C_PD(0 V) maximum for 0x1 pF |','|---|---:|---:|---|---:|']
        for p in a['paths']:out.append(f"| {p['pd']} → {p['afe']}.{p['afe_pin']} | {p['length_mm']:.3f} | {p['vias']} | {', '.join(p['non_pd_pad_intrusions']) or 'none'} | {p['capacitance']['c_pd_zero_v_max_for_pdbias_0x1_pf']:.3f} |")
        out += ['', 'PD_IN zero vias is PROJECT_DERIVED; the 6.0 mm path ceiling and fab dimensions are PROVISIONAL_ASSUMPTION. MAX86141 shielding, adjacent ground, single-point connection and individual capacitor ground-via guidance are MANUFACTURER_VERIFIED (Rev5 pp49–52). Regions/loops are reservation envelopes, not routing verification.','', '| Tie | Distance to C5 mm | Single-point netlist | Locality |','|---|---:|---|---|']
        for t in a['ties']:out.append(f"| {t['tie']} | {t['distance_mm']:.3f} | {t['single_point_netlist']} | {t['pass_check']} |")
        out += ['', '| Decoupler/passive | Target | Distance mm | Limit mm | Vias | Check |','|---|---|---:|---:|---:|---|']
        for p in a['locality']:out.append(f"| {p['ref']} | {p.get('target',','.join(p.get('targets',[])))} | {p.get('distance_mm',p.get('nearest_afe_centre_mm')):.3f} | {p['limit_mm']} | {p['signal_vias']} | {p['pass_check']} |")
        out += ['', '| VREF inner alternative | Direct projection | Vias | Distance mm | Outcome |','|---|---|---:|---:|---|']
        for v in a['vref_inner_variants']:out.append(f"| {v['ref']} | {v['inside_afe_projection_plus_margin']} | {v['vref_vias']} | {v['distance_mm']:.3f} | {v['outcome']} |")
        out += ['', '| LED loop | Ordered polygon gap mm | Copper extent gap mm (edge-to-edge) | Convex hull gap mm (diagnostic only) | Hard result |', '|---|---:|---:|---:|---|']
        for l in a['led_loops']:
            out.append(f"| {l['afe']} LED{l['led']} | {l['ordered_polygon_gap_mm']:.6f} | {l['shield_gap_mm']:.6f} | {l['convex_hull_diagnostic']['shield_gap_mm']:.6f} | {'PASS' if l['passes_no_intersection'] and l['passes_aggressor_gap'] else 'FAIL'} |")
        out += ['', '| VLED target | Orientation | Edge-to-edge gap mm | Selected |', '|---|---|---:|---|']
        for entry in a['vled_entries']:
            for alt in entry['alternatives']:
                out.append(f"| {entry['target']} | {alt['orientation']} | {alt['gap_mm']:.6f} | {alt['orientation']==entry['selected_orientation']} |")
        out += ['', 'Exact remaining nominal aggressor failures:']
        out += [f"- {f['aggressor']} → {f['shield']}: {f['gap_mm']:.6f} mm edge-to-edge < {f['required_mm']:.3f} mm." for f in a['aggressor_failures']] or ['- None.']
        t=c['tail']['selected']
        if t:
            tn=t['corners']['nominal'];out += ['',f"J1502 geometric alternative: **{t['id']}**, {tn['rows']} row(s), pitch {tn['pitch_mm']:.3f} mm, land {tn['land_width_mm']:.3f} × {tn['land_depth_mm']:.3f} mm; single-row tail width {tn['single_row_tail_width_mm']:.3f} mm. Sector fit: {tn['sector_fit']}; outline/thermode fit: {tn['outline_and_thermode_fit']}; inside nominal G2 attach window: {tn['inside_g2_attach_window']}. The full alternative sweep and conservative/optimistic results remain in the JSON. Supplier fanout/land qualification remains open."]
        else:out += ['','**No J1502 alternative fits. STOP: G2 allocation affected.**']
        th=c['thermal']['selected'];out += ['',f"U6 selected by thermal-proxy ranking at assembly azimuth {th['azimuth_deg']:.3f}°, radius {th['radius_mm']:.3f} mm: emitter gap {th['emitter_gap_mm']:.3f} mm, AFE/mux/entry gap {th['afe_mux_entry_gap_mm']:.3f} mm, tail gap {th['tail_gap_mm']:.3f} mm, isolated perimeter {th['isolated_perimeter_fraction']:.3f}. Neck carries {c['thermal']['traces_across_neck']} unique nets. No skin-temperature accuracy claim.",'', '| Reservation | Outline overlap mm² | Plan clearance mm | Disposition |','|---|---:|---:|---|']
        for rid,x in c['interactions'].items():out.append(f"| {rid} | {x['overlap_area_mm2']:.3f} | {x['plan_gap_mm']:.3f} | {x['disposition']} |")
        out += ['','Curved-reservation overlap areas use disclosed arc tessellation; chord sagitta ≤0.001 mm. Courtyard polygon collisions and tail-sector containment are evaluated directly. Charger 3-D distances are lower bounds equal to plan gaps because qualified corridor Z envelopes are absent.','']
        for rid,d in th['charger_plan_gaps_mm'].items():out.append(f'- U6 to {rid}: plan / minimum 3-D distance {d:.3f} mm.')
    out += ['', '## Stack and fabrication','', '| G2 baseline | Nominal mm | RSS mm | Linear worst mm | G3 nominal delta mm |','|---|---:|---:|---:|---:|']
    first=res['candidates'][0]
    for b,d in zip(first['stacks']['baseline'],first['stacks']['with_g3_height_reservations']):out.append(f"| {b['id']} | {b['nominal_mm']:.3f} | {b['rss_mm']:.3f} | {b['linear_mm']:.3f} | {d['delta_nominal_mm']:.3f} |")
    out += ['','These are conditional height-reservation calculations; zero Z delta does not make a rejected XY topology acceptable. C1501 stays DNP, with a ≤0.650 mm reservation ceiling; no thinned MPN is assumed.','', '```json',dumps(res['height_thresholds']).rstrip(),'```','', 'HDI / filled microvia-in-pad escape is required for B2/B3/B4/C2/C3/C4. At 0.4 mm pitch and 0.254 mm pads, the interpad gap is 0.146 mm; even the optimistic 0.075 mm trace plus two 0.075 mm clearances needs 0.225 mm. Reserve ≥4 layers: L1 PD_IN/coplanar guard, L2 PD_GND islands, L3 solid adjacent GND, L4 inner face. Supplier stackup/drill/fill/plating are unqualified.','', '```json',dumps(res['section']).rstrip(),'```','', 'G3→G4 carries every candidate outline/r_max, pod, aperture/window flags, support positions, U6 contact alternatives, tail and reservation clearances numerically in JSON. No rejected candidate is released. Conservative radial margin **−0.950 mm** and X25 cover fit **−1.100 mm** remain unchanged.','', '## Supplier and measurement gates','']
    for gate in res['supplier_measurement_gates']:out += ['### '+gate['id']+' — '+gate['status'], '',gate['evidence_class']+'. '+gate['blocks']+'.','', '```json',dumps(gate['acceptance']).rstrip(),'```','']
    out += ['## Manufacturing and bring-up','']+[f'{i}. {x}.' for i,x in enumerate(res['manufacturing']['assembly_order'],1)]+['',res['manufacturing']['reflow_cycles']+'.',res['manufacturing']['test_access']+'.','', '## Conflict status','', '| Conflict | G3 status | Evidence |','|---|---|---|']
    out += [f"| {c['id']} | {c['g3_status']} | {c['g3_evidence']} |" for c in res['conflict_status']]
    out += ['', '## Acceptance record','', '| Criterion | Satisfied | Evidence |','|---|---|---|']
    out += [f"| {i} | {res['acceptance'][str(i)]['satisfied']} | {res['acceptance'][str(i)]['reason']} |" for i in range(1,12)]
    out += ['', 'Generator consistency and mutation self-tests are separate from engineering acceptance. Run all G3_BRIEF §10 commands. No supplier request has been issued. No measurement result has been invented.','']
    return '\n'.join(out)

def architecture_section(res):return '<!-- G3 GENERATED BEGIN -->\n'+render_md(res).replace('# G3 —','## G3 —',1)+'<!-- G3 GENERATED END -->\n'

def render_faces(res):
    esc=html.escape;scale=12;panels=len(res['candidates'])*2;width=900;height=panels//2*480+80
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">','<rect width="100%" height="100%" fill="white"/>',f'<text x="15" y="23" font-family="sans-serif" font-size="16">{esc(res["verdict"])}</text>','<text x="15" y="43" font-family="sans-serif" font-size="11">REAR frame, skin view north up / east left. Diagnostic reservations only; no KiCad edits.</text>']
    for ci,c in enumerate(res['candidates']):
        for fi,face in enumerate(['skin','inner']):
            ox=225+450*fi;oy=290+480*ci
            def polygon(ps,fill,stroke='#333',opacity=1):out.append('<polygon points="'+' '.join(f'{ox+scale*x:.3f},{oy+scale*y:.3f}' for x,y in ps)+f'" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="0.7"/>')
            out.append(f'<text x="{ox-200}" y="{oy-218}" font-family="sans-serif" font-size="13">{esc(c["id"]+" / "+face+" / "+c["outcome"])}</text>')
            polygon(c['outline']['rear_mm'],'#f5f6f8')
            for rid,color in [('MAG_CLEAR','#f4cccc'),('LRA','#999999'),('FPC_UNDER','#ead590')]:
                for piece in res['reservations']['imported_rear'][rid]:
                    clipped=clip(piece['rear_mm'],c['outline']['rear_mm'])
                    if area(clipped)>EPS:polygon(clipped,color,color,.35)
            for ref,p in c['placements'].items():
                if p['face']!=face:continue
                polygon(p['courtyard']['rear_mm'],'#f3bb89' if ref in EMITTERS else '#a7c9ec' if ref in PDS else '#d5d6d8')
                x,y=p['xy'];out.append(f'<text x="{ox+scale*x:.3f}" y="{oy+scale*y:.3f}" text-anchor="middle" font-family="monospace" font-size="8">{esc(ref)}</text>')
            if face=='skin':
                for slot in c['thermal']['selected']['slot_centrelines']:
                    polygon(slot['rear_mm'],'none','#444')
                for ss in c['corners']['nominal']['analog']['shield_regions'].values():
                    for p in ss:polygon(p['rear_mm'],'#43c58a','#047849',.25)
                for loop in c['corners']['nominal']['analog']['led_loops']:polygon(loop['polygon']['rear_mm'],'none','#db4646',.3)
                polygon(c['corners']['nominal']['pod']['rear_mm'],'none','#854fa1')
            else:
                for entry in c['corners']['nominal']['analog']['vled_entry_regions']:polygon(entry['rear_mm'],'#cd7c00','#cd7c00',.5)
                for land in c['corners']['nominal']['supports']['selected']:polygon(land['polygon']['rear_mm'],'#c8b6e0')
                if c['tail']['selected']:polygon(c['tail']['selected']['thermode_keepout']['rear_mm'],'none','#bb7924')
    out.insert(4,'<text x="15" y="59" font-family="sans-serif" font-size="10">Rose: MAG_CLEAR; grey: LRA; gold: FPC_UNDER; green: shield; red: ordered loops; orange: VLED entry; purple: pod/stops.</text>')
    out.append('</svg>');return '\n'.join(out)+'\n'

def render_section(res):
    c=res['section']['corners']['nominal'];out=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="400" viewBox="0 0 960 400">','<rect width="960" height="400" fill="white"/>','<text x="20" y="30" font-family="sans-serif" font-size="18">G3 REAR section — parametric height reservation, no case design</text>']
    y=65
    inner_layer=next(l for l in res['candidates'][0]['stacks']['baseline'][0]['layers'] if l['id']=='rear_inner')
    for title,value,color in [('Carrier lower web',c['lower_web_mm'],'#ddd'),('G2 inner clearance + component + joint budget',inner_layer['thickness_mm'],'#c5b3dc'),('REAR PCB nominal',res['fabrication']['pcb_thickness_mm']['nom'],'#83b796'),('Optical component ceiling',res['height_thresholds']['stack_neutral_skin_max_mm'],'#e7b476'),('Optical clearance / retention and compression',c['optical_clearance_mm'],'#f3dda6'),('Window nominal',next(l['thickness_mm'] for l in res['candidates'][0]['stacks']['baseline'][0]['layers'] if l['id']=='window'),'#a5d3ea')]:
        h=value*55;out += [f'<rect x="35" y="{y:.3f}" width="400" height="{h:.3f}" fill="{color}" stroke="#444"/>',f'<text x="450" y="{y+h/2+4:.3f}" font-family="sans-serif" font-size="12">{html.escape(title)}: {value:.3f} mm</text>'];y+=h
    out += [f'<text x="20" y="345" font-family="sans-serif" font-size="12">Pod depth {c["pod_depth_mm"]:.3f} mm; outside-pod residual {c["caseback_residual_before_wall_mm"]:.3f} mm minus caseback wall.</text>','<text x="20" y="367" font-family="sans-serif" font-size="12">G2 joint remains 0.03 / 0.05 / 0.08 mm; G3 qualification requires ≤0.05 mm. No thickness lever credited.</text>','</svg>']
    return '\n'.join(out)+'\n'

def outputs(res):return {'g3_rear_optical.json':dumps(res),'g3_rear_optical.md':render_md(res),'g3_rear_faces.svg':render_faces(res),'g3_rear_section.svg':render_section(res)}

def validate_model(res):
    assert res['channel_reproduction_pass'] and len(res['optical_channel_map'])==12 and len(res['detector_map'])==4
    assert len(res['candidates'])>=3
    for c in res['candidates']:
        assert len(c['placements'])==46
        for p in c['placements'].values():assert frame_valid(p)
        for st in c['stacks']['with_g3_height_reservations']:
            assert all(k in st for k in ['delta_nominal_mm','delta_rss_mm','delta_linear_mm'])
        if c['outcome']=='RECOMMENDED':assert c['nominal_acceptable'] and not c['corners']['nominal']['hard_failures'] and c['stacks']['zero_delta']
        assert c['nominal_acceptable']==all(c['corners']['nominal']['hard_checks'].values())
    selected=res['selection']['selected_candidate']
    if selected is None:
        assert not any(c['nominal_acceptable'] for c in res['candidates'])
        assert res['verdict']=='G3 FAIL'
    else:assert next(c for c in res['candidates'] if c['id']==selected)['outcome']=='RECOMMENDED'
    assert not res['acceptance']['10']['satisfied']
    assert res['g4_handoff']['conservative_radial_margin_mm']==-.95 and res['g4_handoff']['x25_conservative_cover_fit_mm']==-1.1

def self_tests(res):
    # Use the same geometry predicates and transform checker as production, on injected faults.
    c=copy.deepcopy(res['candidates'][0]);a,b='D401','D403'
    original=c['placements'][a]['courtyard']['rear_mm'];injected=copy.deepcopy(original)
    assert overlap(original,injected),'Courtyard overlap injection not caught'
    assert not overlap(rect(0,0,1,1),rect(1,0,2,1)),'Abutting courtyard incorrectly rejected'
    path=copy.deepcopy(c['corners']['nominal']['analog']['paths'][0]);path['vias']=1
    assert not path_valid(path,load(MECH/'inputs/g3_rear_optical.json')['limits']['pd_path_mm']),'PD_IN via injection not caught'
    shield=c['corners']['nominal']['analog']['shield_regions']['U12'][0]['rear_mm']
    injected_loop=grow(shield,.1);assert overlap(injected_loop,shield),'LED loop / shield injection not caught'
    p=c['placements']['D401'];wrong=[100+p['xy'][0],100+p['xy'][1]]
    if abs(p['xy'][0])<EPS:wrong=[wrong[0]+1,wrong[1]]
    mutant=copy.deepcopy(p);mutant['assembly_xy_mm']=wrong
    assert not frame_valid(mutant),'Mirrored transform injection not caught'
    assert gap(rect(0,0,1,1),rect(2,0,3,1))==1
    assert abs(area(clip(rect(0,0,2,2),rect(1,1,3,3)))-1)<EPS
    concave=[[0,0],[3,0],[3,1],[1,1],[1,3],[0,3]];probe=rect(2,2,2.5,2.5)
    pieces=polygon_pieces(concave)
    assert abs(sum(area(p) for p in pieces)-5)<EPS
    assert min(gap(p,probe) for p in pieces)==1 and gap(hull(concave),probe)==0,'Hull must not replace ordered polygon'
    assert abs(sum(area(p) for p in polygon_pieces([[0,0],[2,2],[0,2],[2,0]]))-2)<EPS,'Self-crossing even-odd fill'
    court=rect(-1,-1,1,1);fixed=[rect(-.2,-.2,.2,.2)];sensitive=[rect(.3,-.2,.5,.2)]
    assert clearance(fixed,sensitive,court)>.5 and clearance(fixed,sensitive)<.5,'Only owning package is exempt'
    outside=[rect(1.01,-.2,1.1,.2)];shield_outside=[rect(1.3,-.2,1.5,.2)]
    assert clearance(outside,shield_outside,court)<.5,'Exemption leaked beyond boundary'
    crossing=[rect(.9,-.2,1.4,.2)]
    assert clearance(crossing,shield_outside,court)==0,'Discretionary boundary crossing not caught'
    assert gap(rect(0,0,.254,.254),rect(.7,0,1,.254))<.5
    assert .7-.127>.5,'Pad-centre metric would incorrectly pass the extent fixture'
    base=next(c for c in res['candidates'] if c['id']=='G3-B')['corners']['nominal']['analog']
    for afe in AFES:
        led4=next(l for l in base['led_loops'] if l['afe']==afe and l['led']==4)
        led5=next(l for l in base['led_loops'] if l['afe']==afe and l['led']==5)
        assert led4['passes_no_intersection'] and led4['passes_aggressor_gap']
        assert .36<led5['ordered_polygon_gap_mm']<.38 and led5['shield_gap_mm']<.5,'Real LED5 failure lost'
    entries={x['target']:x for x in base['vled_entries']}
    assert entries['U12.A1']['selected_orientation']=='horizontal-first'
    assert entries['U13.A1']['selected_orientation']=='vertical-first'
    for e in entries.values():
        assert len(e['alternatives'])==2 and e['pass_check']
        assert e['selected_orientation']==min(e['alternatives'],key=lambda x:x['rank'])['orientation']
    brief=(MECH/'G3_BRIEF.md').read_text()
    assert {d['id'] for d in res['owner_decisions']}=={'OD-G3-ENTRY','OD-G3-SIDE','OD-G3-RECORD','OD-G3-MAX86141-PKG'}
    assert all(d['verbatim'] in brief for d in res['owner_decisions'])
    return ['courtyard_overlap','abutting_allowed','pd_in_via','led_loop_shield_crossing','mirrored_transform','polygon_gap','polygon_clip',
            'ordered_concavity_not_hull','self_crossing_ordered_loop','package_exemption_scope','outside_boundary_no_waiver',
            'pad_extent_threshold','g3b_led4_clear_led5_fails','both_vled_orientations','owner_decisions_verbatim']

def scope_check():
    allowed={'architecture.md','architecture.json','README.md','tools/arch_diagrams.py','inputs/g3_rear_optical.json','tools/g3_rear_optical.py','generated/g3_rear_optical.json','generated/g3_rear_optical.md','generated/g3_rear_faces.svg','generated/g3_rear_section.svg'}
    files=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith('design/mechanical/') and p[len('design/mechanical/'):] in allowed for p in files),files
    base=json.loads(subprocess.check_output(['git','show','eea49e4:design/mechanical/architecture.json'],cwd=ROOT));current=load(MECH/'architecture.json');assert base['g2']==current['g2']
    old=subprocess.check_output(['git','show','eea49e4:design/mechanical/architecture.md'],cwd=ROOT,text=True);new=(MECH/'architecture.md').read_text()
    pat=r'<!-- G2 GENERATED BEGIN -->.*?<!-- G2 GENERATED END -->'
    assert re.search(pat,old,re.S)[0]==re.search(pat,new,re.S)[0],'Immutable G2 Markdown section changed'

def check_architecture(res):
    a=load(MECH/'architecture.json');assert a['g3']==res,'G3 architecture JSON differs'
    md=(MECH/'architecture.md').read_text();assert architecture_section(res) in md,'G3 architecture Markdown differs'
    assert md.count('<!-- G3 GENERATED BEGIN -->')==md.count('<!-- G3 GENERATED END -->')==1
    for conflict in a['conflicts']:
        status=next(x for x in res['conflict_status'] if x['id']==conflict['id'])
        assert conflict['g3_status']==status['g3_status'] and conflict['g3_evidence']==status['g3_evidence']
    assert res['g2_record'] in (MECH/'README.md').read_text()
    scope_check()

def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ['build','check']:raise SystemExit('usage: g3_rear_optical.py build|check')
    res=build_results();validate_model(res);tests=self_tests(res);files=outputs(res)
    if sys.argv[1]=='build':
        for name,text in files.items():(GEN/name).write_text(text)
    else:
        for name,text in files.items():assert (GEN/name).read_bytes()==text.encode(),'Generated byte difference: '+name
        check_architecture(res)
    print(dumps(dict(status='PASS',engineering_verdict=res['verdict'],selected_candidate=res['selection']['selected_candidate'],self_tests=tests,unsatisfied_acceptance=res['unsatisfied_acceptance'],outputs=list(files))).rstrip())

if __name__=='__main__':main()
