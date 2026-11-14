import importlib.util
from pathlib import Path
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))

class SeminarPagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('seminar_build',ROOT/'tools/build_enshu_seminar.py')
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)

    def test_each_complete_lesson_and_sources(self):
        for lesson in self.module.lessons:
            page=(ROOT/'enshu/seminar'/lesson['id']/'index.html').read_text(encoding='utf8')
            self.assertIn(lesson['body'],page)
            self.assertIn(lesson['question'],page)
            self.assertIn(lesson['answer'],page)
            self.assertEqual(len(re.findall('<h1>',page)),1)
            self.assertEqual(len(re.findall('<article class="seminar-lesson"',page)),1)
            self.assertNotIn('name="iwata:published"',page)
            self.assertIn('href="/enshu/seminar/"',page)
            self.assertIn('href="/enshu/"',page)
            for sid,*_ in self.module.sources:self.assertIn('id="source-'+sid+'"',page)
            ids=re.findall(r'\bid="([^"]+)"',page)
            self.assertEqual(len(ids),len(set(ids)))

    def test_index_and_top_navigation(self):
        page=(ROOT/'enshu/seminar/index.html').read_text(encoding='utf8')
        self.assertNotIn('<article class="seminar-lesson"',page)
        self.assertIn('academy-paths',page.split('seminar-hero')[0])
        for lesson in self.module.lessons:
            self.assertIn('href="/enshu/seminar/'+lesson['id']+'/"',page)
            self.assertNotIn('/enshu/seminar/#lesson-'+lesson['id'],page)

if __name__=='__main__':unittest.main()
