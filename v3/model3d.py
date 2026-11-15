"""3D model of Titik Temu v3, built from the same room model as the drawing set (plan3 + plans + sections + siteplan).
Coordinates = site metres (x east, y north, z up), the same as the DXF drawings, so the model drops straight onto them.
python3 model3d.py  ->  out/3d/titik-temu-v3.dae (SketchUp: File > Import > COLLADA), .glb (viewers), .obj + .mtl"""
import os, math, json
import numpy as np
import trimesh
from trimesh.creation import extrude_polygon
import mapbox_earcut as earcut
from shapely.geometry import Polygon, MultiPolygon, Point, LineString, box
from shapely.ops import unary_union
import plan3 as M
from plan3 import C, P, d, tdir, frame, SC, CORES, S4, EXT, FFL, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, R_OCULUS
import plans, sections as SE, siteplan as ST, landscape as LS
import rings as RG

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', '3d'); os.makedirs(OUT, exist_ok=True)

# layer -> (colour, opacity). Layer names match the DXF layers where they overlap, so SketchUp tags line up.
MAT = {
    'SITE-LAWN': ('#9DB585', 1.0), 'SITE-PAVING': ('#E3DCCD', 1.0), 'SITE-ROAD': ('#6E7176', 1.0), 'SITE-PLINTH': ('#CFC8BA', 1.0),
    'SITE-WATER': ('#4F9CC0', 0.85), 'SITE-TREE': ('#6F9460', 1.0), 'SITE-TRUNK': ('#7A6650', 1.0),
    'A-SLAB': ('#D8D4CC', 1.0), 'A-BRIDGE': ('#E4E0D8', 1.0), 'A-WALL': ('#EEECE8', 1.0), 'A-CORE': ('#C9C4BB', 1.0), 'A-GLAZ': ('#8DBBD3', 0.32),
    'A-ROOFLIGHT': ('#DDEBF2', 0.6), 'A-CLERESTORY': ('#9CC6DA', 0.45), 'A-ROOF-MID': ('#C3C8CE', 1.0),
    'A-COLS': ('#E2DFD8', 1.0), 'A-STRS': ('#BDB7AD', 1.0), 'A-BALU': ('#A9CDE0', 0.25), 'A-ROOF': ('#CDD1D6', 1.0),
    'A-ROOF-SOFFIT': ('#E9E5DC', 1.0), 'A-FUNNEL': ('#EAE6DD', 1.0), 'A-MAST': ('#D9CFB4', 1.0), 'A-FIN': ('#A39C88', 1.0),
    'A-FASCIA': ('#3A4048', 1.0), 'A-UTIL': ('#B7BCC2', 1.0), 'A-FURN': ('#8A7F70', 1.0),
    'L-CANP-RIB': ('#A88B57', 1.0), 'L-CANP-PANEL': ('#D8C69C', 1.0), 'L-CANP-GLASS': ('#CFE3EC', 0.38), 'L-CANP-COL': ('#8E7448', 1.0),
    'L-PLANTER': ('#C9C1B1', 1.0), 'L-SOIL': ('#6B5A44', 1.0), 'L-PLANT': ('#5E8F4C', 1.0), 'L-PLAY': ('#9DC08A', 1.0),
}

# ------------------------------------------------------------------------------------------------ mesh helpers
def _polys(g):
    if g is None or g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    return [q for q in getattr(g, 'geoms', []) if q.geom_type == 'Polygon' and q.area > 1e-6]

def tri_poly(poly):
    """earcut triangulation of a shapely polygon with holes -> (verts2d, faces)"""
    rings = [np.array(poly.exterior.coords)[:-1]] + [np.array(r.coords)[:-1] for r in poly.interiors]
    verts = np.vstack(rings).astype(np.float64)
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    f = earcut.triangulate_float64(verts, ends).reshape(-1, 3)
    return verts, f

def flat(poly, z0, z1):
    out = []
    for p in _polys(poly):
        p = p.buffer(0)
        for q in _polys(p):
            try:
                m = extrude_polygon(q, z1 - z0); m.apply_translation((0, 0, z0)); out.append(m)
            except Exception:
                pass
    return out

