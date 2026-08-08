"""記事ページに Article / BreadcrumbList 構造化データを注入する。

SEO改修指示書（docs/seo-expansion-directive-20260808.md）§17・§18 の実装。

- 出典は data/pages.json（title / summary / url / district / published_at / updated_at / parent）。
  HTMLを解析して情報を作らない ── 台帳を単一の真実とする。
- 既に Article 系 LD を持つページには手を触れない（手書きの記述を尊重する）。
- BreadcrumbList も同様に、既にあるページはそのまま。
- 挿入位置は </head> の直前。マーカーコメントを付けるので再実行しても二重挿入しない。
- @id はページ自身が宣言している canonical に合わせる（台帳URLから組み立てない）。
  canonical が自分以外を指すページ（＝自らを正規URLでないと宣言しているページ）は、
  Article を名乗らせるべきでないので丸ごとスキップし、末尾に一覧を出す。

使い方:
    python tools/inject-structured-data.py --dry-run   # 対象件数と例を表示
    python tools/inject-structured-data.py             # 実際に書き込む
"""

import argparse
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://iwata-monogatari.net"
DEFAULT_IMAGE = f"{ORIGIN}/img/ogp.jpg"
MARKER = "<!-- structured-data:auto -->"

PUBLISHER = {
    "@type": "Organization",
    "name": "磐田物語",
    "url": f"{ORIGIN}/",
    "logo": {"@type": "ImageObject", "url": DEFAULT_IMAGE},
}

ARTICLE_LD_RE = re.compile(r'"@type"\s*:\s*"(Article|NewsArticle|BlogPosting)"')


def load_ledger():
    data = json.loads((ROOT / "data" / "pages.json").read_text(encoding="utf-8"))
    districts = {d["district_id"]: d for d in data["districts"]}
    pages = {p["url"].lstrip("/"): p for p in data["pages"]}
    return data, districts, pages


def resolve_path(url):
    rel = url.lstrip("/")
    if not rel:
        return None
    candidate = ROOT / rel
    if candidate.is_dir():
        candidate = candidate / "index.html"
    if candidate.suffix != ".html":
        candidate = ROOT / (rel.rstrip("/") + "/index.html")
    return candidate if candidate.is_file() else None


def canonical_url(url):
    return f"{ORIGIN}/{url.lstrip('/')}"


def iso_date(value):
    """台帳の published_at は 'YYYY-MM-DD' と ISO 日時が混在する。日付部分だけ取る。"""
    if not value:
        return None
    return str(value)[:10]


CANONICAL_RE = re.compile(r'rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', re.I)


def declared_canonical(html):
    m = CANONICAL_RE.search(html)
    if not m:
        m = re.search(r'href=["\']([^"\']+)["\'][^>]*rel=["\']canonical', html, re.I)
    return m.group(1).strip() if m else None


def same_url(a, b):
    """末尾スラッシュと .html の有無だけの違いは同一とみなす。

    Cloudflare Pages は /x.html を /x へ308するので、台帳の 'x.html' と
    canonical の '/x' は同じページを指す。
    """
    def norm(u):
        u = (u or "").rstrip("/")
        return u[:-5] if u.endswith(".html") else u
    return norm(a) == norm(b)


def build_article_ld(page, self_id):
    published = iso_date(page.get("published_at"))
    modified = iso_date(page.get("updated_at")) or published
    ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": page["title"],
        "description": page.get("summary", ""),
        "image": DEFAULT_IMAGE,
        "inLanguage": "ja",
        "author": {"@type": "Organization", "name": "磐田物語", "url": f"{ORIGIN}/"},
        "publisher": PUBLISHER,
        "isPartOf": {"@type": "WebSite", "name": "磐田物語", "url": f"{ORIGIN}/"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": self_id},
    }
    if published:
        ld["datePublished"] = published
    if modified:
        ld["dateModified"] = modified
    if page.get("section"):
        ld["articleSection"] = page["section"]
    topics = page.get("topics") or []
    if topics:
        ld["keywords"] = ", ".join(topics)
    return ld


