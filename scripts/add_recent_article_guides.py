from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "img" / "article-guides"
DATES = {"2026-08-18", "2026-08-19"}
EXTRA = {"s029.html", "s030.html", "s031.html", "u055.html", "u056.html"}


def plain(fragment: str) -> str:
    fragment = re.sub(r"<script\b.*?</script>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<style\b.*?</style>", "", fragment, flags=re.I | re.S)
    return re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", fragment)))


def text_of(raw: str, tag: str) -> list[str]:
    values = re.findall(rf"<{tag}\b[^>]*>(.*?)</{tag}>", raw, flags=re.I | re.S)
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", v))).strip() for v in values]


def lines(value: str, width: int, limit: int) -> list[str]:
    value = value.replace("――", "｜").replace(" ── ", "｜").replace("──", "｜")
    chunks: list[str] = []
    for part in value.split("｜"):
        part = part.strip()
        while part:
            chunks.append(part[:width])
            part = part[width:]
    return chunks[:limit] or [""]


def palette(name: str) -> tuple[str, str, str]:
    if any(k in name for k in ("水", "川", "橋", "池", "浦")):
        return "#e7f4f7", "#21758a", "#123f4b"
    if any(k in name for k in ("寺", "神社", "観音", "古墳", "遺跡", "瓦")):
        return "#f4eddf", "#8a6230", "#4e351d"
    if any(k in name for k in ("工場", "鉄道", "団地", "市場")):
        return "#edf0f3", "#5d6975", "#29343d"
    return "#eef3e6", "#5f773a", "#34451e"


def svg(title: str, headings: list[str]) -> str:
    bg, accent, ink = palette(title)
    title_lines = lines(title, 22, 3)
    cards = (headings + ["史料上の限界と次の確認"] * 3)[:3]
    title_spans = "".join(
        f'<tspan x="80" dy="{0 if i == 0 else 34}">{html.escape(line)}</tspan>'
        for i, line in enumerate(title_lines)
    )
    blocks: list[str] = []
    for idx, heading in enumerate(cards):
        x = 70 + idx * 350
        label_lines = lines(heading, 17, 3)
        tspans = "".join(
            f'<tspan x="{x + 30}" dy="{0 if i == 0 else 27}">{html.escape(line)}</tspan>'
            for i, line in enumerate(label_lines)
        )
        blocks.append(
            f'<g><rect x="{x}" y="270" width="290" height="170" rx="18" fill="#ffffff" stroke="{accent}" stroke-width="2"/>'
            f'<circle cx="{x + 38}" cy="308" r="18" fill="{accent}"/><text x="{x + 38}" y="315" text-anchor="middle" class="num">{idx + 1}</text>'
            f'<text x="{x + 30}" y="356" class="card">{tspans}</text></g>'
        )
    arrows = (
        f'<path d="M360 355 H408" stroke="{accent}" stroke-width="4" marker-end="url(#arrow)"/>'
        f'<path d="M710 355 H758" stroke="{accent}" stroke-width="4" marker-end="url(#arrow)"/>'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 540" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(title)}の論点図</title><desc id="desc">記事の三つの主要節を順番に示す概念図</desc>
<defs><linearGradient id="bg" x1="0" x2="1"><stop stop-color="{bg}"/><stop offset="1" stop-color="#fffdf7"/></linearGradient><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="{accent}"/></marker></defs>
<style>.ttl{{font:700 28px 'Yu Mincho','Noto Serif JP',serif;fill:{ink}}}.sub{{font:500 17px system-ui,sans-serif;fill:{accent}}}.card{{font:600 20px 'Yu Gothic','Noto Sans JP',sans-serif;fill:{ink}}}.num{{font:700 18px system-ui,sans-serif;fill:white}}</style>
<rect width="1120" height="540" rx="28" fill="url(#bg)"/><path d="M0 178 C220 142 368 214 560 178 S910 142 1120 178" fill="none" stroke="{accent}" stroke-width="3" opacity=".35"/>
<text x="80" y="82" class="sub">磐田物語｜記事の読み方</text><text x="80" y="128" class="ttl">{title_spans}</text>
{''.join(blocks)}{arrows}<text x="560" y="492" text-anchor="middle" class="sub">記録された事実 → 地域の変化 → 史料の限界を分けて読む</text></svg>'''


def figure(stem: str, title: str, headings: list[str]) -> str:
    alt = f"{title}の主要な論点を三段階で示した図"
    caption = "記事の読み方。" + "、".join(headings[:3]) + "を順に整理します。"
    return (
        f'\n<figure class="article-guide"><img src="/assets/img/article-guides/{stem}.svg" '
        f'alt="{html.escape(alt, quote=True)}" width="1120" height="540" loading="lazy">'
        f'<figcaption>{html.escape(caption)}</figcaption></figure>\n'
    )


def main() -> None:
    pages = json.loads((ROOT / "data" / "pages.json").read_text(encoding="utf-8"))["pages"]
    targets = {
        item["url"] for item in pages
        if item.get("content_type") == "article" and item.get("published_at") in DATES
    } | EXTRA
    OUT.mkdir(parents=True, exist_ok=True)
    changed = 0
    for filename in sorted(targets):
        path = ROOT / filename
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        main_match = re.search(r"<main\b.*?</main>", raw, flags=re.I | re.S)
        if not main_match or len(plain(main_match.group(0))) < 4000:
            continue
        titles = text_of(raw, "h1")
        headings = text_of(raw, "h2")[:3]
        if not titles or len(headings) < 2:
            continue
        title = titles[0].replace("\n", " ")
        stem = path.stem
        (OUT / f"{stem}.svg").write_text(svg(title, headings), encoding="utf-8", newline="\n")
        if f'/assets/img/article-guides/{stem}.svg' not in raw:
            lead = re.search(r'<p\b[^>]*class="[^"]*\blead\b[^"]*"[^>]*>.*?</p>', raw, flags=re.I | re.S)
            if not lead:
                continue
            raw = raw[:lead.end()] + figure(stem, title, headings) + raw[lead.end():]
            if ".article-guide{" not in raw:
                css = ".article-guide{margin:28px 0}.article-guide img{display:block;width:100%;height:auto;border:1px solid #d8e8ef;border-radius:16px;background:#fff}.article-guide figcaption{margin-top:8px;font-size:14px;color:#5b6b74}"
                raw = raw.replace("</style>", css + "</style>", 1)
            path.write_text(raw, encoding="utf-8", newline="\n")
            changed += 1
    print(f"article guides: {changed} HTML file(s), {len(list(OUT.glob('*.svg')))} SVG file(s)")


if __name__ == "__main__":
    main()
