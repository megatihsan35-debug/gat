"""Titik Temu v3: the complete building, room by room, on three floors. Site metres, x east, y north, bearings clockwise from N.
Everything (plans, fire, plumbing, M&E, sections, 3D) is drawn from this one file. Run: python3 v3/plan3.py  -> checks.
Programme = BRIEF_SITE_C.docx Schedule of Accommodation (1,218 m2 net). Rules = UBBL 1984 (7th + 10th Schedules), MS 1184:2014.
Geometry of the ring, spines, roof and centre comes from v2/scheme.py (agreed after Crit 1)."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'v2'))
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity
import scheme as SC
from scheme import C, P, d, QIBLA, SPINES, roof_h, R_BR0, R_BR1, R_GF, R_L1, R_ROOF, R_COURT, R_POOL, R_OCULUS, R_DISC, SITE, ENV, spine_end

FFL = {'GF': 0.9, 'L1': 5.4, 'L2': 9.6}
SLAB = 0.30                       # structural slab; floor zone shown 0.6 in sections incl. beams/finishes
R_ROOF_IN = R_BR1                 # v3: petal roofs start at the bridge edge so the L2 ring bridge has headroom
LV = dict(SC.LV); LV.update(roof_in=R_ROOF_IN)
def tdir(b): r = math.radians(b); return np.array([math.cos(r), -math.sin(r)])      # direction of increasing bearing
def frame(bc, u, v): return C + d(bc) * v + tdir(bc) * u                           # local core frame: u across, v out from C

def sec(b0, b1, r0, r1, step=0.5):
    n = max(2, int(abs(b1 - b0) / step) + 1)
    out = [tuple(P(r1, b0 + (b1 - b0) * i / (n - 1))) for i in range(n)] + [tuple(P(r0, b1 - (b1 - b0) * i / (n - 1))) for i in range(n)]
    return Polygon(out)
def rect(bc, u0, u1, v0, v1): return Polygon([tuple(frame(bc, u0, v0)), tuple(frame(bc, u1, v0)), tuple(frame(bc, u1, v1)), tuple(frame(bc, u0, v1))])
def norm(b): return b % 360

# ---------------------------------------------------------------------------------------------- floor plates
PLATE = {'GF': SC.GF, 'L1': SC.L1}
_l2 = []
for nm, a, b in SC.L2_RANGES:
    if nm == 'E': a = 104.0            # east: third floor only from the S3 stair to the gallery
    if nm == 'SW': continue            # south-west: no third floor (admin below gets the tall space under the crest)
    _l2.append(SC.L1.intersection(SC.sector(a, b)))
PLATE['L2'] = unary_union(_l2)
ARCADE = None
ARCADE = SC.ann(R_BR0, R_BR1)            # ground: open arcade under the ring bridge; L1/L2: the ring bridge
def _corefp(c): return rect(c['bc'], -c['W'] / 2 - 0.2, c['W'] / 2 + 0.2, (c['v_l0'] - 0.2) if c['lift'] else c['v_s0'] - 0.2, c['v_s1'] + 0.2)
COURT = SC.disc(R_COURT)

# ---------------------------------------------------------------------------------------------- rooms
ROOMS = []                               # dict(fl, key, name, poly, kind, brief, ac, occ, facade, doors, fix)
def room(fl, key, name, poly, kind='room', brief=None, ac=False, occ=None, facade='solid', doors=(), fix=None, note='', inner='solid'):
    g = poly.intersection(PLATE[fl]) if kind != 'site' else poly
    if g.geom_type != 'Polygon':
        g = max(getattr(g, 'geoms', [g]), key=lambda q: q.area)
    r = dict(fl=fl, key=key, name=name, poly=g, kind=kind, brief=brief, ac=ac, occ=occ, facade=facade, inner=inner, doors=list(doors), fix=fix or [], note=note)
    ROOMS.append(r); return r

def span(area, b0, r0, r1, fl, sign=1, wall=0.15):
    """bearing b1 so that sec(b0,b1,r0,r1) clipped to the plate has `area` m2 of NET floor (inside half of each wall)"""
    lo, hi = 0.2, 60.0
    for _ in range(40):
        mid = (lo + hi) / 2; b1 = b0 + sign * mid
        g = sec(min(b0, b1), max(b0, b1), r0, r1).intersection(PLATE[fl]).buffer(-wall / 2, join_style=2)
        if g.area < area: lo = mid
        else: hi = mid
    return round(b0 + sign * hi, 2)

# ---- cores: lift (front, opens to the arcade / ring bridge) + switch-back stair behind it, final exit at R23
STAIR_W = 1.65                           # clear flight width = 3 units of 550 mm (UBBL 7th Schedule)
GO, RISE = 0.280, {('GF', 'L1'): (4.5, 26), ('L1', 'L2'): (4.2, 24)}
def core(bc, name, to_l2=True, sw=STAIR_W, lift=True, key='C', side=1):
    W = 2 * sw + 0.20                     # two flights + 200 well wall
    v_l0, v_l1 = 12.95, 15.15             # lift shaft internal (2.2 deep x 2.1 wide) for a 1.6 x 1.4 car
    v_s0 = 15.55 if lift else 13.2        # stair internal from here outwards
    v_s1 = v_s0 + sw + 12 * GO + sw       # landing + 12 goings + landing (26 risers in two flights of 13)
    parts = dict(bc=bc, W=W, sw=sw, v_s0=v_s0, v_s1=v_s1, v_l0=v_l0, v_l1=v_l1, lift=lift, name=name, to_l2=to_l2, key=key, side=side)
    parts['stair'] = rect(bc, -W / 2, W / 2, v_s0, v_s1)
    parts['stair_wall'] = rect(bc, -W / 2 - 0.2, W / 2 + 0.2, v_s0 - 0.2, v_s1 + 0.2)
    if lift:
        parts['shaft'] = rect(bc, -1.05, 1.05, v_l0, v_l1)
        parts['shaft_wall'] = rect(bc, -1.25, 1.25, v_l0 - 0.2, v_l1 + 0.2)
    return parts

# ---- toilets: the brief's banks (3 cubicles: PwD, parent + child, general; basins 1 child + 2 adult). 2 urinals added in male.
CORES = {}
S3_BC = 113.0
CORES['C1'] = core(223.0, 'CORE 1', key='C1', side=1, to_l2=False)   # south-west, Tengah side; ground + first floor
CORES['C2'] = core(339.0, 'CORE 2', key='C2', side=-1)   # north, beside the Utara gate; carries the roof water tank
CORES['S3'] = core(S3_BC, 'STAIR 3', lift=False, sw=STAIR_W, key='S3', side=1)   # east, open escape stair to the Pekan Sehari deck + gallery
# S4: external open stair from the west deck (L1) down to the arrival garden, straight run with a mid landing, 2.2 m clear (4 units)
S4 = dict(bc=279.0, w=2.2, v0=R_L1, run=12 * GO, land=2.2)
S4['v1'] = S4['v0'] + 2 * S4['run'] + S4['land']
S4['poly'] = rect(S4['bc'], -S4['w'] / 2 - 0.1, S4['w'] / 2 + 0.1, S4['v0'], S4['v1'])

def core_rooms(fl):
    for k, c in CORES.items():
        if fl == 'L2' and not c['to_l2']: continue
        room(fl, f'{k}-ST', f"{c['name']} STAIR" if c['lift'] else c['name'], c['stair_wall'], kind='stair', note=k)
        if c['lift']: room(fl, f'{k}-LF', 'LIFT', c['shaft_wall'], kind='lift', note=k)

# ============================================================== GROUND FLOOR (FFL +0.900)
RI, RO = R_BR1, R_GF
RM, R_PAR = 18.5, 15.3                   # east block band split; parents' room split (nappy front, nursing behind)
EAST = {}
def gf():
    fl = 'GF'
    # --- east block, clockwise from the Timur gate
    # two radial bands so the wet rooms get usable widths: inner band R12.5-18.5 opens to the arcade (public),
    # outer band R18.5-23 opens to the outer colonnade under the hanging first floor (staff + service)
    b = 41.8
    b1 = span(22.5, b, RI, RM, fl); room(fl, 'G01', 'MALE TOILET', sec(b, b1, RI, RM), 'wet', ('D3', 20), occ='wc'); EAST['G01'] = (b, b1); b = b1
    b1 = span(22.5, b, RI, RM, fl); room(fl, 'G02', 'FEMALE TOILET', sec(b, b1, RI, RM), 'wet', ('D3', 20), occ='wc'); EAST['G02'] = (b, b1); b = b1
    bp = b                                                       # parents' room: nappy change lobby, nursing room behind it
    b1 = max(span(4.0, b, RI, R_PAR, fl), span(6.0, b, R_PAR, RM, fl), b + 8.0)
    bo = 41.8
    bo1 = span(28.0, bo, RM, RO, fl); room(fl, 'G06', 'MALE STAFF RESTROOM', sec(bo, bo1, RM, RO), 'wet', ('D3', 28), occ='wc'); bo = bo1
    bo1 = span(28.0, bo, RM, RO, fl); room(fl, 'G07', 'FEMALE STAFF RESTROOM', sec(bo, bo1, RM, RO), 'wet', ('D3', 28), occ='wc'); bo = bo1
    bj = max(span(4.0, bo, RM, RO, fl), b1, bo + 3.4)          # janitor closet closes the outer band; both bands end on one radial
    b1 = bj; EAST['PAR'] = (bp, b1)
    room(fl, 'G04', 'NAPPY CHANGE', sec(bp, b1, RI, R_PAR), 'wet', ('D3', 4), occ='wc')
    room(fl, 'G03', 'NURSING', sec(bp, b1, R_PAR, RM), 'room', ('D3', 6), ac=True, occ='wc')
    room(fl, 'G05', 'JANITOR', sec(bo, bj, RM, RO), 'wet', ('D3', 4), occ='store'); b = bj
    b1 = span(20.0, b, 15.4, RO, fl)
    room(fl, 'G08', 'MAIN DISTRIBUTION BOARD', sec(b, b1, 15.4, RO), 'room', ('E4', 20), occ='plant')
    room(fl, 'G09', 'LAN / TELECOM', sec(b, b1, RI, 15.4), 'room', ('E4', 4), occ='plant'); b = b1
    b1 = span(30.0, b, RI, RO, fl); room(fl, 'G10', 'LOADING + RECEPTION', sec(b, b1, RI, RO), 'room', ('E2', 30), occ='store'); b = b1
    b1 = span(15.0 + 1.2, b, RI, RO, fl)
    room(fl, 'G11', 'FREEZER / WET STORE + DUMBWAITER', sec(b, b1, RI, RO), 'room', ('E1', 15), occ='store'); b = b1
    # S3 open escape stair straight after the stores; the shops follow it
    W3 = 2 * STAIR_W + 0.2; hw = math.degrees(math.asin((W3 / 2 + 0.25) / 13.2))
    CORES['S3'] = core(round(b + hw + 0.3, 2), 'STAIR 3', lift=False, sw=STAIR_W, key='S3', side=1)
    shops('A2', 'KUIH + SNACKS', CORES['S3']['bc'] + hw + 0.3, None, fl, target=32.3)
    # --- south-west block, clockwise from the main gate
    c1 = CORES['C1']; bc0 = c1['bc'] - math.degrees(math.asin((c1['W'] / 2 + 0.2) / 15.4)) - 0.4
    b = 201.4
    b1 = span(12.0, b, RI, RO, fl); room(fl, 'G20', 'SECURITY · FIRE CONTROL · WHEELCHAIR LOAN', sec(b, b1, RI, RO), 'room', ('D1', 0), ac=True, occ='office', facade='glass'); b = b1
    b1 = span(15.0, b, RI, RO, fl); room(fl, 'G21', 'FIRST AID', sec(b, b1, RI, RO), 'room', ('C', 15), ac=True, occ='office'); b = b1
    room(fl, 'G22', 'WHEELCHAIR + PRAM STORE', sec(b, bc0, RI, RO), 'room', None, occ='store')
    # --- west block: four A1 shop lots
    shops('A1', 'COOKING INGREDIENTS', 256.8, 303.7, fl)
    # --- north block: cafe + hand wash, core 2 on the Utara side
    c2 = CORES['C2']; hw2 = math.degrees(math.asin((c2['W'] / 2 + 0.2) / 15.6))
    b = c2['bc'] + hw2 + 0.6
    b1 = span(18.0, b, 16.0, RO, fl); room(fl, 'G30', 'CAFE KITCHEN', sec(b, b1, 16.0, RO), 'room', ('A3', 18), occ='kitchen')
    room(fl, 'G32', 'CAFE STORE', sec(b, b1, RI, 16.0), 'room', None, occ='store'); b = b1
    b1 = span(12.0 + 20.0, b, RI, RO, fl)
    room(fl, 'G31', 'CAFE SERVING + DINING', sec(b, b1, RI, RO), 'room', ('A3', 32), ac=True, occ='dining', facade='glass', inner='glass'); b = b1
    room(fl, 'G33', 'HAND WASH', sec(b, span(15.0, b, RI, 18.0, fl, wall=0.0), RI, 18.0), 'open', ('B3', 15), occ='open')
    core_rooms(fl)
    # open public spaces on the ground floor

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
    fl = 'L1'; RI1, RO1 = R_BR1, R_L1
    # toilet bank 2 stacked exactly over bank 1 (shared soil stacks); janitor + LAN over the parents' room
    room(fl, 'L04', 'MALE TOILET', sec(*EAST['G01'], RI1, RM), 'wet', ('D3', 20), occ='wc')
    room(fl, 'L05', 'FEMALE TOILET', sec(*EAST['G02'], RI1, RM), 'wet', ('D3', 20), occ='wc')
    room(fl, 'L07', 'LAN', sec(*EAST['PAR'], RI1, 15.0), 'room', ('E4', 4), occ='plant')
    room(fl, 'L06', 'JANITOR', sec(*EAST['PAR'], 15.0, RM), 'wet', ('E7', 4), occ='store')
    # housekeeping + cleaners' rest behind the male toilet, opening sideways onto the deck
    b = EAST['G01'][0]
    b1 = max(span(12.0, b, RM, 22.5, fl), span(12.0, b, 22.5, RO1, fl))
    room(fl, 'L01', 'HOUSEKEEPING STORE', sec(b, b1, RM, 22.5), 'room', ('E7', 12), occ='store')
    room(fl, 'L02', "CLEANERS' REST", sec(b, b1, 22.5, RO1), 'room', ('E7', 12), ac=True, occ='office')
    # multipurpose hall over the loading bay + stores (dumbwaiter from the dry store below)
    s3 = CORES['S3']; bend = s3['bc'] - math.degrees(math.asin((s3['W'] / 2 + 0.25) / s3['v_s0'])) - 0.3
    # inner band (R12.5-18.5): dry store over the GF freezer store (the dumbwaiter stacks); the rest is open deck to the bridge.
    bd = span(16.0, bend, RI1, RM, fl, sign=-1)
    room(fl, 'L13', 'DRY STORE + DUMBWAITER', sec(bd, bend, RI1, RM), 'room', ('E1', 15), occ='store')
    # outer band (R18.5-26.5): equipment + furniture stores by stair 3, then the hall; the hall opens to the deck on two sides
    # one wedge by stair 3 split radially: furniture store (inner) + equipment store (outer), both open off the hall's side wall
    bf = min(span(15.0, bend, RM, 23.1, fl, sign=-1), span(12.0, bend, 23.1, RO1, fl, sign=-1)); be = bf
    room(fl, 'L10', 'FURNITURE STORE', sec(bf, bend, RM, 23.1), 'room', ('B2', 15), occ='store')
    room(fl, 'L11', 'EQUIPMENT STORE', sec(bf, bend, 23.1, RO1), 'room', ('B2', 12), occ='store')
    bh = span(70.0, bf, RM, RO1, fl, sign=-1)
    room(fl, 'L12', 'MULTIPURPOSE HALL · DAPUR REWANG', sec(bh, bf, RM, RO1), 'room', ('B2', 70), ac=True, occ='hall', facade='glass')
    EAST['L1'] = dict(bd=bd, bf=bf, be=be, bh=bh, bend=bend)
    # south-west: administration suite between the main-gate slot and core 1. inner band R12.5-18.2 off the ring bridge,
    # corridor ring R18.2-19.7 (1.5 m), outer band R19.7-26.5 on the facade
    c1 = CORES['C1']; cb0 = c1['bc'] - math.degrees(math.asin((c1['W'] / 2 + 0.2) / 13.0)) - 0.4
    a0 = 191.9; RA, RB = 18.2, 19.7
    room(fl, 'L20', 'ADMIN CORRIDOR', sec(a0 - 1.5, cb0 + 1.0, RA, RB), 'room', None, ac=True, occ='circ')
    b = a0
    b1 = span(8.0, b, RI1, RA, fl); room(fl, 'L23', 'STAFF TOILET (PwD)', sec(b, b1, RI1, RA), 'wet', ('C', 8), occ='wc'); b = b1
    b1 = span(10.0, b, RI1, RA, fl); room(fl, 'L22', 'PANTRY', sec(b, b1, RI1, RA), 'wet', ('C', 10), occ='office'); b = b1
    room(fl, 'L21', 'RECEPTION + WAITING', sec(b, cb0, RI1, RA), 'room', ('C', 12), ac=True, occ='office', inner='glass')
    # the manager's office wraps behind core 1 (the core stops at R22.4; the floor runs on to R26.5)
    cfp = _corefp(c1).buffer(0.15, join_style=2); bwr = c1['bc'] + 4.6
    lo, hi = 0.5, 25.0
    for _ in range(40):
        mm = (lo + hi) / 2; g = sec(cb0 + 1.6 - mm, bwr, RB, RO1).difference(cfp).intersection(PLATE[fl]).buffer(-0.075, join_style=2)
        if g.area < 15.0: lo = mm
        else: hi = mm
    b1 = cb0 + 1.6 - hi
    room(fl, 'L25', "MANAGER'S OFFICE", sec(b1, bwr, RB, RO1).difference(cfp), 'room', ('C', 15), ac=True, occ='office', facade='glass'); b = b1
    b1 = span(20.0, b, RB, RO1, fl, sign=-1); room(fl, 'L26', 'MEETING ROOM', sec(b1, b, RB, RO1), 'room', ('C', 20), ac=True, occ='office', facade='glass'); b = b1
    b1 = span(8.0, b, RB, RO1, fl, sign=-1); room(fl, 'L27', 'OFFICE STORE', sec(b1, b, RB, RO1), 'room', ('C', 8), occ='store'); b = b1
    room(fl, 'L24', 'MAIN OFFICE', sec(184.0, b, RB, RO1), 'room', ('C', 30), ac=True, occ='office', facade='glass')
    core_rooms(fl)

# ============================================================== SECOND FLOOR (FFL +9.600)
def l2():
    fl = 'L2'; RI1, RO1 = R_BR1, R_L1
    # east: local food heritage gallery under the high roof by the main gate
    b1 = 173.4
    b0 = span(45.0, b1, 17.0, RO1, fl, sign=-1); room(fl, 'M01', 'LOCAL FOOD HERITAGE GALLERY', sec(b0, b1, 17.0, RO1), 'room', ('B1', 45), ac=True, occ='gallery', facade='glass')
    b0s = span(20.0, b1, RI1, 17.0, fl, sign=-1); room(fl, 'M02', 'GALLERY STORAGE', sec(b0s, b1, RI1, 17.0), 'room', ('B1', 20), occ='store')
    b0t = span(10.0, b0s, RI1, 17.0, fl, sign=-1); room(fl, 'M03', 'GALLERY STAFF', sec(b0t, b0s, RI1, 17.0), 'room', ('B1', 10), ac=True, occ='office')
    b0l = span(4.2, b0t, RI1, 17.0, fl, sign=-1); room(fl, 'M16', 'LAN', sec(b0l, b0t, RI1, 17.0), 'room', ('E4', 4), occ='plant')
    b0j = span(5.2, b0l, RI1, 17.0, fl, sign=-1); room(fl, 'M15', 'JANITOR', sec(b0j, b0l, RI1, 17.0), 'wet', ('D2', 5), occ='store')
    # west: musolla on the qibla radial
    bq = QIBLA
    hb = span(28.0, bq, 16.0, RO1, fl) - bq
    room(fl, 'M10', "MALE PRAYER ROOM", sec(bq - hb / 2, bq + hb / 2, 16.0, RO1), 'room', ('D2', 28), ac=True, occ='prayer', facade='glass')
    room(fl, 'M11', 'MALE WUDHU', sec(bq - hb / 2, bq + hb / 2, RI1, 16.0), 'wet', None, occ='wc')
    b = bq + hb / 2
    b1 = span(28.0, b, 16.0, RO1, fl); room(fl, 'M12', 'FEMALE PRAYER ROOM', sec(b, b1, 16.0, RO1), 'room', ('D2', 28), ac=True, occ='prayer', facade='glass')
    room(fl, 'M13', 'FEMALE WUDHU + CHANGING', sec(b, b1, RI1, 16.0), 'wet', None, occ='wc'); b = b1
    b0 = bq - hb / 2
    a = span(30.0, b0, 16.0, RO1, fl, sign=-1); room(fl, 'M14', 'FAMILY WAITING', sec(a, b0, 16.0, RO1), 'room', ('D2', 30), occ='seat', facade='glass')


    core_rooms(fl)

PLATE['L2'] = unary_union([PLATE['L2']] + [_corefp(c).buffer(1.2, join_style=2).intersection(SC.L1) for c in CORES.values() if c['to_l2']])
gf(); l1(); l2()

# ---------------------------------------------------------------------------------------------- open spaces (for occupancy, fire, finishes)
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

# ---------------------------------------------------------------------------------------------- doors: (room key, r, bearing, width, side)  side = 'in' swings into the room
DOORS = []
def door(key, r, b, w=0.9, swing='in', tag=None, fire=None, kind='single'):
    DOORS.append(dict(key=key, p=P(r, b), w=w, swing=swing, tag=tag, fire=fire, kind=kind))
def mid(key):
    rr = [r for r in ROOMS if r['key'] == key][0]; g = rr['poly']
    pts = np.array(g.exterior.coords); brg = np.degrees(np.arctan2(pts[:, 0] - C[0], pts[:, 1] - C[1])) % 360
    if brg.max() - brg.min() > 180: brg = np.where(brg < 180, brg + 360, brg)
    return (brg.min() + brg.max()) / 2, brg.min(), brg.max()
def place_doors():
    for k in ('G01', 'G02', 'L04', 'L05'):
        bm, b0, b1 = mid(k); door(k, R_BR1, bm, 1.0, 'in', 'D2')
    for k in ('G06', 'G07'):
        bm, b0, b1 = mid(k); door(k, R_GF, bm, 1.0, 'in', 'D2')
    bm, b0, b1 = mid('G04'); door('G04', R_BR1, bm, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('G03'); door('G03', R_PAR, bm, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('G05'); door('G05', R_GF, bm, 0.8, 'out', 'D1')
    bm, b0, b1 = mid('G08'); door('G08', R_GF, bm, 1.5, 'out', 'D4', fire='FD60', kind='double')
    bm, b0, b1 = mid('G09'); door('G09', R_BR1, bm, 0.9, 'out', 'D1', fire='FD60')
    bm, b0, b1 = mid('G10'); door('G10', R_GF, bm, 3.0, 'out', 'RS', kind='shutter'); door('G10', R_BR1, bm, 1.5, 'in', 'D4', kind='double')
    bm, b0, b1 = mid('G11'); door('G11', R_GF, bm, 1.2, 'out', 'D3')
    for r in SHOPS:
        bm, b0, b1 = mid(r['key']); door(r['key'], R_BR1, bm, 1.8, 'in', 'SF', kind='slide'); door(r['key'], R_GF, bm, 0.9, 'out', 'D1')
    bm, b0, b1 = mid('G20'); door('G20', 19.0, b0, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('G21'); door('G21', R_GF, bm, 1.2, 'out', 'D3'); door('G21', R_BR1, bm, 1.0, 'in', 'D2')
    bm, b0, b1 = mid('G22'); door('G22', R_BR1, bm, 1.2, 'in', 'D3')
    bm, b0, b1 = mid('G30'); door('G30', R_GF, bm, 1.0, 'out', 'D2'); door('G32', 16.0, bm, 0.9, 'in', 'D1'); door('G30', 20.6, b1, 1.0, 'in', 'D2')
    bm, b0, b1 = mid('G31'); door('G31', R_BR1, bm, 1.8, 'in', 'SF', kind='slide'); door('G31', R_GF, bm, 1.8, 'out', 'SF', kind='slide')
    bm, b0, b1 = mid('L01'); door('L01', 20.5, b0, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('L02'); door('L02', 24.5, b0, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('L06'); door('L06', 16.8, b1, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('L07'); door('L07', R_BR1, bm, 0.9, 'out', 'D1', fire='FD60')
    e1 = EAST['L1']; door('L10', 20.8, e1['bf'], 1.5, 'in', 'D4', kind='double')                     # stores open from the hall
    bm, b0, b1 = mid('L13'); door('L13', R_BR1, bm, 1.2, 'in', 'D3')
    e1 = EAST['L1']
    door('L11', 24.8, e1['bf'], 1.2, 'in', 'D3')                                     # from the hall
    door('L12', 22.8, e1['bh'], 1.8, 'out', 'D5', kind='double')                     # to the open deck (acw side)
    door('L12', RM, (max(e1['bh'], EAST['PAR'][1]) + e1['bd']) / 2, 1.8, 'out', 'D5', kind='double')   # to the open deck towards the ring bridge
    bm, b0, b1 = mid('L21'); door('L21', R_BR1, bm, 1.8, 'in', 'GD', kind='slide')
    for k in ('L24', 'L26', 'L27'): bm, b0, b1 = mid(k); door(k, 19.7, bm, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('L25'); door('L25', 19.7, b0 + 1.6, 0.9, 'in', 'D1')
    for k in ('L22', 'L23'): bm, b0, b1 = mid(k); door(k, 18.2, bm, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('L21'); door('L21', 18.2, bm, 0.9, 'out', 'D1')
    bm, b0, b1 = mid('M01'); door('M01', 21.8, b0, 1.8, 'out', 'D5', kind='double'); door('M02', 17.0, b1 - 2.5, 1.2, 'in', 'D3')
    bm, b0, b1 = mid('M02'); door('M02', R_BR1, bm, 1.2, 'in', 'D3')
    bm, b0, b1 = mid('M03'); door('M03', R_BR1, bm, 0.9, 'in', 'D1')
    for k in ('M10', 'M12'): bm, b0, b1 = mid(k); door(k, 16.0, bm, 1.2, 'in', 'D3')
    bm, b0, b1 = mid('M12'); door('M12', 21.0, b1, 1.2, 'out', 'D3')                       # second exit, straight to the deck
    for k in ('M11', 'M13'): bm, b0, b1 = mid(k); door(k, R_BR1, bm, 1.0, 'in', 'D2')
    bm, b0, b1 = mid('M14'); door('M14', 16.0, bm, 1.8, 'in', 'GD', kind='slide')
    bm, b0, b1 = mid('M15'); door('M15', R_BR1, bm, 0.9, 'in', 'D1')
    bm, b0, b1 = mid('M16'); door('M16', R_BR1, bm, 0.9, 'out', 'D1', fire='FD60')
place_doors()

def core_doors():
    """stair doors: FD60 self-closing, swing in the direction of escape; GF final exit to the colonnade; lift landing doors"""
    out = []
    for k, c in CORES.items():
        bc, W, v1 = c['bc'], c['W'], c['v_s1']
        for fl in ('GF', 'L1', 'L2'):
            if fl == 'L2' and not c['to_l2']: continue
            if k == 'S3':          # open stair: no enclosure doors
                continue
            if fl == 'GF': out.append(dict(fl=fl, key=f'{k}-ST', p=frame(bc, 0, v1 + 0.1), w=1.65, swing='out', tag='D6', fire='FD60', kind='double', axis='v'))
            out.append(dict(fl=fl, key=f'{k}-ST', p=frame(bc, c['side'] * (W / 2 + 0.1), v1 - c['sw'] / 2), w=1.65 if fl != 'GF' else 1.2, swing='in', tag='D6', fire='FD60', kind='single' if fl == 'GF' else 'double', axis='u'))
            if c['lift']: out.append(dict(fl=fl, key=f'{k}-LF', p=frame(bc, 0, c['v_l0'] - 0.1), w=1.0, swing='lift', tag='LD', fire='FR', kind='lift', axis='v'))
    return out
CORE_DOORS = core_doors()

# ---------------------------------------------------------------------------------------------- structural grid
GRID = []                    # (label, bearing)
def make_grid():
    lims = {'E': (39.0, 163.0), 'SW': (203.0, 232.0), 'W': (254.0, 307.0), 'N': (329.0, 376.5)}
    n = {'E': 11, 'SW': 3, 'W': 5, 'N': 4}
    i = 1
    for p in ('E', 'SW', 'W', 'N'):
        a, b = lims[p]
        for k in range(n[p] + 1):
            GRID.append((str(i), norm(a + (b - a) * k / n[p]), p)); i += 1
make_grid()
def cols(fl):
    """columns: B ring (R12.5) where clear of the spines, C ring (R23) where clear of the gate scoops; A ring R9.5 bridge + funnel"""
    out = []
    for lab, b, p in GRID:
        for ring, r in (('B', R_BR1), ('C', R_GF)):
            pt = Point(P(r, b))
            if SC.GF_VOID.buffer(0.35).contains(pt): continue
            out.append(dict(lab=lab, ring=ring, p=P(r, b), b=b, top=roof_h(b) - 0.5))
    for c, bb in SC.COLS_DISC: out.append(dict(lab='', ring='A', p=np.array(c), b=bb, top=12.4))
    return out
COLS = cols('GF')

# ---------------------------------------------------------------------------------------------- occupancy (UBBL 7th Schedule)
OCC_FACTOR = dict(shop=3.0, shop_up=6.0, office=10.0, hall=0.7, gallery=1.5, prayer=0.7, seat=1.5, dining=1.5, deck=1.5, arcade=None, kitchen=10.0, store=None, plant=None, wc=None, circ=None, open=None)
def occupancy():
    rows = []
    for r in ROOMS:
        f = OCC_FACTOR.get(r['occ'])
        if r['occ'] == 'shop' and r['fl'] != 'GF': f = 6.0
        if f: rows.append((r['fl'], r['name'], r['poly'].area, f, math.ceil(r['poly'].area / f)))
    for o in OPEN:
        if o['fl'] != 'GF': rows.append((o['fl'], 'OPEN DECK', o['poly'].area, 1.5, math.ceil(o['poly'].area / 1.5)))
    return rows
UNITS = {k: int(round(c['sw'] * 1000)) // 550 for k, c in CORES.items()}
UNITS['S4'] = int(round(S4['w'] * 1000)) // 550

def travel(fl, pt):
    """conservative route length from pt to the nearest stair door: radial leg to the ring bridge (R11) + arc on the bridge + leg to the stair.
    returns (nearest, second) in metres; the first radial leg is the one-way (dead-end) part."""
    v = np.array(pt) - C; r = float(np.hypot(*v)); b = math.degrees(math.atan2(v[0], v[1])) % 360
    res = []
    for k, c in CORES.items():
        if fl == 'L2' and not c['to_l2']: continue
        sb = c['bc']; door_r = (c['v_s1'] - c['sw'] / 2) if fl != 'GF' else c['v_s1']
        da = abs((b - sb + 180) % 360 - 180)
        direct = math.hypot(*(np.array(pt) - frame(sb, c['side'] * (c['W'] / 2 + 0.1), door_r)))
        if da < 12: res.append((direct * 1.15, k)); continue
        res.append((max(0.0, r - R_BR1) + 1.5 + math.radians(da) * 11.0 + abs(door_r - 11.0) + 1.5, k))
    if fl == 'L1':
        top = frame(S4['bc'], 0, S4['v0'] + 0.3); res.append((float(np.hypot(*(np.array(pt) - top))) * 1.2, 'S4'))
    res.sort()
    return res

if __name__ == '__main__':
    tot = {}
    for r in ROOMS:
        net = r['poly'].buffer(-0.075, join_style=2).area
        br = r['brief']
        print(f"{r['fl']:3} {r['key']:6} {r['name'][:34]:34} {r['kind']:5} gross {r['poly'].area:6.1f} net {net:6.1f}" + (f"  brief {br[0]} {br[1]}" if br else ''))
        tot[r['fl']] = tot.get(r['fl'], 0) + r['poly'].area
    print('enclosed by floor', {k: round(v) for k, v in tot.items()}, 'total', round(sum(tot.values())))
    print('open', {fl: round(sum(o['poly'].area for o in OPEN if o['fl'] == fl)) for fl in ('GF', 'L1', 'L2')})
    occ = occupancy(); byfl = {}
    for fl, nm, a, f, n in occ: byfl[fl] = byfl.get(fl, 0) + n
    print('occupant load', byfl, '| stair units', UNITS, '| capacity per floor (assembly 75/unit)', {fl: 75 * sum(u for k, u in UNITS.items() if (fl == 'L1') or (k != 'S4' and CORES[k]['to_l2'])) for fl in ('L1', 'L2')})
    worst = {}
    for fl in ('L1', 'L2'):
        pl = PLATE[fl]; xs = np.linspace(pl.bounds[0], pl.bounds[2], 90); ys = np.linspace(pl.bounds[1], pl.bounds[3], 90)
        w1 = w2 = de = 0
        for x in xs:
            for y in ys:
                if not pl.contains(Point(x, y)): continue
                t = travel(fl, (x, y)); w1 = max(w1, t[0][0]); w2 = max(w2, t[1][0] if len(t) > 1 else 0)
                de = max(de, min(t[0][0], max(0.0, math.hypot(x - C[0], y - C[1]) - R_BR1)))
        worst[fl] = (round(w1, 1), round(w2, 1), round(de, 1))
    print('travel (nearest exit worst, second worst, worst one-way leg)', worst)
    for k, c in CORES.items(): print(k, 'stair', round(c['W'], 2), 'x', round(c['v_s1'] - c['v_s0'], 2), 'from R', c['v_s0'], 'to', round(c['v_s1'], 2))
    print('grid', [(l, round(b, 1)) for l, b, p in GRID][:6], '...', len(GRID), '| columns', len(COLS))
