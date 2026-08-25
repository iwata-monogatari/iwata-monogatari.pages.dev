from __future__ import annotations

import html
import json
import re
from pathlib import Path

from build_iwata_second_volume import ARTICLES


ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-25"
START = "<!-- iwata-second-volume-l3:start -->"
END = "<!-- iwata-second-volume-l3:end -->"


DATA = {
    "c138": {
        "fact": "国立公文書館は、明治21年（1888年）4月25日の市制・町村制公布を、本格的な地方自治制度の創設として位置づける。さらに1946年の町村制改正を審議した帝国議会記録は、女性を含む選挙権・被選挙権の拡張を政府が説明した一次資料である。したがって、磐田の初期議会と戦後議会を同じ『住民代表』として比較するには、資格要件の断絶を明示しなければならない。",
        "records": "選挙人名簿、町村税賦課台帳、候補者届、投票録、町村会議事録",
        "unit": "総人口・成年人口・公民資格者・実際の投票者",
        "actors": "女性、無資産層、転入者、被救助者、立候補しなかった住民",
        "question": "底本の『1％』がどの年・区域・分母から算出されたか",
        "sources": [("https://www.archives.go.jp/exhibition/digital/henbou/contents/13.html", "国立公文書館「市制・町村制」"), ("https://teikokugikai-i.ndl.go.jp/simple/detail?minId=009003242X02819460903&spkNum=20", "国立国会図書館「地方制度改正の政府説明」")],
    },
    "c139": {
        "fact": "国立公文書館が公開する市制・町村制の御署名原本には、市町村の財産、市税、歳入出予算・決算が独立した章として置かれている。近代町村財政は、寄付を集めた事実だけでなく、財産の帰属、課税、議決、出納、監督という手続の束として成立した。この制度枠と磐田の決算書を照合することで、寄付を単なる美談にも行政の失敗にも還元せずに読める。",
        "records": "予算案、議決書、決算書、寄付採納簿、共有財産台帳、工事精算書",
        "unit": "予算額・決算額・寄付申込額・実収入額・世帯当たり負担",
        "actors": "寄付できない世帯、土地を共有した集落、会計担当者、事業の受益地域",
        "question": "学校・道路・救済の各寄付が任意だったか、割当を伴ったか",
        "sources": [("https://www.jacar.archives.go.jp/das/meta/A03020018600", "アジア歴史資料センター「市制及町村制」御署名原本")],
    },
    "c140": {
        "fact": "国立公文書館の開拓使文書解説は、北海道側の行政文書が土地、移住者、産業、交通など複数系列に分かれて残ることを示す。磐田側の移住証明や旅費割引だけでは到着後の定着を証明できず、北海道側の土地貸付、戸籍、学校、収穫・離農記録まで接続して初めて一世帯の移動史になる。送出政策と生活結果を別々に検証する必要がある。",
        "records": "移住証明、副申書、除籍簿、土地貸付簿、入植者名簿、現地学校記録",
        "unit": "申請戸数・出発人数・到着人数・土地貸付戸数・定着戸数",
        "actors": "同行しなかった家族、先発者、帰郷者、現地雇用者、入植地の先住者",
        "question": "中泉の申請者がどの入植地へ到達し、何年居住したか",
        "sources": [("https://www.archives.go.jp/about/report/pdf/tyousa03.pdf", "国立公文書館『開拓使文書』資料解説")],
    },
    "c141": {
        "fact": "国立公文書館の内務省地方行政関係文書には、市制町村制例規を含む明治期の制度資料がまとまっている。これらは役場が従うべき制度設計を示すが、磐田の組合役場で同じ書式がいつ運用されたかを直接示すものではない。法令、県の通達、役場の受付印、実際の簿冊という四段階を分けることで、制度公布日を地域実施日に置き換える誤りを避けられる。",
        "records": "県達受領簿、組合規約、分掌規程、職員辞令、受付発送簿、保存簿冊目録",
        "unit": "制度公布日・県通達日・役場受領日・実施開始日",
        "actors": "戸長、書記、収入役、組長、窓口へ出向いた住民",
        "question": "中泉町・梅原村などの共同処理がどの事務に限られたか",
        "sources": [("https://www.digital.archives.go.jp/fonds/2327218", "国立公文書館「内務省文書（地方行政関係）」")],
    },
    "c142": {
        "fact": "国立国会図書館は『戦後自治史 第1』を『隣組及び町内会、部落会等の廃止』に特化した公刊資料として所蔵する。一方、磐田市公式の現在の自治会一覧は、5支部・29地区・300自治会という現況を示す。戦時組織の廃止と現在の自治会数の間には約80年の再編があり、名称や回覧経路の連続だけで組織の法的・政治的連続を主張できない。",
        "records": "町内会部落会整備規則、役員名簿、廃止通達、戦後規約、総会議案書、区域図",
        "unit": "隣組・町内会・部落会・戦後自治会・現在の自治会",
        "actors": "未加入世帯、女性部、借家世帯、新住民、配給や連絡を担った班長",
        "question": "旧組織の資産・役員・区域のうち何が戦後組織へ継承されたか",
        "sources": [("https://ndlsearch.ndl.go.jp/books/R100000002-I000000861167", "国立国会図書館『戦後自治史 第1』"), ("https://www.city.iwata.shizuoka.jp/kurashi_tetsuzuki/chiiki_kouryuu/1011755/1001672.html", "磐田市「自治会概要・一覧」")],
    },
    "c143": {
        "fact": "国税庁は、明治29年（1896年）の税務管理局・税務署設置時に全国520署が発足し、国税事務の直轄化が進んだと説明する。ただし地租・所得税の一部では市町村の徴収義務が残り、国の税務署ができた瞬間に町村の徴税実務が消えたわけではない。磐田税務署と県財務事務所も所管税目と指揮系統を分けて記述する必要がある。",
        "records": "税務署沿革、県組織規則、町村徴税簿、納税組合規約、庁舎台帳、管轄告示",
        "unit": "国税・県税・町村税、賦課・徴収・滞納整理・相談",
        "actors": "零細納税者、徴税担当町村職員、納税組合役員、税務署職員",
        "question": "磐田の窓口移転が管轄変更・組織改編・庁舎事情のどれによるか",
        "sources": [("https://www.nta.go.jp/about/organization/ntc/sozei/tokubetsu/h24shiryoukan/00.htm", "国税庁「税務署の誕生」"), ("https://www.nta.go.jp/about/organization/ntc/sozei/tokubetsu/r06shiryoukan/01.htm", "国税庁「近代の税務行政と納税組合」")],
    },
    "c144": {
        "fact": "日本銀行『日本銀行百年史 第5巻』は、1949年のドッジ・ラインを単一為替相場、経済安定九原則、金融引締めと関連づけて章立てする。1930年代の匡救事業は失業・農村困窮への公共事業、1949年の緊縮は戦後インフレ安定化策であり、同じ『不景気対策』ではない。磐田の工事・失業・融資記録をそれぞれの政策時点へ結び直す必要がある。",
        "records": "匡救事業設計書、労務者名簿、町村決算、企業整理記録、金融機関日誌、失業統計",
        "unit": "事業費・延べ就労日数・実人数・企業倒産・求人減少・貸出残高",
        "actors": "日雇い、農家兼業者、女性内職者、中小企業、支援対象外の失業者",
        "question": "磐田のどの工事が正式な匡救事業で、どの雇用減が1949年政策と重なるか",
        "sources": [("https://www.boj.or.jp/about/outline/history/hyakunen/hyaku5.htm", "日本銀行『日本銀行百年史 第5巻』")],
    },
    "c145": {
        "fact": "国立国会図書館の『史料にみる日本の近代』は、1942年4月30日の翼賛選挙で推薦候補の当選が全体の8割以上だったことと、非推薦当選者も存在したことを示す。したがって『選挙がなかった』とも『通常の自由選挙だった』とも書けない。磐田の奉祝行事、推薦運動、投票、非推薦候補への対応を別の資料群として扱う。",
        "records": "候補者推薦資料、選挙公報、警察報告、投票録、奉祝行事日程、学校・町内会日誌",
        "unit": "推薦・非推薦、立候補・当選、参加者・動員対象、投票率・得票率",
        "actors": "非推薦候補の支持者、女性、若年者、棄権者、行事へ形式参加した住民",
        "question": "磐田地域の推薦運動を誰が担い、行政行事と選挙運動がどこで接続したか",
        "sources": [("https://www.ndl.go.jp/modern/cha4/description14.html", "国立国会図書館「翼賛政治会」")],
    },
    "c146": {
        "fact": "磐田市公式サイトは、現在の広報を紙面だけでなくウェブ、メール配信、防災行政無線、SNSなど複数媒体へ展開している。これは回覧板から広報紙へ一直線に置き換わったのではなく、到達速度、保存性、対象者、緊急性の違う媒体が積み重なった結果である。創刊号の発行目的と現在の媒体政策を同じ『市からのお知らせ』で一括しない。",
        "records": "回覧文書、配布簿、創刊号、編集規程、自治会別配布数、訂正文、ウェブ公開履歴",
        "unit": "発行部数・世帯数・配布先・閲覧数・登録者数・情報更新時刻",
        "actors": "未加入世帯、転入者、視覚障害者、外国語話者、配布担当者",
        "question": "創刊時の配布区域・発行主体・読者投稿欄がどのように変わったか",
        "sources": [("https://www.city.iwata.shizuoka.jp/shiseijouhou/kouhou_kouchou/index.html", "磐田市「広報・広聴」")],
    },
    "c147": {
        "fact": "磐田市公式資料によれば、現市章は『い』をモチーフにし、青・緑・赤へ自然、文化、活力、希望などの意味を与える。市の花・木・昆虫は、2005年合併後の市域を対象に選定委員会と市民アンケートを経て2009年2月1日に制定された。旧中泉町章、旧磐田市章、現市章、市の木を一つの連続した意匠史にせず、制定主体と対象区域を分ける。",
        "records": "章制定告示、応募原画、選定委員会記録、市民アンケート、使用規程、合併協議資料",
        "unit": "旧町・旧市・合併後市、章・ロゴ・花木昆虫・記念標章",
        "actors": "デザイン応募者、選定委員、アンケート回答者、旧市町村住民",
        "question": "旧章が公印・庁舎・旗・学校備品でいつまで使用されたか",
        "sources": [("https://www.city.iwata.shizuoka.jp/shiseijouhou/profile/1002307.html", "磐田市「市章」"), ("https://www.city.iwata.shizuoka.jp/shiseijouhou/profile/hana_ki_koncfuu_shika/1004446.html", "磐田市「市の花・木・昆虫」")],
    },
    "n099": {
        "fact": "磐田市は旧見付学校校舎を国指定史跡ではなく、国指定文化財の建造物として案内し、現在の小中学校一覧は現行の設置校を示す。中泉学校の仮校舎、校舎新築、学区再編を検証するときは、見付学校の著名な校舎史を中泉へ転用せず、学校沿革誌・建築図・土地台帳を中泉固有の系列として追う必要がある。",
        "records": "開校伺、校舎平面図、土地寄付証書、学校日誌、学区告示、児童名簿",
        "unit": "学校名・設置者・所在地・校舎・学区・児童数",
        "actors": "寄付者、借家所有者、通学児童、教員、学区境界の世帯",
        "question": "仮校舎から旧校舎への移転日と、校舎・学校組織の継承関係",
        "sources": [("https://www.city.iwata.shizuoka.jp/kosodate_kyouiku/shougakkou_chuugakkou/index.html", "磐田市「小学校・中学校」"), ("https://www.city.iwata.shizuoka.jp/sports_midokoro/bunkazai/kunishitei/1002050.html", "磐田市「旧見付学校」")],
    },
    "s035": {
        "fact": "国立公文書館の山岡鉄舟展は、鉄舟を幕臣・書家として一次資料とともに位置づける。一方、龍門館との関係や長野小学校に伝わった扁額の由来は、中央の人物史だけでは証明できない。扁額現物の落款・印章・材質・裏書、学校受入記録、仲介者の書簡をそろえ、筆跡評価と伝来経路を別々に検証する必要がある。",
        "records": "扁額現物、落款・印章写真、寄贈台帳、学校沿革誌、仲介者書簡、修理記録",
        "unit": "揮毫年・寄贈年・掲額年・移管年・修理年",
        "actors": "龍門館の学習者、扁額の依頼者、仲介者、学校保管者、地域の伝承者",
        "question": "鉄舟本人の揮毫を示す同時代記録と、龍門館から学校への移管経路",
        "sources": [("https://www.archives.go.jp/exhibition/haruaki_30_haru.html", "国立公文書館「江戸無血開城と山岡鉄舟」")],
    },
    "c148": {
        "fact": "文部科学省『学制百年史』は、学校制度を明治6年、14年、25年、33年、41年など改革時点ごとの系統図で示す。机、試験、授業料、規則を語る際も、どの小学校令・教則の時期かを固定しなければならない。全国制度は教室の枠を示すが、磐田の時間割、欠席、机の形、授業料徴収を証明するのは学校日誌や町村決算である。",
        "records": "学校日誌、教則、時間割、試験簿、授業料台帳、備品台帳、児童作文",
        "unit": "制度上の課程・学校の実施科目・児童が経験した授業",
        "actors": "女子児童、欠席児童、授業料免除世帯、代用教員、子守を担った子ども",
        "question": "底本に出る規則・試験・机がどの学校と年度の記録か",
        "sources": [("https://www.mext.go.jp/b_menu/hakusho/html/others/detail/1318188.htm", "文部科学省『学制百年史』学校系統図")],
    },
    "c149": {
        "fact": "文部科学省『学制百年史』は、明治期の小学校費を設置者負担、授業料、国庫負担の変化として説明する。学校組合は複数町村が費用と運営を共同化する仕組みだが、負担割合は人口・児童数・財産・距離など規約ごとに異なる。『共同で支えた』という結論は、組合規約と各町村決算を同じ年度で突き合わせて初めて具体化できる。",
        "records": "学校組合規約、負担金割当表、町村決算、児童数、校地台帳、組合会議事録",
        "unit": "人口割・戸数割・財産割・児童数割・定額負担",
        "actors": "遠距離通学世帯、組合外通学者、負担町村の納税者、校地提供者",
        "question": "各町村の負担割合と、議員・保護者が示した異議や要望",
        "sources": [("https://www.mext.go.jp/b_menu/hakusho/html/others/detail/1317617.htm", "文部科学省『学制百年史』小学校制度の整備")],
    },
    "c150": {
        "fact": "文部科学省資料は、1947年学校教育法による身体検査、1949年規程の検査項目、1958年学校保健法という制度変化を区別する。また『学制百年史』は、学校給食が1932年の欠食児童救済、戦時中断、1946年以後の全国普及を経たと説明する。体格検査、健康診断、欠食救済、全校給食を同じ福祉施策としてまとめない。",
        "records": "身体検査簿、学校医記録、給食日誌、欠食児童調査、扶助申請、町村・PTA会計",
        "unit": "対象児童・実施児童・延べ食数・欠席者・未納者・支援決定者",
        "actors": "検査を欠席した児童、給食費未納世帯、障害児、養護担当者、調理従事者",
        "question": "磐田で各制度が始まった年月と、対象選別から全員給食への移行",
        "sources": [("https://www.mext.go.jp/content/20250715-mxt_kenshoku-000043834_08.pdf", "文部科学省「健康診断の変遷」"), ("https://www.mext.go.jp/b_menu/hakusho/html/others/detail/1317788.htm", "文部科学省『学制百年史』学校給食の普及・奨励")],
    },
    "c151": {
        "fact": "文部科学省『学制百年史』は1945年までを戦時下教育として区分するが、全国制度史だけでは磐田の分散授業場所や開始日を特定できない。空襲警報、校舎使用制限、寺院・民家・屋外への移動、児童の欠席は学校ごとに異なる。『分散授業が行われた』という確認と、毎日同じ場所で授業が継続したという推定を分ける。",
        "records": "学校日誌、警報記録、分散先一覧、出席簿、児童作文、寺院・自治組織の記録",
        "unit": "学校・学年・分散班・授業日・警報日・欠席日",
        "actors": "疎開児童、勤労動員中の上級生、病弱児、受入家庭、分散先の管理者",
        "question": "各校の分散先、使用期間、授業内容、空襲警報による中止日",
        "sources": [("https://www.mext.go.jp/b_menu/hakusho/html/others/detail/1317552.htm", "文部科学省『学制百年史』"), ("https://www.city.iwata.shizuoka.jp/_res/projects/default_project/_page_/001/016/021/heiwa_book.pdf", "磐田市『磐田の戦争と平和』")],
    },
    "c152": {
        "fact": "文部科学省『学制百二十年史』は、1876年の東京女子師範学校附属幼稚園を本格的幼稚園の最初とし、1899年の幼稚園保育及設備規程で法的基準が明確になったと説明する。見付で1895年に議決された付属幼稚園構想は、この全国制度化以前の地域事例として検討できるが、議決、開園、継続を同じ出来事にしない。",
        "records": "町会議決、設置認可、園児名簿、保育者辞令、予算、園舎図、休廃止届",
        "unit": "構想・議決・認可・開園・休止・再開・制度上の継承",
        "actors": "就園しなかった幼児、保育者、母親、幼児を小学校へ通わせた家庭",
        "question": "1895年の議決後に実際の保育がいつ、どこで、誰により始まったか",
        "sources": [("https://www.mext.go.jp/b_menu/hakusho/html/others/detail/1318229.htm", "文部科学省『学制百二十年史』幼稚園の成立と展開")],
    },
    "c153": {
        "fact": "文部科学省『学制百年史』は、米国教育使節団報告を背景に、文部省とCIEが1947年に『父母と先生の会―教育民主化の手引』、1948年に参考規約を作成したとする。PTAを占領軍が一律に設置した組織と書くのは正確でなく、国の手引、県・市の伝達、各校の規約作成、会員の参加を別々に追う必要がある。",
        "records": "結成趣意書、初期規約、総会議事録、会費台帳、学校日誌、市連絡会記録",
        "unit": "国の手引・県通知・学校結成日・連絡会発会日・規約改正日",
        "actors": "加入しなかった保護者、母親、父親、教職員、地域有志、会費免除世帯",
        "question": "岩田小学校を市内最初とする根拠と、通知以前の準備過程",
        "sources": [("https://www.mext.go.jp/b_menu/hakusho/html/others/detail/1318266.htm", "文部科学省『学制百年史』PTAの成立")],
    },
    "c154": {
        "fact": "文部科学省『学制百年史』は、1934年時点で青年訓練所1万5,770、生徒91万5,461人と、実業補習学校1万5,315校の併存を示し、少なくとも半数が二重学籍だったと説明する。青年訓練所、実業補習学校、青年学校、任意の青年会・青年団は名称も対象も違う。磐田の団旗や訓練記録を全国制度のどこへ置くかを確定する必要がある。",
        "records": "青年訓練所学籍簿、実業補習学校名簿、青年団規約、団旗台帳、教練日誌、出席簿",
        "unit": "施設数・在籍者・二重学籍・訓練日・団体会員・任意参加",
        "actors": "女子青年、未就学者、農繁期欠席者、在郷軍人、青年団役員",
        "question": "底本の団旗・青年会活動が学校制度、軍事訓練、地域団体のどれに属したか",
        "sources": [("https://www.mext.go.jp/b_menu/hakusho/html/others/detail/1317682.htm", "文部科学省『学制百年史』青少年教育の進展")],
    },
}


