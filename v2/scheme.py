"""Titik Temu v3 ("one centre", three floors, wave roof) — review-stage geometry.
Site metres (x east, y north), bearings clockwise from north. Everything radiates from ONE centre C.
Run: python3 v2/scheme.py  -> prints the checks. Site + v1 programme come from model/geom.py.
v3 changes after the user's replies (15 Nov): three floors, tennis-court land added on the east (to Jalan Ibrahim),
public path on the north confirmed, a taller landmark (mast), a sculpted roof and a fin facade."""
import sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model'))
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, polylabel
import geom as G

# ---- site: Lot 10150 (model/geom.py SITE) + the tennis court strip up to the edge of Jalan Ibrahim ------------------
# The new east line is traced from the brief's site plan (Figure 2.6 sheet, about 0.5 m per pixel): approximate.
SITE_V1 = Polygon(G.SITE)
S0 = [tuple(map(float, p)) for p in G.SITE]
NE_NEW = (100.7, 64.7)                         # north boundary line continued 13.5 m east to the road edge
SITE_PTS = [S0[0], S0[1], NE_NEW, S0[3], S0[4], S0[5], S0[6], S0[7]]      # the old notch corner S0[2] is dropped
SETBACKS = [3, 3, 6, 6, 6, 3, 3, 3]            # N, N (new), E road, tail E road, S road, W, W, W
SITE = Polygon(SITE_PTS)
ENV = SITE.difference(unary_union([LineString([SITE_PTS[i], SITE_PTS[(i + 1) % 8]]).buffer(SETBACKS[i], cap_style=2) for i in range(8)]))
TENNIS = SITE.difference(SITE_V1.buffer(0.01))
_pole = polylabel(ENV, 0.05)
C = np.array([round(_pole.x, 1), round(_pole.y, 1)])     # the one centre = centre of the largest circle inside the setbacks
QIBLA = G.QIBLA                                # 292.3
d = lambda b: np.array([math.sin(math.radians(b)), math.cos(math.radians(b))])
P = lambda r, b: C + d(b) * r

# ---- radii (m) -------------------------------------------------------------------------------------------------
R_POOL, R_OCULUS = 2.5, 1.5                    # the titik: pool on the floor, rain oculus above it, mast through both
R_COURT = 9.0                                  # Talam court, kept at dia 18 m / 100 seats
R_BR0, R_BR1 = 9.5, 12.5                       # ring bridge at L1 (arcade under it at ground)
R_GF = 23.0                                    # ground-floor wall line (concave scoops cut into it at the gates)
R_L1 = 26.5                                    # first + second floor edge: convex, 3.5 m beyond the ground floor wall
R_ROOF = 28.3                                  # roof edge
R_ROOF_IN = 11.0
R_DISC = 14.0                                  # central funnel roof over the court
CANT = R_L1 - R_GF
# ---- levels (m) ------------------------------------------------------------------------------------------------
LV = dict(site=0.0, plinth=0.9, l1=5.4, l2=9.6, roof_lo=10.2, roof_hi=16.2, oculus=11.4, crown=13.5, mast=30.0)
SLAB, ROOF_T, L2_CLEAR = 0.6, 0.5, 2.7
# ---- four spines on the mean true bearing from Temerloh to each region's capitals (film data) ---------------------
# crest = the roof rises to three storeys at this gate; the other two gates are low (two storeys)
SPINES = [dict(k='TIMUR', b=27.9, w=6.0, gap=3.0, bite=(27.0, 6.0), crest=False, states='Pahang · Terengganu · Kelantan'),
          dict(k='SELATAN', b=182.7, w=8.0, gap=4.0, bite=(28.0, 10.0), crest=True, states='N. Sembilan · Melaka · Johor', main=True),
          dict(k='TENGAH', b=242.8, w=6.0, gap=3.0, bite=(27.0, 6.0), crest=False, states='Selangor · KL · Putrajaya'),
          dict(k='UTARA', b=317.7, w=6.0, gap=3.0, bite=(27.0, 6.0), crest=True, states='Perak · Penang · Kedah · Perlis')]

