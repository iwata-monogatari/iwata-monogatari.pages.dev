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
# THEME_MAP をそのまま踏襲しつつ、pages.json に実在するのに未対応だった値を
# 追加した（2026-07-15 テーマ空欄解消。見付→全9地区展開時にさらに拡張）。
# 注意: 時代・政治タグ（heian-period, edo-era, medieval-history, sengoku-period,
# bakumatsu 等）はカテゴリではなく副次タグなので意図的にマップしない。それらしか
# 持たない記事は THEME_OVERRIDE でタイトルから個別にカテゴリを与える。
THEME_MAP = {
    "shiryo": "史料", "reference-list": "史料", "archives": "史料",
    "old-map": "古地図", "old-photo": "古地図",
    "village-history": "町村沿革", "shugo": "町村沿革", "self-government": "町村沿革",
    "land-system": "町村沿革",
    "shrine-temple": "神社仏閣", "temple": "神社仏閣", "shrine": "神社仏閣",
    "temple-history": "神社仏閣", "shrine-history": "神社仏閣",
    "folk-belief": "神社仏閣", "akiba-faith": "神社仏閣",
    "festival": "祭り",
    "road-traffic": "街道・交通", "railway": "街道・交通", "transportation": "街道・交通",
    "post-town": "街道・交通", "military-transport": "街道・交通",
    "port-history": "街道・交通", "bridge": "街道・交通", "ferry": "街道・交通",
    "transport": "街道・交通",
    "architecture": "建物・古民家",
    "school": "学校", "education": "学校", "school-history": "学校",
    "old-system-middle-school": "学校", "coeducation": "学校",
    "international-exchange": "学校", "science-education": "学校",
    "club-activities": "学校", "iwata-minami": "学校", "education-history": "学校",
    "life": "暮らし", "agriculture": "暮らし", "industry": "暮らし",
    "water": "暮らし", "craft": "暮らし", "mingei": "暮らし", "commerce": "暮らし",
    "culture": "暮らし", "folk-medicine": "暮らし", "peasant-uprising": "暮らし",
    "fire": "暮らし", "fire-brigade": "暮らし",
    "land-memory": "土地の記憶", "place-name": "土地の記憶",
    "terrain": "土地の記憶", "archaeology": "土地の記憶",
    "castle": "土地の記憶", "military-history": "土地の記憶",
    "geography": "土地の記憶", "nature": "土地の記憶",
    "disaster": "土地の記憶", "disaster-record": "土地の記憶",
    "earthquake": "土地の記憶", "legend": "土地の記憶", "ichidaibanashi": "土地の記憶",
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

    # --- 中泉（01002）---
    "n047.html": ["街道・交通"],  # 磐田駅貨物・工場引込線・専売公社側線
    "n048.html": ["土地の記憶"],  # 中泉御殿と関ヶ原の戦い（家康滞在記録・御殿跡）
    "n049.html": ["神社仏閣"],    # 遠江国分尼寺
    "n050.html": ["街道・交通"],  # 古代東海道と駅家
    "matsuri-fuhachiman-dashi.html": ["祭り"],    # 府八幡宮例大祭 二十町の山車
    "matsuri-fuhachiman-kindai.html": ["祭り"],   # 府八幡宮例大祭 山車祭りの近代史
    "matsuri-fuhachiman-meigyo.html": ["祭り"],   # 府八幡宮例大祭 命魚奉献の儀
    "matsuri-fuhachiman-shinji.html": ["祭り"],   # 府八幡宮例大祭 神事の詳細
    "matsuri-fuhachiman.html": ["祭り"],          # 府八幡宮例大祭【特集】
    "matsuri-kokubunji-gyoretsu.html": ["祭り"],  # 国司参拝行列
    "matsuri-kokubunji-jidai.html": ["祭り"],     # いくつもの時代が重なる祭り
    "matsuri-kokubunji-yoichi.html": ["祭り"],    # 史跡から夜市へ
    "matsuri-kokubunji.html": ["祭り"],           # 遠江国分寺まつり【特集】
    "n002.html": ["神社仏閣"],    # 遠江国分寺とは何か
    "n003.html": ["神社仏閣"],    # なぜ磐田に国分寺が置かれたのか
    "n004.html": ["神社仏閣"],    # 遠江国分寺の伽藍を読む
    "n005.html": ["神社仏閣"],    # 金堂とは何か
    "n006.html": ["神社仏閣"],    # 七重塔とは何か
    "n007.html": ["神社仏閣"],    # 講堂とは何か
    "n008.html": ["神社仏閣"],    # 回廊と中門
    "n009.html": ["神社仏閣"],    # 僧坊と寺院の日常
    "n010.html": ["神社仏閣"],    # 遠江国分寺の瓦を読む
    "n011.html": ["神社仏閣"],    # 遠江国分寺 年表
    "n012.html": ["神社仏閣"],    # 遠江国分寺が人々の暮らしをどう変えたか
    "n013.html": ["神社仏閣"],    # 遠江国分寺を歩く
    "n014.html": ["神社仏閣"],    # 遠江国分寺を復興できないか
    "n015.html": ["神社仏閣"],    # 遠江国分寺を読むための用語集

    # --- 御厨（01003）---
    "c101.html": ["土地の記憶"],  # 源平争乱と遠江（頼朝の挙兵から遠江支配へ）
    "u032.html": ["土地の記憶"],  # 古墳と川・海・道（磐田海・大乃浦と水運）
    "u033.html": ["土地の記憶"],  # 消えた古墳・塚地名の調査
    "u034.html": ["史料"],        # 発掘調査報告書から読む磐田の古代
    "u035.html": ["街道・交通"],  # 三ヶ野坂・物見の松・本多忠勝伝承
    "matsuri-kamada-mushifuji.html": ["祭り"],  # 幼児の虫封じ
    "matsuri-kamada-sengu.html": ["祭り"],      # 御厨十七郷十九社と式年遷宮
    "matsuri-kamada-urayasu.html": ["祭り"],    # 浦安の舞
    "matsuri-kamada-yatai.html": ["祭り"],      # 御厨六地区の屋台と囃子
    "matsuri-kamada.html": ["祭り"],            # 鎌田神明宮大祭【特集】
    "u005.html": ["土地の記憶"],  # 新貝
    "u006.html": ["土地の記憶"],  # 東脇・新出
    "u007.html": ["土地の記憶"],  # 稗原
    "u008.html": ["土地の記憶"],  # 大立野
    "u009.html": ["土地の記憶"],  # 安久路
    "u010.html": ["街道・交通"],  # 三ケ野・三ケ野坂（東海道の難所）
    "u011.html": ["土地の記憶"],  # 富士見台
    "u012.html": ["土地の記憶"],  # 東新屋
    "u013.html": ["土地の記憶"],  # 和口
    "u014.html": ["土地の記憶"],  # 御厨駅と現代の御厨（令和に蘇った地名）
    "u015.html": ["町村沿革"],    # 御厨村の分立と再編
    "u016.html": ["町村沿革"],    # 南御厨村の誕生
    "u017.html": ["町村沿革"],    # 田原村の誕生

    # --- 豊田（01004）---
    "t059.html": ["土地の記憶"],  # 皆川陣屋跡と稲荷山
    "t039.html": ["街道・交通"],  # 旧東海道の一里塚・松並木・木戸
    "t040.html": ["土地の記憶"],  # 一言坂の戦いと磐田の戦場地形
    "t041.html": ["街道・交通"],  # 天竜川の筏流しと木材流通
    "t042.html": ["土地の記憶"],  # 天竜川の堤防・洪水碑・水害記録
    "t016.html": ["街道・交通"],  # 池田宿の賑わいと本陣の記憶
    "t017.html": ["街道・交通"],  # 船頭自治と徳川家康の朱印状
    "t018.html": ["土地の記憶"],  # 金原明善と天竜川治水の足跡
    "t020.html": ["土地の記憶"],  # 小銚子塚古墳と周辺の古墳群
    "t021.html": ["町村沿革"],    # 井通村の成立と近代の教育・水利
    "t022.html": ["町村沿革"],    # 富岡村の開拓と磐田原台地西縁の農業
    "t023.html": ["土地の記憶"],  # 天竜川の「暴れ天竜」と決壊の歴史
    "t024.html": ["神社仏閣", "土地の記憶"],  # 社山の山岳信仰・砦の記憶
    "t025.html": ["祭り"],        # 池田やかた祭りと天白神社の祭礼
    "t026.html": ["町村沿革"],    # 豊田町への合併と近代行政のあゆみ

    # --- 南部（01005）---
    "s021.html": ["土地の記憶"],  # 今之浦と大池の消滅・埋立て
    "s022.html": ["土地の記憶"],  # 今之浦が磐田の都市形成に与えた影響
    "s002.html": ["土地の記憶"],  # 豊島・北島
    "s003.html": ["神社仏閣"],    # 千手堂・万正寺（寺院名が語る中世の信仰空間）
    "s004.html": ["土地の記憶"],  # 上大之郷・下大之郷
    "s005.html": ["土地の記憶"],  # 上岡田・下岡田
    "s006.html": ["土地の記憶"],  # 鮫島・小島
    "s007.html": ["土地の記憶"],  # 野箱・白拍子
    "s008.html": ["暮らし"],      # 浜部（塩田と沿岸漁業）
    "s009.html": ["土地の記憶"],  # 新島・長須賀
    "s010.html": ["土地の記憶"],  # 刑部島
    "s011.html": ["町村沿革"],    # 長野村（南部町村合併）
    "s012.html": ["町村沿革"],    # 於保村（分村編入・合併史）

    # --- 向陽（01006）---
    "k002.html": ["土地の記憶"],  # 新豊院山古墳群
    "k003.html": ["土地の記憶"],  # 米塚古墳群
    "k004.html": ["土地の記憶"],  # 長者屋敷遺跡
    "k005.html": ["土地の記憶"],  # 匂坂城跡と匂坂氏
    "k006.html": ["土地の記憶"],  # 向笠城と向笠氏
    "k007.html": ["暮らし"],      # 寺谷用水の開削（遠州最古の用水路）
    "k008.html": ["土地の記憶"],  # 大久保と藤上原
    "k009.html": ["土地の記憶"],  # 笠梅の歴史
    "k010.html": ["土地の記憶"],  # 平松掛下入作（長大地名）
    "k011.html": ["町村沿革"],    # 「向陽」の誕生（昭和の合併と学校区）

    # --- 竜洋（01007）特集入口（ディレクトリURL）---
    "area/ryuyo/": ["町村沿革"],                    # 竜洋地区の歴史を歩く（特集入口）
    "area/ryuyo/ancient-coast/": ["土地の記憶"],    # 太古の竜洋と大の浦
    "area/ryuyo/former-villages/": ["町村沿革"],    # 掛塚・袖浦・十束
    "area/ryuyo/history/": ["町村沿革"],            # 竜洋町の沿革
    "area/ryuyo/local-leaders/": ["町村沿革"],      # 町や村を背負った人達
    "area/ryuyo/medieval-early-modern/": ["土地の記憶"],  # 室町時代以降の竜洋
    "area/ryuyo/tenryu-river/": ["土地の記憶"],     # 天竜川の変遷と竜洋
    "area/ryuyo/timeline/": ["町村沿革"],           # 竜洋地区年表
}

