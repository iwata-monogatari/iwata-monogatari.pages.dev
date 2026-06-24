// 配置先: /functions/api/bbs/post.js
// 投稿作成。Turnstile検証 → honeypot → 文字数 → HTML/URLチェック → published保存 → 通知メール。
import {
  json, nowIso, sanitizeText, looksLikeHtml, countUrls,
  hashIp, verifyTurnstile, sendNotifyMail,
} from "./_lib.js";

const MIN_BODY = 10;
const MAX_BODY = 800;
const MAX_NAME = 40;
const MAX_AREA = 60;
const MAX_URL = 300;
const MAX_URLS_IN_BODY = 2;
const RATELIMIT_SECONDS = 30; // 同一IPハッシュからの連続投稿制限

export async function onRequestPost({ request, env }) {
  if (!env.DB) {
    return json({ ok: false, error: "データベース未設定です。" }, 500);
  }

  let payload;
  try {
    payload = await request.json();
  } catch (e) {
    return json({ ok: false, error: "送信形式が正しくありません。" }, 400);
  }

  // 1. honeypot: 何か入っていれば bot とみなし、成功を装って破棄
  if (payload.website && String(payload.website).trim() !== "") {
    return json({ ok: true });
  }

  // 2. 同意チェック
  if (payload.agree !== true) {
    return json({ ok: false, error: "注意事項への同意が必要です。" }, 400);
  }

  // 3. Turnstile 検証
  const remoteIp = request.headers.get("CF-Connecting-IP") || "";
  const ts = await verifyTurnstile(
    payload["cf-turnstile-response"],
    env.TURNSTILE_SECRET_KEY,
    remoteIp
  );
  if (!ts.ok) {
    return json({ ok: false, error: "bot対策の確認に失敗しました。ページを再読み込みしてお試しください。" }, 400);
  }

  // 4. 入力サニタイズ
  const name = sanitizeText(payload.name, MAX_NAME) || "匿名";
  const area = sanitizeText(payload.area, MAX_AREA);
  const body = sanitizeText(payload.body, MAX_BODY);
  const relatedUrlRaw = sanitizeText(payload.related_url, MAX_URL);

  // 5. 本文の長さ
  if (body.length < MIN_BODY) {
    return json({ ok: false, error: "投稿内容は" + MIN_BODY + "文字以上でご記入ください。" }, 400);
  }
  if (body.length > MAX_BODY) {
    return json({ ok: false, error: "投稿内容は" + MAX_BODY + "文字以内でご記入ください。" }, 400);
  }

  // 6. HTML/スクリプト混入の拒否（保存もエスケープ表示もするが、入口でも弾く）
  if (looksLikeHtml(body) || looksLikeHtml(name) || looksLikeHtml(area)) {
    return json({ ok: false, error: "HTMLタグやスクリプトは使用できません。" }, 400);
  }

  // 7. URL大量投稿の拒否
  if (countUrls(body) > MAX_URLS_IN_BODY) {
    return json({ ok: false, error: "本文中のURLが多すぎます。リンクは控えめにしてください。" }, 400);
  }

  // 8. related_url は http/https のみ許可。それ以外は破棄
  let relatedUrl = null;
  if (relatedUrlRaw) {
    if (/^https?:\/\//i.test(relatedUrlRaw)) {
      relatedUrl = relatedUrlRaw;
    } else {
      return json({ ok: false, error: "関連URLは http(s) で始まる形式でご入力ください。" }, 400);
    }
  }

  // 9. IPハッシュと連続投稿チェック
  const ipHash = await hashIp(remoteIp, env.BBS_IP_SALT || "iwata-monogatari");
  const userAgent = (request.headers.get("User-Agent") || "").slice(0, 300);
  const created = nowIso();

  if (ipHash) {
    try {
      const recent = await env.DB.prepare(
        `SELECT created_at FROM bbs_posts
         WHERE ip_hash = ?
         ORDER BY created_at DESC LIMIT 1`
      ).bind(ipHash).first();
      if (recent && recent.created_at) {
        const diffMs = Date.parse(created) - Date.parse(recent.created_at);
        if (diffMs >= 0 && diffMs < RATELIMIT_SECONDS * 1000) {
          return json({ ok: false, error: "投稿の間隔が短すぎます。少し時間をおいて再度お試しください。" }, 429);
        }
      }
    } catch (e) {
      // チェック失敗は致命ではないので続行
    }
  }

  // 10. 保存（status = published）
  let newId = null;
  try {
    const result = await env.DB.prepare(
      `INSERT INTO bbs_posts
        (name, area, body, related_url, status, ip_hash, user_agent, created_at, updated_at)
       VALUES (?, ?, ?, ?, 'published', ?, ?, ?, ?)`
    ).bind(name, area || null, body, relatedUrl, ipHash, userAgent, created, created).run();
    newId = result.meta && result.meta.last_row_id ? result.meta.last_row_id : null;
  } catch (e) {
    return json({ ok: false, error: "保存に失敗しました。時間をおいて再度お試しください。" }, 500);
  }

  // 11. 通知メール（失敗しても投稿は成功扱い）
  try {
    await sendNotifyMail(env, { name, area, body, related_url: relatedUrl, created_at: created });
  } catch (e) { /* 通知失敗は無視 */ }

  return json({ ok: true, id: newId });
}
