"""Create a byte-consistent resumable source snapshot; no external action."""
from pathlib import Path
import hashlib,json,zipfile,datetime
W=Path(__file__).resolve().parents[1]
out=W/'checkpoints/latent_frontier_v3_execution_checkpoint.zip';out.parent.mkdir(exist_ok=True)
state=json.loads((W/'run_state/ledger.json').read_text())
private_transient_prefixes=('assets/audio/tts_ai/receipts/','assets/audio/tts_ai/poll_history.jsonl','assets/audio/tts_ai/production.log')
files=[p for p in W.rglob('*') if p.is_file() and 'checkpoints' not in p.relative_to(W).parts and '__pycache__' not in p.parts and p.suffix!='.pyc' and not p.relative_to(W).as_posix().startswith(private_transient_prefixes)]
contents={p.relative_to(W).as_posix():p.read_bytes() for p in sorted(files)}
manifest={'project':'latent-comm-lab','checkpoint_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completed_tasks':state['completed_tasks'],'research_state':'NOT_RUN','active_source_may_be_partial':True,'source_library_ids':['libfile_fa620cd9cff0819194a6265758545066','libfile_2eaa97fdc5dc8191823af3486a892a82','libfile_0ba2c9e7773c819193aeaa5b11a80961','libfile_fb6b95544f708191841d47feeadd2c54'],'files':[{'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for name,raw in contents.items()]}
manifest['excluded_private_transient_prefixes']=list(private_transient_prefixes)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for name,raw in contents.items():z.writestr('latent-comm-lab/'+name,raw)
 z.writestr('CHECKPOINT_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(out) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 for row in manifest['files']:assert hashlib.sha256(z.read('latent-comm-lab/'+row['path'])).hexdigest()==row['sha256']
print(json.dumps({'checkpoint':str(out),'completed_tasks':state['completed_tasks'],'files':len(contents),'bytes':out.stat().st_size,'all_archive_hashes_verified':True}))
