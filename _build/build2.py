"""今天買這個 v2 — youbi-shop.com static site.

Inputs : data/products.json (catalog.py), data/reels.json (ids with vid/<id>.mp4), data/guides.json + data/picks.json (topic guides)
Output : out2/  — index.html, c/<slug>.html, product.html (#id), guides/<slug>.html, about.html, disclosure.html, 404.html,
         data/p.json (compact catalog for the browser), img/, vid/, sitemap.xml, robots.txt, CNAME
Usage  : python3 build2.py [--limit N]   (limit trims the catalog for previews)
"""
import json, html, os, shutil, sys, datetime, itertools
sys.path.insert(0, '.')
from catalog import CAT_LABEL, CATS

BASE = 'https://youbi-shop.com/'
SITE = '今天買這個'
OUT = os.environ.get('YB_OUT', 'out2')  # 本機測試可以另外建一份（例：YB_OUT=out3）
PROD = '--prod' in sys.argv  # production: images hotlinked from the shop CDN, no img/ folder
CDN = 'https://down-aws-tw.img.susercontent.com/file/'
LIMIT = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
GA_ID = 'G-57HK1REXVR'  # GA4 property youbi-shop.com (account 今天買這個)
TODAY = datetime.date.today()
VER = datetime.datetime.now().strftime('%m%d%H%M')
e = html.escape
# ---- game shop (夜市地下城 造型商城). Empty SHOP_API = 金燈籠儲值/帳號關閉，只開放夜市幣造型。上線步驟見 _build/server/README.md ----
SHOP_API = os.environ.get('YB_SHOP_API', 'https://youbi-shop-api.y927788.workers.dev')  # Cloudflare Worker URL (env override only for local tests), e.g. https://youbi-shop-api.<subdomain>.workers.dev
GOOGLE_CLIENT_ID = '583244121695-3sr83o3tmvml020ajs6q84tv48ol5tl9.apps.googleusercontent.com'  # optional Google sign-in (OAuth client ID)
SHOP_OWNER = '玖悠谷國際企業社'        # 營運者（個人姓名或行號名稱），儲值開放前要填
SHOP_CONTACT = 'kunoya.store@gmail.com'      # 客服信箱，儲值開放前要填
GAME_RATING = '輔導十五歲級'  # 10/7 使用者同意放寬；有血花（可關）與恐怖場景，不做殘虐畫面
CP_TRACK = 'AF7017986'  # Coupang Partners tracking code (今天買這個)
CP_SEARCH = 'https://coupa.ng/cpXDzB'  # official Coupang Partners search-bar widget
CP_W = [('1912', '家電數碼'), ('1913', '玩具愛好'), ('1914', '廚具'), ('1915', '居家生活'), ('1916', '美食'), ('1917', '美妝'), ('1918', '運動休閒'), ('1919', '寵物'), ('1920', '文具辦公')]  # 「分類最佳」dynamic widgets
CP_FOR_CAT = {'3c': '1912', 'audio': '1912', 'appliance': '1912', 'hobby': '1913', 'gift': '1913', 'kitchen': '1914', 'storage': '1915', 'bedding': '1915', 'scent': '1915', 'clean': '1915', 'diy': '1915',
              'food': '1916', 'beauty': '1917', 'sport': '1918', 'shoes': '1918', 'fashion': '1918', 'bags': '1918', 'pet': '1919', 'other': '1920'}
NEW_GROUPS = {'社群爆款': ['抖音同款', '小紅書爆款', 'IG爆紅', '爆紅', '網美', '開箱'],
              '新品聯名': ['韓國新品', '日本新品', '2026新款', '聯名款', '限定版'],
              '國外直送': ['韓國代購', '日本代購', '美國代購', '泰國代購', '歐美', '日本進口', '韓國進口']}
NEW_ALL = [t for g in NEW_GROUPS.values() for t in g]
PRIVATE_SRC = {'dungeon.js'}  # 原始碼只放私人倉庫 y927788-gif/youbi-shop-src
ASSET_SRC = ['hero3d.js', 'play.js', 'gifts.js', 'deals.js', 'game.js', 'newin.js', 'dungeon.js', 'finder.js']  # hand-written page scripts (kept in _build/assets_src/)

products = json.load(open('data/products.json', encoding='utf-8'))
# 通路王等品牌官網商品（手動核對、不經蝦皮資料流程），檔案在 repo 的 _build/data/brands.json
if not os.path.exists('data/brands.json'):
    try:
        import urllib.request
        urllib.request.urlretrieve('https://raw.githubusercontent.com/y927788-gif/youbi-shop/main/_build/data/brands.json', 'data/brands.json')
    except Exception as _e:
        print('no brands.json', _e)
if os.path.exists('data/brands.json'):
    _have = {p['id'] for p in products}
    products += [b for b in json.load(open('data/brands.json', encoding='utf-8')) if b['id'] not in _have]
# 顯示用短名：去掉「現貨、免運、24H、同款」之類的字和重複關鍵字；代購佔位賣場、違規類商品不上架
from catalog import nice as _nice, junk as _junk
products = [p for p in products if p.get('shop_name') or not _junk(p['name'])]
for _p in products:
    if not _p.get('shop_name'):
        _p['short'] = _nice(_p['name'])
if LIMIT:
    products = products[:LIMIT]
# production: the reel videos already live in the repo's vid/ folder, so trust data/reels.json
reels = [r for r in (json.load(open('data/reels.json')) if os.path.exists('data/reels.json') else [f[:-4] for f in sorted(os.listdir('vid'))]) if PROD or os.path.exists(f'vid/{r}.mp4')]
have = {p['id'] for p in products}
reels = [r for r in reels if r in have]
byid = {p['id']: p for p in products}
guides = json.load(open('data/guides.json', encoding='utf-8'))
picks = json.load(open('data/picks.json', encoding='utf-8'))
quests = json.load(open('data/quests.json', encoding='utf-8')) if os.path.exists('data/quests.json') else []
cats = [(s, CAT_LABEL[s]) for s, _, _ in CATS] + [('other', CAT_LABEL['other'])]
counts = {s: sum(1 for p in products if p['cat'] == s) for s, _ in cats}
cats = sorted([c for c in cats if counts[c[0]]], key=lambda c: -counts[c[0]])

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Chakra+Petch:wght@600;700&family=Noto+Serif+TC:wght@900&display=swap">'

