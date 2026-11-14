import sys, importlib
sys.path.insert(0, '/home/claude/boards')
from render_local import page, IM
for n in (sys.argv[1:] or ['1', '2', '3', '4', '5']):
    mod = importlib.import_module(f's{n}')
    open(f'/home/claude/boards/out/s{n}.html', 'w').write(page(mod.build(IM), f'Titik Temu Sheet {n}', 1587, 1123))
