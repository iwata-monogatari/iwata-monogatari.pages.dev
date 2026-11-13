import json,html
from pathlib import Path
def new_source_coverage(notes,table):
 data=json.loads((Path(__file__).resolve().parents[1]/'data/enshu-new-source-review.json').read_text(encoding='utf8'))
 slugs={n['slug'] for n in notes};assert all(set(r['notes'])<=slugs for r in data['candidates'])
 assert len(data['historical_records'])==60 and all(r['note'] in slugs for r in data['historical_records'])
 e=html.escape
 out='<section id="new-source-review" class="research-editorial"><p class="eyebrow">NEW PAPERS / PRIMARY RECORDS</p><h2>新しい資料を、既掲載の問いと照合する。</h2><p>2026年の学会発表・公開論文、4月公開の『物類称呼』DB、磐田の改訂地域計画などを確認。独立した問いは新設し、同じ問いの追加証拠は既存ノートへ補足しました。本数を区切りの基準にせず、調べた資料ごとに扱いと根拠を残しています。</p>'
 out+=table(['調べた資料・問い','照合後の扱い','根拠・残る確認'],[[e(r['label']),e(r['disposition'])+''.join('<br><a href="/enshu/research/'+e(s)+'/">'+e(next(n['title'] for n in notes if n['slug']==s))+'</a>' for s in r['notes']),e(r['reason'])] for r in data['candidates']],'新しい資料候補の採用・補足・見送りと確認範囲')
 out+='<details class="research-downloads"><summary>歴史資料60行の掲載先と、未確認の本文を確認する</summary><p>原地名または整理地名に遠江・遠州を含む60行を、全5巻の所在へ照合。注記だけに遠江がある他地域2行は除きました。60行は60人・60の新語を意味しません。語形・場所・条件・所在と掲載先を記録しています。</p><p><a href="/downloads/enshu-research/new-source-evidence.json" download>資料候補・60行の採否・出典の所在（JSON）</a></p><p>静岡大学・筑波大学の一部本文はメンテナンス中。FIT2024の本文PDFは取得エラーのため、確認できた公式抄録と未読の本文を区別しています。未読資料や未収集の音声を確認済みにしたり、将来の追加研究が不可能としたりはしていません。</p></details></section>'
 return out,(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf8')
