"""Render model of Titik Temu v3.1 on its site: the v3 model (model3d + interior3d) re-dressed with real materials and textures,
proper furniture, people, trees and cars as COMPONENTS (instanced), limited to the site (lot + tennis-court land) and the edge of the
two roads beside it.
Outputs (out/render/):
  titik-temu-render.glb   for the Blender renders (site metres, Y-up glTF; Blender's importer turns it back to Z-up site metres)
  dae/titik-temu.dae + dae/textures/*   for SketchUp (File > Import > COLLADA). Metres, Z up, the same site coordinates as the DXFs.
python3 render_model.py"""
import os, math, json, shutil
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union
import plan3 as M
from plan3 import C, P, d, tdir, SC, ROOMS, FFL, CORES
import rings as RG
import landscape as LS
import siteplan as ST
import sections as SE
import interior as IN
import interior3d as I3
import model3d as M3

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'render'); TEXD = os.path.join(OUT, 'textures')
TILE = json.load(open(os.path.join(TEXD, 'tiles.json')))

# ------------------------------------------------------------------------------------------------ materials
# key -> dict(color, tex, tile, alpha, metal, rough, emit)  (tile in metres; tex None = plain colour)
def MATL(color, tex=None, tile=None, alpha=1.0, metal=0.0, rough=0.6, glass=False):
    return dict(color=color, tex=tex, tile=tile if tile is not None else (TILE.get(tex.split('.')[0], 1.0) if tex else 1.0), alpha=alpha, metal=metal, rough=rough, glass=glass)
MATS = {
    'Grass': MATL('#7FA24E', 'grass.jpg', rough=0.95), 'Paving': MATL('#CFC9BE', 'pavers.jpg', rough=0.8), 'Paving-Dark': MATL('#B9B3A7', 'pavers_dark.jpg', rough=0.8),
    'Asphalt': MATL('#3A3C40', 'asphalt.jpg', rough=0.9), 'Road-Marking': MATL('#F2F2EE', rough=0.7), 'Kerb': MATL('#BDB8AE', 'concrete.jpg', rough=0.85),
    'Plinth': MATL('#C9C2B4', 'plinth.jpg', rough=0.85), 'Terrazzo': MATL('#C9C6C0', 'terrazzo.jpg', rough=0.35), 'Terrazzo-Light': MATL('#E3E0DA', 'terrazzo_light.jpg', rough=0.35),
    'Water': MATL('#3E8DB3', 'water.jpg', alpha=0.75, rough=0.05, glass=True),
    'GRC-White': MATL('#ECEAE5', 'grc.jpg', rough=0.55), 'Plaster-White': MATL('#F4F2EE', 'plaster.jpg', rough=0.7), 'Roof-Panel': MATL('#E8EAEC', 'roof.jpg', rough=0.35, metal=0.3),
    'Glass': MATL('#9CC5D6', alpha=0.28, rough=0.03, glass=True), 'Glass-Balustrade': MATL('#B9DAE6', alpha=0.18, rough=0.03, glass=True),
    'Glass-Opal': MATL('#EEF4F6', alpha=0.7, rough=0.3, glass=True),
    'Bronze-Anodised': MATL('#2E2724', metal=0.55, rough=0.45), 'Fin-Bronze': MATL('#8F7E62', 'fin.jpg', metal=0.6, rough=0.4),
    'Stainless': MATL('#C9CED3', metal=1.0, rough=0.25), 'Brass': MATL('#B08D3C', metal=1.0, rough=0.25), 'Steel-Dark': MATL('#4A4D52', metal=0.8, rough=0.4),
    'Timber': MATL('#9C6B3F', 'timber.jpg', rough=0.55), 'Timber-Light': MATL('#B98A5E', 'timber_light.jpg', rough=0.55),
    'Solid-Surface': MATL('#F1EEE8', rough=0.3), 'Concrete': MATL('#D4D0C8', 'concrete.jpg', rough=0.85),
    'Soil': MATL('#5E4A36', 'soil.jpg', rough=1.0), 'Shrub': MATL('#4A7A36', 'shrub.jpg', rough=0.9), 'Leaves': MATL('#5B8A3C', 'leaves.jpg', rough=0.85),
    'Leaves-Pink': MATL('#8DA453', 'leaves_pink.jpg', rough=0.85), 'Bark': MATL('#6E5A46', rough=0.95), 'Rubber-Play': MATL('#6FAE8C', rough=0.9),
    'Tactile-Yellow': MATL('#E3B505', rough=0.6), 'Tenun-Lining': MATL('#CBB98C', 'tenun.png', alpha=1.0, metal=0.5, rough=0.4), 'Ceiling-Baffle': MATL('#F7F7F5', rough=0.5),
    'River-Dark': MATL('#4F98BE', rough=0.35), 'River-Light': MATL('#9CCDE3', rough=0.35), 'Stall-Fabric': MATL('#F6EBD2', 'stall.jpg', rough=0.9),
    'Champagne': MATL('#D8C38A', metal=0.6, rough=0.35), 'Gallery-Lilac': MATL('#B9ACE0', rough=0.6), 'Anyaman': MATL('#D8C69C', 'timber_light.jpg', rough=0.7),
    'Mast': MATL('#E6E1D4', metal=0.4, rough=0.35), 'Car-White': MATL('#EDEDED', metal=0.5, rough=0.25), 'Car-Grey': MATL('#7C8085', metal=0.6, rough=0.25),
    'Car-Red': MATL('#A3262A', metal=0.5, rough=0.25), 'Car-Glass': MATL('#1F2A30', alpha=0.85, rough=0.05, glass=True), 'Tyre': MATL('#202022', rough=0.9),
    'Chair-Seat': MATL('#B98A5E', 'timber_light.jpg', rough=0.5), 'Upholstery-Teal': MATL('#2E7D74', rough=0.9), 'Upholstery-Grey': MATL('#5E6368', rough=0.9),
}
for k, v in IN.ST.items():
    MATS[f'State-{k}'] = MATL(v[4], rough=0.5)
    if k in IN.SHOP.values():
        MATS[f'Screen-{k}'] = MATL(v[4], f'screen_{k}.jpg', tile=tuple(TILE[f'screen_{k}']), rough=0.45, metal=0.3)
        MATS[f'Backwall-{k}'] = MATL(v[4], f'back_{k}.jpg', tile=tuple(TILE[f'back_{k}']), rough=0.55)
