# Codex 作業ルール

## 作業開始時の必須チェック

このリポジトリで調査、編集、記事作成、ビルド、公開、デプロイ確認を行う前に、最初の確認コマンドとして必ず次を実行する。

```powershell
npm.cmd run check-live-sync
```

このチェックが成功するまで、記事本文、`data/pages.json`、`data/new-articles.json`、`index.html`、`updates.html`、`sitemap.xml`、公開関連スクリプトを編集しない。

失敗した場合は作業を止め、表示された差分・Git不一致・wrangler権限警告・release guard不一致をそのままユーザーへ報告する。原因が解消するまで、上書き、再生成、デプロイ、コミットを進めない。

このルールは、`git status` や `origin/main` との一致より優先する。本番 `https://iwata-monogatari.net` とローカルの一致確認を先に行う。
