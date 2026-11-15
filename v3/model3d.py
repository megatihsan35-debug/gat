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
from plan3 import C, P, d, tdir, frame, SC, CORES, S4, FFL, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, R_OCULUS
import plans, sections as SE, siteplan as ST

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', '3d'); os.makedirs(OUT, exist_ok=True)

# layer -> (colour, opacity). Layer names match the DXF layers where they overlap, so SketchUp tags line up.
MAT = {
    'SITE-LAWN': ('#9DB585', 1.0), 'SITE-PAVING': ('#E3DCCD', 1.0), 'SITE-ROAD': ('#6E7176', 1.0), 'SITE-PLINTH': ('#CFC8BA', 1.0),
    'SITE-WATER': ('#4F9CC0', 0.85), 'SITE-TREE': ('#6F9460', 1.0), 'SITE-TRUNK': ('#7A6650', 1.0),
    'A-SLAB': ('#D8D4CC', 1.0), 'A-WALL': ('#EEECE8', 1.0), 'A-CORE': ('#C9C4BB', 1.0), 'A-GLAZ': ('#8DBBD3', 0.32),
    'A-COLS': ('#E2DFD8', 1.0), 'A-STRS': ('#BDB7AD', 1.0), 'A-BALU': ('#A9CDE0', 0.25), 'A-ROOF': ('#CDD1D6', 1.0),
    'A-ROOF-SOFFIT': ('#E9E5DC', 1.0), 'A-FUNNEL': ('#EAE6DD', 1.0), 'A-MAST': ('#D9CFB4', 1.0), 'A-FIN': ('#A39C88', 1.0),
    'A-FASCIA': ('#3A4048', 1.0), 'A-UTIL': ('#B7BCC2', 1.0), 'A-FURN': ('#8A7F70', 1.0),
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
    hard = unary_union([g for _, g in ST.forecourts()] + [ST.YARD, ST.AISLE, ST.HS_S] + [g for _, g in ST.PARK] + ST.MOTOR + ST.BIKES)
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
    add('A-SLAB', flat(M.PLATE['L1'], 4.8, 5.4)); add('A-SLAB', flat(SC.ann(R_BR0, R_BR1), 5.05, 5.4))
    add('A-SLAB', flat(M.PLATE['L2'], 9.0, 9.6)); add('A-SLAB', flat(SC.ann(R_BR0, R_BR1), 9.25, 9.6))
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
    # cores: enclosure walls from GF to the top of each core (C1 to L1 + 3.6, C2 to the tank room under the roof)
    for c in CORES.values():
        if c['key'] == 'S3': continue
        ztop = 9.25 if not c['to_l2'] else 15.0
        enc = c['stair_wall'].difference(c['stair'])
        if c['lift']: enc = enc.union(c['shaft_wall'].difference(c['shaft']))
        dcut = []
        for dd in M.CORE_DOORS:
            if dd['key'].split('-')[0] != c['key']: continue
            t = tdir(c['bc']) if dd['axis'] == 'v' else d(c['bc'])
            p = np.array(dd['p']); dcut.append((dd['fl'], LineString([p - t * dd['w'] / 2, p + t * dd['w'] / 2]).buffer(0.32, cap_style=2)))
        levels = [0.9, 5.4, 9.6, ztop] if c['to_l2'] else [0.9, 5.4, ztop]
        fls = ['GF', 'L1', 'L2']
        for i in range(len(levels) - 1):
            za, zb = levels[i], levels[i + 1]
            cut = unary_union([g for f, g in dcut if f == fls[i]]) if any(f == fls[i] for f, _ in dcut) else Polygon()
            add('A-CORE', flat(enc.difference(cut), za, zb))
            add('A-CORE', flat(cut.intersection(enc.buffer(0.05)), za + 2.4, zb))
        roof = unary_union([c['stair_wall']] + ([c['shaft_wall']] if c['lift'] else []))
        add('A-CORE', flat(roof, ztop, ztop + 0.25))
        stairs(c, L)
    s4_stair(L)
    # ---- columns
    for c in M.COLS:
        z0 = SE.ground_z(c['p']) if c['ring'] != 'A' else 0.9
        top = c['top'] if c['ring'] != 'A' else SE.funnel_top(R_BR0) - 0.28
        add('A-COLS', cyl(c['p'], 0.175, z0 - 0.3, top + 0.05))
    # ---- roof petals (wave), fascia band, funnel, mast
    add('A-ROOF', draped(SE.ROOF_FP, lambda x, y: SE.roof_top((x, y)), lambda x, y: SE.roof_under((x, y)), cell=(1.5, 2.0)))
    edge = SC.ann(M.R_ROOF - 0.08, M.R_ROOF + 0.02).difference(SC.RF_VOID)
    add('A-FASCIA', draped(edge, lambda x, y: SE.roof_top((x, y)) + 0.02, lambda x, y: SE.roof_top((x, y)) - 0.32, cell=(1.0, 1.0)))
    fun = SE.FUNNEL_FP
    add('A-FUNNEL', draped(fun, lambda x, y: SE.funnel_top(plans.rad((x, y))), lambda x, y: SE.funnel_top(plans.rad((x, y))) - 0.28, cell=(5.0, 1.0)))
    add('A-MAST', cone(C, 0.42, 0.1, 0.9, SC.LV['mast']))
    s = trimesh.creation.icosphere(subdivisions=2, radius=0.25); s.apply_translation((C[0], C[1], SC.LV['mast'] + 0.25)); add('A-MAST', [s])
    # ---- facade fins (option A) + deck balustrades
    for bb, ang, top in SC.FINS:
        p = P(R_L1, bb); tn = np.array([math.cos(math.radians(bb)), -math.sin(math.radians(bb))])
        a = math.radians(ang); fd = d(bb) * math.sin(a) + tn * math.cos(a); nn = np.array([-fd[1], fd[0]])
        q0, q1 = p, p + fd * SC.FIN_D
        add('A-FIN', boxy([q0 - nn * 0.03, q1 - nn * 0.03, q1 + nn * 0.03, q0 + nn * 0.03], 5.4, top))
    for fl, z in (('L1', 5.4), ('L2', 9.6)):
        add('A-BALU', flat(SC.ann(R_BR0, R_BR0 + 0.03), z, z + 1.1))
        rooms_fp = unary_union([r['poly'] for r in plans.rooms(fl)]).buffer(0.15)
        for g in _polys(M.PLATE[fl]):
            ring = LineString(g.exterior.coords).difference(rooms_fp)
            for ln in getattr(ring, 'geoms', [ring]):
                if ln.length > 0.3: add('A-BALU', flat(ln.buffer(0.015, cap_style=2).intersection(g.buffer(0.02)), z, z + 1.1))
    # ---- utility block, trees
    add('A-UTIL', flat(ST.UB, 0.0, 4.5))
    for i, nt in ((ST.S_ROAD, 9), (ST.E_ROAD, 6), (0, 6)):
        a, b, t, _ = ST.edge(i); Ln = np.linalg.norm(b - a)
        for k in range(nt):
            p = a + t * Ln * (k + 0.5) / nt + ST.inward(i) * 2.0
            if any(g.buffer(1.5).contains(Point(p)) for g in [ST.AISLE, ST.YARD, ST.HS_S, ST.UB] + [g for _, g in ST.forecourts()] + [g for _, g in ST.PARK]): continue
            add('SITE-TRUNK', cyl(p, 0.15, 0.0, 3.2, 8))
            s = trimesh.creation.icosphere(subdivisions=1, radius=2.4); s.apply_scale((1, 1, 0.8)); s.apply_translation((p[0], p[1], 5.0)); add('SITE-TREE', [s])
    # ---- court tables (brief B3) as simple discs
    for q in plans.court_tables(): add('A-FURN', cyl(q, 0.6, 1.62, 1.66, 20) + cyl(q, 0.05, 0.9, 1.62, 6))
    return {k: trimesh.util.concatenate(v) for k, v in L.items() if v}

def stairs(c, L):
    """switchback flights as solid steps + landings, matching the plan (13 + 13 risers GF-L1, 12 + 12 L1-L2)"""
    bc, sw, W = c['bc'], c['sw'], c['W']; f = lambda u, v: frame(bc, u, v)
    ta = c['v_s0'] + sw; tb = c['v_s1'] - sw
    runs = [(0.9, 5.4, 26)] + ([(5.4, 9.6, 24)] if c['to_l2'] else [])
    for z0, z1, n in runs:
        h = (z1 - z0) / n; half = n // 2; g = (tb - ta) / (half - 1) if half > 1 else M.GO
        g = min(g, M.GO)
        for i in range(half):                                            # flight A goes out (v increasing) on the u<0 side
            v = ta + i * g; z = z0 + h * (i + 1)
            L['A-STRS'] += boxy([f(-W / 2 + 0.1, v), f(-0.1, v), f(-0.1, v + g), f(-W / 2 + 0.1, v + g)], z - 0.25, z)
        zl = z0 + h * half
        L['A-STRS'] += boxy([f(-W / 2 + 0.1, tb), f(W / 2 - 0.1, tb), f(W / 2 - 0.1, c['v_s1'] - 0.1), f(-W / 2 + 0.1, c['v_s1'] - 0.1)], zl - 0.25, zl)
        for i in range(n - half):                                        # flight B comes back on the u>0 side
            v = tb - (i + 1) * g; z = zl + h * (i + 1)
            L['A-STRS'] += boxy([f(0.1, v), f(W / 2 - 0.1, v), f(W / 2 - 0.1, v + g), f(0.1, v + g)], z - 0.25, z)
        L['A-STRS'] += boxy([f(-W / 2 + 0.1, c['v_s0'] + 0.1), f(W / 2 - 0.1, c['v_s0'] + 0.1), f(W / 2 - 0.1, ta), f(-W / 2 + 0.1, ta)], z1 - 0.25, z1)
    if c['key'] == 'S3':                                                  # open stair: glass balustrades
        for u in (-W / 2, W / 2):
            L['A-BALU'] += boxy([f(u - 0.015, c['v_s0']), f(u + 0.015, c['v_s0']), f(u + 0.015, c['v_s1']), f(u - 0.015, c['v_s1'])], 0.9, 10.7 if c['to_l2'] else 6.5)

def s4_stair(L):
    f = lambda u, v: frame(S4['bc'], u, v); w = S4['w']; h = 4.5 / 26; v = S4['v0']; z = 5.4
    for i in range(13):
        L['A-STRS'] += boxy([f(-w / 2, v), f(w / 2, v), f(w / 2, v + M.GO), f(-w / 2, v + M.GO)], z - h - 0.25, z - h); v += M.GO; z -= h
    L['A-STRS'] += boxy([f(-w / 2, v), f(w / 2, v), f(w / 2, v + S4['land']), f(-w / 2, v + S4['land'])], z - 0.3, z); v += S4['land']
    for i in range(13):
        L['A-STRS'] += boxy([f(-w / 2, v), f(w / 2, v), f(w / 2, v + M.GO), f(-w / 2, v + M.GO)], z - h - 0.25, z - h); v += M.GO; z -= h
    for u in (-w / 2, w / 2):
        L['A-BALU'] += boxy([f(u - 0.015, S4['v0']), f(u + 0.015, S4['v0']), f(u + 0.015, S4['v1']), f(u - 0.015, S4['v1'])], 1.0, 6.5)

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
