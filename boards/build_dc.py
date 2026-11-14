import re, json, sys
sys.path.insert(0, '/home/claude/boards')
import board1, board2
B = {'hero1': '660c3cb4f6c2b60f0187c0bd4fd8f648', 'exaxo': '4c71001b8d5ce3842c8753f4c6f8a956', 'sky2': 'ef2f4ca2100783467a7a86c008a3ff46', 'map': 'f51186af51a99befcb746cc9525c21d8',
     'formgen': 'f450bfdcf3da4436ca47c831002c66b5', 'synth': 'b8fa169f9d24173c938e103c859aa42f', 'siteplan': 'e45a80b7e506d8f4d7aa480f224ad16c', 'p8': '9370b869e0f11e129e54cf41c7377aec',
     'pbait': '1bb3279e56f60f4c7d40dd6481e0b839', 'pka': '8c74b3e21226c04fb2f513731bb38db4', 'gf': '6c84f4afc79206344a29c88da497c1d4', 'l1': 'fd504af4db50e12c2913a319ea774606',
     'roof': '6dfdc501b32fac48a4a9ff6a98ada2c2', 'secA': '3af181dbfef2ed1263154f4770da27c2', 'secB': '1cc9ee1813be6b9c46c9a922b8c2a2db', 'elS': 'b7857bfd7258c674186a8f2178e855a2',
     'elE': '063a6759e1ea95f95c0c35f3756da8bd', 'i_court': '52da09dfdedb5375712d618bd1c4e9d2', 'i_lobby': 'dfc4e880afedbb11d8982fb711339721', 'i_hall': '3896989cf0cbfd2f3aedb05a18bdb8a4',
     'i_gate': 'a3f13d07205569d6a1267972e3ad1c64', 'struct': 'c4fea326337781fc8ce8f6ac88b93a65', 'serv': '5beccc2b3dc616c6fd5037f9f28a4b54'}
F = [('Syne', 600, 'normal', '12153aaa06c742364b419e8a918b91a4'), ('Syne', 700, 'normal', 'ca7d0ad494c05b078bc5f592575b20eb'), ('Syne', 800, 'normal', '40fedd78d94ff3ee04852a1cc3dee9a1'),
     ('DM Sans', 400, 'normal', 'b38d3fcdf128f693623e1f91dcf903bc'), ('DM Sans', 400, 'italic', 'e00b912795a09194be7b92969eaa75dc'), ('DM Sans', 500, 'normal', '28c573571bd08ce6563fc3ee6359a128'),
     ('DM Sans', 700, 'normal', '808119fbbad439fd346b03d7cda0f077'), ('DM Sans', 700, 'italic', '645286dfe5664678f417a82d40f96cce')]
FACES = '\n'.join(f"@font-face {{ font-family: '{f}'; font-weight: {w}; font-style: {s}; src: url(/_blob/{i}) format('woff2'); }}" for f, w, s, i in F)
IM = lambda k: f'/_blob/{B[k]}'
def tb(html):
    html = re.sub(r'(<table[^>]*>)', r'\1<tbody>', html)
    return html.replace('</table>', '</tbody></table>')
def dc(inner, title):
    assert '{{' not in inner and '}}' not in inner
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
<div style="position:relative;width:1123px;height:1587px;overflow:hidden;background:#F4F1EA;font-family:'DM Sans', Arial, sans-serif;color:#1F2A2E;box-sizing:border-box">
{tb(inner)}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1123,"height":1587}}}}'>
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
import os; os.makedirs(root + '/project', exist_ok=True)
open(root + '/project/Main.dc.html', 'w').write(dc(board1.build(IM), 'Titik Temu — Board 01 (concept + site)'))
open(root + '/project/Board2.dc.html', 'w').write(dc(board2.build(IM), 'Titik Temu — Board 02 (the building)'))
for f in ['Main', 'Board2']:
    t = open(f'{root}/project/{f}.dc.html').read(); print(f, len(t), t.count('<img'), t.count('/_blob/'))
