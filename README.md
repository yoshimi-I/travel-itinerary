# Travel Itinerary

[![CI](https://github.com/yoshimi-I/travel-itinerary/actions/workflows/ci.yml/badge.svg)](https://github.com/yoshimi-I/travel-itinerary/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI エージェントに質問してもらいながら、旅のしおりを作るための skill です。Claude Code、Codex、Kiro で動きます。

旅行の幹事をやると、日程や集合場所、持ち物をまとめてみんなに共有するのが地味に手間です。これを使うと、AI の質問に答えていくだけで、スマホで見やすい 1 ファイルの HTML のしおりができあがります。そのまま LINE やメールで送れます。

できあがりはこんな感じです: [examples/sample-trip.html](examples/sample-trip.html)（ダウンロードしてブラウザで開いてください）

## インストール

ターミナルで次を実行すると、Claude Code・Codex・Kiro のすべてに入ります。

```bash
curl -fsSL https://raw.githubusercontent.com/yoshimi-I/travel-itinerary/main/install.sh | bash
```

`~/.claude/skills/`、`~/.agents/skills/`（Codex）、`~/.kiro/skills/` に skill がコピーされるので、どのフォルダからでも使えます。使うものだけに入れたいときは、`--claude`・`--codex`・`--kiro` を付けてください（`--claude --kiro` のように組み合わせもできます）。もう一度実行すると最新版に更新され、`--uninstall` で削除できます。新しいバージョンが出ると、skill を使い始めたときに AI が教えてくれます（確認は 1 日 1 回まで。`TRAVEL_ITINERARY_NO_UPDATE_CHECK=1` で止められます）。

clone して使うこともできます。

```bash
git clone https://github.com/yoshimi-I/travel-itinerary.git
cd travel-itinerary
./install.sh
```

macOS と Linux（Windows は WSL）で動きます。Python 3 があると、しおりの作成が安定します。

## 使い方

しおりを保存したいフォルダでエージェントを起動します。Claude Code と Kiro なら `/travel-itinerary`、Codex なら `$travel-itinerary` で始まります。「旅のしおりを作りたい」と話しかけるだけでも大丈夫です。

最初に「もう決まっていること」を聞かれるので、予約済みの飛行機や宿、行きたい場所、予算など、分かっていることを自由に書いてください。予約メールを貼り付けても大丈夫です。

あとは、足りないことだけを選択肢で聞かれます（予算の目安や、天気・雨天プラン・持ち物・参考ブログを入れるかなど）。夜ごはんのお店や空いた時間の過ごし方、雨の日のプランは AI が調べて提案してくれるので、最後にまとめて見て「この内容で作る」を選べば完成です。気になるところだけ変えることもできます。

しおりは、起動したフォルダの `output/<旅の名前>/index.html` に作られます。直したいところは、そのまま AI に伝えれば作り直してくれます。

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

skill の本体は `.agents/skills/travel-itinerary/` にあります。`install.sh` は、これを各エージェントの skill のフォルダにそのままコピーします。リポジトリの `.claude/skills/` と `.kiro/skills/` にあるものは、clone したリポジトリの中で Claude Code や Kiro を使うときのための入口です。

Kiro のカスタムエージェントは、skill を自動では読み込みません。カスタムエージェントで使う場合は、設定の `resources` に `skill://~/.kiro/skills/travel-itinerary/SKILL.md` を追加してください（標準のエージェントならそのまま使えます）。

```
.agents/skills/travel-itinerary/
├── SKILL.md                 # 手順
├── references/interview.md  # 質問の進め方
├── references/schema.md     # JSON の仕様
├── assets/template.html     # しおりのテンプレート
├── scripts/build.py         # JSON を HTML にする
├── scripts/check_update.sh  # 新しいバージョンがあるかの確認
└── VERSION
.claude/skills/travel-itinerary/SKILL.md  # Claude Code 用の入口
.kiro/skills/travel-itinerary/SKILL.md    # Kiro 用の入口
examples/                    # サンプル（中身は架空です）
install.sh                   # インストール用スクリプト
tests/
```

## 個人情報について

しおりには電話番号や予約の情報が入ることがあるので、作ったしおりは `output/` に保存して git の管理から外しています。Web に公開するときは、中身を一度確認してください。予約確認ページの URL は、予約番号などが含まれることがあるので、しおりに入れないようにしています。

## 開発

```bash
python3 -m unittest discover -s tests -v
```

テンプレートやサンプルの JSON を変えたときは、サンプルの HTML も作り直してコミットしてください。使う人に更新を届けたいときは、`.agents/skills/travel-itinerary/VERSION` の番号を上げて main に push します。タグ（`v0.2.0` など）と GitHub の Release が自動で作られ、インストールした人には、次に使ったときに更新のお知らせが出ます。CI（GitHub Actions）で、テスト、サンプルが最新かどうか、テンプレートの JavaScript の構文と、`install.sh` のインストール・削除（macOS と Linux）をチェックしています。

```bash
python3 .agents/skills/travel-itinerary/scripts/build.py examples/sample-trip.json examples/sample-trip.html
```

英語版は、これからやる予定です。Issue や Pull Request は気軽にどうぞ。

## License

[MIT](LICENSE)
