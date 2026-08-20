from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha1
from html import unescape
import json
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[1]


def resolve(url: str) -> Path | None:
    rel = str(url or "").split("?", 1)[0].split("#", 1)[0].lstrip("/").rstrip("/")
    candidates = [ROOT / rel, ROOT / f"{rel}.html", ROOT / rel / "index.html"]
    return next((p for p in candidates if p.is_file()), None)


def clean(fragment: str) -> str:
    fragment = re.sub(r"<(script|style|nav|footer)\b.*?</\1>", " ", fragment, flags=re.I | re.S)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def content(raw: str) -> str:
    articles = len(re.findall(r"<article\b", raw, re.I))
    match = None
    if articles == 1:
        match = re.search(r"<article\b[^>]*>(.*?)</article>", raw, re.I | re.S)
    if match is None:
        match = re.search(r"<main\b[^>]*>(.*?)</main>", raw, re.I | re.S)
    if match is None:
        match = re.search(r"<body\b[^>]*>(.*?)(?:<footer\b|</body>)", raw, re.I | re.S)
    return match.group(1) if match else ""


def attr(tag: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*(['\"])(.*?)\1", tag, re.I | re.S)
    return unescape(match.group(2)).strip() if match else ""


def svg_topology(path: Path) -> str:
    root = ET.parse(path).getroot()
    parts = []
    for node in root.iter():
        name = node.tag.rsplit("}", 1)[-1]
        if name in {"title", "desc", "text", "tspan"}:
            parts.append(f"<{name}>")
            continue
        attrs = []
        for key, value in sorted(node.attrib.items()):
            key = key.rsplit("}", 1)[-1]
            if key in {"id", "aria-labelledby", "aria-label"}:
                continue
            attrs.append(f"{key}={value}")
        parts.append(f"<{name} {' '.join(attrs)}>")
    return sha1("\n".join(parts).encode()).hexdigest()


def main() -> int:
    pages = json.loads((ROOT / "data/pages.json").read_text(encoding="utf-8"))["pages"]
    exempt = set(json.loads((ROOT / "data/content-quality-exemptions.json").read_text(encoding="utf-8"))["pages"])
    records = []
    paragraph_owners: dict[str, set[str]] = defaultdict(set)
    paragraph_text: dict[str, str] = {}
    page_paragraph_hashes: dict[str, list[str]] = {}
    title_owners: dict[str, list[str]] = defaultdict(list)
    h1_owners: dict[str, list[str]] = defaultdict(list)
    desc_owners: dict[str, list[str]] = defaultdict(list)
    image_owners: dict[str, set[str]] = defaultdict(set)
    svg_shapes: dict[str, set[str]] = defaultdict(set)
    broken_links = []
    broken_images = []
    missing_alt = []
    missing_caption = []
    metadata = []
    weak_sources = []
    memo_like = []
    pipeline_prose = []
    missing_sources = []
    seen = set()

    # 「未確認」は史料批判上の正当な確度表示なので、作業予定とは数えない。
    memo_re = re.compile(r"今後|確認したい|記録したい|整理したい|明記したい|残したい|照合したい|調査項目|追加資料|追加調査|更新では")
    pipeline_re = re.compile(r"機械検査|品質ゲート|本文内部リンク|公開ページも|記事公開後|このページの更新|更新作業では|再生成ツール|記事を完成形として")
    weak_source_re = re.compile(r"^(?:磐田市|静岡県|文化庁|国土地理院)?(?:公式)?(?:サイト|ホームページ|公開資料|関連資料|文化財資料|郷土資料|各ページ|資料)$")

    for page in pages:
        if not page.get("count_as_knowledge"):
            continue
        path = resolve(page.get("url", ""))
        if path is None:
            metadata.append(f"{page.get('url')}: file missing")
            continue
        key = path.relative_to(ROOT).as_posix()
        if key in seen:
            continue
        seen.add(key)
        raw = path.read_text(encoding="utf-8", errors="replace")
        body = content(raw)
        title = clean((re.search(r"<title>(.*?)</title>", raw, re.I | re.S) or [None, ""])[1])
        h1s = [clean(x) for x in re.findall(r"<h1\b[^>]*>(.*?)</h1>", raw, re.I | re.S)]
        desc_tag = re.search(r'<meta\b(?=[^>]*\bname=["\']description["\'])(?=[^>]*\bcontent=["\']([^"\']*)["\'])[^>]*>', raw, re.I)
        desc = clean(desc_tag.group(1)) if desc_tag else ""
        canonical = re.search(r'<link\b(?=[^>]*\brel=["\']canonical["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>', raw, re.I)
        expected_base = "https://iwata-monogatari.net/" + str(page.get("url", "")).lstrip("/").removesuffix(".html")
        if not title or len(h1s) != 1 or not desc or not canonical:
            metadata.append(f"{key}: title={bool(title)} h1={len(h1s)} desc={bool(desc)} canonical={bool(canonical)}")
        elif canonical.group(1).rstrip("/").removesuffix(".html") != expected_base.rstrip("/"):
            metadata.append(f"{key}: canonical mismatch {canonical.group(1)}")
        title_owners[title].append(key)
        if h1s:
            h1_owners[h1s[0]].append(key)
        desc_owners[desc].append(key)

        paragraphs = [clean(p) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", body, re.I | re.S)]
        paragraphs = [p for p in paragraphs if len(p) >= 80]
        page_paragraph_hashes[key] = []
        for paragraph in paragraphs:
            digest = sha1(re.sub(r"\d+", "#", paragraph).encode()).hexdigest()
            paragraph_owners[digest].add(key)
            paragraph_text[digest] = paragraph
            page_paragraph_hashes[key].append(digest)
        if key not in exempt and paragraphs:
            memo_count = sum(bool(memo_re.search(p)) for p in paragraphs)
            if memo_count >= 3 and memo_count / len(paragraphs) >= 0.28:
                memo_like.append((key, memo_count, len(paragraphs)))
            hits = sorted({m.group(0) for p in paragraphs for m in pipeline_re.finditer(p)})
            if hits:
                pipeline_prose.append((key, hits))

        source_sections = re.findall(r'<(?:section|div)\b[^>]*class=["\'][^"\']*\b(?:sources|refs|references)\b[^"\']*["\'][^>]*>(.*?)</(?:section|div)>', raw, re.I | re.S)
        source_sections += re.findall(r'<p\b[^>]*>.*?(?:主な参考|参考資料|出典|資料情報).*?</p>\s*<ul\b[^>]*>(.*?)</ul>', raw, re.I | re.S)
        source_text = " ".join(source_sections)
        source_items = [clean(x) for x in re.findall(r"<li\b[^>]*>(.*?)</li>", source_text, re.I | re.S)]
        specific = [x for x in source_items if ("『" in x or "「" in x or re.search(r"\d{4}|頁|巻|号|編|著|発行|https?://", x)) and not weak_source_re.match(x)]
        body_chars = len(re.sub(r"\s+", "", clean(body)))
        if key not in exempt and body_chars >= 2500:
            if not source_sections and not re.search(r"参考資料|出典|資料情報", raw):
                missing_sources.append(key)
            elif len(specific) < 2:
                weak_sources.append((key, len(source_items), len(specific)))

        for href in re.findall(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', body, re.I):
            if not href.startswith("/") or href.startswith("//") or href.startswith("/#"):
                continue
            target = href.split("#", 1)[0].split("?", 1)[0]
            if target and resolve(target) is None and not (ROOT / "_redirects").read_text(encoding="utf-8", errors="ignore").find(target) >= 0:
                broken_links.append((key, href))

        figure_blocks = re.findall(r"<figure\b[^>]*>.*?</figure>", body, re.I | re.S)
        figure_img_tags = {tag for block in figure_blocks for tag in re.findall(r"<img\b[^>]*>", block, re.I | re.S)}
        for tag in re.findall(r"<img\b[^>]*>", body, re.I | re.S):
            src = attr(tag, "src")
            if not src:
                broken_images.append((key, "missing src"))
                continue
            image_owners[src].add(key)
            if not attr(tag, "alt"):
                missing_alt.append((key, src))
            if src.startswith("/") and not src.startswith("//"):
                image_path = ROOT / src.lstrip("/")
                if not image_path.is_file():
                    broken_images.append((key, src))
                elif image_path.suffix.lower() == ".svg":
                    try:
                        svg_shapes[svg_topology(image_path)].add(src)
                    except ET.ParseError:
                        broken_images.append((key, src + " invalid SVG"))
            if tag in figure_img_tags:
                block = next((x for x in figure_blocks if tag in x), "")
                if not re.search(r"<figcaption\b", block, re.I):
                    missing_caption.append((key, src))
        records.append((key, body_chars, len(paragraphs)))

    duplicate_titles = {k: v for k, v in title_owners.items() if k and len(v) > 1}
    duplicate_h1s = {k: v for k, v in h1_owners.items() if k and len(v) > 1}
    duplicate_descs = {k: v for k, v in desc_owners.items() if k and len(v) >= 3}
    repeated_paragraphs = {k: v for k, v in paragraph_owners.items() if len(v) >= 3}
    repeated_paragraph_pages = Counter(page for owners in repeated_paragraphs.values() for page in owners)
    repeated_paragraph_ratios = []
    for page, hashes in page_paragraph_hashes.items():
        total = sum(len(paragraph_text[h]) for h in hashes)
        repeated = sum(len(paragraph_text[h]) for h in hashes if h in repeated_paragraphs)
        if total and repeated / total >= 0.20:
            repeated_paragraph_ratios.append((page, round(repeated / total, 3), repeated_paragraph_pages[page]))
    topology_clusters = sorted((len(v), sorted(v)) for v in svg_shapes.values() if len(v) >= 5)
    duplicate_h1_similarity = []
    body_by_page = {key: re.sub(r"\s+", "", clean(content((ROOT / key).read_text(encoding="utf-8", errors="replace")))) for key, _, _ in records}
    for heading, owners in duplicate_h1s.items():
        for index, left in enumerate(owners):
            for right in owners[index + 1:]:
                ratio = SequenceMatcher(None, body_by_page.get(left, ""), body_by_page.get(right, ""), autojunk=False).ratio()
                if ratio >= 0.70:
                    duplicate_h1_similarity.append((left, right, round(ratio, 3), heading))

    report = {
        "knowledge_pages": len(records),
        "metadata_issues": metadata,
        "duplicate_title_groups": duplicate_titles,
        "duplicate_h1_groups": duplicate_h1s,
        "high_similarity_same_h1_pairs": duplicate_h1_similarity,
        "duplicate_description_groups": duplicate_descs,
        "broken_internal_links": broken_links,
        "broken_images": broken_images,
        "missing_alt": missing_alt,
        "missing_figure_captions": missing_caption,
        "missing_sources": missing_sources,
        "weak_source_pages": weak_sources,
        "memo_like_pages": memo_like,
        "pipeline_prose_pages": pipeline_prose,
        "repeated_paragraph_groups": len(repeated_paragraphs),
        "pages_with_3plus_repeated_paragraphs": sorted((p, n) for p, n in repeated_paragraph_pages.items() if n >= 3),
        "pages_with_20pct_repeated_paragraphs": sorted(repeated_paragraph_ratios),
        "repeated_paragraph_examples": sorted(
            ((len(owners), paragraph_text[digest][:500], sorted(owners)) for digest, owners in repeated_paragraphs.items()),
            reverse=True,
        ),
        "svg_topology_clusters": topology_clusters,
        "shared_image_assets_10plus": sorted((len(v), src, sorted(v)) for src, v in image_owners.items() if len(v) >= 10),
    }
    output = Path(tempfile.gettempdir()) / "iwata-deep-quality-audit.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("deep audit complete")
    for name in (
        "metadata_issues", "duplicate_title_groups", "duplicate_h1_groups",
        "duplicate_description_groups", "high_similarity_same_h1_pairs", "broken_internal_links", "broken_images",
        "missing_alt", "missing_figure_captions", "missing_sources",
        "weak_source_pages", "memo_like_pages", "pipeline_prose_pages",
        "pages_with_3plus_repeated_paragraphs", "pages_with_20pct_repeated_paragraphs", "svg_topology_clusters",
        "shared_image_assets_10plus",
    ):
        print(f"{name}: {len(report[name])}")
    print(f"repeated_paragraph_groups: {len(repeated_paragraphs)}")
    print(f"report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
