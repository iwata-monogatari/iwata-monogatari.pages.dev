"""Build research notes and an auditable corpus workbench from frozen sources."""
from pathlib import Path
from collections import Counter
import csv, hashlib, html, io, json, re, sys
from enshu_research_content import make_notes
from enshu_research_sound import SOUND_SOURCES, make_sound_notes
from enshu_research_grammar import GRAMMAR_SOURCES, make_grammar_notes
from enshu_research_honorific import HONORIFIC_SOURCES, make_honorific_notes
from enshu_research_kinship import KINSHIP_SOURCES, make_kinship_notes
from enshu_research_extended import EXTENDED_SOURCES, make_extended_notes, augment_existing_notes
from enshu_research_coverage import build_coverage
from enshu_photo_layout import apply_photos
from enshu_research_language import LANGUAGE_SOURCES, make_language_notes, augment_language_notes, language_coverage
from enshu_research_new_sources import NEW_SOURCES, make_new_source_notes
from enshu_research_new_supplements import COMPARATIVE_SOURCES, augment_new_source_notes
from enshu_research_new_coverage import new_source_coverage
from enshu_research_regional import REGIONAL_SOURCES, make_regional_notes
from enshu_research_regional_supplements import augment_regional_notes
from enshu_research_regional_coverage import regional_coverage
from enshu_research_systematic import SYSTEMATIC_SOURCES, make_systematic_notes
from enshu_research_systematic_supplements import EXTRA_SOURCES, augment_systematic_notes
from enshu_research_systematic_coverage import systematic_coverage

R=Path(__file__).resolve().parents[1]
E=lambda value:html.escape(str(value),quote=True)
DATE='2026-11-12'
BASE='/enshu/research/'
corpus_file=R/'data/enshu-gunshi-corpus.json'
corpus=json.loads(corpus_file.read_text(encoding='utf8'))
records=corpus['records']
fpjd=json.loads((R/'data/c006-fpjd.json').read_text(encoding='utf8'))
forms=Counter(r['form'] for r in records)
regions=Counter(r['village'] for r in records)
duplicate_forms={f for f,n in forms.items() if n>1}
assert len(records)==380 and len(forms)==376 and len(duplicate_forms)==4
assert len(regions)==13 and sum(n for _,n in regions.most_common(3))==315

SOURCES={
 'gunshi':('史料｜1921年の郡誌','静岡県磐田郡教育会編『静岡県磐田郡誌』1921年、第23章「風俗」第7節「方言」、1242–1254頁。','https://dl.ndl.go.jp/pid/965680','本サイトの原画像照合済み選録380行を使用。全文翻刻ではありません。原表記と意味の整理・原注を区別し、記録地のラベルを保持。原画像照合は2026年11月11日、今回の集計は11月12日。'),
 'fpjd':('調査データ｜磐田市1地点','国立国語研究所「全国方言分布調査（FPJD）」公開データ、2025年10月7日版。地点137874-34763。','https://www2.ninjal.ac.jp/hogen/dp/fpjd/fpjd_index.html','2026年10月12日取得の既存照合データを使用。287回答・211質問。原回答、設問、注記を保持。国立国語研究所の共同研究「方言の形成過程解明のための全国方言分布調査」の成果に基づく。'),
 'notes':('調査の凡例｜回答と注記','国立国語研究所「FPJD公開データの注記に用いた記号」。','https://www2.ninjal.ac.jp/hogen/dp/fpjd/fpjd_data_notes.html','2026年11月12日確認。〈 〉は話者、（ ）は調査者の注記。ゆ＝語形を提示した誘導回答、多＝使うことが多い。使用者人口の比率を示す記号ではありません。'),
 'fujiwara':('研究論文｜形態・統語・用法','藤原あかね（2021）「静岡県中部方言における推量表現『ラ』『ダラ』について」『阪大社会言語学研究ノート』17、1–17頁。','https://doi.org/10.18910/81761','本文の対象・方法（1–2頁）、接続（6–8頁）、生起位置（9頁）、比較と結論（15–16頁）を確認。牧之原市出身の著者の内省を軸にした記述。磐田市全域の調査と扱いません。'),
 'shiraiwa':('研究論文｜談話的機能への変化','白岩広行（2011）「方言の推量形式における意味変化―談話的機能へ―」『阪大日本語研究』23、57–77頁。','https://doi.org/10.18910/6730','対象と資料（57–61頁）、内省の方法と分析（65–68頁）、形態面と意味面の区別（72頁）を確認。岡崎・静岡・茅ヶ崎が対象。磐田の追跡調査を行った論文ではありません。'),
 'mingu':('研究機関の解説｜物と暮らし','東京文化財研究所 無形文化遺産部「無形文化遺産と民具」。','https://www.tobunken.go.jp/ich/research/mingu/introduction/','2026年11月12日確認。呼称・製作・使用・流通などの情報と物を結び付ける視点を参照。本サイトの聞き取り様式は編集部による設計で、現地調査の実績ではありません。'),
}

