"""Copy sanitized public provenance while preserving private pending-job recovery.
No network access. Private directory is explicit and never published in provenance.
"""
from pathlib import Path
import json,re,argparse,datetime
R=Path(__file__).resolve().parent;W=R.parents[2]
p=argparse.ArgumentParser();p.add_argument('--private-recovery-dir',type=Path,required=True);p.add_argument('--allow-partial',action='store_true');a=p.parse_args();S=a.private_recovery_dir.resolve();assert not S.is_relative_to(W)
paths=sorted((S/'receipts').glob('*.json'));rs=[json.loads(p.read_text()) for p in paths]
if not a.allow_partial:assert len(rs)==58 and all(r.get('status')=='downloaded' for r in rs)
secret_keys={'uuid','job_id','result_url','download_url','url','authorization','set-cookie','cookie','x-api-key'}
removed=[]
def clean(v):
 if isinstance(v,dict):
  out={}
  for k,x in v.items():
   if k.lower() in secret_keys:removed.append(k);continue
   if k=='response_headers':out[k]={h:y for h,y in x.items() if h.lower() in {'content-type','date','x-ratelimit-limit','x-ratelimit-remaining','x-ratelimit-reset'}}
   else:out[k]=clean(x)
  return out
 if isinstance(v,list):return [clean(x) for x in v]
 return v
(R/'receipts').mkdir(exist_ok=True)
for p,r in zip(paths,rs):(R/'receipts'/p.name).write_text(json.dumps(clean(r),ensure_ascii=False,indent=2)+'\n')
p=S/'poll_history.jsonl';rows=[clean(json.loads(x)) for x in p.read_text().splitlines() if x];(R/'poll_history.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n')
s=(S/'production.log').read_text() if (S/'production.log').exists() else ''
s=re.sub(r'\b[0-9a-f]{32}\b','[private job reference removed]',s);s=re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b','[private job reference removed]',s);s=re.sub(r'https://(?:cdn|api)\.tts\.ai/[^\s\"\']+', '[temporary provider URL removed]',s)
(R/'production.log').write_text(s or 'Production progress is preserved in sanitized receipts.\n')
complete=len(rs)==58 and all(r['status']=='downloaded' for r in rs)
report={'status':'sanitized' if complete else 'sanitized_partial','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'transient_result_urls_removed':True,'raw_job_capability_ids_removed':True,'sensitive_header_fields_removed':True,'private_recovery_state_preserved':True,'accepted_records':len(rs),'downloaded':sum(r['status']=='downloaded' for r in rs),'pending':sum(r['status']!='downloaded' for r in rs),'retained':['exact public/synthetic text','provider/model/voice/settings','status and credit counters','license restriction','actual WAV SHA256'],'removed_field_count':len(removed)}
(R/'sanitization.json').write_text(json.dumps(report,indent=2)+'\n')
for p in [*(R/'receipts').glob('*.json'),R/'poll_history.jsonl',R/'production.log']:
 s=p.read_text();assert 'cdn.tts.ai/' not in s and not re.search(r'\b[0-9a-f]{32}\b',s),p
print(json.dumps({'status':report['status'],'accepted':len(rs),'downloaded':report['downloaded'],'pending':report['pending'],'private_state_preserved':True}))
