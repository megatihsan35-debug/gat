import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle, Arc, FancyArrowPatch, Rectangle
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity
from geom import *
import site_el as SE

plt.rcParams['font.family'] = 'DejaVu Sans'
ZC = {'pub': '#F7D9A0', 'semi': '#CFE5B4', 'serv': '#D9D2EA', 'priv': '#BFDDF2', 'circ': '#ECECEC', 'open': '#FFFFFF'}
INK = '#1E2326'

def geoms(g):
    if g.is_empty: return []
    return list(g.geoms) if hasattr(g, 'geoms') else [g]

def fillpoly(ax, g, fc, ec='none', lw=0.0, z=1, alpha=1, hatch=None, ls='-'):
    for q in geoms(g):
        if q.geom_type != 'Polygon': continue
        verts = np.array(q.exterior.coords)
        codes = [1] + [2] * (len(verts) - 2) + [79]
        allv, allc = [verts], [codes]
        for h in q.interiors:
            hv = np.array(h.coords); allv.append(hv); allc.append([1] + [2] * (len(hv) - 2) + [79])
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        p = PathPatch(Path(np.vstack(allv), np.concatenate(allc)), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, hatch=hatch, ls=ls)
        ax.add_patch(p)

def line(ax, pts, lw=0.5, c=INK, z=5, ls='-', alpha=1):
    pts = np.array(pts); ax.plot(pts[:, 0], pts[:, 1], lw=lw, c=c, zorder=z, ls=ls, alpha=alpha, solid_capstyle='butt')

def outline(ax, g, lw=0.5, c=INK, z=5, ls='-'):
    for q in geoms(g):
        if q.geom_type == 'Polygon':
            line(ax, q.exterior.coords, lw, c, z, ls)
            for h in q.interiors: line(ax, h.coords, lw, c, z, ls)
        elif q.geom_type in ('LineString', 'LinearRing'):
            line(ax, q.coords, lw, c, z, ls)

def arcpts(C, r, b0, b1, n=60):
    if b1 <= b0: b1 += 360
    return [C + d(t) * r for t in np.linspace(b0, b1, n)]

# ---------------- doors & glazing ----------------
def tangent(b): r = np.radians(b); return np.array([np.cos(r), -np.sin(r)])
DOORS = {'GF': [], 'L1': []}     # (centre, wall_dir, width, swing_normal or None)
GLAZE = {'GF': [], 'L1': []}     # (C, r, b0, b1)
def arc_door(level, C, r, b, w, swing=+1, hinged=True):
    DOORS[level].append((C + d(b) * r, tangent(b), w, d(b) * swing if hinged else None))
def rad_door(level, C, r, b, w, swing=+1, hinged=True):
    DOORS[level].append((C + d(b) * r, d(b), w, tangent(b) * swing if hinged else None))
def mid(i): b0, b1 = mod(i); return (b0 + 9) % 360

for i in [5, 6, 7, 8, 13, 14, 15, 16]:
    b = mid(i); b0, b1 = mod(i)
    GLAZE['GF'].append((B, R_VER, b0, b1)); arc_door('GF', B, R_VER, b, 1.8, hinged=False)
    arc_door('GF', B, R1_SHOP, b, 0.9, +1); arc_door('GF', B, R2_SHOP, b, 0.9, +1); arc_door('GF', B, R_OUT, b, 1.0, +1)
