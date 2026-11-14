"""Titik Temu – full 3D model spec for SketchUp (and DAE fallback).
Everything is derived from the same geometry as the Crit 1 drawings (geom.py / draw.py / site_el.py)."""
import json, math, io, base64
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity
from geom import *
import draw as DR
from draw import DOORS, GLAZE, LINE_GLAZE, WINDOWS, CS1, CL1, QV, PV_
import site_el as SE
from draw2 import L1_SECT, z_roof_top, OPEN_ARCS, in_arcs
from m3d import *

# ------------------------------------------------------------------ levels
ZG, ZSOF, ZL = 0.9, 5.0, 5.4            # GF FFL, GF slab soffit, L1 FFL / terrace
ZL1_TOP, ZSR_ROOF = 9.5, 9.9            # small ring L1 wall top, small ring roof top
ZCEIL = 9.9                              # east block ceilings
Z_CORE, Z_LIFT = 10.9, 12.4
DOOR_H = 2.4
B1, B2 = mod(8)[0], mod(13)[1]           # east block bearings 40.3 .. 148.3
def zdeck(r): return z_roof_top(r) - 0.3  # underside of ribbon roof deck
def P2(b, r, C=B): return C + d(b) * r
def tang(b): return d(b + 90)

# ------------------------------------------------------------------ spec containers
MATS, TAGS, DEFS, ROOT, SCENES = {}, [], {}, [], []
def mat(name, hexc, alpha=1.0, desc=''):
    h = hexc.lstrip('#'); MATS[name] = dict(c=[int(h[i:i + 2], 16) for i in (0, 2, 4)], a=alpha)
def tag(name, folder, visible=True, color=None): TAGS.append(dict(n=name, f=folder, v=visible, c=color))
def G(name, tag_=None, mat_=None, f=None, c=None, soft=25):
    n = dict(t='g', n=name)
    if tag_: n['tag'] = tag_
    if mat_: n['m'] = mat_
    if f: n['f'] = [x for x in f if x]
    if c: n['c'] = [x for x in c if x]
    if soft is not None: n['s'] = soft
    return n
def I(defname, o, x, y=None, z=(0, 0, 1), tag_=None, name=None):
    x = np.array(x, float); z = np.array(z, float); x /= np.linalg.norm(x); z /= np.linalg.norm(z)
    if y is None: y = np.cross(z, x)
    y = np.array(y, float); y /= np.linalg.norm(y)
    if np.dot(np.cross(x, y), z) < 0: y = -y
    n = dict(t='i', d=defname, o=[round(float(v), 4) for v in o], x=[round(float(v), 6) for v in x],
             y=[round(float(v), 6) for v in y], z=[round(float(v), 6) for v in z])
    if tag_: n['tag'] = tag_
    if name: n['n'] = name
    return n
def D(name, desc, children):
    if name not in DEFS: DEFS[name] = dict(desc=desc, c=[x for x in children if x])
    return name

# ------------------------------------------------------------------ materials
for n_, c_, a_ in [('TT Render white', '#F2EDE5', 1), ('TT Render interior', '#F7F4EF', 1), ('TT Concrete', '#CFCBC4', 1),
                   ('TT Slab white', '#F4F2EE', 1), ('TT Glass', '#8FB9CE', 0.35), ('TT Aluminium', '#4A5056', 1),
                   ('TT Steel dark', '#3A3F44', 1), ('TT Stainless', '#B8BDC2', 1), ('TT Roof metal white', '#F3F3F0', 1),
                   ('TT PV panel', '#24364A', 1), ('TT PTFE membrane', '#FAFAF8', 0.85), ('TT Ribbon white', '#FBFBFB', 1),
                   ('TT Crown terracotta', '#B4492B', 1), ('TT Terracotta lamella', '#B55A33', 1), ('TT Podium stone', '#D3CCBD', 1),
                   ('TT Court paving', '#E9DDC8', 1), ('TT Plaza granite', '#DDD0B5', 1), ('TT Path paving', '#E8E1D2', 1),
                   ('TT Asphalt', '#6F757A', 1), ('TT Line paint white', '#FFFFFF', 1), ('TT OKU blue', '#2E6DB4', 1),
                   ('TT Lawn', '#93B26F', 1), ('TT Planting', '#6E9A4E', 1), ('TT Timber deck', '#B98C5E', 1),
                   ('TT Door timber', '#8A6243', 1), ('TT Louvre', '#8B9196', 1), ('TT Tank GRP', '#BFC9D1', 1),
                   ('TT Rubber play', '#E7A57D', 1), ('TT Context', '#E3E3DF', 1), ('TT Tennis court', '#4F7C5C', 1),
                   ('TT River', '#6FA3B5', 1), ('TT Tree canopy', '#6E9A4E', 1), ('TT Tree trunk', '#6B5B45', 1),
                   ('TT Terrazzo', '#E2DED6', 1), ('TT Mihrab timber', '#7A5232', 1)]:
    mat(n_, c_, a_)

# ------------------------------------------------------------------ tags
T = {}
for key, name, folder, vis in [
    ('base', 'A Site - Basemap (group plan)', '1 Site', True), ('bound', 'A Site - Boundary & setback lines', '1 Site', True),
    ('ground', 'A Site - Ground, lawn & paving', '1 Site', True), ('roads', 'A Site - Roads & parking', '1 Site', True),
    ('ctx', 'A Site - Context massing', '1 Site', True),
    ('pod', 'B Podium, steps & ramps', '2 Ground floor', True), ('gfw', 'B GF - Walls', '2 Ground floor', True),
    ('gfg', 'B GF - Glazing & louvres', '2 Ground floor', True), ('gfd', 'B GF - Doors', '2 Ground floor', True),
    ('gfc', 'B GF - Columns', '2 Ground floor', True),
    ('l1s', 'C L1 - Floor slab', '3 Level 1', True), ('l1w', 'C L1 - Walls', '3 Level 1', True),
    ('l1g', 'C L1 - Glazing & louvres', '3 Level 1', True), ('l1d', 'C L1 - Doors', '3 Level 1', True),
    ('l1c', 'C L1 - Columns & posts', '3 Level 1', True), ('l1ce', 'C L1 - Ceilings', '3 Level 1', True),
    ('terr', 'C Terrace - deck, planters & balustrade', '3 Level 1', True),
    ('core', 'D Core walls', '4 Core & stairs', True), ('stair', 'D Stairs', '4 Core & stairs', True), ('lift', 'D Lifts', '4 Core & stairs', True),
    ('roof', 'E Roof - slabs & ribbon roof', '5 Roof', True), ('truss', 'E Roof - steel trusses', '5 Roof', True),
    ('pv', 'E Roof - PV panels', '5 Roof', True), ('tank', 'E Roof - water tanks', '5 Roof', True),
    ('fin', 'F Terracotta lamellas', '6 Skin & canopies', True), ('ocu', 'F Oculus canopy', '6 Skin & canopies', True),
    ('rib', 'F Ribbon canopies', '6 Skin & canopies', True), ('crown', 'F Simpul crown', '6 Skin & canopies', True),
    ('furn', 'G Court & terrace furniture', '7 Landscape & furniture', True), ('tree', 'G Trees', '7 Landscape & furniture', True),
    ('bike', 'G Bicycle stands', '7 Landscape & furniture', True),
    ('grid', 'H Set-out & grids', '8 Drawing aids', False), ('lab0', 'H Room labels GF', '8 Drawing aids', False),
    ('lab1', 'H Room labels L1', '8 Drawing aids', False), ('sec', 'H Section planes', '8 Drawing aids', True)]:
    T[key] = name; tag(name, folder, vis)

# ------------------------------------------------------------------ helper geometry
CORE_FP = unary_union([core1_stair.buffer(0.25, join_style=2), core1_lifts.buffer(0.25, join_style=2)]).buffer(0.0)
CORE_SHELL = unary_union([CORE_FP.difference(core1_stair).difference(core1_lifts),
                          rect_at(CL1, 0.2, 2.4, QIBLA)])                       # divider between the 2 lifts
LIFT_SHELL = core1_lifts.buffer(0.25, join_style=2).difference(core1_lifts).union(rect_at(CL1, 0.2, 2.4, QIBLA))
EAST_ZONE = sector(B, R_COURT - 0.3, R_L1 + 0.6, B1 - 1.2, B2 + 1.2)
# stair 2 (module 10): dog-leg along bearing mid(10)
B_ST2 = (mod(10)[0] + 9) % 360
ST2 = dict(u=d(B_ST2), v=tang(B_ST2), u_in=R_VER + 0.13, u0=R_VER + 0.13 + 1.34, w=1.2, gap=0.2)
ST2['u1'] = ST2['u0'] + 12 * 0.28; ST2['u2'] = ST2['u1'] + 1.3
def st2_pt(u, v): return B + ST2['u'] * u + ST2['v'] * v
ST2_OPEN = Polygon([st2_pt(ST2['u0'], -1.3), st2_pt(ST2['u2'], -1.3), st2_pt(ST2['u2'], 1.3), st2_pt(ST2['u0'], 1.3)])

def rect_cut(c, t, w, depth=0.3):
    t = np.array(t, float); t /= np.linalg.norm(t); n = np.array([-t[1], t[0]])
    return Polygon([c + t * w / 2 + n * depth, c - t * w / 2 + n * depth, c - t * w / 2 - n * depth, c + t * w / 2 - n * depth])
def line_cut(a, b, depth=0.3, inset=0.3):
    u = (b - a) / np.linalg.norm(b - a); n = np.array([-u[1], u[0]]); a2, b2 = a + u * inset, b - u * inset
    return Polygon([a2 + n * depth, b2 + n * depth, b2 - n * depth, a2 - n * depth])

def wall_full(level):
    rs = [r for r in ROOMS if r['level'] == level and r['code'] != 'OPEN']
    env = unary_union([r['poly'] for r in rs]).buffer(0.01).buffer(-0.01)
    inner = unary_union([LineString(q.exterior.coords).buffer(0.075, cap_style=2, join_style=2) for r in rs if r['code'] not in ('CIRC',) for q in polys(r['poly'])])
    ext = unary_union([LineString(q.exterior.coords).buffer(0.13, cap_style=2, join_style=2) for q in polys(env)] +
                      [LineString(h.coords).buffer(0.13, cap_style=2, join_style=2) for q in polys(env) for h in q.interiors])
    w = unary_union([inner, ext]).intersection(env.buffer(0.14, join_style=2))
    return w

