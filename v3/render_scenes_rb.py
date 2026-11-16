import math, sys
sys.path.insert(0, '/home/claude/gat/v3')
import importlib.util
spec = importlib.util.spec_from_file_location('rb', '/home/claude/gat/v3/render_blender.py')
src = open('/home/claude/gat/v3/render_blender.py').read().split("def setup_scene")[0].replace('import bpy', '').replace('from mathutils import Vector', '')
ns = {'__file__': '/home/claude/gat/v3/render_blender.py'}; exec(src, ns)
V = ns['VIEWS']
times = {'dusk': (18, 50)}
lines = ['# Titik Temu - scenes for SketchUp (run AFTER importing titik-temu.dae with "Preserve drawing origin" ticked)',
         '# Window > Ruby Console, then: load "C:/path/to/titik-temu-scenes.rb"', 'm = Sketchup.active_model',
         'def tt_pt(x, y, z) Geom::Point3d.new(x.m, y.m, z.m) end',
         'si = m.shadow_info', "si['City'] = 'Temerloh'; si['Country'] = 'Malaysia'; si['Latitude'] = 3.45; si['Longitude'] = 102.42; si['TZOffset'] = 8.0",
         "si['DisplayShadows'] = true; si['UseSunForAllShading'] = true; si['Light'] = 85; si['Dark'] = 45",
         'm.start_operation("Titik Temu scenes", true)']
names = {'hero': '01 Hero, south-east', 'gate': '02 Selatan gate (eye level)', 'aerial_nw': '03 Aerial, north-west', 'bridge': '04 Ring bridge', 'dusk': '05 Dusk, Tengah side',
         'court': '06 Talam court', 'arcade': '07 Arcade + shopfronts'}
for k in ['hero', 'gate', 'aerial_nw', 'bridge', 'dusk', 'court', 'arcade']:
    v = V[k]; hf = 2 * math.atan(18 / v['lens']); vf = math.degrees(2 * math.atan(math.tan(hf / 2) * 9 / 16))
    hh, mm = times.get(k, (9, 30))
    e = ', '.join(f'{c:.2f}' for c in v['cam']); t = ', '.join(f'{c:.2f}' for c in v['tgt'])
    lines.append(f"si['ShadowTime'] = Time.new(2026, 11, 16, {hh}, {mm}, 0, '+08:00')")
    lines.append(f"m.active_view.camera = Sketchup::Camera.new(tt_pt({e}), tt_pt({t}), Z_AXIS, true, {vf:.1f})")
    lines.append(f"pg = m.pages.add('{names[k]}'); pg.use_shadow_info = true; pg.update")
lines += ['m.commit_operation', "puts 'Titik Temu: 7 scenes added'"]
open('/home/claude/gat/v3/out/render/dae/titik-temu-scenes.rb', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines[-6:]))
