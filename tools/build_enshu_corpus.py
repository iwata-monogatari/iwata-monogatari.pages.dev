"""Build the source-checked historical lexicon and its thematic comparison index."""
from pathlib import Path
import json,html,re,sys,collections
from urllib.parse import quote
R=Path(__file__).resolve().parents[1];E=lambda s:html.escape(str(s),quote=True)
data=json.loads((R/'data/enshu-gunshi-corpus.json').read_text(encoding='utf-8'));rows=data['records']
groups=json.loads((R/'data/enshu-comparisons.json').read_text(encoding='utf-8'))
words=json.loads((R/'data/c006-dictionary.json').read_text(encoding='utf-8'))['entries'];current={e['w']:e for e in words}
assert len(rows)>=350 and len({e['id'] for e in rows})==len(rows)
assert len({(e['page'],e['form'],e['gloss'],e['village']) for e in rows})==len(rows)
for e in rows:
 assert e['form'] and e['gloss'] and e['village'] and 1242<=e['page']<=1254
 assert e['frame']==740+(e['page']-1242)//2
assert len(groups)==24 and len({g['id'] for g in groups})==24
for g in groups:
 assert len(g['intro'])>=90 and len(g['words'])>=2
 assert all(any(e['form']==w for e in rows) for w in g['words']),g['id']
template=(R/'enshu/index.html').read_text(encoding='utf-8')
header=re.search(r'<header class="gh-site".*?</header>',template,re.S)[0];footer=re.search(r'<footer\b.*?</footer>',template,re.S)[0]
N=len(rows);forms=len({e['form'] for e in rows});villages=sorted({e['village'] for e in rows});byform=collections.defaultdict(list)
for e in rows:byform[e['form']].append(e)
def source(e):return f'https://dl.ndl.go.jp/pid/965680/1/{e["frame"]}'
def shell(title,description,path,body,script=False):
 dataset={'@context':'https://schema.org','@type':'CollectionPage','name':title,'description':description,'url':'https://iwata-monogatari.net'+path,'inLanguage':'ja','datePublished':'2026-11-12','isPartOf':{'@type':'WebSite','name':'磐田物語','url':'https://iwata-monogatari.net/'}}
 return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)}｜磐田物語</title><meta name="description" content="{E(description)}"><link rel="canonical" href="https://iwata-monogatari.net{path}"><meta name="iwata:published" content="2026-11-12"><meta name="iwata:category" content="特別コンテンツ"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(description)}"><meta property="og:url" content="https://iwata-monogatari.net{path}"><meta property="og:type" content="website"><meta property="og:image" content="https://iwata-monogatari.net/assets/img/kotoba/gunshi-740.webp"><link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/assets/css/site-header.css"><link rel="stylesheet" href="/assets/css/enshu-academy.css?v=20261111"><link rel="stylesheet" href="/assets/css/enshu-academy-design.css?v=20261111"><link rel="stylesheet" href="/assets/css/enshu-corpus.css?v=20261111"><script type="application/ld+json">{json.dumps(dataset,ensure_ascii=False).replace('<',chr(92)+'u003c')}</script>{'<script defer src="/assets/js/enshu-corpus.js?v=20261111"></script>' if script else ''}</head><body>{header}<main class="academy archive">{body}</main>{footer}</body></html>'''
