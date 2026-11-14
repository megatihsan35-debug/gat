import json, numpy as np
from geom import *
import site_el as SE
from draw2 import L1_SECT, z_roof_top, OPEN_ARCS, in_arcs
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

items = []
def ext(g, z0, z1, mat, edges=True):
    for q in (g.geoms if hasattr(g, 'geoms') else [g]):
        if q.is_empty or q.geom_type != 'Polygon': continue
        items.append(dict(t='ext', outer=[list(map(float, c)) for c in q.exterior.coords[:-1]],
                          holes=[[list(map(float, c)) for c in h.coords[:-1]] for h in q.interiors], z0=z0, z1=z1, m=mat, e=edges))
fins = []
def finset(C, R, b0, b1, z0, zfn, step, mat='fin', excl=()):
    if b1 <= b0: b1 += 360
    for b in np.linspace(b0, b1, int(np.radians(b1 - b0) * R / step)):
        if in_arcs(b, excl): continue
        p = C + d(b) * R; fins.append([float(p[0]), float(p[1]), float(b), z0, float(zfn(b)), mat])

ZG, ZL = 0.9, 5.4
plinth = unary_union([Point(B).buffer(R_OVH + 3.0, 180), Point(S).buffer(RS_OUT + 3.0, 180), lobby.buffer(3.0)])
ext(SITE_POLY, 0.0, 0.03, 'site', False)
ext(SE.PLAZA_SE.difference(plinth), 0.03, 0.06, 'plaza', False); ext(SE.GARDEN_N.difference(plinth), 0.03, 0.12, 'grass', False)
for g in (SE.DRIVE, SE.YARD, SE.LAYBY, SE.PARK_AISLE): ext(g.difference(plinth), 0.03, 0.07, 'asphalt', False)
ext(plinth, 0.0, ZG, 'stone')
ext(Point(B).buffer(R_COURT, 180), ZG, ZG + 0.02, 'court', False)
gates = unary_union([sector(B, R_COURT - 0.1, R_OVH + 0.2, *a) for a in [mod(9), mod(17), mod(19)]])
cafe_glass = sector(B, R_VER, R_OUT, *mod(12))
solid = ring(B, R_VER + 0.35, R_OUT).difference(gates).difference(cafe_glass).difference(lobby.buffer(0.05))
ext(solid, ZG, 5.0, 'wall')
ext(ring(B, R_VER, R_VER + 0.35).difference(gates).difference(lobby), ZG, 5.0, 'glass', False)
ext(cafe_glass.difference(gates), ZG, 5.0, 'glass', False)
for k in range(10):
    b = (M0 + 36 * k) % 360; p = B + d(b) * R_COURT
    ext(Point(p).buffer(0.28, 16), ZG, 5.0, 'white')
ext(ring(B, R_COURT, R_OVH).difference(lobby.buffer(0.05)), 5.0, ZL, 'white')
terr_out = ring(B, R_OUT, R_OVH).difference(L1_SECT)
ext(terr_out, ZL, ZL + 0.55, 'planter')
ext(ring(B, R_COURT, R_COURT + 0.06).difference(L1_SECT), ZL, ZL + 1.1, 'glass', False)
finset(B, R_OVH + 0.05, mod(13)[1], mod(8)[0] + 360, ZL, lambda b: 6.6, 0.6)
finset(B, R_OUT + 0.35, 0, 360, ZG, lambda b: 5.0, 0.6, excl=OPEN_ARCS + [(mod(8)[0], mod(13)[1])] if False else OPEN_ARCS)
# L1 block: slab, glass, fins (roof built in JS)
ext(L1_SECT.difference(Point(B).buffer(R_OVH, 180)), 5.0, ZL, 'white')
ext(ring(B, R_L1 - 0.1, R_L1).intersection(L1_SECT), ZL, 11.4, 'glass', False)
ext(ring(B, R_VER, R_VER + 0.1).intersection(L1_SECT), ZL, 10.0, 'glass', False)
for k in range(4):
    b = mod(8)[0] + 36 * k; p = B + d(b) * R_L1; ext(Point(p).buffer(0.16, 12), 5.0, 11.7, 'steel')
