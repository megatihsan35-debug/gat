"""Drawings for the Crit 2 A2 boards (all model metres unless paper=True).
- board versions of the plans (room numbers instead of crowded labels, context from the site plan)
- 1:50 foundation-to-roof section through the outer ring, 1:50 mid-span gate truss (elevation + section)
- 1:10 joints (truss node, fin bracket), keynote conversion of the existing details
- diagrams: peninsula, design development, site synthesis, structure axonometric, environment"""
import math, json, os, copy
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, shape
from shapely.ops import unary_union
from cad import Drawing, INK
import plan3 as M, plans, sections as SE, siteplan as ST, rings as RG, scheme as SC, sheets2 as S2
from plan3 import C, P, FFL, ROOMS

HERE = os.path.dirname(os.path.abspath(__file__))
ACC = '#A8773A'; GREY = '#8A9097'; LG = '#C9CDD2'; CUT = '#BFC4CA'; GLASS = '#BFD9E6'; SKY = '#E0A100'; AIR = '#3E7D3A'; WATER = '#1AA0C8'
UP = lambda s: s.upper().replace('Ø', 'Ø')

# --------------------------------------------------------------------------------------------- helpers
def upper(D):
    for k, l, a in D.items:
        if k == 'text': a['s'] = a['s'].upper()
    return D

def bbox(D, layers=None):
    xs, ys = [], []
    for k, l, a in D.items:
        if layers and l not in layers: continue
        if k == 'line': pts = a['pts']
        elif k == 'poly': pts = [p for r in a['rings'] for p in r]
        elif k in ('circle', 'arc'): c, r = a['c'], a['r']; pts = [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)]
        elif k == 'text': pts = [a['p']]
        else: continue
        for x, y in pts: xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)

def tag(D, p, n, scale, r_mm=2.3, fill=INK, color='white', size=2.3):
    """keynote bubble: circle radius r_mm on paper at the drawing scale"""
    r = r_mm * scale / 1000.0
    D.circle(p, r, 'A-ANNO', fill=fill, edge=None, z=9)
    D.text(p, str(n), 'A-ANNO', size=size, color=color, weight='bold', z=10)

def keynote_leads(D, scale, start=1, lead_size=1.9):
    """turn every leader text written by sheets2.lead() (A-ANNO, size 1.9) into a numbered bubble; returns the texts"""
    notes = []; n = start; items = []
    for k, l, a in D.items:
        if k == 'text' and l == 'A-ANNO' and abs(a['size'] - lead_size) < 1e-6:
            x, y = a['p']; x += -0.03 if a['ha'] == 'left' else 0.03
            notes.append(' '.join(a['s'].upper().split()))
            r = 2.3 * scale / 1000.0
            items.append(('circle', 'A-ANNO', dict(c=(x, y), r=r, fill=INK, edge=None, lw=0.1, z=9, ls='-')))
            items.append(('text', 'A-ANNO', dict(p=(x, y), s=str(n), size=2.3, ha='center', va='center', rot=0.0, color='white', weight='bold', z=10, font=None, halo=False, box=None)))
            n += 1
        else:
            items.append((k, l, a))
    D.items = items
    return notes

def leader(D, p, q, n, scale):
    D.line([p, q], 'A-ANNO', lw=0.13); D.circle(p, 0.6 * scale / 1000.0, 'A-ANNO', fill=INK, edge=None, z=8)
    tag(D, q, n, scale)

# --------------------------------------------------------------------------------------------- plans for the boards
KEEP_SIZES = {'A-GRID', 'A-STRS'}
def plan_board(fl, context=True):
    """plan at 1:200 for the A2 boards: drop fixture/door/area text, tag every room with its number (legend on the board)"""
    D = plans.plan_drawing(fl, 'arch')
    items = []
    for k, l, a in D.items:
        if k == 'text':
            s = a['s']
            if l in KEEP_SIZES: a = dict(a, size=a['size'] * 1.2)
            elif l == 'A-ANNO' and a['size'] >= 2.0: a = dict(a, size=2.8, weight='bold')                 # section marks
            elif l == 'A-ANNO' and s.startswith(('CORE', 'LIFT')) and a['size'] >= 1.6: a = dict(a, size=2.0, weight='bold')
            else: continue
            a['s'] = a['s'].upper()
        elif k == 'line' and l == 'A-DIMS': continue
        items.append((k, l, a))
    D.items = items
    legend = []
    for r in sorted([r for r in ROOMS if r['fl'] == fl and r['kind'] in ('room', 'wet', 'shop')], key=lambda r: r['key']):
        p = r['poly'].representative_point()
        net = r['poly'].buffer(-0.075, join_style=2).area
        D.text((p.x, p.y), r['key'], 'A-AREA', size=2.1 if len(r['key']) <= 3 else 1.9, weight='bold', box='white', z=9)
        legend.append((r['key'], r['name'].upper(), f'{net:.0f}'))
    # big labels for the shared spaces
    big = {'GF': [((0.0, 1.5), 'TITIK POOL', 0), ((0, -6.0), 'TALAM COURT', 0)],
           'L1': [((0, 4.5), 'VOID OVER\nTALAM COURT', 0)], 'L2': [((0, 4.5), 'VOID OVER THE COURT', 0)]}[fl]
    for (dx, dy), s, _ in big:
        D.text(C + np.array([dx, dy]), s, 'A-ANNO', size=2.4, weight='bold', color='#5A6168', halo=True, z=9)
    if fl == 'GF':
        for s in SC.SPINES:
            q = P(31.5 if s['k'] != 'SELATAN' else 33.0, s['b'])
            D.text(q, f"{s['k']} GATE", 'A-ANNO', size=2.6, weight='bold', color=ACC, halo=True, z=9)
    if fl == 'L1':
        D.text(P(18.5, 120), 'RING BRIDGE\n+5.400', 'A-ANNO', size=2.0, weight='bold', color='#5A6168', halo=True, z=9)
        D.text(P(18.5, 300), 'RING BRIDGE', 'A-ANNO', size=2.0, weight='bold', color='#5A6168', halo=True, z=9)
    if context and fl == 'GF':
        site = ST.site_drawing(services=False)
        ctx = []
        for k, l, a in site.items:
            if k == 'text': continue
            pts = a['pts'] if k == 'line' else ([p for r in a['rings'] for p in r] if k == 'poly' else [a['c']])
            cx, cy = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
            if math.hypot(cx - C[0], cy - C[1]) < 29.5: continue
            a = dict(a); a['z'] = min(a.get('z', 1), 0)
            ctx.append((k, l, a))
        for k, l, a in site.items:
            if k == 'text' and l in ('A-SITE', 'A-ANNO') and a['size'] >= 1.6 and math.hypot(a['p'][0] - C[0], a['p'][1] - C[1]) > 30:
                ctx.append((k, l, dict(a, s=a['s'].upper(), size=2.2)))
        D.items = ctx + D.items
    return D, legend

def grow(D, k, below=2.0, cap=2.6):
    for kk, l, a in D.items:
        if kk == 'text' and a['size'] < below: a['size'] = min(a['size'] * k, cap)
    return D

def section_board():
    (A, XA), (B, XB) = SE.section_set()
    for D in (A, B):
        D.items = [(k, l, a) for k, l, a in D.items if not (k == 'text' and a['size'] < 1.15)]
        upper(D); grow(D, 1.45, 2.0, 2.4)
    return (A, XA), (B, XB)

def elevation_board(b, label):
    E = SE.elevation(b, label)
    E.items = [(k, l, a) for k, l, a in E.items if not (k == 'text' and a['size'] < 1.15)]
    return grow(upper(E), 1.45, 2.0, 2.4)

def roof_board():
    D = ST.roof_drawing()
    D.items = [(k, l, a) for k, l, a in D.items if not (k == 'text' and a['size'] < 1.3)]
    return grow(upper(D), 1.6, 2.0, 2.3)

def site_board():
    return grow(upper(ST.site_drawing(services=False)), 1.3, 1.8, 2.2)