CSS = r"""
/* 中二 battle-HUD: night arena, manga-serif titles, rarity frames. Loud parts: rarity + price plate. */
:root{color-scheme:dark;--bg:#09090D;--panel:#13131B;--panel2:#1B1B26;--line:#2A2A38;--ink:#F3F1EA;--muted:#9B98A8;--pop:#FFE600;--red:#FF2E3B;--cyan:#3CF0FF;--ssr:#FFC83D;--sr:#C77DFF;--r:#4DA3FF;
--disp:"Noto Serif TC","Songti TC","PMingLiU",serif;--body:"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;--num:"Anton","Impact",sans-serif;--hud:"Chakra Petch","Anton",sans-serif;
--cut:polygon(0 0,calc(100% - 14px) 0,100% 14px,100% 100%,14px 100%,0 calc(100% - 14px))}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6;
background-image:radial-gradient(rgba(255,255,255,.045) 1px,transparent 1.2px),linear-gradient(115deg,transparent 0 62%,rgba(255,46,59,.07) 62% 63%,transparent 63% 71%,rgba(255,230,0,.05) 71% 71.6%,transparent 71.6%);background-size:6px 6px,100% 100vh;background-attachment:fixed}
a{color:inherit}img,video{max-width:100%;display:block}
.w{max-width:1240px;margin:0 auto;padding-inline:16px}
.kick{display:block;font:700 .78rem/1 var(--hud);letter-spacing:.32em;color:var(--red);margin-bottom:8px;text-transform:uppercase}
/* header */
.hd{position:sticky;top:0;z-index:20;background:rgba(9,9,13,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.hd::after{content:"";position:absolute;left:0;right:0;bottom:-2px;height:2px;background:linear-gradient(90deg,var(--red),var(--pop) 40%,transparent 70%)}
.hd .w{display:flex;align-items:center;gap:14px;min-height:64px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;flex:none}
.logo b{width:42px;height:42px;background:var(--pop);clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%);display:grid;place-items:center;font:900 .7rem/1.05 var(--disp);text-align:center;color:#09090D}
.logo span{font:900 1.2rem var(--disp);letter-spacing:.06em}
.sbox{flex:1;position:relative;max-width:560px}
.sbox input{width:100%;min-height:44px;border:1px solid var(--line);border-radius:4px;background:var(--panel);color:var(--ink);font:inherit;padding:0 16px;clip-path:var(--cut)}
.sbox input::placeholder{color:var(--muted)}
.sbox input:focus-visible{outline:2px solid var(--pop);outline-offset:2px}
.sres{position:absolute;left:0;right:0;top:50px;background:var(--panel);border:1px solid var(--pop);max-height:70vh;overflow:auto;display:none}
.sres.on{display:block}.sres a{display:flex;gap:10px;align-items:center;padding:8px 12px;text-decoration:none;border-bottom:1px solid var(--line)}
.sres a:hover{background:var(--panel2)}
.sres img{width:44px;height:44px;object-fit:cover}.sres .sp{margin-left:auto;font:1.05rem var(--num);color:var(--pop)}
.nav{display:flex;gap:2px}.nav a{text-decoration:none;font:700 .95rem var(--body);padding:8px 12px;color:var(--muted)}
.nav a:hover{color:var(--ink)}.nav a[aria-current="page"]{color:var(--pop);box-shadow:inset 0 -2px var(--pop)}
@media (max-width:1100px){.nav a{padding:8px 8px;font-size:.9rem}}
@media (max-width:900px){.hd .w{flex-wrap:wrap;padding-block:8px;gap:8px 14px}.sbox{order:2;flex:1 1 200px}.nav{order:3;flex-basis:100%;overflow-x:auto;scrollbar-width:none;margin-inline:-16px;padding-inline:10px}.nav::-webkit-scrollbar{display:none}.nav a{flex:none;padding:6px 10px;font-size:.9rem}}
/* hero */
.hero{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:32px;align-items:center;padding-block:44px 30px;position:relative}
@media (max-width:900px){.hero{grid-template-columns:1fr;padding-block:26px 18px}}
.hero h1{font:900 clamp(2.6rem,6.4vw,5rem)/1.04 var(--disp);margin:0 0 16px;letter-spacing:.01em;text-wrap:balance}
.hero h1 em{font-style:normal;color:var(--pop);text-shadow:3px 3px 0 var(--red)}
.hero p{margin:0 0 20px;color:var(--muted);max-width:30em}
.stats{display:flex;flex-wrap:wrap;gap:10px}
.stat{border:1px solid var(--line);background:var(--panel);padding:8px 14px;clip-path:var(--cut);font:700 .85rem var(--body);color:var(--muted)}
.stat strong{display:block;font:1.7rem/1 var(--num);color:var(--ink);letter-spacing:.03em}
.stat:first-child strong{color:var(--pop)}
.reels{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(150px,200px);gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:6px}
.reel{scroll-snap-align:start;position:relative;overflow:hidden;background:#000;aspect-ratio:9/16;text-decoration:none;clip-path:var(--cut);outline:1px solid var(--line)}
.reel video,.reel img{width:100%;height:100%;object-fit:cover}
/* category bar */
.cats{display:flex;gap:8px;overflow-x:auto;padding:4px 0 14px;scrollbar-width:none}.cats::-webkit-scrollbar{display:none}
.chip{flex:none;border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:7px 14px;font:700 .9rem var(--body);text-decoration:none;cursor:pointer;clip-path:polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)}
.chip small{font:.95rem var(--num);margin-left:6px;color:var(--muted);letter-spacing:.03em}
.chip:hover{border-color:var(--muted)}
.chip[aria-pressed="true"],.chip.on{background:var(--pop);color:#09090D;border-color:var(--pop)}.chip[aria-pressed="true"] small,.chip.on small{color:#09090D}
h2{font:900 clamp(1.7rem,3.4vw,2.5rem)/1.15 var(--disp);margin:56px 0 14px;letter-spacing:.02em}
.sub{color:var(--muted);margin:-6px 0 18px}
/* top 10 */
.rank{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px 18px;counter-reset:r}
.rank li{counter-increment:r;display:grid;grid-template-columns:58px 72px minmax(0,1fr);gap:12px;align-items:center;background:var(--panel);padding:10px 12px 10px 4px;clip-path:var(--cut)}
.rank li::before{content:counter(r,decimal-leading-zero);font:2.5rem/1 var(--num);color:var(--muted);text-align:right;font-style:italic}
.rank li:nth-child(1)::before{color:var(--ssr)}.rank li:nth-child(2)::before{color:#D8DCE6}.rank li:nth-child(3)::before{color:#E08A4A}
.rank img{width:72px;height:72px;object-fit:cover}
.rank a{text-decoration:none;min-width:0}.rank .t{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:.92rem;line-height:1.4}
.rank .m{font-size:.8rem;color:var(--muted)}.rank .m b{font:1.15rem var(--num);color:var(--pop);letter-spacing:.02em}
/* grid */
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:16px}
.tools select{min-height:40px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font:700 .9rem var(--body);padding:0 10px}
.tools .cnt{margin-left:auto;color:var(--muted);font:600 .85rem var(--hud);letter-spacing:.08em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:22px 14px}
@media (max-width:520px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 10px}}
.it{text-decoration:none;display:grid;gap:6px;min-width:0;align-content:start}
.it .ph{position:relative;aspect-ratio:1;overflow:hidden;background:var(--panel2);clip-path:var(--cut)}
.it .ph::after{content:"";position:absolute;inset:0;border:2px solid transparent;clip-path:var(--cut);pointer-events:none}
.it .ph img{width:100%;height:100%;object-fit:cover;transition:transform .3s}
.it:hover .ph img{transform:scale(1.05)}
.it:hover .ph::after{border-color:var(--pop)}
.it:focus-visible{outline:2px solid var(--pop);outline-offset:3px}
.rar{position:absolute;top:0;left:0;font:700 .78rem/1 var(--hud);letter-spacing:.12em;padding:6px 10px 6px 8px;color:#09090D;clip-path:polygon(0 0,100% 0,calc(100% - 8px) 100%,0 100%)}
.r-ur{background:linear-gradient(90deg,#FF5CA8,#FFE600 35%,#3CF0FF 70%,#C77DFF)}.r-ssr{background:linear-gradient(90deg,#FFE27A,var(--ssr) 50%,#FF9F1C)}.r-sr{background:var(--sr)}.r-r{background:var(--r)}.r-n{background:#5B5B6B;color:#fff}
.it:has(.r-ssr) .ph::after{border-color:rgba(255,200,61,.5)}.it:has(.r-ur) .ph::after{border-color:rgba(60,240,255,.6)}
.off{position:absolute;bottom:8px;left:8px;background:var(--red);color:#fff;padding:2px 9px;font:700 .8rem var(--body);clip-path:polygon(6px 0,100% 0,calc(100% - 6px) 100%,0 100%)}
.off b{font:1rem var(--num);letter-spacing:.02em;margin-right:1px}
.vid{position:absolute;top:6px;right:6px;background:rgba(0,0,0,.7);color:var(--pop);font:700 .7rem var(--hud);letter-spacing:.08em;padding:3px 7px}
.tag{justify-self:start;display:inline-flex;align-items:baseline;gap:2px;background:var(--pop);color:#09090D;padding:0 12px 0 10px;margin:-18px 0 0 8px;position:relative;clip-path:polygon(6px 0,100% 0,calc(100% - 6px) 100%,0 100%)}
.tag .d{font:1rem var(--num)}.tag .v{font:1.6rem/1.3 var(--num);letter-spacing:.02em}
.it .n{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:.9rem;line-height:1.45}
.it .s{font:600 .78rem var(--body);color:var(--muted)}.it .s b{font:.95rem var(--num);color:var(--cyan);letter-spacing:.03em;margin-left:2px}
.more{display:block;margin:28px auto 0;border:0;background:var(--pop);color:#09090D;font:900 1rem var(--disp);padding:14px 34px;cursor:pointer;clip-path:var(--cut);letter-spacing:.1em}
.more:hover{background:#fff}
.more:focus-visible,.chip:focus-visible,.cta:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}
/* product */
.pd{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:32px;padding-block:28px}
@media (max-width:860px){.pd{grid-template-columns:1fr;gap:18px}}
.pd .media{display:grid;gap:12px;align-content:start}.pd .media img{aspect-ratio:1;object-fit:cover;width:100%;clip-path:var(--cut)}
.pd .media video{max-height:70vh;margin:0 auto;clip-path:var(--cut)}
.pd h1{font:900 clamp(1.35rem,2.6vw,1.9rem)/1.35 var(--disp);margin:6px 0 16px}
.pd .tag{margin:0 0 16px;padding:2px 18px}.pd .tag .v{font-size:3.2rem}.pd .tag .d{font-size:1.6rem}
.pd .rar{position:static;display:inline-block;margin-bottom:8px}
.buybar{position:fixed;left:0;right:0;bottom:0;z-index:55;display:none;align-items:center;gap:10px;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:rgba(9,9,13,.96);border-top:2px solid var(--pop);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px)}
.buybar .bt{flex:1;min-width:0;font:700 .8rem/1.35 var(--body);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;color:var(--muted)}.buybar .bt b{display:block;color:var(--pop);font:900 1.15rem var(--disp)}
.buybar .cta{min-height:48px;padding:0 18px;font-size:1rem;flex:0 0 auto;letter-spacing:.02em}
@media (max-width:860px){.buybar.on{display:flex}body.has-bb{padding-bottom:76px}body.has-bb .ybf-btn{bottom:86px}body.has-bb .ybf-tip{bottom:150px}}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px;padding:0;list-style:none}
.facts li{border:1px solid var(--line);background:var(--panel);padding:3px 12px;font-size:.9rem}
.cta{display:flex;justify-content:center;align-items:center;gap:8px;min-height:58px;background:var(--pop);color:#09090D;font:900 1.15rem var(--disp);text-decoration:none;clip-path:var(--cut);letter-spacing:.06em}
.cta:hover{background:#fff}
.cta[aria-disabled="true"]{background:var(--panel2);color:var(--muted);pointer-events:none}
.fine{font-size:.8rem;color:var(--muted);margin:12px 0 0}
.crumb{font-size:.85rem;color:var(--muted)}.crumb a{color:var(--muted)}
/* theme shelves */
.shelf{margin:0 0 26px}.shelf h3{font:900 1.25rem var(--disp);margin:0 0 10px;display:flex;gap:10px;align-items:baseline}.shelf h3 small{font:600 .8rem var(--hud);color:var(--muted);letter-spacing:.1em}
.srow{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(150px,170px);gap:14px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x mandatory}
.srow .it{scroll-snap-align:start}
/* trending: social quests */
.qs{display:grid;gap:26px}
.q{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:20px;background:var(--panel);padding:18px;clip-path:var(--cut);position:relative}
.q::before{content:attr(data-no);position:absolute;right:14px;top:-6px;font:900 5.5rem/1 var(--num);color:rgba(255,255,255,.04);pointer-events:none}
@media (max-width:860px){.q{grid-template-columns:1fr;padding:14px}}
.q h3{font:900 clamp(1.35rem,2.6vw,1.9rem)/1.25 var(--disp);margin:0 0 6px}
.q h3 small{display:block;font:700 .75rem var(--hud);letter-spacing:.28em;color:var(--red);margin-bottom:6px}
.q .why{color:var(--muted);font-size:.92rem;margin:0 0 12px}
.emb{position:relative;clip-path:var(--cut);background:#000}
.emb>button{all:unset;cursor:pointer;display:block;position:relative;width:100%;box-sizing:border-box}
.emb>button:focus-visible{outline:3px solid var(--pop);outline-offset:-3px}
.emb.yt.big{aspect-ratio:16/9;overflow:hidden}.emb.yt.big>button{position:absolute;inset:0}
.emb.yt.big img{width:100%;height:100%;object-fit:cover;opacity:.85;transition:opacity .2s}.emb.yt.big button:hover img{opacity:1}
.play{position:absolute;left:50%;top:50%;width:76px;height:54px;transform:translate(-50%,-50%);background:var(--red);clip-path:polygon(0 0,100% 12%,100% 88%,0 100%)}
.play::after{content:"";position:absolute;left:30px;top:15px;border-style:solid;border-width:12px 0 12px 20px;border-color:transparent transparent transparent #fff}
.emb iframe{display:block;width:100%;border:0}
.emb.yt iframe{aspect-ratio:16/9;height:auto}
.emb.tt iframe{aspect-ratio:9/16;height:auto;max-height:640px;max-width:360px;margin:0 auto}
.emb.th.on{background:transparent;clip-path:none}.emb.th blockquote{margin:0}.emb.th.on:has(iframe) blockquote{display:none}.intel .emb.on{grid-column:1/-1;max-width:560px}.intel .emb.tt.on{max-width:360px}
.emb.card{background:var(--panel2);display:grid}
.emb.card>button{padding:12px 12px 10px;display:grid;gap:4px;align-content:start;min-height:120px}
.emb.card>button:hover{background:#22222F}
.emb.card img{width:100%;aspect-ratio:16/9;object-fit:cover;margin-bottom:4px}
.emb.card.on{background:#000}.emb.card.on .orig{display:none}
.emb.card.big{max-width:420px;background:linear-gradient(160deg,#1B1B26 0%,#121219 55%,rgba(60,240,255,.18) 100%)}.emb.card.big>button{min-height:300px;padding:18px;align-content:end;gap:6px}.emb.card.big>button::before{content:'';position:absolute;left:50%;top:38%;width:84px;height:84px;transform:translate(-50%,-50%);border-radius:50%;background:var(--cyan);box-shadow:0 0 0 10px rgba(60,240,255,.15)}.emb.card.big>button::after{content:'';position:absolute;left:calc(50% + 4px);top:38%;transform:translate(-50%,-50%);border-style:solid;border-width:16px 0 16px 26px;border-color:transparent transparent transparent #09090D}.emb.card.big .au{font-size:1.05rem}.emb.card.big .nt{font-size:.95rem;color:var(--ink)}.emb.card.big.on{max-width:360px;background:#000}.emb.card.big.on>button::before,.emb.card.big.on>button::after{display:none}
.ch{display:flex;gap:6px;align-items:center}
.pf{font:700 .7rem/1 var(--hud);letter-spacing:.1em;padding:4px 7px;color:#09090D}.pf-yt{background:#FF3B3B;color:#fff}.pf-tt{background:var(--cyan)}.pf-th{background:#F3F1EA}
.lg{font:600 .72rem var(--body);color:var(--muted);border:1px solid var(--line);padding:1px 6px}
.au{font:700 .86rem var(--body)}.nt{font-size:.84rem;color:var(--muted);line-height:1.45}
.op{font:700 .8rem var(--body);color:var(--pop);margin-top:4px}
.orig{font-size:.74rem;color:var(--muted);padding:0 12px 10px;text-decoration:none}.orig:hover{color:var(--ink)}
.ih{margin:16px 0 8px;font:700 .78rem var(--hud);letter-spacing:.24em;color:var(--cyan);display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
.ih span{font:600 .74rem var(--body);letter-spacing:0;color:var(--muted)}
.intel{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;align-items:start}
.src .pf,.src .lg{vertical-align:1px;margin-right:2px}
.src{font-size:.78rem;color:var(--muted);margin:8px 0 0}.src a{color:var(--muted)}
.loot{display:grid;gap:10px;align-content:start}
.loot h4{margin:0;font:700 .78rem var(--hud);letter-spacing:.28em;color:var(--pop)}
.li{display:grid;grid-template-columns:76px minmax(0,1fr);gap:12px;align-items:center;text-decoration:none;background:var(--panel2);padding:8px;clip-path:var(--cut)}
.li:hover{outline:1px solid var(--pop)}
.li img{width:76px;height:76px;object-fit:cover}
.li .t{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:.86rem;line-height:1.4}
.li .m{font-size:.78rem;color:var(--muted)}.li .m b{font:1.1rem var(--num);color:var(--pop);margin-right:6px;letter-spacing:.02em}
.li .go{display:block;font:700 .76rem var(--body);color:var(--cyan);margin-top:2px}
.qnote{font-size:.8rem;color:var(--muted);border-left:3px solid var(--red);padding-left:10px;margin:18px 0 0}
/* guides */
.gl{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.gc{background:var(--panel);padding:16px 18px;text-decoration:none;display:grid;gap:4px;clip-path:var(--cut)}
.gc:hover{background:var(--panel2);box-shadow:inset 3px 0 var(--pop)}.gc .k{font:700 .78rem var(--hud);letter-spacing:.2em;color:var(--red)}.gc .t{font:900 1.08rem/1.4 var(--disp)}
.art{max-width:760px}.art h1{font:900 clamp(1.6rem,3.4vw,2.4rem)/1.3 var(--disp);margin:8px 0 12px}
.art .tbl{overflow-x:auto;border:1px solid var(--line)}.art table{border-collapse:collapse;width:100%;min-width:560px;font-size:.92rem}
.art th,.art td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}.art th{background:var(--pop);color:#09090D}
.art .crit{display:grid;gap:10px;padding-left:1.2em}.art dt{font-weight:700;margin-top:12px}.art dd{margin:4px 0 0}
.art .cta{display:inline-flex;padding:0 22px}
.note{border:1px dashed var(--line);padding:10px 14px;font-size:.86rem;color:var(--muted)}
.ft{border-top:1px solid var(--line);margin-top:64px;padding-block:22px 40px;font-size:.85rem;color:var(--muted)}
.ft a{color:var(--muted)}
@media (prefers-reduced-motion:reduce){.it .ph img,.emb img{transition:none}}
/* ===== v3: 3D hero, games, gifts, deals ===== */
body{overflow-x:clip}
.h3{position:relative;margin-inline:calc(50% - 50vw);height:min(82vh,740px);min-height:580px;overflow:hidden;background:radial-gradient(ellipse at 70% 45%,rgba(255,46,59,.2),transparent 55%),radial-gradient(ellipse at 72% 70%,rgba(255,230,0,.1),transparent 60%),var(--bg);border-bottom:1px solid var(--line)}
.h3 canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:pan-y;cursor:grab;opacity:0;transition:opacity 1.2s}
.h3.live canvas{opacity:1}
.h3::before,.h3::after{content:"";position:absolute;width:46px;height:46px;border:2px solid var(--pop);pointer-events:none;z-index:2;opacity:.8}
.h3::before{top:18px;right:18px;border-left:0;border-bottom:0}.h3::after{bottom:18px;right:18px;border-left:0;border-top:0}
.h3scan{position:absolute;left:0;right:0;height:120px;top:-120px;background:linear-gradient(transparent,rgba(60,240,255,.06),transparent);pointer-events:none;animation:scan 7s linear infinite;z-index:1}
@keyframes scan{to{top:100%}}
.h3in{position:relative;z-index:2;height:100%;display:flex;align-items:center;pointer-events:none}
.h3txt{max-width:520px;pointer-events:auto}
.h3 h1{font:900 clamp(2.6rem,6.4vw,5rem)/1.04 var(--disp);margin:0 0 16px;letter-spacing:.01em;text-shadow:0 2px 18px rgba(9,9,13,.8)}
.h3 h1 em{font-style:normal;color:var(--pop);text-shadow:3px 3px 0 var(--red)}
.h3 p.lead{margin:0 0 18px;color:#C9C6D4;max-width:30em;text-shadow:0 1px 8px rgba(9,9,13,.9)}
.h3cta{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 14px}
.h3cta a{text-decoration:none}
.btn{display:inline-flex;align-items:center;gap:8px;min-height:48px;padding:0 22px;font:900 1rem var(--disp);letter-spacing:.06em;clip-path:var(--cut);text-decoration:none;cursor:pointer;border:0}
.btn.y{background:var(--pop);color:#09090D}.btn.y:hover{background:#fff}
.btn.o{background:rgba(19,19,27,.85);color:var(--ink);box-shadow:inset 0 0 0 1px var(--cyan)}.btn.o:hover{background:var(--panel2)}
.snd{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.snd button{min-height:40px;border:1px solid var(--line);background:rgba(19,19,27,.85);color:var(--ink);font:700 .88rem var(--body);padding:0 14px;cursor:pointer;clip-path:polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)}
.snd button[aria-pressed="true"]{background:var(--cyan);color:#09090D;border-color:var(--cyan)}
.snd button:focus-visible,.btn:focus-visible{outline:2px solid var(--pop);outline-offset:3px}
.snd .hint{font:600 .76rem var(--hud);letter-spacing:.12em;color:var(--muted)}
#h3note{font-size:.78rem;color:var(--muted);margin:8px 0 0;min-height:1.2em}
.h3tip{position:absolute;left:0;top:0;z-index:3;max-width:230px;background:rgba(19,19,27,.95);border:1px solid var(--pop);padding:8px 10px;pointer-events:none;display:grid;gap:3px;clip-path:var(--cut)}
.h3tip .rar{position:static;justify-self:start}.h3tip b{font-size:.86rem;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.h3tip .m{font:600 .78rem var(--body);color:var(--pop)}
@media (max-width:899px){.h3{height:auto;min-height:0}.h3 canvas{height:260px;bottom:auto}.h3in{align-items:flex-end;padding-top:232px;padding-bottom:22px}.h3txt{max-width:none}.h3::before,.h3::after{display:none}.h3 h1{font-size:clamp(2rem,9vw,2.6rem);margin-bottom:10px}.h3 p.lead{font-size:.92rem;margin-bottom:12px}.h3cta{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0 8px}.h3cta .btn{justify-content:center;padding-inline:8px;font-size:.88rem}.snd .hint{display:none}}
@media (prefers-reduced-motion:reduce){.h3scan{display:none}}
/* card tilt + price-drop badge */
@media (hover:hover) and (pointer:fine){.it .ph{transition:transform .25s ease;transform:perspective(700px) rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg))}
.it .ph::before{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;background:radial-gradient(circle at var(--mx,50%) var(--my,50%),rgba(255,255,255,.22),transparent 45%);opacity:0;transition:opacity .2s}.it:hover .ph::before{opacity:1}}
.drop{position:absolute;bottom:8px;right:8px;background:var(--cyan);color:#09090D;padding:2px 8px;font:700 .78rem var(--hud);letter-spacing:.04em;clip-path:polygon(6px 0,100% 0,calc(100% - 6px) 100%,0 100%)}
.ptitle{font:900 clamp(2rem,4.6vw,3.2rem)/1.15 var(--disp);margin:28px 0 8px}

/* evolve game */
.arena{position:relative;width:100%;height:min(74vh,680px);min-height:440px;background:#09090D;clip-path:var(--cut);outline:1px solid var(--line);user-select:none;-webkit-user-select:none}
.arena:fullscreen{height:100vh;clip-path:none}
@media (max-width:700px){.arena{height:calc(100svh - 190px);min-height:420px;margin-inline:-16px;width:calc(100% + 32px);clip-path:none}}
.arena>canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none;cursor:crosshair}
.gov{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:18px;background:linear-gradient(transparent 0,rgba(9,9,13,.55) 32%,rgba(9,9,13,.94) 60%);overflow:auto;text-align:center}
.gov[hidden]{display:none}.gov>*{flex-shrink:0}
.gov h2{margin:0 0 4px;font:900 clamp(1.8rem,4.6vw,3rem)/1.1 var(--disp)}.gov h2 em{font-style:normal;color:var(--pop);text-shadow:3px 3px 0 var(--red)}
.gov .sub{margin:0 0 10px;max-width:40em}
.lvrow{display:flex;align-items:center;gap:10px;justify-content:center;font:700 .85rem var(--hud);letter-spacing:.1em;color:var(--muted);margin:6px 0}
.lvrow b{font:1.6rem var(--num);color:var(--pop);letter-spacing:.03em}
.lvbar{width:160px;height:8px;background:var(--line)}.lvbar i{display:block;height:100%;background:linear-gradient(90deg,var(--sr),var(--cyan))}
.evo{list-style:none;display:flex;gap:6px;padding:0;margin:8px 0;justify-content:center;flex-wrap:wrap}
.evo li{background:var(--panel);clip-path:var(--cut);padding:4px 8px 6px;display:grid;justify-items:center;opacity:.55;min-width:84px}.evo li.on{opacity:1;box-shadow:inset 0 0 0 1px var(--pop)}
.evo canvas{width:60px;height:60px}.evo b{font:900 .82rem var(--disp)}.evo small{font:600 .62rem var(--hud);letter-spacing:.14em;color:var(--muted)}
.perks{list-style:none;padding:0;margin:6px 0 12px;display:flex;flex-wrap:wrap;gap:6px;justify-content:center;max-width:760px}
.perks li{font-size:.76rem;color:var(--muted);border:1px solid var(--line);padding:3px 8px;background:rgba(19,19,27,.8)}.perks li.on{color:var(--ink);border-color:var(--cyan)}.perks b{font:700 .72rem var(--hud);color:var(--cyan);margin-right:6px}
.ctrl{font-size:.8rem;color:var(--muted);margin:8px 0 0}
#gdaily{font-size:.82rem;margin:6px 0 0;color:var(--muted)}#gdaily a{color:var(--pop)}
.gs{font:clamp(3rem,9vw,5rem)/1 var(--num);color:var(--pop);text-shadow:4px 4px 0 var(--red)}
.glvup{font:700 .9rem var(--body);color:var(--cyan);margin:4px 0 10px}
.gloot{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;width:100%;max-width:760px;margin:6px 0 12px}
.lt{position:relative;display:grid;gap:3px;text-decoration:none;background:var(--panel);padding:6px;clip-path:var(--cut);text-align:left}
.lt img{width:100%;aspect-ratio:1;object-fit:cover}.lt .rar{top:6px;left:6px;font-size:.62rem}.lt .ln{font-size:.7rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.lt .lp{font:.95rem var(--num);color:var(--pop)}
.lt.t-ur{box-shadow:inset 0 0 0 2px #3CF0FF}.lt.t-ssr{box-shadow:inset 0 0 0 2px var(--ssr)}
.gtools{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.gtools button{min-height:38px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font:700 .85rem var(--body);padding:0 14px;cursor:pointer}
@media (max-width:700px){.gov{justify-content:flex-start;background:rgba(9,9,13,.93);padding:12px}.gov h2{font-size:1.7rem}.gov .sub{font-size:.8rem;margin-bottom:6px}.evo{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px;width:100%}.evo li{min-width:0;padding:3px 2px}.evo canvas{width:44px;height:44px}.evo b{font-size:.68rem}.evo small{display:none}.perks{gap:4px}.perks li{font-size:.68rem;padding:2px 6px}.ctrl{font-size:.72rem}.gloot{grid-template-columns:repeat(3,minmax(0,1fr))}.gs{font-size:3rem}}
#gdash{position:absolute;right:18px;bottom:22px;z-index:1;width:76px;height:76px;border-radius:50%;border:2px solid var(--cyan);background:conic-gradient(rgba(9,9,13,.75) var(--cd,0%),rgba(60,240,255,.35) 0);color:#fff;font:900 1rem var(--disp);touch-action:none}
/* coupang widgets */
.cpw,.cps{background:#fff;clip-path:var(--cut);padding:6px 6px 2px;margin:10px 0}
.cpl{display:flex;gap:8px;align-items:baseline;font:900 .9rem var(--disp);color:#09090D;padding:2px 6px 6px}.cpl small{font:600 .7rem var(--body);color:#6b6b7a}
.cpf{height:140px}.cpf iframe{display:block;border:0;width:100%;height:140px}
.cptabs{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 8px}
.cpgrid{display:grid;gap:12px}

/* night market dungeon */
.dg{position:relative;width:100%;height:min(76vh,700px);min-height:460px;background:#07060a;outline:1px solid var(--line);user-select:none;-webkit-user-select:none;overflow:hidden;touch-action:none}
.dg:fullscreen{height:100vh;width:100vw}.dg:-webkit-full-screen{height:100vh;width:100vw}
.dg.dg-full{position:fixed;inset:0;width:100vw;height:100vh;height:100dvh;min-height:0;max-height:none;margin:0;z-index:9999;outline:0}
html.dg-lock,html.dg-lock body{overflow:hidden;overscroll-behavior:none}.dg-full .dghud{padding-top:max(8px,env(safe-area-inset-top));padding-left:max(10px,env(safe-area-inset-left));padding-right:max(10px,env(safe-area-inset-right))}.dg-full .dgpad{right:max(12px,env(safe-area-inset-right));bottom:max(14px,env(safe-area-inset-bottom))}.dg-full .dgov{padding-top:max(16px,env(safe-area-inset-top));padding-bottom:max(16px,env(safe-area-inset-bottom))}html.dg-lock .ybf-btn,html.dg-lock .ybf-tip{display:none}
.dginst{font:700 .78rem var(--body);color:var(--muted);margin:6px auto 0;max-width:420px}
@media (max-width:700px){.dg{height:calc(100svh - 170px);min-height:440px;margin-inline:-16px;width:calc(100% + 32px)}}
#dgc{position:absolute;inset:0;width:100%;height:100%;image-rendering:pixelated;image-rendering:crisp-edges;display:block;cursor:crosshair}.dgfx{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:1}.lvr{flex-basis:100%;font:700 .74rem var(--body);color:#FFE27A;text-align:center}
.dghud{position:absolute;left:0;right:0;top:0;z-index:2;display:flex;align-items:center;gap:10px;padding:8px 10px;background:linear-gradient(rgba(7,6,10,.85),rgba(7,6,10,0));pointer-events:none;flex-wrap:wrap}
.dghud[hidden]{display:none}.dghud button,.dghud .slot{pointer-events:auto}
.dghp{display:flex;gap:2px;flex-wrap:wrap;max-width:150px}.dghp i{width:10px;height:9px;background:#3a3a48;clip-path:polygon(50% 100%,0 40%,0 15%,25% 0,50% 18%,75% 0,100% 15%,100% 40%)}.dghp i.on{background:#FF2E3B}
.dgfl{font:900 .9rem var(--disp);color:var(--pop);text-shadow:2px 2px 0 #000}.dgco{font:700 .85rem var(--hud);color:#fff}.dgco b{font:1.05rem var(--num);color:var(--pop)}
.dgeq{display:flex;gap:4px;margin-left:auto}.slot{width:34px;height:34px;padding:0;border:2px solid #444;background:#13131b;color:#888;font-size:.8rem;cursor:pointer;overflow:hidden}.slot img{width:100%;height:100%;object-fit:cover;image-rendering:pixelated}
.slot.t-r{border-color:#4DA3FF}.slot.t-sr{border-color:#C77DFF}.slot.t-ssr{border-color:#FFC83D}.slot.t-ur{border-color:#3CF0FF;box-shadow:0 0 8px #3CF0FF}
#dgmm{width:90px;height:69px;background:rgba(7,6,10,.7);border:1px solid #333;image-rendering:pixelated}
#dgpz{width:34px;height:34px;border:1px solid #444;background:#13131b;color:#fff;cursor:pointer;font-size:.75rem}
@media (max-width:700px){#dgmm{width:66px;height:51px}.dghp{max-width:110px}.slot{width:28px;height:28px}}
.dgboss{position:absolute;left:50%;bottom:16px;transform:translateX(-50%);z-index:2;width:min(420px,80%);text-align:center;pointer-events:none}
.dgboss b{font:900 .95rem var(--disp);color:#fff;text-shadow:2px 2px 0 #000}.dgboss i{display:block;height:8px;background:#2a0a12;border:1px solid #000;margin-top:3px}.dgboss span{display:block;height:100%;background:linear-gradient(90deg,#FF2E3B,#FFE600);transition:width .2s}
@media (max-width:700px){.dgboss{bottom:auto;top:62px}}
.dgtoast{position:absolute;left:50%;top:58px;transform:translate(-50%,-6px);z-index:3;background:rgba(7,6,10,.85);border:1px solid var(--pop);color:#fff;font:700 .82rem var(--body);padding:5px 12px;opacity:0;transition:.25s;pointer-events:none;max-width:90%;text-align:center}
.dgtoast.on{opacity:1;transform:translate(-50%,0)}
.dgbanner{position:absolute;left:0;right:0;top:36%;z-index:3;text-align:center;pointer-events:none;opacity:0}
.dgbanner.on{animation:dgb 2.6s ease}.dgbanner b{display:block;font:900 clamp(1.6rem,5vw,2.6rem)/1.1 var(--disp);color:var(--pop);text-shadow:3px 3px 0 var(--red),0 0 18px rgba(0,0,0,.8)}.dgbanner small{font:700 .9rem var(--body);color:#fff;text-shadow:1px 1px 0 #000}
@keyframes dgb{0%{opacity:0;transform:scale(1.3)}12%{opacity:1;transform:none}80%{opacity:1}100%{opacity:0}}
.dgcard{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);z-index:4;display:grid;grid-template-columns:72px minmax(0,1fr);gap:4px 10px;width:min(440px,94%);background:rgba(19,19,27,.96);border:2px solid var(--pop);padding:8px}
.dgcard[hidden]{display:none}.dgcard .ci{position:relative}.dgcard .ci img{width:72px;height:72px;object-fit:cover}.dgcard .ci .rar{top:0;left:0;font-size:.62rem}
.dgcard .ct{display:grid;gap:2px;align-content:start;min-width:0}.dgcard small{font:700 .7rem var(--hud);color:var(--cyan);letter-spacing:.1em}.dgcard b{font-size:.82rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.dgcard .st{font:700 .82rem var(--body);color:var(--pop)}.dgcard .cmp{font-size:.74rem;color:var(--muted)}
.dgcard .cb{grid-column:1/-1;display:flex;gap:8px}.dgcard .btn{min-height:36px;font-size:.85rem;padding:0 14px}
.dgcard:not(:has(.ci)){grid-template-columns:1fr}
@media (max-width:700px){.dgcard{bottom:auto;top:96px}}
.dgjoy{position:absolute;z-index:3;width:84px;height:84px;margin:-42px 0 0 -42px;border:2px solid rgba(255,255,255,.3);border-radius:50%;pointer-events:none}.dgjoy i{position:absolute;left:50%;top:50%;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;background:rgba(255,230,0,.55)}
.dgjoy[hidden]{display:none}
.dgpad{position:absolute;right:12px;bottom:14px;z-index:3;display:grid;grid-template-columns:auto auto;gap:10px;align-items:end}
.dgpad[hidden]{display:none}.dgpad button{border-radius:50%;border:2px solid #fff;color:#fff;font:900 .85rem var(--disp);touch-action:none}
#dgatk{width:78px;height:78px;background:rgba(255,46,59,.75);grid-column:2;grid-row:2/span 2}#dgroll{width:56px;height:56px;background:rgba(60,240,255,.45);grid-column:1;grid-row:3}#dgact{position:absolute;right:8px;bottom:222px;width:62px;height:62px;background:rgba(255,230,0,.8);color:#09090D}#dgskb{grid-column:1;grid-row:2;width:56px;height:56px;background:rgba(166,92,232,.6);position:relative;overflow:hidden}#dgskb i{position:absolute;left:0;right:0;bottom:0;background:rgba(7,6,10,.65);pointer-events:none}#dgskb.rdy{box-shadow:0 0 12px #C77DFF}.dgsk{pointer-events:auto;position:relative;overflow:hidden;display:flex;align-items:center;gap:6px;padding:4px 10px 4px 4px;background:rgba(19,19,27,.85);border:2px solid #6E33A6;color:var(--ink);font:700 .78rem var(--hud);cursor:pointer;min-height:34px}.dgsk b{display:grid;place-items:center;width:22px;height:22px;background:#A65CE8;color:#fff;font:900 .8rem var(--num)}.dgsk i{position:absolute;left:0;right:0;bottom:0;background:rgba(7,6,10,.7);pointer-events:none}.dgsk.rdy{border-color:#C77DFF;box-shadow:0 0 10px rgba(199,125,255,.6)}@media (max-width:700px){.dgsk{display:none}}
#dgact[hidden]{display:none}
.dgov{position:absolute;inset:0;z-index:5;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(7,6,10,.72);overflow:auto}
.dgov[hidden]{display:none}.dgov .tl{max-width:760px;width:100%;text-align:center}
.dgov h2{margin:0 0 6px;font:900 clamp(2rem,6vw,3.6rem)/1.05 var(--disp)}.dgov h2 em{font-style:normal;color:var(--pop);text-shadow:3px 3px 0 var(--red)}.dgov h2 small{font:600 .9rem var(--hud);color:var(--muted)}
.dgov .sub{margin:0 auto 10px;max-width:36em}
.dgst{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:8px 0}.dgst span{background:var(--panel);padding:6px 12px;clip-path:var(--cut);font:700 .8rem var(--body);color:var(--muted)}.dgst b{font:1.1rem var(--num);color:var(--pop);margin-left:4px}
.dgbt{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:12px 0}
.dgopt{display:flex;gap:6px;justify-content:center;flex-wrap:wrap}.dgopt button{min-height:34px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font:700 .8rem var(--body);padding:0 12px;cursor:pointer}
.dgov .ctrl{font-size:.76rem;color:var(--muted);margin:8px 0}
.upg{list-style:none;padding:0;margin:10px auto;display:grid;gap:6px;max-width:520px}.upg li{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;background:var(--panel);padding:8px 12px;text-align:left;clip-path:var(--cut)}
.upg .ul{font:1rem var(--num);color:var(--pop);letter-spacing:.1em}.upg .um{font:700 .8rem var(--hud);color:var(--cyan)}.upg .btn{min-height:34px;font-size:.85rem;padding:0 12px}.upg .btn:disabled{opacity:.45;cursor:not-allowed}
.dx2{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:8px;margin:8px 0;text-align:left}
#dgshop{align-items:flex-start;background:rgba(7,6,10,.9)}.shtabs{display:flex;gap:6px;justify-content:center;margin:10px 0}.shtabs button{font:700 .9rem var(--hud);padding:8px 18px;background:var(--panel);color:var(--ink);border:0;clip-path:var(--cut);cursor:pointer;min-height:40px}.shtabs [aria-selected=true]{background:var(--pop);color:#111}.shmsg{margin:6px auto;max-width:520px;padding:8px 12px;background:rgba(60,240,255,.12);color:var(--cyan);font-size:.85rem}#dgpv{width:266px;height:140px;image-rendering:pixelated;display:block;margin:6px auto;background:rgba(255,255,255,.04)}.shg{font:700 .95rem var(--hud);margin:14px 0 6px;color:var(--ink)}.shgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:6px;max-width:620px;margin:0 auto}.sh{display:flex;flex-direction:column;align-items:center;gap:3px;padding:8px 4px;background:var(--panel);color:var(--ink);border:2px solid transparent;cursor:pointer;font:600 .8rem var(--body);min-height:44px}.sh i{width:28px;height:18px;display:block;border:2px solid #1A1420}.sh i.none{background:repeating-linear-gradient(45deg,#333 0 4px,#222 4px 8px)}.sh img{width:33px;height:27px;image-rendering:pixelated;object-fit:contain}.sh img.lk{width:30px;height:42px}.sh small{font:700 .72rem var(--hud);color:var(--muted)}.sh.gd small{color:#FFC83D}.sh.on{border-color:var(--pop)}.sh.on small{color:var(--pop)}.pks{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;max-width:600px;margin:8px auto}.pk{display:flex;flex-direction:column;gap:2px;align-items:center;padding:12px 6px;background:var(--panel);color:var(--ink);border:2px solid rgba(255,200,61,.4);cursor:pointer}.pk b{font:1.2rem var(--num);color:#FFC83D}.pk span{font:700 .95rem var(--hud)}.pk small{font-size:.72rem;color:var(--cyan)}.shcf{max-width:480px;margin:10px auto;padding:12px;background:var(--panel)}.rbf{display:flex;gap:6px;justify-content:center;max-width:420px;margin:6px auto}.rbf input{flex:1;min-width:0;padding:8px 10px;font:600 1rem var(--body);background:#0d0b12;color:var(--ink);border:1px solid var(--line)}.rbl{list-style:none;padding:0;margin:6px auto;max-width:520px;text-align:left;font-size:.8rem;color:var(--muted)}.code{font:1.3rem var(--num);letter-spacing:.12em;color:var(--pop);background:#0d0b12;display:inline-block;padding:6px 12px;user-select:all}
.dgday{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center;margin:6px auto;max-width:560px;font:600 .82rem var(--body);color:var(--muted)}.dgday b{color:var(--pop);font-family:var(--num)}.dgday .btn{min-height:36px;font-size:.85rem;padding:0 14px}
.dglv{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;margin:8px auto 4px;max-width:520px;font:700 .82rem var(--body);color:var(--muted)}.dglv .lvb{background:var(--pop);color:#111;padding:2px 10px;clip-path:var(--cut);font:900 .85rem var(--disp)}.dglv .lvb b{font:1.05rem var(--num)}.dglv .lvt{color:var(--ink);font-weight:900}.dglv .lvbar{flex:1 1 140px;max-width:220px;height:8px;background:#2A2A38;position:relative;overflow:hidden}.dglv .lvbar i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,var(--pop),#FF9F1C)}.dglv .lvn{font:.75rem var(--num);color:var(--muted)}.dglv.end{flex-direction:row}.dglv .xg{flex-basis:100%;text-align:center;color:var(--muted)}.dglv .xg b{color:var(--pop)}
.dglvh{font:900 .85rem/1.3 var(--body);color:#111;background:var(--pop);padding:2px 8px;clip-path:var(--cut);letter-spacing:.02em}
.dgrk{list-style:none;margin:8px auto;padding:0;max-width:460px;text-align:left;max-height:46vh;overflow:auto}.dgrk li{display:grid;grid-template-columns:2.2em 1fr auto auto;gap:8px;align-items:center;padding:6px 10px;border-bottom:1px solid var(--line);font:700 .85rem var(--body);color:var(--ink)}.dgrk li b{font:1rem var(--num);color:var(--muted)}.dgrk li:nth-child(1) b{color:#FFC83D}.dgrk li:nth-child(2) b{color:#D9E2EC}.dgrk li:nth-child(3) b{color:#E0A060}.dgrk li .lv{color:var(--muted);font-size:.75rem}.dgrk li .sc{font:.95rem var(--num);color:var(--pop)}.dgrk li.me{background:rgba(255,230,0,.12);outline:1px solid var(--pop)}
.dgdaily{margin:6px auto 8px;max-width:420px;padding:10px 14px;border:1px solid var(--pop);background:rgba(255,230,0,.06);display:grid;gap:2px;justify-items:center}.dgdaily b{font:2rem var(--num);color:var(--pop)}.dgdaily small{color:var(--muted)}.dgdaily p{margin:4px 0 0;font:700 .85rem var(--body);color:var(--ink)}.dgdaily p b{font:inherit;color:var(--pop)}
.dgjoin{display:flex;gap:8px;justify-content:center;margin:10px auto;max-width:360px}.dgjoin input{flex:1;min-width:0;min-height:46px;padding:0 12px;background:#111;border:1px solid var(--line);color:var(--ink);font:900 1.2rem var(--num);letter-spacing:.3em;text-transform:uppercase;text-align:center}
.dgnetc{flex-basis:100%;font:700 .75rem var(--body);color:#3CF0FF;text-shadow:1px 1px 0 #000}.dgnetc[hidden]{display:none}
#dgemo{pointer-events:auto;min-height:34px;padding:0 11px;border:1.5px solid var(--pop);background:rgba(19,19,27,.88);color:var(--pop);border-radius:17px;font:800 .82rem var(--body);cursor:pointer;white-space:nowrap}#dgemo[hidden]{display:none}
.dgemob{position:absolute;z-index:6;left:10px;top:90px;display:flex;flex-direction:column;align-items:stretch;gap:6px;width:calc(100% - 20px);max-height:62%;overflow:auto;background:rgba(9,9,13,.88);border:1px solid var(--line);padding:6px}.dgemob[hidden]{display:none}.dgemob.land{width:min(400px,44%)}.dgemor{display:flex;gap:5px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}.dgemor::-webkit-scrollbar{display:none}.dgemor button{flex:none;min-height:30px;padding:0 10px;border:1.5px solid #fff;background:rgba(19,19,27,.92);color:#fff;font:800 .74rem var(--body);border-radius:16px;cursor:pointer}.dgemor .dgchx{position:sticky;right:0;margin-left:auto;border-color:var(--line);background:#13131b;color:var(--muted);border-radius:50%;min-width:30px;padding:0}.dgchf{display:flex;gap:6px}.dgchf input{flex:1;min-width:0;background:#0d0d14;border:1px solid var(--line);color:var(--ink);font:600 16px var(--body);padding:5px 8px}.dgchf input:focus{outline:2px solid var(--pop);outline-offset:-1px}.dgchf .btn{min-height:34px;padding:0 12px;font-size:.82rem}.dgchn{margin:0;text-align:center;font:600 .74rem var(--body);color:var(--muted)}.dgchn button{background:none;border:0;color:var(--cyan);font:700 .74rem var(--body);text-decoration:underline;cursor:pointer}.dgchsafe{font:600 .8rem/1.55 var(--body);color:var(--ink)}.dgchsafe b{color:var(--pop)}.dgchsafe ul{margin:6px 0 10px;padding-left:1.2em}.dgchsafe .btn{min-height:36px;padding:0 14px;font-size:.82rem}.dgchl{position:absolute;z-index:3;left:10px;top:90px;max-width:min(62%,360px);display:grid;gap:3px;pointer-events:none}.dgchl div{background:rgba(0,0,0,.6);color:#fff;font:600 .78rem/1.4 var(--body);padding:3px 8px;transition:opacity .6s;overflow-wrap:anywhere}.dgchl div b{color:var(--cyan);margin-right:6px}.dgchl div.me b{color:var(--pop)}.dgchl div.sys{color:var(--muted);font-style:italic}.dgchl div.out{opacity:0}
.dgnpc{align-items:flex-end}.dgnpcw{width:min(520px,100%);max-height:100%;display:flex;flex-direction:column;gap:8px;background:rgba(19,19,27,.97);border:2px solid var(--pop);padding:10px;box-shadow:0 0 0 4px rgba(0,0,0,.4)}
.dgnpch{display:flex;align-items:center;gap:10px}.dgnpch img{width:44px;height:36px;image-rendering:pixelated;background:#2a1a12;padding:2px;border:1px solid #7a5232}.dgnpch div{flex:1;display:grid}.dgnpch b{font:900 1rem var(--body);color:var(--pop)}.dgnpch small{font:600 .7rem var(--body);color:var(--muted)}
.dgnpcx{background:none;border:0;color:var(--muted);font-size:1.1rem;cursor:pointer;padding:4px 8px}
.dgnpcl{flex:1;min-height:120px;max-height:min(46vh,320px);overflow:auto;display:flex;flex-direction:column;gap:6px;padding:2px}
.dgnpcl p{margin:0;max-width:86%;padding:7px 10px;font:600 .86rem/1.5 var(--body);border-radius:12px;position:relative}
.dgnpcl p.n{align-self:flex-start;background:#2a1f16;border:1px solid #7a5232;color:var(--ink);border-bottom-left-radius:2px}.dgnpcl p.u{align-self:flex-end;background:#1f2f40;border:1px solid #2f6a8a;color:#dff6ff;border-bottom-right-radius:2px}
.dgnpcl p i{font:700 .58rem var(--hud);font-style:normal;color:var(--cyan);margin-left:6px;letter-spacing:.08em;vertical-align:middle}.dgnpcl p.wait span{display:inline-block;animation:dgdots 1s steps(3) infinite}@keyframes dgdots{0%{opacity:.2}50%{opacity:1}}
.dgnpcit{align-self:flex-start;display:flex;gap:8px;max-width:86%;background:var(--panel2);border:1px solid var(--line);padding:6px;color:var(--ink);text-decoration:none}.dgnpcit img{width:52px;height:52px;object-fit:cover;flex:none}.dgnpcit span{display:grid;gap:2px;min-width:0}.dgnpcit b{font-size:.76rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.dgnpcit small{font:700 .66rem var(--body);padding:1px 6px;justify-self:start;color:#111}.dgnpcit em{font:700 .68rem var(--body);font-style:normal;color:var(--cyan)}
.dgnpcq{display:flex;flex-wrap:wrap;gap:6px}.dgnpcq button{background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:700 .78rem var(--body);padding:6px 10px;border-radius:999px;cursor:pointer}.dgnpcq button:hover{border-color:var(--pop)}.dgnpcq button:disabled{opacity:.45;cursor:wait}
.dgnpcf{display:flex;gap:6px}.dgnpcf input{flex:1;min-width:0;background:#0d0d14;border:1px solid var(--line);color:var(--ink);font:600 16px var(--body);padding:8px 10px}.dgnpcf input:focus{outline:2px solid var(--pop);outline-offset:-1px}.dgnpcf .btn{min-height:38px;padding:0 14px}
.dgnpcgo{align-self:center;min-height:36px}
.dgeqp{align-items:flex-start}.gp{width:min(820px,100%);background:rgba(13,13,20,.97);border:2px solid var(--pop);padding:10px;display:flex;flex-direction:column;gap:8px;text-align:left}.gph{display:flex;align-items:center;gap:10px}.gph b{font:900 1.05rem var(--body);color:var(--pop)}.gph span{font:800 .85rem var(--body);margin-left:auto}.gpx{background:none;border:0;color:var(--muted);font-size:1.1rem;cursor:pointer;padding:2px 8px}.gpb{display:grid;grid-template-columns:minmax(0,280px) minmax(0,1fr);gap:12px}@media (max-width:640px){.gpb{grid-template-columns:1fr}}.gpeq{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.gslot{display:grid;justify-items:center;gap:2px}.gslot small{font:700 .66rem var(--body);color:var(--muted)}.gc{position:relative;width:100%;aspect-ratio:1;max-width:72px;padding:0;border:2px solid #3a3a4a;background:#15151f;cursor:pointer;overflow:hidden;display:grid;place-items:center}.gc img{width:100%;height:100%;object-fit:cover}.gc .gi{font-size:1.3rem;opacity:.45}.gc i{position:absolute;right:2px;bottom:1px;font:900 .62rem var(--num);font-style:normal;color:#fff;text-shadow:1px 1px 0 #000}.gc.on{outline:2px solid #fff;outline-offset:1px}.gc.empty{cursor:default;border-style:dashed;border-color:#262633;background:none}.gc.t-r{border-color:var(--r)}.gc.t-sr{border-color:var(--sr)}.gc.t-ssr{border-color:var(--ssr);box-shadow:0 0 6px rgba(255,200,61,.45)}.gc.t-ur{border-color:#3CF0FF;box-shadow:0 0 8px rgba(60,240,255,.55)}.gpst{display:flex;flex-wrap:wrap;gap:4px 12px;margin-top:8px;font:700 .78rem var(--body);color:var(--muted)}.gpst b{color:var(--ink)}.gpset{display:grid;gap:3px;margin-top:6px;font:700 .74rem var(--body);color:#FFE27A}.mu{color:var(--muted);font:600 .76rem var(--body)}.gpbh{display:flex;align-items:center;gap:6px;font:700 .8rem var(--body);color:var(--muted);margin-bottom:6px}.gpbh b{color:var(--ink)}.gpbh button{margin-left:auto;background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:700 .74rem var(--body);padding:3px 10px;cursor:pointer}.gpbag{display:grid;grid-template-columns:repeat(8,1fr);gap:4px;max-height:260px;overflow:auto}@media (max-width:640px){.gpbag{grid-template-columns:repeat(6,1fr);max-height:200px}}.gpd{display:grid;grid-template-columns:72px minmax(0,1fr);gap:6px 10px;background:var(--panel);border:1px solid var(--line);padding:8px;min-height:60px}.gpd>p{grid-column:1/-1;margin:0}.gpdi{position:relative}.gpdi img{width:72px;height:72px;object-fit:cover}.gpdi .rar{position:absolute;top:0;left:0;font-size:.62rem}.gpdt{display:grid;gap:2px;min-width:0}.gpdt small{font:700 .7rem var(--body);color:var(--cyan)}.gpdt b{font-size:.84rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.gpdt .st{font:700 .82rem var(--body);color:var(--pop)}.gpdt .cmp{font-size:.74rem;color:var(--muted)}.gpda{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.gpda .btn{min-height:34px;font-size:.8rem;padding:0 12px}.gpda .btn[disabled]{opacity:.5}.gpd .fine{grid-column:1/-1;margin:0;font-size:.66rem;color:var(--muted)}.slot.gbag{position:relative;font-size:1rem;color:#fff;border-color:var(--pop)}.slot.gbag i{position:absolute;right:1px;bottom:0;font:900 .55rem var(--num);font-style:normal;color:var(--pop)}.dgdiff{display:flex;align-items:center;justify-content:center;gap:10px;margin:6px auto 2px}.dgdiff span{font:800 .92rem var(--body)}.dgdiff b{color:var(--pop);font:900 1.2rem var(--num);margin:0 4px}.dgdiff small{color:var(--muted);font:600 .72rem var(--body);margin-left:4px}.dgdiff button{width:34px;height:34px;border:2px solid var(--pop);background:#13131b;color:var(--pop);font:900 1.1rem var(--body);cursor:pointer}.dgdiff button[disabled]{opacity:.3;cursor:default}.dgdiffn{margin:0 auto 8px;max-width:40em;font:600 .74rem/1.5 var(--body);color:var(--muted)}.dgshopn{display:grid;gap:6px}.dgshopi{display:grid;grid-template-columns:48px minmax(0,1fr) auto;gap:8px;align-items:center;background:var(--panel2);border:1px solid var(--line);padding:6px}.dgshopi img{width:48px;height:48px;object-fit:cover}.dgshopi span{display:grid;gap:2px;min-width:0}.dgshopi b{font-size:.78rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.dgshopi small{font:600 .7rem var(--body);color:var(--muted)}.dgshopi small i{font-style:normal;padding:0 5px;color:#111;font-weight:900}.dgshopi .btn{min-height:34px;padding:0 12px;font-size:.8rem}.dgshopi .btn[disabled]{opacity:.45}.dgshopi em{font:700 .74rem var(--body);color:var(--muted);font-style:normal}.dgnpcq .shopb{border-color:var(--pop);color:var(--pop)}.mnr{width:min(860px,100%);display:flex;flex-direction:column;gap:8px;text-align:left}.mnrh{display:flex;align-items:center;gap:10px}.mnrh b{font:900 1.05rem var(--body);color:var(--pop)}.mnrh span{margin-left:auto;font:800 .9rem var(--body)}#mnrc{width:100%;aspect-ratio:16/9;image-rendering:pixelated;image-rendering:crisp-edges;border:2px solid var(--line);background:#07060f;cursor:pointer}.mnrb{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:6px}.mnrc{display:grid;gap:4px;background:var(--panel);border:1px solid var(--line);padding:8px;cursor:pointer}.mnrc.on{border-color:var(--pop);box-shadow:0 0 0 1px var(--pop)}.mnrc b{font:800 .84rem var(--body)}.mnrc small{font:600 .72rem/1.45 var(--body);color:var(--muted)}.mnrc .btn{min-height:32px;font-size:.78rem;padding:0 10px;justify-self:start}.mnrc .btn[disabled]{opacity:.5}.mnrd{background:var(--panel);border:1px solid var(--line);padding:8px}.mnrd>b{font:800 .86rem var(--body);display:block;margin-bottom:6px}.mnrd .upg{margin:0}.pevl{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}.pevl button{display:grid;grid-template-columns:28px auto;grid-template-rows:auto auto;column-gap:6px;align-items:center;background:var(--panel2);border:1px solid var(--line);color:var(--ink);padding:4px 10px 4px 6px;cursor:pointer;text-align:left}.pevl button img{grid-row:1/3;width:28px;height:28px;image-rendering:pixelated;object-fit:contain}.pevl button span{font:800 .76rem var(--body)}.pevl button small{font:700 .66rem var(--body);color:var(--muted)}.pevl button.on{border-color:var(--pop);box-shadow:0 0 0 1px var(--pop)}.pevl button.can small{color:#FFE27A}.pevm{display:grid;grid-template-columns:minmax(0,360px) minmax(0,1fr);gap:10px;align-items:center}@media (max-width:640px){.pevm{grid-template-columns:1fr}}#petc{width:100%;aspect-ratio:36/26;background:radial-gradient(ellipse at 50% 80%,#1d1530,#0a0812);border:1px solid var(--line)}#petc4{width:100%;max-width:640px;aspect-ratio:480/150;background:#0a0812;border:1px solid var(--line);margin-top:8px;display:block}.pevi{display:grid;gap:5px;align-content:start}.pevi>b{font:900 1.05rem var(--body);color:var(--pop)}.pevi>small{font:700 .74rem var(--body);color:var(--cyan)}.pevx{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:8px;align-items:center;font:800 .8rem var(--body)}.pevx i{height:8px;background:#22222e;border:1px solid var(--line);display:block}.pevx em{display:block;height:100%;background:linear-gradient(90deg,#FF8AD8,#FFE27A)}.pevx small{font:700 .7rem var(--num);color:var(--muted)}.pevn{margin:0;font:700 .76rem/1.5 var(--body);color:var(--muted)}.pevn span.ok,.pevn.ok{color:#39E58C}.pevi .btn{justify-self:start;min-height:36px}.pevi .btn[disabled]{opacity:.5}.dglv .xg.pet{display:block;margin-top:2px;color:#FFB3C7}.sh span em{font-style:normal;color:var(--pop);font-size:.86em}.mnrdeco{display:flex;flex-wrap:wrap;gap:6px}.mnrdeco button{background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:700 .76rem var(--body);padding:6px 10px;cursor:pointer}.mnrdeco button.own{border-color:#39E58C;color:#39E58C;cursor:pointer}.mnrdeco button.own.dkoff{border-color:var(--line);color:var(--muted);border-style:dashed}.mnrdeco button[disabled]{opacity:.45;cursor:default}.hubm #dghp,.hubm #dgsk,.hubm #dgmm,.hubm #dgskb,.hubm #dgatk,.hubm #dglvh,.hubm #dgeq{display:none!important}.dgcut{position:absolute;left:0;right:0;top:9%;z-index:4;pointer-events:none;opacity:0;--uc:#3CF0FF}.dgcut.on{animation:dgcut .85s ease-out forwards}.dgcut i{position:absolute;left:-10%;right:-10%;top:-6px;bottom:-6px;background:linear-gradient(90deg,transparent,rgba(9,9,13,.88) 14%,rgba(9,9,13,.88) 86%,transparent);border-top:2px solid var(--uc);border-bottom:2px solid var(--uc);transform:skewY(-4deg);box-shadow:0 0 18px var(--uc)}.dgcut b{position:relative;display:block;text-align:center;font:900 clamp(1.2rem,4.4vw,2.2rem)/1.1 var(--disp);color:#fff;text-shadow:0 0 10px var(--uc),0 0 26px var(--uc),3px 3px 0 #000;letter-spacing:.1em;padding:5px 0}.dgcut small{display:block;font:800 .78rem var(--hud);color:var(--uc);letter-spacing:.5em;text-shadow:none;margin-bottom:2px}@keyframes dgcut{0%{opacity:0;transform:translateX(-45%) skewX(-14deg)}14%{opacity:1;transform:translateX(0) skewX(-6deg)}78%{opacity:1;transform:translateX(3%) skewX(-6deg)}100%{opacity:0;transform:translateX(45%) skewX(-14deg)}}#dgultb{position:absolute;left:-74px;bottom:0;width:62px;height:62px;background:radial-gradient(circle at 50% 40%,var(--uc,#3CF0FF),rgba(9,9,13,.75) 72%);overflow:hidden}#dgultb i{position:absolute;left:0;right:0;bottom:0;background:rgba(7,6,10,.7);pointer-events:none}#dgultb.rdy{box-shadow:0 0 16px var(--uc,#3CF0FF)}#dgultb[hidden],#dgulth[hidden]{display:none!important}
.frme{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px 10px;background:var(--panel);padding:8px 12px;margin:6px auto;max-width:520px;clip-path:var(--cut)}.frme span{font:700 .78rem var(--body);color:var(--muted)}.frme b{font:1.15rem var(--num);color:var(--pop);letter-spacing:.12em}.frme small{flex-basis:100%;text-align:center;font:600 .72rem var(--body);color:var(--muted)}.frme .btn{min-height:30px;padding:0 10px;font-size:.78rem}
.frl{list-style:none;padding:0;margin:6px auto;display:grid;gap:5px;max-width:520px}.frl li{display:grid;grid-template-columns:1fr auto;gap:2px 8px;align-items:center;background:var(--panel);padding:7px 10px;text-align:left;clip-path:var(--cut)}.frl .frn{font:800 .86rem var(--body)}.frl .frn em{font:700 .7rem var(--num);color:var(--pop);font-style:normal}.frl .frs{grid-column:1;font:600 .72rem var(--body);color:var(--muted)}.frl .frb{grid-column:2;grid-row:1/3;display:flex;gap:4px}.frl .frb .btn{min-height:30px;padding:0 9px;font-size:.76rem}.frd{display:inline-block;width:8px;height:8px;border-radius:50%;background:#55556a;margin-right:6px;vertical-align:1px}.frl li.on .frd{background:#39E58C;box-shadow:0 0 6px #39E58C}.frl li.on .frs{color:#39E58C}
.fbc{display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin:8px auto;max-width:560px}.fbc button{background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:700 .8rem var(--body);padding:6px 10px;cursor:pointer}.fbc button.on{border-color:var(--pop);color:var(--pop);background:rgba(255,230,0,.08)}.fbs{display:flex;justify-content:center;align-items:center;gap:2px;margin:6px 0}.fbs span{font:700 .8rem var(--body);color:var(--muted);margin-right:8px}.fbs button{background:none;border:0;font-size:1.6rem;line-height:1;color:#44445a;cursor:pointer;padding:2px}.fbs button.on{color:#FFE600;text-shadow:0 0 8px rgba(255,230,0,.5)}.fbp textarea{display:block;width:min(560px,100%);margin:6px auto 0;background:var(--panel);border:1px solid var(--line);color:var(--ink);font:500 .9rem/1.5 var(--body);padding:10px;resize:vertical;box-sizing:border-box}.fbp textarea:focus{outline:2px solid var(--pop)}.fbn{font:600 .7rem var(--num);color:var(--muted);text-align:right;width:min(560px,100%);margin:2px auto}.fbok{font:800 1.1rem var(--body);color:#39E58C;margin:18px 0}
.dgfeed{position:absolute;left:8px;top:96px;z-index:3;display:flex;flex-direction:column;align-items:flex-start;gap:3px;pointer-events:none;width:min(60%,320px)}.dgfeed .fd{font:800 .76rem var(--body);background:rgba(10,10,18,.72);border-left:3px solid currentColor;padding:2px 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;animation:dgfd .25s ease-out}.dgfeed .fd.on{animation:dgfd .25s ease-out}@keyframes dgfd{from{transform:translateX(-14px);opacity:0}to{transform:none;opacity:1}}.hubm .dgfeed{display:none}#dggsi{display:flex;justify-content:center;min-height:44px;margin:4px 0 8px;background:none}#dggsi iframe{color-scheme:light}@media (max-width:560px),(max-height:480px){.dgfeed{width:min(62%,250px);gap:2px}.dgfeed .fd{font-size:.68rem;padding:1px 6px;background:rgba(10,10,18,.6)}}
.dgfinv{position:absolute;left:50%;top:120px;transform:translateX(-50%);z-index:6;display:flex;gap:8px;align-items:center;background:rgba(10,10,18,.94);border:2px solid var(--pop);padding:8px 10px;font:800 .82rem var(--body);color:#fff;box-shadow:0 6px 18px rgba(0,0,0,.5);max-width:94%}.dgfinv[hidden]{display:none}.dgfinv .btn{min-height:30px;padding:0 10px;font-size:.78rem}
#dgparb{position:absolute;right:11px;left:auto;bottom:88px;width:56px;height:56px;background:radial-gradient(circle at 50% 40%,#FFF6EC,rgba(9,9,13,.75) 72%);color:#111;overflow:hidden;text-shadow:0 0 3px #fff}#dgparb i{position:absolute;left:0;right:0;bottom:0;background:rgba(7,6,10,.7);pointer-events:none}#dgparb.rdy{box-shadow:0 0 14px #FFE27A}#dgtwb{position:absolute;right:11px;left:auto;bottom:156px;width:56px;height:56px;background:radial-gradient(circle at 50% 40%,#F0C98A,rgba(9,9,13,.78) 72%);color:#111;text-shadow:0 0 3px #fff;overflow:visible}#dgtwb b{position:absolute;right:-4px;top:-4px;background:#111;color:#FFE27A;border:1px solid #FFE27A;font:900 .62rem var(--num);padding:1px 4px;line-height:1.2;text-shadow:none}#dgtwb[hidden],#dgtwh[hidden]{display:none!important}#dgtwb.c1{box-shadow:0 0 12px 2px #fff}#dgtwb.c2{box-shadow:0 0 18px 4px #FFA53C}#dgtwb.c3{box-shadow:0 0 26px 7px #9FEFFF;animation:dgpw .18s ease-in-out infinite alternate}.dgtwh{border-color:#F0C98A}.dgtwh b{background:#F0C98A;color:#111}.dgtwh.c3{box-shadow:0 0 14px #9FEFFF}.dgsplash h2[data-egg]{cursor:default;user-select:none;-webkit-user-select:none}.dgsplash h2.eggp{animation:dgegp .18s ease-out}.dgsplash h2.eggr{animation:dgegr .65s linear 4}@keyframes dgegp{50%{transform:scale(1.06) rotate(-1.5deg)}}@keyframes dgegr{from{filter:hue-rotate(0deg)}to{filter:hue-rotate(360deg)}}.eggl{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px;margin:6px 0}.egg{background:var(--panel2);border:1px dashed var(--line);padding:6px 8px;display:grid;gap:2px;text-align:left}.egg b{font:800 .8rem var(--body);color:var(--muted)}.egg small{font:600 .68rem/1.4 var(--body);color:var(--muted)}.egg.on{border-style:solid;border-color:#FFE27A}.egg.on b{color:#FFE27A}.dg.tch .dgsk,.dg.tch .dgparh,.dg.tch .dgtwh{display:none!important}#dgend,#dgpause{background:rgba(7,6,10,.95)}.dgws{display:grid;gap:6px;justify-items:center;max-width:520px;margin:10px auto 4px;padding:10px 12px;border:2px solid var(--pop);background:rgba(255,230,0,.07);animation:dgcop .35s ease-out}.dgws b{font:900 .95rem var(--body);color:var(--pop)}.dgws span{font:600 .8rem/1.5 var(--body);color:var(--ink)}.dgrsm{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px 10px;margin:6px 0;padding:8px 10px;border:2px solid var(--cyan);background:rgba(60,240,255,.07);font:700 .82rem var(--body)}.dgrsm .btn{min-height:34px;padding:0 12px;font-size:.8rem}.dghelp{max-width:620px;margin:10px auto 0;text-align:left}.dghelp summary{cursor:pointer;font:800 .85rem var(--body);color:var(--muted);text-align:center}.dghelp .ctrl{font:600 .76rem/1.6 var(--body);color:var(--muted)}.dg.tch .dgcard:has(.cmini){width:auto;max-width:70%;padding:4px 10px;border-width:1px}.dg.tch .dgcard:has(.cmini) .cb,.dg.tch .dgcard .cmini .st{display:none}.dg.tch .dgcard .cmini b{font-size:.74rem}.dgperk{background:rgba(7,6,12,.9)}#dgerr{position:absolute;left:8px;right:8px;bottom:max(8px,env(safe-area-inset-bottom));z-index:9;background:rgba(120,0,16,.92);color:#fff;font:700 .72rem/1.4 var(--body);padding:6px 10px;border:1px solid #FF6B78;pointer-events:auto;word-break:break-all}#dgerr[hidden]{display:none}.dgchb{flex:none;white-space:nowrap}.dgchb[aria-pressed=true]{border-color:var(--y,#FFE600)!important;color:var(--y,#FFE600)}.dgchh{max-height:min(38vh,260px);overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;display:flex;flex-direction:column;gap:3px;padding:4px 2px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);font:500 .78rem/1.45 var(--body);color:#e8e8ef}.dgchh div{word-break:break-all}.dgchh i{font-style:normal;color:#8a8a99;font-size:.68rem;margin-right:5px}.dgchh b{color:#7FD8FF;margin-right:5px}.dgchh .me b{color:#FFE600}.dgchh .sys{color:#9a9aaa;font-size:.72rem}.dg,.dg *{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none;-webkit-tap-highlight-color:transparent}.dg input,.dg textarea,.dg [contenteditable]{-webkit-user-select:text;user-select:text;-webkit-touch-callout:default}.dg button,.dgpad,.dg canvas{touch-action:manipulation}.dg,.dgov{overscroll-behavior:contain}.dgios{position:absolute;left:50%;top:max(56px,env(safe-area-inset-top));transform:translateX(-50%);z-index:8;width:min(92%,520px);display:flex;gap:8px;align-items:center;background:rgba(10,10,18,.94);border:2px solid var(--cyan);padding:8px 10px;font:700 .76rem/1.5 var(--body);color:var(--ink);pointer-events:auto}.dgios[hidden]{display:none}.dgios b{color:var(--cyan)}.dgios button{flex:none;background:var(--pop);color:#111;border:0;font:800 .74rem var(--body);padding:6px 10px;cursor:pointer}.pkc{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;max-width:640px;margin:8px auto 0}.pkc button{display:grid;gap:4px;justify-items:center;align-content:start;background:var(--panel);border:2px solid var(--line);color:var(--ink);padding:12px 8px;cursor:pointer;font:600 .76rem/1.45 var(--body);transition:transform .12s,border-color .12s}.pkc button:hover,.pkc button:focus-visible{border-color:var(--pop);transform:translateY(-2px)}.pkc i{font-style:normal;font-size:1.8rem;line-height:1}.pkc b{font:900 .92rem var(--body);color:var(--pop)}.pkc b small{font:800 .7rem var(--num);color:var(--cyan)}.pkc span{color:var(--muted)}@media (max-width:560px){.pkc{grid-template-columns:1fr}.pkc button{grid-template-columns:40px 1fr;justify-items:start;text-align:left;padding:8px 10px}.pkc i{grid-row:1/3;align-self:center;font-size:1.5rem}}.pkl{display:flex;flex-wrap:wrap;justify-content:center;gap:4px;margin:4px auto 8px;max-width:620px}.pkl span{font:700 .72rem var(--body);background:var(--panel2);border:1px solid var(--line);padding:2px 7px}.dgach .tl{max-width:720px;text-align:left}.dgach h2,.dgach .sub{text-align:center}.qrow,.ach{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 10px;align-items:center;background:var(--panel);border:1px solid var(--line);padding:7px 10px;margin:4px 0}.qrow b,.ach b{font:800 .84rem var(--body)}.qrow small,.ach small{display:block;font:600 .7rem var(--body);color:var(--muted)}.qrow i,.ach i,.evbox i{display:block;height:4px;background:rgba(255,255,255,.08);margin:4px 0 2px;position:relative}.qrow i::after,.ach i::after,.evbox i::after{content:"";position:absolute;inset:0 auto 0 0;width:var(--p);background:var(--pop)}.qrow.ok,.ach.ok{border-color:var(--pop)}.qrow.got,.ach.got{opacity:.6}.qrow em{font:700 .72rem var(--body);color:var(--muted);font-style:normal}.qrow .btn,.ach .btn{min-height:30px;padding:0 10px;font-size:.74rem}.ach{grid-template-columns:1fr}.ach span{font:700 .72rem var(--body);color:var(--muted)}.achl{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:0 8px}.ttl{display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin:4px 0 8px}.ttl small{font:700 .72rem var(--body);color:var(--muted)}.ttl button{background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:700 .74rem var(--body);padding:4px 8px;cursor:pointer}.ttl button[aria-pressed="true"]{border-color:var(--pop);color:var(--pop)}.evbox{display:block;border:2px solid #7CFFB2;background:rgba(124,255,178,.07);padding:8px 10px;margin:6px 0 10px}.evbox b{font:900 .9rem var(--body);color:#7CFFB2}.evbox small{display:block;font:600 .74rem var(--body);color:var(--ink)}.evbox span{font:700 .72rem var(--body);color:var(--muted)}.evbox i::after{background:#7CFFB2}.ttlb{font:800 .7rem var(--body);color:var(--pop);margin-left:4px}.fdx{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px;margin:6px 0 12px;text-align:left}.fdc{display:grid;grid-template-columns:40px 1fr;gap:2px 8px;align-items:center;background:var(--panel);border:1px solid var(--line);padding:6px}.fdc img{grid-row:1/3;width:40px;height:40px;object-fit:contain;image-rendering:pixelated}.fdc b{font:800 .78rem var(--body)}.fdc small{font:600 .66rem var(--body);color:var(--muted)}.fdc span{grid-column:1/-1;font:600 .66rem/1.4 var(--body);color:var(--ink)}.fdc.lock b{color:var(--muted)}.dlockd{margin:10px 0}.dlockd summary{cursor:pointer;font:800 .9rem var(--body);color:var(--muted)}.dlock .lt.lock img{filter:brightness(0) opacity(.55)}.dlock .lt.lock{opacity:.8}.dgcoach{position:absolute;left:50%;transform:translateX(-50%);z-index:4;display:flex;align-items:center;gap:8px;max-width:min(92%,460px);background:rgba(10,10,18,.9);border:2px solid var(--pop);padding:7px 8px 7px 12px;font:800 .82rem/1.45 var(--body);color:var(--ink);box-shadow:0 4px 18px rgba(0,0,0,.5);pointer-events:auto}.dgcoach[hidden]{display:none}.dgcoach.pop{animation:dgcop .35s ease-out}.dgcoach button{flex:none;background:none;border:1px solid var(--line);color:var(--muted);font:700 .7rem var(--body);padding:3px 8px;cursor:pointer}@keyframes dgcop{from{transform:translate(-50%,-8px);opacity:0}to{transform:translate(-50%,0);opacity:1}}.nrule{max-width:34em;margin:6px auto 10px;text-align:left;font:600 .78rem/1.55 var(--body);color:var(--muted)}.nrule summary{cursor:pointer;text-align:center;color:var(--ink);font-weight:800;padding:6px}.nrule ul{margin:4px 0 0;padding-left:1.2em}.nrule li{margin:2px 0}#dgparb.warn,.dgparh.warn{animation:dgpw .25s ease-in-out infinite alternate;box-shadow:0 0 22px 4px #FFE27A}@keyframes dgpw{from{transform:scale(1)}to{transform:scale(1.12)}}#dgparb[hidden],#dgparh[hidden]{display:none!important}.dgparh{border-color:#E8DCC0}.dgparh b{background:#E8DCC0;color:#111}.dgparh em{position:absolute;left:0;right:0;bottom:0;background:rgba(7,6,10,.7);pointer-events:none}.dgparh.rdy{box-shadow:0 0 10px rgba(255,226,122,.6)}.dgulth{border-color:var(--uc,#3CF0FF)}.dgulth b{background:var(--uc,#3CF0FF);color:#111}.dgulth.rdy{border-color:var(--uc,#3CF0FF);box-shadow:0 0 10px var(--uc,#3CF0FF)}.dgult{max-width:600px;margin:8px auto;text-align:left}.dgult>b{font:800 .86rem var(--body);color:var(--pop)}.dgult div{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px;margin-top:6px}.dgult button{display:grid;gap:2px;text-align:left;background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--uc);color:var(--ink);font:800 .8rem var(--body);padding:6px 8px;cursor:pointer}.dgult button small{font:600 .66rem/1.35 var(--body);color:var(--muted)}
.dgult button em{font-style:normal;font-size:.62rem;background:var(--uc);color:#111;padding:0 4px;margin-right:5px;vertical-align:1px}.dgult button.on{border-color:var(--uc);box-shadow:0 0 0 1px var(--uc)}.dgult button[disabled]{opacity:.45;cursor:default}#dgultb.cbh,.dgulth.cbh{animation:dgcbh .5s ease-in-out infinite alternate}@keyframes dgcbh{from{box-shadow:0 0 6px #FFE27A}to{box-shadow:0 0 22px #FFE27A,0 0 0 3px #FFE27A}}.dgdown{position:absolute;left:50%;top:54%;transform:translateX(-50%);z-index:6;width:min(380px,92%);background:rgba(9,9,13,.93);border:2px solid #FF2E3B;box-shadow:0 0 18px rgba(255,46,59,.35);padding:10px 12px;display:grid;gap:6px;text-align:center;pointer-events:auto}.dgdown[hidden]{display:none}.dgdown>b{font:900 1.05rem var(--body);color:#FF6B78}.dgdown p{margin:0;font:600 .76rem/1.5 var(--body);color:var(--muted)}.dgdpb{display:block;height:8px;background:#22222e;border:1px solid var(--line)}.dgdpb em{display:block;height:100%;width:0;background:linear-gradient(90deg,#39E58C,#3CF0FF)}.dgdown small{font:700 .72rem var(--body);color:#39E58C}.dgdown small.no{color:#9a9aaa}.dgdown .spec{background:none;border:1px solid var(--line);color:var(--cyan);font:700 .74rem var(--body);padding:3px 10px;cursor:pointer;justify-self:center}.dgdb{display:flex;flex-wrap:wrap;gap:6px;justify-content:center}.dgdb .btn{min-height:34px;font-size:.8rem;padding:0 12px}.dgdb .btn.warn{border-color:#FF2E3B;color:#FF6B78}.dgdb .btn[disabled]{opacity:.45}.dgdown.min{top:auto;bottom:16%;width:min(320px,88%);padding:6px 10px;gap:4px}.dgdown.min>b{font-size:.86rem}@media (max-width:640px){.dgdown{top:38%}.dgdown.min{top:auto;bottom:22%}}.dgsex .sexc{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin:12px auto}.dgsex .sexc button{display:grid;gap:6px;justify-items:center;background:var(--panel2);border:2px solid var(--line);color:var(--ink);padding:10px 14px;cursor:pointer;min-width:150px}.dgsex .sexc button:hover,.dgsex .sexc button:focus-visible{border-color:var(--pop);box-shadow:0 0 0 1px var(--pop)}.dgsex .sexc canvas{width:200px;height:96px;image-rendering:pixelated;image-rendering:crisp-edges}.dgsex .sexc b{font:900 1rem var(--body)}.shsex{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin:6px 0;font:700 .84rem var(--body)}.shsex .btn{min-height:32px;font-size:.78rem;padding:0 12px}.dgbub.pet{background:#FFF0F7;color:#3a1830;max-width:170px}.pcb{display:flex;flex-wrap:wrap;gap:4px}.pcb .btn{min-height:32px;font-size:.74rem;padding:0 9px}.pneed{display:grid;gap:4px;margin:6px 0;font:700 .76rem var(--body);color:var(--muted)}.pneed b{color:var(--ink)}.pneed .pbar{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:6px;align-items:center}.pneed .pbar i{height:7px;background:#22222e;border:1px solid var(--line);display:block}.pneed .pbar em{display:block;height:100%}.pneed small{font:600 .68rem/1.5 var(--body)}.dgbub.lov{background:#fff;border:2px solid #FF8AD8;max-width:200px}.lvst{display:flex;flex-wrap:wrap;gap:4px 12px;font:700 .74rem var(--body);color:var(--muted);padding:2px 0}.lvst b{font-weight:900}.lh{color:#FF5CA8;letter-spacing:-1px}.lh i{font-style:normal;color:#55556A}.lvact{display:flex;flex-wrap:wrap;gap:5px;margin:4px 0}.lvact .btn{min-height:32px;font-size:.76rem;padding:0 10px}.lvact .btn[disabled]{opacity:.45}.lvact .btn.warn{border-color:#FF2E3B;color:#FF6B78}.lvgift .mu{margin:4px 0}.lvbuy{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}.lvbuy .btn{min-height:32px;font-size:.78rem}.lvbuy .btn[disabled]{opacity:.45}.lvinv{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:5px;max-height:240px;overflow:auto}.lvinv button{display:grid;grid-template-columns:34px minmax(0,1fr);grid-template-rows:auto auto;column-gap:6px;align-items:center;text-align:left;background:var(--panel2);border:1px solid var(--line);color:var(--ink);padding:4px;cursor:pointer}.lvinv button[disabled]{opacity:.45;cursor:default}.lvinv img{grid-row:1/3;width:34px;height:34px;object-fit:cover}.lvinv span{font:700 .68rem/1.3 var(--body);overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.lvinv small{font:600 .64rem var(--body);color:var(--muted)}.dgprop{top:30%;border-color:#FF5CA8;box-shadow:0 0 18px rgba(255,92,168,.4)}.dgprop>b{color:#FF8AD8}.dgmates .mry{border-color:#FF5CA8;color:#FF8AD8}.dgsplash{display:flex;flex-direction:column;align-items:center;gap:10px;padding:10px 0 4px}.dgsplash h2{margin:0}.dgsplash .sub{margin:0}#dghero{width:220px;height:110px;image-rendering:pixelated;image-rendering:crisp-edges;filter:drop-shadow(0 6px 10px rgba(0,0,0,.6))}.dgbig{font-size:1.2rem!important;min-height:58px!important;padding:0 46px!important;animation:dgpulse 1.6s ease-in-out infinite}@keyframes dgpulse{50%{transform:scale(1.04)}}@media (prefers-reduced-motion:reduce){.dgbig{animation:none}}.dgme{margin:0;font:700 .8rem var(--body);color:var(--muted)}.dgme b{color:#FFE600}.dgfoot{display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap;margin-top:4px}.dgfoot>button,.mfoot>button{background:none;border:1px solid var(--line);color:var(--muted);font:700 .74rem var(--body);padding:5px 10px;cursor:pointer}.dgrate1{font:800 .66rem var(--body);border:1px solid #FF5C6B;color:#FF8A95;padding:3px 6px}.dgfoot .dglog,.mfoot .dglog{margin:0;max-width:min(520px,92vw)}.dgfoot .dglog summary,.mfoot .dglog summary{border:1px solid var(--line);padding:5px 10px;font:700 .74rem var(--body);color:var(--muted);cursor:pointer;list-style:none}.dgfoot .dglog[open] ul,.mfoot .dglog[open] ul{text-align:left}.dgmenu{max-width:600px;margin:0 auto;display:flex;flex-direction:column;gap:9px}.mhead{background:var(--panel);border:1px solid var(--line);padding:8px 10px;display:grid;gap:6px}.dgmenu .dglv{margin:0}.dgmenu .lvr{display:none}.mme{display:flex;flex-wrap:wrap;gap:4px 16px;justify-content:center;font:700 .82rem var(--body);color:var(--muted)}.mme b{color:var(--ink)}.mme button{background:none;border:0;cursor:pointer;font-size:.82rem;padding:0 2px}.dgmenu .dgday{margin:0}.mplay{display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:8px}.mcard{display:grid;justify-items:center;align-content:center;gap:3px;padding:14px 6px;background:var(--panel2);border:2px solid #3CF0FF;color:var(--ink);cursor:pointer;min-height:92px}.mcard i{font-style:normal;font-size:1.6rem;line-height:1}.mcard b{font:900 1rem var(--body)}.mcard small{font:700 .68rem var(--body);color:var(--muted)}.mcard.y{background:#FFE600;border-color:#FFE600;color:#111;box-shadow:0 0 16px rgba(255,230,0,.35)}.mcard.y small{color:#5a4b00}.mcard:hover,.mcard:focus-visible{transform:translateY(-2px)}.mgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:6px}.mgrid button{position:relative;display:grid;justify-items:center;gap:3px;padding:9px 2px;background:var(--panel);border:1px solid var(--line);color:var(--ink);cursor:pointer}.mgrid i{font-style:normal;font-size:1.35rem;line-height:1}.mgrid span{font:800 .74rem var(--body)}.mgrid em{position:absolute;top:2px;right:4px;font:800 .62rem var(--body);font-style:normal;color:#FFE600}.mfoot{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap}.dgmenu .dgdiff{margin:0 auto}.dgmenu .dgdiffn{margin:0 auto;font-size:.66rem}.dgset{max-width:540px;margin:0 auto;text-align:center;display:flex;flex-direction:column;gap:8px}.dgset h3{margin:0;font:900 1.2rem var(--body);color:var(--pop)}.dgset h4{margin:4px 0 0;font:800 .9rem var(--body)}.dgset .ctrl,.dgset .dgrate{text-align:center;margin:0}.dgset .dgbt{justify-content:center}@media (max-width:560px){.mplay{grid-template-columns:1fr 1fr}.mplay .mcard.y{grid-column:1/-1;min-height:84px}.mgrid{grid-template-columns:repeat(3,1fr)}#dghero{width:180px;height:90px}}.mme .addc{margin-left:4px;width:22px;height:22px;border:1px solid #FFE600!important;color:#FFE600;font:900 .9rem/1 var(--body);background:none;cursor:pointer;padding:0}.pks .pk[disabled]{opacity:.4;cursor:default}.dg img[src^="data:image/png"]{image-rendering:pixelated;image-rendering:crisp-edges}.gc .gs{position:absolute;left:0;top:0;text-shadow:none;color:#fff;font-size:.62rem;line-height:1;font-weight:400;background:rgba(0,0,0,.7);padding:2px 3px}.gpflt{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 6px}.gpflt button{background:var(--panel2);border:1px solid var(--line);color:var(--muted);font:700 .7rem var(--body);padding:3px 8px;cursor:pointer}.gpflt button[aria-pressed="true"]{background:var(--pop);border-color:var(--pop);color:#111}.lvsh{font:800 .78rem var(--body);color:var(--ink);margin:8px 0 4px}.lvsh small{font-weight:600;color:var(--muted);margin-left:4px}.lvgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px;max-height:300px;overflow:auto}.lvg{display:grid;grid-template-columns:54px minmax(0,1fr) auto;grid-template-rows:auto auto auto;column-gap:8px;row-gap:2px;align-items:center;background:var(--panel2);border:1px solid var(--line);padding:6px;text-align:left}.lvg.fav{border-color:#FF5CA8}.lvg img{grid-row:1/4;width:54px;height:54px;object-fit:cover;background:#fff}.lvgn{grid-column:2/4;font:700 .74rem/1.3 var(--body);color:var(--ink);overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.lvg small{grid-column:2/4;font:600 .66rem var(--body);color:var(--muted)}.lvg .btn{grid-column:3;grid-row:3;padding:4px 10px;font-size:.72rem;min-height:0;clip-path:none}.lvg .btn[disabled]{opacity:.45}.lvg a{grid-column:2;grid-row:3;font:600 .64rem var(--body);color:var(--muted);text-decoration:underline;white-space:nowrap}.lvstall .fine{font-size:.64rem;color:var(--muted);margin:4px 0 0}.mplay{grid-template-columns:repeat(4,1fr)}@media (max-width:560px){.mplay{grid-template-columns:repeat(3,1fr)}.mplay .mcard.y{grid-column:1/-1}.mplay .mcard{min-height:78px;padding:10px 4px}}.mats{display:flex;flex-wrap:wrap;gap:4px 12px;font:700 .74rem var(--body);color:var(--muted);background:var(--panel);border:1px solid var(--line);padding:5px 8px}.mats b{color:var(--ink)}.cost{display:flex;flex-wrap:wrap;gap:3px 10px;font:700 .72rem var(--body)}.cost .ok{color:#39E58C}.cost .no{color:#FF6B78}.cost small{color:var(--muted);font-weight:600;margin-left:2px}.gptab{display:flex;gap:6px}.gptab button{flex:1;background:var(--panel2);border:1px solid var(--line);color:var(--muted);font:800 .82rem var(--body);padding:7px;cursor:pointer}.gptab button[aria-pressed="true"]{background:var(--pop);border-color:var(--pop);color:#111}.gc .gst{position:absolute;left:1px;bottom:0;font-style:normal;font-size:.5rem;line-height:1;color:#FFE600;text-shadow:1px 1px 0 #000;letter-spacing:-1px}.gpdt .stars{font-style:normal;color:#FFE600;font-size:.78rem;letter-spacing:-1px}.gpcost{grid-column:1/-1;display:grid;gap:3px;background:var(--panel2);border:1px dashed var(--line);padding:6px 8px}.gpcost small{font:600 .68rem var(--body);color:var(--muted)}.gpda .btn.rk{border-color:#3CF0FF;box-shadow:0 0 8px rgba(60,240,255,.4)}.gc.t-ur{animation:urb 2.4s linear infinite}@keyframes urb{0%,100%{border-color:#3CF0FF;box-shadow:0 0 8px rgba(60,240,255,.6)}33%{border-color:#FF5CA8;box-shadow:0 0 10px rgba(255,92,168,.6)}66%{border-color:#FFE600;box-shadow:0 0 10px rgba(255,230,0,.6)}}@media (prefers-reduced-motion:reduce){.gc.t-ur{animation:none}}.craft{display:grid;gap:8px}.craft .ch{font:900 .9rem var(--body);color:var(--pop);margin-top:4px}.craft .mu{margin:0}.cpos,.ctier{display:flex;flex-wrap:wrap;gap:5px}.cpos button,.ctier button{background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:800 .76rem var(--body);padding:5px 10px;cursor:pointer}.cpos button[aria-pressed="true"],.ctier button[aria-pressed="true"]{border-color:var(--pop);box-shadow:0 0 0 1px var(--pop);color:var(--pop)}.cbase{display:grid;grid-template-columns:repeat(auto-fill,minmax(64px,1fr));gap:5px;max-height:190px;overflow:auto}.cbase button{display:grid;justify-items:center;gap:2px;background:#15151f;border:1px solid var(--line);color:var(--muted);padding:4px 2px;cursor:pointer}.cbase button img{width:40px;height:40px}.cbase button small{font:700 .62rem var(--body)}.cbase button[aria-pressed="true"]{border-color:var(--pop);color:var(--pop)}.cout,.lt2{display:grid;grid-template-columns:56px minmax(0,1fr) auto;gap:8px;align-items:center;background:var(--panel);border:1px solid var(--line);padding:8px}.cout img,.lt2 img{width:56px;height:56px}.cout b,.lt2 b{font:800 .86rem var(--body);display:block}.cout small,.lt2 small{font:600 .68rem var(--body);color:var(--muted);display:block}.cout .btn,.lt2 .btn{min-height:36px;font-size:.8rem;padding:0 14px}.cout .btn[disabled],.lt2 .btn[disabled]{opacity:.45}.cltd{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:6px}.lt2.lock{opacity:.55}.lt2.lock img{filter:grayscale(1) brightness(.6)}
.talg{list-style:none;padding:0;margin:8px 0;display:grid;gap:6px}.talg li{display:grid;grid-template-columns:1fr auto;gap:2px 10px;align-items:center;background:var(--panel);padding:7px 10px;text-align:left;clip-path:var(--cut)}.talg .tn{font:800 .86rem var(--body)}.talg .tn em{font:700 .72rem var(--num);color:var(--pop);font-style:normal;margin-left:4px}.talg small{grid-column:1;font:600 .7rem/1.3 var(--body);color:var(--muted)}.talg i{grid-column:1;display:block;height:4px;background:rgba(255,255,255,.08)}.talg i em{display:block;height:100%;background:var(--pop)}.talg .tb{grid-column:2;grid-row:1/4;display:flex;gap:4px}.talg .tb .btn{min-height:32px;min-width:34px;padding:0 8px;font-size:.85rem}.talg .tb .btn:disabled{opacity:.4;cursor:not-allowed}
.dgdps{position:absolute;left:50%;top:84px;transform:translateX(-50%);z-index:4;display:flex;gap:6px;align-items:center;background:rgba(10,10,18,.86);border:1px solid var(--pop);padding:4px 6px 4px 10px;font:800 .74rem var(--body);color:#fff;white-space:nowrap;max-width:96%}.dgdps span{overflow:hidden;text-overflow:ellipsis}.dgdps .btn{min-height:26px;padding:0 8px;font-size:.72rem}.hubm .dgdps,.dgdps[hidden]{display:none}
.r-mr{background:linear-gradient(90deg,#FF4FD8,#7A1FFF 50%,#FF4FD8);color:#fff}
.gc.t-mr{border-color:#FF4FD8;box-shadow:0 0 10px rgba(255,79,216,.7)}
.slot.t-mr{border-color:#FF4FD8;box-shadow:0 0 8px #FF4FD8}
.lt.t-mr{box-shadow:inset 0 0 0 2px #FF4FD8}
.cbase button img,.cout img,.lt2 img,.cline img,.gpdi img,.gc img{image-rendering:pixelated}
.cdesc{color:var(--ink)!important;opacity:.85;line-height:1.45;margin:2px 0}
.cline{display:flex;flex-wrap:wrap;align-items:center;gap:3px;background:#15151f;border:1px solid var(--line);padding:6px}
.cline span{display:grid;justify-items:center;width:56px;gap:2px;background:none}
.cline img{width:44px;height:44px}
.cline small{font:700 .56rem var(--body);text-align:center;line-height:1.2;padding:1px 2px}
.cline i{color:var(--muted);font-style:normal}
.need{list-style:none;margin:4px 0;padding:0;font:700 .68rem var(--body);line-height:1.4}
.need .ok{color:#39E58C}
.need .no{color:#FF9AA4}
.lt2.myth{border-color:#FF4FD8}
.msrc{background:var(--panel);border:1px solid var(--line);padding:6px 8px;font:600 .74rem var(--body)}
.msrc summary{cursor:pointer;font-weight:800;color:var(--ink)}
.msrc ul{list-style:none;margin:6px 0;padding:0;display:grid;gap:5px}
.msrc li small{display:block;color:var(--muted);font-weight:600}
.gpdt .afl{color:#FFE27A}
.gpdt .ldesc{color:var(--ink);opacity:.8;line-height:1.4}
.dgck{display:flex;flex-wrap:wrap;gap:6px;align-items:center;justify-content:center;margin:6px 0}
.dgck small{font:700 .74rem var(--body);color:var(--muted)}
.dgck button{background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:800 .76rem var(--body);padding:4px 10px;cursor:pointer}
.dgck button[aria-pressed="true"]{border-color:var(--pop);color:var(--pop);box-shadow:0 0 0 1px var(--pop)}
.dgdate{flex-direction:column;flex-wrap:nowrap;align-items:center;justify-content:flex-end;padding:0 0 14px;background:#07060a}
.dgdate canvas{position:relative;flex:none;width:min(100%,calc(64vh * 16 / 9));height:auto;margin:0 auto auto;image-rendering:pixelated;image-rendering:crisp-edges;border-bottom:2px solid var(--line)}
.dgdate #dgdatel{position:relative;z-index:1;width:100%;display:flex;flex-direction:column;align-items:center}
.dpor{position:relative;z-index:1;flex:none;width:min(168px,40vw);max-height:30vh;object-fit:contain;image-rendering:pixelated;image-rendering:crisp-edges;margin:8px auto;filter:drop-shadow(0 4px 0 rgba(0,0,0,.4))}
.dchs{width:min(720px,94%);display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px;margin-top:6px}
.dchs .btn{min-height:42px;font-size:.86rem;white-space:normal;line-height:1.3}
.scbox img{width:64px}
.aib{display:inline-block;margin-left:6px;font:800 .62rem var(--hud);font-style:normal;color:var(--muted);border:1px solid var(--line);padding:0 4px}
.lvdates{display:grid;gap:6px;margin:8px 0}
.dtc{display:grid;gap:2px;text-align:left;background:var(--panel2);border:2px solid var(--line);color:var(--ink);padding:8px 10px;cursor:pointer}
.dtc b{font:900 .92rem var(--body)}.dtc small{font:600 .72rem var(--body);color:var(--muted)}.dtc em{font:800 .72rem var(--body);font-style:normal;color:var(--pop)}
.dtc[disabled]{opacity:.55;cursor:default}.dtc.lock em{color:var(--muted)}
.lvalb{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;margin:8px 0}
.alb{margin:0;background:var(--panel2);border:1px solid var(--line);padding:6px;text-align:center}
.alb img{width:100%;image-rendering:pixelated;image-rendering:crisp-edges}.alb figcaption{font:700 .7rem var(--body);color:var(--muted);margin-top:3px}
.dgnpch img{width:44px;height:auto}.dgstory{flex-direction:column;flex-wrap:nowrap;align-items:center;justify-content:flex-end;background:linear-gradient(180deg,transparent 40%,rgba(5,4,10,.75));padding:0 0 14px}.scbox{width:min(720px,94%);display:grid;grid-template-columns:auto minmax(0,1fr);gap:12px;align-items:center;background:rgba(10,9,16,.95);border:2px solid var(--pop);box-shadow:0 0 22px rgba(255,230,0,.25);padding:12px 14px;cursor:pointer}.scbox.nar{grid-template-columns:1fr;border-color:#55556a;box-shadow:none;text-align:center}.scbox img{width:72px;height:auto;min-height:48px;max-height:96px;object-fit:contain;image-rendering:pixelated;image-rendering:crisp-edges;background:radial-gradient(circle,#2a2440,#0a0812);border:1px solid var(--line);padding:4px}.sct b{font:900 .95rem var(--body);display:block;margin-bottom:3px}.sct p{margin:0;font:700 .95rem/1.6 var(--body);color:var(--ink)}.scbox.nar p{color:#C9C9D6;font-style:italic}.scbt{width:min(720px,94%);display:flex;align-items:center;gap:10px;margin-top:6px}.scbt span{font:700 .72rem var(--num);color:var(--muted);margin-left:auto}.scbt>button:first-child{background:none;border:1px solid var(--line);color:var(--muted);font:700 .74rem var(--body);padding:5px 10px;cursor:pointer}.scbt .btn{min-height:38px;font-size:.84rem;padding:0 16px}.dgstm{max-width:760px;margin:0 auto}.dgstm h3{margin:2px 0;font:900 1.25rem var(--body);color:var(--pop)}.chl{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:7px;margin:10px 0}.chc{display:grid;gap:2px;text-align:left;background:var(--panel2);border:2px solid var(--line);color:var(--ink);padding:9px 10px;cursor:pointer}.chc i{font:800 .7rem var(--hud);font-style:normal;color:var(--cyan)}.chc b{font:900 .96rem var(--body)}.chc small{font:600 .7rem var(--body);color:var(--muted)}.chc em{font:800 .72rem var(--body);font-style:normal;color:var(--pop)}.chc.done{border-color:#39E58C}.chc.done em{color:#39E58C}.chc.open{border-color:var(--pop);box-shadow:0 0 12px rgba(255,230,0,.25)}.chc.lock{opacity:.5;cursor:default}.chc.lock em{color:var(--muted)}.dgnick{margin:2px auto 6px;font:700 .8rem var(--body);color:var(--muted)}.dgnick b{color:var(--ink)}.dgcap{display:flex;align-items:center;justify-content:center;gap:6px;margin:6px auto;font:800 .8rem var(--body)}.dgcap span{color:var(--muted);margin-right:4px}.dgcap button{min-width:52px;min-height:32px;background:var(--panel2);border:1px solid var(--line);color:var(--ink);font:800 .8rem var(--body);cursor:pointer}.dgcap button.on{border-color:var(--pop);color:var(--pop);box-shadow:0 0 0 1px var(--pop)}.dgmates{display:grid;gap:5px;max-width:420px;margin:6px auto;text-align:left}.dgmates div{display:flex;flex-wrap:wrap;align-items:center;gap:6px;background:var(--panel2);border:1px solid var(--line);padding:5px 8px}.dgmates b{font:800 .82rem var(--body);margin-right:auto}.dgmates button{background:none;border:1px solid var(--line);color:var(--muted);font:700 .72rem var(--body);padding:3px 8px;cursor:pointer}.dgnick button{margin-left:8px;background:none;border:1px solid var(--line);color:var(--cyan);font:700 .74rem var(--body);padding:2px 8px;cursor:pointer}.dghp .bento{margin-left:6px;font:800 .78rem var(--body);color:#39E58C;text-shadow:1px 1px 0 #000}#dgcamp{align-items:flex-start}.dgbub{position:absolute;z-index:3;transform:translate(-50%,-100%);background:#fff;color:#111;font:900 .8rem var(--body);padding:3px 9px;border-radius:12px;white-space:nowrap;pointer-events:none;box-shadow:0 2px 0 rgba(0,0,0,.4)}.dgbub.tx{white-space:normal;width:max-content;max-width:190px;font-weight:700;line-height:1.35;overflow-wrap:anywhere}.dgbub.mt{background:#DFF8FF}
.dgrate{margin:6px auto 10px;max-width:520px;font:700 .78rem var(--body);color:#FFB27A;border:1px solid rgba(255,178,122,.4);padding:4px 10px;display:inline-block}
.dglog{margin:10px auto 0;max-width:520px;text-align:left;font-size:.78rem;color:var(--muted)}.dglog summary{cursor:pointer;text-align:center;color:var(--cyan)}.dglog ul{margin:6px 0 0;padding-left:1.2em}.dglog b{color:var(--pop)}
.dgfade{position:absolute;inset:0;z-index:6;background:#000;opacity:0;pointer-events:none;transition:opacity .4s}.dgfade.on{opacity:1}
/* games */
.gtabs{display:flex;gap:6px;flex-wrap:wrap;margin:18px 0 22px}
.gtabs button{border:1px solid var(--line);background:var(--panel);color:var(--muted);font:900 1rem var(--disp);padding:10px 20px;cursor:pointer;clip-path:var(--cut);letter-spacing:.06em}
.gtabs button[aria-selected="true"]{background:var(--pop);color:#09090D;border-color:var(--pop)}
.gpanel{background:var(--panel);padding:20px;clip-path:var(--cut)}
.gwrap{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px;align-items:center}
@media (max-width:820px){.gwrap{grid-template-columns:1fr}}
.gstage{min-height:420px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:center;perspective:1200px;position:relative}
.gstage::before{content:"";position:absolute;inset:10%;border-radius:50%;opacity:0;pointer-events:none;transition:opacity .4s}
.gstage.burst.t-ur::before{opacity:1;background:conic-gradient(from 0deg,#FF5CA8,#FFE600,#3CF0FF,#C77DFF,#FF5CA8);filter:blur(40px);animation:spin 3s linear infinite}
.gstage.burst.t-ssr::before{opacity:.9;background:radial-gradient(#FFC83D,transparent 65%);filter:blur(20px)}
.gstage.burst.t-sr::before{opacity:.7;background:radial-gradient(#C77DFF,transparent 65%);filter:blur(20px)}
@keyframes spin{to{transform:rotate(360deg)}}
.gc3{width:150px;aspect-ratio:3/4;position:relative}
.gc3.big{width:min(300px,78vw)}
.gci{position:absolute;inset:0;transform-style:preserve-3d;transition:transform .7s cubic-bezier(.3,1.4,.5,1)}
.gc3.flip .gci{transform:rotateY(180deg)}
.gcb,.gcf{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;clip-path:var(--cut)}
.gcb{background:repeating-linear-gradient(45deg,#1B1B26 0 10px,#13131B 10px 20px);display:grid;place-items:center;box-shadow:inset 0 0 0 3px var(--pop)}
.gcb b{white-space:pre;text-align:center;font:900 1.4rem/1.1 var(--disp);color:var(--pop);background:var(--bg);padding:14px 10px;clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%)}
.gc3:not(.big) .gcb b{font-size:.8rem;padding:8px 6px}
.gcf{transform:rotateY(180deg);background:var(--panel2);text-decoration:none;display:grid;grid-template-rows:auto 1fr auto;padding:8px;gap:4px}
.gcf img{width:100%;aspect-ratio:1;object-fit:cover}
.gcf .rar{top:8px;left:8px}
.gcf .gn{font-size:.82rem;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.gcf .gp{font:1.3rem var(--num);color:var(--pop)}
.gc3:not(.big) .gcf .gn{font-size:.7rem;-webkit-line-clamp:2}.gc3:not(.big) .gcf .gp{font-size:1rem}
.gc3.t-ur .gcf{box-shadow:inset 0 0 0 3px #3CF0FF}.gc3.t-ssr .gcf{box-shadow:inset 0 0 0 3px var(--ssr)}.gc3.t-sr .gcf{box-shadow:inset 0 0 0 3px var(--sr)}
.gstage.charge .gc3{animation:shake .9s ease-in}
@keyframes shake{0%,100%{transform:none}20%{transform:rotate(-3deg) scale(1.02)}40%{transform:rotate(3deg) scale(1.04)}60%{transform:rotate(-4deg) scale(1.06)}80%{transform:rotate(4deg) scale(1.08)}}
.luck{margin:0 0 4px;display:flex;gap:12px;align-items:baseline}.luck small{font:700 .8rem var(--hud);letter-spacing:.2em;color:var(--muted)}
.luck strong{font:900 3rem/1 var(--disp)}.luck.t-ur strong{background:linear-gradient(90deg,#FF5CA8,#FFE600,#3CF0FF);-webkit-background-clip:text;background-clip:text;color:transparent}.luck.t-ssr strong{color:var(--ssr)}.luck.t-sr strong{color:var(--sr)}.luck.t-r strong{color:var(--r)}
.gname{font:900 1.15rem/1.4 var(--disp);margin:8px 0 2px}.gmeta{color:var(--pop);font-weight:700;margin:0 0 8px}
.gact{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:12px}.gact .more{margin:0;padding:12px 26px}
.ghost{font:700 .95rem var(--body);color:var(--cyan);text-decoration:none;padding:10px 6px}
.gbtns{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 4px}
.gbtns button:disabled{opacity:.45;cursor:not-allowed}
.gleft{font:600 .85rem var(--hud);letter-spacing:.08em;color:var(--muted)}
.dex{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:8px;margin-top:10px}
.dx{position:relative;display:block;aspect-ratio:1;clip-path:var(--cut);outline:2px solid var(--line);outline-offset:-2px}.dx img{width:100%;height:100%;object-fit:cover}.dx .rar{font-size:.6rem;padding:3px 6px 3px 4px}
.dx.t-ur{outline-color:#3CF0FF}.dx.t-ssr{outline-color:var(--ssr)}.dx.t-sr{outline-color:var(--sr)}
.hl{display:grid;grid-template-columns:1fr auto 1fr;gap:16px;align-items:stretch;max-width:760px}
@media (max-width:700px){.hl{grid-template-columns:1fr 1fr;gap:10px}.hl .vs{display:none}}
.hlc{background:var(--panel2);padding:10px;clip-path:var(--cut);display:grid;gap:6px;align-content:start;transition:box-shadow .2s}
.hlc img{width:100%;aspect-ratio:1;object-fit:cover}.hlc .hn{font-size:.86rem;line-height:1.4;text-decoration:none;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.hlc .hp{margin:0;font:1.1rem var(--num);color:var(--muted)}.hlc .hs{margin:0}.hlc .hs small{display:block;font:700 .72rem var(--hud);letter-spacing:.18em;color:var(--muted)}.hlc .hs strong{font:2.2rem/1 var(--num);color:var(--pop)}
.hlc.ok{box-shadow:inset 0 0 0 3px #39E58C}.hlc.no{box-shadow:inset 0 0 0 3px var(--red)}
.vs{align-self:center;font:2.6rem var(--num);color:var(--red);font-style:italic}
.hlbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:14px 0}.hlbar .btn{min-height:52px}
.score{display:flex;gap:18px;font:600 .85rem var(--hud);letter-spacing:.1em;color:var(--muted)}.score b{font:1.6rem var(--num);color:var(--ink);margin-left:6px}
.prq{display:grid;grid-template-columns:200px minmax(0,1fr);gap:16px;align-items:center}.prq img{width:200px;aspect-ratio:1;object-fit:cover;clip-path:var(--cut)}
@media (max-width:560px){.prq{grid-template-columns:120px minmax(0,1fr)}.prq img{width:120px}}
.propt{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}.propt .chip{font:1.3rem var(--num);padding:10px 22px;letter-spacing:.03em}.propt .chip.bad{background:var(--red);border-color:var(--red)}
.gmsg{font:900 1.15rem var(--disp);margin:6px 0}
/* gift finder */
.gq{margin:0 0 14px}.gq h3{font:700 .8rem var(--hud);letter-spacing:.24em;color:var(--cyan);margin:0 0 8px}
.gq .cats{flex-wrap:wrap;padding:0}
.gout{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px 14px;margin-top:16px}
@media (max-width:520px){.gout{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 10px}}
.gift{text-decoration:none;display:grid;gap:6px;align-content:start;animation:up .45s both}
@keyframes up{from{opacity:0;transform:translateY(14px)}}
.gift .ph{position:relative;aspect-ratio:1;overflow:hidden;clip-path:var(--cut);background:var(--panel2)}.gift .ph img{width:100%;height:100%;object-fit:cover}
.gift .n{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:.9rem;line-height:1.45}
.gift .m{font:700 .85rem var(--body);color:var(--pop)}.gift .why{font:600 .76rem var(--body);color:var(--cyan)}
@media (prefers-reduced-motion:reduce){.gift{animation:none}.gci{transition:none}.gstage.charge .gc3{animation:none}}
/* deals */
.cd{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 10px}
.cd span{background:var(--panel);clip-path:var(--cut);padding:10px 16px 8px;min-width:92px;text-align:center;font:700 .78rem var(--hud);letter-spacing:.2em;color:var(--muted)}
.cd b{display:block;font:3.4rem/1 var(--num);color:var(--pop);letter-spacing:.02em;text-shadow:3px 3px 0 var(--red)}
.hist{margin:0 0 16px}.hist svg{width:100%;height:90px;display:block;background:var(--panel)}.hist p{font-size:.8rem;color:var(--muted);margin:4px 0 0}
"""

