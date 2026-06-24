// 配置先: /functions/api/bbs/list.js
// 公開投稿一覧 (status = 'published') を新しい順に取得する。
import { json } from "./_lib.js";

export async function onRequestGet({ env }) {
  if (!env.DB) {
    return json({ ok: false, error: "データベース未設定です。", posts: [] }, 500);
  }
  try {
    const { results } = await env.DB.prepare(
      `SELECT id, name, area, body, related_url, created_at
       FROM bbs_posts
       WHERE status = 'published'
       ORDER BY created_at DESC, id DESC
       LIMIT 50`
    ).all();
    return json({ ok: true, posts: results || [] });
  } catch (e) {
    return json({ ok: false, error: "取得に失敗しました。", posts: [] }, 500);
  }
}
