"""Interior sheets I-200 (shopfront kit), I-201 (interior sections), I-300 (signage + wayfinding).
Model units in metres; the elevations use x = metres along the front, z = metres above FFL (shop) or above site datum (sections)."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
from cad import Drawing, INK
import plan3 as M
from plan3 import C, P, d, tdir, SC, ROOMS, FFL, CORES
import rings as RG
import sheets as SH
from sheets import new_sheet, drawing_title, wrap, scale_bar
import sheets2 as S2
import interior as IN
from interior import ST, SHOP, SHOP_TXT, tint, BRASS, BRONZE, SIGN, HOST, room, store_r

GLASS = '#DCEBF2'; GREYF = '#BFC4CA'; WHITE = 'white'
def rect(D, x0, y0, x1, y1, layer='A-ELEV', fill=None, edge=INK, lw=0.1, z=3, ls='-', alpha=1.0):
    D.poly(box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), layer, fill=fill, edge=edge, lw=lw, z=z, ls=ls, alpha=alpha)
def dim_h(D, x0, x1, y, txt=None, size=1.5, color='#2C6E7A', tick=0.06):
    D.line([(x0, y), (x1, y)], 'A-DIMS', lw=0.08, color=color)
    for x in (x0, x1): D.line([(x - tick, y - tick), (x + tick, y + tick)], 'A-DIMS', lw=0.15, color=color)
    D.text(((x0 + x1) / 2, y + tick * 1.2), txt or f'{(x1 - x0) * 1000:.0f}', 'A-DIMS', size=size, va='bottom', color=color)
def dim_v(D, y0, y1, x, txt=None, size=1.5, color='#2C6E7A', tick=0.06):
    D.line([(x, y0), (x, y1)], 'A-DIMS', lw=0.08, color=color)
    for y in (y0, y1): D.line([(x - tick, y - tick), (x + tick, y + tick)], 'A-DIMS', lw=0.15, color=color)
    D.text((x - tick * 1.2, (y0 + y1) / 2), txt or f'{(y1 - y0) * 1000:.0f}', 'A-DIMS', size=size, rot=90, va='bottom', color=color)

# ------------------------------------------------------------------------------------------------ state patterns (CAD)
def pattern(D, sk, x0, y0, w, h, col, layer='A-ELEV', z=4):
    """the unique state screen pattern drawn inside the band (x0, y0, w, h); every shape is clipped to the band"""
    B = box(x0, y0, x0 + w, y0 + h)
    def put(g, fill=col, edge=None, lw=0.05):
        g = g.intersection(B)
        if not g.is_empty: D.poly(g, layer, fill=fill, edge=edge, lw=lw, z=z)
    def ln(pts, lw=0.1, color=col):
        g = LineString(pts).intersection(B)
        for q in getattr(g, 'geoms', [g]):
            if q.geom_type == 'LineString' and q.length > 1e-3: D.line(list(q.coords), layer, lw=lw, color=color, z=z)
    rng = np.random.default_rng(11)
    if sk == 'PHG':          # tenun check: weft / warp stripes, every third heavy
        for i, x in enumerate(np.arange(x0 + 0.03, x0 + w, 0.075)): put(box(x, y0, x + (0.025 if i % 3 == 0 else 0.01), y0 + h))
        for i, y in enumerate(np.arange(y0 + 0.03, y0 + h, 0.075)): put(box(x0, y, x0 + w, y + (0.025 if i % 3 == 0 else 0.01)), fill='#2E6E8E')
    elif sk == 'JHR':        # zapin rhythm fins: 1-1-2 step
        x, i = x0 + 0.04, 0
        while x < x0 + w: put(box(x, y0, x + 0.03, y0 + h)); x += (0.07, 0.07, 0.16)[i % 3]; i += 1
    elif sk == 'MLK':        # peranakan flower tile: 4 petals on the diagonals, gold centre, pale leaves between (reads as a flower, not a cross)
        for cx in np.arange(x0 + 0.1, x0 + w, 0.2):
            for cy in np.arange(y0 + 0.1, y0 + h, 0.2):
                for a in (45, 135, 225, 315):
                    e = affinity.scale(Point(0, 0).buffer(0.04, 12), 1.0, 0.55)
                    e = affinity.translate(affinity.rotate(e, a, origin=(0, 0)), cx + 0.038 * math.cos(math.radians(a)), cy + 0.038 * math.sin(math.radians(a)))
                    put(e)
                for a in (0, 90, 180, 270):
                    e = affinity.scale(Point(0, 0).buffer(0.022, 8), 1.0, 0.45)
                    e = affinity.translate(affinity.rotate(e, a, origin=(0, 0)), cx + 0.05 * math.cos(math.radians(a)), cy + 0.05 * math.sin(math.radians(a)))
                    put(e, fill='#7FA35A')
                put(Point(cx, cy).buffer(0.014, 8), fill='#E8B523')
    elif sk == 'NSN':        # gonjong roof profile: sweeping horns
        for cx in np.arange(x0, x0 + w, 0.32):
            xs = np.linspace(cx, cx + 0.32, 24); ys = y0 + 0.08 + (h - 0.12) * (np.abs(np.linspace(-1, 1, 24)) ** 2.6)
            put(Polygon([(cx, y0)] + list(zip(xs, ys)) + [(cx + 0.32, y0)]).buffer(0))
    elif sk == 'SGR':        # firefly dots
        for _ in range(int(w * h * 260)):
            x, y = rng.uniform(x0, x0 + w), rng.uniform(y0, y0 + h); put(Point(x, y).buffer(rng.uniform(0.006, 0.022), 6))
    elif sk == 'PRK':        # karst skyline
        xs = np.linspace(x0, x0 + w, 160); ys = y0 + 0.08 + (h - 0.16) * np.abs(np.sin(xs * 7.1)) ** 0.6 * (0.6 + 0.4 * np.sin(xs * 2.3))
        put(Polygon([(x0, y0)] + list(zip(xs, ys)) + [(x0 + w, y0)]).buffer(0))
    elif sk == 'PNG':        # oval portals
        for cx in np.arange(x0 + 0.12, x0 + w, 0.24):
            e = affinity.scale(Point(cx, y0 + h / 2).buffer(0.08, 16), 1.0, (h * 0.36) / 0.08)
            put(e.difference(e.buffer(-0.018)))
    elif sk == 'KDH':        # padi stalk rows with gold grains
        for cx in np.arange(x0 + 0.03, x0 + w, 0.055):
            ln([(cx, y0 + 0.03), (cx + 0.02, y0 + h - 0.05)], lw=0.12)
            put(affinity.scale(Point(cx + 0.02, y0 + h - 0.08).buffer(0.012, 8), 1.0, 3.0), fill='#D9B24A')
    elif sk == 'KEL':        # wau bulan crescents
        for cx in np.arange(x0 + 0.25, x0 + w, 0.5):
            a = Point(cx, y0 + h * 0.6).buffer(h * 0.45); b_ = Point(cx, y0 + h * 0.75).buffer(h * 0.42)
            put(a.difference(b_))

def back_pattern(D, sk, x0, y0, w, h, col, z=3.5):
    """the feature back wall (store partition) seen from the arcade"""
    B = box(x0, y0, x0 + w, y0 + h)
    def put(g, fill=col, edge=None, lw=0.05):
        g = g.intersection(B)
        if not g.is_empty: D.poly(g, 'A-ELEV', fill=fill, edge=edge, lw=lw, z=z)
    def ln(pts, lw=0.08, color=INK):
        g = LineString(pts).intersection(B)
        for q in getattr(g, 'geoms', [g]):
            if q.geom_type == 'LineString' and q.length > 1e-3: D.line(list(q.coords), 'A-ELEV', lw=lw, color=color, z=z + 0.1)
    put(B, fill=tint(col, 0.75))
    if sk == 'PHG':          # silver ripple shingles
        for j, y in enumerate(np.arange(y0, y0 + h, 0.16)):
            for x in np.arange(x0 - 0.15 * (j % 2), x0 + w + 0.3, 0.3):
                put(Point(x + 0.15, y).buffer(0.15).intersection(box(x, y - 0.15, x + 0.3, y)), fill='#C9D3DA', edge=INK, lw=0.04)
    elif sk == 'JHR':        # deep green glazed tile 200 x 200 (rotated stack)
        put(B, fill='#2F6B3A')
        for x in np.arange(x0, x0 + w, 0.2): ln([(x, y0), (x, y0 + h)], 0.05, '#9BC2A3')
        for y in np.arange(y0, y0 + h, 0.2): ln([(x0, y), (x0 + w, y)], 0.05, '#9BC2A3')
    elif sk == 'MLK':        # Stadthuys red dado + Peranakan tile panel above
        put(box(x0, y0, x0 + w, y0 + 0.9), fill=col)
        pattern(D, 'MLK', x0 + 0.2, y0 + 1.1, w - 0.4, 1.6, col, z=z + 0.2)
    elif sk == 'NSN':        # CNC merbau boards with Minangkabau carving lines
        put(B, fill='#B07A50')
        for x in np.arange(x0, x0 + w, 0.15): ln([(x, y0), (x, y0 + h)], 0.04, '#6E4426')
        for y in np.arange(y0 + 0.5, y0 + h, 0.6):
            for x in np.arange(x0, x0 + w, 0.3): ln([(x, y), (x + 0.15, y + 0.2), (x + 0.3, y)], 0.07, '#4A2C16')
    elif sk == 'SGR':        # mangrove roots in white GRC
        put(B, fill='#F2F5EC')
        for x in np.arange(x0 + 0.2, x0 + w, 0.45):
            for k in (-1, 1):
                ts = np.linspace(0, 1, 20); ln([(x + k * 0.35 * t_, y0 + 1.2 * (1 - t_) ** 0.6 * (1 - (1 - t_) ** 2) + 0.0) for t_ in ts], 0.18, '#7FA35A')
            ln([(x, y0 + 0.9), (x, y0 + h)], 0.25, '#7FA35A')
    elif sk == 'PRK':        # faceted limestone
        put(B, fill='#EEE9E0')
        pts = [(x0 + rng_x, y0 + rng_y) for rng_x in np.linspace(0, w, 7) for rng_y in np.linspace(0, h, 6)]
        for i in range(6):
            for j in range(5):
                a = (x0 + w * i / 6, y0 + h * j / 5); b_ = (x0 + w * (i + 1) / 6, y0 + h * (j + 1) / 5)
                ln([a, b_], 0.05, '#A89A84'); ln([(a[0], b_[1]), (b_[0], a[1])], 0.03, '#C9BCA6')
    elif sk == 'PNG':        # apothecary jar wall: shelves + jars
        for y in np.arange(y0 + 0.4, y0 + h, 0.45):
            ln([(x0 + 0.1, y), (x0 + w - 0.1, y)], 0.12, '#7A5A3A')
            for x in np.arange(x0 + 0.2, x0 + w - 0.15, 0.22): put(box(x, y, x + 0.14, y + 0.26).buffer(0.02), fill=tint(col, 0.4), edge=INK, lw=0.03)
    elif sk == 'KDH':        # stepped sawah bands
        for j, y in enumerate(np.arange(y0, y0 + h, 0.35)):
            put(box(x0, y, x0 + w, y + 0.35), fill=tint(col, 0.15 + 0.12 * (j % 4)))
            ln([(x0, y), (x0 + w, y)], 0.06, '#D9B24A')
    D.poly(B, 'A-ELEV', fill=None, edge=INK, lw=0.15, z=z + 0.3)

# ------------------------------------------------------------------------------------------------ elevations
H_FRONT, H_DOOR, H_FASC = 3.9, 2.7, 3.3
def front_w(key):
    bm, b0, b1 = M.mid(key); return 2 * M.R_BR1 * math.sin(math.radians((b1 - b0) / 2))

def front_elev(D, key, x0, text=True, detail=False):
    sk = SHOP[key]; nm = ST[sk][0]; col = ST[sk][4]; W = front_w(key); hp = 0.05; cw = W - 2 * hp
    fixed = cw - 1.05
    rect(D, x0, H_FRONT, x0 + W, H_FRONT + 0.6, 'A-SLAB', fill=GREYF, edge=INK, lw=0.15)                 # L1 slab over (4.8-5.4)
    for xp in (x0, x0 + W - hp):
        rect(D, xp, 0, xp + hp, H_FRONT, fill='#D7DBDF', lw=0.12)
    for xl in (x0 + hp * 0.5, x0 + W - hp * 0.5): D.line([(xl, 0.1), (xl, H_DOOR)], 'A-ELEV', lw=0.35, color=col, z=5)
    pattern(D, sk, x0 + hp, H_FASC, cw, H_FRONT - H_FASC, col)
    rect(D, x0 + hp, H_FASC, x0 + W - hp, H_FRONT, fill=None, lw=0.12, z=4.5)
    rect(D, x0 + hp, H_DOOR, x0 + W - hp, H_FASC, fill=BRONZE, lw=0.12)
    if text:
        D.text((x0 + W / 2, 3.07), 'KEDAI ' + key, 'A-ELEV', size=2.4 if detail else 1.3, color='white', weight='bold', z=6)
        D.text((x0 + W / 2, 2.85), nm, 'A-ELEV', size=1.6 if detail else 0.9, color=tint(col, 0.25), weight='bold', z=6)
    rect(D, x0 + hp, 0, x0 + hp + fixed, H_DOOR, fill=GLASS, lw=0.1)
    rect(D, x0 + hp + 0.04, 0, x0 + hp + fixed - 0.04, 0.9, fill='#F2EDE4', lw=0.08, z=3.5)              # display case behind
    rect(D, x0 + hp + fixed - 0.05, 0, x0 + W - hp, H_DOOR, fill='#EEF6F9', lw=0.14, z=3.6)              # sliding leaf (closed)
    D.line([(x0 + hp + fixed + 0.1, 0.95), (x0 + hp + fixed + 0.1, 1.65)], 'A-ELEV', lw=0.5, color=col, z=6)   # pull in accent
    D.line([(x0 + hp + fixed + 0.75, 2.1), (x0 + hp + fixed - 0.25, 2.1)], 'A-ELEV', lw=0.08, z=6)
    D.poly(Polygon([(x0 + hp + fixed - 0.25, 2.1), (x0 + hp + fixed - 0.13, 2.14), (x0 + hp + fixed - 0.13, 2.06)]), 'A-ELEV', fill=INK, edge=None, z=6)
    rect(D, x0, -0.03, x0 + W, 0.0, fill=BRASS, edge=None, z=4)                                          # threshold
    rect(D, x0 - 0.04, 2.4, x0, 2.7, fill=col, lw=0.06, z=5)                                              # blade sign seen edge-on
    D.line([(x0 - 0.6, 0), (x0 + W + 0.6, 0)], 'A-ELEV', lw=0.25, z=5)
    return W

def back_elev(D, key, x0):
    sk = SHOP[key]; col = ST[sk][4]; r = room(key); bm, b0, b1 = M.mid(key); rr = store_r(r)
    W = 2 * rr * math.sin(math.radians((b1 - b0) / 2)) - 0.125
    top = 5.3 - FFL['GF']                                                     # up to the opal rooflight of light band 2
    back_pattern(D, sk, x0, 0, W, top, col)
    rect(D, x0 + W / 2 - 0.45, 0, x0 + W / 2 + 0.45, 2.1, fill=None, edge=INK, lw=0.1, ls='--', z=5)   # flush concealed store door
    D.line([(x0, 3.3), (x0 + W, 3.3)], 'A-ELEV', lw=0.08, ls='--', z=5)
    rect(D, x0 - 0.1, top, x0 + W + 0.1, top + 0.08, fill='#E3F0F7', lw=0.08, z=5)
    D.line([(x0 - 0.4, 0), (x0 + W + 0.4, 0)], 'A-ELEV', lw=0.25, z=5)
    return W

# ------------------------------------------------------------------------------------------------ 1:20 kit details (A2-3)
def kit_plan():
    """plan of the A2-3 front at R12.5, rotated so the shop axis points up; x along the front, y = radius - 12.5"""
    D = Drawing('KIT PLAN'); key = 'A2-3'; bm, b0, b1 = M.mid(key); r = room(key)
    def T(p):
        v = np.array(p) - C; a = math.radians(bm)
        x = v[0] * math.cos(a) - v[1] * math.sin(a); y = v[0] * math.sin(a) + v[1] * math.cos(a)
        return (x, y - M.R_BR1)
    W = front_w(key); hp = 0.05; cw = W - 2 * hp; fixed = cw - 1.05; col = ST['MLK'][4]
    # side walls (125, on the room edges) from R12.5 to R14.4
    for b in (b0, b1):
        wl = LineString([T(P(M.R_BR1, b)), T(P(14.4, b))]).buffer(0.0625, cap_style=2)
        D.poly(wl, 'A-WALL', fill=INK, edge=None, z=5)
    xl, xr = T(P(M.R_BR1, b0))[0], T(P(M.R_BR1, b1))[0]
    rect(D, xl + 0.0625, -0.02, xl + 0.0625 + hp, 0.12, 'A-WALL', fill='#D7DBDF', lw=0.1); rect(D, xr - 0.0625 - hp, -0.02, xr - 0.0625, 0.12, 'A-WALL', fill='#D7DBDF', lw=0.1)
    xa = xl + 0.0625 + hp; xb = xr - 0.0625 - hp
    rect(D, xa, 0.03, xa + fixed, 0.045, 'A-GLAZ', fill=GLASS, lw=0.08)                                   # fixed pane
    rect(D, xa + fixed - 0.05, -0.04, xb, -0.025, 'A-GLAZ', fill=GLASS, lw=0.1)                             # leaf, closed (outside the pane)
    rect(D, xa - 0.0, -0.04, xa + 1.05, -0.025, 'A-GLAZ', fill=None, lw=0.06, ls='--')                       # leaf, parked
    D.line([(xb - 1.0, -0.09), (xb, -0.09)], 'A-DIMS', lw=0.06); D.text((xb - 0.5, -0.17), 'SLIDING LEAF 1000 CLEAR', 'A-ANNO', size=1.4)
    rect(D, xa + 0.04, 0.12, xa + fixed - 0.04, 0.66, 'A-FURN', fill='#F2EDE4', lw=0.08)
    D.text((xa + fixed / 2, 0.39), 'DISPLAY CASE 900 H', 'A-ANNO', size=1.3)
    rect(D, xl, -0.33, xr, -0.03, 'A-FLOR', fill=BRASS, edge=None, alpha=0.6)
    D.text(((xl + xr) / 2, -0.24), f"BRASS THRESHOLD: MELAKA · {ST['MLK'][2]}° · {ST['MLK'][3]} KM", 'A-ANNO', size=1.2, color='#5A4410')
    rect(D, xl + 0.06, -0.63, xl + 0.09, -0.03, 'A-ELEV', fill=col, lw=0.06)                                 # blade sign 600 projecting
    D.text((xl - 0.05, -0.5), 'BLADE SIGN\n600 x 300', 'A-ANNO', size=1.2, ha='right')
    D.line([(xa + fixed - 0.4, 0.75), (xa + fixed - 0.4, 1.4)], 'A-ANNO', lw=0.05, ls=':')
    dim_h(D, xl, xr, -0.85, f'{(xr - xl) * 1000:.0f} (WALL TO WALL)')
    dim_h(D, xa, xa + fixed, 0.85, f'{fixed * 1000:.0f} FIXED'); dim_h(D, xa + fixed, xb, 0.85, '1000 CLEAR')
    D.text(((xl + xr) / 2, 1.5), 'SHOP A2-3 (DISPLAY ZONE)', 'A-ANNO', size=1.6, weight='bold')
    D.text(((xl + xr) / 2, -1.2), 'ARCADE (3200 CLEAR, NO FURNITURE)', 'A-ANNO', size=1.6, weight='bold')
    return D

def kit_section():
    """section through the front (x = radius - 12.5, z above FFL)"""
    D = Drawing('KIT SECTION'); col = ST['MLK'][4]
    rect(D, -1.2, -0.3, 1.6, 0.0, 'S-DETL', fill=GREYF, lw=0.15)                                           # GF slab
    rect(D, -1.2, 3.9, 1.6, 4.5, 'S-DETL', fill=GREYF, lw=0.15)                                            # L1 slab zone (4.8-5.4)
    rect(D, -0.012, 0.0, 0.012, 2.7, 'A-GLAZ', fill=GLASS, lw=0.08)                                       # glass
    rect(D, -0.05, 2.7, 0.15, 2.76, 'S-DETL', fill='#8C949C', lw=0.06)                                     # head track
    rect(D, -0.15, 2.76, 0.0, 3.3, 'A-ELEV', fill=BRONZE, lw=0.1)                                          # fascia box, letters backlit
    rect(D, -0.15, 3.3, -0.12, 3.9, 'A-ELEV', fill=tint(col, 0.4), lw=0.08)                                # perforated screen
    for z in (3.45, 3.75): D.circle((-0.06, z), 0.02, 'A-ELEV', fill='#F7D27A', edge=None)                # LED backlight
    rect(D, 0.05, 3.45, 0.35, 3.75, 'A-ELEV', fill='#D0D4D8', lw=0.08)                                     # grille box
    D.line([(0.2, 3.45), (0.2, 2.8)], 'A-ELEV', lw=0.05, ls='--')
    rect(D, 0.0, 3.3, 1.6, 3.32, 'A-ELEV', fill='white', lw=0.08)                                          # shop ceiling +3.300
    rect(D, 0.1, 0.0, 0.65, 0.9, 'A-FURN', fill='#F2EDE4', lw=0.08)                                        # display case
    rect(D, -0.3, -0.02, 0.0, 0.0, 'A-FLOR', fill=BRASS, edge=None)
    rect(D, -0.62, 2.4, -0.15, 2.7, 'A-ELEV', fill=col, lw=0.06)                                           # blade sign (side)
    S2.lead(D, (-0.075, 3.0), (-0.9, 3.25), 'FASCIA: DARK BRONZE ANODISED BOX,\nBACKLIT CUT LETTERS', 'right')
    S2.lead(D, (-0.135, 3.6), (-0.9, 3.75), 'STATE SCREEN: 3 MM PERFORATED\nALUMINIUM, LED BACKLIGHT', 'right')
    S2.lead(D, (0.2, 3.6), (0.7, 4.25), 'ROLL-DOWN PERFORATED GRILLE BOX\n(NIGHT; SCREEN STAYS LIT)')
    S2.lead(D, (0.0, 1.6), (-0.9, 1.6), '12 MM TOUGHENED, FRAMELESS,\nTOP-HUNG SLIDING LEAF', 'right')
    S2.lead(D, (0.4, 0.6), (0.9, 1.2), 'DISPLAY CASE 900 H')
    S2.lead(D, (-0.4, 2.55), (-0.9, 2.2), 'BLADE SIGN, U/S 2400', 'right')
    S2.lead(D, (-0.15, -0.01), (-0.9, 0.5), 'BRASS THRESHOLD IN TERRAZZO', 'right')
    S2.lead(D, (1.0, 3.31), (1.2, 2.9), 'SHOP CEILING +3.300 (FFL)')
    dim_v(D, 0.0, 2.7, 1.45); dim_v(D, 2.7, 3.3, 1.45); dim_v(D, 3.3, 3.9, 1.45)
    D.text((-0.6, -0.6), 'ARCADE', 'A-ANNO', size=1.6, weight='bold'); D.text((0.8, -0.6), 'SHOP', 'A-ANNO', size=1.6, weight='bold')
    return D

# ------------------------------------------------------------------------------------------------ I-200
def shopfront_sheet(no='I-200'):
    title = 'SHOPFRONT KIT · EIGHT STATE SHOPFRONTS'
    S, F, x0, y = new_sheet(no, title, '1:50 · 1:20 @ A0')
    side = Drawing('side', paper=True)
    order = ['A2-1', 'A2-2', 'A2-3', 'A2-4', 'A1-1', 'A1-2', 'A1-3', 'A1-4']
    E = Drawing('FRONTS'); Bk = Drawing('BACK WALLS')
    slot = 5.4; xs = []
    for i, k in enumerate(order):
        x = i * slot + (0.6 if i >= 4 else 0); xs.append(x)
        w = front_elev(E, k, x)
        sk = SHOP[k]
        E.text((x + w / 2, -0.55), f'{k} · {ST[sk][0]}', 'A-ANNO', size=2.0, weight='bold')
        E.text((x + w / 2, -0.95), wrap(SHOP_TXT[k][0], 26), 'A-ANNO', size=1.35, va='top', color='#55606A')
        E.text((x + w / 2, -1.85), 'SCREEN: ' + wrap(SHOP_TXT[k][1], 22), 'A-ANNO', size=1.35, va='top', color=ST[sk][4] if sk not in ('JHR', 'SGR', 'PRK') else '#6B5A1C', weight='bold')
        dim_h(E, x, x + w, 4.75, size=1.4)
        wb = back_elev(Bk, k, x)
        Bk.text((x + wb / 2, -0.55), f'{k} BACK WALL', 'A-ANNO', size=1.8, weight='bold')
        Bk.text((x + wb / 2, -0.95), wrap(SHOP_TXT[k][2] + ' · SIGNATURE: ' + SHOP_TXT[k][3], 28), 'A-ANNO', size=1.3, va='top', color='#55606A')
    for z, t in ((0, '±0 FFL +0.900'), (2.7, '2700 DOOR HEAD'), (3.3, '3300 SHOP CEILING'), (3.9, '3900 ARCADE SOFFIT (+4.800)')):
        E.line([(-0.5, z), (-0.15, z)], 'A-DIMS', lw=0.08); E.text((-0.6, z), t, 'A-DIMS', size=1.4, ha='right')
    E.text((-0.6, 3.6), 'STATE SCREEN (UNIQUE)', 'A-ANNO', size=1.5, ha='right', color='#B83A2E', weight='bold')
    E.text((-0.6, 3.0), 'FASCIA SIGN BAND', 'A-ANNO', size=1.5, ha='right')
    E.text((-0.6, 1.4), 'GLASS: FIXED PANE\n+ SLIDING LEAF', 'A-ANNO', size=1.5, ha='right')
    S.place(E, 50, (0, 0), (110, 640))
    drawing_title(side, (40, 800), '1', 'SHOPFRONTS AS SEEN FROM THE ARCADE (CHORD AT R12.5, TRUE WIDTH)', 50, 'A2 KUIH + SNACKS · A1 COOKING INGREDIENTS')
    S.place(Bk, 50, (0, 0), (110, 450))
    drawing_title(side, (40, 575), '2', 'FEATURE BACK WALLS (STORE PARTITION, LIT BY ROOFLIGHT BAND 2)', 50, 'SEEN FROM THE SHOP DOOR · STORE DOOR FLUSH + CONCEALED')
    K = Drawing('KIT ELEV'); front_elev(K, 'A2-3', 0.0, detail=True)
    W = front_w('A2-3'); hp = 0.05; fixed = W - 2 * hp - 1.05
    dim_h(K, 0, W, -0.35); dim_h(K, 0, hp, 4.6, '50'); dim_h(K, hp, hp + fixed, 4.6); dim_h(K, hp + fixed, W - hp, 4.6, '1000 CLEAR + 50')
    dim_v(K, 0, 2.7, W + 0.25); dim_v(K, 2.7, 3.3, W + 0.25); dim_v(K, 3.3, 3.9, W + 0.25)
    S.place(K, 20, (0, 0), (70, 120))
    drawing_title(side, (40, 75), '3', 'KIT ELEVATION · SHOP A2-3 (MELAKA)', 20)
    S.place(kit_plan(), 20, (0.0, 0.0), (380, 250))
    drawing_title(side, (300, 75), '4', 'KIT PLAN AT THE FRONT · A2-3', 20)
    S.place(kit_section(), 20, (0.0, 0.0), (760, 120))
    drawing_title(side, (620, 75), '5', 'KIT SECTION THROUGH THE FRONT', 20)
    S2.finish(S, F, side, no, title, '1:50 · 1:20', None, [
        'ONE KIT FOR ALL EIGHT SHOPS: HALF-PIERS, GLASS, SLIDING LEAF, FASCIA, LIGHT TRACK, GRILLE, SIGNS AND FLOOR ARE THE SAME. ONLY FOUR THINGS CHANGE PER STATE: THE SCREEN PATTERN, THE ACCENT COLOUR, THE FEATURE BACK WALL AND THE SIGNATURE DISPLAY.',
        'DOOR TYPE SF1 (A-600): 1000 CLEAR FRAMELESS SLIDING LEAF IN FRONT OF THE FIXED DISPLAY PANE. REPLACES THE SF 1800 OF REV 00, WHICH DID NOT FIT THE 2.1 M CLEAR FRONT.',
        'FRONT WIDTHS ARE THE CHORD AT R12.5 BETWEEN WALL CENTRES: A2-1 TO A2-3 2300, A2-4 2450, A1 2550.',
        'PRODUCT RANGES ARE SUGGESTIONS FOR THE TENANT; THE BRIEF FIXES ONLY THE TRADE (A2 KUIH + SNACKS, A1 COOKING INGREDIENTS).',
        'STATE COLOURS = CRIT 1 PALETTE. NO STATE CRESTS OR FLAGS ARE USED.'], y, x0)
    return S, [(E, (0, 0)), (Bk, (0, -8)), (K, (0, -16)), (kit_plan(), (8, -16)), (kit_section(), (14, -16))]

# ------------------------------------------------------------------------------------------------ I-201 interior sections
def person(D, x, z, h=1.65, color='#55606A'):
    D.circle((x, z + h - 0.11), 0.11, 'A-ANNO', fill=None, edge=color, lw=0.09)
    D.line([(x, z + 0.85), (x, z + h - 0.22)], 'A-ANNO', lw=0.12, color=color)
    D.line([(x - 0.15, z), (x, z + 0.85), (x + 0.15, z)], 'A-ANNO', lw=0.12, color=color)
    D.line([(x - 0.2, z + 1.2), (x, z + 1.35), (x + 0.2, z + 1.2)], 'A-ANNO', lw=0.1, color=color)

def interior_section(b, shop, l1, l2):
    """1:50 radial section at bearing b (x = radius, z = level): structure as detail 9 (A-501) + the interior"""
    D = Drawing(f'INT SECTION {b}'); H = GREYF; G = '#BFD9E6'; Pb = lambda r: P(r, b)
    sk = SHOP[shop]; col = ST[sk][4]
    D.line([(7.0, 0.9), (29.5, 0.9)], 'A-SITE', lw=0.35); D.poly(box(7.0, 0.0, 29.5, 0.9), 'A-SITE', fill='#E9E5DC', edge=None, z=1)
    # court edge: talam bench + pocket garden, arcade floor with the river terrazzo + tactile path
    D.poly(box(7.85, 0.9, 8.3, 1.35), 'A-FURN', fill='#F4F1EA', edge=INK, lw=0.08); D.poly(box(8.3, 0.9, 9.3, 1.45), 'L-PLNT', fill='#DDE8D3', edge='#3E7D3A', lw=0.1)
    D.poly(box(11.6, 0.9, 11.9, 0.92), 'A-TACT', fill='#E3B505', edge=None)
    # columns
    for rc in (11.0, 15.5, 18.5, 23.0): D.poly(box(rc - 0.175, 0.9, rc + 0.175, 4.8 if rc != 18.5 else 4.7), 'S-DETL', fill=H, edge=INK, lw=0.12)
    # slabs
    D.poly(box(9.5, 4.8, 15.5, 5.4), 'S-DETL', fill=H, edge=INK, lw=0.18)
    D.poly(box(17.0, 5.05, 20.0, 5.4), 'S-DETL', fill=H, edge=INK, lw=0.18); D.poly(box(18.1, 4.7, 18.9, 5.05), 'S-DETL', fill=H, edge=INK, lw=0.18)
    D.poly(box(21.5, 4.8, 26.5, 5.4), 'S-DETL', fill=H, edge=INK, lw=0.18)
    D.poly(box(9.5, 9.0, 15.5, 9.6), 'S-DETL', fill=H, edge=INK, lw=0.18)
    for x0, x1 in ((15.5, 16.95), (20.05, 21.5)): D.poly(box(x0, 5.27, x1, 5.37), 'A-GLAZ', fill='#E3F0F7', edge=INK, lw=0.08)
    for xb in (9.55, 15.45, 17.05, 19.95, 21.55): D.poly(box(xb - 0.01, 5.4, xb + 0.01, 6.5), 'A-GLAZ', fill=G, edge=INK, lw=0.06)
    D.line([(17.05, 6.5), (19.95, 6.5)], 'A-HIDN', lw=0.05, ls=':')
    for xb in (17.07, 19.93): D.circle((xb, 6.45), 0.03, 'A-ELEV', fill='#8C5A2B', edge=None)                 # chengal handrail + LED
    zt_ = RG.out_under(Pb(26.0))
    D.poly(box(26.44, 5.4, 26.5, zt_), 'A-GLAZ', fill=G, edge=INK, lw=0.08)
    D.poly(box(9.55 - 0.01, 9.6, 9.55 + 0.01, 10.7), 'A-GLAZ', fill=G, edge=INK, lw=0.06)
    for rp in M.POST_R: D.poly(box(rp - 0.075, 5.4, rp + 0.075, RG.mid_under(Pb(rp))), 'S-DETL', fill='#8C949C', edge=INK, lw=0.08)
    def tier(r0, r1, top, und, fill):
        rs = np.linspace(r0, r1, 40)
        D.poly(Polygon([(r, top(Pb(r))) for r in rs] + [(r, und(Pb(r))) for r in rs[::-1]]), 'A-ROOF', fill=fill, edge=INK, lw=0.18)
    tier(7.0, RG.R_FUN, RG.fun_top, RG.fun_under, '#E6E8EB'); tier(RG.T_MID[0], RG.T_MID[1], RG.mid_top, RG.mid_under, '#D4D8DD'); tier(RG.T_OUT[0], 28.3, RG.out_top, RG.out_under, '#C4CAD0')
    for rr_, lo, hi in ((16.25, RG.mid_top, RG.fun_under), (20.9, RG.out_top, RG.mid_under)):
        D.poly(box(rr_ - 0.03, lo(Pb(rr_)), rr_ + 0.03, hi(Pb(rr_))), 'A-GLAZ', fill=G, edge=INK, lw=0.06)
    # tenun aluminium lining under the funnel (dotted line 120 below the underside)
    rs = np.linspace(7.0, 15.3, 60); D.line([(r, RG.fun_under(Pb(r)) - 0.12) for r in rs], 'A-ELEV', lw=0.25, color='#2E6E8E', ls=':')
    S2.lead(D, (8.0, RG.fun_under(Pb(8.0)) - 0.12), (7.2, RG.fun_under(Pb(8.0)) - 1.2), 'TENUN PAHANG LINING\n(PERFORATED ALUMINIUM)', 'left')
    for xx in np.arange(9.65, 12.4, 0.3): D.poly(box(xx, 4.62, xx + 0.03, 4.8), 'A-ELEV', fill='white', edge=INK, lw=0.04)   # arcade baffles
    S2.lead(D, (10.9, 4.65), (8.4, 4.0), 'WHITE ALUMINIUM\nRADIAL BAFFLES', 'right')
    # ---------------- GF shop
    rr = store_r(room(shop))
    D.poly(box(12.44, 0.9, 12.56, 3.6), 'A-GLAZ', fill=G, edge=INK, lw=0.08)
    D.poly(box(12.35, 3.6, 12.5, 4.2), 'A-ELEV', fill=BRONZE, edge=INK, lw=0.06); D.poly(box(12.35, 4.2, 12.38, 4.8), 'A-ELEV', fill=tint(col, 0.35), edge=INK, lw=0.06)
    D.poly(box(11.9, 3.3, 12.35, 3.6), 'A-ELEV', fill=col, edge=INK, lw=0.05)
    for a, c in ((12.5, 15.5), (17.0, 20.0)): D.line([(a, 4.2), (c, 4.2)], 'A-ELEV', lw=0.12)
    for a, c in ((15.5, 17.0), (20.0, min(21.5, rr))): D.line([(a, 4.2), (a, 5.27)], 'A-ELEV', lw=0.06, ls='--')
    D.poly(box(rr - 0.06, 0.9, rr + 0.06, 5.27), 'A-ELEV', fill=col, edge=INK, lw=0.08)                    # feature back wall, full height
    D.line([(rr + 0.06, 4.2), (23.0, 4.2)], 'A-ELEV', lw=0.12)
    D.poly(box(22.95, 0.9, 23.05, 4.8), 'A-GLAZ', fill=G, edge=INK, lw=0.06)
    D.poly(box(12.6, 0.9, 13.2, 1.8), 'A-FURN', fill='#F2EDE4', edge=INK, lw=0.06)
    for zz in (1.5, 2.0, 2.5): D.line([(13.3, zz), (15.2, zz)], 'A-FURN', lw=0.06)
    D.poly(box(15.75, 0.9, 16.75, 1.75), 'A-FURN', fill=tint(col, 0.5), edge=INK, lw=0.06)
    D.poly(box(18.6, 0.9, 21.0, 1.8), 'A-FURN', fill='#F2EDE4', edge=INK, lw=0.06)
    for xx in np.linspace(15.6, 16.9, 4): D.line([(xx, 5.2), (xx, 2.1)], 'A-ANNO', lw=0.06, color='#E0A100')
    for xx in np.linspace(20.1, 21.0, 3): D.line([(xx, 5.2), (xx, 2.1)], 'A-ANNO', lw=0.06, color='#E0A100')
    person(D, 10.4, 0.9); person(D, 14.2, 0.9); person(D, 19.8, 0.9)
    S2.lead(D, (12.4, 4.5), (11.0, 3.4), f'STATE SCREEN · {ST[sk][0]}', 'right')
    S2.lead(D, (rr, 3.0), (rr + 1.0, 2.6), 'FEATURE BACK WALL\n(FULL HEIGHT TO THE ROOFLIGHT)')
    S2.lead(D, (16.25, 1.75), (16.6, 3.0), 'SIGNATURE DISPLAY\nUNDER LIGHT BAND 1')
    D.text((17.8, 3.7), f'SHOP {shop} · {ST[sk][0]}', 'A-ANNO', size=2.0, weight='bold')
    D.text((10.4, 3.9), 'ARCADE', 'A-ANNO', size=1.8, weight='bold')
    # ---------------- L1
    l1(D, b); l2(D, b)
    # levels
    for z, t in ((0.9, '+0.900 GF'), (5.4, '+5.400 L1 · BRIDGE'), (9.6, '+9.600 L2')):
        D.line([(28.9, z), (29.5, z)], 'A-DIMS', lw=0.1); D.text((29.6, z), t, 'A-DIMS', size=1.6, ha='left', weight='bold')
    for lab, R in (('A', 9.5), ('B', 11.0), ('C', 15.5), ('D', 18.5), ('E', 23.0), ('F', 26.5)):
        D.line([(R, -0.5), (R, 0.0)], 'A-GRID', lw=0.06, color='#7A8590', ls='-.'); D.circle((R, -0.85), 0.32, 'A-GRID', fill='white', edge='#7A8590', lw=0.1); D.text((R, -0.85), lab, 'A-GRID', size=1.4, color='#5B6570')
    return D

def l1_balcony_bridge_deck(D, b, inner='ledge'):
    # inner ring: balcony ledge (inner deck) or room
    if inner == 'ledge':
        D.poly(box(11.2, 5.4, 11.55, 6.5), 'A-FURN', fill='white', edge=INK, lw=0.06); D.circle((11.85, 6.1), 0.17, 'A-FURN', fill='white', edge=INK, lw=0.06)
        D.line([(11.85, 5.4), (11.85, 5.93)], 'A-FURN', lw=0.06)
        person(D, 12.2, 5.4); D.text((13.4, 7.6), 'ANJUNG TALAM\nLEDGE + STOOLS', 'A-ANNO', size=1.6, weight='bold')
        D.poly(box(14.0, 5.4, 15.25, 5.9), 'L-PLNT', fill='#DDE8D3', edge='#3E7D3A', lw=0.08)
    # bridge: brass state line seen in the floor + person
    D.poly(box(17.0, 5.4, 20.0, 5.42), 'A-FLOR', fill=BRASS, edge=None)
    person(D, 18.5, 5.4); D.text((18.5, 7.6), 'JAMBATAN SIMPUL\n11 BRASS STATE LINES', 'A-ANNO', size=1.6, weight='bold')
    # outer deck: gerai lipat (market days) + fin walk
    D.poly(box(21.6, 5.4, 23.6, 5.45), 'A-FURN', fill='#FBF4E4', edge=None)
    for xx in (21.65, 23.55): D.line([(xx, 5.4), (xx, 7.6)], 'A-FURN', lw=0.08, ls='--')
    D.poly(Polygon([(21.5, 7.6), (23.7, 7.6), (22.6, 8.0)]), 'A-FURN', fill=tint('#6FB3D2', 0.6), edge=INK, lw=0.06, ls='--')
    D.poly(box(22.3, 5.4, 23.5, 6.3), 'A-FURN', fill='white', edge=INK, lw=0.06, ls='--')
    person(D, 24.3, 5.4); person(D, 25.7, 5.4)
    D.text((23.9, 8.6), 'DEK PEKAN SEHARI\nGERAI LIPAT (MARKET DAYS)', 'A-ANNO', size=1.6, weight='bold')

def l1_a23(D, b): l1_balcony_bridge_deck(D, b, 'ledge')
def l1_a13(D, b):
    # meeting room L26: glass both sides with frosted band, curved table + chairs
    D.poly(box(10.97, 5.4, 11.03, 9.0), 'A-GLAZ', fill='#BFD9E6', edge=INK, lw=0.06)
    D.poly(box(10.97, 6.4, 11.03, 7.0), 'A-GLAZ', fill='#EEF2F4', edge=INK, lw=0.05)
    D.line([(11.0, 8.4), (15.5, 8.4)], 'A-ELEV', lw=0.1)
    D.poly(box(15.44, 5.4, 15.5, 9.0), 'A-GLAZ', fill='#BFD9E6', edge=INK, lw=0.06)
    D.poly(box(12.7, 6.08, 13.8, 6.15), 'A-FURN', fill='white', edge=INK, lw=0.08); D.line([(13.25, 5.4), (13.25, 6.08)], 'A-FURN', lw=0.08)
    for xx in (12.25, 14.25): D.circle((xx, 5.85), 0.2, 'A-FURN', fill='white', edge=INK, lw=0.06)
    person(D, 14.6, 5.4); D.text((13.25, 7.6), 'MEETING ROOM L26', 'A-ANNO', size=1.6, weight='bold')
    S2.lead(D, (11.0, 6.7), (9.8, 7.4), 'FROSTED BAND\n1000-1600', 'right')
    l1_balcony_bridge_deck(D, b, 'room')

def l2_gallery(D, b):
    D.poly(box(10.97, 9.6, 11.03, RG.fun_under(P(11.0, b))), 'A-GLAZ', fill='#BFD9E6', edge=INK, lw=0.06)
    D.poly(box(15.44, 9.6, 15.5, RG.fun_under(P(15.5, b))), 'A-GLAZ', fill='#BFD9E6', edge=INK, lw=0.06)
    D.line([(11.0, 12.6), (15.5, 12.6)], 'A-ELEV', lw=0.1, ls='--')
    D.poly(box(14.55, 9.6, 14.8, 12.0), 'A-FURN', fill=tint(IN.GAL, 0.3), edge=INK, lw=0.08)
    D.poly(box(14.3, 10.5, 14.55, 10.9), 'A-FURN', fill='white', edge=INK, lw=0.05)
    D.poly(box(12.2, 9.6, 12.8, 10.1), 'A-FURN', fill='white', edge=INK, lw=0.06)
    for zz in np.linspace(12.3, 12.55, 3): D.circle((13.0 + (zz - 12.3) * 4, zz), 0.04, 'A-ELEV', fill='#F7D27A', edge=None)
    person(D, 13.6, 9.6)
    S2.lead(D, (14.67, 11.2), (16.4, 11.6), 'PETA RASA MAP WALL (GRC RELIEF)\n+ SHOWCASES · UV FILM ON GLASS')
    D.text((12.7, 11.2), 'GALERI\nPETA RASA', 'A-ANNO', size=1.6, weight='bold')

def l2_prayer(D, b):
    D.poly(box(10.97, 9.6, 11.03, 12.6), 'S-DETL', fill=GREYF, edge=INK, lw=0.06)
    zt = RG.fun_under(P(15.5, b))
    D.poly(box(15.44, 9.6, 15.5, zt), 'A-GLAZ', fill='#BFD9E6', edge=INK, lw=0.06)
    D.poly(box(15.3, 9.6, 15.36, zt - 0.3), 'A-ELEV', fill=tint(IN.PRAY, 0.3), edge=INK, lw=0.06)
    for zz in np.arange(9.9, zt - 0.4, 0.3): D.line([(15.28, zz), (15.38, zz + 0.15)], 'A-ELEV', lw=0.04)
    D.line([(11.0, 12.6), (15.3, 12.6)], 'A-ELEV', lw=0.1, ls='--')
    D.poly(box(11.0, 9.6, 15.3, 9.63), 'A-FLOR', fill='#C7B27A', edge=None)
    person(D, 13.0, 9.6, 1.65); person(D, 14.2, 9.6, 1.65)
    S2.lead(D, (15.33, 11.0), (16.4, 11.6), 'GIRIH SCREEN ON THE QIBLA GLASS\n(PERFORATED, 8-POINT STAR)')
    D.text((12.5, 11.4), 'SURAU LELAKI M10', 'A-ANNO', size=1.6, weight='bold')

SEC_CALLOUTS = [('FLOORS', 'COURT, ARCADE, BRIDGE, DECKS: GREY TERRAZZO WITH RIVER-PEBBLE AGGREGATE (HONED, R11 OUTSIDE), BRASS INLAYS. SHOPS: TERRAZZO TILE. SURAU: CARPET WITH SHAF LINES.'),
                ('CEILINGS', 'SHOPS: GYPSUM AT +3.300 FFL, OPEN TO THE TWO OPAL ROOFLIGHT BANDS. ARCADE: WHITE ALUMINIUM RADIAL BAFFLES. FUNNEL: PERFORATED ALUMINIUM TENUN LINING.'),
                ('WALLS', 'WHITE GRC / GRG CURVES; STATE FEATURE BACK WALL IN EACH SHOP (I-200); GIRIH SCREEN ON THE SURAU QIBLA GLASS; PETA RASA MAP WALL IN THE GALLERY.'),
                ('EDGES', '1100 LAMINATED GLASS BALUSTRADE ON EVERY GAP EDGE, CHENGAL HANDRAIL WITH LED UNDER. OPAL ROOFLIGHTS ARE MAINTENANCE ONLY.'),
                ('LIGHT', 'DAYLIGHT FROM THE OCULUS, THE CLERESTORIES AND THE ROOFLIGHT BANDS; 3000 K LED IN PUBLIC AND FOOD SPACES, 4000 K IN OFFICES (SEE I-100 TO I-102).')]
SEC_DEF = {'I-201': ('A2-3', l1_a23, l2_gallery, 'SHOP A2-3 MELAKA · ANJUNG TALAM · BRIDGE · DEK PEKAN SEHARI · GALERI PETA RASA'),
           'I-202': ('A1-3', l1_a13, l2_prayer, 'SHOP A1-3 PULAU PINANG · MEETING ROOM · BRIDGE · DEK PEKAN SEHARI · SURAU LELAKI')}
def sections_sheet(no='I-201'):
    shop, f1, f2, sub = SEC_DEF[no]
    b = M.mid(shop)[0]
    title = f'INTERIOR SECTION {"1" if no == "I-201" else "2"} · RADIAL AT {b:.1f}°'
    S, F, x0, y = new_sheet(no, title, '1:50 @ A0')
    side = Drawing('side', paper=True)
    D1 = interior_section(b, shop, f1, f2)
    S.place(D1, 50, (7.0, 0.0), (60, 110), clip=(22, 12, 1022, 829))
    drawing_title(side, (40, 50), '1', f'RADIAL SECTION AT {b:.1f}°', 50, sub)
    # key plan: GF interior plan at 1:300 with the cut line
    import plans
    K = plans.plan_drawing('GF', 'base')
    K.line([P(7.0, b), P(29.5, b)], 'A-ANNO', lw=0.5, color=SIGN, z=10)
    for rr in (7.0, 29.5): K.circle(P(rr, b), 0.9, 'A-ANNO', fill=SIGN, edge=None, z=10)
    S.place(K, 300, tuple(C), (850, 640), clip=(700, 500, 1000, 800))
    drawing_title(side, (700, 480), '2', 'KEY PLAN · GROUND FLOOR · CUT LINE', 300)
    yy = 430
    side.text((640, yy), 'INTERIOR CALLOUTS', 'X-TITL', size=2.6, ha='left', va='top', weight='bold'); yy -= 7
    for k_, t in SEC_CALLOUTS:
        side.text((640, yy), k_, 'X-TITL', size=2.0, ha='left', va='top', weight='bold')
        w = wrap(t, 62); side.text((672, yy), w, 'X-TITL', size=1.9, ha='left', va='top'); yy -= 2.6 * (w.count('\n') + 1) + 4
    S2.finish(S, F, side, no, title, '1:50', None, [
        'X = RADIUS FROM CENTRE C, Z = LEVEL ABOVE SITE DATUM. STRUCTURE AS A-501 DETAIL 9.',
        'EACH SHOP HAS FOUR ZONES UNDER TWO DAYLIGHT BANDS: DISPLAY (R12.5-15.5), LIGHT BAND 1 WITH THE SIGNATURE DISPLAY (R15.5-17), PREP + CASHIER UNDER THE BRIDGE, LIGHT BAND 2 ON THE FEATURE BACK WALL.',
        'NO FURNITURE ON THE BRIDGE, WALKWAYS, GALLERY WALK OR FIN WALK (ESCAPE ROUTES). THE GERAI LIPAT STAND ONLY ON MARKET DAYS AND KEEP A 1400 AISLE + THE 1500 FIN WALK.'], y, x0)
    return S, [(D1, (0, 0))]

# ------------------------------------------------------------------------------------------------ I-300 signage
def heads_up_map(D, cx, cy, s, rot, here_b, fl='GF'):
    a = math.radians(rot)
    def T(p):
        v = (np.array(p) - C) * s; return (cx + v[0] * math.cos(a) - v[1] * math.sin(a), cy + v[0] * math.sin(a) + v[1] * math.cos(a))
    D.circle((cx, cy), 27.5 * s, 'A-SIGN', fill='#4A403B', edge=None, z=4)
    for r in ROOMS:
        if r['fl'] != fl: continue
        fc = '#8A949C' if r['kind'] in ('stair', 'lift') else IN.theme_fill(r)
        D.poly(Polygon([T(c) for c in r['poly'].exterior.coords]), 'A-SIGN', fill=fc, edge='#3B3330', lw=0.03, z=5)
    D.circle((cx, cy), M.R_COURT * s, 'A-SIGN', fill='#DCEFF6', edge=None, z=5)
    for sp in SC.SPINES: D.text(T(P(25.0, sp['b'])), sp['k'], 'A-SIGN', size=0.9, color='white', weight='bold', z=7)
    h = T(P(16.0, here_b)); D.circle(h, 0.018, 'A-SIGN', fill='#E4572E', edge='white', lw=0.05, z=8)

def signage_drawing():
    """all signs at 1:20 (model metres), laid out left to right"""
    D = Drawing('SIGNS'); D2 = Drawing('SIGNS 2'); R1 = D
    # 1 gate marker on the canopy beam (6.0 x 0.9 band), drawn with its underside at 1.3 so it sits beside the totems
    x = 0.0
    rect(D, x, 1.3, x + 6.0, 2.2, 'A-SIGN', fill='#E9ECEF', lw=0.1)
    D.text((x + 3.0, 1.8), 'SELATAN', 'A-SIGN', size=14, color=BRONZE, weight='bold')
    D.text((x + 3.0, 1.42), 'PINTU SELATAN · SOUTH GATE (MAIN)', 'A-SIGN', size=2.6, color=BRONZE)
    for i, sk in enumerate(('NSN', 'MLK', 'JHR')): rect(D, x + i * 2.0, 1.16, x + (i + 1) * 2.0, 1.28, 'A-SIGN', fill=ST[sk][4], edge=None)
    for i, sk in enumerate(('NSN', 'MLK', 'JHR')): D.text((x + i * 2.0 + 1.0, 0.92), ST[sk][0], 'A-SIGN', size=2.0, weight='bold')
    dim_h(D, x, x + 6.0, 2.4, '6000 (TYPICAL; LENGTH TO SUIT CANOPY BEAM)', size=1.8); dim_v(D, 1.3, 2.2, x + 6.3, '900', size=1.8); dim_v(D, 1.6, 2.15, x - 0.2, '600 LETTERS', size=1.5)
    D.text((x + 3.0, 0.5), '1 · GATE MARKER (x4)\nCUT ALUMINIUM LETTERS, DARK BRONZE, HALO-LIT\nON THE CANOPY BEAM AT THE STREET END', 'A-ANNO', size=2.2, va='top', weight='bold')
    # 2 totems (x4) with heads-up maps
    for i, sp in enumerate(SC.SPINES):
        tx = 7.2 + i * 1.0
        rect(D, tx, 0.0, tx + 0.6, 2.2, 'A-SIGN', fill=BRONZE, lw=0.1)
        D.text((tx + 0.3, 2.08), sp['k'], 'A-SIGN', size=2.0, color='white', weight='bold')
        D.text((tx + 0.3, 1.98), 'DIREKTORI · DIRECTORY', 'A-SIGN', size=0.9, color='#D9C6A0')
        heads_up_map(D, tx + 0.3, 1.62, 0.0095, sp['b'] - 180, sp['b'])
        D.text((tx + 0.3, 1.3), 'ANDA DI SINI\nYOU ARE HERE', 'A-SIGN', size=0.8, color='white')
        for j in range(10): D.line([(tx + 0.07, 1.12 - j * 0.07), (tx + 0.53, 1.12 - j * 0.07)], 'A-SIGN', lw=0.06, color='#8B8079')
        D.text((tx + 0.3, 0.3), 'ARAS G · 1 · 2', 'A-SIGN', size=1.0, color='white')
    dim_v(D, 0, 2.2, 7.0, '2200', size=1.6); dim_h(D, 7.2, 7.8, 2.35, '600', size=1.6)
    D.text((8.9, -0.25), '2 · DIRECTORY TOTEM (x4 GATES + 1 AT KAUNTER INFO)\nPOWDER-COATED STEEL, 600 x 120 x 2200, ROUND PLAN OF G / 1 / 2\nHEADS-UP: EACH TOTEM TURNS THE PLAN SO ITS OWN GATE IS AT THE BOTTOM', 'A-ANNO', size=2.2, va='top', weight='bold')
    D = D2
    # 3 level sign
    x = 0.0
    rect(D, x, 0.6, x + 1.2, 2.2, 'A-SIGN', fill='white', lw=0.1)
    D.text((x + 0.6, 1.62), '2', 'A-SIGN', size=40, color=BRONZE, weight='bold')
    D.text((x + 0.6, 0.98), 'ARAS 2 · LEVEL 2', 'A-SIGN', size=2.2, color=BRONZE, weight='bold')
    D.text((x + 0.6, 0.78), 'GALERI · SURAU · SERAMBI KELUARGA', 'A-SIGN', size=1.2, color=BRONZE)
    dim_h(D, x, x + 1.2, 2.35, '1200', size=1.6); dim_v(D, 0.6, 2.2, x + 1.4, '1600', size=1.6); dim_v(D, 0.0, 0.6, x + 1.4, '600', size=1.4)
    D.line([(x - 0.2, 0), (x + 1.6, 0)], 'A-ELEV', lw=0.2)
    D.text((x + 0.6, -0.25), '3 · LEVEL SIGN (x12)\nON THE CORE WALL BESIDE\nEVERY LIFT AND STAIR DOOR', 'A-ANNO', size=2.2, va='top', weight='bold')
    # 5 blade sign
    x = 2.6
    rect(D, x, 2.4, x + 0.6, 2.7, 'A-SIGN', fill='white', lw=0.1); rect(D, x, 2.4, x + 0.04, 2.7, 'A-SIGN', fill=ST['MLK'][4], edge=None)
    pattern(D, 'MLK', x + 0.06, 2.42, 0.2, 0.26, ST['MLK'][4], 'A-SIGN', z=5)
    D.text((x + 0.42, 2.55), 'A2-3', 'A-SIGN', size=2.4, color=BRONZE, weight='bold')
    D.line([(x - 0.05, 2.7), (x - 0.05, 3.3)], 'A-ELEV', lw=0.2); D.line([(x - 0.05, 2.7), (x + 0.6, 2.7)], 'A-ELEV', lw=0.06, ls='--')
    dim_h(D, x, x + 0.6, 2.85, '600', size=1.6); dim_v(D, 2.4, 2.7, x + 0.75, '300', size=1.4); dim_v(D, 0, 2.4, x + 0.75, '2400 MIN CLEAR', size=1.4)
    D.line([(x - 0.3, 0), (x + 0.9, 0)], 'A-ELEV', lw=0.2)
    D.text((x + 0.3, -0.25), '5 · BLADE SIGN (x9)\nDOUBLE-SIDED, MOTIF\nICON + UNIT NO.', 'A-ANNO', size=2.2, va='top', weight='bold')
    # 6 room plate on a door (plate 300 x 150, centre 1500)
    x = 4.8
    rect(D, x, 0, x + 1.0, 2.1, 'A-ELEV', fill='#F4F1EA', lw=0.1); D.circle((x + 0.88, 1.05), 0.03, 'A-ELEV', fill=INK, edge=None)
    rect(D, x + 1.12, 1.425, x + 1.42, 1.575, 'A-SIGN', fill=BRONZE, lw=0.06)
    dim_v(D, 0, 1.5, x + 1.6, '1500 TO CENTRE', size=1.4)
    D.line([(x - 0.2, 0), (x + 1.9, 0)], 'A-ELEV', lw=0.2)
    D.text((x + 0.95, -0.25), '6 · ROOM PLATE (EVERY DOOR)\nLATCH SIDE, CENTRE ~1500\n(CHECK MS 1184)', 'A-ANNO', size=2.2, va='top', weight='bold')
    # 7 floor inlay + 8 tactile (plan, 1:20)
    x = 7.8
    rect(D, x, 1.0, x + 3.0, 1.9, 'A-FLOR', fill='#D9DCDF', lw=0.08)
    rect(D, x, 1.44, x + 3.0, 1.46, 'A-FLOR', fill=BRASS, edge=None)
    rect(D, x + 1.7, 1.5, x + 2.8, 1.75, 'A-FLOR', fill=BRASS, edge=None, alpha=0.7)
    D.text((x + 2.25, 1.62), 'KANGAR 414 KM · 323.6°', 'A-SIGN', size=1.2, color='#3B2A08', weight='bold')
    D.text((x + 1.5, 0.82), 'BRASS LINE 10 MM IN TERRAZZO + STAMPED PLATE', 'A-ANNO', size=1.3)
    for j in range(6):
        rect(D, x + j * 0.3 + 0.1, 0.0, x + j * 0.3 + 0.38, 0.28, 'A-TACT', fill='#F2C14E', lw=0.05)
        for q in range(4): D.line([(x + j * 0.3 + 0.13, 0.04 + q * 0.065), (x + j * 0.3 + 0.35, 0.04 + q * 0.065)], 'A-TACT', lw=0.06)
    D.text((x + 1.5, -0.25), '7 + 8 · FLOOR INLAYS + TACTILE PATH\nBRIDGE (x11), THRESHOLDS (x8), COMPASS RING\nGUIDING TILES 300 x 300 (MS 1184)', 'A-ANNO', size=2.2, va='top', weight='bold')
    return R1, D2

def room_plate():
    """6 at 1:5: 300 x 150 plate"""
    D = Drawing('PLATE')
    rect(D, 0, 0, 0.3, 0.15, 'A-SIGN', fill=BRONZE, lw=0.1)
    D.text((0.17, 0.105), 'SURAU WANITA', 'A-SIGN', size=4.0, color='white', weight='bold')
    D.text((0.17, 0.072), "WOMEN'S PRAYER ROOM", 'A-SIGN', size=2.4, color='#D9C6A0')
    D.circle((0.045, 0.09), 0.025, 'A-SIGN', fill=None, edge='white', lw=0.15)
    for j in range(12): D.circle((0.1 + j * 0.012, 0.03), 0.0025, 'A-SIGN', fill='white', edge=None)
    dim_h(D, 0, 0.3, 0.17, '300', size=1.6, tick=0.006); dim_v(D, 0, 0.15, 0.32, '150', size=1.6, tick=0.006)
    S2.lead(D, (0.16, 0.03), (0.36, -0.02), 'GRADE 1 BRAILLE')
    S2.lead(D, (0.1, 0.105), (0.36, 0.05), 'RAISED LETTERS 1 MM, UPPERCASE\nBM OVER EN, STRONG CONTRAST')
    return D

def signage_sheet(no='I-300'):
    title = 'SIGNAGE + WAYFINDING FAMILY'
    S, F, x0, y = new_sheet(no, title, '1:20 · 1:5 @ A0')
    side = Drawing('side', paper=True)
    Sg, Sg2 = signage_drawing(); S.place(Sg, 20, (0.0, 0.0), (80, 640))
    drawing_title(side, (40, 560), '1', 'SIGN TYPES 1 + 2 · GATE MARKER + DIRECTORY TOTEMS', 20, 'ELEVATIONS')
    S.place(Sg2, 20, (0.0, 0.0), (420, 330))
    drawing_title(side, (400, 250), '3', 'SIGN TYPES 3, 5, 6, 7 + 8', 20, 'ELEVATIONS (FLOOR INLAYS + TACTILE IN PLAN)')
    S.place(room_plate(), 5, (0.0, 0.0), (90, 360))
    drawing_title(side, (40, 320), '2', 'ROOM PLATE', 5)
    # schedule
    nlev = sum(1 for dd in M.CORE_DOORS); ndoor = sum(1 for dd in M.DOORS if dd['tag'] not in ('SF1', 'RS'))
    rows = [('1', 'GATE MARKER', '4', 'STREET END OF EACH CANOPY', '6000 x 900', 'CUT ALUMINIUM, DARK BRONZE', 'HALO LED'),
            ('2', 'DIRECTORY TOTEM', '5', '4 GATE MOUTHS + KAUNTER INFO', '600 x 120 x 2200', 'POWDER-COATED STEEL, PRINTED GLASS', 'EDGE LED'),
            ('3', 'LEVEL SIGN', str(nlev), 'CORE WALL BESIDE EVERY LIFT / STAIR DOOR', '1200 x 1600', 'PRINTED ALUMINIUM', '—'),
            ('4', 'FASCIA BAND', '9', '8 SHOPS + CAFE (KIT, I-200)', '600 HIGH', 'ANODISED BOX, CUT LETTERS', 'BACKLIT'),
            ('5', 'BLADE SIGN', '9', 'LEFT PIER OF EACH SHOP + CAFE', '600 x 300', 'ALUMINIUM, DOUBLE-SIDED', '—'),
            ('6', 'ROOM PLATE', str(ndoor), 'EVERY ROOM DOOR, LATCH SIDE', '300 x 150', 'ANODISED, RAISED + BRAILLE', '—'),
            ('7', 'FLOOR INLAY', '11 + 8 + 1', 'BRIDGE, SHOP THRESHOLDS, COURT RING', '10 MM LINE', 'BRASS IN TERRAZZO', '—'),
            ('8', 'TACTILE PATH', '1 SYSTEM', 'GATES → ARCADE RING → INFO, LIFTS, WC', '300 x 300', 'STAINLESS STUD / PORCELAIN', '—'),
            ('9', 'STATUTORY', 'PER BOMBA', 'EXITS, FIRE EQUIPMENT (F-100..102)', 'TO BOMBA', 'PHOTOLUMINESCENT / LIT', 'MAINTAINED')]
    S2.table(side, 40, 230, [('TYPE', 10, 'left'), ('SIGN', 26, 'left'), ('NO.', 14, 'left'), ('WHERE', 52, 'left'), ('SIZE', 26, 'left'), ('MATERIAL', 46, 'left'), ('LIGHT', 20, 'left')],
             rows, title='3  SIGN SCHEDULE', size=1.5, lh=2.6, k=1.4)
    S2.finish(S, F, side, no, title, '1:20 · 1:5', None, [
        'BAHASA MELAYU FIRST AND LARGER, ENGLISH BELOW (CONFIRM WITH MAJLIS PERBANDARAN TEMERLOH).',
        'ALL SIGN TEXT UPPERCASE, ONE SANS TYPEFACE, LIGHT ON DARK BRONZE OR THE REVERSE.',
        'COLOUR MEANS GATE, NOT ROOM: DIRECTIONAL SIGNS USE THE GATE STATE STRIPES; STATE COLOURS STAY ON THEIR OWN ROOMS.',
        'MAPS ARE HEADS-UP: THE PLAN ON EACH TOTEM IS TURNED SO THE READER\'S GATE IS AT THE BOTTOM.',
        'PICTOGRAMS USED THE SAME WAY ON EVERY SIGN: WC, PwD, NURSING, SURAU, FIRST AID, INFO, LIFT, STAIRS.',
        'STATUTORY EXIT AND FIRE SIGNS ARE NEVER MIXED WITH THE BRAND SIGNS (SEE F-100 TO F-102).',
        'LOCATIONS: SEE I-100 TO I-102 (ORANGE HEXAGONS).'], y, x0)
    return S, [(Sg, (0, 0)), (Sg2, (0, -5)), (room_plate(), (0, -9))]
