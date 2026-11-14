// Titik Temu interior vignettes. World coords from the drawings (m). z = height above the floor (FFL = 0).
import * as THREE from 'three';
import { V, M, add, prism, box, arcPts, sector, disk, surf, wallStrip, tube, line, cyl, sphere, lathe, torus, person, stool, plant, palm,
         shade, ledArc, pointL, spotL, rectL, ctex, TM, planarUV, pol, D2R, LINE } from './kit.js';
const P = await (await fetch('plan.json')).json();
export const B = P.B, S = P.S;
const M0 = 274.3, mod = i => [(M0 + 18 * (i - 1)), (M0 + 18 * i)];
const at = (C, r, b) => { const [x, y] = pol(r, b); return [C[0] + x, C[1] + y]; };
const R_COURT = 9, R_VER = 11, R_DISP = 14.75, R_OUT = 18.1, SOF = 4.1;
export const ST = {
  KEL: { n: 'Kelantan', b: 356.2, km: 298, c: '#3456D6' }, TRG: { n: 'Terengganu', b: 20.9, km: 224, c: '#11A89A' },
  PHG: { n: 'Pahang', b: 68.4, km: 108, c: '#8CC9E0' }, JHR: { n: 'Johor', b: 145.9, km: 263, c: '#E8B523' },
  MLK: { n: 'Melaka', b: 187.6, km: 141, c: '#B83A2E' }, NSN: { n: 'Negeri Sembilan', b: 213.3, km: 96, c: '#9A6A45' },
  SGR: { n: 'Selangor', b: 247.3, km: 108, c: '#B5E655' }, PRK: { n: 'Perak', b: 311.0, km: 195, c: '#C9A27A' },
  PNG: { n: 'Pulau Pinang', b: 313.4, km: 318, c: '#E46F8C' }, KDH: { n: 'Kedah', b: 322.7, km: 374, c: '#4E8F3A' },
  PLS: { n: 'Perlis', b: 323.6, km: 414, c: '#F28C28' } };
