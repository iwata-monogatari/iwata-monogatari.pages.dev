"""Build compact courses and a short-round quiz using the canonical learning data."""
import html
from urllib.parse import quote
from enshu_materials import source_label, source_href
E=lambda x:html.escape(str(x),quote=True)

def conversation_cards(scene,by):
    cards=[]
    for c in scene['conversations']:
        turns=''.join(f'<div class="conversation-turn"><span aria-label="話者{t["speaker"]}">{t["speaker"]}</span><div><p>{E(t["dialect"])}</p><p class="conversation-standard">標準語：{E(t["standard"])}</p></div></div>' for t in c['turns'])
        links=''.join(f'<a href="/enshu/?word={wid}#cards" data-explore-word="{wid}">{E(by[wid]["w"])}</a>' for wid in c['words'])
        cards.append(f'<article class="conversation-card" id="conversation-{c["id"]}"><h4>{E(c["title"])}</h4>{turns}<p class="conversation-point">{E(c["point"])}</p><div class="conversation-words" aria-label="会話のことばを確かめる">{links}</div></article>')
    return '<div class="scene-conversation-section"><h3>2つの会話で、使い方を読む</h3><p class="conversation-policy">掲載語の意味に基づく編集部の作例です。実際の発話の引用ではありません。</p><div class="scene-conversations">'+''.join(cards)+'</div></div>'

