"""Builds the drawing set: A0 PDF sheets (true scale) + one DXF per drawing (metres, named layers).
python3 build.py [sheet-no ...]   -> out/TITIK-TEMU_V3_SET.pdf, out/<sheet>.pdf, out/dxf/<drawing>.dxf"""
import os, sys, math
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import Polygon, Point, LineString
import plan3 as M
from plan3 import C, P, d, SC, ROOMS, FFL
from cad import Drawing, to_dxf, INK
import sheets as SH
from sheets import new_sheet, notes_block, legend_block, north, scale_bar, drawing_title, key_plan
import plans

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out'); os.makedirs(os.path.join(OUT, 'dxf'), exist_ok=True)
CEN = (515.0, 425.0)                       # plan centre on the sheet
CLIP = SH.DRAW_BOX
SIDE_X = 850.0                             # side column of the drawing area (key plan, legend, notes)

FL_NAME = {'GF': 'GROUND FLOOR PLAN', 'L1': 'FIRST FLOOR PLAN', 'L2': 'SECOND FLOOR PLAN'}
ARCH_LEGEND = [('fill', dict(fill=INK), 'WALL CUT (RC / BLOCKWORK, PLASTERED)'), ('line', dict(lw=0.3), 'GLAZING (FULL HEIGHT)'),
               ('circle', dict(fill=INK, r=1.6), 'COLUMN Ø350 RC'), ('line', dict(lw=0.15, color='#7A8590', ls='-.'), 'STRUCTURAL GRID (RADIAL / RING)'),
               ('line', dict(lw=0.25, ls='--'), 'LINE OVER / SLAB EDGE'), ('text', dict(t='D2'), 'DOOR TYPE (SEE A-600)'),
               ('text', dict(t='FD60', size=1.5), 'FIRE DOOR, 60 MIN, SELF-CLOSING'), ('fill', dict(fill='#F6F7F8', edge='#9AA3AD'), 'RING BRIDGE (OPEN WALKWAY)')]

def area_table(D, x, y, fl):
    D.text((x, y), f'ROOM AREAS · {FL_NAME[fl].replace(" PLAN", "")}', 'X-TITL', size=2.4, ha='left', va='top', weight='bold'); y -= 5
    D.text((x, y), 'NO.', 'X-TITL', size=1.6, ha='left', va='top', color='#6B7480'); D.text((x + 13, y), 'ROOM', 'X-TITL', size=1.6, ha='left', va='top', color='#6B7480')
    D.text((x + 150, y), 'NET M²', 'X-TITL', size=1.6, ha='right', va='top', color='#6B7480'); D.text((x + 166, y), 'BRIEF', 'X-TITL', size=1.6, ha='right', va='top', color='#6B7480'); y -= 3.6
    tot = 0
    for r in ROOMS:
        if r['fl'] != fl or r['kind'] in ('stair', 'lift'): continue
        a = r['poly'].buffer(-0.075, join_style=2).area if r['kind'] != 'open' else r['poly'].area; tot += a
        br = r['brief']
        D.text((x, y), r['key'], 'X-TITL', size=1.75, ha='left', va='top', font='DejaVu Sans Mono')
        D.text((x + 13, y), r['name'][:52], 'X-TITL', size=1.75, ha='left', va='top')
        D.text((x + 150, y), f'{a:.1f}', 'X-TITL', size=1.75, ha='right', va='top', font='DejaVu Sans Mono')
        D.text((x + 166, y), f"{br[1]}" if br and br[1] else '–', 'X-TITL', size=1.75, ha='right', va='top', font='DejaVu Sans Mono')
        y -= 2.9
    D.line([(x, y + 0.6), (x + 166, y + 0.6)], 'X-TITL', lw=0.15); y -= 0.8
    op = sum(o['poly'].area for o in M.OPEN if o['fl'] == fl)
    D.text((x + 13, y), 'ENCLOSED ROOMS (NET)', 'X-TITL', size=1.8, ha='left', va='top', weight='bold'); D.text((x + 150, y), f'{tot:.0f}', 'X-TITL', size=1.8, ha='right', va='top', weight='bold'); y -= 3.2
    D.text((x + 13, y), 'OPEN ' + ('ARCADE / COURT EDGE' if fl == 'GF' else 'DECKS (ROOFED)'), 'X-TITL', size=1.8, ha='left', va='top'); D.text((x + 150, y), f'{op:.0f}', 'X-TITL', size=1.8, ha='right', va='top')
    return y - 6

