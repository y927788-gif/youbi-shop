// 社群新品・國外直送: products found through social / new-launch / overseas keywords, filterable by keyword.
document.addEventListener('DOMContentLoaded', function () {
  var root = document.documentElement.dataset.root || '';
  var grid = document.getElementById('ngrid'), chips = document.getElementById('nchips'), more = document.getElementById('nmore'), cnt = document.getElementById('ncnt'), sort = document.getElementById('nsort');
  var GROUPS = JSON.parse(document.getElementById('ngroups').textContent);
  var cur = (location.hash || '').slice(1) ? decodeURIComponent(location.hash.slice(1)) : '', list = [], shown = 0, STEP = 48, all = null;
  function card(p) {
    var a = document.createElement('a'); a.className = 'it'; a.href = root + 'product.html#' + p.i;
    var ph = document.createElement('div'); ph.className = 'ph';
    var im = document.createElement('img'); im.src = window.__img(p); im.alt = p.s; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer'; im.width = 400; im.height = 400;
    ph.appendChild(im); ph.appendChild(window.__rar(p.q || 0));
    var tag = (p.g || '').split(',').filter(function (t) { return GROUPS.all.indexOf(t) >= 0; })[0];
    if (tag) { var b = document.createElement('span'); b.className = 'vid'; b.textContent = tag; ph.appendChild(b); }
    var tg = document.createElement('span'); tg.className = 'tag'; tg.innerHTML = '<span class="d">$</span><span class="v"></span>'; tg.querySelector('.v').textContent = Number(p.p).toLocaleString('zh-TW');
    var n = document.createElement('span'); n.className = 'n'; n.textContent = p.s;
    var s = document.createElement('span'); s.className = 's'; s.textContent = '銷量 ' + (p.sold || '—');
    a.append(ph, tg, n, s); return a;
  }
  function apply() {
    var want = cur ? (GROUPS[cur] || [cur]) : GROUPS.all;
    list = all.filter(function (p) { var g = (p.g || '').split(','); return g.some(function (t) { return want.indexOf(t) >= 0; }); });
    var k = sort.value; list.sort(function (a, b) { return k === 'sold' ? (b.q || 0) - (a.q || 0) : k === 'low' ? a.p - b.p : b.n - a.n; });
    grid.textContent = ''; shown = 0; page(); cnt.textContent = '共 ' + list.length + ' 件';
    chips.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.k === cur)); });
  }
  function page() { list.slice(shown, shown + STEP).forEach(function (p) { grid.appendChild(card(p)); }); shown += STEP; more.hidden = shown >= list.length; }
  chips.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; cur = b.dataset.k; history.replaceState(null, '', cur ? '#' + encodeURIComponent(cur) : location.pathname); apply(); });
  more.addEventListener('click', page); sort.addEventListener('change', apply);
  window.__load(function (d) { all = d; apply(); });
});
