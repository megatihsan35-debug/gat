"""Interior layers for the 3D model (same geometry rules as interior.py / interior_sheets.py, approved study 16 Nov 2026).
Each layer becomes one SketchUp tag: I-FURN, I-KIT (shopfront kit), I-STATE-<KEY> (screens, back walls, signature displays,
accent pieces in that state's colour), I-BRASS (inlays), I-SIGN, I-TACTILE, I-CEIL (arcade baffles, tenun lining),
I-RIVER (court floor bands), I-MARKET (Gerai Lipat, market days), I-PRAYER (girih screens, mihrab), I-GALLERY."""
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
import plan3 as M
from plan3 import C, P, d, tdir, SC, ROOMS, FFL, CORES, QIBLA
import rings as RG
import landscape as LS
import plans
from plans import Wall
import interior as IN
from interior import ST, SHOP, tint, room, store_r, arc_band

MAT_I = {'I-FURN': ('#F1EEE8', 1.0), 'I-FURN-TIMBER': ('#9C6B3F', 1.0), 'I-KIT': ('#D7DBDF', 1.0), 'I-FASCIA': ('#3B3330', 1.0),
         'I-BRASS': ('#B08D3C', 1.0), 'I-SIGN': ('#3B3330', 1.0), 'I-TACTILE': ('#E3B505', 1.0), 'I-CEIL': ('#F4F4F2', 1.0),
         'I-TENUN': ('#CBB98C', 0.85), 'I-RIVER': ('#4F98BE', 1.0), 'I-RIVER2': ('#9CCDE3', 1.0), 'I-MARKET': ('#F6EBD2', 1.0),
         'I-PRAYER': ('#D8C38A', 1.0), 'I-GALLERY': ('#B9ACE0', 1.0), 'I-STEEL': ('#C9CED3', 1.0)}
for k, v in ST.items(): MAT_I[f'I-STATE-{k}'] = (v[4], 1.0)

def _flat(poly, z0, z1):
    out = []
    for q in getattr(poly, 'geoms', [poly]):
        if q.is_empty or q.geom_type != 'Polygon' or q.area < 1e-6: continue
        try:
            m = trimesh.creation.extrude_polygon(q.buffer(0), z1 - z0); m.apply_translation((0, 0, z0)); out.append(m)
        except Exception:
            pass
    return out
def _cyl(p, r, z0, z1, n=16):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n); m.apply_translation((p[0], p[1], (z0 + z1) / 2)); return [m]
def _rect(c, u, v, a, b):
    c, u, v = np.array(c), np.array(u), np.array(v)
    return Polygon([c - u * a - v * b, c + u * a - v * b, c + u * a + v * b, c - u * a + v * b])
def _vplate(p0, p1, z0, z1, t=0.03):
    """vertical plate from plan point p0 to p1"""
    return _flat(LineString([p0, p1]).buffer(t / 2, cap_style=2), z0, z1)

RENDER = False            # render_model.py sets this: seats + products become component instances, screens / back walls get their own textured layers
SEATS = []                # (component, (x, y), heading (x, y), z)
def seat(kind, p, h, z):
    h = np.array(h, float); h = h / (np.linalg.norm(h) + 1e-9); SEATS.append((kind, (float(p[0]), float(p[1])), (float(h[0]), float(h[1])), float(z)))