CSS += r"""
/* 找東西小幫手（finder.js） */
.ybf-btn{position:fixed;right:16px;bottom:16px;z-index:60;display:flex;align-items:center;gap:6px;padding:6px 14px 6px 6px;border:3px solid var(--pop);border-radius:40px;background:#111;color:var(--ink);font:900 .95rem var(--body);cursor:pointer;box-shadow:0 6px 24px rgba(0,0,0,.5)}
.ybf-btn:hover{transform:translateY(-2px)}.ybf-btn:focus-visible,.ybf button:focus-visible,.ybf input:focus-visible,.ybf-card:focus-visible{outline:3px solid var(--cyan);outline-offset:2px}
.ybf-face{width:46px;height:48px;display:block}.ybf-face svg,.ybf-av svg,.ybf-mini svg{width:100%;height:100%;display:block}
.ybf-tip{position:fixed;right:20px;bottom:84px;z-index:60;background:var(--pop);color:#111;border:0;border-radius:14px 14px 4px 14px;padding:10px 14px;font:900 .9rem var(--body);cursor:pointer;animation:ybfIn .3s ease-out;box-shadow:0 6px 20px rgba(0,0,0,.5)}
@keyframes ybfIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.ybf{position:fixed;right:16px;bottom:84px;z-index:61;width:min(400px,calc(100vw - 32px));height:min(620px,calc(100vh - 110px));display:flex;flex-direction:column;background:var(--panel);border:2px solid var(--pop);border-radius:18px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.6)}
.ybf[hidden]{display:none}
.ybf-hd{display:flex;align-items:center;gap:10px;padding:10px 12px;background:#0E0E15;border-bottom:1px solid var(--line)}
.ybf-av{width:44px;height:46px;flex:none}.ybf-tt{flex:1;display:flex;flex-direction:column;line-height:1.3}.ybf-tt b{color:var(--pop);font-size:1.05rem}.ybf-tt small{color:var(--muted);font-size:.75rem}
.ybf-x{background:none;border:0;color:var(--ink);font-size:1.7rem;line-height:1;cursor:pointer;padding:4px 8px}
.ybf-log{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:10px;overscroll-behavior:contain}
.ybf-msg{display:flex;gap:8px;align-items:flex-end;max-width:92%}.ybf-msg p{margin:0;padding:9px 12px;border-radius:14px;background:var(--panel2);font-size:.92rem;line-height:1.55}
.ybf-mini{width:28px;height:30px;flex:none}
.ybf-msg.me{align-self:flex-end}.ybf-msg.me p{background:var(--pop);color:#111;font-weight:700;border-bottom-right-radius:4px}
.ybf-msg.bot p{border-bottom-left-radius:4px}.ybf-msg.wait p{color:var(--muted)}
.ybf-chips{display:flex;flex-wrap:wrap;gap:6px}.ybf-chips button{background:transparent;color:var(--ink);border:1.5px solid var(--pop);border-radius:20px;padding:6px 12px;font:700 .85rem var(--body);cursor:pointer}
.ybf-chips button:hover{background:var(--pop);color:#111}
.ybf-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.ybf-card{position:relative;display:flex;flex-direction:column;gap:4px;background:#0E0E15;border:1px solid var(--line);border-radius:10px;padding:6px;text-decoration:none;color:var(--ink)}
.ybf-card:hover{border-color:var(--pop)}.ybf-card img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:6px;background:var(--panel2)}
.ybf-card .n{font-size:.78rem;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.ybf-card .m{display:flex;justify-content:space-between;align-items:baseline;gap:4px}.ybf-card .m b{color:var(--pop);font:1rem var(--num);letter-spacing:.02em}.ybf-card .m small{color:var(--muted);font-size:.7rem}
.ybf-card .ybf-off{position:absolute;top:10px;left:10px;background:var(--red);color:#fff;font:900 .72rem var(--body);padding:2px 6px;border-radius:4px}
.ybf-link{color:var(--cyan);font-weight:700;font-size:.9rem}
.ybf-in{display:flex;gap:6px;padding:10px;border-top:1px solid var(--line);background:#0E0E15}
.ybf-in input{flex:1;min-width:0;background:var(--panel2);border:1px solid var(--line);border-radius:22px;padding:10px 14px;color:var(--ink);font:500 16px var(--body)}
.ybf-in button{background:var(--pop);color:#111;border:0;border-radius:22px;padding:0 18px;font:900 1rem var(--body);cursor:pointer}
.ybf-ft{margin:0;padding:6px 12px 10px;background:#0E0E15;color:var(--muted);font-size:.7rem;line-height:1.5}
.ybf-clr{background:none;border:0;color:var(--cyan);font:700 .7rem var(--body);cursor:pointer;padding:0 0 0 6px;text-decoration:underline}
.ybf-strip{margin:18px 0 6px;padding:14px;background:linear-gradient(90deg,rgba(255,230,0,.10),transparent 70%),var(--panel);border-left:6px solid var(--pop)}
.ybf-sh{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}.ybf-sh p{margin:0;flex:1;min-width:200px;font-weight:900;font-size:1.05rem}
.ybf-ask{background:var(--pop);color:#111;border:0;border-radius:20px;padding:8px 14px;font:900 .88rem var(--body);cursor:pointer}
.ybf-row{display:grid;grid-auto-flow:column;grid-auto-columns:150px;gap:10px;overflow-x:auto;padding-bottom:6px;scroll-snap-type:x mandatory}.ybf-row .ybf-card{scroll-snap-align:start}
@media (max-width:600px){.ybf{right:0;bottom:0;width:100vw;height:82vh;border-radius:18px 18px 0 0;border-width:2px 0 0}.ybf-btn{right:12px;bottom:12px}.ybf-lbl{display:none}.ybf-btn{padding:6px}.ybf-tip{right:12px;bottom:76px}body.ybf-on{overflow:hidden}}
@media (prefers-reduced-motion:reduce){.ybf-tip{animation:none}.ybf-btn:hover{transform:none}}
"""

