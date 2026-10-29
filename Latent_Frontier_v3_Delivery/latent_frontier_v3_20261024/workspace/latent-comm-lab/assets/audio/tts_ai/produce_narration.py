"""Authorized anonymous TTS.ai production only. No research inference or paid fallback.
Synthesizes the existing 1,754 public/synthetic characters once in cue-sized chunks.
Never resubmits an uncertain POST. Rate limited, one job in flight, durable receipts.
"""
from pathlib import Path
import json,time,datetime,hashlib,urllib.request,urllib.error,urllib.parse,wave,math,array,sys,subprocess,argparse,os,tempfile
ROOT=Path(__file__).resolve().parent;W=ROOT.parents[2]
# Completed generation must never be replaced by this historical58-request summary.
if (ROOT/'generation_summary.json').exists() and json.loads((ROOT/'generation_summary.json').read_text()).get('status')=='all_audio_downloaded':
 raise SystemExit('All unique narration audio already downloaded; reuse current WAVs and cumulative provenance. No network action.')
args=argparse.ArgumentParser(description=__doc__);args.add_argument('--private-recovery-dir',type=Path,required=True);args.add_argument('--allow-network',action='store_true');options=args.parse_args()
# This flag is only an execution safeguard. It is not user authorization.
if not options.allow_network:raise SystemExit('Network disabled; obtain applicable user authorization before production.')
REC=options.private_recovery_dir.resolve()
if REC.is_relative_to(W):raise SystemExit('Private recovery state must be outside the deliverable workspace.')
REC.mkdir(mode=0o700,parents=True,exist_ok=True);(REC/'receipts').mkdir(exist_ok=True)
API='https://api.tts.ai/v1/tts/';POLL='https://api.tts.ai/v1/speech/results/?uuid='
LAST=0

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);fd,n=tempfile.mkstemp(dir=p.parent,prefix='.'+p.stem)
 with os.fdopen(fd,'w') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(n,p)
def dump(p,d):
 atomic(p,d)
 if p.parent==REC/'receipts':
  safe={k:d[k] for k in ['id','edition','scene_id','characters','request_url','request_body','authentication','submitted_at_utc','status','license','audio','downloaded_at_utc'] if k in d}
  safe['response']={k:d.get('response',{}).get(k) for k in ['status','credits_used','credits_remaining','instructions_supported','instructions_applied']}
  safe['recovery_rule']='Pending jobs are never resubmitted when private recovery state is unavailable.'
  atomic(ROOT/'receipts'/p.name,safe);atomic(ROOT/'public_receipts'/p.name,safe)
  rows=[]
  for q in sorted((REC/'receipts').glob('*.json')):
   r=json.loads(q.read_text());rows.append({'id':r['id'],'status':r['status'],'characters':r['characters'],'credits_used':r.get('response',{}).get('credits_used')})
  atomic(ROOT/'public_progress.json',{'checked_at_utc':now(),'chunks':rows,'transient_capabilities_excluded':True})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def request(url,data=None):
 global LAST
 if time.monotonic()-LAST<8:time.sleep(8-(time.monotonic()-LAST))
 LAST=time.monotonic()
 req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'} if data is not None else {})
 with urllib.request.urlopen(req,timeout=90) as r:return r.status,dict(r.headers),r.read()
def stats(p):
 with wave.open(str(p),'rb') as f:
  channels,sw,rate,n=f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes();b=f.readframes(n)
 assert sw==2 and channels==1 and n>0
 a=array.array('h',b)
 if sys.byteorder!='little':a.byteswap()
 rms=math.sqrt(sum(x*x for x in a)/len(a));peak=max(abs(x) for x in a)
 assert rms>1 and peak>0
 return {'channels':channels,'sample_width_bytes':sw,'sample_rate':rate,'frames':n,'duration_seconds':n/rate,'sample_peak':peak,'sample_rms':rms,'sha256':sha(p),'audio_listened':False}
chunks=[]
for stem in ['intro_90','explainer_360']:
 d=json.loads((W/f'assets/audio/{stem}.narration.json').read_text())
 for c in d['cues']:
  text=c['text'].replace('\n','');assert 0<len(text)<=500
  chunks.append({'id':stem+'_'+str(c['id']).zfill(3),'edition':stem,'scene_id':c['scene_id'],'cue_id':c['id'],'display_text':c['text'],'text':text,'characters':len(text)})
