"""Generate the public search corpus and HTML fallbacks using only the standard library.

The allowlist is data/pages.json (published) plus data/blog-posts.json.
No DB, admin content, external full text, filesystem mtime, or guessed readings.
Artifacts are content addressed; write the manifest after every artifact is ready.
Run --check in CI to detect stale artifacts without modifying files.
"""
import argparse
import gzip
import hashlib
import html
import json
import math
import re
import unicodedata
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://iwata-monogatari.net'
SCHEMA = 1
SHARDS = 128
HUBS = [('c130', '鉄道史'), ('c094', '学校史'), ('c016', '祭り'),
        ('c009', '地名・町名の由来'), ('c014', '旧村と合併'), ('c012', '古墳・遺跡'),
        ('c098', '産業史'), ('h001', '戦争の記憶'), ('c131', '古写真・古地図'),
        ('c132', '人物'), ('c133', '神社'), ('c134', '寺院'),
        ('c135', '消えた建物'), ('c136', '道と橋')]
EXCLUDED_PATHS = {'/', '/c034', '/bbs', '/updates', '/404', '/blog/', '/oishi-ronko/'}


def normalize(value):
    value = unicodedata.normalize('NFKC', str(value)).lower()
    value = ''.join(chr(ord(c) - 96) if '\u30a1' <= c <= '\u30f6' else c for c in value)
    return re.sub(r'\s+', ' ', value).strip()


def key(value):
    parsed = urlsplit(value)
    if (parsed.scheme and parsed.scheme not in {'http', 'https'}) or (parsed.netloc and parsed.netloc != 'iwata-monogatari.net'):
        raise ValueError('Not an approved internal URL: ' + value)
    path = '/' + parsed.path.lstrip('/')
    if path.endswith('/index.html'):
        path = path[:-10]
    if path.endswith('.html'):
        path = path[:-5]
    if '.' not in path.rsplit('/', 1)[-1] and path.count('/') == 1:
        path = path.rstrip('/') or '/'
    return path


def local_file(value):
    parsed = urlsplit(value)
    relative = unquote(parsed.path).lstrip('/')
    if '..' in Path(relative).parts or '\\' in relative:
        raise ValueError('Unsafe URL')
    options = [ROOT / relative]
    if relative.endswith('/') or not relative:
        options = [ROOT / relative / 'index.html']
    elif not Path(relative).suffix:
        options += [ROOT / (relative + '.html'), ROOT / relative / 'index.html']
    for candidate in options:
        if candidate.is_file() and candidate.resolve().is_relative_to(ROOT.resolve()):
            return candidate
    raise ValueError('Missing local public file: ' + value)


class Page(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.body = []
        self.scoped = []
        self.headings = []
        self.heading = None
        self.links = []
        self.content_links = []
        self.assets = []
        self.anchors = []
        self.canonical = ''
        self.description = ''
        self.noindex = False
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        classes = set(a.get('class', '').split())
        blocked = (tag in {'script', 'style', 'header', 'footer', 'nav', 'aside', 'noscript'} or
                   bool(classes & {'crumb', 'pager', 'related', 'im-related', 'article-policy', 'local-property-note', 'article-reactions'}))
        if self.stack and self.stack[-1][1]:
            blocked = True
        in_body = tag == 'body' or any(s[0] == 'body' for s in self.stack)
        if tag == 'link' and 'canonical' in a.get('rel', '').split():
            self.canonical = a.get('href', '')
        if tag == 'meta':
            if a.get('name') == 'description':
                self.description = a.get('content', '')
            if a.get('name', '').lower() == 'robots' and 'noindex' in a.get('content', '').lower():
                self.noindex = True
        if a.get('id'):
            self.anchors.append(a['id'])
        if a.get('src'):
            self.assets.append(a['src'])
        if a.get('href'):
            self.links.append(a['href'])
            if in_body and not blocked:
                self.content_links.append(a['href'])
        if tag in {'h1', 'h2', 'h3'} and not blocked:
            self.heading = []
        if tag not in self.VOID:
            self.stack.append((tag, blocked))

    def handle_endtag(self, tag):
        if tag in {'h1', 'h2', 'h3'} and self.heading is not None:
            self.headings.append(' '.join(self.heading))
            self.heading = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        if not self.stack or self.stack[-1][1] or not any(s[0] == 'body' for s in self.stack):
            return
        value = data.strip()
        if not value:
            return
        self.body.append(value)
        if any(s[0] in {'main', 'article'} for s in self.stack):
            self.scoped.append(value)
        if self.heading is not None:
            self.heading.append(value)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')


def stamp(value):
    return hashlib.sha256(value).hexdigest()


def redirect_map():
    redirects = {}
    for line in (ROOT / '_redirects').read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] == '301' and '*' not in parts[0] and parts[1].startswith('/'):
            redirects[key(parts[0])] = key(parts[1])
    return redirects