nav='<nav class="archive-nav"><a href="/enshu/">学び舎の12コース</a><a href="/enshu/records/">380記録を調べる</a><a href="/enshu/compare/">24テーマで比べる</a><a href="/c006">現行134語の辞典</a><a href="/c008">変換ツール</a></nav>'
policy=f'''<aside class="archive-policy"><strong>1921年の記録として読む</strong><p>『静岡県磐田郡誌』第23章「風俗」第7節「方言」の1242〜1254頁から、原画像で照合した{N}記録を選録しました。原表記は{forms}種類。同じ形でも意味や記録地が異なる行は別記録です。現行辞典134語との重なりや、同じ意味の別形も含みます。</p><p>大きな仮名・旧仮名を含む語形を残し、意味欄は対応語と原注を読みやすく整理しています。原表記の判読を留保した項目は除外し、対応語の関係を確定できない項目には、その留保を明記しています。全文翻刻や現代の全域調査ではなく、古い記録地には現在の磐田市域外も含まれます。</p></aside>'''
pages_intro={1242:'方言節の冒頭です。総説のあとに語の一覧が始まり、福島村の項目が並びます。語形だけでなく、意味欄と漢字の原注を合わせて読むと、同音の別の語との取り違えを避けられます。',1243:'「あ」「い」の語が続きます。同じ「あそこ」に対応する形や、兄の呼び名などが複数の記録地に現れます。表の「同」は直前の記録地を引き継ぐため、ここでは旧町村名を展開して表示しています。',1244:'「う」「え」「お」の語が並ぶ頁です。汁、座敷、親類などの暮らしの語と、人物への評価を表す語が混在します。現在知っている意味を当てはめる前に、この頁の対応語を確かめてください。',1245:'「か」「き」「く」の語が中心です。なた、そらまめ、急須など、原注の漢字が対象を特定する手掛かりになります。「かたる」のように同じ形でも記録地と意味が違う項目があります。',1246:'「け」「こ」「さ」から「し」へ続く頁です。「けあめ」「けんけあめ」のような近い形に加え、「じるい」には道のぬかるみに関する原注があります。現行辞典との比較では原表記の違いを残しています。',1247:'「し」「す」「せ」の語が並びます。身なりや草履、つくし、語尾など、意味の分野はさまざまです。動詞の形は現代標準語と見た目が重なることがあり、括弧内や原注まで読む必要があります。',1248:'「そ」「た」「ち」の項目が続きます。朝飯や小さいことを表す形が複数見られます。ここに多くの形があることと、細かな強弱の使い分けまで判明していることは区別して読みます。',1249:'「ち」から「な」までが続く頁です。「つよ」は露と杖の二つの意味で別行に記録されています。同じ文字の行を消さず、記録地・意味・原注を一組として扱うことの大切さが分かります。',1250:'「な」「に」「ぬ」「ね」「の」「は」の語を読みます。「ねんぼう」のように同じ形でも道具と身体の部位という異なる対応があります。古い意味の説明は、現在の使用を保証するものではありません。',1251:'「は」「ひ」「ふ」「へ」「ほ」の語が並びます。動物、植物、道具、気持ちなどの呼び名が混在し、人や身体への当時の評価語も含まれます。意味を記録することと、現代の呼びかけに使うことを区別します。',1252:'「ほ」から「や」へ続く頁です。ごみや道具、貝・虫・鳥の名前、子守などの語が見られます。同じ表記の項目が別の地域で別の意味に対応するときは、それぞれの記録を別に読んでください。',1253:'「や」「ゆ」「よ」「ら」「り」「れ」「ろ」「わ」の語が並ぶ頁です。「ら」など現行辞典とも比べられる語がありますが、資料の意味欄と現代の説明を無条件に同一視しません。',1254:'方言節の末尾です。前頁から草鞋の語が続き、そのあと浦川村の記録があります。同じ見開きで次章「変災」が始まるため、方言の項目と次章本文を取り違えずに読む必要があります。'}
chapters=''
for page in range(1242,1255):
 subset=[e for e in rows if e['page']==page];frame=740+(page-1242)//2
 image=f'<figure class="source-thumb"><a href="https://dl.ndl.go.jp/pid/965680/1/{frame}"><img src="/assets/img/kotoba/gunshi-{frame}.webp" width="1200" height="853" loading="lazy" alt="磐田郡誌{page}頁を含む見開きの原画像"><span>原画像を開く ↗</span></a><figcaption>国立国会図書館デジタルコレクション</figcaption></figure>' if page%2==0 else ''
 cards=''
 for e in subset:
  c=current.get(e['form']);link=f'<a href="/c006?q={quote(c["w"])}#{c["id"]}">現行辞典と比較する →</a>' if c else ''
  cards+=f'<article class="record" id="{e["id"]}" data-search="{E(e["form"]+" "+e["gloss"]+" "+e["note"])}" data-village="{E(e["village"])}" data-page="{page}"><div class="record-meta"><span>1921 / {page}頁</span><a href="#{e["id"]}" aria-label="{E(e["form"])}の記録へのリンク">#</a></div><h3>{E(e["form"])}</h3><p class="record-gloss">{E(e["gloss"])}</p><p class="record-place">記録地：{E(e["village"])}</p>{f"<p class=\"record-note\">{E(e[chr(110)+chr(111)+chr(116)+chr(101)])}</p>" if e["note"] else ""}<div class="record-links"><a href="{source(e)}">原資料{page}頁 ↗</a>{link}</div></article>'
 chapters+=f'<section class="source-chapter" id="page-{page}"><div class="source-heading"><div><p class="eyebrow">原資料を一頁ずつ / {len(subset)}記録</p><h2>{page}<small>頁</small></h2><p>{pages_intro[page]}</p></div>{image}</div><div class="record-grid">{cards}</div></section>'
