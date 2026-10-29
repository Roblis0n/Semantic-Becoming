"""Actual D01 standard-library static checks. Does not import research packages."""
from pathlib import Path
import datetime, hashlib, json, re, subprocess, sys

WORK=Path(__file__).resolve().parents[2]
PLAN=WORK.parents[1]
CHECK=WORK/'run_state/checks'
results=[]

def check(name, condition, detail):
    results.append({'name':name,'passed':bool(condition),'detail':detail})

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

ledger=read(WORK/'specs/novelty_ledger.json')
registry=read(PLAN/'specs/hypotheses.json')
mechanisms=ledger['mechanisms']; sources=ledger['sources']
source_map={s['id']:s for s in sources}
expected={x['id'] for x in registry}
check('all_48_mechanisms',len(mechanisms)==48 and {m['id'] for m in mechanisms}==expected,'Exact registry coverage, not example-only coverage.')
check('unique_mechanism_ids',len({m['id'] for m in mechanisms})==len(mechanisms),'No duplicate mechanism hides missing coverage.')
check('all_43_supplied_source_records_retained',sum(s['origin'].startswith('supplied') for s in sources)==43,'25 v3 + 18 inherited records retained.')
check('14_targeted_source_additions',sum(s['origin']=='newly_found_D01' for s in sources)==14,'Includes optional N07 explicitly excluded from evidence.')
check('57_unique_source_ids',len(source_map)==57,'Aliases retain distinct supplied IDs with canonical IDs.')
check('all_43_supplied_sources_rechecked',all(s['source_status'].startswith('PRIMARY_CHECKED') for s in sources if s['origin'].startswith('supplied')),'Stable docs target independently checked after redirect.')
required=['object_type','operation','invariant','shared_primitive','candidate_difference','separating_case','unproven_bridge','aggressive_extension']
check('all_mechanisms_have_specific_comparison',all(all(isinstance(m[k],str) and len(m[k])>=8 for k in required) for m in mechanisms),'Object, operation, invariant, shared primitive, candidate delta, counterexample, bridge, extension.')
check('distinct_case_per_mechanism',len({m['separating_case'] for m in mechanisms})==48,'No generic duplicated counterexample.')
check('at_least_two_checked_neighbors_per_mechanism',all(len(m['nearest_sources'])>=2 and all(x['status'].startswith('PRIMARY_CHECKED') and source_map[x['id']]['cite_allowed'] for x in m['nearest_sources']) for m in mechanisms),'Every mechanism has multiple actually checked primary neighbors.')
check('supplied_refs_resolve',all(all(r in source_map for r in m['supplied_source_refs']) for m in mechanisms),'Original references remain traceable, including inherited aliases.')
check('canonical_refs_resolve',all(s['canonical_id'] in source_map for s in sources),'All aliases target a real source.')
check('canonical_citation_keys_match',all(s['citation_key']==source_map[s['canonical_id']]['citation_key'] for s in sources),'Duplicate source identities share citation keys.')
check('source_scopes_nonempty',all(s.get('supported_scope') and s.get('unsupported_scope') for s in sources),'All sources have bounded relevance and non-validation caveat.')
check('priority_not_claimed',all(m['global_first_claim'] is False and m['novelty_status']=='proposal_not_priority_verified' for m in mechanisms),'No assertion of global first priority.')
check('aggressive_extensions_preserved',all(m['innovation_retained'] and m['aggressive_extension'] for m in mechanisms),'No mechanism cancelled for absent experiment.')
check('research_not_run',ledger['research_state']=='NOT_RUN' and ledger['research_execution_count']==0 and ledger['model_loading_or_initialization_count']==0 and all(m['research_state']=='NOT_RUN' for m in mechanisms),'Static bibliography/claim review only.')
check('counterexamples_not_misreported_as_executed',all(m['separating_case_status']=='specified_not_executed_in_D01' for m in mechanisms),'Design cases are not model results.')
arxiv=[s for s in sources if '/abs/' in s['canonical_url']]
check('arxiv_first_dates_and_versions',all(re.fullmatch(r'\d{4}-\d\d-\d\d',s['first_arxiv_submission'] or '') and re.fullmatch(r'v\d+',s['current_version'] or '') for s in arxiv),'Visible arXiv versions and submission dates retained.')
check('no_future_or_reverse_arxiv_dates',all(s['first_arxiv_submission']<=ledger['as_of_utc'] and (s['latest_revision'] is None or s['first_arxiv_submission']<=s['latest_revision']<=ledger['as_of_utc']) for s in arxiv),'Chronology checked against 2026-10-24; first and revised dates separate.')
recent=['S02','S03','S08','S13','inherited:R06','inherited:R13','inherited:R14']
check('recent_2026_identities_checked',all(source_map[k]['source_status'].startswith('PRIMARY_CHECKED') and source_map[k]['snapshot_ids'] for k in recent),'All supplied recent 2026 research identities have direct primary observations.')
snapshots={s['capture_id'] for s in ledger['source_snapshot_index']}
check('all_source_snapshots_resolve',all(s['snapshot_ids'] and all(i in snapshots for i in s['snapshot_ids']) for s in sources),'Metadata observation index, not unclaimed full-paper snapshots.')
check('snapshot_hashes_valid',all(hashlib.sha256(json.dumps({k:v for k,v in s.items() if k!='metadata_sha256'},sort_keys=True,ensure_ascii=False).encode()).hexdigest()==s['metadata_sha256'] for s in ledger['source_snapshot_index']),'Hashes bind exact metadata records.')
check('optional_fetch_failure_scoped',source_map['N07']['cite_allowed'] is False and source_map['N07']['source_status']=='PRIMARY_SEARCH_ONLY_DIRECT_FETCH_FAILED' and all(x['id']!='N07' for m in mechanisms for x in m['nearest_sources']),'Direct DOI 403 not represented as a successful full-text read.')
check('S15_title_corrected','Verified Functional Synthesis' in source_map['S15']['observed_title'] and 'N14' in source_map['S15']['identity_note'],'Supplied lecture label not silently reused.')
check('H39_has_real_predecessor','N01' in [x['id'] for x in next(m for m in mechanisms if m['id']=='H39')['nearest_sources']],'Fills the empty supplied source list.')
bib=(WORK/'paper/references.bib').read_text()
keys=re.findall(r'^@\w+\{([^,]+),',bib,re.M)
expected_keys={s['citation_key'] for s in sources if s['cite_allowed']}
check('46_unique_bib_entries',len(keys)==46 and len(set(keys))==46 and set(keys)==expected_keys,'Canonical checked source identities only.')
balance=0; bad=False
for i,c in enumerate(bib):
    if i and bib[i-1]=='\\':continue
    balance+=(c=='{')-(c=='}')
    bad|=balance<0