def resolve(value, redirects):
    value = key(value)
    visited = set()
    while value in redirects:
        if value in visited:
            raise ValueError('Redirect loop: ' + value)
        visited.add(value)
        value = redirects[value]
    return value


def corpus():
    ledger = json.loads((ROOT / 'data/pages.json').read_text(encoding='utf-8'))
    blogs = json.loads((ROOT / 'data/blog-posts.json').read_text(encoding='utf-8'))['posts']
    redirects = redirect_map()
    rows = list(ledger['pages']) + [dict(title=p['title'], url='/blog/' + p['slug'] + '/',
                 summary=p.get('description', ''), status=p.get('status', 'published'), district=[], themes=[],
                 published_at=p['date'], date_provisional=False, source='blog-posts', content_type='blog') for p in blogs]
    blocked_urls = {key(row['url']) for row in rows if row.get('status') != 'published'}
    excluded, inventory, records, bodies = [], [], {}, {}
    for row in rows:
        original_url = row['url']
        url_key = key(original_url)
        if row.get('status') != 'published':
            excluded.append({'url': original_url, 'reason': 'status:' + str(row.get('status', 'unknown'))})
            continue
        if url_key in EXCLUDED_PATHS or url_key.startswith(('/admin', '/api/', '/archive/')):
            excluded.append({'url': original_url, 'reason': 'functional-or-private-path'})
            continue
        target = resolve(original_url, redirects)
        source = local_file(target)
        text = source.read_text(encoding='utf-8-sig')
        page = Page(text)
        if page.noindex:
            excluded.append({'url': original_url, 'reason': 'noindex'})
            continue
        canonical = resolve(page.canonical or target, redirects)
        canonical_file = local_file(canonical)
        if canonical_file != source:
            source = canonical_file
            text = source.read_text(encoding='utf-8-sig')
            page = Page(text)
        if page.noindex or canonical in blocked_urls or canonical in EXCLUDED_PATHS or canonical.startswith(('/admin', '/api/', '/archive/')):
            excluded.append({'url': original_url, 'reason': 'canonical-not-public'})
            continue
        display_body = ' '.join(page.scoped or page.body)
        body = normalize(display_body)
        identifier = canonical.strip('/') or 'home'
        entry = {'id': identifier, 'url': canonical, 'title': row['title'],
                 'description': row.get('summary') or page.description,
                 'headings': page.headings, 'districts': row.get('district', []),
                 'themes': [], 'ledgerThemes': row.get('themes', []),
                 'keywords': row.get('topics', []), 'aliases': [], 'sourceIds': [url_key.strip('/')],
                 'kind': row.get('content_type', 'reading'),
                 'dateProvisional': bool(row.get('date_provisional', True)),
                 'published': row.get('published_at', '') if not row.get('date_provisional', True) else '',
                 'updated': row.get('updated_at', '') if not row.get('date_provisional', True) else '',
                 'body': '/data/search/bodies/' + stamp(encoded({'schemaVersion': SCHEMA, 'id': identifier, 'text': body, 'display': display_body}))[:24] + '.json'}
        if canonical in records:
            previous = records[canonical]
            # Prefer the canonical page's own ledger title, retain real former titles as aliases.
            if url_key == canonical and row.get('source') != 'blog-posts':
                entry['aliases'] = previous['aliases'] + ([previous['title']] if previous['title'] != entry['title'] else [])
                entry['sourceIds'] = sorted(set(previous['sourceIds'] + entry['sourceIds']))
                entry['districts'] = sorted(set(previous['districts'] + entry['districts']))
                records[canonical] = entry
            else:
                previous['sourceIds'] = sorted(set(previous['sourceIds'] + entry['sourceIds']))
                previous['districts'] = sorted(set(previous['districts'] + entry['districts']))
                if entry['title'] != previous['title']:
                    previous['aliases'].append(entry['title'])
        else:
            records[canonical] = entry
        bodies[canonical] = {'text': body, 'display': display_body}
        inventory.append({'original_url': original_url, 'canonical': canonical, 'file': source.relative_to(ROOT).as_posix(),
                          'title': row['title'], 'status': 'published', 'html_sha256': stamp(source.read_bytes()),
                          'body_sha256': stamp(body.encode()), 'anchors': page.anchors,
                          'assets': page.assets, 'links': page.links,
                          'districts': row.get('district', []), 'themes': row.get('themes', []),
                          'date_provisional': entry['dateProvisional']})
    for hub_id, label in HUBS:
        hub = Page(local_file('/' + hub_id).read_text(encoding='utf-8-sig'))
        for link in hub.content_links + ['/' + hub_id]:
            try:
                link_key = resolve(link, redirects)
            except ValueError:
                continue
            if link_key in records and hub_id not in records[link_key]['themes']:
                records[link_key]['themes'].append(hub_id)
    # Explicit editorial update entries are dated changes, unlike filesystem mtime.
    # Use only the authored "・更新" categories, not discovery's generic fallback "更新".
    for update in json.loads((ROOT / 'data/new-articles.json').read_text(encoding='utf-8')):
        if '・更新' not in update.get('category', '') or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', update.get('date', '')):
            continue
        url = resolve(update['url'], redirects)
        if url in records and not records[url]['dateProvisional'] and update['date'] > records[url]['updated']:
            records[url]['updated'] = update['date']
            records[url]['updateDateSource'] = '/data/new-articles.json'
    # Scope dictionary entries to documented district membership or explicit person pages.
    dictionary = []
    for district in ledger['districts']:
        name = district['name'].removesuffix('地区')
        dictionary.append({'entityId': 'district:' + district['district_id'], 'entityType': 'district',
            'preferredLabel': name, 'aliases': [], 'reading': district['kana'],
            'scopeArticleIds': sorted(r['id'] for r in records.values() if district['district_id'] in r['districts']),
            'regionScope': [district['district_id']], 'periodScope': [], 'sourceUrl': '/data/pages.json',
            'sourceNote': '地区台帳に明記されたkana。記事への対応はdistrict値のみ。姓の読みへ適用しない。',
            'verifiedBy': 'Codex:公開台帳と本文の照合', 'verifiedAt': '2026-10-05'})
    dictionary.append({'entityId': 'person:fukuda-hanko', 'entityType': 'person', 'preferredLabel': '福田半香',
        'aliases': [], 'reading': 'ふくだ',
        'scopeArticleIds': sorted(r['id'] for r in records.values() if '福田半香' in r['title']),
        'regionScope': [], 'periodScope': [], 'sourceUrl': '/oishi-ronko/027/',
        'sourceNote': '本文冒頭で姓「福田（ふくだ）」と地名「福田（ふくで）」を区別。名の全文読みは公開本文の明記を要するため姓のみ有効。',
        'verifiedBy': 'Codex:公開本文の照合', 'verifiedAt': '2026-10-05'})
    for entity in dictionary:
        for record in records.values():
            if record['id'] in entity['scopeArticleIds']:
                record.setdefault('entities', []).append(entity['entityId'])
    records = sorted(records.values(), key=lambda r: r['id'])
    gram_shards = [defaultdict(list) for _ in range(SHARDS)]
    for ordinal, record in enumerate(records):
        body = bodies[record['url']]['text']
        for gram in sorted({body[i:i + 2] for i in range(len(body) - 1)}):
            shard = (ord(gram[0]) * 31 + ord(gram[1])) % SHARDS
            gram_shards[shard][gram].append(ordinal)
    return ledger, records, bodies, gram_shards, dictionary, inventory, excluded


