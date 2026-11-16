"""SketchUp-safe COLLADA writer for the render model, in the SAME format as model/dae_export.py (the Crit 1 .dae that
SketchUp opens): ElementTree, one material per geometry (symbol "m"), per-triangle NORMAL index, components as
library_nodes + instance_node, small geometries (<= CHUNK triangles), no degenerate triangles.
Textured variant adds the image/surface/sampler layout SketchUp itself exports (texcoord UVSET0, TEXCOORD set 0).
python3 dae_su.py  ->  out/render/dae_su/  (titik-temu-colour.dae, titik-temu-textured.dae + textures/)"""
import os, re, json, shutil, sys
import numpy as np, trimesh
import xml.etree.ElementTree as ET
from PIL import Image
import render_model as R

CHUNK = 6000
MIN_EDGE = 0.002            # m - drop slivers SketchUp would collapse
def sid(s): return re.sub(r'[^A-Za-z0-9_]', '_', s)
def fmt(a, d): return ' '.join(f'{v:.{d}f}' for v in np.asarray(a).ravel())

def clean(mesh):
    """exact-duplicate vertices merged only (no rounding), degenerate / sliver triangles removed"""
    V = np.asarray(mesh.vertices, float); F = np.asarray(mesh.faces)
    if len(F) == 0: return None
    T = V[F]
    e = np.stack([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1), np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], 1)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); area = np.linalg.norm(n, axis=1) / 2
    ok = (e.min(1) >= MIN_EDGE) & (area > 1e-6) & np.isfinite(T).all(axis=(1, 2))
    F = F[ok]
    if not len(F): return None
    used, inv = np.unique(F.ravel(), return_inverse=True)
    V2 = np.round(V[used], 4); F2 = inv.reshape(-1, 3)
    # rounding to 0.1 mm can still join two corners of a tiny triangle -> check again
    good = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 0] != F2[:, 2])
    m = trimesh.Trimesh(V2, F2[good], process=False)
    return m if len(m.faces) else None

def tex_mean(t):
    im = Image.open(os.path.join(R.TEXD, t)).convert('RGBA'); a = np.asarray(im, float)
    w = a[..., 3:] / 255.0; c = (a[..., :3] * w).sum((0, 1)) / max(w.sum(), 1)
    return [float(x) / 255 for x in c]

