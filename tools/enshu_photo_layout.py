"""Place attributed, real Iwata photographs without rewriting research prose."""
from pathlib import Path
from functools import lru_cache
import html,json,re
R=Path(__file__).resolve().parents[1]
E=lambda s:html.escape(str(s),quote=True)
CSS='/assets/css/enshu-photos.css?v=20261113'

@lru_cache(maxsize=1)
def data():
 return json.loads((R/'data/enshu-photo-plan.json').read_text(encoding='utf8'))['pages'],json.loads((R/'assets/enshu/photos/credits.json').read_text(encoding='utf8'))

def block(slot,content):return f'<!-- iwata-photo:{slot} -->{content}<!-- /iwata-photo:{slot} -->'

def strip_photos(text):
 text=re.sub(r'<!-- iwata-photo:([\w-]+) -->.*?<!-- /iwata-photo:\1 -->','',text,flags=re.S)
 return text.replace(' has-iwata-photo','')

def image(key,role='lead'):
 _,photos=data();p=photos[key];files=sorted(p['outputs'],key=lambda x:x['width']);large=files[-1]
 sizes='96px' if role=='thumb' else '(max-width:700px) calc(100vw - 36px), (max-width:1050px) 42vw, 440px'
 alt='' if role=='thumb' else p['caption']+'。'+p['date']+'撮影。'
 return f'<img src="/{files[0]["path"]}" srcset="'+', '.join('/'+f['path']+' '+str(f['width'])+'w' for f in files)+f'" sizes="{sizes}" width="{large["width"]}" height="{large["height"]}" alt="{E(alt)}" loading="lazy" decoding="async" data-iwata-photo="{E(key)}">'

def figure(key,slot='lead',caption=None):
 _,photos=data();p=photos[key];caption=caption or p['caption'];large=max(p['outputs'],key=lambda x:x['width'])
 return block(slot,f'<figure class="iwata-photo iwata-photo-{slot}" data-photo-place="{E(p["caption"])}"><a class="iwata-photo-image" href="/{large["path"]}" aria-label="{E(p["caption"])}の写真を大きく見る">{image(key,slot)}</a><figcaption><span class="iwata-photo-kicker">磐田の風景</span><strong>{E(caption)}</strong><span class="iwata-photo-date">{E(p["date"])}撮影</span><small>写真：{E(p["author"])} ／ <a href="{E(p["source"])}">原写真</a> ／ <a href="{E(p["license_url"])}" rel="license">{E(p["license"])}</a></small></figcaption></figure>')

def credits(keys):
 _,photos=data();keys=sorted(set(keys))
 items=''.join(f'<li><strong>{E(photos[k]["label"])}</strong> — {E(photos[k]["author"])}、{E(photos[k]["date"])}。<a href="{E(photos[k]["source"])}">原写真・撮影地</a> ／ <a href="{E(photos[k]["license_url"])}" rel="license">{E(photos[k]["license"])}</a></li>' for k in keys)
 return block('credits','<details class="iwata-photo-credits"><summary>写真の撮影地・出典について</summary><p>写真は、撮影地・撮影年を添えた磐田の風景です。本文の言語調査や過去の出来事を撮影した資料とは区別しています。画像の切り抜き・色調変更・生成補完はしていません。既存WebPは縮小・形式変換済み、新規写真はCommonsの縮小版です。</p><ul>'+items+'</ul></details>')

def before_nth(text,pattern,n,addition):
 matches=list(re.finditer(pattern,text))
 assert len(matches)>=n,(pattern,n,len(matches))
 i=matches[n-1].start();return text[:i]+addition+text[i:]

