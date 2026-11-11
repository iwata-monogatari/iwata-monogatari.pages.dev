"""Synchronize curated learning courses with the canonical dictionary, without adding article counts."""
from pathlib import Path
import json,html,re,sys
from urllib.parse import quote
R=Path(__file__).resolve().parents[1];E=lambda x:html.escape(str(x),quote=True)
d=json.loads((R/'data/c006-dictionary.json').read_text(encoding='utf-8'))
p=R/'data/enshu-learning.json';learning=json.loads(p.read_text(encoding='utf-8'));learning['entries']=d['entries']
by={e['id']:e for e in d['entries']};assert len(by)==len(d['entries'])
examples=[]
for e in d['entries']:
 assert len(e['learning']['examples'])==2 and len(e['learning']['point'])>20
 pairs=[e['ex']]+[x['dialect'] for x in e['learning']['examples']]
 normalize=lambda s:re.sub(r'[\s、。]','',s)
 assert len(set(map(normalize,pairs)))==3,e['id']
 examples.extend(pairs)
sections=''
for scene in learning['scenes']:
 a,b,c,v=[scene[k] for k in ['id','title','intro','words']];assert len(v)==len(set(v))
 items=''
 for i in v:
  e=by[i];x=e['learning']['examples'][0]
  items+=f'<details class="lesson-word"><summary>{E(e["w"])}<span>{E(e["m"].split("。")[0])}</span></summary><p>{E(e["learning"]["point"])}</p><p class="pair">{E(x["dialect"])}<br><small>標準語：{E(x["standard"])}</small></p><a href="/c006?q={quote(e["w"])}#{i}">3つの例文・絵札・資料を読む →</a></details>'
 sections+=f'<section id="scene-{a}" class="scene"><p class="eyebrow">SCENE / {E(a.upper())}</p><h2>{b}</h2><p>{c}</p>{items}<a href="#courses">コース一覧へ ↑</a></section>'
page=R/'enshu/index.html';original=page.read_text(encoding='utf-8');result=re.sub(r'<section id="scene-kitchen".*?(?=<section class="sources">)',lambda _:sections,original,flags=re.S)
assert result!=original or sections in original
serialized=json.dumps(learning,ensure_ascii=False,indent=2)+'\n'
if '--check' in sys.argv:
 assert serialized==p.read_text(encoding='utf-8') and result==original,'Run tools/build_enshu_learning.py'
else:
 p.write_text(serialized,encoding='utf-8');page.write_text(result,encoding='utf-8')
print(f'Enshu learning: {len(by)} words; {len(examples)} distinct per-word examples; {len(learning["scenes"])} courses; {len(by)*2} directional quiz items')
