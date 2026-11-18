"""ChatGPT のシートの各コマを、つながった部品（キャラクター・文字・飾り）に切り分ける。

透明でない画素を少しふくらませてから、つながっているかたまりごとに番号をつける。
一番大きいかたまりがキャラクター、それ以外が文字や飾り（ハート・線など）。
"""
from collections import deque

import numpy as np
from PIL import Image

XS = [0, 392, 774, 1162, 1536]
YS = [0, 280, 518, 776, 1024]


def cells(sheet: Image.Image):
    out = []
    for row in range(4):
        for col in range(4):
            out.append(sheet.crop((XS[col], YS[row], XS[col + 1], YS[row + 1])))
    return out


def dilate(mask: np.ndarray, r: int) -> np.ndarray:
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r:
                continue
            out |= np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
    return out


def label(mask: np.ndarray):
    """4近傍でつながったかたまりに番号をつける（0は背景）。"""
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    n = 0
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
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


def split(cell: Image.Image, grow: int = 4):
    """コマを部品に分ける。戻り値：[(部品の画像, 面積, bbox)]、面積の大きい順。"""
    a = np.array(cell.getchannel("A"))
    mask = a > 24
    lab, n = label(dilate(mask, grow))
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


if __name__ == "__main__":
    from pathlib import Path
    sheet = Image.open(Path(__file__).resolve().parent / "chatgpt-sheet.webp").convert("RGBA")
    for i, c in enumerate(cells(sheet), start=1):
        ps = split(c)
        print(f"{i:02d}: {len(ps)} parts ->", [(p[1], p[2]) for p in ps[:8]])
