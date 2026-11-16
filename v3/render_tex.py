"""Procedural textures for the render model (seamless tiles, JPG/PNG). Each texture covers TILE[name] metres.
python3 render_tex.py -> out/render/textures/*"""
import os, math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'out', 'render', 'textures'); os.makedirs(TEX, exist_ok=True)
rng = np.random.default_rng(7)

def noise(n, scale, octaves=4, seed=0):
    """seamless value noise in [0,1] (n x n), sum of octaves of wrapped bilinear-upsampled random grids"""
    r = np.random.default_rng(seed); out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        g = max(2, int(scale * 2 ** o))
        a = r.random((g, g))
        x = np.linspace(0, g, n, endpoint=False); i0 = np.floor(x).astype(int); f = x - i0; i1 = (i0 + 1) % g
        f = f * f * (3 - 2 * f)
        row = a[i0][:, i0] * (1 - f)[None, :] + a[i0][:, i1] * f[None, :]
        row2 = a[i1][:, i0] * (1 - f)[None, :] + a[i1][:, i1] * f[None, :]
        out += amp * (row * (1 - f)[:, None] + row2 * f[:, None]); tot += amp; amp *= 0.5
    return out / tot

def rgb(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
def save(arr, name, q=88):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    p = os.path.join(TEX, name); im.save(p, quality=q) if name.endswith('.jpg') else im.save(p); return p
def mix(c0, c1, t): return c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]

TILE = {}
def grass(n=512):
    t = noise(n, 6, 5, 1); fine = noise(n, 64, 2, 2)
    a = mix(rgb('#5F8A3E'), rgb('#8BAE55'), np.clip(t * 1.2 - 0.1, 0, 1)) * (0.85 + 0.3 * fine[..., None])
    TILE['grass'] = 6.0; return save(a, 'grass.jpg')
def asphalt(n=512):
    t = noise(n, 40, 3, 3); s = (rng.random((n, n)) > 0.985) * 40
    a = np.stack([52 + 22 * t + s, 54 + 22 * t + s, 58 + 22 * t + s], -1); TILE['asphalt'] = 4.0; return save(a, 'asphalt.jpg')
def pavers(n=512, w=0.6, h=0.3, tile=2.4, base='#CFC9BE', var=14, joint='#9E978B', name='pavers.jpg', key='pavers'):
    """stretcher-bond granite pavers"""
    t = noise(n, 50, 3, 4); a = np.zeros((n, n, 3)); px = n / tile
    yy, xx = np.mgrid[0:n, 0:n] / px
    row = np.floor(yy / h).astype(int); off = (row % 2) * w / 2
    col = np.floor((xx + off) / w).astype(int)
    cid = (row * 31 + col * 17) % 97; shade = (cid / 97.0 - 0.5) * var
    a[:] = rgb(base)[None, None, :] + shade[..., None] + (t[..., None] - 0.5) * 20
    jx = ((xx + off) % w) < 0.006 * 1.6; jy = (yy % h) < 0.006 * 1.6
    a[jx | jy] = rgb(joint); TILE[key] = tile; return save(a, name)