def disc(r, n=128): return Point(C).buffer(r, n)
def ann(r0, r1): return disc(r1).difference(disc(r0))
def strip(b, w, r0=0.0, r1=90.0): return LineString([P(r0, b), P(r1, b)]).buffer(w / 2, cap_style=2)
def sector(b0, b1, r=95):
    b0 %= 360; b1 %= 360
    if b1 <= b0: b1 += 360
    return Polygon([tuple(C)] + [tuple(P(r, b0 + (b1 - b0) * i / 96)) for i in range(97)])
def spine_end(b):
    hit = LineString([C, P(140, b)]).intersection(SITE.exterior)
    pts = [hit] if hit.geom_type == 'Point' else list(hit.geoms)
    return min(pts, key=lambda q: q.distance(Point(C)))

bs = [s['b'] for s in SPINES]; NAMES = ['E', 'SW', 'W', 'N']
def petal_of(b):
    b %= 360
    for i in range(4):
        b0, sp = bs[i], (bs[(i + 1) % 4] - bs[i]) % 360
        if (b - b0) % 360 <= sp: return i, ((b - b0) % 360) / sp
    return 0, 0.0
def roof_h(b):
    """top of the roof at bearing b: a smooth wave, high at the Selatan and Utara gates, low at Tengah and Timur"""
    i, t = petal_of(b)
    h0 = LV['roof_hi'] if SPINES[i]['crest'] else LV['roof_lo']; h1 = LV['roof_hi'] if SPINES[(i + 1) % 4]['crest'] else LV['roof_lo']
    s = t * t * (3 - 2 * t)
    return h0 + (h1 - h0) * s
def l2_ok(b): return roof_h(b) - ROOF_T - LV['l2'] >= L2_CLEAR

GF_VOID = unary_union([strip(s['b'], s['w']) for s in SPINES] + [Point(P(s['bite'][0], s['b'])).buffer(s['bite'][1], 96) for s in SPINES])
L1_VOID = unary_union([strip(s['b'], s['gap']) for s in SPINES])
RF_VOID = unary_union([strip(s['b'], s['gap'] - 1.0) for s in SPINES])
GF = ann(R_BR1, R_GF).difference(GF_VOID)
L1 = ann(R_BR1, R_L1).difference(L1_VOID)
ROOF = ann(R_ROOF_IN, R_ROOF).difference(RF_VOID)
BRIDGE = ann(R_BR0, R_BR1)
# second floor: only where the wave roof gives 2.7 m clear, i.e. the two crests
L2_RANGES = []
for i in range(4):
    b0, sp = bs[i], (bs[(i + 1) % 4] - bs[i]) % 360
    ok = [b0 + sp * k / 400 for k in range(401) if l2_ok(b0 + sp * k / 400)]
    if ok: L2_RANGES.append((NAMES[i], min(ok), max(ok)))
L2 = unary_union([L1.intersection(sector(a, b)) for _, a, b in L2_RANGES])
PETALS = []
for i in range(4):
    b0, b1 = bs[i], bs[(i + 1) % 4]; sec = sector(b0, b1)
    PETALS.append(dict(name=NAMES[i], b0=b0, b1=b1, span=(b1 - b0) % 360, gf=GF.intersection(sec), l1=L1.intersection(sec), l2=L2.intersection(sec), roof=ROOF.intersection(sec)))

def col_ring(r, clear, step):
    out = []
    for i, p in enumerate(PETALS):
        half = [math.degrees(math.asin(min(1, (s['w'] / 2 + clear) / r))) for s in SPINES]
        a0 = p['b0'] + half[i]; a1 = p['b0'] + p['span'] - half[(i + 1) % 4]
        n = max(1, round((a1 - a0) / step))
        out += [(tuple(P(r, a0 + (a1 - a0) * k / n)), a0 + (a1 - a0) * k / n) for k in range(n + 1)]
    return out
COLS_OUT = col_ring(R_GF, 0.6, 9.0); COLS_IN = col_ring(R_BR1, 0.6, 18.0); COLS_DISC = col_ring(R_BR0, 0.6, 26.0)

