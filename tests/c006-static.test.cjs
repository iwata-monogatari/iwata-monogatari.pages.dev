const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { pathToFileURL } = require('node:url');
const test = require('node:test');

const ROOT = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'c006.html'), 'utf8');
const generator = import(pathToFileURL(path.join(ROOT, 'tools/build_c006_dictionary.mjs')));
const fields = { word: 'w', kana: 'k', cat: 'cat', mean: 'm', example: 'ex', std: 'std' };
function decode(text) {
  const entities = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'" };
  return text.replace(/&(amp|lt|gt|quot|#39);/g, (_, name) => entities[name]);
}
function parseEntries(block) {
  return block.split('<div class="entry">').slice(1).map(entry => {
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
function expectedEntries() {
  // Independent extraction and comparison against the original page source.
  const data = vm.runInNewContext(html.match(/const DATA = (\[[\s\S]*?\r?\n\]);/)[1]);
  const key = vm.runInNewContext(`${html.match(/(function dictionarySortKey\(reading\)\{[\s\S]*?\r?\n\})/)[1]}; dictionarySortKey`);
  return JSON.parse(JSON.stringify(Array.from(data).sort((a,b)=>key(a.k).localeCompare(key(b.k),'ja'))));
}

test('initial HTML contains all 79 unique entries, all six original fields and the existing order', async () => {
  const { START, END } = await generator;
  const block = html.split(START)[1].split(END)[0];
  const actual = parseEntries(block);
  assert.equal(actual.length, 79);
  assert.equal(new Set(actual.map(d=>d.w)).size, 79);
  assert.deepEqual(actual, expectedEntries());
  assert.deepEqual(actual.slice(0,8).map(d=>d.w), ['あいさ','頭を切る','あんも','いいにする','いずようない','いっちょ','いのく','いぼる']);
  assert.equal((html.match(/<div class="entry">/g)||[]).length,79);
  assert.match(html, /id="count"[^>]*>79 語<\/p>/);
  assert.match(html, /<div class="dict" id="dict">\s*<!-- c006-dictionary:start -->/);
});

test('all fields round trip HTML metacharacters, whitespace and reading variants without normalization', async () => {
  const { renderEntries } = await generator;
  const value = '  &<>"\'　～あ／い~\n';
  const fixture = Object.fromEntries(Object.values(fields).map(k=>[k,value]));
  const markup = renderEntries([fixture]);
  assert.deepEqual(parseEntries(markup), [fixture]);
  assert.equal((markup.match(/&amp;&lt;&gt;&quot;&#39;/g)||[]).length,6);
  assert.ok(!markup.includes(value));
});

test('regeneration is identical, preserves content outside markers, and does not write unchanged files', async () => {
  const { START, END, generateHtml, buildDictionary } = await generator;
  assert.equal(generateHtml(html),html);
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'c006-static-'));
  const file=path.join(dir,'c006.html');
  try {
    fs.writeFileSync(file, html);
    const old=new Date('2020-01-01T00:00:00Z'); fs.utimesSync(file,old,old);
    assert.equal(buildDictionary({file}),false);
    assert.equal(fs.statSync(file).mtimeMs,old.getTime());
    assert.equal(buildDictionary({file,check:true}),false);
    const start=html.indexOf(START)+START.length, end=html.indexOf(END);
    const stale=html.slice(0,start)+'\nSTALE\n'+html.slice(end);
    fs.writeFileSync(file,stale);
    assert.throws(()=>buildDictionary({file,check:true}),/stale/);
    assert.equal(fs.readFileSync(file,'utf8'),stale,'check mode never writes');
    assert.equal(buildDictionary({file}),true);
    assert.equal(fs.readFileSync(file,'utf8'),html);
  } finally { fs.rmSync(dir,{recursive:true,force:true}); }
});

test('generator rejects failed extraction, count mismatch, duplicate words, missing fields and broken markers', async () => {
  const { START, END, generateHtml } = await generator;
  assert.throws(()=>generateHtml(html.replace('const DATA =','const MISSING =')),/DATA/);
  assert.throws(()=>generateHtml(html.replace('function dictionarySortKey(reading){','function missing(reading){')),/dictionarySortKey/);
  const data=html.match(/const DATA = (\[[\s\S]*?\r?\n\]);/)[1];
  assert.throws(()=>generateHtml(html.replace(data,'[\n]')),/79/);
  const duplicate=JSON.parse(JSON.stringify(expectedEntries())); duplicate[1].w=duplicate[0].w;
  const modified=(entries)=>html.replace(data,JSON.stringify(entries,null,2));
  assert.throws(()=>generateHtml(modified(duplicate)),/Duplicate/);
  const missing=expectedEntries(); delete missing[0].std;
  assert.throws(()=>generateHtml(modified(missing)),/six/);
  assert.throws(()=>generateHtml(html.replace(START,'')),/marker/);
  assert.throws(()=>generateHtml(html+START),/marker/);
  assert.throws(()=>generateHtml(html.replace(START,'TEMP').replace(END,START).replace('TEMP',END)),/reversed/);
});

test('JavaScript enhancement is opt-in and build generates the dictionary before indexing', () => {
  assert.match(html,/<div class="tabs" hidden>/);
  assert.match(html,/<div class="search-box" hidden>/);
  assert.match(html,/id="filters" hidden/);
  assert.match(html,/id="dictionary-offline-note">[^<]*79語/);
  assert.match(html,/\.panel\{display:block;\}/);
  assert.doesNotMatch(html,/dictEl\.innerHTML\s*=/);
  const build=JSON.parse(fs.readFileSync(path.join(ROOT,'package.json'),'utf8')).scripts.build;
  assert.ok(build.startsWith('node tools/build_c006_dictionary.mjs && '));
  for (const step of ['sync_new_articles.py','scripts/build_search.py','scripts/build_saguchi_related.py','tools/sync-knowledge-count.mjs']) assert.ok(build.includes(step));
});
