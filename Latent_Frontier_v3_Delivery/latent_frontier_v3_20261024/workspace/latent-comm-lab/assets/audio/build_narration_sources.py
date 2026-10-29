"""Complete narration, SSML and subtitle timing budgets. No audio synthesis."""
from pathlib import Path
import json,re,xml.etree.ElementTree as ET,hashlib
WORK=Path(__file__).resolve().parents[2];PLAN=WORK.parents[1]
def timecode(t,sep=','):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}{sep}{ms%1000:03}'
def lines(txt,width=22):
 if len(txt)<=width:return txt
 # CJK line-breaking: closing punctuation never begins a line; opening quotes never end one.
 closing='，、。？！：；）》」』】”’'
 opening='（《「『【“‘'
 candidates=[k for k in range(max(1,len(txt)-width),min(width,len(txt)-1)+1) if txt[k] not in closing and txt[k-1] not in opening]
 assert candidates,'No two-line punctuation-safe split available'
 split=max(candidates,key=lambda k:(txt[k-1] in '，、。？！：；',k))
 return txt[:split]+'\n'+txt[split:]
def cue_chunks(txt):
 # Keep the complete evidence prohibition within one cue, preserving every source word.
 prohibition='系统不能先生成一个结论，再把自己生成的观察当作现实证据。'
 if prohibition in txt:
  before,after=txt.split(prohibition,1)
  return cue_chunks(before)+[prohibition]+cue_chunks(after)
 parts=re.findall(r'.*?[。？！；，：]|.+$',txt)
 chunks=[];current=''
 for p in parts:
  while len(p)>44:
   if current:chunks.append(current);current=''
   chunks.append(p[:40]);p=p[40:]
  if len(current)+len(p)>42:
   if current:chunks.append(current)
   current=p
  else:current+=p
 if current:chunks.append(current)
 return chunks
all_data={}
for num,stem in [(3,'intro_90'),(4,'explainer_360')]:
 source=next((PLAN/'media').glob(f'{num:02}_*'));raw=source.read_text();blocks=re.split(r'^## ',raw,flags=re.M)[1:];scenes=[]
 for i,b in enumerate(blocks,1):
  head=b.splitlines()[0];m=re.search(r'(\d+)–(\d+)秒 · (.+)',head);start,end,title=int(m[1]),int(m[2]),m[3]
  match=re.search(r'\*\*旁白全文：\*\*\s*(.*?)(?=\n\n\*\*|\Z)',b,re.S);narr=match[1].strip();narr=re.sub(r'\s+','',narr)
  visual=re.search(r'\*\*画面(?:及动作)?：\*\*\s*([^\n]+)',b)[1]
  scenes.append({'scene_id':f'S{i:02}','start':start,'end':end,'duration':end-start,'title':title,'visual':visual,'narration':narr})
 cues=[]
 for s in scenes:
  chunks=cue_chunks(s['narration']);total=sum(map(len,chunks));t=s['start']
  for j,chunk in enumerate(chunks):
   end=s['end'] if j==len(chunks)-1 else t+s['duration']*len(chunk)/total
   cues.append({'id':len(cues)+1,'scene_id':s['scene_id'],'start':round(t,3),'end':round(end,3),'text':lines(chunk)});t=end
 assert ''.join(c['text'].replace('\n','') for c in cues)==''.join(s['narration'] for s in scenes)
 assert all(len(c['text'].splitlines())<=2 and max(map(len,c['text'].splitlines()))<=22 for c in cues)
 assert all(cues[i]['end']<=cues[i+1]['start'] for i in range(len(cues)-1))
 data={'project':stem,'requested_duration':scenes[-1]['end'],'timing_status':'draft_timing_budget_not_audio_aligned','research_state':'NOT_RUN','narration_audio_created':False,'listened':False,'source':str(source.relative_to(PLAN)),'scenes':scenes,'cues':cues,'pronunciation_notes':['H27：机制二十七','ISA：首次读“指令集”','KV：读英文字母 K、V','NOT_RUN：尚未运行','synthetic：合成的','JVP：雅可比向量积','lambda：正则化系数','四分之一：0.25','4/17：十七分之四']}
 all_data[stem]=data
 (WORK/f'assets/audio/{stem}.narration.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 (WORK/f'assets/audio/{stem}.narration.txt').write_text('\n\n'.join(f'[{s["scene_id"]} {s["start"]}–{s["end"]}秒 · {s["title"]}]\n{s["narration"]}' for s in scenes)+'\n')
 speak=ET.Element('speak',{'version':'1.0','{http://www.w3.org/XML/1998/namespace}lang':'zh-CN'});ET.SubElement(speak,'meta',{'name':'timing-status','content':'draft timing; no generated audio'})
 for s in scenes:
  p=ET.SubElement(speak,'p');ET.SubElement(p,'mark',{'name':s['scene_id']});ET.SubElement(p,'s').text=s['narration'];ET.SubElement(p,'break',{'time':'350ms'})
 (WORK/f'assets/audio/{stem}.ssml').write_text(ET.tostring(speak,encoding='unicode'))
 (WORK/f'assets/subtitles/{stem}.draft_timing.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2))
 (WORK/f'assets/subtitles/{stem}.draft_timing.srt').write_text('\n\n'.join(f'{c["id"]}\n{timecode(c["start"])} --> {timecode(c["end"])}\n{c["text"]}' for c in cues)+'\n')
 (WORK/f'assets/subtitles/{stem}.draft_timing.vtt').write_text('WEBVTT\n\nNOTE Draft timing budgets. No narration audio alignment.\n\n'+'\n\n'.join(f'{timecode(c["start"],".")} --> {timecode(c["end"],".")}\n{c["text"]}' for c in cues)+'\n')
 print(stem,len(scenes),'scenes,',len(cues),'cues,',len(''.join(s['narration'] for s in scenes)),'Chinese script characters')
(WORK/'assets/audio/README.md').write_text('''# 旁白制作源与真实边界

两版旁白完整保留当前 V3 分镜文本，附逐镜头 JSON、普通中文合成声 SSML 和字幕草稿。

未生成 WAV / MP3。实际旁白缺失，未试听，未测响度，也没有最终音频对齐字幕。未调用费用或权限不明的 TTS。视频 silent_draft 版是确实编码的无声视觉示意，不是完成配音的成片。

继续制作需先确认无新增费用、已授权的普通中文 TTS 或提供合法录音。逐段生成后，按实际时长编排，试听专业名词与公式，调整字幕，不通过强行加速凑到 90 秒。不要模仿真人声音。

SSML 是可编辑制作源，具体供应商须按其支持的 schema 校验；它不是已被 TTS 接收的证明。

发音：H27 读“机制二十七”；ISA 首次读“指令集”；KV 读英文字母；NOT_RUN 读“尚未运行”；synthetic 读“合成的”；公式采用原旁白的自然语言说明。

所有研究模型路径保持 NOT_RUN。
''')
