"""Interior fit-out for the Titik Temu model (Rasa Kompas scheme).
Every item is placed from the real room polygons (net of walls), with a check that it stays inside its room,
clear of door swings, columns and the core. Returns groups per level for explode_build.py."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPoint, box as sbox
from shapely.ops import unary_union, polylabel
import skp_build as K
from skp_build import G, I, D, defn_box, Solids, mat, ZG, ZL, ZSOF, ZL1_TOP, ZCEIL, zdeck, CORE_FP, COLS_BIG, COLS_SMALL
from m3d import prism, box_faces, cyl_faces, mesh_faces, beam, xprism, fix_outward, clean, polys, F
from geom import ROOMS, B, S, d, mod, sector, QIBLA, R_COURT, R_VER, R_OUT, R_L1, RS_COR, RS_OUT, RS_WELL, core1_stair, core1_lifts
from draw import DOORS

R_DISP = 14.75
# ================================================================== materials
for n_, c_, a_ in [('TT Brass inlay', '#C8A050', 1), ('TT Bronze PVD', '#9C7A4C', 1), ('TT Mint glass', '#BFE8DC', 0.45),
                   ('TT GRG white', '#F7F6F3', 1), ('TT Solid surface', '#FAFAF8', 1), ('TT Sanitary white', '#FDFDFC', 1),
                   ('TT HPL partition', '#E9E4DA', 1), ('TT Mirror', '#C9D6DC', 1), ('TT Porcelain tile', '#D9D6CF', 1),
                   ('TT Epoxy grey', '#B9BCBE', 1), ('TT Vinyl soft', '#DCD3C4', 1), ('TT Carpet sage', '#8FA898', 1),
                   ('TT Carpet office', '#8C8F93', 1), ('TT Timber oak', '#C49A6C', 1), ('TT Chengal', '#8A4B2A', 1),
                   ('TT Upholstery', '#5B6B73', 1), ('TT Cushion warm', '#D9B48C', 1), ('TT Black', '#26292B', 1),
                   ('TT LED warm', '#FFE2A8', 1), ('TT Equipment grey', '#9AA0A5', 1), ('TT Bin green', '#3E7B4F', 1),
                   ('TT Bin blue', '#2E5F9E', 1), ('TT Bin orange', '#E07B2E', 1), ('TT Bin brown', '#7A5A3A', 1),
                   ('TT Labu black', '#1D1A18', 1), ('TT Karst stone', '#C9C1B4', 1), ('TT Tin', '#B8BCC0', 1),
                   ('TT Coffee slat', '#6B4A33', 1), ('TT Felt acoustic', '#5E6A62', 1), ('TT Soft play', '#F2C9A0', 1),
                   ('TT Soft play mint', '#BFE1D5', 1), ('TT Firefly soffit', '#1B2530', 1), ('TT Firefly light', '#D6FF7A', 1),
                   ('TT Star screen', '#EFE6D2', 1), ('TT Encaustic tile', '#E7B9C4', 1), ('TT Map screen', '#14202A', 1),
                   ('TT Kelantan blue', '#3456D6', 1), ('TT Terengganu teal', '#11A89A', 1), ('TT Pahang river', '#8CC9E0', 1),
                   ('TT Johor gold', '#E8B523', 1), ('TT Johor green tile', '#2F6B3A', 1), ('TT Melaka red', '#B83A2E', 1),
                   ('TT NSembilan bronze', '#9A6A45', 1), ('TT Selangor lime', '#B5E655', 1), ('TT Perak caramel', '#C9A27A', 1),
                   ('TT Penang pink', '#E46F8C', 1), ('TT Kedah green', '#4E8F3A', 1), ('TT Kedah gold', '#D9B24A', 1),
                   ('TT Perlis mango', '#F28C28', 1), ('TT Bead pink', '#F6A2B5', 1), ('TT Bead mint', '#7FD1C4', 1), ('TT Bead yellow', '#FFE08A', 1),
                   ('TT Pantai Timur kit', '#3F93B8', 1), ('TT Planter gold', '#C9A24A', 1), ('TT Palm', '#4C8A3F', 1), ('TT Plant green', '#5E9A45', 1)]:
    mat(n_, c_, a_)

ST = {'KEL': ('Kelantan', 356.2, 'TT Kelantan blue'), 'TRG': ('Terengganu', 20.9, 'TT Terengganu teal'), 'PHG': ('Pahang', 68.4, 'TT Pahang river'),
      'JHR': ('Johor', 145.9, 'TT Johor gold'), 'MLK': ('Melaka', 187.6, 'TT Melaka red'), 'NSN': ('Negeri Sembilan', 213.3, 'TT NSembilan bronze'),
      'SGR': ('Selangor', 247.3, 'TT Selangor lime'), 'PRK': ('Perak', 311.0, 'TT Perak caramel'), 'PNG': ('Pulau Pinang', 313.4, 'TT Penang pink'),
      'KDH': ('Kedah', 322.7, 'TT Kedah green'), 'PLS': ('Perlis', 323.6, 'TT Perlis mango')}
FFL = {'GF': ZG, 'L1': ZL}

# ================================================================== geometry helpers
def P(C, r, b): return np.asarray(C, float) + d(b) * r
def rad3(b): return np.array([*d(b), 0.0])
def tan3(b): return np.array([*d(b + 90), 0.0])
Z = np.array([0.0, 0, 1])
def room(level, name): return [r for r in ROOMS if r['level'] == level and r['name'] == name][0]['poly']

# walls per level (2D) -> net room polygons
_east = K.east_part()[4]
WALLS = {'GF': unary_union([K.wall_full('GF'), CORE_FP]), 'L1': unary_union([K.wall_full('L1').difference(K.EAST_ZONE), _east, CORE_FP])}
COLS = unary_union([Point(P(B, r, b)).buffer(0.26 if r == R_COURT else 0.36, 8) for r, b in COLS_BIG] +
                   [Point(P(S, r, b)).buffer(0.29, 8) for r, b in COLS_SMALL])
def net(level, name):
    g = room(level, name).difference(WALLS[level]).difference(COLS if level == 'GF' or True else Polygon())
    ps = polys(g); return max(ps, key=lambda q: q.area) if ps else g

def rspan(netp, C, b, r_hint):
    ls = LineString([P(C, 0.05, b), P(C, 40, b)]); seg = ls.intersection(netp)
    segs = [seg] if seg.geom_type == 'LineString' else [s for s in getattr(seg, 'geoms', []) if s.geom_type == 'LineString']
    best = None
    for s in segs:
        rr = sorted(np.linalg.norm(np.array(s.coords) - C, axis=1))
        if rr[0] - 1e-6 <= r_hint <= rr[-1] + 1e-6: best = (rr[0], rr[-1])
    if best is None: raise ValueError(f'rspan miss b={b:.2f} r={r_hint:.2f}')
    return best

def tspan(netp, C, r, b):
    p = P(C, r, b); t = d(b + 90)
    ls = LineString([p - t * 30, p + t * 30]); seg = ls.intersection(netp)
    segs = [seg] if seg.geom_type == 'LineString' else [s for s in getattr(seg, 'geoms', []) if s.geom_type == 'LineString']
    for s in segs:
        ss = sorted(float(np.dot(np.array(q) - p, t)) for q in s.coords)
        if ss[0] - 1e-6 <= 0 <= ss[-1] + 1e-6: return ss[0], ss[-1]
    raise ValueError('tspan miss')

# ================================================================== registry + checks
ITEMS = []          # (level, room, footprint2d, zbottom, label)
def _def_pts(name, M=np.eye(4), acc=None):
    acc = [] if acc is None else acc
    for c in K.DEFS[name]['c']:
        _node_pts(c, M, acc)
    return acc
def _node_pts(n, M, acc):
    if n['t'] == 'g':
        for f in n.get('f', []):
            for p in f[0]: acc.append((M @ np.array([*p, 1.0]))[:3])
        for c in n.get('c', []): _node_pts(c, M, acc)
    elif n['t'] == 'i':
        Mi = np.eye(4); Mi[:3, 0], Mi[:3, 1], Mi[:3, 2], Mi[:3, 3] = n['x'], n['y'], n['z'], n['o']
        _def_pts(n['d'], M @ Mi, acc)
def _faces_pts(fs):
    return [np.array(p) for f in fs for p in f[0]]
def footprint(pts):
    a = np.array(pts); return MultiPoint(a[:, :2]).convex_hull, float(a[:, 2].min()), float(a[:, 2].max())

def reg(level, rname, node, label=None, check=True, fp=None):
    if node is None: return None
    if fp is None:
        pts = _node_pts(node, np.eye(4), []) or []
        if node['t'] == 'i': pts = []; _node_pts(node, np.eye(4), pts)
        if not pts: return node
        fp2, z0, z1 = footprint(pts)
    else:
        fp2, z0, z1 = fp
    ITEMS.append(dict(lv=level, room=rname, fp=fp2, z0=z0, z1=z1, label=label or node.get('n') or node.get('d'), check=check))
    return node

def frame_y(y):
    y = np.array(y, float); y /= np.linalg.norm(y); x = np.cross(y, Z); return x, y
def inst(defn, o, y, name=None):
    x, y = frame_y(y); return I(defn, o, x, y, Z, name=name)

def on_outer(defn, level, rname, C, b, r_hint, z, gap=0.0, name=None):
    n_ = NET[(level, rname)]; r1 = rspan(n_, C, b, r_hint)[1] - gap
    return reg(level, rname, inst(defn, [*P(C, r1, b), z], -rad3(b), name), name)
def on_inner(defn, level, rname, C, b, r_hint, z, gap=0.0, name=None):
    n_ = NET[(level, rname)]; r0 = rspan(n_, C, b, r_hint)[0] + gap
    return reg(level, rname, inst(defn, [*P(C, r0, b), z], rad3(b), name), name)
def on_radial(defn, level, rname, C, r, b_hint, side, z, gap=0.0, name=None):
    """side 'lo' = wall on the low-bearing side (fixture faces +tangent); 'hi' = high-bearing side"""
    n_ = NET[(level, rname)]; s0, s1 = tspan(n_, C, r, b_hint); p = P(C, r, b_hint); t = d(b_hint + 90)
    if side == 'lo': o = p + t * (s0 + gap); y = tan3(b_hint)
    else: o = p + t * (s1 - gap); y = -tan3(b_hint)
    return reg(level, rname, inst(defn, [*o, z], y, name), name)
def free(defn, level, rname, xy, z, ydir, name=None, check=True):
    return reg(level, rname, inst(defn, [xy[0], xy[1], z], [ydir[0], ydir[1], 0], name), name, check)
def grp(level, rname, name, m, faces, check=True):
    if not faces: return None
    node = G(name, None, m, faces)
    pts = _faces_pts(faces); fp2, z0, z1 = footprint(pts)
    ITEMS.append(dict(lv=level, room=rname, fp=fp2, z0=z0, z1=z1, label=name, check=check))
    return node

# ================================================================== component library (x along wall, y into the room, z up; origin = wall face, floor)
def box(x0, y0, z0, x1, y1, z1): return box_faces(x0, y0, z0, x1, y1, z1)
def lathe(profile, n=20, cx=0.0, cy=0.0):
    """profile [(r, z)] bottom->top -> closed solid of revolution (r=0 ends allowed)"""
    V, Pp = [], []
    for r, z in profile:
        for k in range(n):
            a = 2 * math.pi * k / n; V.append([cx + r * math.cos(a), cy + r * math.sin(a), z])
    m = len(profile)
    for i in range(m - 1):
        for k in range(n):
            a, b_ = i * n + k, i * n + (k + 1) % n; c, d_ = a + n, b_ + n
            Pp.append([a, b_, d_, c])
    Pp.append(list(range(n))[::-1]); Pp.append([(m - 1) * n + k for k in range(n)])
    fs = mesh_faces(V, Pp)
    zc = sum(z for _, z in profile) / m
    return fix_outward(fs, [cx, cy, zc])

def D_counter(L, Dp, H, top='TT Solid surface', body='TT HPL partition', kick='TT Black'):
    name = f'Counter {int(L*1000)}x{int(Dp*1000)} h{int(H*1000)} ({body.replace("TT ", "")})'
    if name in K.DEFS: return name
    return defn_box(name, 'counter: top, body, recessed kick', [(top, box(-L/2, 0, H - 0.03, L/2, Dp, H)), (body, box(-L/2, 0, 0.1, L/2, Dp - 0.03, H - 0.03)),
                                                                (kick, box(-L/2 + 0.05, 0, 0, L/2 - 0.05, Dp - 0.1, 0.1))])
def D_rack(L, Dp=0.45, H=2.0, n=5):
    name = f'Shelving rack {int(L*1000)}x{int(Dp*1000)} h{int(H*1000)}'
    if name in K.DEFS: return name
    posts = Solids([box(x, y, 0, x + 0.04, y + 0.04, H) for x in (-L/2, L/2 - 0.04) for y in (0.02, Dp - 0.04)])
    sh = Solids([box(-L/2, 0.02, 0.15 + k * (H - 0.25) / (n - 1), L/2, Dp, 0.17 + k * (H - 0.25) / (n - 1)) for k in range(n)])
    return defn_box(name, 'steel shelving', [('TT Equipment grey', posts), ('TT Stainless', sh)])
def D_boxu(name, desc, w, dp, h, m, base=0.0):
    if name in K.DEFS: return name
    return defn_box(name, desc, [(m, box(-w/2, 0, base, w/2, dp, h))])
D_FRIDGE = lambda: D_boxu('Fridge 2-door 1200x750 h2000', 'stainless upright chiller', 1.2, 0.75, 2.0, 'TT Stainless')
D_FRIDGE1 = lambda: D_boxu('Fridge 1-door 600x650 h1800', 'stainless upright chiller', 0.6, 0.65, 1.8, 'TT Stainless')
D_MDB = lambda: D_boxu('Switchboard panel 800x600 h2100', 'MDB cubicle', 0.8, 0.6, 2.1, 'TT Equipment grey')
D_SERVER = lambda: D_boxu('Server rack 600x1000 h2000', '42U rack', 0.6, 1.0, 2.0, 'TT Black')
D_LOCKER = lambda L: D_boxu(f'Locker bank {int(L*1000)}x450 h1800', 'staff lockers', L, 0.45, 1.8, 'TT Upholstery')
D_SCREEN = lambda: D_boxu('Wall screen 1650x60 h950 (at 1.1 m)', 'TV / presentation screen', 1.65, 0.06, 2.05, 'TT Black', base=1.1)

def D_sink_counter(L, Dp=0.65, H=0.9, top='TT Stainless', body='TT Stainless', nsink=1, label='SS'):
    name = f'Sink counter {label} {int(L*1000)}x{int(Dp*1000)} ({nsink} bowl)'
    if name in K.DEFS: return name
    parts = [(top, box(-L/2, 0, H - 0.04, L/2, Dp, H)), (body, box(-L/2, 0, 0.1, L/2, Dp - 0.04, H - 0.04)), ('TT Black', box(-L/2 + 0.05, 0, 0, L/2 - 0.05, Dp - 0.1, 0.1))]
    taps = []
    for k in range(nsink):
        x = -L/2 + (k + 0.5) * L / nsink
        taps += beam([x, 0.08, H], [x, 0.08, H + 0.28], 0.03, 0.03) + beam([x, 0.08, H + 0.28], [x, 0.24, H + 0.28], 0.025, 0.025)
        parts.append(('TT Equipment grey', box(x - 0.22, 0.15, H, x + 0.22, 0.52, H + 0.003)))     # bowl rim mark
    parts.append(('TT Stainless', taps))
    return defn_box(name, f'counter with {nsink} sink(s) and taps', parts)

def D_wc():
    name = 'WC wall-hung + concealed cistern'
    if name in K.DEFS: return name
    pan = box(-0.18, 0.2, 0.22, 0.18, 0.38, 0.42) + lathe([(0.0, 0.22), (0.17, 0.24), (0.19, 0.42), (0.0, 0.42)], 18, 0, 0.42)
    seat = box(-0.19, 0.2, 0.42, 0.19, 0.4, 0.44)
    return defn_box(name, 'wall-hung WC on a tiled IPS duct', [('TT HPL partition', box(-0.3, 0, 0, 0.3, 0.2, 1.1)), ('TT Sanitary white', Solids([pan[:6], pan[6:], seat])),
                                                              ('TT Stainless', box(-0.12, 0.2, 0.95, 0.12, 0.215, 1.07))])
def D_urinal():
    name = 'Urinal + privacy screen'
    if name in K.DEFS: return name
    bowl = lathe([(0.0, 0.5), (0.16, 0.52), (0.18, 0.75), (0.15, 1.02), (0.0, 1.05)], 16, 0, 0.18)
    return defn_box(name, 'urinal (bowl rim 600 mm) with screen', [('TT Sanitary white', bowl), ('TT HPL partition', box(0.36, 0, 0.6, 0.385, 0.42, 1.5))])
def D_vanity(L):
    name = f'Vanity {int(L*1000)} with basins + mirror'
    if name in K.DEFS: return name
    n = max(1, int(L // 0.8)); parts = [('TT Solid surface', box(-L/2, 0, 0.8, L/2, 0.55, 0.83)), ('TT HPL partition', box(-L/2, 0.45, 0.62, L/2, 0.55, 0.8)),
                                       ('TT Mirror', box(-L/2, 0, 1.0, L/2, 0.012, 1.9))]
    bowls, taps = [], []
    for k in range(n):
        x = -L/2 + (k + 0.5) * L / n
        bowls.append(lathe([(0.0, 0.83), (0.18, 0.83), (0.2, 0.95), (0.0, 0.95)], 16, x, 0.3))
        taps += beam([x, 0.08, 0.83], [x, 0.08, 1.05], 0.03, 0.03) + beam([x, 0.08, 1.05], [x, 0.2, 1.05], 0.025, 0.025)
    parts += [('TT Sanitary white', Solids(bowls)), ('TT Stainless', taps)]
    return defn_box(name, f'solid-surface vanity at 830 mm, {n} vessel basin(s)', parts)
def D_grab():
    name = 'Grab bars PwD (L + drop-down)'
    if name in K.DEFS: return name
    fs = beam([-0.45, 0.05, 0.7], [0.3, 0.05, 0.7], 0.035, 0.035) + beam([0.3, 0.05, 0.7], [0.3, 0.05, 1.4], 0.035, 0.035)
    return defn_box(name, 'stainless grab rails to MS 1184', [('TT Stainless', fs)])
def D_dryer(): return D_boxu('Hand dryer', 'hand dryer at 1100', 0.3, 0.18, 1.4, 'TT Stainless', base=1.1)
def D_mop():
    name = 'Mop sink 600x500'
    if name in K.DEFS: return name
    return defn_box(name, 'janitor sink + tap', [('TT Stainless', box(-0.3, 0, 0, 0.3, 0.5, 0.45)), ('TT Stainless', beam([0, 0.06, 0.45], [0, 0.06, 0.9], 0.03, 0.03))])

def D_chair(m='TT Upholstery'):
    name = f'Chair ({m.replace("TT ", "")})'
    if name in K.DEFS: return name
    legs = Solids([box(x, y, 0, x + 0.03, y + 0.03, 0.44) for x in (-0.22, 0.19) for y in (0.05, 0.42)])
    return defn_box(name, 'side chair (origin = back edge centre, y = facing)', [('TT Steel dark', legs), (m, box(-0.23, 0.04, 0.44, 0.23, 0.47, 0.49)),
                                                                                (m, box(-0.23, 0.0, 0.49, 0.23, 0.05, 0.9))])
def D_officechair():
    name = 'Office chair'
    if name in K.DEFS: return name
    return defn_box(name, 'task chair', [('TT Black', cyl_faces(0, 0.25, 0.3, 0.0, 0.05, 10)), ('TT Black', cyl_faces(0, 0.25, 0.03, 0.05, 0.42, 8)),
                                         ('TT Upholstery', box(-0.24, 0.04, 0.42, 0.24, 0.48, 0.5)), ('TT Upholstery', box(-0.22, 0.0, 0.55, 0.22, 0.06, 1.0))])
def D_armchair(m='TT Cushion warm'):
    name = f'Armchair ({m.replace("TT ", "")})'
    if name in K.DEFS: return name
    return defn_box(name, 'lounge chair', [(m, box(-0.38, 0.0, 0.1, 0.38, 0.75, 0.42)), (m, box(-0.38, 0.0, 0.42, 0.38, 0.16, 0.8)),
                                           (m, Solids([box(-0.38, 0.16, 0.42, -0.28, 0.75, 0.6), box(0.28, 0.16, 0.42, 0.38, 0.75, 0.6)])),
                                           ('TT Steel dark', box(-0.33, 0.05, 0.0, 0.33, 0.7, 0.1))])
def D_desk(L, Dp=0.7):
    name = f'Desk {int(L*1000)}x{int(Dp*1000)}'
    if name in K.DEFS: return name
    return defn_box(name, 'desk h740', [('TT Timber oak', box(-L/2, 0, 0.71, L/2, Dp, 0.74)),
                                        ('TT GRG white', Solids([box(-L/2, 0.05, 0, -L/2 + 0.03, Dp - 0.05, 0.71), box(L/2 - 0.03, 0.05, 0, L/2, Dp - 0.05, 0.71),
                                                                 box(-L/2 + 0.03, 0.0, 0.35, L/2 - 0.03, 0.02, 0.71)]))])
def D_table_rect(L, W, H=0.74, top='TT Timber oak'):
    name = f'Table {int(L*1000)}x{int(W*1000)} ({top.replace("TT ", "")})'
    if name in K.DEFS: return name
    legs = Solids([box(x, y, 0, x + 0.05, y + 0.05, H - 0.03) for x in (-L/2 + 0.08, L/2 - 0.13) for y in (-W/2 + 0.08, W/2 - 0.13)])
    return defn_box(name, 'table (origin = centre)', [(top, box(-L/2, -W/2, H - 0.03, L/2, W/2, H)), ('TT Steel dark', legs)])
def D_table_round(R, H=0.74, top='TT Solid surface'):
    name = f'Round table Ø{int(R*2000)} ({top.replace("TT ", "")})'
    if name in K.DEFS: return name
    return defn_box(name, 'round table (origin = centre)', [(top, cyl_faces(0, 0, R, H - 0.03, H, 24)), ('TT Black', cyl_faces(0, 0, 0.04, 0.03, H - 0.03, 8)),
                                                           ('TT Black', cyl_faces(0, 0, R * 0.55, 0, 0.03, 16))])
def D_stool(m, H=0.46, R=0.19):
    name = f'Stool Ø{int(R*2000)} h{int(H*1000)} ({m.replace("TT ", "")})'
    if name in K.DEFS: return name
    return defn_box(name, 'stool (origin = centre)', [('TT Bronze PVD', cyl_faces(0, 0, 0.025, 0, H - 0.05, 8)), (m, cyl_faces(0, 0, R, H - 0.05, H, 16))])
def D_bench(L, Dp=0.45, H=0.45, m='TT Timber oak'):
    name = f'Bench {int(L*1000)}x{int(Dp*1000)} ({m.replace("TT ", "")})'
    if name in K.DEFS: return name
    return defn_box(name, 'bench', [(m, box(-L/2, 0, H - 0.05, L/2, Dp, H)), ('TT Steel dark', Solids([box(-L/2 + 0.1, 0.05, 0, -L/2 + 0.14, Dp - 0.05, H - 0.05),
                                                                                                        box(L/2 - 0.14, 0.05, 0, L/2 - 0.1, Dp - 0.05, H - 0.05)]))])
def D_bed():
    name = 'Treatment bed 800x1900'
    if name in K.DEFS: return name
    return defn_box(name, 'first aid couch', [('TT Vinyl soft', box(-0.4, 0.0, 0.55, 0.4, 1.9, 0.65)), ('TT Stainless', box(-0.35, 0.1, 0, 0.35, 1.8, 0.55))])
def D_genset():
    name = 'Generator set 3200x1300 h1800'
    if name in K.DEFS: return name
    return defn_box(name, 'standby genset on plinth + exhaust riser', [('TT Concrete', box(-1.7, 0.0, 0, 1.7, 1.5, 0.15)), ('TT Kedah green', box(-1.6, 0.1, 0.15, 1.6, 1.4, 1.8)),
                                                                     ('TT Steel dark', cyl_faces(1.2, 0.75, 0.1, 1.8, 3.9, 10))])
def D_bin(kind):
    spec = {'660': (1.26, 0.78, 1.3, 'TT Bin green'), 'blue': (0.58, 0.73, 1.07, 'TT Bin blue'), 'orange': (0.58, 0.73, 1.07, 'TT Bin orange'),
            'brown': (0.58, 0.73, 1.07, 'TT Bin brown')}[kind]
    w, dp, h, m = spec; name = f'Wheelie bin {kind} {int(w*1000)}x{int(dp*1000)}'
    if name in K.DEFS: return name
    return defn_box(name, 'refuse bin', [(m, box(-w/2, 0.02, 0.05, w/2, dp, h)), ('TT Black', Solids([cyl_faces(-w/2 + 0.1, 0.15, 0.05, 0, 0.1, 8), cyl_faces(w/2 - 0.1, 0.15, 0.05, 0, 0.1, 8)]))])
def D_coldroom():
    name = 'Walk-in cold room 2400x2000 h2400'
    if name in K.DEFS: return name
    return defn_box(name, 'insulated panel cold room', [('TT Sanitary white', box(-1.2, 0, 0, 1.2, 2.0, 2.4)), ('TT Stainless', box(-0.4, 2.0, 0, 0.4, 2.03, 2.0))])
def D_shoerack(L):
    name = f'Shoe rack {int(L*1000)}x350 h1100'
    if name in K.DEFS: return name
    sh = Solids([box(-L/2, 0, 0.1 + k * 0.25, L/2, 0.35, 0.12 + k * 0.25) for k in range(5)])
    return defn_box(name, 'slatted shoe rack, 5 tiers', [('TT Timber oak', sh), ('TT Timber oak', Solids([box(-L/2, 0, 0, -L/2 + 0.03, 0.35, 1.1), box(L/2 - 0.03, 0, 0, L/2, 0.35, 1.1)]))])
def D_ablution(L):
    name = f'Ablution bench {int(L*1000)} (seated)'
    if name in K.DEFS: return name
    n = max(2, int(L // 0.7)); taps = []; seats = []
    for k in range(n):
        x = -L/2 + (k + 0.5) * L / n
        taps += beam([x, 0.02, 0.85], [x, 0.18, 0.85], 0.025, 0.025)
        seats.append(box(x - 0.18, 0.75, 0.0, x + 0.18, 1.05, 0.4))
    return defn_box(name, 'trough + taps at 850 + low seats', [('TT Porcelain tile', box(-L/2, 0, 0, L/2, 0.4, 0.3)), ('TT Stainless', taps),
                                                              ('TT Porcelain tile', box(-L/2, 0, 0, L/2, 0.06, 1.2)), ('TT Timber oak', Solids(seats))])
def D_planter_palm():
    name = 'Palm in gold planter'
    if name in K.DEFS: return name
    pot = lathe([(0.0, 0.0), (0.38, 0.0), (0.45, 0.65), (0.0, 0.65)], 20)
    trunk = beam([0, 0, 0.6], [0.05, 0, 2.6], 0.12, 0.12)
    fr = []
    for k in range(9):
        a = 2 * math.pi * k / 9; tip = np.array([math.cos(a) * 1.15, math.sin(a) * 1.15, 2.25]); base = np.array([0.05, 0, 2.6])
        mid = base + (tip - base) * 0.5 + np.array([0, 0, 0.35]); s = np.array([-math.sin(a), math.cos(a), 0]) * 0.17
        fr += mesh_faces([base, mid + s, tip, mid - s], [[0, 1, 2, 3]])
    return defn_box(name, 'inspo 4: palms in gold pots', [('TT Planter gold', pot), ('TT Tree trunk', trunk), ('TT Palm', fr)])
def D_plant():
    name = 'Plant in white pot'
    if name in K.DEFS: return name
    pot = lathe([(0.0, 0.0), (0.2, 0.0), (0.24, 0.5), (0.0, 0.5)], 16)
    V, Fc = K.icosphere(0.4, 1); V = [v * np.array([1, 1, 0.8]) + np.array([0, 0, 0.85]) for v in V]
    return defn_box(name, 'indoor plant', [('TT GRG white', pot), ('TT Plant green', fix_outward(mesh_faces(V, Fc), [0, 0, 0.85]))])

# ================================================================== state colour line + inlays
def inlay(level, rname, C, b, r0, r1, z, m='TT Brass inlay', w=0.024, h=0.004, name='Brass line'):
    a, c = P(C, r0, b), P(C, r1, b)
    g = LineString([a, c]).buffer(w / 2, cap_style=2)
    return grp(level, rname, name, m, prism(g, z, z + h), check=False)

def arc_bar(C, r, b0, b1, z0, z1, t=0.05):
    return prism(sector(C, r - t / 2, r + t / 2, b0, b1, max(4, int(abs(b1 - b0) / 1.5))), z0, z1)

# ================================================================== FLOORS (finishes)
FIN = {'Entrance lobby + info': 'TT Terrazzo', 'Info / security / wheelchair loan': 'TT Terrazzo', 'First aid': 'TT Vinyl soft',
       'Cafe dining': 'TT Timber oak', 'Cafe serving counter': 'TT Terrazzo', 'Cafe kitchen': 'TT Epoxy grey',
       'Nappy change (family room)': 'TT Vinyl soft', 'Nursing room (family room)': 'TT Vinyl soft',
       'Gallery exhibition': 'TT Terrazzo', 'Multipurpose hall (Dapur Rewang)': 'TT Timber oak', 'Family waiting': 'TT Timber oak',
       'Male prayer + ablution': 'TT Carpet sage', 'Female prayer + ablution': 'TT Carpet sage', 'Musolla foyer + shoe racks': 'TT Terrazzo',
       'Admin reception + waiting': 'TT Terrazzo', 'Main office': 'TT Carpet office', "Manager's office": 'TT Carpet office',
       'Meeting room': 'TT Carpet office', 'Pantry': 'TT Porcelain tile', 'L1 lift lobby': 'TT Terrazzo', 'Gallery staff': 'TT Carpet office'}
def floor_mat(r):
    n = r['name']
    if n in FIN: return FIN[n]
    if 'restroom' in n.lower() or 'toilet' in n.lower() or 'WC' in r['label']: return 'TT Porcelain tile'
    if 'display' in n: return 'TT Terrazzo'
    if r['zone'] in ('serv',) or 'prep' in n or 'store' in n.lower(): return 'TT Epoxy grey'
    if r['zone'] == 'circ': return 'TT Terrazzo'
    return 'TT Terrazzo'

def floors(level):
    out = []; z = FFL[level]
    for r in ROOMS:
        if r['level'] != level: continue
        if r['zone'] == 'open' and r['name'].startswith('Verandah'):
            g = r['poly']
        elif r['zone'] == 'open': continue
        else: g = r['poly']
        if r['name'] in ('Stair 1', 'Lifts (2 nos)') or r['name'].startswith('Stair 2'): continue
        g = clean(g.buffer(-0.03, join_style=2).difference(CORE_FP))
        if g.is_empty: continue
        m = 'TT Terrazzo' if r['zone'] == 'open' else floor_mat(r)
        if r['name'] == 'Multipurpose hall (Dapur Rewang)': g = clean(g.difference(room('L1', 'MPH furniture store')))
        out.append(G(f'Floor – {r["name"]} ({m.replace("TT ", "")})', None, m, prism(g, z, z + 0.02)))
    return G(f'{level} FLOOR FINISHES', None, None, None, out)

# ================================================================== GF
def gf_interior():
    nodes, ceil = [], []
    z = ZG; zf = ZG + 0.02
    # ---------- court: 11 compass lines, beacons
    court_obst = unary_union([Point(B).buffer(1.55, 24), sector(B, R_COURT - 0.9, R_COURT - 0.3, 300, 318, 12)])
    play = sector(B, 3.3, 8.6, 22, 94)
    lines = []
    for k, (nm, b, m) in ST.items():
        seg = LineString([P(B, 1.6, b), P(B, R_COURT - 0.05, b)]).difference(court_obst)
        for s in ([seg] if seg.geom_type == 'LineString' else list(seg.geoms)):
            for part, zz in ((s.difference(play), ZG + 0.03), (s.intersection(play), ZG + 0.05)):
                for q in ([part] if part.geom_type == 'LineString' else list(getattr(part, 'geoms', []))):
                    if q.length > 0.05: lines += prism(q.buffer(0.012, cap_style=2), zz, zz + 0.004)
        # verandah strip
        lines += prism(LineString([P(B, R_COURT + 0.05, b), P(B, R_VER - 0.1, b)]).buffer(0.012, cap_style=2), zf, zf + 0.004)
    nodes.append(G('Court + verandah: 11 brass compass lines (true bearings from Temerloh)', None, 'TT Brass inlay', lines))
    bdef = defn_box('State beacon bollard h1000', 'beacon at the end of each compass line: bronze post + state-colour light ring',
                    [('TT Bronze PVD', cyl_faces(0, 0, 0.07, 0, 0.9, 12)), ('TT LED warm', cyl_faces(0, 0, 0.075, 0.9, 1.0, 12))])
    bea = []
    for k, (nm, b, m) in ST.items():
        if k in ('PRK', 'PNG', 'KDH', 'PLS'): continue            # Utara beacons sit in the lobby
        p = P(B, R_COURT + 0.35, b)
        bea.append(reg('GF', 'Verandah (open, covered)', I(bdef, [p[0], p[1], zf], [*d(b + 90), 0], name=f'Beacon {nm} {b}°'), f'Beacon {nm}'))
        bea.append(G(f'Beacon ring colour {nm}', None, m, cyl_faces(p[0], p[1], 0.078, zf + 0.92, zf + 0.98, 12)))
    nodes.append(G('State beacons (7 in the court ring)', None, None, None, bea))
    # tenun underside is on the oculus canopy (existing); add verandah bulkheads + state light lines for every stall
    # ---------- stalls
    STALLS = {5: 'KEL', 6: 'TRG', 7: None, 8: None, 13: 'JHR', 14: None, 15: None, 16: 'MLK'}
    for m_, key in STALLS.items():
        b0, b1 = mod(m_); bc = (b0 + b1) / 2
        lab = {5: 'A2-1', 6: 'A2-2', 7: 'A2-3', 8: 'A2-4', 13: 'A1-1', 14: 'A1-2', 15: 'A1-3', 16: 'A1-4'}[m_]
        rn = f'{lab} display'; mcol = ST[key][2] if key else 'TT Pantai Timur kit'
        kids, ck = [], []
        nm = ST[key][0] if key else 'Tamu guest pod'
        # bulkhead with state light line inside the shopfront
        ck.append(G('GRG bulkhead', None, 'TT GRG white', prism(sector(B, R_VER + 0.2, R_VER + 0.45, b0 + 0.9, b1 - 0.9, 10), ZG + 3.4, ZSOF)))
        ck.append(G(f'State light line ({nm})', None, mcol, prism(sector(B, R_VER + 0.2, R_VER + 0.26, b0 + 0.9, b1 - 0.9, 10), ZG + 3.36, ZG + 3.4)))
        # counter (curved, across the stall) – themed body
        cb = {'KEL': 'TT Solid surface', 'TRG': 'TT Chengal', 'JHR': 'TT Johor green tile', 'MLK': 'TT Melaka red'}.get(key, 'TT Pantai Timur kit')
        a0, a1 = b0 + 3.0, b1 - 3.0
        if key == 'TRG':           # hull-shaped (double-ended)
            n = 24; pts = [P(B, 13.05 + math.sin(math.pi * i / n) * 0.36, a0 + (a1 - a0) * i / n) for i in range(n + 1)] + \
                          [P(B, 13.05 - math.sin(math.pi * i / n) * 0.3, a0 + (a1 - a0) * i / n) for i in range(n, -1, -1)]
            hull = Polygon(pts).buffer(0)
            kids.append(grp('GF', rn, 'Hull counter (chengal)', 'TT Chengal', prism(hull, zf + 0.12, zf + 0.96)))
            kids.append(G('Hull counter top', None, 'TT Solid surface', prism(hull, zf + 0.96, zf + 1.0)))
            kids.append(G('Counter plinth', None, 'TT Black', prism(hull.buffer(-0.06), zf, zf + 0.12)))
        else:
            kids.append(grp('GF', rn, 'Display counter body', cb, prism(sector(B, 12.75, 13.35, a0, a1, 12), zf + 0.12, zf + 0.97)))
            kids.append(G('Display counter top', None, 'TT Solid surface' if key != 'JHR' else 'TT Timber oak', prism(sector(B, 12.71, 13.38, a0 - 0.2, a1 + 0.2, 12), zf + 0.97, zf + 1.0)))
            kids.append(G('Counter plinth', None, 'TT Black', prism(sector(B, 12.8, 13.28, a0 + 0.3, a1 - 0.3, 12), zf, zf + 0.12)))
            # accessible low section 800 at the front edge (MS 1184)
            kids.append(grp('GF', rn, 'Low counter 760–860 (MS 1184)', 'TT Solid surface', prism(sector(B, 12.45, 12.75, a0, a0 + 3.2, 6), zf + 0.78, zf + 0.81)))
        # back shelves (floating) on the back wall, clear of the back door (door sits towards b0 side for A2, b1 side for A1? -> use real door)
        dpos = [np.array(c) for c, t, w, sw in DOORS['GF'] if room('GF', rn).buffer(0.2).contains(Point(c)) and abs(np.linalg.norm(np.array(c) - B) - R_DISP) < 0.3]
        db = math.degrees(math.atan2(*(dpos[0] - B))) % 360 if dpos else bc
        if db < b0 - 1: db += 360
        span = [(b0 + 1.0, db - 3.0), (db + 3.0, b1 - 1.0)]
        sa, sb_ = max(span, key=lambda s: s[1] - s[0])
        shelf_m = {'KEL': 'TT Solid surface', 'TRG': 'TT Chengal', 'JHR': 'TT Johor gold', 'MLK': 'TT Solid surface'}.get(key, 'TT Stainless')
        sh = []
        for zz in (1.5, 2.0, 2.5): sh += prism(sector(B, R_DISP - 0.42, R_DISP - 0.12, sa, sb_, 8), zf + zz, zf + zz + 0.04)
        kids.append(grp('GF', rn, 'Back shelves', shelf_m, sh))
        # themed features
        if key == 'KEL':          # wau bulan crescent cove + blue rim + indigo wall panel
            nn = 30; cres = [P(B, 13.75 - math.sin(math.pi * i / nn) * 1.6, b0 + 1.6 + (b1 - b0 - 3.2) * i / nn) for i in range(nn + 1)] + \
                              [P(B, 13.95 - math.sin(math.pi * i / nn) * 0.55, b0 + 1.6 + (b1 - b0 - 3.2) * i / nn) for i in range(nn, -1, -1)]
            cr = Polygon(cres).buffer(0)
            ck.append(G('Wau bulan crescent cove (GRG)', None, 'TT GRG white', prism(cr, ZG + 3.62, ZG + 3.72)))
            ck.append(G('Crescent rim light (bunga telang blue)', None, 'TT Kelantan blue', prism(cr.buffer(0.03).difference(cr), ZG + 3.58, ZG + 3.62)))
            kids.append(G('Indigo gradient wall panel', None, 'TT Kelantan blue', prism(sector(B, R_DISP - 0.11, R_DISP - 0.08, sa, sb_, 8), zf + 1.0, zf + 3.0)))
        elif key == 'TRG':        # chengal boat ribs
            ribs = []
            for k_ in range(8):
                r = 11.5 + k_ * 0.42; pts = []
                for i in range(13):
                    t = i / 12; a = b0 + 1.2 + (b1 - b0 - 2.4) * t; p = P(B, r, a); pts.append([p[0], p[1], ZG + 3.1 + math.sin(t * math.pi) * 0.7])
                for p, q in zip(pts[:-1], pts[1:]): ribs += beam(p, q, 0.06, 0.12, up=[0, 0, 1])
            ck.append(G('Chengal ribs (boat frames)', None, 'TT Chengal', ribs))
            kids.append(G('Sea-teal wall panel with wave lines', None, 'TT Terengganu teal', prism(sector(B, R_DISP - 0.11, R_DISP - 0.08, sa, sb_, 8), zf + 1.0, zf + 3.0)))
        elif key == 'JHR':        # zapin fins + faceted (pineapple) grid
            fins = []; a = sa; steps = [1, 1, 2, 1, 1, 2, 1, 1, 3]
            for s_ in steps:
                if a > sb_ - 0.5: break
                fins += prism(sector(B, R_DISP - 0.38, R_DISP - 0.1, a, a + 0.6, 2), zf, zf + 1.2 + s_ * 0.65); a += 0.9 + s_ * 0.6
            kids.append(grp('GF', rn, 'Zapin rhythm fins (gold)', 'TT Johor gold', fins))
            grid = []
            for k_ in range(-6, 12):
                for sgn in (1, -1):
                    pts = []
                    for i in range(11):
                        u = i / 10; v = (u * 6 - k_) / 6 if sgn > 0 else (k_ - u * 6) / 6
                        if 0 <= v <= 1: pts.append([*P(B, R_VER + 0.5 + (R_DISP - R_VER - 0.8) * v, b0 + 1.0 + (b1 - b0 - 2.0) * u), ZG + 3.55])
                    for p, q in zip(pts[:-1], pts[1:]): grid += beam(p, q, 0.03, 0.08)
            ck.append(G('Faceted pineapple ceiling grid (gold)', None, 'TT Johor gold', grid))
        elif key == 'MLK':        # bead pendants + red dado + tile rug
            kids.append(G('Stadthuys red dado', None, 'TT Melaka red', prism(sector(B, R_DISP - 0.11, R_DISP - 0.08, b0 + 0.9, b1 - 0.9, 10), zf, zf + 0.9)))
            kids.append(G('Peranakan tile rug', None, 'TT Encaustic tile', prism(sector(B, 11.5, 12.5, b0 + 3, b1 - 3, 10), zf, zf + 0.004)))
            beads = {'TT Bead pink': [], 'TT Bead mint': [], 'TT Bead yellow': []}; rods = []
            V0, F0 = K.icosphere(0.07, 0)
            for k_ in range(3):
                c0 = P(B, 12.9, b0 + 4.5 + k_ * 4.5)
                for j in range(9):
                    q = c0 + d(j * 40) * (0.08 + (j % 3) * 0.09); zz = ZG + 2.3 + (j % 4) * 0.22
                    beads[list(beads)[j % 3]] += fix_outward(mesh_faces([v + np.array([q[0], q[1], zz]) for v in V0], F0), [q[0], q[1], zz])
                    rods += beam([q[0], q[1], zz + 0.07], [q[0], q[1], ZSOF], 0.006, 0.006)
            for mm, fs in beads.items(): ck.append(G(f'Bead pendants {mm.replace("TT Bead ", "")}', None, mm, fs))
            ck.append(G('Pendant rods', None, 'TT Black', rods))
        else:                     # guest pod: magnetic rails + lightbox + service bulkhead
            kids.append(G('Magnetic rails', None, 'TT Stainless', prism(sector(B, R_DISP - 0.13, R_DISP - 0.08, sa, sb_, 8), zf + 1.1, zf + 1.15) +
                          prism(sector(B, R_DISP - 0.13, R_DISP - 0.08, sa, sb_, 8), zf + 2.6, zf + 2.65)))
            kids.append(G('Swap-in lightbox (region kit)', None, 'TT Pantai Timur kit', prism(sector(B, R_DISP - 0.16, R_DISP - 0.13, sa + 0.3, sb_ - 0.3, 8), zf + 1.25, zf + 2.5)))
            kids.append(grp('GF', rn, 'Fixed service drop (power, water, exhaust)', 'TT Tin', prism(sector(B, R_DISP - 0.6, R_DISP - 0.1, sb_ - 2.2, sb_, 4), ZG + 3.0, ZSOF), check=False))
        # bearing tag on the bulkhead (state stalls)
        if key:
            kids.append(G(f'Bearing tag {ST[key][1]}° ({nm})', None, 'TT Solid surface', prism(sector(B, R_VER + 0.17, R_VER + 0.2, bc - 4, bc + 4, 6), ZG + 3.55, ZG + 3.9)))
            kids.append(inlay('GF', rn, B, ST[key][1], R_VER + 0.1, 12.6, zf + 0.02, name=f'Brass line {nm} (into the stall)'))
        # prep room: SS sink counter + worktop + fridge + hand basin ; store: racks
        pr = f'{lab} staff/prep'; stn = f'{lab} store'
        kids.append(on_outer(D_sink_counter(1.8, 0.65, 0.9, nsink=1, label='prep'), 'GF', pr, B, bc - 3.5, 15.8, zf, name='Prep sink counter'))
        kids.append(on_outer(D_FRIDGE(), 'GF', pr, B, bc + 4.2, 15.8, zf, name='Chiller'))
        kids.append(on_radial(D_counter(1.2, 0.6, 0.9, 'TT Stainless', 'TT Stainless'), 'GF', pr, B, 15.8, bc, 'lo' if (b1 - db) < (db - b0) else 'hi', zf, name='SS worktop'))
        kids.append(on_outer(D_rack(1.8, 0.45, 2.0), 'GF', stn, B, bc + 3.0, 17.4, zf, name='Store rack'))
        nodes.append(G(f'STALL {lab} – {nm}', None, None, None, [x for x in kids if x]))
        ceil.append(G(f'Stall {lab} ceiling features', None, None, None, ck))
    # ---------- café (Perak)
    s0, s1 = mod(11); c0, c1 = mod(12); kids, ck = [], []
    kids.append(grp('GF', 'Cafe serving counter', 'Tin servery counter', 'TT Tin', prism(sector(B, 13.1, 13.7, s0 + 1.6, s1 - 0.4, 12), zf + 0.1, zf + 1.02)))
    kids.append(G('Servery top (white quartz)', None, 'TT Solid surface', prism(sector(B, 13.06, 13.74, s0 + 1.4, s1 - 0.2, 12), zf + 1.02, zf + 1.06)))
    kids.append(grp('GF', 'Cafe serving counter', 'Low counter 760–860', 'TT Solid surface', prism(sector(B, 12.8, 13.1, s1 - 3.4, s1 - 0.4, 6), zf + 0.78, zf + 0.81)))
    kids.append(on_outer(D_counter(2.4, 0.6, 0.9, 'TT Solid surface', 'TT Coffee slat'), 'GF', 'Cafe serving counter', B, (s0 + s1) / 2 + 2.5, 14.0, zf, name='Back bar (coffee)'))
    # kitchen
    kids.append(on_outer(D_sink_counter(2.4, 0.7, 0.9, nsink=2, label='kitchen'), 'GF', 'Cafe kitchen', B, (s0 + s1) / 2 - 2.0, 17.2, zf, name='Double sink'))
    kids.append(on_radial(D_counter(2.0, 0.7, 0.9, 'TT Stainless', 'TT Stainless'), 'GF', 'Cafe kitchen', B, 16.6, s1 - 2, 'hi', zf, name='Cook line (induction)'))
    kids.append(on_radial(D_FRIDGE(), 'GF', 'Cafe kitchen', B, 15.9, s0 + 2, 'lo', zf, name='Chiller'))
    kids.append(on_outer(D_boxu('Exhaust hood 2000x900', 'kitchen hood', 2.0, 0.9, 2.4, 'TT Stainless', base=1.9), 'GF', 'Cafe kitchen', B, s1 - 4.0, 16.6, zf, name='Hood'))
    # dining
    tdef = D_table_round(0.38, 0.74, 'TT Solid surface'); sdef = D_stool('TT Perak caramel')
    tables = []
    for r, f in [(12.5, 0.5), (14.1, 0.28), (14.1, 0.72), (15.7, 0.5), (17.1, 0.3), (17.1, 0.7)]:
        p = P(B, r, c0 + (c1 - c0) * f); tables.append(free(tdef, 'GF', 'Cafe dining', p, zf, d(0), name='Kopitiam table'))
        for j in range(3):
            q = p + d(j * 120 + 30) * 0.62; tables.append(free(sdef, 'GF', 'Cafe dining', q, zf, d(0), name='Stool'))
    kids.append(G('Kopitiam tables + stools', None, None, None, tables))
    # karst relief wall on the 130.3° wall (dining side)
    kw = []
    nr, nz = 22, 12
    for i in range(nr):
        for j in range(nz):
            r_a, r_b = 11.5 + i * 0.28, 11.5 + (i + 1) * 0.28; za, zb = zf + j * 0.3, zf + (j + 1) * 0.3
            dep = 0.05 + 0.18 * abs(math.sin(i * 0.7 + j * 0.45) * math.sin(j * 0.33 + i * 0.2))
            g = Polygon([P(B, r_a, c1), P(B, r_b, c1)] + [P(B, r_b, c1) - d(c1 + 90) * dep, P(B, r_a, c1) - d(c1 + 90) * dep])
            kw += prism(g.intersection(NET[('GF', 'Cafe dining')].buffer(0.02)) if True else g, za, zb)
    kids.append(grp('GF', 'Cafe dining', 'Ipoh karst relief wall', 'TT Karst stone', [f for f in kw if f]))
    # labu sayong pendants + coffee ring slats
    lab_prof = [(0.0, 0.0), (0.12, 0.01), (0.2, 0.1), (0.2, 0.22), (0.15, 0.32), (0.06, 0.4), (0.045, 0.52), (0.06, 0.58), (0.0, 0.6)]
    lab_def = defn_box('Labu sayong pendant', 'smoked-black gourd pendant (lip, neck, body), warm light at the base',
                       [('TT Labu black', lathe(lab_prof, 20)), ('TT LED warm', cyl_faces(0, 0, 0.1, -0.01, 0.0, 12)), ('TT Black', beam([0, 0, 0.6], [0, 0, 1.6], 0.006, 0.006))])
    pend = []
    for r, f, h in [(12.2, 0.3, 2.35), (12.6, 0.62, 2.55), (13.4, 0.35, 2.2), (14.2, 0.7, 2.45), (15.1, 0.4, 2.3), (15.9, 0.66, 2.6), (16.7, 0.36, 2.25), (17.3, 0.6, 2.5)]:
        p = P(B, r, c0 + (c1 - c0) * f); pend.append(I(lab_def, [p[0], p[1], zf + h], [1, 0, 0]))
    ck.append(G('Labu sayong pendants (8)', None, None, None, pend))
    sl = []
    for k_ in range(16):
        r = 11.3 + k_ * 0.42; sl += prism(sector(B, r, r + 0.08, s0 + 0.6, c1 - 0.6, 30), ZG + 3.55, ZG + 3.75)
    ck.append(G('Coffee-brown ring slats', None, 'TT Coffee slat', sl))
    ck.append(G('Bulkhead + Perak light line', None, 'TT Perak caramel', prism(sector(B, R_VER + 0.2, R_VER + 0.26, c0 + 0.9, c1 - 0.9, 10), ZG + 3.36, ZG + 3.4)))
    nodes.append(G('CAFÉ – Perak (kopi putih, labu sayong, tin, karst)', None, None, None, [x for x in kids if x]))
    ceil.append(G('Café ceiling features', None, None, None, ck))
    # ---------- lobby (Perlis)
    LN = NET[('GF', 'Entrance lobby + info')]; MC = np.array([46.7, 23.6]); kids, ck = [], []
    kids.append(grp('GF', 'Entrance lobby + info', 'Simpul medallion ring', 'TT Brass inlay',
                    prism(Point(MC).buffer(1.2, 32).difference(Point(MC).buffer(1.17, 32)), zf, zf + 0.004) +
                    prism(Point(MC).buffer(0.36, 16).difference(Point(MC).buffer(0.33, 16)), zf, zf + 0.004), check=False))
    ll = []
    for k, (nm, b, m) in ST.items():
        seg = LineString([P(MC, 1.2, b), P(MC, 30, b)]).intersection(LN.buffer(-0.25))
        segs = [seg] if seg.geom_type == 'LineString' else list(getattr(seg, 'geoms', []))
        segs = [s for s in segs if s.distance(Point(P(MC, 1.2, b))) < 0.05]
        if not segs: continue
        s = segs[0]; ll += prism(s.buffer(0.012, cap_style=2), zf, zf + 0.004)
        end = np.array(s.coords[-1]); kids.append(G(f'Line-end light {nm}', None, m, cyl_faces(end[0], end[1], 0.07, zf, zf + 0.012, 12)))
    kids.append(G('Lobby: 11 brass lines from the knot', None, 'TT Brass inlay', ll))
    # curved bench along the small-ring wall, palms, totem
    bp = sector(S, 11.0, 11.5, 104, 128, 16)
    kids.append(grp('GF', 'Entrance lobby + info', 'Curved bench (solid surface)', 'TT Solid surface', prism(bp.intersection(LN), zf, zf + 0.45)))
    pal = D_planter_palm()
    for xy in ([44.2, 19.8], [49.1, 21.0]):
        kids.append(free(pal, 'GF', 'Entrance lobby + info', xy, zf, [0, 1], name='Palm in gold planter'))
    kids.append(free(D_boxu('Peta Rasa digital totem 600x80 h1900', 'route map screen', 0.6, 0.08, 1.9, 'TT Map screen'), 'GF', 'Entrance lobby + info', [48.9, 26.6], zf, [0, -1], name='Peta Rasa totem'))
    # ceiling: ring cove + Gua Kelam fins
    ck.append(G('Ring cove over the knot (GRG)', None, 'TT GRG white', prism(Point(MC).buffer(2.45, 32).difference(Point(MC).buffer(2.05, 32)), ZG + 3.5, ZG + 3.62)))
    ck.append(G('Ring cove light (warm)', None, 'TT LED warm', prism(Point(MC).buffer(2.08, 32).difference(Point(MC).buffer(2.05, 32)), ZG + 3.46, ZG + 3.5)))
    fins = []
    for k_ in range(44):
        b = k_ * 360 / 44 + 3; r = 2.75 + 0.3 * math.sin(k_ * 1.7); ln = 0.35 + 0.5 * abs(math.sin(k_ * 2.3)) ** 2
        c = P(MC, r, b)
        if not LN.buffer(-0.2).contains(Point(c)): continue
        a, e = c + d(b + 90) * 0.14, c - d(b + 90) * 0.14
        fins += prism(LineString([a, e]).buffer(0.015, cap_style=2), ZG + 3.95 - ln, ZG + 3.95)
    ck.append(G('Gua Kelam curtain fins (44, GRG)', None, 'TT GRG white', fins))
    nodes.append(G('LOBBY SIMPUL – Perlis (Gua Kelam, knot medallion)', None, None, None, [x for x in kids if x]))
    ceil.append(G('Lobby ceiling features', None, None, None, ck))
    # ---------- gates: Serambi Tengah (Selangor) + Gerbang Selatan (N9) + Timur (Pahang)
    kids, ck = [], []
    g0, g1 = mod(19)
    ck.append(G('Firefly soffit (dark)', None, 'TT Firefly soffit', prism(sector(B, R_VER + 0.1, R_OUT + 1.3, g0 + 0.5, g1 - 0.5, 20), ZSOF - 0.06, ZSOF - 0.01)))
    rng = np.random.default_rng(3); ff = []
    for i in range(260):
        r = R_VER + 0.4 + (R_OUT + 1.0 - R_VER - 0.4) * rng.random(); b = g0 + 1 + (g1 - g0 - 2) * ((i % 7) / 7 + 0.1 * math.sin(r * 1.3 + i))
        b = min(g1 - 0.8, max(g0 + 0.8, b)); p = P(B, r, b); s = 0.012 + 0.025 * rng.random() ** 3; zz = ZSOF - 0.07 - 0.4 * rng.random() ** 4
        ff += box(p[0] - s, p[1] - s, zz - s, p[0] + s, p[1] + s, zz + s)
    ck.append(G('Firefly points (260)', None, 'TT Firefly light', ff))
    mg = []
    for r, f in [(R_OUT - 0.5, 0.22), (R_OUT - 0.5, 0.78), (R_VER + 1.6, 0.22), (R_VER + 1.6, 0.78)]:
        p = P(B, r, g0 + (g1 - g0) * f); mg += cyl_faces(p[0], p[1], 0.1, zf + 0.9, ZSOF, 12)
        for k_ in range(6):
            q = p + d(k_ * 60 + 15) * 0.55; mid = (p * 2 + q) / 3
            mg += beam([q[0], q[1], zf], [mid[0], mid[1], zf + 0.55], 0.06, 0.06) + beam([mid[0], mid[1], zf + 0.55], [p[0], p[1], zf + 1.0], 0.06, 0.06)
    kids.append(G('Berembang root columns (4)', None, 'TT GRG white', mg))
    kids.append(G('Brass line 247.3° (Selangor) through the gate', None, 'TT Brass inlay',
                  prism(LineString([P(B, R_VER, 247.3), P(B, R_OUT + 2.0, 247.3)]).buffer(0.012, cap_style=2), zf, zf + 0.004)))
    hb = []
    for f in (0.1, 0.9):
        a = g0 + (g1 - g0) * f; hb += prism(sector(B, R_VER + 2.3, R_OUT - 1.4, a - 1.1, a + 1.1, 6), zf, zf + 0.5)
    kids.append(G('Ulam herb benches', None, 'TT Solid surface', hb))
    kids.append(G('Ulam herbs', None, 'TT Plant green', [f for a in (0.1, 0.9) for f in prism(sector(B, R_VER + 2.45, R_OUT - 1.55, g0 + (g1 - g0) * a - 0.9, g0 + (g1 - g0) * a + 0.9, 6), zf + 0.5, zf + 0.62)]))
    nodes.append(G('SERAMBI TENGAH – Selangor (fireflies, berembang)', None, None, None, kids))
    ceil.append(G('Serambi Tengah ceiling features', None, None, None, ck))
    # Gerbang Selatan
    kids = []; g0, g1 = mod(17); rr = R_OUT + 1.45
    W = math.radians(g1 - g0) * rr; top = []
    for i in range(41):
        u = i / 40; x = (u - 0.5) * 2; top.append([*P(B, rr, g0 + (g1 - g0) * u), ZSOF + 0.55 + 0.25 * x * x + 1.9 * abs(x) ** 6])
    fr = []
    for p, q in zip(top[:-1], top[1:]): fr += beam(p, q, 0.16, 0.16)
    for u in (0.04, 0.96):
        p = P(B, rr, g0 + (g1 - g0) * u); fr += beam([p[0], p[1], 0.3], [p[0], p[1], ZSOF + 0.75], 0.18, 0.18)
    kids.append(G('Gonjong portal (bronze PVD)', None, 'TT NSembilan bronze', fr))
    led = []
    for p, q in zip(top[:-1], top[1:]): led += beam([p[0], p[1], p[2] - 0.2], [q[0], q[1], q[2] - 0.2], 0.04, 0.04)
    kids.append(G('Gonjong rim light', None, 'TT LED warm', led))
    gt = top[20]; sg = []
    for sgn in (-1, 1):
        a = P(B, rr, (g0 + g1) / 2 + sgn * 3.2); e = P(B, rr, (g0 + g1) / 2 - sgn * 0.7)
        sg += beam([a[0], a[1], ZSOF + 0.62], [e[0], e[1], ZSOF + 1.75], 0.05, 0.05)
    kids.append(G('Silang gunting (crossed gable)', None, 'TT NSembilan bronze', sg))
    pl = []                        # tengkolok pleated soffit: zig-zag strips
    nfold = 12
    for k_ in range(nfold):
        a0_, a1_ = g0 + 0.5 + (g1 - g0 - 1) * k_ / nfold, g0 + 0.5 + (g1 - g0 - 1) * (k_ + 1) / nfold; am = (a0_ + a1_) / 2
        for (aa, ab, za, zb) in ((a0_, am, 0.0, 0.28), (am, a1_, 0.28, 0.0)):
            V = [[*P(B, R_VER + 0.2, aa), ZSOF - 0.05 - za], [*P(B, R_OUT + 1.3, aa), ZSOF - 0.05 - za], [*P(B, R_OUT + 1.3, ab), ZSOF - 0.05 - zb], [*P(B, R_VER + 0.2, ab), ZSOF - 0.05 - zb]]
            f = F(V);  pl += [f] if f else []
            if f: g2 = F(V[::-1]); pl += [g2] if g2 else []
    nodes.append(G('GERBANG SELATAN – Negeri Sembilan (gonjong, tengkolok)', None, None, None, kids +
                   [G('Brass line 213.3° (N. Sembilan)', None, 'TT Brass inlay', prism(LineString([P(B, R_VER, 213.3), P(B, R_OUT + 2.5, 213.3)]).buffer(0.012, cap_style=2), zf, zf + 0.004))]))
    ceil.append(G('Gerbang Selatan pleated soffit', None, 'TT Star screen', pl))
    # Timur gate (Pahang): patin-silver portal lining + line
    g0, g1 = mod(9)
    nodes.append(G('GERBANG TIMUR – Pahang', None, None, None, [
        G('Brass line 68.4° (Pahang)', None, 'TT Brass inlay', prism(LineString([P(B, R_VER, 68.4), P(B, R_OUT + 2.0, 68.4)]).buffer(0.012, cap_style=2), zf, zf + 0.004)),
        G('Patin-silver portal lining', None, 'TT Tin', prism(sector(B, R_OUT - 0.05, R_OUT + 0.1, g0 + 0.6, g1 - 0.6, 12), ZG + 3.6, ZSOF))]))
    # ---------- info + first aid
    kids = []
    kids.append(on_outer(D_counter(2.4, 0.7, 1.05, 'TT Solid surface', 'TT Solid surface'), 'GF', 'Info / security / wheelchair loan', B, 226.5, 13.0, zf, name='Info counter'))
    kids.append(on_outer(D_counter(1.0, 0.7, 0.8, 'TT Solid surface', 'TT Solid surface'), 'GF', 'Info / security / wheelchair loan', B, 231.8, 13.0, zf, name='Low counter 800 (MS 1184)'))
    kids.append(on_radial(D_rack(1.2, 0.6, 1.2, 3), 'GF', 'Info / security / wheelchair loan', B, 13.4, 236, 'hi', zf, name='Wheelchair loan bay'))
    kids.append(on_outer(D_bed(), 'GF', 'First aid', B, 223.8, 16.5, zf, gap=0.0, name='Treatment bed'))
    kids.append(on_outer(D_sink_counter(1.2, 0.6, 0.9, 'TT Solid surface', 'TT GRG white', 1, 'clinic'), 'GF', 'First aid', B, 233.5, 16.5, zf, name='Clinical sink'))
    kids.append(on_radial(D_desk(1.2), 'GF', 'First aid', B, 16.0, 236.0, 'hi', zf, name='Desk'))
    kids.append(on_radial(D_boxu('Medicine cabinet 900x450 h1900', 'lockable', 0.9, 0.45, 1.9, 'TT GRG white'), 'GF', 'First aid', B, 15.3, 222.0, 'lo', zf, name='Cabinet'))
    nodes.append(G('INFO + FIRST AID', None, None, None, [x for x in kids if x]))
    return nodes, ceil

# ================================================================== WC builder (any ring sector)
def cubicle_row_outer(level, rname, C, b0, b1, zf, widths, depth=1.5, pwd_idx=()):
    """cubicles along the outer arc between bearings b0..b1 (bearings measured at the cubicle front).
    widths: list of widths (m) measured at the front line. Returns (nodes, bearings of WC centres)."""
    n_ = NET[(level, rname)]; bc = (b0 + b1) / 2
    r_out = rspan(n_, C, bc, (rspan(n_, C, bc, 0.5 * sum(rspan(n_, C, bc, 99) if False else (0, 0)) or 1)[1] if False else 0) or 0, 0) if False else None
    return None

def wc_sector(level, rname, C, layout, zf):
    """generic WC/ablution room fit-out inside a ring sector. layout: dict with keys
       cub: (side, r_front_from_outer, [widths], pwd_set)  -> cubicles on the outer arc
       uri: (side 'lo'|'hi', r0, n)  urinals on a radial wall
       van: (side, r_centre, L)      vanity on a radial wall
       extra: list of callables"""
    n_ = NET[(level, rname)]; kids = []
    rr = [r for r in ROOMS if r['level'] == level and r['name'] == rname][0]['poly']
    # sector bearings from the polygon
    pts = np.array(rr.exterior.coords); brg = (np.degrees(np.arctan2(pts[:, 0] - C[0], pts[:, 1] - C[1])) % 360)
    if brg.max() - brg.min() > 180: brg = np.where(brg < 180, brg + 360, brg)
    b0, b1 = brg.min(), brg.max(); bc = (b0 + b1) / 2
    r_in, r_out = rspan(n_, C, bc, np.linalg.norm(np.array(rr.centroid.coords[0]) - C))
    if 'cub' in layout:
        widths, depth, pwd = layout['cub']
        rf = r_out - depth                                         # cubicle front radius
        s0, s1 = tspan(n_, C, rf, bc); tot = sum(widths); s = (s0 + s1) / 2 - tot / 2
        if tot > (s1 - s0) + 1e-6: raise ValueError(f'{rname}: cubicles {tot:.2f} > {s1 - s0:.2f}')
        pf = P(C, rf, bc); t = d(bc + 90); u = -d(bc)          # u = from front towards the outer wall
        part, doors, wcs = [], [], []
        edges = [s]
        for w in widths: edges.append(edges[-1] + w)
        for k, e in enumerate(edges):
            if k in (0, len(edges) - 1):
                # end panels only if not touching a wall
                if (k == 0 and e - s0 < 0.05) or (k == len(edges) - 1 and s1 - e < 0.05): continue
            a = pf + t * e; bpt = a + u * depth
            # extend to the outer wall face
            hit = LineString([a, a + u * (depth + 1.0)]).intersection(n_.exterior)
            if not hit.is_empty:
                hp = min([np.array(g.coords[0]) for g in ([hit] if hit.geom_type == 'Point' else list(hit.geoms))], key=lambda q: np.linalg.norm(q - a)); bpt = hp
            part += beam([a[0], a[1], zf + 0.15], [bpt[0], bpt[1], zf + 0.15], 0.025, 0.0001)[:0] + prism(LineString([a, bpt]).buffer(0.0125, cap_style=2), zf + 0.15, zf + 2.1)
        for k, w in enumerate(widths):
            a, e = pf + t * (edges[k] + 0.06), pf + t * (edges[k + 1] - 0.06)
            front = prism(LineString([a, e]).buffer(0.0125, cap_style=2), zf + 0.15, zf + 2.1)
            if k in pwd: doors += front
            else: doors += front
            mid = pf + t * (edges[k] + edges[k + 1]) / 2
            # WC on the outer wall, centred (PwD: 450 from side wall)
            back = mid + u * depth
            hit = LineString([mid, mid + u * (depth + 1.0)]).intersection(n_.exterior)
            if not hit.is_empty:
                back = min([np.array(g.coords[0]) for g in ([hit] if hit.geom_type == 'Point' else list(hit.geoms))], key=lambda q: np.linalg.norm(q - mid))
            if k in pwd:
                back = back + t * ((edges[k + 1] - edges[k]) / 2 - 0.5)
            kids.append(reg(level, rname, inst(D_wc(), [back[0], back[1], zf], [*(-u), 0], name='WC' + (' PwD' if k in pwd else '')), 'WC'))
            if k in pwd:
                kids.append(inst(D_grab(), [back[0], back[1], zf], [*(-u), 0], name='Grab bars'))
                bas = mid - t * ((edges[k + 1] - edges[k]) / 2 - 0.03) + u * 0.35
                kids.append(inst(D_boxu('PwD basin 500x400 h830', 'wall basin', 0.5, 0.4, 0.83, 'TT Sanitary white', base=0.68), [bas[0], bas[1], zf], [*t, 0], name='PwD basin'))
        kids.append(grp(level, rname, 'Cubicle partitions (HPL 25)', 'TT HPL partition', part, check=False))
        kids.append(grp(level, rname, 'Cubicle doors (HPL 25)', 'TT HPL partition', doors, check=False))
        layout['_front'] = rf
    if 'uri' in layout:
        side, r0, n = layout['uri']
        for k in range(n):
            kids.append(on_radial(D_urinal(), level, rname, C, r0 + k * 0.75, bc, side, zf, name='Urinal'))
    if 'van' in layout:
        side, rc, L = layout['van']
        kids.append(on_radial(D_vanity(L), level, rname, C, rc, bc, side, zf, name='Vanity'))
        kids.append(on_radial(D_dryer(), level, rname, C, rc + L / 2 + 0.35, bc, side, zf, name='Hand dryer'))
    for f in layout.get('extra', []):
        kids.append(f(n_, C, bc, r_in, r_out))
    return G(f'{rname} – fit-out', None, None, None, [x for x in kids if x])

# ================================================================== GF WCs + family + service
def gf_wet_service():
    zf = ZG + 0.02; nodes = []
    nodes.append(wc_sector('GF', 'Male restroom (bank 1)', B, dict(cub=([1.75, 0.95, 0.95], 1.5, {0}), uri=('hi', 12.9, 3), van=('lo', 13.3, 1.6)), zf))
    nodes.append(wc_sector('GF', 'Female restroom (bank 1)', B, dict(cub=([1.75, 0.95, 0.95], 1.5, {0}), van=('lo', 13.3, 1.6),
                                                                     extra=[lambda n_, C, bc, ri, ro: on_radial(D_counter(1.4, 0.5, 0.85, 'TT Solid surface', 'TT HPL partition'), 'GF', 'Female restroom (bank 1)', C, 13.6, bc, 'hi', zf, name='Bag + baby shelf')]), zf))
    # nappy change + nursing
    nodes.append(G('Nappy change – fit-out', None, None, None, [
        on_radial(D_counter(1.6, 0.6, 0.9, 'TT Cushion warm', 'TT HPL partition'), 'GF', 'Nappy change (family room)', B, 12.6, 341.3, 'hi', zf, name='Changing counter'),
        on_radial(D_bench(1.2, 0.4), 'GF', 'Nappy change (family room)', B, 12.0, 341.3, 'lo', zf, name='Bench')]))
    nodes.append(G('Nursing room – fit-out', None, None, None, [
        on_outer(D_armchair(), 'GF', 'Nursing room (family room)', B, 338.6, 16.5, zf, name='Nursing chair'),
        on_outer(D_armchair(), 'GF', 'Nursing room (family room)', B, 344.2, 16.5, zf, name='Nursing chair'),
        on_radial(D_sink_counter(1.0, 0.55, 0.9, 'TT Solid surface', 'TT HPL partition', 1, 'nursing'), 'GF', 'Nursing room (family room)', B, 15.4, 341.3, 'hi', zf, name='Sink + bottle warmer'),
        on_radial(D_FRIDGE1(), 'GF', 'Nursing room (family room)', B, 15.2, 341.3, 'lo', zf, name='Milk fridge')]))
    # staff WCs (small ring)
    nodes.append(wc_sector('GF', 'Staff restroom F', S, dict(cub=([0.95, 0.95, 0.95, 1.0], 1.45, set()), van=('lo', 6.4, 1.6),
                                                            extra=[lambda n_, C, bc, ri, ro: on_radial(D_LOCKER(1.8), 'GF', 'Staff restroom F', C, 6.6, bc, 'hi', zf, name='Lockers')]), zf))
    nodes.append(wc_sector('GF', 'Staff restroom M', S, dict(cub=([0.95, 0.95, 1.0], 1.45, set()), uri=('hi', 5.6, 2), van=('lo', 6.4, 1.6),
                                                            extra=[lambda n_, C, bc, ri, ro: on_outer(D_LOCKER(1.2), 'GF', 'Staff restroom M', C, bc + 17, 9.0, zf, name='Lockers')]), zf))
    # service
    sv = []
    for k, b in enumerate((232, 240, 247)):
        sv.append(on_outer(D_MDB(), 'GF', 'Main distribution board', S, b, 9.0, zf, name='Switchboard'))
    sv.append(on_outer(D_genset(), 'GF', 'Generator set', S, 280.7, 9.0, zf, gap=0.6, name='Genset'))
    sv.append(on_outer(D_LOCKER(1.2), 'GF', "Cleaner's rest", S, 258, 9.0, zf, name='Lockers'))
    sv.append(free(D_table_rect(1.2, 0.75), 'GF', "Cleaner's rest", P(S, 7.4, 261.5), zf, d(261.5), name='Table'))
    for j, off in enumerate((-0.45, 0.45)):
        q = P(S, 7.4, 261.5) + d(261.5 + 90) * off
        sv.append(free(D_chair(), 'GF', "Cleaner's rest", q + d(261.5) * 0.85, zf, -d(261.5), name='Chair'))
    for b in (295.5, 303.5):
        sv.append(on_outer(D_rack(1.6, 0.5, 2.0), 'GF', 'Housekeeping store', S, b, 9.0, zf, name='Rack'))
    sv.append(on_outer(D_mop(), 'GF', 'Janitor', S, 311.9, 8.0, zf, name='Mop sink'))
    sv.append(on_outer(D_desk(1.6), 'GF', 'Loading bay reception', S, 344.0, 9.0, zf, name='Receiving desk'))
    sv.append(free(D_boxu('Platform scale 800x800', 'goods scale', 0.8, 0.8, 0.12, 'TT Equipment grey'), 'GF', 'Loading bay reception', P(S, 7.3, 337.0), zf, d(337), name='Scale'))
    for k, b in enumerate((3.5, 8.5, 13.5)):
        sv.append(on_outer(D_bin('660'), 'GF', 'Refuse wet', S, b, 9.0, zf, gap=0.05, name='Bin 660 L'))
    sv.append(on_radial(D_sink_counter(1.0, 0.6, 0.9, nsink=1, label='wash-down'), 'GF', 'Refuse wet', S, 6.0, 10.0, 'lo', zf, name='Wash-down sink'))
    for k, (b, kind) in enumerate([(27, 'blue'), (31, 'orange'), (35, 'brown'), (39, 'blue')]):
        sv.append(on_outer(D_bin(kind), 'GF', 'Refuse dry / recycle', S, b, 9.0, zf, gap=0.05, name=f'Recycling {kind}'))
    for b in (50, 58):
        sv.append(on_outer(D_rack(1.8, 0.5, 2.0), 'GF', 'Dry store', S, b, 9.0, zf, name='Rack'))
    sv.append(on_outer(D_coldroom(), 'GF', 'Freezer / wet store', S, 71.5, 9.0, zf, gap=0.05, name='Cold room'))
    sv.append(on_outer(D_SERVER(), 'GF', 'LAN room', S, 87.1, 9.0, zf, name='Server rack'))
    nodes.append(G('SERVICE ROOMS – equipment', None, None, None, [x for x in sv if x]))
    return nodes

# ================================================================== L1
def l1_interior():
    zf = ZL + 0.02; nodes, ceil = [], []
    # ---------- gallery (Penang): oval portals, tile runner, jetty edges, vitrines, map
    b0, b1 = mod(8); bc = (b0 + b1) / 2; kids, ck = [], []
    gn = NET[('L1', 'Gallery exhibition')]
    kids.append(G('Encaustic tile runner (five-foot way)', None, 'TT Encaustic tile', prism(sector(B, R_VER + 0.4, R_L1 - 0.4, bc - 2.4, bc + 2.4, 10).intersection(gn), zf, zf + 0.004)))
    for a, c in ((b0 + 0.6, b0 + 2.2), (b1 - 2.2, b1 - 0.6)):
        kids.append(G('Jetty boardwalk edge (chengal)', None, 'TT Chengal', prism(sector(B, R_VER + 0.4, R_L1 - 0.4, a, c, 10).intersection(gn), zf, zf + 0.006)))
    portals = []
    for r in (12.6, 14.6, 16.6, 18.6):
        wr = math.radians(b1 - b0) * r; op = 1.25 + (r - 12.6) * 0.07; hTop = 3.4 + (r - 12.6) * 0.12; zt = zdeck(r) - 0.05
        bands = []
        zs = [zf, zf + hTop - op] + [zf + hTop - op + op * math.sin(math.pi / 2 * k / 8) for k in range(1, 9)] + [zt]
        for za, zb in zip(zs[:-1], zs[1:]):
            zm = (za + zb) / 2 - zf; wall = sector(B, r - 0.11, r + 0.11, b0 - 0.5, b1 + 0.5, 24).intersection(gn.buffer(0.05))
            if zm < hTop - op: half = op
            elif zm < hTop: half = math.sqrt(max(0, op ** 2 - (zm - (hTop - op)) ** 2))
            else: half = 0
            if half > 0.02:
                da = math.degrees(half / r); wall = wall.difference(sector(B, r - 0.2, r + 0.2, bc - da, bc + da, 12))
            bands.append((za, zb, wall))
        from m3d import bsolid
        portals.append(G(f'Oval portal r={r:g} (GRG)', None, 'TT GRG white', bsolid([(a, c, clean(g)) for a, c, g in bands])))
        # bronze ring at the opening edge + warm line
        ring = []
        pts = []
        for k in range(25):
            th = math.pi * k / 24; half = op * math.cos(th); zz = hTop - op + op * math.sin(th) if True else 0
            pts.append(P(B, r - 0.12, bc - math.degrees(half / r)).tolist() + [zf + zz])
        pts = [P(B, r - 0.12, bc - math.degrees(op / r)).tolist() + [zf]] + pts + [P(B, r - 0.12, bc + math.degrees(op / r)).tolist() + [zf]]
        for p, q in zip(pts[:-1], pts[1:]): ring += beam(p, q, 0.04, 0.04)
        ck.append(G(f'Portal light ring r={r:g}', None, 'TT LED warm', ring))
        for side in (-1, 1):
            a = bc + side * ((b1 - b0) / 2 - 1.3); p = P(B, r + 0.85, a)
            kids.append(free(D_boxu('Vitrine base 700x700 h850 (bronze)', 'display plinth', 0.7, 0.7, 0.85, 'TT Bronze PVD'), 'L1', 'Gallery exhibition', p + d(a) * 0.35, zf, -d(a), name='Vitrine base'))
            kids.append(G('Vitrine glass', None, 'TT Mint glass', box_faces(p[0] - 0.33, p[1] - 0.33, zf + 0.85, p[0] + 0.33, p[1] + 0.33, zf + 1.55)))
    kids += portals
    mp = P(B, R_L1 - 0.9, bc)
    kids.append(free(D_boxu('Peta Rasa route map 2400x120 h3200 (lit)', 'freestanding lit map of the 11 routes', 2.4, 0.12, 3.6, 'TT Map screen', base=0.4), 'L1', 'Gallery exhibition', mp, zf, -d(bc), name='Peta Rasa map'))
    kids.append(free(D_bench(1.6, 0.45, 0.45, 'TT Chengal'), 'L1', 'Gallery exhibition', P(B, 19.6, bc), zf, d(bc), name='Bench'))
    nodes.append(G('GALLERY PETA RASA – Pulau Pinang', None, None, None, [x for x in kids if x])); ceil.append(G('Gallery light rings', None, None, None, ck))
    # ---------- MPH Dapur Rewang (Kedah)
    kids, ck = [], []; hb0, hb1 = 94.3, 130.3
    kids.append(grp('L1', 'Multipurpose hall (Dapur Rewang)', 'Communal rewang island (green)', 'TT Kedah green', prism(sector(B, 15.6, 16.6, 97, 126, 30), zf + 0.1, zf + 0.88)))
    kids.append(G('Island top (solid surface)', None, 'TT Solid surface', prism(sector(B, 15.56, 16.64, 96.8, 126.2, 30), zf + 0.88, zf + 0.92)))
    kids.append(G('Island plinth', None, 'TT Black', prism(sector(B, 15.68, 16.52, 97.3, 125.7, 30), zf, zf + 0.1)))
    hobs = []
    for k in range(6):
        p = P(B, 16.1, 99.5 + k * 4.5); hobs += box_faces(p[0] - 0.3, p[1] - 0.25, zf + 0.92, p[0] + 0.3, p[1] + 0.25, zf + 0.925)
    kids.append(G('Induction hobs (6)', None, 'TT Black', hobs))
    kp = P(B, 16.1, 124.0); kids.append(G('Kawah wok', None, 'TT Steel dark', lathe([(0.0, zf + 0.93), (0.3, zf + 0.97), (0.48, zf + 1.13), (0.44, zf + 1.15), (0.0, zf + 1.15)], 20, kp[0], kp[1])))
    for a in (100.5, 106.5, 112.5):   # kenduri tables + benches (radial)
        if a > 111.5: continue
        p0, p1 = P(B, 11.8, a), P(B, 14.6, a); mid = (p0 + p1) / 2; L_ = np.linalg.norm(p1 - p0)
        kids.append(free(D_table_rect(L_, 0.84, 0.76, 'TT Timber oak'), 'L1', 'Multipurpose hall (Dapur Rewang)', mid, zf, d(a + 90), name='Kenduri table'))
        for sgn in (-1, 1):
            kids.append(free(D_bench(L_, 0.32, 0.46, 'TT Timber oak'), 'L1', 'Multipurpose hall (Dapur Rewang)', mid + d(a + 90) * sgn * 0.88, zf, d(a + 90) * (-sgn), name='Bench'))
    kids.append(on_outer(D_sink_counter(2.4, 0.7, 0.9, nsink=2, label='hall'), 'L1', 'Multipurpose hall (Dapur Rewang)', B, 113.0, 20.0, zf, name='Wash-up sinks'))
    kids.append(on_outer(D_FRIDGE(), 'L1', 'Multipurpose hall (Dapur Rewang)', B, 117.0, 20.0, zf, name='Chiller'))
    bf = {}
    for k in range(15):
        r = 12.2 + k * 0.62; zb = zdeck(r) - 0.75 - k * 0.07; pts = [P(B, r + 0.22 * math.sin(i / 50 * 9 + k * 0.8), hb0 + 1 + (hb1 - hb0 - 2) * i / 50) for i in range(51)]
        g = LineString(pts).buffer(0.02, cap_style=2).intersection(NET[('L1', 'Multipurpose hall (Dapur Rewang)')].buffer(-0.05))
        col = 'TT Kedah green' if k < 5 else ('TT Plant green' if k < 10 else 'TT Kedah gold')
        bf.setdefault(col, []).extend(prism(clean(g), zb, zb + 0.42))
    for c, fs in bf.items(): ck.append(G(f'Sawah terrace baffles ({c.replace("TT ", "")})', None, c, fs))
    pend = []
    for k in range(6):
        p = P(B, 16.1, 99.5 + k * 4.5); pend += lathe([(0.0, zf + 2.6), (0.26, zf + 2.6), (0.12, zf + 2.8), (0.0, zf + 2.8)], 16, p[0], p[1]) + beam([p[0], p[1], zf + 2.8], [p[0], p[1], zdeck(16.1) - 0.02], 0.006, 0.006)
    ck.append(G('Island pendants', None, 'TT Black', pend))
    # furniture store: stacked chairs + folded tables ; equipment store racks
    kids.append(on_outer(D_rack(2.0, 0.6, 2.0), 'L1', 'MPH furniture store', B, 116.5, 13.5, zf, name='Folding table rack'))
    kids.append(on_outer(D_boxu('Stacked chairs 500x500 h1600', 'stack of 15', 0.5, 0.5, 1.6, 'TT Upholstery'), 'L1', 'MPH furniture store', B, 122.5, 13.5, zf, name='Chair stack'))
    kids.append(on_outer(D_boxu('Stacked chairs 500x500 h1600', 'stack of 15', 0.5, 0.5, 1.6, 'TT Upholstery'), 'L1', 'MPH furniture store', B, 125.0, 13.5, zf, name='Chair stack'))
    for b in (81, 88):
        kids.append(on_outer(D_rack(1.8, 0.6, 2.0), 'L1', 'MPH equipment store', B, b, 20.0, zf, name='AV / kitchen equipment rack'))
    nodes.append(G('DAPUR REWANG – Kedah (sawah baffles, rewang island)', None, None, None, [x for x in kids if x])); ceil.append(G('Dapur Rewang ceiling', None, None, None, ck))
    # gallery store / staff / J-L
    gs = [on_outer(D_rack(2.0, 0.6, 2.2), 'L1', 'Gallery storage', B, 61.5, 19.0, zf, name='Art rack'),
          on_outer(D_boxu('Plan chest 1300x950 h900', 'flat files', 1.3, 0.95, 0.9, 'TT Equipment grey'), 'L1', 'Gallery storage', B, 65.0, 19.0, zf, name='Plan chest'),
          on_outer(D_desk(1.4), 'L1', 'Gallery staff', B, 70.1, 19.0, zf, name='Desk'),
          on_inner(D_LOCKER(0.9), 'L1', 'Gallery staff', B, 70.1, 13.0, zf, name='Lockers'),
          on_outer(D_mop(), 'L1', 'Janitor + LAN', B, 74.4, 19.0, zf, name='Mop sink'),
          on_radial(D_SERVER(), 'L1', 'Janitor + LAN', B, 13.5, 74.4, 'lo', zf, name='Floor rack')]
    oc = gs[2]
    if oc:
        p = np.array(oc['o'][:2]) + np.array(oc['y'][:2]) * 0.95
        gs.append(free(D_officechair(), 'L1', 'Gallery staff', p, zf, -np.array(oc['y'][:2]), name='Chair'))
    nodes.append(G('GALLERY SUPPORT ROOMS', None, None, None, [x for x in gs if x]))
    # L1 WC bank 2 + janitor
    nodes.append(wc_sector('L1', 'Male restroom (bank 2)', B, dict(cub=([1.1, 1.1], 1.5, set()), uri=('hi', 14.4, 2), van=('lo', 13.0, 1.2)), zf))
    nodes.append(wc_sector('L1', 'Female restroom (bank 2)', B, dict(cub=([1.1, 1.1], 1.5, set()), van=('lo', 13.0, 1.2),
                                                                     extra=[lambda n_, C, bc, ri, ro: on_radial(D_bench(1.2, 0.4), 'L1', 'Female restroom (bank 2)', C, 15.6, bc, 'hi', zf, name='Bench')]), zf))
    nodes.append(G('Janitor (WC L1) – fit-out', None, None, None, [on_outer(D_mop(), 'L1', 'Janitor (WC L1)', B, 146.9, 19.0, zf, name='Mop sink'),
                                                               on_radial(D_rack(1.0, 0.35, 2.0, 5), 'L1', 'Janitor (WC L1)', B, 15.0, 146.9, 'lo', zf, name='Shelf')]))
    # ---------- admin
    kids = []
    rq = 'Admin reception + waiting'
    kids.append(on_outer(D_counter(1.8, 0.7, 1.05, 'TT Solid surface', 'TT Timber oak'), 'L1', rq, S, 103.5, 8.0, zf, name='Reception counter'))
    kids.append(on_outer(D_counter(0.9, 0.7, 0.8, 'TT Solid surface', 'TT Timber oak'), 'L1', rq, S, 108.6, 8.0, zf, name='Low counter (MS 1184)'))
    for b in (90, 95):
        kids.append(on_outer(D_armchair('TT Upholstery'), 'L1', rq, S, b, 8.0, zf, gap=0.02, name='Waiting chair'))
    rO = 'Main office'
    for k, b in enumerate((50.5, 58.0, 65.5, 73.0, 80.0)):
        dk = on_outer(D_desk(1.4, 0.7), 'L1', rO, S, b, 9.0, zf, name='Workstation')
        kids.append(dk)
        if dk:
            p = np.array(dk['o'][:2]) + np.array(dk['y'][:2]) * 0.95
            kids.append(free(D_officechair(), 'L1', rO, p, zf, -np.array(dk['y'][:2]), name='Office chair'))
    kids.append(on_inner(D_boxu('Filing cabinets 1600x450 h1100', '4 x lateral files', 1.6, 0.45, 1.1, 'TT Equipment grey'), 'L1', rO, S, 64.8, 6.0, zf, gap=0.05, name='Files'))
    rM = "Manager's office"
    dk = on_outer(D_desk(1.6, 0.8), 'L1', rM, S, 150.8, 8.0, zf, name='Manager desk'); kids.append(dk)
    if dk:
        y = np.array(dk['y'][:2]); o = np.array(dk['o'][:2])
        kids.append(free(D_officechair(), 'L1', rM, o + y * 0.2 + y * 0.0 - y * 0.0 + np.array(dk['x'][:2]) * 0.0 + y * 0.0 + (-y) * 0.0 + y * 0.0 + y * 0.0, zf, y, name='Manager chair', check=False) if False else None)
        kids.append(free(D_chair(), 'L1', rM, o + y * 1.65 + np.array(dk['x'][:2]) * 0.35, zf, -y, name='Visitor chair'))
        kids.append(free(D_chair(), 'L1', rM, o + y * 1.65 - np.array(dk['x'][:2]) * 0.35, zf, -y, name='Visitor chair'))
    kids.append(on_radial(D_boxu('Credenza 1600x450 h750', 'low storage', 1.6, 0.45, 0.75, 'TT Timber oak'), 'L1', rM, S, 6.6, 150.8, 'hi', zf, name='Credenza'))
    rP = 'Pantry'
    kids.append(on_outer(D_sink_counter(2.4, 0.6, 0.9, 'TT Solid surface', 'TT Timber oak', 1, 'pantry'), 'L1', rP, S, 170.8, 8.0, zf, name='Pantry counter'))
    kids.append(on_radial(D_FRIDGE1(), 'L1', rP, S, 8.6, 170.8, 'lo', zf, name='Fridge'))
    kids.append(free(D_table_round(0.45), 'L1', rP, P(S, 6.9, 170.8), zf, d(0), name='Table'))
    for j in range(3):
        kids.append(free(D_stool('TT Cushion warm'), 'L1', rP, P(S, 6.9, 170.8) + d(j * 120 + 60) * 0.7, zf, d(0), name='Stool'))
    rMt = 'Meeting room'; bm = 192.3; pc = P(S, 7.6, bm)
    kids.append(free(D_table_rect(2.4, 1.1), 'L1', rMt, pc, zf, d(bm + 90), name='Meeting table'))
    for i, (u, v) in enumerate([(-0.75, 1), (0.0, 1), (0.75, 1), (-0.75, -1), (0.0, -1), (0.75, -1)]):
        q = pc + d(bm) * u + d(bm + 90) * v * 0.85
        kids.append(free(D_chair(), 'L1', rMt, q + d(bm + 90) * v * 0.25, zf, -d(bm + 90) * v, name='Chair'))
    kids.append(on_outer(D_SCREEN(), 'L1', rMt, S, bm, 9.0, zf, name='Screen'))
    kids.append(on_outer(D_rack(1.0, 0.45, 2.0), 'L1', 'Office store', S, 209.8, 8.0, zf, name='Rack'))
    nodes.append(G('ADMIN – reception, office, manager, pantry, meeting', None, None, None, [x for x in kids if x]))
    nodes.append(wc_sector('L1', 'Staff toilet (admin)', S, dict(cub=([1.3], 1.5, set()), van=('lo', 6.3, 0.8)), zf))
    # ---------- musolla
    for rname in ('Male prayer + ablution', 'Female prayer + ablution'):
        kids = []; n_ = NET[('L1', rname)]
        pr = [r for r in ROOMS if r['level'] == 'L1' and r['name'] == rname][0]['poly']
        pts = np.array(pr.exterior.coords); brg = (np.degrees(np.arctan2(pts[:, 0] - S[0], pts[:, 1] - S[1])) % 360); b0_, b1_ = brg.min(), brg.max(); bcm = (b0_ + b1_) / 2
        kids.append(on_inner(D_ablution(2.8), 'L1', rname, S, bcm, 6.0, zf, name='Ablution bench'))
        kids.append(grp('L1', rname, 'Low screen (ablution | carpet)', 'TT GRG white', prism(sector(S, 6.05, 6.17, bcm - 12, bcm + 12, 10), zf, zf + 1.1)))
        carpet = n_.intersection(sector(S, 6.3, RS_OUT + 0.2, b0_ - 1, b1_ + 1, 30)).buffer(-0.05)
        kids.append(G('Prayer carpet', None, 'TT Carpet sage', prism(clean(carpet), zf, zf + 0.012)))
        saf = []; qv = d(QIBLA); qt = d(QIBLA + 90)
        cc = np.array(carpet.centroid.coords[0])
        far = max(float(np.dot(np.array(p) - cc, qv)) for p in carpet.exterior.coords)
        for k in range(6):
            off = far - 1.0 - k * 1.2; c0 = cc + qv * off
            seg = LineString([c0 - qt * 15, c0 + qt * 15]).intersection(carpet.buffer(-0.15))
            for s in ([seg] if seg.geom_type == 'LineString' else list(getattr(seg, 'geoms', []))):
                if s.length > 0.6: saf += prism(s.buffer(0.02, cap_style=2), zf + 0.012, zf + 0.015)
        kids.append(G('Saf lines (1.2 m, square to qibla 292.3°)', None, 'TT Star screen', saf))
        if rname.startswith('Male'):
            sc = sector(S, RS_OUT - 0.13 - 0.1, RS_OUT - 0.13 - 0.07, QIBLA - 3.0, QIBLA + 3.0, 8)
            kids.append(G('Lit 8-point star screen (behind mihrab panel)', None, 'TT Star screen', prism(sc, zf + 2.62, zf + 3.4)))
            sl = []
            for sgn in (-1, 1):
                for k in (1, 2, 3):
                    p = P(S, RS_OUT - 0.2, QIBLA + sgn * (7 + k * 3.2)); sl += box_faces(p[0] - 0.012, p[1] - 0.012, zf + 0.4, p[0] + 0.012, p[1] + 0.012, zf + 3.5)
            kids.append(G('Slit lights (6)', None, 'TT LED warm', sl))
        else:
            mk = P(S, 9.9, bcm)
            kids.append(G('Qibla marker plate (brass, floor)', None, 'TT Brass inlay', prism(LineString([mk, mk + d(QIBLA) * 0.5]).buffer(0.05, cap_style=2).intersection(n_), zf + 0.012, zf + 0.016)))
        kids.append(on_outer(D_plant(), 'L1', rname, S, b0_ + 4, 9.5, zf, gap=0.1, name='Plant'))
        kids.append(on_outer(D_plant(), 'L1', rname, S, b1_ - 4, 9.5, zf, gap=0.1, name='Plant'))
        nodes.append(G(f'MUSOLLA – {rname}', None, None, None, [x for x in kids if x]))
    # shoe foyer + musolla janitor
    kids = []
    for b in (8.0, 20.0):
        kids.append(on_outer(D_shoerack(2.0), 'L1', 'Musolla foyer + shoe racks', S, b, 9.0, zf, name='Shoe rack'))
    kids.append(on_outer(D_bench(1.6, 0.4), 'L1', 'Musolla foyer + shoe racks', S, 29.5, 9.0, zf, name='Bench'))
    kids.append(on_outer(D_mop(), 'L1', 'Musolla janitor', S, 40.3, 9.0, zf, name='Mop sink'))
    nodes.append(G('MUSOLLA FOYER + JANITOR', None, None, None, [x for x in kids if x]))
    # ---------- family serambi (N9)
    kids, ck = [], []; bc = (314.8 + 359.8) / 2; P0 = P(S, 7.6, bc)
    kids.append(grp('L1', 'Family waiting', 'Round family bench (timber)', 'TT Timber oak', prism(Point(P0).buffer(1.6, 32).difference(Point(P0).buffer(1.05, 32)), zf, zf + 0.42)))
    kids.append(G('Bench cushion', None, 'TT Cushion warm', prism(Point(P0).buffer(1.58, 32).difference(Point(P0).buffer(1.07, 32)), zf + 0.42, zf + 0.48)))
    kids.append(G('Planter in the bench', None, 'TT Plant green', prism(Point(P0).buffer(1.0, 24), zf, zf + 0.5)))
    # gonjong canopy: surface + 2 posts
    nu, nv = 20, 6; V = []; Pp = []
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = i / nu, j / nv; t = abs(u - 0.5) * 2
            q = P0 + d(bc + 90) * (u - 0.5) * 4.2 + d(bc) * (v - 0.5) * 2.6
            V.append([q[0], q[1], zf + 2.9 + 0.15 * t * t + 0.9 * t ** 6 - 0.12 * abs(v - 0.5) * 2])
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; Pp += [[a, a + 1, a + nu + 2], [a, a + nu + 2, a + nu + 1]]
    can = mesh_faces(V, Pp); can += [[f[0][::-1], [], [-x for x in f[2]]] for f in list(can)]
    ck.append(G('Gonjong canopy (timber veneer)', None, 'TT NSembilan bronze', can))
    for sgn in (-1, 1):
        q = P0 + d(bc + 90) * sgn * 1.3; kids.append(G('Canopy post', None, 'TT Bronze PVD', cyl_faces(q[0], q[1], 0.04, zf + 0.48, zf + 2.93, 10)))
    for (r, b, s, m) in [(5.6, 314.8 + 8, 0.5, 'TT Soft play'), (6.0, 314.8 + 14, 0.38, 'TT Soft play mint'), (5.3, 314.8 + 19, 0.32, 'TT Soft play')]:
        p = P(S, r, b); Vv, Fc = K.icosphere(s, 1); Vv = [v * np.array([1, 1, 0.55]) + np.array([p[0], p[1], zf]) for v in Vv]
        fs = fix_outward(mesh_faces(Vv, Fc), [p[0], p[1], zf])
        kids.append(grp('L1', 'Family waiting', 'Soft play mound', m, fs))
    kids.append(on_outer(D_bench(1.4, 0.45, 0.45, 'TT Cushion warm'), 'L1', 'Family waiting', S, 348.0, 9.0, zf, name='Window bench'))
    nodes.append(G('FAMILY SERAMBI – Negeri Sembilan', None, None, None, [x for x in kids if x])); ceil.append(G('Family serambi canopy', None, None, None, ck))
    # lift lobby
    kids = [free(D_bench(1.6, 0.45, 0.45, 'TT Solid surface'), 'L1', 'L1 lift lobby', [50.6, 29.5], zf, [-0.6, -0.8], name='Bench') if False else None,
            free(D_planter_palm(), 'L1', 'L1 lift lobby', [50.9, 25.4], zf, [0, 1], name='Palm')]
    nodes.append(G('L1 LIFT LOBBY', None, None, None, [x for x in kids if x]))
    return nodes, ceil

# ================================================================== QA
def check():
    doors = {}
    for lv in ('GF', 'L1'):
        zs = []
        for c, t, w, sw in DOORS[lv]:
            c = np.array(c); t = np.array(t, float); t /= np.linalg.norm(t); n = np.array([-t[1], t[0]])
            zs.append(Polygon([c + t * (w / 2 + 0.1) + n * 0.95, c - t * (w / 2 + 0.1) + n * 0.95, c - t * (w / 2 + 0.1) - n * 0.95, c + t * (w / 2 + 0.1) - n * 0.95]))
        doors[lv] = unary_union(zs)
    bad = []
    for it in ITEMS:
        if not it['check']: continue
        key = (it['lv'], it['room'])
        if key not in NET: continue
        n_ = NET[key]; fp = it['fp']
        if fp.area < 1e-6: continue
        out = fp.difference(n_.buffer(0.01)).area
        if out > 0.002: bad.append((it['lv'], it['room'], it['label'], 'outside room/wall by %.3f m2' % out))
        if it['z0'] < FFL[it['lv']] + 2.0:
            dz = fp.intersection(doors[it['lv']]).area
            if dz > 0.005: bad.append((it['lv'], it['room'], it['label'], 'in door clearance %.3f m2' % dz))
    # overlaps between items in the same room (floor items)
    by = {}
    for it in ITEMS:
        if it['check'] and it['z0'] < FFL[it['lv']] + 0.5 and it['fp'].area > 1e-6: by.setdefault((it['lv'], it['room']), []).append(it)
    for k, lst in by.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b_ = lst[i], lst[j]
                ov = a['fp'].intersection(b_['fp']).area
                if ov > 0.01 and not (a['label'] in ('Stool',) and b_['label'] in ('Kopitiam table',)):
                    bad.append((k[0], k[1], f"{a['label']} x {b_['label']}", 'overlap %.3f m2' % ov))
    return bad

NET = {}
for r in ROOMS:
    if r['zone'] == 'open' and not r['name'].startswith('Verandah'): continue
    try: NET[(r['level'], r['name'])] = net(r['level'], r['name'])
    except Exception: pass

def build_interior():
    ITEMS.clear()
    gf, gfc = gf_interior(); gf += gf_wet_service()
    l1, l1c = l1_interior()
    return dict(GF=[floors('GF'), G('GF INTERIOR FIT-OUT', None, None, None, gf), G('GF CEILING FEATURES (hide for a clear plan view)', None, None, None, gfc)],
                L1=[floors('L1'), G('L1 INTERIOR FIT-OUT', None, None, None, l1), G('L1 CEILING FEATURES (hide for a clear plan view)', None, None, None, l1c)])

if __name__ == '__main__':
    out = build_interior()
    bad = check()
    print('items', len(ITEMS), 'defs', len(K.DEFS), 'problems', len(bad))
    for b in bad: print(' ', b)
