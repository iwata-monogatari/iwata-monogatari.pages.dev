// Cloudflare Pages Function — アクセスカウンター
// 配置場所: リポジトリ直下の  functions/api/counter.js
// 公開URL:  https://iwata-monogatari.pages.dev/api/counter
//
// 必要な設定: Pages プロジェクトに KV ネームスペースを「COUNTER」という
//             変数名でバインドしてください（手順は README を参照）。
//
// 集計方針（Cookieベース・ユニーク訪問者）:
//   - 同じ人は 1 日 1 回だけカウンア�（Cookie で判定）
//   - today     = 本日のユニーク訪問者数（日本時間）
//   - yesterday = 昨日のユニーク訪問者数
//   - total     = 累計（日々のユニーク数の積み上げ）

export async function onRequest(context) {
  const { request, env } = context;
  const kv = env.COUNTER;

  // KV が未設定でもページを壊しないようにエラーを返す
  if (!kv) {
    return json({ today: 0, yesterday: 0, total: 0, error: "KV未設定" }, {});
  }

  // 日本時間（UTC+9）の YYYY-MM-DD を作る
  const jst = (offsetDays = 0) =>
    new Date(Date.now() + 9 * 3600e3 + offsetDays * 86400e3)
      .toISOString()
      .slice(0, 10);
  const today = jst(0);
  const yesterday = jst(-1);
  const todayKey = "day:" + today;

  // Cookie を確認（本日すでにカウント済みか）
  const cookie = request.headers.get("Cookie") || "";
  const m = cookie.match(/(?:^|;\s*)iv_seen=([0-9-]+)/);
  const alreadyToday = m && m[1] === today;

  // 現在値を読み込む
  let [todayCount, yCount, total] = await Promise.all([
    kv.get(todayKey).then((v) => parseInt(v || "0", 10) || 0),
    kv.get("day:" + yesterday).then((v) => parseInt(v || "0", 10) || 0),
    kv.get("total").then((v) => parseInt(v || "0", 10) || 0),
  ]);

  // 新規（本日初回）の訪問だけカウントアップ
  let counted = false;
  if (!alreadyToday) {
    todayCount += 1;
    total += 1;
    counted = true;
    await Promise.all([
      // 日別キーは約400日で自動削除（KVを肥大化させない）
      kv.put(todayKey, String(todayCount), { expirationTtl: 60 * 60 * 24 * 400 }),
      kv.put("total", String(total)),
    ]);
  }

  const extraHeaders = {};
  if (counted) {
    // 「本日カウント済み」の印を 2 日間保持
    extraHeaders["Set-Cookie"] =
      `iv_seen=${today}; Path=/; Max-Age=172800; SameSite=Lax; Secure`;
  }

  return json({ today: todayCount, yesterday: yCount, total }, extraHeaders);
}

function json(obj, extraHeaders) {
  return new Response(JSON.stringify(obj), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extraHeaders,
    },
  });
}
