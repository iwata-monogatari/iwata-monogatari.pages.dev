"""Missing canonical pages must be added without rewriting existing sitemap data."""
import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_sitemap", ROOT / "scripts/build_sitemap.py")
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
BASE = sm.BASE


class SitemapTests(unittest.TestCase):
    def test_five_pages_recover_from_missing_entries_and_preserve_every_old_byte(self):
        xml = (ROOT / "sitemap.xml").read_bytes().decode("utf-8")
        import re
        original = re.sub(r"[^\S\r\n]*<url><loc>https://iwata-monogatari.net/c17[2-6]</loc>.*?</url>\r?\n", "", xml)
        pages = [ROOT / f"c{i}.html" for i in range(172, 177)]
        dates = {p: "2026-10-12" for p in pages}
        updated, added = sm.append_missing(original, pages, dates)
        self.assertEqual(added, [f"{BASE}/c{i}" for i in range(172, 177)])
        recovered = re.sub(r"[^\S\r\n]*<url><loc>https://iwata-monogatari.net/c17[2-6]</loc>.*?</url>\r?\n", "", updated)
        self.assertEqual(recovered, original)
        urls = [e.text for e in ET.fromstring(updated).iter(NS + "loc")]
        for url in added:
            self.assertEqual(urls.count(url), 1)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(sm.append_missing(updated, pages, dates), (updated, []))

    def test_noindex_alias_external_or_missing_canonical_are_not_added(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bodies = {
                "valid": f'<link href="{BASE}/valid" rel="canonical">',
                "hidden": f'<meta content="noindex,follow" name="robots"><link rel="canonical" href="{BASE}/hidden">',
                "google": f'<meta content="NOINDEX" name="Googlebot"><link rel="canonical" href="{BASE}/google">',
                "alias": f'<link rel="canonical" href="{BASE}/valid">',
                "external": '<link rel="canonical" href="https://example.org/external">',
                "absent": '<title>No canonical</title>',
                "ambiguous": f'<link rel="canonical" href="{BASE}/ambiguous"><link rel="canonical" href="{BASE}/valid">',
            }
            pages = []
            for name, body in bodies.items():
                p = root / f"{name}.html"; p.write_text(body, encoding="utf-8"); pages.append(p)
            xml = f'<urlset xmlns="{NS[1:-1]}">\r\n<!-- blog:start -->\r\n<!-- blog:end -->\r\n</urlset>\r\n'
            with patch.object(sm, "ROOT", root):
                updated, added = sm.append_missing(xml, pages, {p: "2026-10-12" for p in pages})
            self.assertEqual(added, [BASE + "/valid"])
            self.assertIn("<!-- blog:start -->\r\n<!-- blog:end -->\r\n", updated)
            self.assertNotIn("\n", updated.replace("\r\n", ""))

    def test_invalid_xml_and_duplicate_urls_fail_closed(self):
        for xml in ['<urlset>', f'<urlset xmlns="{NS[1:-1]}"><url><loc>{BASE}/a</loc></url><url><loc>{BASE}/a</loc></url></urlset>']:
            with self.assertRaises((ValueError, ET.ParseError)):
                sm.append_missing(xml, [], {})

    def test_managed_and_private_directories_are_not_scanned(self):
        self.assertTrue({"blog", "archive", "partials", "tests", "tools", "work", "docs", "functions"} <= sm.EXCLUDE_DIRS)
        self.assertTrue({"admin-bbs.html", "admin-reactions.html", "404.html"} <= sm.EXCLUDE_FILES)


if __name__ == "__main__":
    unittest.main()
