import unittest,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class ComparisonPages(unittest.TestCase):
 def test_complete_theme_partition(self):
  groups=json.loads((R/'data/enshu-comparisons.json').read_text(encoding='utf8'))
  corpus=json.loads((R/'data/enshu-gunshi-corpus.json').read_text(encoding='utf8'))['records']
  index=(R/'enshu/compare/index.html').read_text(encoding='utf8')
  self.assertEqual(len(groups),24)
  self.assertNotIn('class="compare-section"',index)
  for g in groups:
   path='/enshu/compare/'+('household-tools' if g['id']=='tools' else g['id'])+'/'
   self.assertIn('href="'+path+'"',index)
   text=(R/path.lstrip('/')/'index.html').read_text(encoding='utf8')
   self.assertEqual(re.findall(r'<section class="compare-section" id="([^"]+)"',text),['compare-'+g['id']])
   self.assertIn(g['intro'],text)
   table=re.search(r'<tbody>(.*?)</tbody>',text,re.S)[1]
   rows=[r for w in g['words'] for r in corpus if r['form']==w]
   self.assertEqual(table.count('<tr>'),len(rows))
   for r in rows:
    self.assertIn('/enshu/records/#'+r['id'],table)
    self.assertIn('https://dl.ndl.go.jp/pid/965680/1/'+str(r['frame']),table)
   self.assertGreaterEqual(text.count('<figure class="iwata-photo '),2)
   self.assertIn('href="/enshu/compare/#themes"',text)
   self.assertIn('href="/enshu/"',text)
   self.assertNotIn('name="iwata:published"',text)
   self.assertIn('href="https://iwata-monogatari.net'+path+'"',text)
if __name__=='__main__':unittest.main()
