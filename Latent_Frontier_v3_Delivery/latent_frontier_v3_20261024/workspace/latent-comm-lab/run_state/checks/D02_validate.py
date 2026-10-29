"""D02 static structure/provenance review. This is not a theorem prover or efficacy test."""
from pathlib import Path
import ast,collections,hashlib,json,re,subprocess,sys
W=Path(__file__).resolve().parents[2];P=W.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
sm=load(W/'docs/formal_notes/source_map.json');ad=load(W/'docs/formal_notes/assumption_dependencies.json');fb=load(W/'specs/future_branches.json');maths=load(W/'run_state/checks/D02_math_fixtures.json');nov=load(W/'specs/novelty_ledger.json')
checks=[]
def record(i,fn):
    try:detail=fn();checks.append({'id':i,'status':'PASS','detail':detail})
    except Exception as e:checks.append({'id':i,'status':'FAIL','error':type(e).__name__+': '+str(e)})
def research_labels():
    for v in (sm,ad,fb,maths):assert v['task_id']=='D02' and v['research_state']=='NOT_RUN'
    assert ad['empirical_results']==fb['empirical_results']==[]
    assert maths['research_execution_count']==0 and maths['neural_imports']==[]
    return {'new_empirical_claims':0,'research_state':'NOT_RUN'}
record('D02-POLICY-STATE',research_labels)
def notes():
    ps=sorted((W/'docs/formal_notes').glob('F*.md'));assert len(ps)==10
    mapping=sm['formal_note_map'];assert set(mapping)=={f'F{i:02}' for i in range(1,11)}
    assert set(x for v in mapping.values() for x in v)=={f'H{i:02}' for i in range(25,49)}
    result=[]
    for p in ps:
        s=p.read_text();fid=p.name[:3]
        assert len(s)>1000 and s.count('## ')>=4 and 'NOT_RUN' in s
        assert 'D0' in s or fid=='F10'
        assert '源码' in s or '实现' in s
        assert '证明' in s and ('反例' in s or '例：' in s)
        assert all(h in s for h in mapping[fid])
        assert 'SBV3_' in s and ('假设' in s or 'A_' in s)
        assert not re.search(r'\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b',s)
        result.append({'path':p.relative_to(W).as_posix(),'characters':len(s),'mechanisms':mapping[fid],'sha256':sha(p)})
    plan_forms=list((P/'formal').glob('F*.md'));assert len(plan_forms)==8
    return {'formal_inputs':len(plan_forms),'derivation_notes':result,'scope':'Presence/coverage and stated boundaries only. Mathematical argument quality was manually reviewed; this parser is not a formal proof assistant.'}
