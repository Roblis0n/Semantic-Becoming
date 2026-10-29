from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def terminal_from_view(view):
    if 'terminal_states' not in view.public_task or 'terminal_source' not in view.public_task:raise ContractError('FutureLabelLeak','public terminal fields missing; receiver features cannot supply a hidden answer')
    view.versions.require('task')
    return PublicTerminalConstraint(tuple(view.public_task['terminal_states']),view.public_task['terminal_source'],view.versions.task)

def solve_boundary(graph,budget=StepBudget(),path_limit=64):
    meter=budget.meter();meter.dimension(len(graph.states));forward=[set(graph.start_states)];backward=[set() for _ in range(len(graph.transitions)+1)];backward[-1]=set(graph.terminal.states)
    if not 1<=path_limit<=64:raise ContractError('SolverLimit','path limit 1..64 required')
    for layer in graph.transitions:
        meter.consume(steps=1);forward.append({b for a,b in layer if a in forward[-1]})
    for t in range(len(graph.transitions)-1,-1,-1):
        meter.consume(steps=1);backward[t]={a for a,b in graph.transitions[t] if b in backward[t+1]}
    paths=[];pending=[(s,) for s in sorted(forward[0]&backward[0])]
    while pending and len(paths)<path_limit:
        prefix=pending.pop(0);t=len(prefix)-1;meter.consume(steps=1)
        if t==len(graph.transitions):meter.consume(branches=1,cases=1);paths.append(prefix);continue
        pending.extend(prefix+(b,) for a,b in graph.transitions[t] if a==prefix[-1] and b in backward[t+1])
    status='SolverLimit' if pending else 'BoundaryInfeasible' if not paths else 'MultiplePaths' if len(paths)>1 else 'UniquePath'
    return BoundaryResult(tuple(paths),tuple(tuple(sorted(s)) for s in forward),tuple(tuple(sorted(s)) for s in backward), status, 'planning_with_public_terminal_not_future_observation',tuple(pending),meter.steps)

def migrate_states(graph,new_version,renames):
    if set(renames)!=set(graph.states) or len(set(renames.values()))!=len(renames):raise ContractError('BoundaryInfeasible','state migration must be bijective')
    terminal=replace(graph.terminal,states=tuple(renames[s] for s in graph.terminal.states))
    return TrajectoryFactorGraph(tuple(renames[s] for s in graph.states),tuple(tuple((renames[a],renames[b]) for a,b in e) for e in graph.transitions),tuple(renames[s] for s in graph.start_states),terminal,new_version)
