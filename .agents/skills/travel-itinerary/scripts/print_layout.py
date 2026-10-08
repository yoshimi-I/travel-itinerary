"""PDF 用のしおりの HTML を作る。

画面用（assets/template.html）とは別のレイアウトで、余白を詰めて読みやすさを優先する。
JavaScript は使わず、ここで HTML を組み立てる（PDF にするときに確実に表示されるようにするため）。
"""

import re
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote

CSS = Path(__file__).resolve().parent.parent / "assets" / "print.css"
WEEK = "月火水木金土日"


# ---- helpers ----------------------------------------------------------------


def has(v):
    if v is None:
        return False
    if isinstance(v, (list, tuple)):
        return len(v) > 0
    if isinstance(v, dict):
        return any(has(x) for x in v.values())
    return str(v).strip() != ""


def e(v):
    return escape("" if v is None else str(v))


def fmt_date(s):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(s or ""))
    if not m:
        return e(s)
    d = date(int(m[1]), int(m[2]), int(m[3]))
    return f"{d.month}/{d.day}（{WEEK[d.weekday()]}）"


def yen(n, cur=None):
    try:
        return f"{int(n):,} {e(cur or '円')}"
    except (TypeError, ValueError):
        return e(n)


def safe_url(u):
    return u if re.match(r"^https?://", str(u or ""), re.I) else None


def link(url, label):
    u = safe_url(url)
    return f'<a href="{e(u)}">{e(label)}</a>' if u else ""


def map_link(query):
    if not has(query):
        return ""
    return f'<a class="map" href="https://www.google.com/maps/search/?api=1&amp;query={quote(str(query))}">地図</a>'


def links_of(entry):
    return " ".join(link(lk.get("url"), lk.get("label") or "リンク") for lk in (entry.get("links") or []) if isinstance(lk, dict))


def tag(text):
    return f' <span class="tag">{e(text)}</span>' if has(text) else ""


def sub(text):
    """1 行下に小さく出す補足。text はエスケープ済みの HTML を渡す。"""
    return f'<span class="sub">{text}</span>' if has(text) else ""


def links_line(html):
    return f'<span class="links">{html}</span>' if has(html) else ""


def join(parts, sep="　"):
    return sep.join(p for p in parts if has(p))


def note_items(v):
    if isinstance(v, list):
        return [str(x) for x in v if has(x)]
    return [t.strip() for t in re.split(r"。|\n", str(v or "")) if t.strip()]


def bullets(v):
    items = note_items(v)
    if not items:
        return ""
    if len(items) == 1:
        return f"<p>{e(items[0])}</p>"
    return '<ul class="bullets">' + "".join(f"<li>{e(t)}</li>" for t in items) + "</ul>"


def kv(rows):
    body = "".join(f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in rows if has(v))
    return f'<dl class="kv">{body}</dl>' if body else ""


def box(title, body, cls=""):
    return f'<div class="box {cls}"><h3>{e(title)}</h3>{body}</div>'


def section(title, body):
    return f"<section><h2>{e(title)}</h2>{body}</section>"


# ---- sections ---------------------------------------------------------------