body=f'''<div class="breadcrumbs"><a href="/enshu/">遠州弁の学び舎</a> ／ 郷土資料辞典</div><header class="archive-hero"><p class="eyebrow">ENSHU WORD ARCHIVE / 1921</p><h1>百年前のことばを、<br><em>一語ずつひらく。</em></h1><p>磐田郡誌の遠州ことば資料辞典</p><div class="archive-metrics"><span><b>{N}</b>記録</span><span><b>{forms}</b>原表記</span><span><b>13</b>頁を照合</span></div><p>家の呼び名、動植物、道具、暮らしの動作。<br>記録地と原資料へ戻れる、遠州のことばの書庫です。</p>{nav}</header>{policy}<section class="archive-search" aria-label="資料の検索"><h2>ことば・意味・記録地から探す</h2><div class="archive-controls"><label for="corpus-search">ことば・意味<input type="search" id="corpus-search" placeholder="例：小さい、かたる、たにし"></label><label for="corpus-village">1921年の記録地<select id="corpus-village"><option value="">すべての記録地</option>{''.join(f'<option>{E(v)}</option>' for v in villages)}</select></label><label for="corpus-page">原資料の頁<select id="corpus-page"><option value="">すべての頁</option>{''.join(f'<option value="{p}">{p}頁</option>' for p in range(1242,1255))}</select></label><button id="corpus-clear" type="button">条件をクリア</button></div><p id="corpus-status" role="status" aria-live="polite">{N}記録を表示</p><p>大きな仮名や旧仮名を含む原表記で検索できます。「つ」と「っ」などは別に扱います。意味を入力して探すこともできます。</p><noscript>絞り込みはJavaScriptを使います。下の全記録と頁ごとのリンクはそのまま読めます。</noscript><nav class="page-jump">{''.join(f'<a href="#page-{p}">{p}頁</a>' for p in range(1242,1255))}</nav></section><div id="corpus-records">{chapters}</div><section class="archive-end"><h2>似たことばを、まとめて読む</h2><p>小さいと言う形、汁の呼び名、同じ表記で意味が違う語。24のテーマから資料を横断して読めます。</p><a href="/enshu/compare/">ことばの比較帖へ →</a><p>出典：静岡県磐田郡教育会編『静岡県磐田郡誌』1921年、第23章「風俗」第7節「方言」、1242〜1254頁。画像は国立国会図書館デジタルコレクション。2026年11月11日原画像照合、12日公開。</p><a href="https://dl.ndl.go.jp/pid/965680">原書の書誌と本文 ↗</a></section>'''
outputs={R/'enshu/records/index.html':shell(f'遠州ことば資料辞典｜磐田郡誌の{N}記録',f'1921年の磐田郡誌から{N}記録・{forms}原表記を原画像照合。意味・旧町村・本文頁・原資料へのリンク付きで検索。','/enshu/records/',body,True)}
tiles=''.join(f'<a href="#compare-{g["id"]}"><span>{n:02}</span><strong>{g["title"]}</strong><small>{sum(len(byform[w]) for w in g["words"])}記録を比較 →</small></a>' for n,g in enumerate(groups,1))
sections=''
for n,g in enumerate(groups,1):
 table=''
 for form in g['words']:
  for e in byform[form]:table+=f'<tr><th scope="row"><a href="/enshu/records/#{e["id"]}">{E(e["form"])}</a></th><td>{E(e["gloss"])}</td><td>{E(e["village"])}</td><td><a href="{source(e)}">{e["page"]}頁 ↗</a></td></tr>'
 sections+=f'<section class="compare-section" id="compare-{g["id"]}"><div class="scene-heading"><span class="scene-number" aria-hidden="true">{n:02}</span><div><p class="eyebrow">ことばの比較帖</p><h2>{g["title"]}</h2></div></div><p class="compare-intro">{E(g["intro"])}</p><div class="compare-table"><table><thead><tr><th scope="col">原表記</th><th scope="col">意味の要約</th><th scope="col">1921年の記録地</th><th scope="col">原資料</th></tr></thead><tbody>{table}</tbody></table></div><a class="course-return" href="#themes">テーマ一覧へ ↑</a></section>'