b0 = mod(3)[0]
for a in (b0 + 6.5, b0 + 19.5, b0 + 31): arc_door('GF', B, R_VER, a, 1.2, +1)
rad_door('GF', B, 14.0, b0 + 31, 0.9, -1) if False else arc_door('GF', B, 14.0, b0 + 31, 0.9, +1)
arc_door('GF', B, R_VER, mid(10), 1.2, +1)
GLAZE['GF'] += [(B, R_VER, *mod(11)), (B, R_VER, *mod(12)), (B, R_OUT, *mod(12)), (B, R_VER, *mod(18)), (B, R_VER, *mod(1)[:1], mod(2)[1])]
arc_door('GF', B, 14.6, mid(11), 0.9, +1); arc_door('GF', B, R_OUT, mid(11), 1.0, +1)
arc_door('GF', B, R_VER, mid(12), 1.8, hinged=False); arc_door('GF', B, R_OUT, mid(12), 1.8, hinged=False)
rad_door('GF', B, 13.0, mod(12)[0], 1.6, hinged=False)
arc_door('GF', B, R_VER, mid(18), 1.2, hinged=False); arc_door('GF', B, 14.6, mid(18), 1.0, +1); arc_door('GF', B, R_OUT, mid(18), 1.2, +1)
rad_door('GF', B, 14.5, mod(1)[0], 3.0, hinged=False)             # main doors from Serambi Tengah
arc_door('GF', B, R_VER, (mod(1)[0] + 18) % 360, 2.4, hinged=False)  # lobby to court
DOORS['GF'].append((np.array(SE.NW_DOOR) - d(QIBLA) * 1.0, d(QIBLA), 2.4, None))   # Utara door
# small ring doors (corridor + outside)
def sdoor(level, k, frac, w, r=RS_COR, swing=+1, hinged=True):
    b = (QIBLA - 180 - 22.5 + 45 * k + 45 * frac) % 360
    arc_door(level, S, r, b, w, swing, hinged)
for k, f, w in [(1, .5, 1.0), (2, .5, 1.0), (3, .3, 1.0), (3, .8, 0.9), (4, .25, 1.2), (4, .66, 0.9), (4, .93, 0.8), (5, .5, 2.0), (6, .25, 1.2), (6, .75, 1.2), (7, .22, 1.0), (7, .66, 1.0), (7, .94, 0.8)]:
    sdoor('GF', k, f, w, swing=+1, hinged=w < 1.8)
for k, f, w in [(5, .5, 3.0), (6, .25, 1.8), (6, .75, 1.8), (4, .25, 1.5), (3, .3, 1.0)]:
    sdoor('GF', k, f, w, r=RS_OUT, hinged=False)
# L1
arc_door('L1', B, R_VER, mid(8), 1.8, hinged=False); GLAZE['L1'].append((B, R_VER, *mod(8)))
b0, b1 = mod(9)
for a in (b0 + 4.7, b0 + 12.2, b0 + 16.1): arc_door('L1', B, R_VER, a, 0.9, +1)
arc_door('L1', B, R_VER, mid(10), 1.2, +1); rad_door('L1', B, 19.8, mod(11)[0], 1.2, +1)
arc_door('L1', B, R_VER, mid(11), 2.4, hinged=False); GLAZE['L1'] += [(B, R_VER, *mod(11)), (B, R_L1, mod(11)[0], mod(12)[1]), (B, R_L1, *mod(8))]
rad_door('L1', B, 13.0, mod(12)[0], 1.5, +1)
b0, b1 = mod(13)
for a in (b0 + 3.8, b0 + 11.3, b0 + 16.6): arc_door('L1', B, R_VER, a, 1.0, +1)
for k, f, w in [(1, .5, 1.0), (2, .35, 1.0), (2, .85, 0.9), (7, .3, 1.0), (7, .8, 0.9), (3, .5, 1.2), (4, .5, 1.2), (5, .5, 1.5), (6, .4, 1.5), (6, .9, 0.8), (0, .3, 1.2), (0, .8, 0.9)]:
    sdoor('L1', k, f, w, swing=+1, hinged=w < 1.4)

def walls_for(level):
    rs = [r for r in ROOMS if r['level'] == level and r['code'] != 'OPEN']
    env = unary_union([r['poly'] for r in rs]).buffer(0.01).buffer(-0.01)
    inner = unary_union([LineString(r['poly'].exterior.coords).buffer(0.075, cap_style=2, join_style=2) for r in rs if r['code'] not in ('CIRC',)])
    ext = unary_union([LineString(q.exterior.coords).buffer(0.13, cap_style=2, join_style=2) for q in geoms(env)] +
                      [LineString(h.coords).buffer(0.13, cap_style=2, join_style=2) for q in geoms(env) for h in q.interiors])
    w = unary_union([inner, ext]).intersection(env.buffer(0.14, join_style=2))
    # remove walls across corridors/lobby internals (keep envelope)
    cut = []
    for C, r, b0, b1 in GLAZE[level]:
        cut.append(sector(C, r - 0.25, r + 0.25, b0 + 0.6, b1 - 0.6, 30))
    for c, t, wdt, sw in DOORS[level]:
        n = np.array([-t[1], t[0]])
        cut.append(Polygon([c + t * wdt / 2 + n * 0.3, c - t * wdt / 2 + n * 0.3, c - t * wdt / 2 - n * 0.3, c + t * wdt / 2 - n * 0.3]))
    return w.difference(unary_union(cut)), env

