import sys; sys.path.insert(0, '/home/claude/mock')
exec(open('/home/claude/mock/kit.py').read()); exec(open('/home/claude/mock/kit2.py').read()); exec(open('/home/claude/mock/kit3.py').read())
import building as GMOD
import geom as GM
# page plan: 1 cover, 2 overview, then site pages
order = [(k, h) for k in range(1, NL + 1) for h in ('WEST', 'EAST') if LAYERS[k].intersection(box(*HALVES[h][:1], YB, HALVES[h][1], YT)).area >= 1]
pages = {}
for i, (k, h) in enumerate(order): pages.setdefault(k, []).append(3 + i)
cover(); overview(pages)
for k, h in order: site_page(k, h)
building_pages(); building_page3(); assembly()
c.save(); print('pages', PAGE[0], order)
