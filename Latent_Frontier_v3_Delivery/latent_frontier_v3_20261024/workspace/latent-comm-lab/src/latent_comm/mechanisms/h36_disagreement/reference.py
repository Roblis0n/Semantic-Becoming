from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def execute(program,x,depth=0):
    if type(x) is not int or depth>8:raise ContractError('InvalidCounterexample','bounded integer program input required')
    if program.op=='divisible':return x%program.divisor==0
    v=tuple(execute(c,x,depth+1) for c in program.children)
    if program.op=='not':return not v[0]
    if program.op=='and':return all(v)
    return not v[0] or v[1]

def challenge(claim,x,observation_rule='universal_validity',other=None):
    if type(x) is not int:raise ContractError('InvalidCounterexample','textual accusations are not executable evidence')
    if x not in claim.domain:raise ContractError('ScopeMismatch','challenge outside claim domain')
    prediction=execute(claim.program,x)
    if observation_rule=='universal_validity':expected=True
    elif observation_rule=='disagreement_only':
        if other is None or x not in other.domain:raise ContractError('ScopeMismatch','second scoped executable claim required')
        expected=None
        if prediction==execute(other.program,x):return Counterexample(claim.claim_id,x,prediction,None,observation_rule,'agreement_not_truth')
        return Counterexample(claim.claim_id,x,prediction,None,observation_rule,'unresolved_disagreement')
    else:raise ContractError('InvalidCounterexample','no registered public observation rule')
    return Counterexample(claim.claim_id,x,prediction,expected,observation_rule,'verified_counterexample' if prediction!=expected else 'not_a_counterexample')

def find_counterexamples(claim,budget=StepBudget(),candidate_inputs=None):
    meter=budget.meter();meter.dimension(len(claim.domain));found=[];rejected=[]
    for x in claim.domain if candidate_inputs is None else candidate_inputs:
        meter.consume(steps=1,cases=1)
        try:c=challenge(claim,x)
        except ContractError as e:rejected.append((x,str(e)));continue
        if c.status=='verified_counterexample':found.append(c)
        else:rejected.append((x,c.status))
    # Minimal means smallest absolute integer in this explicitly finite domain.
    found.sort(key=lambda c:(abs(c.value),c.value))
    return tuple(found),tuple(rejected)

def revise_game(initial,candidate_programs,*,round_limit=6,budget=StepBudget()):
    if not 1<=round_limit<=64:raise ContractError('RevisionLimit','bounded rounds required')
    current=initial;history=[];meter=budget.meter();used={initial.program}
    for round_index in range(round_limit):
        examples,rejected=find_counterexamples(current,budget)
        if not examples:return DisagreementGame(tuple(history),(current,),'valid_on_declared_finite_domain_only')
        viable=[]
        for p in candidate_programs:
            if p in used:continue
            meter.consume(steps=1,cases=1)
            failures=sum(not execute(p,x) for x in current.domain)
            if all(execute(p,c.value) for c in examples):viable.append((failures,repr(p),p))
        if not viable:
            history.append(RevisionRound(current,examples,None,rejected));return DisagreementGame(tuple(history),(current,),'UnresolvedDispute')
        _,_,p=min(viable,key=lambda item:(item[0],item[1]));used.add(p)
        revised=ScopedClaim(current.claim_id+':revision'+str(round_index+1),p,current.domain,current.version+'.'+str(round_index+1))
        history.append(RevisionRound(current,examples,revised,rejected));current=revised
    return DisagreementGame(tuple(history),(current,),'RevisionLimit')

def migrate_claim(claim,new_version,new_domain):
    # Scope extension is not inherited proof: explicitly retain finite validity status.
    if not set(claim.domain)<=set(new_domain) or len(new_domain)>64:raise ContractError('ScopeMismatch','migration must explicitly cover the old finite domain')
    migrated=replace(claim,domain=tuple(new_domain),version=new_version)
    return migrated,find_counterexamples(migrated)[0]

def parse_rule(data,depth=0):
    if depth>8 or set(data)!={'op','divisor','children'}:raise ContractError('InvalidCounterexample','malformed bounded rule program')
    return RuleProgram(data['op'],data['divisor'],tuple(parse_rule(c,depth+1) for c in data['children']))