# --------------------------------------------------------------------------------------------- 1:50 foundation to roof (outer ring)
F2R_NOTES = [
    'ROOF: 0.9 MM ALUMINIUM STANDING SEAM, PVDF SILVER-WHITE, ON BREATHER MEMBRANE, 100 MM ROCKWOOL (48 KG/M³) AND 0.7 MM PERFORATED LINER',
    'Z-PURLINS 200 @ 1200 ON TAPERED STEEL RAFTERS S355 (450 → 250 DEEP) AT EVERY RADIAL GRID',
    'CONCEALED BOX GUTTER 1.6 MM SS316, 400 WIDE, SUMP + Ø150 RWDP INSIDE THE FIN CASING',
    'ROOF EDGE: 3 MM ALUMINIUM FASCIA, PVDF DARK BRONZE, 1800 OVERHANG FOR SHADE AND RAIN',
    'VERTICAL FIN 450 x 60 EXTRUDED ALUMINIUM, 750 C/C, ANGLE 18°-90° SET PER BAY, PIN BRACKETS TOP + BOTTOM',
    'CURTAIN WALL G1: DGU 6 LOW-E + 12 + 6 HS ON 65 x 150 MULLIONS @ 1500, U ≤ 2.0, SHGC ≤ 0.35 (MS 1525)',
    'L1 SLAB: RC 250 (C35) ON RADIAL CANTILEVER BEAMS 300 x 750 OFF GRID E, EDGE BEAM 600, GRC FASCIA 20',
    'GRC SOFFIT PANELS 20 ON GALVANISED HANGERS: THE HANGING FIRST FLOOR SEEN FROM THE ARCADE',
    'COLUMN E: Ø350 RC C35, 40 COVER (2 H FIRE), CONTINUES TO THE OUTER ROOF TIER',
    'L1 FLOOR: 20 TERRAZZO TILES ON 50 SCREED; CEILING 12.5 GYPSUM ON SUSPENDED GRID +8.400',
    'GF SHOPFRONT / WALL ON GRID E: 12 TOUGHENED GLASS (G2) OR 100 GRC-FACED LIGHTWEIGHT PANEL',
    'GF FLOOR: 20 TERRAZZO, 75 SCREED, 150 RC GROUND SLAB (A252 MESH), 1000 G DPM, 150 COMPACTED HARDCORE',
    'PLINTH EDGE +0.900: 200 RC RETAINING UPSTAND, 30 BUSH-HAMMERED GRANITE CLADDING, 50 NOSING',
    'PERIMETER DRAIN 300 WIDE, PRECAST U-DRAIN WITH STAINLESS STEEL GRATING, FALLS 1:200',
    'RC GROUND BEAM 300 x 600 (RING ON GRID E) TYING THE PILE CAPS',
    'RC PILE CAP 1500 x 1500 x 900 ON 2 No. Ø450 BORED PILES; LENGTH TO THE SOIL INVESTIGATION (ALLUVIUM BESIDE SUNGAI PAHANG)',
    'GAP 1500: OPAL LAMINATED GLASS ROOFLIGHT G5 AT +5.400 ON THE GF STRUCTURE, 50 JOINT TO THE BRIDGE',
    'RING BRIDGE EDGE: 350 COMPOSITE SLAB ON STEEL BOX RING BEAM; GLASS BALUSTRADE G4 1100',
    'OUTER CLERESTORY: FIXED LOUVRED GLASS G6 (45° LAP + INSECT MESH) BETWEEN THE OUTER AND MIDDLE TIERS',
]

