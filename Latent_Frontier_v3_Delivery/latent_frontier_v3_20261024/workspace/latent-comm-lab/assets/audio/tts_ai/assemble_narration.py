"""Measured PCM cue/scene assembly and loudness checks, not speech recognition.
Preserves narration wording. Silence/tempo transformations and exact boundaries are logged.
No actual listening or pronunciation certification is claimed.
"""
from pathlib import Path
import json,wave,array,sys,subprocess,math,re,hashlib,datetime,argparse
ROOT=Path(__file__).resolve().parent;W=ROOT.parents[2];RATE=44100

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def readpcm(p):
 with wave.open(str(p),'rb') as f:
  assert f.getnchannels()==1 and f.getsampwidth()==2 and f.getframerate()==RATE
  return f.readframes(f.getnframes())
def writepcm(p,b):
 p.parent.mkdir(exist_ok=True,parents=True)
 with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(b)
def ff(args):return subprocess.run(['ffmpeg','-hide_banner','-nostats','-y']+list(args),capture_output=True,text=True,check=True)
def stats(p):
 b=readpcm(p);a=array.array('h',b)
 if sys.byteorder!='little':a.byteswap()
 return {'path':str(p.relative_to(W)),'sha256':sha(p),'frames':len(a),'duration_seconds':len(a)/RATE,'sample_rate':RATE,'channels':1,'sample_peak':max(abs(x) for x in a),'sample_rms':math.sqrt(sum(x*x for x in a)/len(a)),'samples_at_int16_limit':sum(abs(x)>=32760 for x in a)}
def trim(p,out):
 b=readpcm(p);a=array.array('h',b)
 if sys.byteorder!='little':a.byteswap()
 audible=[i for i,x in enumerate(a) if abs(x)>180];assert audible
 start=max(0,audible[0]-round(.06*RATE));end=min(len(a),audible[-1]+1+round(.12*RATE));writepcm(out,b[start*2:end*2]);return start/RATE,(len(a)-end)/RATE,(end-start)/RATE

def tc(t,sep=','):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}{sep}{ms%1000:03}'

