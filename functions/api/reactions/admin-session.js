// 配置先: /functions/api/reactions/admin-session.js
// 管理者端末の登録・解除。
//   POST   {token}  … トークンが正しければ、この端末に1年間有効の管理者Cookieを保存する
//   DELETE          … この端末の登録を解除する
//   GET             … この端末が登録済みかどうかを返す
// Cookie は HttpOnly・Secure・SameSite=Strict で、/api/reactions/ にだけ送られる。
import { json, readJson, isAdmin, adminCookieValue, ADMIN_COOKIE } from "./_lib.js";

const MAX_AGE = 365 * 86400;
const ATTRS = "Path=/api/reactions/; HttpOnly; Secure; SameSite=Strict";

function withCookie(res, value, maxAge) {
  res.headers.append("Set-Cookie", `${ADMIN_COOKIE}=${value}; Max-Age=${maxAge}; ${ATTRS}`);
  res.headers.set("Cache-Control", "no-store");
  return res;
}

export async function onRequestGet({ request, env }) {
  const res = json({ ok: true, admin: await isAdmin(request, env) });
  res.headers.set("Cache-Control", "no-store");
  return res;
}

export async function onRequestPost({ request, env }) {
  const body = await readJson(request);
  const token = body && typeof body.token === "string" ? body.token.trim() : "";
  const expected = env.BBS_ADMIN_TOKEN;
  if (!expected || !token || token !== expected) {
    return json({ ok: false, error: "トークンが正しくありません。" }, 401);
  }
  return withCookie(json({ ok: true, admin: true }), await adminCookieValue(env), MAX_AGE);
}

export async function onRequestDelete() {
  return withCookie(json({ ok: true, admin: false }), "", 0);
}
