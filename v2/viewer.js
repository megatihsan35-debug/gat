// Titik Temu v3 massing model for the review page. three.js r128 (global THREE) + OrbitControls.
// MODEL comes from v2/drawings.py model_data(): metres relative to the centre, x east, y north. Here: X = east, Y = up, Z = south.
(function () {
  var box = document.getElementById('view3d'); if (!box) return;
  var D = window.MODEL, R = D.R, LV = D.LV;
  var renderer;
  try { if (!window.THREE) throw 0; renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); } catch (e) { box.classList.add('nogl'); return; }
  var css = function (n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); };
  var dark = function () { var t = document.documentElement.getAttribute('data-theme'); return t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; };
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.92;
  box.appendChild(renderer.domElement);
  var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(34, 16 / 9, 0.5, 900);
  var rad = function (b) { return b * Math.PI / 180; };
  var pos = function (r, b, y) { return new THREE.Vector3(r * Math.sin(rad(b)), y, -r * Math.cos(rad(b))); };
  var M = function (o) { return new THREE.MeshStandardMaterial(o); };
  var mat = {
    white: M({ color: 0xf3f4f5, roughness: .7 }), roof: M({ color: 0xfafbfc, roughness: .55, side: THREE.DoubleSide }),
    glass: M({ color: 0x8fcfe4, roughness: .12, metalness: .15, transparent: true, opacity: .5 }),
    glassUp: M({ color: 0xa9dbe9, roughness: .12, metalness: .15, transparent: true, opacity: .42, emissive: 0xffd9a0, emissiveIntensity: 0 }),
    solid: M({ color: 0xe9ebee, roughness: .8 }), fin: M({ color: 0xc8ced6, roughness: .32, metalness: .75, emissive: 0x7fd8e8, emissiveIntensity: 0 }),
    col: M({ color: 0xb9c0c8, roughness: .3, metalness: .8 }), funnel: M({ color: 0xffe2a4, roughness: .5, transparent: true, opacity: .86, side: THREE.DoubleSide, emissive: 0xffb443, emissiveIntensity: .12 }),
    ground: M({ color: 0xc9d3c4, roughness: 1 }), site: M({ color: 0xeef0f1, roughness: 1 }), road: M({ color: 0x8e979f, roughness: 1 }), ctx: M({ color: 0xcfd5db, roughness: .9 }),
    court: M({ color: 0xffefc4, roughness: .9 }), water: M({ color: 0x4faee3, roughness: .1, metalness: .2 }), spine: M({ color: 0x7fb8c3, roughness: 1 }),
    mast: M({ color: 0xdfe4ea, roughness: .25, metalness: .85 }), lamp: M({ color: 0xffffff, emissive: 0xfff1c9, emissiveIntensity: 1.2 })
  };
  function add(geo, m, cast, recv) { var o = new THREE.Mesh(geo, m); o.castShadow = cast !== false; o.receiveShadow = recv !== false; scene.add(o); return o; }
  function shape(rings) {
    var s = new THREE.Shape(rings[0].map(function (p) { return new THREE.Vector2(p[0], p[1]); }));
    for (var i = 1; i < rings.length; i++) s.holes.push(new THREE.Path(rings[i].map(function (p) { return new THREE.Vector2(p[0], p[1]); })));
    return s;
  }
  function extrude(polys, y0, y1, m, cast) {
    polys.forEach(function (rings) {
      var g = new THREE.ExtrudeGeometry(shape(rings), { depth: y1 - y0, bevelEnabled: false, curveSegments: 1 });
      g.rotateX(-Math.PI / 2); g.translate(0, y0, 0); add(g, m, cast);
    });
  }
  function ring(r0, r1, y0, y1, m) {
    var s = new THREE.Shape(); s.absarc(0, 0, r1, 0, Math.PI * 2, false); var h = new THREE.Path(); h.absarc(0, 0, r0, 0, Math.PI * 2, true); s.holes.push(h);
    var g = new THREE.ExtrudeGeometry(s, { depth: y1 - y0, bevelEnabled: false, curveSegments: 64 }); g.rotateX(-Math.PI / 2); g.translate(0, y0, 0); return add(g, m);
  }
  // ground, roads, context
  var gp = add(new THREE.PlaneGeometry(700, 700), mat.ground, false); gp.rotation.x = -Math.PI / 2; gp.position.y = -0.02;
  extrude(D.site, 0, 0.05, mat.site, false); extrude(D.roads, 0, 0.03, mat.road, false); extrude(D.layby, 0.05, 0.08, mat.road, false);
  D.ctx.forEach(function (c) { extrude(c.p, 0, c.h, mat.ctx); });
  D.spines.forEach(function (s) {
    var L = Math.hypot(s.end[0], s.end[1]), g = new THREE.BoxGeometry(s.w, 0.06, L - R.court);
    var o = add(g, mat.spine, false); var mid = pos((L + R.court) / 2, s.b, 0.08); o.position.copy(mid); o.rotation.y = -rad(s.b);
  });
  // plinth as a low mound, court, pool
  add(new THREE.CylinderGeometry(R.gf + 1.5, R.gf + 7.5, LV.plinth, 96), mat.site).position.y = LV.plinth / 2 + 0.04;
  add(new THREE.CylinderGeometry(R.br1, R.br1, 0.06, 96), mat.court, false).position.y = LV.plinth + 0.07;
  add(new THREE.CylinderGeometry(R.pool, R.pool, 0.08, 48), mat.water, false).position.y = LV.plinth + 0.1;
  // floors
  var solidCats = { boh: 1, core: 1 };
  D.gf.forEach(function (z) { extrude(z.p, LV.plinth, 4.8, solidCats[z.c] || (z.c === 'pub') ? mat.solid : mat.glass); });
  extrude(D.l1plate, 4.8, LV.l1, mat.white); ring(R.br0, R.br1, 5.05, LV.l1, mat.white);
  D.l1.forEach(function (z) { if (z.c !== 'open') extrude(z.p, LV.l1, z.top, z.c === 'core' ? mat.solid : mat.glassUp); });
  extrude(D.l2plate, LV.l2 - 0.6, LV.l2, mat.white); ring(R.br0, R.br1, LV.l2 - 0.35, LV.l2, mat.white);
  D.l2.forEach(function (z) { if (z.c !== 'open') extrude(z.p, LV.l2, z.top, z.c === 'core' ? mat.solid : mat.glassUp); });
  // wave roof: one strip per block, 0.5 m thick tapering to a thin edge
  D.roof.forEach(function (S) {
    var v = [], idx = [], n = S.length;
    for (var i = 0; i < n; i++) {
      var b = S[i][0], h = S[i][1];
      [pos(R.roofin, b, h), pos(R.roof, b, h), pos(R.roofin, b, h - 0.5), pos(R.l1, b, h - 0.5), pos(R.roof, b, h - 0.12)].forEach(function (p) { v.push(p.x, p.y, p.z); });
    }
    for (var i = 0; i < n - 1; i++) {
      var a = i * 5, c = a + 5;
      idx.push(a, a + 1, c + 1, a, c + 1, c);                 // top
      idx.push(a + 2, c + 2, c + 3, a + 2, c + 3, a + 3);     // soffit
      idx.push(a + 3, c + 3, c + 4, a + 3, c + 4, a + 4);     // sloped edge soffit
      idx.push(a + 1, a + 4, c + 4, a + 1, c + 4, c + 1);     // outer edge
      idx.push(a, c, c + 2, a, c + 2, a + 2);                 // inner edge
    }
    [0, (n - 1) * 5].forEach(function (a) { idx.push(a, a + 2, a + 3, a, a + 3, a + 1, a + 1, a + 3, a + 4); });
    var g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setIndex(idx); g.computeVertexNormals(); add(g, mat.roof);
  });
  // funnel roof, mast, light
  var lathe = new THREE.LatheGeometry([new THREE.Vector2(R.oculus, LV.oculus), new THREE.Vector2(R.disc, LV.crown)], 72); add(lathe, mat.funnel);
  var mast = add(new THREE.CylinderGeometry(0.1, 0.42, LV.mast - LV.plinth, 16), mat.mast); mast.position.y = (LV.mast + LV.plinth) / 2;
  add(new THREE.SphereGeometry(0.42, 16, 12), mat.lamp, false, false).position.y = LV.mast + 0.2;
  // columns
  function cols(list, r, topDefault) { list.forEach(function (c) { var top = c[2] || topDefault, g = new THREE.CylinderGeometry(r, r, top - LV.plinth, 10); var o = add(g, mat.col); o.position.set(c[0], (top + LV.plinth) / 2, -c[1]); }); }
  cols(D.cols.out, 0.16); cols(D.cols.inn, 0.16); cols(D.cols.disc, 0.18, 12.4);
  // facade fins
  var fg = new THREE.BoxGeometry(D.fin[0], 1, D.fin[1]), fins = new THREE.InstancedMesh(fg, mat.fin, D.fins.length), dm = new THREE.Object3D();
  D.fins.forEach(function (f, i) { var h = f[2] - LV.l1; dm.position.copy(pos(R.l1 + 0.28, f[0], LV.l1 + h / 2)); dm.rotation.set(0, rad(f[1] - f[0]), 0); dm.scale.set(1, h, 1); dm.updateMatrix(); fins.setMatrixAt(i, dm.matrix); });
  fins.castShadow = true; fins.receiveShadow = true; scene.add(fins);
  // light
  var hemi = new THREE.HemisphereLight(0xffffff, 0x9aa4ae, .62), sun = new THREE.DirectionalLight(0xfff4e0, 1.05), glow = new THREE.PointLight(0xffc266, 0, 90, 1.6);
  sun.position.set(-70, 95, 60); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  var sc = sun.shadow.camera; sc.left = -80; sc.right = 80; sc.top = 80; sc.bottom = -80; sc.near = 10; sc.far = 300; sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.05;
  glow.position.set(0, 9, 0); scene.add(hemi, sun, glow);
  var night = dark();
  function mode() {
    scene.background = new THREE.Color(night ? 0x0b1118 : (css('--sky3d') || '#e9eef2'));
    hemi.intensity = night ? .22 : .62; sun.intensity = night ? .16 : 1.15; sun.color.set(night ? 0x9db7ff : 0xfff4e0); glow.intensity = night ? 2.4 : 0;
    mat.funnel.emissiveIntensity = night ? 1.25 : .12; mat.fin.emissiveIntensity = night ? .22 : 0; mat.glassUp.emissiveIntensity = night ? .55 : 0; mat.glass.emissive = new THREE.Color(0xffd9a0); mat.glass.emissiveIntensity = night ? .5 : 0;
    mat.ground.color.set(night ? 0x141c25 : 0xc9d3c4); mat.site.color.set(night ? 0x1d2732 : 0xeef0f1); mat.road.color.set(night ? 0x0f151c : 0x8e979f); mat.ctx.color.set(night ? 0x232e3a : 0xcfd5db);
    mat.spine.color.set(night ? 0x2f6f7b : 0x7fb8c3); mat.court.color.set(night ? 0x6b5a2c : 0xffefc4);
  }
  var ctl = new THREE.OrbitControls(cam, renderer.domElement); ctl.maxPolarAngle = Math.PI / 2 - 0.02; ctl.minDistance = 20; ctl.maxDistance = 260; ctl.addEventListener('change', draw);
  var VIEWS = { aerial: [[-62, 62, 92], [2, 5, 0]], gate: [[-3.2, 1.7, 56], [0, 9.5, 0]], road: [[-58, 9, 62], [0, 8, 0]], river: [[86, 16, 30], [0, 7, 0]], top: [[0, 150, 0.1], [0, 0, 0]] };
  function view(k) { var v = VIEWS[k]; cam.position.set(v[0][0], v[0][1], v[0][2]); ctl.target.set(v[1][0], v[1][1], v[1][2]); ctl.update(); draw(); }
  function draw() { renderer.render(scene, cam); }
  function size() { var w = box.clientWidth, h = Math.round(Math.max(260, Math.min(620, w * 0.58))); renderer.setSize(w, h); cam.aspect = w / h; cam.updateProjectionMatrix(); draw(); }
  document.querySelectorAll('[data-view]').forEach(function (b) { b.addEventListener('click', function () { view(b.getAttribute('data-view')); }); });
  var nb = document.getElementById('nightbtn');
  function label() { if (nb) { nb.textContent = night ? 'Day' : 'Night'; nb.setAttribute('aria-pressed', night ? 'true' : 'false'); } }
  if (nb) nb.addEventListener('click', function () { night = !night; mode(); label(); draw(); });
  mode(); label(); view('aerial'); size();
  if (window.ResizeObserver) new ResizeObserver(size).observe(box); else window.addEventListener('resize', size);
  box.classList.add('live');
  window.__tt = { view: view, night: function (v) { night = v; mode(); label(); draw(); } };
})();
