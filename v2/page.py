"""Assemble the v3 review page (one self-contained HTML file) from v2/scheme.py + v2/drawings.py + v2/viewer.js.
Run: python3 v2/page.py [poster.jpg]   (poster = a screenshot of the 3D view, shown if WebGL or the CDN is unavailable)"""
import sys, os, json, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scheme import *
import drawings as D

sp = {s['k']: spine_end(s['b']).distance(Point(C)) for s in SPINES}
need = {lv: sum(a for _, a, l, *_ in PROG if l == lv) for lv in ('GF', 'L1', 'L2')}
encl = dict(GF=zone_area(GF, ZONES_GF, ENCL), L1=zone_area(L1, ZONES_L1, ENCL), L2=zone_area(L2, ZONES_L2, ENCL))
opn = dict(L1=zone_area(L1, ZONES_L1, ('open',)), L2=zone_area(L2, ZONES_L2, ('open',)))
cover = disc(R_L1).area / SITE.area * 100
S_MAIN = D.S_MAIN; back = S_MAIN['bite'][0] - S_MAIN['bite'][1]
rise_len = (sp['SELATAN'] - 6.0) - R_BR0
r0 = lambda v: f'{v:,.0f}'
poster = ''
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    poster = '<img class="poster" alt="Aerial view of the massing model" src="data:image/jpeg;base64,' + base64.b64encode(open(sys.argv[1], 'rb').read()).decode() + '">'

