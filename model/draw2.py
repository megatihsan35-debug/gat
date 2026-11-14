from draw import *
from matplotlib.patches import Ellipse
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

Z_GF, Z_L1, Z_PAR = 0.9, 5.4, 6.6
def z_roof_top(r): return 11.2 + (r - R_COURT) * (1.7 / (R_L1 - R_COURT))      # L1 ribbon roof (top)
L1_SECT = sector(B, R_COURT, R_L1, mod(8)[0], mod(13)[1])

# ---------------- ROOF PLAN ----------------
def roof_plan(ax):
    fillpoly(ax, SITE_POLY, '#FBFAF6', z=0); outline(ax, SITE_POLY, 0.9, '#C8372D', 1, (0, (10, 3, 2, 3)))
    fillpoly(ax, SE.PLAZA_SE, '#EFE7D6', z=0.5); fillpoly(ax, SE.GARDEN_N, '#E1ECD3', z=0.5)
    terr = ring(B, R_COURT, R_OVH).difference(L1_SECT).difference(lobby.buffer(0.3))
    fillpoly(ax, terr, '#EAF0E2', INK, 0.4, z=2)
    fillpoly(ax, ring(B, R_OUT, R_OVH).difference(L1_SECT), '#CFE3B8', z=2.1)
    label(ax, 'LALUAN SIMPUL\nroof terrace walk +5.400', B + d(235) * 14.0, 5.0, '#3E5A22')
    label(ax, 'TAMAN ULAM\nherb planters', B + d(325) * 14.6, 4.6, '#3E5A22')
    # court canopy with oculus
    fillpoly(ax, ring(B, 4.5, R_COURT), '#F3F6F8', INK, 0.4, z=3)
    for k in range(12):
        b = 15 + 30 * k; line(ax, [B + d(b) * 4.5, B + d(b) * R_COURT], 0.3, '#7A8288', 4)
    label(ax, 'OCULUS Ø9 m\n(open to sky)', B, 4.6, '#3F6E8C')
    label(ax, 'PTFE canopy +7.200', B + d(200) * 6.8, 4.0, '#3F6E8C')
    # L1 ribbon roof with PV
    fillpoly(ax, L1_SECT, '#E8EDF1', INK, 0.6, z=3)
    for r0 in np.arange(10.0, 21.0, 2.2):
        for b in np.arange(mod(8)[0] + 2, mod(13)[1] - 2, 5.5):
            if r0 + 1.8 > R_L1: continue
            fillpoly(ax, sector(B, r0, r0 + 1.8, b, b + 4.2, 6), '#2F4A63', z=4)
    for b in (mod(9)[0], mod(11)[0], mod(13)[0]):
        line(ax, [B + d(b) * R_COURT, B + d(b) * R_L1], 0.3, INK, 5, (0, (6, 3)))
    ax.annotate('', xy=B + d(100) * 21.0, xytext=B + d(100) * 10.0, arrowprops=dict(arrowstyle='->', lw=0.7, color='#7A2E14'), zorder=9)
    label(ax, 'RIBBON ROOF rises\n+11.200 → +12.900\nPV panels', B + d(150) * 25.8, 4.4, '#7A2E14')
    # small ring roof
    fillpoly(ax, ring(S, RS_WELL, RS_OUT), '#E8EDF1', INK, 0.6, z=3)
    tank = rect_at(S + d(QIBLA - 135) * 7.0, 4.0, 2.6, QIBLA - 45)
    fillpoly(ax, tank, '#BFC9D1', INK, 0.5, z=4); label(ax, 'WATER +\nFIRE TANKS', np.array(tank.centroid.coords[0]), 3.8)
    for b in np.arange(0, 360, 30):
        if abs(((b - (QIBLA - 135)) + 180) % 360 - 180) < 40: continue
        fillpoly(ax, sector(S, 5.0, 9.6, b + 3, b + 24, 6), '#2F4A63', z=4)
    label(ax, 'roof +9.900', S + d(QIBLA) * 7.5, 4.2)
    # knot core + crown
    fillpoly(ax, core_block.buffer(0.6, join_style=2), '#D8DEE3', INK, 0.6, z=5)
    label(ax, 'CORE\n+10.900', np.array(core_block.centroid.coords[0]), 4.2)
    for sgn in (1, -1):
        pts = [B + d(QIBLA + 35 * sgn) * 13.0, B + d(QIBLA) * 18.0 + perp * 2.5 * sgn, S + d(QIBLA + 180 - 35 * sgn) * 7.0]
        line(ax, pts, 2.2, '#B4492B', 6)
    label(ax, 'SIMPUL CROWN\n(2 ribbons cross, +13.500)', B + d(QIBLA) * 18 + perp * 7.5, 4.4, '#7A2E14')
    # ribbons
    for k, (nm, pts, w) in SE.RIBBONS.items():
        g = SE.ribbon_poly(pts, w).difference(Point(B).buffer(R_OVH, 180)).difference(Point(S).buffer(RS_OUT, 180))
        fillpoly(ax, g, '#F4F7F9', INK, 0.5, z=2.5)
        L = LineString(pts)
        for f in np.linspace(0.2, 0.8, 3):
            p = L.interpolate(f, normalized=True)
            if g.contains(p): ax.add_patch(Circle((p.x, p.y), 0.9, fc='#FBFAF6', ec=INK, lw=0.3, zorder=3))
    for k, (nm, pts, w) in SE.RIBBONS.items():
        p = LineString(pts).interpolate(0.35, normalized=True)
        label(ax, k, (p.x, p.y), 4.4, '#3F6E8C', w='bold')
    lamellas(ax, B, R_OVH, mod(13)[1], mod(8)[0] + 360, step=0.9, L=0.35)
    grid(ax, 'GF')

