const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const ROOT = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(ROOT, "c006.html"), "utf8");

function extract(pattern, label) {
  const match = html.match(pattern);
  assert.ok(match, `${label} was not found in c006.html`);
  return match[1];
}

const dataSource = extract(/const DATA = (\[[\s\S]*?\n\]);/, "dictionary data");
const sortKeySource = extract(
  /(function dictionarySortKey\(reading\)\{[\s\S]*?\n\})/,
  "dictionarySortKey"
);
const DATA = vm.runInNewContext(dataSource);
const dictionarySortKey = vm.runInNewContext(
  `${sortKeySource}; dictionarySortKey`
);

function sortedWords() {
  return [...DATA]
    .sort((a, b) =>
      dictionarySortKey(a.k).localeCompare(dictionarySortKey(b.k), "ja")
    )
    .map((entry) => entry.w);
}

test("comparison keys ignore leading wave dashes and secondary readings", () => {
  assert.equal(dictionarySortKey("〜ごう"), "ごう");
  assert.equal(dictionarySortKey("～まい／～まいか"), "まい");
  assert.equal(dictionarySortKey("~ない"), "ない");
  assert.equal(dictionarySortKey("あんも／あんもう"), "あんも");
  assert.equal(dictionarySortKey("ぼう／ぼっかける"), "ぼう");
});

test("all 79 entries remain and begin in Japanese syllabary order", () => {
  const words = sortedWords();
  assert.equal(DATA.length, 79);
  assert.equal(new Set(words).size, 79);
  assert.deepEqual(words.slice(0, 8), [
    "あいさ",
    "頭を切る",
    "あんも",
    "いいにする",
    "いずようない",
    "いっちょ",
    "いのく",
    "いぼる",
  ]);
});

test("existing variants with marks, voiced sounds and small kana keep stable positions", () => {
  const words = sortedWords();
  const position = (word) => words.indexOf(word);

  assert.ok(position("けんが") < position("ごう"));
  assert.ok(position("ごう") < position("こさえる"));
  assert.ok(position("っち") < position("っちゅう"));
  assert.ok(position("ど") < position("とぶ"));
  assert.ok(position("とぶ") < position("どべ"));
  assert.ok(position("ぼっかける") < position("ぽんぽん"));
  assert.ok(position("ぽんぽん") < position("まい"));
});
