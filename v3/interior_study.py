"""Interior design study (15 Nov 2026): figures for the Docs study 'Titik Temu — Interior Design Study'.
fig 1  interior zoning plans GF / L1 / L2 coloured by state theme (rooms from plan3, true geometry)
fig 2  shopfront kit: 8 shopfront elevations (true widths at R12.5) + radial section through a shop
fig 3  signage family
Run: python3 v3/interior_study.py OUTDIR"""
import sys, math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Rectangle, Circle, Wedge, FancyBboxPatch
from matplotlib import font_manager as fm
from shapely.geometry import Polygon, MultiPolygon
import plan3 as M
import rings as RG
import scheme as SC

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
plt.rcParams['font.family'] = 'Inter'
INK = '#1F2A33'; GREY = '#C9CED3'; BOH = '#E3E6E9'; CORE = '#8A949C'
# Crit 1 state palette (model/int_plans.py)
ST = {'KEL': ('KELANTAN', 'KOTA BHARU', 356.2, 298, '#3456D6'), 'TRG': ('TERENGGANU', 'K. TERENGGANU', 20.9, 224, '#11A89A'),
      'PHG': ('PAHANG', 'KUANTAN', 68.4, 108, '#6FB3D2'), 'JHR': ('JOHOR', 'JOHOR BAHRU', 145.9, 263, '#E8B523'),
      'MLK': ('MELAKA', 'MELAKA', 187.6, 141, '#B83A2E'), 'NSN': ('N. SEMBILAN', 'SEREMBAN', 213.3, 96, '#9A6A45'),
      'SGR': ('SELANGOR', 'SHAH ALAM', 247.3, 108, '#8CC63F'), 'PRK': ('PERAK', 'IPOH', 311.0, 195, '#C9A27A'),
      'PNG': ('P. PINANG', 'GEORGE TOWN', 313.4, 318, '#E46F8C'), 'KDH': ('KEDAH', 'ALOR SETAR', 322.7, 374, '#4E8F3A'),
      'PLS': ('PERLIS', 'KANGAR', 323.6, 414, '#F28C28')}
HOST = '#BFE0EE'; HOST2 = '#DCEFF6'; HALL = '#E3CF9E'; PRAY = '#EFE4C2'; GAL = '#C9BEE6'; ADMIN = '#FBE2C8'; DECK = '#F3EEE2'
SHOP = {'A2-1': 'PHG', 'A2-2': 'JHR', 'A2-3': 'MLK', 'A2-4': 'NSN', 'A1-1': 'SGR', 'A1-2': 'PRK', 'A1-3': 'PNG', 'A1-4': 'KDH'}

def tint(c, k):
    c = np.array(matplotlib.colors.to_rgb(c)); return tuple(c + (1 - c) * k)

def theme(r):
    k = r['key']
    if k in SHOP: return ST[SHOP[k]][4], ST[SHOP[k]][0]
    if k in ('G31',): return ST['KEL'][4], 'KELANTAN'
    if k in ('G30', 'G32', 'G33'): return tint(ST['KEL'][4], 0.55), None
    if k == 'L21': return ST['PLS'][4], 'PERLIS'
    if k in ('L24', 'L27', 'L22', 'L23', 'L20', 'L25', 'L26'): return ADMIN, None
    if k == 'M14': return ST['TRG'][4], 'TERENGGANU'
    if k == 'L12': return HALL, None
    if k in ('M10', 'M12', 'M11', 'M13'): return PRAY, None
    if k == 'M01': return GAL, None
    if k in ('G01', 'G02', 'L04', 'L05', 'G03', 'G04', 'G20', 'G21'): return HOST, None
    if r['kind'] in ('stair', 'lift'): return CORE, None
    return BOH, None

SHORT = {'G01': 'WC (L)', 'G02': 'WC (P)', 'G03': 'NURSING', 'G04': 'NAPPY', 'G10': 'LOADING', 'G11': 'FREEZER', 'G08': 'MDB', 'G23': 'STORE',
         'G20': 'INFO +\nSECURITY', 'G21': 'FIRST\nAID', 'G22': 'WHEELCHAIR', 'G06': 'STAFF WC', 'G07': 'STAFF WC', 'G31': 'CAFE\nWAU BULAN',
         'G30': 'KITCHEN', 'G33': 'HAND\nWASH', 'L04': 'WC (L)', 'L05': 'WC (P)', 'L12': 'DAPUR\nREWANG', 'L21': 'RECEPTION', 'L24': 'OFFICE',
         'L25': 'MANAGER', 'L26': 'MEETING', 'L13': 'DRY STORE', 'L10': 'FURN.', 'L11': 'EQUIP.', 'M01': 'GALERI\nPETA RASA', 'M10': 'SURAU\nLELAKI',
         'M12': 'SURAU\nWANITA', 'M14': 'SERAMBI\nPANTAI', 'M02': 'STORE', 'M03': 'STAFF', 'M11': 'WUDHU', 'M13': 'WUDHU'}

def polys(g):
    if g.is_empty: return []
    return list(g.geoms) if hasattr(g, 'geoms') else [g]

