QA = LineString([tuple(B + d(QIBLA) * 60), tuple(B - d(QIBLA) * 60)])
def crown_marks():
    out = []
    for cr, lab in zip(CROWN, ('A', 'B')):
        out.append((cr['P0'], f'CR-{lab}', 'B3')); out.append((cr['P2'], f'CR-{lab}', 'B7'))
    return out
OCU_POSTS = [tuple(B + d(b) * 9.4) for b in (25, 115, 205, 295)]
def piece_cell(pid, name, g, mats, x, y_top, note='', w=None, marks=True, extra=None, fill=GREYF):
    gx0, gy0, gx1, gy1 = g.bounds
    w = w or max((gx1 - gx0) * 2, 30)
    T(x, y_top, pid, 10, 'LSB', TERRA)
    yy = para(x, y_top - 4.0, w, name, 6.0, 1.25, 'LSB')
    yy = para(x, yy - 0.3, w, '  +  '.join(f'{m} × {q}' for m, q in mats), 5.8, 1.25, 'LSB', BLUE)
    if note: yy = para(x, yy - 0.2, w, note, 5.2, 1.25, 'LS', MUTE)
    yy -= 1.5
    M = Map(x, yy - (gy1 - gy0) * 2, gx0, gy0, 2.0)
    M.poly(g, INK, fill, 0.45)
    if marks:
        M.clip = g.buffer(0.01); M.line(QA, Color(0.45, 0.45, 0.45), 0.2, ([2.0, 0.8, 0.4, 0.8], 0)); M.clip = None
        for C_, lab in ((B, 'B'), (S, 'S')):
            if g.convex_hull.buffer(1).contains(Point(C_)): M.cross(*C_, 2.0, lab, TERRA)
    if extra: extra(M)
    return yy - (gy1 - gy0) * 2
def b3_extra(M):
    for p, lab, on in crown_marks():
        if on == 'B3': dot(M, p, lab)
    for i, p in enumerate(OCU_POSTS): dot(M, p, f'O{i + 1}', BLUE, 4.2)
    for r in RIBS:
        if P_['B3'][2].contains(Point(r['cl'][-1])): dot(M, r['cl'][-1], 'R-' + r['k'][:3], GREEN, 4.2)
def b7_extra(M):
    for p, lab, on in crown_marks():
        if on == 'B7': dot(M, p, lab)
    M.poly(PIECES[7][2], BLUE, None, 0.3, ([1, 0.8], 0))
    x, y = PIECES[7][2].centroid.coords[0]; M.text(x, y + 4.5, 'B8 CORE', 4.6, BLUE)
P_ = {p[0]: p for p in PIECES}
def cell(pid, x, y, **kw):
    p = P_[pid]; return piece_cell(pid, p[1], p[2], p[3], x, y, p[6], **kw)
def building_pages():
    header('BUILDING PIECES 1:500 · SHEET 1 OF 3', 'TRACE + CUT · NORTH IS UP ON EVERY PIECE', 'BLD-1')
    yb = cell('B1', 10, 278, w=120)
    yb6 = cell('B6', 143, 278, w=57)
    cell('B8', 143, yb6 - 8, w=26); cell('B9', 174, yb6 - 8, w=26)
    y2 = yb - 10
    cell('B2', 10, y2, w=76); cell('B3', 96, y2, w=80, extra=b3_extra)
    para(10, 24, 120, 'Dash-dot line = QIBLA AXIS (292.3°) through ring centres B and S. Push a pin through the B / S crosses to line the stack up. The 3 gaps in B2 are the open gates (Timur, Selatan, Tengah). Dots on B3 = where the crown starts (CR-A, CR-B) and the oculus posts (O1–O4) stand.', 5.8)
    checkbar(145, 18); footer(); c.showPage()
    header('BUILDING PIECES 1:500 · SHEET 2 OF 3', 'TRACE + CUT · NORTH IS UP ON EVERY PIECE', 'BLD-2')
    ya = min(cell('B4', 10, 278, w=34), cell('B5', 50, 278, w=36), cell('B7', 92, 278, w=58, extra=b7_extra))
    cell('B10', 156, 278, w=44, extra=lambda M: [dot(M, p, f'O{i + 1}', BLUE, 4.2) for i, p in enumerate(OCU_POSTS)])
    y2 = ya - 10
    for key, x, w in (('CX1', 10, 44), ('CX2', 60, 92), ('CX3', 160, 40)):
        nm, g, lv, mats, note = CX[key]
        piece_cell(key, nm, g, mats, x, y2, f'{note} · SITS ON L{lv}', w=w, marks=False, fill=Color(0.95, 0.95, 0.95))
    para(10, 24, 130, 'B7 sits on top of B6 and on the knot part of the terrace slab B3. B8 core goes on top of B7 where the blue dashed rectangles are. Context blocks (CX) are approximate massing only.', 5.8)
    checkbar(145, 18); footer(); c.showPage()
def crown_profile():
    cr = CROWN[0]; P = cr['pts'][:, :2]
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    t = np.linspace(0, 1, len(s)); z0, z1, z2 = 5.5, 13.5, 10.5
    z = np.where(t < 0.5, z0 + (z1 - z0) * np.sin(np.pi * t), z2 + (z1 - z2) * np.sin(np.pi * t))
    L = float(np.sum(np.hypot(np.diff(s), np.diff(z))))
    return s, z, L
