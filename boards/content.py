# -*- coding: utf-8 -*-
INK = '#1F2A2E'; MUTE = '#566064'; TERRA = '#B4492B'; NAVY = '#2C3E64'; PAPER = '#F4F1EA'; RULE = '#C9C3B6'
def A(x, y, w, inner='', h=None, st=''):
    hh = f'height:{h}px;' if h is not None else ''
    return f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;{hh}{st}">{inner}</div>'
def IMG(src, x, y, w, h, alt, fit='contain', st=''):
    return f'<img src="{src}" alt="{alt}" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;object-fit:{fit};{st}">'
def SQ(n_on=2, col=TERRA, size=7):
    out = ''
    for i in range(3):
        fill = col if i < n_on else 'transparent'
        out += f'<span style="display:inline-block;width:{size}px;height:{size}px;margin-right:3px;background:{fill};border:1.2px solid {col};box-sizing:border-box;vertical-align:1px"></span>'
    return out
def SH(x, y, w, num, title, sub='', on=2, col=TERRA, dark=False):
    c = '#F4F1EA' if dark else INK
    s = f'<span style="font-family:DM Sans, Arial, sans-serif;font-weight:400;font-size:10px;white-space:nowrap;color:{"#C8D0D8" if dark else MUTE};margin-left:6px">{sub}</span>' if sub else ''
    return A(x, y, w, f'<div style="display:flex;align-items:center;gap:6px;border-bottom:1px solid {"#8C97A8" if dark else INK};padding-bottom:4px">'
             f'<span style="white-space:nowrap">{SQ(on, col)}</span><span style="font-family:DM Sans, Arial, sans-serif;font-weight:700;font-size:12.5px;color:{col}">{num}</span>'
             f'<span style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:12.5px;letter-spacing:0.05em;color:{c};white-space:nowrap">{title}</span>{s}</div>')
def P(text, size=10.5, lh=1.38, col=INK, st=''):
    return f'<p style="margin:0;font-size:{size}px;line-height:{lh};color:{col};{st}">{text}</p>'
def BOX(x, y, w, title, body, dark=False, st=''):
    bc = 'rgba(255,255,255,0.85)' if dark else '#4C565A'
    bg = 'rgba(30,40,62,0.55)' if dark else 'rgba(255,255,255,0.82)'
    tc = '#FFFFFF' if dark else INK
    return A(x, y, w, f'<div style="border:1px dashed {bc};background:{bg};padding:4px 6px 5px">'
             f'<div style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:9.5px;letter-spacing:0.04em;color:{tc}">{title}</div>'
             f'<div style="font-size:9.5px;line-height:1.3;color:{tc}">{body}</div></div>', st=st)
def LEADERS(w, h, lines, col='#3D474B', dot='#B4492B'):
    import math
    out = ''
    for (x1, y1, x2, y2) in lines:
        L = math.hypot(x2 - x1, y2 - y1); ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        out += (f'<div aria-hidden="true" style="position:absolute;left:{x1:.1f}px;top:{y1:.1f}px;width:{L:.1f}px;height:0;border-top:1px dashed {col};'
                f'transform-origin:0 0;transform:rotate({ang:.2f}deg)"></div>')
        out += f'<div aria-hidden="true" style="position:absolute;left:{x2 - 3.5:.1f}px;top:{y2 - 3.5:.1f}px;width:7px;height:7px;border-radius:4px;background:{dot};border:1px solid #FFFFFF;box-sizing:border-box"></div>'
    return out

MMPX = 96 / 25.4
def SCALEBAR(x, y, N, ticks, label=None, bg=True):
    """true-scale bar for 1:N at 96 px/in; ticks in metres e.g. [0,1,2,5,10]"""
    ppm = 1000 / N * MMPX
    W = ticks[-1] * ppm
    segs = ''
    for i in range(len(ticks) - 1):
        a, b = ticks[i] * ppm, ticks[i + 1] * ppm
        segs += f'<div style="position:absolute;left:{a:.2f}px;top:12px;width:{b - a:.2f}px;height:5px;background:{INK if i % 2 == 0 else "#FFFFFF"};border:1px solid {INK};box-sizing:border-box"></div>'
    labs = ''.join(f'<div style="position:absolute;left:{t * ppm - 10:.2f}px;top:0;width:20px;text-align:center;font-size:8px;font-weight:700;color:{INK}">{t}</div>' for t in ticks)
    lab = label or f'SCALE 1:{N} · METRES'
    inner = f'<div style="position:relative;width:{W:.2f}px;height:20px">{segs}{labs}<div style="position:absolute;left:{W + 6:.2f}px;top:9px;font-size:8px;font-weight:700;white-space:nowrap;color:{INK}">M</div></div><div style="font-size:8px;font-weight:700;letter-spacing:0.08em;color:{INK};margin-top:3px;white-space:nowrap">{lab}</div>'
    st = 'background:rgba(255,255,255,0.88);padding:4px 16px 4px 8px;border:1px solid #C9C3B6' if bg else ''
    return f'<div style="position:absolute;left:{x}px;top:{y}px;{st}">{inner}</div>'
def NORTH(x, y, s=26):
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{s}px;text-align:center">'
            f'<div style="font-family:Syne, Arial, sans-serif;font-weight:800;font-size:11px;color:{INK};line-height:1">N</div>'
            f'<div style="width:0;height:0;margin:2px auto 0;border-left:{s * 0.32:.1f}px solid transparent;border-right:{s * 0.32:.1f}px solid transparent;border-bottom:{s:.1f}px solid {INK}"></div></div>')
def PAGEHEAD(x, y, w, sheet, title, sub):
    return A(x, y, w, f'<div style="display:flex;align-items:flex-end;justify-content:space-between;border-bottom:2px solid {INK};padding-bottom:5px">'
             f'<div style="display:flex;align-items:baseline;gap:12px"><span style="font-family:Syne, Arial, sans-serif;font-weight:800;font-size:22px;color:{INK}">TITIK TEMU</span>'
             f'<span style="font-family:Syne, Arial, sans-serif;font-weight:700;font-size:12px;color:{TERRA};letter-spacing:0.04em">{title}</span></div>'
             f'<div style="text-align:right;font-size:8.5px;line-height:1.35;color:{MUTE};letter-spacing:0.06em">{sub}<br><b style="color:{INK}">{sheet}</b></div></div>')