CSS = """
/* layout: one reading column of drawing sheets; mono uppercase annotation like an architectural drawing */
:root{
  --bg:#EDF0F3; --panel:#FFFFFF; --ink:#14202B; --muted:#586574; --line:#CBD3DB; --accent:#0A7486; --hot:#C9690A;
  --site:#F8F9FA; --ground:#E3E7EB; --road:#CED4DA; --ctx:#D5DAE0; --court:#FFF1CC; --water:#4FAEE3; --arcade:#EEF3F5; --tennis:#E4F0E9;
  --z-trade:#F4C055; --z-food:#F09A7A; --z-pub:#86CBD6; --z-priv:#9DA9F0; --z-boh:#B6BEC7; --z-core:#6C7887; --z-open:#CFE5C4;
  --cut:#14202B; --halo:rgba(255,255,255,.82); --sky:#F6F8FA; --sky3d:#E6ECF1; --fin:#7F8B98; --wall:#DDE6EC;
  --f-head:'Space Grotesk',system-ui,sans-serif; --f-body:'Inter',system-ui,sans-serif; --f-mono:'IBM Plex Mono',ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#0D131A; --panel:#141C26; --ink:#E7EDF3; --muted:#94A2B1; --line:#2A3644; --accent:#55C6D8; --hot:#F2A545;
  --site:#1A2430; --ground:#111922; --road:#26313D; --ctx:#222C38; --court:#40371C; --water:#3B9BD4; --arcade:#1F2A36; --tennis:#1D2E2A;
  --z-trade:#A8781C; --z-food:#A8553B; --z-pub:#2C7B88; --z-priv:#4F5CB0; --z-boh:#4A5563; --z-core:#8592A1; --z-open:#34503A;
  --cut:#E7EDF3; --halo:rgba(13,19,26,.8); --sky:#101821; --sky3d:#0B1118; --fin:#9AA7B5; --wall:#1E2935; color-scheme:dark } }
:root[data-theme="dark"]{
  --bg:#0D131A; --panel:#141C26; --ink:#E7EDF3; --muted:#94A2B1; --line:#2A3644; --accent:#55C6D8; --hot:#F2A545;
  --site:#1A2430; --ground:#111922; --road:#26313D; --ctx:#222C38; --court:#40371C; --water:#3B9BD4; --arcade:#1F2A36; --tennis:#1D2E2A;
  --z-trade:#A8781C; --z-food:#A8553B; --z-pub:#2C7B88; --z-priv:#4F5CB0; --z-boh:#4A5563; --z-core:#8592A1; --z-open:#34503A;
  --cut:#E7EDF3; --halo:rgba(13,19,26,.8); --sky:#101821; --sky3d:#0B1118; --fin:#9AA7B5; --wall:#1E2935; color-scheme:dark }
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.55;margin:0}
.wrap{max-width:1060px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;flex-direction:column;gap:44px}
.eyebrow{font-family:var(--f-mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:0 0 10px}
h1{font-family:var(--f-head);font-weight:500;font-size:clamp(34px,6vw,58px);line-height:1.02;letter-spacing:-.02em;margin:0 0 16px;text-wrap:balance}
h2{font-family:var(--f-head);font-weight:500;font-size:clamp(22px,3.2vw,30px);line-height:1.15;letter-spacing:-.01em;margin:0 0 12px;text-wrap:balance}
h3{font-family:var(--f-head);font-weight:500;font-size:18px;margin:0 0 6px}
p{margin:0 0 12px;max-width:68ch} .lead{font-size:18px} .muted{color:var(--muted)}
section{display:flex;flex-direction:column;gap:14px}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-top:8px}
.facts div{padding:12px 14px 12px 0} .facts b{display:block;font-family:var(--f-head);font-weight:500;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums} .facts span{font-family:var(--f-mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:18px;align-items:start} .two>*{min-width:0}
figure{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:4px;min-width:0}
figure .scroll{overflow-x:auto} figure svg{display:block;width:100%;height:auto}
figcaption{font-family:var(--f-mono);font-size:12px;letter-spacing:.03em;color:var(--muted);padding:10px 14px;border-top:1px solid var(--line)}
figcaption b{color:var(--ink);font-weight:500;text-transform:uppercase;letter-spacing:.08em}
.comment{border-left:3px solid var(--accent);padding:2px 0 2px 16px} .comment p{margin-bottom:8px} .comment .q{font-family:var(--f-mono);font-size:13px;color:var(--muted)}
.tbl{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:4px}
table{border-collapse:collapse;width:100%;font-size:14.5px;min-width:560px}
th,td{text-align:left;padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-family:var(--f-mono);font-size:11.5px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
tr:last-child td{border-bottom:0} td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.tot td{font-weight:600;border-top:1.5px solid var(--ink)}
.key{display:flex;flex-wrap:wrap;gap:6px 16px;font-family:var(--f-mono);font-size:12px;color:var(--muted);padding:10px 14px;border-top:1px solid var(--line)}
.key i{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:-1px;border:1px solid var(--line)}
ol.ask{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:10px;max-width:72ch}
ul{margin:0;padding-left:20px;max-width:70ch;display:flex;flex-direction:column;gap:6px}
/* 3D viewer */
#view3d{position:relative;background:var(--sky3d);min-height:260px;touch-action:none}
#view3d canvas{display:block;width:100%!important;height:auto!important;cursor:grab} #view3d .poster{display:block;width:100%}
#view3d.live .poster{display:none}
.bar{display:flex;flex-wrap:wrap;gap:8px;padding:10px 14px;border-top:1px solid var(--line);align-items:center}
.bar button{font-family:var(--f-mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:3px;padding:7px 11px;cursor:pointer}
.bar button:hover{border-color:var(--accent);color:var(--accent)} .bar button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.bar .sep{flex:1} #view3d.nogl + .bar{display:none}
.opt{display:flex;flex-direction:column;gap:14px} .opt h3 span{font-family:var(--f-mono);font-size:12px;letter-spacing:.08em;color:var(--accent);margin-left:8px;text-transform:uppercase}
/* ---- drawings ---- */
svg .ground{fill:var(--ground)} svg .site{fill:var(--site);stroke:var(--ink);stroke-width:1.2} svg .road{fill:var(--road)} svg .ctx{fill:var(--ctx)} svg .tennis{fill:var(--tennis)}
svg .oldsite{fill:none;stroke:var(--muted);stroke-width:.8;stroke-dasharray:2 3} svg .setback{fill:none;stroke:var(--muted);stroke-width:.8;stroke-dasharray:5 4} svg .layby{fill:var(--road);stroke:var(--muted);stroke-width:.7} svg .yard{fill:var(--z-boh);opacity:.45}
svg .spine{fill:var(--accent);opacity:.2} svg .spl{stroke:var(--accent);stroke-width:2.2} svg .shadow{fill:var(--arcade);opacity:.55}
svg .arcade{fill:var(--arcade);stroke:var(--line);stroke-width:.6} svg .court{fill:var(--court);stroke:var(--hot);stroke-width:.8} svg .void{fill:var(--court);opacity:.55} svg .below{fill:var(--arcade);stroke:var(--line);stroke-width:.6}
svg .water{fill:var(--water)} svg .titik{fill:var(--hot)} svg .col{fill:var(--ink)}
svg .z-trade{fill:var(--z-trade)} svg .z-food{fill:var(--z-food)} svg .z-pub{fill:var(--z-pub)} svg .z-priv{fill:var(--z-priv)} svg .z-boh{fill:var(--z-boh)} svg .z-core{fill:var(--z-core)} svg .z-open{fill:var(--z-open)}
svg [class^="z-"]{stroke:var(--panel);stroke-width:1}
svg .bridge{fill:var(--panel);stroke:var(--ink);stroke-width:1} svg .under{fill:none;stroke:var(--ink);stroke-width:.7;stroke-dasharray:2 3;opacity:.55}
svg .above{fill:none;stroke:var(--ink);stroke-width:1.1;stroke-dasharray:7 4} svg .above2{fill:none;stroke:var(--hot);stroke-width:1;stroke-dasharray:2 4}
svg .hang{fill:var(--ink);opacity:.13}
svg .roofhi{fill:var(--accent);stroke:none} svg .roofline{fill:none;stroke:var(--ink);stroke-width:1.1} svg .discroof{fill:var(--court);stroke:var(--hot);stroke-width:1.1} svg .rib{stroke:var(--line);stroke-width:.8}
svg .qibla{stroke:var(--hot);stroke-width:1.4;stroke-dasharray:9 3 2 3} svg .secline{stroke:var(--ink);stroke-width:1;stroke-dasharray:12 4 2 4}
svg .flow{stroke:var(--accent);stroke-width:2.4;fill:none} svg .arrh{fill:var(--accent)}
svg .narrow{stroke:var(--ink);stroke-width:1.2} svg .nhead{fill:var(--ink)} svg .sb1{fill:var(--ink)} svg .sb0{fill:var(--panel);stroke:var(--ink);stroke-width:.6}
svg text.t{font-family:var(--f-mono);font-size:10px;letter-spacing:.04em;fill:var(--ink);paint-order:stroke;stroke:var(--halo);stroke-width:3px;stroke-linejoin:round}
svg text.zl{font-weight:500} svg text.sm{font-size:9px} svg text.mute{fill:var(--muted);font-size:9px} svg text.sp{fill:var(--accent);font-weight:500} svg text.qb{fill:var(--hot);font-weight:500} svg text.sec{font-size:13px;font-weight:600}
svg .sky{fill:var(--sky)} svg .sground{fill:var(--road)} svg .sbeyond{fill:var(--arcade);stroke:var(--line);stroke-width:.6} svg .scut{fill:var(--cut)} svg .sdisc{fill:var(--hot)} svg .scol{fill:var(--muted)} svg .mast{fill:var(--hot)}
svg .veil{stroke:var(--accent);stroke-width:2;stroke-dasharray:3 2} svg .glass{stroke:var(--water);stroke-width:1.6} svg .rail{stroke:var(--muted);stroke-width:1} svg .rain{stroke:var(--water);stroke-width:1.4;stroke-dasharray:2 4}
svg .man{fill:var(--muted)} svg .bnd{stroke:var(--ink);stroke-width:1;stroke-dasharray:8 3 2 3} svg .dim{stroke:var(--accent);stroke-width:1} svg .lead{stroke:var(--line);stroke-width:.8;stroke-dasharray:3 3}
svg .eglass{fill:var(--water);opacity:.35} svg .ewall{fill:var(--wall)} svg .fin{fill:var(--fin)} svg .perf{fill:var(--fin)} svg .ribbon{fill:none;stroke:var(--fin);stroke-width:4.2;stroke-linecap:round}
"""