// ---------------------------------------------------------------- shared finishes
const WHITE = () => M('#f4f2ee', { r: 0.35 }), GRG = () => M('#f7f6f3', { r: 0.55 }), BRONZE = () => M('#9c7a4c', { m: 0.9, r: 0.28 });
const ALU = () => M('#c9ccd0', { m: 0.85, r: 0.3 }), MINT = () => M('#bfe8dc', { glass: 0.28 }), TIMBER = () => M('#8a5a36', { r: 0.55 });
const TERRA = () => M('#b4492b', { r: 0.8 });
function terrazzoTex(base = '#ece8e1', chips = ['#cfc7bb', '#b9b1a6', '#ffffff', '#9c958c'], n = 2600, s = 1024) {
  return ctex(s, s, (g, w, h) => { g.fillStyle = base; g.fillRect(0, 0, w, h);
    let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < n; i++) { g.fillStyle = chips[i % chips.length]; const x = rnd() * w, y = rnd() * h, r = 1 + rnd() * 3.5; g.beginPath(); g.ellipse(x, y, r, r * (0.5 + rnd() * 0.5), rnd() * 3, 0, 7); g.fill(); } }, [1, 1]);
}
let _tz = null; const TERRAZZO = () => LINE ? M('#fff') : (_tz ??= TM(terrazzoTex(), { r: 0.18, cc: 0.6, env: 1.1 }));
function floorT(pts, mat, s = 2.2, z = 0) { return planarUV(prism(pts, z - 0.05, z, mat, [], false), s); }
// brass bearing line with a state light at its end
function bearingLine(C, st, r0, r1, z = 0.004, glow = true) {
  const a = at(C, r0, st.b), b = at(C, r1, st.b);
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy), nx = -dy / L * 0.012, ny = dx / L * 0.012;
  prism([[a[0] + nx, a[1] + ny], [b[0] + nx, b[1] + ny], [b[0] - nx, b[1] - ny], [a[0] - nx, a[1] - ny]], -0.01, z, M('#c8a050', { m: 1, r: 0.2 }), [], false);
  if (glow) { const e = at(C, r1 - 0.12, st.b); cyl(e[0], e[1], 0, 0.012, 0.07, M(st.c, { emit: 3 })); }
}
function sky(top = '#5d79a3', bot = '#f1c9a0') {
  if (LINE) return; const t = ctex(4, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, top); gr.addColorStop(0.55, shade(bot, 0.95)); gr.addColorStop(1, bot); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  const m = new THREE.MeshBasicMaterial({ map: t, side: THREE.BackSide, depthWrite: false, fog: false });
  const s = new THREE.Mesh(new THREE.SphereGeometry(180, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.62), m); s.position.set(B[0], -20, -B[1]); add(s.geometry, m, false).position.copy(s.position);
}
function ground(r = 80, hex = '#8f9a7e') { prism(disk(B[0], B[1], r, 48), -0.4, -0.06, M(hex, { r: 1 }), [], false); }
// generic ring context: verandah floor, soffit, shop fronts with each state's light line
const MODULE_ST = { 5: 'KEL', 6: 'TRG', 13: 'JHR', 16: 'MLK' };
function ringContext(skipMods = [], opts = {}) {
  const C = B;
  floorT(disk(C[0], C[1], R_VER + 0.02, 120), TERRAZZO());
  // court floor river bands (Sungai Pahang) inside r 9
  if (!LINE) { const rv = ctex(1024, 1024, (g, w, h) => { g.fillStyle = '#e9e4dc'; g.fillRect(0, 0, w, h); g.lineCap = 'round';
      for (let k = 0; k < 7; k++) { g.strokeStyle = ['#cdd9dc', '#b8cbd1', '#dde4e3', '#a9bfc7', '#cfd8d6', '#c3d2d6', '#e1e7e6'][k]; g.lineWidth = 34 - k * 3; g.beginPath();
        for (let x = -50; x <= w + 50; x += 8) { const y = h * (0.22 + k * 0.09) + Math.sin(x / 140 + k * 0.7) * 60 + Math.sin(x / 61 + k) * 14; x < -40 ? g.moveTo(x, y) : g.lineTo(x, y); } g.stroke(); } });
    planarUV(prism(disk(C[0], C[1], R_COURT - 0.3, 120), -0.03, 0.002, TM(rv, { r: 0.25, cc: 0.4 }), [], false), 18); }
  // soffit over verandah and shops
  prism(sector(C[0], C[1], R_COURT - 0.15, R_OUT + 1.5, 0, 360, 160).slice(0, -1).length ? arcPts(C[0], C[1], R_OUT + 1.5, 0, 360, 160) : [], SOF, SOF + 0.35, GRG(), [arcPts(C[0], C[1], R_COURT - 0.15, 360, 0, 160)], false);
  ledArc(C[0], C[1], R_COURT - 0.1, 0, 360, SOF - 0.02, '#ffd7a0', 0.015, 2.2);
  // columns on the court ring (every 36 deg)
  for (let k = 0; k < 10; k++) { const p = at(C, R_COURT, M0 + 36 * k); cyl(p[0], p[1], 0, SOF, 0.16, WHITE()); }
  for (let m = 1; m <= 20; m++) {
    if (skipMods.includes(m)) continue;
    const [b0, b1] = mod(m), bc = (b0 + b1) / 2;
    if ([1, 2, 20, 9, 17, 19].includes(m)) continue;                 // lobby + gates handled separately / open
    const st = ST[MODULE_ST[m]]; const col = st ? st.c : (m === 11 || m === 12 ? '#C9A27A' : '#e8e2d6');
    // piers + fascia + light line
    prism(sector(C[0], C[1], R_VER, R_VER + 0.45, b0, b0 + 1.2, 6), 0, SOF, WHITE());
    wallStrip(arcPts(C[0], C[1], R_VER, b0, b1, 16), 3.15, SOF, GRG());
    ledArc(C[0], C[1], R_VER - 0.01, b0 + 1.2, b1, 3.15, col, 0.02, 4);
    // inside glow (a lit back wall) so the ring reads as a band of coloured rooms
    wallStrip(arcPts(C[0], C[1], R_DISP, b0, b1, 16), 0, 3.15, M(shade(col, 0.75), { emit: 0.55 }), false);
    prism(sector(C[0], C[1], R_VER, R_DISP, b0, b1, 12), 3.14, 3.16, M('#f2efe9', { r: 0.6 }), [], false);
    floorT(sector(C[0], C[1], R_VER, R_DISP, b0, b1, 12), TERRAZZO());
    // counter
    prism(sector(C[0], C[1], 12.9, 13.5, b0 + 3, b1 - 3, 8), 0, 1.0, M('#f6f5f2', { r: 0.3 }));
  }
  for (const k of Object.keys(ST)) bearingLine(C, ST[k], 1.6, R_COURT - 0.15);
}
// court tree + bench + tables (Talam)
function courtCore(C = B, tables = true) {
  const W = TIMBER();
  prism(disk(C[0], C[1], 1.55, 64), 0, 0.45, W, [disk(C[0], C[1], 1.05, 64)]);
  prism(disk(C[0], C[1], 1.05, 64), 0, 0.5, M('#5b4a3a', { r: 1 }));
  tube([[C[0], C[1], 0.4], [C[0] + 0.1, C[1], 2.2], [C[0] + 0.25, C[1] - 0.1, 3.4]], 0.22, M('#6d5a48', { r: 0.95 }));
  for (const [dx, dy, dz, r] of [[0, 0, 4.6, 2.3], [1.6, 0.6, 4.1, 1.5], [-1.4, -0.5, 4.3, 1.6], [0.3, -1.6, 4.0, 1.4], [-0.6, 1.5, 4.0, 1.5]])
    sphere(C[0] + dx, C[1] + dy, dz, r, M(['#4c7d3b', '#5e9045', '#3f6e33'][Math.abs(Math.round(dx * 3)) % 3], { r: 0.85 }), [1, 0.62, 1]);
  if (!tables) return;
  for (let k = 0; k < 8; k++) { const b = 22.5 + k * 45, p = at(C, 5.4, b);
    cyl(p[0], p[1], 0, 0.72, 0.05, BRONZE()); cyl(p[0], p[1], 0.72, 0.75, 0.62, M('#f6f3ee', { r: 0.25, cc: 0.5 }));
    torus(p[0], p[1], 0.752, 0.6, 0.012, M('#c8a050', { m: 1, r: 0.25 }));
    for (let j = 0; j < 4; j++) { const q = at(p, 0.95, b + 45 + j * 90); stool(q[0], q[1], 0, 0.45, M(['#3456D6', '#11A89A', '#E8B523', '#B83A2E', '#9A6A45', '#B5E655', '#C9A27A', '#E46F8C'][k], { r: 0.5 })); } }
}
// ---------------------------------------------------------------- the stall (A1 / A2) builder
function stall(m, theme) {
  const [b0, b1] = mod(m), bc = (b0 + b1) / 2, C = B;
  ringContext([m]);
  courtCore(B, true);
  sky();
  // party walls + back wall with door
  prism(sector(C[0], C[1], R_VER, R_DISP + 0.15, b0, b0 + 0.8, 6), 0, SOF, WHITE());
  prism(sector(C[0], C[1], R_VER, R_DISP + 0.15, b1 - 0.8, b1, 6), 0, SOF, WHITE());
  floorT(sector(C[0], C[1], R_VER, R_DISP, b0, b1, 24), theme.floor ? theme.floor() : TERRAZZO());
  const back = theme.back || (() => M('#efece6', { r: 0.6 }));
  const dw = 0.95 / R_DISP / D2R;   // door angular width
  wallStrip(arcPts(C[0], C[1], R_DISP, b0, b1 - 2.6 - dw, 24), 0, SOF, back());
  wallStrip(arcPts(C[0], C[1], R_DISP, b1 - 2.6, b1, 6), 0, SOF, back());
  wallStrip(arcPts(C[0], C[1], R_DISP, b1 - 2.6 - dw, b1 - 2.6, 4), 2.1, SOF, back());
  wallStrip(arcPts(C[0], C[1], R_DISP + 0.6, b1 - 2.6 - dw - 1, b1 - 1.6, 6), 0, SOF, M('#3b3b38', { r: 0.9 }), false);   // dark prep room behind
  prism(sector(C[0], C[1], R_DISP - 0.02, R_DISP + 0.04, b1 - 2.6 - dw - 0.2, b1 - 2.4, 4), 0, 2.2, BRONZE());
  // fascia portal: white GRG with rounded opening + state light line
  wallStrip(arcPts(C[0], C[1], R_VER, b0, b1, 30), 3.2, SOF, GRG());
  ledArc(C[0], C[1], R_VER - 0.012, b0 + 0.8, b1 - 0.8, 3.2, theme.c, 0.022, 5);
  // bearing tag on the fascia
  if (!LINE) { const st = theme.st; const tx = ctex(1024, 160, (g, w, h) => { g.fillStyle = '#f7f6f3'; g.fillRect(0, 0, w, h); g.fillStyle = '#22282b'; g.font = '600 64px Helvetica'; g.textBaseline = 'middle';
      g.fillText(`${st.b.toFixed(1)}°`, 60, h / 2); g.fillStyle = theme.c; g.fillRect(330, h / 2 - 4, 120, 8); g.fillStyle = '#6a7176'; g.font = '48px Helvetica'; g.fillText(`${st.km} km`, 480, h / 2); }, [1, 1]);
    const pts = arcPts(C[0], C[1], R_VER - 0.03, bc - 6, bc + 6, 16); const mm = wallStrip(pts, 3.45, 3.9, TM(tx, { r: 0.5 }), false);
    const uv = []; pts.forEach((p, i) => uv.push(1 - i / (pts.length - 1), 0, 1 - i / (pts.length - 1), 1)); mm.geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); }
  theme.build({ b0, b1, bc, C, m });
  const eye = at(C, 9.75, bc - 5.5), tg = at(C, 14.2, bc + 3.2);
  return { eye: [eye[0], eye[1], 1.55], tgt: [tg[0], tg[1], 1.75], fov: 74, bg: '#e9d9c3', hemi: 0.45, sun: [B[0] - 30, B[1] - 40, 40, '#ffe2bd', 1.2], exposure: 1.0, ...(theme.cfg || {}) };
}
// common shop counter on the arc
function counterArc(C, r0, r1, a0, a1, top, front, h = 1.0) {
  prism(sector(C[0], C[1], r0, r1, a0, a1, 16), 0.12, h - 0.04, front);
  prism(sector(C[0], C[1], r0 + 0.04, r1 - 0.04, a0 + 0.3, a1 - 0.3, 16), 0, 0.12, M('#2b2b2b', { r: 0.9 }));
  prism(sector(C[0], C[1], r0 - 0.04, r1 + 0.02, a0 - 0.2, a1 + 0.2, 16), h - 0.04, h, top);
}
function bowls(C, r, a0, a1, z, hex, n = 5) { for (let i = 0; i < n; i++) { const p = at(C, r, a0 + (a1 - a0) * (i + 0.5) / n);
  lathe(p[0], p[1], z, [[0, 0], [0.07, 0], [0.12, 0.07], [0.13, 0.075], [0, 0.075]], M('#f8f8f6', { r: 0.2 }), 24); sphere(p[0], p[1], z + 0.07, 0.085, M(hex, { r: 0.8 }), [1, 0.45, 1]); } }

