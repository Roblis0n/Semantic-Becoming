"""Decode and inspect actual narrated media, measured cue timing and waveform metadata.
No speech recognition, research model execution or claim of auditory listening.
"""
from pathlib import Path
import json,subprocess,hashlib,wave,array,math,re,sys,argparse,datetime,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def ff(args):return subprocess.run(['ffmpeg','-hide_banner','-nostats','-y']+args,capture_output=True,check=True)
a=argparse.ArgumentParser();a.add_argument('--edition',choices=['intro_90','explainer_360','all'],default='all');args=a.parse_args()
for stem in (['intro_90','explainer_360'] if args.edition=='all' else [args.edition]):
 root=W/'assets/video'/stem;p=root/(stem+'_narrated_personal.mp4');assembly=json.loads((W/f'assets/audio/tts_ai/{stem}.assembly.json').read_text());cues=json.loads((W/f'assets/subtitles/{stem}.audio_timed.json').read_text());tl=json.loads((root/'timeline_audio.json').read_text())
 probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,check=True).stdout);vs=[s for s in probe['streams'] if s['codec_type']=='video'];aus=[s for s in probe['streams'] if s['codec_type']=='audio'];assert len(vs)==len(aus)==1 and vs[0]['width']==1280 and vs[0]['height']==720 and vs[0]['r_frame_rate']=='24/1';assert aus[0]['channels']==1;assert abs(float(probe['format']['duration'])-assembly['requested_duration'])<.05
 decode=ff(['-v','error','-i',str(p),'-f','null','-']);assert not decode.stderr
 raw=ff(['-v','error','-i',str(p),'-map','0:a:0','-ar','44100','-ac','1','-f','s16le','-']).stdout;pcm=array.array('h',raw)
 if sys.byteorder!='little':pcm.byteswap()
 wave_stats={'decoded_pcm_frames':len(pcm),'decoded_audio_seconds':len(pcm)/44100,'peak':max(abs(x) for x in pcm),'rms':math.sqrt(sum(x*x for x in pcm)/len(pcm)),'samples_at_int16_limit':sum(abs(x)>=32760 for x in pcm)};assert wave_stats['rms']>100 and wave_stats['samples_at_int16_limit']==0
 loud=ff(['-i',str(p),'-map','0:a:0','-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-']);loudness=json.loads(re.findall(r'\{[\s\S]*?\}',loud.stderr.decode())[-1]);assert float(loudness['input_tp'])<0
 silence=ff(['-i',str(p),'-map','0:a:0','-af','silencedetect=noise=-45dB:d=0.25','-f','null','-']);silences=[float(x) for x in re.findall(r'silence_duration: ([\d.]+)',silence.stderr.decode())];assert not silences or max(silences)<3
 # Check exact original narration coverage, no cross-scene subtitle leakage or overlap.
 narration=json.loads((W/f'assets/audio/{stem}.narration.json').read_text());assert ''.join(c['text'].replace('\n','') for c in cues)==''.join(s['narration'] for s in narration['scenes'])
 for i,c in enumerate(cues):
  sc=next(s for s in narration['scenes'] if s['scene_id']==c['scene_id']);assert sc['start']<=c['start']<c['end']<=sc['end'];assert c['start']<=c['audio_start'] and c['end']+.001>=c['audio_end'];assert len(c['text'].splitlines())<=2 and max(map(len,c['text'].splitlines()))<=22
  if i:assert cues[i-1]['end']<=c['start']
 xml=ET.parse(root/'project_audio.mlt');assert len(xml.findall('producer'))==len(narration['scenes'])+1
 samples=[];out=root/'narrated_samples';out.mkdir(exist_ok=True)
 for i,t in [(0,.5)]+[(i+1,(c['audio_start']+c['audio_end'])/2) for i,c in enumerate(cues)]:
  fp=out/f'cue-{i:03}.png';ff(['-v','error','-ss',str(t),'-i',str(p),'-frames:v','1',str(fp)]);samples.append({'cue':i,'second':t,'path':str(fp.relative_to(W)),'sha256':sha(fp)})
 f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
 for k in range(0,len(samples),8):
  group=samples[k:k+8];im=Image.new('RGB',(1280,382*((len(group)+1)//2)),'#F4F1E8');draw=ImageDraw.Draw(im)
  for i,s in enumerate(group):
   x=i%2*640;y=i//2*382;im.paste(Image.open(W/s['path']).resize((640,360)),(x,y+22));draw.text((x+12,y),stem+f" cue {s['cue']} @ {s['second']:.2f}s",font=f,fill='#262A25')
  im.save(out/f'contact-{k//8+1:02}.jpg',quality=94)
 report={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'edition':stem,'status':'containers_and_measured_timing_pass_audition_pending','video':{'path':str(p.relative_to(W)),'sha256':sha(p),'duration_seconds':float(probe['format']['duration']),'video_codec':vs[0]['codec_name'],'audio_codec':aus[0]['codec_name'],'audio_channels':aus[0]['channels'],'video_start_time':vs[0].get('start_time'),'audio_start_time':aus[0].get('start_time'),'full_decode_passed':True},'waveform':wave_stats,'actual_container_loudness':{'integrated_lufs':float(loudness['input_i']),'true_peak_dbtp':float(loudness['input_tp']),'loudness_range_lu':float(loudness['input_lra']),'measurement':'FFmpeg loudnorm input statistics measured from the actual decoded container'},'loudnorm_measurement_raw':loudness,'maximum_detected_silence_seconds':max(silences,default=0),'subtitle_cues':len(cues),'subtitle_timing':'measured exact generated PCM chunk boundaries with margins, no proportional text-duration guessing','source_text_coverage':True,'subtitle_scene_bounds':True,'samples':samples,'audio_listened':False,'spoken_word_accuracy_checked':False,'word_level_alignment':False,'mlt_xml_validated':True,'mlt_editor_gui_opened':False,'license':'PERSONAL AND NONCOMMERCIAL USE ONLY','research_state':'NOT_RUN'}
 dump(root/'narrated_qa.json',report);print(stem,report['video'],flush=True)
