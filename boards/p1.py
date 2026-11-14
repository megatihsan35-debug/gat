# -*- coding: utf-8 -*-
import json
from content import *
META = 'MEGAT MUHAMMAD IHSAN BIN MUHAMMAD NOOR · SECTION 8 · AR. ADIB BIN MARUZIKI'
def build(IM):
    an = json.load(open('/home/claude/boards/img/hero1b_anchors.json'))
    ex = json.load(open('/home/claude/boards/img/exaxo.json'))
    o = []
    o.append(IMG(IM('hero1b'), 0, 0, 1123, 484, 'Aerial collage of Titik Temu on Site C floating on a mint grid sky with clouds, gulls and people', fit='cover'))
    o.append(A(40, 28, 560, P('KAED · IIUM  |  BAAR 3101 ARCHITECTURAL DESIGN 5  |  SEM 1 2026/2027', 9.5, 1.3, INK, 'letter-spacing:0.12em;font-weight:500')
                          + P('CRIT 1 · TASK 3A  —  CONCEPTUAL IDEAS + SCHEMATIC BUILDING DESIGN', 9.5, 1.3, TERRA, 'letter-spacing:0.12em;font-weight:700;margin-top:3px')))
    o.append(A(40, 68, 140, f'<div style="display:inline-block;background:{INK};color:#F4F1EA;font-weight:700;font-size:10px;letter-spacing:0.14em;padding:4px 8px">SHEET 01 / 04</div>'))
    o.append(A(36, 128, 440, f'<h1 style="margin:0;font-family:Syne, Arial, sans-serif;font-weight:800;font-size:78px;line-height:0.86;color:{INK}">TITIK<br>TEMU</h1>'))
    o.append(A(40, 274, 430, f'<p style="margin:0;font-family:Syne, Arial, sans-serif;font-weight:700;font-size:19px;color:{TERRA}">SIMPUL RASA SEMENANJUNG</p>'))
    o.append(A(40, 306, 400, P('TEMERLOH SITS AT THE CENTRE OF PENINSULAR MALAYSIA, WHERE THE ROADS FROM EVERY COAST MEET. TITIK TEMU IS WHERE THEIR <b>FOOD</b> AND THEIR <b>PEOPLE</b> MEET: A LOCAL FOOD HUB THAT TIES THE FLAVOURS OF ELEVEN STATES INTO ONE KNOT BESIDE SUNGAI PAHANG.', 10.5, 1.42, INK)))
    o.append(A(40, 412, 420, P('ESPLANADE LOCAL COMMERCIAL HUB · SITE C, JALAN TOK MUDA AWANG NGAH, TEMERLOH · LOT 10150 · 5,370 M²', 8.5, 1.35, MUTE)
                          + P(f'<b>{META}</b>', 8.5, 1.35, INK, 'margin-top:3px')))
    boxes = [(470, 205, 150, 'SIMPUL CROWN', 'TWO RIBBONS CROSS AT +13.5 M OVER THE LIFT CORE.', 'crown', (620, 212)),
             (560, 318, 160, 'TALAM COURT · Ø18 M', 'OPEN DINING FOR 100 UNDER THE OCULUS.', 'court', (720, 322)),
             (730, 410, 170, 'DATARAN TEMU · ≈820 M²', 'PEKAN SEHARI, CAR BOOT + FESTIVE POP-UPS.', 'plaza', (900, 412))]
    lines = []
    for x, y, w, t, b, k, (lx, ly) in boxes:
        o.append(BOX(x, y, w, t, b)); ax, ay = an[k]; lines.append((lx, ly, ax, ay))
    o.append(LEADERS(1123, 484, lines))
    # ---------- row 2 concept
    y2 = 498
    o.append(SH(40, y2, 300, '01', 'THE CENTRE', 'OF THE PENINSULA', on=1))
    o.append(IMG(IM('map'), 40, y2 + 26, 300, 196, 'Sketch map: routes from the 11 state capitals converge on Temerloh', st='background:#EFEBE2'))
    o.append(A(40, y2 + 228, 300, P('JUPEM (2009) FIXED THE CENTRE POINT OF THE PENINSULA IN TEMERLOH DISTRICT. STRAIGHT-LINE: KANGAR 414 KM · KOTA BHARU 299 · JOHOR BAHRU 264 · K. TERENGGANU 224 · IPOH 196 · KUANTAN 108 · KL 88.', 9, 1.34, INK)))
    o.append(SH(360, y2, 400, '02', 'FORM: ROUTES → RIBBONS → KNOT', on=2))
    o.append(IMG(IM('formgen'), 360, y2 + 26, 400, 214, 'Six sketch frames: routes, ribbons, knot, two loops on the qibla line, four gates, lift and skin'))
    o.append(A(360, y2 + 244, 400, P('ELEVEN ROUTES BUNDLE INTO FOUR REGIONAL RIBBONS THAT TIE A KNOT (<i>SIMPUL</i>). THE KNOT BECOMES TWO LOOPS ON THE QIBLA LINE, 26.2 M APART: <b>GELUNG RASA</b> (FOOD RING, Ø36.2 M) AND <b>GELUNG KECIL</b> (QUIET RING, Ø21.2 M). THE LIFT + STAIR CORE SITS AT THE CROSSING.', 9, 1.34, INK)))
    o.append(SH(780, y2, 303, '03', 'FLAVOURS + GATES', '11 STATES, 4 RIBBONS', on=3))
    rows = [('UTARA', 'PERLIS, KEDAH, P. PINANG, PERAK', '311–324°', 'NW DOOR, KNOT'), ('TENGAH', 'SELANGOR, KL, PUTRAJAYA', '235–247°', 'SERAMBI TENGAH'),
            ('SELATAN', 'N. SEMBILAN, MELAKA, JOHOR', '146–214°', 'GERBANG SELATAN'), ('P. TIMUR', 'PAHANG, TERENGGANU, KELANTAN', '356–68°', 'GERBANG TIMUR')]
    cols = ['#D9782A', '#4E8F3A', '#7A55A8', '#C23B2E']
    t = f'<table style="border-collapse:collapse;width:100%;font-size:8.5px;line-height:1.25;color:{INK}">'
    t += f'<tr style="border-bottom:1px solid {INK}">' + ''.join(f'<th style="text-align:left;font-weight:700;padding:2px 3px 3px 0;white-space:nowrap">{h}</th>' for h in ['RIBBON', 'STATES', 'CAPITALS', 'GATE']) + '</tr>'
    for (r, st_, b, g), c in zip(rows, cols):
        t += f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:3px 3px 3px 0;font-weight:700;color:{c};white-space:nowrap">{r}</td><td style="padding:3px 3px">{st_}</td><td style="padding:3px 3px;white-space:nowrap">{b}</td><td style="padding:3px 0 3px 3px">{g}</td></tr>'
    t += '</table>'
    o.append(A(780, y2 + 26, 303, t + P('YOU COME IN FROM THE SIDE OF YOUR OWN REGION AND MEET EVERYONE ELSE IN THE <b>TALAM</b> COURT, LIKE DISHES FROM MANY KITCHENS ON ONE SHARED TRAY.', 9, 1.34, INK, 'margin-top:7px')
               + P('<b style="color:#B4492B">FUTURISTIC TYPOLOGY:</b> CONTINUOUS RIBBON FORMS, A COMPUTED CLAY LAMELLA SKIN, A SOLAR RIBBON ROOF AND PLUG-IN PUBLIC SPACE.', 9, 1.34, INK, 'margin-top:5px')))
    # ---------- row 3 synthesis + exploded axo
    y3 = 818
    o.append(SH(40, y3, 551, '04', 'SITE SYNTHESIS', 'LOT 10150 · 5,370 M² · RESPONSES ON SHEET 02', on=1))
    o.append(IMG(IM('synth'), 40, y3 + 26, 551, 352, 'Site synthesis: sun path, monsoon winds, river breeze, views, Istana privacy, slope and flood-prone riverbank', fit='cover'))
    EW, EH = 454, 352; k = EW / 640; ex0, ey0 = 629, y3 + 26
    o.append(SH(629, y3, EW, '05', 'EXPLODED AXONOMETRIC', 'A DAY AT TITIK TEMU', on=3))
    o.append(IMG(IM('exaxo'), ex0, ey0, EW, EH, 'Exploded axonometric split into night, day and Sunday bands with people on every floor', fit='fill'))
    caps = [('NIGHT', 'ISYAK AT THE MUSOLLA; THE KNOT GLOWS.', True), ('DAY', 'LUNCH AT THE TALAM: 100 SEATS.', False), ('SUNDAY', 'PEKAN SEHARI + COOKING DEMO.', False)]
    for (bx0, bx1, kind), (tt, b, dark), n in zip(ex['bands'], caps, [3, 2, 1]):
        x = ex0 + bx0 * k + 3; w = (bx1 - bx0) * k - 6; c = '#FFFFFF' if dark else INK
        o.append(A(x, ey0 + EH - 44, w, f'<div style="border:1px dashed {"rgba(255,255,255,0.85)" if dark else "#4C565A"};background:{"rgba(28,38,62,0.82)" if dark else "rgba(255,255,255,0.85)"};padding:3px 5px">'
                   + f'<div style="font-size:8.5px;font-weight:700;letter-spacing:0.08em;color:{c};white-space:nowrap">{SQ(n, "#FFFFFF" if dark else TERRA, 6)} {tt}</div><div style="font-size:8px;line-height:1.25;color:{c};margin-top:1px">{b}</div></div>'))
    lab = [('roofhall', 'PV RIBBON ROOF', 10, -14), ('roofsmall', 'ROOF +9.9', -24, -24), ('musolla', 'MUSOLLA · QIBLA', -6, -26),
           ('terrace', 'LALUAN SIMPUL', -34, -26), ('hall', 'DAPUR REWANG HALL', 12, -12), ('gallery', 'GALLERY', 16, -18)]
    lines = []
    for key, tt, dx, dy in lab:
        ax, ay = ex['anchors'][key]; ax = ex0 + ax * k; ay = ey0 + ay * k; tx, ty = ax + dx, ay + dy
        o.append(A(tx, ty - 7, 140, f'<span style="display:inline-block;background:rgba(255,255,255,0.9);border:1px solid #4C565A;font-size:7.5px;font-weight:700;padding:1px 3px;color:{INK};white-space:nowrap">{tt}</span>'))
        lines.append((tx + 2, ty, ax, ay))
    o.append(LEADERS(1123, 1587, lines))
    # ---------- row 4 precedents + perspectives
    y4 = 1210
    o.append(SH(40, y4, 486, '06', 'PRECEDENT STUDIES', 'LESSONS → DECISIONS', on=2))
    pre = [('p8', '8 HOUSE, COPENHAGEN', 'BIG · 2010', 'A FIGURE-8 BLOCK WHOSE KNOT IS A PUBLIC PASSAGE.', 'LOBBY + CORE AT THE KNOT; ROOF WALK LOOPS THE RING'),
           ('pbait', 'BAIT UR ROUF, DHAKA', 'MARINA TABASSUM · 2012', 'HALL TURNED TO THE QIBLA; POROUS BRICK FOR SHADE + AIR.', 'SMALL RING ON THE QIBLA LINE; CLAY LAMELLA SKIN'),
           ('pka', 'KAMPUNG ADMIRALTY, SG', 'WOHA · 2017', 'A TROPICAL COMMUNITY “LIVING ROOM” WITH A HAWKER CENTRE.', 'TALAM COURT + DATARAN TEMU FOR DAILY LIFE')]
    for i, (kk, n, a, l, dd) in enumerate(pre):
        x = 40 + i * 166
        o.append(A(x, y4 + 26, 156, f'<img src="{IM(kk)}" alt="{n} diagram, redrawn" style="display:block;width:156px;height:128px;object-fit:contain;background:#FFFFFF">'
                   + f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:9.5px;color:{INK};margin-top:5px">{n}</div>'
                   + P(a, 8, 1.3, MUTE) + P(l, 8.5, 1.3, INK, 'margin-top:3px') + P(f'<b style="color:#B4492B">→ {dd}</b>', 8.5, 1.3, INK, 'margin-top:3px')))
    o.append(SH(546, y4, 537, '07', 'PERSPECTIVES', 'INTERIOR + EXTERIOR SKETCHES', on=2))
    ints = [('i_court', 'Talam court'), ('i_lobby', 'Lobby Simpul'), ('i_hall', 'Dapur Rewang hall'), ('i_gate', 'Gerbang Selatan')]
    for i, (kk, tt) in enumerate(ints):
        x = 546 + (i % 2) * 272; y = y4 + 26 + (i // 2) * 158
        o.append(IMG(IM(kk), x, y, 265, 152, tt + ' perspective sketch', fit='cover'))
    kf = [('1,548.8 M²', 'ENCLOSED GFA'), ('2 + ROOF', 'STOREYS'), ('12.5 M', 'STEEL SPAN'), ('11', 'STATES · 1 KNOT'), ('4', 'GATES')]
    tiles = ''.join(f'<div style="flex:{1.55 if i == 0 else 1};border-left:2px solid {TERRA};padding:2px 0 2px 7px"><div style="font-family:Syne, Arial, sans-serif;font-weight:800;font-size:15px;line-height:1.1;color:{INK};white-space:nowrap">{a}</div><div style="font-size:7.5px;font-weight:700;letter-spacing:0.06em;color:{MUTE};margin-top:2px;white-space:nowrap">{b}</div></div>' for i, (a, b) in enumerate(kf))
    o.append(A(40, 1500, 486, f'<div style="display:flex;gap:8px;border-top:1px solid {RULE};padding-top:8px">{tiles}</div>'))
    return ''.join(o)
