"""Q01 reproducible source-only inventory: never imports research implementation.

This is a structural gate, not a proof of numerical correctness. Exact finite
checks and scoped human-agent source reviews are separately hash-bound evidence.
"""
from __future__ import annotations
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import task_checkpoint as checkpoint

W=Path(__file__).resolve().parents[1]
RESEARCH_LIBRARIES={'torch','transformers','tensorflow','jax','flax','safetensors','openai','anthropic'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def name(node):return node.id if isinstance(node,ast.Name) else node.attr if isinstance(node,ast.Attribute) else ''
def live_body(node):
    return [s for s in node.body if not(isinstance(s,ast.Expr) and isinstance(s.value,ast.Constant) and isinstance(s.value.value,str))]
def finite_float(text):
    value=float(text)
    if not math.isfinite(value):raise ValueError('nonfinite JSON number')
    return value

def audit():
    files=[];functions=[];protocols=[];errors=[];guarded=[];counts={}
    for base in ('src','tests','configs','specs','scripts'):
        for path in sorted((W/base).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix not in {'.py','.json'}:continue
            rel=path.relative_to(W).as_posix();files.append({'path':rel,'sha256':sha(path),'bytes':path.stat().st_size})
            if path.suffix=='.json':
                try:json.loads(path.read_text(encoding='utf-8'),parse_float=finite_float,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
                except (ValueError,UnicodeError) as exc:errors.append({'path':rel,'error':'invalid finite JSON: '+str(exc)})
                continue
            try:tree=ast.parse(path.read_text(encoding='utf-8'))
            except SyntaxError as exc:errors.append({'path':rel,'error':str(exc)});continue
            if base!='src':continue
            parents={child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
            for node in ast.walk(tree):
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    body=live_body(node);parent=parents.get(node)
                    is_protocol=isinstance(parent,ast.ClassDef) and any(name(b)=='Protocol' for b in parent.bases)
                    row={'path':rel,'name':node.name,'line':node.lineno,'statements':len(body),'protocol':is_protocol}
                    functions.append(row)
                    empty=len(body)==1 and (isinstance(body[0],ast.Pass) or isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and body[0].value.value is Ellipsis)
                    if empty:
                        if is_protocol:protocols.append(row)
                        else:errors.append(dict(row,error='empty concrete method'))
                    if len(body)==1 and isinstance(body[0],ast.Return) and (body[0].value is None or isinstance(body[0].value,ast.Constant)):
                        errors.append(dict(row,error='constant-only concrete method requires review'))
                    if any(isinstance(s,ast.Raise) and 'NotImplemented' in ast.unparse(s) for s in body):errors.append(dict(row,error='unimplemented concrete method'))
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    imports=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
                    if not any(n.split('.')[0] in RESEARCH_LIBRARIES for n in imports):continue
                    current=parents.get(node);ancestors=[]
                    while current is not None:
                        if isinstance(current,(ast.FunctionDef,ast.AsyncFunctionDef)):ancestors.append(current)
                        current=parents.get(current)
                    gates=[s for f in ancestors for s in f.body if isinstance(s,ast.Expr) and isinstance(s.value,ast.Call) and name(s.value.func)=='require_research_action' and s.lineno<node.lineno]
                    row={'path':rel,'line':node.lineno,'imports':imports,'enclosing_function':ancestors[0].name if ancestors else None,'prior_unconditional_gate_lines':[s.lineno for s in gates]}
                    guarded.append(row)
                    if not gates:errors.append(dict(row,error='research import lacks preceding unconditional enclosing policy gate'))
    mechanisms=[]
    for number in range(1,49):
        tid=f'M{number:02d}';receipt=checkpoint.verify_receipt(tid)
        source=[r for r in receipt['outputs'] if r['path'].startswith('src/')]
        tests=[r for r in receipt['outputs'] if r['path'].startswith('tests/')]
        mechanisms.append({'mechanism':f'H{number:02d}','task':tid,'source_files':len(source),'tests_files':len(tests),'receipt_sha256':sha(W/checkpoint.TASKS[tid]['receipt']),'checks':receipt['checks']})
        if not source or not tests:errors.append({'task':tid,'error':'missing concrete source/test ownership'})
    dependencies=[];missing=[]
    for tid in checkpoint.dependencies_for('Q01'):
        if not (W/checkpoint.TASKS[tid]['receipt']).exists():missing.append(tid);continue
        try:
            r=checkpoint.verify_receipt(tid)
            dependencies.append({'task':tid,'status':r['status'],'receipt_sha256':sha(W/checkpoint.TASKS[tid]['receipt']),'output_count':len(r['outputs']),'checks':r.get('checks',[])})
        except (ValueError,OSError,KeyError) as exc:errors.append({'task':tid,'error':str(exc)})
    counts={'python_files':sum(r['path'].endswith('.py') for r in files),'json_files':sum(r['path'].endswith('.json') for r in files),'source_functions':len(functions),'protocol_only_methods':len(protocols),'guarded_research_import_statements':len(guarded),'mechanisms':len(mechanisms),'q01_dependencies_current':len(dependencies)}
    return {'schema_version':1,'kind':'source_only_structural_audit','research_state':'NOT_RUN','research_entry_invocations_in_this_audit':0,'neural_imports_in_this_audit':0,'counts':counts,'errors':errors,'pending_dependencies':missing,'source_files':files,'function_inventory':functions,'protocol_exemptions':protocols,'research_import_gate_inventory':guarded,'mechanisms':mechanisms,'dependencies':dependencies,'limits':['AST structural checks do not prove execution correctness or differentiability.','Guard ordering is checked lexically; this does not claim an OS sandbox.','Finite and independent review evidence is separately cited; historical failing/denied attempts are preserved, not credited as passes.']}

if __name__=='__main__':
    result=audit();out=W/'run_state/checks/Q01_source_contract_inventory.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'report':str(out.relative_to(W)),'counts':result['counts'],'errors':result['errors'],'pending_dependencies':result['pending_dependencies']},ensure_ascii=False,indent=2))
    raise SystemExit(bool(result['errors']))