export const SCENES = {};
// ===================================================================== KELANTAN (A2-1): wau bulan crescent, bunga telang blue
SCENES.kel = { build: () => stall(5, { st: ST.KEL, c: ST.KEL.c,
  back: () => LINE ? M('#fff') : TM(ctex(1024, 512, (g, w, h) => { const gr = g.createLinearGradient(0, h, 0, 0); gr.addColorStop(0, '#1d2f8a'); gr.addColorStop(1, '#6f8cf0'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
      g.strokeStyle = 'rgba(255,255,255,0.55)'; g.lineWidth = 3; for (let k = 0; k < 9; k++) { const cx = 60 + k * 120, cy = 160 + (k % 2) * 120; for (let r = 18; r < 70; r += 13) { g.beginPath(); g.arc(cx, cy, r, Math.PI * (0.2 + k * 0.1), Math.PI * (1.7 + k * 0.1)); g.stroke(); } } }), { r: 0.5, emitMap: null }),
  build: ({ b0, b1, bc, C }) => {
    // crescent (wau bulan lower section) cove in the ceiling: dropped white ceiling with a crescent void, blue rim light
    const cres = [], nn = 40; for (let i = 0; i <= nn; i++) { const t = i / nn; const a = b0 + 1.6 + (b1 - b0 - 3.2) * t; cres.push(at(C, 13.75 - Math.sin(t * Math.PI) * 1.6, a)); }
    for (let i = nn; i >= 0; i--) { const t = i / nn; const a = b0 + 1.6 + (b1 - b0 - 3.2) * t; cres.push(at(C, 13.95 - Math.sin(t * Math.PI) * 0.55, a)); }
    const outer = sector(C[0], C[1], R_VER + 0.05, R_DISP - 0.05, b0 + 0.8, b1 - 0.8, 24);
    prism(outer, 3.3, 3.42, GRG(), [cres.slice(0, -1)]);
    prism(cres, 3.7, 3.72, M('#dfe6ff', { r: 0.5 }), [], false);
    line(cres.concat([cres[0]]).map(p => [p[0], p[1], 3.31]), 0.016, '#5b7cff', 7);
    // counter: white solid surface, front with awan larat perforation glowing blue
    const pf = LINE ? M('#fff') : TM(ctex(512, 128, (g, w, h) => { g.fillStyle = '#f4f4f6'; g.fillRect(0, 0, w, h); g.fillStyle = '#4f6cf5'; for (let x = 8; x < w; x += 16) for (let y = 8; y < h; y += 16) { const r = 2 + 2.4 * Math.abs(Math.sin(x / 40 + y / 30)); g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); } }, [4, 1]), { r: 0.3, emitMap: ctex(512, 128, (g, w, h) => { g.fillStyle = '#000'; g.fillRect(0, 0, w, h); g.fillStyle = '#4f6cf5'; for (let x = 8; x < w; x += 16) for (let y = 8; y < h; y += 16) { const r = 2 + 2.4 * Math.abs(Math.sin(x / 40 + y / 30)); g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); } }, [4, 1]), emitHex: '#ffffff', emit: 1.6 });
    counterArc(C, 12.7, 13.35, b0 + 2.2, b1 - 2.2, M('#fbfbfb', { r: 0.2, cc: 0.6 }), pf);
    bowls(C, 13.05, b0 + 3, b1 - 3, 1.0, '#3d5fe0', 5);
    // floating shelves with blue under-light
    for (const z of [1.5, 2.0, 2.5]) { prism(sector(C[0], C[1], R_DISP - 0.32, R_DISP - 0.02, b0 + 1.5, b1 - 4.2, 12), z, z + 0.04, M('#fafafa', { r: 0.3 })); ledArc(C[0], C[1], R_DISP - 0.3, b0 + 1.6, b1 - 4.3, z - 0.01, '#6d8bff', 0.008, 4); }
    // three crescent pendants
    for (let k = 0; k < 3; k++) { const p = at(C, 13.0, b0 + 4 + k * 4.8); torus(p[0], p[1], 2.35, 0.28, 0.022, M('#ffffff', { emit: 2.2 }), Math.PI, 0, (bc + 90) * D2R); }
    pointL(...at(C, 13, bc), 3.0, '#9db0ff', 5, 6); pointL(...at(C, 12.2, bc), 2.4, '#fff1dc', 6, 7);
    person(...at(C, 12.1, bc - 2), 1, '#f2f0ec'); person(...at(C, 10.3, bc - 1), 0.98, '#efede8');
  } }) };