def plan_sheet(fl, no, mode='arch', title=None, overlay=None, legend=None, notes=None, extra=None, scale=100):
    title = title or FL_NAME[fl]
    S, F, x0, y = new_sheet(no, title, f'1:{scale} @ A0')
    D = plans.plan_drawing(fl, mode)
    if overlay: overlay(D, fl)
    S.place(D, scale, tuple(C), CEN, clip=CLIP)
    side = Drawing('side', paper=True)
    north(side, (SIDE_X + 150, 790)); key_plan(side, (SIDE_X, 752), 70, hilite=M.PLATE[fl] if fl != 'GF' else SC.disc(M.R_GF), label='KEY PLAN · SITE')
    scale_bar(side, (SIDE_X, 728), scale)
    yy = legend_block(F, x0, y - 2, 'LEGEND', legend or ARCH_LEGEND)
    if notes: yy = notes_block(F, x0, yy - 2, 'NOTES', notes)
    if extra: extra(side, fl)
    else: area_table(side, SIDE_X, 700, fl)
    drawing_title(side, (40, 40), no.split('-')[-1][-1], title, scale, f'FFL +{FFL[fl]:.3f}')
    S.place(side, 1, (0, 0), (0, 0)); S.place(F, 1, (0, 0), (0, 0))
    SH.SHEETS.append((no, title, f'1:{scale}'))
    return S, D

FIRE_NOTES = ['TRAVEL DISTANCES ARE MEASURED ALONG THE ROUTE (RADIAL LEG + RING BRIDGE + LEG TO THE STAIR DOOR) AND ARE CHECKED AGAINST UBBL 7TH SCHEDULE: 45 M WHERE TWO DIRECTIONS EXIST, 15 M DEAD END.',
              'SEE F-000 FOR OCCUPANT LOAD, EXIT CAPACITY, TENTH SCHEDULE AND HOSE REEL WATER STORAGE.']
ARCH_NOTES = ['RADII ARE MEASURED FROM CENTRE C (MAST AXIS); BEARINGS CLOCKWISE FROM TRUE NORTH. GRID 1-27 RADIAL, A-D RINGS.',
              'GROUND FLOOR FFL +0.900 ON A RAISED PLINTH; FORECOURTS RAMP 1:20 MAX FROM ±0.000 AT THE GATES.',
              'STAIRS: RISER ≤ 175, GOING 280, FLIGHT 1650 CLEAR (3 UNITS OF 550), HANDRAILS BOTH SIDES 900-1000.',
              'TOILETS TO MS 1184: PwD CUBICLE 2200 x 1850 CLEAR, 900 DOOR OPENING OUT, 1500 TURNING CIRCLE OUTSIDE.',
              'LIFTS: 13-PERSON, CAR 1600 x 1400, DOOR 900 CLEAR, MACHINE-ROOM-LESS, ONE IN EACH OF CORES 1 + 2.',
              'ALL ROOM AREAS ARE NET (INSIDE WALL FACES). SEE A-600 FOR THE BRIEF CHECK AND DOOR SCHEDULE.']

import services as SV, sections as SE, siteplan as ST, sheets2 as S2
PLUMB_NOTES = ['GF FITTINGS ARE FED BY GRAVITY FROM THE ROOF TANK ON CORE 2; L1 + L2 FITTINGS BY THE BOOSTER SET IN THE TANK ROOM (SEE P-000).',
               'SOIL STACKS ARE BOXED IN 300 x 300 DUCTS OR COLUMN CASINGS WITH ACCESS DOORS AT EVERY FLOOR. FALLS: Ø100 1:60, Ø150 1:100.']
MNE_NOTES = ['SUPPLY: TNB LV INTAKE AT THE UTILITY BLOCK → MSB (G08) → SUB-SWITCHBOARDS PER FLOOR → TENANT DBs WITH kWh SUB-METERS. ESTIMATED MAX DEMAND ≈ 250 kVA (PROVISIONAL).',
             'STANDBY GENSET (≈ 100 kVA) SERVES HOSE REEL PUMPS, LIFTS, EMERGENCY LIGHTS, FIRE ALARM, SECURITY + 1/3 OF THE LIGHTING.',
             'ACMV: VRF HEAT-RECOVERY SYSTEM, OUTDOOR UNITS ON THE UTILITY BLOCK ROOF; FRESH AIR BY ENERGY-RECOVERY UNITS TO MS 1525. OPEN COURT AND DECKS: NATURAL VENTILATION + FANS.',
             'LIGHTNING: AIR TERMINAL ON THE MAST, ROOF-EDGE CONDUCTOR, 8 DOWN CONDUCTORS IN RING-C COLUMNS BESIDE THE GATES, RING EARTH ELECTRODE (MS IEC 62305).']
