// Cloudflare Pages middleware — page access aggregation.
// Counts HTML page views by JST date and path for weekly rankings.

export async function onRequest(context) {
  const { request, env, next } = context;
  const response = await next();

  const kv = env.COUNTER;
  if (!kv || request.method !== "GET") return response;

  const url = new URL(request.url);
  if (!shouldTrack(url.pathname, response)) return response;

  const today = jstDate(0);
  const path = normalizePath(url.pathname);
  const cookie = request.headers.get("Cookie") || "";
  const alreadyToday = cookie.match(/(?:^|;\s*)iv_seen=([0-9-]+)/)?.[1] === today;

  await Promise.all([
    increment(kv, `page:${today}:${path}`, 60 * 60 * 24 * 45),
    increment(kv, `pv:day:${today}`, 60 * 60 * 24 * 400),
    increment(kv, "pv:total"),
    alreadyToday ? Promise.resolve() : increment(kv, `day:${today}`, 60 * 60 * 24 * 400),
    alreadyToday ? Promise.resolve() : increment(kv, "total"),
  ]);

  if (alreadyToday) return response;

  const headers = new Headers(response.headers);
  headers.append("Set-Cookie", `iv_seen=${today}; Path=/; Max-Age=172800; SameSite=Lax; Secure`);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function shouldTrack(pathname, response) {
  if (pathname.startsWith("/api/")) return false;
  if (pathname.startsWith("/assets/") || pathname.startsWith("/images/") || pathname.startsWith("/saguchi/")) return false;
  if (/\.(css|js|json|xml|txt|ico|png|jpe?g|webp|avif|gif|svg|pdf|map)$/i.test(pathname)) return false;
  const contentType = response.headers.get("Content-Type") || "";
  return response.ok && contentType.includes("text/html");
}

function normalizePath(pathname) {
  if (!pathname || pathname === "/" || pathname === "/index.html") return "/";
  if (pathname.endsWith("/index.html")) return pathname.slice(0, -"index.html".length);
  return pathname;
}

function jstDate(offsetDays) {
  return new Date(Date.now() + 9 * 3600e3 + offsetDays * 86400e3).toISOString().slice(0, 10);
}

async function increment(kv, key, expirationTtl) {
  const current = parseInt((await kv.get(key)) || "0", 10) || 0;
  const options = expirationTtl ? { expirationTtl } : undefined;
  await kv.put(key, String(current + 1), options);
}