# ---- facade fins: vertical blades on the first-floor edge, from +5.400 to the roof, opening towards the gates -----
FIN_STEP, FIN_D, FIN_T = 0.75, 0.45, 0.06
FINS = []                                      # (bearing, angle from the facade tangent in degrees, top level)
for i, p in enumerate(PETALS):
    half = [math.degrees(math.asin((s['gap'] / 2 + 0.3) / R_L1)) for s in SPINES]
    a0 = p['b0'] + half[i]; a1 = p['b0'] + p['span'] - half[(i + 1) % 4]
    n = round(math.radians(a1 - a0) * R_L1 / FIN_STEP)
    for k in range(n + 1):
        t = k / n; b = a0 + (a1 - a0) * t
        edge = min(t, 1 - t) * (a1 - a0)       # degrees from the nearer gate
        op = max(0.0, 1 - edge / 22.0)         # 1 at the gate, 0 beyond 22 degrees
        FINS.append((b, 18 + 72 * op * op * (3 - 2 * op), roof_h(b) - ROOF_T))

# ---- zoning by bearing slice (review stage: zones, not rooms). (label, category, b0, b1) clockwise ----------------
ZONES_GF = [('RESTROOMS', 'pub', 33.5, 56), ('BACK OF HOUSE', 'boh', 56, 123), ('TRADE A2 · 4 SHOPS', 'trade', 123, 176),
            ('CORE 1', 'core', 190, 210), ('INFO · FIRST AID', 'pub', 210, 236),
            ('TRADE A1 · 4 SHOPS', 'trade', 249, 311.5),
            ('CORE 2', 'core', 324, 339), ('CAFE · NURSING', 'food', 339, 381.5)]
ZONES_L1 = [('DAPUR REWANG HALL', 'pub', 30.5, 66), ('PEKAN SEHARI DECK', 'open', 66, 142),
            ('RESTROOMS', 'pub', 142, 158), ('OPEN DECK', 'open', 158, 180.2),
            ('CORE 1', 'core', 185.2, 199), ('ADMIN', 'priv', 199, 240.3),
            ('STAFF ROOMS', 'priv', 245.3, 277.3), ('OPEN DECK', 'open', 277.3, 315.2),
            ('CORE 2', 'core', 320.2, 333), ('ANJUNG · OPEN TERRACE', 'open', 333, 385.4)]
_r = {n: (a, b) for n, a, b in L2_RANGES}
ZONES_L2 = [('RIVER DECK', 'open', _r['E'][0], 150), ('GALLERY', 'pub', 150, 180.2),
            ('CORE 1', 'core', 185.2, 199), ('MEETING · MANAGER', 'priv', 199, _r['SW'][1]),
            ('MUSOLLA', 'priv', 277.3, 307.3), ('FOYER', 'priv', 307.3, 315.2),
            ('CORE 2', 'core', 320.2, 333), ('SKY TERRACE', 'open', 333, _r['N'][1])]
L2_BRIDGE = ann(R_BR0, R_BR1)                  # the ring bridge again at the second floor, under the funnel roof
def zone_geom(floor, b0, b1): return floor.intersection(sector(b0, b1))

