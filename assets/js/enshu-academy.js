(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
  const shuffled=list=>{const a=[...list];for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
  let data,round=[],position=0,score=0,answered=false,reverse=false,missed=[],cards=[],cardIndex=0;
  const sourceLabel=e=>e.historical?`1921年 / ${e.historical.village} / ${e.historical.page}頁・原表記`:'';
  const sourceHref=e=>e.historical?'/enshu/records/#'+e.id:'/c006?q='+encodeURIComponent(e.w)+'#'+e.id;
  function dictionary(e){const a=node('a',e.historical?'記録・原画像を読む →':'3作例・資料を辞典で読む →');a.href=sourceHref(e);return a;}
  const brief=e=>e.m.split('。')[0]+'。';
  let lastPool=[],lastLimit=5,reviewing=false,activeCourse='kitchen',allCourses=false;
  function quizPool(){
    if(!data)return[];const scene=data.scenes.find(s=>s.id===$('quiz-scene').value),ids=scene&&new Set(scene.words),cat=$('quiz-category').value;
    const scope=$('quiz-source').value;
    return data.entries.filter(e=>(!ids||ids.has(e.id))&&(cat==='all'||e.cat===cat)&&(scope==='all'||(scope==='historical'?!!e.historical:!e.historical)));
  }
  function updateQuizSetup(){
    const n=Math.min(Number($('quiz-length').value),quizPool().length);$('quiz-start').disabled=!n;
    $('quiz-start').textContent=n?`${n}問ではじめる`:'条件を選び直す';
    $('quiz-setup-status').textContent=n?'同じ語は、一回の練習に一度だけ。':'該当する語がありません。場面か分類を広げてください。';
  }
  function progress(){
    $('quiz-progress').textContent=`${position+1} / ${round.length}問 ・ 正解 ${score}問`;
    $('quiz-meter').max=round.length;$('quiz-meter').value=position+(answered?1:0);
  }
  function focusQuestion(){ $('quiz-question').focus({preventScroll:true});$('quiz-board').scrollIntoView({block:'start'}); }
  function question(){
    answered=false;const e=round[position];progress();
    $('quiz-mode-label').textContent=(reviewing?'振り返り / ':'')+(e.historical?sourceLabel(e):(reverse?'意味から、ことばを選ぶ':'ことばから、意味を選ぶ'));
    const context=e.historical?`1921年の${e.historical.village}の記録では`:'この辞典では';
    $('quiz-question').textContent=reverse?`「${brief(e)}」${context}、どのことば？`:`「${e.w}」${context}、どんな意味？`;
    const hasPicture=!reverse&&!e.historical;
    $('quiz-question-picture').hidden=!hasPicture;$('quiz-question-picture').parentElement.classList.toggle('no-picture',!hasPicture);
    if(hasPicture){$('quiz-question-image').src='/assets/karuta/c006/'+e.id+'-300.webp';$('quiz-question-image').alt=e.w+'の作例を描いた創作絵札';}
    $('quiz-hint').hidden=true;$('quiz-hint').textContent='';$('quiz-hint-button').disabled=false;$('quiz-hint-button').textContent='ヒントを読む';$('quiz-hint-button').setAttribute('aria-expanded','false');
    const answer=reverse?e.w:brief(e),pool=data.entries.filter(x=>x.id!==e.id&&x.cat!==e.cat&&brief(x)!==brief(e));
    const choices=shuffled([answer,...shuffled([...new Set(pool.map(x=>reverse?x.w:brief(x)))]).slice(0,3)]);
    $('quiz-options').replaceChildren();$('quiz-feedback').replaceChildren();$('quiz-feedback').hidden=true;$('quiz-next').hidden=true;
    choices.forEach(text=>{const b=node('button',text);b.type='button';b.dataset.answer=String(text===answer);b.onclick=()=>{
      if(answered)return;answered=true;const correct=text===answer;if(correct)score++;else missed.push(e);
      for(const option of $('quiz-options').children){option.disabled=true;if(option.dataset.answer==='true'){option.classList.add('correct');option.textContent='✓ '+option.textContent;}}
      if(!correct){b.classList.add('incorrect');b.textContent='もう一度：'+b.textContent;}
      progress();const feedback=$('quiz-feedback'),card=node('div','');card.className='quiz-answer'+(reverse&&!e.historical?'':' without-picture');
      if(reverse&&!e.historical){const image=document.createElement('img');image.src='/assets/karuta/c006/'+e.id+'-300.webp';image.alt=e.w+'の作例を描いた創作絵札';image.width=90;image.height=120;card.append(image);}
      const copy=node('div','');const prompt=e.historical?(correct?'正解。資料語の作例でも確かめましょう。':'資料に記録された意味を、作例で確かめましょう。'):(correct?'正解。会話でも確かめましょう。':'この辞典の答えを、会話で確かめましょう。');copy.append(node('strong',prompt),node('h4',e.w),node('p',e.m));
      if(e.historical)copy.append(node('p',sourceLabel(e)+'。以下は意味をつかむ編集部の置換作例で、当時の発話の引用ではありません。'));
      const pair=node('blockquote',e.ex);pair.append(node('small','標準語：'+e.std));copy.append(pair,node('p',e.learning.point),dictionary(e));card.append(copy);feedback.append(card);feedback.hidden=false;
      $('quiz-next').hidden=false;$('quiz-next').textContent=position+1===round.length?'ひと回りのまとめを見る →':'次の問題へ →';
      feedback.scrollIntoView({block:'nearest'});
    };$('quiz-options').append(b);});
  }
  function beginQuiz(pool=quizPool(),limit=Number($('quiz-length').value),review=false,direction=$('quiz-direction').value==='word'){
    if(!data||!pool.length)return;lastPool=[...pool];lastLimit=limit;round=shuffled(pool).slice(0,limit);position=0;score=0;missed=[];reverse=direction;reviewing=review;
    $('quiz-summary').replaceChildren();$('quiz-board').hidden=false;question();focusQuestion();
  }
  function results(){
    $('quiz-board').hidden=true;const summary=$('quiz-summary');summary.replaceChildren();
    const title=node('h3',`${round.length}問をひと回り。`);title.tabIndex=-1;summary.append(title,node('p',`正解 ${score} / ${round.length}問。気になったことばを、絵札や資料でもう一度。`));
    const list=node('ul','');list.className='quiz-word-review';const wrongIds=new Set(missed.map(e=>e.id));
    for(const e of round){const li=node('li',''),a=node('a','');a.href='/enshu/?word='+e.id+'#cards';a.dataset.exploreWord=e.id;a.append(node('span',wrongIds.has(e.id)?'↻ もう一度':'✓ 確かめた'),node('strong',e.w),node('small',brief(e)));li.append(a);list.append(li);}summary.append(list);
    const controls=node('div','');controls.className='quiz-result-actions';const retryEntries=[...missed],samePool=[...lastPool],limit=lastLimit,direction=reverse;
    if(retryEntries.length){const retry=node('button',`間違えた${retryEntries.length}語だけ、もう一度`);retry.type='button';retry.onclick=()=>beginQuiz(retryEntries,retryEntries.length,true,direction);controls.append(retry);}
    const again=node('button','同じ範囲でもうひと回り');again.type='button';again.onclick=()=>beginQuiz(samePool,limit,false,direction);controls.append(again);
    const other=node('a','別の場面を選ぶ ↑');other.href='#courses';controls.append(other);summary.append(controls);title.focus({preventScroll:true});summary.scrollIntoView({block:'start'});
  }
  $('quiz-start').onclick=()=>beginQuiz();
  $('quiz-next').onclick=()=>{if(!answered)return;position++;if(position<round.length){question();focusQuestion();}else results();};
  $('quiz-hint-button').onclick=()=>{if(!round.length)return;const e=round[position];$('quiz-hint').textContent=reverse?`${e.cat}のことば。はじめの字は「${Array.from(e.w)[0]}」です。`:'標準語の会話なら：'+e.learning.examples[0].standard;$('quiz-hint').hidden=false;$('quiz-hint-button').disabled=true;$('quiz-hint-button').textContent='ヒント表示中';$('quiz-hint-button').setAttribute('aria-expanded','true');};
  function showCourse(id,showAll=false){
    const scene=data.scenes.find(s=>s.id===id);if(!scene)return;activeCourse=id;allCourses=showAll;
    document.querySelectorAll('#course-lessons .scene').forEach(s=>s.hidden=!showAll&&s.dataset.scene!==id);
    document.querySelectorAll('.study-courses [data-course]').forEach(a=>{if(a.dataset.course===id)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});
    $('course-status').textContent=showAll?'12コースをまとめて表示しています。':`選択中：${scene.title} ・ ${scene.words.length}語`;
    $('courses-show-all').textContent=showAll?'選んだコースだけ読む':'全コースをまとめて読む';$('courses-show-all').setAttribute('aria-expanded',String(showAll));
  }
  function setupStudy(){
    const hash=location.hash.slice(1),initial=data.scenes.find(s=>'scene-'+s.id===hash);showCourse(initial?initial.id:data.scenes[0].id);
    $('courses-show-all').disabled=false;$('courses-show-all').onclick=()=>showCourse(activeCourse,!allCourses);
    for(const id of ['quiz-scene','quiz-length','quiz-direction','quiz-category','quiz-source'])$(id).onchange=updateQuizSetup;
    window.addEventListener('hashchange',()=>{const scene=data.scenes.find(s=>'#scene-'+s.id===location.hash);if(scene){showCourse(scene.id);requestAnimationFrame(()=>document.getElementById('scene-'+scene.id).scrollIntoView({block:'start'}));}});
    document.querySelector('.academy').addEventListener('click',event=>{
      if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||event.button!==0)return;const link=event.target.closest('a');if(!link)return;
      if(link.dataset.course){showCourse(link.dataset.course);return;}
      if(link.dataset.quizScene){event.preventDefault();$('quiz-scene').value=link.dataset.quizScene;$('quiz-category').value='all';$('quiz-source').value=link.dataset.quizSource||'all';$('quiz-length').value='3';updateQuizSetup();history.replaceState(null,'',location.pathname+location.search+'#practice');beginQuiz();return;}
      if(link.dataset.exploreWord&&data.entries.some(e=>e.id===link.dataset.exploreWord)){event.preventDefault();$('flash-scene').value='all';deck('all',link.dataset.exploreWord);flash(true);focusWord();}
    });
    const target=location.hash&&document.getElementById(location.hash.slice(1));if(target)requestAnimationFrame(()=>target.scrollIntoView({block:'start'}));
  }
  let exampleIndex=0;
  const starterButtons=[...document.querySelectorAll('.word-starter')];
  const explorerControls=['flash-prev','flash-random','flash-next','flash-scene','flash-example-next','flash-copy'];
  function example(){
    const e=cards[cardIndex],pairs=[{dialect:e.ex,standard:e.std},...e.learning.examples],pair=pairs[exampleIndex];
    $('flash-example-count').textContent=`${e.historical?'意味をつかむ置換作例':'会話の作例'} ${exampleIndex+1} / ${pairs.length}`;
    $('flash-example').textContent=pair.dialect;$('flash-standard').textContent=pair.standard;
  }
  function flash(interacted=false){
    const e=cards[cardIndex];if(!e)return;exampleIndex=0;
    const scenes=data.scenes.filter(s=>s.words.includes(e.id));
    const scene=scenes.find(s=>s.id===$('flash-scene').value)||scenes[0];
    const image=$('flash-image');$('flash-card').classList.toggle('is-historical',!!e.historical);
    if(e.historical){image.removeAttribute('srcset');image.src='/assets/img/kotoba/gunshi-'+e.historical.frame+'.webp';image.width=1200;image.height=853;image.alt=`磐田郡誌${e.historical.page}頁を含む原画像。国立国会図書館デジタルコレクション`;$('flash-caption').textContent='郡誌原画像 / 国立国会図書館';}
    else{image.src='/assets/karuta/c006/'+e.id+'-900.webp';image.srcset=`/assets/karuta/c006/${e.id}-300.webp 300w, /assets/karuta/c006/${e.id}-900.webp 900w`;image.width=900;image.height=1200;image.alt=e.w+'の作例を描いた創作絵札';$('flash-caption').textContent='生成AIによる創作画';}
    $('flash-source-label').textContent=sourceLabel(e);$('flash-source-label').hidden=!e.historical;
    $('flash-editorial').textContent=e.historical?'原表記を用いた編集部の置換作例です。当時の会話や現代の使用を再現したものではありません。':'例文は掲載した意味に基づく編集部の作例です。';
    $('flash-word').textContent=e.w;$('flash-meaning').textContent=e.m;$('flash-point').textContent=e.learning.point;
    $('flash-scene-label').textContent=scene?scene.title:e.cat;
    $('flash-progress').textContent=`${cardIndex+1} / ${cards.length}語`;
    $('flash-dictionary').href=sourceHref(e);$('flash-dictionary').textContent=e.historical?'記録・原画像を読む →':'使い分け・出典を読む →';
    $('flash-course').href=scene?'#scene-'+scene.id:'#courses';
    $('flash-course').textContent=scene?'この場面のことばを読む →':'12コースから読む →';
    starterButtons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.word===e.id)));
    $('flash-message').textContent='';$('flash-share-fallback').hidden=true;example();
    if(interacted){const url=new URL(location.href);url.searchParams.set('word',e.id);url.hash='cards';history.replaceState(null,'',url.pathname+url.search+url.hash);}
  }
  function deck(sceneId,preferred){
    const scene=data.scenes.find(s=>s.id===sceneId),pool=scene?scene.words.map(id=>data.entries.find(e=>e.id===id)):data.entries.filter(e=>sceneId==='historical'?!!e.historical:sceneId==='dictionary'?!e.historical:true);
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
  fetch('/data/enshu-learning.json?v=20261112-more').then(r=>{if(!r.ok)throw Error('data');return r.json();}).then(d=>{
    data=d;const requested=new URLSearchParams(location.search).get('word');deck('all',d.entries.some(e=>e.id===requested)?requested:'ponpon');flash();
    setupStudy();$('quiz-start').disabled=false;updateQuizSetup();explorerControls.forEach(id=>$(id).disabled=false);starterButtons.forEach(b=>b.disabled=false);
  }).catch(()=>{$('quiz-summary').textContent='練習データを読み込めませんでした。場面別コースと辞典から引き続き学べます。';$('flash-message').textContent='ほかの絵札を読み込めませんでした。表示中の一語と、場面別コース・辞典はそのまま読めます。';});
})();
