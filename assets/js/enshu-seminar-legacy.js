(() => {
  'use strict';
  const lessons = new Set(['evidence','geography','modality','grammar','sound','meaning','folklore','change']);
  const match = /^#lesson-([a-z]+)$/.exec(location.hash);
  if (match && lessons.has(match[1])) {
    location.replace('/enshu/seminar/' + match[1] + '/' + location.search);
  }
})();
