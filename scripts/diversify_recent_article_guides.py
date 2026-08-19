from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATES = {"2026-08-17", "2026-08-18", "2026-08-19"}
PALETTE = {
    "timeline": ("#7a4528", "#f4e4d7", "#fffaf4"),
    "terrain": ("#246b78", "#dceff1", "#f7fcfc"),
    "evidence": ("#76532b", "#eee2ce", "#fffaf0"),
    "index": ("#48683a", "#e4eedc", "#fbfdf8"),
    "comparison": ("#6b4a74", "#ede1f0", "#fdf9fe"),
    "layers": ("#465b75", "#e0e8f1", "#fafcff"),
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def lines(text: str, limit: int = 17, maximum: int = 3) -> list[str]:
    text = clean(text)
    chunks: list[str] = []
    while text and len(chunks) < maximum:
        if len(text) <= limit:
            chunks.append(text)
            text = ""
            break
        cut = limit
        for marker in "――・、のとへを":
            pos = text.rfind(marker, 0, limit + 1)
            if pos >= max(6, limit - 5):
                cut = pos + (0 if marker == "――" else 1)
                break
        chunks.append(text[:cut])
        text = text[cut:]
    if text and chunks:
        chunks[-1] += "…"
    return chunks or [""]


def tspans(text: str, x: int, y: int, css: str, limit: int = 17) -> str:
    out = [f'<text x="{x}" y="{y}" class="{css}">']
    for i, line in enumerate(lines(text, limit)):
        dy = 0 if i == 0 else 31
        out.append(f'<tspan x="{x}" dy="{dy}">{html.escape(line)}</tspan>')
    out.append("</text>")
    return "".join(out)


def layout_for(title: str) -> str:
    if re.search(r"小字|地名資料|自治会", title):
        return "index"
    if re.search(r"変遷|誕生|成立|明治|戦後|合併|団地|工場群|新市街", title):
        return "timeline"
    if re.search(r"川|水|橋|堤|低湿地|用排水|悪水|海岸|農漁|浜部|もぐり", title):
        return "terrain"
    if re.search(r"遺跡|古墳|神社|寺|碑|伝承|城|瓦|文書|墓|塚|地蔵", title):
        return "evidence"
    if re.search(r"・|一～|四つ|三つ|二つ", title):
        return "comparison"
    return "layers"


def base(title: str, kind: str) -> tuple[list[str], str, str, str]:
    accent, pale, paper = PALETTE[kind]
    parts = re.split(r"――| ── |──", title, maxsplit=1)
    short = parts[0].strip()
    subtitle = parts[1].strip() if len(parts) > 1 else "地域資料から読み取れる関係"
    head = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 560" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(title)}の挿絵</title>',
        f'<desc id="desc">{html.escape(kind)}形式で記事固有の論点を示す図</desc>',
        '<style>.ttl{font:700 30px "Yu Mincho","Noto Serif JP",serif}.sub{font:500 17px system-ui,sans-serif}.label{font:700 19px "Yu Gothic","Noto Sans JP",sans-serif}.small{font:500 16px system-ui,sans-serif}.num{font:700 17px system-ui,sans-serif;fill:white}</style>',
        f'<rect width="1120" height="560" rx="30" fill="{paper}"/>',
        f'<text x="62" y="62" class="sub" fill="{accent}">磐田物語｜{kind_label(kind)}</text>',
        *[f'<text x="62" y="{108 + i * 38}" class="ttl" fill="#26343c">{html.escape(line)}</text>' for i, line in enumerate(lines(short, 24, 2))],
        f'<text x="62" y="180" class="sub" fill="#596a72">{html.escape(" / ".join(lines(subtitle, 28, 2)))}</text>',
    ]
    return head, accent, pale, paper


def kind_label(kind: str) -> str:
    return {
        "timeline": "年代の流れ",
        "terrain": "土地と水の関係",
        "evidence": "史料の重なり",
        "index": "地名の配置",
        "comparison": "地域の比較",
        "layers": "時代層の断面",
    }[kind]


