import unittest,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class SceneQuizPages(unittest.TestCase):
 def test_scene_scope_and_controls(self):
  scenes=json.loads((R/'data/enshu-learning.json').read_text(encoding='utf8'))['scenes']
  index=(R/'enshu/practice/index.html').read_text(encoding='utf8')
  self.assertEqual(index.count('class="quiz-scene-card"'),12)
  for s in scenes:
   path='/enshu/practice/'+('work-tools' if s['id']=='work' else s['id'])+'/'
   self.assertIn('href="'+path+'"',index)
   t=(R/path.lstrip('/')/'index.html').read_text(encoding='utf8')
   config=json.loads(re.search(r'id="quiz-page-config">(.*?)</script>',t,re.S)[1])
   self.assertEqual(config['scene'],s['id'])
   self.assertEqual(len(config['paths']),12)
   self.assertIn('<option value="'+s['id']+'" selected>',t)
   for control in ['quiz-length','quiz-direction','quiz-category','quiz-source','quiz-start','quiz-hint-button','quiz-summary','quiz-feedback']:
    self.assertEqual(t.count('id="'+control+'"'),1,control)
   self.assertEqual(t.count('id="quiz-course-return"'),1)
   self.assertIn('href="/enshu/practice/#quiz-scenes"',t)
   self.assertIn('class="iwata-photo ',t)
   self.assertNotIn('name="iwata:published"',t)
   self.assertIn('href="https://iwata-monogatari.net'+path+'"',t)
if __name__=='__main__':unittest.main()
