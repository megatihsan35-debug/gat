"""Titik Temu – Crit 1 geometry (metres). x = east, y = north. Bearings clockwise from north."""
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union

SITE = np.load('/home/claude/crit1/site.npy')
SITE_POLY = Polygon(SITE)
SETBACKS = [3, 3, 3, 3, 6, 3, 3, 3]          # edge i = SITE[i] -> SITE[i+1]; edge 4 = Jalan Tok Muda Awang Ngah

def _build():
    strips = [LineString([SITE[i], SITE[(i + 1) % 8]]).buffer(SETBACKS[i], cap_style=2) for i in range(8)]
    return SITE_POLY.difference(unary_union(strips))
BUILDABLE = _build()

QIBLA = 292.3
def d(b):  # unit vector for bearing
    r = np.radians(b); return np.array([np.sin(r), np.cos(r)])

# ---- primary geometry ----
B = np.array([61.0, 22.0])            # centre of Gelung Rasa (big ring)
R_COURT, R_VER, R_OUT, R_L1 = 9.0, 11.0, 18.1, 21.5
R1_SHOP, R2_SHOP = 14.75, 16.78       # shop display | staff | storage bands
R_OVH = 19.6                           # GF roof / terrace slab edge (1.5 m overhang)
DIST = 26.22
S = B + d(QIBLA) * DIST               # centre of Gelung Kecil (small ring)
RS_WELL, RS_COR, RS_OUT = 2.5, 4.5, 10.6
M0 = 274.3                             # start bearing of module 1 (18 deg modules)
def mod(i):                            # i = 1..20 -> (b0, b1)
    return (M0 + 18 * (i - 1)) % 360, (M0 + 18 * i) % 360

def sector(C, r0, r1, b0, b1, n=48):
    if b1 <= b0: b1 += 360
    a = np.linspace(b0, b1, n)
    outer = [C + d(t) * r1 for t in a]
    inner = [C + d(t) * r0 for t in a[::-1]] if r0 > 0 else [C]
    return Polygon(outer + inner)

def ring(C, r0, r1, n=180):
    return Point(C).buffer(r1, n).difference(Point(C).buffer(r0, n)) if r0 > 0 else Point(C).buffer(r1, n)

def ssec(k, r0=RS_COR, r1=RS_OUT):     # small-ring sector k = 0..7, s0 faces the knot
    b0 = (QIBLA - 180 - 22.5 + 45 * k) % 360
    return sector(S, r0, r1, b0, b0 + 45)
def sbear(k): return (QIBLA - 180 + 45 * k) % 360

def split_angle(poly_fn, b0, b1, parts):
    """parts: list of fractions summing to 1 -> list of (b0,b1)"""
    if b1 <= b0: b1 += 360
    out, a = [], b0
    for f in parts:
        out.append((a, a + (b1 - b0) * f)); a += (b1 - b0) * f
    return out

ROOMS = []   # dicts: name, code, level, poly, zone
def room(name, code, level, poly, zone, label=None):
    ROOMS.append(dict(name=name, code=code, level=level, poly=poly, zone=zone, label=label or name))

# ---------------- GROUND FLOOR ----------------
# knot lobby: modules 1-2 of big ring (R_COURT..R_OUT) + lens + small-ring sector 0 (corridor..outer)
big_m12 = sector(B, R_VER, R_OUT, *mod(1)[:1], mod(2)[1])
s0 = ssec(0)
lobby = unary_union([big_m12, s0, unary_union([big_m12, s0]).convex_hull]).intersection(
    unary_union([Point(B).buffer(R_OUT, 180), Point(S).buffer(RS_OUT, 180), unary_union([big_m12, s0]).convex_hull]))
# core 1 (2 lifts + stair) inside lobby, against north side
CORE1_C = B + d(QIBLA) * (R_OUT + 1.2)
def rect_at(c, w, h, bearing_long):
    """rectangle centred at c, long side w along bearing_long"""
    u = d(bearing_long); v = np.array([u[1], -u[0]])
    pts = [c + u * w / 2 + v * h / 2, c - u * w / 2 + v * h / 2, c - u * w / 2 - v * h / 2, c + u * w / 2 - v * h / 2]
    return Polygon(pts)
