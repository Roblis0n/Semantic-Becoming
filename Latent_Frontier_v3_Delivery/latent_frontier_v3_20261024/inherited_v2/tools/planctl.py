#!/usr/bin/env python3
"""Validate this planning bundle; never imports or executes research models."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

class PlanError(ValueError):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanError(f'Cannot read {path}: {exc}') from exc


def topological_order(tasks: list[dict[str, Any]]) -> list[str]:
    ids=[x['id'] for x in tasks]
    if len(ids)!=len(set(ids)):
        raise PlanError('Duplicate task id')
    known=set(ids)
    for t in tasks:
        missing=set(t['depends_on'])-known
        if missing:
            raise PlanError(f"{t['id']}: unknown dependencies {sorted(missing)}")
    result=[]
    while len(result)<len(tasks):
        ready=sorted(t['id'] for t in tasks if t['id'] not in result
                     and set(t['depends_on']).issubset(result))
        if not ready:
            raise PlanError('Dependency cycle')
        result.extend(ready)
    return result


def authorize(action: str, policy: dict[str, Any]) -> bool:
    """Fail closed. Permission to act is not empirical evidence of success."""
    if action in policy['banned_actions']:
        raise PlanError(f'Policy denied: {action}')
    if action not in policy['allowed_actions']:
        raise PlanError(f'Unknown or unauthorized action: {action}')
    return True


def validate(root: Path) -> dict[str, Any]:
    root=root.resolve()
    policy=read_json(root/'specs/execution_policy.json')
    if policy.get('research_model_execution') is not False:
        raise PlanError('Research execution must be locked')
    if policy.get('no_empirical_gate_for_hypothesis_implementation') is not True:
        raise PlanError('Empirical gate must not restrict innovation')
    if policy.get('new_spending_budget')!=0:
        raise PlanError('Unexpected new-spending authorization')
    if policy.get('public_release_authorized') is not False:
        raise PlanError('Unexpected publication authorization')
    tasks=read_json(root/'specs/task_graph.json')['tasks']
    order=topological_order(tasks)
    if len(tasks)!=60:
        raise PlanError('Expected 60 explicit tasks')
    hs=read_json(root/'specs/hypotheses.json')
    if {x['id'] for x in hs}!={f'H{i:02d}' for i in range(1,25)}:
        raise PlanError('Hypothesis inventory mismatch')
    for h in hs:
        p=(root/h['path']).resolve()
        if not p.is_relative_to(root) or not p.is_file() or p.stat().st_size<500:
            raise PlanError(f"Missing/substantially empty card: {h['id']}")
        if not h['modules']:
            raise PlanError(f"No implementation scope: {h['id']}")
    recipes=list((root/'recipes').glob('*.json'))
    if len(recipes)!=32:
        raise PlanError('Expected 24 individual + 8 combination recipes')
    for p in recipes:
        recipe=read_json(p)
        if recipe.get('execution_mode')!='design' or recipe.get('research_execution_authorized') is not False:
            raise PlanError(f'Unlocked recipe {p.name}')
    for c in read_json(root/'specs/combinations.json'):
        if not set(c['hypotheses'])<={x['id'] for x in hs}:
            raise PlanError(f"Unknown combination member: {c['id']}")
    idx=read_json(root/'specs/document_index.json')
    for p in idx['docs']+idx['prompts']+idx['media']:
        if not (root/p).is_file():
            raise PlanError(f'Missing document: {p}')
    for s in read_json(root/'provenance/input_inventory.json'):
        p=root/'provenance'/s['filename']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=s['sha256']:
            raise PlanError(f"Input provenance hash mismatch: {s['id']}")
    return {'status':'passed','scope':'planning_bundle_structure_only',
            'research_models_executed':False,'hypotheses':len(hs),'tasks':len(tasks),
            'recipes':len(recipes),'topological_order':order}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['validate','order','check-action'])
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--action')
    args=parser.parse_args()
    try:
        if args.command=='check-action':
            if not args.action:
                parser.error('--action is required')
            authorize(args.action,read_json(args.root/'specs/execution_policy.json'))
            out={'allowed':True,'action':args.action}
        else:
            report=validate(args.root)
            out=report['topological_order'] if args.command=='order' else report
        print(json.dumps(out,ensure_ascii=False,indent=2))
    except (PlanError,KeyError,TypeError) as exc:
        parser.exit(2,f'ERROR: {exc}\n')

if __name__=='__main__':
    main()