def detail_f2r(b=300.0):
    """1:50 radial section, foundation to roof, through the outer ring at bearing b (x = radius from C, z = level)"""
    D = Drawing('F2R'); H = CUT; sc = 50
    Pb = lambda r: P(r, b)
    ot = lambda r: RG.out_top(Pb(r)); ou = lambda r: RG.out_under(Pb(r))
    # ground, hardcore, plinth
    D.poly(box(19.3, -3.6, 30.6, 0.0), 'A-SITE', fill='#EFEBE2', edge=None, z=0)
    for x in np.arange(19.4, 30.6, 0.5): D.line([(x, -3.55), (x + 0.4, -3.15)], 'A-SITE', lw=0.05, color='#C9C2B2', z=0)
    D.line([(27.25, 0.0), (30.6, 0.0)], 'A-SITE', lw=0.35)
    D.poly(box(19.3, 0.3, 27.05, 0.75), 'S-DETL', fill='#E3DDD0', edge=None, z=1)                         # hardcore
    for x in np.arange(19.4, 27.0, 0.25): D.circle((x, 0.52), 0.06, 'S-DETL', edge='#B8AE98', lw=0.05, z=1)
    D.poly(box(19.3, 0.75, 27.05, 0.9), 'S-DETL', fill=H, edge=INK, lw=0.2, z=2)                            # GF slab
    D.poly(box(26.85, -0.6, 27.05, 0.9), 'S-DETL', fill=H, edge=INK, lw=0.2, z=2)                           # plinth upstand
    D.poly(box(27.05, -0.1, 27.09, 0.92), 'A-ELEV', fill='#D9D2C3', edge=INK, lw=0.1, z=2)                  # granite
    D.poly(box(27.5, -0.35, 27.8, 0.0), 'P-RAIN', fill='white', edge=INK, lw=0.15, z=2)                      # drain
    D.line([(27.5, -0.02), (27.8, -0.02)], 'P-RAIN', lw=0.3, color='#555')
    # foundations under grid E + the GF wall at R21.5 (pile caps, ground beam, piles with break)
    for xc in (23.0,):
        D.poly(box(xc - 0.75, -1.8, xc + 0.75, -0.9), 'S-DETL', fill=H, edge=INK, lw=0.25, z=2)
        D.poly(box(xc - 0.15, -0.9, xc + 0.15, 0.75), 'S-DETL', fill=H, edge=INK, lw=0.2, z=2)
        for px in (xc - 0.45, xc + 0.45):
            D.poly(box(px - 0.225, -3.5, px + 0.225, -1.8), 'S-DETL', fill=H, edge=INK, lw=0.2, z=2)
        D.line([(xc - 0.9, -3.0), (xc - 0.2, -3.25), (xc + 0.2, -2.95), (xc + 0.9, -3.2)], 'A-ANNO', lw=0.2)
    D.poly(box(20.0, -0.6, 26.0, 0.0), 'S-DETL', fill='none', edge=INK, lw=0.12, ls='--', z=2)               # ground beam (seen)
    D.poly(box(21.35, -0.6, 21.65, 0.75), 'S-DETL', fill=H, edge=INK, lw=0.15, z=2)                          # GF wall footing strip
    # ground floor: wall / shopfront on grid E, column E, GF room behind
    D.poly(box(22.825, 0.9, 23.175, ou(23.0)), 'S-DETL', fill=H, edge=INK, lw=0.2, z=3)                       # column E (cut on the grid line)
    D.poly(box(23.18, 0.9, 23.24, 4.2), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.1, z=3)                          # GF shopfront
    D.line([(19.3, 4.2), (22.8, 4.2)], 'A-HIDN', lw=0.12, ls='--')
    D.poly(box(21.35, 0.9, 21.65, 4.8), 'S-DETL', fill='#E8E9EB', edge=INK, lw=0.15, z=3)                    # GF wall under gap edge
    # first floor slab + cantilever beam + edge beam, soffit
    D.poly(box(21.5, 5.15, 26.5, 5.4), 'S-DETL', fill=H, edge=INK, lw=0.2, z=3)
    D.poly(Polygon([(21.5, 4.65), (23.4, 4.65), (26.5, 4.8), (26.5, 5.15), (21.5, 5.15)]), 'S-DETL', fill='#D3D7DB', edge=INK, lw=0.15, z=3)
    D.poly(box(26.15, 4.8, 26.5, 5.4), 'S-DETL', fill=H, edge=INK, lw=0.2, z=3)
    D.poly(box(23.25, 4.47, 26.5, 4.5), 'A-ELEV', fill='#EDEAE3', edge=INK, lw=0.08, z=3)                     # GRC soffit
    for x in np.arange(23.6, 26.4, 0.9): D.line([(x, 4.5), (x, 4.65 + (x - 23.4) * 0.05)], 'S-DETL', lw=0.06)
    D.poly(box(26.5, 4.5, 26.53, 5.45), 'A-ELEV', fill='#3A4048', edge=INK, lw=0.08, z=3)                     # fascia
    D.poly(box(21.5, 5.4, 26.44, 5.45), 'A-ELEV', fill='#DCD8CF', edge=INK, lw=0.06, z=3)                     # terrazzo
    # outer ring L1 room: glass to the gap (inner) + curtain wall behind fins (outer), ceiling
    D.poly(box(21.5, 5.45, 21.56, ou(21.6)), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.1, z=3)
    D.poly(box(26.38, 5.45, 26.44, ou(26.4)), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.1, z=3)
    for zz in (5.6, 9.0): D.poly(box(26.34, zz - 0.04, 26.48, zz + 0.04), 'A-GLAZ', fill='#9AA3AD', edge=INK, lw=0.06, z=3)
    D.line([(21.6, 8.4), (26.3, 8.4)], 'A-HIDN', lw=0.12, ls='--')
    D.poly(box(26.53, 5.45, 26.98, ou(26.5) - 0.05), 'A-ELEV', fill='#C4CAD0', edge=INK, lw=0.12, z=2)        # fin in elevation
    # ring bridge edge + gap rooflight
    D.poly(box(19.3, 5.05, 20.0, 5.4), 'S-DETL', fill=H, edge=INK, lw=0.2, z=3); D.poly(box(19.3, 4.7, 19.6, 5.05), 'S-DETL', fill=H, edge=INK, lw=0.2, z=3)
    D.poly(box(19.97, 5.4, 19.99, 6.5), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.06, z=3); D.poly(box(21.52, 5.45, 21.54, 6.55), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.06, z=3)
    D.poly(box(20.05, 5.27, 21.5, 5.37), 'A-GLAZ', fill='#E3F0F7', edge=INK, lw=0.1, z=3)
    D.poly(box(20.05, 4.95, 20.17, 5.27), 'S-DETL', fill='#9AA3AD', edge=INK, lw=0.08, z=3)
    # roof: outer tier with rafter, purlins, gutter, overhang; middle tier edge + clerestory
    rs = np.linspace(RG.T_OUT[0], 28.3, 50)
    D.poly(Polygon([(r, ot(r)) for r in rs] + [(r, ou(r)) for r in rs[::-1]]), 'A-ROOF', fill='#E6E8EB', edge=INK, lw=0.2, z=3)
    D.poly(Polygon([(r, ou(r)) for r in rs] + [(r, ou(r) - 0.45 + 0.2 * (r - rs[0]) / (rs[-1] - rs[0])) for r in rs[::-1]]), 'S-DETL', fill='#8C949C', edge=INK, lw=0.12, z=3)
    for r in np.arange(20.9, 28.2, 1.2): D.poly(box(r - 0.05, ou(r) - 0.02, r + 0.05, ou(r) + 0.18), 'S-DETL', fill=INK, edge=None, z=4)
    D.poly(box(26.75, ot(26.95) - 0.3, 27.15, ot(26.95) - 0.02), 'P-RAIN', fill='#D8ECF7', edge=WATER, lw=0.15, z=5)
    D.poly(box(28.25, ou(28.3) - 0.05, 28.3, ot(28.3) + 0.02), 'A-ELEV', fill='#3A4048', edge=INK, lw=0.08, z=5)
    rm = np.linspace(RG.T_MID[0] + 3.2, RG.T_MID[1], 20)
    mt = lambda r: RG.mid_top(Pb(r)); mu = lambda r: RG.mid_under(Pb(r))
    D.poly(Polygon([(r, mt(r)) for r in rm] + [(r, mu(r)) for r in rm[::-1]]), 'A-ROOF', fill='#D4D8DD', edge=INK, lw=0.2, z=3)
    z0, z1 = ot(20.9), mu(20.9)
    D.poly(box(20.87, z0, 20.93, z1), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.08, z=3)
    for zz in np.arange(z0 + 0.2, z1 - 0.05, 0.22): D.line([(20.68, zz + 0.1), (21.12, zz - 0.1)], 'A-GLAZ', lw=0.1)
    D.poly(box(20.0 - 0.075, 5.4, 20.0 + 0.075, mu(20.0)), 'S-DETL', fill='#8C949C', edge=INK, lw=0.1, z=3)   # bridge-edge post
    # keynotes
    tags = [((24.0, ot(24.0) + 0.05), (24.0, ot(24.0) + 1.3)), ((22.4, ou(22.4) - 0.25), (22.4, ou(22.4) - 1.2)),
            ((26.95, ot(26.95) - 0.15), (27.6, ot(27.6) + 1.2)), ((28.27, ot(28.3) - 0.2), (29.4, ot(28.3) - 0.2)),
            ((26.75, 11.0), (28.6, 11.0)), ((26.41, 7.2), (25.2, 7.2)), ((24.5, 5.0), (24.5, 6.4)), ((25.2, 4.49), (25.2, 3.4)),
            ((23.0, 2.8), (24.6, 2.8)), ((23.5, 5.43), (23.5, 7.1)), ((23.21, 2.0), (24.6, 1.6)), ((24.5, 0.82), (24.6, 0.45)),
            ((26.95, 0.3), (28.4, 1.2)), ((27.65, -0.2), (28.8, -0.6)), ((25.0, -0.3), (25.4, -1.3)), ((23.0, -1.35), (24.6, -2.1)),
            ((20.8, 5.32), (20.2, 3.6)), ((19.65, 5.2), (19.7, 7.2)), ((20.9, (z0 + z1) / 2), (19.9, (z0 + z1) / 2 + 0.9))]
    for i, (p, q) in enumerate(tags): leader(D, p, q, i + 1, sc)
    # levels
    for z, t in ((0.0, '±0.000 SITE'), (0.9, '+0.900 GF'), (5.4, '+5.400 L1 · BRIDGE'), (ot(26.0), f'+{ot(26.0):.3f} OUTER TIER'), (-1.8, '-1.800 U/S PILE CAP')):
        D.line([(30.3, z), (30.8, z)], 'A-DIMS', lw=0.15); D.text((30.9, z), t, 'A-DIMS', size=2.0, ha='left', weight='bold')
    for x0, x1, t in ((20.0, 21.5, '1500 GAP'), (21.5, 23.0, '1500'), (23.0, 26.5, '3500 CANTILEVER'), (26.5, 28.3, '1800')):
        S2._dim(D, (x0, -3.9), (x1, -3.9), -0.4, t)
    for k, l, a in D.items:
        if k == 'text' and l == 'A-DIMS': a['size'] = max(a['size'], 2.0)
    return D

# --------------------------------------------------------------------------------------------- 1:50 mid-span: gate transfer truss (Timur)
def timur_span():
    E = sorted([c for c in M.COLS if c['ring'] == 'E'], key=lambda c: c['b'])
    s = [x for x in SC.SPINES if x['k'] == 'TIMUR'][0]
    prev = min(E, key=lambda c: (s['b'] - c['b']) % 360); nxt = min(E, key=lambda c: (c['b'] - s['b']) % 360)
    L = float(np.linalg.norm(np.array(nxt['p']) - np.array(prev['p'])))
    return L, prev, nxt, s

TRUSS_NOTES = [
    'TOP CHORD SHS 200 x 200 x 10 (S355): CARRIES THE OUTER ROOF RAFTERS + THE GLAZED ROOF SLOT ON THE GATE AXIS',
    'BOTTOM CHORD SHS 200 x 200 x 10 (S355): CARRIES THE L1 DECK ON RADIAL BEAMS (THE FIRST FLOOR HANGS OVER THE GATE)',
    'DIAGONALS + VERTICALS SHS 150 x 150 x 8 (S355), PRATT PATTERN, 6 BAYS',
    'SHOP-WELDED GUSSET NODES (20 PLATE), ONE SITE-BOLTED SPLICE AT MID-SPAN (TWO 6.7 M LIFTS)',
    'COLUMN E Ø350 RC WITH CAST-IN STEEL BASE PLATE + 4 M24 HOLDING-DOWN BOLTS AT THE BEARING',
    'FIRE: THIN-FILM INTUMESCENT, 60 MIN (UBBL 5TH SCHEDULE), TOP COAT PVDF CHAMPAGNE (EXPRESSED BEHIND THE FINS)',
    'L1 DECK OVER THE GATE: 150 COMPOSITE SLAB ON METAL DECK + 200 SCREED / TERRAZZO ON THE BOTTOM CHORD; GRC SOFFIT HUNG BELOW',
    'GATE PASSAGE: CLEAR HEIGHT 3.55 M UNDER THE GRC SOFFIT AT THE +0.900 EDGE, 4.3 M AT THE GATE; FORECOURT RAMPS 1:20',
    'FOUNDATION: PILE CAP 1500 x 1500 x 900 ON 2 No. Ø450 BORED PILES UNDER EACH GATE COLUMN',
]

