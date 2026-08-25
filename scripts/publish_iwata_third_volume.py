from __future__ import annotations

import html
import json
import re
from pathlib import Path

from iwata_third_volume_data import ARTICLES


ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-25"
ENHANCED = [
    "c075.html", "c083.html", "c118.html", "c123.html", "c144.html",
    "c150.html", "h004.html", "h008.html", "n089.html", "u053.html",
]
THEMES = {
    "c155": ["war-memory", "military-history", "peace"],
    "c156": ["postwar", "administration", "occupation-history"],
    "c157": ["postwar", "social-history", "welfare"],
    "c158": ["war-memory", "migration", "colonial-history"],
    "c159": ["modern-history", "social-history", "economic-history"],
    "c160": ["modern-history", "welfare", "social-history"],
    "c161": ["postwar", "agriculture", "land-history"],
    "c162": ["agriculture", "economic-history", "cooperative-history"],
    "c163": ["postwar", "economic-history", "financial-history"],
    "c164": ["postwar", "labor-history", "industry"],
}


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def update_pages() -> None:
    path = ROOT / "data/pages.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    by_url = {page["url"].lstrip("/"): page for page in doc["pages"]}
    for article in ARTICLES:
        slug = article["slug"]
        url = f"{slug}.html"
        source_refs = [
            f"book:磐田ことはじめ 第二編・現代編:{article['book_pages']}頁",
            *[f"web:{source_url}" for source_url, _ in article.get("official_sources", [])],
        ]
        record = {
            "title": article["title"], "url": url, "district": ["common"],
            "themes": THEMES[slug], "content_type": "article",
            "published_at": DATE, "updated_at": DATE, "date_provisional": False,
            "status": "published", "count_as_knowledge": True,
            "show_in_updates": True, "show_in_all_articles": True,
            "section": "磐田共通・資料", "topics": article["topics"],
            "level": "L2", "summary": strip_tags(article["description"]),
            "source_refs": source_refs,
        }
        if url in by_url:
            by_url[url].update(record)
        else:
            doc["pages"].append(record)
            by_url[url] = record
    for url in ENHANCED:
        if url not in by_url:
            raise RuntimeError(f"enhancement target missing from pages.json: {url}")
        by_url[url]["updated_at"] = DATE
        refs = by_url[url].setdefault("source_refs", [])
        source = "book:磐田ことはじめ 第二編・現代編:89〜149頁"
        if source not in refs:
            refs.append(source)
    doc["updated_at"] = DATE
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_article_index() -> None:
    path = ROOT / "c034.html"
    raw = path.read_text(encoding="utf-8")
    additions = "\n".join(
        f'<li><a href="/{a["slug"]}.html">{html.escape(a["title"])}</a></li>'
        for a in ARTICLES if f'href="/{a["slug"]}.html"' not in raw
    )
    if additions:
        match = re.search(r'<li><a href="/c154\.html">.*?</a></li>', raw)
        if not match:
            raise RuntimeError("c154 marker missing from c034.html")
        raw = raw[:match.end()] + "\n" + additions + raw[match.end():]
        path.write_text(raw, encoding="utf-8", newline="\n")


def update_recent() -> None:
    path = ROOT / "data/new-articles.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    slugs = {article["slug"] for article in ARTICLES}
    items = [
        item for item in items
        if item.get("url", "").strip("/").removesuffix(".html") not in slugs
    ]
    fresh = []
    for index, article in enumerate(ARTICLES):
        fresh.append({
            "date": DATE,
            "category": article["category"],
            "title": article["title"],
            "url": f'/{article["slug"]}.html',
            "published_at": f"2026-08-25T10:{59-index:02}:00+09:00",
        })
    combined = fresh + items
    combined.sort(key=lambda item: (item.get("date", ""), item.get("published_at", "")), reverse=True)
    path.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    raw = path.read_text(encoding="utf-8", errors="replace")
    for article in ARTICLES:
        slug = article["slug"]
        pattern = rf'(<url>\s*<loc>https://iwata-monogatari\.net/{slug}(?:\.html)?</loc>\s*<lastmod>)[^<]+(</lastmod>)'
        if re.search(pattern, raw):
            raw = re.sub(pattern, rf'\g<1>{DATE}\g<2>', raw, count=1)
        else:
            entry = f'  <url><loc>https://iwata-monogatari.net/{slug}</loc><lastmod>{DATE}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
            raw = raw.replace("</urlset>", entry + "</urlset>")
    path.write_text(raw, encoding="utf-8", newline="\n")


def update_ledger() -> None:
    path = ROOT / "docs/pages-ledger.md"
    raw = path.read_text(encoding="utf-8")
    marker = "## 2026-08-25 『磐田ことはじめ』戦争・農業・商工業編"
    if marker in raw:
        raw = raw[: raw.index(marker)].rstrip() + "\n"
    rows = "\n".join(
        f'| {a["slug"]} | {a["title"]} | L2 | {a["book_pages"]}頁＋公的ウェブ資料 |'
        for a in ARTICLES
    )
    enhanced = "、".join(ENHANCED)
    addition = f"""

{marker}

提供PDF31画像（書籍89〜149頁）を全頁確認。PDFの節順を転記せず、既存ページとの3層重複判定（pages.json・c034全記事一覧・本文検索）後、独立性のある10テーマだけを新設した。磐田市・静岡県・国立国会図書館・アジア歴史資料センター・厚生労働省・農林水産省・日本銀行の公的資料で制度年・名称・全国値を照合し、全国値を磐田の実数として使わなかった。

| ファイル | タイトル | 等級 | 主資料 |
|---|---|---|---|
{rows}

既存増強：{enhanced}。中部129部隊の名称、大池量水標石の訴訟・判決年、新円切替とドッジ・ラインの区別、救護法と生活保護法の制度差などを公的資料で再確認した。新規10本は本文4,000字以上、図解2点、年表、内部リンク3本以上、確度表示、ウェブ出典を備える。
"""
    path.write_text(raw.rstrip() + addition.rstrip() + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    update_pages()
    update_article_index()
    update_recent()
    update_sitemap()
    update_ledger()
    print(f"registered {len(ARTICLES)} new pages and {len(ENHANCED)} enhancements")


if __name__ == "__main__":
    main()
