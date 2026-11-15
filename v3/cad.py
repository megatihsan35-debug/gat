"""Tiny CAD layer: record drawing primitives once in MODEL metres, then render them
 - to an A1 PDF sheet at a true scale (matplotlib, all sizes in paper mm), and
 - to a DXF in metres with named layers (ezdxf) for AutoCAD / SketchUp.
Text heights and line weights are given in PAPER mm so a 1:100 and a 1:20 drawing read the same on the sheet."""
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle as MCircle, Arc as MArc, PathPatch, Rectangle
from matplotlib.path import Path
from matplotlib import font_manager as fm
import ezdxf
from ezdxf.enums import TextEntityAlignment

FONT = 'Inter' if any('Inter' in f.name for f in fm.fontManager.ttflist) else 'DejaVu Sans'
MONO = 'DejaVu Sans Mono'
PT = 72 / 25.4                      # points per mm
INK = '#111418'

# DXF layer table: name -> (ACI colour, lineweight in 1/100 mm)
LAYERS = {
    'A-WALL': (7, 50), 'A-WALL-PATT': (8, 0), 'A-GLAZ': (4, 18), 'A-DOOR': (2, 18), 'A-COLS': (7, 50), 'A-GRID': (8, 13),
    'A-STRS': (7, 25), 'A-FIXT': (9, 13), 'A-FURN': (9, 13), 'A-ANNO': (7, 18), 'A-DIMS': (3, 13), 'A-AREA': (5, 13),
    'A-SLAB': (7, 35), 'A-ROOF': (7, 35), 'A-ELEV': (7, 25), 'A-HIDN': (8, 13), 'A-SITE': (8, 18), 'A-LAND': (3, 13),
    'F-ESCP': (1, 35), 'F-EQPT': (1, 25), 'F-DETN': (1, 18), 'F-RATE': (1, 50),
    'P-CWAT': (5, 35), 'P-SANI': (34, 35), 'P-RAIN': (4, 35), 'P-EQPT': (5, 25),
    'M-ELEC': (6, 25), 'M-ACMV': (130, 25), 'M-EQPT': (6, 25),
    'S-DETL': (7, 35), 'X-TITL': (7, 25), 'L-CANP': (32, 25), 'L-PLNT': (82, 18),
}

class Drawing:
    """primitives in model metres (or paper mm when paper=True)"""
    def __init__(self, name, paper=False):
        self.name, self.paper, self.items = name, paper, []
    # style: lw (paper mm), color, ls ('-', '--', ':', '-.'), fill (colour or None), alpha, z (draw order)
    def line(self, pts, layer, lw=0.18, color=INK, ls='-', z=3, closed=False):
        pts = [tuple(map(float, p)) for p in pts]
        if len(pts) > 1: self.items.append(('line', layer, dict(pts=pts, lw=lw, color=color, ls=ls, z=z, closed=closed)))
    def poly(self, geom, layer, fill=None, edge=INK, lw=0.18, ls='-', alpha=1.0, z=2, hatch=None):
        for g in getattr(geom, 'geoms', [geom]):
            if g.is_empty or g.geom_type != 'Polygon': continue
            rings = [list(g.exterior.coords)] + [list(r.coords) for r in g.interiors]
            self.items.append(('poly', layer, dict(rings=rings, fill=fill, edge=edge, lw=lw, ls=ls, alpha=alpha, z=z, hatch=hatch)))
    def circle(self, c, r, layer, fill=None, edge=INK, lw=0.18, z=4, ls='-'):
        self.items.append(('circle', layer, dict(c=(float(c[0]), float(c[1])), r=float(r), fill=fill, edge=edge, lw=lw, z=z, ls=ls)))
    def arc(self, c, r, a0, a1, layer, lw=0.13, color=INK, z=3, ls='-'):
        """a0, a1 in maths degrees (anticlockwise from +x)"""
        self.items.append(('arc', layer, dict(c=(float(c[0]), float(c[1])), r=float(r), a0=float(a0), a1=float(a1), lw=lw, color=color, z=z, ls=ls)))
    def text(self, p, s, layer='A-ANNO', size=2.5, ha='center', va='center', rot=0.0, color=INK, weight='normal', z=8, font=None, halo=False, box=None):
        self.items.append(('text', layer, dict(p=(float(p[0]), float(p[1])), s=str(s), size=size, ha=ha, va=va, rot=float(rot), color=color, weight=weight, z=z, font=font, halo=halo, box=box)))
    def extend(self, other):
        self.items += other.items

