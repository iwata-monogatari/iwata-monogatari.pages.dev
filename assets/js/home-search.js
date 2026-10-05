(() => {
  'use strict';
  const form = document.getElementById('home-search-form');
  if (!form) return;
  // Preserve formerly shared /?q= URLs without sending search terms to analytics.
  const old = new URLSearchParams(location.search);
  if (['q','district','theme','sort','page'].some(key => old.has(key))) {
    const params = new URLSearchParams();
    for (const key of ['q','district','theme','sort','page']) if (old.has(key)) params.set(key, old.get(key));
    location.replace('/search/?' + params); return;
  }
  document.getElementById('chips')?.addEventListener('click', event => {
    const button = event.target.closest('button[data-q]');
    if (!button) return;
    form.elements.q.value=button.dataset.q; form.requestSubmit();
  });
  let composition=false;
  form.elements.q.addEventListener('compositionstart', () => { composition=true; });
  form.elements.q.addEventListener('compositionend', () => { composition=false; });
  form.addEventListener('keydown', event => { if (event.key==='Enter' && (composition || event.isComposing || event.keyCode===229)) event.preventDefault(); });
  form.addEventListener('submit', event => {
    const q=form.elements.q.value;
    if (composition) { event.preventDefault(); return; }
    if (Array.from(q).length>80 || q.normalize('NFKC').trim().split(/\s+/).filter(Boolean).length>8) {
      event.preventDefault(); const error=document.getElementById('home-search-error');
      error.hidden=false; error.textContent='検索語は80文字・8個の言葉以内で入力してください。入力は切り捨てていません。'; form.elements.q.focus();
    }
  });
})();