def overview(data):
    trip = data.get("trip") or {}
    boxes = []

    mt = trip.get("meeting") or {}
    if has(mt):
        when = join([fmt_date(mt["date"]) if mt.get("date") else "", e(mt.get("time"))], " ")
        where = join([e(mt.get("place")), map_link(mt.get("mapQuery"))], " ")
        boxes.append(box("集合", kv([("日時", when), ("場所", where), ("メモ", e(mt.get("note")))])))

    members = data.get("members") or []
    if members:
        items = "".join(f"<li>{e(m.get('name'))}{tag(m.get('role'))}</li>" for m in members)
        boxes.append(box(f"メンバー（{len(members)}人）", f'<ul class="inline">{items}</ul>'))

    transport = data.get("transport") or []
    if transport:
        rows = []
        for t in transport:
            when = join([fmt_date(t["date"]) if t.get("date") else "", e(t.get("type"))], " ")
            route = " → ".join(e(x) for x in (t.get("from"), t.get("to")) if has(x))
            time = " → ".join(e(x) for x in (t.get("depart"), t.get("arrive")) if has(x))
            head = join([f"<b>{when}</b>", route, f'<span class="mono">{time}</span>' if time else ""])
            rows.append(f"<li>{head}{sub(e(t.get('detail')))}{links_line(links_of(t))}</li>")
        boxes.append(box("移動", f'<ul class="rows">{"".join(rows)}</ul>', "wide"))

    stays = data.get("stays") or []
    if stays:
        rows = []
        for s in stays:
            name = e(s.get("name") or s.get("area"))
            area = tag(s.get("area")) if has(s.get("name")) else ""
            period = " → ".join(fmt_date(x) for x in (s.get("checkIn"), s.get("checkOut")) if has(x))
            head = join([f"<b>{name}</b>{area}", f'<span class="mono">{period}</span>' if period else ""])
            more = join([map_link(s.get("mapQuery")), links_of(s)], " ")
            rows.append(f"<li>{head}{sub(e(s.get('note')))}{links_line(more)}</li>")
        boxes.append(box("宿泊", f'<ul class="rows">{"".join(rows)}</ul>'))

    b = data.get("budget") or {}
    if has(b):
        cur = b.get("currency")
        rows = []
        for x in b.get("breakdown") or []:
            if not isinstance(x, dict):
                continue
            amount = yen(x["amount"], cur) if has(x.get("amount")) else "要確認"
            rows.append(f'<li><span>{e(x.get("label"))}</span><span class="mono">{amount}</span></li>')
        if has(b.get("perPerson")):
            rows.append(f'<li class="total"><span>1人あたり</span><span class="mono">{yen(b["perPerson"], cur)}</span></li>')
        amounts = f'<ul class="amounts">{"".join(rows)}</ul>' if rows else ""
        boxes.append(box("予算", amounts + bullets(b.get("note"))))

    return section("概要", f'<div class="grid">{"".join(boxes)}</div>') if boxes else ""


def timeline(items):
    rows = []
    for it in items or []:
        detail = join([e(it.get("place")), e(it.get("note"))])
        rows.append(
            "<tr>"
            f'<td class="time mono">{e(it.get("time"))}</td>'
            f'<td><b>{e(it.get("title"))}</b>{tag(it.get("category"))}{sub(detail)}</td>'
            f'<td class="map-cell">{map_link(it.get("mapQuery"))}</td>'
            "</tr>"
        )
    return f'<table class="timeline">{"".join(rows)}</table>' if rows else ""


def day_note(text):
    return f'<p class="day-note">{e(text)}</p>' if has(text) else ""


def schedule(data):
    rain = {r.get("date"): r for r in (data.get("rainPlan") or []) if isinstance(r, dict) and r.get("date")}
    out = []
    for i, day in enumerate(data.get("days") or [], 1):
        title = e(day.get("title") or f"{i}日目")
        when = fmt_date(day["date"]) if day.get("date") else ""
        head = f'<div class="day-head"><span class="day-no">DAY {i:02d}</span><span class="mono">{when}</span><b>{title}</b></div>'
        body = day_note(day.get("note")) + timeline(day.get("items"))
        r = rain.get(day.get("date"))
        if r:
            rain_title = e(r.get("title") or "雨の日のプラン")
            body += f'<div class="rain"><div class="rain-head">雨天時：{rain_title}</div>{day_note(r.get("note"))}{timeline(r.get("items"))}</div>'
        out.append(f'<div class="day">{head}{body}</div>')
    return section("日程", "".join(out)) if out else ""


def spots(data):
    items = []
    for s in data.get("spots") or []:
        meta = join([e(s.get("day")), e(s.get("category"))], "・")
        more = join([map_link(s.get("mapQuery")), link(s.get("url"), "Web サイト")], " ")
        items.append(f"<li><b>{e(s.get('name'))}</b>{tag(meta)}{sub(e(s.get('description')))}{links_line(more)}</li>")
    return section("プラン", f'<ul class="cols2">{"".join(items)}</ul>') if items else ""


