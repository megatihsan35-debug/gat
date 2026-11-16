"""Crit 2 presentation boards: 13 x A2 portrait (420 x 594 mm), drawings at true scale, all text uppercase.
python3 crit2.py [01 02 ...]  ->  out/crit2/CRIT2_BOARD_XX.pdf + .png previews + TITIK-TEMU_CRIT2_A2_BOARDS.pdf"""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageFont
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle as MCircle, Polygon as MPoly
from cad import Sheet, Drawing, PT, INK
import crit2_draw as CD
import plan3 as M, scheme as SC, rings as RG, siteplan as ST, sections as SE
from plan3 import C, P, FFL, ROOMS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'crit2'); os.makedirs(OUT, exist_ok=True)
RND = os.path.join(HERE, 'out', 'render')
W, H = 420.0, 594.0
X0, X1 = 14.0, 406.0
BG = '#F4F1EA'; ACC = '#A8773A'; GREY = '#6B7178'; LGREY = '#B9BEC3'; PANEL = '#FBFAF6'
FD = '/usr/share/fonts/opentype/inter/'
_F = {}
def font(weight):
    f = {'normal': 'Inter-Regular.otf', 'bold': 'Inter-Bold.otf', 'semibold': 'Inter-SemiBold.otf', 'light': 'Inter-Light.otf', 'medium': 'Inter-Medium.otf'}[weight]
    if f not in _F: _F[f] = ImageFont.truetype(FD + f, 100)
    return _F[f]
def tw(s, size, weight='normal'): return font(weight).getlength(s) / 100.0 * size
def wrap(s, width, size, weight='normal'):
    out = []
    for para in s.split('\n'):
        words = para.split(' '); line = ''
        for w_ in words:
            t = (line + ' ' + w_).strip()
            if tw(t, size, weight) <= width or not line: line = t
            else: out.append(line); line = w_
        out.append(line)
    return out

class Board:
    def __init__(self, no, title, sub, total=13):
        self.no, self.title = no, title
        self.S = Sheet(W, H); ax = self.ax = self.S.ax
        ax.add_patch(Rectangle((0, 0), W, H, fc=BG, ec='none', zorder=-10))
        # header
        self.text(X0, 9.0, 'TITIK TEMU', 11.5, 'bold')
        self.text(X0, 23.2, 'SIMPUL RASA SEMENANJUNG  ·  ESPLANADE LOCAL COMMERCIAL HUB, SITE C, TEMERLOH, PAHANG', 3.3, 'medium', ACC)
        self.text(X1, 8.6, f'BOARD {no} / {total:02d}', 3.3, 'semibold', GREY, ha='right')
        self.text(X1, 14.0, title, 6.6, 'bold', ha='right')
        self.text(X1, 23.2, sub, 3.3, 'medium', GREY, ha='right')
        self.rule(X0, X1, 30.5, 0.6)
        # footer
        self.rule(X0, X1, 579.5, 0.3)
        self.text(X0, 582.5, 'BAAR 3101 ARCHITECTURAL DESIGN 5  ·  SECTION 8  ·  KAED IIUM  ·  SEM 1 2026/2027  ·  CRIT 2 (WEEK 10): DESIGN DEVELOPMENT', 2.9, 'medium', GREY)
        self.text(X1, 582.5, 'MEGAT MUHAMMAD IHSAN BIN MUHAMMAD NOOR  ·  STUDIO MASTER: AR. ADIB BIN MARUZIKI', 2.9, 'medium', GREY, ha='right')
    # ---------------------------------------------------------------- primitives (y measured from the TOP, mm)
    def text(self, x, y, s, size=4.0, weight='normal', color=INK, ha='left', width=None, lh=1.32, va='top', z=20, rot=0):
        s = s.upper()
        lines = wrap(s, width, size, weight) if width else s.split('\n')
        fw = {'normal': 'normal', 'bold': 'bold', 'semibold': 'semibold', 'light': 'light', 'medium': 'medium'}[weight]
        yy = y
        for ln in lines:
            self.ax.text(x, H - yy, ln, fontsize=size * PT, ha=ha, va='top' if va == 'top' else va, color=color, fontweight=fw, family='Inter', zorder=z, rotation=rot)
            yy += size * lh
        return yy
    def rule(self, x0, x1, y, lw=0.3, color=INK):
        self.ax.plot([x0, x1], [H - y, H - y], lw=lw * PT, color=color, zorder=5, solid_capstyle='butt')
    def rect(self, x, y, w, h, fc=PANEL, ec='none', lw=0.0, z=0):
        self.ax.add_patch(Rectangle((x, H - y - h), w, h, fc=fc, ec=ec, lw=lw * PT, zorder=z))
    def head(self, x, y, num, title, w, size=5.2):
        self.text(x, y, num, size, 'bold', ACC)
        self.text(x + tw(num, size, 'bold') + 3.0, y, title, size, 'bold')
        self.rule(x, x + w, y + size * 1.25, 0.25)
        return y + size * 1.25 + 4.0
    def para(self, x, y, s, w, size=4.0, weight='normal', color=INK, lh=1.36):
        return self.text(x, y, s, size, weight, color, width=w, lh=lh)
    def bullets(self, x, y, items, w, size=3.7, gap=1.6, color=INK, mark='—'):
        for it in items:
            self.text(x, y, mark, size, 'bold', ACC)
            y = self.text(x + 5.5, y, it, size, 'normal', color, width=w - 5.5) + gap
        return y
    def img(self, path, x, y, w, h=None, focus=(0.5, 0.5), z=1, alpha=None):
        im = Image.open(path)
        if h is not None:
            ar = w / h; iw, ih = im.size
            if iw / ih > ar:
                nw = int(ih * ar); x0 = int((iw - nw) * focus[0]); im = im.crop((x0, 0, x0 + nw, ih))
            else:
                nh = int(iw / ar); y0 = int((ih - nh) * focus[1]); im = im.crop((0, y0, iw, y0 + nh))
        else:
            h = w * im.size[1] / im.size[0]
        self.ax.imshow(np.asarray(im), extent=(x, x + w, H - y - h, H - y), zorder=z, interpolation='lanczos')
        return y + h
    def draw(self, D, scale, model_xy, cx, cy, clip=None):
        """place drawing D at 1:scale with model point model_xy at paper (cx, cy-from-top); clip = (x0, y0, x1, y1) from top"""
        cl = None
        if clip: cl = (clip[0], H - clip[3], clip[2], H - clip[1])
        self.S.place(D, scale, model_xy, (cx, H - cy), clip=cl)
    def dtitle(self, x, y, num, title, scale_txt, sub=None, w=None):
        r = 4.2
        st = (scale_txt + ('  ·  ' + sub if sub else '')).upper()
        bw = 2 * r + 5 + max(tw(title.upper(), 4.6, 'bold'), min(tw(st, 3.2, 'medium'), w or 999))
        self.rect(x - 1.5, y - 1.5, bw + 3, 15 + (3.2 * 1.32 if w and tw(st, 3.2, 'medium') > w else 0), fc=BG, z=19)
        self.ax.add_patch(MCircle((x + r, H - y - r), r, fc=INK, ec='none', zorder=21))
        self.ax.text(x + r, H - y - r, num, fontsize=4.0 * PT, ha='center', va='center', color='white', fontweight='bold', family='Inter', zorder=22)
        self.text(x + 2 * r + 3.0, y + 0.3, title, 4.6, 'bold')
        yy = self.text(x + 2 * r + 3.0, y + 6.4, scale_txt + ('  ·  ' + sub if sub else ''), 3.2, 'medium', GREY, width=w)
        return yy
    def north(self, x, y, r=7.0):
        ax = self.ax; cy = H - y
        ax.add_patch(MCircle((x, cy), r, fc='none', ec=INK, lw=0.25 * PT, zorder=21))
        ax.add_patch(MPoly([(x, cy + r * 0.95), (x - r * 0.38, cy - r * 0.55), (x, cy - r * 0.25)], closed=True, fc=INK, ec='none', zorder=22))
        ax.add_patch(MPoly([(x, cy + r * 0.95), (x + r * 0.38, cy - r * 0.55), (x, cy - r * 0.25)], closed=True, fc='white', ec=INK, lw=0.2 * PT, zorder=22))
        self.text(x, y - r - 5.2, 'N', 4.0, 'bold', ha='center')
    def scalebar(self, x, y, scale, metres=(0, 1, 2, 5, 10), label=True):
        k = 1000.0 / scale; ax = self.ax
        for i in range(len(metres) - 1):
            a, b = metres[i], metres[i + 1]
            ax.add_patch(Rectangle((x + a * k, H - y - 1.6), (b - a) * k, 1.6, fc=INK if i % 2 == 0 else 'white', ec=INK, lw=0.15 * PT, zorder=21))
        for m_ in metres: self.text(x + m_ * k, y + 2.6, f'{m_}', 2.8, 'medium', ha='center')
        if label: self.text(x + metres[-1] * k + 3, y - 0.6, 'M', 2.8, 'medium')
    def table(self, x, y, cols, rows, size=3.3, lh=5.0, head=True, bold_last=False, zebra=True):
        """cols = [(title, width, align)]"""
        yy = y
        if head:
            cx = x
            for t, w_, al in cols:
                self.text(cx + (w_ if al == 'right' else 0), yy, t, size * 0.92, 'bold', GREY, ha='right' if al == 'right' else 'left'); cx += w_
            yy += lh; self.rule(x, x + sum(c[1] for c in cols), yy - 1.3, 0.25)
        for i, r in enumerate(rows):
            last = bold_last and i == len(rows) - 1
            if zebra and i % 2 == 0: self.rect(x - 1, yy - 1.0, sum(c[1] for c in cols) + 2, lh, fc='#EEEAE1', z=-1)
            cx = x; hmax = 1
            for (t, w_, al), v in zip(cols, r):
                lines = wrap(str(v).upper(), w_ - 2, size, 'bold' if last else 'normal')
                for j, ln in enumerate(lines):
                    self.text(cx + (w_ if al == 'right' else 0), yy + j * size * 1.22, ln, size, 'bold' if last else 'normal', ha='right' if al == 'right' else 'left')
                hmax = max(hmax, len(lines)); cx += w_
            yy += lh + (hmax - 1) * size * 1.22
        return yy
    def keynotes(self, x, y, notes, w, size=3.4, start=1, gap=1.4):
        for i, n in enumerate(notes):
            r = 2.3
            self.ax.add_patch(MCircle((x + r, H - y - r + 0.4), r, fc=INK, ec='none', zorder=21))
            self.ax.text(x + r, H - y - r + 0.4, str(i + start), fontsize=2.4 * PT, ha='center', va='center', color='white', fontweight='bold', family='Inter', zorder=22)
            y = max(self.text(x + 2 * r + 2.5, y, n, size, 'normal', width=w - 2 * r - 2.5), y + 2 * r + 0.6) + gap
        return y
    def save(self):
        fn = os.path.join(OUT, f'CRIT2_BOARD_{self.no}')
        self.S.fig.savefig(fn + '.pdf')
        self.S.fig.savefig(fn + '.png', dpi=110)
        return fn

