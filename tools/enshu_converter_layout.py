"""Place credited Iwata scenery around the unchanged conversion tool."""
import re
from enshu_navigation import navigation
from enshu_photo_layout import figure,credits,CSS as PHOTO_CSS

def original_converter_layout(text):
 text=re.sub(r'<!-- converter-layout:(style|footer) -->.*?<!-- /converter-layout:\1 -->','',text,flags=re.S)
 text=re.sub(r'<section class="hero converter-photo-hero"><div class="converter-hero-copy">(.*?)</div>.*?</section>',lambda m:'<section class="hero">'+m[1]+'</section>',text,count=1,flags=re.S)
 return text

def apply_converter_layout(text):
 text=original_converter_layout(text)
 text=text.replace('</head>','<!-- converter-layout:style --><link rel="stylesheet" href="'+PHOTO_CSS+'"><link rel="stylesheet" href="/assets/css/enshu-converter-layout.css?v=20261114"><!-- /converter-layout:style --></head>',1)
 hero=re.search(r'<section class="hero">(.*?)</section>',text,re.S)
 assert hero,'Converter introduction missing'
 text=text[:hero.start()]+'<section class="hero converter-photo-hero"><div class="converter-hero-copy">'+hero[1]+'</div>'+figure('school','converter-lead')+'</section>'+text[hero.end():]
 assert text.count('</main>')==1,'Converter main must be unique'
 footer='<!-- converter-layout:footer --><section class="converter-landscape" aria-label="磐田の風景と学び舎への案内">'+figure('post','converter-bottom')+'<p class="converter-photo-policy">写真は磐田の風景です。変換例の会話の場所や、方言の採録現場を示すものではありません。</p>'+credits(['school','post'])+'<div class="academy-middle-header">'+navigation('/c008')+'</div></section><!-- /converter-layout:footer -->'
 return text.replace('</main>',footer+'</main>',1)
