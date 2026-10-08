#!/usr/bin/env python3
"""しおりの JSON から、HTML と PDF のしおりを作る。

使い方:
    python3 build.py <itinerary.json> <output.html>                       # HTML だけ
    python3 build.py <itinerary.json> --pdf <output.pdf>                  # PDF だけ
    python3 build.py <itinerary.json> <output.html> --pdf <output.pdf>    # 両方

PDF は Chrome（または Chromium・Edge）で作る。見つからない場所にあるときは、
環境変数 CHROME_PATH に実行ファイルのパスを入れる。
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import print_layout  # noqa: E402

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

    days, rain_plan = data.get("days"), data.get("rainPlan")
    if isinstance(days, list) and isinstance(rain_plan, list):
        day_dates = {d.get("date") for d in days if isinstance(d, dict)}
        for i, plan in enumerate(rain_plan):
            if not isinstance(plan, dict):
                continue
            if not plan.get("date"):
                errors.append(f"`rainPlan[{i}].date` がありません（どの日の雨天プランかを日付で指定してください）")
            elif plan["date"] not in day_dates:
                errors.append(f"`rainPlan[{i}].date`（{plan['date']}）と同じ日付が `days` にありません")

    for key in ("transport", "stays"):
        entries = data.get(key)
        if not isinstance(entries, list):
            continue
        for i, entry in enumerate(entries):
            links = entry.get("links") if isinstance(entry, dict) else None
            if links is None:
                continue
            if not isinstance(links, list):
                errors.append(f"`{key}[{i}].links` は配列にしてください")
                continue
            for j, lk in enumerate(links):
                if not isinstance(lk, dict) or not re.match(r"^https?://", str(lk.get("url") or "")):
                    errors.append(f"`{key}[{i}].links[{j}].url` は http:// か https:// で始まる URL にしてください")

    articles = data.get("articles")
    if isinstance(articles, list):
        for i, art in enumerate(articles):
            if not isinstance(art, dict):
                errors.append(f"`articles[{i}]` はオブジェクトにしてください")
                continue
            if not str(art.get("title") or "").strip():
                errors.append(f"`articles[{i}].title` がありません")
            if not re.match(r"^https?://", str(art.get("url") or "")):
                errors.append(f"`articles[{i}].url` は http:// か https:// で始まる URL にしてください")

    for key in ("budget", "weather"):
        section = data.get(key)
        if isinstance(section, dict) and "note" in section and section["note"] is not None:
            note = section["note"]
            if not isinstance(note, (str, list)) or (isinstance(note, list) and not all(isinstance(x, str) for x in note)):
                errors.append(f"`{key}.note` は文字列か、文字列の配列にしてください")

    for key, kind in (("members", list), ("transport", list), ("stays", list), ("spots", list), ("articles", list),
                      ("weather", dict), ("packing", dict), ("budget", dict), ("notes", dict)):
        if key in data and data[key] is not None and not isinstance(data[key], kind):
            errors.append(f"`{key}` は{'配列' if kind is list else 'オブジェクト'}にしてください")

    return errors


CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]
CHROME_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome"]


def find_chrome():
    env = os.environ.get("CHROME_PATH")
    if env:
        return env if Path(env).exists() or shutil.which(env) else None
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    for cmd in CHROME_COMMANDS:
        found = shutil.which(cmd)
        if found:
            return found
    return None


def build_html(data, dst):
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise RuntimeError(f"テンプレートにプレースホルダー {PLACEHOLDER} がありません")
    # </script> や <!-- で埋め込みが途切れないよう、< を JSON のエスケープにする
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(template.replace(PLACEHOLDER, payload), encoding="utf-8")


def wait_for_file(proc, path, timeout):
    deadline = time.monotonic() + timeout
    last_size, stable_since = -1, None
    while time.monotonic() < deadline:
        size = path.stat().st_size if path.exists() else -1
        if size > 0 and size == last_size:
            stable_since = stable_since or time.monotonic()
            if proc.poll() is not None or time.monotonic() - stable_since >= 1.5:
                return
        else:
            stable_since = None
        last_size = size
        if proc.poll() is not None and size <= 0:
            return  # Chrome が PDF を作らずに終了した（この後のチェックでエラーにする）
        time.sleep(0.3)
    raise RuntimeError("PDF の作成が 120 秒以内に終わりませんでした")


def build_pdf(data, dst):
    """PDF を作る。Chrome がなければ、印刷用の HTML を残して False を返す。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    html = print_layout.render(data)
    chrome = find_chrome()
    if not chrome:
        fallback = dst.with_suffix(".print.html")
        fallback.write_text(html, encoding="utf-8")
        print("注意: Chrome が見つからないため、PDF を作れませんでした。", file=sys.stderr)
        print(f"  {fallback} をブラウザで開いて、印刷から「PDF に保存」を選んでください。", file=sys.stderr)
        return False
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "print.html"
        src.write_text(html, encoding="utf-8")
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={Path(tmp) / 'profile'}",  # 開いている Chrome とぶつからないよう、別のプロファイルを使う
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={dst.resolve()}",
            src.resolve().as_uri(),
        ]
        if dst.exists():
            dst.unlink()
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as err:
            raise RuntimeError(f"PDF の作成に失敗しました（{chrome}）: {err}") from err
        # 環境によっては、PDF を書き終えても Chrome が終了しないことがある。
        # そのため、PDF のサイズが変わらなくなったら書き終えたとみなして Chrome を閉じる
        try:
            wait_for_file(proc, dst, timeout=120)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
    if not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError("PDF の作成に失敗しました（ファイルができませんでした）")
    return True


def parse_args(argv):
    args = argv[1:]
    pdf = None
    if "--pdf" in args:
        i = args.index("--pdf")
        if i + 1 >= len(args):
            return None
        pdf = Path(args[i + 1])
        args = args[:i] + args[i + 2 :]
    if len(args) not in (1, 2) or (len(args) == 1 and pdf is None):
        return None
    html = Path(args[1]) if len(args) == 2 else None
    return Path(args[0]), html, pdf


def main(argv):
    parsed = parse_args(argv)
    if not parsed:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    src, html_dst, pdf_dst = parsed

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

    try:
        if html_dst:
            build_html(data, html_dst)
            print(f"しおりを作成しました: {html_dst}")
        if pdf_dst and build_pdf(data, pdf_dst):
            print(f"PDF を作成しました: {pdf_dst}")
    except RuntimeError as err:
        print(f"エラー: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