def add_interior(L):
    for k in MAT_I: L.setdefault(k, [])
    a = lambda k, ms: L.setdefault(k, []).extend(ms)
    G = FFL['GF']; L1 = FFL['L1']; L2 = FFL['L2']
    # ================================================================ GF shops: kit + unique layer
    for key, sk in SHOP.items():
        r = room(key); bm, b0, b1 = M.mid(key); rr = store_r(r); lay = f'I-STATE-{sk}'
        e = math.degrees(0.07 / 12.5)
        # screen band (front, 3.3-3.9 above FFL) and fascia band (2.7-3.3), half-piers
        a(f'I-SCREEN-{sk}' if RENDER else lay, _flat(arc_band(M.R_BR1 - 0.14, M.R_BR1 - 0.11, b0 + e, b1 - e, 12), G + 3.3, G + 3.9))
        a('I-FASCIA', _flat(arc_band(M.R_BR1 - 0.15, M.R_BR1, b0 + e, b1 - e, 12), G + 2.7, G + 3.3))
        for bb in (b0 + e * 0.5, b1 - e * 0.5): a('I-KIT', _flat(Point(P(M.R_BR1 - 0.03, bb)).buffer(0.04, 6), G, G + 3.9))
        # threshold, blade sign (acw pier, projecting into the arcade)
        a('I-BRASS', _flat(arc_band(M.R_BR1 - 0.3, M.R_BR1, b0 + e, b1 - e, 12), G, G + 0.008))
        pb = P(M.R_BR1, b0 + math.degrees(0.12 / 12.5)); a('I-SIGN', _flat(LineString([pb, pb - d(bm) * 0.6]).buffer(0.02, cap_style=2), G + 2.4, G + 2.7))
        # display case behind the fixed pane, side display counter, prep + cashier
        F = Wall(r, 'acw'); W_ = 2 * M.R_BR1 * math.sin(math.radians((b1 - b0) / 2)); fixed = W_ - 0.125 - 0.1 - 1.0
        a('I-FURN', _flat(F.rect(M.R_BR1 + 0.08, M.R_BR1 + 0.62, 0.05, fixed - 0.05), G, G + 0.9))
        rs = [plans.rad(c) for c in r['poly'].exterior.coords]; r0 = min(rs)
        a('I-FURN', _flat(F.rect(r0 + 0.9, r0 + 3.6, 0.0, 0.55), G, G + 0.9))
        Fc = Wall(r, 'cw'); a('I-FURN', _flat(Fc.rect(rr - 2.6, rr - 0.25, 0.0, 0.6), G, G + 0.9)); a('I-FURN', _flat(Fc.rect(r0 + 0.9, r0 + 3.0, 0.0, 0.45), G, G + 2.1))
        # feature back wall (store partition) full height to the rooflight of light band 2
        a(f'I-BACK-{sk}' if RENDER else lay, _flat(arc_band(rr - 0.12, rr - 0.06, b0 + e, b1 - e, 12), G, 5.25))
        if RENDER:                                                                                          # products on the side display counter
            for i, s_ in enumerate(np.arange(r0 + 1.1, r0 + 3.5, 0.3)):
                for q_ in (0.15, 0.4): seat('jar' if (i + int(q_ * 10)) % 2 else 'pack', F.W(s_, q_), d(bm), G + 0.9)
        # signature display under light band 1
        c = P(16.25, bm)
        if sk == 'PRK':
            for dx, dy in ((0, 0), (0.35, 1.2), (-0.35, -1.2), (0.3, -1.1)):
                q = P(16.25 + dx, bm + dy); s = trimesh.creation.icosphere(subdivisions=2, radius=0.16); s.apply_scale((1, 1, 1.3)); s.apply_translation((q[0], q[1], G + 2.6)); a(lay, [s])
                a('I-STEEL', _cyl(q, 0.006, G + 2.8, 5.27, 4))
            a('I-FURN', _flat(_rect(c, tdir(bm), d(bm), 0.6, 0.4), G, G + 0.85))
        elif sk == 'MLK':
            for i, (rad_, h) in enumerate(((0.45, 0.35), (0.33, 0.35), (0.2, 0.3))): a(lay if i % 2 == 0 else 'I-FURN', _cyl(c, rad_, G + 0.35 * i, G + 0.35 * i + h, 20))
        elif sk == 'KDH':
            for o in (-1.6, 0, 1.6): a(lay, _cyl(P(16.25, bm + o), 0.28, G, G + 0.8, 20))
        elif sk == 'PNG':
            from shapely import affinity
            el = affinity.rotate(affinity.scale(Point(c).buffer(0.5), 1.0, 0.6), -bm, origin=tuple(c)); a(lay, _flat(el, G, G + 0.95))
        elif sk == 'JHR':
            a('I-FURN', _flat(_rect(c, tdir(bm), d(bm), 0.6, 0.4), G, G + 0.85))
            g = _rect(c, tdir(bm), d(bm), 0.9, 0.7); a(lay, _flat(g.difference(g.buffer(-0.05)), G + 2.9, G + 3.0))
        elif sk == 'NSN':
            a('I-FURN', _flat(_rect(c, tdir(bm), d(bm), 0.6, 0.4), G, G + 0.85))
            for o in np.linspace(-0.45, 0.45, 6): a('I-FURN-TIMBER', _cyl(c + tdir(bm) * o, 0.045, G + 0.85, G + 1.6, 10))
            a(lay, _flat(_rect(c, tdir(bm), d(bm), 0.75, 0.5), G + 2.2, G + 2.28))
        else:
            a('I-FURN', _flat(_rect(c, tdir(bm), d(bm), 0.6, 0.4), G, G + 0.85)); a(lay, _flat(_rect(c, tdir(bm), d(bm), 0.62, 0.42), G + 0.85, G + 0.9))
    # ================================================================ GF cafe (Kelantan)
    r = room('G31'); bm, b0, b1 = M.mid('G31'); F = Wall(r, 'acw'); kel = 'I-STATE-KEL'
    a(kel, _flat(F.rect(17.2, 21.3, 0.0, 0.75), G, G + 1.05))
    cc = F.W(19.25, 1.7); ring_ = Point(cc).buffer(1.2).difference(Point(cc + np.array(F.eq) * 0.35).buffer(1.05)); a(kel, _flat(ring_, G + 3.0, G + 3.06))
    bt0, bt1 = b0 + 4.2, b1 - 1.2
    a('I-FURN-TIMBER', _flat(arc_band(20.45, 21.05, bt0, bt1), G + 0.72, G + 0.76)); a('I-FURN', _flat(arc_band(20.6, 20.9, bt0 + 0.5, bt1 - 0.5), G, G + 0.72))
    for rr_ in (20.05, 21.45): a('I-FURN-TIMBER', _flat(arc_band(rr_ - 0.18, rr_ + 0.18, bt0, bt1), G, G + 0.45))
    for o in (0.35, 0.6):
        b = b0 + (b1 - b0) * o + 1.5; q = P(22.25, b)
        if RENDER:
            seat('table_cafe', q, d(b), G)
            for s in (-1, 1): seat('chair', q + tdir(b) * 0.6 * s, -tdir(b) * s, G)
            continue
        a('I-FURN', _cyl(q, 0.33, G + 0.72, G + 0.75, 20) + _cyl(q, 0.05, G, G + 0.72, 8))
        for s in (-1, 1): a('I-FURN', _cyl(q + tdir(b) * 0.6 * s, 0.2, G, G + 0.45, 12))
    Gw = Wall(r, 'cw'); a('I-FURN-TIMBER', _flat(Gw.rect(20.3, 22.7, 0.0, 0.32), G + 1.02, G + 1.07))
    for s in np.arange(20.6, 22.6, 0.55):
        if RENDER: seat('stool_bar', Gw.W(s, 0.55), -np.array(Gw.eq), G)
        else: a('I-FURN', _cyl(Gw.W(s, 0.55), 0.17, G, G + 0.75, 10))
    bm3, a3, c3 = M.mid('G33'); a('I-FURN', _flat(arc_band(20.25, 20.85, a3 + 2.0, c3 - 2.0), G, G + 0.85))
    # ================================================================ GF info, first aid, nursing
    r = room('G20'); bm, b0, b1 = M.mid('G20'); F = Wall(r, 'acw')
    a('I-STATE-PHG', _flat(F.rect(15.0, 17.4, 0.0, 0.6), G, G + 1.05)); a('I-STATE-PHG', _flat(F.rect(15.0, 15.9, -0.55, -0.2), G, G + 0.75))
    r = room('G21'); Gw = Wall(r, 'cw'); a('I-FURN', _flat(Gw.rect(16.0, 17.9, 0.0, 0.7), G, G + 0.6)); a('I-FURN', _flat(Gw.rect(19.5, 20.7, 0.0, 0.5), G, G + 2.0))
    bmN = M.mid('G03')[0]; a('I-STATE-PHG', _cyl(P(17.2, bmN - 1.5), 0.42, G, G + 0.45, 16))
    # ================================================================ court + arcade + gates (host: Pahang)
    for b, col, sg in ((27.9, 'I-RIVER', 1), (242.8, 'I-RIVER2', -1)):
        t = np.linspace(0, 1, 40); rr_ = 11.0 - (11.0 - M.R_POOL - 0.1) * t; bb = b + 55 * t * sg
        a(col, _flat(LineString([P(x, y) for x, y in zip(rr_, bb)]).buffer(0.32), G, G + 0.006))
    a('I-BRASS', _flat(SC.ann(9.37, 9.43), G, G + 0.008))
    a('I-BRASS', _flat(LineString([P(8.8, QIBLA), P(9.9, QIBLA)]).buffer(0.04, cap_style=2), G, G + 0.01))
    for bb in np.arange(0, 360, 1.5):                                                                   # arcade baffles
        a('I-CEIL', _flat(LineString([P(9.6, bb), P(12.4, bb)]).buffer(0.015, cap_style=2), 4.62, 4.8))
    lin = SC.ann(1.7, 9.4)                                                                              # tenun lining under the funnel over the court
    from model3d import draped
    a('I-TENUN', draped(lin, lambda x, y: RG.fun_under((x, y)) - 0.1, lambda x, y: RG.fun_under((x, y)) - 0.12, cell=(4.0, 1.0)))
    # tactile path: arcade ring + gate axes + spurs
    tac = [SC.ann(11.6, 11.9)]
    for s in SC.SPINES:
        cn = [k for k in LS.CANOPIES if abs(k['b'] - s['b']) < 1][0]
        tac.append(LineString([P(11.75, s['b']), P(min(cn['R_out'], 29.0) - 0.5, s['b'])]).buffer(0.15, cap_style=2))
    tac.append(LineString([P(16.2, b_) for b_ in np.linspace(182.7, 200.6, 12)]).buffer(0.15, cap_style=2))
    for dd in M.CORE_DOORS:
        if dd['fl'] == 'GF' and dd['kind'] == 'lift': p = np.array(dd['p']); tac.append(LineString([P(11.75, plans.brg(p)), p + np.array(dd['n']) * 0.3]).buffer(0.15, cap_style=2))
    for k in ('G01', 'G02'): bm = M.mid(k)[0]; tac.append(LineString([P(11.75, bm), P(M.R_BR1 - 0.2, bm)]).buffer(0.15, cap_style=2))
    tz = lambda x, y: plans_ground(x, y) + 0.006
    a('I-TACTILE', draped(unary_union(tac).intersection(SC.disc(30)), tz, lambda x, y: tz(x, y) - 0.008, cell=(6.0, 3.0)))
    for s in SC.SPINES:
        b = s['b']; sts = IN.GATE_ST[s['k']]; w = s['w'] - 1.0; n = len(sts)
        for i, sk in enumerate(sts):
            u0 = -w / 2 + i * w / n; u1 = u0 + w / n
            a(f'I-STATE-{sk}', _flat(Polygon([P(13.6, b) + tdir(b) * u0, P(13.6, b) + tdir(b) * u1, P(14.2, b) + tdir(b) * u1, P(14.2, b) + tdir(b) * u0]), G, G + 0.008))
        tp = P(14.9, b) + tdir(b) * (s['w'] / 2 - 0.9)                                                  # directory totem
        a('I-SIGN', _flat(_rect(tp, d(b), tdir(b), 0.06, 0.3), G, G + 2.2))
        cn = [k for k in LS.CANOPIES if abs(k['b'] - s['b']) < 1][0]                                     # gate marker under the canopy end
        Rm = min(cn['R_out'], 29.0) - 0.4; zt = LS.z_top(cn, Rm, 0.0)
        a('I-SIGN', _flat(_rect(P(Rm, b), d(b), tdir(b), 0.05, 3.0), zt - 1.2, zt - 0.3))
    a('I-SIGN', _flat(_rect(P(16.2, 200.0), d(200.0), tdir(200.0), 0.06, 0.3), G, G + 2.2))            # totem at the Kaunter Info
    for dd in M.CORE_DOORS:                                                                             # level signs on the core walls
        p = IN.level_sign_point(dd) - np.array(dd['n']) * 0.37; t = np.array(dd['t'])
        a('I-SIGN', _flat(_rect(p, t, dd['n'], 0.6, 0.02), FFL[dd['fl']] + 0.6, FFL[dd['fl']] + 2.2))
    # ================================================================ L1
    for k, (nm, cap, b, km, col) in ST.items():                                                        # bridge brass state lines
        a('I-BRASS', _flat(LineString([P(RG.R_BG0 + 0.05, b), P(RG.R_BG1 - 0.05, b)]).buffer(0.012, cap_style=2), L1, L1 + 0.008))
    for b0_, b1_ in ((133.5, 180.0), (185.0, 238.0), (247.5, 271.5)):                                 # Anjung Talam ledge + stools
        a('I-FURN-TIMBER', _flat(arc_band(11.2, 11.55, b0_, b1_), L1 + 1.0, L1 + 1.05)); a('I-STEEL', _flat(arc_band(11.33, 11.42, b0_, b1_), L1, L1 + 1.0))
        for bb in np.arange(b0_ + 1.5, b1_ - 1.0, 2.8):
            if RENDER: seat('stool_bar', P(11.85, bb), -d(bb), L1)
            else: a('I-FURN', _cyl(P(11.85, bb), 0.17, L1, L1 + 0.75, 12))
    deck = [g for g in M.decks('L1') if min(plans.rad(c) for c in g.exterior.coords) > 20 and g.area > 200][0]
    b = 146.5                                                                                           # Gerai Lipat (market days)
    while b < 324:
        p = P(22.6, b); t = tdir(b); v = d(b); sq = Polygon([p - t - v, p + t - v, p + t + v, p - t + v])
        clear = all(abs(((b - s['b'] + 180) % 360) - 180) > math.degrees(3.4 / 22.6) for s in SC.SPINES)
        if deck.buffer(-0.02).contains(sq) and clear:
            for cx in (p - t * 0.95 - v * 0.95, p + t * 0.95 - v * 0.95, p + t * 0.95 + v * 0.95, p - t * 0.95 + v * 0.95): a('I-STEEL', _cyl(cx, 0.025, L1, L1 + 2.3, 6))
            a('I-MARKET', _flat(sq, L1 + 2.3, L1 + 2.34)); a('I-MARKET', _flat(_rect(p + v * 0.45, t, v, 0.9, 0.35), L1, L1 + 0.85))
            b += math.degrees(2.4 / 22.6)
        else: b += 0.5
    for bb in (20.5, 27.0, 59.0, 66.0): a('I-FURN-TIMBER', _flat(arc_band(24.3, 24.75, bb, bb + 4.0), L1, L1 + 0.45))
    r = room('L12'); bm, b0, b1 = M.mid('L12')                                                         # Dapur Rewang
    for o in (0.2, 0.4, 0.6, 0.8):
        bb = b0 + (b1 - b0) * o; a('I-STEEL', _flat(_rect(P(23.4, bb), tdir(bb), d(bb), 0.9, 0.45), L1, L1 + 0.9))
    Gw = Wall(r, 'cw'); a('I-FURN-TIMBER', _flat(Gw.rect(21.8, 24.6, 0.0, 0.45), L1, L1 + 2.4))
    for bb in np.linspace(b0 + 2, b1 - 2, 9):                                                          # anyaman acoustic baffles
        zb = min(RG.out_under(P(24, bb)) - 0.6, L1 + 3.6); a('I-FURN-TIMBER', _flat(arc_band(21.7, 26.3, bb - 0.4, bb + 0.4, 10), zb, zb + 0.05))
    r = room('L21'); bm, b0, b1 = M.mid('L21'); a('I-STATE-PLS', _flat(arc_band(23.9, 24.5, b0 + 1.2, b1 - 1.4), L1, L1 + 1.05))
    r = room('L24'); bm, b0, b1 = M.mid('L24')
    for o in np.linspace(0.12, 0.88, 5):
        bb = b0 + (b1 - b0) * o; a('I-FURN', _flat(_rect(P(22.0, bb), tdir(bb), d(bb), 0.7, 0.35), L1 + 0.72, L1 + 0.75))
        if RENDER: seat('chair_office', P(22.75, bb), -d(bb), L1)
    a('I-FURN', _flat(arc_band(24.55, 24.95, b0 + 1.0, b1 - 1.0), L1, L1 + 2.0))
    bm = M.mid('L25')[0]; a('I-FURN', _flat(_rect(P(13.9, bm), tdir(bm), d(bm), 0.8, 0.4), L1 + 0.72, L1 + 0.75))
    if RENDER:
        seat('chair_office', P(14.6, bm), -d(bm), L1); seat('chair', P(13.1, bm - 1.5), d(bm), L1); seat('chair', P(13.1, bm + 1.5), d(bm), L1)
        b0r, b1r = M.mid('L21')[1:]; seat('chair', P(25.3, b0r + 2.0), -d(b0r), L1); seat('chair', P(25.3, b0r + 3.5), -d(b0r), L1)
    bm, b0, b1 = M.mid('L26'); a('I-FURN', _flat(arc_band(12.7, 13.8, b0 + 3.5, b1 - 3.5), L1 + 0.72, L1 + 0.75))
    if RENDER:
        for bb in np.linspace(b0 + 4.5, b1 - 4.5, 4): seat('chair_office', P(12.25, bb), d(bb), L1); seat('chair_office', P(14.25, bb), -d(bb), L1)
    # ================================================================ L2
    bm, b0, b1 = M.mid('M01'); aa, cc_ = b0 + 7, b1 - 7
    a('I-GALLERY', _flat(arc_band(14.55, 14.8, aa, cc_), L2, L2 + 2.4))
    for bb in np.linspace(aa + 2, cc_ - 2, 11): a('I-FURN', _flat(_rect(P(14.3, bb), tdir(bb), d(bb), 0.3, 0.2), L2 + 0.9, L2 + 1.3))
    for o in (0.33, 0.67): bb = b0 + (b1 - b0) * o; a('I-FURN', _flat(arc_band(12.2, 12.8, bb - 4, bb + 4), L2, L2 + 0.45))
    for key, mb in (('M10', QIBLA), ('M12', M.mid('M12')[2] - 3.0)):
        bm, b0, b1 = M.mid(key)
        a('I-PRAYER', _flat(arc_band(15.3, 15.36, b0 + 0.6, b1 - 0.6), L2, L2 + 2.6))                    # girih screen on the qibla glass
        m = Point(P(15.3, mb)).buffer(0.5).intersection(SC.disc(15.3)); a('I-PRAYER', _flat(m, L2, L2 + 2.4))
        dd = [x for x in M.DOORS if x['key'] == key][0]; bd = plans.brg(dd['p'])
        for sg in (-1, 1): a('I-FURN-TIMBER', _flat(arc_band(11.15, 11.5, bd + sg * math.degrees(0.8 / 11.2), bd + sg * math.degrees(2.0 / 11.2)), L2, L2 + 0.5))
    for key in ('M11', 'M13'):
        bm, b0, b1 = M.mid(key); a('I-FURN', _flat(arc_band(14.85, 15.3, b0 + 0.8, b1 - 0.8), L2, L2 + 0.75))
        for bb in np.linspace(b0 + 1.6, b1 - 1.6, 4):
            if RENDER: seat('stool_low', P(14.45, bb), d(bb), L2)
            else: a('I-STEEL', _cyl(P(14.45, bb), 0.16, L2, L2 + 0.35, 10))
    bm, b0, b1 = M.mid('M14')
    a('I-STATE-TRG', _flat(arc_band(14.6, 15.15, b0 + 3, b1 - 9), L2, L2 + 0.45))
    for bb in np.arange(b0 + 4, b1 - 9, 1.6): a('I-FURN-TIMBER', _flat(LineString([P(14.6, bb), P(15.15, bb)]).buffer(0.04), L2 + 0.45, L2 + 0.8))
    a('I-STATE-TRG', _flat(Point(P(13.3, b1 - 4.5)).buffer(0.9), L2, L2 + 0.02))
    for a_, c_ in ((50, 60), (70, 80), (95, 105), (205, 215), (222, 232)): a('I-FURN-TIMBER', _flat(arc_band(14.8, 15.25, a_, c_), L2, L2 + 0.45))

def plans_ground(x, y):
    import sections as SE
    return SE.ground_z((x, y))