START_MARK = "<!-- district-articles:start -->"
END_MARK = "<!-- district-articles:end -->"

# 旧カード実装時代の末尾スクリプト（var DISTRICT_ID ... の即時関数）を除去するための境界。
OLD_SCRIPT_RE = re.compile(
    r"\n<script>\n\(function\(\)\{\n  var DISTRICT_ID.*?\n\}\)\(\);\n</script>\n",
    re.DOTALL,
)

# 旧カードグリッド実装専用で、表形式移行後は参照されなくなる各ページ<style>内のCSS。
# 地区により1行圧縮／複数行整形が混在するため、固定の連続ブロックでは取りこぼす
# （豊田・向陽は複数行整形で残存した）。**ルール単位**で、行頭のセレクタ＋{…}を
# 改行をまたいで除去する（`[^}]*` はネスト無しCSSなので最初の } まで安全に取れる）。
# 行頭アンカー(MULTILINE)により、@media 内のインデント付き `.article-grid{...}` は
# 誤爆しない（それは OLD_INLINE_CSS_MEDIA_LINE_RE で別途処理）。
OLD_INLINE_CSS_RULE_RES = [
    re.compile(r"^\.filter-chips\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.chip\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.chip\.active\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-count\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-grid\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-card\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-card \.tag\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-card a\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-card p\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-card\.hidden\{[^}]*\}\n", re.MULTILINE),
    re.compile(r"^\.article-loading\{[^}]*\}\n", re.MULTILINE),
]
OLD_INLINE_CSS_MEDIA_LINE_RE = re.compile(r"[ \t]*\.article-grid\{grid-template-columns:1fr\}\n")

