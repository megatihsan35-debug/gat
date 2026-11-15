"""Titik Temu v3.1: the complete building, room by room, on three floors. Site metres, x east, y north, bearings clockwise from N.
Everything (plans, fire, plumbing, M&E, sections, 3D) is drawn from this one file. Run: python3 v3/plan3.py  -> checks.
Programme = BRIEF_SITE_C.docx Schedule of Accommodation (1,218 m2 net). Rules = UBBL 1984 (7th + 10th Schedules), MS 1184:2014.
Geometry of the ring, spines, roof and centre comes from v2/scheme.py (agreed after Crit 1); the three-ring section with the
free-standing ring bridge and the stepped roof tiers comes from rings.py (16 Nov 2026, the user's sketch)."""
import sys, os, math, heapq
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'v2'))
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity
import scheme as SC
import rings as RG
from scheme import C, P, d, QIBLA, SPINES, roof_h, R_BR0, R_BR1, R_GF, R_L1, R_ROOF, R_COURT, R_POOL, R_OCULUS, R_DISC, SITE, ENV, spine_end

FFL = {'GF': 0.9, 'L1': 5.4, 'L2': 9.6}
SLAB = 0.30                       # structural slab; floor zone shown 0.6 in sections incl. beams/finishes
R_ROOF_IN = RG.T_OUT[0]           # inner edge of the outer roof tier
LV = dict(SC.LV)
def tdir(b): r = math.radians(b); return np.array([math.cos(r), -math.sin(r)])      # direction of increasing bearing
def frame(bc, u, v): return C + d(bc) * v + tdir(bc) * u                           # local frame: u along the tangent, v out from C
def brg(p): v = np.array(p) - C; return math.degrees(math.atan2(v[0], v[1])) % 360
def rad(p): return float(np.hypot(*(np.array(p) - C)))

def sec(b0, b1, r0, r1, step=0.5):
    n = max(2, int(abs(b1 - b0) / step) + 1)
    out = [tuple(P(r1, b0 + (b1 - b0) * i / (n - 1))) for i in range(n)] + [tuple(P(r0, b1 - (b1 - b0) * i / (n - 1))) for i in range(n)]
    return Polygon(out)
def rect(bc, u0, u1, v0, v1): return Polygon([tuple(frame(bc, u0, v0)), tuple(frame(bc, u1, v0)), tuple(frame(bc, u1, v1)), tuple(frame(bc, u0, v1))])
def norm(b): return b % 360
def biggest(g):
    if g.is_empty: return g
    if g.geom_type == 'Polygon': return g
    return max([q for q in getattr(g, 'geoms', []) if q.geom_type == 'Polygon'], key=lambda q: q.area)

# ---------------------------------------------------------------------------------------------- the three rings (rings.py)
R_IR0, R_GAL, R_IR1 = RG.R_IR0, RG.R_GAL, RG.R_IR1
R_BG0, R_BG1, R_OR0, R_OS, R_OR1 = RG.R_BG0, RG.R_BG1, RG.R_OR0, RG.R_OS, RG.R_OR1
INNER, BRIDGE, OUTER, WALKWAYS, GAPS = RG.INNER, RG.BRIDGE, RG.OUTER, RG.WALKWAYS, RG.GAPS
WALK = SC.ann(R_IR0, R_GAL)                                   # court gallery walk on the inner ring (L1 + L2)
FINWALK = SC.ann(R_OS, R_OR1)                                 # fin walk on the outer ring behind the rooms
PASS = unary_union([SC.strip(s['b'], RG.WALK_W + 0.3, R_GAL - 0.1, R_IR1 + 0.1) for s in SPINES])    # walkway landings through the inner ring
LAND = unary_union([SC.strip(s['b'], 6.0, R_OR0 - 0.1, R_OR1 + 0.1) for s in SPINES])                # walkway landings on the outer ring
COURT = SC.disc(R_COURT)

# ---------------------------------------------------------------------------------------------- cores
# Stairs and lifts stand inside the inner ring, so they never touch the bridge. Each stair is a straight switch-back run
# along the tangent: floor landing 2000 (door 1650 on the court side), 12 goings of 280, half landing 1650.
STAIR_W = 1.65                           # clear flight width = 3 units of 550 mm (UBBL 7th Schedule)
GO, RISE = 0.280, {('GF', 'L1'): (4.5, 26), ('L1', 'L2'): (4.2, 24)}
LAND0 = 2.0
def core(bc, name, key, lift=True, stair=True, to_l2=True, vout=15.95, s=1, sw=STAIR_W, duct=False):
    """tangential core. local (u, v): u along the tangent (s = +1 clockwise), v = distance out from C.
    order along u: [lift + riser] [floor landing] [flights] [half landing]"""
    c = dict(bc=bc, name=name, key=key, lift=lift, has_stair=stair, to_l2=to_l2, sw=sw, s=s, side=s)
    f = lambda u, v, bc=bc, s=s: frame(bc, s * u, v)
    def R(u0, u1, v0, v1): return Polygon([tuple(f(u0, v0)), tuple(f(u1, v0)), tuple(f(u1, v1)), tuple(f(u0, v1))])
    c['f'], c['R'] = f, R
    c['t'] = tdir(bc) * s                      # +u in site coordinates
    if stair:
        W = 2 * sw + 0.2; vo = vout - 0.2; vi = vo - W
        SL = LAND0 + 12 * GO + sw
        T = 0.2 + ((2.1 + 0.2) if lift else 0.0) + SL + 0.2 + (0.8 if duct else 0.0)
        ue0 = -T / 2; us0 = ue0 + 0.2 + (2.3 if lift else 0.0); us1 = us0 + SL
        c.update(W=W, vi=vi, vo=vo, us0=us0, us1=us1, ue0=ue0, ue1=T / 2, T=T, ua0=us0 + LAND0)
        c['stair'] = R(us0, us1, vi, vo); c['stair_wall'] = R(us0 - 0.2, us1 + 0.2 + (0.8 if duct else 0.0), vi - 0.2, vo + 0.2)
        c['duct'] = R(us1 + 0.2, us1 + 0.8, vi, vo) if duct else None          # services duct: CW down-feed from the tank room
        if lift:
            lu0, lu1 = ue0 + 0.2, ue0 + 2.3
            c.update(lu0=lu0, lu1=lu1, lv0=vi, lv1=vi + 2.2)
            c['shaft'] = R(lu0, lu1, vi, vi + 2.2); c['riser'] = R(lu0, lu1, vi + 2.4, vo)
            c['shaft_wall'] = R(lu0 - 0.2, lu1 + 0.2, vi - 0.2, vo + 0.2)
    else:                                       # lift only (radial box, door to the court side)
        vi = 12.95; lu0, lu1 = -1.05, 1.05
        c.update(W=2.1, vi=vi, vo=vi + 2.2, lu0=lu0, lu1=lu1, lv0=vi, lv1=vi + 2.2, stair=None, stair_wall=None, T=2.5, ue0=-1.25, ue1=1.25)
        c['shaft'] = R(lu0, lu1, vi, vi + 2.2); c['riser'] = None; c['shaft_wall'] = R(lu0 - 0.2, lu1 + 0.2, vi - 0.2, vi + 2.4)
    if not lift: c.update(shaft=None, shaft_wall=None, riser=None)
    c['fp'] = unary_union([g for g in (c.get('stair_wall'), c.get('shaft_wall')) if g is not None])
    c['holes'] = unary_union([g for g in (c.get('stair'), c.get('shaft'), c.get('riser'), c.get('duct')) if g is not None])
    return c

