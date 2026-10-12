// 磐田ことば調査 API（functions/api/kotoba/*）のテスト。
// D1 の代わりに node:sqlite のメモリDBを使う。
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { DatabaseSync } from "node:sqlite";
import { fileURLToPath } from "node:url";

import { onRequestPost } from "../functions/api/kotoba/answer.js";
import { onRequestGet } from "../functions/api/kotoba/stats.js";
import { validAnswer, percentages, summarize, MIN_TOTAL, MIN_CELL, DAILY_LIMIT_PER_IP, WORD_IDS } from "../functions/api/kotoba/_lib.js";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MIGRATION = fs.readFileSync(path.join(ROOT, "migrations/0003_kotoba_survey.sql"), "utf8");

function d1() {
  const db = new DatabaseSync(":memory:");
  db.exec(MIGRATION);
  // D1 と同じく、SQL は実行するときに解釈する（prepare の時点では表の有無を問わない）。
  const wrap = (sql) => {
    const make = (args) => ({
      bind: (...next) => make(next),
      run: async () => db.prepare(sql).run(...args),
      first: async () => db.prepare(sql).get(...args) ?? null,
      all: async () => ({ results: db.prepare(sql).all(...args) }),
    });
    return make([]);
  };
  return { prepare: wrap, batch: async (list) => { const out = []; for (const s of list) out.push(await s.run()); return out; }, raw: db };
}

