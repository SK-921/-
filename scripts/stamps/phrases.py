"""スタンプ16個の言葉・ポーズ・動き方（並び順はシートの左上から右へ、行ごと）。

gen_sheet.py はこの順番で ChatGPT に描いてもらい、build_set.py はこの順番で動きを付ける。
motion の種類は build_set.py の MOTIONS を参照。
"""
PHRASES = [
    {"text": "はーい！", "pose": "片手を上げてあいさつ", "motion": "rock"},
    {"text": "ちらっ", "pose": "台のふちから顔を出してのぞく", "motion": "peek"},
    {"text": "ありがとう！", "pose": "ハートを抱えてにっこり", "motion": "pulse"},
    {"text": "ごめん…！", "pose": "頭を下げてあやまる", "motion": "bow"},
    {"text": "つかれた…", "pose": "ぺたんと寝そべる", "motion": "breathe"},
    {"text": "がんばってー！", "pose": "両手を上げて応援", "motion": "hop"},
    {"text": "よろしくです！", "pose": "ていねいにおじぎ", "motion": "nod"},
    {"text": "じー…", "pose": "壁のかげからのぞく", "motion": "lean"},
    {"text": "えっ!?", "pose": "目を丸くしておどろく", "motion": "shock"},
    {"text": "おやすみ〜", "pose": "ふとんで眠る", "motion": "sleep"},
    {"text": "いってきます！", "pose": "元気に走り出す", "motion": "dash"},
    {"text": "ただいまー！", "pose": "かばんを持って手を上げる", "motion": "jump"},
    {"text": "おいしい！", "pose": "おにぎりを食べて幸せそう", "motion": "wiggle"},
    {"text": "？", "pose": "首をかしげる", "motion": "tilt"},
    {"text": "了解！", "pose": "箱から顔を出してうなずく", "motion": "nod"},
    {"text": "のんびり〜", "pose": "あおむけでくつろぐ", "motion": "sway"},
]