def fillg(ax, g, fc, ec=INK, lw=0.4, z=2, alpha=1.0, ls='-'):
    for p in polys(g):
        if p.geom_type != 'Polygon': continue
        from matplotlib.path import Path as MPath
        from matplotlib.patches import PathPatch
        rings = [np.array(p.exterior.coords)] + [np.array(h.coords) for h in p.interiors]
        verts = np.concatenate(rings); codes = np.concatenate([[MPath.MOVETO] + [MPath.LINETO] * (len(r_) - 2) + [MPath.CLOSEPOLY] for r_ in rings])
        ax.add_patch(PathPatch(MPath(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls))

def lab(ax, xy, s, size=5.2, color=INK, w='semibold', z=9, rot=0):
    ax.text(*xy, s, ha='center', va='center', fontsize=size, color=color, fontweight=w, zorder=z, rotation=rot, linespacing=1.05)

def ringline(ax, r, b0, b1, **kw):
    bs = np.linspace(b0, b1, 200); pts = np.array([M.P(r, b) for b in bs]); ax.plot(pts[:, 0], pts[:, 1], **kw)

def plan(ax, fl):
    C = np.array(M.C)
    # context outline
    ax.add_patch(Circle(C, M.R_ROOF if hasattr(M, 'R_ROOF') else 28.3, fc='none', ec=GREY, lw=0.4, ls='--', zorder=0))
    if fl == 'GF':
        ax.add_patch(Circle(C, M.R_COURT, fc=HOST2, ec=INK, lw=0.5, zorder=1))
        ax.add_patch(Circle(C, M.R_POOL, fc='#9ED0E8', ec=INK, lw=0.4, zorder=2))
        fillg(ax, SC.ann(M.R_BR0, M.R_BR1), HOST2, ec=GREY, lw=0.3, z=1)
        # river bands (Pahang darker from Timur, Semantan lighter from Tengah) meeting at the pool
        for b, c in ((27.9, '#5DA9CC'), (242.8, '#A9D6EA')):
            t = np.linspace(0, 1, 60); rr = M.R_COURT - (M.R_COURT - M.R_POOL) * t; bb = b + 55 * t * (1 if b < 100 else -1)
            pts = np.array([M.P(r_, b_) for r_, b_ in zip(rr, bb)]); ax.plot(pts[:, 0], pts[:, 1], color=c, lw=3.2, zorder=2.5, solid_capstyle='round')
        ringline(ax, 9.4, 0, 360, color='#B08D3C', lw=0.9, zorder=3)
        q = [M.P(9.4, SC.QIBLA), M.P(10.6, SC.QIBLA)]; ax.plot(*np.array(q).T, color='#B08D3C', lw=1.4, zorder=3)
        lab(ax, M.P(7.6, SC.QIBLA), 'QIBLA', 4.2, '#8A6A20', z=9)
        lab(ax, M.P(6.0, 205), 'TALAM COURT', 6, INK)
        lab(ax, M.P(0, 0), 'TITIK', 4.4)
        for s in SC.SPINES:
            lab(ax, M.P(26.0, s['b']), s['k'], 6.2, INK, 'bold')
    else:
        ax.add_patch(Circle(C, M.R_COURT, fc='white', ec=GREY, lw=0.4, ls='--', zorder=0))
        lab(ax, M.P(0, 0), 'OPEN TO\nCOURT', 5, '#7A858E', 'medium')
        fillg(ax, M.WALK, HOST2, ec=GREY, lw=0.3, z=1)
        for g in M.decks(fl):
            rs = [M.rad(c) for c in g.exterior.coords]
            fillg(ax, g, DECK if min(rs) > 20 else '#CFE7F1', ec=GREY, lw=0.3, z=1)
    if fl == 'L1':
        fillg(ax, RG.BRIDGE, '#9FCFE4', ec=INK, lw=0.4, z=2)
        fillg(ax, RG.WALKWAYS, '#9FCFE4', ec=INK, lw=0.4, z=2)
        for k, (nm, cap, b, km, c) in ST.items():
            p0, p1 = M.P(RG.R_BG0 + 0.1, b), M.P(RG.R_BG1 - 0.1, b); ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color='#8A6A20', lw=0.9, zorder=4)
        for s in SC.SPINES: lab(ax, M.P(28.6, s['b']), s['k'], 6.2, INK, 'bold')
        lab(ax, M.P(18.5, 200.5), 'JAMBATAN\nSIMPUL', 4.6, INK)
        lab(ax, M.P(24.0, 215), 'DEK PEKAN\nSEHARI', 5.2, '#6E5E3A')
        lab(ax, M.P(24.0, 52), '', 4)
        lab(ax, M.P(13.2, 205), 'ANJUNG\nTALAM', 4.8, '#3D6E86')
        lab(ax, M.P(24.0, 30), 'ANJUNG\nTIMUR', 4.4, '#6E5E3A')
    if fl == 'L2':
        lab(ax, M.P(13.2, 62), 'ANJUNG\nSUNGAI', 4.8, '#3D6E86')
        lab(ax, M.P(13.4, 207), 'ANJUNG\nSENJA', 4.6, '#3D6E86')
        for s in SC.SPINES: lab(ax, M.P(19.5, s['b']), s['k'], 6.2, '#7A858E', 'bold')
    for r in M.ROOMS:
        if r['fl'] != fl: continue
        fc, st = theme(r)
        fillg(ax, r['poly'], fc, ec=INK, lw=0.45, z=3)
        if r['kind'] in ('stair', 'lift'): continue
        bm, b0, b1 = M.mid(r['key']); rs = [M.rad(c) for c in r['poly'].exterior.coords]; rm = (min(rs) + max(rs)) / 2
        txt = SHORT.get(r['key'], '')
        if r['kind'] == 'shop': txt = r['key']
        dark = st is not None and r['key'] not in ('A1-4',)
        col = 'white' if (st and r['key'] in ('A2-3', 'A2-4', 'G31', 'M14', 'A1-4', 'L21', 'A1-3')) else INK
        span = b1 - b0
        if r['kind'] == 'shop':
            lab(ax, M.P(rm - 1.3, bm), txt, 4.4, col, 'bold', rot=0)
            lab(ax, M.P(rm + 2.6, bm), st, 3.6, col, 'semibold', rot=0)
        elif txt and span >= 7:
            lab(ax, M.P(rm, bm), txt + (('\n' + st) if st and r['kind'] != 'shop' and st not in txt else ''), 4.0, col)
        elif txt:
            a = 90 - bm
            while a < -90: a += 180
            while a > 90: a -= 180
            lab(ax, M.P(rm, bm), txt.replace('\n', ' '), 3.4, col, rot=a)
    for c in M.CORES.values():
        pass
    ax.set_aspect('equal'); ax.set_xlim(M.C[0] - 31, M.C[0] + 31); ax.set_ylim(M.C[1] - 31, M.C[1] + 31); ax.axis('off')
    # north arrow
    x0, y0 = M.C[0] + 26, M.C[1] + 26
    ax.annotate('', xy=(x0, y0 + 3), xytext=(x0, y0), arrowprops=dict(arrowstyle='-|>', color=INK, lw=0.8)); lab(ax, (x0, y0 + 4.2), 'U', 5.5, INK, 'bold')

