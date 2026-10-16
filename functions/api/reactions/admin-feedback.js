import { json, isAdmin, PARTNER_SITES } from "./_lib.js";
import { ensureFeedbackTables, feedbackPeriod } from "./_feedback.js";

export async function onRequestGet({ request, env }) {
  if (!(await isAdmin(request, env))) return json({ ok: false, error: "認証が必要です。" }, 401);
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 503);
  const url = new URL(request.url);
  const site = url.searchParams.get("site") || "oishi";
  if (!["iwata", "oishi", "all"].includes(site)) return json({ ok: false, error: "サイトの指定が正しくありません。" }, 400);
  const { days, today, since } = feedbackPeriod(url.searchParams);
  const pattern = site === "all" ? "%" : site === "iwata" ? "/%" : PARTNER_SITES.oishi + "/%";
  const internal = url.searchParams.get("internal") === "1" ? "" : "AND internal = 0";
  try {
    await ensureFeedbackTables(env.DB);
    const rows = await env.DB.prepare(`SELECT path, MAX(title) AS title, question_id, question_version,
        ui_version, article_type, device,
        SUM(CASE WHEN reaction_at >= ?1 THEN 1 ELSE 0 END) AS reactions,
        SUM(CASE WHEN preference_at >= ?1 THEN 1 ELSE 0 END) AS answers,
        SUM(CASE WHEN preference_at >= ?1 AND preference = 'list' THEN 1 ELSE 0 END) AS list,
        SUM(CASE WHEN preference_at >= ?1 AND preference = 'diagram' THEN 1 ELSE 0 END) AS diagram,
        SUM(CASE WHEN preference_at >= ?1 AND preference = 'qa' THEN 1 ELSE 0 END) AS qa,
        MAX(updated_at) AS last_at
      FROM article_feedback_answers
      WHERE updated_at >= ?1 AND path LIKE ?2 ${internal}
      GROUP BY path, question_id, question_version, ui_version, article_type, device
      ORDER BY last_at DESC LIMIT 500`).bind(since, pattern).all();
    return json({ ok: true, site, days, today, unit: "article-session", rows: rows.results || [],
      measurement: "表示数と反応率はGA4のarticle_feedback_*イベントで確認します。D1には回答だけを保存します。" });
  } catch (error) {
    console.error("article-feedback-summary-failed", error && error.message);
    return json({ ok: false, error: "希望する見せ方を取得できませんでした。" }, 500);
  }
}
