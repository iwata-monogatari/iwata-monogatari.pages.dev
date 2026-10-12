// 配置先: /functions/api/kotoba/stats.js
// 磐田ことば調査の語ごとの集計。個別の回答・端末ID・IPは返さない。
// 回答30件未満の語は件数だけ、地区・世代の内訳は5件以上の区分だけを返す。
import { json, ensureTables, summarize, AGGREGATE_SQL, MIN_TOTAL, MIN_CELL } from "./_lib.js";

export async function onRequestGet({ env }) {
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 500);
  try {
    await ensureTables(env.DB);
    const rows = await env.DB.prepare(`${AGGREGATE_SQL} GROUP BY word_id, answer, generation, district`).all();
    return json(
      { ok: true, min: MIN_TOTAL, minCell: MIN_CELL, words: summarize(rows.results || []) },
      200,
      { "Cache-Control": "public, max-age=300" }
    );
  } catch (e) {
    return json({ ok: false, error: "取得に失敗しました。" }, 500);
  }
}