def corner_angle(c):
    """bearing half-width of a core at its inner corners (its widest angular extent)"""
    return math.degrees(math.atan2(c['T'] / 2, c['vi'] - 0.2))
def core_runs(c):
    """flights per storey: list of dict(f0, f1, z0, z1, n, nA, h, uA0, uA1) - flight A on the court side rises +u from the
    floor landing, flight B on the outer side comes back -u to the next floor landing"""
    out = []
    pairs = [('GF', 'L1')] + ([('L1', 'L2')] if c['to_l2'] else [])
    for f0, f1 in pairs:
        H, n = RISE[(f0, f1)]; nA = n // 2; nB = n - nA
        uA0 = c['ua0']; uA1 = uA0 + (nA - 1) * GO
        out.append(dict(f0=f0, f1=f1, z0=FFL[f0], z1=FFL[f1], n=n, nA=nA, nB=nB, h=H / n, uA0=uA0, uA1=uA1))
    return out

CORES = {}
EAST = {}

# ---- external escape stairs from the outer ring (open steel stairs, 2200 clear = 4 units, mid landing)
# a stair is a run of elements along u: ('land', length) or ('flight', risers); origin O, along a, across n (site metres)
def ext_stair(key, bc, z_top, z_bot, seq, kind='radial', w=2.2, vc=None, s=1):
    st = dict(key=key, name=f'STAIR {key[-1]}', bc=bc, w=w, z_top=z_top, z_bot=z_bot, seq=seq, kind=kind)
    nr = sum(n for k, n in seq if k == 'flight'); st['h'] = (z_top - z_bot) / nr
    L = sum((n - 1) * GO if k == 'flight' else n for k, n in seq); st['L'] = L
    if kind == 'radial':
        st['O'] = P(R_L1, bc); st['a'] = d(bc); st['n'] = tdir(bc); st['v0'] = R_L1; st['v1'] = R_L1 + L
    else:                                         # tangential: wraps the drum outside the fins, u runs towards decreasing bearing when s = 1
        st['a'] = -tdir(bc) * s; st['n'] = d(bc); st['O'] = C + d(bc) * vc - st['a'] * L / 2; st['vc'] = vc
    st['f'] = lambda u, v, st=st: st['O'] + st['a'] * u + st['n'] * v
    st['poly'] = Polygon([tuple(st['f'](0, -w / 2 - 0.1)), tuple(st['f'](L, -w / 2 - 0.1)), tuple(st['f'](L, w / 2 + 0.1)), tuple(st['f'](0, w / 2 + 0.1))])
    # parts: treads / landings as (u0, u1, z) and the flight lines (u0, z0, u1, z1)
    u, z = 0.0, z_top; parts, flights = [], []
    for k, n in seq:
        if k == 'land': parts.append(('land', u, u + n, z)); u += n
        else:
            u0, z0 = u, z
            for i in range(1, n):
                parts.append(('tread', u + (i - 1) * GO, u + i * GO, z - i * st['h']))
            flights.append((u0, z0, u + (n - 1) * GO, z - n * st['h'])); u += (n - 1) * GO; z -= n * st['h']
    st['parts'], st['flights'] = parts, flights
    st['top'] = st['f'](0.3, 0) if kind == 'radial' else st['f'](0.6, 0)        # where people arrive from the deck
    st['run'] = (seq[0][1] - 1) * GO if seq[0][0] == 'flight' else seq[0][1]
    return st
S4 = ext_stair('S4', 279.0, 5.4, 0.9, [('flight', 13), ('land', 2.2), ('flight', 13)])                 # west: to the arrival garden terrace +0.900
S5 = ext_stair('S5', 144.5, 5.4, 0.0, [('land', 2.2), ('flight', 16), ('land', 2.2), ('flight', 15)], kind='tangential', vc=28.2)   # south-east: wraps the drum down to the promenade
EXT = {'S4': S4, 'S5': S5}

# ---------------------------------------------------------------------------------------------- floor plates
PLATE = {'GF': SC.GF}
def _plate_up():
    cf = unary_union([c['fp'] for c in CORES.values()])
    PLATE['L1'] = unary_union([INNER, BRIDGE, OUTER, WALKWAYS, cf])
    PLATE['L2'] = unary_union([INNER, cf])
PLATE['L1'] = unary_union([INNER, BRIDGE, OUTER, WALKWAYS]); PLATE['L2'] = INNER
ARCADE = SC.ann(R_BR0, R_BR1)            # ground: open arcade round the court

# ---------------------------------------------------------------------------------------------- rooms
ROOMS = []                               # dict(fl, key, name, poly, kind, brief, ac, occ, facade, doors, fix)
def room(fl, key, name, poly, kind='room', brief=None, ac=False, occ=None, facade='solid', doors=(), fix=None, note='', inner='solid'):
    g = poly.intersection(PLATE[fl]) if kind != 'site' else poly
    g = biggest(g.buffer(0))
    r = dict(fl=fl, key=key, name=name, poly=g, kind=kind, brief=brief, ac=ac, occ=occ, facade=facade, inner=inner, doors=list(doors), fix=fix or [], note=note)
    ROOMS.append(r); return r

def span(area, b0, r0, r1, fl, sign=1, wall=0.15, minus=None):
    """bearing b1 so that sec(b0,b1,r0,r1) clipped to the plate (less `minus`) has `area` m2 of NET floor (inside half of each wall)"""
    lo, hi = 0.2, 70.0
    for _ in range(40):
        mid_ = (lo + hi) / 2; b1 = b0 + sign * mid_
        g = sec(min(b0, b1), max(b0, b1), r0, r1).intersection(PLATE[fl])
        if minus is not None: g = g.difference(minus)
        g = biggest(g.buffer(0))
        a = g.buffer(-wall / 2, join_style=2).area if not g.is_empty else 0
        if a < area: lo = mid_
        else: hi = mid_
    return round(b0 + sign * hi, 2)

