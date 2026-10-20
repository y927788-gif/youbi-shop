"""今天買這個 社群圖卡模板組（黃黑視覺，和 youbi-shop.com 同一套）。

用法（輸出 1080x1350 PNG，IG 4:5；X、Threads 同一張可用）：
  python3 kit.py rank  --cat kitchen --title "廚房類賣最多的 5 樣" [--sub "..."] [--out x.png]
  python3 kit.py rank  --tag 抖音同款 --title "抖音紅到台灣的 5 樣"
  python3 kit.py deal  --id 23326215796 [--hook "..."]                 降價雷達（單品）
  python3 kit.py guess --id 22859508855                                 猜銷量（輸出 _q.png 題目、_a.png 答案，做輪播）
  python3 kit.py vs    --a "洗完馬上收" --b "晾到下次再用" --q "碗盤洗完你是哪一派？"
  python3 kit.py list  --title "租屋族最後悔沒早買的 3 樣" --items "除濕盒｜梅雨季衣櫃不再發霉" "伸縮桿｜..." "..."
  python3 kit.py trend --tag 小紅書爆款 --title "小紅書爆款，台灣買得到的 4 樣"
  python3 kit.py power --id 23326215796 --hook "一句有梗的開頭"           今日爆品（推薦文配圖）
  python3 kit.py game  --shot 截圖.png --title "平底鍋會噴火的地下城" --sub "..."
共同參數：--out 檔名、--date M/D（預設今天，台灣時間）
資料：預設讀 https://youbi-shop.com/data/p.json（網站每天更新的熱銷資料），或 --data 本機檔案。
規則：圖裡不放連結網址（只放 youbi-shop.com 品牌字）；價格、銷量一律用資料裡的數字，不改不編。
"""
import argparse, datetime, io, json, math, os, re, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
FR = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
NUMF = os.path.join(HERE, 'Anton-Regular.ttf')
BG, PANEL, PANEL2 = (9, 9, 13), (20, 20, 30), (30, 30, 42)
Y, INK, MUTED, RED, CYAN = (255, 230, 0), (243, 241, 234), (160, 158, 172), (255, 46, 59), (60, 240, 255)
CDN = 'https://down-aws-tw.img.susercontent.com/file/'
_fc = {}


def font(path, size):
    k = (path, size)
    if k in _fc: return _fc[k]
    f = None
    if path.endswith('.ttc'):
        for i in range(10):
            try:
                g = ImageFont.truetype(path, size, index=i)
                if 'TC' in ' '.join(g.getname()): f = g; break
            except OSError: break
    if f is None:
        try: f = ImageFont.truetype(path, size)
        except OSError: f = ImageFont.truetype(FB, size)
    _fc[k] = f; return f


def num(size): return font(NUMF if os.path.exists(NUMF) else FB, size)


