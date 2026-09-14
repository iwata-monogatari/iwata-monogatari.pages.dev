# 磐田と馬の歴史｜埴輪・鉄路・供養を読む

- 投稿日：2026-09-14（Get-Date で確認）
- 狙いクエリ：磐田 馬 歴史／意図：know
- 読者：馬と暮らしの接点を知りたい磐田の市民
- 使用原則：一言メモ空欄のため stance 原則5「まだ決めない自由」。史料間のつながりを急いで決めず、判断材料を一つ増やす。
- 一言メモを立てる段落：「私なら、つながらない部分も残す」の意見段落。「馬が出てくるだけで、ひと続きの歴史にしてはいけません。」
- 体験ストック：なし・意見として記述。現地訪問談を作らない。
- 結論ブロック：磐田と馬の歴史は、二子塚古墳の馬具と馬形埴輪、中泉軌道の馬力化申請、馬頭観音の解説という本編3本から読めます。それぞれ、馬を飾る品、輸送の動力、供養への入口です。3本を一つの伝統の証拠にはせず、個別の石塔の場所や建立年代は未確認として残します。
- h2：動物愛護週間を読書の入口に／二子塚古墳は馬具と埴輪を見比べる／中泉軌道は「馬力化の申請」を読む／馬頭観音は一般解説と個別の石塔を分ける／私なら、つながらない部分も残す／よくある質問
- FAQ：磐田と馬の歴史はどの本編から読めますか／中泉軌道は最初から馬が引いていましたか／本編で市内の馬頭観音の場所はわかりますか
- 内部リンク：/u038.html、/c060.html、/c070.html（著者リンク /c007.html）
- 逆リンク：c060.html の馬力化を扱う節の末尾に読書案内を追記。
- 意外な事実：本編が紹介する馬具と馬形埴輪の同じ鈴杏葉の意匠。
- 言い切り：史料の空白を物語で埋めない、という書き手の方針。
- 自分の迷い：馬という共通項で一つの物語にしたくなるが、確認範囲を優先する。
- 一次情報：https://www.env.go.jp/nature/dobutsu/aigo/pickup/week.html 。9月20〜26日を2026-09-14に照合。公表日表示なし。
- 史実の扱い：本編の記述への案内に限定。中泉軌道の申請を実施日へ置き換えない。c070の個別石塔未確認を明記。原史料は今回未照合。
- 専用画像：机上の創作馬形土製品・短い模型レール・無銘の石・白紙ノートを写真調16:9で生成。実在資料の復元と誤認させず、タイトル直下に生成イメージ注記付きWebPを置く。
- 登録：ユーザー指定に従い個別記事を pages.json に count_as_knowledge:false で登録。knowledge-count → related生成 → release:stamp。公開は git push のみ。

## 公開前自己査読

- 結論122字、本文約3,550字。FAQ3問と構造化データ4種、日付・JSON・画像参照を機械検査して合格。
- 一言メモ相当の主張、意見としての一人称、意外な意匠の対応、自分の迷いを本文で確認。事実と評価を段落で分離。
- 出典URLは環境省と本編3本・プロフィールでHTTP 200確認。本編は同期確認と同じUser-Agentとcachebustで取得。
- 初回保存時にPowerShellのパイプ文字コードで日本語が壊れ、タグ検査が不合格。UTF-8で再保存し、文字化け残存・タグ・タイトル・本文を再検査して修正済み。
- 禁止語は公開変更対象HTML・JSON・sitemap・feedで独立grep 0件。SVG追加なし。禁止フレーズ0件。
- knowledge-countは1106本のまま。関連記事生成を実行し、今回と無関係な全体書式の再生成767ブロックは復元。逆リンクはc060本文に保持。
- ローカルのブラウザでタイトル・本文・タイトル直下の専用画像を表示確認。
- 体験ストック未使用のため共有台帳の更新なし。一時資料ファイルは作成していない。

## 画像生成記録

- 方式：built-in image_gen。公開ファイル：assets/blog/20260914-iwata-horse-history-cover.webp（1440×810、98,820 bytes）。
- 使用プロンプト：Use case: photorealistic-natural. Asset type: unique Japanese local history blog hero for 磐田と馬の歴史｜埴輪・鉄路・供養を読む. Generate a photorealistic studio still-life, wide 16:9 landscape. On a wooden reading desk: a small deliberately simplified modern terracotta horse craft object, a short detached model railway track, a small plain uninscribed rounded stone, and an open entirely blank notebook. These separate objects suggest reading about horse-shaped haniwa, transport and memorials; clearly a contemporary tabletop arrangement, not an archaeological exhibit or reconstruction of a real historic place or sacred statue. Natural soft side light, quiet earthy textures, editorial photography, balanced composition. No text, no labels, no carvings or inscriptions on stone, no logo, no watermark, no people, no location markers. The model rail and horse remain separate. 16:9.