def detail_truss(L=None):
    """1:50 elevation of the storey-deep Pratt truss spanning the Timur gate between two E columns (x along the chord)"""
    if L is None: L = timur_span()[0]
    D = Drawing('TRUSS'); sc = 50; H = CUT
    zb, zt = 4.95, 9.35; n = 6; bay = L / n
    zr = RG.out_under(P(23.0, 27.9))
    # ground + gate passage
    D.poly(box(-2.2, -3.6, L + 2.2, 0.0), 'A-SITE', fill='#EFEBE2', edge=None, z=0)
    D.line([(-2.2, 0.0), (L + 2.2, 0.0)], 'A-SITE', lw=0.3)
    D.poly(Polygon([(-2.2, 0.9), (1.2, 0.9), (L / 2 - 1.5, 0.15), (L / 2 + 1.5, 0.15), (L - 1.2, 0.9), (L + 2.2, 0.9), (L + 2.2, 0.0), (-2.2, 0.0)]), 'A-SITE', fill='#E3DDD0', edge=INK, lw=0.15, z=1)
    D.text((L / 2, 0.45), 'GATE PASSAGE · FORECOURT RAMP FROM ±0.000 TO +0.900 (1:20)', 'A-ANNO', size=2.0)
    # columns + foundations
    for x in (0.0, L):
        D.poly(box(x - 0.175, -0.9, x + 0.175, zt + 0.15), 'S-DETL', fill=H, edge=INK, lw=0.25, z=3)
        D.poly(box(x - 0.75, -1.8, x + 0.75, -0.9), 'S-DETL', fill=H, edge=INK, lw=0.25, z=3)
        for px in (x - 0.45, x + 0.45): D.poly(box(px - 0.225, -3.5, px + 0.225, -1.8), 'S-DETL', fill=H, edge=INK, lw=0.2, z=3)
        D.line([(x - 0.9, -3.0), (x - 0.2, -3.25), (x + 0.2, -2.95), (x + 0.9, -3.2)], 'A-ANNO', lw=0.2)
    # chords
    D.poly(box(0.175, zb - 0.1, L - 0.175, zb + 0.1), 'S-DETL', fill='#8C949C', edge=INK, lw=0.2, z=4)
    D.poly(box(0.175, zt - 0.1, L - 0.175, zt + 0.1), 'S-DETL', fill='#8C949C', edge=INK, lw=0.2, z=4)
    # verticals + diagonals (Pratt: diagonals in tension, sloping down towards mid-span)
    for i in range(n + 1):
        x = i * bay; x = min(max(x, 0.25), L - 0.25)
        D.poly(box(x - 0.075, zb + 0.1, x + 0.075, zt - 0.1), 'S-DETL', fill='#A3AAB1', edge=INK, lw=0.15, z=4)
    for i in range(n):
        x0, x1 = i * bay, (i + 1) * bay
        a, c = ((x0, zt - 0.1), (x1, zb + 0.1)) if i < n / 2 else ((x0, zb + 0.1), (x1, zt - 0.1))
        a = np.array(a); c = np.array(c); t = (c - a) / np.linalg.norm(c - a); nn = np.array([-t[1], t[0]]) * 0.075
        D.poly(Polygon([a + nn, c + nn, c - nn, a - nn]), 'S-DETL', fill='#A3AAB1', edge=INK, lw=0.15, z=4)
    for i in range(n + 1):                                                                       # gusset plates
        x = i * bay
        for z in (zb, zt): D.poly(box(x - 0.22, z - 0.18, x + 0.22, z + 0.18).intersection(box(0.0, -9, L, 99)), 'S-DETL', fill='#6C747C', edge=INK, lw=0.1, z=5)
    D.line([(L / 2, zb - 0.35), (L / 2, zt + 0.35)], 'A-ANNO', lw=0.15, ls='-.', color=ACC)
    # L1 deck + roof on top
    D.poly(box(-2.2, zb + 0.1, L + 2.2, 5.4), 'S-DETL', fill=H, edge=INK, lw=0.15, z=3)
    D.poly(box(-2.2, 5.4, L + 2.2, 5.45), 'A-ELEV', fill='#DCD8CF', edge=INK, lw=0.06, z=3)
    D.poly(box(-2.2, 4.45, L + 2.2, 4.5), 'A-ELEV', fill='#EDEAE3', edge=INK, lw=0.08, z=3)
    for x in np.arange(0.6, L, 1.5): D.line([(x, 4.5), (x, zb - 0.1)], 'S-DETL', lw=0.08)
    D.poly(box(-2.2, zt + 0.1, L + 2.2, zt + 0.55), 'A-ROOF', fill='#E6E8EB', edge=INK, lw=0.2, z=3)
    D.poly(box(L / 2 - 1.0, zt + 0.1, L / 2 + 1.0, zt + 0.55), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.12, z=4)
    for x in np.arange(-1.6, L + 2.0, 1.2): D.poly(box(x - 0.05, zt + 0.1, x + 0.05, zt + 0.3), 'S-DETL', fill=INK, edge=None, z=4)
    # balustrade line + people for scale
    for x, z in ((3.2, 0.62), (L - 4.1, 0.68), (5.0, 5.45), (9.0, 5.45)): SE.man(D, x, z)
    # dims
    S2._dim(D, (0.0, -4.1), (L, -4.1), -0.45, f'{L * 1000:.0f} CLEAR SPAN BETWEEN COLUMNS E (CHORD)')
    for i in range(n): S2._dim(D, (i * bay, zt + 1.1), ((i + 1) * bay, zt + 1.1), 0.35, f'{bay * 1000:.0f}')
    S2._dim(D, (L + 0.9, zb), (L + 0.9, zt), -0.45, f'{(zt - zb) * 1000:.0f} DEPTH')
    S2._dim(D, (1.6, 0.9), (1.6, 4.45), 0.45, '3550 CLEAR')
    for k, l, a in D.items:
        if k == 'text' and l == 'A-DIMS': a['size'] = 2.0
    tags = [((3.2, zt), (3.2, zt + 2.2)), ((L - 3.0, zb), (L - 3.0, zb - 1.6)), ((bay * 1.5, (zb + zt) / 2), (bay * 1.5 - 1.0, (zb + zt) / 2 + 1.2)),
            ((bay * 3 + 0.3, zb), (L / 2 + 1.4, zb + 1.4)), ((L, zb - 0.3), (L + 1.7, zb - 1.2)), ((bay * 4.5, (zb + zt) / 2), (bay * 4.5 + 1.1, (zb + zt) / 2 - 1.3)),
            ((L - 1.2, 5.25), (L - 1.2, 7.1)), ((L / 2, 2.5), (L / 2 + 2.4, 2.7)), ((0.0, -1.4), (-1.6, -2.4))]
    for i, (p, q) in enumerate(tags): leader(D, p, q, i + 1, sc)
    return D

