// 配置先: /functions/api/reactions/counts.js
// アクセスダッシュボード用：サイト別の反応件数（今日・7日）だけを返す。一言の中身や記事名は返さない。
// 自分のアクセス（internal）は数えない。「今日」は日本時間の0時から。
import { json, ensureTables, PARTNER_SITES } from "./_lib.js";

function siteOf(path) {
  for (const [site, origin] of Object.entries(PARTNER_SITES)) {
    if (path.startsWith(origin + "/")) return site;
  }
  return "iwata";
}

export async function onRequestGet({ env }) {
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 500);
  const jstNow = new Date(Date.now() + 9 * 3600000);
  const todayStart = new Date(Date.UTC(jstNow.getUTCFullYear(), jstNow.getUTCMonth(), jstNow.getUTCDate()) - 9 * 3600000).toISOString();
  const weekStart = new Date(Date.parse(todayStart) - 6 * 86400000).toISOString();

  try {
    await ensureTables(env.DB);
    const [reactions, notes] = await Promise.all([
      env.DB.prepare(
        `SELECT path, updated_at >= ?1 AS today FROM article_reactions
         WHERE internal = 0 AND updated_at >= ?2`
      ).bind(todayStart, weekStart).all(),
      env.DB.prepare(
        `SELECT path, created_at >= ?1 AS today FROM article_reaction_notes
         WHERE internal = 0 AND created_at >= ?2`
      ).bind(todayStart, weekStart).all(),
    ]);
    const sites = {};
    const bucket = (s) => (sites[s] ||= { today: 0, week: 0, notes_today: 0, notes_week: 0 });
    for (const r of reactions.results || []) {
      const b = bucket(siteOf(r.path)); b.week++; if (r.today) b.today++;
    }
    for (const n of notes.results || []) {
      const b = bucket(siteOf(n.path)); b.notes_week++; if (n.today) b.notes_today++;
    }
    for (const s of ["iwata", ...Object.keys(PARTNER_SITES)]) bucket(s);
    return json({ ok: true, since_today: todayStart, sites });
  } catch (e) {
    return json({ ok: false, error: "取得に失敗しました。" }, 500);
  }
}
