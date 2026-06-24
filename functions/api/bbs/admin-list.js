// 配置先: /functions/api/bbs/admin-list.js
// 管理者用: published / hidden / deleted すべての投稿を取得する。トークン保護。
import { json, checkAdminToken } from "./_lib.js";

export async function onRequestGet({ request, env }) {
  if (!checkAdminToken(request, env)) {
    return json({ ok: false, error: "認証が必要です。" }, 401);
  }
  if (!env.DB) {
    return json({ ok: false, error: "データベース未設定です。", posts: [] }, 500);
  }
  try {
    const { results } = await env.DB.prepare(
      `SELECT id, name, area, body, related_url, status,
              ip_hash, created_at, updated_at, deleted_at, deleted_reason
       FROM bbs_posts
       ORDER BY created_at DESC, id DESC
       LIMIT 300`
    ).all();
    return json({ ok: true, posts: results || [] });
  } catch (e) {
    return json({ ok: false, error: "取得に失敗しました。", posts: [] }, 500);
  }
}