def building_page3():
    header('BUILDING PIECES 1:500 · SHEET 3 OF 3', 'RIBBONS · CROWN · TENNIS COURT · TREES', 'BLD-3')
    nm, g, lv, mats, note = CX['CX4']
    ycx = piece_cell('CX4', nm, g, mats, 10, 278, f'{note} · SITS ON L{lv}', w=34, marks=False, fill=Color(0.95, 0.95, 0.95))
    R = {r['k']: r for r in RIBS}
    ylow = ycx
    for i, (k, x, ytop) in enumerate([('TENGAH', 50, 278), ('UTARA', 82, 278), ('TIMUR', 118, 278), ('SELATAN', 50, 205)]):
        r = R[k]; gx0, gy0, gx1, gy1 = r['poly'].bounds; w = max((gx1 - gx0) * 2, 26) + 4
        def ex(M, r=r):
            for tt, p, z in r['posts']: dot(M, p, f'{z * 2:.1f}', BLUE, 4.6)
            s_, e_ = r['cl'][0], r['cl'][-1]; dot(M, s_, 'ROAD END', MUTE, 4.2); dot(M, e_, 'GATE END', GREEN, 4.2)
        yb = piece_cell(f'R{i + 1}', f'RIBEN {k} · {r["w"]:.1f} M WIDE', r['poly'], [('WHITE CARD ≈1 MM', 1)], x, ytop,
                        f'3 POSTS · HEIGHTS IN MM ABOVE L4', w=w, marks=False, extra=ex, fill=Color(1, 1, 1))
        ylow = min(ylow, yb)
    y = ylow - 10
    # crown
    s, z, L = crown_profile()
    T(10, y, 'CR', 10, 'LSB', TERRA); T(19, y, 'SIMPUL CROWN · 2 STRIPS (CR-A + CR-B, MIRROR IMAGES)', 6.5, 'LSB')
    para(10, y - 4, 95, f'TERRACOTTA / RED CARD, 2 MM WIDE (= 1 M). CUT 2 STRIPS {L * 2:.0f} MM LONG + 2 MM GLUE TAB EACH END = {L * 2 + 4:.0f} MM.', 5.8, font='LSB', col=BLUE)
    para(10, y - 11, 95, 'Bend each strip to the true-size side profile below. Glue the start on the terrace slab B3 at CR-A / CR-B, the top passes over the lift core at +13.5 m, the end lands on the B7 roof at CR-A / CR-B.', 5.8)
    ox, oy = 14, y - 52
    c.setStrokeColor(MUTE); c.setLineWidth(0.25); c.line(ox * mm, oy * mm, (ox + s[-1] * 2 + 4) * mm, oy * mm)
    for lev, lab in ((5.5, 'B3 TOP +5.5'), (10.5, 'B7 TOP +10.5'), (13.5, 'TOP +13.5')):
        c.setDash(1 * mm, 1 * mm); c.line(ox * mm, (oy + lev * 2) * mm, (ox + s[-1] * 2 + 4) * mm, (oy + lev * 2) * mm); c.setDash([], 0)
        T(ox + s[-1] * 2 + 5, oy + lev * 2 - 0.8, lab, 4.8, 'LS', MUTE)
    p = c.beginPath(); p.moveTo(ox * mm, (oy + z[0] * 2) * mm)
    for a_, b_ in zip(s[1:], z[1:]): p.lineTo((ox + a_ * 2) * mm, (oy + b_ * 2) * mm)
    c.setStrokeColor(TERRA); c.setLineWidth(1.6); c.drawPath(p, stroke=1, fill=0)
    T(ox, oy - 3.5, 'SITE L4 (±0)  ·  TRUE-SIZE SIDE PROFILE 1:500', 5, 'LSB', MUTE)
    # strip template
    sy = oy - 12
    for i in range(2):
        c.setFillColor(Color(0.85, 0.45, 0.3)); c.setStrokeColor(INK); c.setLineWidth(0.3)
        c.rect(ox * mm, (sy - i * 5) * mm, (L * 2 + 4) * mm, 2 * mm, stroke=1, fill=1)
        T(ox + L * 2 + 6, sy - i * 5 + 0.3, f'CR-{"AB"[i]}  {L * 2 + 4:.0f} × 2 MM', 5.5, 'LSB')
        c.setDash(0.5 * mm, 0.5 * mm); c.line((ox + 2) * mm, (sy - i * 5) * mm, (ox + 2) * mm, (sy - i * 5 + 2) * mm); c.line((ox + L * 2 + 2) * mm, (sy - i * 5) * mm, (ox + L * 2 + 2) * mm, (sy - i * 5 + 2) * mm); c.setDash([], 0)
    # oculus posts + trees table on the right
    rx = 118
    T(rx, y, 'POSTS + TREES', 8, 'LSB', TERRA)
    rows = [('O1–O4', 'Oculus canopy posts', '4 × 4 mm', 'toothpick on B3 inner edge'),
            ('R1–R4', 'Ribbon posts', '3 per ribbon', 'heights printed on each ribbon'),
            ('T · 6 m', 'Trees, canopy 6 m', f'{sum(1 for t in SE.TREES if t[2] == 6)} × Ø12 mm ball', 'stem 6 mm'),
            ('T · 5 m', 'Trees, canopy 5 m', f'{sum(1 for t in SE.TREES if t[2] == 5) + 1} × Ø10 mm ball', 'stem 6 mm (1 in the court)')]
    yy = y - 6
    for a_, b_, c_, d_ in rows:
        T(rx, yy, a_, 6, 'LSB', BLUE); T(rx + 15, yy, b_, 6, 'LSB'); T(rx + 15, yy - 2.8, f'{c_} · {d_}', 5.5, 'LS', MUTE); yy -= 7.2
    para(rx, yy - 1, 82, 'Tree positions are the green circles on SITE L4. Polystyrene balls on cut toothpicks, like your example model.', 5.8)
    checkbar(145, 18); footer(); c.showPage()
