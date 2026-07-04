# iwata-monogatari.pages.dev
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

## 新規記事ページ作成チェックリスト
既存記事をテンプレートにコピーして新規ページを作るときに漏れがちな項目。2026-07-04、r036.html作成時に `.article-policy` のスタイル定義（旧記事側の`<style>`に個別ベタ書きされていた）を引き継ぎ忘れて見た目が崩れる事故があったため、共通CSS化とあわせてルール化した。

1. **重複チェックを先に行う**：`data/pages.json` のtitle/summaryと新テーマのキーワードを突合し、既存記事と全面的に重複しないか確認する。重複時の統合方法はメモリ「磐田物語 重複記事統合ルール」を参照。
2. **採番**：地区プレフィックス＋3桁連番。ディスク実体・`data/pages.json`・`sitemap.xml`を直前に再確認してから確保する（新規プレフィックスの勝手な新設は禁止）。
3. **`<head>`**：title（`｜磐田物語`）／meta description／og:title・description・type=article・locale／canonical／favicon一式／`<link rel="stylesheet" href="/assets/css/site-header.css">`／`<link rel="stylesheet" href="/assets/css/iwata-area-color.css">`。ページ固有の演出以外のCSSは、既存記事の`<style>`を丸ごとコピーする前に「これは共通CSS（iwata-area-color.css等）に定義済みか」を確認する。定義済みならページ側に再定義しない（重複・引き継ぎ漏れの温床になる）。
4. **`<body class="area-{slug}">`**：地区に紐づく記事には地区クラスを1つ付与（複数地区にまたがる場合は地区番号が最小の地区）。
5. **ヘッダー・フッター**：`<header class="gh-site">`・`<footer class="im-foot">`の中身はCloudflare Pages Functionsが配信時に`partials/`の内容へ差し替えるため、新規ページでは**中身を空にしてよい**（`<footer class="im-foot"></footer>`）。既存記事の多くは旧来のフォールバック用ナビ・フッターHTMLをそのまま持っているが、新規作成時にそれを律儀にコピーする必要はない。
6. **記事末尾の定型ブロック**：`<section class="local-property-note">`（不動産導線）と`<section class="article-policy">`（著者・参考資料・作成方針）を記事本文の後に配置。両方とも`iwata-area-color.css`にスタイル定義済みなので、クラス名を付けるだけでよい。**注意**：2026-07-04、`.article-policy h2`（「この記事について」見出し）が、ページ自前の`<style>`内にある汎用`h2{border-bottom;padding-bottom;letter-spacing;color 等}`ルールを完全には打ち消せず、見出し下に不要な罫線が残る事故が発生した（CSSの上書きは「宣言したプロパティだけ」が対象で、宣言していないプロパティは特異度が高い側でも下位ルールから漏れて適用され続けるため）。共通CSS側で`border-bottom:none`等を明示して解決済みだが、**共通クラスを新設・流用する際は、そのページの汎用タグ用スタイル（無印`h2`・`p`等）が同じ要素に効いてしまわないか、border/padding/color/letter-spacingまで含めて必ず確認する**こと。「一部のプロパティだけ上書きすれば残りは初期値に戻る」という思い込みは誤り。
7. **関連記事の自動挿入位置**：`<!-- im-related:start -->`が無い状態で公開し、`local-property-note`の直前（無ければ`footer.im-foot`の直前、それも無ければ`</body>`の直前）に挿入される前提で構造を作る。手書きで「関連記事」という見出しを入れると自動生成の対象から外れるので注意。
8. **公開後に更新する一式**：`data/pages.json`（新規エントリ or 統合時は旧エントリのurl/titleを上書き）／`sitemap.xml`／該当地区ポータル（`0100X-*.html`）／`c034.html`全記事一覧／`theme.html`／必要なら`data/new-articles.json`／`python tools/generate_related_articles.py`の再実行。
