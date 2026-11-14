"""Interior plan layouts: each space tinted by the state it carries, the 11 true-bearing lines from the court tree."""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from matplotlib import font_manager as fm
from shapely.geometry import Polygon
from shapely.ops import unary_union
import geom as g
from geom import ROOMS, B, S, d, mod, sector, R_VER, R_OUT, R_COURT

ST = {'KEL': ('Kelantan', 'Kota Bharu', 356.2, 298, '#3456D6'), 'TRG': ('Terengganu', 'K. Terengganu', 20.9, 224, '#11A89A'),
      'PHG': ('Pahang', 'Kuantan', 68.4, 108, '#6FB3D2'), 'JHR': ('Johor', 'Johor Bahru', 145.9, 263, '#E8B523'),
      'MLK': ('Melaka', 'Melaka', 187.6, 141, '#B83A2E'), 'NSN': ('N. Sembilan', 'Seremban', 213.3, 96, '#9A6A45'),
      'SGR': ('Selangor', 'Shah Alam', 247.3, 108, '#8CC63F'), 'PRK': ('Perak', 'Ipoh', 311.0, 195, '#C9A27A'),
      'PNG': ('P. Pinang', 'George Town', 313.4, 318, '#E46F8C'), 'KDH': ('Kedah', 'Alor Setar', 322.7, 374, '#4E8F3A'),
      'PLS': ('Perlis', 'Kangar', 323.6, 414, '#F28C28')}
NEU, GUEST = '#E4E1DA', '#F6E7CF'
SPACE = {  # room label -> (state key or None, display name)
    'A2-1': ('KEL', 'Kelantan stall'), 'A2-2': ('TRG', 'Terengganu stall'), 'A2-3': ('G', 'Tamu pod'), 'A2-4': ('G', 'Tamu pod'),
    'A1-1': ('JHR', 'Johor stall'), 'A1-2': ('G', 'Tamu pod'), 'A1-3': ('G', 'Tamu pod'), 'A1-4': ('MLK', 'Melaka stall'),
    'CAFÉ': ('PRK', 'Café (Perak)'), 'SERVERY': ('PRK', ''), 'KITCHEN': (None, ''), 'LOBBY': ('PLS', 'Lobby Simpul'),
    'GALLERY': ('PNG', 'Gallery Peta Rasa'), 'MULTIPURPOSE HALL': ('KDH', 'Dapur Rewang'), 'FAMILY WAITING': ('NSN', 'Family serambi')}
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def at(C, r, b): return np.array(C) + d(b) * r
def fillp(ax, p, fc, ec='#2b2b2b', lw=0.6, z=2, alpha=1):
    for q in ([p] if p.geom_type == 'Polygon' else list(p.geoms)):
        ax.add_patch(MP(np.array(q.exterior.coords), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))
        for h in q.interiors: ax.add_patch(MP(np.array(h.coords), closed=True, fc='white', ec=ec, lw=lw, zorder=z + 0.1))

def tint(hex_, k=0.62):
    c = np.array(matplotlib.colors.to_rgb(hex_)); return tuple(c + (1 - c) * k)

