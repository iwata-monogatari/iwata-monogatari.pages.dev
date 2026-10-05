// Exercise the real worker with a local public-file fetch adapter, plus independent exhaustive body matching.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm'), assert=require('node:assert/strict'), zlib=require('node:zlib');
const root=path.resolve(__dirname,'..');
const S=require('../assets/js/search-core.js');
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p)));
const manifest=json('data/search/manifest.json'), metadata=json(manifest.metadata), docs=S.prepare(metadata);
let resolveJob, requests=[], jobId=0, failMode='', ctx;
function resetWorker(){
ctx=vm.createContext({AbortController,setTimeout:(fn,ms)=>setTimeout(fn,failMode==='timeout'?0:ms),clearTimeout,console,Map,Set,URL,Promise,
 fetch:async (url,options)=> {
  if(failMode==='offline')throw new TypeError('offline');
  if(failMode==='timeout')return await new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('aborted'))));
  if(failMode==='http')return {ok:false};
  if(failMode==='json')return {ok:true,text:async()=>'{broken'};
  if(failMode==='schema'&&url.endsWith('manifest.json'))return {ok:true,text:async()=>JSON.stringify({...manifest,schemaVersion:0})};
  if(failMode==='mixed'&&url===manifest.metadata)return {ok:true,text:async()=>JSON.stringify({...metadata,dictionaryVersion:'bad'})};
  const start=performance.now();const raw=fs.readFileSync(path.join(root,url),'utf8');requests.push({url,bytes:zlib.gzipSync(raw).length});return {ok:true,text:async()=>raw};},
 importScripts:url=>vm.runInContext(fs.readFileSync(path.join(root,url),'utf8'),ctx),
 postMessage:message=>{if(['results','error'].includes(message.type))resolveJob(message);}});
