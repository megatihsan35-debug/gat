"""Face builders for the SketchUp model spec (metres, x east, y north, z up).
A face = [outer_ring, [hole_rings], normal]; rings are lists of [x, y, z] (no repeat of first point).
All solids are closed and every face carries its outward normal."""
import numpy as np
import mapbox_earcut as earcut
from shapely.geometry import Polygon, MultiPolygon, box, Point, LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

R3 = 3          # mm precision in the exported data

def polys(g):
    if g is None or g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    if g.geom_type in ('MultiPolygon', 'GeometryCollection'):
        return [q for q in g.geoms if q.geom_type == 'Polygon' and not q.is_empty]
    return []

def clean(g, min_area=1e-4):
    g = g.buffer(0)
    ps = [orient(q, 1.0) for q in polys(g) if q.area > min_area]
    return MultiPolygon(ps) if ps else MultiPolygon()

def _dedupe(ring, tol=0.0015):
    out = []
    for p in ring:
        if not out or np.linalg.norm(np.array(p) - np.array(out[-1])) > tol: out.append(list(p))
    while len(out) > 1 and np.linalg.norm(np.array(out[0]) - np.array(out[-1])) <= tol: out.pop()
    # drop spikes / exact back-tracks
    changed = True
    while changed and len(out) >= 3:
        changed = False
        for i in range(len(out)):
            a, b, c = np.array(out[i - 1]), np.array(out[i]), np.array(out[(i + 1) % len(out)])
            u, v = b - a, c - b
            if np.linalg.norm(u) < tol or np.linalg.norm(v) < tol: out.pop(i); changed = True; break
            cr = np.linalg.norm(np.cross(u, v)) / (np.linalg.norm(u) * np.linalg.norm(v))
            if cr < 1e-9 and np.dot(u, v) < 0: out.pop(i); changed = True; break
    return out

def F(outer, holes=(), n=None):
    o = _dedupe([[round(float(c), R3) for c in p] for p in outer])
    hs = [_dedupe([[round(float(c), R3) for c in p] for p in h]) for h in holes]
    hs = [h for h in hs if len(h) >= 3]
    if len(o) < 3: return None
    if n is None: n = newell(o)
    n = np.array(n, float); n = n / (np.linalg.norm(n) or 1)
    return [o, hs, [round(float(c), 6) for c in n]]

def newell(ring):
    p = np.array(ring, float); n = np.zeros(3)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
    return n / (np.linalg.norm(n) or 1)

def _hface(poly, z, up):
    o = [[x, y, z] for x, y in list(poly.exterior.coords)[:-1]]
    hs = [[[x, y, z] for x, y in list(h.coords)[:-1]] for h in poly.interiors]
    return F(o, hs, [0, 0, 1 if up else -1])

def bsolid(bands):
    """bands: [(z0, z1, geom)] contiguous bottom -> top. Returns faces of the union solid with merged side faces."""
    bands = [(z0, z1, clean(g)) for z0, z1, g in bands if z1 - z0 > 1e-6]
    faces = []
    # horizontal faces
    for k, (z0, z1, g) in enumerate(bands):
        below = bands[k - 1][2] if k > 0 else MultiPolygon()
        for q in polys(clean(g.difference(below)) if k > 0 else g): faces.append(_hface(q, z0, False))
        above = bands[k + 1][2] if k + 1 < len(bands) else MultiPolygon()
        for q in polys(clean(g.difference(above)) if k + 1 < len(bands) else g): faces.append(_hface(q, z1, True))
    # vertical faces grouped by plane
    planes = {}
    for z0, z1, g in bands:
        for q in polys(g):
            for ring in [q.exterior] + list(q.interiors):
                cs = np.array(ring.coords)
                for i in range(len(cs) - 1):
                    a, b = cs[i], cs[i + 1]; L = np.linalg.norm(b - a)
                    if L < 1e-4: continue
                    t = (b - a) / L; n = np.array([t[1], -t[0]])          # outward (right side) for CCW ext / CW holes
                    ang = round(float(np.degrees(np.arctan2(n[1], n[0]))) % 360, 4) % 360
                    nn = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
                    c = round(float(nn @ a), 4)
                    tt = np.array([-nn[1], nn[0]])
                    s0, s1 = sorted([round(float(tt @ a), 5), round(float(tt @ b), 5)])
                    planes.setdefault((ang, c), []).append(box(s0, z0, s1, z1))
    for (ang, c), boxes in planes.items():
        nn = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))]); tt = np.array([-nn[1], nn[0]])
        u = unary_union(boxes).buffer(0)
        for q in polys(u):
            q = q.simplify(0) if False else q
            def to3(ring):
                return [[*(nn * c + tt * s), z] for s, z in list(ring.coords)[:-1]]
            faces.append(F(to3(q.exterior), [to3(h) for h in q.interiors], [nn[0], nn[1], 0]))
    return [f for f in faces if f]