def jobs_list():
    J = []
    J.append(('A-001', lambda: S2.site_sheet('A-001')))
    for no, fl in (('A-100', 'GF'), ('A-101', 'L1'), ('A-102', 'L2')):
        J.append((no, (lambda fl=fl, no=no: plan_sheet(fl, no, notes=ARCH_NOTES))))
    J.append(('A-103', lambda: S2.roof_sheet('A-103')))
    J.append(('A-200', lambda: S2.sections_sheet('A-200')))
    J.append(('A-300', lambda: S2.elevations_sheet('A-300', [(180.0, 'SOUTH'), (90.0, 'EAST')])))
    J.append(('A-301', lambda: S2.elevations_sheet('A-301', [(0.0, 'NORTH'), (270.0, 'WEST')])))
    J.append(('A-500', lambda: S2.details_sheet('A-500')))
    J.append(('A-600', lambda: S2.schedules_sheet('A-600')))
    J.append(('F-000', lambda: S2.fire_strategy_sheet('F-000')))
    for i, fl in enumerate(('GF', 'L1', 'L2')):
        J.append((f'F-10{i}', (lambda fl=fl, i=i: plan_sheet(fl, f'F-10{i}', 'base', FL_NAME[fl].replace(' PLAN', '') + ' · FIRE PROTECTION + ESCAPE', SV.fire_overlay, SV.FIRE_LEGEND, FIRE_NOTES))))
    J.append(('P-000', lambda: S2.plumbing_calc_sheet('P-000')))
    for i, fl in enumerate(('GF', 'L1', 'L2')):
        J.append((f'P-10{i}', (lambda fl=fl, i=i: plan_sheet(fl, f'P-10{i}', 'base', FL_NAME[fl].replace(' PLAN', '') + ' · PLUMBING + DRAINAGE', SV.plumbing_overlay, SV.PLUMB_LEGEND, PLUMB_NOTES))))
    for i, fl in enumerate(('GF', 'L1', 'L2')):
        J.append((f'M-10{i}', (lambda fl=fl, i=i: plan_sheet(fl, f'M-10{i}', 'base', FL_NAME[fl].replace(' PLAN', '') + ' · ELECTRICAL + ACMV', SV.mne_overlay, SV.MNE_LEGEND, MNE_NOTES))))
    return J

def save(no, S, dl):
    S.fig.savefig(os.path.join(OUT, f'{no}.pdf'))
    S.png(os.path.join(OUT, f'{no}.png'), dpi=60)
    if dl:
        dl = [(D, off) if isinstance(off, tuple) else (D, (0, 0)) for D, off in dl]
        to_dxf(dl, os.path.join(OUT, 'dxf', f'{no}.dxf'))
    S.close(); print('built', no, flush=True)

def build(only=None):
    order = ['A-000']
    for no, fn in jobs_list():
        order.append(no)
        if only and no not in only: continue
        r = fn()
        S, dl = r if isinstance(r[1], list) else (r[0], [(r[1], (0, 0))])
        save(no, S, dl)
    if not only or 'A-000' in only:
        lst = [('A-000', 'COVER · DRAWING LIST · GENERAL NOTES', 'NTS')] + [x for x in SH.SHEETS if x[0] != 'A-000']
        if only: lst = [('A-000', 'COVER · DRAWING LIST · GENERAL NOTES', 'NTS')] + [(n, '', '') for n in order[1:]]
        S, dl = S2.cover_sheet('A-000', lst); save('A-000', S, dl)
    from pypdf import PdfWriter
    w = PdfWriter()
    for no in order:
        f = os.path.join(OUT, f'{no}.pdf')
        if os.path.exists(f): w.append(f)
    w.write(os.path.join(OUT, 'TITIK-TEMU_V3_DRAWING-SET_A0.pdf')); print('merged', len(order))

if __name__ == '__main__':
    build(sys.argv[1:] or None)
