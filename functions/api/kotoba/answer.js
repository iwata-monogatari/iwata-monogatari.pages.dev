// 配置先: /functions/api/kotoba/answer.js
// 磐田ことば調査の回答を記録する。1端末1語1回答で、答え直しは上書き。
import { json, nowIso, hashIp, validAnswer, ensureTables, readJson, summarize, AGGREGATE_SQL, DAILY_LIMIT_PER_IP } from "./_lib.js";

export async function onRequestPost({ request, env }) {
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 500);
  const a = validAnswer(await readJson(request));
  if (!a) return json({ ok: false, error: "不正なリクエストです。" }, 400);
  const ipHash = await hashIp(request.headers.get("CF-Connecting-IP"), env.BBS_IP_SALT);
  const now = nowIso();

  try {
    await ensureTables(env.DB);
    if (ipHash) {
      const since = new Date(Date.now() - 86400000).toISOString();
      const used = await env.DB.prepare(
        "SELECT COUNT(*) AS n FROM kotoba_survey WHERE ip_hash = ?1 AND updated_at >= ?2"
      ).bind(ipHash, since).first();
      if (used && Number(used.n) >= DAILY_LIMIT_PER_IP) {
        return json({ ok: false, error: "回答が多すぎます。時間をおいてお試しください。" }, 429);
      }
    }
    await env.DB.prepare(
      `INSERT INTO kotoba_survey (word_id, answer, district, generation, visitor_id, ip_hash, internal, created_at, updated_at)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?8)
       ON CONFLICT (word_id, visitor_id) DO UPDATE SET
         answer = excluded.answer, district = excluded.district, generation = excluded.generation,
         ip_hash = excluded.ip_hash, internal = excluded.internal, updated_at = excluded.updated_at`
    ).bind(a.word, a.answer, a.district, a.generation, a.vid, ipHash, a.internal, now).run();
    const rows = await env.DB.prepare(
      `${AGGREGATE_SQL} AND word_id = ?1 GROUP BY word_id, answer, generation, district`
    ).bind(a.word).all();
    const stats = summarize(rows.results || [])[a.word] || { n: 0 };
    return json({ ok: true, stats });
  } catch (e) {
    return json({ ok: false, error: "保存に失敗しました。" }, 500);
  }
}
