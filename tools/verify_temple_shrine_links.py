# -*- coding: utf-8 -*-
"""挿入済みの寺社リンクを検証する。1件でも落ちたら公開しない。

  python tools/verify_temple_shrine_links.py          # 構造チェックのみ
  python tools/verify_temple_shrine_links.py --live   # リンク先のHTTP 200も確認

チェック内容
  1. すべての挿入リンクが temple.atawi.link / shrine.atawi.link の個別ページを指す
  2. slug が data/temple-shrine-links.json に登録済みで、種別（寺院/神社）とURLが一致する
  3. アンカー文字列が、その寺社の登録名または別称のいずれかである
  4. リンクが <a> の入れ子になっていない
  5. リンクのあるページに専用CSSの <link> が入っている
  6. pages.dev のURLを1件も持ち込んでいない
  7. （--live）リンク先URLがすべて HTTP 200 を返す
"""
import argparse
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data", "temple-shrine-links.json")

SKIP_DIRS = {
    ".git", ".github", ".tmp", ".wrangler", "node_modules",
    "assets", "images", "img", "data", "functions", "migrations",
    "scripts", "tools", "research", "docs", "work", "partials",
}

LINK = re.compile(
    r'<a class="ts-ref" data-ts-ref="(?P<kind>temple|shrine):(?P<slug>[^"]+)"'
    r' href="(?P<url>[^"]+)" target="_blank" rel="noopener">(?P<text>[^<]*)</a>'
)
ANY_TS = re.compile(r'data-ts-ref="')
NESTED = re.compile(r'<a\b(?:(?!</a>).)*?<a class="ts-ref"', re.S)
PAGES_DEV = re.compile(r'(?:href|src|content)="[^"]*pages\.dev', re.I)


def html_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith(".html"):
                yield os.path.join(root, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="リンク先のHTTP応答も確認する")
    args = ap.parse_args()

    with io.open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    targets = data["targets"]
    allowed_text = collections.defaultdict(set)
    for surface, slug in data["unique_surfaces"].items():
        allowed_text[slug].add(surface)
    for surface, cands in data["ambiguous_surfaces"].items():
        for c in cands:
            allowed_text[c["slug"]].add(surface)
    # page_hints は候補外の社（例: 天神社→矢奈比賣神社）を指すことがある
    for hints in (data.get("page_hints") or {}).values():
        for surface, slug in hints.items():
            allowed_text[slug].add(surface)

    errors = []
    urls = collections.Counter()
    pages = 0
    total = 0

    for path in html_files():
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        with io.open(path, encoding="utf-8", newline="") as fh:
            html = fh.read()
        declared = len(ANY_TS.findall(html))
        found = list(LINK.finditer(html))
        if declared != len(found):
            errors.append("%s: 想定した形のリンクは %d 件だが data-ts-ref は %d 件ある（形式崩れ）"
                          % (rel, len(found), declared))
        if not found:
            if "temple-shrine-ref.css" in html:
                errors.append("%s: リンクが無いのに専用CSSの link が残っている" % rel)
            continue
        pages += 1
        total += len(found)
        if 'href="/assets/css/temple-shrine-ref.css" data-ts-ref-css' not in html:
            errors.append("%s: リンクがあるのに専用CSSの link が無い" % rel)
        if NESTED.search(html):
            errors.append("%s: <a> の入れ子になっているリンクがある" % rel)
        # 全社ルール: pages.dev をURLとして書かない（検索キーワード等の地の文は対象外）
        if PAGES_DEV.search(html):
            errors.append("%s: pages.dev を指すURLがある" % rel)
        for m in found:
            slug, kind, url, text = m.group("slug"), m.group("kind"), m.group("url"), m.group("text")
            t = targets.get(slug)
            if not t:
                errors.append("%s: 未登録の slug %s" % (rel, slug))
                continue
            if t["kind"] != kind:
                errors.append("%s: %s の種別が %s になっている（正しくは %s）"
                              % (rel, slug, kind, t["kind"]))
            if url != t["url"]:
                errors.append("%s: %s のURLが %s（正しくは %s）" % (rel, slug, url, t["url"]))
            if text not in allowed_text[slug]:
                errors.append("%s: %s のリンク文字列「%s」は登録名・別称のどれでもない"
                              % (rel, slug, text))
            urls[url] += 1

    print("リンクのあるページ %d / リンク総数 %d / リンク先URL %d種" % (pages, total, len(urls)))

    if args.live:
        import urllib.request
        import urllib.error
        bad = []
        for i, url in enumerate(sorted(urls), 1):
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "iwata-monogatari-linkcheck"})
            try:
                with urllib.request.urlopen(req, timeout=20) as res:
                    if res.status != 200:
                        bad.append("%s -> HTTP %s" % (url, res.status))
            except urllib.error.HTTPError as e:
                bad.append("%s -> HTTP %s" % (url, e.code))
            except Exception as e:
                bad.append("%s -> %s" % (url, e))
            if i % 20 == 0:
                print("  ... %d/%d 確認" % (i, len(urls)))
        if bad:
            errors.extend("リンク先が200を返さない: " + b for b in bad)
        else:
            print("リンク先 %d件すべて HTTP 200" % len(urls))

    if errors:
        print("\n!! %d件の問題" % len(errors))
        for e in errors[:80]:
            print("  -", e)
        if len(errors) > 80:
            print("  （ほか %d件）" % (len(errors) - 80))
        sys.exit(1)
    print("検証OK")


if __name__ == "__main__":
    main()
