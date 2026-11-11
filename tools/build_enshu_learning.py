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
art_words=['osshii','amake','ooe','chatto','tsuru','yabusettai','chinpurikaeru','dara','oyaku','mokko','choukeru','odokeru']
teasers=['おっしー、あんも、じゅるい。食卓のことばから。','雨の日も、まぶしい日も。空と道の表現。','座敷から庭先へ。家の中に残る呼び名。','ちゃっと出かけて、ちょっくら寄り道。','机を「つる」？ 動きと道具を読み解く。','しんどい、まぶしい、うっとうしいを言葉に。','すねる日も、ほっとする日も。気持ちの表現。','だら・だに・まい。会話をつくる語尾の違い。','家のつながり、人との距離。呼び名をたどる。','もっこ、えいかん。たくさんの言い方。','追う、驚く、ふざける。動きを比べて覚える。','知っているつもりの一語に、別の意味がある。']
cards='';sections=''
for number,scene in enumerate(learning['scenes'],1):
 a,b,c,v=[scene[k] for k in ['id','title','intro','words']];assert len(v)==len(set(v))
 image=art_words[number-1];assert image in by
 assert (R/f'assets/karuta/c006/{image}-900.webp').exists()
 cards+=f'<a class="course course-{a}" href="#scene-{a}"><div class="course-art" aria-hidden="true"><img src="/assets/karuta/c006/{image}-900.webp" width="900" height="1200" loading="lazy" alt=""></div><div class="course-copy"><span class="course-number">{number:02} / SCENE</span><strong>{b}</strong><p>{teasers[number-1]}</p><div class="course-bottom"><small>{len(v)}語を比べる</small><span class="course-arrow" aria-hidden="true">↗</span></div></div></a>'
 items=''
 for i in v:
  e=by[i];x=e['learning']['examples'][0]
  items+=f'<details class="lesson-word"><summary>{E(e["w"])}<span>{E(e["m"].split("。")[0])}</span></summary><p>{E(e["learning"]["point"])}</p><p class="pair">{E(x["dialect"])}<br><small>標準語：{E(x["standard"])}</small></p><a href="/c006?q={quote(e["w"])}#{i}">3つの例文・絵札・資料を読む →</a></details>'
 sections+=f'<section id="scene-{a}" class="scene"><div class="scene-heading"><span class="scene-number" aria-hidden="true">{number:02}</span><div><p class="eyebrow">SCENE / {E(a.upper())} <span class="scene-count">{len(v)}語</span></p><h2>{b}</h2></div></div><p class="scene-intro">{c}</p><div class="lesson-list">{items}</div><a class="course-return" href="#courses">コース一覧へ ↑</a></section>'
page=R/'enshu/index.html';original=page.read_text(encoding='utf-8');result=re.sub(r'<section id="scene-kitchen".*?(?=<section class="sources">)',lambda _:sections,original,flags=re.S)
assert result!=original or sections in original
course_section=f'<section id="courses"><div class="courses-heading"><div><p class="eyebrow">暮らしからひらく、12の入口</p><h2>あの場面の、<br><em>あのことば。</em></h2></div><p>今日は、どこから読みましょう。<br>気になる絵札を選んで、<br>ことばの違いを比べてみてください。</p></div><div class="courses">{cards}</div><p class="courses-credit">絵札は各語の作例をもとに制作した生成AIの創作画です。</p></section>'
result=re.sub(r'<section id="courses">.*?</section>',lambda _:course_section,result,count=1,flags=re.S)
serialized=json.dumps(learning,ensure_ascii=False,indent=2)+'\n'
if '--check' in sys.argv:
 assert serialized==p.read_text(encoding='utf-8') and result==original,'Run tools/build_enshu_learning.py'
else:
 p.write_text(serialized,encoding='utf-8');page.write_text(result,encoding='utf-8')
print(f'Enshu learning: {len(by)} words; {len(examples)} distinct per-word examples; {len(learning["scenes"])} courses; {len(by)*2} directional quiz items')
