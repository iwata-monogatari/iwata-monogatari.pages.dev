"""Split the existing seminar without rewriting its teaching material."""
import html
import json
import re
from enshu_navigation import navigation

BASE = '/enshu/seminar/'

def split_seminar(root, original, lessons, check=False):
    head = re.search(r'<head>(.*?)</head>', original, re.S)[1]
    head += '<link rel="stylesheet" href="/assets/css/enshu-navigation.css?v=20261114">'
    header = re.search(r'<body>(.*?)<main', original, re.S)[1]
    footer = original.split('</main>', 1)[1]
    policy = re.search(r'<aside class="seminar-policy">.*?</aside>', original, re.S)[0]
    glossary = re.search(r'<section id="glossary".*?</section>', original, re.S)[0]
    bibliography = re.search(r'<section id="bibliography".*?</section>', original, re.S)[0]
    credits = re.search(r'<!-- iwata-photo:credits -->.*?<!-- /iwata-photo:credits -->', original, re.S)
    credits = credits[0] if credits else ''
    pattern = r'(?:<!-- iwata-photo:pause-\d+ -->.*?<!-- /iwata-photo:pause-\d+ -->)?<article class="seminar-lesson" id="lesson-([^"]+)">.*?</article>'
    articles = {m[1]: m[0] for m in re.finditer(pattern, original, re.S)}
    assert set(articles) == {x['id'] for x in lessons}
    outputs = {}
    for i, lesson in enumerate(lessons):
        key = lesson['id']; path = BASE + key + '/'
        title = lesson['title']; deck = lesson['deck']
        h = re.sub(r'<meta name="iwata:(?:published|category)"[^>]*>', '', head)
        h = re.sub(r'<title>.*?</title>', '<title>'+html.escape(title)+'｜資料読解講座｜磐田物語</title>', h)
        for attr, name, value in [('name','description',deck),('property','og:title',title),('property','og:description',deck),('property','og:url','https://iwata-monogatari.net'+path)]:
            h = re.sub(r'<meta '+attr+'="'+name+r'" content="[^"]*">', '<meta '+attr+'="'+name+'" content="'+html.escape(value,quote=True)+'">', h)
        h = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="https://iwata-monogatari.net'+path+'">', h)
        schema = {'@context':'https://schema.org','@type':'LearningResource','name':title,'description':deck,'url':'https://iwata-monogatari.net'+path,'inLanguage':'ja','isPartOf':{'@type':'CollectionPage','url':'https://iwata-monogatari.net'+BASE},'learningResourceType':'資料読解講座'}
        h = re.sub(r'<script type="application/ld\+json">.*?</script>', '<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False)+'</script>', h, flags=re.S)
        article = articles[key].replace('<h2>'+html.escape(title)+'</h2>', '<h1>'+html.escape(title)+'</h1>')
        article = article.replace('href="#syllabus"','href="'+BASE+'"').replace('8講の一覧へ ↑','8講の一覧へ戻る →')
        adjacent = '<nav class="academy-paths" aria-label="講座の前後"><a href="'+BASE+'">← 8講の一覧へ</a><div>'
        for j, label in [(i-1,'前の講座'),(i+1,'次の講座')]:
            if 0 <= j < len(lessons):
                item=lessons[j]; adjacent += '<a href="'+BASE+item['id']+'/">'+label+'：'+html.escape(item['title'])+'</a>'
        adjacent += '</div></nav>'
        content = navigation()+ '<div class="breadcrumbs"><a href="/enshu/">遠州弁の学び舎</a> ／ <a href="'+BASE+'">資料読解8講</a> ／ 講座 '+str(i+1).zfill(2)+'</div>'+article+adjacent+policy+glossary+bibliography+credits+navigation()
        outputs['enshu/seminar/'+key+'/index.html']='<!doctype html><html lang="ja"><head>'+h+'</head><body>'+header+'<main class="academy seminar">'+content+'</main>'+footer
    index = re.sub(pattern, '', original, flags=re.S)
    index = index.replace('</head>', '<link rel="stylesheet" href="/assets/css/enshu-navigation.css?v=20261114"><script defer src="/assets/js/enshu-seminar-legacy.js?v=20261114"></script></head>')
    index = index.replace('<main class="academy seminar">','<main class="academy seminar">'+navigation(BASE),1)
    index = index.replace('</main>',navigation(BASE)+'</main>',1)
    for lesson in lessons:
        key=lesson['id']; index=index.replace(BASE+'#lesson-'+key,BASE+key+'/').replace('href="#lesson-'+key+'"','href="'+BASE+key+'/"')
    outputs['enshu/seminar/index.html']=index
    for path, text in outputs.items():
        target=root/path
        if check:
            assert target.exists() and target.read_text(encoding='utf8')==text, 'Regenerate '+path
        else:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf8',newline='\n')
    return outputs