def fig_plans():
    fig, axs = plt.subplots(1, 3, figsize=(16.5, 6.4), dpi=220)
    for ax, fl, t in zip(axs, ('GF', 'L1', 'L2'), ('GROUND FLOOR  FFL +0.900', 'FIRST FLOOR  FFL +5.400', 'SECOND FLOOR  FFL +9.600')):
        plan(ax, fl); ax.set_title(t, fontsize=9.5, fontweight='bold', color=INK, pad=4)
    # legend
    items = [(ST[k][4], ST[k][0]) for k in ('PHG', 'JHR', 'MLK', 'NSN', 'SGR', 'PRK', 'PNG', 'KDH', 'KEL', 'PLS', 'TRG')]
    items += [(HOST, 'HOST: COURT, ARCADE, WC'), ('#9FCFE4', 'RING BRIDGE + WALKWAYS'), (ADMIN, 'ADMIN'), (HALL, 'DAPUR REWANG HALL'),
              (GAL, 'GALLERY (ALL STATES)'), (PRAY, 'PRAYER (NEUTRAL)'), (DECK, 'OPEN DECKS'), (BOH, 'BACK OF HOUSE'), (CORE, 'CORES')]
    x = 0.03
    for i, (c, t) in enumerate(items):
        cx = 0.02 + (i % 10) * 0.098; cy = 0.075 - (i // 10) * 0.035
        fig.patches.append(Rectangle((cx, cy), 0.012, 0.018, transform=fig.transFigure, fc=c, ec=INK, lw=0.3))
        fig.text(cx + 0.016, cy + 0.009, t, fontsize=5.6, va='center', color=INK, fontweight='medium')
    fig.text(0.02, 0.965, 'TITIK TEMU — INTERIOR ZONING BY STATE THEME', fontsize=12, fontweight='bold', color=INK)
    fig.text(0.02, 0.935, 'HOST STATE PAHANG DRESSES THE SHARED SPACES · EACH SHOP AND SPECIAL ROOM TAKES ONE GUEST STATE · BRASS LINES ON THE BRIDGE = TRUE BEARING OF EACH STATE CAPITAL',
             fontsize=6.6, color='#55606A', fontweight='medium')
    plt.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.12, wspace=0.02)
    fig.savefig(os.path.join(OUT, 'int_zoning.png'), facecolor='white'); plt.close(fig)