// ===================================================================== TERENGGANU (A2-2): perahu ribs (Pulau Duyong boat frames), sea teal
SCENES.trg = { build: () => stall(6, { st: ST.TRG, c: ST.TRG.c,
  back: () => LINE ? M('#fff') : TM(ctex(1024, 512, (g, w, h) => { g.fillStyle = '#0f4f57'; g.fillRect(0, 0, w, h); g.lineWidth = 5;
      for (let k = 0; k < 11; k++) { g.strokeStyle = `rgba(${120 + k * 8},${230},${215},${0.35 + k * 0.05})`; g.beginPath(); for (let x = 0; x <= w; x += 6) { const y = 60 + k * 40 + Math.sin(x / 70 + k * 0.6) * 18 + Math.sin(x / 23) * 4; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); } }), { r: 0.6, emitMap: ctex(1024, 512, (g, w, h) => { g.fillStyle = '#000'; g.fillRect(0, 0, w, h); g.lineWidth = 5; for (let k = 0; k < 11; k++) { g.strokeStyle = `rgba(80,240,220,${0.15 + k * 0.05})`; g.beginPath(); for (let x = 0; x <= w; x += 6) { const y = 60 + k * 40 + Math.sin(x / 70 + k * 0.6) * 18 + Math.sin(x / 23) * 4; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); } }), emitHex: '#ffffff', emit: 1.2 }),
  build: ({ b0, b1, bc, C }) => {
    prism(sector(C[0], C[1], R_VER + 0.05, R_DISP - 0.05, b0 + 0.8, b1 - 0.8, 24), 3.75, 3.85, GRG());
    // chengal ribs (like the frames fitted after the planks are shaped): arcs spanning wall to wall
    for (let k = 0; k < 8; k++) { const r = 11.4 + k * 0.45; const pts = [];
      for (let i = 0; i <= 16; i++) { const t = i / 16; const a = b0 + 0.9 + (b1 - b0 - 1.8) * t; const p = at(C, r, a); pts.push([p[0], p[1], 2.95 + Math.sin(t * Math.PI) * 0.8]); }
      tube(pts, 0.045, M('#8a4b2a', { r: 0.45, cc: 0.3 })); }
    // keel spine light
    const sp = []; for (let i = 0; i <= 10; i++) { const p = at(C, 11.3 + i * 0.33, bc); sp.push([p[0], p[1], 3.72]); } line(sp, 0.014, '#7ff5e4', 6);
    // hull-shaped counter (double ended): timber skin
    const hull = []; const n = 24; for (let i = 0; i <= n; i++) { const t = i / n; hull.push(at(C, 13.05 + Math.sin(t * Math.PI) * 0.36, b0 + 2.3 + (b1 - b0 - 4.6) * t)); }
    for (let i = n; i >= 0; i--) { const t = i / n; hull.push(at(C, 13.05 - Math.sin(t * Math.PI) * 0.3, b0 + 2.3 + (b1 - b0 - 4.6) * t)); }
    prism(hull, 0.15, 0.98, M('#8a4b2a', { r: 0.5, cc: 0.4 })); prism(hull, 0.98, 1.02, M('#f7f6f2', { r: 0.2 }));
    for (let k = 1; k < 7; k++) { const pts = hull.slice(0, n + 1).map(p => [p[0], p[1], 0.15 + k * 0.12]); tube(pts, 0.006, M('#5e3119', { r: 0.6 })); }
    bowls(C, 13.05, b0 + 3.4, b1 - 3.4, 1.02, '#d9a35b', 4);
    pointL(...at(C, 12.6, bc), 3.2, '#c8fff6', 6, 7); pointL(...at(C, 12.0, bc + 3), 2.0, '#fff0d8', 4, 6);
    plant(...at(C, 14.3, b0 + 1.6), 0, 1.0, '#3e7a4a', M('#d8d3cb', { r: 0.6 }));
    person(...at(C, 12.2, bc + 2), 1, '#f2f0ec');
  } }) };
