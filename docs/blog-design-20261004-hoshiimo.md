# 磐田の干し芋：記事設計・確認記録

- 起動ID：3ed8c00618a44a0ea6a533d9355f2da0
- 公開日：2026-10-04（Get-Dateで確認）
- slug：20261004-iwata-hoshiimo-trade-reading
- 狙いクエリ：磐田 干し芋 歴史／検索意図：know
- 読者：秋のさつまいもをきっかけに、磐田の食と商いの歴史を知りたい方。
- 一言メモ：空欄。持論の原則5「まだ決めない自由」を使用。
- 原則を立てる段落：「私は、発祥の答えより確認材料を一つ増やしたい」の冒頭。
- 体験ストック：なし。意見として記述。
- 内部リンク：c098、c074、n046。逆リンク：c098の甘藷切干の節。

## 結論ブロック（140字）

磐田の干し芋の歴史を読む入口は、本編「磐田市の産業史」にある甘藷切干と八百庄商店の出荷記録です。次に商店街と中泉の本編を読むと、食べ物から町の商いへ関心を広げられます。ただし、この3本だけで発祥や個別の販売経路は決められません。資料名を一つ控え、分からない点を残す読書を勧めます。

## 構成とFAQ

収穫期から商いの記録へ → c098の出荷記録 → c074の商店街 → n046の中泉 → 発祥の結論を急がない意見 → 資料名と問いを分けるメモ → FAQ。

FAQは「最初に読む本編」「発祥を判断できるか」「商店街の記事で販売店が分かるか」の3問。

## 裏取りと自己査読

- 農林水産省中国四国農政局の指定ページで収穫期9〜11月を照合。公表日の表示なし。磐田の当年の収穫状況に転用しない。
- 本編3本は正規URL（拡張子なし）でHTTP 200を確認。既存の本文と留保を読んで案内。
- 芳名簿・図録の原本は未照合。数値・起源・販売先・輸送経路を新しく主張しない。
- 意外な事実：干し芋の読書の入口が出荷先の芳名簿になること。
- 言い切り：確かめていない関係を面白さのためにつながない。
- 迷い：分かりやすい答えを渡したい気持ちと、未確認を残す判断。
- 結論字数、FAQ、構造化データ4種、日付、リンク、禁止表現、画像の実在・参照を機械検査。
- 関連記事生成を実行後、本題と無関係な既存ページの生成差分を取り除き、c098への逆リンクを残した。

## 専用生成画像

- 方式：組み込みimage_gen。新規生成、使い回しなし。
- 保存先：assets/blog/20261004-iwata-hoshiimo-trade-reading-cover.webp
- 公開用：1440×810、WebP、110110 bytes。
- 写真調の静物。タイトル直下に配置し、生成イメージと明記。
- 最終プロンプト：

```text
Use case: photorealistic-natural. Asset type: unique cover illustration for a Japanese local history reading guide titled 磐田の干し芋｜商いの記録へつなぐ本編3本. Create a photorealistic editorial still life, landscape exactly 16:9. On a contemporary plain wooden reading table, a small ceramic plate holding several naturally golden flat slices of Japanese dried sweet potato (hoshiimo), two whole reddish purple sweet potatoes, and an open entirely blank cream notebook with a simple pencil. Soft autumn daylight, natural food textures, quiet warm restrained composition, oblique overhead viewpoint. This is a conceptual present-day still life connecting food with reading records of trade, not a recreation of historical evidence. No people, no identifiable location, no old document imitation, no writing or letters anywhere, no logos, no watermark. All notebook pages entirely blank. Output one high quality image.
```