# --------------------------------------------------------------------------------------------------------- PDF
class Sheet:
    """an A1 landscape sheet, 841 x 594 mm; everything placed in paper mm"""
    def __init__(self, w=841.0, h=594.0):
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=(w / 25.4, h / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1]); self.ax.set_xlim(0, w); self.ax.set_ylim(0, h); self.ax.axis('off'); self.ax.set_aspect('equal')
        self.views = []
    def place(self, dwg, scale, model_xy, paper_xy, clip=None):
        """put model point model_xy at paper point paper_xy, at 1:scale (scale = paper-mm per model unit inverse).
        clip = (x0, y0, x1, y1) in paper mm"""
        k = 1.0 if dwg.paper else 1000.0 / scale
        T = lambda pts: [((x - model_xy[0]) * k + paper_xy[0], (y - model_xy[1]) * k + paper_xy[1]) for x, y in pts]
        cp = None
        if clip:
            cp = Rectangle((clip[0], clip[1]), clip[2] - clip[0], clip[3] - clip[1], transform=self.ax.transData, fc='none', ec='none')
            self.ax.add_patch(cp)
        ax = self.ax
        for kind, layer, a in dwg.items:
            if kind == 'line':
                pts = T(a['pts'])
                if a['closed']: pts = pts + [pts[0]]
                xs, ys = zip(*pts)
                o = ax.plot(xs, ys, lw=a['lw'] * PT, color=a['color'], ls=a['ls'], zorder=a['z'], solid_capstyle='butt', dash_capstyle='butt')[0]
                if cp: o.set_clip_path(cp)
            elif kind == 'poly':
                verts, codes = [], []
                for ring in a['rings']:
                    pr = T(ring)
                    verts += pr; codes += [Path.MOVETO] + [Path.LINETO] * (len(pr) - 2) + [Path.CLOSEPOLY]
                pp = PathPatch(Path(verts, codes), fc=a['fill'] if a['fill'] else 'none', ec=a['edge'] if a['edge'] else 'none',
                               lw=a['lw'] * PT if a['edge'] else 0, ls=a['ls'], alpha=a['alpha'], zorder=a['z'], hatch=a['hatch'], joinstyle='miter')
                ax.add_patch(pp)
                if cp: pp.set_clip_path(cp)
            elif kind == 'circle':
                (cx, cy), = T([a['c']])
                o = MCircle((cx, cy), a['r'] * k, fc=a['fill'] if a['fill'] else 'none', ec=a['edge'] if a['edge'] else 'none', lw=a['lw'] * PT, zorder=a['z'], ls=a['ls'])
                ax.add_patch(o)
                if cp: o.set_clip_path(cp)
            elif kind == 'arc':
                (cx, cy), = T([a['c']])
                o = MArc((cx, cy), 2 * a['r'] * k, 2 * a['r'] * k, theta1=a['a0'], theta2=a['a1'], lw=a['lw'] * PT, color=a['color'], zorder=a['z'], ls=a['ls'])
                ax.add_patch(o)
                if cp: o.set_clip_path(cp)
            elif kind == 'text':
                (px, py), = T([a['p']])
                if clip and not (clip[0] <= px <= clip[2] and clip[1] <= py <= clip[3]): continue
                kw = dict(fontsize=a['size'] * PT, ha=a['ha'], va=a['va'], rotation=a['rot'], color=a['color'], fontweight=a['weight'], zorder=a['z'],
                          family=a['font'] or FONT, rotation_mode='anchor', linespacing=1.15)
                if a['box']: kw['bbox'] = dict(boxstyle='square,pad=0.25', fc=a['box'], ec='none')
                o = ax.text(px, py, a['s'], **kw)
                if a['halo']:
                    import matplotlib.patheffects as pe
                    o.set_path_effects([pe.withStroke(linewidth=1.6, foreground='white')])
                if cp: o.set_clip_path(cp)
        self.views.append((dwg, scale, model_xy, paper_xy))
    def save(self, path, pdf=None):
        if pdf is not None: pdf.savefig(self.fig)
        else: self.fig.savefig(path)
    def png(self, path, dpi=60): self.fig.savefig(path, dpi=dpi)
    def close(self): plt.close(self.fig)

