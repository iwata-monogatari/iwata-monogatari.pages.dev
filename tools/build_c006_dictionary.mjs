// c006（遠州弁辞典）の生成ツール。
// 語データの正本は data/c006-dictionary.json。ここから次を生成・検査する。
//   1. c006.html の辞典一覧（JavaScript なしでも読める初期HTML）
//   2. c006.html の検索用データ（const DATA）
//   3. c006.html の構造化データ（DefinedTermSet）
//   4. functions/api/kotoba/_words.js（読者調査で受け付ける語ID）
//   5. docs/karuta/c006-karuta-sheet.csv（絵札の制作表）
// 使い方: node tools/build_c006_dictionary.mjs [--check]
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const START = '<!-- c006-dictionary:start -->';
export const END = '<!-- c006-dictionary:end -->';
export const DATA_START = '/* c006-data:start */';
export const DATA_END = '/* c006-data:end */';
export const TERMS_START = '<!-- c006-terms:start -->';
export const TERMS_END = '<!-- c006-terms:end -->';
export const KARUTA_DIR = 'assets/karuta/c006';
const SITE = 'https://iwata-monogatari.net';
const FIELDS = ['w', 'k', 'cat', 'm', 'ex', 'std'];
const OPTIONAL_FIELDS = ['n', 'syn'];
const CATS = ['語尾・あいさつ', '形容・ようす', '気持ち', '程度・量', '動作・行い', '名詞・もの'];
export const SOURCE_TYPES = {
  gunshi1921: { label: '1921', name: '『静岡県磐田郡誌』1921年' },
  fpjd: { label: '国研', name: '国立国語研究所 全国方言分布調査（2010〜2015年）磐田市地点' },
  hogenshu: { label: '方言集', name: '磐田市内の方言集' },
  reader: { label: '読者', name: '磐田ことば調査（読者の自己申告）' },
};
const ID_PATTERN = /^[a-z][a-z-]{0,39}$/;
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

const isNonEmptyString = v => typeof v === 'string' && v.length > 0;

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function extractOnce(html, pattern, label) {
  const matches = [...html.matchAll(pattern)];
  if (matches.length !== 1) throw new Error(`Expected exactly one ${label}`);
  return matches[0][1];
}

// 並び順の比較キーは、ページ内の dictionarySortKey をそのまま使う（表示と一覧の順をずらさない）。
export function sortKeyFunction(html) {
  const source = extractOnce(html, /(function dictionarySortKey\(reading\)\{[\s\S]*?\r?\n\})/g, 'dictionarySortKey');
  return vm.runInNewContext(`${source}; dictionarySortKey`, Object.create(null), { timeout: 1000 });
}

