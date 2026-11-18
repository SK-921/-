"""ChatGPT が描いた 4x4 のスタンプシートから、LINE アニメーションスタンプ16個と申請キットを作る。

使い方:
  python3 scripts/stamps/build_set.py <セットのフォルダ> "<スタンプのタイトル>"

入力 : <セット>/src/chatgpt-sheet.png（または .webp）… gen_sheet.py が作る。手で描いてもらったものを置いてもよい
出力 : <セット>/anim/01〜16.png・main.png・tab.png、<セット>/anim-preview.gif
       outputs/release/line-<セット名>/ に ZIP・info.txt・MUSE.md

やっていること
1. シートの透明なすき間から、4x4 の区切り位置を自動で見つける
2. 各コマを「キャラクター（一番大きいかたまり）」と「文字・飾り（それ以外）」に分け、白いふちを付ける
3. キャラクターは phrases.py の motion で大きく動かし、文字・飾りは波のようにぴょこぴょこ動かす
4. LINE の規格（320x270、12コマ×3回＝3.6秒、1MB以下、透過、端で切れない、となり合うコマが違う）を確かめる
"""
import math
import sys
import zipfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from phrases import PHRASES

W, H = 320, 270
BOX_W, BOX_H, BOTTOM = 292, 228, 14
N, MS, LOOPS = 12, 100, 3
S, PI, TAU = math.sin, math.pi, 2 * math.pi
ROOT = Path(__file__).resolve().parents[2]


def m(dx=0.0, dy=0.0, sx=1.0, sy=1.0, rot=0.0):
    return dx, dy, sx, sy, rot


def _hop(h):
    return lambda t: m(dy=-h * S(PI * t), sx=1.05 if t < 0.09 else 1, sy=0.93 if t < 0.09 else 1)


MOTIONS = {
    "rock": lambda t: m(rot=8 * S(TAU * t)),
    "peek": lambda t: m(dy=8 * S(PI * t) ** 2, sy=1 - 0.04 * S(PI * t) ** 2),
    "pulse": lambda t: m(sx=1 + 0.08 * S(PI * t) ** 2, sy=1 + 0.08 * S(PI * t) ** 2),
    "bow": lambda t: m(dy=3 * S(PI * t) ** 2, sx=1 + 0.05 * S(PI * t) ** 2, sy=1 - 0.14 * S(PI * t) ** 2),
    "breathe": lambda t: m(sx=1 - 0.02 * S(TAU * t), sy=1 + 0.06 * S(TAU * t)),
    "hop": _hop(18),
    "nod": lambda t: m(dy=7 * S(PI * t) ** 2, sy=1 - 0.07 * S(PI * t) ** 2),
    "lean": lambda t: m(dx=-10 * S(PI * t) ** 2),
    "shock": lambda t: m(dx=5 * S(3 * TAU * t) * (1 - t), dy=-14 * S(PI * t), sx=1 + 0.04 * S(PI * t), sy=1 + 0.04 * S(PI * t)),
    "sleep": lambda t: m(sy=1 + 0.04 * S(TAU * t)),
    "dash": lambda t: m(dx=-6 * S(TAU * t), dy=-7 * abs(S(2 * TAU * t)), rot=-4 * S(TAU * t)),
    "jump": lambda t: m(dy=-15 * S(PI * t), rot=4 * S(TAU * t)),
    "wiggle": lambda t: m(rot=7 * S(TAU * t), dy=-4 * abs(S(2 * TAU * t))),
    "tilt": lambda t: m(rot=-8 * S(PI * t) ** 2, dy=-6 * S(PI * t) ** 2),
    "sway": lambda t: m(dx=5 * S(TAU * t), rot=6 * S(TAU * t)),
}
# はみ出したときに少しずつ弱めるための倍率
SOFTEN = [1.0, 0.8, 0.6, 0.45]


# ---------------- シートの区切り ----------------
def _splits(empty: np.ndarray, n: int) -> list[int]:
    """空き列（または行）の並びから、n 等分に近い位置にあるすき間の真ん中を区切りにする。"""
    size = len(empty)
    runs, start = [], None
    for i, e in enumerate(empty):
        if e and start is None:
            start = i
        if not e and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, size - 1))
    cuts = [0]
    for k in range(1, n):
        want = size * k / n
        near = [r for r in runs if r[0] > 0 and r[1] < size - 1 and abs((r[0] + r[1]) / 2 - want) < size / (2 * n)]
        if near:
            best = min(near, key=lambda r: abs((r[0] + r[1]) / 2 - want))
            cuts.append((best[0] + best[1]) // 2)
        else:
            cuts.append(int(want))  # すき間が見つからないときは等分の位置で切る
    cuts.append(size)
    return cuts


def grid(sheet: Image.Image, cols=4, rows=4):
    a = np.array(sheet.getchannel("A")) > 16
    xs = _splits(~a.any(axis=0), cols)
    ys = _splits(~a.any(axis=1), rows)
    return [sheet.crop((xs[c], ys[r], xs[c + 1], ys[r + 1])) for r in range(rows) for c in range(cols)]


# ---------------- 部品に分ける ----------------
def _dilate(mask, r):
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
    return out


def _label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    n = 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0]:
            continue
        n += 1
        q = deque([(y0, x0)])
        lab[y0, x0] = n
        while q:
            y, x = q.popleft()
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = n
                    q.append((ny, nx))
    return lab, n


