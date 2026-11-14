"""Separate academy activities without changing the canonical learning material."""
import html
import re
from urllib.parse import urlencode

LINKS = [('/enshu/courses/', '場面から読む'), ('/enshu/practice/', 'クイズで試す'),
         ('/enshu/words/', '一語ずつ探す'), ('/enshu/seminar/', '資料から学ぶ8講座'),
         ('/enshu/research/', '研究ノート・集計室'), ('/c006', '辞典で調べる'),
         ('/c008', '文を変換する'), ('/enshu/records/', '380記録の資料辞典'),
         ('/enshu/compare/', '24テーマの比較帖')]

def scene_path(sid):
    return '/enshu/courses/'+('work-tools' if sid == 'work' else sid)+'/'


def navigation(current=''):
    links = ''.join(f'<a href="{url}"'+(' aria-current="page"' if current == url else '')+f'>{label}</a>' for url, label in LINKS)
    return '<nav class="academy-paths" aria-label="学び舎のページ"><a class="academy-home" href="/enshu/">← 学び舎の入口へ</a><div>'+links+'</div></nav>'


def middle_header(markup, current):
    """Use the same static academy navigation on the three existing hubs."""
    block = '<!-- academy-middle:start --><div class="academy-middle-header">'+navigation(current)+'</div><!-- academy-middle:end -->'
    if '<!-- academy-middle:start -->' in markup:
        return re.sub(r'<!-- academy-middle:start -->.*?<!-- academy-middle:end -->',lambda _:block,markup,flags=re.S)
    markup = re.sub(r'<nav class="converter-academy-return".*?</nav>', '', markup, flags=re.S)
    if '/assets/css/enshu-navigation.css' not in markup:
        markup = markup.replace('</head>', '<link rel="stylesheet" href="/assets/css/enshu-navigation.css?v=20261114-middle"></head>',1)
    if current == '/c006':
        markup = re.sub(r'(<header class="gh-site">.*?</header>)',lambda m:m[0]+block,markup,count=1,flags=re.S)
    else:
        markup = re.sub(r'<main\b[^>]*>',lambda m:m[0]+block,markup,count=1)
    assert block in markup
    return markup


def external_activity_links(markup, scenes):
    """Keep real links usable with JS disabled, including course-specific quizzes."""
    def quiz(match):
        tag = match.group(0)
        sid = re.search(r'data-quiz-scene="([^"]+)"', tag).group(1)
        source = re.search(r'data-quiz-source="([^"]+)"', tag)
        params = {'scene': sid, 'start': '1'}
        if source:
            params['source'] = source.group(1)
        return tag.replace('href="#practice"', 'href="/enshu/practice/?'+html.escape(urlencode(params), quote=True)+'"')
    markup = re.sub(r'<a\b[^>]*data-quiz-scene="[^"]+"[^>]*>', quiz, markup)
    markup = markup.replace('/enshu/?word=', '/enshu/words/?word=').replace('#cards"', '"')
    markup = markup.replace('href="#practice"', 'href="/enshu/practice/"').replace('href="#courses"', 'href="/enshu/courses/"')
    for scene in scenes:
        markup = markup.replace(f'href="#scene-{scene["id"]}"', f'href="{scene_path(scene["id"])}"')
    markup = markup.replace('コースを選び直す ↑', '場面一覧に戻る →')
    return markup


