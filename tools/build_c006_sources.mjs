// c172の資料表はJSONから生成する。本文の解説はc172.htmlで編集する。
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {escapeHtml as esc} from './build_c006_dictionary.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'data',name),'utf8'));
const fpjd=read('c006-fpjd.json'),gunshi=read('c006-gunshi1921.json'),dictionary=read('c006-dictionary.json');
const words=new Map(dictionary.entries.map(e=>[e.id,e.w]));
if(fpjd.records.length!==287 || new Set(fpjd.records.map(r=>r.question)).size!==211 || new Set(fpjd.records.map(r=>r.point)).size!==1)throw Error('FPJDの件数・質問数・地点数が変わっています');
if(new Set(fpjd.records.map(r=>r.id)).size!==287)throw Error('FPJD data-IDが重複しています');
const table=(head,rows,id='')=>`<div class="table-wrap"><table${id?` id="${id}"`:''} class="source-table"><thead><tr>${head.map(t=>`<th scope="col">${t}</th>`).join('')}</tr></thead><tbody>${rows.join('\n')}</tbody></table></div>`;
const g=table(['本文頁','原表記・意味の抄録','1921年の記録地','比較上の注意・辞典'],gunshi.records.map(r=>{
 if(!words.has(r.word_id)||r.page<1242||r.page>1254||!r.village)throw Error('郡誌レコードが不正');
 return `<tr id="${esc(r.id)}"><th scope="row"><a href="https://dl.ndl.go.jp/pid/965680/1/${r.frame}">${r.page}頁</a></th><td><strong>${esc(r.form)}</strong><br>${esc(r.meaning)}</td><td>${esc(r.village)}</td><td>${esc(r.note)} <a href="/c006#${r.word_id}">辞典「${esc(words.get(r.word_id))}」</a></td></tr>`;
}));
const f=table(['data-ID・質問番号','質問項目','回答語形','原注記','NLJ地図'],fpjd.records.map(r=>`<tr id="fpjd-${r.id}"><th scope="row"><a href="#fpjd-${r.id}">${r.id}</a><br>${esc(r.question)}${r.answer_number?`（回答${esc(r.answer_number)}）`:''}</th><td>${esc(r.item)}</td><td>${esc(r.form)}</td><td>${esc(r.note)}${Object.keys(r.corrections).length?`<details><summary>原データの修正欄</summary>${Object.entries(r.corrections).map(([k,v])=>`${esc(k)}：${esc(v)}`).join('<br>')}</details>`:''}</td><td>${esc(r.map_number)}${r.map_heading?`<br>${esc(r.map_heading)}`:''}</td></tr>`),'fpjd-table');
const images='<div class="scan-grid">'+Array.from({length:7},(_,i)=>`<figure><a href="https://dl.ndl.go.jp/pid/965680/1/${740+i}"><img src="/assets/img/kotoba/gunshi-${740+i}.webp" width="1200" height="853" loading="lazy" decoding="async" alt="磐田郡誌${1242+i*2}〜${1243+i*2}頁の原画像"></a><figcaption>${1242+i*2}〜${1243+i*2}頁（国会図書館${740+i}コマ）${i===6?'。方言節は1254頁で終わる。':''}</figcaption></figure>`).join('')+'</div>';
const target=path.join(root,'c172.html');let html=fs.readFileSync(target,'utf8');
for(const [name,body]of [['gunshi-records',g],['fpjd-records',f],['gunshi-images',images]]){
 const start=`<!-- ${name}:start -->`,end=`<!-- ${name}:end -->`;
 if(html.split(start).length!==2||html.split(end).length!==2)throw Error('資料表マーカー不正');
 const a=html.indexOf(start)+start.length,b=html.indexOf(end);html=html.slice(0,a)+'\n'+body+'\n'+html.slice(b);
}
if(process.argv.includes('--check')){if(html!==fs.readFileSync(target,'utf8'))throw Error('c172資料表の再生成が必要');}
else fs.writeFileSync(target,html,'utf8');
console.log(`c172 sources: ${gunshi.records.length} excerpts, ${fpjd.records.length} responses`);