def split(cell):
    a = np.array(cell.getchannel("A"))
    lab, n = _label(_dilate(a > 24, 4))
    rgba = np.array(cell)
    parts = []
    for k in range(1, n + 1):
        sel = (lab == k) & (a > 0)
        area = int(sel.sum())
        if area < 30:
            continue
        layer = np.zeros_like(rgba)
        layer[sel] = rgba[sel]
        ys, xs = np.nonzero(sel)
        parts.append((Image.fromarray(layer, "RGBA"), area, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)))
    parts.sort(key=lambda p: -p[1])
    return parts


def white_outline(img, width=4):
    pad = width + 2
    big = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(img, (pad, pad))
    grown = big.getchannel("A").point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.MaxFilter(2 * width + 1)).filter(ImageFilter.GaussianBlur(0.8))
    out = Image.new("RGBA", big.size, (255, 255, 255, 0))
    out.putalpha(grown)
    out.alpha_composite(big)
    return out, pad


# ---------------- 動かす ----------------
def transform(layer, pivot, dx, dy, sx, sy, rot):
    if abs(dx) + abs(dy) + abs(sx - 1) + abs(sy - 1) + abs(rot) < 1e-9:
        return layer
    px, py = pivot
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    a, b, d, e = c / sx, s / sx, -s / sy, c / sy
    qx, qy = px + dx, py + dy
    coeffs = (a, b, px - a * qx - b * qy, d, e, py - d * qx - e * qy)
    return layer.convert("RGBa").transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC).convert("RGBA")


def deco(t, cx):
    ph, p0 = TAU * t - cx / 55.0, -cx / 55.0
    return m(dy=-5 * S(ph) + 5 * S(p0), sx=1 + 0.08 * (S(ph) - S(p0)), sy=1 + 0.08 * (S(ph) - S(p0)))


def layers_for(cell):
    parts = split(cell)
    outlined = [white_outline(p[0]) for p in parts]
    pad = outlined[0][1]
    whole = Image.new("RGBA", outlined[0][0].size, (0, 0, 0, 0))
    for o, _ in outlined:
        whole.alpha_composite(o)
    bb = whole.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
    scale = min(BOX_W / (bb[2] - bb[0]), BOX_H / (bb[3] - bb[1]), 1.0)
    ox = (W - (bb[2] - bb[0]) * scale) / 2 - bb[0] * scale
    oy = H - BOTTOM - bb[3] * scale
    out = []
    for (img, area, (x0, y0, x1, y1)), (o, _) in zip(parts, outlined):
        g = o.resize((round(o.width * scale), round(o.height * scale)), Image.LANCZOS)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.alpha_composite(g, (round(ox), round(oy)))
        cx = ((x0 + x1) / 2 + pad) * scale + ox
        cy = ((y0 + y1) / 2 + pad) * scale + oy
        out.append((canvas, (cx, cy), (cx, (y1 + pad) * scale + oy)))
    return out


def frames_for(layers, motion, k_soft=1.0):
    frames = []
    for k in range(N):
        t = k / N
        dx, dy, sx, sy, rot = motion(t)
        cat = (dx * k_soft, dy * k_soft, 1 + (sx - 1) * k_soft, 1 + (sy - 1) * k_soft, rot * k_soft)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.alpha_composite(transform(layers[0][0], layers[0][2], *cat))
        for layer, center, _ in layers[1:]:
            canvas.alpha_composite(transform(layer, center, *deco(t, center[0])))
        frames.append(canvas)
    return frames


def ok(frames):
    if any(frames[k].tobytes() == frames[k + 1].tobytes() for k in range(N - 1)):
        return "となり合う同じコマ"
    if len({f.tobytes() for f in frames}) < 5:
        return "動きが少ない"
    for f in frames:
        bb = f.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if not (bb[0] > 0 and bb[1] > 0 and bb[2] < W and bb[3] < H):
            return "端で切れている"
    return ""


def save_apng(frames, dst):
    frames[0].save(dst, format="PNG", save_all=True, append_images=frames[1:], duration=MS, loop=LOOPS, disposal=1, blend=0)
    return dst.stat().st_size


