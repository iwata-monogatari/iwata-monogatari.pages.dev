from pathlib import Path
import re
import json

import build_iwata_second_volume as renderer
from iwata_fourth_volume_data import ARTICLES


ROOT = Path(__file__).resolve().parents[1]
renderer.DATE = "2026-08-26"
renderer.BOOK = "『磐田ことはじめ（第二編・現代編）』"
ALTS = {
    "c165": "家庭、学校の検診、衛生組合、町村施設が支えた磐田の公衆衛生",
    "c166": "生産から割当、配給所、家庭へ届くまでの条件を示した配給の構造",
    "c167": "場所、材料、仲間、季節が重なって成立する子どもの遊び",
}


def main() -> None:
    for article in ARTICLES:
        rendered = renderer.article_html(article)
        rendered = rendered.replace('<link rel="stylesheet" href="/assets/css/temple-shrine-ref.css" data-ts-ref-css>\n', '')
        # 小見出しを独立ブロックにせず、次の段落の導入文へ統合する。
        rendered = re.sub(
            r'<p class="subheading"><strong>(.*?)</strong></p>\s*<p>',
            r'<p><strong>\1。</strong> ', rendered,
        )
        guide = (
            f'<figure class="evidence-visual article-guide"><img src="/assets/img/article-guides/{article["slug"]}.svg" '
            f'alt="{ALTS[article["slug"]]}" style="display:block;width:100%;height:auto">'
            '<figcaption>記事固有の論点図。本文で扱う関係を、史料の読み順に沿って整理した。</figcaption></figure>\n'
        )
        rendered = rendered.replace('<figure class="evidence-visual"><svg', guide + '<figure class="evidence-visual"><svg', 1)
        structured = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Article", "@id": f"https://iwata-monogatari.net/{article['slug']}#article",
                    "headline": article["title"], "description": article["description"],
                    "datePublished": "2026-08-26", "dateModified": "2026-08-26",
                    "mainEntityOfPage": f"https://iwata-monogatari.net/{article['slug']}",
                    "image": f"https://iwata-monogatari.net/assets/img/article-guides/{article['slug']}.svg",
                    "publisher": {"@type": "Organization", "name": "磐田物語", "url": "https://iwata-monogatari.net/"},
                },
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "磐田物語", "item": "https://iwata-monogatari.net/"},
                        {"@type": "ListItem", "position": 2, "name": article["short_title"], "item": f"https://iwata-monogatari.net/{article['slug']}"},
                    ],
                },
            ],
        }
        rendered = rendered.replace('</head>', '<!-- structured-data:auto -->\n<script type="application/ld+json">' + json.dumps(structured, ensure_ascii=False) + '</script>\n</head>', 1)
        rendered = rendered.replace("2026年8月24日</time> 初版公開", "2026年8月26日</time> 初版公開")
        (ROOT / f"{article['slug']}.html").write_text(rendered, encoding="utf-8", newline="\n")
    print(f"generated {len(ARTICLES)} fourth-volume articles")


if __name__ == "__main__":
    main()
