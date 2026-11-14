import unittest,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from enshu_research_topics import TOPICS
class ResearchTopicLayout(unittest.TestCase):
 def test_all_categories_photographs_and_navigation(self):
  self.assertEqual(len(TOPICS),14)
  cards=[]
  for key in TOPICS:
   text=(R/'enshu/research/topics'/key/'index.html').read_text(encoding='utf8')
   self.assertEqual(text.count('<figure class="iwata-photo '),2,key)
   self.assertEqual(text.count('class="research-topic-return"'),2)
   self.assertEqual(text.count('href="/enshu/research/" aria-current="page"'),2)
   self.assertIn('href="/enshu/research/#notebooks"',text)
   for section in ['coverage','lab','sources']:self.assertIn('/enshu/research/#'+section,text)
   self.assertIn('rel="license"',text)
   cards+=re.findall(r'<a href="(/enshu/research/[^"#]+/)"><div class="research-card-top">',text)
  self.assertEqual(len(cards),124)
  self.assertEqual(len(set(cards)),124)
if __name__=='__main__':unittest.main()