def terrazzo(n=1024, base='#C9C6C0', chips=('#8E8A84', '#F2F0EC', '#6F7C86', '#B9A68A', '#E5E1D8'), tile=1.5, name='terrazzo.jpg', key='terrazzo', dens=900):
    t = noise(n, 8, 3, 5); a = np.zeros((n, n, 3)) + rgb(base)[None, None, :] + (t[..., None] - 0.5) * 10
    im = Image.fromarray(a.astype(np.uint8)); dr = ImageDraw.Draw(im); r = np.random.default_rng(11)
    for _ in range(dens):
        x, y = r.integers(0, n, 2); s = r.integers(2, 9); c = tuple(int(v) for v in rgb(chips[r.integers(len(chips))]))
        pts = [(x + s * math.cos(a_) * r.uniform(0.6, 1.2), y + s * math.sin(a_) * r.uniform(0.6, 1.2)) for a_ in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
        for dx in (-n, 0, n):
            for dy in (-n, 0, n): dr.polygon([(px + dx, py + dy) for px, py in pts], fill=c)
    TILE[key] = tile; im.save(os.path.join(TEX, name), quality=90); return name
def timber(n=512, base='#9C6B3F', dark='#6E4426', tile=1.2, name='timber.jpg', key='timber'):
    yy, xx = np.mgrid[0:n, 0:n] / n
    g = noise(n, 3, 3, 6); streak = 0.5 + 0.5 * np.sin((yy * 38 + g * 6) * math.pi * 2)
    boards = ((xx * 8) % 1 < 0.012)
    a = mix(rgb(base), rgb(dark), streak * 0.45 + noise(n, 20, 2, 7) * 0.25); a[boards] = rgb(dark) * 0.8
    TILE[key] = tile; return save(a, name)
def grc(n=512, base='#ECEAE5', tile=3.0, name='grc.jpg', key='grc', joints=True):
    t = noise(n, 10, 4, 8); a = np.zeros((n, n, 3)) + rgb(base)[None, None, :] + (t[..., None] - 0.5) * 9
    if joints:
        a[:4, :] -= 28; a[:, :4] -= 28
    TILE[key] = tile; return save(a, name)
def roof(n=512, base='#E8EAEC', tile=2.4, name='roof.jpg', key='roof'):
    """aluminium composite roof panels with a fine seam"""
    t = noise(n, 6, 3, 9); a = np.zeros((n, n, 3)) + rgb(base)[None, None, :] + (t[..., None] - 0.5) * 8
    a[:, :3] -= 40; a[:3, :] -= 20; TILE[key] = tile; return save(a, name)
def fin(n=256, base='#8F7E62', tile=1.0, name='fin.jpg', key='fin'):
    yy, xx = np.mgrid[0:n, 0:n]; s = noise(n, 60, 2, 10)
    a = np.zeros((n, n, 3)) + rgb(base)[None, None, :] + (np.sin(xx * 0.9) * 0.5 + s - 0.5)[..., None] * 10
    TILE[key] = tile; return save(a, name)
def concrete(n=512, base='#D4D0C8', tile=4.0, name='concrete.jpg', key='concrete'):
    t = noise(n, 12, 5, 12); a = np.zeros((n, n, 3)) + rgb(base)[None, None, :] + (t[..., None] - 0.5) * 22
    TILE[key] = tile; return save(a, name)
def leaves(n=512, c0='#3E6B2E', c1='#7FA84A', tile=1.5, name='leaves.jpg', key='leaves', flowers=None):
    t = noise(n, 24, 4, 13); f = noise(n, 90, 2, 14)
    a = mix(rgb(c0), rgb(c1), np.clip(t * 1.3 - 0.15, 0, 1)) * (0.7 + 0.5 * f[..., None])
    if flowers:
        m = noise(n, 30, 2, 15) > 0.62; a[m] = rgb(flowers) * (0.8 + 0.3 * f[m][:, None])
    TILE[key] = tile; return save(a, name)
def soil(n=256, tile=1.0):
    t = noise(n, 40, 3, 16); a = mix(rgb('#4A3A2A'), rgb('#7A6248'), t); TILE['soil'] = tile; return save(a, 'soil.jpg')
def water(n=256, tile=2.0):
    t = noise(n, 8, 4, 17); a = mix(rgb('#2F7FA3'), rgb('#7CC3DD'), t); TILE['water'] = tile; return save(a, 'water.jpg')
def fabric_stripe(n=256, c0='#F6EBD2', c1='#6FB3D2', tile=1.0, name='stall.jpg', key='stall'):
    yy, xx = np.mgrid[0:n, 0:n] / n; m = ((xx * 6) % 1 < 0.5)
    a = np.where(m[..., None], rgb(c1)[None, None, :], rgb(c0)[None, None, :]); TILE[key] = tile; return save(a, name)

def tenun_alpha(n=512, tile=1.2):
    """perforated tenun check: champagne aluminium with square holes (PNG with alpha)"""
    a = np.zeros((n, n, 4)); a[..., :3] = rgb('#CBB98C'); a[..., 3] = 255
    yy, xx = np.mgrid[0:n, 0:n]; cell = n // 8
    hole = ((xx % cell) > cell * 0.2) & ((xx % cell) < cell * 0.8) & ((yy % cell) > cell * 0.2) & ((yy % cell) < cell * 0.8)
    big = (((xx // cell) + (yy // cell)) % 3 == 0)
    a[hole & ~big, 3] = 0; a[hole & big, 3] = 70
    TILE['tenun'] = tile; Image.fromarray(a.astype(np.uint8), 'RGBA').save(os.path.join(TEX, 'tenun.png')); return 'tenun.png'

def state_screens():
    """each state's screen pattern + feature back wall, drawn with the CAD patterns of interior_sheets"""
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from cad import Drawing, Sheet
    import interior_sheets as IS, interior as IN
    out = {}
    for sk, v in IN.ST.items():
        for kind, (w, h) in (('screen', (2.4, 0.6)), ('back', (4.0, 4.4))):
            if kind == 'back' and sk not in IN.SHOP.values(): continue
            D = Drawing('t')
            if kind == 'screen':
                D.poly(__import__('shapely.geometry', fromlist=['box']).box(0, 0, w, h), 'A-ELEV', fill=IN.tint(v[4], 0.75), edge=None, z=1)
                IS.pattern(D, sk, 0, 0, w, h, v[4])
            else:
                IS.back_pattern(D, sk, 0, 0, w, h, v[4])
            S = Sheet(w * 100, h * 100); S.place(D, 10, (0, 0), (0, 0))
            p = os.path.join(TEX, f'{kind}_{sk}.jpg')
            S.fig.savefig(p, dpi=int(1024 / (w * 100 / 25.4)), pil_kwargs={'quality': 88}); S.close()
            out[f'{kind}_{sk}'] = (p, w, h)
    return out

def build_all():
    grass(); asphalt(); pavers(); pavers(base='#B9B3A7', joint='#8A8478', name='pavers_dark.jpg', key='pavers_dark', var=20)
    terrazzo(); terrazzo(base='#E3E0DA', name='terrazzo_light.jpg', key='terrazzo_light', tile=1.2)
    timber(); timber(base='#B98A5E', dark='#8A5F3A', name='timber_light.jpg', key='timber_light')
    grc(); grc(base='#F4F2EE', name='plaster.jpg', key='plaster', joints=False); roof(); fin(); concrete(); concrete(base='#C9C2B4', name='plinth.jpg', key='plinth', tile=3.0)
    leaves(); leaves(c0='#5C7F33', c1='#9DBF5A', name='leaves_light.jpg', key='leaves_light'); leaves(c0='#466B2C', c1='#86A64A', name='leaves_pink.jpg', key='leaves_pink', flowers='#E79AB8')
    leaves(c0='#2F5A2A', c1='#5E8F3C', name='shrub.jpg', key='shrub', tile=0.8)
    soil(); water(); fabric_stripe(); tenun_alpha()
    st = state_screens()
    for k, (p, w, h) in st.items(): TILE[k] = (w, h)
    import json; json.dump(TILE, open(os.path.join(TEX, 'tiles.json'), 'w'), indent=1)
    return TILE

if __name__ == '__main__':
    t = build_all(); print(len(t), 'textures')