def draped(poly, ztop, zbot, cell=None, seg=0.6):
    """solid whose top and bottom follow ztop(x, y) / zbot(x, y). The polygon is cut into polar cells so a
    curved top (wave roof, ramp, funnel) is followed closely. cell = (degrees, metres) or None for no cutting."""
    meshes = []
    for p in _polys(poly):
        pieces = [p]
        if cell:
            db, dr = cell; pieces = []
            rs = [plans.rad(c) for ring in [p.exterior] + list(p.interiors) for c in ring.coords]
            r0, r1 = max(0.0, min(rs) - 0.01), max(rs) + 0.01
            for b in np.arange(0, 360, db):
                sec = SC.sector(b, b + db)
                for r in np.arange(r0, r1, dr):
                    g = p.intersection(sec.intersection(SC.ann(r, r + dr) if r > 0 else SC.disc(r + dr)))
                    pieces += _polys(g)
        V, F = [], []
        for q in pieces:
            v, f = tri_poly(q)
            n = len(V)
            V += [(x, y, ztop(x, y)) for x, y in v]; F += [(a + n, b + n, c + n) for a, b, c in f]
            n = len(V)
            V += [(x, y, zbot(x, y)) for x, y in v]; F += [(a + n, c + n, b + n) for a, b, c in f]
        # side walls along the densified outline
        for ring in [p.exterior] + list(p.interiors):
            ls = LineString(ring.coords); L = ls.length; k = max(4, int(L / seg))
            pts = [ls.interpolate(L * i / k).coords[0] for i in range(k)]
            if not ring.is_ccw ^ (ring is not p.exterior): pass
            for i in range(k):
                a, b = pts[i], pts[(i + 1) % k]; n = len(V)
                V += [(a[0], a[1], zbot(*a)), (b[0], b[1], zbot(*b)), (b[0], b[1], ztop(*b)), (a[0], a[1], ztop(*a))]
                F += [(n, n + 1, n + 2), (n, n + 2, n + 3)]
        if V:
            m = trimesh.Trimesh(np.array(V), np.array(F), process=True); m.fix_normals(); meshes.append(m)
    return meshes

def boxy(pts4, z0, z1):
    return flat(Polygon(pts4), z0, z1)

def cyl(p, r, z0, z1, sections=16):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections); m.apply_translation((p[0], p[1], (z0 + z1) / 2)); return [m]

def cone(p, r0, r1, z0, z1, sections=24):
    prof = [[0, 0], [r0, 0], [r1, z1 - z0], [0, z1 - z0]]
    m = trimesh.creation.revolve(prof, sections=sections); m.apply_translation((p[0], p[1], z0)); return [m]

# ------------------------------------------------------------------------------------------------ the model
def walls_top(fl):
    if fl == 'GF': return lambda x, y: 4.8
    if fl == 'L1':
        l2 = M.PLATE['L2'].buffer(0.3)
        return lambda x, y: 9.0 if l2.contains(Point(x, y)) else SE.roof_under((x, y))
    return lambda x, y: SE.roof_under((x, y))

