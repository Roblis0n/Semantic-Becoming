"""Generate self-contained edit timelines for both current V3 video editions."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
WORK=Path(__file__).resolve().parents[3]
# subcuts retain the exact supplied scene budgets, while giving each mechanism room.
sequences={
'intro_90':[[('communication','communication_to_object',0,1)],[('animation','A03',0,1)],[('slide',26,0,1)],[('animation','A04',0,.77),('slide',15,.77,1)],[('animation','A05',0,1)],[('animation','A01',0,.33),('animation','A02',.33,.67),('slide',28,.67,1)],[('figure','F01',0,.65),('slide',33,.65,1)],[('slide',36,0,1)]],
'explainer_360':[[('communication','communication_to_object',0,.35),('slide',4,.35,.7),('slide',1,.7,1)],[('animation','A03',0,.7),('slide',11,.7,1)],[('animation','A02',0,.7),('slide',7,.7,1)],[('slide',13,0,.38),('animation','A04',.38,1)],[('slide',15,0,.5),('slide',17,.5,1)],[('slide',19,0,.3),('animation','A05',.3,.8),('slide',21,.8,1)],[('animation','A01',0,.25),('slide',25,.25,.5),('slide',28,.5,.75),('slide',29,.75,1)],[('slide',33,0,.5),('slide',34,.5,1)],[('slide',36,0,1)]]}
for stem,seq in sequences.items():
 data=json.loads((WORK/f'assets/audio/{stem}.narration.json').read_text());timeline={k:data[k] for k in ('project','requested_duration','research_state','timing_status')};timeline.update(width=1280,height=720,fps=24,render_fps=12,audio_tracks=[],audio_status='not_created_external_optional_blocker',subtitles=f'../../subtitles/{stem}.draft_timing.srt',visual_edition='silent_draft_with_burned_draft_timed_captions',source_scenes=[])
 for s,cuts in zip(data['scenes'],seq):
  q=dict(s);q['cuts']=[{'kind':kind,'source':id,'start':s['start']+a*s['duration'],'end':s['start']+b*s['duration']} for kind,id,a,b in cuts];q['clip']=f'clips/{s["scene_id"]}.mp4';timeline['source_scenes'].append(q)
 root=WORK/f'assets/video/{stem}';(root/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
 mlt=ET.Element('mlt',{'producer':'tractor','version':'7.0.0'});ET.SubElement(mlt,'profile',{'description':'HD 720p24','width':'1280','height':'720','frame_rate_num':'24','frame_rate_den':'1','progressive':'1','sample_aspect_num':'1','sample_aspect_den':'1','display_aspect_num':'16','display_aspect_den':'9','colorspace':'709'})
 for s in timeline['source_scenes']:
  producer=ET.SubElement(mlt,'producer',{'id':s['scene_id']});ET.SubElement(producer,'property',{'name':'resource'}).text=s['clip'];ET.SubElement(producer,'property',{'name':'mlt_service'}).text='avformat';ET.SubElement(producer,'property',{'name':'shotcut:caption'}).text=s['title']
 playlist=ET.SubElement(mlt,'playlist',{'id':'timeline'});ET.SubElement(playlist,'property',{'name':'shotcut:name'}).text='V1 · silent draft'
 for s in timeline['source_scenes']:ET.SubElement(playlist,'entry',{'producer':s['scene_id'],'in':'0','out':str(round(s['duration']*24)-1)})
 tractor=ET.SubElement(mlt,'tractor',{'id':'tractor','shotcut':'1','in':'0','out':str(data['requested_duration']*24-1)});ET.SubElement(tractor,'property',{'name':'shotcut:name'}).text=stem+' · 无声视觉稿';ET.SubElement(tractor,'track',{'producer':'timeline'})
 ET.indent(mlt);(root/'project.mlt').write_text(ET.tostring(mlt,encoding='unicode'))
 (root/'README.md').write_text(f'''# {stem}：无声视觉剪辑工程

目标时长 {data['requested_duration']} 秒。当前工程包含编辑时间线、分镜头 MP4、实际无声 MP4 容器、逐镜头 JSON、草稿时间字幕。

最终旁白尚未生成，没有最终音频对齐。片中明确标“无声视觉稿 / 字幕按脚本预算”，不得称为完成配音的成片。研究状态始终 NOT_RUN。

project.mlt 可供支持 MLT 的编辑器导入，使用相对路径引用 clips。该项目 XML 已静态校验；未声称在 Shotcut 图形界面中打开。timeline.json 保留每个镜头、语义对象、来源、旁白和子切换点，动画 HTML/SVG 可独立修改。

重建：在本项目根目录运行 Node 渲染脚本 assets/animations/render_media.mjs videos。需现有 sharp、ffmpeg 与系统 Noto 字体；不含字体包、不安装任何模型。

画面和开头解码检查只证明媒体可读，不证明研究机制有效。旁白授权后应根据实录时长重排，而非机械保留当前时间预算。
''')
 print(stem,'timeline ready')
