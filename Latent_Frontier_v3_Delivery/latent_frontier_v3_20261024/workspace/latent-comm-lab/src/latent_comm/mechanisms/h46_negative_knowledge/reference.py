from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def predicate_holds(predicate,x):
    if type(x) is not int:raise ContractError('UnsupportedExclusion','finite prototype candidate domain is integer-valued')
    v=predicate.value
    return {'eq':lambda:x==v,'ne':lambda:x!=v,'lt':lambda:x<v,'le':lambda:x<=v,'gt':lambda:x>v,'ge':lambda:x>=v,'divisible':lambda:x%v==0,'not_divisible':lambda:x%v!=0}[predicate.op]()

def validate_domain(domain):
    if not domain or len(domain)>64 or len(set(domain))!=len(domain) or any(type(x) is not int for x in domain):raise ContractError('UnsupportedExclusion','finite unique integer domain of at most64 candidates required')

def verify_hard(capsule,domain,meter=None):
    if capsule.mode!='hard' or capsule.witness.kind not in ('proof_scoped','program_exhaustive'):raise ContractError('HardSoftConfusion','hard certificate not supplied')
    witness=capsule.witness
    if set(witness.checked_domain)!=set(domain) or len(witness.checked_domain)!=len(domain):raise ContractError('UnsupportedExclusion','certificate is not complete over this exact finite domain')
    counterexamples=[]
    for x in domain:
        if meter:meter.consume(steps=1,cases=1)
        if predicate_holds(capsule.excluded,x) and predicate_holds(witness.required_predicate,x):counterexamples.append(x)
    if counterexamples:raise ContractError('UnsupportedExclusion','overgeneralized exclusion would prune feasible candidates: '+repr(counterexamples))
    return True

def dependency_order(capsules):
    if len(capsules)>64:raise ContractError('UnsupportedExclusion','at most64 exclusion capsules in finite reference')
    lookup={c.capsule_id:c for c in capsules}
    if len(lookup)!=len(capsules):raise ContractError('UnsupportedExclusion','duplicate capsule identity')
    visiting=set();done=set();order=[]
    def visit(key):
        if key not in lookup:raise ContractError('UnsupportedExclusion','unknown exclusion dependency')
        if key in visiting:raise ContractError('UnsupportedExclusion','cyclic exclusion dependency')
        if key in done:return
        visiting.add(key)
        for dep in lookup[key].dependencies:visit(dep)
        visiting.remove(key);done.add(key);order.append(lookup[key])
    for key in lookup:visit(key)
    return tuple(order)

def apply_exclusions(domain,capsules,active_assumptions,domain_version,*,retracted=(),budget=StepBudget()):
    validate_domain(domain);meter=budget.meter();meter.dimension(len(domain));active=set(active_assumptions);revoked=set(retracted);feasible=set(domain);penalties={x:0. for x in domain};applied=[];inactive=[];disabled=set()
    for capsule in dependency_order(capsules):
        meter.consume(steps=1)
        if capsule.domain_version!=domain_version:reason='ScopeExpired'
        elif set(capsule.assumptions)-active or set(capsule.assumptions)&revoked or set(capsule.retract_on)&revoked:reason='AssumptionRetracted'
        elif capsule.capsule_id in revoked or set(capsule.dependencies)&disabled:reason='AssumptionRetracted'
        else:reason=None
        if reason:inactive.append((capsule.capsule_id,reason));disabled.add(capsule.capsule_id);continue
        if capsule.mode=='hard':verify_hard(capsule,domain,meter)
        for x in domain:
            meter.consume(steps=1)
            if predicate_holds(capsule.excluded,x):
                if capsule.mode=='hard':feasible.discard(x)
                elif capsule.mode=='soft':penalties[x]+=capsule.reliability
        applied.append(capsule.capsule_id)
    conflicts=tuple(c.capsule_id for c in capsules if c.mode=='hard' and c.capsule_id in applied) if not feasible else ()
    return ConditionalFeasibleRegion(tuple(domain),tuple(x for x in domain if x in feasible),tuple(penalties.items()),tuple(applied),tuple(inactive),conflicts,'EmptyDomainConflict' if not feasible else 'conditional_feasible',domain_version,meter.steps,meter.cases)

def retract_exclusions(previous,capsules,active_assumptions,retractions,*,budget=StepBudget()):
    next_region=apply_exclusions(previous.original_domain,capsules,set(active_assumptions)-set(retractions),previous.version,retracted=retractions,budget=budget)
    invalidated=tuple(key for key,reason in next_region.inactive if reason=='AssumptionRetracted')
    restored=tuple(x for x in next_region.feasible if x not in previous.feasible)
    return RetractionEvent(invalidated,restored,next_region)

def generalization_counterexamples(candidate,required_predicate,domain,*,budget=StepBudget()):
    validate_domain(domain);meter=budget.meter();bad=[]
    for x in domain:
        meter.consume(steps=1,cases=1)
        if predicate_holds(candidate,x) and predicate_holds(required_predicate,x):bad.append(x)
    return tuple(bad)

def migrate_capsule(capsule,new_version,new_domain):
    validate_domain(new_domain)
    if capsule.mode=='hard':
        if set(new_domain)!=set(capsule.witness.checked_domain):raise ContractError('ScopeExpired','new domain requires re-proving the exclusion; old finite proof does not generalize')
    return replace(capsule,domain_version=new_version)