def build():
    L = {k: [] for k in MAT}
    add = lambda k, ms: L[k].extend(ms)
    # ---- site: lawn, roads, paving, plinth, ramps, terrace, pool
    lawn = SC.SITE.difference(SC.disc(R_GF + 1.5)).difference(ST.TERRACE)
    hard = unary_union([g for _, g in ST.forecourts()] + [ST.YARD, ST.AISLE, ST.HS_S, SC.ann(*ST.PROM_R).intersection(SC.SITE)] + [g for _, g in ST.PARK] + ST.MOTOR + ST.BIKES)
    ramp_zone = unary_union([SC.strip(s['b'], s['w'] + 2.0, R_BR0, 95) for s in SC.SPINES]).intersection(SC.SITE)
    add('SITE-LAWN', flat(lawn.difference(hard).difference(ST.UB), -0.3, 0.0))
    add('SITE-PAVING', flat(hard.difference(ramp_zone).difference(SC.disc(R_GF + 1.5)), -0.3, 0.02))
    for i, nm, w in ((ST.S_ROAD, 'S', 12.0), (ST.E_ROAD, 'E', 10.0), (3, 'E2', 10.0)):
        a, b, t, n = ST.edge(i); no = -ST.inward(i)
        add('SITE-ROAD', flat(Polygon([a - t * 12, b + t * 12, b + t * 12 + no * w, a - t * 12 + no * w]).difference(SC.SITE), -0.45, -0.15))
    plinth = SC.disc(R_GF + 1.5).difference(ramp_zone).difference(SC.disc(R_POOL + 0.2))
    add('SITE-PLINTH', flat(plinth, -0.3, 0.9))
    add('SITE-PLINTH', flat(ST.TERRACE, -0.3, 0.9))
    gz = lambda x, y: SE.ground_z((x, y))
    for s in SC.SPINES:
        rz = SC.strip(s['b'], s['w'] + 2.0, R_BR0, 95).intersection(SC.SITE)
        add('SITE-PAVING', draped(rz, lambda x, y: gz(x, y), lambda x, y: -0.3, cell=(3.0, 1.0)))
    add('SITE-PLINTH', flat(SC.ann(R_POOL, R_POOL + 0.2), 0.1, 0.9))
    add('SITE-PLINTH', flat(SC.disc(R_POOL), 0.1, 0.3))
    add('SITE-WATER', flat(SC.disc(R_POOL - 0.05), 0.3, 0.72))
    # ---- slabs + ring bridges
    thin = unary_union([M.BRIDGE, M.WALKWAYS])
    add('A-SLAB', flat(M.PLATE['L1'].difference(thin), 4.8, 5.4)); add('A-BRIDGE', flat(thin.intersection(M.PLATE['L1']), 5.05, 5.4))
    add('A-BRIDGE', flat(SC.ann(RG.R_M - 0.4, RG.R_M + 0.4), 4.7, 5.05))                        # ring beam of the free-standing bridge
    add('A-SLAB', flat(M.PLATE['L2'], 9.0, 9.6))
    add('A-ROOFLIGHT', flat(plans.gap_glass(), 5.27, 5.37))                                       # opal rooflights in the gaps (over GF rooms)
    # ---- walls (with door openings + heads), glazing, cores
    for fl in ('GF', 'L1', 'L2'):
        W = plans.walls(fl); dl = plans.door_list(fl); top = walls_top(fl); z0 = FFL[fl]
        cutd = unary_union([LineString([q['p'] - q['t'] * q['w'] / 2, q['p'] + q['t'] * q['w'] / 2]).buffer(0.32, cap_style=2) for q in dl]) if dl else Polygon()
        cs = plans.core_solid(fl)
        rw = W['solid'].difference(cs.buffer(0.02))
        add('A-WALL', draped(rw.difference(cutd), top, lambda x, y: z0, cell=(4.0, 3.0)))
        heads = cutd.intersection(rw.buffer(0.05))
        add('A-WALL', draped(heads, top, lambda x, y: z0 + 2.4, cell=(4.0, 3.0)))
        if not W['glaz'].is_empty:
            gl = W['glaz'].difference(cutd)
            add('A-GLAZ', draped(unary_union([ln.buffer(0.03, cap_style=2) for ln in getattr(gl, 'geoms', [gl]) if ln.length > 0.05]), top, lambda x, y: z0, cell=(4.0, 3.0)))
            add('A-GLAZ', draped(unary_union([LineString([q['p'] - q['t'] * q['w'] / 2, q['p'] + q['t'] * q['w'] / 2]).buffer(0.03, cap_style=2) for q in dl if q['kind'] in ('slide',)]).intersection(W['glaz'].buffer(0.1)) if dl else Polygon(), top, lambda x, y: z0 + 2.4, cell=(4.0, 3.0)))
    # cores: enclosure walls from GF to the core roof (lift overrun / stair roof under the funnel), tank room on core 2
    for c in CORES.values():
        enc = c['fp'].difference(c['holes'])
        dcut = []
        for dd in M.CORE_DOORS:
            if dd['key'].split('-')[0] != c['key']: continue
            t = np.array(dd['t']); p = np.array(dd['p']); dcut.append((dd['fl'], LineString([p - t * dd['w'] / 2, p + t * dd['w'] / 2]).buffer(0.32, cap_style=2)))
        top = c['top']
        levels = [0.9, 5.4, 9.6, top - 0.2] if c['to_l2'] else [0.9, 5.4, top - 0.2]
        fls = ['GF', 'L1', 'L2']
        for i in range(len(levels) - 1):
            za, zb = levels[i], levels[i + 1]
            cut = unary_union([g for f, g in dcut if f == fls[i]]) if any(f == fls[i] for f, _ in dcut) else Polygon()
            add('A-CORE', flat(enc.difference(cut), za, zb))
            add('A-CORE', flat(cut.intersection(enc.buffer(0.05)), za + 2.4, zb))
        add('A-CORE', flat(c['fp'], top - 0.2, top))
        if c.get('tank') is not None:
            tk = c['tank']; add('A-CORE', flat(tk.difference(tk.buffer(-0.2)), top, c['tank_top'] - 0.2)); add('A-CORE', flat(tk, c['tank_top'] - 0.2, c['tank_top']))
        if c['stair'] is not None: stairs(c, L)
    for st_ in EXT.values(): ext_stair3d(st_, L)
    # ---- columns
    for c in M.COLS:
        z0 = c['z0'] if c['z0'] is not None else SE.ground_z(c['p'])
        add('A-COLS', cyl(c['p'], c['r'], z0 - (0.3 if c['z0'] is None else 0.0), c['top'] + 0.05))
    # ---- roof petals (wave), fascia band, funnel, mast
    # three roof tiers on the wave, each 1.8 m above the one outside it, clerestories where they overlap, glazed gate slots
    add('A-ROOF', draped(RG.OUT_FP, lambda x, y: RG.out_top((x, y)), lambda x, y: RG.out_under((x, y)), cell=(1.5, 2.0)))
    add('A-ROOF-MID', draped(RG.MID_FP, lambda x, y: RG.mid_top((x, y)), lambda x, y: RG.mid_under((x, y)), cell=(1.5, 1.4)))
    add('A-FUNNEL', draped(RG.FUN_FP, lambda x, y: RG.fun_top((x, y)), lambda x, y: RG.fun_under((x, y)), cell=(3.0, 1.0)))
    add('A-GLAZ', draped(RG.SLOT_GLASS, lambda x, y: RG.roof_top_at((x, y)) - 0.02, lambda x, y: RG.roof_top_at((x, y)) - 0.08, cell=(1.0, 1.0)))
    for g, top, und in ((SC.ann(M.R_ROOF, M.R_ROOF + 0.06).difference(SC.RF_VOID), lambda x, y: RG.out_top((x, y)) + 0.02, lambda x, y: RG.out_top((x, y)) - 0.32),
                        (SC.ann(RG.T_MID[1], RG.T_MID[1] + 0.06).difference(SC.RF_VOID), lambda x, y: RG.mid_top((x, y)) + 0.02, lambda x, y: RG.mid_under((x, y))),
                        (SC.ann(RG.T_MID[0] - 0.06, RG.T_MID[0]).difference(SC.RF_VOID), lambda x, y: RG.mid_top((x, y)) + 0.02, lambda x, y: RG.mid_under((x, y))),
                        (SC.ann(RG.R_FUN, RG.R_FUN + 0.06), lambda x, y: RG.fun_top((x, y)) + 0.02, lambda x, y: RG.fun_under((x, y)) - 0.1)):
        add('A-FASCIA', draped(g, top, und, cell=(1.0, 1.0)))
    add('A-CLERESTORY', draped(SC.ann(16.22, 16.28), lambda x, y: RG.fun_under((x, y)), lambda x, y: RG.mid_top((x, y)), cell=(1.0, 1.0)))
    add('A-CLERESTORY', draped(SC.ann(20.87, 20.93).difference(SC.RF_VOID), lambda x, y: RG.mid_under((x, y)), lambda x, y: RG.out_top((x, y)), cell=(1.0, 1.0)))
    add('A-MAST', cone(C, 0.42, 0.1, 0.9, SC.LV['mast']))
    s = trimesh.creation.icosphere(subdivisions=2, radius=0.25); s.apply_translation((C[0], C[1], SC.LV['mast'] + 0.25)); add('A-MAST', [s])
    # ---- facade fins (option A) + deck balustrades
    for bb, ang, top in SC.FINS:
        p = P(R_L1, bb); tn = np.array([math.cos(math.radians(bb)), -math.sin(math.radians(bb))])
        a = math.radians(ang); fd = d(bb) * math.sin(a) + tn * math.cos(a); nn = np.array([-fd[1], fd[0]])
        q0, q1 = p, p + fd * SC.FIN_D
        add('A-FIN', boxy([q0 - nn * 0.03, q1 - nn * 0.03, q1 + nn * 0.03, q0 + nn * 0.03], 5.4, top))
    for fl, z in (('L1', 5.4), ('L2', 9.6)):
        rooms_fp = unary_union([r['poly'] for r in plans.rooms(fl)] + [c['fp'] for c in CORES.values()]).buffer(0.15)
        for g in _polys(M.PLATE[fl]):
          for rg in [g.exterior] + list(g.interiors):
            ring = LineString(rg.coords).difference(rooms_fp)
            for ln in getattr(ring, 'geoms', [ring]):
                if ln.length > 0.3: add('A-BALU', flat(ln.buffer(0.015, cap_style=2).intersection(g.buffer(0.02)), z, z + 1.1))
    # ---- utility block, trees
    add('A-UTIL', flat(ST.UB, 0.0, 4.5))
    for i, nt in ((ST.S_ROAD, 9), (ST.E_ROAD, 6), (0, 6)):
        a, b, t, _ = ST.edge(i); Ln = np.linalg.norm(b - a)
        for k in range(nt):
            p = a + t * Ln * (k + 0.5) / nt + ST.inward(i) * 2.0
            if any(g.buffer(1.5).contains(Point(p)) for g in [ST.AISLE, ST.YARD, ST.HS_S, ST.UB, LS.CANOPY_FP] + [g for _, g in ST.forecourts()] + [g for _, g in ST.PARK] + ST.OUTER): continue
            add('SITE-TRUNK', cyl(p, 0.15, 0.0, 3.2, 8))
            s = trimesh.creation.icosphere(subdivisions=1, radius=2.4); s.apply_scale((1, 1, 0.8)); s.apply_translation((p[0], p[1], 5.0)); add('SITE-TREE', [s])
    landscape3d(L)
    return {k: trimesh.util.concatenate(v) for k, v in L.items() if v}

