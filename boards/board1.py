# -*- coding: utf-8 -*-
import json
from content import *
def build(IM):
    an = json.load(open('/home/claude/boards/img/hero1_anchors.json'))
    o = []
    o.append(IMG(IM('hero1'), 0, 0, 1123, 640, 'Aerial collage of Titik Temu on Site C: the two terracotta lamella rings tied by the red Simpul crown, PV ribbon roof, ribbon canopies and plaza, floating on a mint grid sky with clouds, gulls and people', fit='cover'))
    # kicker
    o.append(A(40, 34, 560, P('KAED · IIUM  |  BAAR 3101 ARCHITECTURAL DESIGN 5  |  SEM 1 2026/2027', 9.5, 1.3, INK, 'letter-spacing:0.12em;font-weight:500')
                          + P('CRIT 1 · TASK 3A  —  CONCEPTUAL IDEAS + SCHEMATIC BUILDING DESIGN', 9.5, 1.3, TERRA, 'letter-spacing:0.12em;font-weight:700;margin-top:3px')))
    o.append(A(40, 76, 120, f'<div style="display:inline-block;background:{INK};color:#F4F1EA;font-family:DM Sans, Arial, sans-serif;font-weight:700;font-size:10px;letter-spacing:0.14em;padding:4px 8px">BOARD 01 / 02</div>'))
    # title block
    o.append(A(36, 296, 520, f'<h1 style="margin:0;font-family:Syne, Arial, sans-serif;font-weight:800;font-size:88px;line-height:0.86;letter-spacing:-0.01em;color:{INK}">TITIK<br>TEMU</h1>'))
    o.append(A(40, 456, 470, f'<p style="margin:0;font-family:Syne, Arial, sans-serif;font-weight:700;font-size:21px;color:{TERRA}">Simpul Rasa Semenanjung</p>'))
    o.append(A(40, 488, 400, P('Temerloh sits at the centre of Peninsular Malaysia, where the roads from every coast meet. Titik Temu is where their <b>food</b> and their <b>people</b> meet: a local food hub that ties the flavours of eleven states into one knot beside Sungai Pahang.', 11.5, 1.42, INK)))
    o.append(A(40, 572, 420, P('Esplanade Local Commercial Hub · Site C, Jalan Tok Muda Awang Ngah, Temerloh · Lot 10150 · 5,370 m²', 9.5, 1.35, MUTE)
                          + P('<b>Megat Muhammad Ihsan bin Muhammad Noor</b> · Section 8 · Lecturer: Ar. Adib bin Maruziki', 9.5, 1.35, INK, 'margin-top:3px')))
    # hero annotations (dashed boxes, ref style)
    boxes = [
        (548, 14, 150, 'SIMPUL CROWN', 'Two ribbons cross at +13.5 m over the lift core: the knot.', 'crown', (698, 30)),
        (410, 120, 156, 'GELUNG KECIL · Ø21.2 m', 'Services GF · admin + musolla L1, on the qibla line 292.3°.', 'kecil', (566, 136)),
        (612, 518, 168, 'TALAM COURT · Ø18 m', 'Open dining for 100 under the oculus, one shade tree.', 'court', (700, 518)),
        (900, 268, 182, 'DAPUR REWANG HALL', '12.5 m steel span; PV ribbon roof rises to the river.', 'hall', (900, 290)),
        (925, 470, 160, 'DATARAN TEMU · ≈820 m²', 'Pekan Sehari, car boot + festive pop-ups.', 'plaza', (960, 470)),
    ]
    lines = []
    for x, y, w, t, b, k, (lx, ly) in boxes:
        o.append(BOX(x, y, w, t, b))
        ax, ay = an[k]; lines.append((lx, ly, ax, ay))
    o.append(LEADERS(1123, 640, lines))
    # ---------------- row 2: concept
    y2 = 662
    o.append(SH(40, y2, 300, '01', 'THE CENTRE', 'of the Peninsula', on=1))
    o.append(IMG(IM('map'), 40, y2 + 28, 300, 214, 'Sketch map: routes from the 11 state capitals converge on Temerloh, coloured by region', st='background:#EFEBE2'))
    o.append(A(40, y2 + 250, 300, P('JUPEM (2009) fixed the centre point of the Peninsula in Temerloh District. Straight-line distances: Kangar 414 km · Kota Bharu 299 · Johor Bahru 264 · K. Terengganu 224 · Ipoh 196 · Kuantan 108 · KL 88.', 10, 1.36, INK)))
    o.append(SH(360, y2, 400, '02', 'FORM: ROUTES → RIBBONS → KNOT', on=2))
    o.append(IMG(IM('formgen'), 360, y2 + 28, 400, 238, 'Six sketch frames: eleven routes, four ribbons, tie the knot, two loops on the qibla line, four gates, lift and skin'))
    o.append(A(360, y2 + 272, 400, P('Eleven routes bundle into four regional ribbons that tie a knot (<i>simpul</i>). The knot becomes two loops on the qibla line, 26.2 m apart: <b>Gelung Rasa</b>, the food ring (Ø36.2 m) and <b>Gelung Kecil</b>, the quiet ring (Ø21.2 m). The lift + stair core sits at the crossing.', 10, 1.36, INK)))
    o.append(SH(780, y2, 303, '03', 'FLAVOURS + GATES', '11 states, 4 ribbons', on=3))
    rows = [('UTARA', 'Perlis, Kedah, P. Pinang, Perak', '311–324°', 'NW door, knot'),
            ('TENGAH', 'Selangor, KL, Putrajaya', '235–247°', 'Serambi Tengah'),
            ('SELATAN', 'N. Sembilan, Melaka, Johor', '146–214°', 'Gerbang Selatan'),
            ('P. TIMUR', 'Pahang, Terengganu, Kelantan', '356–68°', 'Gerbang Timur')]
    cols = ['#D9782A', '#4E8F3A', '#7A55A8', '#C23B2E']
    t = f'<table style="border-collapse:collapse;width:100%;font-size:9px;line-height:1.25;color:{INK}">'
    t += f'<tr style="border-bottom:1px solid {INK}">' + ''.join(f'<th style="text-align:left;font-weight:700;padding:2px 3px 3px 0;white-space:nowrap">{h}</th>' for h in ['Ribbon', 'States', 'Capitals', 'Gate']) + '</tr>'
    for (r, st_, b, g), c in zip(rows, cols):
        t += f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:3px 3px 3px 0;font-weight:700;color:{c};white-space:nowrap">{r}</td><td style="padding:3px 3px">{st_}</td><td style="padding:3px 3px;white-space:nowrap">{b}</td><td style="padding:3px 0 3px 3px">{g}</td></tr>'
    t += '</table>'
    o.append(A(780, y2 + 28, 303, t
               + P('You come in from the side of your own region and meet everyone else in the <b>Talam</b> court, like dishes from many kitchens on one shared tray. Each gate is the end of its ribbon canopy, set on the true bearing of its capitals.', 10, 1.36, INK, 'margin-top:8px')
               + P('<b style="color:#B4492B">Futuristic typology:</b> continuous ribbon forms, a computed clay lamella skin, a solar ribbon roof and plug-in public space for future events.', 10, 1.36, INK, 'margin-top:6px')))
    # ---------------- row 3: site
    y3 = 982
    o.append(SH(40, y3, 430, '04', 'SITE SYNTHESIS', 'Lot 10150 · 5,370 m²', on=1))
    o.append(IMG(IM('synth'), 40, y3 + 28, 430, 275, 'Site synthesis: sun path, monsoon winds, river breeze, views, Istana privacy, slope and flood-prone riverbank', fit='cover'))
    o.append(SH(490, y3, 343, '05', 'SITE PLANNING', 'with context · 1:500 @ A1', on=2))
    o.append(IMG(IM('siteplan'), 490, y3 + 28, 343, 275, 'Site plan 1:500 with context: the two rings, Dataran Temu plaza to the south-east, Taman Ulam to the north, service yard to the west, ribbons to the road', fit='cover'))
    resp = [('Hot west sun', 'Gelung Kecil + solid lamella drum on the west'),
            ('Sungai Pahang (E)', 'hall, Gerbang Timur + plaza face the river'),
            ('Monsoons + river breeze', 'open court + oculus, porous clay skin'),
            ('Istana (NW), futsal (N)', 'service yard + quiet Taman Ulam to the north'),
            ('Road + stadium (S)', 'Gerbang Selatan, Serambi Tengah, ribbons'),
            ('Slope + Dec 2014 floods', 'plinth +0.9 m; MDB + genset on the plinth')]
    rt = ''.join(P(f'<b>{a}</b> → {b}', 9.5, 1.3, INK, 'margin-bottom:4px') for a, b in resp)
    o.append(A(850, y3 + 28, 233, f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:10px;letter-spacing:0.06em;color:{TERRA};margin-bottom:4px">SITE → RESPONSE</div>' + rt
               + f'<div style="border-top:1px solid {RULE};margin-top:6px;padding-top:5px">'
               + P('<b>Public front</b> south + east; <b>service back</b> west on its own drive. Setbacks 6 m (road) / 3 m. Coverage ≈30 % · plot ratio ≈0.29. Parking: 5 staff, 1 OKU, 10 motorcycle, 10 bicycle; visitors use street + stadium parking.', 9.5, 1.3, INK) + '</div>'))
    # ---------------- row 4: Islamic values + precedents
    y4 = 1300
    o.append(SH(40, y4, 500, '06', 'ISLAMIC VALUE ADDED', 'Quran + Hadith → design', on=2))
    isl = [('QS Al-Hujurat 49:13', '“…made you peoples and tribes that you may know one another.”', 'one Talam court, four gates: everyone meets in one place'),
           ('QS Quraysh 106:1–4', 'The caravans of winter and summer; “…Who has fed them… and made them safe…”', 'a safe place to eat on the coast-to-coast route (E8)'),
           ('Sahih al-Bukhari 5986', 'Whoever wants more provision and a longer life “should keep good relations with his kith and kin.”', 'the simpul (knot) = ties of silaturrahim'),
           ('Sahih al-Bukhari 5392', '“The food for two persons is sufficient for three…”', 'shared round tables, no wastage, food-waste compost'),
           ('QS Al-Baqarah 2:143', '“…We have made you a median [just] community…” (ummatan wasatan)', 'the centre point, and the qibla datum through the knot'),
           ('Brief Islamic values', 'No wastage · beneficial (rahmatan lil-‘alamin) · accessible · no harm · fit for purpose', 'PV + rainwater, lifts + ramps, flood plinth')]
    cells = ''
    for h, q, r in isl:
        cells += (f'<div style="border-top:2px solid {TERRA};padding-top:4px">'
                  f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:10px;color:{TERRA}">{h}</div>'
                  f'<div style="font-size:9.5px;line-height:1.3;font-style:italic;color:{INK};margin-top:2px">{q}</div>'
                  f'<div style="font-size:9.5px;line-height:1.3;color:{INK};margin-top:3px"><b>→ {r}</b></div></div>')
    o.append(A(40, y4 + 28, 500, f'<div style="display:grid;grid-template-columns:repeat(3, minmax(0, 1fr));column-gap:14px;row-gap:10px">{cells}</div>'))
    o.append(SH(560, y4, 523, '07', 'PRECEDENT STUDIES', 'lessons → decisions', on=3))
    pre = [('p8', '8 House, Copenhagen', 'BIG · 2010', 'A figure-8 block whose knot is a public passage, with one path up the building.', 'lobby + core at the knot; roof walk loops the ring'),
           ('pbait', 'Bait Ur Rouf, Dhaka', 'Marina Tabassum · 2012', 'Prayer hall turned to the qibla; porous brick for shade, light and air.', 'small ring on the qibla line; clay lamella skin'),
           ('pka', 'Kampung Admiralty, SG', 'WOHA · 2017', 'A tropical community “living room” with a hawker centre at its heart.', 'Talam court + Dataran Temu for daily life')]
    for i, (k, n, a, l, d) in enumerate(pre):
        x = 560 + i * 178
        o.append(A(x, y4 + 28, 166, f'<img src="{IM(k)}" alt="{n} diagram, redrawn" style="display:block;width:166px;height:96px;object-fit:cover">'
                   + f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:10.5px;color:{INK};margin-top:5px">{n}</div>'
                   + P(a, 9, 1.3, MUTE) + P(l, 9.5, 1.3, INK, 'margin-top:3px') + P(f'<b style="color:#B4492B">→ {d}</b>', 9.5, 1.3, INK, 'margin-top:3px')))
    o.append(A(40, 1530, 1043, P('Sources: KAED IIUM BAAR 3101 brief + Site C SoA · Sinar Harian (6 Sep 2022) and Pahang State Govt (18 Jan 2024) on the JUPEM centre point · Al-Quran, Sahih International · Sahih al-Bukhari · Dezeen, Aga Khan Award for Architecture, WOHA (precedents) · distances and bearings calculated from 3.448° N, 102.423° E.', 8.5, 1.3, MUTE)))
    return ''.join(o)
