#!/usr/bin/env python3
"""不足している OGP / Twitter カードのメタタグを補う。

canonical は全ページで公開URLに統一済みだが、og:url・og:image・og:site_name・
twitter:card は入っているページと入っていないページが混在していた。
SNSに貼られたときにタイトルだけの素っ気ない表示になるため、既定値で埋める。

  - og:url      : canonical と同じURL
  - og:image    : ページに指定が無ければサイト既定の /img/ogp.jpg
  - og:site_name / og:locale / twitter:card : 未指定なら既定値
  - 既に値が入っているものは書き換えない
  - canonical が無いページ、noindex のページは対象外

  python scripts/fill_ogp_metadata.py          # 変更点の確認のみ
  python scripts/fill_ogp_metadata.py --write  # 書き込む
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://iwata-monogatari.net"
DEFAULT_IMAGE = f"{BASE}/img/ogp.jpg"

EXCLUDE_DIRS = {".git", ".github", ".claude", ".tmp", ".wrangler", "node_modules",
                "archive", "partials", "docs", "scripts", "functions", "migrations",
                "assets", "images", "img", "data"}
EXCLUDE_FILES = {"404.html", "admin-bbs.html", "googlea3467099ea123f53.html"}

NOINDEX_RE = re.compile(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', re.I)
CANONICAL_RE = re.compile(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)


def has_meta(html: str, attr: str, key: str) -> bool:
    return re.search(rf'<meta[^>]*\b{attr}="{re.escape(key)}"', html, re.I) is not None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    counts = {"og:url": 0, "og:image": 0, "og:site_name": 0, "og:locale": 0, "twitter:card": 0}
    changed = 0
    skipped_noindex = skipped_nocanon = 0

    for path in sorted(ROOT.rglob("*.html")):
        parts = path.relative_to(ROOT).parts
        if any(p in EXCLUDE_DIRS for p in parts[:-1]) or path.name in EXCLUDE_FILES:
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        if NOINDEX_RE.search(html):
            skipped_noindex += 1
            continue
        m = CANONICAL_RE.search(html)
        if not m:
            skipped_nocanon += 1
            continue
        url = m.group(1).strip()

        additions = []
        for attr, key, value in (
            ("property", "og:url", url),
            ("property", "og:image", DEFAULT_IMAGE),
            ("property", "og:site_name", "磐田物語"),
            ("property", "og:locale", "ja_JP"),
            ("name", "twitter:card", "summary_large_image"),
        ):
            if not has_meta(html, attr, key):
                additions.append(f'<meta {attr}="{key}" content="{value}">')
                counts[key] += 1

        if not additions:
            continue
        new = html.replace("</head>", "\n".join(additions) + "\n</head>", 1)
        if new == html:
            continue
        changed += 1
        if args.write:
            path.write_text(new, encoding="utf-8", newline="\n")

    print(f"変更ファイル     : {changed} 件")
    for k, v in counts.items():
        print(f"  {k:<14} {v} 件追加")
    print(f"noindex で対象外 : {skipped_noindex} 件")
    print(f"canonical 無しで対象外: {skipped_nocanon} 件")
    print("書き込み完了" if args.write else "（ドライラン。--write で書き込み）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
