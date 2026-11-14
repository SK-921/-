# Jarvis（AI秘書）

Claude Code に「判断軸・仕事ボード・実行チーム・定期実行」の4点セットを持たせたAI秘書の土台です。

| ファイル | 役割 |
|---|---|
| `CLAUDE.md` | 判断軸（目的・任せないこと・報告ルール） |
| `board.md` | 仕事ボード（タスクを1行ずつ） |
| `memory.md` | 学習メモ（失敗と修正） |
| `.claude/agents/maker.md` / `checker.md` | 作る担当 / チェック担当 |
| `.claude/commands/interview.md` | `/interview` で初期インタビュー |
| `.claude/settings.json` | 権限（読み取り＋outputs/projects への書き込みのみ、削除・送信は禁止） |
| `scripts/run.sh` | 定期実行用 |

## 使い始める

1. Claude Code をインストール（Pro 以上のプランが必要）
   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```
2. このリポジトリを clone して中で `claude` を起動
3. `/interview` と打ってインタビューに答える → CLAUDE.md と board.md が出来上がる
4. まずは手動で「board.md を見て今日やることを整理して」と頼む

## 定期実行（慣れてから）

`crontab -e` に追加（まずは1日1回から）：
```cron
50 8 * * 1-5 /path/to/jarvis/scripts/run.sh morning
```
慣れたら毎時実行も：
```cron
0 * * * 1-5 /path/to/jarvis/scripts/run.sh hourly
```
ログは `logs/日付.log` に残ります。Windows はタスクスケジューラで `claude -p "..."` を登録してください。

## 注意
- PC がスリープ中は動きません
- 実行頻度を上げすぎるとプランの5時間枠/週間枠を使い切ります
- 自分のための秘書として使う（他人向けサービスを自分のログインで動かすのは規約違反）
