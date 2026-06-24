// 配置先: /functions/api/bbs/hide.js
// 管理者用: 投稿を hidden / published に切り替える。トークン保護。
import { json, nowIso, checkAdminToken } from "./_lib.js";

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
  // hidden にするか、再公開(published)に戻すか
  const target = payload.status === "published" ? "published" : "hidden";

  try {
    const res = await env.DB.prepare(
      `UPDATE bbs_posts SET status = ?, updated_at = ? WHERE id = ?`
    ).bind(target, nowIso(), id).run();
    const changed = res.meta && res.meta.changes ? res.meta.changes : 0;
    if (!changed) return json({ ok: false, error: "対象の投稿が見つかりません。" }, 404);
    return json({ ok: true, id, status: target });
  } catch (e) {
    return json({ ok: false, error: "更新に失敗しました。" }, 500);
  }
}
