#!/usr/bin/env bash
# 定期実行用ラッパー。cron / タスクスケジューラから呼ぶ。
# 使い方: scripts/run.sh morning | hourly | daily | weekly
#   daily  : 毎日の無料記事を作り、公開キットを GitHub に送る（Muse が拾う）
#   weekly : 週1本の有料記事を作り、公開キットを GitHub に送る
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/$(date +%Y-%m-%d).log"
PUBLISH=0

case "${1:-hourly}" in
  morning)
    PROMPT="朝の確認：memory.md と board.md を読み、今日の優先タスクを3つまで進め、判断が必要なものと締切が危ないものだけ報告して" ;;
  hourly)
    PROMPT="board.md をチェックし、進められるタスクを1つ実行。成果物は checker でレビュー。報告は判断が必要な場合と締切超過の場合のみ" ;;
  daily)
    PROMPT="projects/earn/prompts.md の「5. 毎日の無料記事」を実行して。今日の日付は $(date +%Y-%m-%d)"
    PUBLISH=1 ;;
  weekly)
    PROMPT="projects/earn/prompts.md の「6. 週1本の有料記事」を実行して。今日の日付は $(date +%Y-%m-%d)"
    PUBLISH=1 ;;
  *)
    PROMPT="$1" ;;
esac

claude -p "$PROMPT" >> "$LOG" 2>&1

# チェックに合格した号（checked.txt がある号）だけ、公開キットに分ける（まだキットがない号だけ）
for post in outputs/ai/vol*/note-post.txt; do
  [ -f "$post" ] || continue
  [ -f "$(dirname "$post")/checked.txt" ] || continue
  vol=$(basename "$(dirname "$post")")
  kit="outputs/release/ai-$vol"
  if [ ! -d "$kit" ]; then
    python3 scripts/make_release.py "$post" "$(dirname "$post")/images" "$kit" >> "$LOG" 2>&1
    [ -f "$(dirname "$post")/MUSE.md" ] && cp "$(dirname "$post")/MUSE.md" "$kit/"
  fi
done

# 公開キットだけを GitHub に送る（AI ではなく、このスクリプトが決まった手順で行う）
if [ "$PUBLISH" = 1 ] && [ -n "$(git status --porcelain outputs/ projects/ board.md memory.md)" ]; then
  git add outputs/ projects/ board.md memory.md
  git commit -q -m "自動実行（$1）：$(date +%Y-%m-%d) の公開キット" >> "$LOG" 2>&1
  git push -q >> "$LOG" 2>&1 || echo "push に失敗（あとで手動で push）" >> "$LOG"
fi