# ------------------------------------------------------------------------------------------------- shopfront patterns
def pattern(ax, k, x0, y0, w, h, col):
    """the unique state screen, drawn in a w x h band (metres)"""
    ax.add_patch(Rectangle((x0, y0), w, h, fc=tint(col, 0.75), ec=INK, lw=0.5, zorder=3))
    clip = Rectangle((x0, y0), w, h, transform=ax.transData)
    arts = []
    rng = np.random.default_rng(7)
    if k == 'PHG':   # tenun check
        for i in np.arange(x0, x0 + w, 0.12): arts.append(ax.plot([i, i], [y0, y0 + h], color=col, lw=1.8 if int(round((i - x0) / 0.12)) % 3 == 0 else 0.7, zorder=4)[0])
        for j in np.arange(y0, y0 + h, 0.12): arts.append(ax.plot([x0, x0 + w], [j, j], color='#2E6E8E', lw=1.4 if int(round((j - y0) / 0.12)) % 3 == 0 else 0.5, zorder=4)[0])
    elif k == 'JHR':  # zapin fins: 1-2-3 step rhythm
        xs = x0 + 0.05; steps = [0.06, 0.06, 0.18]; i = 0
        while xs < x0 + w:
            arts.append(ax.add_patch(Rectangle((xs, y0), 0.035, h, fc=col, ec='none', zorder=4))); xs += steps[i % 3]; i += 1
    elif k == 'MLK':  # peranakan four-petal
        for cx in np.arange(x0 + 0.15, x0 + w, 0.3):
            for cy in (y0 + 0.15, y0 + 0.45):
                for a in (0, 90, 180, 270):
                    e = matplotlib.patches.Ellipse((cx + 0.06 * math.cos(math.radians(a)), cy + 0.06 * math.sin(math.radians(a))), 0.11, 0.06, angle=a, fc=col, ec='none', zorder=4)
                    arts.append(ax.add_patch(e))
    elif k == 'NSN':  # gonjong profile
        for cx in np.arange(x0, x0 + w, 0.38):
            xs = np.linspace(cx, cx + 0.38, 30); ys = y0 + 0.1 + 0.38 * (np.abs(np.linspace(-1, 1, 30)) ** 2.4)
            arts.append(ax.fill_between(xs, y0 + 0.08, ys, color=col, zorder=4, lw=0))
    elif k == 'SGR':  # firefly dots
        pts = rng.uniform([x0, y0], [x0 + w, y0 + h], (90, 2)); s = rng.uniform(1, 9, 90)
        arts.append(ax.scatter(pts[:, 0], pts[:, 1], s=s, color=col, zorder=4, lw=0))
    elif k == 'PRK':  # karst skyline
        xs = np.linspace(x0, x0 + w, 120); ys = y0 + 0.12 + 0.3 * np.abs(np.sin(xs * 7.1)) ** 0.6 * (0.6 + 0.4 * np.sin(xs * 2.3))
        arts.append(ax.fill_between(xs, y0, ys, color=col, zorder=4, lw=0))
    elif k == 'PNG':  # oval portals
        for cx in np.arange(x0 + 0.17, x0 + w, 0.34):
            arts.append(ax.add_patch(matplotlib.patches.Ellipse((cx, y0 + h / 2), 0.2, 0.42, fc='none', ec=col, lw=1.6, zorder=4)))
    elif k == 'KDH':  # padi rows
        for cx in np.arange(x0 + 0.05, x0 + w, 0.09):
            arts.append(ax.plot([cx, cx + 0.03], [y0 + 0.05, y0 + h - 0.06], color=col, lw=0.9, zorder=4)[0])
            arts.append(ax.add_patch(matplotlib.patches.Ellipse((cx + 0.03, y0 + h - 0.1), 0.03, 0.1, fc='#D9B24A', ec='none', zorder=4)))
    elif k == 'KEL':  # wau bulan curves
        for cx in np.arange(x0 + 0.3, x0 + w, 0.6):
            arts.append(ax.add_patch(matplotlib.patches.Arc((cx, y0 + 0.62), 0.55, 0.7, theta1=200, theta2=340, ec=col, lw=2.2, zorder=4)))
    for a in arts:
        try: a.set_clip_path(clip)
        except Exception: pass

RANGE = {'A2-1': 'LEMPOK DURIAN · KEREPEK', 'A2-2': 'KOLE KACANG · PUTU BAMBU', 'A2-3': 'KUIH NYONYA · GULA MELAKA', 'A2-4': 'WAJIK · APAM JOHOL · LEMANG',
         'A1-1': 'REMPAH SATAY · HASIL LAUT KERING', 'A1-2': 'KOPI PUTIH · REMPAH RENDANG TOK', 'A1-3': 'BUAH PALA · REMPAH', 'A1-4': 'BERAS KEDAH · LAKSA KEDAH'}
SIG = {'A2-1': 'TIERED TENUN TABLE', 'A2-2': 'GOLD PINEAPPLE GRID', 'A2-3': 'TINGKAT TOWER', 'A2-4': 'LEMANG BAMBOO RACK', 'A1-1': 'SPICE DRAWER WALL',
       'A1-2': 'LABU SAYONG PENDANTS', 'A1-3': 'OVAL PORTAL CASE', 'A1-4': 'RICE BINS + GANTANG'}

