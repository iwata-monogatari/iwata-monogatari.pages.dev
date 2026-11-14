"""Paginate frozen historical records and keep cross-page search available."""
import html,json,re
from enshu_navigation import navigation
from enshu_photo_layout import figure,credits,CSS as PHOTO_CSS

BASE='/enshu/records/'
PHOTO_KEYS=['street','school','merchant','shrine','market','post','river','tea','forest','bridge','pond','hime','station']

def page_url(page):
    return BASE if page==1242 else BASE+str(page)+'/'

def page_navigation(page):
    links=''.join('<a href="'+page_url(p)+'"'+(' aria-current="page"' if p==page else '')+'>'+str(p)+'頁</a>' for p in range(1242,1255))
    adjacent='<div class="records-adjacent">'
    if 1242<page<=1254:adjacent+='<a href="'+page_url(page-1)+'">← 前の頁</a>'
    adjacent+='<a href="'+BASE+'">資料辞典の入口・頁一覧へ</a><a href="'+BASE+'search/">380記録を横断検索</a>'
    if 1242<=page<1254:adjacent+='<a href="'+page_url(page+1)+'">次の頁 →</a>'
    return '<nav class="records-pagination" aria-label="原資料の頁を選ぶ"><div class="page-jump">'+links+'</div>'+adjacent+'</div></nav>'

