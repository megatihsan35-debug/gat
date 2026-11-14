import sys, math, numpy as np, cv2
sys.path.insert(0, '/home/claude/crit1')
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
from geom import *
import geom as GM
import site_el as SE
SC = 2.0   # mm per metre at 1:500
def dsk(C, r): return Point(C).buffer(r, 360)
def gaps(): 
    gs = []
    for b0, b1 in [mod(9), mod(17), (mod(19)[0], mod(20)[1])]:
        gs.append(sector(B, 0, 30, b0, b1, 60))
    return unary_union(gs)
B1_, B2_ = mod(8)[0], mod(13)[1]
lobby = GM.lobby
l1_link = lobby.difference(dsk(B, R_VER))
core_all = unary_union([GM.core1_stair, GM.core1_lifts])
PIECES = [
 # id, name, geometry, [(material, qty)], sits on, top (mm above site layer), note
 ('B1', 'PODIUM (+0.9 m)', unary_union([dsk(B, R_OVH + 3.0), dsk(S, RS_OUT + 3.0), lobby.buffer(3.0)]), [('GREYBOARD 2 MM', 1)], 'SITE LAYER 4', 2, 'INCLUDES THE ENTRANCE STEPS AROUND THE BUILDING'),
 ('B2', 'GELUNG RASA · GF SHOP RING', dsk(B, R_OUT).difference(dsk(B, R_VER)).difference(gaps()), [('FOAM 5 MM', 1), ('GREYBOARD 2 MM', 1)], 'B1', 9, '3 GAPS = GERBANG TIMUR, SELATAN, TENGAH (OPEN GATES)'),
 ('B3', 'TERRACE SLAB · LALUAN SIMPUL (+5.4 m)', dsk(B, R_OVH).difference(dsk(B, R_COURT)), [('GREYBOARD 2 MM', 1)], 'B2', 11, 'CENTRE HOLE = TALAM COURT Ø18 M'),
 ('B4', 'EAST BLOCK · GALLERY + DAPUR REWANG HALL', sector(B, R_VER, R_L1, B1_, B2_, 90), [('FOAM 5 MM', 2), ('GREYBOARD 2 MM', 1)], 'B3 (EAST SIDE)', 23, 'OVERHANGS THE SLAB EDGE BY ≈1 MM (3.4 M OVERSAIL)'),
 ('B5', 'EAST RIBBON ROOF (+11.2 → +12.9 m)', sector(B, R_COURT, R_L1, B1_, B2_, 90), [('GREYBOARD 2 MM', 1)], 'B4', 25, 'OVERHANGS INTO THE COURT EDGE (R9 M)'),
 ('B6', 'GELUNG KECIL + KNOT · GF', unary_union([dsk(S, RS_OUT), lobby]).difference(dsk(B, R_OVH)).difference(dsk(S, RS_WELL)), [('FOAM 5 MM', 1), ('GREYBOARD 2 MM', 2)], 'B1', 11, 'SMALL HOLE = LIGHT WELL Ø5 M'),
 ('B7', 'GELUNG KECIL + KNOT · L1 (TO PARAPET +10.5 m)', unary_union([dsk(S, RS_OUT), l1_link]).difference(dsk(S, RS_WELL)), [('FOAM 5 MM', 2)], 'B6 + B3', 21, 'MUSOLLA + ADMIN RING; PART SITS ON THE TERRACE SLAB'),
 ('B8', 'LIFT + STAIR CORE', core_all, [('GREYBOARD 2 MM', 1)], 'B7', 23, ''),
 ('B9', 'LIFT OVERRUN (+12.4 m)', GM.core1_lifts, [('GREYBOARD 2 MM', 1)], 'B8', 25, ''),
 ('B10', 'OCULUS CANOPY (PTFE, +7.2 → +7.7 m)', dsk(B, 9.0).difference(dsk(B, 4.5)), [('TRACING PAPER / ACETATE', 1)], '4 POSTS 4 MM ON B3 INNER EDGE', 15, 'OCULUS HOLE Ø9 M'),
]
# crown ribbons (two)
perp = GM.perp if hasattr(GM, 'perp') else None
def crown():
    out = []
    pp = np.array([d(QIBLA)[1], -d(QIBLA)[0]])
    try:
        from skp_build import perp as P_
        pp = P_
    except Exception:
        pass
    for sgn in (1, -1):
        P0_ = B + d(QIBLA + 38 * sgn) * 12.5; P2_ = S + d(QIBLA + 180 + 40 * sgn) * 8.0; P1_ = B + d(QIBLA) * 17.5 - pp * 9.0 * sgn
        z0, z1, z2 = 6.6, 13.5, 9.95
        pts = []
        for t in np.linspace(0, 1, 61):
            # quadratic through P0,P1,P2 at t=0,.5,1
            p = (1 - t) * (1 - 2 * t) * P0_ + 4 * t * (1 - t) * P1_ + t * (2 * t - 1) * P2_
            z = (z0 + (z1 - z0) * math.sin(math.pi * t)) if t < 0.5 else (z2 + (z1 - z2) * math.sin(math.pi * t))
            pts.append((p[0], p[1], z))
        out.append(dict(sgn=sgn, P0=P0_, P1=P1_, P2=P2_, pts=np.array(pts)))
    return out
CROWN = crown()
def ribbons():
    out = []
    for k, (nm, pts, w) in SE.RIBBONS.items():
        ls = LineString(pts); L = ls.length
        zf = lambda t: 3.6 + 1.5 * math.sin(math.pi * t * 0.9) + 1.3 * t
        posts = [(tt, ls.interpolate(tt * L).coords[0], zf(tt) - 0.22) for tt in (0.12, 0.42, 0.72)]
        dev = sum(math.hypot(L / 60, (zf((i + 1) / 60) - zf(i / 60))) for i in range(60))
        out.append(dict(k=k, nm=nm, poly=ls.buffer(w / 2, cap_style=2, join_style=1), cl=list(ls.coords), w=w, L=L, dev=dev, posts=posts))
    return out
RIBS = ribbons()
if __name__ == '__main__':
    for p in PIECES:
        g = p[2]; x0, y0, x1, y1 = g.bounds
        print(p[0], p[1], g.geom_type, round((x1 - x0) * SC, 1), 'x', round((y1 - y0) * SC, 1), 'mm', p[3])
    for c in CROWN:
        P = c['pts']; L3 = np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1)); Lp = np.sum(np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1))
        print('crown', c['sgn'], 'len3d m', round(L3, 1), 'plan', round(Lp, 1), 'mm', round(L3 * SC, 1))
    for r in RIBS: print(r['k'], round(r['L'], 1), round(r['dev'], 1), [(t, round(z, 2)) for t, p, z in r['posts']])
