#!/usr/bin/env python3
"""Deterministic G2 planning study. Stdlib only; build writes G2 outputs only.

Geometry is a bounded installation-envelope calculation, not component selection,
placement, or sealing qualification. Unknown vendor data is expressed as requirements.
G1 stack/tolerance and F.Cu edge-crossing functions are imported unchanged.
"""
import hashlib
import itertools
import json
import math
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
MECH = ROOT / 'design/mechanical'
GEN = MECH / 'generated'
sys.path.insert(0, str(MECH / 'tools'))
import mech_model as mm
import g1_scenarios as g1
import arch_diagrams as ad

CORNERS = ('nominal', 'conservative', 'optimistic')
KEY = dict(nominal='nom', conservative='max', optimistic='min')
SPACE = dict(nominal='nom', conservative='min', optimistic='max')
BASE = '168badbab6de1201bb3209902a53fe1e4b874cc9'
REG = 'design/mechanical/inputs/input_register.json'
CLASSES = {'PROJECT_DERIVED', 'PROVISIONAL_ASSUMPTION', 'SUPPLIER_DATA_REQUIRED',
           'MANUFACTURER_VERIFIED', 'OWNER_DECISION'}


def load(p):
    return json.loads(Path(p).read_text(), object_pairs_hook=unique_pairs)


def unique_pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError('duplicate JSON key: ' + k)
        d[k] = v
    return d


def r(v):
    return round(v + 0.0, 3)


