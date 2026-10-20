# 今天買這個 社群素材工具（10/6 版）

黃黑視覺，和 youbi-shop.com 同一套。資料來自網站每天更新的 `https://youbi-shop.com/data/p.json`（熱銷商品：名稱、價格、折數、銷量、分類、標籤、商品圖）。

## 準備
```
mkdir -p social/shots && cd social
B=https://raw.githubusercontent.com/y927788-gif/youbi-shop/main/_build/social
curl -sSfO $B/kit.py -O $B/reel.py
for f in storage_box dryer_wind bubble_shield lightning; do curl -sSf -o shots/$f.png $B/shots/$f.png; done
curl -sSfL -o Anton-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf || true   # 數字字型，抓不到會自動改用思源黑體
```

## 圖卡（1080x1350，IG 4:5；X、Threads 用同一張）
| 指令 | 用途 | 帶連結？ |
|---|---|---|
| `kit.py rank --cat 分類 / --tag 標籤 / --ids … --title …` | 熱銷排行 Top 5 | 否 |
| `kit.py trend --tag 小紅書爆款 --title …` | 社群爆紅 4 宮格 | 否 |
| `kit.py guess --id … --opts "A. …" "B. …" "C. …"` | 猜銷量（_q 題目＋_a 答案，做輪播） | 否 |
| `kit.py vs --a … --b … --q …` | 二選一 | 否 |
| `kit.py list --title … --items "標題｜說明" …` | 清單／痛點解法 | 否 |
| `kit.py game --shot shots/xxx.png --title … --sub …` | 夜市地下城話題 | 否 |
| `kit.py deal --id … --hook …` | 降價雷達（單品） | 推薦文配圖 |
| `kit.py power --id … --hook …` | 今日爆品（單品） | 推薦文配圖 |

共同參數：`--name 商品ID=短名`（每件商品都要給一個好懂的短名，不要用整串關鍵字標題）、`--exclude ID …`、`--out 檔名`、`--date M/D`。

## 短影音（1080x1920、約 12～18 秒、無聲 MP4；IG Reels、Threads 用，不發 X）
```
python3 reel.py rank --tag 抖音同款 --title "抖音紅到台灣，這週賣最多的 5 樣" --name ID=短名 … --cover --out reel.mp4
python3 reel.py deal --ids ID1 ID2 ID3 --title "這週真的有在降價的 3 樣" --name … --out reel.mp4
```
音樂在 IG 發佈時用 App 內建音樂庫加。

## 檢查（每次都要）
- 自動挑商品（rank、trend、reel）會跳過「照片雜亂度」超過 38 的賣場圖（字和拼貼很多的那種），stderr 會列出跳過了哪些；單品模板（power、deal、guess）遇到雜亂照片會印警告，請換一件。
- 自動挑出來的短名常常還是很怪（例如「好惠買」是店名不是商品），每件都要用 --name 給一個好懂的名字。
- 用 Read 看每張圖、影片抽 3 格（`ffmpeg -ss 秒數 -i x.mp4 -frames:v 1 f.png`）。
- 商品照片裡有卡通角色、名人、品牌吉祥物、成人或醫療療效字眼 → `--exclude` 換掉。標題提到知名角色的商品會自動排除，但照片還是要看。
- 分類資料有時不準（例如 kitchen 混到泡麵），排行標題要和實際商品相符，不符就用 `--ids` 自己挑。
- 圖上和標題不強調「蝦皮」「酷澎」等通路名稱：重點是「今天買這個幫你篩好了」（實際銷量排行、價格追蹤、整理清單），不是哪個平台有賣。
- 價格、銷量、折數只用資料裡的數字；圖上不放網址（只有 youbi-shop.com 品牌字）。