SKIN = ['#C68E6B', '#A8714F', '#E0B08F', '#8A5A3C']
CLOTH = ['#F2F2EE', '#1F2A44', '#C4572E', '#2E7D74', '#D9A1B8', '#E8C76A', '#6B4E9B', '#3A3A3A', '#9BB7D4', '#7A9A4A', '#B83A2E', '#D8CBB3']
for i, c in enumerate(SKIN): MATS[f'Skin-{i}'] = MATL(c, rough=0.6)
for i, c in enumerate(CLOTH): MATS[f'Cloth-{i}'] = MATL(c, rough=0.85)
MATS['Hair'] = MATL('#1C1714', rough=0.7); MATS['Shoe'] = MATL('#2A2420', rough=0.6)
for i, c in enumerate(['#C0392B', '#E8B523', '#2E7D74', '#E46F8C', '#8C5A2B', '#F2F2EE', '#4E8F3A']): MATS[f'Product-{i}'] = MATL(c, rough=0.4)

LAYER_MAT = {
    'SITE-LAWN': 'Grass', 'SITE-PAVING': 'Paving', 'SITE-ROAD': 'Asphalt', 'SITE-PLINTH': 'Plinth', 'SITE-WATER': 'Water',
    'A-SLAB': 'Terrazzo-Light', 'A-BRIDGE': 'Terrazzo-Light', 'A-WALL': 'Plaster-White', 'A-CORE': 'GRC-White', 'A-GLAZ': 'Glass',
    'A-ROOFLIGHT': 'Glass-Opal', 'A-CLERESTORY': 'Glass', 'A-ROOF-MID': 'Roof-Panel', 'A-COLS': 'GRC-White', 'A-STRS': 'Terrazzo-Light',
    'A-BALU': 'Glass-Balustrade', 'A-ROOF': 'Roof-Panel', 'A-FUNNEL': 'Roof-Panel', 'A-MAST': 'Mast', 'A-FIN': 'Fin-Bronze', 'A-FASCIA': 'Bronze-Anodised',
    'A-UTIL': 'Concrete', 'A-FURN': 'Timber-Light', 'L-CANP-RIB': 'Timber', 'L-CANP-PANEL': 'Anyaman', 'L-CANP-GLASS': 'Glass', 'L-CANP-COL': 'Steel-Dark',
    'L-PLANTER': 'GRC-White', 'L-SOIL': 'Soil', 'L-PLANT': 'Shrub', 'L-PLAY': 'Rubber-Play',
    'I-FURN': 'Solid-Surface', 'I-FURN-TIMBER': 'Timber', 'I-KIT': 'Stainless', 'I-FASCIA': 'Bronze-Anodised', 'I-BRASS': 'Brass', 'I-SIGN': 'Bronze-Anodised',
    'I-TACTILE': 'Tactile-Yellow', 'I-CEIL': 'Ceiling-Baffle', 'I-TENUN': 'Tenun-Lining', 'I-RIVER': 'River-Dark', 'I-RIVER2': 'River-Light',
    'I-MARKET': 'Stall-Fabric', 'I-PRAYER': 'Champagne', 'I-GALLERY': 'Gallery-Lilac', 'I-STEEL': 'Stainless',
    'FLOOR-TERRAZZO': 'Terrazzo', 'ROAD-MARK': 'Road-Marking', 'KERB': 'Kerb', 'GROUND': 'Grass', 'SIGN-LETTERS': 'Stainless',
}
for k in IN.ST:
    LAYER_MAT[f'I-STATE-{k}'] = f'State-{k}'; LAYER_MAT[f'I-SCREEN-{k}'] = f'Screen-{k}'; LAYER_MAT[f'I-BACK-{k}'] = f'Backwall-{k}'
DROP = {'SITE-TREE', 'SITE-TRUNK'}                     # replaced by tree components