def build_study(learning,by,art_words,teasers):
    tiles=[];lessons=[];scenes=learning['scenes']
    for number,s in enumerate(scenes,1):
        sid,title,words=s['id'],s['title'],s['words'];image=art_words[number-1]
        assert image in by and len(words)==len(set(words)) and words
        tiles.append(f'<a class="course course-{sid}" href="#scene-{sid}" data-course="{sid}"><div class="course-art" aria-hidden="true"><img src="/assets/karuta/c006/{image}-300.webp" width="300" height="400" loading="lazy" alt=""></div><div class="course-copy"><span class="course-number">{number:02} / {len(words)}語</span><strong>{E(title)}</strong><p>{E(teasers[number-1])}</p><span class="course-bottom">この場面を読む <span aria-hidden="true">→</span></span></div></a>')
        items=[];historic=[]
        for wid in words:
            e=by[wid];x=e['learning']['examples'][0]
            is_old=bool(e.get('historical'));source=f'<p class="lesson-source">{E(source_label(e))}</p>' if is_old else ''
            more=''
            if is_old:
                for pair in [{'dialect':e['ex'],'standard':e['std']},e['learning']['examples'][1]]:
                    more+=f'<div class="lesson-example"><p>{E(pair["dialect"])}</p><p class="lesson-standard">標準語：{E(pair["standard"])}</p></div>'
            card=f'<article class="lesson-word" id="learn-{sid}-{wid}"><div class="lesson-word-heading"><h3>{E(e["w"])}</h3><a href="/enshu/?word={wid}#cards" data-explore-word="{wid}">{"一語で読む" if is_old else "絵札で見る"} ↗</a></div>{source}<p class="lesson-meaning">{E(e["m"])}</p><div class="lesson-example"><p>{E(x["dialect"])}</p><p class="lesson-standard">標準語：{E(x["standard"])}</p></div><details class="lesson-more"><summary>{"残り2作例・資料を読む" if is_old else "使い分け・資料を読む"}</summary><p>{E(e["learning"]["point"])}</p>{more}<a href="{source_href(e)}">{"記録と原画像を読む" if is_old else "3つの作例・出典を辞典で読む"} →</a></details></article>'
            (historic if is_old else items).append(card)
        nxt=scenes[number%len(scenes)]
        archive=f'<div class="historical-course"><h3>1921年の資料から、{len(historic)}語</h3><p class="conversation-policy">原表記と記録地を付けています。文は意味を学ぶための置換作例です。</p><div class="lesson-list">{"".join(historic)}</div><a class="archive-quiz" href="#practice" data-quiz-scene="{sid}" data-quiz-source="historical">この場面の資料語だけで試す →</a></div>' if historic else ''
        lessons.append(f'<section id="scene-{sid}" class="scene" data-scene="{sid}" aria-labelledby="scene-title-{sid}"><div class="scene-heading"><span class="scene-number" aria-hidden="true">{number:02}</span><div><p class="eyebrow">選んだ場面 / {len(words)}語・2会話</p><h2 id="scene-title-{sid}">{E(title)}</h2></div></div><p class="scene-intro">{E(s["intro"])}</p><div class="scene-actions"><a class="scene-play" href="#practice" data-quiz-scene="{sid}">この場面を3問で試す →</a><a href="#scene-{nxt["id"]}" data-course="{nxt["id"]}">次は「{E(nxt["title"])}」へ →</a></div>{conversation_cards(s,by)}<h3 class="lesson-group-title">辞典のことばを読む</h3><div class="lesson-list">{"".join(items)}</div>{archive}<div class="scene-end"><a href="#practice" data-quiz-scene="{sid}">読んだら、3問で確かめる →</a><a class="course-return" href="#courses">コースを選び直す ↑</a></div></section>')
    courses=f'<section id="courses" class="study-courses"><div class="courses-heading"><div><p class="eyebrow">暮らしからひらく、12の入口</p><h2>今日は、どの場面で話す？</h2></div><p>場面を選ぶ → 意味と会話を読む → 3問で試す。<br>気になる一語は、絵札にも寄り道できます。</p></div><div class="courses">{"".join(tiles)}</div><div class="course-view-controls"><p id="course-status" role="status">12コースから、好きな場面を選べます。</p><button type="button" id="courses-show-all" aria-controls="course-lessons" disabled>全コースをまとめて読む</button></div><p class="courses-credit">絵札は各語の作例をもとに制作した生成AIの創作画です。</p></section>'
    options=f'<option value="all">すべての場面（{len(by)}語）</option>'+''.join(f'<option value="{s["id"]}">{E(s["title"])}（{len(s["words"])}語）</option>' for s in scenes)
    categories=''.join(f'<option>{c}</option>' for c in ['語尾・あいさつ','形容・ようす','気持ち','程度・量','動作・行い','名詞・もの'])
    practice=f'''<section id="practice" class="practice study-quiz" aria-labelledby="practice-title"><p class="eyebrow">TRY / まずは3問から</p><h2 id="practice-title">読んだことばで、ひと遊び。</h2><p class="quiz-lead">答えた後は、絵札と会話で確かめます。間違えた語だけ、もう一度試すこともできます。</p>
<div class="quiz-setup"><label for="quiz-scene">遊ぶ場面<select id="quiz-scene">{options}</select></label><label for="quiz-length">問題数<select id="quiz-length"><option value="3" selected>3問</option><option value="5">5問</option><option value="10">10問</option></select></label><button id="quiz-start" type="button" disabled>3問ではじめる</button></div>
<details class="quiz-settings"><summary>出題方向・分類・資料語を選ぶ</summary><div class="controls"><label for="quiz-source">出題することば<select id="quiz-source"><option value="all">辞典と資料語（182語）</option><option value="dictionary">辞典の134語</option><option value="historical">1921年の資料48語</option></select></label><label for="quiz-direction">出題方向<select id="quiz-direction"><option value="meaning">ことば → 意味</option><option value="word">意味 → ことば</option></select></label><label for="quiz-category">語の分類<select id="quiz-category"><option value="all">すべての分類</option>{categories}</select></label></div></details><p id="quiz-setup-status" role="status"></p>
<div id="quiz-board" hidden><div class="quiz-progress-row"><p id="quiz-progress" role="status"></p><progress id="quiz-meter" value="0" max="3" aria-label="回答済みの問題数"></progress></div><div class="quiz-question-block"><figure id="quiz-question-picture"><img id="quiz-question-image" width="300" height="400" alt=""></figure><div><p id="quiz-mode-label" class="eyebrow"></p><h3 id="quiz-question" tabindex="-1"></h3></div></div><div class="quiz-hint-row"><button type="button" id="quiz-hint-button" aria-controls="quiz-hint">ヒントを読む</button><p id="quiz-hint" hidden></p></div><div id="quiz-options" role="group" aria-label="答えを選ぶ"></div><div id="quiz-feedback" aria-live="polite" hidden></div><button id="quiz-next" type="button" hidden>次の問題へ →</button></div>
<div id="quiz-summary" aria-live="polite"></div><noscript>クイズはJavaScriptを使います。場面別の意味と作例、絵札の最初の一語はそのまま読めます。</noscript></section>'''
    return courses,'<!-- course-lessons:start --><div id="course-lessons">'+''.join(lessons)+'</div><!-- course-lessons:end -->',practice