def build_breadcrumb_ld(page, districts, pages, self_id):
    """磐田物語 ＞ ○○地区 ＞（親記事）＞ この記事。

    親記事（parent）は特集の入口ページなど。台帳にある場合だけ1階層挟む。
    """
    items = [{"@type": "ListItem", "position": 1, "name": "磐田物語", "item": f"{ORIGIN}/"}]
    pos = 2

    district_ids = page.get("district") or []
    if len(district_ids) == 1 and district_ids[0] in districts:
        d = districts[district_ids[0]]
        items.append(
            {
                "@type": "ListItem",
                "position": pos,
                "name": d["name"],
                "item": canonical_url(d["page"]),
            }
        )
        pos += 1

    parent_url = page.get("parent")
    if parent_url:
        parent = pages.get(str(parent_url).lstrip("/"))
        if parent and parent["url"].lstrip("/") != page["url"].lstrip("/"):
            items.append(
                {
                    "@type": "ListItem",
                    "position": pos,
                    "name": parent["title"],
                    "item": canonical_url(parent["url"]),
                }
            )
            pos += 1

    items.append(
        {
            "@type": "ListItem",
            "position": pos,
            "name": page["title"],
            "item": self_id,
        }
    )
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def render_block(ld_objects):
    parts = [MARKER]
    for ld in ld_objects:
        body = json.dumps(ld, ensure_ascii=False, indent=2)
        parts.append(f'<script type="application/ld+json">\n{body}\n</script>')
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    _, districts, pages = load_ledger()

    written = 0
    skipped_missing = []
    skipped_nohead = []
    skipped_existing = 0
    skipped_noindex = 0
    skipped_foreign_canonical = []
    skipped_no_canonical = []
    added_article = 0
    added_breadcrumb = 0

    for url, page in pages.items():
        if page.get("status") != "published":
            continue
        path = resolve_path(page["url"])
        if path is None:
            skipped_missing.append(page["url"])
            continue

        html = io.open(path, encoding="utf-8").read()

        if MARKER in html:
            skipped_existing += 1
            continue
        if re.search(r'name=["\']robots["\'][^>]*noindex', html):
            skipped_noindex += 1
            continue

        canon = declared_canonical(html)
        if not canon:
            skipped_no_canonical.append(page["url"])
            continue
        if not same_url(canon, canonical_url(page["url"])):
            # 自らを正規URLでないと宣言しているページ。Article を名乗らせない。
            skipped_foreign_canonical.append((page["url"], canon))
            continue
        self_id = canon

        blocks = []
        if not ARTICLE_LD_RE.search(html):
            blocks.append(build_article_ld(page, self_id))
            added_article += 1
        if "BreadcrumbList" not in html:
            blocks.append(build_breadcrumb_ld(page, districts, pages, self_id))
            added_breadcrumb += 1
        if not blocks:
            skipped_existing += 1
            continue

        m = re.search(r"</head>", html, re.I)
        if not m:
            skipped_nohead.append(page["url"])
            continue

        new_html = html[: m.start()] + render_block(blocks) + html[m.start() :]

        if not args.dry_run:
            io.open(path, "w", encoding="utf-8", newline="\n").write(new_html)
        written += 1
        if args.limit and written >= args.limit:
            break

    print(f"{'[dry-run] ' if args.dry_run else ''}pages updated: {written}")
    print(f"  Article LD added:        {added_article}")
    print(f"  BreadcrumbList LD added: {added_breadcrumb}")
    print(f"  skipped (already had):   {skipped_existing}")
    print(f"  skipped (noindex):       {skipped_noindex}")
    print(f"  skipped (file missing):  {len(skipped_missing)} {skipped_missing[:10]}")
    print(f"  skipped (no </head>):    {len(skipped_nohead)} {skipped_nohead[:10]}")
    print(f"  skipped (canonical欠落): {len(skipped_no_canonical)} {skipped_no_canonical[:10]}")
    print(f"  skipped (canonicalが他ページを指す): {len(skipped_foreign_canonical)}")
    for url, canon in skipped_foreign_canonical:
        print(f"      {url} -> {canon}")


if __name__ == "__main__":
    main()
