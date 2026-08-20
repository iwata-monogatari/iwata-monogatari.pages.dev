"""公開知識ページの文字量・図版・出典・重複を一括検査する。"""

from collections import defaultdict
from hashlib import sha1
from html import unescape
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MIN_ARTICLE_CHARS = 1800
VISUAL_REQUIRED_CHARS = 2500
TWO_VISUALS_REQUIRED_CHARS = 4000


def resolve_page(url):
    rel = str(url or "").lstrip("/").rstrip("/")
    candidates = (ROOT / rel, ROOT / f"{rel}.html", ROOT / rel / "index.html")
    return next((path for path in candidates if path.is_file()), None)


def plain(fragment):
    fragment = re.sub(
        r"<(?:script|style|nav|footer)\b.*?</(?:script|style|nav|footer)>",
        "",
        fragment,
        flags=re.I | re.S,
    )
    return re.sub(r"\s+", "", unescape(re.sub(r"<[^>]+>", "", fragment)))


def content_body(raw):
    # A number of cultural-property pages use several sibling <article> cards.
    # Selecting only the first card would misclassify the whole page as a thin
    # article, so prefer <main> whenever more than one article is present.
    article_count = len(re.findall(r"<article\b", raw, re.I))
    match = None
    if article_count == 1:
        match = re.search(r"<article\b[^>]*>(.*?)</article>", raw, re.I | re.S)
    if match is None:
        match = re.search(r"<main\b[^>]*>(.*?)</main>", raw, re.I | re.S)
    if not match:
        match = re.search(r"<body\b[^>]*>(.*?)(?:<footer\b|</body>)", raw, re.I | re.S)
    return match.group(1) if match else None


def has_source_scaffolding(raw):
    if re.search(r'<section\b[^>]*class="[^"]*\b(?:sources|refs)\b', raw, re.I):
        return True
    if re.search(r"<(?:h[2-4]|p)\b[^>]*>.*?(?:参考資料|主な資料|出典|資料情報|底本).*?</(?:h[2-4]|p)>", raw, re.I | re.S):
        return True
    source_items = re.findall(
        r"<li\b[^>]*>.*?(?:https?://|href=|『|\d{4}年|史料|報告書).*?</li>",
        raw,
        re.I | re.S,
    )
    return len(source_items) >= 2


def main():
    pages = json.loads((ROOT / "data/pages.json").read_text(encoding="utf-8"))["pages"]
    exclusions = json.loads(
        (ROOT / "data/content-quality-exemptions.json").read_text(encoding="utf-8")
    )["pages"]
    errors = []
    records = []
    owners = defaultdict(set)
    seen = set()

    for page in pages:
        if not page.get("count_as_knowledge"):
            continue
        path = resolve_page(page.get("url"))
        if path is None:
            errors.append(f"{page.get('url')}: HTMLが見つからない")
            continue
        key = path.relative_to(ROOT).as_posix()
        if key in seen:
            continue
        seen.add(key)
        raw = path.read_text(encoding="utf-8", errors="replace")
        body = content_body(raw)
        if body is None:
            errors.append(f"{key}: 本文コンテナを判定できない")
            continue
        text = plain(body)
        paragraphs = [plain(p) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", body, re.I | re.S)]
        paragraphs = [p for p in paragraphs if len(p) >= 80]
        hashes = [sha1(p.encode()).hexdigest() for p in paragraphs]
        for digest in hashes:
            owners[digest].add(key)
        records.append((key, raw, body, text, paragraphs, hashes))

    for key, raw, body, text, paragraphs, hashes in records:
        if key in exclusions:
            item = exclusions[key]
            if len(str(item.get("reason", ""))) < 20 or not item.get("kind"):
                errors.append(f"{key}: 品質除外理由が不十分")
            continue
        chars = len(text)
        visuals = len(re.findall(r"<(?:img|svg)\b", body, re.I))
        if chars < MIN_ARTICLE_CHARS:
            errors.append(f"{key}: 本文{chars}字（最低{MIN_ARTICLE_CHARS}字）")
        if chars >= VISUAL_REQUIRED_CHARS and visuals < 1:
            errors.append(f"{key}: 本文{chars}字だが図版なし")
        if chars >= TWO_VISUALS_REQUIRED_CHARS and visuals < 2:
            errors.append(f"{key}: 本文{chars}字だが図版{visuals}点")
        if chars >= VISUAL_REQUIRED_CHARS and not has_source_scaffolding(raw):
            errors.append(f"{key}: 出典・参考資料への導線なし")
        if max(map(len, paragraphs), default=0) >= 900:
            errors.append(f"{key}: 900字以上の長大段落あり")
        total = sum(map(len, paragraphs))
        repeated = sum(
            len(p) for p, digest in zip(paragraphs, hashes) if len(owners[digest]) >= 3
        )
        if total >= 1500 and repeated / total >= 0.35:
            errors.append(f"{key}: 完全一致定型文の比率{repeated / total:.1%}")
        for src in re.findall(r'<img\b[^>]*\bsrc="(/assets/img/quality-round[34]/[^"]+)"', body, re.I):
            if not (ROOT / src.lstrip("/")).is_file():
                errors.append(f"{key}: 図版ファイルなし {src}")
        for figure in re.findall(r'<figure\b[^>]*class="[^"]*quality-round[34][^"]*".*?</figure>', body, re.I | re.S):
            if not re.search(r'<img\b[^>]*style="[^"]*width:100%;[^"]*height:auto', figure, re.I):
                errors.append(f"{key}: 新規図版にレスポンシブ指定なし")

    unknown = sorted(set(exclusions) - seen)
    for key in unknown:
        errors.append(f"{key}: 品質除外対象が公開知識ページに存在しない")

    if errors:
        print(f"content quality FAILED: {len(errors)} issue(s)")
        for error in errors[:120]:
            print(" - " + error)
        return 1
    print(
        f"content quality OK: {len(records)} knowledge pages, "
        f"{len(exclusions)} justified functional exemptions, "
        f"minimum {MIN_ARTICLE_CHARS} chars, visual/source/duplicate gates passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
