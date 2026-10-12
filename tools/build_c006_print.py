"""A4の絵札・読み札PDF。辞典JSONと配信用WebPから再生成する。"""
import argparse, io, json, re
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parents[1]
NAVY=HexColor('#223c49'); RED=HexColor('#a74632'); GREY=HexColor('#56646a')
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--font',default='C:/Windows/Fonts/YuGothR.ttc')
    ap.add_argument('--bold-font',default='C:/Windows/Fonts/YuGothB.ttc')
    ap.add_argument('--output',type=Path,default=ROOT/'downloads/enshu-karuta-122.pdf')
    args=ap.parse_args()
    pdfmetrics.registerFont(TTFont('JP',args.font,subfontIndex=0))
    pdfmetrics.registerFont(TTFont('JPB',args.bold_font,subfontIndex=0))
    entries=json.loads((ROOT/'data/c006-dictionary.json').read_text(encoding='utf-8'))['entries']
    # 印刷の並びもウェブの五十音順に合わせる。既成の静的一覧を唯一の順序として使う。
    html=(ROOT/'c006.html').read_text(encoding='utf-8')
    order=re.findall(r'<div class="entry" id="w-[^"]+" data-id="([a-z-]+)">',html)
    byid={e['id']:e for e in entries}
    assert len(order)==len(entries)==122 and set(order)==set(byid)
    entries=[byid[i] for i in order]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(args.output),pagesize=A4,pageCompression=1,invariant=1)
    c.setTitle('遠州弁かるた 122語 絵札・読み札 | 磐田物語')
    c.setAuthor('磐田物語'); c.setSubject('2026-10-12版 / 用例は編集部作例、絵札は生成AIを用いて制作')
    W,H=A4
    def para(text,x,top,width,size=11,leading=None,bold=False,color=NAVY,maxheight=None):
        style=ParagraphStyle('p',fontName='JPB' if bold else 'JP',fontSize=size,leading=leading or size*1.65,textColor=color,wordWrap='CJK')
        p=Paragraph(escape(text).replace('\n','<br/>'),style);pw,ph=p.wrap(width,H)
        if maxheight is not None and ph>maxheight:raise ValueError(f'overflow: {text}')
        p.drawOn(c,x,top-ph);return top-ph
    def picture(e,x,y,w,h):
        p=ROOT/f"assets/karuta/c006/{e['id']}-900.webp"
        # 60×80mmの札に約254dpi。配信上限25MiBに収まるJPEGを埋め込む。
        im=Image.open(p).convert('RGB');im.thumbnail((600,800),Image.Resampling.LANCZOS)
        b=io.BytesIO();im.save(b,'JPEG',quality=75,optimize=True);b.seek(0)
        c.drawImage(ImageReader(b),x,y,w,h)
    def footer(n):
        c.setFillColor(GREY);c.setFont('JP',8)
        c.drawString(20*mm,10*mm,'磐田物語  https://iwata-monogatari.net/c006  |  2026-10-12')
        c.drawRightString(W-20*mm,10*mm,str(n))
    c.setFillColor(RED);c.rect(20*mm,H-30*mm,12*mm,2*mm,fill=1,stroke=0)
    y=para('遠州弁かるた',20*mm,H-39*mm,W-40*mm,29,bold=True)
    y=para('引札風の122語  /  絵札・読み札',20*mm,y-6*mm,W-40*mm,16)
    for i,key in enumerate(['dara','senhiki','anmo']):picture(byid[key],(20+i*57)*mm,H-148*mm,50*mm,66.667*mm)
    y=H-158*mm
    for title,text in [
        ('印刷と準備','A4・縦・片面、拡大縮小100％（実際のサイズ）で印刷します。2頁以降の枠を切り分けると、60×80mmの札になります。各段の左が絵札、右が読み札です。下の番号で組を確認できます。'),
        ('遊び方','最初は10〜20組を選び、見出し語と例文を読んで絵札を探します。同じ頭文字の札があるため、文字だけでなく場面で見分けてください。言い方の違いや「知らない」も、会話のきっかけにできます。'),
        ('制作・利用','例文は編集部の作例、絵は生成AIを用いた新規制作です。家庭・非営利の教育利用は出典明記で利用できます。営利利用は事前相談。詳しくは辞典の利用案内と /c176 をご覧ください。')]:
        y=para(title,20*mm,y,W-40*mm,11,bold=True)
        y=para(text,20*mm,y-1.5*mm,W-40*mm,10,16)-5*mm
    assert y>16*mm
    footer(1);c.showPage()
    for start in range(0,len(entries),3):
        c.setFont('JPB',10);c.setFillColor(NAVY)
        c.drawString(42.5*mm,H-15*mm,'絵札')
        c.drawString(107.5*mm,H-15*mm,'読み札（例文は編集部作例）')
        for row,e in enumerate(entries[start:start+3]):
            x=42.5*mm; y=H-(21+row*87+80)*mm;cw=60*mm;ch=80*mm;rx=107.5*mm
            picture(e,x,y,cw,ch)
            c.setStrokeColor(GREY);c.setLineWidth(.35);c.rect(x,y,cw,ch);c.rect(rx,y,cw,ch)
            c.setFillColor(HexColor('#faf7ef'));c.rect(rx+.5,y+.5,cw-1,ch-1,fill=1,stroke=0)
            top=y+ch-6*mm
            title_size=min(18,(cw-10*mm)/pdfmetrics.stringWidth(e['w'],'JPB',1))
            top=para(e['w'],rx+5*mm,top,cw-10*mm,title_size,bold=True,maxheight=22*mm)
            top=para(e['k'],rx+5*mm,top-1.5*mm,cw-10*mm,9,color=GREY,maxheight=12*mm)
            top=para(e['ex'],rx+5*mm,top-5*mm,cw-10*mm,12.5,19,bold=True,maxheight=30*mm)
            top=para('標準語：'+e['std'],rx+5*mm,top-4*mm,cw-10*mm,9.5,15,color=GREY,maxheight=23*mm)
            if top<y+5*mm:raise ValueError('card overflow '+e['id'])
            label=f"{start+row+1:03d}  {e['id']}"
            c.setFont('JP',6.8);c.setFillColor(GREY)
            c.drawString(x,y-3*mm,label);c.drawString(rx,y-3*mm,label)
        footer(start//3+2);c.showPage()
    c.save()
    print(f'{args.output}: 42 pages, {len(entries)} pairs, {args.output.stat().st_size:,} bytes')
if __name__=='__main__':main()
