LEVCOL = {0: Color(0.97, 0.96, 0.93), 1: Color(0.93, 0.91, 0.86), 2: Color(0.90, 0.87, 0.81), 3: Color(0.87, 0.83, 0.76), 4: Color(0.80, 0.86, 0.74),
          5: Color(0.80, 0.75, 0.66), 6: Color(0.75, 0.69, 0.59), 7: Color(0.70, 0.63, 0.52), 8: Color(0.64, 0.56, 0.45), 9: Color(0.58, 0.49, 0.38)}
SITE_PAGES = {}
def cover():
    header('1:500 MOCK-UP MODEL KIT', 'SITE C, TEMERLOH · SIMPUL RASA SEMENANJUNG', 'READ FIRST')
    T(10, 270, 'TITIK TEMU', 30, 'LSB'); T(10, 261, 'MOCK-UP MODEL KIT · SCALE 1:500 · A4 TEMPLATES', 11, 'LSB', TERRA)
    para(10, 254, 120, 'Print every page at 100 % ("Actual size", not "Fit to page"). Trace or stick each template on the board and cut on the solid black line. 1 m on site = 2 mm on the model.', 7.5)
    c.drawImage('/home/claude/mock/out/hero.jpg', 10 * mm, 152 * mm, 120 * mm, 120 * 1326 / 1800 * mm)
    T(10, 148.5, 'WHAT YOU ARE BUILDING (DESIGN RENDER)', 5.8, 'LSB', MUTE)
    # right column facts
    rx = 138; y = 254
    T(rx, y, 'KEY NUMBERS', 8, 'LSB', TERRA); y -= 5
    for a_, b_ in [('SCALE', '1:500 · 1 M = 2 MM'), ('BASE BOARD', '300 × 264 MM'), ('SITE LAYERS', f'{NL} × GREYBOARD 2 MM'), ('1 LAYER', '= 1 M OF LEVEL'),
                   ('FOAM 5 MM', '= 2.5 M OF HEIGHT'), ('BUILDING', 'B1–B10 + CROWN + 4 RIBBONS'), ('CONTEXT', 'CX1–CX4'), ('TALLEST', 'CROWN 27 MM ABOVE SITE')]:
        T(rx, y, a_, 6.3, 'LSB'); T(rx + 22, y, b_, 6.3, 'LS', INK); y -= 4.2
    y -= 3; T(rx, y, 'YOU NEED', 8, 'LSB', TERRA); y -= 5
    y = para(rx, y, 62, '• Greyboard 2 mm: about 6 × A3 (L1–L5 each need a full A3; L6–L9 and the building fit in offcuts)\n• Foam board 5 mm: 1 × A3 (B2, B4 ×2, B6, B7 ×2, CX1–CX3)\n• Base board 300 × 264 mm (3 mm greyboard / MDF)\n• White card ≈1 mm (ribbons), red card (crown), tracing paper (oculus)\n• 20 polystyrene balls (12 × Ø12 mm, 8 × Ø10 mm), toothpicks\n• Cutter + new blades, steel ruler, cutting mat, compass cutter (rings)\n• Carbon paper or glue stick (to stick templates on), PVA / UHU glue, pins', 6.3, 1.3)
    # build order
    y0 = 140
    T(10, y0, 'BUILD ORDER', 9, 'LSB', TERRA)
    steps = [('1', 'CHECK THE PRINT', 'Measure the 50 mm bar on any page. If it is not 50 mm, reprint at 100 %.'),
             ('2', 'SITE LAYERS L1 → L9', 'Each layer has a WEST and an EAST half page. Tape the halves together on the shaded strip so the red R crosses sit on top of each other, then trace and cut one piece.'),
             ('3', 'STACK THE SITE', 'Glue L1 on the base board (outer edges flush). Glue each next layer inside the blue dashed line of the layer below. Pin-prick the R crosses through every layer to check alignment.'),
             ('4', 'DRAW ON THE SITE', 'On L4 draw the red site boundary, Jalan Ibrahim, paths and the podium outline. On L1–L3 draw Jalan Tok Muda Awang Ngah.'),
             ('5', 'CUT THE BUILDING', 'Sheets BLD-1 to BLD-3. Cut foam with a fresh blade in 2–3 light passes; use a compass cutter for the rings.'),
             ('6', 'ASSEMBLE THE BUILDING', 'Follow the ASSEMBLY sheet: B1 podium → rings → slab → east block → small ring L1 → core → oculus → crown.'),
             ('7', 'DETAILS + CONTEXT', 'Ribbons R1–R4 on toothpick posts, context blocks CX1–CX4, trees on the green circles.')]
    y = y0 - 7
    for n_, h_, b_ in steps:
        c.setFillColor(TERRA); c.circle(13 * mm, (y + 1) * mm, 2.6 * mm, stroke=0, fill=1); T(13, y - 0.1, n_, 7, 'LSB', white, 'c')
        T(18, y + 0.5, h_, 7, 'LSB'); y = para(18, y - 3.0, 180, b_, 6.6) - 2.2
    c.setFillColor(LIGHT); c.rect(10 * mm, (y - 15) * mm, 190 * mm, 13 * mm, stroke=0, fill=1)
    yy = para(13, y - 6, 184, 'ABOUT THE CONTOURS: there was no survey contour file for Site C, so the 9 site layers were traced from your 1:500 example model photo and fitted to the real site boundary. Treat levels as approximate (about ±2 m in plan, 1 m steps). If your lecturer gives survey levels, swap them in before cutting.', 6.3)
    checkbar(10, 14); T(200, 14, 'SHEETS: READ FIRST · SITE OVERVIEW · SITE L1–L9 · BLD-1 · BLD-2 · BLD-3 · ASSEMBLY', 5.8, 'LSB', INK, 'r')
    footer(); c.showPage()