def article_block(article: dict, item: dict) -> str:
    title = html.escape(article["short_title"])
    records = html.escape(item["records"])
    unit = html.escape(item["unit"])
    actors = html.escape(item["actors"])
    question = html.escape(item["question"])
    return f'''\n{START}
<section class="l3-review" aria-label="公的資料による再検証">
  <p class="section-label"><strong>公的資料で再検証する――底本の記述を全国制度へ照らす</strong></p>
  <p>{item["fact"]}</p>
  <p>この照合で確定できるのは制度の骨格と全国的な時期である。磐田での実施主体、開始日、人数、場所を確定するには地域側の一次史料が要る。全国の制度公布日を旧町村の実施日へ置き換えず、底本の記述が公文書そのものか、著者の要約か、聞き取りかを段落ごとに区別した。</p>
  <div class="table-wrap"><table><thead><tr><th>検証層</th><th>{title}で確認する内容</th></tr></thead><tbody>
    <tr><th>国制度</th><td>法令・国の公刊史・中央機関の記録。制度の名称、施行時期、全国的な目的を確認する。</td></tr>
    <tr><th>静岡県</th><td>県令・県公報・統計・所管課文書。国制度が県内へ伝達された時期と例外を確認する。</td></tr>
    <tr><th>旧町村・学校</th><td>{records}を照合し、磐田での実施日と運用を確定する。</td></tr>
    <tr><th>未確認</th><td>{question}。現段階では断定せず、追跡課題として残す。</td></tr>
  </tbody></table></div>
  <p class="section-label"><strong>数字と制度名を追試できる形にする</strong></p>
  <p>{title}の数量は、{unit}を区別する。同じ数字でも区域、基準日、対象年齢、重複計上の扱いが違えば比較できない。底本、国の統計、旧町村資料の数字が食い違う場合は平均化せず、定義の違いを表へ残す。</p>
  <p>名称の似た制度を改称の連続として扱わない。設置根拠、所管、対象者、財源、強制力の五項目をそろえ、五項目のどこが変わったかを確認する。建物、役員、帳簿が引き継がれても、法的性格まで同一とは限らない。</p>
  <p>記録からこぼれやすいのは、{actors}である。公的記録に名前がないことを不在の証明にせず、家計簿、書簡、作文、写真、聞き取りを補助資料として使う。ただし後年の記憶は、同時代記録と一致する部分と一致しない部分を分けて保存する。</p>
  <p class="section-label"><strong>本稿の到達点と更新条件</strong></p>
  <p>本稿の立場は、底本を地域の具体的な調査索引として尊重しながら、制度説明は公的資料へ戻し、磐田固有の細部は地域一次史料が確認できた範囲に限定する、というものである。資料が不足する箇所は『なかった』ではなく『現時点で確認できない』と記す。</p>
  <p>今後、{records}のいずれかが確認され、{question}への回答が得られた場合は、本文、年表、図、参考資料、更新履歴を同時に改める。新資料が従来説明と矛盾する場合も削除せず、旧説明の根拠と訂正理由を履歴へ残す。</p>
</section>
{END}\n'''


