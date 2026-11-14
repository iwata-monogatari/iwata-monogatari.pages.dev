(() => {
  'use strict';
  const node = document.getElementById('records-page-map');
  if (!node) return;
  const pages = JSON.parse(node.textContent);
  function redirect() {
    const params = new URLSearchParams(location.search);
    if (['q','v','p'].some(key => params.has(key))) {
      location.replace('/enshu/records/search/' + location.search + location.hash);
      return;
    }
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const page = pages[id] || (/^page-(124[3-9]|125[0-4])$/.test(id) ? Number(id.slice(5)) : null);
    if (page >= 1243 && page <= 1254) {
      location.replace('/enshu/records/' + page + '/' + location.search + '#' + encodeURIComponent(id));
    }
  }
  window.addEventListener('hashchange', redirect);
  redirect();
})();
