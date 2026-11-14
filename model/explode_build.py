"""Exploded version of the Titik Temu model: GF + site stays, L1 lifted, roof lifted; room floors coloured by zone."""
import copy, json, math
import numpy as np
import skp_build as K
from skp_build import G, I, T, D
from m3d import prism, bsolid, polys, clean
from geom import ROOMS, B, S, d, QIBLA
from shapely.ops import unary_union, polylabel

DZ1, DZ2 = 12.0, 26.0                 # lift of Level 1 and of the roof

spec = K.build()
TAGKEY = {v: k for k, v in T.items()}
LAYER = {'pod': 'GF', 'gfw': 'GF', 'gfg': 'GF', 'gfd': 'GF', 'gfc': 'GF', 'stair': 'GF', 'lift': 'GF', 'furn': 'GF',
         'ground': 'GF', 'roads': 'GF', 'rib': 'GF', 'bike': 'GF',
         'l1s': 'L1', 'l1w': 'L1', 'l1g': 'L1', 'l1d': 'L1', 'l1c': 'L1', 'terr': 'L1', 'ocu': 'L1', 'crown': 'L1',
         'roof': 'RF', 'truss': 'RF', 'pv': 'RF', 'tank': 'RF'}
BINS = {'GF': [], 'L1': [], 'RF': []}

def shift(n, dz):
    n = copy.deepcopy(n)
    def go(x):
        if x['t'] == 'g':
            for f in x.get('f', []):
                f[0] = [[p[0], p[1], p[2] + dz] for p in f[0]]
                f[1] = [[[p[0], p[1], p[2] + dz] for p in h] for h in f[1]]
            for c in x.get('c', []): go(c)
        elif x['t'] == 'i':
            x['o'] = [x['o'][0], x['o'][1], x['o'][2] + dz]
    go(n); return n

# ---------------------------------------------------------------- sort the tagged groups into layers
def walk(n):
    if n['t'] != 'g': return
    key = TAGKEY.get(n.get('tag'))
    if key is None:
        for c in n.get('c', []): walk(c)
        return
    if key in LAYER: BINS[LAYER[key]].append(n)
    elif key == 'tree':
        keep = [c for c in n['c'] if c.get('n') in ('Court tree', 'Light well tree')]
        if keep: BINS['GF'].append(G('Court + light well trees', None, None, None, keep))
    elif key == 'fin':
        gf, l1 = [], []
        top_def = K.fin_def(K.ZSR_ROOF + 0.05 - K.ZSOF)            # small ring fin above GF slab level
        for i_ in n['c']:
            if i_['d'].endswith('h9050'):                            # small ring full height -> split at +5.000
                a = copy.deepcopy(i_); a['d'] = 'Terracotta lamella 90x400 h4100'; gf.append(a)
                b = copy.deepcopy(i_); b['d'] = top_def; b['o'] = [b['o'][0], b['o'][1], K.ZSOF]; l1.append(b)
            elif abs(i_['o'][2] - K.ZG) < 1e-3: gf.append(i_)
            else: l1.append(i_)
        BINS['GF'].append(G('Terracotta lamellas (GF)', None, None, None, gf))
        BINS['L1'].append(G('Terracotta lamellas (L1)', None, None, None, l1))
    elif key == 'core':
        pass                                                         # rebuilt below, split per level
    # dropped: basemap, context, ceilings, set-out, labels, section planes
for n in K.ROOT: walk(n)

# ---------------------------------------------------------------- core split by level
from shapely.geometry import Polygon
cuts = [dict(cut=K.rect_cut(o['c'], o['t'], o['w'], 0.45), zb=o['zb'], zt=o['zt']) for o in K.OPEN['CORE']]
zs = sorted({K.ZG, K.ZG + K.DOOR_H, K.ZSOF, K.ZL, K.ZL + K.DOOR_H, K.ZL1_TOP, K.Z_CORE, K.Z_LIFT})
bands = {'GF': [], 'L1': [], 'RF': []}
for k in range(len(zs) - 1):
    za, zb_ = zs[k], zs[k + 1]
    base = K.CORE_SHELL if zb_ <= K.Z_CORE + 1e-6 else K.LIFT_SHELL
    cc = [c['cut'] for c in cuts if c['zb'] <= za + 1e-6 and c['zt'] >= zb_ - 1e-6]
    g = base.difference(unary_union(cc)) if cc else base
    lv = 'GF' if zb_ <= K.ZSOF + 1e-6 else ('L1' if zb_ <= K.ZL1_TOP + 1e-6 else 'RF')
    bands[lv].append((za, zb_, g))
