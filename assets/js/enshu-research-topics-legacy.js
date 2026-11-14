(() => {
  'use strict';
  const topics = new Set(['systematic','regional','new-sources','kinship','livelihood','honorific','festival','language','grammar','word-history','folk-life','variation','sound','foundations']);
  function redirect() {
    const key = location.hash.slice(1);
    if (topics.has(key)) location.replace('/enshu/research/topics/' + key + '/' + location.search);
    else if (['life-water','life-forest','life-farm','life-trade'].includes(key)) {
      location.replace('/enshu/research/topics/livelihood/' + location.search + '#' + key);
    }
  }
  window.addEventListener('hashchange', redirect);
  redirect();
})();
