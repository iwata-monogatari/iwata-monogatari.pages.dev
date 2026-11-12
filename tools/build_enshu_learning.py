"""Synchronize curated learning courses with the canonical dictionary, without adding article counts."""
from pathlib import Path
import json,html,re,sys
from urllib.parse import quote
from enshu_explorer import explorer_section
from enshu_study import build_study
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
course_section,sections,practice=build_study(learning,by,art_words,teasers)
page=R/'enshu/index.html';original=page.read_text(encoding='utf-8')
result=re.sub(r'<!-- course-lessons:start -->.*?<!-- course-lessons:end -->','',original,flags=re.S)
if '<section id="scene-kitchen"' in result:
 result=re.sub(r'<section id="scene-kitchen".*?(?=<section class="sources">)','',result,flags=re.S)
result=re.sub(r'<section id="courses".*?</section>',lambda _:course_section+sections,result,count=1,flags=re.S)
result=re.sub(r'<section id="practice".*?</section>',lambda _:practice,result,count=1,flags=re.S)
result=re.sub(r'<section id="cards".*?</section>',lambda _:explorer_section(learning,by),result,count=1,flags=re.S)
result=result.replace('enshu-academy.js?v=20261111','enshu-academy.js?v=20261112-explorer').replace('href="#cards">絵札で覚える','href="#cards">絵札でことば探し')
result=result.replace('enshu-academy.js?v=20261112-explorer','enshu-academy.js?v=20261112-study')
result=result.replace('href="#practice">10問に挑戦','href="#practice">クイズで試す')
if '/assets/css/enshu-word-explorer.css' not in result:
 result=result.replace('</head>','<link rel="stylesheet" href="/assets/css/enshu-word-explorer.css?v=20261112"></head>',1)
if '/assets/css/enshu-study.css' not in result:
 result=result.replace('</head>','<link rel="stylesheet" href="/assets/css/enshu-study.css?v=20261112"></head>',1)
serialized=json.dumps(learning,ensure_ascii=False,indent=2)+'\n'
if '--check' in sys.argv:
 assert serialized==p.read_text(encoding='utf-8') and result==original,'Run tools/build_enshu_learning.py'
else:
 p.write_text(serialized,encoding='utf-8');page.write_text(result,encoding='utf-8')
print(f'Enshu learning: {len(by)} words; {len(examples)} distinct per-word examples; {len(learning["scenes"])} courses; {len(by)*2} directional quiz items')
