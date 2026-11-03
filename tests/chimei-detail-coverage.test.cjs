const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const data=JSON.parse(fs.readFileSync('data/chimei-towns.json','utf8')),details=JSON.parse(fs.readFileSync('data/chimei-details.json','utf8')),contract=JSON.parse(fs.readFileSync('data/chimei-handoff.json','utf8'));
test('all 186 official labels lead to exactly one individual reference, reusing the seven existing pages',()=>{
 assert.equal(details.items.length,179);assert.equal(Object.keys(details.existing).length,7);
 assert.equal(new Set(data.items.map(r=>r.detail)).size,186);
 for(const r of data.items){
  assert.ok(r.detail);const html=fs.readFileSync(r.detail.slice(1)+'index.html','utf8');
  assert.ok(html.includes('https://iwata-monogatari.net'+r.detail));assert.equal(contract.towns[r.code],r.name);
  if(details.existing[r.name])assert.equal(r.detail,details.existing[r.name]);
  else{assert.ok(html.includes('chimei_town='+r.code));assert.ok(html.includes('value="'+r.code+'"'));assert.ok(html.includes('towns_bottom'));}
 }
});
test('unlocated Oya and post-replot Shingai never borrow a falsely labelled location',()=>{
 const oya=details.items.find(r=>r.name==='大谷'),html=fs.readFileSync(oya.path.slice(1)+'index.html','utf8');
 assert.ok(html.includes('所在地は未確認'));assert.ok(html.includes('大谷の現地写真ではありません'));assert.ok(!html.includes('alt="大谷周辺'));
 for(const name of ['新貝一丁目','新貝二丁目','新貝三丁目']){const row=details.items.find(r=>r.name===name);assert.equal(row.photo_scope,'新貝');const text=fs.readFileSync(row.path.slice(1)+'index.html','utf8');assert.ok(text.includes('alt="新貝周辺の航空写真"'));assert.ok(text.includes('2023年10月13日'));}
 const owara=details.items.find(r=>r.name==='大原');assert.ok(owara.facts.find(r=>r[0]==='郵便番号')[1].includes('437-1211'));
});
