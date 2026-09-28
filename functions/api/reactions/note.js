// 配置先: /functions/api/reactions/note.js
// 反応ボタンを押したあとの任意の一言（非公開）。IPごとに1日10件まで。
import { json, nowIso, sanitizeText, hashIp, REACTIONS, storedPath, validVisitorId, readJson, ensureTables } from "./_lib.js";

const DAILY_LIMIT = 10;

export async function onRequestPost({ request, env }) {
  if (!env.DB) return json({ ok: false, error: "データベース未設定です。" }, 500);
  const body = await readJson(request);
  if (!body) return json({ ok: false, error: "不正なリクエストです。" }, 400);

  const path = storedPath(body, request);
  const note = sanitizeText(body.note || "", 200);
  if (!path || !validVisitorId(body.vid) || !note) {
    return json({ ok: false, error: "一言を入力してください。" }, 400);
  }
  const reaction = REACTIONS.includes(body.reaction) ? body.reaction : null;
  const title = sanitizeText(body.title || "", 200);
  const internal = body.internal ? 1 : 0;
  const ipHash = await hashIp(request.headers.get("CF-Connecting-IP"), env.BBS_IP_SALT);
  const now = nowIso();

  try {
    await ensureTables(env.DB);
    if (ipHash) {
      const since = new Date(Date.now() - 86400000).toISOString();
      const row = await env.DB.prepare(
        "SELECT COUNT(*) AS n FROM article_reaction_notes WHERE ip_hash = ?1 AND created_at >= ?2"
      ).bind(ipHash, since).first();
      if (row && row.n >= DAILY_LIMIT) {
        return json({ ok: false, error: "本日の送信上限に達しました。" }, 429);
      }
    }
    await env.DB.prepare(
      `INSERT INTO article_reaction_notes (path, title, reaction, note, visitor_id, ip_hash, internal, created_at)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)`
    ).bind(path, title, reaction, note, body.vid, ipHash, internal, now).run();
    return json({ ok: true });
  } catch (e) {
    return json({ ok: false, error: "保存に失敗しました。" }, 500);
  }
}
