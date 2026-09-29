// 配置先: /functions/api/reactions/_lib.js
// 記事の反応ボタンAPIの共通処理。掲示板の共通関数を流用する。
import { checkAdminToken } from "../bbs/_lib.js";
export { json, nowIso, sanitizeText, hashIp, checkAdminToken } from "../bbs/_lib.js";

export const REACTIONS = ["learned", "local", "more"];

// 記事パスを正規化（クエリ・末尾の .html / スラッシュを落とす）
export function normalizePath(input) {
  if (typeof input !== "string") return "";
  let p = input.split("?")[0].split("#")[0].trim();
  if (!p.startsWith("/") || p.length > 300) return "";
  p = p.replace(/\/index\.html$/, "/").replace(/\.html$/, "");
  if (p.length > 1) p = p.replace(/\/+$/, "");
  return /^[\w\-\/.%]+$/.test(p) ? p : "";
}

// 他サイトの記事も同じ表に記録する。磐田物語はパスのまま、他サイトはオリジン付きの完全URLで保存して区別する。
export const PARTNER_SITES = { oishi: "https://oishi-hiroyuki.org" };

export function storedPath(body, request) {
  const path = normalizePath(body && body.path);
  if (!path) return "";
  const site = body.site;
  if (!site || site === "iwata") return path;
  const origin = PARTNER_SITES[site];
  // 他サイト名義の記録は、そのサイトのページから送られたものだけ受け付ける
  if (!origin || request.headers.get("Origin") !== origin) return "";
  return origin + path;
}

// 端末ごとの匿名ID（ブラウザで生成したランダム値）
export function validVisitorId(v) {
  return typeof v === "string" && /^[a-z0-9]{16,40}$/i.test(v);
}

// テーブルが無ければ作る（migrations/0002_article_reactions.sql と同じ定義）。
// wrangler の手動適用に頼らず、初回リクエストで本番D1に用意されるようにする。
let tablesReady = false;
export async function ensureTables(db) {
  if (tablesReady) return;
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS article_reactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, title TEXT,
      reaction TEXT NOT NULL CHECK (reaction IN ('learned','local','more')),
      visitor_id TEXT NOT NULL, ip_hash TEXT, internal INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE (path, visitor_id))`),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_article_reactions_path ON article_reactions (path)"),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_article_reactions_created ON article_reactions (created_at)"),
    db.prepare(`CREATE TABLE IF NOT EXISTS article_reaction_notes (
      id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, title TEXT, reaction TEXT,
      note TEXT NOT NULL, visitor_id TEXT NOT NULL, ip_hash TEXT,
      internal INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)`),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_article_reaction_notes_created ON article_reaction_notes (created_at)"),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_article_reaction_notes_ip ON article_reaction_notes (ip_hash, created_at)"),
  ]);
  tablesReady = true;
}

export async function readJson(request) {
  try {
    return await request.json();
  } catch (e) {
    return null;
  }
}

// ── 管理者端末の登録（Cookie）──────────────────────────────
// 一度トークンで登録した端末には、トークンそのものではなくハッシュ値を
// HttpOnly Cookie として保存し、以後は入力なしで一言の本文を表示する。
// BBS_ADMIN_TOKEN を変更すると、登録済みの端末はすべて自動的に無効になる。
export const ADMIN_COOKIE = "im_admin";

export async function adminCookieValue(env) {
  const token = env.BBS_ADMIN_TOKEN;
  if (!token) return "";
  const data = new TextEncoder().encode("iwata-monogatari-admin-v1:" + token);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function readCookie(request, name) {
  const raw = request.headers.get("Cookie") || "";
  for (const part of raw.split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i) === name) return part.slice(i + 1);
  }
  return "";
}

// トークン（Authorization ヘッダー）または登録済み端末の Cookie で管理者と判定する
export async function isAdmin(request, env) {
  if (checkAdminToken(request, env)) return true;
  const expected = await adminCookieValue(env);
  const got = readCookie(request, ADMIN_COOKIE);
  return !!expected && got.length === expected.length && got === expected;
}
