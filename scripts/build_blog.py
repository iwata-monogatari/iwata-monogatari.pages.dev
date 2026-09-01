#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/blog-posts.json から /blog/index.html を生成し、記事の体裁を機械検査する。

記事の実体（blog/<slug>/index.html）は手書き（または自動生成）である。
本スクリプトは次の3つを担当する。

  1. 台帳（data/blog-posts.json）と実ファイルの突き合わせ
  2. 品質ゲートの機械チェック
  3. 一覧ページ /blog/index.html の生成

--------------------------------------------------------------------
なぜ品質ゲートがこの形なのか（重要）
--------------------------------------------------------------------
磐田物語は500ページを超える郷土史データベースであり、正確さがサイトの価値
そのものである。一方このブログは毎日自動生成される運用に載る。自動生成が
「資料の裏付けのない新しい史実」を書き足し始めると、サイト全体の信頼を
損なう。そこで、ブログ記事が主張できる範囲を機械的に狭める。

  * 既存ページへの内部リンクを2本以上必須にする（G5）
    → 記事の骨格を「既に書かれていること」に縛りつける。既存ページを
      指せない話題は、そもそもこのブログの守備範囲ではない。
  * 年号を含む段落には必ずリンクを要求する（G10）
    → 「〇〇年に△△だった」という新規の史実主張を、出典または既存ページ
      への参照なしには書けなくする。
  * 外部リンクを公的機関等の許可ドメインに限定する（G7）
    → 素性の知れない外部ページを根拠に仕立てられないようにする。
  * 断定・新発見を主張する語を禁止する（G9）
  * 既存1093ページとのタイトル重複を検出する（G11）

機械では「本文の内容が本当に既存ページの範囲内か」までは判定できない。
最終判断は執筆者・査読者が行う。詳細な編集方針は docs/BLOG-SKILL.md。

使い方:
    python scripts/build_blog.py            # 検査して /blog/index.html を生成
    python scripts/build_blog.py --check    # 検査のみ（ファイルを書かない）
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "blog-posts.json"
PAGES_JSON = ROOT / "data" / "pages.json"
BLOG_DIR = ROOT / "blog"

SITE = "https://iwata-monogatari.net"
SITE_NAME = "磐田物語"

MIN_BODY_CHARS = 1200
MAX_BODY_CHARS = 9000
MIN_INTERNAL_LEDGER_LINKS = 2
MIN_SOURCE_ITEMS = 2

KIND_LABEL = {
    "reading": "既存ページの読み解き",
    "now-and-then": "いまの風景と記録",
    "how-to-research": "調べ方",
    "guide": "サイト内の道案内",
}

# 外部リンクとして認めるドメイン（公的機関・公的アーカイブ等）。
# ここに無いドメインを根拠として引くことはできない。
ALLOWED_EXTERNAL_HOST_SUFFIXES = (
    "iwata-monogatari.net",
    ".go.jp",
    ".lg.jp",
    ".ac.jp",
    "city.iwata.shizuoka.jp",
    "pref.shizuoka.jp",
    "lega-shizu.com",  # 静岡県「しずおか無形民俗文化財ナビ」
    "rekihaku.ac.jp",
    "ndl.go.jp",
    "bunka.go.jp",
)

# 「資料の裏付けなしに新しい史実を主張する」典型的な言い回し。
BANNED_PHRASES = (
    "新事実",
    "新発見",
    "初めて明らかに",
    "初めて判明",
    "独自調査により",
    "独自調査で判明",
    "断定できる",
    "間違いなく",
    "に違いない",
    "確実である",
    "疑いようがない",
    "定説を覆す",
    "真実はこうだ",
)

# 年（西暦・元号）を含む段落は出典リンクを必須にするための検出パターン。
YEAR_PATTERN = re.compile(
    r"(?:\d{3,4}\s*年)|(?:(?:明治|大正|昭和|平成|令和)\s*(?:\d+|元)\s*年)"
)


# --------------------------------------------------------------------
# 共通ユーティリティ
# --------------------------------------------------------------------
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"<!--.*?-->", "", fragment, flags=re.S)
    fragment = re.sub(
        r"<(script|style)\b.*?</\1>", "", fragment, flags=re.S | re.I
    )
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def visible_chars(fragment: str) -> int:
    return len(re.sub(r"\s+", "", strip_tags(fragment)))


