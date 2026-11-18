"""白ネコの静止画スタンプ（stamp/01〜16.png）に動きを付けて、LINE アニメーションスタンプ（APNG）にする。

LINE Creators Market の規格：最大 320x270（縦か横のどちらかは270以上）、5〜20コマ、1個4秒まで、
ループ1〜4回、1個1MB以下、背景透過、全コマ同じ大きさ。1コマ目は止まった絵として表示される。
ここでは 12コマ × 100ms ＝ 1.2秒 を 3回 ループ（合計3.6秒）。1コマ目はかならず元の絵のまま。

使い方: python3 outputs/line-stamp/cat/src/animate.py
"""
import math
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "stamp"
OUT = BASE / "anim"
W, H = 320, 270
BOX_W, BOX_H = 292, 236  # 動いてもはみ出さないよう、少し小さめに置く
N, MS, LOOPS = 12, 100, 3
S = math.sin
TAU = 2 * math.pi


# 各スタンプの動き：t（0〜1）→ (dx, dy, sx, sy, rot)。rot は時計回りの角度
def m(dx=0.0, dy=0.0, sx=1.0, sy=1.0, rot=0.0):
    return dx, dy, sx, sy, rot


MOTIONS = {
    1: ("はーい", lambda t: m(rot=6 * S(TAU * t))),                                    # 手をふるように揺れる
    2: ("ちらっ", lambda t: m(dy=12 * S(math.pi * t) ** 2)),                                # 下がってから、ちらっと戻る
    3: ("ありがとう", lambda t: m(sx=1 + 0.06 * S(math.pi * t) ** 2, sy=1 + 0.06 * S(math.pi * t) ** 2)),  # どきどき
    4: ("ごめん", lambda t: m(dy=4 * S(math.pi * t) ** 2, sx=1 + 0.03 * S(math.pi * t) ** 2, sy=1 - 0.09 * S(math.pi * t) ** 2)),  # ぺこり
    5: ("つかれた", lambda t: m(sx=1 - 0.015 * S(TAU * t), sy=1 + 0.035 * S(TAU * t))),      # ぐったり呼吸
    6: ("がんばって", lambda t: m(dy=-14 * S(math.pi * t))),                           # ぴょんぴょん
    7: ("よろしくです", lambda t: m(dy=5 * S(math.pi * t) ** 2, sy=1 - 0.05 * S(math.pi * t) ** 2)),  # ゆっくりおじぎ
    8: ("じー", lambda t: m(dx=-6 * S(math.pi * t) ** 2)),                                  # そっとのぞき込む
    9: ("えっ", lambda t: m(dx=5 * S(3 * TAU * t) * (1 - t), sx=1 + 0.05 * S(math.pi * t), sy=1 + 0.05 * S(math.pi * t))),  # びくっ
    10: ("おやすみ", lambda t: m(sy=1 + 0.03 * S(TAU * t))),                                # すやすや
    11: ("いってきます", lambda t: m(dx=-7 * S(TAU * t), dy=-5 * abs(S(2 * TAU * t)), rot=-3 * S(TAU * t))),  # とことこ
    12: ("ただいま", lambda t: m(dy=-12 * S(math.pi * t))),                            # ぴょんと跳ねる
    13: ("おいしい", lambda t: m(rot=5 * S(TAU * t), dy=-3 * abs(S(2 * TAU * t)))),                                  # もぐもぐ揺れる
    14: ("はてな", lambda t: m(rot=-8 * S(TAU * t / 2) ** 2)),                              # くびをかしげる
    15: ("了解", lambda t: m(dy=7 * S(math.pi * t) ** 2, sy=1 - 0.05 * S(math.pi * t) ** 2)),  # こくこく
    16: ("のんびり", lambda t: m(dx=3 * S(TAU * t), rot=4 * S(TAU * t))),                   # ゆらゆら
}


def place(img: Image.Image) -> tuple[Image.Image, tuple[float, float]]:
    """絵を枠に収まるよう縮小して、キャンバスの下寄り中央に置く。動きの支点（足もと中央）も返す。"""
    scale = min(BOX_W / img.width, BOX_H / img.height, 1.0)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - img.width) // 2
    y = H - 16 - img.height  # 下に16pxあける（ぺこりで沈む分）
    canvas.alpha_composite(img, (x, y))
    return canvas, (W / 2, H - 16)


def move(base: Image.Image, pivot, dx, dy, sx, sy, rot) -> Image.Image:
    """支点を中心に、拡大縮小・回転・移動した1コマを作る（アフィン変換の逆行列で写す）。"""
    if (dx, dy, sx, sy, rot) == (0, 0, 1, 1, 0):
        return base.copy()
    px, py = pivot
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    a, b = c / sx, s / sx
    d, e = -s / sy, c / sy
    qx, qy = px + dx, py + dy
    coeffs = (a, b, px - a * qx - b * qy, d, e, py - d * qx - e * qy)
    pre = base.convert("RGBa")  # 縁が黒ずまないよう、透明度をかけた状態で変形する
    return pre.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC).convert("RGBA")


def save_apng(frames, dst: Path) -> int:
    frames[0].save(dst, format="PNG", save_all=True, append_images=frames[1:],
                   duration=MS, loop=LOOPS, disposal=1, blend=0)
    return dst.stat().st_size


def main() -> None:
    OUT.mkdir(exist_ok=True)
    all_frames = []
    for i, (label, fn) in MOTIONS.items():
        base, pivot = place(Image.open(SRC / f"{i:02d}.png").convert("RGBA"))
        frames = [move(base, pivot, *fn(k / N)) for k in range(N)]
        assert frames[0].tobytes() == base.tobytes(), "1コマ目は元の絵"
        assert all(frames[k].tobytes() != frames[k + 1].tobytes() for k in range(N - 1)), f"{label}: となり合う同じコマがある"
        assert len({f.tobytes() for f in frames}) >= 5, f"{label}: 動きが少なすぎる"
        assert N * MS * LOOPS <= 4000
        size = save_apng(frames, OUT / f"{i:02d}.png")
        assert size <= 1024 * 1024, f"{label}: {size // 1024}KB"
        print(f"{i:02d}.png {label}: {N}コマ, {size // 1024}KB")
        all_frames.append(frames)

    # メイン画像（240x240、APNG）：01 を縮小
    main_frames = []
    for f in all_frames[0]:
        sq = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        g = f.copy()
        g.thumbnail((240, 240), Image.LANCZOS)
        sq.alpha_composite(g, ((240 - g.width) // 2, (240 - g.height) // 2))
        main_frames.append(sq)
    print("main.png:", save_apng(main_frames, OUT / "main.png") // 1024, "KB")
    Image.open(SRC / "tab.png").save(OUT / "tab.png")

    # 確認用 GIF（4列×4行、白背景）
    tw, th = 200, 170
    sheets = []
    for k in range(N):
        sheet = Image.new("RGBA", (4 * tw, 4 * th), (255, 255, 255, 255))
        for i, frames in enumerate(all_frames):
            f = frames[k].copy()
            f.thumbnail((tw - 8, th - 8))
            sheet.alpha_composite(f, ((i % 4) * tw + (tw - f.width) // 2, (i // 4) * th + (th - f.height) // 2))
        sheets.append(sheet.convert("RGB"))
    sheets[0].save(BASE / "anim-preview.gif", save_all=True, append_images=sheets[1:], duration=MS, loop=0)
    print("anim-preview.gif")


if __name__ == "__main__":
    main()
