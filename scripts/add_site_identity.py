#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""運営者表記の統一・rel="author"・サイト共通 JSON-LD（WebSite / Organization / Person）を一括適用する。冪等。

2026-10-06 導入（AI推薦対策指示書 A-3）。

  1. フッター等の運営者表記「大石ひろゆき」を「大石浩之（おおいし ひろゆき）」へ置換。
     置換対象はフッター系の定型文言だけ（SVG図版・記事固有の説明文・引用は触らない）。
  2. oishi-hiroyuki.org への運営者リンクに rel="author" を付与（既存 rel は保持して追記）。
  3. インデックス対象の全HTMLの </head> 直前に、共通 JSON-LD
     <script type="application/ld+json" id="site-identity"> を1つだけ置く（無ければ追加、あれば更新）。
     @id は正本を再利用:
       Person       https://oishi-hiroyuki.org/#person
       Organization https://www.fujigaoka-service.co.jp/#organization

使い方:
  python scripts/add_site_identity.py            # ドライラン（件数のみ表示）
  python scripts/add_site_identity.py --apply    # 書き込み
  python scripts/add_site_identity.py --check    # 未適用があれば exit 1
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://iwata-monogatari.net/"
PERSON_ID = "https://oishi-hiroyuki.org/#person"
ORG_ID = "https://www.fujigaoka-service.co.jp/#organization"
LD_ID = "site-identity"

NAME_OLD = "大石ひろゆき"
NAME_NEW = "大石浩之（おおいし ひろゆき）"

# フッター系の定型文言のみ置換する（完全一致の文字列）。
NAME_REPLACEMENTS = [
    ("大石ひろゆき関連サイト", NAME_NEW + "関連サイト"),
    ('aria-label="大石ひろゆき"', f'aria-label="{NAME_NEW}"'),
    ('__heading">大石ひろゆき</p>', f'__heading">{NAME_NEW}</p>'),
    ("<h2>大石ひろゆき</h2>", f"<h2>{NAME_NEW}</h2>"),
    ("大石ひろゆき公式サイト", NAME_NEW + "公式サイト"),
    ("Copyright 大石ひろゆき", "Copyright " + NAME_NEW),
    ("大石ひろゆきの別活動", NAME_NEW + "の別活動"),
    ("大石ひろゆきのSNS", NAME_NEW + "のSNS"),
]

OISHI_A_RE = re.compile(
    r'<a\b(?=[^>]*\bhref=["\']https?://(?:www\.)?oishi-hiroyuki\.org(?:[/?#"\'][^"\']*)?["\'])[^>]*>', re.I)
REL_RE = re.compile(r'\brel=(["\'])([^"\']*)\1', re.I)

