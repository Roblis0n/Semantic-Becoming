from pathlib import Path
import fitz,json,hashlib
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;W=D.parents[3];old=fitz.open(D/'baseline/main.pdf');new=fitz.open(D/'render/main.pdf');changed=[];same=[];outside=[]
for i,p in enumerate(new):
 pix=p.get_pixmap(matrix=fitz.Matrix(1,1));previous=old[i].get_pixmap(matrix=fitz.Matrix(1,1)) if i<len(old) else None
 if previous and (pix.width,pix.height,pix.samples)==(previous.width,previous.height,previous.samples):same.append(i+1)
 else:changed.append(i+1)
 outside.extend([{'page':i+1,'word':w[4],'bbox':w[:4]} for w in p.get_text('words') if w[0]<10 or w[1]<10 or w[2]>p.rect.width-10 or w[3]>p.rect.height-10])
for start in range(0,len(changed),8):
 pages=changed[start:start+8];sheet=Image.new('RGB',(1600,610*((len(pages)+3)//4)),'#dddddd');draw=ImageDraw.Draw(sheet)
 for k,i in enumerate(pages):
  pix=new[i-1].get_pixmap(matrix=fitz.Matrix(.65,.65));im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((390,575));x=k%4*400+(400-im.width)//2;y=k//4*610+25;sheet.paste(im,(x,y));draw.text((x,y-20),f'Page {i}',fill='black')
 sheet.save(D/f'visual/changed_{start//8+1:02}.jpg',quality=94)
for i in changed:
 if '媒体状态快照' in new[i-1].get_text() or '实际试听与中文' in new[i-1].get_text():new[i-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(D/f'visual/detail_{i:02}.png')
log=(D/'latex_pass3.txt').read_text();report={'current_pdf':{'path':str((D/'render/main.pdf').relative_to(W)),'sha256':hashlib.sha256((D/'render/main.pdf').read_bytes()).hexdigest(),'pages':len(new)},'previous_pdf':{'path':str((D/'baseline/main.pdf').relative_to(W)),'sha256':hashlib.sha256((D/'baseline/main.pdf').read_bytes()).hexdigest(),'pages':len(old)},'changed_render_pages':changed,'pixel_identical_pages':same,'out_of_page_words':outside,'missing_glyph_warnings':log.count('Missing character:'),'overfull_box_warnings':log.count('Overfull \\hbox')+log.count('Overfull \\vbox'),'research_state':'NOT_RUN'}
(D/'layout_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));assert not outside and not report['missing_glyph_warnings'] and not report['overfull_box_warnings']
