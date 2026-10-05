(() => {
  'use strict';
  if (window.__iwataReaderPreferences) return;
  window.__iwataReaderPreferences = true;
  const sizes = ['standard', 'large', 'largest'];
  function apply(size) {
    document.documentElement.dataset.textSize = sizes.includes(size) ? size : 'standard';
    document.querySelectorAll('[data-text-size]').forEach(button => {
      if (button.tagName === 'BUTTON') button.setAttribute('aria-pressed', String(button.dataset.textSize === document.documentElement.dataset.textSize));
    });
  }
  try { apply(localStorage.getItem('iwata-text-size')); } catch (_) { apply('standard'); }
  document.addEventListener('click', event => {
    const button = event.target.closest('button[data-text-size]');
    if (!button) return;
    apply(button.dataset.textSize);
    try { localStorage.setItem('iwata-text-size', button.dataset.textSize); } catch (_) {}
  });
  // Never infer a return history for an external or direct arrival.
  if (location.pathname.startsWith('/search')) return;
  try {
    const pending = JSON.parse(sessionStorage.getItem('iwata-search-return') || 'null');
    const key = path => path.replace(/\/index\.html$/, '/').replace(/\.html$/, '').replace(/\/$/, '') || '/';
    let value = history.state?.iwataSearchReturn;
    if (pending && Date.now() - pending.createdAt < 90 * 1000 && key(pending.article) === key(location.pathname)) {
      value = pending;
      sessionStorage.removeItem('iwata-search-return');
      history.replaceState({...history.state, iwataSearchReturn: value}, '', location.href);
    }
    if (!value || Date.now() - value.createdAt > 24 * 60 * 60 * 1000) return;
    const result = new URL(value.resultUrl, location.origin);
    if (result.origin !== location.origin || result.pathname !== '/search/' || key(value.article) !== key(location.pathname)) return;
    const nav = document.querySelector('.gh-menu');
    if (!nav) return;
    const link = document.createElement('a'); link.href=result.pathname + result.search; link.textContent='検索結果へ戻る';
    link.className='gh-search-return'; nav.prepend(link);
  } catch (_) { /* Common search/catalogue links remain available. */ }
})();