def split_records(root, original, rows, check=False):
    chapters={int(m[1]):m[0] for m in re.finditer(r'<section class="source-chapter" id="page-(\d+)">.*?</section>',original,re.S)}
    assert set(chapters)==set(range(1242,1255))
    head=re.search(r'<head>(.*?)</head>',original,re.S)[1]
    head=re.sub(r'<script\b[^>]*enshu-corpus\.js[^>]*></script>','',head)
    head+='<link rel="stylesheet" href="'+PHOTO_CSS+'"><link rel="stylesheet" href="/assets/css/enshu-records-pages.css?v=20261114">'
    header=re.search(r'<body>(.*?)<main',original,re.S)[1]
    footer=original.split('</main>',1)[1]
    policy=re.search(r'<aside class="archive-policy">.*?</aside>',original,re.S)[0]
    ending=re.search(r'<section class="archive-end">.*?</section>',original,re.S)[0]
    hero=re.search(r'<header class="archive-hero">(.*?)</header>',original,re.S)[1]
    search=re.search(r'<section class="archive-search".*?</section>',original,re.S)[0]
    form=re.search(r'<div class="archive-controls">(.*?)</div>',search,re.S)[1]
    for id_,name in [('corpus-search','q'),('corpus-village','v'),('corpus-page','p')]:
        form=form.replace('id="'+id_+'"','id="'+id_+'" name="'+name+'"')
    form=re.sub(r'<button id="corpus-clear".*?</button>','<button type="submit">検索ページで探す →</button>',form,flags=re.S)
    search_form='<section class="archive-search"><h2>380記録を横断して探す</h2><p>検索結果は専用ページで表示します。この頁だけでなく、原資料13頁の記録から探せます。</p><form class="archive-controls" action="'+BASE+'search/" method="get">'+form+'</form></section>'
    outputs={}

    def document(path,title,description,content,search_page=False,root_page=False):
        h=head
        if not root_page:h=re.sub(r'<meta name="iwata:(?:published|category)"[^>]*>','',h)
        h=re.sub(r'<title>.*?</title>','<title>'+html.escape(title)+'｜磐田物語</title>',h)
        for attr,name,value in [('name','description',description),('property','og:title',title),('property','og:description',description),('property','og:url','https://iwata-monogatari.net'+path)]:
            h=re.sub(r'<meta '+attr+'="'+name+r'" content="[^"]*">','<meta '+attr+'="'+name+'" content="'+html.escape(value,quote=True)+'">',h)
        h=re.sub(r'<link rel="canonical" href="[^"]*">','<link rel="canonical" href="https://iwata-monogatari.net'+path+'">',h)
        schema={'@context':'https://schema.org','@type':'CollectionPage','name':title,'description':description,'url':'https://iwata-monogatari.net'+path,'inLanguage':'ja','isPartOf':{'@type':'CollectionPage','url':'https://iwata-monogatari.net'+BASE}}
        if root_page:schema['isPartOf']={'@type':'WebSite','url':'https://iwata-monogatari.net/'}
        h=re.sub(r'<script type="application/ld\+json">.*?</script>','<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False)+'</script>',h,flags=re.S)
        if search_page:h+='<script defer src="/assets/js/enshu-corpus.js?v=20261111"></script>'
        if root_page:h+='<script defer src="/assets/js/enshu-records-pages.js?v=20261114"></script>'
        return '<!doctype html><html lang="ja"><head>'+h+'</head><body>'+header+'<main class="academy archive records-paging">'+navigation(BASE)+content+navigation(BASE)+'</main>'+footer

    for page,chapter in chapters.items():
        subset=[r for r in rows if r['page']==page]
        # Odd pages share the same photographed spread as the preceding page.
        if 'class="source-thumb"' not in chapter:
            frame=subset[0]['frame']
            thumb='<figure class="source-thumb"><a href="https://dl.ndl.go.jp/pid/965680/1/'+str(frame)+'"><img src="/assets/img/kotoba/gunshi-'+str(frame)+'.webp" width="1200" height="853" loading="lazy" alt="磐田郡誌'+str(page)+'頁を含む見開きの原画像"><span>原画像を開く ↗</span></a><figcaption>国立国会図書館デジタルコレクション</figcaption></figure>'
            chapter=chapter.replace('</div><div class="record-grid">',thumb+'</div><div class="record-grid">',1)
        photo_a=PHOTO_KEYS[page-1242];photo_b=PHOTO_KEYS[(page-1242+5)%len(PHOTO_KEYS)]
        article_matches=list(re.finditer(r'<article class="record".*?</article>',chapter,re.S))
        assert len(article_matches)==len(subset)
        midpoint=article_matches[max(0,len(article_matches)//2-1)].end()
        chapter=chapter[:midpoint]+'<div class="records-photo-break">'+figure(photo_b,'reading-pause')+'</div>'+chapter[midpoint:]
        title='遠州ことば資料辞典｜磐田郡誌'+str(page)+'頁・'+str(len(subset))+'記録'
        if page==1242:title=re.search(r'<title>(.*?)｜磐田物語</title>',original,re.S)[1]
        description=str(page)+'頁の原表記・意味・記録地・原注と出典を読む。磐田の風景写真を添え、前後の頁と全380記録の検索へ進めます。'
        intro=hero if page==1242 else '<p class="eyebrow">ENSHU WORD ARCHIVE / 1921</p><h1>'+str(page)+'頁のことば</h1><p>磐田郡誌の遠州ことば資料辞典 ／ この頁の'+str(len(subset))+'記録を読む。</p>'
        hero_page='<header class="archive-hero" data-iwata-layout="intro"><div class="iwata-intro-copy">'+intro+'</div>'+figure(photo_a)+'</header>'
        breadcrumb='<div class="breadcrumbs"><a href="/enshu/">遠州弁の学び舎</a> ／ <a href="'+BASE+'">郷土資料辞典</a> ／ '+str(page)+'頁</div>'
        content=breadcrumb+hero_page+policy+'<p class="records-page-note">このページには'+str(page)+'頁の'+str(len(subset))+'記録を掲載しています。他の頁は頁一覧から開けます。写真は磐田の風景で、方言の採録現場を示すものではありません。</p>'+page_navigation(page)+search_form+'<div id="corpus-records">'+chapter+'</div>'+page_navigation(page)+ending+credits([photo_a,photo_b])
        if page==1242:
            mapping={r['id']:r['page'] for r in rows}
            content+='<script type="application/json" id="records-page-map">'+json.dumps(mapping,ensure_ascii=False)+'</script>'
        outputs[page_url(page).lstrip('/')+'index.html']=document(page_url(page),title,description,content,root_page=page==1242)

    # Keep cross-page filtering on a dedicated page rather than silently narrowing it.
    search_all=search
    search_all=re.sub(r'<nav class="page-jump">.*?</nav>',page_navigation(0),search_all,flags=re.S)
    all_chapters=''.join(chapters.values())
    for row in rows:
        all_chapters=all_chapters.replace('href="#'+row['id']+'"','href="'+page_url(row['page'])+'#'+row['id']+'"')
    content='<div class="breadcrumbs"><a href="/enshu/">学び舎</a> ／ <a href="'+BASE+'">資料辞典の入口へ</a> ／ 横断検索</div><header class="archive-hero" data-iwata-layout="intro"><div class="iwata-intro-copy"><p class="eyebrow">ENSHU WORD ARCHIVE / SEARCH</p><h1>380記録を、横断して探す。</h1><p>原表記・意味・記録地・頁で絞り、見つけた語の記録頁へ戻れます。</p></div>'+figure('market')+'</header>'+policy+search_all+'<div id="corpus-records">'+all_chapters+'</div>'+ending+credits(['market'])
    outputs['enshu/records/search/index.html']=document(BASE+'search/','遠州ことば資料辞典の横断検索｜380記録','磐田郡誌の380記録を、原表記・意味・旧町村・原資料の頁で横断検索。',content,search_page=True)
    for path,text in outputs.items():
        target=root/path
        if check:assert target.exists() and target.read_text(encoding='utf8')==text,'Regenerate '+path
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf8',newline='\n')
