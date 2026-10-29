"""Write a postbuild verification sidecar; never mutate the sealed ZIP."""
from pathlib import Path
import argparse,datetime,hashlib,json
import task_checkpoint as ck
W=ck.WORK
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--primary-library-file-id');args=parser.parse_args()
 z02=ck.verify_receipt('Z02');state={'done':[],'external_blockers':{}}
 archive=W/'release/latent-comm-lab-source-design.zip';integrity=json.loads((W/'reports/release_integrity.json').read_text());review_path=W/'release/independent_delivery_acceptance.json';review=json.loads(review_path.read_text())
 if review.get('status')!='PASS' or review.get('archive_sha256')!=sha(archive) or integrity['archive_sha256']!=sha(archive):raise ValueError('independent acceptance or archive identity is not current')
 rows=[]
 for tid in ck.TASKS:
  receipt=ck.verify_receipt(tid);rows.append({'task_id':tid,'status':receipt['status'],'receipt_sha256':sha(W/ck.TASKS[tid]['receipt']),'blockers':receipt.get('blockers',[])})
  state['done'].append(tid)
  if receipt.get('blockers'):state['external_blockers'][tid]=receipt['blockers']
 result={'schema_version':1,'project':'Latent Frontier v3 / Semantic Becoming','title':'前沿机制提案 / 无模型实测','written_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primary_archive':{'filename':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'library_file_id':args.primary_library_file_id},'research_state':'NOT_RUN','task_denominator':133,'terminal_tasks':len(rows),'done_without_external_blocker':sum(r['status']=='done' for r in rows),'complete_with_external_blockers':sum(r['status']=='complete_with_external_blockers' for r in rows),'delivery_status':'SOURCE_AND_LOCAL_ARTIFACTS_SEALED_WITH_DISCLOSED_EXTERNAL_BLOCKERS' if state['external_blockers'] else 'SOURCE_AND_LOCAL_ARTIFACTS_SEALED','external_blockers':state['external_blockers'],'tasks':rows,'archive_integrity':integrity,'independent_acceptance':review,'independent_acceptance_sha256':sha(review_path),'Z02_receipt_sha256':sha(W/'run_state/receipts/Z02.json'),'media_license':'Third-party generated TTS audio and videos containing it: personal/noncommercial only. Independent source/PPT/SVG/silent visuals have separately recorded provenance. No blanket commercial-rights warranty.','auditory_review':'USER_WAIVED_NOT_PERFORMED: user removed listening acceptance condition on20261027. Actual audio input remains unsupported; objective checks are not listening.','publication':'NOT_PUBLISHED','self_reference_boundary':'This sidecar is outside the ZIP; it supplies the final ZIP hash, Z02 completion and postbuild independent acceptance. The ZIP does not purport to hash itself.'}
 out=W/'release/FINAL_DELIVERY_VERIFICATION.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');print(json.dumps({'sidecar':str(out),'sha256':sha(out),'terminal_tasks':len(rows),'external_blocker_tasks':list(state['external_blockers'])},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
