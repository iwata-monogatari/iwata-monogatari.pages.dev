const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {findSections,normalize}=require('../assets/js/c006-explanation-search.js');
const html=fs.readFileSync(path.join(__dirname,'../c006.html'),'utf8');
const plain=s=>s.replace(/<[^>]+>/g,' ').replace(/&amp;/g,'&');
const sections=[];
for(const m of html.matchAll(/<div class="gsec"[^>]*data-explanation-search="([^"]+)"[^>]*>/g)){
 let depth=0,end;
 for(const t of html.slice(m.index).matchAll(/<\/?div\b[^>]*>/g)){depth+=t[0].startsWith('</')?-1:1;if(!depth){end=m.index+t.index+t[0].length;break;}}
 const block=html.slice(m.index,end);const heading=block.match(/<h2[^>]*>(.*?)<\/h2>|<p class="gh2"[^>]*>(.*?)<\/p>|<p><strong>(.*?)<\/strong>/s);
 assert.ok(heading,m[1]);const text=plain(block),shortForms=[...text.matchAll(/「([^」]+)」/g)].flatMap(m=>m[1].split(/[・／/、]/)).concat([...block.matchAll(/<td[^>]*>(.*?)<\/td>/gs)].map(m=>plain(m[1]))).map(normalize).filter(t=>t.length===1);sections.push({id:m[1],title:plain(heading[1]||heading[2]||heading[3]),text,shortForms});
}
test('all existing explanatory sections have unique working anchors',()=>{
 assert.equal(sections.length,19);assert.equal(new Set(sections.map(s=>s.id)).size,19);
 for(const s of sections){assert.equal((html.match(new RegExp('id="'+s.id+'"','g'))||[]).length,1,s.id);assert.ok(findSections(sections,s.title).some(x=>x.id===s.id),s.title);}
});
test('existing grammar examples and explanatory terms are reachable, including kana and query modifiers',()=>{
 for(const [q,id] of [['食べれる','grammar-forms'],['降らなんだ','grammar-forms'],['雨ん降ってきた','grammar-particles'],['が','grammar-particles'],['け','grammar-endings'],['ん','negative-possibility'],['ジュビロ','grammar-iwata-accent'],['イ音便','dialect-sounds'],['無声化','dialect-glossary'],['ぜんいちたい','dialect-glossary'],['頭高型 意味','grammar-iwata-accent'],['磐田地方の方言集','dialect-literature'],['検索結果を共有','dictionary-help'],['見れん','negative-possibility']])assert.ok(findSections(sections,q).some(x=>x.id===id),q);
 assert.deepEqual(findSections(sections,'じゅびろ').map(s=>s.id),findSections(sections,'ジュビロ').map(s=>s.id));
});
test('no navigation is invented for empty, generic, unknown or mismatched compound searches',()=>{
 for(const q of ['', '遠州弁', '方言 意味', 'のんばめる', '無声化 のんばめる','未練'])assert.deepEqual(findSections(sections,q),[],q);
});
