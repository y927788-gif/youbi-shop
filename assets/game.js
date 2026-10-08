// 買爆獸進化論 — playable arcade game. Steer your beast (mouse / touch joystick / WASD), eat real product orbs,
// dodge 爛貨炸彈 and 砍單鬼, evolve 5 times in a run; total XP levels you up for stronger starts next time.
// Progress is stored only in this browser (localStorage, falls back to memory).
(function () {
  var root = document.documentElement.dataset.root || '';
  var wrap = document.getElementById('arena'); if (!wrap) return;
  var cv = document.getElementById('gcv'), ctx = cv.getContext('2d');
  var ui = { start: document.getElementById('gstart'), over: document.getElementById('gover'), dash: document.getElementById('gdash'), mute: document.getElementById('gmute'), full: document.getElementById('gfull') };
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var touch = matchMedia('(pointer:coarse)').matches;
  function ev(n, p) { if (window.gtag) window.gtag('event', n, p || {}); }
  // ---------- storage ----------
  var mem = {};
  function load(k, d) { try { var v = JSON.parse(localStorage.getItem('yb_' + k)); if (v !== null && v !== undefined) return v; } catch (e) { } return mem[k] !== undefined ? mem[k] : d; }
  function save(k, v) { mem[k] = v; try { localStorage.setItem('yb_' + k, JSON.stringify(v)); } catch (e) { } }
  var meta = load('beast', { xp: 0, best: 0, maxStage: 0, runs: 0 });
  function lvOf(xp) { return Math.floor(Math.sqrt(xp / 90)) + 1; }
  function xpFor(lv) { return (lv - 1) * (lv - 1) * 90; }
  // ---------- constants ----------
  var STAGES = [
    { n: '爆蛋', en: 'EGG', need: 0, skill: '' },
    { n: '買買獸', en: 'CUB', need: 30, skill: '衝刺：空白鍵／點兩下／按衝刺鈕，衝刺中撞到敵人直接打爆' },
    { n: '爆買獸', en: 'BEAST', need: 100, skill: '磁吸：附近的商品會被吸過來' },
    { n: '霸買龍', en: 'DRAGON', need: 230, skill: '護盾：每 8 秒自動擋一次傷害' },
    { n: '買爆神', en: 'LEGEND', need: 460, skill: '震波：每 6 秒清掉身邊的敵人，經驗 ×1.5' }];
  var PERKS = [[2, '每升 1 級，經驗 +5%（最多 +50%）'], [3, '血量 3 → 4'], [5, '開局直接是「買買獸」（有衝刺）'], [8, '連擊時間 1.5 秒 → 2.2 秒'], [12, '開局直接是「爆買獸」（有磁吸）'], [16, '血量 4 → 5']];
  var TIERS = ['n', 'r', 'sr', 'ssr', 'ur'], TNAME = { n: 'N', r: 'R', sr: 'SR', ssr: 'SSR', ur: 'UR' };
  var TCOL = { n: '#8A8A9A', r: '#4DA3FF', sr: '#C77DFF', ssr: '#FFC83D', ur: '#3CF0FF' };
  var TXP = { n: 2, r: 4, sr: 8, ssr: 16, ur: 40 }, TRAD = { n: 15, r: 17, sr: 20, ssr: 23, ur: 27 };
  var TW = [['n', .4], ['r', .3], ['sr', .18], ['ssr', .09], ['ur', .03]];
  function tier(q) { return q >= 1e6 ? 'ur' : q >= 3e5 ? 'ssr' : q >= 5e4 ? 'sr' : q >= 1e4 ? 'r' : 'n'; }
  // ---------- sizing ----------
  var W = 0, H = 0, U = 1, DPR = 1;
  function size() {
    var r = wrap.getBoundingClientRect(); DPR = Math.min(devicePixelRatio || 1, 2);
    W = r.width; H = r.height; cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0); U = Math.max(.82, Math.min(W, H) / 600);
    if (!running) drawIdle();
  }
  addEventListener('resize', size);
  // ---------- sound ----------
  var ac = null, muted = load('mute', false);
  function snd(type, v) {
    if (muted) return;
    try {
      if (!ac) ac = new (window.AudioContext || window.webkitAudioContext)();
      if (ac.state === 'suspended') ac.resume();
      var t = ac.currentTime, o = ac.createOscillator(), g = ac.createGain(); o.connect(g); g.connect(ac.destination);
      if (type === 'eat') { o.type = 'triangle'; o.frequency.setValueAtTime(420 + v * 140, t); o.frequency.exponentialRampToValueAtTime(900 + v * 260, t + .08); g.gain.setValueAtTime(.12, t); g.gain.exponentialRampToValueAtTime(.001, t + .14); o.start(t); o.stop(t + .15); }
      else if (type === 'hit') { o.type = 'sawtooth'; o.frequency.setValueAtTime(180, t); o.frequency.exponentialRampToValueAtTime(50, t + .25); g.gain.setValueAtTime(.2, t); g.gain.exponentialRampToValueAtTime(.001, t + .3); o.start(t); o.stop(t + .32); }
      else if (type === 'dash') { o.type = 'sine'; o.frequency.setValueAtTime(300, t); o.frequency.exponentialRampToValueAtTime(1200, t + .12); g.gain.setValueAtTime(.08, t); g.gain.exponentialRampToValueAtTime(.001, t + .16); o.start(t); o.stop(t + .17); }
      else if (type === 'boom') { o.type = 'square'; o.frequency.setValueAtTime(120, t); o.frequency.exponentialRampToValueAtTime(40, t + .2); g.gain.setValueAtTime(.1, t); g.gain.exponentialRampToValueAtTime(.001, t + .22); o.start(t); o.stop(t + .23); }
      else if (type === 'evo') { [0, 4, 7, 12, 16].forEach(function (s, i) { var oo = ac.createOscillator(), gg = ac.createGain(); oo.type = 'square'; oo.frequency.value = 440 * Math.pow(2, s / 12); oo.connect(gg); gg.connect(ac.destination); gg.gain.setValueAtTime(.0001, t + i * .08); gg.gain.exponentialRampToValueAtTime(.07, t + i * .08 + .02); gg.gain.exponentialRampToValueAtTime(.001, t + i * .08 + .25); oo.start(t + i * .08); oo.stop(t + i * .08 + .3); }); o.disconnect(); }
    } catch (e) { }
  }
  function setMute() { if (ui.mute) { ui.mute.textContent = muted ? '🔇 音效關' : '🔊 音效開'; ui.mute.setAttribute('aria-pressed', String(!muted)); } }
  if (ui.mute) ui.mute.addEventListener('click', function () { muted = !muted; save('mute', muted); setMute(); });
  setMute();
  if (ui.full) ui.full.addEventListener('click', function () { var el = wrap; if (document.fullscreenElement) document.exitFullscreen(); else if (el.requestFullscreen) el.requestFullscreen().catch(function () { }); });
  document.addEventListener('fullscreenchange', function () { setTimeout(size, 60); });
  // ---------- items ----------
  var pool = { n: [], r: [], sr: [], ssr: [], ur: [] }, daily = null, imgs = {};
  function sprite(p) {
    if (imgs[p.i]) return imgs[p.i];
    var o = { img: null, ok: false }; imgs[p.i] = o;
    var im = new Image(); im.crossOrigin = 'anonymous'; im.referrerPolicy = 'no-referrer';
    im.onload = function () { o.img = im; o.ok = true; }; im.src = window.__img(p);
    return o;
  }
  // ---------- state ----------
  var running = false, paused = false, S = null, last = 0, raf = 0;
  var keys = {}, ptr = { on: false, x: 0, y: 0 }, joy = { on: false, id: null, sx: 0, sy: 0, x: 0, y: 0 };
  function lvl() { return lvOf(meta.xp); }
  function newRun() {
    var L = lvl();
    var st = L >= 12 ? 2 : L >= 5 ? 1 : 0;
    S = {
      t: 0, dur: 75, hp: L >= 16 ? 5 : L >= 3 ? 4 : 3, maxhp: L >= 16 ? 5 : L >= 3 ? 4 : 3, xp: STAGES[st].need, score: 0, stage: st, startStage: st,
      x: W / 2, y: H / 2, vx: 0, vy: 0, inv: 0, dashCd: 0, dashT: 0, shieldCd: 0, shield: st >= 3, waveCd: 6,
      combo: 0, comboT: 0, comboWin: L >= 8 ? 2.2 : 1.5, mult: 1 + Math.min(.5, (L - 1) * .05),
      items: [], foes: [], fx: [], texts: [], caught: {}, spawnI: 0, spawnF: 1.6, shake: 0, slow: 0, banner: null, dailyAt: [12, 34, 56], gotDaily: false, eaten: 0, kills: 0
    };
  }
  function rad() { return (19 + S.stage * 4.5) * U; }
  function pickTier() { var x = Math.random(), c = 0; for (var i = 0; i < TW.length; i++) { c += TW[i][1]; if (x < c) return TW[i][0]; } return 'n'; }
  function spawnItem(forceDaily) {
    var p, t;
    if (forceDaily && daily) { p = daily; t = tier(p.q || 0); }
    else { t = pickTier(); var arr = pool[t].length ? pool[t] : pool.n; p = arr[Math.floor(Math.random() * arr.length)]; if (!p) return; }
    var r = (forceDaily ? 30 : TRAD[t]) * U, m = r + 10;
    var x, y, k = 0; do { x = m + Math.random() * (W - 2 * m); y = m + 40 * U + Math.random() * (H - 2 * m - 40 * U); k++; } while (k < 12 && Math.hypot(x - S.x, y - S.y) < 140 * U);
    S.items.push({ p: p, t: t, x: x, y: y, r: r, a: Math.random() * 6.28, life: forceDaily ? 9 : 9 + Math.random() * 4, born: S.t, daily: !!forceDaily, spr: sprite(p) });
  }
  function spawnFoe() {
    var side = Math.floor(Math.random() * 4), x = side === 0 ? -30 : side === 1 ? W + 30 : Math.random() * W, y = side === 2 ? -30 : side === 3 ? H + 30 : Math.random() * H;
    var chase = S.t > 18 && Math.random() < Math.min(.45, .15 + S.t / 200);
    var sp = (chase ? 80 + S.t * .9 : 70 + Math.random() * 70 + S.t * 1.1) * U;
    var ang = Math.atan2(S.y - y + (Math.random() - .5) * 200, S.x - x + (Math.random() - .5) * 200);
    S.foes.push({ x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp, sp: sp, r: (chase ? 20 : 17) * U, chase: chase, a: 0, life: 14 });
  }
  function burst(x, y, col, n, spd) { if (reduce) n = Math.ceil(n / 3); for (var i = 0; i < n; i++) { var a = Math.random() * 6.28, s = (spd || 160) * (.4 + Math.random()) * U; S.fx.push({ x: x, y: y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: .5 + Math.random() * .4, max: .9, c: col, r: (2 + Math.random() * 3) * U }); } }
  function say(x, y, txt, col, big) { S.texts.push({ x: x, y: y, txt: txt, c: col, life: 1, big: big }); }
  // ---------- input ----------
  addEventListener('keydown', function (e) {
    if (!running) return;
    var k = e.key.toLowerCase(); keys[k] = true;
    if (k === ' ' || k === 'arrowup' || k === 'arrowdown' || k === 'arrowleft' || k === 'arrowright') e.preventDefault();
    if (k === ' ' || k === 'shift') dash();
    if (k === 'p' || k === 'escape') togglePause();
  });
  addEventListener('keyup', function (e) { keys[e.key.toLowerCase()] = false; });
  function local(e) { var r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
  var lastTap = 0;
  cv.addEventListener('pointerdown', function (e) {
    if (!running) return;
    var l = local(e);
    if (e.pointerType === 'mouse') { ptr.on = true; ptr.x = l[0]; ptr.y = l[1]; dash(); return; }
    joy.on = true; joy.id = e.pointerId; joy.sx = joy.x = l[0]; joy.sy = joy.y = l[1];
    var now = performance.now(); if (now - lastTap < 280) dash(); lastTap = now;
    try { cv.setPointerCapture(e.pointerId); } catch (_) { }
  });
  cv.addEventListener('pointermove', function (e) {
    var l = local(e);
    if (e.pointerType === 'mouse') { ptr.on = true; ptr.x = l[0]; ptr.y = l[1]; }
    else if (joy.on && e.pointerId === joy.id) { joy.x = l[0]; joy.y = l[1]; }
  });
  function endJoy(e) { if (e.pointerId === joy.id) joy.on = false; }
  cv.addEventListener('pointerup', endJoy); cv.addEventListener('pointercancel', endJoy);
  cv.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') ptr.on = false; });
  if (ui.dash) ui.dash.addEventListener('pointerdown', function (e) { e.preventDefault(); dash(); });
  function dash() {
    if (!S || S.stage < 1 || S.dashCd > 0 || paused) return;
    var dx = S.vx, dy = S.vy, m = Math.hypot(dx, dy);
    if (m < 5) { dx = 1; dy = 0; m = 1; }
    S.dashT = .22; S.dashCd = 2.4; S.dvx = dx / m * 900 * U; S.dvy = dy / m * 900 * U; S.inv = Math.max(S.inv, .3); snd('dash');
  }
  function togglePause() { if (!running) return; paused = !paused; if (!paused) { last = performance.now(); loop(); } else draw(); }
  document.addEventListener('visibilitychange', function () { if (document.hidden && running && !paused) togglePause(); });
  // ---------- update ----------
  function evolve(to) {
    S.stage = to; S.banner = { txt: '進化！' + STAGES[to].n, sub: STAGES[to].skill, life: 2.6 }; S.slow = .7;
    if (to >= 3) S.shield = true;
    burst(S.x, S.y, '#FFE600', 40, 300); burst(S.x, S.y, '#3CF0FF', 30, 220); snd('evo'); S.shake = .4;
    ev('game_evolve', { game: 'evolve', stage: STAGES[to].en });
  }
  function hurt() {
    if (S.inv > 0 || S.dashT > 0) return;
    if (S.shield) { S.shield = false; S.shieldCd = 8; S.inv = .8; burst(S.x, S.y, '#3CF0FF', 18, 200); say(S.x, S.y - 30 * U, '護盾！', '#3CF0FF'); snd('boom'); return; }
    S.hp--; S.inv = 1.3; S.shake = .35; S.combo = 0; burst(S.x, S.y, '#FF2E3B', 24, 260); snd('hit');
    if (S.hp <= 0) end();
  }
  function update(dt) {
    if (S.slow > 0) { S.slow -= dt; dt *= .35; }
    S.t += dt;
    // move
    var ax = 0, ay = 0, sp = (300 + S.stage * 12) * U;
    if (keys.a || keys.arrowleft) ax -= 1; if (keys.d || keys.arrowright) ax += 1; if (keys.w || keys.arrowup) ay -= 1; if (keys.s || keys.arrowdown) ay += 1;
    var tx = 0, ty = 0;
    if (ax || ay) { var m = Math.hypot(ax, ay); tx = ax / m * sp; ty = ay / m * sp; }
    else if (joy.on) { var jx = joy.x - joy.sx, jy = joy.y - joy.sy, jm = Math.hypot(jx, jy), cap = 60 * U; if (jm > 4) { var f = Math.min(1, jm / cap); tx = jx / jm * sp * f; ty = jy / jm * sp * f; } }
    else if (ptr.on) { var px = ptr.x - S.x, py = ptr.y - S.y, pm = Math.hypot(px, py); if (pm > 6) { var g = Math.min(1, pm / (90 * U)); tx = px / pm * sp * g; ty = py / pm * sp * g; } }
    var k = Math.min(1, dt * 9); S.vx += (tx - S.vx) * k; S.vy += (ty - S.vy) * k;
    var mvx = S.vx, mvy = S.vy;
    if (S.dashT > 0) { S.dashT -= dt; mvx = S.dvx; mvy = S.dvy; if (Math.random() < .8) S.fx.push({ x: S.x, y: S.y, vx: 0, vy: 0, life: .25, max: .25, c: 'ghost', r: rad(), st: S.stage }); }
    var R = rad();
    S.x = Math.max(R, Math.min(W - R, S.x + mvx * dt)); S.y = Math.max(R + 34 * U, Math.min(H - R, S.y + mvy * dt));
    S.inv = Math.max(0, S.inv - dt); S.dashCd = Math.max(0, S.dashCd - dt); S.shake = Math.max(0, S.shake - dt);
    if (S.stage >= 3 && !S.shield) { S.shieldCd -= dt; if (S.shieldCd <= 0) { S.shield = true; say(S.x, S.y - 30 * U, '護盾充能', '#3CF0FF'); } }
    if (S.stage >= 4) { S.waveCd -= dt; if (S.waveCd <= 0) { S.waveCd = 6; S.fx.push({ x: S.x, y: S.y, vx: 0, vy: 0, life: .5, max: .5, c: 'wave', r: 0 }); S.foes.forEach(function (f) { if (Math.hypot(f.x - S.x, f.y - S.y) < 240 * U) { f.dead = true; S.kills++; burst(f.x, f.y, '#FF2E3B', 10, 180); } }); snd('boom'); } }
    // combo
    if (S.comboT > 0) { S.comboT -= dt; if (S.comboT <= 0) S.combo = 0; }
    // spawn
    S.spawnI -= dt; if (S.spawnI <= 0 && S.items.length < 11) { spawnItem(false); S.spawnI = .55 + Math.random() * .5; }
    S.spawnF -= dt; if (S.spawnF <= 0) { spawnFoe(); S.spawnF = Math.max(.55, 2.3 - S.t * .028) * (.7 + Math.random() * .6); }
    if (S.dailyAt.length && S.t >= S.dailyAt[0]) { S.dailyAt.shift(); spawnItem(true); say(W / 2, 70 * U, '★ 今日爆品出現了！', '#FFE600', true); }
    // items
    var mag = S.stage >= 2 ? (120 + S.stage * 20) * U : 0;
    for (var i = S.items.length - 1; i >= 0; i--) {
      var it = S.items[i]; it.a += dt; it.life -= dt;
      var d = Math.hypot(it.x - S.x, it.y - S.y);
      if (mag && d < mag) { var pull = (1 - d / mag) * 520 * U * dt; it.x += (S.x - it.x) / d * pull; it.y += (S.y - it.y) / d * pull; }
      if (d < R + it.r * .8) {
        S.combo++; S.comboT = S.comboWin;
        var cm = 1 + Math.min(4, Math.floor(S.combo / 4)) * .5;
        var gain = Math.round((it.daily ? 60 : TXP[it.t]) * cm * S.mult * (S.stage >= 4 ? 1.5 : 1));
        S.xp += gain; S.score += gain; S.eaten++;
        if (!S.caught[it.p.i]) S.caught[it.p.i] = { p: it.p, t: it.t, n: 0, daily: it.daily }; S.caught[it.p.i].n++;
        if (it.daily) S.gotDaily = true;
        burst(it.x, it.y, TCOL[it.t], it.t === 'ur' || it.daily ? 30 : 12, 200);
        say(it.x, it.y - it.r, '+' + gain + (it.t === 'n' ? '' : ' ' + TNAME[it.t]), TCOL[it.t], it.t === 'ur' || it.daily);
        snd('eat', TIERS.indexOf(it.t));
        S.items.splice(i, 1);
        var nx = S.stage + 1; if (nx < STAGES.length && S.xp >= STAGES[nx].need) evolve(nx);
        continue;
      }
      if (it.life <= 0) S.items.splice(i, 1);
    }
    // foes
    for (var j = S.foes.length - 1; j >= 0; j--) {
      var f = S.foes[j]; f.a += dt * 3; f.life -= dt;
      if (f.chase) { var ang = Math.atan2(S.y - f.y, S.x - f.x); f.vx += (Math.cos(ang) * f.sp - f.vx) * Math.min(1, dt * 1.6); f.vy += (Math.sin(ang) * f.sp - f.vy) * Math.min(1, dt * 1.6); }
      f.x += f.vx * dt; f.y += f.vy * dt;
      var fd = Math.hypot(f.x - S.x, f.y - S.y);
      if (fd < R + f.r * .85) {
        if (S.dashT > 0) { f.dead = true; S.kills++; var kg = Math.round(5 * S.mult); S.xp += kg; S.score += kg; burst(f.x, f.y, '#FF2E3B', 16, 240); say(f.x, f.y, '擊破 +' + kg, '#FF5CA8'); snd('boom'); var nx2 = S.stage + 1; if (nx2 < STAGES.length && S.xp >= STAGES[nx2].need) evolve(nx2); }
        else { hurt(); f.dead = true; burst(f.x, f.y, '#FF2E3B', 10, 160); }
      }
      if (f.dead || f.life <= 0 || f.x < -80 || f.x > W + 80 || f.y < -80 || f.y > H + 80) S.foes.splice(j, 1);
    }
    // fx
    for (var q = S.fx.length - 1; q >= 0; q--) { var p = S.fx[q]; p.life -= dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= .96; p.vy *= .96; if (p.life <= 0) S.fx.splice(q, 1); }
    for (var z = S.texts.length - 1; z >= 0; z--) { var tt = S.texts[z]; tt.life -= dt * .9; tt.y -= 40 * U * dt; if (tt.life <= 0) S.texts.splice(z, 1); }
    if (S.banner) { S.banner.life -= dt; if (S.banner.life <= 0) S.banner = null; }
    if (S.t >= S.dur) end();
  }
  // ---------- drawing ----------
  function bg(t) {
    var g = ctx.createRadialGradient(W * .5, H * .45, 0, W * .5, H * .5, Math.max(W, H) * .75);
    g.addColorStop(0, '#1A1024'); g.addColorStop(1, '#09090D'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    var step = 46 * U, off = reduce ? 0 : (t * 18 * U) % step;
    ctx.strokeStyle = 'rgba(255,230,0,.07)'; ctx.lineWidth = 1; ctx.beginPath();
    for (var x = -step + off; x < W + step; x += step) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
    for (var y = -step + off; y < H + step; y += step) { ctx.moveTo(0, y); ctx.lineTo(W, y); }
    ctx.stroke();
    ctx.strokeStyle = 'rgba(255,46,59,.35)'; ctx.lineWidth = 2; ctx.strokeRect(4, 4, W - 8, H - 8);
  }
  function eye(x, y, r, dx, dy, angry) {
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.28); ctx.fill();
    ctx.fillStyle = '#09090D'; ctx.beginPath(); ctx.arc(x + dx * r * .45, y + dy * r * .45, r * .55, 0, 6.28); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x + dx * r * .45 - r * .18, y + dy * r * .45 - r * .2, r * .17, 0, 6.28); ctx.fill();
    if (angry) { ctx.strokeStyle = '#09090D'; ctx.lineWidth = r * .35; ctx.beginPath(); ctx.moveTo(x - r * 1.1, y - r * 1.3 + (x < 0 ? 0 : 0)); ctx.lineTo(x + r * .9, y - r * .9); ctx.stroke(); }
  }
  function beast(x, y, r, st, t, vx, vy, open, alpha) {
    ctx.save(); ctx.globalAlpha = alpha === undefined ? 1 : alpha; ctx.translate(x, y);
    var sp = Math.hypot(vx, vy), dx = sp > 5 ? vx / sp : 0, dy = sp > 5 ? vy / sp : .2;
    var sq = 1 + Math.min(.12, sp / (3000 * U)) * Math.sin(t * 18);
    ctx.scale(1 / sq, sq);
    if (st >= 4) { // rainbow aura
      ctx.save(); ctx.rotate(t * 1.5); var cg = ctx.createConicGradient ? ctx.createConicGradient(0, 0, 0) : null;
      if (cg) { ['#FF5CA8', '#FFE600', '#3CF0FF', '#C77DFF', '#FF5CA8'].forEach(function (c, i) { cg.addColorStop(i / 4, c); }); ctx.strokeStyle = cg; }
      else ctx.strokeStyle = '#3CF0FF';
      ctx.lineWidth = r * .18; ctx.globalAlpha *= .8; ctx.beginPath(); ctx.arc(0, 0, r * 1.45, 0, 6.28); ctx.stroke(); ctx.restore();
    }
    if (st >= 3) { // wings
      var fl = Math.sin(t * 12) * .35;
      [-1, 1].forEach(function (s) {
        ctx.save(); ctx.scale(s, 1); ctx.rotate(-fl);
        var wg = ctx.createLinearGradient(r * .4, 0, r * 1.9, -r); wg.addColorStop(0, st >= 4 ? '#3CF0FF' : '#C77DFF'); wg.addColorStop(1, 'rgba(255,46,59,.2)');
        ctx.fillStyle = wg; ctx.beginPath(); ctx.moveTo(r * .5, -r * .2); ctx.quadraticCurveTo(r * 1.7, -r * 1.6, r * 2, -r * .5); ctx.lineTo(r * 1.5, -r * .3); ctx.lineTo(r * 1.75, r * .1); ctx.lineTo(r * 1.25, 0); ctx.lineTo(r * 1.35, r * .45); ctx.closePath(); ctx.fill(); ctx.restore();
      });
    }
    if (st >= 2) { // spikes
      ctx.fillStyle = st >= 4 ? '#FFFFFF' : '#FF2E3B';
      for (var i = 0; i < 9; i++) { var a = Math.PI + (i / 8) * Math.PI; ctx.save(); ctx.rotate(a); ctx.beginPath(); ctx.moveTo(r * .82, -r * .2); ctx.lineTo(r * 1.32, 0); ctx.lineTo(r * .82, r * .2); ctx.fill(); ctx.restore(); }
    }
    // body
    var body = [['#FFE27A', '#FFB800'], ['#FFE600', '#FF9F1C'], ['#FF9F1C', '#FF2E3B'], ['#C77DFF', '#7B2CBF'], ['#E8FDFF', '#3CF0FF']][st];
    var bgd = ctx.createRadialGradient(-r * .3, -r * .4, r * .1, 0, 0, r * 1.1); bgd.addColorStop(0, body[0]); bgd.addColorStop(1, body[1]);
    ctx.fillStyle = bgd; ctx.beginPath();
    if (st === 0) ctx.ellipse(0, 0, r * .86, r * 1.05, Math.sin(t * 7) * .06 * Math.min(1, sp / 100), 0, 6.28); else ctx.arc(0, 0, r, 0, 6.28);
    ctx.fill();
    if (st === 0) { ctx.strokeStyle = 'rgba(80,40,0,.55)'; ctx.lineWidth = r * .07; ctx.beginPath(); ctx.moveTo(-r * .8, -r * .05); for (var c = 0; c < 6; c++) ctx.lineTo(-r * .8 + (c + 1) * r * .27, (c % 2 ? -1 : 1) * r * .14); ctx.stroke(); }
    else { ctx.fillStyle = 'rgba(255,255,255,.28)'; ctx.beginPath(); ctx.ellipse(0, r * .38, r * .6, r * .42, 0, 0, 6.28); ctx.fill(); }
    if (st >= 1) { // horns
      ctx.fillStyle = st >= 4 ? '#FFE600' : st >= 2 ? '#FFF6EC' : '#FF6B35'; var hh = r * (.45 + st * .12);
      [-1, 1].forEach(function (s) { ctx.beginPath(); ctx.moveTo(s * r * .25, -r * .78); ctx.lineTo(s * r * .62, -r * .7 - hh); ctx.lineTo(s * r * .62, -r * .62); ctx.fill(); });
    }
    if (st >= 3) { // crown
      ctx.fillStyle = '#FFC83D'; ctx.beginPath(); var cy = -r * 1.02, cw = r * .5;
      ctx.moveTo(-cw, cy); ctx.lineTo(-cw, cy - r * .3); ctx.lineTo(-cw * .5, cy - r * .12); ctx.lineTo(0, cy - r * .42); ctx.lineTo(cw * .5, cy - r * .12); ctx.lineTo(cw, cy - r * .3); ctx.lineTo(cw, cy); ctx.fill();
    }
    var er = r * (st === 0 ? .2 : .24);
    eye(-r * .34 + dx * r * .1, -r * .16 + dy * r * .08, er, dx, dy, st >= 2);
    eye(r * .34 + dx * r * .1, -r * .16 + dy * r * .08, er, dx, dy, false);
    if (st >= 2) { ctx.strokeStyle = '#09090D'; ctx.lineWidth = er * .35; ctx.beginPath(); ctx.moveTo(r * .1, -r * .5); ctx.lineTo(r * .58, -r * .44); ctx.stroke(); }
    // mouth
    ctx.fillStyle = '#3A0A12'; ctx.beginPath();
    if (open) ctx.ellipse(dx * r * .1, r * .3, r * .26, r * .22, 0, 0, 6.28); else ctx.ellipse(dx * r * .1, r * .3, r * .18, r * .06, 0, 0, 6.28);
    ctx.fill();
    if (st >= 1 && open) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(dx * r * .1 - r * .14, r * .14); ctx.lineTo(dx * r * .1 - r * .07, r * .26); ctx.lineTo(dx * r * .1, r * .14); ctx.fill(); }
    ctx.restore();
  }
  function itemDraw(it) {
    var b = Math.sin(it.a * 3) * 3 * U, x = it.x, y = it.y + b, r = it.r;
    var fade = it.life < 2 ? (Math.sin(it.life * 20) > 0 ? 1 : .35) : 1;
    ctx.save(); ctx.globalAlpha = fade;
    if (it.t === 'ur' || it.t === 'ssr' || it.daily) { var gl = ctx.createRadialGradient(x, y, r * .6, x, y, r * 1.9); gl.addColorStop(0, it.daily ? 'rgba(255,230,0,.55)' : TCOL[it.t] + '88'); gl.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(x, y, r * 1.9, 0, 6.28); ctx.fill(); }
    ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.28); ctx.closePath(); ctx.fillStyle = '#1B1B26'; ctx.fill(); ctx.clip();
    if (it.spr.ok) { try { ctx.drawImage(it.spr.img, x - r, y - r, r * 2, r * 2); } catch (e) { it.spr.ok = false; } }
    ctx.restore();
    ctx.lineWidth = (it.daily ? 4 : 3) * U; ctx.strokeStyle = it.daily ? '#FFE600' : TCOL[it.t]; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.28); ctx.stroke();
    if (it.t !== 'n' || it.daily) { ctx.font = '700 ' + Math.round(10 * U) + 'px "Chakra Petch",sans-serif'; var lab = it.daily ? '今日' : TNAME[it.t]; var tw = ctx.measureText(lab).width + 8 * U; ctx.fillStyle = it.daily ? '#FFE600' : TCOL[it.t]; ctx.fillRect(x - tw / 2, y + r - 6 * U, tw, 13 * U); ctx.fillStyle = '#09090D'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(lab, x, y + r + .5 * U); }
    ctx.restore();
  }
  function foeDraw(f) {
    ctx.save(); ctx.translate(f.x, f.y); ctx.rotate(f.a * (f.chase ? .4 : 1));
    var r = f.r;
    if (f.chase) { // 砍單鬼: ghost with X eyes
      ctx.fillStyle = '#FF2E3B'; ctx.beginPath(); ctx.arc(0, -r * .1, r, Math.PI, 0); ctx.lineTo(r, r * .8); for (var i = 0; i < 4; i++) ctx.lineTo(r - (i + .5) * r * .5, r * (i % 2 ? .8 : .45)); ctx.lineTo(-r, r * .8); ctx.fill();
      ctx.strokeStyle = '#09090D'; ctx.lineWidth = r * .14; [-1, 1].forEach(function (s) { ctx.beginPath(); ctx.moveTo(s * r * .45 - r * .15, -r * .35); ctx.lineTo(s * r * .45 + r * .15, -r * .05); ctx.moveTo(s * r * .45 + r * .15, -r * .35); ctx.lineTo(s * r * .45 - r * .15, -r * .05); ctx.stroke(); });
    } else { // 爛貨炸彈: spiky box
      ctx.fillStyle = '#5B1A22'; for (var k = 0; k < 8; k++) { ctx.save(); ctx.rotate(k * .785); ctx.beginPath(); ctx.moveTo(r * .55, -r * .2); ctx.lineTo(r * 1.15, 0); ctx.lineTo(r * .55, r * .2); ctx.fill(); ctx.restore(); }
      ctx.fillStyle = '#8B3A2E'; ctx.fillRect(-r * .7, -r * .7, r * 1.4, r * 1.4);
      ctx.fillStyle = '#C9A06A'; ctx.fillRect(-r * .7, -r * .12, r * 1.4, r * .24);
      ctx.fillStyle = '#FF2E3B'; ctx.font = '900 ' + Math.round(r * .9) + 'px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('爛', 0, -r * .32);
    }
    ctx.restore();
  }
  function hud() {
    var pad = 12 * U, fs = Math.round(15 * U);
    ctx.fillStyle = 'rgba(9,9,13,.6)'; ctx.fillRect(0, 0, W, 34 * U);
    ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
    for (var i = 0; i < S.maxhp; i++) { ctx.fillStyle = i < S.hp ? '#FF2E3B' : '#3A3A48'; heart(pad + i * 22 * U + 8 * U, 17 * U, 8 * U); }
    ctx.font = '700 ' + fs + 'px "Chakra Petch",sans-serif'; ctx.fillStyle = '#FFE600';
    ctx.fillText('SCORE ' + S.score, pad + S.maxhp * 22 * U + 10 * U, 17 * U);
    // timer bar
    var tw = Math.min(260 * U, W * .28), tx = W / 2 - tw / 2, rem = Math.max(0, S.dur - S.t);
    ctx.fillStyle = '#2A2A38'; ctx.fillRect(tx, 12 * U, tw, 10 * U); ctx.fillStyle = rem < 10 ? '#FF2E3B' : '#3CF0FF'; ctx.fillRect(tx, 12 * U, tw * rem / S.dur, 10 * U);
    ctx.textAlign = 'center'; ctx.fillStyle = '#F3F1EA'; ctx.font = '700 ' + Math.round(11 * U) + 'px "Chakra Petch",sans-serif'; ctx.fillText(Math.ceil(rem) + 's', W / 2, 29 * U);
    // stage + evo bar
    ctx.textAlign = 'right'; ctx.font = '900 ' + fs + 'px "Noto Serif TC",serif'; ctx.fillStyle = '#F3F1EA';
    var st = STAGES[S.stage], nx = STAGES[S.stage + 1];
    ctx.fillText(st.n, W - pad, 13 * U);
    var bw = Math.min(150 * U, W * .2), bx = W - pad - bw;
    ctx.fillStyle = '#2A2A38'; ctx.fillRect(bx, 24 * U, bw, 6 * U);
    ctx.fillStyle = '#C77DFF'; ctx.fillRect(bx, 24 * U, nx ? bw * Math.min(1, (S.xp - st.need) / (nx.need - st.need)) : bw, 6 * U);
    // combo
    if (S.combo >= 3) { ctx.textAlign = 'center'; ctx.font = '900 ' + Math.round(14 * U) + 'px "Anton",sans-serif'; ctx.fillStyle = '#FF5CA8'; ctx.fillText(S.combo + ' COMBO ×' + (1 + Math.min(4, Math.floor(S.combo / 4)) * .5), S.x, S.y - rad() - 18 * U); }
    // dash cd (desktop text)
    if (ui.dash) { ui.dash.hidden = !(touch && S.stage >= 1); ui.dash.style.setProperty('--cd', (S.dashCd / 2.4 * 100).toFixed(0) + '%'); }
    if (!touch && S.stage >= 1) { ctx.textAlign = 'left'; ctx.font = '600 ' + Math.round(11 * U) + 'px "Chakra Petch",sans-serif'; ctx.fillStyle = S.dashCd > 0 ? '#6B6B7A' : '#3CF0FF'; ctx.fillText(S.dashCd > 0 ? 'DASH ' + S.dashCd.toFixed(1) : 'DASH READY [SPACE / CLICK]', pad, H - 14 * U); }
  }
  function heart(x, y, s) { ctx.beginPath(); ctx.moveTo(x, y + s * .9); ctx.bezierCurveTo(x - s * 1.4, y - s * .1, x - s * .6, y - s * 1.1, x, y - s * .35); ctx.bezierCurveTo(x + s * .6, y - s * 1.1, x + s * 1.4, y - s * .1, x, y + s * .9); ctx.fill(); }
  function draw() {
    ctx.save();
    if (S.shake > 0 && !reduce) ctx.translate((Math.random() - .5) * 14 * U * S.shake, (Math.random() - .5) * 14 * U * S.shake);
    bg(S.t);
    S.fx.forEach(function (p) { if (p.c === 'ghost') beast(p.x, p.y, p.r, p.st, S.t, 0, 0, false, p.life / p.max * .35); });
    S.items.forEach(itemDraw);
    S.foes.forEach(foeDraw);
    var R = rad();
    if (S.stage >= 2) { ctx.strokeStyle = 'rgba(199,125,255,.12)'; ctx.lineWidth = 1; ctx.setLineDash([4, 6]); ctx.beginPath(); ctx.arc(S.x, S.y, (120 + S.stage * 20) * U, 0, 6.28); ctx.stroke(); ctx.setLineDash([]); }
    var near = S.items.some(function (it) { return Math.hypot(it.x - S.x, it.y - S.y) < R + 60 * U; });
    if (!(S.inv > 0 && S.dashT <= 0 && Math.floor(S.t * 14) % 2)) beast(S.x, S.y, R, S.stage, S.t, S.vx, S.vy, near);
    if (S.shield) { ctx.strokeStyle = 'rgba(60,240,255,.7)'; ctx.lineWidth = 3 * U; ctx.beginPath(); ctx.arc(S.x, S.y, R * 1.35, 0, 6.28); ctx.stroke(); }
    S.fx.forEach(function (p) {
      if (p.c === 'ghost') return;
      if (p.c === 'wave') { var k = 1 - p.life / p.max; ctx.strokeStyle = 'rgba(255,230,0,' + (1 - k) + ')'; ctx.lineWidth = 6 * U; ctx.beginPath(); ctx.arc(p.x, p.y, k * 240 * U, 0, 6.28); ctx.stroke(); return; }
      ctx.globalAlpha = Math.max(0, p.life / p.max); ctx.fillStyle = p.c; ctx.fillRect(p.x - p.r / 2, p.y - p.r / 2, p.r, p.r); ctx.globalAlpha = 1;
    });
    S.texts.forEach(function (t) { ctx.globalAlpha = Math.min(1, t.life * 2); ctx.textAlign = 'center'; ctx.font = '900 ' + Math.round((t.big ? 22 : 14) * U) + 'px "Anton","Noto Serif TC",sans-serif'; ctx.lineWidth = 3 * U; ctx.strokeStyle = '#09090D'; ctx.strokeText(t.txt, t.x, t.y); ctx.fillStyle = t.c; ctx.fillText(t.txt, t.x, t.y); ctx.globalAlpha = 1; });
    if (S.banner) {
      var b = S.banner, a = Math.min(1, b.life * 1.5, (2.6 - b.life) * 4);
      ctx.globalAlpha = a; ctx.fillStyle = 'rgba(9,9,13,.7)'; ctx.fillRect(0, H * .38, W, 92 * U);
      ctx.textAlign = 'center'; ctx.font = '900 ' + Math.round(38 * U) + 'px "Noto Serif TC",serif'; ctx.fillStyle = '#FFE600'; ctx.lineWidth = 4 * U; ctx.strokeStyle = '#FF2E3B'; ctx.strokeText(b.txt, W / 2, H * .38 + 38 * U); ctx.fillText(b.txt, W / 2, H * .38 + 38 * U);
      ctx.font = '600 ' + Math.round(13 * U) + 'px sans-serif'; ctx.fillStyle = '#F3F1EA'; ctx.fillText(b.sub, W / 2, H * .38 + 72 * U); ctx.globalAlpha = 1;
    }
    ctx.restore();
    hud();
    if (joy.on) { ctx.strokeStyle = 'rgba(255,255,255,.25)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(joy.sx, joy.sy, 60 * U, 0, 6.28); ctx.stroke(); ctx.fillStyle = 'rgba(255,230,0,.5)'; var jx = joy.x - joy.sx, jy = joy.y - joy.sy, jm = Math.hypot(jx, jy), c = Math.min(1, 60 * U / (jm || 1)); ctx.beginPath(); ctx.arc(joy.sx + jx * c, joy.sy + jy * c, 20 * U, 0, 6.28); ctx.fill(); }
    if (paused) { ctx.fillStyle = 'rgba(9,9,13,.7)'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#FFE600'; ctx.textAlign = 'center'; ctx.font = '900 ' + Math.round(36 * U) + 'px "Noto Serif TC",serif'; ctx.fillText('暫停', W / 2, H / 2); ctx.font = '600 ' + Math.round(13 * U) + 'px sans-serif'; ctx.fillStyle = '#F3F1EA'; ctx.fillText('按 P／Esc 或點畫面繼續', W / 2, H / 2 + 30 * U); }
  }
  var idleT = 0;
  function drawIdle() {
    if (!W) return;
    S = S || null;
    ctx.save(); bg(idleT); ctx.restore();
    var st = Math.min(4, meta.maxStage), r = Math.min(W, H) * .11;

  }
  function idleLoop() { if (running) return; idleT += 1 / 60; drawIdle(); if (!reduce && !document.hidden) requestAnimationFrame(idleLoop); }
  cv.addEventListener('click', function () { if (paused) togglePause(); });
  // ---------- loop ----------
  function loop() { cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); }
  function frame(now) {
    if (!running || paused) return;
    var dt = Math.min(.05, (now - last) / 1000 || 0); last = now;
    update(dt); if (running) { draw(); raf = requestAnimationFrame(frame); }
  }
  // ---------- screens ----------
  function el(t, c, txt) { var e = document.createElement(t); if (c) e.className = c; if (txt !== undefined) e.textContent = txt; return e; }
  function startScreen() {
    var L = lvl(), into = meta.xp - xpFor(L), need = xpFor(L + 1) - xpFor(L);
    document.getElementById('glv').textContent = 'Lv.' + L;
    document.getElementById('glvbar').style.width = Math.min(100, into / need * 100) + '%';
    document.getElementById('glvtxt').textContent = '下一級還差 ' + (need - into) + ' 經驗・最高分 ' + meta.best + '・已玩 ' + meta.runs + ' 局';
    var dex = document.getElementById('gevo'); dex.textContent = '';
    STAGES.forEach(function (s, i) {
      var li = el('li', i <= meta.maxStage ? 'on' : ''); var c = el('canvas'); c.width = c.height = 88; li.appendChild(c);
      var cx = c.getContext('2d'), keep = ctx; ctx = cx; ctx.setTransform(1, 0, 0, 1, 0, 0);
      if (i <= meta.maxStage) beast(44, 46, 26, i, 0, 0, 30, false); else { cx.fillStyle = '#2A2A38'; cx.beginPath(); cx.arc(44, 46, 26, 0, 6.28); cx.fill(); cx.fillStyle = '#6B6B7A'; cx.font = '900 26px sans-serif'; cx.textAlign = 'center'; cx.textBaseline = 'middle'; cx.fillText('?', 44, 47); }
      ctx = keep; ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      li.appendChild(el('b', '', i <= meta.maxStage ? s.n : '？？？')); li.appendChild(el('small', '', 'STAGE ' + (i + 1)));
      dex.appendChild(li);
    });
    var pk = document.getElementById('gperks'); pk.textContent = '';
    PERKS.forEach(function (p) { var li = el('li', L >= p[0] ? 'on' : ''); li.appendChild(el('b', '', 'Lv.' + p[0])); li.appendChild(document.createTextNode(p[1])); pk.appendChild(li); });
    ui.start.hidden = false; ui.over.hidden = true; idleLoop();
  }
  function begin() {
    if (!pool.n.length && !pool.r.length) return;
    size(); newRun(); running = true; paused = false; ui.start.hidden = true; ui.over.hidden = true;
    keys = {}; last = performance.now(); snd('dash'); loop();
    try { wrap.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } catch (e) { }
    ev('game_play', { game: 'evolve', action: 'start' });
  }
  function end() {
    if (!running) return; running = false; if (ui.dash) ui.dash.hidden = true;
    var before = lvl();
    meta.xp += S.score; meta.runs++; var newBest = S.score > meta.best; if (newBest) meta.best = S.score; meta.maxStage = Math.max(meta.maxStage, S.stage);
    save('beast', meta); var after = lvl();
    ev('game_play', { game: 'evolve', score: S.score, stage: STAGES[S.stage].en, level: after });
    var o = ui.over; o.querySelector('.gt').textContent = S.hp <= 0 ? '倒下了…' : '時間到！';
    o.querySelector('.gs').textContent = S.score;
    o.querySelector('.gsub').textContent = (newBest ? '🏆 新紀錄！' : '最高分 ' + meta.best) + '・進化到「' + STAGES[S.stage].n + '」・吃了 ' + S.eaten + ' 件・擊破 ' + S.kills + ' 個';
    o.querySelector('.glvup').textContent = after > before ? '⬆ 獵人等級提升到 Lv.' + after + '！' + (PERKS.filter(function (p) { return p[0] > before && p[0] <= after; }).map(function (p) { return '解鎖：' + p[1]; }).join('　')) : '獵人經驗 +' + S.score + '（Lv.' + after + '）';
    var list = o.querySelector('.gloot'); list.textContent = '';
    var got = Object.keys(S.caught).map(function (k) { return S.caught[k]; }).sort(function (a, b) { return (b.daily - a.daily) || TIERS.indexOf(b.t) - TIERS.indexOf(a.t) || b.n - a.n; }).slice(0, 6);
    got.forEach(function (g) {
      var a = el('a', 'lt t-' + g.t); a.href = root + 'product.html#' + g.p.i;
      var im = el('img'); im.src = window.__img(g.p); im.alt = g.p.s; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer';
      a.append(im, el('span', 'rar r-' + g.t, g.daily ? '今日' : TNAME[g.t]), el('span', 'ln', g.p.s), el('span', 'lp', window.__money(g.p.p)));
      list.appendChild(a);
    });
    if (!got.length) list.appendChild(el('p', 'sub', '這局沒吃到東西，再來一次！'));
    o.hidden = false;
    var sh = o.querySelector('.gshare'); sh.onclick = function () {
      var txt = '我在「買爆獸進化論」拿到 ' + S.score + ' 分，進化到「' + STAGES[S.stage].n + '」！你能贏我嗎？';
      var url = location.origin + location.pathname;
      if (navigator.share) navigator.share({ title: '買爆獸進化論', text: txt, url: url }).catch(function () { });
      else if (navigator.clipboard) navigator.clipboard.writeText(txt + ' ' + url).then(function () { sh.textContent = '✓ 已複製，貼給朋友'; });
      ev('game_share', { game: 'evolve', score: S.score });
    };
  }
  document.getElementById('gbegin').addEventListener('click', begin);
  ui.over.querySelector('.gagain').addEventListener('click', begin);
  ui.over.querySelector('.gmenu').addEventListener('click', startScreen);
  // ---------- data ----------
  window.__load(function (d) {
    var ok = d.filter(function (p) { return p.m && p.u && !/客製|訂製|刻字|客制/.test(p.s); }).sort(function (a, b) { return b.n - a.n; });
    var top = ok.slice(0, Math.max(300, Math.floor(ok.length * .6)));
    top.forEach(function (p) { pool[tier(p.q || 0)].push(p); });
    TIERS.forEach(function (t) { pool[t] = pool[t].sort(function () { return Math.random() - .5; }).slice(0, t === 'n' ? 24 : 18); pool[t].forEach(sprite); });
    var day = new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10), h = 0; for (var i = 0; i < day.length; i++) h = (h * 31 + day.charCodeAt(i)) % 9973;
    var feat = ok.filter(function (p) { return p.g; }); daily = (feat.length ? feat : ok)[h % (feat.length || ok.length)]; if (daily) sprite(daily);
    var dl = document.getElementById('gdaily');
    if (dl && daily) { dl.textContent = ''; var a = el('a', '', daily.s.length > 26 ? daily.s.slice(0, 26) + '…' : daily.s); a.href = root + 'product.html#' + daily.i; dl.append(el('span', '', '★ 今日爆品（每局出現 3 次，吃到 +60 經驗）：'), a); }
    document.getElementById('gbegin').disabled = false;
  });
  size(); startScreen();
})();
