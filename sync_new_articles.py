import html
import json
import re
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "new-articles.json"
DISCOVERED_PATH = ROOT / "data" / "new-articles-discovered.json"
INDEX_PATH = ROOT / "index.html"
UPDATES_PATH = ROOT / "updates.html"

INDEX_LIMIT = 22
UPDATES_STATIC_LIMIT = 60
SITE_ORIGIN = "https://iwata-monogatari.net"
SKIP_DIRS = {".git", "assets", "data", "docs", "functions", "images", "img", "saguchi", "work"}
SKIP_FILES = {
    "admin-bbs.html",
    "bbs.html",
    "index.html",
    "updates.html",
}


def read_text(path):
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def load_articles():
    data = load_json_array(DATA_PATH)
    data.extend(discover_articles())

    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

    normalized = []
    seen = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        date = str(item.get("date", "")).strip()
        category = str(item.get("category", "")).strip()
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        if not (date and category and title and url):
            continue
        # (date, url) で重複排除する。同じ記事が再スキャンで別表記の
        # category/title を持って再登録され、二重掲載になるのを防ぐため。
        # 既存分を先に処理するため、手作業で整えた表記が優先して残る。
        key = (date, url)
        if key in seen:
            continue
        seen.add(key)
        # published_at: 同日内の並び順を決める実投稿時刻。既存分は温存し、
        # 新規発見分のみ「今回の同期実行時刻」を暫定値として付与する。
        published_at = str(item.get("published_at", "")).strip() or (
            date + "T00:00:00+09:00"
        )
        normalized.append(
            {
                "date": date,
                "category": category,
                "title": title,
                "url": url,
                "published_at": published_at,
            }
        )

    known_urls = {str(item.get("url", "")).strip() for item in load_json_array(DATA_PATH)}
    for item in normalized:
        if item["url"] not in known_urls:
            item["published_at"] = now_iso

    normalized.sort(key=lambda item: (item["date"], item["published_at"]), reverse=True)
    return normalized


