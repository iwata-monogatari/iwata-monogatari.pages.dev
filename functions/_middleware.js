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

export async function onRequest(context) {
  const { request, next } = context;
  const url = new URL(request.url);

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
    if (!isPreviewHost) return res;
    const guarded = new Response(res.body, res);
    guarded.headers.set("X-Robots-Tag", "noindex");
    return guarded;
  };

  const response = await next();
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/html")) {
    return withHostGuard(response);
  }

  const [headerHtml, footerHtml, policyHtml, propertyHtml] = await Promise.all([
    fetchPartial(context, "/partials/header.html"),
    fetchFooterHtml(context),
    fetchPartial(context, "/partials/article-policy.html"),
    fetchPartial(context, "/partials/local-property-note.html"),
  ]);

  if (!headerHtml || !footerHtml || !policyHtml || !propertyHtml) {
    return withHostGuard(response);
  }

  return withHostGuard(new HTMLRewriter()
    .on("header.gh-site", {
      element(el) {
        el.setInnerContent(headerHtml, { html: true });
      },
    })
    .on("footer.im-foot", {
      element(el) {
        el.setInnerContent(footerHtml, { html: true });
      },
    })
    .on("section.article-policy[data-common]", {
      element(el) {
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