# ------------------------------------------------------------------------------------------------ helpers
def _m(mesh, mat): return (mesh, mat)
def cyl(r, z0, z1, n=12, xy=(0, 0)):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n); m.apply_translation((xy[0], xy[1], (z0 + z1) / 2)); return m
def bx(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0)); m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)); return m
def rod(p0, p1, r, n=8):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=n)
def capsule(p0, p1, r, n=10):
    p0, p1 = np.array(p0, float), np.array(p1, float); L_ = np.linalg.norm(p1 - p0)
    m = trimesh.creation.capsule(height=max(L_, 1e-3), radius=r, count=[n, n // 2 + 2])
    z = np.array([0, 0, 1.0]); v = (p1 - p0) / max(L_, 1e-9)
    R = trimesh.geometry.align_vectors(z, v); m.apply_transform(R); m.apply_translation((p0 + p1) / 2); return m
def ellipsoid(c, s, sub=2):
    m = trimesh.creation.icosphere(subdivisions=sub, radius=1.0); m.apply_scale(s); m.apply_translation(c); return m
def rotz(th):
    c, s = math.cos(th), math.sin(th); T = np.eye(4); T[:2, :2] = [[c, -s], [s, c]]; return T
def place(p, z, h=(0, 1), scale=1.0):
    """matrix: local +y faces heading h, origin at (p, z)"""
    th = math.atan2(-h[0], h[1]); T = rotz(th); T[:3, :3] *= scale; T[:3, 3] = (p[0], p[1], z); return T

# ------------------------------------------------------------------------------------------------ component library (local: x right, y forward, z up)
def comp_chair():
    parts = [_m(bx(-0.21, -0.21, 0.42, 0.21, 0.21, 0.46), 'Chair-Seat'), _m(bx(-0.21, -0.23, 0.48, 0.21, -0.2, 0.86), 'Chair-Seat')]
    for x in (-0.18, 0.18):
        for y in (-0.18, 0.18): parts.append(_m(cyl(0.013, 0, 0.42, 6, (x, y)), 'Steel-Dark'))
    return parts
def comp_chair_office():
    p = [_m(bx(-0.24, -0.22, 0.44, 0.24, 0.24, 0.52), 'Upholstery-Grey'), _m(bx(-0.22, -0.28, 0.58, 0.22, -0.22, 1.05), 'Upholstery-Grey'), _m(cyl(0.025, 0.08, 0.44, 8), 'Stainless')]
    for k in range(5):
        a = k * 2 * math.pi / 5; p.append(_m(rod((0, 0, 0.07), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.04), 0.015, 6), 'Steel-Dark'))
    return p
def comp_stool_bar():
    ring = trimesh.creation.annulus(r_min=0.15, r_max=0.17, height=0.02, sections=16); ring.apply_translation((0, 0, 0.3))
    return [_m(cyl(0.18, 0.72, 0.76, 16), 'Timber-Light'), _m(cyl(0.025, 0.02, 0.72, 8), 'Stainless'), _m(cyl(0.2, 0.0, 0.02, 16), 'Stainless'), _m(ring, 'Stainless')]
def comp_stool_low():
    return [_m(cyl(0.16, 0.32, 0.36, 14), 'Stainless'), _m(cyl(0.03, 0.0, 0.32, 8), 'Stainless')]
def comp_table_cafe():
    return [_m(cyl(0.35, 0.72, 0.75, 24), 'Terrazzo-Light'), _m(cyl(0.04, 0.03, 0.72, 8), 'Steel-Dark'), _m(cyl(0.25, 0.0, 0.03, 16), 'Steel-Dark')]
def comp_jar():
    return [_m(cyl(0.05, 0.0, 0.16, 10), 'Glass'), _m(cyl(0.042, 0.005, 0.12, 8), 'Product-0'), _m(cyl(0.052, 0.16, 0.19, 10), 'Brass')]
def comp_pack():
    return [_m(bx(-0.06, -0.03, 0.0, 0.06, 0.03, 0.18), 'Product-1')]

def person(kind, skin, top, bottom, H=1.68, walk=0.0, tudung=None, arms_swing=0.0):
    """stylised but proportioned figure: kind 'm' (shirt + trousers), 'f' (baju kurung + tudung), 'c' (child)"""
    h = H; parts = []; sw = walk
    hip = 0.52 * h; sh = 0.815 * h
    if kind == 'f':
        dress = trimesh.creation.cone(radius=0.17 * h, height=0.62 * h, sections=16); dress.apply_scale((1.0, 0.85, 1.0)); dress.apply_translation((0, 0, 0.03 * h))
        parts.append(_m(dress, bottom))
        for sx in (-0.05, 0.05): parts.append(_m(ellipsoid((sx * h, 0.04 * h * (1 if sx > 0 else -1) * sw, 0.03 * h), (0.035 * h, 0.07 * h, 0.03 * h), 1), 'Shoe'))
    else:
        for sx, sg in ((-0.055, 1), (0.055, -1)):
            ft = (sx * h, 0.18 * h * sw * sg, 0.045 * h)
            parts.append(_m(capsule((sx * h, 0, hip), ft, 0.058 * h, 8), bottom))
            parts.append(_m(ellipsoid((ft[0], ft[1] + 0.03 * h, 0.025 * h), (0.04 * h, 0.075 * h, 0.03 * h), 1), 'Shoe'))
    parts.append(_m(ellipsoid((0, 0, 0.69 * h), (0.125 * h, 0.075 * h, 0.17 * h), 2), top))                   # torso
    parts.append(_m(ellipsoid((0, 0, 0.535 * h), (0.11 * h, 0.07 * h, 0.07 * h), 1), top if kind == 'f' else bottom))
    for sx, sg in ((-0.135, -1), (0.135, 1)):
        hand = (sx * h * 1.05, 0.12 * h * arms_swing * sg, 0.47 * h)
        parts.append(_m(capsule((sx * h, 0, sh - 0.03 * h), hand, 0.036 * h, 8), top))
        parts.append(_m(ellipsoid(hand, (0.03 * h, 0.03 * h, 0.04 * h), 1), skin))
    parts.append(_m(cyl(0.035 * h, 0.84 * h, 0.89 * h, 10), skin))
    parts.append(_m(ellipsoid((0, 0.005 * h, 0.935 * h), (0.062 * h, 0.07 * h, 0.075 * h), 2), skin))
    if tudung:
        parts.append(_m(ellipsoid((0, -0.008 * h, 0.94 * h), (0.072 * h, 0.08 * h, 0.085 * h), 2).slice_plane((0, 0.05 * h, 0.9 * h), (0, -1, 0.35)), tudung))
        cape = trimesh.creation.cone(radius=0.15 * h, height=0.15 * h, sections=14); cape.apply_scale((1, 0.8, 1)); cape.apply_translation((0, -0.01 * h, 0.79 * h)); parts.append(_m(cape, tudung))
    else:
        hair = ellipsoid((0, -0.012 * h, 0.95 * h), (0.066 * h, 0.072 * h, 0.07 * h), 2).slice_plane((0, 0.02 * h, 0.93 * h), (0, -1, 0.6))
        parts.append(_m(hair, 'Hair'))
    return parts

def comp_tree(scale=1.0, mat='Leaves', seed=0, n=9):
    r = np.random.default_rng(seed); s = scale; parts = []
    trunk = trimesh.creation.cone(radius=0.32 * s, height=4.2 * s, sections=10); parts.append(_m(trunk, 'Bark'))
    blobs = []
    for i in range(n):
        a = i * 2 * math.pi / n + r.uniform(-0.3, 0.3); rr = r.uniform(1.4, 2.9) * s
        top = (rr * math.cos(a), rr * math.sin(a), r.uniform(5.2, 6.6) * s)
        parts.append(_m(rod((0, 0, 3.0 * s), top, 0.09 * s, 6), 'Bark'))
        e = ellipsoid(top, (r.uniform(1.5, 2.2) * s, r.uniform(1.5, 2.2) * s, r.uniform(0.9, 1.3) * s), 2)
        e.vertices += r.normal(0, 0.09 * s, e.vertices.shape); blobs.append(e)
    e = ellipsoid((0, 0, 6.9 * s), (2.2 * s, 2.2 * s, 1.2 * s), 2); e.vertices += r.normal(0, 0.1 * s, e.vertices.shape); blobs.append(e)
    parts.append(_m(trimesh.util.concatenate(blobs), mat))
    return parts

def comp_car(body):
    p = [_m(bx(-0.88, -2.25, 0.3, 0.88, 2.25, 0.95), body), _m(bx(-0.78, -1.15, 0.95, 0.78, 0.95, 1.42), 'Car-Glass'), _m(bx(-0.8, -1.05, 1.42, 0.8, 0.85, 1.46), body)]
    for x in (-0.82, 0.82):
        for y in (-1.45, 1.45):
            w = trimesh.creation.cylinder(radius=0.33, height=0.22, sections=14); w.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (0, 1, 0))); w.apply_translation((x, y, 0.33)); p.append(_m(w, 'Tyre'))
    return p

