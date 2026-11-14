"""Give each existing comparison theme its own canonical reading page."""
import html,json,re
from enshu_navigation import navigation
from enshu_photo_layout import figure,credits,CSS as PHOTO_CSS
from enshu_records_pages import PHOTO_KEYS

BASE='/enshu/compare/'
def theme_url(id_):return BASE+('household-tools' if id_=='tools' else id_)+'/'

def split_comparisons(root,original,groups,check=False):
    sections={m[1]:m[0] for m in re.finditer(r'<section class="compare-section" id="compare-([^"]+)">.*?</section>',original,re.S)}
    assert set(sections)=={g['id'] for g in groups}
    head=re.search(r'<head>(.*?)</head>',original,re.S)[1]
    head+='<link rel="stylesheet" href="'+PHOTO_CSS+'"><link rel="stylesheet" href="/assets/css/enshu-compare-pages.css?v=20261114">'
    header=re.search(r'<body>(.*?)<main',original,re.S)[1]
    footer=original.split('</main>',1)[1]
    policy=re.search(r'<aside class="archive-policy">.*?</aside>',original,re.S)[0]
    ending=re.search(r'<section class="archive-end">.*?</section>',original,re.S)[0]
    tiles=re.search(r'<section id="themes">.*?</section>',original,re.S)[0]
    hero=re.search(r'<header class="archive-hero compare-hero">(.*?)</header>',original,re.S)[1]
    for g in groups:tiles=tiles.replace('href="#compare-'+g['id']+'"','href="'+theme_url(g['id'])+'"')

    def document(path,title,description,content,index=False):
        h=head
        if not index:h=re.sub(r'<meta name="iwata:(?:published|category)"[^>]*>','',h)
        h=re.sub(r'<title>.*?</title>','<title>'+html.escape(title)+'｜磐田物語</title>',h)
        for attr,name,value in [('name','description',description),('property','og:title',title),('property','og:description',description),('property','og:url','https://iwata-monogatari.net'+path)]:
            h=re.sub(r'<meta '+attr+'="'+name+r'" content="[^"]*">','<meta '+attr+'="'+name+'" content="'+html.escape(value,quote=True)+'">',h)
        h=re.sub(r'<link rel="canonical" href="[^"]*">','<link rel="canonical" href="https://iwata-monogatari.net'+path+'">',h)
        schema={'@context':'https://schema.org','@type':'CollectionPage','name':title,'description':description,'url':'https://iwata-monogatari.net'+path,'inLanguage':'ja','isPartOf':{'@type':'CollectionPage','url':'https://iwata-monogatari.net'+BASE}}
        if index:schema['datePublished']='2026-11-12'
        h=re.sub(r'<script type="application/ld\+json">.*?</script>','<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False)+'</script>',h,flags=re.S)
        if index:h+='<script defer src="/assets/js/enshu-compare-pages.js?v=20261114"></script>'
        return '<!doctype html><html lang="ja"><head>'+h+'</head><body>'+header+'<main class="academy archive compare-paging">'+navigation(BASE)+content+navigation(BASE)+'</main>'+footer

    breadcrumb='<div class="breadcrumbs"><a href="/enshu/">遠州弁の学び舎</a> ／ ことばの比較帖</div>'
    home_hero='<header class="archive-hero compare-hero" data-iwata-layout="intro"><div class="iwata-intro-copy">'+hero+'</div>'+figure('merchant')+'</header>'
    content=breadcrumb+home_hero+policy+'<p class="compare-page-note">各テーマは別のページで読めます。原表記・意味・記録地・資料へのリンクを保持し、一覧へ戻って選び直せます。</p>'+tiles+figure('river','reading-pause')+ending+credits(['merchant','river'])
    mapping={g['id']:theme_url(g['id']) for g in groups}
    content+='<script type="application/json" id="compare-page-map">'+json.dumps(mapping,ensure_ascii=False)+'</script>'
    outputs={BASE.lstrip('/')+'index.html':document(BASE,'遠州ことばの比較帖｜24テーマで郷土資料を読む','雨、食卓、家、道具、動植物、語尾。24テーマから独立した比較ページを選び、原表記・旧町村・出典を読み比べる。',content,True)}
    for ix,g in enumerate(groups):
        path=theme_url(g['id']);a=PHOTO_KEYS[ix%len(PHOTO_KEYS)];b=PHOTO_KEYS[(ix+5)%len(PHOTO_KEYS)]
        section=sections[g['id']].replace('href="#themes"','href="'+BASE+'#themes"').replace('テーマ一覧へ ↑','← 24テーマの一覧へ')
        # Keep the complete original explanatory paragraph and every table row.
        section=section.replace('<div class="compare-table">',figure(b,'reading-pause')+'<div class="compare-table">',1)
        adjacent='<nav class="compare-adjacent" aria-label="比較帖の読み進め方">'
        if ix:adjacent+='<a href="'+theme_url(groups[ix-1]['id'])+'">← 前のテーマ</a>'
        adjacent+='<a href="'+BASE+'#themes">24テーマの一覧へ戻る</a>'
        if ix+1<len(groups):adjacent+='<a href="'+theme_url(groups[ix+1]['id'])+'">次のテーマ →</a>'
        adjacent+='</nav>'
        heading=re.search(r'<div class="scene-heading">.*?</div></div>',section,re.S)[0]
        section=section.replace(heading,'',1)
        hero_page='<header class="archive-hero compare-hero" data-iwata-layout="intro"><div class="iwata-intro-copy"><p class="eyebrow">ことばの比較帖 / '+f'{ix+1:02} / 24'+'</p><h1>'+html.escape(g['title'])+'</h1><p>原表記・意味・記録地と出典を読み比べる。</p></div>'+figure(a)+'</header>'
        breadcrumb='<div class="breadcrumbs"><a href="/enshu/">学び舎</a> ／ <a href="'+BASE+'">ことばの比較帖</a> ／ '+html.escape(g['title'])+'</div>'
        content=breadcrumb+hero_page+adjacent+policy+'<p class="compare-page-note">写真は磐田の風景です。方言の採録現場や、この語の使用地点を示すものではありません。</p>'+section+adjacent+ending+credits([a,b])
        outputs[path.lstrip('/')+'index.html']=document(path,g['title']+'｜遠州ことばの比較帖',g['intro'],content)
    for path,text in outputs.items():
        p=root/path
        if check:assert p.exists() and p.read_text(encoding='utf8')==text,'Regenerate '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf8',newline='\n')
