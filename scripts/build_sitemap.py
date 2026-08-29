#!/usr/bin/env python3
"""sitemap.xml をリポジトリの実ファイルから再生成する。

方針
  - 掲載するのは「自分自身を canonical に指定しているページ」だけ。
    別URLを canonical に持つ複製ページ（xxx.html と xxx/index.html の重複など）は自動的に除外される。
  - robots noindex のページ、404 / 管理画面 / 検索エンジン所有権確認ファイルは除外。
  - URL は拡張子なしに統一する（.html は Cloudflare Pages が 308 でリダイレクトするため）。
    ディレクトリの index.html は末尾スラッシュ形式にする。
  - lastmod は git の最終コミット日。git 情報が取れない場合はファイル更新日。
  - blog:start / blog:end の区画は scripts/build_blog.py の管理領域なのでそのまま引き継ぐ。

使い方
  python scripts/build_sitemap.py          # 差分だけ表示（書き込まない）
  python scripts/build_sitemap.py --write  # sitemap.xml を書き換える
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://iwata-monogatari.net"

# 走査しないディレクトリ
EXCLUDE_DIRS = {
    ".git", ".github", ".claude", ".tmp", ".wrangler", "node_modules",
    "archive", "partials", "docs", "scripts", "functions", "migrations",
    "assets", "images", "img", "data", "blog",
}
# 掲載しないファイル
EXCLUDE_FILES = {"404.html", "admin-bbs.html", "googlea3467099ea123f53.html"}

NOINDEX_RE = re.compile(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', re.I)
CANONICAL_RE = re.compile(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
BLOG_BLOCK_RE = re.compile(r"[ \t]*<!-- blog:start.*?<!-- blog:end -->", re.S)


def url_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[: -len('index.html')]}"
    return f"{BASE}/{rel[: -len('.html')]}"


def git_lastmod(paths: list[Path]) -> dict[Path, str]:
    """全ファイルの最終コミット日を1回の git 呼び出しでまとめて取る。"""
    out: dict[Path, str] = {}
    try:
        raw = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--name-only", "--format=%x00%cs", "--", "."],
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return out
    date = None
    for line in raw.splitlines():
        if line.startswith("\x00"):
            date = line[1:].strip()
        elif line.strip() and date:
            p = ROOT / line.strip()
            out.setdefault(p, date)  # log は新しい順なので最初に出たものが最終更新
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="sitemap.xml を書き換える")
    args = ap.parse_args()

    pages: list[Path] = []
    for p in ROOT.rglob("*.html"):
        if any(part in EXCLUDE_DIRS for part in p.relative_to(ROOT).parts[:-1]):
            continue
        if p.name in EXCLUDE_FILES:
            continue
        pages.append(p)

    lastmods = git_lastmod(pages)
    entries: list[tuple[str, str]] = []
    skipped_noindex = 0
    skipped_dup: list[str] = []

    for p in sorted(pages):
        html = p.read_text(encoding="utf-8", errors="replace")
        if NOINDEX_RE.search(html):
            skipped_noindex += 1
            continue
        url = url_for(p)
        m = CANONICAL_RE.search(html)
        if m:
            canon = m.group(1).strip()
            if canon == BASE:
                canon = BASE + "/"
            # 末尾スラッシュの有無も別URLとして扱う（/f002 と /f002/ は同一ではない）
            if canon != url:
                # 別URLを正典としているページ（旧版の重複ファイルなど）は載せない
                skipped_dup.append(f"{p.relative_to(ROOT).as_posix()} -> {canon}")
                continue
        date = lastmods.get(p)
        if not date:
            date = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")
        entries.append((url, date))

    entries.sort(key=lambda e: e[0])

    blog_block = ""
    if SITEMAP.exists():
        m = BLOG_BLOCK_RE.search(SITEMAP.read_text(encoding="utf-8"))
        if m:
            blog_block = m.group(0).strip()

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, date in entries:
        freq, prio = ("daily", "1.0") if url == BASE + "/" else ("monthly", "0.7")
        lines.append(
            f"  <url><loc>{url}</loc><lastmod>{date}</lastmod>"
            f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>"
        )
    if blog_block:
        lines.append("  " + blog_block)
    lines.append("</urlset>")
    xml = "\n".join(lines) + "\n"

    blog_urls = len(re.findall(r"<loc>", blog_block))
    print(f"掲載URL          : {len(entries)} 件（+ blog 区画 {blog_urls} 件）")
    print(f"noindex で除外   : {skipped_noindex} 件")
    print(f"重複canonicalで除外: {len(skipped_dup)} 件")
    for s in skipped_dup[:10]:
        print(f"    {s}")
    if len(skipped_dup) > 10:
        print(f"    ... 他 {len(skipped_dup) - 10} 件")

    if args.write:
        SITEMAP.write_text(xml, encoding="utf-8", newline="\n")
        print(f"書き込み完了: {SITEMAP}")
    else:
        print("（ドライラン。--write で書き込み）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