def library():
    L = {'chair': comp_chair(), 'chair_office': comp_chair_office(), 'stool_bar': comp_stool_bar(), 'stool_low': comp_stool_low(), 'table_cafe': comp_table_cafe(),
         'jar': comp_jar(), 'pack': comp_pack(), 'tree_rain': comp_tree(1.0, 'Leaves', 1), 'tree_rain2': comp_tree(0.85, 'Leaves', 5, 8), 'tree_pink': comp_tree(0.62, 'Leaves-Pink', 3, 7),
         'car_white': comp_car('Car-White'), 'car_grey': comp_car('Car-Grey'), 'car_red': comp_car('Car-Red')}
    P_ = [('m', 0, 'Cloth-0', 'Cloth-1', 1.72, 0.9, None, 0.8), ('m', 1, 'Cloth-2', 'Cloth-11', 1.68, 0.0, None, 0.1), ('f', 2, 'Cloth-4', 'Cloth-4', 1.6, 0.6, 'Cloth-11', 0.5),
          ('f', 0, 'Cloth-3', 'Cloth-3', 1.62, 0.0, 'Cloth-5', 0.0), ('f', 1, 'Cloth-0', 'Cloth-1', 1.58, 0.7, 'Cloth-7', 0.6), ('m', 3, 'Cloth-8', 'Cloth-7', 1.75, 0.8, None, 0.7),
          ('m', 2, 'Cloth-10', 'Cloth-1', 1.7, 0.0, None, 0.05), ('c', 0, 'Cloth-5', 'Cloth-8', 1.15, 0.7, None, 0.6), ('f', 3, 'Cloth-6', 'Cloth-6', 1.57, 0.5, 'Cloth-0', 0.5),
          ('m', 1, 'Cloth-9', 'Cloth-11', 1.66, 0.6, None, 0.6)]
    for i, (k, sk, top, bot, H, w, tu, ar) in enumerate(P_):
        L[f'person_{i}'] = person('m' if k == 'c' else k, f'Skin-{sk}', top, bot, H, w, tu, ar)
    return L

# ------------------------------------------------------------------------------------------------ placements
def ground(x, y): return SE.ground_z((x, y))
def trees():
    out = []
    for i, nt in ((ST.S_ROAD, 9), (ST.E_ROAD, 6), (0, 6)):
        a, b, t, _ = ST.edge(i); Ln = np.linalg.norm(b - a)
        for k in range(nt):
            p = a + t * Ln * (k + 0.5) / nt + ST.inward(i) * 2.0
            if any(g.buffer(1.5).contains(Point(p)) for g in [ST.AISLE, ST.YARD, ST.HS_S, ST.UB, LS.CANOPY_FP] + [g for _, g in ST.forecourts()] + [g for _, g in ST.PARK] + ST.OUTER): continue
            out.append(('tree_rain' if k % 2 == 0 else 'tree_rain2', place(p, 0.0, (math.cos(k), math.sin(k)))))
    for j, p in enumerate(ST.POCKET_TREES): out.append(('tree_pink', place(p, 0.3, (math.sin(j), math.cos(j)))))
    return out

