from dataclasses import replace
from latent_comm.core import ContractError,StepBudget
from .reference import query_distribution

def intervention_after_graft(operation,certificate):
    if operation.world_version!=certificate.before.version or operation.variable not in dict(certificate.intervention_map):raise ContractError('UnboundCausalMap','H31 graft must explicitly map this intervention variable')
    target=dict(certificate.intervention_map)[operation.variable];modules={m.output:m for m in certificate.after.modules}
    if target not in modules or modules[target].unit!=operation.variable_unit:raise ContractError('UnitConflict','graft does not silently rescale intervention values')
    return replace(operation,variable=target,allowed_variables=frozenset({target}),world_version=certificate.after.version)

def kernel_action_for_intervention(operation,kernel,action_bindings):
    if operation.world_version!=kernel.version:raise ContractError('VersionMismatch','H43 action binding world differs')
    key=(operation.variable,operation.value,operation.variable_unit)
    if key not in action_bindings:raise ContractError('UnboundCausalMap','do-assignment needs an explicit world-kernel action correspondence')
    action=action_bindings[key]
    if action not in dict(kernel.actions):raise ContractError('ActionMismatch','mapped action is absent in world kernel')
    return action

def intervention_identification_query(worlds,noise_distributions,query,outcome_values,*,query_id,cost,budget=StepBudget()):
    from latent_comm.mechanisms.h45_identifiability.types import QuerySpec
    if query.semantics!='do' or len(worlds)!=len(noise_distributions) or not worlds:raise ContractError('UnknownCausalSemantics','H45 intervention likelihoods require explicit do queries and each candidate noise law')
    rows=[];meter=budget.meter()
    for world,noise in zip(worlds,noise_distributions):
        meter.consume(steps=len(world.modules)*len(noise),cases=1)
        distribution=dict(query_distribution(world,noise,replace(query,versions=replace(query.versions,world=world.version)),budget=budget))
        if not set(distribution)<=set(outcome_values):raise ContractError('UnknownLikelihood','declared response domain misses outcomes')
        rows.append(tuple(distribution.get(value,0.) for value in outcome_values))
    return QuerySpec(query_id,tuple(str(v) for v in outcome_values),tuple(rows),cost,True,True)
