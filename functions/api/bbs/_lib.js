// 配置先: /functions/api/bbs/_lib.js
// 掲示板APIの共通ユーティリティ。Cloudflare Pages Functions ランタイム前提。

export function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extraHeaders,
    },
  });
}

export function nowIso() {
  return new Date().toISOString();
}

// 本文サニタイズ: 制御文字を除去し、前後空白を整理。
// 表示側も textContent を使うため、HTMLは二重に実行不能。
export function sanitizeText(input, maxLen) {
  if (typeof input !== "string") return "";
  let s = input;
  // 改行を正規化（CRLF/CR -> LF）
  s = s.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  // 制御文字を除去（改行 \n とタブ \t は許可）
  s = s.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "");
  s = s.trim();
  if (typeof maxLen === "number" && s.length > maxLen) {
    s = s.slice(0, maxLen);
  }
  return s;
}

// HTMLタグらしき記述が含まれるか（< ... > / scriptスキーム / onイベント属性）
export function looksLikeHtml(s) {
  if (typeof s !== "string") return false;
  return /<\s*\/?\s*[a-z!]/i.test(s) || /javascript\s*:/i.test(s) || /\son\w+\s*=/i.test(s);
}

// URLの個数を数える
export function countUrls(s) {
  if (typeof s !== "string") return 0;
  const m = s.match(/https?:\/\/[^\s]+/gi);
  return m ? m.length : 0;
}

// IP を SHA-256 でハッシュ化（生IPは保存しない）
export async function hashIp(ip, salt) {
  if (!ip) return null;
  const data = new TextEncoder().encode((salt || "") + "|" + ip);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// Cloudflare Turnstile のサーバー側検証
export async function verifyTurnstile(token, secret, remoteIp) {
  if (!secret) return { ok: true, skipped: true }; // 未設定なら検証スキップ
  if (!token) return { ok: false, reason: "missing-token" };
  const form = new FormData();
  form.append("secret", secret);
  form.append("response", token);
  if (remoteIp) form.append("remoteip", remoteIp);
  try {
    const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      body: form,
    });
    const data = await res.json();
    return { ok: !!data.success, reason: (data["error-codes"] || []).join(",") };
  } catch (e) {
    return { ok: false, reason: "verify-error" };
  }
}

// 管理APIのトークン認証（Cloudflare Access 併用が望ましいが簡易代替）
export function checkAdminToken(request, env) {
  const expected = env.BBS_ADMIN_TOKEN;
  if (!expected) return false; // 未設定なら拒否（事故防止）
  const auth = request.headers.get("Authorization") || "";
  const bearer = auth.replace(/^Bearer\s+/i, "");
  const headerToken = request.headers.get("X-Admin-Token") || "";
  return bearer === expected || headerToken === expected;
}

// 投稿通知メール（Resend API）。未設定なら何もしない。
export async function sendNotifyMail(env, post) {
  const apiKey = env.RESEND_API_KEY;
  const to = env.BBS_NOTIFY_TO;
  const from = env.BBS_NOTIFY_FROM;
  if (!apiKey || !to || !from) return { ok: false, skipped: true };

  const subject = "【磐田物語】掲示板に新しい投稿がありました";
  const text =
    "磐田物語の掲示板に新しい投稿がありました。\n\n" +
    "お名前：" + (post.name || "匿名") + "\n" +
    "地域：" + (post.area || "（未記入）") + "\n" +
    "投稿日時：" + (post.created_at || "") + "\n" +
    "関連URL：" + (post.related_url || "（なし）") + "\n\n" +
    "投稿内容：\n" + (post.body || "") + "\n\n" +
    "管理画面：\nhttps://iwata-monogatari.pages.dev/admin-bbs.html\n";

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ from, to, subject, text }),
    });
    return { ok: res.ok };
  } catch (e) {
    return { ok: false, reason: "mail-error" };
  }
}
