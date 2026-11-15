"""Titik Temu v3 review drawings: to-scale SVG diagrams + the 3D model data, from v2/scheme.py (used by v2/page.py).
Named drawings.py because model/draw.py already exists."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model'))
import numpy as np, cv2
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from scheme import *
import geom as G, site_el as SE

class View:
    def __init__(s, x0, x1, y0, y1, k): s.x0, s.x1, s.y0, s.y1, s.k = x0, x1, y0, y1, k; s.w = (x1 - x0) * k; s.h = (y1 - y0) * k; s.out = []
    def X(s, p): return ((p[0] - s.x0) * s.k, (s.y1 - p[1]) * s.k)
    def d(s, g):
        out = ''
        for q in getattr(g, 'geoms', [g]):
            if q.is_empty or q.geom_type != 'Polygon': continue
            for ring in [q.exterior] + list(q.interiors):
                out += 'M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in (s.X(c) for c in ring.coords)) + 'Z'
        return out
    def poly(s, g, cls, extra=''):
        dd = s.d(g)
        if dd: s.out.append(f'<path class="{cls}" fill-rule="evenodd" d="{dd}" {extra}/>')
    def line(s, a, b, cls, extra=''):
        (x1, y1), (x2, y2) = s.X(a), s.X(b); s.out.append(f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {extra}/>')
    def circ(s, p, r_m, cls):
        x, y = s.X(p); s.out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r_m * s.k:.1f}"/>')
    def dot(s, p, r_px, cls):
        x, y = s.X(p); s.out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r_px}"/>')
    def text(s, p, t, cls='t', anchor='middle', dx=0, dy=0, rot=None):
        x, y = s.X(p); x += dx; y += dy
        tr = f' transform="rotate({rot:.1f} {x:.1f} {y:.1f})"' if rot is not None else ''
        lines = t.split('\n')
        sp = ''.join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else 11.5}">{l}</tspan>' for i, l in enumerate(lines))
        s.out.append(f'<text class="{cls}" x="{x:.1f}" y="{y - 5.7 * (len(lines) - 1):.1f}" text-anchor="{anchor}"{tr}>{sp}</text>')
    def svg(s, label, minw=None):
        st = f' style="min-width:{minw}px"' if minw else ''
        return f'<svg viewBox="0 0 {s.w:.0f} {s.h:.0f}" role="img" aria-label="{label}"{st}>' + ''.join(s.out) + '</svg>'

Hm = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mockup', 'H.npy'))
def ph(b): return Polygon(cv2.perspectiveTransform(np.array([b], float), Hm)[0])
CTX = [('ISTANA SRI UDARA', ph([(105, 470), (205, 470), (205, 570), (105, 570)]), 5.0),
       ('AD FUTSAL COURT', ph([(470, 280), (760, 265), (785, 440), (500, 455)]).difference(SITE.buffer(2.5)), 7.5),
       ('NEIGHBOUR BLOCK', ph([(400, 290), (445, 290), (470, 410), (415, 410)]), 5.0)]
TR, NI = SE.T_ROAD, SE.N_IN
ROADP = Polygon([tuple(SE.ROAD_A - TR * 30), tuple(SE.ROAD_B + TR * 40), tuple(SE.ROAD_B + TR * 40 - NI * 9), tuple(SE.ROAD_A - TR * 30 - NI * 9)])
_e0, _e1 = np.array(SITE_PTS[2]), np.array(SITE_PTS[4]); _de = (_e1 - _e0) / np.linalg.norm(_e1 - _e0); _ne = np.array([_de[1], -_de[0]]); _ne = _ne if _ne[0] > 0 else -_ne
ROADE = Polygon([tuple(_e0 - _de * 25), tuple(_e1 + _de * 8), tuple(_e1 + _de * 8 + _ne * 9), tuple(_e0 - _de * 25 + _ne * 9)])   # Jalan Ibrahim
S_MAIN = [s for s in SPINES if s.get('main')][0]
E_MAIN = np.array(spine_end(S_MAIN['b']).coords[0])
LAYBY = Polygon([tuple(E_MAIN - TR * 18 + NI * 0.6), tuple(E_MAIN + TR * 18 + NI * 0.6), tuple(E_MAIN + TR * 15 + NI * 3.6), tuple(E_MAIN - TR * 15 + NI * 3.6)])
YARD = SITE.intersection(box(98, -20, 120, 1.5)).buffer(-1.2)                        # south-east corner: staff parking
SERVICE = SITE.intersection(box(C[0] + R_ROOF + 0.8, C[1] - 13, 130, C[1] + 15)).buffer(-1.0)   # service court off Jalan Ibrahim
ZC = dict(trade='z-trade', food='z-food', pub='z-pub', priv='z-priv', boh='z-boh', core='z-core', open='z-open')
FLOOR = dict(GF=(GF, ZONES_GF, R_GF), L1=(L1, ZONES_L1, R_L1), L2=(L2, ZONES_L2, R_L1))

def base(v, labels=True, old_site=False):
    v.poly(box(v.x0, v.y0, v.x1, v.y1), 'ground'); v.poly(ROADP, 'road'); v.poly(ROADE, 'road')
    for nm, g, h in CTX:
        v.poly(g, 'ctx')
        gi = g.intersection(box(v.x0 + 2, v.y0 + 2, v.x1 - 2, v.y1 - 2))
        if labels and not gi.is_empty and gi.area > 40:
            c = gi.representative_point(); v.text((c.x, c.y), nm + '\n(APPROX.)', 't mute')
    v.poly(SITE_V1 if old_site else SITE, 'site')
    if not old_site: v.poly(TENNIS, 'tennis')

def spines(v, r_in=R_COURT):
    for s in SPINES:
        e = np.array(spine_end(s['b']).coords[0])
        v.poly(LineString([tuple(P(r_in, s['b'])), tuple(e)]).buffer(s['w'] / 2, cap_style=2).intersection(SITE), 'spine')

def furniture(v):
    nx, ny = (v.x1 - 7, v.y1 - 9)
    v.line((nx, ny - 4), (nx, ny + 3.5), 'narrow'); v.poly(Polygon([(nx, ny + 5), (nx - 1.3, ny + 1.6), (nx + 1.3, ny + 1.6)]), 'nhead'); v.text((nx, ny - 5), 'N', 't sp', dy=10)
    sx, sy = v.x0 + 5, v.y0 + 4.5
    for i in range(4): v.poly(box(sx + i * 5, sy, sx + (i + 1) * 5, sy + 0.9), 'sb1' if i % 2 == 0 else 'sb0')
    for i in range(5): v.text((sx + i * 5, sy), str(i * 5), 't sm', dy=13)
    v.text((sx + 21.5, sy), 'M', 't sm', dy=13, anchor='start')

LBL_R = {('L1', 'RESTROOMS'): 17.2, ('L1', 'OPEN DECK'): 22.5, ('L2', 'FOYER'): 22.0, ('L2', 'CORE 1'): 21.5, ('L2', 'CORE 2'): 21.5, ('GF', 'CORE 1'): 19.5}
def plan(level):
    full = level == 'GF'
    v = View(-9, 127, -27, 75, 7.1) if full else View(C[0] - 34.2, C[0] + 34.2, C[1] - 34, C[1] + 34, 7.4)
    base(v, labels=full)
    if full:
        v.poly(ENV, 'setback'); v.poly(SITE_V1, 'oldsite'); v.poly(LAYBY, 'layby'); v.poly(YARD, 'yard'); v.poly(SERVICE, 'yard')
    spines(v)
    v.poly(disc(R_ROOF if level == 'ROOF' else R_L1), 'shadow')
    if level == 'GF':
        v.poly(BRIDGE, 'arcade')
        for l, c, a, b in ZONES_GF: v.poly(zone_geom(GF, a, b), ZC[c])
        v.poly(disc(R_COURT), 'court')
    elif level in ('L1', 'L2'):
        fl, zs, _ = FLOOR[level]
        v.poly(disc(R_COURT), 'void')
        if level == 'L2': v.poly(L1, 'below')
        for l, c, a, b in zs: v.poly(zone_geom(fl, a, b), ZC[c])
        v.poly(BRIDGE, 'bridge')
        v.poly(GF if level == 'L1' else L1, 'under')
    else:
        for p in PETALS:                                   # roof shaded by height: darker = higher
            n = max(4, round(p['span'] / 5))
            for k in range(n):
                a, b = p['b0'] + p['span'] * k / n, p['b0'] + p['span'] * (k + 1) / n
                hgt = roof_h((a + b) / 2); op = 0.08 + 0.6 * (hgt - LV['roof_lo']) / (LV['roof_hi'] - LV['roof_lo'])
                v.poly(p['roof'].intersection(sector(a, b + 0.05)), 'roofhi', f'style="fill-opacity:{op:.2f}"')
        v.poly(ROOF, 'roofline')
        v.poly(disc(R_DISC).difference(disc(R_OCULUS)), 'discroof')
        for k in range(24): v.line(P(R_OCULUS, k * 15), P(R_DISC, k * 15), 'rib')
    if level != 'ROOF':
        v.circ(C, R_POOL, 'water')
        cols = COLS_OUT + COLS_IN + COLS_DISC if level == 'GF' else COLS_IN + COLS_DISC
        for c, _ in cols: v.dot(c, 2.0, 'col')
    else: v.circ(C, R_OCULUS, 'water')
    v.dot(C, 3.4, 'titik')
    if level == 'GF': v.poly(L1, 'above'); v.poly(disc(R_DISC), 'above2')
    v.line(P(R_POOL + 0.6, QIBLA), P(33.0, QIBLA), 'qibla')
    if full: v.text(P(35.8, QIBLA), f'QIBLA {QIBLA}°', 't qb')
    else: v.text(P(30.6, QIBLA), f'QIBLA {QIBLA}°', 't qb', anchor='start', dx=-4, dy=-9)
    if level in FLOOR:
        fl, zs, rr = FLOOR[level]
        for l, c, a, b in zs:
            g = zone_geom(fl, a, b); r = LBL_R.get((level, l), (R_BR1 + rr) / 2 + (0.6 if level != 'GF' else 0)); small = g.area < 62
            v.text(P(r, (a + b) / 2), f"{l if small else l.replace(' · ', chr(10))}\n{g.area:.0f} m²", 't zl' + (' sm' if small else ''))
    if level == 'GF':
        v.text(C, 'TALAM COURT\nØ18 M · 100 SEATS', 't zl', dy=-36); v.text(C, 'TITIK POOL + MAST', 't sm', dy=31)
        for s in SPINES:
            e = np.array(spine_end(s['b']).coords[0]); L = np.linalg.norm(e - C)
            rr = {'SELATAN': 33, 'TENGAH': 46, 'UTARA': 34.5, 'TIMUR': 34.5}[s['k']]
            side = {'SELATAN': (40, 8, 'start'), 'TENGAH': (0, -40, 'middle'), 'UTARA': (-12, 2, 'end'), 'TIMUR': (12, 0, 'start')}[s['k']]
            v.text(P(rr, s['b']), f"{s['k']} {s['b']:.0f}°" + (' · MAIN GATE' if s.get('main') else '') + f"\n{L:.0f} M TO THE CENTRE", 't sp', anchor=side[2], dx=side[0], dy=side[1])
        c = LAYBY.centroid; v.text((c.x, c.y), 'DROP-OFF LAY-BY', 't sm', dx=-132, dy=-13)
        c = YARD.centroid; v.text((c.x + 1, c.y - 3.5), '5 STAFF + 1 OKU\n10 MOTORCYCLES', 't sm')
        c = SERVICE.centroid; v.text((c.x, c.y), 'SERVICE\nCOURT', 't sm')
        v.text((27, 30), 'LAMAN PEKAN SEHARI\nARRIVAL GARDEN · CAR-BOOT STALLS\n10 BICYCLES', 't mute')
        c = TENNIS.centroid; v.text((c.x - 0.5, 40.5), 'TENNIS COURT\nLAND ADDED', 't mute')
        v.text((58, -20.3), 'JALAN TOK MUDA AWANG NGAH', 't mute', rot=math.degrees(math.atan2(-TR[1], TR[0])))
        v.text((118.5, 32), 'JALAN IBRAHIM · SUNGAI PAHANG →', 't mute', rot=math.degrees(math.atan2(-_de[1], _de[0])))
        v.text((52, 66.5), 'PUBLIC PATH (NORTH)', 't mute', rot=-7.3)
        ax = d(S_MAIN['b']); wst = np.array([ax[1], -ax[0]])
        a0, a1 = C + ax * 39 + wst * 3, C - ax * 33 + wst * 3
        v.line(a0, a1, 'secline'); v.text(a0, 'A', 't sec', dx=-9, dy=10); v.text(a1, 'A', 't sec', dx=-9, dy=-2)
    if level in ('L1', 'L2'):
        v.text(C, 'OPEN TO THE\nCOURT BELOW', 't sm', dy=-22); v.text(P(11.0, 62), 'RING BRIDGE', 't sm', dy=-2)
    if level == 'L2':
        v.text(P(20, 68), 'FIRST-FLOOR DECK\nBELOW · ROOF LOW', 't mute'); v.text(P(20, 258), 'ROOF LOW\nNO THIRD FLOOR', 't mute')
    if level == 'ROOF':
        v.text(C, 'MAST +30.000', 't sm', dy=26); v.text(P(8.6, 150), 'FUNNEL ROOF Ø28', 't zl')
        for s in SPINES:
            v.text(P(31.6, s['b']), f"{s['k']}\n+{roof_h(s['b']):.3f}", 't sp' if s['crest'] else 't sm', dy=3)
        v.text(P(21.5, 112), 'RISES TO\nSELATAN', 't zl'); v.text(P(21.5, 272), 'RISES TO\nUTARA', 't zl'); v.text(P(21.5, 212), 'FALLS TO\nTENGAH', 't zl'); v.text(P(21.5, 357), 'FALLS TO\nTIMUR', 't zl')
    furniture(v)
    names = {'GF': 'Ground floor plan on the extended Site C', 'L1': 'First floor plan', 'L2': 'Second floor plan', 'ROOF': 'Roof plan'}
    return v.svg(names[level], 920 if full else 470)

def entrance():
    cen = P(21.5, S_MAIN['b']); v = View(cen[0] - 23, cen[0] + 23, cen[1] - 14.5, cen[1] + 13.5, 16)
    v.poly(box(v.x0, v.y0, v.x1, v.y1), 'site'); v.poly(ROADP, 'road'); v.poly(LAYBY, 'layby')
    spines(v)
    v.poly(BRIDGE, 'arcade')
    for l, c, a, b in ZONES_GF: v.poly(zone_geom(GF, a, b), ZC[c])
    v.poly(disc(R_COURT), 'court')
    v.poly(L1.intersection(GF_VOID.union(ann(R_GF, R_L1))), 'hang'); v.poly(L1, 'above')
    for c, _ in COLS_OUT + COLS_IN + COLS_DISC: v.dot(c, 3.4, 'col')
    b = S_MAIN['b']; ax = d(b); px = np.array([ax[1], -ax[0]])
    for off, r1 in ((-8.5, 19.6), (0, 27.2), (8.5, 19.6)):
        v.line(P(35.8, b) + px * off, P(r1, b) + px * off * 0.26, 'flow', 'marker-end="url(#arr)"')
    v.out.insert(0, '<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrh" d="M0,0L10,5L0,10z"/></marker></defs>')
    back = S_MAIN['bite'][0] - S_MAIN['bite'][1]
    v.text(P(back - 0.2, b) + px * 10.2, f'CONCAVE GROUND WALL\nSCOOPED BACK {R_GF - back:.1f} M', 't zl')
    v.text(P(R_L1 + 1.6, b) + px * 15.5, 'UPPER FLOORS STAY\nCONVEX', 't sp')
    v.text(P(24.4, b) + px * 10.5, 'TWO FLOORS\nOVERHEAD', 't sm'); v.text(P(24.4, b) - px * 10.5, 'TWO FLOORS\nOVERHEAD', 't sm')
    v.text(P(14.6, b), f"GATE {S_MAIN['w']:.0f} M", 't sm'); v.text(P(22.8, b), f"SKY SLOT {S_MAIN['gap'] - 1:.0f} M", 't sm')
    v.text(P(19.4, b) - px * 15.5, 'COLUMNS STAY ON\nTHE R 23 LINE', 't sm'); v.text(P(10.3, b) - px * 8, 'TALAM COURT', 't sm')
    c = LAYBY.centroid; v.text((c.x, c.y), 'DROP-OFF LAY-BY', 't sm', dx=-190, dy=-2)
    return v.svg('Main gate: concave ground floor under the convex upper floors', 640)

def parti(which):
    v = View(-6, 124, -24, 70, 2.65)
    base(v, labels=False, old_site=(which == 'v1'))
    if which == 'v1':
        B, S = G.B, G.S
        v.poly(Point(B).buffer(G.R_L1, 96).difference(Point(B).buffer(G.R_COURT, 96)), 'z-pub')
        v.poly(Point(S).buffer(G.RS_OUT, 96).difference(Point(S).buffer(G.RS_WELL, 96)), 'z-priv')
        qd = (S - B) / np.linalg.norm(S - B); v.line(B - qd * 30, S + qd * 22, 'qibla')
        v.dot(B, 4, 'titik'); v.dot(S, 4, 'titik'); v.text(B, 'PUBLIC', 't sm', dy=-30); v.text(S, 'PRIVATE', 't sm', dy=-36)
    else:
        v.poly(L1, 'z-pub'); v.poly(zone_geom(L1, 185.2, 277.3), 'z-priv'); v.poly(zone_geom(L1, 277.3, 315.2), 'z-priv')
        for s in SPINES: v.line(np.array(spine_end(s['b']).coords[0]), P(R_POOL, s['b']), 'spl')
        v.line(P(R_POOL, QIBLA), P(34, QIBLA), 'qibla'); v.dot(C, 4.5, 'titik')
        v.text(P(19.5, 100), 'PUBLIC', 't sm'); v.text(P(19.5, 262), 'PRIVATE\n(UPSTAIRS)', 't sm')
    return v.svg('Crit 1: two centres' if which == 'v1' else 'Proposed: one centre', None)

# ---- unrolled elevation: the facade opened out flat, clockwise from the Timur gate ------------------------------
B_START = SPINES[0]['b']
def unroll(option='A', b_from=None, b_to=None, k=6.0, labels=True):
    b_from = B_START if b_from is None else b_from; b_to = B_START + 360 if b_to is None else b_to
    PADL = 6.0 if labels else 0.0
    arc = lambda b: math.radians(b - b_from) * R_L1 + PADL
    Wm = arc(b_to); Z1 = 20.5; Hm = Z1 + 2.2
    o = []
    X = lambda b, z: (arc(b) * k, (Z1 - z) * k)
    def pg(pts, cls, extra=''): o.append(f'<path class="{cls}" {extra} d="M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + 'Z"/>')
    def tx(b, z, t, cls='t sm', anchor='middle', dy=0):
        x, y = X(b, z); sp = ''.join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else 11}">{l}</tspan>' for i, l in enumerate(t.split('\n')))
        o.append(f'<text class="{cls}" x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}">{sp}</text>')
    o.append(f'<rect class="sky" x="0" y="0" width="{Wm * k:.0f}" height="{Hm * k:.0f}"/>')
    o.append(f'<rect class="sground" x="0" y="{Z1 * k:.1f}" width="{Wm * k:.0f}" height="{2.2 * k:.1f}"/>')
    gates = []
    for s in SPINES:
        for bb in (s['b'], s['b'] + 360):
            if b_from - 2 <= bb <= b_to + 2: gates.append((bb, s))
    half = lambda s, w: math.degrees(math.asin((w / 2) / R_L1))
    segs = []                                    # solid stretches between gates
    edges = sorted([(bb - half(s, s['gap']), bb + half(s, s['gap'])) for bb, s in gates])
    cur = b_from
    for a, b in edges:
        if a > cur: segs.append((cur, a))
        cur = max(cur, b)
    if cur < b_to: segs.append((cur, b_to))
    for a, b in segs:
        n = max(2, int((b - a) * 2)); bsx = [a + (b - a) * i / n for i in range(n + 1)]
        pg([X(q, .9) for q in bsx] + [X(q, 4.8) for q in reversed(bsx)], 'eglass')                       # ground floor glass, set back
        pg([X(q, 4.8) for q in bsx] + [X(q, 5.4) for q in reversed(bsx)], 'scut')                         # first floor slab
        pg([X(q, 5.4) for q in bsx] + [X(q, roof_h(q) - ROOF_T) for q in reversed(bsx)], 'ewall')        # upper wall behind the screen
        l2 = [q for q in bsx if l2_ok(q)]
        if len(l2) > 1: pg([X(q, 9.0) for q in l2] + [X(q, 9.6) for q in reversed(l2)], 'scut', 'style="opacity:.55"')
        ext = lambda q: q + (-0.9 if q == a else 0.9 if q == b else 0)                                    # roof oversails a little
        pg([X(ext(q), roof_h(q) - ROOF_T) for q in bsx] + [X(ext(q), roof_h(q)) for q in reversed(bsx)], 'scut')
        if option == 'A':
            for fb, ang, top in FINS + [(f[0] + 360, f[1], f[2]) for f in FINS]:
                if a <= fb <= b:
                    w = max(0.07, FIN_D * abs(math.cos(math.radians(ang)))) * k; x, y = X(fb, top)
                    o.append(f'<rect class="fin" x="{x - w / 2:.1f}" y="{y:.1f}" width="{w:.1f}" height="{(top - 5.4) * k:.1f}"/>')
        elif option == 'B':
            step = 1.1
            nb = int(math.radians(b - a) * R_L1 / step)
            for i in range(nb + 1):
                q = a + (b - a) * i / max(1, nb); top = roof_h(q) - ROOF_T
                edge = min(q - a, b - q); dens = 0.25 + 0.75 * min(1, edge / 22.0)
                nz = int((top - 5.6) / step)
                for j in range(nz + 1):
                    z = 5.9 + j * step + (0.55 if i % 2 else 0)
                    if z > top - 0.3: continue
                    r = 0.42 * dens * k; x, y = X(q, z)
                    o.append(f'<path class="perf" d="M{x:.1f},{y - r:.1f}L{x + r * .7:.1f},{y:.1f}L{x:.1f},{y + r:.1f}L{x - r * .7:.1f},{y:.1f}Z"/>')
            pg([X(a, 5.4), X(b, 5.4), X(b, 5.5), X(a, 5.5)], 'scut')
        else:
            n2 = max(2, int((b - a) * 3)); qs = [a + (b - a) * i / n2 for i in range(n2 + 1)]
            for j in range(7):
                f = (j + 0.5) / 7
                def zz(q):
                    top = roof_h(q) - ROOF_T; edge = min(q - a, b - q); lift = max(0, 1 - edge / 18.0) ** 2
                    return 5.4 + (top - 5.4) * (0.06 + 0.86 * f) + lift * math.sin(math.pi * f) * 0.9
                o.append('<path class="ribbon" d="M' + 'L'.join(f'{X(q, zz(q))[0]:.1f},{X(q, zz(q))[1]:.1f}' for q in qs) + '"/>')
    if labels:
        for bb, s in gates:
            if b_from <= bb <= b_to:
                tx(bb, roof_h(s['b']) + 1.2, f"{s['k']}{' · MAIN' if s.get('main') else ''}\n+{roof_h(s['b']):.3f}", 't sp' if s['crest'] else 't sm')
        for i, p in enumerate(PETALS):
            mid = p['b0'] + p['span'] / 2
            mid = mid + 360 if mid < b_from else mid
            if b_from < mid < b_to: tx(mid, -1.3, f"{['EAST', 'SOUTH-WEST', 'WEST', 'NORTH'][i]} BLOCK", 't mute')
        for z, t in ((5.4, '+5.400'), (.9, '+0.900')):
            o.append(f'<text class="t mute" x="2" y="{(Z1 - z) * k - 3:.1f}">{t}</text>')
    return f'<svg viewBox="0 0 {Wm * k:.0f} {Hm * k:.0f}" role="img" aria-label="Unrolled elevation, facade option {option}" style="min-width:{min(900, int(Wm * k * 0.8))}px">' + ''.join(o) + '</svg>'

def facade(option):
    """a 62 m stretch of the west block, from the low Tengah gate up to the high Utara gate"""
    return unroll(option, b_from=SPINES[2]['b'] - 8, b_to=SPINES[3]['b'] + 8, k=9.0, labels=False)

def section():
    k = 11.0; U0, U1, Z0, Z1 = -42.0, 54.0, -2.9, 32.0
    W, H = (U1 - U0) * k, (Z1 - Z0) * k
    o = []
    X = lambda u, z: ((u - U0) * k, (Z1 - z) * k)
    def pg(pts, cls): o.append(f'<path class="{cls}" d="M' + 'L'.join(f'{X(u, z)[0]:.1f},{X(u, z)[1]:.1f}' for u, z in pts) + 'Z"/>')
    def ln(a, b, cls): (x1, y1), (x2, y2) = X(*a), X(*b); o.append(f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    def tx(u, z, t, cls='t sm', anchor='middle', dy=0):
        x, y = X(u, z); sp = ''.join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else 11.5}">{l}</tspan>' for i, l in enumerate(t.split('\n')))
        o.append(f'<text class="{cls}" x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}">{sp}</text>')
    def man(u, z):
        x, y = X(u, z); o.append(f'<circle class="man" cx="{x:.1f}" cy="{y - 1.58 * k:.1f}" r="{0.13 * k:.1f}"/><rect class="man" x="{x - 0.17 * k:.1f}" y="{y - 1.42 * k:.1f}" width="{0.34 * k:.1f}" height="{1.42 * k:.1f}" rx="{0.15 * k:.1f}"/>')
    bS, bN = S_MAIN['b'] + 5.0, (S_MAIN['b'] + 180) % 360            # the cut is 3 m west of the axis on the south side
    LS = spine_end(S_MAIN['b']).distance(Point(C)); LN = spine_end(bN).distance(Point(C))
    hS, hN = roof_h(bS), roof_h(bN)
    us = -(LS - 6.0); gz = lambda u: LV['plinth'] * min(1, max(0, (u - us) / (-R_BR0 - us)))
    o.append(f'<rect class="sky" x="0" y="0" width="{W:.0f}" height="{H:.0f}"/>')
    pg([(U0, 0), (us, 0), (-R_BR0, .9), (R_GF + 1.5, .9), (R_GF + 1.5, 0), (U1, 0), (U1, Z0), (U0, Z0)], 'sground')
    pg([(-R_POOL, .9), (R_POOL, .9), (R_POOL, .72), (-R_POOL, .72)], 'water')
    wb = math.sqrt(S_MAIN['bite'][1] ** 2 - (S_MAIN['w'] / 2) ** 2); rw = S_MAIN['bite'][0] - wb
    pg([(-rw, gz(-rw)), (-R_BR1, gz(-R_BR1)), (-R_BR1, 4.8), (-rw, 4.8)], 'sbeyond')
    pg([(R_BR1, .9), (R_GF, .9), (R_GF, 4.8), (R_BR1, 4.8)], 'z-food')
    pg([(-R_L1 + .5, 5.4), (-R_BR1, 5.4), (-R_BR1, 9.0), (-R_L1 + .5, 9.0)], 'z-core'); pg([(-R_L1 + .5, 9.6), (-R_BR1, 9.6), (-R_BR1, hS - ROOF_T), (-R_L1 + .5, hS - ROOF_T)], 'z-core')
    # mast
    pg([(-.42, .9), (.42, .9), (.1, LV['mast']), (-.1, LV['mast'])], 'mast')
    for sg, hh in ((-1, hS), (1, hN)):
        pg([(sg * R_BR1, 4.8), (sg * R_L1, 4.8), (sg * R_L1, 5.4), (sg * R_BR1, 5.4)], 'scut')
        pg([(sg * R_BR0, 5.05), (sg * R_BR1, 5.05), (sg * R_BR1, 5.4), (sg * R_BR0, 5.4)], 'scut')
        pg([(sg * R_BR0, 9.25), (sg * R_BR1, 9.25), (sg * R_BR1, 9.6), (sg * R_BR0, 9.6)], 'scut')
        if sg < 0: pg([(sg * R_BR1, 9.0), (sg * R_L1, 9.0), (sg * R_L1, 9.6), (sg * R_BR1, 9.6)], 'scut')
        pg([(sg * R_ROOF_IN, hh - ROOF_T), (sg * R_L1, hh - ROOF_T), (sg * R_ROOF, hh - .12), (sg * R_ROOF, hh), (sg * R_ROOF_IN, hh)], 'scut')
        pg([(sg * R_DISC, 13.5), (sg * R_OCULUS, 11.4), (sg * R_OCULUS, 11.12), (sg * R_DISC, 13.22)], 'sdisc')
        zc = 11.4 + (13.5 - 11.4) * (R_BR0 - R_OCULUS) / (R_DISC - R_OCULUS) - 0.3
        for r, top in ((R_BR0, zc), (R_BR1, hh - ROOF_T), (R_GF, hh - ROOF_T)):
            z0 = gz(sg * r) if sg < 0 else .9
            pg([(sg * r - .16, z0), (sg * r + .16, z0), (sg * r + .16, top), (sg * r - .16, top)], 'scol')
        ln((sg * R_L1, 5.4), (sg * R_L1, hh - ROOF_T), 'veil')
        ln((sg * R_BR0, 5.4), (sg * R_BR0, 6.5), 'rail'); ln((sg * R_BR0, 9.6), (sg * R_BR0, 10.7), 'rail')
    ln((R_BR1, .9), (R_BR1, 4.8), 'glass'); ln((R_GF, .9), (R_GF, 4.8), 'glass')
    for u, z in [(-35.5, 0), (-21, gz(-21)), (-5.5, .9), (4.5, .9), (20, 5.4), (17, .9), (33, 0), (-11, 9.6), (11, 9.6), (-11, 5.4)]: man(u, z)
    for u, t in [(-LS, 'SITE BOUNDARY\n(ROAD)'), (LN, 'SITE BOUNDARY\n(NORTH PATH)')]:
        ln((u, -1.2), (u, 3.2), 'bnd'); tx(u, 3.5, t, 't mute', dy=-14)
    def dim(u0, u1, z, t, up=True):
        ln((u0, z), (u1, z), 'dim'); ln((u0, z - .3), (u0, z + .3), 'dim'); ln((u1, z - .3), (u1, z + .3), 'dim'); tx((u0 + u1) / 2, z, t, 't sp', dy=-5 if up else 13)
    dim(R_GF, R_L1, 3.6, f'{CANT:.1f} M', up=False)
    dim(-R_L1, -rw, 3.9, f'{R_L1 - rw:.1f} M OVER THE FORECOURT', up=False)
    dim(us, -R_BR0, -1.0, f'FORECOURT RISES 0.9 M OVER {(-R_BR0 - us):.1f} M (1:{(-R_BR0 - us) / .9:.0f})', up=False)
    for z, t, dy in [(LV['mast'], '+30.000 MAST', 3.5), (LV['roof_hi'], '+16.200 ROOF, HIGH GATES', 3.5), (13.5, '+13.500 FUNNEL RIM', 3.5), (LV['roof_lo'], '+10.200 ROOF, LOW GATES', -1), (9.6, '+9.600 SECOND FLOOR', 10), (5.4, '+5.400 FIRST FLOOR', 3.5), (0.9, '+0.900 COURT', -1), (0, '±0.000 SITE', 9)]:
        ln((U1 - 19.6, z), (U1 - 18.4, z), 'dim'); tx(U1 - 18.0, z, t, 't sp', anchor='start', dy=dy)
    ln((.5, LV['mast']), (U1 - 19.8, LV['mast']), 'lead'); ln((-R_ROOF, LV['roof_hi']), (U1 - 19.8, LV['roof_hi']), 'lead')
    tx(-14, 21.5, 'MAST THROUGH THE OCULUS\nLIGHT AT THE TOP', 't zl'); tx(0, 7.4, 'TALAM COURT\nØ18 M', 't zl', dy=18); tx(0, 0.1, 'TITIK POOL', 't sm', dy=14)
    tx(-19.5, 7.6, 'CORE 1 · STAIRS + LIFTS', 't zl'); tx(-19.5, 12.8, 'CORE 1 (MEETING BEYOND)', 't zl'); tx(19.5, 8.3, 'ANJUNG\nOPEN TERRACE', 't zl'); tx(17.8, 3.0, 'CAFE', 't zl')
    tx(-6.2, 7.5, 'RING BRIDGES', 't sm'); tx(-15.6, 1.6, 'WALL\nBEYOND', 't mute'); tx(-R_GF - .5, 1.7, 'FREE\nCOLUMN', 't sm', anchor='end')
    tx(8.5, 14.4, 'FUNNEL ROOF', 't sm'); tx(-39.4, 0, 'ROAD', 't mute', dy=-8)
    return f'<svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="Section A-A through the main gate, the court and the north block" style="min-width:900px">' + ''.join(o) + '</svg>'

# ---- data for the 3D model (three.js in the page): metres relative to the centre, x east, y north ----------------
def model_data():
    rel = lambda p: [round(p[0] - C[0], 2), round(p[1] - C[1], 2)]
    def rings(g, tol=0.06):
        out = []
        for q in getattr(g, 'geoms', [g]):
            if q.is_empty or q.geom_type != 'Polygon' or q.area < 0.2: continue
            q = q.simplify(tol)
            out.append([[rel(c) for c in list(q.exterior.coords)[:-1]]] + [[rel(c) for c in list(r.coords)[:-1]] for r in q.interiors])
        return out
    def ztop(a, b, upper):                           # underside of what is above this zone
        qs = [a + (b - a) * i / 24 for i in range(25)]
        return round(min((LV['l2'] - SLAB if (l2_ok(q) and not upper) else roof_h(q) - ROOF_T) for q in qs), 2)
    def zlist(fl, zs, upper=False): return [dict(c=c, p=rings(zone_geom(fl, a, b)), top=ztop(a, b, upper)) for l, c, a, b in zs]
    roof = []
    for p in PETALS:                                   # roof as bearing samples per petal, trimmed to the gate slots
        hw = [math.degrees(math.asin(((s['gap'] - 1.0) / 2) / R_ROOF)) for s in SPINES]; i = NAMES.index(p['name'])
        a0, a1 = p['b0'] + hw[i], p['b0'] + p['span'] - hw[(i + 1) % 4]; n = max(8, round((a1 - a0) / 2.5))
        roof.append([[round(a0 + (a1 - a0) * k / n, 2), round(roof_h(a0 + (a1 - a0) * k / n), 3)] for k in range(n + 1)])
    return dict(R=dict(pool=R_POOL, oculus=R_OCULUS, court=R_COURT, br0=R_BR0, br1=R_BR1, gf=R_GF, l1=R_L1, roof=R_ROOF, roofin=R_ROOF_IN, disc=R_DISC),
                LV=LV, site=rings(SITE), tennis=rings(TENNIS), roads=rings(ROADP) + rings(ROADE), ctx=[dict(p=rings(g), h=h) for _, g, h in CTX],
                spines=[dict(k=s['k'], b=s['b'], w=s['w'], end=rel(spine_end(s['b']).coords[0]), crest=s['crest']) for s in SPINES],
                gf=zlist(GF, ZONES_GF), l1=zlist(L1, ZONES_L1), l2=zlist(L2, ZONES_L2, True), l1plate=rings(L1), l2plate=rings(L2),
                roof=roof, fins=[[round(b, 2), round(a, 1), round(t, 2)] for b, a, t in FINS], fin=[FIN_D, FIN_T],
                cols=dict(out=[[*rel(c), round(roof_h(b) - ROOF_T, 2)] for c, b in COLS_OUT], inn=[[*rel(c), round(roof_h(b) - ROOF_T, 2)] for c, b in COLS_IN], disc=[rel(c) for c, _ in COLS_DISC]),
                layby=rings(LAYBY))

if __name__ == '__main__':
    for nm, s in (('gf', plan('GF')), ('l1', plan('L1')), ('l2', plan('L2')), ('roof', plan('ROOF')), ('ent', entrance()), ('p1', parti('v1')), ('p2', parti('v2')), ('sec', section()),
                  ('unroll', unroll('A')), ('fa', facade('A')), ('fb', facade('B')), ('fc', facade('C'))):
        print(nm, len(s))
    print('model json', len(json.dumps(model_data())))