def make_svg(title: str, headings: list[str], kind: str) -> str:
    normalized_title = re.sub(r"[\s　・―─|｜]", "", clean(title))
    labels = []
    for heading in headings:
        normalized_heading = re.sub(r"[\s　・―─|｜]", "", clean(heading))
        if normalized_heading and normalized_heading != normalized_title and heading not in labels:
            labels.append(heading)
    for fallback in ("確認できる記録", "地域資料の説明", "未確認事項"):
        if len(labels) >= 3:
            break
        labels.append(fallback)
    svg, accent, pale, _ = base(title, kind)
    if kind == "timeline":
        svg.append(f'<path d="M120 360 H1000" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>')
        for i, (x, tx, label) in enumerate(zip((180, 560, 940), (60, 395, 730), labels), 1):
            svg += [f'<circle cx="{x}" cy="360" r="34" fill="{accent}"/>', f'<text x="{x}" y="367" text-anchor="middle" class="num">{i}</text>', tspans(label, tx, 430, "label", 15)]
    elif kind == "terrain":
        svg += [f'<path d="M0 410 C180 330 310 470 505 390 S850 305 1120 390 V560 H0 Z" fill="{pale}"/>', f'<path d="M0 410 C180 330 310 470 505 390 S850 305 1120 390" fill="none" stroke="{accent}" stroke-width="10"/>']
        for i, (x, y, label) in enumerate(zip((90, 420, 750), (250, 315, 235), labels), 1):
            svg += [f'<rect x="{x}" y="{y}" width="280" height="128" rx="20" fill="white" stroke="{accent}" stroke-width="2"/>', f'<circle cx="{x+34}" cy="{y+34}" r="19" fill="{accent}"/>', f'<text x="{x+34}" y="{y+40}" text-anchor="middle" class="num">{i}</text>', tspans(label, x + 65, y + 42, "label", 14)]
    elif kind == "evidence":
        for i, (x, y, w, label) in enumerate(((105, 245, 910, labels[0]), (145, 350, 830, labels[1]), (185, 455, 750, labels[2])), 1):
            svg += [f'<rect x="{x}" y="{y}" width="{w}" height="82" rx="22" fill="{pale if i % 2 else "white"}" stroke="{accent}" stroke-width="2"/>', f'<text x="{x+28}" y="{y+34}" class="small" fill="{accent}">史料層 {i}</text>', tspans(label, x + 150, y + 34, "label", 27)]
    elif kind == "index":
        positions = ((85, 255), (420, 255), (755, 255))
        for i, ((x, y), label) in enumerate(zip(positions, labels), 1):
            svg += [f'<path d="M{x} {y+35} L{x+105} {y} L{x+270} {y+45} L{x+235} {y+220} L{x+45} {y+205} Z" fill="{pale}" stroke="{accent}" stroke-width="3"/>', f'<circle cx="{x+52}" cy="{y+62}" r="20" fill="{accent}"/>', f'<text x="{x+52}" y="{y+68}" text-anchor="middle" class="num">{i}</text>', tspans(label, x + 35, y + 125, "label", 14)]
    elif kind == "comparison":
        svg += [f'<circle cx="405" cy="370" r="155" fill="{pale}" stroke="{accent}" stroke-width="3"/>', f'<circle cx="715" cy="370" r="155" fill="#f5ead8" stroke="{accent}" stroke-width="3"/>', f'<path d="M560 245 A155 155 0 0 1 560 495 A155 155 0 0 1 560 245" fill="#fff" opacity=".82"/>', tspans(labels[0], 275, 350, "label", 13), tspans(labels[1], 675, 350, "label", 13), tspans(labels[2], 500, 390, "small", 10)]
    else:
        for i, (y, label) in enumerate(zip((245, 345, 445), labels), 1):
            svg += [f'<path d="M120 {y} H1000 L950 {y+72} H170 Z" fill="{pale if i % 2 else "white"}" stroke="{accent}" stroke-width="2"/>', f'<text x="155" y="{y+42}" class="small" fill="{accent}">時代層 {i}</text>', tspans(label, 330, y + 42, "label", 25)]
    svg.append("</svg>")
    return "".join(svg)


