"""公開知識記事の本文見出し間隔を検査する。

H2/H3の各見出しから次の本文見出し（最後は本文末）まで、タグを除いた
実本文が1,000文字以上あることを必須とする。1,000文字未満の記事は
本文見出しを置かない。
"""

from html import unescape
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def resolve_page(url):
    rel = str(url or "").lstrip("/").rstrip("/")
    candidates = (ROOT / rel, ROOT / f"{rel}.html", ROOT / rel / "index.html")
    return next((path for path in candidates if path.is_file()), None)


def text_length(fragment):
    fragment = re.sub(
        r"<(?:script|style|nav|footer)\b.*?</(?:script|style|nav|footer)>",
        "",
        fragment,
        flags=re.I | re.S,
    )
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return len(re.sub(r"\s+", "", unescape(fragment)))


def content_body(html):
    match = re.search(r"<article\b[^>]*>(.*?)</article>", html, re.I | re.S)
    if not match:
        match = re.search(r"<main\b[^>]*>(.*?)</main>", html, re.I | re.S)
    if not match:
        match = re.search(
            r"<body\b[^>]*>(.*?)(?:<footer\b|</body>)", html, re.I | re.S
        )
    return match.group(1) if match else None


def main():
    data = json.loads((ROOT / "data" / "pages.json").read_text(encoding="utf-8"))
    pages = [page for page in data["pages"] if page.get("count_as_knowledge")]
    errors = []

    for page in pages:
        path = resolve_page(page.get("url"))
        if path is None:
            errors.append(f"{page.get('url')}: HTMLが見つからない")
            continue
        html = path.read_text(encoding="utf-8")
        body = content_body(html)
        if body is None:
            errors.append(f"{page.get('url')}: 本文コンテナを判定できない")
            continue

        headings = list(
            re.finditer(r"<h[23]\b[^>]*>.*?</h[23]>", body, re.I | re.S)
        )
        chars = text_length(body)
        if len(headings) > chars // 1000:
            errors.append(
                f"{page.get('url')}: 本文{chars}字に対し見出し{len(headings)}件"
            )
            continue

        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
            section_chars = text_length(body[heading.end():end])
            if section_chars < 1000:
                errors.append(
                    f"{page.get('url')}: 見出し{index + 1}の本文が{section_chars}字"
                )
                break

    if errors:
        print(f"heading density FAILED: {len(errors)} article(s)")
        for error in errors[:50]:
            print(" - " + error)
        return 1

    print(f"heading density OK: {len(pages)} article(s), minimum 1,000 chars/heading")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
