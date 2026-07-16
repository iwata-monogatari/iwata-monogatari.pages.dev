# iwata-monogatari.pages.dev

## 作業を始める前に必ず（2026-07-15）
`npm.cmd run check-live-sync` を実行し、ローカルの `data/pages.json`・`data/new-articles.json` が今の本番（`https://iwata-monogatari.net`）と一致しているか確認する。**`git status`が「origin/mainと同期」と言っていても、本番はそれと無関係に食い違っていることがある**（Gitを経由しない直接デプロイが別経路から入る場合があるため）。一致していなければ、編集を始める前にまず差分の原因を調べる。2026-07-15、この確認をせずに作業を始めたため、本番にしか無かった108記事に気づかず上書きしかけた事故があった。

磐田物語――静岡県磐田市に積み重ねられてきた歴史と文化を、一市民の視点で掘り起こし、書き留めていく場である。遠江国の国府が置かれ、東海道見付宿として栄えたこの地には、古代の遺跡から宿場の面影、祭りや暮らしの記憶まで、語り継ぐべきものが数多く眠っている。本サイトでは、郷土の史料や現地の風景をたどりながら、磐田に生きた人々の営みとまちの移ろいを、ひとつひとつの物語として綴っていく。地域に暮らす者として、足もとの歴史を見つめ直し、次の世代へと手渡していきたい。

## コンテンツ
- 読みもの（記事）：ルート直下の各 `*.html`
- 見付天神裸祭【特集】：`m011.html` ＋子ページ4本（`hadaka-matsuri-*.html`）
- 文化財コンテンツ群：`/c003.html/` 配下。更新方針は [`docs/bunkazai-guide.md`](docs/bunkazai-guide.md) を参照。
- 文化財データ：`/data/bunkazai.json`

## 編集方針
記事は「である調」。史実と伝承を分け、観光PR・不動産営業に寄せすぎない。文化財ページは磐田市公式情報を一次資料とし、丸写しせず独自に再構成、各ページに出典明記。詳細は `docs/bunkazai-guide.md`。

## 関連記事セクション（内部リンク）
番号付き記事ページ（`m001.html` 等）末尾の「関連記事」欄は `tools/generate_related_articles.py` による自動生成。`data/pages.json` の地区・テーマとタイトル・説明文のキーワード一致で最大6件を選定し、`<!-- im-related:start -->`〜`<!-- im-related:end -->` のマーカー内に静的HTMLとして埋め込む（再実行で置き換わる冪等仕様）。**新規記事を公開したら `data/pages.json` を更新後に `python tools/generate_related_articles.py` を再実行**し、既存記事側の関連リンクにも新記事を行き渡らせること。手書きの「関連記事」見出しを持つページ・機能ページ・移転スタブは自動対象外。

## 公開記事数（磐田の集合知）の同期
トップページ（`index.html`）の「磐田の集合知（公開記事）」の数字は、`data/pages.json` の `count_as_knowledge: true` 件数を唯一の根拠とする（2026-07-10、`c034.html` との全件突き合わせにより一本化。詳細は `docs/pages-ledger.md` の同日エントリを参照）。

数字の更新・整合性チェックは `tools/sync-knowledge-count.mjs` が行う。

```bash
npm run knowledge-count          # data/pages.json の件数を数え、index.html の表示を更新する
npm run knowledge-count:audit    # 更新はせず、監査レポートのみ表示する（c034.html との突き合わせ）
node tools/sync-knowledge-count.mjs --check   # 更新はせず、ズレがあれば exit code 1（CI/デプロイ前チェック向け）
```

監査レポートは、`c034.html`（全記事一覧）に実際に載っているのに `data/pages.json` に未登録、または `count_as_knowledge` が `true` になっていないページを検出する。**新規記事を作成したら、`data/pages.json` への登録と同時に `npm run knowledge-count` を実行**し、表示を最新化すること。

`npm run guard`（`scripts/predeploy_guard.py`、`npm run deploy` から自動実行）は内部で `node tools/sync-knowledge-count.mjs --check` を呼び出しており、件数がズレたままでは通らない。ズレを検出したら `npm run knowledge-count` で解消してからコミットする。

表示先を増やしたい場合（例：集合知説明ページ `c033.html` にも数字を出す）は、対象要素に `data-knowledge-count` 属性を付け、`tools/sync-knowledge-count.mjs` の `DISPLAY_TARGETS` にファイルパスを追加すればよい。


## 公開・デプロイ手順（再発防止）

**2026-07-15以降、公開は`git push`のみ**（下記「本番の巻き戻り・記事消失を防ぐ安全装置」参照。このマシンのwranglerはPages権限を持たないため、`npm run deploy`・`wrangler pages deploy`はもう実行できない）。

標準手順は次の通り。

