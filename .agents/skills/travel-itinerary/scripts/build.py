#!/usr/bin/env python3
"""しおりの JSON をテンプレートに埋め込んで、1 ファイルの HTML を出力する。

使い方:
    python3 build.py <itinerary.json> <output.html>
"""

import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
PLACEHOLDER = "/*__ITINERARY_DATA__*/"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["JSON のトップレベルはオブジェクトにしてください"]

    trip = data.get("trip")
    if not isinstance(trip, dict):
        errors.append("`trip` がありません")
    else:
        for key in ("title", "destination", "startDate", "endDate"):
            if not str(trip.get(key) or "").strip():
                errors.append(f"`trip.{key}` がありません")
        for key in ("startDate", "endDate"):
            value = trip.get(key)
            if value and not DATE_RE.match(str(value)):
                errors.append(f"`trip.{key}` は YYYY-MM-DD 形式にしてください（{value}）")

    for list_key in ("days", "rainPlan"):
        days = data.get(list_key)
        if days is None and list_key == "rainPlan":
            continue
        if not isinstance(days, list) or (list_key == "days" and not days):
            errors.append(f"`{list_key}` は 1 日以上の配列にしてください")
            continue
        for i, day in enumerate(days):
            where = f"`{list_key}[{i}]`"
            if not isinstance(day, dict):
                errors.append(f"{where} はオブジェクトにしてください")
                continue
            if day.get("date") and not DATE_RE.match(str(day["date"])):
                errors.append(f"{where}.date は YYYY-MM-DD 形式にしてください（{day['date']}）")
            if not isinstance(day.get("items", []), list):
                errors.append(f"{where}.items は配列にしてください")

    for key, kind in (("members", list), ("transport", list), ("stays", list), ("spots", list),
                      ("weather", dict), ("packing", dict), ("budget", dict), ("notes", dict)):
        if key in data and data[key] is not None and not isinstance(data[key], kind):
            errors.append(f"`{key}` は{'配列' if kind is list else 'オブジェクト'}にしてください")

    return errors


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    src, dst = Path(argv[1]), Path(argv[2])
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"エラー: {src} が見つかりません", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"エラー: {src} の JSON が壊れています（{e.lineno} 行目 {e.colno} 文字目: {e.msg}）", file=sys.stderr)
        return 1

    errors = validate(data)
    if errors:
        print(f"エラー: {src} の内容に問題があります", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        print(f"エラー: テンプレートにプレースホルダー {PLACEHOLDER} がありません", file=sys.stderr)
        return 1

    # </script> や <!-- で埋め込みが途切れないよう、< を JSON のエスケープにする
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    html = template.replace(PLACEHOLDER, payload)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html, encoding="utf-8")
    print(f"しおりを作成しました: {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