def truss_section():
    """1:50 radial section through the gate deck at mid-span: truss on the chord line, deck cantilevering both sides"""
    D = Drawing('TRUSS-X'); H = CUT
    zb, zt = 4.95, 9.35
    sag = 1.0
    x0 = 23.0 - sag
    D.poly(box(x0 - 0.1, zb - 0.1, x0 + 0.1, zb + 0.1), 'S-DETL', fill='#8C949C', edge=INK, lw=0.2, z=4)
    D.poly(box(x0 - 0.1, zt - 0.1, x0 + 0.1, zt + 0.1), 'S-DETL', fill='#8C949C', edge=INK, lw=0.2, z=4)
    D.poly(box(x0 - 0.075, zb + 0.1, x0 + 0.075, zt - 0.1), 'S-DETL', fill='#A3AAB1', edge=INK, lw=0.12, z=3)
    D.poly(box(21.5, 5.25, 26.5, 5.45), 'S-DETL', fill=H, edge=INK, lw=0.15, z=3)
    D.poly(Polygon([(21.5, 4.6), (26.5, 4.8), (26.5, 5.25), (21.5, 5.25)]), 'S-DETL', fill='#D3D7DB', edge=INK, lw=0.12, z=2)
    D.poly(box(21.5, 4.45, 26.5, 4.5), 'A-ELEV', fill='#EDEAE3', edge=INK, lw=0.08, z=3)
    zr = lambda r: zt + 0.1 + 0.0 * r
    D.poly(Polygon([(20.6, zt + 0.1), (28.3, zt + 0.1 - 0.2), (28.3, zt + 0.35), (20.6, zt + 0.55)]), 'A-ROOF', fill='#E6E8EB', edge=INK, lw=0.2, z=3)
    for xb in (21.55, 26.45): D.poly(box(xb - 0.01, 5.45, xb + 0.01, 6.55), 'A-GLAZ', fill=GLASS, edge=INK, lw=0.06)
    D.poly(box(26.53, 5.45, 26.98, zt - 0.05), 'A-ELEV', fill='#ECEDEF', edge=GREY, lw=0.08, z=2)
    D.text((26.75, 7.4), 'FIN', 'A-ANNO', size=2.2, rot=90, color=GREY)
    D.line([(19.8, 0.9), (29.0, 0.9)], 'A-SITE', lw=0.3)
    SE.man(D, 24.0, 5.45); SE.man(D, 24.5, 0.9)
    D.text((x0, zt + 1.5), 'TRUSS ON THE CHORD (1.0 M INSIDE\nGRID E AT MID-SPAN)', 'A-ANNO', size=2.5)
    D.text((24.2, 2.7), 'GATE PASSAGE BELOW', 'A-ANNO', size=2.5, color=GREY)
    D.text((24.9, 7.6), 'L1 DECK = WALKWAY\nOVER THE GATE', 'A-ANNO', size=2.5)
    S2._dim(D, (21.5, 3.9), (x0, 3.9), -0.3, f'{(x0 - 21.5) * 1000:.0f}'); S2._dim(D, (x0, 3.9), (26.5, 3.9), -0.3, f'{(26.5 - x0) * 1000:.0f} CANTILEVER')
    for k, l, a in D.items:
        if k == 'text' and l == 'A-DIMS': a['size'] = 2.4
    return D

# --------------------------------------------------------------------------------------------- 1:10 joints
NODE_NOTES = ['BOTTOM CHORD SHS 200 x 200 x 10', 'VERTICAL SHS 150 x 150 x 8', 'DIAGONAL SHS 150 x 150 x 8 (TENSION)',
              '20 GUSSET PLATE, 8 FILLET WELD ALL ROUND (SHOP)', 'SLOTTED END + 10 CAP PLATE, SEALED', 'DECK BEAM CLEAT: 2 No. M20 GRADE 8.8 BOLTS']
def joint_node():
    D = Drawing('NODE')
    D.poly(box(-0.62, -0.1, 0.62, 0.1), 'S-DETL', fill='#A3AAB1', edge=INK, lw=0.25, z=3)
    D.poly(box(-0.61, -0.09, 0.61, 0.09), 'S-DETL', fill='none', edge=INK, lw=0.1, ls='--', z=3)
    D.poly(box(-0.075, 0.1, 0.075, 0.68), 'S-DETL', fill='#C4CAD0', edge=INK, lw=0.2, z=3)
    ang = math.radians(62.6); t = np.array([math.cos(ang), math.sin(ang)]); nn = np.array([-t[1], t[0]]) * 0.075
    a = np.array([0.12, 0.1]) + t * 0.05; c = a + t * 0.62
    D.poly(Polygon([a + nn, c + nn, c - nn, a - nn]), 'S-DETL', fill='#C4CAD0', edge=INK, lw=0.2, z=3)
    D.poly(Polygon([(-0.3, 0.1), (0.4, 0.1), (0.4, 0.34), (0.26, 0.55), (-0.3, 0.34)]), 'S-DETL', fill='#6C747C', edge=INK, lw=0.2, z=4, alpha=0.85)
    D.poly(box(-0.28, -0.38, 0.28, -0.1), 'S-DETL', fill='#D3D7DB', edge=INK, lw=0.15, z=2)
    for x in (-0.12, 0.12): D.circle((x, -0.2), 0.022, 'S-DETL', fill='white', edge=INK, lw=0.08, z=4)
    tags = [((-0.5, 0.0), (-0.72, 0.28)), ((-0.075, 0.62), (-0.45, 0.66)), ((0.38, 0.6), (0.72, 0.62)), ((0.25, 0.25), (0.72, 0.3)),
            ((0.33, 0.45), (0.72, 0.46)), ((0.0, -0.25), (0.6, -0.32))]
    for i, (p, q) in enumerate(tags): leader(D, p, q, i + 1, 10)
    return D

FIN_NOTES = ['FIN 450 x 60 EXTRUDED ALUMINIUM 6063-T6, PVDF CHAMPAGNE-SILVER', 'SS316 PIN Ø20 THROUGH NYLON BUSH: SETS THE FIN ANGLE 18°-90°',
             'SS316 FORK BRACKET, 8 PLATE, M12 BOLTS', 'CAST-IN CHANNEL IN THE SLAB EDGE BEAM (TOP + BOTTOM FIXING)',
             'EPDM ISOLATION PAD (NO ALUMINIUM-STEEL CONTACT)', 'GRC FASCIA 20 + SLAB EDGE BEAM 600']
def joint_fin():
    """1:10 plan at the bottom fin bracket"""
    D = Drawing('FIN')
    D.poly(box(-0.6, -0.35, 0.6, 0.0), 'S-DETL', fill=CUT, edge=INK, lw=0.25, z=2)
    D.poly(box(-0.6, -0.02, 0.6, 0.0), 'A-ELEV', fill='#3A4048', edge=None, z=3)
    D.poly(box(-0.1, -0.06, 0.1, -0.02), 'S-DETL', fill='#6C747C', edge=INK, lw=0.1, z=3)
    D.poly(box(-0.05, 0.0, 0.05, 0.12), 'S-DETL', fill='#9AA3AD', edge=INK, lw=0.15, z=3)
    D.poly(box(-0.06, 0.0, 0.06, 0.008), 'S-DETL', fill=INK, edge=None, z=4)
    D.circle((0.0, 0.1), 0.01, 'S-DETL', fill='white', edge=INK, lw=0.08, z=6)
    ang = math.radians(54)
    fin = Polygon([(-0.03, 0.0), (0.03, 0.0), (0.03, 0.45), (-0.03, 0.45)])
    from shapely import affinity
    fin = affinity.rotate(affinity.translate(fin, 0, 0.07), -(90 - 54), origin=(0.0, 0.1))
    D.poly(fin, 'A-ELEV', fill='#D9D2BE', edge=INK, lw=0.2, z=5)
    D.poly(fin.buffer(-0.006), 'A-ELEV', fill='none', edge=INK, lw=0.06, z=5)
    for a_ in (18, 90):
        f2 = affinity.rotate(affinity.translate(Polygon([(-0.03, 0), (0.03, 0), (0.03, 0.45), (-0.03, 0.45)]), 0, 0.07), -(90 - a_), origin=(0.0, 0.1))
        D.poly(f2, 'A-HIDN', fill='none', edge=GREY, lw=0.08, ls='--', z=4)
    D.text((-0.72, 0.6), 'FIN RANGE 18° (CLOSED, MID-PETAL)\nTO 90° (OPEN, AT THE GATES)', 'A-ANNO', size=2.3, ha='left', color=GREY)
    tags = [((0.13, 0.3), (0.45, 0.3)), ((0.0, 0.1), (-0.35, 0.3)), ((0.04, 0.05), (-0.4, 0.12)), ((0.0, -0.04), (-0.35, -0.12)),
            ((0.05, 0.004), (0.4, 0.06)), ((-0.4, -0.2), (-0.68, -0.2))]
    for i, (p, q) in enumerate(tags): leader(D, p, q, i + 1, 10)
    return D

# --------------------------------------------------------------------------------------------- diagrams (paper mm)
def lonlat_xy(lon, lat, k):
    return ((lon - 99.5) * k * math.cos(math.radians(4)), (lat - 1.2) * k)

CAPS = [('KANGAR', 100.199, 6.441), ('ALOR SETAR', 100.367, 6.121), ('GEORGE TOWN', 100.333, 5.414), ('IPOH', 101.083, 4.597),
        ('KOTA BHARU', 102.238, 6.133), ('K. TERENGGANU', 103.137, 5.330), ('KUANTAN', 103.326, 3.808), ('SHAH ALAM', 101.519, 3.073),
        ('KUALA LUMPUR', 101.687, 3.139), ('SEREMBAN', 101.938, 2.726), ('MELAKA', 102.250, 2.189), ('JOHOR BAHRU', 103.741, 1.493)]