JS_COMMON = r"""
<script>
(function(){
var root=document.documentElement.dataset.root||'';
var box=document.getElementById('q'),res=document.getElementById('sres'),data=null;
function load(cb){if(data)return cb(data);fetch(root+'data/p.json').then(function(r){return r.json()}).then(function(d){data=d;cb(d)}).catch(function(){})}
function money(n){return '$'+Number(n).toLocaleString('zh-TW')}
function rar(n){var r=n>=1000000?['UR','ur']:n>=300000?['SSR','ssr']:n>=50000?['SR','sr']:n>=10000?['R','r']:['N','n'];var s=document.createElement('span');s.className='rar r-'+r[1];s.textContent=r[0];return s}
function img(p,big){if(p.mu)return p.mu;return p.m?'https://down-aws-tw.img.susercontent.com/file/'+p.m+(big?'':'_tn'):root+'img/'+p.i+'.webp'}
if(box){box.addEventListener('focus',function(){load(function(){})});
box.addEventListener('input',function(){var t=box.value.trim().toLowerCase();if(!t){res.classList.remove('on');return}
load(function(d){var hit=d.filter(function(p){return p.s.toLowerCase().indexOf(t)>=0}).slice(0,12);res.textContent='';
if(!hit.length){var no=document.createElement('p');no.style.padding='10px 14px';no.textContent='本站找不到「'+box.value+'」';res.appendChild(no)}
var cpa=document.createElement('a');cpa.href=root+'coupang.html#search';cpa.innerHTML='<span style="color:var(--cyan);font-weight:700">到酷澎館搜尋全站商品 ›</span>';res.appendChild(cpa);
hit.forEach(function(p){var a=document.createElement('a');a.href=root+'product.html#'+p.i;var im=document.createElement('img');im.src=img(p);im.alt='';im.loading='lazy';im.referrerPolicy='no-referrer';
var tx=document.createElement('span');tx.textContent=p.s;var pr=document.createElement('span');pr.className='sp';pr.textContent=money(p.p);a.appendChild(im);a.appendChild(tx);a.appendChild(pr);res.appendChild(a)});res.classList.add('on')})});
document.addEventListener('click',function(ev){if(!res.contains(ev.target)&&ev.target!==box)res.classList.remove('on')});}
window.__load=load;window.__money=money;window.__img=img;window.__rar=rar;
function cpLoad(el){var f=el.querySelector('.cpf');if(!f||f.firstChild)return;var w=Math.max(300,Math.min(2000,Math.round(f.clientWidth||680)));var i=document.createElement('iframe');i.width=w;i.height=140;i.setAttribute('frameborder','0');i.setAttribute('scrolling','no');i.referrerPolicy='unsafe-url';i.title='酷澎熱銷商品';
i.src='https://ads-partners.tw.coupang.com/widgets.html?id='+el.dataset.id+'&template=carousel&trackingCode=AF7017986&subId=&width='+w+'&height=140&tsource=';f.appendChild(i)}
window.__cpLoad=cpLoad;
var cps=document.querySelectorAll('.cpw');if(cps.length){if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){cpLoad(x.target);io.unobserve(x.target)}})},{rootMargin:'300px'});cps.forEach(function(c){io.observe(c)})}else cps.forEach(cpLoad)}
document.addEventListener('click',function(ev){var b=ev.target.closest('[data-cpw]');if(!b)return;var box=document.getElementById(b.dataset.target);if(!box)return;box.dataset.id=b.dataset.cpw;var f=box.querySelector('.cpf');f.textContent='';cpLoad(box);box.querySelector('.cpl').firstChild.textContent='酷澎熱銷・'+b.textContent;
document.querySelectorAll('[data-target="'+b.dataset.target+'"]').forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});if(window.gtag)gtag('event','coupang_tab',{cat:b.textContent})});
if(matchMedia('(hover:hover) and (pointer:fine)').matches&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
document.addEventListener('pointermove',function(e){var ph=e.target.closest&&e.target.closest('.it .ph');if(!ph)return;var r=ph.getBoundingClientRect(),x=(e.clientX-r.left)/r.width,y=(e.clientY-r.top)/r.height;
ph.style.setProperty('--ry',((x-.5)*16).toFixed(1)+'deg');ph.style.setProperty('--rx',((.5-y)*16).toFixed(1)+'deg');ph.style.setProperty('--mx',(x*100).toFixed(0)+'%');ph.style.setProperty('--my',(y*100).toFixed(0)+'%')});
document.addEventListener('pointerout',function(e){var ph=e.target.closest&&e.target.closest('.it .ph');if(ph&&!ph.contains(e.relatedTarget)){ph.style.setProperty('--rx','0deg');ph.style.setProperty('--ry','0deg')}});}
function ev(n,p){if(window.gtag)window.gtag('event',n,p)}
document.addEventListener('click',function(e){var a=e.target.closest('a[href]');if(a&&/(^https:\/\/(s\.)?shopee\.tw|coupang|oeya\.com\.tw)/.test(a.href)){var q=a.closest('.q');ev('shop_click',{placement:q?'quest':a.dataset.pl?a.dataset.pl:(a.classList.contains('cta')?(location.pathname.indexOf('/guides/')>=0?'guide':'product'):'other'),quest:q?q.dataset.qid:'',item_name:(a.querySelector('.t')||a).textContent.slice(0,90),link_url:a.href})}
var b=e.target.closest('.emb button');if(b){var q2=b.closest('.q');ev('media_open',{platform:b.dataset.p,quest:q2?q2.dataset.qid:'',creator:(b.querySelector('.au')||{}).textContent||''})}},true);
document.addEventListener('click',function(ev){var b=ev.target.closest('.emb button');if(!b)return;var p=b.dataset.p,box=b.parentNode,el;
if(p==='th'){el=document.createElement('blockquote');el.className='text-post-media';el.setAttribute('data-text-post-permalink',b.dataset.url);el.setAttribute('data-text-post-version','0');var a=document.createElement('a');a.href=b.dataset.url;a.textContent='Threads 貼文載入中…';el.appendChild(a);box.classList.add('on');b.replaceWith(el);var sc=document.createElement('script');sc.async=true;sc.src='https://www.threads.com/embed.js';document.body.appendChild(sc);setTimeout(function(){box.querySelectorAll('iframe').forEach(function(f){if(f.offsetHeight<40){f.style.height='560px'}})},6000);return}
el=document.createElement('iframe');el.title=b.getAttribute('aria-label');el.allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen';el.allowFullscreen=true;el.referrerPolicy='strict-origin-when-cross-origin';
el.src=p==='yt'?'https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1&rel=0':'https://www.tiktok.com/player/v1/'+b.dataset.id+'?autoplay=1&rel=0&description=1';
box.classList.add('on');b.replaceWith(el)});
})();
</script>"""

