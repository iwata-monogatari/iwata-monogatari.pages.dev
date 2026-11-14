"""Add landscape photographs and consistent returns without rewriting lessons."""
import re
from enshu_navigation import navigation
from enshu_photo_layout import figure,credits,CSS as PHOTO_CSS
from enshu_records_pages import PHOTO_KEYS

def course_layout(markup,scene,number):
 a=PHOTO_KEYS[number%len(PHOTO_KEYS)];b=PHOTO_KEYS[(number+5)%len(PHOTO_KEYS)]
 markup=markup.replace('</head>','<link rel="stylesheet" href="'+PHOTO_CSS+'"><link rel="stylesheet" href="/assets/css/enshu-course-layout.css?v=20261114"></head>',1)
 markup=markup.replace('<main class="academy">','<main class="academy course-reading">',1)
 markup=re.sub(r'<nav class="academy-paths".*?</nav>',lambda _:navigation('/enshu/courses/'),markup,flags=re.S)
 header=re.search(r'<header class="academy-section-heading">(.*?)</header>',markup,re.S)
 assert header
 hero='<header class="academy-section-heading course-reading-hero"><div>'+header[1]+'</div>'+figure(a)+'</header>'
 markup=markup[:header.start()]+hero+markup[header.end():]
 path='/enshu/practice/'+('work-tools' if scene['id']=='work' else scene['id'])+'/'
 back='<nav class="course-reading-return" aria-label="場面の読み進め方"><a href="/enshu/courses/">← 12場面の一覧へ戻る</a><a href="'+path+'">この場面のクイズへ</a><a href="/enshu/words/">一語ずつ探す</a></nav>'
 markup=markup.replace('</header><section id="scene-', '</header>'+back+'<p class="course-photo-policy">写真は磐田の風景で、方言の採録現場や、本文の会話が行われた場所を示すものではありません。</p><section id="scene-',1)
 marker='<h3 class="lesson-group-title">'
 assert marker in markup
 markup=markup.replace(marker,figure(b,'middle')+marker,1)
 markup=markup.replace('class="course-return" href="/enshu/courses/">場面一覧に戻る →','class="course-return" href="/enshu/courses/">← 12場面の一覧へ戻る')
 markup=markup.replace('<section class="notice">',back+'<section class="notice">',1)
 markup=markup.replace('</main>',credits([a,b])+'</main>',1)
 assert markup.count('class="course-reading-return"')==2
 return markup
