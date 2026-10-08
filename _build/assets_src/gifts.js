// 送禮神器：選對象、預算、風格，從 data/p.json 挑 6 件。Everything runs in the browser.
document.addEventListener('DOMContentLoaded', function () {
  var root = document.documentElement.dataset.root || '';
  function ev(n, p) { if (window.gtag) window.gtag('event', n, p || {}); }
  var STYLE = {
    fun: ['搞笑', '整人', '惡搞', '交換禮物', '趣味', '沙雕', '阿嬤', '創意', '造型', '惡趣味', '迷因', '屁', '崩潰'],
    heal: ['療癒', '捏捏', '公仔', '盲盒', '夜燈', '卡皮巴拉', '水豚', '絨毛', '玩偶', '娃娃', '抱枕', '解壓', '小夜燈', '可愛'],
    use: ['收納', '保溫', '便攜', '充電', '行動電源', '雨傘', '藍牙', '耳機', '露營', '磁吸', '多功能', '隨行', '保冷', '手電筒', '風扇'],
    lux: ['設計', '北歐', '擴香', '香氛', '手沖', '咖啡', '黑膠', '復古', '禮盒', '皮革', '木質', '陶瓷', '水晶', '香水', '質感', '蠟燭'],
    food: ['零食', '巧克力', '禮盒', '餅乾', '咖啡', '茶', '伴手禮', '堅果', '糖', '杜拜', '韓國', '日本']
  };
  var WHO = {
    work: ['交換禮物', '創意', '療癒', '杯', '文具', '桌上', '辦公'],
    friend: ['創意', '造型', '公仔', '盲盒', '桌遊', '搞笑', '整人'],
    love: ['香氛', '項鍊', '手鍊', '飾品', '夜燈', '情侶', '玫瑰', '香水', '禮盒', '永生花', '音樂盒'],
    elder: ['保暖', '茶', '禮盒', '按摩', '拖鞋', '保溫', '圍巾', '毛毯'],
    kid: ['玩具', '積木', '兒童', '公仔', '恐龍', '扭蛋', '盲盒', '繪本', '童'],
    me: []
  };
  var CATS = { fun: ['gift', 'hobby'], heal: ['scent', 'gift', 'hobby'], use: ['3c', 'audio', 'sport', 'kitchen', 'appliance'], lux: ['scent', 'kitchen', 'bags'], food: ['food'] };
  var NO = ['衛生紙', '抽取式', '洗衣', '垃圾袋', '口罩', '批發', '箱購', '尿布', '清潔', '除臭', '除濕', '蚊', '掛勾', '襪', '電池', '網卡', 'SIM', '客製', '訂製', '刻字', '雨衣', '補充包', '替換'];
  var BUDGET = { a: [0, 300], b: [300, 800], c: [800, 2000], d: [2000, 1e9], x: [0, 1e9] };
  var sel = { who: 'work', budget: 'b', style: 'fun' };
  var out = document.getElementById('gout'), sum = document.getElementById('gsum'), again = document.getElementById('gagain');
  var seed = 0, data = null;

  document.querySelectorAll('[data-k]').forEach(function (b) {
    b.addEventListener('click', function () {
      var k = b.dataset.k; sel[k] = b.dataset.v;
      document.querySelectorAll('[data-k="' + k + '"]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      seed = 0; render(); ev('gift_finder', { who: sel.who, budget: sel.budget, style: sel.style });
    });
  });
  again.addEventListener('click', function () { seed++; render(); ev('gift_finder', { action: 'reshuffle' }); });

  function hits(name, words) { var h = []; words.forEach(function (w) { if (name.indexOf(w) >= 0 && h.indexOf(w) < 0) h.push(w); }); return h; }
  function rnd(i) { var x = Math.sin(i * 9301 + seed * 49297) * 233280; return x - Math.floor(x); }

  function render() {
    if (!data) return;
    var bd = BUDGET[sel.budget], sw = STYLE[sel.style], ww = WHO[sel.who], sc = CATS[sel.style] || [];
    var ranked = [];
    data.forEach(function (p, i) {
      if (!p.u || !p.m || p.p < bd[0] || p.p >= bd[1]) return;
      var nm = p.s + ' ' + (p.g || '');
      if (NO.some(function (w) { return nm.indexOf(w) >= 0; })) return;
      if (sel.style === 'food' && p.c !== 'food') return;
      if (sel.style !== 'food' && p.c === 'food' && sel.who !== 'elder') return;
      if ((p.q || 0) < 30) return;  // skip listings with almost no sales
      var hs = hits(nm, sw), hw = hits(nm, ww);
      var score = (p.n || 0) + hs.length * 2.2 + hw.length * 1.6 + (sc.indexOf(p.c) >= 0 ? .8 : 0) + (p.g ? .6 : 0);
      if (!hs.length && !hw.length && sc.indexOf(p.c) < 0) score -= 3;
      ranked.push({ p: p, s: score, why: hs.concat(hw).slice(0, 3), r: rnd(i) });
    });
    ranked.sort(function (a, b) { return b.s - a.s; });
    var top = ranked.slice(0, 40);
    if (seed) top.sort(function (a, b) { return (b.s + b.r * 4) - (a.s + a.r * 4); });
    // avoid near-duplicates: skip items sharing 3+ two-character pieces with one already picked (generic words removed)
    var used = [], picks = [], GEN = /禮物|交換|療癒|小物|可愛|現貨|創意|造型|小夜燈|夜燈/g;
    function grams(s) { s = s.replace(GEN, '').replace(/[^\u4e00-\u9fffA-Za-z]/g, '').slice(0, 24); var o = {}; for (var i = 0; i < s.length - 1; i++) o[s.substr(i, 2)] = 1; return o; }
    for (var j = 0; j < top.length && picks.length < 6; j++) {
      var gset = grams(top[j].p.s), dup = used.some(function (u) { var n = 0; for (var k in gset) if (u[k]) n++; return n >= 3; });
      if (dup) continue; used.push(gset); picks.push(top[j]);
    }
    out.textContent = '';
    sum.textContent = ranked.length ? '從 ' + ranked.length + ' 件符合的商品裡挑出這 ' + picks.length + ' 件' : '這個組合找不到商品，換個預算或風格試試';
    picks.forEach(function (x, idx) {
      var p = x.p, a = document.createElement('a'); a.className = 'gift'; a.href = root + 'product.html#' + p.i; a.style.animationDelay = (idx * 70) + 'ms';
      var ph = document.createElement('div'); ph.className = 'ph';
      var im = document.createElement('img'); im.src = window.__img(p, 1); im.alt = p.s; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer'; ph.appendChild(im); ph.appendChild(window.__rar(p.q || 0));
      var n = document.createElement('span'); n.className = 'n'; n.textContent = p.s;
      var m = document.createElement('span'); m.className = 'm'; m.textContent = window.__money(p.p) + '・銷量 ' + p.sold;
      var w = document.createElement('span'); w.className = 'why'; w.textContent = x.why.length ? '#' + x.why.join(' #') : (p.g ? '#' + p.g.split(',')[0] : '#人氣');
      a.append(ph, n, m, w); out.appendChild(a);
    });
  }
  window.__load(function (d) { data = d; render(); });
});
