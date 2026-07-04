// 全ページ共通ヘッダー・フッター・記事末尾の定型ブロックの差し込み。
// partials/*.html を唯一のソースとし、配信時（エッジ）で対象要素の中身を
// そこから読み込んで差し替える。各HTMLファイルに残る同クラスの内容は、
// この関数が読めない場合（ローカル簡易サーバー等）向けのフォールバック
// であり、実際に配信される中身は partials/ 側が正となる。
// 対象外: header class="site" を使う祭り特集ページ群（独自の局所ナビの
// ため意図的に除外）。
//
// section.article-policy / section.local-property-note は、記事によって
// 参考資料・作成方針・見出し文言を個別にカスタマイズしていることがあるため、
// header/footerと違い無条件には差し替えない。data-common 属性を付けた
// （＝中身を空にした）要素だけを対象にし、既存記事の個別カスタム文言を
// 上書きしないようにする。新規記事では
//   <section class="article-policy" data-common></section>
//   <section class="local-property-note" data-common></section>
// のように空タグ＋data-commonで置くだけでよい。

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

  const [headerRes, footerRes, policyRes, propertyRes] = await Promise.all([
    context.env.ASSETS.fetch(new URL("/partials/header.html", request.url)),
    context.env.ASSETS.fetch(new URL("/partials/footer.html", request.url)),
    context.env.ASSETS.fetch(new URL("/partials/article-policy.html", request.url)),
    context.env.ASSETS.fetch(new URL("/partials/local-property-note.html", request.url)),
  ]);

  if (!headerRes.ok || !footerRes.ok || !policyRes.ok || !propertyRes.ok) {
    return response;
  }

  const [headerHtml, footerHtml, policyHtml, propertyHtml] = await Promise.all([
    headerRes.text(),
    footerRes.text(),
    policyRes.text(),
    propertyRes.text(),
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
    .transform(response);
}