def shopfront(ax, key, x0):
    k = SHOP[key]; nm, cap, b, km, col = ST[k]
    r = [x for x in M.ROOMS if x['key'] == key][0]; bm, b0, b1 = M.mid(key)
    W = round(2 * 12.5 * math.sin(math.radians((b1 - b0) / 2)), 2)
    H = 3.9; hp = 0.05
    # piers
    ax.add_patch(Rectangle((x0, 0), hp, H, fc='#D7DBDF', ec=INK, lw=0.5, zorder=3)); ax.add_patch(Rectangle((x0 + W - hp, 0), hp, H, fc='#D7DBDF', ec=INK, lw=0.5, zorder=3))
    for xx in (x0 + hp * 0.5, x0 + W - hp * 0.5): ax.plot([xx, xx], [0.1, 2.7], color=col, lw=2.0, zorder=4)
    cw = W - 2 * hp
    # screen + fascia
    pattern(ax, k, x0 + hp, 3.3, cw, 0.6, col)
    ax.add_patch(Rectangle((x0 + hp, 2.7), cw, 0.6, fc='#3B3330', ec=INK, lw=0.5, zorder=3))
    ax.text(x0 + W / 2, 3.07, key.replace('-', '') if False else ('KEDAI ' + key), color='white', fontsize=6.0, ha='center', va='center', fontweight='bold', zorder=5)
    ax.text(x0 + W / 2, 2.86, nm, color=tint(col, 0.2), fontsize=4.6, ha='center', va='center', fontweight='semibold', zorder=5)
    # glass: fixed pane + door leaf (1.0 clear)
    fixed = cw - 1.05
    ax.add_patch(Rectangle((x0 + hp, 0), fixed, 2.7, fc='#E4F1F6', ec=INK, lw=0.5, zorder=3))
    ax.add_patch(Rectangle((x0 + hp + 0.05, 0.0), fixed - 0.1, 0.9, fc='#F2EDE4', ec=INK, lw=0.4, zorder=3.5))
    ax.text(x0 + hp + fixed / 2, 0.45, 'DISPLAY\nCASE', fontsize=3.6, ha='center', va='center', color=INK, zorder=5)
    ax.add_patch(Rectangle((x0 + hp + fixed, 0), 1.05, 2.7, fc='#EEF6F9', ec=INK, lw=0.6, zorder=3))
    ax.plot([x0 + hp + fixed + 0.12] * 2, [0.9, 1.6], color=col, lw=2.2, zorder=5)
    ax.annotate('', xy=(x0 + hp + fixed - 0.25, 1.95), xytext=(x0 + hp + fixed + 0.35, 1.95), arrowprops=dict(arrowstyle='->', color=INK, lw=0.5), zorder=6)
    ax.text(x0 + hp + fixed + 0.53, 1.35, 'DOOR\n1000\nCLEAR', fontsize=3.5, ha='center', va='center', color=INK, zorder=5)
    # threshold
    ax.add_patch(Rectangle((x0, -0.08), W, 0.08, fc='#B08D3C', ec='none', zorder=3))
    # blade sign
    ax.add_patch(Rectangle((x0 - 0.12, 2.42), 0.08, 0.3, fc=col, ec=INK, lw=0.4, zorder=6))
    # width dim + labels
    ax.annotate('', xy=(x0, -0.42), xytext=(x0 + W, -0.42), arrowprops=dict(arrowstyle='<->', color=INK, lw=0.5))
    ax.text(x0 + W / 2, -0.55, f'{W * 1000:.0f}', fontsize=4.4, ha='center', va='top', color=INK)
    ax.text(x0 + W / 2, -0.95, f'{key} · {nm}', fontsize=5.2, ha='center', va='top', color=INK, fontweight='bold')
    ax.text(x0 + W / 2, -1.25, RANGE[key], fontsize=3.7, ha='center', va='top', color='#55606A')
    ax.text(x0 + W / 2, -1.5, 'SIGNATURE: ' + SIG[key], fontsize=3.7, ha='center', va='top', color='#55606A')
    ax.text(x0 + W / 2, -1.75, f'BRASS THRESHOLD: {b:.1f}° · {km} KM', fontsize=3.7, ha='center', va='top', color='#8A6A20')
    return W

