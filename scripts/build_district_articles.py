"""地区別入口ページ「記事を探す」ブロックを data/pages.json から静的生成し、
対象の 0100X-*.html に注入する。

使い方:
    python scripts/build_district_articles.py --district 01001
    python scripts/build_district_articles.py            # 9地区すべて

生成物はコメントマーカー <!-- district-articles:start/end --> の間に
冪等に上書きされる。ページ側のそれ以外のブロック（三つの入口／時間の
道しるべ／文化財表／成り立ち等）には一切触れない。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_JSON = ROOT / "data" / "pages.json"
PER_PAGE = 50
SUMMARY_MAX = 40

# 生の themes 値 -> 表示ラベル。既存の地区ページ内スクリプト（カード表示時代）の
# THEME_MAP をそのまま踏襲しつつ、pages.json に実在するのに未対応だった値
# （shrine, archives, shugo 等）を追加した（2026-07-15 テーマ空欄解消対応）。
THEME_MAP = {
    "shiryo": "史料", "reference-list": "史料", "archives": "史料",
    "old-map": "古地図", "old-photo": "古地図",
    "village-history": "町村沿革", "shugo": "町村沿革", "self-government": "町村沿革",
    "shrine-temple": "神社仏閣", "temple": "神社仏閣", "shrine": "神社仏閣",
    "festival": "祭り",
    "road-traffic": "街道・交通", "railway": "街道・交通", "transportation": "街道・交通",
    "post-town": "街道・交通", "military-transport": "街道・交通",
    "architecture": "建物・古民家",
    "school": "学校", "education": "学校", "school-history": "学校",
    "old-system-middle-school": "学校", "coeducation": "学校",
    "international-exchange": "学校", "science-education": "学校",
    "club-activities": "学校", "iwata-minami": "学校",
    "life": "暮らし", "agriculture": "暮らし", "industry": "暮らし",
    "water": "暮らし", "craft": "暮らし", "mingei": "暮らし", "commerce": "暮らし",
    "land-memory": "土地の記憶", "place-name": "土地の記憶",
    "terrain": "土地の記憶", "archaeology": "土地の記憶",
}
THEME_ORDER = [
    "史料", "古地図", "町村沿革", "神社仏閣", "祭り",
    "街道・交通", "建物・古民家", "学校", "暮らし", "土地の記憶",
]

# テーブルの「テーマ」列専用の短縮表記（折り返し防止）。フィルターボタンの
# 正式名称はそのまま使い、この短縮形は表示テキストにのみ用いる。
SHORT_LABEL = {
    "史料": "史料", "古地図": "地図", "町村沿革": "沿革", "神社仏閣": "社寺",
    "祭り": "祭り", "街道・交通": "交通", "建物・古民家": "建物",
    "学校": "学校", "暮らし": "暮らし", "土地の記憶": "記憶",
}

# themes に手がかりが無い（"reading" のみ／空）記事向けの個別テーマ指定。
# タイトル・meta descriptionを確認したうえで設定（2026-07-15）。
THEME_OVERRIDE = {
    "m007.html": ["祭り"],   # 見付天神裸祭・起源をめぐる三つの説
    "m008.html": ["祭り"],   # 見付天神裸祭・神事の構造と日程
    "m009.html": ["祭り"],   # 見付天神裸祭・無形文化財としての継承
    "m062.html": ["街道・交通"],  # 見付宿の東木戸・西木戸・高札場
    "m082.html": ["街道・交通"],  # 見付の坂道・辻・曲がり角
    "m083.html": ["街道・交通"],  # 見付の路地裏と生活道路
    "m084.html": ["暮らし"],      # 見付の水路・井戸・生活用水
    "m085.html": ["建物・古民家"],  # 見付の旧家・屋号・家並み
    "m086.html": ["建物・古民家"],  # 見付の町家・蔵・商家建築
    "m087.html": ["神社仏閣"],    # 見付の寺町と寺院配置
    "m088.html": ["建物・古民家"],  # 見付の古写真・絵葉書から消えた建物を復元する
    "m102.html": ["神社仏閣"],    # 矢奈比賣神社と見付天神
    "m112.html": ["史料"],        # 磐田文庫と幕末・明治の地域知性
    "m113.html": ["学校"],        # 旧見付学校以前の寺子屋教育
    "m114.html": ["学校"],        # 見付地区の学校史と地域教育
    "m115.html": ["学校"],        # 校歌・学校区から見る見付の地域意識
    "m116.html": ["土地の記憶"],  # 家康が見付から浜松へ移った理由
    "m117.html": ["土地の記憶"],  # 城之崎城が完成していた場合の歴史IF
    "m118.html": ["街道・交通"],  # 見付宿の助郷制度と周辺村の負担
    "m119.html": ["街道・交通"],  # 見付宿の成立と宿場範囲
    "m120.html": ["古地図"],      # 見付宿を愛宕神社から俯瞰する（絵葉書）
    "m133.html": ["街道・交通"],  # 徳川家康と三方原合戦 ── 見付を通った遠江攻略
}

START_MARK = "<!-- district-articles:start -->"
END_MARK = "<!-- district-articles:end -->"

# 旧カード実装時代の末尾スクリプト（var DISTRICT_ID ... の即時関数）を除去するための境界。
OLD_SCRIPT_RE = re.compile(
    r"\n<script>\n\(function\(\)\{\n  var DISTRICT_ID.*?\n\}\)\(\);\n</script>\n",
    re.DOTALL,
)

# 旧カードグリッド実装専用で、表形式移行後は参照されなくなる各ページ<style>内のCSS。
OLD_INLINE_CSS_BLOCK_RE = re.compile(
    r"\.filter-chips\{[^\n]*\}\n"
    r"\.chip\{[^\n]*\}\n"
    r"\.chip\.active\{[^\n]*\}\n"
    r"\.article-count\{[^\n]*\}\n"
    r"\.article-grid\{[^\n]*\}\n"
    r"\.article-card\{[^\n]*\}\n"
    r"\.article-card \.tag\{[^\n]*\}\n"
    r"\.article-card a\{[^\n]*\}\n"
    r"\.article-card p\{[^\n]*\}\n"
    r"\.article-card\.hidden\{[^\n]*\}\n"
    r"\.article-loading\{[^\n]*\}\n"
)
OLD_INLINE_CSS_MEDIA_LINE_RE = re.compile(r"[ \t]*\.article-grid\{grid-template-columns:1fr\}\n")

CSS_LINK = '<link rel="stylesheet" href="/assets/css/district-articles.css">'
JS_TAG = '<script defer src="/assets/js/district-articles.js"></script>'


class BuildError(RuntimeError):
    pass


def load_pages_json():
    with PAGES_JSON.open("r", encoding="utf-8", newline="") as f:
        return json.load(f)


def truncate_summary(text):
    text = (text or "").strip()
    if len(text) <= SUMMARY_MAX:
        return text
    return text[:SUMMARY_MAX] + "…"


def theme_labels_for(page):
    labels = []
    for raw in page.get("themes") or []:
        label = THEME_MAP.get(raw)
        if label and label not in labels:
            labels.append(label)
    if not labels:
        labels = list(THEME_OVERRIDE.get(page.get("url") or "", []))
    labels.sort(key=lambda l: THEME_ORDER.index(l))
    return labels


def short_theme_display(labels):
    return "／".join(SHORT_LABEL.get(l, l) for l in labels)


def collect_district_pages(data, district_id):
    pages = [
        p for p in data["pages"]
        if district_id in (p.get("district") or []) and p.get("status") == "published"
    ]

    # published_at 降順・同日は url 昇順で安定させる（stable sort を2段階で利用）。
    pages.sort(key=lambda p: p.get("url") or "")
    pages.sort(key=lambda p: p.get("published_at") or "", reverse=True)
    return pages


def esc(text):
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_rows_html(pages):
    rows = []
    for idx, p in enumerate(pages):
        no = idx + 1
        page_no = idx // PER_PAGE + 1
        hidden_attr = " hidden" if page_no > 1 else ""
        labels = theme_labels_for(p)
        data_themes = esc(" ".join(labels))  # フィルターボタンとの突合は正式名称のまま
        # 表示は列幅に収まる短縮形を「／」区切りで連結する（「街道・交通」等の
        # 正式名称自体に「・」を含むため、正式名称のまま連結すると境界が曖昧になる
        # うえ、複数テーマが並ぶと折り返してしまうため）。
        theme_display = esc(short_theme_display(labels))
        title = esc(p.get("title") or "")
        url = esc(p.get("url") or "")
        summary = esc(truncate_summary(p.get("summary") or ""))
        published = p.get("published_at") or ""
        date_disp = published.replace("-", ".")
        rows.append(
            f'<tr data-themes="{data_themes}" data-page="{page_no}"{hidden_attr}>'
            f'<td class="col-no">{no}</td>'
            f'<td class="col-title"><a href="/{url}">{title}</a></td>'
            f'<td class="col-theme">{theme_display}</td>'
            f'<td class="col-desc">{summary}</td>'
            f'<td class="col-date"><time datetime="{esc(published)}">{esc(date_disp)}</time></td>'
            f"</tr>"
        )
    return "\n        ".join(rows)


def build_filter_html():
    buttons = ['<button type="button" class="is-active" data-theme="all" aria-pressed="true">すべて</button>']
    for label in THEME_ORDER:
        buttons.append(
            f'<button type="button" data-theme="{esc(label)}" aria-pressed="false">{esc(label)}</button>'
        )
    return "\n    ".join(buttons)


def build_pager_html(total, total_pages):
    if total_pages <= 1:
        nums = '<li><button type="button" class="is-current" data-page-to="1" aria-current="page">1</button></li>'
        status = f"1〜{total}件目／全{total}件（1／1ページ）"
        return (
            '<nav class="article-pager" aria-label="記事一覧のページ送り" hidden>\n'
            '    <button type="button" data-page-prev disabled>前へ</button>\n'
            f'    <ol class="pager-nums">{nums}</ol>\n'
            '    <button type="button" data-page-next disabled>次へ</button>\n'
            f'    <p class="pager-status">{status}</p>\n'
            "  </nav>"
        )
    items = []
    for i in range(1, total_pages + 1):
        cls = ' class="is-current" aria-current="page"' if i == 1 else ""
        items.append(f'<li><button type="button"{cls} data-page-to="{i}">{i}</button></li>')
    shown_end = min(PER_PAGE, total)
    status = f"1〜{shown_end}件目／全{total}件（1／{total_pages}ページ）"
    return (
        '<nav class="article-pager" aria-label="記事一覧のページ送り">\n'
        '    <button type="button" data-page-prev disabled>前へ</button>\n'
        f'    <ol class="pager-nums">{"".join(items)}</ol>\n'
        '    <button type="button" data-page-next>次へ</button>\n'
        f'    <p class="pager-status">{status}</p>\n'
        "  </nav>"
    )


def build_jsonld(name, pages):
    top = pages[:20]
    elements = []
    for idx, p in enumerate(top):
        elements.append({
            "@type": "ListItem",
            "position": idx + 1,
            "url": f"https://iwata-monogatari.net/{p.get('url')}",
            "name": p.get("title") or "",
        })
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{name}の記事一覧",
        "itemListElement": elements,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def bare_name(district):
    # data/pages.json の districts[].name は「見付地区」のように末尾に「地区」が
    # 付いた形で入っている。既存ページの見出し・リード文は「見付の記事を探す」
    # 「見付地区に関係する」のように地名だけを使う体裁なので、ここで剥がす。
    name = district["name"]
    if name.endswith("地区"):
        return name[: -len("地区")]
    return name


def build_section(district, pages):
    name = bare_name(district)
    district_id = district["district_id"]
    total = len(pages)

    if total == 0:
        body = '<p class="article-placeholder">この地区の読み物は準備中です。</p>'
        return (
            f"{START_MARK}\n"
            f"<h2>{esc(name)}の記事を探す</h2>\n"
            f'<p class="section-lead">{esc(name)}地区に関係する読み物・特集・史料ページを、随時追加していきます。</p>\n\n'
            f'<section class="district-articles" id="articles" data-district="{esc(district_id)}">\n'
            f"  {body}\n"
            f"</section>\n"
            f"{END_MARK}\n"
        )

    total_pages = max(1, -(-total // PER_PAGE))
    rows_html = build_rows_html(pages)
    filter_html = build_filter_html()
    pager_html = build_pager_html(total, total_pages)
    jsonld = build_jsonld(name, pages)

    return (
        f"{START_MARK}\n"
        f"<h2>{esc(name)}の記事を探す</h2>\n"
        f'<p class="section-lead">{esc(name)}地区に関係する読み物・特集・史料ページを、新着を上にして並べています。テーマ別に絞り込むこともできます。</p>\n\n'
        f'<section class="district-articles" id="articles" data-district="{esc(district_id)}">\n'
        f'  <div class="article-filter" role="group" aria-label="テーマで絞り込む">\n'
        f"    {filter_html}\n"
        f"  </div>\n\n"
        f'  <p class="article-count" aria-live="polite">表示中：<span data-count>{total}</span>件</p>\n\n'
        f'  <div class="article-table-wrap">\n'
        f'    <table class="article-table">\n'
        f'      <caption class="visually-hidden">{esc(name)}地区の記事一覧</caption>\n'
        f"      <thead>\n"
        f'        <tr><th scope="col" class="col-no">No.</th><th scope="col" class="col-title">タイトル</th>'
        f'<th scope="col" class="col-theme">テーマ</th><th scope="col" class="col-desc">概要</th>'
        f'<th scope="col" class="col-date">公開日</th></tr>\n'
        f"      </thead>\n"
        f"      <tbody>\n"
        f"        {rows_html}\n"
        f"      </tbody>\n"
        f"    </table>\n"
        f"  </div>\n"
        f'  <noscript><style>.district-articles tr[hidden]{{display:table-row !important}}</style></noscript>\n\n'
        f"  {pager_html}\n\n"
        f'  <script type="application/ld+json">{jsonld}</script>\n'
        f"</section>\n"
        f"{END_MARK}\n"
    )


def inject(html, section_html):
    if START_MARK in html and END_MARK in html:
        pattern = re.compile(re.escape(START_MARK) + r".*?" + re.escape(END_MARK) + r"\n?", re.DOTALL)
        html = pattern.sub(section_html, html, count=1)
    else:
        # 初回投入：旧「優先2：記事を探す」ブロック（h2〜article-grid終端の</div>まで）を置き換える。
        old_block_re = re.compile(
            r"<!-- 優先2：記事を探す -->\n<h2>.*?の記事を探す</h2>\n.*?<div class=\"article-grid\"[^>]*>.*?</div>\n",
            re.DOTALL,
        )
        if not old_block_re.search(html):
            raise BuildError("既存の『記事を探す』ブロックが見つからず、初回投入マーカーの設置に失敗しました")
        html = old_block_re.sub(section_html, html, count=1)

    # 旧カード時代の末尾インラインスクリプトと、参照されなくなったインラインCSSを除去
    html = OLD_SCRIPT_RE.sub("\n", html)
    html = OLD_INLINE_CSS_BLOCK_RE.sub("", html)
    html = OLD_INLINE_CSS_MEDIA_LINE_RE.sub("", html)

    if CSS_LINK not in html:
        html = html.replace(
            '<link rel="stylesheet" href="/assets/css/site-header.css">',
            '<link rel="stylesheet" href="/assets/css/site-header.css">\n' + CSS_LINK,
            1,
        )
    if JS_TAG not in html:
        html = html.replace("</body>", JS_TAG + "\n</body>", 1)

    return html


def run_for_district(district, data, dry_run=False):
    page_file = ROOT / district["page"]
    if not page_file.exists():
        raise BuildError(f"地区ページが見つかりません: {district['page']}")

    pages = collect_district_pages(data, district["district_id"])

    # 記事の実ファイルが存在するかここで検証（silent skip 禁止）
    missing = [p["url"] for p in pages if not (ROOT / p["url"]).exists()]
    if missing:
        raise BuildError(f"{district['district_id']}: 実体の無いURLがあります: {missing}")

    section_html = build_section(district, pages)
    with page_file.open("r", encoding="utf-8", newline="") as f:
        html = f.read()
    new_html = inject(html, section_html)

    if not dry_run:
        with page_file.open("w", encoding="utf-8", newline="") as f:
            f.write(new_html)

    print(f"{district['district_id']} ({district['page']}): {len(pages)}件")
    return len(pages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", help="地区分類番号（例: 01001）。省略時は9地区すべて")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = load_pages_json()
    districts = data["districts"]

    if args.district:
        targets = [d for d in districts if d["no"] == args.district]
        if not targets:
            print(f"該当する地区が見つかりません: {args.district}", file=sys.stderr)
            return 1
    else:
        targets = districts

    try:
        for d in targets:
            run_for_district(d, data, dry_run=args.dry_run)
    except BuildError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
