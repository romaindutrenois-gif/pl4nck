// Home hero: the model map assembles itself in 3D.
// Stars gather into the nine families, links form between them, then the quantum algorithms
// rise above the models they build on. The camera then circles slowly. Not interactive:
// the page scrolls normally; the "Explore" button opens the real map.
const hero = document.getElementById('hero');
const canvas = document.getElementById('hero3d');
const labelsEl = document.getElementById('hlabels');
const cap = document.getElementById('herocap');
const cue = document.getElementById('cue');
const introTitle = document.querySelector('.intro h1');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- scroll: the picture fades before the intro text reaches it ----------
let visible = true;
function onScroll() {
  const p = Math.min(1, Math.max(0, window.scrollY / window.innerHeight));
  const t = introTitle.getBoundingClientRect().top, vh = window.innerHeight;
  const o = Math.min(1, Math.max(0, (t - vh) / (vh * 0.25)));
  hero.style.opacity = String(o);
  hero.style.transform = `scale(${1 + p * 0.06})`;
  cue.style.opacity = String(Math.max(0, 1 - p * 6));
  visible = o > 0 && !document.hidden;
  if (visible) start();
}
let ticking = false;
window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { ticking = false; onScroll(); }); } }, { passive: true });
document.addEventListener('visibilitychange', onScroll);

let start = () => {};
onScroll();

// ---------- scene ----------
let THREE;
try { THREE = await import('three'); } catch { THREE = null; }
const data = THREE ? await fetch('/map.json').then((r) => r.json()).catch(() => null) : null;
let renderer = null;
if (THREE && data) { try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true }); } catch { renderer = null; } }
if (!renderer) {
  cap.classList.add('on');            // no WebGL: the caption and button still invite to the map
} else {
  run();
}

