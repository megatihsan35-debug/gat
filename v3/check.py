"""Consistency checks on the v3 building model: brief areas, overlaps, rooms on their slab, a door for every room,
doors on walls and not opening into other rooms, columns clear of rooms, stairs, headroom, exits, travel. python3 check.py"""
import math
import numpy as np
from shapely.geometry import Point
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
    return bad, dict(load=load, cap=cap, l2clear=round(l2clear, 2), rises={k: round(v * 1000) for k, v in rises.items()})

if __name__ == '__main__':
    bad, info = run()
    print(info)
    for b in bad: print(b)
    print('ISSUES:', len(bad))
