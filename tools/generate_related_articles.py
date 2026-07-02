# -*- coding: utf-8 -*-
"""磐田物語 関連記事セクション自動生成スクリプト

ルート直下の番号付き記事ページ（例: m001.html, c024.html）に対し、
data/pages.json の地区・テーマ情報とタイトル・説明文のキーワード一致から
関連記事を選定し、静的HTMLの「関連記事」セクションを埋め込む。

- 挿入位置: <section class="local-property-note"> の直前
  （無い場合は <footer class="im-foot"> の直前、それも無ければ </body> の直前）
- <!-- im-related:start --> ～ <!-- im-related:end --> のマーカーで囲むため、
  再実行すると既存セクションを最新の内容に置き換える（冪等）。
- リダイレクトスタブ、手書きの「関連記事」見出しを持つページ、機能ページは対象外。

新規記事を公開したら、data/pages.json を更新した上で本スクリプトを再実行する:
    python tools/generate_related_articles.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARK_START = "<!-- im-related:start -->"
MARK_END = "<!-- im-related:end -->"

# 記事プレフィックス → 地区ID（pages.json の district_id に対応）
PREFIX_DISTRICT = {
    "m": "mitsuke", "n": "nakaizumi", "u": "mikuriya", "t": "toyoda",
    "s": "nanbu", "k": "koyo", "r": "ryuyo", "f": "fukude",
    "y": "toyooka", "o": "toyooka",
    # c=共通, h=戦争・平和特集（地区なし）
}

DISTRICT_NAME = {
    "mitsuke": "見付", "nakaizumi": "中泉", "mikuriya": "御厨", "toyoda": "豊田",
    "nanbu": "南部", "koyo": "向陽", "ryuyo": "竜洋", "fukude": "福田",
    "toyooka": "豊岡",
}

# 機能ページ（一覧・辞典・ツール類）: 挿入対象からもリンク候補からも外す
FUNCTIONAL_PAGES = {
    "c001.html",  # 憲章
    "c002.html",  # 地域分類
    "c004.html",  # タイムトラベル地図
    "c005.html",  # 資料集
    "c006.html",  # 遠州弁辞典
    "c007.html",  # はじめに
    "c008.html",  # 標準語⇄遠州弁 変換
    "c014.html",  # 連載目次
    "c019.html",  # 史料目録
    "c021.html",  # 指定文化財一覧
    "c033.html",  # 集合知とは
    "c034.html",  # 全記事一覧
}

# タイトルのキーワード抽出時に無視する一般語
STOPWORDS = {
    "磐田", "磐田市", "物語", "ものがたり", "アーカイブ", "記憶", "歴史",
    "地域", "解説", "記事", "年表", "図解",
}

MAX_LINKS = 6
MIN_SCORE = 2.0
EXCERPT_LEN = 62


def load_ledger():
    data = json.loads((ROOT / "data" / "pages.json").read_text(encoding="utf-8-sig"))
    ledger = {}
    for p in data.get("pages", []):
        url = p.get("url", "")
        if p.get("status") == "published":
            ledger[url] = p
    return ledger


def extract_meta(html):
    m = re.search(r"<title>([^<]*)</title>", html)
    title = m.group(1).strip() if m else ""
    # サイト名サフィックスを除去
    title = re.sub(r"\s*[|｜]\s*磐田物語(アーカイブ)?\s*$", "", title)
    d = re.search(
        r'<meta\s+name="description"\s+content="([^"]*)"', html
    ) or re.search(r'<meta\s+content="([^"]*)"\s+name="description"', html)
    desc = d.group(1).strip() if d else ""
    return title, desc


def keywords(text):
    """漢字2文字以上・カタカナ3文字以上の連なりをキーワードとして抽出する。"""
    toks = re.findall(r"[一-鿿々]{2,}|[゠-ヿ]{3,}", text)
    out = set()
    for t in toks:
        if t in STOPWORDS:
            continue
        out.add(t)
        # 長い複合語は前後2文字も部分キーワードとして持つ（「池田荘」↔「池田」等）
        if len(t) > 2:
            for sub in (t[:2], t[-2:]):
                if sub not in STOPWORDS:
                    out.add(sub)
    return out


def build_index():
    ledger = load_ledger()
    pages = {}
    for f in sorted(ROOT.glob("[a-z][0-9][0-9][0-9].html")):
        name = f.name
        with open(f, encoding="utf-8", newline="") as fh:  # 改行コードを保持
            html = fh.read()
        if re.search(r'http-equiv="refresh"', html, re.I):
            continue  # 移転スタブ
        title, desc = extract_meta(html)
        if not title:
            continue
        entry = ledger.get(name, {})
        prefix = name[0]
        districts = set(entry.get("district") or [])
        if not districts and prefix in PREFIX_DISTRICT:
            districts = {PREFIX_DISTRICT[prefix]}
        summary = entry.get("summary") or desc
        pages[name] = {
            "file": f,
            "html": html,
            "title": title,
            "excerpt": summary,
            "themes": set(entry.get("themes") or []),
            "districts": districts,
            "prefix": prefix,
            "num": int(name[1:4]),
            "published_at": entry.get("published_at") or "",
            "kw_title": keywords(title),
            "kw_desc": keywords(desc + " " + (entry.get("summary") or "")),
            "functional": name in FUNCTIONAL_PAGES,
            # 手書きの関連記事見出し判定（自動挿入ブロックは除外して判定する）
            "has_manual_related": bool(
                re.search(
                    r"<h[23][^>]*>\s*関連記事",
                    re.sub(
                        re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
                        "", html, flags=re.S,
                    ),
                )
            ),
        }
    return pages


def score(a, b):
    s = 0.0
    s += 3.0 * len(a["themes"] & b["themes"])
    if a["districts"] & b["districts"]:
        s += 2.0
    s += 1.5 * min(len(a["kw_title"] & b["kw_title"]), 3)
    s += 0.5 * min(len(a["kw_desc"] & b["kw_desc"]), 4)
    if a["prefix"] == b["prefix"]:
        s += 0.5
        if abs(a["num"] - b["num"]) <= 3:
            s += 1.0  # 同シリーズの前後回
    return s


def pick_related(name, pages):
    me = pages[name]
    cands = []
    for other, p in pages.items():
        if other == name or p["functional"]:
            continue
        sc = score(me, p)
        if sc >= MIN_SCORE:
            cands.append((sc, p["published_at"], other))
    cands.sort(key=lambda x: (-x[0], x[1], x[2]))
    picked = [c[2] for c in cands[:MAX_LINKS]]
    if len(picked) < 3:  # 候補が少ない場合は同地区の新しい記事で補完
        fallback = [
            (p["published_at"], other)
            for other, p in pages.items()
            if other != name and other not in picked and not p["functional"]
            and (me["districts"] & p["districts"])
        ]
        fallback.sort(reverse=True)
        for _, other in fallback:
            if len(picked) >= MAX_LINKS:
                break
            picked.append(other)
    return picked


def esc(s):
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def trim(s, n=EXCERPT_LEN):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


STYLE = """
  .im-related{margin:56px auto 0;max-width:860px;padding:0 20px;font-family:"Zen Kaku Gothic New",system-ui,sans-serif;}
  .im-related h2#im-related-title{font-family:"Shippori Mincho",serif;font-size:22px;letter-spacing:.08em;color:#1f3a48;margin:0 0 6px;padding-left:14px;border-left:4px solid #2f7fa3;background:none;}
  .im-related .im-related-lead{margin:0 0 18px;font-size:13.5px;color:#5c7482;letter-spacing:.03em;}
  .im-related ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}
  .im-related li{margin:0;}
  .im-related a{display:block;height:100%;background:#fff;border:1px solid #d9e4ea;border-radius:10px;padding:14px 16px;text-decoration:none;transition:border-color .2s,box-shadow .2s;}
  .im-related a:hover{border-color:#2f7fa3;box-shadow:0 3px 10px rgba(31,58,72,.08);}
  .im-related .im-related-t{display:block;font-size:15px;font-weight:700;line-height:1.6;color:#1f3a48;}
  .im-related a:hover .im-related-t{color:#2f7fa3;}
  .im-related .im-related-d{display:block;margin-top:6px;font-size:12.5px;line-height:1.7;color:#5c7482;}
  @media(max-width:640px){.im-related ul{grid-template-columns:1fr;}.im-related h2{font-size:20px;}}
""".strip("\n")


def render_section(items, pages):
    lis = []
    for name in items:
        p = pages[name]
        excerpt = trim(p["excerpt"]) if p["excerpt"] else ""
        d = (
            f'<span class="im-related-d">{esc(excerpt)}</span>' if excerpt else ""
        )
        lis.append(
            f'    <li><a href="/{name}">'
            f'<span class="im-related-t">{esc(p["title"])}</span>{d}</a></li>'
        )
    lis_html = "\n".join(lis)
    return f"""{MARK_START}
<section class="im-related" aria-labelledby="im-related-title">
  <style>
{STYLE}
  </style>
  <h2 id="im-related-title">関連記事</h2>
  <p class="im-related-lead">この記事とあわせて読みたい、磐田物語の読みものです。</p>
  <ul>
{lis_html}
  </ul>
</section>
{MARK_END}"""


def insert_section(html, section):
    if "\r\n" in html:  # 元ファイルの改行コードに合わせる
        section = section.replace("\n", "\r\n")
    # 既存の自動セクションがあれば置き換え
    if MARK_START in html and MARK_END in html:
        pattern = re.escape(MARK_START) + r".*?" + re.escape(MARK_END)
        return re.sub(pattern, lambda _: section, html, count=1, flags=re.S)
    for anchor in ('<section class="local-property-note"', '<footer class="im-foot">', "</body>"):
        idx = html.find(anchor)
        if idx != -1:
            return html[:idx] + section + "\n\n" + html[idx:]
    return None


def main():
    pages = build_index()
    stats = Counter()
    for name, p in sorted(pages.items()):
        if p["functional"]:
            stats["skip_functional"] += 1
            continue
        if p["has_manual_related"]:
            stats["skip_manual"] += 1
            continue
        related = pick_related(name, pages)
        if not related:
            stats["skip_no_candidates"] += 1
            continue
        section = render_section(related, pages)
        new_html = insert_section(p["html"], section)
        if new_html is None:
            stats["skip_no_anchor"] += 1
            print(f"  [warn] 挿入位置が見つからない: {name}", file=sys.stderr)
            continue
        if new_html != p["html"]:
            with open(p["file"], "w", encoding="utf-8", newline="") as fh:
                fh.write(new_html)
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1
    print(f"対象記事: {len(pages)}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
