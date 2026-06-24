# 磐田物語 リネーム第1弾 実装指示書

作成日：2026-06-25  
対象リポジトリ：`iwata-monogatari/iwata-monogatari.pages.dev`  
作業ID：`rename-batch-001`

## Claude coworkへ渡す4ファイルと配置先

この作業では、以下の4ファイルを使用する。  
Claude coworkは、作業開始前に下記のGitHubリポジトリ内パスへ配置・反映すること。

| No | この出力内のファイル | GitHubリポジトリ内の配置先 | 役割 |
|---:|---|---|---|
| 1 | `work/rename-batch01/instruction.md` | `work/rename-batch01/instruction.md` | 本作業指示書 |
| 2 | `work/rename-batch01/rename-plan.json` | `work/rename-batch01/rename-plan.json` | リネーム対応表 |
| 3 | `data/pages.json` | `data/pages.json` | 正式ページ台帳 |
| 4 | `docs/pages-ledger.md` | `docs/pages-ledger.md` | 人間確認用の台帳 |

## ChatGPT出力先パス

ChatGPTからダウンロードしたファイル一式は、次の構成で出力している。

```text
iwata_rename_batch01_handoff/
├─ data/
│  └─ pages.json
├─ docs/
│  └─ pages-ledger.md
└─ work/
   └─ rename-batch01/
      ├─ instruction.md
      └─ rename-plan.json
```

## 重要ルール

- GitHub上の正式原本は `data/pages.json` とする。
- 人間確認用は `docs/pages-ledger.md` とする。
- `work/rename-batch01/` は今回の作業用資料として残してよい。
- 実行後は、`m001.html`〜`m005.html` が正式ページになっていることを確認する。
- `kai1.html`〜`kai5.html` は削除せず、旧URL案内ページとして残す。
- `sitemap.xml`、内部リンク、親ページ、台帳を必ず同時更新する。


## 目的

`kai1.html`〜`kai5.html` はファイル名だけでは内容が分かりにくく、今後の1000ページ化に向けて管理しづらい。  
見付地区の短い地域別連番として、`m001.html`〜`m005.html` に整理する。

## 確定済みの命名ルール

- 作成日はファイル名に入れない。
- 正式タイトル、地区分類、内容分類、作成日、旧ファイル名は `data/pages.json` で管理する。
- 地区入口ページ `01001-mitsuke.html` などは固定維持する。
- 読み物・特集・史料ページは短い地域別連番を基本にする。

## リネーム対象

| 旧ファイル名 | 新ファイル名 | タイトル | 地区 | 親ページ |
|---|---|---|---|---|
| `kai1.html` | `m001.html` | 見付古地図散歩 第1回 見付の土地と記憶 | 見付 | `01001-mitsuke.html` |
| `kai2.html` | `m002.html` | 見付古地図散歩 第2回 相続される土地 | 見付 | `01001-mitsuke.html` |
| `kai3.html` | `m003.html` | 見付古地図散歩 第3回 道と調査 | 見付 | `01001-mitsuke.html` |
| `kai4.html` | `m004.html` | 見付古地図散歩 第4回 町の中枢 | 見付 | `01001-mitsuke.html` |
| `kai5.html` | `m005.html` | 見付古地図散歩 第5回 手放す前に | 見付 | `01001-mitsuke.html` |

## 実装手順

### 1. 新ファイルを作成する

旧ファイルの本文をそのままコピーし、新ファイルを作成する。

```bash
cp kai1.html m001.html
cp kai2.html m002.html
cp kai3.html m003.html
cp kai4.html m004.html
cp kai5.html m005.html
```

### 2. 旧ファイルは削除せず、移転案内ページにする

既存URLから来た人と検索エンジン向けに、旧ファイルは削除しない。  
`kai1.html`〜`kai5.html` は、以下の形式の移転案内ページに差し替える。

```html
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0; url=NEW_FILE">
  <link rel="canonical" href="https://iwata-monogatari.pages.dev/NEW_FILE">
  <title>ページを移動しました｜磐田物語</title>
</head>
<body>
  <p>このページは移動しました。<a href="NEW_FILE">新しいページへ移動する</a></p>
</body>
</html>
```

各ファイルでは `NEW_FILE` を次のように置換する。

| 旧ファイル | NEW_FILE |
|---|---|
| `kai1.html` | `m001.html` |
| `kai2.html` | `m002.html` |
| `kai3.html` | `m003.html` |
| `kai4.html` | `m004.html` |
| `kai5.html` | `m005.html` |

### 3. 内部リンクをすべて新ファイル名に置換する

リポジトリ全体で以下を置換する。

```text
kai1.html → m001.html
kai2.html → m002.html
kai3.html → m003.html
kai4.html → m004.html
kai5.html → m005.html
```

対象は少なくとも以下。

```text
index.html
01001-mitsuke.html
各記事HTML
sitemap.xml
data/pages.json
docs/pages-ledger.md
```

### 4. sitemap.xml を更新する

`sitemap.xml` には新URLのみを掲載する。

```text
https://iwata-monogatari.pages.dev/m001.html
https://iwata-monogatari.pages.dev/m002.html
https://iwata-monogatari.pages.dev/m003.html
https://iwata-monogatari.pages.dev/m004.html
https://iwata-monogatari.pages.dev/m005.html
```

旧URL `kai1.html`〜`kai5.html` は `sitemap.xml` から外す。

### 5. 台帳を更新する

`data/pages.json` では、各ページを次のように管理する。

```json
{
  "file": "m001.html",
  "title": "見付古地図散歩 第1回 見付の土地と記憶",
  "region_code": "01",
  "region_label": "見付",
  "content_label": "読み物",
  "parent_file": "01001-mitsuke.html",
  "old_file": "kai1.html",
  "redirect_from": ["kai1.html"],
  "rename_batch": "rename-batch-001"
}
```

同様に、`m002.html`〜`m005.html` も更新する。

### 6. 確認項目

- `m001.html`〜`m005.html` が公開URLで表示される。
- `kai1.html`〜`kai5.html` が移転案内ページとして機能する。
- `01001-mitsuke.html` から新ファイルへリンクされている。
- `index.html` から旧ファイル名へのリンクが残っていない。
- `sitemap.xml` に新URLが入り、旧URLが残っていない。
- GitHub全体検索で通常リンクとして `kai1.html`〜`kai5.html` が残っていない。

## コミットメッセージ案

```text
Rename Mitsuke map walk pages to short regional filenames
```

## 注意

この作業は、単なるファイル名変更ではなく、URL・内部リンク・サイトマップ・台帳を同時に更新する作業である。  
旧URLを完全削除すると既存リンクが切れるため、旧ファイルは移転案内ページとして残す。