def fig_shopfronts():
    fig = plt.figure(figsize=(16.5, 10.2), dpi=220)
    ax = fig.add_axes([0.02, 0.36, 0.96, 0.56])
    x = 0.4; gap = 0.55
    order = ['A2-1', 'A2-2', 'A2-3', 'A2-4', 'A1-1', 'A1-2', 'A1-3', 'A1-4']
    for i, k in enumerate(order):
        W = shopfront(ax, k, x); x += W + gap + (0.6 if i == 3 else 0)
    # height dims at left
    for z, t in ((0, '±0 (FFL +0.900)'), (2.7, '2700 DOOR HEAD'), (3.3, '3300 SHOP CEILING'), (3.9, '3900 ARCADE SOFFIT')):
        ax.plot([-0.25, 0.25], [z, z], color=INK, lw=0.5); ax.text(-0.3, z, t, fontsize=4.4, ha='right', va='center', color=INK)
    ax.text(-0.3, 3.6, 'STATE SCREEN\n(UNIQUE)', fontsize=4.4, ha='right', va='center', color='#B83A2E', fontweight='bold')
    ax.text(-0.3, 3.0, 'FASCIA SIGN BAND', fontsize=4.4, ha='right', va='center', color=INK)
    ax.text(-0.3, 1.35, 'GLASS ZONE:\nFIXED PANE +\nSLIDING LEAF', fontsize=4.4, ha='right', va='center', color=INK)
    ax.set_xlim(-2.4, x + 0.2); ax.set_ylim(-2.0, 4.4); ax.set_aspect('equal'); ax.axis('off')
    ax.text(0.4, 4.25, 'A2 · KUIH + SNACKS (123.6–166.5°)', fontsize=7, fontweight='bold', color=INK)
    ax.text(0.4 + sum(2 * 12.5 * math.sin(math.radians((M.mid(k)[2] - M.mid(k)[1]) / 2)) + gap for k in order[:4]) + 0.6, 4.25,
            'A1 · COOKING INGREDIENTS (256.8–303.7°)', fontsize=7, fontweight='bold', color=INK)
    # ---- radial section through a shop (A2-3 Melaka), R9 -> R24
    bx = fig.add_axes([0.06, 0.03, 0.9, 0.3])
    z0 = 0.9
    def R(x): return x
    col = ST['MLK'][4]
    # floors / slabs
    bx.add_patch(Rectangle((9.0, z0 - 0.3), 15.0, 0.3, fc='#B9BEC3', ec='none'))
    for a, b in ((9.5, 15.5), (17.0, 20.0), (21.5, 24.0)):
        bx.add_patch(Rectangle((a, 4.8), b - a, 0.6, fc='#B9BEC3', ec='none'))
    for a, b in ((15.5, 17.0), (20.0, 21.5)):
        bx.add_patch(Rectangle((a, 5.3), b - a, 0.06, fc='#F4F4EC', ec=INK, lw=0.4))
        bx.text((a + b) / 2, 5.55, 'OPAL\nROOFLIGHT', fontsize=4.2, ha='center', va='bottom', color=INK)
        for xx in np.linspace(a + 0.15, b - 0.15, 4): bx.annotate('', xy=(xx, 1.8), xytext=(xx, 5.25), arrowprops=dict(arrowstyle='->', color='#E8B523', lw=0.6, alpha=0.8))
    # shop ceiling
    for a, b in ((12.5, 15.5), (17.0, 20.0)): bx.plot([a, b], [z0 + 3.3, z0 + 3.3], color=INK, lw=0.6)
    # front kit
    bx.add_patch(Rectangle((12.45, z0), 0.1, 2.7, fc='#E4F1F6', ec=INK, lw=0.5))
    bx.add_patch(Rectangle((12.4, z0 + 2.7), 0.2, 0.6, fc='#3B3330', ec='none'))
    bx.add_patch(Rectangle((12.4, z0 + 3.3), 0.2, 0.6, fc=tint(col, 0.4), ec='none'))
    # store wall + store + back door
    bx.add_patch(Rectangle((21.15, z0), 0.12, 3.3, fc=col, ec=INK, lw=0.4))
    bx.plot([23.0, 23.0], [z0, z0 + 3.3], color=INK, lw=1.0)
    # furniture
    bx.add_patch(Rectangle((12.9, z0), 2.4, 0.9, fc='#F2EDE4', ec=INK, lw=0.4))
    for zz in (1.4, 1.9): bx.plot([13.1, 15.1], [z0 + zz, z0 + zz], color=INK, lw=0.5)
    bx.add_patch(Rectangle((15.7, z0), 1.0, 0.9, fc=tint(col, 0.5), ec=INK, lw=0.4))
    for i in range(4): bx.add_patch(Rectangle((15.85 + i * 0.05, z0 + 0.9 + i * 0.32), 0.7 - i * 0.1, 0.3, fc=col if i % 2 == 0 else tint(col, 0.5), ec=INK, lw=0.3))
    bx.add_patch(Rectangle((18.6, z0), 2.4, 0.9, fc='#F2EDE4', ec=INK, lw=0.4))
    # arcade + court edge + bridge people
    bx.plot([9.5, 9.5], [z0, z0 + 3.9], color=GREY, lw=0.6, ls='--')
    bx.add_patch(Rectangle((10.9, z0), 0.25, 3.9, fc='white', ec=INK, lw=0.4))
    for x_ in (13.8, 18.5): pass
    def person(x, z, h=1.65):
        bx.add_patch(Circle((x, z + h - 0.11), 0.11, fc='none', ec=INK, lw=0.5)); bx.plot([x, x], [z + 0.85, z + h - 0.22], color=INK, lw=0.6)
        bx.plot([x - 0.15, x, x + 0.15], [z, z + 0.85, z], color=INK, lw=0.6)
    person(10.2, z0); person(14.0, z0); person(19.7, z0); person(18.5, 5.4); person(13.6, 5.4)
    for xx, t in ((11.0, 'ARCADE\nR9.5–12.5'), (14.0, 'DISPLAY\nR12.5–15.5'), (16.25, 'LIGHT BAND 1\nSIGNATURE'), (18.9, 'PREP + CASHIER\nR17–21'), (20.6, 'LIGHT\nBAND 2'), (22.1, 'STORE\n7 m²')):
        bx.text(xx, -0.55, t, fontsize=4.6, ha='center', va='top', color=INK, fontweight='semibold')
    bx.text(18.5, 7.35, 'RING BRIDGE (L1 +5.400)', fontsize=4.6, ha='center', color=INK)
    bx.text(12.5, 7.35, 'INNER RING (L1)', fontsize=4.6, ha='center', color=INK)
    bx.text(22.7, 7.35, 'OUTER RING (L1)', fontsize=4.6, ha='center', color=INK)
    bx.text(21.0, z0 + 3.55, 'FEATURE\nBACK WALL', fontsize=4.2, ha='right', va='bottom', color=col, fontweight='bold')
    bx.text(12.3, z0 + 3.6, 'STATE SCREEN', fontsize=4.2, ha='right', va='center', color=col, fontweight='bold')
    bx.text(12.3, z0 + 3.0, 'FASCIA', fontsize=4.2, ha='right', va='center', color=INK)
    bx.text(23.1, z0 + 0.6, 'DOOR 900\nTO STREET', fontsize=4.0, ha='left', va='center', color=INK)
    bx.set_xlim(8.6, 24.6); bx.set_ylim(-1.4, 7.8); bx.set_aspect('equal'); bx.axis('off')
    bx.set_title('RADIAL SECTION THROUGH SHOP A2-3 (MELAKA): THE FOUR ZONES FOLLOW THE TWO ROOFLIGHT BANDS', fontsize=7.5, fontweight='bold', color=INK, loc='left')
    fig.text(0.02, 0.965, 'TITIK TEMU — SHOPFRONT KIT + ONE UNIQUE LAYER PER STATE', fontsize=12, fontweight='bold', color=INK)
    fig.text(0.02, 0.94, 'FRONT ELEVATIONS AT TRUE WIDTH (CHORD AT R12.5, 1:50 PROPORTION) · SAME FRAME, GLASS, FASCIA AND LIGHT FOR ALL · ONLY THE SCREEN PATTERN, ACCENT COLOUR, BACK WALL AND SIGNATURE DISPLAY CHANGE',
             fontsize=6.6, color='#55606A', fontweight='medium')
    fig.savefig(os.path.join(OUT, 'int_shopfronts.png'), facecolor='white'); plt.close(fig)