# ---------------- まとめ ----------------
def main(set_dir: str, title: str) -> None:
    base = Path(set_dir)
    src = next(p for p in [base / "src" / "chatgpt-sheet.png", base / "src" / "chatgpt-sheet.webp"] if p.exists())
    sheet = Image.open(src).convert("RGBA")
    r, g, b, a = sheet.split()
    sheet = Image.merge("RGBA", (r, g, b, a.point(lambda v: 255 if v >= 250 else v)))
    assert a.getextrema()[0] == 0, "背景が透明になっていない（透明な背景で描き直してもらう）"

    out = base / "anim"
    out.mkdir(parents=True, exist_ok=True)
    all_frames = []
    for i, (cell, ph) in enumerate(zip(grid(sheet), PHRASES), start=1):
        layers = layers_for(cell)
        for k_soft in SOFTEN:
            frames = frames_for(layers, MOTIONS[ph["motion"]], k_soft)
            err = ok(frames)
            if not err:
                break
        assert not err, f"{i:02d} {ph['text']}: {err}"
        size = save_apng(frames, out / f"{i:02d}.png")
        assert size <= 1024 * 1024, f"{i:02d}: {size // 1024}KB"
        print(f"{i:02d}.png {ph['text']}: {ph['motion']} x{k_soft}, {size // 1024}KB")
        all_frames.append(frames)

    mains = []
    for f in all_frames[0]:
        sq = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        g2 = f.copy()
        g2.thumbnail((240, 240), Image.LANCZOS)
        sq.alpha_composite(g2, ((240 - g2.width) // 2, (240 - g2.height) // 2))
        mains.append(sq)
    save_apng(mains, out / "main.png")
    tab = Image.new("RGBA", (96, 74), (0, 0, 0, 0))
    t0 = all_frames[0][0].copy()
    t0 = t0.crop(t0.getchannel("A").getbbox())
    t0.thumbnail((92, 70), Image.LANCZOS)
    tab.alpha_composite(t0, ((96 - t0.width) // 2, (74 - t0.height) // 2))
    tab.save(out / "tab.png")

    tw, th = 200, 170
    sheets = []
    for k in range(N):
        sh = Image.new("RGBA", (4 * tw, 4 * th), (255, 255, 255, 255))
        for i, frames in enumerate(all_frames):
            f = frames[k].copy()
            f.thumbnail((tw - 8, th - 8))
            sh.alpha_composite(f, ((i % 4) * tw + (tw - f.width) // 2, (i // 4) * th + (th - f.height) // 2))
        sheets.append(sh.convert("RGB"))
    sheets[0].save(base / "anim-preview.gif", save_all=True, append_images=sheets[1:], duration=MS, loop=0)

    # 申請キット
    name = base.name
    inside = str(base.resolve()).startswith(str(ROOT))
    rel = ROOT / "outputs" / "release" / f"line-{name}" if inside else base / "release"  # リポジトリの外で試すときは、そのフォルダの中に出す
    rel.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(rel / f"line-{name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for n in ["main.png", "tab.png"] + [f"{i:02d}.png" for i in range(1, 17)]:
            z.write(out / n, n)
    words = "\n".join(f"{i:02d} {p['text']}" for i, p in enumerate(PHRASES, start=1))
    (rel / "info.txt").write_text(
        f"LINE Creators Market に入力する内容（アニメーションスタンプ・16個）\n\n"
        f"■ スタンプのタイトル（全角20文字以内）\n{title}\n\n"
        f"■ スタンプの説明文（全角80文字以内）\nあいさつ・お礼・おやすみなど、毎日のやりとりで使えるアニメーションスタンプです。キャラクターと文字がぴょこぴょこ動いて、気持ちを伝えます。\n\n"
        f"■ クリエイター名・コピーライト（英数字）・販売価格：【本人が決める】\n\n"
        f"■ ZIP：line-{name}.zip（main.png・tab.png・01〜16.png）\n\n■ 並び順と言葉\n{words}\n\n"
        f"■ 申請の前に本人が確かめること\n"
        f"1. LINE ストアで似たキャラクター・同じ名前のスタンプがないか\n"
        f"2. OpenAI の画像生成で作った絵を商用で売ってよいか（今の利用規約）\n"
        f"3. 文字に誤字がないか（ChatGPT は文字をまちがえることがある）\n",
        encoding="utf-8")
    muse = (ROOT / "outputs" / "release" / "line-cat-anim" / "MUSE.md").read_text(encoding="utf-8")
    (rel / "MUSE.md").write_text(muse.replace("line-cat-anim.zip", f"line-{name}.zip").replace("白ねこのアニメーションスタンプ", f"「{title}」"), encoding="utf-8")
    print(f"kit: {rel}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