def load_json_array(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def discover_articles():
    discovered = []
    for path in ROOT.rglob("*.html"):
        if should_skip_html(path):
            continue
        item = article_from_html(path)
        if item:
            discovered.append(item)

    write_discovered(discovered)
    return discovered


def should_skip_html(path):
    rel = path.relative_to(ROOT)
    if len(rel.parts) == 1 and rel.name in SKIP_FILES:
        return True
    if len(rel.parts) == 2 and rel.name == "index.html":
        parent_html = ROOT / (rel.parts[0] + ".html")
        if parent_html.exists():
            return True
    if any(part in SKIP_DIRS for part in rel.parts[:-1]):
        return True
    return False


def article_from_html(path):
    text = read_text(path)
    published = first_meta(
        text,
        [
            ("name", "iwata:published"),
            ("name", "article:published_time"),
            ("property", "article:published_time"),
            ("name", "datePublished"),
            ("itemprop", "datePublished"),
        ],
    )
    include_flag = first_meta(text, [("name", "iwata:new-article")])
    if not published and include_flag not in {"1", "true", "yes"}:
        return None

    if not published:
        published = date.today().isoformat()
    published = normalize_date(published)
    if not published:
        return None

    title = (
        first_meta(text, [("name", "iwata:title")])
        or first_meta(text, [("property", "og:title")])
        or first_tag_text(text, "h1")
        or title_from_html(text)
    )
    title = clean_title(title)
    if not title:
        return None

    category = (
        first_meta(text, [("name", "iwata:category")])
        or first_class_text(text, "cat")
        or category_from_body(text)
        or "更新"
    )
    category = clean_category(category)

    url = url_from_html(path, text)
    if not url:
        return None

    return {"date": published, "category": category, "title": title, "url": url}


def first_meta(text, selectors):
    for attr, value in selectors:
        pattern = re.compile(
            rf'<meta\b(?=[^>]*\b{attr}=["\']{re.escape(value)}["\'])(?=[^>]*\bcontent=["\']([^"\']+)["\'])[^>]*>',
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            return html.unescape(match.group(1).strip())
    return ""


def first_tag_text(text, tag):
    match = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return strip_tags(match.group(1))


def first_class_text(text, class_name):
    pattern = re.compile(
        rf'<[^>]*\bclass=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'][^>]*>(.*?)</[^>]+>',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return strip_tags(match.group(1))


def title_from_html(text):
    return first_tag_text(text, "title")


def strip_tags(value):
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def clean_title(value):
    value = strip_tags(value or "")
    value = re.sub(r"\s*[｜|]\s*磐田物語.*$", "", value)
    value = re.sub(r"\s*｜\s*$", "", value)
    return value.strip()


def clean_category(value):
    value = strip_tags(value or "")
    value = re.sub(r"\s*[｜|].*$", "", value).strip()
    return value or "更新"


def normalize_date(value):
    match = re.search(r"\d{4}-\d{2}-\d{2}", value or "")
    return match.group(0) if match else ""


def category_from_body(text):
    match = re.search(r'<body\b[^>]*\bclass=["\']([^"\']+)["\']', text, re.IGNORECASE)
    if not match:
        return ""
    classes = set(match.group(1).split())
    areas = [
        ("area-mitsuke", "見付"),
        ("area-nakaizumi", "中泉"),
        ("area-mikuriya", "御厨"),
        ("area-toyoda", "豊田"),
        ("area-nanbu", "南部"),
        ("area-koyo", "向陽"),
        ("area-ryuyo", "竜洋"),
        ("area-fukude", "福田"),
        ("area-toyooka", "豊岡"),
    ]
    for cls, label in areas:
        if cls in classes:
            return label
    return ""


def url_from_html(path, text):
    canonical = first_link(text, "canonical")
    og_url = first_meta(text, [("property", "og:url")])
    url = canonical or og_url
    if url.startswith(SITE_ORIGIN):
        return url[len(SITE_ORIGIN) :] or "/"
    if url.startswith("/"):
        return url

    rel = path.relative_to(ROOT).as_posix()
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def first_link(text, rel):
    pattern = re.compile(
        rf'<link\b(?=[^>]*\brel=["\']{re.escape(rel)}["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>',
        re.IGNORECASE,
    )
    match = pattern.search(text)
    return html.unescape(match.group(1).strip()) if match else ""


def write_discovered(discovered):
    try:
        DISCOVERED_PATH.write_text(
            json.dumps(discovered, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except PermissionError:
        print(f"Warning: could not write {DISCOVERED_PATH}")


def area_class(item):
    url = item.get("url", "")
    category = item.get("category", "")
    if category in {"磐田共通・資料", "特別コンテンツ"}:
        return ""
    special_urls = {
        "/iwata-nogyo-high-school-history.html": "area-nakaizumi",
        "/iwata-nishi-high-school-history.html": "area-nakaizumi",
        "/iwata-kita-high-school-history.html": "area-mitsuke",
        "/iwata-minami-high-school-history.html": "area-mitsuke",
        "/iwata-higashi-high-school-history.html": "area-mitsuke",
    }
    if url in special_urls:
        return special_urls[url]
    category_areas = [
        ("見付", "area-mitsuke"),
        ("中泉", "area-nakaizumi"),
        ("御厨", "area-mikuriya"),
        ("豊田", "area-toyoda"),
        ("南部", "area-nanbu"),
        ("向陽", "area-koyo"),
        ("竜洋", "area-ryuyo"),
        ("福田", "area-fukude"),
        ("豊岡", "area-toyooka"),
    ]
    for label, cls in category_areas:
        if category.startswith(label):
            return cls
    if url == "/inotani/" or url.startswith("/inotani/"):
        return "area-mitsuke"
    if url == "/c028.html":
        return "area-mitsuke"
    if url == "/u004.html":
        return "area-mikuriya"
    if re.match(r"^/m", url):
        return "area-mitsuke"
    if re.match(r"^/n", url):
        return "area-nakaizumi"
    if re.match(r"^/u", url):
        return "area-mikuriya"
    if re.match(r"^/t", url):
        return "area-toyoda"
    if re.match(r"^/s", url):
        return "area-nanbu"
    if re.match(r"^/k", url):
        return "area-koyo"
    if re.match(r"^/r", url):
        return "area-ryuyo"
    if re.match(r"^/f", url):
        return "area-fukude"
    if re.match(r"^/y", url):
        return "area-toyooka"
    return ""


def index_articles(articles):
    seen_urls = set()
    deduped = []
    for item in articles:
        url = item["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(item)

    present_urls = {item["url"] for item in deduped}
    filtered = []
    child_pattern = re.compile(r"^(/matsuri-[^-]+)-.+\.html$")
    for item in deduped:
        match = child_pattern.match(item["url"])
        if match and f"{match.group(1)}.html" in present_urls:
            continue
        filtered.append(item)
    return filtered


def esc(value):
    return html.escape(value, quote=True)


def render_index_item(item):
    cls = area_class(item)
    district = cls.removeprefix("area-") if cls else ""
    li_attr = f' data-district="{esc(district)}"' if district else ""
    a_cls = f"new-article-link news-link {cls}" if cls else "new-article-link news-link"
    return "\n".join(
        [
            f'          <li class="new-article-item news-item"{li_attr}>',
            f'            <a href="{esc(item["url"])}" class="{esc(a_cls)}">',
            f'              <span class="news-meta"><time class="new-article-date news-date" datetime="{esc(item["date"])}">{esc(item["date"])}</time><span class="new-article-category news-tag">{esc(item["category"])}</span></span>',
            f'              <span class="new-article-title news-title">{esc(item["title"])}</span>',
            '              <span class="new-article-arrow news-arrow" aria-hidden="true">→</span>',
            "            </a>",
            "          </li>",
        ]
    )


def render_update_item(item):
    cls = area_class(item)
    a_cls = f"history-link {cls}" if cls else "history-link"
    return (
        f'      <li class="history-item"><a class="{esc(a_cls)}" href="{esc(item["url"])}">'
        f'<time class="history-date" datetime="{esc(item["date"])}">{esc(item["date"])}</time>'
        f'<span class="history-category">{esc(item["category"])}</span>'
        f'<span class="history-title">{esc(item["title"])}</span></a></li>'
    )


def replace_between(text, start_pattern, end_pattern, replacement):
    start = re.search(start_pattern, text)
    if not start:
        raise ValueError(f"start pattern not found: {start_pattern}")
    end = re.search(end_pattern, text[start.end() :])
    if not end:
        raise ValueError(f"end pattern not found: {end_pattern}")
    end_start = start.end() + end.start()
    return text[: start.end()] + replacement + text[end_start:]


def sync_index(articles):
    html_text = INDEX_PATH.read_text(encoding="utf-8")
    items = "\n" + "\n".join(render_index_item(item) for item in articles[:INDEX_LIMIT]) + "\n"
    html_text = replace_between(
        html_text,
        r'(<ul class="new-article-list news-list" id="new-article-list" aria-label="新着記事一覧">\n)',
        r"        </ul>",
        items,
    )
    INDEX_PATH.write_text(html_text, encoding="utf-8", newline="\n")


def sync_updates(articles):
    html_text = UPDATES_PATH.read_text(encoding="utf-8")
    items = "\n" + "\n".join(render_update_item(item) for item in articles[:UPDATES_STATIC_LIMIT]) + "\n"
    html_text = replace_between(
        html_text,
        r'(<ul class="update-list">\n)',
        r"    </ul>",
        items,
    )
    UPDATES_PATH.write_text(html_text, encoding="utf-8", newline="\n")


def sync_data(articles):
    DATA_PATH.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main():
    articles = load_articles()
    sync_data(articles)
    sync_index(articles)
    sync_updates(articles)
    print(
        f"Synced {len(articles)} articles: "
        f"index fallback {INDEX_LIMIT}, updates fallback {UPDATES_STATIC_LIMIT}"
    )


if __name__ == "__main__":
    main()
