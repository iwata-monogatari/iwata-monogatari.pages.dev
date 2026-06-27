// Cloudflare Pages Function — access counter and weekly page ranking.
// Public URLs:
//   /api/counter
//   /api/counter?ranking=weekly&limit=10

export async function onRequest(context) {
  const { request, env } = context;
  const kv = env.COUNTER;

  if (!kv) {
    return json({ today: 0, yesterday: 0, total: 0, items: [], error: "KV未設定" });
  }

  const url = new URL(request.url);
  if (url.searchParams.get("ranking") === "weekly") {
    const limit = clampInt(url.searchParams.get("limit"), 10, 1, 50);
    return json(await weeklyRanking(kv, limit));
  }

  const today = jstDate(0);
  const yesterday = jstDate(-1);
  const [todayCount, yCount, total, todayPv, yPv, totalPv] = await Promise.all([
    getInt(kv, `day:${today}`),
    getInt(kv, `day:${yesterday}`),
    getInt(kv, "total"),
    getInt(kv, `pv:day:${today}`),
    getInt(kv, `pv:day:${yesterday}`),
    getInt(kv, "pv:total"),
  ]);

  return json({
    today: todayCount,
    yesterday: yCount,
    total,
    pv_today: todayPv,
    pv_yesterday: yPv,
    pv_total: totalPv,
    rows: [
      { label: "today", users: todayCount, pv: todayPv },
      { label: "yesterday", users: yCount, pv: yPv },
      { label: "total", users: total, pv: totalPv },
    ],
  });
}

async function weeklyRanking(kv, limit) {
  const totals = new Map();
  const days = Array.from({ length: 3 }, (_, i) => jstDate(-i));

  for (const day of days) {
    let cursor;
    do {
      const listed = await kv.list({ prefix: `page:${day}:`, cursor });
      cursor = listed.cursor;
      await Promise.all(
        listed.keys.map(async (entry) => {
          const path = entry.name.slice(`page:${day}:`.length);
          if (isExcludedFromRanking(path)) return;
          const count = await getInt(kv, entry.name);
          totals.set(path, (totals.get(path) || 0) + count);
        })
      );
    } while (cursor);
  }

  const items = Array.from(totals.entries())
    .map(([path, count]) => ({ path, count }))
    .sort((a, b) => b.count - a.count || a.path.localeCompare(b.path))
    .slice(0, limit);

  return {
    range: "weekly",
    days,
    generated_at: new Date().toISOString(),
    items,
  };
}

function isExcludedFromRanking(path) {
  if (!path || path === "/" || path === "/index.html") return true;
  if (/^\/010\d{2}-/i.test(path)) return true;
  if (/^\/(assets|images|saguchi)\//i.test(path)) return true;
  if (/\.(png|jpe?g|webp|avif|gif|svg|pdf|ico)$/i.test(path)) return true;
  if (path === "/c019.html" || path === "/c020.html") return true;
  return false;
}

function jstDate(offsetDays) {
  return new Date(Date.now() + 9 * 3600e3 + offsetDays * 86400e3).toISOString().slice(0, 10);
}

async function getInt(kv, key) {
  return parseInt((await kv.get(key)) || "0", 10) || 0;
}

function clampInt(value, fallback, min, max) {
  const n = parseInt(value || "", 10);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(min, Math.min(max, n));
}

function json(obj) {
  return new Response(JSON.stringify(obj), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
