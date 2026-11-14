import sys, os
sys.path.insert(0, '/home/claude/boards')
import board1
FM = '/home/claude/r3d/node_modules/@fontsource/'
FACES = ''.join(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:{st};src:url('file://{FM}{pk}/files/{pk}-latin-{w}-{st}.woff2') format('woff2');}}"
                for fam, pk, w, st in [('Syne', 'syne', 600, 'normal'), ('Syne', 'syne', 700, 'normal'), ('Syne', 'syne', 800, 'normal'),
                                       ('DM Sans', 'dm-sans', 400, 'normal'), ('DM Sans', 'dm-sans', 400, 'italic'), ('DM Sans', 'dm-sans', 500, 'normal'), ('DM Sans', 'dm-sans', 700, 'normal'), ('DM Sans', 'dm-sans', 700, 'italic')])
IM = lambda k: f'file:///home/claude/boards/img/{k}.jpg'
def page(inner, title, w=1123, h=1587):
    root = f'position:relative;width:{w}px;height:{h}px;overflow:hidden;text-transform:uppercase;background:#F4F1EA;font-family:"DM Sans", Arial, sans-serif;color:#1F2A2E'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><style>{FACES} body{{margin:0}} *{{box-sizing:border-box}}</style></head><body>'
            f"<div style='{root}'>{inner}</div></body></html>")
if __name__ == '__main__':
    import importlib
    which = sys.argv[1:] or ['1', '2', '3', '4']
    for n in which:
        mod = importlib.import_module(f'p{n}')
        w, h = (1587, 1123) if n == '4' else (1123, 1587)
        open(f'/home/claude/boards/out/p{n}.html', 'w').write(page(mod.build(IM), f'Titik Temu Sheet {n}', w, h))