# ------------------------------------------------------------------------------------------------- signage family
def mini_map(ax, cx, cy, s, rot, here_b):
    """heads-up round map: rotated so the reader's gate is at the bottom"""
    def T(p):
        v = (np.array(p) - np.array(M.C)) * s; a = math.radians(rot); R_ = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        return R_ @ v + np.array([cx, cy])
    for r in M.ROOMS:
        if r['fl'] != 'GF': continue
        fc, st = theme(r)
        ax.add_patch(MP(np.array([T(c) for c in r['poly'].exterior.coords]), closed=True, fc=fc, ec='#3B3330', lw=0.2, zorder=4))
    ax.add_patch(Circle((cx, cy), M.R_COURT * s, fc=HOST2, ec='#3B3330', lw=0.3, zorder=4))
    for sp in SC.SPINES:
        p = T(M.P(25.5, sp['b'])); ax.text(*p, sp['k'], fontsize=2.6, ha='center', va='center', color='white', fontweight='bold', zorder=6)
    h = T(M.P(17.0, here_b)); ax.add_patch(Circle(h, 0.03, fc='#E4572E', ec='white', lw=0.4, zorder=7))
    ax.text(h[0], h[1] - 0.08, 'ANDA DI SINI\nYOU ARE HERE', fontsize=2.3, ha='center', va='top', color='white', fontweight='bold', zorder=7)

