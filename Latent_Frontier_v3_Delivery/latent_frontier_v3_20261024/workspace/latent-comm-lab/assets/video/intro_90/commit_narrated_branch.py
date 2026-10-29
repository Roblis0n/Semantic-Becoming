"""Commit truthful V04–V07 narrated media receipts after current final QA.
Never edits shared ledger; user-waived audition remains explicitly not performed.
"""
from pathlib import Path
import json,hashlib,subprocess,sys,importlib.util
W=Path(__file__).resolve().parents[3];sys.dont_write_bytecode=True
block='Mandatory actual audition and pronunciation/sound-quality review remain unperformed because this runtime does not support audio input. Actual WAVs, narrated MP4s, measured cue-boundary subtitles, objective audio measurements and visual checks are complete; these do not substitute for listening.'
notes={
'V04':'Actual 90-second personal/noncommercial narrated H.264/AAC edition, PCM WAV, measured 14-cue subtitles and editable MLT/timeline. Full A/V decode and every cue-midpoint frame checked. Silent history preserved. Actual audition USER_WAIVED_NOT_PERFORMED under20261027scope change.',
'V05':'Actual 360-second personal/noncommercial narrated H.264/AAC edition, PCM WAV, measured 44-cue subtitles and editable MLT/timeline. Full A/V decode and every cue-midpoint frame checked. Silent history preserved. Actual audition USER_WAIVED_NOT_PERFORMED under20261027scope change.',
'V06':'58 unique TTS.ai MeloTTS/ZH cue WAVs cover1754unique source characters;60accepted submissions/1811characters include two explicitly authorized replacements with oldUNKNOWNhistories retained;credits_used total0. Two full WAVs, 17 scene WAVs, precise PCM cue-boundary SRT/VTT and sanitized provenance exist. Loudness, clipping and silence measured. Audio input unsupported: no actual listening, pronunciation or word-level alignment claim.',
'V07':'Current dependency hashes verified. All original graphical media plus actual 90/360-second narrated editions and exact cue-boundary subtitles exist. Generated speech/containing videos are personal/noncommercial only; independent sources/PPT/SVG do not automatically inherit that restriction. Actual audition USER_WAIVED_NOT_PERFORMED under20261027scope change. All research paths NOT_RUN.'}
def commit(t):
 p=subprocess.run([sys.executable,str(W/'scripts/task_checkpoint.py'),'commit',t,'--check',f'run_state/checks/{t}_validation.json','--notes',notes[t]],cwd=W,capture_output=True,text=True,check=True)
 (W/f'run_state/checks/{t}_commit_narrated.log').write_text(p.stdout)
 subprocess.run([sys.executable,str(W/'assets/animations/enrich_media_receipt.py'),t],cwd=W,check=True)
 rp=W/f'run_state/receipts/{t}.json'; rr=json.loads(rp.read_text());rr.update(auditory_review='USER_WAIVED_NOT_PERFORMED',acceptance_scope_change='release/authorization_updates/20261027_AUDITION_SCOPE_CHANGE.json');rp.write_text(json.dumps(rr,ensure_ascii=False,indent=2)+'\n')
for t in ['V04','V05','V06']:commit(t)
spec=importlib.util.spec_from_file_location('media_checkpoint',W/'scripts/task_checkpoint.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
verified=[]
for t in ['V01','V02','V03','V04','V05','V06']:
 r=m.verify_receipt(t);p=W/f'run_state/receipts/{t}.json';verified.append({'task_id':t,'status':r['status'],'receipt':{'path':str(p.relative_to(W)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size},'blockers':r.get('blockers',[])})
p=W/'reports/media_qa.json';qa=json.loads(p.read_text());qa['dependency_receipts_verified']=verified;p.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
v={'status':'done','research_state':'NOT_RUN','report':{'path':'reports/media_qa.json','sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'dependency_receipts_verified':verified,'new_narrated_exports':qa['new_narrated_exports'],'blockers':qa['blockers'],'auditory_review':'USER_WAIVED_NOT_PERFORMED','acceptance_scope_change':'release/authorization_updates/20261027_AUDITION_SCOPE_CHANGE.json'}
(W/'run_state/checks/V07_validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');commit('V07');r=m.verify_receipt('V07');print('V07 recursive verification passed:',r['status'])
