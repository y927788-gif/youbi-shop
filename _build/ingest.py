"""Merge Shopee affiliate harvests into the accumulating master catalog (data/master.json).

Inputs (any number, any order):
  批量商品連結*.csv   - the affiliate back-office "批量取得連結" export: item id, name, price, sold, shop, commission,
                        product link (has the shop id) and the affiliate short link (Sub_id1=web)
  youbi_harvest_*.json - cards scraped from the same offer pages: image hash, discount, list tag
Products are never deleted: each run updates price/sold/link and keeps first_seen, so the site keeps growing.
usage: python3 ingest.py <files...>
"""
import csv, json, os, sys, datetime, re

MASTER = 'data/master.json'
GENERAL_TABS = {'全部', '分潤加碼', '熱銷商品', '居家生活', '男生包包與配件', '美食、伴手禮', '家電影音', '男女鞋'}
today = datetime.date.today().isoformat()
master = json.load(open(MASTER, encoding='utf-8')) if os.path.exists(MASTER) else {}

links, cards = {}, {}
for f in sys.argv[1:]:
    if f.endswith('.csv'):
        for r in csv.DictReader(open(f, encoding='utf-8-sig')):
            links[r['商品編號']] = r
    elif f.endswith('.json'):
        for c in json.load(open(f, encoding='utf-8')):
            prev = cards.get(c['id'])
            c['tags'] = (prev.get('tags', []) if prev else []) + [c.get('tag', '')]
            cards[c['id']] = c

new = upd = 0
for iid, r in links.items():
    c = cards.get(iid, {})
    m = re.search(r'/product/(\d+)/(\d+)', r.get('商品連結', ''))
    rec = master.get(iid) or {'id': iid, 'first_seen': today}
    if iid in master:
        upd += 1
    else:
        new += 1
    rec.update({
        'shop': m.group(1) if m else rec.get('shop', ''),
        'name': r['商品名稱'],
        'shop_name': r.get('商店名稱', ''),
        'price': r['商品價格'],
        'sold': r['銷售量'],
        'comm': r.get('分潤率', ''),
        'url': r['推廣連結'],
        'img': c.get('img') or rec.get('img', ''),
        'discount': c.get('disc') or rec.get('discount', ''),
        'tag': c.get('tag') or rec.get('tag', ''),
        'store': 'shopee',
        'last_seen': today,
    })
    try:  # price history, one point per day (for 近期最低價 / 降價雷達)
        ph = dict(rec.get('ph') or {})
        from catalog import parse_price
        ph[today] = int(round(parse_price(r['商品價格'])))
        rec['ph'] = dict(sorted(ph.items())[-120:])
    except ValueError:
        pass
    for tg in c.get('tags') or [c.get('tag') or '']:
        theme = tg.rsplit('-p', 1)[0]
        if theme and theme not in GENERAL_TABS:  # found through a theme keyword search (創意小物、交換禮物…)
            rec['themes'] = sorted(set(rec.get('themes', [])) | {theme})
    master[iid] = rec

# carry over images for legacy entries that came from the first scrape (full CDN URLs)
legacy = 'data/products.json'
if os.path.exists(legacy):
    for p in json.load(open(legacy, encoding='utf-8')):
        if p['id'] in master and not master[p['id']].get('img'):
            master[p['id']]['img'] = p['img'].rsplit('/', 1)[-1].replace('.webp', '')

# seed price history for records saved before tracking started (10/6)
for x in master.values():
    if not x.get('ph') and x.get('price'):
        try:
            x['ph'] = {x.get('last_seen') or x.get('first_seen') or today: int(round(float(str(x['price']).replace(',', ''))))}
        except ValueError:
            pass

json.dump(master, open(MASTER, 'w', encoding='utf-8'), ensure_ascii=False)
print(f'master: {len(master)} items ({new} new, {upd} updated); links in this run: {len(links)}, cards: {len(cards)}; missing image: {sum(1 for x in master.values() if not x.get("img"))}')
