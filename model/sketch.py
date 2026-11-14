"""Turn each interior render into (a) a graded colour image and (b) a hand-drawn style sketch with annotations."""
import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

D = '/home/claude/crit1/out/int/'
TITLES = {'kel': 'Kelantan stall · A2-1', 'trg': 'Terengganu stall · A2-2', 'jhr': 'Johor stall · A1-1', 'mlk': 'Melaka stall · A1-4',
          'pod': 'Tamu guest pod · A1-2', 'lobby': 'Lobby Simpul · Perlis', 'court': 'Court Talam · Pahang', 'cafe': 'Café · Perak',
          'sgr': 'Serambi Tengah · Selangor', 'nsn': 'Gerbang Selatan · N. Sembilan', 'png': 'Gallery Peta Rasa · P. Pinang',
          'kdh': 'Dapur Rewang · Kedah', 'mus': 'Musolla (male) · calm', 'fam': 'Family serambi · N. Sembilan'}
F_T = ImageFont.truetype('/home/claude/crit1/Caveat-700.ttf', 64)
F_N = ImageFont.truetype('/home/claude/crit1/Caveat-600.ttf', 40)
rng = np.random.default_rng(4)

def smooth_noise(h, w, scale, amp):
    n = rng.standard_normal((h // scale + 2, w // scale + 2)).astype(np.float32)
    return cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * amp

def grade(img):
    f = img.astype(np.float32) / 255
    f = np.clip((f - 0.5) * 1.06 + 0.5, 0, 1)                       # a touch more contrast
    h, w = f.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    f *= (1 - 0.18 * np.clip(r - 0.55, 0, 1) ** 1.6)[..., None]      # soft vignette
    return (f * 255).astype(np.uint8)

def sketch(name):
    col = cv2.imread(D + name + '.png'); ln = cv2.imread(D + name + '_line.png', 0)
    h, w = ln.shape
    # wash: flatten and lighten the colour render like marker / watercolour
    wash = col.copy()
    for _ in range(3): wash = cv2.bilateralFilter(wash, 9, 40, 9)
    hsv = cv2.cvtColor(wash, cv2.COLOR_BGR2HSV).astype(np.float32); hsv[..., 1] *= 0.78; hsv[..., 2] = np.round(hsv[..., 2] / 22) * 22
    wash = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    wash = 255 - (255 - wash) * 0.72
    paper = 0.94 + 0.06 * np.clip(smooth_noise(h, w, 3, 0.5) + smooth_noise(h, w, 40, 0.6), -1, 1)
    paper = np.clip(paper, 0.86, 1.0)[..., None] * np.array([0.985, 0.975, 1.0])[None, None, :]   # BGR: warm paper
    # ink: line render + edges of the colour render, wobbled a little
    g = cv2.cvtColor(col, cv2.COLOR_BGR2GRAY); g = cv2.GaussianBlur(g, (3, 3), 0)
    can = cv2.Canny(g, 28, 80)
    ink = np.minimum(255 - (255 - ln.astype(np.float32)) * 1.0, 255 - can.astype(np.float32) * 0.55)
    mx, my = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    ink = cv2.remap(ink, mx + smooth_noise(h, w, 60, 1.6), my + smooth_noise(h, w, 60, 1.6), cv2.INTER_LINEAR, borderValue=255)
    ink = cv2.erode(ink, np.ones((2, 2), np.uint8))                    # slightly heavier pen
    out = wash * paper * (ink / 255)[..., None]
    im = Image.fromarray(cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB))
    # notes with leaders, stacked in two margins
    notes = json.load(open(D + name + '_line.notes.json'))
    dr = ImageDraw.Draw(im)
    INK = (38, 42, 46)
    left = sorted([n for n in notes if n[1] < w / 2], key=lambda n: n[2]); right = sorted([n for n in notes if n[1] >= w / 2], key=lambda n: n[2])
    for side, lst in (('L', left), ('R', right)):
        ys = []
        for t, x, y, z in lst:
            x = min(max(x, 30), w - 30); y = min(max(y, 150), h - 40)
            ty = max(y, (ys[-1] + 74) if ys else 170); ty = min(ty, h - 60); ys.append(ty)
            tw = dr.textlength(t, font=F_N)
            tx = 46 if side == 'L' else w - 46 - tw
            ex = tx + tw + 12 if side == 'L' else tx - 12
            # leader: hand-ish two-segment line
            dr.line([(ex, ty + 22), ((ex + x) / 2, ty + 22 + (y - ty) * 0.15), (x, y)], fill=INK, width=3, joint='curve')
            dr.ellipse([x - 7, y - 7, x + 7, y + 7], outline=INK, width=3)
            pad = 8; dr.rounded_rectangle([tx - pad, ty - 2, tx + tw + pad, ty + 50], 10, fill=(252, 250, 244))
            dr.text((tx, ty), t, font=F_N, fill=INK)
    dr.text((48, 30), TITLES[name], font=F_T, fill=(180, 73, 43))
    im.save(D + name + '_sketch.jpg', quality=90)
    cv2.imwrite(D + name + '_render.jpg', grade(col), [cv2.IMWRITE_JPEG_QUALITY, 90])

for n in (sys.argv[1:] or TITLES): sketch(n); print('ok', n)
