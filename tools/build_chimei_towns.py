"""Render the reviewed town snapshot. Never fetch external data during a build."""
from pathlib import Path
import json,re,html,unicodedata
ROOT=Path(__file__).resolve().parents[1]
START='<!-- chimei:town-index:start -->';END='<!-- chimei:town-index:end -->'
def render(data):
 items=data['items'];assert len(items)==data['count']==186 and len({r['name'] for r in items})==186
 esc=lambda s:html.escape(s,quote=True)
 groups=[('あ','あいうえお'),('か','かきくけこがぎぐげご'),('さ','さしすせそざじずぜぞ'),('た','たちつてとだぢづでど'),('な','なにぬねの'),('は','はひふへほばびぶべぼぱぴぷぺぽ'),('ま','まみむめも'),('や','やゆよ'),('ら','らりるれろ'),('わ','わをん')]
 pieces=[]
 for key,letters in groups:
  subset=[r for r in items if r['reading'][0] in letters]
  if not subset:continue
  pieces.append('<section class="town-group" id="town-row-'+key+'"><h2>'+key+'行</h2><ul class="town-list">')
  for r in subset:
   labels=' '.join(x['label'] for x in r['address_sources']);search=r['name']+' '+r['reading']+' '+r['kana']
   related=r['related'] or '/search/?q='+__import__('urllib.parse',fromlist=['quote']).quote(r['name'])
   pieces.append('<li class="town-record" id="town-'+r['id']+'" data-town-id="'+r['id']+'" data-town-search="'+esc(search)+'" data-town-areas="'+esc(labels)+'"><p class="town-name"><strong>'+esc(r['name'])+'</strong></p><p class="town-reading">'+esc(r['reading'])+'</p><p><a href="'+esc(related)+'">'+esc(r['related_label'])+'</a></p><p class="town-transfer" data-chimei-entry="towns_document"><a data-chimei-link referrerpolicy="origin" href="https://fudosan.atawi.link/karte/?area=%E7%A3%90%E7%94%B0%E5%B8%82&amp;chimei=towns_document&amp;chimei_town='+r['code']+'">この町名で実家カルテへ</a></p>')
   if labels:pieces.append('<p class="town-source-links">住所の照合先：'+' ／ '.join('<a href="'+esc(x['url'])+'">'+x['label']+'</a>' for x in r['address_sources'])+'</p>')
   pieces.append('</li>')
  pieces.append('</ul></section>')
 assert sum(len([r for r in items if r['reading'][0] in letters]) for _,letters in groups)==186
 return '\n'.join(pieces)
def build():
 data=json.loads((ROOT/'data/chimei-towns.json').read_text(encoding='utf8'));p=ROOT/'chimei/towns/index.html';s=p.read_text(encoding='utf8');assert s.count(START)==s.count(END)==1
 a=s.index(START)+len(START);b=s.index(END);new=s[:a]+'\n'+render(data)+'\n'+s[b:]
 if new!=s:p.write_text(new,encoding='utf8')
 print('Chimei town index: 186 current names; four auxiliary old-area records excluded from address labels.')
if __name__=='__main__':build()