SOURCES.update(SOUND_SOURCES)
SOURCES.update(GRAMMAR_SOURCES)
SOURCES.update(HONORIFIC_SOURCES)
SOURCES.update(KINSHIP_SOURCES)
SOURCES.update(EXTENDED_SOURCES)
SOURCES.update(LANGUAGE_SOURCES)
SOURCES.update(NEW_SOURCES)
SOURCES.update(COMPARATIVE_SOURCES)
SOURCES.update(REGIONAL_SOURCES)
SOURCES.update(SYSTEMATIC_SOURCES)
SOURCES.update(EXTRA_SOURCES)

def table(head,rows,caption='比較のための資料表'):
    return '<p class="research-table-hint">表は横にスクロールできます →</p><div class="seminar-table" tabindex="0" role="region" aria-label="'+E(caption)+'"><table><caption>'+E(caption)+'</caption><thead><tr>'+''.join(f'<th scope="col">{E(h)}</th>' for h in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<th scope="row">{v}</th>' if i==0 else f'<td>{v}</td>' for i,v in enumerate(row))+'</tr>' for row in rows)+'</tbody></table></div>'

def cite(sid,label):
    assert sid in SOURCES
    return f'<a class="seminar-cite" href="#source-{sid}">［{E(label)}］</a>'

def gunshi(*wanted,record_ids=None):
    selected=[r for r in records if r['form'] in wanted or r['id'] in (record_ids or [])]
    assert set(wanted)<=set(r['form'] for r in selected)
    assert set(record_ids or [])<=set(r['id'] for r in selected)
    return table(['原表記','意味の整理・原注','記録地の原ラベル','原資料'],[
        [f'<a href="/enshu/records/#{r["id"]}">{E(r["form"])}</a>',E(r['gloss'])+(f'<small>{E(r["note"])}</small>' if r['note'] else ''),E(r['village']),f'<a href="https://dl.ndl.go.jp/pid/965680/1/{r["frame"]}">{r["page"]}頁 ↗</a>'] for r in selected], '郡誌選録からの比較表（刊行1921年）')

def responses(*questions):
    selected=[r for q in questions for r in fpjd['records'] if r['question']==q]
    assert set(questions)==set(r['question'] for r in selected)
    return table(['設問コード・項目','回答語形','原注記'],[
        [f'<small>{E(r["question"])}</small>{E(r["item"])}',f'<a href="/c172#fpjd-{r["id"]}">{E(r["form"])}</a>',E(r['note']) or '注記なし'] for r in selected], 'FPJD・磐田市1地点（選んだ設問の全回答）')

region_table=table(['記録地の原ラベル','記録数','ラベル内の原表記数','380行中の割合'],[
    [E(v),str(n),str(len({r['form'] for r in records if r['village']==v})),f'{n/len(records)*100:.1f}％'] for v,n in regions.most_common()], '郡誌選録380行の構成（人口・使用率ではありません）')
notes=make_notes(table,gunshi,responses,cite,region_table)
notes.extend(make_sound_notes(table,cite))
notes.extend(make_grammar_notes(table,gunshi,responses,cite))
notes.extend(make_honorific_notes(table,gunshi,responses,cite))
notes.extend(make_kinship_notes(table,gunshi,responses,cite))
original_slugs={n['slug'] for n in notes}
notes.extend(make_extended_notes(table,gunshi,responses,cite))
supplements=augment_existing_notes(notes,table,gunshi,cite)
notes.extend(make_language_notes(table,responses,cite))
language_supplements=augment_language_notes(notes,table,responses,cite)
for slug,headings in language_supplements.items():supplements.setdefault(slug,[]).extend(headings)
notes.extend(make_new_source_notes(table,responses,cite))
new_source_supplements=augment_new_source_notes(notes,table,responses,cite)
for slug,headings in new_source_supplements.items():supplements.setdefault(slug,[]).extend(headings)
notes.extend(make_regional_notes(table,responses,cite))
regional_supplements=augment_regional_notes(notes,table,responses,cite)
for slug,headings in regional_supplements.items():supplements.setdefault(slug,[]).extend(headings)
notes.extend(make_systematic_notes(table,cite))
systematic_supplements=augment_systematic_notes(notes,table,cite)
assert len({n['slug'] for n in notes})==len(notes)
for n in notes:
    n['published']='2026-11-12' if n['slug'] in original_slugs else '2026-11-13'
    if n.get('group')=='systematic':n['published']='2026-11-14'
kin_count=sum(n.get('group')=='kinship' for n in notes)
language_count=sum(n.get('group')=='language' for n in notes)
new_source_count=sum(n.get('group')=='new-sources' for n in notes)
sound_count=sum(n.get('group')=='sound' for n in notes)
variation_count=sum(n.get('group')=='variation' for n in notes)
life_count=sum(n.get('group')=='livelihood' for n in notes)
life_topics={
 'water':('漁と水辺',['yuto-market-house-names','hamanako-gear-and-fishing-method','sappa-and-boat-classification','fish-names-growth-and-products','noriko-and-seasonal-work','ferry-person-role-and-right','kawadome-kawaake-and-signs']),
 'forest':('山・林業と運ぶ仕事',['sakuma-forest-transport','yamatsukuri-and-toguwa','kureki-transport-and-counting','atago-paper-craft-explanation']),
 'farm':('農・茶・養蚕と材料',['livelihood-change-and-language','sericulture-house-memory','tea-process-and-skill-language','parent-child-metaphor-in-taro','crop-names-and-compounds','enshu-tatami-and-fibre-names']),
 'trade':('商い・技術・仕事の仕組み',['house-names-and-trade','fukude-textile-vocabulary','yotabi-work-time','craft-names-and-jisshoku','salt-bale-and-measure','salt-boundary-language','kasai-market-space-names'])}
assert {x for _,xs in life_topics.values() for x in xs}=={n['slug'] for n in notes if n.get('group')=='livelihood'}


def source_archive_link(key):
    if key not in SYSTEMATIC_SOURCES and key not in EXTRA_SOURCES:return ''
    match=re.search(r'https://web\.archive\.org/[^\s]+\.pdf',SOURCES[key][3])
    return ' ／ <a href="'+E(match[0])+'">確認した公開保存版へ ↗</a>' if match else ''

def bibliography(keys):
    return '<section id="sources" class="seminar-bibliography"><p class="eyebrow">REFERENCES / 確認範囲を明記</p><h2>出典に戻って読む</h2><ol>'+''.join(f'<li id="source-{k}"><h3>{E(SOURCES[k][0])}</h3><p>{E(SOURCES[k][1])}</p><p>{E(SOURCES[k][3])}</p><a href="{E(SOURCES[k][2])}">原資料・論文へ ↗</a>{source_archive_link(k)}</li>' for k in keys)+'</ol></section>'

template=(R/'enshu/index.html').read_text(encoding='utf8')
header=re.search(r'<header class="gh-site".*?</header>',template,re.S)[0]
footer=re.search(r'<footer\b.*?</footer>',template,re.S)[0]

def shell(title,description,url,body,article=False,script=False,published=None,modified=None):
    published=published or DATE
    modified=modified or published
    canonical='https://iwata-monogatari.net'+url
    schema={'@context':'https://schema.org','@type':'Article' if article else 'CollectionPage','name':title,'headline':title,'description':description,'url':canonical,'inLanguage':'ja','datePublished':published,'dateModified':modified,'author':{'@type':'Organization','name':'磐田物語 編集部','url':'https://iwata-monogatari.net/'}}
    if article:schema['isPartOf']={'@type':'CollectionPage','name':'遠州弁研究ノート','url':'https://iwata-monogatari.net'+BASE}
    else:schema['hasPart']=[{'@type':'Article','name':n['title'],'url':canonical+n['slug']+'/'} for n in notes]
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)}｜磐田物語</title><meta name="description" content="{E(description)}"><link rel="canonical" href="{canonical}"><meta name="iwata:published" content="{published}"><meta name="iwata:category" content="特別コンテンツ"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(description)}"><meta property="og:url" content="{canonical}"><meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:image" content="https://iwata-monogatari.net/assets/img/kotoba/gunshi-744.webp"><link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/assets/css/site-header.css"><link rel="stylesheet" href="/assets/css/enshu-academy.css?v=20261111"><link rel="stylesheet" href="/assets/css/enshu-seminar.css?v=20261112"><link rel="stylesheet" href="/assets/css/enshu-research.css?v=20261112b"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body>{header}<a class="research-skip" href="#research-content">本文へ</a><main class="academy seminar research" id="research-content">{body}</main>{footer}{'<script src="/assets/js/enshu-research.js?v=20261112" defer></script>' if script else ''}</body></html>'''