GRAPH = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "@id": SITE + "#website",
            "name": "磐田物語",
            "url": SITE,
            "inLanguage": "ja",
            "description": "静岡県磐田市の歴史と文化を、一市民の視点から書き留めていく地域アーカイブ。",
            "publisher": {"@id": ORG_ID},
            "author": {"@id": PERSON_ID},
        },
        {
            "@type": ["Organization", "RealEstateAgent"],
            "@id": ORG_ID,
            "name": "富士ヶ丘サービス株式会社",
            "alternateName": ["ふじがおか", "ATAWI FUDOSAN"],
            "url": "https://www.fujigaoka-service.co.jp/",
            "description": "磐田市・袋井市で、介護・相続・空き家に特化した不動産売却支援。2011年創業の介護事業者が2018年から不動産仲介を行う。",
            "foundingDate": "2011-03",
            "founder": {"@id": PERSON_ID},
            "address": {
                "@type": "PostalAddress",
                "postalCode": "438-0086",
                "addressRegion": "静岡県",
                "addressLocality": "磐田市",
                "streetAddress": "見付5789番地1",
                "addressCountry": "JP",
            },
            "telephone": "+81-538-31-3308",
            "faxNumber": "+81-538-31-3307",
            "identifier": [
                {"@type": "PropertyValue", "name": "宅地建物取引業免許", "value": "静岡県知事 (2) 第14083号"}
            ],
            "sameAs": [
                "https://www.fujigaoka-service.info/",
                "https://fudosan.atawi.link/",
                "https://oishi-hiroyuki.org/",
                "https://iwata.enshu-lifehack.com/",
                "https://www.facebook.com/realestatefujigaokaservice/",
                "https://www.homes.co.jp/realtor/mid-144301hQA24Pw1v0pM/",
                "https://iqrafudosan.com/companies/7405",
                "https://share.google/JvfsXQE82HymM6k8k",
            ],
        },
        {
            "@type": "Person",
            "@id": PERSON_ID,
            "name": "大石浩之",
            "alternateName": ["大石ひろゆき", "おおいし ひろゆき", "Hiroyuki Oishi"],
            "jobTitle": "代表取締役／宅地建物取引士",
            "url": "https://oishi-hiroyuki.org/",
            "worksFor": {"@id": ORG_ID},
            "sameAs": [
                "https://oishi-hiroyuki.org/",
                "https://oishi-hiroyuki.org/profile",
                "https://www.instagram.com/hiroyuki.oishi.fujigaoka/",
            ],
        },
    ],
}
LD_JSON = json.dumps(GRAPH, ensure_ascii=False, indent=2)
LD_BLOCK = f'<script type="application/ld+json" id="{LD_ID}">\n{LD_JSON}\n</script>\n'
LD_BLOCK_RE = re.compile(
    r'<script type="application/ld\+json" id="' + LD_ID + r'">.*?</script>\n?', re.S)

SKIP_PREFIX = ("partials/", "search/")
SKIP_NAMES = {"404.html", "googlea3467099ea123f53.html"}
NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', re.I)
REFRESH_RE = re.compile(r'<meta[^>]+http-equiv=["\']refresh["\']', re.I)


def add_author_rel(html):
    def repl(m):
        tag = m.group(0)
        r = REL_RE.search(tag)
        if r:
            vals = r.group(2).split()
            if "author" in vals:
                return tag
            return tag[:r.start()] + f'rel={r.group(1)}{" ".join(vals + ["author"])}{r.group(1)}' + tag[r.end():]
        return tag[:-1].rstrip() + ' rel="author">'
    return OISHI_A_RE.sub(repl, html)


def replace_names(html):
    for old, new in NAME_REPLACEMENTS:
        html = html.replace(old, new)
    return html


def wants_jsonld(rel, html):
    if rel in SKIP_NAMES or rel.startswith(SKIP_PREFIX) or rel.startswith("admin-"):
        return False
    if "</head>" not in html:
        return False
    head = html[:html.index("</head>")]
    return not (NOINDEX_RE.search(head) or REFRESH_RE.search(head))


def add_jsonld(rel, html):
    if not wants_jsonld(rel, html):
        return html
    if LD_BLOCK_RE.search(html):
        return LD_BLOCK_RE.sub(lambda m: LD_BLOCK, html, count=1)
    return html.replace("</head>", LD_BLOCK + "</head>", 1)


def main():
    apply_ = "--apply" in sys.argv
    check = "--check" in sys.argv
    files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8").stdout.splitlines()
    stats = {"names": 0, "rel": 0, "jsonld": 0, "any": 0}
    changed = []
    for rel in files:
        p = ROOT / rel
        with open(p, encoding="utf-8", newline="") as fh:
            src = fh.read()
        a = replace_names(src)
        b = add_author_rel(a)
        c = add_jsonld(rel, b)
        stats["names"] += a != src
        stats["rel"] += b != a
        stats["jsonld"] += c != b
        if c != src:
            stats["any"] += 1
            changed.append(rel)
            if apply_:
                p.write_text(c, encoding="utf-8", newline="")
    mode = "適用" if apply_ else ("確認" if check else "ドライラン")
    print(f"{mode}: 対象HTML {len(files)} / 変更 {stats['any']} files "
          f"(名前表記 {stats['names']}, rel=author {stats['rel']}, JSON-LD {stats['jsonld']})")
    if (check or not apply_) and changed and check:
        for rel in changed[:20]:
            print("  ", rel)
        sys.exit(1)


if __name__ == "__main__":
    main()