GRID_JS = r"""
<script>
document.addEventListener('DOMContentLoaded',function(){
var root=document.documentElement.dataset.root||'';var fixedCat=document.body.dataset.cat||'';
var grid=document.getElementById('grid'),more=document.getElementById('more'),sort=document.getElementById('sort'),band=document.getElementById('band'),cnt=document.getElementById('cnt'),chips=document.querySelectorAll('[data-filter]');
var cat=fixedCat,shown=0,list=[],STEP=/\/(index\.html)?$/.test(location.pathname)?24:48;more.textContent='再看 '+STEP+' 件';
function card(p){var a=document.createElement('a');a.className='it';a.href=root+'product.html#'+p.i;
var ph=document.createElement('div');ph.className='ph';var im=document.createElement('img');im.src=window.__img(p);im.alt=p.s;im.loading='lazy';im.referrerPolicy='no-referrer';im.width=400;im.height=400;ph.appendChild(im);if(!p.sh)ph.appendChild(window.__rar(p.q||0));
if(p.d){var o=document.createElement('span');o.className='off';var b=document.createElement('b');b.textContent=p.d;o.appendChild(b);o.appendChild(document.createTextNode('折'));ph.appendChild(o)}
if(p.v){var v=document.createElement('span');v.className='vid';v.textContent='▶ REEL';ph.appendChild(v)}
if(p.dr||p.lw){var dp=document.createElement('span');dp.className='drop';dp.textContent=p.dr?'↓'+p.dr+'%':'30天最低';ph.appendChild(dp)}
var tg=document.createElement('span');tg.className='tag';var d=document.createElement('span');d.className='d';d.textContent='$';var val=document.createElement('span');val.className='v';val.textContent=Number(p.p).toLocaleString('zh-TW');tg.appendChild(d);tg.appendChild(val);
var n=document.createElement('span');n.className='n';n.textContent=p.s;var s=document.createElement('span');s.className='s';s.textContent=p.sh?'品牌官網':'銷量戰力';var sb=document.createElement('b');sb.textContent=p.sh||p.sold;s.appendChild(sb);
a.appendChild(ph);a.appendChild(tg);a.appendChild(n);a.appendChild(s);return a}
function apply(){window.__load(function(d){var b=band.value;list=d.filter(function(p){return (!cat||p.c===cat)&&(b==='all'||(b==='a'&&p.p<100)||(b==='b'&&p.p>=100&&p.p<500)||(b==='c'&&p.p>=500&&p.p<2000)||(b==='d'&&p.p>=2000))});
var k=sort.value;list.sort(function(x,y){return k==='hot'?y.n-x.n:k==='sold'?(y.q||0)-(x.q||0):k==='off'?((x.d||10)-(y.d||10)):k==='low'?x.p-y.p:y.p-x.p});
grid.textContent='';shown=0;page();cnt.textContent='共 '+list.length+' 件'})}
function page(){list.slice(shown,shown+STEP).forEach(function(p){grid.appendChild(card(p))});shown+=STEP;more.hidden=shown>=list.length}
more.addEventListener('click',page);sort.addEventListener('change',apply);band.addEventListener('change',apply);
chips.forEach(function(c){c.addEventListener('click',function(){cat=c.dataset.filter;chips.forEach(function(x){x.setAttribute('aria-pressed',String(x===c))});apply()})});
apply();
});
</script>"""


