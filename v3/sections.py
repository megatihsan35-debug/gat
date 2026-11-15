"""Sections and elevations from the same model (plan3 + scheme). Drawing coordinates: x = u (metres along the cut / across
the elevation), y = z (metres above site datum ±0.000). Placed on the sheet at 1:100 like the plans."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiLineString, box
from shapely.ops import unary_union
from cad import Drawing, INK
import plan3 as M
from plan3 import C, P, d, tdir, SC, FFL, CORES, S4, EXT, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, R_OCULUS
import plans
import landscape as LS
import rings as RG

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
def roof_top(p): return RG.roof_top_at(p)
def roof_under(p): return RG.roof_under_at(p)
def funnel_top(p): return RG.fun_top(p)                    # p = point (the funnel rim follows the wave, so it depends on bearing)
ROOF_FP = RG.OUT_FP                                       # outer tier
MID_FP = RG.MID_FP
FUNNEL_FP = RG.FUN_FP
L1_FP = M.PLATE['L1']
L2_FP = M.PLATE['L2']
THIN = unary_union([M.BRIDGE, M.WALKWAYS, M.WALK])       # 350 slabs: bridge, walkways, gallery walk edge
def core_top(c): return c.get('top', 13.2)

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
            pm = X.pt((u0 + u1) / 2)
            zb = z1 - 0.35 if THIN.contains(Point(pm)) else z0
            D.poly(box(u0, zb, u1, z1), 'A-SLAB', fill=CUT, edge=None, z=5)
    # the gaps: opal glass rooflights over the rooms (thin, light blue), open over the gates; glass balustrades either side
    for u0, u1 in X.spans(plans.gap_glass()):
        D.poly(box(u0, 5.3, u1, 5.42), 'A-GLAZ', fill=GLASS, edge=CUT, lw=0.09, z=5)
    for u0, u1 in X.spans(M.GAPS):
        for uu in (u0, u1): D.line([(uu, 5.4), (uu, 6.5)], 'A-GLAZ', lw=0.18, color='#5E9CBB', z=6)
    # ---- the three roof tiers (cut): outer tier, middle tier over the bridge, the funnel over the inner ring + court
    for fp, top, und in ((ROOF_FP, RG.out_top, RG.out_under), (MID_FP, RG.mid_top, RG.mid_under), (FUNNEL_FP, RG.fun_top, RG.fun_under)):
        for u0, u1 in X.spans(fp):
            band(D, u0, u1, lambda u, f=und: f(X.pt(u)), lambda u, f=top: f(X.pt(u)), 'A-ROOF', z=5)
    for u0, u1 in X.spans(RG.SLOT_GLASS):
        band(D, u0, u1, lambda u: roof_top(X.pt(u)) - 0.06, lambda u: roof_top(X.pt(u)), 'A-GLAZ', fill=GLASS, z=5)
    # clerestories: louvred glass between the tiers where the cut crosses R16.25 and R20.9
    us = np.linspace(0, X.L, int(X.L / 0.05)); rs = np.array([rad(X.pt(u)) for u in us])
    for Rc, lo, hi in ((16.25, RG.mid_top, RG.fun_under), (20.9, RG.out_top, RG.mid_under)):
        for i in np.where(np.diff(np.sign(rs - Rc)) != 0)[0]:
            p = X.pt(us[i]); D.poly(box(us[i] - 0.05, lo(p), us[i] + 0.05, hi(p)), 'A-GLAZ', fill=GLASS, edge=CUT, lw=0.09, z=5)
            for zz in np.arange(lo(p) + 0.25, hi(p) - 0.1, 0.3): D.line([(us[i] - 0.2, zz), (us[i] + 0.2, zz - 0.12)], 'A-GLAZ', lw=0.07, color=CUT, z=6)
    # ---- walls (cut) per floor, glazing
    tops = {'GF': lambda p: 4.8, 'L1': lambda p: 9.0 if M.PLATE['L2'].buffer(0.3).contains(Point(p)) else roof_under(p), 'L2': lambda p: roof_under(p) - 0.0}
    labels = []
    for fl in ('GF', 'L1', 'L2'):
        W = plans.walls(fl); dl = plans.door_list(fl)
        cutd = unary_union([LineString([q['p'] - q['t'] * q['w'] / 2, q['p'] + q['t'] * q['w'] / 2]).buffer(0.32, cap_style=2) for q in dl]) if dl else Polygon()
        for u0, u1 in X.spans(W['solid'].difference(cutd)):
            p = X.pt((u0 + u1) / 2); top = tops[fl](p); rr = rad(p)
            incore = [c for c in CORES.values() if c['fp'].buffer(0.05).contains(Point(p))]
            facade = min(abs(rr - R_GF), abs(rr - R_L1), abs(rr - R_BR1), abs(rr - M.R_IR1), abs(rr - M.R_OR0), abs(rr - M.R_GAL)) < 0.35 or bool(incore)
            if incore: top = core_top(incore[0]) if fl == ('L2' if incore[0]['to_l2'] else 'L1') else (FFL['L1'] - 0.6 if fl == 'GF' else FFL['L2'] - 0.6)
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
        z0 = c['z0'] if c['z0'] is not None else ground_z(p)
        top = c['top']; r_ = c['r']
        if abs(off) < 0.25: D.poly(box(u - r_, z0, u + r_, top), 'A-COLS', fill=CUT, edge=None, z=5)
        elif 0 < off < 14: D.poly(box(u - r_, z0, u + r_, top), 'A-ELEV', fill=None, edge=BEY, lw=0.09, z=2)
    # ---- mast (beyond or cut)
    u = X.u(C); D.poly(Polygon([(u - 0.42, 0.9), (u + 0.42, 0.9), (u + 0.1, SC.LV['mast']), (u - 0.1, SC.LV['mast'])]), 'A-ELEV', fill=GREYF, edge=INK, lw=0.18, z=3)
    D.circle((u, SC.LV['mast'] + 0.25), 0.25, 'A-ELEV', fill='white', edge=INK, lw=0.13)
    # ---- beyond: roof outer edge and L1 / L2 slab edges seen in the looking half (silhouettes)
    for rr, zf, lw in ((R_ROOF, lambda b: SC.roof_h(b), 0.18), (R_ROOF, lambda b: SC.roof_h(b) - 0.12, 0.09), (R_L1, lambda b: 5.4, 0.13), (R_L1, lambda b: 4.8, 0.09),
                       (RG.T_MID[1], lambda b: SC.roof_h(b) + RG.STEP, 0.15), (RG.T_MID[1], lambda b: SC.roof_h(b) + RG.STEP - RG.MID_T, 0.09),
                       (RG.R_FUN, lambda b: RG.fun_rim(b), 0.15), (RG.R_FUN, lambda b: RG.fun_rim(b) - RG.FUN_T, 0.09),
                       (M.R_BG1, lambda b: 5.4, 0.1), (M.R_BG1, lambda b: 5.05, 0.07), (M.R_IR1, lambda b: 9.6, 0.1)):
        segs, cur = [], []
        for bb in np.arange(0, 360, 0.5):
            p = P(rr, bb); off = float(np.dot(p - X.a, nrm))
            ok = off > 0.3 and (rr != R_ROOF or not SC.RF_VOID.buffer(0.2).contains(Point(p)))
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
        if c['stair'] is not None and X.line.intersects(c['stair']):
            stair_flights(D, X, c)
    for s_ in EXT.values():
        if s_['kind'] == 'radial' and X.line.distance(Point(s_['f'](3.0, 0))) < s_['w'] / 2:
            s4_flights(D, X, s_)
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
    level_marks(D, X.L + 1.5, LEVELS)
    for u_ in (0.4, X.L - 0.4): pass
    return D, X

def wrapn(t, n):
    out, line = [], ''
    for w in t.split(' '):
        if len(line) + len(w) + 1 > n and line: out.append(line); line = w
        else: line = (line + ' ' + w).strip()
    out.append(line); return '\n'.join(out)

LEVELS = [(0, '±0.000 SITE'), (0.9, '+0.900 FFL GF'), (5.4, '+5.400 FFL L1 · BRIDGE'), (9.6, '+9.600 FFL L2'),
          (10.2, '+10.200 OUTER TIER LOW'), (12.0, '+12.000 MIDDLE TIER LOW'), (13.8, '+13.800 FUNNEL RIM LOW'), (16.2, '+16.200 OUTER TIER HIGH'),
          (18.0, '+18.000 MIDDLE TIER HIGH'), (19.8, '+19.800 FUNNEL RIM HIGH'), (30.0, '+30.000 MAST TOP')]

def _local(c, p):
    """site point -> core local (u, v)"""
    q = np.array(p) - C; return float(np.dot(q, c['t'])), float(np.dot(q, d(c['bc'])))
def stair_z(c, run, u, outer):
    """top of tread / landing at local u for flight A (court side) or B (outer side) of one storey"""
    uA0, uA1, h, z0 = run['uA0'], run['uA1'], run['h'], run['z0']
    zl = z0 + run['nA'] * h
    if u >= uA1: return zl                                         # half landing
    if u <= uA0: return run['z1'] if outer else z0                 # floor landings
    if not outer: return z0 + h * (math.floor((u - uA0) / GO_) + 1)
    return zl + h * (math.floor((uA1 - u) / GO_) + 1)
GO_ = M.GO
def stair_flights(D, X, c):
    """tangential core stair cut across its width: each flight shows as a cut tread (or landing) at the height it has where
    the section passes; the enclosure walls come from the plan walls"""
    us = [u for u in np.linspace(0, X.L, int(X.L / 0.04)) if c['stair'].contains(Point(X.pt(u)))]
    if not us: return
    runs = M.core_runs(c); segs = {}
    for ri, run in enumerate(runs):
        zl = run['z0'] + run['nA'] * run['h']
        for u in us:
            lu, lv = _local(c, X.pt(u))
            keys = []
            if lu >= run['uA1']: keys.append(('mid', ri, zl))
            elif lu <= run['uA0']:
                keys.append(('floor', run['z0']))
                if ri == len(runs) - 1: keys.append(('floor', run['z1']))
            else:
                if c['vi'] <= lv <= c['vi'] + c['sw']: keys.append(('A', ri, stair_z(c, run, lu, False)))
                if c['vo'] - c['sw'] <= lv <= c['vo']: keys.append(('B', ri, stair_z(c, run, lu, True)))
            for k in keys: segs.setdefault(k, []).append(u)
    for k, uu in segs.items():
        z = k[-1]; uu = sorted(uu); start = uu[0]; prev = uu[0]
        for u in uu[1:] + [None]:
            if u is None or u - prev > 0.1:
                D.poly(box(start, z - 0.18, prev + 0.02, z), 'A-STRS', fill=CUT, edge=None, z=6)
                if u is not None: start = u
            if u is not None: prev = u
    um = (us[0] + us[-1]) / 2
    D.text((um, FFL['L1'] + 2.0), c['name'] + '\nSTAIR', 'A-ANNO', size=1.5, halo=True)
    top = core_top(c)
    u0, u1 = us[0] - 0.2, us[-1] + 0.2
    D.poly(box(u0, top - 0.2, u1, top), 'A-SLAB', fill=CUT, edge=None, z=5)
    if c.get('tank') is not None:
        ut = [u for u in np.linspace(0, X.L, int(X.L / 0.04)) if c['tank'].contains(Point(X.pt(u)))]
        if ut:
            a_, b_ = ut[0], ut[-1]
            D.poly(box(a_, c['tank_fl'] - 0.2, b_, c['tank_fl']), 'A-SLAB', fill=CUT, edge=None, z=5)
            D.poly(box(a_, c['tank_top'] - 0.2, b_, c['tank_top']), 'A-SLAB', fill=CUT, edge=None, z=5)
            for uu in (a_, b_): D.poly(box(uu - 0.1, c['tank_fl'], uu + 0.1, c['tank_top']), 'A-WALL', fill=CUT, edge=None, z=5)
            D.poly(box(a_ + 0.4, c['tank_fl'] + 0.3, b_ - 0.4, c['tank_fl'] + 1.3), 'P-EQPT', fill='#D8ECF7', edge=CUT, lw=0.13, z=6)
            D.text(((a_ + b_) / 2, c['tank_fl'] + 0.8), 'CW TANK', 'A-ANNO', size=1.2)

def s4_flights(D, X, s_):
    """external radial stair cut along its axis: flights + landing as a stepped profile"""
    pts = []
    for kind, u0, u1, z in s_['parts']:
        a, b = X.u(s_['f'](u0, 0)), X.u(s_['f'](u1, 0))
        pts += [(a, z), (b, z)]
    first = X.u(s_['f'](0, 0)); pts = [(first, s_['z_top'])] + pts
    last = X.u(s_['f'](s_['L'], 0)); pts.append((last, s_['z_bot']))
    D.line(pts, 'A-STRS', lw=0.3, color=CUT, z=6)
    D.line([(first, s_['z_top'] - 0.35), (last, s_['z_bot'] - 0.35 + 0.0)], 'A-STRS', lw=0.2, color=CUT, z=6)
    nr = sum(n for k, n in s_['seq'] if k == 'flight')
    D.text(((first + last) / 2, s_['z_top'] - 0.8), f"{s_['name']} (EXTERNAL)\n{nr} R x {int(round(s_['h'] * 1000))}, G 280", 'A-ANNO', size=1.6, halo=True)

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
    # the two upper tiers behind the outer roof: clerestory glass, then the tier fascia (front half only)
    for b in bs:
        b1 = b + 0.5
        for Rf, lo, hi, kind in ((RG.T_MID[1], lambda bb: SC.roof_h(bb), lambda bb: SC.roof_h(bb) + RG.STEP - RG.MID_T, 'cler'),
                                 (RG.T_MID[1], lambda bb: SC.roof_h(bb) + RG.STEP - RG.MID_T, lambda bb: SC.roof_h(bb) + RG.STEP, 'tier'),
                                 (RG.R_FUN, lambda bb: SC.roof_h(bb) + RG.STEP, lambda bb: RG.fun_rim(bb) - RG.FUN_T, 'cler'),
                                 (RG.R_FUN, lambda bb: RG.fun_rim(bb) - RG.FUN_T, lambda bb: RG.fun_rim(bb), 'tier')):
            pm = P(Rf, b + 0.25); dep = depth(pm)
            if Rf == RG.T_MID[1] and SC.RF_VOID.buffer(0.2).contains(Point(pm)): continue
            p0, p1 = P(Rf, b), P(Rf, b1)
            items.append((dep - 30, kind if dep >= 0 else kind + '_b', Polygon([(U(p0), lo(b)), (U(p1), lo(b1)), (U(p1), hi(b1)), (U(p0), hi(b))]).buffer(0.002), b))
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
    colors = dict(roof=('#2B3036', None), veil=('#EEF1F3', None), l1=('#3A4048', None), l2=('#3A4048', None), gf=('#C9D3DA', None), cler=('#BFD9E6', None), tier=('#3A4048', None), cler_b=('#D6E6EE', None), tier_b=('#6B727B', None),
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
    level_marks(D, 31.5, LEVELS)
    return D

def section_set():
    L = plans.sec_lines()
    A = section(*L['A'], look_side=plans.SEC_LOOK['A'], label='A')
    B = section(*L['B'], look_side=plans.SEC_LOOK['B'], label='B')
    return A, B
