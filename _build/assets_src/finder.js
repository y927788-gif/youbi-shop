/* 今天買這個 找東西小幫手（吉祥物＋AI 理解需求＋本站紀錄個人化）
   - 推薦的商品一律來自本站 data/p.json，AI 只負責把一句話轉成「分類／關鍵字／預算」。
   - 個人化只用客人在本站的行為，存在他自己的瀏覽器（localStorage yb_me），不上傳；可一鍵清除或關閉。
   - 社群連結可帶 ?for=主題 或 ?q=一句話，落地就看到對應商品。 */
(function () {
  'use strict';
  var D = document, H = D.documentElement, root = H.dataset.root || '';
  // AI 後端是獨立的小 Worker youbi-shop-find（本機測試時跟著 data-api 走 127.0.0.1）
  var API = /127\.0\.0\.1|localhost/.test(H.dataset.api || '') ? H.dataset.api : (H.dataset.find || 'https://api.youbi-shop.com'), API2 = 'https://youbi-shop-find.y927788.workers.dev';  // 10/7 改用自己的網域；被擋時自動退回舊網址
  var MASCOT = 'cat';  // 使用者選定後改這裡：tag 標標／cat 夜貓／bag 袋袋
  var NAMES = { tag: '標標', cat: '夜貓', bag: '袋袋' };
  var SVG = {"tag": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"-8 -8 256 266\"><defs><filter id=\"stk\" x=\"-10%\" y=\"-10%\" width=\"120%\" height=\"120%\"><feMorphology in=\"SourceAlpha\" operator=\"dilate\" radius=\"5\" result=\"d\"/><feFlood flood-color=\"#FFF6EC\"/><feComposite in2=\"d\" operator=\"in\" result=\"o\"/><feMerge><feMergeNode in=\"o\"/><feMergeNode in=\"SourceGraphic\"/></feMerge></filter></defs><g filter=\"url(#stk)\"><g stroke=\"#111\" stroke-width=\"8\" stroke-linecap=\"round\" stroke-linejoin=\"round\">\n<path d=\"M120 52 C 104 22, 140 4, 156 22\" fill=\"none\"/>\n<path d=\"M62 168 L 34 138\" fill=\"none\"/>\n<ellipse cx=\"96\" cy=\"226\" rx=\"16\" ry=\"9\" fill=\"#111\"/><ellipse cx=\"146\" cy=\"226\" rx=\"16\" ry=\"9\" fill=\"#111\"/>\n<path d=\"M60 76 L120 34 L180 76 L180 198 Q180 214 164 214 L76 214 Q60 214 60 198 Z\" fill=\"#FFE600\"/>\n<circle cx=\"120\" cy=\"66\" r=\"9\" fill=\"#111\" stroke=\"none\"/>\n<path d=\"M178 170 L 192 160\" fill=\"none\"/>\n<circle cx=\"208\" cy=\"146\" r=\"20\" fill=\"#9FF4FF\" fill-opacity=\".55\"/>\n</g>\n<ellipse cx=\"98\" cy=\"122\" rx=\"10\" ry=\"13\" fill=\"#111\"/><ellipse cx=\"142\" cy=\"122\" rx=\"10\" ry=\"13\" fill=\"#111\"/>\n<circle cx=\"101\" cy=\"117\" r=\"3.5\" fill=\"#fff\"/><circle cx=\"145\" cy=\"117\" r=\"3.5\" fill=\"#fff\"/>\n<ellipse cx=\"80\" cy=\"146\" rx=\"11\" ry=\"7\" fill=\"#FF6B6B\" opacity=\".75\"/><ellipse cx=\"160\" cy=\"146\" rx=\"11\" ry=\"7\" fill=\"#FF6B6B\" opacity=\".75\"/>\n<path d=\"M108 146 Q120 160 132 146\" fill=\"none\" stroke=\"#111\" stroke-width=\"6\" stroke-linecap=\"round\"/>\n<rect x=\"60\" y=\"180\" width=\"120\" height=\"18\" fill=\"#111\"/><text x=\"120\" y=\"194\" font-family=\"Anton,Impact,sans-serif\" font-size=\"15\" fill=\"#FFE600\" text-anchor=\"middle\" letter-spacing=\"2\">TODAY</text>\n<path d=\"M199 136 l6 -4\" stroke=\"#fff\" stroke-width=\"4\" stroke-linecap=\"round\"/>\n</g></svg>", "cat": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"-8 -8 256 266\"><defs><filter id=\"stk\" x=\"-10%\" y=\"-10%\" width=\"120%\" height=\"120%\"><feMorphology in=\"SourceAlpha\" operator=\"dilate\" radius=\"5\" result=\"d\"/><feFlood flood-color=\"#FFF6EC\"/><feComposite in2=\"d\" operator=\"in\" result=\"o\"/><feMerge><feMergeNode in=\"o\"/><feMergeNode in=\"SourceGraphic\"/></feMerge></filter></defs><g filter=\"url(#stk)\"><g stroke=\"#FFE600\" stroke-width=\"6\" stroke-linejoin=\"round\" stroke-linecap=\"round\">\n<path d=\"M164 200 C 210 196, 214 150, 196 132\" fill=\"none\" stroke=\"#FFE600\" stroke-width=\"14\"/>\n<path d=\"M164 200 C 210 196, 214 150, 196 132\" fill=\"none\" stroke=\"#1A1714\" stroke-width=\"6\"/>\n<path d=\"M70 230 Q60 160 120 150 Q180 160 170 230 Z\" fill=\"#1A1714\"/>\n<path d=\"M58 62 L72 18 L102 50 Q120 44 138 50 L168 18 L182 62 Q200 92 186 122 Q170 156 120 156 Q70 156 54 122 Q40 92 58 62 Z\" fill=\"#1A1714\"/>\n</g>\n<path d=\"M72 30 L80 52 L92 46 Z\" fill=\"#FFE600\"/><path d=\"M168 30 L160 52 L148 46 Z\" fill=\"#FFE600\"/>\n<ellipse cx=\"96\" cy=\"100\" rx=\"17\" ry=\"19\" fill=\"#FFE600\"/><ellipse cx=\"144\" cy=\"100\" rx=\"17\" ry=\"19\" fill=\"#FFE600\"/>\n<ellipse cx=\"98\" cy=\"102\" rx=\"6\" ry=\"13\" fill=\"#111\"/><ellipse cx=\"146\" cy=\"102\" rx=\"6\" ry=\"13\" fill=\"#111\"/>\n<circle cx=\"92\" cy=\"94\" r=\"4\" fill=\"#fff\"/><circle cx=\"140\" cy=\"94\" r=\"4\" fill=\"#fff\"/>\n<path d=\"M114 124 L126 124 L120 131 Z\" fill=\"#FF8FA3\"/>\n<path d=\"M120 131 Q112 140 104 134 M120 131 Q128 140 136 134\" fill=\"none\" stroke=\"#FFE600\" stroke-width=\"3.5\" stroke-linecap=\"round\"/>\n<path d=\"M60 122 L30 116 M60 130 L32 134 M180 122 L210 116 M180 130 L208 134\" stroke=\"#FFE600\" stroke-width=\"3\" stroke-linecap=\"round\"/>\n<path d=\"M80 152 Q120 172 160 152 L156 170 Q120 186 84 170 Z\" fill=\"#FF2E3B\" stroke=\"#FFE600\" stroke-width=\"4\" stroke-linejoin=\"round\"/>\n<g transform=\"translate(38 168)\"><line x1=\"14\" y1=\"-14\" x2=\"14\" y2=\"0\" stroke=\"#FFE600\" stroke-width=\"4\"/><rect x=\"0\" y=\"0\" width=\"28\" height=\"6\" rx=\"2\" fill=\"#FFE600\"/><ellipse cx=\"14\" cy=\"24\" rx=\"18\" ry=\"20\" fill=\"#FF2E3B\" stroke=\"#FFE600\" stroke-width=\"4\"/><path d=\"M2 18 H26 M2 30 H26\" stroke=\"#FFE600\" stroke-width=\"3\"/><rect x=\"0\" y=\"42\" width=\"28\" height=\"6\" rx=\"2\" fill=\"#FFE600\"/><circle cx=\"14\" cy=\"24\" r=\"22\" fill=\"#FFB020\" opacity=\".18\"/></g>\n<ellipse cx=\"96\" cy=\"232\" rx=\"16\" ry=\"8\" fill=\"#1A1714\" stroke=\"#FFE600\" stroke-width=\"4\"/><ellipse cx=\"144\" cy=\"232\" rx=\"16\" ry=\"8\" fill=\"#1A1714\" stroke=\"#FFE600\" stroke-width=\"4\"/>\n</g></svg>", "bag": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"-8 -8 256 266\"><defs><filter id=\"stk\" x=\"-10%\" y=\"-10%\" width=\"120%\" height=\"120%\"><feMorphology in=\"SourceAlpha\" operator=\"dilate\" radius=\"5\" result=\"d\"/><feFlood flood-color=\"#FFF6EC\"/><feComposite in2=\"d\" operator=\"in\" result=\"o\"/><feMerge><feMergeNode in=\"o\"/><feMergeNode in=\"SourceGraphic\"/></feMerge></filter></defs><g filter=\"url(#stk)\"><g stroke=\"#111\" stroke-width=\"8\" stroke-linejoin=\"round\" stroke-linecap=\"round\">\n<path d=\"M88 74 C 88 30, 152 30, 152 74\" fill=\"none\"/>\n<rect x=\"132\" y=\"40\" width=\"34\" height=\"46\" rx=\"4\" fill=\"#3CF0FF\" transform=\"rotate(14 149 63)\"/>\n<rect x=\"76\" y=\"46\" width=\"28\" height=\"40\" rx=\"4\" fill=\"#FF2E3B\" transform=\"rotate(-12 90 66)\"/>\n<path d=\"M50 78 L190 78 L200 212 Q200 222 190 222 L50 222 Q40 222 40 212 Z\" fill=\"#FFE600\"/>\n<path d=\"M40 150 L 18 128\" fill=\"none\"/><path d=\"M200 150 L 222 132\" fill=\"none\"/>\n<ellipse cx=\"92\" cy=\"232\" rx=\"16\" ry=\"8\" fill=\"#111\"/><ellipse cx=\"148\" cy=\"232\" rx=\"16\" ry=\"8\" fill=\"#111\"/>\n</g>\n<path d=\"M54 78 L186 78 L188 96 L52 96 Z\" fill=\"#111\"/>\n<text x=\"120\" y=\"92\" font-family=\"Noto Sans TC,sans-serif\" font-weight=\"900\" font-size=\"13\" fill=\"#FFE600\" text-anchor=\"middle\" letter-spacing=\"3\">今天買這個</text>\n<path d=\"M84 136 Q96 124 108 136\" fill=\"none\" stroke=\"#111\" stroke-width=\"7\" stroke-linecap=\"round\"/>\n<path d=\"M132 136 Q144 124 156 136\" fill=\"none\" stroke=\"#111\" stroke-width=\"7\" stroke-linecap=\"round\"/>\n<ellipse cx=\"74\" cy=\"160\" rx=\"12\" ry=\"7\" fill=\"#FF6B6B\" opacity=\".75\"/><ellipse cx=\"166\" cy=\"160\" rx=\"12\" ry=\"7\" fill=\"#FF6B6B\" opacity=\".75\"/>\n<path d=\"M104 158 Q120 182 136 158 Z\" fill=\"#111\" stroke=\"#111\" stroke-width=\"4\" stroke-linejoin=\"round\"/>\n<path d=\"M112 168 Q120 174 128 168\" fill=\"#FF8FA3\"/>\n<path d=\"M58 200 L 74 200 M166 200 L 182 200\" stroke=\"#111\" stroke-width=\"5\" stroke-linecap=\"round\"/>\n</g></svg>"};
  var NAME = NAMES[MASCOT], FACE = SVG[MASCOT];
  var CATS = { other: '生活雜貨', bags: '包包飾品', food: '美食零食', shoes: '鞋子', fashion: '服飾', appliance: '家電', beauty: '美妝個清', scent: '香氛燈飾', clean: '清潔洗衣', sport: '運動戶外', gift: '客製禮物', kitchen: '廚房', '3c': '3C 周邊', hobby: '玩具卡牌', storage: '收納居家', audio: '耳機音響', pet: '寵物', diy: '居家修繕', bedding: '寢具' };
  var path = location.pathname.split('/').pop() || 'index.html';
  var NOBTN = /^(dungeon|game)\.html$/.test(path);  // 遊戲頁不放浮動按鈕，免得擋到操作

  function ev(n, p) { try { if (window.gtag) window.gtag('event', n, p || {}); } catch (e) {} }
  // ---------- 本站紀錄（只存在這台裝置） ----------
  function lget(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function lset(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function ldel(k) { try { localStorage.removeItem(k); } catch (e) {} }
  function isOff() { return lget('yb_me_off', false); }
  function me() { var m = lget('yb_me', null); return m && m.c ? m : { c: {}, q: [], seen: [], t: 0 }; }
  function rec(fn) { if (isOff()) return; var m = me(); fn(m); m.t = Date.now(); lset('yb_me', m); }
  function addCat(c, w) { if (!CATS[c]) return; rec(function (m) { for (var k in m.c) m.c[k] = Math.round(m.c[k] * 97) / 100; m.c[c] = (m.c[c] || 0) + (w || 1); }); }
  function addQ(q) { q = String(q || '').trim().slice(0, 30); if (q.length < 2) return; rec(function (m) { m.q = [q].concat(m.q.filter(function (x) { return x !== q; })).slice(0, 5); }); }
  function addSeen(id) { rec(function (m) { m.seen = [id].concat(m.seen.filter(function (x) { return x !== id; })).slice(0, 30); }); }

  // ---------- 資料 ----------
  var DATA = null;
  function load(cb) {
    if (DATA) return cb(DATA);
    if (window.__load) return window.__load(function (d) { DATA = d; cb(d); });
    fetch(root + 'data/p.json').then(function (r) { return r.json(); }).then(function (d) { DATA = d; cb(d); }).catch(function () {});
  }
  function img(p) { if (p.mu) return p.mu; return p.m ? 'https://down-aws-tw.img.susercontent.com/file/' + p.m + '_tn' : root + 'img/' + p.i + '.webp'; }
  function nice(s) {  // 賣場標題去掉符號和「現貨、免運」這類字，比較好讀
    return String(s).replace(/[【\[〖(（「][^】\]〗)）」]{0,24}[】\]〗)）」]/g, ' ').replace(/[\u2600-\u27BF\uD83C-\uDBFF\uDC00-\uDFFF\uFE0F]/g, ' ')
      .replace(/台灣現貨|臺灣現貨|現貨|免運費?|隔日到貨|隔日配|最快隔日到|台灣出貨|快速出貨|電子發票|台灣公司貨|公司貨|台灣公司|附發票|開發票|新品上市|檢驗合格|最低價|超低價/g, ' ').replace(/\s+/g, ' ').trim() || s;
  }
  function money(n) { return '$' + Number(n).toLocaleString('zh-TW'); }

  // ---------- 理解需求（本機規則；有 AI 時再合併 AI 的結果） ----------
  var INTENT = [
    [/交換禮物|禮物|送禮|生日|聖誕|紀念日/, ['gift', 'hobby', 'scent'], ['交換禮物', '禮物']],
    [/浴室|發霉|霉/, ['clean', 'storage'], ['除霉', '防霉', '浴室']],
    [/除濕|潮濕|濕氣|反潮/, ['appliance', 'clean', 'storage'], ['除濕']],
    [/租屋|套房|宿舍|小空間/, ['storage', 'diy'], ['免打孔', '伸縮', '收納']],
    [/收納|整理|置物|亂/, ['storage'], ['收納', '置物']],
    [/打掃|清潔|洗衣|拖地|掃地|髒/, ['clean', 'appliance'], ['清潔', '洗衣', '拖把']],
    [/廚房|煮|做菜|料理|鍋|便當/, ['kitchen'], ['鍋', '廚房']],
    [/咖啡/, ['kitchen'], ['咖啡']],
    [/貓/, ['pet'], ['貓']], [/狗/, ['pet'], ['狗']], [/寵物|毛小孩/, ['pet'], []],
    [/耳機|音響|喇叭/, ['audio'], ['耳機', '喇叭']],
    [/充電|手機|行動電源|傳輸線|支架/, ['3c'], ['充電', '行動電源', '支架']],
    [/零食|宵夜|餅乾|泡麵|好吃|嘴饞|吃|餓|下午茶|點心/, ['food'], ['零食', '餅乾']],
    [/保養|化妝|美妝|口紅|面膜|洗髮|保濕/, ['beauty'], []],
    [/香氛|蠟燭|香味|夜燈|氛圍/, ['scent'], ['香氛', '夜燈']],
    [/露營|戶外|登山/, ['sport'], ['露營', '登山']], [/運動|健身|跑步|瑜珈/, ['sport'], ['運動', '健身']],
    [/睡|枕頭|床|棉被|失眠/, ['bedding'], ['枕頭', '被', '床']],
    [/工具|維修|膠帶|修理/, ['diy'], []],
    [/玩具|小孩|兒童|小朋友|卡牌|療癒|紓壓/, ['hobby'], ['玩具', '療癒']],
    [/冷|保暖|冬天|暖/, [], ['保暖', '暖']],
    [/包包|後背包|錢包|包/, ['bags'], ['包']],
    [/鞋/, ['shoes'], ['鞋']],
    [/衣服|外套|褲|裙/, ['fashion'], []],
    [/家電/, ['appliance'], []]
  ];
  var WHO = /(男同事|女同事|同事|男朋友|女朋友|男友|女友|老公|老婆|另一半|爸爸|媽媽|爸媽|長輩|朋友|小孩|兒子|女兒|自己|主管|老闆|學生)/;
  var STOP = /怎麼辦|怎麼|什麼|推薦|一個|好用|有沒有|想要|想買|可以|適合|請問|幫我|有什麼|東西|預算|左右|以內|以下|元|塊|給|送|找|買|的|嗎|呢|啊|喔|我|要|內/g;
  var CN = { 一: 1, 二: 2, 兩: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9 };
  function norm(s) {
    return String(s || '').replace(/藍牙/g, '藍芽').replace(/臺/g, '台')
      .replace(/([一二兩三四五六七八九])萬/g, function (m, d) { return CN[d] * 10000 + '元'; })
      .replace(/([一二兩三四五六七八九])千(?:([一二兩三四五六七八九])百?)?/g, function (m, d, e) { return CN[d] * 1000 + (e ? CN[e] * 100 : 0) + '元'; })
      .replace(/([一二兩三四五六七八九])百(?:([一二三四五六七八九])十?)?/g, function (m, d, e) { return CN[d] * 100 + (e ? CN[e] * 10 : 0) + '元'; })
      .replace(/(\d+(?:\.\d+)?)\s*k\b/gi, function (m, d) { return Math.round(parseFloat(d) * 1000) + '元'; })
      .toLowerCase();
  }
  function localParse(q, data) {
    var t = norm(q), r = { cats: [], kw: [], min: null, max: null, who: '', need: '', miss: [] }, m;
    if ((m = t.match(/(\d{2,6})\s*(?:-|~|～|到|至)\s*(\d{2,6})/))) { r.min = +m[1]; r.max = +m[2]; }
    else if ((m = t.match(/(\d{2,6})\s*(?:元|塊|\$)?\s*(?:以內|以下|內|有找)/))) r.max = +m[1];
    else if ((m = t.match(/(\d{2,6})\s*(?:元|塊)?\s*(?:左右|上下)/))) { r.min = Math.round(+m[1] * .6); r.max = Math.round(+m[1] * 1.4); }
    else if ((m = t.match(/(?:預算|大概|約)\s*(\d{2,6})/))) r.max = +m[1];
    INTENT.forEach(function (it) { if (it[0].test(t)) { it[1].forEach(function (c) { if (r.cats.indexOf(c) < 0) r.cats.push(c); }); it[2].forEach(function (k) { if (r.kw.indexOf(k) < 0) r.kw.push(k); }); } });
    if ((m = t.match(WHO))) r.who = m[1];
    var chunks = t.replace(/\d+/g, ' ').replace(WHO, ' ').replace(STOP, ' ').split(/[\s,，。！？!?、\/]+/).filter(function (x) { return x.length >= 2; });
    chunks.forEach(function (ch) {
      if (r.kw.length >= 6) return;
      if (data.some(function (p) { return p.s.toLowerCase().indexOf(ch) >= 0; })) { if (r.kw.indexOf(ch) < 0) r.kw.unshift(ch); return; }
      if (ch.length <= 8 && !INTENT.some(function (it) { return it[0].test(ch); })) r.miss.push(ch);  // 本站商品名稱裡完全沒有這個詞，也不是常見需求
      for (var i = 0; i + 2 <= ch.length; i++) {  // 長句拆成兩個字，只留商品名稱裡常出現的
        var bi = ch.substr(i, 2), n = 0;
        for (var j = 0; j < data.length && n < 3; j++) if (data[j].s.indexOf(bi) >= 0) n++;
        if (n >= 3 && r.kw.indexOf(bi) < 0) r.kw.push(bi);
      }
    });
    r.kw = r.kw.slice(0, 8);
    r.need = chunks[0] || r.kw[0] || '';
    return r;
  }
  function clean(a) {  // AI 回來的東西一律再檢查一次
    if (!a || typeof a !== 'object') return null;
    var r = { cats: [], kw: [], min: null, max: null, who: '', need: '' };
    (Array.isArray(a.cats) ? a.cats : []).forEach(function (c) { if (CATS[c] && r.cats.length < 3) r.cats.push(c); });
    (Array.isArray(a.kw) ? a.kw : []).forEach(function (k) { k = norm(k).replace(/[^一-鿿a-z0-9]/g, '').slice(0, 10); if (k.length >= 1 && r.kw.length < 6) r.kw.push(k); });
    ['min', 'max'].forEach(function (f) { var v = parseInt(a[f], 10); if (v > 0 && v < 1e6) r[f] = v; });
    if (r.min && r.max && r.min >= r.max * .8) r.min = null;  // 模型常把「1000 以內」寫成 min=max，當成只有上限
    r.who = String(a.who || '').replace(/[^一-鿿A-Za-z0-9]/g, '').slice(0, 8);
    r.need = String(a.need || '').replace(/[^一-鿿A-Za-z0-9 ]/g, '').slice(0, 12);
    return r;
  }
  function merge(loc, ai) {
    if (!ai) return loc;
    var r = { cats: ai.cats.slice(), kw: ai.kw.slice(), min: ai.min != null ? ai.min : loc.min, max: ai.max != null ? ai.max : loc.max, who: ai.who || loc.who, need: ai.need || loc.need, miss: loc.miss || [] };
    loc.cats.forEach(function (c) { if (r.cats.indexOf(c) < 0 && r.cats.length < 4) r.cats.push(c); });
    loc.kw.forEach(function (k) { if (r.kw.indexOf(k) < 0 && r.kw.length < 10) r.kw.push(k); });
    return r;
  }
  function askAI(q) {
    if (!API) return Promise.resolve(null);
    var t = new Promise(function (res) { setTimeout(function () { res(null); }, 6000); });
    var go = function (base) { return fetch(base + '/api/find', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ q: q }) }); };
    var f = go(API).catch(function (e) { if (API2 && API !== API2 && !/127\.0\.0\.1|localhost/.test(API)) return go(API2).then(function (r) { API = API2; return r; }); throw e; })
      .then(function (r) { return r.ok ? r.json() : null; }).then(clean).catch(function () { return null; });
    return Promise.race([f, t]);
  }
  function rank(data, r, skip) {
    var seen = me().seen, out = [], kw = r.kw.map(norm), N = data.length, W = {};
    kw.forEach(function (k) { var df = 0; for (var j = 0; j < N; j++) { var q = data[j]; if (q.s.toLowerCase().indexOf(k) >= 0 || (q.g || '').indexOf(k) >= 0) df++; } W[k] = 1 + Math.log((N + 1) / (df + 1)); });  // 越少見的關鍵字越重要
    function pass(needKw) {
      var L = [];
      data.forEach(function (p) {
        if (p.p < 15 || (r.max && p.p > r.max) || (r.min && p.p < r.min) || (skip && skip[p.i])) return;
        var s = 0, hit = 0, nm = p.s.toLowerCase(), g = p.g || '';
        kw.forEach(function (k) { var i = nm.indexOf(k); if (i >= 0) { s += W[k] * (i < 14 ? 1.3 : 1); hit++; } else if (g.indexOf(k) >= 0) { s += W[k] * .7; hit++; } });
        var ch = r.cats.indexOf(p.c) >= 0;
        if (r.cats.length) s += ch ? 2.5 : -1.5;
        if (needKw ? !hit : !ch) return;
        s += Math.log(((p.q || 0) + 10)) / Math.LN10 * .7 + (p.d ? .4 : 0) + (p.sh ? 1.5 : 0) - (seen.indexOf(p.i) >= 0 ? 1 : 0);
        L.push([s, p]);
      });
      L.sort(function (a, b) { return b[0] - a[0]; });
      if (r.cats.length) {  // 有分類時，分類內的商品優先；分類內夠多就只用分類內的（「生活雜貨」太雜，不算）
        var core = r.cats.filter(function (c) { return c !== 'other'; }); if (!core.length) core = r.cats;
        var inC = L.filter(function (x) { return core.indexOf(x[1].c) >= 0; });
        if (needKw) r.thin = inC.length < 3;
        if (inC.length >= 6) L = inC; else L = inC.concat(L.filter(function (x) { return core.indexOf(x[1].c) < 0; }));
      }
      return L.map(function (x) { return x[1]; });
    }
    out = kw.length ? pass(true) : [];
    if (out.length < 6 && r.cats.length) { var more = pass(false), have = {}; out.forEach(function (p) { have[p.i] = 1; }); more.forEach(function (p) { if (!have[p.i]) out.push(p); }); }
    var uniq = [], names = {};
    out.forEach(function (p) { var k = p.s.slice(0, 8); if (!names[k]) { names[k] = 1; uniq.push(p); } });
    return uniq;
  }

  // ---------- 畫面 ----------
  function el(tag, cls, txt) { var e = D.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function face(cls) { var s = el('span', cls); s.innerHTML = FACE; s.setAttribute('aria-hidden', 'true'); return s; }
  function card(p, where) {
    var a = el('a', 'ybf-card'); a.href = root + 'product.html#' + p.i;
    var im = el('img'); im.src = img(p); im.alt = ''; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer'; im.width = 160; im.height = 160;
    a.appendChild(im); a.appendChild(el('span', 'n', nice(p.s)));
    var b = el('span', 'm'); b.appendChild(el('b', '', money(p.p))); b.appendChild(el('small', '', '已售 ' + (p.sold || '—'))); a.appendChild(b);
    if (p.d) a.appendChild(el('span', 'ybf-off', p.d + ' 折'));
    a.addEventListener('click', function () { addSeen(p.i); addCat(p.c, 2); ev('finder_click', { placement: where, item_name: p.s.slice(0, 60) }); });
    return a;
  }

  var panel, log, input, btn, state = { r: null, list: [], shown: 0, flow: {} };
  function build() {
    if (panel) return;
    panel = el('section', 'ybf'); panel.id = 'ybf'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', NAME + '幫你找東西'); panel.hidden = true;
    var hd = el('div', 'ybf-hd'); hd.appendChild(face('ybf-av'));
    var tt = el('div', 'ybf-tt'); tt.appendChild(el('b', '', NAME)); tt.appendChild(el('small', '', '幫你從本站 ' + (DATA ? DATA.length.toLocaleString('zh-TW') : '2,000+') + ' 件熱銷品裡挑'));
    hd.appendChild(tt);
    var x = el('button', 'ybf-x', '×'); x.type = 'button'; x.setAttribute('aria-label', '關閉'); x.addEventListener('click', close); hd.appendChild(x);
    log = el('div', 'ybf-log'); log.setAttribute('aria-live', 'polite');
    var fm = el('form', 'ybf-in'); input = el('input'); input.type = 'text'; input.maxLength = 60; input.placeholder = '例如：送男同事 500 內、浴室一直發霉'; input.setAttribute('aria-label', '你想找什麼');
    var go = el('button', '', '找'); go.type = 'submit'; fm.appendChild(input); fm.appendChild(go);
    fm.addEventListener('submit', function (e) { e.preventDefault(); var q = input.value.trim(); if (!q) return; input.value = ''; ask(q); });
    var ft = el('p', 'ybf-ft');
    ft.appendChild(D.createTextNode('AI 只幫忙理解你的需求，商品都是本站實際銷量挑出來的，可能會猜錯；商品連結含推廣連結。'));
    var clr = el('button', 'ybf-clr', '清除我的紀錄'); clr.type = 'button';
    clr.addEventListener('click', function () { ldel('yb_me'); lset('yb_me_off', true); say('好，我把你在這台裝置的瀏覽紀錄清掉了，之後也不會再記。想恢復可以按「記住我的喜好」。'); clr.hidden = true; on.hidden = false; ev('finder_clear'); });
    var on = el('button', 'ybf-clr', '記住我的喜好'); on.type = 'button'; on.hidden = !isOff(); clr.hidden = isOff();
    on.addEventListener('click', function () { ldel('yb_me_off'); say('好，之後我會記得你常看的東西（只存在這台裝置）。'); on.hidden = true; clr.hidden = false; });
    ft.appendChild(clr); ft.appendChild(on);
    panel.appendChild(hd); panel.appendChild(log); panel.appendChild(fm); panel.appendChild(ft);
    D.body.appendChild(panel);
    D.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) close(); });
  }
  function say(t, who) { var b = el('div', 'ybf-msg ' + (who || 'bot')); if (who !== 'me') b.appendChild(face('ybf-mini')); b.appendChild(el('p', '', t)); log.appendChild(b); log.scrollTop = log.scrollHeight; return b; }
  function chips(list, cb) {
    var w = el('div', 'ybf-chips');
    list.forEach(function (c) { var b = el('button', '', c[0]); b.type = 'button'; b.addEventListener('click', function () { w.remove(); say(c[0], 'me'); cb(c); }); w.appendChild(b); });
    log.appendChild(w); log.scrollTop = log.scrollHeight;
  }
  var WHOS = [['自己', ''], ['另一半', '另一半'], ['爸媽長輩', '爸媽'], ['朋友同事', '朋友'], ['小孩', '小孩'], ['毛小孩', '寵物']];
  var NEEDS = [['居家收納', ['storage'], ['收納', '置物']], ['打掃清潔', ['clean'], ['清潔']], ['廚房料理', ['kitchen'], []], ['3C 配件', ['3c', 'audio'], []], ['美妝保養', ['beauty'], []], ['好吃零食', ['food'], []], ['送禮驚喜', ['gift', 'scent', 'hobby'], ['禮物']], ['運動戶外', ['sport'], []], ['睡得更好', ['bedding'], []], ['療癒小物', ['hobby', 'scent'], ['療癒']]];
  var BUDGET = [['200 內', 200], ['500 內', 500], ['1,000 內', 1000], ['3,000 內', 3000], ['不限', 0]];
  function start() {
    log.textContent = '';
    var m = me(), last = m.q[0];
    say('喵～我是' + NAME + '，夜市裡哪攤好我都熟。想找什麼？直接打一句話給我，或點下面的選項。' + (last && !isOff() ? '（上次你在找「' + last + '」）' : ''));
    chips(WHOS, function (w) {
      state.flow = { who: w[1] };
      if (w[1] === '寵物') { state.flow.cats = ['pet']; state.flow.kw = []; return askBudget(); }
      say('想解決什麼，或想要哪一類？');
      chips(NEEDS, function (n) { state.flow.cats = n[1]; state.flow.kw = n[2]; state.flow.need = n[0]; if (state.flow.who === '小孩') state.flow.cats = state.flow.cats.concat(['hobby']); askBudget(); });
    });
  }
  function askBudget() {
    say('預算大概多少？');
    chips(BUDGET, function (b) {
      var f = state.flow, r = { cats: f.cats || [], kw: f.kw || [], min: null, max: b[1] || null, who: f.who || '', need: f.need || '' };
      ev('finder_query', { mode: 'chips', cat: r.cats[0] || '' });
      r.cats.forEach(function (c) { addCat(c, 1); });
      load(function (d) { show(d, r); });
    });
  }
  function ask(q) {
    say(q, 'me'); addQ(q);
    var wait = say('喵，我去翻翻看…'); wait.classList.add('wait');
    load(function (d) {
      var loc = localParse(q, d);
      askAI(q).then(function (ai) {
        wait.remove();
        var r = merge(loc, ai);
        ev('finder_query', { mode: 'text', ai: ai ? 1 : 0, cat: r.cats[0] || '' });
        r.cats.slice(0, 2).forEach(function (c) { addCat(c, 1); });
        show(d, r);
      });
    });
  }
  function show(d, r) {
    state.r = r; state.list = rank(d, r); state.shown = 0;
    if (!state.list.length) {
      say('這個我在本站找不到合適的 😅 換個說法試試，或到酷澎館搜尋全站商品。');
      var a = el('a', 'ybf-link', '到酷澎館搜尋 ›'); a.href = root + 'coupang.html#search'; log.appendChild(a);
      return again();
    }
    var bits = [];
    if (r.who) bits.push('買給' + r.who);
    if (r.need) bits.push('想要「' + r.need + '」');
    if (r.max) bits.push('預算 ' + r.max.toLocaleString('zh-TW') + ' 元內');
    var miss = (r.miss || []).filter(function (x) { return !/^(怎麼|一直|很|好|有)/.test(x); });
    if (miss.length) {
      say('老實說，本站目前沒有「' + miss[0] + '」這種商品。' + (bits.length ? bits.join('、') + '，' : '') + '先給你看比較接近的，也可以到酷澎館搜尋全站：');
      var a = el('a', 'ybf-link', '到酷澎館搜尋「' + miss[0] + '」 ›'); a.href = root + 'coupang.html#search'; log.appendChild(a);
    } else if (r.thin) {
      say((bits.length ? '了解，' + bits.join('、') + '。' : '') + '不過這類商品本站還不多，下面是比較相關的，可能不完全是你要的；也可以到酷澎館搜尋全站：');
      var a2 = el('a', 'ybf-link', '到酷澎館搜尋 ›'); a2.href = root + 'coupang.html#search'; log.appendChild(a2);
    } else say((bits.length ? '了解，' + bits.join('、') + '。' : '') + '我照實際銷量挑了這幾件：');
    page();
  }
  function page() {
    var g = el('div', 'ybf-grid');
    state.list.slice(state.shown, state.shown + 6).forEach(function (p) { g.appendChild(card(p, 'finder')); });
    state.shown += 6; log.appendChild(g); log.scrollTop = log.scrollHeight;
    again();
  }
  function again() {
    var opts = [];
    if (state.shown < state.list.length) opts.push(['換一批']);
    opts.push(['重新挑']);
    if (state.r && state.r.cats[0]) opts.push(['看全部「' + CATS[state.r.cats[0]] + '」']);
    chips(opts, function (c) {
      if (c[0] === '換一批') { say('再給你看幾件：'); page(); }
      else if (c[0] === '重新挑') start();
      else location.href = root + 'c/' + state.r.cats[0] + '.html';
    });
  }
  function open(q) {
    load(function () {});
    build(); panel.hidden = false; if (btn) btn.setAttribute('aria-expanded', 'true'); D.body.classList.add('ybf-on');
    if (!log.firstChild) start();
    if (q) ask(q); else setTimeout(function () { try { input.focus({ preventScroll: true }); } catch (e) {} }, 50);
    ev('finder_open');
  }
  function close() { panel.hidden = true; if (btn) { btn.setAttribute('aria-expanded', 'false'); btn.focus(); } D.body.classList.remove('ybf-on'); }

  // ---------- 首頁「猜你在找」與社群落地 ----------
  var TOPIC = {
    bath: ['浴室防霉', ['clean', 'storage'], ['除霉', '防霉', '浴室']], damp: ['除濕', ['appliance', 'clean'], ['除濕']],
    rental: ['租屋好物', ['storage', 'diy'], ['免打孔', '伸縮', '收納']], kitchen: ['廚房', ['kitchen'], []],
    gift: ['送禮', ['gift', 'scent', 'hobby'], ['交換禮物', '禮物']], pet: ['毛小孩', ['pet'], []],
    '3c': ['3C 配件', ['3c', 'audio'], []], snack: ['零食宵夜', ['food'], []], sleep: ['好睡', ['bedding'], []],
    clean: ['打掃', ['clean'], []], warm: ['保暖', [], ['保暖', '暖']], camp: ['露營', ['sport'], ['露營']]
  };
  function strip() {
    var main = D.querySelector('main'); if (!main) return;
    var qs = new URLSearchParams(location.search), topic = TOPIC[qs.get('for') || ''], m = me();
    var top = Object.keys(m.c).sort(function (a, b) { return m.c[b] - m.c[a]; })[0];
    if (!topic && !(path === 'index.html' && !isOff() && (top || m.q.length))) return;
    load(function (d) {
      var r, line;
      if (topic) { r = { cats: topic[1], kw: topic[2], min: null, max: null }; line = '你是從「' + topic[0] + '」那篇來的吧？這幾件最多人買：'; addCat(topic[1][0], 1); }
      else if (top) { r = { cats: [top], kw: [], min: null, max: null }; line = '上次你在看「' + CATS[top] + '」'; }
      else { r = localParse(m.q[0], d); line = '上次你在找「' + m.q[0] + '」'; }
      var list = rank(d, r);
      if (!topic) { var deals = list.filter(function (p) { return p.d; }); if (deals.length >= 3) { list = deals; line += '，這幾件現在有打折：'; } else line += '，這幾件賣最好：'; }
      list = list.slice(0, 8); if (list.length < 3) return;
      var s = el('section', 'ybf-strip'); s.setAttribute('aria-label', '猜你在找');
      var h = el('div', 'ybf-sh'); h.appendChild(face('ybf-av')); h.appendChild(el('p', '', line));
      var b = el('button', 'ybf-ask', '跟' + NAME + '說你要什麼'); b.type = 'button'; b.addEventListener('click', function () { open(); }); h.appendChild(b);
      var row = el('div', 'ybf-row'); list.forEach(function (p) { row.appendChild(card(p, topic ? 'landing' : 'for_you')); });
      s.appendChild(h); s.appendChild(row); main.insertBefore(s, main.firstChild);
      ev('finder_strip', { mode: topic ? 'landing' : 'for_you' });
    });
  }

  // ---------- 記錄瀏覽（只存在這台裝置） ----------
  function track() {
    var cat = D.body.dataset.cat; if (cat) addCat(cat, 1);
    if (path === 'product.html') {
      var f = function () { var id = location.hash.slice(1); if (!id) return; load(function (d) { for (var i = 0; i < d.length; i++) if (d[i].i === id) { addCat(d[i].c, 2); addSeen(id); break; } }); };
      f(); window.addEventListener('hashchange', f);
    }
    var q = D.getElementById('q'), tq;
    if (q) q.addEventListener('input', function () { clearTimeout(tq); tq = setTimeout(function () { addQ(q.value); }, 1500); });
  }

  function init() {
    track();
    strip();
    var qs = new URLSearchParams(location.search), q0 = (qs.get('q') || '').slice(0, 60);
    if (!NOBTN) {
      btn = el('button', 'ybf-btn'); btn.type = 'button'; btn.setAttribute('aria-label', '問' + NAME + '：幫你找東西'); btn.setAttribute('aria-controls', 'ybf'); btn.setAttribute('aria-expanded', 'false');
      btn.appendChild(face('ybf-face')); btn.appendChild(el('span', 'ybf-lbl', '找東西'));
      btn.addEventListener('click', function () { if (panel && !panel.hidden) close(); else open(); });
      D.body.appendChild(btn);
      var greeted = false; try { greeted = sessionStorage.getItem('ybf_hi'); } catch (e) {}
      if (!greeted && !q0) setTimeout(function () {
        if (panel && !panel.hidden) return;
        var tip = el('button', 'ybf-tip', '喵，要找什麼？跟我說一句話就好'); tip.type = 'button'; tip.addEventListener('click', function () { tip.remove(); open(); });
        D.body.appendChild(tip); setTimeout(function () { tip.remove(); }, 7000);
        try { sessionStorage.setItem('ybf_hi', '1'); } catch (e) {}
      }, 3500);
    }
    if (q0) open(q0);
    window.ybFinder = { open: open };
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', init); else init();
})();
