// 配置先: /functions/api/reactions/react.js
// 反応ボタンの記録。1端末1記事1票で、押し直しは上書き。
import { json, nowIso, sanitizeText, hashIp, REACTIONS, storedPath, validVisitorId, readJson, ensureTables } from "./_lib.js";

export async function onRequestPost({ request, env }) {
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 500);
  const body = await readJson(request);
  if (!body) return json({ ok: false, error: "不正なリクエストです。" }, 400);

  const path = storedPath(body, request);
  const reaction = body.reaction;
  if (!path || !REACTIONS.includes(reaction) || !validVisitorId(body.vid)) {
    return json({ ok: false, error: "不正なリクエストです。" }, 400);
  }
  const title = sanitizeText(body.title || "", 200);
  const internal = body.internal ? 1 : 0;
  const ipHash = await hashIp(request.headers.get("CF-Connecting-IP"), env.BBS_IP_SALT);
  const now = nowIso();

  try {
    await ensureTables(env.DB);
    await env.DB.prepare(
      `INSERT INTO article_reactions (path, title, reaction, visitor_id, ip_hash, internal, created_at, updated_at)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?7)
       ON CONFLICT (path, visitor_id) DO UPDATE SET
         reaction = excluded.reaction, title = excluded.title,
         internal = excluded.internal, updated_at = excluded.updated_at`
    ).bind(path, title, reaction, body.vid, ipHash, internal, now).run();
    return json({ ok: true });
  } catch (e) {
    return json({ ok: false, error: "保存に失敗しました。" }, 500);
  }
}
