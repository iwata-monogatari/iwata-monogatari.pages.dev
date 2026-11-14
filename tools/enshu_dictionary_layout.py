"""Add attributed scenery around the unchanged dictionary and its controls."""
import re
from enshu_navigation import navigation
from enshu_photo_layout import figure,credits,CSS as PHOTO_CSS

def original_dictionary_layout(text):
 text=re.sub(r'<!-- dictionary-layout:(style|footer) -->.*?<!-- /dictionary-layout:\1 -->','',text,flags=re.S)
 text=re.sub(r'<section class="hero dictionary-photo-hero"><div class="dictionary-hero-copy">(.*?)</div>.*?</section>',lambda m:'<section class="hero">'+m[1]+'</section>',text,count=1,flags=re.S)
 return text

def apply_dictionary_layout(text):
 text=original_dictionary_layout(text)
 style='<!-- dictionary-layout:style --><link rel="stylesheet" href="'+PHOTO_CSS+'"><link rel="stylesheet" href="/assets/css/enshu-dictionary-layout.css?v=20261114"><!-- /dictionary-layout:style -->'
 text=text.replace('</head>',style+'</head>',1)
 hero=re.search(r'<section class="hero">(.*?)</section>',text,re.S)
 assert hero,'Dictionary introduction missing'
 replacement='<section class="hero dictionary-photo-hero"><div class="dictionary-hero-copy">'+hero[1]+'</div>'+figure('street','dictionary-lead')+'</section>'
 text=text[:hero.start()]+replacement+text[hero.end():]
 footer='<!-- dictionary-layout:footer --><section class="dictionary-landscape" aria-label="磐田の風景と学び舎への案内">'+figure('merchant','middle')+'<p class="dictionary-photo-policy">写真は磐田の風景です。各語の使用地点や方言の採録現場を示すものではありません。</p>'+credits(['street','merchant'])+'<div class="academy-middle-header">'+navigation('/c006')+'</div></section><!-- /dictionary-layout:footer -->'
 landmarks=list(re.finditer(r'<div class="note">(?=\s*<section class="revision-history)',text))
 assert len(landmarks)==1,'Dictionary revision landmark must be unique'
 at=landmarks[0].start();text=text[:at]+footer+text[at:]
 return text
