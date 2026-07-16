# Release Guard

このサイトでは、古い作業コピーや古い成果物で本番が先祖返りしないように、`data/release-guard.json` を本番世代の印として使う。

## 何を守るか

- `data/pages.json` と `data/new-articles.json` の件数とハッシュ
- トップ、更新一覧、全記事一覧、sitemap、redirect 設定
- 直近120件の新着記事 URL
- 2026-07-16 復旧時点で必ず守る記事:
  - `/m056.html`
  - `/k006.html`
  - `/k056.html`
  - `/m132.html`
  - `/m133.html`
  - `/m134.html`
  - `/s023.html`
  - `/s024.html`
  - `/s025.html`
  - `/oishi-iwata-tochi-kiokuroku/05`

## 通常の公開手順

記事や一覧を変更したら、公開前に必ず次を実行する。

```powershell
npm.cmd run build
npm.cmd run knowledge-count
npm.cmd run release:stamp
npm.cmd run guard
git add -A
git commit -m "..."
git push
```

`release:stamp` は現在の正しい状態を `data/release-guard.json` に記録する。記録後に保護対象ファイルや保護対象 URL の本文が変わると、`guard` は失敗する。

## 先祖返りを止める仕組み

Cloudflare Pages のビルドでは `scripts/predeploy_guard.py` が `scripts/release_guard.py check-build` を呼ぶ。

- 今回の世代が本番世代より古い場合: ビルド失敗
- 同じ世代なのに内容ハッシュが違う場合: ビルド失敗
- 本番にまだ世代ファイルがない初回導入だけ: 許可

起動時チェックとして `npm.cmd run check-live-sync` を実行すると、`main` 側の世代ファイルと本番の世代ファイルが一致しているかも確認する。

## 手元確認

```powershell
npm.cmd run release:check
npm.cmd run release:check-live
npm.cmd run check-live-sync
```

`check-live-sync` も世代ファイルを確認する。データ件数が同じでも、本文や一覧が古い場合は検出できる。
