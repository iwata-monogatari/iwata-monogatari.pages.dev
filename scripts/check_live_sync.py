"""Run this before touching this repo in any session.

Compares the local working copy's data/pages.json and data/new-articles.json
against what is *actually live* at https://iwata-monogatari.net right now.

Why this exists: on 2026-07-15, work started from the assumption that the
local git clone was "in sync" because `git status` showed no divergence
from origin/main. Production had in fact drifted 108 articles ahead via a
non-git deploy path, and nobody noticed until partway through a session
that started without checking. Never assume local == live; check.

Exit code is nonzero if local and live disagree, so this can be used as a
pre-flight gate, not just a printout.
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://iwata-monogatari.net"


def normalize_url(url):
    return "/" + str(url or "").lstrip("/")


def fetch_live_json(path):
    url = SITE_ORIGIN + "/" + path.lstrip("/") + "?cachebust=check-live-sync"
    req = urllib.request.Request(url, headers={"User-Agent": "check-live-sync"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_local_json(path):
    with (ROOT / path).open("r", encoding="utf-8") as f:
        return json.load(f)


def published_urls(pages_doc):
    pages = pages_doc.get("pages", pages_doc) if isinstance(pages_doc, dict) else pages_doc
    return {normalize_url(p.get("url", "")).rstrip("/") for p in pages if p.get("status") == "published"}


def article_urls(new_articles_list):
    return {normalize_url(a.get("url", "")).rstrip("/") for a in new_articles_list}


def report(label, local_only, live_only):
    ok = not local_only and not live_only
    print(f"--- {label} ---")
    if ok:
        print("  一致（ローカル ＝ 本番）")
        return True
    if local_only:
        print(f"  ローカルにのみ存在（本番未反映・push/deploy漏れの可能性）: {len(local_only)} 件")
        for u in sorted(local_only)[:15]:
            print(f"    - {u}")
    if live_only:
        print(f"  本番にのみ存在（ローカルに無い＝別経路で追加された可能性、要調査）: {len(live_only)} 件")
        for u in sorted(live_only)[:15]:
            print(f"    - {u}")
    return False


def main():
    try:
        live_pages = fetch_live_json("data/pages.json")
        live_articles = fetch_live_json("data/new-articles.json")
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"本番の取得に失敗しました（ネットワーク等）: {exc}", file=sys.stderr)
        return 1

    local_pages = load_local_json("data/pages.json")
    local_articles = load_local_json("data/new-articles.json")

    live_page_urls = published_urls(live_pages)
    local_page_urls = published_urls(local_pages)
    live_article_urls = article_urls(live_articles)
    local_article_urls = article_urls(local_articles)

    ok1 = report(
        "data/pages.json（公開記事）",
        local_page_urls - live_page_urls,
        live_page_urls - local_page_urls,
    )
    ok2 = report(
        "data/new-articles.json",
        local_article_urls - live_article_urls,
        live_article_urls - local_article_urls,
    )

    if ok1 and ok2:
        print("\nローカルと本番は一致しています。作業を始めて問題ありません。")
        return 0

    print(
        "\n食い違いがあります。編集・上書きを始める前に、この差分の原因を先に調べてください"
        "（本番にしか無いものを消して良いとは限りません）。",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