def today(): return (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%-m/%-d')


# ---------------- data ----------------
def load(path=None):
    if path: return json.load(open(path, encoding='utf-8'))
    req = urllib.request.Request('https://youbi-shop.com/data/p.json', headers={'User-Agent': 'Mozilla/5.0'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def photo(p, size):
    cache = os.path.join('/tmp', 'ybimg_' + p['m'] + '.jpg')
    try:
        if not os.path.exists(cache):
            raw = urllib.request.urlopen(urllib.request.Request(CDN + p['m'], headers={'Referer': 'https://youbi-shop.com/', 'User-Agent': 'Mozilla/5.0 Chrome/129'}), timeout=30).read()
            open(cache, 'wb').write(raw)
        im = Image.open(cache).convert('RGB')
    except Exception as e:
        print('photo fail', p.get('i'), e, file=sys.stderr)
        im = Image.new('RGB', (size, size), PANEL2)
    s = min(im.size); im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width - s) // 2 + s, (im.height - s) // 2 + s))
    return im.resize((size, size), Image.LANCZOS)


NOISE = r'(台灣公司|獨家|下殺\d*元?|大牌|全台|[Cc][Pp]值最高|[Cc][Pp]值|超值|必買|好評|熱賣|檢驗合格|最快隔日到|隔日到貨|隔日到|臺灣現貨|台灣現貨|實拍|官方正品|現貨|免運|快速出貨|台灣出貨|發票|隔日配|當天出貨|24H|24h|開發票|附發票|官方|正品|保固|蝦皮代開|熱銷|爆款|限時|特價|促銷|新品|最新|2026|2025|NCC|BSMI|認證|台灣現貨|免運費)'


def short(s, n=14):
    """Turn a keyword-stuffed listing title into a readable short name."""
    s = re.sub(r'[【\[\(（「『<〔][^】\]\)）」』>〕]{0,30}[】\]\)）」』>〕]', ' ', s)
    s = re.sub(r'[^\w一-鿿぀-ヿ\s\-+.x×]', ' ', s)
    s = re.sub(NOISE, ' ', s)
    out = ''
    for t in s.split():
        if t in out: continue
        if len(out) + len(t) > n and out: break
        out += (' ' if out and re.match(r'[A-Za-z0-9]', t[0]) and re.match(r'[A-Za-z0-9]', out[-1]) else '') + t
    return (out or s.strip())[:n + 4]


def sold_txt(p): return p.get('sold') or ('—' if not p.get('q') else f"{p['q']:,}+")


EXCLUDE = set()
# 標題提到知名角色、品牌角色或名人的商品自動排除（圖片多半有版權角色）；照片仍要人工再看一次
IPRE = re.compile(r'麵包超人|kitty|凱蒂貓|三麗鷗|sanrio|史努比|snoopy|皮卡丘|寶可夢|pokemon|迪士尼|disney|漫威|marvel|蠟筆小新|哆啦|小叮噹|拉拉熊|吉伊卡哇|chiikawa|蛋黃哥|米奇|米妮|小小兵|海綿寶寶|美樂蒂|酷洛米|大耳狗|line ?friends|熊大|兔兔|角落生物|卡比|瑪利歐|馬力歐|鬼滅|航海王|海賊王|七龍珠|名偵探|柯南|蜘蛛人|冰雪奇緣|艾莎|玩具總動員|小熊維尼|維尼|史迪奇|小楊哥|明星同款|周杰倫|聯名', re.I)


def pick(P, cat=None, tag=None, n=5, ids=None):
    if ids: m = {p['i']: p for p in P}; return [m[i] for i in ids if i in m]
    L = [p for p in P if p.get('m') and p['i'] not in EXCLUDE and not IPRE.search(p['s']) and (not cat or p['c'] == cat) and (not tag or tag in (p.get('g') or '').split(','))]
    L.sort(key=lambda p: (-(p.get('q') or 0), -(p.get('n') or 0)))
    seen, out = [], []
    for p in L:
        k = short(p['s'], 6)
        if k in seen: continue
        if clutter(p) > CLUTTER_MAX: print('skip cluttered photo', p['i'], short(p['s']), file=sys.stderr); continue
        seen.append(k); out.append(p)
        if len(out) == n: break
    return out


CLUTTER_MAX = 38  # 商品圖邊緣密度上限：文字、拼貼很多的賣場圖（>38）放進圖卡會很亂，自動跳過


def clutter(p):
    """0～100，越高代表照片上的字和拼貼越多（以 256px 灰階邊緣平均值估算）。"""
    from PIL import ImageStat
    return ImageStat.Stat(photo(p, 256).convert('L').filter(ImageFilter.FIND_EDGES)).mean[0]


# ---------------- drawing helpers ----------------
def wrap(d, text, f, width, nmax=9):
    out, cur = [], ''
    for ch in text:
        if ch == '\n': out.append(cur); cur = ''; continue
        if d.textlength(cur + ch, font=f) > width: out.append(cur); cur = ch
        else: cur += ch
    if cur: out.append(cur)
    if len(out) > nmax: out = out[:nmax]; out[-1] = out[-1][:-1] + '…'
    return out


def hexlogo(d, cx, cy, r):
    d.polygon([(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [i * math.pi / 3 - math.pi / 6 for i in range(6)]], fill=Y)
    f = font(FB, int(r * .48)); d.text((cx, cy - r * .27), '今天', font=f, fill=BG, anchor='mm'); d.text((cx, cy + r * .27), '買這個', font=f, fill=BG, anchor='mm')


def base(kick, w=W, h=H, date=None):
    im = Image.new('RGB', (w, h), BG); d = ImageDraw.Draw(im)
    for x in range(-h, w + 200, 54): d.line([(x, h), (x + h * .37, 0)], fill=(16, 16, 24), width=3)
    d.rectangle([0, 0, w, 10], fill=Y)
    hexlogo(d, 92, 96, 44)
    d.text((152, 96), '今天買這個', font=font(FB, 40), fill=INK, anchor='lm')
    if kick:
        fk = font(FB, 30); tw = d.textlength(kick, font=fk)
        d.rectangle([w - 60 - tw - 36, 70, w - 60, 122], fill=Y); d.text((w - 60 - 18, 96), kick, font=fk, fill=BG, anchor='rm')
    return im, d


def footer(d, left, w=W, h=H):
    d.rectangle([0, h - 80, w, h], fill=Y)
    d.text((60, h - 40), left, font=font(FB, 30), fill=BG, anchor='lm')
    d.text((w - 60, h - 40), 'youbi-shop.com', font=font(FB, 30), fill=BG, anchor='rm')


def framed(im, ph, x, y, col=Y, bw=6, glow=False):
    d = ImageDraw.Draw(im)
    if glow:
        g = Image.new('RGBA', im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.rectangle([x - 14, y - 14, x + ph.width + 13, y + ph.height + 13], outline=col + (255,), width=16)
        g = g.filter(ImageFilter.GaussianBlur(18)); im.paste(g, (0, 0), g)
    d.rectangle([x - bw, y - bw, x + ph.width + bw - 1, y + ph.height + bw - 1], fill=col); im.paste(ph, (x, y))


def title_block(d, title, sub, y=170, size=66, w=W):
    ft = font(FB, size)
    for ln in wrap(d, title, ft, w - 120, 2): d.text((60, y), ln, font=ft, fill=INK); y += int(size * 1.22)
    d.rectangle([60, y + 8, 170, y + 18], fill=Y); y += 40
    if sub:
        fs = font(FR, 32)
        for ln in wrap(d, sub, fs, w - 120, 2): d.text((60, y), ln, font=fs, fill=MUTED); y += 46
    return y


def price(p): return f"NT${p['p']:,}"


# ---------------- templates ----------------
def rank(P, a):
    items = pick(P, a.cat, a.tag, 5, a.ids)
    im, d = base(f'{a.date} 熱銷排行')
    y0 = title_block(d, a.title, a.sub or '依實際銷量整理・今天買這個每天更新', 160) + 6
    rowh = min(176, (H - 100 - y0) // max(1, len(items)))
    for k, p in enumerate(items):
        y = y0 + k * rowh; top1 = k == 0
        d.rectangle([40, y, W - 40, y + rowh - 14], fill=PANEL if not top1 else (34, 30, 6))
        if top1: d.rectangle([40, y, 50, y + rowh - 14], fill=Y)
        d.text((112, y + (rowh - 14) // 2), str(k + 1), font=num(96), fill=Y if top1 else INK, anchor='mm')
        s = rowh - 40; ph = photo(p, s); framed(im, ph, 186, y + 13, Y if top1 else PANEL2, 4)
        x = 186 + s + 32
        fn = font(FB, 38)
        for j, ln in enumerate(wrap(d, a.names.get(p['i']) or short(p['s']), fn, W - 80 - x, 1)): d.text((x, y + 22), ln, font=fn, fill=INK)
        d.text((x, y + rowh - 40), price(p), font=font(FB, 40), fill=Y, anchor='ls')
        d.text((W - 70, y + rowh - 40), '已售 ' + sold_txt(p), font=font(FR, 32), fill=MUTED, anchor='rs')
    footer(d, '你買過哪一個？留言 👇'.replace(' 👇', ''))
    return [im]


def deal(P, a):
    p = pick(P, ids=[a.id])[0]
    if clutter(p) > CLUTTER_MAX: print(f'警告：這件商品的照片很雜（{clutter(p):.0f} > {CLUTTER_MAX}），建議換一件', file=sys.stderr)
    im, d = base(f'{a.date} 降價雷達')
    ph = photo(p, 560); framed(im, ph, 60, 180, Y, 8, True)
    try: off = float(p.get('d') or 0)
    except ValueError: off = 0
    # discount badge
    cx, cy = 790, 330
    d.ellipse([cx - 170, cy - 170, cx + 170, cy + 170], fill=RED)
    if off: d.text((cx, cy - 10), f'{off:g}', font=num(170), fill=INK, anchor='mm'); d.text((cx, cy + 105), '折', font=font(FB, 56), fill=INK, anchor='mm')
    else: d.text((cx, cy), '好價', font=font(FB, 96), fill=INK, anchor='mm')
    if off:
        orig = round(p['p'] / (off / 10))
        d.text((700, 580), f'原價約 NT${orig:,}', font=font(FR, 34), fill=MUTED, anchor='lm'); tl = d.textlength(f'原價約 NT${orig:,}', font=font(FR, 34))
        d.line([(700, 582), (700 + tl, 582)], fill=MUTED, width=3)
    d.text((700, 680), price(p), font=font(FB, 76), fill=Y, anchor='lm')
    y = 800; fh = font(FB, 58)
    for ln in wrap(d, a.hook or (a.names.get(p['i']) or short(p['s'], 18)) + ' 正在特價', fh, W - 120, 2): d.text((60, y), ln, font=fh, fill=INK); y += 74
    fn = font(FR, 32)
    if a.hook:
        for ln in wrap(d, a.names.get(p['i']) or short(p['s'], 20), fn, W - 120, 1): d.text((60, y + 8), ln, font=fn, fill=MUTED); y += 48
    stats = [('現在', price(p)), ('已售', sold_txt(p)), ('折數', f'{off:g} 折' if off else '—')]
    for k, (t, v) in enumerate(stats):
        x0 = 60 + k * 330; d.rectangle([x0, 1100, x0 + 300, 1220], fill=PANEL)
        d.text((x0 + 22, 1118), t, font=font(FR, 26), fill=MUTED); d.text((x0 + 22, 1152), v, font=font(FB, 44), fill=Y if k == 0 else INK)
    footer(d, f'價格以 {a.date} 商品頁為準，隨時會變')
    return [im]


def guess(P, a):
    p = pick(P, ids=[a.id])[0]; nm = a.names.get(p['i']) or short(p['s'], 16)
    if clutter(p) > CLUTTER_MAX: print(f'警告：這件商品的照片很雜（{clutter(p):.0f} > {CLUTTER_MAX}），建議換一件', file=sys.stderr)
    out = []
    for ans in (False, True):
        im, d = base('猜猜看' if not ans else '公布答案')
        ph = photo(p, 640); framed(im, ph, (W - 640) // 2, 170, Y, 8, ans)
        fn = font(FB, 50); d.text((W // 2, 880), nm, font=fn, fill=INK, anchor='mm')
        d.text((W // 2, 950), price(p), font=font(FB, 44), fill=Y, anchor='mm')
        if not ans:
            d.text((W // 2, 1060), a.hook or '你猜它已經賣出幾個？', font=font(FB, 54), fill=INK, anchor='mm')
            for k, opt in enumerate(['A. 500 個', 'B. 5,000 個', 'C. 5 萬個'] if not a.opts else a.opts):
                x0 = 60 + k * 330; d.rectangle([x0, 1130, x0 + 300, 1230], fill=PANEL)
                d.text((x0 + 150, 1180), opt, font=font(FB, 38), fill=INK, anchor='mm')
            footer(d, '留言你的答案，下一張公布')
        else:
            d.rectangle([140, 1010, W - 140, 1220], fill=Y)
            d.text((W // 2, 1060), '已經賣出', font=font(FB, 40), fill=BG, anchor='mm')
            d.text((W // 2, 1150), sold_txt(p), font=font(FB, 100), fill=BG, anchor='mm')
            footer(d, f'銷量以 {a.date} 商品頁為準')
        out.append(im)
    return out


def vs(P, a):
    im, d = base('二選一')
    d.polygon([(0, 180), (W, 180), (W, 560), (0, 760)], fill=Y)
    fa = font(FB, 110 if len(a.a) <= 6 else 84); fb = font(FB, 110 if len(a.b) <= 6 else 84)
    d.text((W // 2, 380), a.a, font=fa, fill=BG, anchor='mm')
    d.ellipse([440, 620, 640, 820], fill=RED); d.text((W // 2, 718), 'VS', font=num(110), fill=INK, anchor='mm')
    d.text((W // 2, 960), a.b, font=fb, fill=Y, anchor='mm')
    d.text((W // 2, 1120), a.q, font=font(FB, 48), fill=INK, anchor='mm')
    d.text((W // 2, 1190), '留言 A 或 B，看看哪一派人多', font=font(FR, 34), fill=MUTED, anchor='mm')
    footer(d, '今天買這個・二選一')
    return [im]


def lst(P, a):
    im, d = base(a.kick or '清單')
    y = title_block(d, a.title, a.sub, 170, 70) + 20
    n = len(a.items); rowh = min(240, (H - 110 - y) // max(1, n))
    for k, it in enumerate(a.items):
        head, _, body = it.partition('｜')
        yy = y + k * rowh; d.rectangle([60, yy, W - 60, yy + rowh - 22], fill=PANEL)
        d.rectangle([60, yy, 150, yy + rowh - 22], fill=Y); d.text((105, yy + (rowh - 22) // 2), str(k + 1), font=num(80), fill=BG, anchor='mm')
        d.text((182, yy + 26), head, font=font(FB, 46), fill=INK)
        fb_ = font(FR, 32)
        for j, ln in enumerate(wrap(d, body, fb_, W - 60 - 182 - 30, 2)): d.text((182, yy + 92 + j * 44), ln, font=fb_, fill=MUTED)
    footer(d, a.foot or '收藏起來，下次買之前看')
    return [im]


def trend(P, a):
    items = pick(P, a.cat, a.tag, 4, a.ids)
    im, d = base(f'{a.date} 社群爆紅')
    y0 = title_block(d, a.title, a.sub or f'#{a.tag} 熱門款，台灣買得到的幫你整理好了' if a.tag else a.sub, 160) + 10
    s = min(440, (H - 90 - y0 - 2 * 116) // 2); gx = (W - 2 * s - 80) // 2
    for k, p in enumerate(items):
        x0, yy = gx + (k % 2) * (s + 80), y0 + (k // 2) * (s + 116)
        framed(im, photo(p, s), x0 + 10, yy, Y if k == 0 else PANEL2, 5)
        d.text((x0 + 10, yy + s + 18), (a.names.get(p['i']) or short(p['s'], 11)), font=font(FB, 34), fill=INK)
        d.text((x0 + 10, yy + s + 66), price(p) + '・已售 ' + sold_txt(p), font=font(FR, 28), fill=MUTED)
    footer(d, '你最想要哪一個？')
    return [im]


TIER = [(1e6, CYAN, 'UR'), (3e5, (255, 200, 61), 'SSR'), (5e4, (199, 125, 255), 'SR'), (1e4, (77, 163, 255), 'R'), (0, (154, 154, 170), 'N')]


def power(P, a):
    p = pick(P, ids=[a.id])[0]
    if clutter(p) > CLUTTER_MAX: print(f'警告：這件商品的照片很雜（{clutter(p):.0f} > {CLUTTER_MAX}），建議換一件', file=sys.stderr)
    tc, tn = next((c, n) for q, c, n in TIER if (p.get('q') or 0) >= q)
    im, d = base(f'{a.date} 今日爆品')
    ph = photo(p, 640); framed(im, ph, (W - 640) // 2, 180, tc, 10, True)
    d.rectangle([(W - 640) // 2 - 10, 170, (W - 640) // 2 + 150, 240], fill=tc); d.text(((W - 640) // 2 + 70, 205), tn, font=num(56), fill=BG, anchor='mm')
    y = 870; fh = font(FB, 56)
    for ln in wrap(d, a.hook or short(p['s'], 20), fh, W - 120, 2): d.text((60, y), ln, font=fh, fill=INK); y += 72
    d.text((60, y + 8), a.names.get(p['i']) or short(p['s'], 28), font=font(FR, 32), fill=MUTED)
    stats = [('價格', price(p)), ('已售', sold_txt(p)), ('戰力', tn)]
    for k, (t, v) in enumerate(stats):
        x0 = 60 + k * 330; d.rectangle([x0, 1120, x0 + 300, 1235], fill=PANEL)
        d.text((x0 + 22, 1136), t, font=font(FR, 26), fill=MUTED); d.text((x0 + 22, 1170), v, font=font(FB, 44), fill=Y if k == 0 else INK)
    footer(d, '連結在留言／簡介（含推廣連結）')
    return [im]


def game(P, a):
    im, d = base('夜市地下城')
    y = title_block(d, a.title, a.sub, 160, 70)
    s = Image.open(a.shot).convert('RGB'); bw, bh = W - 140, H - 120 - y - 40
    r = min(bw / s.width, bh / s.height); s = s.resize((int(s.width * r), int(s.height * r)), Image.NEAREST if r >= 2 else Image.LANCZOS)
    s2 = Image.open(a.shot).convert('RGB'); bh2 = min(bh, 640); r = min(bw / s2.width, bh2 / s2.height)
    s = s2.resize((int(s2.width * r), int(s2.height * r)), Image.NEAREST if r >= 2 else Image.LANCZOS)
    x0 = (W - s.width) // 2; framed(im, s, x0, y + 10, Y, 8, True)
    chips = a.items or ['真商品當裝備', '8 種武器技能', '每日簽到送幣']
    cy = y + 10 + s.height + 50; cw = (W - 120 - 20 * (len(chips) - 1)) // len(chips)
    for k, c in enumerate(chips[:3]):
        x = 60 + k * (cw + 20); d.rectangle([x, cy, x + cw, cy + 96], fill=PANEL, outline=Y, width=3)
        d.text((x + cw // 2, cy + 48), c, font=font(FB, 34), fill=INK, anchor='mm')
    footer(d, '免費玩・電腦手機都能玩')
    return [im]


T = {'rank': rank, 'deal': deal, 'guess': guess, 'vs': vs, 'list': lst, 'trend': trend, 'power': power, 'game': game}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('kind', choices=T)
    for k in ['cat', 'tag', 'title', 'sub', 'id', 'hook', 'a', 'b', 'q', 'shot', 'kick', 'foot', 'data', 'out']: ap.add_argument('--' + k)
    ap.add_argument('--ids', nargs='*'); ap.add_argument('--items', nargs='*', default=[]); ap.add_argument('--opts', nargs='*')
    ap.add_argument('--exclude', nargs='*', default=[], help='排除的商品ID（照片有卡通角色、品牌商標、不適合的商品）')
    ap.add_argument('--clutter', type=float, default=None, help='照片雜亂度上限（預設 38）')
    ap.add_argument('--name', action='append', default=[], help='商品短名覆寫：--name 商品ID=短名（可重複）')
    ap.add_argument('--date', default=today())
    a = ap.parse_args(argv)
    a.names = dict(x.split('=', 1) for x in a.name); EXCLUDE.update(a.exclude)
    global CLUTTER_MAX
    if a.clutter: CLUTTER_MAX = a.clutter
    P = load(a.data) if a.kind not in ('vs', 'list', 'game') else []
    ims = T[a.kind](P, a)
    out = a.out or f'card_{a.kind}.png'
    paths = [out] if len(ims) == 1 else [out.replace('.png', f'_{s}.png') for s in ('q', 'a')]
    for im, pth in zip(ims, paths): im.save(pth, optimize=True); print('saved', pth)
    return paths


if __name__ == '__main__': main()