# ---- programme: v1 net areas (model/geom.py areas()) regrouped, and where each group goes -------------------------
A1 = {k: v for k, v in G.areas().items()}
def net(*keys, level=None): return sum(a for (lv, code, name), a in A1.items() if any(k in name for k in keys) and (level is None or lv == level))
PROG = [  # (group, v1 net m2, level, petal, note)
    ('Trade: 8 local-product shops', net('display', 'staff/prep', ' store', level='GF') - net('Dry store', 'wet store', 'Housekeeping'), 'GF', 'E + W', '4 shops in each block, glass fronts behind the columns'),
    ('Info, security, wheelchair loan, first aid', net('First aid') + 30.0, 'GF', 'SW', 'beside the main gate; the open forecourt replaces the 74 m² enclosed lobby'),
    ('Cafe (kitchen, counter, dining) + nursing, nappy change', net('Cafe') + net('Nursing', 'Nappy'), 'GF', 'N', 'opens straight onto the Talam court'),
    ('Public restrooms + janitor', net('restroom (bank 1)', 'Janitor (WC)', level='GF'), 'GF', 'E', 'by the Timur gate'),
    ('Lifts + 2 stairs', net('Stair', 'Lifts', level='GF'), 'GF', 'SW + N', 'one core beside each high gate; both reach every floor'),
    ('Back of house: loading, refuse, stores, MDB, genset, service corridor', net('Main distribution', 'Generator', 'Loading', 'Refuse', 'Dry store', 'wet store', 'Service corridor') + net('Janitor', level='GF') - net('Janitor (WC)', level='GF'), 'GF', 'E', 'faces Jalan Ibrahim, served from a service court on that side'),
    ('Multipurpose hall (Dapur Rewang) + stores', net('Multipurpose', 'MPH'), 'L1', 'E', 'opens onto the Pekan Sehari deck'),
    ('Public restrooms + janitor/LAN', net('restroom (bank 2)', 'Janitor (WC L1)', 'Janitor + LAN'), 'L1', 'E', ''),
    ('Admin offices (office, reception, pantry, store, toilet, corridor)', net('Main office', 'Office store', 'Pantry', 'Admin reception', 'Staff toilet', 'Admin corridor'), 'L1', 'SW', 'over the info point'),
    ('Staff restrooms, cleaners, housekeeping, LAN', net('Staff restroom', "Cleaner", 'Housekeeping', 'LAN room'), 'L1', 'W', 'moved up from the ground floor'),
    ('Lifts + 2 stairs', net('Stair', 'Lifts', level='L1'), 'L1', 'SW + N', ''),
    ('Meeting room + manager', net('Meeting', 'Manager'), 'L2', 'SW', 'top floor over the main gate'),
    ('Gallery (exhibition 54, store, staff)', net('Gallery exhibition', 'Gallery storage', 'Gallery staff'), 'L2', 'E', 'beside the river deck'),
    ('Musolla (male, female, ablution, foyer, family)', net('prayer', 'Family waiting', 'Musolla'), 'L2', 'W', f'top floor, centred on the qibla radial {QIBLA}°'),
]
BRIEF = dict(net=1218, gross=1525.63, staff=5, oku=1, motor=10, bike=10)   # BRIEF_SITE_C.docx, Table 2 and section F2

def zone_area(floor, zs, cats): return sum(zone_geom(floor, a, b).area for l, c, a, b in zs if c in cats)
ENCL = ('trade', 'food', 'pub', 'priv', 'boh', 'core')

if __name__ == '__main__':
    print('site v1', round(SITE_V1.area, 1), '| site v3', round(SITE.area, 1), '| tennis strip', round(TENNIS.area, 1), '| buildable', round(ENV.area, 1))
    print('C', C, 'clear to setback line', round(ENV.exterior.distance(Point(C)), 2), '| roof R', R_ROOF, '| inside setbacks:', disc(R_ROOF).within(ENV))
    for s in SPINES:
        e = spine_end(s['b']); L = e.distance(Point(C)); bi = s['bite'][0] - s['bite'][1]
        print(f"{s['k']:8} {s['b']:6.1f}°  centre→boundary {L:5.1f} m | boundary→L1 edge {L - R_L1:4.1f} | scoop depth {R_GF - bi:.1f} | roof at gate +{roof_h(s['b']):.1f}")
    print('L2 ranges', [(n, round(a, 1), round(b, 1)) for n, a, b in L2_RANGES], '| qibla roof +', round(roof_h(QIBLA), 2), 'clear', round(roof_h(QIBLA) - ROOF_T - LV['l2'], 2))
    for nm, fl, zs in (('GF', GF, ZONES_GF), ('L1', L1, ZONES_L1), ('L2', L2, ZONES_L2)):
        print(nm, ' | '.join(f'{l} {zone_geom(fl, a, b).area:.0f}' for l, c, a, b in zs), '| zoned', round(sum(zone_geom(fl, a, b).area for l, c, a, b in zs), 1), 'of', round(fl.area, 1), '| enclosed', round(zone_area(fl, zs, ENCL), 1))
    for lv, fl in (('GF', GF), ('L1', L1), ('L2', L2)):
        need = {}
        for g, a, l, pt, note in PROG:
            if l == lv:
                for q in pt.split(' + '): need[q] = need.get(q, 0) + a / len(pt.split(' + '))
        print(lv, 'net needed', round(sum(need.values()), 1), {k: round(v) for k, v in need.items()}, '| petal gross', {p['name']: round(p[lv.lower()].area) for p in PETALS})
    for g, a, lv, pt, note in PROG: print(f'  {lv} {pt:7} {a:6.1f}  {g}')
    print('total net', round(sum(a for _, a, *_ in PROG), 1), '| footprint', f'{disc(R_L1).area / SITE.area * 100:.1f}% of site | fins', len(FINS), '| cols', len(COLS_OUT), len(COLS_IN), len(COLS_DISC))