TEMERLOH = (102.419, 3.449)

def peninsula(k=36.0, pahang=True, lines=True, labels=True, lab_size=2.4):
    """Peninsular Malaysia states (Natural Earth admin-1), Temerloh + the state capitals, in paper mm (lon/lat scaled by k mm per degree)"""
    D = Drawing('PEN', paper=True)
    gj = json.load(open(os.path.join(HERE, 'peninsula_states.geojson')))
    for f in gj['features']:
        g = shape(f['geometry']); nm = f['properties']['name']
        for poly in getattr(g, 'geoms', [g]):
            pts = [lonlat_xy(x, y, k) for x, y in poly.exterior.coords]
            hi = pahang and nm == 'Pahang'
            D.poly(Polygon(pts), 'A-LAND', fill='#E7DCC6' if hi else '#F7F4EE', edge='#9C9284', lw=0.2, z=1)
    t = lonlat_xy(*TEMERLOH, k)
    if lines:
        for nm, lo, la in CAPS:
            p = lonlat_xy(lo, la, k)
            D.line([p, t], 'A-ANNO', lw=0.35, color=ACC, z=3, ls='-')
            D.circle(p, 0.9, 'A-ANNO', fill=INK, edge=None, z=4)
            if labels:
                dx = -1.5 if lo < TEMERLOH[0] else 1.5
                dy = {'SHAH ALAM': -2.2, 'KUALA LUMPUR': 1.4, 'SEREMBAN': -1.0}.get(nm, 0.0) * lab_size / 2.4
                D.text((p[0] + dx, p[1] + dy), nm, 'A-ANNO', size=lab_size, ha='right' if dx < 0 else 'left', z=5, halo=True)
    D.circle(t, 2.2, 'A-ANNO', fill=ACC, edge='white', lw=0.5, z=6)
    D.text((t[0] + 3.2, t[1] - 2.6), 'TEMERLOH', 'A-ANNO', size=lab_size + 0.6, weight='bold', ha='left', z=6, halo=True)
    return D

def dev_diagrams():
    """three small plan diagrams in model metres: Crit 1 (two rings), v2 (one centre, 4 gates), v3.1 (three rings + bridge)"""
    import sys; sys.path.insert(0, os.path.join(HERE, '..', 'model'))
    out = []
    site_v1 = Polygon(np.load('/home/claude/crit1/site.npy'))
    D = Drawing('V1'); D.poly(site_v1, 'A-SITE', fill='#F7F4EE', edge=GREY, lw=0.25, ls='-.')
    Bc = np.array([61.0, 22.0]); q = math.radians(292.3); Sc = Bc + 26.22 * np.array([math.sin(q), math.cos(q)])
    D.poly(Point(Bc).buffer(21.5).difference(Point(Bc).buffer(9.0)), 'A-WALL', fill='#C9CDD2', edge=INK, lw=0.3)
    D.poly(Point(Sc).buffer(10.6).difference(Point(Sc).buffer(2.5)), 'A-WALL', fill='#C9CDD2', edge=INK, lw=0.3)
    for c in (Bc, Sc): D.circle(c, 1.2, 'A-ANNO', fill=ACC, edge=None)
    out.append(D)
    D = Drawing('V2'); D.poly(SC.SITE, 'A-SITE', fill='#F7F4EE', edge=GREY, lw=0.25, ls='-.')
    D.poly(SC.ann(9.0, 26.5).difference(SC.GF_VOID), 'A-WALL', fill='#C9CDD2', edge=INK, lw=0.3)
    for s in SC.SPINES: D.line([P(9, s['b']), P(40, s['b'])], 'A-ANNO', lw=0.5, color=ACC)
    D.circle(C, 1.2, 'A-ANNO', fill=ACC, edge=None); out.append(D)
    D = Drawing('V3'); D.poly(SC.SITE, 'A-SITE', fill='#F7F4EE', edge=GREY, lw=0.25, ls='-.')
    for g, f in ((RG.INNER, '#AEB4BA'), (RG.BRIDGE, '#D9C7A6'), (RG.OUTER, '#C9CDD2')): D.poly(g, 'A-WALL', fill=f, edge=INK, lw=0.25)
    D.poly(RG.WALKWAYS.intersection(SC.ann(15.5, 21.5)), 'A-WALL', fill='#D9C7A6', edge=INK, lw=0.2)
    for s in SC.SPINES: D.line([P(26.5, s['b']), P(40, s['b'])], 'A-ANNO', lw=0.5, color=ACC)
    D.circle(C, 1.2, 'A-ANNO', fill=ACC, edge=None); out.append(D)
    return out

def synthesis(scale=1500):
    """site synthesis diagram in model metres: site, building, sun path, monsoons, river, roads, gates (text sizes in paper mm)"""
    D = Drawing('SYN'); f = 1500.0 / scale; ts = 2.2
    D.poly(SC.SITE, 'A-SITE', fill='#F7F4EE', edge=INK, lw=0.35, ls='-.', z=1)
    D.poly(SC.disc(26.5), 'A-WALL', fill='#D7DBDF', edge=INK, lw=0.25, z=2)
    D.circle(C, 9.0, 'A-WALL', fill='#F2E6CF', edge=INK, lw=0.2, z=3)
    # roads (schematic bands) + river to the east
    for a, b_ in (((-8, 1.1), (122, -17.2)), ((113.5, -17), (101.5, 72))):
        D.line([a, b_], 'A-SITE', lw=1.6, color='#C9CDD2', z=0)
    D.text((44, -11.5), 'MAIN ROAD · ARRIVAL + NOISE', 'A-ANNO', size=ts, color=GREY, weight='bold', rot=-8)
    D.line([(128, -24), (124, 76)], 'A-ANNO', lw=2.2, color='#9FD0E6', z=0)
    D.text((131, 26), 'SUNGAI PAHANG (≈150 M EAST)', 'A-ANNO', size=ts, color=WATER, weight='bold', rot=-88, ha='center')
    # sun path E -> W
    th = np.linspace(-1, 1, 41)
    arc = [(C[0] + 48 * t, C[1] - 5 * (1 - t * t) + 2) for t in th]
    D.line(arc, 'A-ANNO', lw=0.6, color=SKY, z=4)
    D.circle(arc[-1], 2.2 * f, 'A-ANNO', fill='#E8833A', edge=None, z=5); D.circle(arc[0], 2.2 * f, 'A-ANNO', fill=SKY, edge=None, z=5)
    D.text((arc[-1][0], arc[-1][1] + 5 * f), 'SUNRISE', 'A-ANNO', size=ts, color='#B4561E', weight='bold')
    D.text((arc[0][0], arc[0][1] + 5 * f), 'SUNSET · HOT WEST SUN', 'A-ANNO', size=ts, color='#B4561E', weight='bold')
    # monsoons
    for ang, lab, col in ((45.0, 'SW MONSOON (MAY-SEP)', AIR), (225.0, 'NE MONSOON (NOV-MAR)', '#2F6A8F')):
        t = np.array([math.sin(math.radians(ang)), math.cos(math.radians(ang))]); n = np.array([-t[1], t[0]])
        o = np.array(C) - t * 62
        for k in (-9, 0, 9):
            a = o + n * k; c = a + t * 14
            D.line([a, c], 'A-ANNO', lw=0.6, color=col, z=5)
            D.poly(Polygon([c + t * 2.6 * f, c + n * 1.3 * f, c - n * 1.3 * f]), 'A-ANNO', fill=col, edge=None, z=5)
        q = o - t * 8
        D.text(q, lab, 'A-ANNO', size=ts, color=col, weight='bold', ha='center', halo=True)
    for s in SC.SPINES:
        D.line([P(10, s['b']), P(36, s['b'])], 'A-ANNO', lw=0.5, color=ACC, ls='--', z=4)
        D.text(P(40 if s['k'] != 'SELATAN' else 38, s['b']), s['k'], 'A-ANNO', size=ts, color=ACC, weight='bold', z=6, halo=True)
    D.circle(C, 1.2 * f, 'A-ANNO', fill=ACC, edge=None, z=6)
    return D

def axo_xy(x, y, z, az=210.0, el=30.0):
    a = math.radians(az); X, Y = x - C[0], y - C[1]
    u = X * math.cos(a) - Y * math.sin(a)
    v = (X * math.sin(a) + Y * math.cos(a)) * math.sin(math.radians(el)) + z * math.cos(math.radians(el))
    return (u, v)