KEY = ''.join(f'<span><i style="background:var(--{k})"></i>{n}</span>' for k, n in [('z-trade', 'Trade'), ('z-food', 'Food'), ('z-pub', 'Public'), ('z-priv', 'Private (staff, prayer)'), ('z-boh', 'Back of house'), ('z-core', 'Stairs + lifts'), ('z-open', 'Open deck')])
def fig(svg, title, cap, key=False, scroll=True):
    return f'<figure><div class="{"scroll" if scroll else ""}">{svg}</div>' + (f'<div class="key">{KEY}<span>— — floor above</span></div>' if key else '') + f'<figcaption><b>{title}</b> · {cap}</figcaption></figure>'
LVN = dict(GF='Ground', L1='First', L2='Second')
prog_rows = ''.join(f'<tr><td>{g}</td><td class="n">{a:.0f}</td><td>{LVN[lv]} · {pt}</td><td class="muted">{note}</td></tr>' for g, a, lv, pt, note in PROG)
tot_encl = sum(encl.values()); tot_open = sum(opn.values())

HTML = f"""<title>Titik Temu v2 Review</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;600&family=Space+Grotesk:wght@500&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header>
  <p class="eyebrow">Titik Temu · Site C, Temerloh · after Crit 1 · second pass</p>
  <h1>One centre, four ways in</h1>
  <p class="lead">This version takes in your six replies: three floors, the tennis court land, a taller landmark, and a shape and façade with more character. Drag the model to look around.</p>
  <div class="facts">
    <div><b>3</b><span>floors at the high gates</span></div>
    <div><b>+{LV['roof_hi']:.3f}</b><span>roof at its highest</span></div>
    <div><b>+{LV['mast']:.3f}</b><span>mast at the centre</span></div>
    <div><b>{r0(SITE.area)} m²</b><span>site with the tennis land</span></div>
    <div><b>{len(FINS)}</b><span>façade fins</span></div>
  </div>
</header>

<section>
  <p class="eyebrow">The model</p>
  <h2>A ring that rises to its two main gates</h2>
  <figure>
    <div id="view3d">{poster}</div>
    <div class="bar">
      <button type="button" data-view="aerial">Aerial</button><button type="button" data-view="gate">Main gate</button><button type="button" data-view="road">From the road</button><button type="button" data-view="river">River side</button><button type="button" data-view="top">Top</button>
      <span class="sep"></span><button type="button" id="nightbtn" aria-pressed="false">Night</button>
    </div>
    <figcaption><b>Massing model</b> · drag to orbit, scroll or pinch to zoom. Built from the same numbers as the plans below. Neighbouring buildings are approximate.</figcaption>
  </figure>
  <ul>
    <li><b>The roof is one wave.</b> It is low at the Tengah and Timur gates (+{LV['roof_lo']:.3f}, two floors) and rises to +{LV['roof_hi']:.3f} at the Selatan and Utara gates (three floors). So the main gate is framed by the two tallest ends of the building.</li>
    <li><b>The third floor exists only under the high parts.</b> It holds the musolla, the gallery and the meeting rooms, which keeps the building from being bigger than the brief needs.</li>
    <li><b>The landmark is a slender mast</b> through the roof opening at the exact centre, with a light at +{LV['mast']:.3f}. That is about twice the height of the roof.</li>
    <li><b>The façade is a screen of {len(FINS)} vertical fins</b> on the upper floors. They lie almost flat along the wall and turn open as they reach a gate, so the building looks solid from the side and transparent where you enter.</li>
  </ul>
</section>

<section>
  <p class="eyebrow">Your six replies</p>
  <h2>What changed, point by point</h2>
  <div class="tbl"><table>
    <tr><th>You said</th><th>What I did</th></tr>
    <tr><td>1 · There is a public path on the north</td><td>Utara and Timur are now real gates. Utara also gets one of the two high roof ends.</td></tr>
    <tr><td>2 · Three floors</td><td>Ground, first and second floor. The second floor ({r0(L2.area)} m²) sits under the two high parts of the roof. The ring bridge repeats at +{LV['l2']:.3f}.</td></tr>
    <tr><td>3 · Service yard move is OK</td><td>With the tennis land the building now has a side on Jalan Ibrahim, so back of house faces that road with a small service court. Staff parking takes the south-east corner. See question 4.</td></tr>
    <tr><td>4 · A taller landmark</td><td>A mast to +{LV['mast']:.3f} through the oculus. The funnel roof keeps the +13.500 crown level.</td></tr>
    <tr><td>5 · Refer to the brief</td><td>The brief gives no coverage or height limit. It only points to the PLANMalaysia guidelines. It asks for {BRIEF['net']:,} m² net ({BRIEF['gross']:,.0f} m² gross), 5 staff bays, 1 OKU bay, 10 motorcycles and 10 bicycles, with visitors on street parking. All are in the plan.</td></tr>
    <tr><td>5 · Tennis court demolished</td><td>The site grows from {r0(SITE_V1.area)} to {r0(SITE.area)} m². The centre moves {C[0] - 58.2:.0f} m east to stay in the middle of the buildable area. The west side becomes Laman Pekan Sehari, an arrival garden for market and car-boot stalls.</td></tr>
    <tr><td>6 · Cooler shape, play with the façade</td><td>The wave roof and the fin screen above. Two other façade options are drawn below for you to choose from.</td></tr>
  </table></div>
</section>

<section>
  <p class="eyebrow">The façade</p>
  <h2>The whole elevation, opened out flat</h2>
  {fig(D.unroll('A'), 'Unrolled elevation', 'the outside of the ring walked clockwise from the Timur gate, 166 m long')}
  <p>Three ways to dress the upper floors, drawn on the same stretch of the west block from the low Tengah gate (left) to the high Utara gate (right). I recommend A.</p>
  <div class="opt">
    <div><h3>A · Fins that open at the gates <span>recommended, shown in the model</span></h3>
    {fig(D.facade('A'), 'Option A', 'vertical aluminium blades 450 mm deep at 750 mm centres, each one turned a little more than the last')}
    <p class="muted">Strongest futuristic look and the best shade for the east and west sun. One repeated part, so it is simple to model in SketchUp. Changes as you walk past it.</p></div>
    <div><h3>B · Songket veil</h3>
    {fig(D.facade('B'), 'Option B', 'a perforated aluminium skin with diamond openings that grow towards the gates')}
    <p class="muted">Ties the building to local craft. Flatter and calmer than the fins. Needs a good pattern to avoid looking like a generic screen.</p></div>
    <div><h3>C · Ribbons</h3>
    {fig(D.facade('C'), 'Option C', 'horizontal bands that lift away from the wall at each gate')}
    <p class="muted">Closest to your “simpul” idea, and the bands could run out along the spines as canopies. Hardest to build and to draw, and it shades the low sun less well.</p></div>
  </div>
</section>

<section>
  <p class="eyebrow">What the panel said</p>
  <h2>Still answered</h2>
  <div class="two">
    <div class="comment">
      <p class="q">1 · “If the concept is titik temu, why two radial areas? Make one.”</p>
      <p>One centre. The public gets the ground floor and the court. The private rooms (admin, staff, musolla) are upstairs in the same ring. The qibla line passes through that centre and the musolla sits on it, now on the top floor.</p>
    </div>
    <div class="comment">
      <p class="q">2 · “Make the entrance concave. Use convex on the first floor so it hangs.”</p>
      <p>At each gate the ground-floor wall is scooped back, {R_GF - back:.1f} m deep at the main gate. The two upper floors keep the convex line and pass over it. Columns stay on one ring, so the real cantilever is {CANT:.1f} m, a third of the {R_GF - R_BR1:.1f} m span behind it.</p>
    </div>
  </div>
  <div class="two">
    {fig(D.parti('v1'), 'Crit 1', 'two rings, two centres, the old site', scroll=False)}
    {fig(D.parti('v2'), 'Proposed', 'one ring, one centre, four spines, the wider site', scroll=False)}
  </div>
  {fig(D.entrance(), 'Main gate, 1:150 approx', f'grey tint = upper floors overhead. They reach {R_L1 - back:.1f} m in front of the scooped wall.')}
</section>

<section>
  <p class="eyebrow">Plans</p>
  <h2>Ground floor on the wider site</h2>
  {fig(D.plan('GF'), 'Ground floor + site', 'north up · dashed grey = setback line · dotted = old lot line · A–A = section below', key=True)}
  <ul>
    <li><b>The four spines</b> keep the real bearings to each region: Selatan 183°, Tengah 243°, Utara 318°, Timur 28°. They run {sp['SELATAN']:.0f}, {sp['TENGAH']:.0f}, {sp['UTARA']:.0f} and {sp['TIMUR']:.0f} m from the boundary to the centre.</li>
    <li><b>The main forecourt</b> rises 0.9 m over {rise_len:.1f} m (about 1:{rise_len / .9:.0f}), so there are no steps and no separate ramp. Check against MS 1184 at plan stage.</li>
    <li><b>Parking from the brief:</b> 5 staff bays, 1 OKU bay and 10 motorcycles in the south-east corner, 10 bicycles by the arrival garden, a drop-off lay-by at the main gate.</li>
    <li><b>The Tengah spine</b> is {sp['TENGAH']:.0f} m long and crosses the arrival garden. On market days the Pekan Sehari and car-boot stalls line it, which the brief names as users.</li>
  </ul>
  <div class="two">
    {fig(D.plan('L1'), 'First floor +5.400', 'dotted = ground-floor walls below')}
    {fig(D.plan('L2'), 'Second floor +9.600', 'only under the high roof; dotted = first floor below')}
  </div>
  <div class="two">
    {fig(D.plan('ROOF'), 'Roof', 'darker = higher. Compare with your roof-plan sketch.')}
    <div>
      <ul>
        <li><b>The ring bridge</b> is the corridor on both upper floors. On the second floor it runs under the funnel roof and links the two high parts.</li>
        <li><b>Two cores</b> (stairs and lifts) stand beside the two high gates, opposite each other across the court, and reach all three floors.</li>
        <li><b>The musolla</b> is on the top floor, centred on the qibla radial {QIBLA}°, with {roof_h(QIBLA) - ROOF_T - LV['l2']:.1f} m of height under the rising roof.</li>
        <li><b>The gallery</b> shares the top floor with an open river deck that looks east over Jalan Ibrahim towards Sungai Pahang.</li>
        <li><b>The funnel roof</b> still sends rain through the Ø3 m opening into the pool at the centre.</li>
      </ul>
    </div>
  </div>
</section>

<section>
  <p class="eyebrow">Section A–A</p>
  <h2>Three floors at the main gate, two at the back</h2>
  {fig(D.section(), 'Section through the main gate, court and north block', 'left = road side. The cut runs 3 m west of the Selatan axis and through the centre inside the court.')}
</section>

<section>
  <p class="eyebrow">Does it fit</p>
  <h2>Sizes and areas</h2>
  <div class="two">
    <div class="tbl"><table style="min-width:300px">
      <tr><th>Floor</th><th class="n">Rooms need (net)</th><th class="n">Enclosed (gross)</th><th class="n">Open deck</th></tr>
      <tr><td>Ground</td><td class="n">{r0(need['GF'])}</td><td class="n">{r0(encl['GF'])}</td><td class="n">0</td></tr>
      <tr><td>First</td><td class="n">{r0(need['L1'])}</td><td class="n">{r0(encl['L1'])}</td><td class="n">{r0(opn['L1'])}</td></tr>
      <tr><td>Second</td><td class="n">{r0(need['L2'])}</td><td class="n">{r0(encl['L2'])}</td><td class="n">{r0(opn['L2'])}</td></tr>
      <tr class="tot"><td>Total m²</td><td class="n">{r0(sum(need.values()))}</td><td class="n">{r0(tot_encl)}</td><td class="n">{r0(tot_open)}</td></tr>
    </table></div>
    <div class="tbl"><table style="min-width:300px">
      <tr><th>Check</th><th class="n">Value</th></tr>
      <tr><td>Brief asks for</td><td class="n">{BRIEF['net']:,} net / {BRIEF['gross']:,.0f} gross m²</td></tr>
      <tr><td>Site with the tennis land</td><td class="n">{r0(SITE.area)} m²</td></tr>
      <tr><td>Footprint</td><td class="n">{cover:.0f}% of the site</td></tr>
      <tr><td>Roof edge from the centre</td><td class="n">{R_ROOF} m</td></tr>
      <tr><td>Setback line, nearest point</td><td class="n">{ENV.exterior.distance(Point(C)):.1f} m</td></tr>
      <tr><td>Cantilever of the upper floors</td><td class="n">{CANT:.1f} m</td></tr>
    </table></div>
  </div>
  <p class="muted">“Rooms need” is your Crit 1 room schedule, regrouped over three floors. It is larger than the brief’s {BRIEF['net']:,} m² because it includes stairs, lifts and corridors. Enclosed space is {tot_encl / BRIEF['gross'] * 100 - 100:.0f}% over the brief’s gross figure. The open decks are extra, shaded, and useful for Pekan Sehari and events.</p>
  <div class="tbl"><table>
    <tr><th>Room group</th><th class="n">Crit 1 net m²</th><th>Floor · block</th><th>Note</th></tr>
    {prog_rows}
    <tr class="tot"><td>Total</td><td class="n">{sum(need.values()):.0f}</td><td></td><td class="muted">The enclosed lobby, verandah and balcony of Crit 1 are replaced by the forecourt, arcade and ring bridges.</td></tr>
  </table></div>
</section>

<section>
  <p class="eyebrow">Futuristic, no brick</p>
  <h2>White plates, silver fins, a glowing centre</h2>
  <div class="tbl"><table>
    <tr><th>Part</th><th>Material</th><th>Why</th><th>Watch out</th></tr>
    <tr><td>Wave roof</td><td>White standing-seam aluminium on steel, smooth white soffit, edge tapered to a thin line</td><td>Reads as one thin plate that lifts at the gates</td><td>New aluminium is carbon-heavy. Ask for recycled content.</td></tr>
    <tr><td>Fins</td><td>Anodised aluminium blades, 450 mm deep, with a thin light strip on the edge</td><td>Shade the glass behind, and at night each fin becomes a line of light</td><td>Fix each fin top and bottom. Check heat gain against MS 1525.</td></tr>
    <tr><td>Upper walls</td><td>Curved glass with a printed dot pattern behind the fins</td><td>Keeps the rooms bright without glare</td><td>Curved glass costs more. Facet it in flat panels if needed.</td></tr>
    <tr><td>Ground floor</td><td>Full-height clear glass shopfronts. Solid walls in white GRC panels (thin glass-fibre concrete).</td><td>GRC curves easily, so the concave scoops are simple to make</td><td>Set the panel joints out from the centre.</td></tr>
    <tr><td>Columns and mast</td><td>Slender round steel with brushed stainless cladding</td><td>The columns disappear, so the floors look like they hang</td><td>Steel needs fire protection paint. The mast needs a wind check.</td></tr>
    <tr><td>Centre roof</td><td>ETFE cushions with a printed pattern on steel ribs</td><td>Very light, lets daylight into the court, and glows at night</td><td>Heavy rain is loud on ETFE. It lasts about 25 to 50 years.</td></tr>
    <tr><td>Floors</td><td>Pale terrazzo with stainless inlay lines along each spine</td><td>The lines point at the titik. State names and bearings can be set into them.</td><td>Use a slip-resistant finish outdoors.</td></tr>
  </table></div>
  <p><b>Structure in one line:</b> radial steel frames on two column rings ({R_BR1} m and {R_GF} m from the centre), beams about 525 mm deep for the {R_GF - R_BR1:.1f} m span, upper floors and roof cantilevering {CANT:.1f} m, and the two cores as bracing. Your structure consultant should confirm it.</p>
</section>

<section>
  <p class="eyebrow">Before SketchUp</p>
  <h2>Five things to check</h2>
  <ol class="ask">
    <li><b>The new east boundary.</b> I traced it from the brief’s site plan, where one pixel is about half a metre, and took it to the edge of Jalan Ibrahim. Please confirm the real line with your lecturer. If the land stops at the tennis court fence, the site is slightly smaller but the building still fits.</li>
    <li><b>Which façade: A, B or C?</b></li>
    <li><b>The high ends at Selatan and Utara.</b> Are those the right two gates to make tall? The other choice is all four blocks rising the same way round, like a pinwheel.</li>
    <li><b>Back of house on Jalan Ibrahim.</b> It is the shortest service route, but that side also faces the river. If you want the river side fully public, service goes to the south-east corner instead.</li>
    <li><b>The mast at +{LV['mast']:.3f} and the open decks ({r0(tot_open)} m²).</b> I could not find a height limit in the brief. Tell me if either feels too much.</li>
  </ol>
  <p class="muted">Approximate on purpose: the neighbouring buildings and the zone shapes. Fire escape distances (UBBL 1984) and access details (MS 1184) are checked at plan stage, not here.</p>
</section>
</div>
<script>window.MODEL = {json.dumps(D.model_data(), separators=(',', ':'))};</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>{open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'viewer.js')).read()}</script>
"""
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'titik-temu-v2-review.html'), 'w').write(HTML)
print('written', len(HTML), '| poster', bool(poster))
