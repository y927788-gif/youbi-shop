"""今天買這個 短影音模板：直式 1080x1920、約 16 秒、30fps、無聲 MP4（IG Reels／Threads 用；X 會卡處理中，不發 X）。

  python3 reel.py rank --cat clean --title "清潔用品賣最多的 5 樣" [--name 商品ID=短名 ...] [--out reel.mp4]
  python3 reel.py rank --tag 抖音同款 --title "抖音紅到台灣的 5 樣"
  python3 reel.py rank --ids ID1 ID2 ID3 ID4 ID5 --title "..."          自己指定 5 件（第 1 個是第 1 名）
  python3 reel.py deal --ids ID1 ID2 ID3 --title "這週真的有在降價的 3 樣"    降價雷達版（每件顯示折數）
  加 --cover 另外輸出封面 PNG（同檔名 .jpg）。
倒數格式：第 5 名 → 第 1 名，最後一張是互動問題。音樂請在 IG 發佈時用 App 內建的音樂庫加（不要用沒授權的音樂）。
"""
import argparse, subprocess, sys, os
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import font, num, Y, INK, MUTED, BG, PANEL, RED, wrap, short, sold_txt, price

W, H, FPS = 1080, 1920, 30
INTRO, PER, OUTRO = 2.2, 2.6, 2.4


def eob(x):
    x = min(max(x, 0), 1); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3


def bg():
    im, d = kit.base('', W, H)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kind', choices=['rank', 'deal'])
    for k in ['cat', 'tag', 'title', 'sub', 'data', 'out', 'ask']: ap.add_argument('--' + k)
    ap.add_argument('--ids', nargs='*'); ap.add_argument('--name', action='append', default=[]); ap.add_argument('--cover', action='store_true'); ap.add_argument('--exclude', nargs='*', default=[])
    ap.add_argument('--date', default=kit.today())
    a = ap.parse_args()
    names = dict(x.split('=', 1) for x in a.name); kit.EXCLUDE.update(a.exclude)
    P = kit.load(a.data)
    items = kit.pick(P, a.cat, a.tag, 5, a.ids) if a.kind == 'rank' else kit.pick(P, ids=a.ids)
    n = len(items); assert n >= 3, '至少要 3 件商品'
    order = list(range(n - 1, -1, -1))  # countdown: last rank first
    photos = [kit.photo(p, 800) for p in items]
    base = bg()
    out = a.out or f'reel_{a.kind}.mp4'
    total = INTRO + PER * n + OUTRO; frames = int(total * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    ttl = a.title or '這週賣最多的 5 樣'
    cover = None
    for fi in range(frames):
        t = fi / FPS; im = base.copy(); d = ImageDraw.Draw(im)
        if t < INTRO:
            k = eob(t / .5)
            f = font(kit.FB, 96); lines = wrap(d, ttl, f, W - 140, 3)
            y = 640 - len(lines) * 60
            for ln in lines:
                lw = d.textlength(ln, font=f); x = (W - lw) / 2 - (1 - k) * 600
                d.text((x, y), ln, font=f, fill=INK); y += 124
            d.rectangle([W / 2 - 90, y + 20, W / 2 + 90 * eo(t / .8) - 0, y + 34], fill=Y)
            sub = a.sub or ('依實際銷量・第 ' + str(n) + ' 名到第 1 名' if a.kind == 'rank' else '價格以 ' + a.date + ' 商品頁為準')
            if t > .5: d.text((W / 2, y + 100), sub, font=font(kit.FR, 44), fill=MUTED, anchor='mm')
            if t > 1.0:
                b = eob((t - 1.0) / .4); r = 70 * b
                d.ellipse([W / 2 - r * 2.2, 1220 - r, W / 2 + r * 2.2, 1220 + r], fill=RED)
                if b > .8: d.text((W / 2, 1220), '倒數開始', font=font(kit.FB, 52), fill=INK, anchor='mm')
            if cover is None and t >= 1.6: cover = im.copy()
        elif t < INTRO + PER * n:
            s = int((t - INTRO) // PER); lt = (t - INTRO) - s * PER; idx = order[s]; p = items[idx]
            # rank number
            rk = eo(lt / .35)
            label = f'NO.{idx + 1}' if a.kind == 'rank' else (f"{p.get('d')} 折" if p.get('d') else '好價')
            col = Y if idx == 0 else INK
            d.text((80 - (1 - rk) * 500, 250), label, font=num(150) if a.kind == 'rank' else font(kit.FB, 130), fill=col if a.kind == 'rank' else RED)
            # photo
            sc = .82 + .18 * eob(lt / .45); ps = int(800 * sc); ph = photos[idx].resize((ps, ps))
            x0, y0 = (W - ps) // 2, 470 + (800 - ps) // 2
            d.rectangle([x0 - 10, y0 - 10, x0 + ps + 9, y0 + ps + 9], fill=Y if idx == 0 else (70, 70, 86)); im.paste(ph, (x0, y0))
            # text
            tk = eo((lt - .3) / .4)
            if tk > 0:
                yy = 1330 + (1 - tk) * 60
                nm = names.get(p['i']) or short(p['s'], 14)
                for ln in wrap(d, nm, font(kit.FB, 64), W - 160, 2): d.text((W / 2, yy), ln, font=font(kit.FB, 64), fill=INK, anchor='mt'); yy += 80
                d.text((W / 2, yy + 20), price(p) + '   已售 ' + sold_txt(p), font=font(kit.FB, 50), fill=Y, anchor='mt')
            # progress
            for j in range(n):
                cx = W / 2 + (j - (n - 1) / 2) * 44; on = j <= s
                d.ellipse([cx - 10, 1700 - 10, cx + 10, 1700 + 10], fill=Y if on else (60, 60, 70))
        else:
            lt = t - INTRO - PER * n; k = eob(lt / .5)
            d.text((W / 2, 700), a.ask or '你買過哪一個？', font=font(kit.FB, int(100 * k) + 1), fill=INK, anchor='mm')
            d.text((W / 2, 840), '留言告訴我 👇'.replace(' 👇', ''), font=font(kit.FB, 64), fill=Y, anchor='mm')
            if lt > .5:
                d.rectangle([140, 1010, W - 140, 1150], fill=Y)
                d.text((W / 2, 1080), '完整排行 youbi-shop.com', font=font(kit.FB, 54), fill=BG, anchor='mm')
            d.text((W / 2, 1260), '價格、銷量以商品頁為準', font=font(kit.FR, 36), fill=MUTED, anchor='mm')
        ff.stdin.write(im.tobytes())
    ff.stdin.close(); ff.wait()
    print('saved', out, f'{total:.1f}s')
    if a.cover and cover: cover.convert('RGB').save(out.rsplit('.', 1)[0] + '.jpg', quality=90); print('cover', out.rsplit('.', 1)[0] + '.jpg')


if __name__ == '__main__': main()
