import sys, json, re
sys.path.insert(0, '/home/claude/boards')
from build_dc import B, FACES, tb
import p1, p2, p3, p4
B = dict(B)
B.update({'hero1b': '50a964d667b87f16bf026a7e65b7aea7', 'gf': '348f4b106aeef7b7dd806933d0afa83a', 'l1': '5d94d1adc337b2e7072e8dd79b39d847', 'site': 'b806a439c83571c5b4b7c5ff96eb9e63',
          'secA': '7096df15eb111af463db6dfdb7d3a7c2', 'secB': 'd8859355ef21149a042731bae1bedcde', 'elS': 'ba96e37c2fd41eab95489014fd74bd11', 'elE': 'ffd8df44b3d7d1bc4671b4d7128dfaf2'})
IM = lambda k: f'/_blob/{B[k]}'
def dc(inner, title, w, h):
    assert '{{' not in inner and '}}' not in inner and 'file://' not in inner and 'data:' not in inner
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<style>
{FACES}
body{{margin:0}}
a{{color:#B4492B}}a:hover{{color:#8E3720}}
</style>
</helmet>
<div style="position:relative;width:{w}px;height:{h}px;overflow:hidden;text-transform:uppercase;background:#F4F1EA;font-family:'DM Sans', Arial, sans-serif;color:#1F2A2E;box-sizing:border-box">
{tb(inner)}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
  renderVals() {{
    return {{}};
  }}
}}
</script>
</body>
</html>
'''
root = '/tmp/claude-0/-home-claude/696fbe25-b3a1-58f2-ae57-2aad7225b91b/scratchpad/canvas'
spec = [('Main', p1, 'Sheet 01 · Concept + site', 1123, 1587), ('Sheet2', p2, 'Sheet 02 · Site plan 1:500 + GF plan 1:200', 1123, 1587),
        ('Sheet3', p3, 'Sheet 03 · L1 plan + section B–B 1:200, SoA, brief', 1123, 1587), ('Sheet4', p4, 'Sheet 04 · Section A–A + elevations 1:200, technical', 1587, 1123)]
for f, m, t, w, h in spec:
    s = dc(m.build(IM), 'Titik Temu — ' + t, w, h)
    open(f'{root}/project/{f}.dc.html', 'w').write(s)
    print(f, len(s), s.count('<img'), s.count('/_blob/'), re.findall(r'src="(?!/_blob|\./support)[^"]*"', s)[:3])
c = json.load(open(f'{root}/project/canvas.json'))
c['boards'] = {}; x = 0
for f, m, t, w, h in spec:
    c['boards'][f + '.dc.html'] = {'x': x, 'y': 0, 'w': w, 'h': h, 'title': t + (' (A3 landscape)' if w > h else ' (A3 portrait)')}; x += w + 80
c['order'] = [f + '.dc.html' for f, *_ in spec]
c['title'] = 'Titik Temu — Crit 1 Boards (A3)'
json.dump(c, open(f'{root}/project/canvas.json', 'w'), ensure_ascii=False)
print(json.dumps(c, ensure_ascii=False))
