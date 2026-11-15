"""Consistency checks on the v3 building model: brief areas, overlaps, rooms on their slab, a door for every room,
doors on walls and not opening into other rooms, columns clear of rooms, stairs, headroom, exits, travel. python3 check.py"""
import math
import numpy as np
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
import plans
import plan3 as M
from plan3 import SC

THROUGH_OK = {('G30', 'G31'), ('G32', 'G30'), ('L10', 'L12'), ('L11', 'L12'), ('G03', 'G04'), ('M10', 'M11'), ('M12', 'M13'), ('M02', 'M01')} | \
             {(k, 'L20') for k in ('L21', 'L22', 'L23', 'L24', 'L25', 'L26', 'L27')}

def run():
    bad = []
    for r in M.ROOMS:
        if r['brief'] and r['brief'][1]:
            net = r['poly'].buffer(-0.075, join_style=2).area if r['kind'] != 'open' else r['poly'].area
            if net < r['brief'][1] - 0.05: bad.append(('BRIEF SHORT', r['key'], round(net, 1), r['brief']))
    for fl in ('GF', 'L1', 'L2'):
        rs = [r for r in M.ROOMS if r['fl'] == fl and r['kind'] != 'open']
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                ov = a['poly'].intersection(b['poly']).area
                if ov > 0.05: bad.append(('OVERLAP', fl, a['key'], b['key'], round(ov, 2)))
        for r in rs:
            out = r['poly'].difference(M.PLATE[fl].buffer(0.05)).area
            if out > 0.1 and r['kind'] not in ('stair', 'lift'): bad.append(('OFF SLAB', fl, r['key'], round(out, 2)))
    keys = {d['key'] for d in M.DOORS}
    for r in M.ROOMS:
        if r['kind'] in ('room', 'wet', 'shop') and r['key'] not in keys and r['key'] != 'L20': bad.append(('NO DOOR', r['key']))
    for d in M.DOORS:
        r = [q for q in M.ROOMS if q['key'] == d['key']][0]; p = Point(d['p'])
        dist = r['poly'].exterior.distance(p)
        if dist > 0.2: bad.append(('DOOR OFF WALL', d['key'], round(dist, 2)))
        for q in M.ROOMS:
            if q['fl'] == r['fl'] and q is not r and q['kind'] in ('room', 'wet', 'shop', 'stair', 'lift') and q['poly'].buffer(0.05).contains(p):
                if (r['key'], q['key']) not in THROUGH_OK: bad.append(('DOOR INTO ANOTHER ROOM', d['key'], q['key']))
    for c in M.COLS:
        for r in M.ROOMS:
            if r['fl'] == 'GF' and r['kind'] in ('room', 'wet', 'shop') and r['poly'].buffer(-0.3).contains(Point(c['p'])):
                bad.append(('COLUMN INSIDE ROOM', r['key'], c['lab'], c['ring']))
    rises = {'GF-L1': 4.5 / 26, 'L1-L2': 4.2 / 24, 'S4': 4.5 / 26}
    for k, v in rises.items():
        if v > 0.180: bad.append(('RISER > 180', k, round(v * 1000)))
    pts = []
    for g in getattr(M.PLATE['L2'], 'geoms', [M.PLATE['L2']]): pts += list(g.exterior.coords)
    l2clear = min(SC.roof_h(math.degrees(math.atan2(p[0] - M.C[0], p[1] - M.C[1])) % 360) for p in pts) - SC.ROOF_T - M.FFL['L2']
    if l2clear < 2.7 - 1e-6: bad.append(('L2 HEADROOM', round(l2clear, 2)))
    occ = M.occupancy(); load = {}
    for fl, nm, a, f, n in occ: load[fl] = load.get(fl, 0) + n
    U = M.UNITS
    cap = {'L1': 75 * (U['C1'] + U['C2'] + U['S3'] + U['S4']), 'L2': 75 * (U['C2'] + U['S3'])}
    for fl in cap:
        if load[fl] > cap[fl]: bad.append(('EXIT CAPACITY', fl, load[fl], cap[fl]))
    # ---- entrance canopies + pocket gardens
    import landscape as LS, siteplan as ST, sections as SE
    for c in LS.CANOPIES:
        if not LS.outline(c).within(SC.ENV.buffer(0.01)) and LS.outline(c).difference(SC.ENV).area > 0.05 and \
           LS.outline(c).difference(SC.ENV).difference(SC.disc(M.R_L1 + 0.01)).area > 0.05:
            bad.append(('CANOPY OUTSIDE SETBACK', c['k'], round(LS.outline(c).difference(SC.ENV).area, 2)))
        worst_in, worst_out = 99, 99
        for s_ in np.arange(c['R_in'], c['R_out'], 0.2):
            for t in np.linspace(-1, 1, 11):
                p = LS.xy(c, s_, t); clear = LS.z_top(c, s_, t) - (0.4 if abs(t) > 0.95 else LS.rib_depth(c, s_)) - SE.ground_z(p)   # edge beam 400 deep, ribs elsewhere
                if s_ <= c['R_gate']: worst_in = min(worst_in, clear)
                else: worst_out = min(worst_out, clear)
                if s_ <= c['R_gate'] and LS.z_top(c, s_, t) > 4.52 - 0.05: bad.append(('CANOPY HITS L1 SOFFIT', c['k'], round(s_, 1)))
        if worst_in < 2.4: bad.append(('CANOPY HEADROOM INSIDE', c['k'], round(worst_in, 2)))
        if worst_out < 2.7: bad.append(('CANOPY HEADROOM OUTSIDE', c['k'], round(worst_out, 2)))
        for q in LS.column_pts(c):
            for nm, g in (('HARDSTANDING', ST.HS_S.union(ST.HS_E)), ('PARKING', ST.AISLE.union(unary_union([k for _, k in ST.PARK]))), ('YARD', ST.YARD)):
                if g.buffer(0.3).contains(Point(q['base'])): bad.append(('CANOPY COLUMN IN ' + nm, c['k']))
        # canopy must sit inside the gate passage (clear of GF walls) between the court edge and the first-floor edge
        inside = LS.outline(c).intersection(SC.disc(M.R_L1 - 0.3))
        walls = plans.walls('GF')['solid']
        if inside.intersects(walls.buffer(-0.01)): bad.append(('CANOPY CLASHES WITH GF WALL', c['k'], round(inside.intersection(walls).area, 2)))
    import sheets2
    hs = sheets2.canopy_hs_clear()
    if hs < 4.5: bad.append(('CANOPY OVER HARDSTANDING < 4.5 M', round(hs, 2)))
    hard = unary_union([ST.HS_E, ST.HS_S, ST.YARD, ST.AISLE, ST.UB, ST.TERRACE] + [k for _, k in ST.PARK] + ST.MOTOR + ST.BIKES + [s_ for _, s_ in ST.forecourts()])
    for i, q in enumerate(ST.OUTER):
        if q.intersection(hard).area > 0.05: bad.append(('OUTER POCKET ON HARD AREA', i, round(q.intersection(hard).area, 2)))
        if not q.within(SC.ENV.buffer(0.01)): bad.append(('OUTER POCKET OUTSIDE SETBACK', i))
        for nm, ln in list(ST.SERVICE_LINES.items()) + [(k, ST.SEWER[k]) for k in ('east', 'north', 'west')]:
            if q.intersects(LineString(ln).buffer(0.5)): bad.append(('POCKET OVER BURIED SERVICE', i, nm))
    def doors_on(fl):
        return unary_union([Point(dd['p']).buffer(1.2) for dd in M.DOORS if [q for q in M.ROOMS if q['key'] == dd['key']][0]['fl'] == fl] +
                           [Point(x['p']).buffer(1.2) for x in M.CORE_DOORS if x['fl'] == fl])
    for g, fl in [(g, 'GF') for g in ST.GATE] + [(dict(k='SKY', poly=q), 'L1') for q in LS.SKY]:
        if g['poly'].intersects(doors_on(fl)): bad.append(('POCKET IN FRONT OF A DOOR', g['k'], fl))
    for a, b in LS.INNER:
        for sp in SC.SPINES:
            h = LS.gate_halfangle(sp, 8.8, 0.0)
            if (a - (sp['b'] + h) + 180) % 360 - 180 < 0 and ((sp['b'] - h) - b + 180) % 360 - 180 < 0: bad.append(('INNER POCKET BLOCKS GATE', sp['k']))
    st = LS.seats()
    if st['total'] < 100: bad.append(('COURT SEATS < 100', st['total']))
    if LS.play_poly().area < 30: bad.append(('PLAY AREA < 30', round(LS.play_poly().area, 1)))
    return bad, dict(load=load, cap=cap, seats=st['total'], canopy_hs_clear=round(hs, 2), outer=len(ST.OUTER), gate=len(ST.GATE), inner=len(LS.INNER), sky=len(LS.SKY), l2clear=round(l2clear, 2), rises={k: round(v * 1000) for k, v in rises.items()})

if __name__ == '__main__':
    bad, info = run()
    print(info)
    for b in bad: print(b)
    print('ISSUES:', len(bad))