# ---------------- SITE PLAN 1:500 ----------------
AFF = np.load('/home/claude/crit1/affine.npy')
def ctx_image(x0, x1, y0, y1):
    big = Image.open('/mnt/user-data/uploads/A0_BASEMAP_Temerloh_template_copy_jpg.jpeg')
    px0, py1 = np.array([x0, y0, 1]) @ AFF; px1, py0 = np.array([x1, y1, 1]) @ AFF
    crop = big.crop((int(px0), int(py0), int(px1), int(py1))).convert('RGB')
    crop.thumbnail((2400, 2400)); return crop

def site_plan(ax, ext=(-32, 150, -48, 98)):
    x0, x1, y0, y1 = ext
    im = ctx_image(x0, x1, y0, y1)
    ax.imshow(im, extent=(x0, x1, y0, y1), zorder=0, alpha=0.55, interpolation='bilinear')
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='white', alpha=0.28, zorder=0.1))
    fillpoly(ax, SITE_POLY, '#FBFAF6', z=0.3, alpha=0.92)
    outline(ax, SITE_POLY, 1.0, '#C8372D', 6, (0, (10, 3, 2, 3)))
    outline(ax, BUILDABLE, 0.4, '#C8372D', 6, (0, (3, 3)))
    fillpoly(ax, SE.PLAZA_SE, '#EADFC8', z=0.5); fillpoly(ax, SE.GARDEN_N, '#D9E8C6', z=0.5)
    for g_ in (SE.DRIVE, SE.YARD, SE.LAYBY, SE.PARK_AISLE): fillpoly(ax, g_, '#D9D9D9', z=0.6)
    for p in SE.PARK_STAFF + [SE.OKU_BAY]: outline(ax, p, 0.3, INK, 2)
    for p in SE.MOTOR: outline(ax, p, 0.2, INK, 2)
    outline(ax, SE.SUCTION, 0.3, INK, 2, (0, (2, 1)))
    for b_ in SE.BIKES: outline(ax, b_, 0.4, INK, 2)
    # buildings (roof)
    fillpoly(ax, Point(B).buffer(R_OVH + 0.6, 180).buffer(0).difference(Point(B).buffer(R_COURT)).union(Point(S).buffer(RS_OUT + 0.6, 180)).union(lobby).union(L1_SECT).translate(0.8, -0.8) if False else Point(0, 0).buffer(0.001), '#00000022', z=0.9)
    shadow = unary_union([Point(B).buffer(R_OVH, 180).difference(Point(B).buffer(R_COURT, 180)), Point(S).buffer(RS_OUT, 180), lobby, L1_SECT])
    fillpoly(ax, affinity.translate(shadow, 1.6, -1.2), '#8A8F93', z=0.95, alpha=0.45)
    fillpoly(ax, ring(B, R_COURT, R_OVH), '#F2F2EE', INK, 0.5, z=1)
    fillpoly(ax, Point(B).buffer(R_COURT, 180), '#EADFC8', INK, 0.3, z=1)
    fillpoly(ax, ring(B, 4.5, R_COURT), '#FFFFFF', INK, 0.3, z=1.2, alpha=0.8)
    fillpoly(ax, L1_SECT, '#D9DEE3', INK, 0.6, z=1.5)
    fillpoly(ax, Point(S).buffer(RS_OUT, 180).difference(Point(S).buffer(RS_WELL)), '#D9DEE3', INK, 0.6, z=1.5)
    fillpoly(ax, lobby.difference(Point(S).buffer(RS_OUT)).difference(Point(B).buffer(R_OVH)), '#D9DEE3', INK, 0.5, z=1.5)
    fillpoly(ax, core_block.buffer(0.6, join_style=2), '#C9CFD4', INK, 0.5, z=1.6)
    for k, (nm, pts, w) in SE.RIBBONS.items():
        g = SE.ribbon_poly(pts, w).difference(Point(B).buffer(R_OVH, 180)).difference(Point(S).buffer(RS_OUT, 180))
        fillpoly(ax, g, '#FFFFFF', '#3F6E8C', 0.5, z=1.4)
    for (x, y, dia) in SE.TREES + [SE.COURT_TREE]:
        ax.add_patch(Circle((x, y), dia / 2, fc='#9DBE73', ec='#5C7F3A', lw=0.3, alpha=0.85, zorder=2))
    # labels
    T = lambda t, xy, fs=6, c=INK, w='normal', rot=0: ax.text(xy[0], xy[1], t, fontsize=fs, color=c, ha='center', va='center', fontweight=w, rotation=rot, zorder=12,
                                                              bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.75))
    T('GELUNG RASA\n(food ring)', B + d(200) * 14.0, 5.5, '#7A2E14', 'bold')
    T('GELUNG\nKECIL', S, 5.0, '#7A2E14', 'bold')
    T('DATARAN TEMU\n(Pekan Sehari · car boot · events)', (101, -4), 5.2, '#7A2E14')
    T('TAMAN ULAM 11 NEGERI', (72, 51), 5.2, '#3E5A22')
    T('SERVICE YARD', (44, 51), 4.6); T('DROP-OFF', tuple(SE.road_pt(44) + SE.N_IN * 1.5), 4.4)
    T('OKU', tuple(SE.OKU_BAY.centroid.coords[0]), 4.0); T('STAFF P ×5\nMOTOR ×10', tuple(SE.road_pt(25) + SE.N_IN * 21.5), 4.2)
    T('BICYCLE ×10', (100, 7.5), 4.0)
    T('JALAN TOK MUDA AWANG NGAH', tuple(SE.road_pt(45) - SE.N_IN * 5.5), 6.0, INK, 'bold', -8.0)
    T('ISTANA SRI UDARA\n(grounds)', (-12, 72), 5.6); T('FUTSAL HALL', (78, 86), 5.6); T('TENNIS COURT', (118, 42), 5.6)
    T('↓ STADIUM TEMERLOH', (95, -40), 5.6); T('SUNGAI PAHANG +\nESPLANADE 2 → (~150 m)', (136, 8), 5.4, '#2D6E73')
    for k, (nm, pts, w) in SE.RIBBONS.items():
        p = np.array(pts[0]); T(f'RIBEN {k}', p + (np.array([0, -3.2]) if k in ('TENGAH', 'SELATAN', 'TIMUR') else np.array([0, 2.8])), 4.6, '#3F6E8C', 'bold')
    # access arrows
    def arr(p, q, c, lw=1.4):
        ax.annotate('', xy=q, xytext=p, arrowprops=dict(arrowstyle='-|>', lw=lw, color=c, mutation_scale=9), zorder=13)
    arr(tuple(SE.road_pt(13) - SE.N_IN * 8), tuple(SE.road_pt(13) + SE.N_IN * 2), '#7A5BA8')
    arr(tuple(SE.road_pt(28) - SE.N_IN * 7), tuple(SE.road_pt(33) + SE.N_IN * 1.5), '#555555')
    arr((112, -24), (104, -10), '#E08A1E'); arr(tuple(SE.road_pt(73) - SE.N_IN * 9), tuple(SE.road_pt(73) + SE.N_IN * 1), '#E08A1E')
    arr((53, 66), (53, 57.5), '#E08A1E')
    # legend
    lx, ly = x0 + 3, y0 + 18
    for i, (c, t) in enumerate([('#E08A1E', 'pedestrian entry'), ('#555555', 'drop-off / OKU'), ('#7A5BA8', 'service + staff vehicles')]):
        arr((lx, ly - 4.5 * i), (lx + 7, ly - 4.5 * i), c); ax.text(lx + 9, ly - 4.5 * i, t, fontsize=5.2, va='center', zorder=13)