def reposition(raw: str, figure: str, kind: str) -> str:
    # Re-running the generator must move the guide, not duplicate it.  Older
    # runs may already have a layout-specific class such as ``guide-index``.
    raw = re.sub(
        r'<figure\b[^>]*class="[^"]*\barticle-guide\b[^"]*"[^>]*>.*?</figure>',
        "",
        raw,
        flags=re.S,
    )
    if kind == "comparison":
        m = re.search(r'<p class="lead">.*?</p>', raw, re.S)
        pos = m.end() if m else raw.find("<h2")
    elif kind == "index":
        m = re.search(r'<div class="tablewrap">.*?</div>', raw, re.S)
        pos = m.end() if m else raw.find("<h2")
    elif kind == "terrain":
        m = re.search(r'<h2[^>]*>.*?</h2>.*?</p>', raw, re.S)
        pos = m.end() if m else raw.find("<h2")
    elif kind == "evidence":
        hs = list(re.finditer(r"<h2[^>]*>", raw))
        pos = hs[1].start() if len(hs) > 1 else raw.find("<h2")
    elif kind == "layers":
        hs = list(re.finditer(r"<h2[^>]*>", raw))
        pos = hs[2].start() if len(hs) > 2 else raw.find("<h2")
    else:
        m = re.search(r'<div class="tablewrap">.*?</div>', raw, re.S)
        pos = m.end() if m else raw.find("<h2")
    return raw[:pos] + figure + raw[pos:]


def main() -> None:
    data = json.loads((ROOT / "data/pages.json").read_text(encoding="utf-8"))
    pages = data.get("pages", data)
    counts: Counter[str] = Counter()
    changed = 0
    for page in pages:
        if page.get("updated_at") not in DATES:
            continue
        url = page.get("url", "")
        path = ROOT / url
        if not path.exists() or path.suffix != ".html":
            continue
        raw = path.read_text(encoding="utf-8")
        match = re.search(r'<img[^>]+src="(/assets/img/article-guides/([^"]+\.svg))"', raw)
        if not match:
            body = re.search(r'<(?:article|main)\b[^>]*>(.*?)</(?:article|main)>', raw, re.S)
            if body is None or len(re.sub(r"\s+", "", clean(body.group(1)))) < 4000:
                continue
        title = page["title"]
        article = re.search(r"<article\b[^>]*>(.*?)</article>", raw, re.S)
        main_body = re.search(r"<main\b[^>]*>(.*?)</main>", raw, re.S)
        heading_source = article.group(1) if article else (main_body.group(1) if main_body else raw)
        headings = [clean(m) for m in re.findall(r"<h2[^>]*>(.*?)</h2>", heading_source, re.S)][:3]
        kind = layout_for(title)
        svg_rel = match.group(1).lstrip("/") if match else f"assets/img/article-guides/{path.stem}.svg"
        (ROOT / svg_rel).write_text(make_svg(title, headings, kind), encoding="utf-8")
        caption = f"{kind_label(kind)}として、{'、'.join(headings)}の関係を示します。"
        figure = (
            f'<figure class="article-guide guide-{kind}"><img src="/{svg_rel}" '
            f'alt="{html.escape(title)}を{kind_label(kind)}で示した挿絵" width="1120" height="560" loading="lazy">'
            f'<figcaption>{html.escape(caption)}</figcaption></figure>'
        )
        path.write_text(reposition(raw, figure, kind), encoding="utf-8")
        counts[kind] += 1
        changed += 1
    if changed < 1:
        raise SystemExit("no recent article guides found")
    print(f"diversified {changed} guides: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