for lv, nm in (('GF', 'Core walls GF'), ('L1', 'Core walls L1'), ('RF', 'Core walls above roof')):
    BINS[lv].append(G(nm, None, 'TT Concrete', bsolid(bands[lv])))
BINS['RF'].append(G('Core roof slabs', None, 'TT Concrete',
                    prism(K.core1_stair.buffer(0.25, join_style=2), K.Z_CORE - 0.3, K.Z_CORE) + prism(K.core1_lifts.buffer(0.25, join_style=2), K.Z_LIFT - 0.3, K.Z_LIFT)))

# ---------------------------------------------------------------- zone floor colours
ZONES = {'pub': ('TT Zone public', '#F2C27A', 'Public: lobby, shops, café, toilets'),
         'semi': ('TT Zone semi-public', '#AFD58C', 'Semi-public: gallery, hall, prayer, first aid'),
         'priv': ('TT Zone admin', '#8EC3EA', 'Admin (staff only)'),
         'serv': ('TT Zone service', '#B9A9E3', 'Service: stores, plant, loading, refuse'),
         'circ': ('TT Zone circulation', '#D9D9D9', 'Circulation: stairs, lifts, corridors')}
for z_, (mn, hx, _) in ZONES.items(): K.mat(mn, hx)
LABELS = []
for level, ffl, lv in (('GF', K.ZG, 'GF'), ('L1', K.ZL, 'L1')):
    kids = []
    for zone, (mn, hx, _) in ZONES.items():
        geom = unary_union([r['poly'] for r in ROOMS if r['level'] == level and r['zone'] == zone])
        if geom.is_empty: continue
        kids.append(G(f'Zone floor – {mn.replace("TT Zone ", "")}', None, mn, prism(clean(geom.buffer(-0.03, join_style=2)), ffl, ffl + 0.03)))
    BINS[lv].append(G(f'{level} zone floors (colour by use)', None, None, None, kids))
    for r in ROOMS:
        if r['level'] != level or r['zone'] == 'open' or r['label'] in ('store', 'prep', 'JAN', ''): continue
        if r['code'] in ('A1', 'A2') and 'display' not in r['name']: continue
        q = r['poly'] if r['poly'].geom_type == 'Polygon' else max(r['poly'].geoms, key=lambda g: g.area)
        if q.area < 9 and r['code'] not in ('A1', 'A2'): continue
        c = polylabel(q, 0.05)
        a = sum(x['poly'].area for x in ROOMS if x['name'].startswith(r['label'])) if r['code'] in ('A1', 'A2') else r['poly'].area
        LABELS.append(dict(s=r['label'], a=round(a), p=[c.x, c.y, ffl + 0.05 + (DZ1 if lv == 'L1' else 0)]))

# ---------------------------------------------------------------- assemble
root = [G('GROUND FLOOR + SITE (in place)', None, None, None, BINS['GF']),
        shift(G(f'LEVEL 1 (lifted +{DZ1:g} m)', None, None, None, BINS['L1']), DZ1),
        shift(G(f'ROOF (lifted +{DZ2:g} m)', None, None, None, BINS['RF']), DZ2)]
used = set()
def uses(n):
    if n['t'] == 'i': used.add(n['d'])
    for c in n.get('c', []): uses(c)
for n in root: uses(n)
defs = {k: v for k, v in K.DEFS.items() if k in used}
out = dict(materials=K.MATS, defs=defs, root=root, tags=[], scenes=[], labels=LABELS,
           legend=[(hx, txt) for _, hx, txt in ZONES.values()], dz=[DZ1, DZ2])
json.dump(out, open('/home/claude/crit1/out/titiktemu_exploded.json', 'w'))
print('bins', {k: len(v) for k, v in BINS.items()}, 'labels', len(LABELS), 'defs', len(defs))
