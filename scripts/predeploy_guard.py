import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://iwata-monogatari.net"
EXPECTED_REMOTE_SLUG = "iwata-monogatari/iwata-monogatari.pages.dev"

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

# Low-water-mark floors, kept only as a fallback for when the live-production
# comparison below can't run (e.g. no network). The primary defense against
# silently dropping a published page is verify_no_silent_removal(), which
# diffs against what's actually live and never needs manual updating.
MIN_HOME_COUNT = 620
MIN_PAGES_COUNT = 625
MIN_NEW_ARTICLE_COUNT = 600

PROTECTED_TITLE_FRAGMENTS = {
    "/c051.html": "磐田駅から消えた二つの鉄路",
    "/c052.html": "中泉軌道とは何だったのか",
    "/c053.html": "旧東海道を走った軌道",
    "/m055.html": "見付に残る幻の城",
    "/m056.html": "城之崎城とは何か",
}


class GuardError(RuntimeError):
    pass


def load_json(relative_path):
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def normalize_url(url):
    return "/" + str(url or "").lstrip("/")


def equivalent_url(left, right):
    left = normalize_url(left).rstrip("/")
    right = normalize_url(right).rstrip("/")
    return left == right or left.removesuffix(".html") == right.removesuffix(".html")


def extract_date(value):
    match = re.search(r"\d{4}-\d{2}-\d{2}", str(value or ""))
    return match.group(0) if match else ""


def page_path_for_url(url):
    url = normalize_url(url).split("?", 1)[0]
    rel = url.lstrip("/")
    if not rel:
        return ROOT / "index.html"
    if url.endswith("/"):
        return ROOT / rel / "index.html"
    if not rel.endswith(".html"):
        return ROOT / rel / "index.html"
    return ROOT / rel


def is_archived_stub(page):
    if page.get("status") != "archived":
        return False
    path = page_path_for_url(page.get("url", ""))
    if not path.exists():
        return False
    html = path.read_text(encoding="utf-8", errors="ignore").lower()
    return "noindex" in html


def command(args):
    return subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git_output(args):
    result = command(["git", *args])
    if result.returncode != 0:
        raise GuardError((result.stderr or result.stdout or "git command failed").strip())
    return result.stdout.strip()


def fail(message):
    print(f"publish guard failed: {message}", file=sys.stderr)
    return 1


def hrefs_from_updates(updates_html):
    return [
        normalize_url(match)
        for match in re.findall(
            r'<a\s+class="history-link[^"]*"\s+href="([^"]+)"', updates_html
        )
    ]


def url_path_from_absolute(value):
    value = str(value or "").strip()
    if value.startswith(SITE_ORIGIN):
        return normalize_url(urlparse(value).path)
    if value.startswith("/"):
        return normalize_url(value)
    return ""


def page_declared_urls(html_text):
    values = []
    canonical = re.search(
        r'<link\b(?=[^>]*\brel=["\']canonical["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>',
        html_text,
        re.IGNORECASE,
    )
    if canonical:
        values.append(canonical.group(1))
    og_url = re.search(
        r'<meta\b(?=[^>]*\bproperty=["\']og:url["\'])(?=[^>]*\bcontent=["\']([^"\']+)["\'])[^>]*>',
        html_text,
        re.IGNORECASE,
    )
    if og_url:
        values.append(og_url.group(1))
    return [path for value in values if (path := url_path_from_absolute(value))]


