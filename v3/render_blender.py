"""Cycles renders of the render model (run with the bpy venv):
  /home/claude/bpyenv/.venv/bin/python render_blender.py VIEW [scale%] [samples]
VIEW in VIEWS below, or 'all'. Output: out/render/img/<view>.png"""
import sys, os, math, json, time
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'render'); IMG = os.path.join(OUT, 'img'); os.makedirs(IMG, exist_ok=True)
C = (70.3, 27.0)
def P(r, b, z=0.0): return (C[0] + r * math.sin(math.radians(b)), C[1] + r * math.cos(math.radians(b)), z)

# view: camera, target, lens (mm), sun azimuth / elevation (deg), aspect
VIEWS = {
    'hero':   dict(cam=P(70, 150, 22), tgt=P(3, 170, 8.5), lens=34, sun=(70, 34), res=(1920, 1080), ev=0.1),
    'gate':   dict(cam=P(41, 186.5, 1.55), tgt=P(9, 181, 6.2), lens=22, sun=(105, 42), res=(1920, 1080), ev=0.35, interior=True),
    'court':  dict(cam=P(8.6, 214, 2.45), tgt=P(5, 30, 8.8), lens=15, sun=(95, 62), res=(1920, 1080), ev=0.45, interior=True),
    'arcade': dict(cam=P(9.9, 127, 1.95), tgt=P(13.4, 152, 3.0), lens=22, sun=(95, 55), res=(1920, 1080), ev=0.0, interior=True),
    'bridge': dict(cam=P(18.5, 206, 7.0), tgt=P(18.4, 248, 6.8), lens=17, sun=(250, 35), res=(1920, 1080), ev=0.5),
    'aerial_nw': dict(cam=P(85, 318, 52), tgt=P(0, 0, 4), lens=38, sun=(250, 32), res=(1920, 1080), ev=0.1),
    'dusk':   dict(cam=P(58, 228, 9.0), tgt=P(4, 210, 8.0), lens=30, sun=(285, 2.5), res=(1920, 1080), ev=0.9, dusk=True),
}

