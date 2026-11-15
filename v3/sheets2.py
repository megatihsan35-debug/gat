"""The non-plan sheets: site, roof, sections, elevations, fire strategy, plumbing schematic + calcs, M&E notes, details,
schedules, cover. Every builder returns (Sheet, [(Drawing, (dx, dy))]) so build.py can write the PDF page + one DXF."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
import plan3 as M
from plan3 import C, P, d, tdir, SC, ROOMS, FFL, CORES, S4
from cad import Drawing, INK
import sheets as SH
from sheets import new_sheet, notes_block, legend_block, north, scale_bar, drawing_title, key_plan, wrap, ACCENT
import plans, sections as SE, siteplan as ST, services as SV
GREYT = '#6B7480'

# --------------------------------------------------------------------------------------------- table helper (paper mm)
TS = 1.85                                  # table scale on the A0 calc / schedule sheets
def table(D, x, y, cols, rows, head=None, size=1.75, lh=3.1, title=None, bold_last=False, k=TS):
    """cols = [(header, width, align)], rows = list of tuples of strings. returns y below the table. k scales widths + text"""
    size, lh = size * k, lh * k; cols = [(h, w * k, al) for h, w, al in cols]
    if title: D.text((x, y), title, 'X-TITL', size=2.4 * k * 0.8, ha='left', va='top', weight='bold'); y -= 5 * k * 0.8
    W = sum(c[1] for c in cols)
    D.line([(x, y + 0.8), (x + W, y + 0.8)], 'X-TITL', lw=0.25)
    xx = x
    for h, w, al in cols:
        D.text((xx + (w - 1 if al == 'right' else 0), y), h, 'X-TITL', size=size * 0.9, ha='right' if al == 'right' else 'left', va='top', color=GREYT, weight='bold'); xx += w
    y -= lh * (1 + max(h.count('\n') for h, _, _ in cols)); D.line([(x, y + 0.9), (x + W, y + 0.9)], 'X-TITL', lw=0.15)
    for i, r in enumerate(rows):
        xx = x; nl = max(str(v).count('\n') for v in r) + 1
        last = bold_last and i == len(rows) - 1
        for (h, w, al), v in zip(cols, r):
            D.text((xx + (w - 1 if al == 'right' else 0), y), str(v), 'X-TITL', size=size, ha='right' if al == 'right' else 'left', va='top', weight='bold' if last else 'normal'); xx += w
        y -= lh * nl
    D.line([(x, y + 0.9), (x + W, y + 0.9)], 'X-TITL', lw=0.25)
    return y - 3 * k

def finish(S, F, side, no, title, scale_txt, legend=None, notes=None, y=None, x0=None):
    yy = y
    if legend: yy = legend_block(F, x0, yy - 2, 'LEGEND', legend)
    if notes: yy = notes_block(F, x0, yy - 2, 'NOTES', notes)
    S.place(side, 1, (0, 0), (0, 0)); S.place(F, 1, (0, 0), (0, 0))
    SH.SHEETS.append((no, title, scale_txt))

# --------------------------------------------------------------------------------------------- A-001 site plan
def site_sheet(no='A-001'):
    title = 'SITE PLAN + EXTERNAL WORKS'
    S, F, x0, y = new_sheet(no, title, '1:200 @ A0')
    D = ST.site_drawing(services=True)
    S.place(D, 200, (56.0, 24.5), (520, 440), clip=SH.DRAW_BOX)
    side = Drawing('side', paper=True)
    north(side, (960, 790)); scale_bar(side, (850, 760), 200, (0, 5, 10, 20))
    rc = ST.rain_calc()
    gfa_enc = sum(r['poly'].area for r in ROOMS if r['kind'] not in ('open',)); cover = SC.disc(SC.R_ROOF).area
    rows = [('SITE AREA (LOT 10150 + TENNIS COURT)', f'{SC.SITE.area:,.1f} M²'), ('BUILDING FOOTPRINT (ROOF EDGE Ø56.6)', f'{cover:,.0f} M²'),
            ('SITE COVERAGE', f'{cover / SC.SITE.area * 100:.0f} %'), ('ENCLOSED FLOOR AREA (GROSS, 3 FLOORS)', f'{gfa_enc:,.0f} M²'),
            ('ROOFED OPEN DECKS + ARCADE', f'{sum(o["poly"].area for o in M.OPEN):,.0f} M²'), ('PLOT RATIO (ENCLOSED / SITE)', f'1 : {SC.SITE.area / gfa_enc:.1f}'),
            ('HEIGHT: ROOF / MAST', '+16.200 / +30.000'), ('STAFF PARKING (BRIEF 5)', f'{sum(1 for k, _ in ST.PARK if k == "S")}'),
            ('OKU PARKING (BRIEF 1)', f'{sum(1 for k, _ in ST.PARK if k == "OKU")}'), ('MOTORCYCLE (BRIEF 10)', f'{len(ST.MOTOR)}'), ('BICYCLE (BRIEF 10)', f'{len(ST.BIKES)}')]
    yy = table(side, 850, 735, [('SITE DATA', 120, 'left'), ('', 45, 'right')], rows, title='SITE DATA', k=1.0)
    hs = (ST.HS_E.area + ST.HS_S.area) / 6.0
    rows = [('FIRE APPLIANCE ACCESS (BY-LAW 140)', f'{hs:.0f} M OF 6 M HARDSTANDING'), ('FACADE SERVED / PERIMETER', f'{hs / (2 * math.pi * M.R_L1) * 100:.0f} % OF {2 * math.pi * M.R_L1:.0f} M'),
            ('HYDRANT H1 TO HARDSTANDING S', f'{Point(ST.HYDRANTS[0][0]).distance(ST.HS_S):.0f} M (≤ 30)'), ('HYDRANT H2 TO HARDSTANDING E', f'{Point(ST.HYDRANTS[1][0]).distance(ST.HS_E):.0f} M (≤ 30)'),
            ('ROOF CATCHMENT (PETALS + FUNNEL)', f'{rc["A_roof"]:,.0f} + {rc["A_fun"]:,.0f} M²'), ('DESIGN STORM (TO MSMA 2ND ED.)', f'{ST.I_RAIN:.0f} MM/H'),
            ('PEAK RUN-OFF, ROOF', f'{rc["Q_roof"] + rc["Q_fun"]:.0f} L/S'), ('ON-SITE DETENTION (OSD)', 'SIZED BY C&S TO MSMA')]
    yy = table(side, 850, yy - 2, [('ACCESS + DRAINAGE', 105, 'left'), ('', 60, 'right')], rows, title='BOMBA ACCESS + DRAINAGE', k=1.0)
    drawing_title(side, (40, 40), '1', title, 200, 'SITE DATUM ±0.000 = ROAD CROWN (ASSUMED, TO SURVEY)')
    legend = [('line', dict(lw=0.4, ls='-.'), 'SITE BOUNDARY'), ('line', dict(lw=0.2, ls='--', color='#7A8590'), 'BUILDING SETBACK LINE'),
              ('line', dict(lw=0.4, ls='--', color=ST.RED), 'FIRE APPLIANCE HARDSTANDING 6 M'), ('circle', dict(fill=ST.RED, edge=ST.RED, r=1.2), 'PILLAR HYDRANT'),
              ('line', dict(lw=0.4, color=ST.BROWN), 'SEWER (uPVC Ø150) + IC / MH'), ('line', dict(lw=0.4, color=ST.CYAN), 'STORMWATER DRAIN'),
              ('line', dict(lw=0.4, color=ST.BLUE), 'WATER (HDPE)'), ('line', dict(lw=0.4, color=ST.RED, ls='--'), 'HOSE REEL MAIN'), ('line', dict(lw=0.4, color=ST.MAG, ls=':'), 'LV CABLE IN DUCT')]
    notes = ['ROAD NAMES AND LEVELS TO BE CONFIRMED BY THE TOPOGRAPHIC SURVEY. THE FORMER TENNIS COURT IS DEMOLISHED AND ADDED TO THE SITE.',
             'FORECOURTS RISE FROM ±0.000 AT THE ROAD TO +0.900 AT THE RING BRIDGE LINE AT 1:20 OR FLATTER (MS 1184), WITH LANDINGS.',
             'THE SOUTH HARDSTANDING IS PAVED FOR 30 T AND KEPT CLEAR BY REMOVABLE BOLLARDS; THE EAST ONE DOUBLES AS THE SERVICE YARD.']
    finish(S, F, side, no, title, '1:200', legend, notes, y, x0)
    return S, [(D, (0, 0))]

# --------------------------------------------------------------------------------------------- A-103 roof plan
def roof_sheet(no='A-103'):
    title = 'ROOF PLAN + ROOF DRAINAGE'
    S, F, x0, y = new_sheet(no, title, '1:100 @ A0')
    D = ST.roof_drawing()
    S.place(D, 100, tuple(C), (515, 425), clip=SH.DRAW_BOX)
    side = Drawing('side', paper=True)
    north(side, (1000, 790)); scale_bar(side, (850, 760), 100)
    rc = ST.rain_calc()
    rows = [('PETAL ROOF CATCHMENT', f'{rc["A_roof"]:,.0f} M²'), ('FUNNEL ROOF CATCHMENT', f'{rc["A_fun"]:,.0f} M²'), ('DESIGN INTENSITY i', f'{ST.I_RAIN:.0f} MM/H'),
            ('Q = C·i·A / 3600 (C = 1.0), PETALS', f'{rc["Q_roof"]:.0f} L/S'), ('DOWNPIPES Ø150 (PERIMETER + VALLEY)', f'{rc["n"]} NOS.'),
            ('FLOW PER DOWNPIPE', f'{rc["per"]:.1f} L/S ≤ 9 L/S'), ('FUNNEL → OCULUS → POOL', f'{rc["Q_fun"]:.0f} L/S'), ('POOL OVERFLOW 2 x Ø150 @ 1:50', 'TO PERIMETER DRAIN')]
    yy = table(side, 850, 735, [('RAINWATER', 110, 'left'), ('', 55, 'right')], rows, title='ROOF DRAINAGE CHECK', k=1.0)
    roof_spec = ['PETAL ROOFS: 0.9 MM ALUMINIUM STANDING SEAM (PVDF, SILVER-WHITE) ON 100 MM ROCKWOOL + BREATHER MEMBRANE ON STEEL PURLINS ON TAPERED RADIAL STEEL RAFTERS.',
                 'SEAMS RUN ALONG THE FALL (ROUND THE RING) TO THE VALLEYS AT THE TIMUR AND TENGAH GATES; 3° RADIAL CROSS FALL TO THE CONCEALED PERIMETER GUTTER.',
                 'FUNNEL ROOF: GRC-CLAD STEEL CONE FALLING 2.1 M TO THE Ø3 M OCULUS; RAIN DROPS 10.7 M INTO THE TITIK POOL (THE "TITIK" MOMENT).',
                 'GUTTERS: 1.6 MM STAINLESS STEEL 316 BOX GUTTERS, 400 WIDE, WITH SUMP OUTLETS + OVERFLOW WEIRS AT EVERY DOWNPIPE.',
                 'DOWNPIPES RUN INSIDE A FIN-PROFILE CASING ON THE FACADE LINE (SEE A-500 DETAIL 2) TO THE PERIMETER DRAIN.']
    yy = notes_block(side, 850, yy - 2, 'ROOF SPECIFICATION', roof_spec, width=60)
    drawing_title(side, (40, 40), '1', title, 100, 'SPOT LEVELS = TOP OF ROOF AT THE EDGE')
    legend = [('line', dict(lw=0.4, color=ST.CYAN), 'GUTTER / RAINWATER'), ('circle', dict(edge=ST.CYAN, r=1.0), 'RWDP Ø150'), ('line', dict(lw=0.3), 'FALL ARROW (DOWNHILL)'),
              ('line', dict(lw=0.15, color='#9AA3AD'), 'STANDING SEAM'), ('line', dict(lw=0.2, ls='--', color='#9AA3AD'), 'FIRST FLOOR EDGE BELOW')]
    finish(S, F, side, no, title, '1:100', legend, None, y, x0)
    return S, [(D, (0, 0))]

# --------------------------------------------------------------------------------------------- A-200 sections
def sections_sheet(no='A-200'):
    title = 'SECTIONS A-A + B-B'
    S, F, x0, y = new_sheet(no, title, '1:100 @ A0')
    (A, XA), (B, XB) = SE.section_set()
    S.place(A, 100, (0, 0), (60, 480)); S.place(B, 100, (0, 0), (60, 85))
    side = Drawing('side', paper=True)
    drawing_title(side, (60, 452), 'A', 'SECTION A-A', 100, 'THROUGH THE SELATAN (MAIN) GATE, COURT + UTARA BLOCK · LOOKING WEST · SOUTH ON THE LEFT')
    drawing_title(side, (60, 57), 'B', 'SECTION B-B', 100, 'THROUGH STAIR 4, THE WEST SHOPS, COURT + EAST HALL · LOOKING NORTH · WEST ON THE LEFT')
    scale_bar(side, (880, 452), 100)
    finish(S, F, side, no, title, '1:100', None, ['LEVELS IN METRES ABOVE SITE DATUM ±0.000. FLOOR ZONES: 600 (RC SLAB 250 + BEAMS + SERVICES); RING BRIDGE 350.',
           'CEILINGS (DASHED): GF +4.200, L1 +8.400, L2 +12.600 OR UNDER THE ROOF WHERE LOWER. CLEAR HEIGHTS: GF 3300, L1 3000-4300, L2 ≥ 2700.',
           'COLUMNS Ø350 RC ON PAD FOOTINGS (C&S TO DESIGN); ROOF RAFTERS CANTILEVER 5.3 M BEYOND RING C (R23) TO THE ROOF EDGE R28.3.'], y, x0)
    return S, [(A, (0, 0)), (B, (0, -45))]

def elevations_sheet(no, views):
    title = 'ELEVATIONS · ' + ' + '.join(v[1] for v in views)
    S, F, x0, y = new_sheet(no, title, '1:100 @ A0')
    side = Drawing('side', paper=True); dx = []
    for i, (vb, nm) in enumerate(views):
        E = SE.elevation(vb, nm[0]); yb = 470 if i == 0 else 75
        S.place(E, 100, (0, 0), (500, yb), clip=(22, yb - 25, SH.TB_X - 8, yb + 345))
        drawing_title(side, (60, yb - 22), str(i + 1), f'{nm} ELEVATION', 100, f'SEEN FROM BEARING {vb:.0f}°')
        dx.append((E, (0, -45 * i)))
    scale_bar(side, (880, 445), 100)
    finish(S, F, side, no, title, '1:100', [('fill', dict(fill='#8C949C', edge='#5E666E'), 'ALUMINIUM FIN 450 x 60, PVDF CHAMPAGNE-SILVER'),
           ('fill', dict(fill='#EEF1F3', edge='#9AA3AD'), 'DOUBLE-GLAZED LOW-E CURTAIN WALL BEHIND FINS'), ('fill', dict(fill='#3A4048'), 'SLAB EDGE: GRC CLAD, DARK BRONZE'),
           ('fill', dict(fill='#2B3036'), 'ROOF EDGE: ALUMINIUM FASCIA'), ('fill', dict(fill='#C9D3DA'), 'GROUND FLOOR GLAZING IN SHADE'), ('fill', dict(fill='#DCD8CF'), 'PLINTH: GRANITE-FACED, BUSH-HAMMERED')],
           ['FACADE OPTION A: VERTICAL FINS AT 750 CENTRES TURN FROM 18° (CLOSED, NEAR TANGENT) MID-PETAL TO 90° (OPEN, RADIAL) AT THE GATES, SO THE BUILDING OPENS WHERE PEOPLE ENTER.',
            'NO BRICK. GRC, ALUMINIUM, GLASS AND GRANITE ONLY.'], y, x0)
    return S, dx

# --------------------------------------------------------------------------------------------- F-000 fire strategy
def fire_strategy_sheet(no='F-000'):
    title = 'FIRE STRATEGY + CALCULATIONS'
    S, F, x0, y = new_sheet(no, title, 'NTS @ A0')
    D = Drawing('fire', paper=True)
    occ = M.occupancy(); byfl = {}
    for fl, nm, a, f, n in occ: byfl.setdefault(fl, []).append((nm, a, f, n))
    rows = []
    for fl in ('GF', 'L1', 'L2'):
        tot = 0
        for nm, a, f, n in byfl[fl]:
            rows.append((fl, nm[:40], f'{a:.0f}', f'{f}', f'{n}')); tot += n
        rows.append((fl, 'TOTAL FLOOR', '', '', f'{tot}'))
    y1 = table(D, 30, 805, [('FL', 12, 'left'), ('SPACE', 92, 'left'), ('AREA M²', 22, 'right'), ('M²/P', 18, 'right'), ('PERSONS', 22, 'right')], rows,
               title='1  OCCUPANT LOAD (UBBL 7TH SCHEDULE FACTORS)', size=1.55, lh=2.65)
    loads = {fl: sum(n for _, _, _, n in byfl[fl]) for fl in byfl}
    U = M.UNITS
    capL1 = 75 * (U['C1'] + U['C2'] + U['S3'] + U['S4']); capL2 = 75 * (U['C2'] + U['S3'])
    rows = [('L1 +5.400', 'C1 3 + C2 3 + S3 3 + S4 4 = 13 UNITS', f'{capL1}', f'{loads["L1"]}', 'OK' if capL1 >= loads['L1'] else 'FAIL'),
            ('L2 +9.600', 'C2 3 + S3 3 = 6 UNITS', f'{capL2}', f'{loads["L2"]}', 'OK' if capL2 >= loads['L2'] else 'FAIL'),
            ('GF +0.900', 'ALL ROOMS OPEN STRAIGHT TO THE ARCADE / COLONNADE AND 4 OPEN GATES', '—', f'{loads["GF"]}', 'OK')]
    y2 = table(D, 390, 805, [('FLOOR', 20, 'left'), ('STAIRS (UNIT = 550 MM)', 92, 'left'), ('CAPACITY', 22, 'right'), ('LOAD', 18, 'right'), ('', 14, 'right')], rows,
               title='2  EXIT CAPACITY (75 PERSONS / UNIT, ASSEMBLY STAIRS)', size=1.6)
    tv = {}
    for fl in ('L1', 'L2'):
        pl = M.PLATE[fl]; xs = np.linspace(pl.bounds[0], pl.bounds[2], 70); ys = np.linspace(pl.bounds[1], pl.bounds[3], 70); w1 = de = 0
        for xx in xs:
            for yy in ys:
                if not pl.contains(Point(xx, yy)): continue
                t = M.travel(fl, (xx, yy)); w1 = max(w1, t[0][0]); de = max(de, min(t[0][0], max(0.0, math.hypot(xx - C[0], yy - C[1]) - M.R_BR1)))
        tv[fl] = (w1, de)
    rows = [(fl, f'{tv[fl][0]:.1f}', '45.0', f'{tv[fl][1]:.1f}', '15.0', 'OK' if tv[fl][0] <= 45 and tv[fl][1] <= 15 else 'FAIL') for fl in ('L1', 'L2')]
    y2 = table(D, 390, y2 - 2, [('FLOOR', 20, 'left'), ('WORST TRAVEL M', 30, 'right'), ('LIMIT', 18, 'right'), ('WORST DEAD END', 32, 'right'), ('LIMIT', 18, 'right'), ('', 14, 'right')], rows,
               title='3  TRAVEL DISTANCE (UNSPRINKLERED, TWO DIRECTIONS)', size=1.6)
    enc = sum(r['poly'].area for r in ROOMS if r['kind'] not in ('open',)); op = sum(o['poly'].area for o in M.OPEN)
    nhr = SV.n_hose_reels(); st = SV.hr_storage(nhr)
    rows = [('PURPOSE GROUPS (5TH SCHEDULE)', 'V SHOP (MAIN) · VII ASSEMBLY (HALL, MUSOLLA, DECKS) · IV OFFICE'),
            ('STOREYS / TOP FLOOR HEIGHT', '3 / +9.600 (< 18 M: NO FIRE LIFT, NO DRY OR WET RISER)'),
            ('ENCLOSED FLOOR AREA', f'{enc:,.0f} M² → 10TH SCHEDULE BAND 1,001-3,000 M² (SHOP ≥ 2 STOREYS)'),
            ('REQUIRED (10TH SCHEDULE)', 'HOSE REEL (G) + AUTOMATIC DETECTION (1) + MANUAL ALARM (2) — ALL PROVIDED'),
            ('FLAG FOR BOMBA', f'IF THE ROOFED OPEN DECKS ({op:,.0f} M²) ARE COUNTED, TOTAL {enc + op:,.0f} M² > 3,000 M²\n→ SPRINKLERS. PUMP ROOM + TANK BAY SIZED TO TAKE THEM.'),
            ('HOSE REELS', f'{nhr} NOS. (GF 3, L1 3, L2 3) Ø25 x 30 M, EVERY POINT WITHIN 30 M + 6 M THROW'),
            ('HOSE REEL WATER STORAGE', f'2,275 + {nhr - 1} x 1,137.5 = {2275 + (nhr - 1) * 1137.5:,.0f} L → CAP {st:,.0f} L (9.1 M³ TANK)'),
            ('HOSE REEL PUMPS', 'DUTY + STANDBY (ELECTRIC, STANDBY ON GENSET) + JOCKEY, IN UTILITY BLOCK'),
            ('FIRE RESISTANCE', 'STRUCTURE 1 HR; STAIR + LIFT SHAFTS, MDB, LAN 1 HR, FD60 SELF-CLOSING DOORS'),
            ('SMOKE CONTROL', 'NATURAL: COURT, ARCADE AND DECKS OPEN ON 2+ SIDES; ENCLOSED ROOMS < 100 M²'),
            ('EMERGENCY LIGHTING + SIGNS', 'SELF-CONTAINED LED, 3 H (MS 619 / MS IEC 60598-2-22)'),
            ('FIRE ALARM INTERFACE', 'LIFTS HOME TO GF, VRF + FANS TRIP, HOLD-OPEN DOORS RELEASE, AUTO-DIAL TO BOMBA'),
            ('KITCHEN', 'HOOD WITH WET-CHEMICAL SUPPRESSION, SHUNT-TRIP OF COOKING POWER, 1 HR EXHAUST SHAFT'),
            ('FIRE APPLIANCE ACCESS', f'2 HARDSTANDINGS 6 M WIDE, {(ST.HS_E.area + ST.HS_S.area) / 6:.0f} M TOTAL, ≈ 1/3 OF THE PERIMETER (BY-LAW 140)'),
            ('HYDRANTS', '2 PILLAR HYDRANTS ON THE PUBLIC MAINS, ≤ 30 M FROM THE HARDSTANDINGS'),
            ('ASSEMBLY POINT', 'SOUTH-EAST LAWN BY THE SELATAN FORECOURT (SEE A-001)')]
    y3 = table(D, 390, y2 - 2, [('ITEM', 62, 'left'), ('PROVISION', 128, 'left')], rows, title='4  CLASSIFICATION + ACTIVE / PASSIVE PROVISION', size=1.6, lh=3.0)
    # mini escape diagram: the three plates with stairs
    Dd = Drawing('diag')
    for fl, col in (('L1', '#C9CED4'), ('L2', '#9AA3AD')):
        Dd.poly(M.PLATE[fl], 'A-SLAB', fill=col, edge=INK, lw=0.1, alpha=0.6)
    Dd.poly(SC.ann(M.R_BR0, M.R_BR1), 'A-SLAB', fill='#F6F7F8', edge=INK, lw=0.1)
    for c in CORES.values(): Dd.poly(c['stair_wall'], 'F-ESCP', fill=SV.GREEN, edge=None)
    Dd.poly(S4['poly'], 'F-ESCP', fill=SV.GREEN, edge=None)
    for s in SC.SPINES: Dd.text(P(31, s['b']), s['k'], 'A-ANNO', size=3.0, weight='bold')
    S.place(Dd, 250, tuple(C), (190, 250))
    D.text((30, y1 - 4), '5  ESCAPE DIAGRAM (1:250)', 'X-TITL', size=3.6, ha='left', va='top', weight='bold')
    D.text((30, 95), 'GREEN = PROTECTED STAIRS C1, C2 (ENCLOSED, FD60), OPEN STAIR S3, EXTERNAL STAIR S4.\nLIGHT GREY = FIRST FLOOR, DARK = SECOND FLOOR. EVERY FLOOR HAS ≥ 2 STAIRS IN DIFFERENT DIRECTIONS.', 'X-TITL', size=2.6, ha='left', va='top')
    drawing_title(D, (40, 30), 'F', title, None, 'UBBL 1984 (PART VII + 10TH SCHEDULE) · MS 1184 · TO BE AGREED WITH BOMBA AT THE FIRE PLAN SUBMISSION')
    finish(S, F, D, no, title, 'NTS', None, ['BASIS: UBBL 1984 AS AMENDED. WHERE THIS SHEET STATES A FIGURE IT IS COMPUTED FROM THE MODEL ON THE SAME DATE AS THE PLANS.'], y, x0)
    return S, []

# --------------------------------------------------------------------------------------------- P-000 plumbing schematic + calcs
def plumbing_calc_sheet(no='P-000'):
    title = 'COLD WATER + SANITARY SCHEMATIC, CALCULATIONS'
    S, F, x0, y = new_sheet(no, title, 'NTS @ A0')
    D = Drawing('pl', paper=True)
    rows = [('STAFF (MANAGEMENT 12 + TENANTS 16 + CAFE 4)', '32 P', '70 L', '2,240'), ('VISITORS (PEAK DAY, ESTIMATE)', '1,000 P', '5 L', '5,000'),
            ('CAFE (MEALS)', '100', '10 L', '1,000'), ('MUSOLLA WUDHU', '300', '3 L', '900'), ('CLEANING + LANDSCAPE', '—', '—', '1,000'), ('TOTAL DAILY DEMAND', '', '', '10,140 L')]
    y1 = table(D, 30, 805, [('USE', 90, 'left'), ('NO.', 20, 'right'), ('L / UNIT / DAY', 26, 'right'), ('L / DAY', 24, 'right')], rows, title='1  WATER DEMAND (PROVISIONAL — SPAN TO CONFIRM)', bold_last=True)
    rows = [('SUCTION TANK (UTILITY BLOCK, GROUND)', '2 x 1.5 x 2.0', '6.0 M³'), ('ROOF TANK (TANK ROOM ON CORE 2, FL +12.900)', '2 NOS. 2 x 2 x 1 SECTIONAL FRP', '7.2 M³'),
            ('TOTAL DOMESTIC STORAGE', '≥ 1 DAY', '13.2 M³ ≥ 10.1'), ('FIRE (HOSE REEL) TANK, SEPARATE', 'UBBL 10TH SCHEDULE CAP', '9.1 M³')]
    y1 = table(D, 30, y1 - 2, [('STORAGE', 90, 'left'), ('SIZE', 46, 'left'), ('VOLUME', 24, 'right')], rows, title='2  STORAGE')
    fx = [('PUBLIC TOILETS (2 BANKS: GF + L1)', 'MALE', '3 WC (PwD, PARENT, STD) + 2 URINALS + 3 BASINS PER BANK'), ('', 'FEMALE', '3 WC (PwD, PARENT, STD) + 3 BASINS PER BANK'),
          ('STAFF RESTROOMS (GF)', 'M + F', '2 WC (1 PwD) + 2 SHOWERS + 2 BASINS + LOCKERS EACH'), ('PARENTS ROOM (GF)', '', 'CHANGING COUNTER + SINK; NURSING BASIN'),
          ('ADMIN (L1)', '', 'PwD WC + BASIN; PANTRY SINK'), ('MUSOLLA (L2)', 'M + F', '6 WUDHU TAPS + FOOT TROUGH EACH'), ('JANITORS (3)', '', 'MOP SINK + TAP'),
          ('SHOPS (8)', '', 'PREP SINK EACH'), ('CAFE', '', 'DOUBLE SINK + HAND BASIN, VIA GREASE TRAP'), ('HAND WASH (B3)', '', '6 BASINS IN A TROUGH BY THE CAFE')]
    y1 = table(D, 30, y1 - 2, [('AREA', 62, 'left'), ('', 16, 'left'), ('FITTINGS', 104, 'left')], fx, title='3  SANITARY FITTINGS PROVIDED')
    rc = ST.rain_calc()
    rows = [('SOIL + VENT STACKS', 'SVP 1 + 2 (TOILET BANKS), SVP W (WUDHU, COLUMN 21/B), SVP SW (ADMIN, COLUMN 13/B)'),
            ('BELOW-SLAB DRAINS', 'uPVC Ø100 AT 1:60 MIN TO IC AT R31; MAX 6 M FROM A WC TO THE STACK'),
            ('EXTERNAL SEWER', 'uPVC Ø150 AT 1:100 IN 3 LINES (E, N, W) TO MH-S → IWK PUBLIC SEWER (SOUTH ROAD)'),
            ('GREASE TRAP', 'PRECAST, 2-CHAMBER, OUTSIDE THE CAFE KITCHEN (NORTH)'),
            ('RAINWATER', f'{rc["n"]} RWDP Ø150 ({rc["per"]:.1f} L/S EACH) → 300 U-DRAIN → OSD → ROADSIDE DRAIN'),
            ('POOL', 'OCULUS RAIN + MAKE-UP WATER; 2 x Ø150 OVERFLOW; RECIRCULATION PLANT IN PUMP ROOM')]
    y1 = table(D, 30, y1 - 2, [('DRAINAGE', 50, 'left'), ('', 132, 'left')], rows, title='4  SANITARY + RAINWATER')
    # schematic (paper mm): vertical cold water riser diagram
    X0, Y0 = 420, 520; lv = {'GF': 0, 'L1': 75, 'L2': 140, 'TR': 200}
    for k, z in lv.items():
        D.line([(X0 - 20, Y0 + z), (X0 + 330, Y0 + z)], 'P-CWAT', lw=0.15, color='#9AA3AD', ls='--')
        D.text((X0 - 22, Y0 + z + 2), {'GF': 'GF +0.900', 'L1': 'L1 +5.400', 'L2': 'L2 +9.600', 'TR': 'TANK ROOM +12.900'}[k], 'X-TITL', size=1.8, ha='right', va='bottom', weight='bold')
    def bx(x, yy, w, h, t, col=ST.BLUE):
        D.poly(box(x, yy, x + w, yy + h), 'P-EQPT', fill='white', edge=col, lw=0.3); D.text((x + w / 2, yy + h / 2), t, 'P-EQPT', size=1.6, color=col, weight='bold')
    bx(X0 - 10, Y0 - 45, 40, 18, 'SPAN METER\nØ50')
    bx(X0 + 50, Y0 - 45, 46, 18, 'SUCTION TANK\n6 M³')
    bx(X0 + 116, Y0 - 45, 46, 18, 'TRANSFER PUMPS\nDUTY + STANDBY')
    bx(X0 + 116, Y0 + lv['TR'] + 4, 56, 20, 'ROOF TANK 7.2 M³\nCORE 2')
    bx(X0 + 190, Y0 + lv['TR'] + 4, 46, 20, 'BOOSTER SET\nVSD, DUTY+STBY')
    bx(X0 + 190, Y0 - 45, 46, 18, 'FIRE TANK 9.1 M³', ST.RED); bx(X0 + 256, Y0 - 45, 50, 18, 'HOSE REEL PUMPS\nD + S + JOCKEY', ST.RED)
    D.line([(X0 + 30, Y0 - 36), (X0 + 50, Y0 - 36)], 'P-CWAT', lw=0.4, color=ST.BLUE); D.line([(X0 + 96, Y0 - 36), (X0 + 116, Y0 - 36)], 'P-CWAT', lw=0.4, color=ST.BLUE)
    D.line([(X0 + 162, Y0 - 36), (X0 + 176, Y0 - 36), (X0 + 176, Y0 + lv['TR'] + 14), (X0 + 172, Y0 + lv['TR'] + 14)], 'P-CWAT', lw=0.4, color=ST.BLUE)
    D.text((X0 + 179, Y0 + 100), 'Ø50 RISING MAIN', 'P-CWAT', size=1.5, color=ST.BLUE, ha='left', rot=90)
    D.line([(X0 + 130, Y0 + lv['TR'] + 4), (X0 + 130, Y0 + 3), (X0 + 20, Y0 + 3)], 'P-CWAT', lw=0.4, color=ST.BLUE)
    D.text((X0 + 60, Y0 + 5), 'GRAVITY DOWN-FEED → GF RING Ø50 (ALL GF FITTINGS)', 'P-CWAT', size=1.5, color=ST.BLUE, ha='left', va='bottom')
    D.line([(X0 + 172, Y0 + lv['TR'] + 14), (X0 + 190, Y0 + lv['TR'] + 14)], 'P-CWAT', lw=0.4, color=ST.BLUE)
    D.line([(X0 + 236, Y0 + lv['TR'] + 14), (X0 + 250, Y0 + lv['TR'] + 14), (X0 + 250, Y0 + lv['L1'] + 3), (X0 + 320, Y0 + lv['L1'] + 3)], 'P-CWAT', lw=0.4, color=ST.BLUE)
    D.line([(X0 + 250, Y0 + lv['L2'] + 3), (X0 + 320, Y0 + lv['L2'] + 3)], 'P-CWAT', lw=0.4, color=ST.BLUE)
    D.text((X0 + 255, Y0 + lv['L1'] + 5), 'BOOSTED: L1 TOILETS, JANITOR, PANTRY', 'P-CWAT', size=1.5, color=ST.BLUE, ha='left', va='bottom')
    D.text((X0 + 255, Y0 + lv['L2'] + 5), 'BOOSTED: WUDHU M + F, JANITOR', 'P-CWAT', size=1.5, color=ST.BLUE, ha='left', va='bottom')
    D.line([(X0 + 306, Y0 - 36), (X0 + 320, Y0 - 36), (X0 + 320, Y0 + lv['L2'] + 40)], 'F-EQPT', lw=0.4, color=ST.RED, ls='--')
    for k in ('GF', 'L1', 'L2'):
        D.line([(X0 + 320, Y0 + lv[k] + 12), (X0 + 328, Y0 + lv[k] + 12)], 'F-EQPT', lw=0.4, color=ST.RED); D.text((X0 + 330, Y0 + lv[k] + 12), 'HR x 3', 'F-EQPT', size=1.5, color=ST.RED, ha='left')
    D.text((X0 + 60, Y0 + lv['TR'] + 46), '5  COLD WATER + HOSE REEL SCHEMATIC (NTS)', 'X-TITL', size=2.4, ha='left', weight='bold')
    # sanitary stack diagram
    X1, Y1 = 420, 110
    D.text((X1, Y1 + 210), '6  SOIL STACK DIAGRAM (NTS)', 'X-TITL', size=2.4, ha='left', weight='bold')
    for i, (nm, fls) in enumerate((('SVP 1', 'GF L1'), ('SVP 2', 'GF L1'), ('SVP W', 'L2'), ('SVP SW', 'L1'))):
        x = X1 + 20 + i * 75
        D.line([(x, Y1), (x, Y1 + 170)], 'P-SANI', lw=0.5, color=ST.BROWN)
        D.text((x, Y1 + 175), nm + ' Ø100\nVENT 600 ABOVE ROOF', 'P-SANI', size=1.5, color=ST.BROWN, va='bottom')
        for k, z in (('GF', 10), ('L1', 75), ('L2', 140)):
            if k in fls: D.line([(x, Y1 + z + 6), (x + 30, Y1 + z + 12)], 'P-SANI', lw=0.35, color=ST.BROWN); D.text((x + 32, Y1 + z + 12), f'{k} WCs / BASINS', 'P-SANI', size=1.3, color=ST.BROWN, ha='left')
        D.line([(x, Y1), (x + 40, Y1 - 10)], 'P-SANI', lw=0.5, color=ST.BROWN); D.poly(box(x + 38, Y1 - 14, x + 46, Y1 - 6), 'P-SANI', fill='white', edge=ST.BROWN, lw=0.3)
        D.text((x + 42, Y1 - 18), 'IC', 'P-SANI', size=1.4, color=ST.BROWN)
    drawing_title(D, (40, 30), 'P', title, None, 'SPAN UNIFORM TECHNICAL GUIDELINES · MS 1228 (SEWERAGE) · MSMA 2ND ED. — FIGURES PROVISIONAL, M&E TO CONFIRM')
    finish(S, F, D, no, title, 'NTS', None, None, y, x0)
    return S, []

# --------------------------------------------------------------------------------------------- A-600 schedules
DOOR_DESC = {'D1': 'SINGLE SWING 900, SOLID CORE, LEVER + CLOSER', 'D2': 'SINGLE SWING 1000, HPL, KICK PLATE (TOILETS)', 'D3': 'SINGLE SWING 1200, 900 + 300 LEAF',
             'D4': 'DOUBLE 1500, STEEL (SERVICE)', 'D5': 'DOUBLE 1800, GLAZED (HALL, GALLERY)', 'D6': 'STAIR DOOR FD60, SELF-CLOSING, VISION PANEL, PANIC BAR',
             'SF': 'SHOPFRONT FRAMELESS SLIDING 1800, 12 MM TOUGHENED', 'GD': 'AUTO GLASS SLIDING 1800', 'RS': 'ROLLER SHUTTER 3000 x 3000 (LOADING)', 'LD': 'LIFT LANDING DOOR 900 (FIRE RATED)'}
FINISH = [('SHOPS + CAFE', 'POLISHED CONCRETE, SEALED', 'SKIM + PAINT (TENANT FIT-OUT)', 'EXPOSED SOFFIT, PAINTED'),
          ('TOILETS / WUDHU / RESTROOMS', 'ANTI-SLIP PORCELAIN R11, 600 x 600', 'PORCELAIN TILE TO 2100, PAINT ABOVE', 'MOISTURE-RESISTANT BOARD'),
          ('ADMIN / GALLERY / HALL', 'VINYL PLANK / TERRAZZO (GALLERY)', 'SKIM + PAINT', 'ACOUSTIC MINERAL FIBRE 600 x 600'),
          ('MUSOLLA', 'CARPET TILE ON RAISED SCREED', 'SKIM + PAINT, TIMBER DADO', 'ACOUSTIC BOARD'),
          ('ARCADE / DECKS / BRIDGE', 'GRANITE 600 x 300 FLAMED (EXTERNAL)', '—', 'GRC SOFFIT PANELS'),
          ('COURT', 'TERRAZZO WITH BRASS "TALAM" RINGS', '—', 'GRC FUNNEL SOFFIT'),
          ('PLANT / STORES / LOADING', 'POWER-FLOATED CONCRETE, EPOXY', 'FAIR-FACED BLOCK, PAINT', 'EXPOSED')]
def schedules_sheet(no='A-600'):
    title = 'SCHEDULES · ROOMS vs BRIEF, DOORS, FINISHES'
    S, F, x0, y = new_sheet(no, title, 'NTS @ A0')
    D = Drawing('sch', paper=True)
    groups = {}
    for r in ROOMS:
        if not r['brief'] or not r['brief'][1]: continue
        net = r['poly'].buffer(-0.075, join_style=2).area if r['kind'] != 'open' else r['poly'].area
        groups.setdefault(r['brief'][0], []).append((r['fl'], r['key'], r['name'], r['brief'][1], net))
    rows = []
    for g in sorted(groups):
        for fl, k, nm, req, net in groups[g]:
            rows.append((g, fl, k, nm[:44], f'{req}', f'{net:.1f}', 'OK' if net >= req - 0.05 else 'SHORT'))
    extra = [('B3', 'GF', 'COURT', 'OPEN SEATING (100) IN TALAM COURT', '100 P', '100 P', 'OK'), ('B3', 'GF', 'COURT', "CHILDREN'S PLAY", '30', f"{SC.sector(*plans.PLAY).intersection(SC.ann(3.3, M.R_COURT - 0.3)).area:.0f}", 'OK'),
             ('D1', 'GF', 'GATE', 'COVERED ARRIVAL (SELATAN GATE UNDER L1)', '50', f"{SC.strip(182.7, 8.0, M.R_BR1, M.R_L1).intersection(SC.disc(M.R_L1)).area:.0f}", 'OK'),
             ('E', 'EXT', 'UB', 'REFUSE WET / DRY, GENSET, SUCTION TANK, PUMPS', '18/18/15/15', '18/18/15/15', 'OK'), ('F', 'EXT', 'PARK', 'STAFF 5 + OKU 1 + MOTOR 10 + BIKE 10', '5+1+10+10', f'{sum(1 for k, _ in ST.PARK if k == "S")}+1+{len(ST.MOTOR)}+{len(ST.BIKES)}', 'OK')]
    y1 = table(D, 30, 805, [('BRIEF', 12, 'left'), ('FL', 10, 'left'), ('NO.', 14, 'left'), ('ROOM', 84, 'left'), ('BRIEF M²', 20, 'right'), ('NET M²', 18, 'right'), ('', 14, 'right')],
               rows + extra, title='1  ROOMS vs BRIEF (BRIEF_SITE_C, SCHEDULE OF ACCOMMODATION)', size=1.5, lh=2.55)
    cnt = {}
    for dd in M.DOORS + M.CORE_DOORS: cnt[(dd['tag'], dd['fire'] or '')] = cnt.get((dd['tag'], dd['fire'] or ''), 0) + 1
    rows = [(t, DOOR_DESC.get(t, ''), f or '—', f'{n}') for (t, f), n in sorted(cnt.items())]
    y2 = table(D, 400, 805, [('TYPE', 12, 'left'), ('DESCRIPTION', 120, 'left'), ('FIRE', 16, 'left'), ('NO.', 12, 'right')], rows, title='2  DOOR SCHEDULE (COUNTED FROM THE PLANS)', size=1.6)
    y2 = table(D, 400, y2 - 2, [('ROOM TYPE', 44, 'left'), ('FLOOR', 44, 'left'), ('WALL', 44, 'left'), ('CEILING', 44, 'left')], [tuple(wrap(v, 26) for v in r) for r in FINISH], title='3  FINISHES', size=1.5, lh=2.7)
    gl = [('G1', 'CURTAIN WALL, DGU 6 LOW-E + 12 + 6 HS, U ≤ 2.0, SHGC ≤ 0.35 (MS 1525)', 'L1/L2 FACADE BEHIND FINS'), ('G2', 'SHOPFRONT 12 MM TOUGHENED, FRAMELESS', 'GF SHOPS, CAFE'),
          ('G3', 'FIXED GLAZED SCREEN 10.38 LAMINATED', 'ADMIN, GALLERY SIDES'), ('G4', 'BALUSTRADE 17.52 LAMINATED, 1100 HIGH', 'RING BRIDGE, DECK EDGES')]
    y2 = table(D, 400, y2 - 2, [('TYPE', 12, 'left'), ('SPECIFICATION', 100, 'left'), ('WHERE', 64, 'left')], gl, title='4  GLAZING', size=1.6)
    drawing_title(D, (40, 30), 'S', title, None, 'AREAS ARE NET (INSIDE WALL FACES) MEASURED FROM THE PLAN MODEL')
    finish(S, F, D, no, title, 'NTS', None, None, y, x0)
    return S, []

# --------------------------------------------------------------------------------------------- A-500 details
def _dim(D, a, b, off, txt, layer='A-DIMS'):
    a, b = np.array(a, float), np.array(b, float); t = (b - a) / np.linalg.norm(b - a); n = np.array([-t[1], t[0]]) * off
    D.line([a + n, b + n], layer, lw=0.09); D.line([a, a + n * 1.15], layer, lw=0.07); D.line([b, b + n * 1.15], layer, lw=0.07)
    for q in (a + n, b + n): D.line([q - (t + n / max(abs(off), 1e-6) * 0) * 0.04 - t * 0.04 + n / abs(off) * 0.04, q + t * 0.04 - n / abs(off) * 0.04], layer, lw=0.18)
    D.text((a + b) / 2 + n * 1.6, txt, layer, size=1.6, rot=math.degrees(math.atan2(t[1], t[0])) if abs(t[0]) > 0.01 else 90)
def lead(D, p, q, txt, ha='left'):
    D.line([p, q], 'A-ANNO', lw=0.09); D.circle(p, 0.012, 'A-ANNO', fill=INK, edge=None)
    D.text(np.array(q) + (0.03 if ha == 'left' else -0.03, 0), txt, 'A-ANNO', size=1.9, ha=ha, va='center')

def detail_facade():
    """1:20 vertical section through the first-floor edge, fins, glazing, L2 edge and the roof edge (local x = radius - 26.5)"""
    D = Drawing('DET 1'); z0 = 4.4
    hatch = '#BFC4CA'
    # L1 slab edge beam 600, GRC fascia, soffit
    D.poly(box(-1.6, 4.8, 0.0, 5.4), 'S-DETL', fill=hatch, edge=INK, lw=0.25); D.poly(box(-0.35, 4.55, 0.0, 4.8), 'S-DETL', fill=hatch, edge=INK, lw=0.25)
    D.poly(box(0.0, 4.5, 0.03, 5.45), 'A-ELEV', fill='#3A4048', edge=INK, lw=0.1)
    D.poly(box(-1.6, 5.4, 0.0, 5.45), 'A-ELEV', fill='#DCD8CF', edge=INK, lw=0.1)
    # glazing line (curtain wall) set back 150 from the slab edge, mullion + transoms
    D.poly(box(-0.25, 5.45, -0.15, 9.0), 'A-GLAZ', fill='#BFD9E6', edge=INK, lw=0.15)
    D.poly(box(-0.28, 5.45, -0.12, 5.6), 'A-GLAZ', fill='#9AA3AD', edge=INK, lw=0.1)
    # L2 slab (where present) + roof
    D.poly(box(-1.6, 9.0, 0.0, 9.6), 'S-DETL', fill=hatch, edge=INK, lw=0.25); D.poly(box(0.0, 8.95, 0.03, 9.65), 'A-ELEV', fill='#3A4048', edge=INK, lw=0.1)
    D.poly(box(-0.25, 9.65, -0.15, 15.6), 'A-GLAZ', fill='#BFD9E6', edge=INK, lw=0.15)
    zt = 16.2
    D.poly(Polygon([(-1.6, zt - 0.5), (0.0, zt - 0.5), (1.8, zt - 0.12), (1.8, zt), (-1.6, zt)]), 'S-DETL', fill='#E6E8EB', edge=INK, lw=0.25)
    D.poly(box(-1.6, zt - 0.5, 1.8, zt - 0.45), 'S-DETL', fill=INK, edge=None)
    D.poly(box(1.35, zt - 0.32, 1.75, zt - 0.05), 'P-RAIN', fill='#D8ECF7', edge='#1AA0C8', lw=0.15)
    # fin (seen in elevation) 450 deep from the slab edge, fixed at both ends
    D.poly(box(0.03, 5.45, 0.48, zt - 0.55), 'A-ELEV', fill='#C4CAD0', edge=INK, lw=0.15)
    for zz in (5.6, zt - 0.7): D.poly(box(0.0, zz - 0.05, 0.12, zz + 0.05), 'S-DETL', fill=INK, edge=None)
    D.line([(-1.6, 8.4), (-0.25, 8.4)], 'A-HIDN', lw=0.13, ls='--'); D.line([(-1.6, 15.0), (-0.25, 15.0)], 'A-HIDN', lw=0.13, ls='--')
    lead(D, (-0.8, 5.1), (-2.2, 4.0), 'RC EDGE BEAM 600 + SLAB 250,\nGRC FASCIA 20 DARK BRONZE', 'right')
    lead(D, (-0.2, 7.0), (-2.2, 7.0), 'CURTAIN WALL G1: DGU 6 LOW-E +12+ 6 HS,\nALUMINIUM 65 x 150 MULLIONS @ 1500', 'right')
    lead(D, (0.25, 11.0), (1.2, 11.0), 'ALUMINIUM FIN 450 x 60 HOLLOW,\nPVDF, ANGLE 18°-90° (SET\nPER BAY), PIN BRACKETS\nTOP + BOTTOM, 750 C/C')
    lead(D, (1.55, zt - 0.2), (2.2, zt + 0.6), 'CONCEALED GUTTER SS316 400 W,\nSUMP + Ø150 OUTLET → RWDP\nIN FIN CASING (DETAIL 2)')
    lead(D, (-0.8, zt - 0.2), (-2.2, zt + 0.7), 'STANDING SEAM 0.9 AL, 100 ROCKWOOL,\nPURLINS ON TAPERED STEEL RAFTER', 'right')
    lead(D, (-0.8, 9.3), (-2.2, 9.9), 'L2 SLAB (CRESTS ONLY) — ELSEWHERE\nTHE GLAZING RUNS TO THE ROOF', 'right')
    for z, t in ((5.4, '+5.400 FFL L1'), (9.6, '+9.600 FFL L2'), (zt, '+10.200 TO +16.200 ROOF')):
        D.text((2.0, z), t, 'A-DIMS', size=1.6, ha='left', weight='bold')
    _dim(D, (0.0, 4.3), (0.48, 4.3), -0.25, '450')
    _dim(D, (0.0, zt + 0.25), (1.8, zt + 0.25), 0.2, '1800 ROOF OVERHANG')
    return D

def detail_rwdp():
    """1:10 plan through the facade line: a downpipe hidden in a fin-shaped casing between two fins"""
    D = Drawing('DET 2')
    D.poly(box(-1.2, -0.4, 1.2, 0.0), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.2)
    D.poly(box(-1.2, -0.03, 1.2, 0.0), 'A-ELEV', fill='#3A4048', edge=None)
    for x in (-0.75, 0.75):
        D.poly(box(x - 0.03, 0.0, x + 0.03, 0.45), 'A-ELEV', fill='#C4CAD0', edge=INK, lw=0.12)
    D.poly(box(-0.11, 0.0, 0.11, 0.45), 'A-ELEV', fill='#C4CAD0', edge=INK, lw=0.15)
    D.circle((0.0, 0.2), 0.08, 'P-RAIN', fill='#D8ECF7', edge='#1AA0C8', lw=0.2)
    lead(D, (0.0, 0.2), (0.45, 0.7), 'RWDP Ø150 uPVC (SHOWN Ø160 OD) IN\n220 x 450 ALUMINIUM CASING, SAME FINISH\nAS THE FINS; ACCESS PANEL AT 1 M')
    lead(D, (0.75, 0.35), (1.0, 0.95), 'TYPICAL FIN 450 x 60')
    lead(D, (-0.6, -0.2), (-1.1, -0.75), 'SLAB EDGE + GRC FASCIA', 'right')
    _dim(D, (-0.75, 0.55), (0.75, 0.55), 0.12, '1500 = 2 FIN BAYS')
    return D

def detail_soffit():
    """1:20 section through the hanging first floor over a concave gate (radial section, x = radius)"""
    D = Drawing('DET 3')
    D.poly(box(19.0, 4.8, 26.5, 5.4), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.25)
    D.poly(Polygon([(23.0, 4.8), (26.5, 5.05), (26.5, 4.8)]), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.25)
    D.poly(Polygon([(19.0, 4.55), (23.0, 4.55), (26.47, 4.98), (26.5, 5.0), (26.5, 4.96), (23.0, 4.52), (19.0, 4.52)]), 'A-ELEV', fill='#DCD8CF', edge=INK, lw=0.12)
    D.poly(box(22.82, 0.9, 23.18, 4.8), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.25)
    D.line([(18.5, 0.9), (27.0, 0.9)], 'A-SITE', lw=0.3)
    lead(D, (21.0, 4.53), (20.0, 3.4), 'GRC SOFFIT PANELS 15 MM ON STAINLESS\nHANGERS, CURVED TO THE CONVEX EDGE;\nLINEAR LED IN THE SHADOW GAP', 'right')
    lead(D, (25.0, 5.2), (25.4, 6.3), 'RC CANTILEVER 3.5 M FROM RING C,\nTAPERED 600 → 250 AT THE EDGE')
    lead(D, (23.0, 2.5), (24.2, 2.0), 'RING C COLUMN Ø350 (GRID C)')
    lead(D, (19.6, 4.53), (19.6, 3.0), 'L1 WC DRAIN Ø100 1:40\nIN SOFFIT VOID (ADMIN)', 'right')
    _dim(D, (23.0, 5.6), (26.5, 5.6), 0.25, '3500 HANGING FIRST FLOOR')
    _dim(D, (27.0, 0.9), (27.0, 4.52), -0.3, '3620 CLEAR')
    return D

def detail_pool():
    """1:20 section through the Titik pool and the mast base (x = distance from C)"""
    D = Drawing('DET 4')
    D.poly(box(-3.2, 0.1, 3.2, 0.3), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.25)
    for sg in (-1, 1): D.poly(box(sg * 2.5 - (0.2 if sg > 0 else 0), 0.1, sg * 2.5 + (0.2 if sg < 0 else 0), 0.9), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.25)
    D.poly(box(-2.3, 0.3, 2.3, 0.72), 'A-SITE', fill='#D8ECF7', edge='#1AA0C8', lw=0.15)
    D.poly(box(-1.2, -0.9, 1.2, 0.1), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.25)
    D.poly(Polygon([(-0.42, 0.3), (0.42, 0.3), (0.36, 2.6), (-0.36, 2.6)]), 'A-ELEV', fill='#E6E8EB', edge=INK, lw=0.2)
    D.poly(box(-0.6, 0.3, 0.6, 0.36), 'S-DETL', fill=INK, edge=None)
    D.line([(-3.4, 0.9), (-2.7, 0.9)], 'A-SITE', lw=0.3); D.line([(2.7, 0.9), (3.4, 0.9)], 'A-SITE', lw=0.3)
    D.poly(box(2.05, 0.62, 2.25, 0.72), 'P-RAIN', fill='white', edge='#1AA0C8', lw=0.12)
    lead(D, (0.0, 2.2), (0.8, 2.6), 'STEEL MAST Ø840 → Ø200 AT +30.000, PAINTED\nCHAMPAGNE; AIR TERMINAL + AVIATION LIGHT AT TOP')
    lead(D, (0.0, -0.4), (1.6, -0.7), 'RC PILE CAP 2400 x 2400 x 1000\nON BORED PILES (C&S), HD BOLTS M36 x 8')
    lead(D, (-1.5, 0.55), (-2.4, 2.3), 'WATER 420 DEEP, BLACK GRANITE,\nWATERPROOFED RC TANK,\nTACTILE EDGE KERB (MS 1184)', 'right')
    lead(D, (2.15, 0.67), (1.3, 1.9), 'OVERFLOW WEIR → 2 x Ø150\nTO PERIMETER DRAIN')
    D.text((0, 1.6), 'RAIN FROM THE OCULUS\n(+11.400) FALLS HERE', 'A-ANNO', size=1.6, color='#1AA0C8')
    _dim(D, (-2.5, -1.2), (2.5, -1.2), -0.2, '5000 POOL')
    return D

def detail_stair():
    """1:20 section of a stair flight: riser 173, going 280, handrails, nosings"""
    D = Drawing('DET 5'); h, g = 4.5 / 26, M.GO
    pts = [(0, 0)]
    for i in range(6): pts += [(i * g, (i + 1) * h), ((i + 1) * g, (i + 1) * h)]
    D.poly(Polygon(pts + [(6 * g, 6 * h - 0.3), (0, -0.3)]), 'S-DETL', fill='#BFC4CA', edge=INK, lw=0.25)
    for i in range(6): D.line([(i * g + 0.0, (i + 1) * h + 0.9), ((i + 1) * g, (i + 2) * h + 0.9)], 'A-STRS', lw=0.15)
    D.line([(0, 0.9 + h), (6 * g, 0.9 + 7 * h)], 'A-STRS', lw=0.35)
    lead(D, (3 * g, 3.5 * h + 0.9), (2.2, 2.4), 'HANDRAIL Ø50 SS, 900-1000 ABOVE PITCH LINE,\nBOTH SIDES, EXTENDS 300 PAST TOP + BOTTOM')
    lead(D, (2 * g, 3 * h), (2.2, 0.5), 'NOSING: CONTRASTING ANTI-SLIP STRIP 50 (MS 1184)')
    _dim(D, (0, 1 * h), (g, 1 * h), -0.12, '280')
    _dim(D, (g * 1.0, h), (g * 1.0, 2 * h), 0.15, '173')
    return D

def details_sheet(no='A-500'):
    title = 'DETAILS'
    S, F, x0, y = new_sheet(no, title, 'AS SHOWN @ A0')
    side = Drawing('side', paper=True)
    d1 = detail_facade(); S.place(d1, 20, (0.0, 4.3), (165, 135))
    drawing_title(side, (40, 100), '1', 'FACADE SECTION AT THE FIRST-FLOOR EDGE', 20, 'FINS, CURTAIN WALL, SLAB EDGE, ROOF EDGE')
    d3 = detail_soffit(); S.place(d3, 20, (19.0, 0.9), (390, 475))
    drawing_title(side, (360, 445), '3', 'HANGING FIRST FLOOR OVER A CONCAVE GATE', 20)
    D6 = plans.plan_drawing('GF')
    bm = M.mid('G01')[0]; cen = P(16.0, (bm + M.mid('G02')[0]) / 2)
    S.place(D6, 50, tuple(cen), (920, 680), clip=(825, 565, 1018, 800))
    drawing_title(side, (825, 545), '6', 'PUBLIC TOILETS, BANK 1', 50, 'PwD 2200 x 1850 · TURNING CIRCLE 1500 · DOOR 900 OUT')
    d2 = detail_rwdp(); S.place(d2, 10, (0.0, 0.0), (480, 300))
    drawing_title(side, (360, 205), '2', 'DOWNPIPE IN FIN CASING (PLAN)', 10)
    d4 = detail_pool(); S.place(d4, 20, (0.0, 0.0), (860, 300))
    drawing_title(side, (690, 215), '4', 'TITIK POOL + MAST BASE', 20)
    d5 = detail_stair(); S.place(d5, 20, (0.0, 0.0), (380, 60))
    drawing_title(side, (560, 40), '5', 'STAIR FLIGHT (CORES 1-3)', 20)
    finish(S, F, side, no, title, 'AS SHOWN', None, ['DETAILS ARE DESIGN-INTENT FOR THE 3D MODEL AND THE CRIT; FIXINGS AND SIZES TO BE CONFIRMED BY THE FACADE AND C&S ENGINEERS.',
           'MATERIALS: ALUMINIUM (FINS, FASCIAS, ROOF), GRC (SOFFITS, FUNNEL), GLASS, GRANITE, STAINLESS STEEL. NO BRICK.'], y, x0)
    return S, [(d1, (0, 0)), (d2, (10, 0)), (d3, (0, 20)), (d4, (40, 20)), (d5, (50, 0))]

# --------------------------------------------------------------------------------------------- M-000 + cover
def cover_sheet(no='A-000', sheet_list=()):
    title = 'COVER · DRAWING LIST · GENERAL NOTES'
    S, F, x0, y = new_sheet(no, title, 'NTS @ A0')
    D = Drawing('cov', paper=True)
    D.text((40, 790), 'TITIK TEMU', 'X-TITL', size=34, ha='left', va='top', weight='bold')
    D.text((42, 752), 'SIMPUL RASA SEMENANJUNG', 'X-TITL', size=9, ha='left', va='top', color=ACCENT, weight='bold')
    D.text((42, 738), 'ESPLANADE LOCAL COMMERCIAL HUB · SITE C · TEMERLOH, PAHANG\nCOMPLETE BUILDING DRAWING SET (V3, AFTER CRIT 1): ARCHITECTURE, BOMBA, PLUMBING + DRAINAGE, ELECTRICAL + ACMV', 'X-TITL', size=3.0, ha='left', va='top')
    E = SE.elevation(180.0, 'S'); S.place(E, 200, (0, 8), (300, 520))
    D.text((60, 455), 'SOUTH ELEVATION 1:200 (FROM JALAN TOK MUDA AWANG NGAH)', 'X-TITL', size=2.6, ha='left', weight='bold')
    G = plans.plan_drawing('GF'); S.place(G, 250, tuple(C), (300, 225), clip=(40, 60, 560, 430))
    D.text((60, 60), 'GROUND FLOOR 1:250 (KEY)', 'X-TITL', size=2.6, ha='left', weight='bold')
    rows = [(n, t, s) for n, t, s in sheet_list]
    table(D, 600, 720, [('SHEET', 22, 'left'), ('TITLE', 140, 'left'), ('SCALE', 28, 'left')], rows, title='DRAWING LIST (A0, TRUE SCALE)', size=1.6, lh=2.9)
    notes = ['ALL DRAWINGS ARE PRINTED AT TRUE SCALE ON A0 (1189 x 841). DXF FILES (METRES, NAMED LAYERS) ARE ISSUED WITH THE SET FOR THE 3D MODEL.',
             'SITE COORDINATES IN METRES: X = EAST, Y = NORTH, ORIGIN = SOUTH-WEST SITE CORNER. CENTRE C = (70.3, 27.0). LEVELS ABOVE SITE DATUM ±0.000.',
             'GEOMETRY: ONE CENTRE C; RINGS A R9.5 (BRIDGE INNER), B R12.5, C R23.0 (GF WALL), D R26.5 (L1/L2 EDGE); ROOF EDGE R28.3; COURT R9.0; POOL R2.5.',
             'GATES: TIMUR 27.9°, SELATAN 182.7° (MAIN), TENGAH 242.8°, UTARA 317.7°. WAVE ROOF HIGH AT SELATAN + UTARA (+16.200), LOW AT TIMUR + TENGAH (+10.200).',
             'CODES: UBBL 1984, MS 1184 (ACCESS), MS 1525 (ENERGY), MS 1228 (SEWERAGE), MSMA 2ND ED. (DRAINAGE), SPAN GUIDELINES (WATER), MS IEC 62305 (LIGHTNING).',
             'SERVICES AND FIRE DRAWINGS ARE DESIGN-STAGE PROPOSALS FOR A STUDENT PROJECT; ENGINEERS AND BOMBA MUST CHECK THEM BEFORE ANY REAL USE.']
    notes_block(D, 600, 300, 'GENERAL NOTES', notes, width=80, size=2.6)
    finish(S, F, D, no, title, 'NTS', None, None, y, x0)
    return S, []
