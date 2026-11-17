// トークン不要の反応集計。非公開の一言本文・端末ID・IP情報は返さない。
import { json, ensureTables, PARTNER_SITES } from "./_lib.js";

export async function onRequestGet({ request, env }) {
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 500);
  const url = new URL(request.url);
  const site = url.searchParams.get("site") || "iwata";
  if (!["iwata", "all", ...Object.keys(PARTNER_SITES)].includes(site)) {
    return json({ ok: false, error: "サイトの指定が正しくありません。" }, 400);
  }
  const requestedDays = Number(url.searchParams.get("days") ?? "30");
  const days = [0, 7, 30, 90].includes(requestedDays) ? requestedDays : 30;
  const today = new Date(Date.now() + 9 * 3600000).toISOString().slice(0, 10);
  const since = days
    ? new Date(Date.parse(today + "T00:00:00+09:00") - (days - 1) * 86400000).toISOString()
    : "0000";
  const pathPattern = site === "all" ? "%" : site === "iwata" ? "/%" : PARTNER_SITES[site] + "/%";
  const where = "internal = 0 AND updated_at >= ?1 AND path LIKE ?2";
  try {
    await ensureTables(env.DB);
    const [pages, daily, totals] = await Promise.all([
      env.DB.prepare(`SELECT path, MAX(title) AS title,
          SUM(reaction = 'learned') AS learned, SUM(reaction = 'local') AS local,
          SUM(reaction = 'more') AS more, COUNT(*) AS total, MAX(updated_at) AS last_at
        FROM article_reactions WHERE ${where}
        GROUP BY path ORDER BY total DESC, last_at DESC LIMIT 500`).bind(since, pathPattern).all(),
      env.DB.prepare(`SELECT date(updated_at, '+9 hours') AS day, COUNT(*) AS n
        FROM article_reactions WHERE ${where} GROUP BY day ORDER BY day`).bind(since, pathPattern).all(),
      env.DB.prepare(`SELECT COUNT(*) AS reactions,
          COALESCE(SUM(reaction = 'learned'), 0) AS learned,
          COALESCE(SUM(reaction = 'local'), 0) AS local,
          COALESCE(SUM(reaction = 'more'), 0) AS more,
          (SELECT COUNT(*) FROM article_reaction_notes
            WHERE internal = 0 AND created_at >= ?1 AND path LIKE ?2) AS notes
        FROM article_reactions WHERE ${where}`).bind(since, pathPattern).first(),
    ]);
    return json({ ok: true, site, days, today, totals, pages: pages.results || [], daily: daily.results || [] });
  } catch (e) {
    console.error("reaction-summary-failed", e && e.message);
    return json({ ok: false, error: "反応の取得に失敗しました。再読み込みしてください。" }, 500);
  }
}
