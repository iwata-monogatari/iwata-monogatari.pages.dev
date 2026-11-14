"""Static word readings, with a searchable catalog and unchanged teaching data."""
import html,json,re
from urllib.parse import quote
from enshu_navigation import navigation,scene_path
from enshu_photo_layout import figure,credits,CSS as PHOTO_CSS
from enshu_records_pages import PHOTO_KEYS
E=lambda x:html.escape(str(x),quote=True)
BASE='/enshu/words/'
def word_path(id_):return BASE+id_+'/'

def word_pages(root,template,entries,scenes):
    head=re.search(r'<head>(.*?)</head>',template,re.S)[1]
    head=re.sub(r'<script\b[^>]*enshu-academy\.js[^>]*></script>','',head)
    head+='<link rel="stylesheet" href="'+PHOTO_CSS+'"><link rel="stylesheet" href="/assets/css/enshu-word-pages.css?v=20261114">'
    notice=re.search(r'<section class="notice">.*?</section>',template,re.S)[0]
    sources=re.search(r'<section class="sources">.*?</section>',template,re.S)
    sources=sources[0] if sources else ''
    dictionary=(root/'c006.html').read_text(encoding='utf8')
    def document(path,title,description,content,photo,index=False):
        h=re.sub(r'<title>.*?</title>','<title>'+E(title)+'｜磐田物語</title>',head)
        for attr,name,value in [('name','description',description),('property','og:title',title),('property','og:description',description),('property','og:url','https://iwata-monogatari.net'+path)]:
            h=re.sub(r'<meta '+attr+'="'+name+r'" content="[^"]*">','<meta '+attr+'="'+name+'" content="'+E(value)+'">',h)
        h=re.sub(r'<link rel="canonical" href="[^"]*">','<link rel="canonical" href="https://iwata-monogatari.net'+path+'">',h)
        schema={'@context':'https://schema.org','@type':'CollectionPage' if index else 'WebPage','name':title,'description':description,'url':'https://iwata-monogatari.net'+path,'inLanguage':'ja','isPartOf':{'@type':'CollectionPage','url':'https://iwata-monogatari.net'+BASE}}
        h=re.sub(r'<script type="application/ld\+json">.*?</script>','',h,flags=re.S)
        h+='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script>'
        h+='<script defer src="/assets/js/enshu-word-pages.js?v=20261114"></script>'
        return '<!doctype html><html lang="ja"><head>'+h+'</head><body><header class="gh-site"></header><main class="academy word-pages">'+navigation(BASE)+content+notice+sources+credits([photo])+navigation(BASE)+'</main><footer class="im-foot"></footer></body></html>\n'
    def hero(title,subtitle,photo):
        return '<header class="word-page-hero"><div><p class="eyebrow">遠州弁の学び舎 / 一語ずつ探す</p><h1>'+E(title)+'</h1><p>'+E(subtitle)+'</p></div>'+figure(photo)+'</header>'
    membership={e['id']:[s for s in scenes if e['id'] in s['words']] for e in entries}
    options='<option value="all">すべての場面</option>'+''.join('<option value="'+E(s['id'])+'">'+E(s['title'])+'</option>' for s in scenes)
    controls='<section class="word-catalog" id="word-list"><h2>ことばを選ぶ</h2><form id="word-search-form" action="'+BASE+'" method="get"><label>ことば・意味・作例<input id="word-search" name="q" type="search" placeholder="例：ぽんぽん、雨、食べる"></label><label>場面<select id="word-scene" name="scene">'+options+'</select></label><label>資料の種類<select id="word-source" name="source"><option value="all">すべてのことば（182語）</option><option value="dictionary">絵札のある辞典語（134語）</option><option value="historical">1921年の資料語（48語）</option></select></label><button type="submit">検索する</button><button type="button" id="word-clear">条件をクリア</button><button type="button" id="word-random">おまかせの一語</button></form><p id="word-status" role="status" aria-live="polite">182語を表示</p><noscript>下の182語のリンクはそのまま開けます。ページ内検索でも探せます。</noscript><div class="word-catalog-grid">'
    tiles=''
    for e in entries:
        searchable=' '.join([e['w'],e['k'],e['m'],e['ex'],e['std'],e['learning']['point']]+[x[k] for x in e['learning']['examples'] for k in ['dialect','standard']])
        tiles+='<a class="word-catalog-item" href="'+word_path(e['id'])+'" data-word-id="'+E(e['id'])+'" data-search="'+E(searchable)+'" data-source="'+('historical' if e.get('historical') else 'dictionary')+'" data-scenes="'+','.join(s['id'] for s in membership[e['id']])+'"><small>'+('1921年の資料語' if e.get('historical') else E(e['cat']))+'</small><strong>'+E(e['w'])+'</strong><span>'+E(e['m'])+'</span><small>意味・3作例・資料を読む →</small></a>'
    starters='<p class="word-page-starters">気になる一語から：<a href="'+word_path('ponpon')+'">ぽんぽん</a> ／ <a href="'+word_path('chatto')+'">ちゃっと</a> ／ <a href="'+word_path('amake')+'">あまけ</a></p>'
    mapping={e['id']:word_path(e['id']) for e in entries}
    content=hero('一語ずつ探す','182の学習語を、意味・3つの作例・使い分け・出典から読む。','street')+starters+controls+tiles+'</div></section><script type="application/json" id="word-page-map">'+json.dumps(mapping,ensure_ascii=False)+'</script>'
    outputs={'enshu/words/index.html':document(BASE,'一語ずつ探す｜遠州弁182語の一覧と検索','182の学習語を検索し、意味・3つの作例・使い分け・出典を個別ページで読む。',content,'street',True)}
    for ix,e in enumerate(entries):
        id_=e['id'];history=e.get('historical');photo=PHOTO_KEYS[ix%len(PHOTO_KEYS)]
        adjacent='<nav class="word-page-return" aria-label="ことばの読み進め方">'
        if ix:adjacent+='<a href="'+word_path(entries[ix-1]['id'])+'">← 前のことば</a>'
        adjacent+='<a href="'+BASE+'#word-list">一覧・検索へ戻る</a>'
        if ix+1<len(entries):adjacent+='<a href="'+word_path(entries[ix+1]['id'])+'">次のことば →</a>'
        adjacent+='</nav>'
        if history:
            picture='<figure class="word-original"><a href="https://dl.ndl.go.jp/pid/965680/1/'+str(history['frame'])+'"><img src="/assets/img/kotoba/gunshi-'+str(history['frame'])+'.webp" width="1200" height="853" loading="lazy" alt="磐田郡誌'+str(history['page'])+'頁を含む原画像"><figcaption>郡誌原画像 / 国立国会図書館デジタルコレクション</figcaption></a></figure>'
            material='<section class="word-material" id="word-sources"><h2>記録と資料</h2><p>1921年 / '+E(history['village'])+' / '+str(history['page'])+'頁・原表記</p><p>'+E(history['note'])+'</p><a href="/enshu/records/#'+id_+'">記録・原画像を読む →</a><p>出典：静岡県磐田郡教育会編『静岡県磐田郡誌』1921年、第23章「風俗」第7節「方言」、'+str(history['page'])+'頁。</p></section>'
        else:
            picture='<figure class="word-original"><a href="/assets/karuta/c006/'+id_+'-900.webp"><img src="/assets/karuta/c006/'+id_+'-300.webp" srcset="/assets/karuta/c006/'+id_+'-300.webp 300w, /assets/karuta/c006/'+id_+'-900.webp 900w" sizes="(max-width:700px) 65vw, 300px" width="900" height="1200" loading="lazy" alt="'+E(e['w'])+'の作例を描いた創作絵札"></a><figcaption>生成AIによる創作画。実景の復元や資料の挿絵ではありません。</figcaption></figure>'
            start=dictionary.index('data-id="'+id_+'"');end=dictionary.find('data-id="',start+10);entry=dictionary[start:end if end!=-1 else len(dictionary)]
            details=''
            for pattern in [r'<p class="note-word">.*?</p>',r'<table class="word-context">.*?</table>',r'<p class="word-src">.*?</p>',r'<p class="word-links">.*?</p>']:
                m=re.search(pattern,entry,re.S)
                if m:details+=m[0]
            material='<section class="word-material" id="word-sources"><h2>解説・資料</h2>'+details+'<p><a href="/c006?q='+quote(e['w'])+'#'+id_+'">使い分け・出典を辞典で読む →</a></p></section>'
        pairs=[{'dialect':e['ex'],'standard':e['std']}]+e['learning']['examples']
        examples='<section class="word-page-examples"><h2>'+('意味をつかむ置換作例' if history else '会話の作例')+'</h2>'+''.join('<div class="word-page-pair"><h3>作例 '+str(n)+'</h3><blockquote>'+E(x['dialect'])+'</blockquote><p>標準語：'+E(x['standard'])+'</p></div>' for n,x in enumerate(pairs,1))+'</section>'
        editorial='例文は資料の意味をつかむ編集部の置換作例です。当時の発話の引用や、現在の全域の使い方を示すものではありません。' if history else '例文は掲載した意味に基づく編集部の作例です。実際の発話の引用ではありません。'
        related='<nav class="word-reading-links" aria-label="場面と練習">'+''.join('<a href="'+scene_path(s['id'])+'">'+E(s['title'])+'のことばを読む →</a>' for s in membership[id_])+'<a href="/enshu/practice/">クイズで試す →</a><a href="/c008">文を変換する →</a></nav>'
        content='<p class="breadcrumbs"><a href="'+BASE+'">一語ずつ探す</a> ／ '+E(e['w'])+'</p>'+hero(e['w'],('1921年の資料語 / '+history['village'] if history else e['cat']),photo)+adjacent+'<article class="word-reading" data-word-id="'+id_+'"><div class="word-reading-intro">'+picture+'<section><h2>こんな意味</h2><p class="word-page-meaning">'+E(e['m'])+'</p><p>読み：'+E(e['k'])+'</p></section></div>'+examples+'<section class="word-page-usage"><h2>使うとき・読むときのヒント</h2><p>'+E(e['learning']['point'])+'</p><p>'+editorial+'</p></section>'+material+related+'</article><p class="word-photo-policy">写真は磐田の風景で、方言の採録現場や、この語の使用地点を示すものではありません。</p>'+adjacent
        outputs[word_path(id_).lstrip('/')+'index.html']=document(word_path(id_),e['w']+'の意味・作例・資料｜遠州弁の学び舎',e['m'],content,photo)
    return outputs
