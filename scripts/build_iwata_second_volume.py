from __future__ import annotations

import html
import json
import re
from pathlib import Path

from iwata_second_volume_admin_data import ARTICLES as ADMIN_ARTICLES
from iwata_second_volume_data import ARTICLES as MIXED_ARTICLES
from iwata_second_volume_education_a_data import ARTICLES as EDUCATION_ARTICLES

ARTICLES = MIXED_ARTICLES + ADMIN_ARTICLES + EDUCATION_ARTICLES

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-24"
BOOK = "『磐田ことはじめ（第二編・現代編）』"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def plain(value: str) -> str:
    return re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", value)))


def grouped_sections(items: list[tuple[str, list[str]]]) -> list[list[tuple[str, list[str]]]]:
    lengths = [sum(len(plain(p)) for p in paragraphs) for _, paragraphs in items]
    groups: list[list[tuple[str, list[str]]]] = []
    current: list[tuple[str, list[str]]] = []
    current_length = 0
    for index, item in enumerate(items):
        current.append(item)
        current_length += lengths[index]
        if current_length >= 1100 and sum(lengths[index + 1 :]) >= 700:
            groups.append(current)
            current = []
            current_length = 0
    if current:
        if groups and current_length < 700:
            groups[-1].extend(current)
        else:
            groups.append(current)
    return groups