def across(c, t, geom, reach=0.7):
    """thickness of geom across point c (wall direction t) -> (length, midpoint)"""
    t = np.array(t, float); t /= np.linalg.norm(t); n = np.array([-t[1], t[0]])
    seg = LineString([c - n * reach, c + n * reach]).intersection(geom)
    if seg.is_empty: return None, None
    segs = [seg] if seg.geom_type == 'LineString' else [g for g in seg.geoms if g.geom_type == 'LineString']
    if not segs: return None, None
    s = min(segs, key=lambda g: g.distance(Point(c)))
    cs = np.array(s.coords); return float(np.linalg.norm(cs[-1] - cs[0])), (cs[0] + cs[-1]) / 2

def arc_ring_poly(C, r0, r1, b0, b1, seg=0.5):
    if b1 <= b0: b1 += 360
    n = max(2, int(math.ceil(math.radians(b1 - b0) * r1 / seg)))
    return sector(C, r0, r1, b0, b1, n + 1)

# ------------------------------------------------------------------ openings registry
OPEN = {'GF': [], 'L1': [], 'L1E': [], 'CORE': []}
def classify_level(level, c):
    if Point(c).distance(CORE_FP) < 0.45: return 'CORE'
    if level == 'L1' and EAST_ZONE.contains(Point(c)): return 'L1E'
    return level
FFL = {'GF': ZG, 'L1': ZL}
for level in ('GF', 'L1'):
    for c, t, w, sw in DOORS[level]:
        c = np.array(c, float); key = classify_level(level, c)
        OPEN[key].append(dict(k='door', c=c, t=np.array(t, float), w=w, hinged=sw is not None, lv=level,
                              zb=FFL[level], zt=FFL[level] + DOOR_H, cut=rect_cut(c, t, w)))
    for C, r, b0, b1 in GLAZE[level]:
        cen = P2((b0 + (b1 - b0) % 360 / 2), r, C); key = classify_level(level, cen)
        OPEN[key].append(dict(k='arc', C=np.array(C), r=r, b0=b0 + 0.6, b1=(b1 if b1 > b0 else b1 + 360) - 0.6, lv=level, kind='glass',
                              zb=FFL[level], zt=None, cut=sector(C, r - 0.25, r + 0.25, b0 + 0.6, b1 - 0.6, 30)))
    for C, r, b0, b1, sill, head, kind in WINDOWS[level]:
        cen = P2((b0 + (b1 - b0) % 360 / 2), r, C); key = classify_level(level, cen)
        OPEN[key].append(dict(k='arc', C=np.array(C), r=r, b0=b0 + 0.6, b1=(b1 if b1 > b0 else b1 + 360) - 0.6, lv=level, kind=kind,
                              zb=FFL[level] + sill, zt=FFL[level] + head, cut=sector(C, r - 0.25, r + 0.25, b0 + 0.6, b1 - 0.6, 30)))
    for a, b_ in LINE_GLAZE[level]:
        OPEN[level].append(dict(k='line', a=np.array(a), b=np.array(b_), lv=level, kind='glass', zb=FFL[level],
                                zt=FFL[level] + (3.5 if level == 'GF' else 3.0), cut=line_cut(np.array(a), np.array(b_))))
# default heads for full-height glazing
for o in OPEN['GF']:
    if o['k'] in ('arc', 'line') and o['zt'] is None: o['zt'] = ZG + 3.5
for o in OPEN['L1']:
    if o['k'] in ('arc', 'line') and o['zt'] is None: o['zt'] = ZL + 3.0
for o in OPEN['L1E']:
    if o['k'] == 'arc' and o['zt'] is None: o['zt'] = zdeck(o['r'])

# ------------------------------------------------------------------ wall builder (bands)
def wall_bands(piece, z0, z1, opens):
    zs = {z0, z1}
    rel = [o for o in opens if o['cut'].intersects(piece)]
    for o in rel:
        for z in (o['zb'], o['zt']):
            if z0 < z < z1: zs.add(round(z, 4))
    zs = sorted(zs); bands = []
    for k in range(len(zs) - 1):
        za, zb_ = zs[k], zs[k + 1]
        cuts = [o['cut'] for o in rel if o['zb'] <= za + 1e-6 and o['zt'] >= zb_ - 1e-6]
        g = piece.difference(unary_union(cuts)) if cuts else piece
        bands.append((za, zb_, g))
    return bands

def build_walls(geom, z0, z1, opens, prefix, tag_, mat_='TT Render white'):
    out = []
    for i, piece in enumerate(sorted(polys(clean(geom, 0.01)), key=lambda q: -q.area)):
        fs = bsolid(wall_bands(piece, z0, z1, opens))
        if fs: out.append(G(f'{prefix} {i + 1:02d}', tag_, mat_, fs))
    return out

# ------------------------------------------------------------------ component definitions
def defn_box(name, desc, parts):
    """parts: [(mat, faces)]"""
    return D(name, desc, [G(f'{name} · {m.replace("TT ", "")}', None, m, f) for m, f in parts])

def door_def(w, thk, kind):
    w, thk = round(w, 2), round(max(thk, 0.1), 2); H = DOOR_H
    name = f'Door {kind} {int(w * 1000)}x{int(H * 1000)} (wall {int(thk * 1000)})'
    if name in DEFS: return name
    fr = 0.05; parts = []
    frame = box_faces(-w / 2, -thk / 2, 0, -w / 2 + fr, thk / 2, H) + box_faces(w / 2 - fr, -thk / 2, 0, w / 2, thk / 2, H) + \
            box_faces(-w / 2 + fr, -thk / 2, H - fr, w / 2 - fr, thk / 2, H)
    if kind == 'hinged':
        leaves = [(-w / 2 + fr + 0.003, w / 2 - fr - 0.003)] if w <= 1.2 else [(-w / 2 + fr + 0.003, -0.003), (0.003, w / 2 - fr - 0.003)]
        lf = []
        for a, b_ in leaves: lf += box_faces(a, -0.022, 0.01, b_, 0.022, H - fr - 0.003)
        parts = [('TT Aluminium', frame), ('TT Door timber', lf)]
    elif kind == 'sliding glass':
        g1 = box_faces(-w / 2 + fr, -0.035, 0.01, 0.03, -0.015, H - fr); g2 = box_faces(-0.03, 0.015, 0.01, w / 2 - fr, 0.035, H - fr)
        st = box_faces(-0.03, -0.04, 0.0, 0.03, 0.04, H - fr)
        parts = [('TT Aluminium', frame + st), ('TT Glass', g1 + g2)]
    else:   # lift landing door
        p1 = box_faces(-w / 2 + fr, -0.03, 0.0, -0.002, 0.0, H - fr); p2 = box_faces(0.002, -0.03, 0.0, w / 2 - fr, 0.0, H - fr)
        parts = [('TT Stainless', frame + p1 + p2)]
    return defn_box(name, f'{kind} door, clear opening {int(w * 1000)} mm, height {int(H * 1000)} mm', parts)

def place_door(o, wall_geom, tag_, z):
    thk, mid = across(o['c'], o['t'], wall_geom)
    if thk is None: thk, mid = 0.15, o['c']
    kind = 'lift' if (o['w'] == 1.1 and Point(o['c']).distance(core1_lifts) < 0.5) else ('hinged' if o['hinged'] else 'sliding glass')
    dn = door_def(o['w'], thk, kind)
    t = np.array([o['t'][0], o['t'][1], 0.0])
    return I(dn, [mid[0], mid[1], z], t, tag_=tag_)

def mullion_def(h, kind='glass'):
    name = f'Mullion 60x120 h{int(round(h * 1000))}' if kind == 'glass' else f'Louvre post 60x60 h{int(round(h * 1000))}'
    if name in DEFS: return name
    dep = 0.12 if kind == 'glass' else 0.06
    return defn_box(name, 'aluminium mullion (x = along glazing, y = across)', [('TT Aluminium', box_faces(-0.03, -dep / 2, 0, 0.03, dep / 2, h))])

def glazing_arc(o, doors, tag_):
    """glass / louvre panels on an arc opening, doors subtracted, transom glass above doors, mullions."""
    C, r, b0, b1, zb, zt = o['C'], o['r'], o['b0'], o['b1'], o['zb'], o['zt']
    kind = o['kind']; th = 0.012 if kind == 'glass' else 0.025
    mt = 'TT Glass' if kind == 'glass' else 'TT Louvre'
    on = []
    for dd in doors:
        dc = dd['c']
        if abs(np.linalg.norm(dc - C) - r) < 0.08:
            bd = math.degrees(math.atan2(dc[0] - C[0], dc[1] - C[1])) % 360
            rel = (bd - b0) % 360
            if 0 <= rel <= (b1 - b0): on.append((b0 + rel, math.degrees(dd['w'] / 2 / r) + 0.02))
    lower = arc_ring_poly(C, r - th, r + th, b0, b1)
    for bd, hw in on: lower = lower.difference(sector(C, r - 0.5, r + 0.5, bd - hw, bd + hw, 6))
    faces = []
    head = zb + DOOR_H
    if on and zt > head + 0.05:
        faces += bsolid([(zb, head, lower), (head, zt, arc_ring_poly(C, r - th, r + th, b0, b1))])
    else:
        faces += bsolid([(zb, zt, lower)])
    kids = [G('panels', None, mt, faces)]
    # mullions: at ends, at door jambs and at <= 1.5 m spacing
    L = math.radians(b1 - b0) * r; n = max(1, int(math.ceil(L / (1.5 if kind == 'glass' else 1.2))))
    angs = [b0 + (b1 - b0) * k / n for k in range(n + 1)]
    for bd, hw in on:
        angs = [a for a in angs if abs(a - bd) > hw + 0.6 * 180 / math.pi / r] + [bd - hw, bd + hw]
    mdef = mullion_def(zt - zb, kind)
    for a in sorted(angs):
        p = P2(a, r, C); full = all(abs(a - bd) > hw + 1e-3 for bd, hw in on) or True
        kids.append(I(mdef, [p[0], p[1], zb], [*tang(a), 0]))
    if on and zt > head + 0.05:   # transom at door head
        kids.append(G('transom', None, 'TT Aluminium', bsolid([(head - 0.03, head + 0.03, arc_ring_poly(C, r - 0.06, r + 0.06, b0, b1))])))
    if zt - zb > 5.0:
        for zz in (zb + 4.8,):
            kids.append(G('transom', None, 'TT Aluminium', bsolid([(zz - 0.03, zz + 0.03, arc_ring_poly(C, r - 0.06, r + 0.06, b0, b1))])))
    return G(f'{"Glazing" if kind == "glass" else "Louvres"} R{r:.2f}', tag_, None, None, kids)