record('D02-FORMAL-COVERAGE',notes)
def snapshots():
    count=0;python_files=set();syms=0
    for r in sm['input_snapshots']:
        path=({'PLAN_ROOT':P,'WORK_ROOT':W}[r['root']])/r['path'];assert path.is_file(),str(path)
        assert sha(path)==r['sha256'],r['path'];count+=1
    ids=set()
    for m in sm['mechanisms']:
        assert m['mechanism_id'] not in ids;ids.add(m['mechanism_id'])
        assert sha(P/m['design_input'])==m['design_sha256']
        for r in m['source_files']:
            p=W/r['path'];assert sha(p)==r['sha256'],r['path'];count+=1
            if p.suffix=='.py':
                tree=ast.parse(p.read_text());python_files.add(r['path'])
                symbols=[{'name':n.name,'line':n.lineno,'end_line':n.end_lineno,'kind':type(n).__name__} for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
                assert symbols==r['symbols'];syms+=len(symbols)
            elif p.suffix=='.json':load(p)
        assert any(r['path'].endswith('/reference.py') for r in m['source_files'])
        assert all((W/p).is_file() for p in m['formal_notes'])
    assert ids=={f'H{i:02}' for i in range(25,49)}
    return {'hashes_rechecked':count,'mechanisms':len(ids),'source_AST_files':len(python_files),'top_level_symbols':syms,'imports_executed_for_AST':0}
record('D02-SOURCE-SNAPSHOTS',snapshots)
def citations():
    sources={s['id']:s for s in nov['sources']};cites={s['citation_key'] for s in nov['sources'] if s['source_status']=='PRIMARY_CHECKED' and s['cite_allowed']}
    bib=(W/'paper/references.bib').read_text();keys=set(re.findall(r'@\w+\{([^,]+),',bib));used=set()
    for p in list((W/'docs/formal_notes').glob('*.md'))+[W/'docs/frontier_afterword.md']:
        found=set(re.findall(r'SBV3_[SN]\d+',p.read_text()));assert found<=cites and found<=keys,(str(p),found-cites,found-keys);used|=found
    for s in sm['citations']:assert s==sources[s['id']]
    for m in sm['mechanisms']:
        original=next(n for n in nov['mechanisms'] if n['id']==m['mechanism_id'])
        assert m['nearest_sources']==original['nearest_sources']
    for b in fb['branches']:
        for sid in b['nearest_source_ids']:assert sources[sid]['source_status']=='PRIMARY_CHECKED' and sources[sid]['cite_allowed']
    assert 'SBV3_N07' not in used
    return {'verified_citation_keys_used':sorted(used),'exact_D01_source_records':len(sm['citations']),'scope':'Identity/metadata and D01 recorded visible-content scope, not exhaustive/full-paper priority review.'}
record('D02-CITATIONS',citations)
def branch_check(b):
    assert b['claim_class']=='V' and b['research_state']=='NOT_RUN' and b['implementation_status']=='future_proposal_not_implemented'
    for k in ('id','parent_horizon','title','new_object','released_assumption','preserved_invariant','separating_witness','unproved_bridge','current_finite_anchor','admission_policy','check_scope'):assert isinstance(b[k],str) and b[k].strip(),k
    for k in ('mainlines','p24_questions','algorithm_steps','additional_assumptions','nearest_source_ids','mechanism_ids','requirement_ids'):assert isinstance(b[k],list) and b[k] and all(isinstance(x,str) and x for x in b[k]),k
    assert len(b['algorithm_steps'])>=4
    h=next(x for x in load(P/'specs/horizons.json') if x['id']==b['parent_horizon'])
    assert b['current_finite_anchor']==h['target_path'] and b['mechanism_ids']==h['mechanisms']
    assert b['design_check_id']=='D02-BRANCH-'+b['id']
    assert b['id'] in (W/'docs/frontier_afterword.md').read_text()
    return {'new_object':b['new_object'],'released_assumption':b['released_assumption'],'separating_witness':b['separating_witness'],'nearest_source_ids':b['nearest_source_ids'],'scope':'Field/reference integrity with human-authored distinguishing witness. No branch implementation or objective originality score.'}
for b in fb['branches']:record(b['design_check_id'],lambda b=b:branch_check(b))
def branches():
    bs=fb['branches'];assert len(bs)==38 and len({b['id'] for b in bs})==38
    assert len({b['new_object'] for b in bs})==38 and len({b['released_assumption'] for b in bs})==38
    assert len({tuple(b['algorithm_steps']) for b in bs})==38
    h=collections.Counter(b['parent_horizon'] for b in bs);assert set(h)=={f'X{i:02}' for i in range(1,13)} and min(h.values())>=3
    main=collections.Counter(x for b in bs for x in b['mainlines']);axes=collections.Counter(x for b in bs for x in b['p24_questions'])
    assert set(main)==set(fb['mainline_definitions']) and all(main[x]>=3 for x in main)
    assert set(axes)==set(fb['p24_questions']) and all(axes[x]>=3 for x in axes)
    assert [b['id'] for b in bs if 'BIFURCATION' in b['mainlines']]==['X11-B1','X11-B4','X11-B5']
    return {'branches':len(bs),'horizons':dict(h),'mainlines_and_retained_sides':dict(main),'P24_axes':dict(axes),'bifurcation_objects':['pitchfork structure','Hopf stable periodic orbit','fold and hysteretic branch history'],'comparison_scope':'Distinct specified objects/operations/assumptions, not empirical novelty or theorem independence.'}
record('D02-BRANCH-COVERAGE',branches)
def dependencies():
    assumptions={a['id'] for a in ad['assumptions']};claims={c['id'] for c in ad['claims']};assert len(assumptions)==len(ad['assumptions']) and len(claims)==len(ad['claims'])
    external=set(ad['external_legacy_nodes']);counts=collections.Counter(c['claim_class'] for c in ad['claims']);assert counts=={'D':10,'H':24,'V':38}
    for c in ad['claims']:
        assert c['research_state']=='NOT_RUN'
        assert set(c.get('depends_on',[])) <= assumptions|claims|external,(c['id'],set(c.get('depends_on',[]))-assumptions-claims-external)
        if c['claim_class']=='D':assert (W/c['proof_file']).is_file() and c['exact_scope']
        else:assert c['unproved_bridge']
    # All direct dependencies are checked for cycles, not only existence.
    lookup={c['id']:c for c in ad['claims']}
    def visit(k,path):
        assert k not in path,('cycle',path,k)
        for t in lookup[k].get('depends_on',[]):
            if t in lookup:visit(t,path+(k,))
    for k in lookup:visit(k,())
    return {'claim_classes':dict(counts),'explicit_assumptions':len(assumptions),'external_legacy_nodes':sorted(external),'scope':'Dependency graph structure, not empirical confirmation of assumptions.'}
record('D02-ASSUMPTION-GRAPH',dependencies)
def fixtures():
    assert maths['passed']==24 and maths['failed']==0
    assert maths['source_runner_sha256']==sha(W/'run_state/checks/D02_finite_checks.py')
    for r in maths['checks']:
        assert r['status']=='PASS'
        l=r['declared_limits'];assert l['max_dimension']<=64 and l['max_steps']<=128 and l['max_cases']<=64
        assert r['consumed_steps_including_precharged_solver_bounds']<=l['max_steps'] and r['consumed_cases']<=l['max_cases'] and r['consumed_branches']<=l['max_branches']
    assert set(r['formal_note'] for r in maths['checks'])=={f'F{i:02}' for i in range(1,11)}|{'policy'}
    text=(W/'run_state/checks/D02_finite_checks.py').read_text();tree=ast.parse(text)
    assert 'with aggregate_budget(limit)' in text and 'sys.meta_path.insert(0,NoResearchImports())' in text
    assert 'max_sweeps=min(4,max_sweeps)' in text
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):assert all(x.name.split('.')[0] not in {'torch','transformers','jax','tensorflow'} for x in n.names)
        if isinstance(n,ast.ImportFrom):assert (n.module or '').split('.')[0] not in {'torch','transformers','jax','tensorflow'}
    return {'actual_passed':maths['passed'],'max_declared_dimension':max(r['declared_limits']['max_dimension'] for r in maths['checks']),'max_consumed_steps':max(r['consumed_steps_including_precharged_solver_bounds'] for r in maths['checks']),'max_consumed_cases':max(r['consumed_cases'] for r in maths['checks']),'scope':'Source-bound finite algebraic witnesses and counterexamples. Not neural training, eval, benchmark, or scientific efficacy.'}