def core_rooms(fl):
    for k, c in CORES.items():
        if fl == 'L2' and not c['to_l2']: continue
        if c['stair'] is not None: room(fl, f'{k}-ST', f"{c['name']} STAIR", c['stair_wall'], kind='stair', note=k)
        if c['lift']: room(fl, f'{k}-LF', 'LIFT' if c['stair'] is not None else c['name'], c['shaft_wall'], kind='lift', note=k)

RI, RO = R_BR1, R_GF
RM, R_PAR = 18.5, 15.3                   # east block band split; parents' room split (nappy front, nursing behind)
R_BOH = 16.7                             # back-of-house band behind core 1

# ============================================================== FIRST FLOOR first: the toilets fix where core 1 can go
def l1_toilets():
    fl = 'L1'; s0 = SPINES[0]
    b = s0['b'] + math.degrees(math.asin((RG.WALK_W + 0.3) / 2 / R_GAL)) + 0.25
    b1 = span(20.3, b, R_GAL, R_IR1, fl, minus=PASS); EAST['L04'] = (b, b1); b = b1
    b1 = span(20.3, b, R_GAL, R_IR1, fl, minus=PASS); EAST['L05'] = (b, b1)
    return b1

# ============================================================== GROUND FLOOR (FFL +0.900)
def gf():
    fl = 'GF'
    # --- east block, clockwise from the Timur gate: two radial bands (inner R12.5-18.5 public, outer R18.5-23 staff + service)
    b = 41.8
    b1 = span(20.6, b, RI, RM, fl); room(fl, 'G01', 'MALE TOILET', sec(b, b1, RI, RM), 'wet', ('D3', 20), occ='wc'); EAST['G01'] = (b, b1); b = b1
    b1 = span(20.6, b, RI, RM, fl); room(fl, 'G02', 'FEMALE TOILET', sec(b, b1, RI, RM), 'wet', ('D3', 20), occ='wc'); EAST['G02'] = (b, b1); b = b1
    bp = b
    bo = 41.8
    bo1 = span(28.0, bo, RM, RO, fl); room(fl, 'G06', 'MALE STAFF RESTROOM', sec(bo, bo1, RM, RO), 'wet', ('D3', 28), occ='wc'); bo = bo1
    bo1 = span(28.0, bo, RM, RO, fl); room(fl, 'G07', 'FEMALE STAFF RESTROOM', sec(bo, bo1, RM, RO), 'wet', ('D3', 28), occ='wc'); bo = bo1
    bj = max(span(4.0, bo, RM, RO, fl), bo + 3.4)
    EAST['PAR'] = (bp, bj)
    c1 = CORES['C1']; cf = c1['fp']
    room(fl, 'G04', 'NAPPY CHANGE', sec(bp, bj, RI, R_PAR).difference(cf), 'wet', ('D3', 4), occ='wc')
    room(fl, 'G03', 'NURSING', sec(bp, bj, R_PAR, RM).difference(cf), 'room', ('D3', 6), ac=True, occ='wc')
    room(fl, 'G05', 'JANITOR', sec(bo, bj, RM, RO), 'wet', ('D3', 4), occ='store')
    # --- back of house behind core 1 (core 1 stands in the inner ring R12-16.7; the rooms fill R15.3/16.7-23 round it)
    shop0 = c1['bc'] + corner_angle(c1) + 0.9
    b = bj
    b1 = span(15.0 + 1.2, b, R_PAR, RO, fl, minus=cf)
    room(fl, 'G11', 'FREEZER / WET STORE + DUMBWAITER', sec(b, b1, R_PAR, RO).difference(cf), 'room', ('E1', 15), occ='store'); EAST['G11'] = (b, b1); b = b1
    R_LAN = 18.4
    b8 = span(20.0, b, R_LAN, RO, fl, minus=cf)
    room(fl, 'G08', 'MAIN DISTRIBUTION BOARD', sec(b, b8, R_LAN, RO).difference(cf), 'room', ('E4', 20), occ='plant')
    room(fl, 'G09', 'LAN / TELECOM', sec(b, b8, R_BOH, R_LAN).difference(cf), 'room', ('E4', 4), occ='plant')
    EAST['G08'] = (b, b8); b = b8
    room(fl, 'G10', 'LOADING + RECEPTION', sec(b, shop0 - 0.4, RI, RO).difference(cf), 'room', ('E2', 30), occ='store')
    EAST['BOH_END'] = shop0 - 0.4
    shops('A2', 'KUIH + SNACKS', shop0, None, fl, target=32.3)
    # --- south-west block, clockwise from the main gate; lift 2 stands in the inner band, a general store behind it
    b = 201.4
    b1 = span(12.0, b, RI, RO, fl); room(fl, 'G20', 'SECURITY · FIRE CONTROL · WHEELCHAIR LOAN', sec(b, b1, RI, RO), 'room', ('D1', 0), ac=True, occ='office', facade='glass'); b = b1
    b1 = span(15.0, b, RI, RO, fl); room(fl, 'G21', 'FIRST AID', sec(b, b1, RI, RO), 'room', ('C', 15), ac=True, occ='office'); b = b1
    c3 = CORES['C3']; lw = c3['shaft_wall']
    bl = min(brg(q) for q in lw.exterior.coords) - 0.5
    room(fl, 'G22', 'WHEELCHAIR + PRAM STORE', sec(b, bl, RI, RO), 'room', None, occ='store')
    room(fl, 'G23', 'GENERAL STORE', sec(bl, 236.0, c3['vi'] + 2.4, RO), 'room', None, occ='store')
    EAST['G22'] = (b, bl)
    # --- west block: four A1 shop lots
    shops('A1', 'COOKING INGREDIENTS', 256.8, 303.7, fl)
    # --- north block: core 2 stands in front; the cafe sits behind it (R16.8-23), lit from the gap rooflights above
    rn = 16.8; c2 = CORES['C2']
    bk0 = 325.0
    bk1 = span(18.0, bk0, RM, RO, fl)
    room(fl, 'G30', 'CAFE KITCHEN', sec(bk0, bk1, RM, RO), 'room', ('A3', 18), occ='kitchen')
    room(fl, 'G32', 'CAFE STORE', sec(bk0, bk1, rn, RM), 'room', None, occ='store')
    b1 = span(32.0, bk1, rn, RO, fl)
    room(fl, 'G31', 'CAFE SERVING + DINING', sec(bk1, b1, rn, RO), 'room', ('A3', 32), ac=True, occ='dining', facade='glass', inner='glass')
    EAST['CAFE'] = (bk0, bk1, b1)
    room(fl, 'G33', 'HAND WASH', sec(b1, span(15.0, b1, rn, 21.0, fl, wall=0.0), rn, 21.0), 'open', ('B3', 15), occ='open')
    core_rooms(fl)

