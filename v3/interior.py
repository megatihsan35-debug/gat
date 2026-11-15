"""Interior design drawings (v3.1, interior study approved 16 Nov 2026).
Host state Pahang dresses the shared spaces; each shop / special room takes one guest state; one shopfront kit + one unique layer.
 I-100..I-102  interior plans 1:100 (themes, furniture, floor inlays, sign locations)
 I-200         shopfront kit: 8 front elevations + kit plan detail 1:50
 I-201         two interior sections 1:50 (radial, through A2-3 Melaka and A1-3 Pulau Pinang)
 I-300         signage + wayfinding family 1:20
Everything comes from plan3 (rooms, doors, cores), rings (section) and scheme (gates, qibla) - no separate geometry."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, polylabel
from cad import Drawing, INK
import plan3 as M
from plan3 import C, P, d, tdir, SC, ROOMS, CORES, FFL, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, QIBLA
import rings as RG
import plans
from plans import Wall, Arc, rad, brg
import landscape as LS

# ------------------------------------------------------------------------------------------------ themes
# Crit 1 state palette (model/int_plans.py): (name, capital, true bearing from site, straight-line km, colour)
ST = {'KEL': ('KELANTAN', 'KOTA BHARU', 356.2, 298, '#3456D6'), 'TRG': ('TERENGGANU', 'K. TERENGGANU', 20.9, 224, '#11A89A'),
      'PHG': ('PAHANG', 'KUANTAN', 68.4, 108, '#6FB3D2'), 'JHR': ('JOHOR', 'JOHOR BAHRU', 145.9, 263, '#E8B523'),
      'MLK': ('MELAKA', 'MELAKA', 187.6, 141, '#B83A2E'), 'NSN': ('N. SEMBILAN', 'SEREMBAN', 213.3, 96, '#9A6A45'),
      'SGR': ('SELANGOR', 'SHAH ALAM', 247.3, 108, '#8CC63F'), 'PRK': ('PERAK', 'IPOH', 311.0, 195, '#C9A27A'),
      'PNG': ('P. PINANG', 'GEORGE TOWN', 313.4, 318, '#E46F8C'), 'KDH': ('KEDAH', 'ALOR SETAR', 322.7, 374, '#4E8F3A'),
      'PLS': ('PERLIS', 'KANGAR', 323.6, 414, '#F28C28')}
SHOP = {'A2-1': 'PHG', 'A2-2': 'JHR', 'A2-3': 'MLK', 'A2-4': 'NSN', 'A1-1': 'SGR', 'A1-2': 'PRK', 'A1-3': 'PNG', 'A1-4': 'KDH'}
ROOM_ST = dict(SHOP, G31='KEL', G30='KEL', G32='KEL', G33='KEL', L21='PLS', M14='TRG')
HOST = '#6FB3D2'; BRASS = '#B08D3C'; BRONZE = '#3B3330'; SIGN = '#C9690A'
HALL = '#D9C08C'; PRAY = '#D8C38A'; GAL = '#9C8BD0'; ADMIN = '#E7A86A'
GATE_ST = {'TIMUR': ('PHG', 'TRG', 'KEL'), 'SELATAN': ('NSN', 'MLK', 'JHR'), 'TENGAH': ('SGR',), 'UTARA': ('PRK', 'PNG', 'KDH', 'PLS')}
GATE_EN = {'TIMUR': 'EAST GATE', 'SELATAN': 'SOUTH GATE (MAIN)', 'TENGAH': 'CENTRAL GATE', 'UTARA': 'NORTH GATE'}

SHOP_TXT = {   # range, screen, back wall, signature display
    'A2-1': ('LEMPOK DURIAN · KEREPEK · PAHANG KUIH', 'TENUN PAHANG DIRAJA CHECK', 'SILVER RIPPLE SHINGLES (ALUMINIUM)', 'TIERED TENUN TABLE'),
    'A2-2': ('KOLE KACANG · PUTU BAMBU · BORONGKO · TART NENAS', 'ZAPIN RHYTHM FINS (1-1-2 STEP)', 'DEEP GREEN GLAZED TILE', 'FACETED GOLD PINEAPPLE GRID OVER'),
    'A2-3': ('KUIH NYONYA · GULA MELAKA', 'PERANAKAN FOUR-PETAL TILE', 'STADTHUYS RED DADO + PERANAKAN TILE', 'TINGKAT TOWER'),
    'A2-4': ('WAJIK · KUIH SOPANG · APAM JOHOL · LEMANG', 'GONJONG ROOF PROFILE', 'CNC MERBAU, MINANG CARVING LINES', 'LEMANG BAMBOO RACK + GONJONG CANOPY'),
    'A1-1': ('REMPAH SATAY · HASIL LAUT KERING · SAMBAL', 'FIREFLY DOTS (KELIP-KELIP)', 'GRC MANGROVE ROOTS', 'SPICE DRAWER GRID WALL'),
    'A1-2': ('KOPI PUTIH IPOH · REMPAH RENDANG TOK', 'KARST HILL SKYLINE', 'FACETED GRC LIMESTONE', 'LABU SAYONG PENDANT CLUSTER'),
    'A1-3': ('BUAH PALA · REMPAH · HEKO', 'OVAL PORTAL RHYTHM', 'APOTHECARY GLASS JAR WALL', 'OVAL PORTAL DISPLAY CASE'),
    'A1-4': ('BERAS KEDAH · LAKSA KEDAH · TEPUNG', 'PADI STALK ROWS', 'STEPPED SAWAH BANDS', 'RICE BINS + BRASS GANTANG')}

def tint(c, k):
    import matplotlib.colors as mc
    c = np.array(mc.to_rgb(c)); return mc.to_hex(c + (1 - c) * k)

def room(k): return [r for r in ROOMS if r['key'] == k][0]
def theme_fill(r):
    k = r['key']
    if k in ROOM_ST: return tint(ST[ROOM_ST[k]][4], 0.72 if k in SHOP or k in ('G31', 'L21', 'M14') else 0.85)
    if k in ('L24', 'L27', 'L22', 'L23', 'L20', 'L25', 'L26'): return tint(ADMIN, 0.8)
    if k == 'L12' or k in ('L13', 'L10', 'L11'): return tint(HALL, 0.7 if k == 'L12' else 0.88)
    if k in ('M10', 'M12', 'M11', 'M13'): return tint(PRAY, 0.75)
    if k in ('M01', 'M02', 'M03'): return tint(GAL, 0.75 if k == 'M01' else 0.88)
    if k in ('G01', 'G02', 'L04', 'L05', 'G03', 'G04', 'G20', 'G21', 'G22', 'G06', 'G07'): return tint(HOST, 0.75)
    return '#EEF0F2'

# ------------------------------------------------------------------------------------------------ small symbols
def sign_mark(D, p, n, size=0.36):
    """sign location: orange hexagon with the sign type number (see I-300)"""
    pts = [np.array(p) + size * np.array([math.cos(math.radians(a)), math.sin(math.radians(a))]) for a in range(30, 390, 60)]
    D.poly(Polygon(pts), 'A-SIGN', fill=SIGN, edge=None, z=9.5); D.text(p, str(n), 'A-SIGN', size=1.15, color='white', weight='bold', z=9.6)
def chair(D, p, r=0.22, color=INK): D.circle(p, r, 'A-FURN', fill='white', edge=color, lw=0.07, z=5.5)
def rect_at(D, c, u, v, a, b, layer='A-FURN', fill='white', edge=INK, lw=0.08, z=5.4, ls='-'):
    """rectangle centred at c, half-size a along unit u and b along unit v"""
    c = np.array(c); u = np.array(u); v = np.array(v)
    D.poly(Polygon([c - u * a - v * b, c + u * a - v * b, c + u * a + v * b, c - u * a + v * b]), layer, fill=fill, edge=edge, lw=lw, z=z, ls=ls)
def arc_band(r0, r1, b0, b1, n=24):
    bs = np.linspace(b0, b1, n)
    return Polygon([P(r0, b) for b in bs] + [P(r1, b) for b in bs[::-1]])
def arc_line(D, r, b0, b1, layer, lw=0.1, color=INK, ls='-', z=5, n=40):
    D.line([P(r, b) for b in np.linspace(b0, b1, n)], layer, lw=lw, color=color, ls=ls, z=z)
def label(D, p, t, size=1.2, color=INK, rot=0.0, weight='normal', z=9.2):
    D.text(p, t, 'A-ANNO', size=size, color=color, rot=rot, weight=weight, halo=True, z=z)
def tang_rot(b):
    a = -b                                       # text along the tangent at bearing b, kept upright
    while a < -90: a += 180
    while a > 90: a -= 180
    return a
def rad_rot(b):
    a = 90 - b
    while a < -90: a += 180
    while a > 90: a -= 180
    return a

def store_r(r):
    """radius of the store partition in a shop (same rule as plans.shop_fit: 7.2 m2 at the outer end)"""
    g = r['poly']; rs = [rad(c) for c in g.exterior.coords]; r1 = max(rs); rr = r1
    while g.intersection(SC.disc(r1 + 1).difference(SC.disc(rr))).area < 7.2 and rr > min(rs): rr -= 0.05
    return rr

# ------------------------------------------------------------------------------------------------ GF
def shops_gf(D, full=True):
    for k, sk in SHOP.items():
        r = room(k); bm, b0, b1 = M.mid(k); col = ST[sk][4]; rr = store_r(r)
        e = math.degrees(0.12 / 13)                                     # small inset in bearing
        # feature back wall on the store partition (thick, state colour) + light band rooflights over (dotted)
        arc_line(D, rr - 0.09, b0 + e * 1.2, b1 - e * 1.2, 'A-FURN', lw=0.55, color=col, z=6)
        # fixed display case behind the fixed pane (acw side of the front) + the sliding leaf opening on the cw side
        F = Wall(r, 'acw'); W_ = 2 * R_BR1 * math.sin(math.radians((b1 - b0) / 2)); fixed = W_ - 0.125 - 0.1 - 1.0
        D.poly(F.rect(R_BR1 + 0.08, R_BR1 + 0.62, 0.05, fixed - 0.05), 'A-FURN', fill='white', edge=INK, lw=0.08, z=5.4)
        # signature display in light band 1 (R15.5-17)
        c = P(16.25, bm)
        if sk in ('PRK',): [D.circle(P(16.25 + dx, bm + dy), 0.16, 'A-FURN', fill=tint(col, 0.3), edge=INK, lw=0.06, z=5.5) for dx, dy in ((0, 0), (0.35, 1.2), (-0.35, -1.2), (0.3, -1.1))]
        elif sk == 'MLK': [D.circle(c, rr_, 'A-FURN', fill=tint(col, 0.2 + 0.2 * i), edge=INK, lw=0.06, z=5.5 + i * 0.01) for i, rr_ in enumerate((0.45, 0.33, 0.2))]
        elif sk == 'PNG':
            from shapely import affinity
            el = affinity.scale(Point(c).buffer(0.5), 1.0, 0.6); el = affinity.rotate(el, -bm, origin=tuple(c))
            D.poly(el, 'A-FURN', fill=tint(col, 0.5), edge=INK, lw=0.07, z=5.5)
        elif sk == 'KDH': [D.circle(P(16.25, bm + o), 0.28, 'A-FURN', fill=tint(col, 0.4), edge=INK, lw=0.06, z=5.5) for o in (-1.6, 0, 1.6)]
        else: rect_at(D, c, tdir(bm), d(bm), 0.6, 0.4, fill=tint(col, 0.4))
        # threshold strip in the arcade floor (brass) + blade sign at the acw pier + state label
        if full:
            arc_line(D, R_BR1 - 0.15, b0 + e, b1 - e, 'A-FLOR', lw=0.45, color=BRASS, z=4)
            sign_mark(D, P(R_BR1 - 0.42, b0 + math.degrees(0.5 / 12)), 5)
        label(D, P(19.6, bm), ST[sk][0], 1.15, col if sk not in ('JHR', 'SGR', 'PRK') else '#6B5A1C', rad_rot(bm), 'bold')

def cafe_gf(D):
    col = ST['KEL'][4]
    r = room('G31'); bm, b0, b1 = M.mid('G31')
    F = Wall(r, 'acw')                                              # kitchen wall: serving counter + pass
    D.poly(F.rect(17.2, 21.3, 0.0, 0.75), 'A-FURN', fill=tint(col, 0.55), edge=INK, lw=0.09, z=5.4)
    label(D, F.W(19.25, 0.38), 'COUNTER', 1.0, 'white', rad_rot(b0), 'bold')
    # wau bulan crescent over the counter (dashed, overhead)
    cc = F.W(19.25, 1.7); D.arc(cc, 1.2, 0, 360, 'A-FURN', lw=0.07, color=col, ls='--')
    label(D, F.W(19.25, 2.4), 'WAU BULAN LIGHT OVER', 0.95, col, rad_rot(b0))
    # communal table under light band 2 (R20-21.5) + benches
    bt0, bt1 = b0 + 4.2, b1 - 1.2
    D.poly(arc_band(20.45, 21.05, bt0, bt1), 'A-FURN', fill='white', edge=INK, lw=0.09, z=5.4)
    for rr in (20.05, 21.45): D.poly(arc_band(rr - 0.18, rr + 0.18, bt0, bt1), 'A-FURN', fill='#F4F1EA', edge=INK, lw=0.06, z=5.4)
    # two-seat tables at the street glass
    for o in (0.35, 0.6):
        b = b0 + (b1 - b0) * o + 1.5; c = P(22.25, b); D.circle(c, 0.33, 'A-FURN', fill='white', edge=INK, lw=0.08, z=5.4)
        for s in (-1, 1): chair(D, c + tdir(b) * 0.6 * s)
    # stool ledge on the cw wall beyond the side door
    G = Wall(r, 'cw'); D.poly(G.rect(20.3, 22.7, 0.0, 0.32), 'A-FURN', fill='white', edge=INK, lw=0.08, z=5.4)
    for s in np.arange(20.6, 22.6, 0.55): D.circle(G.W(s, 0.55), 0.17, 'A-FURN', fill='white', edge=INK, lw=0.06, z=5.5)
    # hand wash G33: one long trough on its outer arc
    r3 = room('G33'); bm3, a3, c3 = M.mid('G33')
    D.poly(arc_band(20.25, 20.85, a3 + 2.0, c3 - 2.0), 'A-FURN', fill='white', edge=INK, lw=0.09, z=5.4)
    label(D, P(19.8, bm3), 'TROUGH BASIN · CHILD TAPS AT 600', 0.95, INK, tang_rot(bm3))

def info_gf(D, full=True):
    r = room('G20'); bm, b0, b1 = M.mid('G20'); F = Wall(r, 'acw')
    # counter window in the wall to the Selatan gate passage (R15.0-17.4), door D1 stays at R19
    D.poly(F.rect(15.0, 17.4, -0.2, 0.02), 'A-WALL', fill='white', edge=None, z=5.2)
    D.line([F.W(15.0, -0.09), F.W(17.4, -0.09)], 'A-GLAZ', lw=0.1, z=6)
    D.poly(F.rect(15.0, 17.4, 0.0, 0.6), 'A-FURN', fill=tint(HOST, 0.4), edge=INK, lw=0.09, z=5.4)
    D.poly(F.rect(15.0, 15.9, -0.55, -0.2), 'A-FURN', fill=tint(HOST, 0.4), edge=INK, lw=0.07, z=5.4)        # 750 low ledge outside
    label(D, F.W(16.2, -1.6), 'KAUNTER INFO\n1050 / 750 + LOOP', 1.0, INK, rad_rot(b0), 'bold')
    chair(D, F.W(16.6, 1.0)); chair(D, F.W(15.5, 1.0))
    if full: sign_mark(D, F.W(14.2, -1.1), 2)
    # first aid G21: couch, desk, cabinet, basin
    r = room('G21'); bm, b0, b1 = M.mid('G21'); G = Wall(r, 'cw')
    D.poly(G.rect(16.0, 17.9, 0.0, 0.7), 'A-FURN', fill='white', edge=INK, lw=0.08, z=5.4); label(D, G.W(16.95, 0.35), 'COUCH', 0.9, INK, rad_rot(b1))
    D.poly(G.rect(19.5, 20.7, 0.0, 0.5), 'A-FURN', fill='white', edge=INK, lw=0.08, z=5.4)
    plans.basin(D, G, 21.5, 0.0)
    # wheelchair + pram bays in G22
    r = room('G22'); bm, b0, b1 = M.mid('G22')
    for i, s in enumerate(np.arange(13.6, 21.5, 1.1)):
        rect_at(D, P(s, bm), d(bm), tdir(bm), 0.45, 0.3, fill='white', lw=0.06)
    label(D, P(17.5, bm), 'WHEELCHAIR + PRAM LOAN', 0.95, INK, rad_rot(bm))

def nursing_gf(D):
    r = room('G03'); bm, b0, b1 = M.mid('G03')
    c = P(17.2, bm - 1.5); D.poly(Point(c).buffer(0.42), 'A-FURN', fill=tint(HOST, 0.5), edge=INK, lw=0.08, z=5.4)
    label(D, P(16.4, bm + 2.0), 'NURSING CHAIR\n2700 K DIM', 0.9, INK, 0)

def tactile_gf(D):
    """MS 1184 tactile guide path: arcade ring at R11.75 + the four gate axes + spurs to info, lifts and toilets"""
    y = '#E3B505'
    arc_line(D, 11.75, 0, 360, 'A-TACT', lw=0.32, color=y, z=3.6, n=360)
    for s in SC.SPINES:
        c = [k for k in LS.CANOPIES if abs(k['b'] - s['b']) < 1][0]
        D.line([P(11.75, s['b']) + tdir(s['b']) * 0.0, P(min(c['R_out'], 29.0) - 0.5, s['b'])], 'A-TACT', lw=0.32, color=y, z=3.6)
    # spurs: info counter (along R16.2 from the Selatan axis), lifts, toilets
    D.line([P(16.2, 182.7), P(16.2, 200.6)], 'A-TACT', lw=0.32, color=y, z=3.6)
    for dd in M.CORE_DOORS:
        if dd['fl'] == 'GF' and dd['kind'] == 'lift':
            p = np.array(dd['p']); D.line([P(11.75, brg(p)), p + np.array(dd['n']) * 0.3], 'A-TACT', lw=0.32, color=y, z=3.6)
    for k in ('G01', 'G02'):
        bm = M.mid(k)[0]; D.line([P(11.75, bm), P(R_BR1 - 0.2, bm)], 'A-TACT', lw=0.32, color=y, z=3.6)

def court_gf(D):
    # river bands in the terrazzo: Pahang (darker) from Timur, Semantan (lighter) from Tengah, meeting at the Titik pool
    for b, c, sg in ((27.9, '#4F98BE', 1), (242.8, '#9CCDE3', -1)):
        t = np.linspace(0, 1, 50); rr = 11.0 - (11.0 - R_POOL - 0.1) * t; bb = b + 55 * t * sg
        D.line([P(r_, b_) for r_, b_ in zip(rr, bb)], 'A-FLOR', lw=1.6, color=c, z=1.6)
    label(D, P(7.2, 75), 'SUNGAI PAHANG BAND', 1.0, '#2E6E8E', tang_rot(75))
    label(D, P(7.2, 205), 'SUNGAI SEMANTAN BAND', 1.0, '#2E6E8E', tang_rot(205))
    # brass compass ring at R9.4 with 10-degree ticks, gate names, qibla
    arc_line(D, 9.4, 0, 360, 'A-FLOR', lw=0.3, color=BRASS, z=3.5, n=360)
    for b in range(0, 360, 10): D.line([P(9.25, b), P(9.55, b)], 'A-FLOR', lw=0.1, color=BRASS, z=3.5)
    D.line([P(8.8, QIBLA), P(9.9, QIBLA)], 'A-FLOR', lw=0.35, color=BRASS, z=3.5)
    label(D, P(8.2, QIBLA), 'QIBLA 292.3°', 1.0, '#8A6A20', tang_rot(QIBLA), 'bold')
    label(D, P(7.4, 150), 'BRASS COMPASS RING R9.4', 1.0, '#8A6A20', tang_rot(150))

def gates_gf(D):
    for s in SC.SPINES:
        c = [k for k in LS.CANOPIES if abs(k['b'] - s['b']) < 1][0]
        b = s['b']
        # floor stripes of the gate's states (just inside the gate, across the passage)
        sts = GATE_ST[s['k']]; w = s['w'] - 1.0; n = len(sts)
        for i, sk in enumerate(sts):
            u0 = -w / 2 + i * w / n; u1 = u0 + w / n
            D.poly(Polygon([P(13.6, b) + tdir(b) * u0, P(13.6, b) + tdir(b) * u1, P(14.2, b) + tdir(b) * u1, P(14.2, b) + tdir(b) * u0]), 'A-FLOR', fill=ST[sk][4], edge=None, z=3.5)
        # directory totem (sign 2) at the gate mouth, one side of the axis
        tp = P(14.9, b) + tdir(b) * (s['w'] / 2 - 0.9)
        rect_at(D, tp, d(b), tdir(b), 0.3, 0.08, fill=BRONZE, edge=None, z=6)
        sign_mark(D, tp + d(b) * 0.9, 2)
        # gate marker (sign 1) on the canopy beam at the street end
        q = P(min(c['R_out'], 29.0) - 0.2, b); sign_mark(D, q, 1)
        label(D, q + d(b) * 1.1, s['k'], 1.6, INK, tang_rot(b), 'bold')

def gf_furniture(D, full):
    shops_gf(D, full); cafe_gf(D); info_gf(D, full); nursing_gf(D)
    if full:
        court_gf(D); gates_gf(D); tactile_gf(D)
        sign_mark(D, P(R_GF + 0.8, M.mid('G31')[0] - 3.0), 5)

# ------------------------------------------------------------------------------------------------ L1
def bridge_l1(D):
    for k, (nm, cap, b, km, col) in ST.items():
        D.line([P(RG.R_BG0 + 0.05, b), P(RG.R_BG1 - 0.05, b)], 'A-FLOR', lw=0.3, color=BRASS, z=4.5)
        side = -1 if k in ('KDH', 'PNG') else 1                       # Kedah / Penang plates on the other side of their line
        q = P((RG.R_BG0 + RG.R_BG1) / 2, b) + tdir(b) * 0.55 * side
        label(D, q, f'{nm}\n{cap} {km} KM', 0.85, '#8A6A20', rad_rot(b), 'bold')
    for s in SC.SPINES:
        label(D, P((RG.R_BG0 + RG.R_BG1) / 2, s['b']), s['k'], 1.1, INK, tang_rot(s['b']), 'bold')

def balcony_l1(D):
    # ledge + stools on the inner deck edge (R11.2-11.55), walk R9.5-11 kept clear 1500; 132-273 deg
    b0, b1 = 133.5, 271.5
    for a, c in ((b0, 180.0), (185.0, 238.0), (247.5, b1)):          # gaps at the Selatan + Tengah walkways and lift 2
        D.poly(arc_band(11.2, 11.55, a, c), 'A-FURN', fill='white', edge=INK, lw=0.08, z=5.4)
        for b in np.arange(a + 1.5, c - 1.0, 2.8): D.circle(P(11.85, b), 0.17, 'A-FURN', fill='white', edge=INK, lw=0.06, z=5.5)
    label(D, P(12.7, 160), 'ANJUNG TALAM · LEDGE + STOOLS', 1.1, '#2E6E8E', tang_rot(160), 'bold')

def stalls_l1(D):
    """Gerai Lipat 2 x 2 m folding market stalls on Dek Pekan Sehari (market days), backs to the gap, fronts on a 2.9 m aisle"""
    deck = [g for g in M.decks('L1') if min(rad(c) for c in g.exterior.coords) > 20 and g.area > 200][0]
    n = 0; b = 146.5
    while b < 324:
        p = P(22.6, b); t = tdir(b); v = d(b)
        sq = Polygon([p - t - v, p + t - v, p + t + v, p - t + v])
        clear = all(abs(((b - s['b'] + 180) % 360) - 180) > math.degrees(3.4 / 22.6) for s in SC.SPINES)
        if deck.buffer(-0.02).contains(sq) and clear:
            D.poly(sq, 'A-FURN', fill='#FBF4E4', edge=INK, lw=0.07, ls='--', z=5.4); n += 1
            b += math.degrees(2.4 / 22.6)
        else: b += 0.5
    label(D, P(24.2, 214), f'DEK PEKAN SEHARI · {n} GERAI LIPAT 2 x 2 (MARKET DAYS)', 1.15, '#7A5A20', tang_rot(214), 'bold')
    label(D, P(24.2, 280), 'AISLE 1400 + FIN WALK 1500', 0.95, '#7A5A20', tang_rot(280))
    # Anjung Timur: fixed benches + planters
    for b in (20.5, 27.0, 59.0, 66.0): D.poly(arc_band(24.3, 24.75, b, b + 4.0), 'A-FURN', fill='#F4F1EA', edge=INK, lw=0.07, z=5.4)
    label(D, P(23.2, 63), 'ANJUNG TIMUR', 1.1, '#7A5A20', tang_rot(63), 'bold')
    return n

def hall_l1(D):
    r = room('L12'); bm, b0, b1 = M.mid('L12')
    for o in (0.2, 0.4, 0.6, 0.8):                                     # 4 mobile cooking islands 1800 x 900
        b = b0 + (b1 - b0) * o; rect_at(D, P(23.4, b), tdir(b), d(b), 0.9, 0.45, fill='#E9EDF0')
        for s in (-1, 1): D.circle(P(23.4, b) + tdir(b) * 0.45 * s, 0.17, 'A-FURN', edge=INK, lw=0.06, z=5.5)
    G = Wall(r, 'cw'); D.poly(G.rect(21.8, 24.6, 0.0, 0.45), 'A-FURN', fill=tint(HALL, 0.4), edge=INK, lw=0.08, z=5.4)
    label(D, G.W(23.2, 0.9), 'POTS + TALAM SHELVES', 0.95, INK, rad_rot(b1))
    label(D, P(25.0, bm), 'ANYAMAN ACOUSTIC BAFFLES OVER · 4 REWANG ISLANDS (INDUCTION)', 0.95, '#7A5A20', tang_rot(bm))

def admin_l1(D, full=True):
    r = room('L21'); bm, b0, b1 = M.mid('L21')
    D.poly(arc_band(23.9, 24.5, b0 + 1.2, b1 - 1.4), 'A-FURN', fill=ST['PLS'][4], edge=INK, lw=0.09, z=5.4)
    for b in (b0 + 2.0, b0 + 3.5): chair(D, P(25.3, b))
    label(D, P(22.6, bm), 'GUA KELAM DESK', 0.9, '#8A4A10', rad_rot(bm), 'bold')
    if full: sign_mark(D, P(22.6, b0 - 1.2), 6)
    r = room('L24'); bm, b0, b1 = M.mid('L24')
    for o in np.linspace(0.12, 0.88, 5):                               # 5 workstations along the inner glass
        b = b0 + (b1 - b0) * o; rect_at(D, P(22.0, b), tdir(b), d(b), 0.7, 0.35); chair(D, P(22.75, b))
    D.poly(arc_band(24.55, 24.95, b0 + 1.0, b1 - 1.0), 'A-FURN', fill='#F4F1EA', edge=INK, lw=0.07, z=5.4)
    label(D, P(23.6, bm), 'FILE + PRINT WALL ON THE SOLID SIDE', 0.9, INK, tang_rot(bm))
    r = room('L25'); bm, b0, b1 = M.mid('L25')
    rect_at(D, P(13.9, bm), tdir(bm), d(bm), 0.8, 0.4); chair(D, P(14.6, bm)); chair(D, P(13.1, bm - 1.5)); chair(D, P(13.1, bm + 1.5))
    r = room('L26'); bm, b0, b1 = M.mid('L26')
    D.poly(arc_band(12.7, 13.8, b0 + 3.5, b1 - 3.5), 'A-FURN', fill='white', edge=INK, lw=0.09, z=5.4)
    for b in np.linspace(b0 + 4.5, b1 - 4.5, 4):
        chair(D, P(12.25, b)); chair(D, P(14.25, b))
    label(D, P(15.0, bm), 'FROSTED BAND 1000-1600 TO THE WALK', 0.85, INK, tang_rot(bm))

def l1_furniture(D, full):
    balcony_l1(D); stalls_l1(D); hall_l1(D); admin_l1(D, full)
    if full: bridge_l1(D)

# ------------------------------------------------------------------------------------------------ L2
def gallery_l2(D):
    r = room('M01'); bm, b0, b1 = M.mid('M01')
    # freestanding curved Peta Rasa map wall in front of the outer glass (R14.6-14.8), 11 showcases on its face
    a, c = b0 + 7, b1 - 7
    D.poly(arc_band(14.55, 14.8, a, c), 'A-FURN', fill=tint(GAL, 0.2), edge=INK, lw=0.09, z=5.4)
    for b in np.linspace(a + 2, c - 2, 11): rect_at(D, P(14.3, b), tdir(b), d(b), 0.3, 0.2, fill='white', lw=0.06)
    label(D, P(13.75, bm), 'PETA RASA MAP WALL · 11 SHOWCASES', 1.0, '#4A3A8A', tang_rot(bm), 'bold')
    for o in (0.33, 0.67):                                             # two low curved plinths
        b = b0 + (b1 - b0) * o; D.poly(arc_band(12.2, 12.8, b - 4, b + 4), 'A-FURN', fill='white', edge=INK, lw=0.08, z=5.4)
    rect_at(D, P(12.5, bm), tdir(bm), d(bm), 0.3, 0.2, fill=BRONZE, edge=None)
    label(D, P(11.8, bm + 6), 'TOUCH SCREEN', 0.85, INK, tang_rot(bm))

def shaf(D, key, mihrab_b):
    r = room(key); g = r['poly'].buffer(-0.3); q = d(QIBLA); n = np.array([-q[1], q[0]])
    proj = [float(np.dot(np.array(c) - C, q)) for c in g.exterior.coords]
    for k in np.arange(max(proj) - 0.9, min(proj), -1.2):
        ln = LineString([C + q * k - n * 40, C + q * k + n * 40]).intersection(g)
        for s in getattr(ln, 'geoms', [ln]):
            if s.geom_type == 'LineString' and s.length > 0.3: D.line(list(s.coords), 'A-FLOR', lw=0.12, color='#8A6A20', z=4.8)
    cx = np.array(r['poly'].centroid.coords[0])
    D.line([cx - q * 1.0, cx + q * 1.6], 'A-ANNO', lw=0.18, color=SIGN); D.text(cx + q * 2.0 - n * 0.6, f'QIBLA {QIBLA}°', 'A-ANNO', size=1.2, color=SIGN, halo=True, z=9.3)
    m = P(15.3, mihrab_b); D.poly(Point(m).buffer(0.5).intersection(SC.disc(15.42)), 'A-FURN', fill=tint(PRAY, 0.2), edge=INK, lw=0.09, z=5.4)
    label(D, P(14.1, mihrab_b), 'MIHRAB', 0.9, '#6E5A20', tang_rot(mihrab_b), 'bold')
    # shoe rack inside the door
    dd = [x for x in M.DOORS if x['key'] == key][0]; bd = brg(dd['p'])
    for sg in (-1, 1):
        D.poly(arc_band(11.15, 11.5, bd + sg * math.degrees(0.8 / 11.2), bd + sg * math.degrees(2.0 / 11.2)), 'A-FURN', fill='white', edge=INK, lw=0.07, z=5.4)

def prayer_l2(D):
    shaf(D, 'M10', QIBLA)
    b1 = M.mid('M12')[2]; shaf(D, 'M12', b1 - 3.0)
    label(D, P(12.2, M.mid('M10')[0] + 6), 'SHAF LINES ⟂ QIBLA', 0.9, '#6E5A20', tang_rot(M.mid('M10')[0]))
    label(D, P(12.2, M.mid('M12')[0] - 5), 'SHAF LINES ⟂ QIBLA (28° TO THE ROOM)', 0.9, '#6E5A20', tang_rot(M.mid('M12')[0]))
    label(D, P(15.9, M.mid('M10')[0]), 'GIRIH SCREEN ON QIBLA GLASS', 0.9, '#6E5A20', tang_rot(M.mid('M10')[0]))
    for k in ('M11', 'M13'):                                            # wudhu taps + stools on the outer wall
        r = room(k); bm, b0, b1 = M.mid(k)
        D.poly(arc_band(14.85, 15.3, b0 + 0.8, b1 - 0.8), 'A-FIXT', fill='white', edge=INK, lw=0.08, z=5.4)
        for b in np.linspace(b0 + 1.6, b1 - 1.6, 4): D.circle(P(14.45, b), 0.16, 'A-FURN', edge=INK, lw=0.06, z=5.5)

def family_l2(D):
    r = room('M14'); bm, b0, b1 = M.mid('M14'); col = ST['TRG'][4]
    D.poly(arc_band(14.6, 15.15, b0 + 3, b1 - 9), 'A-FURN', fill=tint(col, 0.5), edge=INK, lw=0.09, z=5.4)
    for b in np.arange(b0 + 4, b1 - 9, 1.6): D.line([P(14.6, b), P(15.15, b)], 'A-FURN', lw=0.05, color=INK, z=5.5)
    label(D, P(13.8, bm - 3), 'PERAHU BENCH (CHENGAL RIBS)', 0.95, '#0B6E64', tang_rot(bm), 'bold')
    c = P(13.3, b1 - 4.5); D.poly(Point(c).buffer(0.9), 'A-FURN', fill=tint(col, 0.75), edge=INK, lw=0.07, z=5.3)
    D.poly(arc_band(14.9, 15.25, b1 - 7.5, b1 - 1.5), 'A-FURN', fill='white', edge=INK, lw=0.07, z=5.4)
    label(D, c, "KIDS' CORNER", 0.9, '#0B6E64')
    rect_at(D, P(11.6, b0 + 3.0), tdir(b0), d(b0), 0.25, 0.2, fill='white')
    label(D, P(12.4, b0 + 3.3), 'WATER', 0.8, INK)
    label(D, P(12.4, b0 + 8.5), 'PRAM BAY', 0.8, INK)

def decks_l2(D):
    for a, c in ((50, 60), (70, 80), (95, 105), (205, 215), (222, 232)):
        D.poly(arc_band(14.8, 15.25, a, c), 'A-FURN', fill='#F4F1EA', edge=INK, lw=0.07, z=5.4)
    label(D, P(13.0, 88), 'ANJUNG SUNGAI', 1.1, '#2E6E8E', tang_rot(88), 'bold')
    label(D, P(13.0, 218), 'ANJUNG SENJA', 1.1, '#2E6E8E', tang_rot(218), 'bold')

def l2_furniture(D, full):
    gallery_l2(D); prayer_l2(D); family_l2(D); decks_l2(D)

# ------------------------------------------------------------------------------------------------ common to all floors
def themes(D, fl):
    for r in ROOMS:
        if r['fl'] != fl or r['kind'] in ('stair', 'lift', 'open'): continue
        D.poly(r['poly'], 'A-FLOR', fill=theme_fill(r), edge=None, z=0.4)
def level_sign_point(dd):
    """on the core wall beside the door: the side whose wall (just behind the point) belongs to the same core"""
    c = CORES[dd['key'].split('-')[0]]; p0 = np.array(dd['p']); n = np.array(dd['n']); t = np.array(dd['t'])
    for sg, off in ((-1, 0.45), (1, 0.45), (-1, 0.75), (1, 0.75)) if dd['kind'] == 'lift' else ((1, 0.75), (-1, 0.75), (1, 0.45), (-1, 0.45)):
        q = p0 + t * sg * (dd['w'] / 2 + off)
        if c['fp'].buffer(0.05).contains(Point(q - n * 0.25)): return q + n * 0.4
    return p0 + n * 0.9
def level_signs(D, fl):
    for dd in M.CORE_DOORS:
        if dd['fl'] != fl: continue
        p = level_sign_point(dd)
        sign_mark(D, p, 3)

# rooms whose furniture comes from this module (plans.fit skips them, so the A- and I- plans show the same layout)
REFIT = {'G31', 'G20', 'G21', 'L12', 'L21', 'L24', 'L25', 'L26', 'M01', 'M10', 'M12', 'M11', 'M13', 'M14'}
def furniture(D, fl, full=False):
    """called by plans.plan_drawing in 'arch' (full=False) and 'int' (full=True) mode"""
    {'GF': gf_furniture, 'L1': l1_furniture, 'L2': l2_furniture}[fl](D, full)

def interior_overlay(D, fl):
    themes(D, fl); level_signs(D, fl)

# ------------------------------------------------------------------------------------------------ plan sheets
INT_LEGEND = [('fill', dict(fill=tint(HOST, 0.6)), 'HOST THEME: PAHANG RIVER (COURT, ARCADE, WC, INFO)'),
              ('fill', dict(fill=tint(ST['MLK'][4], 0.72)), 'GUEST STATE ROOM (TINT OF THE STATE COLOUR)'),
              ('fill', dict(fill=tint(ADMIN, 0.8)), 'ADMIN'), ('fill', dict(fill=tint(HALL, 0.7)), 'DAPUR REWANG HALL + STORES'),
              ('fill', dict(fill=tint(GAL, 0.75)), 'GALERI PETA RASA'), ('fill', dict(fill=tint(PRAY, 0.75)), 'SURAU + WUDHU (NEUTRAL)'),
              ('line', dict(lw=0.6, color=ST['JHR'][4]), 'FEATURE BACK WALL (STATE)'), ('line', dict(lw=0.45, color=BRASS), 'BRASS INLAY / THRESHOLD'),
              ('line', dict(lw=0.35, color='#E3B505'), 'TACTILE GUIDE PATH (MS 1184)'), ('fill', dict(fill='white'), 'FURNITURE / FITTINGS'),
              ('fill', dict(fill='#FBF4E4', edge=INK), 'GERAI LIPAT (MARKET DAYS ONLY)'),
              ('fill', dict(fill=SIGN, edge=SIGN), 'SIGN LOCATION, TYPE 1-9 (SEE I-300)')]
INT_NOTES = ['INTERIOR STUDY (16.11.2026): HOST STATE PAHANG DRESSES THE SHARED SPACES; EACH SHOP + SPECIAL ROOM TAKES ONE GUEST STATE. ONE SHOPFRONT KIT + ONE UNIQUE LAYER (SCREEN, COLOUR, BACK WALL, SIGNATURE) - SEE I-200.',
             'STATE COLOURS = CRIT 1 PALETTE. NO STATE CRESTS OR FLAGS ARE USED.',
             'NO FURNITURE IN THE ARCADE (3200 CLEAR), ON THE RING BRIDGE, THE WALKWAYS, THE GALLERY WALK OR THE FIN WALK: THESE ARE ESCAPE ROUTES.',
             'ROOM PLATES (SIGN 6) AT EVERY DOOR, LATCH SIDE: NOT ALL SHOWN. STATUTORY EXIT / FIRE SIGNS: SEE F-100 TO F-102.',
             'FINISHES: SEE THE SCHEDULE ON THE RIGHT AND A-600.']

SCHED = {
 'GF': [('TALAM COURT', 'HOST', 'TERRAZZO + RIVER BANDS, BRASS RING', 'TENUN ALUMINIUM LINING (FUNNEL)', '150-200 LX 3000 K'),
        ('ARCADE', 'HOST', 'TERRAZZO, TACTILE PATH', 'WHITE ALUMINIUM RADIAL BAFFLES', '150-200 LX 3000 K'),
        ('SHOPS A2-1..A1-4', 'STATE (I-200)', 'TERRAZZO TILE LIGHT GREY', 'GYPSUM +3.300, OPEN AT 2 ROOFLIGHT BANDS', '300-500 LX 3000 K'),
        ('CAFE G31', 'KELANTAN', 'TERRAZZO; BUNGA TELANG COUNTER', 'GYPSUM + WAU BULAN LIGHT', '300 LX 3000 K'),
        ('INFO G20 / FIRST AID G21', 'HOST', 'VINYL SHEET (G21), TERRAZZO', 'MINERAL FIBRE', '300-500 LX 4000 K'),
        ('WC G01 / G02, NURSING', 'HOST', 'PORCELAIN R11', 'MR BOARD; BLUE-WHITE MOSAIC WALLS', '200 LX; 2700 K DIM (NURSING)'),
        ('BACK OF HOUSE', '—', 'EPOXY', 'EXPOSED', '150-300 LX 4000 K')],
 'L1': [('RING BRIDGE + WALKWAYS', 'HOST', 'HONED PRECAST TERRAZZO R11, 11 BRASS STATE LINES', 'MIDDLE TIER SOFFIT', 'HANDRAIL LED'),
        ('ANJUNG TALAM / DECKS', 'HOST', 'HONED PRECAST TERRAZZO R11', 'FUNNEL / TIER SOFFITS', '100-150 LX'),
        ('DEK PEKAN SEHARI', '—', 'HONED PRECAST TERRAZZO R11, FLOOR BOXES', 'OUTER TIER SOFFIT', '150 LX'),
        ('DAPUR REWANG L12', 'REWANG', 'TERRAZZO', 'ANYAMAN ACOUSTIC BAFFLES', '500 LX ON ISLANDS, DIM'),
        ('RECEPTION L21', 'PERLIS', 'TERRAZZO', 'GUA KELAM FIN DESK', '300 LX 3000 K'),
        ('OFFICES L24-L26', 'ADMIN', 'VINYL PLANK', 'MINERAL FIBRE', '300-500 LX 4000 K'),
        ('WC L04 / L05', 'HOST', 'PORCELAIN R11', 'MR BOARD; MOSAIC WALLS', '200 LX')],
 'L2': [('GALERI PETA RASA M01', 'ALL STATES', 'TERRAZZO', 'TRACK LIGHT', '150-200 LX, 50 ON TEXTILES, UV FILM'),
        ('SURAU M10 / M12', 'NEUTRAL', 'CARPET WITH SHAF LINES', 'ACOUSTIC BOARD; GIRIH SCREEN', '200-300 LX 3000 K DIM'),
        ('WUDHU M11 / M13', 'NEUTRAL', 'PORCELAIN R11', 'MR BOARD', '200 LX'),
        ('SERAMBI PANTAI M14', 'TERENGGANU', 'TERRAZZO', 'FUNNEL SOFFIT', '150-200 LX 3000 K'),
        ('ANJUNG SUNGAI / SENJA', 'HOST', 'HONED PRECAST TERRAZZO R11', 'FUNNEL SOFFIT', '100 LX')]}

def sched_table(side, fl):
    x, y = 850.0, 700.0
    side.text((x, y), f'INTERIOR SCHEDULE · {fl}', 'X-TITL', size=2.4, ha='left', va='top', weight='bold'); y -= 5
    cols = [('SPACE', 0), ('THEME', 34), ('FLOOR', 58), ('CEILING / WALL', 100), ('LIGHT', 140)]
    for t, dx in cols: side.text((x + dx, y), t, 'X-TITL', size=1.5, ha='left', va='top', color='#6B7480')
    y -= 3.6
    import sheets as SH
    for row in SCHED[fl]:
        hs = []
        for (t, dx), v in zip(cols, row):
            w = SH.wrap(v, {0: 17, 34: 12, 58: 21, 100: 20, 140: 16}[dx]); hs.append(w.count('\n') + 1)
            side.text((x + dx, y), w, 'X-TITL', size=1.45, ha='left', va='top')
        y -= 2.2 * max(hs) + 1.4
    y -= 3
    side.text((x, y), 'SIGN TYPES (I-300)', 'X-TITL', size=2.0, ha='left', va='top', weight='bold'); y -= 4
    for n, t in ((1, 'GATE MARKER'), (2, 'DIRECTORY TOTEM'), (3, 'LIFT / STAIR LEVEL SIGN'), (4, 'FASCIA BAND (SHOPFRONT KIT)'), (5, 'BLADE SIGN'),
                 (6, 'ROOM PLATE + BRAILLE'), (7, 'FLOOR COMPASS / INLAYS'), (8, 'TACTILE GUIDE PATH'), (9, 'STATUTORY (SEE F-SHEETS)')):
        sign_mark(side, (x + 2, y - 1), n, size=1.6); side.text((x + 6, y - 1), t, 'X-TITL', size=1.5, ha='left', va='center'); y -= 4.2

def interior_plan(fl, no):
    import build as B
    titles = {'GF': 'GROUND FLOOR · INTERIOR PLAN', 'L1': 'FIRST FLOOR · INTERIOR PLAN', 'L2': 'SECOND FLOOR · INTERIOR PLAN'}
    return B.plan_sheet(fl, no, 'int', titles[fl], interior_overlay, INT_LEGEND, INT_NOTES, sched_table)
