# 池田の渡し歴史風景館｜秋の見学前に読む本編

- 投稿日：2026-09-17（Get-Dateで木曜日・当日確認）
- slug：20260917-ikeda-ferry-museum-visit
- 狙いクエリ：池田の渡し歴史風景館 見学／検索意図：local
- 読者：秋の連休に池田を訪れ、展示と地域の歴史を結び付けたい人。
- 一言メモ：空欄。持論原則1「理念より、家計・防災・段取りの実利で語る」を使用。
- 主張を立てる段落：「私なら、展示の前に開館日を確かめる」。見たい気持ちだけでは扉は開かない、という段取りの判断を明示。
- 体験ストック：なし・意見として記述。訪問・電話確認の実話を創作しない。

## 結論ブロック（200字以内）

Q. 池田の渡し歴史風景館へ行く前に、何を読んでおけばいい？

A. 本編3本から「船賃は誰に分配されたか」「川を渡れない旅人はどこで待ったか」「渡河はどう判断されたか」を選んで読むと、展示で確かめたい問いができます。市の案内は無料・9〜17時ですが、9月21〜23日の開館日は個別に明記されていません。訪問日を決める前に文化振興課へ確認し、展示では資料名と年代を控える見学を勧めます。

## h2構成

1. 9月21〜23日の休日と、風景館の開館は分けて確認
2. 船賃の問いは「渡船経済のしくみ」から
3. 宿の問いは「池田宿の賑わいと本陣の記憶」から
4. 渡河の問いは「池田の渡し」から
5. 私なら、展示の前に開館日を確かめる
6. よくある質問

## FAQ3問

- 池田の渡し歴史風景館の料金と見学時間は？
- 9月21〜23日は開館していますか？
- 本編3本を全部読まないと見学できませんか？

## 内部リンクと逆リンク

- /t048.html：船賃の分配と維持費。
- /t016.html：宿と待ち時間。
- /t004.html：渡河と川留め。本文に見学準備記事への逆リンクを1文追加。
- 著者プロフィール /c007.html。

## 原文照合・線引き

- 国立天文台 https://www.nao.ac.jp/news/topics/2025/20250203-rekiyoko.html ：2025年2月3日公表。2026年9月21日敬老の日、22日休日、23日秋分の日。
- 磐田市 https://www.city.iwata.shizuoka.jp/shisetsu_guide/toshokan_bunka/tenji/1003510.html ：無料、9〜17時、池田300-3。毎週月曜（国民の休日に当たるときは翌日）、毎月最終火曜、12月28日〜1月4日休館。文化振興課0538-37-8550。
- 市の施設欄の休館規定と、ページ末尾の情報発信元の月曜休館注記は区別する。連休3日間の実際の開館日は未確認。暦から推定して開館と断定しない。
- 本編の概要・問いへの案内に限る。展示品の個別一覧、船賃の現代円換算、当時の正確な船着場と現在地の一致は未確認。
- t004・t016の架橋・渡船終了の語り方に幅がある。終了年の単純化や沿革の再構成はしない。
- 意外な事実：本編t048では、渡船収益を受け取る権利自体が売買・分割の対象と説明される。
- 言い切り：見たい気持ちだけでは扉は開かない。開館確認も見学の一部だ。
- 迷い：予習の問いを増やしすぎると展示を読む楽しさを狭めないか。
- 今日できる確認：希望日を添えて開館を確認し、3本から問いを1つ選ぶ。

## 画像と公開手順

- 組み込みimage_genで記事専用の写真調静物を生成。横長16:9、幅1440px以下WebP。
- 内容：秋の光の机に無地の冊子3冊、白紙ノートと鉛筆、現代の木製船模型。文字・ロゴ・人物なし。実在施設や史実の復元としない。
- 保存先：assets/blog/20260917-ikeda-ferry-museum-visit-cover.webp。
- タイトル直下に掲載し、生成イメージ・模型は実際の渡船や展示品を再現しない旨を明記。
- ユーザー指定を優先しdata/pages.jsonへ個別登録（count_as_knowledge:false）、knowledge-count→関連記事生成。ブログ生成・検査、build、release:stamp、guardを実施。feed・sitemap・LLM索引・逆リンクを同じコミットに含めgit push。本番titleと画像を確認。

## 公開前査読

- 結論161字、本文約3,600字。FAQ3問と構造化データ4種、JSON妥当性、日付、内部リンク3本＋プロフィール、逆リンク、画像実在・台帳参照一致を機械検査。
- build_blog.py --checkは34記事すべて合格。禁止語は変更対象HTML・JSON・XMLの独立grepで0件。SVGの新規作成・変更なし。禁止フレーズと相対表現も0件。
- 公的出典2本・本編3本・プロフィール・著者写真はHTTP 200。Python標準User-Agentではサイト側が403を返したため、通常ブラウザーUser-Agentで確認。
- 原則1の段取りの判断、意外な事実、迷いを自己査読。私の意見と本編・公的案内を段落で区別。架橋時期や渡船終了の単純化、展示品一覧の創作なし。
- 集合知は1106本を維持。関連記事生成で生じた767本の無関係な整形・URL変更は取り除き、t004の本文逆リンク1文を保持。
- 画像は1440×810 WebP、95,604バイト。生成画像を目視し、文字・人物なしと内容との対応を確認。ローカルプレビューはポート制限・ブラウザーのfile URL制限により実施できず。本番のブラウザー表示を公開後に確認する。
- 本文の品質ゲート未達なし。台帳のテーマ値は登録済みのroad-trafficに修正。

## 最終画像プロンプト（組み込みimage_gen）

Use case: photorealistic-natural. Create a unique horizontal 16:9 editorial photograph-style hero for a Japanese blog about preparing to visit Ikeda ferry history museum: on a simple wooden reading desk, three closed unmarked booklets, an open completely blank notebook and pencil, with a small clearly modern handmade wooden ferry-boat model beside them. Soft early autumn daylight. Calm tactile paper and wood, elegant natural composition, full width landscape 16:9. This is a conceptual still life about reading and asking questions before a museum visit, not a real museum interior or historical reconstruction. No people, no text or writing anywhere, no logos, no watermarks, no historical documents, no identifiable actual building.
