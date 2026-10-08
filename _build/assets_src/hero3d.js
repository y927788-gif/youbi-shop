// 今天買這個 — 3D hero: a ring of real product cards over a neon grid. Mouse/touch = parallax + spin,
// sound (built-in synth loop or the visitor's microphone, opt-in) makes the grid, core and particles pulse.
// Microphone audio is analysed in the browser only; nothing is recorded or sent anywhere.
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js';

const box = document.getElementById('h3');
const cv = document.getElementById('h3c');
const tip = document.getElementById('h3tip');
const root = document.documentElement.dataset.root || '';
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const ev = (n, p) => { if (window.gtag) window.gtag('event', n, p || {}); };

function webglOK() { try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch (e) { return false; } }

if (box && cv && webglOK()) init();

function init() {
  box.classList.add('live');
  const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.75));
  renderer.setClearColor(0x09090d, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x09090d, 10, 24);
  const cam = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
  cam.position.set(0, 1.4, 11.5);

  // ---------- neon grid floor ----------
  const gridMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { t: { value: 0 }, lv: { value: 0 }, bass: { value: 0 } },
    vertexShader: `uniform float t;uniform float lv;uniform float bass;varying vec2 vUv;varying float vD;
      void main(){vUv=uv;vec3 p=position;float d=length(p.xy);
      p.z+=sin(p.x*.35+t*1.3)*cos(p.y*.28+t)*(.18+lv*1.6)+sin(d*.6-t*3.)*bass*1.1;
      vec4 mv=modelViewMatrix*vec4(p,1.);vD=-mv.z;gl_Position=projectionMatrix*mv;}`,
    fragmentShader: `uniform float t;uniform float lv;varying vec2 vUv;varying float vD;
      void main(){vec2 g=vUv*vec2(60.,60.);g.y+=t*1.6;vec2 f=abs(fract(g-.5)-.5)/fwidth(g);float l=1.-min(min(f.x,f.y),1.);
      vec3 c=mix(vec3(1.,.9,0.),vec3(1.,.18,.23),smoothstep(6.,22.,vD));c=mix(c,vec3(.24,.94,1.),lv*.6);
      float a=l*(1.-smoothstep(8.,26.,vD))*(.55+lv*.9);gl_FragColor=vec4(c*a,a);}`
  });
  const grid = new THREE.Mesh(new THREE.PlaneGeometry(70, 70, 90, 90), gridMat);
  grid.rotation.x = -Math.PI / 2; grid.position.y = -3.3;
  scene.add(grid);

  // ---------- particles ----------
  const PN = innerWidth < 700 ? 260 : 520;
  const pp = new Float32Array(PN * 3), ps = new Float32Array(PN);
  for (let i = 0; i < PN; i++) { pp[i * 3] = (Math.random() - .5) * 34; pp[i * 3 + 1] = Math.random() * 12 - 3; pp[i * 3 + 2] = (Math.random() - .5) * 26 - 3; ps[i] = .4 + Math.random(); }
  const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pp, 3));
  const pm = new THREE.PointsMaterial({ color: 0xffe600, size: .07, transparent: true, opacity: .75, blending: THREE.AdditiveBlending, depthWrite: false });
  const pts = new THREE.Points(pg, pm); scene.add(pts);

  // ---------- core ----------
  const core = new THREE.Group(); scene.add(core);
  const ico = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.IcosahedronGeometry(1.05, 1)), new THREE.LineBasicMaterial({ color: 0xffe600, transparent: true, opacity: .85 }));
  const ico2 = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.OctahedronGeometry(.55, 0)), new THREE.LineBasicMaterial({ color: 0xff2e3b }));
  core.add(ico, ico2);
  const gc = document.createElement('canvas'); gc.width = gc.height = 128;
  const gx = gc.getContext('2d'); const rg = gx.createRadialGradient(64, 64, 0, 64, 64, 64);
  rg.addColorStop(0, 'rgba(255,230,0,.9)'); rg.addColorStop(.35, 'rgba(255,46,59,.35)'); rg.addColorStop(1, 'rgba(255,46,59,0)');
  gx.fillStyle = rg; gx.fillRect(0, 0, 128, 128);
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(gc), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  glow.scale.set(4, 4, 1); core.add(glow);

  // ---------- ring of product cards ----------
  const ring = new THREE.Group(); scene.add(ring);
  const cards = [];
  const RARC = q => q >= 1e6 ? 0x3cf0ff : q >= 3e5 ? 0xffc83d : q >= 5e4 ? 0xc77dff : q >= 1e4 ? 0x4da3ff : 0x77778a;
  const RART = q => q >= 1e6 ? 'UR' : q >= 3e5 ? 'SSR' : q >= 5e4 ? 'SR' : q >= 1e4 ? 'R' : 'N';
  const loader = new THREE.TextureLoader(); loader.setCrossOrigin('anonymous');
  const ids = (box.dataset.ids || '').split(',').filter(Boolean);
  const small = innerWidth < 700;
  const N = Math.min(ids.length, small ? 14 : 22);
  const R = small ? 3.6 : 4.5;
  window.__load(d => {
    const by = {}; d.forEach(p => { by[p.i] = p; });
    const list = ids.map(i => by[i]).filter(p => p && p.m).slice(0, N);
    list.forEach((p, i) => {
      const a = i / list.length * Math.PI * 2;
      const g = new THREE.Group();
      const frame = new THREE.Mesh(new THREE.PlaneGeometry(1.72, 1.72), new THREE.MeshBasicMaterial({ color: RARC(p.q || 0), side: THREE.DoubleSide }));
      const mat = new THREE.MeshBasicMaterial({ color: 0x222230, side: THREE.DoubleSide });
      const face = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.6), mat); face.position.z = .01;
      const back = face.clone(); back.position.z = -.01; back.rotation.y = Math.PI;
      loader.load(window.__img(p), tx => { tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 4; mat.map = tx; mat.color.set(0xffffff); mat.needsUpdate = true; if (reduce) loop(); });
      g.add(frame, face, back);
      g.position.set(Math.cos(a) * R, Math.sin(a * 3) * .45, Math.sin(a) * R);
      g.lookAt(g.position.x * 2, g.position.y, g.position.z * 2);
      g.userData = { p, base: g.position.clone(), a, s: 1 };
      face.userData.card = g; back.userData.card = g; frame.userData.card = g;
      ring.add(g); cards.push(g);
    });
  });

  // ---------- sound ----------
  let actx = null, analyser = null, bins = null, music = null, mic = null;
  const lvl = { v: 0, b: 0 };
  function ensureCtx() {
    if (!actx) { actx = new (window.AudioContext || window.webkitAudioContext)(); analyser = actx.createAnalyser(); analyser.fftSize = 256; analyser.smoothingTimeConstant = .78; bins = new Uint8Array(analyser.frequencyBinCount); }
    if (actx.state === 'suspended') actx.resume();
  }
  // original synthwave loop, generated live (no recorded music)
  function startMusic() {
    ensureCtx();
    const out = actx.createGain(); out.gain.value = .16; out.connect(actx.destination); out.connect(analyser);
    const bpm = 112, step = 60 / bpm / 4; let next = actx.currentTime + .05, n = 0;
    const roots = [45, 41, 48, 43]; // A F C G
    const hz = m => 440 * Math.pow(2, (m - 69) / 12);
    function kick(t) { const o = actx.createOscillator(), g = actx.createGain(); o.frequency.setValueAtTime(140, t); o.frequency.exponentialRampToValueAtTime(40, t + .18); g.gain.setValueAtTime(1, t); g.gain.exponentialRampToValueAtTime(.001, t + .3); o.connect(g); g.connect(out); o.start(t); o.stop(t + .32); }
    let noiseBuf = null;
    function hat(t, v) { if (!noiseBuf) { noiseBuf = actx.createBuffer(1, actx.sampleRate * .1, actx.sampleRate); const ch = noiseBuf.getChannelData(0); for (let i = 0; i < ch.length; i++) ch[i] = Math.random() * 2 - 1; }
      const s = actx.createBufferSource(), f = actx.createBiquadFilter(), g = actx.createGain(); s.buffer = noiseBuf; f.type = 'highpass'; f.frequency.value = 7000; g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(.001, t + .05); s.connect(f); f.connect(g); g.connect(out); s.start(t); s.stop(t + .06); }
    function bass(t, m) { const o = actx.createOscillator(), f = actx.createBiquadFilter(), g = actx.createGain(); o.type = 'sawtooth'; o.frequency.value = hz(m); f.type = 'lowpass'; f.frequency.setValueAtTime(900, t); f.frequency.exponentialRampToValueAtTime(200, t + step * 1.8); g.gain.setValueAtTime(.32, t); g.gain.exponentialRampToValueAtTime(.001, t + step * 1.9); o.connect(f); f.connect(g); g.connect(out); o.start(t); o.stop(t + step * 2); }
    function lead(t, m) { const o = actx.createOscillator(), g = actx.createGain(); o.type = 'square'; o.frequency.value = hz(m); g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(.06, t + .02); g.gain.exponentialRampToValueAtTime(.001, t + step * 3); o.connect(g); g.connect(out); o.start(t); o.stop(t + step * 3.2); }
    const arp = [0, 7, 12, 15, 12, 7, 3, 7];
    const timer = setInterval(() => {
      while (next < actx.currentTime + .12) {
        const bar = Math.floor(n / 16) % 4, s = n % 16, r = roots[bar];
        if (s % 4 === 0) kick(next);
        if (s % 2 === 1) hat(next, s % 4 === 3 ? .18 : .08);
        if (s % 2 === 0) bass(next, r + (s % 8 === 6 ? 12 : 0));
        if (s % 2 === 0 && (n >> 5) % 2 === 1) lead(next, r + 36 + arp[(s / 2) % 8]);
        next += step; n++;
      }
    }, 25);
    return { stop() { clearInterval(timer); out.gain.setTargetAtTime(0, actx.currentTime, .05); setTimeout(() => out.disconnect(), 400); } };
  }
  const bMusic = document.getElementById('h3music'), bMic = document.getElementById('h3mic'), note = document.getElementById('h3note');
  function setBtn(b, on) { if (b) { b.setAttribute('aria-pressed', String(on)); } }
  if (bMusic) bMusic.addEventListener('click', () => {
    if (music) { music.stop(); music = null; setBtn(bMusic, false); return; }
    if (mic) { stopMic(); }
    music = startMusic(); setBtn(bMusic, true); ev('hero3d', { action: 'music' });
  });
  function stopMic() { if (mic) { mic.stream.getTracks().forEach(t => t.stop()); mic.src.disconnect(); mic = null; } setBtn(bMic, false); }
  if (bMic) bMic.addEventListener('click', async () => {
    if (mic) { stopMic(); return; }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { if (note) note.textContent = '這個瀏覽器不支援麥克風互動，可以改開音樂。'; return; }
    try {
      ensureCtx();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false } });
      if (music) { music.stop(); music = null; setBtn(bMusic, false); }
      const src = actx.createMediaStreamSource(stream); src.connect(analyser);
      mic = { stream, src }; setBtn(bMic, true); ev('hero3d', { action: 'mic' });
      if (note) note.textContent = '對著麥克風拍手、說話或放音樂試試。聲音只在你的瀏覽器裡分析，不會錄音或上傳。';
    } catch (e) { if (note) note.textContent = '沒有取得麥克風權限，可以改開音樂。'; }
  });

  // ---------- pointer ----------
  const mouse = new THREE.Vector2(0, 0), ndc = new THREE.Vector2(-9, -9);
  let spin = reduce ? 0 : .0026, vel = 0, drag = null, moved = 0, hover = null;
  const ray = new THREE.Raycaster();
  function local(e) { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top, r]; }
  cv.addEventListener('pointermove', e => {
    const [x, y, r] = local(e);
    mouse.set(x / r.width * 2 - 1, -(y / r.height) * 2 + 1);
    ndc.copy(mouse);
    if (drag) { const dx = e.clientX - drag.x; vel = dx * .00042; ring.rotation.y += dx * .006; drag.x = e.clientX; moved += Math.abs(dx); }
    if (tip && hover) { tip.style.transform = `translate(${Math.min(x + 16, r.width - 230)}px,${y + 16}px)`; }
  });
  cv.addEventListener('pointerleave', () => { ndc.set(-9, -9); if (!drag) setHover(null); });
  cv.addEventListener('pointerdown', e => { drag = { x: e.clientX }; moved = 0; try { cv.setPointerCapture(e.pointerId); } catch (_) { } });
  cv.addEventListener('pointerup', e => {
    const wasDrag = moved > 8; drag = null;
    if (!wasDrag) { const [x, y, r] = local(e); ray.setFromCamera(new THREE.Vector2(x / r.width * 2 - 1, -(y / r.height) * 2 + 1), cam); const hit = ray.intersectObjects(ring.children, true)[0]; if (hit) setHover(hit.object.userData.card); }
    if (!wasDrag && hover) { const p = hover.userData.p; ev('hero3d', { action: 'card', item_name: p.s.slice(0, 90) }); location.href = root + 'product.html#' + p.i; }
  });
  function setHover(g) {
    if (hover === g) return; hover = g; cv.style.cursor = g ? 'pointer' : 'grab';
    if (!tip) return;
    if (!g) { tip.hidden = true; return; }
    const p = g.userData.p; tip.hidden = false; tip.textContent = '';
    const r = document.createElement('span'); r.className = 'rar r-' + RART(p.q || 0).toLowerCase(); r.textContent = RART(p.q || 0);
    const n = document.createElement('b'); n.textContent = p.s;
    const m = document.createElement('span'); m.className = 'm'; m.textContent = window.__money(p.p) + '・銷量 ' + p.sold;
    tip.append(r, n, m);
  }

  // ---------- size / visibility ----------
  let W = 0, H = 0, run = true;
  function size() {
    W = cv.clientWidth; H = cv.clientHeight; renderer.setSize(W, H, false); cam.aspect = W / H;
    if (W >= 900) { cam.setViewOffset(W, H, -W * .19, 0, W, H); cam.position.z = 12.5; }  // ring sits right of the headline
    else { cam.clearViewOffset(); cam.position.z = 10.5; }                                   // phones: ring in its own block above the headline
    cam.updateProjectionMatrix();
  }
  size(); addEventListener('resize', size);
  new IntersectionObserver(es => { run = es[0].isIntersecting; if (run) loop(); }).observe(box);
  document.addEventListener('visibilitychange', () => { if (!document.hidden && run) loop(); });

  // ---------- frame ----------
  const clock = new THREE.Clock(); let raf = 0, t = 0;
  const tmp = new THREE.Vector3();
  function loop() { cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); }
  function frame() {
    if (!run || document.hidden) return;
    const dt = Math.min(clock.getDelta(), .05); t += dt;
    // sound level
    let v = 0, b = 0;
    if (analyser && (music || mic)) { analyser.getByteFrequencyData(bins); let s = 0, sb = 0; for (let i = 0; i < bins.length; i++) { s += bins[i]; if (i < 6) sb += bins[i]; } v = s / bins.length / 255; b = sb / 6 / 255; v = Math.min(1, v * (mic ? 2.6 : 1.8)); b = Math.min(1, b * (mic ? 1.4 : 1.05)); }
    else if (!reduce) { v = .08 + Math.sin(t * .8) * .04; }
    lvl.v += (v - lvl.v) * .25; lvl.b += (b - lvl.b) * .3;
    gridMat.uniforms.t.value = reduce ? 0 : t; gridMat.uniforms.lv.value = lvl.v; gridMat.uniforms.bass.value = lvl.b;
    // ring
    if (!drag) { vel *= .95; ring.rotation.y += spin + vel; }
    ring.rotation.x += ((.2 - mouse.y * .16) - ring.rotation.x) * .05;
    ring.rotation.z += ((mouse.x * .08) - ring.rotation.z) * .05;
    const pulse = 1 + lvl.b * .22;
    cards.forEach((g, i) => {
      const u = g.userData;
      tmp.copy(u.base).multiplyScalar(pulse); tmp.y = u.base.y + (reduce ? 0 : Math.sin(t * 1.4 + u.a * 3) * .18) + lvl.v * Math.sin(u.a * 5 + t * 6) * .5;
      g.position.lerp(tmp, .2);
      const target = g === hover ? 1.32 : 1 + lvl.b * .12;
      u.s += (target - u.s) * .18; g.scale.setScalar(u.s);
    });
    // core
    core.rotation.y += reduce ? 0 : .006 + lvl.v * .05; core.rotation.x += reduce ? 0 : .003;
    const cs = 1 + lvl.b * .9 + lvl.v * .3; ico.scale.setScalar(cs); ico2.scale.setScalar(1 + lvl.v * 1.4);
    glow.scale.setScalar(3.2 + lvl.b * 6 + lvl.v * 2); glow.material.opacity = .55 + lvl.v * .45;
    ico.material.color.setHSL((.15 - lvl.v * .45 + 1) % 1, 1, .5 + lvl.b * .2);
    // particles
    if (!reduce) { const a = pg.attributes.position.array; for (let i = 0; i < PN; i++) { a[i * 3 + 1] += dt * ps[i] * (.35 + lvl.v * 5); if (a[i * 3 + 1] > 9) a[i * 3 + 1] = -3; } pg.attributes.position.needsUpdate = true; }
    pm.size = .07 + lvl.b * .14; pm.color.setHSL(.15 - lvl.v * .32, 1, .55);
    // camera parallax
    cam.position.x += (mouse.x * 1.6 - cam.position.x) * .04; cam.position.z += ((W >= 900 ? 12.5 : 10.5) - cam.position.z) * .1;
    cam.position.y += (1.4 + mouse.y * .9 - cam.position.y) * .04;
    cam.lookAt(0, 0, 0);
    // hover pick
    if (ndc.x > -2 && !drag) { ray.setFromCamera(ndc, cam); const hit = ray.intersectObjects(ring.children, true)[0]; setHover(hit ? hit.object.userData.card : null); }
    renderer.render(scene, cam);
    if (!reduce || drag || vel) raf = requestAnimationFrame(frame);
  }
  if (reduce) { setTimeout(() => { renderer.render(scene, cam); }, 600); cv.addEventListener('pointermove', loop); }
  loop();
}
