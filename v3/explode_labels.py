"""Labels + leader lines on the exploded render -> out/render/explode/TITIK-TEMU_EXPLODED-AXO.png"""
import os, json
from PIL import Image, ImageDraw, ImageFont
ED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'render', 'explode')
F = '/usr/share/fonts/opentype/inter/Inter-{}.otf'
DESC = {
    'ROOF': '3-TIER WAVE ROOF  ·  FUNNEL + TENUN LINING  ·  CLERESTORIES  ·  MAST +30.000',
    'L2': 'INNER RING ONLY  ·  GALLERY  ·  SURAU  ·  FAMILY WAITING',
    'L1': 'INNER RING  ·  FREE-STANDING RING BRIDGE + GERAI LIPAT  ·  OUTER RING',
    'GF': 'TALAM COURT  ·  ARCADE  ·  8 STATE SHOPS  ·  CAFE  ·  4 GATES',
}
def main():
    im = Image.open(os.path.join(ED, 'exploded_raw.png')).convert('RGB'); W, H = im.size; s = W / 2400
    lab = json.load(open(os.path.join(ED, 'labels2d.json')))
    d = ImageDraw.Draw(im)
    fb, fl, fs, ft = (ImageFont.truetype(F.format(w), int(sz * s)) for w, sz in (('Bold', 34), ('Medium', 24), ('Regular', 21), ('Bold', 44)))
    ink = (38, 42, 48); grey = (110, 116, 124); acc = (176, 128, 62)
    x0 = int(70 * s)
    d.text((x0, int(60 * s)), 'TITIK TEMU  —  EXPLODED AXONOMETRIC', font=ft, fill=ink)
    d.text((x0, int(118 * s)), 'SIMPUL RASA SEMENANJUNG  ·  ESPLANADE LOCAL COMMERCIAL HUB, TEMERLOH', font=fs, fill=grey)
    for b in ('ROOF', 'L2', 'L1', 'GF'):
        L = lab[b]; ax, ay = L['x'] * W, L['y'] * H
        ty = ay - 30 * s
        name = L['name']; lvl = L['level'] if b != 'ROOF' else '+10.200 TO +19.800'
        d.text((x0, ty), name, font=fb, fill=ink)
        nw = d.textlength(name, font=fb)
        d.text((x0 + nw + 18 * s, ty + 8 * s), lvl, font=fl, fill=acc)
        d.text((x0, ty + 46 * s), DESC[b], font=fs, fill=grey)
        lx = x0 + max(nw + 18 * s + d.textlength(lvl, font=fl), d.textlength(DESC[b], font=fs)) + 24 * s
        if lx < ax - 20 * s:
            d.line([(lx, ty + 22 * s), (ax - 8 * s, ty + 22 * s), (ax - 8 * s, ay)], fill=(150, 154, 160), width=max(1, int(2 * s)))
            d.ellipse([ax - 14 * s, ay - 6 * s, ax - 2 * s, ay + 6 * s], fill=acc)
        d.line([(x0, ty + 82 * s), (x0 + 120 * s, ty + 82 * s)], fill=acc, width=max(1, int(3 * s)))
    off = json.load(open(os.path.join(ED, 'explode.json')))['off']
    d.text((x0, H - 70 * s), ('SITE ±0.000 WITH GROUND FLOOR ON THE +0.900 PLINTH  ·  FLOORS LIFTED {} M FOR CLARITY  ·  VIEW FROM THE SOUTH-EAST').format(' / '.join(str(int(off[b])) for b in ('L1', 'L2', 'ROOF'))),
           font=fs, fill=grey)
    out = os.path.join(ED, 'TITIK-TEMU_EXPLODED-AXO.png'); im.save(out); print(out, im.size)
if __name__ == '__main__': main()
