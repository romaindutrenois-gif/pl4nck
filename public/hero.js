// Home hero: the model map assembles itself in 3D, then rises in four layers.
// Stars gather into the families on the bottom plane; the library settles into dust except the
// components with a path upward; the acceleration, quantum adaptation and hardware planes rise
// one by one with their components, and a pulse climbs one path. Not interactive.
const hero = document.getElementById('hero');
const canvas = document.getElementById('hero3d');
const labelsEl = document.getElementById('hlabels');
const cap = document.getElementById('herocap');
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
  visible = o > 0 && !document.hidden;
  if (visible) start();
}
let ticking = false;
window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { ticking = false; onScroll(); }); } }, { passive: true });
document.addEventListener('visibilitychange', onScroll);

let start = () => {};
onScroll();

// ---------- scene ----------
import { LAYERS, LIFT, EXTRA, LEDGES, layerOf, aboveOf, isDust, LY } from './layers.js';
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
  const COL = { conv: 0x94a3b8, curves: 0x6cc48a, vol: 0xf08a66, models: 0xa78bfa, methods: 0xe3b341, engines: 0x6cc3d2, instruments: 0xec7aa7, risk: 0xc09a72, quantum: 0x8ea2ff, infra: 0xa3a8b2 };
  // the map's wide layout, on every screen (phones look at it from the side)
  const POS = { W: 1000, H: 400, at: { conv: [95, 105], curves: [105, 290], vol: [290, 95], models: [300, 285], methods: [505, 92], engines: [530, 268], instruments: [770, 270], risk: [770, 92], quantum: [925, 185] } };
  const radius = (n) => 18 + 5 * Math.sqrt(n);
  const K = 0.15;
  const base = data.nodes.filter((n) => !n.quantum);
  const byCloud = {};
  base.forEach((n) => (byCloud[n.cloud] = byCloud[n.cloud] || []).push(n));
  const order = ['conv', 'curves', 'vol', 'models', 'methods', 'engines', 'instruments', 'risk'];
  const clouds = data.clouds.filter((c) => c.id !== 'quantum');
  const centre = {}, fin = {}, startP = {}, delay = {};
  let seed = 11; const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (const c of clouds) {
    const [x, y] = POS.at[c.id];
    centre[c.id] = new THREE.Vector3((x - POS.W / 2) * K, 0, (y - POS.H / 2) * K);
    const ids = byCloud[c.id].slice().sort((a, b) => (b.core ? 1 : 0) - (a.core ? 1 : 0));
    const R = radius(ids.length) * K * 0.92, step = R / Math.sqrt(ids.length + 0.5);
    ids.forEach((n, i) => {
      const r = step * Math.sqrt(i + 0.5), a = i * 2.39996;
      const h = Math.sin(i * 12.9898) * 43758.5453, j = h - Math.floor(h);
      fin[n.id] = centre[c.id].clone().add(new THREE.Vector3(r * Math.cos(a), 0.4 + j * 2.2 + (n.core ? 1.2 : 0), r * Math.sin(a)));
      const th = rnd() * Math.PI * 2, ph = Math.acos(2 * rnd() - 1), d = 45 + rnd() * 85;
      startP[n.id] = new THREE.Vector3(d * Math.sin(ph) * Math.cos(th), Math.abs(d * Math.cos(ph)) * 0.6 - 10, d * Math.sin(ph) * Math.sin(th));
      delay[n.id] = 0.25 + order.indexOf(c.id) * 0.16 + rnd() * 0.5;
    });
  }
  // upper layers: lifted components and new ones, each above the component it builds on
  const upper = data.nodes.filter((n) => LIFT[n.id]).concat(EXTRA);
  for (const n of upper) {
    const ab = fin[aboveOf(n)], h = Math.sin(n.id.length * 7.1) * 0.8;
    fin[n.id] = new THREE.Vector3(ab.x + (n.dx || 0), layerOf(n) * LY + 0.6 + h, ab.z + (n.dz || 0));
  }
  const all = Object.values(fin);
  const bx = [Math.min(...all.map((q) => q.x)) - 16, Math.max(...all.map((q) => q.x)) + 7], bz = [Math.min(...all.map((q) => q.z)) - 7, Math.max(...all.map((q) => q.z)) + 7];
  const PW = bx[1] - bx[0], PD = bz[1] - bz[0], PX = (bx[0] + bx[1]) / 2, PZ = (bz[0] + bz[1]) / 2;

  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const dl = new THREE.DirectionalLight(0xffffff, 0.9); dl.position.set(20, 60, 40); scene.add(dl);
  const starPts = [];
  for (let i = 0; i < 700; i++) {
    const th = rnd() * Math.PI * 2, ph = Math.acos(2 * rnd() - 1), d = 260 + rnd() * 260;
    starPts.push(new THREE.Vector3(d * Math.sin(ph) * Math.cos(th), d * Math.cos(ph), d * Math.sin(ph) * Math.sin(th)));
  }
  scene.add(new THREE.Points(new THREE.BufferGeometry().setFromPoints(starPts), new THREE.PointsMaterial({ color: 0x9fb0ca, size: 1.4, sizeAttenuation: false, transparent: true, opacity: 0.45 })));

  // the four planes
  const planes = LAYERS.map((_, i) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(PW, PD), new THREE.MeshBasicMaterial({ color: i >= 2 ? 0x4f6ef7 : 0x5b7bb5, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }));
    m.rotation.x = -Math.PI / 2; m.position.set(PX, -0.6, PZ); scene.add(m);
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry), new THREE.LineBasicMaterial({ color: 0x7f97d8, transparent: true, opacity: 0 }));
    e.rotation.copy(m.rotation); e.position.copy(m.position); scene.add(e);
    return { m, e };
  });
  const discs = {};
  for (const c of clouds) {
    const disc = new THREE.Mesh(new THREE.CircleGeometry(radius(byCloud[c.id].length) * K * 1.05, 48),
      new THREE.MeshBasicMaterial({ color: 0x5b7bb5, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }));
    disc.rotation.x = -Math.PI / 2; disc.position.copy(centre[c.id]); disc.position.y = -0.5; scene.add(disc); discs[c.id] = disc;
  }

  // nodes
  const meshes = {};
  const geo = new THREE.SphereGeometry(0.62, 20, 14), dgeo = new THREE.SphereGeometry(0.42, 12, 9), qgeo = new THREE.OctahedronGeometry(1.0, 0);
  for (const n of base.concat(upper)) {
    const c = new THREE.Color(COL[n.quantum ? 'quantum' : n.cloud]);
    const m = new THREE.Mesh(n.quantum ? qgeo : isDust(n) ? dgeo : geo, new THREE.MeshStandardMaterial({ color: c, emissive: c.clone().multiplyScalar(0.45), roughness: 0.35, metalness: 0.15, transparent: true, opacity: 0 }));
    m.position.copy(layerOf(n) ? fin[aboveOf(n)] : startP[n.id]); scene.add(m); meshes[n.id] = m;
  }
  const NB = Object.fromEntries(base.concat(upper).map((n) => [n.id, n]));

  // links on the bottom plane (fade to almost nothing once the library becomes dust)
  const pts = [];
  for (const [from, to, type] of data.edges) {
    if (type === 'quantum' || !fin[from] || !fin[to] || layerOf(NB[from]) || layerOf(NB[to])) continue;
    const a = fin[from], b = fin[to], mid = a.clone().lerp(b, 0.5); mid.y += Math.min(10, a.distanceTo(b) * 0.12);
    const cp = new THREE.QuadraticBezierCurve3(a, mid, b).getPoints(10);
    for (let i = 0; i < cp.length - 1; i++) pts.push(cp[i], cp[i + 1]);
  }
  const linkMat = new THREE.LineBasicMaterial({ color: 0x8fa0bd, transparent: true, opacity: 0, depthWrite: false });
  scene.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), linkMat));
  // vertical threads between layers, redrawn each frame while the layers rise
  const thrGeo = new THREE.BufferGeometry(), thrArr = new Float32Array(LEDGES.length * 6);
  thrGeo.setAttribute('position', new THREE.BufferAttribute(thrArr, 3));
  const thrMat = new THREE.LineBasicMaterial({ color: 0x8ea2ff, transparent: true, opacity: 0, depthWrite: false });
  scene.add(new THREE.LineSegments(thrGeo, thrMat));
  // one path, climbed by a pulse
  const PATH = ['heston', 'hg', 'qae_price', 'qpu'];
  const pulse = new THREE.Mesh(new THREE.SphereGeometry(0.75, 16, 12), new THREE.MeshBasicMaterial({ color: 0xdfe6ff, transparent: true, opacity: 0 }));
  scene.add(pulse);

  // labels: family names on the bottom plane, layer names at each plane's front corner
  const lab = {}, labPos = {};
  for (const c of clouds) {
    const s = document.createElement('span'); s.textContent = c.name; labelsEl.append(s); lab[c.id] = s;
    labPos[c.id] = centre[c.id].clone().add(new THREE.Vector3(0, 4.5, -radius(byCloud[c.id].length) * K - 2.5));
  }
  const plab = LAYERS.map((t) => { const s = document.createElement('span'); s.className = 'pln'; s.textContent = t; labelsEl.append(s); return s; });
  const plPos = LAYERS.map((_, i) => new THREE.Vector3(portrait ? bx[1] : bx[0], i * LY - 0.6, bz[1]));

  const target = portrait ? new THREE.Vector3(PX, 12, PZ) : new THREE.Vector3(PX - 12, 4, PZ + 6);
  const dist = portrait ? 285 : 180, elev = portrait ? 0.42 : 0.6, az0 = portrait ? Math.PI / 2 - 0.15 : -0.33;
  let pointer = { x: 0, y: 0 }, pSm = { x: 0, y: 0 };
  window.addEventListener('pointermove', (e) => { pointer = { x: e.clientX / innerWidth - 0.5, y: e.clientY / innerHeight - 0.5 }; }, { passive: true });

  const easeOut = (x) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
  const ramp = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
  const v = new THREE.Vector3();
  // timeline (seconds): gather 0.25-3.8 · dust 4-5 · layers rise from 5.2, one every 1.3 s · caption 9 · pulse from 10
  const RISE = (i) => 5.2 + (i - 1) * 1.3;
  let T = reduce ? 30 : 0;
  let capShown = false;
  const yOf = (n, t) => layerOf(n) * LY * easeOut(ramp(t, RISE(layerOf(n)), RISE(layerOf(n)) + 1.2));

  function frameAt(t, dt) {
    const dustK = ramp(t, 4, 5);
    for (const n of base) {
      const m = meshes[n.id], k = easeOut((t - delay[n.id]) / 2.4);
      m.position.lerpVectors(startP[n.id], fin[n.id], k);
      const full = 0.3 + 0.7 * Math.min(1, k * 1.4);
      m.material.opacity = isDust(n) ? full * (1 - 0.55 * dustK) : full;
      if (isDust(n)) m.scale.setScalar(1 - 0.25 * dustK);
    }
    for (const n of upper) {
      const m = meshes[n.id], l = layerOf(n), k = ramp(t, RISE(l), RISE(l) + 1.2);
      m.position.set(fin[n.id].x, fin[n.id].y - l * LY + yOf(n, t), fin[n.id].z);
      m.material.opacity = Math.min(1, k * 1.6);
      if (n.quantum) m.rotation.y += dt * 0.6;
    }
    linkMat.opacity = 0.2 * ramp(t, 3.4, 4.4) * (1 - 0.85 * dustK);
    for (const c of clouds) discs[c.id].material.opacity = 0.08 * ramp(t, 3.2, 5);
    planes.forEach((p, i) => {
      const k = i ? ramp(t, RISE(i), RISE(i) + 1.2) : ramp(t, 2.6, 4.2), y = i ? i * LY * easeOut(k) : 0;
      p.m.position.y = p.e.position.y = y - 0.6;
      p.m.material.opacity = (i >= 2 ? 0.09 : 0.06) * k; p.e.material.opacity = 0.45 * k;
    });
    LEDGES.forEach(([a, b], i) => {
      const A = meshes[a].position, B = meshes[b].position;
      thrArr.set([A.x, A.y, A.z, B.x, B.y, B.z], i * 6);
    });
    thrGeo.attributes.position.needsUpdate = true;
    thrMat.opacity = 0.6 * ramp(t, RISE(1), RISE(1) + 0.8);
    // the pulse climbs Heston > GPU > amplitude estimation > QPU access, every 5 s
    const pt = t - 10;
    if (pt > 0 && !reduce) {
      const ph = (pt % 5) / 3.2;
      if (ph < 1) {
        const seg = Math.min(PATH.length - 2, Math.floor(ph * (PATH.length - 1))), f = ph * (PATH.length - 1) - seg;
        pulse.position.lerpVectors(meshes[PATH[seg]].position, meshes[PATH[seg + 1]].position, f);
        pulse.material.opacity = Math.sin(Math.PI * ph) * 0.95;
      } else pulse.material.opacity = 0;
    }
    // camera: slow sway, dollying in while the map assembles
    const a0 = reduce ? az0 : az0 + (portrait ? 0.12 : 0.35) * Math.sin(t * 0.045 - 0.9);
    const d = dist * (1 + 0.45 * (1 - easeOut(t / 8)));
    pSm.x += (pointer.x - pSm.x) * 0.04; pSm.y += (pointer.y - pSm.y) * 0.04;
    const el = elev + pSm.y * 0.1;
    camera.position.set(target.x + d * Math.cos(el) * Math.sin(a0 + pSm.x * 0.2), target.y + d * Math.sin(el), target.z + d * Math.cos(el) * Math.cos(a0 + pSm.x * 0.2));
    camera.lookAt(target);
    renderer.render(scene, camera);
    const w = canvas.clientWidth, h = canvas.clientHeight, taken = [];
    plab.forEach((el2, i) => {
      v.copy(plPos[i]); v.y = planes[i].m.position.y; v.project(camera);
      const x = portrait ? 8 : (v.x + 1) / 2 * w, y = (1 - v.y) / 2 * h, on = (i ? ramp(t, RISE(i) + 0.6, RISE(i) + 1.4) : ramp(t, 4.4, 5.2)) > 0;
      el2.style.left = x + 'px'; el2.style.top = y + 'px'; el2.style.opacity = on && v.z < 1 ? '1' : '0';
      if (on) { const wd = el2._w || (el2._w = el2.offsetWidth || 140); taken.push(portrait ? { l: x, r: x + wd + 10, t: y - 22, b: y } : { l: x - wd - 14, r: x, t: y - 9, b: y + 9 }); }
    });
    const lv = ramp(t, 4.2, 5) > 0;
    const pri = ['models', 'methods', 'risk'];
    for (const c of [...clouds].sort((a, b) => pri.includes(b.id) - pri.includes(a.id))) {
      const el2 = lab[c.id];
      v.copy(labPos[c.id]).project(camera);
      const x = (v.x + 1) / 2 * w, y = (1 - v.y) / 2 * h, wd = el2._w || (el2._w = el2.offsetWidth || 120);
      const r = { l: x - wd / 2 - 6, r: x + wd / 2 + 6, t: y - 13, b: y + 13 };
      const free = v.z < 1 && y > 70 && !taken.some((o) => r.l < o.r && r.r > o.l && r.t < o.b && r.b > o.t);
      el2.style.left = x + 'px'; el2.style.top = y + 'px'; el2.style.opacity = lv && free ? '0.95' : '0';
      if (free) taken.push(r);
    }
    if (!capShown && t > 9) { capShown = true; cap.classList.add('on'); }
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
