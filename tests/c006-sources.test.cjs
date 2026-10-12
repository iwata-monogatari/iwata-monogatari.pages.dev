const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const root = path.resolve(__dirname, '..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const fpjd = read('data/c006-fpjd.json');
const gunshi = read('data/c006-gunshi1921.json');
const entries = read('data/c006-dictionary.json').entries;
const html = fs.readFileSync(path.join(root, 'c172.html'), 'utf8');

test('FPJD preserves all 287 records, 211 questions and one point with stable deep links', () => {
  assert.equal(fpjd.records.length, 287);
  assert.equal(new Set(fpjd.records.map(r => r.id)).size, 287);
  assert.equal(new Set(fpjd.records.map(r => r.question)).size, 211);
  assert.equal(new Set(fpjd.records.map(r => r.point)).size, 1);
  for (const r of fpjd.records) assert.ok(html.includes(`id="fpjd-${r.id}"`));
  const zura = fpjd.records.find(r => String(r.id) === '119897');
  assert.equal(zura.form, 'センセーズラ');
  assert.match(zura.note, /ゆ/);
  assert.match(zura.note, /少/);
  assert.match(html, /センセーズラ<\/td><td>（ゆ）〈少〉/);
});

test('each badge resolves to a source record and preserves historical place or note status', () => {
  for (const e of entries) for (const s of e.sources) {
    const anchor = new URL(s.url).hash.slice(1);
    assert.ok(html.includes(`id="${anchor}"`), `${e.id}: ${anchor}`);
    if (s.type === 'gunshi1921') {
      const record = gunshi.records.find(r => r.id === anchor);
      assert.ok(record);
      assert.equal(s.village, record.village);
      assert.equal(s.forms, record.form);
      assert.equal(String(s.page), String(record.page));
    } else if (s.type === 'fpjd') {
      const record = fpjd.records.find(r => String(r.id) === String(s.dataId));
      assert.ok(record);
      assert.equal(s.item, record.item);
      if (s.recordKind === 'note') assert.ok(record.note.includes(s.forms));
      else assert.equal(s.forms, record.form);
      assert.equal(s.note, record.note);
    }
  }
  assert.equal(entries.find(e => e.id === 'ozoi').sources[0].village, '浦川村');
  for (const id of ['chinpurikaeru', 'tenkocho', 'seseru']) {
    assert.ok(!entries.find(e => e.id === id).sources.some(s => s.type === 'gunshi1921'), `${id} is comparison only`);
  }
});

test('every dictionary word has both image sizes and the PDF has been produced', () => {
  for (const e of entries) for (const width of [300, 900]) {
    assert.ok(fs.statSync(path.join(root, `assets/karuta/c006/${e.id}-${width}.webp`)).size > 1000);
  }
  const pdf = fs.readFileSync(path.join(root, 'downloads/enshu-karuta-122.pdf'));
  assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
  assert.ok(pdf.length < 25 * 1024 * 1024, 'Cloudflare Pages asset limit');
});