def fetch_live_json(path):
    """Fetch a JSON file from the currently-live production site.

    Cloudflare Pages builds run against a *shallow* clone (verified
    2026-07-15: `git rev-parse --is-shallow-repository` -> true, `git log`
    shows only the commit being built), so there is no parent commit to
    diff against locally. Comparing against what is actually live is the
    only way, at build time, to notice that a change would silently drop
    an already-published page.
    """
    url = SITE_ORIGIN + "/" + path.lstrip("/") + "?cachebust=predeploy-guard"
    req = urllib.request.Request(url, headers={"User-Agent": "predeploy-guard"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_redirect_sources(redirects_text):
    sources = set()
    for line in redirects_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            src = normalize_url(parts[0]).rstrip("/")
            sources.add(src)
            sources.add(src + ".html")
    return sources


def verify_no_silent_removal(label, live_urls, new_urls, redirect_sources):
    """Fail if any URL that is live in production has vanished from the
    incoming build, unless it is explicitly retired via `_redirects`.

    This replaces hand-maintained "recent required URL" lists and count
    floors, which need updating every time new content ships (a real
    source of the busywork this check exists to end) -- comparing against
    what is actually live needs no maintenance and never goes stale.
    """
    new_norm = {normalize_url(u).rstrip("/") for u in new_urls}
    missing = []
    for u in live_urls:
        norm = normalize_url(u).rstrip("/")
        if norm in new_norm:
            continue
        if norm in redirect_sources or (norm + ".html") in redirect_sources:
            continue
        missing.append(u)
    if missing:
        return fail(
            f"{label}: {len(missing)} page(s) live in production would disappear "
            "and have no matching _redirects entry: " + ", ".join(sorted(missing)[:20])
            + (" ..." if len(missing) > 20 else "")
        )
    return 0


def verify_strict_git_state():
    if not (ROOT / ".git").exists():
        raise GuardError("strict deploy requires the canonical Git checkout")

    remote_url = git_output(["config", "--get", "remote.origin.url"])
    if EXPECTED_REMOTE_SLUG not in remote_url.replace("\\", "/"):
        raise GuardError(f"unexpected git origin: {remote_url}")

    branch = git_output(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch != "main":
        raise GuardError(f"deploy must run from main, not {branch}")

    fetch = command(["git", "fetch", "--quiet", "origin", "main"])
    if fetch.returncode != 0:
        raise GuardError(
            "could not refresh origin/main before deploy: "
            + (fetch.stderr or fetch.stdout).strip()
        )

    head = git_output(["rev-parse", "HEAD"])
    origin_main = git_output(["rev-parse", "origin/main"])
    if head != origin_main:
        raise GuardError(
            "local HEAD is not origin/main; run git pull --ff-only or commit and push before deploy"
        )

    tracked_status = git_output(["status", "--porcelain", "--untracked-files=no"])
    if tracked_status.strip():
        raise GuardError(
            "tracked files have uncommitted changes; run build/knowledge-count, commit, and push first:\n"
            + tracked_status
        )


def verify_release_guard_state():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release_guard.py"), "check-build"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        return fail("release generation guard blocked this build")
    return 0


def verify_latest_sync(pages, latest, index_html, updates_html):
    if len(pages) < MIN_PAGES_COUNT:
        return fail(f"page registry count went backwards: {len(pages)} < {MIN_PAGES_COUNT}")

    if len(latest) < MIN_NEW_ARTICLE_COUNT:
        return fail(
            f"new article registry count went backwards: {len(latest)} < {MIN_NEW_ARTICLE_COUNT}"
        )

    latest_keys = [
        (str(item.get("date", "")), str(item.get("published_at", ""))) for item in latest
    ]
    if latest_keys != sorted(latest_keys, reverse=True):
        return fail("data/new-articles.json is not sorted; run `npm run build`")

    latest_urls = [normalize_url(item.get("url", "")) for item in latest]
    latest_keys_for_dup = [
        (str(item.get("date", "")), normalize_url(item.get("url", ""))) for item in latest
    ]
    duplicate_latest = sorted(
        {key for key in latest_keys_for_dup if latest_keys_for_dup.count(key) > 1}
    )
    if duplicate_latest:
        return fail(
            "duplicate same-day new-article entries: "
            + ", ".join(f"{date} {url}" for date, url in duplicate_latest)
        )

    latest_url_set = set(latest_urls)

    page_dates = sorted(
        {
            extract_date(page.get("published_at"))
            for page in pages
            if page.get("status") == "published" and page.get("show_in_updates") is True
        },
        reverse=True,
    )
    recent_dates = set(page_dates[:2])
    missing_recent_pages = []
    recent_pages = []
    for page in pages:
        page_url = normalize_url(page.get("url", ""))
        page_date = extract_date(page.get("published_at"))
        if (
            page.get("status") == "published"
            and page.get("show_in_updates") is True
            and page_date in recent_dates
        ):
            recent_pages.append(page)
            if page_url not in latest_url_set:
                missing_recent_pages.append(page_url)
    if missing_recent_pages:
        return fail(
            "recent published pages missing from data/new-articles.json: "
            + ", ".join(sorted(missing_recent_pages))
            + "; run `npm run build`"
        )

    update_urls = hrefs_from_updates(updates_html)
    expected_update_urls = latest_urls[: min(60, len(latest_urls))]
    if update_urls[: len(expected_update_urls)] != expected_update_urls:
        for idx, expected in enumerate(expected_update_urls):
            actual = update_urls[idx] if idx < len(update_urls) else "(missing)"
            if actual != expected:
                return fail(
                    "updates.html is out of sync with data/new-articles.json at item "
                    f"{idx + 1}: expected {expected}, got {actual}; run `npm run build`"
                )
        return fail("updates.html is out of sync with data/new-articles.json; run `npm run build`")

    latest_urls_top = latest_urls[:5]
    missing_from_home = [url for url in latest_urls_top if url not in index_html]
    if missing_from_home:
        return fail("latest articles missing from home: " + ", ".join(missing_from_home))

    for page in recent_pages:
        page_url = normalize_url(page.get("url", ""))
        path = page_path_for_url(page_url)
        if not path.exists():
            return fail(f"recent page file is missing: {page_url}")
        declared = page_declared_urls(path.read_text(encoding="utf-8", errors="ignore"))
        if declared and not any(equivalent_url(page_url, item) for item in declared):
            return fail(
                f"recent page canonical/og:url mismatch for {page_url}: "
                + ", ".join(declared)
            )

    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict-deploy",
        action="store_true",
        help="also require clean, pushed canonical main checkout before Pages deploy",
    )
    args = parser.parse_args()

    if args.strict_deploy:
        try:
            verify_strict_git_state()
        except GuardError as exc:
            return fail(str(exc))

    release_guard = verify_release_guard_state()
    if release_guard != 0:
        return release_guard

    pages_data = load_json("data/pages.json")
    pages = pages_data["pages"]
    latest = load_json("data/new-articles.json")
    index_html = read_text("index.html")
    updates_html = read_text("updates.html")
    middleware_js = read_text("functions/_middleware.js")
    redirects_text = read_text("_redirects") if (ROOT / "_redirects").exists() else ""
    redirect_sources = parse_redirect_sources(redirects_text)

    try:
        live_pages = fetch_live_json("data/pages.json")
        live_latest = fetch_live_json("data/new-articles.json")
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return fail(
            "could not fetch live production data/pages.json or data/new-articles.json "
            f"to check for silent content loss ({exc}); re-run the build once network "
            "is available rather than skipping this check"
        )

    live_page_urls = [
        p.get("url", "") for p in live_pages.get("pages", []) if p.get("status") == "published"
    ]
    new_page_urls = [
        p.get("url", "")
        for p in pages
        if p.get("status") == "published" or is_archived_stub(p)
    ]
    result = verify_no_silent_removal(
        "data/pages.json (published pages)", live_page_urls, new_page_urls, redirect_sources
    )
    if result != 0:
        return result

    live_article_urls = [a.get("url", "") for a in live_latest]
    new_article_urls = [a.get("url", "") for a in latest]
    result = verify_no_silent_removal(
        "data/new-articles.json", live_article_urls, new_article_urls, redirect_sources
    )
    if result != 0:
        return result

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

    latest_sync = verify_latest_sync(pages, latest, index_html, updates_html)
    if latest_sync != 0:
        return latest_sync

    count_match = re.search(
        r'class="philosophy-band__count">\s*<span class="num"[^>]*>(\d+)</span>',
        index_html,
    )
    if not count_match:
        return fail("home article count was not found")

    home_count = int(count_match.group(1))
    if home_count < MIN_HOME_COUNT:
        return fail(f"home article count went backwards: {home_count} < {MIN_HOME_COUNT}")

    knowledge_check = subprocess.run(
        ["node", str(ROOT / "tools" / "sync-knowledge-count.mjs"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if knowledge_check.returncode != 0:
        print(knowledge_check.stdout, file=sys.stderr)
        print(knowledge_check.stderr, file=sys.stderr)
        return fail(
            "knowledge count is out of sync (data/pages.json vs displayed count / "
            "全記事一覧); run `node tools/sync-knowledge-count.mjs` and commit the result"
        )

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
