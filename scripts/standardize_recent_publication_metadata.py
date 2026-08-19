from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATES = {"2026-08-17", "2026-08-18", "2026-08-19"}
TODAY = "2026-08-19"
BASE = "https://iwata-monogatari.net/"


def main() -> None:
    ledger_path = ROOT / "data/pages.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    changed = 0
    for page in ledger["pages"]:
        if page.get("published_at") not in DATES and page.get("updated_at") not in DATES:
            continue
        rel = str(page.get("url", "")).lstrip("/")
        path = ROOT / rel
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        if "article-guide" not in raw:
            continue
        expected = BASE + rel
        original = raw
        raw = re.sub(
            r'(<link\b[^>]*rel="canonical"[^>]*href=")[^"]+("[^>]*>)',
            rf"\g<1>{expected}\g<2>",
            raw,
            count=1,
            flags=re.I,
        )
        if re.search(r'<meta\b[^>]*property="og:url"', raw, re.I):
            raw = re.sub(
                r'(<meta\b[^>]*property="og:url"[^>]*content=")[^"]+("[^>]*>)',
                rf"\g<1>{expected}\g<2>",
                raw,
                count=1,
                flags=re.I,
            )
        else:
            canonical = re.search(r'<link\b[^>]*rel="canonical"[^>]*>', raw, re.I)
            if canonical:
                raw = raw[:canonical.end()] + f'<meta property="og:url" content="{expected}">' + raw[canonical.end():]
        stem_url = BASE + Path(rel).stem
        raw = raw.replace(f'"{stem_url}"', f'"{expected}"')
        raw = re.sub(r'("dateModified"\s*:\s*")\d{4}-\d{2}-\d{2}(")', rf"\g<1>{TODAY}\g<2>", raw, count=1)
        if raw != original:
            path.write_text(raw, encoding="utf-8")
            changed += 1
        page["updated_at"] = TODAY
    ledger["updated_at"] = TODAY
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"standardized metadata for {changed} recent illustrated pages")


if __name__ == "__main__":
    main()