let ip = 0;
function post(env, body, { addr } = {}) {
  const request = new Request("https://iwata-monogatari.net/api/kotoba/answer", {
    method: "POST",
    headers: { "Content-Type": "application/json", "CF-Connecting-IP": addr || `10.0.${Math.floor(ip / 250)}.${ip++ % 250}` },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
  return onRequestPost({ request, env });
}
const vid = (n) => `visitor${String(n).padStart(12, "0")}`;
const base = { word: "dara", answer: "use", district: "mitsuke", generation: "60s" };

test("the accepted word ids are exactly the dictionary ids", () => {
  const entries = JSON.parse(fs.readFileSync(path.join(ROOT, "data/c006-dictionary.json"), "utf8")).entries;
  assert.deepEqual([...WORD_IDS].sort(), entries.map((e) => e.id).sort());
});

test("validAnswer accepts only known words, answers, districts, generations and visitor ids", () => {
  assert.ok(validAnswer({ ...base, vid: vid(1) }));
  assert.equal(validAnswer({ ...base, vid: vid(1), district: undefined, generation: undefined }).district, "none");
  for (const bad of [{ word: "nosuchword" }, { answer: "maybe" }, { vid: "short" }, { district: "tokyo" }, { generation: "90s" }]) {
    assert.equal(validAnswer({ ...base, vid: vid(1), ...bad }), null, JSON.stringify(bad));
  }
  assert.equal(validAnswer(null), null);
});

test("percentages always add up to 100", () => {
  assert.deepEqual(percentages({ use: 1, heard: 1, unknown: 1 }, 3), { use: 34, heard: 33, unknown: 33 });
  for (let a = 0; a < 20; a++) for (let b = 0; b < 20; b++) {
    const total = a + b + 7;
    const p = percentages({ use: a, heard: b, unknown: 7 }, total);
    assert.equal(p.use + p.heard + p.unknown, 100);
  }
});

test("summarize hides shares under 30 answers and breakdown cells under 5", () => {
  const few = summarize([{ word_id: "dara", answer: "use", generation: "60s", district: "mitsuke", n: MIN_TOTAL - 1 }]);
  assert.deepEqual(few.dara, { n: MIN_TOTAL - 1 });
  const rows = [
    { word_id: "dara", answer: "use", generation: "60s", district: "mitsuke", n: 20 },
    { word_id: "dara", answer: "heard", generation: "20s", district: "fukude", n: 6 },
    { word_id: "dara", answer: "unknown", generation: "10s", district: "toyooka", n: MIN_CELL - 1 },
  ];
  const s = summarize(rows).dara;
  assert.equal(s.n, 30);
  assert.deepEqual(s.share, { use: 67, heard: 20, unknown: 13 });
  assert.deepEqual(s.gen, { "60s": { n: 20, use: 100 }, "20s": { n: 6, use: 0 } });
  assert.deepEqual(Object.keys(s.district).sort(), ["fukude", "mitsuke"]);
});

test("one answer per visitor and word: re-answering overwrites, internal answers are not counted", async () => {
  const env = { DB: d1(), BBS_IP_SALT: "salt" };
  let res = await post(env, { ...base, vid: vid(1) });
  assert.equal(res.status, 200);
  assert.deepEqual((await res.json()).stats, { n: 1 });
  res = await post(env, { ...base, answer: "heard", vid: vid(1) });
  assert.deepEqual((await res.json()).stats, { n: 1 });
  const row = env.DB.raw.prepare("SELECT answer, ip_hash FROM kotoba_survey WHERE visitor_id = ?").get(vid(1));
  assert.equal(row.answer, "heard");
  assert.match(row.ip_hash, /^[0-9a-f]{64}$/, "only a salted hash of the IP is stored");
  res = await post(env, { ...base, vid: vid(2), internal: true });
  assert.deepEqual((await res.json()).stats, { n: 1 }, "operator access is excluded");
});

test("rejects malformed requests without writing", async () => {
  const env = { DB: d1() };
  for (const body of ["not json", { ...base, word: "nosuchword", vid: vid(1) }, { ...base, vid: "x" }]) {
    const res = await post(env, body);
    assert.equal(res.status, 400);
  }
  assert.equal(env.DB.raw.prepare("SELECT COUNT(*) AS n FROM kotoba_survey").get().n, 0);
  assert.equal((await onRequestPost({ request: new Request("https://x/api/kotoba/answer", { method: "POST", body: "{}" }), env: {} })).status, 500);
});

test("stats publish shares from 30 answers and never return visitor ids or IP hashes", async () => {
  const env = { DB: d1(), BBS_IP_SALT: "salt" };
  for (let i = 0; i < MIN_TOTAL; i++) {
    const answer = i < 18 ? "use" : i < 27 ? "heard" : "unknown";
    const generation = i < 10 ? "70s" : i < 13 ? "30s" : "none";
    await post(env, { ...base, answer, generation, vid: vid(100 + i) });
  }
  await post(env, { ...base, word: "senhiki", vid: vid(999) });
  const res = await onRequestGet({ env });
  assert.equal(res.headers.get("Cache-Control"), "public, max-age=300");
  const text = await res.text();
  assert.doesNotMatch(text, /visitor0|ip_hash|[0-9a-f]{64}/);
  const data = JSON.parse(text);
  assert.equal(data.min, MIN_TOTAL);
  assert.deepEqual(data.words.dara.share, { use: 60, heard: 30, unknown: 10 });
  assert.deepEqual(data.words.dara.gen, { "70s": { n: 10, use: 100 } }, "30s has 3 answers and 'none' is never shown");
  assert.deepEqual(data.words.senhiki, { n: 1 });
});

test("one IP address cannot submit more than the daily limit", async () => {
  const env = { DB: d1(), BBS_IP_SALT: "salt" };
  const now = new Date().toISOString();
  const { hashIp } = await import("../functions/api/bbs/_lib.js");
  const h = await hashIp("192.0.2.1", "salt");
  const insert = env.DB.raw.prepare(
    "INSERT INTO kotoba_survey (word_id, answer, visitor_id, ip_hash, created_at, updated_at) VALUES (?, 'use', ?, ?, ?, ?)"
  );
  for (let i = 0; i < DAILY_LIMIT_PER_IP; i++) insert.run("dara", vid(5000 + i), h, now, now);
  const res = await post(env, { ...base, vid: vid(1) }, { addr: "192.0.2.1" });
  assert.equal(res.status, 429);
  const other = await post(env, { ...base, vid: vid(2) }, { addr: "192.0.2.2" });
  assert.equal(other.status, 200);
});

test("the table created on first request matches the migration", async () => {
  const migrated = d1();
  const empty = d1();
  empty.raw.exec("DROP TABLE kotoba_survey");
  // 別インスタンスのモジュールで、表が無い状態から ensureTables を走らせる。
  const lib = await import(new URL("../functions/api/kotoba/_lib.js?fresh=1", import.meta.url));
  await lib.ensureTables(empty);
  const shape = (db) => ({
    columns: db.raw.prepare("PRAGMA table_info(kotoba_survey)").all().map((c) => [c.name, c.type, c.notnull, c.dflt_value, c.pk]),
    indexes: db.raw.prepare("SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'kotoba_survey' ORDER BY name").all().map((r) => r.name),
  });
  assert.deepEqual(shape(empty), shape(migrated));
});