def stair_symbol(ax, poly, nflights=2, lw=0.35):
    q = poly.minimum_rotated_rectangle; c = np.array(q.exterior.coords)[:4]
    e1, e2 = c[1] - c[0], c[2] - c[1]
    if np.linalg.norm(e1) < np.linalg.norm(e2): c = np.roll(c, -1, axis=0); e1, e2 = c[1] - c[0], c[2] - c[1]
    L, W = np.linalg.norm(e1), np.linalg.norm(e2); u, v = e1 / L, e2 / W
    outline(ax, q, 0.5)
    line(ax, [c[0] + v * W / 2, c[0] + v * W / 2 + u * (L - 1.5)], 0.5)
    for k in range(13):
        a = c[0] + u * (k * (L - 1.5) / 12)
        line(ax, [a, a + v * W], lw)
    ax.annotate('', xy=c[0] + u * (L - 1.7) + v * W * 0.25, xytext=c[0] + u * 0.3 + v * W * 0.25, arrowprops=dict(arrowstyle='->', lw=0.6, color=INK), zorder=7)
    ax.text(*(c[0] + u * 0.6 + v * W * 0.25), 'UP', fontsize=4.5, zorder=8, va='center')

def lift_symbol(ax, poly):
    q = poly.minimum_rotated_rectangle; c = np.array(q.exterior.coords)[:4]
    outline(ax, q, 0.6); mid_ = (c[0] + c[1]) / 2; mid2 = (c[2] + c[3]) / 2
    for a, b_ in [(c[0], c[2]), (c[1], c[3])]: pass
    h1 = [c[0], (c[0] + c[1]) / 2, (c[3] + c[2]) / 2, c[3]]; h2 = [(c[0] + c[1]) / 2, c[1], c[2], (c[3] + c[2]) / 2]
    for h in (h1, h2):
        outline(ax, Polygon(h), 0.4); line(ax, [h[0], h[2]], 0.3); line(ax, [h[1], h[3]], 0.3)

def label(ax, txt, xy, fs=5.2, c=INK, z=9, w='normal', rot=0):
    ax.text(xy[0], xy[1], txt, fontsize=fs, ha='center', va='center', color=c, zorder=z, fontweight=w, rotation=rot, linespacing=1.05)

def columns(ax, level):
    s = 0.5
    for r, b in COLS_BIG:
        if level == 'L1' and not (mod(8)[0] - 0.1 <= b <= mod(13)[1] + 0.1): continue
        p = B + d(b) * (r if r == R_COURT else R_OUT)
        fillpoly(ax, affinity.rotate(box(p[0] - s / 2, p[1] - s / 2, p[0] + s / 2, p[1] + s / 2), -b, origin=tuple(p)), INK, z=8)
    for r, b in COLS_SMALL:
        p = S + d(b) * r
        fillpoly(ax, affinity.rotate(box(p[0] - 0.2, p[1] - 0.2, p[0] + 0.2, p[1] + 0.2), -b, origin=tuple(p)), INK, z=8)
    if level == 'L1':
        for k in range(4):
            b = mod(8)[0] + 36 * k
            p = B + d(b) * R_L1; ax.add_patch(Circle(p, 0.18, fc=INK, zorder=8))

