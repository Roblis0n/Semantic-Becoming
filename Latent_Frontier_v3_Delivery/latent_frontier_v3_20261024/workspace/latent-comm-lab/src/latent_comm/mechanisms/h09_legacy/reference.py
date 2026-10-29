import math
from latent_comm.core import ContractError,StepBudget
from latent_comm.mechanisms.h31_grafting.reference import validate_scm,evaluate_scm
from .types import *

def descendants(world,variable):
    order=validate_scm(world);affected={variable}
    if variable not in order:raise ContractError('UnknownVariable',variable)
    for node in order:
        module=next(m for m in world.modules if m.output==node)
        if any(p in affected for p in module.parents):affected.add(node)
    return frozenset(affected-{variable})
def apply_intervention(world,noise,operation):
    modules={m.output:m for m in world.modules}
    if operation.world_version!=world.version or operation.variable not in modules or modules[operation.variable].unit!=operation.variable_unit:raise ContractError('BoundaryMismatch','typed intervention requires matching variable/unit/world')
    return evaluate_scm(world,noise,((operation.variable,operation.value),))
def compose_interventions(operations):
    # Sequential overwrite semantics; no commutation assumed for repeated assignment.
    effective={}
    for op in operations:
        if effective and op.world_version!=next(iter(effective.values())).world_version:raise ContractError('VersionMismatch','intervention worlds differ')
        effective[op.variable]=op
    return tuple(effective.values())
def may_commute(world,left,right):
    return left.variable!=right.variable and right.variable not in descendants(world,left.variable) and left.variable not in descendants(world,right.variable)
def query_distribution(world,noise_distribution,query,*,budget=StepBudget()):
    if query.versions.world!=world.version:raise ContractError('VersionMismatch','query world version')
    order=validate_scm(world)
    if query.outcome not in order or any(k not in order for k,_ in query.assignments):raise ContractError('UnknownVariable','query variable absent')
    if not noise_distribution or len(noise_distribution)>64 or any(p<0 or not math.isfinite(p) for _,p in noise_distribution) or abs(sum(p for _,p in noise_distribution)-1)>1e-9:raise ContractError('InvalidDistribution','explicit normalized joint exogenous distribution')
    if query.semantics=='observe' and query.assignments:raise ContractError('ConditioningRequired','observe does not silently condition on assignments')
    meter=budget.meter();counts={};normalizer=0.
    for noise,p in noise_distribution:
        meter.consume(steps=len(order),cases=1)
        values=dict(evaluate_scm(world,dict(noise),query.assignments if query.semantics=='do' else ()))
        if query.semantics=='condition' and any(values[k]!=v for k,v in query.assignments):continue
        counts[values[query.outcome]]=counts.get(values[query.outcome],0)+p;normalizer+=p
    if normalizer==0:raise ContractError('ImpossibleObservation','zero-probability conditioning event')
    return tuple(sorted((value,p/normalizer) for value,p in counts.items()))
def transport_intervention(operation,*,target_variable,target_unit,target_world,scale,offset,allowed_variables,assumption):
    if not assumption:raise ContractError('UnboundCausalMap','explicit structural correspondence assumption required')
    return Intervention(target_variable,scale*operation.value+offset,target_unit,frozenset(allowed_variables),target_world)
