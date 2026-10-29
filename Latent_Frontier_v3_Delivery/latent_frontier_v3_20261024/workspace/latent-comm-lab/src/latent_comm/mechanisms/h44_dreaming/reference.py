from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

import hashlib,json
from dataclasses import asdict
from latent_comm.mechanisms.h43_world_kernels.reference import compose_kernels,rollout

def construct_dream(kernels,noise_joint,edits,*,assumptions=(),conditional_independence=False,budget=StepBudget()):
    if not kernels or len(edits)>3:raise ContractError('DreamBudget','finite nonempty kernel pool and at most three explicit edits required')
    if len({k.kernel_id for k in kernels})!=len(kernels):raise ContractError('IncompatibleWorlds','dream edit targets require unique parent kernel identities')
    meter=budget.meter();ids={k.kernel_id for k in kernels};changes={}
    for edit in edits:
        meter.consume(steps=1)
        if edit.kernel_id not in ids:raise ContractError('IncompatibleWorlds','edit targets a kernel outside the pool')
        key=(edit.kernel_id,edit.state,edit.action,edit.noise_values)
        if key in changes:raise ContractError('IncompatibleWorlds','multiple edits conflict on the same conditional row')
        changes[key]=edit.probabilities
    signature=hashlib.sha256(json.dumps({'parents':[asdict(k) for k in kernels],'noise':asdict(noise_joint),'edits':[asdict(e) for e in edits],'assumptions':assumptions},sort_keys=True).encode()).hexdigest()[:20]
    modified=[];applied=set()
    for kernel in kernels:
        rows=[]
        for row in kernel.transition_rows:
            key=(kernel.kernel_id,row.state,row.action,row.noise_values)
            if key in changes:rows.append(replace(row,probabilities=tuple(changes[key])));applied.add(key)
            else:rows.append(row)
        modified.append(replace(kernel,transition_rows=tuple(rows),version=kernel.version+':dream:'+signature))
    if applied!=set(changes):raise ContractError('IncompatibleWorlds','edit conditional state/action/noise row does not exist')
    try:composed=compose_kernels(tuple(modified),noise_joint,conditional_independence=conditional_independence,new_version='dream:'+signature,budget=budget)
    except ContractError as error:raise ContractError('IncompatibleWorlds',str(error)) from error
    return DreamWorld('dream:'+signature,composed,tuple(k.kernel_id for k in kernels),tuple(edits),tuple(assumptions))

def observe_dream(world,initial,actions,budget=StepBudget()):
    result=rollout(world.kernel,initial,actions,budget)
    identity=hashlib.sha256(json.dumps({'world':world.world_id,'initial':initial,'actions':actions},sort_keys=True).encode()).hexdigest()[:20]
    return SyntheticEvidence('synthetic:'+identity,world.world_id,(world.world_id,)+world.parent_kernel_ids,result['observations'])

def assert_evidence_use(evidence,claim_id,claim_kind,dependency_edges=()):
    if claim_kind=='real_world_fact':raise ContractError('SyntheticAsReal','dream observations cannot establish independent real-world truth')
    edges=tuple(dependency_edges)+tuple((p,evidence.evidence_id) for p in evidence.parents)+((evidence.evidence_id,claim_id),)
    nodes=tuple(sorted({x for e in edges for x in e}))
    try:topological_order(nodes,edges)
    except ContractError as error:raise ContractError('CircularSupport','self-confirmation support cycle detected') from error
    return True

def question_candidates(world,baseline,start_states,budget=StepBudget()):
    if baseline.states!=world.kernel.states or baseline.actions!=world.kernel.actions:raise ContractError('IncompatibleWorlds','counterfactual question comparison requires common state/action coordinates')
    meter=budget.meter();out=[];before=dict(baseline.transitions);after=dict(world.kernel.transitions)
    for start in start_states:
        if start not in world.kernel.states:raise ContractError('IncompatibleWorlds','question seed outside feasible world')
        i=world.kernel.states.index(start)
        for action,_ in world.kernel.actions:
            for j,target in enumerate(world.kernel.states):
                meter.consume(steps=1)
                if abs(after[action][i][j]-before[action][i][j])>1e-9:
                    meter.consume(cases=1);out.append(QuestionCandidate('question:'+str(len(out)),world.world_id,start,action,target,'counterfactual edit changed transition probability'))
    return tuple(out)

def answer_question(world,question):
    if question.world_id!=world.world_id or not question.synthetic:raise ContractError('SyntheticAsReal','question belongs to a different or unlabelled world')
    table=dict(world.kernel.transitions)
    return table[question.action][world.kernel.states.index(question.start_state)][world.kernel.states.index(question.target_state)]

def local_role_view(world,role,component_indices):
    from latent_comm.core.views import RoleView
    from latent_comm.core import VersionSet
    if any(type(i) is not int or not 0<=i<len(world.parent_kernel_ids) for i in component_indices):raise ContractError('IncompatibleWorlds','visibility projection index absent')
    observations=tuple(tuple(o[i] for i in component_indices) for o in world.kernel.observations)
    return RoleView(role,{'actions':tuple(a for a,_ in world.kernel.actions),'synthetic':True},{'visible_observation_domain':observations},VersionSet(world=world.world_id))

def independent_holdout(parent_sources,holdout_sources,*,independence_assumed=False):
    """Check declared source IDs and require, but do not verify, independence.

    Distinct IDs cannot establish distinct lineage or statistical independence:
    aliases, common ancestors and selection effects require external assessment.
    True means that this necessary ID check passed under the caller's explicitly
    stated independence assumption; it is not an independence certificate.
    """
    parents=tuple(parent_sources);holdouts=tuple(holdout_sources)
    if not parents or not holdouts or any(not isinstance(x,str) or not x for x in parents+holdouts):
        raise ContractError('CircularSupport','nonempty parent and holdout source identities required')
    if set(parents)&set(holdouts):raise ContractError('CircularSupport','outer holdout source identity overlaps a parent')
    if independence_assumed is not True:raise ContractError('CircularSupport','statistical independence must be explicitly assumed; source IDs alone cannot establish it')
    return True
