"""地区別入口ページ「記事を探す」ブロックの検証（build_district_articles.py 実行後に使う）。

data/pages.json を真実源として期待値を再計算し、生成済みの 0100X-*.html と突合する。
1件でも失敗したら exit 非0（silent skip 禁止）。
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_JSON = ROOT / "data" / "pages.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_district_articles as bda  # noqa: E402

MITSUKE_EXPECTED_COUNT = 115


def load_pages_json():
    with PAGES_JSON.open("r", encoding="utf-8", newline="") as f:
        return json.load(f)


def valid_date(s):
    try:
        y, m, d = s.split("-")
        date(int(y), int(m), int(d))
        return True
    except Exception:
        return False


def verify_district(district, data, errors):
    district_id = district["district_id"]
    page_path = ROOT / district["page"]
    expected_pages = bda.collect_district_pages(data, district_id)
    expected_count = len(expected_pages)

    if district_id == "mitsuke" and expected_count != MITSUKE_EXPECTED_COUNT:
        errors.append(
            f"[{district_id}] 期待件数の想定と不一致: {expected_count} 件 "
            f"(想定 {MITSUKE_EXPECTED_COUNT} 件)"
        )

    for p in expected_pages:
        if not (ROOT / p["url"]).exists():
            errors.append(f"[{district_id}] URLの実体が存在しません: {p['url']}")
        if not valid_date(p.get("published_at") or ""):
            errors.append(f"[{district_id}] published_at が不正: {p.get('url')} = {p.get('published_at')}")
        labels = bda.theme_labels_for(p)
        if any(l not in bda.THEME_ORDER for l in labels):
            errors.append(f"[{district_id}] 表示テーマ語彙の範囲外: {p.get('url')} labels={labels}")
        if not labels:
            errors.append(
                f"[{district_id}] テーマが空欄です（THEME_MAPかTHEME_OVERRIDEに追加してください）: {p.get('url')}"
            )

    if not page_path.exists():
        errors.append(f"[{district_id}] 地区ページが存在しません: {district['page']}")
        return

    with page_path.open("r", encoding="utf-8", newline="") as f:
        html = f.read()

    if expected_count == 0:
        if "article-placeholder" not in html:
            errors.append(f"[{district_id}] 0件地区なのにプレースホルダが見つかりません")
        return

    actual_rows = re.findall(r"<tr data-themes=", html)
    if len(actual_rows) != expected_count:
        errors.append(
            f"[{district_id}] HTML内の行数がpages.jsonの件数と不一致: "
            f"HTML={len(actual_rows)} 件 / pages.json={expected_count} 件"
        )

    count_span = re.search(r'article-count[^>]*>\s*表示中：<span data-count>(\d+)</span>', html)
    if not count_span or int(count_span.group(1)) != expected_count:
        errors.append(f"[{district_id}] 「表示中：N件」の初期値が不一致")

    # ビルド時に埋め込んだ全URLがHTML中に存在するか
    missing_links = [
        p["url"] for p in expected_pages
        if f'href="/{p["url"]}"' not in html
    ]
    if missing_links:
        errors.append(f"[{district_id}] 一覧に現れないURL: {missing_links[:10]}")

    if 'district-articles:start' not in html or 'district-articles:end' not in html:
        errors.append(f"[{district_id}] マーカーコメントが見つかりません")

    if 'var DISTRICT_ID' in html:
        errors.append(f"[{district_id}] 旧カード実装の末尾スクリプトが残存しています")

    if '/assets/css/district-articles.css' not in html:
        errors.append(f"[{district_id}] 共通CSSの<link>がありません")
    if '/assets/js/district-articles.js' not in html:
        errors.append(f"[{district_id}] 共通JSの<script>がありません")


def main():
    data = load_pages_json()
    districts = data["districts"]

    target_no = sys.argv[1] if len(sys.argv) > 1 else None
    if target_no:
        targets = [d for d in districts if d["no"] == target_no]
    else:
        targets = districts

    errors = []
    for d in targets:
        verify_district(d, data, errors)

    if errors:
        print("verify FAILED:", file=sys.stderr)
        for e in errors:
            print(" - " + e, file=sys.stderr)
        return 1

    print(f"verify OK ({len(targets)} district(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