# =============================================================================================== data
def gross():
    enc = sum(r['poly'].area for r in ROOMS if r['kind'] != 'open')
    by = {fl: sum(r['poly'].area for r in ROOMS if r['fl'] == fl and r['kind'] != 'open') for fl in ('GF', 'L1', 'L2')}
    return enc, by

SOA = [('A1', 'LOCAL INGREDIENT SHOPS (4 No.)'), ('A2', 'KUIH + SNACK SHOPS (4 No.)'), ('A3', 'CAFE: KITCHEN + DINING'),
       ('B1', 'LOCAL FOOD HERITAGE GALLERY'), ('B2', 'MULTIPURPOSE HALL · DAPUR REWANG'), ('C', 'MANAGEMENT + FIRST AID'),
       ('D2', 'SURAU (M + F) + FAMILY WAITING'), ('D3', 'TOILETS, NURSING, NAPPY CHANGE'), ('E1', 'COLD + DRY STORES'), ('E2', 'LOADING + RECEPTION'),
       ('E4', 'MDB + LAN / TELECOM'), ('E7', 'HOUSEKEEPING + JANITOR')]
def soa_rows():
    req, got = {}, {}
    for r in ROOMS:
        if r['brief'] and r['brief'][1]:
            g = r['brief'][0]; req[g] = req.get(g, 0) + r['brief'][1]
            got[g] = got.get(g, 0) + (r['poly'].buffer(-0.075, join_style=2).area if r['kind'] != 'open' else r['poly'].area)
    rows = [(g, nm, f'{req.get(g, 0):.0f}', f'{got.get(g, 0):.0f}') for g, nm in SOA]
    tr, tg = sum(req.values()), sum(got.values())
    rows.append(('', 'TOTAL NET · ROOMS LISTED', f'{tr:.0f}', f'{tg:.0f}'))
    return rows

