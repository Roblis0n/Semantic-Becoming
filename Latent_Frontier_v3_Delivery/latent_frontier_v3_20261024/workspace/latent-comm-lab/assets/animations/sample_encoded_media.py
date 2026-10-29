"""Extract visual QA samples from actual encoded containers, not source PNGs."""
from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[2]
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for stem,times in [('intro_90',[6,15,26,38,51,61,71,85]),('explainer_360',[11,13,55,105,145,169,200,230,240,285,320,345,357])]:
 root=W/'assets/video'/stem;target=root/'decoded_samples';target.mkdir(exist_ok=True);video=root/(stem+'_silent_draft.mp4');samples=[]
 for t in times:
  p=target/f'{t:03}.png';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(p)],check=True)
  samples.append({'second':t,'path':str(p.relative_to(W)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 im=Image.new('RGB',(1280,382*((len(samples)+1)//2)),'#F4F1E8');draw=ImageDraw.Draw(im)
 for i,s in enumerate(samples):
  x=i%2*640;y=i//2*382;im.paste(Image.open(W/s['path']).resize((640,360)),(x,y+22));draw.text((x+12,y),stem+' decoded '+str(s['second'])+'s',font=f,fill='#262A25')
 im.save(target/'contact_sheet.jpg',quality=94)
 for k in ['source']:
  ps=sorted((root/'renders').glob('*.png'));im2=Image.new('RGB',(1280,382*((len(ps)+1)//2)),'#F4F1E8');draw2=ImageDraw.Draw(im2)
  for i,p in enumerate(ps):
   x=i%2*640;y=i//2*382;im2.paste(Image.open(p).resize((640,360)),(x,y+22));draw2.text((x+12,y),stem+' '+p.stem,font=f,fill='#262A25')
  im2.save(root/'contact_sheet.jpg',quality=92)
 (target/'samples.json').write_text(json.dumps({'source':str(video.relative_to(W)),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'samples':samples,'audio_listened':False},ensure_ascii=False,indent=2))
# Contact sheets preserve slide aspect ratio.
for stem in ['research_36','brief_12']:
 root=W/'assets/slides/verified_renders';ps=sorted((root/stem).glob('*.png'))
 for k in range(0,len(ps),12):
  group=ps[k:k+12];im=Image.new('RGB',(1278,262*((len(group)+2)//3)),'#F4F1E8');draw=ImageDraw.Draw(im)
  for i,p in enumerate(group):
   x=(i%3)*426;y=(i//3)*262;im.paste(Image.open(p).resize((426,240)),(x,y+22));draw.text((x+12,y),p.stem,font=f,fill='#262A25')
  im.save(root/(stem+'_contact_'+str(k//12+1)+'.jpg'),quality=93)
