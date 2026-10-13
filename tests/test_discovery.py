"""Check discovery policy without reducing the readable article corpus."""
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class HeadAndLinks(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.robots = []
        self.canonical = []
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name') == 'robots':
            self.robots.append(attrs.get('content', ''))
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs['href'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))


class DiscoveryTests(unittest.TestCase):
    def test_catalog_is_noindex_but_all_articles_and_pagination_remain(self):
        manifest = json.loads((ROOT / 'data/search/manifest.json').read_text(encoding='utf-8'))
        metadata = json.loads((ROOT / manifest['metadata'].lstrip('/')).read_text(encoding='utf-8'))
        records = metadata['records']
        expected = {r['url'] for r in records}
        actual = []
        pages = sorted((ROOT / 'search/catalog').glob('*/index.html'), key=lambda p: int(p.parent.name))
        self.assertEqual(len(pages), (len(records) + 19) // 20)
        for index, page in enumerate(pages, 1):
            text = page.read_text(encoding='utf-8')
            head = HeadAndLinks(text)
            self.assertEqual(head.robots, ['noindex,follow'], str(page))
            self.assertEqual(head.canonical, [f'https://iwata-monogatari.net/search/catalog/{index}/'])
            listing = text.split('<ol class="search-list">', 1)[1].split('</ol>', 1)[0]
            rows = HeadAndLinks(listing).links
            self.assertTrue(all(url in expected for url in rows))
            self.assertEqual(len(rows), min(20, len(records) - (index - 1) * 20))
            actual.extend(rows)
            if index > 1:
                self.assertIn(f'/search/catalog/{index - 1}/', head.links)
            if index < len(pages):
                self.assertIn(f'/search/catalog/{index + 1}/', head.links)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(set(actual), expected)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [e.text for e in ET.parse(ROOT / 'sitemap.xml').findall('s:url/s:loc', ns)]
        self.assertFalse(any('/search/catalog/' in url for url in urls))
        for url in ['/c096', '/n007', '/s006', '/oishi-ronko/', '/oishi-ronko/020/']:
            self.assertIn('https://iwata-monogatari.net' + url, urls)
        self.assertFalse(HeadAndLinks((ROOT / 'c034.html').read_text(encoding='utf-8')).robots)

    def test_updated_blog_keeps_publication_date_and_order(self):
        blog = module('build_blog')
        posts = [
            {'slug': '20260801-old', 'date': '2026-08-01', 'updated_at': '2026-10-14', 'title': 'old & revised', 'description': 'details'},
            {'slug': '20261013-new', 'date': '2026-10-13', 'title': 'new', 'description': 'details'},
        ]
        ns = {'a': 'http://www.w3.org/2005/Atom'}
        feed = ET.fromstring(blog.build_feed(posts))
        self.assertEqual(feed.find('a:updated', ns).text, '2026-10-14T00:00:00+09:00')
        entries = feed.findall('a:entry', ns)
        self.assertTrue(entries[0].find('a:id', ns).text.endswith('/20261013-new/'))
        old = entries[1]
        self.assertEqual(old.find('a:published', ns).text, '2026-08-01T00:00:00+09:00')
        self.assertEqual(old.find('a:updated', ns).text, '2026-10-14T00:00:00+09:00')
        self.assertEqual(old.find('a:title', ns).text, 'old & revised')
        block = blog.build_sitemap_block(posts)
        root = ET.fromstring('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + block + '</urlset>')
        sns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        dates = {e.find('s:loc', sns).text: e.find('s:lastmod', sns).text for e in root.findall('s:url', sns)}
        self.assertEqual(dates[blog.SITE + '/blog/20260801-old/'], '2026-10-14')
        self.assertEqual(dates[blog.SITE + '/blog/20261013-new/'], '2026-10-13')
        self.assertEqual(dates[blog.SITE + '/blog/'], '2026-10-14')


if __name__ == '__main__':
    unittest.main()
