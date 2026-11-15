"""Add a credited real Iwata photograph to the academy entrance only."""
import re
from enshu_photo_layout import figure

def original_home_hero(text):
 text=re.sub(r'<!-- academy-home-hero:style -->.*?<!-- /academy-home-hero:style -->','',text,flags=re.S)
 text=re.sub(r'<div class="academy-home-hero-grid"><div class="academy-home-hero-copy">(.*?)</div><!-- academy-home-hero:photo -->.*?<!-- /academy-home-hero:photo --></div>',lambda m:m[1],text,flags=re.S)
 return text

def apply_home_hero(text):
 text=original_home_hero(text)
 style='<!-- academy-home-hero:style --><link rel="stylesheet" href="/assets/css/enshu-photos.css?v=20261113"><link rel="stylesheet" href="/assets/css/enshu-home-hero.css?v=20261115"><!-- /academy-home-hero:style -->'
 text=text.replace('</head>',style+'</head>',1)
 hero=re.search(r'<header class="academy-hero">(.*?)</header>',text,re.S);assert hero
 metric=re.search(r'<div class="metrics">.*?</div>',hero[1],re.S);assert metric and hero[1].endswith(metric[0])
 photo=figure('school','home-hero').replace('loading="lazy"','loading="eager" fetchpriority="high"',1)
 photo=re.sub(r'sizes="[^"]+"','sizes="(max-width:700px) calc(100vw - 36px), (max-width:1100px) 46vw, 510px"',photo,count=1)
 body='<div class="academy-home-hero-grid"><div class="academy-home-hero-copy">'+hero[1][:metric.start()]+'</div><!-- academy-home-hero:photo -->'+photo+'<!-- /academy-home-hero:photo --></div>'+metric[0]
 return text[:hero.start()]+'<header class="academy-hero">'+body+'</header>'+text[hero.end():]
