"""遠州弁かるたの変換ツール（tools/build_c006_karuta.py）のテスト。

実行: python -m unittest tests/test_c006_karuta.py
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_c006_karuta', ROOT / 'tools/build_c006_karuta.py')
karuta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(karuta)


class KarutaPipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name) / 'originals'
        self.out = Path(self.tmp.name) / 'out'
        self.src.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def image(self, name, size, mode='RGB'):
        path = self.src / name
        Image.new(mode, size, (200, 120, 60, 128) if mode == 'RGBA' else (200, 120, 60)).save(path)
        return path

    def test_converts_to_both_sizes_with_exact_dimensions(self):
        written = karuta.convert(self.image('aisa.png', (1200, 1600)), self.out)
        self.assertEqual([p.name for p in written], ['aisa-300.webp', 'aisa-900.webp'])
        with Image.open(self.out / 'aisa-300.webp') as im:
            self.assertEqual(im.size, (300, 400))
        with Image.open(self.out / 'aisa-900.webp') as im:
            self.assertEqual(im.size, (900, 1200))
        self.assertEqual(karuta.check_outputs(self.out, ids={'aisa'}), [])

    def test_transparent_sources_are_flattened_onto_paper_color(self):
        karuta.convert(self.image('dara.png', (900, 1200), 'RGBA'), self.out)
        with Image.open(self.out / 'dara-300.webp') as im:
            self.assertEqual(im.mode, 'RGB')

    def test_rejects_small_or_wrong_ratio_sources(self):
        with self.assertRaisesRegex(ValueError, '小さすぎ'):
            karuta.convert(self.image('aisa.png', (600, 800)), self.out)
        with self.assertRaisesRegex(ValueError, '3:4'):
            karuta.convert(self.image('aisa.png', (1200, 1200)), self.out)
        self.assertFalse(self.out.exists() and any(self.out.iterdir()))

    def test_check_reports_unknown_ids_missing_pairs_and_wrong_sizes(self):
        self.out.mkdir()
        Image.new('RGB', (300, 400)).save(self.out / 'nosuch-300.webp', 'WEBP')
        Image.new('RGB', (300, 300)).save(self.out / 'aisa-300.webp', 'WEBP')
        problems = '\n'.join(karuta.check_outputs(self.out, ids={'aisa'}))
        self.assertIn('辞典にない語ID: nosuch-300.webp', problems)
        self.assertIn('aisa-300.webp: 300x300', problems)
        self.assertIn('対になるファイルがありません: aisa-900.webp', problems)

    def test_refuses_source_folder_inside_repository(self):
        with self.assertRaises(SystemExit):
            karuta.main(['--src', str(ROOT / 'assets')])

    def test_word_ids_come_from_the_dictionary(self):
        ids = karuta.word_ids()
        self.assertIn('aisa', ids)
        self.assertIn('hon-ya', ids)
        self.assertGreaterEqual(len(ids), 122)


if __name__ == '__main__':
    unittest.main()