def cars():
    out = []; kinds = ['car_white', 'car_grey', 'car_red', 'car_white']
    for i, (k, g) in enumerate([q for q in ST.PARK if q[0] == 'S'][:4]):
        cs = np.array(g.minimum_rotated_rectangle.exterior.coords)[:4]; e1 = cs[1] - cs[0]; e2 = cs[2] - cs[1]
        ax = e1 if np.linalg.norm(e1) > np.linalg.norm(e2) else e2
        c = np.array(g.centroid.coords[0]); out.append((kinds[i], place(c, ground(*c) + 0.02, ax)))
    return out

def people():
    """people on the walkable areas: court, arcade, gates, forecourts, bridge, L1 decks, L2 walk"""
    r = np.random.default_rng(42); out = []
    rooms = {fl: unary_union([q['poly'] for q in ROOMS if q['fl'] == fl] + [c['fp'] for c in CORES.values()]).buffer(0.4) for fl in ('GF', 'L1', 'L2')}
    furn = unary_union([LS.ann_sec(4.2, 6.6, a_, b_) for a_, b_ in LS.TABLES] + [LS.ann_sec(7.8, 9.35, a_, b_) for a_, b_ in LS.INNER] + [SC.disc(M.R_POOL + 0.6)]).buffer(0.25)
    cols = unary_union([Point(c['p']).buffer(c['r'] + 0.35) for c in M.COLS])
    fc = unary_union([g for _, g in ST.forecourts()])
    zones = [  # (polygon, z, count, tangential walk?)
        (SC.ann(3.2, 9.2).difference(furn), 0.9, 22, False),
        (SC.ann(9.7, 12.3).difference(cols), 0.9, 16, True),
        (unary_union([SC.strip(s['b'], s['w'] - 1.5, 12.8, 24.0) for s in SC.SPINES]).difference(rooms['GF']).difference(cols), 0.9, 10, False),
        (fc.difference(SC.disc(M.R_GF + 0.5)), None, 16, False),
        (SC.ann(17.3, 19.7).difference(cols), 5.4, 12, True),
        (unary_union([q for q in M.decks('L1')]).difference(rooms['L1']).difference(cols), 5.4, 12, False),
        (M.WALK.difference(cols), 9.6, 5, True)]
    for zi, (poly, z, n, tang) in enumerate(zones):
        if poly.is_empty: continue
        b = poly.bounds; got, tries = 0, 0
        while got < n and tries < 4000:
            tries += 1; p = np.array([r.uniform(b[0], b[2]), r.uniform(b[1], b[3])])
            if not poly.contains(Point(p)) or any(np.linalg.norm(p - np.array(q[2])) < 1.1 for q in out): continue
            if tang: h = tdir(M.brg(p)) * (1 if r.random() < 0.5 else -1)
            else: a = r.uniform(0, 2 * math.pi); h = np.array([math.cos(a), math.sin(a)])
            k = int(r.integers(0, 10)); zz = z if z is not None else ground(*p)
            out.append((f'person_{k}', place(p, zz, h), tuple(p))); got += 1
    return [(k, T) for k, T, _ in out]

def seats():
    return [(k, place(p, z, h)) for k, p, h, z in I3.SEATS]

# ------------------------------------------------------------------------------------------------ extra geometry: floors, road markings, kerbs, sign letters
def letters(text, height, font_path='/usr/share/fonts/opentype/inter/Inter-Bold.otf'):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), text, size=1.0, prop=FontProperties(fname=font_path))
    polys = [Polygon(p) for p in tp.to_polygons() if len(p) > 2]
    g = Polygon()
    for q in sorted(polys, key=lambda q: -q.area): g = g.symmetric_difference(q.buffer(0))
    b = g.bounds; s = height / (b[3] - b[1] if b[3] > b[1] else 1)
    from shapely import affinity
    return affinity.scale(affinity.translate(g, -(b[0] + b[2]) / 2, -b[1]), s, s, origin=(0, 0))

