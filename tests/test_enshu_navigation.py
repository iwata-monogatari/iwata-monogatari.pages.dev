"""Regression checks for splitting existing lessons without dropping material."""
import html
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class AcademyPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.learning=json.loads((ROOT/'data/enshu-learning.json').read_text(encoding='utf-8'))
        cls.words={entry['id']:entry for entry in cls.learning['entries']}

    def test_all_scene_words_and_conversations_remain(self):
        seen=set();conversations=0
        for scene in self.learning['scenes']:
            sid=scene['id'];slug='work-tools' if sid=='work' else sid
            text=(ROOT/f'enshu/courses/{slug}/index.html').read_text(encoding='utf-8')
            self.assertIn(f'href="https://iwata-monogatari.net/enshu/courses/{slug}/"',text)
            for wid in scene['words']:
                self.assertIn(f'id="learn-{sid}-{wid}"',text)
                self.assertIn(html.escape(self.words[wid]['m'],quote=True),text)
                seen.add(wid)
            for conversation in scene['conversations']:
                self.assertIn(f'id="conversation-{conversation["id"]}"',text)
                for turn in conversation['turns']:
                    self.assertIn(html.escape(turn['dialect'],quote=True),text)
                    self.assertIn(html.escape(turn['standard'],quote=True),text)
                conversations+=1
            self.assertIn(f'/enshu/practice/?scene={sid}&amp;start=1',text)
            self.assertNotIn('href="#practice"',text)
        # Preserve the original course memberships; not every dictionary word
        # was assigned to a course. All 182 remain in the explorer/quiz data.
        self.assertEqual({wid for scene in self.learning['scenes'] for wid in scene['words']},seen)
        self.assertEqual(24,conversations)

    def test_entrance_opens_seven_different_pages(self):
        text=(ROOT/'enshu/index.html').read_text(encoding='utf-8')
        hero=re.search(r'<header class="academy-hero">(.*?)</header>',text,re.S)[1]
        self.assertNotIn('<nav>',hero)
        self.assertNotIn('class="academy-paths"',text)
        choices=re.search(r'<section class="academy-destinations">(.*?)</section>',text,re.S)[1]
        urls=re.findall(r'<a href="([^"]+)"',choices)
        self.assertEqual(['/enshu/courses/','/enshu/practice/','/enshu/words/','/enshu/seminar/','/enshu/research/','/c006','/c008'],urls)
        for widget in ('quiz-start','flash-next','course-lessons'):
            self.assertNotIn('id="'+widget+'"',text)
        self.assertEqual(1,text.count('class="academy-destinations"'))

    def test_activity_pages_have_home_and_self_canonicals(self):
        for section in ('courses','practice','words'):
            text=(ROOT/f'enshu/{section}/index.html').read_text(encoding='utf-8')
            self.assertIn(f'rel="canonical" href="https://iwata-monogatari.net/enshu/{section}/"',text)
            self.assertIn('href="/enshu/">← 学び舎の入口へ',text)
            # A split activity is not a newly dated knowledge article.
            self.assertNotIn('name="iwata:published"',text)
            ids=re.findall(r'\bid="([^"]+)"',text)
            self.assertEqual(len(ids),len(set(ids)))

if __name__=='__main__':unittest.main()