# =============================================================================================== boards
def board01():
    B = Board('01', 'DESIGN CONCEPT + PROGRAMME', 'WHERE THE PENINSULA MEETS')
    hero = os.path.join(RND, 'img', 'hero.png') if Image.open(os.path.join(RND, 'img', 'hero.png')).size[0] > 2000 else os.path.join(RND, 'final', '01_hero.png')
    y = B.img(hero, X0, 36, X1 - X0, 214, focus=(0.5, 0.55))
    B.rect(X0, 36 + 214 - 17, 150, 17, fc='#1E2226', z=3)
    B.text(X0 + 5, 36 + 214 - 14.2, 'TITIK TEMU', 6.0, 'bold', 'white', z=4)
    B.text(X0 + 52, 36 + 214 - 12.6, 'VIEW FROM JALAN TOK MUDA AWANG NGAH', 2.9, 'medium', '#D9DCDF', z=4)
    y = 258
    # concept text
    B.head(X0, y, '01', 'CONCEPT · TITIK TEMU', 190)
    t = ('TEMERLOH SITS AT THE CENTRE OF PENINSULAR MALAYSIA. JUPEM FIXED THE CENTRE POINT OF THE PENINSULA IN TEMERLOH DISTRICT, '
         'AND THE ROADS FROM EVERY COAST MEET HERE. TITIK TEMU (THE MEETING POINT) IS WHERE THE FOOD AND THE PEOPLE OF EVERY STATE MEET: '
         'A LOCAL FOOD HUB BESIDE SUNGAI PAHANG.')
    yy = B.para(X0, y + 11, t, 190, 3.9)
    t2 = ('ONE RADIAL CENTRE (THE MAST + TITIK POOL) GATHERS EVERYTHING. FOUR GATES FACE THE FOUR REGIONS ON THEIR TRUE BEARINGS: '
          'TIMUR (PAHANG · TERENGGANU · KELANTAN), SELATAN (N. SEMBILAN · MELAKA · JOHOR), TENGAH (SELANGOR · KL · PUTRAJAYA) AND '
          'UTARA (PERAK · PENANG · KEDAH · PERLIS). LONG ROUTES FROM EACH GATE LEAD PAST THE STATE SHOPS TO THE TALAM COURT, '
          'WHERE RAIN FALLS THROUGH THE OCULUS INTO THE POOL: THE "TITIK".')
    yy = B.para(X0, yy + 2.5, t2, 190, 3.9)
    yy += 3
    for i, t3 in enumerate(['ONE CENTRE: THE MAST (+30 M) AND THE TITIK POOL', 'FOUR GATES ON THE TRUE BEARINGS OF THE FOUR REGIONS',
                            'THREE RINGS + A FREE-STANDING RING BRIDGE: A MARKET STREET IN THE AIR', 'ROOF STEPS UP 1.8 M PER TIER TO THE FUNNEL: LIGHT + AIR IN, RAIN TO THE TITIK']):
        B.text(X0, yy, f'{i + 1}', 3.7, 'bold', ACC); yy = B.text(X0 + 6, yy, t3, 3.6, 'semibold', width=184) + 1.2
    # peninsula diagram
    k = 26.5
    D = CD.peninsula(k, labels=True, lab_size=2.6)
    x0_, y0_, x1_, y1_ = CD.bbox(D)
    B.draw(D, 1, (x0_, y1_), 222, 262 - 0.0)
    B.text(X1, 262, 'ROUTES FROM THE 12 STATE\nCAPITALS CONVERGE ON TEMERLOH', 3.3, 'semibold', ACC, ha='right')
    B.text(X1, 397, 'PAHANG SHADED · KEY PLAN (NTS)', 2.9, 'medium', GREY, ha='right')
    # development
    y = 404
    B.head(X0, y, '02', 'DESIGN DEVELOPMENT · CRIT 1 → CRIT 2', X1 - X0)
    devs = CD.dev_diagrams()
    caps = [('CRIT 1', 'TWO RINGS: GELUNG RASA (PUBLIC) + GELUNG KECIL (PRIVATE) ON THE QIBLA AXIS.'),
            ('V2 · AFTER THE PANEL', 'ONE RADIAL CENTRE. FOUR CONCAVE GATES, THE CONVEX FIRST FLOOR HANGS OVER THEM. THREE FLOORS, TENNIS COURT LAND ADDED.'),
            ('V3.1 · CRIT 2', 'THREE RINGS: INNER RING, FREE-STANDING RING BRIDGE, OUTER RING, WITH LIGHT GAPS BETWEEN. ROOF STEPS UP IN THREE TIERS TO THE FUNNEL.')]
    cw = (X1 - X0 - 12) / 3
    for i, (D, (tt, cc)) in enumerate(zip(devs, caps)):
        cx = X0 + i * (cw + 6) + cw / 2
        B.draw(D, 1500, (56.0, 24.5), cx, 440)
        B.text(X0 + i * (cw + 6), 465, tt, 3.6, 'bold', ACC)
        B.para(X0 + i * (cw + 6), 470.5, cc, cw, 3.2, lh=1.3)
        if i < 2: B.text(X0 + (i + 1) * (cw + 6) - 3.4, 437, '→', 7, 'bold', ACC, ha='center')
    # islamic values + SOA
    y = 489
    B.head(X0, y, '03', 'ISLAMIC VALUES', 150)
    B.bullets(X0, y + 11, ['NO WASTAGE: ONE SHOPFRONT KIT FOR 8 SHOPS, RAINWATER KEPT ON SITE (TITIK POOL)',
                           'RAHMATAN LIL ALAMIN: FREE PUBLIC COURT, SHADE + WATER FOR EVERY VISITOR',
                           'ACCESSIBLE: 1:20 RAMPS AT ALL 4 GATES, 2 LIFTS, MS 1184 TOILETS',
                           'FIT FOR PURPOSE: SURAU ON THE QUIET TOP FLOOR, FACING QIBLA 292.3°'], 150, 3.25, gap=1.0)
    B.head(172, y, '04', 'SCHEDULE OF ACCOMMODATION (NET M²)', X1 - 172)
    yy = B.table(172, y + 11, [('', 12, 'left'), ('SPACE', 150, 'left'), ('BRIEF', 36, 'right'), ('PROVIDED', 36, 'right')], soa_rows(), size=2.95, lh=4.25, bold_last=True)
    enc, by = gross()
    B.text(172, yy + 0.5, f'+ TALAM COURT (105 SEATS + PLAY), COVERED ARRIVAL, UTILITY BLOCK + PARKING ON THE SITE PLAN · GROSS FLOOR AREA {enc:,.0f} M² (BRIEF 900-1,500 M², GROSS 1,526 M²)', 2.7, 'medium', GREY, width=X1 - 172)
    return B

def board02():
    B = Board('02', 'SITE PLAN + SITE SYNTHESIS', 'LOT 10150 + FORMER TENNIS COURT · JALAN TOK MUDA AWANG NGAH')
    y = 36
    B.head(X0, y, '01', 'LOCATION', 84)
    D = CD.peninsula(11.0, lines=False, labels=False)
    x0_, y0_, x1_, y1_ = CD.bbox(D)
    B.draw(D, 1, (x0_, y1_), X0 + 12, 50)
    B.text(X0, 120, 'PENINSULAR MALAYSIA · PAHANG SHADED\nTEMERLOH 3.45°N 102.42°E · NTS', 2.9, 'medium', GREY)
    B.head(104, y, '02', 'SITE SYNTHESIS', 184)
    D = CD.synthesis(1450)
    B.draw(D, 1450, (63.0, 26.0), 104 + 92, 87, clip=(104, 46, 288, 130))
    B.head(296, y, '03', 'SITE DATA', X1 - 296)
    enc, by = gross(); cover = SC.disc(SC.R_ROOF).area
    rows = [('SITE AREA', f'{SC.SITE.area:,.0f} M²'), ('FOOTPRINT (ROOF Ø56.6)', f'{cover:,.0f} M²'), ('SITE COVERAGE', f'{cover / SC.SITE.area * 100:.0f} %'),
            ('GROSS FLOOR AREA', f'{enc:,.0f} M²'), ('GF / L1 / L2', f'{by["GF"]:.0f} / {by["L1"]:.0f} / {by["L2"]:.0f}'), ('STOREYS', '3 (BRIEF ≤ 3)'),
            ('HEIGHT: ROOF / MAST', '+19.8 / +30.0 M'), ('PARKING', '5 STAFF + 1 OKU'), ('MOTOR / BICYCLE', '10 / 10')]
    B.table(296, y + 11, [('ITEM', 52, 'left'), ('', 58, 'right')], rows, size=3.0, lh=4.6, head=False)
    # site plan 1:500
    y = 134
    B.dtitle(X0, y, '1', 'SITE PLAN', 'SCALE 1:500 AT A2', 'ROOF PLAN WITH CONTEXT · SITE DATUM ±0.000 = ROAD CROWN')
    B.draw(CD.site_board(), 500, (58.0, 23.0), 210, 262, clip=(X0, 146, X1, 382))
    B.north(392, 160); B.scalebar(300, 372, 500, (0, 5, 10, 20, 30))
    # aerial + strategy
    y = 390
    B.img(os.path.join(RND, 'final', '02_aerial_nw.png'), X0, y, 238, 134, focus=(0.5, 0.5))
    B.text(X0, y + 137, 'AERIAL FROM THE NORTH-WEST: THE ROUND HUB SITS ON ITS PLINTH, FOUR GATES OPEN TO THE ROADS AND PATHS', 2.9, 'medium', GREY, width=238)
    B.head(260, y, '04', 'SITE STRATEGY', X1 - 260)
    B.bullets(260, y + 11, ['CENTRE C = THE POLE OF THE BUILDABLE AREA (LOT + TENNIS COURT): THE BUILDING SITS EQUALLY FAR FROM EVERY SETBACK',
                            'SELATAN = MAIN GATE ON THE MAIN ROAD; DROP-OFF, OKU + STAFF PARKING BESIDE IT',
                            'SERVICE YARD, REFUSE + UTILITY BLOCK ON JALAN IBRAHIM, AWAY FROM THE PUBLIC GATES',
                            'GF ON A +0.900 PLINTH ABOVE FLOOD LEVEL; FORECOURTS RAMP 1:20 OR FLATTER',
                            'ROUND, NO BACK FACADE: DEEP 1.8 M ROOF OVERHANG + FINS CUT THE LOW EAST AND WEST SUN',
                            'TAMAN ULAM POCKET GARDENS + SHADE TREES ON THE PERIMETER PROMENADE'], X1 - 260, 3.3, gap=1.2)
    B.head(260, 495, '05', 'SETBACKS + ACCESS', X1 - 260)
    B.table(260, 506, [('', 70, 'left'), ('', 76, 'right')], [('FRONT · JALAN TOK MUDA AWANG NGAH', '6 M'), ('SIDE · JALAN IBRAHIM', '6 M'),
            ('NORTH + WEST BOUNDARIES', '3 M'), ('BOMBA HARDSTANDING (6 M)', 'SOUTH + EAST'), ('PILLAR HYDRANTS', '2 No. ≤ 30 M'), ('ROOF EDGE TO SETBACKS', 'CLEAR ALL ROUND')],
            size=3.0, lh=4.7, head=False)
    return B