PRODUCT_JS = r"""<script>
document.addEventListener('DOMContentLoaded',function(){var root='';var box=document.getElementById('pd'),rel=document.getElementById('rel');
function render(){var id=location.hash.replace('#','');window.__load(function(d){fetch('data/cats.json').then(function(r){return r.json()}).then(function(cats){
var p=d.find(function(x){return x.i===id})||d[0];document.title=p.s+'｜今天買這個';box.textContent='';
var wrap=document.createElement('section');wrap.className='pd';var media=document.createElement('div');media.className='media';
if(p.v){var v=document.createElement('video');v.src='vid/'+p.i+'.mp4';v.poster=window.__img(p);v.muted=true;v.loop=true;v.playsInline=true;v.autoplay=true;v.controls=true;media.appendChild(v)}
if(!p.v){var im=document.createElement('img');im.src=window.__img(p,1);im.referrerPolicy='no-referrer';im.alt=p.s;media.appendChild(im)}
var info=document.createElement('div');var cr=document.createElement('p');cr.className='crumb';var ca=document.createElement('a');ca.href='c/'+p.c+'.html';ca.textContent=cats[p.c]||'';cr.appendChild(document.createTextNode('爆品 › '));cr.appendChild(ca);
var h=document.createElement('h1');h.textContent=p.s;var tg=document.createElement('p');tg.className='tag';tg.innerHTML='<span class="d">$</span><span class="v"></span>';tg.querySelector('.v').textContent=Number(p.p).toLocaleString('zh-TW');
var f=document.createElement('ul');f.className='facts';[p.dr?'比近 30 天最高價便宜 '+p.dr+'%':'',p.lw?'近 30 天最低價':'',p.d?(p.sh?'官網特價 '+p.d+' 折':'賣場標示 '+p.d+' 折'):'',p.sh?'品牌官網：'+p.sh:'',p.sold&&p.sold!=='—'?'已售出 '+p.sold:'',cats[p.c]||''].filter(Boolean).forEach(function(t){var li=document.createElement('li');li.textContent=t;f.appendChild(li)});
var c=document.createElement('a');c.className='cta';var sn={shopee:'蝦皮',coupang:'酷澎'}[p.st]||(p.sh||'品牌官網');c.textContent=p.u?'⚡ 到'+sn+'看這件':'購物連結準備中';if(p.u){c.href=p.u;c.target='_blank';c.rel='sponsored nofollow noopener'}else{c.setAttribute('aria-disabled','true')}
var fn=document.createElement('p');fn.className='fine';fn.textContent='推廣連結・價格以購物網站為準';
var hs=document.createElement('div');hs.className='hist';
fetch('data/ph.json').then(function(r){return r.json()}).then(function(H){var h=H[p.i];if(!h||h.length<2)return;var W=600,Hh=90,v=h.map(function(x){return x[1]}),mn=Math.min.apply(0,v),mx=Math.max.apply(0,v),sp=(mx-mn)||1;
var pts=h.map(function(x,i){return (i/(h.length-1)*(W-20)+10).toFixed(1)+','+(Hh-12-(x[1]-mn)/sp*(Hh-28)).toFixed(1)}).join(' ');
hs.innerHTML='<svg viewBox="0 0 '+W+' '+Hh+'" preserveAspectRatio="none" role="img"><polyline fill="none" stroke="#FFE600" stroke-width="2.5" points="'+pts+'"/></svg><p></p>';
hs.querySelector('svg').setAttribute('aria-label','價格紀錄 '+h[0][0]+' 到 '+h[h.length-1][0]);hs.querySelector('p').textContent='本站價格紀錄 '+h[0][0]+'～'+h[h.length-1][0]+'：最低 $'+mn+'、最高 $'+mx}).catch(function(){});
[cr,p.sh?document.createTextNode(''):window.__rar(p.q||0),h,tg,f,hs,c,fn].forEach(function(x){info.appendChild(x)});wrap.appendChild(media);wrap.appendChild(info);box.appendChild(wrap);
var bb=document.getElementById('buybar');if(!bb){bb=document.createElement('div');bb.id='buybar';bb.className='buybar';document.body.appendChild(bb)}bb.textContent='';if(p.u){var bt=document.createElement('span');bt.className='bt';var bp=document.createElement('b');bp.textContent='$'+Number(p.p).toLocaleString('zh-TW');bt.appendChild(bp);bt.appendChild(document.createTextNode(p.s));var bc=c.cloneNode(true);bc.textContent='到'+sn+'看 ›';bc.dataset.pl='buybar';bb.appendChild(bt);bb.appendChild(bc);bb.classList.add('on');document.body.classList.add('has-bb')}else{bb.classList.remove('on');document.body.classList.remove('has-bb')}
rel.textContent='';d.filter(function(x){return x.c===p.c&&x.i!==p.i}).slice(0,12).forEach(function(x){var a=document.createElement('a');a.className='it';a.href='product.html#'+x.i;a.innerHTML='<div class="ph"><img loading="lazy" alt=""></div><span class="tag"><span class="d">$</span><span class="v"></span></span><span class="n"></span><span class="s"></span>';
a.querySelector('img').referrerPolicy='no-referrer';a.querySelector('img').src=window.__img(x);a.querySelector('.v').textContent=Number(x.p).toLocaleString('zh-TW');a.querySelector('.n').textContent=x.s;a.querySelector('img').alt=x.s;a.querySelector('.s').textContent=x.sh?'品牌官網 '+x.sh.replace(/ ?官網/,''):'銷量戰力 '+x.sold;rel.appendChild(a)});window.scrollTo(0,0)})})}
window.addEventListener('hashchange',render);render();});
</script>"""


def strip_tags(js):
    return js.strip().removeprefix('<script>').removesuffix('</script>').strip()


OGPAGE = {'index.html': 'index', 'trending.html': 'trending', 'new.html': 'new', 'gifts.html': 'gifts', 'deals.html': 'deals', 'coupang.html': 'coupang', 'guides.html': 'guides', 'play.html': 'play', 'game.html': 'game', 'dungeon.html': 'dungeon'}  # social share images in og/ (made by make_og.py, uploaded once to /og/)
def shell(path, title, desc, body, current='', depth=0, extra_head='', noindex=False, cat='', js='', mod='', vp='width=device-width,initial-scale=1'):
    root = '../' * depth
    canon = BASE + ('' if path == 'index.html' else path)
    nav = [('index.html', '爆品'), ('trending.html', '社群爆紅'), ('new.html', '社群新品'), ('dungeon.html', '遊戲'), ('gifts.html', '送禮神器'), ('deals.html', '雙11'), ('coupang.html', '酷澎館'), ('guides.html', '主題整理')]
    navh = ''.join(f'<a href="{root}{h}"' + (' aria-current="page"' if h == current else '') + f'>{t}</a>' for h, t in nav)
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ''
    doc = f"""<!doctype html>
<html lang="zh-Hant-TW" data-root="{root}" data-api="{e(SHOP_API or "")}"><head><meta charset="utf-8"><meta name="viewport" content="{vp}">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canon}">{robots}
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}"><meta property="og:site_name" content="{SITE}"><meta property="og:image" content="{BASE}og/{OGPAGE.get(path, "default")}.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}og/{OGPAGE.get(path, "default")}.jpg"><meta property="og:locale" content="zh_TW">
<meta name="theme-color" content="#09090D"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23FFE600' stroke='%231A1714' stroke-width='4'/%3E%3Ctext x='32' y='42' font-size='28' text-anchor='middle' fill='%231A1714' font-family='sans-serif' font-weight='900'%3E買%3C/text%3E%3C/svg%3E">
{FONTS}<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA_ID}",{{allow_google_signals:false,allow_ad_personalization_signals:false}});</script><link rel="stylesheet" href="{root}assets/site.css?v={VER}">{extra_head}<script src="{root}assets/app.js?v={VER}" defer></script><script src="{root}assets/finder.js?v={VER}" defer></script>{(f'<script src="{root}assets/{js}.js?v={VER}" defer></script>') if js else ''}{(f'<script type="module" src="{root}assets/{mod}.js?v={VER}"></script>') if mod else ''}</head><body{(' data-cat="' + cat + '"') if cat else ''}>
<header class="hd"><div class="w"><a class="logo" href="{root}index.html"><b aria-hidden="true">今天<br>買這個</b><span>{SITE}</span></a>
<div class="sbox"><input id="q" type="search" placeholder="搜尋 {len(products)} 件爆品：火雞麵、除濕機、藍芽耳機…" aria-label="搜尋商品" autocomplete="off"><div id="sres" class="sres" role="listbox"></div></div>
<nav class="nav" aria-label="主選單">{navh}</nav></div></header>
<main class="w">{body}</main>
<footer class="ft"><div class="w"><p>{SITE} · youbi-shop.com　｜　<a href="{root}disclosure.html">推廣連結與隱私說明</a></p>
<p>商品資料來自蝦皮、酷澎與合作品牌公開的商品資訊，價格、折扣與銷量以購物網站當下顯示為準。本站含推廣連結，經由連結購買不會增加你的費用。</p></div></footer>
</body></html>"""
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full) or OUT, exist_ok=True)
    open(full, 'w', encoding='utf-8').write(doc)


