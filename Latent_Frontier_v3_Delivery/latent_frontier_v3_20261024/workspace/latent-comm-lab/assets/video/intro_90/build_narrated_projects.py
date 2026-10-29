"""Create new narrated projects while preserving every silent visual edition."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,argparse
W=Path(__file__).resolve().parents[3]
a=argparse.ArgumentParser();a.add_argument('--edition',choices=['intro_90','explainer_360','all'],default='all');args=a.parse_args()
for stem in (['intro_90','explainer_360'] if args.edition=='all' else [args.edition]):
 root=W/'assets/video'/stem;tl=json.loads((root/'timeline.json').read_text());audio=json.loads((W/f'assets/audio/tts_ai/{stem}.assembly.json').read_text())
 tl.update(timing_status='measured_synthesized_PCM_cue_boundaries',audio_status='real_narration_created_not_auditioned',visual_edition='narrated_personal_noncommercial',license='PERSONAL AND NONCOMMERCIAL USE ONLY',voice='TTS.ai / MeloTTS / ZH',subtitles=f'../../subtitles/{stem}.audio_timed.srt',audio_tracks=[{'resource':f'../../audio/{stem}.narration.wav','start':0,'duration_seconds':audio['actual_audio_duration_seconds']}],audio_timing_source=f'../../audio/tts_ai/{stem}.assembly.json',audio_listened=False,pronunciation_review='not_performed',silent_history='timeline.json and '+stem+'_silent_draft.mp4')
 for sc in tl['source_scenes']:sc['clip']=f'narrated_clips/{sc["scene_id"]}.mp4'
 (root/'timeline_audio.json').write_text(json.dumps(tl,ensure_ascii=False,indent=2))
 mlt=ET.Element('mlt',{'producer':'tractor','version':'7.0.0'});ET.SubElement(mlt,'profile',{'description':'HD 720p24 with narration','width':'1280','height':'720','frame_rate_num':'24','frame_rate_den':'1','progressive':'1','sample_aspect_num':'1','sample_aspect_den':'1','display_aspect_num':'16','display_aspect_den':'9','colorspace':'709'})
 for sc in tl['source_scenes']:
  p=ET.SubElement(mlt,'producer',{'id':sc['scene_id']});ET.SubElement(p,'property',{'name':'resource'}).text=sc['clip'];ET.SubElement(p,'property',{'name':'mlt_service'}).text='avformat';ET.SubElement(p,'property',{'name':'shotcut:caption'}).text=sc['title']
 p=ET.SubElement(mlt,'producer',{'id':'narration'});ET.SubElement(p,'property',{'name':'resource'}).text=f'../../audio/{stem}.narration.wav';ET.SubElement(p,'property',{'name':'mlt_service'}).text='avformat'
 v=ET.SubElement(mlt,'playlist',{'id':'visual'});ET.SubElement(v,'property',{'name':'shotcut:name'}).text='V1 · measured captions'
 for sc in tl['source_scenes']:ET.SubElement(v,'entry',{'producer':sc['scene_id'],'in':'0','out':str(round(sc['duration']*24)-1)})
 a=ET.SubElement(mlt,'playlist',{'id':'audio'});ET.SubElement(a,'property',{'name':'shotcut:name'}).text='A1 · synthesized Mandarin · PERSONAL/NONCOMMERCIAL';ET.SubElement(a,'entry',{'producer':'narration','in':'0','out':str(tl['requested_duration']*24-1)})
 tr=ET.SubElement(mlt,'tractor',{'id':'tractor','in':'0','out':str(tl['requested_duration']*24-1)});ET.SubElement(tr,'track',{'producer':'visual'});ET.SubElement(tr,'track',{'producer':'audio','hide':'video'})
 ET.indent(mlt);(root/'project_audio.mlt').write_text(ET.tostring(mlt,encoding='unicode'))
 print(stem,'narrated editable project ready')
