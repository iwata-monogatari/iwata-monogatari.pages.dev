# 業務指示書：新規ページ公開と新着・公開履歴の自動更新

## 目的

磐田物語で新しいページを公開したときに、トップページの新着記事、公開履歴・更新履歴、`data/new-articles.json` が自動的に更新される状態を維持する。

## 基本方針

- 新着記事と公開履歴の正本は `data/new-articles.json` とする。
- `index.html` と `updates.html` の直書きフォールバックは手で編集しない。
- 新規ページの公開時は、ページの `<head>` に新着登録用メタタグを入れる。
- デプロイ前に `python sync_new_articles.py` または `npm run build` を実行する。
- Cloudflare Pages では Build command に `npm run build` を設定する。

## 新規ページに必ず入れるメタタグ

新規公開ページの `<head>` に以下を入れる。

```html
<meta name="iwata:published" content="2026-06-30">
<meta name="iwata:category" content="竜洋・歴史沿革">
<meta name="iwata:title" content="竜洋町の沿革 — 川と海に向き合ってきた町の成り立ち">
```

あわせて、次のどちらかでURLを明示する。

```html
<link rel="canonical" href="https://iwata-monogatari.net/area/ryuyo/history/">
```

または

```html
<meta property="og:url" content="https://iwata-monogatari.net/area/ryuyo/history/">
```

## 公開前チェック

1. 新規ページの本文・タイトル・canonical URLを確認する。
2. `<meta name="iwata:published">` の日付が公開日になっているか確認する。
3. `<meta name="iwata:category">` が地区・分類を表しているか確認する。
4. `<meta name="iwata:title">` が新着に表示したい文言になっているか確認する。
5. `python sync_new_articles.py` を実行する。
6. `data/new-articles.json` の先頭付近に新規ページが入っているか確認する。
7. `index.html` と `updates.html` が更新されていることを確認する。
8. デプロイする。

## 実行コマンド

PowerShellでは次を使う。

```powershell
python sync_new_articles.py
```

または、Cloudflare Pages と同じ経路で確認する場合は次を使う。

```powershell
npm.cmd run build
```

## Cloudflare Pages 設定

Build command:

```text
npm run build
```

Build output directory:

```text
.
```

この設定により、デプロイ時に `sync_new_articles.py` が実行され、`data/new-articles.json`、`index.html`、`updates.html` が更新された状態で公開される。

## 手動でJSONに残すケース

以下はHTMLメタタグから自動収集できないため、必要に応じて `data/new-articles.json` に直接残す。

- トップページ自体の更新
- 外部生成・別ディレクトリ生成で、このリポジトリにHTMLが無いページ
- 複数ページ公開を1件の「特集公開」として見せたい告知
- サイト更新、機能追加、デザイン変更などの記事ページではない履歴

## 禁止事項

- `index.html` の新着リストを手で直書き更新しない。
- `updates.html` の「最新の更新」を手で直書き更新しない。
- 公開後に `data/new-articles.json` だけを更新して、同期コマンドを実行しない状態で放置しない。
- 新規ページに `iwata:published`、`iwata:category`、`iwata:title` を入れ忘れない。

## 既知の注意点

- 静的サイトなので、公開後にサーバー側で自動的にJSONを書き換えることはできない。
- 自動更新はデプロイ前またはCloudflare Pagesのビルド時に実行される。
- PowerShellでは `npm run build` が実行ポリシーで止まる場合がある。その場合は `npm.cmd run build` を使う。
- `data/new-articles-discovered.json` は自動収集結果の確認用ファイルであり、正本は `data/new-articles.json`。

## 今回の記憶事項

- 竜洋の `/area/ryuyo/...` 系8ページは、公開ページとして存在していたが `data/new-articles.json` に未登録だったため、新着記事に表示されなかった。
- 原因はキャッシュではなく、新着JSONの正本に登録されていないことだった。
- 今後は新規ページにメタタグを入れ、ビルド時に `sync_new_articles.py` を走らせることで同じ漏れを防ぐ。