def export(groups, lib, inst, path, textured, texdir='textures', bands=None):
    """bands: optional [(group name, {material: mesh}, [(component, matrix)])] -> one top group per band (exploded model)"""
    NS = 'http://www.collada.org/2005/11/COLLADASchema'
    root = ET.Element('COLLADA', xmlns=NS, version='1.4.1')
    asset = ET.SubElement(root, 'asset')
    ET.SubElement(ET.SubElement(asset, 'contributor'), 'authoring_tool').text = 'Titik Temu model builder'
    ET.SubElement(asset, 'unit', name='meter', meter='1')
    ET.SubElement(asset, 'up_axis').text = 'Z_UP'
    allg = set(groups or {}) | {k for _, d, _ in (bands or []) for k in d}
    used = sorted(allg | {k for parts in lib.values() for _, k in parts})
    texs = sorted({R.MATS[k]['tex'] for k in used if R.MATS[k]['tex']}) if textured else []
    if texs:
        limg = ET.SubElement(root, 'library_images')
        for t in texs:
            ET.SubElement(ET.SubElement(limg, 'image', id=f'img_{sid(t.split(".")[0])}', name=t.split('.')[0]), 'init_from').text = f'{texdir}/{t}'
    lfx, lmat, lgeo = ET.SubElement(root, 'library_effects'), ET.SubElement(root, 'library_materials'), ET.SubElement(root, 'library_geometries')
    lnodes = ET.SubElement(root, 'library_nodes'); lvs = ET.SubElement(root, 'library_visual_scenes')
    mid, is_tex = {}, {}
    for i, k in enumerate(used):
        md = R.MATS[k]; mk = f'mat{i}'; mid[k] = mk; is_tex[k] = bool(textured and md['tex'])
        name = 'TT ' + k.replace('-', ' ')
        fx = ET.SubElement(lfx, 'effect', id=f'{mk}_fx', name=name)
        pc = ET.SubElement(fx, 'profile_COMMON')
        if is_tex[k]:
            iid = f'img_{sid(md["tex"].split(".")[0])}'
            sf = ET.SubElement(ET.SubElement(pc, 'newparam', sid=f'{mk}_surf'), 'surface', type='2D'); ET.SubElement(sf, 'init_from').text = iid
            sp = ET.SubElement(ET.SubElement(pc, 'newparam', sid=f'{mk}_samp'), 'sampler2D'); ET.SubElement(sp, 'source').text = f'{mk}_surf'
        lam = ET.SubElement(ET.SubElement(pc, 'technique', sid='COMMON' if is_tex[k] else 'common'), 'lambert')
        if is_tex[k]:
            ET.SubElement(ET.SubElement(lam, 'diffuse'), 'texture', texture=f'{mk}_samp', texcoord='UVSET0')
        else:
            if md['tex']: c = tex_mean(md['tex'])
            else: h = md['color'].lstrip('#'); c = [int(h[j:j + 2], 16) / 255 for j in (0, 2, 4)]
            ET.SubElement(ET.SubElement(lam, 'diffuse'), 'color').text = f'{c[0]:.4f} {c[1]:.4f} {c[2]:.4f} 1'
        if md['alpha'] < 1:
            ET.SubElement(ET.SubElement(lam, 'transparent', opaque='A_ONE'), 'color').text = f'1 1 1 {md["alpha"]:.3f}'
            ET.SubElement(ET.SubElement(lam, 'transparency'), 'float').text = '1'
        mt = ET.SubElement(lmat, 'material', id=mk, name=name); ET.SubElement(mt, 'instance_effect', url=f'#{mk}_fx')
    gc = [0]; ntri = [0]
    def geometry(mesh, k):
        """one geometry per <= CHUNK triangles; returns list of geometry ids"""
        m = clean(mesh)
        if m is None: return []
        out = []
        md = R.MATS[k]
        for s0 in range(0, len(m.faces), CHUNK):
            sub = m.submesh([np.arange(s0, min(s0 + CHUNK, len(m.faces)))], append=True)
            sub = trimesh.Trimesh(sub.vertices, sub.faces, process=False)
            V, F = sub.vertices, sub.faces; N = sub.face_normals
            gid = f'g{gc[0]}'; gc[0] += 1; ntri[0] += len(F)
            g = ET.SubElement(lgeo, 'geometry', id=gid); mesh_ = ET.SubElement(g, 'mesh')
            srcs = [('pos', V, 4, 'XYZ'), ('nrm', N, 4, 'XYZ')]
            if is_tex[k]:
                uv = R.box_uv(sub, md['tile']).reshape(-1, 2)
                uvr = np.round(uv, 4); uq, uinv = np.unique(uvr, axis=0, return_inverse=True); uinv = uinv.reshape(-1)
                srcs.append(('uv', uq, 4, 'ST'))
            for nm, arr, d, prm in srcs:
                src = ET.SubElement(mesh_, 'source', id=f'{gid}_{nm}')
                fa = ET.SubElement(src, 'float_array', id=f'{gid}_{nm}_a', count=str(arr.size)); fa.text = fmt(arr, d)
                acc = ET.SubElement(ET.SubElement(src, 'technique_common'), 'accessor', source=f'#{gid}_{nm}_a', count=str(len(arr)), stride=str(len(prm)))
                for a in prm: ET.SubElement(acc, 'param', name=a, type='float')
            vt = ET.SubElement(mesh_, 'vertices', id=f'{gid}_v'); ET.SubElement(vt, 'input', semantic='POSITION', source=f'#{gid}_pos')
            tr = ET.SubElement(mesh_, 'triangles', count=str(len(F)), material='m')
            ET.SubElement(tr, 'input', semantic='VERTEX', source=f'#{gid}_v', offset='0')
            ET.SubElement(tr, 'input', semantic='NORMAL', source=f'#{gid}_nrm', offset='1')
            fi = np.repeat(np.arange(len(F)), 3)
            if is_tex[k]:
                ET.SubElement(tr, 'input', semantic='TEXCOORD', source=f'#{gid}_uv', offset='2', set='0')
                idx = np.stack([F.ravel(), fi, uinv], 1)
            else:
                idx = np.stack([F.ravel(), fi], 1)
            ET.SubElement(tr, 'p').text = ' '.join(map(str, idx.ravel()))
            out.append(gid)
        return out
    def inst_geom(parent, gid, k):
        ig = ET.SubElement(parent, 'instance_geometry', url=f'#{gid}')
        tc = ET.SubElement(ET.SubElement(ig, 'bind_material'), 'technique_common')
        im = ET.SubElement(tc, 'instance_material', symbol='m', target=f'#{mid[k]}')
        if is_tex[k]: ET.SubElement(im, 'bind_vertex_input', semantic='UVSET0', input_semantic='TEXCOORD', input_set='0')
    nn = [0]
    def gnode(parent, name, mesh, k):
        gids = geometry(mesh, k)
        if not gids: return
        el = ET.SubElement(parent, 'node', id=f'n{nn[0]}_{sid(name)[:40]}', name=name); nn[0] += 1
        if len(gids) == 1: inst_geom(el, gids[0], k); return
        for j, gid in enumerate(gids):
            c = ET.SubElement(el, 'node', id=f'n{nn[0]}_{sid(name)[:36]}_{j + 1}', name=f'{name} {j + 1}'); nn[0] += 1
            inst_geom(c, gid, k)
    # components
    have = set()
    for cname, parts in lib.items():
        el = ET.SubElement(lnodes, 'node', id=f'def_{sid(cname)}', name=cname.replace('_', ' '))
        for j, (pm, k) in enumerate(parts): gnode(el, f'{k} {j + 1}', pm, k)
        have.add(cname)
    vs = ET.SubElement(lvs, 'visual_scene', id='scene', name='Titik Temu')
    top = ET.SubElement(vs, 'node', id='TitikTemu', name='Titik Temu v3 render model (units m, origin SW site corner)')
    TAG = lambda k: ('SITE' if k in ('Grass', 'Paving', 'Paving-Dark', 'Asphalt', 'Road-Marking', 'Kerb', 'Plinth', 'Water', 'Concrete') else
                     'LANDSCAPE' if k in ('Shrub', 'Soil', 'Rubber-Play', 'Anyaman') else
                     'INTERIOR' if k.startswith(('Screen-', 'Backwall-', 'State-', 'River-', 'Tactile', 'Stall', 'Gallery', 'Solid-Surface')) else 'BUILDING')
    cat = lambda c: 'PEOPLE' if c.startswith('person') else 'TREES' if c.startswith('tree') else 'CARS' if c.startswith('car') else 'FURNITURE'
    def place(parent, items, pre):
        cats = {}
        for cname, T in items: cats.setdefault(cat(cname), []).append((cname, T))
        for cg in ('TREES', 'CARS', 'PEOPLE', 'FURNITURE'):
            if cg not in cats: continue
            el = ET.SubElement(parent, 'node', id=f'grp_{pre}{cg}', name=cg)
            for cname, T in cats[cg]:
                T = np.asarray(T, float)
                c = ET.SubElement(el, 'node', id=f'n{nn[0]}_i', name=cname.replace('_', ' ')); nn[0] += 1
                ET.SubElement(c, 'matrix').text = fmt(T.ravel(), 6)
                ET.SubElement(c, 'instance_node', url=f'#def_{sid(cname)}')
    if bands:
        for bi, (bname, d, items) in enumerate(bands):
            el = ET.SubElement(top, 'node', id=f'band{bi}', name=bname)
            for k, m in d.items(): gnode(el, k, m, k)
            place(el, items, f'b{bi}_')
        ET.SubElement(ET.SubElement(root, 'scene'), 'instance_visual_scene', url='#scene')
        ET.ElementTree(root).write(path, xml_declaration=True, encoding='utf-8')
        return gc[0], ntri[0], texs
    tags = {}
    for k in groups: tags.setdefault(TAG(k), []).append(k)
    for tg in ('SITE', 'LANDSCAPE', 'BUILDING', 'INTERIOR'):
        if tg not in tags: continue
        el = ET.SubElement(top, 'node', id=f'grp_{tg}', name=tg)
        for k in tags[tg]: gnode(el, k, groups[k], k)
    cat = lambda c: 'PEOPLE' if c.startswith('person') else 'TREES' if c.startswith('tree') else 'CARS' if c.startswith('car') else 'FURNITURE'
    cats = {}
    for cname, T in inst: cats.setdefault(cat(cname), []).append((cname, T))
    for cg in ('TREES', 'CARS', 'PEOPLE', 'FURNITURE'):
        if cg not in cats: continue
        el = ET.SubElement(top, 'node', id=f'grp_{cg}', name=cg)
        for cname, T in cats[cg]:
            T = np.asarray(T, float)
            c = ET.SubElement(el, 'node', id=f'n{nn[0]}_i', name=cname.replace('_', ' ')); nn[0] += 1
            ET.SubElement(c, 'matrix').text = fmt(T.ravel(), 6)
            ET.SubElement(c, 'instance_node', url=f'#def_{sid(cname)}')
    ET.SubElement(ET.SubElement(root, 'scene'), 'instance_visual_scene', url='#scene')
    ET.ElementTree(root).write(path, xml_declaration=True, encoding='utf-8')
    return gc[0], ntri[0], texs