def inject_article(path: Path, block: str, sources: list[tuple[str, str]]) -> None:
    raw = path.read_text(encoding="utf-8")
    if START in raw:
        before, rest = raw.split(START, 1)
        _, after = rest.split(END, 1)
        raw = before + block.strip("\n") + after
    else:
        marker = '<p class="section-label"><strong>年代を整理する</strong></p>'
        if marker not in raw:
            raise RuntimeError(f"timeline marker missing: {path.name}")
        raw = raw.replace(marker, block + marker, 1)
    for url, label in sources:
        if url not in raw:
            li = f'      <li><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a></li>\n'
            marker = "  </ul></section>"
            pos = raw.find(marker, raw.find('<section class="sources">'))
            if pos < 0:
                raise RuntimeError(f"sources marker missing: {path.name}")
            raw = raw[:pos] + li + raw[pos:]
    old = f'<li><time datetime="2026-08-24">2026年8月24日</time> 初版公開。'
    addition = f'<li><time datetime="{DATE}">2026年8月25日</time> 公的資料による再検証、史料階層、数量定義、未確認事項を追補しL3へ増強。</li>'
    if addition not in raw:
        hist = raw.find('<section class="revision-history">')
        ul = raw.find("<ul>", hist)
        raw = raw[:ul + 4] + addition + raw[ul + 4:]
    raw = re.sub(r"(?m)^[ \t]+$", "", raw)
    path.write_text(raw, encoding="utf-8", newline="\n")


