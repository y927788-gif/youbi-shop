import re
"""Turn raw Shopee affiliate offers into the site catalog (data/products.json).

- drop placeholder listings and off-limits categories
- classify into site categories by keywords
- compute sold number for sorting, short display name
"""
import json, re, sys, glob, datetime

CATS = [  # (slug, label, keywords)  order matters: first match wins
    ('pet', '寵物', ['寵物', '貓砂', '貓咪', '狗狗', '犬', '飼料', '貓抓']),
    ('hobby', '玩具卡牌', ['卡牌', '寶可夢', '積木', '玩具', '公仔', '拼圖']),
    ('diy', '居家修繕', ['插座', '壁插', '暗盒', '地板貼', '地板漆', '防壁癌', '隔熱', '玻璃貼', '防窺', '採光板', '接線', '延長線', '電線', '五金']),
    ('scent', '香氛燈飾', ['投影燈', '夜燈', '氣氛燈', '燈串', '擴香', '香氛', '蠟燭', '薰香', '艾草']),
    ('food', '美食零食', ['零食', '餅乾', '泡芙', '海苔', '巧克力', '咖啡', '茶包', '茶葉', '果茶', '麵', '醬', '雞胸', '堅果', '肉乾', '蛋黃', '伴手禮', '蛋捲', '糖', '地瓜', '芝麻', '湯', '鴨翅', '肉包', '饅頭', '蜜餞', '胡椒', '烤肉', '咖啡膠囊', '可可', '燕麥', '果醋', '雞精', '雞腿', '牛肉', '甘栗', '黑豆', '麻花', '牛排', '牛腱', '菲力', '豬肉', '雞肉', '海鮮']),
    ('audio', '耳機音響', ['耳機', '喇叭', '音響', '音箱', '麥克風', 'KTV', '卡拉OK']),
    ('3c', '3C 周邊', ['行動電源', '充電', '鍵盤', '滑鼠', '電競', '保護貼', '鏡頭貼', '定位器', '標籤機', '網卡', 'sim', 'SIM', '傳輸線', '支架', '電腦包', '筆電']),
    ('appliance', '家電', ['除濕', '清淨', '吸塵', '掃地', '掃拖', '除螨', '除蟎', '烘鞋', '煮蛋', '氣炸', '快煮', '熱水', '攪拌', '調理機', '掛燙', '熨斗', '電暖', '風扇', '冷氣', '遙控器', '濾網', '濾芯', '濾心', '電池', '延長線', '冰箱', '洗衣機', '直髮器', '吹風', '織物', 'CD', 'DVD', '接線', '電熱']),
    ('bedding', '寢具', ['被', '床包', '枕', '床墊', '保潔墊', '床單', '毯']),
    ('kitchen', '廚房', ['鍋', '碗', '盤', '砧板', '保鮮', '便當', '餐具', '杯', '紙巾', '抹布']),
    ('clean', '清潔洗衣', ['清潔', '洗衣', '洗碗', '拖把', '海綿', '菜瓜布', '垃圾袋', '衛生紙', '除霉', '凝珠', '洗衣球']),
    ('storage', '收納居家', ['窗簾', '收納', '衣櫃', '衣櫥', '櫃', '置物', '掛勾', '掛鉤', '衣架', '壓縮袋', '巧拼', '地墊', '地毯', '磁鐵', '魔鬼氈', '無框畫', '暖暖包', '暖暖貼', '螢光棒', '縫紉', '除濕袋', '除濕包']),
    ('beauty', '美妝個清', ['口罩', '衛生棉', '護墊', '眼罩', '棉花棒', '唇膏', '洗髮', '沐浴', '保養', '化妝', '修容', '精華', '乳液', '香水', '面膜', '口紅', '防曬', '卸妝', '牙']),
    ('sport', '運動戶外', ['運動', '健身', '拳擊', '登山', '露營', '跑步', '瑜珈', '雨衣', '雨罩', '水壺']),
    ('shoes', '鞋子', ['鞋', '拖', '鞋墊', '鞋套']),
    ('bags', '包包飾品', ['耳飾', '耳環', '耳釘', '項鍊', '手鍊', '戒指', '包包', '背包', '手提包', '側背', '斜背', '托特', '腰包', '肩背', '皮夾', '短夾', '長夾', '錢包', '零錢袋', '手錶', '飾品', '購物袋']),
    ('fashion', '服飾', ['外套', '上衣', '褲', '裙', '洋裝', 'T恤', '帽T', '襪', '浴巾', '毛巾']),
    ('gift', '客製禮物', ['客製', '禮物', '馬克杯']),
]
CAT_LABEL = {s: l for s, l, _ in CATS}
CAT_LABEL['other'] = '生活雜貨'