def cards(items):
    return '<div class="research-cards">'+''.join(f'<a href="{BASE}{n["slug"]}/"><div class="research-card-top"><span>{notes.index(n)+1:02}</span><small>{E(n["field"])}</small></div><h3>{E(n["title"])}</h3><p>{E(n["deck"])}</p><b>資料と分析を読む →</b></a>' for n in items)+'</div>'

nav='<nav class="research-nav"><a href="/enshu/">学び舎</a><a href="/enshu/seminar/">入門の8講座</a><a href="/enshu/records/">原記録の辞典</a><a href="/enshu/research/#lab">資料の集計室</a></nav>'
lab_rows=''.join(f'<tr><th scope="row">{E(v)}</th><td><span class="research-bar" style="--share:{n/122*100:.3f}%"></span><b>{n}</b> 行</td><td>{len({r["form"] for r in records if r["village"]==v})} 種類</td></tr>' for v,n in regions.most_common())
embedded=json.dumps([{'id':r['id'],'form':r['form'],'village':r['village']} for r in records],ensure_ascii=False).replace('<','\\u003c')
livelihood_cards=''.join('<section id="life-'+k+'"><h4>'+title+'</h4>'+cards([n for n in notes if n['slug'] in slugs])+'</section>' for k,(title,slugs) in life_topics.items())
body=f'''<div class="breadcrumbs"><a href="/enshu/">遠州弁の学び舎</a> ／ 研究ノート</div><header class="research-hero"><div><p class="eyebrow">ENSHU / RESEARCH NOTES</p><h1>ことばの仕組みを、<br><em>根拠から解き明かす。</em></h1><p class="seminar-deck">遠州弁研究ノート ── 文法・語史・暮らしから、音の仕組みまで</p><p>一語の意味から、説明できる知識へ。文の組立てと意味、音声、会話の使い分けから、親族・農林漁業・商いの言葉まで、独立した問いと資料で深く読みます。原資料、先行研究、編集部の分析をたどれる研究解説です。</p><nav><a href="#notebooks">{len(notes)}本の研究ノート</a><a href="#lab">資料を集計する</a><a href="#sources">文献と確認範囲</a></nav></div><figure><img src="/assets/img/kotoba/gunshi-744.webp" width="1200" height="853" alt="1921年刊『静岡県磐田郡誌』方言欄の原画像、1250・1251頁" loading="eager"><figcaption>議論は、この一行から。<br>『静岡県磐田郡誌』1250–1251頁<br><a href="https://dl.ndl.go.jp/pid/965680/1/744">国立国会図書館の原画像 ↗</a></figcaption></figure></header><div class="research-principles"><span><b>01</b> 原記録へ戻れる</span><span><b>02</b> 解釈を検討できる</span><span><b>03</b> 集計を再現できる</span></div><section id="notebooks"><div class="seminar-heading"><p class="eyebrow">{len(notes)} RESEARCH NOTES</p><h2>一つの問いを、深く読む。</h2><p>各ノートは〈問い・資料・分析・別の読み・検証方法〉で構成。入門8講の先へ進む研究解説です。</p></div><nav class="research-topics" aria-label="研究テーマを選ぶ"><a href="#kinship">親族・人の呼び方 <b>{kin_count}本</b></a><a href="#livelihood">仕事・生業 <b>{life_count}本</b></a><a href="#honorific">敬語・待遇表現 <b>4本</b></a><a href="#festival">祭り・年中行事 <b>4本</b></a><a href="#language">文の組立てと意味 <b>{language_count}本</b></a><a href="#grammar">否定・条件・可能・勧誘 <b>4本</b></a><a href="#word-history">語源・語史 <b>3本</b></a><a href="#folk-life">暮らしと民俗 <b>5本</b></a><a href="#variation">地域・世代・意味の変化 <b>{variation_count}本</b></a><a href="#sound">発音・アクセント <b>{sound_count}本</b></a><a href="#foundations">文法・民俗・資料 <b>6本</b></a></nav><div class="research-note-group" id="kinship"><h3>親族の関係と、呼び方の仕組みを読む <small>{kin_count}本</small></h3>{cards([n for n in notes if n.get("group")=="kinship"])}</div><div class="research-note-group" id="livelihood"><h3>地域の仕事から、ことばの使われ方を読む <small>{life_count}本</small></h3><nav class="research-topics" aria-label="仕事の分野を選ぶ"><a href="#life-water">漁と水辺</a><a href="#life-forest">山と運搬</a><a href="#life-farm">農・茶・材料</a><a href="#life-trade">商いと技術</a></nav>{livelihood_cards}</div><div class="research-note-group" id="honorific"><h3>誰について、誰に話すか。待遇表現を読む <small>追加4本</small></h3>{cards([n for n in notes if n.get('group')=='honorific'])}</div><div class="research-note-group" id="festival"><h3>祭りの名前・役割・道具・声を読み解く <small>追加4本</small></h3>{cards([n for n in notes if n.get('group')=='festival'])}</div><div class="research-note-group" id="language"><h3>音から文へ、場面から意味へ <small>{language_count}本</small></h3>{cards([n for n in notes if n.get("group")=="language"])}</div><div class="research-note-group" id="grammar"><h3>否定・条件・可能・勧誘を、文脈から読む <small>追加4本</small></h3>{cards([n for n in notes if n.get('group')=='grammar'])}</div><div class="research-note-group" id="word-history"><h3>言葉の由来を、証拠の強さから考える <small>追加3本</small></h3>{cards([n for n in notes if n.get('group')=='word-history'])}</div><div class="research-note-group" id="folk-life"><h3>食事・子育て・生業・住まい・民具を読む <small>追加5本</small></h3>{cards([n for n in notes if n.get('group')=='folk-life'])}</div><div class="research-note-group" id="variation"><h3>地域・世代と会話から、ことばの変化を読む <small>{variation_count}本</small></h3>{cards([n for n in notes if n.get('group')=='variation'])}</div><div class="research-note-group" id="sound"><h3>音の仕組みを、記述と図解から読む <small>{sound_count}本</small></h3>{cards([n for n in notes if n.get('group')=='sound'])}</div><div class="research-note-group" id="foundations"><h3>文法・民俗・資料を精読する <small>基礎の6本</small></h3>{cards(notes[:6])}</div></section><section id="lab" class="research-lab"><p class="eyebrow">OPEN NOTEBOOK / 集計条件を動かす</p><h2>資料の集計室</h2><p>対象は郡誌の選録380行。記録数と原表記の種類数を比較できます。<strong>棒の長さは資料中の行数で、人口・発話頻度・方言の豊かさを表すものではありません。</strong></p><div class="research-controls" hidden id="lab-controls"><label>集計の範囲<select id="lab-scope"><option value="all">選録380行のすべて</option><option value="repeated">同じ原表記が複数ある記録</option><option value="outside">上位3地域名を除いた記録</option></select></label><label>記録地の原ラベル<select id="lab-region"><option value="">すべての記録地</option>{''.join(f'<option>{E(v)}</option>' for v in regions)}</select></label><button type="button" id="lab-reset">条件を戻す</button></div><p class="research-lab-status" id="lab-status" role="status" aria-live="polite">380記録 ／ 376原表記 ／ 13地域名ラベル</p><p class="research-small" id="lab-rule">原表記は完全一致で数えます。旧仮名・大きな仮名を統合しません。</p><p class="research-table-hint">表は横にスクロールできます →</p><div class="seminar-table" tabindex="0" role="region" aria-label="地域名別の集計表"><table class="research-counts"><caption>条件内の記録数と原表記数（各ラベル内で重複除去）</caption><thead><tr><th scope="col">記録地の原ラベル</th><th scope="col">記録数</th><th scope="col">原表記数</th></tr></thead><tbody id="lab-table">{lab_rows}</tbody></table></div><noscript><p>JavaScriptが無効でも全件の集計表と研究ノート、ダウンロード資料を読めます。条件の切替にはJavaScriptを使います。</p></noscript><p><a href="{BASE}sampling/">この数字から言えること・言えないこと →</a></p><details class="research-downloads"><summary>元データ・再現手順を開く</summary><p>CSVの380行は既存選録の書き出しです。新発見の380語という意味ではありません。ID、原表記、意味の整理、記録地、頁、原注、原画像リンクを保持しています。</p><ul><li><a href="/downloads/enshu-research/records.csv" download>郡誌選録380記録（CSV・UTF-8）</a></li><li><a href="/downloads/enshu-research/reproduce.py" download>集計を再現するPythonスクリプト</a></li><li><a href="/downloads/enshu-research/README.txt" download>集計方法・列の説明・引用例</a></li><li><a href="/downloads/enshu-research/manifest.json" download>資料版・件数・ファイル照合値（JSON）</a></li><li><a href="/downloads/enshu-research/fieldwork-template.csv" download>生活語彙の調査記録ひな形（空のCSV）</a></li></ul><p>CSVとスクリプトを同じフォルダーに置き、<code>python reproduce.py</code>で集計できます。標準ライブラリだけを使い、外部送信や追加取得は行いません。</p></details></section><section class="research-editorial" id="editorial"><p class="eyebrow">EDITORIAL METHOD</p><h2>専門性を、確かめられる形に。</h2><dl><div><dt>資料の観察</dt><dd>表は原記録から生成し、記録ID・設問・頁に戻れるようにします。資料にない発音や使用率を補いません。</dd></div><div><dt>研究と分析の区別</dt><dd>論文の対象地・話者条件・確認した頁を示します。編集部の分析候補と、研究者が述べた結論を区別します。</dd></div><div><dt>更新と訂正</dt><dd>データの版と照合値を残します。訂正は対象の記録・頁・理由を確認し、原記録と編集上の判断を追える形で扱います。</dd></div></dl><p class="research-byline">編集：磐田物語 編集部 ／ 資料の照合・補足：2026年11月13日。公開資料に基づく研究解説です。新たな現地調査・録音調査を実施した記事、研究者の監修・学術査読を受けた論文ではありません。</p></section>{bibliography(SOURCES)}<section class="seminar-next"><h2>学ぶ・調べる・考えるを、行き来する。</h2>{nav}</section><script type="application/json" id="research-records">{embedded}</script>'''
coverage_html,coverage_json=build_coverage(notes,supplements,table,cite)
language_html,language_json=language_coverage(notes,table)
coverage_html+=language_html
new_source_html,new_source_json=new_source_coverage(notes,table)
coverage_html+=new_source_html
coverage_ledger=json.loads(coverage_json)
coverage_ledger["language_review"]={"scope":"FPJD磐田市1地点の全211設問と談話・多義性の公開研究を、既掲載の問いと照合。原著未読・音声未収集の課題は別に保持。","details":"/downloads/enshu-research/language-evidence.json"}
coverage_json=(json.dumps(coverage_ledger,ensure_ascii=False,indent=2)+"\n").encode("utf8")
body=body.replace('<section id="lab"',coverage_html+'<section id="lab"',1).replace('<a href="#lab">資料を集計する</a>','<a href="#coverage">調査した範囲と未解決点</a><a href="#lab">資料を集計する</a>',1)
outputs={R/'enshu/research/index.html':shell(f'遠州弁研究ノート{len(notes)}本｜文法・語源・民俗・生業・発音とアクセント',f'遠州弁を{len(notes)}の問いから深く読む研究解説。否定・条件・可能・勧誘、みるいの語史、食事・子育て・農業・住まい・民具、地域差と音声。原資料・調査条件・比較表・小演習と資料の集計室。',BASE,body,script=True,published=DATE,modified='2026-11-13'),R/'downloads/enshu-research/topic-evidence.json':coverage_json,R/'downloads/enshu-research/language-evidence.json':language_json}
body=body.replace('<a href="#kinship">親族・人の呼び方',f'<a href="#new-sources">新資料から深く読む <b>{new_source_count}本</b></a><a href="#kinship">親族・人の呼び方',1)
body=body.replace('<div class="research-note-group" id="kinship">',f'<div class="research-note-group" id="new-sources"><h3>新しい研究と、近世・地域の原資料を読む <small>{new_source_count}本</small></h3><p>2026年の文法・音声技術研究、4月公開の歴史方言DB、磐田の地域資料を、既掲載の問いと照合しました。</p>{cards([n for n in notes if n.get("group")=="new-sources"])}</div><div class="research-note-group" id="kinship">',1)
outputs[R/'enshu/research/index.html']=shell(f'遠州弁研究ノート{len(notes)}本｜文法・語源・民俗・生業・発音とアクセント',f'遠州弁を{len(notes)}の問いから深く読む研究解説。近世語彙、ケの文法、鳥の聞きなし、民俗信仰、伝説、音声とAIまで。原資料・調査条件・比較表・小演習と写真を掲載。',BASE,body,script=True,published=DATE,modified='2026-11-13')
outputs[R/'downloads/enshu-research/new-source-evidence.json']=new_source_json
regional_html,regional_json=regional_coverage(notes,table)
body=body.replace('<section id="lab"',regional_html+'<section id="lab"',1)
body=body.replace('<a href="#new-sources">',f'<a href="#regional">地域の原資料を読む <b>{sum(n.get("group")=="regional" for n in notes)}本</b></a><a href="#new-sources">',1)
body=body.replace('<div class="research-note-group" id="new-sources">','<div class="research-note-group" id="regional"><h3>地域の記録から、会話・暮らし・研究法を読む</h3><p>町史・文化誌・郷土教材の原画像と、新たに取得した論文本文を照合。重なる証拠は既存ノートへ補足しました。</p>'+cards([n for n in notes if n.get('group')=='regional'])+'</div><div class="research-note-group" id="new-sources">',1)
outputs[R/'enshu/research/index.html']=shell(f'遠州弁研究ノート{len(notes)}本｜文法・語源・民俗・生業・発音とアクセント',f'遠州弁を{len(notes)}の問いから深く読む。文法・音声・語史・民俗から地域資料の読み方まで、出典・比較表・小演習・磐田の写真を掲載。',BASE,body,script=True,published=DATE,modified='2026-11-13')
outputs[R/'downloads/enshu-research/regional-evidence.json']=regional_json
systematic_html,systematic_json=systematic_coverage(notes,table)
body=body.replace('<section id="lab"',systematic_html+'<section id="lab"',1)
body=body.replace('<a href="#regional">','<a href="#systematic">原論文から深く読む <b>'+str(sum(n.get('group')=='systematic' for n in notes))+'本</b></a><a href="#regional">',1)
body=body.replace('<div class="research-note-group" id="regional">','<div class="research-note-group" id="systematic"><h3>原論文から、仕組み・意味・継承を深める</h3><p>使役・疑問・取り立て否定、アクセントの体系、語義と水辺、文法変化、作品表現、調査と継承。新設と既存への統合を、資料ごとの問いから選びました。</p>'+cards([n for n in notes if n.get('group')=='systematic'])+'</div><div class="research-note-group" id="regional">',1)
body=body.replace('資料の照合・補足：2026年11月13日','資料の照合・補足：2026年11月14日')
outputs[R/'enshu/research/index.html']=shell(f'遠州弁研究ノート{len(notes)}本｜文法・語源・民俗・生業・発音とアクセント',f'遠州弁を{len(notes)}の問いから深く読む。原論文と地域の原資料、語義・文法・発音・民俗・研究法。出典・比較表・小演習・磐田の写真を掲載。',BASE,body,script=True,published=DATE,modified='2026-11-14')
outputs[R/'downloads/enshu-research/systematic-evidence.json']=systematic_json


