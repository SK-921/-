"""ChatGPT が描いた白ネコ（見た目はそのまま）を、部品ごとに動かして LINE アニメーションスタンプ（APNG）にする。

- 各コマを parts.py で「ネコ（一番大きいかたまり）」と「文字・飾り（それ以外）」に分ける
- ネコは大きく動かす（跳ねる・おじぎ・首をかしげる など）
- 文字と飾りは、1つずつ時間をずらして波のようにぴょこぴょこ動かす
- どの部品にも白いふちを付ける（ダークモードでも見えるように）

LINE Creators Market の規格：最大 320x270（縦か横のどちらかは270以上）、5〜20コマ、1個4秒まで、
ループ1〜4回、1個1MB以下、背景透過、全コマ同じ大きさ。1コマ目は止まった絵として表示される。
ここでは 12コマ × 100ms ＝ 1.2秒 を 3回 ループ（合計3.6秒）。1コマ目は元の絵の並びのまま。

使い方: python3 outputs/line-stamp/cat/src/animate.py
"""
import math
from pathlib import Path

from PIL import Image

from parts import cells, split
from slice import white_outline

BASE = Path(__file__).resolve().parent.parent
SHEET = BASE / "src" / "chatgpt-sheet.webp"
OUT = BASE / "anim"
W, H = 320, 270
BOX_W, BOX_H = 292, 228     # 動いてもはみ出さないよう、少し小さめに置く
BOTTOM = 14                 # 下の余白
N, MS, LOOPS = 12, 100, 3
S, PI, TAU = math.sin, math.pi, 2 * math.pi


def m(dx=0.0, dy=0.0, sx=1.0, sy=1.0, rot=0.0):
    return dx, dy, sx, sy, rot


# ネコの動き：t（0〜1）→ (dx, dy, sx, sy, rot)。rot は時計回りの角度。支点はネコの足もと中央
def hop(h):
    return lambda t: m(dy=-h * S(PI * t), sx=1.05 if t < 0.09 else 1, sy=0.93 if t < 0.09 else 1)


CAT = {
    1: ("はーい", lambda t: m(rot=8 * S(TAU * t))),
    2: ("ちらっ", lambda t: m(dy=8 * S(PI * t) ** 2, sy=1 - 0.04 * S(PI * t) ** 2)),
    3: ("ありがとう", lambda t: m(sx=1 + 0.08 * S(PI * t) ** 2, sy=1 + 0.08 * S(PI * t) ** 2)),
    4: ("ごめん", lambda t: m(dy=3 * S(PI * t) ** 2, sx=1 + 0.05 * S(PI * t) ** 2, sy=1 - 0.14 * S(PI * t) ** 2)),
    5: ("つかれた", lambda t: m(sx=1 - 0.02 * S(TAU * t), sy=1 + 0.06 * S(TAU * t))),
    6: ("がんばって", hop(18)),
    7: ("よろしくです", lambda t: m(dy=6 * S(PI * t) ** 2, sy=1 - 0.08 * S(PI * t) ** 2)),
    8: ("じー", lambda t: m(dx=-10 * S(PI * t) ** 2)),
    9: ("えっ", lambda t: m(dx=5 * S(3 * TAU * t) * (1 - t), dy=-14 * S(PI * t), sx=1 + 0.04 * S(PI * t), sy=1 + 0.04 * S(PI * t))),
    10: ("おやすみ", lambda t: m(sy=1 + 0.04 * S(TAU * t))),
    11: ("いってきます", lambda t: m(dx=-6 * S(TAU * t), dy=-7 * abs(S(2 * TAU * t)), rot=-4 * S(TAU * t))),
    12: ("ただいま", lambda t: m(dy=-15 * S(PI * t), rot=4 * S(TAU * t))),
    13: ("おいしい", lambda t: m(rot=7 * S(TAU * t), dy=-4 * abs(S(2 * TAU * t)))),
    14: ("はてな", lambda t: m(rot=-8 * S(PI * t) ** 2, dy=-6 * S(PI * t) ** 2)),
    15: ("了解", lambda t: m(dy=8 * S(PI * t) ** 2, sy=1 - 0.06 * S(PI * t) ** 2)),
    16: ("のんびり", lambda t: m(dx=5 * S(TAU * t), rot=6 * S(TAU * t))),
}


def deco(t: float, cx: float):
    """文字・飾りの動き：左から順に時間をずらした、ぴょこぴょこの波。"""
    ph = TAU * t - cx / 55.0
    return m(dy=-5 * S(ph) + 5 * S(-cx / 55.0), sx=1 + 0.08 * S(ph) - 0.08 * S(-cx / 55.0),
             sy=1 + 0.08 * S(ph) - 0.08 * S(-cx / 55.0))