# 日用消耗品：照樣收，但往後排（使用者 10/6：「日用雜貨品可以排在後面，找點有特色的東西」）
COMMODITY = ['衛生紙', '抽取式', '面紙', '濕紙巾', '洗衣球', '洗衣精', '洗衣凝珠', '洗衣膠囊', '洗衣粉', '柔軟精', '垃圾袋', '保鮮膜', '保鮮袋', '夾鏈袋',
             '塑膠袋', '衛生棉', '護墊', '口罩', '棉花棒', '牙刷', '牙膏', '洗碗精', '清潔劑', '漂白', '菜瓜布', '抹布', '拖把', '網卡', 'SIM', 'sim', '上網',
             '電池', '鞋墊', '襪', '內褲', '免洗', '一次性', '浴帽', '吸管', '紙杯', '紙碗', '鋁箔', '烘焙紙', '吸油紙', '膠帶', '電線', '延長線', '引磁片',
             '鐵片', '批發', '補充包', '補充瓶', '箱購', '整箱', '米', '雞蛋', '牛奶', '泡麵', '飲用水', '礦泉水',
             '洗碗', '家事皂', '馬桶', '尿布', '紙尿褲', '雨衣', '坐墊', '椅墊', '漆', '即飲', '滴濾', '入組', '清潔噴霧', '除臭', '香香袋', '除濕', '蚊', '掛勾', '收納袋', '洗手', '封條', '密封條', '牛腱', '牛排', '雞胸', '肉品', '生鮮', '冷凍', '水管', '清潔', '除菌']
# 有特色的關鍵字：往前排
FEATURE = ['創意', '造型', '療癒', '文創', '聯名', '限定', '設計', '擺件', '擺飾', '夜燈', '投影', '香氛', '蠟燭', '擴香', '公仔', '盲盒', '積木', '模型',
           '桌遊', '露營', '戶外', '智能', '黑科技', '懸浮', '磁吸', '迷你', '便攜', '復古', '手沖', '日本', '韓國', '北歐', '交換禮物', '禮物', '萬聖',
           '聖誕', '捏捏', '卡皮巴拉', '水豚', '3D', '手作', '原創', '插畫', '黑膠', '機械', '氛圍', '杜拜', '藍牙喇叭', '咖啡']


def feature_score(name, sold_n, price, themes):
    import math
    s = math.log10(sold_n + 10)  # 1 (no sales) … 7 (千萬)
    if any(k in name for k in COMMODITY):
        s *= 0.3
    if themes:
        s *= 1.5
    if any(k in name for k in FEATURE):
        s *= 1.35
    if price < 60:
        s *= 0.75
    elif 200 <= price <= 5000:
        s *= 1.12
    if sold_n < 20:
        s *= 0.55
    if '客製' in name:
        s *= 0.5
    return round(s, 3)


def bigrams(name):
    n = re.sub(r'[^\w]', '', name)[:24]
    return {n[i:i + 2] for i in range(len(n) - 1)}


def dedupe_key(short_name):
    return re.sub(r'[^\w]', '', short_name)[:12]


DROP = ['下單區', '專頁', '專用》', '截圖', '直播', '補差價', '運費', '請必須', '結帳',
        # 代購 is fine (overseas goods sold in Taiwan, user 10/6) but not 'send us a link' placeholder listings or replicas
        '客訂', '代買', '網址', '代購專區', '客製代購', '代購下單', '刷卡', '官網直購', '專櫃品質', '高仿', '原單', 'A貨', '1:1']
BAN = ['B群', '雞精', '滴雞精', '膠原蛋白', '益生菌', '維他命', '維生素', '葉黃素', '魚油', '酵素', '乳清', '代餐', 'HCA', '代謝', '膠原蛋白', '法事', '算命', '通靈', '問事', '下單專區', '鎖心', '手機本體', 'iPad', '平板電腦', '酒', '菸', '電子煙', '保健', '益生菌', '減肥', '瘦身', '醫療', '藥', '情趣', '成人用品', '黃金', '點數', '療效']


