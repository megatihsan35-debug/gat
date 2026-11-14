import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
def _poly(d, pts, s, ox, oy, fill, line, lw):
    P = [(ox + x * s, oy + y * s) for x, y in pts]; d.polygon(P, fill=255)
def figure(im, x, y, h, kind=0, flip=1, fill=(255, 255, 255, 250), line=(105, 112, 116, 235)):
    """white cut-out person, feet at (x, y), height h px; drawn 4x supersampled"""
    if h < 6: return
    S = 4; s = h * S; pad = int(0.35 * s); Wt, Ht = int(0.7 * s) + 2 * pad, int(1.12 * s) + pad
    t = Image.new('L', (Wt, Ht), 0); d = ImageDraw.Draw(t)
    ox, oy = Wt / 2, Ht - pad * 0.3; lw = max(2, int(s / 55))
    sc = 0.62 if kind == 2 else 1.0; ss = s * sc
    def P(pts): return [(flip * px, py) for px, py in pts]
    step = [0.07, 0.03, 0.05, 0.0, 0.06][kind % 5]
    if kind in (1, 4):   # baju kurung + tudung
        _poly(d, P([(-0.1, -0.56), (0.1, -0.56), (0.15, -0.015), (-0.15, -0.015)]), ss, ox, oy, fill, line, lw)
        _poly(d, P([(-0.115, -0.83), (0.115, -0.83), (0.105, -0.5), (-0.105, -0.5)]), ss, ox, oy, fill, line, lw)
        _poly(d, P([(-0.07, -0.99), (0.07, -0.99), (0.1, -0.9), (0.14, -0.74), (-0.14, -0.74), (-0.1, -0.9)]), ss, ox, oy, fill, line, lw)
        d.ellipse([ox - 0.062 * ss, oy - 1.0 * ss, ox + 0.062 * ss, oy - 0.875 * ss], fill=255)
    else:
        for sg in (-1, 1):   # legs
            st = step * sg
            _poly(d, P([(sg * 0.012, -0.52), (sg * 0.088, -0.52), (sg * 0.06 + st, 0), (sg * 0.02 + st, 0)]), ss, ox, oy, fill, line, lw)
        _poly(d, P([(-0.115, -0.84), (0.115, -0.84), (0.095, -0.5), (-0.095, -0.5)]), ss, ox, oy, fill, line, lw)
        d.ellipse([ox - 0.065 * ss, oy - 1.0 * ss, ox + 0.065 * ss, oy - 0.87 * ss], fill=255)
    for sg in (-1, 1):       # arms
        sw = (0.05 if kind % 2 else -0.04) * sg
        _poly(d, P([(sg * 0.105, -0.82), (sg * 0.14, -0.8), (sg * 0.15 + sw, -0.5), (sg * 0.12 + sw, -0.5)]), ss, ox, oy, fill, line, max(2, lw - 1))
    if kind == 3:            # shopping bag
        _poly(d, P([(0.15, -0.5), (0.27, -0.5), (0.27, -0.33), (0.15, -0.33)]), ss, ox, oy, fill, line, lw)
    k = max(3, (lw // 2) * 2 + 1); ring = ImageChops.subtract(t.filter(ImageFilter.MaxFilter(k)), t)
    out = Image.new('RGBA', (Wt, Ht), (0, 0, 0, 0))
    out.paste(Image.new('RGBA', (Wt, Ht), fill), (0, 0), t); out.paste(Image.new('RGBA', (Wt, Ht), line), (0, 0), ring)
    t = out.resize((max(1, Wt // S), max(1, Ht // S)), Image.LANCZOS)
    im.alpha_composite(t, (int(x - t.width / 2), int(y - (Ht - pad * 0.3) / S)))
