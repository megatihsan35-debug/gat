# -*- coding: utf-8 -*-
import json
from content import *
from s2 import LBL, SUB
W, H = 1587, 1123
def build(IM):
    T = json.load(open('/home/claude/boards/img/truescale.json')); o = []
    o.append(PAGEHEAD(32, 18, W - 64, 'SHEET 03 / 05', 'GROUND FLOOR PLAN 1:200 · SCHEDULE OF ACCOMMODATION · BRIEF', SUB))
    gw, gh = T['gf']['wpx'], T['gf']['hpx']; gx, gy = 32, 92
    o.append(LBL(gx, 68, gw, f'{SQ(2)} 10 · GROUND FLOOR PLAN · FFL +0.900 · <span style="color:{TERRA}">SCALE 1:200</span> · ROOM AREAS IN M²'))
    o.append(IMG(IM('gf'), gx, gy, gw, gh, 'Ground floor plan at 1:200: shop lots and café around the Talam court, lobby and core at the knot, services in Gelung Kecil', fit='fill'))
    o.append(SCALEBAR(gx + gw - 236, gy + gh - 48, 200, [0, 1, 2, 5, 10]))
    o.append(NORTH(gx + gw - 40, gy + 10))
    zones = [('#F6D9A0', 'PUBLIC'), ('#CFE3B8', 'SEMI-PUBLIC'), ('#BFD8EC', 'PRIVATE / ADMIN'), ('#D9D0EC', 'SERVICE'), ('#ECECEC', 'CIRCULATION')]
    zl = ''.join(f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:10px"><span style="display:inline-block;width:12px;height:9px;background:{c};border:1px solid #8A8F93"></span>{t}</span>' for c, t in zones)
    o.append(A(gx + 8, gy + gh - 22, 620, f'<div style="display:inline-block;background:rgba(255,255,255,0.9);border:1px solid {RULE};padding:3px 6px;font-size:7.5px;font-weight:700;color:{INK}">{zl}</div>'))
    cx = gx + gw + 24; cw = W - 32 - cx
    o.append(SH(cx, 66, cw, '11', 'SCHEDULE OF ACCOMMODATION', 'M²', on=3))
    soa = [('A', 'RETAIL: 8 SHOP LOTS + CAFÉ', '306', '403.9', '324.5'), ('B', 'GALLERY + MPH (COURT DINING OPEN)', '317', '418.4', '224.3'),
           ('C', 'MANAGEMENT / ADMIN + FIRST AID', '118', '142.8', '137.5'), ('D', 'LOBBY, MUSOLLA, TOILETS', '295', '340.7', '436.4'),
           ('E', 'SERVICES / UTILITIES', '182', '219.8', '191.7'), ('', 'CORES, STAIRS, LIFTS, CORRIDORS', '–', 'IN %', '234.3')]
    pd = 'padding:6px 4px'
    th = ''.join(f'<th style="text-align:{al};font-weight:700;{pd};border-bottom:1.5px solid {INK};white-space:nowrap">{h}</th>' for h, al in
                 [('', 'left'), ('CATEGORY', 'left'), ('NET', 'right'), ('GROSS', 'right'), ('DRAWN', 'right')])
    tr = ''.join(f'<tr style="border-bottom:1px solid {RULE}"><td style="{pd};font-weight:700;color:{TERRA}">{a}</td><td style="{pd}">{b}</td><td style="{pd};text-align:right">{c}</td><td style="{pd};text-align:right">{d}</td><td style="{pd};text-align:right;font-weight:700">{e}</td></tr>' for a, b, c, d, e in soa)
    tr += f'<tr style="border-top:1.5px solid {INK};background:#EFE8DA"><td></td><td style="{pd};font-weight:700">TOTAL ENCLOSED</td><td style="{pd};text-align:right;font-weight:700">1,218</td><td style="{pd};text-align:right;font-weight:700">1,525.6</td><td style="{pd};text-align:right;font-weight:700;color:{TERRA};white-space:nowrap">1,548.8</td></tr>'
    o.append(A(cx, 94, cw, f'<table style="border-collapse:collapse;width:100%;font-size:10.5px;line-height:1.3;color:{INK}"><tr>{th}</tr>{tr}</table>'
               + P('DRAWN = +1.5 % OVER SOA GROSS. EVERY ROOM MEETS OR BEATS ITS SOA NET SIZE. GF ≈866 M² + L1 ≈683 M²; OPEN VERANDAH + BALCONY ≈163 M² NOT COUNTED. CIRCULATION ≈28 % (BRIEF 25–30 %). PLOT RATIO ≈0.29 · COVERAGE ≈30 % · TOP OF CROWN +13.5 M.', 9.3, 1.4, MUTE, 'margin-top:6px')))
    ks = [('GERBANG SELATAN', 'INFO 14 + FIRST AID 18 AT THE GATE'), ('TALAM COURT', 'OPEN DINING FOR 100 · PLAY 30 · HAND-WASH · COVERED VERANDAH WALK'),
          ('8 SHOP LOTS × 32 M²', 'A1-1 TO A1-4 (SOUTH ARC) · A2-1 TO A2-4 (NORTH ARC)'), ('GERBANG TIMUR', 'CAFÉ 32 + SERVERY 14 + KITCHEN 18'),
          ('LOBBY 87 AT THE KNOT', 'LIFT + STAIR CORE · MALE WC 23 · FEMALE WC 23 · NURSING 11 · NAPPY 7'),
          ('GELUNG KECIL = SERVICE', 'LOADING 36 · REFUSE WET 18 + DRY 18 · DRY 16 · FREEZER 16 · MDB 23 · GENSET 18 · HK 14 · CLEANER 14 · STAFF WC 36 + 36 · AROUND A LIGHT WELL'),
          ('SERAMBI TENGAH', 'POP-UP BAYS WHERE THE TENGAH RIBBON ARRIVES')]
    kt = ''.join(f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:7px 8px 7px 0;font-weight:700;white-space:nowrap;vertical-align:top;color:{TERRA}">{a}</td><td style="padding:7px 0">{b}</td></tr>' for a, b in ks)
    o.append(SH(cx, 350, cw, '', 'GROUND FLOOR · KEY SPACES', 'M²', on=1))
    o.append(A(cx, 376, cw, f'<table style="border-collapse:collapse;width:100%;font-size:10.5px;line-height:1.38;color:{INK}">{kt}</table>'))
    yb = gy + gh + 22
    o.append(SH(gx, yb, gw, '12', 'INDIVIDUAL BRIEF', on=2))
    br = [('PURPOSE', 'SELL AND CELEBRATE THE FOOD OF TEMERLOH AND THE 11 PENINSULAR STATES; ONE PLACE WHERE TRAVELLERS, TRADERS AND RESIDENTS MEET.'),
          ('USERS', '8 SHOP-LOT TRADERS + CAFÉ · PEKAN SEHARI + CAR-BOOT TRADERS · FAMILIES, VISITORS, BALIK-KAMPUNG TRAVELLERS · 20 STAFF.'),
          ('BUILDING', '2 STOREYS + ROOF TERRACE · 1,548.8 M² ENCLOSED · 12.5 M STEEL SPAN OVER THE HALL (MEDIUM SPAN).'),
          ('ADDED (OPEN, NOT GFA)', 'SERAMBI TENGAH POP-UP BAYS · LALUAN SIMPUL ROOF WALK + TAMAN ULAM · DATARAN TEMU PLAZA · 4 RIBBON CANOPIES.')]
    cards = ''.join(f'<div style="background:#FFFFFF;border:1px solid {RULE};padding:7px 9px"><div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:10px;color:{TERRA}">{h}</div><div style="font-size:9px;line-height:1.35;color:{INK};margin-top:2px">{b}</div></div>' for h, b in br)
    o.append(A(gx, yb + 26, gw, f'<div style="display:grid;grid-template-columns:repeat(4, minmax(0, 1fr));gap:8px">{cards}</div>'
               + P('<b>CULTURE EXCHANGE:</b> JELAJAH RASA 11 NEGERI · RUMAH TERBUKA SEMENANJUNG · DAPUR REWANG DEMOS · HENTIAN BALIK KAMPUNG · PEKAN SEHARI · PETA RASA + TAMAN ULAM.', 9.5, 1.38, INK, 'margin-top:8px')))
    return ''.join(o)