def site_ledger_urls() -> set[str]:
    """data/pages.json に登録された「既存ページ」のURL集合（正規化済み）。"""
    data = load_json(PAGES_JSON)
    urls = set()
    for page in data.get("pages", []):
        if page.get("status") != "published":
            continue
        urls.add(normalize_url(page.get("url", "")))
    for district in data.get("districts", []):
        urls.add(normalize_url(district.get("page", "")))
    urls.discard("")
    return urls


def site_ledger_titles() -> dict[str, str]:
    data = load_json(PAGES_JSON)
    return {
        str(p.get("title", "")).strip(): normalize_url(p.get("url", ""))
        for p in data.get("pages", [])
        if str(p.get("title", "")).strip()
    }


def normalize_url(url: str) -> str:
    """/c007 と /c007.html と c007.html を同一視するためのキー。"""
    u = str(url or "").strip()
    if not u:
        return ""
    u = u.split("#", 1)[0].split("?", 1)[0]
    if not u.startswith("/"):
        u = "/" + u
    if u.endswith(".html"):
        u = u[: -len(".html")]
    if len(u) > 1 and u.endswith("/"):
        u = u[:-1]
    return u


def resolve_local_file(url: str) -> Path | None:
    """サイト内URLがリポジトリ上の実ファイルに解決できるか。"""
    rel = normalize_url(url).lstrip("/")
    if not rel:
        return ROOT / "index.html"
    for candidate in (
        ROOT / rel,
        ROOT / f"{rel}.html",
        ROOT / rel / "index.html",
    ):
        if candidate.is_file():
            return candidate
    return None


def post_body(src: str) -> str | None:
    m = re.search(r'<div class="post-body">(.*?)</div>\s*<!-- /post-body -->', src, re.S)
    return m.group(1) if m else None


def links_in(fragment: str) -> list[str]:
    return re.findall(r'<a\b[^>]*\bhref="([^"]+)"', fragment)


def external_host(href: str) -> str | None:
    m = re.match(r"https?://([^/]+)", href, re.I)
    return m.group(1).lower() if m else None


def host_allowed(host: str) -> bool:
    return any(
        host == suffix.lstrip(".") or host.endswith(suffix)
        for suffix in ALLOWED_EXTERNAL_HOST_SUFFIXES
    )


