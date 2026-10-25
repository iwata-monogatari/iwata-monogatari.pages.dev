const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { pathToFileURL } = require('node:url');
const test = require('node:test');

const ROOT = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'c006.html'), 'utf8');
const json = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/c006-dictionary.json'), 'utf8'));
const COUNT = json.entries.length;
const generator = import(pathToFileURL(path.join(ROOT, 'tools/build_c006_dictionary.mjs')));
const fields = { word: 'w', kana: 'k', cat: 'cat', mean: 'm', example: 'ex', std: 'std' };

function decode(text) {
  const entities = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'" };
  return text.replace(/&(amp|lt|gt|quot|#39);/g, (_, name) => entities[name]);
}
function parseEntries(block) {
  return block.split(/<div class="entry"[^>]*>/).slice(1).map(entry => {
    const result = {};
    for (const [cls, key] of Object.entries(fields)) {
      const matches = [...entry.matchAll(new RegExp(`<(?:span|p) class="${cls}">([^<]*)<\/(?:span|p)>`, 'g'))];
      assert.equal(matches.length, 1, `exactly one escaped ${key} field`);
      let value = decode(matches[0][1]);
      if (key === 'std') { assert.ok(value.startsWith('＝ ')); value = value.slice(2); }
      result[key] = value;
    }
    return result;
  });
}
function sortKey() {
  return vm.runInNewContext(`${html.match(/(function dictionarySortKey\(reading\)\{[\s\S]*?\r?\n\})/)[1]}; dictionarySortKey`);
}
function expectedEntries() {
  // JSON（正本）から独立に並べ替えて比較する。
  const key = sortKey();
  return json.entries.slice().sort((a, b) => key(a.k).localeCompare(key(b.k), 'ja'))
    .map(d => Object.fromEntries(Object.values(fields).map(k => [k, d[k]])));
}
function block(text = html) {
  return text.split('<!-- c006-dictionary:start -->')[1].split('<!-- c006-dictionary:end -->')[0];
}

test('initial HTML contains every JSON entry with its six fields, id anchor and the existing order', () => {
  const actual = parseEntries(block());
  assert.equal(actual.length, COUNT);
  assert.equal(new Set(actual.map(d => d.w)).size, COUNT);
  assert.deepEqual(actual, expectedEntries());
  assert.deepEqual(actual.slice(0, 8).map(d => d.w), ['あいさ', 'あおたえる', '頭を切る', 'あっこ', 'あわくい', 'あんき', 'あんも', 'いいにする']);
  assert.equal((html.match(/<div class="entry" id="w-[^"]+" data-id="[a-z-]+">/g) || []).length, COUNT);
  for (const e of json.entries) {
    assert.ok(html.includes(`id="w-${e.w}" data-id="${e.id}"`), `old anchor kept for ${e.w}`);
    assert.ok(html.includes(`<span class="word-anchor" id="${e.id}" aria-hidden="true"></span>`), `new anchor for ${e.id}`);
  }
  assert.match(html, new RegExp(`id="count" role="status">${COUNT} 語<`));
  assert.match(html, /<div class="dict" id="dict">\s*<!-- c006-dictionary:start -->/);
});

test('ids are unique, URL-safe and never collide with other element ids on the page', () => {
  const ids = json.entries.map(e => e.id);
  assert.equal(new Set(ids).size, COUNT);
  for (const id of ids) assert.match(id, /^[a-z][a-z-]{0,39}$/);
  const outside = html.replace(/<!-- c006-dictionary:start -->[\s\S]*<!-- c006-dictionary:end -->/, '');
  const pageIds = new Set([...outside.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]));
  for (const id of ids) assert.ok(!pageIds.has(id), `id ${id} collides with a page element`);
});

test('every entry shows a karuta slot: a pending card now, an image once both WebP files exist', async () => {
  const { karutaReadyIds, renderEntry, headCharOf } = await generator;
  const ready = karutaReadyIds(ROOT);
  const pending = (block().match(/<figure class="karuta karuta-pending"/g) || []).length;
  const shown = (block().match(/<figure class="karuta karuta-ready"/g) || []).length;
  assert.equal(pending + shown, COUNT);
  assert.equal(shown, ready.size);
  const e = json.entries.find(x => x.id === 'aisa');
  const key = sortKey();
  const withImage = renderEntry(e, { ready: true, headChar: headCharOf(e, key) });
  assert.match(withImage, /<img src="\/assets\/karuta\/c006\/aisa-300\.webp" width="300" height="400" loading="lazy" decoding="async" alt="遠州弁かるた「あいさ」の絵札：[^"]+">/);
  assert.match(withImage, /<a class="karuta-zoom" href="\/assets\/karuta\/c006\/aisa-900\.webp">/);
  const placeholder = renderEntry(e, { ready: false, headChar: headCharOf(e, key) });
  assert.match(placeholder, /role="img" aria-label="遠州弁かるた「あいさ」の絵札（準備中）"/);
  assert.match(placeholder, /<span class="karuta-kana" aria-hidden="true">あ<\/span>/);
  assert.doesNotMatch(placeholder, /<img/);
});

test('source badges appear only for recorded sources and say what was recorded', () => {
  const withSources = json.entries.filter(e => e.sources.length);
  assert.equal(withSources.length, 30);
  const b = block();
  assert.equal((b.match(/<span class="src-badges">/g) || []).length, withSources.length);
  assert.match(b, /<span class="src-badge src-gunshi1921" title="『静岡県磐田郡誌』1921年、1242頁・旧福島村に「あんもう」の記録[^"]*">1921<\/span>/);
  assert.match(b, /<span class="src-badge src-fpjd" title="[^"]*質問「じょうぎ（定規）」にセンヒキの回答[^"]*">国研<\/span>/);
  assert.match(b, /原注：.*モノサシ/);
  assert.match(b, /質問「うつくしい（美しい）」の注記にケッコイの記録/);
  assert.equal((b.match(/<p class="word-src">/g) || []).length, withSources.length);
});

test('article links point only to public search records', async () => {
  const { loadArticleTitles } = await generator;
  const titles = loadArticleTitles(ROOT);
  const linked = json.entries.flatMap(e => e.articles);
  assert.ok(linked.length >= 14);
  for (const a of linked) assert.ok(titles.has(a), `${a} is public`);
  assert.match(block(), /<a href="\/c008">標準語⇄遠州弁 変換<\/a>/);
});

test('structured data lists every term as a DefinedTerm with a stable URL', () => {
  const m = html.match(/<script type="application\/ld\+json" id="c006-terms">\s*([\s\S]*?)\s*<\/script>/);
  assert.ok(m, 'DefinedTermSet script exists');
  const doc = JSON.parse(m[1]);
  assert.equal(doc['@type'], 'DefinedTermSet');
  assert.equal(doc.hasDefinedTerm.length, COUNT);
  const aisa = doc.hasDefinedTerm.find(t => t.termCode === 'aisa');
  assert.equal(aisa.url, 'https://iwata-monogatari.net/c006#aisa');
  assert.equal(aisa.name, 'あいさ');
  assert.equal(aisa.inDefinedTermSet['@id'], doc['@id']);
  const hon = doc.hasDefinedTerm.find(t => t.termCode === 'hon-ya');
  assert.deepEqual(hon.alternateName, ['ほんや']);
});

test('fields round trip HTML metacharacters without normalization', async () => {
  const { renderEntry } = await generator;
  const value = '  &<>"\'〜／ぁ~\n';
  const fixture = { id: 'test', ...Object.fromEntries(Object.values(fields).map(k => [k, value])), sources: [], articles: [], karuta: { scene: value } };
  const markup = renderEntry(fixture, { headChar: 'あ' });
  assert.deepEqual(parseEntries(markup), [Object.fromEntries(Object.values(fields).map(k => [k, value]))]);
  assert.ok(!markup.includes(value));
});

test('regeneration is identical, check mode never writes, and stale output is detected', async () => {
  const { buildDictionary, generateHtml, readJson, loadArticleTitles, karutaReadyIds } = await generator;
  assert.equal(generateHtml(html, readJson(ROOT), { ready: karutaReadyIds(ROOT), articleTitles: loadArticleTitles(ROOT) }), html);
  assert.deepEqual(buildDictionary({ root: ROOT, check: true }).changed, []);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'c006-static-'));
  try {
    for (const rel of ['c006.html', 'data/c006-dictionary.json', 'data/search/manifest.json']) {
      fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
      fs.copyFileSync(path.join(ROOT, rel), path.join(dir, rel));
    }
    const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/search/manifest.json'), 'utf8'));
    fs.copyFileSync(path.join(ROOT, manifest.metadata.replace(/^\//, '')), path.join(dir, manifest.metadata.replace(/^\//, '')));
    fs.cpSync(path.join(ROOT, 'assets/karuta/c006'), path.join(dir, 'assets/karuta/c006'), { recursive: true });
    const stale = html.replace('<!-- c006-dictionary:end -->', 'STALE<!-- c006-dictionary:end -->');
    fs.writeFileSync(path.join(dir, 'c006.html'), stale);
    assert.throws(() => buildDictionary({ root: dir, check: true }), /stale/);
    assert.equal(fs.readFileSync(path.join(dir, 'c006.html'), 'utf8'), stale, 'check mode never writes');
    assert.ok(buildDictionary({ root: dir }).changed.includes('c006.html'));
    assert.equal(fs.readFileSync(path.join(dir, 'c006.html'), 'utf8'), html);
    assert.deepEqual(buildDictionary({ root: dir }).changed, [], 'second run writes nothing');
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('generator rejects broken data, count drift, unknown articles and stray karuta files', async () => {
  const { generateHtml, validateDictionary, checkKarutaFiles } = await generator;
  const clone = () => JSON.parse(JSON.stringify(json));
  assert.throws(() => generateHtml(html.replace('function dictionarySortKey(reading){', 'function missing(reading){'), json), /dictionarySortKey/);
  assert.throws(() => validateDictionary({ entries: [] }), /79/);
  let j = clone(); j.entries[1].w = j.entries[0].w; assert.throws(() => validateDictionary(j), /Duplicate dictionary word/);
  j = clone(); j.entries[1].id = j.entries[0].id; assert.throws(() => validateDictionary(j), /Duplicate dictionary id/);
  j = clone(); delete j.entries[0].std; assert.throws(() => validateDictionary(j), /six/);
  j = clone(); j.entries[0].id = 'Bad Id'; assert.throws(() => validateDictionary(j), /Invalid id/);
  j = clone(); j.entries[0].karuta = {}; assert.throws(() => validateDictionary(j), /karuta\.scene/);
  j = clone(); j.entries[0].sources = [{ type: 'rumor', forms: 'x' }]; assert.throws(() => validateDictionary(j), /Unknown source type/);
  j = clone(); j.entries[0].sources = [{ type: 'gunshi1921', forms: 'x' }]; assert.throws(() => validateDictionary(j), /page/);
  j = clone(); j.entries[0].articles = ['no-such-page']; assert.throws(() => validateDictionary(j, { articleTitles: new Map() }), /public search record/);
  j = clone(); j.entries.push({ ...j.entries[0], id: 'extra', w: '追加語' });
  assert.throws(() => generateHtml(html, j), /語数/);
  assert.throws(() => generateHtml(html.replace('<!-- c006-terms:start -->', ''), json), /terms marker/);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'c006-karuta-'));
  try {
    const kd = path.join(dir, 'assets/karuta/c006'); fs.mkdirSync(kd, { recursive: true });
    fs.writeFileSync(path.join(kd, 'aisa-300.webp'), '');
    assert.throws(() => checkKarutaFiles(json.entries, dir), /pair/);
    fs.writeFileSync(path.join(kd, 'aisa-900.webp'), '');
    checkKarutaFiles(json.entries, dir);
    fs.writeFileSync(path.join(kd, 'nosuchword-300.webp'), '');
    assert.throws(() => checkKarutaFiles(json.entries, dir), /no dictionary entry/);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('JavaScript enhancement is opt-in and build generates the dictionary before indexing', () => {
  assert.match(html, /<div class="tabs" hidden>/);
  assert.match(html, /<div class="search-box" hidden>/);
  assert.match(html, /id="filters" hidden/);
  assert.match(html, new RegExp(`id="dictionary-offline-note">[^<]*${COUNT}語`));
  assert.match(html, /\.panel\{display:block;\}/);
  assert.doesNotMatch(html, /dictEl\.innerHTML\s*=/);
  assert.match(html, /<button type="button" class="act" id="karuta-view" aria-pressed="false">絵札で並べる<\/button>/);
  const build = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8')).scripts.build;
  assert.ok(build.startsWith('node tools/build_c006_dictionary.mjs && '));
  for (const step of ['sync_new_articles.py', 'scripts/build_search.py', 'scripts/build_saguchi_related.py', 'tools/sync-knowledge-count.mjs']) assert.ok(build.includes(step));
});

test('generated companion files are current: survey word list and karuta production sheet', async () => {
  const { renderWordIds, renderKarutaSheet, karutaReadyIds } = await generator;
  assert.equal(fs.readFileSync(path.join(ROOT, 'functions/api/kotoba/_words.js'), 'utf8'), renderWordIds(json.entries));
  const sheet = fs.readFileSync(path.join(ROOT, 'docs/karuta/c006-karuta-sheet.csv'), 'utf8');
  assert.equal(sheet, renderKarutaSheet(json.entries, { sortKey: sortKey(), ready: karutaReadyIds(ROOT) }));
  assert.equal(sheet.trim().split('\r\n').length, COUNT + 1);
  assert.ok(sheet.startsWith('﻿id,語,読み,分類,頭の字,読み札（作例）,絵の場面,alt,'));
});

test('mamettai keeps its example and paper beside one semantic four-sense table in initial HTML', () => {
  const entry = json.entries.find(e => e.id === 'mamettai');
  const markup = block().split('<div class="entry" id="w-まめったい"')[1].split('<div class="entry"')[0];
  assert.equal((block().match(/<table class="word-context">/g) || []).length, 1);
  assert.deepEqual(entry.contextTable.rows.map(r => r.meaning), ['体を動かしてよく働く', '健康だ', '落ち着きがない', '性格的に几帳面だ']);
  const rows = [...markup.matchAll(/<tr><th scope="row"><span class="txt">([^<]*)<\/span><\/th><td><span class="txt">([^<]*)<\/span><\/td><\/tr>/g)]
    .map(m => ({ meaning: decode(m[1]), scene: decode(m[2]) }));
  assert.deepEqual(rows, entry.contextTable.rows);
  assert.match(markup, /<caption><span class="txt">「まめったい」4義の場面別整理<\/span><\/caption>/);
  assert.equal((markup.match(/<th scope="col">/g) || []).length, 2);
  assert.ok(markup.includes('あの子はまめったいで、よう手伝ってくれる。'));
  assert.ok(markup.includes('あの子はまめだから、よく手伝ってくれる。'));
  assert.ok(markup.includes(`href="${entry.reference.url}"`));
  assert.match(entry.n, /編集上の整理.*採集用例ではありません/);
  assert.match(entry.n, /判断できなければ話し手へ意味を確認/);
  assert.match(entry.n, /年齢だけで判定する資料ではありません/);
});

test('context table content is escaped, searchable and rejected when rows or source are incomplete', async () => {
  const { renderEntry, renderData, validateDictionary } = await generator;
  const entry = structuredClone(json.entries.find(e => e.id === 'mamettai'));
  const value = ' &<>"\'〜／ぁ\n';
  entry.contextTable = { caption: value, rows: [{ meaning: value, scene: value }] };
  const markup = renderEntry(entry, { headChar: 'ま' });
  assert.ok(!markup.includes(value));
  const cells = [...markup.matchAll(/<span class="txt">([^<]*)<\/span>/g)].slice(-3).map(m => decode(m[1]));
  assert.deepEqual(cells, [value, value, value]);
  const data = vm.runInNewContext(`${renderData([entry])}; JSON.stringify(DATA)`);
  assert.deepEqual(JSON.parse(data)[0].contextTable, entry.contextTable);
  assert.match(html, /rest: normalize\([^\n]*d\.contextTable\.rows\.map/);
  for (const mutate of [
    e => { e.contextTable.rows = []; },
    e => { e.contextTable.rows[0].scene = ''; },
    e => { e.contextTable.rows.push(e.contextTable.rows[0]); },
    e => { e.contextTable.caption = ''; },
    e => { delete e.reference; },
  ]) {
    const doc = structuredClone(json); mutate(doc.entries.find(e => e.id === 'mamettai'));
    assert.throws(() => validateDictionary(doc), /contextTable/);
  }
});