def extras():
    E = {}
    add = lambda k, ms: E.setdefault(k, []).extend(ms)
    # terrazzo floor skin on the plinth inside the building line (court, arcade, gates, rooms), the pool stays
    fl = SC.disc(M.R_GF + 0.02).difference(SC.disc(M.R_POOL + 0.2))
    add('FLOOR-TERRAZZO', M3.flat(fl, 0.9, 0.905))
    # grass beyond the site edge (only a narrow apron, so the model stays on the site) - the roads come from model3d
    apron = SC.SITE.buffer(4.0).difference(SC.SITE)
    add('GROUND', M3.flat(apron, -0.32, -0.05))
    # road centre line + kerb on the two roads
    for i, w in ((ST.S_ROAD, 12.0), (ST.E_ROAD, 10.0)):
        a, b, t, n = ST.edge(i); no = -ST.inward(i)
        add('KERB', M3.flat(Polygon([a - t * 12, b + t * 12, b + t * 12 + no * 0.25, a - t * 12 + no * 0.25]).difference(SC.SITE), -0.15, 0.0))
        c0, c1 = a - t * 12 + no * w / 2, b + t * 12 + no * w / 2; L_ = np.linalg.norm(c1 - c0); u = (c1 - c0) / L_
        for s in np.arange(0, L_ - 3, 6.0):
            add('ROAD-MARK', M3.flat(LineString([c0 + u * s, c0 + u * (s + 3.0)]).buffer(0.075, cap_style=2), -0.15, -0.14))
    # gate names in stainless letters on the gate markers (street face), 'TITIK TEMU' over the Selatan marker
    for s in SC.SPINES:
        cn = [k for k in LS.CANOPIES if abs(k['b'] - s['b']) < 1][0]
        Rm = min(cn['R_out'], 29.0) - 0.4; zt = LS.z_top(cn, Rm, 0.0)
        line2 = ('TITIK TEMU', zt - 0.62, 0.2) if s['k'] == 'SELATAN' else ('PINTU ' + s['k'], zt - 0.6, 0.15)
        for txt, zc, hh in ((s['k'], zt - 1.08, 0.4), line2):
            g = letters(txt, hh)
            if g.bounds[2] - g.bounds[0] > 5.6:
                from shapely import affinity; k_ = 5.6 / (g.bounds[2] - g.bounds[0]); g = affinity.scale(g, k_, k_, origin=(0, 0))
            for q in getattr(g, 'geoms', [g]):
                try: m = trimesh.creation.extrude_polygon(q, 0.03)
                except Exception: continue
                # local (x along the marker, y up) -> world: x -> -tdir (reads left-to-right from the street), y -> z, extrusion -> outward d(b)
                b = s['b']; ex = -tdir(b); out_ = d(b); base = P(Rm + 0.055, b)
                T = np.eye(4); T[:3, 0] = (ex[0], ex[1], 0); T[:3, 1] = (0, 0, 1); T[:3, 2] = (out_[0], out_[1], 0); T[:3, 3] = (base[0], base[1], zc)
                m.apply_transform(T); add('SIGN-LETTERS', [m])
    return E

# ------------------------------------------------------------------------------------------------ build + UVs
def box_uv(mesh, tile):
    """per-corner box projection: returns (uv array F x 3 x 2)"""
    tu, tv = (tile, tile) if not isinstance(tile, (tuple, list)) else tile
    V = mesh.vertices[mesh.faces]; n = mesh.face_normals; ax = np.argmax(np.abs(n), axis=1)
    uv = np.zeros(V.shape[:2] + (2,))
    m = ax == 2; uv[m] = V[m][..., [0, 1]]
    m = ax == 0; uv[m] = V[m][..., [1, 2]]
    m = ax == 1; uv[m] = V[m][..., [0, 2]]
    uv[..., 0] /= tu; uv[..., 1] /= tv
    return uv

def build(coarse=False):
    if coarse:                                                            # lighter tessellation for the SketchUp file
        _dr, _fl = M3.draped, M3.flat
        def dr(poly, ztop, zbot, cell=None, seg=0.6):
            if cell: cell = (cell[0] * 2.0, cell[1] * 1.6)
            return _dr(poly.simplify(0.03), ztop, zbot, cell, seg * 2)
        def fl(poly, z0, z1): return _fl(poly.simplify(0.02) if hasattr(poly, 'simplify') else poly, z0, z1)
        M3.draped, M3.flat = dr, fl
    I3.RENDER = True; I3.SEATS.clear()
    layers = M3.build()
    if coarse: M3.draped, M3.flat = _dr, _fl
    ex = extras()
    groups = {}
    for k, m in list(layers.items()) + [(k, trimesh.util.concatenate(v)) for k, v in ex.items()]:
        if k in DROP: continue
        mat = LAYER_MAT.get(k)
        if mat is None: print('no material for', k); mat = 'Solid-Surface'
        groups.setdefault(mat, []).append(m)
    groups = {k: trimesh.util.concatenate(v) for k, v in groups.items()}
    inst = trees() + cars() + people() + seats()
    return groups, library(), inst

# ------------------------------------------------------------------------------------------------ GLB (Blender)
def export_glb(groups, lib, inst, path):
    from PIL import Image
    imgs = {}
    def material(key):
        md = MATS[key]; h = md['color'].lstrip('#'); col = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        kw = dict(name=key, metallicFactor=md['metal'], roughnessFactor=md['rough'], doubleSided=True,
                  baseColorFactor=[1, 1, 1, md['alpha']] if md['tex'] else col + [md['alpha']], alphaMode='BLEND' if md['alpha'] < 1 or (md['tex'] or '').endswith('.png') else 'OPAQUE')
        if md['tex']:
            if md['tex'] not in imgs: imgs[md['tex']] = Image.open(os.path.join(TEXD, md['tex']))
            kw['baseColorTexture'] = imgs[md['tex']]
        return trimesh.visual.material.PBRMaterial(**kw)
    def dressed(mesh, key):
        md = MATS[key]; m = mesh.copy()
        if md['tex']:
            uv = box_uv(m, md['tile']); F = len(m.faces)
            m = trimesh.Trimesh(m.vertices[m.faces].reshape(-1, 3), np.arange(F * 3).reshape(-1, 3), process=False)
            m.visual = trimesh.visual.TextureVisuals(uv=uv.reshape(-1, 2), material=material(key))
        else:
            m.visual = trimesh.visual.TextureVisuals(material=material(key))
        return m
    sc = trimesh.Scene()
    Y = trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0))     # z-up site metres -> glTF y-up
    for key, m in groups.items(): sc.add_geometry(dressed(m, key), node_name=f'L_{key}', geom_name=f'L_{key}', transform=Y)
    # components: each part once, then nodes referencing it
    for cname, parts in lib.items():
        for j, (pm, key) in enumerate(parts): sc.geometry[f'C_{cname}_{j}'] = dressed(pm, key)
    for i, (cname, T) in enumerate(inst):
        for j in range(len(lib[cname])):
            sc.graph.update(frame_to=f'I{i}_{cname}_{j}', frame_from=sc.graph.base_frame, matrix=Y @ T, geometry=f'C_{cname}_{j}')
    sc.export(path)

