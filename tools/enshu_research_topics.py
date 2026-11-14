"""Separate existing research categories while preserving each original card."""
import html
import json
import re
from enshu_navigation import navigation
from enshu_photo_layout import figure,credits as photo_credits
from enshu_records_pages import PHOTO_KEYS

BASE='/enshu/research/'
TOPICS=['systematic','regional','new-sources','kinship','livelihood','honorific','festival','language','grammar','word-history','folk-life','variation','sound','foundations']
TOPIC_LABELS=dict(zip(TOPICS,['原論文から深く読む','地域の原資料を読む','新資料から深く読む','親族・人の呼び方','仕事・生業','敬語・待遇表現','祭り・年中行事','文の組立てと意味','否定・条件・可能・勧誘','語源・語史','暮らしと民俗','地域・世代・意味の変化','発音・アクセント','文法・民俗・資料']))

def note_category_return(note):
    key=note.get('group','foundations')
    assert key in TOPICS,(note['slug'],key)
    return '<nav class="research-nav research-category-return" aria-label="所属する研究分類"><a href="'+BASE+'topics/'+key+'/">← '+html.escape(TOPIC_LABELS[key])+'の分類ページへ</a></nav>'

def note_reading_return(text):
    """Reuse existing note photographs and repeat its exact category return below."""
    text=re.sub(r'<!-- research-note-return:start -->.*?<!-- research-note-return:end -->','',text,flags=re.S)
    category=re.findall(r'<nav class="research-nav research-category-return".*?</nav>',text,re.S)
    assert len(category)==1,'Each note must have one original category return'
    assert len(re.findall(r'<figure class="iwata-photo iwata-photo-(?:lead|middle)"',text))==2,'Keep both existing Iwata photographs'
    footer='<!-- research-note-return:start --><section class="seminar-next research-note-return" aria-label="研究ノートから戻る"><p class="research-small">写真は、撮影地・撮影年を添えた磐田の風景です。本文の調査対象地や方言の採録現場を示すものではありません。</p>'+category[0]+'<div class="academy-middle-header">'+navigation(BASE)+'</div></section><!-- research-note-return:end -->'
    assert text.count('</main>')==1
    return text.replace('</main>',footer+'</main>',1)

def balanced_div(text,start):
    depth=0
    for match in re.finditer(r'</?div\b[^>]*>',text[start:]):
        depth += -1 if match[0].startswith('</') else 1
        if depth==0:return text[start:start+match.end()]
    raise AssertionError('Unclosed category')

