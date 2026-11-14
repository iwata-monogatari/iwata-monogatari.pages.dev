import unittest,sys,re,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from enshu_dictionary_layout import apply_dictionary_layout
class DictionaryLayout(unittest.TestCase):
 def test_idempotence_and_existing_controls(self):
  t=(R/'c006.html').read_text(encoding='utf8')
  self.assertEqual(t,apply_dictionary_layout(t))
  self.assertEqual(t.count('<figure class="iwata-photo '),2)
  self.assertEqual(t.count('href="/c006" aria-current="page"'),2)
  self.assertEqual(len(re.findall(r'<div class="entry" id="w-',t)),134)
  for id_ in ['search','dict','filters','rows','karuta-view','random','reset','count']:
   self.assertEqual(t.count('id="'+id_+'"'),1,id_)
  self.assertIn('rel="license"',t)
if __name__=='__main__':unittest.main()
