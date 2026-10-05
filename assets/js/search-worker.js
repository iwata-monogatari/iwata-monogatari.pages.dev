'use strict';
importScripts('/assets/js/search-core.js');
const S = IwataSearch;
let initialization, metadata, manifest, documents, lastRequest = 0;
const cache = new Map();
let cacheBytes = 0;
async function read(url) {
  if (!url.startsWith('/data/search/') || url.includes('..')) throw new Error('索引のURLが正しくありません。');
  if (cache.has(url)) { const item = cache.get(url); cache.delete(url); cache.set(url, item); return item.value; }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(url, { signal: controller.signal, credentials: 'same-origin', cache: url === '/data/search/manifest.json' ? 'no-store' : 'default' });
    if (!response.ok) throw new Error('索引を取得できませんでした。');
    const raw = await response.text();
    const value = JSON.parse(raw);
    cache.set(url, { value, bytes: raw.length * 2 }); cacheBytes += raw.length * 2;
    while (cacheBytes > 20 * 1024 * 1024 && cache.size > 1) {
      const key = cache.keys().next().value; cacheBytes -= cache.get(key).bytes; cache.delete(key);
    }
    return value;
  } finally { clearTimeout(timeout); }
}
async function initialize() {
  if (!initialization) initialization = (async () => {
    manifest = await read('/data/search/manifest.json');
    if (manifest.schemaVersion !== 1 || manifest.gramShards.length !== 128) throw new Error('索引の版が対応していません。');
    metadata = await read(manifest.metadata);
    if (metadata.schemaVersion !== 1 || metadata.dictionaryVersion !== manifest.dictionaryVersion || metadata.records.length !== manifest.count) throw new Error('索引の組合せが一致しません。');
    documents = S.prepare(metadata);
  })().catch(error => { initialization = null; throw error; });
  return initialization;
}
async function run(request, id) {
  await initialize();
  const query = S.validate(request, [...metadata.districts.map(d => d.district_id), 'common', 'unknown'], [...metadata.themes.map(t => t.id), 'unknown']);
  const active = documents.map((doc, ordinal) => ({ doc, ordinal, matches: query.terms.map(t => S.metadataMatch(doc, t)) })).filter(d => S.eligible(d.doc, query));
  const missingTerms = [...new Set(active.flatMap(d => query.terms.filter((t, i) => !d.matches[i] && Array.from(t).length > 1)))];
  const postings = new Map();
  // Fetch query-specific shards. Use compact frequency hints to choose up to three rare bigrams; verify complete terms
  // against full bodies so this prefilter never changes substring semantics.
  for (const term of missingTerms) {
    if (id !== lastRequest) return;
    const grams = S.grams(term).sort((a,b) => S.frequencyHint(a,manifest.gramFrequencyHint) - S.frequencyHint(b,manifest.gramFrequencyHint));
    let candidates;
    for (const gram of grams.slice(0,3)) {
      const data = await read(manifest.gramShards[S.shard(gram)]);
      const found = data[gram] || [];
      if (!candidates) candidates = found;
      else { const set = new Set(found); candidates = candidates.filter(n => set.has(n)); }
      if (!candidates.length) break;
    }
    postings.set(term, new Set(candidates));
  }
  const candidates = active.filter(d => query.terms.every((term, i) => d.matches[i] || (postings.has(term) && postings.get(term).has(d.ordinal))));
  const results = [];
  let next = 0, completed = 0;
  async function consume() {
    while (next < candidates.length) {
      if (id !== lastRequest) return;
      const candidate = candidates[next++];
      let matches = candidate.matches, snippet = '';
      if (matches.some(m => !m)) {
        const body = await read(candidate.doc.record.body);
        if (body.schemaVersion !== 1 || body.id !== candidate.doc.record.id || typeof body.text !== 'string') throw new Error('本文索引が一致しません。');
        matches = matches.map((match, i) => match || (body.text.includes(query.terms[i]) ? {score: 5, reason: '本文に一致'} : null));
        if (matches.every(Boolean) && typeof body.display === 'string') {
          const term = String(query.q).split(/\s+/).find(t => t && body.display.includes(t));
          if (term) {
            const at = body.display.indexOf(term);
            const before = Array.from(body.display.slice(0, at)).slice(-45).join('');
            const after = Array.from(body.display.slice(at)).slice(0, 120).join('');
            snippet = (at > before.length ? '…' : '') + before + after + (at + after.length < body.display.length ? '…' : '');
          }
        }
      }
      if (matches.every(Boolean)) results.push({...S.score(candidate.doc, query, matches), snippet});
      completed++;
      if (completed % 40 === 0 && id === lastRequest) postMessage({type: 'progress', id, text: `本文も確認しています（${completed} / ${candidates.length}件）。確定した件数は確認後に表示します。`});
    }
  }
  await Promise.all(Array.from({length: Math.min(6, candidates.length || 1)}, consume));
  if (id !== lastRequest) return;
  S.sort(results, query);
  const total = results.length;
  const pages = Math.max(1, Math.ceil(total / 20));
  const requestedPage = query.page;
  query.page = Math.min(query.page, pages);
  postMessage({type: 'results', id, query, total, pages, pageAdjusted: requestedPage !== query.page,
    records: results.slice((query.page - 1) * 20, query.page * 20), generation: manifest.generation});
}
onmessage = event => {
  lastRequest = event.data.id;
  postMessage({type: 'progress', id: lastRequest, text: '公開記事の索引を読み込んでいます。下の一覧も利用できます。'});
  run(event.data.query, event.data.id).catch(() => {
    if (event.data.id === lastRequest) postMessage({type:'error', id: event.data.id, text:'検索を読み込めませんでした。通信や索引の状態をご確認ください。記事が0件という意味ではありません。'});
  });
};
