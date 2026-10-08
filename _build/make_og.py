"""Make the 1200x630 social share images (og:image) for youbi-shop.com → out2/og/*.png (upload once to /og/).
python3 make_og.py   (needs out2/data/p.json from a build; product photos are fetched from the Shopee CDN)"""
import json, io, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

OUT = 'og'; os.makedirs(OUT, exist_ok=True)  # source copy; build2.py copies og/ into out2/og/
CDN = 'https://down-aws-tw.img.susercontent.com/file/'
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'; FR = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(path, size):
    for i in range(10):
        try:
            f = ImageFont.truetype(path, size, index=i)
            if 'TC' in ' '.join(f.getname()): return f
        except OSError: break
    return ImageFont.truetype(path, size)
BG, Y, INK, MUTED = (9, 9, 13), (255, 230, 0), (243, 241, 234), (170, 168, 182)
P = json.load(open('out2/data/p.json'))
withimg = [p for p in P if p.get('m')]
def top(f, n=4):
    seen, out = set(), []
    for p in sorted([p for p in withimg if f(p)], key=lambda p: -(p.get('q') or 0)):
        k = p['s'][:8]
        if k in seen: continue
        seen.add(k); out.append(p)
        if len(out) == n: break
    return out
def tags(p): return (p.get('g') or '').split(',')
def photo(p):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(CDN + p['m'], headers={'Referer': 'https://youbi-shop.com/', 'User-Agent': 'Mozilla/5.0 Chrome/129'}), timeout=30).read()
        return Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception as e:
        print('img fail', p['i'], e); return None
def wrap(d, text, f, width):
    lines, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=f) > width: lines.append(cur); cur = ch
        else: cur += ch
    if cur: lines.append(cur)
    return lines
def card(name, title, sub, prods=None, shot=None):
    im = Image.new('RGB', (1200, 630), BG); d = ImageDraw.Draw(im)
    for x in range(-200, 1400, 46): d.line([(x, 630), (x + 300, 0)], fill=(18, 18, 26), width=2)
    d.rectangle([0, 0, 1200, 8], fill=Y); d.rectangle([0, 622, 1200, 630], fill=(255, 46, 59))
    # logo hexagon
    cx, cy, r = 92, 92, 46
    hexp = [(cx + r * __import__('math').cos(a), cy + r * __import__('math').sin(a)) for a in [i * 3.14159 / 3 - 3.14159 / 6 for i in range(6)]]
    d.polygon(hexp, fill=Y); fl = font(FB, 22)
    d.text((cx, cy - 12), '今天', font=fl, fill=BG, anchor='mm'); d.text((cx, cy + 13), '買這個', font=fl, fill=BG, anchor='mm')
    d.text((156, 92), '今天買這個', font=font(FB, 38), fill=INK, anchor='lm')
    ft = font(FB, 74 if len(title) <= 6 else 60); y = 200
    for ln in wrap(d, title, ft, 540)[:2]: d.text((60, y), ln, font=ft, fill=INK); y += ft.size + 12
    d.rectangle([60, y + 6, 160, y + 14], fill=Y); y += 40
    fs = font(FR, 30)
    for ln in wrap(d, sub, fs, 540)[:4]: d.text((60, y), ln, font=fs, fill=MUTED); y += 44
    d.text((60, 572), 'youbi-shop.com', font=font(FB, 30), fill=Y, anchor='ls')
    if shot:
        s = Image.open(shot).convert('RGB'); s.thumbnail((520, 520)); x0, y0 = 1160 - s.width, (630 - s.height) // 2
        d.rectangle([x0 - 6, y0 - 6, x0 + s.width + 5, y0 + s.height + 5], fill=Y); im.paste(s, (x0, y0))
    elif prods:
        tiles = [t for t in (photo(p) for p in prods) if t][:4]
        for k, t in enumerate(tiles):
            t = t.resize((248, 248)); x0, y0 = 640 + (k % 2) * 262, 60 + (k // 2) * 262
            d.rectangle([x0 - 4, y0 - 4, x0 + 251, y0 + 251], fill=Y if k == 0 else (60, 60, 74)); im.paste(t, (x0, y0))
    im.save(f'{OUT}/{name}.jpg', quality=86, optimize=True, progressive=True); print('ok', name)

TREND = {'抖音同款', '小紅書爆款', 'IG爆紅', '爆紅', '網美'}
NEW = {'韓國新品', '日本新品', '2026新款', '聯名款', '限定版', '開箱'}
card('default', '今天，誰會被買爆？', '每天整理蝦皮、酷澎熱銷爆品：價格追蹤、社群爆紅、送禮清單，還有用真實商品當裝備的小遊戲。', top(lambda p: True))
card('index', '今天，誰會被買爆？', '蝦皮、酷澎熱銷榜每天更新，銷量就是戰力。拖曳 3D 爆品牆，點商品看詳情與歷史價格。', top(lambda p: (p.get('q') or 0) > 0))
card('trending', '社群爆紅', '抖音、小紅書、IG 上正在紅的東西，台灣哪裡買得到一次看。', top(lambda p: TREND & set(tags(p))))
card('new', '社群新品', '日韓新品、聯名款、限定版、國外直送，台灣有人在賣的新東西。', top(lambda p: NEW & set(tags(p))))
card('gifts', '送禮神器', '交換禮物、生日、聖誕禮物，依預算和對象幫你挑。', top(lambda p: p.get('c') in ('gift', 'hobby')))
card('deals', '雙11 降價雷達', '真的有在降價的熱銷品：3～7 折、30 天最低價一眼看。', top(lambda p: bool(p.get('d'))))
card('coupang', '酷澎館', '酷澎家電、廚具、美妝、寵物、文具各分類熱銷，也能直接搜尋酷澎全站。', top(lambda p: p.get('c') in ('appliance', 'kitchen')))
card('guides', '主題整理', '依生活情境整理的好物清單與各分類熱銷排行。', top(lambda p: p.get('c') in ('storage', 'clean', 'bedding', 'diy')))
card('play', '每日爆品翻牌', '每天翻一張爆品卡測運勢，還有爆品比大小、猜價格。', top(lambda p: p.get('c') in ('hobby', 'beauty')))
card('game', '買爆獸進化論', '吃下熱銷商品讓爆獸進化的街機小遊戲。', top(lambda p: p.get('c') in ('food', 'pet')))
shot = sys.argv[1] if len(sys.argv) > 1 else None
card('dungeon', '夜市地下城', '像素動作冒險：撿到的武器、防具全是真的熱銷商品，平底鍋放火、喇叭放音波。電腦手機都能玩。', top(lambda p: p.get('c') == 'kitchen'), shot=shot)
