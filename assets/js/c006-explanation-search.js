/* Search existing explanatory text separately from the134 dictionary entries. */
(function(root){
  'use strict';
  function normalize(s){return (s||'').normalize('NFKC').toLowerCase().replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-0x60)).replace(/[〜～~ー－\-・、。，．,.!?！？「」『』（）()\s]/gu,'');}
  function findSections(sections,query){
    const terms=query.split(/[\s　]+/u).map(normalize).filter(t=>t&&!['遠州弁','方言','意味','例文'].includes(t));
    if(!terms.length)return [];
    return sections.map((s,i)=>{
      const title=normalize(s.title),text=normalize(s.text);
      if(!terms.every(t=>t.length===1?(title.includes(t)||(s.shortForms||[]).includes(t)):text.includes(t)))return null;
      const score=terms.reduce((n,t)=>n+(title===t?100:title.includes(t)?50:10),0);
      return {section:s,score,index:i};
    }).filter(Boolean).sort((a,b)=>b.score-a.score||a.index-b.index).map(x=>x.section);
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={normalize,findSections};
  if(!root.document)return;
  const document=root.document,box=document.getElementById('explanation-results');
  const sections=Array.from(document.querySelectorAll('#panel-grammar [data-explanation-search],#panel-more [data-explanation-search]')).map(el=>{
    const copy=el.cloneNode(true);copy.querySelectorAll('a[href="#search"],button,svg').forEach(n=>n.remove());
    const title=el.querySelector('h2,.gh2,p>strong').textContent.trim();
    const shortForms=[...copy.textContent.matchAll(/「([^」]+)」/g)].flatMap(m=>m[1].split(/[・／/、]/)).concat(Array.from(copy.querySelectorAll('td,dt')).map(n=>n.textContent)).map(normalize).filter(t=>t.length===1);
    return {id:el.dataset.explanationSearch,title,text:copy.textContent,shortForms,panel:el.closest('.panel').id==='panel-grammar'?'文法と語法':'もっと知る'};
  });
  function render(query){
    box.replaceChildren();
    const miren=document.getElementById('explanation-match');
    const matches=findSections(sections,query).filter(s=>s.id!=='negative-possibility'||miren.hidden);
    box.hidden=!matches.length;if(!matches.length)return;
    const heading=document.createElement('strong');heading.textContent='文法・解説で見つかりました';box.appendChild(heading);
    const note=document.createElement('p');note.textContent='本文中の文字が一致する既存の解説です。';box.appendChild(note);
    const list=document.createElement('ul');
    matches.forEach(s=>{const li=document.createElement('li'),a=document.createElement('a');a.href='#'+s.id;a.textContent=s.title+'（'+s.panel+'）';
      a.addEventListener('click',event=>{event.preventDefault();root.history.pushState(null,'','#'+s.id);root.openHash();});
      li.appendChild(a);list.appendChild(li);});box.appendChild(list);
  }
  root.c006ExplanationSearch={render};render(document.getElementById('search').value);
})(typeof window==='undefined'?{}:window);