def split_research_topics(root, original, check=False):
    groups={}
    for key in TOPICS:
        match=re.search(r'<div class="research-note-group" id="'+key+'">',original)
        assert match,key
        groups[key]=balanced_div(original,match.start())
    topic_nav=re.search(r'<nav class="research-topics" aria-label="研究テーマを選ぶ">.*?</nav>',original,re.S)[0]
    labels={m[1]:m[2] for m in re.finditer(r'<a href="#([^"]+)">(.*?)</a>',topic_nav,re.S)}
    assert set(labels)==set(TOPICS)
    def path(key):return BASE+'topics/'+key+'/'
    new_nav=topic_nav
    for key in TOPICS:new_nav=new_nav.replace('href="#'+key+'"','href="'+path(key)+'"')
    head=re.search(r'<head>(.*?)</head>',original,re.S)[1]
    before_main=original.split('<main',1)[0].split('</head>',1)[1]
    footer=original.split('</main>',1)[1]
    footer=re.sub(r'<script\b[^>]*enshu-research\.js[^>]*></script>','',footer)
    credits=re.search(r'<!-- iwata-photo:credits -->.*?<!-- /iwata-photo:credits -->',original,re.S)
    credits=credits[0] if credits else ''
    outputs={}
    for i,key in enumerate(TOPICS):
        label=re.sub('<[^>]+>','',labels[key]).strip()
        title=re.sub(r'\s*\d+本$','',label).strip()
        description=title+'の研究ノート一覧。問い・資料・分析・別の読み・検証方法を、各ノートで確かめます。'
        url='https://iwata-monogatari.net'+path(key)
        h=re.sub(r'<meta name="iwata:(?:published|category)"[^>]*>','',head)
        h=re.sub(r'<title>.*?</title>','<title>'+html.escape(label)+'｜遠州弁研究ノート｜磐田物語</title>',h)
        h=re.sub(r'<link rel="canonical" href="[^"]*">','<link rel="canonical" href="'+url+'">',h)
        for attr,name,value in [('name','description',description),('property','og:title',title),('property','og:description',description),('property','og:url',url)]:
            h=re.sub(r'<meta '+attr+'="'+name+r'" content="[^"]*">','<meta '+attr+'="'+name+'" content="'+html.escape(value,quote=True)+'">',h)
        cards=re.findall(r'<a href="(/enshu/research/[^"#]+/)"><div class="research-card-top">',groups[key])
        schema={'@context':'https://schema.org','@type':'CollectionPage','name':title,'description':description,'url':url,'inLanguage':'ja','isPartOf':{'@type':'CollectionPage','url':'https://iwata-monogatari.net'+BASE},'hasPart':[{'@type':'Article','url':'https://iwata-monogatari.net'+c} for c in cards]}
        h=re.sub(r'<script type="application/ld\+json">.*?</script>','<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False)+'</script>',h,flags=re.S)
        h+='<link rel="stylesheet" href="/assets/css/enshu-research-topic-layout.css?v=20261114">'
        links='<nav class="research-topic-return" aria-label="研究分類の前後"><a href="'+BASE+'#notebooks">← 研究一覧へ戻る</a><div>'
        for j,word in [(i-1,'前の分類'),(i+1,'次の分類')]:
            if 0<=j<len(TOPICS):
                other=TOPICS[j];links+='<a href="'+path(other)+'">'+word+'：'+re.sub('<[^>]+>','',labels[other])+'</a>'
        links+='</div></nav>'
        lower='<nav class="research-nav" aria-label="調査と資料"><a href="'+BASE+'#coverage">調査した範囲と未解決点</a><a href="'+BASE+'#lab">資料を集計する</a><a href="'+BASE+'#sources">文献と確認範囲</a></nav>'
        a=PHOTO_KEYS[i%len(PHOTO_KEYS)];b=PHOTO_KEYS[(i+5)%len(PHOTO_KEYS)]
        used=[a,b]+re.findall(r'data-iwata-photo="([^"]+)"',groups[key])
        hero='<header class="academy-section-heading research-topic-hero"><div><p>遠州弁研究ノート</p><h1>'+html.escape(title)+'</h1><p>'+html.escape(label)+' ／ 既存ノートを分類から読む。</p></div>'+figure(a)+'</header>'
        body=navigation(BASE)+ '<div class="breadcrumbs"><a href="/enshu/">学び舎</a> ／ <a href="'+BASE+'">研究ノート・集計室</a> ／ '+html.escape(title)+'</div>'+hero+links+'<p class="research-topic-photo-policy">写真は磐田の風景です。方言の採録地点や、各研究の調査を実施した場所を示すものではありません。</p>'+groups[key]+figure(b,'middle')+links+lower+photo_credits(used)+navigation(BASE)
        outputs['enshu/research/topics/'+key+'/index.html']='<!doctype html><html lang="ja"><head>'+h+'</head>'+before_main+'<main class="academy seminar research" id="research-content">'+body+'</main>'+footer
    index=original.replace(topic_nav,new_nav)
    for group in groups.values():index=index.replace(group,'',1)
    hero=re.search(r'<header class="research-hero">.*?</header>',index,re.S)
    # Photograph layout adds attributes to this header, so match its full tag.
    if not hero:hero=re.search(r'<header class="research-hero"[^>]*>.*?</header>',index,re.S)
    hero_new=hero[0]
    for anchor in ('coverage','lab','sources'):hero_new=re.sub(r'<a href="#'+anchor+r'">.*?</a>','',hero_new)
    index=index[:hero.start()]+hero_new+index[hero.end():]
    lower='<nav class="research-nav" aria-label="調査と資料"><a href="#coverage">調査した範囲と未解決点</a><a href="#lab">資料を集計する</a><a href="#sources">文献と確認範囲</a></nav>'
    marker=re.search(r'<section\b[^>]*\bid="coverage"[^>]*>',index)
    assert marker,'Coverage section must remain on index'
    index=index[:marker.start()]+lower+index[marker.start():]
    index=index.replace('</head>','<script defer src="/assets/js/enshu-research-topics-legacy.js?v=20261114"></script></head>',1)
    outputs['enshu/research/index.html']=index
    for name,text in outputs.items():
        target=root/name
        if check:assert target.exists() and target.read_text(encoding='utf8')==text,'Regenerate '+name
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf8',newline='\n')
    return groups
