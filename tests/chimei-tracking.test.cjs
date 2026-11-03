const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('assets/js/chimei.js','utf8');
function run(search,hostname='iwata-monogatari.net',entry='hub_bottom'){
 const fields=[],events=[],handlers={};
 const form={appendChild(x){fields.push(x);},addEventListener(type,fn){handlers[type]=fn;}};
 const link={href:'https://fudosan.atawi.link/karte/?area=磐田市&chimei=hub_bottom',addEventListener(){}};
 const element={dataset:{chimeiEntry:entry},querySelector(s){return s==='form'?form:link;}};
 vm.runInNewContext(source,{URL,URLSearchParams,location:{search,hostname},navigator:{webdriver:false},window:{fgaTrack(name){events.push(name);}},document:{querySelectorAll(){return [element];},createElement(){return {};}}});
 handlers.submit();return {fields,events,link};
}
test('QA uses the receiver-supported ignore flag and cannot count source clicks',()=>{
 for(const query of ['?fga_internal=1','?fga_ignore=1']){
  const s=run(query);assert.deepEqual(s.events,[]);assert.equal(s.fields[0].name,'fga_ignore');assert.equal(s.fields[0].value,'1');assert.equal(new URL(s.link.href).searchParams.get('fga_ignore'),'1');
 }
 assert.equal(run('', 'localhost').fields[0].name,'fga_ignore');
});
test('ordinary click only records a fixed public entry code without selected address data',()=>{
 const s=run('');assert.deepEqual(s.events,['chimei_hub_bottom_click']);assert.equal(s.fields.length,0);
});
test('expanded guide and region entries count fixed codes while rejecting an arbitrary source',()=>{
 for(const entry of ['fukude_bottom','toyooka_early','missing-aza_bottom','similar-names_early']){
  assert.deepEqual(run('','iwata-monogatari.net',entry).events,['chimei_'+entry.replace(/-/g,'_')+'_click']);
 }
 assert.deepEqual(run('','iwata-monogatari.net','private_person_bottom').events,[]);
});
