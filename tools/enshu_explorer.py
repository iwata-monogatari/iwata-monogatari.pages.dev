"""Render an immediately readable word explorer from the existing dictionary."""
import html
from urllib.parse import quote
E=lambda value:html.escape(str(value),quote=True)

def explorer_section(learning, by):
    e=by['ponpon']
    for entry in by.values():
        assert entry['ex'] and entry['std'] and entry['learning']['point']
    options=f'<option value="all">すべてのことば（{len(by)}語）</option><option value="historical">1921年の資料語（48語）</option><option value="dictionary">絵札のある辞典語（134語）</option>'+''.join(f'<option value="{E(s["id"])}">{E(s["title"])}（{len(s["words"])}語）</option>' for s in learning['scenes'])
    starters=''.join(f'<button type="button" class="word-starter" data-word="{wid}" aria-pressed="{str(wid==e["id"]).lower()}" disabled><span>{title}</span><strong>{E(by[wid]["w"])}</strong></button>' for wid,title in [('ponpon','乗り物の話'),('chatto','急いでいるとき'),('amake','空のようす')])
    return f'''<section id="cards" class="flash word-explorer" aria-labelledby="word-explorer-title">
<div class="explorer-heading"><div><p class="eyebrow">182 WORDS / ことばの寄り道</p><h2 id="word-explorer-title">絵と資料で出会う、<br>遠州のひと言。</h2></div><p>「ぽんぽん」って、何のこと？<br>134枚の絵札と48の資料語から、意味と作例を読んでみましょう。</p></div>
<div class="word-starters" aria-label="気になることばから始める">{starters}</div>
<div class="explorer-toolbar"><label for="flash-scene">気になる場面・資料から<select id="flash-scene" disabled>{options}</select></label><p id="flash-progress" role="status" aria-live="polite">1 / 182語</p></div>
<article id="flash-card" class="word-stage" aria-labelledby="flash-word">
<figure class="word-picture"><img id="flash-image" src="/assets/karuta/c006/ponpon-900.webp" srcset="/assets/karuta/c006/ponpon-300.webp 300w, /assets/karuta/c006/ponpon-900.webp 900w" sizes="(max-width:700px) 40vw, 340px" width="900" height="1200" alt="{E(e['w'])}の作例を描いた創作絵札"><figcaption id="flash-caption">生成AIによる創作画</figcaption></figure>
<header class="word-intro"><p id="flash-scene-label" class="eyebrow">外出・乗り物</p><h3 id="flash-word" tabindex="-1">{E(e['w'])}</h3><p id="flash-source-label" class="word-source" hidden></p></header>
<dl class="word-meaning"><dt>こんな意味</dt><dd id="flash-meaning">{E(e['m'])}</dd></dl>
<div class="word-dialogue"><div class="word-example-heading"><p id="flash-example-count">会話の作例 1 / 3</p><button type="button" id="flash-example-next" disabled>次の作例 →</button></div><blockquote id="flash-example">{E(e['ex'])}</blockquote><p class="word-standard">標準語：<span id="flash-standard">{E(e['std'])}</span></p></div>
<div class="word-usage"><p class="word-usage-label">使うとき・読むときのヒント</p><p id="flash-point">{E(e['learning']['point'])}</p><p id="flash-editorial" class="word-editorial">例文は掲載した意味に基づく編集部の作例です。</p></div>
<div class="word-reading-links"><a id="flash-dictionary" href="/c006?q={quote(e['w'])}#ponpon">使い分け・出典を読む →</a><a id="flash-course" href="#scene-outing">この場面のことばを読む →</a></div>
</article>
<div class="word-controls" aria-label="絵札を選ぶ"><button type="button" id="flash-prev" disabled>← ひとつ前</button><button type="button" id="flash-random" disabled>おまかせの一語</button><button type="button" id="flash-next" disabled>次のことば →</button></div>
<div class="word-share"><button type="button" id="flash-copy" disabled>この一語のリンクをコピー</button><p id="flash-message" role="status" aria-live="polite">ほかの絵札を準備しています。</p><label id="flash-share-fallback" hidden>このリンクを選択してコピーできます<input id="flash-share-url" type="text" readonly></label></div>
<div class="word-trails"><a href="#practice"><strong>覚えたら、クイズで試す</strong><span>意味からことばを選ぶ練習も。</span></a><a href="/c008"><strong>自分の一文を遠州弁に</strong><span>変換ツールでことばを試す。</span></a><a href="/enshu/compare/"><strong>似たことばを読み比べる</strong><span>24テーマの比較帖へ。</span></a></div>
<p class="word-image-policy">絵札は意味に基づく生成AIの創作画です。実景の復元や資料の挿絵ではありません。掲載語や作例を、現在の全地域で同じように使うとは限りません。</p>
<noscript>表示中の一語はそのまま読めます。ほかの語は、下の場面別コースや辞典で確かめられます。</noscript>
</section>'''