export function validateDictionary(json, { articleTitles = null } = {}) {
  if (!json || !Array.isArray(json.entries)) throw new Error('Dictionary JSON must have an entries array');
  const entries = json.entries;
  if (entries.length < 79) throw new Error('Expected at least 79 dictionary entries');
  const words = new Set();
  const ids = new Set();
  for (const e of entries) {
    if (!e || FIELDS.some(f => !isNonEmptyString(e[f]))) {
      throw new Error('Every dictionary entry must have six non-empty string fields');
    }
    if (OPTIONAL_FIELDS.some(f => f in e && !isNonEmptyString(e[f]))) {
      throw new Error(`Optional fields must be non-empty strings: ${e.w}`);
    }
    if (!ID_PATTERN.test(e.id || '')) throw new Error(`Invalid id for ${e.w}: ${e.id}`);
    if (ids.has(e.id)) throw new Error(`Duplicate dictionary id: ${e.id}`);
    if (words.has(e.w)) throw new Error(`Duplicate dictionary word: ${e.w}`);
    ids.add(e.id); words.add(e.w);
    if (!CATS.includes(e.cat)) throw new Error(`Unknown category for ${e.w}: ${e.cat}`);
    if (!DATE_PATTERN.test(e.added || '') || !DATE_PATTERN.test(e.updated || '') || e.updated < e.added) {
      throw new Error(`added/updated must be dates with updated >= added: ${e.w}`);
    }
    if (!Array.isArray(e.sources)) throw new Error(`sources must be an array: ${e.w}`);
    for (const s of e.sources) {
      if (!s || !SOURCE_TYPES[s.type]) throw new Error(`Unknown source type for ${e.w}`);
      if (!isNonEmptyString(s.forms)) throw new Error(`Source must name the recorded forms: ${e.w}`);
      if (s.type === 'gunshi1921' && !isNonEmptyString(s.page)) throw new Error(`gunshi1921 needs a page: ${e.w}`);
      if (s.type === 'fpjd' && !isNonEmptyString(s.item)) throw new Error(`fpjd needs a survey item: ${e.w}`);
      if (s.type === 'hogenshu' && !isNonEmptyString(s.book)) throw new Error(`hogenshu needs a book: ${e.w}`);
      if (s.url && !/^https:\/\//.test(s.url)) throw new Error(`Source url must be https: ${e.w}`);
    }
    if (!Array.isArray(e.articles) || new Set(e.articles).size !== e.articles.length) {
      throw new Error(`articles must be a list without duplicates: ${e.w}`);
    }
    if (articleTitles) {
      for (const a of e.articles) {
        if (!articleTitles.has(a)) throw new Error(`Article is not a public search record: ${a} (${e.w})`);
      }
    }
    if (!e.karuta || !isNonEmptyString(e.karuta.scene)) throw new Error(`karuta.scene is required: ${e.w}`);
    if ('alt' in e.karuta && !isNonEmptyString(e.karuta.alt)) throw new Error(`karuta.alt must be non-empty: ${e.w}`);
  }
  return entries;
}

// 検索インデックスの公開レコードだけをリンク先として認める（佐口史料の関連記事と同じ方針）。
export function loadArticleTitles(root = ROOT) {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'data/search/manifest.json'), 'utf8'));
  const metadata = JSON.parse(fs.readFileSync(path.join(root, manifest.metadata.replace(/^\//, '')), 'utf8'));
  const titles = new Map();
  for (const r of metadata.records) titles.set(r.url.replace(/^\/+|\/+$/g, ''), { url: r.url, title: r.title });
  return titles;
}

export function karutaFiles(id) {
  return { thumb: `/${KARUTA_DIR}/${id}-300.webp`, large: `/${KARUTA_DIR}/${id}-900.webp` };
}

export function karutaReadyIds(root = ROOT) {
  const dir = path.join(root, KARUTA_DIR);
  if (!fs.existsSync(dir)) return new Set();
  const files = new Set(fs.readdirSync(dir));
  const ready = new Set();
  for (const name of files) {
    const m = name.match(/^([a-z][a-z-]*)-300\.webp$/);
    if (m && files.has(`${m[1]}-900.webp`)) ready.add(m[1]);
  }
  return ready;
}

export function checkKarutaFiles(entries, root = ROOT) {
  const dir = path.join(root, KARUTA_DIR);
  if (!fs.existsSync(dir)) return;
  const ids = new Set(entries.map(e => e.id));
  for (const name of fs.readdirSync(dir)) {
    if (name === 'README.md' || name === '.gitkeep') continue;
    const m = name.match(/^([a-z][a-z-]*)-(300|900)\.webp$/);
    if (!m) throw new Error(`Unexpected file in ${KARUTA_DIR}: ${name}`);
    if (!ids.has(m[1])) throw new Error(`Karuta image has no dictionary entry: ${name}`);
    const pair = `${m[1]}-${m[2] === '300' ? '900' : '300'}.webp`;
    if (!fs.existsSync(path.join(dir, pair))) throw new Error(`Karuta image is missing its pair: ${pair}`);
  }
}

export function karutaAlt(e) {
  return e.karuta.alt || `遠州弁かるた「${e.w}」の絵札：${e.karuta.scene}`;
}

function sourceText(s) {
  if (s.type === 'fpjd') return `${SOURCE_TYPES.fpjd.name}：質問「${s.item}」${s.recordKind === 'note' ? 'の注記に' : 'に'}${s.forms}${s.recordKind === 'note' ? 'の記録' : 'の回答'}${s.dataId ? `（data-ID ${s.dataId}）` : ''}${s.note ? `。原注：${s.note}` : ''}`;
  if (s.type === 'gunshi1921') return `${SOURCE_TYPES.gunshi1921.name}、${s.page}頁${s.village ? `・旧${s.village}` : ''}に「${s.forms}」の記録${s.note ? `。${s.note}` : ''}`;
  if (s.type === 'hogenshu') return `${s.book}に「${s.forms}」の記載`;
  return `${SOURCE_TYPES.reader.name}：${s.forms}`;
}

function shortTitle(title) {
  return title.split(/\s*(?:──|—|｜)\s*/u)[0].trim() || title;
}

export function renderEntry(e, { ready = false, headChar, articleTitles = null } = {}) {
  const id = escapeHtml(e.id);
  const files = karutaFiles(e.id);
  const karuta = ready
    ? `      <figure class="karuta karuta-ready">
        <a class="karuta-zoom" href="${files.large}"><img src="${files.thumb}" width="300" height="400" loading="lazy" decoding="async" alt="${escapeHtml(karutaAlt(e))}"></a>
        <figcaption class="karuta-credit">絵札：磐田物語</figcaption>
      </figure>`
    : `      <figure class="karuta karuta-pending" role="img" aria-label="${escapeHtml(`遠州弁かるた「${e.w}」の絵札（準備中）`)}">
        <span class="karuta-kana" aria-hidden="true">${escapeHtml(headChar)}</span>
        <figcaption class="karuta-status" aria-hidden="true">絵札準備中</figcaption>
      </figure>`;
  const badges = e.sources.length ? `
          <span class="src-badges">${e.sources.map(s => `<span class="src-badge src-${escapeHtml(s.type)}" title="${escapeHtml(sourceText(s))}">${escapeHtml(SOURCE_TYPES[s.type].label)}</span>`).join('')}</span>` : '';
  const note = e.n ? `
        <p class="note-word"><span class="label">解説</span>${escapeHtml(e.n)}</p>` : '';
  const sources = e.sources.length ? `
        <p class="word-src"><span class="label">資料</span>${e.sources.map(s => s.url
    ? `<a href="${escapeHtml(s.url)}" rel="noopener">${escapeHtml(sourceText(s))}</a>`
    : escapeHtml(sourceText(s))).join('／')}</p>` : '';
  const articles = e.articles.length ? `
        <p class="word-links"><span class="label">記事</span>${e.articles.map(a => {
    const rec = articleTitles && articleTitles.get(a);
    const href = rec ? rec.url : `/${a}`;
    return `<a href="${escapeHtml(href)}">${escapeHtml(rec ? shortTitle(rec.title) : a)}</a>`;
  }).join('、')}</p>` : '';
  return `    <div class="entry" id="w-${escapeHtml(e.w)}" data-id="${id}">
      <span class="word-anchor" id="${id}" aria-hidden="true"></span>
${karuta}
      <div class="entry-body">
        <div class="top">
          <span class="word">${escapeHtml(e.w)}</span>
          <span class="kana">${escapeHtml(e.k)}</span>${badges}
          <span class="cat">${escapeHtml(e.cat)}</span>
        </div>
        <p class="mean">${escapeHtml(e.m)}</p>
        <div class="ex">
          <span class="label">使用例</span><span class="example">${escapeHtml(e.ex)}</span>
          <span class="std">＝ ${escapeHtml(e.std)}</span>
        </div>${note}${sources}${articles}
      </div>
    </div>`;
}

export function sortEntries(entries, sortKey) {
  return entries.slice().sort((a, b) => sortKey(a.k).localeCompare(sortKey(b.k), 'ja'));
}

export function headCharOf(e, sortKey) {
  return Array.from(sortKey(e.k))[0] || Array.from(e.w)[0];
}

export function renderEntries(entries, { sortKey, ready = new Set(), articleTitles = null }) {
  return sortEntries(entries, sortKey)
    .map(e => renderEntry(e, { ready: ready.has(e.id), headChar: headCharOf(e, sortKey), articleTitles }))
    .join('\n');
}

const JS_FIELDS = ['id', ...FIELDS, ...OPTIONAL_FIELDS];
export function renderData(entries) {
  // ページの検索・絞り込みが使う項目だけを、元の並び（JSONの並び）で書き出す。
  const lines = entries.map(e => '  ' + JSON.stringify(Object.fromEntries(JS_FIELDS.filter(f => f in e).map(f => [f, e[f]]))).replace(/</g, '\\u003c'));
  return `const DATA = [\n${lines.join(',\n')}\n];`;
}

export function renderTerms(entries, sortKey) {
  const set = `${SITE}/c006#terms`;
  const terms = sortEntries(entries, sortKey).map(e => {
    const readings = e.k.split(/[／/]/u).map(r => r.trim()).filter(r => r && r !== e.w);
    const term = { '@type': 'DefinedTerm', '@id': `${SITE}/c006#${e.id}`, name: e.w };
    if (readings.length) term.alternateName = readings;
    term.description = e.m;
    term.termCode = e.id;
    term.url = `${SITE}/c006#${e.id}`;
    term.inDefinedTermSet = { '@id': set };
    return term;
  });
  const doc = {
    '@context': 'https://schema.org',
    '@type': 'DefinedTermSet',
    '@id': set,
    name: '遠州弁辞典 ── 磐田・中遠のことば',
    description: `磐田・中遠地域を中心とした遠州弁${entries.length}語。用例は編集部の作例。`,
    url: `${SITE}/c006`,
    inLanguage: 'ja',
    hasDefinedTerm: terms,
  };
  // </script> を閉じないよう、< をエスケープする。
  return `<script type="application/ld+json" id="c006-terms">\n${JSON.stringify(doc, null, 1).replace(/</g, '\\u003c')}\n</script>`;
}

export function renderWordIds(entries) {
  return `// 生成ファイル（tools/build_c006_dictionary.mjs）。手で編集しない。\n// 読者調査（/api/kotoba/*）で受け付ける遠州弁辞典の語ID。\nexport const WORD_IDS = new Set(${JSON.stringify(entries.map(e => e.id).sort())});\n`;
}

function csvCell(v) {
  const s = String(v ?? '');
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function renderKarutaSheet(entries, { sortKey, ready = new Set() }) {
  const header = ['id', '語', '読み', '分類', '頭の字', '読み札（作例）', '絵の場面', 'alt', '元画ファイル名', '配信ファイル（300px）', '配信ファイル（900px）', '状態'];
  const rows = sortEntries(entries, sortKey).map(e => {
    const f = karutaFiles(e.id);
    return [e.id, e.w, e.k, e.cat, headCharOf(e, sortKey), e.ex, e.karuta.scene, karutaAlt(e), `${e.id}.png`, f.thumb, f.large, ready.has(e.id) ? '公開済み' : '未制作'];
  });
  return '\ufeff' + [header, ...rows].map(r => r.map(csvCell).join(',')).join('\r\n') + '\r\n';
}

function replaceBetween(text, start, end, body, label) {
  if (text.split(start).length !== 2 || text.split(end).length !== 2) throw new Error(`Expected one ${label} marker pair`);
  const a = text.indexOf(start) + start.length;
  const b = text.indexOf(end);
  if (b < a) throw new Error(`${label} markers are reversed`);
  return text.slice(0, a) + body + text.slice(b);
}

// 語数を含む本文の数字は手で書くので、生成時に食い違いを止める。
export function checkCounts(html, n) {
  const checks = [
    [new RegExp(`id="count" role="status">${n} 語<`), '辞典上部の件数表示'],
    [new RegExp(`<title>[^<]*｜${n}語の`), 'title'],
    [new RegExp(`id="dictionary-offline-note">遠州弁${n}語を`), 'JavaScriptなしの案内文'],
    [new RegExp(`下の${n}語を五十音順`), '一覧の案内文'],
  ];
  for (const [re, label] of checks) if (!re.test(html)) throw new Error(`${label}の語数が${n}語と一致しません`);
}

export function generateHtml(html, json, { ready = new Set(), articleTitles = null } = {}) {
  const entries = validateDictionary(json, { articleTitles });
  const sortKey = sortKeyFunction(html);
  checkCounts(html, entries.length);
  const eol = html.includes('\r\n') ? '\r\n' : '\n';
  const nl = s => s.replaceAll('\r\n', '\n').replaceAll('\n', eol);
  let out = replaceBetween(html, START, END,
    eol + nl(renderEntries(entries, { sortKey, ready, articleTitles })) + eol + '  ', 'dictionary');
  out = replaceBetween(out, DATA_START, DATA_END, eol + nl(renderData(entries)) + eol, 'data');
  out = replaceBetween(out, TERMS_START, TERMS_END, eol + nl(renderTerms(entries, sortKey)) + eol, 'terms');
  return out;
}

export function readJson(root = ROOT) {
  return JSON.parse(fs.readFileSync(path.join(root, 'data/c006-dictionary.json'), 'utf8'));
}

export function buildDictionary({ root = ROOT, check = false } = {}) {
  const json = readJson(root);
  const entries = validateDictionary(json);
  checkKarutaFiles(entries, root);
  const ready = karutaReadyIds(root);
  const articleTitles = loadArticleTitles(root);
  const htmlFile = path.join(root, 'c006.html');
  const before = fs.readFileSync(htmlFile, 'utf8');
  const sortKey = sortKeyFunction(before);
  const outputs = [
    [htmlFile, before, generateHtml(before, json, { ready, articleTitles })],
    [path.join(root, 'functions/api/kotoba/_words.js'), null, renderWordIds(entries)],
    [path.join(root, 'docs/karuta/c006-karuta-sheet.csv'), null, renderKarutaSheet(entries, { sortKey, ready })],
  ];
  const changed = [];
  for (const [file, current, next] of outputs) {
    const now = current ?? (fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null);
    if (now === next) continue;
    changed.push(path.relative(root, file));
    if (!check) {
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, next, 'utf8');
    }
  }
  if (check && changed.length) throw new Error(`c006 generated files are stale (${changed.join(', ')}); run node tools/build_c006_dictionary.mjs`);
  return { changed, count: entries.length, ready: ready.size };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.slice(2).some(arg => arg !== '--check')) throw new Error('Usage: node tools/build_c006_dictionary.mjs [--check]');
    const check = process.argv.includes('--check');
    const { changed, count, ready } = buildDictionary({ check });
    console.log(`c006 dictionary: ${count} entries, karuta ${ready}/${count} ${check ? 'verified' : changed.length ? `generated (${changed.join(', ')})` : 'unchanged'}`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