# --------------------------------------------------------------------------------------------------------- DXF
def to_dxf(dwgs, path, scale=100):
    """write drawings into one DXF in model metres. dwgs = [(Drawing, (dx, dy) offset in metres)]"""
    doc = ezdxf.new('R2010', setup=True)
    doc.header['$INSUNITS'] = 6; doc.header['$MEASUREMENT'] = 1
    for nm, (col, lwt) in LAYERS.items():
        if nm not in doc.layers: doc.layers.add(nm, color=col, lineweight=lwt if lwt else -3)
    msp = doc.modelspace()
    ls_map = {'--': 'DASHED', ':': 'DOT', '-.': 'DASHDOT'}
    for dwg, (dx, dy) in dwgs:
        k = 1.0 if not dwg.paper else scale / 1000.0
        T = lambda p: ((p[0]) * k + dx, (p[1]) * k + dy)
        for kind, layer, a in dwg.items:
            if layer not in doc.layers: doc.layers.add(layer)
            at = {'layer': layer}
            if kind == 'line':
                if a.get('ls') in ls_map: at['linetype'] = ls_map[a['ls']]
                msp.add_lwpolyline([T(p) for p in a['pts']], close=a['closed'], dxfattribs=at)
            elif kind == 'poly':
                for ring in a['rings']:
                    msp.add_lwpolyline([T(p) for p in ring[:-1]], close=True, dxfattribs=at)
                if a['fill'] and a['fill'] not in ('none', 'white', '#ffffff', '#FFFFFF') and layer in ('A-WALL', 'A-COLS', 'F-RATE', 'S-DETL'):
                    h = msp.add_hatch(color=7 if layer != 'F-RATE' else 1, dxfattribs={'layer': layer})
                    for i, ring in enumerate(a['rings']):
                        h.paths.add_polyline_path([T(p) for p in ring[:-1]], is_closed=True, flags=1 if i == 0 else 0)
            elif kind == 'circle':
                msp.add_circle(T(a['c']), a['r'] * k, dxfattribs=at)
            elif kind == 'arc':
                msp.add_arc(T(a['c']), a['r'] * k, a['a0'], a['a1'], dxfattribs=at)
            elif kind == 'text':
                h = a['size'] * scale / 1000.0 * (1.0 if not dwg.paper else 1.0)
                for i, line in enumerate(a['s'].split('\n')):
                    t = msp.add_text(line, height=h, rotation=a['rot'], dxfattribs={'layer': layer, 'style': 'OpenSans'})
                    al = {('center', 'center'): TextEntityAlignment.MIDDLE_CENTER, ('left', 'center'): TextEntityAlignment.MIDDLE_LEFT,
                          ('right', 'center'): TextEntityAlignment.MIDDLE_RIGHT, ('center', 'bottom'): TextEntityAlignment.BOTTOM_CENTER,
                          ('left', 'bottom'): TextEntityAlignment.BOTTOM_LEFT, ('center', 'top'): TextEntityAlignment.TOP_CENTER,
                          ('left', 'top'): TextEntityAlignment.TOP_LEFT, ('right', 'bottom'): TextEntityAlignment.BOTTOM_RIGHT}.get((a['ha'], a['va']), TextEntityAlignment.MIDDLE_CENTER)
                    p = T(a['p']); r = math.radians(a['rot'])
                    off = i * h * 1.4
                    t.set_placement((p[0] + math.sin(r) * off, p[1] - math.cos(r) * off), align=al)
    doc.saveas(path)
