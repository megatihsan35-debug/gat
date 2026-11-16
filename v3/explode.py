"""Exploded model: SITE + GROUND FLOOR | FIRST FLOOR | SECOND FLOOR | ROOF, each band lifted by OFF[band].
Bands are cut from the render model by height planes (just under each slab top, so a slab goes with the floor it carries);
L2 exists on the inner ring only, so anything above the L2 cut outside R_L2 stays with the first floor (outer-ring walls
and fins run up to the outer roof). Roof layers go to ROOF whole; landscape outside the drum stays on the site.
python3 explode.py [glb] [dae]  ->  out/render/explode/"""
import os, sys, json, math, shutil
import numpy as np, trimesh
import render_model as R, model3d as M3, interior3d as I3

C = (70.3, 27.0)
BANDS = ['SITE', 'GF', 'L1', 'L2', 'ROOF']
NAME = {'SITE': 'SITE', 'GF': 'GROUND FLOOR', 'L1': 'FIRST FLOOR', 'L2': 'SECOND FLOOR', 'ROOF': 'ROOF'}
LEVEL = {'SITE': '±0.000', 'GF': '+0.900', 'L1': '+5.400', 'L2': '+9.600', 'ROOF': '+10.200 TO +19.800'}
OFF = {'SITE': 0.0, 'GF': 0.0, 'L1': 16.0, 'L2': 34.0, 'ROOF': 50.0}
CUT_GF, CUT_L1, CUT_L2 = 0.88, 4.78, 8.98
R_L2 = 16.4                    # second floor + its balustrades lie inside this radius
R_SITE = 27.2                  # landscape outside the drum stays on the site
ROOF_LAYERS = {'A-ROOF', 'A-ROOF-MID', 'A-FUNNEL', 'A-CLERESTORY', 'A-FASCIA', 'I-TENUN'}
SITE_LAYERS = ('SITE-', 'L-', 'GROUND', 'KERB', 'ROAD-MARK')

def _slab(m, z0, z1):
    """part of mesh m between heights z0..z1 (triangles cut by the planes, no caps)"""
    for z, sgn in ((z0, 1), (z1, -1)):
        if m is None or not len(m.faces): return None
        if not np.isfinite(z): continue
        zz = m.vertices[:, 2]
        if sgn > 0 and zz.min() >= z: continue
        if sgn < 0 and zz.max() <= z: continue
        if (sgn > 0 and zz.max() <= z) or (sgn < 0 and zz.min() >= z): return None
        m = trimesh.intersections.slice_mesh_plane(m, (0, 0, sgn), (0, 0, z), cap=False)
    return m if m is not None and len(m.faces) else None

def _faces(m, mask):
    if m is None or not mask.any(): return None
    return m.submesh([np.where(mask)[0]], append=True)

def _r(m):
    c = m.triangles_center; return np.hypot(c[:, 0] - C[0], c[:, 1] - C[1])

def split(key, m):
    """-> {band: mesh}"""
    out = {}
    def put(b, q):
        if q is not None and len(q.faces): out.setdefault(b, []).append(q)
    m = trimesh.Trimesh(m.vertices, m.faces, process=False)
    if key in ROOF_LAYERS: put('ROOF', m); return {b: trimesh.util.concatenate(v) for b, v in out.items()}
    if key.startswith(SITE_LAYERS):
        r = _r(m); put('SITE', _faces(m, r > R_SITE)); m = _faces(m, r <= R_SITE)
        if m is None: return {b: trimesh.util.concatenate(v) for b, v in out.items()}
    put('SITE', _slab(m, -np.inf, CUT_GF)); put('GF', _slab(m, CUT_GF, CUT_L1)); put('L1', _slab(m, CUT_L1, CUT_L2))
    up = _slab(m, CUT_L2, np.inf)
    if up is not None:
        if key == 'A-MAST': put('ROOF', up)
        else:
            r = _r(up); put('L2', _faces(up, r <= R_L2)); put('L1', _faces(up, r > R_L2))
    return {b: trimesh.util.concatenate(v) for b, v in out.items()}