def plan_legend(B, x, y, legend, cols, colw, size=3.0, lh=4.25, title=None):
    if title: y = B.text(x, y, title, 3.4, 'bold', ACC) + 1.0
    n = math.ceil(len(legend) / cols)
    for c in range(cols):
        yy = y
        for key, name, area in legend[c * n:(c + 1) * n]:
            B.text(x + c * colw, yy, key, size, 'bold')
            B.text(x + c * colw + 12.5, yy, name[:46] if tw(name, size) < colw - 25 else name, size, 'normal', width=colw - 26)
            B.text(x + (c + 1) * colw - 4, yy, area, size, 'medium', GREY, ha='right')
            yy += lh * (len(wrap(name, colw - 26, size)) if len(wrap(name, colw - 26, size)) > 1 else 1)
    return y + n * lh

def board03():
    B = Board('03', 'GROUND FLOOR PLAN', 'FFL +0.900 · WITH CONTEXT · SCALE 1:200')
    D, leg = CD.plan_board('GF')
    B.draw(D, 200, tuple(C), 210, 252, clip=(X0, 36, X1, 474))
    B.dtitle(X0, 38, '1', 'GROUND FLOOR PLAN', 'SCALE 1:200 AT A2', 'FFL +0.900')
    B.north(394, 52); B.scalebar(318, 464, 200, (0, 1, 2, 5, 10, 15))
    B.rule(X0, X1, 479, 0.25)
    plan_legend(B, X0, 483, leg, 3, (X1 - X0) / 3, title='ROOM LEGEND  ·  NET M²', size=3.2, lh=4.6)
    B.text(X0, 571, 'SECTION LINES A-A AND B-B: SEE BOARD 06 · GRID 1-27 RADIAL FROM CENTRE C (MAST), RINGS A-F · ROOM NUMBERS G = GROUND FLOOR, A1/A2 = SHOPS', 2.9, 'medium', GREY)
    return B

def board04():
    B = Board('04', 'FIRST + SECOND FLOOR PLANS', 'FFL +5.400 + +9.600 · SCALE 1:200')
    D, leg = CD.plan_board('L1')
    B.draw(D, 200, tuple(C), 154, 186, clip=(X0, 36, 296, 336))
    B.dtitle(X0, 38, '2', 'FIRST FLOOR PLAN', 'SCALE 1:200', 'FFL +5.400 · RING BRIDGE')
    B.north(282, 52)
    B.rule(300, 300, 40, 0.0)
    plan_legend(B, 302, 40, leg, 1, X1 - 302, title='FIRST FLOOR · NET M²', size=3.15, lh=4.5)
    B.rule(X0, X1, 340, 0.25)
    D, leg2 = CD.plan_board('L2')
    B.draw(D, 200, tuple(C), 128, 432, clip=(X0, 344, 250, 520))
    B.dtitle(X0, 346, '3', 'SECOND FLOOR PLAN', 'SCALE 1:200', 'FFL +9.600 · INNER RING ONLY')
    yy = plan_legend(B, 256, 348, leg2, 1, X1 - 256, title='SECOND FLOOR · NET M²', size=3.3, lh=4.8)
    B.scalebar(256, yy + 8, 200, (0, 1, 2, 5, 10, 15))
    B.rule(X0, X1, 526, 0.25)
    B.head(X0, 530, '04', 'PLANNING STRATEGY', X1 - X0)
    B.bullets(X0, 541, ['FIRST FLOOR = THREE RINGS: INNER RING (OFFICE, HALL, TOILETS) · 1.5 M LIGHT GAP · FREE-STANDING RING BRIDGE WITH GERAI LIPAT STALLS · 1.5 M GAP · OUTER RING. THE BRIDGE TOUCHES THE RINGS ONLY BY 4 WALKWAYS ON THE GATE AXES.'],
              (X1 - X0) / 2 - 4, 3.4, gap=1)
    B.bullets(X0 + (X1 - X0) / 2 + 4, 541, ['SECOND FLOOR SITS ON THE INNER RING ONLY: GALLERY, SURAU (M + F, QIBLA 292.3°) AND FAMILY WAITING, THE QUIETEST LEVEL. CORES: C1 EAST (STAIR + LIFT 1), C2 NORTH (STAIR), LIFT 2 SOUTH-WEST.'],
              (X1 - X0) / 2 - 4, 3.4, gap=1)
    return B