def grid(ax, level, ext=4.0):
    for k in range(10):
        b = (M0 + 36 * k) % 360
        p0, p1 = B + d(b) * (R_COURT - 1.5), B + d(b) * (R_L1 + ext)
        line(ax, [p0, p1], 0.25, '#7A8288', 2, (0, (8, 3, 1, 3)))
        ax.add_patch(Circle(B + d(b) * (R_L1 + ext + 1.1), 1.1, fc='white', ec=INK, lw=0.4, zorder=6))
        label(ax, str(k + 1), B + d(b) * (R_L1 + ext + 1.1), 5)
    for k in range(8):
        b = (QIBLA - 180 - 22.5 + 45 * k) % 360
        if k in (0, 1, 7): continue
        p0, p1 = S + d(b) * 1.0, S + d(b) * (RS_OUT + 3.0)
        line(ax, [p0, p1], 0.25, '#7A8288', 2, (0, (8, 3, 1, 3)))
        ax.add_patch(Circle(S + d(b) * (RS_OUT + 4.1), 1.1, fc='white', ec=INK, lw=0.4, zorder=6))
        label(ax, 'ABCDEFGH'[k], S + d(b) * (RS_OUT + 4.1), 5)

def lamellas(ax, C, r, b0, b1, step=0.6, L=0.55, lw=0.35, c='#9A3F25'):
    if b1 <= b0: b1 += 360
    n = int(np.radians(b1 - b0) * r / step)
    for t in np.linspace(b0, b1, n):
        line(ax, [C + d(t) * r, C + d(t) * (r + L)], lw, c, 6)

def court_furniture(ax):
    import math
    # tables in rings around central tree; play area to the north-east
    for rr, n, off in [(5.6, 9, 0), (7.6, 12, 15)]:
        for k in range(n):
            b = off + 360 / n * k
            if 20 < b < 95: continue                     # play zone
            p = B + d(b) * rr
            ax.add_patch(Circle(p, 0.55, fc='white', ec=INK, lw=0.35, zorder=6))
            for j in range(5):
                q = p + d(b + 72 * j) * 0.95; ax.add_patch(Circle(q, 0.2, fc='white', ec=INK, lw=0.25, zorder=6))
    play = sector(B, 3.3, 8.6, 22, 94)
    fillpoly(ax, play, '#F2C3A8', '#B4492B', 0.4, z=4); label(ax, 'PLAY\n30 m²', B + d(58) * 6.0, 4.6)
    ax.add_patch(Circle(B, 1.0, fc='#9DBE73', ec='#4C6B2C', lw=0.4, zorder=5))
    ax.add_patch(Circle(B, 2.6, fc='none', ec='#4C6B2C', lw=0.3, ls=':', zorder=5))
    hw = sector(B, R_COURT - 0.9, R_COURT - 0.3, 300, 318)
    fillpoly(ax, hw, '#BFE0EA', INK, 0.4, z=6); label(ax, 'HAND-WASH', B + d(309) * (R_COURT - 1.6), 4.2)

def ribbons_overhead(ax, lw=0.45):
    for k, (nm, pts, w) in SE.RIBBONS.items():
        g = SE.ribbon_poly(pts, w).difference(Point(B).buffer(R_OUT, 180)).difference(Point(S).buffer(RS_OUT, 180))
        outline(ax, g, lw, '#3F6E8C', 3, (0, (4, 2)))

