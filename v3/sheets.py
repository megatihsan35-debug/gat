"""A0 sheet frame, title block, legends, north arrow, scale bars, key plan. All paper mm. Text uppercase (board rule)."""
import math, datetime
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from cad import Drawing, Sheet, INK
import plan3 as M
from plan3 import C, P, d, SC

W0, H0 = 1189.0, 841.0                    # A0 landscape
TB_X = 1030.0                             # title block strip from here to the right margin
DRAW_BOX = (22.0, 12.0, TB_X - 8.0, H0 - 12.0)
PROJECT = 'TITIK TEMU'
SUB = 'SIMPUL RASA SEMENANJUNG'
SITE_TXT = 'ESPLANADE LOCAL COMMERCIAL HUB · SITE C\nJALAN TOK MUDA AWANG NGAH, TEMERLOH, PAHANG\nLOT 10150 + FORMER TENNIS COURT · 6,418.6 M²'
COURSE = 'BAAR 3101 ARCHITECTURAL DESIGN 5\nSECTION 8 · KAED IIUM'
STUDENT = 'MEGAT MUHAMMAD IHSAN'
STAGE = 'DESIGN DEVELOPMENT (V3, POST CRIT 1)'
DATE = '15.11.2026'
ACCENT = '#C9690A'
NOTE = ('STUDENT DESIGN PROJECT. STRUCTURE, SERVICES AND FIRE LAYOUTS ARE DESIGN-STAGE PROPOSALS BASED ON UBBL 1984, '
        'MS 1184, MS 1525 AND COMMON BOMBA / SPAN PRACTICE; THEY ARE TO BE CHECKED BY C&S AND M&E ENGINEERS AND BOMBA BEFORE USE. '
        'DO NOT SCALE OFF A PRINT THAT IS NOT A0. ALL DIMENSIONS IN MILLIMETRES, LEVELS IN METRES.')

def frame(sheet_no, title, scale_txt, rev='00'):
    D = Drawing('frame', paper=True)
    D.poly(Polygon([(20, 10), (W0 - 10, 10), (W0 - 10, H0 - 10), (20, H0 - 10)]), 'X-TITL', edge=INK, lw=0.5)
    D.line([(TB_X, 10), (TB_X, H0 - 10)], 'X-TITL', lw=0.35)
    x0, x1 = TB_X + 6, W0 - 16
    y = H0 - 22
    D.text((x0, y), PROJECT, 'X-TITL', size=9.5, ha='left', va='top', weight='bold'); y -= 13
    D.text((x0, y), SUB, 'X-TITL', size=3.6, ha='left', va='top', color=ACCENT, weight='bold'); y -= 9
    D.text((x0, y), SITE_TXT, 'X-TITL', size=2.4, ha='left', va='top'); y -= 16
    D.line([(TB_X, y), (W0 - 10, y)], 'X-TITL', lw=0.25); y -= 6
    def field(label, value, size=3.0, bold=False, h=None):
        nonlocal y
        D.text((x0, y), label, 'X-TITL', size=1.8, ha='left', va='top', color='#6B7480'); y -= 3.6
        D.text((x0, y), value, 'X-TITL', size=size, ha='left', va='top', weight='bold' if bold else 'normal')
        y -= (h if h else size * 1.25 * (value.count('\n') + 1)) + 3.2
    field('COURSE', COURSE, 2.6)
    field('STUDENT', STUDENT, 3.0, True)
    field('STAGE', STAGE, 2.4)
    return D, (x0, x1), y

def title_bottom(D, sheet_no, title, scale_txt, rev='00', legend=None, notes=None, y_top=None):
    """bottom part of the title strip: legend / notes from y_top down, sheet title + number at the bottom"""
    x0, x1 = TB_X + 6, W0 - 16
    yb = 118
    D.line([(TB_X, yb), (W0 - 10, yb)], 'X-TITL', lw=0.35)
    D.text((x0, yb - 6), 'DRAWING TITLE', 'X-TITL', size=1.8, ha='left', va='top', color='#6B7480')
    D.text((x0, yb - 10), title, 'X-TITL', size=4.2, ha='left', va='top', weight='bold')
    D.line([(TB_X, 58), (W0 - 10, 58)], 'X-TITL', lw=0.25)
    cols = [('SCALE', scale_txt), ('DATE', DATE), ('REV', rev)]
    for i, (k, v) in enumerate(cols):
        xx = x0 + i * 46
        D.text((xx, 53), k, 'X-TITL', size=1.8, ha='left', va='top', color='#6B7480'); D.text((xx, 48.5), v, 'X-TITL', size=2.8, ha='left', va='top')
    D.line([(TB_X, 38), (W0 - 10, 38)], 'X-TITL', lw=0.25)
    D.text((x0, 33), 'SHEET', 'X-TITL', size=1.8, ha='left', va='top', color='#6B7480')
    D.text((x1, 15), sheet_no, 'X-TITL', size=13, ha='right', va='bottom', weight='bold')
    if y_top is not None:
        D.poly(Polygon([(x0 - 2, 124), (x1 + 2, 124), (x1 + 2, 124.01), (x0 - 2, 124.01)]), 'X-TITL', edge=None)
    return D

def wrap(s, n):
    out, line = [], ''
    for w in s.split(' '):
        if len(line) + len(w) + 1 > n and line: out.append(line); line = w
        else: line = (line + ' ' + w).strip()
    out.append(line); return '\n'.join(out)

