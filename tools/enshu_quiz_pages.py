"""Separate scene quizzes while retaining the shared quiz engine and data."""
import html,json,re
from enshu_navigation import navigation,scene_path
from enshu_photo_layout import figure,credits,data as photo_data,CSS as PHOTO_CSS
from enshu_records_pages import PHOTO_KEYS
E=lambda x:html.escape(str(x),quote=True)
BASE='/enshu/practice/'
def quiz_path(id_):return BASE+('work-tools' if id_=='work' else id_)+'/'

def quiz_pages(template,practice,scenes):
 head=re.search(r'<head>(.*?)</head>',template,re.S)[1]
 head=re.sub(r'<script\b[^>]*enshu-academy\.js[^>]*></script>','',head)
 head+='<link rel="stylesheet" href="'+PHOTO_CSS+'"><link rel="stylesheet" href="/assets/css/enshu-quiz-pages.css?v=20261114"><script defer src="/assets/js/enshu-academy.js?v=20261114-scene-quiz"></script>'
 notice=re.search(r'<section class="notice">.*?</section>',template,re.S)[0]
 sources=re.search(r'<section class="sources">.*?</section>',template,re.S)
 sources=sources[0] if sources else ''
 paths={s['id']:quiz_path(s['id']) for s in scenes}
 def document(scene=None,ix=0):
  path=quiz_path(scene['id']) if scene else BASE
  title=scene['title']+'の遠州弁クイズ' if scene else 'クイズで試す｜12場面の一覧と出題設定'
  desc='問題数・出題方向・分類・資料を選んで練習し、作例と解説で確かめます。'
  photo=PHOTO_KEYS[ix%len(PHOTO_KEYS)] if scene else 'street'
  h=re.sub(r'<title>.*?</title>','<title>'+E(title)+'｜磐田物語</title>',head)
  for attr,name,value in [('name','description',desc),('property','og:title',title),('property','og:description',desc),('property','og:url','https://iwata-monogatari.net'+path)]:
   h=re.sub(r'<meta '+attr+'="'+name+r'" content="[^"]*">','<meta '+attr+'="'+name+'" content="'+E(value)+'">',h)
  h=re.sub(r'<link rel="canonical" href="[^"]*">','<link rel="canonical" href="https://iwata-monogatari.net'+path+'">',h)
  h=re.sub(r'<script type="application/ld\+json">.*?</script>','',h,flags=re.S)
  schema={'@context':'https://schema.org','@type':'WebPage','name':title,'url':'https://iwata-monogatari.net'+path,'inLanguage':'ja','isPartOf':{'@type':'CollectionPage','url':'https://iwata-monogatari.net'+BASE}}
  h+='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False)+'</script>'
  hero='<header class="quiz-page-hero"><div><p class="eyebrow">遠州弁の学び舎 / クイズで試す</p><h1>'+E(title)+'</h1><p>'+desc+'</p>'+('<p>この場面の'+str(len(scene['words']))+'語から出題します。</p>' if scene else '<p>場面を選ぶと、その場面の専用ページが開きます。下の出題設定では全182語からも練習できます。</p>')+'</div>'+figure(photo)+'</header>'
  adjacent='<nav class="quiz-page-return" aria-label="クイズの行き先"><a href="'+BASE+'#quiz-scenes">12場面の一覧・出題設定へ戻る</a>'
  if scene:adjacent+='<a id="quiz-course-return" href="'+scene_path(scene['id'])+'">← 「'+E(scene['title'])+'」を読む</a>'
  else:adjacent+='<a id="quiz-course-return" href="/enshu/courses/">← 場面の意味と会話を読む</a>'
  adjacent+='</nav>'
  body=practice.replace('<section id="practice"','<section data-quiz-page="'+(scene['id'] if scene else 'all')+'" id="practice"',1)
  if scene:
   body=body.replace('<option value="'+scene['id']+'">','<option value="'+scene['id']+'" selected>')
  listing=''
  if not scene:
   listing='<section id="quiz-scenes"><h2>12の場面から選ぶ</h2><div class="quiz-scene-grid">'+''.join('<a class="quiz-scene-card" href="'+quiz_path(s['id'])+'"><img src="/'+photo_data()[1][PHOTO_KEYS[n%len(PHOTO_KEYS)]]['outputs'][0]['path']+'" alt="" loading="lazy"><strong>'+E(s['title'])+'</strong><span>'+str(len(s['words']))+'語 / この場面のクイズへ →</span></a>' for n,s in enumerate(scenes))+'</div><p>一覧の写真は磐田の風景です。撮影地・作者・権利情報は、各場面のページと末尾の写真出典欄で確認できます。</p></section>'
  config='<script type="application/json" id="quiz-page-config">'+json.dumps({'scene':scene['id'] if scene else None,'paths':paths},ensure_ascii=False)+'</script>'
  content=hero+listing+adjacent+body+adjacent.replace(' id="quiz-course-return"','')+'<p class="quiz-photo-policy">写真は磐田の風景で、方言の採録地や各語の使用地点を示すものではありません。</p>'
  return '<!doctype html><html lang="ja"><head>'+h+'</head><body><header class="gh-site"></header><main class="academy quiz-pages">'+navigation(BASE)+content+notice+sources+credits([photo] if scene else PHOTO_KEYS[:len(scenes)])+navigation(BASE)+config+'</main><footer class="im-foot"></footer></body></html>\n'
 outputs={'enshu/practice/index.html':document()}
 for ix,scene in enumerate(scenes):outputs[quiz_path(scene['id']).lstrip('/')+'index.html']=document(scene,ix)
 return outputs