def plan(ax, level, title=True, show_site=True, fs=5.2):
    if show_site:
        fillpoly(ax, SITE_POLY, '#FBFAF6', z=0)
        outline(ax, SITE_POLY, 0.9, '#C8372D', 1, (0, (10, 3, 2, 3)))
        outline(ax, BUILDABLE, 0.35, '#C8372D', 1, (0, (3, 3)))
    if level == 'GF':
        fillpoly(ax, SE.PLAZA_SE, '#EFE7D6', z=0.5); fillpoly(ax, SE.GARDEN_N, '#E1ECD3', z=0.5)
        fillpoly(ax, SE.LAYBY, '#DADADA', INK, 0.3, z=0.6); fillpoly(ax, SE.DRIVE, '#E4E4E4', z=0.6)
        fillpoly(ax, SE.YARD, '#E4E4E4', z=0.6)
        for p in SE.PARK_STAFF + [SE.OKU_BAY]: outline(ax, p, 0.3)
        fillpoly(ax, Point(B).buffer(R_COURT, 180), '#F6F1E7', z=0.7)
        court_furniture(ax)
        fillpoly(ax, ring(B, R_COURT, R_VER), '#F6F1E7', z=0.8)
        line(ax, arcpts(B, R_OVH, 0, 360, 200), 0.35, INK, 3, (0, (4, 2)))
        outline(ax, sector(B, R_COURT, R_L1, mod(8)[0], mod(13)[1]), 0.35, '#3F6E8C', 3, (0, (6, 2, 1, 2)))
        ribbons_overhead(ax)
        line(ax, arcpts(B, 4.5, 0, 360), 0.35, '#3F6E8C', 3, (0, (4, 2)))
    if level == 'L1':
        terr = ring(B, R_COURT, R_OVH).difference(sector(B, R_COURT, R_L1, mod(8)[0], mod(13)[1])).difference(lobby)
        fillpoly(ax, terr, '#E9F0E1', z=0.5); outline(ax, terr, 0.3, '#6E8F4E', 1)
        lp = ring(B, R_OUT, R_OVH).difference(sector(B, R_COURT, R_L1, mod(8)[0], mod(13)[1]))
        fillpoly(ax, lp, '#D7E6C4', z=0.6)                          # planter strip
        line(ax, arcpts(B, R_OVH, mod(13)[1], mod(8)[0] + 360, 200), 0.6, INK, 6)
        fillpoly(ax, Point(B).buffer(R_COURT, 180), 'white', z=0.4)
        line(ax, arcpts(B, R_COURT, 0, 360, 200), 0.35, INK, 3, (0, (4, 2)))
        fillpoly(ax, ring(B, 4.5, R_COURT), 'none', '#3F6E8C', 0.35, z=3)
        label(ax, 'OCULUS CANOPY BELOW\n(open to sky Ø9 m)', B, 4.6, '#3F6E8C')
        label(ax, 'LALUAN SIMPUL · roof terrace walk +5.400', B + d(230) * 15.0, 5.0, '#3E5A22', rot=0)
        label(ax, 'TAMAN ULAM terrace\n(herbs of 11 states)', B + d(330) * 14.5, 4.6, '#3E5A22')
    for r in ROOMS:
        if r['level'] != level or r['code'] == 'OPEN': continue
        fillpoly(ax, r['poly'], ZC[r['zone']], z=1)
    if level == 'GF':
        fillpoly(ax, ring(B, R_COURT, R_VER), '#F3EDE1', z=1)
    w, env = walls_for(level)
    fillpoly(ax, w, INK, z=7)
    for C, r, b0, b1 in GLAZE[level]:
        for rr in (r - 0.05, r + 0.05): line(ax, arcpts(C, rr, b0 + 0.6, b1 - 0.6, 30), 0.3, INK, 7)
    for c, t, wdt, sw in DOORS[level]:
        if sw is None: continue
        h = c - t * wdt / 2
        ang0 = np.degrees(np.arctan2(t[1], t[0])); angs = np.degrees(np.arctan2(sw[1], sw[0]))
        diff = (angs - ang0 + 180) % 360 - 180
        a0, a1 = (ang0, ang0 + 90) if diff > 0 else (ang0 - 90, ang0)
        ax.add_patch(Arc(h, 2 * wdt, 2 * wdt, theta1=a0, theta2=a1, lw=0.3, color=INK, zorder=7))
        line(ax, [h, h + sw * wdt], 0.3, INK, 7)
    for r in ROOMS:
        if r['level'] != level: continue
        if r['code'] in ('ST1', 'ST2'):
            pol = core1_stair if r['code'] == 'ST1' else Polygon([B + d(mid(10) - 6.5) * 11.6, B + d(mid(10) + 6.5) * 11.6, B + d(mid(10) + 5.3) * 17.6, B + d(mid(10) - 5.3) * 17.6])
            stair_symbol(ax, pol)
            continue
        if r['code'] == 'LIFT': lift_symbol(ax, r['poly']); continue
        if r['code'] in ('OPEN', 'CIRC') and not r['label']: continue
        if r['label'] in ('store', 'prep'): continue
        c = r['poly'].representative_point() if r['name'] not in ('Entrance lobby + info',) else Point(B + d(QIBLA) * 20.5 - PERP_ * 3.0)
        a = r['poly'].area
        txt = f"{r['label']}\n{a:.0f} m²"
        if r['code'] in ('A1', 'A2') and 'display' in r['name']:
            b_ = float(r['name'][3:4])
            txt = f"{r['label']}\n{sum(x['poly'].area for x in ROOMS if x['name'].startswith(r['label'])):.0f} m²"
        label(ax, txt, (c.x, c.y), fs if a > 12 else fs - 1)
    columns(ax, level)
    if level == 'GF':
        lamellas(ax, B, R_OUT + 0.15, mod(13)[0], mod(17)[0]); lamellas(ax, B, R_OUT + 0.15, mod(18)[0], mod(19)[0])
        lamellas(ax, B, R_OUT + 0.15, mod(3)[0], mod(9)[0]); lamellas(ax, B, R_OUT + 0.15, mod(10)[0], mod(12)[0])
        lamellas(ax, S, RS_OUT + 0.15, QIBLA - 180 + 22.5, QIBLA + 180 - 22.5)
        for nm, xy in [('SERAMBI TENGAH\n(main gate · pop-up\nPekan Sehari bays)', B + d(256.3) * 14.5), ('GERBANG\nSELATAN', B + d(211.3) * 14.5), ('GERBANG\nTIMUR', B + d(67.3) * 14.5)]:
            label(ax, nm, xy, 4.6, '#7A2E14', w='bold')
        label(ax, 'COURT “TALAM”\nopen dining 100 seats', B + d(205) * 5.3, 4.6, '#7A2E14')
        label(ax, 'VERANDAH\n(covered walk)', B + d(150) * 10.0, 3.8, '#555555')
        label(ax, 'light\nwell', S, 4.0)
        label(ax, 'SERVICE\nCORRIDOR', S + d(QIBLA + 90) * 3.5, 3.6, '#555555')
    if level == 'L1':
        lamellas(ax, B, R_L1 + 0.1, mod(8)[0], mod(11)[0]); lamellas(ax, B, R_L1 + 0.1, mod(13)[0], mod(13)[1])
        lamellas(ax, S, RS_OUT + 0.15, QIBLA - 180 + 22.5, QIBLA + 180 - 22.5)
        q = S + d(QIBLA) * (RS_OUT + 1.5)
        ax.annotate('', xy=q + d(QIBLA) * 3.5, xytext=q, arrowprops=dict(arrowstyle='-|>', lw=0.8, color='#7A2E14'), zorder=9)
        label(ax, 'QIBLA\n292.3°', q + d(QIBLA) * 5.0 + np.array([0, 1.8]), 4.6, '#7A2E14', w='bold')
        label(ax, '12.5 m CLEAR SPAN\n(steel ribbon trusses)', B + d(112) * 16.5 + np.array([0, -3.3]), 3.8, '#7A2E14')
    grid(ax, level)

