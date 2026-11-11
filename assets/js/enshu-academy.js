(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
  const shuffled=list=>{const a=[...list];for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
  let data,round=[],position=0,score=0,answered=false,reverse=false,missed=[],cards=[],cardIndex=0;
  function dictionary(e){const a=node('a','3作例・資料を辞典で読む →');a.href='/c006?q='+encodeURIComponent(e.w)+'#'+e.id;return a;}
  function question(){
    answered=false;const e=round[position];$('quiz-progress').textContent=`${position+1} / ${round.length}問　正解 ${score}問`;
    $('quiz-question').textContent=reverse?`「${e.m}」を表す語は？`:`「${e.w}」の、この辞典での意味は？`;
    const answer=reverse?e.w:e.m;
    const pool=data.entries.filter(x=>x.id!==e.id&&x.cat!==e.cat&&(reverse?x.w:x.m)!==answer);
    // Distinct word/meaning options, without claiming that other dialect synonyms do not exist.
    const choices=shuffled([answer,...shuffled([...new Set(pool.map(x=>reverse?x.w:x.m))]).slice(0,3)]);
    $('quiz-options').replaceChildren();$('quiz-feedback').replaceChildren();$('quiz-next').hidden=true;
    choices.forEach(text=>{const b=node('button',text);b.onclick=()=>{
      if(answered)return;answered=true;const correct=text===answer;if(correct)score++;else missed.push(e);
      for(const option of $('quiz-options').children){option.disabled=true;if(option.textContent===answer)option.classList.add('correct');}
      b.classList.add(correct?'correct':'incorrect');
      $('quiz-feedback').append(node('strong',correct?'正解です。':'この辞典の答え：'+answer),node('p',e.learning.point),dictionary(e));
      $('quiz-next').hidden=false;$('quiz-next').textContent=position+1===round.length?'結果を見る':'次の問題へ';
    };$('quiz-options').append(b);});
  }
  $('quiz-start').onclick=()=>{
    if(!data)return;const cat=$('quiz-category').value;const pool=data.entries.filter(e=>cat==='all'||e.cat===cat);
    round=shuffled(pool).slice(0,10);position=0;score=0;missed=[];reverse=$('quiz-direction').value==='word';
    $('quiz-board').hidden=false;$('quiz-summary').replaceChildren();question();$('quiz-question').tabIndex=-1;$('quiz-question').focus();
  };
  $('quiz-next').onclick=()=>{if(!answered)return;position++;if(position<round.length){question();$('quiz-question').focus();return;}
    $('quiz-board').hidden=true;$('quiz-summary').replaceChildren(node('strong',`${round.length}問中${score}問正解。`));
    if(missed.length){$('quiz-summary').append(node('span',' 振り返る語：'));for(const e of missed){const a=dictionary(e);a.textContent=e.w+'　';$('quiz-summary').append(a);}}
    else $('quiz-summary').append(node('span',' 全問正解です。別の方向や分類でも試せます。'));
  };
  let exampleIndex=0;
  const starterButtons=[...document.querySelectorAll('.word-starter')];
  const explorerControls=['flash-prev','flash-random','flash-next','flash-scene','flash-example-next','flash-copy'];
  function example(){
    const e=cards[cardIndex],pairs=[{dialect:e.ex,standard:e.std},...e.learning.examples],pair=pairs[exampleIndex];
    $('flash-example-count').textContent=`会話の作例 ${exampleIndex+1} / ${pairs.length}`;
    $('flash-example').textContent=pair.dialect;$('flash-standard').textContent=pair.standard;
  }
  function flash(interacted=false){
    const e=cards[cardIndex];if(!e)return;exampleIndex=0;
    const scenes=data.scenes.filter(s=>s.words.includes(e.id));
    const scene=scenes.find(s=>s.id===$('flash-scene').value)||scenes[0];
    const image=$('flash-image');image.src='/assets/karuta/c006/'+e.id+'-900.webp';
    image.srcset=`/assets/karuta/c006/${e.id}-300.webp 300w, /assets/karuta/c006/${e.id}-900.webp 900w`;
    image.alt=e.w+'の作例を描いた創作絵札';
    $('flash-word').textContent=e.w;$('flash-meaning').textContent=e.m;$('flash-point').textContent=e.learning.point;
    $('flash-scene-label').textContent=scene?scene.title:e.cat;
    $('flash-progress').textContent=`${cardIndex+1} / ${cards.length}語`;
    $('flash-dictionary').href='/c006?q='+encodeURIComponent(e.w)+'#'+e.id;
    $('flash-course').href=scene?'#scene-'+scene.id:'#courses';
    $('flash-course').textContent=scene?'この場面のことばを読む →':'12コースから読む →';
    starterButtons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.word===e.id)));
    $('flash-message').textContent='';$('flash-share-fallback').hidden=true;example();
    if(interacted){const url=new URL(location.href);url.searchParams.set('word',e.id);url.hash='cards';history.replaceState(null,'',url.pathname+url.search+url.hash);}
  }
  function deck(sceneId,preferred){
    const scene=data.scenes.find(s=>s.id===sceneId),pool=scene?scene.words.map(id=>data.entries.find(e=>e.id===id)):data.entries;
    const first=pool.find(e=>e.id===preferred)||pool[0];
    cards=[first,...pool.filter(e=>e.id!==first.id)];cardIndex=0;
  }
  function focusWord(){ $('flash-word').focus({preventScroll:true});$('flash-card').scrollIntoView({block:'start'}); }
  $('flash-next').onclick=()=>{if(!cards.length)return;cardIndex=(cardIndex+1)%cards.length;flash(true);focusWord();};
  $('flash-prev').onclick=()=>{if(!cards.length)return;cardIndex=(cardIndex-1+cards.length)%cards.length;flash(true);focusWord();};
  $('flash-random').onclick=()=>{if(cards.length<2)return;cardIndex=(cardIndex+1+Math.floor(Math.random()*(cards.length-1)))%cards.length;flash(true);focusWord();};
  $('flash-example-next').onclick=()=>{if(!cards.length)return;exampleIndex=(exampleIndex+1)%(1+cards[cardIndex].learning.examples.length);example();};
  $('flash-scene').onchange=()=>{if(!data)return;deck($('flash-scene').value);flash(true);};
  starterButtons.forEach(b=>{b.onclick=()=>{if(!data)return;$('flash-scene').value='all';deck('all',b.dataset.word);flash(true);focusWord();};});
  $('flash-copy').onclick=async()=>{
    if(!cards.length)return;const url=new URL('https://iwata-monogatari.net/enshu/');url.searchParams.set('word',cards[cardIndex].id);url.hash='cards';
    try{await navigator.clipboard.writeText(url.href);$('flash-message').textContent='この一語へのリンクをコピーしました。';}
    catch{$('flash-message').textContent='コピーできませんでした。下のリンクを選択してコピーできます。';$('flash-share-url').value=url.href;$('flash-share-fallback').hidden=false;$('flash-share-url').focus();$('flash-share-url').select();}
  };
  $('quiz-start').disabled=true;explorerControls.forEach(id=>$(id).disabled=true);
  fetch('/data/enshu-learning.json').then(r=>{if(!r.ok)throw Error('data');return r.json();}).then(d=>{
    data=d;const requested=new URLSearchParams(location.search).get('word');deck('all',d.entries.some(e=>e.id===requested)?requested:'ponpon');flash();
    $('quiz-start').disabled=false;explorerControls.forEach(id=>$(id).disabled=false);starterButtons.forEach(b=>b.disabled=false);
  }).catch(()=>{$('quiz-summary').textContent='練習データを読み込めませんでした。場面別コースと辞典から引き続き学べます。';$('flash-message').textContent='ほかの絵札を読み込めませんでした。表示中の一語と、場面別コース・辞典はそのまま読めます。';});
})();