def rounded(o):
    if isinstance(o, float):
        return r(o)
    if isinstance(o, dict):
        return {k: rounded(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [rounded(v) for v in o]
    return o


def dumps(o):
    return json.dumps(rounded(o), indent=2, sort_keys=True, ensure_ascii=False) + '\n'


def xy(rad, az):
    t = math.radians(az)
    return [100 + rad * math.sin(t), 100 - rad * math.cos(t)]


def rectgeom(rect):
    return dict(type='rect', rect=rect)


def sect(az, radii):
    return dict(type='sector', az=az, r=radii)


def centre(rect):
    return [(rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2]


def normrad(pt):
    return math.hypot(pt[0] - 100, pt[1] - 100)


def maxrad(rect):
    return max(normrad([x, y]) for x in (rect[0], rect[2]) for y in (rect[1], rect[3]))


class Study:
    def __init__(self):
        self.I = load(MECH / 'inputs/g2_interconnect.json')
        self.A = load(MECH / 'architecture.json')
        self.S = load(MECH / 'inputs/stack_parameters.json')
        self.G = load(MECH / 'inputs/g1_scenarios.json')
        self.H = load(MECH / 'inputs/package_heights.json')
        self.HM = load(GEN / 'main_height_map.json')
        self.Z = load(GEN / 'zstack.json')
        self.P = self.I['parameters']
        self.cov = dict(options=g1.cover_options(self.G, self.S),
                        levers={x['id']: x for x in self.G['levers']})
        self.heights = g1.lever_heights(self.G, self.H)
        self.options = {o['id']: o for o in self.I['options']}
        self.fp = {f['ref']: f for f in self.HM['main_footprints']}
        self.res = {v['id']: v for v in self.A['reservations']}
        self.edge = ad.derive_edge_crossings(self.A, self.Z, self.HM)
        self.pockets = load(ROOT / 'design/placement/phase1_placement.json')['battery_carrier_cavities_required']
        g1result=g1.build_results()
        self.g1rows = {s['id']: s for s in g1result['scenarios']}
        self.web_handling_clearance=g1result['deterministic_checks']['fpc_underrun_lower_web']['requirement_mm']-self.S['radial']['parameters']['t_fpc']['max']
        self.hstack = {k: sum([self.P['mated_mm'][k], self.P['stiffener_mm'][k],
                              self.P['solder_mm'][k], self.S['radial']['parameters']['t_fpc'][k]])
                       for k in ('min', 'nom', 'max')}
        self.groups = {}
        for o in self.options.values():
            self.groups.setdefault(o['interface'], []).append(o['id'])
        # Check the live PCB; this also detects stale cached geometry, not only counts.
        live = mm.parse_board(ROOT / 'sportwatch_revA.kicad_pcb')
        assert len(live) == len(self.fp)
        for f in live:
            cached = self.fp[f['ref']]
            for k in ('ref', 'side', 'x', 'y', 'rot', 'footprint', 'value', 'courtyard_bbox'):
                assert rounded(f[k]) == rounded(cached[k]), (f['ref'], k)

    def g1_eval(self, levers, delta=None):
        return g1.scenario_eval(self.G, self.S, self.HM, self.H, self.cov,
                               self.G['baseline_cover_option'], levers, self.heights, delta)

    def tolerances(self, levers):
        return g1.scenario_tolerances(self.G, self.S,
                                    self.cov['options'][self.G['baseline_cover_option']], levers)

    def reference(self):
        levers = next(s['levers'] for s in self.G['scenarios'] if s['id'] == 'G1-K2')
        n = self.g1_eval(levers)[0]
        d = self.tolerances(levers)
        sens = {k: r(self.g1_eval(levers, {k: v})[0] - n) for k, v in d.items()}
        out = dict(nominal_mm=r(n), rss_mm=r(n + math.sqrt(sum(v*v for v in sens.values()))),
                   linear_mm=r(self.g1_eval(levers, d)[0]))
        expected = {k: self.I['reference'][k] for k in out}
        assert out == expected, 'STOP G2-K2-REF mismatch: %r != %r' % (out, expected)
        for k, gk in [('nominal_mm', 'T_nominal_mm'), ('rss_mm', 'T_rss_mm'), ('linear_mm', 'T_worst_linear_mm')]:
            assert out[k] == self.g1rows['G1-K2'][gk]
        return dict(out, id='G2-K2-REF', body_mm=r(n-self.G['h_pod_reported_mm']),
                    h_pod_mm=self.G['h_pod_reported_mm'], evidence_class='PROJECT_DERIVED',
                    source='Imported g1.scenario_eval / scenario_tolerances; independently recomputed G1-K2',
                    reference_pass=True)

    def stack(self, allocation, high=False, stack_override=None, verified_max=False):
        rear = self.options[allocation['J1502']]
        levers = ['P-0402'] + ([rear['lever']] if rear.get('lever') else [])
        vals = {oid: self.hstack['max' if high else 'nom'] for oid in allocation.values()
                if self.options[oid]['interface'] in ('J1501','J201','J202') or
                self.options[oid].get('termination') == 'connector'}
        if stack_override:
            vals.update({k:v for k,v in stack_override.items() if k in vals})
        d = self.tolerances(levers)
        # Full positive planning range treated as uncertainty, not a hidden fixed design choice.
        # G1 h_rear_inner tolerance is still retained: deliberately conservative double coverage.
        extras = {'connector:' + oid: 0. if verified_max else max(0., self.hstack['max']-v) for oid, v in vals.items()}
        if rear.get('termination') == 'tail':
            extras['tail_joint'] = 0 if high else self.P['tail_joint_mm']['max']-self.P['tail_joint_mm']['nom']
        d.update(extras)

        def ev(delta=None):
            delta = delta or {}
            base_delta = {k: v for k, v in delta.items() if k not in extras}
            _, _, _, p, hf, hb = self.g1_eval(levers, base_delta)
            if allocation.get('U7/LRA') == 'U7-B.Cu':
                hb = max(hb, self.fp['U7']['seated_max'])
            for oid, v in vals.items():
                opt = self.options[oid]
                h = v + delta.get('connector:'+oid, 0)
                if opt['interface'] == 'J1502':
                    p['h_rear_inner'] = max(h, self.heights['bcu_0402_high_cv_mm']) + base_delta.get('h_rear_inner', 0)
                elif opt['side'] == 'B.Cu':
                    hb = max(hb, h)
                else:
                    hf = max(hf, h)
            if rear.get('termination') == 'tail':
                p['h_rear_inner'] += (self.P['tail_joint_mm']['max']-self.P['tail_joint_mm']['nom'] if high else 0)
                p['h_rear_inner'] += delta.get('tail_joint', 0)
            layers = mm.eval_stack(p, hf, hb)
            return sum(l['thickness_mm'] for l in layers), layers, p, hb
        n, layers, p, hb = ev()
        sensitivities = {k: r(ev({k: v})[0]-n) for k, v in d.items()}
        rss = n + math.sqrt(sum(v*v for v in sensitivities.values()))
        lin = ev(d)[0]
        credible = all(self.cov['levers'][l]['status'] == 'CREDIBLE_LATER_TASK' for l in levers)
        lim = self.I['limits']
        return dict(evidence_class='PROJECT_DERIVED', nominal_mm=r(n), rss_mm=r(rss), linear_mm=r(lin),
                    body_mm=r(n-self.G['h_pod_reported_mm']), h_pod_mm=self.G['h_pod_reported_mm'],
                    body_rss_mm=r(rss-self.G['h_pod_reported_mm']), body_linear_mm=r(lin-self.G['h_pod_reported_mm']),
                    nominal_compliant=n<=lim['nominal_mm']+1e-9, rss_compliant=rss<=lim['rss_mm']+1e-9,
                    compliant=credible and n<=lim['nominal_mm']+1e-9 and rss<=lim['rss_mm']+1e-9,
                    credible_levers_only=credible, levers=levers, credited_gated_levers=[],
                    back_zone_mm=next(x['thickness_mm'] for x in layers if x['id']=='back_zone'),
                    h_rear_inner_mm=r(p['h_rear_inner']), governing_back_height_mm=r(hb),
                    layers=layers, tolerance_deltas_mm=d, tolerance_sensitivities_mm=sensitivities,
                    delta_G1_S4_mm=r(n-self.g1rows['G1-S4']['T_nominal_mm']),
                    delta_G1_K2_mm=r(n-self.g1rows['G1-K2']['T_nominal_mm']))

    def window(self, opt):
        if opt['interface']=='C901/C903':
            boxes=[self.fp[x]['courtyard_bbox'] for x in ('C901','C903')]
            return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
        if opt.get('retained_ref'):
            return self.fp[opt['retained_ref']]['courtyard_bbox']
        return opt.get('window_rect_mm')

    def geometry(self, opt):
        """Equal geometry treatment for front/back options; all overlaps disclosed."""
        rect = self.window(opt)
        interface = opt['interface']
        side = opt['side']
        if rect is None:
            return self.rear_geometry(opt)
        mid = centre(rect)
        azi = ad.az_of(*mid)
        az_window = ad.rect_corner_az(rect)
        src = opt.get('retained_ref', 'U7' if interface=='U7/LRA' else '')
        hits = [f for f in self.fp.values() if f['side']==side and f['ref'] != src and
                ad.interiors_overlap(rectgeom(rect), rectgeom(f['courtyard_bbox']))]
        pocket_hits = [i for i, p in enumerate(self.pockets) if side=='B.Cu' and
                       ad.interiors_overlap(rectgeom(rect), rectgeom(p['rect']))]
        # Retained components keep their approved envelopes; their existing neighbours are evidence.
        failures = []
        if maxrad(rect)>self.S['radial']['parameters']['R_main']['nom']:
            failures.append('window extends beyond MAIN')
        if hits and not opt.get('retained_ref'):
            failures.append('occupied body window: '+','.join(f['ref'] for f in hits))
        if pocket_hits and not opt.get('retained_ref'):
            failures.append('body intersects existing carrier pocket')
        out = dict(evidence_class='PROJECT_DERIVED', window_rect_mm=rect, centre_xy_mm=mid,
                   azimuth_window_deg=az_window, max_body_radius_mm=maxrad(rect),
                   courtyard_hits=[f['ref'] for f in hits], carrier_pocket_hits=pocket_hits,
                   nominal_failures=failures, corners={}, overlaps=[], supplier_requirements=[])
        if 'route_kind' not in opt:
            return self.retained_geometry(opt, out)
        riser = opt['riser_az_deg']; az = sum(riser)/2
        body_g = rectgeom(rect)
        for c in CORNERS:
            k, sk = KEY[c], SPACE[c]
            p = self.Z['radial']['corners'][c]['parameters']
            b = self.edge['budget'][c]
            rc = self.Z['radial']['corners'][c]['checks']
            rv = rc['R_channel_inner']['value_mm']
            pack = rc['R_pack_max']['value_mm']
            t, clear, rb = p['t_fpc'], p['c_fpc'], p['R_bend_min']
            hst = self.fp['U7']['seated_max'] if interface=='U7/LRA' else self.hstack[k]
            hb = max(self.heights['bcu_0402_high_cv_mm'], hst if side=='B.Cu' else 0)
            gap = max(self.S['parameters']['t_carrier_web'][sk], hb+self.S['parameters']['c_back'][sk])
            bz = gap+self.S['parameters']['t_insulator'][sk]
            ang=self.P['approach_angle_margin_deg'][k];hw=self.P['approach_half_width_mm'][k]
            approach = sect([min(azi,az)-ang,max(azi,az)+ang], [max(0,normrad(mid)-hw),rv])
            if interface=='J201' and side=='F.Cu':
                ar=self.P['fcu_overpass_radius_mm'][k]
                approach=sect([min(azi,az)-ang,max(azi,az)+ang], [ar-hw,ar+hw])
            approach_hits = [f for f in self.fp.values() if f['side']==side and f['ref']!=src and
                             ad.interiors_overlap(approach,rectgeom(f['courtyard_bbox']))]
            hparts = max([f['seated_max'] or 0 for f in approach_hits]+[0])
            exit_h = self.P['lra_lead_exit_mm' if interface=='U7/LRA' else 'exit_mm'][k]
            if side=='F.Cu':
                # Reuse the exact G1 circular bend inset and land ceiling. A raised approach is
                # an explicit additional pair of bends, not an assumption of a high vendor mouth.
                run_h=max(exit_h,hparts+clear)
                inset=ad._bend_inset(rb,run_h)
                rv_used=max(p['R_main']+rb-inset,rv)
                margin=rc['R_case_inner']['value_mm']-rv_used-t-clear
                rmax=None; hollow=None
                fit=b['h_max_mm']-run_h
            else:
                run_h=exit_h
                rv_used=rv
                # Pack top is z=0. Inner turn connects (xv-R,g) to (xv,g-R).
                # For d=xv-xpack, g=horizontal flex underside clearance above pack,
                # corner lies inside hollow when (R-d)^2+(R-g)^2<=R^2,
                # or is outside the curved quadrant (d>=R or g>=R).
                d=rv_used-pack
                g=gap-run_h-t-clear
                rmax=(d+g+math.sqrt(2*d*g)) if d>=0 and g>=0 else 0.
                hollow=(g>=0 and (d>=rb or g>=rb or (rb-d)**2+(rb-g)**2<=rb**2+1e-9))
                margin=rc['margin_straight_run']['value_mm']
                fit=gap-run_h-t-clear
            width=((opt['positions']-1)*self.P['sensor_pitch_mm'][k]+2*self.P['sensor_edge_margin_mm'][k]
                   if interface=='J1501' else self.P['harness_width_mm'][k])
            arc_slot=math.radians(riser[1]-riser[0])*rv_used
            width_margin=arc_slot-width-2*clear
            # Front-gap battery route replaces the long annulus BATT_TAIL with an inboard arc.
            # Other rear links use an arc outside the REAR envelope, then a local annulus rise.
            rear_radius=self.A['rear_module']['envelope_results']['D_env_double_mm'][c]/2
            source_r=rear_radius if interface=='J1501' else opt['source_radius_mm']
            underrun=max(0,rv_used-source_r)
            arc_radius=(self.P['fcu_overpass_radius_mm'][k] if interface=='J201' and side=='F.Cu'
                        else self.P['lra_route_radius_mm'][k] if interface=='U7/LRA' else opt['source_radius_mm'])
            arc_angle=(abs(azi-az) if interface=='J201' and side=='F.Cu' else abs(opt['source_az_deg']-az))
            arc_length=math.radians(arc_angle)*arc_radius
            vertical=(sum(self.S['parameters'][q][sk if q in ('c_axial','t_lower_web') else k]
                          for q in ('t_pack_nom','tol_pack_thick','g_axial','c_axial','t_lower_web'))
                      if opt['route_kind']!='battery' else self.S['parameters']['c_axial'][sk])
            if side=='F.Cu': vertical+=self.S['parameters']['t_main'][sk]+bz+run_h
            radial_run=max(0,rv_used-normrad(mid))
            # Conservative length upper bound: full orthogonal runs + arcs (no tangent deductions).
            bends=2+(2 if arc_angle>0.001 else 0)+(2 if run_h>exit_h+1e-9 else 0)
            length=underrun+arc_length+vertical+radial_run+bends*math.pi/2*(rb+t/2)
            hinge=xy(p['R_main'],az)
            fold_length=2*math.dist(mid,hinge)+math.pi*(rb+t/2)
            web=self.S['parameters']['t_lower_web'][sk]
            web_margin=web-t-self.web_handling_clearance
            lift=max(0,run_h-exit_h)
            jog_angle=math.acos(max(-1,min(1,1-lift/(2*rb)))) if lift else 0
            jog_run=2*rb*math.sin(jog_angle) if lift<=2*rb else 2*rb
            jog_space=max(0,rv_used-maxrad(rect))
            if opt.get('mouth_direction')=='inboard':
                inner=normrad([min(max(100,rect[0]),rect[2]),min(max(100,rect[1]),rect[3])])
                jog_space=inner-self.P['fcu_overpass_radius_mm'][k]
            corner=dict(raised_approach_jog_horizontal_required_mm=jog_run,raised_approach_jog_available_mm=jog_space,raised_approach_jog_margin_mm=jog_space-jog_run,back_zone_mm=bz,h_stack_mm=hst,exit_height_mm=exit_h,
                        approach_height_mm=run_h,approach_parts=[f['ref'] for f in approach_hits],
                        approach_part_height_mm=hparts,vertical_gap_margin_mm=fit,
                        R_bend_mm=rb,R_bend_max_mm=rmax,pack_corner_inside_hollow=hollow,
                        straight_radial_margin_mm=rc['margin_straight_run']['value_mm'],
                        actual_radial_margin_mm=margin,land_h_max_mm=b['h_max_mm'],
                        flat_exit_margin_mm=b['margin_flat_exit_mm'],
                        mouth_radius_max_mm=b['R_mouth_max_mm'],
                        channel_inner_radius_mm=rv_used,conductor_width_mm=width,
                        riser_arc_available_mm=arc_slot,riser_width_margin_mm=width_margin,
                        installed_length_excluding_service_mm=length,bend_count=bends,
                        underrun_mm=underrun,vertical_run_mm=vertical,annulus_arc_mm=0.,
                        rear_or_front_arc_mm=arc_length,radial_approach_mm=radial_run,
                        fold_length_required_mm=fold_length if side=='B.Cu' else 0.,
                        fold_slack_margin_mm=self.P['service_slack_mm'][sk]-fold_length if side=='B.Cu' else None,
                        lower_web_remaining_mm=web_margin,
                        lower_web_groove_margin_mm=web_margin-self.P['collar_clearance_mm'][k],
                        pack_corner_model=dict(d_mm=rv_used-pack,g_mm=fit) if side=='B.Cu' else None)
            out['corners'][c]=corner
            if c=='nominal':
                for key in ['actual_radial_margin_mm','vertical_gap_margin_mm','riser_width_margin_mm','raised_approach_jog_margin_mm']:
                    if corner[key]<-1e-9: failures.append(key+' < 0')
                if side=='B.Cu' and not hollow: failures.append('pack corner outside bend hollow')
                if side=='B.Cu' and approach_hits: failures.append('B.Cu approach obstructed')
                # Correlated conservative failure is deliberately deferred, not hidden.
                if opt['route_kind']!='battery' and corner['lower_web_groove_margin_mm']<0:
                    failures.append('lower web cannot preserve minimum separating material')
        n=out['corners']['nominal']
        shapes=[('body',body_g,['MAIN']),('riser',sect(riser,[n['channel_inner_radius_mm'],24.05]),['MAIN','BATTERY'])]
        if opt['route_kind'] in ('charger','lra'):
            rad=self.P['lra_route_radius_mm']['nom'] if interface=='U7/LRA' else opt['source_radius_mm']; a0,a1=sorted([opt['source_az_deg'],sum(riser)/2])
            shapes.append(('rear-route',sect([a0,a1],[rad-self.P['harness_width_mm']['nom']/2,rad+self.P['harness_width_mm']['nom']/2]),['REAR']))
        elif opt['route_kind']=='sensor':
            half=math.degrees(math.asin((n['conductor_width_mm']/2+.2)/11.6))
            shapes.append(('lower-web',sect([az-half,az+half],[11.6,n['channel_inner_radius_mm']]),['REAR']))
        else:
            shapes.append(('front-approach' if side=='F.Cu' else 'back-approach',
                           sect([min(azi,az)-self.P['approach_angle_margin_deg']['nom'],max(azi,az)+self.P['approach_angle_margin_deg']['nom']],[self.P['fcu_overpass_radius_mm']['nom']-self.P['approach_half_width_mm']['nom'],self.P['fcu_overpass_radius_mm']['nom']+self.P['approach_half_width_mm']['nom']]),['MAIN']))
        critical={'GNSS_RAD','BLE_RAD','WIFI_RAD','MAG_CLEAR','SUP_SW','SUP_SE','SUP_NE','SW1','SW2','SW3','SW4','SW5'}
        for region,g,z in shapes:
            for res in self.res.values():
                if not set(z)&set(res['z_levels']) or not ad.interiors_overlap(g,res['geometry']): continue
                rid=res['id']
                disposition='Existing planning envelope; see interface-specific assembly and Z separation.'
                if rid=='DISP_LAND': disposition=('Opposite PCB face; no land crossing.' if side=='B.Cu' else 'G1 land ceiling and actual positive radial margin required; fold interruption remains supplier-gated.')
                elif rid=='LRA': disposition='Lower-web groove and actuator lie on different Z faces; supplier actuator intrusion into groove must be zero; minimum residual material checked.'
                elif rid in ('FPC_UNDER','CHG_ROUTE'):
                    disposition='Overlapping plan projection: sensor is inside lower web; charger/LRA leads are below it in separate perimeter channels. Z clearance checked in shared-corridor results; no carrier support removed.'
                elif rid in critical:
                    disposition='BLOCKED at common planning Z; supplier/next-gate refinement cannot be silently assumed.'
                    # Existing body of retained U7 is not a new intrusion. Front approach is above
                    # a support only if it stays inboard; detector tests that explicitly.
                    if not (region=='body' and interface=='U7/LRA'):
                        failures.append(region+' overlaps '+rid)
                out['overlaps'].append(dict(region=region,reservation=rid,disposition=disposition))
        out['path_regions']=[dict(name=k,geometry=g,z_levels=z,section_channel='inside-lower-web' if k=='lower-web' else 'below-lower-web' if k=='rear-route' else 'MAIN-'+side) for k,g,z in shapes]
        out['main_edge_crossings']=int(side=='F.Cu')
        out['display_land_interactions']=int(side=='F.Cu')
        out['seal_band_crossings']=int(interface=='J202') # fixed separately sealed contact feedthrough
        out['button_bore_crossings']=sum(1 for o in out['overlaps'] if o['reservation'].startswith('SW') and o['reservation']!='SWD' and o['region']=='riser')
        out['mating_direction']=('Insert radially outward into inward-facing J201 mouth; actuate from F.Cu' if opt.get('mouth_direction')=='inboard' else 'Insert radially inward into outward-facing mouth; actuate latch from '+side)
        out['exit_direction']=('Inboard toward the raised front-gap arc, then SW riser; no long annulus tail' if opt.get('mouth_direction')=='inboard' else 'Radially outward toward riser azimuth; inward-facing branch at REAR/pack end')
        out['mated_z_range_mm']=({k:self.fp['U7']['seated_max'] for k in self.hstack} if interface=='U7/LRA' else self.hstack)
        if interface=='U7/LRA':
            out['mating_direction']='Solder insulated lead pair on '+side+' with strain relief; no demountable latch'
            out['exit_direction']='Radially outward toward the allocated LRA riser'
            out['mated_z_basis']='Governing seated U7 height; lead attachment is a separate solder allowance, not a connector'
            out['lead_attachment_allowance_mm']=self.P['lra_lead_exit_mm']
        out['book_fold']=dict(required=side=='B.Cu',hinge_axis='tangent to MAIN edge at riser centre azimuth',
                              hinge_centre_xy_mm=xy(23,sum(riser)/2),
                              slack_location='External assembly jig during turn; separated lower-web service pocket after closing',
                              motion='MAIN B.Cu-up; mate cold in S1, rotate 180 degrees, lower onto carrier without dragging the pack',
                              length_model='2*distance(mouth-centre, tangent hinge)+pi*(R_bend+t/2); additional service slack, excluded from installed length',
                              storage_requirement='No doubling inside the thin annulus; pocket area/height in supplier requirements',
                              access=dict(S0='both sides on jig',S1='B.Cu-up before fold' if side=='B.Cu' else 'display absent',S2='reverse to S1 after battery isolation',S3='open caseback then reverse S2'))
        target=self.fp[opt['routing_target_ref']]
        manhattan=abs(mid[0]-target['x'])+abs(mid[1]-target['y'])
        out['routing']=dict(evidence_class='PROJECT_DERIVED',pad_side=side,
                            via_transition_estimate=opt['signal_positions'] if side=='B.Cu' else 0,
                            new_onboard_manhattan_mm=manhattan,
                            escape_region_mm2=(rect[2]-rect[0])*(rect[3]-rect[1]),
                            current_positions=([21,22,23] if interface=='J1501' else [1,3] if interface=='J201' else [1,2]),
                            entry_protection='U1201/D1201 must sit immediately behind the new MAIN entry; preserve series+TVS+ESD_ENTRY, then protected VBUSIN to U201.21' if opt.get('entry_protection_relocation') else 'Preserve existing entry-side protection architecture',
                            scope='Estimate only; no net routing or placement. Return vias and decoupler relocation still required in later implementation. U7 control transitions cover SDA, SCL, NRST and TRIG_INTZ; REG capacitor remains local to U7, VSYS/GND require power/return connections.')
        out['mirrored_physical_position_requirement']=(('Re-derive all 24 mating positions and the 13 logical nets; physical permutation may reverse, logical net assignments must not.' if interface=='J1501' else 'Re-derive opposite-face physical pad/lead order. Preserve J201 GND/NTC/VBAT, J202 power/return or U7 ball/lead nets as applicable; verify continuity from actual mating view.') if side=='B.Cu' else 'Verify mating-view map; logical positions unchanged.')
        out['supplier_requirements']=[dict(id=opt['supplier'],evidence_class='SUPPLIER_DATA_REQUIRED',
            acceptance=dict(body_width_max_mm=rect[2]-rect[0],body_depth_max_mm=rect[3]-rect[1],
                            conductor_thickness_max_mm=self.edge['budget']['nominal']['t_allow_straight_mm'],
                            riser_azimuth_deg=riser,bend_radius_max_mm=n['R_bend_max_mm'] if side=='B.Cu' else n['R_bend_mm'],
                            exit_height_min_mm=n['approach_part_height_mm']+.2 if side=='F.Cu' else None,
                            exit_height_max_mm=n['land_h_max_mm'] if side=='F.Cu' else n['back_zone_mm']-.05-.12-.2,
                            service_fold_length_min_mm=n['fold_length_required_mm'],
                            service_pocket_height_min_mm=2*.2+.3,
                            service_pocket_plan_length_min_mm=n['fold_length_required_mm']/2+2*n['R_bend_mm']),
            note='Acceptance envelope only; no actual vendor dimensions asserted. Round wires must satisfy the same thickness/channel and bend limits.')]
        return out

    def rear_geometry(self,opt):
        out=dict(evidence_class='PROJECT_DERIVED',side='REAR-inner',nominal_failures=[],corners={},overlaps=[],
                 window_rect_mm=None,azimuth_window_deg=self.options['J1501-F.Cu']['riser_az_deg'],
                 mating_direction='Bond under process fixture' if opt['termination']=='tail' else 'Radial insertion, latch accessed before carrier',
                 exit_direction='toward J1501 south riser',main_edge_crossings=0,display_land_interactions=0,
                 seal_band_crossings=0,button_bore_crossings=0,
                 flex_path='radially outward in lower-web groove to the common sensor riser; counted once in J1501 installed length',
                 service='Replace REAR+bonded tail as a unit; J1501 is its only demountable joint' if opt['termination']=='tail' else 'Demount J1501, withdraw module, then release inner-face J1502 before removing carrier',
                 supplier_requirements=[],routing=dict(via_transition_estimate=0,new_onboard_manhattan_mm=0,
                 scope='REAR digital/power inner-face attach only; sensitive analog remains skin-facing; detailed REAR placement is G3'))
        for c in CORNERS:
            k=KEY[c]; rr=self.A['rear_module']['envelope_results']['D_env_double_mm'][c]/2
            h=(self.heights['bcu_0402_high_cv_mm'] if opt.get('lever')=='INNER-TAIL' else self.heights['inner_0201_mm'])+self.P['tail_joint_mm'][k]
            if opt['termination']=='connector':h=max(self.hstack[k],self.heights['bcu_0402_high_cv_mm'])
            rad=self.Z['radial']['corners'][c]['checks']['R_channel_inner']['value_mm']
            out['corners'][c]=dict(h_rear_inner_mm=h,radial_attach_window_mm=[rr-2,rr],
               installed_length_excluding_service_mm=max(0,rad-rr),underrun_mm=max(0,rad-rr),bend_count=0,
               actual_radial_margin_mm=self.Z['radial']['corners'][c]['checks']['margin_straight_run']['value_mm'])
        out['mated_z_range_mm']={k:out['corners'][c]['h_rear_inner_mm'] for c,k in [('optimistic','min'),('nominal','nom'),('conservative','max')]}
        out['access']=dict(S0='REAR subassembly in attach fixture',S1='Mate/bond before insertion into carrier',S2='Inner face inaccessible; withdraw REAR after disconnecting J1501',S3='Open and isolate before reversing to S1')
        out['supplier_requirements']=[dict(id=opt['supplier'],evidence_class='SUPPLIER_DATA_REQUIRED',
            acceptance=dict(joint_thickness_max_mm=self.P['tail_joint_mm']['max'],
                            fpc_thickness_max_mm=self.S['radial']['parameters']['t_fpc']['max'],
                            h_rear_inner_max_mm=out['mated_z_range_mm']['max'],positions=24),
            note='Hot-bar/ACF process qualification and peel/pull/rework limits; verify no tall inner-face capacitors for INNER-0201. No sensitive REAR-local path crosses the boundary.')]
        return out

    def retained_geometry(self,opt,out):
        ref=opt['retained_ref'];f=self.fp[ref]; interface=opt['interface']
        out.update(main_edge_crossings=0,display_land_interactions=int(interface=='J1'),seal_band_crossings=0,
                   button_bore_crossings=0,mating_direction='Z insertion from F.Cu in S0/S1' if interface in ('J1','J1301') else 'soldered; no mating operation',
                   exit_direction='west display fold' if interface=='J1' else 'not applicable: probe or soldered component',
                   flex_path='west DISP_FPC envelope' if interface=='J1' else 'not applicable',
                   routing=dict(pad_side=opt['side'],via_transition_estimate=0,new_onboard_manhattan_mm=0,
                                scope='Retained. P-0402 later footprint/BOM task only.'),
                   mated_z_range_mm={k:f['seated_max'] for k in ('min','nom','max')})
        for c in CORNERS:
            k=KEY[c]; b=self.edge['budget'][c]
            row=dict(installed_length_excluding_service_mm=0.,bend_count=0,
                     actual_radial_margin_mm=self.Z['radial']['corners'][c]['checks']['margin_straight_run']['value_mm'])
            if interface=='J1':
                rb=self.S['radial']['parameters']['R_bend_min'][k]
                tf=self.S['parameters']['t_display_fpc_fold'][k]
                radial=self.Z['radial']['corners'][c]['checks']['R_case_inner']['value_mm']-22.65
                row.update(fold_height_budget_mm=b['front_gap_mm']-.8-b['c_mm'],
                           fold_height_assumption_mm=tf,fold_height_margin_mm=b['front_gap_mm']-.8-b['c_mm']-tf,
                           folded_outer_radius_mm=22.65,fold_radial_margin_mm=radial,
                           land_interruption_arc_mm=math.radians(295-269)*21.95,
                           fold_length_min_mm=math.pi*(rb+tf/2),bend_count=1,
                           installed_length_excluding_service_mm=math.dist(centre(out['window_rect_mm']),xy(21.95,282))+math.pi*(rb+tf/2))
            if interface=='J1301':
                gap=self.heights['bcu_0402_high_cv_mm']+self.S['parameters']['c_back'][SPACE[c]]
                row.update(guide_pin_protrusion_max_without_relief_mm=gap-self.P['assembly_clearance_mm'][k],
                           carrier_relief_formula='depth >= max(0, supplier pin protrusion - clearance above); clip outline must fit the reserved probe area or use a bare-board fixture')
            if interface=='C901/C903':row['seated_height_cap_mm']=self.heights['bcu_0402_high_cv_mm']
            out['corners'][c]=row
        out['access']=dict(S0='Bare-board fixture; battery isolated',S1='Visible before display; Tag-Connect requires protrusion acceptance or external raised MAIN fixture',S2='Display blocks front access; return to S1 after isolation',S3='Open caseback, isolate battery, return through S2 to S1')
        if interface=='J1':
            n=out['corners']['nominal']
            out['supplier_requirements']=[dict(id='SR-DISPLAY-FPC',evidence_class='SUPPLIER_DATA_REQUIRED',acceptance=dict(fold_height_max_mm=n['fold_height_budget_mm'],outer_radius_max_mm=22.65,azimuth_deg=[269,295],support_interruption_arc_mm=n['land_interruption_arc_mm'],bend_radius_max_mm=1.2),note='Actual folded cable length and plug position require drawing. Display support must bridge the interruption without loading the fold. J1 rated 50 cycles / planned 25; visible mating precedes closure.')]
        elif interface=='J1301':
            out['supplier_requirements']=[dict(id='SR-TAGCONNECT',evidence_class='SUPPLIER_DATA_REQUIRED',acceptance=dict(protrusion_max_without_relief_mm=out['corners']['nominal']['guide_pin_protrusion_max_without_relief_mm'],probe_relief_window_mm=out['window_rect_mm']),note='No seated Z increment. Probe/guide pins and clip must be withdrawn before S2; if protrusion exceeds threshold use an external S0/S1 raised-MAIN fixture. Carrier relief must remain above the pack/insulator and cannot consume battery clearance; never drill or press into the pack envelope.')]
        elif interface=='C901/C903':
            out['mated_z_range_mm']={k:self.heights['bcu_0402_high_cv_mm'] for k in ('min','nom','max')}
            out['electrical_gate']=self.G['electrical_evidence']
        return out

    def score(self, oid, allocation, geometry, stack_override=None, verified_max=False):
        trial=dict(allocation);trial[self.options[oid]['interface']]=oid
        st=self.stack(trial,stack_override=stack_override,verified_max=verified_max)
        opt=self.options[oid];g=geometry[oid];n=g['corners']['nominal']
        route=g.get('routing',{})
        # Seven ordered criteria; subkeys explicitly retain the order within a criterion.
        return (0, int(not st['compliant']),
                (g['main_edge_crossings'],g['display_land_interactions']),
                (g['seal_band_crossings'],g['button_bore_crossings']),
                (r(n['installed_length_excluding_service_mm']),n['bend_count']),
                (len(opt.get('assembly_actions',[])), -opt.get('service_joints',0)),
                (route.get('via_transition_estimate',0),route.get('new_onboard_manhattan_mm',0),opt.get('routing_changes',0)))

    def allocation(self,geometry):
        # Start by ID, not a lead hypothesis. Repeated coordinate minimisation is followed
        # by an exhaustive fixed-point search to remove traversal-order dependence.
        groups=[k for k in self.groups if len(self.groups[k])>1]
        fixed={k:v[0] for k,v in self.groups.items() if len(v)==1}
        candidates=[]
        for ids in itertools.product(*(self.groups[k] for k in groups)):
            a=dict(fixed,**dict(zip(groups,ids)))
            if any(geometry[i]['nominal_failures'] for i in a.values()):continue
            if not self.stack(a)['compliant']:continue
            stable=True
            for key in groups:
                valid=[i for i in self.groups[key] if not geometry[i]['nominal_failures']]
                if self.score(a[key],a,geometry)!=min(self.score(i,a,geometry) for i in valid):
                    stable=False;break
            if stable:candidates.append(a)
        if not candidates:
            # Preserve the full tradeoff if no acceptable joint allocation exists.
            a=dict(fixed)
            for key in groups:
                a[key]=min(self.groups[key],key=lambda i:(len(geometry[i]['nominal_failures']),i))
            return a,[],False
        candidates.sort(key=lambda a:tuple(a[k] for k in sorted(a)))
        return candidates[0],candidates,True

    def joint_fold(self,allocation,geometry):
        ids=[oid for oid in allocation.values() if self.options[oid]['side']=='B.Cu' and 'route_kind' in self.options[oid]]
        if not ids:return dict(evidence_class='PROJECT_DERIVED',required=False)
        # One rigid MAIN has one rotation axis. Pick the sampled tangent hinge that
        # minimises the longest attached-lead reach; no independent hinges are claimed.
        def needs(az):
            hinge=xy(self.S['radial']['parameters']['R_main']['nom'],az)
            return {oid:2*math.dist(geometry[oid]['centre_xy_mm'],hinge)+math.pi*(self.S['radial']['parameters']['R_bend_min']['nom']+self.S['radial']['parameters']['t_fpc']['nom']/2) for oid in ids}
        az=min(range(360),key=lambda a:(max(needs(a).values()),sum(needs(a).values()),a))
        lengths=needs(az)
        return dict(evidence_class='PROJECT_DERIVED',required=True,common_hinge_az_deg=az,
                    common_hinge_xy_mm=xy(23,az),required_lead_slack_mm=lengths,
                    nominal_service_slack_budget_mm=self.P['service_slack_mm']['nom'],
                    nominal_slack_sufficient=all(n<=self.P['service_slack_mm']['nom'] for n in lengths.values()),
                    scope='Single 180-degree rigid-MAIN rotation in external fixture. Local per-option hinge lengths are lower bounds; these joint lengths govern when multiple B.Cu leads are installed.')

    def thresholds(self,oid,allocation):
        opt=self.options[oid]
        if opt['side']!='B.Cu' or opt['interface'] not in ('J1501','J201','J202'):return None
        # Nominal deterministic height ceiling independent of supplier variability.
        a=dict(allocation);a[opt['interface']]=oid
        st=self.stack(a,stack_override={oid:self.heights['bcu_0402_high_cv_mm']})
        neutral=self.heights['bcu_0402_high_cv_mm']
        hnom=neutral+self.I['limits']['nominal_mm']-st['nominal_mm']
        base_sens={k:v for k,v in st['tolerance_sensitivities_mm'].items() if k!='connector:'+oid}
        base_variance=sum(v*v for v in base_sens.values())
        # RSS cap is a joint constraint on nominal stack and max-minus-nom variation.
        rows=[]
        for hn in sorted(set([neutral,max(neutral,hnom),self.hstack['nom']])):
            n=st['nominal_mm']+max(0,hn-neutral)
            budget=(self.I['limits']['rss_mm']-n)**2-base_variance
            ds=math.sqrt(budget) if budget>=0 and n<=self.I['limits']['rss_mm'] else None
            rows.append(dict(h_stack_nominal_mm=hn,T_nominal_mm=n,
                             max_positive_h_stack_variation_mm=ds,
                             nominal_limit_pass=n<=self.I['limits']['nominal_mm']))
        return dict(evidence_class='PROJECT_DERIVED',K2_reference_neutral_max_h_stack_mm=neutral,
                    K2_neutral_note='With the G1-K2 rear-inner choice. A taller J1502 cannot be cancelled by an imaginary negative back-zone height.',
                    current_rear_choice_K2_neutral_feasible=st['nominal_mm']<=self.reference()['nominal_mm']+1e-9,
                    OD_nominal_max_h_stack_mm=hnom,OD_RSS_joint_acceptance=rows,
                    joint_bend_requirement=self.bend_at_cap(opt,hnom),
                    equation='T = reference with P-0402 + max(0,h_stack-0.65); T_RSS = T + sqrt(sum(imported sensitivity^2)+connector sensitivity^2). Both owner limits apply.',
                    shoulder_variant=dict(evidence_class='SUPPLIER_DATA_REQUIRED',request='SR-BATT-PACK',
                        acceptance='Provide edge-seal/shoulder height relative to protected-pack top. No reduction is credited.',
                        corners=self.shoulder_limits(opt),
                        credited_stack_reduction_mm=0))

    def shoulder_limits(self,opt):
        geom=self.geometry(opt);out={}
        for c,n in geom['corners'].items():
            d=n['pack_corner_model']['d_mm'];gap=n['pack_corner_model']['g_mm'];rb=n['R_bend_mm']
            needed=0 if d>=rb else rb-math.sqrt(max(0,rb*rb-(rb-d)**2))
            out[c]=dict(max_shoulder_protrusion_mm=gap-needed,required_hollow_gap_mm=needed,
                        max_bend_radius_without_shoulder_protrusion_mm=n['R_bend_max_mm'])
        return out

    def bend_at_cap(self,opt,cap):
        p=self.Z['radial']['corners']['nominal']['parameters']
        rc=self.Z['radial']['corners']['nominal']['checks']
        d=rc['R_channel_inner']['value_mm']-rc['R_pack_max']['value_mm']
        rb=p['R_bend_min']
        gmin=0 if d>=rb else rb-math.sqrt(max(0,rb*rb-(rb-d)**2))
        upper=cap+self.S['parameters']['c_back']['nom']-p['t_fpc']-p['c_fpc']-gmin
        return dict(evidence_class='PROJECT_DERIVED',h_stack_cap_mm=cap,
                    required_pack_hollow_gap_min_mm=gmin,exit_height_max_at_stack_cap_mm=upper,
                    bend_radius_mm=rb,note='Simultaneous condition at the stack ceiling. A low connector stack alone is insufficient: supplier mouth height must also meet this limit. Lower stacks tighten the exit-height ceiling one-for-one.')

    def sweep_pcm(self):
        rows=[]
        # Angular sweep only; the body translates rigidly with the pack exit.
        o=self.options['J201-B.Cu'];mid=centre(o['window_rect_mm']);rho=normrad(mid)
        hw=(o['window_rect_mm'][2]-o['window_rect_mm'][0])/2
        hh=(o['window_rect_mm'][3]-o['window_rect_mm'][1])/2
        for az in range(int(self.P['pcm_az_deg']['min']),int(self.P['pcm_az_deg']['max'])+1,5):
            x,y=xy(rho,az);box=[x-hw,y-hh,x+hw,y+hh]
            blocked=[q['id'] for q in self.res.values() if q['id'] in ('SUP_SW','SUP_SE','SW3','MAG_CLEAR','BLE_RAD') and
                     ad.interiors_overlap(rectgeom(box),q['geometry'])]
            rows.append(dict(az_deg=az,window_rect_mm=box,inside_MAIN=maxrad(box)<=23,
                             blocking_reservations=blocked,
                             BATT_TAIL_annulus_length_mm=0,
                             VBAT_Manhattan_to_U201_mm=abs(x-self.fp['U201']['x'])+abs(y-self.fp['U201']['y'])))
        return dict(evidence_class='PROJECT_DERIVED',source='SR-BATT-PCM plausible SW range; no actual PCM exit claimed',rows=rows)

    def shared_corridors(self,allocation,geometry):
        rows=[]
        # Crossings use their actual sectional channel, not the coarse REAR Z label.
        paths=[(k,region) for k,oid in allocation.items() for region in geometry[oid].get('path_regions',[])
               if 'REAR' in region['z_levels']]
        for (ka,ga),(kb,gb) in itertools.combinations(paths,2):
            if ka==kb or not ad.interiors_overlap(ga['geometry'],gb['geometry']):continue
            corners={}
            for c in CORNERS:
                k,sk=KEY[c],SPACE[c]
                t=self.S['radial']['parameters']['t_fpc'][k]
                clear=self.S['radial']['parameters']['c_fpc'][k]
                web=self.S['parameters']['t_lower_web'][sk]
                same_channel=ga['section_channel']==gb['section_channel']
                height=web if same_channel else self.stack(allocation)['h_rear_inner_mm']+self.S['parameters']['c_rear_inner'][sk]
                required=2*t+clear if same_channel else t+clear+self.P['collar_clearance_mm'][k]
                corners[c]=dict(required_height_mm=required,available_channel_mm=height,margin_mm=height-required,
                                max_each_flex_thickness_mm=(height-clear)/2 if same_channel else height-clear-self.P['collar_clearance_mm'][k])
            rows.append(dict(interfaces=[ka,kb],regions=[ga['name'],gb['name']],section_channels=[ga['section_channel'],gb['section_channel']],corners=corners,
              disposition='Sensor remains inside lower web; charger and LRA leads below it outside REAR PCB. Continuous web separates the crossing. Supplier must meet computed channel limits; no hidden Z addition.',
              nominal_pass=corners['nominal']['margin_mm']>=-1e-9))
        return dict(evidence_class='PROJECT_DERIVED',crossings=rows)

    def discovered(self):
        out=[]
        for n in range(1,6):
            rid='SW'+str(n);q=self.res[rid]
            out.append(dict(id=rid,side='F.Cu interface requirement (switch body TBD)',
                            evidence_class='SUPPLIER_DATA_REQUIRED',source='input_register MAIN-TBD / BUTTONS',
                            outcome='CONDITIONAL',azimuth_window_deg=q['az_deg'],radial_window_mm=[21,23],
                            mating_direction='radial pusher through separately sealed case bore',exit_direction='toward switch pads on MAIN',
                            flex_length_mm=0,bend_count=0,mated_z_range_mm=[0,self.edge['budget']['nominal']['h_max_mm']],
                            acceptance=dict(body_height_max_mm=self.edge['budget']['nominal']['h_max_mm'],
                            conservative_height_max_mm=self.edge['budget']['conservative']['h_max_mm'],
                            bore_half_width_deg=7.5,pressure_target_ATM=5),
                            note='No switch selected or placed; supply force/travel/side/height and seal drawing within this envelope. Do not count an unselected switch as a thickness lever.'))
        for rid,ref in [('GNSS_RAD','AE1420'),('BLE_RAD','AE1401'),('WIFI_RAD','AE1410')]:
            q=self.res[rid]
            out.append(dict(id=ref,evidence_class='SUPPLIER_DATA_REQUIRED',outcome='CONDITIONAL',
                side='MAIN F.Cu feed to case radiator; radiator construction TBD',azimuth_window_deg=q['az_deg'],
                window_geometry=q['geometry'],mating_direction='radial into reserved radome',exit_direction='outboard',
                flex_length_mm=None,bend_count=None,mated_z_range_mm=None,
                acceptance=dict(new_interconnect_intrusion_into_radome_mm=0,feed_span_upper_bound_mm=math.dist(q['geometry']['rect'][:2],q['geometry']['rect'][2:]),F_Cu_seated_height_max_mm=self.edge['budget']['nominal']['h_max_mm']),
                note='Feed/cable form and actual length are not known. Preserve entire radiator envelope across Z; no antenna placement/selection in G2. SR-ANTENNAS must supply dimensions before G4.'))
        out.append(dict(id='TP1301-TP1306',evidence_class='PROJECT_DERIVED',source='MAIN PCB + input register',
                        outcome='RECOMMENDED',side='F.Cu',window_geometry=self.res['TP']['geometry'],
                        mating_direction='probe along Z in S0/S1',exit_direction='withdraw before display',
                        flex_length_mm=0,bend_count=0,mated_z_range_mm=[0,0],
                        note='Temporary probe fixture only; no added seated stack.'))
        return out

    def build(self):
        reference=self.reference() # explicit stop before option work if G1 differs
        geometry={oid:self.geometry(opt) for oid,opt in self.options.items()}
        alloc,fixedpoints,feasible=self.allocation(geometry)
        base=self.stack(alloc);hi=self.stack(alloc,high=True)
        base['id']='G2-REVA';hi['id']='G2-REVA-HI'
        rows=[]
        for oid,opt in self.options.items():
            a=dict(alloc);a[opt['interface']]=oid
            st=self.stack(a)
            g=geometry[oid]
            nominal_score=self.score(oid,alloc,geometry)
            alternatives=[v for v in self.groups[opt['interface']] if not geometry[v]['nominal_failures']]
            best=min((self.score(i,alloc,geometry) for i in alternatives),default=None)
            outcomes=[]
            # Supplier extrema can discriminate stack priority. All options receive the same test.
            for k in ('min','nom','max'):
                overrides={i:self.hstack[k] for i,o in self.options.items() if o['interface'] in ('J1501','J201','J202') or o.get('termination')=='connector'}
                scores={i:self.score(i,alloc,geometry,overrides,verified_max=True) for i in alternatives}
                outcomes.append(sorted(i for i,s in scores.items() if s==min(scores.values())) if scores else [])
            supplier_dependent=len({tuple(v) for v in outcomes})>1
            if g['nominal_failures']:
                status='REJECTED';reason='Nominal deterministic geometry fails: '+'; '.join(g['nominal_failures'])
            elif nominal_score==best:
                status='CONDITIONAL' if (supplier_dependent or opt.get('supplier')) and opt['interface']!='U8' else 'RECOMMENDED'
                reason='Lexicographic nominal winner; procurement/assembly gates must meet the numeric envelope.'
            elif any(oid in v for v in outcomes):
                status='CONDITIONAL';reason='Supplier envelope changes the lexicographic winner; retained alternative, not selected at planning nominal.'
            else:
                status='REJECTED';reason='Dominated under the lexicographic rule at all evaluated supplier corners.'
            rows.append(dict(id=oid,interface=opt['interface'],side=opt['side'],outcome=status,reason=reason,
                             selected=alloc[opt['interface']]==oid,acceptable_at_nominal=not g['nominal_failures'],
                             evidence_class='PROJECT_DERIVED',source='g2_interconnect.py geometry + section-6 lexicographic rule',joint_book_fold=self.joint_fold(a,geometry),
                             rank_key=nominal_score,supplier_corner_winners=outcomes,supplier_corner_meaning='Hypothetical VERIFIED MAXIMUM total envelope at min/nom/max. Planning baseline always retains full range uncertainty; a supplier upper bound is not credited until verified.',
                             allocation_stack=st,geometry=g,height_thresholds=self.thresholds(oid,alloc)))
        shared=self.shared_corridors(alloc,geometry)
        # Report unresolved geometry honestly; a software check can pass while engineering exit fails.
        unmet=[]
        if not feasible:unmet.append('No joint allocation passes all nominal geometric checks and the stack limit.')
        if not base['compliant']:unmet.append('G2-REVA is not compliant using credible levers only.')
        if any(not x['nominal_pass'] for x in shared['crossings']):
            unmet.append('Shared lower-web flex crossings exceed nominal groove height; alternatives must be closed before G2 acceptance.')
        for x in self.discovered():
            if x.get('flex_length_mm') is None:
                unmet.append(x['id']+': supplier-controlled feed construction prevents a final length/bend/Z allocation (acceptance 2).')
        verdict=('REV-A STACK OWNER DECISION REQUIRED' if not base['compliant'] else
                 'G2 CONDITIONAL — ENGINEERING GATES OPEN' if unmet else 'G2 COMPLETE — PROVISIONAL ALLOCATION')
        result=dict(schema='sportwatch-g2-result/1',evidence_class='PROJECT_DERIVED',
                    evidence_policy=self.I['evidence_policy'],verdict=verdict,acceptance_complete=not unmet,
                    unsatisfied_acceptance=unmet,allocation=alloc,options=rows,
                    selection=dict(rule=self.I['selection_rule'],method='Exhaustive joint combinations; retain only per-interface lexicographic fixed points with nominal geometry and Rev-A stack passing. Supplier min/nom/max envelope tests preserve conditional alternatives. IDs only break exact ties, all ties disclosed.',
                                   fixed_points=fixedpoints,nominal_feasible=feasible),
                    stacks=[reference,base,hi],connector_stack_range_mm=dict(self.hstack,evidence_class='PROVISIONAL_ASSUMPTION',source='sum of G2 mated + G1 FPC + G2 stiffener + solder planning ranges; no vendor dimensions'),
                    pcm_sweep=self.sweep_pcm(),shared_corridors=shared,discovered_interfaces=self.discovered(),
                    assembly=self.I['assembly'],joint_book_fold=self.joint_fold(alloc,geometry),rf_verification=self.I['rf_verification'],
                    electrical_gate=self.G['electrical_evidence'],limits=self.I['limits'],
                    conservative_handoff=dict(evidence_class='PROJECT_DERIVED',
                      radial_margin_mm=self.Z['radial']['corners']['conservative']['checks']['margin_straight_run']['value_mm'],
                      recipient='G3 REAR integration must carry radial failure to G4 case/outline co-design; not solved by changing side',
                      cover_case_fit=self.g1rows and g1.build_results()['deterministic_checks']['cover_rim']),
                    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                        MECH/'inputs/g2_interconnect.json',MECH/'inputs/g1_scenarios.json',MECH/'inputs/stack_parameters.json',
                        MECH/'inputs/package_heights.json',GEN/'main_height_map.json',GEN/'zstack.json',
                        ROOT/'sportwatch_revA.kicad_pcb',ROOT/'design/placement/phase1_placement.json',
                        ROOT/'design/interfaces/main_rear_interface.json',ROOT/'design/interfaces/charger_harness.json']})
        result['channel_architecture']=self.I['channel_architecture']
        result['service_pocket_check']=self.service_pocket(result)
        if not result['service_pocket_check']['nominal_pass']:
            result['unsatisfied_acceptance'].append('Selected U7 service pocket fails nominal geometric capacity.')
            result['acceptance_complete']=False
            result['verdict']='G2 CONDITIONAL — ENGINEERING GATES OPEN'
        result['supplier_requests']=self.requests(result)
        result['reservations']=self.reservations(result)
        result['conflict_status']=self.conflicts(result)
        return rounded(result)

    def service_pocket(self,result):
        spec=self.I['service_pocket'];r0,r1=spec['radial_mm'];a0,a1=spec['az_deg']
        opt=next(o for o in result['options'] if o['id']=='U7-B.Cu')
        corners={}
        for c in CORNERS:
            k,sk=KEY[c],SPACE[c];p=self.S['radial']['parameters']
            rb=p['R_bend_min'][k];t=p['t_fpc'][k];cl=p['c_fpc'][k]
            width=self.P['harness_width_mm'][k]
            fold=opt['geometry']['corners'][c]['fold_length_required_mm']
            # U-shaped planar loop. Two straights plus semicircle; no Z hairpin.
            tangent=max(0,(fold-math.pi*(rb+t/2))/2)
            need_width=2*rb+t+width+2*cl
            need_length=tangent+rb+width+2*cl
            have_length=math.radians(a1-a0)*(r0+r1)/2
            rr=self.A['rear_module']['envelope_results']['D_env_double_mm'][c]/2
            inner_gap=result['stacks'][1]['h_rear_inner_mm']+self.S['parameters']['c_rear_inner'][sk]
            height=t+cl+self.P['collar_clearance_mm'][k]
            # LRA pocket is below this channel; derive its envelope without consuming optics/window.
            h_lra=inner_gap+self.S['parameters']['t_rear_pcb'][sk]+self.S['parameters']['h_optics_max'][sk]+self.S['parameters']['c_optics'][sk]-height
            corners[c]=dict(required_width_mm=need_width,available_width_mm=r1-r0,width_margin_mm=r1-r0-need_width,
                            required_length_mm=need_length,available_length_mm=have_length,length_margin_mm=have_length-need_length,
                            required_height_mm=height,available_height_mm=inner_gap,height_margin_mm=inner_gap-height,
                            REAR_outline_clearance_mm=r0-rr,LRA_height_max_below_channel_mm=h_lra)
        return dict(evidence_class='PROJECT_DERIVED',source='G2 service_pocket planning envelope and imported stack',
                    geometry=sect(spec['az_deg'],spec['radial_mm']),corners=corners,
                    nominal_pass=all(v>=0 for k,v in corners['nominal'].items() if k.endswith('margin_mm')),
                    note='Planar U loop for selected U7 B.Cu leads; conservative dimensional failure remains a supplier/G3/G4 gate. No vertical hairpin and no pack compression.')

    def requests(self,result):
        out=[]
        for sid in ['SR-FPC-MECH','SR-BATT-PCM','SR-BATT-PACK','SR-CHG-MECH','SR-TAGCONNECT','SR-LRA','SR-BUTTONS','SR-DISPLAY-FPC','SR-ANTENNAS']:
            reqs=[]
            for o in result['options']:
                for q in o['geometry']['supplier_requirements']:
                    if q['id']==sid:reqs.append(dict(option=o['id'],selected=o['selected'],requirements=q['acceptance'],note=q['note']))
                if self.options[o['id']].get('supplier')==sid and o['height_thresholds']:
                    reqs.append(dict(option=o['id'],selected=o['selected'],height_requirements=o['height_thresholds']))
            if sid=='SR-BATT-PACK':
                reqs.append(dict(finished_diameter_max_mm=self.S['radial']['parameters']['D_pack_nom']['nom']+self.S['radial']['parameters']['tol_pack_dia']['nom'],finished_thickness_max_mm=self.S['parameters']['t_pack_nom']['nom']+self.S['parameters']['tol_pack_thick']['nom'],
                                 edge_shoulder_protrusion_budget_mm=0.,note='Nominal envelope acceptance only. Conservative G1 model includes 44.5 diameter and 4.8 thickness; no thinner edge seal credited. Provide signed edge profile and growth limits.'))
            if sid=='SR-FPC-MECH':
                count=len(load(ROOT/'design/interfaces/main_rear_interface.json')['positions'])
                width=self.options['J1501-F.Cu']['window_rect_mm'][2]-self.options['J1501-F.Cu']['window_rect_mm'][0]
                reqs.append(dict(positions=count,logical_nets=13,pitch_class_mm={k:self.P['sensor_pitch_mm'][k] for k in ('min','nom','max')},
                                 pitch_geometric_max_mm=(width-2*self.P['sensor_edge_margin_mm']['max'])/(count-1),
                                 VLED_positions=[21,22,23],equal_share_initial_peak_mA=self.P['vled_peak_mA']['value']/3,
                                 required_rating_each_mA=self.P['vled_position_requirement_mA']['nom'],
                                 recharge_headroom_under_single_contact_full_peak_mA=self.P['vled_position_requirement_mA']['nom']-self.P['vled_peak_mA']['value'],
                                 note='Confirm actual pulse+recharge/current sharing and voltage drop; rating requirement is not measured load. Confirm contact side, mirror map, joint process, outward exit and assembly-cycle limit.'))
            if sid=='SR-BATT-PCM':reqs.append(dict(plausible_exit_range_deg=[self.P['pcm_az_deg']['min'],self.P['pcm_az_deg']['max']],
                nominal_riser_slot_deg=self.options['J201-B.Cu']['riser_az_deg'],accessible_isolation_break_required=True,
                note='State PCM body/exit and 3-pin GND/NTC/VBAT map; no live remating; supplier must fit an accessible pack isolation point or specify a verified cold-service procedure.'))
            if sid in ('SR-CHG-MECH','SR-BUTTONS'):reqs.append(dict(sealing_target_ATM=5,unsealed_face_seal_crossings_allowed=0,note='Issue pressure, cycling, material and force/travel drawings; no seal qualification claimed. Charger feedthrough has its own seal.'))
            if sid=='SR-LRA':reqs.append(dict(service_pocket=result['service_pocket_check'],pocket_az_deg=[165,195],pocket_radial_mm=[12.65,22],intrusion_into_lower_web_groove_max_mm=0,minimum_residual_material_mm=self.P['collar_clearance_mm']['nom'],note='Confirm lead pair, actuator envelope and mount loads. Separate sensor groove from actuator cavity; no pack or optical-stack compression.'))
            if sid=='SR-BUTTONS':reqs.extend(x['acceptance'] for x in result['discovered_interfaces'] if x['id'].startswith('SW'))
            if sid=='SR-ANTENNAS':
                reqs.extend(dict(interface=x['id'],**x['acceptance']) for x in result['discovered_interfaces'] if x['id'].startswith('AE'))
            if sid=='SR-ANTENNAS':reqs.append(dict(interconnect_intrusion_max_mm=0,source='entire GNSS_RAD/BLE_RAD/WIFI_RAD reservations; RF validation required',note='No new antenna cable length can be asserted without a supplier construction.'))
            out.append(dict(id=sid,evidence_class='SUPPLIER_DATA_REQUIRED',status='DRAFTED / ISSUE-READY — OWNER ISSUES',numeric_acceptance=reqs))
        return out

    def reservations(self,result):
        out=[]
        for row in result['options']:
            if not row['selected']:continue
            opt=self.options[row['id']];g=row['geometry']
            for idx,reg in enumerate(g.get('path_regions',[])):
                out.append(dict(id='G2-'+row['id']+'-'+str(idx),class_='PARAMETRIC',
                                evidence_class='PROVISIONAL_ASSUMPTION',source='g2 option '+row['id'],
                                side=row['side'],z_levels=reg['z_levels'],geometry=reg['geometry'],
                                role=reg['name'],note='Planning reservation only; does not alter PCB geometry'))
        out.append(dict(id='G2-U7-SERVICE-POCKET',class_='PARAMETRIC',evidence_class='PROVISIONAL_ASSUMPTION',source='inputs/g2_interconnect.json service_pocket; generated service_pocket_check',side='below lower web',z_levels=['REAR'],geometry=result['service_pocket_check']['geometry'],role='planar service slack',note='Existing rear-inner perimeter Z gap; no vertical hairpin or carrier thinning.'))
        for q in out:
            q['class']=q.pop('class_')
            d=ad.derive_reservations([q])[q['id']]
            q['azimuth_deg']=d['az'];q['radial_mm']=d['r'];q['clock']={'from':ad.clock_str(d['az'][0]),'to':ad.clock_str(d['az'][1])}
        return out

    def conflicts(self,result):
        statuses={}
        for c in self.A['conflicts']:
            cid=c['id']
            if cid.startswith('G2-'):continue
            st='REMAINS_OPEN'
            ev='G2 allocation is provisional; prior geometry/qualification dependency remains. See generated option checks and supplier requirements.'
            if cid.startswith(('C3-','C6-','X10-','X18-','X20-','X23-')):
                st='SUPPLIER_DATA_GATED';ev='Numeric supplier acceptance requirements in G2 supplier requests; conservative geometry/qualification is not closed.'
            elif cid.startswith(('C5-','X11-','X12-')):
                st='DEFERRED_G3';ev='G3 REAR optical/guarded-analog integration, including inner-face attach and lower-web crossings, remains separately authorized work.'
            elif cid.startswith('C9-'):
                st='RESOLVED_BY_G2' if result['stacks'][1]['compliant'] else 'OWNER_DECISION_GATED'
                ev='OD-THICK-REVA applied; see generated G2-REVA nominal/RSS compliance. HI result separately reported; no gated lever credited.'
            elif cid.startswith('C1-'):
                ev='U8 retained F.Cu north. G1 valid necessary bound 18.00 < 21.95; no relocation or GNSS change studied. RF list remains required.'
            elif cid.startswith(('C7-','X14-','X15-','X21-','X22-','X24-','X25-')):
                ev='Deferred to G4 case + final MAIN outline (status REMAINS_OPEN; no DEFERRED_G4 enum in contract). Carry G1 cover fit -1.100 mm conservative and residual wall -0.150 mm nominal; land clearance -0.060 mm conservative where applicable.'
            elif cid.startswith('X19-'):
                st='RESOLVED_BY_G2';ev='P-0402 adopted as a credible later task. DC-bias/effective capacitance evidence remains mandatory before electrical implementation.'
            statuses[cid]=dict(id=cid,g2_status=st,g2_evidence=ev,evidence_class='PROJECT_DERIVED')
        for cid,st,ev in [
            ('G2-CROSSING-HEIGHT','SUPPLIER_DATA_GATED','Shared lower-web crossing heights computed in shared_corridors; no unverified thin flex is credited.'),
            ('G2-BOOK-FOLD','SUPPLIER_DATA_GATED','B.Cu options need quantified tangent-hinge slack, remating space and accessible battery isolation. Requirements in each option.'),
            ('G2-PROBE-RELIEF','SUPPLIER_DATA_GATED','Tag-Connect through-board guide pins must fit the derived clearance or use carrier relief / S0 fixture. No added seated Z.'),
            ('G2-BACK-STACK','SUPPLIER_DATA_GATED','Full connector + flex + stiffener + solder stack and its positive uncertainty must meet both nominal and RSS limits.'),
            ('G2-DISCOVERED-INTERFACES','SUPPLIER_DATA_GATED','SW1-SW5, antenna feeds and TP access registered; supplier feed construction remains unknown.')]:
            statuses[cid]=dict(id=cid,g2_status=st,g2_evidence=ev,evidence_class='PROJECT_DERIVED')
        return list(statuses.values())


def geometry_gap(g):
    return g['corners']['nominal'].get('vertical_gap_margin_mm',0)


def render_md(res):
    o=['# G2 interconnect allocation (generated; do not edit)','', '**'+res['verdict']+'**','',
       'Values are planning envelopes, not supplier dimensions. PROJECT_DERIVED values inherit their cited inputs; supplier requirements are acceptance limits. No KiCad change is authorized.','',
       '## Stack','', '| ID | nominal mm | RSS mm | linear worst mm | body mm (pod 0.8) | compliant |', '|---|---:|---:|---:|---:|---|']
    for s in res['stacks']:
        o.append('| %s | %.3f | %.3f | %.3f | %.3f | %s |'%(s['id'],s['nominal_mm'],s['rss_mm'],s['linear_mm'],s['body_mm'],s.get('compliant','reference reproduced')))
    o+=['','G1 tolerance terms are imported unchanged. New connector ranges are propagated as full independent max-minus-nom sensitivities. The inner-face G1 allowance is retained conservatively. T_body subtracts the reported pod protrusion; no pod reduction is a lever.','',
        '## Options and allocation','', '| option | side | outcome | selected | length mm | bends | crossings | stack nominal / RSS |', '|---|---|---|---|---|---|---|---|']
    for x in res['options']:
        g=x['geometry'];n=g['corners']['nominal'];s=x['allocation_stack']
        o.append('| %s | %s | %s | %s | %.3f | %s | %s | %.3f / %.3f |'%(x['id'],x['side'],x['outcome'],x['selected'],n['installed_length_excluding_service_mm'],n['bend_count'],g['main_edge_crossings'],s['nominal_mm'],s['rss_mm']))
    for x in res['options']:
        o+=['','### '+x['id'], '', x['reason'], '', 'Evidence: PROJECT_DERIVED. Lexicographic key: `'+json.dumps(x['rank_key'])+'`.','',
            'Geometry, corners, access, routing estimate and supplier acceptance:', '', '```json',dumps(dict(geometry=x['geometry'],height_thresholds=x['height_thresholds'])).rstrip(),'```']
    o+=['','## Assembly and service','']
    for k in ['S0','S1','S2','S3','isolation']:o.append('- **'+k+'**: '+res['assembly'][k])
    o+=['','J1 cycle limit: 50 rated, 25 planned. No external SWD after sealing.','', '## U8 RF verification','']
    o+=['- '+s for s in res['rf_verification']]
    for label,key in [('PCM sweep','pcm_sweep'),('Shared corridors','shared_corridors'),('Discovered interfaces','discovered_interfaces'),('Issue-ready supplier requests','supplier_requests'),('G2 reservations','reservations'),('G3/G4 handoff','conservative_handoff')]:
        o+=['','## '+label,'','```json',dumps(res[key]).rstrip(),'```']
    o+=['','## Conflict status','', '| conflict | g2_status | evidence |','|---|---|---|']
    for x in res['conflict_status']:o.append('| %s | %s | %s |'%(x['id'],x['g2_status'],x['g2_evidence']))
    o+=['','## Unsatisfied acceptance (engineering exit, independent of generator consistency)','']
    o+=['- '+s for s in res['unsatisfied_acceptance']] or ['None.']
    return '\n'.join(o)+'\n'


def architecture_section(res):
    """Exact checked excerpt. All G2 numbers in architecture.md live inside this block."""
    o=['<!-- G2 GENERATED BEGIN -->','## G2','', '**'+res['verdict']+'**','',
       'OD-THICK-REVA governs this provisional integration: nominal ≤ 16.5 mm and RSS ≤ 17.0 mm. The earlier 14.0–15.5 mm target is a non-binding production goal. Source: owner decision 2026-10-12.','',
       'All numbers below are PROJECT_DERIVED from generated/g2_interconnect.json unless labelled otherwise. No supplier dimension is asserted. Full three-corner calculations, overlaps, routing estimates, numeric acceptance requirements and alternative options are in [the generated G2 report](generated/g2_interconnect.md).','',
       '| Interface option | Outcome | Selected | Side | XY window / azimuth | Length excluding service mm | Bends |',
       '|---|---|---|---|---|---:|---:|']
    for x in res['options']:
        g=x['geometry'];n=g['corners']['nominal']
        o.append('| %s | %s | %s | %s | %s / %s | %.3f | %s |'%(x['id'],x['outcome'],x['selected'],x['side'],g.get('window_rect_mm'),g['azimuth_window_deg'],n['installed_length_excluding_service_mm'],n['bend_count']))
    o+=['','| Selected interface | mating / exit | mated Z range mm | path |','|---|---|---|---|']
    for x in res['options']:
        if not x['selected']: continue
        g=x['geometry']
        o.append('| %s | %s / %s | %s | %s |'%(x['interface'],g['mating_direction'],g['exit_direction'],json.dumps(g['mated_z_range_mm'],sort_keys=True),g.get('flex_path','Generated path_regions; corner length excludes service slack')))
    o+=['','| Stack | nominal | RSS | linear worst | T_body (h_pod 0.8) | compliance |','|---|---:|---:|---:|---:|---|']
    for s in res['stacks']:o.append('| %s | %.3f | %.3f | %.3f | %.3f | %s |'%(s['id'],s['nominal_mm'],s['rss_mm'],s['linear_mm'],s['body_mm'],s.get('compliant','reference PASS')))
    o+=['','| B.Cu option | K2-neutral h_stack max | Rev-A nominal h_stack max | R_bend max nominal | fold length required |','|---|---:|---:|---:|---:|']
    for x in res['options']:
        if x['height_thresholds']:
            t=x['height_thresholds'];n=x['geometry']['corners']['nominal']
            o.append('| %s | %.3f | %.3f | %.3f | %.3f |'%(x['id'],t['K2_reference_neutral_max_h_stack_mm'],t['OD_nominal_max_h_stack_mm'],n['R_bend_max_mm'],n['fold_length_required_mm']))
    o+=['','RSS additionally limits positive stack variation; the generated joint-acceptance table is mandatory, not optional. A side change requires a verified mirrored physical mating map with the logical interface unchanged.','', 'P-0402 is adopted as a CREDIBLE_LATER_TASK. C901/C903 retain the electrical evidence gate: ≥6.3 V class, effective capacitance at 3.0 V / 1.8 V against eMMC requirements; a second same-height passive may be needed. No footprint/schematic edit is made. No supplier-gated nesting, cover lamination or reduced pod height is credited.','',
        'Assembly/service (PROVISIONAL_ASSUMPTION):','']
    for k in ['S0','S1','S2','S3','isolation']:o.append('- **'+k+'**: '+res['assembly'][k])
    o+=['','The rigid MAIN folds about the single common tangent hinge in joint_book_fold; isolated option hinges provide lower bounds only. Required slack and pocket requirements are recorded per option and for the joint fold. Slack stays outside the case during rotation and never doubles inside the annulus. J1 budget: 50 rated / 25 planned mating cycles.','', 'U8 RF verification:','']
    o+=['- '+s for s in res['rf_verification']]
    o+=['','G3 must carry the unchanged conservative radial margin %.3f mm to G4. X25 remains: conservative cover fit %.3f mm; nominal wall margin %.3f mm. No downstream phase is authorized.'%(res['conservative_handoff']['radial_margin_mm'],res['conservative_handoff']['cover_case_fit']['conservative']['fit_margin_mm'],res['conservative_handoff']['cover_case_fit']['nominal']['wall_margin_mm']),'',
        '| Conflict | g2_status | Evidence |','|---|---|---|']
    for c in res['conflict_status']:o.append('| %s | %s | %s |'%(c['id'],c['g2_status'],c['g2_evidence']))
    o+=['','Drafted / issue-ready supplier requests (owner issues): '+', '.join(q['id'] for q in res['supplier_requests'])+'. Numeric requirements are incorporated into architecture.json and the generated report.','',
        'G2 reservations: '+', '.join(q['id'] for q in res['reservations'])+'.','',
        'Remaining acceptance gaps:','']+['- '+s for s in res['unsatisfied_acceptance']]
    o+=['','<!-- G2 GENERATED END -->']
    return '\n'.join(o)+'\n'


def render_svg(res):
    s=ad.Svg(820,790,'G2 provisional allocation — front view; no KiCad placement','Nominal planning reservation geometry. Labels list selected options; all supplier gates remain. MAIN and pack circles are provisional envelopes.')
    s.text(20,28,res['verdict'],size=16)
    cx,cy,scale=400,365,10
    s.circle(cx,cy,23*scale,fill='none',stroke='#333')
    s.circle(cx,cy,22*scale,fill='none',stroke='#bbb')
    colors=['#0072b2','#d55e00','#009e73','#cc79a7']
    for idx,q in enumerate(res['reservations']):
        g=q['geometry'];color=colors[idx%len(colors)]
        if g['type']=='rect':
            x0,y0,x1,y1=g['rect'];s.text(cx+((x0+x1)/2-100)*scale,cy+(y0-100)*scale-4,q['source'].replace('g2 option ',''),size=9,fill=color,anchor='middle');s.rect(cx+(x0-100)*scale,cy+(y0-100)*scale,(x1-x0)*scale,(y1-y0)*scale,fill='none',stroke=color)
        else:
            s.path(ad.sector_path(cx,cy,scale,g['r'][0],g['r'][1],g['az'][0],g['az'][1]),fill='none',stroke=color)
    for idx,(key,val) in enumerate(res['allocation'].items()):s.text(20,605+idx*12,key+': '+val,size=10)
    return s.render()


def model_integrity(res):
    """Contract invariants and independent boundary checks; no engineering gates waived."""
    failures=[]
    I=load(MECH/'inputs/g2_interconnect.json')
    required={'J1501':2,'J1502':3,'J201':2,'J202':3,'J1301':1,'J1':1,'U7/LRA':2,'U8':1,'C901/C903':1}
    for interface,count in required.items():
        rows=[o for o in res['options'] if o['interface']==interface]
        if len(rows)!=count or sum(o['selected'] for o in rows)!=1:
            failures.append('option coverage or selection count: '+interface)
    ids=[o['id'] for o in res['options']]
    if len(set(ids))!=len(ids):failures.append('duplicate option id')
    for key,value in I['parameters'].items():
        if all(k in value for k in ('min','nom','max')) and not value['min']<value['nom']<value['max']:
            failures.append('planning nominal must be internal to range: '+key)
    for option in I['options']:
        if any(k in option for k in ('outcome','recommended','selected','verdict')):
            failures.append('hand-authored option verdict in input: '+option['id'])
    # Source geometry remains frozen, independent of output-generation code.
    old=load_register_at_base()
    current=load(ROOT/REG)
    found=[e for e in current['entries'] if e['id']=='OD-THICK-REVA']
    current['entries']=[e for e in current['entries'] if e['id']!='OD-THICK-REVA']
    if current!=old or len(found)!=1:failures.append('prior input register or owner decisions changed')
    if found and (found[0].get('date')!='2026-10-12' or found[0].get('class')!='OWNER_DECISION'):
        failures.append('OD-THICK-REVA date/class')
    for row in res['options']:
        for corner, c in row['geometry']['corners'].items():
            p=c.get('pack_corner_model');mx=c.get('R_bend_max_mm')
            if p and mx and mx>0:
                d,h=p['d_mm'],p['g_mm']
                # Rounded report tolerance; direct circle equation verifies the derived limit.
                if abs((mx-d)**2+(mx-h)**2-mx*mx)>0.02:
                    failures.append('pack-corner radius boundary inconsistent: '+row['id']+'/'+corner)
        if row['selected'] and row['geometry']['nominal_failures']:
            failures.append('selected geometry has nominal failures: '+row['id'])
    for st in res['stacks'][1:]:
        if st['credited_gated_levers'] or not st['credible_levers_only']:
            failures.append('gated lever counted in Rev-A compliance')
        if abs(st['body_mm']+st['h_pod_mm']-st['nominal_mm'])>.001:
            failures.append('body/pod convention differs')
        sigma=math.sqrt(sum(v*v for v in st['tolerance_sensitivities_mm'].values()))
        if abs(st['rss_mm']-st['nominal_mm']-sigma)>.001:
            failures.append('RSS sensitivity aggregation differs')
    if not res['joint_book_fold'].get('nominal_slack_sufficient',True):
        failures.append('selected common book-fold hinge exceeds nominal slack')
    if not res['service_pocket_check']['nominal_pass']:
        failures.append('selected planar slack pocket does not fit at nominal')
    return failures


def load_register_at_base():
    return json.loads(subprocess.run(['git','show',BASE+':'+REG],capture_output=True,check=True).stdout)


def validate(res,files,check_package=True):
    fails=model_integrity(res)
    for name,data in files.items():
        p=GEN/name
        if not p.exists() or p.read_bytes()!=data.encode():fails.append(name+': missing or differs from regeneration')
    # Model integrity is separate from engineering acceptance; open gates must never be hidden.
    for row in res['options']:
        if row['outcome'] not in ('RECOMMENDED','CONDITIONAL','REJECTED'):fails.append('invalid outcome '+row['id'])
        if row['selected'] and row['outcome']=='REJECTED':fails.append('selected rejected option '+row['id'])
    if check_package:
        a=load(MECH/'architecture.json')
        if a.get('g2')!=res:fails.append('architecture.json g2 does not match generated model')
        md=(MECH/'architecture.md').read_text()
        if architecture_section(res) not in md:fails.append('architecture.md lacks exact generated G2 section')
    return fails


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ('build','check'):
        print('usage: g2_interconnect.py build|check',file=sys.stderr);return 2
    try:
        res=Study().build()
        files={'g2_interconnect.json':dumps(res),'g2_interconnect.md':render_md(res),'g2_allocation.svg':render_svg(res)}
        if sys.argv[1]=='build':
            for name,data in files.items():(GEN/name).write_bytes(data.encode())
            print(dumps(dict(status='BUILT',files=list(files),verdict=res['verdict'],allocation=res['allocation'],stacks=[{k:s[k] for k in ['id','nominal_mm','rss_mm','linear_mm','body_mm']} for s in res['stacks']])).rstrip())
            return 0
        fails=validate(res,files)
        print(dumps(dict(status='PASS' if not fails else 'FAIL',failures=fails,verdict=res['verdict'],acceptance_complete=res['acceptance_complete'])).rstrip())
        return int(bool(fails))
    except (AssertionError,KeyError,ValueError,OSError) as exc:
        print('STOP: '+str(exc),file=sys.stderr);return 1


if __name__=='__main__':
    sys.exit(main())
