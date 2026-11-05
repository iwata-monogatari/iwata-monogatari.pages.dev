import contextlib
import importlib.util
import io
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('guard', ROOT / 'scripts/predeploy_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class RecentArticleCanonicalTest(unittest.TestCase):
    def test_extensionless_new_article_matches_html_ledger(self):
        self.assertEqual(guard.verify_latest_sync(
            guard.load_json('data/pages.json')['pages'],
            guard.load_json('data/new-articles.json'),
            guard.read_text('index.html'), guard.read_text('updates.html')), 0)

    def test_missing_recent_article_is_still_rejected(self):
        latest = [p for p in guard.load_json('data/new-articles.json') if not guard.equivalent_url(p['url'], '/c181')]
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            result = guard.verify_latest_sync(guard.load_json('data/pages.json')['pages'], latest,
                guard.read_text('index.html'), guard.read_text('updates.html'))
        self.assertEqual(result, 1)
        self.assertIn('missing from data/new-articles.json: /c181.html', errors.getvalue())

if __name__ == '__main__': unittest.main()
