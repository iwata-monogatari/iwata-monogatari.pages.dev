const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const assert=require('node:assert/strict');
const test=require('node:test');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/enshu-legacy-navigation.js'),'utf8');
function target(input){let result=null;vm.runInNewContext(source,{URL,location:{href:'https://iwata-monogatari.net'+input,origin:'https://iwata-monogatari.net',replace:url=>result=url}});return result;}
test('old activity anchors open their dedicated pages',()=>{for(const [hash,dest] of [['courses','courses'],['practice','practice'],['cards','words']])assert.equal(target('/enshu/#'+hash),'/enshu/'+dest+'/');});
test('old shared word keeps its ID and internal-traffic flag',()=>assert.equal(target('/enshu/?word=jurui&fga_internal=1#cards'),'/enshu/words/?word=jurui&fga_internal=1'));
test('old course IDs keep their destination including work',()=>{assert.equal(target('/enshu/#scene-kitchen'),'/enshu/courses/kitchen/');assert.equal(target('/enshu/#scene-work'),'/enshu/courses/work-tools/');});
test('unknown anchors do not redirect to nonexistent courses',()=>assert.equal(target('/enshu/#scene-nonexistent'),null));
test('the entrance without an activity remains the entrance',()=>assert.equal(target('/enshu/'),null));
