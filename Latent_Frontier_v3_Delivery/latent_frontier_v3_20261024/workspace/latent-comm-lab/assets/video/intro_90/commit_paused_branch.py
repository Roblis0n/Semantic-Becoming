"""Commit the honest pending-authorization checkpoint; local operations only.
All available outputs are hashed. No missing long speech is declared complete.
"""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
W=Path(__file__).resolve().parents[3];sys.dont_write_bytecode=True
def rd(p):return json.loads((W/p).read_text())
notes={
 'V04':'Actual 90-second personal/noncommercial narrated H.264/AAC edition and PCM WAV, measured 14-cue subtitles and editable timeline/MLT. Full A/V decode and all cue-midpoint frames inspected. Mandatory actual audition remains blocked; no pronunciation assessment.',
 'V05':'Actual 360-second silent visual edition and complete editable sources preserved. Long voiced export and full narration WAV do not exist: 28/44 long cue WAVs downloaded, one 16-character cue already accepted but outcome unknown, 15 chunks/493 characters unsubmitted. External disclosure permission and actual audition remain blocked.',
 'V06':'42 real downloaded cue WAVs from 43 accepted requests, 1261 submitted characters and credits_used 0. One full 90-second WAV, eight scene WAVs and 14 measured short cues exist. Long full WAV and long audio-timed subtitles are incomplete. Private pending recovery preserved outside deliverable; public provenance sanitized. Mandatory audition unavailable.',
 'V07':'Pending-approval checkpoint: all original graphical exports and actual short narrated edition verified; long voice remains incomplete. Current dependency hashes verified and all declared output bytes included. External disclosure permission and mandatory audition remain real blockers. Research paths NOT_RUN.'}
paths={'V04':'assets/video/intro_90/media_status.json','V05':'assets/video/explainer_360/media_status.json','V06':'assets/audio/media_status.json','V07':'reports/media_qa.json'}
def commit(t):
 status=rd(paths[t]);blockers=status['blockers']
 cmd=[sys.executable,str(W/'scripts/task_checkpoint.py'),'commit',t,'--check',f'run_state/checks/{t}_validation.json','--notes',notes[t]]
 for b in blockers:cmd+=['--external-blocker',b if isinstance(b,str) else b['reason']]
 p=subprocess.run(cmd,cwd=W,capture_output=True,text=True,check=True)
 (W/f'run_state/checks/{t}_commit_paused.log').write_text(p.stdout)
 subprocess.run([sys.executable,str(W/'assets/animations/enrich_media_receipt.py'),t],cwd=W,check=True)
for t in ['V04','V05','V06']:commit(t)
spec=importlib.util.spec_from_file_location('checkpoint',W/'scripts/task_checkpoint.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
verified=[]
for t in ['V01','V02','V03','V04','V05','V06']:
 r=m.verify_receipt(t);p=W/f'run_state/receipts/{t}.json'
 verified.append({'task_id':t,'status':r['status'],'receipt':{'path':str(p.relative_to(W)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size},'blockers':r.get('blockers',[])})
p=W/'reports/media_qa.json';qa=rd('reports/media_qa.json');qa['dependency_receipts_verified']=verified;p.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
check={'status':'complete_with_external_blockers','research_state':'NOT_RUN','report':{'path':'reports/media_qa.json','sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'dependency_receipts_verified':verified,'new_narrated_exports':qa['new_narrated_exports'],'audio_production_state':qa['audio_production_state'],'blockers':qa['blockers']}
(W/'run_state/checks/V07_validation.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
commit('V07');r=m.verify_receipt('V07')
print('V07 recursive verification passed:',r['status'])
for name in ['reports/media_qa.json',*[f'run_state/receipts/V{i:02d}.json' for i in range(4,8)]]:
 p=W/name;print(hashlib.sha256(p.read_bytes()).hexdigest(),name)