def split_pages(root, result, courses, lessons, practice, explorer, scenes, check=False):
    head = re.search(r'<head>(.*?)</head>', result, re.S).group(1)
    head = re.sub(r'<script\b[^>]*enshu-academy\.js[^>]*></script>', '', head)
    head = re.sub(r'<script\b[^>]*enshu-legacy-navigation\.js[^>]*></script>', '', head)
    head = re.sub(r'<link\b[^>]*enshu-navigation\.css[^>]*>', '', head)
    head = re.sub(r'<meta name="iwata:(?:published|category)"[^>]*>', '', head)
    head += '<link rel="stylesheet" href="/assets/css/enshu-navigation.css?v=20261114">'
    notice = re.search(r'<section class="notice">.*?</section>', result, re.S).group(0)
    sources = re.search(r'<section class="sources">.*?</section>', result, re.S)
    sources = sources.group(0) if sources else ''

    def document(path, title, description, content, script=False):
        h = re.sub(r'<title>.*?</title>', '<title>'+html.escape(title)+'｜磐田物語</title>', head)
        for attr, key, value in [('name', 'description', description), ('property', 'og:title', title), ('property', 'og:description', description), ('property', 'og:url', 'https://iwata-monogatari.net'+path)]:
            h = re.sub(r'<meta '+attr+'="'+key+r'" content="[^"]*">', '<meta '+attr+'="'+key+'" content="'+html.escape(value, quote=True)+'">', h)
        h = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="https://iwata-monogatari.net'+path+'">', h)
        if script:
            h += '<script defer src="/assets/js/enshu-academy.js?v=20261114-pages"></script>'
        top = '<header class="academy-section-heading"><p>遠州弁の学び舎</p><h1>'+html.escape(title)+'</h1><p>'+html.escape(description)+'</p></header>'
        return '<!doctype html><html lang="ja"><head>'+h+'</head><body><header class="gh-site"></header><main class="academy">'+navigation(path)+top+content+notice+sources+navigation(path)+'</main><footer class="im-foot"></footer></body></html>\n'

    outputs = {}
    courses = external_activity_links(courses, scenes)
    courses = re.sub(r'<div class="course-view-controls">.*?</div>', '', courses, flags=re.S)
    outputs['enshu/courses/index.html'] = document('/enshu/courses/', '場面から読む｜遠州弁の12コース', '暮らしの場面を選び、ことばの意味と24の会話を読む。各場面は独立したページで開きます。', courses)
    for scene in scenes:
        sid = scene['id']
        body = re.search(r'<section id="scene-'+re.escape(sid)+r'".*?</section>', lessons, re.S).group(0)
        body = external_activity_links(body, scenes)
        outputs[scene_path(sid).lstrip('/')+'index.html'] = document(scene_path(sid), scene['title']+'の遠州弁', '意味・会話・資料を読み、気になることばやクイズへ進めます。', body)
    back = '<p class="activity-return"><a id="quiz-course-return" href="/enshu/courses/">← 場面を選び直す</a></p>'
    practice = practice.replace('場面別の意味と作例、絵札の最初の一語はそのまま読めます。', '場面別ページと「一語ずつ探す」では、意味と作例を読めます。')
    outputs['enshu/practice/index.html'] = document('/enshu/practice/', '遠州弁クイズ｜3問から試す', '場面・語の分類・出題方向を選んで練習。答えたあとは、作例と資料で確かめます。', back+practice, True)
    outputs['enshu/words/index.html'] = document('/enshu/words/', '一語ずつ探す｜遠州弁の絵札と資料語', '182の学習語から、意味・3つの作例・使い分け・出典へ進む。', external_activity_links(explorer, scenes), True)

    # The entrance stays an entrance; no duplicate lesson, quiz or word widgets.
    landing = re.sub(r'<!-- course-lessons:start -->.*?<!-- course-lessons:end -->', '', result, flags=re.S)
    for section in ('courses', 'practice', 'cards'):
        landing = re.sub(r'<section id="'+section+r'".*?</section>', '', landing, flags=re.S)
    landing = re.sub(r'<script\b[^>]*enshu-academy\.js[^>]*></script>', '<script defer src="/assets/js/enshu-legacy-navigation.js?v=20261114"></script>', landing)
    landing = re.sub(r'<link\b[^>]*enshu-navigation\.css[^>]*>', '', landing)
    landing = landing.replace('</head>', '<link rel="stylesheet" href="/assets/css/enshu-navigation.css?v=20261114"></head>')
    for anchor, url in [('courses', '/enshu/courses/'), ('practice', '/enshu/practice/'), ('cards', '/enshu/words/')]:
        landing = landing.replace('href="#'+anchor+'"', 'href="'+url+'"')
    choices = '<section class="academy-destinations"><h2>今日の学び方を選ぶ</h2><p>原画像13頁を照合した380記録の資料辞典と、24テーマの比較帖も、ここから開けます。原表記と旧町村をたどりながら、今の辞典とも読み比べられます。</p><div>'+''.join('<a href="'+url+'"><strong>'+label+'</strong><span>ページを開く →</span></a>' for url, label in LINKS)+'</div></section>'
    landing = re.sub(r'<div class="archive-banner"><div>.*?</div><div>.*?</div></div>', '', landing, flags=re.S)
    landing = landing.replace('</header>\n<section class="notice">', '</header>'+choices+'\n<section class="notice">', 1)
    # On subsequent builds the cards already exist.
    if 'class="academy-destinations"' not in landing:
        landing = landing.replace('</header>\n', '</header>'+choices+'\n', 1)
    landing = re.sub(r'(<section class="academy-destinations">).*?(</section>)', lambda _: choices, landing, flags=re.S)
    # The entrance uses its seven destination cards as the primary chooser.
    landing = re.sub(r'(<header class="academy-hero">.*?)<nav>.*?</nav>', r'\1', landing, count=1, flags=re.S)
    landing = re.sub(r'<nav class="academy-paths".*?</nav>', '', landing, flags=re.S)
    legacy = '<noscript><p>以前のページ内リンクをご利用の方も、上の学び方から各ページへ進めます。</p></noscript>'
    if legacy not in landing:
        landing = landing.replace('</main>', legacy+'</main>')
    outputs['enshu/index.html'] = landing
    for path, markup in outputs.items():
        target = root/path
        if check:
            assert target.exists() and target.read_text(encoding='utf-8') == markup, 'Run tools/build_enshu_learning.py: '+path
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_text(encoding='utf-8') != markup:
                target.write_text(markup, encoding='utf-8')
    return outputs