perp = np.array([d(QIBLA)[1], -d(QIBLA)[0]])          # pointing to the right of the qibla axis (north-east-ish)
core1_stair = rect_at(CORE1_C + perp * 3.3, 6.0, 3.0, QIBLA)
core1_lifts = rect_at(CORE1_C + perp * 0.2 + d(QIBLA) * 1.1, 4.2, 2.4, QIBLA)
lobby_net = lobby.difference(core1_stair.buffer(0.1)).difference(core1_lifts.buffer(0.1))
room('Entrance lobby + info', 'D1', 'GF', lobby_net, 'pub', 'LOBBY')
room('Stair 1', 'ST1', 'GF', core1_stair, 'circ', 'STAIR 1')
room('Lifts (2 nos)', 'LIFT', 'GF', core1_lifts, 'circ', 'LIFTS')

# toilets GF (modules 3-4)
b0, b1 = mod(3)[0], mod(4)[1]
tw = split_angle(None, b0, b1, [20 / 54, 20 / 54, 14 / 54])
room('Male restroom (bank 1)', 'D3', 'GF', sector(B, R_VER, R_OUT, *tw[0]), 'pub', 'MALE WC')
room('Female restroom (bank 1)', 'D3', 'GF', sector(B, R_VER, R_OUT, *tw[1]), 'pub', 'FEMALE WC')
a0, a1 = tw[2]
room('Nursing room', 'D3', 'GF', sector(B, R1_SHOP, R_OUT, a0, a1), 'pub', 'NURSING')
room('Nappy change', 'D3', 'GF', sector(B, R_VER + 1.6, R1_SHOP, a0, a1), 'pub', 'NAPPY')
room('Janitor (WC)', 'D3', 'GF', sector(B, R_VER, R_VER + 1.6, a0, a1), 'serv', 'JAN')

def shop(i, code, label):
    b0, b1 = mod(i)
    room(f'{label} display', code, 'GF', sector(B, R_VER, R1_SHOP, b0, b1), 'pub', label)
    room(f'{label} staff/prep', code, 'GF', sector(B, R1_SHOP, R2_SHOP, b0, b1), 'semi', 'prep')
    room(f'{label} store', code, 'GF', sector(B, R2_SHOP, R_OUT, b0, b1), 'serv', 'store')
for k, i in enumerate([5, 6, 7, 8]): shop(i, 'A2', f'A2-{k+1}')
# m9 Timur gate (open)
b0, b1 = mod(10)
room('Stair 2 + dumbwaiter + riser', 'ST2', 'GF', sector(B, R_VER, R_OUT, b0, b1), 'circ', 'STAIR 2')
b0, b1 = mod(11)
room('Cafe serving counter', 'A3', 'GF', sector(B, R_VER, 14.6, b0, b1), 'pub', 'SERVERY')
room('Cafe kitchen', 'A3', 'GF', sector(B, 14.6, R_OUT, b0, b1), 'serv', 'KITCHEN')
b0, b1 = mod(12)
room('Cafe dining', 'A3', 'GF', sector(B, R_VER, R_OUT, b0, b1), 'pub', 'CAFÉ')
for k, i in enumerate([13, 14, 15, 16]): shop(i, 'A1', f'A1-{k+1}')
b0, b1 = mod(18)
room('Info / security / wheelchair loan', 'D1', 'GF', sector(B, R_VER, 14.6, b0, b1), 'pub', 'INFO')
room('First aid', 'C', 'GF', sector(B, 14.6, R_OUT, b0, b1), 'semi', 'FIRST AID')