def draw(level, out):
    fig = plt.figure(figsize=(16, 10), dpi=150); ax = fig.add_axes([0, 0, 1, 1]); ax.set_aspect('equal'); ax.axis('off')
    fig.patch.set_facecolor('#FBFAF7')
    if level == 'GF':
        fillp(ax, Polygon(g.COURT.exterior.coords), tint(ST['PHG'][4], 0.8), '#9aa', 0.6, 1)
        fillp(ax, g.VER, '#F1EEE8', '#bbb', 0.4, 1)
        for nm, (b0, b1), k in (('Timur gate', mod(9), 'PHG'), ('Selatan gate', mod(17), 'NSN'), ('Serambi Tengah', mod(19), 'SGR')):
            fillp(ax, sector(B, R_VER, R_OUT, b0, b1), tint(ST[k][4], 0.55), '#555', 0.6, 2)
            c = at(B, (R_VER + R_OUT) / 2, (b0 + b1) / 2)
            ax.text(*c, nm, fontsize=7.5, ha='center', va='center', rotation=0, zorder=9, color='#22282B', fontweight='bold')
    for r in ROOMS:
        if r['level'] != level or r['zone'] == 'open': continue
        k, nm = SPACE.get(r['label'], (None, ''))
        fc = tint(ST[k][4], 0.5) if k in ST else (GUEST if k == 'G' else (NEU if r['zone'] in ('pub', 'semi') else '#F4F2EE'))
        fillp(ax, r['poly'], fc, '#3a3a3a', 0.7, 3)
        q = r['poly'] if r['poly'].geom_type == 'Polygon' else max(r['poly'].geoms, key=lambda a: a.area)
        from shapely.ops import polylabel
        c = polylabel(q, 0.05)
        lab = nm or (r['label'] if r['label'] not in ('prep', 'store', 'JAN', 'J', '') else '')
        if lab and q.area > 6:
            ax.text(c.x, c.y, lab.replace(' ', '\n') if len(lab) > 12 else lab, fontsize=6.6 if q.area < 20 else 7.6, ha='center', va='center', zorder=9, color='#22282B',
                    fontweight='bold' if nm else 'normal', linespacing=1.0)
    # core
    fillp(ax, g.core_block, '#CFCAC0', '#333', 0.8, 4)
    # compass lines
    if level == 'GF':
        C0 = B
        for k, (st, cap, br, km, hx) in ST.items():
            p0, p1 = at(C0, 1.4, br), at(C0, R_OUT + 3.0, br)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=hx, lw=1.6, zorder=8, solid_capstyle='round')
            ax.plot(*p1, 'o', color=hx, ms=4.5, zorder=8)
        # labels fanned so Utara four do not collide
        lab_r = {k: R_OUT + 4.2 for k in ST}
        offs = {'PRK': -7, 'PNG': -2.5, 'KDH': 2.5, 'PLS': 7}
        for k, (st, cap, br, km, hx) in ST.items():
            bb = br + offs.get(k, 0); p = at(C0, lab_r[k] + (2.5 if k in offs else 0), bb)
            ha = 'left' if 0 < (bb % 360) < 180 else 'right'
            if k in offs:
                q = at(C0, R_OUT + 3.0, br); ax.plot([q[0], p[0]], [q[1], p[1]], color=hx, lw=0.6, zorder=8)
            ax.text(*p, f'{st}\n{br:.1f}° · {km} km', fontsize=7, color='#22282B', ha=ha, va='center', zorder=9,
                    bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=hx, lw=1))
        ax.add_patch(plt.Circle(B, 1.5, fc='#5b8f45', ec='#2b2b2b', lw=0.6, zorder=8))
        ax.text(B[0], B[1] - 2.6, 'court tree\n(origin of the 11 lines)', fontsize=6.5, ha='center', va='top', zorder=9, color='#22282B')
        xl, yl = (14, 96), (-14, 50)
    else:
        xl, yl = (16, 92), (-6, 48)
    # north arrow + scale
    nx, ny = xl[0] + 4, yl[1] - 6
    ax.annotate('', xy=(nx, ny + 3), xytext=(nx, ny - 1), arrowprops=dict(arrowstyle='-|>', color='#22282B', lw=1.2))
    ax.text(nx, ny + 3.6, 'N', ha='center', fontsize=10, fontweight='bold')
    sx, sy = xl[0] + 2, yl[0] + 3
    for i in range(5): ax.add_patch(plt.Rectangle((sx + i * 2, sy), 2, 0.5, fc='#22282B' if i % 2 == 0 else 'white', ec='#22282B', lw=0.6))
    ax.text(sx, sy - 1.3, '0', fontsize=7); ax.text(sx + 10, sy - 1.3, '10 m', fontsize=7)
    ax.set_xlim(*xl); ax.set_ylim(*yl)
    fig.savefig(out, facecolor=fig.get_facecolor()); plt.close(fig)

draw('GF', '/home/claude/crit1/out/int/plan_gf_int.png')
draw('L1', '/home/claude/crit1/out/int/plan_l1_int.png')
print('ok')