# ------------------------------------------------------------------------------------------------ DAE (SketchUp)
def f3(a): return ' '.join(f'{v:.3f}'.rstrip('0').rstrip('.') if v != 0 else '0' for v in np.asarray(a).ravel())
def f4(a): return ' '.join(f'{v:.4f}'.rstrip('0').rstrip('.') if v != 0 else '0' for v in np.asarray(a).ravel())
def write_dae(groups, lib, inst, path, texdir_rel='textures'):
    """compact COLLADA 1.4: shared positions, separate TEXCOORD index stream, components as library_nodes + instance_node"""
    used_mats = set(groups) | {k for parts in lib.values() for _, k in parts}
    X = ['<?xml version="1.0" encoding="utf-8"?>', '<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">',
         '<asset><contributor><authoring_tool>Titik Temu render_model.py</authoring_tool></contributor><unit name="meter" meter="1"/><up_axis>Z_UP</up_axis></asset>']
    X.append('<library_images>')
    texs = sorted({MATS[k]['tex'] for k in used_mats if MATS[k]['tex']})
    for t in texs: X.append(f'<image id="img_{t.split(".")[0]}"><init_from>{texdir_rel}/{t}</init_from></image>')
    X.append('</library_images><library_effects>')
    for k in sorted(used_mats):
        md = MATS[k]; h = md['color'].lstrip('#'); col = ' '.join(f'{int(h[i:i + 2], 16) / 255:.3f}' for i in (0, 2, 4))
        if md['tex']:
            tid = md['tex'].split('.')[0]
            diff = (f'<newparam sid="s_{tid}"><surface type="2D"><init_from>img_{tid}</init_from></surface></newparam>'
                    f'<newparam sid="sm_{tid}"><sampler2D><source>s_{tid}</source></sampler2D></newparam>', f'<texture texture="sm_{tid}" texcoord="UV"/>')
        else: diff = ('', f'<color>{col} 1</color>')
        tr = f'<transparent opaque="A_ONE"><color>1 1 1 {md["alpha"]:.2f}</color></transparent><transparency><float>1</float></transparency>' if md['alpha'] < 1 else ''
        X.append(f'<effect id="fx_{k}"><profile_COMMON>{diff[0]}<technique sid="common"><lambert><diffuse>{diff[1]}</diffuse>{tr}</lambert></technique></profile_COMMON></effect>')
    X.append('</library_effects><library_materials>')
    for k in sorted(used_mats): X.append(f'<material id="mat_{k}" name="{k}"><instance_effect url="#fx_{k}"/></material>')
    X.append('</library_materials><library_geometries>')
    def geom(gid, mesh, key):
        md = MATS[key]; m = mesh.copy(); m.merge_vertices(digits_vertex=4)
        s = [f'<geometry id="{gid}" name="{gid}"><mesh>', f'<source id="{gid}_p"><float_array id="{gid}_pa" count="{m.vertices.size}">{f3(m.vertices)}</float_array>'
             f'<technique_common><accessor source="#{gid}_pa" count="{len(m.vertices)}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>']
        if md['tex']:
            uv = box_uv(m, md['tile']).reshape(-1, 2); uvr = np.round(uv, 3); uq, inv = np.unique(uvr, axis=0, return_inverse=True)
            s.append(f'<source id="{gid}_t"><float_array id="{gid}_ta" count="{uq.size}">{f4(uq)}</float_array><technique_common><accessor source="#{gid}_ta" count="{len(uq)}" stride="2"><param name="S" type="float"/><param name="T" type="float"/></accessor></technique_common></source>')
            idx = np.stack([m.faces.reshape(-1), inv.reshape(-1)], 1).ravel()
            inputs = f'<input semantic="VERTEX" source="#{gid}_v" offset="0"/><input semantic="TEXCOORD" source="#{gid}_t" offset="1" set="0"/>'
        else:
            idx = m.faces.ravel(); inputs = f'<input semantic="VERTEX" source="#{gid}_v" offset="0"/>'
        s.append(f'<vertices id="{gid}_v"><input semantic="POSITION" source="#{gid}_p"/></vertices>')
        s.append(f'<triangles material="m" count="{len(m.faces)}">{inputs}<p>{" ".join(map(str, idx))}</p></triangles></mesh></geometry>')
        return ''.join(s)
    def inst_geom(gid, key):
        md = MATS[key]; bind = '<bind_vertex_input semantic="UV" input_semantic="TEXCOORD" input_set="0"/>' if md['tex'] else ''
        return f'<instance_geometry url="#{gid}"><bind_material><technique_common><instance_material symbol="m" target="#mat_{key}">{bind}</instance_material></technique_common></bind_material></instance_geometry>'
    for key, m in groups.items(): X.append(geom(f'g_{key}', m, key))
    for cname, parts in lib.items():
        for j, (pm, key) in enumerate(parts): X.append(geom(f'c_{cname}_{j}', pm, key))
    X.append('</library_geometries><library_nodes>')
    for cname, parts in lib.items():
        X.append(f'<node id="comp_{cname}" name="{cname}">' + ''.join(inst_geom(f'c_{cname}_{j}', key) for j, (_, key) in enumerate(parts)) + '</node>')
    X.append('</library_nodes><library_visual_scenes><visual_scene id="scene" name="TitikTemu">')
    TAG = lambda k: ('SITE' if k in ('Grass', 'Paving', 'Paving-Dark', 'Asphalt', 'Road-Marking', 'Kerb', 'Plinth', 'Water', 'Concrete') else
                     'LANDSCAPE' if k in ('Shrub', 'Soil', 'Rubber-Play', 'Anyaman') else 'INTERIOR' if k.startswith(('Screen-', 'Backwall-', 'State-')) else 'BUILDING')
    by = {}
    for key in groups: by.setdefault(TAG(key), []).append(key)
    for tag, keys in by.items():
        X.append(f'<node id="{tag}" name="{tag}">' + ''.join(f'<node id="n_{k}" name="{k}">{inst_geom("g_" + k, k)}</node>' for k in keys) + '</node>')
    cat = lambda c: 'PEOPLE' if c.startswith('person') else 'TREES' if c.startswith('tree') else 'CARS' if c.startswith('car') else 'FURNITURE'
    cats = {}
    for i, (cname, T) in enumerate(inst): cats.setdefault(cat(cname), []).append((i, cname, T))
    for cg, items in cats.items():
        X.append(f'<node id="{cg}" name="{cg}">')
        for i, cname, T in items: X.append(f'<node id="i{i}" name="{cname}"><matrix>{f4(T)}</matrix><instance_node url="#comp_{cname}"/></node>')
        X.append('</node>')
    X.append('</visual_scene></library_visual_scenes><scene><instance_visual_scene url="#scene"/></scene></COLLADA>')
    open(path, 'w').write('\n'.join(X))
    return len(texs)

