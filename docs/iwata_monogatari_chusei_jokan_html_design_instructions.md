# 磐田物語「中世上巻」HTMLデザイン実装指示書

作成日：2026-06-28  
対象リポジトリ：`iwata-monogatari/iwata-monogatari.pages.dev`  
適用フェーズ：中世史料・読み物コンテンツ群（中世上巻）の新規作成および共通スタイリング

---

## 1. 概要と基本方針

本指示書は、「磐田物語」における中世史（主に鎌倉時代から戦国時代前期まで）を扱うコンテンツ群（総称「中世上巻」）を新規HTMLとして作成・公開する際のデザインおよびマークアップ規則を定めたものである。

中世の磐田は、遠江国の政治の中心地であった「見付国府・守護所」、大規模な伊勢神宮領「鎌田御厨」、天竜川東岸の主要荘園「池田庄」、そして水陸交通の要衝たる「福田湊」「掛塚湊」など、多様な歴史の層が重なる地域である。
これらの歴史的価値を伝えるため、単なる史実の箇条書きにとどまらず、**「土地の記憶」「道や川の痕跡」を五感でたどるビジュアルと読みやすさ**をデザインで表現する。

---

## 2. 対象ページとURL設計

「中世上巻」を構成する新規ページは、磐田物語の地区別連番ルールおよびテーマ別命名規則に従い、以下のファイル名で新規作成する。

| ファイル名 | 想定タイトル | 地域分類 (コード) | 親ページ | 主なテーマ・見どころ |
| :--- | :--- | :--- | :--- | :--- |
| `m030.html` | 遠江国守護所の見付と中世国府の変容 | 見付 (01) | `01001-mitsuke.html` | 鎌倉・室町期の守護所設置と、古代国府から中世都市への発展 |
| `u020.html` | 伊勢神宮領「鎌田御厨」の繁栄と人々の祈り | 御厨 (03) | `01003-mikuriya.html` | 鎌田神明宮を中心とする御厨の成立、寄進地系荘園の生活像 |
| `t033.html` | 遠州最古の荘園「池田庄」と熊野御前の足跡 | 豊田 (04) | `01004-toyoda.html` | 天竜川東岸の要衝、熊野信仰（行興寺）と平家・源氏の歴史 |
| `f022.html` | 中世の海運を支えた「福田湊」と太田川の舟運 | 福田 (08) | `01008-fukude.html` | 遠州灘の海上交易拠点、年貢米輸送と地域流通網 |
| `t034.html` | 霊峰・社山と古代・中世の山岳信仰・砦の記憶 | 豊田 (04) | `01004-toyoda.html` | 山岳修験の霊地、戦国期の今川・徳川攻防における砦群 |
| `k012.html` | 在地武士「匂坂氏」「向笠氏」と中世の館跡 | 向陽 (06) | `01006-koyo.html` | 匂坂城・向笠城を拠点とした土豪の台頭と室町・戦国期の動向 |

---

## 3. デザインシステム（色彩・タイポグラフィ）

磐田物語の既存世界観（和モダン・地域歴史アーカイブ）を踏襲し、中世の深みと厳かさを表現するためのスタイルを適用する。

### 3.1 カラーパレット (CSS変数)

```css
:root {
  /* 基本背景・テキスト */
  --color-bg-base: #f7f2e9;        /* 生成り（全体の背景色） */
  --color-text-main: #2c2a29;      /* 墨色（本文） */
  --color-text-muted: #65605c;     /* 鈍色（補助テキスト・メタ情報） */

  /* ブランドカラー・アクセント */
  --color-accent-brown: #a6713e;   /* 琥珀茶（見出し・リンクホバー） */
  --color-accent-darkbrown: #85562c; /* 渋茶（主要ボーダー・強調用） */
  --color-accent-pine: #46624a;    /* 松緑（中世特集のテーマカラー・バッジ等） */

  /* 背景・枠線 */
  --color-bg-card: #ffffff;        /* 白（カード背景） */
  --color-bg-note: #efebe2;        /* 薄生成り（研究ノート・補足コラム背景） */
  --color-border-subtle: #e6dfd5;  /* 枠線・区切り線 */
}
```

