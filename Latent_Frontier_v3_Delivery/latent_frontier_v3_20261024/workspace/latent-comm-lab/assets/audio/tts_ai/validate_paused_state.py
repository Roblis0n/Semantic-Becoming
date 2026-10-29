"""Local-only partial production validation; never contacts the provider.
Private recovery path is required but is not emitted into public evidence.
"""
from pathlib import Path
import argparse,array,ast,datetime,hashlib,json,math,sys,wave
P=argparse.ArgumentParser();P.add_argument('--private-recovery-dir',type=Path,required=True);args=P.parse_args()
R=Path(__file__).resolve().parent;W=R.parents[2];S=args.private_recovery_dir.resolve();assert not S.is_relative_to(W)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
private=[json.loads(p.read_text()) for p in sorted((S/'receipts').glob('*.json'))]
public=[json.loads(p.read_text()) for p in sorted((R/'receipts').glob('*.json'))]
assert len(private)==len(public)==43
assert sum(r['status']=='downloaded' for r in private)==42
assert sum(r['characters'] for r in public)==1261
assert sum(r['response']['credits_used'] for r in public)==0
pending=[r for r in private if r['status']!='downloaded'];assert len(pending)==1 and pending[0]['characters']==16 and pending[0].get('uuid')
manifest=json.loads((R/'manifest.json').read_text());assert len(manifest['chunks'])==58 and sum(c['characters'] for c in manifest['chunks'])==1754
remaining=[c for c in manifest['chunks'] if c['id'] not in {r['id'] for r in private}]
assert len(remaining)==15 and sum(c['characters'] for c in remaining)==493
waves=[]
for r in public:
 if r['status']!='downloaded':continue
 p=R/'raw'/(r['id']+'.wav');assert sha(p)==r['audio']['sha256']
 with wave.open(str(p),'rb') as f:
  channels,sw,rate,n=f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes();data=f.readframes(n)
 assert channels==1 and sw==2 and n>0
 a=array.array('h',data)
 if sys.byteorder!='little':a.byteswap()
 rms=math.sqrt(sum(x*x for x in a)/len(a));assert rms>1
 waves.append({'path':str(p.relative_to(W)),'sha256':sha(p),'frames':n,'sample_rate':rate,'duration_seconds':n/rate,'sample_rms':rms,'audio_listened':False})
assert len(list((R/'raw').glob('*.wav')))==42
secrets=set()
def collect(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if k.lower() in {'uuid','job_id','result_url','download_url'} and isinstance(x,str) and x:secrets.add(x.encode())
   else:collect(x)
 elif isinstance(v,list):
  for x in v:collect(x)
for r in private:collect(r)
for line in (S/'poll_history.jsonl').read_text().splitlines():collect(json.loads(line))
assert secrets
needles=[*secrets,str(S).encode()];scanned=0;leaks=[]
for p in W.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 scanned+=1
 tail=b''
 with p.open('rb') as f:
  while b:=f.read(1024*1024):
   b=tail+b
   if any(n in b for n in needles):leaks.append(str(p.relative_to(W)));break
   tail=b[-4096:]
assert not leaks, 'Capability-bearing content remains in public workspace; no values emitted.'
for p in R.glob('*.py'):ast.parse(p.read_text())
assert not (W/'assets/audio/explainer_360.narration.wav').exists()
assert not (W/'assets/video/explainer_360/explainer_360_narrated_personal.mp4').exists()
report={'status':'passed_local_only','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'accepted':43,'downloaded':42,'pending_accepted_chunks':1,'pending_accepted_characters':16,'unsubmitted_chunks':15,'unsubmitted_characters':493,'characters_submitted':1261,'credits_used':0,'private_recovery_preserved':True,'private_recovery_capabilities_in_deliverable':False,'workspace_files_scanned':scanned,'raw_wav_checks':waves,'long_final_wav_exists':False,'long_voiced_video_exists':False,'network_activity_performed':False,'audition_performed':False,'research_state':'NOT_RUN'}
(R/'pause_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='raw_wav_checks'}))
