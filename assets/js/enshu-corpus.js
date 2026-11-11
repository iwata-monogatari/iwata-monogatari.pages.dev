(() => {
 'use strict';
 const input=document.getElementById('corpus-search'),village=document.getElementById('corpus-village'),page=document.getElementById('corpus-page'),status=document.getElementById('corpus-status');
 const rows=[...document.querySelectorAll('.record')],chapters=[...document.querySelectorAll('.source-chapter')];
 const normalize=s=>s.normalize('NFKC').replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-96)).toLowerCase();
 const texts=new Map(rows.map(e=>[e,normalize(e.dataset.search+' '+e.dataset.village)]));
 function render(sync=false){
  const terms=normalize(input.value.trim()).split(/\s+/).filter(Boolean);let n=0;
  rows.forEach(e=>{const show=terms.every(t=>texts.get(e).includes(t))&&(!village.value||e.dataset.village===village.value)&&(!page.value||e.dataset.page===page.value);e.hidden=!show;if(show)n++;});
  chapters.forEach(c=>{c.hidden=![...c.querySelectorAll('.record')].some(e=>!e.hidden);});
  status.textContent=n?`${n}記録を表示（全${rows.length}記録）`:'一致する記録はありません。別の表記や意味で探すか、条件をクリアしてください。';
  if(sync){const url=new URL(location.href);[['q',input.value.trim()],['v',village.value],['p',page.value]].forEach(([key,value])=>value?url.searchParams.set(key,value):url.searchParams.delete(key));history.replaceState(null,'',url.pathname+url.search+url.hash);}
 }
 input.addEventListener('input',()=>render(true));village.addEventListener('change',()=>render(true));page.addEventListener('change',()=>render(true));
 document.getElementById('corpus-clear').onclick=()=>{input.value='';village.value='';page.value='';history.replaceState(null,'',location.pathname);render();input.focus();};
 function anchor(){let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}const target=id&&document.getElementById(id);if(!target)return;
  if(target.hidden||target.closest('[hidden]')){input.value='';village.value='';page.value='';render(true);}
  (document.fonts?document.fonts.ready:Promise.resolve()).then(()=>requestAnimationFrame(()=>target.scrollIntoView({block:'start'})));
 }
 const params=new URLSearchParams(location.search);input.value=params.get('q')||'';
 for(const [select,key] of [[village,'v'],[page,'p']])if([...select.options].some(o=>o.value===params.get(key)))select.value=params.get(key);
 render();anchor();window.addEventListener('hashchange',anchor);
})();