def glazing_line(o, doors, tag_):
    a, b_, zb, zt = o['a'], o['b'], o['zb'], o['zt']
    u = (b_ - a) / np.linalg.norm(b_ - a); n2 = np.array([-u[1], u[0]]); a2, b2 = a + u * 0.3, b_ - u * 0.3; L = np.linalg.norm(b2 - a2)
    on = []
    for dd in doors:
        rel = dd['c'] - a2
        if abs(rel @ n2) < 0.08 and 0 <= rel @ u <= L: on.append((rel @ u, dd['w'] / 2 + 0.003))
    def strip(s0, s1, th=0.012):
        return Polygon([a2 + u * s0 + n2 * th, a2 + u * s1 + n2 * th, a2 + u * s1 - n2 * th, a2 + u * s0 - n2 * th])
    lower = strip(0, L)
    for s, hw in on: lower = lower.difference(strip(s - hw, s + hw, 0.5))
    head = zb + DOOR_H
    faces = bsolid([(zb, head, lower), (head, zt, strip(0, L))]) if on and zt > head + 0.05 else bsolid([(zb, zt, lower)])
    kids = [G('panels', None, 'TT Glass', faces)]
    n = max(1, int(math.ceil(L / 1.5))); ss = [L * k / n for k in range(n + 1)]
    for s, hw in on: ss = [x for x in ss if abs(x - s) > hw + 0.6] + [s - hw, s + hw]
    mdef = mullion_def(zt - zb)
    for s in sorted(ss):
        p = a2 + u * s; kids.append(I(mdef, [p[0], p[1], zb], [u[0], u[1], 0]))
    if on and zt > head + 0.05:
        kids.append(G('transom', None, 'TT Aluminium', bsolid([(head - 0.03, head + 0.03, strip(0, L, 0.06))])))
    return G('Glazing (straight)', tag_, None, None, kids)

# ================================================================== 1. SITE
def site_part():
    nodes = []
    # basemap image (resampled to a uniform 0.2 m / px grid, true north up)
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        A = np.load('/home/claude/crit1/affine.npy')
        x0, x1, y0, y1, ppm = -70.0, 190.0, -90.0, 150.0, 5.0
        W_, H_ = int((x1 - x0) * ppm), int((y1 - y0) * ppm)
        src = Image.open('/mnt/user-data/uploads/A0_BASEMAP_Temerloh_template_copy_jpg.jpeg').convert('RGB')
        a, b_, c = A[0, 0] / ppm, -A[1, 0] / ppm, A[0, 0] * x0 + A[1, 0] * y1 + A[2, 0]
        dd_, e, f = A[0, 1] / ppm, -A[1, 1] / ppm, A[0, 1] * x0 + A[1, 1] * y1 + A[2, 1]
        img = src.transform((W_, H_), Image.AFFINE, (a, b_, c, dd_, e, f), resample=Image.BILINEAR)
        img.save('/home/claude/crit1/out/basemap_site.jpg', quality=78)
        bio = io.BytesIO(); img.save(bio, 'JPEG', quality=78)
        nodes.append(dict(t='img', tag=T['base'], o=[x0, y0, -0.03], w=x1 - x0, data=base64.b64encode(bio.getvalue()).decode(), n='Basemap'))
    except Exception as ex:
        print('basemap skipped', ex)
    # boundary + setback (edges)
    nodes.append(dict(t='e', tag=T['bound'], n='Site boundary (5,361 m2)', pts=[[x, y, 0.08] for x, y in list(SITE_POLY.exterior.coords)[:-1]], closed=True))
    for q in polys(BUILDABLE):
        nodes.append(dict(t='e', tag=T['bound'], n='Building setback line', pts=[[x, y, 0.07] for x, y in list(q.exterior.coords)[:-1]], closed=True))
    return nodes

# podium + steps + ramps
P0 = unary_union([Point(B).buffer(R_OVH + 3.0, 180), Point(S).buffer(RS_OUT + 3.0, 180), lobby.buffer(3.0)]).buffer(0)
DOCK = SE.YARD.buffer(0.6)
RAMPS, RAMP_Z = [], []
def path_ls(pts): return LineString(pts)
def ramp_for(name, pts, w_ramp=2.0, grad=15.0):
    L = path_ls(pts)
    # first entry into the top tier P0
    s_top = None
    for s in np.linspace(0, L.length, 2000):
        if P0.contains(L.interpolate(s)): s_top = s; break
    if s_top is None: return None
    run = 0.9 * grad; s0 = max(0.0, s_top - run)
    seg = LineString([L.interpolate(s) for s in np.linspace(s0, min(L.length, s_top + 0.6), 60)])
    poly = seg.buffer(w_ramp / 2, cap_style=2, join_style=2)
    def zf(x, y, s0=s0, s_top=s_top, L=L):
        s = L.project(Point(x, y)); return round(0.9 * min(1.0, max(0.0, (s - s0) / (s_top - s0))), 4)
    return dict(name=name, poly=poly, zf=zf, s0=s0, s_top=s_top, L=L, grad=(s_top - s0) / 0.9)
for k, (nm, pts, w) in SE.RIBBONS.items():
    rp = ramp_for(k, pts)
    if rp: RAMPS.append(rp)
RAMP_U = unary_union([r['poly'] for r in RAMPS])
T1 = P0.buffer(0.9, join_style=1).difference(P0.buffer(0.45, join_style=1)).difference(RAMP_U).difference(DOCK)
T2 = P0.buffer(0.45, join_style=1).difference(P0).difference(RAMP_U).difference(DOCK)
PODIUM_FOOT = P0.buffer(0.9, join_style=1).difference(DOCK).union(P0)
def ground_z(x, y):
    p = Point(x, y)
    if P0.contains(p): return ZG
    for r in RAMPS:
        if r['poly'].contains(p): return r['zf'](x, y)
    if T2.contains(p): return 0.6
    if T1.contains(p): return 0.3
    return 0.0

def podium_part():
    kids = [G('Podium (GF +0.900)', None, 'TT Podium stone', prism(P0, 0, ZG)),
            G('Step tier 2 (+0.600)', None, 'TT Podium stone', prism(T2, 0, 0.6)),
            G('Step tier 1 (+0.300)', None, 'TT Podium stone', prism(T1, 0, 0.3))]
    for r in RAMPS:
        poly = clean(r['poly'].difference(P0))
        kids.append(G(f'Ramp {r["name"].title()} (1:{r["grad"]:.0f})', None, 'TT Path paving', vtop(poly, 0.0, lambda x, y, zf=r['zf']: max(0.02, zf(x, y)))))
        # handrails both sides at 900 above ramp
        L = r['L']; ss = np.linspace(r['s0'], r['s_top'], 12)
        for side in (-1, 1):
            rail = []
            for s in ss:
                p = np.array(L.interpolate(s).coords[0]); s2 = min(L.length, s + 0.05)
                q = np.array(L.interpolate(s2).coords[0]); t = (q - p) / (np.linalg.norm(q - p) or 1); n = np.array([-t[1], t[0]])
                pp = p + n * side * 0.95; rail.append([pp[0], pp[1], r['zf'](*p) + 0.9])
            fs = []
            for a, b_ in zip(rail[:-1], rail[1:]): fs += beam(a, b_, 0.05, 0.05)
            for k_ in range(0, len(rail), 3): fs += beam([rail[k_][0], rail[k_][1], rail[k_][2] - 0.9], rail[k_], 0.05, 0.05)
            kids.append(G(f'Ramp handrail {r["name"].title()}', None, 'TT Stainless', fs, soft=None))
    return G('PODIUM, STEPS & RAMPS', T['pod'], None, None, kids)