def search_form(districts):
    district_options = ''.join(f'<option value="{html.escape(d["district_id"])}">{html.escape(d["name"])}</option>' for d in districts)
    themes = ''.join(f'<option value="{i}">{name}</option>' for i, name in HUBS)
    return f'''<form id="search-form" action="/search/" method="get">
<label for="search-query">地名・人物名・言葉で検索</label>
<div class="query-row"><input id="search-query" name="q" type="search" autocomplete="off" aria-describedby="search-hint"><button type="submit">検索</button></div>
<p id="search-hint">例：光明電気鉄道、ふくで、中泉 軌道。空白で区切ると、すべての言葉を含む記事を探します。</p>
<div class="filter-row"><label for="search-district">地区<select id="search-district" name="district"><option value="">すべての地区</option>{district_options}<option value="common">市全域・共通</option><option value="unknown">地区未分類</option></select></label>
<label for="search-theme">テーマ<select id="search-theme" name="theme"><option value="">すべてのテーマ</option>{themes}<option value="unknown">テーマ未分類</option></select></label>
<label for="search-sort">並び順<select id="search-sort" name="sort"><option value="relevance">関連度</option><option value="newest">新しい順</option><option value="title">題名順</option></select></label></div>
<p class="small">テーマは既存のテーマハブ本文に掲載された記事から絞り込みます。未分類の記事も「すべて」で探せます。</p>
<button type="submit">この条件で探す</button> <a href="/search/help/">記事の探し方</a>
</form>'''


