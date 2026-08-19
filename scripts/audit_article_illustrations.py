"""指定日に公開された長文記事の挿絵・alt・SVGを監査する。"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

from check_heading_density import content_body, text_length

ROOT = Path(__file__).resolve().parents[1]
MINIMUM = 4000


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", action="append", dest="dates")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    today = date.today()
    dates = set(args.dates or [(today - timedelta(days=1)).isoformat(), today.isoformat()])
    pages = json.loads((ROOT / "data" / "pages.json").read_text(encoding="utf-8"))["pages"]
    targets = [p for p in pages if p.get("content_type") == "article" and p.get("published_at") in dates]
    long_pages = 0
    errors: list[str] = []
    for page in targets:
        path = ROOT / str(page["url"]).lstrip("/")
        if not path.exists():
            errors.append(f"{page['url']}: HTMLなし")
            continue
        raw = path.read_text(encoding="utf-8")
        body = content_body(raw)
        if body is None or text_length(body) < MINIMUM:
            continue
        long_pages += 1
        stem = path.stem
        expected = f"/assets/img/article-guides/{stem}.svg"
        image = re.search(rf'<img\b[^>]*\bsrc=["\']{re.escape(expected)}["\'][^>]*>', body, re.I)
        if not image:
            errors.append(f"{page['url']}: 記事固有SVGなし")
            continue
        if not re.search(r'\balt=["\'][^"\']+["\']', image.group(0), re.I):
            errors.append(f"{page['url']}: altなし")
        svg_path = ROOT / expected.lstrip("/")
        if not svg_path.exists():
            errors.append(f"{page['url']}: SVGファイルなし")
            continue
        try:
            svg_root = ET.parse(svg_path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{page['url']}: SVG XML不正 {exc}")
            continue
        ns = {"svg": "http://www.w3.org/2000/svg"}
        if svg_root.find("svg:title", ns) is None or svg_root.find("svg:desc", ns) is None:
            errors.append(f"{page['url']}: SVG title/descなし")
    if errors:
        print(f"illustration audit FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(" - " + error)
        return 1
    print(f"illustration audit OK: {long_pages} long article(s), minimum {MINIMUM} chars, dates {', '.join(sorted(dates))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
