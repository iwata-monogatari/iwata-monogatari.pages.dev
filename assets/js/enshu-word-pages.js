(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('word-page-map')) return;
  const map = JSON.parse($('word-page-map').textContent);
  const params = new URLSearchParams(location.search), requested = params.get('word');
  if (Object.prototype.hasOwnProperty.call(map, requested)) { location.replace(map[requested]); return; }
  const cards = [...document.querySelectorAll('.word-catalog-item')];
  const normalize = s => s.normalize('NFKC').toLocaleLowerCase('ja');
  $('word-search').value = params.get('q') || '';
  for (const key of ['scene', 'source']) {
    const field = $('word-' + key), value = params.get(key);
    if ([...field.options].some(o => o.value === value)) field.value = value;
  }
  function filter(update = false) {
    const q = normalize($('word-search').value.trim()), scene = $('word-scene').value, source = $('word-source').value;
    cards.forEach(a => { a.hidden = !((!q || normalize(a.dataset.search).includes(q)) && (scene === 'all' || a.dataset.scenes.split(',').includes(scene)) && (source === 'all' || a.dataset.source === source)); });
    const count = cards.filter(a => !a.hidden).length;
    $('word-status').textContent = `${count}語を表示（全${cards.length}語）` + (count ? '' : '。条件を広げてください。');
    $('word-random').disabled = !count;
    if (update) {
      const url = new URL(location.href);url.searchParams.delete('word');
      for (const [key, value] of [['q', $('word-search').value.trim()], ['scene', scene], ['source', source]]) { if (value && value !== 'all') url.searchParams.set(key, value); else url.searchParams.delete(key); }
      history.replaceState(null, '', url.pathname + url.search + url.hash);
    }
  }
  $('word-search-form').addEventListener('submit', e => { e.preventDefault(); filter(true); });
  $('word-search').addEventListener('input', () => filter(true));
  for (const key of ['scene','source']) $('word-' + key).addEventListener('change', () => filter(true));
  $('word-clear').addEventListener('click', () => { $('word-search').value = ''; $('word-scene').value = 'all'; $('word-source').value = 'all'; filter(true); });
  $('word-random').addEventListener('click', () => { const visible = cards.filter(a => !a.hidden);if (visible.length) location.assign(visible[Math.floor(Math.random() * visible.length)].href); });
  filter();
})();