# ---------------- SECTIONS ----------------
def rooms_at(level, p):
    pt = Point(p)
    for r in ROOMS:
        if r['level'] == level and r['poly'].buffer(0.02).contains(pt): return r
    return None

def section(ax, brg, s0, s1, title_pts=True, fs=5.0):
    u = d(brg)
    S_ = np.arange(s0, s1, 0.05)
    P = lambda s: B + u * s
    # ground + plinth
    plinth_g = unary_union([Point(B).buffer(R_OVH + 3.0, 180), Point(S).buffer(RS_OUT + 3.0, 180), lobby.buffer(3.0)])
    gx, gz = [], []
    for s in S_:
        p = Point(P(s)); inside = plinth_g.contains(p)
        dist = plinth_g.exterior.distance(p) if not inside else 0
        gz.append(Z_GF if inside else max(0.0, Z_GF - dist / 20)); gx.append(s)
    gx, gz = np.array(gx), np.array(gz)
    ax.fill_between(gx, gz, -1.2, color='#E7E1D3', zorder=1, lw=0)
    ax.plot(gx, gz, color=INK, lw=0.9, zorder=6)
    ax.fill_between(gx, np.where(gz >= Z_GF - 0.01, Z_GF, np.nan), Z_GF - 0.3, color=INK, zorder=6)
    # helper to find intervals of a predicate
    def intervals(pred):
        out, st = [], None
        for s in S_:
            v = pred(s)
            if v and st is None: st = s
            if not v and st is not None: out.append((st, s)); st = None
        if st is not None: out.append((st, S_[-1]))
        return out
    inL1sect = lambda s: L1_SECT.contains(Point(P(s)))
    ringpoly = ring(B, R_COURT, R_OVH)
    l1floor = unary_union([ringpoly, ring(S, RS_WELL, RS_OUT), lobby, L1_SECT])
    for a, b_ in intervals(lambda s: l1floor.contains(Point(P(s)))):
        ax.add_patch(Rectangle((a, Z_L1 - 0.45), b_ - a, 0.45, fc=INK, zorder=7))
    # terrace parapets / planters
    for a, b_ in intervals(lambda s: ring(B, R_OUT, R_OVH).contains(Point(P(s))) and not inL1sect(s)):
        ax.add_patch(Rectangle((a, Z_L1), b_ - a, 0.6, fc='#9DBE73', ec=INK, lw=0.4, zorder=6))
        edge = a if abs(np.linalg.norm(P(a) - B) - R_OVH) < 0.2 else b_
        ax.plot([edge, edge], [Z_L1, Z_PAR], color='#9A3F25', lw=1.2, zorder=7)
    # L1 block roof (ribbon) and walls
    for a, b_ in intervals(inL1sect):
        xs = np.linspace(a, b_, 30); rr = np.array([np.linalg.norm(P(s) - B) for s in xs])
        top = z_roof_top(rr); bot = top - 1.2
        ax.fill_between(xs, top - 0.25, top, color=INK, zorder=7)
        for k in range(len(xs) - 1):           # truss zigzag
            ax.plot([xs[k], xs[k + 1]], [bot[k] if k % 2 else top[k] - 0.25, top[k + 1] - 0.25 if k % 2 else bot[k + 1]], color='#5A6166', lw=0.4, zorder=6)
        ax.plot(xs, bot, color='#5A6166', lw=0.6, zorder=6)
        for edge in (a, b_):
            r_ = np.linalg.norm(P(edge) - B)
            if abs(r_ - R_L1) < 0.3:
                ax.plot([edge, edge], [Z_L1, z_roof_top(R_L1) - 1.2], color='#4F8FB5', lw=1.0, zorder=7)
                ax.add_patch(Rectangle((edge - 0.12, Z_L1), 0.24, z_roof_top(R_L1) - 1.2 - Z_L1, fc='none', ec=INK, lw=0.4, zorder=7))
        mid_s = (a + b_) / 2
    # small ring roof + tanks
    for a, b_ in intervals(lambda s: ring(S, RS_WELL, RS_OUT).contains(Point(P(s)))):
        ax.add_patch(Rectangle((a, 9.6), b_ - a, 0.35, fc=INK, zorder=7))
        ax.add_patch(Rectangle((a, 9.95), b_ - a, 0.9, fc='none', ec='#9A3F25', lw=0.6, zorder=6, hatch='||||'))
    # core
    for a, b_ in intervals(lambda s: core_block.buffer(0.6, join_style=2).contains(Point(P(s)))):
        ax.add_patch(Rectangle((a, 10.5), b_ - a, 0.4, fc=INK, zorder=7))
        ax.add_patch(Rectangle((a, Z_GF), b_ - a, 10.5 - Z_GF, fc='none', ec=INK, lw=0.5, zorder=6))
        ax.plot([(a + b_) / 2 - 1.0, (a + b_) / 2 + 1.0], [12.4, 12.4], color=INK, lw=0.6)
    # walls per level: transitions
    for level, z0, z1 in (('GF', Z_GF, Z_L1 - 0.45), ('L1', Z_L1, None)):
        prev = None; prev_s = None
        for s in S_:
            r = rooms_at(level, P(s))
            key = r['name'] if r else None
            if prev_s is not None and key != prev:
                zz1 = z1
                if level == 'L1':
                    rr_ = np.linalg.norm(P(s) - B)
                    zz1 = (z_roof_top(rr_) - 1.2) if L1_SECT.contains(Point(P(s))) else 9.6
                    if not (r or prev): continue
                    if (r and r['code'] == 'OPEN') and (prev is None): continue
                glaze = False
                for C, rad, gb0, gb1 in GLAZE[level]:
                    q = P(s); rq = np.linalg.norm(q - C); bq = np.degrees(np.arctan2(q[0] - C[0], q[1] - C[1])) % 360
                    lo, hi = gb0 % 360, gb1 % 360
                    inside = (lo <= bq <= hi) if lo <= hi else (bq >= lo or bq <= hi)
                    if abs(rq - rad) < 0.3 and inside: glaze = True
                both_open = (prev is None or (r is None)) and not (r or prev)
                if r is None and prev is None: pass
                elif (r and r['code'] == 'OPEN' and prev is None) or (prev and prev_code == 'OPEN' and r is None):
                    pass
                elif glaze:
                    ax.plot([s, s], [z0, zz1], color='#4F8FB5', lw=1.1, zorder=7)
                else:
                    ax.add_patch(Rectangle((s - 0.1, z0), 0.2, zz1 - z0, fc=INK, zorder=7))
            prev, prev_s = key, s; prev_code = r['code'] if r else None
    # room names
    for level, zc in (('GF', 3.0), ('L1', 7.6)):
        segs = []; cur = None; st = None
        for s in S_:
            r = rooms_at(level, P(s)); k = r['label'] if r else None
            if k != cur:
                if cur and st is not None: segs.append((cur, st, s))
                cur, st = k, s
        for k, a, b_ in segs:
            if b_ - a < 2.4 or k in ('', 'prep', 'store') : continue
            ax.text((a + b_) / 2, zc, k.replace(' ', '\n') if len(k) > 9 else k, fontsize=fs - 0.6, ha='center', va='center', zorder=9, linespacing=1.0)
    # court + canopy + verandah columns
    for a, b_ in intervals(lambda s: np.linalg.norm(P(s) - B) < R_COURT):
        ax.text((a + b_) / 2, 2.4, 'COURT “TALAM”\nopen dining', fontsize=fs - 0.4, ha='center', zorder=9, color='#7A2E14')
        for side in (a, b_):
            ax.add_patch(Rectangle((side - 0.25, Z_GF), 0.5, Z_L1 - Z_GF - 0.45, fc='white', ec=INK, lw=0.5, zorder=6))
        cx = (a + b_) / 2
        for sgn in (-1, 1):
            ax.plot([cx + sgn * R_COURT, cx + sgn * 4.5], [6.6, 7.2], color=INK, lw=1.4, zorder=7)
        ax.text(cx, 8.1, 'oculus Ø9 m', fontsize=fs - 0.8, ha='center', color='#3F6E8C')
        ax.add_patch(Circle((cx, Z_GF + 3.2), 2.4, fc='#9DBE73', ec='#5C7F3A', lw=0.4, zorder=4, alpha=0.9))
        ax.plot([cx, cx], [Z_GF, Z_GF + 1.6], color='#5C7F3A', lw=1.2, zorder=4)
    # piles (indicative) under columns
    for s in S_[::20]:
        pass
    # levels
    xl = s0 - 1.0
    for z, t in [(0.0, '±0.000 existing ground'), (Z_GF, '+0.900 GF (plinth)'), (Z_L1, '+5.400 L1 / roof terrace'), (11.2, '+11.200 ribbon roof (inner)'), (12.9, '+12.900 ribbon roof (outer)')]:
        ax.plot([xl - 0.8, xl + 0.8], [z, z], color=INK, lw=0.5, zorder=8)
        ax.add_patch(MPoly([(xl, z), (xl - 0.45, z + 0.55), (xl + 0.45, z + 0.55)], closed=True, fc=INK, zorder=8))
        ax.text(xl - 1.2, z + 0.25, t, fontsize=fs - 0.8, ha='right', va='center', zorder=8)

