"""frames.js が書き出したコマを、LINE のアニメーションスタンプ（APNG）にまとめる。

規格（LINE Creators Market）：最大320x270、5〜20コマ、1個4秒まで、ループ1〜4回、1MB以下、背景透過。
ここでは 12コマ × 100ms ＝ 1.2秒 を 3回 ループ（合計3.6秒）にする。
確認用に、全部を並べた GIF（白背景）も作る。

使い方: python3 outputs/line-stamp/cat-v2/src/make_apng.py
"""
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent.parent
FRAMES = BASE / "frames"
OUT = BASE / "anim"
DURATION_MS = 100
LOOPS = 3
LIMIT_KB = 1024


def main() -> None:
    OUT.mkdir(exist_ok=True)
    sets = sorted(p for p in FRAMES.iterdir() if p.is_dir())
    all_frames = []
    for i, d in enumerate(sets, start=1):
        frames = [Image.open(f).convert("RGBA") for f in sorted(d.glob("*.png"))]
        assert 5 <= len(frames) <= 20, f"{d.name}: コマ数 {len(frames)}"
        assert len(frames) * DURATION_MS * LOOPS <= 4000, f"{d.name}: 4秒を超える"
        assert all(frames[k].tobytes() != frames[k + 1].tobytes() for k in range(len(frames) - 1)), f"{d.name}: となり合う同じコマ"
        assert len({f.tobytes() for f in frames}) >= 5, f"{d.name}: 動きが少ない"
        assert frames[0].size == (320, 270)
        dst = OUT / f"{i:02d}.png"
        frames[0].save(
            dst, format="PNG", save_all=True, append_images=frames[1:],
            duration=DURATION_MS, loop=LOOPS, disposal=1, blend=0,
        )
        kb = dst.stat().st_size / 1024
        assert kb <= LIMIT_KB, f"{dst.name}: {kb:.0f}KB"
        print(f"{dst.name} ({d.name}): {len(frames)}コマ, {kb:.0f}KB")
        all_frames.append(frames)

    tab = Image.open(FRAMES / "tab.png")
    tab.save(OUT / "tab.png")
    print("tab.png:", tab.size)

    # メイン画像（240x240、APNG）：01 を縮小
    mains = []
    for f in all_frames[0]:
        sq = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        g = f.copy(); g.thumbnail((240, 240), Image.LANCZOS)
        sq.alpha_composite(g, ((240 - g.width) // 2, (240 - g.height) // 2))
        mains.append(sq)
    mains[0].save(OUT / "main.png", format="PNG", save_all=True, append_images=mains[1:], duration=DURATION_MS, loop=LOOPS, disposal=1, blend=0)
    print("main.png 240x240")

    # 確認用 GIF：4列×4行、白背景
    n = len(all_frames[0])
    sheet_frames = []
    for k in range(n):
        sheet = Image.new("RGBA", (4 * 330 + 10, 4 * 280 + 10), (255, 255, 255, 255))
        for i, frames in enumerate(all_frames):
            x, y = 10 + (i % 4) * 330, 10 + (i // 4) * 280
            sheet.alpha_composite(frames[k], (x, y))
        sheet_frames.append(sheet.convert("RGB"))
    sheet_frames[0].save(BASE / "preview.gif", save_all=True, append_images=sheet_frames[1:],
                         duration=DURATION_MS, loop=0)
    print("preview.gif done")


if __name__ == "__main__":
    main()
