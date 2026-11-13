"""Public evidence/candidate ledger: distinguish addressed questions and missing evidence."""
import json,html
E=lambda t:html.escape(str(t),quote=True)

GAPS=[
 {'topic':'地域・世代ごとの親族呼称の使用率','state':'統計を示せない','reason':'郡誌と文献採録は、同条件で地域・世代を比較した代表標本ではない。現代の地域別・世代別の標本と設問が必要。','needed':'比較可能な調査設計・話者条件・全回答'},
 {'topic':'親族呼称や人名のアクセント・会話の間','state':'音声資料が必要','reason':'仮名の語彙記録・編集された取材記事だけから、アクセントや発話の長さ、間を復元できない。','needed':'対象地域・話者・場面を伴う利用可能な音声と照合'},
 {'topic':'各世帯の屋号の分布・現在の呼び方','state':'全体像を示せない','reason':'公開資料の個別例と他地方の研究はあるが、遠州の各集落の全世帯を同条件で確認した名簿ではない。','needed':'当事者の説明、時点、同意と公開範囲を伴う現地資料'},
 {'topic':'機械音のある職場の指示・身振り・短縮語','state':'実際の会話が必要','reason':'産業の存在や機械の展示だけで、作業中の言葉や発音がどう変わるかを実証できない。','needed':'作業と発話の対応、記録・利用条件'},
 {'topic':'語形の類似からの確定語源・伝播経路','state':'未確定のまま保持','reason':'似た形や原注の推測を確定へ変えない。作物・技術・材料が動くことと言葉が移ることを分ける。','needed':'年代の分かる語の実例と物・人の移動資料'},
 {'topic':'生業の違いが文法や性格を生むという因果','state':'因果を断定しない','reason':'産業史や語彙の存在だけでは、職業が文法・話し方を決める証拠にならない。','needed':'比較対象と交絡条件を含む言語資料'},
]
BOOKS=[
 ('磐田地方の方言集','書名の案内を確認。今回、原著本文は直接閲覧していない。'),
 ('ふくで方言集','図書館の資料案内を確認。本文の語義を確認した出典として使わない。'),
 ('おらん生まれた長野ん方言','資料案内を確認。今回本文に基づく新たな断定はしない。'),
 ('竜洋町の方言 訛集','資料案内を確認。書名の確認と本文の確認を区別する。'),
 ('遠州方言集・水窪の語彙調査','国語研1979の採録を介して該当箇所を確認。採録元原著の直接確認とは区別する。'),
 ('豊田町の方言','県立図書館の書誌一覧で確認。今回、原著本文を直接閲覧していない。'),
]

COMPARISONS=[
 {'topic':'問屋場の役割と職名','source':'https://adeac.jp/hamamatsu-city/texthtml/d100020/mp010020-100020/ht003260','disposition':'独立ページにはしない','reason':'市史の本文を確認したが、制度ごとの役名を列挙するだけでは、既掲載の渡船組織・職名分類の問いと十分に区別できない。別制度の呼称を一つの職場の会話へ合成しない。'},
 {'topic':'市史の阿多古紙の短い記述','source':'https://adeac.jp/hamamatsu-city/texthtml/d100020/mp010020-100020/ht004360','disposition':'同じ題材の薄い別記事を作らない','reason':'市史の紙漉きの記述と職人の説明を比較し、工程・発話を直接検討できる取材記事を主資料にした。季節的な生産の紹介だけを別の研究ノートへ分割しない。'},
 {'topic':'楮栽培から「かず」の語源を説明できるか','source':'https://adeac.jp/hamamatsu-city/texthtml/d100020/mp010020-100020/ht005180','disposition':'確定語源の記事は作らない','reason':'市史の栽培史の本文は確認したが、語形の成立・音変化・伝播の年代を実証する資料ではない。作物の歴史だけを語源の証拠に変えない。'},
]

def build_coverage(notes,supplements,table,cite):
    new=[n for n in notes if n.get('published')=='2026-11-13']
    rows=[{'topic':n['title'],'disposition':'独立した問いとして掲載','slug':n['slug'],'reason':n['deck'],'sources':n['sources']} for n in new]
    rows += [{'topic':heading,'disposition':'重複する既存ノートへ補足','slug':slug,'reason':'同じ資料上の問いを細分化して新しいページ数を増やさず、既存の論点の中で比較。'} for slug,headings in supplements.items() for heading in headings]
    ledger={'version':'2026-11-13','scope':'親族呼称・人の呼び方・地域の仕事と生業。郡誌選録、国語研の親族語研究、公的な地域史・文化財・産業・技術資料を照合。世界中の全資料や将来の新資料を調べ尽くしたという意味ではない。','method':'先に本数を決めず、独立した問いは新設、既存の問いに重なる証拠は補足、裏付けを欠く断定は保留する。','candidates':rows,'evidence_gaps':GAPS,'books':[{'title':t,'status':s} for t,s in BOOKS],'reviewed_collections':[{'name':'磐田郡誌選録','records':380,'limit':'全文翻刻ではなく、過去に原画像照合した選録。'}, {'name':'FPJD磐田市1地点','records':287,'questions':211,'limit':'親族呼称全体や職業集団を一様に調べたデータではない。既存の敬語・文法ノートとの重複を照合。'}]}
    ledger['source_comparisons']=COMPARISONS
    parts=['<section id="coverage" class="research-editorial"><p class="eyebrow">EVIDENCE MAP</p><h2>どこまで資料で確かめられるか。</h2><p>親族・呼称・生業の資料を、既存の論点と照合しています。新設した問い、既存ノートへ加えた証拠、追加の一次資料を要する未解決点を分けました。掲載件数を、調査の完全終了の証拠とはしません。</p>']
    parts.append('<details class="research-downloads"><summary>資料と論点の対応を見る</summary>')
    parts.append(table(['扱い','問い・補足した内容','読む場所'],[[E(x['disposition']),E(x['topic']),f'<a href="/enshu/research/{x["slug"]}/">該当ノートへ →</a>'] for x in rows],'資料から採用した問いと既存ノートへの補足'))
    parts.append('</details><details class="research-downloads"><summary>比較して、独立した記事にしなかった資料</summary>')
    parts.append(table(['比較した題材','扱いと理由','確認した本文'],[[E(x['topic']),E(x['reason']),f'<a href="{E(x["source"])}">市史の本文へ ↗</a>'] for x in COMPARISONS],'独立記事にしなかった資料と判断の理由'))
    parts.append('</details><h3>追加資料を必要とする問い</h3>')
    parts.append(table(['問い','現時点での位置付け','必要な証拠'],[[E(x['topic']),E(x['reason']),E(x['needed'])] for x in GAPS],'掲載済みの解説からは断定できない事項'))
    parts.append('<details class="research-downloads"><summary>書名の確認と、本文の確認を分ける</summary><p>図書館の資料案内'+cite('iwata_dialect_guide','磐田市立図書館・磐田の方言')+'と県立図書館の公開書誌一覧を参照しました。紹介された本の書名が分かることは、その本文を読んだことと同じではありません。</p><ul>')
    parts.extend('<li><strong>'+E(t)+'</strong>：'+E(s)+'</li>' for t,s in BOOKS)
    parts.append('</ul><p><a href="https://www.tosyokan.pref.shizuoka.jp/assets/d9194fda6587cd83154b03ecae68f63b_1.pdf">県立中央図書館の公開書誌一覧へ ↗</a></p></details><p><a href="/downloads/enshu-research/topic-evidence.json" download>論点・資料条件・未解決点の対応（JSON）</a></p></section>')
    return ''.join(parts),(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode('utf8')