vm.runInContext(fs.readFileSync(path.join(root,'assets/js/search-worker.js'),'utf8'),ctx);
}
resetWorker();
async function search(query){requests=[];const start=performance.now();const response=await new Promise(resolve=>{resolveJob=resolve;ctx.onmessage({data:{id:++jobId,query:{page:1,...query}}});});return {...response,ms:performance.now()-start,transferGzipBytes:requests.reduce((s,r)=>s+r.bytes,0),requests:requests.length};}
(async()=>{
 const report={count:docs.length,exactTitle:0,exactId:0,exceptions:[],cases:[],exhaustiveBodyCases:[],validation:[]};
 for(const doc of docs) for(const field of ['title','id']) {
  const query=S.validate({q:doc.record[field]},[],[]); const hits=docs.map(d=>({doc:d,matches:query.terms.map(t=>S.metadataMatch(d,t))})).filter(d=>d.matches.every(Boolean)).map(d=>S.score(d.doc,query,d.matches));S.sort(hits,query);
  if(hits[0]?.id!==doc.record.id) {assert.ok(field==='title' && S.normalize(hits[0].title)===S.normalize(doc.record.title),'wrong exact-title/ID top');report.exceptions.push({id:doc.record.id,field,top:hits[0]?.id,reason:'異なるcanonicalの記事に同一題名があるためID順で同順位を決定。対象も完全一致集合内。'});}else report[field==='title'?'exactTitle':'exactId']++;
 }
 const titleCounts=new Map();for(const doc of docs)titleCounts.set(S.normalize(doc.record.title),(titleCounts.get(S.normalize(doc.record.title))||0)+1);
 report.uniqueTitleQueries=docs.filter(d=>titleCounts.get(S.normalize(d.record.title))===1).length;
 report.sameTitleGroups=[...titleCounts.values()].filter(n=>n>1).length;
 report.sameTitleArticleCount=docs.length-report.uniqueTitleQueries;
 report.sourceIdQueries=0;
 for(const doc of docs)for(const id of doc.record.sourceIds){const query=S.validate({q:id},[],[]);const hits=docs.filter(d=>S.metadataMatch(d,S.normalize(id))).map(d=>S.score(d,query,[S.metadataMatch(d,S.normalize(id))]));S.sort(hits,query);assert.equal(hits[0]?.id,doc.record.id,'former ID '+id);report.sourceIdQueries++;}
 assert.equal(report.exactId,docs.length);
 for(const test of json('tests/search-cases.json')){
  const result=await search(test);assert.equal(result.type,'results',test.q+' worker error');
  for(const expected of test.expected) {const rank=result.records.findIndex(r=>r.id===expected)+1;assert.ok(rank>0&&rank<=test.maxRank,`${test.q}: ${expected} outside first20 / rank ${rank}`);}
  if(test.expected.length===0)assert.equal(result.total,0,test.q);
  report.cases.push({...test,total:result.total,top:result.records.slice(0,5).map(r=>r.id),ms:Math.round(result.ms),transferGzipBytes:result.transferGzipBytes,requests:result.requests});
 }
 const bodies=new Map(docs.map(d=>[d.record.id,json(d.record.body).text]));
 for(const q of ['中泉 軌道','福田','ふくで','福田半香','磐田の郷土史の出典を残す','郷土史 市史','崋山 義会','資料番号','シラス','ﾌｸﾃﾞ','ｶﾞ','漢字','\u304b\u3099']){
  const query=S.validate({q},[],[]);const expected=docs.filter(d=>query.terms.every(t=>S.metadataMatch(d,t)||(Array.from(t).length>1&&bodies.get(d.record.id).includes(t)))).map(d=>d.record.id).sort();
  const found=[];let first=await search({q});found.push(...first.records.map(r=>r.id));for(let page=2;page<=first.pages;page++){const next=await search({q,page});found.push(...next.records.map(r=>r.id));}
  assert.deepEqual(found.sort(),expected,q+' differs from exhaustive full-body scan');report.exhaustiveBodyCases.push({q,count:expected.length});
 }
 for(const q of ['光明電気鉄道','中泉 軌道','磐田の郷土史の出典を残す3手順']){const runs=[];for(let i=0;i<10;i++)runs.push((await search({q})).ms);runs.sort((a,b)=>a-b);report.validation.push({warm:q,p95Ms:Math.ceil(runs[9])});}
 assert.equal(S.normalize('ﾌｸﾃﾞ'),'ふくで');assert.equal(S.normalize('カ\u3099'),'が');assert.throws(()=>S.validate({q:'あ'.repeat(81)},[],[]));assert.throws(()=>S.validate({q:'a b c d e f g h i'},[],[]));
 const invalid=await search({q:'<script>alert(1)</script>',district:'bad',theme:'bad',page:'99999999999999999',sort:'bad'});assert.equal(invalid.total,0);assert.equal(invalid.query.page,1);assert.equal(invalid.query.district,'');
 const empty=await search({q:'  ',page:999999});assert.equal(empty.total,docs.length);assert.equal(empty.query.page,Math.ceil(docs.length/20));
 const one=await search({q:'土'});assert.ok(one.records.every(r=>S.metadataMatch(docs.find(d=>d.record.id===r.id),'土')));
 report.validation.push('NFKC/kana/combining mark; limit81/9terms; invalid filters/sort/page; XSS-like input; empty/clamped page; 1char restriction');
 report.cold=[];
 for(const q of ['光明電気鉄道','中泉 軌道','磐田の郷土史の出典を残す3手順','磐田の郷土史の出典を残す','福田','ふくで','福田半香','f001']) {
  resetWorker();const result=await search({q});assert.equal(result.type,'results');report.cold.push({q,total:result.total,ms:Math.round(result.ms),transferGzipBytes:result.transferGzipBytes,requests:result.requests});
 }
 report.failures=[];
 for(const mode of ['http','json','schema','mixed','timeout','offline']){
  failMode=mode;resetWorker();const failed=await search({q:'中泉 軌道'});assert.equal(failed.type,'error',mode);failMode='';resetWorker();const retry=await search({q:'中泉 軌道'});assert.equal(retry.type,'results');report.failures.push({mode,errorInsteadOfZero:true,retryPassed:true});
 }
 fs.writeFileSync(process.env.IWATA_SEARCH_REPORT || path.resolve(root,'../search-test-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({count:report.count,exactTitle:report.exactTitle,exactId:report.exactId,referenceQueries:report.cases.length,exhaustiveQueries:report.exhaustiveBodyCases.length,passed:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
