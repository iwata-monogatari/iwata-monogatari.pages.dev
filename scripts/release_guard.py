import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "release-guard.json"
SITE_ORIGIN = "https://iwata-monogatari.net"
SCHEMA_VERSION = 1
LATEST_ARTICLE_LIMIT = 120

PROTECTED_FILES = [
    "AGENTS.md",
    "_redirects",
    "_headers",
    "c034.html",
    "data/new-articles.json",
    "data/pages.json",
    "index.html",
    "package.json",
    "scripts/check_live_sync.py",
    "scripts/predeploy_guard.py",
    "scripts/release_guard.py",
    "sitemap.xml",
    "updates.html",
]

# These URLs are the post-recovery canaries. They protect the current
# 2026-07-16 state even after they fall out of the latest-article window.
PINNED_URLS = [
    "/m056.html",
    "/k006.html",
    "/k056.html",
    "/m132.html",
    "/m133.html",
    "/m134.html",
    "/s023.html",
    "/s024.html",
    "/s025.html",
    "/oishi-iwata-tochi-kiokuroku/05",
]


class ReleaseGuardError(RuntimeError):
    pass


class MissingLiveState(RuntimeError):
    pass


def normalize_url(url):
    return "/" + str(url or "").lstrip("/").rstrip("/")


def display_url(url):
    value = normalize_url(url)
    return "/" if value == "" else value


def rel_path(path):
    return str(path).replace("\\", "/")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    data = path.read_bytes()
    # The same checkout is LF on Cloudflare/Linux and often CRLF on Windows.
    # Normalize text line endings so startup checks do not fail on checkout style.
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256_bytes(data)


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def page_path_for_url(url):
    url = normalize_url(url)
    if url == "/":
        return ROOT / "index.html"
    rel = url.lstrip("/")
    if url.endswith("/"):
        return ROOT / rel / "index.html"
    if not rel.endswith(".html"):
        return ROOT / rel / "index.html"
    return ROOT / rel


def latest_article_urls():
    latest = load_json(ROOT / "data" / "new-articles.json")
    urls = []
    for item in latest[:LATEST_ARTICLE_LIMIT]:
        url = item.get("url")
        if url:
            urls.append(normalize_url(url))
    return urls


