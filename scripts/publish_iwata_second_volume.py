from __future__ import annotations

import html
import json
import re
from pathlib import Path

from iwata_second_volume_data import ARTICLES as MIXED
from iwata_second_volume_admin_data import ARTICLES as ADMIN
from iwata_second_volume_education_a_data import ARTICLES as EDUCATION


ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-24"
ARTICLES = MIXED + ADMIN + EDUCATION
EXPECTED = {
    "c138", "c139", "c140", "c141", "c142", "c143", "c144", "c145",
    "c146", "c147", "c148", "c149", "c150", "c151", "c152", "c153",
    "c154", "n099", "s035",
}
ENHANCED = {
    "c017.html", "c094.html", "c103.html", "c115.html", "c116.html",
    "c125.html", "c128.html", "m015.html", "m180.html", "n091.html",
    "iwata-nishi-high-school-history.html", "iwata-higashi-high-school-history.html",
    "iwata-minami-high-school-history.html", "iwata-nogyo-high-school-history.html",
    "iwata-kita-high-school-history.html",
}


THEMES = {
    "c138": ["modern-history", "political-history", "self-government"],
    "c139": ["modern-history", "administration", "self-government"],
    "c140": ["modern-history", "social-history", "people"],
    "c141": ["modern-history", "administration", "village-governance"],
    "c142": ["modern-history", "self-government", "life"],
    "c143": ["modern-history", "administration", "municipal-history"],
    "c144": ["modern-history", "social-history", "industry"],
    "c145": ["modern-history", "political-history", "war-memory"],
    "c146": ["modern-history", "communication", "self-government"],
    "c147": ["modern-history", "municipal-history", "culture"],
    "c148": ["modern-history", "school", "modern-education"],
    "c149": ["modern-history", "school", "administration"],
    "c150": ["modern-history", "school", "life"],
    "c151": ["war-memory", "school", "peace"],
    "c152": ["modern-history", "school", "modern-education"],
    "c153": ["postwar", "school", "self-government"],
    "c154": ["modern-history", "modern-education", "social-history"],
    "n099": ["school", "modern-education", "architecture"],
    "s035": ["school", "modern-education", "person", "source-criticism"],
}


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def verify_articles() -> dict[str, dict]:
    by_slug = {article["slug"]: article for article in ARTICLES}
    if set(by_slug) != EXPECTED or len(ARTICLES) != len(EXPECTED):
        missing = sorted(EXPECTED - set(by_slug))
        extra = sorted(set(by_slug) - EXPECTED)
        raise RuntimeError(f"article set mismatch: missing={missing}, extra={extra}")
    return by_slug


def update_pages(by_slug: dict[str, dict]) -> None:
    path = ROOT / "data" / "pages.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    pages = doc["pages"]
    by_url = {page["url"].lstrip("/"): page for page in pages}
    for slug, article in by_slug.items():
        url = f"{slug}.html"
        district = ["nakaizumi"] if slug == "n099" else ["nanbu"] if slug == "s035" else ["common"]
        record = {
            "title": article["title"],
            "url": url,
            "district": district,
            "themes": THEMES[slug],
            "content_type": "article",
            "published_at": DATE,
            "updated_at": DATE,
            "date_provisional": False,
            "status": "published",
            "count_as_knowledge": True,
            "show_in_updates": True,
            "show_in_all_articles": True,
            "section": "中泉" if slug == "n099" else "南部" if slug == "s035" else "磐田共通・資料",
            "topics": article["topics"],
            "level": "L2",
            "summary": strip_tags(article["description"]),
            "source_refs": [f"book:磐田ことはじめ 第二編・現代編:{article['book_pages']}頁"],
        }
        if url in by_url:
            by_url[url].update(record)
        else:
            pages.append(record)
            by_url[url] = record
    for url in ENHANCED:
        if url not in by_url:
            raise RuntimeError(f"enhancement registry target missing: {url}")
        by_url[url]["updated_at"] = DATE
        refs = by_url[url].setdefault("source_refs", [])
        source = "book:磐田ことはじめ 第二編・現代編:行政・自治会17〜55頁／学校・教育56〜88頁"
        if source not in refs:
            refs.append(source)
    doc["updated_at"] = DATE
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_recent(by_slug: dict[str, dict]) -> None:
    path = ROOT / "data" / "new-articles.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    targets = {f"/{slug}.html" for slug in by_slug} | {f"/{slug}" for slug in by_slug}
    items = [item for item in items if item.get("url") not in targets]
    order = [
        "c138", "c139", "c140", "c141", "c142", "c143", "c144", "c145", "c146", "c147",
        "n099", "s035", "c148", "c149", "c150", "c151", "c152", "c153", "c154",
    ]
    fresh = []
    for index, slug in enumerate(order):
        article = by_slug[slug]
        minute = 59 - index
        fresh.append({
            "date": DATE,
            "category": article["category"],
            "title": article["title"],
            "url": f"/{slug}.html",
            "published_at": f"2026-08-24T20:{minute:02}:00+09:00",
        })
    combined = fresh + items
    combined.sort(key=lambda x: (x.get("date", ""), x.get("published_at", "")), reverse=True)
    path.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_index(by_slug: dict[str, dict]) -> None:
    path = ROOT / "c034.html"
    raw = path.read_text(encoding="utf-8")

    def add_after(marker_slug: str, slugs: list[str]) -> None:
        nonlocal raw
        additions = "\n".join(
            f'<li><a href="/{slug}.html">{html.escape(by_slug[slug]["title"])}</a></li>'
            for slug in slugs if f'href="/{slug}.html"' not in raw
        )
        if not additions:
            return
        match = re.search(rf'<li><a href="/{marker_slug}\.html">.*?</a></li>', raw)
        if not match:
            raise RuntimeError(f"c034 marker missing: {marker_slug}")
        raw = raw[:match.end()] + "\n" + additions + raw[match.end():]

    add_after("c137", [f"c{number}" for number in range(138, 155)])
    add_after("n098", ["n099"])
    add_after("s034", ["s035"])
    path.write_text(raw, encoding="utf-8", newline="\n")


def update_sitemap(by_slug: dict[str, dict]) -> None:
    path = ROOT / "sitemap.xml"
    raw = path.read_text(encoding="utf-8", errors="replace")
    for slug in by_slug:
        pattern = rf'(<url>\s*<loc>https://iwata-monogatari\.net/{slug}(?:\.html)?</loc>\s*<lastmod>)[^<]+(</lastmod>)'
        if re.search(pattern, raw):
            raw = re.sub(pattern, rf'\g<1>{DATE}\g<2>', raw, count=1)
        else:
            entry = f'  <url><loc>https://iwata-monogatari.net/{slug}</loc><lastmod>{DATE}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
            pos = raw.rfind("</urlset>")
            if pos < 0:
                raise RuntimeError("sitemap closing tag missing")
            raw = raw[:pos] + entry + raw[pos:]
    path.write_text(raw, encoding="utf-8", newline="\n")


def main() -> None:
    by_slug = verify_articles()
    update_pages(by_slug)
    update_recent(by_slug)
    update_index(by_slug)
    update_sitemap(by_slug)
    print(f"registered {len(by_slug)} new pages and {len(ENHANCED)} enhancements")


if __name__ == "__main__":
    main()