def card(record, districts):
    district_names = {d['district_id']: d['name'] for d in districts} | {'common': '市全域・共通'}
    names = [district_names.get(d, '地区未分類') for d in record['districts']]
    labels = [label for code, label in HUBS if code in record['themes']]
    description = html.escape(record['description'])
    return f'<li class="search-item"><h3><a href="{html.escape(record["url"])}">{html.escape(record["title"])}</a></h3><p>{description}</p><p class="search-meta">{html.escape("・".join(names) or "地区未分類")} ／ {html.escape("・".join(labels) or "テーマ未分類")}</p></li>'


def shell(title, content, canonical, noindex=False, scripts=''):
    header = (ROOT / 'partials/header.html').read_text(encoding='utf-8')
    result = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} ｜ 磐田物語</title><meta name="description" content="磐田物語の公開記事とブログを、言葉・テーマ・地区から探せます。">
<link rel="canonical" href="{ORIGIN}{canonical}"><meta name="referrer" content="origin">
{('<meta name="robots" content="noindex,follow">' if noindex else '')}
<link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/assets/css/site-header.css"><link rel="stylesheet" href="/assets/css/article-search.css">
</head><body class="search-page"><a class="skip-link" href="#search-main">本文へ移動</a><header class="gh-site">{header}</header>
<main id="search-main" class="search-main"><nav class="search-nav" aria-label="記事の入口"><a href="/search/">記事を探す</a><a href="/c137">テーマ</a><a href="/#districts">地区</a><a href="/c034">全記事一覧</a><a href="/c019">資料目録</a></nav>
<div class="text-size" role="group" aria-label="文字サイズ"><span>文字サイズ</span><button type="button" data-text-size="standard" aria-pressed="true">標準</button><button type="button" data-text-size="large" aria-pressed="false">大</button><button type="button" data-text-size="largest" aria-pressed="false">特大</button></div>
{content}</main><footer class="im-foot"></footer><script defer src="/assets/js/search-preferences.js"></script>{scripts}</body></html>'''
    return re.sub(r'<a\b', '<a referrerpolicy="origin"', result)


def build(check=False):
    ledger, records, bodies, grams, dictionary, inventory, excluded = corpus()
    artifacts = {}
    metadata = {'schemaVersion': SCHEMA, 'dictionaryVersion': stamp(encoded(dictionary))[:16],
                'districts': ledger['districts'], 'themes': [{'id': i, 'name': n, 'sourceUrl': '/' + i} for i, n in HUBS],
                'dictionary': dictionary, 'records': records}
    raw = encoded(metadata)
    metadata_path = 'data/search/metadata.' + stamp(raw)[:24] + '.json'
    artifacts[metadata_path] = raw
    gram_paths = []
    for i, shard in enumerate(grams):
        data = encoded(shard)
        path = 'data/search/grams/' + str(i) + '.' + stamp(data)[:24] + '.json'
        artifacts[path] = data
        gram_paths.append('/' + path)
    for record in records:
        artifacts[record['body'].lstrip('/')] = encoded({'schemaVersion': SCHEMA, 'id': record['id'], **bodies[record['url']]})
    # Compact count-min hint only chooses rare grams; exact postings/body checks decide matches.
    hint_rows = [[0] * 8192 for _ in range(3)]
    for shard in grams:
        for gram, postings in shard.items():
            for row in range(3):
                value = 0x811c9dc5 ^ row
                for char in gram:
                    value = ((value ^ ord(char)) * 16777619) & 0xffffffff
                hint_rows[row][value % 8192] += len(postings)
    frequency_hint = {'width': 8192, 'rows': [''.join(chr(65 + min(25, math.ceil(math.log2(value + 1)))) for value in row) for row in hint_rows]}
    manifest = {'schemaVersion': SCHEMA, 'generation': stamp(raw)[:24], 'metadata': '/' + metadata_path,
                'count': len(records), 'gramFrequencyHint': frequency_hint, 'gramShards': gram_paths, 'dictionaryVersion': metadata['dictionaryVersion'],
                'metadataGzipBytes': len(gzip.compress(raw, mtime=0))}
    manifest_bytes = encoded(manifest)
    recent = sorted(records, key=lambda r: (r['updated'] or r['published'], r['id']), reverse=True)
    fallback = ''.join(card(r, ledger['districts']) for r in recent[:20])
    content = f'''<h1>磐田の歴史や暮らしの記事を探す</h1>{search_form(ledger['districts'])}