body=f'<div class="breadcrumbs"><a href="/enshu/">遠州弁の学び舎</a> ／ ことばの比較帖</div><header class="archive-hero compare-hero"><p class="eyebrow">ENSHU / 24 READINGS</p><h1>似ていることば。<br><em>違って見える暮らし。</em></h1><p>郷土資料を、24のテーマから読み比べる。</p>{nav}</header>{policy}<section id="themes"><p class="eyebrow">意味と記録地を、横に並べて。</p><h2>今日はどの違いを読みますか。</h2><div class="comparison-tiles">{tiles}</div></section>{sections}<section class="archive-end"><h2>原資料へ戻って確かめる</h2><p>各表の意味は原画像の対応語・原注を読みやすく整理したものです。比較のための解説は編集部によるもので、当時の話者への新しい聞き取りではありません。推測の原注は推測と明記し、使い分けを資料以上に断定していません。</p><a href="/enshu/records/">380記録の資料辞典へ →</a><p>出典：静岡県磐田郡教育会編『静岡県磐田郡誌』1921年、第23章「風俗」第7節「方言」、1242〜1254頁。原画像：国立国会図書館デジタルコレクション。</p></section>'
outputs[R/'enshu/compare/index.html']=shell('遠州ことばの比較帖｜24テーマで郷土資料を読む','雨、食卓、家、道具、動植物、語尾。同じ意味の別形や同じ形の別の意味を、原表記・旧町村・出典で比較。','/enshu/compare/',body)
for path,text in outputs.items():
 from enshu_navigation import middle_header,navigation
 url='/'+path.parent.relative_to(R).as_posix()+'/'
 text=re.sub(r'<nav class="archive-nav">.*?</nav>','',text,flags=re.S)
 text=middle_header(text,url).replace('</main>',navigation(url)+'</main>',1)
 text=text.replace('enshu-navigation.css?v=20261114-middle','enshu-navigation.css?v=20261114-archive')
 from enshu_photo_layout import apply_photos
 text=apply_photos(text,'/'+path.parent.relative_to(R).as_posix()+'/')
 if '--check' in sys.argv:assert path.exists() and path.read_text(encoding='utf-8')==text,str(path)
 else:path.parent.mkdir(exist_ok=True,parents=True);path.write_text(text,encoding='utf-8')
print(f'Historical lexicon: {N} records; {forms} original forms; {len(villages)} recorded areas; 24 comparison themes; 13 printed pages')
