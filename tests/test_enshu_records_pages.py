from pathlib import Path
import json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from enshu_records_pages import page_url

class RecordsPagesTest(unittest.TestCase):
 def test_each_record_on_exact_original_page(self):
  records=json.loads((ROOT/'data/enshu-gunshi-corpus.json').read_text(encoding='utf8'))['records']
  seen=[]
  for page in range(1242,1255):
   text=(ROOT/page_url(page).lstrip('/')/'index.html').read_text(encoding='utf8')
   ids=re.findall(r'<article class="record" id="([^"]+)"',text)
   self.assertEqual(ids,[r['id'] for r in records if r['page']==page])
   self.assertEqual(len(re.findall(r'<section class="source-chapter"',text)),1)
   self.assertIn('id="page-'+str(page)+'"',text)
   self.assertIn('href="/enshu/records/search/"',text)
   self.assertIn('href="/enshu/"',text)
   self.assertGreaterEqual(len(re.findall(r'<img[^>]+data-iwata-photo=',text)),2)
   self.assertIn('写真は磐田の風景で、方言の採録現場を示すものではありません。',text)
   self.assertIn('rel="license"',text)
   if page!=1242:self.assertNotIn('name="iwata:published"',text)
   seen+=ids
  self.assertEqual(len(seen),380);self.assertEqual(len(set(seen)),380)

 def test_search_and_legacy_mapping(self):
  text=(ROOT/'enshu/records/search/index.html').read_text(encoding='utf8')
  self.assertEqual(len(re.findall(r'<article class="record"',text)),380)
  self.assertIn('enshu-corpus.js',text)
  self.assertNotIn('/enshu/records/1/',text)
  root=(ROOT/'enshu/records/index.html').read_text(encoding='utf8')
  self.assertEqual(len(re.findall(r'<article class="record"',root)),12)
  mapping=json.loads(re.search(r'<script type="application/json" id="records-page-map">(.*?)</script>',root,re.S)[1])
  self.assertEqual(len(mapping),380)
  for page in range(1243,1255):self.assertIn('href="'+page_url(page)+'"',root)

if __name__=='__main__':unittest.main()
