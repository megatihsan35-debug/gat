// Interior vignette kit. World coords: x east, y north, z up (metres). three: (x, z, -y)
import * as THREE from 'three';
export const V = (x, y, z) => new THREE.Vector3(x, z, -y);
export const D2R = Math.PI / 180;
export const pol = (r, b) => [r * Math.sin(b * D2R), r * Math.cos(b * D2R)];   // bearing b (deg)

export let ROOT, LINE = false;
export function setRoot(g, line) { ROOT = g; LINE = line; }

const MC = {};
export function M(hex, o = {}) {
  const k = hex + JSON.stringify(o); if (MC[k]) return MC[k];
  let m;
  if (LINE) m = new THREE.MeshBasicMaterial({ color: o.emit ? 0xffffff : 0xffffff, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
  else if (o.emit) m = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: new THREE.Color(hex), emissiveIntensity: o.emit, side: THREE.DoubleSide });
  else if (o.glass) m = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(hex), roughness: o.r ?? 0.05, metalness: 0, transmission: 0, transparent: true, opacity: o.glass, side: THREE.DoubleSide, envMapIntensity: 1.2 });
  else m = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(hex), roughness: o.r ?? 0.6, metalness: o.m ?? 0, clearcoat: o.cc ?? 0, clearcoatRoughness: 0.1, side: THREE.DoubleSide, envMapIntensity: o.env ?? 1, transparent: !!o.op, opacity: o.op ?? 1 });
  m.userData.emit = !!o.emit; m.userData.glass = !!o.glass;
  return (MC[k] = m);
}
export function add(geo, mat, edges = true, angle = 30) {
  const me = new THREE.Mesh(geo, mat); ROOT.add(me);
  if (LINE && edges && !mat.userData.glass) {
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(geo, angle), new THREE.LineBasicMaterial({ color: 0x1a1a1a }));
    ROOT.add(e);
  }
  return me;
}
// ---------------------------------------------------------------- primitives
export function prism(pts, z0, z1, mat, holes = [], edges = true) {
  const sh = new THREE.Shape(pts.map(p => new THREE.Vector2(p[0], p[1])));
  for (const h of holes) sh.holes.push(new THREE.Path(h.map(p => new THREE.Vector2(p[0], p[1]))));
  const g = new THREE.ExtrudeGeometry(sh, { depth: z1 - z0, bevelEnabled: false, curveSegments: 24 });
  g.rotateX(-Math.PI / 2); g.translate(0, z0, 0);
  return add(g, mat, edges);
}
export function box(x0, y0, x1, y1, z0, z1, mat) { return prism([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], z0, z1, mat); }
export function arcPts(cx, cy, r, b0, b1, n = 48) { const o = []; for (let i = 0; i <= n; i++) { const b = b0 + (b1 - b0) * i / n; const [x, y] = pol(r, b); o.push([cx + x, cy + y]); } return o; }
export function sector(cx, cy, r0, r1, b0, b1, n = 48) { return arcPts(cx, cy, r1, b0, b1, n).concat(r0 > 0 ? arcPts(cx, cy, r0, b1, b0, n) : [[cx, cy]]); }
export function disk(cx, cy, r, n = 64) { return arcPts(cx, cy, r, 0, 360, n).slice(0, -1); }
// grid surface z = f(x, y) over a param domain (u,v) -> [x,y]; f gives z
export function surf(nu, nv, xy, zf, mat, edges = false) {
  const pos = [], idx = [];
  for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) { const [x, y] = xy(i / nu, j / nv); const z = zf(x, y, i / nu, j / nv); pos.push(x, z, -y); }
  for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) { const a = j * (nu + 1) + i, b = a + 1, c = a + nu + 1, d = c + 1; idx.push(a, c, b, b, c, d); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return add(g, mat, edges, 50);
}
// vertical ribbon through a polyline from z0(i) to z1(i)
export function wallStrip(pts, z0, z1, mat, edges = true) {
  const pos = [], idx = [];
  pts.forEach((p, i) => { const a = typeof z0 === 'function' ? z0(i, p) : z0, b = typeof z1 === 'function' ? z1(i, p) : z1; pos.push(p[0], a, -p[1], p[0], b, -p[1]); });
  for (let i = 0; i < pts.length - 1; i++) { const a = 2 * i; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return add(g, mat, edges, 40);
}
export function tube(pts3, r, mat, closed = false, seg = 0) {
  const c = new THREE.CatmullRomCurve3(pts3.map(p => V(...p)), closed, 'centripetal');
  const g = new THREE.TubeGeometry(c, seg || Math.max(16, pts3.length * 12), r, 8, closed);
  return add(g, mat, false);
}
export function line(pts3, r, hex, emit = 4) { return tube(pts3, r, M(hex, { emit })); }
export function cyl(x, y, z0, z1, r, mat, rt = null, seg = 32) {
  const g = new THREE.CylinderGeometry(rt ?? r, r, z1 - z0, seg, 1); g.translate(0, (z0 + z1) / 2, 0); g.translate(x, 0, -y);
  return add(g, mat, true, 40);
}
export function sphere(x, y, z, r, mat, s = [1, 1, 1]) { const g = new THREE.SphereGeometry(r, 32, 20); g.scale(...s); g.translate(x, z, -y); return add(g, mat, true, 60); }
export function lathe(x, y, z, prof, mat, seg = 40) { const g = new THREE.LatheGeometry(prof.map(p => new THREE.Vector2(p[0], p[1])), seg); g.translate(x, z, -y); return add(g, mat, true, 50); }
export function torus(x, y, z, R, r, mat, arc = Math.PI * 2, rotX = Math.PI / 2, rotY = 0) { const g = new THREE.TorusGeometry(R, r, 16, 96, arc); g.rotateX(rotX); g.rotateY(rotY); g.translate(x, z, -y); return add(g, mat, false); }
// ---------------------------------------------------------------- props
export function person(x, y, s = 1, hex = 0xf4f4f2, face = 0) {
  const m = M(hex, { r: 0.9 });
  const h = 1.7 * s;
  lathe(x, y, 0, [[0, 0], [0.13 * s, 0], [0.16 * s, 0.5 * s], [0.2 * s, 0.95 * s], [0.23 * s, 1.3 * s], [0.18 * s, 1.42 * s], [0.06 * s, 1.47 * s], [0, 1.47 * s]], m, 20);
  sphere(x, y, 1.58 * s, 0.11 * s, m);
}
export function seat(x, y, mat, r = 0.22, h = 0.45) { cyl(x, y, 0, h, r, mat, r * 0.95); }
export function stool(x, y, z = 0, h = 0.75, mat) { cyl(x, y, z, z + h - 0.05, 0.03, M('#9a7b4f', { m: 0.8, r: 0.3 })); cyl(x, y, z + h - 0.05, z + h, 0.19, mat); }
export function plant(x, y, z, s = 1, hex = '#4f8a3c', pot = null) {
  if (pot) lathe(x, y, z, [[0, 0], [0.22 * s, 0], [0.28 * s, 0.5 * s], [0.25 * s, 0.52 * s], [0, 0.52 * s]], pot, 28);
  const z0 = z + (pot ? 0.5 * s : 0), lm = M(hex, { r: 0.7 }), lm2 = M(shade(hex, 1.25), { r: 0.7 });
  for (let i = 0; i < 9; i++) {
    const a = i * 40 + 13 * (i % 3), up = 0.45 + 0.35 * ((i * 7) % 5) / 4, L = (0.55 + 0.25 * ((i * 3) % 4) / 3) * s;
    const pts = []; for (let k = 0; k <= 8; k++) { const t = k / 8; const rr = L * t; const [dx, dy] = pol(rr, a); pts.push([x + dx, y + dy, z0 + Math.sin(t * Math.PI * 0.9) * up * s * 0.9]); }
    leaf(pts, 0.09 * s, i % 2 ? lm : lm2);
  }
}
function leaf(pts, w, mat) {
  const pos = [], idx = [];
  pts.forEach((p, i) => { const t = i / (pts.length - 1); const ww = w * Math.sin(Math.PI * Math.min(1, t * 1.15)); const nx = i < pts.length - 1 ? pts[i + 1] : pts[i]; const pv = i > 0 ? pts[i - 1] : pts[i];
    const dx = nx[0] - pv[0], dy = nx[1] - pv[1], l = Math.hypot(dx, dy) || 1; const ox = -dy / l * ww, oy = dx / l * ww;
    pos.push(p[0] + ox, p[2], -(p[1] + oy), p[0] - ox, p[2], -(p[1] - oy)); });
  for (let i = 0; i < pts.length - 1; i++) { const a = 2 * i; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return add(g, mat, false);
}
export function palm(x, y, z, s, hex, pot) {
  if (pot) lathe(x, y, z, [[0, 0], [0.42 * s, 0], [0.5 * s, 0.7 * s], [0.46 * s, 0.72 * s], [0, 0.72 * s]], pot, 36);
  const z0 = z + (pot ? 0.7 * s : 0), H = 2.2 * s;
  tube([[x, y, z0], [x + 0.05, y, z0 + H * 0.5], [x + 0.1, y + 0.03, z0 + H]], 0.06 * s, M('#7a6248', { r: 0.9 }));
  const lm = M(hex, { r: 0.6 });
  for (let i = 0; i < 11; i++) { const a = i * 360 / 11 + (i % 2) * 9; const L = (1.2 + 0.3 * (i % 3) / 2) * s; const pts = [];
    for (let k = 0; k <= 10; k++) { const t = k / 10; const [dx, dy] = pol(L * t, a); pts.push([x + 0.1 + dx, y + 0.03 + dy, z0 + H + Math.sin(t * Math.PI * 0.75) * 0.45 * s - t * t * 0.9 * s]); }
    leaf(pts, 0.16 * s, lm); }
}
export function shade(hex, f) { const c = new THREE.Color(hex); c.r = Math.min(1, c.r * f); c.g = Math.min(1, c.g * f); c.b = Math.min(1, c.b * f); return '#' + c.getHexString(); }
// recessed linear LED: a thin emissive tube along a 2D/3D polyline
export function ledArc(cx, cy, r, b0, b1, z, hex, w = 0.018, emit = 5) { return line(arcPts(cx, cy, r, b0, b1, 64).map(p => [p[0], p[1], z]), w, hex, emit); }
export function pointL(x, y, z, hex, i, d = 8) { if (LINE) return; const l = new THREE.PointLight(new THREE.Color(hex), i, d, 2); l.position.copy(V(x, y, z)); ROOT.add(l); return l; }
export function spotL(x, y, z, tx, ty, tz, hex, i, ang = 0.5, d = 12) { if (LINE) return; const l = new THREE.SpotLight(new THREE.Color(hex), i, d, ang, 0.6, 2); l.position.copy(V(x, y, z)); l.target.position.copy(V(tx, ty, tz)); ROOT.add(l); ROOT.add(l.target); return l; }
export function rectL(x, y, z, w, h, hex, i, lookAt) { if (LINE) return; const l = new THREE.RectAreaLight(new THREE.Color(hex), i, w, h); l.position.copy(V(x, y, z)); l.lookAt(V(...lookAt)); ROOT.add(l); return l; }
// canvas texture helper for patterns / graphics
export function ctex(w, h, draw, rep = [1, 1]) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); t.anisotropy = 8; return t;
}
export function TM(tex, o = {}) {
  if (LINE) return M('#fff');
  const m = new THREE.MeshPhysicalMaterial({ map: tex, roughness: o.r ?? 0.5, metalness: o.m ?? 0, clearcoat: o.cc ?? 0, clearcoatRoughness: 0.08, side: THREE.DoubleSide, envMapIntensity: o.env ?? 1 });
  if (o.emitMap) { m.emissiveMap = o.emitMap; m.emissive = new THREE.Color(o.emitHex || '#ffffff'); m.emissiveIntensity = o.emit ?? 1; }
  return m;
}
// planar UVs (x,y in metres / scale) for ExtrudeGeometry tops
export function planarUV(mesh, s = 1) {
  const g = mesh.geometry, p = g.attributes.position, uv = [];
  for (let i = 0; i < p.count; i++) uv.push(p.getX(i) / s, -p.getZ(i) / s);
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); return mesh;
}