```powershell
git pull --ff-only
npm.cmd run build
npm.cmd run knowledge-count
npm.cmd run guard
git add <更新ファイル>
git commit -m "..."
git push
```

pushすると、Cloudflare Pages側のGit連携が自動でビルド・デプロイする（そのビルドコマンドが`predeploy_guard.py`を実行する）。`npm run guard`をpush前に手元でも実行しておくと、ビルド失敗に気づくのが早い。`guard`は次を満たさない場合に失敗する。

- このリポジトリの `main` ブランチであること。
- `git fetch origin main` 後の `HEAD` が `origin/main` と一致していること。
- 追跡済みファイルに未コミット変更がないこと（未追跡の作業用フォルダは対象外）。
- `data/new-articles.json`、`index.html`、`updates.html` が同期済みで、最近公開した記事が欠落していないこと。
- 公開記事数・ページ台帳・新着台帳の件数が既知の下限を下回っていないこと。

記事作成中の通常確認は従来通り `npm.cmd run guard` を使う。これは Git 同期までは要求しない。公開直前だけ `npm.cmd run guard:deploy` が必須になる。

## 本番の巻き戻り・記事消失を防ぐ安全装置（2026-07-15）

過去に、このリポジトリの別クローン（別マシン／別ツールの作業コピー）から `wrangler pages deploy .` を直接実行し、Git に見えない形で本番が古い版に巻き戻る事故が繰り返し起きた。対策は最終的に次の4つ。