# district-articles.css / .js の内容を変更するたびに繰り上げる。Cloudflare側の
# Cache-Control: max-age=14400 とブラウザキャッシュにより、バージョンを上げない
# 限り既存訪問者に最大4時間、更新前のCSS/JSが配信され続けてしまうため
# （2026-07-15、テーマ列の折り返し修正が反映されない不具合の実因になった）。
ASSET_VERSION = 7
CSS_LINK = f'<link rel="stylesheet" href="/assets/css/district-articles.css?v={ASSET_VERSION}">'
JS_TAG = f'<script defer src="/assets/js/district-articles.js?v={ASSET_VERSION}"></script>'
OLD_CSS_LINK_RE = re.compile(r'<link rel="stylesheet" href="/assets/css/district-articles\.css(?:\?v=\d+)?">\n?')
OLD_JS_TAG_RE = re.compile(r'<script defer src="/assets/js/district-articles\.js(?:\?v=\d+)?"></script>\n?')


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


# --- 初回投入用：旧カード実装の「記事を探す」関連断片を除去する正規表現群 ---
# 見付以外の 0100X ページは開発途中の重複により「記事を探す」ブロックが intro-block・
# 本体・後半と 2〜3 箇所に散在し、間に温存すべきセクション（時間の道しるべ／文化財／
# 成り立ち／人物／CTA）を挟む。これら旧断片だけを class 名で確実に狙って全除去し、
# 最初の位置に新ブロック 1 つへ統合する。温存セクションはこれらの class を持たず無傷。
# 新ブロックの誤爆を防ぐため id="count" 等・旧 class 名に限定している。
PLACEHOLDER = "\x00DISTRICT_ARTICLES_PLACEHOLDER\x00"
FIRST_SEARCH_BLOCK_RE = re.compile(
    r'(?:<!-- 優先2：記事を探す -->\n)?'
    r'(?:<section class="intro-block">\n)?'
    r'<h2>[^<]*の記事を探す</h2>'
)
OLD_SEARCH_FRAGMENT_RES = [
    # intro-block（見出しとリードだけを入れた箱）
    re.compile(
        r'<section class="intro-block">\n<h2>[^<]*の記事を探す</h2>\n'
        r'<p class="section-lead">[^<]*</p>\n</section>\n?'
    ),
    re.compile(r'<!-- 優先2：記事を探す -->\n?'),
    # 記事探しの見出し＋リード文
    re.compile(r'<h2>[^<]*の記事を探す</h2>\n<p class="section-lead">[^<]*</p>\n?'),
    # フィルターチップ（直後に取り残される孤立した </section> ゴミも巻き込む）
    re.compile(r'<div class="filter-chips"[^>]*>.*?</div>\n(?:</section>\n)?', re.DOTALL),
    # 旧件数表示（id="count" 限定＝新ブロックの data-count 版は消さない）
    re.compile(r'<p class="article-count">表示中：<span id="count">\d+</span>件</p>\n?'),
    # 旧カード一覧グリッド
    re.compile(r'<div class="article-grid"[^>]*>.*?</div>\n?', re.DOTALL),
]


