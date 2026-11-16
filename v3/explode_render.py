"""Exploded axonometric render (Cycles, orthographic) of out/render/explode/titik-temu-exploded.glb + labels.
/home/claude/bpyenv/.venv/bin/python explode_render.py [pct] [samples] [preview]"""
import sys, os, math, json
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_blender as RB
from bpy_extras.object_utils import world_to_camera_view

ED = os.path.join(RB.OUT, 'explode')
AZ, EL = 150.0, 36.0                  # view from the south-east (bearing 150°), 30° down - same side as the hero render
RES = (2400, 1800)

def main(pct=100, spp=96, preview=False):
    sc = RB.setup_scene(os.path.join(ED, 'titik-temu-exploded.glb'), context=False)
    info = json.load(open(os.path.join(ED, 'explode.json')))
    # world: soft white studio
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.93, 0.94, 0.95, 1); bg.inputs['Strength'].default_value = 0.9
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3.4; sd.angle = math.radians(3); sd.color = (1.0, 0.95, 0.88)
    so = bpy.data.objects.new('Sun', sd); sc.collection.objects.link(so)
    az, el = 120, 52
    s = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    so.rotation_euler = (-s).to_track_quat('-Z', 'Y').to_euler()
    # orthographic camera fitted to the model
    pts = []
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for c in o.bound_box: pts.append(o.matrix_world @ Vector(c))
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    tgt = Vector((RB.C[0], RB.C[1], (lo.z + hi.z) / 2))
    d = Vector((math.sin(math.radians(AZ)) * math.cos(math.radians(EL)), math.cos(math.radians(AZ)) * math.cos(math.radians(EL)), math.sin(math.radians(EL))))
    cd = bpy.data.cameras.new('Cam'); cd.type = 'ORTHO'; cd.clip_start = 1; cd.clip_end = 2000
    co = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(co); sc.camera = co
    co.location = tgt + d * 400; co.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = pct
    bpy.context.view_layer.update()
    # fit: model extents in camera space -> ortho scale + recentre (extra room on the left for the labels)
    Mi = co.matrix_world.inverted(); loc = [Mi @ p for p in pts]
    x0, x1 = min(p.x for p in loc), max(p.x for p in loc); y0, y1 = min(p.y for p in loc), max(p.y for p in loc)
    asp = RES[0] / RES[1]; W, H = (x1 - x0), (y1 - y0)
    LEFT = 0.24                                          # fraction of the frame width kept free for labels
    frame_w = max(W / (1 - LEFT - 0.04), H / 0.92 * asp); frame_h = frame_w / asp
    cd.ortho_scale = max(frame_w, frame_h); print("FIT", x0, x1, y0, y1, W, H, frame_w, frame_h, flush=True)
    cx = (x0 + x1) / 2 - frame_w * (LEFT / 2 - 0.0); cy = (y0 + y1) / 2
    co.location = co.location + co.matrix_world.to_3x3() @ Vector((cx, cy, 0))
    bpy.context.view_layer.update()
    # label anchors -> 2D (pixel) positions: the model's left silhouette at each band's level
    lab = {}
    for b, L in info['labels'].items():
        z = L['z']; best = None
        for ang in range(0, 360, 3):
            p = Vector((RB.C[0] + 30 * math.sin(math.radians(ang)), RB.C[1] + 30 * math.cos(math.radians(ang)), z))
            q = world_to_camera_view(sc, co, p)
            if best is None or q.x < best.x: best = q
        lab[b] = dict(L, x=best.x, y=1 - best.y)
    json.dump(lab, open(os.path.join(ED, 'labels2d.json'), 'w'), indent=1)
    if preview:
        sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
        sc.display.shading.show_shadows = True
    else:
        sc.render.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = spp; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
        cy.use_denoising = True; cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 2; cy.transmission_bounces = 6; cy.transparent_max_bounces = 10
        cy.caustics_reflective = False; cy.caustics_refractive = False; cy.sample_clamp_indirect = 6
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0.25
    TR = os.environ.get('EXPLODE_TRANSPARENT') == '1'
    sc.render.film_transparent = TR
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA' if TR else 'RGB'
    sc.render.filepath = os.path.join(ED, 'exploded_preview.png' if preview else ('exploded_alpha.png' if TR else 'exploded_raw.png'))
    bpy.ops.render.render(write_still=True); print('RENDERED', sc.render.filepath, flush=True)

if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    main(int(a[0]) if a else 100, int(a[1]) if len(a) > 1 else 96, len(a) > 2 and a[2] == 'preview')
