"""Reproduce counts for Iwata Monogatari's 1921 Gunshi SELECTED records."""
from pathlib import Path
import csv, json, hashlib
from collections import Counter
folder=Path(__file__).resolve().parent
csv_path=folder/'records.csv'
with csv_path.open(encoding='utf-8-sig',newline='') as stream:
    rows=list(csv.DictReader(stream))
forms=Counter(r['form'] for r in rows)
regions=Counter(r['village'] for r in rows)
repeated={f:n for f,n in forms.items() if n>1}
result={'records':len(rows),'original_forms':len(forms),'region_labels':len(regions),
        'repeated_forms':repeated,'repeated_rows':sum(repeated.values()),
        'top3_records':sum(n for _,n in regions.most_common(3)),
        'regions':dict(regions.most_common()),'csv_sha256':hashlib.sha256(csv_path.read_bytes()).hexdigest()}
manifest_path=folder/'manifest.json'
if manifest_path.exists():
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert result['csv_sha256']==manifest['csv_sha256'],'CSV checksum mismatch'
    for key,value in manifest['expected'].items():
        assert result[key]==value,(key,result[key],value)
print(json.dumps(result,ensure_ascii=False,indent=2))