def overview(pages):
    header('SITE LAYERS · OVERVIEW', 'NOT TO SCALE FOR CUTTING — 1:1000 (HALF SIZE)', 'SITE-0')
    M = Map(10, 128, XL, YB, 1.0)
    for k in range(0, NL + 1):
        g = BOARD if k == 0 else LAYERS[k]
        M.poly(g, INK, LEVCOL[k], 0.25)
    M.line(Polygon(SITE), RED, 0.3, ([1.6, 0.9], 0))
    M.poly(PODIUM, BLUE, Color(0.85, 0.9, 1.0), 0.35)
    for key in CX: M.poly(CX[key][1], MUTE, Color(1, 1, 1), 0.25)
    for f, L in zip(FACES, LEVELS):
        x, y = f.representative_point().coords[0]
        if f.area > 150: M.text(x, y, f'{L}', 7, INK)
    M.line(LineString([(53, YB), (53, YT)]), TERRA, 0.3, ([1, 1], 0)); M.line(LineString([(57, YB), (57, YT)]), TERRA, 0.3, ([1, 1], 0))
    M.text(18, YT + 2, 'WEST HALF PAGES', 5.5, TERRA); M.text(92, YT + 2, 'EAST HALF PAGES', 5.5, TERRA)
    north(167, 245, 1.2)
    T(10, 122, 'Numbers = how many greyboard layers are under that spot (0 = base board). Blue = building podium. White = context blocks.', 6.2)
    # table
    y = 112
    T(10, y, 'LAYER', 6.5, 'LSB'); T(26, y, 'LEVEL', 6.5, 'LSB'); T(42, y, 'TOP SURFACE SHOWS', 6.5, 'LSB'); T(120, y, 'SIZE (MM)', 6.5, 'LSB'); T(150, y, 'PAGES', 6.5, 'LSB')
    c.setStrokeColor(INK); c.setLineWidth(0.4); c.line(10 * mm, (y - 1.5) * mm, 200 * mm, (y - 1.5) * mm); y -= 5.5
    for k in range(NL, 0, -1):
        x0, y0, x1, y1 = LAYERS[k].bounds
        c.setFillColor(LEVCOL[k]); c.rect(10 * mm, (y - 1) * mm, 4 * mm, 3.4 * mm, stroke=0, fill=1)
        T(16, y, f'L{k}', 6.5, 'LSB'); T(26, y, LAYER_INFO[k][0], 6.3); T(42, y, LAYER_INFO[k][1], 6.3)
        T(120, y, f'{(x1 - x0) * 2:.0f} × {(y1 - y0) * 2:.0f}', 6.3); T(150, y, ', '.join(str(p) for p in pages.get(k, [])), 6.3)
        c.setStrokeColor(Color(0.8, 0.78, 0.74)); c.setLineWidth(0.2); c.line(10 * mm, (y - 1.6) * mm, 200 * mm, (y - 1.6) * mm); y -= 5.2
    T(16, y, 'BASE', 6.5, 'LSB'); T(26, y, '−4 M', 6.3); T(42, y, 'BASE BOARD 300 × 264 MM — RIVER SIDE STRIP EAST OF JALAN IBRAHIM', 6.3); y -= 8
    # stack diagram
    T(10, y, 'HOW THE LAYERS STACK (SIDE VIEW, NOT TO SCALE)', 6.5, 'LSB', TERRA); y -= 4
    for k in range(0, NL + 1):
        g = BOARD if k == 0 else LAYERS[k]; x0, _, x1, _ = g.bounds
        c.setFillColor(LEVCOL[k]); c.setStrokeColor(INK); c.setLineWidth(0.2)
        X0 = 10 + (x0 - XL) * 0.9; Wd = (x1 - x0) * 0.9
        c.rect(X0 * mm, (y - 20 + k * 2.0) * mm, Wd * mm, 2.0 * mm, stroke=1, fill=1)
        T(X0 + Wd + 1.5, y - 20 + k * 2.0 + 0.3, 'BASE' if k == 0 else f'L{k}', 4.8, 'LSB')
    para(155, y - 2, 45, 'Each layer is glued on the one below, with its outer edges flush with the board edge where it reaches it.', 6)
    para(155, y - 14, 45, 'SAVE BOARD: L1–L3 are mostly hidden under L4. You can cut out their middle, keeping a 20 mm rim plus every part that sticks out beyond L4.', 6, font='LSB', col=TERRA)
    footer(); c.showPage()