// ===================================================================== JOHOR (A1-1): zapin step rhythm fins + pineapple facet ceiling
SCENES.jhr = { build: () => stall(13, { st: ST.JHR, c: ST.JHR.c,
  back: () => M('#f1ece2', { r: 0.6 }),
  build: ({ b0, b1, bc, C }) => {
    // faceted ceiling: diamond lattice (pineapple eyes), each cell a shallow pyramid with gold rim
    const nu = 9, nv = 7; const Lp = (u, v) => at(C, R_VER + 0.1 + (R_DISP - R_VER - 0.2) * v, b0 + 0.9 + (b1 - b0 - 1.8) * u);
    surf(nu * 2, nv * 2, (u, v) => Lp(u, v), (x, y, u, v) => 3.55 + 0.11 * Math.abs(Math.sin(u * nu * Math.PI) * Math.sin(v * nv * Math.PI)), M('#fbf6ea', { r: 0.5 }), !!LINE);
    for (let k = -nv; k <= nu; k++) { const pts = []; for (let i = 0; i <= 20; i++) { const u = i / 20, v = (u * nu - k) / nv; if (v < 0 || v > 1) continue; const p = Lp(u, v); pts.push([p[0], p[1], 3.54]); } if (pts.length > 2) line(pts, 0.006, '#ffcc4d', 3); }
    for (let k = 0; k <= nu + nv; k++) { const pts = []; for (let i = 0; i <= 20; i++) { const u = i / 20, v = (k - u * nu) / nv; if (v < 0 || v > 1) continue; const p = Lp(u, v); pts.push([p[0], p[1], 3.54]); } if (pts.length > 2) line(pts, 0.006, '#ffcc4d', 3); }
    // zapin rhythm fins on the back wall: 1-2-3 / pause (step counts of the dance)
    const steps = [1, 1, 2, 1, 1, 2, 1, 1, 3]; let a = b0 + 1.2;
    for (const s of steps) { if (a > b1 - 3.6) break; const h = 1.2 + s * 0.65; prism(sector(C[0], C[1], R_DISP - 0.28, R_DISP - 0.02, a, a + 0.25, 3), 0, h, M('#e8b523', { m: 0.6, r: 0.35 })); a += 0.55 + s * 0.35; }
    ledArc(C[0], C[1], R_DISP - 0.03, b0 + 1, b1 - 3.6, 0.05, '#ffd36b', 0.01, 4);
    // counter: green-glazed tile front (pineapple leaf) + timber top
    const tile = LINE ? M('#fff') : TM(ctex(256, 256, (g, w, h) => { g.fillStyle = '#2f6b3a'; g.fillRect(0, 0, w, h); g.strokeStyle = '#7fb35d'; g.lineWidth = 6; for (let i = -4; i < 8; i++) { g.beginPath(); g.moveTo(i * 40, h); g.lineTo(i * 40 + 128, 0); g.stroke(); g.beginPath(); g.moveTo(i * 40, 0); g.lineTo(i * 40 + 128, h); g.stroke(); } }, [6, 1]), { r: 0.15, cc: 0.8 });
    counterArc(C, 12.65, 13.3, b0 + 2.1, b1 - 2.1, M('#b07a45', { r: 0.4, cc: 0.4 }), tile);
    bowls(C, 13.0, b0 + 3, b1 - 3, 1.0, '#c8722e', 5);
    for (let k = 0; k < 3; k++) { const p = at(C, 12.95, b0 + 4 + k * 4.8); lathe(p[0], p[1], 2.1, [[0, 0], [0.16, 0.05], [0.2, 0.22], [0.15, 0.4], [0.03, 0.5], [0, 0.5]], M('#e8b523', { m: 0.7, r: 0.3 }), 6); sphere(p[0], p[1], 2.12, 0.1, M('#fff2c4', { emit: 3 })); cyl(p[0], p[1], 2.6, 3.55, 0.004, M('#222')); }
    pointL(...at(C, 12.6, bc), 3.0, '#ffe2a6', 6, 7);
    person(...at(C, 11.9, bc + 1.5), 1, '#f2f0ec'); person(...at(C, 10.4, bc - 3), 0.95, '#ecebe6');
  } }) };
