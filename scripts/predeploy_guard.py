import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_URLS = [
    "/c051.html",
    "/c052.html",
    "/c053.html",
    "/m055.html",
    "/m056.html",
    "/c090.html",
    "/c091.html",
    "/c092.html",
    "/m121.html",
    "/m122.html",
]

MIN_HOME_COUNT = 421

PROTECTED_TITLE_FRAGMENTS = {
    "/c051.html": "磐田駅から消えた二つの鉄路",
    "/c052.html": "中泉軌道とは何だったのか",
    "/c053.html": "旧東海道を走った軌道",
    "/m055.html": "見付に残る幻の城",
    "/m056.html": "城之崎城とは何か",
}


def load_json(relative_path):
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def normalize_url(url):
    return "/" + url.lstrip("/")


def fail(message):
    print(f"publish guard failed: {message}", file=sys.stderr)
    return 1


def main():
    pages_data = load_json("data/pages.json")
    pages = pages_data["pages"]
    latest = load_json("data/new-articles.json")
    index_html = read_text("index.html")
    middleware_js = read_text("functions/_middleware.js")

    urls = [normalize_url(item.get("url", "")) for item in pages]
    duplicates = sorted({url for url in urls if urls.count(url) > 1})
    if duplicates:
        return fail("duplicate page urls: " + ", ".join(duplicates))

    page_by_url = {normalize_url(item.get("url", "")): item for item in pages}
    missing = [url for url in REQUIRED_URLS if url not in page_by_url]
    if missing:
        return fail("missing required urls: " + ", ".join(missing))

    missing_files = [url for url in REQUIRED_URLS if not (ROOT / url.lstrip("/")).exists()]
    if missing_files:
        return fail("missing article files: " + ", ".join(missing_files))

    for url, fragment in PROTECTED_TITLE_FRAGMENTS.items():
        title = page_by_url[url].get("title", "")
        html = read_text(url.lstrip("/"))
        if fragment not in title or fragment not in html:
            return fail(f"protected article changed unexpectedly: {url}")

    latest_urls = [item.get("url", "") for item in latest[:5]]
    missing_from_home = [url for url in latest_urls if url not in index_html]
    if missing_from_home:
        return fail("latest articles missing from home: " + ", ".join(missing_from_home))

    count_match = re.search(
        r'class="philosophy-band__count">\s*<span class="num">(\d+)</span>',
        index_html,
    )
    if not count_match:
        return fail("home article count was not found")

    home_count = int(count_match.group(1))
    if home_count < MIN_HOME_COUNT:
        return fail(f"home article count went backwards: {home_count} < {MIN_HOME_COUNT}")

    if "site_fragments" not in middleware_js or "fetchFooterFromDb" not in middleware_js:
        return fail("footer middleware is not reading from DB")

    if not (ROOT / "partials" / "footer.html").exists():
        return fail("footer fallback partial is missing")

    suspect_texts = ["????????", "??????????", "???"]
    for relative_path in ["index.html", "updates.html", "data/pages.json"]:
        text = read_text(relative_path)
        if any(suspect in text for suspect in suspect_texts):
            return fail(f"mojibake-like question marks found in {relative_path}")

    print("publish guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
