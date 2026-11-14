import pymupdf as fitz, json, sys, numpy as np
from PIL import Image, ImageDraw
d = fitz.open('/home/claude/boards/a1_upper.pdf')
info = json.load(open('img/truescale.json'))
dpi = int(sys.argv[1]); out = sys.argv[2]
for n in info:
    pg = {'gf': 1, 'l1': 1, 'site': 0}.get(n, 2); r = fitz.Rect(info[n]['rect'])
    pix = d[pg].get_pixmap(dpi=dpi, clip=r, alpha=False)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    if n in ('gf', 'l1'):
        k = dpi / 72; a = np.asarray(im)
        dr = ImageDraw.Draw(im)
        for g in d[pg].get_drawings():
            rr = g['rect']
            if rr.intersects(r) and not r.contains(rr) and rr.width < 40 and rr.height < 40 and g.get('fill') == (1.0, 1.0, 1.0):
                cx, cy = ((rr.x0 + rr.x1) / 2 - r.x0) * k, ((rr.y0 + rr.y1) / 2 - r.y0) * k; R = (rr.width / 2 + 1.5) * k
                ys, xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
                ring = ((xs - cx) ** 2 + (ys - cy) ** 2 > (R * 1.15) ** 2) & ((xs - cx) ** 2 + (ys - cy) ** 2 < (R * 1.6) ** 2)
                col = tuple(int(v) for v in np.median(a[ring], axis=0)) if ring.any() else (250, 249, 245)
                dr.ellipse([cx - R, cy - R, cx + R, cy + R], fill=col)
    im.save(f'{out}/{n}.png' if dpi < 200 else f'{out}/{n}.jpg', **({} if dpi < 200 else {'quality': 93}))
    print(n, im.size)