record('D02-FINITE-FIXTURES',fixtures)
def task_dependencies():
    results=[]
    for dep in ['A01']+[f'M{i:02}' for i in range(25,49)]+['D01']:
        r=subprocess.run([sys.executable,'scripts/task_checkpoint.py','verify',dep],cwd=W,text=True,capture_output=True)
        results.append({'dependency':dep,'returncode':r.returncode,'receipt_verified':r.returncode==0,'error':r.stderr[-2000:] if r.returncode else None,'receipt_sha256':sha(W/f'run_state/receipts/{dep}.json')})
    (W/'run_state/checks/D02_dependencies_final.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    assert all(r['returncode']==0 for r in results),[r for r in results if r['returncode']]
    return {'verified_dependency_receipts':len(results),'formal_task_dependencies':25,'additional_source_dependency':'D01'}
record('D02-DEPENDENCY-REVERIFY',task_dependencies)
for p in sorted((W/'run_state/checks').glob('D02*.py')):ast.parse(p.read_text())
result={'task_id':'D02','research_state':'NOT_RUN','validation_scope':'Static/schema/source identity checks and comparison with already executed finite proof fixtures. Neither proof-assistant verification nor efficacy/novelty validation.','checks':checks,'passed':sum(r['status']=='PASS' for r in checks),'failed':sum(r['status']=='FAIL' for r in checks),'provenance':{'validator_sha256':sha(Path(__file__)),'math_fixtures_sha256':sha(W/'run_state/checks/D02_math_fixtures.json'),'initial_fixture_run':'D02_finite_checks_initial.txt retained: two harness field-name mistakes, corrected without source changes.'}}
(W/'run_state/checks/D02_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(bool(result['failed']))
