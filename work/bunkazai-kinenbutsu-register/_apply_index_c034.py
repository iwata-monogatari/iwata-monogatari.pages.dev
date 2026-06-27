import json,re

# ---------- c034.html ----------
c=open('c034.html',encoding='utf-8').read()
def li(u,t): return '      <li><a href="/%s">%s</a></li>\n'%(u,t)
ins={
 '      <li><a href="/m022.html">木造毘沙門天立像</a></li>\n':[
   ('m025.html','甲塚のクロガネモチ ── かぶと塚公園に残る古墳と巨木'),
   ('m026.html','阿多古山一里塚 ── 東海道見付宿の一里塚'),
   ('m027.html','見付本陣（神谷家・鈴木家）墓所 ── 西光寺に眠る本陣の家'),
   ('m028.html','西光寺大クス附ナギの木 ── 見付宿西端の寺の社寺林'),
   ('m029.html','西光寺のイヌマキ ── 時宗の寺に立つ巨木'),
 ],
 '      <li><a href="/n024.html">府八幡宮楼門</a></li>\n':[
   ('n026.html','善導寺大クス ── 中泉の市街地に残る大クス'),
   ('n027.html','澄水山古墳 ── 磐田農業高校に残る古墳'),
   ('n028.html','アキザキヤツシロラン群生地 ── 福王寺の林床に生きる腐生植物'),
   ('n029.html','天御子神社のヤマモモの木 ── 中央町の鎮守の巨木'),
   ('n030.html','福王寺のケヤキ ── 城之崎の古刹に立つ平地最大級のケヤキ'),
   ('n031.html','福王寺のクロバイ ── 染めの媒染に使われた常緑樹'),
   ('n032.html','静岡県立磐田農業高等学校記念館 ── 中泉の農業教育と登録文化財'),
 ],
 '      <li><a href="/u024.html">西貝塚から安久路・城之崎へ — 田園から市街地へ変わった地域の記憶</a></li>\n':[
   ('u027.html','御厨古墳群 ── 松林山古墳に始まる大型古墳群【国指定史跡】'),
   ('u028.html','医王寺庭園及び参道 ── 鎌田の名勝庭園と参道'),
   ('u029.html','袴田家のマキ ── 鎌田の屋敷林に立つイヌマキ'),
 ],
 '      <li><a href="/r012.html">旧竜洋町になるまでの変遷 ── 江戸・明治・大正期の町村沿革と生活圏の形成</a></li>\n':[
   ('r015.html','須賀神社クス ── 西島の鎮守に育つ低地のクス'),
 ],
}
for anchor,items in ins.items():
    assert c.count(anchor)==1, ('c034 anchor',anchor[:40],c.count(anchor))
    c=c.replace(anchor, anchor+''.join(li(u,t) for u,t in items),1)
assert '現在 <strong>206</strong> 本' in c
c=c.replace('現在 <strong>206</strong> 本','現在 <strong>222</strong> 本')
open('c034.html','w',encoding='utf-8').write(c)
print('c034 ok')

# ---------- index.html ----------
i=open('index.html',encoding='utf-8').read()
assert '>216<span>ページ</span>' in i
i=i.replace('>216<span>ページ</span>','>252<span>ページ</span>')
def nali(url,cat,title,area):
    ac=' '+area if area else ''
    return ('          <li class="new-article-item">\n'
            '            <a href="%s" class="new-article-link%s">\n'
            '              <span class="new-article-date">2026-06-27</span>\n'
            '              <span class="new-article-category">%s</span>\n'
            '              <span class="new-article-title">%s</span>\n'
            '              <span class="new-article-arrow"> →</span>\n'
            '            </a>\n'
            '          </li>\n')%(url,ac,cat,title)
fallback=(nali('/u027.html','国指定史跡','御厨古墳群 ── 松林山古墳に始まる大型古墳群','area-mikuriya')
         +nali('/n032.html','国登録有形文化財','静岡県立磐田農業高等学校記念館 ── 中泉の農業教育','area-nakaizumi')
         +nali('/c021.html','記念物・登録文化財','記念物・登録文化財16ページの読みものを公開（甲塚のクロガネモチ・善導寺大クス・医王寺庭園ほか）',''))
mk='<ul class="new-article-list" id="new-article-list">\n'
assert mk in i
i=i.replace(mk, mk+fallback,1)
open('index.html','w',encoding='utf-8').write(i)
print('index ok')

# ---------- new-articles.json (canonical; also feeds updates.html) ----------
P='data/new-articles.json'
d=json.load(open(P,encoding='utf-8-sig'))
add=[
 {"date":"2026-06-27","category":"国指定史跡","title":"御厨古墳群 ── 松林山古墳に始まる大型古墳群","url":"/u027.html"},
 {"date":"2026-06-27","category":"国登録有形文化財","title":"静岡県立磐田農業高等学校記念館 ── 中泉の農業教育","url":"/n032.html"},
 {"date":"2026-06-27","category":"記念物・登録文化財","title":"記念物・登録文化財16ページの読みものを公開（甲塚のクロガネモチ・善導寺大クス・医王寺庭園ほか）","url":"/c021.html"},
]
urls={e.get('url') for e in d}
new=[a for a in add if not (a['url'] in urls and any(e['url']==a['url'] and e['title']==a['title'] for e in d))]
d=add+d
open(P,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('new-articles +',len(add),'total',len(d))
json.load(open(P,encoding='utf-8-sig'))  # validate
print('json valid')
