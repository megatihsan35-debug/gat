"""Board collages in the reference style: pale grid sky, hatched clouds, gulls, peach sun, white cut-out people,
and an activity axo split into three tinted time-of-day bands with night lights."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import skp_build as K
from geom import B, S, d, mod

OUT = '/home/claude/crit1/out/board/'
rng = np.random.default_rng(11)

# ---------------------------------------------------------------- camera projection (same as three.js PerspectiveCamera.lookAt)
def projector(eye, tgt, fov, W, H):
    V = lambda p: np.array([p[0], p[2], -p[1]], float)
    E, T = V(eye), V(tgt); f = T - E; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f); t = math.tan(math.radians(fov) / 2); a = W / H
    def proj(p):
        dd = V(p) - E; xc, yc, zc = dd @ r, dd @ u, dd @ f
        return np.array([(xc / (zc * t * a) + 1) / 2 * W, (1 - yc / (zc * t)) / 2 * H]), zc
    return proj

# ---------------------------------------------------------------- sky
def sky(W, H, top=(205, 227, 222), bot=(240, 244, 239), grid=64):
    y = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top) * (1 - y) + np.array(bot) * y) * np.ones((1, W, 1))
    im = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    dr = ImageDraw.Draw(im, 'RGBA')
    for x in range(0, W, grid): dr.line([(x, 0), (x, H)], fill=(255, 255, 255, 120), width=2)
    for yy in range(0, H, grid): dr.line([(0, yy), (W, yy)], fill=(255, 255, 255, 120), width=2)
    return im

def sun(im, cx, cy, R):
    dr = ImageDraw.Draw(im, 'RGBA')
    dr.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(244, 196, 166, 235))
    n = 48
    for k in range(n):
        if k % 2: continue
        a0, a1 = 360 * k / n, 360 * (k + 1) / n
        dr.arc([cx - R * 1.18, cy - R * 1.18, cx + R * 1.18, cy + R * 1.18], a0, a1, fill=(255, 255, 255, 230), width=max(2, int(R * 0.025)))

def cloud(im, cx, cy, w, seed=0, alpha=235):
    r = np.random.default_rng(seed); W_, H_ = int(w * 1.3), int(w * 0.75)
    m = Image.new('L', (W_, H_), 0); dm = ImageDraw.Draw(m)
    base = H_ * 0.72
    dm.rectangle([W_ * 0.12, base - H_ * 0.12, W_ * 0.88, base], fill=255)
    for k in range(9):
        x = W_ * (0.15 + 0.7 * k / 8) + r.uniform(-0.04, 0.04) * W_
        rr = W_ * (0.09 + 0.12 * math.sin(math.pi * (k + 0.5) / 9)) * r.uniform(0.8, 1.15)
        dm.ellipse([x - rr, base - rr * 1.55, x + rr, base + rr * 0.15], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    body = Image.new('RGBA', (W_, H_), (255, 255, 255, 0)); body.putalpha(m.point(lambda v: int(v * alpha / 255)))
    # hatch on the lower half
    hatch = Image.new('L', (W_, H_), 0); dh = ImageDraw.Draw(hatch)
    for x in range(-H_, W_, max(5, int(w / 60))):
        dh.line([(x, H_), (x + H_, 0)], fill=255, width=max(1, int(w / 260)))
    grad = Image.linear_gradient('L').resize((W_, H_)).point(lambda v: max(0, v - 110) * 2)
    hm = ImageChops.multiply(ImageChops.multiply(hatch, m), grad)
    shade = Image.new('RGBA', (W_, H_), (150, 168, 172, 0)); shade.putalpha(hm.point(lambda v: int(v * 0.55)))
    body.alpha_composite(shade)
    # outline
    edge = m.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    ol = Image.new('RGBA', (W_, H_), (135, 150, 152, 0)); ol.putalpha(edge.point(lambda v: int(v * 0.7)))
    body.alpha_composite(ol)
    im.alpha_composite(body, (int(cx - W_ / 2), int(cy - H_ * 0.72)))

def gull(im, cx, cy, s, flip=1, ang=0.0):
    """stylised gull: two arched wings + body, white fill, grey line"""
    def bez(p0, p1, p2, n=16): return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]
    L = [(-1.0, -0.15), (-0.55, -0.55), (-0.08, 0.0)]; R_ = [(0.08, 0.0), (0.55, -0.6), (1.05, -0.2)]
    up = bez(*L) + bez(*R_)
    lo = bez((1.05, -0.2), (0.55, -0.35), (0.12, 0.12)) + bez((-0.12, 0.12), (-0.55, -0.3), (-1.0, -0.15))
    pts = up + lo
    ca, sa = math.cos(ang), math.sin(ang)
    P = [(cx + s * (x * flip * ca - y * sa), cy + s * (x * flip * sa + y * ca)) for x, y in pts]
    dr = ImageDraw.Draw(im, 'RGBA'); dr.polygon(P, fill=(255, 255, 255, 245)); dr.line(P + [P[0]], fill=(90, 100, 104, 230), width=max(2, int(s / 28)), joint='curve')
    dr.ellipse([cx - s * 0.12, cy - s * 0.05, cx + s * 0.12, cy + s * 0.2], fill=(255, 255, 255, 255), outline=(90, 100, 104, 230), width=max(1, int(s / 40)))

def person(im, x, y, h, kind=0, alpha=245):
    """white cut-out figure standing at (x, y) (feet), height h px"""
    dr = ImageDraw.Draw(im, 'RGBA'); w = h * 0.26; col = (255, 255, 255, alpha); ln = (120, 128, 132, 220); lw = max(1, int(h / 70))
    hr = h * 0.075
    head = [x - hr, y - h, x + hr, y - h + 2 * hr]
    sh, hip = y - h + 2.3 * hr, y - h * 0.48
    step = [0.18, -0.05, 0.3, 0.1][kind % 4] * w
    body = [(x - w * 0.5, sh + h * 0.03), (x + w * 0.5, sh + h * 0.03), (x + w * 0.42, hip), (x - w * 0.42, hip)]
    legs = [(x - w * 0.36, hip), (x - w * 0.05, hip), (x - w * 0.1 - step, y), (x - w * 0.34 - step, y)]
    legs2 = [(x + w * 0.05, hip), (x + w * 0.36, hip), (x + w * 0.34 + step, y), (x + w * 0.1 + step, y)]
    for poly in (legs, legs2, body): dr.polygon(poly, fill=col, outline=ln, width=lw)
    if kind % 3 == 1:  # bag / child
        dr.ellipse([x + w * 0.5, hip - h * 0.08, x + w * 0.85, hip + h * 0.05], fill=col, outline=ln, width=lw)
    dr.ellipse(head, fill=col, outline=ln, width=lw)

# ---------------------------------------------------------------- 1. hero aerial collage
def hero():
    ren = Image.open(OUT + 'hero.png').convert('RGBA'); W, H = ren.size
    im = sky(W, H); sun(im, int(W * 0.13), int(H * 0.17), int(W * 0.055))
    for cx, cy, w, sd in [(W * 0.33, H * 0.13, W * 0.24, 1), (W * 0.74, H * 0.07, W * 0.30, 2), (W * 0.95, H * 0.24, W * 0.2, 3)]:
        cloud(im, cx, cy, w, sd)
    im.alpha_composite(ren)
    # front clouds drifting over the corners (like the reference)
    for cx, cy, w, sd in [(W * 0.06, H * 0.5, W * 0.2, 4), (W * 0.97, H * 0.62, W * 0.22, 5)]:
        cloud(im, cx, cy, w, sd, alpha=215)
    for cx, cy, s, fl, a in [(W * 0.55, H * 0.12, W * 0.05, 1, -0.1), (W * 0.62, H * 0.2, W * 0.028, -1, 0.15), (W * 0.47, H * 0.22, W * 0.02, 1, 0.05), (W * 0.86, H * 0.38, W * 0.03, -1, -0.2)]:
        gull(im, cx, cy, s, fl, a)
    # people on the plaza / podium (projected)
    pr = projector([123, -56, 58], [57, 26, 2], 35, W, H)
    pts = [(P2[0], P2[1], 0.9) for P2 in [K.P2(b, r) for b, r in [(150, 21), (160, 22.5), (170, 21.5), (120, 22), (110, 23.5), (135, 24.5), (200, 21), (95, 24)]]]
    pts += [(B[0] + rr * math.sin(math.radians(bb)), B[1] + rr * math.cos(math.radians(bb)), 0.9) for bb, rr in [(150, 5), (200, 6.5), (100, 4), (60, 6), (250, 6), (300, 5)]]
    for k, p in enumerate(pts):
        (x, y), zc = pr(p); (x2, y2), _ = pr((p[0], p[1], p[2] + 1.7)); person(im, x, y, abs(y - y2) * 1.15, k)
    im.convert('RGB').save(OUT + 'hero_collage.jpg', quality=93)

# ---------------------------------------------------------------- 2. eye-level collage (Gerbang Selatan arrival)
def eye():
    ren = Image.open(OUT + 'eyeS.png').convert('RGBA'); W, H = ren.size
    im = sky(W, H); sun(im, int(W * 0.84), int(H * 0.12), int(W * 0.045))
    for cx, cy, w, sd in [(W * 0.2, H * 0.1, W * 0.28, 7), (W * 0.58, H * 0.06, W * 0.22, 8), (W * 0.97, H * 0.28, W * 0.2, 9)]:
        cloud(im, cx, cy, w, sd)
    im.alpha_composite(ren)
    for cx, cy, s, fl, a in [(W * 0.42, H * 0.16, W * 0.06, 1, -0.05), (W * 0.52, H * 0.25, W * 0.03, -1, 0.1), (W * 0.33, H * 0.27, W * 0.022, 1, 0.12), (W * 0.7, H * 0.13, W * 0.025, -1, -0.1)]:
        gull(im, cx, cy, s, fl, a)
    pr = projector([46.5, -7.5, 1.7], [60, 22, 7.5], 62, W, H)
    ppl = []
    for b, r, z in [(209, 19.6, 0.9), (215, 19.9, 0.9), (221, 20.4, 0.9), (205, 22.8, 0.6), (225, 23.2, 0.3), (213, 25.6, 0.0), (199, 26.5, 0.0), (230, 27.5, 0.0), (190, 23.4, 0.6)]:
        p = K.P2(b, r); ppl.append((p[0], p[1], z))
    ppl.sort(key=lambda p: -pr(p)[1])
    for k, p in enumerate(ppl):
        (x, y), zc = pr(p); (x2, y2), _ = pr((p[0], p[1], p[2] + 1.65)); person(im, x, y, abs(y - y2), k)
    im.convert('RGB').save(OUT + 'eye_collage.jpg', quality=93)

# ---------------------------------------------------------------- 3. activity axo in three bands (ref 1)
def activity():
    ren = Image.open(OUT + 'actaxo.png').convert('RGBA'); W, H = ren.size
    base = Image.new('RGBA', (W, H), (244, 241, 234, 255))
    # faint grid under the model like a drafting sheet
    dr0 = ImageDraw.Draw(base, 'RGBA')
    for x in range(0, W, 48): dr0.line([(x, 0), (x, H)], fill=(210, 214, 210, 120), width=1)
    for y in range(0, H, 48): dr0.line([(0, y), (W, y)], fill=(210, 214, 210, 120), width=1)
    base.alpha_composite(ren)
    pr = projector([66, -52, 88], [50, 24, 0], 33, W, H)
    x0, x1, x2, x3 = int(W * 0.04), int(W * 0.35), int(W * 0.655), int(W * 0.965); y0, y1 = int(H * 0.05), int(H * 0.95)
    out = base.copy()
    def band(xa, xb, rgb, k, mode):
        reg = base.crop((xa, y0, xb, y1)).convert('RGB'); arr = np.asarray(reg).astype(float) / 255
        c = np.array(rgb) / 255
        if mode == 'night': res = arr * c * 0.95 + 0.03
        else: res = arr * (1 - k) + (arr * c) * k
        out.paste(Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8)).convert('RGBA'), (xa, y0))
    band(x0, x1, (52, 72, 112), 1, 'night'); band(x1, x2, (255, 214, 120), 0.45, 'day'); band(x2, x3, (232, 150, 140), 0.38, 'wk')
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(glow, 'RGBA')
    def light(p, rad, col=(255, 214, 140)):
        (x, y), zc = pr(p)
        if x0 < x < x1 and y0 < y < y1:
            for k, a in ((3.2, 40), (1.9, 90), (1.0, 230)): dg.ellipse([x - rad * k, y - rad * k, x + rad * k, y + rad * k], fill=(*col, a))
    for b in np.arange(0, 360, 3): light((*K.P2(b, 8.95), 0.9 + 4.05), 5)                       # ring cove under the soffit
    for m in range(1, 21):
        b0, b1 = mod(m)
        if b1 < b0: b1 += 360
        for b in np.linspace(b0 + 2, b1 - 2, 4): light((*K.P2(b, 11.0), 0.9 + 3.1), 6, (255, 196, 120))
    for b in np.arange(0, 360, 20): light((*K.P2(b, 5.6), 0.9 + 0.8), 7, (255, 230, 170))
    for bx in [(41, 30), (46, 21), (55, 8), (64, 4), (75, 6), (84, 12), (88, 22)]: light((bx[0], bx[1], 4.0), 12, (255, 220, 150))
    for b in np.arange(0, 360, 6): light((*K.P2(b, 13.6, S), 5.4 + 3.6), 4, (255, 200, 140))
    glow = glow.filter(ImageFilter.GaussianBlur(4)); out.alpha_composite(glow)
    # people: day (many), weekend (crowds at the plaza), night (around the court)
    def crowd(xa, xb, n, zone, seed):
        r = np.random.default_rng(seed); placed = 0; tries = 0
        while placed < n and tries < n * 40:
            tries += 1
            if zone == 'court': b, rr, z = r.uniform(0, 360), r.uniform(2.5, 10.5), 0.9
            elif zone == 'podium': b, rr, z = r.uniform(80, 260), r.uniform(18.8, 24), 0.9
            else: b, rr, z = r.uniform(95, 175), r.uniform(23, 34), 0.05
            p = (B[0] + rr * math.sin(math.radians(b)), B[1] + rr * math.cos(math.radians(b)), z)
            (x, y), _ = pr(p); (x2, y2), _ = pr((p[0], p[1], z + 1.7))
            if not (xa + 10 < x < xb - 10 and y0 + 40 < y < y1 - 20): continue
            person(out, x, y, abs(y - y2) * 1.05, placed, 250 if zone != 'night' else 230); placed += 1
    crowd(x1, x2, 26, 'court', 3); crowd(x1, x2, 12, 'podium', 4)
    crowd(x2, x3, 22, 'plaza', 5); crowd(x2, x3, 14, 'podium', 6); crowd(x2, x3, 10, 'court', 7)
    crowd(x0, x1, 18, 'court', 8); crowd(x0, x1, 8, 'podium', 9)
    dr = ImageDraw.Draw(out, 'RGBA')
    for xa in (x0, x1, x2): dr.line([(xa, y0), (xa, y1)], fill=(255, 255, 255, 230), width=3)
    dr.line([(x3, y0), (x3, y1)], fill=(255, 255, 255, 230), width=3)
    out.convert('RGB').save(OUT + 'activity_bands.jpg', quality=93)
    return [(x0 / W, x1 / W, x2 / W, x3 / W), (y0 / H, y1 / H)]

if __name__ == '__main__':
    hero(); eye(); print(activity())
