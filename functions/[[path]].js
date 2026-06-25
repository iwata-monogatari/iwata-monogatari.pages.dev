const CLEAN_HTML_PAGES = new Set([
  "c004",
  "c010",
  "c011",
  "c017",
  "u001",
  "u002",
  "n017",
  "n019",
  "n021",
  "n022",
  "k001",
  "t007",
  "s001",
]);

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const cleanPath = url.pathname.replace(/^\/+|\/+$/g, "");

  if (CLEAN_HTML_PAGES.has(cleanPath)) {
    const assetUrl = new URL(`/${cleanPath}.html`, url);
    const assetRequest = new Request(assetUrl.toString(), context.request);
    return context.env.ASSETS.fetch(assetRequest);
  }

  return context.env.ASSETS.fetch(context.request);
}