SHOPS = []
def shops(code, label, b0, b1, fl, target=None):
    n = 4; step = ((b1 or b0) - b0) / n
    edges = [b0 + i * step for i in range(n + 1)]
    if target:                                   # equal NET area each (the last lot is clipped by the gate scoop)
        edges = [b0]
        for i in range(n): edges.append(span(target, edges[-1], RI, RO, fl))
    for i in range(n):
        a, b = edges[i], edges[i + 1]
        k = f'{code}-{i + 1}'
        r = room(fl, k, f'SHOP {k}', sec(a, b, RI, RO), 'shop', (code, 32), ac=True, occ='shop', facade='glass', inner='glass')
        r['label2'] = label; SHOPS.append(r)

# ============================================================== FIRST FLOOR (FFL +5.400)
def l1():
    fl = 'L1'
    # ---- inner ring (rooms R11.0-15.5 behind the court gallery walk)
    room(fl, 'L04', 'MALE TOILET', sec(*EAST['L04'], R_GAL, R_IR1).difference(PASS), 'wet', ('D3', 20), occ='wc')
    room(fl, 'L05', 'FEMALE TOILET', sec(*EAST['L05'], R_GAL, R_IR1), 'wet', ('D3', 20), occ='wc')
    c1 = CORES['C1']; b = c1['bc'] + corner_angle(c1) + 0.35
    b1 = span(4.0, b, R_GAL, R_IR1, fl); room(fl, 'L06', 'JANITOR', sec(b, b1, R_GAL, R_IR1), 'wet', ('E7', 4), occ='store'); b = b1
    b1 = span(4.0, b, R_GAL, R_IR1, fl); room(fl, 'L07', 'LAN', sec(b, b1, R_GAL, R_IR1), 'room', ('E4', 4), occ='plant')
    # manager + meeting on the inner ring, west, beside the Utara walkway that leads across to the admin office
    su = SPINES[3]; b = su['b'] - math.degrees(math.asin((RG.WALK_W + 0.3) / 2 / R_GAL)) - 0.25
    b1 = span(15.0, b, R_GAL, R_IR1, fl, sign=-1); room(fl, 'L25', "MANAGER'S OFFICE", sec(b1, b, R_GAL, R_IR1), 'room', ('C', 15), ac=True, occ='office', inner='glass', facade='glass'); b = b1
    b1 = span(20.0, b, R_GAL, R_IR1, fl, sign=-1); room(fl, 'L26', 'MEETING ROOM', sec(b1, b, R_GAL, R_IR1), 'room', ('C', 20), ac=True, occ='office', inner='glass', facade='glass')
    # ---- outer ring, north: administration suite entered from the Utara walkway landing (rooms R21.5-25.0, corridor R25.0-26.5)
    a0 = su['b'] + math.degrees(math.asin(3.0 / R_OR0)) + 0.25
    a1 = span(12.0, a0, R_OR0, R_OR1, fl); room(fl, 'L21', 'RECEPTION + WAITING', sec(a0, a1, R_OR0, R_OR1), 'room', ('C', 12), ac=True, occ='office', inner='glass', facade='glass')
    b = a1
    b1 = span(30.0, b, R_OR0, R_OS, fl); room(fl, 'L24', 'MAIN OFFICE', sec(b, b1, R_OR0, R_OS), 'room', ('C', 30), ac=True, occ='office', inner='glass'); b = b1
    b1 = span(8.0, b, R_OR0, R_OS, fl); room(fl, 'L27', 'OFFICE STORE', sec(b, b1, R_OR0, R_OS), 'room', ('C', 8), occ='store'); b = b1
    b1 = span(10.0, b, R_OR0, R_OS, fl); room(fl, 'L22', 'PANTRY', sec(b, b1, R_OR0, R_OS), 'wet', ('C', 10), occ='office'); b = b1
    b1 = span(8.0, b, R_OR0, R_OS, fl); room(fl, 'L23', 'STAFF TOILET (PwD)', sec(b, b1, R_OR0, R_OS), 'wet', ('C', 8), occ='wc'); b = b1
    room(fl, 'L20', 'ADMIN CORRIDOR', sec(a1, b, R_OS, R_OR1), 'room', None, ac=True, occ='circ')
    EAST['ADMIN'] = (a0, a1, b)
    # ---- outer ring, east: cleaners, then the stores + dumbwaiter over the freezer store, then the hall (Dapur Rewang)
    st = SPINES[0]; b = st['b'] + math.degrees(math.asin(3.0 / R_OR0)) + 0.25
    R_DK = 23.0                                                  # these two sit behind a deck strip R21.5-23.0 that runs on to the dry store
    b1 = span(12.0, b, R_DK, R_OR1, fl); room(fl, 'L02', "CLEANERS' REST", sec(b, b1, R_DK, R_OR1), 'room', ('E7', 12), ac=True, occ='office', inner='glass'); b = b1
    b1 = span(12.0, b, R_DK, R_OR1, fl); room(fl, 'L01', 'HOUSEKEEPING STORE', sec(b, b1, R_DK, R_OR1), 'room', ('E7', 12), occ='store'); b = b1
    g11 = EAST['G11']; b = g11[0] - 5.6                          # dry store over the freezer store (the dumbwaiter stacks), door to the open deck
    b1 = span(16.2, b, R_OR0, R_OS, fl); room(fl, 'L13', 'DRY STORE + DUMBWAITER', sec(b, b1, R_OR0, R_OS), 'room', ('E1', 15), occ='store'); EAST['L13'] = (b, b1); b = b1
    bh = span(70.0, b, R_OR0, R_OR1, fl)
    room(fl, 'L12', 'MULTIPURPOSE HALL · DAPUR REWANG', sec(b, bh, R_OR0, R_OR1), 'room', ('B2', 70), ac=True, occ='hall', facade='glass', inner='glass')
    hb0 = b; b = bh
    b1 = span(15.0, b, R_OR0, R_OS, fl); room(fl, 'L10', 'FURNITURE STORE', sec(b, b1, R_OR0, R_OS), 'room', ('B2', 15), occ='store'); b = b1
    b1 = span(12.0, b, R_OR0, R_OS, fl); room(fl, 'L11', 'EQUIPMENT STORE', sec(b, b1, R_OR0, R_OS), 'room', ('B2', 12), occ='store'); EAST['L11'] = b1
    b = hb0
    EAST['L1'] = dict(bh0=b, bh1=bh)
    core_rooms(fl)

