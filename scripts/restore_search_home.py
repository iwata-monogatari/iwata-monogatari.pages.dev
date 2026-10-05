"""Forward UI recovery. Leaves every article, asset, ledger, D1 and current search intact.
Default is read-only. --apply requires clean main and successful live sync first.
Reject concurrent home edits instead of silently overwriting them.
"""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fingerprint(text):
 text=re.sub(r'(data-knowledge-count[^>]*>)\s*\d+\s*(<)',r'\1\2',text)
 return hashlib.sha256(re.sub(r'(<ul class="new-article-list news-list"[^>]*>).*?(</ul>)',r'\1\2',text,flags=re.S).encode()).hexdigest()
def restored_home(root=ROOT):
 baseline=json.loads((root/'docs/search-ui-baseline.json').read_text(encoding='utf8'))
 current=(root/'index.html').read_text(encoding='utf8')
 if fingerprint(current)!=baseline['supportedHomeFingerprint']:raise ValueError('Homepage changed concurrently: review the UI inverse manually; no files changed.')
 old=baseline['home']
 # Remove the old hand-written corpus and its handler completely. The latest search page is the adapter.
 old=re.sub(r'<script>\s*\(function\(\)\{\s*var ARTICLES = \[.*?</script>','<script defer src="/assets/js/home-search.js"></script>',old,flags=re.S)
 if 'var ARTICLES' in old:raise ValueError('Legacy search block was not removed.')
 old=re.sub(r'<div class="search-box">.*?</div>', '<div class="home-search"><form id="home-search-form" action="/search/" method="get"><label for="q">地名・人物名・言葉で検索</label><div class="query-row"><input id="q" name="q" type="search"><button type="submit">検索</button></div><p id="home-search-error" role="alert" hidden></p></form><p><a href="/search/">テーマ・地区を選んで探す</a> ／ <a href="/c034">全記事一覧</a></p></div>',old,count=1,flags=re.S)
 old=re.sub(r'<script\b[^>]*src="https://fujigaoka-analytics-worker[^>]*>.*?</script>','',old,flags=re.S)
 old=re.sub(r'<span([^>]*class="chip"[^>]*data-q=[^>]*)>(.*?)</span>', r'<button type="button"\1>\2</button>', old, flags=re.S)
 old=old.replace('</head>','<link rel="stylesheet" href="/assets/css/article-search.css"></head>')
 old=old.replace('</body>','<script defer src="/assets/js/search-preferences.js"></script></body>')
 return old
if __name__=='__main__':
 args=argparse.ArgumentParser();args.add_argument('--apply',action='store_true');options=args.parse_args()
 home=restored_home()
 if not options.apply:print('Read-only recovery plan: restore older home layout + current search form; keep current articles, catalogue/index, Functions and D1. Use --apply only after current backup/review.');sys.exit(0)
 if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():raise SystemExit('Recovery requires clean latest main. No files changed.')
 if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).strip()!=b'main':raise SystemExit('Recovery requires latest main.')
 subprocess.run([sys.executable,'scripts/check_live_sync.py'],cwd=ROOT,check=True)
 (ROOT/'index.html').write_text(home,encoding='utf8')
 for command in [[sys.executable,'sync_new_articles.py'],[sys.executable,'scripts/build_search.py'],['node','tools/sync-knowledge-count.mjs'],[sys.executable,'scripts/release_guard.py','stamp'],[sys.executable,'scripts/release_guard.py','check-local'],[sys.executable,'scripts/predeploy_guard.py']]:subprocess.run(command,cwd=ROOT,check=True)
 print('Forward UI recovery candidate ready for review. No publish/push/database restore performed.')