def assembly():
    header('BUILDING ASSEMBLY', 'STACK ORDER · HEIGHTS · WHERE EVERYTHING GOES', 'ASSEMBLY')
    # section along qibla axis, 1:333 (3 mm per m), u measured from B toward S
    k_ = 3.0; ox, oy = 10 + 22.6 * k_ + 5, 228
    def R(u0, u1, z0, z1, col, lab=None, tx=None):
        a, b = sorted((u0, u1)); c.setFillColor(col); c.setStrokeColor(INK); c.setLineWidth(0.25)
        c.rect((ox + a * k_) * mm, (oy + z0 * k_) * mm, (b - a) * k_ * mm, (z1 - z0) * k_ * mm, stroke=1, fill=1)
        if lab: T(ox + (tx if tx is not None else (a + b) / 2) * k_, oy + (z0 + z1) / 2 * k_ - 0.9, lab, 4.8, 'LSB', INK, 'c')
    FO = Color(1, 1, 1); GB = Color(0.80, 0.77, 0.70)
    c.setStrokeColor(INK); c.setLineWidth(0.6); c.line((ox - 22.6 * k_ - 4) * mm, oy * mm, (ox + 41 * k_) * mm, oy * mm)
    R(-22.6, 39.8, 0, 1, GB, 'B1 PODIUM · 2 MM')
    for sg in (-1, 1):
        R(sg * 11, sg * 18.1, 1, 3.5, FO, 'B2' if sg < 0 else None); R(sg * 11, sg * 18.1, 3.5, 4.5, GB)
        R(sg * 9, sg * 19.6, 4.5, 5.5, GB, 'B3' if sg < 0 else None)
    R(19.6, 23.72, 1, 3.5, FO); R(28.72, 36.82, 1, 3.5, FO, 'B6'); R(19.6, 23.72, 3.5, 5.5, GB); R(28.72, 36.82, 3.5, 5.5, GB)
    R(11, 23.72, 5.5, 8, FO); R(11, 23.72, 8, 10.5, FO, 'B7 ×2'); R(28.72, 36.82, 5.5, 8, FO); R(28.72, 36.82, 8, 10.5, FO)
    R(18.2, 22.6, 10.5, 11.5, GB, 'B8'); R(19.2, 21.6, 11.5, 12.5, GB)
    R(-21.5, -11, 5.5, 8, FO); R(-21.5, -11, 8, 10.5, FO, 'B4'); R(-21.5, -11, 10.5, 11.5, GB); R(-21.5, -9, 11.5, 12.5, GB, 'B5')
    c.setStrokeColor(BLUE); c.setLineWidth(0.8); c.line((ox - 9 * k_) * mm, (oy + 7.5 * k_) * mm, (ox - 4.5 * k_) * mm, (oy + 7.5 * k_) * mm); c.line((ox + 4.5 * k_) * mm, (oy + 7.5 * k_) * mm, (ox + 9 * k_) * mm, (oy + 7.5 * k_) * mm)
    T(ox, oy + 7.5 * k_ + 1.2, 'B10 OCULUS (ON 4 MM POSTS)', 4.8, 'LSB', BLUE, 'c')
    p = c.beginPath(); p.moveTo((ox + 12.5 * k_) * mm, (oy + 5.5 * k_) * mm); p.curveTo((ox + 14 * k_) * mm, (oy + 15 * k_) * mm, (ox + 22 * k_) * mm, (oy + 14.5 * k_) * mm, (ox + 26 * k_) * mm, (oy + 10.5 * k_) * mm)
    c.setStrokeColor(TERRA); c.setLineWidth(1.2); c.drawPath(p, stroke=1, fill=0); T(ox + 18 * k_, oy + 13.9 * k_, 'CR CROWN · TOP 27 MM', 4.8, 'LSB', TERRA, 'c')
    T(ox, oy - 3.5, 'B (BIG RING CENTRE)', 4.8, 'LSB', TERRA, 'c'); T(ox + 26.22 * k_, oy - 3.5, 'S (SMALL RING CENTRE)', 4.8, 'LSB', TERRA, 'c')
    for z_, lab in ((1, '2'), (5.5, '11'), (10.5, '21'), (12.5, '25'), (13.5, '27')):
        T(ox + 41 * k_ + 1, oy + z_ * k_ - 0.8, f'{lab} MM', 4.8, 'LS', MUTE)
    T(10, 275, 'SECTION ALONG THE QIBLA AXIS (S – B) · DRAWN 1.5× MODEL SIZE · WHITE = FOAM 5 MM, GREY = GREYBOARD 2 MM · HEIGHTS = MODEL MM ABOVE L4', 6, 'LSB')
    # assembly plan at 1:500
    T(10, 208, 'ASSEMBLY PLAN · TRUE 1:500 · LAY PIECES ON THIS TO CHECK', 6.5, 'LSB', TERRA)
    gx0, gy0, gx1, gy1 = PODIUM.bounds
    M = Map(10, 203 - (gy1 - gy0) * 2, gx0, gy0, 2.0)
    M.poly(PODIUM, INK, GREYF, 0.4)
    cols = {'B2': INK, 'B3': MUTE, 'B4': BLUE, 'B5': BLUE, 'B6': INK, 'B7': GREEN, 'B8': TERRA, 'B9': TERRA}
    for p_ in PIECES[1:9]:
        M.line(p_[2], cols.get(p_[0], INK), 0.35, ([1.4, 0.8], 0) if p_[0] in ('B3', 'B5', 'B7') else None)
    labs = {'B2': B + d(170) * 14.5, 'B3': B + d(200) * 19.0, 'B4': B + d(95) * 16, 'B5': B + d(95) * 20.3, 'B6': S + d(200) * 7, 'B7': S + d(20) * 7.5, 'B8': GM.CORE1_C + d(QIBLA) * 4}
    for k, p in labs.items(): M.text(p[0], p[1], k, 5.2, cols[k])
    for p, lab, on in crown_marks(): dot(M, p, lab, TERRA, 4.2)
    for i, p in enumerate(OCU_POSTS): dot(M, p, f'O{i + 1}', BLUE, 4)
    M.cross(*B, 2.0, 'B', TERRA); M.cross(*S, 2.0, 'S', TERRA); north(122, 196, 1.0)
    # steps
    sx, y = 138, 205
    T(sx, y, 'STEP BY STEP', 8, 'LSB', TERRA); y -= 5.5
    st = ['B1 podium on L4, inside the blue podium outline (B, S crosses on top of the L4 crosses).',
          'B2 foam, then B2 greyboard, centred on B. North up: the gaps face E (Timur), SSW (Selatan), WSW (Tengah).',
          'B6 foam + 2 × B6 greyboard around S, next to B2.',
          'B3 terrace slab on top of B2 (B on B). Its top must be level with the top of B6 (11 mm).',
          'B4 = foam + foam + greyboard on the east side of B3. B5 roof on top (overhangs into the court).',
          'B7 foam × 2 on B6 + the knot part of B3. Light-well holes line up with B6.',
          'B8 core on B7 (blue dashed rectangles on BLD-2), then B9 on the lift part.',
          'B10 oculus ring on 4 posts (4 mm toothpick) at O1–O4 on the B3 inner edge.',
          'Crown: bend CR-A and CR-B to the profile on BLD-3, glue the starts at CR marks on B3 and the ends on B7.',
          'Ribbons R1–R4 on their posts (heights on BLD-3); gate end touches the B3 / B4 edge.',
          'Trees on the green circles; CX blocks on their layers (CX1 on L9, CX2 + CX3 on L5, CX4 on L4).']
    for i, s_ in enumerate(st):
        T(sx, y, f'{i + 1}', 7, 'LSB', TERRA); y = para(sx + 5, y, 57, s_, 6.1, 1.28) - 1.6
    c.setFillColor(LIGHT); c.rect(10 * mm, 20 * mm, 120 * mm, 26 * mm, stroke=0, fill=1)
    T(13, 41.5, 'HEIGHT CHECK (MODEL MM ABOVE L4 = REAL M × 2)', 6.3, 'LSB', TERRA)
    rows = [('Podium B1', '2', '+0.9'), ('Terrace B3 / B6 top', '11', '+5.4'), ('Small ring B7 top', '21', '+10.5 parapet'), ('East roof B5 top', '25', '+11.2 → +12.9'),
            ('Lift overrun B9 top', '25', '+12.4'), ('Crown top', '27', '+13.5')]
    yy = 37.5
    for i, (a_, b_, c_) in enumerate(rows):
        xx = 13 + (i // 3) * 60; y2 = yy - (i % 3) * 4.6
        T(xx, y2, a_, 6, 'LSB'); T(xx + 33, y2, b_ + ' MM', 6, 'LS', INK); T(xx + 44, y2, c_, 5.6, 'LS', MUTE)
    checkbar(145, 18); footer(); c.showPage()
