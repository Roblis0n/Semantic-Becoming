from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

from itertools import combinations
import random

def value_table(game):return {frozenset(s):v for s,v in game.values}

def exact_shapley(game,budget=StepBudget()):
    n=len(game.players);meter=budget.meter();meter.dimension(n);table=value_table(game)
    if n>8:raise ContractError('CoalitionBudget','exact source algorithm limited to eight members; use sampled permutations')
    needed=[frozenset(s) for r in range(n+1) for s in combinations(game.players,r)];meter.consume(cases=len(needed))
    missing=tuple(tuple(sorted(s)) for s in needed if s not in table)
    if missing:return ContributionRecord(tuple((p,None) for p in game.players),tuple((p,None) for p in game.players),False,0,missing,None,'UndefinedValue')
    result={p:0. for p in game.players}
    for p in game.players:
        others=tuple(q for q in game.players if q!=p)
        for r in range(n):
            weight=math.factorial(r)*math.factorial(n-r-1)/math.factorial(n)
            for subset in combinations(others,r):
                meter.consume(steps=1);s=frozenset(subset);result[p]+=weight*(table[s|{p}]-table[s])
    residual=sum(result.values())-(table[frozenset(game.players)]-table[frozenset()])
    return ContributionRecord(tuple(result.items()),tuple((p,0.) for p in game.players),True,len(needed),(),residual,'exact_finite_value_table')

def sampled_shapley(game,*,samples=128,seed=0,budget=StepBudget()):
    if not 1<=samples<=128:raise ContractError('CoalitionBudget','bounded permutation count required')
    rng=random.Random(seed);table=value_table(game);meter=budget.meter();values={p:[] for p in game.players};missing=set();done=0;limited=False
    for _ in range(samples):
        if meter.steps+len(game.players)>budget.max_steps or meter.cases+1>budget.max_cases:limited=True;break
        meter.consume(steps=len(game.players),cases=1);order=list(game.players);rng.shuffle(order);s=frozenset();sample={};valid=True
        for p in order:
            target=s|{p}
            if s not in table:missing.add(s);valid=False
            if target not in table:missing.add(target);valid=False
            if s in table and target in table:sample[p]=table[target]-table[s]
            s=target
        if valid:
            done+=1
            for p in game.players:values[p].append(sample[p])
    means={p:sum(v)/len(v) if v else None for p,v in values.items()}
    variances={p:sum((x-means[p])**2 for x in v)/(len(v)-1) if len(v)>1 else None for p,v in values.items()}
    residual=sum(means.values())-(table[frozenset(game.players)]-table[frozenset()]) if done else None
    return ContributionRecord(tuple(means.items()),tuple(variances.items()),False,done,tuple(tuple(sorted(s)) for s in sorted(missing,key=lambda x:tuple(sorted(x)))),residual,'UndefinedValue' if missing else 'budget_limited_estimate' if limited else 'permutation_estimate')

def capability_plan(contract,members):
    agents={a.name:a for a in contract.agents}
    if not set(members)<=agents.keys():raise ContractError('CapabilityUnsatisfied','unknown coalition member')
    if sum(agents[p].cost for p in members)>contract.resource_budget:raise ContractError('CoalitionBudget','coalition exceeds internal resource budget')
    available=set(contract.public_inputs);pending=set(members);order=[]
    while pending:
        ready=sorted(p for p in pending if set(agents[p].requires)<=available)
        if not ready:raise ContractError('CapabilityUnsatisfied','capability dependency cycle or missing input')
        for p in ready:available.update(agents[p].provides);pending.remove(p);order.append(p)
    if not set(contract.required_outputs)<=available:raise ContractError('CapabilityUnsatisfied','coalition does not produce requested type')
    return tuple(order)

def choose_coalition(game,contract,budget=StepBudget()):
    meter=budget.meter();candidates=[]
    for members,value in game.values:
        meter.consume(steps=1,cases=1)
        try:plan=capability_plan(contract,members)
        except ContractError:continue
        candidates.append((value,tuple(members),plan))
    if not candidates:raise ContractError('CapabilityUnsatisfied','no known feasible coalition; unknown values were not assumed zero')
    return max(candidates,key=lambda x:(x[0],-len(x[1])))

def unique_evidence_value(supports,atom_values):
    atoms=set(a for source in supports for a in source)
    if not atoms<=dict(atom_values).keys():raise ContractError('UndefinedValue','evidence support value absent')
    return sum(dict(atom_values)[a] for a in atoms)

def migrate_players(game,new_version,names):
    if set(names)!=set(game.players) or len(set(names.values()))!=len(names):raise ContractError('CreditConflict','player migration must be bijective')
    return CoalitionGame(tuple(names[p] for p in game.players),tuple((tuple(names[p] for p in s),v) for s,v in game.values),new_version)