# ============================================================== SECOND FLOOR (FFL +9.600) - the inner ring only
def l2():
    fl = 'L2'
    c1 = CORES['C1']; b = c1['bc'] + corner_angle(c1) + 0.35
    b1 = span(20.0, b, R_GAL, R_IR1, fl); room(fl, 'M02', 'GALLERY STORAGE', sec(b, b1, R_GAL, R_IR1), 'room', ('B1', 20), occ='store'); b = b1
    b1 = span(45.0, b, R_GAL, R_IR1, fl); room(fl, 'M01', 'LOCAL FOOD HERITAGE GALLERY', sec(b, b1, R_GAL, R_IR1), 'room', ('B1', 45), ac=True, occ='gallery', inner='glass', facade='glass'); b = b1
    b1 = span(10.0, b, R_GAL, R_IR1, fl); room(fl, 'M03', 'GALLERY STAFF', sec(b, b1, R_GAL, R_IR1), 'room', ('B1', 10), ac=True, occ='office'); b = b1
    EAST['L2'] = dict(gal_end=b)
    # musolla: male prayer hall centred on the qibla radial (292.3°): the qibla wall is the outer wall, facing the gap
    bq = QIBLA
    lo, hi = 2.0, 30.0
    for _ in range(40):
        hb = (lo + hi) / 2; g = sec(bq - hb, bq + hb, R_GAL, R_IR1).intersection(PLATE[fl]).buffer(-0.075, join_style=2)
        if g.area < 28.0: lo = hb
        else: hi = hb
    hb = hi
    room(fl, 'M10', 'MALE PRAYER ROOM', sec(bq - hb, bq + hb, R_GAL, R_IR1), 'room', ('D2', 28), ac=True, occ='prayer', facade='glass')
    b = bq + hb
    b1 = span(8.0, b, R_GAL, R_IR1, fl); room(fl, 'M11', 'MALE WUDHU', sec(b, b1, R_GAL, R_IR1), 'wet', None, occ='wc'); b = b1
    b1 = span(5.0, b, R_GAL, R_IR1, fl); room(fl, 'M15', 'JANITOR', sec(b, b1, R_GAL, R_IR1), 'wet', ('D2', 5), occ='store'); b = b1
    b1 = span(4.0, b, R_GAL, R_IR1, fl); room(fl, 'M16', 'LAN', sec(b, b1, R_GAL, R_IR1), 'room', ('E4', 4), occ='plant'); EAST['M16'] = b1
    b = bq - hb
    b1 = span(28.0, b, R_GAL, R_IR1, fl, sign=-1); room(fl, 'M12', 'FEMALE PRAYER ROOM', sec(b1, b, R_GAL, R_IR1), 'room', ('D2', 28), ac=True, occ='prayer', facade='glass'); b = b1
    b1 = span(8.0, b, R_GAL, R_IR1, fl, sign=-1); room(fl, 'M13', 'FEMALE WUDHU + CHANGING', sec(b1, b, R_GAL, R_IR1), 'wet', None, occ='wc'); EAST['M13'] = b1
    # family waiting by the lift lobby of core 2
    c2 = CORES['C2']; b = c2['bc'] + corner_angle(c2) + 0.35
    b1 = span(30.0, b, R_GAL, R_IR1, fl); room(fl, 'M14', 'FAMILY WAITING', sec(b, b1, R_GAL, R_IR1), 'room', ('D2', 30), occ='seat', inner='glass', facade='glass')
    core_rooms(fl)

# ---- place the cores, then build the floors
_l1b = l1_toilets()
_c1 = core(0.0, 'CORE 1', 'C1', lift=True, vout=15.95)
_c1_bc = _l1b + corner_angle(_c1) + 0.35
CORES['C1'] = core(_c1_bc, 'CORE 1', 'C1', lift=True, vout=15.95)
_c2 = core(0.0, 'CORE 2', 'C2', lift=False, vout=16.1, duct=True)
_ca = corner_angle(_c2); _r2 = math.hypot(_c2['T'] / 2, _c2['vi'] - 0.2)
_ga = math.degrees(math.asin(3.6 / _r2))
_lo = SPINES[3]['b'] + _ga + _ca; _hi = SPINES[0]['b'] + 360 - _ga - _ca
CORES['C2'] = core(norm((_lo + _hi) / 2), 'CORE 2', 'C2', lift=False, vout=16.1, s=-1, duct=True)
CORES['C3'] = core(223.0, 'LIFT 2', 'C3', lift=True, stair=False)
CORES['C1']['top'] = 13.2; CORES['C2']['top'] = 12.7; CORES['C3']['top'] = 13.2   # roof slabs of the cores (lift overrun 13.2) under the funnel
_k2 = CORES['C2']                                                                    # tank room: over the half landing + duct end of core 2 (the high, Utara end)
_k2['tank'] = _k2['R'](_k2['us1'] - _k2['sw'] - 0.2, _k2['ue1'], _k2['vi'] - 0.2, _k2['vo'] + 0.2); _k2['tank_fl'] = 12.2; _k2['tank_top'] = 14.6
for _c in CORES.values(): _c.setdefault('tank', None)
_plate_up()
gf(); l1(); l2()
_bdw = (max(EAST['G11'][0], EAST['L13'][0]) + min(EAST['G11'][1], EAST['L13'][1])) / 2
DUMBWAITER = rect(_bdw, -0.45, 0.45, 21.7, 22.5)                # 900 x 800 shaft, freezer store (GF) -> dry store (L1)

# ---------------------------------------------------------------------------------------------- open spaces (for occupancy, fire, finishes)
CIRC = {'L1': unary_union([WALK, BRIDGE, WALKWAYS, FINWALK.intersection(SC.sector(SPINES[0]['b'], SPINES[1]['b']))]), 'L2': WALK}
def open_spaces():
    out = []
    for fl in ('L1', 'L2'):
        encl = unary_union([r['poly'] for r in ROOMS if r['fl'] == fl])
        rest = PLATE[fl].difference(encl.buffer(0.01))
        for g in getattr(rest, 'geoms', [rest]):
            if g.area > 3: out.append(dict(fl=fl, poly=g, kind='open', occ='deck'))
    gfe = unary_union([r['poly'] for r in ROOMS if r['fl'] == 'GF' and r['kind'] != 'open'])
    rest = PLATE['GF'].difference(gfe.buffer(0.01))
    for g in getattr(rest, 'geoms', [rest]):
        if g.area > 3: out.append(dict(fl='GF', poly=g, kind='open', occ='arcade'))
    return out