# --------------------------------------------------------------------
# 品質ゲート
# --------------------------------------------------------------------
def audit(posts: list[dict]) -> list[tuple[str, str]]:
    problems: list[tuple[str, str]] = []
    ledger_urls = site_ledger_urls()
    existing_titles = site_ledger_titles()
    seen_titles: dict[str, str] = {}
    seen_slugs: set[str] = set()

    for post in posts:
        slug = str(post.get("slug", "")).strip()
        add = lambda why: problems.append((slug or "(slug未設定)", why))  # noqa: E731

        # G0: 台帳そのものの妥当性
        if not slug:
            add("台帳に slug が無い")
            continue
        if slug in seen_slugs:
            add("台帳内で slug が重複している")
        seen_slugs.add(slug)
        for field in ("date", "title", "description", "kind"):
            if not str(post.get(field, "")).strip():
                add(f"台帳の必須項目『{field}』が空")
        if post.get("kind") and post["kind"] not in KIND_LABEL:
            add(f"kind『{post['kind']}』は未定義（{'/'.join(KIND_LABEL)}）")

        index_path = BLOG_DIR / slug / "index.html"
        if not index_path.is_file():
            add(f"記事本体が無い: blog/{slug}/index.html")
            continue
        src = index_path.read_text(encoding="utf-8")

        # G1: 本文コンテナ
        body = post_body(src)
        if body is None:
            add('本文コンテナ <div class="post-body">…<!-- /post-body --> が無い')
            continue

        # G2: 本文分量
        count = visible_chars(body)
        if count < MIN_BODY_CHARS:
            add(f"本文が {count} 文字。最低 {MIN_BODY_CHARS} 文字に未達")
        if count > MAX_BODY_CHARS:
            add(f"本文が {count} 文字。上限 {MAX_BODY_CHARS} 文字を超過")

        # G3/G4/G5: リンクの実在確認と、既存ページへの内部リンク本数
        body_links = links_in(body)
        source_block = re.search(
            r'<section class="post-sources">(.*?)</section>', src, re.S
        )
        all_links = body_links + links_in(source_block.group(1) if source_block else "")

        internal_ledger_hits: set[str] = set()
        for href in all_links:
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            host = external_host(href)
            if host:
                # G7: 外部リンクは許可ドメインのみ
                if not host_allowed(host):
                    add(f"許可されていない外部ドメインへのリンク: {host}")
                continue
            if not href.startswith("/"):
                add(f"相対リンクは使わない（サイト絶対パスにする）: {href}")
                continue
            key = normalize_url(href)
            if key.startswith("/blog"):
                continue  # ブログ内リンクは「既存ページ」に数えない
            # G3: デッドリンク禁止
            if resolve_local_file(href) is None:
                add(f"リンク先がリポジトリに実在しない: {href}")
                continue
            # G5: 台帳に載っている既存ページか
            if key in ledger_urls:
                internal_ledger_hits.add(key)

        if len(internal_ledger_hits) < MIN_INTERNAL_LEDGER_LINKS:
            add(
                "サイト内の既存ページへのリンクが "
                f"{len(internal_ledger_hits)} 本。最低 {MIN_INTERNAL_LEDGER_LINKS} 本必要"
                "（新規の史実主張を防ぐための必須ゲート）"
            )

        # G6: 台帳の internal_links と本文の実態が一致しているか
        declared = {normalize_url(u) for u in post.get("internal_links", [])}
        if declared and not declared <= (internal_ledger_hits | {normalize_url(u) for u in all_links}):
            missing = sorted(declared - internal_ledger_hits)
            add("台帳の internal_links が本文に現れない: " + ", ".join(missing))

        # G8: 出典セクション
        if not source_block:
            add('出典セクション <section class="post-sources"> が無い')
        else:
            items = re.findall(r"<li\b", source_block.group(1))
            if len(items) < MIN_SOURCE_ITEMS:
                add(f"出典が {len(items)} 件。最低 {MIN_SOURCE_ITEMS} 件必要")

        # G9: 断定・新発見を主張する語の禁止
        body_text = strip_tags(body)
        for phrase in BANNED_PHRASES:
            if phrase in body_text:
                add(f"断定・新規主張につながる禁止表現『{phrase}』が本文にある")

        # G10: 年号を含む段落には必ずリンク（出典 or 既存ページ）を伴わせる
        for para in re.findall(r"<p\b[^>]*>(.*?)</p>", body, re.S):
            if YEAR_PATTERN.search(strip_tags(para)) and not links_in(para):
                snippet = re.sub(r"\s+", "", strip_tags(para))[:36]
                add(
                    "年号を含む段落に出典リンクが無い（新しい史実の主張になりうる）: "
                    f"「{snippet}…」"
                )

        # G11: スコープ宣言（このブログが何を書かないかの明示）
        if 'class="post-scope"' not in src:
            add('本稿の範囲を示す <p class="post-scope"> が無い')

        # G12: 著者表記
        if 'class="post-author"' not in src:
            add('著者表記 <span class="post-author"> が無い')

        # G13: canonical / og:url が /blog/<slug>/ に一致
        expected = f"{SITE}/blog/{slug}/"
        for label, pattern in (
            ("canonical", r'<link rel="canonical" href="([^"]+)"'),
            ("og:url", r'<meta property="og:url" content="([^"]+)"'),
        ):
            m = re.search(pattern, src)
            if not m:
                add(f"{label} が無い")
            elif m.group(1) != expected:
                add(f"{label} が {m.group(1)}。{expected} であるべき")

        # G14: 公開日が台帳と一致
        if post.get("date") and post["date"] not in src:
            add(f"本文中に公開日 {post['date']} が現れない（台帳と不一致の疑い）")

        # G15: タイトル重複（ブログ内 / 既存1093ページ）
        title = str(post.get("title", "")).strip()
        if title:
            if title in seen_titles:
                add(f"タイトルが {seen_titles[title]} と重複")
            seen_titles[title] = slug
            if title in existing_titles:
                add(f"タイトルが既存ページ {existing_titles[title]} と重複")

        # G16: 自動発見への混入防止（新着フィードを汚さない）
        for meta_name in ("iwata:published", "iwata:new-article", "article:published_time"):
            if f'"{meta_name}"' in src or f"'{meta_name}'" in src:
                add(
                    f"meta {meta_name} を持たせてはいけない"
                    "（sync_new_articles.py の新着自動収集に混入する）"
                )

    return problems


