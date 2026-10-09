import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const START = '<!-- c006-dictionary:start -->';
export const END = '<!-- c006-dictionary:end -->';
const FIELDS = ['w', 'k', 'cat', 'm', 'ex', 'std'];

function extractOnce(html, pattern, label) {
  const matches = [...html.matchAll(pattern)];
  if (matches.length !== 1) throw new Error(`Expected exactly one ${label}`);
  return matches[0][1];
}

export function readDictionary(html) {
  // Only the existing DATA and comparison function are authoritative. Never
  // execute the page script (DOM handlers, analytics, etc.) during a build.
  const source = extractOnce(html, /const DATA = (\[[\s\S]*?\r?\n\]);/g, 'DATA array');
  const sortSource = extractOnce(html,
    /(function dictionarySortKey\(reading\)\{[\s\S]*?\r?\n\})/g, 'dictionarySortKey');
  const data = vm.runInNewContext(source, Object.create(null), { timeout: 1000 });
  if (!Array.isArray(data) || data.length !== 79) throw new Error('Expected exactly 79 dictionary entries');
  const words = new Set();
  for (const entry of data) {
    if (!entry || FIELDS.some(field => typeof entry[field] !== 'string' || !entry[field].length)) {
      throw new Error('Every dictionary entry must have six non-empty string fields');
    }
    if (words.has(entry.w)) throw new Error(`Duplicate dictionary word: ${entry.w}`);
    words.add(entry.w);
  }
  // Run the existing sort function inside the timed context, preserving every
  // field verbatim. Only the comparison key is transformed by that function.
  return Array.from(vm.runInNewContext(
    `${sortSource}\nDATA.slice().sort((a,b)=>dictionarySortKey(a.k).localeCompare(dictionarySortKey(b.k),"ja"))`,
    { DATA: data }, { timeout: 1000 }
  ));
}

export function escapeHtml(value) {
  return value.replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

export function renderEntries(entries) {
  return entries.map(d => `    <div class="entry">
      <div class="top">
        <span class="word">${escapeHtml(d.w)}</span>
        <span class="kana">${escapeHtml(d.k)}</span>
        <span class="cat">${escapeHtml(d.cat)}</span>
      </div>
      <p class="mean">${escapeHtml(d.m)}</p>
      <div class="ex">
        <span class="label">例</span><span class="example">${escapeHtml(d.ex)}</span>
        <span class="std">＝ ${escapeHtml(d.std)}</span>
      </div>
    </div>`).join('\n');
}

export function generateHtml(html) {
  if (html.split(START).length !== 2 || html.split(END).length !== 2) {
    throw new Error('Expected one dictionary marker pair');
  }
  const start = html.indexOf(START) + START.length;
  const end = html.indexOf(END);
  if (end < start) throw new Error('Dictionary markers are reversed');
  const eol = html.includes('\r\n') ? '\r\n' : '\n';
  const entries = renderEntries(readDictionary(html)).replaceAll('\n', eol);
  return html.slice(0, start) + eol + entries + eol + '  ' + html.slice(end);
}

export function buildDictionary({ file = path.join(ROOT, 'c006.html'), check = false } = {}) {
  const before = fs.readFileSync(file, 'utf8');
  const after = generateHtml(before);
  if (check && before !== after) throw new Error('c006 static dictionary is stale; run node tools/build_c006_dictionary.mjs');
  if (!check && before !== after) fs.writeFileSync(file, after, 'utf8');
  return before !== after;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.slice(2).some(arg => arg !== '--check')) throw new Error('Usage: node tools/build_c006_dictionary.mjs [--check]');
    const check = process.argv.includes('--check');
    const changed = buildDictionary({ check });
    console.log(`c006 dictionary: 79 entries ${check ? 'verified' : changed ? 'generated' : 'unchanged'}`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