def board05():
    B = Board('05', 'ROOF PLAN + EXPLODED AXONOMETRIC', 'THREE ROOF TIERS ON THE WAVE · SCALE 1:200')
    D = CD.roof_board()
    B.draw(D, 200, tuple(C), 160, 190, clip=(X0, 36, 306, 344))
    B.dtitle(X0, 38, '4', 'ROOF PLAN', 'SCALE 1:200', 'SPOT LEVELS = TOP OF EACH TIER')
    B.north(296, 52); B.scalebar(X0, 336, 200, (0, 1, 2, 5, 10, 15))
    B.head(312, 40, '01', 'ROOF', X1 - 312)
    B.bullets(312, 51, ['3 TIERS, EACH +1.8 M TOWARDS THE CENTRE: OUTER (W), MIDDLE (W + 1.8), FUNNEL RIM (W + 3.6)',
                        'THE WAVE: HIGH (+16.2) OVER THE SELATAN + UTARA GATES, LOW (+10.2) OVER TENGAH + TIMUR',
                        'CLERESTORIES WHERE THE TIERS OVERLAP: DAYLIGHT + STACK-EFFECT AIR IN, RAIN KEPT OUT',
                        'FUNNEL FALLS TO A Ø3 M OCULUS: RAIN DROPS INTO THE TITIK POOL',
                        '0.9 MM ALUMINIUM STANDING SEAM, SS316 GUTTERS, Ø150 DOWNPIPES IN FIN CASINGS',
                        'MAST +30.000: LIGHTNING AIR TERMINAL + AVIATION LIGHT'], X1 - 312, 3.15, gap=1.1)
    B.rule(X0, X1, 348, 0.25)
    B.head(X0, 352, '02', 'EXPLODED AXONOMETRIC', X1 - X0)
    exp = os.path.join(RND, 'explode', 'exploded_alpha.png')
    if not os.path.exists(exp): exp = os.path.join(RND, 'explode', 'exploded_raw.png')
    im = Image.open(exp); iw, ih = im.size
    # crop away the empty label margin on the left of the render
    bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox() if im.mode == 'RGBA' else (int(iw * 0.22), int(ih * 0.03), int(iw * 0.97), int(ih * 0.99))
    crop = (max(bb[0] - 10, 0), max(bb[1] - 10, 0), min(bb[2] + 10, iw), min(bb[3] + 10, ih)); im2 = im.crop(crop)
    tmp = os.path.join(OUT, '_exp.png'); im2.save(tmp)
    w_ = 280; h_ = w_ * im2.size[1] / im2.size[0]
    if h_ > 212: h_ = 212; w_ = h_ * im2.size[0] / im2.size[1]
    ix, iy = X1 - w_, 361
    B.img(tmp, ix, iy, w_, h_)
    lab = json.load(open(os.path.join(RND, 'explode', 'labels2d.json')))
    desc = {'ROOF': ('ROOF', '3-TIER WAVE ROOF, FUNNEL + TENUN LINING, CLERESTORIES, MAST +30.000'),
            'L2': ('SECOND FLOOR +9.600', 'INNER RING ONLY: GALLERY, SURAU, FAMILY WAITING'),
            'L1': ('FIRST FLOOR +5.400', 'INNER RING · FREE-STANDING RING BRIDGE + GERAI LIPAT · OUTER RING WITH FINS'),
            'GF': ('GROUND FLOOR +0.900', 'TALAM COURT, ARCADE, 8 STATE SHOPS, CAFE, 4 CONCAVE GATES ON THE SITE PLINTH')}
    for b in ('ROOF', 'L2', 'L1', 'GF'):
        L = lab[b]; px = (L['x'] * iw - crop[0]) / im2.size[0]; py = (L['y'] * ih - crop[1]) / im2.size[1]
        ax_, ay_ = ix + px * w_, iy + py * h_
        ty = ay_ - 4
        B.text(X0, ty, desc[b][0], 3.7, 'bold')
        B.text(X0, ty + 5.2, desc[b][1], 3.1, 'normal', GREY, width=96)
        B.ax.plot([X0 + 98, ax_ - 2], [H - ty - 2.2, H - ty - 2.2], lw=0.25 * PT, color=LGREY, zorder=6)
        B.ax.plot([ax_ - 2], [H - ty - 2.2], 'o', ms=3.2, color=ACC, zorder=7)
    B.text(X0, 566, 'FLOORS LIFTED 16 / 46 / 66 M FOR CLARITY · VIEW FROM THE SOUTH-EAST', 2.9, 'medium', GREY)
    return B

def section_blocks(B, items, y0):
    """items = [(drawing, label_num, title, sub)] stacked; each drawing placed at 1:200 centred on its own bbox"""
    y = y0
    for D, num, title, sub, model_c, hgt in items:
        x0_, z0_, x1_, z1_ = CD.bbox(D, layers=None)
        xs = [p[0] for k, l, a in D.items if k in ('line', 'poly') for p in (a['pts'] if k == 'line' else [q for r in a['rings'] for q in r])]
        xs = sorted(xs); xa, xb = xs[int(len(xs) * 0.002)], xs[int(len(xs) * 0.998) - 1]
        mx = max(model_c[0], xb - 31.0)
        B.dtitle(X0, y, num, title, 'SCALE 1:200', sub, w=X1 - X0 - 20)
        B.draw(D, 200, (mx, model_c[1]), 210, y + 14 + hgt / 2 + 8, clip=(X0, y + 13, X1, y + 14 + hgt + 12))
        y += hgt + 30
    return y

def board06():
    B = Board('06', 'SECTIONS + SOUTH ELEVATION', 'SCALE 1:200 · LEVELS IN METRES ABOVE SITE DATUM')
    (A, XA), (Bs, XB) = CD.section_board()
    E = CD.elevation_board(180.0, 'S')
    ua, ub = XA.u(C), XB.u(C)
    items = [(A, 'A', 'SECTION A-A', 'THROUGH THE SELATAN (MAIN) GATE, THE GAPS, RING BRIDGE, TALAM COURT + CORE 2 · LOOKING WEST', (ua, 15.0), 150),
             (Bs, 'B', 'SECTION B-B', 'THROUGH STAIR 4, THE WEST SHOPS, COURT, CORE 1 + THE HALL · LOOKING NORTH', (ub, 15.0), 150),
             (E, '5', 'SOUTH ELEVATION', 'FROM JALAN TOK MUDA AWANG NGAH (BEARING 180°)', (0.0, 15.0), 150)]
    section_blocks(B, items, 36)
    B.scalebar(318, 570, 200, (0, 1, 2, 5, 10, 15))
    return B

def board07():
    B = Board('07', 'ELEVATIONS', 'SCALE 1:200 · FACADE OPTION A: FINS OPEN AT THE GATES')
    items = [(CD.elevation_board(0.0, 'N'), '6', 'NORTH ELEVATION', 'BEARING 0° · UTARA GATE ON THE LEFT', (0.0, 15.0), 150),
             (CD.elevation_board(90.0, 'E'), '7', 'EAST ELEVATION', 'BEARING 90° · FROM JALAN IBRAHIM, TIMUR GATE', (0.0, 15.0), 150),
             (CD.elevation_board(270.0, 'W'), '8', 'WEST ELEVATION', 'BEARING 270° · TENGAH GATE + STAIR 4', (0.0, 15.0), 150)]
    section_blocks(B, items, 36)
    B.scalebar(318, 570, 200, (0, 1, 2, 5, 10, 15))
    return B

