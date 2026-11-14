// Sketch-diagram helpers on top of rough.js
const C = {
  paper: '#F3EEE4', ink: '#22282B', soft: '#5A6166', brick: '#B4492B', teal: '#2D6E73',
  orange: '#E08A1E', green: '#7FA84A', glass: '#5BA7C9', purple: '#7A5BA8', red: '#C8372D',
  pub: '#F2B045', semi: '#9CC26A', priv: '#6FA9D2', serv: '#A99BC4', sand: '#E6D3B0'
};
let svg, rc, W, H;
function setup(w, h, bg) {
  W = w; H = h;
  svg = document.getElementById('s');
  svg.setAttribute('width', w); svg.setAttribute('height', h);
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  rc = rough.svg(svg);
  if (bg !== null) rect0(0, 0, w, h, bg || C.paper);
}
function el(tag, attrs, parent) {
  const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  (parent || svg).appendChild(e); return e;
}
function rect0(x, y, w, h, fill, op) { return el('rect', { x, y, width: w, height: h, fill, opacity: op == null ? 1 : op }); }
function img(href, x, y, w, h, op) { return el('image', { href, x, y, width: w, height: h, opacity: op == null ? 1 : op, preserveAspectRatio: 'none' }); }
function add(n) { svg.appendChild(n); return n; }
const base = (o) => Object.assign({ roughness: 1.3, bowing: 1.2, stroke: C.ink, strokeWidth: 3 }, o || {});
function line(x1, y1, x2, y2, o) { return add(rc.line(x1, y1, x2, y2, base(o))); }
function lp(pts, o) { return add(rc.linearPath(pts, base(o))); }
function crv(pts, o) { return add(rc.curve(pts, base(o))); }
function poly(pts, o) { return add(rc.polygon(pts, base(o))); }
function circ(cx, cy, d, o) { return add(rc.circle(cx, cy, d, base(o))); }
function ell(cx, cy, w, h, o) { return add(rc.ellipse(cx, cy, w, h, base(o))); }
function rect(x, y, w, h, o) { return add(rc.rectangle(x, y, w, h, base(o))); }
function pth(d, o) { return add(rc.path(d, base(o))); }
// watercolour wash: few translucent solid layers
function wash(pts, color, op, n) {
  n = n || 2; const g = el('g', { opacity: op == null ? 0.45 : op });
  for (let i = 0; i < n; i++) g.appendChild(rc.polygon(pts, { fill: color, fillStyle: 'solid', stroke: 'none', roughness: 2.2, bowing: 3, seed: 10 + i * 7 }));
  return g;
}
function washEll(cx, cy, w, h, color, op) {
  const g = el('g', { opacity: op == null ? 0.45 : op });
  for (let i = 0; i < 2; i++) g.appendChild(rc.ellipse(cx, cy, w * (1 - i * 0.06), h * (1 - i * 0.06), { fill: color, fillStyle: 'solid', stroke: 'none', roughness: 2, seed: 3 + i }));
  return g;
}
function head(x1, y1, x2, y2, size, color, open) {
  const a = Math.atan2(y2 - y1, x2 - x1), s = size || 22;
  const p1 = [x2 - s * Math.cos(a - 0.45), y2 - s * Math.sin(a - 0.45)];
  const p2 = [x2 - s * Math.cos(a + 0.45), y2 - s * Math.sin(a + 0.45)];
  if (open) { lp([p1, [x2, y2], p2], { stroke: color, strokeWidth: 3, roughness: 0.6 }); }
  else add(rc.polygon([p1, [x2, y2], p2], { fill: color, fillStyle: 'solid', stroke: color, strokeWidth: 2, roughness: 0.5 }));
}
function arrow(x1, y1, x2, y2, o) {
  o = o || {}; const c = o.stroke || C.ink;
  line(x1, y1, x2, y2, o); head(x1, y1, x2, y2, o.hs || 24, c, o.open);
  if (o.both) head(x2, y2, x1, y1, o.hs || 24, c, o.open);
}
function carrow(pts, o) { // curved arrow through points
  o = o || {}; const c = o.stroke || C.ink; crv(pts, o);
  const n = pts.length; head(pts[n - 2][0], pts[n - 2][1], pts[n - 1][0], pts[n - 1][1], o.hs || 24, c, o.open);
}
function dashFlow(pts, color, o) { // orange-marker style dashed flow
  o = Object.assign({ stroke: color, strokeWidth: 9, strokeLineDash: [24, 14], roughness: 0.7, bowing: 0.5 }, o || {});
  crv(pts, o); const n = pts.length; head(pts[n - 2][0], pts[n - 2][1], pts[n - 1][0], pts[n - 1][1], o.hs || 34, color);
}
function T(txt, x, y, o) {
  o = o || {};
  const t = el('text', {
    x, y, 'font-family': o.font || 'AD, sans-serif', 'font-size': o.size || 30, fill: o.color || C.ink,
    'text-anchor': o.anchor || 'start', 'font-weight': o.weight || 400,
    transform: o.rot ? `rotate(${o.rot} ${x} ${y})` : ''
  });
  if (o.halo) { t.setAttribute('stroke', o.halo); t.setAttribute('stroke-width', o.haloW || 8); t.setAttribute('paint-order', 'stroke'); t.setAttribute('stroke-linejoin', 'round'); }
  const lines = String(txt).split('\n');
  lines.forEach((l, i) => { const s = el('tspan', { x, dy: i ? (o.lh || 1.15) * (o.size || 30) : 0 }, t); s.textContent = l; });
  return t;
}
function ulTitle(txt, x, y, size, color) { T(txt, x, y, { size: size || 40, color: color || C.ink }); line(x, y + 12, x + (size || 40) * 0.52 * txt.length, y + 10, { strokeWidth: 2.5, stroke: color || C.ink }); }
function northArrow(x, y, s, rotDeg) {
  s = s || 60; const r = (rotDeg || 0) * Math.PI / 180;
  const R = (px, py) => [x + px * Math.cos(r) - py * Math.sin(r), y + px * Math.sin(r) + py * Math.cos(r)];
  poly([R(0, -s), R(s * 0.35, s * 0.5), R(0, s * 0.25), R(-s * 0.35, s * 0.5)], { fill: C.ink, fillStyle: 'solid', roughness: 0.6, strokeWidth: 2 });
  const p = R(0, -s - 18); T('N', p[0], p[1], { size: 32, anchor: 'middle' });
}
// Asymmetric Gerono figure-8 along local axis. returns points in local (u,v), big loop u>0
function eightPts(aBig, hBig, aSmall, hSmall, n) {
  n = n || 160; const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n * Math.PI * 2, c = Math.cos(t), s = Math.sin(t);
    const big = c >= 0;
    pts.push([c * (big ? aBig : aSmall), 2 * s * c * (big ? hBig : hSmall)]);
  }
  return pts;
}
function loopPts(a, h, sign, n, scale, cu) { // single Gerono loop, optional scale about centre cu
  n = n || 90; const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = -Math.PI / 2 + i / n * Math.PI; const c = Math.cos(t), s = Math.sin(t);
    let u = sign * c * a, v = 2 * s * c * h;
    if (scale) { u = cu + (u - cu) * scale; v = v * scale; }
    pts.push([u, v]);
  }
  return pts;
}
function xf(pts, ox, oy, angDeg, k) { // local->screen: u along angle (screen degrees, 0 = +x), scale k px per unit
  const a = angDeg * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
  return pts.map(([u, v]) => [ox + k * (u * ca - v * sa), oy + k * (u * sa + v * ca)]);
}
// isometric projection
function iso(ox, oy, k) { return (x, y, z) => [ox + (x - y) * 0.866 * k, oy + (x + y) * 0.5 * k - z * k]; }
function done() { window.__done = true; }
