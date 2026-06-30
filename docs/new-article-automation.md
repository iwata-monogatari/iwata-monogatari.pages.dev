# 新着記事・公開履歴の自動更新

`sync_new_articles.py` が、以下をまとめて更新します。

- `data/new-articles.json`
- `data/new-articles-discovered.json`
- `index.html` の新着記事フォールバック
- `updates.html` の最新更新フォールバック

## 新規ページ側に入れるメタタグ

新しい記事ページの `<head>` に、最低限この3つを入れます。

```html
<meta name="iwata:published" content="2026-06-30">
<meta name="iwata:category" content="竜洋・歴史沿革">
<meta name="iwata:title" content="竜洋町の沿革 — 川と海に向き合ってきた町の成り立ち">
```

URLは `<link rel="canonical" href="https://iwata-monogatari.net/...">` または `og:url` から取得します。どちらも無い場合は、ファイルパスから推定します。

## 生成コマンド

デプロイ前にルートで実行します。

```powershell
python sync_new_articles.py
```

Cloudflare Pages の Build command に設定する場合も同じです。

```text
python sync_new_articles.py
```

このコマンドを通すと、公開履歴JSONとトップ/更新履歴HTMLが同時に更新され、その状態がデプロイされます。

## 直接JSONへ残す項目

トップページ更新や外部で生成されたページなど、HTMLファイルがこのリポジトリに無いものは、従来通り `data/new-articles.json` に残します。スクリプトは既存JSONを消さず、HTMLメタから見つけた新規ページを追加・整列します。