def structure_axo(spread=7.0):
    """exploded structural axonometric (model metres projected): pile caps + ground beams, columns, L1 ring beams + gate trusses,
    L2 slab, roof rafters + funnel + mast"""
    D = Drawing('STRAXO')
    def ring(r, z, lw, col=INK, ls='-', n=96, zoff=0):
        pts = [axo_xy(*P(r, b), z + zoff) for b in np.linspace(0, 360, n + 1)]
        D.line(pts, 'S-DETL', lw=lw, color=col, ls=ls)
    off = {'F': 0.0, 'G': 0.0, 'L1': spread, 'L2': 2 * spread, 'R': 3 * spread}
    # foundations + ground beams
    for r in (11.0, 15.5, 18.5, 23.0): ring(r, -0.6, 0.25, '#8C949C')
    cols = [c for c in M.COLS if c['ring'] in 'BCDE']
    for c in cols:
        x, y = c['p']; D.poly(Polygon([axo_xy(x + dx, y + dy, -0.6) for dx, dy in ((-0.75, -0.75), (0.75, -0.75), (0.75, 0.75), (-0.75, 0.75))]), 'S-DETL', fill='#C9CDD2', edge=INK, lw=0.08)
    # columns GF
    for c in cols:
        x, y = c['p']; top = 4.8
        D.line([axo_xy(x, y, 0.9), axo_xy(x, y, top)], 'S-DETL', lw=0.45, color=INK)
    # L1 rings (offset) + gate trusses
    z1 = 5.1 + off['L1']
    for r, lw in ((9.5, 0.3), (15.5, 0.3), (17.0, 0.35), (20.0, 0.35), (21.5, 0.3), (26.5, 0.45)): ring(r, z1, lw, '#5E666E' if r in (17.0, 20.0) else INK)
    for s in SC.SPINES: D.line([axo_xy(*P(15.5, s['b']), z1), axo_xy(*P(21.5, s['b']), z1)], 'S-DETL', lw=1.2, color='#D9C7A6')
    E = sorted([c for c in M.COLS if c['ring'] == 'E'], key=lambda c: c['b'])
    for s in SC.SPINES:
        a = min(E, key=lambda c: (s['b'] - c['b']) % 360); b_ = min(E, key=lambda c: (c['b'] - s['b']) % 360)
        pa, pb = np.array(a['p']), np.array(b_['p']); n = 6
        zb, zt = 4.95 + off['L1'], 9.35 + off['L1']
        D.line([axo_xy(*pa, zb), axo_xy(*pb, zb)], 'S-DETL', lw=0.6, color=ACC); D.line([axo_xy(*pa, zt), axo_xy(*pb, zt)], 'S-DETL', lw=0.6, color=ACC)
        for i in range(n + 1):
            q = pa + (pb - pa) * i / n; D.line([axo_xy(*q, zb), axo_xy(*q, zt)], 'S-DETL', lw=0.35, color=ACC)
        for i in range(n):
            q0 = pa + (pb - pa) * i / n; q1 = pa + (pb - pa) * (i + 1) / n
            if i < n / 2: D.line([axo_xy(*q0, zt), axo_xy(*q1, zb)], 'S-DETL', lw=0.35, color=ACC)
            else: D.line([axo_xy(*q0, zb), axo_xy(*q1, zt)], 'S-DETL', lw=0.35, color=ACC)
    for c in [c for c in M.COLS if c['ring'] in 'BCE']:
        x, y = c['p']; D.line([axo_xy(x, y, 5.4 + off['L1']), axo_xy(x, y, 9.0 + off['L1'])], 'S-DETL', lw=0.3, color=GREY)
    # L2 slab (inner ring)
    z2 = 9.3 + off['L2']
    for r in (9.5, 15.5): ring(r, z2, 0.35)
    for c in [c for c in M.COLS if c['ring'] in 'BC']:
        x, y = c['p']; D.line([axo_xy(x, y, 9.6 + off['L2']), axo_xy(x, y, 12.0 + off['L2'])], 'S-DETL', lw=0.3, color=GREY)
    # roof: radial rafters of the three tiers + funnel + mast
    zr = off['R']
    for bb in np.arange(0, 360, 7.5):
        rr = np.linspace(RG.R_OC, RG.R_FUN, 12)
        D.line([axo_xy(*P(r, bb), RG.fun_top(P(r, bb)) + zr) for r in rr], 'S-DETL', lw=0.15, color='#5E666E')
        rr = np.linspace(RG.T_OUT[0], RG.T_OUT[1], 6)
        D.line([axo_xy(*P(r, bb), RG.out_top(P(r, bb)) + zr) for r in rr], 'S-DETL', lw=0.15, color='#5E666E')
    for r, f in ((RG.R_OC, lambda p: RG.fun_top(p)), (RG.R_FUN, lambda p: RG.fun_top(p)), (RG.T_OUT[1], lambda p: RG.out_top(p)), (RG.T_OUT[0], lambda p: RG.out_top(p)),
                 (RG.T_MID[0], lambda p: RG.mid_top(p)), (RG.T_MID[1], lambda p: RG.mid_top(p))):
        D.line([axo_xy(*P(r, bb), f(P(r, bb)) + zr) for bb in np.linspace(0, 360, 121)], 'S-DETL', lw=0.3, color=INK)
    D.line([axo_xy(*C, 0.9), axo_xy(*C, 30.0 + zr)], 'S-DETL', lw=1.0, color=ACC)
    for bb in np.arange(0, 360, 30): D.line([axo_xy(*C, 26.0 + zr), axo_xy(*P(RG.R_OC, bb), RG.Z_OC + zr)], 'S-DETL', lw=0.12, color=ACC, ls='--')
    # dashed alignment posts
    for bb in (60, 150, 240, 330):
        x, y = P(26.5, bb); D.line([axo_xy(x, y, 4.8), axo_xy(x, y, 5.1 + off['L1'])], 'A-HIDN', lw=0.12, ls='--', color=GREY)
    return D, off

def env_section():
    """section A-A (reused) with daylight, stack-effect air, rain-to-oculus and shade arrows"""
    (A, XA), _ = SE.section_set()
    A.items = [(k, l, a) for k, l, a in A.items if l != 'A-GRID' and (k != 'text' or (l == 'A-DIMS' and a['size'] >= 1.4))]
    for k, l, a in A.items:
        if k == 'text': a['size'] = 2.2; a['s'] = a['s'].upper()
    for k, l, a in A.items:
        if k in ('poly',) and a.get('fill') not in (None, 'none'): a['alpha'] = 0.55
    uc = XA.u(C)
    def arrow(pts, col, lw=0.6):
        A.line(pts, 'A-ANNO', lw=lw, color=col, z=9)
        a, c = np.array(pts[-2]), np.array(pts[-1]); t = (c - a) / np.linalg.norm(c - a); n = np.array([-t[1], t[0]])
        A.poly(Polygon([c + t * 0.9, c + n * 0.5, c - n * 0.5]), 'A-ANNO', fill=col, edge=None, z=9)
    for sgn in (-1, 1):
        for r in (16.25, 20.9):
            arrow([(uc + sgn * (r + 6), 25.0), (uc + sgn * r, 7.0)], SKY, 0.5)                    # daylight down the gaps
            arrow([(uc + sgn * r, 6.5), (uc + sgn * r, 17.0), (uc + sgn * (r + 1.5), 21.0)], '#C0392B', 0.45)   # warm air out
        arrow([(uc + sgn * 34, 2.6), (uc + sgn * 26, 2.6), (uc + sgn * 11, 2.2)], AIR, 0.6)            # cross-ventilation at GF
    arrow([(uc, 26.0), (uc, 12.5)], WATER, 0.7)
    arrow([(uc + 13, 21.5), (uc + 3, 13.0)], WATER, 0.45); arrow([(uc - 13, 21.5), (uc - 3, 13.0)], WATER, 0.45)
    return A, XA

