// 配置先: /functions/api/reactions/admin-summary.js
// 管理者用: 記事別の反応数・日別推移・届いた一言。BBS_ADMIN_TOKEN で保護。
// ?days=7|30|90|0(全期間)  ?internal=1 で自分のアクセスも含める
import { json, checkAdminToken, ensureTables } from "./_lib.js";

export async function onRequestGet({ request, env }) {
  if (!checkAdminToken(request, env)) return json({ ok: false, error: "認証が必要です。" }, 401);
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 500);

  const url = new URL(request.url);
  const days = Math.max(0, Math.min(3650, parseInt(url.searchParams.get("days") || "30", 10) || 0));
  const includeInternal = url.searchParams.get("internal") === "1";
  const since = days ? new Date(Date.now() - days * 86400000).toISOString() : "0000";
  const internalCond = includeInternal ? "" : " AND internal = 0";

  try {
    await ensureTables(env.DB);
    const [pages, daily, notes, totals] = await Promise.all([
      env.DB.prepare(
        `SELECT path, MAX(title) AS title,
                SUM(reaction = 'learned') AS learned,
                SUM(reaction = 'local') AS local,
                SUM(reaction = 'more') AS more,
                COUNT(*) AS total,
                MAX(updated_at) AS last_at
         FROM article_reactions
         WHERE updated_at >= ?1${internalCond}
         GROUP BY path
         ORDER BY total DESC, last_at DESC
         LIMIT 500`
      ).bind(since).all(),
      env.DB.prepare(
        `SELECT substr(updated_at, 1, 10) AS day, COUNT(*) AS n
         FROM article_reactions
         WHERE updated_at >= ?1${internalCond}
         GROUP BY day ORDER BY day`
      ).bind(since).all(),
      env.DB.prepare(
        `SELECT id, path, title, reaction, note, internal, created_at
         FROM article_reaction_notes
         WHERE created_at >= ?1${internalCond}
         ORDER BY created_at DESC LIMIT 300`
      ).bind(since).all(),
      env.DB.prepare(
        `SELECT
           (SELECT COUNT(*) FROM article_reactions WHERE updated_at >= ?1${internalCond}) AS reactions,
           (SELECT COUNT(DISTINCT visitor_id) FROM article_reactions WHERE updated_at >= ?1${internalCond}) AS visitors,
           (SELECT COUNT(*) FROM article_reaction_notes WHERE created_at >= ?1${internalCond}) AS notes`
      ).bind(since).first(),
    ]);
    return json({
      ok: true,
      days,
      totals: totals || {},
      pages: pages.results || [],
      daily: daily.results || [],
      notes: notes.results || [],
    });
  } catch (e) {
    return json({ ok: false, error: "取得に失敗しました。" }, 500);
  }
}
