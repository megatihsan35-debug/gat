import json, math, numpy as np, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '/home/claude/boards/py')
import cl
from fig import figure
from proj import projector
R = '/home/claude/boards/r/'; OUT = '/home/claude/boards/img/'
eye, tgt, fov = (123.86, -96.10, 102.31), (57, 19, 0), 32.76
W, H = 3369, 1920
RW, RH = 3600, 2400
pr0 = projector(eye, tgt, RW, RH, fov=fov)
ren = Image.open(R + 'hero_c.png').convert('RGBA'); flo = np.asarray(Image.open(R + 'hero_f.png').convert('L'))
BB = (447, 526, 2978, 2391)
DX, DY = 3345 - BB[2], 1905 - BB[3]
def pr(p): q = pr0(p); return np.array([q[0] + DX, q[1] + DY])
im = cl.sky(W, H, top=(198, 224, 218), bot=(236, 242, 236), grid=96)
cl.sun(im, int(W * 0.905), int(H * 0.15), int(W * 0.042))
for cx, cy, w, sd in [(W * 0.66, H * 0.08, W * 0.24, 2), (W * 0.985, H * 0.27, W * 0.18, 3)]:
    cl.cloud(im, cx, cy, w, sd, alpha=230)
# shift the render
ren = ren.crop(BB); im.alpha_composite(ren, (BB[0] + DX, BB[1] + DY))
# people (feet must land on a walkable pixel of the floor pass)
rng = np.random.default_rng(7); B = np.array([61.0, 22.0]); S = np.array([36.74, 31.95])
site = np.load('/home/claude/crit1/site.npy')
from shapely.geometry import Polygon, Point
SP = Polygon(site)
def ok(p, z):
    q = pr0((p[0], p[1], z)); x, y = int(q[0]), int(q[1])
    if not (2 <= x < RW - 2 and 2 <= y < RH - 6): return False
    if not (0 <= x + DX < W and 0 <= y + DY < H): return False
    return flo[y, x] > 200 and flo[y - 3, x] > 200 and flo[y + 3, x] > 200
people = []
def scatter(n, gen, z, tries=4000):
    c = 0; t = 0
    while c < n and t < tries:
        t += 1; p = gen()
        if ok(p, z) and all(np.hypot(*(p - q[0])) > 1.4 for q in people): people.append((p, z)); c += 1
pol = lambda C, r, b: C + np.array([math.sin(math.radians(b)), math.cos(math.radians(b))]) * r
scatter(14, lambda: pol(B, rng.uniform(2.3, 8.4), rng.uniform(0, 360)), 0.93)            # court
scatter(16, lambda: pol(B, rng.uniform(13.0, 14.0), rng.uniform(150, 330)), 5.45)       # roof walk deck
scatter(24, lambda: np.array([rng.uniform(70, 108), rng.uniform(-14, 14)]), 0.03)       # Dataran Temu + paths
scatter(10, lambda: np.array([rng.uniform(40, 76), rng.uniform(-6, 6)]), 0.03)          # road edge walk
scatter(8, lambda: np.array([rng.uniform(60, 86), rng.uniform(42, 60)]), 0.03)          # Taman Ulam
people.sort(key=lambda q: pr(( *q[0], q[1]))[1])
for k, (p, z) in enumerate(people):
    a = pr((p[0], p[1], z)); b = pr((p[0], p[1], z + 1.65))
    h = abs(a[1] - b[1]); kind = int(rng.integers(0, 5)); figure(im, a[0], a[1], h, kind, 1 if rng.random() < .5 else -1)
# front clouds + gulls
for cx, cy, w, sd in [(W * 0.47, H * 0.985, W * 0.17, 4), (W * 0.99, H * 0.86, W * 0.18, 5)]:
    cl.cloud(im, cx, cy, w, sd, alpha=225)
for cx, cy, s, fl, a in [(W * 0.31, H * 0.30, W * 0.036, 1, -0.1), (W * 0.37, H * 0.37, W * 0.02, -1, 0.15), (W * 0.27, H * 0.40, W * 0.016, 1, 0.05)]:
    cl.gull(im, cx, cy, s, fl, a)
im.convert('RGB').save(OUT + 'hero1.jpg', quality=92)
# label anchors in board px (1123 x 640)
core = (43.14, 29.32)
A = {'crown': (core[0] + 1.5, core[1] - 1.0, 13.3), 'court': (61, 22, 0.95), 'hall': (*pol(B, 17.5, 112), 11.8), 'kecil': (*pol(S, 6, 330), 9.9),
     'plaza': (89.4, 2.1, 0.05), 'timur': (98.5, 6.0, 4.0), 'deck': (*pol(B, 13.0, 205), 5.5), 'ulam': (73.0, 51.5, 0.1), 'selatan': (62.0, 1.0, 4.0)}
json.dump({k: (pr(v) / 3).round(1).tolist() for k, v in A.items()}, open(OUT + 'hero1_anchors.json', 'w'), indent=1)
print(json.load(open(OUT + 'hero1_anchors.json')), len(people))