<section id="search-results" aria-labelledby="search-results-title"><h2 id="search-results-title" tabindex="-1">記事一覧</h2>
<p id="search-status" role="status" aria-live="polite" aria-atomic="true">検索を使わずに、下の一覧から記事を読めます。</p>
<p id="search-error" role="alert" hidden></p><div id="search-conditions"></div><div id="search-recovery"></div>
<ol id="search-list" class="search-list">{fallback}</ol><nav id="search-pagination" class="search-pagination" aria-label="検索結果のページ送り"></nav></section>
<noscript><p>言葉による検索にはJavaScriptが必要です。地区・テーマの入口、全記事一覧、または下の20件ずつの一覧から記事を読めます。</p></noscript>
<p><a href="/search/catalog/1/">20件ずつ全記事を読む</a> ／ <a href="/c034">地区別の全記事一覧</a> ／ <a href="/search/help/">記事の探し方</a></p>'''
    artifacts['search/index.html'] = shell('記事を探す', content, '/search/', True,
        '<script defer src="/assets/js/article-search.js"></script>').encode()
    help_content = """<h1>記事の探し方</h1><p>地名・人物名・気になる言葉を入力し、「検索」を押します。入力中には結果を変えません。</p><h2>言葉と読み</h2><p>「中泉 軌道」のように空白で区切ると、すべての言葉を含む記事を探します。全角・半角、ひらがな・カタカナは検索用に揃えます。本文は書き換えません。1文字だけの検索は題名・記事IDと確認済みの読みを対象にします。</p><p>福田地区の「ふくで」と、福田半香の姓「ふくだ」は、根拠のある対象記事だけに対応させています。未確認の読みは推測しません。</p><h2>条件と並び順</h2><p>地区とテーマを選び「この条件で探す」を押します。テーマは既存のテーマハブ本文に掲載された記事を対象とします。「テーマ未分類」も選べます。題名順は表示された題名で並べ、読みを推測した五十音順ではありません。確認できない公開・更新日は表示しません。</p><h2>結果と戻る操作</h2><p>結果は検索欄の直後に20件ずつ表示します。「次の20件」で進み、ブラウザーの戻る操作や「検索結果へ戻る」で条件と位置を復元します。URLを保存して同じ条件を再び開けます。検索履歴のない記事には戻るリンクを作りません。</p><h2>文字サイズと通信の失敗</h2><p>標準・大・特大を選べます。検索の読込みに失敗したときは「もう一度試す」、または全記事一覧をご利用ください。失敗は記事が0件という意味ではありません。</p><p>JavaScriptを使えない環境でも、通常のリンクで<a href="/search/catalog/1/">全記事を20件ずつ読む</a>、<a href="/c034">地区別の全記事一覧</a>へ進めます。</p>"""
    artifacts['search/help/index.html'] = shell('記事の探し方', help_content, '/search/help/').encode()
    page_count = (len(records) + 19) // 20
    for page in range(1, page_count + 1):
        rows = recent[(page - 1) * 20:page * 20]
        links = (f'<a href="/search/catalog/{page - 1}/">前の20件</a>' if page > 1 else '')
        links += (f'<a href="/search/catalog/{page + 1}/">次の20件</a>' if page < page_count else '')
        content = f'<h1>全記事を20件ずつ読む</h1><p>全{len(records)}件中 {(page - 1) * 20 + 1}〜{min(page * 20, len(records))}件（{page} / {page_count}ページ）</p><ol class="search-list">' + ''.join(card(r, ledger['districts']) for r in rows) + f'</ol><nav class="search-pagination" aria-label="一覧のページ送り">{links}</nav>'
        artifacts[f'search/catalog/{page}/index.html'] = shell(f'全記事一覧 {page}ページ', content, f'/search/catalog/{page}/').encode()
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    sitemap = re.sub(r'\s*<!-- search:start -->.*?<!-- search:end -->', '', sitemap, flags=re.S)
    entries = [f'  <url><loc>{ORIGIN}/search/help/</loc></url>'] + [f'  <url><loc>{ORIGIN}/search/catalog/{page}/</loc></url>' for page in range(1, page_count + 1)]
    sitemap = sitemap.replace('</urlset>', '<!-- search:start -->\n' + '\n'.join(entries) + '\n<!-- search:end -->\n</urlset>')
    artifacts['sitemap.xml'] = sitemap.encode()
    # Keep the full legacy directory and its anchors; only remove explicitly archived entries.
    c034 = (ROOT / 'c034.html').read_text(encoding='utf-8')
    c034 = re.sub(r'<!-- search-catalog-extra:start -->.*?<!-- search-catalog-extra:end -->', '', c034, flags=re.S)
    c034 = re.sub(r'<!-- search-knowledge-extra:start -->.*?<!-- search-knowledge-extra:end -->', '', c034, flags=re.S)
    hidden_urls = {key(p['url']) for p in ledger['pages'] if p.get('status') != 'published'}
    c034 = re.sub(r'<li><a href="([^"]+)">.*?</a></li>', lambda match: '' if key(match[1]) in hidden_urls else match[0], c034)
    for part in ['idx-count', 'search-catalog-extra']:
        if part == 'idx-count':
            c034 = re.sub(r'<p class="idx-count">.*?</p>',
                f'<p class="idx-count">公開の知識記事は<strong>{sum(p.get("count_as_knowledge") is True and p.get("status") == "published" for p in ledger["pages"])}本</strong>です。ブログを含む検索対象は{len(records)}件（canonical単位）です。<a href="/search/">言葉・テーマ・地区で探す</a> ／ <a href="/search/catalog/1/">20件ずつ読む</a></p>', c034, count=1)
    primary = {key(link) for link in re.findall(r'<li><a href="([^"]+)">', c034)}
    additions = [p for p in ledger['pages'] if p.get('status') == 'published' and p.get('count_as_knowledge') is True and key(p['url']) not in primary]
    knowledge = '<!-- search-knowledge-extra:start --><ul class="idx-list" aria-label="新しく追加された知識記事">' + ''.join(f'<li><a href="{html.escape(key(p["url"]))}">{html.escape(p["title"])}</a></li>' for p in additions) + '</ul><!-- search-knowledge-extra:end -->' if additions else ''
    c034 = re.sub(r'\s*</article>', lambda _: ('\n' + knowledge if knowledge else '') + '\n</article>', c034, count=1)
    redirects = redirect_map()
    existing = {resolve(link, redirects) for link in Page(c034).links if link.startswith('/') and not link.startswith('//')}
    extras = [r for r in records if r['url'] not in existing]
    extra = '<!-- search-catalog-extra:start --><section class="article idx-group" id="search-catalog-extra"><h2>ブログ・公開記事の補完一覧</h2><p>地区別の一覧と重ならない公開記事です。<a href="/search/catalog/1/">全記事を20件ずつ読む</a>こともできます。</p><ul class="search-list">' + ''.join(card(r, ledger['districts']) for r in extras) + '</ul></section><!-- search-catalog-extra:end -->'
    if not extras:
        extra = '<!-- search-catalog-extra:start --><!-- search-catalog-extra:end -->'
    c034 = re.sub(r'</article>\s*', lambda _: '</article>\n' + extra + '\n', c034, count=1)
    if 'id="catalog-main"' not in c034:
        c034 = c034.replace('<div class="article-head">', '<main id="catalog-main"><div class="article-head">', 1)
        c034 = c034.replace('<!-- managed-footer:start -->', '</main>\n<!-- managed-footer:start -->', 1)
        c034 = c034.replace('<body>', '<body><a class="skip-link" href="#catalog-main">本文へ移動</a>', 1)
    header = (ROOT / 'partials/header.html').read_text(encoding='utf-8')
    c034 = re.sub(r'(<header class="gh-site">).*?</header>', lambda m: m[1] + header + '</header>', c034, count=1, flags=re.S)
    if '/assets/css/article-search.css' not in c034:
        c034 = c034.replace('</head>', '<link rel="stylesheet" href="/assets/css/article-search.css">\n</head>', 1)
    artifacts['c034.html'] = c034.encode()
    artifacts['data/search/manifest.json'] = manifest_bytes
    failures = [path for path, data in artifacts.items() if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data]
    managed = list((ROOT / 'data/search').glob('metadata.*.json')) + list((ROOT / 'data/search/grams').glob('*.json')) + list((ROOT / 'data/search/bodies').glob('*.json')) + list((ROOT / 'search/catalog').glob('*/index.html'))
    obsolete = [p for p in managed if p.relative_to(ROOT).as_posix() not in artifacts]
    if check and obsolete:
        failures += [p.relative_to(ROOT).as_posix() for p in obsolete]
    if check and failures:
        raise SystemExit('Search artifacts are stale: ' + ', '.join(failures[:12]))
    if not check:
        # manifest is last: a reader never sees a partially generated corpus.
        for path, data in artifacts.items():
            if path == 'data/search/manifest.json':
                continue
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists() or destination.read_bytes() != data:
                destination.write_bytes(data)
        (ROOT / 'data/search/manifest.json').write_bytes(manifest_bytes)
        for path in obsolete:
            assert path.resolve().is_relative_to(ROOT.resolve())
            path.unlink()
    report = {'schemaVersion': SCHEMA, 'indexed': len(records), 'metadata_gzip_bytes': manifest['metadataGzipBytes'],
              'body_total_gzip_bytes': sum(len(gzip.compress(encoded(b), mtime=0)) for b in bodies.values()),
              'gram_total_gzip_bytes': sum(len(gzip.compress(encoded(g), mtime=0)) for g in grams),
              'exclusions': excluded, 'inventory': inventory,
              'unknown_ledger_themes': sorted({t for r in records for t in r['ledgerThemes']} - set(ledger['themes'])),
              'classification_policy': '14 hub body links are separate from ledger themes; no semantic inference',
              'body_extraction': 'main/article else body, excluding scripts/styles/nav/header/footer/aside/common policy/property/reactions/related/pager/crumb. All original file hashes and references preserved separately.'}
    print(json.dumps({k: v for k, v in report.items() if k not in {'inventory', 'exclusions', 'unknown_ledger_themes'}}, ensure_ascii=False))
    return report


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--check', action='store_true')
    args.add_argument('--report', type=Path)
    options = args.parse_args()
    result = build(options.check)
    if options.report:
        options.report.parent.mkdir(parents=True, exist_ok=True)
        options.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