### 3.2 タイポグラフィ

- **大見出し・中見出し (`h1`, `h2`, `h3`)**:
  和風の伝統と信頼感を醸し出すため、Google Fontsの **Shippori Mincho (しっぽり明朝)** を適用する。
  ```css
  font-family: "Shippori Mincho", "Georgia", serif;
  font-weight: 600;
  color: var(--color-accent-darkbrown);
  ```
- **本文・キャプション**:
  モバイル環境での可読性を担保するため、すっきりしたデザインの **Zen Kaku Gothic New (Zen角ゴシックNew)** を使用する。
  ```css
  font-family: "Zen Kaku Gothic New", "Helvetica Neue", Arial, sans-serif;
  line-height: 1.8;
  letter-spacing: 0.03em;
  color: var(--color-text-main);
  ```

---

## 4. 共通コンポーネントとHTMLマークアップ構造

中世上巻の各ページは、以下の統一されたクラス構成でマークアップを行う。

### 4.1 基本骨格 (Template)

```html
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="[ここに100〜120文字の要約を記載]">
  <title>[記事タイトル] ｜ 磐田物語</title>
  
  <!-- ファビコン定義 -->
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
  <link rel="icon" href="/favicon-16.png" type="image/png" sizes="16x16">
  <link rel="apple-touch-icon" href="/favicon-180.png" sizes="180x180">

  <!-- 外部CSS -->
  <link rel="stylesheet" href="/assets/css/site-header.css">
  <link rel="stylesheet" href="/assets/css/district.css">
  <link rel="stylesheet" href="/assets/css/iwata-area-color.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@600;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body>

  <!-- 共通ヘッダー -->
  <header class="site-header">
    <div class="header-inner">
      <a href="/" class="brand-logo">磐田物語</a>
      <nav class="header-nav">
        <a href="/bunkazai.html">文化財</a>
        <a href="/matsuri.html">祭り</a>
        <a href="/chizu.html">地図</a>
      </nav>
    </div>
  </header>

  <!-- メインコンテンツ -->
  <main class="container">
    <article class="reading-article">
      <!-- 記事ヘッダー -->
      <header class="article-header">
        <span class="category-badge badge-chusei">中世上巻</span>
        <h1 class="entry-title">[記事のタイトル]</h1>
        <div class="entry-meta">
          <span class="region-label">[地域名]地区</span>
          <time datetime="2026-06-28">2026.06.28</time>
        </div>
      </header>

      <!-- 本文エリア -->
      <section class="article-body">
        <p>本文テキスト（である調で統一）。独自の語り口で磐田の歴史を解説します...</p>
        
        <h2>中見出し（h2）</h2>
        <p>本文テキスト...</p>

        <!-- 補足コラム・現地情報：.rnote (Research Note) -->
        <aside class="rnote">
          <h4 class="rnote-title">【土地の記憶】現地を歩くヒント</h4>
          <p>現在の地形や小字、道路の曲がり角に残るかつての境界線など、現地確認のポイントを記載します。</p>
        </aside>

        <h3>小見出し（h3）</h3>
        <p>本文テキスト...</p>

        <!-- 年表コンポーネント：.timeline -->
        <div class="timeline-container">
          <h4 class="timeline-title">関連略年表</h4>
          <table class="timeline">
            <tbody>
              <tr>
                <td class="time-year">1190年</td>
                <td class="time-event">源頼朝、上洛の途上で池田宿に立ち寄り、熊野御前と対面したと伝わる。</td>
              </tr>
              <tr>
                <td class="time-year">1338年</td>
                <td class="time-event">足利尊氏、見付を国衙・守護所の拠点として重視。</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 出典・参考資料：.sourcebox -->
      <footer class="article-footer">
        <div class="sourcebox">
          <h5>主な参考資料・出典</h5>
          <ul>
            <li>『磐田市誌』中世編</li>
            <li>『静岡県史』通史編2（中世）</li>
            <li>磐田市公式ウェブサイト（文化財情報）</li>
          </ul>
          <p class="disclaimer">※本記事は、公式な一次資料および地域伝承をもとに「磐田物語」編集部が独自に構成した読み物です。現地の安全や私有地への立ち入りには十分ご注意ください。</p>
        </div>

        <!-- 不動産・家のご相談導線：.local-property-note -->
        <div class="local-property-note">
          <h4>磐田での「家と土地」の相続・空き家相談</h4>
          <p>見付や中泉など、古い歴史を持つ地区では、先代から受け継いだ土地の売却・境界調査・実家の片付けについてのご相談を専門家チームがお受けしています。お気軽にお問い合わせください。</p>
          <a href="https://fudosan.atawi.link/souzoku/?utm_source=iwata_monogatari&utm_medium=referral&utm_campaign=context_link" class="cta-button">相続・不動産相談窓口へ</a>
        </div>
      </footer>
    </article>

    <!-- 下部ナビゲーション -->
    <nav class="article-nav">
      <a href="/[親ページのファイル名].html" class="nav-back">← [地域名]地区ポータルへ戻る</a>
      <a href="/" class="nav-home">磐田物語トップへ</a>
    </nav>
  </main>

  <!-- 共通フッター -->
  <footer class="site-footer">
    <p class="copyright">&copy; 2026 磐田物語 All Rights Reserved.</p>
  </footer>

</body>
</html>
```