ap=argparse.ArgumentParser();ap.add_argument('--edition',choices=['intro_90','explainer_360','all'],default='all');args=ap.parse_args()
manifest=json.loads((ROOT/'manifest.json').read_text())
for stem in (['intro_90','explainer_360'] if args.edition=='all' else [args.edition]):
 data=json.loads((W/f'assets/audio/{stem}.narration.json').read_text());items=[c for c in manifest['chunks'] if c['edition']==stem]
 assert all((ROOT/'raw'/(c['id']+'.wav')).exists() for c in items),'Wait for every cue of this edition to download'
 cue_records=[];scene_records=[];all_pcm=bytearray();silence=lambda frames:b'\0\0'*frames
 for scene in data['scenes']:
  chunks=[c for c in items if c['scene_id']==scene['scene_id']];trimmed=[]
  for c in chunks:
   rp=ROOT/'raw'/(c['id']+'.wav');receipt=json.loads((ROOT/'receipts'/(c['id']+'.json')).read_text());assert receipt['status']=='downloaded' and receipt['response']['credits_used']==0 and receipt['audio']['sha256']==sha(rp)
   out=ROOT/'chunks'/(c['id']+'.trimmed.wav');lead,tail,dur=trim(rp,out);trimmed.append((c,out,lead,tail,dur))
  # Bounded speed fitting only. Never speed up beyond 1.10x or slow below 0.80x.
  budget=scene['duration'];target_pause=.3*(len(chunks)-1)+.55;raw_total=sum(x[4] for x in trimmed)
  tempo=min(1.10,max(.80,raw_total/(budget-target_pause)))
  processed=[]
  for c,p,lead,tail,dur in trimmed:
   out=ROOT/'chunks'/(c['id']+'.timed.wav');outdur=dur/tempo
   ff(['-i',str(p),'-af',f'atempo={tempo:.9f},afade=t=in:st=0:d=0.005,afade=t=out:st={max(0,outdur-.01):.9f}:d=0.01','-ar',str(RATE),'-ac','1','-c:a','pcm_s16le',str(out)])
   pcm=readpcm(out);processed.append((c,out,pcm,lead,tail))
  target_frames=round(budget*RATE);content_frames=sum(len(x[2])//2 for x in processed);remaining=target_frames-content_frames
  assert remaining>=round(.15*RATE),'Scene cannot fit within bounded 1.10x tempo; retime explicitly instead of forcing speed'
  # Allocate actual remaining silence, avoiding a single long blank tail.
  weights=[.7]+[1.]*(len(processed)-1)+[1.3];den=sum(weights);gaps=[round(remaining*w/den) for w in weights];gaps[-1]+=remaining-sum(gaps)
  assert max(gaps)/RATE<=2.5,'Pause would exceed 2.5 seconds; needs editorial retiming'
  scene_pcm=bytearray(silence(gaps[0]));cursor=gaps[0]
  for i,(c,p,pcm,lead,tail) in enumerate(processed):
   start=scene['start']+cursor/RATE;end=start+len(pcm)/2/RATE
   caption_start=max(scene['start'],start-min(.08,gaps[i]/RATE*.45));caption_end=min(scene['end'],end+min(.14,gaps[i+1]/RATE*.45))
   cue_records.append({**c,'audio_start':round(start,6),'audio_end':round(end,6),'start':round(caption_start,3),'end':round(caption_end,3),'text':c['display_text'],'timing_method':'measured exact PCM chunk frames, with documented display margins','tempo_factor':tempo,'raw_audio':str((ROOT/'raw'/(c['id']+'.wav')).relative_to(W)),'timed_audio':str(p.relative_to(W)),'raw_trim_leading_seconds':lead,'raw_trim_trailing_seconds':tail,'receipt':str((ROOT/'receipts'/(c['id']+'.json')).relative_to(W))})
   scene_pcm+=pcm;cursor+=len(pcm)//2;scene_pcm+=silence(gaps[i+1]);cursor+=gaps[i+1]
  assert len(scene_pcm)//2==target_frames
  out=ROOT/'scenes'/(stem+'_'+scene['scene_id']+'.pre_normalization.wav');writepcm(out,scene_pcm);all_pcm+=scene_pcm
  scene_records.append({'scene_id':scene['scene_id'],'start':scene['start'],'end':scene['end'],'duration':budget,'raw_trimmed_speech_seconds':raw_total,'tempo_factor':tempo,'pause_seconds':[g/RATE for g in gaps],'pcm_frames':target_frames,'pre_normalization_audio':str(out.relative_to(W))})
 pre=ROOT/(stem+'.pre_normalization.wav');writepcm(pre,all_pcm)
 measure=ff(['-i',str(pre),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-']);j=json.loads(re.findall(r'\{[\s\S]*?\}',measure.stderr)[-1]);dump(ROOT/(stem+'.loudness_before.json'),j)
 filter=f"loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=json"
 normalized=ROOT/(stem+'.normalized.wav');ff(['-i',str(pre),'-af',filter,'-ar',str(RATE),'-ac','1','-c:a','pcm_s16le',str(normalized)])
 target=round(data['requested_duration']*RATE);pcm=readpcm(normalized);pcm=(pcm+silence(max(0,target-len(pcm)//2)))[:target*2]
 final=W/f'assets/audio/{stem}.narration.wav';writepcm(final,pcm);a=stats(final);assert a['sample_peak']<32760 and a['sample_rms']>100
 after=ff(['-i',str(final),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-']);loud=json.loads(re.findall(r'\{[\s\S]*?\}',after.stderr)[-1]);dump(ROOT/(stem+'.loudness_after.json'),loud)
 for scene in scene_records:
  p=ROOT/'scenes'/(stem+'_'+scene['scene_id']+'.wav');writepcm(p,pcm[round(scene['start']*RATE)*2:round(scene['end']*RATE)*2]);scene['audio']=stats(p)
 # Every display cue covers one exact generated audio chunk, not proportional text-duration guessing.
 assert ''.join(c['text'].replace('\n','') for c in cue_records)==''.join(s['narration'] for s in data['scenes'])
 assert all(cue_records[i]['end']<=cue_records[i+1]['start'] for i in range(len(cue_records)-1))
 for c in cue_records:
  assert c['start']<=c['audio_start']<c['audio_end']<=c['end']+.001
  assert len(c['text'].splitlines())<=2 and max(map(len,c['text'].splitlines()))<=22
 report={'edition':stem,'status':'audio_created_measured_cue_timing','audio':a,'scenes':scene_records,'cues':cue_records,'actual_audio_duration_seconds':a['duration_seconds'],'requested_duration':data['requested_duration'],'voice':'TTS.ai MeloTTS / ZH','license':'PERSONAL AND NONCOMMERCIAL USE ONLY','loudness_after':{'integrated_lufs':float(loud['input_i']),'true_peak_dbtp':float(loud['input_tp']),'loudness_range_lu':float(loud['input_lra']),'measurement':'FFmpeg loudnorm input statistics measured from the normalized final WAV'},'timing_method':'exact generated chunk PCM boundaries, not ASR or text-length allocation','word_alignment_verified':False,'audio_listened':False,'pronunciation_review':'not_performed','research_state':'NOT_RUN'}
 dump(ROOT/(stem+'.assembly.json'),report)
 base=W/f'assets/subtitles/{stem}.audio_timed';dump(Path(str(base)+'.json'),cue_records)
 Path(str(base)+'.srt').write_text('\n\n'.join(f"{i+1}\n{tc(c['start'])} --> {tc(c['end'])}\n{c['text']}" for i,c in enumerate(cue_records))+'\n')
 Path(str(base)+'.vtt').write_text('WEBVTT\n\nNOTE Exact synthesized PCM chunk boundaries; not word-level forced alignment. Personal/noncommercial only.\n\n'+'\n\n'.join(f"{tc(c['start'],'.')} --> {tc(c['end'],'.')}\n{c['text']}" for c in cue_records)+'\n')
 print(stem,a['duration_seconds'],'seconds',len(cue_records),'measured cues','loudness',loud['input_i'],loud['input_tp'],flush=True)
