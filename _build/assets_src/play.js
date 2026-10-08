// 遊戲區：每日翻牌（含圖鑑）、爆品比大小、猜價格。All data from data/p.json; progress kept in this browser only.
document.addEventListener('DOMContentLoaded', function () {
  var root = document.documentElement.dataset.root || '';
  function ev(n, p) { if (window.gtag) window.gtag('event', n, p || {}); }
  function store(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem('yb_' + k) || 'null'); localStorage.setItem('yb_' + k, JSON.stringify(v)); } catch (e) { return v === undefined ? null : undefined; } }
  var mem = {};
  function get(k, d) { var v = store(k); if (v === null || v === undefined) v = mem[k]; return v === undefined || v === null ? d : v; }
  function put(k, v) { mem[k] = v; store(k, v); }
  var today = new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10);
  function tier(q) { return q >= 1e6 ? 'ur' : q >= 3e5 ? 'ssr' : q >= 5e4 ? 'sr' : q >= 1e4 ? 'r' : 'n'; }
  var TN = { ur: 'UR', ssr: 'SSR', sr: 'SR', r: 'R', n: 'N' };
  var LUCK = { ur: '超大吉', ssr: '大吉', sr: '中吉', r: '小吉', n: '吉' };
  var LUCKT = { ur: '傳說降臨！今天做什麼都順，適合許願。', ssr: '金光閃閃，今天很適合買點小東西犒賞自己。', sr: '紫色光芒，運氣不錯，記得多喝水。', r: '穩穩的，平凡也是一種幸福。', n: '平安就是福，明天再來挑戰 UR！' };
  function el(t, c, txt) { var e = document.createElement(t); if (c) e.className = c; if (txt !== undefined) e.textContent = txt; return e; }
  function money(n) { return window.__money(n); }
  function pick(a) { return a[Math.floor(Math.random() * a.length)]; }

  // tabs
  var tabs = document.querySelectorAll('[data-tab]');
  function show(id) { tabs.forEach(function (b) { b.setAttribute('aria-selected', String(b.dataset.tab === id)); }); document.querySelectorAll('.gpanel').forEach(function (p) { p.hidden = p.id !== id; }); }
  tabs.forEach(function (b) { b.addEventListener('click', function () { show(b.dataset.tab); history.replaceState(null, '', '#' + b.dataset.tab); }); });
  var h0 = location.hash.slice(1); show({ gacha: 1, hl: 1, price: 1 }[h0] ? h0 : 'gacha');

  window.__load(function (all) {
    var pool = all.filter(function (p) { return p.u && p.m; });
    var byT = { ur: [], ssr: [], sr: [], r: [], n: [] };
    pool.forEach(function (p) { byT[tier(p.q || 0)].push(p); });
    ['ur', 'ssr', 'sr', 'r', 'n'].forEach(function (k) { byT[k].sort(function (a, b) { return b.n - a.n; }); });
    var byId = {}; pool.forEach(function (p) { byId[p.i] = p; });

    // ================= 每日翻牌 =================
    var RATE = [['ur', .04], ['ssr', .12], ['sr', .26], ['r', .3], ['n', .28]];
    function roll() {
      var x = Math.random(), t = 'n';
      for (var i = 0, c = 0; i < RATE.length; i++) { c += RATE[i][1]; if (x < c) { t = RATE[i][0]; break; } }
      var arr = byT[t].length ? byT[t] : pool;
      var top = arr.slice(0, Math.max(30, Math.floor(arr.length * .6)));  // prefer the more interesting half
      return pick(top);
    }
    var LIMIT = 3;
    var state = get('gacha', null);
    if (!state || state.d !== today) state = { d: today, n: 0, ten: false };
    var dex = get('dex', {});
    var gStage = document.getElementById('gstage'), gBtn = document.getElementById('gone'), gTen = document.getElementById('gten'), gLeft = document.getElementById('gleft'), gRes = document.getElementById('gres'), gDex = document.getElementById('gdex'), gDexN = document.getElementById('gdexn');
    function left() { gLeft.textContent = '今天還有 ' + Math.max(0, LIMIT - state.n) + ' 次單翻' + (state.ten ? '' : '・1 次十連翻'); gBtn.disabled = state.n >= LIMIT; gTen.disabled = state.ten; }
    function cardEl(p, big) {
      var t = tier(p.q || 0);
      var c = el('div', 'gc3 t-' + t + (big ? ' big' : ''));
      var inner = el('div', 'gci');
      var back = el('div', 'gcb'); back.appendChild(el('b', '', '今天\n買這個'));
      var front = el('a', 'gcf'); front.href = root + 'product.html#' + p.i;
      var im = el('img'); im.src = window.__img(p, big); im.alt = p.s; im.referrerPolicy = 'no-referrer'; im.loading = 'lazy';
      var badge = el('span', 'rar r-' + t, TN[t]);
      var nm = el('span', 'gn', p.s); var pr = el('span', 'gp', money(p.p));
      front.append(im, badge, nm, pr);
      inner.append(back, front); c.appendChild(inner); return c;
    }
    function saveDex(p) { dex[p.i] = tier(p.q || 0); put('dex', dex); renderDex(); }
    function renderDex() {
      var ids = Object.keys(dex).filter(function (i) { return byId[i]; });
      gDexN.textContent = ids.length + ' / ' + pool.length;
      gDex.textContent = '';
      var order = { ur: 0, ssr: 1, sr: 2, r: 3, n: 4 };
      ids.sort(function (a, b) { return order[dex[a]] - order[dex[b]]; }).slice(0, 60).forEach(function (i) {
        var p = byId[i], a = el('a', 'dx t-' + dex[i]); a.href = root + 'product.html#' + i; a.title = p.s;
        var im = el('img'); im.src = window.__img(p); im.alt = p.s; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer';
        a.append(im, el('span', 'rar r-' + dex[i], TN[dex[i]])); gDex.appendChild(a);
      });
      if (!ids.length) gDex.appendChild(el('p', 'sub', '還沒翻到任何卡。翻到的商品會收進這裡。'));
    }
    function result(p) {
      var t = tier(p.q || 0); gRes.textContent = '';
      var h = el('p', 'luck t-' + t); h.append(el('small', '', '今日運勢'), el('strong', '', LUCK[t]));
      var msg = el('p', 'sub', LUCKT[t]);
      var row = el('div', 'gact');
      var a1 = el('a', 'more', '看這件'); a1.href = root + 'product.html#' + p.i; a1.style.textDecoration = 'none';
      var a2 = el('a', 'ghost', '到蝦皮看 ›'); a2.href = p.u; a2.target = '_blank'; a2.rel = 'sponsored nofollow noopener';
      row.append(a1, a2);
      var f = el('p', 'fine', '推廣連結・價格以購物網站為準');
      gRes.append(h, el('p', 'gname', p.s), el('p', 'gmeta', money(p.p) + '・銷量 ' + p.sold), msg, row, f);
    }
    function drawOne() {
      if (state.n >= LIMIT) return;
      state.n++; put('gacha', state); left();
      var p = roll(), t = tier(p.q || 0);
      gStage.textContent = ''; gRes.textContent = '';
      var c = cardEl(p, true); gStage.appendChild(c); gStage.className = 'gstage charge t-' + t;
      setTimeout(function () { c.classList.add('flip'); gStage.className = 'gstage burst t-' + t; result(p); saveDex(p); }, 900);
      ev('game_play', { game: 'gacha', result: TN[t] });
    }
    function drawTen() {
      if (state.ten) return; state.ten = true; put('gacha', state); left();
      gStage.textContent = ''; gRes.textContent = ''; gStage.className = 'gstage ten';
      var best = null, ord = { ur: 0, ssr: 1, sr: 2, r: 3, n: 4 };
      for (var i = 0; i < 10; i++) {
        var p = roll(); if (i === 9 && !['ur', 'ssr', 'sr'].some(function (k) { return k === tier(p.q || 0); }) && byT.sr.length) p = pick(byT.sr.slice(0, 40)); // 10th card: SR or better
        var c = cardEl(p, false); gStage.appendChild(c);
        (function (c, d) { setTimeout(function () { c.classList.add('flip'); }, 300 + d * 180); })(c, i);
        saveDex(p); if (!best || ord[tier(p.q || 0)] < ord[tier(best.q || 0)]) best = p;
      }
      setTimeout(function () { result(best); }, 300 + 10 * 180);
      ev('game_play', { game: 'gacha10', result: TN[tier(best.q || 0)] });
    }
    gBtn.addEventListener('click', drawOne); gTen.addEventListener('click', drawTen);
    left(); renderDex();

    // ================= 爆品比大小 =================
    var hlPool = pool.filter(function (p) { return (p.q || 0) > 0; });
    var hlL = document.getElementById('hlL'), hlR = document.getElementById('hlR'), hlMsg = document.getElementById('hlmsg'), hlS = document.getElementById('hls'), hlB = document.getElementById('hlb');
    var hlBtns = document.querySelectorAll('[data-hl]'), hlAgain = document.getElementById('hlagain');
    var cur, nxt, streak = 0, best = get('hlbest', 0), busy = false;
    function other(p) { for (var k = 0; k < 60; k++) { var x = pick(hlPool); var r = (x.q || 1) / (p.q || 1); if (x.i !== p.i && (r >= 1.6 || r <= .62)) return x; } return pick(hlPool); }
    function face(box, p, reveal) {
      box.textContent = '';
      var im = el('img'); im.src = window.__img(p, 1); im.alt = p.s; im.referrerPolicy = 'no-referrer';
      var n = el('a', 'hn', p.s); n.href = root + 'product.html#' + p.i;
      var s = el('p', 'hs'); s.append(el('small', '', '已售出'), el('strong', '', reveal ? p.sold : '？？？'));
      box.append(im, n, el('p', 'hp', money(p.p)), s);
    }
    function hlStart() { cur = pick(hlPool); nxt = other(cur); streak = 0; face(hlL, cur, true); face(hlR, nxt, false); hlS.textContent = '0'; hlB.textContent = best; hlMsg.textContent = '右邊這件，賣得比左邊多還是少？'; hlAgain.hidden = true; hlBtns.forEach(function (b) { b.disabled = false; }); busy = false; }
    hlBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        if (busy) return; busy = true;
        var more = (nxt.q || 0) > (cur.q || 0), ok = (b.dataset.hl === 'more') === more;
        face(hlR, nxt, true); hlR.classList.add(ok ? 'ok' : 'no');
        if (ok) {
          streak++; hlS.textContent = streak; if (streak > best) { best = streak; put('hlbest', best); hlB.textContent = best; }
          hlMsg.textContent = ['答對！', '眼光不錯！', '連勝中！', '蝦皮雷達全開！'][Math.min(3, streak - 1)];
          setTimeout(function () { hlR.classList.remove('ok'); cur = nxt; nxt = other(cur); face(hlL, cur, true); face(hlR, nxt, false); hlMsg.textContent = '下一題：右邊賣得比較多還是少？'; busy = false; }, 1300);
        } else {
          hlMsg.textContent = '可惜！這次連勝 ' + streak + ' 題，最佳紀錄 ' + best + ' 題。';
          hlBtns.forEach(function (x) { x.disabled = true; }); hlAgain.hidden = false;
          ev('game_play', { game: 'higher_lower', score: streak });
          setTimeout(function () { hlR.classList.remove('no'); }, 1200);
        }
      });
    });
    hlAgain.addEventListener('click', hlStart); hlStart();

    // ================= 猜價格 =================
    var prPool = pool.filter(function (p) { return p.p >= 60 && !/\$|元|NT|[0-9]{3,}/.test(p.s); });
    var prBox = document.getElementById('prq'), prMsg = document.getElementById('prmsg'), prN = document.getElementById('prn'), prS = document.getElementById('prs'), prOpt = document.getElementById('propt'), prAgain = document.getElementById('pragain');
    var round = 0, score = 0, ROUNDS = 10;
    function nice(x) { return x < 100 ? Math.round(x / 5) * 5 - 1 : x < 1000 ? Math.round(x / 10) * 10 - 1 : Math.round(x / 50) * 50; }
    function prNext() {
      if (round >= ROUNDS) {
        var title = score >= 10 ? '價格之神' : score >= 7 ? '蝦皮老司機' : score >= 4 ? '精打細算' : '網購新手';
        prBox.textContent = ''; prOpt.textContent = '';
        prMsg.textContent = '答對 ' + score + ' / ' + ROUNDS + ' 題，稱號：「' + title + '」';
        prAgain.hidden = false; ev('game_play', { game: 'guess_price', score: score }); return;
      }
      round++; prN.textContent = round + ' / ' + ROUNDS;
      var p = pick(prPool), real = p.p;
      var opts = [real, nice(real * (.42 + Math.random() * .2)), nice(real * (1.6 + Math.random() * .7))].filter(function (v, i, a) { return a.indexOf(v) === i && v > 0; });
      while (opts.length < 3) opts.push(nice(real * (2.4 + Math.random())));
      opts.sort(function () { return Math.random() - .5; });
      prBox.textContent = '';
      var im = el('img'); im.src = window.__img(p, 1); im.alt = p.s; im.referrerPolicy = 'no-referrer';
      prBox.append(im, el('p', 'hn', p.s));
      prMsg.textContent = '這件賣多少？'; prOpt.textContent = '';
      opts.forEach(function (v) {
        var b = el('button', 'chip', money(v)); b.type = 'button';
        b.addEventListener('click', function () {
          prOpt.querySelectorAll('button').forEach(function (x) { x.disabled = true; if (x.textContent === money(real)) x.classList.add('on'); });
          if (v === real) { score++; prMsg.textContent = '答對！就是 ' + money(real); } else { b.classList.add('bad'); prMsg.textContent = '答案是 ' + money(real) + '（銷量 ' + p.sold + '）'; }
          prS.textContent = score; setTimeout(prNext, 1500);
        });
        prOpt.appendChild(b);
      });
    }
    function prStart() { round = 0; score = 0; prS.textContent = '0'; prAgain.hidden = true; prNext(); }
    prAgain.addEventListener('click', prStart); prStart();
  });
});