def prism(top_pts, depth, half):
    """thin plate following a 3D polyline (top edge), hanging 'depth' below it, 2*half thick"""
    out = []
    for p0, p1 in zip(top_pts[:-1], top_pts[1:]):
        p0, p1 = np.array(p0, float), np.array(p1, float); v = p1[:2] - p0[:2]; L_ = np.linalg.norm(v)
        if L_ < 1e-4: continue
        n = np.array([-v[1], v[0]]) / L_ * half
        V = []
        for p in (p0, p1):
            for sg in (-1, 1): V += [(p[0] + n[0] * sg, p[1] + n[1] * sg, p[2]), (p[0] + n[0] * sg, p[1] + n[1] * sg, p[2] - depth)]
        # V: 0 p0- top,1 p0- bot,2 p0+ top,3 p0+ bot,4 p1- top,5 p1- bot,6 p1+ top,7 p1+ bot
        F = [(0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5), (0, 1, 5), (0, 5, 4), (2, 6, 7), (2, 7, 3), (0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6)]
        out.append(trimesh.Trimesh(np.array(V), np.array(F), process=False))
    return out

def rod(p0, p1, r, sections=8):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    if np.linalg.norm(p1 - p0) < 1e-3: return []
    return [trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)]

def landscape3d(L):
    # ---- anyaman canopies
    for c in LS.CANOPIES:
        ss = np.arange(c['R_in'], c['R_out'] + 1e-6, 0.25); ts = np.linspace(-1, 1, 25)
        grid = np.array([[(*LS.xy(c, s, t), LS.z_top(c, s, t)) for t in ts] for s in ss])
        for kind in (True, False):
            V, F = [], []
            for i in range(len(ss) - 1):
                for j in range(len(ts) - 1):
                    if LS.cell_solid(c, (ss[i] + ss[i + 1]) / 2, (ts[j] + ts[j + 1]) / 2) != kind: continue
                    n = len(V); V += [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
                    F += [(n, n + 1, n + 2), (n, n + 2, n + 3)]
            if V: L['L-CANP-PANEL' if kind else 'L-CANP-GLASS'].append(trimesh.Trimesh(np.array(V), np.array(F)))
        for rib in LS.ribs(c, nt=16):
            pts = [(*LS.xy(c, s, t), LS.z_top(c, s, t) - 0.02) for s, t in rib]
            L['L-CANP-RIB'] += prism(pts, LS.rib_depth(c, rib[0][0]), 0.03)
        for side in (-1, 1):
            pts = [(*LS.xy(c, s, side), LS.z_edge(c, s)) for s in np.arange(c['R_in'], c['R_out'] + 1e-6, 0.5)]
            L['L-CANP-RIB'] += prism(pts, 0.4, 0.08)
        for q, z0, z1 in LS.hangers(c): L['L-CANP-RIB'] += rod((q[0], q[1], z0), (q[0], q[1], z1), 0.025)
        for q in LS.column_pts(c):
            gz = SE.ground_z(q['base'])
            for tp, zt in zip(q['tops'], q['ztops']): L['L-CANP-COL'] += rod((q['base'][0], q['base'][1], gz), (tp[0], tp[1], zt - 0.2), 0.11, 12)
            L['L-CANP-COL'] += cyl(q['base'], 0.3, gz - 0.05, gz + 0.12, 16)
    # ---- pocket gardens
    def planter(poly, z0, h=0.45, soil=0.38, wall=0.2, shrubs=True):
        inner = poly.buffer(-wall)
        L['L-PLANTER'] += flat(poly.difference(inner), z0, z0 + h)
        L['L-SOIL'] += flat(inner, z0, z0 + soil)
        if shrubs and not inner.is_empty:
            b = inner.bounds; rng = np.random.default_rng(int(abs(b[0] * 7 + b[1] * 13)) % 2**31)
            for x in np.arange(b[0] + 0.5, b[2], 1.1):
                for y in np.arange(b[1] + 0.5, b[3], 1.1):
                    p = (x + rng.uniform(-0.25, 0.25), y + rng.uniform(-0.25, 0.25))
                    if inner.buffer(-0.3).contains(Point(p)):
                        r = rng.uniform(0.35, 0.6); s = trimesh.creation.icosphere(subdivisions=1, radius=r)
                        s.apply_scale((1, 1, rng.uniform(0.7, 1.2))); s.apply_translation((p[0], p[1], z0 + soil + r * 0.6)); L['L-PLANT'].append(s)
    for q in ST.OUTER: planter(q, 0.0)
    for p in ST.POCKET_TREES:
        L['SITE-TRUNK'] += cyl(p, 0.16, 0.3, 3.4, 8)
        s = trimesh.creation.icosphere(subdivisions=2, radius=2.3); s.apply_scale((1, 1, 0.75)); s.apply_translation((p[0], p[1], 5.0)); L['SITE-TREE'].append(s)
    for g in ST.GATE:
        z0 = SE.ground_z(np.array(g['poly'].centroid.coords[0])); planter(g['poly'], z0)
    for a, b in LS.INNER:
        planter(LS.ann_sec(*LS.POCKET_IN_R, a, b), 0.9)
        L['A-FURN'] += flat(LS.ann_sec(*LS.BENCH_IN_R, a, b), 0.9, 1.35)
    for q in LS.SKY: planter(q, 5.4, h=0.6, soil=0.55, wall=0.15)
    # ---- Talam court: curved communal tables + benches, play surface
    for a, b in LS.TABLES:
        L['A-FURN'] += flat(LS.ann_sec(*LS.TABLE_R, a, b), 0.9 + 0.68, 0.9 + 0.75)
        L['A-FURN'] += flat(LS.ann_sec(LS.TABLE_R[0] + 0.3, LS.TABLE_R[1] - 0.3, a + 1, b - 1), 0.9, 0.9 + 0.68)
        for rr in (LS.BENCH_T_IN, LS.BENCH_T_OUT): L['A-FURN'] += flat(LS.ann_sec(*rr, a, b), 0.9, 0.9 + 0.45)
    L['L-PLAY'] += flat(LS.play_poly(), 0.9, 0.93)

def stairs(c, L):
    """tangential switch-back flights as solid steps + landings, matching the plan and sections"""
    f = c['f']; sw, vi, vo = c['sw'], c['vi'], c['vo']
    q = lambda u0, u1, v0, v1: [f(u0, v0), f(u1, v0), f(u1, v1), f(u0, v1)]
    for run in M.core_runs(c):
        uA0, uA1, h, z0 = run['uA0'], run['uA1'], run['h'], run['z0']; zl = z0 + run['nA'] * h
        for i in range(run['nA'] - 1):
            z = z0 + h * (i + 1); L['A-STRS'] += boxy(q(uA0 + i * M.GO, uA0 + (i + 1) * M.GO, vi + 0.05, vi + sw), z - 0.25, z)
        L['A-STRS'] += boxy(q(uA1, c['us1'], vi + 0.05, vo - 0.05), zl - 0.25, zl)
        for j in range(run['nB'] - 1):
            z = zl + h * (j + 1); L['A-STRS'] += boxy(q(uA1 - (j + 1) * M.GO, uA1 - j * M.GO, vo - sw, vo - 0.05), z - 0.25, z)
        L['A-STRS'] += boxy(q(c['us0'] + 0.05, uA0, vi + 0.05, vo - 0.05), run['z1'] - 0.25, run['z1'])

def ext_stair3d(st, L):
    f = st['f']; w = st['w']
    q = lambda u0, u1, v0, v1: [f(u0, v0), f(u1, v0), f(u1, v1), f(u0, v1)]
    for kind, u0, u1, z in st['parts']:
        L['A-STRS'] += boxy(q(u0, u1, -w / 2, w / 2), z - (0.3 if kind == 'land' else 0.25), z)
        for v in (-w / 2, w / 2): L['A-BALU'] += boxy(q(u0, u1, v - 0.015, v + 0.015), z, z + 1.0)
    if st['kind'] == 'tangential':
        q0 = P(R_L1 - 0.1, plans.brg(st['top']))
        L['A-STRS'] += flat(LineString([q0, st['top']]).buffer(1.1, cap_style=2), 5.05, 5.4)
    for u0, z0, u1, z1 in st['flights']:
        for v in (-w / 2 + 0.3, w / 2 - 0.3):                          # raking steel stringers
            L['A-STRS'] += prism([(*f(u0, v), z0 - 0.25), (*f(u1, v), z1 - 0.25)], 0.3, 0.06)

# ------------------------------------------------------------------------------------------------ export
def write_dae(layers, path):
    """COLLADA 1.4 for SketchUp: one node (= one SketchUp group/tag) and one coloured material per layer, metres, Z up,
    site coordinates unchanged so it lines up with the DXF sheets"""
    import collada
    from collada import asset, material, source, geometry, scene as cscene
    mesh = collada.Collada()
    mesh.assetInfo.unitname = 'meter'; mesh.assetInfo.unitmeter = 1.0; mesh.assetInfo.upaxis = asset.UP_AXIS.Z_UP
    nodes = []
    for k, m in layers.items():
        col, a = MAT[k]; h = col.lstrip('#'); rgb = tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        eff = material.Effect(f'{k}-effect', [], 'lambert', diffuse=rgb + (1.0,), transparency=a if a < 1 else None, transparent=(1.0, 1.0, 1.0, 1.0) if a < 1 else None, double_sided=True)
        mat = material.Material(f'{k}-material', k, eff)
        mesh.effects.append(eff); mesh.materials.append(mat)
        v = np.asarray(m.vertices, dtype=np.float32).ravel(); n = np.asarray(m.vertex_normals, dtype=np.float32).ravel()
        vs = source.FloatSource(f'{k}-verts', v, ('X', 'Y', 'Z')); ns = source.FloatSource(f'{k}-normals', n, ('X', 'Y', 'Z'))
        geom = geometry.Geometry(mesh, f'{k}-geom', k, [vs, ns])
        il = source.InputList(); il.addInput(0, 'VERTEX', f'#{k}-verts'); il.addInput(0, 'NORMAL', f'#{k}-normals')
        tri = geom.createTriangleSet(np.asarray(m.faces, dtype=np.int32).ravel(), il, f'{k}-mat')
        geom.primitives.append(tri); mesh.geometries.append(geom)
        mn = cscene.MaterialNode(f'{k}-mat', mat, inputs=[])
        nodes.append(cscene.Node(k, children=[cscene.GeometryNode(geom, [mn])]))
    sc = cscene.Scene('titik-temu-v3', nodes); mesh.scenes.append(sc); mesh.scene = sc
    mesh.write(path)

def glb_to_json(src, dst):
    """same model as a single glTF JSON with the binary buffer embedded (artifact pages can serve .json, not .glb)"""
    import struct, base64
    b = open(src, 'rb').read(); _, _, length = struct.unpack('<4sII', b[:12]); off = 12; js = binc = None
    while off < length:
        clen, ctype = struct.unpack('<II', b[off:off + 8]); data = b[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A: js = json.loads(data)
        elif ctype == 0x004E4942: binc = data
        off += 8 + clen
    js['buffers'][0]['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(binc).decode()
    open(dst, 'w').write(json.dumps(js, separators=(',', ':')))

def hexrgba(h, a):
    """glTF base colour factors are LINEAR: convert the sRGB hex so the colours read as specified"""
    h = h.lstrip('#'); lin = lambda c: (c / 255.0) / 12.92 if c / 255.0 <= 0.04045 else ((c / 255.0 + 0.055) / 1.055) ** 2.4
    return [lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)] + [a]

def export(layers):
    scene = trimesh.Scene()
    for k, m in layers.items():
        col, a = MAT[k]
        mat = trimesh.visual.material.PBRMaterial(name=k, baseColorFactor=hexrgba(col, a), metallicFactor=0.0, roughnessFactor=0.85,
                                                  alphaMode='BLEND' if a < 1 else 'OPAQUE', doubleSided=True)
        mm = m.copy(); mm.visual = trimesh.visual.TextureVisuals(material=mat)
        scene.add_geometry(mm, node_name=k, geom_name=k)
    # GLB is Y-up: rotate z-up site metres -> y-up, origin moved to the centre C so viewers orbit the building
    T = trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0)) @ trimesh.transformations.translation_matrix((-C[0], -C[1], 0))
    g = scene.copy(); g.apply_transform(T)
    g.export(os.path.join(OUT, 'titik-temu-v3.glb'))
    glb_to_json(os.path.join(OUT, 'titik-temu-v3.glb'), os.path.join(OUT, 'titik-temu-v3.gltf.json'))
    # DAE for SketchUp: z-up, metres, site coordinates (matches the DXF sheets)
    write_dae(layers, os.path.join(OUT, 'titik-temu-v3.dae'))
    obj = trimesh.exchange.obj.export_obj(scene, include_normals=True, include_color=True, mtl_name='titik-temu-v3.mtl', return_texture=True)
    txt, tex = obj if isinstance(obj, tuple) else (obj, {})
    open(os.path.join(OUT, 'titik-temu-v3.obj'), 'w').write(txt)
    for nm, data in tex.items(): open(os.path.join(OUT, nm), 'wb').write(data)
    stats = {k: dict(faces=int(len(m.faces)), colour=MAT[k][0]) for k, m in layers.items()}
    json.dump(stats, open(os.path.join(OUT, 'layers.json'), 'w'), indent=1)
    return stats

if __name__ == '__main__':
    layers = build()
    st = export(layers)
    print({k: v['faces'] for k, v in st.items()}, sum(v['faces'] for v in st.values()))
