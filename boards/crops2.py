import pymupdf as fitz, json, sys
PDF = '/home/claude/boards/a1_clean.pdf'
d = fitz.open(PDF); s200 = 72 / 25.4 * 5; s500 = 72 / 25.4 * 2
def gf(x, y): return (-221 + s200 * x, 947 - s200 * y)
def l1(x, y): return (927 + s200 * x, 947 - s200 * y)
def sp(x, y): return (232.4 + s500 * x, 601.2 + s500 * (63.0 - y))
C = {}
a, b = gf(25.3, 43.3), gf(81.2, 1.8); C['gf'] = (1, fitz.Rect(a[0], a[1], b[0], b[1]))
a, b = l1(25.8, 43.3), l1(82.8, 1.8); C['l1'] = (1, fitz.Rect(a[0], a[1], b[0], b[1]))
a, b = sp(-4, 65.0), sp(116.9, -17.9); C['site'] = (0, fitz.Rect(a[0], a[1], b[0], b[1]))
C['secA'] = (2, fitz.Rect(190, 270, 1278, 512)); C['secB'] = (2, fitz.Rect(1381, 299, 2189, 512))
C['elS'] = (2, fitz.Rect(193, 804, 1274, 1010)); C['elE'] = (2, fitz.Rect(1324, 804, 2222, 1010))
dpi = int(sys.argv[1]) if len(sys.argv) > 1 else 60
info = {}
for n, (pg, r) in C.items():
    pix = d[pg].get_pixmap(dpi=dpi, clip=r, alpha=False)
    out = f'img/t_{n}.png' if dpi >= 200 else f'/tmp/claude-0/-home-claude/696fbe25-b3a1-58f2-ae57-2aad7225b91b/scratchpad/t_{n}.png'
    pix.save(out); info[n] = dict(wmm=round(r.width / 72 * 25.4, 2), hmm=round(r.height / 72 * 25.4, 2), wpx=round(r.width * 96 / 72, 2), hpx=round(r.height * 96 / 72, 2), rect=[round(v, 2) for v in r])
    print(n, info[n], pix.width, pix.height)
json.dump(info, open('img/truescale.json', 'w'), indent=1)