def apply_photos(text,url):
 if 'class="academy archive compare-paging"' in text:return text
 # Paginated records own their per-page photographs and inline reading breaks.
 if url.startswith('/enshu/records/') and 'class="academy archive records-paging"' in text:return text
 plan,_=data()
 if url not in plan:
  assert not url.startswith('/enshu/research/'),'新規研究ノートには撮影地確認済みの写真計画を追加してください: '+url
  return text
 text=normalize_original(text);p=plan[url];used=[p['lead'],p['middle']]
 text=text.replace('</head>',block('style',f'<link rel="stylesheet" href="{CSS}">')+'</head>',1)
 kind=p['kind'];lead=figure(p['lead']);middle_caption=None
 if url=='/enshu/research/house-name-form-and-origin/':middle_caption='掛塚のつるや酒店（靏谷家住宅）。本文の「つたや」とは別の商家です。'
 middle=figure(p['middle'],'middle',middle_caption)
 if kind=='research-note':
  match=re.search(r'<header class="research-note-head">(.*?)</header>',text,re.S);assert match
  split=match[1].index('<div class="research-finding">')
  head='<header class="research-note-head has-iwata-photo">'+block('copy-open','<div class="iwata-note-copy">')+match[1][:split]+block('copy-close','</div>')+lead+match[1][split:]+'</header>'
  text=text[:match.start()]+head+text[match.end():]
  assert '<section id="alternatives">' in text
  text=text.replace('<section id="alternatives">',middle+'<section id="alternatives">',1)
 elif kind=='research-index':
  match=re.search(r'(<header class="research-hero">.*?)(<figure>.*?</figure>)(</header>)',text,re.S);assert match
  replacement=match[1]+block('aside-open','<aside class="iwata-hero-aside">')+lead+match[2]+block('aside-close','</aside>')+match[3]
  text=text[:match.start()]+replacement+text[match.end():]
  text=text.replace('<div class="research-note-group" id="livelihood">',middle+'<div class="research-note-group" id="livelihood">',1)
 else:
  if kind in ('seminar','records','compare'):
   match=re.search(r'(<header class="(?:seminar-hero|archive-hero)[^"]*")(>)(.*?)(</header>)',text,re.S);assert match
   replacement=match[1]+' data-iwata-layout="intro"'+match[2]+block('copy-open','<div class="iwata-intro-copy">')+match[3]+block('copy-close','</div>')+lead+match[4]
   text=text[:match.start()]+replacement+text[match.end():]
   if kind=='seminar':
    for nth,key in reversed([(3,p['middle']),(5,'market'),(7,'bridge')]):text=before_nth(text,r'<article class="seminar-lesson"',nth,figure(key,'pause-'+str(nth)));used.append(key)
   elif kind=='compare':
    for nth,key in reversed([(7,p['middle']),(13,'tea'),(19,'market')]):text=before_nth(text,r'<section class="compare-section"',nth,figure(key,'pause-'+str(nth)));used.append(key)
   else:
    marker='<section class="source-chapter" id="page-1248">';assert marker in text;text=text.replace(marker,marker+middle,1)
  elif kind=='blog':
   start=text.index('<div class="post-body">');end=text.index('<!-- /post-body -->',start);part=text[start:end]
   part=before_nth(part,r'<h2\b',4,middle);part=before_nth(part,r'<h2\b',1,lead)
   text=text[:start]+part+text[end:]
  else:raise AssertionError(kind)
 # Tiny contextual thumbnails shorten the text wall in research catalogs and related reading.
 def thumb(m):
  target='/enshu/research/'+m[1]+'/'
  if target not in plan:return m[0]
  key=plan[target]['lead'];used.append(key)
  return m[0]+block('thumb',image(key,'thumb'))
 text=re.sub(r'<a href="/enshu/research/([^/]+)/"><div class="research-card-top">',thumb,text)
 text=text.replace('</main>',credits(used)+'</main>',1)
 return text

def normalize_original(text):
 return strip_photos(text).replace(' data-iwata-layout="intro"','')

if __name__=='__main__':
 import sys
 for url in data()[0]:
  f=R/url.lstrip('/')/'index.html';old=f.read_text(encoding='utf8');new=apply_photos(old,url)
  if '--check' in sys.argv:assert new==old,('Photo layout out of date',url)
  else:f.write_text(new,encoding='utf8',newline='\n')
