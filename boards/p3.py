# -*- coding: utf-8 -*-
import json
from content import *
def build(IM):
    T = json.load(open('/home/claude/boards/img/truescale.json')); o = []
    o.append(PAGEHEAD(32, 18, 1059, 'SHEET 03 / 04', 'FIRST FLOOR PLAN + SECTION B–B 1:200 · BRIEF + SOA', 'CRIT 1 · TASK 3A · MEGAT MUHAMMAD IHSAN · SECTION 8'))
    lw, lh = T['l1']['wpx'], T['l1']['hpx']; lx = (1123 - lw) / 2; ly = 90
    o.append(A(lx, 68, lw, f'<div style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK}">{SQ(2)} 10 · FIRST FLOOR PLAN · FFL +5.400 · <span style="color:{TERRA}">SCALE 1:200</span> · ROOM AREAS IN M²</div>'))
    o.append(IMG(IM('l1'), lx, ly, lw, lh, 'First floor plan at 1:200: gallery and Dapur Rewang hall to the east, admin and musolla in Gelung Kecil, roof walk around the court', fit='fill'))
    o.append(SCALEBAR(lx + 12, ly + lh - 48, 200, [0, 1, 2, 5, 10]))
    o.append(NORTH(lx + lw - 46, ly + 10))
    bw, bh = T['secB']['wpx'], T['secB']['hpx']; bx = (1123 - bw) / 2; by = ly + lh + 30
    o.append(A(bx, by - 20, bw, f'<div style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK}">{SQ(1)} 11 · SECTION B–B · NORTH–SOUTH THROUGH THE TALAM COURT · <span style="color:{TERRA}">SCALE 1:200</span></div>'))
    o.append(IMG(IM('secB'), bx, by, bw, bh, 'Section B-B at 1:200 through the Talam court between shop lots A1-4 and A2-2', fit='fill'))
    o.append(SCALEBAR(bx + bw - 230, by + 6, 200, [0, 1, 2, 5, 10]))
    yR = by + bh + 12
    o.append(SH(32, yR, 560, '12', 'SCHEDULE OF ACCOMMODATION', 'DRAWN VS SITE C BRIEF (M²)', on=3))
    soa = [('A', 'RETAIL: 8 SHOP LOTS + CAFÉ', '306', '403.9', '324.5'), ('B', 'GALLERY + MPH (COURT DINING OPEN)', '317', '418.4', '224.3'),
           ('C', 'MANAGEMENT / ADMIN + FIRST AID', '118', '142.8', '137.5'), ('D', 'LOBBY, MUSOLLA, TOILETS', '295', '340.7', '436.4'),
           ('E', 'SERVICES / UTILITIES', '182', '219.8', '191.7'), ('', 'CORES, STAIRS, LIFTS, CORRIDORS', '–', 'IN %', '234.3')]
    th = ''.join(f'<th style="text-align:{al};font-weight:700;padding:4px 5px;border-bottom:1.5px solid {INK};white-space:nowrap">{h}</th>' for h, al in
                 [('', 'left'), ('CATEGORY', 'left'), ('SOA NET', 'right'), ('SOA GROSS', 'right'), ('DRAWN', 'right')])
    tr = ''.join(f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:4px 5px;font-weight:700;color:{TERRA}">{a}</td><td style="padding:4px 5px">{b}</td><td style="padding:4px 5px;text-align:right">{c}</td><td style="padding:4px 5px;text-align:right">{d}</td><td style="padding:4px 5px;text-align:right;font-weight:700">{e}</td></tr>' for a, b, c, d, e in soa)
    tr += f'<tr style="border-top:1.5px solid {INK};background:#EFE8DA"><td></td><td style="padding:5px 5px;font-weight:700">TOTAL ENCLOSED</td><td style="padding:5px 5px;text-align:right;font-weight:700">1,218</td><td style="padding:5px 5px;text-align:right;font-weight:700">1,525.6</td><td style="padding:5px 5px;text-align:right;font-weight:700;color:{TERRA}">1,548.8 (+1.5 %)</td></tr>'
    o.append(A(32, yR + 24, 560, f'<table style="border-collapse:collapse;width:100%;font-size:10px;line-height:1.25;color:{INK}"><tr>{th}</tr>{tr}</table>'
               + P('EVERY ROOM MEETS OR BEATS ITS SOA NET SIZE. GF ≈866 M² + L1 ≈683 M²; OPEN VERANDAH + BALCONY ≈163 M² NOT COUNTED. CIRCULATION ≈28 % (BRIEF 25–30 %). PLOT RATIO ≈0.29 · COVERAGE ≈30 % · TOP OF CROWN +13.5 M.', 8.5, 1.35, MUTE, 'margin-top:6px')))
    o.append(SH(608, yR, 483, '13', 'INDIVIDUAL BRIEF', on=2))
    br = [('PURPOSE', 'SELL AND CELEBRATE THE FOOD OF TEMERLOH AND THE 11 PENINSULAR STATES; ONE PLACE WHERE TRAVELLERS, TRADERS AND RESIDENTS MEET.'),
          ('USERS', '8 SHOP-LOT TRADERS + CAFÉ · PEKAN SEHARI + CAR-BOOT TRADERS · FAMILIES, VISITORS, BALIK-KAMPUNG TRAVELLERS · 20 STAFF.'),
          ('BUILDING', '2 STOREYS + ROOF TERRACE · 1,548.8 M² ENCLOSED · 12.5 M STEEL SPAN OVER THE HALL (MEDIUM SPAN).'),
          ('ADDED (OPEN, NOT GFA)', 'SERAMBI TENGAH POP-UP BAYS · LALUAN SIMPUL ROOF WALK + TAMAN ULAM · DATARAN TEMU PLAZA · 4 RIBBON CANOPIES.')]
    cards = ''.join(f'<div style="background:#FFFFFF;border:1px solid {RULE};padding:7px 8px"><div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:10.5px;color:{TERRA}">{h}</div><div style="font-size:9px;line-height:1.35;color:{INK};margin-top:1px">{b}</div></div>' for h, b in br)
    o.append(A(608, yR + 24, 483, f'<div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:7px">{cards}</div>'
               + P('<b>CULTURE EXCHANGE:</b> JELAJAH RASA 11 NEGERI · RUMAH TERBUKA SEMENANJUNG · DAPUR REWANG DEMOS · HENTIAN BALIK KAMPUNG · PEKAN SEHARI · PETA RASA + TAMAN ULAM.', 9, 1.35, INK, 'margin-top:8px')))
    idx = [('01', 'CONCEPT, SITE SYNTHESIS, FORM, EXPLODED AXO, PRECEDENTS, PERSPECTIVES'), ('02', 'SITE PLAN 1:500 + GROUND FLOOR PLAN 1:200'),
           ('03', 'FIRST FLOOR PLAN + SECTION B–B 1:200 · SOA · BRIEF'), ('04', 'SECTION A–A + SOUTH / EAST ELEVATIONS 1:200 · TECHNICAL STUDY')]
    it = ''.join(f'<div style="flex:1;font-size:8px;line-height:1.3;color:{INK}"><b style="font-family:Syne, Arial, sans-serif;font-size:11px;color:{TERRA}">{a}</b> {b}</div>' for a, b in idx)
    o.append(A(32, 1500, 1059, f'<div style="border-top:2px solid {INK};padding-top:6px;display:flex;gap:18px;align-items:flex-start">'
               + f'<div style="flex:0 0 120px;font-size:9px;font-weight:700;letter-spacing:0.08em;color:{INK}">SHEET INDEX</div>{it}</div>'
               + f'<div style="margin-top:8px;font-size:8.5px;font-weight:700;letter-spacing:0.06em;color:{TERRA}">PRINT AT 100 % ON A3 (NO "FIT TO PAGE") — PLANS, SECTIONS + ELEVATIONS ARE TRUE 1:200, SITE PLAN TRUE 1:500. CHECK WITH THE SCALE BARS.</div>'))
    return ''.join(o)
