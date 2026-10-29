"""Deterministic per-task authoring receipts; stdlib-only and no research execution.

Individual workers own only their task receipt. The coordinator alone calls sync,
which rebuilds the shared ledger from verified, content-addressed receipts.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile

WORK = Path(__file__).resolve().parents[1]
BINDING = json.loads((WORK / 'run_state/workspace_binding.json').read_text(encoding='utf-8'))
def locate_plan(work: Path, binding: dict) -> Path:
    """Prefer the shipped relative layout, never a stale absolute source tree.

    The historical binding is immutable evidence. Relocation is permitted only
    when the authoritative task-graph bytes match that binding; each receipt
    still hashes every prescribed input before accepting any completion.
    """
    candidates = (work.parents[1], Path(binding['PLAN_ROOT']))
    for candidate in candidates:
        graph = candidate / 'specs/task_graph.json'
        if graph.is_file():
            if hashlib.sha256(graph.read_bytes()).hexdigest() != binding['task_graph_sha256']:
                raise ValueError('candidate plan has a different task-graph identity')
            return candidate
    raise ValueError('authoritative plan not found with the bound task-graph identity')

PLAN = locate_plan(WORK, BINDING)
GRAPH = json.loads((PLAN / 'specs/task_graph.json').read_text(encoding='utf-8'))
TASKS = {task['id']: task for task in GRAPH['tasks']}
RUNTIME_DEPENDENCY_PATH=WORK/'run_state/implementation_dependencies.json'
RUNTIME_DEPENDENCIES=json.loads(RUNTIME_DEPENDENCY_PATH.read_text(encoding='utf-8')) if RUNTIME_DEPENDENCY_PATH.exists() else {}
def dependencies_for(task_id):
    extra=RUNTIME_DEPENDENCIES.get(task_id,[])
    if any(dep not in TASKS or dep==task_id for dep in extra):raise ValueError('invalid implementation dependency')
    return tuple(dict.fromkeys(TASKS[task_id]['dependencies']+extra))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

def output_files(task_id: str) -> list[dict[str, object]]:
    paths: dict[str, dict[str, object]] = {}
    for declared in TASKS[task_id]['outputs']:
        target = WORK / declared
        if not target.exists(): raise ValueError(f'{task_id}: missing output {declared}')
        candidates = sorted(target.rglob('*')) if target.is_dir() else [target]
        actual = [p for p in candidates if p.is_file() and '__pycache__' not in p.parts]
        if not actual: raise ValueError(f'{task_id}: empty output {declared}')
        for path in actual:
            if path.is_symlink() or not path.resolve().is_relative_to(WORK):
                raise ValueError(f'unsafe output {path}')
            if path.stat().st_size == 0: raise ValueError(f'empty output {path}')
            rel = path.relative_to(WORK).as_posix()
            paths[rel] = {'path': rel, 'sha256': digest(path), 'bytes': path.stat().st_size}
    return list(paths.values())

def read_receipt(task_id: str) -> dict:
    return json.loads((WORK / TASKS[task_id]['receipt']).read_text(encoding='utf-8'))

def verify_receipt(task_id: str, seen: frozenset[str] = frozenset(), memo: dict | None = None) -> dict:
    if task_id in seen: raise ValueError('task dependency cycle')
    memo = {} if memo is None else memo
    if task_id in memo: return memo[task_id]
    receipt = read_receipt(task_id)
    if receipt['status'] not in {'done','complete_with_external_blockers'}: raise ValueError(f'{task_id} is not terminal')
    if receipt['status']=='complete_with_external_blockers' and (not TASKS[task_id].get('external_optional') or not receipt.get('blockers')): raise ValueError('external-blocker terminal state requires an optional task and concrete blockers')
    current_outputs={row['path']:row for row in output_files(task_id)}
    recorded_outputs={row['path']:row for row in receipt['outputs']}
    if current_outputs!=recorded_outputs:
        raise ValueError(f'{task_id}: declared output contents changed, including added or removed files')
    for record in receipt['outputs'] + receipt.get('checks', []):
        if digest(WORK / record['path']) != record['sha256']:
            raise ValueError(f'{task_id}: changed output {record["path"]}')
    expected = input_digest(task_id, seen | {task_id}, memo)
    if receipt['input_digest'] != expected:
        raise ValueError(f'{task_id}: changed task inputs; descendants invalid')
    memo[task_id] = receipt
    return receipt

def input_digest(task_id: str, seen: frozenset[str] = frozenset(), memo: dict | None = None) -> str:
    memo = {} if memo is None else memo
    task = TASKS[task_id]
    input_names = set(task['design_inputs']) | {task['role_prompt'], task['task_card']} | set(task.get('helper_prompts', []))
    inputs = {name: digest(PLAN / name) for name in sorted(input_names)}
    inputs['specs/task_graph.json'] = digest(PLAN / 'specs/task_graph.json')
    inputs['specs/execution_policy.json'] = digest(PLAN / 'specs/execution_policy.json')
    for dep in dependencies_for(task_id):
        r = verify_receipt(dep, seen, memo)
        inputs[f'dependency:{dep}'] = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()

def completion_status(task_id: str, blockers: list[str]) -> str:
    if blockers and (not TASKS[task_id].get('external_optional') or any(not isinstance(b,str) or not b.strip() for b in blockers)):raise ValueError('only declared optional external exports may close with concrete blockers')
    return 'complete_with_external_blockers' if blockers else 'done'

def commit(task_id: str, checks: list[str], notes: str = '', external_blockers: list[str] | None = None) -> dict:
    blockers=list(external_blockers or [])
    status=completion_status(task_id,blockers)
    signature = input_digest(task_id)
    checked = []
    for name in checks:
        p = WORK / name
        if not p.is_file(): raise ValueError(f'check evidence missing: {name}')
        checked.append({'path': name, 'sha256': digest(p)})
    receipt = {'task_id': task_id, 'status': status, 'input_digest': signature,
               'outputs': output_files(task_id), 'checks': checked,
               'research_state': 'NOT_RUN', 'research_execution': 'forbidden',
               'unrun_paths': ['all neural adapter, model, training, eval and benchmark paths'],
               'blockers': blockers, 'notes': notes, 'next_actions': [],
               'committed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    atomic(WORK / TASKS[task_id]['receipt'], receipt)
    return receipt

def sync() -> dict:
    prior = json.loads((WORK / 'run_state/ledger.json').read_text(encoding='utf-8'))
    # Receipts are the authority. A historical terminal ledger row must not
    # survive deletion of its receipt and strand the task outside `ready`.
    tasks = {tid: {'status': 'pending', 'invalid_reason': 'task receipt missing',
                   'outputs': [], 'checks': []} for tid in TASKS}
    done = []
    invalid = []
    memo = {}
    external_blockers = {}
    for tid in TASKS:
        receipt_path = WORK / TASKS[tid]['receipt']
        if receipt_path.exists():
            try:
                r = verify_receipt(tid,memo=memo)
                tasks[tid] = {'status': r['status'], 'input_digest': r['input_digest'],
                              'outputs': r['outputs'], 'checks': r['checks'], 'blockers': r.get('blockers',[])}
                if r.get('blockers'):external_blockers[tid]=r['blockers']
                done.append(tid)
            except (ValueError, OSError, KeyError) as error:
                tasks[tid] = {'status': 'pending', 'invalid_reason': str(error), 'outputs': [], 'checks': []}
                invalid.append(tid)
    ready = [tid for tid, task in TASKS.items() if tasks[tid]['status'] == 'pending'
             and all(dep in done for dep in dependencies_for(tid))]
    prior.update({'completed_tasks': done, 'external_blockers':external_blockers, 'tasks': tasks, 'research_state': 'NOT_RUN',
                  'updated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    atomic(WORK / 'run_state/ledger.json', prior)
    atomic(WORK / 'run_state/next_actions.json', {'ready': ready, 'invalidated': invalid,
           'external_blockers':external_blockers, 'remaining': [tid for tid in TASKS if tid not in done], 'research_state': 'NOT_RUN'})
    return {'done': done, 'ready': ready, 'invalidated': invalid, 'external_blockers':external_blockers}

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['commit', 'verify', 'sync'])
    p.add_argument('task_id', nargs='?')
    p.add_argument('--check', action='append', default=[])
    p.add_argument('--notes', default='')
    p.add_argument('--external-blocker', action='append', default=[])
    a = p.parse_args()
    result = sync() if a.command == 'sync' else commit(a.task_id, a.check, a.notes, a.external_blocker) if a.command == 'commit' else verify_receipt(a.task_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
