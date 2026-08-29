#!/usr/bin/env python3
"""一の谷特集（/inotani/）の各ページに Article / BreadcrumbList の構造化データを付ける。

磐田物語の本編記事（c070 など）は JSON-LD を2本持つのに対し、この特集の13ページは
どれも持っていなかったため、同じ書式でそろえる。既に入っているページは何もしない。

  python scripts/add_inotani_structured_data.py          # 変更点の確認のみ
  python scripts/add_inotani_structured_data.py --write  # 書き込む
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "inotani"
BASE = "https://iwata-monogatari.net"
OGP = f"{BASE}/img/ogp.jpg"
FEATURE = "一の谷中世墳墓群と見付の中世"

ORG = {"@type": "Organization", "name": "磐田物語", "url": f"{BASE}/"}


def meta(html: str, prop: str) -> str:
    m = re.search(rf'<meta[^>]*(?:name|property)="{re.escape(prop)}"[^>]*content="([^"]*)"', html)
    return html_mod.unescape(m.group(1)) if m else ""


def git_dates(path: Path) -> tuple[str, str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--format=%cs", "--", str(path.relative_to(ROOT))],
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        out = []
    if not out:
        return "", ""
    return out[-1], out[0]  # (最初のコミット日=公開日, 最新コミット日=更新日)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    changed = 0
    for path in sorted(DIR.glob("*.html")):
        html = path.read_text(encoding="utf-8")
        if "application/ld+json" in html:
            print(f"  skip (既にあり): {path.name}")
            continue

        canonical = ""
        m = re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', html)
        if m:
            canonical = m.group(1)
        if not canonical:
            print(f"  skip (canonical なし): {path.name}")
            continue

        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        headline = html_mod.unescape(re.sub(r"<[^>]+>", "", h1.group(1)).strip()) if h1 else ""
        headline = headline or meta(html, "og:title")
        description = meta(html, "description")
        published, modified = git_dates(path)

        article = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline,
            "description": description,
            "image": OGP,
            "inLanguage": "ja",
            "author": ORG,
            "publisher": {**ORG, "logo": {"@type": "ImageObject", "url": OGP}},
            "isPartOf": {"@type": "WebSite", "name": "磐田物語", "url": f"{BASE}/"},
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
            "articleSection": FEATURE,
        }
        if published:
            article["datePublished"] = published
        if modified:
            article["dateModified"] = modified

        crumbs = [
            {"@type": "ListItem", "position": 1, "name": "磐田物語", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": FEATURE, "item": f"{BASE}/inotani/"},
        ]
        if canonical.rstrip("/") != f"{BASE}/inotani":
            crumbs.append({"@type": "ListItem", "position": 3, "name": headline, "item": canonical})
        breadcrumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs}

        block = "".join(
            f'<script type="application/ld+json">\n{json.dumps(o, ensure_ascii=False, indent=2)}\n</script>\n'
            for o in (article, breadcrumb)
        )
        new = html.replace("</head>", block + "</head>", 1)
        if new == html:
            print(f"  skip (</head> なし): {path.name}")
            continue

        changed += 1
        print(f"  add: {path.name}  headline={headline}  {published}→{modified}")
        if args.write:
            path.write_text(new, encoding="utf-8", newline="\n")

    print(f"\n対象 {changed} ファイル" + ("（書き込み済み）" if args.write else "（ドライラン）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
