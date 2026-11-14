"""Model spec -> COLLADA 1.4.1 (.dae) with nested groups, reusable components (library_nodes) and materials.
Fallback for SketchUp versions without Ruby (File > Import > COLLADA)."""
import json, sys, re, numpy as np
import xml.etree.ElementTree as ET
from spec_render import tri_face

def sid(s): return re.sub(r'[^A-Za-z0-9_]', '_', s)

def export(spec, path):
    NS = 'http://www.collada.org/2005/11/COLLADASchema'
    root = ET.Element('COLLADA', xmlns=NS, version='1.4.1')
    asset = ET.SubElement(root, 'asset')
    ET.SubElement(ET.SubElement(asset, 'contributor'), 'authoring_tool').text = 'Titik Temu model builder'
    ET.SubElement(asset, 'unit', name='meter', meter='1')
    ET.SubElement(asset, 'up_axis').text = 'Z_UP'
    lfx, lmat, lgeo = ET.SubElement(root, 'library_effects'), ET.SubElement(root, 'library_materials'), ET.SubElement(root, 'library_geometries')
    lnodes = ET.SubElement(root, 'library_nodes')
    lvs = ET.SubElement(root, 'library_visual_scenes')
    mid = {}
    for i, (name, m) in enumerate(spec['materials'].items()):
        k = f'mat{i}'; mid[name] = k
        fx = ET.SubElement(lfx, 'effect', id=f'{k}_fx', name=name)
        lam = ET.SubElement(ET.SubElement(ET.SubElement(fx, 'profile_COMMON'), 'technique', sid='common'), 'lambert')
        c = [x / 255 for x in m['c']]
        ET.SubElement(ET.SubElement(lam, 'diffuse'), 'color').text = f'{c[0]:.4f} {c[1]:.4f} {c[2]:.4f} 1'
        if m['a'] < 1:
            ET.SubElement(ET.SubElement(lam, 'transparent', opaque='A_ONE'), 'color').text = f'1 1 1 {m["a"]:.3f}'
            ET.SubElement(ET.SubElement(lam, 'transparency'), 'float').text = '1'
        mt = ET.SubElement(lmat, 'material', id=k, name=name); ET.SubElement(mt, 'instance_effect', url=f'#{k}_fx')
    gcount = [0]
    def geometry(faces):
        tris = []
        for f in faces: tris += tri_face(f)
        if not tris: return None
        T = np.array(tris).reshape(-1, 3)
        N = []
        for t in tris:
            n = np.cross(t[1] - t[0], t[2] - t[0]); ln = np.linalg.norm(n); N.append(n / ln if ln > 0 else [0, 0, 1])
        gid = f'g{gcount[0]}'; gcount[0] += 1
        g = ET.SubElement(lgeo, 'geometry', id=gid); mesh = ET.SubElement(g, 'mesh')
        for nm, arr in (('pos', T), ('nrm', np.array(N))):
            src = ET.SubElement(mesh, 'source', id=f'{gid}_{nm}')
            fa = ET.SubElement(src, 'float_array', id=f'{gid}_{nm}_a', count=str(arr.size)); fa.text = ' '.join(f'{v:.5f}' for v in arr.ravel())
            acc = ET.SubElement(ET.SubElement(src, 'technique_common'), 'accessor', source=f'#{gid}_{nm}_a', count=str(len(arr)), stride='3')
            for a in 'XYZ': ET.SubElement(acc, 'param', name=a, type='float')
        vt = ET.SubElement(mesh, 'vertices', id=f'{gid}_v'); ET.SubElement(vt, 'input', semantic='POSITION', source=f'#{gid}_pos')
        tr = ET.SubElement(mesh, 'triangles', count=str(len(tris)), material='m')
        ET.SubElement(tr, 'input', semantic='VERTEX', source=f'#{gid}_v', offset='0')
        ET.SubElement(tr, 'input', semantic='NORMAL', source=f'#{gid}_nrm', offset='1')
        idx = []
        for i in range(len(tris)):
            for j in range(3): idx += [3 * i + j, i]
        ET.SubElement(tr, 'p').text = ' '.join(map(str, idx))
        return gid
    def node(parent, n, mat):
        if n['t'] == 'g':
            el = ET.SubElement(parent, 'node', id=f'n{gcount[0]}_{sid(n["n"])[:40]}', name=n['n'])
            m = n.get('m', mat)
            if n.get('f'):
                gid = geometry(n['f'])
                if gid:
                    ig = ET.SubElement(el, 'instance_geometry', url=f'#{gid}')
                    tc = ET.SubElement(ET.SubElement(ig, 'bind_material'), 'technique_common')
                    ET.SubElement(tc, 'instance_material', symbol='m', target=f'#{mid.get(m, "mat0")}')
            for c in n.get('c', []): node(el, c, m)
        elif n['t'] == 'i':
            el = ET.SubElement(parent, 'node', name=n.get('n', n['d']))
            x, y, z, o = n['x'], n['y'], n['z'], n['o']
            ET.SubElement(el, 'matrix').text = ' '.join(f'{v:.6f}' for v in [x[0], y[0], z[0], o[0], x[1], y[1], z[1], o[1], x[2], y[2], z[2], o[2], 0, 0, 0, 1])
            ET.SubElement(el, 'instance_node', url=f'#def_{sid(n["d"])}')
    for name, dd in spec['defs'].items():
        el = ET.SubElement(lnodes, 'node', id=f'def_{sid(name)}', name=name)
        for c in dd['c']: node(el, c, None)
    vs = ET.SubElement(lvs, 'visual_scene', id='scene', name='Titik Temu')
    top = ET.SubElement(vs, 'node', id='TitikTemu', name='Titik Temu model (units m, origin SW site corner)')
    for n in spec['root']: node(top, n, None)
    ET.SubElement(ET.SubElement(root, 'scene'), 'instance_visual_scene', url='#scene')
    ET.ElementTree(root).write(path, xml_declaration=True, encoding='utf-8')
    print('dae', path, 'geometries', gcount[0])

if __name__ == '__main__':
    export(json.load(open(sys.argv[1])), sys.argv[2])
