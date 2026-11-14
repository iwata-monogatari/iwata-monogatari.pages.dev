import unittest,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class SeminarLayout(unittest.TestCase):
 def test_all_lessons_photos_and_returns(self):
  for id_ in ['evidence','geography','modality','grammar','sound','meaning','folklore','change']:
   t=(R/'enshu/seminar'/id_/'index.html').read_text(encoding='utf8')
   self.assertEqual(t.count('<figure class="iwata-photo '),2,id_)
   self.assertEqual(len(set(re.findall(r'data-iwata-photo="([^"]+)"',t))),2)
   self.assertEqual(t.count('class="seminar-reading-return"'),2)
   self.assertEqual(t.count('href="/enshu/seminar/" aria-current="page"'),2)
   self.assertEqual(t.count('<aside class="seminar-exercise">'),1)
   self.assertIn('資料に戻って答えを確かめる',t)
   self.assertIn('id="bibliography"',t)
   self.assertIn('id="glossary"',t)
   self.assertIn('rel="license"',t)
   self.assertNotIn('name="iwata:published"',t)
if __name__=='__main__':unittest.main()
