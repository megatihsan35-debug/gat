# -*- coding: utf-8 -*-
import json
from content import *
BADGE_BG = '#B4492B'
def badge(x, y, t, col=BADGE_BG):
    return (f'<div style="position:absolute;left:{x - 6.5:.1f}px;top:{y - 6.5:.1f}px;width:13px;height:13px;border-radius:7px;background:{col};border:1px solid #FFFFFF;'
            f'color:#FFFFFF;font-size:7.5px;font-weight:700;line-height:11px;text-align:center;font-family:DM Sans, Arial, sans-serif">{t}</div>')
GF_B = {'1': [(376.5, 361)], '2': [(550.5, 450)], '3': [(703.3, 521), (653.2, 547), (597.4, 562), (540, 557)], '4': [(567.1, 203), (624.6, 208), (677.8, 231), (718.8, 262)],
        '5': [(763.8, 495), (782.0, 433)], '6': [(447.1, 502), (408.8, 535)], '7': [(442.3, 237), (479.1, 208)], '8': [(509.3, 169), (525.4, 216)], '9': [(654.4, 338)],
        '10': [(285.7, 335), (196.3, 327)], '11': [(195.6, 157), (277.8, 149)], '12': [(344.0, 190), (134.3, 259), (131.0, 198)],
        'G': [(388.8, 464), (475.5, 558), (771.9, 304)]}
GF_K = [('1', 'Lobby Simpul 87'), ('2', 'Talam court (open)'), ('3', 'A1 shops 4 × 32'), ('4', 'A2 shops 4 × 32'), ('5', 'Café + servery, kitchen'),
        ('6', 'Info 14 + first aid 18'), ('7', 'WC male / female 23'), ('8', 'Nursing 11 + nappy 7'), ('9', 'Play corner 30'), ('10', 'Staff WC F / M 36'),
        ('11', 'Loading + refuse'), ('12', 'Stores + plant rooms'), ('G', 'Gates T · S · Ti')]
L1_B = {'1': [(410.7, 301.7)], '2': [(296.5, 291)], '3': [(335.5, 186), (289.6, 329.5)], '4': [(215.2, 342), (255.2, 345)], '5': [(141.4, 189.5)], '6': [(141.4, 295)],
        '7': [(195.3, 157), (271.4, 149)], '8': [(754, 243)], '9': [(815.7, 487)], '10': [(782.4, 284), (735.3, 480), (861.5, 358)], '11': [(744.8, 539), (723.1, 560)],
        '12': [(419, 519.6)], '13': [(581.9, 382.6)]}
L1_K = [('1', 'Lift lobby 25'), ('2', 'Admin reception 19'), ('3', 'Office + manager'), ('4', 'Meeting + pantry'), ('5', 'Male prayer 36 · qibla'),
        ('6', 'Female prayer 36'), ('7', 'Family + shoe foyer'), ('8', 'Gallery Peta Rasa 54'), ('9', 'Dapur Rewang hall 92'), ('10', 'Stores'),
        ('11', 'WC male / female 23'), ('12', 'Laluan Simpul walk'), ('13', 'Oculus Ø9 m, open')]
def plan(IM, key, x, y, w, h, badges, label, alt):
    o = [IMG(IM(key), x, y, w, h, alt, fit='fill')]
    sx, sy = w / 966.6, h / 795.6
    for t, pts in badges.items():
        for px, py in pts: o.append(badge(x + px * sx, y + py * sy, t, NAVY if t == 'G' else BADGE_BG))
    o.append(A(x + 6, y + 6, 260, f'<div style="display:inline-block;background:{INK};color:#FFFFFF;font-size:9px;font-weight:700;letter-spacing:0.1em;padding:3px 6px">{label}</div>'))
    return ''.join(o)
def keylist(items, x, y, w, cols=3):
    cells = ''.join(f'<div style="display:flex;gap:4px;align-items:flex-start;font-size:9px;line-height:1.3;white-space:nowrap"><span style="flex:0 0 13px;height:13px;border-radius:7px;background:{NAVY if n == "G" else BADGE_BG};color:#FFFFFF;font-size:7.5px;font-weight:700;line-height:13px;text-align:center">{n}</span><span>{t}</span></div>' for n, t in items)
    return A(x, y, w, f'<div style="display:grid;grid-template-columns:repeat({cols}, minmax(0, 1fr));column-gap:6px;row-gap:2px">{cells}</div>')
