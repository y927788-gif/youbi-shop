// 雙11 降價雷達：倒數、真降價（比近 30 天最高價便宜）、近 30 天最低價、賣場標示折扣最多的特色商品。
document.addEventListener('DOMContentLoaded', function () {
  var root = document.documentElement.dataset.root || '';
  var T = Date.parse('2026-11-11T00:00:00+08:00');
  var cd = document.getElementById('cd');
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function tick() {
    var s = Math.max(0, Math.floor((T - Date.now()) / 1000));
    var d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
    cd.querySelector('[data-u=d]').textContent = d; cd.querySelector('[data-u=h]').textContent = pad(h);
    cd.querySelector('[data-u=m]').textContent = pad(m); cd.querySelector('[data-u=s]').textContent = pad(x);
    if (!s) { document.getElementById('cdlab').textContent = '雙11 開跑中'; }
  }
  tick(); setInterval(tick, 1000);
  var NO = ['衛生紙', '抽取式', '洗衣', '垃圾袋', '口罩', '批發', '箱購', '尿布', '清潔', '除臭', '除濕', '蚊', '掛勾', '襪', '電池', '網卡', 'SIM', '客製', '訂製', '補充包'];
  function card(p, badge) {
    var a = document.createElement('a'); a.className = 'it'; a.href = root + 'product.html#' + p.i;
    var ph = document.createElement('div'); ph.className = 'ph';
    var im = document.createElement('img'); im.src = window.__img(p); im.alt = p.s; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer'; im.width = 400; im.height = 400;
    ph.appendChild(im); ph.appendChild(window.__rar(p.q || 0));
    if (badge) { var b = document.createElement('span'); b.className = 'drop'; b.textContent = badge; ph.appendChild(b); }
    var tg = document.createElement('span'); tg.className = 'tag'; tg.innerHTML = '<span class="d">$</span><span class="v"></span>'; tg.querySelector('.v').textContent = Number(p.p).toLocaleString('zh-TW');
    var n = document.createElement('span'); n.className = 'n'; n.textContent = p.s;
    var s = document.createElement('span'); s.className = 's'; s.textContent = p.lo && p.lo < p.p ? '30 天最低 $' + p.lo : '銷量戰力 ' + p.sold;
    a.append(ph, tg, n, s); return a;
  }
  window.__load(function (d) {
    var ok = d.filter(function (p) { return p.u && p.m && !NO.some(function (w) { return p.s.indexOf(w) >= 0; }); });
    var tracked = d.filter(function (p) { return p.tk >= 2; }).length;
    var drops = ok.filter(function (p) { return p.dr >= 5; }).sort(function (a, b) { return b.dr - a.dr || b.n - a.n; }).slice(0, 36);
    var lows = ok.filter(function (p) { return p.lw && !(p.dr >= 5); }).sort(function (a, b) { return b.n - a.n; }).slice(0, 24);
    var med = d.map(function (p) { return p.n; }).sort(function (a, b) { return a - b; })[Math.floor(d.length / 2)];
    var off = ok.filter(function (p) { return p.d && p.n >= med && +p.d >= 3 && +p.d <= 7; }).sort(function (a, b) { return (+a.d) - (+b.d) || b.n - a.n; }).slice(0, 24);
    function fill(id, list, badge, empty) {
      var g = document.getElementById(id); g.textContent = '';
      if (!list.length) { var p = document.createElement('p'); p.className = 'note'; p.textContent = empty; g.appendChild(p); g.classList.remove('grid'); return; }
      list.forEach(function (p) { g.appendChild(card(p, badge(p))); });
    }
    fill('drops', drops, function (p) { return '↓' + p.dr + '%'; }, '價格追蹤從 10/6 開始，每天上架時記錄一次價格，目前有 ' + tracked + ' 件商品累積到兩天以上的紀錄。等同一件商品被記錄到降價，就會出現在這裡。');
    fill('lows', lows, function () { return '30 天最低'; }, '還在累積價格紀錄（至少要有 3 天的價格才算得出近 30 天最低）。');
    fill('offs', off, function (p) { return p.d + ' 折'; }, '目前沒有符合的商品。');
    document.getElementById('trk').textContent = tracked;
  });
});
