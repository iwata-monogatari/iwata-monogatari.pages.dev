"""国研配布XLSXから磐田市地点を抽出する（openpyxlを使用、原本は変更しない）。

python tools/import_c006_fpjd.py /path/to/FPJD-db-2025-10-07.xlsx
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    'data-ID': 'id', '地点番号': 'point', '質問番号': 'question',
    '項目名': 'item', '複数回答番号': 'answer_number', '回答語形': 'form',
    '注記': 'note', 'NLJ地図番号': 'map_number',
    'NLJ地図見出しコード': 'map_code', 'NLJ地図見出し': 'map_heading',
}


def main():
    import openpyxl
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('xlsx', type=Path)
    args = parser.parse_args()
    wb = openpyxl.load_workbook(args.xlsx, read_only=True, data_only=True)
    rows = iter(wb.active.values)
    headers = list(next(rows))
    if not set(FIELDS).issubset(headers):
        raise ValueError('配布ファイルの列構成が変わっています。原本を確認してください。')
    records = []
    for values in rows:
        r = dict(zip(headers, values))
        if r.get('都道府県') == '静岡県' and r.get('市区町村') == '磐田市':
            item = {dest: str(r.get(src) if r.get(src) is not None else '') for src, dest in FIELDS.items()}
            item['corrections'] = {k: str(v) for k, v in r.items() if '修正' in str(k) and v is not None}
            records.append(item)
    wb.close()
    if len(records) != 287 or len({r['point'] for r in records}) != 1:
        raise ValueError('2025-10-07版の287回答・1地点と一致しません。更新内容を確認してください。')
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('重複data-ID')
    data = {
        'title': '全国方言分布調査（FPJD）磐田市地点の回答',
        'credit': '国立国語研究所の共同研究「方言の形成過程解明のための全国方言分布調査」の成果に基づく。',
        'source': 'https://www2.ninjal.ac.jp/hogen/dp/fpjd/fpjd_index.html',
        'download': 'https://www2.ninjal.ac.jp/hogen/dp/fpjd/FPJD-db-2025-10-07.zip',
        'notes_source': 'https://www2.ninjal.ac.jp/hogen/dp/fpjd/fpjd_data_notes.html',
        'edition': '2025-10-07', 'accessed': '2026-10-12',
        'source_sha256': hashlib.sha256(args.xlsx.read_bytes()).hexdigest(),
        'scope': '磐田市の1地点。地区別・世代別の普及率を示す調査ではない。287回答は211質問への複数回答を含む。',
        'records': records,
    }
    (ROOT / 'data/c006-fpjd.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'FPJD: {len(records)}回答 / {len({r["question"] for r in records})}質問')


if __name__ == '__main__':
    main()
