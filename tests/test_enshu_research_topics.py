import json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from enshu_research_topics import TOPICS
from enshu_navigation import LINKS

class ResearchTopicsTest(unittest.TestCase):
 def test_category_membership_and_navigation(self):
  index=(ROOT/'enshu/research/index.html').read_text(encoding='utf8')
  self.assertNotIn('class="research-note-group"',index)
  self.assertIn('class="academy-middle-header"',index)
  cards=[]
  for key in TOPICS:
   path='/enshu/research/topics/'+key+'/'
   match=re.search(r'<a href="'+re.escape(path)+r'">(.*?)</a>',index,re.S)
   self.assertIsNotNone(match)
   count=int(re.search(r'(\d+)本',match[1])[1])
   page=(ROOT/path.lstrip('/')/'index.html').read_text(encoding='utf8')
   links=re.findall(r'<a href="(/enshu/research/[^"#]+/)"><div class="research-card-top">',page)
   self.assertEqual(count,len(links),key);cards+=links
   self.assertIn('rel="canonical" href="https://iwata-monogatari.net'+path+'"',page)
   self.assertIn('href="/enshu/research/#notebooks"',page)
   self.assertIn('href="/enshu/"',page)
   self.assertNotIn('name="iwata:published"',page)
   self.assertEqual(page.count('<h1>'),1)
   ids=re.findall(r'\bid="([^"]+)"',page)
   self.assertEqual(len(ids),len(set(ids)),key)
  notes=json.loads((ROOT/'data/enshu-research-index.json').read_text(encoding='utf8'))['notes']
  self.assertEqual(set(cards),{'/enshu/research/'+n['slug']+'/' for n in notes})
  self.assertEqual(len(cards),len(notes))

 def test_bottom_resources_remain_on_index(self):
  index=(ROOT/'enshu/research/index.html').read_text(encoding='utf8')
  for key in ('coverage','lab','sources'):
   match=re.search(r'<section\b[^>]*\bid="'+key+'"',index)
   self.assertIsNotNone(match,key)
   self.assertGreater(match.start(),index.index('aria-label="研究テーマを選ぶ"'))
   self.assertIn('href="#'+key+'"',index)
  self.assertIn('id="research-records"',index)

 def test_each_note_returns_to_its_actual_category(self):
  count=0
  for key in TOPICS:
   category=(ROOT/'enshu/research/topics'/key/'index.html').read_text(encoding='utf8')
   paths=re.findall(r'<a href="(/enshu/research/[^"#]+/)"><div class="research-card-top">',category)
   for path in paths:
    page=(ROOT/path.lstrip('/')/'index.html').read_text(encoding='utf8')
    self.assertEqual(page.count('class="academy-middle-header"'),1,path)
    block=re.search(r'<!-- academy-middle:start -->(.*?)<!-- academy-middle:end -->',page,re.S)[1]
    self.assertEqual(block.count('<a '),len(LINKS)+1,path)
    back=re.search(r'<nav class="research-nav research-category-return".*?</nav>',page,re.S)[0]
    self.assertIn('href="/enshu/research/topics/'+key+'/"',back,path)
    self.assertLess(page.index('academy-middle:start'),page.index('research-note-head'))
    self.assertLess(page.index('research-category-return'),page.index('research-note-head'))
    count+=1
  self.assertEqual(count,len(json.loads((ROOT/'data/enshu-research-index.json').read_text(encoding='utf8'))['notes']))

if __name__=='__main__':unittest.main()
