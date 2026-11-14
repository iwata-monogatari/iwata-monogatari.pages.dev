(() => {
  'use strict';
  const map = JSON.parse(document.getElementById('compare-page-map')?.textContent || '{}');
  function followLegacyTheme() {
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    if (!hash.startsWith('compare-')) return;
    const id = hash.slice('compare-'.length);
    if (Object.prototype.hasOwnProperty.call(map, id)) location.replace(map[id] + location.hash);
  }
  followLegacyTheme();
  window.addEventListener('hashchange', followLegacyTheme);
})();