finset(B, R_L1 + 0.15, mod(8)[0], mod(13)[1], 5.0, lambda b: z_roof_top(R_L1) - 0.3, 0.75, excl=[mod(11), mod(12)])
# small ring
ext(ring(S, RS_WELL, RS_OUT), ZG, 9.9, 'wall')
finset(S, RS_OUT + 0.3, 0, 360, ZG, lambda b: 9.95, 0.6)
ext(rect_at(S + d(QIBLA - 135) * 7.0, 4.0, 2.6, QIBLA - 45), 9.9, 12.0, 'grey')
# knot
ext(lobby.difference(Point(B).buffer(R_OUT, 180)).difference(Point(S).buffer(RS_OUT, 180)), ZG, ZL, 'glass', False)
ext(core_block.buffer(0.3, join_style=2), ZG, 10.9, 'grey')
ext(core1_lifts.buffer(-0.3, join_style=2), 10.9, 12.4, 'grey')
ext(lobby.difference(Point(B).buffer(R_OUT, 180)).difference(Point(S).buffer(RS_OUT, 180)), ZL - 0.4, ZL, 'white')
# court canopy (oculus)
ext(ring(B, 4.5, R_COURT), 6.9, 7.05, 'membrane')
# tables + play
for rr, n, off in [(5.6, 9, 0), (7.6, 12, 15)]:
    for k in range(n):
        b = off + 360 / n * k
        if 20 < b < 95: continue
        p = B + d(b) * rr; ext(Point(p).buffer(0.55, 16), ZG + 0.7, ZG + 0.76, 'wood', False); ext(Point(p).buffer(0.06, 6), ZG, ZG + 0.7, 'steel', False)
ext(sector(B, 3.3, 8.6, 22, 94), ZG, ZG + 0.05, 'play', False)
# context
ctx = [((56, 65, 106, 112), 10.0, 'ctx'), ((-18, 44, 4.4, 67), 7.0, 'ctx'), ((40, -70, 150, -52), 9.0, 'ctx')]
for (x0, y0, x1, y1), hgt, m in ctx: ext(Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), 0, hgt, m)
ext(Polygon([(91, 5), (109, 5), (109, 63), (91, 63)]), 0.0, 0.08, 'tennis', False)
road = Polygon([tuple(SE.road_pt(-60) - SE.N_IN * 0.5), tuple(SE.road_pt(130) - SE.N_IN * 0.5), tuple(SE.road_pt(130) - SE.N_IN * 11), tuple(SE.road_pt(-60) - SE.N_IN * 11)])
ext(road, 0.0, 0.04, 'asphalt', False)
ext(Polygon([(113.5, -40), (123, -40), (123, 120), (113.5, 120)]), 0.0, 0.04, 'asphalt', False)
ext(Polygon([(250, -200), (330, -200), (330, 250), (250, 250)]), -0.5, -0.45, 'water', False)
ribbons = [dict(name=k, pts=[list(map(float, p)) for p in pts], w=w) for k, (n, pts, w) in SE.RIBBONS.items()]
crown = []
for sgn in (1, -1):
    P0 = B + d(QIBLA + 38 * sgn) * 12.5; P2 = S + d(QIBLA + 180 + 40 * sgn) * 8.0; P1 = B + d(QIBLA) * 17.5 - perp * 9.0 * sgn
    crown.append([[float(P0[0]), float(P0[1]), 6.6], [float(P1[0]), float(P1[1]), 13.5], [float(P2[0]), float(P2[1]), 9.95]])
trees = [[float(x), float(y), float(dd)] for x, y, dd in SE.TREES] + [[float(B[0]), float(B[1]), 5.0]]
rng = np.random.default_rng(7)
people = []
for _ in range(40):
    p = np.array([rng.uniform(70, 110), rng.uniform(-12, 18)])
    if SE.PLAZA_SE.contains(Point(p)): people.append([float(p[0]), float(p[1]), 0.06])
for _ in range(30):
    b = rng.uniform(0, 360); rr = rng.uniform(2, 8.5); p = B + d(b) * rr; people.append([float(p[0]), float(p[1]), ZG])
for _ in range(14):
    b = rng.uniform(150, 330); rr = rng.uniform(13, 18.5); p = B + d(b) * rr; people.append([float(p[0]), float(p[1]), ZL])
scene = dict(items=items, fins=fins, ribbons=ribbons, crown=crown, trees=trees, people=people,
             B=list(map(float, B)), S=list(map(float, S)), L1=dict(r0=R_COURT, r1=R_L1, b0=mod(8)[0], b1=mod(13)[1], z0=11.2, z1=12.9),
             mph=dict(b0=mod(11)[0], b1=mod(12)[1]))
open('/home/claude/r3d/scene.js', 'w').write('window.SCENE=' + json.dumps(scene) + ';')
print(len(items), len(fins))
