# -*- coding: utf-8 -*-
import json
from content import *
META = 'MEGAT MUHAMMAD IHSAN BIN MUHAMMAD NOOR · SECTION 8 · AR. ADIB BIN MARUZIKI'
W, H = 1587, 1123
def build(IM):
    an = json.load(open('/home/claude/boards/img/hero1b_anchors.json'))
    ex = json.load(open('/home/claude/boards/img/exaxo.json'))
    o = []
    HW, HH = 1090, 470; k = HW / 1123
    o.append(IMG(IM('hero1b'), 0, 0, HW, HH, 'Aerial collage of Titik Temu on Site C floating on a mint grid sky with clouds, gulls and people', fit='cover'))
    o.append(A(38, 26, 560, P('KAED · IIUM  |  BAAR 3101 ARCHITECTURAL DESIGN 5  |  SEM 1 2026/2027', 9.5, 1.3, INK, 'letter-spacing:0.12em;font-weight:500')
                          + P('CRIT 1 · TASK 3A  —  CONCEPTUAL IDEAS + SCHEMATIC BUILDING DESIGN', 9.5, 1.3, TERRA, 'letter-spacing:0.12em;font-weight:700;margin-top:3px')))
    o.append(A(38, 66, 140, f'<div style="display:inline-block;background:{INK};color:#F4F1EA;font-weight:700;font-size:10px;letter-spacing:0.14em;padding:4px 8px">SHEET 01 / 05</div>'))
    o.append(A(34, 122, 440, f'<h1 style="margin:0;font-family:Syne, Arial, sans-serif;font-weight:800;font-size:76px;line-height:0.86;color:{INK}">TITIK<br>TEMU</h1>'))
    o.append(A(38, 264, 430, f'<p style="margin:0;font-family:Syne, Arial, sans-serif;font-weight:700;font-size:18.5px;color:{TERRA}">SIMPUL RASA SEMENANJUNG</p>'))
    o.append(A(38, 295, 395, P('TEMERLOH SITS AT THE CENTRE OF PENINSULAR MALAYSIA, WHERE THE ROADS FROM EVERY COAST MEET. TITIK TEMU IS WHERE THEIR <b>FOOD</b> AND THEIR <b>PEOPLE</b> MEET: A LOCAL FOOD HUB THAT TIES THE FLAVOURS OF ELEVEN STATES INTO ONE KNOT BESIDE SUNGAI PAHANG.', 10.3, 1.42, INK)))
    o.append(A(38, 398, 410, P('ESPLANADE LOCAL COMMERCIAL HUB · SITE C, JALAN TOK MUDA AWANG NGAH, TEMERLOH · LOT 10150 · 5,370 M²', 8.5, 1.35, MUTE)
                          + P(f'<b>{META}</b>', 8.5, 1.35, INK, 'margin-top:3px')))
    boxes = [(470, 205, 150, 'SIMPUL CROWN', 'TWO RIBBONS CROSS AT +13.5 M OVER THE LIFT CORE.', 'crown', (620, 212)),
             (560, 318, 160, 'TALAM COURT · Ø18 M', 'OPEN DINING FOR 100 UNDER THE OCULUS.', 'court', (720, 322)),
             (730, 410, 170, 'DATARAN TEMU · ≈820 M²', 'PEKAN SEHARI, CAR BOOT + FESTIVE POP-UPS.', 'plaza', (900, 412))]
    lines = []
    for x, y, w, t, b, kk, (lx, ly) in boxes:
        o.append(BOX(round(x * k), round(y * k) - 4, w, t, b)); ax, ay = an[kk]; lines.append((lx * k, ly * k - 4, ax * k, ay * k))
    o.append(LEADERS(W, H, lines))
    # ---------- right column: 01 the centre
    X1, W1 = 1110, 445
    o.append(SH(X1, 20, W1, '01', 'THE CENTRE', 'OF THE PENINSULA', on=1))
    o.append(IMG(IM('map'), X1, 46, W1, 318, 'Sketch map: routes from the 11 state capitals converge on Temerloh', st='background:#EFEBE2'))
    o.append(A(X1, 372, W1, P('JUPEM (2009) FIXED THE CENTRE POINT OF THE PENINSULA IN TEMERLOH DISTRICT. STRAIGHT-LINE: KANGAR 414 KM · KOTA BHARU 299 · JOHOR BAHRU 264 · K. TERENGGANU 224 · IPOH 196 · KUANTAN 108 · KL 88.', 9.5, 1.36, INK)))
    # ---------- row B
    yB = 488
    o.append(SH(32, yB, 400, '02', 'FORM: ROUTES → RIBBONS → KNOT', on=2))
    o.append(IMG(IM('formgen'), 32, yB + 26, 400, 246, 'Six sketch frames: routes, ribbons, knot, two loops on the qibla line, four gates, lift and skin'))
    o.append(A(32, yB + 278, 400, P('ELEVEN ROUTES BUNDLE INTO FOUR REGIONAL RIBBONS THAT TIE A KNOT (<i>SIMPUL</i>). THE KNOT BECOMES TWO LOOPS ON THE QIBLA LINE, 26.2 M APART: <b>GELUNG RASA</b> (FOOD RING, Ø36.2 M) AND <b>GELUNG KECIL</b> (QUIET RING, Ø21.2 M). THE LIFT + STAIR CORE SITS AT THE CROSSING.', 8.6, 1.32, INK)))
    o.append(SH(450, yB, 310, '03', 'FLAVOURS + GATES', '11 STATES, 4 RIBBONS', on=3))
    rows = [('UTARA', 'PERLIS, KEDAH, P. PINANG, PERAK', '311–324°', 'NW DOOR, KNOT'), ('TENGAH', 'SELANGOR, KL, PUTRAJAYA', '235–247°', 'SERAMBI TENGAH'),
            ('SELATAN', 'N. SEMBILAN, MELAKA, JOHOR', '146–214°', 'GERBANG SELATAN'), ('P. TIMUR', 'PAHANG, TERENGGANU, KELANTAN', '356–68°', 'GERBANG TIMUR')]
    cols = ['#D9782A', '#4E8F3A', '#7A55A8', '#C23B2E']
    t = f'<table style="border-collapse:collapse;width:100%;font-size:9.3px;line-height:1.3;color:{INK}">'
    t += f'<tr style="border-bottom:1px solid {INK}">' + ''.join(f'<th style="text-align:left;font-weight:700;padding:2px 3px 3px 0;white-space:nowrap">{h}</th>' for h in ['RIBBON', 'STATES', 'CAPITALS', 'GATE']) + '</tr>'
    for (r, st_, b, g), c in zip(rows, cols):
        t += f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:4px 3px 4px 0;font-weight:700;color:{c};white-space:nowrap">{r}</td><td style="padding:4px 3px">{st_}</td><td style="padding:3px 3px;white-space:nowrap">{b}</td><td style="padding:3px 0 3px 3px">{g}</td></tr>'
    t += '</table>'
    o.append(A(450, yB + 26, 310, t + P('YOU COME IN FROM THE SIDE OF YOUR OWN REGION AND MEET EVERYONE ELSE IN THE <b>TALAM</b> COURT, LIKE DISHES FROM MANY KITCHENS ON ONE SHARED TRAY.', 9.8, 1.4, INK, 'margin-top:10px')
               + P('<b style="color:#B4492B">FUTURISTIC TYPOLOGY:</b> CONTINUOUS RIBBON FORMS, A COMPUTED CLAY LAMELLA SKIN, A SOLAR RIBBON ROOF AND PLUG-IN PUBLIC SPACE.', 9.8, 1.4, INK, 'margin-top:8px')))
    o.append(SH(778, yB, 392, '04', 'SITE SYNTHESIS', 'RESPONSES ON SHEET 02', on=1))
    o.append(IMG(IM('synth'), 778, yB + 26, 392, 250, 'Site synthesis: sun path, monsoon winds, river breeze, views, Istana privacy, slope and flood-prone riverbank', fit='cover'))
    o.append(A(778, yB + 282, 392, P('LOT 10150 · 5,370 M² · SUN, MONSOONS, RIVER BREEZE, VIEWS TO SUNGAI PAHANG, ISTANA PRIVACY, SLOPE + DEC 2014 FLOODS.', 8.6, 1.32, MUTE)))
    EW = 370; kx = EW / 640; EH = round(496.2 * kx, 1); ex0, ey0 = 1185, yB + 26
    o.append(SH(ex0, yB, EW, '05', 'EXPLODED AXONOMETRIC', 'A DAY AT TITIK TEMU', on=3))
    o.append(IMG(IM('exaxo'), ex0, ey0, EW, EH, 'Exploded axonometric split into night, day and Sunday bands with people on every floor', fit='fill'))
    caps = [('NIGHT', 'ISYAK AT THE MUSOLLA; THE KNOT GLOWS.', True), ('DAY', 'LUNCH AT THE TALAM: 100 SEATS.', False), ('SUNDAY', 'PEKAN SEHARI + COOKING DEMO.', False)]
    for (bx0, bx1, kind), (tt, b, dark), n in zip(ex['bands'], caps, [3, 2, 1]):
        x = ex0 + bx0 * kx + 2; w = (bx1 - bx0) * kx - 4; c = '#FFFFFF' if dark else INK
        o.append(A(x, ey0 + EH + 6, w, f'<div style="border:1px dashed {"rgba(255,255,255,0.85)" if dark else "#4C565A"};background:{"rgba(28,38,62,0.92)" if dark else "rgba(255,255,255,0.9)"};padding:3px 4px">'
                   + f'<div style="font-size:8px;font-weight:700;letter-spacing:0.06em;color:{c};white-space:nowrap">{SQ(n, "#FFFFFF" if dark else TERRA, 5)} {tt}</div><div style="font-size:7.6px;line-height:1.22;color:{c};margin-top:1px">{b}</div></div>'))
    lab = [('roofhall', 'PV RIBBON ROOF', 8, -12), ('roofsmall', 'ROOF +9.9', -20, -20), ('musolla', 'MUSOLLA · QIBLA', -4, -22),
           ('terrace', 'LALUAN SIMPUL', -30, -22), ('hall', 'DAPUR REWANG HALL', 10, -10), ('gallery', 'GALLERY', 12, -16)]
    lines = []
    for key, tt, dx, dy in lab:
        ax, ay = ex['anchors'][key]; ax = ex0 + ax * kx; ay = ey0 + ay * kx; tx, ty = ax + dx, ay + dy
        tx = min(tx, ex0 + EW - 96) if key in ('hall',) else tx
        o.append(A(tx, ty - 7, 140, f'<span style="display:inline-block;background:rgba(255,255,255,0.92);border:1px solid #4C565A;font-size:7px;font-weight:700;padding:1px 3px;color:{INK};white-space:nowrap">{tt}</span>'))
        lines.append((tx + 2, ty, ax, ay))
    o.append(LEADERS(W, H, lines))
    # ---------- row C
    yC = 858
    o.append(SH(32, yC, 560, '06', 'PRECEDENT STUDIES', 'LESSONS → DECISIONS', on=2))
    pre = [('p8', '8 HOUSE, COPENHAGEN', 'BIG · 2010', 'A FIGURE-8 BLOCK WHOSE KNOT IS A PUBLIC PASSAGE.', 'LOBBY + CORE AT THE KNOT; ROOF WALK LOOPS THE RING'),
           ('pbait', 'BAIT UR ROUF, DHAKA', 'MARINA TABASSUM · 2012', 'HALL TURNED TO THE QIBLA; POROUS BRICK FOR SHADE + AIR.', 'SMALL RING ON THE QIBLA LINE; CLAY LAMELLA SKIN'),
           ('pka', 'KAMPUNG ADMIRALTY, SG', 'WOHA · 2017', 'A TROPICAL COMMUNITY “LIVING ROOM” WITH A HAWKER CENTRE.', 'TALAM COURT + DATARAN TEMU FOR DAILY LIFE')]
    for i, (kk, n, a, l, dd) in enumerate(pre):
        x = 32 + i * 190
        o.append(A(x, yC + 26, 180, f'<img src="{IM(kk)}" alt="{n} diagram, redrawn" style="display:block;width:180px;height:112px;object-fit:contain;background:#FFFFFF">'
                   + f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:9.5px;color:{INK};margin-top:5px;white-space:nowrap">{n}</div>'
                   + P(a, 8, 1.3, MUTE) + P(l, 8.3, 1.3, INK, 'margin-top:2px') + P(f'<b style="color:#B4492B">→ {dd}</b>', 8.3, 1.3, INK, 'margin-top:2px')))
    X7 = 610; W7 = W - 32 - X7
    o.append(SH(X7, yC, W7, '07', 'PERSPECTIVES', 'INTERIOR + EXTERIOR SKETCHES', on=2))
    ints = [('i_court', 'Talam court'), ('i_lobby', 'Lobby Simpul'), ('i_hall', 'Dapur Rewang hall'), ('i_gate', 'Gerbang Selatan')]
    pw = (W7 - 3 * 8) / 4
    for i, (kk, tt) in enumerate(ints):
        o.append(IMG(IM(kk), X7 + i * (pw + 8), yC + 26, pw, pw / 1.6, tt + ' perspective sketch', fit='cover'))
    kf = [('1,548.8 M²', 'ENCLOSED GFA'), ('2 + ROOF', 'STOREYS'), ('12.5 M', 'STEEL SPAN'), ('11', 'STATES · 1 KNOT'), ('4', 'GATES + RIBBONS')]
    tiles = ''.join(f'<div style="flex:{1.4 if i == 0 else 1};border-left:2px solid {TERRA};padding:2px 0 2px 8px"><div style="font-family:Syne, Arial, sans-serif;font-weight:800;font-size:17px;line-height:1.1;color:{INK};white-space:nowrap">{a}</div><div style="font-size:8px;font-weight:700;letter-spacing:0.06em;color:{MUTE};margin-top:2px;white-space:nowrap">{b}</div></div>' for i, (a, b) in enumerate(kf))
    o.append(A(X7, yC + 200, W7, f'<div style="display:flex;gap:10px;border-top:1px solid {RULE};padding-top:9px">{tiles}</div>'))
    return ''.join(o)
