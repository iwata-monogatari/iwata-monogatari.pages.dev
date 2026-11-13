from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1];E=lambda s:html.escape(str(s),quote=True)
def systematic_coverage(notes,table):
 j=json.loads((R/'data/enshu-systematic-review.json').read_text(encoding='utf8'));by={n['slug']:n for n in notes}
 def links(slugs):
  assert set(slugs)<=set(by),slugs
  return ' ／ '.join('<a href="/enshu/research/'+s+'/">'+E(by[s]['title'])+'</a>' for s in slugs)
 rows=[[E(x['topic']),E(x['decision']),E(x['reason']),links(x['notes'])] for x in j['candidates']]
 source_rows=[[E(x['title']),E(x['confirmed_scope']),links(x['notes'])] for x in j['sources']]
 gaps=[[E(x['topic']),E(x['status']),E(x['evidence']),E(x['condition'])] for x in j['gaps']]
 body='<section class="research-editorial" id="systematic-review"><p class="eyebrow">PRIMARY TEXTS / 原論文と地域資料の照合</p><h2>原著で確かめたことと、残る問い。</h2><p>2026年11月13〜14日、国語研の地域名等13検索の結果を重複除去した237件と、関連する原論文・著者公開版・地域資料を照合しました。作品名の「浜松」、滋賀の「湖西」等を除外し、書誌・抄録・本文の確認を分けています。237件すべての全文を読んだ、全遠州研究を調べ終えたという意味ではありません。</p><p>使役・疑問・取り立て、語義と水辺、アクセントの体系、文法変化、調査法、作品と継承を深めました。同じ問いの証拠は既存ノートへ統合し、類似記事への分割を避けています。下の台帳は追加本数ではなく、資料ごとの処理と未確認事項を追うためのものです。</p><details class="research-downloads"><summary>問いごとの採否と掲載先を開く</summary>'+table(['問い','処理','理由','掲載先'],rows,'原著の知見と既掲載の問いの対応')+'</details><details class="research-downloads"><summary>資料ごとの確認範囲を開く</summary>'+table(['資料','本文・原画像・対象の条件','掲載先'],source_rows,'原資料の確認範囲')+'</details><details class="research-downloads"><summary>本文・録音等が未確認の課題を開く</summary>'+table(['課題','現在の状態','確認したこと','解決に必要な証拠'],gaps,'未取得の原著と現地資料の課題')+'</details><p><a href="/downloads/enshu-research/systematic-evidence.json">237件の書誌・採否・掲載先・未確認事項を読む（JSON）</a></p><p class="research-small">佐野・菅野2026は大学の停止告知と著者の公開業績・資料欄まで再確認しましたが、別の全文は得られていません。抄録を全文へ読み替えず、取得した本文で説明できる範囲を公開します。今後の原著・音声による再検討の条件も保持します。</p></section>'
 return body,json.dumps(j,ensure_ascii=False,indent=2)+'\n'
