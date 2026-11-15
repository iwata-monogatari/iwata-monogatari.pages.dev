"""Mark existing explanatory sections without changing their text or references."""
import re

TARGETS={
 'grammar':['grammar-landscape','grammar-endings','grammar-forms','grammar-particles','grammar-iwata-accent','grammar-yaramaika'],
 'more':['more-introduction','dialect-region','dialect-boundaries','dialect-theories','dialect-sounds','negative-possibility','yaramaika-readings','dialect-literature','word-origins','dialect-inheritance','dictionary-help','dialect-research-history','dialect-glossary']
}
def balanced(text,start):
 depth=0
 for m in re.finditer(r'</?div\b[^>]*>',text[start:]):
  depth+=-1 if m[0].startswith('</') else 1
  if depth==0:return text[start:start+m.end()]
 raise AssertionError('Unclosed explanatory section')

def apply_explanation_navigation(text):
 for panel,targets in TARGETS.items():
  m=re.search(r'<div class="panel" id="panel-'+panel+'">',text);assert m
  original=balanced(text,m.start());part=original
  blocks=list(re.finditer(r'<div class="gsec"[^>]*>',part));assert len(blocks)==len(targets)
  for match,target in reversed(list(zip(blocks,targets))):
   old=balanced(part,match.start());body=old[old.index('>')+1:-6]
   body=re.sub(r'<!-- explanation-return:start -->.*?<!-- explanation-return:end -->','',body,flags=re.S)
   already_anchored=target in ('dialect-region','negative-possibility')
   attrs=(' id="'+target+'"') if not already_anchored else ''
   opening='<div class="gsec"'+attrs+' data-explanation-search="'+target+'">'
   back='' if target=='negative-possibility' else '<!-- explanation-return:start --><p class="explanation-search-return"><a href="#search">← 検索結果へ戻る</a></p><!-- explanation-return:end -->'
   new=opening+body+back+'</div>';part=part[:match.start()]+new+part[match.start()+len(old):]
  text=text[:m.start()]+part+text[m.start()+len(original):]
 return text