# --------------------------------------------------------------------
# 一覧ページ生成
# --------------------------------------------------------------------
LEAD = (
    "磐田物語の本編は、資料にあたって書いた郷土史の記事です。"
    "このブログはその周辺を書きます。すでに公開しているページの読み解き、"
    "いまの風景と記録の対比、資料の探し方。"
    "新しい史実をここで主張することはありません。"
)


def build_index(posts: list[dict]) -> str:
    items = []
    for post in sorted(posts, key=lambda p: (p["date"], p["slug"]), reverse=True):
        label = KIND_LABEL.get(post.get("kind", ""), "")
        badge = (
            f'<span class="post-kind">{html.escape(label)}</span>' if label else ""
        )
        items.append(
            '<li class="post-item"><a class="post-item-link" href="/blog/{slug}/">'
            '<span class="post-item-meta"><time datetime="{date}">{shown}</time>{badge}</span>'
            '<span class="post-item-title">{title}</span>'
            '<span class="post-item-desc">{desc}</span>'
            "</a></li>".format(
                slug=post["slug"],
                date=post["date"],
                shown=post["date"].replace("-", "."),
                badge=badge,
                title=html.escape(post["title"]),
                desc=html.escape(post["description"]),
            )
        )

    body = (
        '<ul class="post-list">%s</ul>' % "".join(items)
        if items
        else '<p class="note">記事はまだありません。</p>'
    )
    title = "ブログ｜磐田物語"
    desc = (
        "磐田物語のブログ。既存ページの読み解き、いまの磐田の風景と記録の対比、"
        "郷土史の調べ方を書いています。"
    )
    breadcrumb_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "ブログ", "item": SITE + "/blog/"},
            ],
        },
        ensure_ascii=False,
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/blog/">
<meta property="og:locale" content="ja_JP">
<link rel="canonical" href="{SITE}/blog/">
<link rel="alternate" type="application/atom+xml" title="磐田物語ブログ" href="{SITE}/feed.xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/favicon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site-header.css">
<link rel="stylesheet" href="/assets/css/iwata-area-color.css">
<link rel="stylesheet" href="/assets/css/blog.css">
<script type="application/ld+json">{breadcrumb_ld}</script>
</head>
<body>
<header class="gh-site"></header>
<main class="blog-main">
  <div class="crumb"><a href="/">磐田物語</a> ／ ブログ</div>
  <h1>ブログ</h1>
  <div class="lead">{LEAD}</div>
  <div class="note">
    このブログは既存ページへの案内役です。史実そのものは本編の記事に書いてあります。
    まとまった記録を読みたい方は<a href="/c034">全記事一覧</a>、
    テーマから探す方は<a href="/c137">テーマから調べる</a>をご覧ください。
  </div>
{body}
</main>
<section class="article-policy" data-common></section>
<footer class="im-foot"></footer>
<script defer src="https://fujigaoka-analytics-worker.hiroyukio0122.workers.dev/tracker.js" data-site="iwata-monogatari" data-fujigaoka-analytics="true"></script>
</body></html>
"""


SITEMAP = ROOT / "sitemap.xml"
SITEMAP_START = "  <!-- blog:start scripts/build_blog.py が自動生成する区画。手で編集しない。 -->"
SITEMAP_END = "  <!-- blog:end -->"
FEED = ROOT / "feed.xml"


def build_sitemap_block(posts: list[dict]) -> str:
    """/blog/ 配下のURLだけを sitemap.xml のマーカー区画へ冪等に書き出す。

    毎日の自動生成で5,000行超の sitemap.xml を手編集させないための処置。
    マーカーの外側には一切触れない。
    """
    newest = max((p["date"] for p in posts), default="")
    lines = [SITEMAP_START]
    lines.append(
        f'  <url><loc>{SITE}/blog/</loc><lastmod>{newest}</lastmod>'
        "<changefreq>daily</changefreq><priority>0.6</priority></url>"
    )
    for post in sorted(posts, key=lambda p: (p["date"], p["slug"])):
        lines.append(
            f'  <url><loc>{SITE}/blog/{post["slug"]}/</loc>'
            f'<lastmod>{post["date"]}</lastmod>'
            "<changefreq>monthly</changefreq><priority>0.5</priority></url>"
        )
    lines.append(SITEMAP_END)
    return "\n".join(lines)


def update_sitemap(posts: list[dict]) -> str:
    text = SITEMAP.read_text(encoding="utf-8")
    block = build_sitemap_block(posts)
    pattern = re.compile(
        re.escape(SITEMAP_START) + r".*?" + re.escape(SITEMAP_END), re.S
    )
    if pattern.search(text):
        updated = pattern.sub(lambda _: block, text)
    else:
        updated = text.replace("</urlset>", block + "\n</urlset>")
    if updated != text:
        SITEMAP.write_text(updated, encoding="utf-8", newline="")
        return "sitemap.xml: 更新"
    return "sitemap.xml: 変更なし"


def build_feed(posts: list[dict]) -> str:
    """ブログ台帳からAtomフィードを生成する。"""
    ordered = sorted(posts, key=lambda p: (p["date"], p["slug"]), reverse=True)
    newest = ordered[0]["date"] if ordered else "1970-01-01"
    entries = []
    for post in ordered:
        url = f'{SITE}/blog/{post["slug"]}/'
        title = html.escape(post["title"])
        summary = html.escape(post["description"])
        stamp = f'{post["date"]}T00:00:00+09:00'
        entries.append(
            "  <entry>\n"
            f"    <title>{title}</title>\n"
            f'    <link href="{url}"/>\n'
            f"    <id>{url}</id>\n"
            f"    <published>{stamp}</published>\n"
            f"    <updated>{stamp}</updated>\n"
            f"    <summary>{summary}</summary>\n"
            "  </entry>"
        )
    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="ja">\n'
        '  <title>磐田物語ブログ</title>\n'
        f'  <link href="{SITE}/blog/"/>\n'
        f'  <link href="{SITE}/feed.xml" rel="self" type="application/atom+xml"/>\n'
        f'  <id>{SITE}/blog/</id>\n'
        f'  <updated>{newest}T00:00:00+09:00</updated>\n'
        '  <author><name>大石浩之</name></author>\n'
        f'{body}\n'
        '</feed>\n'
    )


def update_feed(posts: list[dict]) -> str:
    updated = build_feed(posts)
    previous = FEED.read_text(encoding="utf-8") if FEED.exists() else ""
    if updated != previous:
        FEED.write_text(updated, encoding="utf-8", newline="")
        return "feed.xml: 更新"
    return "feed.xml: 変更なし"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="検査のみ（書き込まない）")
    args = parser.parse_args()

    posts = load_json(LEDGER)["posts"]
    problems = audit(posts)
    if problems:
        print("品質ゲート未達 %d 件:" % len(problems))
        for slug, why in problems:
            print("  %s: %s" % (slug, why))
        print("→ 一覧は生成しません。記事を直してから再実行してください。")
        return 1

    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    out = BLOG_DIR / "index.html"
    sitemap_note = "sitemap.xml: 未更新（--check）"
    feed_note = "feed.xml: 未更新（--check）"
    if not args.check:
        out.write_text(build_index(posts), encoding="utf-8", newline="")
        sitemap_note = update_sitemap(posts)
        feed_note = update_feed(posts)

    print(
        "記事 %d 件 / 品質ゲート未達 0 / 一覧: blog/index.html%s / %s / %s"
        % (
            len(posts),
            "（未書き込み: --check）" if args.check else "",
            sitemap_note,
            feed_note,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