# small ring GF
room('Staff restroom F', 'D3', 'GF', ssec(1), 'serv', 'STAFF WC F')
room('Staff restroom M', 'D3', 'GF', ssec(2), 'serv', 'STAFF WC M')
def ssplit(k, names, fr, level, zone, codes):
    b0 = (QIBLA - 180 - 22.5 + 45 * k) % 360
    a = b0
    for nm, f, cd in zip(names, fr, codes):
        room(nm[0], cd, level, sector(S, RS_COR, RS_OUT, a, a + 45 * f), zone, nm[1]); a += 45 * f
ssplit(3, [('Main distribution board', 'MDB'), ("Cleaner's rest", 'CLEANER')], [20 / 32, 12 / 32], 'GF', 'serv', ['E4', 'E7'])
ssplit(4, [('Generator set', 'GENSET'), ('Housekeeping store', 'HK'), ('Janitor', 'JAN')], [15 / 31, 12 / 31, 4 / 31], 'GF', 'serv', ['E4', 'E7', 'E7'])
room('Loading bay reception', 'E2', 'GF', ssec(5), 'serv', 'LOADING')
ssplit(6, [('Refuse wet', 'REFUSE WET'), ('Refuse dry / recycle', 'REFUSE DRY')], [0.5, 0.5], 'GF', 'serv', ['E3', 'E3'])
ssplit(7, [('Dry store', 'DRY'), ('Freezer / wet store', 'FREEZER'), ('LAN room', 'LAN')], [15 / 34, 15 / 34, 4 / 34], 'GF', 'serv', ['E1', 'E1', 'E4'])
SCOR = ring(S, RS_WELL, RS_COR).difference(Point(B).buffer(R_OUT, 180))
room('Service corridor', 'CIRC', 'GF', SCOR, 'circ', '')
# verandah (open, covered) - big ring R_COURT..R_VER except gates
VER = ring(B, R_COURT, R_VER)
room('Verandah (open, covered)', 'OPEN', 'GF', VER, 'open', '')

# ---------------- LEVEL 1 ----------------
def l1mod(i, name, code, zone, label, r0=R_VER, r1=R_L1, parts=None):
    b0, b1 = mod(i)
    room(name, code, 'L1', sector(B, r0, r1, b0, b1), zone, label)
