"""scripts/build.py のテスト（標準ライブラリの unittest のみ）。

実行: python3 -m unittest discover -s tests -v
"""

import copy
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / ".agents" / "skills" / "travel-itinerary"
SAMPLE = ROOT / "examples" / "sample-trip.json"

spec = importlib.util.spec_from_file_location("build", SKILL_DIR / "scripts" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

MINIMAL = {
    "trip": {"title": "t", "destination": "d", "startDate": "2026-01-01", "endDate": "2026-01-02"},
    "days": [{"date": "2026-01-01", "items": []}],
}


def errors_for(data):
    return build.validate(data)


class ValidateTest(unittest.TestCase):
    def test_sample_is_valid(self):
        data = json.loads(SAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(errors_for(data), [])

    def test_minimal_is_valid(self):
        self.assertEqual(errors_for(MINIMAL), [])

    def test_missing_required_fields(self):
        errs = errors_for({"trip": {"title": "t"}, "days": []})
        joined = "\n".join(errs)
        for key in ("trip.destination", "trip.startDate", "trip.endDate", "days"):
            self.assertIn(key, joined)

    def test_bad_date_format(self):
        data = copy.deepcopy(MINIMAL)
        data["trip"]["startDate"] = "2026/01/01"
        self.assertTrue(any("trip.startDate" in e for e in errors_for(data)))

    def test_rain_plan_must_match_a_day(self):
        data = copy.deepcopy(MINIMAL)
        data["rainPlan"] = [{"date": "2026-01-05", "items": []}, {"items": []}]
        errs = errors_for(data)
        self.assertTrue(any("rainPlan[0].date" in e for e in errs))
        self.assertTrue(any("rainPlan[1].date" in e for e in errs))

    def test_transport_links_must_be_http(self):
        data = copy.deepcopy(MINIMAL)
        data["transport"] = [{"type": "飛行機", "links": [{"label": "x", "url": "javascript:alert(1)"}]}]
        self.assertTrue(any("transport[0].links[0].url" in e for e in errors_for(data)))

    def test_articles_need_title_and_http_url(self):
        data = copy.deepcopy(MINIMAL)
        data["articles"] = [{"url": "ftp://example.com"}]
        errs = errors_for(data)
        self.assertTrue(any("articles[0].title" in e for e in errs))
        self.assertTrue(any("articles[0].url" in e for e in errs))

    def test_wrong_section_type(self):
        data = copy.deepcopy(MINIMAL)
        data["packing"] = []
        self.assertTrue(any("packing" in e for e in errors_for(data)))


spec_pl = importlib.util.spec_from_file_location("print_layout", SKILL_DIR / "scripts" / "print_layout.py")
print_layout = importlib.util.module_from_spec(spec_pl)
spec_pl.loader.exec_module(print_layout)


class ArgsTest(unittest.TestCase):
    def test_html_only(self):
        self.assertEqual(build.parse_args(["b", "in.json", "out.html"]), (Path("in.json"), Path("out.html"), None))

    def test_pdf_only(self):
        self.assertEqual(build.parse_args(["b", "in.json", "--pdf", "o.pdf"]), (Path("in.json"), None, Path("o.pdf")))

    def test_both(self):
        self.assertEqual(build.parse_args(["b", "in.json", "o.html", "--pdf", "o.pdf"]), (Path("in.json"), Path("o.html"), Path("o.pdf")))

    def test_needs_an_output(self):
        self.assertIsNone(build.parse_args(["b", "in.json"]))
        self.assertIsNone(build.parse_args(["b", "in.json", "--pdf"]))


class PrintLayoutTest(unittest.TestCase):
    def test_renders_sample_sections(self):
        data = json.loads(SAMPLE.read_text(encoding="utf-8"))
        html = print_layout.render(data)
        for title in ("概要", "日程", "プラン", "天気", "持ち物", "メモ", "参考ブログ", "雨天時"):
            self.assertIn(title, html)
        self.assertNotIn("<script", html)

    def test_escapes_text(self):
        data = copy.deepcopy(MINIMAL)
        data["trip"]["title"] = "<img src=x onerror=alert(1)>"
        data["days"][0]["items"] = [{"title": "<b>x</b>", "mapQuery": "a&b"}]
        html = print_layout.render(data)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", html)

    def test_skips_empty_sections_and_unsafe_links(self):
        data = copy.deepcopy(MINIMAL)
        data["articles"] = [{"title": "x", "url": "javascript:alert(1)"}]
        html = print_layout.render(data)
        self.assertNotIn("参考ブログ", html)
        self.assertNotIn("javascript:", html)

    def test_note_becomes_bullets(self):
        data = copy.deepcopy(MINIMAL)
        data["budget"] = {"note": "一つ目。二つ目。"}
        self.assertIn('<ul class="bullets"><li>一つ目</li><li>二つ目</li></ul>', print_layout.render(data))


class VersionTest(unittest.TestCase):
    def test_version_is_semver(self):
        version = (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^[0-9]+\.[0-9]+\.[0-9]+$")


class BuildTest(unittest.TestCase):
    def run_build(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.json"
            dst = Path(tmp) / "out" / "index.html"
            src.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            code = build.main(["build.py", str(src), str(dst)])
            html = dst.read_text(encoding="utf-8") if dst.exists() else None
            return code, html

    def test_builds_html_with_embedded_data(self):
        code, html = self.run_build(MINIMAL)
        self.assertEqual(code, 0)
        self.assertNotIn(build.PLACEHOLDER, html)
        payload = re.search(r'<script type="application/json" id="itinerary-data">(.*?)</script>', html, re.S).group(1)
        self.assertEqual(json.loads(payload), MINIMAL)

    def test_escapes_script_breakout(self):
        data = copy.deepcopy(MINIMAL)
        data["trip"]["title"] = "</script><img src=x onerror=alert(1)><!--"
        code, html = self.run_build(data)
        self.assertEqual(code, 0)
        payload = re.search(r'id="itinerary-data">(.*?)</script>', html, re.S).group(1)
        self.assertNotIn("<", payload)
        self.assertEqual(json.loads(payload)["trip"]["title"], data["trip"]["title"])

    def test_invalid_data_returns_error(self):
        code, html = self.run_build({"trip": {}})
        self.assertEqual(code, 1)
        self.assertIsNone(html)

    def test_broken_json_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.json"
            src.write_text("{broken", encoding="utf-8")
            self.assertEqual(build.main(["build.py", str(src), str(Path(tmp) / "o.html")]), 1)


if __name__ == "__main__":
    unittest.main()