// ===================================================================== MELAKA (A1-4): manik (beaded) dot wall, Stadthuys red, bead pendants
SCENES.mlk = { build: () => stall(16, { st: ST.MLK, c: ST.MLK.c,
  floor: () => LINE ? M('#fff') : TM(ctex(512, 512, (g, w, h) => { g.fillStyle = '#efe9df'; g.fillRect(0, 0, w, h); for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { const x = i * 128 + 64, y = j * 128 + 64; g.fillStyle = (i + j) % 2 ? '#e6dccb' : '#efe9df'; g.fillRect(i * 128, j * 128, 128, 128);
      g.fillStyle = '#b83a2e'; g.beginPath(); for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4; g.ellipse(x + Math.cos(a) * 26, y + Math.sin(a) * 26, 16, 7, a, 0, 7); } g.fill(); g.fillStyle = '#4fa59a'; g.beginPath(); g.arc(x, y, 12, 0, 7); g.fill(); } }, [1, 1]), { r: 0.3, cc: 0.5 }),
  back: () => LINE ? M('#fff') : TM(ctex(1024, 512, (g, w, h) => { g.fillStyle = '#f3ede4'; g.fillRect(0, 0, w, h); bead(g, w, h, false); }), { r: 0.5, emitMap: ctex(1024, 512, (g, w, h) => { g.fillStyle = '#000'; g.fillRect(0, 0, w, h); bead(g, w, h, true); }), emitHex: '#ffffff', emit: 1.5 }),
  build: ({ b0, b1, bc, C }) => {
    prism(sector(C[0], C[1], R_VER + 0.05, R_DISP - 0.05, b0 + 0.8, b1 - 0.8, 24), 3.6, 3.7, GRG());
    // Stadthuys red dado band all round
    wallStrip(arcPts(C[0], C[1], R_DISP - 0.02, b0 + 0.8, b1 - 0.8, 24), 0, 0.9, M('#b83a2e', { r: 0.5, cc: 0.3 }));
    counterArc(C, 12.65, 13.3, b0 + 2.1, b1 - 2.1, M('#f5f2ec', { r: 0.2, cc: 0.6 }), M('#b83a2e', { r: 0.45, cc: 0.5 }));
    ledArc(C[0], C[1], 12.62, b0 + 2.1, b1 - 2.1, 0.13, '#ffb7a8', 0.01, 3);
    bowls(C, 13.0, b0 + 3, b1 - 3, 1.0, '#5aa45e', 5);   // cendol green
    // bead pendant clusters (manik potong)
    for (let k = 0; k < 3; k++) { const p = at(C, 12.9, b0 + 4 + k * 4.8); for (let j = 0; j < 9; j++) { const q = at(p, 0.08 + (j % 3) * 0.09, j * 40); const z = 2.2 + (j % 4) * 0.22;
        cyl(q[0], q[1], z, 3.6, 0.003, M('#333')); sphere(q[0], q[1], z, 0.07, j % 3 ? M(['#f6a2b5', '#7fd1c4', '#ffe08a'][j % 3], { emit: 1.6 }) : M('#ffffff', { emit: 2.4 })); } }
    pointL(...at(C, 12.6, bc), 2.8, '#ffd9cf', 6, 7);
    plant(...at(C, 14.3, b0 + 1.6), 0, 0.9, '#4e8a3c', M('#b83a2e', { r: 0.5 }));
    person(...at(C, 12.0, bc - 1.5), 1, '#f2f0ec');
  } }) };
