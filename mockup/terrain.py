"""Site contour layers for the 1:500 mock-up, traced from the user's model photo (approximate)."""
import json, sys, numpy as np, cv2
sys.path.insert(0, '/home/claude/crit1')
from shapely.geometry import LineString, Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union, polygonize, linemerge
import site_el as SE
from geom import SITE, SITE_POLY

XL, XR, YB, YT = -20.0, 130.0, -40.0, 92.0
BOARD = box(XL, YB, XR, YT)
H = np.load('/home/claude/mock/H.npy')
E = json.load(open('/home/claude/mock/edges_px.json'))
def mp(pts): return [tuple(p) for p in cv2.perspectiveTransform(np.array([pts], float), H)[0]]
def comp(k, top_first=True, key=lambda p: -p[1]):
    pts = mp(E[str(k)])
    if (key(pts[0]) > key(pts[-1])) != top_first: pts = pts[::-1]
    ls = LineString(pts).simplify(0.6)
    return list(ls.coords)
def ext(p, q, L=80):   # extend beyond p in direction q->p
    v = np.array(p) - np.array(q); v /= np.linalg.norm(v); return tuple(np.array(p) + v * L)

def extend(p, q, L):  # point beyond q along p->q
    v = np.array(q) - np.array(p); v /= np.linalg.norm(v); return tuple(np.array(q) + v * L)
A = [(13.0, 97), (13.8, 93.5), (15.7, 89.1), (16.3, 85.5), (17.2, 81.8), (17.9, 78.2), (18.7, 74.3), (18.9, 70.4), (18.6, 66.5), (18.2, 62.6),
     (17.9, 58.6), (17.5, 54.2), (14.5, 50.5), (10.9, 46.4), (6.5, 43.6), (1.9, 42.2), (-4.0, 41.5), (XL - 5, 41.0)]
Bl = [(19.0, 97), (19.4, 93.1), (20.4, 89.5), (21.8, 85.1), (22.4, 81.0), (22.9, 76.7), (23.5, 72.3), (23.9, 67.8), (24.1, 63.2), (24.4, 58.5),
      (23.6, 53.7), (21.6, 49.0), (19.4, 44.2), (16.9, 38.9), (11.5, 36.3), (6.1, 32.2), (0.0, 30.5), (XL - 5, 29.5)]
RN = [tuple(SE.road_pt(x) - SE.N_IN * 0.5) for x in (-40, 160)]
_c = [(27.5, 97), (27.3, 92.0), (26.7, 89.6), (26.3, 87.4), (25.9, 85.1), (25.4, 82.9), (25.2, 81.0), (26.4, 78.3), (27.2, 75.7), (28.0, 73.4),
      (29.1, 70.6), (29.7, 69.0), (32.2, 66.3), (35.2, 62.5), (36.6, 59.4), (35.6, 56.4), (33.4, 54.6), (31.5, 50.8), (29.7, 46.9), (27.8, 42.7),
      (25.8, 38.4), (23.9, 34.2), (22.9, 32.0), (21.1, 29.8), (18.8, 27.6), (16.6, 25.5), (14.5, 23.6), (12.1, 22.4), (6.0, 21.0), (-0.5, 17.4),
      (-3.1, 16.3), (-4.9, 15.2), (-5.9, 12.5), (-7.2, 10.0), (-8.2, 7.2), (-9.3, 4.2), (-10.3, 2.3)]
_c = [((x - 4.0 * max(0.0, 1 - abs(y - 36) / 14)) if 20 < y < 52 else x, y) for x, y in _c]
C = _c + [extend(_c[-2], _c[-1], 6)]
D = [(33.5, 97), (33.2, 91.0), (32.7, 88.0), (32.3, 84.6), (32.1, 81.2), (31.9, 79.7), (32.5, 77.7), (33.6, 74.0), (34.6, 70.2), (35.4, 67.5),
     (37.1, 65.9), (39.0, 64.3), (40.8, 62.8), (48.0, 60.4), (70.0, 63.2), (87.5, 65.5), (100.0, 67.0), (112.0, 68.5)]
def thru(p, q):
    return [extend(q, p, 120), extend(p, q, 120)]
cut = Polygon([RN[0], RN[1], (160, -300), (-40, -300)])
F = list(LineString(thru((4.2, -26.8), (16.3, -13.3))).intersection(cut).coords)
G = list(LineString(thru((30.9, -38.8), (44.4, -21.8))).intersection(cut).coords)
G = [G[0], extend(G[0], G[1], 0) if False else G[1]]
J = thru((133.2, -52.9), (99.4, 85.0))
F = [F[0], extend(F[0], F[1], 0.3)] if F[1][1] > F[0][1] else [extend(F[1], F[0], 0.3), F[1]]
G = [G[0], extend(G[0], G[1], 0.3)] if G[1][1] > G[0][1] else [extend(G[1], G[0], 0.3), G[1]]
W = [(40.8, 62.8), (36.6, 59.4)]
LINES = dict(A=A, B=Bl, C=C, D=D, W=W, RN=RN, F=F, G=G, J=J)
SEEDS = [((-12, 75), 9), ((5, 60), 9), ((-12, 35), 8), ((21, 75), 8), ((-12, 15), 7), ((24, 45), 7), ((30, 85), 6), ((65, 82), 5), ((60, 20), 4), ((108, 30), 4),
         ((-5, 5), 4), ((-15, -12), 3), ((15, -32), 2), ((80, -30), 1), ((126, 80), 0), ((128, -10), 0), ((129, -30), 0)]
def faces():
    net = unary_union([LineString(v) for v in LINES.values()] + [BOARD.exterior])
    fs = [f.intersection(BOARD) for f in polygonize(net)]
    fs = [f for f in fs if f.area > 0.5 and BOARD.contains(f.representative_point())]
    lev = []
    for f in fs:
        hits = [L for p, L in SEEDS if f.contains(Point(p))]
        lev.append(hits[0] if hits else None)
    return fs, lev
FACES, LEVELS = faces()
NL = 9
def layer(k):
    g = unary_union([f for f, L in zip(FACES, LEVELS) if L is not None and L >= k]).buffer(0.01).buffer(-0.01)
    return g.intersection(BOARD)
LAYERS = {k: layer(k) for k in range(1, NL + 1)}
if __name__ == '__main__':
    for f, L in zip(FACES, LEVELS): print(L, round(f.area), [round(v, 1) for v in f.representative_point().coords[0]])
    for k, g in LAYERS.items(): print(k, g.geom_type, round(g.area), getattr(g, 'geoms', [g]).__len__() if hasattr(g, 'geoms') else 1)
