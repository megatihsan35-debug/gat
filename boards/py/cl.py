import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
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

