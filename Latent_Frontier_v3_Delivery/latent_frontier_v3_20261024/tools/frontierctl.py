#!/usr/bin/env python3
"""Offline plan controller. This is NOT the future scientific compiler or model runner.

Only stdlib is imported. No network, model, package installer or shell execution.
Path and policy checks reduce mistakes; they are not a hostile-code sandbox.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any

class PlanError(ValueError):
    """Invalid plan, state, policy or path."""

ALLOWED = frozenset({'public_read','workspace_read','workspace_write','static_check',
                     'stdlib_math_fixture','plan_compile','local_media_export',
                     'authorized_zero_new_cost_media'})
REQUIRED_FALSE = ('download','initialize','forward','train','benchmark','api_inference',
                  'random_tiny_model_for_tests')
STATUSES = frozenset({'pending','running','done','blocked','failed','cancelled'})


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k,v in pairs:
        if k in result:
            raise PlanError(f'duplicate JSON key: {k}')
        result[k]=v
    return result


def loads(text: str) -> Any:
    def bad_constant(s: str) -> None:
        raise PlanError(f'nonfinite JSON value: {s}')
    try:
        return json.loads(text,object_pairs_hook=_unique_pairs,parse_constant=bad_constant)
    except json.JSONDecodeError as e:
        raise PlanError(f'invalid JSON: {e}') from e


def load(path: Path) -> Any:
    return loads(path.read_text(encoding='utf-8'))


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def relative(value: str) -> PurePosixPath:
    if not isinstance(value,str) or not value or '\\' in value or '\x00' in value:
        raise PlanError(f'invalid relative path: {value!r}')
    if value.startswith(('~','/')) or re.match(r'^[A-Za-z]:',value):
        raise PlanError(f'absolute or home path is forbidden: {value}')
    parts=value.rstrip('/').split('/')
    if any(p in ('','..','.') for p in parts):
        raise PlanError(f'noncanonical or escaping path: {value}')
    return PurePosixPath(*parts)


def within(root: Path, value: str, must_exist: bool=False) -> Path:
    rel=relative(value)
    root=root.resolve()
    p=root.joinpath(*rel.parts)
    # Reject symlinks even if they currently resolve inside the root.
    cursor=root
    for part in rel.parts:
        cursor=cursor/part
        if cursor.is_symlink():
            raise PlanError(f'symlink is forbidden: {value}')
    try:
        p.resolve().relative_to(root)
    except ValueError as e:
        raise PlanError(f'path outside root: {value}') from e
    if must_exist and not p.exists():
        raise PlanError(f'missing path: {value}')
    return p


def atomic_json(path: Path, data: Any) -> None:
    """Single coordinator writes; atomic replace on the same filesystem."""
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)


def check_policy(policy: dict[str, Any]) -> None:
    if policy.get('research_state')!='not_run':
        raise PlanError('this package requires research_state=not_run')
    models=policy.get('models',{})
    for key in REQUIRED_FALSE:
        if models.get(key) is not False:
            raise PlanError(f'model action must be explicitly false: {key}')
    effects=policy.get('external_effects',{})
    if type(effects.get('new_spend')) is not int or effects['new_spend']!=0:
        raise PlanError('new_spend must be integer zero')
    for key in ('public_publish','email_or_message_send','unrelated_private_access'):
        if effects.get(key) is not False:
            raise PlanError(f'external effect must be false: {key}')
    declared=policy.get('allowed_actions',[])
    if not isinstance(declared,list) or not set(declared)<=ALLOWED:
        raise PlanError('policy contains unknown or forbidden allowed action')


def gate(policy: dict[str, Any], action: str, *, authorized: bool=False,
         zero_new_cost: bool=False) -> dict[str, Any]:
    check_policy(policy)
    if action not in ALLOWED or action not in policy['allowed_actions']:
        raise PlanError(f'action denied: {action}')
    if action in set(policy.get('denied_actions',[])):
        raise PlanError(f'action explicitly denied: {action}')
    if action=='authorized_zero_new_cost_media' and not (authorized and zero_new_cost):
        raise PlanError('media needs explicit existing authorization and zero new cost')
    return {'action':action,'allowed_by_plan':True,'executed':False,
            'not_a_platform_sandbox':True}


def graph_order(graph: dict[str, Any]) -> list[str]:
    tasks=graph.get('tasks')
    if not isinstance(tasks,list) or not tasks:
        raise PlanError('tasks must be a nonempty list')
    index={}
    for t in tasks:
        tid=t.get('id')
        if not isinstance(tid,str) or not re.fullmatch(r'[A-Z][0-9]{2}',tid):
            raise PlanError(f'invalid task id: {tid}')
        if tid in index: raise PlanError(f'duplicate task: {tid}')
        index[tid]=t
    owners: list[tuple[PurePosixPath,str]]=[]
    for tid,t in index.items():
        deps=t.get('dependencies')
        if not isinstance(deps,list) or len(deps)!=len(set(deps)):
            raise PlanError(f'invalid or duplicated dependencies: {tid}')
        for dep in deps:
            if dep not in index: raise PlanError(f'missing dependency: {tid}->{dep}')
        outputs=t.get('outputs')
        if not isinstance(outputs,list) or not outputs:
            raise PlanError(f'task has no concrete output: {tid}')
        for output in outputs:
            p=relative(output)
            for previous,owner in owners:
                if owner!=tid and (p==previous or p in previous.parents or previous in p.parents):
                    raise PlanError(f'overlapping writers: {owner}/{tid}: {previous}/{p}')
            owners.append((p,tid))
    indegree={tid:len(t['dependencies']) for tid,t in index.items()}
    children={tid:[] for tid in index}
    for tid,t in index.items():
        for dep in t['dependencies']: children[dep].append(tid)
    ready=sorted(tid for tid,d in indegree.items() if d==0)
    order=[]
    while ready:
        tid=ready.pop(0);order.append(tid)
        for child in sorted(children[tid]):
            indegree[child]-=1
            if indegree[child]==0:
                ready.append(child);ready.sort()
    if len(order)!=len(index):
        raise PlanError('dependency cycle: '+','.join(k for k,v in indegree.items() if v))
    terminal=graph.get('terminal_task')
    if terminal not in index: raise PlanError('missing terminal task')
    if 'task_count' in graph and graph['task_count']!=len(tasks):
        raise PlanError('task_count disagrees with actual graph')
    # Every task must be reachable backwards from the terminal.
    seen=set();stack=[terminal]
    while stack:
        tid=stack.pop()
        if tid in seen: continue
        seen.add(tid);stack.extend(index[tid]['dependencies'])
    if seen!=set(index):
        raise PlanError('orphan tasks outside terminal closure: '+','.join(sorted(set(index)-seen)))
    return order


def registry(path: Path) -> dict[str, dict[str, Any]]:
    records=load(path)
    if not isinstance(records,list): raise PlanError('registry must be list')
    result={}
    for record in records:
        rid=record.get('id')
        if not isinstance(rid,str) or rid in result: raise PlanError('invalid/duplicate registry ID')
        result[rid]=record
    return result


def validate(root: Path, verify_sources: bool=True) -> dict[str, Any]:
    policy=load(within(root,'specs/execution_policy.json',True));check_policy(policy)
    graph=load(within(root,'specs/task_graph.json',True));order=graph_order(graph)
    hypotheses=registry(within(root,'specs/hypotheses.json',True))
    combinations=registry(within(root,'specs/combinations.json',True))
    horizons=registry(within(root,'specs/horizons.json',True))
    sources=registry(within(root,'specs/sources.json',True))
    prompts=registry(within(root,'specs/prompt_registry.json',True))
    tids={t['id'] for t in graph['tasks']}
    for p in prompts.values(): within(root,p['path'],True)
    for group in (hypotheses,combinations,horizons):
        for rid,item in group.items():
            within(root,item['design_path'],True)
            if rid.startswith('H'):
                if 'M'+rid[1:] not in tids: raise PlanError(f'missing implementation task for {rid}')
                if item.get('research_status')!='not_run': raise PlanError('invalid scientific status')
                for ref in item.get('source_refs',[]):
                    if not ref.startswith('inherited:') and ref not in sources:
                        raise PlanError(f'unknown source: {ref}')
            elif rid not in tids: raise PlanError(f'missing task: {rid}')
            for member in item.get('mechanisms',[]):
                if member not in hypotheses: raise PlanError(f'unknown mechanism: {member}')
            if 'recipe_path' in item:
                r=load(within(root,item['recipe_path'],True))
                if r.get('id')!=rid: raise PlanError('recipe ID mismatch')
                if r.get('design_only') is not True or r.get('research_execution_authorized') is not False:
                    raise PlanError(f'unlocked recipe: {rid}')
                if set(r.get('mechanisms',[]))-hypotheses.keys():raise PlanError('recipe unknown mechanism')
    for task in graph['tasks']:
        within(root,task['task_card'],True);within(root,task['role_prompt'],True)
        for source in task['design_inputs']: within(root,source,True)
    checked=0
    if verify_sources:
        manifest=load(within(root,'specs/source_inventory.json',True))
        if digest(within(root,manifest['input_zip'],True))!=manifest['sha256']:
            raise PlanError('input zip changed')
        for item in manifest['files']:
            p=within(root,'inherited_v2/'+item['path'],True)
            if digest(p)!=item['sha256']: raise PlanError(f'inherited file changed: {item["path"]}')
            checked+=1
    return {'ok':True,'scope':'plan_structure_and_inherited_integrity_only',
            'hypotheses':len(hypotheses),'combinations':len(combinations),
            'horizons':len(horizons),'tasks':len(order),'prompts':len(prompts),
            'recipes':len(hypotheses)+len(combinations),'inherited_files_verified':checked,
            'research_models_run':0,'scientific_claims_validated':0,'task_order':order}


def compile_recipe(root: Path, recipe_id: str) -> dict[str, Any]:
    if not re.fullmatch(r'[HC][0-9]{2}',recipe_id):raise PlanError('invalid recipe ID')
    policy=load(within(root,'specs/execution_policy.json',True));gate(policy,'plan_compile')
    r=load(within(root,f'recipes/{recipe_id}.json',True))
    if r.get('id')!=recipe_id or r.get('design_only') is not True or r.get('research_execution_authorized') is not False:
        raise PlanError('recipe not design-locked')
    h=registry(within(root,'specs/hypotheses.json',True))
    members=r.get('mechanisms',[])
    if not members or any(m not in h for m in members):raise PlanError('invalid recipe members')
    return {'recipe_id':recipe_id,'plan_compilation_only':True,'research_execution':False,
            'mechanisms':[{'id':m,'design':h[m]['design_path'],'target':h[m]['target_base']} for m in members],
            'stages':r.get('stages',r.get('legacy_recipe',{}).get('pipeline_nodes',[])),
            'implementation_state':'assigned_to_dot_not_executed_by_this_tool'}


def initial_state(graph: dict[str, Any], plan_digest: str) -> dict[str, Any]:
    order=graph_order(graph)
    return {'schema':1,'plan_digest':plan_digest,'research_state':'not_run',
            'tasks':{tid:{'status':'pending','outputs':[],'checks':[]} for tid in order}}


def ready_tasks(graph: dict[str, Any], state: dict[str, Any]) -> list[str]:
    graph_order(graph)
    ts=state.get('tasks',{})
    ids={t['id'] for t in graph['tasks']}
    if set(ts)!=ids:raise PlanError('state task IDs do not match graph')
    for v in ts.values():
        if v.get('status') not in STATUSES:raise PlanError('invalid task status')
    index={t['id']:t for t in graph['tasks']}
    def satisfied(tid: str) -> bool:
        status=ts[tid]['status']
        return status=='done' or (status=='blocked' and index[tid].get('external_optional') is True)
    return sorted(t['id'] for t in graph['tasks'] if ts[t['id']]['status']=='pending'
                  and all(satisfied(dep) for dep in t['dependencies']))


def invalidate(graph: dict[str, Any], state: dict[str, Any], task_id: str) -> list[str]:
    graph_order(graph)
    if task_id not in state['tasks']:raise PlanError('unknown invalidation task')
    affected={task_id}
    changed=True
    while changed:
        changed=False
        for task in graph['tasks']:
            if task['id'] not in affected and set(task['dependencies']) & affected:
                affected.add(task['id']);changed=True
    for tid in affected:
        previous=state['tasks'][tid]
        state['tasks'][tid]={'status':'pending','outputs':[],'checks':[],
                             'invalidation_reason':f'upstream_changed:{task_id}',
                             'previous_status':previous['status']}
    return sorted(affected)


def verify_outputs(workroot: Path, task: dict[str, Any]) -> list[dict[str, str]]:
    results=[]
    for value in task['outputs']:
        p=within(workroot,value,True)
        files=sorted(p.rglob('*')) if p.is_dir() else [p]
        actual=[]
        for candidate in files:
            rel=candidate.relative_to(workroot.resolve()).as_posix()
            checked=within(workroot,rel,True)
            if checked.is_file():
                if checked.stat().st_size==0:raise PlanError(f'empty output: {rel}')
                actual.append({'path':rel,'sha256':digest(checked)})
        if not actual:raise PlanError(f'empty output directory: {value}')
        results.extend(actual)
    return results


def scan_python(path: Path) -> dict[str, Any]:
    """AST-only warning scanner; findings need review, no imports are performed."""
    try: tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    except SyntaxError as e:raise PlanError(f'syntax error: {e}') from e
    warnings=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            body=node.body
            if body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str):body=body[1:]
            if not body or all(isinstance(n,ast.Pass) or (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and n.value.value is Ellipsis) for n in body):
                warnings.append({'line':node.lineno,'kind':'empty_or_abstract_body','name':node.name})
        if isinstance(node,ast.Raise) and isinstance(node.exc,(ast.Name,ast.Call)):
            exc=node.exc.func if isinstance(node.exc,ast.Call) else node.exc
            if isinstance(exc,ast.Name) and exc.id=='NotImplementedError':
                warnings.append({'line':node.lineno,'kind':'not_implemented'})
    return {'path':str(path),'parsed':True,'executed':False,'warnings':warnings,
            'note':'Protocol abstract methods may be legitimate; warnings are not automatic verdicts.'}


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    sub=parser.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate')
    p=sub.add_parser('compile');p.add_argument('recipe_id')
    p=sub.add_parser('gate');p.add_argument('action');p.add_argument('--authorized',action='store_true');p.add_argument('--zero-new-cost',action='store_true')
    sub.add_parser('initial-state')
    p=sub.add_parser('ready');p.add_argument('state_path')
    p=sub.add_parser('scan');p.add_argument('python_path')
    args=parser.parse_args(argv)
    try:
        if args.cmd=='validate':result=validate(args.root)
        elif args.cmd=='compile':result=compile_recipe(args.root,args.recipe_id)
        elif args.cmd=='gate':result=gate(load(within(args.root,'specs/execution_policy.json',True)),args.action,authorized=args.authorized,zero_new_cost=args.zero_new_cost)
        elif args.cmd=='initial-state':
            p=within(args.root,'specs/task_graph.json',True);result=initial_state(load(p),digest(p))
        elif args.cmd=='ready':
            result={'ready':ready_tasks(load(within(args.root,'specs/task_graph.json',True)),load(within(args.root,args.state_path,True)))}
        else:result=scan_python(within(args.root,args.python_path,True))
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False));return 0
    except (PlanError,OSError,KeyError,TypeError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False),file=sys.stderr);return 2

if __name__=='__main__':
    raise SystemExit(main())
