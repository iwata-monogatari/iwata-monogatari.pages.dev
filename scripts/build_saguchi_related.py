"""Build reviewed reading links for every Saguchi catalogue item.

The catalogue's original metadata is never changed. Links describe related
subjects, places or material types; they do not assert that an article quotes
the exact object. Specific objects override the broader category defaults.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {
    '引札': ['m140', 'c020'],
    '銅印': ['c020', 'c098'],
    '浮世絵': ['m017', 'c020'],
    '商家・地域資料': ['c098', 'c020'],
    '地図・絵図': ['c131', 'c011'],
    '名所・観光案内': ['c020', 'c131'],
    '鉄道・交通': ['c130', 'c020'],
    '道中・講社': ['m017', 'c136'],
    '記念・行事': ['c020', 'c131'],
    '絵馬': ['m019', 'c133'],
    '屋台・祭礼写真': ['matsuri-hadaka', 'm102'],
    '絵葉書': ['m088', 'c020'],
}
OVERRIDES = {
    **dict.fromkeys(['ts-41', 'ts-42'], ['c055', 'c056', 'c020']),
    **dict.fromkeys(['ts-66', 'ts-67', 'ts-68'], ['r039', 'c136', 'c020']),
    **dict.fromkeys(['ts-76', 'ez2-1', 'ez2-2'], ['m001', 'm017', 'c011']),
    **dict.fromkeys(['ts-84', 'ts-85'], ['f003', 'c098']),
    **dict.fromkeys(['ts-61', 'ts-62', 'ts-63'], ['c069', 'c020']),
    **dict.fromkeys(['eh-23', 'eh-32'], ['m019', 'm127']),
}


def build():
    catalogue = json.loads((ROOT / 'data/saguchi-shiryo.json').read_text(encoding='utf8'))
    manifest = json.loads((ROOT / 'data/search/manifest.json').read_text(encoding='utf8'))
    metadata = json.loads((ROOT / manifest['metadata'].lstrip('/')).read_text(encoding='utf8'))
    records = {r['id']: r for r in metadata['records']}
    items = {}
    for item in catalogue['items']:
        ids = DEFAULTS.get(item['cat'], ['c020', 'c131'])
        if item['cat'] == '絵葉書':
            subject = item['name'] + ' ' + item.get('grp', '')
            if re.search('天神|裸祭|はだか|浜垢離|屋台|神輿|鬼踊り', subject):
                ids = ['matsuri-hadaka', 'm102']
        items[item['id']] = OVERRIDES.get(item['id'], ids)
    articles = {}
    for ids in items.values():
        assert 2 <= len(ids) <= 3 and len(set(ids)) == len(ids)
        for id in ids:
            record = records[id]  # Only public, canonical search records may be linked.
            articles[id] = {'url': record['url'], 'title': record['title']}
    assert len(items) == len(catalogue['items']) == catalogue['_meta']['count']
    return {'version': 1, 'articles': articles, 'items': items}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = ROOT / 'data/saguchi-related.json'
    result = build()
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert target.read_text(encoding='utf8') == text, 'Run build_saguchi_related.py'
    else:
        target.write_text(text, encoding='utf8')
    print(f'Saguchi related reading: {len(result["items"])} items, {len(result["articles"])} articles')
