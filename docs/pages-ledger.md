# 磐田物語 ページ台帳（pages-ledger）

最終更新：2026-06-25

地区別ポータルの正式台帳は `data/pages.json`。本ファイルは人間が読むための要約・運用メモ。

## 地区ページ一覧

| No | 地区ID | 地区名 | URL | ヒーロー図 | 改修状況 |
|---|---|---|---|---|---|
| 01001 | mitsuke | 見付地区 | 01001-mitsuke.html | assets/img/district-hero/01001-mitsuke-hero.svg | ✅ 完成（基盤プレート） |
| 01002 | nakaizumi | 中泉地区 | 01002-nakaizumi.html | assets/img/district-hero/01002-nakaizumi-hero.svg | ✅ 完成 |
| 01003 | mikuriya | 御厨地区 | 01003-mikuriya.html | assets/img/district-hero/01003-mikuriya-hero.svg | ✅ 完成 |
| 01004 | toyoda | 豊田地区 | 01004-toyoda.html | assets/img/district-hero/01004-toyoda-hero.svg | ✅ 完成 |
| 01005 | nanbu | 南部地区 | 01005-nanbu.html | assets/img/district-hero/01005-nanbu-hero.svg | ✅ 完成 |
| 01006 | koyo | 向陽地区 | 01006-koyo.html | assets/img/district-hero/01006-koyo-hero.svg | ✅ 完成 |
| 01007 | ryuyo | 竜洋地区 | 01007-ryuyo.html | assets/img/district-hero/01007-ryuyo-hero.svg | ✅ 完成 |
| 01008 | fukude | 福田地区 | 01008-fukude.html | assets/img/district-hero/01008-fukude-hero.svg | ✅ 完成（記事準備中） |
| 01009 | toyooka | 豊岡地区 | 01009-toyooka.html | assets/img/district-hero/01009-toyooka-hero.svg | ✅ 完成（記事準備中） |

※ 福田の地区IDは必ず `fukude`（`fukuda` にしない）。

## 見付地区（01001）に紐づく記事

m018, m016, m017, m012, m019, m006, m015, m014, m013, m001〜m005, c020, c019（計16件）。
詳細・テーマ分類は `data/pages.json` を参照。

### m017.html

| ID | タイトル | 地区 | 分類 | 概要 | 状態 |
|---|---|---|---|---|---|
| m017 | 東海道・見付宿の面影 | 見付 | 街道・宿場・地域史 | 東海道五十三次二十八番目の宿場、見付宿の歴史と現地痕跡を整理 | 公開中 |

- 改修内容：学術HTML化、東海道・姫街道・天竜川の概念図追加、宿場構成図改善、時代整理表追加、史実・記録・伝承・推定・現地観察ラベル追加、佐口行正氏所蔵資料との本文接続、権利表記整理
- 参考資料：磐田市公開資料、静岡県・磐田市の文化財案内、東海道・旧街道関連資料、現地確認、佐口行正氏所蔵資料

## 共通基盤ファイル

- `assets/css/district.css` … 2カラム・ヒーロー・絞り込み・サイドバー共通スタイル
- `assets/js/district-filter.js` … テーマ別絞り込み（JS無効でも全件表示）
- `assets/img/district-hero/` … 地区別ヒーローSVG

## 運用ルール

- 左サイドバーは `index.html` の `COMMON-LEFT-SIDEBAR` ブロックを正とし、9地区へ同内容を反映する。
- 記事カードを追加したら `data/pages.json` と本ファイル、`sitemap.xml` を更新する。
- 既存URL・既存ページは削除・変更しない。
- `published_at` は新着順整列のための値。未確認のものは `date_provisional:true`（画面には表示しない）。