def setup_scene(glb=None, context=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb or os.path.join(OUT, 'titik-temu-render.glb'), merge_vertices=False)
    sc = bpy.context.scene
    # ---- materials
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None: continue
        nm = m.name
        def setv(k, v):
            if k in bsdf.inputs: bsdf.inputs[k].default_value = v
        if nm.startswith(('Glass', 'Car-Glass', 'Water')):
            setv('Transmission Weight', 1.0); setv('Alpha', 1.0); setv('IOR', 1.45 if not nm.startswith('Water') else 1.33)
            setv('Roughness', 0.32 if nm == 'Glass-Opal' else 0.02)
            col = {'Glass': (0.78, 0.88, 0.9, 1), 'Glass-Balustrade': (0.92, 0.97, 0.98, 1), 'Glass-Opal': (0.95, 0.97, 0.98, 1), 'Car-Glass': (0.08, 0.1, 0.12, 1)}.get(nm)
            if col: setv('Base Color', col)
            if nm == 'Car-Glass': setv('Transmission Weight', 0.2)
        if nm.startswith(('Leaves', 'Shrub')):
            setv('Subsurface Weight', 0.15) if 'Subsurface Weight' in bsdf.inputs else None
            setv('Roughness', 0.75)
        if nm in ('Roof-Panel',): setv('Roughness', 0.28); setv('Metallic', 0.15)
        if nm in ('Bronze-Anodised',): setv('Metallic', 0.15); setv('Roughness', 0.5)
        if nm in ('Solid-Surface',): setv('Base Color', (0.82, 0.8, 0.77, 1)); setv('Roughness', 0.45)
        if nm.startswith(('Screen-', 'Tenun-Lining')):             # backlit state screens + tenun lining lit from above
            tex = next((n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'), None)
            if tex: m.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
            setv('Emission Strength', 1.4 if nm.startswith('Screen-') else 0.35)
    # ---- smooth shading on curved, faceted architecture (by angle)
    done = set()
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.data.name not in done:
            done.add(o.data.name)
            for p in o.data.polygons: p.use_smooth = True
            leafy = any(ms and ms.name.startswith(('Leaves', 'Shrub', 'Skin', 'Cloth', 'Hair')) for ms in o.data.materials)
            if not leafy:
                try: o.data.set_sharp_from_angle(angle=math.radians(32))
                except Exception: pass
    if not context: return sc
    # ---- context: big ground plane + road continuations + a ring of trees (render only, not in the SketchUp file)
    bpy.ops.mesh.primitive_plane_add(size=1400, location=(C[0], C[1], -0.36))
    g = bpy.context.active_object; g.name = 'CTX-GROUND'
    mg = bpy.data.materials.new('CTX-Ground'); mg.use_nodes = True; b = mg.node_tree.nodes['Principled BSDF']
    tex = mg.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.join(OUT, 'textures', 'grass.jpg'))
    mp = mg.node_tree.nodes.new('ShaderNodeMapping'); tc = mg.node_tree.nodes.new('ShaderNodeTexCoord'); mp.inputs['Scale'].default_value = (233, 233, 1)
    mg.node_tree.links.new(tc.outputs['UV'], mp.inputs['Vector']); mg.node_tree.links.new(mp.outputs['Vector'], tex.inputs['Vector']); mg.node_tree.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95; g.data.materials.append(mg)
    asph = bpy.data.materials.get('Asphalt')
    # the two roads continue AWAY from the junction at the south-east corner (Jalan Tok Muda Awang Ngah west, Jalan Ibrahim north)
    for (a, c, w) in (((112.9, -15.9), (-250.0, 35.0), 12.0), ((115.0, -15.6), (52.4, 334.7), 10.0)):
        a, c = Vector((a[0], a[1], 0)), Vector((c[0], c[1], 0)); t = (c - a).normalized(); n = Vector((t.y, -t.x, 0))
        side = 1 if (Vector((C[0], C[1], 0)) - a).dot(n) < 0 else -1
        cen = (a + c) / 2 + n * side * (w / 2 + 0.25); Lr = (c - a).length
        bpy.ops.mesh.primitive_plane_add(size=1, location=(cen.x, cen.y, -0.17)); r = bpy.context.active_object; r.name = 'CTX-ROAD'
        r.scale = (w, Lr, 1); r.rotation_euler = (0, 0, math.atan2(-t.x, t.y))
        if asph: r.data.materials.append(asph)
    import random; random.seed(3)
    parts = [bpy.data.meshes[n] for n in bpy.data.meshes.keys() if n.startswith(('C_tree_rain_', 'C_tree_rain2_'))]
    groups = {}
    for me in parts: groups.setdefault(me.name.rsplit('_', 1)[0], []).append(me)
    site_pts = [(31.8, 55.8), (87.3, 63.0), (100.7, 64.7), (112.2, 0.1), (112.9, -15.9), (0.0, 0.0), (1.5, 13.9), (16.4, 30.1)]
    def inside(x, y):
        c = False; n = len(site_pts)
        for i in range(n):
            x1, y1 = site_pts[i]; x2, y2 = site_pts[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1: c = not c
        return c
    roads = [((112.9, -15.9), (0.0, 0.0)), ((100.7, 64.7), (112.2, 0.1))]
    def droad(x, y):
        best = 1e9
        for (ax, ay), (cx, cy) in roads:
            tx, ty = cx - ax, cy - ay; L = math.hypot(tx, ty); tx, ty = tx / L, ty / L
            s_ = (x - ax) * tx + (y - ay) * ty; nx, ny = x - ax - tx * s_, y - ay - ty * s_
            best = min(best, math.hypot(nx, ny))
        return best
    bpy.context.view_layer.update()
    REF = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.data and o.data.name not in REF and not o.name.startswith('CTX'): REF[o.data.name] = o.matrix_world.copy()
    n = 0; keys = list(groups)
    while n < 520:
        x, y = C[0] + random.uniform(-320, 320), C[1] + random.uniform(-320, 320)
        if inside(x, y) or droad(x, y) < 11: continue
        dmin = min(math.hypot(x - px, y - py) for px, py in site_pts)
        if dmin < 9 or math.hypot(x - C[0], y - C[1]) < 50: continue
        k = keys[n % len(keys)]; rot = random.uniform(0, 6.28); sc_ = random.uniform(0.8, 1.25)
        from mathutils import Matrix
        for me in groups[k]:
            ref = REF.get(me.name)
            if ref is None: continue
            o = bpy.data.objects.new(f'CTX-TREE-{n}-{me.name}', me); sc.collection.objects.link(o)
            # the importer keeps the glTF axis turn in the object matrix, so copy the rotation of an imported instance
            R0 = ref.to_3x3().normalized().to_4x4()
            o.matrix_world = Matrix.Translation((x, y, -0.35)) @ Matrix.Rotation(rot, 4, 'Z') @ R0 @ Matrix.Scale(sc_, 4)
        n += 1
    return sc

def interior_lights(sc, mult=1.0):
    for i, (x, y, z, su, sv, w, col, hd) in enumerate(json.load(open(os.path.join(OUT, 'lights.json')))):
        if su in (1.2,) and sv in (0.6,): w = w * 0.45                # shop downlights: softer so the white counters do not burn out
        ld = bpy.data.lights.new(f'IL{i}', 'AREA'); ld.shape = 'RECTANGLE'; ld.size = su; ld.size_y = sv; ld.energy = w * mult; ld.color = col
        o = bpy.data.objects.new(f'IL{i}', ld); sc.collection.objects.link(o); o.location = (x, y, z); o.rotation_euler = (0, 0, -math.radians(hd))

def lights(sc, az, el):
    w = bpy.data.worlds.new('Sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree
    sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_disc = False
    sky.sun_elevation = math.radians(el); sky.sun_rotation = math.radians(90 - az) if False else math.radians(-az + 90)
    sky.air_density = 1.2; sky.dust_density = 1.6; sky.ozone_density = 1.0; sky.altitude = 50
    bg = nt.nodes['Background']; bg.inputs['Strength'].default_value = 0.22
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 4.2; sd.angle = math.radians(1.2); sd.color = (1.0, 0.93, 0.82)
    so = bpy.data.objects.new('Sun', sd); sc.collection.objects.link(so)
    s = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    so.rotation_euler = (-s).to_track_quat('-Z', 'Y').to_euler()

def camera(sc, v):
    cd = bpy.data.cameras.new('Cam'); cd.lens = v['lens']; cd.sensor_width = 36; cd.clip_start = 0.1; cd.clip_end = 2000
    co = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(co); sc.camera = co
    co.location = Vector(v['cam']); d = Vector(v['tgt']) - Vector(v['cam'])
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cd.shift_y = 0.0

def render(view, pct=100, samples=128):
    sc = setup_scene(); v = VIEWS[view]
    # keep people out of the first metres in front of the lens (they read as giants in a wide-angle frame)
    cam = Vector(v['cam']); near = v.get('clear', 4.5 if v.get('interior') else 3.0)
    for o in bpy.data.objects:
        if '_person_' in o.name and (o.matrix_world.translation - cam).length < near: o.hide_render = True
    lights(sc, *v['sun']); camera(sc, v); interior_lights(sc, 1.6 if v.get('dusk') else 1.0)
    if v.get('dusk'):
        sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.06
        sun = bpy.data.objects['Sun'].data; sun.energy = 1.6; sun.color = (1.0, 0.62, 0.38)
    sc.render.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'
    cy.samples = samples; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02; cy.use_denoising = True
    cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 12
    cy.caustics_reflective = False; cy.caustics_refractive = False; cy.blur_glossy = 1.0; cy.sample_clamp_indirect = 8
    sc.render.resolution_x, sc.render.resolution_y = v['res']; sc.render.resolution_percentage = pct
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = v.get('ev', 0.15)
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = os.path.join(IMG, f'{view}.png')
    # atmospheric haze by distance (mist pass) + a soft glow, in the compositor
    sc.view_layers[0].use_pass_mist = True
    ms = sc.world.mist_settings; ms.start = 45 if not v.get('dusk') else 35; ms.depth = 420; ms.falloff = 'QUADRATIC'
    sc.use_nodes = True; nt = sc.node_tree
    for n_ in list(nt.nodes): nt.nodes.remove(n_)
    rl = nt.nodes.new('CompositorNodeRLayers'); mx = nt.nodes.new('CompositorNodeMixRGB'); cp = nt.nodes.new('CompositorNodeComposite')
    mt = nt.nodes.new('CompositorNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = 0.0 if v.get('interior') else (0.45 if not v.get('dusk') else 0.35)
    mx.inputs[2].default_value = (0.80, 0.85, 0.9, 1) if not v.get('dusk') else (0.55, 0.42, 0.42, 1)
    gl = nt.nodes.new('CompositorNodeGlare'); gl.glare_type = 'FOG_GLOW'; gl.quality = 'MEDIUM'; gl.mix = -0.9 if not v.get('dusk') else -0.75; gl.threshold = 1.2
    nt.links.new(rl.outputs['Mist'], mt.inputs[0]); nt.links.new(mt.outputs[0], mx.inputs[0])
    nt.links.new(rl.outputs['Image'], mx.inputs[1]); nt.links.new(mx.outputs[0], gl.inputs[0]); nt.links.new(gl.outputs[0], cp.inputs[0])
    t = time.time(); bpy.ops.render.render(write_still=True); print('RENDERED', view, round(time.time() - t), 's', flush=True)

if __name__ == '__main__':
    view = sys.argv[1] if len(sys.argv) > 1 else 'hero'
    pct = int(sys.argv[2]) if len(sys.argv) > 2 else 100; spp = int(sys.argv[3]) if len(sys.argv) > 3 else 128
    for vw in (VIEWS if view == 'all' else [view]): render(vw, pct, spp)
