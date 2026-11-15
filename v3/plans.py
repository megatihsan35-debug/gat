"""Floor plans from plan3.py: walls (poche), glazing, doors with swings, stairs, lifts, sanitary fittings, furniture, grid,
dimensions, room tags. plan_drawing(fl, mode) -> cad.Drawing in site metres. mode 'arch' = architectural; 'base' = greyed
background for the services sheets (fire / plumbing / M&E draw on top of it)."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiLineString, box
from shapely.ops import unary_union, linemerge, polylabel, nearest_points
from cad import Drawing, INK
import plan3 as M
from plan3 import C, P, d, tdir, frame, ROOMS, CORES, S4, FFL, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, R_OCULUS, QIBLA, SC

GREY = '#9AA3AD'; LGREY = '#C9CED4'; PALE = '#E9ECEF'
WALL_T = dict(ext=0.20, int=0.125, wet=0.15, fire=0.20)

def rooms(fl, kinds=('room', 'wet', 'shop')): return [r for r in ROOMS if r['fl'] == fl and r['kind'] in kinds]
def core_list(fl): return [c for c in CORES.values() if fl != 'L2' or c['to_l2']]
def brg(p): v = np.array(p) - C; return math.degrees(math.atan2(v[0], v[1])) % 360
def rad(p): return float(np.hypot(*(np.array(p) - C)))

# ------------------------------------------------------------------------------------------------ walls
def core_walls(fl):
    out = []
    for c in core_list(fl):
        if c['key'] == 'S3': continue
        out.append(c['stair_wall'].difference(c['stair']))
        if c['lift']: out.append(c['shaft_wall'].difference(c['shaft']))
    return unary_union(out)
def core_solid(fl):
    out = []
    for c in core_list(fl):
        if c['key'] == 'S3': continue
        out.append(c['stair_wall'])
        if c['lift']: out.append(c['shaft_wall'])
    return unary_union(out)

def walls(fl):
    """returns dict(solid=polygon, glaz=[LineString], rated=polygon, segments=list)"""
    rs = rooms(fl); cs = core_solid(fl)
    others = lambda r: unary_union([q['poly'] for q in rs if q is not r])
    solid, glaz, rated = [], [], []
    for r in rs:
        g = r['poly']; oth = others(r)
        pts = list(g.exterior.coords)
        for a, b in zip(pts[:-1], pts[1:]):
            a, b = np.array(a), np.array(b); L = np.linalg.norm(b - a)
            if L < 1e-4: continue
            t = (b - a) / L; n = np.array([-t[1], t[0]]); m = (a + b) / 2
            p1, p2 = Point(m + n * 0.12), Point(m - n * 0.12)
            out = p2 if g.contains(p1) else p1
            if cs.buffer(0.02).contains(out): continue               # core walls are drawn by the core
            seg = LineString([a, b])
            if oth.buffer(0.01).contains(out):
                th = WALL_T['wet'] if r['kind'] == 'wet' else WALL_T['int']
                if r['occ'] == 'plant': th = WALL_T['fire']; rated.append(seg.buffer(th / 2, cap_style=3))
                solid.append(seg.buffer(th / 2, cap_style=3))
            else:
                inner = abs(rad(m) - R_BR1) < 0.08
                style = r['inner'] if inner else r['facade']
                if style == 'glass': glaz.append(seg)
                else: solid.append(seg.buffer(WALL_T['ext'] / 2, cap_style=3))
    rated += [core_walls(fl)]
    return dict(solid=unary_union(solid + [core_walls(fl)]), glaz=linemerge(unary_union(glaz)) if glaz else MultiLineString(), rated=unary_union(rated))

# ------------------------------------------------------------------------------------------------ doors
def door_list(fl):
    out = []
    for dd in M.DOORS:
        r = [q for q in ROOMS if q['key'] == dd['key']][0]
        if r['fl'] != fl: continue
        g = r['poly']; p = Point(dd['p'])
        ext = g.exterior; s = ext.project(p); q = np.array(ext.interpolate(s).coords[0])
        q2 = np.array(ext.interpolate(min(ext.length, s + 0.05)).coords[0]); q1 = np.array(ext.interpolate(max(0, s - 0.05)).coords[0])
        t = (q2 - q1); t = t / (np.linalg.norm(t) + 1e-9); n = np.array([-t[1], t[0]])
        if not g.contains(Point(q + n * 0.3)): n = -n                        # n points into the room
        sw = n if dd['swing'] == 'in' else -n
        out.append(dict(p=q, t=t, sw=sw, w=dd['w'], kind=dd['kind'], tag=dd['tag'], fire=dd['fire'], key=dd['key']))
    for dd in M.CORE_DOORS:
        if dd['fl'] != fl: continue
        c = CORES[dd['key'].split('-')[0]]
        if dd['axis'] == 'v': t = tdir(c['bc']); n = d(c['bc'])            # wall runs across the radial axis
        else: t = d(c['bc']); n = tdir(c['bc']) * c['side']
        sw = n if dd['swing'] in ('out', 'lift') else -n
        if dd['axis'] == 'v' and dd['swing'] == 'lift': sw = -d(c['bc'])
        out.append(dict(p=np.array(dd['p']), t=t, sw=sw, w=dd['w'], kind=dd['kind'], tag=dd['tag'], fire=dd['fire'], key=dd['key']))
    return out

def draw_door(D, dd, color=INK, lw=0.13, tags=True):
    p, t, sw, w = dd['p'], dd['t'], dd['sw'], dd['w']
    a, b = p - t * w / 2, p + t * w / 2
    if dd['kind'] in ('single', 'double'):
        leaves = [(a, t, w)] if dd['kind'] == 'single' else [(a, t, w / 2), (b, -t, w / 2)]
        for h, dirn, lw_ in leaves:
            tip = h + sw * lw_
            D.line([h, tip], 'A-DOOR', lw=0.18, color=color)
            a0 = math.degrees(math.atan2(*(sw[::-1]))); a1 = math.degrees(math.atan2(*(dirn[::-1])))
            lo, hi = sorted([a0, a1])
            if hi - lo > 180: lo, hi = hi, lo + 360
            D.arc(h, lw_, lo, hi, 'A-DOOR', lw=0.09, color=color)
    elif dd['kind'] == 'slide':
        D.line([a + sw * 0.05, p + t * 0.1 + sw * 0.05], 'A-DOOR', lw=0.18, color=color)
        D.line([p - t * 0.1 + sw * 0.12, b + sw * 0.12], 'A-DOOR', lw=0.18, color=color)
    elif dd['kind'] == 'shutter':
        D.line([a, b], 'A-DOOR', lw=0.18, color=color, ls='--')
    elif dd['kind'] == 'lift':
        D.line([a + sw * 0.05, p + sw * 0.05], 'A-DOOR', lw=0.18, color=color); D.line([p + sw * 0.12, b + sw * 0.12], 'A-DOOR', lw=0.18, color=color)
    if tags and dd['tag'] and dd['kind'] != 'lift':
        q = p - sw * 0.55
        D.text(q, dd['tag'] + ('\n' + dd['fire'] if dd['fire'] else ''), 'A-ANNO', size=1.5, color=color if color != INK else '#444', font='DejaVu Sans Mono')

# ------------------------------------------------------------------------------------------------ fixtures (local wall frame)
class Wall:
    """a straight wall face of a wedge room; s runs along the wall (outwards), q runs into the room"""
    def __init__(self, room, edge, rho0=None):
        bm, b0, b1 = M.mid(room['key']); self.room = room
        self.b = b0 if edge == 'acw' else b1
        self.es = d(self.b); self.eq = tdir(self.b) * (1 if edge == 'acw' else -1)
        self.half = WALL_T['wet'] / 2
    def W(self, s, q): return C + self.es * s + self.eq * (q + self.half)
    def rect(self, s0, s1, q0, q1): return Polygon([self.W(s0, q0), self.W(s1, q0), self.W(s1, q1), self.W(s0, q1)])
class Arc:
    """an arc wall face at radius r of a room (outer or inner); s = bearing offset in metres along the arc, q into the room"""
    def __init__(self, room, which):
        bm, b0, b1 = M.mid(room['key']); self.bm = bm
        g = room['poly']; rs = [rad(c) for c in g.exterior.coords]
        self.r = max(rs) if which == 'out' else min(rs); self.sg = -1 if which == 'out' else 1
    def W(self, s, q):
        r = self.r + self.sg * (q + WALL_T['ext'] / 2); b = self.bm + math.degrees(s / self.r)
        return P(r, b)
    def rect(self, s0, s1, q0, q1): return Polygon([self.W(s0, q0), self.W(s1, q0), self.W(s1, q1), self.W(s0, q1)])

def wc(D, F, s, q0=0.0, color=INK, lw=0.1):
    """WC pan: cistern on the wall + bowl"""
    D.poly(F.rect(s - 0.22, s + 0.22, q0, q0 + 0.18), 'A-FIXT', fill='white', edge=color, lw=lw, z=5)
    c = F.W(s, q0 + 0.45); D.circle(c, 0.2, 'A-FIXT', fill='white', edge=color, lw=lw, z=5)
def basin(D, F, s, q0=0.0, w=0.5, color=INK, lw=0.1):
    D.poly(F.rect(s - w / 2, s + w / 2, q0, q0 + 0.42), 'A-FIXT', fill='white', edge=color, lw=lw, z=5)
    D.circle(F.W(s, q0 + 0.22), 0.14, 'A-FIXT', edge=color, lw=lw, z=6)
def urinal(D, F, s, q0=0.0, color=INK, lw=0.1):
    D.poly(F.rect(s - 0.2, s + 0.2, q0, q0 + 0.32), 'A-FIXT', fill='white', edge=color, lw=lw, z=5)
def shower(D, F, s0, s1, q0, q1, color=INK, lw=0.1):
    D.poly(F.rect(s0, s1, q0, q1), 'A-FIXT', fill='white', edge=color, lw=lw, z=5)
    D.line([F.W(s0, q0), F.W(s1, q1)], 'A-FIXT', lw=0.07, color=color); D.line([F.W(s1, q0), F.W(s0, q1)], 'A-FIXT', lw=0.07, color=color)
def counter(D, F, s0, s1, q0, q1, color=INK, lw=0.1, fill='white', layer='A-FIXT'):
    D.poly(F.rect(s0, s1, q0, q1), layer, fill=fill, edge=color, lw=lw, z=5)
def sink(D, F, s, q0=0.0, color=INK, lw=0.1):
    D.poly(F.rect(s - 0.3, s + 0.3, q0 + 0.06, q0 + 0.5), 'A-FIXT', edge=color, lw=lw, z=6)
def partition(D, F, s, q1, color=INK, lw=0.13):
    D.line([F.W(s, 0), F.W(s, q1)], 'A-FIXT', lw=lw, color=color)

def _rr(r):
    rs = [rad(c) for c in r['poly'].exterior.coords]; return min(rs), max(rs)
def _w(r, rr):
    """clear width of a wedge room at radius rr"""
    bm, b0, b1 = M.mid(r['key']); return math.radians(b1 - b0) * rr - WALL_T['wet']
def booth(D, F, s0, s1, q0, q1, color, door_face=None, dw=0.8, sw_into='out'):
    """cubicle outline in a Wall frame with an opening on one face ('s0','s1','q1') and a door leaf"""
    D.poly(F.rect(s0, s1, q0, q1), 'A-FIXT', edge=color, lw=0.13, z=5)
    if door_face == 's0':
        a, b = F.W(s0, (q0 + q1) / 2 - dw / 2), F.W(s0, (q0 + q1) / 2 + dw / 2)
        D.line([a, b], 'A-FIXT', lw=0.5, color='white', z=5.5)
        tip = F.W(s0 - dw, (q0 + q1) / 2 - dw / 2) if sw_into == 'out' else F.W(s0 + dw, (q0 + q1) / 2 - dw / 2)
        D.line([a, tip], 'A-DOOR', lw=0.13, color=color, z=6)
    if door_face == 'q1':
        a, b = F.W((s0 + s1) / 2 - dw / 2, q1), F.W((s0 + s1) / 2 + dw / 2, q1)
        D.line([a, b], 'A-FIXT', lw=0.5, color='white', z=5.5)
        D.line([a, F.W((s0 + s1) / 2 - dw / 2, q1 - dw)], 'A-DOOR', lw=0.13, color=color, z=6)

def toilet_bank(D, r, male, color):
    """brief D3: 3 cubicles (PwD, parent + child, general), basins 2 adult + 1 child; male + 2 urinals.
    inner band wedge R12.5-18.5, door from the arcade / ring bridge at the inner end."""
    F = Wall(r, 'cw'); G = Wall(r, 'acw'); r0, r1 = _rr(r); e = r1 - 0.075
    # PwD cubicle (MS 1184: 2200 x 1700 min) in the outer corner on the cw wall, door 900 on its inner face opening out
    pw = 1.85
    booth(D, F, e - 2.25, e, 0, pw, color, 's0', 0.9)
    wc(D, F, e - 0.5, 0.0, color)
    D.poly(F.rect(e - 2.1, e - 1.6, 0, 0.42), 'A-FIXT', fill='white', edge=color, lw=0.1, z=5)       # basin inside
    D.circle(F.W(e - 1.85, 0.21), 0.12, 'A-FIXT', edge=color, lw=0.08, z=6)
    D.text(F.W(e - 1.2, pw / 2 + 0.25), 'PwD', 'A-FIXT', size=1.5, color=color, weight='bold')
    D.circle(F.W(e - 3.05, 0.95), 0.75, 'A-FIXT', edge=color, lw=0.07, ls=':')                       # 1500 turning circle
    # parent + child cubicle in the outer corner on the acw wall (fills to the PwD partition), door on its inner face
    wo = _w(r, e - 1.6)
    booth(D, G, e - 1.6, e, 0, wo - pw, color, 's0', 0.8)
    wc(D, G, e - 0.5, 0.0, color)
    D.circle(G.W(e - 0.5, 1.15), 0.14, 'A-FIXT', edge=color, lw=0.08)
    D.text(G.W(e - 0.8, 1.55), 'PARENT\n+ CHILD', 'A-FIXT', size=1.2, color=color)
    # general cubicle on the acw wall, door on its face to the room
    booth(D, G, e - 2.75, e - 1.75, 0, 1.55, color, 'q1', 0.7)
    wc(D, G, e - 2.25, 0.0, color)
    # basins on the cw wall near the door: 2 adult + 1 child (lower)
    for i, (w, lab) in enumerate(((0.5, ''), (0.5, ''), (0.45, 'CHILD'))):
        s = r0 + 0.65 + i * 0.6
        basin(D, F, s, 0.0, w, color)
    D.text(F.W(r0 + 1.85, 0.75), 'CHILD', 'A-FIXT', size=1.0, color=color)
    if male:
        for i in range(2): urinal(D, G, r0 + 0.75 + i * 0.7, 0.0, color)

def staff_restroom(D, r, color):
    """brief D3 staff restroom 28: PwD WC, WC, 2 shower / bath cubicles, 2 basins, lockers. Door from the outer colonnade."""
    F = Wall(r, 'cw'); G = Wall(r, 'acw'); A = Arc(r, 'in'); r0, r1 = _rr(r); s0 = r0 + 0.075
    booth(D, F, s0, s0 + 2.25, 0, 1.85, color, None)
    D.line([F.W(s0 + 2.25, 0.45), F.W(s0 + 2.25 + 0.9, 0.45)], 'A-DOOR', lw=0.13, color=color)
    D.line([F.W(s0 + 2.25, 0.45), F.W(s0 + 2.25, 1.35)], 'A-FIXT', lw=0.5, color='white', z=5.5)
    wc(D, Arc(r, 'in'), 0, 0, color) if False else wc(D, F, s0 + 0.5, 0.0, color)
    D.text(F.W(s0 + 1.35, 1.1), 'PwD', 'A-FIXT', size=1.4, color=color, weight='bold')
    booth(D, F, s0 + 2.35, s0 + 3.35, 0, 1.6, color, 'q1', 0.7); wc(D, F, s0 + 2.85, 0.0, color)
    for i in range(2):
        shower(D, G, s0 + i * 1.05, s0 + 1.0 + i * 1.05, 0, 1.0, color)
    D.text(G.W(s0 + 1.05, 1.3), 'SHOWER / BATH', 'A-FIXT', size=1.1, color=color)
    for i in range(2): basin(D, G, s0 + 2.75 + i * 0.7, 0.0, 0.5, color)
    hw = _w(r, r0) / 2
    counter(D, A, -hw + 1.15, hw - 2.0, 0, 0.5, color); D.text(A.W((-hw + 1.15 + hw - 2.0) / 2, 0.25), 'LOCKERS', 'A-FIXT', size=1.1, color=color)

def parents_room(D, r, color):
    if r['key'] == 'G04':
        F = Wall(r, 'cw'); r0, r1 = _rr(r)
        counter(D, F, r0 + 0.5, r0 + 1.9, 0, 0.65, color); sink(D, F, r0 + 0.85, 0, color)
        D.text(F.W(r0 + 1.45, 0.33), 'CHANGING', 'A-FIXT', size=1.0, color=color)
    else:
        A = Arc(r, 'out')
        D.poly(Point(A.W(0, 0.55)).buffer(0.38), 'A-FURN', fill='white', edge=color, lw=0.08)
        G = Wall(r, 'acw'); r0, r1 = _rr(r); basin(D, G, r0 + 0.7, 0, 0.45, color)

def shop_fit(D, r, color):
    """brief A1/A2: display 15, staff area 10 (cashier, prep, basin, seat), store 7 (freezer, shelves)"""
    g = r['poly']; rs = [rad(c) for c in g.exterior.coords]; r0, r1 = min(rs), max(rs)
    bm, b0, b1 = M.mid(r['key'])
    # store at the outer end: find radius with 7 m2 beyond
    rr = r1
    while g.intersection(SC.disc(r1 + 1).difference(SC.disc(rr))).area < 7.2 and rr > r0: rr -= 0.05
    seg = LineString([P(rr, b0 - 1), P(rr, b1 + 1)]).intersection(g.buffer(-0.06))
    if not seg.is_empty:
        cs = list(seg.coords) if seg.geom_type == 'LineString' else list(max(seg.geoms, key=lambda q: q.length).coords)
        a, b = np.array(cs[0]), np.array(cs[-1]); L = np.linalg.norm(b - a); t = (b - a) / L
        D.line([a, a + t * (L / 2 - 0.45)], 'A-WALL', lw=0.35, color=color); D.line([b, b - t * (L / 2 - 0.45)], 'A-WALL', lw=0.35, color=color)
        h = a + t * (L / 2 - 0.45); n = -d(bm)
        D.line([h, h + n * 0.9], 'A-DOOR', lw=0.13, color=color)
        a0 = math.degrees(math.atan2(n[1], n[0])); a1 = math.degrees(math.atan2(t[1], t[0])); lo, hi = sorted([a0, a1])
        if hi - lo > 180: lo, hi = hi, lo + 360
        D.arc(h, 0.9, lo, hi, 'A-DOOR', lw=0.08, color=color)
        D.text(P((rr + r1) / 2, bm), 'STORE', 'A-FIXT', size=1.3, color=color)
    F = Wall(r, 'cw'); G = Wall(r, 'acw')
    counter(D, G, r0 + 0.9, r0 + 3.6, 0.0, 0.55, color); D.text(G.W(r0 + 2.25, 0.9), 'DISPLAY', 'A-FIXT', size=1.2, color=color)
    counter(D, F, rr - 2.6, rr - 0.25, 0.0, 0.6, color); sink(D, F, rr - 0.7, 0.0, color)
    D.text(F.W(rr - 1.5, 0.95), 'PREP + CASHIER', 'A-FIXT', size=1.2, color=color)
    counter(D, F, r0 + 0.9, r0 + 3.0, 0.0, 0.45, color)

def fit(D, fl, color=INK):
    for r in rooms(fl):
        k, nm = r['key'], r['name']
        if k in ('G01', 'L04'): toilet_bank(D, r, True, color)
        elif k in ('G02', 'L05'): toilet_bank(D, r, False, color)
        elif k in ('G06', 'G07'): staff_restroom(D, r, color)
        elif r['kind'] == 'shop': shop_fit(D, r, color)
        elif k in ('L23',):
            F = Arc(r, 'out'); wc(D, F, -0.6, 0.0, color); basin(D, F, 0.6, 0.0, 0.5, color); D.text(r['poly'].centroid.coords[0], '', 'A-FIXT')
        elif k in ('G03', 'G04'): parents_room(D, r, color)
        elif k == 'L02':
            A = Arc(r, 'out'); D.poly(LineString([A.W(-0.9, 0.5), A.W(0.9, 0.5)]).buffer(0.3, cap_style=2), 'A-FURN', fill='white', edge=color, lw=0.08)
            D.text(A.W(0, 1.25), 'REST BENCH', 'A-FURN', size=1.0, color=color)
        elif k == 'L01':
            F = Wall(r, 'acw'); r0, r1 = _rr(r); counter(D, F, r0 + 0.3, r1 - 0.3, 0, 0.5, color); D.text(F.W((r0 + r1) / 2, 0.25), 'SHELVES', 'A-FIXT', size=1.0, color=color)
        elif 'JANITOR' in nm:
            F = Wall(r, 'cw'); rs = [rad(c) for c in r['poly'].exterior.coords]
            D.poly(F.rect(max(rs) - 0.9, max(rs) - 0.25, 0, 0.6), 'A-FIXT', fill='white', edge=color, lw=0.1); D.circle(F.W(max(rs) - 0.57, 0.3), 0.12, 'A-FIXT', edge=color, lw=0.08)
        elif k in ('L22',):
            F = Arc(r, 'in'); counter(D, F, -1.2, 1.2, 0.0, 0.6, color); sink(D, F, 0.5, 0.0, color)
        elif k == 'G30':
            F = Wall(r, 'cw'); G = Wall(r, 'acw'); rs = [rad(c) for c in r['poly'].exterior.coords]; r0, r1 = min(rs), max(rs)
            counter(D, F, r0 + 0.2, r1 - 0.2, 0, 0.65, color); sink(D, F, r0 + 1.3, 0, color)
            counter(D, G, r0 + 0.2, r1 - 1.3, 0, 0.65, color)
            for i in range(2): D.circle(G.W(r0 + 1.6 + i * 0.6, 0.33), 0.17, 'A-FIXT', edge=color, lw=0.08)
            D.text(G.W(r0 + 1.9, 1.0), 'HOB + HOOD', 'A-FIXT', size=1.2, color=color); D.text(F.W(r0 + 3.4, 1.0), 'PREP + WASH', 'A-FIXT', size=1.2, color=color)
        elif k == 'G31':
            F = Wall(r, 'acw'); rs = [rad(c) for c in r['poly'].exterior.coords]; r0, r1 = min(rs), max(rs)
            counter(D, F, r0 + 2.0, r0 + 5.5, 0, 0.7, color); D.text(F.W(r0 + 3.7, 1.1), 'SERVING COUNTER', 'A-FIXT', size=1.2, color=color)
            bm, b0, b1 = M.mid(k)
            for rr, bb in ((19.0, bm - 1.5), (19.0, bm + 3.5), (21.2, bm - 1.0), (21.2, bm + 3.0), (16.6, bm + 2.5)):
                D.circle(P(rr, bb), 0.38, 'A-FURN', fill='white', edge=color, lw=0.08)
                for j in range(4): D.circle(P(rr, bb) + np.array([math.cos(j * math.pi / 2), math.sin(j * math.pi / 2)]) * 0.62, 0.17, 'A-FURN', edge=color, lw=0.07)
        elif k == 'G21':
            F = Arc(r, 'out'); counter(D, F, -1.0, 0.95, 0.1, 0.8, color); D.text(F.W(0, 1.2), 'COUCH', 'A-FIXT', size=1.2, color=color)
            G = Wall(r, 'cw'); rs = [rad(c) for c in r['poly'].exterior.coords]; basin(D, G, min(rs) + 1.8, 0, 0.5, color)
        elif k == 'G20':
            F = Arc(r, 'in'); counter(D, F, -1.0, 1.0, 0.0, 0.6, color); D.text(F.W(0, 1.0), 'COUNTER + FIRE PANEL', 'A-FIXT', size=1.2, color=color)
        elif k == 'G08':
            F = Wall(r, 'cw'); rs = [rad(c) for c in r['poly'].exterior.coords]
            counter(D, F, min(rs) + 0.8, max(rs) - 0.8, 0, 0.6, color, fill=PALE); D.text(F.W((min(rs) + max(rs)) / 2, 0.3), 'MSB / MDB PANELS', 'A-FIXT', size=1.2, color=color)
        elif k in ('G09', 'L07', 'M16'):
            F = Wall(r, 'acw'); rs = [rad(c) for c in r['poly'].exterior.coords]
            counter(D, F, min(rs) + 0.4, min(rs) + 1.0, 0, 0.6, color, fill=PALE); D.text(F.W(min(rs) + 0.7, 0.3), 'RACK', 'A-FIXT', size=1.0, color=color)
        elif k == 'G11':
            F = Wall(r, 'cw'); rs = [rad(c) for c in r['poly'].exterior.coords]; r0, r1 = min(rs), max(rs)
            for i in range(3): counter(D, F, r1 - 0.4 - (i + 1) * 1.3, r1 - 0.4 - i * 1.3 - 0.1, 0, 0.75, color); D.text(F.W(r1 - 0.4 - i * 1.3 - 0.65, 0.38), 'FZ', 'A-FIXT', size=1.0, color=color)
            G = Wall(r, 'acw'); D.poly(G.rect(r0 + 0.5, r0 + 1.3, 0, 0.8), 'A-FIXT', edge=color, lw=0.13); D.line([G.W(r0 + 0.5, 0), G.W(r0 + 1.3, 0.8)], 'A-FIXT', lw=0.07, color=color)
            D.text(G.W(r0 + 0.9, 1.15), 'DUMBWAITER', 'A-FIXT', size=1.1, color=color)
        elif k == 'L13':                           # same shaft position as in G11 below (stacked dumbwaiter)
            G = Wall([q for q in ROOMS if q['key'] == 'G11'][0], 'acw'); r0 = R_BR1
            D.poly(G.rect(r0 + 0.5, r0 + 1.3, 0, 0.8), 'A-FIXT', edge=color, lw=0.13); D.line([G.W(r0 + 0.5, 0), G.W(r0 + 1.3, 0.8)], 'A-FIXT', lw=0.07, color=color)
            D.text(G.W(r0 + 0.9, 1.15), 'DUMBWAITER', 'A-FIXT', size=1.1, color=color)
        elif k == 'L12':
            bm, b0, b1 = M.mid(k)
            for rr in (21.0, 23.4):
                for bb in (bm - 4.5, bm + 1.0, bm + 6.5):
                    D.poly(LineString([P(rr, bb - 1.6), P(rr, bb + 1.6)]).buffer(0.38, cap_style=2), 'A-FURN', fill='white', edge=color, lw=0.08)
            D.poly(LineString([P(25.3, bm - 2.0), P(25.3, bm + 2.0)]).buffer(0.45, cap_style=2), 'A-FURN', fill=PALE, edge=color, lw=0.1)
            D.text(P(25.3, bm), 'DEMO KITCHEN ISLAND', 'A-FURN', size=1.1, color=color)
        elif k == 'L24':
            bm, b0, b1 = M.mid(k)
            for i, bb in enumerate(np.linspace(b0 + 2.4, b1 - 2.4, 3)):
                for rr in (21.6, 24.2):
                    D.poly(Point(P(rr, bb)).buffer(0.0).buffer(0.01) if False else LineString([P(rr, bb - 0.8), P(rr, bb + 0.8)]).buffer(0.35, cap_style=2), 'A-FURN', fill='white', edge=color, lw=0.08)
        elif k == 'L25':
            bm, b0, b1 = M.mid(k); D.poly(LineString([P(23.6, bm - 1.2), P(23.6, bm + 1.2)]).buffer(0.4, cap_style=2), 'A-FURN', fill='white', edge=color, lw=0.08)
        elif k == 'L26':
            bm, b0, b1 = M.mid(k); D.poly(LineString([P(21.6, bm), P(24.8, bm)]).buffer(0.55, cap_style=1), 'A-FURN', fill='white', edge=color, lw=0.08)
            for j in range(4):
                for sgn in (-1, 1): D.circle(P(21.9 + j * 0.85, bm) + tdir(bm) * sgn * 0.85, 0.2, 'A-FURN', edge=color, lw=0.07)
        elif k == 'L21':
            F = Arc(r, 'in'); counter(D, F, -0.9, 0.9, 0.6, 1.15, color); D.text(F.W(0, 1.55), 'COUNTER', 'A-FIXT', size=1.1, color=color)
        elif k == 'M01':
            bm, b0, b1 = M.mid(k)
            for rr, bb in ((20.0, bm - 2), (20.0, bm + 2.5), (23.3, bm)):
                D.poly(Point(P(rr, bb)).buffer(0.55, 4), 'A-FURN', fill=PALE, edge=color, lw=0.08)
            D.text(P(21.6, bm + 0.2), 'DISPLAY PLINTHS', 'A-FURN', size=1.1, color=color)
        elif k in ('M10', 'M12'):
            # saf lines perpendicular to the qibla direction; qibla arrow
            g = r['poly']; qd = d(QIBLA); pq = np.array([-qd[1], qd[0]])
            cx = np.array(g.centroid.coords[0])
            for j in range(-3, 5):
                c0 = cx + qd * (j * 1.1 - 0.4)
                ln = LineString([c0 - pq * 8, c0 + pq * 8]).intersection(g.buffer(-0.4))
                if not ln.is_empty and ln.geom_type == 'LineString': D.line(list(ln.coords), 'A-FURN', lw=0.07, color=color, ls='--')
            D.line([cx - qd * 1.0, cx + qd * 1.6], 'A-ANNO', lw=0.18, color='#C9690A')
            D.text(cx + qd * 2.0, f'QIBLA {QIBLA}°', 'A-ANNO', size=1.4, color='#C9690A')
        elif k in ('M11', 'M13'):
            F = Wall(r, 'cw'); rs = [rad(c) for c in r['poly'].exterior.coords]; r0, r1 = min(rs), max(rs)
            counter(D, F, r0 + 0.4, r1 - 0.3, 0, 0.35, color)
            for j in range(int((r1 - r0 - 0.8) / 0.75)): D.circle(F.W(r0 + 0.8 + j * 0.75, 0.75), 0.15, 'A-FIXT', edge=color, lw=0.07)
            D.text(F.W((r0 + r1) / 2, 1.25), 'WUDHU TAPS', 'A-FIXT', size=1.1, color=color)
        elif k == 'M14':
            bm, b0, b1 = M.mid(k)
            for bb in (bm - 3, bm + 3): D.poly(LineString([P(19.0, bb), P(24.5, bb)]).buffer(0.25, cap_style=2), 'A-FURN', fill='white', edge=color, lw=0.08)
        elif k == 'G10':
            bm, b0, b1 = M.mid(k); D.poly(LineString([P(19.6, bm), P(22.3, bm)]).buffer(1.1, cap_style=2), 'A-FIXT', edge=color, lw=0.08, ls='--')

import landscape as LS
PLAY = LS.PLAY
def court_fit(D, color):
    """brief B3: open seating for 100 (curved communal 'talam' tables + benches in the planter fronts), children's play 30 m2,
    hand wash 15 (G33). Inner ring of pocket gardens (Taman Teduh) on the court rim."""
    play = LS.play_poly()
    D.poly(play, 'A-FURN', fill='#EAF3E1', edge=color, lw=0.1, ls='--', z=2)
    p = P(5.6, sum(PLAY) / 2); D.text(p, f"CHILDREN'S PLAY\nSOFT RUBBER\n{play.area:.0f} m²", 'A-AREA', size=1.6, color=color, halo=True, z=9)
    for a, b in LS.TABLES:
        D.poly(LS.ann_sec(*LS.TABLE_R, a, b), 'A-FURN', fill='white', edge=color, lw=0.1, z=3)
        for rr in (LS.BENCH_T_IN, LS.BENCH_T_OUT): D.poly(LS.ann_sec(*rr, a, b), 'A-FURN', fill='#F4F1EA', edge=color, lw=0.08, z=3)
    for a, b in LS.INNER:
        D.poly(LS.ann_sec(*LS.POCKET_IN_R, a, b), 'L-PLNT', fill='#DDE8D3', edge='#3E7D3A' if color == INK else color, lw=0.13, z=3.4)
        D.poly(LS.ann_sec(*LS.BENCH_IN_R, a, b), 'A-FURN', fill='#F4F1EA', edge=color, lw=0.08, z=3.4)
    st = LS.seats()
    D.text(P(6.2, 212), f"TALAM COURT · OPEN SEATING {st['total']}\n{st['table_inner'] + st['table_outer']} AT TALAM TABLES + {st['pocket_benches']} ON GARDEN BENCHES", 'A-AREA', size=1.6, color=color, halo=True, z=9)
    a, b = LS.INNER[-1]; D.text(P(9.9, (a + b) / 2), 'TAMAN TEDUH\n(INNER RING)', 'L-PLNT', size=1.3, color='#3E7D3A' if color == INK else color, halo=True, z=9)
    D.text(P(1.9, 300), 'TITIK POOL\nWATER +0.720', 'A-AREA', size=1.4, color=color, halo=True, z=9)

def landscape_overlay(D, fl, color=None):
    """canopies, gate + outer pockets (GF), sky pockets (L1). On GF the canopy is overhead (dashed) and only its columns land."""
    import siteplan as ST
    leaf = '#3E7D3A' if not color else color
    if fl == 'GF':
        for c in LS.CANOPIES: ST.canopy_plan(D, c, solid=False, color=color)
        ST.pockets_plan(D, inner=False, gate=True, outer=True, color=color)
        for g in ST.GATE[:1]:
            p = polylabel(g['poly'], 0.1); D.text((p.x, p.y), 'TAMAN\nGERBANG', 'L-PLNT', size=1.2, color=leaf, halo=True, z=9)
        c = [k for k in LS.CANOPIES if k['main']][0]
        D.text(LS.xy(c, 20.0, 0.0), 'ANYAMAN CANOPY OVER\n(HANGS FROM L1, U/S +3.55 TO +3.75)', 'L-CANP', size=1.4, color=color or '#7A6A4A', halo=True, z=9, rot=0)
    elif fl == 'L1':
        for q in LS.SKY: D.poly(q, 'L-PLNT', fill='#DDE8D3', edge=leaf, lw=0.13, z=3.4)
        if LS.SKY:
            q = max(LS.SKY, key=lambda g: g.area); p = polylabel(q, 0.05)
            D.text((p.x, p.y), 'SKY POCKET', 'L-PLNT', size=1.2, color=leaf, halo=True, z=9)
        for c in LS.CANOPIES: ST.canopy_plan(D, c, solid=True, color=color, region=SC.disc(M.R_L1).symmetric_difference(SC.disc(80)))

# ------------------------------------------------------------------------------------------------ stairs + lifts
def draw_core(D, c, fl, color=INK, show_text=True):
    bc, sw, W = c['bc'], c['sw'], c['W']
    f = lambda u, v: frame(bc, u, v)
    v0, v1 = c['v_s0'], c['v_s1']; ta, tb = v0 + sw, v1 - sw
    top = (fl == 'L1' and not c['to_l2']) or fl == 'L2'
    bottom = fl == 'GF'
    for side, sgn in (('A', -1), ('B', 1)):
        u_in, u_out = sgn * 0.1, sgn * (W / 2)
        solid = (side == 'A' and not top) or (side == 'B' and not bottom)
        for i in range(13):
            v = ta + i * M.GO
            D.line([f(u_in, v), f(u_out, v)], 'A-STRS', lw=0.09, color=color, ls='-' if solid else '--')
        D.line([f(u_in, ta), f(u_in, tb)], 'A-STRS', lw=0.13, color=color)
    D.line([f(-0.1, v0 + 0.05), f(-0.1, tb)], 'A-STRS', lw=0.13, color=color); D.line([f(0.1, v0 + 0.05), f(0.1, tb)], 'A-STRS', lw=0.13, color=color)
    # arrows
    def arrow(u, va, vb, lab):
        D.line([f(u, va), f(u, vb)], 'A-STRS', lw=0.13, color=color)
        tip = f(u, vb); bk = f(u, vb + (0.35 if vb < va else -0.35))
        sd = tdir(bc) * 0.15
        D.line([bk + sd, tip, bk - sd], 'A-STRS', lw=0.13, color=color)
        if show_text: D.text(f(u, va + (0.45 if va < vb else -0.45)), lab, 'A-STRS', size=1.4, color=color, weight='bold')
    if not top: arrow(-W / 4 - 0.05, tb + 0.3, ta + 0.2, 'UP')
    if not bottom: arrow(W / 4 + 0.05, tb + 0.3, ta + 0.2, 'DN')
    if c['key'] == 'S3':                                  # open stair: balustrades instead of walls
        for u in (-W / 2, W / 2): D.line([f(u, v0), f(u, v1)], 'A-STRS', lw=0.25, color=color)
        D.line([f(-W / 2, v0), f(W / 2, v0)], 'A-STRS', lw=0.25, color=color)
    if c['lift']:
        a = [f(-0.8, c['v_l0'] + 0.35), f(0.8, c['v_l0'] + 0.35), f(0.8, c['v_l0'] + 1.75), f(-0.8, c['v_l0'] + 1.75)]
        D.poly(Polygon(a), 'A-FIXT', edge=color, lw=0.13); D.line([a[0], a[2]], 'A-FIXT', lw=0.08, color=color); D.line([a[1], a[3]], 'A-FIXT', lw=0.08, color=color)
    if show_text:
        D.text(f(0, (v0 + v1) / 2 + 0.2), c['name'], 'A-ANNO', size=1.8, weight='bold', color=color, rot=0, halo=True)
        D.text(f(0, (v0 + v1) / 2 - 0.45), f"{int(round(sw * 1000))} CLEAR · {int(round(sw * 1000)) // 550} UNITS", 'A-ANNO', size=1.3, color=color, halo=True)
        if c['lift']: D.text(f(0, c['v_l0'] - 0.75), 'LIFT 13P', 'A-ANNO', size=1.3, color=color, halo=True)

def draw_s4(D, fl, color=INK):
    f = lambda u, v: frame(S4['bc'], u, v); w = S4['w']; v0 = S4['v0']
    runs = [(v0, v0 + S4['run']), (v0 + S4['run'] + S4['land'], S4['v1'])]
    show = runs[:1] if fl == 'L1' else runs
    for a, b in show:
        for i in range(13): D.line([f(-w / 2, a + i * M.GO), f(w / 2, a + i * M.GO)], 'A-STRS', lw=0.09, color=color)
    for u in (-w / 2, w / 2): D.line([f(u, v0), f(u, S4['v1'] if fl == 'GF' else v0 + S4['run'])], 'A-STRS', lw=0.25, color=color)
    D.text(f(0, v0 + S4['run'] / 2), 'STAIR 4\n(EXTERNAL)\n2200 · 4 UNITS', 'A-ANNO', size=1.4, color=color, halo=True, rot=0)
    lab = 'DN' if fl == 'L1' else 'UP'
    D.text(f(0, v0 + 0.5 if fl == 'L1' else S4['v1'] - 0.5), lab, 'A-STRS', size=1.4, weight='bold', color=color)

# ------------------------------------------------------------------------------------------------ grid + dims
def grid(D, fl, color='#7A8590'):
    for lab, b, p in M.GRID:
        D.line([P(7.5, b), P(29.6, b)], 'A-GRID', lw=0.07, color=color, ls='-.')
        c = P(30.6, b); D.circle(c, 0.42, 'A-GRID', fill='white', edge=color, lw=0.13, z=7); D.text(c, lab, 'A-GRID', size=1.6, color=color, z=8)
    for lab, r in (('A', R_BR0), ('B', R_BR1), ('C', R_GF), ('D', R_L1)):
        D.arc(C, r, 0, 360, 'A-GRID', lw=0.07, color=color, ls='-.')
        c = P(r, 254.0) if False else P(r, 248.5)
        D.circle(c, 0.42, 'A-GRID', fill='white', edge=color, lw=0.13, z=7); D.text(c, lab, 'A-GRID', size=1.6, color=color, z=8)

def radial_dims(D, b=242.8, color='#2C6E7A'):
    stops = [0, R_POOL, R_COURT, R_BR0, R_BR1, R_GF, R_L1, M.R_ROOF]
    off = tdir(b) * 1.6
    for r in stops: D.line([P(r, b) + off * 0.6, P(r, b) + off * 1.4], 'A-DIMS', lw=0.09, color=color)
    D.line([P(0, b) + off, P(stops[-1], b) + off], 'A-DIMS', lw=0.09, color=color)
    for a, c in zip(stops[:-1], stops[1:]):
        D.text(P((a + c) / 2, b) + off * 1.45, f'{int(round((c - a) * 1000))}', 'A-DIMS', size=1.4, color=color, rot=(90 - b) % 180 - 0, halo=True)
    D.text(P(stops[-1] + 2.2, b) + off, 'RADII FROM\nTHE CENTRE', 'A-DIMS', size=1.3, color=color)

# ------------------------------------------------------------------------------------------------ tags
TAG_AT = dict(G01=14.3, G02=14.3, L04=14.3, L05=14.3, G06=21.4, G07=21.4, G10=16.0, G11=17.2, G08=19.6)
def room_tags(D, fl, color=INK, area=True, scale=1.0):
    for r in rooms(fl) + [r for r in ROOMS if r['fl'] == fl and r['kind'] == 'open']:
        g = r['poly']; a = g.buffer(-0.075, join_style=2).area
        p = polylabel(g, 0.05); p = (p.x, p.y)
        if r['key'] in ('L24', 'L25', 'L26', 'L27', 'L23'): p = tuple(P(24.6 if r['key'] != 'L25' else 24.8, M.mid(r['key'])[0]))
        if r['key'] in TAG_AT: p = tuple(P(TAG_AT[r['key']], M.mid(r['key'])[0]))
        nm = r['name']; small = a < 14
        words = nm.replace(' · ', '\n').split('\n')
        out = []
        for w in words:
            if len(w) > 13 and ' ' in w:
                parts = w.split(' '); line = ''
                for q in parts:
                    if len(line) + len(q) > 12 and line: out.append(line); line = q
                    else: line = (line + ' ' + q).strip()
                out.append(line)
            else: out.append(w)
        txt = '\n'.join(out) + (f'\n{a:.0f} m²' if area else '')
        D.text(p, txt, 'A-AREA', size=(1.45 if small else 1.85) * scale, color=color, weight='normal', halo=True, z=9)

def level_tag(D, p, txt, color=INK):
    D.poly(Polygon([p + np.array([-0.3, 0]), p + np.array([0.3, 0]), p + np.array([0, -0.45])]), 'A-ANNO', fill=color, edge=None, z=8)
    D.text(p + np.array([0.5, -0.2]), txt, 'A-ANNO', size=1.6, ha='left', color=color, weight='bold', halo=True)

def sec_lines():
    """section cut lines (start, end) in site metres. A: 3 m west of the Selatan axis, south -> north.
    B: through the axis of stair 4 (279°) to the east stores at 103°, west -> east (not through C, so it misses the radial walls)"""
    ax_ = d(182.7); wst = np.array([ax_[1], -ax_[0]])
    A = (C + ax_ * 37 + wst * 3, C - ax_ * 34 + wst * 3)
    p0, p1 = P(30.0, 279.0), P(30.0, 103.0); t = (p1 - p0) / np.linalg.norm(p1 - p0)
    B = (p0 - t * 8.5, p1 + t * 6.0)
    return dict(A=A, B=B)
SEC_LOOK = dict(A=1, B=1)
def section_marks(D, color=INK):
    for lab, (a0, a1) in sec_lines().items():
        a0, a1 = np.array(a0), np.array(a1)
        D.line([a0, a1], 'A-ANNO', lw=0.13, color=color, ls='-.')
        dirn = (a1 - a0) / np.linalg.norm(a1 - a0); nrm = np.array([-dirn[1], dirn[0]]) * SEC_LOOK[lab]
        for q, sg in ((a0, 1), (a1, -1)):
            D.circle(q, 0.7, 'A-ANNO', fill='white', edge=color, lw=0.18, z=8); D.text(q, lab, 'A-ANNO', size=2.2, weight='bold', color=color, z=9)
            D.poly(Polygon([q + nrm * 0.7, q + nrm * 1.8, q + nrm * 0.7 + dirn * 0.6 * sg]), 'A-ANNO', fill=color, edge=None, z=8)

# ------------------------------------------------------------------------------------------------ the plan
def plan_drawing(fl, mode='arch'):
    D = Drawing(f'PLAN {fl} {mode}')
    base = mode != 'arch'
    ink = GREY if base else INK; wfill = LGREY if base else INK
    # context: spines, court, pool, plate outline below / above
    for s in SC.SPINES:
        e = np.array(SC.spine_end(s['b']).coords[0])
        if fl == 'GF': D.poly(LineString([P(R_COURT, s['b']), e]).buffer(s['w'] / 2, cap_style=2).intersection(SC.SITE), 'A-SITE', fill='#F2F4F5', edge=LGREY, lw=0.09, z=0)
    if fl == 'GF':
        D.circle(C, R_COURT, 'A-SITE', fill='#FBF6E9' if not base else '#FAFAFA', edge=ink, lw=0.13, z=1)
        D.circle(C, R_POOL, 'A-SITE', fill='#D8ECF7', edge=ink, lw=0.13, z=2)
        D.circle(C, 0.42, 'A-COLS', fill=ink, edge=None, z=4); D.text(C + np.array([0, -1.0]), 'MAST Ø840\nAT BASE', 'A-ANNO', size=1.3, color=ink, halo=True)
        D.arc(C, R_BR0, 0, 360, 'A-SLAB', lw=0.13, color=ink, ls='--')
        D.arc(C, R_L1, 0, 360, 'A-SLAB', lw=0.13, color=ink, ls='--')
        D.text(P(R_L1 + 0.35, 75), 'LINE OF FLOOR ABOVE', 'A-ANNO', size=1.2, color=ink, rot=-75 + 90 - 90, ha='left')
    else:
        g = M.PLATE[fl]
        D.poly(g, 'A-SLAB', fill=None, edge=ink, lw=0.25, z=1)
        D.poly(SC.ann(R_BR0, R_BR1), 'A-SLAB', fill='#F6F7F8' if not base else None, edge=ink, lw=0.25, z=1)
        D.circle(C, R_BR0 - 0.1, 'A-SLAB', edge=ink, lw=0.13, z=1)          # balustrade
        D.text(P(11.0, 168), 'RING BRIDGE  3000', 'A-ANNO', size=1.4, color=ink, rot=-(168 - 90), halo=True)
        D.circle(C, R_COURT, 'A-SITE', edge=LGREY, lw=0.09, ls='--', z=1); D.text(C, 'OPEN TO\nTALAM COURT\nBELOW', 'A-ANNO', size=1.6, color=ink)
        D.circle(C, 0.3, 'A-COLS', fill=ink, edge=None, z=4)
        for o in M.OPEN:
            if o['fl'] == fl and o['poly'].area > 20:
                p = polylabel(o['poly'], 0.1)
                D.text((p.x, p.y), 'OPEN DECK\n(ROOFED)', 'A-AREA', size=1.6, color='#5B7F4E' if not base else ink, halo=True)
        D.poly(M.PLATE[fl].difference(SC.disc(R_L1 - 0.4)), 'A-SLAB', edge=None, fill=None)
    grid(D, fl, color='#B9C0C7' if base else '#7A8590')
    # columns
    for c in M.COLS:
        if fl != 'GF' and c['ring'] == 'C' and False: continue
        D.circle(c['p'], 0.175 if c['ring'] != 'A' else 0.2, 'A-COLS', fill=wfill, edge=None, z=6)
    # walls + glazing + doors
    W = walls(fl); dl = door_list(fl)
    cut = unary_union([LineString([q['p'] - q['t'] * q['w'] / 2, q['p'] + q['t'] * q['w'] / 2]).buffer(0.32, cap_style=2) for q in dl]) if dl else Polygon()
    D.poly(W['solid'].difference(cut), 'A-WALL', fill=wfill, edge=None, z=5)
    if not W['glaz'].is_empty:
        gl = W['glaz'].difference(cut)
        for ln in getattr(gl, 'geoms', [gl]):
            if ln.is_empty or ln.length < 0.05: continue
            D.poly(ln.buffer(0.06, cap_style=2), 'A-GLAZ', fill='white', edge=ink, lw=0.09, z=5)
            D.line(list(ln.coords), 'A-GLAZ', lw=0.07, color=ink, z=6)
    for q in dl: draw_door(D, q, color=ink, tags=not base)
    # stairs, lifts, external stair
    for c in core_list(fl): draw_core(D, c, fl, color=ink, show_text=True)
    if fl in ('GF', 'L1'): draw_s4(D, fl, color=ink)
    fit(D, fl, color=ink if not base else '#B5BCC4')
    if fl == 'GF': court_fit(D, ink if not base else '#B5BCC4')
    if fl in ('GF', 'L1'): landscape_overlay(D, fl, None if not base else '#B5BCC4')
    room_tags(D, fl, color=ink)
    level_tag(D, P(R_COURT - 1.5, 160) if fl == 'GF' else P(R_BR1 + 1.4, 300 if fl != 'L2' else 122), f'FFL +{FFL[fl]:.3f}', color=ink)
    if not base:
        radial_dims(D)
        section_marks(D)
    return D

if __name__ == '__main__':
    for fl in ('GF', 'L1', 'L2'):
        D = plan_drawing(fl); print(fl, len(D.items))
