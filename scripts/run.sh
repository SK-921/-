#!/usr/bin/env bash
# 定期実行用ラッパー。cron / タスクスケジューラから呼ぶ。
# 使い方: scripts/run.sh morning | hourly
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs

case "${1:-hourly}" in
  morning)
    PROMPT="朝の確認：memory.md と board.md を読み、今日の優先タスクを3つまで進め、判断が必要なものと締切が危ないものだけ報告して" ;;
  hourly)
    PROMPT="board.md をチェックし、進められるタスクを1つ実行。成果物は checker でレビュー。報告は判断が必要な場合と締切超過の場合のみ" ;;
  *)
    PROMPT="$1" ;;
esac

claude -p "$PROMPT" >> "logs/$(date +%Y-%m-%d).log" 2>&1
