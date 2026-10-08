---
name: travel-itinerary
description: 旅のしおりを作る。旅行の行き先・日程・メンバー・プラン・持ち物・天気・雨天時のプランをユーザーに質問し、その回答から、タブで切り替えられて配布できる 1 ファイルの HTML のしおりを生成する。「旅のしおり」「しおりを作りたい」「旅行の計画」「旅程表」「travel itinerary」などと言われたときに使う。旅行と関係のない資料の作成には使わない。
---

# 旅のしおり作成（このリポジトリの中で Kiro から使うための入口）

手順の本体は `.agents/skills/travel-itinerary/` にある。リポジトリのルートにある `.agents/skills/travel-itinerary/SKILL.md` を読み、その手順に従う。`<skill_dir>` は `.agents/skills/travel-itinerary` の絶対パスと読み替える。

`install.sh` でインストールした場合は、本体がまるごと `~/.kiro/skills/travel-itinerary/` にコピーされるので、このファイルは使われない。
