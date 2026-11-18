"""OpenAI の画像生成 API（ChatGPT の画像生成と同じ仕組み）に、LINE スタンプ16個ぶんのシートを描いてもらう。

使い方:
  python3 scripts/stamps/gen_sheet.py <セットのフォルダ> "<キャラクターの説明>" --prompt-only   ← 課金なし（おすすめ）
  python3 scripts/stamps/gen_sheet.py <セットのフォルダ> "<キャラクターの説明>" [--model gpt-image-1]   ← API（従量課金）

--prompt-only：API を呼ばず、ChatGPT に貼る頼み方を <セット>/src/prompt.txt に書くだけ。
  ChatGPT で描いてもらった絵（背景透明の PNG）を <セット>/src/chatgpt-sheet.png に置いてから build_set.py を動かす。

例:
  python3 scripts/stamps/gen_sheet.py outputs/line-stamp/shiba "まるい柴犬。茶色と白、太い輪郭線"

- API キーはこのスクリプトには書かない。環境のネットワーク設定（秘密情報）として登録したものが、
  api.openai.com への通信に自動で付く。手元のPCで動かすときは、環境変数 OPENAI_API_KEY に入れる。
- 画像1枚ごとに料金がかかる（料金は OpenAI の公式ページで確認）。
- できたシートは <セット>/src/chatgpt-sheet.png に保存し、使ったお題を <セット>/src/prompt.txt に残す。
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from phrases import PHRASES

API = "https://api.openai.com/v1/images/generations"

PROMPT = """LINEのアニメーションスタンプ用に、オリジナルのマスコットキャラクターのスタンプ16個を1枚の画像に描いてください。

キャラクター：{character}

条件
- 4列×4行のグリッドに16個を並べる。各スタンプの間には、何も描かない透明なすき間をはっきり空ける
- 背景は透明（PNG で、背景を透過にして出力）。各スタンプの外枠や区切り線は描かない
- 16個とも同じキャラクター（形・色・線の太さを完全にそろえる）
- 既存のキャラクター、企業のマスコット、有名な作品に似せない。ロゴやサービス名は描かない
- やわらかい色、こげ茶色の太めの輪郭線、かわいいゆるいタッチ
- 各スタンプの上に、手書き風の日本語の文字を入れる。文字は下の言葉そのまま（誤字なし）
- ハートや汗などの小さな飾りは、キャラクターから少し離して描く

左上から右へ、行ごとに次の順番で：
{order}
"""


def build_prompt(character: str) -> str:
    order = "\n".join(f"{i:2d}. {p['text']}（{p['pose']}）" for i, p in enumerate(PHRASES, start=1))
    return PROMPT.format(character=character, order=order)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    ap.add_argument("character")
    ap.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1"))
    ap.add_argument("--prompt-only", action="store_true", help="API を呼ばず、頼み方だけ書く（課金なし）")
    args = ap.parse_args()

    src = Path(args.set_dir) / "src"
    src.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(args.character)
    (src / "prompt.txt").write_text(prompt, encoding="utf-8")
    if args.prompt_only:
        print(f"wrote {src / 'prompt.txt'}（ChatGPT に貼って、できた絵を {src / 'chatgpt-sheet.png'} に置く）")
        return

    body = json.dumps({
        "model": args.model,
        "prompt": prompt,
        "size": "1536x1024",
        "background": "transparent",
        "output_format": "png",
        "quality": "high",
        "n": 1,
    }).encode("utf-8")
    # キーは環境が自動で付ける。手元で動かすときは OPENAI_API_KEY を使う（なければダミーのまま送る）
    key = os.environ.get("OPENAI_API_KEY", "sk-placeholder-injected-by-proxy")
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=300) as res:
            data = json.load(res)
    except urllib.error.HTTPError as e:
        print(f"API エラー {e.code}: {e.read().decode('utf-8', 'replace')[:800]}", file=sys.stderr)
        sys.exit(1)

    png = base64.b64decode(data["data"][0]["b64_json"])
    out = src / "chatgpt-sheet.png"
    out.write_bytes(png)
    print(f"saved {out} ({len(png) // 1024}KB), model={args.model}")


if __name__ == "__main__":
    main()