if __name__ == '__main__':
    import sys, time
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    if 'glb' in sys.argv or len(sys.argv) == 1:
        g, lib, inst = build(coarse=False)
        print('render groups', len(g), 'faces', sum(len(m.faces) for m in g.values()), 'instances', len(inst), round(time.time() - t0), 's')
        export_glb(g, lib, inst, os.path.join(OUT, 'titik-temu-render.glb')); print('glb', os.path.getsize(os.path.join(OUT, 'titik-temu-render.glb')) // 1e6, 'MB')
        json.dump([(c, T.tolist()) for c, T in inst], open(os.path.join(OUT, 'instances.json'), 'w'))
    if 'dae' in sys.argv or len(sys.argv) == 1:
        g, lib, inst = build(coarse=True)
        dd = os.path.join(OUT, 'dae'); os.makedirs(os.path.join(dd, 'textures'), exist_ok=True)
        n = write_dae(g, lib, inst, os.path.join(dd, 'titik-temu.dae'))
        used = {MATS[k]['tex'] for k in set(g) | {k for p in lib.values() for _, k in p} if MATS[k]['tex']}
        for t in used: shutil.copy(os.path.join(TEXD, t), os.path.join(dd, 'textures', t))
        print('dae faces', sum(len(m.faces) for m in g.values()), 'MB', os.path.getsize(os.path.join(dd, 'titik-temu.dae')) / 1e6, 'textures', n, round(time.time() - t0), 's')

# ------------------------------------------------------------------------------------------------ interior lights for the renders (Blender)
def light_list():
    """(x, y, z, size_u, size_v, watts, kelvin-ish rgb, heading) - room ceilings, arcade, shops, court"""
    import sections as SE_
    L = []
    for r in ROOMS:
        if r['kind'] in ('stair', 'lift'): continue
        g = r['poly']; a = g.area; c = g.representative_point()
        z = FFL[r['fl']] + SE_.CEIL[r['fl']] - 0.05
        w = 9.0 * a if r['kind'] != 'shop' else 0.0
        if r['kind'] == 'open' or w <= 0: continue
        L.append((c.x, c.y, z, min(3.0, math.sqrt(a) * 0.5), min(3.0, math.sqrt(a) * 0.5), w, (1.0, 0.86, 0.7), 0.0))
    for k in IN.SHOP:
        bm = M.mid(k)[0]
        for rr, z, w in ((13.9, 4.15, 140), (16.25, 4.6, 120), (18.8, 4.15, 120), (20.6, 4.6, 90)):
            p = P(rr, bm); L.append((p[0], p[1], z, 1.2, 0.6, w, (1.0, 0.84, 0.66), bm))
    for b in range(0, 360, 6):                                                   # arcade ring under the first floor
        p = P(11.0, b); L.append((p[0], p[1], 4.55, 0.25, 2.2, 45, (1.0, 0.85, 0.68), b))
    for b in range(0, 360, 45):                                                  # court: soft light under the tenun lining
        p = P(6.0, b); z = RG.fun_under(p) - 0.4; L.append((p[0], p[1], z, 3.0, 3.0, 380, (1.0, 0.9, 0.78), b))
    for b in range(0, 360, 8):                                                   # bridge handrail LED (both edges) as thin strips
        for rr in (17.08, 19.92):
            p = P(rr, b); L.append((p[0], p[1], 6.38, 0.04, 2.5, 6, (1.0, 0.83, 0.62), b))
    return L

if __name__ == '__main__':
    json.dump(light_list(), open(os.path.join(OUT, 'lights.json'), 'w'))
    print('lights', len(light_list()))