1. **このマシンのwranglerログインから、Cloudflare Pagesの権限を完全に除去済み（2026-07-15）**。`wrangler login --scopes ...`で`pages:write`スコープを含めずに再認証したため、**このマシンのどのツール・どのフォルダから`wrangler pages deploy`を叩いても、Cloudflare API側で認証エラーになり物理的に失敗する**（`wrangler pages deployment list`等の閲覧も同様に失敗する）。Workers・D1・KV等、他プロジェクトで使う権限は維持したまま動作確認済み。これにより「直接アップロードで本番が巻き戻る」という事故の経路そのものが無くなったため、常時監視タスク（watchdog）は不要と判断し削除した（旧SKILL.mdは`C:\Users\fujig\.claude\scheduled-tasks\iwata-monogatari-deploy-watchdog\`に退避してある）。**Pages関連の操作は今後、Cloudflareダッシュボードから行うか、必要な作業のためだけに一時的に`wrangler login --scopes ... pages:write ...`で再認証すること。**
2. **Cloudflare Pages の Build Command に `predeploy_guard.py` を設定済み**（プロジェクト設定、Cloudflareダッシュボード側）。`main` へ `git push` すると Cloudflare Pages が自動ビルドするが、そのビルドコマンドが `python scripts/predeploy_guard.py` を実行する。必須記事の欠落・公開記事数の後退・`data/new-articles.json` 等の同期崩れがあれば**そのビルドだけが失敗し、本番は直前の正常な版のまま残る**（pushしたコミット自体は履歴に残るが、公開はされない）。動作確認済み（正常内容→ビルド成功、意図的に記事を1件消した内容→ビルド失敗を確認）。
3. **`verify_no_silent_removal()`**: Cloudflare Pages のビルドはシャロークローン（`git rev-parse --is-shallow-repository` → `true`、親コミットにアクセスできない）で動くため、コミット単体では「前より記事が減っていないか」を判定できない。そこで `predeploy_guard.py` は本番の `data/pages.json` / `data/new-articles.json` を直接fetchし、**現在ライブで公開中のURLが、今回のビルドに1件でも欠けていたら（`_redirects`で明示的に301されている場合を除き）ビルドを失敗させる**。手動更新が必要な固定リストは無く、何を公開しても自動的にチェックされる。
4. **GitHub branch protection（main）**: force-push・ブランチ削除を禁止済み。2026-07-15、`enforce_admins`を有効化し、管理者権限アカウント（普段pushしている`iwata-monogatari`自身を含む）にも適用されるようにした（通常のpushには影響なし・確認済み）。
5. **中身の巻き戻り検知（2026-07-17）**: URL集合の比較（上記3や`check_live_sync.py`）は「URLは残っているが本文が古い版に戻った」タイプの巻き戻りを検知できない。そこで`release_guard.py stamp`が保護URL（トップ・updates・c034・カナリア・新着120件）ごとに**正規化済み本文ハッシュ（`content_sha256`）**を記録し、`check-live`／`check-live-content`が本番の実ページを並列fetchして突き合わせる。正規化では、配信時にmiddlewareが差し替える4ブロック（`header.gh-site`／`footer.im-foot`／`section.article-policy[data-common]`／`section.local-property-note[data-common]`）とCloudflare自動注入のアナリティクスビーコン・改行コード差を両側から除去するため、それ以外の本文が1文字でも本番とスタンプ時ローカルで食い違えば検知される。`data/pages.json`・`data/new-articles.json`は生バイト（改行正規化のみ）で照合。起動時チェック`check_live_sync.py`はこの`check-live`を呼ぶため、**セッション開始時に中身の先祖返りも自動検知される**（タイムアウト時はスキップせず失敗扱い）。デプロイ時の`check-build`には含めない（正当な編集も本文を変えるため。古いツリーのデプロイは従来通り世代番号の単調増加チェックが止める）。

## 新規記事ページ作成チェックリスト
既存記事をテンプレートにコピーして新規ページを作るときに漏れがちな項目。2026-07-04、r036.html作成時に `.article-policy` のスタイル定義（旧記事側の`<style>`に個別ベタ書きされていた）を引き継ぎ忘れて見た目が崩れる事故があったため、共通CSS化とあわせてルール化した。

1. **重複チェックを先に行う**：`data/pages.json` のtitle/summaryと新テーマのキーワードを突合し、既存記事と全面的に重複しないか確認する。重複時の統合方法はメモリ「磐田物語 重複記事統合ルール」を参照。
2. **採番**：地区プレフィックス＋3桁連番。ディスク実体・`data/pages.json`・`sitemap.xml`を直前に再確認してから確保する（新規プレフィックスの勝手な新設は禁止）。
3. **`<head>`**：title（`｜磐田物語`）／meta description／og:title・description・type=article・locale／canonical／favicon一式／`<link rel="stylesheet" href="/assets/css/site-header.css">`／`<link rel="stylesheet" href="/assets/css/iwata-area-color.css">`。ページ固有の演出以外のCSSは、既存記事の`<style>`を丸ごとコピーする前に「これは共通CSS（iwata-area-color.css等）に定義済みか」を確認する。定義済みならページ側に再定義しない（重複・引き継ぎ漏れの温床になる）。
4. **`<body class="area-{slug}">`**：地区に紐づく記事には地区クラスを1つ付与（複数地区にまたがる場合は地区番号が最小の地区）。
5. **ヘッダー・フッター**：`<header class="gh-site">`・`<footer class="im-foot">`の中身はCloudflare Pages Functionsが配信時に`partials/`の内容へ差し替えるため、新規ページでは**中身を空にしてよい**（`<footer class="im-foot"></footer>`）。既存記事の多くは旧来のフォールバック用ナビ・フッターHTMLをそのまま持っているが、新規作成時にそれを律儀にコピーする必要はない。
6. **記事末尾の定型ブロック（2026-07-04〜: content呼び出し方式に変更）**：`<section class="local-property-note">`（不動産導線）と`<section class="article-policy">`（著者・参考資料・作成方針）は、header/footerと同じ仕組みで`partials/local-property-note.html`・`partials/article-policy.html`から配信時に中身を差し込む。**新規記事では中身を空にして`data-common`属性を付けるだけでよい**：
   ```html
   <section class="local-property-note" aria-labelledby="local-property-note-title" data-common></section>
   <section class="article-policy" data-common></section>
   ```
   `functions/_middleware.js`が`section.article-policy[data-common]`・`section.local-property-note[data-common]`を検出したときだけ中身を差し替える（`data-common`が無いセクションには手を出さない）。これは、既存記事の一部が参考資料・作成方針を記事ごとにカスタマイズしている（丸写し不可・重複回避の観点で個別の断り書きが要ることがある）ため、header/footerのように無条件で上書きしてしまうと過去の記事の個別カスタム文言を消してしまうからである。**記事固有の参考資料・作成方針を書きたい場合だけ、`data-common`を付けずに中身を直接書く**（この場合は必要なCSSが`iwata-area-color.css`の`.article-policy`/`.local-property-note`で足りているか確認する）。
   - 背景：スタイルだけを共通CSS化しても、コピペのたびにCSSの引き継ぎ漏れ（r036.html, 2026-07-04）や特異度の低い汎用ルールとの衝突（見出し下の罫線残り）が繰り返し発生したため、**中身ごと呼び出す方式**に変更した。
7. **関連記事の自動挿入位置**：`<!-- im-related:start -->`が無い状態で公開し、`local-property-note`の直前（無ければ`footer.im-foot`の直前、それも無ければ`</body>`の直前）に挿入される前提で構造を作る。手書きで「関連記事」という見出しを入れると自動生成の対象から外れるので注意。
8. **公開後に更新する一式**：`data/pages.json`（新規エントリ or 統合時は旧エントリのurl/titleを上書き）／`sitemap.xml`／該当地区ポータル（`0100X-*.html`）／`c034.html`全記事一覧／`theme.html`／必要なら`data/new-articles.json`／`python tools/generate_related_articles.py`の再実行。
