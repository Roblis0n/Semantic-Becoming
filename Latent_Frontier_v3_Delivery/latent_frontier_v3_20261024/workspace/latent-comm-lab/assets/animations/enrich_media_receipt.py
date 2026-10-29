"""Add media-specific requested/export/open/timing fields to this owner's V receipt.
Run only after task_checkpoint.py commit; never alters ledger or task terminal state.
"""
from pathlib import Path
import json,sys,os,tempfile
W=Path(__file__).resolve().parents[2]
task=sys.argv[1];paths={'V01':'assets/figures/media_status.json','V02':'assets/slides/media_status.json','V03':'assets/animations/media_status.json','V04':'assets/video/intro_90/media_status.json','V05':'assets/video/explainer_360/media_status.json','V06':'assets/audio/media_status.json','V07':'reports/media_qa.json'}
assert task in paths
p=W/f'run_state/receipts/{task}.json';r=json.loads(p.read_text());s=json.loads((W/paths[task]).read_text());assert r['task_id']==task and r['status']==s['status']
for k in ['requested','source_created','export_created','opened_checked','timing_verified','timing_applicable','timing_scope','opened_scope','export_edition','narrated_final_created','audio_timing_verified','audio_listened']:
 if k in s:r[k]=s[k]
r['media_status_source']=paths[task]
fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.'+task)
with os.fdopen(fd,'w') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
os.replace(tmp,p)
print(task,r['status'],'media fields recorded')
