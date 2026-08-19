from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from check_heading_density import content_body, resolve_page, text_length


ROOT = Path(__file__).resolve().parents[1]
DATES = {"2026-08-17", "2026-08-18", "2026-08-19"}
FORBIDDEN = re.compile(
    r"参考資料には書名だけ|最終査読|四千.{0,3}八千字|本文内部リンク|"
    r"機械検査|URL整合|構造化データ|再生成ツール|手書き外部リンク|"
    r"画像座標|公開台帳|判読台帳|調査台帳|校訂作業用台帳|"
    r"更新作業では|公開後.{0,80}更新履歴|内部リンクは|今後の更新では|"
    r"更新履歴として公開|公開ページも|挿図も.{0,80}配置|記事公開後"
)
SOURCE_SCOPE = {f"s{i:03d}.html" for i in range(2, 13)} | {f"s{i:03d}.html" for i in range(32, 35)}


def target_pages() -> list[dict]:
    pages = json.loads((ROOT / "data/pages.json").read_text(encoding="utf-8"))["pages"]
    return [
        page
        for page in pages
        if page.get("published_at") in DATES or page.get("updated_at") in DATES
    ]


def main() -> int:
    pages = target_pages()
    errors: list[str] = []
    layouts: Counter[str] = Counter()
    placements: Counter[str] = Counter()
    long_count = 0
    article_count = 0

    for page in pages:
        path = resolve_page(page.get("url"))
        if path is None:
            errors.append(f"{page.get('url')}: HTMLなし")
            continue
        raw = path.read_text(encoding="utf-8")
        body = content_body(raw)
        if body is None:
            errors.append(f"{page['url']}: 本文コンテナなし")
            continue
        chars = text_length(body)
        if page.get("content_type") == "article":
            article_count += 1
            if not 4000 <= chars <= 8000:
                errors.append(f"{page['url']}: 記事本文{chars}字（4,000～8,000字外）")

        visible = re.sub(r"<[^>]+>", " ", body)
        hit = FORBIDDEN.search(visible)
        if hit:
            errors.append(f"{page['url']}: 内部命令語句「{hit.group(0)}」")

        if page.get("content_type") != "article":
            continue
        long_count += 1
        headings = list(re.finditer(r"<h[23]\b[^>]*>.*?</h[23]>", body, re.I | re.S))
        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
            section_chars = text_length(body[heading.end():end])
            if section_chars < 1000:
                errors.append(f"{page['url']}: 見出し{index + 1}区間{section_chars}字")
                break

        links = re.findall(r"href=[\"'](/(?!assets/|#)[^\"']+)[\"']", body, re.I)
        if len(links) < 3:
            errors.append(f"{page['url']}: 本文内部リンク{len(links)}本")
        if not re.search(r"<table\b", body, re.I):
            errors.append(f"{page['url']}: 表なし")
        if not re.search(r"class=[\"'][^\"']*(?:refs|sources)[^\"']*[\"']|参考資料", raw):
            errors.append(f"{page['url']}: 参考資料なし")
        if not re.search(r"史料.{0,8}(?:限界|読み分け)|確度|未確認", body):
            errors.append(f"{page['url']}: 史料限界の明示なし")
        if "更新履歴" not in raw:
            errors.append(f"{page['url']}: 更新履歴なし")

        figures = re.findall(
            r"<figure\b[^>]*class=[\"'][^\"']*\barticle-guide\b[^\"']*[\"'][^>]*>.*?</figure>",
            body,
            re.I | re.S,
        )
        if len(figures) != 1:
            errors.append(f"{page['url']}: 記事挿絵{len(figures)}点（1点必須）")
        else:
            kind_match = re.search(r"\bguide-([a-z]+)\b", figures[0])
            if not kind_match:
                errors.append(f"{page['url']}: 挿絵レイアウト種別なし")
            else:
                layouts[kind_match.group(1)] += 1
            image = re.search(r"<img\b[^>]*src=[\"']([^\"']+)[\"'][^>]*>", figures[0], re.I)
            if not image or not re.search(r"alt=[\"'][^\"']+[\"']", image.group(0), re.I):
                errors.append(f"{page['url']}: 挿絵src/alt不備")
            else:
                svg = ROOT / image.group(1).lstrip("/")
                if not svg.exists():
                    errors.append(f"{page['url']}: 挿絵SVGなし")
                else:
                    try:
                        tree = ET.parse(svg).getroot()
                        ns = {"s": "http://www.w3.org/2000/svg"}
                        if tree.find("s:title", ns) is None or tree.find("s:desc", ns) is None:
                            errors.append(f"{page['url']}: SVG title/descなし")
                    except ET.ParseError as exc:
                        errors.append(f"{page['url']}: SVG不正 {exc}")
            pos = body.find(figures[0])
            preceding = body[:pos]
            h2_before = len(re.findall(r"<h2\b", preceding, re.I))
            if re.search(r'<div class="tablewrap">[^<]*(?:<table\b.*?</table>)?</div>\s*$', preceding, re.S):
                placements["after-table"] += 1
            elif h2_before == 0:
                placements["before-first-h2"] += 1
            else:
                placements[f"after-h2-{h2_before}"] += 1

        canonical = re.search(r"<link\b[^>]*rel=[\"']canonical[\"'][^>]*href=[\"']([^\"']+)", raw, re.I)
        og = re.search(r"<meta\b[^>]*property=[\"']og:url[\"'][^>]*content=[\"']([^\"']+)", raw, re.I)
        expected = "https://iwata-monogatari.net/" + str(page["url"]).lstrip("/")
        if not canonical or not og or canonical.group(1) != og.group(1) or canonical.group(1) != expected:
            errors.append(f"{page['url']}: canonical/og:url/台帳URL不一致")

        paragraphs = [
            re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", item))
            for item in re.findall(r"<p\b[^>]*>(.*?)</p>", body, re.I | re.S)
        ]
        repeated = [text for text, count in Counter(p for p in paragraphs if len(p) >= 80).items() if count > 1]
        if repeated:
            errors.append(f"{page['url']}: 同一段落重複{len(repeated)}件")

        if path.name in SOURCE_SCOPE:
            refs = re.search(r'<section class="refs">.*?</section>', raw, re.S)
            ref_text = refs.group(0) if refs else ""
            if not (re.search(r"\d+[～〜-]\d+(?:・\d+[～〜-]\d+)?頁", ref_text) and re.search(r"PDF画像\d+(?:[～〜・-]\d+)?枚目", ref_text)):
                errors.append(f"{page['url']}: 参考資料の頁/PDF画像範囲なし")

    if len(layouts) < 5:
        errors.append(f"挿絵レイアウトが{len(layouts)}種のみ")
    if layouts and max(layouts.values()) / sum(layouts.values()) > 0.60:
        errors.append(f"挿絵レイアウト偏重: {layouts}")
    if len(placements) < 3:
        errors.append(f"挿絵配置が{len(placements)}種のみ")

    print(f"recent quality audit: targets={len(pages)}, articles={article_count}, long={long_count}")
    print("layouts:", ", ".join(f"{k}={v}" for k, v in sorted(layouts.items())))
    print("placements:", ", ".join(f"{k}={v}" for k, v in sorted(placements.items())))
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(" - " + error)
        return 1
    print("OK: recent publication quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
