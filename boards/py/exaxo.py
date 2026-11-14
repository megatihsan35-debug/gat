import json, math, numpy as np, sys
from PIL import Image, ImageDraw, ImageFilter
import cl
from fig import figure
from proj import projector
R = '/home/claude/boards/r/'; OUT = '/home/claude/boards/img/'
eye, tgt = (-66.26, -147.75, 158.16), (56, 22, 22)
RW, RH = 2900, 1900; BB = (673, 130, 2687, 1692)
W, H = 1920, 1488; k = min(W / (BB[2] - BB[0]), H / (BB[3] - BB[1]))
ox = (W - (BB[2] - BB[0]) * k) / 2; oy = (H - (BB[3] - BB[1]) * k) / 2
pr0 = projector(eye, tgt, RW, RH, ortho=44)
def pr(p): q = pr0(p); return np.array([(q[0] - BB[0]) * k + ox, (q[1] - BB[1]) * k + oy])
def load(n):
    im = Image.open(R + n).crop(BB); return im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
day, night = load('ex_c.png'), load('ex_n.png')
flo = np.asarray(Image.open(R + 'ex_f.png').convert('L'))
PAPER = (244, 241, 234)
B = np.array([61.0, 22.0]); S = np.array([36.74, 31.95])
pol = lambda C, r, b: C + np.array([math.sin(math.radians(b)), math.cos(math.radians(b))]) * r
# band edges from the geometry
xs = {n: pr(p)[0] for n, p in {'S': (*S, 0.9), 'core': (43.1, 29.3, 0.9), 'B': (*B, 0.9), 'hallL1': (*pol(B, 16, 100), 23.4)}.items()}
print({n: round(v) for n, v in xs.items()})
x0 = 30; x3 = 1520; bw = (x3 - x0) / 3; x1 = int(x0 + bw); x2 = int(x0 + 2 * bw)
gap = 14; y0, y1 = 70, H - 30
bands = [(x0, x1 - gap // 2, 'night'), (x1 + gap // 2, x2 - gap // 2, 'day'), (x2 + gap // 2, x3, 'sun')]
base = Image.new('RGBA', (W, H), PAPER + (255,))
dr = ImageDraw.Draw(base, 'RGBA')
for x in range(0, W, 48): dr.line([(x, 0), (x, H)], fill=(214, 214, 206, 110), width=1)
for y in range(0, H, 48): dr.line([(0, y), (W, y)], fill=(214, 214, 206, 110), width=1)
COL = {'night': (44, 62, 100), 'day': (248, 228, 168), 'sun': (244, 196, 186)}
plain = base.copy(); plain.alpha_composite(day, (round(ox), round(oy)))
out = plain.copy()
for xa, xb, kind in bands:
    reg = Image.new('RGBA', (xb - xa, y1 - y0), COL[kind] + (255 if kind == 'night' else 235,))
    src = (night if kind == 'night' else day)
    tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); tmp.alpha_composite(src, (round(ox), round(oy)))
    tile = tmp.crop((xa, y0, xb, y1)); arr = np.asarray(tile).astype(float) / 255
    rgb, a = arr[..., :3], arr[..., 3:]
    c = np.array(COL[kind]) / 255
    if kind == 'night': rgb = rgb * 0.82 + c * 0.18
    else: rgb = rgb * (1 - 0.16) + rgb * c * 0.16
    tile = Image.fromarray((np.dstack([rgb, a]) * 255).clip(0, 255).astype(np.uint8))
    reg.alpha_composite(tile); out.paste(reg, (xa, y0))
# night glows
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(glow, 'RGBA')
def light(p, rad, col=(255, 214, 140)):
    x, y = pr(p)
    if bands[0][0] < x < bands[0][1] and y0 < y < y1:
        for kk, a in ((3.0, 35), (1.8, 80), (0.9, 220)): dg.ellipse([x - rad * kk, y - rad * kk, x + rad * kk, y + rad * kk], fill=(*col, a))
for b in np.arange(0, 360, 15): light((*pol(S, 3.2, b), 0.9 + 3.6), 5)
for b in np.arange(0, 360, 20): light((*pol(S, 3.2, b), 23.4 + 3.4), 5)
for b in np.arange(220, 320, 12): light((*pol(B, 19.9, b), 0.95), 4, (255, 226, 160))
glow = glow.filter(ImageFilter.GaussianBlur(3)); out.alpha_composite(glow)
# people on visible floors
rng = np.random.default_rng(5); people = []
def ok(p, z):
    q = pr0((p[0], p[1], z)); x, y = int(q[0]), int(q[1])
    if not (3 <= x < RW - 3 and 3 <= y < RH - 6): return False
    return flo[y, x] > 200 and flo[y - 3, x] > 200 and flo[y + 4, x] > 200
def scatter(n, gen, z, tries=3000):
    c = t = 0
    while c < n and t < tries:
        t += 1; p = gen()
        if ok(p, z) and all(np.hypot(*(p - q[0])) > 1.3 or abs(z - q[1]) > 1 for q in people): people.append((p, z)); c += 1
scatter(22, lambda: pol(B, rng.uniform(2.3, 8.5), rng.uniform(0, 360)), 0.93)          # Talam court
scatter(10, lambda: pol(B, rng.uniform(9.3, 10.8), rng.uniform(0, 360)), 0.93)         # verandah
scatter(8, lambda: pol(B, rng.uniform(11.5, 14.4), rng.uniform(0, 360)), 0.92)         # shops / cafe
scatter(10, lambda: pol(B, rng.uniform(11.4, 14.2), rng.uniform(150, 360)), 18 + 5.45) # roof walk
scatter(12, lambda: pol(B, rng.uniform(11.5, 21), rng.uniform(42, 147)), 18 + 5.42)   # gallery + hall
scatter(9, lambda: pol(S, rng.uniform(5.0, 10.2), rng.uniform(220, 400)), 18 + 5.42)  # musolla, family
scatter(5, lambda: pol(S, rng.uniform(5.0, 10.2), rng.uniform(40, 220)), 18 + 5.42)   # admin
scatter(6, lambda: pol(S, rng.uniform(4.6, 10.2), rng.uniform(0, 360)), 0.92)         # GF small ring
scatter(10, lambda: pol(B, rng.uniform(19.5, 23), rng.uniform(150, 300)), 0.92)       # podium edge
people.sort(key=lambda q: pr((*q[0], q[1]))[1])
for p, z in people:
    a = pr((p[0], p[1], z)); b = pr((p[0], p[1], z + 1.65)); h = abs(a[1] - b[1])
    figure(out, a[0], a[1], h * 1.1, int(rng.integers(0, 5)), 1 if rng.random() < .5 else -1)
out.convert('RGB').save(OUT + 'exaxo.jpg', quality=92)
pt = lambda p: (pr(p) / 3).round(1).tolist()
A = {'roofhall': pt((*pol(B, 16.5, 95), 38 + 12.5)), 'roofsmall': pt((*S, 38 + 9.9)), 'crown': pt((44.6, 28.3, 18 + 13.0)),
     'musolla': pt((*pol(S, 8.0, 292.3), 18 + 5.4)), 'admin': pt((*pol(S, 7.5, 150), 18 + 5.4)), 'family': pt((*pol(S, 7.6, 337), 18 + 5.4)),
     'terrace': pt((*pol(B, 12.8, 230), 18 + 5.45)), 'oculus': pt((*pol(B, 7.5, 200), 18 + 6.8)), 'hall': pt((*pol(B, 16.0, 112), 18 + 5.4)),
     'gallery': pt((*pol(B, 16.0, 49), 18 + 5.4)), 'court': pt((*pol(B, 5.0, 230), 0.9)), 'shops': pt((*pol(B, 13.5, 175), 0.9)),
     'cafe': pt((*pol(B, 14.5, 121), 0.9)), 'lobby': pt((46.7, 23.6, 0.9)), 'service': pt((*pol(S, 7.5, 0), 0.9)), 'staffwc': pt((*pol(S, 7.5, 180), 0.9)),
     'toilets': pt((*pol(B, 14.5, 323), 0.9))}
json.dump(dict(anchors=A, bands=[(round(a / 3, 1), round(b / 3, 1), kk) for a, b, kk in bands], y=[round(y0 / 3, 1), round(y1 / 3, 1)]), open(OUT + 'exaxo.json', 'w'), indent=1)
print(len(people), A)
