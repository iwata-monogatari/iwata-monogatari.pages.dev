"""Join source-checked supplementary learning material without altering the dictionary."""
import json

def expand_materials(root, learning, dictionary):
    addition=json.loads((root/'data/enshu-learning-additions.json').read_text(encoding='utf-8'))
    corpus=json.loads((root/'data/enshu-gunshi-corpus.json').read_text(encoding='utf-8'))
    records={r['id']:r for r in corpus['records']};base_ids={e['id'] for e in dictionary['entries']}
    entries=list(dictionary['entries']);scene_ids={s['id'] for s in learning['scenes']}
    for item in addition['entries']:
        r=item['record'];assert r==records[r['id']] and item['scene'] in scene_ids
        pairs=item['examples'];assert len(pairs)==3
        assert r['form'] not in {e['w'] for e in entries}
        cat='名詞・もの'
        if r['form'] in ['ぬくさい','さらい']:cat='形容・ようす'
        if r['form']=='けなるい':cat='気持ち'
        if r['form'] in ['わざき','ずんだん','とこしよ']:cat='程度・量'
        if r['form']=='よか':cat='語尾・あいさつ'
        if r['form']=='うむす':cat='動作・行い'
        entries.append({'id':r['id'],'w':r['form'],'k':r['form'],'cat':cat,'m':r['gloss'],'ex':pairs[0]['dialect'],'std':pairs[0]['standard'],'learning':{'point':item['point'],'examples':pairs[1:]},'historical':r,'sources':[{'type':'gunshi1921','page':str(r['page']),'village':r['village'],'forms':r['form'],'url':f'/enshu/records/#{r["id"]}'}]})
    learning['entries']=entries
    learning['policy']=addition['policy']
    for s in learning['scenes']:
        s['words']=[wid for wid in s['words'] if wid in base_ids]
        s['words'] += [x['record']['id'] for x in addition['entries'] if x['scene']==s['id']]
        if s['id']=='similar':
            s['words'] += [x['record']['id'] for x in addition['entries'] if x['record']['form'] in ['ねこ','かげ','ゆるい']]
        s['conversations']=[x for x in addition['conversations'] if x['scene']==s['id']]
        assert len(s['conversations'])==2
    assert len(entries)==182 and len(addition['entries'])==48
    return learning

def source_label(e):
    r=e.get('historical')
    return f'1921年 / {r["village"]} / {r["page"]}頁・原表記' if r else ''

def source_href(e):
    from urllib.parse import quote
    return '/enshu/records/#'+e['id'] if e.get('historical') else '/c006?q='+quote(e['w'])+'#'+e['id']
