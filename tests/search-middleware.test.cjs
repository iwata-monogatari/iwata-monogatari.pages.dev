const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
let hooks, beforeCount=0, dbReads=0, innerValues=[], anchorPolicy;
global.HTMLRewriter=class{constructor(){hooks=new Map()}on(selector,hook){hooks.set(selector,hook);return this;}transform(response){return response;}};
(async()=>{
 const source=fs.readFileSync(path.join(root,'functions/_middleware.js'),'utf8');const {onRequest}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
 async function request(route,type='text/html',host='iwata-monogatari.net'){
  beforeCount=0;dbReads=0;innerValues=[];anchorPolicy=null;
  const context={request:new Request('https://'+host+route),next:async()=>new Response('original',{headers:{'Content-Type':type}}),env:{ASSETS:{fetch:async()=>new Response('<a href="/c019">partial</a>')},DB:{prepare:sql=>{assert.match(sql,/^SELECT html FROM site_fragments/);dbReads++;return {bind:()=>({first:async()=>({html:'<a href="https://example.org/?utm_source=iwata">public footer</a>'})})};}}}};
  const response=await onRequest(context);if(hooks)for(const selector of ['header.gh-site','section.article-policy[data-common]','footer.im-foot','a'])hooks.get(selector)?.element({before:()=>beforeCount++,setInnerContent:value=>innerValues.push(value),setAttribute:(name,value)=>{anchorPolicy={name,value}}});hooks=null;return response;
 }
 for(const route of ['/search/','/search/help/','/search/catalog/2/']){const response=await request(route);assert.equal(response.headers.get('Referrer-Policy'),'origin');assert.equal(beforeCount,0);assert.equal(dbReads,1);assert.ok(innerValues[0].includes('referrerpolicy="origin"'));assert.ok(innerValues[2].includes('referrerpolicy="origin"'));assert.deepEqual(anchorPolicy,{name:'referrerpolicy',value:'origin'});}
 assert.equal((await request('/?q=private-test')).headers.get('Referrer-Policy'),'origin');
 assert.equal((await request('/search/')).headers.get('X-Robots-Tag'),'noindex');
 assert.equal((await request('/data/search/manifest.json','application/json')).headers.get('Cache-Control'),'no-store');
 assert.match((await request('/data/search/bodies/abcd.json','application/json')).headers.get('Cache-Control'),/immutable/);
 assert.equal((await request('/assets/js/search-worker.js','text/javascript')).headers.get('Cache-Control'),'no-cache');
 const article=await request('/c056');assert.equal(beforeCount,1);assert.equal(article.headers.get('Referrer-Policy'),'same-origin');
 assert.equal((await request('/','text/html','abc.iwata-monogatari.pages.dev')).headers.get('X-Robots-Tag'),'noindex');
 const redirect=await request('/c056','text/html','iwata-monogatari.pages.dev');assert.equal(redirect.status,301);assert.equal(redirect.headers.get('Location'),'https://iwata-monogatari.net/c056');
 console.log('Middleware passed: query referrer suppression, manifest/hashed/UI cache, no search reactions, existing D1 footer SELECT and article behavior, preview noindex/domain redirect. No DB writes.');
})().catch(error=>{console.error(error);process.exitCode=1});
