# 磐田の航空史｜空の日に読む飛行場と暮らし

- 投稿日：2026-09-16（Get-Dateで当日確認）
- slug：20260916-iwata-aviation-history
- 狙いクエリ：磐田 航空史／検索意図：know
- 読者：磐田と飛行機の関わりを地域の記録から知りたい市民
- 一言メモ：空欄。持論原則5「読者にまだ決めない自由を残す」を使用。
- 主張を立てる段落：「私なら、結び付ける前に三つの欄を作る」内。「分からないつながりを、読みやすさのために埋めない。」を私の判断として明示する。
- 体験ストック：なし・意見として記述。実地訪問の創作なし。

## 結論ブロック（200字以内）

Q. 磐田と飛行機の関わりは、どこから読めば分かる？

A. 磐田の航空史を暮らしから読む入口は、福長飛行場跡、旧田原小学校の飛行機見物、天竜飛行場と竜洋の学童を扱う本編3本です。場所の記録、回想、戦時の教育を分けて読みます。飛行機見物の場所や二つの飛行場の関係は、この3本だけで結び付けません。空の日を機に、分かることと未確認事項を一つずつ控える読み方を案内します。

## h2構成

1. 空の日を入口に、磐田の航空史を三つの記録で読む
2. 福長飛行場跡は、掛塚と天竜川の場所の記録から
3. 旧田原小学校では、飛行機見物を回想として読む
4. 天竜飛行場と学童生活は、本編の留保まで読む
5. 私なら、結び付ける前に三つの欄を作る
6. よくある質問

## FAQ3問

- 磐田の航空史は、どの記事から読むとよいですか。
- 旧田原小学校の飛行機見物は、福長飛行場での出来事ですか。
- 空の日に合わせて、飛行場跡を見学できますか。

## 内部リンクと逆リンク

- /r065.html（福長飛行場跡。逆リンクも本文へ追記）
- /u042.html（旧田原小学校の回想）
- /r029.html（天竜飛行場と竜洋の学童）
- 著者プロフィール：/c007.html

## 原文照合と線引き

- 国土交通省 https://www.mlit.go.jp/koku/15_bf_000222.html ：空の日9月20日、空の旬間9月20〜30日。公表日表示なし。2026-09-16確認。
- 3本の本編、上記公的情報、プロフィール、著者写真：HTTP 200確認。
- r065は細かな所在地・現況・管理主体を保留。年の列挙から開設年や規模を推定しない。
- u042は『田原の史話』本文19〜25頁の回想紹介。原著の再調査はしていない。見物先の同定はしない。
- r029は飛行場での学童の具体的作業、空襲の日時・件数等を未確認とする。底本の書誌も未確認。年表や現存遺構の断定を転記しない。
- 新たな史実、二つの飛行場の同一視、三つの記録の因果関係は主張しない。
- 意外な事実：飛行機見物がピアノと並んで学校の回想に収められること。
- 迷い：興味を引く一続きの物語にしたいが、見物先を確定する根拠がない。
- 今日できる確認：場所・見聞きしたこと・学校生活の3欄に、記事の記載と未確認事項を分けて記す。

## 画像

- 組み込みimage_genで新規生成。16:9の写真調。
- 内容：現代の机に無印の木製プロペラ機の模型、白紙の学校ノート、資料カード3枚。人物・文字・ロゴなし。史実再現ではなく読書の静物。
- 公開先：/assets/blog/20260916-iwata-aviation-history-cover.webp（1440×810以下）
- タイトル直下へ掲載し、生成イメージである旨と実在の場所の復元でない旨を明記。

## 技術方針

ユーザーの今回の指示に従い、個別記事もdata/pages.jsonへcount_as_knowledge:falseで登録する。knowledge-count、関連記事生成、ブログ検査・生成、build、release:stamp、guardを実行。逆リンク・sitemap・feed・LLM索引を同じコミットに含め、git pushで公開する。

## 公開前査読

- 自己査読：新たな史実の追加なし。回想と施設の同定を分離。意外な事実・言い切り・迷い・今日できる確認を本文で確認。
- 結論153字。本文約3,700字。FAQ3問と構造化データ4種、日付、出典HTTP 200、逆リンク、画像実在・参照一致を検査済み。
- 禁止語の独立grepは変更対象のHTML・JSON・XML全10ファイルで0件。今回SVGは作成していない。
- 初回の台帳書き込み時、PowerShellのパイプ文字コードにより日本語が変換され、タグ重複検査に失敗。UTF-8で再作成して修正。文字化け・禁止フレーズも0件。
- build_blog.py --checkは33記事すべて合格。knowledge-countは1106本のまま。公開前guardは全17項目合格。
- 関連記事生成は実行済み。既存記事群の無関係なURL表記変更は取り除き、r065の明示的な逆リンクを保持。
- 画像：1440×810、87,744バイト。ローカルのブラウザーでタイトル直下の表示を確認。

## 最終画像プロンプト（組み込みimage_gen）

Use case: photorealistic-natural. Asset type: Japanese local history blog hero, landscape 16:9. Create a photorealistic editorial still life illustrating reading about aviation and everyday school life in Iwata: a small unmarked wooden propeller airplane model, an open blank school notebook and three blank archival cards arranged on a contemporary wooden reading desk near a softly lit window. Modern staged tabletop, clearly objects used for study, no reenactment or real historical site. Natural soft daylight, quiet thoughtful mood, realistic wood and paper textures, restrained colors, high quality wide composition. No people, no text or letters, no logos, no watermark, no photographs or maps on the papers, no military emblems. Exactly 16:9 aspect ratio.
