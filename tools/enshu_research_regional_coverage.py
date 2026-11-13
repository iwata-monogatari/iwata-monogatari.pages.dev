"""Expose the reviewed source scope and evidence gaps, not an article quota."""
from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1]
E=lambda s:html.escape(str(s),quote=True)
def regional_coverage(notes,table):
 j=json.loads((R/'data/enshu-regional-review.json').read_text('utf8'))
 slugs={n['slug'] for n in notes}
 assert all(set(x['notes'])<=slugs for x in j['candidates'])
 rows=[[E(x['topic']),E(x['source_scope']),E(x['decision'])+'<small>'+E(x['reason'])+'</small>',' ／ '.join('<a href="/enshu/research/'+E(s)+'/">'+E(next(n['title'] for n in notes if n['slug']==s))+'</a>' for s in x['notes']) or '本文・音声等の取得後に再検討'] for x in j['candidates']]
 body='<section id="regional-review" class="research-editorial"><p class="eyebrow">REGIONAL SOURCES / 原画像と全文</p><h2>今回の地域資料と未取得本文を、どう扱ったか</h2><p>町史の章・文化誌の関連箇所を既掲載の問いと照合しました。独立した論点は新設、重なる証拠は元のノートへ補足。未取得資料は確認済みにせず、記事数を区切りや調査終了の証明にしません。</p><p>FIT2024の「いいにする」は、公式ダウンロードから全2頁を今回取得。静岡大学・筑波大学の2論文は実ブラウザでもメンテナンス中でした。抄録・全文・原画像の確認状態を区別しています。</p>'+table(['検討した問い','資料と確認範囲','処理と理由','掲載先・残る証拠'],rows,'地域資料・論文本文の照合と採否')+'<p><a href="/downloads/enshu-research/regional-evidence.json">資料・採否の台帳を読む（JSON）</a></p><p class="research-small">確認範囲はこの台帳に示す資料です。未読の方言集や未取得の録音まで調べ終えたという意味ではありません。新たな原著や音声が得られた時に、独立性と根拠を再検討します。</p></section>'
 return body,json.dumps(j,ensure_ascii=False,indent=2)+'\n'