def unique_in_order(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def required_policy_urls():
    return unique_in_order([normalize_url(u) for u in PINNED_URLS] + latest_article_urls())


def git_commit():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def registry_summary():
    pages_doc = load_json(ROOT / "data" / "pages.json")
    latest = load_json(ROOT / "data" / "new-articles.json")
    pages = pages_doc.get("pages", [])
    published = [p for p in pages if p.get("status") == "published"]
    knowledge = [
        p
        for p in published
        if p.get("count_as_knowledge") is True
    ]
    archived = [p for p in pages if p.get("status") == "archived"]
    return {
        "pages_total": len(pages),
        "published_pages": len(published),
        "knowledge_pages": len(knowledge),
        "archived_pages": len(archived),
        "new_articles": len(latest),
        "pages_sha256": sha256_file(ROOT / "data" / "pages.json"),
        "new_articles_sha256": sha256_file(ROOT / "data" / "new-articles.json"),
    }


def protected_file_entries(file_paths):
    entries = []
    for item in file_paths:
        path = ROOT / item
        if not path.exists():
            raise ReleaseGuardError(f"protected file is missing: {item}")
        entries.append({
            "path": rel_path(Path(item)),
            "sha256": sha256_file(path),
        })
    return entries


def protected_url_entries(urls):
    entries = []
    for url in urls:
        path = page_path_for_url(url)
        if not path.exists():
            raise ReleaseGuardError(f"protected URL has no file: {url} -> {rel_path(path.relative_to(ROOT))}")
        entries.append({
            "url": display_url(url),
            "path": rel_path(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        })
    return entries


def canonical_payload(state):
    return {
        "schema": state["schema"],
        "generation": state["generation"],
        "policy": state["policy"],
        "summary": state["summary"],
        "protected_files": state["protected_files"],
        "protected_urls": state["protected_urls"],
    }


def state_hash(state):
    data = json.dumps(canonical_payload(state), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(data)


def build_state(generation, urls=None, files=None):
    urls = urls or required_policy_urls()
    files = files or PROTECTED_FILES
    state = {
        "schema": SCHEMA_VERSION,
        "generation": int(generation),
        "generated_at_unix": int(time.time()),
        "git_commit_at_stamp": git_commit(),
        "policy": {
            "latest_article_limit": LATEST_ARTICLE_LIMIT,
            "pinned_urls": [normalize_url(u) for u in PINNED_URLS],
        },
        "summary": registry_summary(),
        "protected_files": protected_file_entries(files),
        "protected_urls": protected_url_entries(urls),
    }
    state["state_hash"] = state_hash(state)
    return state


def load_state():
    if not STATE_PATH.exists():
        raise ReleaseGuardError("data/release-guard.json is missing; run `npm run release:stamp`")
    return load_json(STATE_PATH)


def validate_state_shape(state):
    if state.get("schema") != SCHEMA_VERSION:
        raise ReleaseGuardError("release guard schema mismatch")
    if not isinstance(state.get("generation"), int):
        raise ReleaseGuardError("release guard generation must be an integer")
    for key in ["policy", "summary", "protected_files", "protected_urls", "state_hash"]:
        if key not in state:
            raise ReleaseGuardError(f"release guard field is missing: {key}")


def verify_local_state():
    state = load_state()
    validate_state_shape(state)

    required_urls = set(required_policy_urls())
    guarded_urls = {normalize_url(item.get("url", "")) for item in state["protected_urls"]}
    missing_urls = sorted(required_urls - guarded_urls)
    if missing_urls:
        raise ReleaseGuardError(
            "release guard is stale; missing protected URLs: "
            + ", ".join(missing_urls[:20])
            + (" ..." if len(missing_urls) > 20 else "")
            + "; run `npm run release:stamp`"
        )

    files = [item["path"] for item in state["protected_files"]]
    urls = [item["url"] for item in state["protected_urls"]]
    expected = build_state(state["generation"], urls=urls, files=files)

    if state["summary"] != expected["summary"]:
        raise ReleaseGuardError("registry summary changed; run `npm run release:stamp`")
    if state["protected_files"] != expected["protected_files"]:
        raise ReleaseGuardError("protected file hashes changed; run `npm run release:stamp`")
    if state["protected_urls"] != expected["protected_urls"]:
        raise ReleaseGuardError("protected URL hashes changed; run `npm run release:stamp`")
    if state.get("state_hash") != expected["state_hash"]:
        raise ReleaseGuardError("release guard state_hash is invalid; run `npm run release:stamp`")
    return state


def fetch_live_state():
    url = SITE_ORIGIN + "/data/release-guard.json?cachebust=release-guard"
    req = urllib.request.Request(url, headers={"User-Agent": "release-guard"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
    try:
        return json.loads(body)
    except ValueError as exc:
        raise MissingLiveState("live release guard state is not installed yet") from exc


def check_build():
    local = verify_local_state()
    try:
        live = fetch_live_state()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print("release guard: no live state yet; allowing first guarded deploy")
            return
        raise
    except MissingLiveState:
        print("release guard: no live state yet; allowing first guarded deploy")
        return
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ReleaseGuardError(f"could not fetch live release guard state: {exc}")

    validate_state_shape(live)
    live_gen = int(live["generation"])
    local_gen = int(local["generation"])
    if local_gen < live_gen:
        raise ReleaseGuardError(
            f"ancestor deployment blocked: local generation {local_gen} is older than live generation {live_gen}"
        )
    if local_gen == live_gen and local.get("state_hash") != live.get("state_hash"):
        raise ReleaseGuardError(
            "same release generation has different content; run `npm run release:stamp` to bump generation"
        )


def check_live():
    local = verify_local_state()
    try:
        live = fetch_live_state()
    except MissingLiveState as exc:
        raise ReleaseGuardError(str(exc))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ReleaseGuardError(f"could not fetch live release guard state: {exc}")
    validate_state_shape(live)
    if int(live["generation"]) != int(local["generation"]):
        raise ReleaseGuardError(
            f"live generation {live['generation']} != local generation {local['generation']}"
        )
    if live.get("state_hash") != local.get("state_hash"):
        raise ReleaseGuardError("live release guard hash does not match local")


def stamp():
    previous = 0
    if STATE_PATH.exists():
        try:
            previous = int(load_json(STATE_PATH).get("generation", 0))
        except (ValueError, TypeError, json.JSONDecodeError):
            previous = 0
    generation = int(time.strftime("%Y%m%d%H%M%S", time.localtime()))
    if generation <= previous:
        generation = previous + 1
    state = build_state(generation)
    write_json(STATE_PATH, state)
    print(f"release guard stamped: generation {state['generation']}, {len(state['protected_urls'])} URLs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["stamp", "check-local", "check-build", "check-live"])
    args = parser.parse_args()
    try:
        if args.command == "stamp":
            stamp()
        elif args.command == "check-local":
            state = verify_local_state()
            print(f"release guard local OK: generation {state['generation']}")
        elif args.command == "check-build":
            check_build()
            print("release guard build OK")
        elif args.command == "check-live":
            check_live()
            print("release guard live OK")
    except ReleaseGuardError as exc:
        print(f"release guard failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
