"""Complete the academy catalogs' photo heroes without duplicating existing ones."""
import re
from enshu_photo_layout import figure,CSS

def courses_index_hero(markup):
    if '<!-- courses-index-hero:start -->' in markup:return markup
    match=re.search(r'<header class="academy-section-heading">(.*?)</header>',markup,re.S)
    assert match,'Course index heading must exist'
    photo=figure('street','catalog-hero').replace('loading="lazy"','loading="eager" fetchpriority="high"',1)
    hero='<!-- courses-index-hero:start --><header class="academy-section-heading academy-catalog-hero"><div>'+match[1]+'</div>'+photo+'</header><p class="academy-catalog-photo-policy">写真は磐田の風景です。方言の採録現場や、各場面の会話が行われた場所を示すものではありません。</p><!-- courses-index-hero:end -->'
    markup=markup[:match.start()]+hero+markup[match.end():]
    return markup.replace('</head>','<!-- courses-index-hero:style --><link rel="stylesheet" href="'+CSS+'"><link rel="stylesheet" href="/assets/css/enshu-index-hero.css?v=20261115"><!-- /courses-index-hero:style --></head>',1)

def original_courses_index(markup):
    markup=re.sub(r'<!-- courses-index-hero:style -->.*?<!-- /courses-index-hero:style -->','',markup,flags=re.S)
    return re.sub(r'<!-- courses-index-hero:start --><header[^>]*><div>(.*?)</div><!-- iwata-photo:catalog-hero -->.*?<!-- courses-index-hero:end -->',lambda m:'<header class="academy-section-heading">'+m[1]+'</header>',markup,flags=re.S)
