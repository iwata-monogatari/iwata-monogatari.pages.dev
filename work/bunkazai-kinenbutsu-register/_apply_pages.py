import json
P='data/pages.json'
d=json.load(open(P,encoding='utf-8-sig'))
def e(title,url,district,themes,parent,summary):
    return {"title":title,"url":url,"district":[district],"themes":themes,
            "content_type":"reading","published_at":"2026-06-27","date_provisional":False,
            "status":"published","summary":summary,"parent":parent}
CP="cultural-property"; LM="land-memory"; ST="shrine-temple"
new=[
 e("阿多古山一里塚 ── 東海道見付宿の一里塚から、街道と道中の記憶を読む","m026.html","mitsuke",[CP,LM],"01001-mitsuke.html","市指定・史跡。見付の東海道一里塚を、公式指定情報と見付地区の地域史から読み直す。"),
 e("見付本陣（神谷家・鈴木家）墓所 ── 西光寺に眠る本陣の家から、宿場の運営を読む","m027.html","mitsuke",[CP,LM],"01001-mitsuke.html","市指定・史跡。見付宿本陣を務めた家の墓所を、公式指定情報と見付地区の地域史から読み直す。"),
 e("西光寺大クス附ナギの木 ── 見付宿西端の寺に育つ社寺林の巨木","m028.html","mitsuke",[CP,ST,LM],"01001-mitsuke.html","市指定・天然記念物。西光寺境内の大クスとナギを、公式指定情報と見付地区の地域史から読み直す。"),
 e("西光寺のイヌマキ ── 時宗の寺に立つイヌマキと見付の社寺林","m029.html","mitsuke",[CP,ST,LM],"01001-mitsuke.html","市指定・天然記念物。西光寺境内のイヌマキを、公式指定情報と見付地区の地域史から読み直す。"),
 e("澄水山古墳 ── 磐田農業高校に残る古墳から、台地縁辺の首長墓を読む","n027.html","nakaizumi",[CP,LM],"01002-nakaizumi.html","市指定・史跡。中泉・磐田農業高校内の古墳を、公式指定情報と中泉地区の地域史から読み直す。"),
 e("アキザキヤツシロラン群生地 ── 福王寺の林床に生きる腐生植物と社寺林","n028.html","nakaizumi",[CP,ST,LM],"01002-nakaizumi.html","市指定・天然記念物。福王寺境内の稀少植物群生地を、公式指定情報と中泉地区の地域史から読み直す。"),
 e("天御子神社のヤマモモの木 ── 中央町の鎮守に育つ平地最大級のヤマモモ","n029.html","nakaizumi",[CP,ST,LM],"01002-nakaizumi.html","市指定・天然記念物。中央町・天御子神社のヤマモモを、公式指定情報と地域史から読み直す（地区分類は要確認）。"),
 e("福王寺のケヤキ ── 城之崎の古刹に立つ平地最大級のケヤキ","n030.html","nakaizumi",[CP,ST,LM],"01002-nakaizumi.html","市指定・天然記念物。福王寺境内のケヤキを、公式指定情報と中泉地区の地域史から読み直す。"),
 e("福王寺のクロバイ ── 染めの媒染に使われた常緑樹と境内の植生","n031.html","nakaizumi",[CP,ST,LM],"01002-nakaizumi.html","市指定・天然記念物。福王寺境内のクロバイを、公式指定情報と中泉地区の地域史から読み直す。"),
 e("静岡県立磐田農業高等学校記念館 ── 中泉に移った農業教育と登録文化財の校舎","n032.html","nakaizumi",[CP,LM],"01002-nakaizumi.html","国登録・有形文化財。磐田農業高校記念館を、登録制度の説明とともに中泉地区の近代教育史から読み直す。"),
 e("御厨古墳群 ── 松林山古墳に始まる新貝・鎌田の大型古墳群","u027.html","mikuriya",[CP,LM],"01003-mikuriya.html","国指定・史跡。御厨・新貝の大型古墳群を、公式指定情報と御厨地区の地域史から読み直す。"),
 e("医王寺庭園及び参道 ── 鎌田の名勝庭園と参道空間を歩く","u028.html","mikuriya",[CP,ST,LM],"01003-mikuriya.html","市指定・名勝。鎌田・医王寺の庭園と参道を、公式指定情報と御厨地区の地域史から読み直す。"),
 e("袴田家のマキ ── 鎌田の屋敷林に立つイヌマキと遠州の風土","u029.html","mikuriya",[CP,LM],"01003-mikuriya.html","市指定・天然記念物。鎌田・袴田家の屋敷木マキを、公式指定情報と御厨地区の地域史から読み直す。"),
 e("須賀神社クス ── 西島の鎮守に育つ低地のクスと水辺の信仰","r015.html","ryuyo",[CP,ST,LM],"01007-ryuyo.html","市指定・天然記念物。西島・須賀神社のクスを、公式指定情報と地域史から読み直す（地区分類は要確認）。"),
]
have={p['url'] for p in d['pages']}
add=[n for n in new if n['url'] not in have]
d['pages'].extend(add)
d['updated_at']="2026-06-27"
open(P,'w',encoding='utf-8').write('﻿'+json.dumps(d,ensure_ascii=False,indent=4)+'\n')
print('appended',len(add),'total now',len(d['pages']))
# validate
json.load(open(P,encoding='utf-8-sig')); print('valid json')
