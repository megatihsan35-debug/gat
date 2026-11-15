"""Services overlays drawn on the grey base plans: fire (Bomba), plumbing + drainage, electrical + ACMV.
Each overlay(D, fl) adds symbols / routes in site metres. Positions are derived from the room model (plan3)."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import polylabel, unary_union
from cad import INK
import plan3 as M
from plan3 import C, P, d, tdir, frame, SC, CORES, S4, EXT, ROOMS, R_BR0, R_BR1, R_GF, R_L1, R_COURT, R_POOL, FFL
import plans, siteplan as ST
from siteplan import arrow, RED, BLUE, CYAN, BROWN, GREEN, MAG, ORANGE
TEAL = '#138A72'; VIOLET = '#6A4FB3'
def R(key): return [r for r in ROOMS if r['key'] == key][0]
def mid(key): return M.mid(key)
def rr(key): rs = [plans.rad(c) for c in R(key)['poly'].exterior.coords]; return min(rs), max(rs)
def label_pt(key): p = polylabel(R(key)['poly'], 0.05); return np.array([p.x, p.y])
def rooms_on(fl, pred=lambda r: True): return [r for r in ROOMS if r['fl'] == fl and r['kind'] in ('room', 'wet', 'shop') and pred(r)]

# --------------------------------------------------------------------------------------------- symbols
def sym_box(D, p, txt, layer, color, w=0.9, h=0.55, fill='white', size=1.2):
    p = np.array(p); D.poly(Polygon([p + (-w / 2, -h / 2), p + (w / 2, -h / 2), p + (w / 2, h / 2), p + (-w / 2, h / 2)]), layer, fill=fill, edge=color, lw=0.2, z=9)
    D.text(p, txt, layer, size=size, color=color if fill == 'white' else 'white', weight='bold', z=10)
def sym_circ(D, p, txt, layer, color, r=0.3, fill='white', size=1.1):
    D.circle(p, r, layer, fill=fill, edge=color, lw=0.18, z=9); D.text(p, txt, layer, size=size, color=color if fill == 'white' else 'white', weight='bold', z=10)
def sym_tri(D, p, txt, layer, color, s=0.42):
    p = np.array(p); D.poly(Polygon([p + (0, s), p + (-s * 0.9, -s * 0.6), p + (s * 0.9, -s * 0.6)]), layer, fill=color, edge=None, z=9)
    D.text(p + (0, -s - 0.35), txt, layer, size=1.0, color=color, weight='bold', z=10)
def core_door(c, fl=None):
    """centre of the stair door (court side of the floor landing)"""
    return c['f'](c['us0'] + M.LAND0 / 2, c['vi'] - 0.1)
def lobby(c, fl=None, du=0.0, dv=0.0):
    """a point just outside the stair door, on the walk / arcade"""
    return c['f'](c['us0'] + M.LAND0 / 2 + du, c['vi'] - 1.0 + dv)
def cores_on(fl): return [c for c in CORES.values() if c['stair'] is not None and (fl != 'L2' or c['to_l2'])]
def lifts_on(fl): return [c for c in CORES.values() if c['lift'] and (fl != 'L2' or c['to_l2'])]
def ccw_n(c): return -d(c['bc'])                                     # out of a core, towards the court

# --------------------------------------------------------------------------------------------- FIRE
def hr_points(fl):
    """hose reels (30 m hose + 6 m throw): beside every stair door and the lift-2 lobby; on the first floor also at the
    four outer-ring landings / external stairs, so every point of the outer ring is in reach without crossing the bridge"""
    out = []
    for c in cores_on(fl): out.append(c['f'](c['ua0'] + 0.6, c['vi'] - 0.45))
    c3 = CORES['C3']; out.append(c3['f'](c3['lu1'] + 0.9, c3['vi'] - 0.45))
    if fl == 'L1':
        for b in (52.0, 336.0): out.append(P(M.R_OR0 + 0.45, b))                     # outer ring E (cleaners) + N (admin)
        for s_ in EXT.values(): out.append(s_['top'] + (C - s_['top']) / np.linalg.norm(C - s_['top']) * 1.2)
    return out
def n_hose_reels(): return sum(len(hr_points(f)) for f in ('GF', 'L1', 'L2'))
def hr_storage(n): return min(9100.0, 2275.0 + 1137.5 * (n - 1))

def escape_route(fl, pt):
    pts, dist, k = M.travel_path(fl, pt)
    clean = [pts[0]]
    for q in pts[1:]:
        if np.linalg.norm(np.array(q) - np.array(clean[-1])) > 0.05: clean.append(np.array(q))
    return clean, dist, k

def fire_overlay(D, fl):
    # fire-rated enclosures: stair cores, lift shafts, MDB, LAN (60 min)
    rated = [c['fp'].difference(c['holes']) for c in CORES.values() if fl != 'L2' or c['to_l2']]
    for r in rooms_on(fl, lambda r: r['occ'] == 'plant'):
        rated.append(r['poly'].exterior.buffer(0.1))
    D.poly(unary_union(rated), 'F-RATE', fill='#F3B3B0', edge=RED, lw=0.13, z=6)
    # escape routes (green) on the upper floors from points round the rings, with the route length to the nearest exit
    if fl != 'GF':
        pl = M.PLATE[fl]
        encl = unary_union([r['poly'].buffer(-0.3) for r in rooms_on(fl)] + [c['fp'].buffer(-0.05) for c in CORES.values()])
        samples = [(b, rr_) for b in np.arange(7.5, 360, 15) for rr_ in ((12.4, 18.5, 23.8) if fl == 'L1' else (12.4,))]
        for b, rr_ in samples:
            pt = P(rr_, b)
            if not pl.buffer(-0.3).contains(Point(pt)) or encl.contains(Point(pt)): continue
            pts, dist, k = escape_route(fl, pt)
            if len(pts) < 2: continue
            D.line(pts[:-1], 'F-ESCP', lw=0.3, color=GREEN, z=8); arrow(D, pts[-2], pts[-1], 'F-ESCP', GREEN, lw=0.3, head=0.55)
            D.text(pt + (np.array(pt) - C) / np.linalg.norm(np.array(pt) - C) * 0.9, f'{dist:.0f} M', 'F-ESCP', size=1.4, color=GREEN, weight='bold', halo=True)
    else:
        for s in SC.SPINES:
            arrow(D, P(R_COURT - 1.5, s['b']), P(R_L1 + 3.0, s['b']), 'F-ESCP', GREEN, lw=0.45, head=0.9)
            D.text(P(R_L1 + 4.6, s['b']), 'FINAL EXIT\nTO OPEN AIR', 'F-ESCP', size=1.6, color=GREEN, weight='bold', halo=True)
        for c in cores_on(fl):
            q = core_door(c); arrow(D, q, q + ccw_n(c) * 2.4, 'F-ESCP', GREEN, lw=0.35, head=0.6)
        for r in rooms_on('GF'):
            bm, b0, b1 = mid(r['key']); r0, r1 = rr(r['key'])
            if r['kind'] == 'shop' or r['key'] in ('G01', 'G02', 'G04', 'G22', 'G21'):
                arrow(D, P((r0 + r1) / 2, bm), P(R_BR1 - 1.2, bm), 'F-ESCP', GREEN, lw=0.2, head=0.45)
            elif r['key'] in ('G06', 'G07', 'G05', 'G08', 'G30', 'G20', 'G10', 'G11', 'G31', 'G23'):
                arrow(D, P((r0 + r1) / 2, bm), P(R_L1 + 0.5, bm), 'F-ESCP', GREEN, lw=0.2, head=0.45)
    # exit signs at stair doors + external stairs
    for c in cores_on(fl):
        sym_box(D, core_door(c) + ccw_n(c) * 0.7, 'EXIT', 'F-EQPT', '#1E8B3A', w=1.1, h=0.5, fill='#1E8B3A', size=1.1)
    if fl == 'L1':
        for s_ in EXT.values(): sym_box(D, s_['top'] + (C - s_['top']) / np.linalg.norm(C - s_['top']) * 0.6, 'EXIT', 'F-EQPT', '#1E8B3A', w=1.1, h=0.5, fill='#1E8B3A', size=1.1)
    # hose reels + extinguishers
    for p in hr_points(fl):
        sym_box(D, p, 'HR', 'F-EQPT', RED, w=0.8, h=0.8, fill=RED, size=1.3); sym_tri(D, p + (np.array(p) - C) / np.linalg.norm(np.array(p) - C) * -1.1, 'DP 9KG', 'F-EQPT', RED)
        D.circle(p, 36.0, 'F-EQPT', edge=RED, lw=0.07, ls=':', z=3)
    # detection: smoke detector per 50 m2 in every enclosed room, heat detector in the kitchen, MCP at exits, bells
    for r in rooms_on(fl):
        n = max(1, math.ceil(r['poly'].area / 50.0)); bm, b0, b1 = mid(r['key']); r0, r1 = rr(r['key'])
        for i in range(n):
            q = P(r0 + (r1 - r0) * 0.5, b0 + (b1 - b0) * (i + 0.5) / n + (b1 - b0) * 0.06)
            if not r['poly'].contains(Point(q)): q = np.array(polylabel(r['poly'], 0.05).coords[0]) + (0.4, 0.4)
            sym_circ(D, q, 'H' if r['occ'] == 'kitchen' else 'S', 'F-DETN', RED, r=0.28)
        if r['occ'] == 'plant': sym_tri(D, label_pt(r['key']) + (0.9, -0.6), 'CO2 5KG', 'F-EQPT', RED)
        if r['occ'] == 'kitchen':
            sym_tri(D, P(r1 - 1.2, bm - (b1 - b0) * 0.25), 'WET CHEM\n+ BLANKET', 'F-EQPT', RED)
            D.text(P(r0 + 1.5, bm - 1.6), 'HOOD WITH WET-CHEMICAL\nSUPPRESSION', 'F-EQPT', size=1.2, color=RED, halo=True)
    for c in cores_on(fl):
        q = core_door(c) + c['t'] * 1.6 + ccw_n(c) * 0.4
        sym_box(D, q, 'MCP', 'F-DETN', RED, w=0.9, h=0.5, size=1.0)
        sym_circ(D, q + c['t'] * 1.0, 'AB', 'F-DETN', RED, r=0.32, size=1.0)
    if fl == 'GF':
        g = label_pt('G20'); sym_box(D, g + (0.0, -1.2), 'FCP', 'F-DETN', RED, w=1.0, h=0.6, fill=RED, size=1.2)
        D.text(g + (0.0, -2.2), 'MAIN FIRE ALARM\nPANEL (MANNED)', 'F-DETN', size=1.2, color=RED, halo=True)
    D.text(P(4.5, 135), 'COURT, DECKS AND RING BRIDGE ARE OPEN-SIDED:\nSMOKE RISES THROUGH THE TWO GAPS AND LEAVES\nBY THE CLERESTORIES AND THE OCULUS', 'F-ESCP', size=1.5, color=GREEN, halo=True)

FIRE_LEGEND = [('line', dict(lw=0.45, color=GREEN), 'ESCAPE ROUTE + TRAVEL DISTANCE (M)'), ('fill', dict(fill='#F3B3B0', edge=RED), '60 MIN FIRE-RESISTING ENCLOSURE'),
               ('text', dict(t='HR', color=RED), 'HOSE REEL Ø25 x 30 M (MS 1489)'), ('text', dict(t='DP', color=RED), 'EXTINGUISHER 9 KG ABC DRY POWDER'),
               ('text', dict(t='CO2', color=RED), 'EXTINGUISHER CO2 5 KG (ELECTRICAL)'), ('text', dict(t='S', color=RED), 'SMOKE DETECTOR (ADDRESSABLE)'),
               ('text', dict(t='H', color=RED), 'HEAT DETECTOR (KITCHEN)'), ('text', dict(t='MCP', color=RED, size=1.4), 'MANUAL CALL POINT 1.4 M AFF'),
               ('text', dict(t='AB', color=RED), 'ALARM BELL / SOUNDER-STROBE'), ('text', dict(t='EXIT', color='#1E8B3A', size=1.4), 'EXIT SIGN (MAINTAINED, 3 H BATTERY)'),
               ('text', dict(t='FCP', color=RED, size=1.4), 'FIRE CONTROL PANEL'), ('line', dict(lw=0.15, color=RED, ls=':'), 'HOSE REEL REACH 36 M (30 + 6)')]

# --------------------------------------------------------------------------------------------- PLUMBING + DRAINAGE
def stacks():
    """soil + vent stacks (Ø100): (point, label, floors it collects from). Every stack runs straight down to a ground-floor room
    or column casing and vents above the funnel roof; wudhu / janitor wastes on L2 that sit over a gate run 1:60 in the floor
    zone to the nearest stack."""
    out = []
    for g, l, lab in (('G01', 'L04', 'SVP 1'), ('G02', 'L05', 'SVP 2')):
        a0 = max(mid(g)[1], mid(l)[1]); a1 = min(mid(g)[2], mid(l)[2])
        out.append((P(14.9, a0 + 0.8), lab, ('GF', 'L1')))
    out.append((P(12.8, mid('L06')[1] + 1.4), 'SVP E', ('GF', 'L1')))                  # L1 janitor -> casing on the shop A2-1 side wall
    out.append((P(12.8, 302.6), 'SVP W1', ('GF', 'L1', 'L2')))                         # male wudhu + L2 janitor (via 1:60 branch)
    out.append((P(12.8, 258.2), 'SVP W2', ('GF', 'L1', 'L2')))                         # female wudhu (via 1:60 branch)
    a0, a1, ae = M.EAST['ADMIN']; b_ = mid('L23')[1] + 0.7
    out.append((P(22.3, b_), 'SVP N', ('GF', 'L1')))                                    # admin pantry + staff toilet, column casing at GF
    return out
def ic_ring(): return [(P(31.0, b), f'IC') for b in (50, 75, 105, 135, 160, 205, 235, 268, 300, 350, 20)]

def plumbing_overlay(D, fl):
    # cold water ring mains: inner ring R12.9 (arcade soffit / inner ring ceilings), outer ring R22.3 (GF ceilings, outer ring L1)
    ring_r = 12.9
    D.circle(C, ring_r, 'P-CWAT', edge=BLUE, lw=0.3, z=7)
    D.text(P(ring_r + 0.4, 160), 'Ø50 CW RING MAIN IN SOFFIT' if fl != 'L2' else 'Ø32 CW (BOOSTED) TO WUDHU', 'P-CWAT', size=1.4, color=BLUE, ha='left', halo=True)
    if fl in ('GF', 'L1'):
        D.circle(C, 22.3, 'P-CWAT', edge=BLUE, lw=0.22, ls='--', z=7)
        D.text(P(22.7, 196), 'Ø40 CW OUTER RING' + (' (FED UP FROM GF AT THE GATES)' if fl == 'L1' else ''), 'P-CWAT', size=1.3, color=BLUE, ha='left', halo=True)
    c2 = CORES['C2']; riser = np.array(c2['duct'].centroid.coords[0])
    sym_circ(D, riser, 'R', 'P-CWAT', BLUE, r=0.3, fill=BLUE, size=1.0)
    D.text(riser + d(c2['bc']) * -1.6, 'CW DOWN-FEED FROM TANK\nROOM ON CORE 2 (FL +12.200)', 'P-CWAT', size=1.3, color=BLUE, halo=True)
    D.line([riser, P(ring_r, M.brg(riser))], 'P-CWAT', lw=0.3, color=BLUE, z=7)
    wet = rooms_on(fl, lambda r: r['kind'] == 'wet' or r['occ'] in ('kitchen', 'shop', 'wc') or r['key'] in ('L22', 'G33', 'G21'))
    for r in wet:
        bm, b0, b1 = mid(r['key']); r0, r1 = rr(r['key'])
        rm = ring_r if r0 < 18.0 else 22.3
        a = P(rm, bm); e = P(min(r1 - 0.6, max(r0 + 0.6, (r0 + r1) / 2)), bm)
        D.line([a, e], 'P-CWAT', lw=0.2, color=BLUE, z=7); D.circle(e, 0.12, 'P-CWAT', fill=BLUE, edge=None, z=8)
    # soil + waste: floor traps, stacks, below-slab drains to the inspection chambers
    for p, lab, fls in stacks():
        if fl not in fls: continue
        sym_circ(D, p, '', 'P-SANI', BROWN, r=0.22, fill=BROWN)
        D.text(p + (np.array(p) - C) / np.linalg.norm(np.array(p) - C) * 1.0, f'{lab} Ø100', 'P-SANI', size=1.3, color=BROWN, weight='bold', halo=True)
        if fl == 'GF':
            b = math.degrees(math.atan2(*(np.array(p) - C))) % 360
            D.line([p, P(31.0, b)], 'P-SANI', lw=0.3, color=BROWN, ls='--', z=7)
    for r in wet:
        if r['occ'] == 'store' and 'JANITOR' not in r['name']: continue
        bm, b0, b1 = mid(r['key']); r0, r1 = rr(r['key'])
        ft = P((r0 + r1) / 2, bm - (b1 - b0) * 0.2)
        sym_circ(D, ft, 'FT', 'P-SANI', BROWN, r=0.26, size=0.9)
        if fl == 'GF' and r['key'] not in ('G01', 'G02'):
            out = P(31.0, bm); D.line([ft, out], 'P-SANI', lw=0.22, color=BROWN, ls='--', z=7)
    if fl == 'GF':
        for p, lab in ic_ring():
            D.poly(Point(p).buffer(0.45, cap_style=3), 'P-SANI', fill='white', edge=BROWN, lw=0.2, z=8); D.text(p + (0.0, -0.95), lab, 'P-SANI', size=1.1, color=BROWN)
        D.poly(Point(P(31.0, 350)).buffer(0.75, cap_style=3), 'P-SANI', fill='#E8D7C3', edge=BROWN, lw=0.25, z=8)
        D.text(P(33.0, 350), 'GREASE TRAP', 'P-SANI', size=1.3, color=BROWN, ha='left', halo=True)
        for p, kind in ST.RWDP:
            D.circle(p, 0.2, 'P-RAIN', fill='white', edge=CYAN, lw=0.25, z=8)
        D.circle(C, ST.PERIM_DRAIN_R, 'P-RAIN', edge=CYAN, lw=0.4, z=6)
        D.text(P(ST.PERIM_DRAIN_R + 0.6, 120), '300 U-DRAIN + GRATING', 'P-RAIN', size=1.3, color=CYAN, ha='left', halo=True)
        D.text(C + (0, 3.1), 'POOL OVERFLOW 2 x Ø150\nTO PERIMETER DRAIN', 'P-RAIN', size=1.3, color=CYAN, halo=True)
        for b in (100, 280): D.line([P(R_POOL, b), P(ST.PERIM_DRAIN_R, b)], 'P-RAIN', lw=0.25, color=CYAN, ls='--', z=6)
        g = label_pt('G30'); D.text(g + (0, -2.5), 'KITCHEN SINK VIA\nGREASE TRAP', 'P-SANI', size=1.2, color=BROWN, halo=True)
    if fl == 'L2':
        for k, tgt in (('M11', 302.6), ('M15', 302.6), ('M13', 258.2)):
            bm, b0, b1 = mid(k); a = P(13.6, bm); q = P(12.8, tgt)
            D.line([a, P(13.6, tgt), q], 'P-SANI', lw=0.3, color=BROWN, z=7)
        D.text(P(14.2, 322.0), 'Ø100 1:60 IN FLOOR ZONE\nTO SVP W1 / W2', 'P-SANI', size=1.2, color=BROWN, halo=True)
        sym_box(D, riser + d(c2['bc']) * -2.6, 'BP', 'P-EQPT', BLUE, w=0.8, h=0.6, size=1.1)
        D.text(P(14.0, 300.0), 'WUDHU: 6 TAPS EACH SIDE,\nSTOOLS, FOOT-WASH TROUGH', 'P-CWAT', size=1.2, color=BLUE, halo=True)

PLUMB_LEGEND = [('line', dict(lw=0.4, color=BLUE), 'COLD WATER (PPR PN16)'), ('line', dict(lw=0.4, color=BROWN, ls='--'), 'SOIL / WASTE BELOW SLAB (uPVC)'),
                ('circle', dict(fill=BROWN, edge=BROWN, r=1.0), 'SOIL + VENT STACK Ø100'), ('text', dict(t='FT', color=BROWN), 'FLOOR TRAP Ø100'),
                ('text', dict(t='IC', color=BROWN), 'INSPECTION CHAMBER 600 x 600'), ('circle', dict(edge=CYAN, r=1.0), 'RAINWATER DOWNPIPE Ø150'),
                ('line', dict(lw=0.4, color=CYAN), 'PERIMETER U-DRAIN 300'), ('text', dict(t='R', color=BLUE), 'CW RISER / DOWN-FEED'), ('text', dict(t='BP', color=BLUE), 'BOOSTER PUMP SET')]

# --------------------------------------------------------------------------------------------- ELECTRICAL + ACMV
def mne_overlay(D, fl):
    tray_r = 13.4
    D.circle(C, tray_r, 'M-ELEC', edge=MAG, lw=0.3, ls='--', z=7)
    D.text(P(tray_r + 0.4, 168), 'CABLE TRAY 300 IN SOFFIT', 'M-ELEC', size=1.3, color=MAG, ha='left', halo=True)
    D.circle(C, 14.0, 'M-ACMV', edge=VIOLET, lw=0.3, z=7)
    D.text(P(14.4, 176), 'VRF REFRIGERANT PIPES', 'M-ACMV', size=1.3, color=VIOLET, ha='left', halo=True)
    if fl in ('GF', 'L1'):
        D.circle(C, 22.8, 'M-ELEC', edge=MAG, lw=0.22, ls='--', z=7); D.circle(C, 23.3, 'M-ACMV', edge=VIOLET, lw=0.22, z=7)
        D.text(P(23.6, 208), 'OUTER TRAY + VRF RING' + (' (CROSS AT THE GATES IN THE WALKWAY SOFFITS)' if fl == 'L1' else ''), 'M-ELEC', size=1.2, color=MAG, ha='left', halo=True)
    db = {'GF': [('G08', 'MSB / MDB'), ('G09', 'SSB-GF')], 'L1': [('L07', 'SSB-L1'), ('L27', 'DB-ADMIN')], 'L2': [('M16', 'SSB-L2')]}[fl]
    for k, t in db:
        p = label_pt(k) + (0, -1.0); sym_box(D, p, t, 'M-EQPT', MAG, w=1.6, h=0.55, fill=MAG, size=1.0)
    for r in rooms_on(fl, lambda r: r['kind'] == 'shop'):
        bm, b0, b1 = mid(r['key']); r0, r1 = rr(r['key']); sym_box(D, P(r1 - 0.7, bm + (b1 - b0) * 0.3), 'DB', 'M-EQPT', MAG, w=0.7, h=0.45, size=0.9)
    if fl == 'GF':
        g = label_pt('G30'); sym_box(D, g + (1.0, -1.0), 'DB', 'M-EQPT', MAG, w=0.7, h=0.45, size=0.9)
    # VRF indoor cassettes: one per started 25 m2 in every air-conditioned room
    for r in rooms_on(fl, lambda r: r['ac']):
        n = max(1, math.ceil(r['poly'].area / 25.0)); bm, b0, b1 = mid(r['key']); r0, r1 = rr(r['key'])
        for i in range(n):
            q = P(r0 + (r1 - r0) * (i + 0.5) / n, bm - (b1 - b0) * 0.18)
            D.poly(Point(q).buffer(0.42, cap_style=3), 'M-ACMV', fill='white', edge=VIOLET, lw=0.2, z=9)
            D.line([q + (-0.42, -0.42), q + (0.42, 0.42)], 'M-ACMV', lw=0.1, color=VIOLET, z=10); D.line([q + (-0.42, 0.42), q + (0.42, -0.42)], 'M-ACMV', lw=0.1, color=VIOLET, z=10)
        D.line([P(14.0 if r0 < 18.0 else 23.3, bm), P(r0 + (r1 - r0) * 0.5 / n, bm - (b1 - b0) * 0.18)], 'M-ACMV', lw=0.15, color=VIOLET, z=8)
    # exhaust fans in toilets / wudhu / kitchen hood
    for r in rooms_on(fl, lambda r: r['occ'] in ('wc', 'kitchen') or 'JANITOR' in r['name']):
        bm, b0, b1 = mid(r['key']); r0, r1 = rr(r['key'])
        sym_circ(D, P(r0 + (r1 - r0) * 0.6, bm + (b1 - b0) * 0.25), 'EF', 'M-ACMV', VIOLET, r=0.32, size=0.95)
    if fl == 'GF':
        bk0, bk1, bd1 = M.EAST['CAFE']; q = P(22.2, bk0 + 4.0)
        D.poly(Point(q).buffer(0.45, cap_style=3), 'M-ACMV', fill='#E7E1F5', edge=VIOLET, lw=0.25, z=9)
        D.text(P(25.0, bk0 + 4.0), 'KITCHEN EXHAUST: ESP +\nCARBON FILTER, DISCHARGE\nAT COLONNADE SOFFIT', 'M-ACMV', size=1.15, color=VIOLET, halo=True)
        for b in (45, 135, 225, 315):
            D.circle(P(5.6, b), 2.0, 'M-ACMV', edge=VIOLET, lw=0.15, ls='--', z=8); D.text(P(5.6, b), 'HVLS\nØ4.0', 'M-ACMV', size=1.0, color=VIOLET, z=9)
        sym_box(D, P(R_COURT + 0.8, 250), 'LP', 'M-EQPT', MAG, w=0.7, h=0.45, size=0.9)
    else:
        for o in M.decks(fl):
            if o.area < 12: continue
            for b in np.arange(0, 360, 12):
                for rrr in (13.3, 23.8):
                    q = P(rrr, b)
                    if o.buffer(-1.0).contains(Point(q)):
                        D.circle(q, 0.6, 'M-ACMV', edge=VIOLET, lw=0.1, z=8); D.line([q + (-0.6, 0), q + (0.6, 0)], 'M-ACMV', lw=0.08, color=VIOLET, z=8)
    # lifts, lightning protection
    for c in lifts_on(fl):
        D.text(c['f']((c['lu0'] + c['lu1']) / 2, c['lv0'] + 1.1), 'MRL LIFT\n13P 1000KG', 'M-EQPT', size=1.0, color=MAG, halo=True, z=10)
    if fl == 'GF':
        for s in SC.SPINES:
            for sg in (-1, 1):
                b = s['b'] + sg * 14.0; q = P(R_GF, b)
                sym_circ(D, q, 'DC', 'M-ELEC', MAG, r=0.3, size=0.9)
        D.text(P(R_GF + 1.5, s['b'] + 14.0), 'DOWN CONDUCTOR IN\nCOLUMN, TEST JOINT', 'M-ELEC', size=1.2, color=MAG, ha='left', halo=True)
        D.circle(C, 31.6, 'M-ELEC', edge=MAG, lw=0.15, ls=':', z=5)
        D.text(P(31.9, 210), 'RING EARTH ELECTRODE (25 MM² Cu)', 'M-ELEC', size=1.2, color=MAG, ha='left', halo=True)

MNE_LEGEND = [('text', dict(t='MSB', color=MAG, size=1.4), 'MAIN SWITCHBOARD / MAIN DB'), ('text', dict(t='SSB', color=MAG, size=1.4), 'SUB-SWITCHBOARD (PER FLOOR)'),
              ('text', dict(t='DB', color=MAG), 'TENANT DB + kWh SUB-METER'), ('line', dict(lw=0.4, color=MAG, ls='--'), 'CABLE TRAY RING (SOFFIT)'),
              ('fill', dict(fill='white', edge=VIOLET), 'VRF 4-WAY CASSETTE (≤ 25 M² EACH)'), ('line', dict(lw=0.4, color=VIOLET), 'VRF REFRIGERANT PIPE RING'),
              ('text', dict(t='EF', color=VIOLET), 'EXHAUST FAN 10 AC/H (TOILET, WUDHU)'), ('circle', dict(edge=VIOLET, r=1.2), 'CEILING FAN 1.5 M (OPEN DECKS)'),
              ('text', dict(t='DC', color=MAG), 'LIGHTNING DOWN CONDUCTOR (MS IEC 62305)'), ('text', dict(t='LP', color=MAG), 'LIGHTING PANEL (COURT + FACADE)')]
