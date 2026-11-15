"""Roof plan (1:100) with roof drainage, and site plan (1:200) with fire appliance access, hydrants, external services,
parking and the utility block. All geometry in site metres."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import unary_union, polylabel
from shapely import affinity
from cad import Drawing, INK
import plan3 as M
from plan3 import C, P, d, tdir, SC, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, R_OCULUS, S4
import plans

R_ROOF, R_DISC = SC.R_ROOF, SC.R_DISC
ROOF_FP = SC.ann(M.R_ROOF_IN, R_ROOF).difference(SC.RF_VOID)
BLUE = '#1F6FB2'; CYAN = '#1AA0C8'; BROWN = '#8A5A2B'; RED = '#D0312D'; GREEN = '#3E7D3A'; MAG = '#9B2D8E'; ORANGE = '#C9690A'
def brg(p): v = np.array(p) - C; return math.degrees(math.atan2(v[0], v[1])) % 360
def rad(p): return float(np.hypot(*(np.array(p) - C)))
LOW = [s for s in SC.SPINES if not s['crest']]           # Timur, Tengah: valleys of the wave roof

# ------------------------------------------------------------------------------------------------ rainwater (shared with plumbing)
I_RAIN = 250.0                                            # mm/h, 5-min design storm (MSMA 2nd ed. range for Pahang ~ 200-260; to confirm)
def rwdp_points():
    """perimeter downpipes Ø150 at R26.7 (behind the fins), evenly spaced per petal, clear of the gate slots; + 2 at each valley gate"""
    out = []
    for p in SC.PETALS:
        half = [math.degrees(math.asin((s['gap'] / 2 + 1.2) / 26.7)) for s in SC.SPINES]
        i = SC.NAMES.index(p['name']); a0 = p['b0'] + half[i]; a1 = p['b0'] + p['span'] - half[(i + 1) % 4]
        n = max(2, round(math.radians(a1 - a0) * 26.7 / 9.5))
        out += [(P(26.7, a0 + (a1 - a0) * (k + 0.5) / n), 'P') for k in range(n)]
    for s in LOW:
        for sg in (-1, 1):
            out.append((C + d(s['b']) * 26.7 + tdir(s['b']) * sg * (s['gap'] / 2 + 0.25), 'V'))
    return out
RWDP = rwdp_points()
def rain_calc():
    A_roof = ROOF_FP.area; A_fun = SC.ann(R_OCULUS, R_DISC).area
    q = lambda A: I_RAIN / 3600.0 * A                      # L/s with C = 1.0 (A in m2, I in mm/h -> L/s)
    n = len(RWDP)
    return dict(A_roof=A_roof, A_fun=A_fun, Q_roof=q(A_roof), Q_fun=q(A_fun), n=n, per=q(A_roof) / n)

def arrow(D, a, b, layer, color, lw=0.18, head=0.45):
    a, b = np.array(a), np.array(b); t = (b - a) / np.linalg.norm(b - a); n = np.array([-t[1], t[0]])
    D.line([a, b], layer, lw=lw, color=color)
    D.poly(Polygon([b, b - t * head + n * head * 0.4, b - t * head - n * head * 0.4]), layer, fill=color, edge=None)

# ------------------------------------------------------------------------------------------------ roof plan
def roof_drawing():
    D = Drawing('ROOF PLAN')
    D.poly(SC.disc(R_L1), 'A-HIDN', edge='#9AA3AD', lw=0.13, ls='--', z=1)
    D.poly(ROOF_FP, 'A-ROOF', fill='#EEF0F2', edge=INK, lw=0.35, z=2)
    # standing seams run along the fall: arcs every 1.0 m
    for r in np.arange(M.R_ROOF_IN + 0.5, R_ROOF, 1.0):
        for g in getattr(SC.disc(r).exterior.intersection(ROOF_FP), 'geoms', []):
            if g.geom_type == 'LineString' and g.length > 0.5: D.line(list(g.coords), 'A-ROOF', lw=0.05, color='#9AA3AD', z=3)
    # concealed perimeter gutter + valley gutters at the low gates
    D.poly(SC.ann(R_ROOF - 0.45, R_ROOF - 0.05).intersection(ROOF_FP), 'P-RAIN', fill='#D8ECF7', edge=CYAN, lw=0.09, z=4)
    for s in LOW:
        for sg in (-1, 1):
            off = tdir(s['b']) * sg * ((s['gap'] - 1.0) / 2 + 0.25)
            D.poly(LineString([C + d(s['b']) * M.R_ROOF_IN + off, C + d(s['b']) * (R_ROOF - 0.3) + off]).buffer(0.25, cap_style=2), 'P-RAIN', fill='#D8ECF7', edge=CYAN, lw=0.09, z=4)
            arrow(D, C + d(s['b']) * 16 + off, C + d(s['b']) * 22 + off, 'P-RAIN', CYAN, lw=0.13, head=0.4)
    # fall arrows (tangential, towards the valleys) + 3° radial cross fall to the perimeter gutter
    for p in SC.PETALS:
        for k in range(1, 8):
            b = p['b0'] + p['span'] * k / 8; h0 = SC.roof_h(b); h1 = SC.roof_h(b + 2.5)
            sgn = 1 if h1 < h0 else -1
            for r in (16.5, 22.5):
                a = P(r, b); bb = P(r, b + sgn * math.degrees(3.4 / r)); arrow(D, a, bb, 'A-ROOF', INK, lw=0.13, head=0.42)
            D.text(P(25.2, b), f'+{SC.roof_h(b):.2f}', 'A-ROOF', size=1.6, rot=0, color=INK, halo=True)
            arrow(D, P(19.5, b + 1.2), P(21.0, b + 1.2), 'A-ROOF', '#6B7480', lw=0.09, head=0.3)
    for s in SC.SPINES:
        D.text(P(29.6, s['b']), f"{s['k']} GATE\nRIDGE +{SC.roof_h(s['b']):.3f}" if s['crest'] else f"{s['k']} GATE\nVALLEY +{SC.roof_h(s['b']):.3f}", 'A-ANNO', size=1.8, weight='bold', halo=True)
    # funnel roof over the court: falls to the oculus, rain drops into the Titik pool
    fun = SC.ann(R_OCULUS, R_DISC)
    D.poly(fun, 'A-ROOF', fill='#F7F7F8', edge=INK, lw=0.3, z=2)
    for b in np.arange(0, 360, 7.5): D.line([P(R_OCULUS + 0.2, b), P(R_DISC - 0.2, b)], 'A-ROOF', lw=0.05, color='#9AA3AD', z=3)
    for b in range(15, 360, 45): arrow(D, P(10.0, b), P(5.0, b), 'P-RAIN', CYAN, lw=0.18, head=0.5)
    D.circle(C, R_OCULUS, 'A-ROOF', fill='#D8ECF7', edge=CYAN, lw=0.2, z=4)
    D.circle(C, 0.18, 'A-COLS', fill=INK, edge=None, z=6)
    D.text(P(6.6, 200), 'FUNNEL ROOF +13.500 RIM\nFALLS TO OCULUS +11.400', 'A-ANNO', size=1.8, halo=True)
    D.text(C + np.array([0, -2.3]), 'OCULUS Ø3000 · RAIN TO TITIK POOL', 'A-ANNO', size=1.5, halo=True)
    # downpipes
    for p, kind in RWDP:
        D.circle(p, 0.2, 'P-RAIN', fill='white', edge=CYAN, lw=0.25, z=7)
    D.text(RWDP[0][0] + np.array([0.6, 0.5]), 'RWDP Ø150', 'P-RAIN', size=1.5, color=CYAN, ha='left', halo=True)
    # core 2 tank room below the roof (dashed) + roof access hatch
    c2 = M.CORES['C2']; D.poly(plans.M._corefp(c2), 'A-HIDN', edge='#6B7480', lw=0.13, ls='--', z=5)
    D.text(plans.frame(c2['bc'], 0, (c2['v_s0'] + c2['v_s1']) / 2), 'CORE 2 TANK ROOM\nBELOW ROOF, FL +12.900\nCOLD WATER TANK 7.2 M³', 'P-EQPT', size=1.6, color=BLUE, halo=True)
    D.poly(Polygon([plans.frame(c2['bc'], -0.4, c2['v_s1'] - 0.9), plans.frame(c2['bc'], 0.4, c2['v_s1'] - 0.9), plans.frame(c2['bc'], 0.4, c2['v_s1'] - 0.1), plans.frame(c2['bc'], -0.4, c2['v_s1'] - 0.1)]), 'A-ROOF', fill='white', edge=INK, lw=0.18, z=6)
    D.text(plans.frame(c2['bc'], 1.3, c2['v_s1'] - 0.5), 'ROOF\nHATCH', 'A-ANNO', size=1.3, ha='left', halo=True)
    for c in LS.CANOPIES: canopy_plan(D, c, solid=True, region=SC.disc(80).difference(SC.disc(R_ROOF)))
    plans.grid(D, 'RF', color='#B9C0C7'); plans.section_marks(D)
    D.circle(C, 0.25, 'M-ELEC', edge=MAG, lw=0.2, z=7)
    D.text(C + np.array([1.2, 1.0]), 'MAST +30.000 · AIR TERMINAL', 'M-ELEC', size=1.4, color=MAG, ha='left', halo=True)
    return D

# ------------------------------------------------------------------------------------------------ site elements
SITE = SC.SITE; ENV = SC.ENV; PTS = [np.array(p) for p in SC.SITE_PTS]
def edge(i): a, b = PTS[i], PTS[(i + 1) % 8]; t = (b - a) / np.linalg.norm(b - a); n = np.array([-t[1], t[0]]); return a, b, t, n    # n points inward (site is anticlockwise?)
def inward(i):
    a, b, t, n = edge(i)
    return n if SITE.contains(Point((a + b) / 2 + n * 0.5)) else -n
def along(i, s, off=0.0):
    a, b, t, n = edge(i); return a + t * s + inward(i) * off
def rect_on(i, s0, s1, o0, o1):
    return Polygon([along(i, s0, o0), along(i, s1, o0), along(i, s1, o1), along(i, s0, o1)])

E_ROAD, S_ROAD = 2, 4                                     # edge 2-3 = east road, edge 4-5 = south road
def s_at_x(i, x):
    a, b, t, n = edge(i); return (x - a[0]) / t[0]
# utility block on the east road, 6 m back from the boundary (setback), south end of the service yard
UB_S0, UB_D = 53.0, (6.1, 13.0)
_w = [('REFUSE\nWET 18', 2.6), ('REFUSE\nDRY 18', 2.6), ('GENSET\n15', 2.2), ('PUMP\nROOM', 2.2), ('FIRE\nTANK\n9.1 M³', 1.6), ('SUCTION\nTANK\n6 M³', 2.2), ('TNB\nMETER', 1.1)]
UB_ROOMS = []; _s = UB_S0
for _n, _l in _w: UB_ROOMS.append((_n, _s, _s + _l)); _s += _l
UB = rect_on(E_ROAD, UB_S0, _s, *UB_D).intersection(ENV)
SERVICE_DRIVE = None
def service():
    """service yard + 6 m fire appliance accessway from the east road to the loading bay; hardstanding beside the east facade"""
    dr = LineString([along(E_ROAD, 33.0, -1.0), P(R_L1 + 1.0, 93.0)]).buffer(3.0, cap_style=2)
    yard = rect_on(E_ROAD, 14.0, UB_S0, 0.0, 12.0).union(dr).intersection(SITE).difference(SC.disc(R_L1 + 0.5))
    hs_e = rect_on(E_ROAD, 14.0, 42.0, 3.5, 9.5).difference(SC.disc(R_L1 + 0.5))
    return dr.intersection(SITE), yard, hs_e
DRIVE_E, YARD, HS_E = service()
# south forecourt hardstanding (30 t paving, removable bollards), 6 m wide, 1-7 m off the first-floor edge
HS_S = Polygon([(56, -7.2), (86, -7.2), (86, -1.2), (56, -1.2)]).intersection(SITE).difference(SC.disc(R_L1 + 0.3))
# parking off the south road between the Tengah and Selatan forecourts
PARK = []; MOTOR = []
def parking():
    """walking east from x = 38 along the south road (edge 4-5 runs east -> west, so s falls going east)"""
    s0 = s_at_x(S_ROAD, 38.0); s = s0
    for k, w in [('OKU', 3.6)] + [('S', 2.5)] * 5:
        PARK.append((k, rect_on(S_ROAD, s - w, s, 1.0, 6.0))); s -= w
    s1 = s
    for i in range(10): MOTOR.append(rect_on(S_ROAD, s0 + 0.5 + i * 1.0, s0 + 0.5 + (i + 1) * 1.0 - 0.02, 1.0, 3.5))
    aisle = rect_on(S_ROAD, s1, s0 + 11.0, 6.0, 12.0)
    entry = rect_on(S_ROAD, s0 + 4.5, s0 + 10.5, -0.5, 6.0)
    tg = [q for q in SC.SPINES if q['k'] == 'TENGAH'][0]
    return aisle.union(entry).difference(SC.strip(tg['b'], tg['w'] + 3.0, R_GF - 1.0, 95))
AISLE = parking()
BIKES = [rect_on(S_ROAD, s_at_x(S_ROAD, 90.0) - i * 0.8, s_at_x(S_ROAD, 90.0) - i * 0.8 - 0.6, 1.2, 3.0) for i in range(10)]
# arrival garden terrace +0.900 at the foot of stair 4 (west), steps + 1:12 ramp down to ±0.000
TERRACE = SC.sector(268, 290).intersection(SC.ann(R_GF + 1.4, S4['v1'] + 3.0)).buffer(0)
HYDRANTS = [(along(S_ROAD, s_at_x(S_ROAD, 62.0), -1.5), 'H1'), (along(E_ROAD, 30.0, -1.5), 'H2')]
def forecourts():
    out = []
    for s in SC.SPINES:
        g = SC.strip(s['b'], s['w'] + 2.0, R_GF - 1.0, 95).intersection(SITE)
        out.append((s, g))
    return out

# external drainage + sewer (site plan + plumbing)
PERIM_DRAIN_R = 27.4
PROM_R = (R_GF + 1.5, 30.7)               # perimeter promenade (paved) round the building; buried services run under it
SEWER_R, WATER_R, HR_R, LV_R = 28.7, 29.4, 29.9, 30.3
def sewer_runs():
    """IC = inspection chamber. East line takes the toilet stacks + staff restrooms; north line takes the cafe (via grease
    trap); west line takes the musolla wudhu stack and the shop sinks. All fall to MH-S on the south road (public sewer)."""
    mh_s = along(S_ROAD, s_at_x(S_ROAD, 80.0), 2.0)
    R = SEWER_R
    east = [P(R, 50), P(R, 75), P(R, 105), P(R, 135), P(R, 160), mh_s]
    north = [P(R, 350), P(R, 20), P(R, 50)]
    west = [P(R, 300), P(R, 268), P(R, 235), P(R, 205), mh_s]
    return dict(east=east, north=north, west=west, mh=mh_s)
SEWER = sewer_runs()
OSD = rect_on(S_ROAD, s_at_x(S_ROAD, 47.0), s_at_x(S_ROAD, 53.0), 6.5, 10.0)
WATER_IN = along(E_ROAD, 63.0, -0.5)
ASSEMBLY = P(36.5, 147.0)
def service_lines():
    """buried service routes (site metres): used for drawing and to keep pocket gardens off them"""
    return dict(
        water=[along(E_ROAD, 60.0, 13.0), P(WATER_R, 100), P(WATER_R, 75), P(WATER_R, 20), P(WATER_R, 345), P(R_GF, 339)],
        hr=[along(E_ROAD, 61.0, 13.0), P(HR_R, 103), P(HR_R, 93)],
        lv=[along(E_ROAD, 65.0, 13.0), P(LV_R, 104), P(LV_R, 84.0), P(R_GF, 84.0)],
        outfall=[P(PERIM_DRAIN_R, 228), np.array(OSD.centroid.coords[0]), along(S_ROAD, s_at_x(S_ROAD, 50.0), -1.0)])
SERVICE_LINES = service_lines()
import landscape as LS
_avoid_cols = unary_union([AISLE, HS_S, HS_E, YARD] + [k for _, k in PARK] + MOTOR + BIKES)
for _c in LS.CANOPIES: LS.place_columns(_c, _avoid_cols)
LS.COL_FP = unary_union([Point(q['base']).buffer(0.6) for c in LS.CANOPIES for q in LS.column_pts(c)])
def _outer_exclude():
    g = [SC.strip(s['b'], s['w'] + 2.0, R_GF - 1.0, 95).buffer(1.0) for s in SC.SPINES]
    g += [LS.CANOPY_FP.buffer(1.0), LS.COL_FP, HS_E.buffer(0.5), HS_S.buffer(0.5), YARD.buffer(0.5), DRIVE_E.buffer(0.5), AISLE.buffer(0.8),
          TERRACE.buffer(1.0), UB.buffer(1.5), OSD.buffer(0.5), Point(ASSEMBLY).buffer(3.0)]
    g += [k.buffer(0.8) for _, k in PARK] + [k.buffer(0.8) for k in MOTOR + BIKES] + [Point(p).buffer(1.5) for p, _ in HYDRANTS]
    g += [LineString(v).buffer(1.0) for v in SERVICE_LINES.values()] + [LineString(SEWER[k]).buffer(1.0) for k in ('east', 'north', 'west')]
    g += [Point(WATER_IN).buffer(1.5)]
    return unary_union(g)
OUTER = LS.outer_pockets(_outer_exclude())
GATE = LS.gate_pockets()
def pocket_trees():
    """one shade tree in every outer pocket of 14 m2 or more (at its pole of inaccessibility)"""
    out = []
    for q in OUTER:
        if q.area >= 14.0:
            p = polylabel(q, 0.1); out.append(np.array([p.x, p.y]))
    return out
POCKET_TREES = pocket_trees()

def site_drawing(services=True):
    D = Drawing('SITE PLAN')
    # roads beyond the boundary
    for i, nm, w in ((S_ROAD, 'JALAN TOK MUDA AWANG NGAH', 12.0), (E_ROAD, 'JALAN IBRAHIM', 10.0), (3, '', 10.0)):
        a, b, t, n = edge(i); n_out = -inward(i)
        road = Polygon([a - t * 12, b + t * 12, b + t * 12 + n_out * w, a - t * 12 + n_out * w])
        D.poly(road, 'A-SITE', fill='#E3E5E8', edge=None, z=0)
        D.line([a - t * 12 + n_out * 1.5, b + t * 12 + n_out * 1.5], 'A-SITE', lw=0.13, color='#9AA3AD')
        D.line([a - t * 12 + n_out * w / 2 + n_out * 0.75, b + t * 12 + n_out * w / 2 + n_out * 0.75], 'A-SITE', lw=0.09, color='#9AA3AD', ls='--')
        if nm:
            m = (a + b) / 2 + n_out * (w / 2 + 0.75) - t * (10 if i == S_ROAD else 0)
            ang = math.degrees(math.atan2(t[1], t[0])); ang = ang - 180 if abs(ang) > 90 else ang
            D.text(m, nm, 'A-SITE', size=3.2, rot=ang, color='#5B6570', weight='bold')
    D.text(along(0, 30, -4.0), 'PUBLIC PATH (NORTH)', 'A-SITE', size=2.4, color='#5B6570', rot=math.degrees(math.atan2(*(PTS[1] - PTS[0])[::-1])))
    # lawn + boundary + setbacks
    D.poly(SITE, 'A-LAND', fill='#EEF3E8', edge=None, z=0.5)
    D.line(list(SITE.exterior.coords), 'A-SITE', lw=0.5, color=INK, ls='-.', z=6)
    D.poly(ENV, 'A-SITE', edge='#7A8590', lw=0.13, ls='--', z=5)
    for i in range(8):
        a, b, t, n = edge(i); m = (a + b) / 2; inn = inward(i)
        D.text(m + inn * (SC.SETBACKS[i] / 2), f'{SC.SETBACKS[i]} M\nSETBACK', 'A-DIMS', size=1.5, color='#5B6570', halo=True)
    # forecourts + plinth + terrace
    for s, g in forecourts():
        D.poly(g, 'A-SITE', fill='#F3EEE4', edge='#B3A88F', lw=0.09, z=1)
        e = np.array(SC.spine_end(s['b']).coords[0])
        arrow(D, C + d(s['b']) * (rad(e) - 3), C + d(s['b']) * (R_L1 + 1), 'A-ANNO', '#7A6A4A', lw=0.13, head=0.7)
        D.text(C + d(s['b']) * (rad(e) - 7.0) + tdir(s['b']) * (s['w'] / 2 + 2.2), f"{s['k']} FORECOURT\nRAMP 1:{(rad(e) - 6 - R_BR0) / 0.9:.0f} TO +0.900", 'A-ANNO', size=1.8, color='#7A6A4A', halo=True)
    D.poly(SC.ann(*PROM_R).intersection(SITE), 'A-SITE', fill='#EFEAE0', edge='#C9BFAA', lw=0.09, z=1.1)
    D.text(P(PROM_R[1] - 1.2, 205), 'PERIMETER PROMENADE', 'A-ANNO', size=1.4, color='#7A6A4A', rot=-(205 - 90) + 180, halo=True)
    D.poly(SC.disc(R_GF + 1.5), 'A-SITE', fill='#F7F3EA', edge='#B3A88F', lw=0.18, z=1.2)
    D.poly(TERRACE, 'A-SITE', fill='#F7F3EA', edge='#B3A88F', lw=0.18, z=1.2)
    D.text(P(S4['v1'] + 1.5, 284.5), 'ARRIVAL GARDEN\nTERRACE +0.900\n5 STEPS + 1:12 RAMP', 'A-ANNO', size=1.6, halo=True)
    # building
    D.poly(SC.GF, 'A-WALL', fill='#C9CED4', edge=INK, lw=0.25, z=3)
    for c in M.CORES.values(): D.poly(c['stair_wall'], 'A-WALL', fill='#5B6570', edge=None, z=3.2)
    D.poly(SC.disc(R_COURT), 'A-SITE', fill='#FBF6E9', edge=INK, lw=0.18, z=3); D.circle(C, R_POOL, 'A-SITE', fill='#D8ECF7', edge=INK, lw=0.13, z=3.1)
    D.poly(ROOF_FP, 'A-ROOF', fill=None, edge=INK, lw=0.35, ls='--', z=4); D.circle(C, R_DISC, 'A-ROOF', edge=INK, lw=0.18, ls='--', z=4)
    D.poly(S4['poly'], 'A-STRS', fill='white', edge=INK, lw=0.13, z=3.5)
    landscape_plan(D, site=True)
    D.text(C + np.array([0, -5.0]), 'TITIK TEMU\nGF +0.900 · L1 +5.400 · L2 +9.600\nROOF +10.200 TO +16.200 · MAST +30.000', 'A-ANNO', size=2.2, weight='bold', halo=True)
    # utility block + yard + hardstandings + parking
    D.poly(YARD, 'A-SITE', fill='#E6E8EB', edge='#7A8590', lw=0.13, z=1.5)
    D.poly(UB, 'A-WALL', fill='#C9CED4', edge=INK, lw=0.3, z=3)
    for nm, s0, s1 in UB_ROOMS:
        D.line([along(E_ROAD, s1, UB_D[0]), along(E_ROAD, s1, UB_D[1])], 'A-WALL', lw=0.18, color=INK, z=3.1)
        D.text((along(E_ROAD, (s0 + s1) / 2, 9.5)), nm, 'A-ANNO', size=1.2, z=8)
    D.text(along(E_ROAD, UB_S0 + 6.5, 15.5), 'UTILITY BLOCK · SINGLE STOREY RC, ROOF +4.500\nVRF OUTDOOR UNITS ON ROOF', 'A-ANNO', size=1.7, weight='bold', rot=math.degrees(math.atan2(*edge(E_ROAD)[2][::-1])) + 90, halo=True)
    for k, g in PARK:
        D.poly(g, 'A-SITE', fill='white' if k == 'S' else '#DCEBF7', edge=INK, lw=0.13, z=2)
        D.text(np.array(g.centroid.coords[0]), 'OKU\n3600' if k == 'OKU' else 'STAFF', 'A-ANNO', size=1.3, z=8)
    for g in MOTOR: D.poly(g, 'A-SITE', fill='white', edge=INK, lw=0.09, z=2)
    D.text(np.array(unary_union(MOTOR).centroid.coords[0]) + np.array([0, 2.6]), '10 MOTORCYCLE BAYS', 'A-ANNO', size=1.3, halo=True)
    D.poly(AISLE, 'A-SITE', fill='#E6E8EB', edge='#7A8590', lw=0.09, z=1.6)
    D.text(np.array(AISLE.centroid.coords[0]), '6 M AISLE · ENTRY / EXIT', 'A-ANNO', size=1.3, halo=True)
    for g in BIKES: D.poly(g, 'A-SITE', fill='white', edge=INK, lw=0.09, z=2)
    D.text(np.array(unary_union(BIKES).centroid.coords[0]) + np.array([0, 2.6]), '10 BICYCLE STANDS', 'A-ANNO', size=1.3, halo=True)
    # trees along the roads
    for i, nt in ((S_ROAD, 9), (E_ROAD, 6), (0, 6)):
        a, b, t, _ = edge(i); L = np.linalg.norm(b - a)
        for k in range(nt):
            p = a + t * L * (k + 0.5) / nt + inward(i) * 2.0
            if any(g.buffer(1.5).contains(Point(p)) for g in [AISLE, YARD, HS_S, UB, LS.CANOPY_FP] + [g for _, g in forecourts()] + [g for _, g in PARK] + OUTER): continue
            D.circle(p, 2.2, 'A-LAND', fill='#DDE8D3', edge=GREEN, lw=0.09, z=1.8)
    if services: site_services(D)
    return D

def site_services(D):
    # fire appliance access
    for g, nm in ((HS_E, 'FIRE APPLIANCE HARDSTANDING E\n6 M WIDE · 30 T · 2-10 M OFF FACADE'), (HS_S, 'FIRE APPLIANCE HARDSTANDING S\n6 M WIDE · 30 T · REMOVABLE BOLLARDS')):
        D.poly(g, 'F-ESCP', fill=None, edge=RED, lw=0.35, ls='--', z=6, hatch=None)
        D.text(np.array(g.centroid.coords[0]), nm, 'F-ESCP', size=1.6, color=RED, weight='bold', halo=True, z=9)
    arrow(D, along(E_ROAD, 33.0, -4.0), along(E_ROAD, 33.0, 8.0), 'F-ESCP', RED, lw=0.35, head=1.0)
    D.text(along(E_ROAD, 33.0, -6.5), 'BOMBA ACCESS', 'F-ESCP', size=1.8, color=RED, weight='bold', halo=True)
    arrow(D, along(S_ROAD, s_at_x(S_ROAD, 71.0), -4.0), along(S_ROAD, s_at_x(S_ROAD, 71.0), 2.5), 'F-ESCP', RED, lw=0.35, head=1.0)
    for p, nm in HYDRANTS:
        D.circle(p, 0.6, 'F-EQPT', fill=RED, edge=None, z=9); D.text(p + np.array([1.0, 0.0]), f'{nm} PILLAR HYDRANT\n(TWIN 65 MM OUTLETS)', 'F-EQPT', size=1.4, color=RED, ha='left', halo=True)
    D.poly(Point(ASSEMBLY).buffer(0.6), 'F-EQPT', fill=None, edge=RED, lw=0.2)
    D.text(ASSEMBLY + np.array([1.2, 0.0]), 'FIRE ASSEMBLY\nPOINT', 'F-EQPT', size=1.4, color=RED, ha='left', halo=True)
    # perimeter drain + OSD + outfall
    D.circle(C, PERIM_DRAIN_R, 'P-RAIN', edge=CYAN, lw=0.35, z=5)
    D.text(P(PERIM_DRAIN_R + 0.8, 130), '300 U-DRAIN WITH\nGRATING, 1:200 FALL', 'P-RAIN', size=1.4, color=CYAN, ha='left', halo=True)
    D.poly(OSD, 'P-RAIN', fill='#D8ECF7', edge=CYAN, lw=0.2, ls='--', z=5)
    D.text(np.array(OSD.centroid.coords[0]) + np.array([0, -0.2]), 'OSD TANK\n(UNDERGROUND)', 'P-RAIN', size=1.3, color=CYAN, halo=True)
    D.line(SERVICE_LINES['outfall'], 'P-RAIN', lw=0.35, color=CYAN, z=5)
    D.text(along(S_ROAD, s_at_x(S_ROAD, 50.0), -2.6), 'OUTFALL TO ROADSIDE DRAIN', 'P-RAIN', size=1.4, color=CYAN, halo=True)
    # sewer
    for k in ('east', 'north', 'west'):
        pts = SEWER[k]; D.line(pts, 'P-SANI', lw=0.35, color=BROWN, z=5)
        for q in pts[:-1]: D.poly(Point(q).buffer(0.45, cap_style=3), 'P-SANI', fill='white', edge=BROWN, lw=0.18, z=6)
    D.poly(Point(SEWER['mh']).buffer(0.7, cap_style=3), 'P-SANI', fill=BROWN, edge=None, z=6)
    D.text(SEWER['mh'] + np.array([1.2, 0.8]), 'MH · CONNECT TO IWK\nPUBLIC SEWER', 'P-SANI', size=1.4, color=BROWN, ha='left', halo=True)
    D.poly(Point(P(SEWER_R, 350)).buffer(0.7, cap_style=3), 'P-SANI', fill='#E8D7C3', edge=BROWN, lw=0.2, z=6)
    D.text(P(SEWER_R + 2.2, 350), 'GREASE TRAP\n(CAFE KITCHEN)', 'P-SANI', size=1.4, color=BROWN, ha='left', halo=True)
    # water + power + gas-free kitchen
    D.circle(WATER_IN, 0.45, 'P-CWAT', fill=BLUE, edge=None, z=8)
    D.text(WATER_IN + np.array([1.0, 0]), 'SPAN WATER METER\nØ50 INCOMING', 'P-CWAT', size=1.4, color=BLUE, ha='left', halo=True)
    ub_c = np.array(UB.centroid.coords[0])
    D.line([WATER_IN, along(E_ROAD, 63.0, 8.0)], 'P-CWAT', lw=0.3, color=BLUE, z=5)
    D.line(SERVICE_LINES['water'], 'P-CWAT', lw=0.3, color=BLUE, z=5)
    D.text(P(WATER_R + 1.0, 25), 'Ø50 RISING MAIN TO TANK\nON CORE 2', 'P-CWAT', size=1.4, color=BLUE, ha='left', halo=True)
    D.line(SERVICE_LINES['hr'], 'F-EQPT', lw=0.3, color=RED, z=5, ls='--')
    D.text(P(HR_R + 1.0, 98), 'Ø80 HOSE REEL MAIN', 'F-EQPT', size=1.4, color=RED, ha='left', halo=True)
    D.line([along(E_ROAD, 65.0, 6.0), along(E_ROAD, 65.0, -0.5)], 'M-ELEC', lw=0.3, color=MAG, z=5)
    D.line(SERVICE_LINES['lv'], 'M-ELEC', lw=0.3, color=MAG, z=5, ls=':')
    D.text(P(LV_R + 1.0, 108), 'LV CABLE IN DUCT TO MDB', 'M-ELEC', size=1.4, color=MAG, halo=True)


# ------------------------------------------------------------------------------------------------ canopies + pocket gardens (plans)
LEAF = '#DDE8D3'; LEAF_E = GREEN; RIB = '#9C845A'
def canopy_plan(D, c, solid=False, color=None, region=None, lw=0.07):
    """canopy in plan: outline, edge beams, lattice ribs. region = shapely area to keep (e.g. outside the roof)"""
    col = color or RIB
    out = LS.outline(c)
    keep = out if region is None else out.intersection(region)
    if keep.is_empty: return
    D.poly(keep, 'L-CANP', fill='#F4EBD8' if solid else None, edge=col, lw=0.18, ls='-' if solid else '--', z=2.6)
    for rib in LS.ribs(c):
        ln = LineString([LS.xy(c, s_, t_) for s_, t_ in rib]).intersection(keep)
        for g in getattr(ln, 'geoms', [ln]):
            if g.geom_type == 'LineString' and g.length > 0.05: D.line(list(g.coords), 'L-CANP', lw=lw, color=col, ls='-' if solid else '--', z=2.7)
    for q in LS.column_pts(c):
        D.circle(q['base'], 0.18, 'L-CANP', fill=col, edge=None, z=2.8)
        for tp in q['tops']: D.line([q['base'], tp], 'L-CANP', lw=0.13, color=col, z=2.8)

def pockets_plan(D, inner=True, gate=True, outer=True, color=None, labels=True):
    e = color or LEAF_E
    if outer:
        for q in OUTER: D.poly(q, 'L-PLNT', fill=LEAF, edge=e, lw=0.13, z=2.2)
        for p in POCKET_TREES:
            D.circle(p, 2.0, 'L-PLNT', fill=None, edge=e, lw=0.09, z=2.3); D.circle(p, 0.15, 'L-PLNT', fill=e, edge=None, z=2.3)
        if labels and OUTER:
            big = max(OUTER, key=lambda q: q.area); p = polylabel(big, 0.1)
            D.text((p.x, p.y - 2.6), 'TAMAN ULAM', 'L-PLNT', size=1.4, color=e, weight='bold', halo=True, z=9)
    if gate:
        for g in GATE: D.poly(g['poly'], 'L-PLNT', fill=LEAF, edge=e, lw=0.13, z=2.4)
    if inner:
        for a, b in LS.INNER:
            D.poly(LS.ann_sec(*LS.POCKET_IN_R, a, b), 'L-PLNT', fill=LEAF, edge=e, lw=0.13, z=3.4)

def landscape_plan(D, site=False):
    for c in LS.CANOPIES: canopy_plan(D, c, solid=True, region=None if site else None)
    pockets_plan(D, inner=False)
