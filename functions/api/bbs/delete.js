// 配置先: /functions/api/bbs/delete.js
// 管理者用: 投稿を deleted 扱いにする（物理削除はしない）。トークン保護。
import { json, nowIso, sanitizeText, checkAdminToken } from "./_lib.js";

export async function onRequestPost({ request, env }) {
  if (!checkAdminToken(request, env)) {
    return json({ ok: false, error: "認証が必要です。" }, 401);
  }
  if (!env.DB) {
    return json({ ok: false, error: "データベース未設定です。" }, 500);
  }

  let payload;
  try {
    payload = await request.json();
  } catch (e) {
    return json({ ok: false, error: "送信形式が正しくありません。" }, 400);
  }

  const id = parseInt(payload.id, 10);
  if (!id || id < 1) {
    return json({ ok: false, error: "対象IDが不正です。" }, 400);
  }
  const reason = sanitizeText(payload.reason, 200) || null;
  const now = nowIso();

  try {
    const res = await env.DB.prepare(
      `UPDATE bbs_posts
       SET status = 'deleted', deleted_at = ?, deleted_reason = ?, updated_at = ?
       WHERE id = ?`
    ).bind(now, reason, now, id).run();
    const changed = res.meta && res.meta.changes ? res.meta.changes : 0;
    if (!changed) return json({ ok: false, error: "対象の投稿が見つかりません。" }, 404);
    return json({ ok: true, id, status: "deleted" });
  } catch (e) {
    return json({ ok: false, error: "更新に失敗しました。" }, 500);
  }
}