def board08():
    B = Board('08', 'STRUCTURAL SYSTEM', 'RC FRAME ON BORED PILES · STEEL ROOF + GATE TRUSSES')
    spread = 13.0
    D, off = CD.structure_axo(spread=spread)
    x0_, y0_, x1_, y1_ = CD.bbox(D)
    sc = 345; cx_, cy_ = 136, 47 + 126
    B.draw(D, sc, ((x0_ + x1_) / 2, (y0_ + y1_) / 2), cx_, cy_)
    B.head(X0, 36, '01', 'STRUCTURAL AXONOMETRIC (EXPLODED)', 236)
    k = 1000 / sc; uc, vc = (x0_ + x1_) / 2, (y0_ + y1_) / 2
    import math as _m
    el = _m.cos(_m.radians(30.0))
    for r, zl, t in ((28.3, off['R'] + 16.5, 'ROOF: STEEL RAFTERS ON EVERY GRID,\nFUNNEL RING HUNG FROM THE MAST'), (15.5, 9.3 + off['L2'], 'L2 SLAB + RING BEAMS\n(INNER RING ONLY)'),
                     (26.5, 5.1 + off['L1'], 'L1 RINGS + RING BRIDGE,\n4 GATE TRUSSES (MID-SPAN)'), (23.0, 2.6, 'COLUMNS Ø350, RINGS B C D E;\nPILE CAPS + GROUND BEAMS')):
        px = cx_ + (-r - uc) * k; py = cy_ - (zl * el - vc) * k
        B.text(X0, py - 4.5, t, 3.0, 'semibold')
        B.ax.plot([X0 + 58, px], [H - py, H - py], lw=0.25 * PT, color=LGREY, zorder=6); B.ax.plot([px], [H - py], 'o', ms=2.6, color=ACC, zorder=7)
    B.head(258, 36, '02', 'SYSTEM', X1 - 258)
    yy = B.bullets(258, 47, ['FRAME: RC COLUMNS Ø350 (C35) ON RINGS B R11.0, C R15.5, D R18.5 (BRIDGE) + E R23.0, ON RADIAL GRIDS 1-27',
                        'FLOORS: RC SLABS 250 ON RING + RADIAL BEAMS; L1 CANTILEVERS 3.5 M BEYOND GRID E: THE HANGING FIRST FLOOR',
                        'RING BRIDGE: 350 COMPOSITE SLAB ON A STEEL BOX RING BEAM ON RING D; SEPARATED BY 50 JOINTS',
                        'MID-SPAN: STOREY-DEEP STEEL PRATT TRUSSES SPAN EACH CONCAVE GATE BETWEEN TWO E COLUMNS (BOARD 09)',
                        'ROOF: TAPERED STEEL RAFTERS; FUNNEL RING HUNG FROM THE MAST BY 12 STAY RODS',
                        'STABILITY: RC CORES C1 + C2 + LIFT 2 WITH THE SLAB DIAPHRAGMS',
                        'FOUNDATION: Ø450 BORED PILES + PILE CAPS + GROUND BEAMS (ALLUVIUM BY SUNGAI PAHANG, SI TO CONFIRM)'], X1 - 258, 3.05, gap=0.8)
    B.text(258, yy + 2, 'MATERIAL GRADES', 3.3, 'bold', ACC)
    B.table(258, yy + 8, [('', 70, 'left'), ('', 78, 'right')], [('CONCRETE (FRAME / CAPS)', 'C35 / C30'), ('REINFORCEMENT', 'B500 · 40 COVER'),
            ('STRUCTURAL STEEL', 'S355 · INTUMESCENT 60 MIN'), ('BOLTS', 'GRADE 8.8 HSFG'), ('PILES', 'Ø450 BORED · C30')], size=2.95, lh=4.4, head=False)
    yy = yy + 8 + 5 * 4.4 + 4
    B.text(258, yy, 'DESIGN LOADS (MS EN 1991)', 3.3, 'bold', ACC)
    B.table(258, yy + 6, [('', 84, 'left'), ('', 64, 'right')], [('SHOPS, COURT, ARCADE', '5.0 KN/M²'), ('RING BRIDGE + WALKWAYS (CROWD)', '5.0 KN/M²'), ('HALL + GALLERY', '5.0 KN/M²'),
            ('OFFICES', '3.0 KN/M²'), ('FINISHES + SERVICES', '1.5 KN/M²'), ('ROOF (MAINTENANCE)', '0.5 KN/M²'), ('WIND', 'TO MS 1553')], size=2.95, lh=4.4, head=False)
    B.rule(X0, X1, 304, 0.25)
    B.head(X0, 308, '03', 'COLUMN GRID + GATE SPANS', 190)
    G = Drawing('GRID')
    for r, lab in ((11.0, 'B'), (15.5, 'C'), (18.5, 'D'), (23.0, 'E'), (26.5, 'F')):
        G.circle(C, r, 'A-GRID', edge='#9AA3AD', lw=0.15, ls='--')
        G.text(P(r, 140.0), lab, 'A-GRID', size=2.6, weight='bold', color=ACC, halo=True)
    G.poly(SC.disc(26.5).difference(SC.disc(9.5)), 'A-WALL', fill='#ECE8DF', edge=None, z=0)
    for c in M.COLS:
        if c['ring'] in 'BCDE': G.circle(c['p'], 0.45, 'A-COLS', fill=INK, edge=None, z=4)
    Ecol = sorted([c for c in M.COLS if c['ring'] == 'E'], key=lambda c: c['b'])
    rows = []
    for sp in SC.SPINES:
        pa = min(Ecol, key=lambda c: (sp['b'] - c['b']) % 360); pb = min(Ecol, key=lambda c: (c['b'] - sp['b']) % 360)
        G.line([pa['p'], pb['p']], 'S-DETL', lw=0.8, color=ACC, z=5)
        l_ = np.linalg.norm(np.array(pb['p']) - np.array(pa['p']))
        G.text(P(32.0, sp['b']), f"{sp['k']}\n{l_:.1f} M", 'A-ANNO', size=2.7, weight='bold', color=ACC if sp['k'] == 'TIMUR' else INK, halo=True)
        rows.append((sp['k'], f'{l_:.1f}', '4.4', 'SHS 200' if l_ < 15 else ('SHS 250' if l_ < 20 else 'SHS 300 + PROP')))
    G.circle(C, 0.6, 'A-COLS', fill=ACC, edge=None)
    B.draw(G, 500, tuple(C), 104, 400)
    B.text(X0, 476, 'SCALE 1:500 · BRONZE LINE = GATE TRUSS ON THE CHORD BETWEEN TWO E COLUMNS', 2.9, 'medium', GREY)
    B.table(X0, 484, [('GATE', 46, 'left'), ('SPAN M', 34, 'right'), ('DEPTH M', 34, 'right'), ('CHORDS', 66, 'right')], rows, size=3.1, lh=4.8)
    B.text(X0, 515, 'TIMUR (13.4 M) IS THE MID-SPAN STUDY, INSIDE THE 10-15 M RANGE OF THE BRIEF. THE SELATAN SPAN (23.3 M) NEEDS A DEEPER TRUSS OR A PROP AT THE GATE AXIS: C&S TO CONFIRM.', 3.0, 'normal', GREY, width=182)
    B.head(204, 308, '04', 'GATE DECK · CROSS-SECTION', X1 - 204)
    T = CD.upper(CD.truss_section())
    B.draw(T, 50, (24.4, 6.6), 305, 410, clip=(204, 320, X1, 512))
    B.dtitle(204, 516, '9', 'GATE DECK SECTION', 'SCALE 1:50', 'TRUSS + CANTILEVERED DECK')
    B.rect(204, 536, X1 - 204, 22, fc='#EAE4D6', z=1)
    B.text(208, 540, 'LOAD PATH', 3.2, 'bold', ACC)
    B.text(208, 546, 'ROOF RAFTERS + L1 DECK → TRUSS CHORDS → COLUMNS E → PILE CAPS → Ø450 BORED PILES', 3.1, 'semibold', INK, width=X1 - 212)
    return B

def board09():
    B = Board('09', 'MID-SPAN STRUCTURE · GATE TRUSS', 'TIMUR GATE · 13.4 M CLEAR SPAN · SCALE 1:50')
    L = CD.timur_span()[0]
    D = CD.upper(CD.detail_truss(L))
    B.dtitle(X0, 36, '10', 'TIMUR GATE TRUSS · ELEVATION ON THE CHORD', 'SCALE 1:50 AT A2', 'THE FIRST FLOOR HANGS OVER THE CONCAVE GATE', w=300)
    B.draw(D, 50, (L / 2, 3.9), 210, 236, clip=(X0, 52, X1, 428))
    B.scalebar(318, 56, 50, (0, 0.5, 1, 2, 3))
    B.rule(X0, X1, 432, 0.25)
    B.head(X0, 436, '01', 'SPECIFICATION (KEYNOTES)', 238)
    B.keynotes(X0, 447, CD.TRUSS_NOTES, 238, 3.25, gap=0.9)
    B.head(260, 436, '02', 'PRELIMINARY CHECK', X1 - 260)
    wkn = 95.0; Mx = wkn * L ** 2 / 8; F = Mx / 4.4; V = wkn * L / 2; Fd = V / math.sin(math.atan(4.4 / (L / 6)))
    rows = [('SPAN L / DEPTH d', f'{L:.1f} / 4.4 M'), ('ULS LINE LOAD w', '≈ 95 KN/M'), ('(L1 DECK 5 M + ROOF 7.7 M)', ''),
            ('M = wL² / 8', f'{Mx:,.0f} KNM'), ('CHORD FORCE M / d', f'{F:,.0f} KN'), ('SHS 200x200x10 S355', '≈ 2,600 KN'),
            ('SHEAR V = wL / 2', f'{V:,.0f} KN'), ('END DIAGONAL', f'{Fd:,.0f} KN'), ('SHS 150x150x8 S355', '≈ 1,590 KN (T)'), ('DEFLECTION LIMIT', 'L / 360')]
    yy = B.table(260, 447, [('', 82, 'left'), ('', 64, 'right')], rows, size=3.15, lh=4.9, head=False)
    B.text(260, yy + 1, 'HAND CHECK FOR DESIGN DEVELOPMENT ONLY. FINAL SIZES BY THE C&S ENGINEER.', 2.9, 'medium', GREY, width=X1 - 260)
    return B