def transform(layer: Image.Image, pivot, dx, dy, sx, sy, rot) -> Image.Image:
    """支点を中心に、拡大縮小・回転・移動する（アフィン変換の逆行列で写す）。"""
    if abs(dx) < 1e-9 and abs(dy) < 1e-9 and abs(sx - 1) < 1e-9 and abs(sy - 1) < 1e-9 and abs(rot) < 1e-9:
        return layer
    px, py = pivot
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    a, b = c / sx, s / sx
    d, e = -s / sy, c / sy
    qx, qy = px + dx, py + dy
    coeffs = (a, b, px - a * qx - b * qy, d, e, py - d * qx - e * qy)
    return layer.convert("RGBa").transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC).convert("RGBA")


def build(cell: Image.Image):
    """コマを部品に分け、白ふちを付けて、キャンバス上の位置にそろえる。"""
    parts = split(cell)
    outlined = [white_outline(p[0], 4) for p in parts]  # 4px ずつ大きくなる（pad=6）
    pad = 6
    whole = Image.new("RGBA", outlined[0].size, (0, 0, 0, 0))
    for o in outlined:
        whole.alpha_composite(o)
    bb = whole.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
    scale = min(BOX_W / (bb[2] - bb[0]), BOX_H / (bb[3] - bb[1]), 1.0)
    ox = (W - (bb[2] - bb[0]) * scale) / 2 - bb[0] * scale
    oy = H - BOTTOM - bb[3] * scale

    def place(img):
        g = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.alpha_composite(g, (round(ox), round(oy)))
        return canvas

    layers = []
    for (img, area, (x0, y0, x1, y1)), o in zip(parts, outlined):
        cx = ((x0 + x1) / 2 + pad) * scale + ox
        cy = ((y0 + y1) / 2 + pad) * scale + oy
        foot = (cx, (y1 + pad) * scale + oy)
        layers.append((place(o), (cx, cy), foot))
    return layers


def frames_for(i: int, layers):
    cat_fn = CAT[i][1]
    frames = []
    for k in range(N):
        t = k / N
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cat, _, foot = layers[0]
        canvas.alpha_composite(transform(cat, foot, *cat_fn(t)))
        for layer, center, _ in layers[1:]:
            canvas.alpha_composite(transform(layer, center, *deco(t, center[0])))
        frames.append(canvas)
    return frames


def save_apng(frames, dst: Path) -> int:
    frames[0].save(dst, format="PNG", save_all=True, append_images=frames[1:],
                   duration=MS, loop=LOOPS, disposal=1, blend=0)
    return dst.stat().st_size


def main() -> None:
    OUT.mkdir(exist_ok=True)
    sheet = Image.open(SHEET).convert("RGBA")
    r, g, b, a = sheet.split()
    sheet = Image.merge("RGBA", (r, g, b, a.point(lambda v: 255 if v >= 250 else v)))
    all_frames = []
    for i, cell in enumerate(cells(sheet), start=1):
        frames = frames_for(i, build(cell))
        label = CAT[i][0]
        assert all(frames[k].tobytes() != frames[k + 1].tobytes() for k in range(N - 1)), f"{label}: となり合う同じコマ"
        assert len({f.tobytes() for f in frames}) >= 5, f"{label}: 動きが少ない"
        for f in frames:
            bb = f.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
            assert bb[0] > 0 and bb[1] > 0 and bb[2] < W and bb[3] < H, f"{label}: 端で切れている {bb}"
        size = save_apng(frames, OUT / f"{i:02d}.png")
        assert size <= 1024 * 1024, f"{label}: {size // 1024}KB"
        print(f"{i:02d}.png {label}: {N}コマ, {size // 1024}KB")
        all_frames.append(frames)

    mains = []
    for f in all_frames[0]:
        sq = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        g2 = f.copy()
        g2.thumbnail((240, 240), Image.LANCZOS)
        sq.alpha_composite(g2, ((240 - g2.width) // 2, (240 - g2.height) // 2))
        mains.append(sq)
    print("main.png:", save_apng(mains, OUT / "main.png") // 1024, "KB")
    Image.open(BASE / "stamp" / "tab.png").save(OUT / "tab.png")

    tw, th = 200, 170
    sheets = []
    for k in range(N):
        sh = Image.new("RGBA", (4 * tw, 4 * th), (255, 255, 255, 255))
        for i, frames in enumerate(all_frames):
            f = frames[k].copy()
            f.thumbnail((tw - 8, th - 8))
            sh.alpha_composite(f, ((i % 4) * tw + (tw - f.width) // 2, (i // 4) * th + (th - f.height) // 2))
        sheets.append(sh.convert("RGB"))
    sheets[0].save(BASE / "anim-preview.gif", save_all=True, append_images=sheets[1:], duration=MS, loop=0)
    print("anim-preview.gif")


if __name__ == "__main__":
    main()
