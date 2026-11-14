/* Public word IDs and old section links remain usable after the page split. */
(() => {
  const current = new URL(location.href), hash = current.hash.slice(1);
  let path = {courses:'/enshu/courses/', practice:'/enshu/practice/', cards:'/enshu/words/'}[hash];
  if (current.searchParams.has('word')) path = '/enshu/words/';
  const scenes=['kitchen','weather','home','outing','work','body','feelings','grammar','family','amount','play','similar'];
  if (scenes.some(id=>hash==='scene-'+id)) path = '/enshu/courses/'+(hash==='scene-work'?'work-tools':hash.slice(6))+'/';
  if (!path) return;
  const next = new URL(path, location.origin);
  for (const key of ['word','scene','source','fga_internal','atawi_internal']) {
    if (current.searchParams.has(key)) next.searchParams.set(key, current.searchParams.get(key));
  }
  location.replace(next.pathname+next.search);
})();
