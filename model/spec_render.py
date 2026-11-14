"""Turn the model spec into a GLB for rendering (restored)."""
import json, sys, numpy as np, trimesh, mapbox_earcut as earcut

def tri_face(f):
    outer, holes, n = f[0], f[1], np.array(f[2], float)
    rings = [np.array(outer, float)] + [np.array(h, float) for h in holes]
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a); u /= np.linalg.norm(u); v = np.cross(n, u)
    V3 = np.vstack(rings); V2 = np.c_[V3 @ u, V3 @ v]
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    idx = earcut.triangulate_float64(V2, ends).reshape(-1, 3)
    out = []
    for i, j, k in idx:
        p = V3[[i, j, k]]
        if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), n) < 0: p = p[[0, 2, 1]]
        out.append(p)
    return out

def xf(inst):
    o, x, y, z = (np.array(inst[k], float) for k in ('o', 'x', 'y', 'z'))
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, o
    return M

def collect(spec, hide=()):
    buckets = {}; defs = spec['defs']; cache = {}
    def def_tris(name):
        if name in cache: return cache[name]
        acc = {}
        for c in defs[name]['c']: walk(c, np.eye(4), None, acc)
        cache[name] = acc; return acc
    def walk(n, M, mat, acc):
        if n.get('tag') in hide: return
        if n['t'] == 'g':
            m = n.get('m', mat)
            for f in n.get('f', []):
                for t in tri_face(f):
                    p = (M @ np.c_[t, np.ones(3)].T).T[:, :3]
                    acc.setdefault(m or 'default', []).append(p)
            for c in n.get('c', []): walk(c, M, m, acc)
        elif n['t'] == 'i':
            sub = def_tris(n['d']); Mi = M @ xf(n)
            for m, tris in sub.items():
                mm = m if m != 'default' else (mat or 'default')
                T = np.array(tris).reshape(-1, 3); T = (Mi @ np.c_[T, np.ones(len(T))].T).T[:, :3]
                acc.setdefault(mm, []).extend(list(T.reshape(-1, 3, 3)))
    for n in spec['root']: walk(n, np.eye(4), None, buckets)
    return buckets

def to_glb(spec, path, hide=()):
    b = collect(spec, hide); scene = trimesh.Scene()
    for m, tris in b.items():
        if not tris: continue
        T = np.array(tris).reshape(-1, 3)
        T = T[:, [0, 2, 1]] * np.array([1, 1, -1])          # z-up -> y-up (x, z, -y)
        mesh = trimesh.Trimesh(vertices=T, faces=np.arange(len(T)).reshape(-1, 3), process=False)
        info = spec['materials'].get(m, dict(c=[200, 200, 200], a=1))
        mat = trimesh.visual.material.PBRMaterial(name=m, baseColorFactor=[*[c / 255 for c in info['c']], info['a']], metallicFactor=0.0, roughnessFactor=0.85,
                                                  alphaMode='BLEND' if info['a'] < 1 else 'OPAQUE', doubleSided=True)
        mesh.visual = trimesh.visual.TextureVisuals(material=mat)
        scene.add_geometry(mesh, node_name=m, geom_name=m)
    scene.export(path); print('glb', path, sum(len(v) for v in b.values()), 'triangles')

if __name__ == '__main__':
    spec = json.load(open(sys.argv[1])); hide = set()
    if len(sys.argv) > 3:
        keys = sys.argv[3].split(',')
        hide = {t['n'] for t in spec['tags'] if any(t['n'].startswith(k) for k in keys)}
    to_glb(spec, sys.argv[2], hide)