def DG_LD(lang):
    zh = lang == 'zh'
    d = {'@context': 'https://schema.org', '@type': 'VideoGame', 'name': '夜市地下城' if zh else 'Night Market Dungeon', 'alternateName': 'Night Market Dungeon' if zh else '夜市地下城',
         'url': BASE + ('dungeon.html' if zh else 'en/dungeon.html'), 'image': BASE + 'og/dungeon.jpg', 'inLanguage': 'zh-Hant' if zh else 'en',
         'description': ('免費像素動作冒險：故事 40 層、冒險 50 層、最多 4 人連線，手機電腦打開瀏覽器就能玩，不用下載。' if zh else 'Free pixel action roguelite in your browser: 40-floor Story Mode, 50-floor Adventure Mode, online co-op for up to 4 players. No download.'),
         'genre': ['Action', 'Roguelite', 'Pixel art'], 'gamePlatform': ['Web browser', 'Android', 'iOS', 'PC'], 'applicationCategory': 'Game', 'operatingSystem': 'Any',
         'playMode': ['SinglePlayer', 'CoOp'], 'numberOfPlayers': {'@type': 'QuantitativeValue', 'minValue': 1, 'maxValue': 4}, 'contentRating': '輔導十五歲級' if zh else 'Rated 15+',
         'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'TWD' if zh else 'USD', 'availability': 'https://schema.org/InStock'}}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace('</', '<\\/') + '</script>'
HREFLANG_DG = f'<link rel="alternate" hreflang="zh-Hant" href="{BASE}dungeon.html"><link rel="alternate" hreflang="en" href="{BASE}en/dungeon.html"><link rel="alternate" hreflang="x-default" href="{BASE}en/dungeon.html">'
def shell_en(path, title, desc, body, js='', og='dungeon', head=''):
    """English pages (/en/…): no Taiwan shopping chrome, same game account & saves."""
    root = '../'; canon = BASE + path
    doc = f"""<!doctype html>
<html lang="en" data-root="{root}" data-api="{e(SHOP_API or "")}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canon}">{HREFLANG_DG}
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}"><meta property="og:site_name" content="Night Market Dungeon"><meta property="og:image" content="{BASE}og/{og}.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}og/{og}.jpg"><meta property="og:locale" content="en_US">
<meta name="theme-color" content="#09090D"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23FFE600' stroke='%231A1714' stroke-width='4'/%3E%3Ctext x='32' y='43' font-size='30' text-anchor='middle' fill='%231A1714' font-family='sans-serif' font-weight='900'%3EN%3C/text%3E%3C/svg%3E">
{FONTS}<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA_ID}",{{allow_google_signals:false,allow_ad_personalization_signals:false}});</script>
<link rel="stylesheet" href="{root}assets/site.css?v={VER}">{head}<script src="{root}assets/app.js?v={VER}" defer></script>{(f'<script src="{root}assets/{js}.js?v={VER}" defer></script>') if js else ''}</head>
<body class="en"><header class="hd"><div class="w"><a class="logo" href="dungeon.html"><b aria-hidden="true">NMD</b><span>Night Market Dungeon</span></a>
<nav class="nav" aria-label="Menu"><a href="dungeon.html"{' aria-current="page"' if path.endswith('dungeon.html') else ''}>Play</a><a href="terms.html"{' aria-current="page"' if path.endswith('terms.html') else ''}>Terms &amp; Privacy</a><a href="{root}dungeon.html" lang="zh-Hant">中文</a></nav></div></header>
<main class="w">{body}</main>
<footer class="ft"><div class="w"><p>Night Market Dungeon · youbi-shop.com　|　<a href="terms.html">Terms of Service &amp; Privacy</a></p><p>Original pixel art. Made in Taiwan.</p></div></footer>
</body></html>"""
    full = os.path.join(OUT, path); os.makedirs(os.path.dirname(full), exist_ok=True); open(full, 'w', encoding='utf-8').write(doc)

def shell_en_dungeon():
    body = ('<span class="kick" style="margin-top:22px">PIXEL ROGUELITE</span><h1 class="ptitle" style="margin-bottom:12px">Night Market Dungeon</h1>'
            f'<div class="dg" id="dg" data-api="{e(SHOP_API)}" data-gcid="{e(GOOGLE_CLIENT_ID)}"></div>'
            '<p class="sub" style="margin-top:12px">A pixel action roguelite you can play right in your phone or desktop browser: a 40-floor Story Mode, 50-floor Adventure Mode and online co-op for up to 4 players. '
            'All original pixel art. Boss Nightcat and the residents talk through AI — their lines are generated automatically, for fun only. Rated 15+ (cartoon pixel violence; blood effects can be turned off). '
            '<a href="terms.html">Terms of Service &amp; Privacy</a></p>')
    shell_en('en/dungeon.html', 'Night Market Dungeon — Free Pixel Roguelite, No Download, 4P Co-op', 'Free pixel action roguelite you play right in your browser on phone or PC: fight down a dungeon under a Taiwanese night market, craft gear, and team up online with up to 4 players. No download.', body, js='dungeon.en', head=DG_LD('en'))
    owner = e(SHOP_OWNER) if SHOP_OWNER else '(to be announced)'
    contact = f'<a href="mailto:{e(SHOP_CONTACT)}">{e(SHOP_CONTACT)}</a>' if SHOP_CONTACT else '(to be announced)'
    t = ('<article class="art"><h1>Night Market Dungeon — Terms of Service &amp; Privacy</h1>'
         f'<h2>1. Operator &amp; contact</h2><p>Operated by {owner}, a business registered in Taiwan. Support: {contact}. We reply within 3 business days (in English or Chinese).</p>'
         '<h2>2. Rating &amp; prices</h2><p>The game is rated <b>15+</b>: cartoon pixel combat with blood effects (can be turned off in Settings) and some spooky floors. The game is free to play. Some outfits can be unlocked with <b>Gold Lanterns</b>. Everything you can buy is cosmetic only and never makes you stronger. There are no loot boxes, gacha or other randomized paid items: every item and its price are shown before you buy.</p>'
         '<h2>3. Virtual currencies</h2><p><b>Night Coins</b> are earned by playing, or converted from Gold Lanterns (1 Gold Lantern = 20 Night Coins, one way only). They live in your game save (this browser; backed up to the cloud if you have an account) and cannot be turned into Gold Lanterns or money. If you clear your browser data without a cloud backup, your Night Coins are lost with the save.</p>'
         '<p><b>Gold Lanterns</b> are bought with real money or given in events, and are stored on our server. They can only be used in this game to unlock outfits or convert to Night Coins. They cannot be exchanged for cash, transferred to another account, or redeemed for physical goods.</p>'
         '<h2>4. Payments</h2><p>Players on the English version pay in <b>US dollars through PayPal</b>; we never receive your card or bank details. Packs: US$2.99 = 90, US$4.99 = 160, US$9.99 = 330, US$29.99 = 1,100 Gold Lanterns. Your bank or PayPal may apply currency conversion fees. Players on the Chinese version pay in New Taiwan dollars through ECPay.</p>'
         '<h2>5. Refunds</h2><p>Within 7 days of purchase, Gold Lanterns you have not used yet can be refunded in full, no reason needed. Gold Lanterns already used to unlock outfits or convert to Night Coins are digital content delivered at your request (we show the amount and ask you to confirm first), so they cannot be refunded. Double charges, payments that did not arrive, or losses caused by our bugs are always refunded or re-credited. To ask for a refund, email us with the first 8 characters of your account ID (Style Shop → Account) and your PayPal transaction ID. Refunds go back to the original payment method within 14 days. Nothing here limits rights you have under the consumer law of your country.</p>'
         '<h2>6. Accounts</h2><p>You can play without an account. You can create a free game account (or sign in with Google) from “☁ Save” on the title menu; one is also created automatically the first time you buy. You get a <b>recovery code</b>: keep it private. Use it, or your linked Google account, to get your save back on a new device.</p>'
         '<h2>7. Minors</h2><p>If you are under 18 (or the age of majority where you live), ask a parent or guardian before buying Gold Lanterns.</p>'
         '<h2>8. Fair play</h2><p>Cheats, modified clients, packet tampering or abusing bugs to get Gold Lanterns or outfits are not allowed. We may remove items obtained this way after notice; serious cases may lead to account suspension, with unused paid Gold Lanterns refunded pro rata.</p>'
         '<h2>9. Online play &amp; chat</h2><p>Co-op chat travels directly between players’ devices; our server does not see or store it. Chat with strangers is off by default. Links, contact details, long numbers, requests for personal info or meet-ups, trading and inappropriate content are blocked automatically on both sides. If you use “Report &amp; block”, the other player’s last 10 messages and system ID are sent to our server and kept for 30 days for review.</p>'
         '<h2>10. AI characters</h2><p>Boss Nightcat and the Manor residents are fictional characters voiced by AI (Cloudflare Workers AI). What you type (up to 80 characters) and basic game state (floor, HP, level, gear names) are sent to our server to generate a reply; we do not store the conversation or use it for training. Replies are automatic, for fun only, and may be wrong. The characters will always admit they are AI if you ask.</p>'
         '<h2>11. Privacy</h2><p>Your progress is stored in your browser. If you create an account we store only: a random account ID, a hash of your recovery code, your Google account identifier (not your email, name or photo), your cloud save, your Gold Lantern and outfit records, and payment order records (PayPal order ID and amount — never card details). Leaderboards, player names and friends use your system ID, the name you choose (filtered for bad words), your level and scores. Feedback you send is stored with your level, game version and device type; emails and phone numbers in it are masked automatically. We use Google Analytics with cookies to count visits and clicks, with ad personalization turned off; you can block cookies in your browser. To delete your account, cloud save or feedback, send feedback (category “Other”) with the first 8 characters of your account ID; we delete it within 7 days. If you are in the EU/UK, you also have the rights of access, correction, deletion and objection under the GDPR — contact us at the email above.</p>'
         '<h2>12. Changes &amp; termination</h2><p>We announce changes on this page and in the game. If we ever stop selling Gold Lanterns or end the game, we will announce it at least 30 days in advance and refund unused paid Gold Lanterns pro rata on request.</p>'
         '<h2>13. Governing law</h2><p>These terms are governed by the laws of Taiwan (Republic of China), without prejudice to mandatory consumer protections of your country of residence. The Chinese version applies to players on the Chinese site; this English version applies to the English site.</p>'
         '<p class="fine">Last updated: 2026-10-09</p></article>')
    shell_en('en/terms.html', 'Night Market Dungeon — Terms of Service & Privacy', 'Rating, virtual currency, PayPal payments, refunds, accounts and privacy for Night Market Dungeon.', t)


def rar(n):
    return ('UR', 'ur') if n >= 1000000 else ('SSR', 'ssr') if n >= 300000 else ('SR', 'sr') if n >= 50000 else ('R', 'r') if n >= 10000 else ('N', 'n')


def rar_html(n):
    t, c = rar(n)
    return f'<span class="rar r-{c}">{t}</span>'


def cp_widget(wid, label=''):
    """Coupang Partners 「分類最佳」carousel, lazy-loaded by app.js (iframe width follows the container)."""
    return f'<div class="cpw" data-id="{wid}"><span class="cpl">酷澎熱銷{("・" + e(label)) if label else ""}<small>推廣連結</small></span><div class="cpf"></div></div>'


def cp_search():
    return f'<div class="cps"><span class="cpl">搜尋酷澎全站<small>推廣連結・結果在酷澎開啟</small></span><iframe src="{CP_SEARCH}" width="100%" height="75" frameborder="0" scrolling="no" referrerpolicy="unsafe-url" loading="lazy" title="酷澎搜尋"></iframe></div>'


def key(p):
    if p.get('img_url'): return ''
    k = p['img'].rsplit('/', 1)[-1]
    return k[:-5] if k.endswith('.webp') else k


def thumb(p, root=''):
    if p.get('img_url'): return p['img_url']
    return f'{CDN}{key(p)}_tn' if PROD else f'{root}img/{p["id"]}.webp'


def tag_html(p):
    return f'<span class="tag"><span class="d">$</span><span class="v">{p["price"]:,}</span></span>'


def static_card(p, root=''):
    off = f'<span class="off"><b>{p["discount"]:g}</b>折</span>' if p.get('discount') else ''
    v = '<span class="vid">▶ REEL</span>' if p['id'] in reels else ''
    rp = '' if p.get('shop_name') else rar_html(p['soldN'])
    return (f'<a class="it" href="{root}product.html#{p["id"]}"><div class="ph"><img src="{thumb(p, root)}" referrerpolicy="no-referrer" alt="{e(p["short"])}" loading="lazy" width="400" height="400">{rp}{off}{v}</div>'
            f'{tag_html(p)}<span class="n">{e(p["short"])}</span>' + (f'<span class="s">品牌官網<b>{e(p["shop_name"].replace(" 官網", "").replace("官網", ""))}</b></span></a>' if p.get('shop_name') else f'<span class="s">銷量戰力<b>{e(p["sold"])}</b></span></a>'))


PLAT = {'yt': 'YouTube', 'tt': 'TikTok', 'th': 'Threads'}


def media_html(m, big=False):
    """Click-to-load facade for an official embed. Nothing from the platform loads until the visitor clicks
    (except the YouTube thumbnail, served by YouTube)."""
    p = m['p']
    data = f'data-p="{p}" data-id="{e(m.get("id", ""))}" data-url="{e(m["url"])}"'
    label = f'播放 {PLAT[p]}：{m["author"]}－{m["note"]}' if p != 'th' else f'展開 Threads 貼文：{m["author"]}－{m["note"]}'
    thumb = f'<img src="https://i.ytimg.com/vi/{m["id"]}/hqdefault.jpg" alt="" loading="lazy">' if p == 'yt' else ''
    head = f'<span class="pf pf-{p}">{PLAT[p]}</span><span class="lg">{e(m["lang"])}</span>'
    if big and p == 'yt':
        return (f'<div class="emb big yt"><button type="button" {data} aria-label="{e(label)}">{thumb}<span class="play" aria-hidden="true"></span></button></div>'
                f'<p class="src">{head} <a href="{e(m["url"])}" target="_blank" rel="noopener">{e(m["author"])}</a>：{e(m["note"])}（官方嵌入播放）</p>')
    cls = 'emb card ' + p + (' big' if big else '')
    return (f'<div class="{cls}"><button type="button" {data} aria-label="{e(label)}">'
            f'{thumb}<span class="ch">{head}</span><span class="au">{e(m["author"])}</span><span class="nt">{e(m["note"])}</span>'
            f'<span class="op">{"▶ 點了播放" if p != "th" else "≡ 展開貼文"}</span></button>'
            f'<a class="orig" href="{e(m["url"])}" target="_blank" rel="noopener">在 {PLAT[p]} 開啟原文 ›</a></div>')


_SOFT = [('蝦皮直營賣得', '網購賣得'), ('蝦皮直營的', '網購的'), ('蝦皮熱銷的', '網購熱銷的'), ('蝦皮有人賣', '網購買得到'), ('蝦皮買得到的', '網購買得到的'), ('蝦皮買得到', '網購買得到'), ('蝦皮上', '網購上')]


def soft(t):  # 文案不強調通路名（使用者 10/6）
    for a, b in _SOFT:
        t = t.replace(a, b)
    return t


def _qimg(x):
    i = x.get('img') or ''
    return i if i.startswith('http') else f'{CDN}{i}_tn'


def _qsold(x):
    s = str(x.get('sold') or '—')
    return s if s.startswith('評價') else f'銷量 {s}'


def quest_html(q):
    items = ''.join(
        f'<a class="li" href="{e(x["url"])}" target="_blank" rel="{"sponsored nofollow noopener" if x.get("aff") else "nofollow noopener"}">'
        f'<img src="{e(_qimg(x))}" referrerpolicy="no-referrer" alt="" loading="lazy" width="76" height="76">'
        f'<span><span class="t">{e(_nice(x["name"], 40))}</span><span class="m"><b>${x["price"]:,}</b>{e(_qsold(x))}</span><span class="go">{"到酷澎看這件 ›" if x.get("store") == "coupang" else "到蝦皮看這件 ›"}</span></span></a>' for x in q['items'])
    first, rest = q['media'][0], q['media'][1:]
    langs = sorted({m['lang'] for m in q['media']}, key=lambda l: (l != '中文', l))
    intel = (f'<h4 class="ih">INTEL · 各國網友怎麼說<span>{" · ".join(e(l) for l in langs)}</span></h4><div class="intel">{"".join(media_html(m) for m in rest)}</div>') if rest else ''
    return (f'<article class="q" data-no="{q["no"]}" data-qid="{q["id"]}"><div class="qm"><h3><small>{e(q["kick"])}</small>{e(q["title"])}</h3><p class="why">{e(soft(q["why"]))}</p>'
            f'{media_html(first, True)}{intel}</div>'
            f'<div class="loot"><h4>LOOT · 網購買得到</h4>{items}<p class="fine">推廣連結・價格以購物網站為準</p></div></article>')


def tools(with_chips=True):
    chips = ''
    if with_chips:
        chips = '<div class="cats" role="group" aria-label="分類"><button class="chip" type="button" data-filter="" aria-pressed="true">全部<small>' + str(len(products)) + '</small></button>' + \
                ''.join(f'<button class="chip" type="button" data-filter="{s}" aria-pressed="false">{e(l)}<small>{counts[s]}</small></button>' for s, l in cats) + '</div>'
    return chips + ('<div class="tools"><label class="vh" for="sort" hidden>排序</label><select id="sort" aria-label="排序"><option value="hot">精選推薦</option><option value="sold">銷量最高</option><option value="off">折扣最多</option><option value="low">價格低到高</option><option value="high">價格高到低</option></select>'
                    '<select id="band" aria-label="價格帶"><option value="all">全部價格</option><option value="a">100 元以下</option><option value="b">100～499</option><option value="c">500～1,999</option><option value="d">2,000 以上</option></select><span id="cnt" class="cnt" aria-live="polite"></span></div>'
                    '<div id="grid" class="grid"></div><button id="more" class="more" type="button">再看 48 件</button>')


# ---- 夜市地下城 App 模式（10/7）：加到主畫面後像 App 一樣全螢幕開啟 ----
DG_APP_HEAD = ('<link rel="manifest" href="dungeon.webmanifest"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">'
               '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="夜市地下城"><link rel="apple-touch-icon" href="app/dg-180.png">')


def dg_app_files():
    man = {'name': '夜市地下城', 'short_name': '夜市地下城', 'description': '像素動作冒險：在夜市底下的地下城打怪、用素材打造原創裝備、跟莊園居民交朋友。',
           'start_url': '/dungeon.html?app=1', 'scope': '/', 'display': 'fullscreen', 'display_override': ['fullscreen', 'standalone'], 'orientation': 'any',
           'background_color': '#07060a', 'theme_color': '#07060a', 'lang': 'zh-Hant-TW',
           'icons': [{'src': '/app/dg-192.png', 'sizes': '192x192', 'type': 'image/png'}, {'src': '/app/dg-512.png', 'sizes': '512x512', 'type': 'image/png'},
                     {'src': '/app/dg-512m.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]}
    json.dump(man, open(f'{OUT}/dungeon.webmanifest', 'w', encoding='utf-8'), ensure_ascii=False)
    # 只管地下城的 service worker（沒有 fetch 處理，不快取、不影響網站其他頁）
    open(f'{OUT}/dg-sw.js', 'w').write("self.addEventListener('install',function(){self.skipWaiting()});self.addEventListener('activate',function(e){e.waitUntil(self.clients.claim())});\n")
    os.makedirs(f'{OUT}/app', exist_ok=True)
    try:
        from PIL import Image, ImageDraw
        PAL = {'k': '#1A1420', 'y': '#FFE600', 'Y': '#C9A800', 's': '#F2C49B', 'S': '#D99A73', 'h': '#3B2A20', 'b': '#3D4F9E', 'B': '#2B3870', 'r': '#FF2E3B', 'w': '#FFFFFF'}
        hero = ['...kkkkkk...', '..khhhhhhk..', '.khhhhhhhhk.', '.khsssssshk.', '.kssksskssk.', '.kssssssssk.', '..kSssssSk..',
                '.kkyyyyyykk.', 'kyyyyyyyyyyk', 'kyYyyyyyyYyk', 'ksyyyyyyyysk', '.kyyyyyyyyk.', '.kbbbbbbbbk.', '.kbbBkkBbbk.', '.kbbk..kbbk.', '.kkk....kkk.']
        lan = ['..kk..', '.krrk.', 'krrrrk', 'kryyrk', 'krrrrk', '.krrk.', '..kk..']
        def icon(n, pad):
            im = Image.new('RGB', (n, n), '#07060a'); d = ImageDraw.Draw(im)
            d.ellipse([n * .12, n * .1, n * .88, n * .86], fill='#2a1422')
            u = int(n * (1 - 2 * pad) / 20)
            ox, oy = (n - 12 * u) // 2, int(n * .2)
            for j, row in enumerate(hero):
                for i2, ch in enumerate(row):
                    if ch in PAL: d.rectangle([ox + i2 * u, oy + j * u, ox + (i2 + 1) * u - 1, oy + (j + 1) * u - 1], fill=PAL[ch])
            v = max(1, u // 2)
            for lx in (int(n * .14), n - int(n * .14) - 6 * v):
                for j, row in enumerate(lan):
                    for i2, ch in enumerate(row):
                        if ch in PAL: d.rectangle([lx + i2 * v, int(n * .12) + j * v, lx + (i2 + 1) * v - 1, int(n * .12) + (j + 1) * v - 1], fill=PAL[ch])
            return im
        icon(192, .08).save(f'{OUT}/app/dg-192.png'); icon(512, .08).save(f'{OUT}/app/dg-512.png'); icon(512, .2).save(f'{OUT}/app/dg-512m.png'); icon(180, .08).save(f'{OUT}/app/dg-180.png')
    except Exception as _e:
        print('app icons skipped', _e)


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(f'{OUT}/data')
    # assets
    os.makedirs(f'{OUT}/vid'); os.makedirs(f'{OUT}/assets')
    if os.path.isdir('og'): shutil.copytree('og', f'{OUT}/og')
    if not PROD:
        os.makedirs(f'{OUT}/img')
        for p in products:
            if not p.get('img_url'): shutil.copy(f'img/{p["id"]}.webp', f'{OUT}/img/')
    open(f'{OUT}/assets/site.css', 'w', encoding='utf-8').write(CSS.strip())
    open(f'{OUT}/assets/app.js', 'w', encoding='utf-8').write(strip_tags(JS_COMMON))
    open(f'{OUT}/assets/grid.js', 'w', encoding='utf-8').write(strip_tags(GRID_JS))
    open(f'{OUT}/assets/product.js', 'w', encoding='utf-8').write(strip_tags(PRODUCT_JS))
    for f in ASSET_SRC:
        src = f'assets_src/{f}'
        if f in PRIVATE_SRC and not os.path.exists(src):
            # 遊戲原始碼放在私人倉庫（10/8 起）：沒有原始碼時，直接沿用網站上已經上線的壓縮版，不要去公開倉庫抓
            import urllib.request
            try:
                urllib.request.urlretrieve(f'https://youbi-shop.com/assets/{f}', f'{OUT}/assets/{f}')
                if f == 'dungeon.js':  # 英文版也一樣沿用線上那份
                    urllib.request.urlretrieve('https://youbi-shop.com/assets/dungeon.en.js', f'{OUT}/assets/dungeon.en.js')
            except Exception as ex:
                print(f'  (skip {f}: no source, live copy unavailable: {ex})')
            continue
        if not os.path.exists(src):
            import urllib.request
            os.makedirs('assets_src', exist_ok=True)
            urllib.request.urlretrieve(f'https://raw.githubusercontent.com/y927788-gif/youbi-shop/main/_build/assets_src/{f}', src)
        shutil.copy(src, f'{OUT}/assets/{f}')
        if f == 'dungeon.js':  # 英文版：字串換成英文（tools/i18n/en.json）→ dungeon.en.js
            sys.path.insert(0, 'tools/i18n'); from en_build import build as en_build
            ent, enmiss = en_build(src, None); enp = 'tools/i18n/.dungeon.en.js'; open(enp, 'w', encoding='utf-8').write(ent)
            if enmiss: print(f'  !! 英文版有 {len(enmiss)} 段沒翻譯：', enmiss[:5])
            shutil.copy(enp, f'{OUT}/assets/dungeon.en.js')
            if PROD:
                import subprocess
                mj = next((m for m in [os.environ.get('DG_MIN', ''), 'tools/min/min.mjs'] if m and os.path.exists(m)), None)
                if not (mj and subprocess.run(['node', mj, enp, f'{OUT}/assets/dungeon.en.js']).returncode == 0): print('  !! WARNING: dungeon.en.js 沒有壓縮')
        if PROD and f in PRIVATE_SRC:
            # 上線版壓縮：去註解、把變數名改短（防抄）。壓縮器在私人倉庫 _build/tools/min/（terser 5.31.6），找不到就照原樣並警告
            import subprocess
            mj = next((m for m in [os.environ.get('DG_MIN', ''), 'tools/min/min.mjs', os.path.expanduser('~/tools/min/min.mjs')] if m and os.path.exists(m)), None)
            if mj and subprocess.run(['node', mj, src, f'{OUT}/assets/{f}']).returncode == 0:
                pass
            else:
                print(f'  !! WARNING: {f} 沒有壓縮（找不到 tools/min/min.mjs）——不要把這份上傳到網站')
    for r in reels:
        if os.path.exists(f'vid/{r}.mp4'):
            shutil.copy(f'vid/{r}.mp4', f'{OUT}/vid/')
    compact = [{'i': p['id'], 's': p['short'], 'p': p['price'], 'd': (f'{p["discount"]:g}' if p.get('discount') else ''), 'sold': p['sold'], 'n': p.get('score', 0), 'q': p['soldN'],
                'c': p['cat'], 'v': 1 if p['id'] in reels else 0, **({'m': key(p)} if PROD and not p.get('img_url') else {}), **({'mu': p['img_url'], 'sh': p.get('shop_name', '')} if p.get('img_url') else {}), 'u': p.get('url') or '', 'st': p.get('store', 'shopee'),
                **({'g': ','.join(p['themes'])} if p.get('themes') else {}), **({'tk': p['tracked']} if p.get('tracked', 0) >= 2 else {}),
                **({'dr': p['drop']} if p.get('drop', 0) >= 5 else {}), **({'lw': 1} if p.get('atlow') else {}), **({'lo': p['lo30']} if p.get('tracked', 0) >= 2 else {})} for p in products]
    json.dump(compact, open(f'{OUT}/data/p.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump({p['id']: p['hist'] for p in products if p.get('hist')}, open(f'{OUT}/data/ph.json', 'w', encoding='utf-8'), separators=(',', ':'))
    json.dump({s: l for s, l in cats}, open(f'{OUT}/data/cats.json', 'w', encoding='utf-8'), ensure_ascii=False)
    urls = []

    # home
    reel_html = ''.join(f'<a class="reel" href="product.html#{r}" aria-label="{e(byid[r]["short"])}"><video src="vid/{r}.mp4" poster="{thumb(byid[r])}" muted loop playsinline autoplay preload="metadata"></video></a>' for r in reels[:12])
    top = [p for p in products if '客製' not in p['name']][:40]  # products are already in feature-score order
    latest = max((p.get('added') or '') for p in products)
    fresh = [p for p in products if p.get('added') == latest]
    fresh_html = ''
    if latest and len(fresh) < len(products):
        fresh_html = (f'<h2><span class="kick">NEW DROPS · {latest[5:].replace("-", ".")}</span>今日新上架 {len(fresh)} 件</h2><p class="sub">今天新加入的熱銷商品，依銷量排序。</p>'
                      f'<div class="grid">{"".join(static_card(p) for p in fresh[:12])}</div>')
    # theme shelves: products found through theme keywords (創意小物、交換禮物…), best first
    shelves = {}
    for p in products:
        for t in p.get('themes', []):
            if t not in NEW_ALL:
                shelves.setdefault(t, []).append(p)
    newin = {g: [p for p in products if set(p.get('themes', [])) & set(ts)] for g, ts in NEW_GROUPS.items()}
    import re as _re
    from collections import Counter as _C
    def _quads(n):
        n = _re.sub(r'[^\w]', '', n)[:30]
        return {n[i:i + 4] for i in range(len(n) - 3)}
    _qc = _C(q for p in products for q in _quads(p['short']))
    from catalog import COMMODITY as _COMMODITY
    def diverse(ps, k, theme=''):  # one listing per product: skip items sharing 2+ fairly rare 4-character phrases with one shown
        out, used = [], []
        for p in ps:
            if theme and any(w in p['name'] for w in _COMMODITY):
                continue
            sig = {q for q in _quads(p['short']) if 2 <= _qc[q] <= 25 and not any(ch in theme for ch in q[:2])}
            if any(len(sig & u) >= 2 for u in used):
                continue
            used.append(sig)
            out.append(p)
            if len(out) == k:
                break
        return out
    shelf_html = ''.join(
        f'<div class="shelf"><h3>{e(t)}<small>{len(ps)} 件</small></h3><div class="srow">{"".join(static_card(p) for p in diverse(ps, 8, t))}</div></div>'
        for t, ps in sorted(shelves.items(), key=lambda kv: -sum(x['score'] for x in kv[1][:8]))[:5])
    top = diverse(top, 10)
    rank = ''.join(f'<li><a href="product.html#{p["id"]}"><img src="{thumb(p)}" referrerpolicy="no-referrer" alt="" loading="lazy"></a><a href="product.html#{p["id"]}"><span class="t">{e(p["short"])}</span><span class="m"><b>${p["price"]:,}</b>　銷量 {e(p["sold"])}</span></a></li>' for p in top)
    if shelf_html:
        shelf_html = f'<h2><span class="kick">CURATED</span>主題選物：有梗、有設計、送禮不踩雷</h2><p class="sub">用主題關鍵字一件件挑出來的特色商品，日用消耗品不在這裡。</p>{shelf_html}'
    ncat = len(cats)
    brand_items = [p for p in products if p.get('store') == 'other' and p.get('shop_name')]
    _bshops = {}
    for p in brand_items:
        _bshops.setdefault(p['shop_name'], []).append(p)
    brand_home = [x for rnd in itertools.zip_longest(*_bshops.values()) for x in rnd if x][:18]
    nur = sum(1 for p in products if p['soldN'] >= 1000000)
    qs_home = ''.join(quest_html(q) for q in quests[:1])
    hero_ids = ','.join(p['id'] for p in diverse([p for p in products if p.get('themes') and '客製' not in p['name'] and not any(w in p['name'] for w in _COMMODITY)], 30))
    body = (f'<section class="h3" id="h3" data-ids="{hero_ids}"><canvas id="h3c" aria-hidden="true"></canvas><div class="h3scan" aria-hidden="true"></div><div class="h3tip" id="h3tip" hidden></div>'
            f'<div class="w h3in"><div class="h3txt"><span class="kick">DAILY DROP · {TODAY.month:02d}.{TODAY.day:02d}</span><h1>今天，<br>誰會被<em>買爆</em>？</h1>'
            f'<p class="lead">每天從熱銷榜和社群話題裡召喚爆品。銷量就是戰力：UR 是賣破百萬件的傳說級，SSR 也賣破 30 萬。拖曳旋轉，點商品看詳情。</p>'
            f'<div class="stats"><span class="stat"><strong>{len(products)}</strong>件爆品</span><span class="stat"><strong>{nur}</strong>件 UR</span><span class="stat"><strong>{ncat}</strong>個陣營</span></div>'
            f'<div class="h3cta"><a class="btn y" href="dungeon.html">🎮 玩夜市地下城</a><a class="btn o" href="play.html">🎴 翻今日爆品牌</a><a class="btn o" href="gifts.html">🎁 送禮神器</a><a class="btn o" href="deals.html">⏱ 雙11 降價雷達</a></div>'
            f'<div class="snd"><button type="button" id="h3music" aria-pressed="false">♪ 開音樂</button><button type="button" id="h3mic" aria-pressed="false" title="聲音只在你的瀏覽器裡分析，不會錄音或上傳">🎤 聲音互動</button><span class="hint">MOUSE · DRAG · SOUND</span></div><p id="h3note" aria-live="polite"></p></div></div></section>'
            + (f'<h2><span class="kick">REELS</span>爆品短影片</h2><div class="reels" aria-label="爆品短影片">{reel_html}</div>' if reel_html else '')
            + (f'<h2><span class="kick">BRAND STORES</span>品牌官網精選</h2><p class="sub">直接向品牌官網買：{"、".join(x.replace(" 官網", "").replace("官網", "") for x in list(_bshops)[:6])} 等 {len(_bshops)} 個品牌，價格以官網為準。</p><div class="shelf"><div class="srow">{"".join(static_card(p) for p in brand_home)}</div></div><a class="more" href="brands.html" style="text-decoration:none;width:max-content">看全部 {len(brand_items)} 件品牌官網商品</a>' if brand_items else '')
            + f'<h2><span class="kick">RANKING</span>霸主排行 TOP 10</h2><p class="sub">有特色又賣得好的優先；衛生紙、洗衣球這類日用消耗品排在後面。</p><ol class="rank">{rank}</ol>'
            + (f'<h2><span class="kick">SOCIAL QUESTS</span>社群討伐中：網友正在瘋這些</h2><p class="sub">台灣和國外網友在 YouTube、TikTok、Threads 上正在聊的爆品，點了就能看，旁邊直接買。</p><div class="qs">{qs_home}</div>'
               f'<a class="more" href="trending.html" style="text-decoration:none;width:max-content">看全部 {len(quests)} 個副本</a>' if quests else '') +
            (f'<h2><span class="kick">NEW IN · SOCIAL</span>社群新品・國外直送</h2><p class="sub">抖音、小紅書、IG 上爆紅的、日韓新品和聯名限定，還有日本、韓國、泰國、美國直送，台灣賣家就買得到。</p>'
             + ''.join(f'<div class="shelf"><h3><a href="new.html#{e(g)}" style="text-decoration:none">{e(g)} ›</a><small>{len(ps)} 件</small></h3><div class="srow">{"".join(static_card(p) for p in diverse(ps, 10, g))}</div></div>' for g, ps in [kv for kv in newin.items() if len(kv[1]) >= 6][:3])
             + f'<a class="more" href="new.html" style="text-decoration:none;width:max-content">看全部 {len({p["id"] for ps in newin.values() for p in ps})} 件社群新品</a>' if any(newin.values()) else '') +
            shelf_html +
            '<h2><span class="kick">COUPANG</span>酷澎熱銷：火箭速配</h2><p class="sub">酷澎各分類正在熱賣的商品，部分有火箭速配。點分類切換，或直接搜尋酷澎全站。</p>'
            '<div class="cptabs" role="group" aria-label="酷澎分類">' + ''.join(f'<button type="button" class="chip" data-cpw="{w}" data-target="cphome" aria-pressed="{str(i == 0).lower()}">{e(l)}</button>' for i, (w, l) in enumerate(CP_W)) + '</div>'
            + cp_widget(CP_W[0][0], CP_W[0][1]).replace('class="cpw"', 'class="cpw" id="cphome"', 1) + cp_search() +
            '<p class="sub" style="margin-top:6px"><a href="coupang.html" style="color:var(--cyan)">逛酷澎館：9 個分類一次看 ›</a></p>' +
            fresh_html +
            f'<h2><span class="kick">ALL DROPS</span>全部爆品</h2>{tools()}'
            '<h2><span class="kick">GUIDES</span>主題整理</h2><div class="gl">' + ''.join(f'<a class="gc" href="guides/{g["slug"]}.html"><span class="k">{e(g["cat"])}</span><span class="t">{e(g["title"])}</span></a>' for g in guides) + '</div>')
    shell('index.html', f'{SITE}｜網購爆品、社群爆紅、熱銷排行一次看', f'整理網購熱銷爆品 {len(products)} 件、社群爆紅商品與品牌官網精選：附價格、折扣、銷量、開箱影片，每天更新。', body, 'index.html', js='grid', mod='hero3d')
    urls.append('index.html')

    # categories (static top list for search engines + live grid)
    for s, l in cats:
        items = [p for p in products if p['cat'] == s][:24]
        body = (f'<p class="crumb"><a href="../index.html">爆品</a> › {e(l)}</p><h1 style="font:900 clamp(1.8rem,4vw,2.8rem)/1.2 var(--disp);margin:8px 0 6px">{e(l)}熱銷排行</h1>'
                f'<p class="sub" style="margin:0 0 18px">{counts[s]} 件，預設依精選推薦排序，可以改成看銷量、折扣或價格。</p>{tools(False)}'
                f'<noscript><div class="grid">{"".join(static_card(p, "../") for p in items)}</div></noscript>' + (f'<h2 style="margin-top:40px"><span class="kick">COUPANG</span>酷澎也在賣</h2>' + cp_widget(CP_FOR_CAT.get(s, '1920'), dict(CP_W).get(CP_FOR_CAT.get(s, '1920'), '')) + cp_search()))
        shell(f'c/{s}.html', f'{l}熱銷排行：網購爆品 {counts[s]} 件｜{SITE}', f'{l}熱銷商品 {counts[s]} 件，附價格、折扣與銷量，依銷量排行，每天更新。', body, '', 1, cat=s, js='grid')
        urls.append(f'c/{s}.html')
    # social trending quests
    if quests:
        body = (f'<span class="kick" style="margin-top:28px">SOCIAL QUESTS · {len(quests)} ACTIVE</span><h1 style="font:900 clamp(2rem,4.6vw,3.2rem)/1.15 var(--disp);margin:0 0 10px">社群爆紅：網友正在瘋的副本</h1>'
                '<p class="sub" style="margin:0 0 22px">每個副本是一個正在被討論的爆品話題：台灣和國外網友在 YouTube、TikTok、Threads 上的開箱與討論，加上網購買得到的同類商品。</p>'
                f'<div class="qs">{"".join(quest_html(q) for q in quests)}</div>'
                '<p class="qnote">影片和貼文由各平台的創作者公開發布，本站只用 YouTube、TikTok、Threads 的官方嵌入功能播放，點了才會載入，與創作者沒有合作關係；外語內容旁的中文是本站依原標題寫的一句話說明。商品是本站另外挑選的同類熱銷款，不代表影片中的同一件。</p>')
        shell('trending.html', f'社群爆紅：火雞麵、杜拜巧克力、韓國零食開箱一次看｜{SITE}', '台灣和國外網友正在討論的爆紅商品：附 YouTube、TikTok、Threads 開箱與討論，加上網購連結。', body, 'trending.html')
        urls.append('trending.html')




    # ---- new-in / social / overseas ----
    present = sorted({t for p in products for t in p.get('themes', []) if t in NEW_ALL}, key=NEW_ALL.index)
    groups_js = json.dumps({**NEW_GROUPS, 'all': NEW_ALL}, ensure_ascii=False)
    body = ('<span class="kick" style="margin-top:28px">NEW IN · SOCIAL · OVERSEAS</span><h1 class="ptitle">社群新品・國外直送</h1>'
            '<p class="sub" style="margin:0 0 14px">抖音同款、小紅書爆款、IG 爆紅、日韓新品、聯名限定，還有日本、韓國、泰國、美國代購直送。都是台灣賣家在賣、蝦皮買得到的。代購商品出貨時間較長，下單前看清楚賣場說明。</p>'
            '<div class="cats" id="nchips" role="group" aria-label="篩選" style="flex-wrap:wrap"><button class="chip" type="button" data-k="" aria-pressed="true">全部</button>'
            + ''.join(f'<button class="chip" type="button" data-k="{e(g)}" aria-pressed="false">{e(g)}</button>' for g in NEW_GROUPS)
            + ''.join(f'<button class="chip" type="button" data-k="{e(t)}" aria-pressed="false">{e(t)}</button>' for t in present) + '</div>'
            '<div class="tools"><select id="nsort" aria-label="排序"><option value="hot">精選推薦</option><option value="sold">銷量最高</option><option value="low">價格低到高</option></select><span id="ncnt" class="cnt" aria-live="polite"></span></div>'
            '<div id="ngrid" class="grid"></div><button id="nmore" class="more" type="button">再看 48 件</button>'
            f'<script type="application/json" id="ngroups">{groups_js}</script>'
            '<p class="fine" style="margin-top:18px">推廣連結・價格與出貨以購物網站為準。</p>')
    shell('new.html', f'社群新品：抖音同款、小紅書爆款、日韓新品、國外代購｜{SITE}', '抖音、小紅書、IG 爆紅商品與日韓新品、聯名限定，還有日本韓國泰國美國代購，台灣賣家就買得到。', body, 'new.html', js='newin')
    urls.append('new.html')
    # ---- coupang hall ----
    body = ('<span class="kick" style="margin-top:28px">COUPANG HALL</span><h1 class="ptitle">酷澎館</h1>'
            '<p class="sub" style="margin:0 0 14px">酷澎各分類正在熱賣的商品，由酷澎依銷售自動更新；想找別的直接搜尋酷澎全站。點商品會在酷澎開啟，價格與配送以酷澎頁面為準。</p>'
            '<div id="search">' + cp_search() + '</div>'
            '<div class="cpgrid">' + ''.join(cp_widget(w, l) for w, l in CP_W) + '</div>'
            '<p class="fine" style="margin-top:16px">本頁商品輪播與搜尋欄由酷澎夥伴計畫（Coupang Partners）提供，皆為推廣連結：經由連結購買，本站會獲得小額回饋，不會增加你的費用。</p>')
    shell('coupang.html', f'酷澎館：酷澎各分類熱銷商品一次看｜{SITE}', '酷澎家電數碼、玩具、廚具、居家、美食、美妝、運動、寵物、文具熱銷商品，還能直接搜尋酷澎全站。', body, 'coupang.html')
    urls.append('coupang.html')

    # ---- night market dungeon ----
    body = ('<span class="kick" style="margin-top:22px">PIXEL ROGUELITE</span><h1 class="ptitle" style="margin-bottom:12px">夜市地下城</h1>'
            f'<div class="dg" id="dg" data-api="{e(SHOP_API)}" data-gcid="{e(GOOGLE_CLIENT_ID)}"></div>'
            '<p class="sub" style="margin-top:12px">像素動作冒險，手機打開就能玩：故事 40 層、冒險 50 層、最多 4 人連線。全原創像素美術；夜貓老闆和居民的對話由 AI 產生、僅供娛樂；禮品攤的商品頁含推廣連結。' + f'{GAME_RATING}・<a href="terms.html">遊戲服務與儲值條款</a></p>'
            '<p class="sub">其他遊戲：<a href="game.html">買爆獸進化論</a>・<a href="play.html">每日翻牌、爆品比大小、猜價格</a></p>')
    shell('dungeon.html', '夜市地下城｜免費像素動作冒險・免下載・4 人連線', '免費像素動作冒險遊戲，手機電腦打開就能玩、不用下載：故事 40 層、冒險 50 層、最多 4 人連線，在夜市底下的地下城打怪、打造原創裝備、跟莊園居民交朋友。', body, 'dungeon.html', js='dungeon', vp='width=device-width,initial-scale=1,viewport-fit=cover', extra_head=DG_APP_HEAD + HREFLANG_DG + DG_LD('zh'))
    dg_app_files()
    shell_en_dungeon(); urls.append('en/dungeon.html'); urls.append('en/terms.html')
    urls.append('dungeon.html')
    # ---- evolve game ----
    body = ('<span class="kick" style="margin-top:22px">ARCADE · EVOLVE</span><h1 class="ptitle" style="margin-bottom:12px">買爆獸進化論</h1>'
            '<div class="arena" id="arena"><canvas id="gcv" aria-label="遊戲畫面：操控買爆獸吃商品、躲敵人"></canvas>'
            '<button type="button" id="gdash" hidden aria-label="衝刺">衝刺</button>'
            '<div class="gov" id="gstart"><h2>吃爆品，<em>進化</em>！</h2>'
            '<p class="sub">操控你的買爆獸吃掉場上的商品球（都是網購真的熱銷款），稀有度越高經驗越多。躲開「爛貨炸彈」和會追人的「砍單鬼」。吃夠了就當場進化，一局最多進化 4 次。</p>'
            '<ul class="evo" id="gevo"></ul>'
            '<div class="lvrow">獵人等級 <b id="glv">Lv.1</b><span class="lvbar"><i id="glvbar"></i></span></div><p class="sub" id="glvtxt" style="font-size:.8rem;margin:0"></p>'
            '<ul class="perks" id="gperks"></ul>'
            '<button type="button" class="btn y" id="gbegin" disabled>▶ 開始（75 秒）</button>'
            '<p class="ctrl">電腦：滑鼠移動或 WASD／方向鍵，點擊或空白鍵衝刺，P 暫停｜手機：按住畫面任一處拖曳移動，點兩下或按「衝刺」</p><p id="gdaily"></p></div>'
            '<div class="gov" id="gover" hidden><h2 class="gt">時間到！</h2><div class="gs">0</div><p class="sub gsub"></p><p class="glvup"></p>'
            '<p class="sub" style="margin:0 0 4px;font-size:.8rem">這局你吃到的爆品（點了看商品）</p><div class="gloot"></div>'
            '<div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center"><button type="button" class="btn y gagain">↻ 再玩一次</button><button type="button" class="btn o gshare">分享戰績</button><button type="button" class="btn o gmenu">進化圖鑑</button></div></div></div>'
            '<div class="gtools"><button type="button" id="gmute" aria-pressed="true">🔊 音效開</button><button type="button" id="gfull">⛶ 全螢幕</button></div>'
            '<p class="sub">進度（等級、最高分、進化圖鑑）只存在你這台裝置的瀏覽器。更多小遊戲：<a href="play.html">每日翻牌・爆品比大小・猜價格</a>。</p>')
    shell('game.html', f'買爆獸進化論：吃爆品進化的小遊戲｜{SITE}', '操控買爆獸吃網購熱銷商品、躲爛貨炸彈，一局進化 4 次，越玩等級越高。電腦手機都能玩。', body, 'dungeon.html', js='game')
    urls.append('game.html')
    # ---- games ----
    body = ('<span class="kick" style="margin-top:28px">ARCADE</span><h1 class="ptitle">爆品遊戲場</h1>'
            '<p class="sub" style="margin:0">每天翻牌測運勢、比比看哪件賣得多、猜猜價格。商品都是真的網購熱銷款，玩完順便逛。</p>'
            '<div class="gtabs" role="tablist"><button type="button" role="tab" data-tab="gacha">🎴 每日翻牌</button><button type="button" role="tab" data-tab="hl">⚔ 爆品比大小</button><button type="button" role="tab" data-tab="price">💰 猜價格</button></div>'
            '<section class="gpanel" id="gacha" role="tabpanel"><div class="gwrap"><div id="gstage" class="gstage"><div class="gc3 big"><div class="gci"><div class="gcb"><b>今天\n買這個</b></div></div></div></div>'
            '<div><h2 style="margin:0 0 6px">今日爆品翻牌</h2><p class="sub" style="margin:0 0 6px">每天 3 次單翻、1 次十連翻（十連必出 SR 以上）。翻到的稀有度就是你今天的運勢，翻到的商品會收進圖鑑。</p>'
            '<p class="sub" style="margin:0 0 10px;font-size:.82rem">機率：UR 4%・SSR 12%・SR 26%・R 30%・N 28%（稀有度依購物網站顯示的銷量）</p>'
            '<div class="gbtns"><button type="button" class="btn y" id="gone">⚡ 單翻</button><button type="button" class="btn o" id="gten">✦ 十連翻</button></div><p class="gleft" id="gleft"></p><div id="gres" aria-live="polite"></div></div></div>'
            '<h3 style="font:900 1.2rem var(--disp);margin:26px 0 0">我的圖鑑 <small id="gdexn" style="font:600 .85rem var(--hud);color:var(--muted)"></small></h3><div class="dex" id="gdex"></div>'
            '<p class="fine">翻牌紀錄只存在你這台裝置的瀏覽器，不會上傳。</p></section>'
            '<section class="gpanel" id="hl" role="tabpanel" hidden><h2 style="margin:0 0 6px">爆品比大小</h2><p class="sub">右邊這件在購物網站上賣得比左邊多，還是比較少？連續答對越多越強。</p>'
            '<div class="score"><span>連勝<b id="hls">0</b></span><span>最佳<b id="hlb">0</b></span></div>'
            '<div class="hl"><div class="hlc" id="hlL"></div><div class="vs" aria-hidden="true">VS</div><div class="hlc" id="hlR"></div></div>'
            '<p class="gmsg" id="hlmsg" aria-live="polite"></p><div class="hlbar"><button type="button" class="btn y" data-hl="more">▲ 賣更多</button><button type="button" class="btn o" data-hl="less">▼ 賣更少</button><button type="button" class="btn o" id="hlagain" hidden>↻ 再玩一次</button></div>'
            '<p class="fine">銷量為購物網站顯示的約略數字（例如「1萬+」）。</p></section>'
            '<section class="gpanel" id="price" role="tabpanel" hidden><h2 style="margin:0 0 6px">猜價格</h2><p class="sub">看圖猜價格，一輪 10 題，看你是網購新手還是價格之神。</p>'
            '<div class="score"><span>題目<b id="prn">1 / 10</b></span><span>答對<b id="prs">0</b></span></div>'
            '<div class="prq" id="prq"></div><p class="gmsg" id="prmsg" aria-live="polite"></p><div class="propt" id="propt"></div><button type="button" class="btn y" id="pragain" hidden>↻ 再玩一輪</button>'
            '<p class="fine">價格以資料更新當天購物網站顯示為準，現在的價格可能不同。</p></section>')
    shell('play.html', f'爆品遊戲場：每日翻牌、比大小、猜價格｜{SITE}', '每天翻一張爆品卡測運勢，玩爆品比大小和猜價格，商品都是網購真實熱銷款。', body, 'dungeon.html', extra_head='', js='play')
    urls.append('play.html')
    # ---- brand stores ----
    if brand_items:
        body = ('<span class="kick" style="margin-top:28px">BRAND STORES</span><h1 class="ptitle">品牌官網精選</h1>'
                f'<p class="sub" style="margin:0 0 18px">{len(_bshops)} 個品牌官網、{len(brand_items)} 件商品：寢具、木頭玩具、彩妝、冷凍披薩、包包和餐具。點進去看商品，再到品牌官網下單。</p>'
                + ''.join(f'<h2>{e(shop.replace("官網", "").strip())}<span class="sub" style="font-size:.6em;margin-left:8px">{len(ps)} 件</span></h2><div class="shelf"><div class="srow">{"".join(static_card(p) for p in ps)}</div></div>' for shop, ps in _bshops.items())
                + '<p class="fine" style="margin-top:20px">價格以品牌官網結帳頁為準，活動價可能隨時調整。本站含推廣連結，經由連結購買不會增加你的費用。</p>')
        shell('brands.html', f'品牌官網精選：寢具、木頭玩具、彩妝、披薩、包包｜{SITE}', f'{len(_bshops)} 個品牌官網的 {len(brand_items)} 件商品：A-nice 雅妮詩寢具、Tender Leaf 木頭玩具、Cath Kidston 包包餐具、KISSME 彩妝等。', body, 'index.html')
        urls.append('brands.html')
    # ---- gift finder ----
    def opts(k, items, on):
        return '<div class="cats" role="group">' + ''.join(f'<button type="button" class="chip" data-k="{k}" data-v="{v}" aria-pressed="{str(v == on).lower()}">{t}</button>' for v, t in items) + '</div>'
    body = ('<span class="kick" style="margin-top:28px">GIFT FINDER</span><h1 class="ptitle">送禮神器</h1>'
            '<p class="sub" style="margin:0 0 18px">交換禮物、生日、謝謝同事，選三個條件，直接給你 6 件。不滿意就換一批。</p>'
            '<div class="gpanel"><div class="gq"><h3>送給誰</h3>' + opts('who', [('work', '同事・交換禮物'), ('friend', '朋友'), ('love', '另一半'), ('elder', '長輩'), ('kid', '小孩'), ('me', '犒賞自己')], 'work') + '</div>'
            '<div class="gq"><h3>預算</h3>' + opts('budget', [('a', '300 以下'), ('b', '300～799'), ('c', '800～1,999'), ('d', '2,000 以上'), ('x', '都可以')], 'b') + '</div>'
            '<div class="gq"><h3>風格</h3>' + opts('style', [('fun', '😂 搞笑有梗'), ('heal', '🧸 療癒可愛'), ('use', '🔧 實用'), ('lux', '✨ 有質感'), ('food', '🍫 吃的')], 'fun') + '</div>'
            '<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center"><button type="button" class="btn y" id="gagain">↻ 換一批</button><span class="sub" id="gsum" style="margin:0" aria-live="polite"></span></div></div>'
            '<div class="gout" id="gout"></div><p class="fine" style="margin-top:18px">依商品名稱、分類和銷量自動挑選，不是實際使用心得。點進去看商品詳情；購物連結為推廣連結，價格以購物網站為準。</p>')
    shell('gifts.html', f'送禮神器：交換禮物、生日禮物怎麼挑｜{SITE}', '選對象、預算、風格，從上千件熱銷商品挑出 6 件禮物：交換禮物、同事、另一半、長輩、小孩都有。', body, 'gifts.html', js='gifts')
    urls.append('gifts.html')
    # ---- 雙11 deals radar ----
    body = ('<span class="kick" style="margin-top:28px">11.11 RADAR</span><h1 class="ptitle">雙11 降價雷達</h1>'
            '<p class="sub" style="margin:0 0 10px" id="cdlab">距離雙11 還有</p>'
            '<div class="cd" id="cd" role="timer"><span><b data-u="d">--</b>天</span><span><b data-u="h">--</b>時</span><span><b data-u="m">--</b>分</span><span><b data-u="s">--</b>秒</span></div>'
            '<p class="sub">本站每天記錄商品價格，目前有 <b id="trk">…</b> 件累積兩天以上的價格紀錄。降價是跟這件商品自己近 30 天的價格比，不是跟賣場標的「原價」比。</p>'
            '<h2><span class="kick">REAL DROPS</span>真降價：比近 30 天最高價便宜</h2><div class="grid" id="drops"></div>'
            '<h2><span class="kick">30-DAY LOW</span>現在是近 30 天最低價</h2><div class="grid" id="lows"></div>'
            '<h2><span class="kick">ON SALE</span>賣場標示折扣最多的特色商品</h2><p class="sub">折扣是賣場自己標示的原價比較，參考就好；只列 3～7 折（低於 3 折多半是原價灌水），日用消耗品不列。</p><div class="grid" id="offs"></div>'
            '<p class="fine" style="margin-top:20px">價格以購物網站結帳頁為準。本站含推廣連結，經由連結購買不會增加你的費用。</p>')
    shell('deals.html', f'雙11 降價雷達：真降價、近 30 天最低價｜{SITE}', '雙11 倒數，加上每天記錄的價格：哪些熱銷商品真的比近 30 天便宜。', body, 'deals.html', js='deals')
    urls.append('deals.html')
    # category index on home is the chips; also link list in guides page

    # product (single template, hash routed, not indexed: thin data pages)
    pbody = '<div id="pd"></div><h2>同分類爆品</h2><div id="rel" class="grid"></div>'
    shell('product.html', f'商品｜{SITE}', '網購爆品商品資訊：價格、折扣、銷量與短影片。', pbody, '', 0, noindex=True, js='product')

    # guides (reuse topic content, new skin)
    def find(prefix):
        for q in picks:
            if q['name'].startswith(prefix):
                return q
    store = {'coupang': '酷澎'}
    for g in guides:
        items = [find(n) for n in g['picks']]
        rows = ''.join(f'<tr><td>{e(q["name"])}</td><td>${int(q["price"]):,}</td><td>{e(q.get("rating", "—"))}</td><td>{e(q.get("sold", "—"))}</td><td>{store.get(q.get("store"), "蝦皮")}</td></tr>' for q in items)
        cards = ''.join(f'<li style="margin:0 0 14px"><b>{e(q["name"])}</b>（${int(q["price"]):,}）<br>{e(q.get("why", ""))}<br><a class="cta" style="min-height:44px;margin-top:8px;font-size:1rem" href="{e(q["url"])}" target="_blank" rel="sponsored nofollow noopener">到{store.get(q.get("store"), "蝦皮")}看這件</a></li>' for q in items)
        body = (f'<article class="art"><p class="crumb"><a href="../index.html">爆品</a> › <a href="../guides.html">主題整理</a></p><h1>{e(g["title"])}</h1>'
                f'<p class="note">本文含推廣連結；內容依商品頁公開資訊整理，更新於 {g["updated"]}。</p>'
                + ''.join(f'<p>{e(x)}</p>' for x in g['intro']) +
                '<h2>怎麼挑</h2><ol class="crit">' + ''.join(f'<li><b>{e(a)}</b>：{e(b)}</li>' for a, b in g['criteria']) + '</ol>'
                f'<h2>比較表</h2><div class="tbl"><table><thead><tr><th>商品</th><th>價格</th><th>評價</th><th>銷量／評價數</th><th>通路</th></tr></thead><tbody>{rows}</tbody></table></div>'
                f'<h2>逐件重點</h2><ol>{cards}</ol><h2>常見問題</h2><dl>' + ''.join(f'<dt>{e(q)}</dt><dd>{e(a)}</dd>' for q, a in g['faq']) + '</dl></article>')
        shell(f'guides/{g["slug"]}.html', f'{g["title"]}｜{SITE}', g['desc'], body, 'guides.html', 1)
        urls.append(f'guides/{g["slug"]}.html')
    gl = ''.join(f'<a class="gc" href="guides/{g["slug"]}.html"><span class="k">{e(g["cat"])}</span><span class="t">{e(g["title"])}</span></a>' for g in guides)
    catl = ''.join(f'<a class="chip" href="c/{s}.html">{e(l)}<small>{counts[s]}</small></a>' for s, l in cats)
    shell('guides.html', f'主題整理與分類｜{SITE}', '依生活情境整理的好物清單與各分類熱銷排行。', f'<h1 style="font:900 2.4rem/1.2 var(--disp);margin:28px 0 14px">主題整理</h1><div class="gl">{gl}</div><h2>分類排行</h2><div class="cats" style="flex-wrap:wrap">{catl}</div>', 'guides.html')
    urls.append('guides.html')
    # about page removed 10/6 (user: redundant); keep the URL as a redirect so old links still work
    open(f'{OUT}/about.html', 'w').write('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url=./"><link rel="canonical" href="https://youbi-shop.com/"><a href="./">今天買這個</a>')
    shell('disclosure.html', f'推廣連結與隱私說明｜{SITE}', '今天買這個的推廣連結揭露與隱私說明。',
          '<article class="art"><h1>推廣連結與隱私說明</h1><p>本站商品連結為蝦皮、酷澎與合作品牌的推廣連結（聯盟行銷）。經由連結購買，本站會獲得小額回饋，不會增加你的費用，也不影響商品的挑選。不收醫療、減肥、保健、菸酒、成人、金融類商品。</p>'
          '<p>商品圖片、名稱、價格、折扣與銷量來自購物網站公開的商品資訊，可能隨時變動，請以購物網站結帳頁為準。</p><p>本站不要求註冊。本站使用 Google Analytics 統計瀏覽量與點擊（例如哪一頁、哪個商品連結被點），會使用 Cookie，不會用來辨識你個人，也關閉了 Google 的廣告個人化功能；你可以用瀏覽器設定封鎖 Cookie，或安裝 Google Analytics 停用外掛。點擊推廣連結後，購物網站可能依其政策使用 Cookie 記錄推薦來源。影片與貼文嵌入（YouTube、TikTok、Threads）在你點開後才會載入，載入後適用各平台的隱私政策。酷澎館和各頁的「酷澎熱銷」輪播、搜尋欄由酷澎夥伴計畫提供，捲動到那裡時才會從酷澎載入，載入後適用酷澎的隱私政策。首頁的「聲音互動」要你按下按鈕並允許後才會使用麥克風，聲音只在你的瀏覽器裡即時分析音量，不會錄音、儲存或上傳；遊戲的翻牌圖鑑和紀錄只存在你自己的瀏覽器。</p><p>右下角的找東西小幫手：你打的那句話會送到本站的伺服器，交給 Cloudflare Workers AI 轉成分類、關鍵字和預算（不會連同你的身分資料，也不會用來訓練模型），推薦的商品都是從本站商品挑出來的。為了讓你下次一打開就看到想找的東西，小幫手會在你自己的瀏覽器記下你在本站看過的分類、搜尋過的字和點過的商品；這些紀錄不會上傳到伺服器，也不會跟別的網站或 App 交換。你可以在小幫手裡按「清除我的紀錄」刪除並停止記錄，或清除瀏覽器的網站資料。</p><p>夜市地下城的 AI 角色「夜貓老闆」：你按的快捷問題或打的字（40 字內），會連同當下的遊戲狀態（樓層、血量、等級、裝備名稱）送到本站伺服器，交給 Cloudflare Workers AI 產生回覆。伺服器不保存聊天內容，也不會用來訓練模型；送出前後都會自動過濾不適當的內容。回覆由 AI 自動產生，僅供娛樂，可能有錯。</p><p>夜市地下城的連線合作聊天：訊息在兩位玩家的裝置之間直接傳送，本站伺服器看不到也不保存。朋友房預設可以打字；陌生人配對預設關閉，要玩家自己開啟。送出和收到時都會自動擋下網址、聯絡方式、長串數字、詢問個資或約見面、交易與不當內容。你按「檢舉並封鎖」時，會把對方最近 10 句訊息和對方的系統代號送到伺服器，保存 30 天供人工查看；3 天內被 3 位不同玩家檢舉的人，會暫停 7 天陌生人配對。</p><p>「夜市地下城」的進度（等級、裝備、夜市幣、莊園、圖鑑等）存在你的瀏覽器；不用註冊也能玩。你自己選擇建立遊戲帳號或用 Google 登入時，伺服器只會保存：隨機產生的帳號編號、救援碼的雜湊值（無法反推）、Google 帳號識別碼（只存識別碼，不存 email、姓名或大頭貼）、雲端存檔（就是上面那些遊戲進度）、金燈籠與造型紀錄、儲值訂單紀錄，以及你登記購物回饋時輸入的蝦皮訂單編號。排行榜、玩家名稱與好友功能會用到你的系統代號、你自己取的玩家名稱（會自動過濾不當字詞）、等級與成績；加好友要雙方同意，好友只看得到名稱、等級和是否在線。「回饋」表單送出的內容會連同等級、遊戲版本與手機／電腦類型保存，供我們改版參考，內容裡的 email 與電話會在送出時自動遮掉；回饋不需要帳號，也不會記錄你是誰。想刪除帳號、雲端存檔或回饋內容，請用回饋表單（類別選「其他」）寫下帳號編號前 8 碼，我們會在 7 天內刪除。付款由綠界科技處理，本站不會取得你的卡號。詳見<a href="terms.html">遊戲服務與儲值條款</a>。</p></article>')

    # ---- game terms (遊戲服務與儲值條款) ----
    owner = e(SHOP_OWNER) if SHOP_OWNER else '（儲值開放前公布）'
    contact = f'<a href="mailto:{e(SHOP_CONTACT)}">{e(SHOP_CONTACT)}</a>' if SHOP_CONTACT else '（儲值開放前公布）'
    draft = '' if (SHOP_API and SHOP_OWNER and SHOP_CONTACT) else '<p class="fine" style="color:var(--pop)">金燈籠儲值尚未開放，本條款為預告版本，開放前可能調整。</p>'
    shell('terms.html', f'夜市地下城 遊戲服務與儲值條款｜{SITE}', '夜市地下城的遊戲分級、虛擬貨幣、付款、退款與帳號規則。',
          '<article class="art"><h1>夜市地下城 遊戲服務與儲值條款</h1>' + draft +
          f'<h2>一、營運者與聯絡方式</h2><p>營運者：{owner}。客服信箱：{contact}。我們會在 3 個工作天內回覆。</p>'
          f'<h2>二、遊戲分級與費用</h2><p>本遊戲分級為「{GAME_RATING}」，適合 15 歲以上：像素風格打鬥，攻擊時有血花效果，部分樓層（例如萬聖節限定的「夜市怪談」）有恐怖場景；不含殘虐、肢解畫面。血花效果可以在遊戲設定中關閉。遊戲本身免費遊玩；部分外觀造型需要使用「金燈籠」兌換。所有付費內容都只改變角色外觀，不影響遊戲強弱。本遊戲沒有任何機率性（抽獎、轉蛋）商品，每一樣商品的內容和價格都事先標示清楚。</p>'
          '<h2>三、虛擬貨幣</h2><ul><li><b>夜市幣</b>：在冒險中取得，或用金燈籠兌換（1 金燈籠 = 20 夜市幣）。存在你的遊戲存檔（這台裝置的瀏覽器；有帳號時可以雲端備份），不能兌換成金燈籠或現金。清除瀏覽器資料又沒有雲端備份時，夜市幣會跟著存檔消失。</li>'
          '<li><b>金燈籠</b>：以新台幣購買，或由活動、購物回饋取得，存在本站伺服器。只能在本遊戲兌換外觀造型或兌換成夜市幣（單向），不能兌換現金、不能轉讓給其他帳號、也不能兌換實體商品。</li></ul>'
          '<h2>四、付款與發票</h2><p>付款由綠界科技（ECPay）處理，本站不會取得你的信用卡號或帳戶資料。標示價格為新台幣含稅價格。付款完成後依法開立電子發票。</p>'
          '<h2>五、退款</h2><ul><li>購買後 7 天內，購得的金燈籠如果還沒有使用，可以不說明理由申請全額退款。</li>'
          '<li>已經用金燈籠兌換的造型或夜市幣屬於線上數位內容，兌換前會再次顯示數量並經你同意，兌換後就不能退回金燈籠或退款。</li>'
          '<li>重複扣款、付款成功卻沒有入帳、或系統錯誤造成的損失，一律全額退款或補發。</li>'
          '<li>申請方式：寄信到客服信箱，附上帳號編號前 8 碼（在遊戲「造型商城 → 帳號」）和綠界交易編號。退款會在確認後 14 天內退回原付款方式。</li></ul>'
          '<h2>六、帳號</h2><p>你可以在遊戲標題選單的「☁ 存檔」免費建立遊戲帳號或用 Google 登入（第一次儲值或用金燈籠兌換造型時也會自動建立），建立時會給你一組「救援碼」。帳號就是一份存檔：登出時會先把進度上傳到帳號，這台裝置再回到全新存檔。換裝置或清除瀏覽器資料時，用救援碼或綁定的 Google 帳號找回。請妥善保管救援碼，不要告訴別人；如果救援碼遺失又沒有綁定 Google，我們可以依你提供的綠界交易紀錄協助找回付費帳號。</p>'
          '<h2>七、未成年人</h2><p>未滿 18 歲的玩家，請先取得父母或法定代理人同意後再購買金燈籠。</p>'
          '<h2>八、購物回饋（開放後適用）</h2><p>透過本站的商品連結在購物網站下單，訂單完成後在遊戲中登記訂單編號，經確認確實經由本站連結購買，本站會贈送金燈籠。回饋是本站自行提供的贈品，與購物網站無關；以購物網站提供給本站的推廣報表為準，取消、退貨或退款的訂單不回饋。回饋比例會在遊戲中標示，調整前會先公告。</p>'
          '<h2>九、禁止行為</h2><p>使用外掛、竄改程式或封包、利用漏洞取得金燈籠或造型，本站可以先通知後收回不當取得的內容；情節重大者停止帳號，未使用的付費金燈籠依比例退款。</p>'
          '<h2>十、服務變更與終止</h2><p>如果要停止金燈籠的販售或終止遊戲服務，會至少在 30 天前於本頁和遊戲中公告。服務終止時，你未使用的付費金燈籠可以依比例申請退款。</p>'
          '<h2>十一、個人資料</h2><p>伺服器只保存遊戲運作需要的資料，詳見<a href="disclosure.html">推廣連結與隱私說明</a>。</p>'
          '<h2>十二、其他</h2><p>本條款以中華民國法律為準據法。條款修改會在本頁公告並標示更新日期，重大變更會在遊戲中通知。</p>'
          f'<p class="fine">最後更新：{TODAY.isoformat()}</p></article>')
    urls.append('terms.html')
    shell('404.html', f'找不到頁面｜{SITE}', '找不到這個頁面。', '<h1 style="font:900 2.4rem var(--disp)">這頁不見了</h1><p><a href="index.html">回去看爆品</a></p>')
    urls += ['disclosure.html']
    sm = ''.join(f'<url><loc>{BASE}{"" if u == "index.html" else u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>' for u in urls)
    open(f'{OUT}/sitemap.xml', 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n')
    open(f'{OUT}/CNAME', 'w').write('youbi-shop.com\n')
    print('built', len(products), 'products', len(reels), 'reels', len(urls), 'indexed pages')


if __name__ == '__main__':
    build()
