# しおり JSON の仕様

`scripts/build.py` に渡す JSON の形です。**必須は `trip` の 4 項目と `days` だけ**で、それ以外は省略できます。
省略したセクション（または空のセクション）のタブは、しおりに表示されません。

- 日付はすべて `YYYY-MM-DD`、時刻は `HH:MM`（例: `07:30`）
- `mapQuery` は Google マップで検索する文字列です。施設名＋地名にすると正確になります（例: `小樽運河 北海道小樽市`）
- 未定の項目は、キーを省略するか、`"未定"` と書きます
- 文字列は HTML としてではなく、テキストとして表示されます（タグは使えません）

## 全体

| キー | 型 | 必須 | タブ | 内容 |
|------|----|------|------|------|
| `trip` | object | ✅ | 概要 | 旅の基本情報 |
| `members` | array | | 概要 | メンバー |
| `transport` | array | | 概要 | 移動（行き・帰り・現地の移動） |
| `stays` | array | | 概要 | 宿泊先 |
| `budget` | object | | 概要 | 予算 |
| `days` | array | ✅ | 日程 | 日ごとのタイムスケジュール |
| `spots` | array | | プラン | 行く場所・食事処の詳細 |
| `articles` | array | | 参考ブログ | 参考になるブログ・記事 |
| `weather` | object | | 天気 | 天気の目安 |
| `rainPlan` | array | | 日程 | 雨の日の代わりの予定（`days` と同じ形）。同じ日付の日程で「晴れ / 雨天」を切り替えられる |
| `packing` | object | | 持ち物 | 持ち物リスト |
| `notes` | object | | メモ | 緊急連絡先・注意事項 |

## 各セクション

### trip
| キー | 必須 | 内容 |
|------|------|------|
| `title` | ✅ | 旅のタイトル |
| `destination` | ✅ | 行き先 |
| `startDate` / `endDate` | ✅ | 出発日 / 帰着日 |
| `summary` | | ひとこと（旅のテーマなど） |
| `meeting` | | 集合: `{ date, time, place, mapQuery, note }` |

### members[]
`{ name, role, note }` — `role` は「幹事」「運転」など。**本名ではなくニックネームを推奨します。**

### transport[]
`{ date, type, from, to, depart, arrive, detail }` — `type` は「飛行機」「新幹線」「レンタカー」など。`depart` / `arrive` は時刻です。

### stays[]
`{ name, area, checkIn, checkOut, mapQuery, note }`

### budget
`{ perPerson, currency, breakdown: [{ label, amount }], note }` — 金額は数値で書きます。`currency` を省略すると「円」になります。

### days[] / rainPlan[]
```json
{
  "date": "2026-08-10",
  "label": "1日目",
  "title": "札幌へ",
  "note": "朝が早いので前日は早めに寝る",
  "items": [
    { "time": "07:30", "title": "羽田空港に集合", "place": "第2ターミナル 出発ロビー", "mapQuery": "羽田空港 第2ターミナル", "note": "", "category": "移動" }
  ]
}
```
`label` を省略すると「1日目」「2日目」…と自動で付きます。`rainPlan` は、雨の場合に差し替える日だけを書けば十分です。**`rainPlan` の `date` は必須**で、`days` のどれかと同じ日付にします。その日の日程カードに「晴れ / 雨天」の切り替えボタンが付き、日程タブの先頭には全日をまとめて切り替えるボタンが出ます。印刷時は、晴れと雨天の両方が出力されます。

### spots[]
`{ name, category, day, description, mapQuery, url }` — `category` は「観光」「ごはん」「おみやげ」など。`day` は「1日目」などの目安。`url` は `http(s)://` で始まるものだけがリンクになります。

### articles[]
```json
{
  "title": "記事のタイトル（ページの見出しのまま）",
  "url": "https://example.com/blog/otaru",
  "site": "サイト名",
  "kind": "ブログ",
  "about": "小樽運河",
  "summary": "1〜2 文の要約。本文を書き写さない",
  "publishedAt": "2025-07-01",
  "checkedAt": "2026-10-08"
}
```
- 必須は `title` と `url`（`http(s)://` で始まるもの）
- `kind`: `ブログ` / `旅行メディア` / `公式サイト` など
- `about`: 関係する場所。同じ `about` の記事はまとめて表示されます。省略すると「旅全体」になります
- `publishedAt`: 記事の公開日・更新日（分かれば）。`checkedAt`: 実際に開いて確認した日
- **実際に開いて確認した URL だけを書く**（推測で作らない）

### weather
```json
{
  "source": "climate",
  "checkedAt": "2026-08-01",
  "note": "朝晩は涼しいので羽織るものを",
  "links": [{ "label": "tenki.jp 札幌", "url": "https://tenki.jp/" }],
  "days": [
    { "date": "2026-08-10", "condition": "sunny", "summary": "晴れ", "high": 26, "low": 18, "rainChance": 20, "clothing": "半袖＋薄手の上着" }
  ]
}
```
- `source`: 予報を調べた場合は `"forecast"`、平年の気候を目安にした場合は `"climate"`。しおりに出る注意書きが変わります
- `checkedAt`: 予報を調べた日（`forecast` のとき）
- `condition`: 天気のアイコン。`sunny`（晴れ）/ `partly`（晴れ時々くもり）/ `cloudy`（くもり）/ `rain`（雨）/ `snow`（雪）/ `storm`（雷雨）/ `fog`（霧）のどれか。省略すると `summary` の文言から推測します

### packing
```json
{
  "shared": [{ "item": "モバイルバッテリー", "category": "電子機器", "assignee": "たろう", "note": "" }],
  "personal": [{ "item": "着替え（2泊分）", "category": "衣類", "note": "" }]
}
```
`shared` はみんなで 1 つあればよいもの（`assignee` に担当者）、`personal` は各自で用意するものです。チェック状態は、開いた端末のブラウザに保存されます。

### notes
`{ emergency: [{ label, value }], items: ["..."] }` — `emergency` は「宿の電話番号」「最寄りの病院」など、`items` は注意事項の箇条書きです。

## 完全な例
[`examples/sample-trip.json`](../../../../examples/sample-trip.json) を参照してください。