def fig_signs():
    fig = plt.figure(figsize=(16.5, 5.9), dpi=220)
    ax = fig.add_axes([0.01, 0.02, 0.98, 0.86]); ax.set_xlim(0, 16.5); ax.set_ylim(-0.75, 4.75); ax.set_aspect('equal'); ax.axis('off')
    BR = '#3B3330'
    def cap(x, t, sub):
        ax.text(x, -0.15, t, fontsize=6.4, ha='center', va='top', color=INK, fontweight='bold'); ax.text(x, -0.42, sub, fontsize=4.6, ha='center', va='top', color='#55606A')
    # scale bar (metres in elevation, 1 unit = 1 m for the totem and plates; gate marker shown at 1:4 of the rest)
    # 1 gate marker
    ax.add_patch(Rectangle((0.2, 3.6), 3.2, 1.0, fc='#E9ECEF', ec=INK, lw=0.5))
    ax.text(1.8, 4.22, 'SELATAN', fontsize=17, ha='center', va='center', color=BR, fontweight='bold')
    ax.text(1.8, 3.82, 'PINTU SELATAN · SOUTH GATE', fontsize=4.6, ha='center', va='center', color=BR, fontweight='semibold')
    for i, k in enumerate(('NSN', 'MLK', 'JHR')):
        ax.add_patch(Rectangle((0.2 + i * 3.2 / 3, 3.48), 3.2 / 3, 0.12, fc=ST[k][4], ec='none'))
        ax.text(0.2 + (i + 0.5) * 3.2 / 3, 3.3, ST[k][0], fontsize=4.0, ha='center', va='center', color=INK, fontweight='semibold')
    ax.plot([0.2, 3.4], [3.2, 3.2], color=GREY, lw=0.4)
    cap(1.8, '1 · GATE MARKER', 'CUT LETTERS ON CANOPY BEAM · ~600 HIGH · GATE STATES BELOW')
    ax.text(1.8, 2.7, 'SAME FOR TENGAH · UTARA · TIMUR\nONLY THE STATE STRIPES CHANGE', fontsize=4.6, ha='center', color='#55606A')
    # 2 totem x4 with heads-up maps (true 0.6 x 2.2 m)
    for i, sp in enumerate(SC.SPINES):
        x = 4.0 + i * 0.95
        ax.add_patch(FancyBboxPatch((x, 0.0), 0.6, 2.2, boxstyle='round,pad=0,rounding_size=0.05', fc=BR, ec=INK, lw=0.5))
        ax.text(x + 0.3, 2.06, sp['k'], fontsize=4.4, ha='center', va='center', color='white', fontweight='bold')
        ax.text(x + 0.3, 1.94, 'DIREKTORI · DIRECTORY', fontsize=2.4, ha='center', va='center', color=tint('#C9A27A', 0.2))
        mini_map(ax, x + 0.3, 1.5, 0.0108, -(180 - sp['b']) if False else (sp['b'] - 180), sp['b'])
        for j in range(9): ax.plot([x + 0.07, x + 0.53], [1.0 - j * 0.07, 1.0 - j * 0.07], color='#8B8079', lw=0.6)
        ax.text(x + 0.3, 0.27, 'ARAS G · 1 · 2', fontsize=2.6, ha='center', color='white')
    ax.text(5.9, 2.42, 'HEADS-UP MAPS: EACH TOTEM TURNS THE PLAN SO ITS OWN GATE IS AT THE BOTTOM', fontsize=4.6, ha='center', color='#B83A2E', fontweight='bold')
    cap(5.9, '2 · DIRECTORY TOTEMS (4 GATES)', '600 × 2200 · ROUND PLAN OF 3 LEVELS · SHOP LIST · FACILITIES')
    # 3 level sign
    x = 8.2
    ax.add_patch(Rectangle((x, 0.6), 1.2, 1.6, fc='white', ec=INK, lw=0.5))
    ax.text(x + 0.6, 1.62, '2', fontsize=40, ha='center', va='center', color=BR, fontweight='bold')
    ax.text(x + 0.6, 1.02, 'ARAS 2 · LEVEL 2', fontsize=5, ha='center', va='center', color=BR, fontweight='bold')
    ax.text(x + 0.6, 0.78, 'GALERI · SURAU · SERAMBI KELUARGA', fontsize=3.0, ha='center', va='center', color=BR)
    cap(x + 0.6, '3 · LIFT + STAIR LEVEL SIGN', 'FACING EVERY LIFT DOOR · C1 · C2 · C3')
    # 4 fascia + 5 blade
    x = 10.0
    ax.add_patch(Rectangle((x, 1.7), 2.3, 0.6, fc=BR, ec=INK, lw=0.5)); pattern(ax, 'MLK', x, 2.3, 2.3, 0.6, ST['MLK'][4])
    ax.text(x + 1.15, 2.07, 'KEDAI A2-3', fontsize=7, ha='center', va='center', color='white', fontweight='bold')
    ax.text(x + 1.15, 1.85, 'MELAKA · KUIH NYONYA', fontsize=3.8, ha='center', va='center', color=tint(ST['MLK'][4], 0.3))
    ax.add_patch(Rectangle((x + 0.2, 0.6), 0.6, 0.3, fc='white', ec=INK, lw=0.5)); ax.add_patch(Rectangle((x + 0.2, 0.6), 0.04, 0.3, fc=ST['MLK'][4], ec='none'))
    ax.text(x + 0.52, 0.75, 'A2-3', fontsize=5, ha='center', va='center', color=BR, fontweight='bold'); ax.plot([x + 0.2, x + 0.2], [0.9, 1.25], color=INK, lw=0.6)
    ax.text(x + 1.4, 0.75, '← BLADE SIGN\n600 × 300', fontsize=4.0, ha='left', va='center', color=INK)
    cap(x + 1.15, '4 + 5 · FASCIA + BLADE', 'PART OF THE SHOPFRONT KIT')
    # 6 room plate (300 x 150 drawn x2.5)
    x = 13.0
    ax.add_patch(Rectangle((x, 1.2), 0.75, 0.375, fc=BR, ec=INK, lw=0.5))
    ax.text(x + 0.45, 1.46, 'SURAU WANITA', fontsize=4.6, ha='center', va='center', color='white', fontweight='bold')
    ax.text(x + 0.45, 1.34, "WOMEN'S PRAYER ROOM", fontsize=3.0, ha='center', va='center', color=tint('#C9A27A', 0.3))
    for j in range(10): ax.add_patch(Circle((x + 0.2 + j * 0.05, 1.25), 0.008, fc='white', ec='none'))
    ax.add_patch(Circle((x + 0.1, 1.42), 0.05, fc='none', ec='white', lw=0.6))
    ax.text(x + 0.375, 1.0, 'RAISED LETTERS + BRAILLE\nLATCH SIDE · CENTRE ~1.5 M\n(CHECK MS 1184)', fontsize=3.8, ha='center', va='top', color=INK)
    cap(x + 0.375, '6 · ROOM PLATE', '300 × 150 (DRAWN 2.5×)')
    # 7 floor compass + 8 tactile
    x = 15.1
    ax.add_patch(Rectangle((x - 0.9, 1.0), 1.8, 0.9, fc='#D9DCDF', ec=INK, lw=0.4))
    ax.plot([x - 0.9, x + 0.9], [1.45, 1.45], color='#B08D3C', lw=2.0)
    ax.text(x, 1.62, 'KANGAR 414 KM · 323.6°', fontsize=3.8, ha='center', color='#8A6A20', fontweight='bold')
    ax.text(x, 1.18, 'BRASS INLAY ON THE BRIDGE', fontsize=3.4, ha='center', color=INK)
    for j in range(6): ax.add_patch(Rectangle((x - 0.9 + j * 0.3, 0.55), 0.28, 0.28, fc='#F2C14E', ec=INK, lw=0.3))
    for j in range(6):
        for q in range(3): ax.plot([x - 0.86 + j * 0.3, x - 0.66 + j * 0.3], [0.6 + q * 0.09, 0.6 + q * 0.09], color=INK, lw=0.5)
    ax.text(x, 0.42, 'TACTILE GUIDE PATH (MS 1184)', fontsize=3.6, ha='center', va='top', color=INK)
    cap(x, '7 + 8 · FLOOR', 'COMPASS INLAYS · TACTILE PATHS')
    fig.text(0.02, 0.955, 'TITIK TEMU — SIGNAGE + WAYFINDING FAMILY', fontsize=12, fontweight='bold', color=INK)
    fig.text(0.02, 0.925, 'BM FIRST AND LARGER · UPPERCASE · DARK BRONZE + WHITE · GATE COLOURS FOR DIRECTION, STATE COLOURS ONLY ON THEIR OWN ROOMS · STATUTORY EXIT + FIRE SIGNS KEPT SEPARATE (BOMBA)',
             fontsize=6.6, color='#55606A', fontweight='medium')
    fig.savefig(os.path.join(OUT, 'int_signage.png'), facecolor='white'); plt.close(fig)

if __name__ == '__main__':
    fig_plans(); fig_shopfronts(); fig_signs(); print('ok')