def prism(g, z0, z1): return bsolid([(z0, z1, g)])

def box_faces(x0, y0, z0, x1, y1, z1):
    return prism(box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), min(z0, z1), max(z0, z1))

def cyl_faces(cx, cy, r, z0, z1, n=16):
    return prism(Point(cx, cy).buffer(r, max(4, n // 4)), z0, z1)

def mesh_faces(V, P):
    """V: vertices, P: polygons (indices, CCW seen from outside)."""
    V = np.array(V, float); out = []
    for poly in P:
        f = F([V[i] for i in poly])
        if f: out.append(f)
    return out

def beam(p, q, w, h, up=(0, 0, 1)):
    """oriented box from p to q, section w (horizontal) x h (vertical-ish)"""
    p, q = np.array(p, float), np.array(q, float); ax = q - p; L = np.linalg.norm(ax)
    if L < 1e-6: return []
    ax /= L; upv = np.array(up, float)
    if abs(ax @ upv) > 0.99: upv = np.array([1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.array([0, 1.0, 0])
    s = np.cross(ax, upv); s /= np.linalg.norm(s); u = np.cross(s, ax)
    V = []
    for e in (p, q):
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            V.append(e + s * a * w / 2 + u * b * h / 2)
    P = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    fs = mesh_faces(V, P)
    # make sure normals point away from the centroid
    cen = (p + q) / 2
    for f in fs:
        c = np.mean(np.array(f[0]), axis=0)
        if np.dot(np.array(f[2]), c - cen) < 0:
            f[0] = f[0][::-1]; f[2] = [-x for x in f[2]]
    return fs

def xprism(profile, vec):
    """planar polygon (3D, simple) extruded by vec."""
    P = np.array(profile, float); v = np.array(vec, float)
    n = newell(P)
    if n @ v > 0: P = P[::-1]; n = -n                        # base faces away from extrusion
    top = P + v
    faces = [F(P, [], n), F(top[::-1], [], -n)]
    m = len(P)
    for i in range(m):
        a, b = P[i], P[(i + 1) % m]
        quad = [a, b, b + v, a + v]
        fn = newell(quad)
        cen = np.mean(np.vstack([P, top]), axis=0)
        f = F(quad)
        if f is None: continue
        if np.dot(f[2], np.mean(np.array(quad), axis=0) - cen) < 0 and False: pass
        faces.append(f)
    # orient side faces outward: side normal must point away from polygon interior in-plane
    fixed = []
    cen = np.mean(np.vstack([P, top]), axis=0)
    for f in faces:
        if f is None: continue
        fixed.append(f)
    return fixed

def tri(poly):
    """earcut a shapely polygon -> list of triangles (2D coordinate arrays)"""
    rings = [np.array(poly.exterior.coords)[:-1]] + [np.array(h.coords)[:-1] for h in poly.interiors]
    V = np.vstack(rings); ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    idx = earcut.triangulate_float64(V, ends).reshape(-1, 3)
    return V, idx

def vtop(poly2d, z0, zfun):
    """prism with flat bottom z0 and a top following zfun(x, y) (triangulated). Sides are vertical (planar)."""
    faces = []
    for q in polys(clean(poly2d)):
        faces.append(_hface(q, z0, False))
        V, idx = tri(q)
        Z = np.array([zfun(x, y) for x, y in V])
        for a, b, c in idx:
            pa, pb, pc = [*V[a], Z[a]], [*V[b], Z[b]], [*V[c], Z[c]]
            f = F([pa, pb, pc])
            if f is None: continue
            if f[2][2] < 0: f = F([pa, pc, pb])
            if f: faces.append(f)
        for ring in [q.exterior] + list(q.interiors):
            cs = np.array(ring.coords)
            for i in range(len(cs) - 1):
                a, b = cs[i], cs[i + 1]
                if np.linalg.norm(b - a) < 1e-4: continue
                t = (b - a) / np.linalg.norm(b - a); n = [t[1], -t[0], 0]
                f = F([[*a, z0], [*b, z0], [*b, zfun(*b)], [*a, zfun(*a)]], [], n)
                if f: faces.append(f)
    return faces

def fix_outward(faces, inside_pt):
    """flip faces whose normal points towards an interior reference point (convex-ish solids only)."""
    c = np.array(inside_pt, float)
    for f in faces:
        m = np.mean(np.array(f[0]), axis=0)
        if np.dot(np.array(f[2]), m - c) < 0:
            f[0] = f[0][::-1]; f[2] = [-x for x in f[2]]
    return faces