assert len(chunks)==58 and sum(c['characters'] for c in chunks)==1754
manifest={'created_at_utc':now(),'scope':'public/synthetic media narration only','provider':'TTS.ai','endpoint':API,'documentation':'https://tts.ai/api/','terms':'https://tts.ai/terms/','terms_effective_date':'2026-09-14','license':'PERSONAL AND NONCOMMERCIAL USE ONLY','authentication':'none','model':'melotts','voice':'ZH','language':'zh','format':'wav','speed':1.0,'budget':{'characters':1754,'requests':58,'max_chars_per_request':500,'daily_character_limit':5000,'prior_probe_characters':47,'min_seconds_between_api_requests':8,'concurrent_jobs':1},'chunks':chunks,'research_state':'NOT_RUN','audio_listened':False,'asr_used':False}
if not (ROOT/'manifest.json').exists():dump(ROOT/'manifest.json',manifest)
else:assert json.loads((ROOT/'manifest.json').read_text())['chunks']==chunks
for c in chunks:
 p=REC/'receipts'/(c['id']+'.json');out=ROOT/'raw'/(c['id']+'.wav')
 public=ROOT/'public_receipts'/(c['id']+'.json')
 if not p.exists() and public.exists():
  known=json.loads(public.read_text())
  if known.get('status')=='downloaded':
   assert out.exists() and sha(out)==known['audio']['sha256'];continue
  raise RuntimeError('Checkpoint has uncertain prior request without private recovery ID; do not resubmit: '+c['id'])
 if p.exists():
  r=json.loads(p.read_text())
  if r.get('status')=='downloaded':assert out.exists() and sha(out)==r['audio']['sha256'];continue
  if not r.get('uuid'):raise RuntimeError('Uncertain or rejected prior POST; no automatic resubmission: '+c['id'])
 else:
  body={'model':'melotts','text':c['text'],'voice':'ZH','format':'wav','language':'zh','speed':1.0}
  r={'id':c['id'],'edition':c['edition'],'scene_id':c['scene_id'],'characters':c['characters'],'request_url':API,'request_body':body,'authentication':'none','submitted_at_utc':now(),'status':'submitting_outcome_not_yet_known','license':'PERSONAL AND NONCOMMERCIAL USE ONLY'};dump(p,r)
  try:
   status,headers,b=request(API,json.dumps(body,ensure_ascii=False).encode());j=json.loads(b)
   r.update(response_http_status=status,response_headers=headers,response=j)
   if status!=200 or j.get('credits_used')!=0 or not j.get('uuid'):
    r['status']='stopped_unexpected_response';dump(p,r);raise RuntimeError('Not a confirmed free queued job: '+str(j))
   r.update(uuid=j['uuid'],status='queued');dump(p,r)
  except Exception as e:
   r['exception']=type(e).__name__+': '+str(e);dump(p,r);raise
 print('QUEUED',c['id'],c['characters'],'[private recovery reference saved]',flush=True)
 while True:
  time.sleep(15)
  status,headers,b=request(POLL+urllib.parse.quote(r['uuid']));j=json.loads(b)
  with (REC/'poll_history.jsonl').open('a') as f:f.write(json.dumps({'at_utc':now(),'id':c['id'],'status':status,'response':j},ensure_ascii=False)+'\n')
  if j.get('status')=='failed':r.update(status='provider_failed',poll_result=j);dump(p,r);raise RuntimeError('Provider failed '+c['id'])
  if j.get('status')=='completed':
   url=j.get('result_url') or j.get('url');u=urllib.parse.urlparse(url)
   if u.scheme!='https' or u.hostname not in ['cdn.tts.ai','api.tts.ai']:raise RuntimeError('Unexpected result domain; stop')
   status,headers,b=request(url);out.write_bytes(b);a=stats(out)
   r.update(status='downloaded',poll_result=j,audio=a,download_url=url,downloaded_at_utc=now());dump(p,r);print('DOWNLOADED',c['id'],a['duration_seconds'],flush=True);break
summary={'finished_at_utc':now(),'status':'all_audio_downloaded','characters':1754,'jobs':58,'credits_used_total':0,'audio_listened':False,'receipts':[str((ROOT/'receipts'/(c['id']+'.json')).relative_to(W)) for c in chunks],'license':'PERSONAL AND NONCOMMERCIAL USE ONLY','research_state':'NOT_RUN'}
dump(ROOT/'generation_summary.json',summary);print('ALL AUDIO DOWNLOADED',flush=True)

subprocess.run([sys.executable,str(ROOT/'sanitize_provenance.py'),'--private-recovery-dir',str(REC)],check=True)
