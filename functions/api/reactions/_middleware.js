// 配置先: /functions/api/reactions/_middleware.js
// 他サイト（oishi-hiroyuki.org）の記事からの反応を受けるための CORS。
// 管理API（admin-summary）は対象外で、磐田物語の管理画面からだけ使う。
import { PARTNER_SITES } from "./_lib.js";

const ALLOWED = new Set(Object.values(PARTNER_SITES));
// 件数だけの counts はアクセスダッシュボードからも読む
const DASHBOARD_ORIGIN = "https://fujigaoka-analytics-worker.hiroyukio0122.workers.dev";

export async function onRequest({ request, next }) {
  const origin = request.headers.get("Origin") || "";
  const path = new URL(request.url).pathname;
  const isCounts = path.endsWith("/counts");
  const corsOk = isCounts
    ? origin === DASHBOARD_ORIGIN
    : ALLOWED.has(origin) && !path.endsWith("/admin-summary") && !path.endsWith("/admin-session");
  const corsHeaders = corsOk
    ? {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": isCounts ? "GET, OPTIONS" : "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
      }
    : {};

  if (request.method === "OPTIONS") {
    return new Response(null, { status: corsOk ? 204 : 403, headers: corsHeaders });
  }
  const res = await next();
  if (!corsOk) return res;
  const out = new Response(res.body, res);
  for (const [k, v] of Object.entries(corsHeaders)) out.headers.set(k, v);
  return out;
}