def pow2_textures(texs, dst):
    """copy textures as power-of-two RGB JPG (PNG kept for the alpha one) so every SketchUp version reads them"""
    os.makedirs(dst, exist_ok=True)
    for t in texs:
        im = Image.open(os.path.join(R.TEXD, t))
        w, h = im.size; p2 = lambda v: 1 << int(round(np.log2(v)))
        im = im.resize((min(1024, p2(w)), min(1024, p2(h))), Image.LANCZOS)
        if t.endswith('.png'): im.convert('RGBA').save(os.path.join(dst, t))
        else: im.convert('RGB').save(os.path.join(dst, t), quality=88, progressive=False, optimize=True)

if __name__ == '__main__':
    import pickle
    pk = sys.argv[1] if len(sys.argv) > 1 else None
    if pk and os.path.exists(pk): g, lib, inst = pickle.load(open(pk, 'rb'))
    else: g, lib, inst = R.build(coarse=True); lib = R.library(low=True)
    od = os.path.join(R.OUT, 'dae_su'); os.makedirs(od, exist_ok=True)
    for tx in (False, True):
        p = os.path.join(od, 'titik-temu-textured.dae' if tx else 'titik-temu-colour.dae')
        ng, nt, texs = export(g, lib, inst, p, tx)
        print(os.path.basename(p), 'geometries', ng, 'triangles', nt, 'MB', round(os.path.getsize(p) / 1e6, 1))
        if tx: pow2_textures(texs, os.path.join(od, 'textures'))
