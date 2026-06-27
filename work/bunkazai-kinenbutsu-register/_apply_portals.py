import re
def card(theme,label,url,title,desc):
    return ('        <article class="content-card" data-district="%s" data-theme="%s" data-published="2026-06-27">\n'
            '          <p class="card-label">%s</p>\n'
            '          <h3><a href="/%s">%s</a></h3>\n'
            '          <p>%s</p>\n'
            '        </article>\n')%(DI,theme,label,url,title,desc)

jobs={
 '01001-mitsuke.html':('mitsuke','全16件','全21件',[
   ('cultural-property land-memory','天然記念物','m025.html','甲塚のクロガネモチ','県指定天然記念物。かぶと塚公園に残る古墳と巨木、学校跡が公園になった記憶。'),
   ('cultural-property land-memory road-traffic','史跡','m026.html','阿多古山一里塚','市指定史跡。東海道見付宿の一里塚から、街道と道中の記憶を読む。'),
   ('cultural-property land-memory','史跡','m027.html','見付本陣（神谷家・鈴木家）墓所','市指定史跡。西光寺に眠る本陣の家から、宿場の運営を読む。'),
   ('cultural-property shrine-temple land-memory','天然記念物','m028.html','西光寺大クス附ナギの木','市指定天然記念物。見付宿西端の寺に育つ社寺林の巨木。'),
   ('cultural-property shrine-temple land-memory','天然記念物','m029.html','西光寺のイヌマキ','市指定天然記念物。時宗の寺に立つイヌマキと見付の社寺林。'),
 ]),
 '01002-nakaizumi.html':('nakaizumi','全8件','全15件',[
   ('cultural-property shrine-temple land-memory','天然記念物','n026.html','善導寺大クス','県指定天然記念物。中泉の市街地に残る大クスと都市化の記憶。'),
   ('cultural-property land-memory','史跡','n027.html','澄水山古墳','市指定史跡。磐田農業高校に残る古墳から、台地縁辺の首長墓を読む。'),
   ('cultural-property shrine-temple land-memory','天然記念物','n028.html','アキザキヤツシロラン群生地','市指定天然記念物。福王寺の林床に生きる腐生植物と社寺林。'),
   ('cultural-property shrine-temple land-memory','天然記念物','n029.html','天御子神社のヤマモモの木','市指定天然記念物。中央町の鎮守に育つ平地最大級のヤマモモ。'),
   ('cultural-property shrine-temple land-memory','天然記念物','n030.html','福王寺のケヤキ','市指定天然記念物。城之崎の古刹に立つ平地最大級のケヤキ。'),
   ('cultural-property shrine-temple land-memory','天然記念物','n031.html','福王寺のクロバイ','市指定天然記念物。染めの媒染に使われた常緑樹と境内の植生。'),
   ('cultural-property architecture school land-memory','建物・学校','n032.html','静岡県立磐田農業高等学校記念館','国登録有形文化財。中泉に移った農業教育と登録文化財の校舎。'),
 ]),
 '01003-mikuriya.html':('mikuriya','全24件','全27件',[
   ('cultural-property land-memory','史跡','u027.html','御厨古墳群','国指定史跡。松林山古墳に始まる新貝・鎌田の大型古墳群。'),
   ('cultural-property shrine-temple land-memory','名勝','u028.html','医王寺庭園及び参道','市指定名勝。鎌田の名勝庭園と参道空間を歩く。'),
   ('cultural-property land-memory','天然記念物','u029.html','袴田家のマキ','市指定天然記念物。鎌田の屋敷林に立つイヌマキと遠州の風土。'),
 ]),
 '01007-ryuyo.html':('ryuyo','全12件','全13件',[
   ('cultural-property shrine-temple land-memory','天然記念物','r015.html','須賀神社クス','市指定天然記念物。西島の鎮守に育つ低地のクスと水辺の信仰。'),
 ]),
}
for fn,(DI,oldc,newc,cards) in jobs.items():
    s=open(fn,encoding='utf-8').read()
    block=''.join(card(t,l,u,ti,de) for (t,l,u,ti,de) in cards)
    marker='      <div class="content-cards">\n'
    assert marker in s, fn
    s=s.replace(marker, marker+block, 1)
    # update count (only the district-filter-count line)
    s=re.sub(r'(class="district-filter-count"[^>]*>)'+re.escape(oldc), r'\g<1>'+newc, s, count=1)
    open(fn,'w',encoding='utf-8').write(s)
    print(fn,'+%d cards, count %s->%s'%(len(cards),oldc,newc))