check('bib_brace_balance',balance==0 and not bad,'Balanced BibTeX field and entry delimiters.')
entries=re.split(r'(?=^@\w+\{)',bib,flags=re.M)[1:]
check('bib_required_fields',all(all(re.search(r'^  '+f+r' = \{.+\}',e,re.M) for f in ['title','author','url','urldate','note']) for e in entries),'Every bibliography entry has author/title/location/retrieval/scope metadata.')
check('no_N07_bib_citation','SBV3_N07' not in bib,'Access-limited optional lead not promoted to usable bibliography.')
doc=(WORK/'docs/related_work.md').read_text()
check('related_work_has_48_sections',len(re.findall(r'^### H\d{2} ·',doc,re.M))==48,'Every mechanism appears in the human-readable deliverable.')
check('related_work_source_links',all(s['canonical_url'] in doc for s in sources if s['canonical_id']==s['id'] and s['cite_allowed']),'Direct verified source URLs, not search-result links.')
inputs=read(CHECK/'D01_inputs.json')['inputs'];changed=[x['path'] for x in inputs if sha(PLAN/x['path'])!=x['sha256']]
check('all_60_input_hashes_unchanged',len(inputs)==60 and not changed,{'changed':changed})
dep=subprocess.run([sys.executable,str(WORK/'scripts/task_checkpoint.py'),'verify','A01'],text=True,capture_output=True)
check('A01_receipt_reverified',dep.returncode==0,dep.stderr or 'Verified latest A01 and recursive dependencies.')
if dep.returncode==0:(CHECK/'D01_dependency_A01.json').write_text(dep.stdout)
artifacts=['docs/related_work.md','specs/novelty_ledger.json','paper/references.bib']
check('three_declared_outputs_nonempty',all((WORK/p).is_file() and (WORK/p).stat().st_size>0 for p in artifacts),'D01 does not claim other tasks or media outputs.')
summary={'task_id':'D01','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'check_kind':'stdlib_static_provenance_and_document_checks','checks':results,
 'passed':sum(x['passed'] for x in results),'failed':sum(not x['passed'] for x in results),
 'model_or_neural_imports':0,'model_execution':0,'numeric_fixture_cases':0,
 'research_state':'NOT_RUN','outputs':[{'path':p,'sha256':sha(WORK/p),'bytes':(WORK/p).stat().st_size} for p in artifacts]}
dump=lambda p,j:p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
dump(CHECK/'D01_validation.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
sys.exit(bool(summary['failed']))
