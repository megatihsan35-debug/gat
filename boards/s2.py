# -*- coding: utf-8 -*-
import json
from content import *
W, H = 1587, 1123
SUB = 'CRIT 1 · TASK 3A · MEGAT MUHAMMAD IHSAN · SECTION 8'
def LBL(x, y, w, t):
    return A(x, y, w, f'<div style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK};white-space:nowrap">{t}</div>')
def build(IM):
    T = json.load(open('/home/claude/boards/img/truescale.json')); o = []
    o.append(PAGEHEAD(32, 18, W - 64, 'SHEET 02 / 05', 'SITE PLAN 1:500 + EAST ELEVATION 1:200', SUB))
    sw, sh = T['site']['wpx'], T['site']['hpx']; sx, sy = 32, 92
    o.append(LBL(sx, 68, sw, f'{SQ(2)} 08 · SITE PLANNING WITH CONTEXT · <span style="color:{TERRA}">SCALE 1:500</span> · LOT 10150 · 5,370 M²'))
    o.append(IMG(IM('site'), sx, sy, sw, sh, 'Site plan at 1:500 with context: the two rings, Dataran Temu plaza, Taman Ulam, service yard and ribbons', fit='fill'))
    o.append(SCALEBAR(sx + 10, sy + 10, 500, [0, 10, 20, 50]))
    o.append(NORTH(sx + sw - 40, sy + 10))
    cx = sx + sw + 24; cw = W - 32 - cx
    o.append(SH(cx, 66, cw, '', 'SITE → RESPONSE', 'FROM 04 SITE SYNTHESIS', on=1))
    resp = [('HOT WEST SUN', 'GELUNG KECIL + SOLID LAMELLA DRUM ON THE WEST'), ('SUNGAI PAHANG (E)', 'HALL, GERBANG TIMUR + PLAZA FACE THE RIVER'),
            ('MONSOONS + RIVER BREEZE', 'OPEN COURT + OCULUS, POROUS CLAY SKIN'), ('ISTANA (NW), FUTSAL (N)', 'SERVICE YARD + QUIET TAMAN ULAM'),
            ('ROAD + STADIUM (S)', 'GERBANG SELATAN, SERAMBI TENGAH, RIBBONS'), ('SLOPE + DEC 2014 FLOODS', 'PLINTH +0.9 M; MDB + GENSET ON THE PLINTH')]
    cards = ''.join(f'<div style="background:#FFFFFF;border:1px solid {RULE};padding:11px 12px"><div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:11.5px;color:{TERRA}">{a}</div><div style="font-size:11px;line-height:1.4;color:{INK};margin-top:4px">→ {b}</div></div>' for a, b in resp)
    o.append(A(cx, sy + 2, cw, f'<div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:8px">{cards}</div>'))
    data = [('PUBLIC FRONT', 'SOUTH + EAST, FACING THE ROAD AND THE RIVER'), ('SERVICE', 'BACK OF HOUSE ON THE WEST, ON ITS OWN DRIVE'), ('SETBACKS', '6 M TO THE ROAD · 3 M TO OTHER SIDES'),
            ('COVERAGE · PLOT RATIO', '≈30 % · ≈0.29'), ('PARKING', '5 STAFF · 1 OKU · 10 MOTORCYCLE · 10 BICYCLE + DROP-OFF'), ('RIBBONS', 'RIBEN UTARA, TENGAH, SELATAN + TIMUR AS SHADE CANOPIES')]
    dt = ''.join(f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:9px 10px 9px 0;font-weight:700;white-space:nowrap;vertical-align:top">{a}</td><td style="padding:9px 0">{b}</td></tr>' for a, b in data)
    o.append(SH(cx, 330, cw, '', 'SITE DATA', 'LOT 10150 · 5,370 M²', on=2))
    o.append(A(cx, 358, cw, f'<table style="border-collapse:collapse;width:100%;font-size:11px;line-height:1.35;color:{INK}">{dt}</table>'))
    ew, eh = T['elE']['wpx'], T['elE']['hpx']; ey = H - 30 - eh
    o.append(LBL(32, ey - 22, ew, f'{SQ(3)} 09 · EAST ELEVATION · DATARAN TEMU / RIVER SIDE · <span style="color:{TERRA}">SCALE 1:200</span>'))
    o.append(IMG(IM('elE'), 32, ey, ew, eh, 'East elevation at 1:200 facing Dataran Temu and the river', fit='fill'))
    bx = 32 + ew + 24; bw = W - 32 - bx
    o.append(A(bx, ey, bw, P('THE RIVER FACE: CLAY LAMELLA SKIN, A RIBBON SWEEPING ACROSS AS A CANOPY AND THE CROWN RISING TO +13.5 M. THE PLAZA SIDE FOR EVENINGS, FESTIVALS AND THE PEKAN SEHARI.', 9.5, 1.38, INK) + P('LEVELS: GF +0.900 · L1 +5.400 · PARAPET +6.000 · RIBBON ROOF +12.900 · CROWN +13.500', 8.5, 1.35, MUTE, 'margin-top:8px')))
    o.append(SCALEBAR(bx, ey + eh - 44, 200, [0, 1, 2, 5, 10]))
    return ''.join(o)
