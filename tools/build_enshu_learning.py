"""Synchronize curated learning courses with the canonical dictionary, without adding article counts."""
from pathlib import Path
import json,html,re,sys
from urllib.parse import quote
from enshu_explorer import explorer_section
from enshu_study import build_study
from enshu_materials import expand_materials
R=Path(__file__).resolve().parents[1];E=lambda x:html.escape(str(x),quote=True)
d=json.loads((R/'data/c006-dictionary.json').read_text(encoding='utf-8'))
p=R/'data/enshu-learning.json';learning=expand_materials(R,json.loads(p.read_text(encoding='utf-8')),d)
by={e['id']:e for e in learning['entries']};assert len(by)==len(learning['entries'])
examples=[]
for e in learning['entries']:
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
hero='''<header class="academy-hero"><p class="eyebrow">ENSHU / ことばを聞く。意味をほどく。</p><h1>遠州弁の学び舎</h1><p class="lead">一語を覚えて、会話の景色をひとつ増やす。</p><p>辞典の134語と、1921年の資料から選んだ48語を、546の語別作例で学べます。12の生活場面には、やり取りで読む24会話も加わりました。</p><div class="metrics"><span><b>182</b>学習語</span><span><b>546</b>語別作例</span><span><b>24</b>会話</span><span><b>12</b>コース</span></div><nav><a href="#courses">場面から読む</a><a href="#practice">クイズで試す</a><a href="#cards">一語ずつ探す</a><a href="/enshu/seminar/">資料から学ぶ8講座</a><a href="/enshu/research/">研究ノート・集計室</a><a href="/c006">辞典で調べる</a><a href="/c008">文を変換する</a></nav></header>'''
notice='''<section class="notice"><h2>ことばを学ぶときに</h2><p>語別作例は各語3例。24会話の48発話は別に数えています。作例・会話・使い分けは編集部が意味に基づいて構成した教材で、話者の発話引用ではありません。双方向の練習は各182問・計364問です。</p><p>追加48語は『静岡県磐田郡誌』の原表記・記録地・頁を付けた資料語です。例文は意味をつかむ置換作例で、当時の会話の復元や、現在も全地域で使うことを示すものではありません。既存134語のうち出典のある51語は辞典の資料欄へ進めます。資料のない語にも同じ出典があるとは扱いません。</p><p><a href="/enshu/seminar/">語形と語義、文法と民俗、調査の読み方を学ぶ8つの資料読解講座 →</a></p><p><a href="/enshu/research/">さらに深く：39本の研究ノートと、元データを確かめる資料の集計室 →</a></p></section>'''
result=re.sub(r'<header class="academy-hero">.*?</header>',lambda _:hero,result,count=1,flags=re.S)
result=re.sub(r'<section class="notice">.*?</section>',lambda _:notice,result,count=1,flags=re.S)
result=result.replace('遠州弁の学び舎｜134語・402例文・場面別12コース','遠州弁の学び舎｜182学習語・546作例・24会話')
result=re.sub(r'(<meta name="description" content=")[^"]*',r'\g<1>遠州弁の辞典134語と歴史資料48語を546語別作例・24会話・12場面で学ぶ。資料読解8講座と364問の双方向クイズ、出典付きの歴史語も。',result,count=1)
result=re.sub(r'(<meta property="og:description" content=")[^"]*',r'\g<1>182学習語・546語別作例・24会話と12コース。歴史資料は年代・記録地を示し、資料読解8講座で文法と暮らしを読み解く。',result,count=1)
result=result.replace('enshu-academy.js?v=20261111','enshu-academy.js?v=20261112-explorer').replace('href="#cards">絵札で覚える','href="#cards">絵札でことば探し')
result=result.replace('enshu-academy.js?v=20261112-explorer','enshu-academy.js?v=20261112-study')
result=result.replace('enshu-academy.js?v=20261112-study','enshu-academy.js?v=20261112-more')
result=result.replace('href="#practice">10問に挑戦','href="#practice">クイズで試す')
if '/assets/css/enshu-word-explorer.css' not in result:
 result=result.replace('</head>','<link rel="stylesheet" href="/assets/css/enshu-word-explorer.css?v=20261112"></head>',1)
if '/assets/css/enshu-study.css' not in result:
 result=result.replace('</head>','<link rel="stylesheet" href="/assets/css/enshu-study.css?v=20261112"></head>',1)
result=result.replace('enshu-study.css?v=20261112"','enshu-study.css?v=20261112-more"')
serialized=json.dumps(learning,ensure_ascii=False,indent=2)+'\n'
if '--check' in sys.argv:
 assert serialized==p.read_text(encoding='utf-8') and result==original,'Run tools/build_enshu_learning.py'
else:
 p.write_text(serialized,encoding='utf-8');page.write_text(result,encoding='utf-8')
print(f'Enshu learning: {len(by)} words; {len(examples)} distinct per-word examples; {len(learning["scenes"])} courses; {len(by)*2} directional quiz items')