def article_html(a: dict) -> str:
    sections = []
    for group in grouped_sections(a["sections"]):
        group_parts = []
        for index, (heading, paragraphs) in enumerate(group):
            label = f"  <h2>{heading}</h2>" if index == 0 else f'  <p class="subheading"><strong>{heading}</strong></p>'
            body = "\n".join(f"    <p>{p}</p>" for p in paragraphs)
            group_parts.append(f"{label}\n{body}")
        sections.append("\n".join(group_parts))
    rows = "\n".join(
        f"<tr><th>{esc(year)}</th><td>{text}</td></tr>" for year, text in a["timeline"]
    )
    related = "\n".join(
        f'    <a href="/{url}">{label}</a>' for url, label in a["related"]
    )
    source_links = "\n".join(
        f'      <li><a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a></li>'
        for url, label in a.get("official_sources", [])
    )
    title = a["title"]
    desc = a["description"]
    slug = a["slug"]
    topics = list(a.get("topics", []))[:3]
    while len(topics) < 3:
        topics.append("追加史料")
    topic_visual = f'''<figure class="evidence-visual"><svg viewBox="0 0 760 220" role="img" aria-labelledby="{slug}-topics-title {slug}-topics-desc"><title id="{slug}-topics-title">{esc(a['short_title'])}の三つの論点</title><desc id="{slug}-topics-desc">{esc('、'.join(topics))}を順に検討する構成図</desc><path d="M130 110H630" stroke="#83b8cf" stroke-width="8" stroke-linecap="round"/><g fill="#fff" stroke="#2f7fa3" stroke-width="4"><circle cx="130" cy="110" r="54"/><circle cx="380" cy="110" r="54"/><circle cx="630" cy="110" r="54"/></g><g fill="#29495a" font-size="17" text-anchor="middle" font-family="sans-serif"><text x="130" y="105">{esc(topics[0][:10])}</text><text x="130" y="128">{esc(topics[0][10:20])}</text><text x="380" y="105">{esc(topics[1][:10])}</text><text x="380" y="128">{esc(topics[1][10:20])}</text><text x="630" y="105">{esc(topics[2][:10])}</text><text x="630" y="128">{esc(topics[2][10:20])}</text></g></svg><figcaption>{esc(a['short_title'])}を、制度・地域での運用・史料の確度に注意して読み進める。</figcaption></figure>'''
    timeline_visual = list(a["timeline"][:3])
    while len(timeline_visual) < 3:
        timeline_visual.append(("未確認", "追加史料で検証"))
    fills = ("#d9edf5", "#e7f1f4", "#f3eee4")
    timeline_cards = "".join(
        f'<g transform="translate({25 + index * 245},30)"><rect width="220" height="125" rx="10" fill="{fills[index]}"/><text x="110" y="38" text-anchor="middle" fill="#2d637c" font-size="18" font-weight="700" font-family="sans-serif">{esc(str(year)[:16])}</text><text x="110" y="70" text-anchor="middle" fill="#29495a" font-size="14" font-family="sans-serif">{esc(plain(text)[:14])}</text><text x="110" y="94" text-anchor="middle" fill="#29495a" font-size="14" font-family="sans-serif">{esc(plain(text)[14:28])}</text></g>'
        for index, (year, text) in enumerate(timeline_visual)
    )
    timeline_figure = f'''<figure class="evidence-visual"><svg viewBox="0 0 760 185" role="img" aria-labelledby="{slug}-timeline-title {slug}-timeline-desc"><title id="{slug}-timeline-title">{esc(a['short_title'])}の年表図</title><desc id="{slug}-timeline-desc">記事中の主要な三時点を示す</desc>{timeline_cards}</svg><figcaption>年表は出来事の前後関係を示す。制度の開始と地域での実施が同時とは限らない。</figcaption></figure>'''
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}｜磐田物語</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:site_name" content="磐田物語">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://iwata-monogatari.net/{slug}">
<meta property="og:locale" content="ja_JP">
<meta name="iwata:title" content="{esc(title)}">
<meta name="iwata:published" content="{DATE}">
<meta name="iwata:category" content="{esc(a['category'])}">
<meta name="iwata:new-article" content="1">
<link rel="canonical" href="https://iwata-monogatari.net/{slug}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/favicon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site-header.css">
<link rel="stylesheet" href="/assets/css/iwata-area-color.css">
<style>
:root{{--kinari:#fffdf7;--cha:#2f7fa3;--matsu:#356f88;--sumi:#22303a;--usuzumi:#5b6b74;--waku:#d8e8ef}}*{{box-sizing:border-box}}body{{margin:0;background:var(--kinari);color:var(--sumi);font:17px/1.95 "Zen Kaku Gothic New",sans-serif}}a{{color:var(--cha);text-decoration:none}}a:hover{{text-decoration:underline}}main{{max-width:820px;margin:auto;padding:0 22px}}.crumb{{font-size:13px;color:var(--usuzumi);padding:20px 0 6px}}.cat{{display:inline-block;font-size:13px;color:var(--matsu);border-left:3px solid var(--cha);padding-left:9px;margin:18px 0 10px}}h1,h2{{font-family:"Shippori Mincho",serif}}h1{{font-size:28px;line-height:1.5;margin:6px 0 28px}}h2{{font-size:22px;color:var(--matsu);margin:42px 0 16px;padding-bottom:9px;border-bottom:2px solid var(--waku)}}p{{margin:0 0 20px}}.lead,.note{{background:#fff;border:1px solid var(--waku);border-radius:8px;padding:20px 22px;margin-bottom:30px}}.note{{font-size:15px}}.subheading,.section-label{{margin-top:30px;color:var(--matsu);font-size:18px}}.evidence-visual{{margin:28px 0}}.evidence-visual svg{{display:block;width:100%;height:auto;background:#fff;border:1px solid var(--waku);border-radius:10px}}figcaption{{font-size:13px;color:var(--usuzumi);margin-top:8px}}.table-wrap{{overflow-x:auto;margin:20px 0 30px}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{border:1px solid var(--waku);padding:10px 12px;text-align:left;vertical-align:top}}th{{white-space:nowrap;color:var(--matsu)}}.related{{display:flex;flex-wrap:wrap;gap:9px;margin:16px 0 34px}}.related a{{border:1px solid var(--waku);background:#fff;border-radius:5px;padding:9px 13px}}.revision-history,.sources{{margin:38px 0}}@media(max-width:600px){{body{{font-size:16px}}h1{{font-size:23px}}h2{{font-size:20px}}}}
</style>
<link rel="stylesheet" href="/assets/css/temple-shrine-ref.css" data-ts-ref-css>
</head>
<body>
<header class="gh-site"></header>
<main>
  <div class="crumb"><a href="/">磐田物語</a> ／ {esc(a['short_title'])}</div>
  <span class="cat">{esc(a['category'])}</span>
  <article>
  <h1>{esc(title)}</h1>
  <div class="lead">{a['lead']}</div>
{topic_visual}
{chr(10).join(sections)}
  <p class="section-label"><strong>年代を整理する</strong></p>
  <div class="table-wrap"><table><tbody>{rows}</tbody></table></div>
{timeline_figure}
  <p class="section-label"><strong>史料の性格と本稿の立場</strong></p>
  <p>{BOOK}は、磐田市役所勤務31年間の経験と行政資料、聞き取りをもとに熊切正次がまとめ、平成8年（1996年）3月に刊行した地域史資料である。本稿が参照したのは同書{esc(a['book_pages'])}頁である。同時代を知る実務者の記録として具体性がある一方、出典注が簡略な箇所、回想と公文書の区別が本文だけでは確定できない箇所もある。</p>
  <p>{a['position']}</p>
  <div class="note">年代・制度名は資料に記された時点を優先した。現在の制度や区域へ直結させず、改称・統合・廃止を別の出来事として扱っている。</div>
  <p class="section-label"><strong>関連記事</strong></p>
  <div class="related">{related}</div>
  <section class="sources"><p class="section-label"><strong>参考資料</strong></p><ul>
    <li>{BOOK}、熊切正次、平成8年（1996年）3月、{esc(a['book_pages'])}頁。</li>
{source_links}
  </ul></section>
  <section class="revision-history"><p class="section-label"><strong>更新履歴</strong></p><ul><li><time datetime="{DATE}">2026年8月24日</time> 初版公開。{BOOK}と公的資料を照合して構成。</li></ul></section>
  </article>
  <section class="local-property-note" aria-label="不動産相談" data-common></section>
</main>
<section class="article-policy" data-common></section>
<footer class="im-foot"></footer>
<script defer src="https://fujigaoka-analytics-worker.hiroyukio0122.workers.dev/tracker.js" data-site="iwata-monogatari" data-fujigaoka-analytics="true"></script>
</body></html>
'''


def main() -> None:
    for article in ARTICLES:
        (ROOT / f"{article['slug']}.html").write_text(article_html(article), encoding="utf-8")
    print(f"generated {len(ARTICLES)} articles")


if __name__ == "__main__":
    main()