function bead(g, w, h, emit) {   // flower + butterfly made of dots on a grid, like kasut manik on its pidangan frame
  const cols = ['#e86a8a', '#f5c75a', '#5fc1b3', '#7a8be6', '#ffffff'];
  for (let x = 10; x < w; x += 20) for (let y = 10; y < h; y += 20) {
    const fx = (x % 340) - 170, fy = y - 256, r = Math.hypot(fx, fy), a = Math.atan2(fy, fx);
    const petal = r < 120 * Math.abs(Math.cos(a * 3)) + 30; const ctr = r < 34;
    g.fillStyle = ctr ? cols[1] : petal ? cols[0] : (((x / 20 + y / 20) | 0) % 7 === 0 ? cols[2] : (emit ? '#000' : '#e2d8c8'));
    if (emit && !petal && !ctr && ((x / 20 + y / 20) | 0) % 7) continue;
    g.beginPath(); g.arc(x, y, 5.2, 0, 7); g.fill(); }
}
// ===================================================================== GUEST POD (A1-2): neutral shell + swap kit (shown with the Pantai Timur kit)
SCENES.pod = { build: () => stall(14, { st: { b: 163.3, km: 0 }, c: '#ff9f43',
  back: () => M('#f4f2ee', { r: 0.6 }),
  build: ({ b0, b1, bc, C }) => {
    prism(sector(C[0], C[1], R_VER + 0.05, R_DISP - 0.05, b0 + 0.8, b1 - 0.8, 24), 3.6, 3.7, GRG());
    // magnetic rail on the back wall + swap-in lightbox
    for (const z of [1.1, 2.6]) prism(sector(C[0], C[1], R_DISP - 0.06, R_DISP - 0.01, b0 + 1, b1 - 3.6, 12), z, z + 0.05, ALU());
    if (!LINE) { const lb = ctex(1024, 512, (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, '#11A89A'); gr.addColorStop(0.5, '#8CC9E0'); gr.addColorStop(1, '#3456D6'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
        g.fillStyle = '#fff'; g.font = '700 92px Helvetica'; g.fillText('MUSIM', 60, 200); g.font = '60px Helvetica'; g.fillText('PANTAI TIMUR', 60, 300); g.font = '40px Helvetica'; g.fillText('guest kitchen · 4 weeks', 60, 380); });
      const pts = arcPts(C[0], C[1], R_DISP - 0.08, b0 + 1.3, b1 - 4, 16); const mm = wallStrip(pts, 1.25, 2.5, TM(lb, { r: 0.4, emitMap: lb, emitHex: '#ffffff', emit: 0.9 }), false);
      const uv = []; pts.forEach((p, i) => uv.push(i / (pts.length - 1), 0, i / (pts.length - 1), 1)); mm.geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); }
    // mobile counter on castors (plug-in kit)
    counterArc(C, 12.7, 13.3, b0 + 2.6, b1 - 2.6, M('#f7f7f5', { r: 0.2 }), M('#11A89A', { r: 0.35, cc: 0.6 }), 0.95);
    for (const a of [b0 + 3, b1 - 3]) for (const r of [12.8, 13.2]) { const p = at(C, r, a); sphere(p[0], p[1], 0.06, 0.06, M('#222')); }
    bowls(C, 13.0, b0 + 3.3, b1 - 3.3, 0.95, '#f2c35b', 4);
    // service bulkhead: power, water, exhaust drop (fixed)
    prism(sector(C[0], C[1], R_DISP - 0.5, R_DISP - 0.02, b1 - 3.4, b1 - 1.0, 6), 2.8, 3.6, M('#d9dbdc', { m: 0.6, r: 0.35 }));
    pointL(...at(C, 12.6, bc), 3.0, '#fff1df', 6, 7);
    person(...at(C, 12.1, bc + 1.5), 1, '#f2f0ec');
  } }) };