---

## 5. 品質・SEO基準

品質監査レポートおよび文化財ガイドラインに則り、以下の要件を厳守する。

1. **文字数要件**:
   - 各新規ページの本文文字数は **2,500〜3,500文字** 程度を維持すること。低評価ページ（2,000字未満）とならないよう、時代背景、地形的考察、伝承と史実の切り分け、現地へのアクセスなどを網羅して充実したコンテンツとする。
2. **である調の徹底**:
   - 文体は「〜である」「〜だ」で統一し、客観的かつ温かみと敬意のある文章を作成する。
3. **SEOベストプラクティス**:
   - `<title>` に「｜ 磐田物語」を付与。文字数は30〜40字程度。
   - `<meta name="description">` はページ固有の内容を記述し、100〜120字に収める。
   - `<h1>` はタイトル部分 of 1箇所のみとする。
   - 見出し構造（`h2` -> `h3`）の階層構造を崩さないこと。
4. **モバイルレスポンシブ**:
   - スマートフォン（画面幅 600px 以下）で閲覧した際、左右余白（`padding`）が適切に縮小され、文字がはみ出さないようにすること。
   - `.timeline` などのテーブル要素は、スマホ表示時に `display: block` または `overflow-x: auto` を適用して横スクロール可能に設計する。

---

## 6. 公開・反映プロセス

新規作成したHTMLファイルをリポジトリへ反映し、正しく公開するために以下の手順を実行する。

### Step 1: 台帳ファイルの更新
1. `/data/pages.json` に新規ページのメタデータを追加する。
   ```json
   {
     "file": "m030.html",
     "title": "遠江国守護所の見付と中世国府の変容",
     "region_code": "01",
     "region_label": "見付",
     "content_label": "読み物",
     "parent_file": "01001-mitsuke.html",
     "old_file": "",
     "rename_batch": "chusei-jokan-001"
   }
   ```
2. `/docs/pages-ledger.md` に人間確認用の行を追加する。

### Step 3: サイトマップへの追加
- `sitemap.xml` の末尾（`</urlset>` の直前）に、作成したすべての新規URLを挿入する。

### Step 4: 親ページ（ポータル）からのリンク追加
- 各地区のポータルページ（例：`01001-mitsuke.html` など）の「読み物・歴史解説」セクションに、新記事へのリンクカード/リストを追記する。

### Step 5: 動作検証
- ローカル環境で `npm run dev` または簡易Webサーバーを起動し、表示崩れがないか、および内部リンクが正しく遷移するかを確認する。
- スマートフォン表示の表示崩れがないか確認する。

### Step 6: Gitコミット＆パブリッシュ
- 以下のコミットメッセージでGitコミットを行い、リモートへプッシュすることで Cloudflare Pages への自動デプロイ（公開）を行う。
  ```text
  feat: add medieval history pages (chusei jokan) and design instructions
  ```

---
以上。
