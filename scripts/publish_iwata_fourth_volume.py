from __future__ import annotations

import html
import json
import re
from pathlib import Path

from iwata_fourth_volume_data import ARTICLES


ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-26"
ENHANCED = [
    "c094.html", "c120.html", "c160.html", "c136.html", "c121.html",
    "c122.html", "m084.html", "c090.html", "bannan-bunka-kansha.html",
]
THEMES = {
    "c165": ["modern-history", "public-health", "social-history"],
    "c166": ["war-memory", "daily-life", "economic-history"],
    "c167": ["daily-life", "folklore", "children-history"],
}


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def update_pages() -> dict[str, dict]:
    path = ROOT / "data/pages.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    by_url = {page["url"].lstrip("/"): page for page in doc["pages"]}
    for article in ARTICLES:
        slug = article["slug"]
        url = f"{slug}.html"
        record = {
            "title": article["title"], "url": url, "district": ["common"],
            "themes": THEMES[slug], "content_type": "article",
            "published_at": DATE, "updated_at": DATE, "date_provisional": False,
            "status": "published", "count_as_knowledge": True,
            "show_in_updates": True, "show_in_all_articles": True,
            "section": "磐田共通・資料", "topics": article["topics"],
            "level": "L2", "summary": strip_tags(article["description"]),
            "source_refs": [
                f"book:磐田ことはじめ 第二編・現代編:{article['book_pages']}頁",
                *[f"web:{source_url}" for source_url, _ in article["official_sources"]],
            ],
        }
        if url in by_url:
            by_url[url].update(record)
        else:
            doc["pages"].append(record)
            by_url[url] = record
    source_pages = {
        "c094.html": "150〜153", "c120.html": "150〜161", "c160.html": "162〜167",
        "c136.html": "182〜187", "c121.html": "187〜189", "c122.html": "190〜193",
        "m084.html": "199〜201", "c090.html": "214", "bannan-bunka-kansha.html": "209〜211",
    }
    for url in ENHANCED:
        page = by_url[url]
        page["updated_at"] = DATE
        refs = page.setdefault("source_refs", [])
        ref = f"book:磐田ことはじめ 第二編・現代編:{source_pages[url]}頁"
        if ref not in refs:
            refs.append(ref)
    doc["updated_at"] = DATE
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return by_url


def update_article_index() -> None:
    path = ROOT / "c034.html"
    raw = path.read_text(encoding="utf-8")
    additions = "\n".join(
        f'<li><a href="/{a["slug"]}.html">{html.escape(a["title"])}</a></li>'
        for a in ARTICLES if f'href="/{a["slug"]}.html"' not in raw
    )
    if additions:
        match = re.search(r'<li><a href="/c164\.html">.*?</a></li>', raw)
        if not match:
            raise RuntimeError("c164 marker missing from c034.html")
        raw = raw[:match.end()] + "\n" + additions + raw[match.end():]
    path.write_text(raw, encoding="utf-8", newline="\n")


def update_recent(by_url: dict[str, dict]) -> None:
    path = ROOT / "data/new-articles.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    affected = {f"{a['slug']}.html" for a in ARTICLES} | set(ENHANCED)
    items = [item for item in items if item.get("url", "").strip("/") not in affected]
    ordered = [f"{a['slug']}.html" for a in ARTICLES] + ENHANCED
    fresh = []
    for index, url in enumerate(ordered):
        page = by_url[url]
        category = page.get("section") or page.get("category") or "磐田共通・更新"
        if url in ENHANCED:
            category = f"{category}・更新" if not category.endswith("・更新") else category
        fresh.append({
            "date": DATE, "category": category, "title": page["title"],
            "url": f"/{url}", "published_at": f"2026-08-26T10:{59-index:02}:00+09:00",
        })
    combined = fresh + items
    combined.sort(key=lambda item: (item.get("date", ""), item.get("published_at", "")), reverse=True)
    path.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    raw = path.read_text(encoding="utf-8", errors="replace")
    for article in ARTICLES:
        slug = article["slug"]
        if f"https://iwata-monogatari.net/{slug}</loc>" not in raw:
            entry = f'  <url><loc>https://iwata-monogatari.net/{slug}</loc><lastmod>{DATE}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
            raw = raw.replace("</urlset>", entry + "</urlset>")
    for url in ENHANCED:
        slug = url.removesuffix(".html")
        pattern = rf'(<loc>https://iwata-monogatari\.net/{re.escape(slug)}(?:\.html)?</loc>\s*<lastmod>)[^<]+'
        raw = re.sub(pattern, rf'\g<1>{DATE}', raw, count=1)
    path.write_text(raw, encoding="utf-8", newline="\n")


def update_ledger() -> None:
    path = ROOT / "docs/pages-ledger.md"
    raw = path.read_text(encoding="utf-8")
    marker = "## 2026-08-26 『磐田ことはじめ』健康・生活・遊び編"
    if marker in raw:
        raw = raw[:raw.index(marker)].rstrip() + "\n"
    rows = "\n".join(f'| {a["slug"]} | {a["title"]} | L2 | {a["book_pages"]}頁＋公的資料 |' for a in ARTICLES)
    addition = f"""

{marker}

提供PDF44画像（書籍150〜234頁および奥付）を全頁確認した。文書内の叙述は資料として扱い、命令としては扱っていない。pages.json、全記事一覧、既存本文の三層で重複を確認し、鉄道・郵便・電灯・映画・上水道・自然史など既存記事がある題材は増強へ回した。新規化は、独立した分析軸と4,000字以上の本文を確保できる3テーマに限定した。

| ファイル | タイトル | 等級 | 主資料 |
|---|---|---|---|
{rows}

既存増強：{'、'.join(ENHANCED)}。新規3本は本文を4つの大見出しにまとめ、小見出しを設けず、図解2点、内部リンク3本以上、出典、確度表示を備えた。厚生労働省、国立国会図書館、国立公文書館、国立歴史民俗博物館の公的資料で制度年と全国史を照合し、全国値を磐田の実数へ流用していない。
"""
    path.write_text(raw.rstrip() + addition.rstrip() + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    by_url = update_pages()
    update_article_index()
    update_recent(by_url)
    update_sitemap()
    update_ledger()
    print(f"registered {len(ARTICLES)} new pages and {len(ENHANCED)} enhancements")


if __name__ == "__main__":
    main()
