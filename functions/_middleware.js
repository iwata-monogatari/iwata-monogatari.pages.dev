// 全ページ共通ヘッダー・フッターの差し込み。
// partials/header.html と partials/footer.html を唯一のソースとし、
// 配信時（エッジ）で <header class="gh-site"> / <footer class="im-foot">
// の中身をそこから読み込んで差し替える。各HTMLファイルに残る同クラスの
// 内容は、この関数が読めない場合（ローカル簡易サーバー等）向けのフォール
// バックであり、実際に配信される中身は partials/ 側が正となる。
// 対象外: header class="site" を使う祭り特集ページ群（独自の局所ナビの
// ため意図的に除外）。

export async function onRequest(context) {
  const { request, next } = context;
  const url = new URL(request.url);

  if (url.pathname.startsWith("/partials/") || url.pathname.startsWith("/api/")) {
    return next();
  }

  const response = await next();
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/html")) {
    return response;
  }

  const [headerRes, footerRes] = await Promise.all([
    context.env.ASSETS.fetch(new URL("/partials/header.html", request.url)),
    context.env.ASSETS.fetch(new URL("/partials/footer.html", request.url)),
  ]);

  if (!headerRes.ok || !footerRes.ok) {
    return response;
  }

  const [headerHtml, footerHtml] = await Promise.all([
    headerRes.text(),
    footerRes.text(),
  ]);

  return new HTMLRewriter()
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
    .transform(response);
}
