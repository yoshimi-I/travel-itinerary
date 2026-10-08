# Travel Itinerary

[![CI](https://github.com/yoshimi-I/travel-itinerary/actions/workflows/ci.yml/badge.svg)](https://github.com/yoshimi-I/travel-itinerary/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI エージェントに質問してもらいながら、旅のしおりを作るための skill です。Claude Code と Codex で動きます。

旅行の幹事をやると、日程や集合場所、持ち物をまとめてみんなに共有するのが地味に手間です。これを使うと、AI の質問に答えていくだけで、スマホで見やすい 1 ファイルの HTML のしおりができあがります。そのまま LINE やメールで送れます。

できあがりはこんな感じです: [examples/sample-trip.html](examples/sample-trip.html)（ダウンロードしてブラウザで開いてください）

## 使い方

clone して、リポジトリの中でエージェントを起動します。

```bash
git clone https://github.com/yoshimi-I/travel-itinerary.git
cd travel-itinerary
```

Claude Code なら `/travel-itinerary`、Codex なら `$travel-itinerary` で始まります。「旅のしおりを作りたい」と話しかけるだけでも大丈夫です。

最初に「もう決まっていることはありますか？」と聞かれるので、予約済みの飛行機や宿、行きたい場所、予算など、分かっていることを書いてください。あとは足りないところだけを、次の順番で少しずつ聞かれます。

1. 基本情報（行き先、日程、メンバー、移動手段、宿）
2. 予算（1 人あたりの予算、何にお金をかけたいか、精算のしかた）
3. 日程とプラン（行きたい場所、食べたいもの、集合時刻など）
4. オプション（雨の日のプラン、持ち物リスト、天気、参考ブログ、緊急連絡先）

決まっていないところは「未定」や「おまかせ」で進められます。おまかせにした部分は AI が提案して、提案だと分かるように確認してくれます。

最後に内容を確認すると、`output/<旅の名前>/index.html` にしおりが作られます。直したいところは、そのまま AI に伝えれば作り直してくれます。

## しおりの中身

しおりはタブで切り替えるようになっていて、情報がない項目のタブは出ません。

- 概要: 集合場所と時刻、メンバー、移動、宿、予算。飛行機や船には、運航状況などのリンクも付けられます
- 日程: 日ごとのタイムスケジュール。雨の日のプランがある日は、「晴れ / 雨天」ボタンで切り替えられます
- プラン: 行く場所やお店の説明と、地図へのリンク
- 天気: 日ごとの天気と服装の目安
- 持ち物: チェックできる持ち物リスト。チェックした状態はブラウザに残ります
- メモ: 緊急連絡先や注意事項
- 参考ブログ: 行き先について参考になるブログや記事

天気は、出発が近ければ天気予報を調べて載せます。まだ先の旅行なら、その時期の平年の気候を目安として載せます。参考ブログと天気予報は Web 検索を使うので、検索できない環境では省略されます。参考ブログは、AI が実際にページを開いて確かめたものだけが載ります。

印刷すると全部のタブが順番に出るので、紙で配りたいときは PDF にして使えます。

## しくみ

AI は回答をもとに `itinerary.json` を書くだけで、見た目はテンプレート（`assets/template.html`）が決めています。なので、どのエージェントで作っても同じデザインになります。

```bash
# JSON から HTML を作る（Python 3 の標準ライブラリだけで動きます）
python3 .agents/skills/travel-itinerary/scripts/build.py examples/sample-trip.json output/sample/index.html
```

JSON の書き方は [schema.md](.agents/skills/travel-itinerary/references/schema.md) にまとめています。

skill の本体は `.agents/skills/travel-itinerary/` にあり、Codex はここを直接読みます。`.claude/skills/travel-itinerary/` は、Claude Code から本体を読むための入口です。

```
.agents/skills/travel-itinerary/
├── SKILL.md                 # 手順
├── references/interview.md  # 質問の進め方
├── references/schema.md     # JSON の仕様
├── assets/template.html     # しおりのテンプレート
└── scripts/build.py         # JSON を HTML にする
.claude/skills/travel-itinerary/SKILL.md
examples/                    # サンプル（中身は架空です）
tests/
```

## 個人情報について

しおりには電話番号や予約の情報が入ることがあるので、作ったしおりは `output/` に保存して git の管理から外しています。Web に公開するときは、中身を一度確認してください。予約確認ページの URL は、予約番号などが含まれることがあるので、しおりに入れないようにしています。

## 開発

```bash
python3 -m unittest discover -s tests -v
```

テンプレートやサンプルの JSON を変えたときは、サンプルの HTML も作り直してコミットしてください。CI（GitHub Actions）で、テスト、サンプルが最新かどうか、テンプレートの JavaScript の構文をチェックしています。

```bash
python3 .agents/skills/travel-itinerary/scripts/build.py examples/sample-trip.json examples/sample-trip.html
```

Kiro への対応と英語版は、これからやる予定です。Issue や Pull Request は気軽にどうぞ。

## License

[MIT](LICENSE)
