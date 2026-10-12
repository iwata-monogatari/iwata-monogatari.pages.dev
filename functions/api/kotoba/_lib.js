// 配置先: /functions/api/kotoba/_lib.js
// 磐田ことば調査（遠州弁辞典 /c006 の語ごとの「使う／聞いたことがある／知らない」）の共通処理。
// 記事の反応ボタン（/api/reactions）とは別の表に記録し、共通部分は変更しない。
export { json, nowIso, hashIp } from "../bbs/_lib.js";
import { WORD_IDS } from "./_words.js";
export { WORD_IDS };

export const ANSWERS = ["use", "heard", "unknown"];
export const DISTRICTS = ["mitsuke", "nakaizumi", "mikuriya", "toyoda", "nanbu", "koyo", "ryuyo", "fukude", "toyooka", "outside", "none"];
export const GENERATIONS = ["10s", "20s", "30s", "40s", "50s", "60s", "70s", "80s", "none"];

// 公開のしきい値：語ごとに回答30件で割合を出し、地区・世代の内訳は5件以上の区分だけ出す。
export const MIN_TOTAL = 30;
export const MIN_CELL = 5;
// 1つのIPから1日に受け付ける回答の上限（全語に答えても収まる数）
export const DAILY_LIMIT_PER_IP = 400;

export function validVisitorId(v) {
  return typeof v === "string" && /^[a-z0-9]{16,40}$/i.test(v);
}

export function validAnswer(body) {
  if (!body || typeof body !== "object") return null;
  const { word, answer, vid } = body;
  const district = body.district || "none";
  const generation = body.generation || "none";
  if (!WORD_IDS.has(word) || !ANSWERS.includes(answer) || !validVisitorId(vid)) return null;
  if (!DISTRICTS.includes(district) || !GENERATIONS.includes(generation)) return null;
  return { word, answer, vid, district, generation, internal: body.internal ? 1 : 0 };
}

// 表が無ければ作る（migrations/0003_kotoba_survey.sql と同じ定義）。
// 個別の回答は集計と二重回答の防止にだけ使い、APIでは返さない。
let tablesReady = false;
export async function ensureTables(db) {
  if (tablesReady) return;
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS kotoba_survey (
      id INTEGER PRIMARY KEY AUTOINCREMENT, word_id TEXT NOT NULL,
      answer TEXT NOT NULL CHECK (answer IN ('use','heard','unknown')),
      district TEXT NOT NULL DEFAULT 'none', generation TEXT NOT NULL DEFAULT 'none',
      visitor_id TEXT NOT NULL, ip_hash TEXT, internal INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE (word_id, visitor_id))`),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_kotoba_survey_word ON kotoba_survey (word_id)"),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_kotoba_survey_ip ON kotoba_survey (ip_hash, updated_at)"),
  ]);
  tablesReady = true;
}

export async function readJson(request) {
  try {
    return await request.json();
  } catch (e) {
    return null;
  }
}

// 最大剰余法で、合計がちょうど100になる整数の百分率にする。
export function percentages(counts, total) {
  const keys = Object.keys(counts);
  const raw = keys.map((k) => (counts[k] * 100) / total);
  const floor = raw.map(Math.floor);
  let rest = 100 - floor.reduce((a, b) => a + b, 0);
  const order = raw.map((v, i) => [v - floor[i], i]).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  for (const [, i] of order) { if (rest <= 0) break; floor[i]++; rest--; }
  return Object.fromEntries(keys.map((k, i) => [k, floor[i]]));
}

// rows: { word_id, answer, generation, district, n } の集計行。個別の回答は受け取らない。
export function summarize(rows) {
  const words = {};
  for (const r of rows) {
    const w = (words[r.word_id] ||= { n: 0, counts: { use: 0, heard: 0, unknown: 0 }, gen: {}, district: {} });
    const n = Number(r.n) || 0;
    w.n += n;
    w.counts[r.answer] = (w.counts[r.answer] || 0) + n;
    for (const [key, value] of [["gen", r.generation], ["district", r.district]]) {
      const cell = (w[key][value] ||= { n: 0, use: 0 });
      cell.n += n;
      if (r.answer === "use") cell.use += n;
    }
  }
  const out = {};
  for (const [id, w] of Object.entries(words)) {
    if (w.n < MIN_TOTAL) { out[id] = { n: w.n }; continue; }
    const cells = (group) => Object.fromEntries(Object.entries(group)
      .filter(([k, c]) => k !== "none" && c.n >= MIN_CELL)
      .map(([k, c]) => [k, { n: c.n, use: Math.round((c.use * 100) / c.n) }]));
    out[id] = { n: w.n, share: percentages(w.counts, w.n), gen: cells(w.gen), district: cells(w.district) };
  }
  return out;
}

export const AGGREGATE_SQL = `SELECT word_id, answer, generation, district, COUNT(*) AS n
  FROM kotoba_survey WHERE internal = 0`;