for i,n in enumerate(notes):
    headings=re.findall(r'<section id="([^"]+)"><h2>([^<]+)</h2>',n['body'])
    toc='<nav class="research-toc" aria-label="この記事の目次"><strong>このノートの道筋</strong>'+''.join(f'<a href="#{key}">{E(title)}</a>' for key,title in headings)+'<a href="#sources">出典・確認範囲</a></nav>'
    related=[notes[(i+1)%len(notes)],notes[(i+2)%len(notes)]]
    article=f'''<div class="breadcrumbs"><a href="/enshu/">学び舎</a> ／ <a href="{BASE}">遠州弁研究ノート</a> ／ {i+1:02}</div><header class="research-note-head"><p class="eyebrow">RESEARCH NOTE {i+1:02} / {E(n['field'])}</p><h1>{E(n['title'])}</h1><p class="seminar-deck">{E(n['deck'])}</p><p class="research-byline">磐田物語 編集部 ／ {n['published'].replace('-', '年', 1).replace('-', '月', 1)}日{' ／ 補足：2026年11月13日' if n.get('updated') else ''} ／ 公開資料に基づく研究解説</p><div class="research-finding"><strong>このノートで確かめること</strong><p>{E(n['finding'])}</p></div></header><div class="research-note-layout"><aside>{toc}</aside><div class="research-prose">{n['body']}{bibliography(n['sources'])}<p class="research-byline">資料の記録、先行研究の見解、編集部の分析・調査案を区別しています。研究者監修・学術査読を受けた論文や、編集部による現地調査報告ではありません。<a href="{BASE}#editorial">編集方針</a></p></div></div><section class="seminar-next"><h2>次の問いへ進む</h2>{cards(related)}{nav}</section>'''
    if n['slug'] in systematic_supplements:article=article.replace('補足：2026年11月13日','補足：2026年11月14日')
    from enshu_research_topics import note_category_return
    article=note_category_return(n)+article
    outputs[R/f'enshu/research/{n["slug"]}/index.html']=shell(n['title']+'｜遠州弁研究ノート',n['deck']+' '+n['finding'],BASE+n['slug']+'/',article,article=True,published=n['published'],modified=n.get('updated',n['published']))