def sold_n(s):
    s = (s or '').replace(',', '').replace('+', '').strip()
    m = re.match(r'([\d.]+)\s*(萬)?', s)
    if not m:
        return 0
    v = float(m.group(1))
    return int(v * 10000) if m.group(2) else int(v)


def short(name):
    n = re.sub(r'[【\[(（][^】\])）]{0,30}[】\])）]', ' ', name)  # strip bracket promos
    n = re.sub(r'[#＃🔥✅⭐💕💗❤💛🚀🚚🎉🎁🥊👉🇹🇭🇺🇸🇮🇹🈶🔺♡◤◢★☆《》『』「」|｜]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip(' -/')
    return (n or name)[:46]


def classify(name):
    n = short(name)
    best, bi = 'other', 10 ** 9
    for slug, _, kws in CATS:
        for k in kws:
            i = n.find(k)
            if i >= 0 and i < bi:
                best, bi = slug, i
    return best


def parse_price(v):
    """'1,299' / '5.5萬' / '' -> float"""
    t = str(v).replace(',', '').replace('$', '').strip()
    if not t:
        return 0.0
    if t.endswith('萬'):
        return float(t[:-1]) * 10000
    try:
        return float(t)
    except ValueError:
        return 0.0


def price_stats(ph, price):
    """From the daily price history: days tracked, 30-day low/high, % below the 30-day high, and whether today is the 30-day low."""
    import datetime
    cut = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    recent = [v for d, v in sorted(ph.items()) if d >= cut] or [price]
    lo, hi = min(recent), max(recent)
    return {'tracked': len(ph), 'lo30': lo, 'hi30': hi,
            'drop': round((hi - price) / hi * 100) if hi > price else 0,
            'atlow': len(recent) >= 3 and price <= lo and hi > lo,
            'hist': [[d[5:], v] for d, v in sorted(ph.items())[-60:]] if len(ph) >= 2 else []}


def main(paths=None):
    """Build data/products.json from the accumulating master catalog (ingest.py). Only items with an affiliate link."""
    master = json.load(open('data/master.json', encoding='utf-8'))
    out = {}
    for r in master.values():
        name = r['name']
        if not r.get('url') or not r.get('img'):
            continue
        if any(k in name for k in DROP) or any(k in name for k in BAN):
            continue
        if '代購' in name and re.search(r'代購(費|服務|性質)|網站代購|官網代購|韓網代購|各品牌|代標|(amazon|zozotown|樂天|rakuten|mercari|煤爐|naver|coupang|淘寶)\s*代', name, re.I):
            continue  # buying-service listings, not products
        price = parse_price(r['price'])
        if price < 10:  # $1-$9 listings are variant bait; the real price is higher
            continue
        img = r['img'] if r['img'].startswith('http') else 'https://down-aws-tw.img.susercontent.com/' + r['img']
        out[r['id']] = {
            'id': r['id'], 'name': name, 'short': short(name), 'img': img,
            'price': int(round(price)), 'discount': float(r['discount']) if r.get('discount') else None,
            'sold': r.get('sold', ''), 'soldN': sold_n(r.get('sold')), 'cat': classify(name),
            'hot': False, 'url': r['url'], 'store': r.get('store', 'shopee'), 'added': r.get('first_seen', ''),
            'shop': r.get('shop', ''), 'themes': r.get('themes', []),
        }
        out[r['id']].update(price_stats(r.get('ph') or {}, int(round(price))))
    for x in out.values():
        x['score'] = feature_score(x['name'], x['soldN'], x['price'], x['themes'])
    # 4-character phrases shared by a handful of listings mark the same product sold by different shops (永恆鉛筆…);
    # phrases shared by many listings are generic (交換禮物、療癒小物) and don't count
    from collections import Counter
    def quads(name):
        n = re.sub(r'[^\w]', '', name)[:30]
        return {n[i:i + 4] for i in range(len(n) - 3)}
    qc = Counter(q for x in out.values() for q in quads(x['short']))
    items, seen, grams, used = [], set(), {}, set()
    for x in sorted(out.values(), key=lambda x: -x['score']):
  # same product listed by many sellers: keep the best one
        k = dedupe_key(x['short'])
        g = bigrams(x['short'])
        if k in seen or any(len(g & o) / max(1, len(g | o)) >= 0.6 for o in grams.get(x['cat'], [])):
            continue
        seen.add(k)
        grams.setdefault(x['cat'], []).append(g)
        items.append(x)
    json.dump(items, open('data/products.json', 'w', encoding='utf-8'), ensure_ascii=False)
    from collections import Counter
    c = Counter(i['cat'] for i in items)
    print(len(items), [(CAT_LABEL[k], v) for k, v in c.most_common()])


if __name__ == '__main__':
    main()

# ---- 網站顯示用的短名（只影響顯示，不影響分類）----
_NOISE = ['現貨秒出', '現貨速發', '現貨供應', '台灣現貨', '臺灣現貨', '台灣出貨', '台灣賣家', '台灣精選', '當天出貨', '快速出貨', '快速到貨', '24H快速寄出', '24h出貨',
          '24H出貨', '24小時出貨', '免運費', '免運', '現貨', '秒出', '臺現', '台現', '熱銷', '熱賣', '爆款推薦', '網紅爆款', '爆款', '推薦', '嚴選好物', '嚴選', '新品', '新款',
          '正品', '可開發票', '開發票', '發票', '限時', '特價', '下殺', '優惠', '促銷', '網紅', '抖音', '小紅書', 'IG爆紅', '最新', '必買', '好物', '24H', '24h', '隔日到', '限時低價', '低價', '特惠', '好物分享', '收據可報帳', '店鋪', '全新', '隔日達', '優質']
_NOISE_RE = re.compile('|'.join(sorted(map(re.escape, _NOISE), key=len, reverse=True)))


def nice(name, limit=30):
    n = re.sub(r'[【\[(（［〔《][^】\])）］〕》]{0,40}[】\])）］〕》]', ' ', name)  # 括號裡多半是促銷字或店名
    n = re.sub(r'[\U00010000-\U0010FFFF←-⇿■-➿⬀-⯿㈀-㋿️‍#＃|｜『』「」]', ' ', n)  # emoji、符號
    n = re.sub(r'\S{0,6}同款', ' ', n)  # 明星同款、張雨綺同款、抖音同款
    n = _NOISE_RE.sub(' ', n)
    n = re.sub(r'\S{0,3}出貨|\b20\d\d\b', ' ', n)  # 臺灣出貨、桃園出貨、2026
    n = re.sub(r'^[A-Za-z]{0,2}\d{1,4}(-\d+)?\s', ' ', n.strip() + ' ')  # 開頭的貨號 D05-2
    toks = [t.strip('-~:：') for t in re.split(r'[\s,，、/·•]+', n)]
    toks = [t for t in toks if len(t) >= 2]
    toks = [t for i, t in enumerate(toks) if not (len(t) <= 3 and any(t in u and t != u for u in toks[i + 1:]))]  # 開頭的「擺件」被後面的「桌上擺件」取代
    out, ends, skipped = [], set(), []
    for t in toks:
        if any(t in o for o in out):
            continue
        sub = [i for i, o in enumerate(out) if o in t]
        if sub:  # 後面的說法比較完整：「空氣炸鍋」→「110v空氣炸鍋多功能大容量」
            i = sub[0]
            rest = len(' '.join(out)) - len(out[i])
            out[i] = t[:max(len(out[i]), limit - rest)]
            continue
        if len(t) >= 3 and t[-2:] in ends:  # 室內拖鞋、EVA拖鞋…同一個品項只留第一個
            skipped.append(t)
            continue
        if out and len(' '.join(out + [t])) > limit:
            room = limit - len(' '.join(out)) - 1
            if len(' '.join(out)) < 12 and room >= 4:
                out.append(t[:room])
            break
        out.append(t[:limit])
        ends.add(t[-2:])
    for t in skipped:  # 太短時補回同品項的其他說法
        if len(' '.join(out)) >= 12:
            break
        if not any(t in o or o in t for o in out) and len(' '.join(out + [t])) <= limit:
            out.append(t)
    return ' '.join(out) or short(name)[:limit]


_JUNK = re.compile(r'(代購.{0,8}(下單|專區)|產品代購|下單專區|下單區|補差價|運費補|客製連結|私人訂單|專屬賣場)')
BAN_MORE = ['瘦臉', '刮痧', '豐胸', '壯陽', '燃脂', '排毒']


def junk(name):
    return bool(_JUNK.search(name)) or any(k in name for k in BAN_MORE)
