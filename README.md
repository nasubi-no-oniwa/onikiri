# 無限鬼斬

名前で決まる日輪刀で、鬼を斬って走る。「色変わりの刀」の続編。なすびのお庭の作品です。

- 遊ぶ：https://nasubi-no-oniwa.com/onikiri/
- ゲーム本体は nasubi-site リポジトリの `onikiri/` フォルダにあります（nasubi-no-oniwa.com で公開）
- このリポジトリはランキングのルール用：`database.rules.onikiri.json` を上げると自動で otokonoji の `onikiri` の部分だけに反映（鍵は Secrets の `OTOKONOJI_SERVICE_ACCOUNT`。ほかのゲームのルールはそのまま残す）
- ランキングの置き場所：全体 `onikiri/n/名前の鍵`、今日 `onikiri/t/日付/名前の鍵`、呼吸ごと `onikiri/k/呼吸/名前の鍵`。名前1つにつき1件だけ（どの技の組みあわせでも、その名前でいちばん良い記録が残る。いまの記録より伸びたときだけ書きかえられる）。`r`・`d`・`b` は試遊のときの古い置き場所
