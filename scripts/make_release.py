"""note 用の完成原稿（note-post.txt）を、Muse がそのまま使える「公開キット」に分ける。

使い方: python3 scripts/make_release.py outputs/fe/note-post.txt outputs/fe/images outputs/release/fe-vol1
"""
import shutil
import sys
from pathlib import Path

PAID_MARK = "▼▼▼ ここに有料ライン"
BODY_START = "本文ここから"
BODY_END = "本文ここまで"


def main(src: str, img_dir: str, out: str) -> None:
    text = Path(src).read_text(encoding="utf-8")
    lines = text.splitlines()

    title = next(l.split("：", 1)[1] for l in lines if l.startswith("タイトル："))
    tags = next(l.split("：", 1)[1] for l in lines if l.startswith("ハッシュタグ："))

    start = next(i for i, l in enumerate(lines) if l.strip() == BODY_START) + 2  # 区切り線の次
    end = next(i for i, l in enumerate(lines) if l.strip() == BODY_END) - 1      # 区切り線の手前
    paid = next(i for i, l in enumerate(lines) if l.startswith(PAID_MARK))

    free_body = "\n".join(lines[start:paid]).strip() + "\n"
    paid_body = "\n".join(lines[paid + 1:end]).strip() + "\n"
    first_paid_heading = next(l for l in lines[paid + 1:end] if l.strip())

    out_dir = Path(out)
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    (out_dir / "01-title.txt").write_text(title + "\n", encoding="utf-8")
    (out_dir / "02-settings.txt").write_text(
        "価格：500円（販売設定で「有料」）\n"
        f"有料エリアの開始位置：「{first_paid_heading}」の直前\n"
        f"ハッシュタグ：{tags}\n"
        "見出し画像：images/00-cover.png\n",
        encoding="utf-8",
    )
    (out_dir / "03-free.txt").write_text(free_body, encoding="utf-8")
    (out_dir / "04-paid.txt").write_text(paid_body, encoding="utf-8")

    for png in sorted(Path(img_dir).glob("0[0-7]-*.png")):
        shutil.copy2(png, out_dir / "images" / png.name)

    n_markers = paid_body.count("【画像】")
    print(f"title: {title}")
    print(f"free: {len(free_body)} chars, paid: {len(paid_body)} chars, image markers: {n_markers}")
    print(f"paid starts at: {first_paid_heading}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
