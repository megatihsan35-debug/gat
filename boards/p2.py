# -*- coding: utf-8 -*-
import json
from content import *
def build(IM):
    T = json.load(open('/home/claude/boards/img/truescale.json')); o = []
    o.append(PAGEHEAD(32, 18, 1059, 'SHEET 02 / 04', 'SITE PLAN 1:500 + GROUND FLOOR PLAN 1:200', 'CRIT 1 · TASK 3A · MEGAT MUHAMMAD IHSAN · SECTION 8'))
    sw, sh = T['site']['wpx'], T['site']['hpx']; sx, sy = 32, 92
    o.append(A(sx, 66, sw, f'<div style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK}">{SQ(2)} 08 · SITE PLANNING WITH CONTEXT · <span style="color:{TERRA}">SCALE 1:500</span> · LOT 10150 · 5,370 M²</div>'))
    o.append(IMG(IM('site'), sx, sy, sw, sh, 'Site plan at 1:500 with context: the two rings, Dataran Temu plaza, Taman Ulam, service yard and ribbons to the road', fit='fill'))
    o.append(SCALEBAR(sx + 10, sy + 10, 500, [0, 10, 20, 50]))
    o.append(NORTH(sx + sw - 40, sy + 10))
    cx = sx + sw + 12; cw = 1091 - cx
    resp = [('HOT WEST SUN', 'GELUNG KECIL + SOLID LAMELLA DRUM ON THE WEST'), ('SUNGAI PAHANG (E)', 'HALL, GERBANG TIMUR + PLAZA FACE THE RIVER'),
            ('MONSOONS + RIVER BREEZE', 'OPEN COURT + OCULUS, POROUS CLAY SKIN'), ('ISTANA (NW), FUTSAL (N)', 'SERVICE YARD + QUIET TAMAN ULAM'),
            ('ROAD + STADIUM (S)', 'GERBANG SELATAN, SERAMBI TENGAH, RIBBONS'), ('SLOPE + DEC 2014 FLOODS', 'PLINTH +0.9 M; MDB + GENSET ON THE PLINTH')]
    rt = ''.join(P(f'<b>{a}</b><br>→ {b}', 9.5, 1.35, INK, 'margin-bottom:9px') for a, b in resp)
    o.append(A(cx, sy, cw, f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:11px;color:{TERRA};margin-bottom:8px">SITE → RESPONSE</div>' + rt
               + f'<div style="border-top:1px solid {RULE};margin-top:4px;padding-top:5px">'
               + P('PUBLIC FRONT SOUTH + EAST; SERVICE BACK WEST ON ITS OWN DRIVE. SETBACKS 6 M ROAD / 3 M OTHERS. COVERAGE ≈30 % · PLOT RATIO ≈0.29. PARKING: 5 STAFF, 1 OKU, 10 MOTORCYCLE, 10 BICYCLE.', 9.5, 1.35, INK) + '</div>'))
    gw, gh = T['gf']['wpx'], T['gf']['hpx']; gx = (1123 - gw) / 2; gy = 1587 - 26 - gh
    o.append(A(gx, gy - 22, gw, f'<div style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK}">{SQ(2)} 09 · GROUND FLOOR PLAN · FFL +0.900 · <span style="color:{TERRA}">SCALE 1:200</span> · ROOM AREAS IN M²</div>'))
    o.append(IMG(IM('gf'), gx, gy, gw, gh, 'Ground floor plan at 1:200: shop lots and café around the Talam court, lobby and core at the knot, services in Gelung Kecil', fit='fill'))
    o.append(SCALEBAR(gx + gw - 236, gy + gh - 48, 200, [0, 1, 2, 5, 10]))
    o.append(NORTH(gx + gw - 40, gy + 10))
    zones = [('#F6D9A0', 'PUBLIC'), ('#CFE3B8', 'SEMI-PUBLIC'), ('#BFD8EC', 'PRIVATE / ADMIN'), ('#D9D0EC', 'SERVICE'), ('#ECECEC', 'CIRCULATION')]
    zl = ''.join(f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:10px"><span style="display:inline-block;width:12px;height:9px;background:{c};border:1px solid #8A8F93"></span>{t}</span>' for c, t in zones)
    o.append(A(gx + 8, gy + gh - 22, 620, f'<div style="display:inline-block;background:rgba(255,255,255,0.9);border:1px solid {RULE};padding:3px 6px;font-size:7.5px;font-weight:700;color:{INK}">{zl}</div>'))
    return ''.join(o)