def landscape_part():
    kids = []
    hard_roads = unary_union([SE.DRIVE, SE.YARD, SE.LAYBY, SE.PARK_AISLE] + SE.PARK_STAFF + SE.MOTOR + [SE.OKU_BAY]).difference(P0)
    paths = []
    for r in RAMPS:
        L = r['L']
        if r['s0'] > 0.3:
            seg = LineString([L.interpolate(s) for s in np.linspace(0, r['s0'] + 0.05, 30)])
            paths.append(seg.buffer(1.0, cap_style=2, join_style=2))
    paths = unary_union(paths).difference(PODIUM_FOOT).difference(hard_roads) if paths else MultiPolygon()
    plaza = SE.PLAZA_SE.difference(PODIUM_FOOT).difference(RAMP_U).difference(paths)
    garden = SE.GARDEN_N.difference(PODIUM_FOOT).difference(RAMP_U).difference(paths)
    suction = SE.SUCTION
    lawn = SITE_POLY.difference(unary_union([PODIUM_FOOT, RAMP_U, hard_roads, paths, plaza, garden, suction]))
    kids += [G('Lawn', None, 'TT Lawn', prism(lawn, 0, 0.02)), G('Dataran Temu plaza (granite)', None, 'TT Plaza granite', prism(plaza, 0, 0.05)),
             G('Ribbon footpaths', None, 'TT Path paving', prism(paths, 0, 0.05)), G('Taman Ulam garden lawn', None, 'TT Lawn', prism(garden, 0, 0.03)),
             G('Suction tank cover slab (tank below ground)', None, 'TT Concrete', prism(suction, 0, 0.1))]
    # herb beds in Taman Ulam (11 states)
    beds = []
    for k in range(11):
        cx, cy = 60.5 + (k % 6) * 4.2, 49.0 + (k // 6) * 4.5
        bb = box(cx - 1.4, cy - 0.7, cx + 1.4, cy + 0.7)
        if garden.buffer(-0.3).contains(bb): beds.append(bb)
    kids.append(G('Taman Ulam herb beds (11 states)', None, 'TT Planting', prism(unary_union(beds), 0.03, 0.45)))
    land = G('GROUND, LAWN & PAVING', T['ground'], None, None, kids)
    # roads + parking
    rk = [G('Service drive, yard, lay-by & parking (asphalt)', None, 'TT Asphalt', prism(hard_roads, 0, 0.04))]
    lines = []
    for p in SE.PARK_STAFF + SE.MOTOR:
        lines.append(LineString(p.exterior.coords).buffer(0.05, cap_style=2, join_style=2).intersection(p.buffer(0.05)))
    rk.append(G('Bay markings', None, 'TT Line paint white', prism(unary_union(lines), 0.04, 0.045)))
    rk.append(G('OKU bay (blue)', None, 'TT OKU blue', prism(SE.OKU_BAY.buffer(-0.06), 0.04, 0.044)))
    road = Polygon([tuple(SE.road_pt(-70) - SE.N_IN * 0.5), tuple(SE.road_pt(190) - SE.N_IN * 0.5), tuple(SE.road_pt(190) - SE.N_IN * 11), tuple(SE.road_pt(-70) - SE.N_IN * 11)])
    rk.append(G('Jalan Tok Muda Awang Ngah', None, 'TT Asphalt', prism(road, 0, 0.03)))
    rk.append(G('East access lane', None, 'TT Asphalt', prism(Polygon([(113.5, -40), (123, -40), (123, 120), (113.5, 120)]).difference(road), 0, 0.03)))
    roads = G('ROADS & PARKING', T['roads'], None, None, rk)
    # context
    ck = []
    for i_, ((x0, y0, x1, y1), hgt) in enumerate([((56, 65, 106, 112), 10.0), ((-18, 44, 4.4, 67), 7.0), ((40, -70, 150, -52), 9.0)]):
        ck.append(G(f'Neighbour block {i_ + 1} (massing)', None, 'TT Context', box_faces(x0, y0, 0, x1, y1, hgt)))
    ck.append(G('Tennis courts (east)', None, 'TT Tennis court', box_faces(91, 5, 0, 109, 63, 0.06)))
    ck.append(G('Sungai Pahang (indicative)', None, 'TT River', box_faces(250, -200, -0.5, 330, 250, -0.45)))
    ctx = G('CONTEXT', T['ctx'], None, None, ck)
    return [land, roads, ctx]

# ================================================================== 2. GF / L1 walls, glazing, doors
def gf_part():
    wf = wall_full('GF').simplify(0.003).buffer(0).difference(CORE_FP)
    walls = build_walls(wf, ZG, ZSOF, OPEN['GF'], 'GF wall', None)
    doors = [o for o in OPEN['GF'] if o['k'] == 'door']
    glz = [glazing_arc(o, doors, None) if o['k'] == 'arc' else glazing_line(o, doors, None) for o in OPEN['GF'] if o['k'] in ('arc', 'line')]
    dr = [place_door(o, wf, None, ZG) for o in doors]
    # columns
    cdef_r = defn_box('Column RC Ø500 h4100', 'GF verandah column on the court edge', [('TT Concrete', cyl_faces(0, 0, 0.25, 0, ZSOF - ZG, 24))])
    cdef_s = defn_box('Column RC 500x500 h4100', 'GF perimeter column (big ring)', [('TT Concrete', box_faces(-0.25, -0.25, 0, 0.25, 0.25, ZSOF - ZG))])
    cdef_k = defn_box('Column RC 400x400 h4100', 'GF column (small ring)', [('TT Concrete', box_faces(-0.2, -0.2, 0, 0.2, 0.2, ZSOF - ZG))])
    cols = []
    for r, b in COLS_BIG:
        p = P2(b, r)
        if r == R_COURT: cols.append(I(cdef_r, [p[0], p[1], ZG], [*tang(b), 0]))
        else: cols.append(I(cdef_s, [p[0], p[1], ZG], [*tang(b), 0]))
    for r, b in COLS_SMALL:
        p = P2(b, r, S); cols.append(I(cdef_k, [p[0], p[1], ZG], [*tang(b), 0]))
    return [G('GF WALLS (walls + lintels, 4.1 m)', T['gfw'], None, None, walls), G('GF GLAZING & LOUVRES', T['gfg'], None, None, glz),
            G('GF DOORS', T['gfd'], None, None, dr), G('GF COLUMNS', T['gfc'], None, None, cols)], wf

def l1_part():
    wf = wall_full('L1').simplify(0.003).buffer(0).difference(CORE_FP).difference(EAST_ZONE)
    walls = build_walls(wf, ZL, ZL1_TOP, OPEN['L1'], 'L1 wall', None)
    doors = [o for o in OPEN['L1'] if o['k'] == 'door']
    glz = [glazing_arc(o, doors, None) if o['k'] == 'arc' else glazing_line(o, doors, None) for o in OPEN['L1'] if o['k'] in ('arc', 'line')]
    dr = [place_door(o, wf, None, ZL) for o in doors]
    # mihrab panel on the qibla wall (male prayer)
    mh = sector(S, RS_OUT - 0.13 - 0.06, RS_OUT - 0.13, QIBLA - 3.5, QIBLA + 3.5, 8)
    mihrab = G('Mihrab panel (qibla 292.3°)', None, 'TT Mihrab timber', prism(mh, ZL, ZL + 2.6))
    # columns small ring L1
    cdef_k = defn_box('Column RC 400x400 h4100', '', [('TT Concrete', box_faces(-0.2, -0.2, 0, 0.2, 0.2, ZSOF - ZG))])
    cols = [I(cdef_k, [P2(b, r, S)[0], P2(b, r, S)[1], ZL], [*tang(b), 0]) for r, b in COLS_SMALL]
    return walls, glz, dr, [mihrab], cols, wf

# ---------------- east block (gallery + Dapur Rewang hall + stores + toilets) explicit
def east_part():
    opens = OPEN['L1E']; doors = [o for o in opens if o['k'] == 'door']
    walls, extra = [], []
    def dang(t, r): return math.degrees(t / r)
    # arc walls (constant top)
    arcs = [('Inner envelope R11.0', R_VER, 0.26, B1, B2, zdeck(R_VER)),
            ('Outer envelope R21.5', R_L1, 0.26, B1, B2, zdeck(R_L1)),
            ('Stair 2 / equipment store R18.1', R_OUT, 0.15, mod(10)[0], mod(10)[1], ZCEIL),
            ('Hall / furniture store R14.75', 14.75, 0.15, mod(12)[0], mod(12)[1], zdeck(14.75))]
    for nm, r, th, b0, b1, top in arcs:
        e0 = dang(0.13 + 0.002, r); geom = arc_ring_poly(B, r - th / 2, r + th / 2, b0 + e0, b1 - e0)
        fs = bsolid(wall_bands(geom, ZL, top, opens))
        walls.append(G(f'L1E wall {nm}', None, 'TT Render white', fs))
    # radial walls (vertical profiles with sloped tops)
    m9 = mod(9); m13 = mod(13)
    rads = [(B1, R_VER, R_L1, 0.26, 'deck', 'End wall 40.3°'), (mod(9)[0], R_VER, R_L1, 0.15, 'deck', 'Gallery | store'),
            (m9[0] + 18 * 20 / 38, R_VER, R_L1, 0.15, ZCEIL, 'Store | staff'), (m9[0] + 18 * 30 / 38, R_VER, R_L1, 0.15, ZCEIL, 'Staff | J/L'),
            (mod(10)[0], R_VER, R_L1, 0.15, ZCEIL, 'J/L | stair 2'), (mod(11)[0], R_VER, R_L1, 0.2, 'deck', 'Stair 2 + store | hall'),
            (mod(12)[0], R_VER, 14.75, 0.15, 'deck', 'Furniture store | hall'), (mod(13)[0], R_VER, R_L1, 0.2, 'deck', 'Hall | toilets'),
            (m13[0] + 18 * 0.42, R_VER, R_L1, 0.15, ZCEIL, 'Male | female WC'), (m13[0] + 18 * 0.84, R_VER, R_L1, 0.15, ZCEIL, 'Female WC | janitor'),
            (B2, R_VER, R_L1, 0.26, 'deck', 'End wall 148.3°')]
    for b, r0, r1, th, top, nm in rads:
        r0e, r1e = r0 + 0.13, r1 - 0.13
        if nm.startswith('End'): r0e, r1e = r0 - 0.13, r1 + 0.13
        if r1 == 14.75: r1e = 14.75 - 0.075
        notches = []
        for o in doors:
            c = o['c']; v = c - B; rr = np.linalg.norm(v); bd = math.degrees(math.atan2(v[0], v[1])) % 360
            if abs(((bd - b) + 180) % 360 - 180) < 0.3 and r0 < rr < r1: notches.append((rr - o['w'] / 2, rr + o['w'] / 2))
        zt = (lambda r: zdeck(r)) if top == 'deck' else (lambda r: top)
        prof = [(r0e, ZL)]
        for a, b_ in sorted(notches): prof += [(a, ZL), (a, ZL + DOOR_H), (b_, ZL + DOOR_H), (b_, ZL)]
        prof += [(r1e, ZL), (r1e, zt(r1e)), (r0e, zt(r0e))]
        tv = tang(b)
        pts3 = [[*(B + d(b) * r - tv * th / 2), z] for r, z in prof]
        walls.append(G(f'L1E wall {nm}', None, 'TT Render white', xprism(pts3, [tv[0] * th, tv[1] * th, 0])))
    # door instances + glazing
    wall2d = unary_union([arc_ring_poly(B, r - th / 2, r + th / 2, b0, b1) for _, r, th, b0, b1, _ in arcs] +
                         [LineString([B + d(b) * r0, B + d(b) * r1]).buffer(th / 2, cap_style=2) for b, r0, r1, th, _, _ in rads])
    dr = [place_door(o, wall2d, None, ZL) for o in doors]
    glz = [glazing_arc(o, doors, None) for o in opens if o['k'] == 'arc']
    # ceilings over service rooms
    ce = []
    for b0, b1, r0, r1 in [(mod(9)[0], mod(10)[1], R_VER, R_L1), (mod(13)[0], mod(13)[1], R_VER, R_L1), (mod(12)[0], mod(12)[1], R_VER, 14.75)]:
        e0 = dang(0.1, r0)
        g = arc_ring_poly(B, r0 + 0.13, r1 - (0.13 if r1 == R_L1 else 0.075), b0 + e0, b1 - e0)
        ce.append(G(f'Ceiling {b0:.1f}–{b1:.1f}°', None, 'TT Render interior', prism(g, ZCEIL, ZCEIL + 0.08)))
    return walls, glz, dr, ce, wall2d

# ================================================================== 3. slabs, core, stairs, lifts
def slabs_part():
    ll = DR._room('L1', 'L1 lift lobby'); rec = DR._room('L1', 'Admin reception + waiting')
    sl1 = unary_union([ring(B, R_COURT, R_OVH), L1_SECT, lobby, ring(S, RS_WELL, RS_OUT), ll, rec]).buffer(0.01, join_style=2).buffer(-0.01, join_style=2)
    sl1 = sl1.difference(CORE_FP).difference(ST2_OPEN)
    l1slab = G('L1 slab / terrace slab (5.000–5.400)', T['l1s'], 'TT Slab white', prism(sl1, ZSOF, ZL))
    roofp = unary_union([ring(S, RS_WELL, RS_OUT), ll.buffer(0.13, join_style=2), rec]).buffer(0.01, join_style=2).buffer(-0.01, join_style=2).difference(CORE_FP)
    roof = G('Small ring + link roof slab (9.500–9.900)', None, 'TT Slab white', prism(roofp, ZL1_TOP, ZSR_ROOF))
    par = G('Roof parapet / upstand (to +10.500)', None, 'TT Render white', prism(roofp.difference(roofp.buffer(-0.2, join_style=2)), ZSR_ROOF, 10.5))
    return l1slab, roof, par, roofp

def core_part():
    opens = OPEN['CORE']
    cuts = []
    for o in opens:
        c = o['c']; cuts.append(dict(cut=rect_cut(c, o['t'], o['w'], 0.45), zb=o['zb'], zt=o['zt']))
    bands = []
    zs = sorted({ZG, ZG + DOOR_H, ZL, ZL + DOOR_H, Z_CORE, Z_LIFT})
    for k in range(len(zs) - 1):
        za, zb_ = zs[k], zs[k + 1]
        base = CORE_SHELL if zb_ <= Z_CORE + 1e-6 else LIFT_SHELL
        cc = [c['cut'] for c in cuts if c['zb'] <= za + 1e-6 and c['zt'] >= zb_ - 1e-6]
        bands.append((za, zb_, base.difference(unary_union(cc)) if cc else base))
    walls = G('Core walls RC 250 (stair to +10.900, lift overrun to +12.400)', None, 'TT Concrete', bsolid(bands))
    caps = [G('Stair shaft roof slab', None, 'TT Concrete', prism(core1_stair.buffer(0.25, join_style=2), Z_CORE - 0.3, Z_CORE)),
            G('Lift overrun roof slab', None, 'TT Concrete', prism(core1_lifts.buffer(0.25, join_style=2), Z_LIFT - 0.3, Z_LIFT))]
    dr = []
    for o in opens:
        dr.append(place_door(o, CORE_SHELL, None, o['zb']))
    return [walls] + caps, dr

H_R, G_T = 4.5 / 26, 0.28
def flight(origin, u, v, side_v0, side_v1, z0, n_r, direction, waist=0.18):
    """RC flight: n_r risers, (n_r-1) treads, rising from z0 starting at origin (u coordinate) going +u (direction=1) or -u."""
    th = math.atan(H_R / G_T); tv = waist / math.cos(th); slope = H_R / G_T
    prof = [(0, z0)]
    for i in range(n_r - 1):
        prof += [(i * G_T, z0 + (i + 1) * H_R), ((i + 1) * G_T, z0 + (i + 1) * H_R)]
    Lg = (n_r - 1) * G_T; ztop = z0 + n_r * H_R
    prof += [(Lg, ztop), (Lg, ztop - 0.2)]
    # soffit parallel to pitch line, from landing underside back down to z0
    u_hit = Lg - (ztop - 0.2 - z0) / slope
    if u_hit > 0.02: prof += [(u_hit, z0)]
    else: prof += [(0.0, ztop - 0.2 - Lg * slope)]
    pts = [[*(origin + u * direction * a + v * side_v0), z] for a, z in prof]
    return xprism(pts, [*(v * (side_v1 - side_v0)), 0])

def stairs_part():
    kids = []
    # ---- stair 1 (core): local u = PV_ (SSW -> NNE), v = QV (B side -> S side)
    u, v, C = PV_, QV, CS1
    ua = -3.0 + 1.34; ub = ua + 12 * G_T            # -1.66 .. 1.70
    zm = ZG + 13 * H_R
    fa = flight(C + u * ua, u, v, -1.5, -0.1, ZG, 13, +1)
    fb = flight(C + u * ub, u, v, 0.1, 1.5, zm, 13, -1)
    land_mid = Polygon([C + u * ub + v * -1.5, C + u * 3.0 + v * -1.5, C + u * 3.0 + v * 1.5, C + u * ub + v * 1.5])
    land_top = Polygon([C + u * -3.0 + v * -1.5, C + u * ua + v * -1.5, C + u * ua + v * 1.5, C + u * -3.0 + v * 1.5])
    s1 = [G('Flight 1 (13 risers 173 / going 280)', None, 'TT Concrete', fa), G('Flight 2 (13 risers 173 / going 280)', None, 'TT Concrete', fb),
          G('Mid landing', None, 'TT Concrete', prism(land_mid, zm - 0.2, zm)), G('L1 landing', None, 'TT Concrete', prism(land_top, ZL - 0.2, ZL))]
    rails = []
    for vv, z0_, d_ in [(-1.45, ZG, +1), (-0.15, ZG, +1), (1.45, zm, -1), (0.15, zm, -1)]:
        a0 = ua if d_ > 0 else ub; a1 = ub if d_ > 0 else ua
        p = C + u * a0 + v * vv; q = C + u * a1 + v * vv
        rails += beam([p[0], p[1], z0_ + H_R + 0.9], [q[0], q[1], z0_ + 13 * H_R + 0.9], 0.05, 0.05)
    s1.append(G('Handrails', None, 'TT Stainless', rails, soft=None))
    kids.append(G('STAIR 1 (core, GF to L1, 26 R x 173)', None, None, None, s1))
    # ---- stair 2 (module 10)
    u, v = ST2['u'], ST2['v']; C = B
    fa = flight(C + u * ST2['u0'], u, v, -1.3, -0.1, ZG, 13, +1)
    fb = flight(C + u * ST2['u1'], u, v, 0.1, 1.3, zm, 13, -1)
    lm = Polygon([st2_pt(ST2['u1'], -1.3), st2_pt(ST2['u2'], -1.3), st2_pt(ST2['u2'], 1.3), st2_pt(ST2['u1'], 1.3)])
    s2 = [G('Flight 1', None, 'TT Concrete', fa), G('Flight 2', None, 'TT Concrete', fb), G('Mid landing', None, 'TT Concrete', prism(lm, zm - 0.2, zm))]
    rails = []
    for vv, z0_, d_ in [(-1.25, ZG, +1), (-0.15, ZG, +1), (1.25, zm, -1), (0.15, zm, -1)]:
        a0 = ST2['u0'] if d_ > 0 else ST2['u1']; a1 = ST2['u1'] if d_ > 0 else ST2['u0']
        p = st2_pt(a0, vv); q = st2_pt(a1, vv)
        rails += beam([p[0], p[1], z0_ + H_R + 0.9], [q[0], q[1], z0_ + 13 * H_R + 0.9], 0.05, 0.05)
    # guard rail around the L1 slab opening (open sides)
    for a, b_ in [((ST2['u0'], -1.3), (ST2['u0'], 1.3))]:
        p = st2_pt(*a); q = st2_pt(*b_); rails += beam([p[0], p[1], ZL + 1.0], [q[0], q[1], ZL + 1.0], 0.05, 0.05)
    s2.append(G('Handrails', None, 'TT Stainless', rails, soft=None))
    kids.append(G('STAIR 2 (module 10, GF to L1)', None, None, None, s2))
    return G('STAIRS', T['stair'], None, None, kids)

def lifts_part():
    kids = []
    for s_ in (-1.05, 1.05):
        c = CL1 + PV_ * s_
        car = rect_at(c + QV * 0.05, 1.6, 1.5, QIBLA + 90)
        kids.append(G(f'Lift car {1 if s_ < 0 else 2} (13 persons, at GF)', None, 'TT Stainless', prism(car, ZG + 0.05, ZG + 2.5)))
    return G('LIFTS (2 nos)', T['lift'], None, None, kids)

# ================================================================== 4. terrace, roof, trusses, PV, tanks
def terrace_part():
    kids = []
    deck = ring(B, 11.3, 14.3).difference(L1_SECT).difference(CORE_FP.buffer(0.4))
    kids.append(G('Laluan Simpul timber deck walk', None, 'TT Timber deck', prism(deck, ZL, ZL + 0.05)))
    pl = ring(B, R_OUT, R_OVH).difference(L1_SECT).difference(CORE_FP.buffer(0.5))
    kids.append(G('Perimeter planter walls', None, 'TT Render white', prism(pl.difference(pl.buffer(-0.15, join_style=2)), ZL, ZL + 0.6)))
    kids.append(G('Perimeter planter (Taman Ulam edge)', None, 'TT Planting', prism(pl.buffer(-0.15, join_style=2), ZL, ZL + 0.55)))
    glass = ring(B, R_COURT - 0.006, R_COURT + 0.006, 360)
    kids.append(G('Glass balustrade to court (1100)', None, 'TT Glass', prism(glass, ZL, ZL + 1.05)))
    kids.append(G('Balustrade handrail', None, 'TT Stainless', prism(ring(B, R_COURT - 0.03, R_COURT + 0.03, 360), ZL + 1.05, ZL + 1.1)))
    # 11 herb planters (one per state)
    pdef = defn_box('Herb planter 2400x1200x600', 'Taman Ulam planter (one per state)',
                    [('TT Timber deck', box_faces(-1.2, -0.6, 0, 1.2, 0.6, 0.6).copy()), ('TT Planting', box_faces(-1.12, -0.52, 0.6, 1.12, 0.52, 0.62))])
    ins = []
    for k in range(11):
        b = 315 + 7.5 * k; p = P2(b, 15.1); ins.append(I(pdef, [p[0], p[1], ZL + 0.05 if 11.3 <= 15.1 <= 14.3 else ZL], [*tang(b), 0]))
    kids.append(G('Taman Ulam herb planters (11 states)', None, None, None, ins))
    return G('ROOF TERRACE – LALUAN SIMPUL', T['terr'], None, None, kids)

def east_roof_part():
    r0, r1 = 8.7, 22.1; b0, b1 = B1 - 1.2, B2 + 1.2
    n = int(math.ceil((b1 - b0) / 1.5)); bs = np.linspace(b0, b1, n + 1)
    def zt(r): return 11.2 + (r - R_COURT) * 1.7 / (R_L1 - R_COURT)
    th = 0.3; faces = []
    for i in range(n):
        a, c = bs[i], bs[i + 1]
        A0, A1, C0, C1 = P2(a, r0), P2(a, r1), P2(c, r0), P2(c, r1)
        top = [[*A0, zt(r0)], [*A1, zt(r1)], [*C1, zt(r1)], [*C0, zt(r0)]]
        bot = [[x, y, z - th] for x, y, z in top]
        ft = F(top); ft = ft if ft[2][2] > 0 else F(top[::-1]); faces.append(ft)
        fb = F(bot); fb = fb if fb[2][2] < 0 else F(bot[::-1]); faces.append(fb)
        faces.append(F([top[1], top[2], bot[2], bot[1]], [], [*d((a + c) / 2), 0]))          # outer fascia
        faces.append(F([top[0], bot[0], bot[3], top[3]], [], [*-d((a + c) / 2), 0]))         # inner fascia
    for bb, sg in ((b0, -1), (b1, 1)):
        A0, A1 = P2(bb, r0), P2(bb, r1)
        faces.append(F([[*A0, zt(r0)], [*A1, zt(r1)], [*A1, zt(r1) - th], [*A0, zt(r0) - th]], [], [*(tang(bb) * sg), 0]))
    roof = G('Ribbon roof over gallery + Dapur Rewang (+11.200 → +12.900)', None, 'TT Roof metal white', faces, soft=10)
    # trusses
    Ltr = R_L1 - R_COURT
    parts = []
    def chord(x0, z0, x1, z1, s): return beam([x0, 0, z0], [x1, 0, z1], s, s, up=(0, 1, 0))
    slope = 1.7 / Ltr
    top_c, bot_c = -0.075, -0.825
    parts += chord(0, top_c, Ltr, top_c + 1.7, 0.15) + chord(0, bot_c, Ltr, bot_c + 1.7, 0.15)
    npan = 10
    for k in range(npan + 1):
        x = Ltr * k / npan
        if k in (0, npan): parts += chord(x, bot_c + slope * x, x, top_c + slope * x, 0.1)
        if k < npan:
            x2 = Ltr * (k + 1) / npan
            if k % 2 == 0: parts += chord(x, bot_c + slope * x, x2, top_c + slope * x2, 0.08)
            else: parts += chord(x, top_c + slope * x, x2, bot_c + slope * x2, 0.08)
    tdef = defn_box('Steel ribbon truss 12.5 m (900 deep)', 'Warren truss spanning R9.0 → R21.5, sits under the roof deck', [('TT Steel dark', parts)])
    trusses = []
    for b in [49.3, 67.3, 76.3, 85.3, 103.3, 112.3, 121.3, 139.3]:
        b = b + (B1 - 40.3); p = P2(b, R_COURT)
        trusses.append(I(tdef, [p[0], p[1], zdeck(R_COURT)], [*d(b), 0]))
    # posts
    pin = defn_box(f'Post CHS 219 h{int((zdeck(R_COURT) - ZL) * 1000)}', 'balcony edge post R9.0', [('TT Steel dark', cyl_faces(0, 0, 0.11, 0, zdeck(R_COURT) - ZL, 16))])
    pout = defn_box(f'Post CHS 273 h{int((zdeck(R_L1) - ZL) * 1000)}', 'curtain wall post R21.5', [('TT Steel dark', cyl_faces(0, 0, 0.137, 0, zdeck(R_L1) - ZL, 16))])
    posts = []
    for k in range(13):
        b = B1 + 9 * k; p = P2(b, R_COURT); posts.append(I(pin, [p[0], p[1], ZL], [*tang(b), 0]))
    for b in [49.3, 67.3, 76.3, 85.3, 103.3, 112.3, 121.3, 139.3]:
        p = P2(b, R_L1 + 0.0); posts.append(I(pout, [p[0], p[1], ZL], [*tang(b), 0]))
    # PV on the ribbon roof
    pvdef = defn_box('PV module 1134x2279x35', 'solar PV module (x = width, y = length up-slope)', [('TT PV panel', box_faces(-0.567, -1.1395, 0, 0.567, 1.1395, 0.035))])
    al = math.atan(slope); pv = []
    for rc in [10.3, 12.7, 15.1, 17.5, 19.9]:
        step = 1.174 / rc; m_ = 0.6 / rc
        a0, a1 = math.radians(B1) + m_, math.radians(B2) - m_
        nn = int((a1 - a0) / step)
        off = ((a1 - a0) - nn * step) / 2
        for k in range(nn):
            b = math.degrees(a0 + off + step * (k + 0.5)); p = P2(b, rc)
            x = np.array([*tang(b), 0]); y = np.array([*(d(b) * math.cos(al)), math.sin(al)]); z = np.cross(x, y)
            if z[2] < 0: x = -x; z = np.cross(x, y)
            pv.append(I(pvdef, [p[0], p[1], zt(rc) + 0.1], x, y, z))
    return roof, trusses, posts, pv

def small_roof_items(roofp):
    kids = []
    tk = rect_at(S + d(QIBLA - 135) * 7.0, 4.0, 2.6, QIBLA - 45)
    u = d(QIBLA - 45); c0 = np.array(tk.centroid.coords[0])
    for k, nm in enumerate(['Cold water storage tank (GRP)', 'Fire water storage tank (GRP)']):
        cc = c0 + u * (-1.0 if k == 0 else 1.0)
        t = rect_at(cc, 1.9, 2.6, QIBLA - 45)
        kids.append(G(nm, None, 'TT Tank GRP', prism(t, ZSR_ROOF + 0.3, 12.0)))
    kids.append(G('Tank plinth beams', None, 'TT Concrete', prism(tk.buffer(0.15, join_style=2), ZSR_ROOF, ZSR_ROOF + 0.3)))
    tanks = G('ROOF WATER TANKS', T['tank'], None, None, kids)
    pvdef = 'PV module 1134x2279x35'
    keep = roofp.buffer(-0.45, join_style=2).difference(tk.buffer(1.0, join_style=2))
    crown_feet = [S + d(QIBLA + 180 + 40 * sg) * 8.0 for sg in (1, -1)]
    for f_ in crown_feet: keep = keep.difference(Point(f_).buffer(1.6))
    pv = []
    for rc in [4.1, 6.5, 8.9]:
        step = 1.174 / rc
        for k in range(int(2 * math.pi / step)):
            b = math.degrees(step * k)
            p = P2(b, rc, S); x = np.array([*tang(b), 0]); y = np.array([*d(b), 0])
            foot = Polygon([P2(b, rc, S) + tang(b) * sx * 0.57 + d(b) * sy * 1.14 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
            if keep.contains(foot): pv.append(I(pvdef, [p[0], p[1], ZSR_ROOF + 0.25], x, y))
    return tanks, pv

# ================================================================== 5. skin: lamellas, oculus canopy, ribbons, crown
def fin_def(h):
    name = f'Terracotta lamella 90x400 h{int(round(h * 1000))}'
    return defn_box(name, 'terracotta baguette fin on steel rails (x = along facade, y = depth)', [('TT Terracotta lamella', box_faces(-0.045, -0.2, 0, 0.045, 0.2, h))])

def fins_part():
    ins = []
    def door_angles(C, r_wall):
        out = []
        for lv in ('GF', 'L1'):
            for c, t, w, sw in DOORS[lv]:
                c = np.array(c)
                if abs(np.linalg.norm(c - C) - r_wall) < 0.1:
                    out.append((math.degrees(math.atan2(c[0] - C[0], c[1] - C[1])) % 360, w / 2 + 0.45))
        return out
    def ring_fins(C, r_wall, r_fin, b0, b1, step, z0, h, excl, label):
        dn = fin_def(h); doors = door_angles(C, r_wall)
        if b1 <= b0: b1 += 360
        n = int(math.radians(b1 - b0) * r_fin / step)
        for k in range(n + 1):
            b = (b0 + (b1 - b0) * k / max(n, 1)) % 360
            if in_arcs(b, excl): continue
            if any(abs(((b - bd) + 180) % 360 - 180) < math.degrees(hw / r_fin) for bd, hw in doors): continue
            p = P2(b, r_fin, C); ins.append(I(dn, [p[0], p[1], z0], [*tang(b), 0]))
    lobby_arc = (mod(20)[0], mod(2)[1])
    ring_fins(B, R_OUT, R_OUT + 0.55, 0, 360, 0.6, ZG, ZSOF - ZG, OPEN_ARCS + [lobby_arc], 'GF drum')
    # terrace band fins (slab edge), not over the L1 block, core or ribbon landings
    rib_ends = [np.array(pts[-1]) for _, pts, _ in SE.RIBBONS.values()]
    dn = fin_def(1.6); r_f = R_OVH + 0.2
    for k in range(int(2 * math.pi * r_f / 0.6)):
        b = 360 * k / int(2 * math.pi * r_f / 0.6)
        if in_arcs(b, [(B1 - 1, B2 + 1), (280, 305)]): continue
        p = P2(b, r_f)
        if min(np.linalg.norm(p - e) for e in rib_ends) < 2.8: continue
        ins.append(I(dn, [p[0], p[1], ZSOF], [*tang(b), 0]))
    ring_fins(B, R_L1, R_L1 + 0.35, B1, mod(11)[0], 0.75, ZSOF, zdeck(R_L1 + 0.35) - ZSOF, [], 'L1 block')
    ring_fins(B, R_L1, R_L1 + 0.35, mod(13)[0], B2, 0.75, ZSOF, zdeck(R_L1 + 0.35) - ZSOF, [], 'L1 block')
    ring_fins(S, RS_OUT, RS_OUT + 0.35, 0, 360, 0.6, ZG, ZSR_ROOF + 0.05 - ZG, [(76, 146)], 'small ring')
    return G('TERRACOTTA LAMELLAS', T['fin'], None, None, ins)

def oculus_part():
    kids = []
    zo, zi, ri, ro = 7.2, 7.7, 4.5, R_COURT
    n = 72; faces = []; th = 0.03
    for k in range(n):
        a, c = 360 * k / n, 360 * (k + 1) / n
        Ao, Co, Ai, Ci = P2(a, ro), P2(c, ro), P2(a, ri), P2(c, ri)
        top = [[*Ai, zi], [*Ao, zo], [*Co, zo], [*Ci, zi]]
        f = F(top); f = f if f[2][2] > 0 else F(top[::-1]); faces.append(f)
        bot = [[x, y, z - th] for x, y, z in top]; f = F(bot); f = f if f[2][2] < 0 else F(bot[::-1]); faces.append(f)
        faces.append(F([[*Ao, zo], [*Ao, zo - th], [*Co, zo - th], [*Co, zo]], [], [*d((a + c) / 2), 0]))
        faces.append(F([[*Ai, zi], [*Ci, zi], [*Ci, zi - th], [*Ai, zi - th]], [], [*-d((a + c) / 2), 0]))
    kids.append(G('PTFE membrane (oculus Ø9 m)', None, 'TT PTFE membrane', faces, soft=10))
    st = []
    for k in range(12):
        b = 15 + 30 * k; po, pi = P2(b, ro), P2(b, ri)
        st += beam([po[0], po[1], zo - th - 0.08], [pi[0], pi[1], zi - th - 0.08], 0.14, 0.16)
    kids.append(G('Radial steel arms (12)', None, 'TT Steel dark', st, soft=None))
    kids.append(G('Compression ring R4.5', None, 'TT Steel dark', prism(ring(B, ri - 0.12, ri + 0.12, 96), zi - th - 0.3, zi - th)))
    kids.append(G('Edge ring R9.0', None, 'TT Steel dark', prism(ring(B, ro - 0.1, ro + 0.05, 180), zo - th - 0.2, zo - th)))
    mdef = defn_box('Mast CHS 219 h1600', 'canopy mast on terrace edge', [('TT Steel dark', cyl_faces(0, 0, 0.11, 0, zo - 0.2 - ZL, 16))])
    for k in range(10):
        b = (M0 + 36 * k) % 360
        if in_arcs(b, [(B1 - 0.5, B2 + 0.5)]): continue
        p = P2(b, R_COURT); kids.append(I(mdef, [p[0], p[1], ZL], [*tang(b), 0]))
    return G('OCULUS CANOPY (PTFE, +7.200 → +7.700)', T['ocu'], None, None, kids)

def catmull(pts, N=80):
    P = [np.array(p, float) for p in pts]; l = len(P)
    def get(t):
        p = (l - 1) * t; ip = int(math.floor(p)); w = p - ip
        if w == 0 and ip == l - 1: ip = l - 2; w = 1
        p0 = P[ip - 1] if ip > 0 else 2 * P[0] - P[1]
        p1, p2 = P[ip], P[ip + 1]
        p3 = P[ip + 2] if ip + 2 < l else 2 * P[l - 1] - P[l - 2]
        dt0 = np.sum((p0 - p1) ** 2) ** 0.25; dt1 = np.sum((p1 - p2) ** 2) ** 0.25; dt2 = np.sum((p2 - p3) ** 2) ** 0.25
        if dt1 < 1e-4: dt1 = 1.0
        if dt0 < 1e-4: dt0 = dt1
        if dt2 < 1e-4: dt2 = dt1
        t1 = ((p1 - p0) / dt0 - (p2 - p0) / (dt0 + dt1) + (p2 - p1) / dt1) * dt1
        t2 = ((p2 - p1) / dt1 - (p3 - p1) / (dt1 + dt2) + (p3 - p2) / dt2) * dt1
        c0, c1, c2, c3 = p1, t1, -3 * p1 + 3 * p2 - 2 * t1 - t2, 2 * p1 - 2 * p2 + t1 + t2
        return c0 + c1 * w + c2 * w * w + c3 * w ** 3
    ts = np.linspace(0, 1, N + 1); pts_ = np.array([get(t) for t in ts])
    tg = np.gradient(pts_, axis=0); tg = tg / np.linalg.norm(tg, axis=1)[:, None]
    return ts, pts_, tg

def ribbon_faces(pts, w, zfn, twist, thick):
    ts, C, TG = catmull(pts)
    V = []
    for t, p, tg in zip(ts, C, TG):
        nx, ny = -tg[1], tg[0]; z = zfn(t); tw = math.sin(t * math.pi * 2) * math.radians(twist)
        for s in (-1, 1):
            for dz in (0, -thick):
                V.append([p[0] + nx * s * w / 2, p[1] + ny * s * w / 2, z + s * math.sin(tw) * w / 2 + dz])
    V = np.array(V); N = len(ts) - 1; faces = []
    def add(idx, ref):
        f = F([V[i] for i in idx])
        if f is None: return
        if np.dot(f[2], ref) < 0: f = F([V[i] for i in idx[::-1]])
        faces.append(f)
    for i in range(N):
        a, b = i * 4, (i + 1) * 4      # per section: 0 L-top, 1 L-bot, 2 R-top, 3 R-bot
        tg = TG[i]; left = np.array([-tg[1], tg[0], 0])
        add([a + 0, b + 0, b + 2], [0, 0, 1]); add([a + 0, b + 2, a + 2], [0, 0, 1])
        add([a + 1, b + 3, b + 1], [0, 0, -1]); add([a + 1, a + 3, b + 3], [0, 0, -1])
        add([a + 0, a + 1, b + 1, b + 0], -left); add([a + 2, b + 2, b + 3, a + 3], left)
    add([0, 2, 3, 1], [-TG[0][0], -TG[0][1], 0]); e = N * 4; add([e + 0, e + 1, e + 3, e + 2], [TG[-1][0], TG[-1][1], 0])
    return faces, ts, C

def ribbons_part():
    kids = []
    for k, (nm, pts, w) in SE.RIBBONS.items():
        zfn = lambda t: 3.6 + 1.5 * math.sin(math.pi * t * 0.9) + 1.3 * t
        faces, ts, C = ribbon_faces(pts, w, zfn, 12, 0.22)
        sub = [G(f'Ribbon {k.title()} (PTFE-clad steel, {w:.1f} m wide)', None, 'TT Ribbon white', faces, soft=30)]
        for tt in (0.12, 0.42, 0.72):
            i_ = int(round(tt * (len(ts) - 1))); p = C[i_]; z0 = ground_z(*p); z1 = zfn(ts[i_]) - 0.22
            sub.append(G('Column CHS 273', None, 'TT Steel dark', cyl_faces(p[0], p[1], 0.137, z0, z1, 16)))
        kids.append(G(f'RIBBON {k}', None, None, None, sub))
    return G('RIBBON CANOPIES (4 regions)', T['rib'], None, None, kids)

def crown_part():
    kids = []
    for sgn in (1, -1):
        P0_ = B + d(QIBLA + 38 * sgn) * 12.5; P2_ = S + d(QIBLA + 180 + 40 * sgn) * 8.0; P1_ = B + d(QIBLA) * 17.5 - perp * 9.0 * sgn
        z0, z1, z2 = 6.6, 13.5, 9.95
        zfn = lambda t: (z0 + (z1 - z0) * math.sin(math.pi * t)) if t < 0.5 else (z2 + (z1 - z2) * math.sin(math.pi * t))
        faces, ts, C = ribbon_faces([P0_, P1_, P2_], 1.0, zfn, 30, 0.25)
        kids.append(G(f'Crown ribbon {"A" if sgn > 0 else "B"} (terrace → small ring roof, top +13.500)', None, 'TT Crown terracotta', faces, soft=30))
        foot = rect_at(P0_, 1.2, 0.8, QIBLA + 38 * sgn)
        kids.append(G(f'Crown footing {"A" if sgn > 0 else "B"}', None, 'TT Crown terracotta', prism(foot, ZL, z0 - 0.25)))
    return G('SIMPUL CROWN', T['crown'], None, None, kids)

# ================================================================== 6. furniture, trees, bikes, labels, grids
def icosphere(r, sub=1):
    t = (1 + 5 ** 0.5) / 2
    V = [[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]]
    Fc = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
          [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]]
    V = [np.array(v, float) / np.linalg.norm(v) for v in V]
    for _ in range(sub):
        cache = {}; nf = []
        def midp(a, b):
            k = tuple(sorted((a, b)))
            if k not in cache:
                m = (V[a] + V[b]) / 2; V.append(m / np.linalg.norm(m)); cache[k] = len(V) - 1
            return cache[k]
        for a, b, c in Fc:
            ab, bc, ca = midp(a, b), midp(b, c), midp(c, a); nf += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        Fc = nf
    return [v * r for v in V], Fc

def tree_def(dd):
    name = f'Tree – canopy Ø{dd:g} m'
    if name in DEFS: return name
    V, Fc = icosphere(dd / 2, 1); V = [np.array([v[0], v[1], v[2] * 0.8 + 3.6 + dd / 2.6]) for v in V]
    can = mesh_faces(V, Fc)
    can = fix_outward(can, [0, 0, 3.6 + dd / 2.6])
    trunk = cyl_faces(0, 0, 0.18, 0, 3.6 + dd / 2.6, 8)
    return defn_box(name, 'low-poly tree (replace with your own 3D Warehouse tree if you like)', [('TT Tree trunk', trunk), ('TT Tree canopy', can)])

def furniture_part():
    kids = []
    ct = Point(B).buffer(R_COURT, 180).difference(Point(B).buffer(1.5, 48)).difference(sector(B, 3.3, 8.6, 22, 94)).difference(sector(B, R_COURT - 0.9, R_COURT - 0.3, 300, 318))
    kids.append(G('Court “Talam” paving', None, 'TT Court paving', prism(ct, ZG, ZG + 0.03)))
    kids.append(G('Play area (rubber, 30 m2)', None, 'TT Rubber play', prism(sector(B, 3.3, 8.6, 22, 94), ZG, ZG + 0.05)))
    kids.append(G('Tree planter bench ring', None, 'TT Timber deck', prism(ring(B, 1.0, 1.5, 48), ZG, ZG + 0.45)))
    kids.append(G('Tree pit soil', None, 'TT Planting', prism(Point(B).buffer(1.0, 24), ZG, ZG + 0.35)))
    kids.append(G('Hand-wash counter (B3)', None, 'TT Terrazzo', prism(sector(B, R_COURT - 0.9, R_COURT - 0.3, 300, 318, 12), ZG, ZG + 0.85)))
    # table sets
    parts_t = cyl_faces(0, 0, 0.55, 0.72, 0.76, 24) + cyl_faces(0, 0, 0.06, 0, 0.72, 8)
    parts_s = []
    for j in range(5):
        q = d(72 * j) * 0.95; parts_s += cyl_faces(q[0], q[1], 0.2, 0.42, 0.46, 12) + cyl_faces(q[0], q[1], 0.04, 0, 0.42, 6)
    tdef = defn_box('Table set Ø1100 + 5 stools', 'court dining set (100 seats in total)', [('TT Timber deck', parts_t), ('TT Steel dark', parts_s)])
    ins = []
    for rr, n, off in [(5.6, 9, 0), (7.6, 12, 15)]:
        for k in range(n):
            b = off + 360 / n * k
            if 20 < b < 95: continue
            p = P2(b, rr); ins.append(I(tdef, [p[0], p[1], ZG + 0.03], [*tang(b), 0], d(b).tolist() + [0]))
    kids.append(G('Dining sets', None, None, None, ins))
    furn = G('COURT FURNITURE', T['furn'], None, None, kids)
    # trees
    tr = []
    for x, y, dd in SE.TREES:
        tr.append(I(tree_def(dd), [x, y, ground_z(x, y)], [1, 0, 0]))
    tr.append(I(tree_def(6.0), [B[0], B[1], ZG + 0.35], [1, 0, 0], name='Court tree'))
    tr.append(I(tree_def(3.0), [S[0], S[1], ZG], [1, 0, 0], name='Light well tree'))
    trees = G('TREES', T['tree'], None, None, tr)
    # bikes
    bdef = defn_box('Bicycle stand (Sheffield)', 'stainless steel', [('TT Stainless', beam([-0.35, 0, 0], [-0.35, 0, 0.8], 0.05, 0.05) +
                                                                            beam([0.35, 0, 0], [0.35, 0, 0.8], 0.05, 0.05) + beam([-0.375, 0, 0.8], [0.375, 0, 0.8], 0.05, 0.05))])
    bk = []
    for k in range(5):
        x = 96.4 + 1.6 * k; bk.append(I(bdef, [x, 5.4, 0.05], [0, 1, 0]))
    bikes = G('BICYCLE STANDS (10 bikes)', T['bike'], None, None, bk)
    return [furn, trees, bikes]

def labels_part():
    out = []
    for level, key, z in (('GF', 'lab0', ZG + 0.1), ('L1', 'lab1', ZL + 0.1)):
        items = []
        for r in ROOMS:
            if r['level'] != level or r['code'] in ('OPEN',) or r['label'] in ('store', 'prep', ''): continue
            c = r['poly'].representative_point()
            a = r['poly'].area
            if r['code'] in ('A1', 'A2') and 'display' in r['name']:
                a = sum(x['poly'].area for x in ROOMS if x['name'].startswith(r['label']))
            items.append(dict(t='txt', p=[c.x, c.y, z], s=f"{r['label']}\n{a:.1f} m2"))
        out.append(G(f'ROOM LABELS {level}', T[key], None, None, items))
    return out

def grids_part():
    items = []
    zz = ZG + 0.01
    for r in (R_COURT, R_VER, R1_SHOP, R2_SHOP, R_OUT, R_OVH, R_L1):
        items.append(dict(t='e', pts=[[*P2(b, r), zz] for b in np.linspace(0, 360, 145)[:-1]], closed=True))
    for r in (RS_WELL, RS_COR, RS_OUT):
        items.append(dict(t='e', pts=[[*P2(b, r, S), zz] for b in np.linspace(0, 360, 97)[:-1]], closed=True))
    for k in range(10):
        b = (M0 + 36 * k) % 360
        items.append(dict(t='cl', a=[*P2(b, R_COURT - 1.5), zz], b=[*P2(b, R_L1 + 4), zz]))
        items.append(dict(t='txt', p=[*P2(b, R_L1 + 5.1), zz], s=str(k + 1)))
    for k in range(8):
        b = (QIBLA - 180 - 22.5 + 45 * k) % 360
        items.append(dict(t='cl', a=[*P2(b, 1.0, S), zz], b=[*P2(b, RS_OUT + 3, S), zz]))
        items.append(dict(t='txt', p=[*P2(b, RS_OUT + 4.1, S), zz], s='ABCDEFGH'[k]))
    items.append(dict(t='e', pts=[[*(B - d(QIBLA) * 40), zz], [*(B + d(QIBLA) * 60), zz]], closed=False))
    items.append(dict(t='txt', p=[*(B + d(QIBLA) * 55), zz], s='QIBLA AXIS 292.3°'))
    items.append(dict(t='txt', p=[B[0], B[1], zz], s='B (61.000, 22.000)'))
    items.append(dict(t='txt', p=[S[0], S[1], zz + 0.5], s=f'S ({S[0]:.3f}, {S[1]:.3f})'))
    return G('SET-OUT: rings, radial grids 1–10 / A–H, qibla axis', T['grid'], None, None, items, soft=None)

# ================================================================== assemble
def build():
    ROOT.clear(); DEFS.clear(); SCENES.clear()
    site_nodes = site_part()
    ROOT.append(G('SITE', None, None, None, site_nodes + landscape_part(), soft=None))
    ROOT.append(podium_part())
    gf_nodes, wf_gf = gf_part()
    l1w, l1g, l1d, l1m, l1c, wf_l1 = l1_part()
    ew, eg, ed, ece, e2d = east_part()
    l1slab, sroof, spar, roofp = slabs_part()
    core_w, core_d = core_part()
    ROOT.append(G('GROUND FLOOR (FFL +0.900)', None, None, None, gf_nodes + [G('CORE DOORS', T['gfd'], None, None, [x for x in core_d])]))
    ROOT.append(G('LEVEL 1 (FFL +5.400)', None, None, None, [
        l1slab,
        G('L1 WALLS (small ring + knot to +9.500, east block to roof)', T['l1w'], None, None, l1w + ew + l1m),
        G('L1 GLAZING & LOUVRES', T['l1g'], None, None, l1g + eg),
        G('L1 DOORS', T['l1d'], None, None, l1d + ed),
        G('L1 CEILINGS (service rooms, +9.900)', T['l1ce'], None, None, ece),
        G('L1 COLUMNS (small ring)', T['l1c'], None, None, l1c)]))
    ROOT.append(G('CORE (2 lifts + stair 1)', None, None, None, [G('CORE WALLS', T['core'], None, None, core_w), stairs_part(), lifts_part()]))
    ROOT.append(terrace_part())
    roof, trusses, posts, pv = east_roof_part()
    tanks, pv2 = small_roof_items(roofp)
    ROOT.append(G('ROOF', None, None, None, [G('ROOF SLABS', T['roof'], None, None, [roof, sroof, spar]),
                                              G('STEEL TRUSSES (8 x 12.5 m)', T['truss'], None, None, trusses),
                                              G('ROOF POSTS (east block)', T['l1c'], None, None, posts),
                                              G('PV PANELS', T['pv'], None, None, pv + pv2), tanks]))
    ROOT.append(G('SKIN & CANOPIES', None, None, None, [fins_part(), oculus_part(), ribbons_part(), crown_part()]))
    ROOT.append(G('LANDSCAPE & FURNITURE', None, None, None, furniture_part()))
    ROOT.append(G('DRAWING AIDS', None, None, None, labels_part() + [grids_part()]))
    # section planes
    ROOT.append(dict(t='sp', n='Section A-A (bearing 110°)', tag=T['sec'], p=[B[0], B[1], 3.0], v=[*d(20), 0]))
    ROOT.append(dict(t='sp', n='Section B-B (bearing 13.3°)', tag=T['sec'], p=[B[0], B[1], 3.0], v=[*d(283.3), 0]))
    # scenes
    allv = {t['n']: t['v'] for t in TAGS}
    def vis(hide=(), show=()):
        v = dict(allv)
        for k in hide: v[T[k]] = False
        for k in show: v[T[k]] = True
        return v
    cB = lambda b, r, z: [*P2(b, r), z]
    SCENES.extend([
        dict(n='01 Aerial from the south-east', eye=[B[0] + 62, B[1] - 78, 58], tgt=[B[0] - 4, B[1] + 4, 2], persp=True, fov=35, vis=vis()),
        dict(n='02 Arriving from Dataran Temu', eye=[99, 4, 1.65], tgt=[70, 18, 4.5], persp=True, fov=55, vis=vis()),
        dict(n='03 Court Talam (under the oculus)', eye=cB(215, 7.6, ZG + 1.6), tgt=cB(35, 9, 5.2), persp=True, fov=65, vis=vis()),
        dict(n='04 Dapur Rewang hall', eye=cB(128, 12.6, ZL + 1.6), tgt=cB(100, 21, ZL + 2.2), persp=True, fov=65, vis=vis()),
        dict(n='05 Roof terrace + Simpul crown', eye=cB(212, 15, ZL + 1.6), tgt=[*(B + d(QIBLA) * 17.5), 10.5], persp=True, fov=60, vis=vis()),
        dict(n='06 Aerial from the north-west', eye=[S[0] - 58, S[1] + 62, 52], tgt=[B[0] - 8, B[1] + 2, 2], persp=True, fov=35, vis=vis()),
        dict(n='07 GF plan (top view, roofs hidden)', eye=[52, 26, 300], tgt=[52, 26, 0], persp=False, h=95,
             vis=vis(hide=['l1s', 'l1w', 'l1g', 'l1d', 'l1c', 'l1ce', 'terr', 'roof', 'truss', 'pv', 'tank', 'ocu', 'rib', 'crown', 'tree', 'ctx'], show=['grid', 'lab0'])),
        dict(n='08 L1 plan (top view, roof hidden)', eye=[52, 26, 300], tgt=[52, 26, 0], persp=False, h=95,
             vis=vis(hide=['roof', 'truss', 'pv', 'tank', 'ocu', 'rib', 'crown', 'tree', 'ctx', 'l1ce'], show=['grid', 'lab1'])),
        dict(n='09 Site plan (top view)', eye=[56, 22, 400], tgt=[56, 22, 0], persp=False, h=180, vis=vis()),
    ])
    return dict(units='m', origin='SW site corner', materials=MATS, tags=TAGS, defs=DEFS, root=ROOT, scenes=SCENES,
                info=dict(project='Titik Temu – Esplanade Local Commercial Hub (Site C), Temerloh', B=list(map(float, B)), S=list(map(float, S)),
                          lat=3.4475, lon=102.4225))

if __name__ == '__main__':
    spec = build()
    def count(nodes):
        f = i = g = 0
        for n in nodes:
            if n['t'] == 'g':
                g += 1; f += len(n.get('f', [])); a, b_, c = count(n.get('c', [])); f += a; i += b_; g += c
            elif n['t'] == 'i': i += 1
        return f, i, g
    print('faces, instances, groups', count(ROOT), 'defs', len(DEFS))
    for r in RAMPS: print('ramp', r['name'], 'gradient 1:%.1f' % r['grad'], 'length %.1f' % (r['s_top'] - r['s0']))
    js = json.dumps(spec, separators=(',', ':'))
    open('/home/claude/crit1/out/titiktemu_model.json', 'w').write(js)
    print('json MB', round(len(js) / 1e6, 2))
