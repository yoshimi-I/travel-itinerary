---
name: travel-itinerary
description: 旅のしおりを作る。旅行の行き先・日程・メンバー・プラン・持ち物・天気・雨天時のプランをユーザーに質問し、その回答から、タブで切り替えられて配布できる 1 ファイルの HTML のしおりを生成する。「旅のしおり」「しおりを作りたい」「旅行の計画」「旅程表」「travel itinerary」などと言われたときに使う。旅行と関係のない資料の作成には使わない。
---

# 旅のしおり作成（Claude Code）

手順の本体は Codex と共通で、`.agents/skills/travel-itinerary/` にある。

1. リポジトリのルートにある `.agents/skills/travel-itinerary/SKILL.md` を読み、その手順に従う
2. `<skill_dir>` は `.agents/skills/travel-itinerary` と読み替える

## Claude Code での補足

- 選択肢で答えられる質問（オプションを入れるか、AI に日程案を作らせるか、最後の確認など）は `AskUserQuestion` を使う。オプションの選択は `multiSelect: true` にする
- 自由に答える質問（日程・行きたい場所など）は、通常のメッセージでまとめて聞く
- 天気予報は `WebSearch` / `WebFetch` が使えるときだけ調べる
