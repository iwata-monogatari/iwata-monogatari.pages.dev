import unittest,json,re,html
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class WordPages(unittest.TestCase):
 def test_all_words_examples_and_sources(self):
  d=json.loads((R/'data/enshu-learning.json').read_text(encoding='utf8'))
  index=(R/'enshu/words/index.html').read_text(encoding='utf8')
  self.assertEqual(index.count('class="word-catalog-item"'),len(d['entries']))
  for e in d['entries']:
   path='/enshu/words/'+e['id']+'/'
   self.assertIn('href="'+path+'"',index)
   text=(R/path.lstrip('/')/'index.html').read_text(encoding='utf8')
   self.assertIn('href="https://iwata-monogatari.net'+path+'"',text)
   self.assertIn('class="word-reading" data-word-id="'+e['id']+'"',text)
   for value in [e['w'],e['m'],e['learning']['point'],e['ex'],e['std']]+[x[k] for x in e['learning']['examples'] for k in ['dialect','standard']]:self.assertIn(html.escape(value,quote=True),text,e['id'])
   self.assertEqual(text.count('class="word-page-pair"'),3)
   self.assertIn('href="/enshu/words/#word-list"',text)
   self.assertIn('class="iwata-photo ',text)
   for source in e.get('sources',[]):
    if source.get('url'):self.assertIn(html.escape(source['url'],quote=True),text,e['id'])
   if e.get('n'):self.assertIn(html.escape(e['n'],quote=True),text)
   if e.get('historical'):self.assertIn(html.escape(e['historical']['note'],quote=True),text)
   self.assertNotIn('name="iwata:published"',text)
   self.assertNotIn('src="/assets/js/enshu-academy.js',text)
if __name__=='__main__':unittest.main()
