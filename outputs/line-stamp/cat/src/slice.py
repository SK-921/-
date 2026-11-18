"""ChatGPT が描いた 4x4 のシート（背景透過）を、LINE スタンプ（静止画）16個に切り分ける。

LINE Creators Market の規格：最大 370x320、縦横は偶数、まわりに10px程度の余白、PNG、背景透過、1MB以下。
メイン画像 240x240、トークルームタブ画像 96x74 も作る。

使い方: python3 outputs/line-stamp/cat/src/slice.py
"""
from pathlib import Path

from PIL import Image, ImageFilter

BASE = Path(__file__).resolve().parent.parent
SHEET = BASE / "src" / "chatgpt-sheet.webp"
OUT = BASE / "stamp"

# シートの空き列・空き行から求めた区切り位置
XS = [0, 392, 774, 1162, 1536]
YS = [0, 280, 518, 776, 1024]
LABELS = [
    "はーい", "ちらっ", "ありがとう", "ごめん",
    "つかれた", "がんばって", "よろしくです", "じー",
    "えっ", "おやすみ", "いってきます", "ただいま",
    "おいしい", "はてな", "了解", "のんびり",
]
MAX_W, MAX_H, MARGIN = 370, 320, 10
OUTLINE = 4  # 白ふちの太さ（px）


def even(n: int) -> int:
    return n + (n % 2)


def fit(img: Image.Image, box_w: int, box_h: int, margin: int, fixed: bool) -> Image.Image:
    """透明な余白を除いて、枠に収まるよう縮小し、余白をつけて置く。"""
    img = img.crop(img.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox())
    scale = min((box_w - 2 * margin) / img.width, (box_h - 2 * margin) / img.height, 1.0)
    img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    w, h = (box_w, box_h) if fixed else (even(img.width + 2 * margin), even(img.height + 2 * margin))
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((w - img.width) // 2, (h - img.height) // 2))
    return canvas


def white_outline(img: Image.Image, width: int) -> Image.Image:
    """絵と文字のまわりに白いふちを付ける（ダークモードでも読めるように）。"""
    pad = width + 2
    big = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(img, (pad, pad))
    mask = big.getchannel("A").point(lambda a: 255 if a > 40 else 0)
    grown = mask.filter(ImageFilter.MaxFilter(2 * width + 1)).filter(ImageFilter.GaussianBlur(0.8))
    out = Image.new("RGBA", big.size, (255, 255, 255, 0))
    out.putalpha(grown)
    out.alpha_composite(big)
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    sheet = Image.open(SHEET).convert("RGBA")
    # ほぼ不透明（250以上）の画素は完全な不透明にそろえる
    r, g, b, a = sheet.split()
    sheet = Image.merge("RGBA", (r, g, b, a.point(lambda v: 255 if v >= 250 else v)))

    cells = []
    for row in range(4):
        for col in range(4):
            cells.append(white_outline(sheet.crop((XS[col], YS[row], XS[col + 1], YS[row + 1])), OUTLINE))

    for i, (cell, label) in enumerate(zip(cells, LABELS), start=1):
        stamp = fit(cell, MAX_W, MAX_H, MARGIN, fixed=False)
        assert stamp.width <= MAX_W and stamp.height <= MAX_H and stamp.width % 2 == 0 and stamp.height % 2 == 0
        dst = OUT / f"{i:02d}.png"
        stamp.save(dst, optimize=True)
        assert dst.stat().st_size <= 1024 * 1024
        print(f"{dst.name} {label}: {stamp.width}x{stamp.height}, {dst.stat().st_size // 1024}KB")

    fit(cells[0], 240, 240, 8, fixed=True).save(OUT / "main.png", optimize=True)
    fit(cells[0], 96, 74, 3, fixed=True).save(OUT / "tab.png", optimize=True)
    print("main.png 240x240 / tab.png 96x74")

    # 確認用：白とダークの背景に並べる
    thumbs = [Image.open(OUT / f"{i:02d}.png") for i in range(1, 17)]
    cw, ch = 190, 165
    prev = Image.new("RGBA", (8 * cw, 4 * ch), (255, 255, 255, 255))
    for half, bg in enumerate([(255, 255, 255, 255), (31, 41, 55, 255)]):
        panel = Image.new("RGBA", (4 * cw, 4 * ch), bg)
        for i, t in enumerate(thumbs):
            t2 = t.copy()
            t2.thumbnail((cw - 10, ch - 10))
            panel.alpha_composite(t2, ((i % 4) * cw + (cw - t2.width) // 2, (i // 4) * ch + (ch - t2.height) // 2))
        prev.alpha_composite(panel, (half * 4 * cw, 0))
    prev.convert("RGB").save(BASE / "preview.png")
    print("preview.png")


if __name__ == "__main__":
    main()
