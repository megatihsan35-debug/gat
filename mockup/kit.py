# -*- coding: utf-8 -*-
import sys, math, numpy as np
sys.path.insert(0, '/home/claude/mock'); sys.path.insert(0, '/home/claude/crit1')
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('LS', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LSB', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white
from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union
from terrain import LAYERS, NL, BOARD, XL, XR, YB, YT, LINES, FACES, LEVELS
from building import *
import site_el as SE
from geom import SITE, SITE_POLY

W, H_ = 210, 297
INK = Color(0.12, 0.16, 0.18); MUTE = Color(0.38, 0.40, 0.42); TERRA = Color(0.71, 0.29, 0.17); BLUE = Color(0.17, 0.36, 0.70)
GREYF = Color(0.86, 0.85, 0.82); RED = Color(0.78, 0.12, 0.12); GREEN = Color(0.25, 0.55, 0.25); LIGHT = Color(0.95, 0.94, 0.91)
OUT = '/home/claude/mock/out/TitikTemu_Mockup_Kit_1-500_A4.pdf'
c = canvas.Canvas(OUT, pagesize=(W * mm, H_ * mm))
c.setTitle('Titik Temu — 1:500 mock-up model kit'); c.setAuthor('Megat Muhammad Ihsan')
PAGE = [0]
def T(x, y, s, size=8, font='LS', col=INK, anchor='l'):
    c.setFont(font, size); c.setFillColor(col)
    f = {'l': c.drawString, 'c': c.drawCentredString, 'r': c.drawRightString}[anchor]
    f(x * mm, y * mm, s)
def para(x, y, w, s, size=8, lead=1.32, font='LS', col=INK):
    c.setFont(font, size); c.setFillColor(col)
    from reportlab.pdfbase.pdfmetrics import stringWidth
    yy = y
    for raw in s.split('\n'):
        words = raw.split(' '); line = ''
        for wd in words:
            t = (line + ' ' + wd).strip()
            if stringWidth(t, font, size) / mm > w and line:
                c.drawString(x * mm, yy * mm, line); yy -= size * lead * 0.3528; line = wd
            else: line = t
        c.drawString(x * mm, yy * mm, line); yy -= size * lead * 0.3528
    return yy
def header(title, sub, sheet):
    PAGE[0] += 1
    c.setFillColor(INK); c.rect(10 * mm, 284 * mm, 190 * mm, 0.5 * mm, stroke=0, fill=1)
    T(10, 287, 'TITIK TEMU', 12, 'LSB'); T(42, 287, title, 9, 'LSB', TERRA)
    T(200, 290.5, sheet, 7, 'LSB', INK, 'r'); T(200, 287, sub, 6.5, 'LS', MUTE, 'r')
def footer():
    T(10, 6, 'TITIK TEMU · 1:500 MOCK-UP KIT · PRINT AT 100 % / ACTUAL SIZE ON A4 · MEGAT MUHAMMAD IHSAN · BAAR 3101 SECTION 8', 5.8, 'LS', MUTE)
    T(200, 6, f'PAGE {PAGE[0]}', 6, 'LSB', INK, 'r')
def checkbar(x, y, vertical=False):
    c.setStrokeColor(INK); c.setLineWidth(0.3)
    if vertical:
        c.setFillColor(INK)
        for i in range(5):
            if i % 2 == 0: c.rect(x * mm, (y + i * 10) * mm, 2 * mm, 10 * mm, stroke=0, fill=1)
        c.rect(x * mm, y * mm, 2 * mm, 50 * mm, stroke=1, fill=0)
        c.saveState(); c.translate((x + 5) * mm, y * mm); c.rotate(90); T(0, 0, 'MUST MEASURE 50 MM', 5.5, 'LSB'); c.restoreState()
    else:
        c.setFillColor(INK)
        for i in range(5):
            if i % 2 == 0: c.rect((x + i * 10) * mm, y * mm, 10 * mm, 2 * mm, stroke=0, fill=1)
        c.rect(x * mm, y * mm, 50 * mm, 2 * mm, stroke=1, fill=0)
        T(x, y - 3.2, 'PRINT CHECK: THIS BAR MUST MEASURE 50 MM', 5.5, 'LSB')
def scalebar(x, y):
    c.setStrokeColor(INK); c.setLineWidth(0.3); c.setFillColor(INK)
    for i, (a, b) in enumerate([(0, 5), (5, 10), (10, 20), (20, 50)]):
        if i % 2 == 0: c.rect((x + a * 2) * mm, y * mm, (b - a) * 2 * mm, 1.6 * mm, stroke=0, fill=1)
    c.rect(x * mm, y * mm, 100 * mm, 1.6 * mm, stroke=1, fill=0)
    for v in (0, 5, 10, 20, 50): T(x + v * 2, y + 2.4, str(v), 5.5, 'LS', INK, 'c')
    T(x + 102, y + 0.2, 'M  · SCALE 1:500', 5.5, 'LSB')
def north(x, y, s=1.0):
    p = c.beginPath(); p.moveTo(x * mm, (y + 7 * s) * mm); p.lineTo((x - 2.2 * s) * mm, y * mm); p.lineTo(x * mm, (y + 1.6 * s) * mm); p.close()
    c.setFillColor(INK); c.drawPath(p, stroke=0, fill=1)
    p = c.beginPath(); p.moveTo(x * mm, (y + 7 * s) * mm); p.lineTo((x + 2.2 * s) * mm, y * mm); p.lineTo(x * mm, (y + 1.6 * s) * mm); p.close()
    c.setStrokeColor(INK); c.setLineWidth(0.3); c.drawPath(p, stroke=1, fill=0); T(x, y + 8 * s, 'N', 6 * s, 'LSB', INK, 'c')
# ---------- geometry drawing
class Map:
    def __init__(self, ox, oy, x0, y0, s=2.0, clip=None): self.ox, self.oy, self.x0, self.y0, self.s, self.clip = ox, oy, x0, y0, s, clip
    def P(self, x, y): return ((self.ox + (x - self.x0) * self.s) * mm, (self.oy + (y - self.y0) * self.s) * mm)
    def poly(self, g, stroke=INK, fill=None, lw=0.35, dash=None, alpha=1):
        if g is None or g.is_empty: return
        if self.clip is not None: g = g.intersection(self.clip)
        for gg in getattr(g, 'geoms', [g]):
            if gg.geom_type != 'Polygon' or gg.is_empty: continue
            p = c.beginPath()
            for ring in [gg.exterior] + list(gg.interiors):
                xy = list(ring.coords); p.moveTo(*self.P(*xy[0]))
                for q in xy[1:]: p.lineTo(*self.P(*q))
                p.close()
            c.setLineWidth(lw); c.setStrokeColor(stroke or black); c.setDash(*(dash or ([], 0)))
            if fill is not None: c.setFillColor(fill); c.setFillAlpha(alpha)
            c.drawPath(p, stroke=1 if stroke else 0, fill=1 if fill is not None else 0, fillMode=0)
            c.setFillAlpha(1); c.setDash([], 0)
    def line(self, g, stroke=INK, lw=0.3, dash=None):
        if g.geom_type in ('Polygon', 'MultiPolygon'): g = g.boundary
        if self.clip is not None: g = g.intersection(self.clip)
        if g.is_empty: return
        c.setLineWidth(lw); c.setStrokeColor(stroke); c.setDash(*(dash or ([], 0)))
        for gg in getattr(g, 'geoms', [g]):
            if gg.geom_type not in ('LineString', 'LinearRing') or gg.is_empty: continue
            xy = list(gg.coords); p = c.beginPath(); p.moveTo(*self.P(*xy[0]))
            for q in xy[1:]: p.lineTo(*self.P(*q))
            c.drawPath(p, stroke=1, fill=0)
        c.setDash([], 0)
    def cross(self, x, y, r=2.5, lab=None, col=INK):
        if self.clip is not None and not self.clip.buffer(0.5).contains(Point(x, y)): return
        X, Y = self.P(x, y); c.setStrokeColor(col); c.setLineWidth(0.3)
        c.line(X - r * mm, Y, X + r * mm, Y); c.line(X, Y - r * mm, X, Y + r * mm); c.circle(X, Y, r * 0.45 * mm, stroke=1, fill=0)
        if lab: T(X / mm + 1.2, Y / mm + 1.2, lab, 4.8, 'LSB', col)
    def text(self, x, y, s, size=5.5, col=INK, anchor='c', font='LSB'):
        if self.clip is not None and not self.clip.contains(Point(x, y)): return
        X, Y = self.P(x, y); T(X / mm, Y / mm, s, size, font, col, anchor)
# ---------- context + features
import cv2
Hm = np.load('/home/claude/mock/H.npy')
def ph(box_): return Polygon(cv2.perspectiveTransform(np.array([box_], float), Hm)[0])
LV = {k: v for k, v in LAYERS.items()}
CX = {'CX1': ('ISTANA SRI UDARA', ph([(105, 470), (205, 470), (205, 570), (105, 570)]), 9, [('FOAM 5 MM', 2)], 'APPROX. 5 M MASSING'),
      'CX2': ('AD FUTSAL COURT', ph([(470, 280), (760, 265), (785, 440), (500, 455)]).intersection(LV[5]).difference(SITE_POLY.buffer(2)), 5, [('FOAM 5 MM', 3)], 'APPROX. 7.5 M MASSING'),
      'CX3': ('NEIGHBOUR BLOCK (N)', ph([(400, 290), (445, 290), (470, 410), (415, 410)]).intersection(BOARD), 5, [('FOAM 5 MM', 2)], 'APPROX. 5 M MASSING'),
      'CX4': ('TENNIS COURT', Polygon([(88.9, 61.0), (98.9, 61.0), (103.7, 1.5), (93.7, 1.5)]), 4, [('GREYBOARD 2 MM', 1)], 'FLAT COURT, DRAW THE COURT LINES')}
ROAD_S = Polygon([tuple(SE.road_pt(-60) - SE.N_IN * 0.5), tuple(SE.road_pt(170) - SE.N_IN * 0.5), tuple(SE.road_pt(170) - SE.N_IN * 11), tuple(SE.road_pt(-60) - SE.N_IN * 11)])
J = LINES['J']; jv = np.array(J[1]) - np.array(J[0]); jv /= np.linalg.norm(jv); jn = np.array([-jv[1], jv[0]])
JI = Polygon([tuple(np.array(J[0])), tuple(np.array(J[1])), tuple(np.array(J[1]) + jn * 6.0), tuple(np.array(J[0]) + jn * 6.0)])
if JI.centroid.x > np.mean([J[0][0], J[1][0]]): JI = Polygon([tuple(np.array(J[0])), tuple(np.array(J[1])), tuple(np.array(J[1]) - jn * 6.0), tuple(np.array(J[0]) - jn * 6.0)])
PODIUM = PIECES[0][2]
FEAT4 = dict(drive=SE.DRIVE, plaza=SE.PLAZA_SE, garden=SE.GARDEN_N, yard=SE.YARD)
REG = [(XL + 2, YB + 2), (XL + 2, YT - 2), (XR - 2, YB + 2), (XR - 2, YT - 2), (55, YB + 2), (55, YT - 2), (55, 30), (XL + 2, 30), (XR - 2, 30)]
LAYER_INFO = {1: 'RIVER-SIDE STEP', 2: 'ROAD (EAST) LEVEL', 3: 'ROAD (WEST) LEVEL', 4: 'SITE LEVEL ±0.000 — BUILDING SITS HERE', 5: 'FUTSAL / NORTH TERRACE (+1 M)',
              6: 'NORTH WEDGE (+2 M)', 7: 'ISTANA SLOPE (+3 M)', 8: 'ISTANA SLOPE (+4 M)', 9: 'ISTANA PLATEAU (+5 M)'}
HALVES = {'WEST': (XL, 57.0), 'EAST': (53.0, XR)}
LAYER_INFO = {1: ('−3 M', 'LOWEST ROAD (EAST) — STEP TO RIVER SIDE'), 2: ('−2 M', 'ROAD STEP'), 3: ('−1 M', 'JALAN TOK MUDA AWANG NGAH (WEST)'),
              4: ('±0 M', 'SITE LEVEL — BUILDING, TENNIS COURT, JALAN IBRAHIM'), 5: ('+1 M', 'NORTH TERRACE — FUTSAL COURT'), 6: ('+2 M', 'NORTH WEDGE + ISTANA SLOPE'),
              7: ('+3 M', 'ISTANA SLOPE'), 8: ('+4 M', 'ISTANA SLOPE'), 9: ('+5 M', 'ISTANA PLATEAU')}
def dot(M, p, lab, col=TERRA, size=4.6):
    X, Y = M.P(*p); c.setFillColor(col); c.circle(X, Y, 0.55 * mm, stroke=0, fill=1)
    if lab: T(X / mm + 0.9, Y / mm + 0.8, lab, size, 'LSB', col)
def exposed(k): return LAYERS[k].difference(LAYERS[k + 1]) if k < NL else LAYERS[k]
def site_page(k, half):
    hx0, hx1 = HALVES[half]; clip = box(hx0, YB, hx1, YT)
    piece = LAYERS[k].intersection(clip)
    if piece.area < 1: return False
    header(f'SITE LAYER {k} OF {NL} · {half} HALF · 1:500', 'TRACE + CUT · GREYBOARD 2 MM', f'SITE L{k}-{half[0]}')
    M = Map(10, 12, hx0, YB, 2.0, clip)
    c.setFillColor(white); c.rect(10 * mm, 12 * mm, (hx1 - hx0) * 2 * mm, (YT - YB) * 2 * mm, stroke=0, fill=1)
    ov = box(53, YB, 57, YT).intersection(clip); M.poly(ov, None, LIGHT)
    M.poly(piece, INK, GREYF, 0.45)
    if k < NL: M.poly(LAYERS[k + 1], BLUE, None, 0.3, ([1.6, 1.0], 0))
    M.poly(clip, MUTE, None, 0.25)
    M.line(Polygon(SITE), RED, 0.35, ([2.2, 1.2], 0))
    ex = exposed(k)
    pen = Color(0.35, 0.35, 0.35)
    if k in (1, 2, 3): M.line(ROAD_S.intersection(ex).boundary.intersection(ex.buffer(-0.3)), pen, 0.25, ([0.8, 0.8], 0))
    if k == 4:
        M.line(JI.intersection(ex).boundary.intersection(ex.buffer(-0.3)), pen, 0.25, ([0.8, 0.8], 0))
        for nm, g in FEAT4.items(): M.line(g, pen, 0.2, ([0.6, 0.8], 0))
        for r in RIBS: M.line(r['poly'], GREEN, 0.25, ([0.6, 0.6], 0))
        M.poly(PODIUM, BLUE, Color(0.85, 0.9, 1.0), 0.45, ([2.5, 1.0, 0.6, 1.0], 0), alpha=0.6)
        M.cross(*B, 2.2, 'B', BLUE); M.cross(*S, 2.2, 'S', BLUE)
        pc = PODIUM.intersection(clip.buffer(-12))
        if not pc.is_empty:
            cx_, cy_ = pc.representative_point().coords[0]; M.text(cx_, cy_ - 4, 'B1 PODIUM HERE', 5.5, BLUE)
        for i, r in enumerate(sorted(RIBS, key=lambda r: ['TENGAH', 'UTARA', 'TIMUR', 'SELATAN'].index(r['k']))):
            for tt, p, z in r['posts']:
                if clip.contains(Point(p)): dot(M, p, '', GREEN, 4)
            mid = LineString(r['cl']).interpolate(0.5, normalized=True).coords[0]
            if clip.buffer(-3).contains(Point(mid)): M.text(mid[0] + 3, mid[1], f'R{i + 1}', 5, GREEN)
        M.poly(CX['CX4'][1], pen, None, 0.3, ([1.2, 0.8], 0)); xx, yy = CX['CX4'][1].representative_point().coords[0]; M.text(xx, yy, 'CX4', 5, pen)
        pass
    for x, y, dd in SE.TREES + [(B[0], B[1], 5)]:
        top = max([kk for kk in range(1, NL + 1) if LAYERS[kk].contains(Point(x, y))] or [0])
        if top == k and clip.contains(Point(x, y)):
            X, Y = M.P(x, y); c.setStrokeColor(GREEN); c.setFillColor(GREEN); c.setLineWidth(0.25); c.circle(X, Y, dd * mm, stroke=1, fill=0); c.circle(X, Y, 0.35 * mm, stroke=0, fill=1)
    if k == 4:
        rx = (hx0 + hx1) / 2; M.text(rx, float(SE.road_pt(rx)[1]) - 6.5, 'JALAN TOK MUDA AWANG NGAH (DRAW ON L1–L3)', 4.6, pen, font='LS')
    if k == 5:
        for key in ('CX2', 'CX3'):
            g = CX[key][1]; M.poly(g, pen, None, 0.3, ([1.2, 0.8], 0)); xx, yy = g.representative_point().coords[0]; M.text(xx, yy, key + ' ' + CX[key][0].split(' (')[0], 5, pen)
    if k == 9:
        g = CX['CX1'][1]; M.poly(g, pen, None, 0.3, ([1.2, 0.8], 0)); xx, yy = g.representative_point().coords[0]; M.text(xx, yy, 'CX1 ISTANA', 5, pen)
    for g in getattr(piece, 'geoms', [piece]):
        if g.area < 8: continue
        x, y = g.representative_point().coords[0]
        M.text(x, y, f'L{k}', 11, INK)
    for i, (x, y) in enumerate(REG):
        if clip.contains(Point(x, y)): M.cross(x, y, 2.8, f'R{i + 1}', TERRA)
    # side column
    sx = 10 + (hx1 - hx0) * 2 + 5; sw = 200 - sx
    T(sx, 268, f'L{k}', 30, 'LSB', INK); T(sx, 261, f'OF {NL}', 8, 'LSB', MUTE)
    T(sx, 254, half + ' HALF', 8, 'LSB', TERRA)
    lv, nm = LAYER_INFO[k]
    y = para(sx, 247, sw, f'LEVEL {lv}', 7, font='LSB')
    y = para(sx, y - 0.5, sw, nm, 6.2)
    y = para(sx, y - 2, sw, 'GREYBOARD 2 MM\nCUT 1 PIECE', 7, font='LSB', col=TERRA)
    y = para(sx, y - 2, sw, ('Tape the WEST + EAST halves together first (match R crosses in the shaded strip), then trace the whole outline as one piece.' if k <= 5 else 'This layer is only on the west half.'), 6.2)
    ly = y - 4
    def leg(yy, kind, s):
        X = sx * mm
        if kind == 'cut':
            c.setFillColor(GREYF); c.setStrokeColor(INK); c.setLineWidth(0.45); c.rect(X, (yy - 0.6) * mm, 6 * mm, 2.6 * mm, stroke=1, fill=1)
        elif kind == 'next':
            c.setStrokeColor(BLUE); c.setLineWidth(0.3); c.setDash(1.6 * mm, 1 * mm); c.line(X, (yy + 0.7) * mm, X + 6 * mm, (yy + 0.7) * mm); c.setDash([], 0)
        elif kind == 'pen':
            c.setStrokeColor(Color(0.35, 0.35, 0.35)); c.setLineWidth(0.25); c.setDash(0.8 * mm, 0.8 * mm); c.line(X, (yy + 0.7) * mm, X + 6 * mm, (yy + 0.7) * mm); c.setDash([], 0)
        elif kind == 'site':
            c.setStrokeColor(RED); c.setLineWidth(0.35); c.setDash(2.2 * mm, 1.2 * mm); c.line(X, (yy + 0.7) * mm, X + 6 * mm, (yy + 0.7) * mm); c.setDash([], 0)
        elif kind == 'reg':
            c.setStrokeColor(TERRA); c.setLineWidth(0.3); c.line(X + 3 * mm, (yy - 0.8) * mm, X + 3 * mm, (yy + 2.2) * mm); c.line(X + 1.5 * mm, (yy + 0.7) * mm, X + 4.5 * mm, (yy + 0.7) * mm)
        return para(sx + 7.5, yy + 0.2, sw - 7.5, s, 5.6)
    ly = leg(ly, 'cut', 'CUT LINE · grey = this layer') - 1.5
    if k < NL: ly = leg(ly, 'next', f'L{k + 1} sits here (do not cut)') - 1.5
    ly = leg(ly, 'site', 'Site boundary (draw)') - 1.5
    ly = leg(ly, 'pen', 'Pen line only (roads, paths)') - 1.5
    ly = leg(ly, 'reg', 'Registration cross R1–R9') - 1.5
    checkbar(sx + 1, 40, vertical=True)
    T(sx, 33, '1 M = 2 MM', 6.5, 'LSB')
    north(sx + 20, 22, 1.2)
    footer(); c.showPage(); return True