OPEN = open_spaces()
def decks(fl):
    """open floor that people stand on (counted for occupancy): the open plate less the walk, bridge, walkways and the fin-walk corridor"""
    g = unary_union([o['poly'] for o in OPEN if o['fl'] == fl]).difference(CIRC[fl])
    return [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon' and q.area > 2.0]

# ---------------------------------------------------------------------------------------------- doors: (room key, r, bearing, width, side)  side = 'in' swings into the room
DOORS = []
def door(key, r, b, w=0.9, swing='in', tag=None, fire=None, kind='single'):
    DOORS.append(dict(key=key, p=P(r, b), w=w, swing=swing, tag=tag, fire=fire, kind=kind))
def mid(key):
    rr = [r for r in ROOMS if r['key'] == key][0]; g = rr['poly']
    pts = np.array(g.exterior.coords); brg_ = np.degrees(np.arctan2(pts[:, 0] - C[0], pts[:, 1] - C[1])) % 360
    if brg_.max() - brg_.min() > 180: brg_ = np.where(brg_ < 180, brg_ + 360, brg_)
    return (brg_.min() + brg_.max()) / 2, brg_.min(), brg_.max()
def place_doors():
    for k in ('G01', 'G02'):
        bm, b0, b1 = mid(k); door(k, R_BR1, bm, 1.0, 'in', 'D2')
    for k in ('L04', 'L05'):
        bm, b0, b1 = mid(k); door(k, R_GAL, bm, 1.0, 'in', 'D2')
    for k in ('G06', 'G07'):
        bm, b0, b1 = mid(k); door(k, R_GF, bm, 1.0, 'in', 'D2')
    bp, bj = EAST['PAR']; door('G04', R_BR1, bp + 2.6, 0.9, 'in', 'D1')
    door('G03', R_PAR, bp + 2.6, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('G05'); door('G05', R_GF, bm, 0.8, 'out', 'D1')
    bm, b0, b1 = mid('G11'); door('G11', R_GF, bm, 1.2, 'out', 'D3')
    bm, b0, b1 = mid('G10'); door('G10', R_GF, bm, 3.0, 'out', 'RS', kind='shutter')
    a, b8 = EAST['G08']; door('G09', 18.15, b8, 0.9, 'out', 'D1', fire='FD60')                     # LAN opens off the loading bay
    door('G08', R_GF, (a + b8) / 2, 1.5, 'out', 'D4', fire='FD60', kind='double')
    for r in SHOPS:
        # shopfront kit (interior study 16 Nov): 1000 clear sliding leaf beside a fixed display pane; the opening sits against the
        # clockwise pier (front chord 2.30-2.55, less 2 x 50 half-piers and the 62.5 wall halves)
        bm, b0, b1 = mid(r['key']); W_ = 2 * R_BR1 * math.sin(math.radians((b1 - b0) / 2))
        bo = bm + math.degrees((W_ / 2 - 0.0625 - 0.05 - 0.5) / R_BR1)
        door(r['key'], R_BR1, bo, 1.0, 'in', 'SF1', kind='slide'); door(r['key'], R_GF, bm, 0.9, 'out', 'D1')
    bm, b0, b1 = mid('G20'); door('G20', 19.0, b0, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('G21'); door('G21', R_GF, bm, 1.2, 'out', 'D3'); door('G21', R_BR1, bm, 1.0, 'in', 'D2')
    bm, b0, b1 = mid('G22'); door('G22', R_BR1, bm, 1.2, 'in', 'D3')
    bm, b0, b1 = mid('G23'); door('G23', R_GF, bm, 1.2, 'out', 'D3')
    bk0, bk1, bd1 = EAST['CAFE']
    door('G30', R_GF, (bk0 + bk1) / 2 + 2.0, 1.0, 'out', 'D2'); door('G32', RM, (bk0 + bk1) / 2 + 2.0, 0.9, 'in', 'D1'); door('G30', 20.6, bk1, 1.0, 'in', 'D2')
    bm = (bk1 + bd1) / 2; door('G31', R_GF, bm, 1.8, 'out', 'SF', kind='slide'); door('G31', 19.2, bd1, 1.8, 'in', 'SF', kind='slide')
    # first floor
    for k in ('L06', 'L07'): bm, b0, b1 = mid(k); door(k, R_GAL, bm, 0.9, 'in' if k == 'L06' else 'out', 'D1', fire='FD60' if k == 'L07' else None)
    for k in ('L25', 'L26'): bm, b0, b1 = mid(k); door(k, R_GAL, bm, 0.9 if k == 'L25' else 1.2, 'in', 'D1' if k == 'L25' else 'D3')
    a0, a1, ae = EAST['ADMIN']
    door('L21', 23.6, a0, 1.8, 'in', 'GD', kind='slide')                                          # from the Utara walkway landing
    door('L21', 25.75, a1, 1.0, 'out', 'D2')                                                    # to the admin corridor
    for k in ('L24', 'L27', 'L22', 'L23'): bm, b0, b1 = mid(k); door(k, R_OS, bm, 0.9, 'in', 'D1')
    door('L20', 25.75, ae, 1.0, 'out', 'D2')                                                    # corridor end: second way out, to the deck
    for k in ('L02', 'L01'): bm, b0, b1 = mid(k); door(k, 23.0, bm, 0.9, 'in', 'D1')
    for k in ('L10', 'L11'): bm, b0, b1 = mid(k); door(k, R_OS, bm, 1.2, 'in', 'D3')
    door('L13', 23.3, EAST['L13'][0], 1.2, 'in', 'D3')                                          # dry store opens to the open deck
    e1 = EAST['L1']
    door('L12', 25.75, e1['bh0'], 1.8, 'out', 'D5', kind='double')                             # west: fin walk behind the dry store -> deck
    door('L12', 25.75, e1['bh1'], 1.8, 'out', 'D5', kind='double')                             # east: fin walk behind the stores -> deck + stair 5
    # second floor
    for k in ('M02', 'M03', 'M15'): bm, b0, b1 = mid(k); door(k, R_GAL, bm, 1.2 if k == 'M02' else 0.9, 'in', 'D3' if k == 'M02' else 'D1')
    bm, b0, b1 = mid('M01'); door('M01', R_GAL, bm, 1.8, 'in', 'D5', kind='double')
    for k in ('M10', 'M12'): bm, b0, b1 = mid(k); door(k, R_GAL, bm, 1.2, 'in', 'D3')
    for k in ('M11', 'M13'): bm, b0, b1 = mid(k); door(k, R_GAL, bm, 1.0, 'in', 'D2')
    bm, b0, b1 = mid('M14'); door('M14', R_GAL, bm, 1.8, 'in', 'GD', kind='slide')
    bm, b0, b1 = mid('M16'); door('M16', R_GAL, bm, 0.9, 'out', 'D1', fire='FD60')
place_doors()

def core_doors():
    """stair doors on the court side of the floor landing: FD60 double, self-closing; at GF the same door is the final exit to the
    arcade (open to the court and the four gates). t = wall direction, n = outward (towards the court)."""
    out = []
    for k, c in CORES.items():
        nrm = -d(c['bc'])
        for fl in ('GF', 'L1', 'L2'):
            if fl == 'L2' and not c['to_l2']: continue
            if c['stair'] is not None:
                p = c['f'](c['us0'] + LAND0 / 2, c['vi'] - 0.1)
                out.append(dict(fl=fl, key=f'{k}-ST', p=p, w=1.65, swing='out' if fl == 'GF' else 'in', tag='D6', fire='FD60', kind='double', t=c['t'], n=nrm))
            if c['lift']:
                p = c['f']((c['lu0'] + c['lu1']) / 2, c['vi'] - 0.1)
                out.append(dict(fl=fl, key=f'{k}-LF', p=p, w=1.0, swing='lift', tag='LD', fire='FR', kind='lift', t=c['t'], n=nrm))
    return out
CORE_DOORS = core_doors()

# ---------------------------------------------------------------------------------------------- structural grid
GRID = []                    # (label, bearing, petal)
def make_grid():
    lims = {'E': (39.0, 163.0), 'SW': (203.0, 232.0), 'W': (254.0, 307.0), 'N': (329.0, 376.5)}
    n = {'E': 11, 'SW': 3, 'W': 5, 'N': 4}
    i = 1
    for p in ('E', 'SW', 'W', 'N'):
        a, b = lims[p]
        for k in range(n[p] + 1):
            GRID.append((str(i), norm(a + (b - a) * k / n[p]), p)); i += 1
make_grid()
RINGS = dict(A=R_IR0, B=RG.R_B, C=RG.R_E, D=RG.R_M, E=R_GF, F=R_L1)   # ring grid lines A-F (columns on B, C, D, E)
POST_R = (R_BG0 + 0.15, R_BG1 - 0.15)                          # bridge-edge posts carrying the middle roof tier

def _wall_bearings(r):
    """bearings where radius r crosses a ground-floor radial wall (room edges) or the gate-passage edge walls"""
    out = []
    circ = SC.disc(r).exterior
    for q in ROOMS:
        if q['fl'] != 'GF' or q['kind'] in ('open',): continue
        g = q['poly']
        if not g.buffer(0.01).intersects(circ): continue
        hit = circ.intersection(g.exterior)
        for h in getattr(hit, 'geoms', [hit]):
            if h.geom_type == 'Point': out.append(brg((h.x, h.y)))
    return sorted(set(round(b, 2) for b in out))
def _thin(cands, target=11.0, lo=6.0, hi=17.0):
    if not cands: return []
    cands = sorted(cands); keep = [cands[0]]
    while True:
        last = keep[-1]
        nxt = [c for c in cands if lo <= (c - last) % 360 <= hi]
        if nxt: c = min(nxt, key=lambda c: abs((c - last) % 360 - target))
        else:
            ahead = [c for c in cands if (c - last) % 360 > 0.5]
            if not ahead: break
            c = min(ahead, key=lambda c: (c - last) % 360)
        if (c - keep[0]) % 360 < (last - keep[0]) % 360 or c == keep[0]: break
        if len(keep) > 1 and (c - keep[0]) % 360 < lo: break
        keep.append(c)
    return keep

def cols():
    out = []
    cf = unary_union([c['fp'] for c in CORES.values()]).buffer(0.25)
    gv = SC.GF_VOID.buffer(0.35)
    # B: R11.0 at every other grid line + one each side of every gate (arcade columns at GF, in the walk wall above)
    bb = [b for i, (lab, b, p) in enumerate(GRID) if i % 2 == 0]
    for s in SPINES:
        h = math.degrees(math.asin((s['w'] / 2 + 0.6) / RG.R_B)); bb += [s['b'] - h, s['b'] + h]
    for b in sorted(set(round(x, 2) for x in bb)):
        p = P(RG.R_B, b)
        if gv.contains(Point(p)) or cf.contains(Point(p)): continue
        out.append(dict(lab='', ring='B', p=p, b=b, r=0.175))
    # C (inner ring edge R15.5) and D (bridge R18.5): only where a ground-floor wall is there to take them
    for ring, rr in (('C', RG.R_E), ('D', RG.R_M)):
        cand = [b for b in _wall_bearings(rr) if not gv.contains(Point(P(rr, b))) and not cf.contains(Point(P(rr, b)))]
        for b in _thin(cand):
            out.append(dict(lab='', ring=ring, p=P(rr, b), b=b, r=0.175))
    # E: R23 on the grid, clear of the gate scoops
    for lab, b, p in GRID:
        pt = P(R_GF, b)
        if SC.GF_VOID.buffer(0.35).contains(Point(pt)): continue
        out.append(dict(lab=lab, ring='E', p=pt, b=b, r=0.175))
    # bridge-edge posts Ø150 at every other D column (portal frames across the bridge carrying the middle tier)
    ms = [c for c in out if c['ring'] == 'D']
    for i, c in enumerate(ms):
        if i % 2: continue
        for rr in POST_R: out.append(dict(lab='', ring='P', p=P(rr, c['b']), b=c['b'], r=0.075))
    for c in out:
        q = c['p']
        if c['ring'] in ('B', 'C'): c['top'] = RG.fun_under(q)
        elif c['ring'] == 'D': c['top'] = FFL['L1'] - 0.35
        elif c['ring'] == 'E': c['top'] = RG.out_under(q)
        else: c['z0'] = FFL['L1']; c['top'] = RG.mid_under(q)
        c.setdefault('z0', None)
    return out
COLS = cols()

# ---------------------------------------------------------------------------------------------- occupancy (UBBL 7th Schedule)
OCC_FACTOR = dict(shop=3.0, shop_up=6.0, office=10.0, hall=0.7, gallery=1.5, prayer=0.7, seat=1.5, dining=1.5, deck=1.5, arcade=None, kitchen=10.0, store=None, plant=None, wc=None, circ=None, open=None)
def occupancy():
    rows = []
    for r in ROOMS:
        f = OCC_FACTOR.get(r['occ'])
        if r['occ'] == 'shop' and r['fl'] != 'GF': f = 6.0
        if f: rows.append((r['fl'], r['name'], r['poly'].area, f, math.ceil(r['poly'].area / f)))
    for fl in ('L1', 'L2'):
        for g in decks(fl): rows.append((fl, 'OPEN DECK', g.area, 1.5, math.ceil(g.area / 1.5)))
    return rows
UNITS = {k: int(round(c['sw'] * 1000)) // 550 for k, c in CORES.items() if c['stair'] is not None}
for k, s in EXT.items(): UNITS[k] = int(round(s['w'] * 1000)) // 550

# ---------------------------------------------------------------------------------------------- travel distance (graph along the rings)
# inner walk R10.25, ring bridge R18.5, outer deck line R22.0 (open deck only) + fin walk R25.75 (behind the outer rooms);
# the four walkways join them on the gate axes. Rooms block the deck line; the hall, reception and admin corridor can be crossed.
R_WALK, R_BRW, R_DECK, R_OUTW = 10.25, 18.5, 22.0, 25.75
RR = dict(I=R_WALK, B=R_BRW, D=R_DECK, O=R_OUTW)
TRAVERSE = ('L12', 'L21', 'L20')
def _blocked(fl, R, k):
    p = Point(P(R, k))
    return any(r['poly'].contains(p) for r in ROOMS if r['fl'] == fl and r['kind'] in ('room', 'wet', 'shop') and r['key'] not in TRAVERSE)
def _graph(fl):
    G = {}
    def add(a, b, w): G.setdefault(a, []).append((b, w)); G.setdefault(b, []).append((a, w))
    for k in range(360): add(('I', k), ('I', (k + 1) % 360), math.radians(1) * R_WALK)
    if fl == 'L1':
        for k in range(360): add(('B', k), ('B', (k + 1) % 360), math.radians(1) * R_BRW)
        okD = [not _blocked(fl, R_DECK, k) for k in range(360)]; okO = [not _blocked(fl, R_OUTW, k) for k in range(360)]
        for k in range(360):
            k1 = (k + 1) % 360
            if okD[k] and okD[k1]: add(('D', k), ('D', k1), math.radians(1) * R_DECK)
            if okO[k] and okO[k1]: add(('O', k), ('O', k1), math.radians(1) * R_OUTW)
            if okD[k] and okO[k]: add(('D', k), ('O', k), R_OUTW - R_DECK)
        for s in SPINES:
            k = int(round(s['b'])) % 360
            add(('I', k), ('B', k), R_BRW - R_WALK); add(('B', k), ('D', k), R_DECK - R_BRW)
    ex = {}
    for k, c in CORES.items():
        if c['stair'] is None or (fl == 'L2' and not c['to_l2']): continue
        p = c['f'](c['us0'] + LAND0 / 2, c['vi'] - 0.2); ex[k] = (('I', int(round(brg(p))) % 360), abs(rad(p) - R_WALK) + 0.6)
    if fl == 'L1':
        for k, s in EXT.items(): ex[k] = (('O', int(round(brg(s['top']))) % 360), abs(rad(s['top']) - R_OUTW) + 0.3)
    return G, ex
def _dijkstra(G, src, w0):
    dist = {src: w0}; pred = {src: None}; h = [(w0, src)]
    while h:
        dd, u = heapq.heappop(h)
        if dd > dist[u]: continue
        for v, w in G.get(u, []):
            nd = dd + w
            if nd < dist.get(v, 1e9): dist[v] = nd; pred[v] = u; heapq.heappush(h, (nd, v))
    return dist, pred
_TR = {}
for _fl in ('L1', 'L2'):
    _G, _ex = _graph(_fl)
    _TR[_fl] = {k: (_dijkstra(_G, n0, w0), n0) for k, (n0, w0) in _ex.items()}
def _nodes_of(fl, pt):
    """candidate (node, leg) pairs for a point: the ring it stands on; outer-ring rooms reach the fin walk through their door"""
    r = rad(pt); b = brg(pt); k = int(round(b)) % 360
    if fl == 'L2' or r < (R_IR1 + R_BG0) / 2: return [(('I', k), abs(r - R_WALK))]
    if r < (R_BG1 + R_OR0) / 2: return [(('B', k), abs(r - R_BRW))]
    rm = [q for q in ROOMS if q['fl'] == fl and q['kind'] in ('room', 'wet') and q['poly'].buffer(0.05).contains(Point(pt))]
    if rm and rm[0]['key'] not in TRAVERSE:
        dd = [q for q in DOORS if q['key'] == rm[0]['key']]
        if dd:
            out = []
            for q in dd:
                q = q['p']; l0 = float(np.hypot(*(np.array(pt) - q)))
                for kq in (int(math.floor(brg(q))) % 360, int(math.ceil(brg(q))) % 360):
                    out += [(('O', kq), l0 + float(np.hypot(*(q - P(R_OUTW, kq))))), (('D', kq), l0 + float(np.hypot(*(q - P(R_DECK, kq)))))]
            return out
    return [(('D', k), abs(r - R_DECK)), (('O', k), abs(r - R_OUTW))]
def _node_xy(n): return P(RR[n[0]], n[1])
def travel(fl, pt):
    """route length from pt to each exit along the rings (+ the leg to the ring). returns [(dist, key)] nearest first."""
    out = []
    for k, ((dist, pred), n0) in _TR[fl].items():
        c = [leg + dist[n] for n, leg in _nodes_of(fl, pt) if n in dist]
        if c: out.append((min(c), k))
    out.sort(); return out
def travel_path(fl, pt):
    best = travel(fl, pt)[0]; k = best[1]
    (dist, pred), n0 = _TR[fl][k]
    n = min([(leg + dist[n], n) for n, leg in _nodes_of(fl, pt) if n in dist])[1]
    pts = [np.array(pt)]; q = n
    while q is not None: pts.append(_node_xy(q)); q = pred[q]
    if k in EXT: pts.append(EXT[k]['top'])
    else:
        c = CORES[k]; pts.append(c['f'](c['us0'] + LAND0 / 2, c['vi'] - 0.1))
    return pts, best[0], k

if __name__ == '__main__':
    tot = {}
    for r in ROOMS:
        net = r['poly'].buffer(-0.075, join_style=2).area
        br = r['brief']; bm, b0, b1 = mid(r['key'])
        print(f"{r['fl']:3} {r['key']:6} {r['name'][:34]:34} {r['kind']:5} {b0:6.1f}-{b1:6.1f} gross {r['poly'].area:6.1f} net {net:6.1f}" + (f"  brief {br[0]} {br[1]}" if br else ''))
        tot[r['fl']] = tot.get(r['fl'], 0) + r['poly'].area
    print('enclosed by floor', {k: round(v) for k, v in tot.items()}, 'total', round(sum(tot.values())))
    print('decks', {fl: round(sum(g.area for g in decks(fl))) for fl in ('L1', 'L2')})
    occ = occupancy(); byfl = {}
    for fl, nm, a, f, n in occ: byfl[fl] = byfl.get(fl, 0) + n
    print('occupant load', byfl, '| stair units', UNITS)
    for k, c in CORES.items(): print(k, round(c['bc'], 2), 'corner ±', round(corner_angle(c), 2), 'T', round(c['T'], 2), 'vi', round(c['vi'], 2), 'vo', round(c['vo'], 2), 'outer corner R', round(max(rad(q) for q in c['fp'].exterior.coords), 2))
    worst = {}
    for fl in ('L1', 'L2'):
        pl = PLATE[fl]; xs = np.linspace(pl.bounds[0], pl.bounds[2], 80); ys = np.linspace(pl.bounds[1], pl.bounds[3], 80)
        w1 = w2 = 0
        for x in xs:
            for y in ys:
                if not pl.contains(Point(x, y)): continue
                t = travel(fl, (x, y)); w1 = max(w1, t[0][0]); w2 = max(w2, t[1][0] if len(t) > 1 else 0)
        worst[fl] = (round(w1, 1), round(w2, 1))
    print('travel (worst nearest, worst second)', worst)
    print('columns', {k: sum(1 for c in COLS if c['ring'] == k) for k in 'BCDEP'})
    print('clerestories min (inner, outer)', [round(min(RG.clerestory(b)[i] for b in range(360)), 2) for i in (0, 1)])
