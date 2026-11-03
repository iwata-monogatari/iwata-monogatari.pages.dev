const test=require('node:test'),assert=require('node:assert/strict');
const S=require('../assets/js/search-core.js');
const metadata={dictionary:[{entityId:'district:fukude',entityType:'district',preferredLabel:'福田',reading:'ふくで',aliases:[]}],records:[
 {id:'f001',sourceIds:['f001'],title:'福田湊の発展と漁業史',description:'',headings:[],keywords:[],aliases:[],entities:['district:fukude']},
 {id:'compound',sourceIds:['compound'],title:'福田中島（ふくでなかじま）の読み方',description:'',headings:[],keywords:[],aliases:[],entities:['district:fukude']},
 {id:'whole',sourceIds:['whole'],title:'福田（ふくで）の読み方',description:'',headings:[],keywords:[],aliases:[],entities:['district:fukude']}
]};
test('whole kana reading and confirmed regional articles precede a prefix inside a longer reading',()=>{
 const docs=S.prepare(metadata),q=S.validate({q:'ふくで'},[],[]),hits=docs.map(doc=>S.score(doc,q,[S.metadataMatch(doc,'ふくで')]));S.sort(hits,q);
 assert.deepEqual(hits.map(r=>r.id),['whole','f001','compound']);
 assert.ok(S.metadataMatch(docs[1],'なかじま'));
 const exact=S.validate({q:metadata.records[1].title},[],[]);assert.ok(S.score(docs[1],exact,[{score:500,reason:'題名に一致'}]).score>100000);
});
