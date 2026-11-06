# 磐南の人物別登録・集計の廃止（2026-11-07）

ユーザーの指示により、「私の知り合い」の登録ボタン・受付API・集計画面・アクセス状況からのリンクをすべて廃止しました。過去の登録データは削除しません。通常のアクセス計測、磐田物語と大石浩之の記事反応・管理者認証は維持します。

- 磐南サイト側のボタンと受付APIは既に廃止済みです。専用 Worker はデータベースを読み書きせず 410 を返します。
- `admin-reactions.html` と `assets/js/admin-feedback.js` の磐南用 UI・ランキング取得を削除しました。
- `functions/_middleware.js` は旧 `admin-reactions?site=banban`（`.html` と末尾 `/` も含む）へ 410 と終了案内を返し、他サイトの集計を代わりに表示しません。
- アクセス状況の磐南カードの反応リンクも削除します。磐南向けの選択肢・API 呼び出し・リンクを再追加しないでください。
- API・登録データを削除するマイグレーションは実行していません。

検査: `node --test tests/article-feedback.test.mjs tests/reactions-summary.test.mjs tests/retired-banban.test.mjs`。
