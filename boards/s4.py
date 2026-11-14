# -*- coding: utf-8 -*-
import json
from content import *
from s2 import LBL, SUB
W, H = 1587, 1123
def build(IM):
    T = json.load(open('/home/claude/boards/img/truescale.json')); o = []
    o.append(PAGEHEAD(32, 18, W - 64, 'SHEET 04 / 05', 'FIRST FLOOR PLAN 1:200 · ISLAMIC VALUE ADDED · TECHNICAL STUDY', SUB))
    lw, lh = T['l1']['wpx'], T['l1']['hpx']; lx, ly = 32, 92
    o.append(LBL(lx, 68, lw, f'{SQ(2)} 13 · FIRST FLOOR PLAN · FFL +5.400 · <span style="color:{TERRA}">SCALE 1:200</span> · ROOM AREAS IN M²'))
    o.append(IMG(IM('l1'), lx, ly, lw, lh, 'First floor plan at 1:200: gallery and multipurpose hall to the east, prayer halls and admin in Gelung Kecil, roof walk around the court', fit='fill'))
    o.append(SCALEBAR(lx + 12, ly + lh - 48, 200, [0, 1, 2, 5, 10]))
    o.append(NORTH(lx + lw - 46, ly + 10))
    cx = lx + lw + 24; cw = W - 32 - cx
    ks = [('GELUNG KECIL · QUIET RING', 'MALE PRAYER 36 · FEMALE PRAYER 36 · FAMILY WAITING 36 · SHOE FOYER 29 · OFFICE 32 · RECEPTION 19 · MANAGER 18 · MEETING 20 · PANTRY 14'),
          ('THE KNOT', 'LIFT LOBBY 25 + STAIR CORE'),
          ('GELUNG RASA ROOF', 'LALUAN SIMPUL ROOF TERRACE WALK +5.400 · TAMAN ULAM TERRACE (HERBS OF 11 STATES) · OCULUS Ø9 M OPEN TO THE SKY'),
          ('EAST WING · RIVER SIDE', 'GALLERY 54 + STORE 28 + STAFF 14 · MULTIPURPOSE HALL 92, 12.5 M CLEAR SPAN ON STEEL RIBBON TRUSSES · MALE WC 23 · FEMALE WC 23')]
    kt = ''.join(f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:7px 0"><b style="color:{TERRA}">{a}</b><br>{b}</td></tr>' for a, b in ks)
    o.append(SH(cx, 66, cw, '', 'FIRST FLOOR · KEY SPACES', 'M²', on=1))
    o.append(A(cx, 92, cw, f'<table style="border-collapse:collapse;width:100%;font-size:10.5px;line-height:1.4;color:{INK}">{kt}</table>'))
    isl = [('QS 49:13', '“…PEOPLES AND TRIBES THAT YOU MAY KNOW ONE ANOTHER.”', 'ONE TALAM COURT, FOUR GATES'),
           ('QS 106:1–4', '“…WHO HAS FED THEM… AND MADE THEM SAFE…”', 'A SAFE FOOD STOP ON THE E8 ROUTE'),
           ('BUKHARI 5986', 'KEEP GOOD RELATIONS WITH YOUR KITH AND KIN.', 'THE SIMPUL = SILATURRAHIM'),
           ('BUKHARI 5392', '“THE FOOD FOR TWO PERSONS IS SUFFICIENT FOR THREE…”', 'SHARED TABLES, NO WASTAGE'),
           ('QS 2:143', '“…A MEDIAN [JUST] COMMUNITY…” (UMMATAN WASATAN)', 'THE CENTRE + QIBLA DATUM')]
    it = ''.join(f'<div style="margin-bottom:13px;font-size:10.5px;line-height:1.42;color:{INK}"><b style="color:{TERRA}">{a}</b> <i>{b}</i><br><b>→ {c}</b></div>' for a, b, c in isl)
    o.append(SH(cx, 320, cw, '14', 'ISLAMIC VALUE ADDED', on=2))
    o.append(A(cx, 348, cw, it + P('BRIEF VALUES: NO WASTAGE · BENEFICIAL · ACCESSIBLE · NO HARM · FIT FOR PURPOSE → PV + RAINWATER, LIFTS + RAMPS, FLOOD PLINTH.', 10, 1.4, MUTE, 'margin-top:4px')))
    yb = ly + lh + 22
    o.append(SH(lx, yb, lw, '15', 'TECHNICAL STUDY', 'STRUCTURE + SERVICES', on=3))
    st = ('RADIAL RC FRAME: BIG RING 10 GRIDS @36° (9.0 M SPAN), SMALL RING 8 GRIDS @45° (8.1 M) · RC CORE WALLS FOR STABILITY, MOVEMENT JOINT BETWEEN RINGS · '
          '<b>MEDIUM SPAN: 12.5 M STEEL RIBBON TRUSSES OVER THE HALL</b> · 3.4 M L1 OVERSAIL ON RC CANTILEVERS · BORED PILES (CONFIRM BY SI) · IBS PRECAST COLUMNS + HOLLOW-CORE SLABS.')
    sv = ('WATER: SUCTION TANK + PUMPS → ROOF TANKS ON GELUNG KECIL → RISERS · SEWER: GREASE TRAP → MANHOLES → MUNICIPAL SEWER · RAINWATER HARVESTING + BIOSWALE · '
          'FIRE: HOSE REELS AT BOTH CORES, ROOF TANK, BREECHING INLET · TNB → MDB + GENSET; PV ROOFS · ACMV: SPLIT / VRF FOR ADMIN, GALLERY, HALL; COURT NATURALLY VENTILATED.')
    col = lambda h, b: f'<div style="flex:1;background:#FFFFFF;border:1px solid {RULE};padding:10px 12px"><div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:11px;color:{TERRA}">{h}</div><div style="font-size:10.2px;line-height:1.45;color:{INK};margin-top:4px">{b}</div></div>'
    o.append(A(lx, yb + 26, lw, f'<div style="display:flex;gap:10px">{col("STRUCTURE", st)}{col("SERVICES", sv)}</div>'))
    return ''.join(o)
