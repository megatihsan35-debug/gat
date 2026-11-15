"""Entrance canopies (Laluan Anyaman) + pocket gardens (inner, gate and outer rings) + the Talam court seating.
All in site metres, built on plan3 / scheme geometry so plans, sections, elevations, site, schedules and 3D agree.

CANOPY: one per gate, on the gate axis, from the court edge (R12.6) through the gate under the hanging first floor and
out to the setback line. Narrow + low at the court, wide + high at the street, so the perspective pulls you to the centre.
Structure: a diamond lattice (anyaman) of champagne ribs in two diagonal families, edge beams with gutters; inside the
gate it hangs from the first-floor slab, outside it stands on V-columns (cantilevered at Selatan to keep the fire
hardstanding clear). Cover: alternating perforated aluminium and fritted laminated glass diamonds."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import unary_union, polylabel
import plan3 as M
from plan3 import C, P, d, tdir, SC, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL

# ------------------------------------------------------------------------------------------------ canopies
R_IN = R_BR1 + 0.1
P_RIB, D_RIB = 1.5, 5.0                     # rib pitch and the axial run of one diagonal across the full width
RIB_DEPTH = dict(inside=0.20, outside=0.25)
Z_IN0, Z_IN1 = 3.90, 4.00                   # edge height at R12.6 and at the first-floor edge (soffit +4.52 / slab +4.80)
RISE_IN, RISE_OUT = 0.40, 0.90              # vault rise at the gate / at the mouth

def _ok_env(b, R, hw):
    a = C + d(b) * R; n = tdir(b)
    return SC.ENV.contains(LineString([a - n * (hw + 0.4), a + n * (hw + 0.4)]))

def _canopy(s):
    b, w = s['b'], s['w']
    hw_in = w / 2 - 0.5
    flare = 2.5
    z_out = 6.2 if s.get('main') else 5.8          # the main (Selatan) mouth is the tallest
    R_out = R_L1
    for R in np.arange(R_L1 + 0.25, 80, 0.25):                # furthest mouth that keeps the whole canopy inside the setback line
        if not _ok_env(b, R, hw_in + flare): break
        R_out = R
    R_out = min(R_out - 0.25, 36.0 if s['k'] == 'TENGAH' else 44.5)   # Tengah stops before the staff parking aisle
    cols = [R_out - 0.9] if s['k'] in ('TIMUR', 'UTARA', 'TENGAH') else []   # Selatan cantilevers: keeps the south hardstanding clear
    return dict(k=s['k'], b=b, w=w, hw_in=hw_in, flare=flare, z_out=z_out, R_in=R_IN, R_gate=R_L1, R_out=R_out, cols=cols, main=bool(s.get('main')))

def place_columns(c, avoid):
    """move each V-column station inwards (towards the gate) until both feet are clear of 'avoid' (parking, hardstanding)"""
    out = []
    for s0 in c['cols']:
        s_ = s0
        while s_ > c['R_gate'] + 2.0:
            feet = [Point(xy(c, s_, sd * 1.12)).buffer(0.6) for sd in (-1, 1)]
            if not any(f.intersects(avoid) for f in feet): break
            s_ -= 0.25
        out.append(s_)
    c['cols'] = out
    return c

CANOPIES = [_canopy(s) for s in SC.SPINES]

def hw(c, s):
    if s <= c['R_gate']: return c['hw_in']
    f = (s - c['R_gate']) / (c['R_out'] - c['R_gate']); return c['hw_in'] + c['flare'] * f
def z_edge(c, s):
    if s <= c['R_gate']: return Z_IN0 + (Z_IN1 - Z_IN0) * (s - c['R_in']) / (c['R_gate'] - c['R_in'])
    f = (s - c['R_gate']) / (c['R_out'] - c['R_gate']); return Z_IN1 + (c['z_out'] - Z_IN1) * math.sqrt(f)
def rise(c, s):
    if s <= c['R_gate']: return RISE_IN
    f = (s - c['R_gate']) / (c['R_out'] - c['R_gate']); return RISE_IN + (RISE_OUT - RISE_IN) * f
def xy(c, s, t): return C + d(c['b']) * s + tdir(c['b']) * (t * hw(c, s))
def z_top(c, s, t): return z_edge(c, s) + rise(c, s) * (1 - t * t)
def rib_depth(c, s): return RIB_DEPTH['inside'] if s <= c['R_gate'] else RIB_DEPTH['outside']

def outline(c, n=40):
    ss = np.linspace(c['R_in'], c['R_out'], n)
    return Polygon([xy(c, s, -1) for s in ss] + [xy(c, s, 1) for s in ss[::-1]])
def ribs(c, nt=14):
    """list of polylines in (s, t); family A: s - t*D/2 = k*P, family B: s + t*D/2 = k*P"""
    out = []
    for fam in (-1, 1):
        k0 = math.floor((c['R_in'] - D_RIB) / P_RIB); k1 = math.ceil((c['R_out'] + D_RIB) / P_RIB)
        for k in range(k0, k1 + 1):
            pts = []
            for t in np.linspace(-1, 1, nt):
                s = k * P_RIB + fam * t * D_RIB / 2
                if c['R_in'] <= s <= c['R_out']: pts.append((s, t))
            if len(pts) > 1: out.append(pts)
    return out
def cell_solid(c, s, t):
    """anyaman weave: alternate diamonds are perforated aluminium (True) or glass (False)"""
    a = s - t * D_RIB / 2; b2 = s + t * D_RIB / 2
    return (math.floor(a / P_RIB) + math.floor(b2 / P_RIB)) % 2 == 0
def column_pts(c):
    """V-columns: ground point just outside each edge, two raking legs up to the edge beam at s +/- 1.4"""
    out = []
    for s in c['cols']:
        for side in (-1, 1):
            g = xy(c, s, side * 1.12)
            out.append(dict(s=s, side=side, base=g, tops=[xy(c, s - 1.4, side), xy(c, s + 1.4, side)], ztops=[z_edge(c, s - 1.4), z_edge(c, s + 1.4)]))
    return out
def hangers(c):
    """hangers drop from the first-floor soffit (+4.52) only where there is floor above: not under the two gaps that run
    across the gate passage (there the edge beam spans between hangers and the lattice is seen from the bridge)"""
    out = []
    above = M.PLATE['L1'].buffer(-0.25)
    for s in np.arange(c['R_in'] + 1.2, c['R_gate'] - 0.4, 1.2):
        for side in (-1, 1):
            q = xy(c, s, side)
            if above.contains(Point(q)) and not any(np.hypot(*(np.array(q) - np.array(h[0]))) < 2.0 for h in out): out.append((q, z_edge(c, s), 4.52))
    return out

CANOPY_FP = unary_union([outline(c) for c in CANOPIES])
COL_FP = unary_union([Point(q['base']).buffer(0.6) for c in CANOPIES for q in column_pts(c)])

# ------------------------------------------------------------------------------------------------ Talam court (inner ring)
PLAY = (50.0, 125.0)                          # moved clear of the Timur gate (27.9°): the gate now opens onto seating, not the play area
PLAY_R = (3.3, 7.7)
POCKET_IN_R = (8.3, 9.3); BENCH_IN_R = (7.85, 8.3)        # planter runs to R9.3: arcade stays 3.2 m clear to the shopfronts
TABLE_R = (5.0, 5.8); BENCH_T_IN = (4.35, 4.8); BENCH_T_OUT = (6.0, 6.45)
SEAT_W = 0.50                                # bench seat width per person (450-500 typical)

def gate_halfangle(s, r, margin=2.0):
    return math.degrees(math.asin(min(1.0, (s['w'] / 2) / r))) + margin
def free_arcs(r, avoid):
    """arcs (start, end) in degrees at radius r that miss every interval in avoid (list of (a, b), may wrap)"""
    blocked = np.zeros(3600, bool)
    for a, b in avoid:
        a10, b10 = int(round(a * 10)), int(round(b * 10))
        for k in range(a10, b10): blocked[k % 3600] = True
    arcs, i = [], 0
    if blocked.all(): return []
    start = int(np.argmax(blocked))                # begin scanning at a blocked cell so arcs don't split at 0°
    cur = None
    for j in range(3600):
        k = (start + j) % 3600
        if not blocked[k] and cur is None: cur = k
        if blocked[k] and cur is not None:
            arcs.append((cur / 10, (cur + ((k - cur) % 3600)) / 10)); cur = None
    if cur is not None: arcs.append((cur / 10, (cur + ((start - cur) % 3600)) / 10))
    return arcs

def inner_pockets():
    r = (POCKET_IN_R[0] + POCKET_IN_R[1]) / 2
    avoid = [(s['b'] - gate_halfangle(s, r), s['b'] + gate_halfangle(s, r)) for s in SC.SPINES]
    out = []
    for a, b in free_arcs(r, avoid):
        span = b - a; n = int((span + 8) // (16 + 8))
        if n < 1:
            if span >= 12: n = 1
            else: continue
        width = min(16.0, span - 4)
        gap = (span - n * width) / (n + 1)
        for i in range(n):
            a0 = a + gap + i * (width + gap); out.append((a0, a0 + width))
    return out
INNER = inner_pockets()

def table_arcs():
    avoid = [(PLAY[0] - 3, PLAY[1] + 3)] + [(s['b'] - 6.5, s['b'] + 6.5) for s in SC.SPINES]
    return free_arcs((TABLE_R[0] + TABLE_R[1]) / 2, avoid)
TABLES = table_arcs()

def seats():
    inner = sum(int(math.radians(b - a) * (BENCH_T_IN[0] + BENCH_T_IN[1]) / 2 / SEAT_W) for a, b in TABLES)
    outer = sum(int(math.radians(b - a) * (BENCH_T_OUT[0] + BENCH_T_OUT[1]) / 2 / SEAT_W) for a, b in TABLES)
    pocket = sum(int(math.radians(b - a) * (BENCH_IN_R[0] + BENCH_IN_R[1]) / 2 / SEAT_W) for a, b in INNER)
    return dict(table_inner=inner, table_outer=outer, pocket_benches=pocket, total=inner + outer + pocket)

def ann_sec(r0, r1, a, b): return SC.ann(r0, r1).intersection(SC.sector(a, b))
def play_poly(): return ann_sec(PLAY_R[0], PLAY_R[1], *PLAY)

# ------------------------------------------------------------------------------------------------ gate + outer pockets
def sky_pockets():
    """inner ring, upper level: planter troughs on the court balcony of the first floor, along its edge to the gap (R14.0-15.25), cut every 30° with
    1.6 m gaps, kept clear of rooms, cores, doors and the walkway landings"""
    fl = 'L1'
    band = SC.ann(14.0, 15.25).intersection(M.PLATE[fl])
    rooms = unary_union([r['poly'] for r in M.ROOMS if r['fl'] == fl and r['kind'] != 'open']).buffer(0.6)
    cores = unary_union([c['fp'] for c in M.CORES.values()]).buffer(1.0)
    doors = unary_union([Point(dd['p']).buffer(1.5) for dd in M.DOORS if [q for q in M.ROOMS if q['key'] == dd['key']][0]['fl'] == fl] +
                        [Point(dd['p']).buffer(1.5) for dd in M.CORE_DOORS if dd['fl'] == fl])
    slots = unary_union([SC.strip(s['b'], 3.3 + 1.6, 9.0, 16.0) for s in SC.SPINES])        # keep the walkway landings clear
    cuts = unary_union([LineString([P(12.0, b), P(15.0, b)]).buffer(0.8) for b in np.arange(7.5, 360, 30.0)])
    g = band.difference(rooms).difference(cores).difference(doors).difference(slots).difference(cuts)
    return [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon' and q.area >= 1.5]
SKY = sky_pockets()

def _doors_gf(): return unary_union([Point(dd['p']).buffer(1.8) for dd in M.DOORS if [q for q in M.ROOMS if q['key'] == dd['key']][0]['fl'] == 'GF'])

def gate_pockets():
    """planted pockets in the concave bite of each gate, under the hanging first floor, either side of the canopy"""
    out = []
    doors = _doors_gf()
    for s, c in zip(SC.SPINES, CANOPIES):
        zone = SC.GF_VOID.intersection(SC.ann(R_GF - 3.0, R_L1 - 0.4)).intersection(SC.sector(s['b'] - 40, s['b'] + 40))
        g = zone.difference(outline(c).buffer(0.9)).difference(doors).difference(SC.strip(s['b'], s['w'] + 1.6))
        g = g.buffer(-0.25, join_style=2).buffer(0.25, join_style=2)
        for q in getattr(g, 'geoms', [g]):
            if q.geom_type == 'Polygon' and q.area >= 3.0: out.append(dict(k=s['k'], poly=q))
    return out

def outer_pockets(exclude):
    """outer ring R31-39 inside the setback line, cut into pockets with 2 m paths between them every 10°"""
    band = SC.ann(31.0, 39.0).intersection(SC.ENV)
    g = band.difference(exclude)
    cuts = unary_union([LineString([P(30.0, b), P(41.0, b)]).buffer(1.0) for b in np.arange(0, 360, 10.0)])
    g = g.difference(cuts).buffer(-0.3, join_style=1).buffer(0.3, join_style=1)
    out = []
    for q in getattr(g, 'geoms', [g]):
        if q.geom_type == 'Polygon' and q.area >= 8.0:
            out.append(q)
    return out

PALETTE = {
    'INNER': ('TAMAN TEDUH · SHADE GARDEN', 'PALAS PALM, BIRD\'S NEST FERN, CALATHEA, KELADI, PHILODENDRON; DRIP IRRIGATION; 600 SOIL ON PLINTH FILL'),
    'GATE': ('TAMAN GERBANG · SCENTED GATE GARDEN', 'KEMUNING (MURRAYA), MELUR (JASMINE), CEMPAKA, PANDAN; UNDER THE HANGING FIRST FLOOR, PART SHADE'),
    'OUTER': ('TAMAN ULAM · HERB + RAIN GARDEN', 'KETAPANG KENCANA / TANJUNG TREES; SERAI, KESUM, DAUN KARI, KUNYIT, LENGKUAS, ULAM RAJA FOR THE CAFE + DEMO KITCHEN; BIORETENTION BASE TO MSMA'),
}
