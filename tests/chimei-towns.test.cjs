const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {normalize,matches}=require('../assets/js/chimei-towns.js');
test('town lookup accepts kana and both written chome forms without changing a place-name numeral',()=>{
 assert.ok(matches('今之浦一丁目 いまのうら1ちょうめ','今之浦１丁目'));
 assert.ok(matches('万瀬 まんぜ マンゼ','マンゼ'));
 assert.ok(matches('明ケ島 みょうがじま','明ヶ島'));
 assert.ok(matches('東新屋 ひがしあらや','東新屋 あらや'));
 assert.equal(matches('西之島 にしのしま','豊田西之島'),false);
 assert.equal(normalize('一色'),'一色');
});
test('all 186 current records are rendered once and use the paired allowlisted town codes',()=>{
 const data=JSON.parse(fs.readFileSync('data/chimei-towns.json','utf8')),html=fs.readFileSync('chimei/towns/index.html','utf8'),contract=JSON.parse(fs.readFileSync('data/chimei-handoff.json','utf8'));
 assert.equal(data.items.length,186);assert.equal(new Set(data.items.map(r=>r.name)).size,186);assert.equal((html.match(/data-town-id=/g)||[]).length,186);
 for(const row of data.items){assert.ok(html.includes('data-town-id="'+row.id+'"'));assert.equal(contract.towns[row.code],row.name);assert.ok(row.reading);}
 assert.equal(data.auxiliary_records.length,4);assert.ok(!data.items.some(r=>r.name==='一言旧豊田町'));
});
