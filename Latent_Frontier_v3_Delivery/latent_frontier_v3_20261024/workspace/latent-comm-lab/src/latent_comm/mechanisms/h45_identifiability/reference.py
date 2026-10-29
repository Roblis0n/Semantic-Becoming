from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def entropy(probabilities):return -sum(p*math.log(p) for p in probabilities if p>0)

def equivalence_partition(state):
    queries=tuple(q for q in state.queries if q.allowed and q.local_only and q.likelihood is not None);groups={}
    for i,h in enumerate(state.hypotheses):
        signature=tuple(q.likelihood[i] for q in queries);groups.setdefault(signature,[]).append(h)
    return tuple(tuple(v) for v in groups.values())

def information_gain(prior,query):
    if query.likelihood is None:raise ContractError('UnknownLikelihood','unknown likelihood cannot produce a fabricated posterior')
    predictive=tuple(sum(prior[h]*query.likelihood[h][y] for h in range(len(prior))) for y in range(len(query.responses)))
    expected=0.
    for y,p in enumerate(predictive):
        if p>0:expected+=p*entropy(tuple(prior[h]*query.likelihood[h][y]/p for h in range(len(prior))))
    return max(0.,entropy(prior)-expected)

def select_query(state,*,cost_weight=0.,budget=StepBudget()):
    meter=budget.meter();partition=equivalence_partition(state);candidates=[];allowed=[q for q in state.queries if q.allowed and q.local_only]
    if not allowed:return QuerySelection(None,'none',None,None,partition,'NoAllowedQuery')
    for q in allowed:
        meter.consume(steps=1,cases=1)
        if q.likelihood is None:continue
        if state.prior is not None:
            ig=information_gain(state.prior,q);score=ig-cost_weight*q.cost;candidates.append((score,q.query_id,ig))
        else:
            worst=max(sum(row[y]>0 for row in q.likelihood) for y in range(len(q.responses)));score=len(state.hypotheses)-worst-cost_weight*q.cost;candidates.append((score,q.query_id,None))
    if not candidates:return QuerySelection(None,'unknown',None,None,partition,'UnknownLikelihood')
    if len(partition)==1:return QuerySelection(None,'information_gain' if state.prior is not None else 'minimax',None,0. if state.prior is not None else None,partition,'NonIdentifiable')
    score,qid,ig=max(candidates,key=lambda x:(x[0],x[1]));criterion='information_gain' if state.prior is not None else 'minimax'
    return QuerySelection(qid,criterion,score,ig,partition,'selected_local_query_only')

def update_posterior(state,query_id,response):
    q=next((q for q in state.queries if q.query_id==query_id),None)
    if q is None or not q.allowed or not q.local_only:raise ContractError('NoAllowedQuery','observation does not match a permitted local query')
    if q.likelihood is None:raise ContractError('UnknownLikelihood','response model unknown')
    if response not in q.responses:return PosteriorUpdate((),None,0. if state.prior is not None else None,'model_mismatch_unknown',True)
    y=q.responses.index(response);remaining=tuple(h for i,h in enumerate(state.hypotheses) if q.likelihood[i][y]>0)
    if state.prior is None:return PosteriorUpdate(remaining,None,None,'set_update' if remaining else 'model_mismatch_unknown',state.unknown_hypothesis_possible or not remaining)
    mass=sum(p*q.likelihood[i][y] for i,p in enumerate(state.prior))
    if mass==0:return PosteriorUpdate((),None,0.,'model_mismatch_unknown',True)
    posterior=tuple(p*q.likelihood[i][y]/mass for i,p in enumerate(state.prior))
    return PosteriorUpdate(state.hypotheses,posterior,mass,'bayesian_update_within_candidate_family',state.unknown_hypothesis_possible)

def migrate_hypotheses(state,new_version,permutation):
    if sorted(permutation)!=list(range(len(state.hypotheses))):raise ContractError('NonIdentifiable','migration must preserve every hypothesis')
    return replace(state,hypotheses=tuple(state.hypotheses[i] for i in permutation),queries=tuple(replace(q,likelihood=tuple(q.likelihood[i] for i in permutation) if q.likelihood is not None else None) for q in state.queries),prior=tuple(state.prior[i] for i in permutation) if state.prior is not None else None,version=new_version)