def span_dim(ax, a, b_, z, txt, fs=4.8):
    ax.annotate('', xy=(a, z), xytext=(b_, z), arrowprops=dict(arrowstyle='<|-|>', lw=0.6, color='#7A2E14', mutation_scale=6), zorder=10)
    ax.text((a + b_) / 2, z + 0.45, txt, fontsize=fs, ha='center', color='#7A2E14', zorder=10)

# ---------------- ELEVATIONS ----------------
def elevation(ax, vb, fs=5.0):
    v = d(vb); h = d(vb + 90)
    X = lambda p: float(np.dot(p, h)); D = lambda p: float(np.dot(p, v))
    items = []
    def fin_set(C, R, b0, b1, z0, z1f, step=0.6, col='#B4492B', fill='#F3EEE7'):
        if b1 <= b0: b1 += 360
        bs = np.linspace(b0, b1, max(3, int(np.radians(b1 - b0) * R / step)))
        vis = [b for b in bs if np.dot(d(b), v) < -0.02]
        if not vis: return
        xs = [X(C + d(b) * R) for b in vis]
        items.append((D(C) - R * 0.5, 'fins', (xs, [z0] * len(vis), [z1f(b) for b in vis], col, fill)))
    # small ring
    fin_set(S, RS_OUT + 0.3, 0, 360, Z_GF, lambda b: 9.95)
    # big ring GF + terrace parapet (exclude gates & cafe glass)
    def z_big(b):
        bb = b % 360; inL1 = (mod(8)[0] <= bb <= mod(13)[1])
        return Z_PAR if not inL1 else 5.0
    fin_set(B, R_OUT + 0.4, 0, 360, Z_GF, z_big, col='#B4492B')
    # L1 block outer face
    fin_set(B, R_L1 + 0.1, mod(8)[0], mod(13)[1], Z_L1 - 0.45, lambda b: z_roof_top(R_L1) - 0.2, step=0.75, col='#9A3F25', fill='#E9EEF2')
    items.sort(key=lambda t: -t[0])
    # L1 block silhouette (behind)
    bs = np.linspace(mod(8)[0], mod(13)[1], 80)
    outer = [(X(B + d(b) * R_L1), z_roof_top(R_L1)) for b in bs]; inner = [(X(B + d(b) * R_COURT), z_roof_top(R_COURT)) for b in bs]
    xs_all = [p[0] for p in outer + inner]
    ax.fill_between([min(xs_all), max(xs_all)], 5.0, [max(p[1] for p in outer + inner)] * 2, color='#E9EEF2', zorder=1)
    top_pts = sorted(outer + inner, key=lambda p: p[0])
    # silhouette top = upper envelope
    xs_env = np.linspace(min(xs_all), max(xs_all), 120)
    env = [max([p[1] for p in top_pts if abs(p[0] - x) < 0.6] or [5.0]) for x in xs_env]
    ax.fill_between(xs_env, 5.0, env, color='#E9EEF2', zorder=1.2); ax.plot(xs_env, env, color=INK, lw=0.8, zorder=1.3)
    # crown + core
    cx = X(B + d(QIBLA) * 17.0)
    ax.add_patch(Rectangle((cx - 3.2, Z_GF), 6.4, 10.9 - Z_GF, fc='#DDE3E8', ec=INK, lw=0.6, zorder=1.1))
    tt = np.linspace(-1, 1, 40)
    for sgn in (1, -1):
        ax.plot(cx + tt * 9.0 * sgn, 13.5 - 3.2 * tt ** 2 - 0.0, color='#B4492B', lw=2.0, zorder=1.4)
    # small ring tanks
    ax.add_patch(Rectangle((X(S) - 2.0, 9.95), 4.0, 2.0, fc='#C9D1D8', ec=INK, lw=0.5, zorder=1.1))
    for depth, kind, data in items:
        xs, z0s, z1s, col, fill = data
        ax.fill_between(sorted(xs), min(z0s), [max(z1s)] * len(xs), color=fill, zorder=2)
        top = sorted(zip(xs, z1s)); ax.plot([p[0] for p in top], [p[1] for p in top], color=INK, lw=0.7, zorder=3)
        for x_, a_, b_ in zip(xs, z0s, z1s): ax.plot([x_, x_], [a_, b_], color=col, lw=0.45, zorder=3)
        ax.plot([min(xs), max(xs)], [min(z0s)] * 2, color=INK, lw=0.7, zorder=3)
    # slab edge band (terrace)
    xb = [X(B) - R_OVH, X(B) + R_OVH]
    ax.add_patch(Rectangle((xb[0], 5.0), xb[1] - xb[0], 0.4, fc='white', ec=INK, lw=0.6, zorder=3.5))
    # ribbons canopies
    for k, (nm, pts, w) in SE.RIBBONS.items():
        L = LineString(pts)
        xs = [X(np.array(L.interpolate(f, normalized=True).coords[0])) for f in np.linspace(0, 1, 30)]
        zz = 4.2 + 1.4 * np.sin(np.linspace(0, np.pi, 30))
        ax.plot(xs, zz, color='#3F6E8C', lw=1.4, zorder=4)
        for f in (0.15, 0.5, 0.85):
            p = np.array(L.interpolate(f, normalized=True).coords[0]); ax.plot([X(p)] * 2, [0.0, 4.2 + 1.4 * np.sin(np.pi * f)], color='#3F6E8C', lw=0.6, zorder=4)
    # ground + trees + people
    allx = [X(np.array(p)) for p in SITE]
    ax.plot([min(allx) - 4, max(allx) + 4], [0, 0], color=INK, lw=1.0, zorder=5)
    for (x, y, dia) in SE.TREES:
        if D(np.array([x, y])) < D(B) - 5:
            xx = X(np.array([x, y])); ax.add_patch(Ellipse((xx, 5.5), dia, dia * 0.9, fc='none', ec='#5C7F3A', lw=0.5, zorder=5))
            ax.plot([xx, xx], [0, 3.6], color='#5C7F3A', lw=0.6, zorder=5)
    rng = np.random.default_rng(int(vb))
    for x in rng.uniform(min(allx) + 10, max(allx) - 10, 9):
        ax.plot([x, x], [0.0, 1.25], color=INK, lw=1.0, zorder=6); ax.add_patch(Circle((x, 1.5), 0.22, fc=INK, zorder=6))
    for z, t in [(0.0, '±0.000'), (Z_GF, '+0.900'), (Z_L1, '+5.400'), (Z_PAR, '+6.600'), (12.9, '+12.900'), (13.5, '+13.500 crown')]:
        x_ = min(allx) - 6
        ax.plot([x_ - 0.8, x_ + 0.8], [z, z], color=INK, lw=0.4); ax.text(x_ - 1.1, z, t, fontsize=fs - 0.8, ha='right', va='center')
