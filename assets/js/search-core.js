(function (root) {
  'use strict';
  const normalize = value => String(value || '').normalize('NFKC').toLowerCase()
    .replace(/[ァ-ヶ]/g, c => String.fromCharCode(c.charCodeAt(0) - 96)).replace(/\s+/g, ' ').trim();
  const grams = value => { const chars = Array.from(value); return [...new Set(chars.slice(1).map((c, i) => chars[i] + c))]; };
  const shard = gram => { const chars = Array.from(gram); return (chars[0].codePointAt(0) * 31 + chars[1].codePointAt(0)) % 128; };
  function frequencyHint(gram, hint) {
    if (!hint || hint.width !== 8192 || hint.rows.length !== 3) return 0;
    return Math.min(...hint.rows.map((row, seed) => {
      let hash = (0x811c9dc5 ^ seed) >>> 0;
      for (const char of gram) hash = Math.imul(hash ^ char.codePointAt(0), 16777619) >>> 0;
      return row.charCodeAt(hash % hint.width) - 65;
    }));
  }
  const idKey = value => normalize(value).replace(/^\//, '').replace(/\.html$/, '').replace(/\/$/, '');
  function validate(query, districts, themes) {
    if (Array.from(String(query.q || '')).length > 80) throw new Error('検索語は80文字以内で入力してください。入力は切り捨てていません。');
    const terms = normalize(query.q).split(' ').filter(Boolean);
    if (terms.length > 8) throw new Error('検索する言葉は8個以内にしてください。空白で区切った言葉を数えます。');
    const safePage = /^\d{1,6}$/.test(String(query.page || '1')) ? Math.max(1, Number(query.page || 1)) : 1;
    return { q: String(query.q || '').trim(), terms, district: districts.includes(query.district) ? query.district : '',
      theme: themes.includes(query.theme) ? query.theme : '', sort: ['relevance', 'newest', 'title'].includes(query.sort) ? query.sort : 'relevance', page: safePage };
  }
  function prepare(metadata) {
    const entities = new Map(metadata.dictionary.map(e => [e.entityId, e]));
    return metadata.records.map(record => ({ record, title: normalize(record.title),
      headings: normalize(record.headings.join(' ')), description: normalize(record.description),
      keywords: normalize(record.keywords.join(' ')), aliases: record.aliases.map(normalize),
      ids: [record.id, ...record.sourceIds].map(idKey),
      readings: (record.entities || []).map(id => entities.get(id)).filter(Boolean)
        .flatMap(e => [e.reading, ...e.aliases].filter(Boolean).map(value => ({value: normalize(value), entity: e}))) }));
  }
  function eligible(doc, query) {
    const r = doc.record;
    const district = !query.district || (query.district === 'unknown' ? !r.districts.length : r.districts.includes(query.district));
    const theme = !query.theme || (query.theme === 'unknown' ? !r.themes.length : r.themes.includes(query.theme));
    return district && theme;
  }
  function metadataMatch(doc, term) {
    if (doc.ids.includes(idKey(term))) return { score: 2000, reason: '記事IDに一致' };
    if (doc.title.includes(term)) return { score: 500, reason: '題名に一致' };
    if (doc.aliases.some(t => t.includes(term))) return { score: 140, reason: '旧題名に一致' };
    const reading = doc.readings.find(r => r.value === term);
    if (reading) return { score: doc.title.includes(normalize(reading.entity.preferredLabel)) ? 400 : 120, reason: `読み（${reading.entity.entityType === 'district' ? '地区' : '人物'}：${reading.entity.preferredLabel}）に一致` };
    // A one-character query intentionally uses titles and confirmed entities only.
    if (Array.from(term).length === 1) return null;
    if (doc.keywords.includes(term)) return { score: 90, reason: '記事の言葉に一致' };
    if (doc.headings.includes(term)) return { score: 60, reason: '見出しに一致' };
    if (doc.description.includes(term)) return { score: 30, reason: '説明に一致' };
    return null;
  }
  function score(doc, query, matches) {
    let score = matches.reduce((sum, match) => sum + match.score, 0);
    if (doc.title === normalize(query.q) || doc.aliases.includes(normalize(query.q)) || doc.ids.includes(idKey(query.q))) score += 100000;
    else if (doc.title.includes(normalize(query.q)) && query.q) score += 500;
    return { ...doc.record, score, reasons: [...new Set(matches.map(m => m.reason))] };
  }
  function sort(results, query) {
    const idOrder = (a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
    const newest = (a, b) => (b.updated || b.published || '').localeCompare(a.updated || a.published || '') || idOrder(a, b);
    return results.sort((a, b) => {
      if (query.sort === 'title') return a.title.localeCompare(b.title, 'ja') || idOrder(a, b);
      if (query.sort === 'newest' || !query.terms.length) return newest(a, b);
      return b.score - a.score || idOrder(a, b);
    });
  }
  root.IwataSearch = { normalize, grams, shard, frequencyHint, validate, prepare, eligible, metadataMatch, score, sort };
  if (typeof module !== 'undefined' && module.exports) module.exports = root.IwataSearch;
})(globalThis);
