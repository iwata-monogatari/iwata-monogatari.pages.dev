/* Input stays in this tab. Only the public dictionary is fetched. */
(() => {
  const input = document.getElementById('in');
  const output = document.getElementById('out');
  const status = document.getElementById('conversion-status');
  const matches = document.getElementById('word-matches');
  const matchedWords = document.getElementById('matched-words');
  const samples = document.getElementById('samples');
  let direction = 's2e', mode = 'futsu', dictionary = [], dictionaryFailed = false;
  let copyTimer;
  const presets = [
    {id:'chatto',group:'買い物・外出',s2e:'急いで買ってくるよ。',e2s:'ちゃっと買ってくるに。'},
    {id:'road',group:'買い物・外出',s2e:'車が来るから道の端に寄りなさい。',e2s:'道のくろに寄って。'},
    {id:'jurui',group:'天気・道',s2e:'雨で道がぬかるんでいる。',e2s:'雨で道がじゅるい。'},
    {id:'rain',group:'天気・道',s2e:'今日は雨だから、出かけるのはやめよう。',e2s:'今日は雨だもんで、出かけるのはやめよう。'},
    {id:'rest',group:'家での会話',s2e:'今日は疲れたから、もう休むよ。',e2s:'今日はえらい。はあ休む。'},
    {id:'hair',group:'家での会話',s2e:'前髪がうっとうしい。',e2s:'前髪がやぶせったい。'},
    {id:'invite',group:'誘う・確かめる',s2e:'明日、一緒にやってみよう。',e2s:'明日、一緒にしまい。'},
    {id:'dara',group:'誘う・確かめる',s2e:'明日は雨でしょう。',e2s:'明日は雨だら。'}
  ];
  function addText(parent, tag, text, className) {
    const el = document.createElement(tag); el.textContent = text;
    if (className) el.className = className;
    parent.appendChild(el); return el;
  }
  function addLink(parent, title, href) {const a=addText(parent,'a',title);a.href=href;}
  function normalize(text) {return text.normalize('NFKC').replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-96));}
  function showWords() {
    matchedWords.replaceChildren();
    const text = normalize(direction === 's2e' ? output.value : input.value);
    if (!text.trim()) {matches.hidden=true;return;}
    matches.hidden=false;
    // These are lookup candidates, not claims that every match was a replacement.
    const found = dictionary.filter(e=>{
      if (e.w.length < 2) return false;
      const aliases = e.id==='jurui' ? ['じゅるい','じゅるく','じゅるかった'] : [normalize(e.w)];
      if (['dara','zura','dani'].includes(e.id)) return new RegExp(normalize(e.w)+'(?:か)?(?=$|[。、！？!?\\s）」])').test(text) && !(e.id==='zura'&&/いたずら/.test(text));
      return aliases.some(word=>text.includes(word));
    }).sort((a,b)=>b.w.length-a.w.length).slice(0,6);
    for (const e of found) {
      const card=document.createElement('div');card.className='matched-word';
      addText(card,'strong',e.w);addText(card,'p',e.m);
      if (e.id==='jurui') addText(card,'p','逆変換は道の「ぬかるみ」を想定します。食べ物なら汁気の意味で読み替えてください。');
      addLink(card,'辞典の作例・出典 →','/c006?q='+encodeURIComponent(e.w)+'#'+encodeURIComponent(e.id));
      if (['chatto','jurui'].includes(e.id)) addLink(card,'詳しい意味と使い方 →','/enshu-'+e.id);
      if (['dara','zura','ra'].includes(e.id)) addLink(card,'語尾を記録から読む →','/c173');
      matchedWords.appendChild(card);
    }
    if (!found.length) addText(matchedWords,'p',dictionaryFailed?'語句解説を読み込めませんでした。辞典へ直接進めます。':dictionary.length?'一致する語の解説は見つかりませんでした。標準語や意味から辞典でも探せます。':'語句解説を読み込んでいます。');
    addLink(matchedWords,'134語の辞典で調べる','/c006');
  }
  function convert() {
    document.getElementById('copied').classList.remove('show');
    if (!input.value.trim()) {output.value='';status.textContent='一文を入力するか、下の例文を選んでください。';showWords();return;}
    output.value=direction==='s2e'?s2e(input.value,mode):e2s(input.value);
    status.textContent=output.value===input.value?'変換できる語句は見つかりませんでした。入力文をそのまま表示しています。':'変換しました。文脈で意味が変わるため、語句の解説も確かめてください。';
    showWords();
  }
  function renderSamples() {
    samples.replaceChildren();let currentGroup='',container;
    for (const p of presets) {
      if (p.group!==currentGroup) {currentGroup=p.group;container=document.createElement('div');container.className='sample-group';addText(container,'strong',currentGroup);samples.appendChild(container);}
      const b=addText(container,'button',p[direction],'samp');b.type='button';
      b.addEventListener('click',()=>{input.value=p[direction];convert();});
    }
  }
  function setDirection(value) {
    direction=value;
    document.querySelectorAll('#dir button').forEach(b=>{const on=b.dataset.dir===direction;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
    document.getElementById('inLabel').textContent=direction==='s2e'?'標準語を入力':'遠州弁を入力';
    document.getElementById('outLabel').textContent=direction==='s2e'?'遠州弁':'標準語';
    input.placeholder=direction==='s2e'?'例：急いで買ってくるよ。':'例：ちゃっと買ってくるに。';
    document.getElementById('modeWrap').hidden=direction==='e2s';
    renderSamples();convert();
  }
  document.querySelectorAll('#dir button').forEach(b=>b.addEventListener('click',()=>setDirection(b.dataset.dir)));
  document.querySelectorAll('#modes button').forEach(b=>b.addEventListener('click',()=>{
    mode=b.dataset.mode;
    document.querySelectorAll('#modes button').forEach(x=>{const on=x===b;x.classList.toggle('active',on);x.setAttribute('aria-pressed',String(on));});convert();
  }));
  document.getElementById('go').addEventListener('click',convert);
  input.addEventListener('input',convert);
  document.getElementById('clear').addEventListener('click',()=>{input.value='';convert();input.focus();});
  document.getElementById('swap').addEventListener('click',()=>{input.value=output.value;setDirection(direction==='s2e'?'e2s':'s2e');});
  document.getElementById('copy').addEventListener('click',async()=>{
    const copied=document.getElementById('copied');clearTimeout(copyTimer);
    if (!output.value) {copied.textContent='先に文章を変換してください。';copied.classList.add('show');return;}
    try {await navigator.clipboard.writeText(output.value);copied.textContent='コピーしました。';}
    catch {copied.textContent='コピーできませんでした。結果欄を選択してコピーしてください。';output.focus();output.select();}
    copied.classList.add('show');copyTimer=setTimeout(()=>copied.classList.remove('show'),4000);
  });
  renderSamples();
  const example=new URLSearchParams(location.search).get('example');
  const preset=presets.find(p=>p.id===example);
  if (preset) {input.value=preset.s2e;convert();}
  fetch('/data/c006-dictionary.json').then(r=>{if(!r.ok)throw new Error('dictionary');return r.json();}).then(data=>{dictionary=Array.isArray(data.entries)?data.entries:[];showWords();}).catch(()=>{dictionaryFailed=true;showWords();});
})();