def inst_band(cname, T):
    if cname.startswith(('tree', 'car')): return 'SITE'
    T = np.asarray(T); x, y, z = T[:3, 3]; z += 0.3
    if math.hypot(x - C[0], y - C[1]) > R_SITE: return 'SITE'
    return 'SITE' if z < CUT_GF else 'GF' if z < CUT_L1 else 'L1' if z < CUT_L2 else ('L2' if math.hypot(x - C[0], y - C[1]) <= R_L2 else 'L1')

def build(coarse):
    if coarse:
        _dr, _fl = M3.draped, M3.flat
        def dr(poly, ztop, zbot, cell=None, seg=0.6):
            if cell: cell = (cell[0] * 2.0, cell[1] * 1.6)
            return _dr(poly.simplify(0.03), ztop, zbot, cell, seg * 2)
        def fl(poly, z0, z1): return _fl(poly.simplify(0.02) if hasattr(poly, 'simplify') else poly, z0, z1)
        M3.draped, M3.flat = dr, fl
    I3.RENDER = True; I3.SEATS.clear()
    layers = M3.build()
    if coarse: M3.draped, M3.flat = _dr, _fl
    ex = R.extras()
    bands = {b: {} for b in BANDS}
    for k, m in list(layers.items()) + [(k, trimesh.util.concatenate(v)) for k, v in ex.items()]:
        if k in R.DROP or not len(m.faces): continue
        mat = R.LAYER_MAT.get(k) or 'Solid-Surface'
        for b, q in split(k, m).items():
            q = q.copy(); q.apply_translation((0, 0, OFF[b])); bands[b].setdefault(mat, []).append(q)
    bands = {b: {k: trimesh.util.concatenate(v) for k, v in d.items()} for b, d in bands.items()}
    inst = R.trees() + R.cars() + R.people() + R.seats()
    binst = {b: [] for b in BANDS}
    for cname, T in inst:
        b = inst_band(cname, T); T2 = np.array(T, float); T2[2, 3] += OFF[b]; binst[b].append((cname, T2))
    return bands, binst

OUTD = os.path.join(R.OUT, 'explode')

def labels():
    """3D anchor points for the band labels (left edge of each band, at its floor level) + alignment posts"""
    lab = {}
    for b, z in (('SITE', 0.0), ('GF', 0.9), ('L1', 5.4), ('L2', 9.6), ('ROOF', 13.0)):
        lab[b] = dict(name=NAME[b], level=LEVEL[b], z=z + OFF[b])
    return lab

if __name__ == '__main__':
    os.makedirs(OUTD, exist_ok=True)
    args = sys.argv[1:] or ['glb', 'dae']
    if 'glb' in args:
        bands, binst = build(coarse=False)
        groups = {}
        for b, d in bands.items():
            for k, m in d.items(): groups.setdefault(k, []).append(m)
        groups = {k: trimesh.util.concatenate(v) for k, v in groups.items()}
        inst = [x for b in BANDS for x in binst[b]]
        R.export_glb(groups, R.library(), inst, os.path.join(OUTD, 'titik-temu-exploded.glb'))
        json.dump(dict(labels=labels(), off=OFF, faces={b: sum(len(m.faces) for m in d.values()) for b, d in bands.items()}),
                  open(os.path.join(OUTD, 'explode.json'), 'w'), indent=1)
        print('glb faces', {b: sum(len(m.faces) for m in d.values()) for b, d in bands.items()})
    if 'dae' in args:
        import dae_su
        bands, binst = build(coarse=True); lib = R.library(low=True)
        tree = [(NAME[b] + ('' if b == 'SITE' else '  ' + LEVEL[b]), bands[b], binst[b]) for b in BANDS]
        for tx in (False, True):
            p = os.path.join(OUTD, 'titik-temu-exploded-textured.dae' if tx else 'titik-temu-exploded-colour.dae')
            ng, nt, texs = dae_su.export(None, lib, None, p, tx, bands=tree)
            print(os.path.basename(p), 'geometries', ng, 'triangles', nt, 'MB', round(os.path.getsize(p) / 1e6, 1))
            if tx: dae_su.pow2_textures(texs, os.path.join(OUTD, 'textures'))