def board10():
    B = Board('10', 'CONSTRUCTION DETAIL · FOUNDATION TO ROOF', 'OUTER RING AT BEARING 300° · SCALE 1:50')
    D = CD.upper(CD.detail_f2r(300.0))
    B.dtitle(X0, 36, '11', 'WALL SECTION · FOUNDATION TO ROOF', 'SCALE 1:50 AT A2', 'OUTER RING, GAP + BRIDGE EDGE', w=200)
    B.draw(D, 50, (25.2, 6.5), 152, 302, clip=(X0, 52, 266, 574))
    B.scalebar(X0 + 4, 566, 50, (0, 0.5, 1, 2, 3))
    B.head(270, 36, '01', 'SPECIFICATION', X1 - 270)
    yy = B.keynotes(270, 47, CD.F2R_NOTES, X1 - 270, 2.95, gap=0.7)
    B.head(270, yy + 4, '02', 'KEY PLAN', X1 - 270)
    K = Drawing('KEY')
    K.poly(SC.SITE, 'A-SITE', fill='#F7F4EE', edge=GREY, lw=0.2, ls='-.')
    for g, f in ((RG.INNER, '#AEB4BA'), (RG.BRIDGE, '#D9C7A6'), (RG.OUTER, '#C9CDD2')): K.poly(g, 'A-WALL', fill=f, edge=INK, lw=0.15)
    a_, b_ = P(14.0, 300.0), P(31.0, 300.0)
    K.line([a_, b_], 'A-ANNO', lw=0.5, color='#C0392B')
    K.text(P(35.5, 300.0), '11', 'A-ANNO', size=2.6, weight='bold', color='#C0392B')
    L, pa, pb, s_ = CD.timur_span(); K.line([pa['p'], pb['p']], 'A-ANNO', lw=0.6, color=ACC)
    K.text(P(33.0, 27.9), '10', 'A-ANNO', size=2.6, weight='bold', color=ACC)
    B.draw(K, 1250, (58.0, 25.0), 270 + (X1 - 270) / 2, yy + 46)
    B.text(270, yy + 79, 'RED = THIS SECTION (11) · BRONZE = GATE TRUSS (10) · SCALE 1:1250', 2.8, 'medium', GREY, width=X1 - 270)
    B.head(270, yy + 90, '03', 'BUILD SEQUENCE (IBS)', X1 - 270)
    B.keynotes(270, yy + 101, ['BORED PILES + PILE CAPS', 'PRECAST GROUND BEAMS, PLINTH + GF SLAB', 'RC COLUMNS + L1 SLABS, CORES', 'STEEL GATE TRUSSES + BRIDGE RING BEAM',
                               'STEEL RAFTERS, PURLINS, MAST + FUNNEL', 'ROOF SHEETING, GUTTERS, CLERESTORIES', 'UNITISED CURTAIN WALL + FINS', 'GRC SOFFITS, FINISHES, LANDSCAPE'],
               X1 - 270, 2.95, gap=0.2)
    return B

def board11():
    B = Board('11', 'FACADE + JOINT DETAILS', 'FACADE 1:25 · JOINTS 1:10')
    F = CD.upper(CD.facade_broken())
    B.dtitle(X0, 36, '12', 'FACADE SECTION · SLAB EDGE + ROOF EDGE', 'SCALE 1:25 AT A2', 'BROKEN: CURTAIN WALL + FIN CONTINUE', w=200)
    B.draw(F, 25, (0.2, 6.75), 120, 160, clip=(X0, 52, 222, 270))
    B.scalebar(150, 268, 25, (0, 0.25, 0.5, 1))
    B.rule(X0, 222, 276, 0.25)
    yy = B.keynotes(X0, 280, CD.FAC_NOTES, 208, 3.0, gap=0.45)
    B.img(os.path.join(RND, 'final', '03_gate.png'), X0, yy + 4, 208, min(572 - yy - 16, 117), focus=(0.5, 0.35))
    B.text(X0, min(yy + 4 + 117, 572 - 12) + 2, 'FACADE OPTION A: FINS CLOSED (18°) MID-PETAL, TURNING OPEN (90°) AT THE GATES', 2.8, 'medium', GREY, width=208)
    xr = 230; wr = X1 - xr
    J = CD.upper(CD.joint_node())
    B.dtitle(xr, 36, '13', 'TRUSS NODE (BOTTOM CHORD)', 'SCALE 1:10', None)
    B.draw(J, 10, (0.0, 0.16), xr + wr / 2, 110, clip=(xr, 52, X1, 168))
    B.keynotes(xr, 170, CD.NODE_NOTES, wr, 2.95, gap=0.2)
    J = CD.upper(CD.joint_fin())
    B.dtitle(xr, 222, '14', 'FIN BRACKET (PLAN)', 'SCALE 1:10', None)
    B.draw(J, 10, (0.0, 0.14), xr + wr / 2, 284, clip=(xr, 238, X1, 336))
    B.keynotes(xr, 338, CD.FIN_NOTES, wr, 2.95, gap=0.2)
    R = CD.upper(CD.rooflight_joint())
    B.dtitle(xr, 392, '15', 'ROOFLIGHT AT THE BRIDGE EDGE', 'SCALE 1:10', None)
    B.draw(R, 10, (0.05, 0.0), xr + wr / 2, 458, clip=(xr, 406, X1, 512))
    B.keynotes(xr, 514, CD.ROOF_NOTES, wr, 2.95, gap=0.2)
    return B