def weather(data):
    w = data.get("weather") or {}
    days = w.get("days") or []
    if not days:
        return ""
    if w.get("source") == "forecast":
        src = f"天気予報（{e(w['checkedAt'])} 時点）" if has(w.get("checkedAt")) else "天気予報"
    else:
        src = "その時期の平年の気候をもとにした目安"
    rows = []
    for d in days:
        temp = join([f"{e(d['high'])}°" if has(d.get("high")) else "", f"{e(d['low'])}°" if has(d.get("low")) else ""], " / ")
        rain = f"{e(d['rainChance'])}%" if has(d.get("rainChance")) else ""
        rows.append(
            f'<tr><td class="mono">{fmt_date(d.get("date"))}</td><td>{e(d.get("summary"))}</td>'
            f'<td class="mono">{temp}</td><td class="mono">{rain}</td><td>{e(d.get("clothing"))}</td></tr>'
        )
    table = '<table class="grid-table"><tr><th>日付</th><th>天気</th><th>最高 / 最低</th><th>降水</th><th>服装</th></tr>' + "".join(rows) + "</table>"
    links = join([link(lk.get("url"), lk.get("label") or lk.get("url")) for lk in (w.get("links") or []) if isinstance(lk, dict)], " ")
    note = f'<p class="note">{src}です。出発前に最新の予報を確認してください。{"　" + links if links else ""}</p>'
    return section("天気", note + table + bullets(w.get("note")))


def packing(data):
    p = data.get("packing") or {}
    groups = []
    for key, title, show_assignee in (("shared", "みんなで用意するもの", True), ("personal", "各自で用意するもの", False)):
        items = p.get(key) or []
        if not items:
            continue
        cats = {}
        for it in items:
            cats.setdefault(it.get("category") or "その他", []).append(it)
        body = ""
        for cat, lst in cats.items():
            lis = "".join(
                f"<li>{e(it.get('item'))}{tag(it.get('assignee')) if show_assignee else ''}{sub(e(it.get('note')))}</li>" for it in lst
            )
            body += f'<div class="cat">{e(cat)}</div><ul class="checks">{lis}</ul>'
        groups.append(box(title, body, "flow"))
    return section("持ち物", f'<div class="grid">{"".join(groups)}</div>') if groups else ""


def notes(data):
    n = data.get("notes") or {}
    parts = []
    if has(n.get("emergency")):
        parts.append(box("緊急連絡先", kv([(x.get("label"), e(x.get("value"))) for x in n["emergency"] if isinstance(x, dict)])))
    if has(n.get("items")):
        parts.append(box("注意事項・メモ", bullets(n["items"])))
    return section("メモ", f'<div class="grid">{"".join(parts)}</div>') if parts else ""


def articles(data):
    rows = []
    for a in data.get("articles") or []:
        if not (isinstance(a, dict) and safe_url(a.get("url")) and has(a.get("title"))):
            continue
        meta = join([join([e(a.get("site")), e(a.get("about"))], "・"), e(a.get("summary"))])
        rows.append(f'<li><a href="{e(a["url"])}"><b>{e(a["title"])}</b></a>{sub(meta)}<span class="url">{e(a["url"])}</span></li>')
    return section("参考ブログ", f'<ul class="rows">{"".join(rows)}</ul>') if rows else ""


def render(data):
    trip = data.get("trip") or {}
    members = data.get("members") or []
    title = e(trip.get("title") or "旅のしおり")
    meta = join(
        [
            e(trip.get("destination")),
            f'{fmt_date(trip.get("startDate"))} 〜 {fmt_date(trip.get("endDate"))}',
            f"{len(members)}人" if members else "",
        ],
        "　｜　",
    )
    summary = f'<p class="summary">{e(trip.get("summary"))}</p>' if has(trip.get("summary")) else ""
    header = f'<header><div class="eyebrow">TRAVEL ITINERARY</div><h1>{title}</h1><div class="meta">{meta}</div>{summary}</header>'
    body = "".join(f(data) for f in (overview, schedule, spots, weather, packing, notes, articles))
    css = CSS.read_text(encoding="utf-8")
    return f'<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>{title}</title><style>{css}</style></head><body>{header}{body}</body></html>'