def update_registry(by_slug: dict[str, dict]) -> None:
    path = ROOT / "data" / "pages.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    pages = doc["pages"] if isinstance(doc, dict) else doc
    indexed = {p.get("url", "").lstrip("/").removesuffix(".html"): p for p in pages}
    for slug, article in by_slug.items():
        p = indexed[slug]
        p["updated_at"] = DATE
        p["level"] = "L3"
        p["topics"] = article["topics"]
        refs = p.setdefault("source_refs", [])
        for url, _ in DATA[slug]["sources"]:
            ref = f"web:{url}"
            if ref not in refs:
                refs.append(ref)
    if isinstance(doc, dict):
        doc["updated_at"] = DATE
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_recent(by_slug: dict[str, dict]) -> None:
    path = ROOT / "data" / "new-articles.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    targets = {f"/{slug}.html" for slug in by_slug} | {f"/{slug}" for slug in by_slug}
    items = [x for x in items if x.get("url") not in targets]
    fresh = []
    for index, slug in enumerate(by_slug):
        a = by_slug[slug]
        fresh.append({"date": DATE, "category": f'{a["category"]}・更新', "title": a["title"], "url": f"/{slug}.html", "published_at": f"2026-08-25T11:{59-index:02}:00+09:00"})
    items = fresh + items
    items.sort(key=lambda x: (x.get("date", ""), x.get("published_at", "")), reverse=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_sitemap(slugs: list[str]) -> None:
    path = ROOT / "sitemap.xml"
    raw = path.read_text(encoding="utf-8")
    for slug in slugs:
        pattern = rf'(<url>\s*<loc>https://iwata-monogatari\.net/{slug}(?:\.html)?</loc>\s*<lastmod>)[^<]+(</lastmod>)'
        raw, count = re.subn(pattern, rf'\g<1>{DATE}\g<2>', raw, count=1)
        if count != 1:
            raise RuntimeError(f"sitemap target missing: {slug}")
    path.write_text(raw, encoding="utf-8", newline="\n")


def update_ledger(by_slug: dict[str, dict]) -> None:
    path = ROOT / "docs" / "pages-ledger.md"
    raw = path.read_text(encoding="utf-8").rstrip()
    marker = "<!-- second-volume-l3-20260825 -->"
    if marker in raw:
        raw = raw.split(marker, 1)[0].rstrip()
    rows = "\n".join(f'| `{slug}.html` | {article["title"]} | L2→L3 | 公的資料との照合・史料階層・未確認事項を増強 |' for slug, article in by_slug.items())
    addition = f'''\n\n{marker}
## 2026-08-25　第二編19ページ L3増強

| URL | 記事 | 等級 | 更新内容 |
|---|---|---|---|
{rows}
'''
    path.write_text(raw + addition, encoding="utf-8", newline="\n")


def main() -> None:
    by_slug = {a["slug"]: a for a in ARTICLES}
    if set(by_slug) != set(DATA):
        raise RuntimeError(f"article set mismatch: {sorted(set(by_slug) ^ set(DATA))}")
    for slug, article in by_slug.items():
        inject_article(ROOT / f"{slug}.html", article_block(article, DATA[slug]), DATA[slug]["sources"])
    update_registry(by_slug)
    update_recent(by_slug)
    update_sitemap(list(by_slug))
    update_ledger(by_slug)
    print(f"enhanced {len(by_slug)} second-volume articles to L3")


if __name__ == "__main__":
    main()