l1mod(8, 'Gallery exhibition', 'B1', 'semi', 'GALLERY')
b0, b1 = mod(9)
g = split_angle(None, b0, b1, [20 / 38, 10 / 38, 8 / 38])
room('Gallery storage', 'B1', 'L1', sector(B, R_VER, R_L1, *g[0]), 'serv', 'G.STORE')
room('Gallery staff', 'B1', 'L1', sector(B, R_VER, R_L1, *g[1]), 'priv', 'G.STAFF')
room('Janitor + LAN', 'E7', 'L1', sector(B, R_VER, R_L1, *g[2]), 'serv', 'J/L')
b0, b1 = mod(10)
room('Stair 2 + dumbwaiter + riser', 'ST2', 'L1', sector(B, R_VER, R_OUT, b0, b1), 'circ', 'STAIR 2')
room('MPH equipment store', 'B2', 'L1', sector(B, R_OUT, R_L1, b0, b1), 'serv', 'EQUIP')
b0, b1 = mod(11)[0], mod(12)[1]
room('Multipurpose hall (Dapur Rewang)', 'B2', 'L1', sector(B, 12.7, R_L1, b0, b1), 'semi', 'MULTIPURPOSE HALL')
room('MPH furniture store', 'B2', 'L1', sector(B, R_VER, 12.7, b0, b1), 'serv', 'FURN. STORE')
b0, b1 = mod(13)
t2 = split_angle(None, b0, b1, [0.42, 0.42, 0.16])
room('Male restroom (bank 2)', 'D3', 'L1', sector(B, R_VER, R_L1, *t2[0]), 'pub', 'MALE WC')
room('Female restroom (bank 2)', 'D3', 'L1', sector(B, R_VER, R_L1, *t2[1]), 'pub', 'FEMALE WC')
room('Janitor (WC L1)', 'D3', 'L1', sector(B, R_VER, R_L1, *t2[2]), 'serv', 'J')
L1_CORR = sector(B, R_COURT, R_VER, mod(8)[0], mod(13)[1])
room('L1 gallery walk (open balcony)', 'OPEN', 'L1', L1_CORR, 'open', '')
# knot L1: core landing + bridge
l1_link = lobby.difference(Point(B).buffer(R_VER, 180))
room('L1 lift lobby + bridge', 'CIRC', 'L1', l1_link.difference(core1_stair.buffer(0.1)).difference(core1_lifts.buffer(0.1)), 'circ', 'LIFT LOBBY')
room('Stair 1', 'ST1', 'L1', core1_stair, 'circ', 'STAIR 1')
room('Lifts (2 nos)', 'LIFT', 'L1', core1_lifts, 'circ', 'LIFTS')
# small ring L1
ssplit(1, [('Main office', 'OFFICE')], [1], 'L1', 'priv', ['C'])
ssplit(2, [('Meeting room', 'MEETING'), ('Office store', 'STORE')], [20 / 28, 8 / 28], 'L1', 'priv', ['C', 'C'])
ssplit(7, [("Manager's office", 'MANAGER'), ('Pantry', 'PANTRY')], [15 / 25, 10 / 25], 'L1', 'priv', ['C', 'C'])
ssplit(3, [('Female prayer + ablution', 'FEMALE PRAYER')], [1], 'L1', 'semi', ['D2'])
ssplit(4, [('Male prayer + ablution', 'MALE PRAYER')], [1], 'L1', 'semi', ['D2'])
ssplit(5, [('Family waiting', 'FAMILY WAITING')], [1], 'L1', 'semi', ['D2'])
ssplit(6, [('Musolla foyer + shoe racks', 'SHOE FOYER'), ('Musolla janitor', 'JAN')], [0.8, 0.2], 'L1', 'semi', ['D2', 'D2'])
# reception + staff WC inside small-ring sector 0 at L1 (part of link zone)
b0 = (QIBLA - 180 - 22.5) % 360
room('Admin reception + waiting', 'C', 'L1', sector(S, RS_COR, RS_OUT, b0, b0 + 26), 'priv', 'RECEPTION')
room('Staff toilet (admin)', 'C', 'L1', sector(S, RS_COR + 2.6, RS_OUT, b0 + 26, b0 + 45), 'priv', 'WC')
room('Admin corridor', 'CIRC', 'L1', ring(S, RS_WELL, RS_COR).difference(Point(B).buffer(R_OUT, 180)), 'circ', '')

# gates & openings (GF, open passages)
GATES = {'TIMUR': mod(9), 'SELATAN': mod(17), 'TENGAH': (mod(19)[0], mod(20)[1])}
COURT = Point(B).buffer(R_COURT, 180)
COLS_BIG = [(r, (M0 + 36 * k) % 360) for k in range(10) for r in (R_COURT, R_OUT)]
COLS_SMALL = [(r, (QIBLA - 180 - 22.5 + 45 * k) % 360) for k in range(8) for r in (RS_WELL, RS_OUT)]

def areas():
    import collections
    t = collections.OrderedDict()
    for r in ROOMS:
        t.setdefault((r['level'], r['code'], r['name']), 0)
        t[(r['level'], r['code'], r['name'])] += r['poly'].area
    return t

if __name__ == '__main__':
    print('S', S, 'site area', round(SITE_POLY.area, 1), 'buildable', round(BUILDABLE.area, 1))
    fp = unary_union([Point(B).buffer(R_OVH, 180), Point(S).buffer(RS_OUT, 180), lobby])
    print('footprint inside buildable?', BUILDABLE.contains(fp), 'footprint', round(fp.area, 1))
    l1fp = sector(B, R_COURT, R_L1, mod(8)[0], mod(13)[1])
    print('L1 east block inside buildable?', BUILDABLE.contains(l1fp))
    for k, v in areas().items(): print(k, round(v, 1))
