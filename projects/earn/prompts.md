# 稼ぐプロジェクト用プロンプト

Claude Code にそのまま貼るか、`scripts/run.sh "<プロンプト>"` で実行する。

## 1. 下書き作成
```
projects/earn/plan.md の「構成」の第N章を、maker サブエージェントで下書きして
outputs/fe/chN.md に保存して。形は「要点 → 覚え方 → 間違えやすいポイント → 自作の例題1問と解説」。
教科書や過去問の文章は写さず、自分の言葉で書くこと。例題は必ず新しく作ること。
自信がない記述には【要確認】と付けて。
```

## 2. 事実チェック
```
outputs/fe/chN.md を checker サブエージェントでチェックして。
見る点：用語・数値・計算の誤り／例題の答えが正しいか／過去問や教科書の丸写しに見える部分がないか。
指摘は outputs/fe/chN.review.md に書き、合格なら board.md のその章を「確認待ち」にして。
```

## 3. 宣伝文3案
```
outputs/fe/ の完成原稿をもとに、宣伝文を3案作って outputs/fe/promo.md に保存して。
X（旧Twitter）用（140字以内）と、LINE で友達に送る用の2種類。
「必ず受かる」などの誇大表現は使わないこと。投稿はしないで、案だけ作って。
```

## 4. 週次の売上集計
```
projects/earn/sales.csv を読んで、今週の販売数・売上・取り分を集計して、
outputs/fe/weekly-YYYY-MM-DD.md に書いて。目標（月8冊）に対して今いくつかと、次にやると良いことを1つだけ添えて。
```

## 5. 毎日の無料記事（`scripts/run.sh daily` で毎朝実行）
```
CLAUDE.md、memory.md、projects/earn/research.md、projects/earn/daily-log.md を読んでから始めて。
今日の無料記事を1本、maker サブエージェントで書き、checker サブエージェントでチェックして直して。

テーマは次の3つを順番に回す（daily-log.md の最後の行の次）：
  A. AI活用メモ：この Jarvis を実際に動かしてわかったことを1つ（logs/ と memory.md と board.md にある事実だけ）
  B. FE一問一答：outputs/fe/ の内容から、新しく作った1問と解説（過去問の文章・数値は使わない）
  C. 制作記録：今週やったことと、売上の数字（projects/earn/sales.csv にある数字だけ。なければ「まだ0」）

形式：
  - 600〜1,200字。note は Markdown が使えないので、見出しは行だけ、箇条書きは「・」
  - 1行目がタイトル、2行目は空行、3行目から本文
  - 最後に「もっと詳しく：」の行を1つ置き、関連する有料記事のタイトルを書く（リンクは Muse が付ける）
  - 「確実」「必ず」「稼げる」「月○万円」は使わない。起きていないことは書かない

保存先：outputs/release/daily/<今日の日付>/post.txt と、同じフォルダの MUSE.md
  （MUSE.md は outputs/release/daily/MUSE-template.md をコピーして日付だけ変える）
最後に projects/earn/daily-log.md に「日付｜テーマ記号｜タイトル」の1行を足して。
同じ日付のフォルダがもうあるなら、何もしないで終わる。
```

## 6. 週1本の有料記事（`scripts/run.sh weekly` で毎週実行）
```
CLAUDE.md、memory.md、projects/earn/research.md、projects/earn/plan.md の「AI活用シリーズ」を読んでから始めて。
まだ出していない号のうち一番上のものを、maker サブエージェントで outputs/ai/volN/note-post.txt に書き、
checker サブエージェントでチェックして直して。形式は outputs/fe/note-post.txt と同じ。
checker の判定が「合格」になったら、outputs/ai/volN/checked.txt に合格した日付と checker の判定の要約を書き、
outputs/release/fe-vol1/MUSE.md を手本に outputs/ai/volN/MUSE.md を作って。
（checked.txt がない号は、run.sh が公開キットにしない。要修正のままなら checked.txt は作らない）
（公開キットへの分割は scripts/run.sh が自動でやるので、ここではしない）
実際にやっていないこと（まだ起きていない売上など）が必要な号は、書かずに board.md で「確認待ち」にして理由を書く。
```
