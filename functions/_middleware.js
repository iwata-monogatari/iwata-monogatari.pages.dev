async function fetchPartial(context, path) {
  const res = await context.env.ASSETS.fetch(new URL(path, context.request.url));
  if (!res.ok) return null;
  return res.text();
}

async function fetchFooterFromDb(context) {
  const db = context.env.DB;
  if (!db) return null;

  try {
    const row = await db
      .prepare(
        "SELECT html FROM site_fragments WHERE fragment_key = ? AND is_active = 1 LIMIT 1"
      )
      .bind("footer")
      .first();

    if (row && typeof row.html === "string" && row.html.trim()) {
      return row.html;
    }
  } catch (error) {
    console.warn("footer-db-fallback", error && error.message ? error.message : error);
  }

  return null;
}

async function fetchFooterHtml(context) {
  return (await fetchFooterFromDb(context)) || fetchPartial(context, "/partials/footer.html");
}

const CANONICAL_HOST = "iwata-monogatari.net";

// 反応ボタンを出さないページ（トップ・一覧・掲示板・管理画面など）
const NO_REACTION_PATHS = new Set(["/", "/index", "/bbs", "/c034", "/404", "/updates", "/blog"]);
function wantsReactions(pathname) {
  const p = pathname.replace(/\/index\.html$/, "/").replace(/\.html$/, "").replace(/(.)\/+$/, "$1");
  return !NO_REACTION_PATHS.has(p) && !p.startsWith("/admin") && p !== "/search" && !p.startsWith("/search/");
}

export async function onRequest(context) {
  const { request, next } = context;
  const url = new URL(request.url);
  const legacySearch = url.pathname === "/" && ["q", "district", "theme", "sort", "page"].some(key => url.searchParams.has(key));
  const searchContext = legacySearch || url.pathname === "/search" || url.pathname.startsWith("/search/");
  const protectLinks = html => searchContext ? html.replace(/<a\b[^>]*>/gi, tag => tag.replace(/\sreferrerpolicy=(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "").replace(/^<a\b/i, '<a referrerpolicy="origin"')) : html;

  // 旧pages.devドメインはURL単位で独自ドメインへ301（SEO評価の分散防止）
  if (url.hostname === "iwata-monogatari.pages.dev") {
    url.hostname = CANONICAL_HOST;
    return Response.redirect(url.toString(), 301);
  }

  // プレビュー用サブドメイン（*.iwata-monogatari.pages.dev）は検索エンジンに載せない
  const isPreviewHost =
    url.hostname !== CANONICAL_HOST && url.hostname.endsWith(".pages.dev");

  if (url.pathname.startsWith("/partials/") || url.pathname.startsWith("/api/")) {
    return next();
  }

  const withHostGuard = (res) => {
    const guarded = new Response(res.body, res);
    guarded.headers.set("Referrer-Policy", searchContext ? "origin" : "same-origin");
    if (url.pathname === "/data/search/manifest.json") guarded.headers.set("Cache-Control", "no-store");
    else if (/^\/data\/search\/(?:metadata\.[a-f0-9]+\.json|grams\/\d+\.[a-f0-9]+\.json|bodies\/[a-f0-9]+\.json)$/.test(url.pathname)) guarded.headers.set("Cache-Control", "public, max-age=31536000, immutable");
    if (/^\/assets\/js\/(?:article-search|search-core|search-worker|search-preferences|home-search)\.js$/.test(url.pathname)) guarded.headers.set("Cache-Control", "no-cache");
    if (isPreviewHost || /^\/search\/?$/.test(url.pathname)) guarded.headers.set("X-Robots-Tag", "noindex");
    return guarded;
  };

  const response = await next();
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/html")) {
    return withHostGuard(response);
  }

  const [headerHtml, footerHtml, policyHtml, propertyHtml, reactionsHtml] = await Promise.all([
    fetchPartial(context, "/partials/header.html"),
    fetchFooterHtml(context),
    fetchPartial(context, "/partials/article-policy.html"),
    fetchPartial(context, "/partials/local-property-note.html"),
    fetchPartial(context, "/partials/article-reactions.html"),
  ]);

  if (!headerHtml || !footerHtml || !policyHtml || !propertyHtml) {
    return withHostGuard(response);
  }

  // 記事への反応ボタン：「この記事について」があればその直前、無ければ共通フッターの直前に1回だけ置く
  let reactionsPlaced = !reactionsHtml || !wantsReactions(url.pathname);
  const placeReactions = (el) => {
    if (reactionsPlaced) return;
    reactionsPlaced = true;
    el.before(reactionsHtml, { html: true });
  };

  return withHostGuard(new HTMLRewriter()
    .on("a", {
      element(el) {
        if (searchContext) el.setAttribute("referrerpolicy", "origin");
      },
    })
    .on("header.gh-site", {
      element(el) {
        el.setInnerContent(protectLinks(headerHtml), { html: true });
      },
    })
    .on("footer.im-foot", {
      element(el) {
        placeReactions(el);
        el.setInnerContent(protectLinks(footerHtml), { html: true });
      },
    })
    .on("section.article-policy[data-common]", {
      element(el) {
        placeReactions(el);
        el.setInnerContent(policyHtml, { html: true });
      },
    })
    .on("section.local-property-note[data-common]", {
      element(el) {
        el.setInnerContent(propertyHtml, { html: true });
      },
    })
    .transform(response));
}
