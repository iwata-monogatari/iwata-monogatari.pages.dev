#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""著者情報を個人サイトの Profile（人物情報の正本）にそろえる。冪等。

2026-09-27 導入。人物情報の正本は https://oishi-hiroyuki.org/profile 、
Person の正本 @id は https://oishi-hiroyuki.org/#person 。

  1. 全HTMLの JSON-LD にある "author" の値を正本の Person 参照に置き換える
     （Article の他の項目・canonical は触らない）。
  2. サイト内で独自に定義している大石浩之の Person ノードは、@id・url を正本へ向け、
     運営サイトを並べた sameAs を外す。
  3. ブログ記事（blog/<slug>/index.html）の末尾著者欄 author-box を標準文面に置き換える。

使い方:  python scripts/normalize_author_profile.py [--check]
  --check  書き換えずに、そろっていないファイル数だけ表示して差があれば exit 1
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERSON_ID = "https://oishi-hiroyuki.org/#person"
PROFILE_URL = "https://oishi-hiroyuki.org/profile"
AUTHOR = {"@type": "Person", "@id": PERSON_ID, "name": "大石浩之", "url": PROFILE_URL}
AUTHOR_JSON = json.dumps(AUTHOR, ensure_ascii=False, separators=(",", ":"))

AUTHOR_BOX_BODY = (
    '<div class="author-body">'
    '<p class="author-name"><strong>大石浩之</strong>'
    '<span class="author-role">磐田市／富士ヶ丘サービス株式会社 代表</span></p>'
    "<p>磐田市で不動産・介護事業を営みながら、地域の歴史・地名・寺社・暮らしの記録を調べています。"
    "磐田物語では、公開資料と現地情報を確認しながら、地域の記憶をWeb上に残しています。</p>"
    f'<p class="author-profile"><a href="{PROFILE_URL}">プロフィールを見る</a></p>'
    "</div>"
)
DEFAULT_IMG = '<img alt="大石浩之" height="84" loading="lazy" src="/author-oishi.jpg" width="84"/>'

LD_RE = re.compile(r'(<script[^>]*application/ld\+json[^>]*>)(.*?)(</script>)', re.S | re.I)
AUTHOR_KEY_RE = re.compile(r'"author"\s*:\s*')
DECODER = json.JSONDecoder()
OISHI_NAMES = {"大石浩之", "大石裕之"}


def fix_author_values(block):
    out, pos = [], 0
    for m in AUTHOR_KEY_RE.finditer(block):
        if m.start() < pos:
            continue
        _, end = DECODER.raw_decode(block, m.end())
        out.append(block[pos:m.end()])
        out.append(AUTHOR_JSON)
        pos = end
    out.append(block[pos:])
    return "".join(out)


def clean_person(node):
    """独自 Person ノードを正本へ向ける。変更があれば True。"""
    changed = False
    if isinstance(node, dict):
        if node.get("@type") == "Person" and node.get("name") in OISHI_NAMES and (
            node.get("@id") != PERSON_ID or "sameAs" in node or node.get("url") != PROFILE_URL
            or node.get("name") != "大石浩之"
        ):
            node["@id"] = PERSON_ID
            node["name"] = "大石浩之"
            node["url"] = PROFILE_URL
            node.pop("sameAs", None)
            if "研究者" in str(node.get("jobTitle", "")):
                node.pop("jobTitle")
            changed = True
        for v in node.values():
            changed |= clean_person(v)
    elif isinstance(node, list):
        for v in node:
            changed |= clean_person(v)
    return changed


def fix_ld(html):
    def repl(m):
        head, block, tail = m.groups()
        new = fix_author_values(block)
        data = json.loads(new)
        if clean_person(data):
            indent = 2 if "\n" in new.strip() else None
            seps = None if indent else (",", ":")
            new = json.dumps(data, ensure_ascii=False, indent=indent, separators=seps)
            if block.startswith("\n"):
                new = "\n" + new + "\n"
        return head + new + tail
    return LD_RE.sub(repl, html)


def balanced_div_end(html, start):
    depth, i = 0, start
    tag = re.compile(r"<(/?)div\b[^>]*>", re.I)
    for t in tag.finditer(html, start):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return t.end()
    raise ValueError("unbalanced div")


def fix_author_box(html):
    html = re.sub(r'(<span class="post-author">)(?:大石裕之|磐田物語 編集部)(</span>)', r"\1大石浩之\2", html)
    for opener in ('<div class="author-box">', '<div class="post-author-box">'):
        start = html.find(opener)
        if start < 0:
            continue
        end = balanced_div_end(html, start)
        old = html[start:end]
        img = re.search(r"<img\b[^>]*>", old)
        img_html = img.group(0) if img else DEFAULT_IMG
        img_html = re.sub(r'\salt="[^"]*"', ' alt="大石浩之"', img_html)
        img_html = re.sub(r'\sclass="[^"]*"', "", img_html)
        new = f'<div class="author-box">{img_html}{AUTHOR_BOX_BODY}</div>'
        return html[:start] + new + html[end:]
    # 著者欄が無い記事は出典（と更新履歴）の直後に置く
    anchor = html.find('<section class="revision-history">')
    if anchor < 0:
        anchor = html.find("</article>")
    return html[:anchor] + f'<div class="author-box">{DEFAULT_IMG}{AUTHOR_BOX_BODY}</div>\n  ' + html[anchor:]


def main():
    check = "--check" in sys.argv
    files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8").stdout.split()
    changed = []
    for rel in files:
        p = ROOT / rel
        with open(p, encoding="utf-8", newline="") as fh:
            src = fh.read()
        new = fix_ld(src)
        if re.fullmatch(r"blog/[^/]+/index\.html", rel):
            new = fix_author_box(new)
        if new != src:
            changed.append(rel)
            if not check:
                p.write_text(new, encoding="utf-8", newline="")
    print(f"{'要修正' if check else '更新'}: {len(changed)} files")
    if check and changed:
        for rel in changed[:20]:
            print("  ", rel)
        sys.exit(1)


if __name__ == "__main__":
    main()