PERP_ = np.array([d(QIBLA)[1], -d(QIBLA)[0]])

def section_marks(ax):
    for nm, brg, r0, r1 in [('A', 110, -44, 26), ('B', 13.3, -26, 26)]:
        u = d(brg); p0, p1 = B + u * r0, B + u * r1
        line(ax, [p0, p1], 0.5, '#B4492B', 9, (0, (12, 3, 2, 3)))
        for p in (p0, p1):
            ax.add_patch(Circle(p, 1.3, fc='#B4492B', ec='none', zorder=10)); label(ax, nm, p, 6, 'white', 11, 'bold')

def north(ax, xy, s=3.0):
    x, y = xy
    ax.add_patch(MPoly([(x, y + s), (x + s * 0.4, y - s * 0.6), (x, y - s * 0.25), (x - s * 0.4, y - s * 0.6)], closed=True, fc=INK, ec=INK, zorder=12))
    label(ax, 'N', (x, y + s + 1.6), 7, w='bold')

def scalebar(ax, xy, lengths=(0, 5, 10, 20), unit_h=0.6, fs=5):
    x, y = xy
    for i in range(len(lengths) - 1):
        a, b_ = lengths[i], lengths[i + 1]
        ax.add_patch(Rectangle((x + a, y), b_ - a, unit_h, fc=INK if i % 2 == 0 else 'white', ec=INK, lw=0.4, zorder=12))
    for L in lengths: label(ax, f'{L}', (x + L, y - 1.2), fs)
    label(ax, 'm', (x + lengths[-1] + 2, y + 0.3), fs)
