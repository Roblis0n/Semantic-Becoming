"""Document rendering QA only. No research modules, models or empirical claims."""
from pathlib import Path
import hashlib,json
import fitz
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[3];root=W/'run_state/checks/D03'
d=fitz.open(root/'render/main.pdf');rows=[]
for i,p in enumerate(d):
 words=p.get_text('words')
 outside=[w for w in words if w[0]<10 or w[1]<10 or w[2]>p.rect.width-10 or w[3]>p.rect.height-10]
 rows.append({'page':i+1,'characters':len(p.get_text()),'words':len(words),'outside_page_margin':outside})
structure={'pages':len(d),'pdf_text_checks':rows,'all_pages_nonempty':all(r['characters']>100 for r in rows),'out_of_page_words':sum(len(r['outside_page_margin']) for r in rows),'contact_sheets':[]}
for start in range(0,len(d),12):
 end=min(start+12,len(d));sheet=Image.new('RGB',(1600,((end-start+3)//4)*610),'#dddddd');draw=ImageDraw.Draw(sheet)
 for j in range(start,end):
  pix=d[j].get_pixmap(matrix=fitz.Matrix(.65,.65));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((390,575));x=((j-start)%4)*400+(400-im.width)//2;y=((j-start)//4)*610+25;sheet.paste(im,(x,y));draw.text((x,y-20),f'Page {j+1}',fill='black')
 path=root/f'visual/pages_{start+1:02d}_{end:02d}.jpg';sheet.save(path,quality=90);structure['contact_sheets'].append(str(path.relative_to(W)))
needles=['5.1 因果模块','每轮响应仅由当前查询','10 条件依赖索引','Pprime','actual_behavior_delta','mean relu(norm','SBV3_N03] Norman']
details={}
for needle in needles:
 pages=[]
 for i,p in enumerate(d):
  if needle in p.get_text():
   pages.append(i+1);p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(root/f'visual/detail_{i+1:02d}.png')
 details[needle]=pages
(root/'pdf_structure.json').write_text(json.dumps(structure,ensure_ascii=False,indent=2)+'\n')
(root/'render_targets.json').write_text(json.dumps({'detail_pages_by_search':details,'pdf_sha256':hashlib.sha256((root/'render/main.pdf').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pages':len(d),'outside_words':structure['out_of_page_words'],'details':details},ensure_ascii=False))