def initial_inject(html, section_html):
    """初回投入：旧記事探し断片を位置問わず全除去し、最初の位置へ新ブロック1つを統合する。"""
    match = FIRST_SEARCH_BLOCK_RE.search(html)
    if not match:
        raise BuildError("既存の『記事を探す』ブロックが見つからず、初回投入マーカーの設置に失敗しました")
    # 最初の記事探しブロックの直前に目印を置いてから、旧断片を全除去する。
    html = html[: match.start()] + PLACEHOLDER + "\n" + html[match.start():]
    for pattern in OLD_SEARCH_FRAGMENT_RES:
        html = pattern.sub("", html)
    # 目印を新ブロックへ差し替える（取り残しがあれば除去）。
    html = html.replace(PLACEHOLDER + "\n", section_html, 1)
    html = html.replace(PLACEHOLDER, "")
    return html


def normalize_canonical(html, page):
    """地区ページ自身の canonical / og:url を .html 付きから正式なクリーンURLへ統一する
    （/0100X-slug.html は /0100X-slug へ 308 されるため、正規URLはクリーン側）。冪等。"""
    clean = page[:-5] if page.endswith(".html") else page
    html = html.replace(
        f'href="https://iwata-monogatari.net/{page}"',
        f'href="https://iwata-monogatari.net/{clean}"',
    )
    html = html.replace(
        f'content="https://iwata-monogatari.net/{page}"',
        f'content="https://iwata-monogatari.net/{clean}"',
    )
    return html


def inject(html, section_html):
    if START_MARK in html and END_MARK in html:
        pattern = re.compile(re.escape(START_MARK) + r".*?" + re.escape(END_MARK) + r"\n?", re.DOTALL)
        html = pattern.sub(section_html, html, count=1)
    else:
        html = initial_inject(html, section_html)

    # 旧カード時代の末尾インラインスクリプトと、参照されなくなったインラインCSSを除去
    html = OLD_SCRIPT_RE.sub("\n", html)
    for rule_re in OLD_INLINE_CSS_RULE_RES:
        html = rule_re.sub("", html)
    html = OLD_INLINE_CSS_MEDIA_LINE_RE.sub("", html)

    # 既存のバージョン違いリンクを一旦除去してから、現在のASSET_VERSIONで入れ直す
    # （冪等・かつバージョン番号を上げたときに確実に更新されるようにする）。
    html = OLD_CSS_LINK_RE.sub("", html)
    html = OLD_JS_TAG_RE.sub("", html)

    html = html.replace(
        '<link rel="stylesheet" href="/assets/css/site-header.css">',
        '<link rel="stylesheet" href="/assets/css/site-header.css">\n' + CSS_LINK,
        1,
    )
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
    new_html = normalize_canonical(new_html, district["page"])

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
