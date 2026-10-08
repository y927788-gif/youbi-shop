# youbi-shop.com 每日上架流程

網站：https://youbi-shop.com（GitHub Pages，repo y927788-gif/youbi-shop，main 分支根目錄）。
這個 `_build/` 資料夾是建置程式和累積資料庫，Jekyll 不會公開它。

## 每天做的事
1. **讀狀態**：從 `https://raw.githubusercontent.com/y927788-gif/youbi-shop/main/_build/...` 抓
   `build2.py catalog.py ingest.py harvest_prep.js data/master.json data/state.json data/reels.json data/guides.json data/picks.json data/quests.json`
   放到工作資料夾（data/ 放 data/）。
2. **抓商品（只用後台介面，慢慢來）**：用「今天買這個」Chrome（deviceId bc423f97…）開
   `https://affiliate.shopee.tw/offer/product_offer`，確認右上角是「木木東京(木々東京)」，用 javascript_tool 貼上 `harvest_prep.js`。
   先 screenshot（scale 0.3 即可）記下 coordinate frame 寬度 W；第一次 prep 後用 `window.__H.rects()` 取對話框位置，點擊座標＝CSS 座標 × W / innerWidth。
   **A. 主題關鍵字（重點，使用者 10/6：要有特色的商品，日用雜貨排後面）**：從 state.themes[next_theme] 起取 themes_per_day 個（到尾就繞回開頭，繞回時 theme_pages 兩個數字都 +3）。每個關鍵字一個 browser_batch：
   - **一個關鍵字一個 browser_batch**。先 javascript_tool：`window.scrollTo(0,0);const i=document.querySelector('input[placeholder*=關鍵字]');i.focus();i.select()`（10/6 發現：翻到第 5 頁後搜尋框在畫面外，直接 triple_click 打字會打不進去）→ type 關鍵字 → key Return → wait 5
   - javascript_tool `await window.__H.prep('<關鍵字>', theme_pages[0], theme_pages[1])`（回傳 modal 要是 block；回傳 'same-results…' 代表搜尋沒刷新，重新聚焦搜尋框再搜一次，不要硬做）
   - 真實點擊 Sub_id1 → type `web` → 點「取得連結」→ wait 7 → `await window.__H.clearSel()`
   **B. 大分類**：從 tabs[next_tab] 起 tab_batches_per_day 個分頁，各做 `prep('<分頁>', next_page, next_page+4)` 一批（分頁名稱就是頁面上的標籤，prep 會自己切換）。做完 next_tab 往後移；8 個分頁都輪過一次後 next_page += 5（超過 max_page 回到 1）。
   全部完成後 `window.__H.save()`。**出現驗證（captcha）、登入頁或任何異常就立刻停，回報使用者，不要重試。**
3. **收檔**：CSV（批量商品連結*.csv）和 youbi_harvest_*.json 會存到 `D:\ComfyUI`。用 device_list_dir 找今天的新檔，device_stage_files 拿進容器。
4. **建置**（`assets_src/` 的 hero3d.js play.js gifts.js deals.js game.js newin.js dungeon.js 也要一起下載；沒有的話 build2.py 會自己從 repo 抓）：`python3 ingest.py <今天的 csv 和 json>` → `python3 catalog.py` → `python3 build2.py --prod`（輸出在 out2/）。
   更新 state.json（next_theme、theme_pages、next_tab、next_page 照上面規則），history 加一筆。
   價格追蹤：ingest.py 每次會把當天價格記進 master 的 ph，catalog.py 算出近 30 天最低、降幅，雙11 降價雷達（deals.html）和商品頁的價格線用這些資料。
   國外代購商品可以收（使用者 10/6：國內外都可），catalog.py 會濾掉「網址代購、代購服務、客訂」這類非商品賣場和仿品字眼。
   酷澎：網站用酷澎夥伴計畫官方的動態廣告（id 1912～1920，分類最佳）和搜尋欄（coupa.ng/cpXDzB）嵌入，不用每天處理。
   排序：catalog.py 的特色分數（COMMODITY 日用消耗品降權、FEATURE 特色字與主題加權、近似商品只留一件），首頁有「主題選物」貨架。
5. **上傳**：Chrome 開 `https://github.com/y927788-gif/youbi-shop/upload/main/<資料夾>`，用 file_upload 放檔（每次 < 6MB），
   等「Uploading x of y」消失、檔名數量對了再按 Commit changes。要上傳：
   根目錄 html（index game trending new play gifts deals coupang dungeon terms product about disclosure guides 404）＋ sitemap.xml、c/*.html、guides/*.html、data/p.json data/cats.json data/ph.json、assets/（全部）、
   `_build/data/master.json` 和 `_build/data/state.json`。
6. **驗證**：等 GitHub Pages 部署（Actions 可能排隊幾分鐘），打開 https://youbi-shop.com 確認件數和「今日新上架」。

## 界線
- 只用後台介面操作，不直接呼叫後台 API（會觸發防機器人驗證）。
- 每次執行最多 14 批（每天兩次：12:46、23:46），翻頁之間要停 1～2 秒；出現驗證就停。
- 不收：醫療、減肥、保健、菸酒、成人、金融類（catalog.py 的 BAN）。
- 推廣連結揭露文字不能拿掉。

## 分享預覽圖（og:image）
- 每頁的 og:image 指向 https://youbi-shop.com/og/<頁面>.jpg（build2.py 的 OGPAGE，其他頁用 default.jpg）。圖已上傳在 /og/，平常不用重做。
- 想換圖：在 site/ 跑 `python3 make_og.py <遊戲截圖.png>`（需要先 build 出 out2/data/p.json），會產生 og/*.jpg，上傳到 repo 的 og/ 資料夾。
