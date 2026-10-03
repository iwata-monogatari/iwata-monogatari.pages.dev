# 磐田の家康伝承の調べ方：記事設計

- 起動ID：18b4c1d4d0944a9b96399a32e43918b0
- 投稿日：2026-10-03（Get-Dateで当日確認）
- slug：20261003-iwata-ieyasu-source-memo
- タイトル：磐田の家康伝承の調べ方｜本編から作る確認メモ
- 狙いクエリ：磐田 家康 伝承 調べ方
- 検索意図：do。磐田で聞いた家康の逸話の根拠を確かめたい市民。
- 持論：一言メモ空欄のため原則5「まだ決めない自由」を使用。
- 主張を立てる段落：「私は、未確認と書けるメモを残したい」。未確認を残すのは調査の失敗ではない、と意見として明示する。
- 体験ストック：なし。訪問・聞き取りを創作せず意見として記述。

## 結論ブロック（200字以内）

Q. 磐田で聞いた家康の話、本当かどうかは何から調べる？

A. まず本編で資料名・書き手・成立時期を拾い、出来事の時期とは別欄にします。中泉御殿の滞在記録、後世の軍記、土地の伝承を分け、どの一文を何が支えるかを記録します。本編に書かれていない成立年や原文は「未確認」のまま残し、参考資料へ戻ることが次の一歩です。

## h2構成

1. 家康企画展の前に、資料の名前を見る準備をする
2. n048で、書き手と資料の性格を分ける
3. n052とt037で、何を裏付ける資料かを確かめる
4. 家康伝承の確認メモを一枚作る
5. 私は、未確認と書けるメモを残したい
6. よくある質問

## FAQ（3問）

1. 古い本に家康の話があれば、史実として扱えますか？
2. 資料の成立年が本編にないときは、どう書きますか？
3. 企画展で磐田の家康伝承も確かめられますか？

## 内部リンク・逆リンク

- /n048：卜斎記と関原始末記の性格の違い。
- /n052：滞在記録と土地の伝承の区別。
- /t037：寄進伝承と近世文書の確認範囲。
- 逆リンク：n052「四、滞在記録と伝承を分けて読む」の本文に案内を1文追加。
- HTTP取得は拡張子なしの公開URLで200を確認。候補の.html表記では403のため、本文には200のURLを使う。

## 根拠・重複確認・留保

- 静岡市 https://www.city.shizuoka.lg.jp/s6725/s013125.html を2026-10-03に原文照合。更新2026-09-02、会期2026-10-10〜11-29、会場は静岡市歴史博物館。静岡市内に遺された資料を中心に家康と豊臣政権の関係を読む企画。磐田の個々の伝承の展示は未確認。
- 本編3本を読書対象として実読。原史料を直接照合したと装わない。成立年・写本の書写年・引用箇所は不足しており、埋めない。
- t037は嘆願の個別年月日・内容・結果を未確認と明記。寄進の逸話全体が文書で証明されたと扱わない。
- ブログ62件のタイトル・slugを照合。同一テーマなし。城之崎城二説比較は説の比較、本稿は資料ごとの確認メモの実作業。本編の伝承論の再論証もしない。

## 画像

- 組み込みimage_genを使用。写真調16:9。無地の資料本、白紙ノート、3枚の白紙カード、鉛筆、虫眼鏡を置いた現代の机。文字・人物・ロゴなし。実在史料や場所の証拠写真ではない構図。
- 生成プロンプト：Use case: photorealistic-natural. Asset type: original Japanese local history blog hero for an article about researching Tokugawa Ieyasu traditions in Iwata through sources and keeping verification notes. Landscape 16:9 photograph-style still life of a contemporary study desk, several closed plain cloth-bound reference books, an open completely blank notebook with three separate blank cream index cards, simple wooden pencil, small magnifying glass. The separate cards suggest separating source title, writer, and date. Quiet warm natural window light, realistic paper and wood texture, restrained scholarly atmosphere, overhead oblique composition, ample breathing room. This is a conceptual staged illustration, not a historical document or any real museum or real historical location. No people, no writing, no readable characters, no letters, no numbers, no symbols, no logos, no watermarks, no personal information. All book covers, spines, pages, and cards must be blank.
- 公開ファイル：assets/blog/20261003-iwata-ieyasu-source-memo-cover.webp（1440×810）。タイトル直下に配置し生成画像と明記。

## 公開前後の確認

ブログゲート、構造化データ4種、FAQ3問、200字以内結論、画像参照・実在・寸法、日付一致、禁止語の独立検索、出典HTTP 200、逆リンク、索引・feed・sitemap、release stampとguard、最新main照合、git push、本番title・本文・画像を確認する。

## 公開前検査結果

- 本文約3,940字、結論127字、FAQ3問、構造化データ4種、タイトル32字以内、日付一致、内部リンク3先・逆リンク、画像実在と1440×810 WebP、禁止フレーズ0件をスクリプトで確認。
- 禁止語を変更対象HTML・JSON・sitemap・feedに独立検索し0件。SVGの新規作成・変更なし。
- build_blog.py --check：63件、品質ゲート未達0。release:stamp後のguard：本編1106件全17規則合格、publish guard passed。
- 自己査読：意外な点＝同日の説明でも宿泊地と饗応描写で根拠が異なる。言い切り＝未確認欄を想像で埋めない。迷い＝楽しさと留保の分量。意見と本編紹介を段落で分離。
- 公開直前に静岡市の更新日・会期・会場・展示趣旨を再照合、すべて一致。
- 関連記事生成は指定順で実行。ただし既存765ページのリンク拡張子・見出し等を置換したため、今回と無関係な生成差分は取り消した。n052には逆リンク1文のみを保持。
- authorの参照は標準形を使用。著者欄の肩書きとPerson.sameAsは上位の編集憲章の必須条件を優先し、全記事を変更する正規化処理は行っていない。
- ローカルブラウザでタイトル直下の専用画像と生成注記、結論ブロックの表示を目視確認。
