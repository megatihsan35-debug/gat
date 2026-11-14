# -*- coding: utf-8 -*-
import json
from content import *
def build(IM):
    T = json.load(open('/home/claude/boards/img/truescale.json')); o = []
    W = 1587
    o.append(PAGEHEAD(32, 18, W - 64, 'SHEET 04 / 04', 'SECTION A–A + ELEVATIONS 1:200 · TECHNICAL STUDY', 'CRIT 1 · TASK 3A · MEGAT MUHAMMAD IHSAN · SECTION 8'))
    def drw(key, x, y, t, alt):
        w, h = T[key]['wpx'], T[key]['hpx']
        return (A(x, y - 18, w, f'<div style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK}">{t} · <span style="color:{TERRA}">SCALE 1:200</span></div>')
                + IMG(IM(key), x, y, w, h, alt, fit='fill')), w, h
    s, w, h = drw('secA', 40, 88, f'{SQ(1)} 14 · SECTION A–A · ALONG THE QIBLA AXIS: GELUNG KECIL – CORE – COURT – HALL', 'Section A-A at 1:200 along the qibla axis'); o.append(s)
    o.append(SCALEBAR(180, 95, 200, [0, 1, 2, 5, 10]))
    yS = 88 + h + 26
    s, w2, h2 = drw('elS', 40, yS, f'{SQ(2)} 15 · SOUTH ELEVATION · JALAN TOK MUDA AWANG NGAH', 'South elevation at 1:200'); o.append(s)
    yE = yS + h2 + 26
    s, w3, h3 = drw('elE', 40, yE, f'{SQ(3)} 16 · EAST ELEVATION · DATARAN TEMU / RIVER SIDE', 'East elevation at 1:200'); o.append(s)
    cx = 40 + w3 + 20; cw = W - 32 - cx
    isl = [('QS 49:13', '“…PEOPLES AND TRIBES THAT YOU MAY KNOW ONE ANOTHER.”', 'ONE TALAM COURT, FOUR GATES'),
           ('QS 106:1–4', '“…WHO HAS FED THEM… AND MADE THEM SAFE…”', 'A SAFE FOOD STOP ON THE E8 ROUTE'),
           ('BUKHARI 5986', 'KEEP GOOD RELATIONS WITH YOUR KITH AND KIN.', 'THE SIMPUL = SILATURRAHIM'),
           ('BUKHARI 5392', '“THE FOOD FOR TWO PERSONS IS SUFFICIENT FOR THREE…”', 'SHARED TABLES, NO WASTAGE'),
           ('QS 2:143', '“…A MEDIAN [JUST] COMMUNITY…” (UMMATAN WASATAN)', 'THE CENTRE + QIBLA DATUM')]
    it = ''.join(f'<div style="margin-bottom:6px;font-size:8.8px;line-height:1.3;color:{INK}"><b style="color:{TERRA}">{a}</b> <i>{b}</i> <b>→ {c}</b></div>' for a, b, c in isl)
    o.append(A(cx, yE - 18, cw, f'<div style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK};margin-bottom:5px">{SQ(2)} 17 · ISLAMIC VALUE ADDED</div>' + it
               + P('BRIEF VALUES: NO WASTAGE · BENEFICIAL · ACCESSIBLE · NO HARM · FIT FOR PURPOSE → PV + RAINWATER, LIFTS + RAMPS, FLOOD PLINTH.', 8.5, 1.3, MUTE)))
    yT = yE + h3 + 12
    o.append(A(40, yT, W - 80, f'<div style="display:flex;gap:24px;border-top:2px solid {INK};padding-top:5px">'
               + f'<div style="flex:0 0 150px;font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK}">{SQ(3)} 18 · TECHNICAL STUDY</div>'
               + f'<div style="flex:1;font-size:9px;line-height:1.35;color:{INK}"><b style="color:{TERRA}">STRUCTURE</b> · RADIAL RC FRAME: BIG RING 10 GRIDS @36° (9.0 M SPAN), SMALL RING 8 GRIDS @45° (8.1 M) · RC CORE WALLS FOR STABILITY, MOVEMENT JOINT BETWEEN RINGS · <b>MEDIUM SPAN: 12.5 M STEEL RIBBON TRUSSES OVER THE HALL</b> · 3.4 M L1 OVERSAIL ON RC CANTILEVERS · BORED PILES (CONFIRM BY SI) · IBS PRECAST COLUMNS + HOLLOW-CORE SLABS.</div>'
               + f'<div style="flex:1;font-size:9px;line-height:1.35;color:{INK}"><b style="color:{TERRA}">SERVICES</b> · WATER: SUCTION TANK + PUMPS → ROOF TANKS ON GELUNG KECIL → RISERS · SEWER: GREASE TRAP → MANHOLES → MUNICIPAL SEWER · RAINWATER HARVESTING + BIOSWALE · FIRE: HOSE REELS AT BOTH CORES, ROOF TANK, BREECHING INLET · TNB → MDB + GENSET; PV ROOFS · ACMV: SPLIT / VRF FOR ADMIN, GALLERY, HALL; COURT NATURALLY VENTILATED.</div></div>'))
    return ''.join(o)