def board12():
    B = Board('12', 'ENVIRONMENT + SERVICES', 'PASSIVE DESIGN · MS 1525 · UBBL · MS 1184')
    A, XA = CD.env_section()
    B.head(X0, 36, '01', 'PASSIVE STRATEGY · SECTION A-A', X1 - X0)
    B.draw(A, 300, (XA.u(C) + 4.0, 14.0), 210, 104, clip=(X0, 47, X1, 160))
    lg = [('#E0A100', 'DAYLIGHT DOWN THE GAPS + CLERESTORIES'), ('#C0392B', 'STACK EFFECT: WARM AIR OUT AT THE CLERESTORIES'),
          ('#3E7D3A', 'CROSS-VENTILATION THROUGH THE 4 GATES'), ('#1AA0C8', 'RAIN → FUNNEL → OCULUS → TITIK POOL')]
    for i, (c, t) in enumerate(lg):
        x = X0 + i * 98
        B.ax.plot([x, x + 9], [H - 167, H - 167], lw=1.2 * PT, color=c, zorder=10); B.text(x + 11, 165.3, t, 3.0, 'semibold', width=84)
    B.rule(X0, X1, 177, 0.25)
    B.head(X0, 181, '02', 'SUN + WIND', 186)
    B.draw(CD.synthesis(1150), 1150, (62.0, 26.0), 107, 246, clip=(X0, 192, 200, 300))
    B.bullets(X0, 304, ['3.45°N: THE SUN IS HIGH ALL YEAR, SO THE ROOF DOES THE SHADING: 1.8 M OVERHANG ROUND THE WHOLE RING',
                        'FINS TURN FROM 18° (CLOSED) TO 90° (OPEN AT THE GATES), BLOCKING THE LOW EAST + WEST SUN',
                        'THE 4 GATES CATCH BOTH MONSOONS AND FEED THE COURT; THE FUNNEL + GAPS EXHAUST THE WARM AIR'], 186, 3.2, gap=1.0)
    B.head(210, 181, '03', 'SERVICES STRATEGY', X1 - 210)
    sv = [('FIRE (UBBL + BOMBA)', 'HOSE REELS + DRY RISER IN CORES C1 + C2, 2 PILLAR HYDRANTS, 6 M APPLIANCE HARDSTANDING ON 2 SIDES; ESCAPE ≤ 45 M (TWO WAYS) TO 3 STAIRS + 2 EXTERNAL STAIRS'),
          ('WATER', 'SUCTION + FIRE TANKS IN THE UTILITY BLOCK; GF FED BY GRAVITY FROM THE TANK ROOM ON CORE 2, UPPER FLOORS BY BOOSTER'),
          ('SEWERAGE', 'SOIL STACKS IN 300 x 300 DUCTS, uPVC Ø150 TO IC + MH, CONNECTION TO THE PUBLIC SEWER'),
          ('ELECTRICAL', 'TNB LV INTAKE → MSB (G08) → FLOOR SUB-BOARDS → SHOP DBs WITH kWh METERS; ≈ 100 kVA STANDBY GENSET'),
          ('ACMV', 'VRF HEAT-RECOVERY FOR THE ENCLOSED ROOMS, OUTDOOR UNITS ON THE UTILITY BLOCK; COURT, ARCADE + BRIDGE NATURALLY VENTILATED'),
          ('RAINWATER', 'SS316 GUTTERS → Ø150 DOWNPIPES IN FIN CASINGS → PERIMETER DRAIN → OSD (MSMA); FUNNEL RAIN → TITIK POOL')]
    yy = 192
    for t, d in sv:
        B.text(210, yy, t, 3.3, 'bold', ACC)
        yy = B.para(210, yy + 4.7, d, X1 - 210, 3.15, lh=1.3) + 2.0
    B.rule(X0, X1, 368, 0.25)
    B.head(X0, 372, '04', 'SUSTAINABILITY + UNIVERSAL DESIGN', X1 - X0)
    cols = [['NO BRICK: GRC, ALUMINIUM, GLASS, GRANITE + STEEL, MOSTLY PREFABRICATED (IBS)', 'RAINWATER KEPT IN THE TITIK POOL FOR LANDSCAPE IRRIGATION',
             'LOW-E DGU, U ≤ 2.0, SHGC ≤ 0.35; OTTV TARGET ≤ 50 W/M² (MS 1525)', 'GF ROOMS DAYLIT BY THE OPAL ROOFLIGHTS IN THE GAPS: LESS ARTIFICIAL LIGHT'],
            ['STEP-FREE: GF ON A +0.900 PLINTH REACHED BY 1:20 RAMPS FROM ALL FOUR GATES', 'TWO 13-PERSON LIFTS (GF-L1-L2), BOTH ON THE MAIN ROUTES',
             'MS 1184 PwD TOILETS ON GF + L1, NURSING + NAPPY CHANGE, FAMILY WAITING ON L2', 'TACTILE ROUTES FROM THE GATES TO THE COURT, INFO COUNTER + WHEELCHAIR LOAN']]
    for i, c in enumerate(cols): B.bullets(X0 + i * 198, 383, c, 190, 3.35, gap=1.2)
    B.rule(X0, X1, 452, 0.25)
    B.head(X0, 456, '05', 'MATERIAL PALETTE', X1 - X0)
    pal = [('#E8EAEC', 'ALUMINIUM STANDING SEAM', 'ROOF TIERS', 'roof.jpg'), ('#B9A47E', 'CHAMPAGNE ALUMINIUM FIN', 'FACADE OPTION A', 'fin.jpg'), ('#ECEAE5', 'WHITE GRC', 'SOFFITS, FUNNEL, FASCIA', 'grc.jpg'),
           ('#BFD9E6', 'LOW-E GLASS', 'CURTAIN WALL G1', None), ('#D9D2C3', 'BUSH-HAMMERED GRANITE', 'PLINTH + FORECOURTS', 'pavers.jpg'), ('#C9C6C0', 'TERRAZZO', 'FLOORS', 'terrazzo.jpg'), ('#9C6B3F', 'TIMBER ANYAMAN', 'GATE CANOPIES', 'timber.jpg')]
    cw = (X1 - X0) / len(pal)
    for i, (c, t, d, tex) in enumerate(pal):
        x = X0 + i * cw
        B.rect(x, 467, cw - 4, 40, fc=c, ec='#8A9097', lw=0.2, z=2)
        if tex and os.path.exists(os.path.join(RND, 'textures', tex)): B.img(os.path.join(RND, 'textures', tex), x, 467, cw - 4, 40, z=3)
        B.text(x, 510, t, 3.0, 'bold', width=cw - 5); B.text(x, 521.5, d, 2.8, 'medium', GREY, width=cw - 5)
    B.rect(X0, 535, X1 - X0, 32, fc='#EAE4D6', z=1)
    B.text(X0 + 4, 539, 'ISLAMIC VALUES IN THE BUILDING', 3.4, 'bold', ACC)
    B.text(X0 + 4, 545.5, 'NO WASTAGE (ONE KIT, RAIN KEPT) · BENEFICIAL (FREE SHADE, WATER + SEATS FOR ALL) · ACCESSIBLE (STEP-FREE, 2 LIFTS) · NO HARM (SAFE ESCAPE, NO GLARE) · FIT FOR PURPOSE (SURAU FACING QIBLA 292.3°)', 3.3, 'semibold', INK, width=X1 - X0 - 8)
    return B

def board13():
    B = Board('13', 'PERSPECTIVES', 'INTERIOR + EXTERIOR VIEWS')
    F = os.path.join(RND, 'final')
    y = B.img(os.path.join(F, '04_dusk.png'), X0, 36, X1 - X0, 226)
    B.text(X0, y + 2.5, '01  DUSK FROM THE TENGAH SIDE: THE LIT RINGS AND THE RING BRIDGE BEHIND THE OPEN FINS', 3.4, 'semibold')
    cw = (X1 - X0 - 6) / 2; ch = 128
    imgs = [('03_gate.png', '02  SELATAN GATE: THE CONCAVE ENTRANCE UNDER THE HANGING FIRST FLOOR', (0.5, 0.45)), ('06_court.png', '03  TALAM COURT UNDER THE TENUN LINING + OCULUS', (0.5, 0.4)),
            ('05_bridge.png', '04  RING BRIDGE WITH THE GERAI LIPAT STALLS', (0.5, 0.5)), ('07_arcade.png', '05  THE ARCADE: EIGHT STATE SHOPFRONTS, ONE KIT', (0.5, 0.5))]
    for i, (f, cap, fo) in enumerate(imgs):
        x = X0 + (i % 2) * (cw + 6); yy = 276 + (i // 2) * (ch + 16)
        B.img(os.path.join(F, f), x, yy, cw, ch, focus=fo)
        B.text(x, yy + ch + 2.5, cap, 3.2, 'semibold', width=cw)
    return B

BOARDS = {'01': board01, '02': board02, '03': board03, '04': board04, '05': board05, '06': board06, '07': board07, '08': board08,
          '09': board09, '10': board10, '11': board11, '12': board12, '13': board13}

if __name__ == '__main__':
    import time
    only = sys.argv[1:] or list(BOARDS)
    for k in only:
        t = time.time(); B = BOARDS[k](); fn = B.save(); B.S.close(); print(k, os.path.basename(fn), round(time.time() - t, 1), 's', flush=True)
    if not sys.argv[1:] or 'all' in sys.argv:
        from pypdf import PdfWriter
        w = PdfWriter()
        for k in BOARDS: w.append(os.path.join(OUT, f'CRIT2_BOARD_{k}.pdf'))
        w.write(os.path.join(OUT, 'TITIK-TEMU_CRIT2_A2_BOARDS.pdf')); print('combined')
