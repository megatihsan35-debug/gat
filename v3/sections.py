"""Sections and elevations from the same model (plan3 + scheme). Drawing coordinates: x = u (metres along the cut / across
the elevation), y = z (metres above site datum ±0.000). Placed on the sheet at 1:100 like the plans."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiLineString, box
from shapely.ops import unary_union
from cad import Drawing, INK
import plan3 as M
from plan3 import C, P, d, tdir, SC, FFL, CORES, S4, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, R_OCULUS
import plans
import landscape as LS

R_ROOF, R_DISC, ROOF_T = SC.R_ROOF, SC.R_DISC, SC.ROOF_T
R_RIN = M.R_ROOF_IN
CUT = INK; BEY = '#8A939C'; EARTH = '#D9D2C3'; GLASS = '#BFD9E6'; GREYF = '#E6E8EB'
CEIL = {'GF': 3.3, 'L1': 3.0, 'L2': 3.0}            # ceiling height above FFL in enclosed rooms
SLAB_Z = {'L1': (4.8, 5.4), 'L2': (9.0, 9.6)}
def brg(p): v = np.array(p) - C; return math.degrees(math.atan2(v[0], v[1])) % 360
def rad(p): return float(np.hypot(*(np.array(p) - C)))
def in_spine(p, extra=0.0):
    return any(SC.strip(s['b'], s['w'] + extra).contains(Point(p)) for s in SC.SPINES)
def ground_z(p):
    r = rad(p)
    import siteplan
    if siteplan.TERRACE.contains(Point(p)): return 0.9
    for s in SC.SPINES:
        if SC.strip(s['b'], s['w'] + 2.0, 0, 95).contains(Point(p)) and r > R_BR0:
            Rend = SC.spine_end(s['b']).distance(Point(C)) - 6.0
            return 0.9 * min(1.0, max(0.0, (Rend - r) / (Rend - R_BR0)))
    return 0.9 if r <= R_GF + 1.5 else 0.0
def roof_top(p): return SC.roof_h(brg(p))
def roof_under(p):
    r = rad(p); t = roof_top(p)
    return t - ROOF_T if r <= R_L1 else t - ROOF_T + (ROOF_T - 0.12) * (r - R_L1) / (R_ROOF - R_L1)
def funnel_top(r): return 11.4 + (13.5 - 11.4) * (r - R_OCULUS) / (R_DISC - R_OCULUS)
ROOF_FP = SC.ann(R_RIN, R_ROOF).difference(SC.RF_VOID)
FUNNEL_FP = SC.ann(R_OCULUS, R_DISC)
L1_FP = unary_union([M.PLATE['L1'], SC.ann(R_BR0, R_BR1)])
L2_FP = unary_union([M.PLATE['L2'], SC.ann(R_BR0, R_BR1)])

class Cut:
    def __init__(self, a, b):
        self.a, self.b = np.array(a, float), np.array(b, float)
        self.L = float(np.linalg.norm(self.b - self.a)); self.t = (self.b - self.a) / self.L
        self.line = LineString([self.a, self.b])
    def u(self, p): return float(np.dot(np.array(p) - self.a, self.t))
    def pt(self, u): return self.a + self.t * u
    def spans(self, geom):
        g = self.line.intersection(geom)
        out = []
        for q in getattr(g, 'geoms', [g]):
            if q.is_empty: continue
            if q.geom_type == 'LineString':
                c = list(q.coords); u0, u1 = sorted((self.u(c[0]), self.u(c[-1])))
                if u1 - u0 > 1e-3: out.append((u0, u1))
        return sorted(out)

def band(D, u0, u1, f0, f1, layer, fill=CUT, edge=None, n=None, lw=0.0, z=4):
    """polygon between z = f0(u) and f1(u) over [u0, u1]"""
    n = n or max(2, int((u1 - u0) / 0.25) + 2)
    us = np.linspace(u0, u1, n)
    pts = [(u, f1(u)) for u in us] + [(u, f0(u)) for u in us[::-1]]
    D.poly(Polygon(pts).buffer(0), layer, fill=fill, edge=edge, lw=lw, z=z)

def man(D, u, z, color=BEY):
    D.circle((u, z + 1.58), 0.12, 'A-ANNO', fill=None, edge=color, lw=0.1)
    D.poly(Polygon([(u - 0.17, z), (u + 0.17, z), (u + 0.17, z + 1.42), (u - 0.17, z + 1.42)]).buffer(0.08).buffer(-0.08), 'A-ANNO', fill=None, edge=color, lw=0.1)

def level_marks(D, x, items, color=INK):
    for z, t in items:
        D.line([(x - 0.8, z), (x + 0.8, z)], 'A-DIMS', lw=0.13, color=color)
        D.poly(Polygon([(x - 0.3, z + 0.45), (x + 0.3, z + 0.45), (x, z)]), 'A-DIMS', fill=color, edge=None)
        D.text((x + 1.1, z + 0.05), t, 'A-DIMS', size=1.8, ha='left', va='bottom', color=color, weight='bold')

def section(a, b, look_side=1, label='A'):
    """cut along a->b; look_side +1 = we look to the left of a->b (that half is drawn as 'beyond')"""
    X = Cut(a, b); D = Drawing(f'SECTION {label}')
    nrm = np.array([-X.t[1], X.t[0]]) * look_side            # direction we look towards
    U0, U1 = 0.0, X.L
    # ---- ground + plinth (cut), earth below
    us = np.linspace(U0, U1, int(X.L / 0.2))
    gz = [ground_z(X.pt(u)) for u in us]
    D.poly(Polygon([(U0, -1.6)] + list(zip(us, gz)) + [(U1, -1.6)]), 'A-SITE', fill=EARTH, edge=None, z=1, hatch=None)
    D.line(list(zip(us, gz)), 'A-SITE', lw=0.5, color=CUT, z=6)
    for u0, u1 in X.spans(SC.disc(R_GF + 1.5).difference(SC.disc(R_POOL))):
        band(D, u0, u1, lambda u: ground_z(X.pt(u)) - 0.15, lambda u: ground_z(X.pt(u)), 'A-SLAB', z=5)
    for u0, u1 in X.spans(SC.disc(R_POOL)):
        D.poly(box(u0, 0.3, u1, 0.72), 'A-SITE', fill='#D8ECF7', edge=CUT, lw=0.13, z=3)
        D.poly(box(u0 - 0.2, 0.1, u1 + 0.2, 0.3), 'A-SLAB', fill=CUT, edge=None, z=5)
    # ---- slabs
    for fl, fp in (('L1', L1_FP), ('L2', L2_FP)):
        z0, z1 = SLAB_Z[fl]
        for u0, u1 in X.spans(fp):
            rmid = rad(X.pt((u0 + u1) / 2))
            zb = z1 - 0.35 if rmid < R_BR1 + 0.05 else z0
            D.poly(box(u0, zb, u1, z1), 'A-SLAB', fill=CUT, edge=None, z=5)
    # ---- roof petals + funnel (cut)
    for u0, u1 in X.spans(ROOF_FP):
        band(D, u0, u1, lambda u: roof_under(X.pt(u)), lambda u: roof_top(X.pt(u)), 'A-ROOF', z=5)
    for u0, u1 in X.spans(FUNNEL_FP):
        band(D, u0, u1, lambda u: funnel_top(rad(X.pt(u))) - 0.28, lambda u: funnel_top(rad(X.pt(u))), 'A-ROOF', z=5)
    # ---- walls (cut) per floor, glazing
    tops = {'GF': lambda p: 4.8, 'L1': lambda p: 9.0 if M.PLATE['L2'].buffer(0.3).contains(Point(p)) else roof_under(p), 'L2': lambda p: roof_under(p) - 0.0}
    labels = []
    for fl in ('GF', 'L1', 'L2'):
        W = plans.walls(fl); dl = plans.door_list(fl)
        cutd = unary_union([LineString([q['p'] - q['t'] * q['w'] / 2, q['p'] + q['t'] * q['w'] / 2]).buffer(0.32, cap_style=2) for q in dl]) if dl else Polygon()
        for u0, u1 in X.spans(W['solid'].difference(cutd)):
            p = X.pt((u0 + u1) / 2); top = tops[fl](p); rr = rad(p)
            facade = min(abs(rr - R_GF), abs(rr - R_L1), abs(rr - R_BR1)) < 0.35 or any(c for c in CORES.values() if c['stair_wall'].buffer(0.05).contains(Point(p)))
            if not facade: top = min(top, FFL[fl] + CEIL[fl] + 0.3)
            D.poly(box(u0, FFL[fl], u1, top), 'A-WALL', fill=CUT, edge=None, z=5)
        for u0, u1 in X.spans(cutd.intersection(W['solid'].buffer(0.05))):
            p = X.pt((u0 + u1) / 2); top = tops[fl](p)
            D.poly(box(u0, FFL[fl] + 2.4, u1, top), 'A-WALL', fill=CUT, edge=None, z=5)          # head over the door
        g = X.line.intersection(W['glaz'].buffer(0.06)) if not W['glaz'].is_empty else None
        if g is not None and not g.is_empty:
            for q in getattr(g, 'geoms', [g]):
                cs = list(q.coords); u = X.u(cs[0]); p = X.pt(u); top = tops[fl](p)
                D.poly(box(u - 0.06, FFL[fl], u + 0.06, top), 'A-GLAZ', fill=GLASS, edge=CUT, lw=0.13, z=5)
        for r in plans.rooms(fl):
            for u0, u1 in X.spans(r['poly']):
                if u1 - u0 > 2.2: labels.append(((u0 + u1) / 2, FFL[fl] + 1.6, r['name'].split(' · ')[0]))
                zc = min(FFL[fl] + CEIL[fl], tops[fl](X.pt((u0 + u1) / 2)) - 0.05)
                if u1 - u0 > 0.5: D.line([(u0 + 0.1, zc), (u1 - 0.1, zc)], 'A-HIDN', lw=0.13, color=INK, ls='--', z=4)
    # ---- columns: cut ones solid, the next ring beyond in grey
    for c in M.COLS:
        p = np.array(c['p']); off = float(np.dot(p - X.a, nrm)); u = X.u(p)
        if not (U0 < u < U1): continue
        z0 = ground_z(p) if c['ring'] != 'A' else 0.9
        top = c['top'] if c['ring'] != 'A' else funnel_top(R_BR0) - 0.28
        if abs(off) < 0.25: D.poly(box(u - 0.175, z0, u + 0.175, top), 'A-COLS', fill=CUT, edge=None, z=5)
        elif 0 < off < 14: D.poly(box(u - 0.175, z0, u + 0.175, top), 'A-ELEV', fill=None, edge=BEY, lw=0.09, z=2)
    # ---- mast (beyond or cut)
    u = X.u(C); D.poly(Polygon([(u - 0.42, 0.9), (u + 0.42, 0.9), (u + 0.1, SC.LV['mast']), (u - 0.1, SC.LV['mast'])]), 'A-ELEV', fill=GREYF, edge=INK, lw=0.18, z=3)
    D.circle((u, SC.LV['mast'] + 0.25), 0.25, 'A-ELEV', fill='white', edge=INK, lw=0.13)
    # ---- beyond: roof outer edge and L1 / L2 slab edges seen in the looking half (silhouettes)
    for rr, zf, lw in ((R_ROOF, lambda b: SC.roof_h(b), 0.18), (R_ROOF, lambda b: SC.roof_h(b) - 0.12, 0.09), (R_L1, lambda b: 5.4, 0.13), (R_L1, lambda b: 4.8, 0.09)):
        segs, cur = [], []
        for bb in np.arange(0, 360, 0.5):
            p = P(rr, bb); off = float(np.dot(p - X.a, nrm))
            ok = off > 0.3 and (rr != R_L1 or not SC.L1_VOID.contains(Point(p))) and (rr != R_ROOF or not SC.RF_VOID.buffer(0.2).contains(Point(p)))
            if ok: cur.append((X.u(p), zf(bb)))
            elif cur: segs.append(cur); cur = []
        if cur: segs.append(cur)
        for sgm in segs:
            if len(sgm) > 1: D.line(sorted(sgm), 'A-ELEV', lw=lw, color=BEY, z=2)
    # facade fins beyond (thin verticals, only the half we look at, within 9 m of the cut plane so the drawing stays readable)
    for bb, ang, top in SC.FINS:
        p = P(R_L1, bb); off = float(np.dot(p - X.a, nrm))
        if 0.3 < off < 9.0: D.line([(X.u(p), 5.4), (X.u(p), top)], 'A-ELEV', lw=0.07, color=BEY, z=2)
    # ---- stairs cut by the line (S4 + cores), drawn as flights
    for k, c in list(CORES.items()):
        if X.line.distance(Point(plans.frame(c['bc'], 0, (c['v_s0'] + c['v_s1']) / 2))) < c['W'] / 2:
            stair_flights(D, X, c)
    if X.line.distance(Point(plans.frame(S4['bc'], 0, S4['v0'] + 3))) < S4['w'] / 2:
        s4_flights(D, X)
    # ---- entrance canopies: cover + ribs where the cut passes through, the far edge beam beyond
    for c in LS.CANOPIES:
        us = np.linspace(0, X.L, int(X.L / 0.1))
        cut_pts, bey = [], []
        for u in us:
            p = X.pt(u); v = p - C; s_ = float(np.dot(v, d(c['b']))); off = float(np.dot(v, tdir(c['b'])))
            if not (c['R_in'] <= s_ <= c['R_out']): continue
            h = LS.hw(c, s_)
            if abs(off) <= h: cut_pts.append((u, s_, off / h))
        if len(cut_pts) > 2:
            top = [(u, LS.z_top(c, s_, t)) for u, s_, t in cut_pts]
            bot = [(u, LS.z_top(c, s_, t) - LS.rib_depth(c, s_)) for u, s_, t in cut_pts]
            D.poly(Polygon(top + bot[::-1]).buffer(0), 'L-CANP', fill='#CDBB93', edge=CUT, lw=0.13, z=5)
            for side in (-1, 1):
                pts = []
                for s_ in np.linspace(c['R_in'], c['R_out'], 60):
                    q = LS.xy(c, s_, side); off = float(np.dot(q - X.a, nrm))
                    if off > 0: pts.append((X.u(q), LS.z_edge(c, s_)))
                if len(pts) > 1: D.line(pts, 'L-CANP', lw=0.18, color='#9C845A', z=3)
            for q in LS.column_pts(c):
                for tp, zt in zip(q['tops'], q['ztops']):
                    if float(np.dot(np.array(q['base']) - X.a, nrm)) > -0.5: D.line([(X.u(q['base']), ground_z(q['base'])), (X.u(tp), zt)], 'L-CANP', lw=0.25, color='#9C845A', z=3)
            for (q, z0, z1) in LS.hangers(c):
                if abs(float(np.dot(np.array(q) - X.a, nrm))) < 4: D.line([(X.u(q), z0), (X.u(q), z1)], 'L-CANP', lw=0.07, color='#9C845A', z=3)
            um = cut_pts[len(cut_pts) // 2]
            D.text((um[0], LS.z_top(c, um[1], um[2]) + 0.9), 'ANYAMAN CANOPY', 'A-ANNO', size=1.7, halo=True)
    # ---- people, labels, levels
    seen = []
    for u_, z_, t in labels:
        if any(abs(u_ - s) < 3.5 and abs(z_ - zz) < 1 for s, zz in seen): continue
        seen.append((u_, z_)); D.text((u_, z_), wrapn(t, 14), 'A-ANNO', size=1.9, color=INK, halo=True)
    # ring grid bubbles under the section (where the cut crosses rings A-D) and hatched earth edge
    us = np.linspace(0, X.L, int(X.L / 0.02))
    rs = np.array([rad(X.pt(u)) for u in us])
    for lab, R in (('A', R_BR0), ('B', R_BR1), ('C', R_GF), ('D', R_L1)):
        for i in np.where(np.diff(np.sign(rs - R)) != 0)[0]:
            u = us[i]; D.line([(u, -2.4), (u, ground_z(X.pt(u)))], 'A-GRID', lw=0.07, color='#7A8590', ls='-.', z=2)
            D.circle((u, -2.9), 0.45, 'A-GRID', fill='white', edge='#7A8590', lw=0.13, z=7); D.text((u, -2.9), lab, 'A-GRID', size=1.6, color='#5B6570', z=8)
    uc = X.u(C) if 0 < X.u(C) < X.L else None
    if uc is not None:
        D.line([(uc, -2.4), (uc, 0.9)], 'A-GRID', lw=0.07, color='#7A8590', ls='-.'); D.circle((uc, -2.9), 0.45, 'A-GRID', fill='white', edge='#7A8590', lw=0.13, z=7); D.text((uc, -2.9), 'C', 'A-GRID', size=1.6, color='#5B6570', z=8)
    level_marks(D, X.L + 1.5, [(0, '±0.000 SITE'), (0.9, '+0.900 FFL GF'), (5.4, '+5.400 FFL L1'), (9.6, '+9.600 FFL L2'),
                                (10.2, '+10.200 ROOF LOW'), (13.5, '+13.500 FUNNEL RIM'), (16.2, '+16.200 ROOF HIGH'), (30.0, '+30.000 MAST TOP')])
    for u_ in (0.4, X.L - 0.4): pass
    return D, X

def wrapn(t, n):
    out, line = [], ''
    for w in t.split(' '):
        if len(line) + len(w) + 1 > n and line: out.append(line); line = w
        else: line = (line + ' ' + w).strip()
    out.append(line); return '\n'.join(out)

def stair_flights(D, X, c):
    """switchback core stair as seen in a cut along its axis: two flights per storey"""
    u_in = X.u(plans.frame(c['bc'], 0, c['v_s0'] + c['sw'])); u_out = X.u(plans.frame(c['bc'], 0, c['v_s1'] - c['sw']))
    sg = 1 if u_out > u_in else -1
    floors = [('GF', 'L1', 26), ('L1', 'L2', 24)] if c['to_l2'] else [('GF', 'L1', 26)]
    for f0, f1, n in floors:
        z0, z1 = FFL[f0], FFL[f1]; h = (z1 - z0) / n; half = n // 2
        g = (abs(u_out - u_in)) / (half - 1)
        pts = [(u_in, z0)]
        for i in range(half):                                 # first flight outwards (cut)
            uu = u_in + sg * g * i; pts += [(uu, z0 + h * (i + 1)), (uu + sg * g, z0 + h * (i + 1))]
        D.line(pts[:-1], 'A-STRS', lw=0.25, color=CUT, z=6)
        zl = z0 + h * half
        D.line([(u_out, zl), (u_out + sg * c['sw'], zl)], 'A-STRS', lw=0.35, color=CUT, z=6)
        pts = []
        for i in range(n - half):                             # return flight (beyond)
            uu = u_out - sg * g * i; pts += [(uu, zl + h * (i + 1)), (uu - sg * g, zl + h * (i + 1))]
        D.line([(u_out, zl)] + pts[:-1], 'A-STRS', lw=0.13, color=BEY, z=3)
    # enclosure top
    top = (FFL['L2'] if c['to_l2'] else FFL['L1']) + 3.3
    for v in (c['v_s0'] - 0.2, c['v_s1'] + 0.2):
        uu = X.u(plans.frame(c['bc'], 0, v)); D.poly(box(uu - 0.1, 0.9, uu + 0.1, top), 'A-WALL', fill=CUT, edge=None, z=5)
    u0, u1 = sorted((X.u(plans.frame(c['bc'], 0, c['v_s0'] - 0.3)), X.u(plans.frame(c['bc'], 0, c['v_s1'] + 0.3))))
    D.poly(box(u0, top, u1, top + 0.25), 'A-SLAB', fill=CUT, edge=None, z=5)

def s4_flights(D, X):
    """external stair S4: L1 +5.400 down to the +0.900 garden terrace, 2 flights of 13 x 173, landing 2200"""
    u0 = X.u(plans.frame(S4['bc'], 0, S4['v0'])); u1 = X.u(plans.frame(S4['bc'], 0, S4['v1']))
    sg = 1 if u1 > u0 else -1; h = 4.5 / 26
    pts = [(u0, 5.4)]; uu = u0; z = 5.4
    for i in range(13): uu += sg * M.GO * (1 if i else 0); pts += [(uu, z), (uu, z - h)]; z -= h
    uu += sg * S4['land']; pts.append((uu, z))
    for i in range(13): pts += [(uu, z - h), (uu + sg * M.GO, z - h)]; uu += sg * M.GO; z -= h
    D.line(pts, 'A-STRS', lw=0.3, color=CUT, z=6)
    D.line([(u0, 5.4 - 0.35), (u0 + sg * (12 * M.GO + S4['land'] + 12 * M.GO), 0.9 - 0.35)], 'A-STRS', lw=0.2, color=CUT, z=6)
    D.text(((u0 + u1) / 2, 4.6), 'STAIR 4 (EXTERNAL)\n26 R x 173, G 280', 'A-ANNO', size=1.6, halo=True)

# ------------------------------------------------------------------------------------------------ elevations
def elevation(view_b, label):
    """orthographic elevation seen from bearing view_b (the viewer stands at that bearing looking at C).
    u runs left -> right as seen by the viewer."""
    D = Drawing(f'ELEVATION {label}')
    vd = d(view_b)                                         # towards the viewer
    right = np.array([vd[1], -vd[0]]) * -1                 # viewer's right hand
    right = np.array([-vd[1], vd[0]])
    U = lambda p: float(np.dot(np.array(p) - C, right))
    depth = lambda p: float(np.dot(np.array(p) - C, vd))   # bigger = nearer the viewer
    front = lambda bb: np.dot(d(bb), vd) > 0.02
    # ground line + site boundary extent
    D.line([(-48, 0), (48, 0)], 'A-SITE', lw=0.5, color=INK, z=9)
    D.poly(box(-48, -1.2, 48, 0), 'A-SITE', fill=EARTH, edge=None, z=1)
    # mast (back)
    D.poly(Polygon([(-0.42, 0.9), (0.42, 0.9), (0.1, SC.LV['mast']), (-0.1, SC.LV['mast'])]), 'A-ELEV', fill=GREYF, edge=INK, lw=0.18, z=1)
    D.circle((0, SC.LV['mast'] + 0.25), 0.25, 'A-ELEV', fill='white', edge=INK, lw=0.13, z=1)
    # far roof silhouette (back half) as a light line, so the wave reads all round
    bs = np.arange(0, 360, 0.5)
    back = [(U(P(R_ROOF, b)), SC.roof_h(b)) for b in bs if not front(b)]
    # draw nearer-first sorting: we use painter's order by depth for each band segment
    items = []
    for b in bs:
        b1 = b + 0.5; p0, p1 = P(R_ROOF, b), P(R_ROOF, b1)
        if SC.RF_VOID.buffer(0.3).contains(Point(P(R_ROOF, b + 0.25))): continue
        dep = depth(P(R_ROOF, b + 0.25))
        q = Polygon([(U(p0), SC.roof_h(b) - 0.12 - (ROOF_T if dep < 0 else 0)), (U(p1), SC.roof_h(b1) - 0.12 - (ROOF_T if dep < 0 else 0)), (U(p1), SC.roof_h(b1)), (U(p0), SC.roof_h(b))])
        items.append((dep, 'roof', q, b))
    for b in bs:
        b1 = b + 0.5; pm = P(R_L1, b + 0.25)
        if SC.L1_VOID.contains(Point(pm)): continue
        dep = depth(pm)
        if dep < 0: continue
        p0, p1 = P(R_L1, b), P(R_L1, b1)
        top0, top1 = SC.roof_h(b) - 0.12, SC.roof_h(b1) - 0.12
        items.append((dep - 1.8, 'veil', Polygon([(U(p0), 5.4), (U(p1), 5.4), (U(p1), top1), (U(p0), top0)]), b))
        items.append((dep, 'l1', Polygon([(U(p0), 4.8), (U(p1), 4.8), (U(p1), 5.4), (U(p0), 5.4)]), b))
        if M.PLATE['L2'].buffer(0.3).contains(Point(P(R_L1 - 0.5, b + 0.25))):
            items.append((dep, 'l2', Polygon([(U(p0), 9.0), (U(p1), 9.0), (U(p1), 9.6), (U(p0), 9.6)]), b))
        pg = P(R_GF, b + 0.25)
        if SC.GF.buffer(0.2).contains(Point(pg)):
            items.append((dep - 3.6, 'gf', Polygon([(U(P(R_GF, b)), 0.9), (U(P(R_GF, b1)), 0.9), (U(P(R_GF, b1)), 4.8), (U(P(R_GF, b)), 4.8)]), b))
    for c in LS.CANOPIES:
        for s_ in np.arange(c['R_in'], c['R_out'] - 1e-6, 0.75):
            s1 = min(c['R_out'], s_ + 0.75)
            for t in np.linspace(-1, 1, 9)[:-1]:
                t1 = t + 0.25; sm, tm = (s_ + s1) / 2, t + 0.125
                pts = [(s_, t), (s1, t), (s1, t1), (s_, t1)]
                q = Polygon([(U(LS.xy(c, a, b)), LS.z_top(c, a, b)) for a, b in pts])
                if q.area < 1e-4: q = q.buffer(0.01)
                kind = 'can_solid' if LS.cell_solid(c, sm, tm) else 'can_glass'
                items.append((depth(LS.xy(c, sm, tm)) + 0.5, kind, q, 0))
            for side in (-1, 1):
                q = Polygon([(U(LS.xy(c, s_, side)), LS.z_edge(c, s_) - 0.4), (U(LS.xy(c, s1, side)), LS.z_edge(c, s1) - 0.4),
                             (U(LS.xy(c, s1, side)), LS.z_edge(c, s1)), (U(LS.xy(c, s_, side)), LS.z_edge(c, s_))])
                items.append((depth(LS.xy(c, sm, side)) + 0.6, 'can_beam', q.buffer(0.005), 0))
    items.sort(key=lambda t: t[0])
    colors = dict(roof=('#2B3036', None), veil=('#EEF1F3', None), l1=('#3A4048', None), l2=('#3A4048', None), gf=('#C9D3DA', None),
                  can_solid=('#CDBB93', None), can_glass=('#E3ECEF', None), can_beam=('#9C845A', None))
    for dep, kind, q, b in items:
        fc = colors[kind][0]
        if kind == 'roof' and dep < 0: fc = '#596069'
        D.poly(q.buffer(0.004), 'L-CANP' if kind.startswith('can') else 'A-ELEV', fill=fc, edge=None, z=2 + (dep + 40) / 100)
    # fins (front half), drawn as their projected width
    for bb, ang, top in SC.FINS:
        dep = depth(P(R_L1, bb))
        if dep < 0: continue
        p = P(R_L1, bb); tn = np.array([math.cos(math.radians(bb)), -math.sin(math.radians(bb))])
        a = math.radians(ang); fd = d(bb) * math.sin(a) + tn * math.cos(a)
        e0, e1 = p, p + fd * SC.FIN_D
        u0, u1 = sorted((U(e0), U(e1)))
        if u1 - u0 < 0.03: u1 = u0 + 0.03
        D.poly(box(u0, 5.4, u1, top), 'A-ELEV', fill='#8C949C', edge='#5E666E', lw=0.05, z=2 + (dep + 40) / 100 + 0.001)
    for c in LS.CANOPIES:
        for q in LS.column_pts(c):
            if depth(q['base']) < -2: continue
            for tp, zt in zip(q['tops'], q['ztops']):
                D.line([(U(q['base']), 0.0), (U(tp), zt)], 'L-CANP', lw=0.3, color='#7E6A45', z=2 + (depth(q['base']) + 40) / 100 + 0.002)
    # plinth band and steps
    D.poly(box(-(R_GF + 1.5), 0, R_GF + 1.5, 0.9), 'A-ELEV', fill='#DCD8CF', edge=INK, lw=0.13, z=1.5)
    # people for scale
    for u_ in (-18, -6, 9, 21): man(D, u_, 0.9 if abs(u_) < R_GF else 0.0, color='#596069')
    level_marks(D, 31.5, [(0, '±0.000 SITE'), (0.9, '+0.900 FFL GF'), (5.4, '+5.400 FFL L1'), (9.6, '+9.600 FFL L2'),
                          (10.2, '+10.200 ROOF LOW'), (13.5, '+13.500 FUNNEL RIM'), (16.2, '+16.200 ROOF HIGH'), (30.0, '+30.000 MAST')])
    return D

def section_set():
    L = plans.sec_lines()
    A = section(*L['A'], look_side=plans.SEC_LOOK['A'], label='A')
    B = section(*L['B'], look_side=plans.SEC_LOOK['B'], label='B')
    return A, B
