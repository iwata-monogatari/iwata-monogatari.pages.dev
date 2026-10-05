(() => {
  'use strict';
  const form = document.getElementById('search-form');
  if (!form) return;
  const controls = { q: form.elements.q, district: form.elements.district, theme: form.elements.theme, sort: form.elements.sort };
  const heading = document.getElementById('search-results-title');
  const status = document.getElementById('search-status');
  const error = document.getElementById('search-error');
  const list = document.getElementById('search-list');
  const pager = document.getElementById('search-pagination');
  const conditions = document.getElementById('search-conditions');
  const recovery = document.getElementById('search-recovery');
  let worker, request = 0, pending = {}, composition = false, current;
  const keys = Object.keys(controls);
  const optionValid = (select, value) => [...select.options].some(o => o.value === value);
  function stateFromUrl() {
    const params = new URLSearchParams(location.search);
    return { q: params.get('q') || '', district: params.get('district') || '', theme: params.get('theme') || '', sort: params.get('sort') || 'relevance', page: params.get('page') || 1 };
  }
  function validate(state) {
    if (Array.from(state.q).length > 80) throw new Error('検索語は80文字以内で入力してください。入力は切り捨てていません。');
    if (state.q.normalize('NFKC').trim().split(/\s+/).filter(Boolean).length > 8) throw new Error('検索する言葉は8個以内にしてください。');
    return {...state, district: optionValid(controls.district, state.district) ? state.district : '',
      theme: optionValid(controls.theme, state.theme) ? state.theme : '', sort: optionValid(controls.sort, state.sort) ? state.sort : 'relevance',
      page: /^\d{1,6}$/.test(String(state.page)) ? Math.max(1, Number(state.page)) : 1};
  }
  function urlFor(state) {
    const params = new URLSearchParams();
    for (const key of keys) if (state[key] && !(key === 'sort' && state[key] === 'relevance')) params.set(key, state[key]);
    if (state.page > 1) params.set('page', state.page);
    return '/search/' + (params.size ? '?' + params : '');
  }
  function loadControls(state) { for (const key of keys) controls[key].value = state[key]; }
  function clearError() { error.hidden = true; error.textContent = ''; controls.q.removeAttribute('aria-invalid'); }
  function showError(text, input = false) {
    error.textContent = text; error.hidden = false;
    status.textContent = input ? '条件を確認してください。前の結果を残しています。' : '検索の読込みに失敗しました。全記事一覧からも読み進められます。';
    if (input) { controls.q.setAttribute('aria-invalid', 'true'); controls.q.focus(); }
  }
  function action(label, execute, parent = recovery) {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = label;
    button.addEventListener('click', execute); parent.append(button); return button;
  }
  function requestSearch(state, {push = false, focus = false, restore = false} = {}) {
    clearError();
    try { state = validate(state); } catch (exception) { showError(exception.message, true); return; }
    if (push) { savePosition(); history.pushState(null, '', urlFor(state)); }
    current = state; loadControls(state);
    pending = {focus, restore}; request++;
    try {
      if (!worker) {
        worker = new Worker('/assets/js/search-worker.js');
        worker.addEventListener('message', receive);
        worker.addEventListener('error', () => failure());
      }
      document.getElementById('search-results').setAttribute('aria-busy', 'true');
      worker.postMessage({id: request, query: state});
    } catch (_) { failure(); }
  }
  function failure() {
    document.getElementById('search-results').removeAttribute('aria-busy');
    showError('検索を読み込めませんでした。記事が0件という意味ではありません。');
    recovery.replaceChildren(); action('もう一度試す', () => { worker?.terminate(); worker = null; requestSearch(current || stateFromUrl(), {focus: true}); });
    const link = document.createElement('a'); link.referrerPolicy='origin'; link.href = '/c034'; link.textContent = '全記事一覧を見る'; recovery.append(link);
  }
  function receive(event) {
    const response = event.data;
    if (response.id !== request) return;
    if (response.type === 'progress') { status.textContent = response.text; return; }
    if (response.type === 'error') { failure(); return; }
    if (response.type !== 'results') return;
    current = response.query;
    history.replaceState(null, '', urlFor(current)); loadControls(current);
    heading.textContent = current.q ? `「${current.q}」の検索結果` : '記事一覧';
    const start = response.total ? (current.page - 1) * 20 + 1 : 0;
    status.textContent = `全${response.total}件。${start}〜${Math.min(current.page * 20, response.total)}件を表示。${current.page} / ${response.pages}ページ。` + (response.pageAdjusted ? '結果件数に合わせてページを調整しました。' : '');
    document.getElementById('search-results').removeAttribute('aria-busy');
    conditions.replaceChildren(); recovery.replaceChildren();
    const selected = [];
    for (const key of ['district','theme']) if (current[key]) selected.push(controls[key].selectedOptions[0].textContent);
    conditions.textContent = selected.length ? '選択中：' + selected.join(' ／ ') : '地区・テーマ：指定なし';
    if (current.district) action('地区の指定を外す', () => requestSearch({...current, district:'', page:1}, {push:true,focus:true}));
    if (current.theme) action('テーマの指定を外す', () => requestSearch({...current, theme:'', page:1}, {push:true,focus:true}));
    if (selected.length) action('絞込みだけをすべて解除', () => requestSearch({...current,district:'',theme:'',page:1}, {push:true,focus:true}));
    if (current.q) action('検索語を消す', () => requestSearch({...current,q:'',page:1}, {push:true,focus:true}));
    list.replaceChildren();
    if (!response.total) {
      const item = document.createElement('li'); item.textContent = '該当する記事が見つかりませんでした。検索語を短くするか、条件を外して探してください。'; list.append(item);
      const link = document.createElement('a'); link.referrerPolicy='origin'; link.href='/c034'; link.textContent='全記事一覧を見る'; recovery.append(link);
    }
    for (const record of response.records) renderRecord(record);
    pager.replaceChildren();
    if (current.page > 1) pageLink('前の20件', current.page - 1);
    const pageStatus = document.createElement('span'); pageStatus.textContent = `${current.page} / ${response.pages}ページ`; pager.append(pageStatus);
    if (current.page < response.pages) pageLink('次の20件', current.page + 1);
    if (pending.restore) restorePosition();
    else if (pending.focus) { heading.focus({preventScroll:true}); heading.scrollIntoView({block:'start'}); }
  }
  function renderRecord(record) {
    const url = new URL(record.url, location.origin);
    if (url.origin !== location.origin || !record.url.startsWith('/') || record.url.startsWith('//')) return;
    const item = document.createElement('li'); item.className = 'search-item';
    const title = document.createElement('h3'); const link = document.createElement('a');
    link.href = record.url; link.referrerPolicy = 'origin'; link.textContent = record.title; link.dataset.resultId = record.id;
    link.addEventListener('click', () => savePosition(record.url, record.id));
    link.addEventListener('auxclick', () => savePosition(record.url, record.id));
    link.addEventListener('contextmenu', () => savePosition(record.url, record.id));
    title.append(link); item.append(title);
    const description = document.createElement('p'); description.textContent = record.description; item.append(description);
    const meta = document.createElement('p'); meta.className='search-meta';
    const districtNames = record.districts.map(id => [...controls.district.options].find(o => o.value === id)?.textContent || '地区未分類');
    const themeNames = record.themes.map(id => [...controls.theme.options].find(o => o.value === id)?.textContent || 'テーマ未分類');
    meta.textContent = (districtNames.join('・') || '地区未分類') + ' ／ ' + (themeNames.join('・') || 'テーマ未分類'); item.append(meta);
    const date = record.updated || record.published;
    if (/^\d{4}-\d{2}-\d{2}$/.test(date) && !record.dateProvisional) {
      const info = document.createElement('p'); info.className='search-meta'; info.textContent=(record.updated ? '実質更新：' : '公開：') + date; item.append(info);
    }
    if (record.reasons.length) { const reason = document.createElement('p'); reason.className='search-reason'; reason.textContent=record.reasons.join(' ／ '); item.append(reason); }
    if (record.snippet) { const excerpt = document.createElement('p'); excerpt.className='search-excerpt'; excerpt.textContent=record.snippet; item.append(excerpt); }
    list.append(item);
  }
  function pageLink(label, page) {
    const link = document.createElement('a'); link.referrerPolicy='origin'; link.href=urlFor({...current,page}); link.textContent=label;
    link.addEventListener('click', event => { if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return; event.preventDefault(); requestSearch({...current,page}, {push:true,focus:true}); });
    pager.append(link);
  }
  function savePosition(article, focusedId) {
    if (!article && document.getElementById('search-results').getAttribute('aria-busy') === 'true') return;
    try {
      const resultUrl = location.pathname + location.search;
      const previous = JSON.parse(sessionStorage.getItem('iwata-search-position:' + resultUrl) || 'null');
      sessionStorage.setItem('iwata-search-position:' + resultUrl, JSON.stringify({scrollY:scrollY, focusedId:focusedId || previous?.focusedId || ''}));
      if (article) sessionStorage.setItem('iwata-search-return', JSON.stringify({resultUrl, article, createdAt:Date.now()}));
    } catch (_) { /* Browser history and normal links still work when storage is blocked. */ }
  }
  function restorePosition() {
    try {
      const value = JSON.parse(sessionStorage.getItem('iwata-search-position:' + location.pathname + location.search) || 'null');
      if (value && Number.isFinite(value.scrollY)) {
        const link = [...list.querySelectorAll('a[data-result-id]')].find(a => a.dataset.resultId === value.focusedId);
        if (link) link.focus({preventScroll:true});
        requestAnimationFrame(() => window.scrollTo({top:value.scrollY,behavior:'instant'}));
      }
    } catch (_) {}
  }
  controls.q.addEventListener('compositionstart', () => { composition=true; });
  controls.q.addEventListener('compositionend', () => { composition=false; });
  form.addEventListener('keydown', event => { if (event.key === 'Enter' && (composition || event.isComposing || event.keyCode === 229)) event.preventDefault(); });
  form.addEventListener('submit', event => { event.preventDefault(); if (composition) return;
    requestSearch(Object.fromEntries(keys.map(key => [key, controls[key].value]).concat([['page',1]])), {push:true,focus:true}); });
  window.addEventListener('popstate', () => requestSearch(stateFromUrl(), {restore:true}));
  window.addEventListener('pagehide', () => savePosition());
  window.addEventListener('pageshow', event => { if (event.persisted) restorePosition(); });
  const initial = stateFromUrl();
  try { loadControls(validate(initial)); } catch (exception) { controls.q.value=initial.q; showError(exception.message,true); return; }
  let restoring = false;
  try { restoring = !!sessionStorage.getItem('iwata-search-position:' + location.pathname + location.search); } catch (_) {}
  if (location.search) requestSearch(initial, {focus:!restoring,restore:restoring});
})();
