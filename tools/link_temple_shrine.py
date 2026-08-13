# -*- coding: utf-8 -*-
"""磐田物語の本文に現れる寺社名を ATAWI TEMPLE / ATAWI SHRINE の個別ページへ自動リンクする。

  python tools/link_temple_shrine.py --dry-run   # 変更せず件数とレポートだけ出す
  python tools/link_temple_shrine.py             # 実際に書き換える
  python tools/link_temple_shrine.py --strip     # 挿入済みリンクを全部はがす

何度実行しても結果は同じになる（既存の挿入リンクを一度はがしてから貼り直す）。
対応表は data/temple-shrine-links.json（tools/build_temple_shrine_links.py が生成）。

リンクを入れない場所:
  - <head> 内、script / style / noscript / svg / template
  - 既存の <a> の内側（リンクは入れ子にできない）
  - h1（ページ見出し）と <title>
  - header / footer / nav と、Pages Functions が配信時に中身を差し替える
    section.article-policy[data-common] / section.local-property-note[data-common]
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
REPORT = os.path.join(REPO, "docs", "temple-shrine-link-report.md")
CSS_HREF = "/assets/css/temple-shrine-ref.css"

SKIP_DIRS = {
    ".git", ".github", ".tmp", ".wrangler", "node_modules",
    "assets", "images", "img", "data", "functions", "migrations",
    "scripts", "tools", "research", "docs", "work", "partials",
}

TAG = re.compile(r"<!--.*?-->|<[^>]+>", re.S)
OPEN = re.compile(r"<\s*([a-zA-Z0-9]+)")
CLOSE = re.compile(r"<\s*/\s*([a-zA-Z0-9]+)")
VOID = {"br", "img", "hr", "meta", "link", "input", "source", "area", "col", "wbr", "embed", "track"}
BLOCK_TAGS = {
    "script", "style", "noscript", "svg", "template", "head", "title",
    "a", "h1", "header", "footer", "nav", "option", "textarea", "select",
}
COMMON_SECTION = re.compile(r'class="[^"]*\b(?:article-policy|local-property-note)\b', re.I)

INJECTED = re.compile(r'<a\b[^>]*\bdata-ts-ref="[^"]*"[^>]*>(.*?)</a>', re.S)
# 書名・史料名。『国分寺ものがたり』の「国分寺」は寺そのものではなく本の題名である
BOOK_TITLE = re.compile(r"『[^』]{0,100}』")
# 直後がこれらの語なら、寺社ではなく遺跡・古墳の名前（新豊院山古墳群、見性寺遺跡）
SITE_SUFFIX = ("山古墳群", "山古墳", "古墳群", "古墳", "遺跡", "廃寺")
H2 = re.compile(r"<h2\b", re.I)
CSS_LINK = '<link rel="stylesheet" href="%s" data-ts-ref-css>\n' % CSS_HREF
CSS_LINK_RE = re.compile(r'[ \t]*<link[^>]*data-ts-ref-css[^>]*>\s*\n?', re.I)


# ---------------------------------------------------------------- HTML走査
def text_spans(html):
    """本文としてリンクを入れてよいテキスト範囲 [(start, end), ...] を返す。"""
    spans = []
    depth = collections.Counter()
    common_depth = 0          # 配信時に差し替えられる共通セクションの入れ子数
    stack = []
    pos = 0
    in_body = False
    for m in TAG.finditer(html):
        if in_body and html[pos:m.start()].strip() and common_depth == 0 \
                and not any(depth[b] for b in BLOCK_TAGS):
            spans.append((pos, m.start()))
        tag = m.group(0)
        pos = m.end()
        if tag.startswith("<!--"):
            continue
        mc = CLOSE.match(tag)
        if mc:
            name = mc.group(1).lower()
            if name == "body":
                in_body = False
            if depth[name]:
                depth[name] -= 1
            while stack and stack[-1][0] != name:
                stack.pop()
            if stack:
                _, was_common = stack.pop()
                if was_common:
                    common_depth -= 1
            continue
        mo = OPEN.match(tag)
        if not mo:
            continue
        name = mo.group(1).lower()
        if name == "body":
            in_body = True
            continue
        if name in VOID or tag.rstrip().endswith("/>"):
            continue
        depth[name] += 1
        is_common = bool(COMMON_SECTION.search(tag))
        if is_common:
            common_depth += 1
        stack.append((name, is_common))
    return spans


# ---------------------------------------------------------------- 対応表
class Linker(object):
    def __init__(self, data):
        self.targets = data["targets"]
        self.unique = data["unique_surfaces"]
        self.ambiguous = data["ambiguous_surfaces"]
        self.blocks = set(data.get("block_forms") or [])
        self.markers = data.get("external_markers") or []
        self.page_hints = data.get("page_hints") or {}
        forms = set(self.unique) | set(self.ambiguous) | self.blocks
        # 長い名前を優先（「遠江国分寺跡」を「国分寺」より先に取る）
        self.pattern = re.compile(
            "|".join(re.escape(f) for f in sorted(forms, key=lambda s: (-len(s), s)))
        )
        self.stats = collections.Counter()
        self.unresolved = collections.defaultdict(list)
        self.resolved = collections.defaultdict(list)
        self.blocked = collections.Counter()
        self.external = collections.Counter()
        self.per_target = collections.Counter()
        self.in_book = collections.Counter()
        self.as_site = collections.Counter()
        self.repeat = collections.Counter()

    def is_external(self, html, start):
        window = html[max(0, start - 12):start]
        return any(mk in window for mk in self.markers)

    NEAR = 40
    # 地名キーの直後にこの字が続くときは別語。「天竜（大字）」と「天竜川」を分ける。
    KEY_TAIL = "川河市区町村駅線港湾郡県府"

    def key_in(self, text, key):
        i = text.find(key)
        while i >= 0:
            tail = text[i + len(key):i + len(key) + 1]
            if tail not in self.KEY_TAIL:
                return True
            i = text.find(key, i + 1)
        return False

    def near_hit(self, surface, html, start, end):
        """マッチの前後40文字に、どれか1候補だけの大字名が出ていれば、その候補を返す。"""
        text = html[max(0, start - self.NEAR):min(len(html), end + self.NEAR)]
        hits = [c["slug"] for c in self.ambiguous[surface]
                if any(self.key_in(text, k) for k in c["oaza_keys"])]
        return hits[0] if len(hits) == 1 else None

    def resolve_page(self, surface, occurrences, html, rel):
        """1ページ分の同名寺社をまとめて判定する。

        判定材料は「マッチの近くに出ている大字名」だけに限る。
          - ページのどこかに地名があるという程度の根拠は使わない
            （『元宮天神社』が福田・南島の天神社に結び付いてしまう）
          - 地区名（南部・竜洋など）も使わない
            （「南部低地の八王子神社」が万正寺の社に結び付いてしまう）
        近くの大字名で決まった社がページ内で1つに揃えば、同じページの残りの出現にも
        それを当てる（1本の記事は普通1つの社について書いているため）。
        """
        hint = (self.page_hints.get(rel) or {}).get(surface)
        if hint:
            return {i: (hint, "手動指定") for i, _ in enumerate(occurrences)}, hint
        label = "大字が近くにある"
        found = {}
        for i, (s, e) in enumerate(occurrences):
            slug = self.near_hit(surface, html, s, e)
            if slug:
                found[i] = (slug, label)
        if not found:
            return {}, None
        agreed = set(v[0] for v in found.values())
        if len(agreed) == 1:
            only = agreed.pop()
            return {i: (only, label if i in found else label + "＋ページ内で一致")
                    for i in range(len(occurrences))}, only
        return found, None

    def link_html(self, surface, slug):
        t = self.targets[slug]
        return ('<a class="ts-ref" data-ts-ref="%s:%s" href="%s" target="_blank" '
                'rel="noopener">%s</a>' % (t["kind"], slug, t["url"], surface))

    def process(self, html, rel):
        book_spans = [(m.start(), m.end()) for m in BOOK_TITLE.finditer(html)]
        sections = [m.start() for m in H2.finditer(html)]

        def in_book(pos):
            return any(s < pos < e for s, e in book_spans)

        def section_of(pos):
            n = 0
            for s in sections:
                if s < pos:
                    n += 1
                else:
                    break
            return n

        # 1周目: リンク候補の位置を集める
        hits = []                                   # [(start, end, surface, span_start, span_end)]
        for a, b in text_spans(html):
            for m in self.pattern.finditer(html, a, b):
                surface = m.group(0)
                if surface in self.blocks:
                    self.blocked[surface] += 1
                    continue
                if self.is_external(html, m.start()):
                    self.external[surface] += 1
                    continue
                if in_book(m.start()):
                    self.in_book[surface] += 1
                    continue
                if html[m.end():m.end() + 6].startswith(SITE_SUFFIX):
                    self.as_site[surface] += 1
                    continue
                hits.append((m.start(), m.end(), surface, a, b))

        # 2周目: 同名寺社をページ単位でまとめて判定する
        decisions = {}
        by_surface = collections.defaultdict(list)
        for idx, (s, e, surface, _, _) in enumerate(hits):
            if surface in self.ambiguous:
                by_surface[surface].append((idx, s, e))
        for surface, items in by_surface.items():
            occ = [(s, e) for _, s, e in items]
            picked, _ = self.resolve_page(surface, occ, html, rel)
            for pos, (idx, _, _) in enumerate(items):
                if pos in picked:
                    decisions[idx] = picked[pos]

        # 3周目: 書き出し。同じ寺社へは h2 セクションごとに1本だけ張る
        out = []
        cursor = 0
        n = 0
        seen = set()
        for idx, (s, e, surface, a, b) in enumerate(hits):
            if surface in self.unique:
                slug, how = self.unique[surface], None
            else:
                slug, how = decisions.get(idx, (None, None))
            ctx = re.sub(r"\s+", " ", html[max(a, s - 30):min(b, e + 30)])
            if not slug:
                if len(self.unresolved[surface]) < 400:
                    self.unresolved[surface].append((rel, ctx))
                self.stats["未解決"] += 1
                continue
            key = (section_of(s), slug)
            if key in seen:
                self.repeat[slug] += 1
                continue
            seen.add(key)
            if how:
                self.resolved[surface].append((rel, slug, how, ctx))
            out.append(html[cursor:s])
            out.append(self.link_html(surface, slug))
            cursor = e
            n += 1
            self.per_target[slug] += 1
        out.append(html[cursor:])
        return "".join(out), n


def strip_links(html):
    html = INJECTED.sub(lambda m: m.group(1), html)
    html = CSS_LINK_RE.sub("", html)
    return html


def ensure_css(html):
    if "data-ts-ref-css" in html:
        return html
    i = html.lower().find("</head>")
    if i < 0:
        return html
    return html[:i] + CSS_LINK + html[i:]


def html_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith(".html"):
                yield os.path.join(root, f)


def write_report(linker, changed, total_links, pages):
    lines = []
    lines.append("# 寺社名の自動リンク レポート\n")
    lines.append("`tools/link_temple_shrine.py` の実行結果。対応表は `data/temple-shrine-links.json`、")
    lines.append("手作業の調整は `data/temple-shrine-links.manual.json` で行う。\n")

    lines.append("## リンクの付け方\n")
    lines.append("- 同じ寺社へは **h2 セクションごとに1本だけ**リンクする。")
    lines.append("  節が変われば張り直すので、長い論考でも「さっきの寺はどれだったか」に戻れる。")
    lines.append("  一方、同じ節の中で同じ寺社名が何度出ても2本目以降は張らない")
    lines.append("  （2026-08-13の初回導入時は全出現に張っており、7,366本のうち86%が")
    lines.append("  同一ページ・同一寺社への重複だった。同日この方式へ変更した）。")
    lines.append("- リンク先は ATAWI TEMPLE / ATAWI SHRINE の**個別ページ**のみ。一覧・検索ページへは逃がさない。")
    lines.append("- 別タブで開く（`target=\"_blank\" rel=\"noopener\"`）。見た目は `assets/css/temple-shrine-ref.css` で一括管理する。")
    lines.append("- リンクを入れない場所: `<head>`、既存の `<a>` の内側、h1、`header`/`footer`/`nav`、")
    lines.append("  配信時に中身が差し替わる `section.article-policy[data-common]` と `section.local-property-note[data-common]`、")
    lines.append("  `script`/`style`/`svg`。\n")
    lines.append("### 誤リンクを避けるための決まり\n")
    lines.append("- **山号だけの別称は使わない**（「松林山」は松林山古墳、「風祭山」は地名と衝突するため）。")
    lines.append("- **長い固有名詞を優先する**（「遠江国分寺跡」を先に取り、内側の「国分寺」では切らない）。")
    lines.append("- **直前12文字に市外の地名があれば見送る**（「京都・松尾神社」「浜松・諏訪神社」「愛知県の津島神社」など）。")
    lines.append("- **書名・史料名（『』の内側）にはリンクしない**（『国分寺ものがたり』は本の題名であって寺ではない）。")
    lines.append("- **直後が「山古墳群」「古墳」「遺跡」「廃寺」ならリンクしない**（新豊院山古墳群は国指定史跡であって寺ではない）。")
    lines.append("- **同名の寺社は、すぐ近くに大字名があるときだけ**リンクする（「下太の八王子神社」「中野白山神社」）。")
    lines.append("  ページのどこかに地名がある、地区名が近くにある、という程度の根拠では判定しない。")
    lines.append("  近くの大字名で決まった社がページ内で1つに揃えば、同じページの残りの出現にも同じ社を当てる。")
    lines.append("- それでも決まらないものはリンクしない（下の一覧に残す）。誤リンクより未リンクを選ぶ。\n")

    lines.append("## 集計\n")
    lines.append("| 項目 | 件数 |")
    lines.append("|---|---:|")
    lines.append("| 走査したHTML | %d |" % pages)
    lines.append("| リンクを挿入したページ | %d |" % changed)
    lines.append("| 挿入したリンク | %d |" % total_links)
    lines.append("| リンク先になった寺社 | %d / %d |" % (len(linker.per_target), len(linker.targets)))
    lines.append("| 同じ節にすでに張ってあり省いた出現 | %d |" % sum(linker.repeat.values()))
    lines.append("| 書名・史料名の中として除外 | %d |" % sum(linker.in_book.values()))
    lines.append("| 遺跡・古墳の名前として除外 | %d |" % sum(linker.as_site.values()))
    lines.append("| 同名で特定できず見送った出現 | %d |" % linker.stats["未解決"])
    lines.append("| 市外の寺社とみて見送った出現 | %d |" % sum(linker.external.values()))
    lines.append("| より長い固有名詞の一部として除外 | %d |" % sum(linker.blocked.values()))
    lines.append("")

    lines.append("## リンク先 上位30寺社\n")
    lines.append("| 寺社 | 種別 | リンク数 |")
    lines.append("|---|---|---:|")
    for slug, cnt in linker.per_target.most_common(30):
        t = linker.targets[slug]
        lines.append("| %s | %s | %d |" % (t["name"], "寺院" if t["kind"] == "temple" else "神社", cnt))
    lines.append("")

    lines.append("## 名前が出てもリンクしなかった寺社（同名で特定できず）\n")
    if not linker.unresolved:
        lines.append("なし。\n")
    for surface in sorted(linker.unresolved, key=lambda s: -len(linker.unresolved[s])):
        items = linker.unresolved[surface]
        cands = ", ".join(
            "%s → `%s`（%s）" % (
                linker.targets[c["slug"]]["name"], c["slug"],
                "/".join(c["oaza_keys"] + c["area_keys"]) or "手がかり無し")
            for c in linker.ambiguous[surface]
        )
        lines.append("### %s（%d件）\n" % (surface, len(items)))
        lines.append("候補: %s\n" % cands)
        for rel, ctx in items[:12]:
            lines.append("- `%s` … %s" % (rel, ctx))
        if len(items) > 12:
            lines.append("- （ほか %d件）" % (len(items) - 12))
        lines.append("")
    lines.append("特定できたものだけをリンクする方針のため、上記は意図的に未リンクとしている。")
    lines.append("人手で確定できる場合は `data/temple-shrine-links.manual.json` の `page_hints` に")
    lines.append("`\"<相対パス>\": {\"<表層形>\": \"<slug>\"}` を書き、ビルドと再実行を行う。\n")

    lines.append("## 市外の寺社として見送った語\n")
    if linker.external:
        lines.append("| 語 | 件数 |")
        lines.append("|---|---:|")
        for s, c in linker.external.most_common():
            lines.append("| %s | %d |" % (s, c))
    else:
        lines.append("なし。")
    lines.append("")

    lines.append("## 一度も本文に現れなかった寺社\n")
    missing = [s for s in linker.targets if s not in linker.per_target]
    lines.append("%d / %d件。磐田物語に記事がまだ無い寺社であり、対応漏れではない。\n"
                 % (len(missing), len(linker.targets)))
    lines.append("<details><summary>一覧</summary>\n")
    for slug in sorted(missing, key=lambda s: linker.targets[s]["name"]):
        t = linker.targets[slug]
        lines.append("- %s（%s）" % (t["name"], "寺院" if t["kind"] == "temple" else "神社"))
    lines.append("\n</details>")

    with io.open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strip", action="store_true")
    ap.add_argument("--audit", metavar="PATH",
                    help="同名寺社をどう判定したかの一覧をこのファイルに書き出す")
    args = ap.parse_args()

    with io.open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    linker = Linker(data)

    files = list(html_files())
    changed = 0
    total = 0
    for path in files:
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        with io.open(path, encoding="utf-8", newline="") as fh:
            original = fh.read()
        base = strip_links(original)
        if args.strip:
            new = base
            n = 0
        else:
            new, n = linker.process(base, rel)
            if n:
                new = ensure_css(new)
        total += n
        if n:
            changed += 1
        if new != original and not args.dry_run:
            with io.open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new)

    if args.strip:
        print("挿入済みリンクをはがしました（%d ファイルを走査）" % len(files))
        return

    if args.audit:
        with io.open(args.audit, "w", encoding="utf-8", newline="\n") as fh:
            for surface in sorted(linker.resolved):
                rows = linker.resolved[surface]
                fh.write("\n=== %s （%d件）\n" % (surface, len(rows)))
                for rel, slug, how, ctx in rows:
                    fh.write("  [%s] -> %s (%s)  %s\n" % (rel, slug, how, ctx))

    write_report(linker, changed, total, len(files))
    print("走査 %d ファイル / リンク挿入 %d 件 / 対象ページ %d" % (len(files), total, changed))
    print("リンク先寺社 %d / %d" % (len(linker.per_target), len(linker.targets)))
    print("未解決(同名) %d 件 / 市外判定 %d 件 / 長い固有名詞で除外 %d 件"
          % (linker.stats["未解決"], sum(linker.external.values()), sum(linker.blocked.values())))
    print("レポート: %s" % os.path.relpath(REPORT, REPO))
    if args.dry_run:
        print("（--dry-run のためファイルは書き換えていません）")


if __name__ == "__main__":
    main()
