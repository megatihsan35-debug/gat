# -*- coding: utf-8 -*-
import json
from content import *
from s2 import LBL, SUB
W, H = 1587, 1123
def build(IM):
    T = json.load(open('/home/claude/boards/img/truescale.json')); o = []
    o.append(PAGEHEAD(32, 18, W - 64, 'SHEET 05 / 05', 'SECTIONS A–A + B–B · SOUTH ELEVATION 1:200', SUB))
    x0 = 40
    def drw(key, y, t, alt):
        w, h = T[key]['wpx'], T[key]['hpx']
        o.append(LBL(x0, y - 20, w, f'{t} · <span style="color:{TERRA}">SCALE 1:200</span>'))
        o.append(IMG(IM(key), x0, y, w, h, alt, fit='fill'))
        return w, h
    yA = 92
    w, h = drw('secA', yA, f'{SQ(1)} 16 · SECTION A–A · ALONG THE QIBLA AXIS: GELUNG KECIL – CORE – COURT – HALL', 'Section A-A at 1:200 along the qibla axis')
    o.append(SCALEBAR(180, yA + 7, 200, [0, 1, 2, 5, 10]))
    yB = yA + h + 34
    wb, hb = drw('secB', yB, f'{SQ(1)} 17 · SECTION B–B · NORTH–SOUTH THROUGH THE TALAM COURT', 'Section B-B at 1:200 through the Talam court between shop lots A1-4 and A2-2')
    bx = x0 + wb + 24; bw = W - 32 - bx
    lv = [('+13.500', 'SIMPUL CROWN'), ('+12.900', 'RIBBON ROOF (OUTER)'), ('+11.200', 'RIBBON ROOF (INNER)'), ('+9.900', 'GELUNG KECIL ROOF'), ('+6.000', 'PARAPET'),
          ('+5.400', 'L1 / ROOF TERRACE'), ('+0.900', 'GF (FLOOD PLINTH)'), ('±0.000', 'EXISTING GROUND')]
    lt = ''.join(f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:4px 10px 4px 0;font-weight:700;white-space:nowrap">{a}</td><td style="padding:4px 0">{b}</td></tr>' for a, b in lv)
    o.append(SH(bx, yB - 22, bw, '', 'LEVELS', 'M', on=1))
    o.append(A(bx, yB + 4, bw, f'<table style="border-collapse:collapse;width:100%;font-size:9.5px;line-height:1.25;color:{INK}">{lt}</table>'
               + P('OCULUS Ø9 M OPEN TO THE SKY OVER THE TALAM COURT · 12.5 M CLEAR SPAN OVER THE HALL.', 9, 1.35, MUTE, 'margin-top:7px')))
    yS = yB + hb + 34
    drw('elS', yS, f'{SQ(2)} 18 · SOUTH ELEVATION · JALAN TOK MUDA AWANG NGAH', 'South elevation at 1:200 facing Jalan Tok Muda Awang Ngah')
    return ''.join(o)