def build(IM):
    ex = json.load(open('/home/claude/boards/img/exaxo.json'))
    o = []
    # header strip
    o.append(IMG(IM('sky2'), 0, 0, 1123, 100, 'Mint grid sky strip with clouds, sun and gulls', fit='cover'))
    o.append(A(40, 22, 380, f'<div style="font-family:Syne, Arial, sans-serif;font-weight:800;font-size:34px;line-height:1;color:{INK}">TITIK TEMU</div>'
               + f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:13px;color:{TERRA};margin-top:5px">Simpul Rasa Semenanjung — the building</div>'))
    o.append(A(430, 26, 330, P('CRIT 1 · TASK 3A — SCHEMATIC BUILDING DESIGN', 9.5, 1.3, TERRA, 'letter-spacing:0.12em;font-weight:700')
                            + P('Megat Muhammad Ihsan bin Muhammad Noor · Section 8', 9.5, 1.35, INK, 'margin-top:3px')
                            + P('KAED IIUM · BAAR 3101 Architectural Design 5 · Nov 2026', 9.5, 1.35, MUTE)))
    o.append(A(40, 74, 120, f'<div style="display:inline-block;background:{INK};color:#F4F1EA;font-family:DM Sans, Arial, sans-serif;font-weight:700;font-size:10px;letter-spacing:0.14em;padding:4px 8px">BOARD 02 / 02</div>'))
    # ---------------- row A: exploded activity axo + brief + SoA
    yA = 112; EW, EH = 545, 422; k = EW / 640
    o.append(SH(40, yA, EW, '08', 'EXPLODED AXONOMETRIC', 'a day at Titik Temu · L1 lifted 18 m, roof 38 m', on=3))
    ex0, ey0 = 40, yA + 26
    o.append(IMG(IM('exaxo'), ex0, ey0, EW, EH, 'Exploded axonometric of Titik Temu split into three tinted bands: night over Gelung Kecil, day over the Talam court, Sunday over the hall; people on every floor', fit='fill'))
    caps = [('NIGHT', 'Isyak at the musolla; the knot glows; supper by the court.', True),
            ('DAY', 'Lunch at the Talam: 8 shops + café, 100 seats.', False),
            ('SUNDAY', 'Pekan Sehari + a cooking demo in the hall.', False)]
    sq = [3, 2, 1]
    for (bx0, bx1, kind), (t, b, dark), n in zip(ex['bands'], caps, sq):
        x = ex0 + bx0 * k + 5; w = (bx1 - bx0) * k - 10
        c = '#FFFFFF' if dark else INK
        o.append(A(x, ey0 + EH - 50, w, f'<div style="border:1px dashed {"rgba(255,255,255,0.85)" if dark else "#4C565A"};background:{"rgba(28,38,62,0.8)" if dark else "rgba(255,255,255,0.82)"};padding:4px 6px">'
                   + f'<div style="font-size:9px;font-weight:700;letter-spacing:0.1em;color:{c};white-space:nowrap">{SQ(n, "#FFFFFF" if dark else TERRA, 6)} {t}</div><div style="font-size:9px;line-height:1.28;color:{c};margin-top:2px">{b}</div></div>'))
    lab = [('roofhall', 'PV ribbon roof +11.2 → 12.9', 14, -16), ('roofsmall', 'Roof +9.9 · tanks + PV', -30, -30), ('musolla', 'Musolla on the qibla', -8, -34),
           ('terrace', 'Laluan Simpul roof walk', -40, -30), ('hall', 'Dapur Rewang hall', 18, -14), ('gallery', 'Gallery Peta Rasa', 20, -24)]
    lines = []
    for key, t, dx, dy in lab:
        ax, ay = ex['anchors'][key]; ax = ex0 + ax * k; ay = ey0 + ay * k
        tx, ty = ax + dx, ay + dy
        o.append(A(tx, ty - 8, 160, f'<span style="display:inline-block;background:rgba(255,255,255,0.9);border:1px solid #4C565A;font-size:8.5px;font-weight:700;padding:1px 4px;color:{INK};white-space:nowrap">{t}</span>'))
        lines.append((tx + 3, ty, ax, ay))
    o.append(LEADERS(1123, 1587, lines))
    # brief + SoA column
    cx, cw = 605, 478
    o.append(SH(cx, yA, cw, '09', 'INDIVIDUAL BRIEF', 'what Titik Temu is for', on=2))
    br = [('Purpose', 'Sell and celebrate the food of Temerloh and the 11 Peninsular states; one shared place where travellers, traders and residents meet.'),
          ('Users', '8 shop-lot traders + café · Pekan Sehari and car-boot traders · families, visitors, balik-kampung travellers · 20 staff.'),
          ('Building', '2 storeys + roof terrace · 1,548.8 m² enclosed (brief gross 1,525.6 m², +1.5 %) · 12.5 m steel span over the hall (medium span).'),
          ('Added (open, not GFA)', 'Serambi Tengah pop-up bays · Laluan Simpul roof walk + Taman Ulam planters · Dataran Temu plaza · 4 ribbon canopies.')]
    cards = ''.join(f'<div style="background:#FFFFFF;border:1px solid {RULE};padding:5px 7px"><div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:10px;color:{TERRA}">{h}</div>'
                    f'<div style="font-size:9.5px;line-height:1.3;color:{INK};margin-top:2px">{b}</div></div>' for h, b in br)
    o.append(A(cx, yA + 26, cw, f'<div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:6px">{cards}</div>'
               + P('<b>Culture exchange programme:</b> Jelajah Rasa 11 Negeri · Rumah Terbuka Semenanjung · Dapur Rewang cooking demos · Hentian Balik Kampung · Pekan Sehari + car boot · Peta Rasa gallery + Taman Ulam.', 9.5, 1.3, INK, 'margin-top:6px')))
    chips = [('1,548.8 m²', 'enclosed floor area'), ('0.29', 'plot ratio'), ('≈30 %', 'site coverage'), ('+13.5 m', 'top of the crown')]
    ch = ''.join(f'<div style="background:{INK};color:#F4F1EA;padding:4px 7px"><div style="font-family:DM Sans, Arial, sans-serif;font-weight:700;font-size:14px;line-height:1.15;white-space:nowrap">{a}</div><div style="font-size:8.5px;color:#D5D9D6;white-space:nowrap">{b}</div></div>' for a, b in chips)
    o.append(A(cx, yA + 194, cw, f'<div style="display:grid;grid-template-columns:repeat(4, minmax(0, 1fr));gap:6px">{ch}</div>'))
    yS = yA + 236
    o.append(SH(cx, yS, cw, '10', 'SCHEDULE OF ACCOMMODATION', 'drawn plans vs Site C brief (m²)', on=3))
    soa = [('A', 'Retail: 8 shop lots + café', '306', '403.9', '324.5', 'GF'), ('B', 'Gallery + MPH (court dining B3 open)', '317', '418.4', '224.3', 'L1'),
           ('C', 'Management / admin + first aid', '118', '142.8', '137.5', 'L1 / GF'), ('D', 'Lobby, musolla, toilets', '295', '340.7', '436.4', 'GF / L1'),
           ('E', 'Services / utilities', '182', '219.8', '191.7', 'GF'), ('', 'Cores, stairs, lifts, corridors', '–', 'in %', '234.3', 'both')]
    th = ''.join(f'<th style="text-align:{al};font-weight:700;padding:3px 4px;border-bottom:1.5px solid {INK};white-space:nowrap">{h}</th>' for h, al in
                 [('', 'left'), ('Category', 'left'), ('SoA net', 'right'), ('SoA gross', 'right'), ('Drawn', 'right'), ('Level', 'left')])
    tr = ''.join(f'<tr style="border-bottom:1px solid {RULE}"><td style="padding:3px 4px;font-weight:700;color:{TERRA}">{a}</td><td style="padding:3px 4px">{b}</td>'
                 f'<td style="padding:3px 4px;text-align:right">{c}</td><td style="padding:3px 4px;text-align:right">{d}</td><td style="padding:3px 4px;text-align:right;font-weight:700">{e}</td><td style="padding:3px 4px">{f}</td></tr>' for a, b, c, d, e, f in soa)
    tr += (f'<tr style="border-top:1.5px solid {INK};background:#EFE8DA"><td></td><td style="padding:4px 4px;font-weight:700">Total enclosed</td><td style="padding:4px 4px;text-align:right;font-weight:700">1,218</td>'
           f'<td style="padding:4px 4px;text-align:right;font-weight:700">1,525.6</td><td style="padding:4px 4px;text-align:right;font-weight:700;color:{TERRA}">1,548.8</td><td style="padding:4px 4px;font-weight:700">+1.5 %</td></tr>')
    o.append(A(cx, yS + 26, cw, f'<table style="border-collapse:collapse;width:100%;font-size:9.5px;line-height:1.2;color:{INK}"><tr>{th}</tr>{tr}</table>'
               + P('Every room meets or beats its SoA net size. GF ≈866 m² + L1 ≈683 m². Open verandah + L1 balcony ≈163 m² not counted. Circulation ≈28 % (brief 25–30 %). D is higher because the lobby is generous and toilets fit PwD cubicles; B is lower because the 145 m² dining + play sits in the open court.', 9, 1.3, MUTE, 'margin-top:5px')))
    # ---------------- row B: plans
    yB = 572; PW, PH = 400, 329
    o.append(SH(40, yB, 1043, '11', 'FLOOR PLANS + ROOF', '1:200 @ A1, reduced · areas in m²', on=2))
    o.append(plan(IM, 'gf', 40, yB + 26, PW, PH, GF_B, 'GROUND FLOOR · FFL +0.900', 'Ground floor plan: shop lots and café around the Talam court, lobby and core at the knot, services in Gelung Kecil'))
    o.append(plan(IM, 'l1', 452, yB + 26, PW, PH, L1_B, 'FIRST FLOOR · FFL +5.400', 'First floor plan: gallery and Dapur Rewang hall to the east, admin and musolla in Gelung Kecil, roof walk around the court'))
    o.append(keylist(GF_K, 40, yB + 26 + PH + 6, PW, 3))
    o.append(keylist(L1_K, 452, yB + 26 + PH + 6, PW, 3))
    o.append(IMG(IM('roof'), 864, yB + 26, 219, 180, 'Roof plan: PV on the ribbon roof and small ring, terrace walk, oculus canopy over the court, crown over the core', fit='cover'))
    o.append(A(870, yB + 32, 200, f'<div style="display:inline-block;background:{INK};color:#FFFFFF;font-size:9px;font-weight:700;letter-spacing:0.1em;padding:3px 6px">ROOF PLAN</div>'))
    zones = [('#F6D9A0', 'Public'), ('#CFE3B8', 'Semi-public'), ('#BFD8EC', 'Private / admin'), ('#D9D0EC', 'Service'), ('#ECECEC', 'Circulation / core')]
    zl = ''.join(f'<div style="display:flex;align-items:center;gap:6px;font-size:9px;margin-bottom:3px"><span style="width:14px;height:10px;background:{c};border:1px solid #8A8F93"></span>{t}</div>' for c, t in zones)
    o.append(A(864, yB + 214, 219, f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:9.5px;color:{TERRA};margin-bottom:4px">ZONES ON THE PLANS</div>' + zl
               + P('Circles = grid lines 1–10 (big ring) and C–G (small ring). Red dots = section cuts A–A, B–B.', 9, 1.3, MUTE, 'margin-top:4px')))
    # ---------------- row C: sections + elevations
    yC = 1014
    o.append(SH(40, yC, 1043, '12', 'SECTIONS + ELEVATIONS', '1:200 @ A1, reduced · ±0.000 ground · +0.900 GF · +5.400 L1 · +9.900 roof · +11.200 → +12.900 ribbon roof · +13.500 crown', on=1))
    sw = 515
    def drw(key, x, y, w, h, t, alt):
        return IMG(IM(key), x, y + 13, w, h, alt, fit='contain') + A(x, y, w, f'<div style="font-size:8.5px;font-weight:700;letter-spacing:0.08em;color:{INK}">{t}</div>')
    o.append(drw('secA', 40, yC + 26, sw, 116, 'SECTION A–A · qibla axis: Gelung Kecil – core – court – hall', 'Section A-A along the qibla axis'))
    o.append(drw('secB', 568, yC + 26, sw, 116, 'SECTION B–B · north–south through the Talam court', 'Section B-B through the court'))
    o.append(drw('elS', 40, yC + 160, sw, 86, 'SOUTH ELEVATION · Jalan Tok Muda Awang Ngah', 'South elevation'))
    o.append(drw('elE', 568, yC + 160, sw, 86, 'EAST ELEVATION · Dataran Temu / river side', 'East elevation'))
    # ---------------- row D: perspectives + technical
    yD = 1290
    o.append(SH(40, yD, 515, '13', 'PERSPECTIVES', 'interior + exterior sketches', on=2))
    ints = [('i_court', 'Talam court · Pahang hosts'), ('i_lobby', 'Lobby Simpul · Perlis'), ('i_hall', 'Dapur Rewang hall · Kedah'), ('i_gate', 'Gerbang Selatan · N. Sembilan')]
    for i, (kk, t) in enumerate(ints):
        x = 40 + (i % 2) * 262; y = yD + 26 + (i // 2) * 117
        o.append(IMG(IM(kk), x, y, 253, 111, t, fit='cover'))
    o.append(SH(568, yD, 515, '14', 'TECHNICAL STUDY', 'structure + services', on=3))
    o.append(IMG(IM('struct'), 568, yD + 26, 160, 115, 'Structure diagram: radial RC frames, core, 12.5 m steel trusses over the hall, 3.4 m L1 oversail', fit='contain', st='background:#FBFAF7;border:1px solid #E2DDD2'))
    o.append(IMG(IM('serv'), 568, yD + 147, 160, 115, 'Services diagram: water, sewer, rainwater, fire, electrical and ACMV routes', fit='contain', st='background:#FBFAF7;border:1px solid #E2DDD2'))
    st_ = ['Radial RC frame: big ring 10 grids @36° (9.0 m span), small ring 8 grids @45° (8.1 m).',
           'RC core walls give stability; movement joint between the two rings.',
           '<b>Medium span:</b> 12.5 m steel ribbon trusses over the hall.',
           '3.4 m L1 oversail on RC cantilevers; lamellas hang on steel rails.',
           'Bored piles (confirm by SI) · IBS precast columns + hollow-core slabs.']
    sv = [('#3B87A8', 'Water: suction tank + pumps → roof tanks on Gelung Kecil → risers.'),
          ('#7A4B2A', 'Sewer: grease trap at the café → manholes → municipal sewer.'),
          ('#4E9A4E', 'Rainwater tank for WCs + planters; overflow to a bioswale.'),
          ('#C8372D', 'Fire: hose reels at both cores, roof fire tank, breeching inlet at the road.'),
          ('#E0A02A', 'Electrical: TNB → MDB + genset → risers; PV on both roofs.'),
          ('#6C5BA8', 'ACMV: split / VRF for admin, gallery, hall; court cooled by stack effect.')]
    li = lambda xs: ''.join(f'<div style="font-size:8.8px;line-height:1.25;color:{INK};padding-left:7px;text-indent:-7px;margin-bottom:2px">· {t}</div>' for t in xs)
    o.append(A(738, yD + 26, 345, f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:9.5px;color:{TERRA};margin-bottom:2px">STRUCTURE</div>' + li(st_)))
    lic = ''.join(f'<div style="display:flex;gap:6px;align-items:center;font-size:8.8px;line-height:1.25;color:{INK};margin-bottom:2px"><span style="flex:0 0 14px;height:3px;background:{c}"></span><span>{t}</span></div>' for c, t in sv)
    o.append(A(738, yD + 147, 345, f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:9.5px;color:{TERRA};margin-bottom:2px">SERVICES</div>' + lic))
    return ''.join(o)
