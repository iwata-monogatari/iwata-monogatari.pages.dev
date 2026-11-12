"""Build compact courses and a short-round quiz using the canonical learning data."""
import html
from urllib.parse import quote
E=lambda x:html.escape(str(x),quote=True)

def build_study(learning,by,art_words,teasers):
    tiles=[];lessons=[];scenes=learning['scenes']
    for number,s in enumerate(scenes,1):
        sid,title,words=s['id'],s['title'],s['words'];image=art_words[number-1]
        assert image in by and len(words)==len(set(words)) and words
        tiles.append(f'<a class="course course-{sid}" href="#scene-{sid}" data-course="{sid}"><div class="course-art" aria-hidden="true"><img src="/assets/karuta/c006/{image}-300.webp" width="300" height="400" loading="lazy" alt=""></div><div class="course-copy"><span class="course-number">{number:02} / {len(words)}語</span><strong>{E(title)}</strong><p>{E(teasers[number-1])}</p><span class="course-bottom">この場面を読む <span aria-hidden="true">→</span></span></div></a>')
        items=[]
        for wid in words:
            e=by[wid];x=e['learning']['examples'][0]
            items.append(f'<article class="lesson-word"><div class="lesson-word-heading"><h3>{E(e["w"])}</h3><a href="/enshu/?word={wid}#cards" data-explore-word="{wid}">絵札で見る ↗</a></div><p class="lesson-meaning">{E(e["m"])}</p><div class="lesson-example"><p>{E(x["dialect"])}</p><p class="lesson-standard">標準語：{E(x["standard"])}</p></div><details class="lesson-more"><summary>使い分け・資料を読む</summary><p>{E(e["learning"]["point"])}</p><a href="/c006?q={quote(e["w"])}#{wid}">3つの作例・出典を辞典で読む →</a></details></article>')
        nxt=scenes[number%len(scenes)]
        lessons.append(f'<section id="scene-{sid}" class="scene" data-scene="{sid}" aria-labelledby="scene-title-{sid}"><div class="scene-heading"><span class="scene-number" aria-hidden="true">{number:02}</span><div><p class="eyebrow">選んだ場面 / {len(words)}語</p><h2 id="scene-title-{sid}">{E(title)}</h2></div></div><p class="scene-intro">{E(s["intro"])}</p><div class="scene-actions"><a class="scene-play" href="#practice" data-quiz-scene="{sid}">この場面を3問で試す →</a><a href="#scene-{nxt["id"]}" data-course="{nxt["id"]}">次は「{E(nxt["title"])}」へ →</a></div><div class="lesson-list">{"".join(items)}</div><div class="scene-end"><a href="#practice" data-quiz-scene="{sid}">読んだら、3問で確かめる →</a><a class="course-return" href="#courses">コースを選び直す ↑</a></div></section>')
    courses=f'<section id="courses" class="study-courses"><div class="courses-heading"><div><p class="eyebrow">暮らしからひらく、12の入口</p><h2>今日は、どの場面で話す？</h2></div><p>場面を選ぶ → 意味と会話を読む → 3問で試す。<br>気になる一語は、絵札にも寄り道できます。</p></div><div class="courses">{"".join(tiles)}</div><div class="course-view-controls"><p id="course-status" role="status">12コースから、好きな場面を選べます。</p><button type="button" id="courses-show-all" aria-controls="course-lessons" disabled>全コースをまとめて読む</button></div><p class="courses-credit">絵札は各語の作例をもとに制作した生成AIの創作画です。</p></section>'
    options='<option value="all">すべての場面（134語）</option>'+''.join(f'<option value="{s["id"]}">{E(s["title"])}（{len(s["words"])}語）</option>' for s in scenes)
    categories=''.join(f'<option>{c}</option>' for c in ['語尾・あいさつ','形容・ようす','気持ち','程度・量','動作・行い','名詞・もの'])
    practice=f'''<section id="practice" class="practice study-quiz" aria-labelledby="practice-title"><p class="eyebrow">TRY / まずは3問から</p><h2 id="practice-title">読んだことばで、ひと遊び。</h2><p class="quiz-lead">答えた後は、絵札と会話で確かめます。間違えた語だけ、もう一度試すこともできます。</p>
<div class="quiz-setup"><label for="quiz-scene">遊ぶ場面<select id="quiz-scene">{options}</select></label><label for="quiz-length">問題数<select id="quiz-length"><option value="3" selected>3問</option><option value="5">5問</option><option value="10">10問</option></select></label><button id="quiz-start" type="button" disabled>3問ではじめる</button></div>
<details class="quiz-settings"><summary>出題方向・分類を変える</summary><div class="controls"><label for="quiz-direction">出題方向<select id="quiz-direction"><option value="meaning">ことば → 意味</option><option value="word">意味 → ことば</option></select></label><label for="quiz-category">語の分類<select id="quiz-category"><option value="all">すべての分類</option>{categories}</select></label></div></details><p id="quiz-setup-status" role="status"></p>
<div id="quiz-board" hidden><div class="quiz-progress-row"><p id="quiz-progress" role="status"></p><progress id="quiz-meter" value="0" max="3" aria-label="回答済みの問題数"></progress></div><div class="quiz-question-block"><figure id="quiz-question-picture"><img id="quiz-question-image" width="300" height="400" alt=""></figure><div><p id="quiz-mode-label" class="eyebrow"></p><h3 id="quiz-question" tabindex="-1"></h3></div></div><div class="quiz-hint-row"><button type="button" id="quiz-hint-button" aria-controls="quiz-hint">ヒントを読む</button><p id="quiz-hint" hidden></p></div><div id="quiz-options" role="group" aria-label="答えを選ぶ"></div><div id="quiz-feedback" aria-live="polite" hidden></div><button id="quiz-next" type="button" hidden>次の問題へ →</button></div>
<div id="quiz-summary" aria-live="polite"></div><noscript>クイズはJavaScriptを使います。場面別の意味と作例、絵札の最初の一語はそのまま読めます。</noscript></section>'''
    return courses,'<!-- course-lessons:start --><div id="course-lessons">'+''.join(lessons)+'</div><!-- course-lessons:end -->',practice
