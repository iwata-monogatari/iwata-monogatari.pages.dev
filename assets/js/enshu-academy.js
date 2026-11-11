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
  function flash(){const e=cards[cardIndex];const image=document.createElement('img');image.src='/assets/karuta/c006/'+e.id+'-300.webp';image.alt=e.w+'の作例を描いた創作絵札';image.width=300;image.height=400;
    const figure=document.createElement('figure');figure.append(image,node('figcaption','生成AIによる創作画'));const answer=node('div','');answer.id='flash-answer';answer.hidden=true;answer.append(node('p',e.m),node('p',e.learning.examples[0].dialect),node('p','標準語：'+e.learning.examples[0].standard),node('p',e.learning.point),dictionary(e));
    $('flash-card').replaceChildren(node('p',`${cardIndex+1} / ${cards.length}枚`),node('h3',e.w),figure,answer);$('flash-reveal').textContent='意味を見る';$('flash-reveal').setAttribute('aria-expanded','false');
  }
  $('flash-reveal').onclick=()=>{const a=$('flash-answer');if(!a)return;a.hidden=!a.hidden;$('flash-reveal').textContent=a.hidden?'意味を見る':'意味を隠す';$('flash-reveal').setAttribute('aria-expanded',String(!a.hidden));};
  $('flash-next').onclick=()=>{if(!cards.length)return;cardIndex=(cardIndex+1)%cards.length;flash();};
  $('quiz-start').disabled=true;$('flash-next').disabled=true;$('flash-reveal').disabled=true;
  fetch('/data/enshu-learning.json').then(r=>{if(!r.ok)throw Error('data');return r.json();}).then(d=>{
    data=d;cards=shuffled(d.entries);flash();$('quiz-start').disabled=false;$('flash-next').disabled=false;$('flash-reveal').disabled=false;
  }).catch(()=>{$('quiz-summary').textContent='練習データを読み込めませんでした。場面別コースと辞典から引き続き学べます。';});
})();