function run() {
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 1200);
  const portrait = innerWidth / innerHeight < 0.9;
  // one colour per family (the map's default "By family" colouring, dark palette)
  const COL = { conv: 0x94a3b8, curves: 0x6cc48a, vol: 0xf08a66, models: 0xa78bfa, methods: 0xe3b341, engines: 0x6cc3d2, instruments: 0xec7aa7, risk: 0xc09a72, quantum: 0x8ea2ff };

  // same layout as the map page
  const POS = portrait
    ? { W: 400, H: 760, at: { conv: [80, 70], curves: [260, 75], vol: [90, 225], models: [290, 225], methods: [100, 365], engines: [255, 400], instruments: [110, 560], risk: [300, 575], quantum: [205, 700] } }
    : { W: 1000, H: 400, at: { conv: [95, 105], curves: [105, 290], vol: [290, 95], models: [300, 285], methods: [505, 92], engines: [530, 268], instruments: [770, 270], risk: [770, 92], quantum: [925, 185] } };
  const radius = (n) => (portrait ? 16 : 18) + (portrait ? 4.2 : 5) * Math.sqrt(n);
  const K = portrait ? 0.2 : 0.15, QY = 14;
  const byCloud = {};
  data.nodes.forEach((n) => (byCloud[n.cloud] = byCloud[n.cloud] || []).push(n));
  const order = ['conv', 'curves', 'vol', 'models', 'methods', 'engines', 'instruments', 'risk', 'quantum'];
  const centre = {}, fin = {}, startP = {}, delay = {};
  let seed = 11; const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (const c of data.clouds) {
    const [x, y] = POS.at[c.id];
    centre[c.id] = new THREE.Vector3((x - POS.W / 2) * K, 0, (y - POS.H / 2) * K);
    const ids = byCloud[c.id].slice().sort((a, b) => (b.core ? 1 : 0) - (a.core ? 1 : 0));
    const R = radius(ids.length) * K * 0.92, step = R / Math.sqrt(ids.length + 0.5);
    ids.forEach((n, i) => {
      const r = step * Math.sqrt(i + 0.5), a = i * 2.39996;
      const h = Math.sin(i * 12.9898) * 43758.5453, j = h - Math.floor(h);
      fin[n.id] = centre[c.id].clone().add(new THREE.Vector3(r * Math.cos(a), 0.4 + j * 2.2 + (n.core ? 1.2 : 0), r * Math.sin(a)));
      // start scattered on a wide shell around the scene
      const th = rnd() * Math.PI * 2, ph = Math.acos(2 * rnd() - 1), d = 45 + rnd() * 85;
      startP[n.id] = new THREE.Vector3(d * Math.sin(ph) * Math.cos(th), Math.abs(d * Math.cos(ph)) * 0.6 - 10, d * Math.sin(ph) * Math.sin(th));
      delay[n.id] = 0.25 + order.indexOf(c.id) * 0.16 + rnd() * 0.5;
    });
  }
  const status = (n) => n.quantum ? 'quantum' : n.cloud;

  // light, floor, stars
  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const dl = new THREE.DirectionalLight(0xffffff, 0.9); dl.position.set(20, 60, 40); scene.add(dl);
  const floor = new THREE.GridHelper(220, 32, 0x2a3d5e, 0x1a2a46); floor.position.y = -0.6; floor.material.transparent = true; floor.material.opacity = 0; scene.add(floor);
  const starPts = [];
  for (let i = 0; i < 700; i++) {
    const th = rnd() * Math.PI * 2, ph = Math.acos(2 * rnd() - 1), d = 260 + rnd() * 260;
    starPts.push(new THREE.Vector3(d * Math.sin(ph) * Math.cos(th), d * Math.cos(ph), d * Math.sin(ph) * Math.sin(th)));
  }
  scene.add(new THREE.Points(new THREE.BufferGeometry().setFromPoints(starPts), new THREE.PointsMaterial({ color: 0x9fb0ca, size: 1.4, sizeAttenuation: false, transparent: true, opacity: 0.45 })));

  // discs under the families
  const discs = {};
  for (const c of data.clouds) {
    const disc = new THREE.Mesh(new THREE.CircleGeometry(radius(byCloud[c.id].length) * K * 1.05, 48),
      new THREE.MeshBasicMaterial({ color: c.id === 'quantum' ? 0x4f6ef7 : 0x5b7bb5, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }));
    disc.rotation.x = -Math.PI / 2; disc.position.copy(centre[c.id]); disc.position.y = -0.5; scene.add(disc); discs[c.id] = disc;
  }

  // nodes
  const meshes = {};
  const geo = new THREE.SphereGeometry(0.62, 20, 14), small = new THREE.SphereGeometry(0.42, 14, 10), qgeo = new THREE.OctahedronGeometry(1.0, 0);
  for (const n of data.nodes) {
    const s = status(n), c = new THREE.Color(COL[s]);
    const m = new THREE.Mesh(n.quantum ? qgeo : n.core ? geo : small, new THREE.MeshStandardMaterial({
      color: c, emissive: s === 'todo' ? new THREE.Color(0x0b1628) : c.clone().multiplyScalar(0.45), roughness: 0.35, metalness: 0.15, transparent: true, opacity: 0 }));
    m.position.copy(startP[n.id]); scene.add(m); meshes[n.id] = m;
  }

  // links, one group per family so they can appear in turn
  const edges = data.edges.map(([from, to, type]) => ({ from, to, type: type || 'builds' }));
  const linkMats = {};
  const segs = {};
  for (const e of edges) {
    if (e.type === 'quantum') continue;
    const a = fin[e.from], b = fin[e.to], mid = a.clone().lerp(b, 0.5); mid.y += Math.min(10, a.distanceTo(b) * 0.12);
    const pts = new THREE.QuadraticBezierCurve3(a, mid, b).getPoints(10);
    const k = data.nodes.find((n) => n.id === e.from).cloud;
    const arr = segs[k] = segs[k] || [];
    for (let i = 0; i < pts.length - 1; i++) arr.push(pts[i], pts[i + 1]);
  }
  for (const [k, arr] of Object.entries(segs)) {
    linkMats[k] = new THREE.LineBasicMaterial({ color: 0x8fa0bd, transparent: true, opacity: 0, depthWrite: false });
    scene.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(arr), linkMats[k]));
  }
  // quantum links: built once the quantum cloud has risen
  const qFin = {};
  for (const n of byCloud.quantum) { qFin[n.id] = fin[n.id].clone(); qFin[n.id].y += QY; }
  const qMat = new THREE.LineDashedMaterial({ color: 0x8ea2ff, dashSize: 0.9, gapSize: 0.6, transparent: true, opacity: 0 });
  for (const e of edges) {
    if (e.type !== 'quantum') continue;
    const a = fin[e.from], b = qFin[e.to] || fin[e.to], mid = a.clone().lerp(b, 0.5); mid.y += 6;
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(new THREE.QuadraticBezierCurve3(a, mid, b).getPoints(30)), qMat);
    line.computeLineDistances(); scene.add(line);
  }

  // family names
  const lab = {};
  for (const c of data.clouds) {
    const s = document.createElement('span'); s.textContent = c.name; if (c.id === 'quantum') s.className = 'q';
    labelsEl.append(s); lab[c.id] = s;
  }
  const labPos = {};
  for (const c of data.clouds) labPos[c.id] = centre[c.id].clone().add(new THREE.Vector3(0, c.id === 'quantum' ? QY + 5 : 4.5, -radius(byCloud[c.id].length) * K - 2.5));

  // camera: wide orbit, dollies in while the map assembles
  const target = new THREE.Vector3(0, portrait ? 2 : 3, portrait ? 14 : 0);
  const dist = portrait ? 248 : 134, elev = portrait ? 0.98 : 0.72;
  let pointer = { x: 0, y: 0 }, pSm = { x: 0, y: 0 };
  window.addEventListener('pointermove', (e) => { pointer = { x: e.clientX / innerWidth - 0.5, y: e.clientY / innerHeight - 0.5 }; }, { passive: true });

  const easeOut = (x) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
  const ramp = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
  const v = new THREE.Vector3();
  let T = reduce ? 30 : 0;
  let capShown = false;

  function frameAt(t, dt) {
    // 1. stars gather into families (0.25 s to about 3.8 s)
    for (const n of data.nodes) {
      const k = easeOut((t - delay[n.id]) / 2.4);
      const m = meshes[n.id];
      const end = n.quantum ? fin[n.id].clone() : fin[n.id];
      m.position.lerpVectors(startP[n.id], end, k);
      m.material.opacity = (0.3 + 0.7 * Math.min(1, k * 1.4)) * (status(n) === 'todo' ? 0.55 : 1);
      // 3. quantum algorithms rise above (5 s to 6.8 s)
      if (n.quantum) { m.position.y += QY * easeOut(ramp(t, 5.0, 6.8)); m.rotation.y += dt * 0.6; }
    }
    // 2. links form, family by family (3.6 s to 6 s)
    order.forEach((k, i) => { if (linkMats[k]) linkMats[k].opacity = 0.2 * ramp(t, 3.6 + i * 0.22, 4.6 + i * 0.22); });
    for (const c of data.clouds) discs[c.id].material.opacity = (c.id === 'quantum' ? 0.16 : 0.08) * ramp(t, 3.2, 5);
    floor.material.opacity = 0.9 * ramp(t, 1.5, 4.5);
    discs.quantum.position.y = -0.5 + QY * easeOut(ramp(t, 5.0, 6.8));
    qMat.opacity = 0.9 * ramp(t, 6.6, 7.8);
    // camera
    // a slow sway rather than a full turn, so the map stays framed (a full turn would put a portrait layout sideways)
    const a0 = reduce ? (portrait ? 0 : -0.3) : portrait ? 0.22 * Math.sin(t * 0.07) : -0.3 + 0.5 * Math.sin(t * 0.045 - 0.9);
    const d = dist * (1 + 0.5 * (1 - easeOut(t / 7.5)));
    pSm.x += (pointer.x - pSm.x) * 0.04; pSm.y += (pointer.y - pSm.y) * 0.04;
    const el = elev + pSm.y * 0.12;
    camera.position.set(target.x + d * Math.cos(el) * Math.sin(a0 + pSm.x * 0.25), target.y + d * Math.sin(el), target.z + d * Math.cos(el) * Math.cos(a0 + pSm.x * 0.25));
    camera.lookAt(target);
    renderer.render(scene, camera);
    // names, then caption
    const lv = ramp(t, 6.4, 7.4) > 0;
    const w = canvas.clientWidth, h = canvas.clientHeight, taken = [];
    for (const c of data.clouds) {
      const el2 = lab[c.id];
      v.copy(labPos[c.id]); if (c.id === 'quantum') v.y = labPos[c.id].y * ramp(t, 5, 6.8) + 4.5 * (1 - ramp(t, 5, 6.8));
      v.project(camera);
      const x = (v.x + 1) / 2 * w, y = (1 - v.y) / 2 * h, wd = el2._w || (el2._w = el2.offsetWidth || 120);
      const r = { l: x - wd / 2 - 6, r: x + wd / 2 + 6, t: y - 13, b: y + 13 };
      const free = v.z < 1 && y > 70 && !taken.some((o) => r.l < o.r && r.r > o.l && r.t < o.b && r.b > o.t);
      el2.style.left = x + 'px'; el2.style.top = y + 'px'; el2.style.opacity = lv && free ? '0.95' : '0';
      if (free) taken.push(r);
    }
    if (!capShown && t > 7.2) { capShown = true; cap.classList.add('on'); }
  }

  function size() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    if (!running) frameAt(T, 0);
  }
  let running = false, last = 0;
  function loop(now) {
    if (!running) return;
    const dt = Math.min(0.1, (now - last) / 1000 || 0); last = now;
    T += dt;
    frameAt(T, dt);
    if (!visible) { running = false; return; }
    requestAnimationFrame(loop);
  }
  start = () => {
    if (reduce) return;
    if (!running) { running = true; last = performance.now(); requestAnimationFrame(loop); }
  };
  // phones resize the viewport when the address bar moves: only react to real size changes
  let lw = innerWidth, lh = innerHeight;
  window.addEventListener('resize', () => { if (innerWidth !== lw || Math.abs(innerHeight - lh) > 140) { lw = innerWidth; lh = innerHeight; size(); } });
  size();
  if (reduce) { frameAt(T, 0); cap.classList.add('on'); }
  else onScroll();
}