# --------------------------------------------------------------------------------------------- 1:25 facade section (broken)
FAC_NOTES = ['ROOF: 0.9 ALUMINIUM STANDING SEAM, BREATHER MEMBRANE, 100 ROCKWOOL, PERFORATED LINER',
             'TAPERED STEEL RAFTER S355 + Z-PURLINS 200 @ 1200',
             'CONCEALED BOX GUTTER SS316 400 W, SUMP + Ø150 OUTLET TO THE RWDP IN THE FIN CASING',
             'ROOF EDGE: 3 MM ALUMINIUM FASCIA, PVDF DARK BRONZE; 1800 OVERHANG',
             'FIN TOP FIXING: SS316 PIN BRACKET ON THE RAFTER EDGE BEAM (JOINT 14)',
             'VERTICAL FIN 450 x 60 HOLLOW ALUMINIUM, PVDF CHAMPAGNE, 750 C/C, ANGLE 18°-90°',
             'CURTAIN WALL HEAD: ALUMINIUM TRANSOM + DEFLECTION HEAD (±20) UNDER THE RAFTER',
             'CURTAIN WALL G1: DGU 6 LOW-E + 12 ARGON + 6 HS ON 65 x 150 MULLIONS @ 1500',
             'FIN BOTTOM FIXING: SS316 FORK BRACKET ON A CAST-IN CHANNEL IN THE EDGE BEAM',
             'L1 FLOOR: 20 TERRAZZO TILES ON 50 SCREED',
             'RC SLAB 250 + EDGE BEAM 600 (C35) ON RADIAL CANTILEVER BEAMS',
             'GRC FASCIA 20, DARK BRONZE, ON STAINLESS CLEATS',
             'GRC SOFFIT PANEL 20 ON GALVANISED HANGERS (THE HANGING FIRST FLOOR)']
def facade_broken(zt=16.2, lo=(4.3, 6.4), hi=(14.3, 16.9), gap=0.45):
    """1:25 section at the outer-ring edge (x = radius - 26.5), drawn in two windows with a break: slab edge + roof edge"""
    D = Drawing('FAC'); H = CUT
    sh = hi[0] - lo[1] - gap
    def Z(z): return z if z <= lo[1] + 1e-6 else z - sh
    def bx(x0, z0, x1, z1, *a, **k):
        for (a0, a1) in (lo, hi):
            q0, q1 = max(z0, a0), min(z1, a1)
            if q1 > q0: D.poly(box(x0, Z(q0), x1, Z(q1)), *a, **k)
    bx(-1.6, 4.8, 0.0, 5.4, 'S-DETL', fill=H, edge=INK, lw=0.25); bx(-0.35, 4.55, 0.0, 4.8, 'S-DETL', fill=H, edge=INK, lw=0.25)
    bx(0.0, 4.5, 0.03, 5.45, 'A-ELEV', fill='#3A4048', edge=INK, lw=0.1)
    bx(-1.6, 5.4, 0.0, 5.45, 'A-ELEV', fill='#DCD8CF', edge=INK, lw=0.1)
    bx(-1.6, 4.47, -0.35, 4.5, 'A-ELEV', fill='#EDEAE3', edge=INK, lw=0.08)
    for x in (-1.3, -0.7): bx(x - 0.01, 4.5, x + 0.01, 4.8, 'S-DETL', fill=INK, edge=None)
    bx(-0.25, 5.45, -0.15, zt - 0.62, 'A-GLAZ', fill=GLASS, edge=INK, lw=0.15)
    bx(-0.28, 5.45, -0.12, 5.6, 'A-GLAZ', fill='#9AA3AD', edge=INK, lw=0.1); bx(-0.28, zt - 0.72, -0.12, zt - 0.6, 'A-GLAZ', fill='#9AA3AD', edge=INK, lw=0.1)
    bx(0.03, 5.45, 0.48, zt - 0.6, 'A-ELEV', fill='#D9D2BE', edge=INK, lw=0.15)
    for zz in (5.6, zt - 0.75): bx(0.0, zz - 0.05, 0.12, zz + 0.05, 'S-DETL', fill=INK, edge=None)
    # roof edge
    D.poly(Polygon([(-1.6, Z(zt - 0.95)), (0.0, Z(zt - 0.82)), (1.55, Z(zt - 0.5)), (1.55, Z(zt - 0.45)), (-1.6, Z(zt - 0.45))]), 'S-DETL', fill='#8C949C', edge=INK, lw=0.15)
    D.poly(Polygon([(-1.6, Z(zt - 0.45)), (1.55, Z(zt - 0.45)), (1.8, Z(zt - 0.12)), (1.8, Z(zt)), (-1.6, Z(zt))]), 'A-ROOF', fill='#E6E8EB', edge=INK, lw=0.2)
    for x in np.arange(-1.4, 1.3, 0.6): D.poly(box(x - 0.04, Z(zt - 0.45), x + 0.04, Z(zt - 0.3)), 'S-DETL', fill=INK, edge=None)
    D.poly(box(1.35, Z(zt - 0.32), 1.75, Z(zt - 0.05)), 'P-RAIN', fill='#D8ECF7', edge=WATER, lw=0.15)
    D.poly(box(1.75, Z(zt - 0.2), 1.8, Z(zt + 0.03)), 'A-ELEV', fill='#3A4048', edge=INK, lw=0.08)
    # break
    zb0, zb1 = lo[1] + 0.06, lo[1] + gap - 0.06
    for zz in (zb0, zb1):
        D.line([(-1.9, zz), (-0.2, zz), (-0.1, zz + 0.12), (0.0, zz - 0.12), (0.1, zz), (2.1, zz)], 'A-ANNO', lw=0.18)
    # levels + dims
    D.line([(2.25, 5.4), (2.6, 5.4)], 'A-DIMS', lw=0.15); D.text((2.7, 5.4), '+5.400 FFL L1', 'A-DIMS', size=2.2, ha='left', weight='bold')
    D.line([(2.25, Z(zt)), (2.6, Z(zt))], 'A-DIMS', lw=0.15); D.text((2.7, Z(zt)), '+10.200 TO +16.200\nOUTER TIER', 'A-DIMS', size=2.2, ha='left', weight='bold')
    S2._dim(D, (0.0, 4.15), (0.48, 4.15), -0.2, '450')
    S2._dim(D, (0.0, Z(zt) + 0.25), (1.8, Z(zt) + 0.25), 0.2, '1800 OVERHANG')
    for k, l, a in D.items:
        if k == 'text' and l == 'A-DIMS': a['size'] = max(a['size'], 2.2)
    tags = [((-0.8, Z(zt - 0.2)), (-1.2, Z(zt) + 0.55)), ((-1.0, Z(zt - 0.7)), (-2.1, Z(zt - 0.7))), ((1.55, Z(zt - 0.2)), (2.05, Z(zt) + 0.45)),
            ((1.78, Z(zt - 0.1)), (2.15, Z(zt - 0.45))), ((0.06, Z(zt - 0.75)), (0.85, Z(zt - 1.25))), ((0.25, Z(14.7)), (0.95, Z(14.6))),
            ((-0.2, Z(zt - 0.66)), (-1.1, Z(zt - 1.15))), ((-0.2, 6.0), (-1.1, 6.05)), ((0.06, 5.6), (0.85, 6.0)), ((-1.0, 5.43), (-1.3, 6.0)),
            ((-0.8, 5.1), (-2.1, 5.1)), ((0.015, 4.9), (0.6, 4.65)), ((-1.0, 4.485), (-1.35, 4.05))]
    for i, (p, q) in enumerate(tags): leader(D, p, q, i + 1, 25)
    return D

ROOF_NOTES = ['RING BRIDGE SLAB EDGE 350 ON A STEEL BOX RING BEAM', 'GLASS BALUSTRADE G4, 17.52 LAMINATED, 1100 HIGH',
              'WALK-ON ROOFLIGHT G5: 3 x 12 HS LAMINATED, OPAL INTERLAYER, ANTI-SLIP FRIT, ON EPDM', 'STEEL BEAM ON THE GF WALLS: THE ROOFLIGHT BELONGS TO THE GROUND FLOOR',
              '50 MOVEMENT JOINT + EPDM SKIRT: THE BRIDGE IS NOT TIED TO IT']
def rooflight_joint():
    D = S2.detail_rooflight()
    D.items = [(k, l, a) for k, l, a in D.items if l != 'A-ANNO']
    tags = [((0.45, 0.17), (0.7, 0.42)), ((0.03, 0.4), (0.32, 0.44)), ((-0.35, -0.08), (-0.55, 0.25)), ((-0.35, -0.24), (-0.62, -0.42)), ((-0.045, -0.07), (0.3, -0.35))]
    for i, (p, q) in enumerate(tags): leader(D, p, q, i + 1, 10)
    return D