# A standard-library-only replay accompanies the frozen exported rows.
replay='''"""Reproduce counts for Iwata Monogatari's 1921 Gunshi SELECTED records."""
from pathlib import Path
import csv, json, hashlib
from collections import Counter
folder=Path(__file__).resolve().parent
csv_path=folder/'records.csv'
with csv_path.open(encoding='utf-8-sig',newline='') as stream:
    rows=list(csv.DictReader(stream))
forms=Counter(r['form'] for r in rows)
regions=Counter(r['village'] for r in rows)
repeated={f:n for f,n in forms.items() if n>1}
result={'records':len(rows),'original_forms':len(forms),'region_labels':len(regions),
        'repeated_forms':repeated,'repeated_rows':sum(repeated.values()),
        'top3_records':sum(n for _,n in regions.most_common(3)),
        'regions':dict(regions.most_common()),'csv_sha256':hashlib.sha256(csv_path.read_bytes()).hexdigest()}
manifest_path=folder/'manifest.json'
if manifest_path.exists():
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert result['csv_sha256']==manifest['csv_sha256'],'CSV checksum mismatch'
    for key,value in manifest['expected'].items():
        assert result[key]==value,(key,result[key],value)
print(json.dumps(result,ensure_ascii=False,indent=2))
'''
stream=io.StringIO(newline='')
columns=['id','form','gloss','village','page','frame','note','source_url']
writer=csv.DictWriter(stream,columns,lineterminator='\n');writer.writeheader()
for r in records:writer.writerow({**r,'source_url':f'https://dl.ndl.go.jp/pid/965680/1/{r["frame"]}'})
csv_bytes=stream.getvalue().encode('utf-8-sig')
manifest={'version':DATE,'source':corpus['source'],'policy':corpus['policy'],'source_json_sha256':hashlib.sha256(corpus_file.read_text(encoding='utf8').encode('utf8')).hexdigest(),'source_json_hash_policy':'UTF-8 with line endings normalized to LF','csv_sha256':hashlib.sha256(csv_bytes).hexdigest(),'transform':'One CSV row per existing record. Exact form/village strings; no spelling normalization. source_url constructed from NDL pid and frame. Repeated forms classified before other filters.','expected':{'records':380,'original_forms':376,'region_labels':13,'repeated_rows':8,'top3_records':315},'generated_by':'tools/build_enshu_research.py','citation':'磐田物語「遠州弁研究ノート・郡誌選録集計」2026年11月12日版。原資料：静岡県磐田郡教育会編『静岡県磐田郡誌』1921年、1242–1254頁。'}
readme='''遠州弁研究ノート：郡誌選録の再現資料 / 2026-11-12
https://iwata-monogatari.net/enshu/research/

対象：1921年刊『静岡県磐田郡誌』1242–1254頁からの既存選録380行。
全文翻刻ではありません。全住民・全語彙の調査や発話頻度のデータではありません。
formは原表記、glossは原資料の対応語と原注を読みやすく整理した意味です。
villageは記録地の原ラベル。「村辺」や袋井町・袋井村を統合していません。
idは固定記録ID、pageは印刷頁、frameはNDL画像のコマ、noteは原注の整理、source_urlは原画像です。

再現：Python 3で python reproduce.py を実行。CSVとスクリプトは同じフォルダーへ保存。
manifest.jsonを同じ場所に置くと、CSVのSHA-256と期待件数も照合します。
標準ライブラリのみ使用。ファイルの更新や外部通信を行いません。
原表記の完全一致で数え、読み・音・独立した語の総数とは扱いません。
同形複数行の条件は全380行に適用してから、他の絞り込みを行います。
上位3ラベル除外は感度確認の例であり、標本の偏りを補正する処理ではありません。

fieldwork-template.csvは編集部作成の空の様式です。実際の聞き取り資料ではありません。
管理IDで情報を対応付け、本人の同意なく氏名・細かな住所・録音を公開しないでください。

引用例：磐田物語「遠州弁研究ノート・郡誌選録集計」2026年11月12日版。
原資料：静岡県磐田郡教育会編『静岡県磐田郡誌』1921年、1242–1254頁。
原画像：国立国会図書館デジタルコレクション https://dl.ndl.go.jp/pid/965680
研究論文のPDFや図版はこの配布に含みません。
'''
fields=['管理ID','資料種別（実物・実見・聞き取り・文献）','呼称の原形','表記を整えた場合の別欄','対象物・行為','地域（公開範囲）','対象の年代','記録日','情報提供者ID','実見・伝聞・推測の区別','使い方・手順','素材・形・寸法','関連する物・人・季節','原資料・頁・音声時刻','公開同意の範囲','未確認事項']
fieldstream=io.StringIO(newline='');csv.writer(fieldstream,lineterminator='\n').writerow(fields)
downloads={'records.csv':csv_bytes,'reproduce.py':replay.encode('utf8'),'README.txt':readme.encode('utf8'),'manifest.json':(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf8'),'fieldwork-template.csv':fieldstream.getvalue().encode('utf-8-sig')}
for name,data in downloads.items():outputs[R/'downloads/enshu-research'/name]=data
outputs[R/'data/enshu-research-index.json']=(json.dumps({'version':DATE,'notes':[{k:n[k] for k in ['slug','field','title','deck','finding']} for n in notes]},ensure_ascii=False,indent=2)+'\n').encode('utf8')
for path,value in outputs.items():
    if path.suffix=='.html' and path.parent.parent==R/'enshu/research' or path==R/'enshu/research/index.html':
        from enshu_navigation import middle_header
        value=middle_header(value,BASE)
    if path.suffix=='.html':value=apply_photos(value,'/'+path.parent.relative_to(R).as_posix()+'/')
    if path==R/'enshu/research/index.html':
        from enshu_research_topics import split_research_topics
        split_research_topics(R,value,check='--check' in sys.argv)
        continue
    data=value.encode('utf8') if isinstance(value,str) else value
    if '--check' in sys.argv:
        assert path.exists() and path.read_bytes()==data,f'Out of date: {path}'
    else:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
print(f'Enshu research: {len(notes)} notes; {len(SOURCES)} cited sources; 380 replayable records; {len(outputs)} outputs')
