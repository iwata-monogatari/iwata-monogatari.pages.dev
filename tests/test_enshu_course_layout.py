import unittest,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class CourseLayout(unittest.TestCase):
 def test_all_scene_material_and_navigation(self):
  d=json.loads((R/'data/enshu-learning.json').read_text(encoding='utf8'))
  for s in d['scenes']:
   slug='work-tools' if s['id']=='work' else s['id']
   t=(R/'enshu/courses'/slug/'index.html').read_text(encoding='utf8')
   self.assertEqual(t.count('class="conversation-card"'),2)
   self.assertEqual(t.count('class="lesson-word"'),len(s['words']))
   self.assertEqual(t.count('<figure class="iwata-photo '),2)
   self.assertEqual(t.count('class="course-reading-return"'),2)
   self.assertEqual(t.count('href="/enshu/courses/" aria-current="page"'),2)
   self.assertIn('href="/enshu/practice/'+slug+'/"',t)
   self.assertIn('写真は磐田の風景',t)
   self.assertIn('rel="license"',t)
if __name__=='__main__':unittest.main()