def notes_block(D, x, y, head, items, width=34, size=1.9):
    D.text((x, y), head, 'X-TITL', size=2.4, ha='left', va='top', weight='bold'); y -= 5
    for it in items:
        t = wrap(it, width)
        D.text((x, y), t, 'X-TITL', size=size, ha='left', va='top'); y -= size * 1.32 * (t.count('\n') + 1) + 1.6
    return y

def legend_block(D, x, y, head, rows):
    """rows: (kind, style, label) kind in line/fill/circle/text"""
    D.text((x, y), head, 'X-TITL', size=2.4, ha='left', va='top', weight='bold'); y -= 6
    for kind, st, lab in rows:
        if kind == 'line': D.line([(x, y - 1), (x + 9, y - 1)], 'X-TITL', lw=st.get('lw', 0.35), color=st.get('color', INK), ls=st.get('ls', '-'))
        elif kind == 'fill': D.poly(Polygon([(x, y - 2.6), (x + 9, y - 2.6), (x + 9, y + 0.6), (x, y + 0.6)]), 'X-TITL', fill=st.get('fill'), edge=st.get('edge', INK), lw=0.15, hatch=st.get('hatch'))
        elif kind == 'circle': D.circle((x + 4.5, y - 1), st.get('r', 1.2), 'X-TITL', fill=st.get('fill'), edge=st.get('edge', INK), lw=0.2)
        elif kind == 'text': D.text((x + 4.5, y - 1), st.get('t', ''), 'X-TITL', size=st.get('size', 1.8), color=st.get('color', INK), weight='bold')
        D.text((x + 12, y - 1), lab, 'X-TITL', size=1.9, ha='left', va='center'); y -= 5.0
    return y - 2

def north(D, p, r=9.0):
    x, y = p
    D.circle(p, r, 'X-TITL', edge=INK, lw=0.25)
    D.poly(Polygon([(x, y + r * 0.95), (x - r * 0.32, y - r * 0.55), (x, y - r * 0.25)]), 'X-TITL', fill=INK, edge=INK, lw=0.1)
    D.poly(Polygon([(x, y + r * 0.95), (x + r * 0.32, y - r * 0.55), (x, y - r * 0.25)]), 'X-TITL', fill='white', edge=INK, lw=0.15)
    D.text((x, y + r + 3.5), 'N', 'X-TITL', size=3.4, weight='bold')
    q = np.array(p) + np.array([math.sin(math.radians(SC.QIBLA)), math.cos(math.radians(SC.QIBLA))]) * r * 1.25
    D.line([p, q], 'X-TITL', lw=0.3, color=ACCENT); D.text(q + np.array([-1.5, 2.6]), 'QIBLA 292.3°', 'X-TITL', size=1.6, color=ACCENT, ha='right')

def scale_bar(D, p, scale, metres=(0, 1, 2, 5, 10), label=None):
    x, y = p; k = 1000.0 / scale
    for i, (a, b) in enumerate(zip(metres[:-1], metres[1:])):
        D.poly(Polygon([(x + a * k, y), (x + b * k, y), (x + b * k, y + 1.6), (x + a * k, y + 1.6)]), 'X-TITL', fill=INK if i % 2 == 0 else 'white', edge=INK, lw=0.15)
    for m in metres: D.text((x + m * k, y - 2.4), f'{m}', 'X-TITL', size=1.7)
    D.text((x + metres[-1] * k + 3, y + 0.8), 'M', 'X-TITL', size=1.7, ha='left')
    D.text((x, y + 4.2), label or f'SCALE 1:{scale}', 'X-TITL', size=2.0, ha='left', weight='bold')

def drawing_title(D, p, num, title, scale, sub=None):
    x, y = p
    D.circle((x + 6, y), 6, 'X-TITL', edge=INK, lw=0.35); D.text((x + 6, y), num, 'X-TITL', size=3.6, weight='bold')
    D.line([(x + 14, y - 0.5), (x + 14 + max(60, len(title) * 2.9), y - 0.5)], 'X-TITL', lw=0.5)
    D.text((x + 14, y + 1.2), title, 'X-TITL', size=4.0, ha='left', va='bottom', weight='bold')
    D.text((x + 14, y - 2.0), (f'SCALE 1:{scale}' if scale else '') + (f'   ·   {sub}' if sub else ''), 'X-TITL', size=2.2, ha='left', va='top')

def key_plan(D, p, size=60.0, hilite=None, label='KEY PLAN'):
    """site outline + building, size = width in mm; hilite = shapely polygon (site metres) to tint"""
    b = SC.SITE.bounds; s = size / (b[2] - b[0]); x0, y0 = p
    T = lambda g: [((xx - b[0]) * s + x0, (yy - b[1]) * s + y0) for xx, yy in g]
    D.poly(Polygon(T(SC.SITE.exterior.coords)), 'X-TITL', fill='#F4F5F6', edge=INK, lw=0.25)
    D.poly(Polygon(T(SC.disc(M.R_ROOF).exterior.coords)), 'X-TITL', fill='white', edge=INK, lw=0.2)
    if hilite is not None:
        for g in getattr(hilite, 'geoms', [hilite]): D.poly(Polygon(T(g.exterior.coords)), 'X-TITL', fill=ACCENT, edge=None, alpha=0.55)
    D.text((x0, y0 + (b[3] - b[1]) * s + 3), label, 'X-TITL', size=2.0, ha='left', weight='bold')

def new_sheet(sheet_no, title, scale_txt, legend=None, notes=None):
    S = Sheet(W0, H0)
    D, (x0, x1), y = frame(sheet_no, title, scale_txt)
    title_bottom(D, sheet_no, title, scale_txt)
    return S, D, x0, y

SHEETS = []                                # (no, title, scale) filled by the builders for the drawing list
