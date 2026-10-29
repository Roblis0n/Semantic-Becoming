from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import eye,transpose,sub,scale,matrix
from .types import ResponseCapsule
from .reference import predict

def response_from_scm(world,noise,variables,anchor,outcomes,*,radius,versions,budget=StepBudget()):
    from latent_comm.mechanisms.h31_grafting.reference import evaluate_scm
    if versions.world!=world.version or len(variables)!=len(anchor):raise ContractError('VersionMismatch','H31 response requires explicit SCM and intervention variable axes')
    meter=budget.meter();base=dict(evaluate_scm(world,noise,tuple(zip(variables,anchor)),budget=budget));meter.consume(steps=len(world.modules),cases=1);columns=[]
    for i in range(len(variables)):
        changed=list(anchor);changed[i]+=1.;meter.consume(steps=len(world.modules),cases=1)
        row=dict(evaluate_scm(world,noise,tuple(zip(variables,changed)),budget=budget));columns.append(tuple(row[k]-base[k] for k in outcomes))
    return ResponseCapsule(tuple(anchor),tuple(base[k] for k in outcomes),transpose(tuple(columns)),eye(len(variables)),radius,tuple(variables),('explicit affine SCM','fixed shared noise assignment'), 'structural_intervention',versions,'exact_affine_structural_response')

def response_from_kernel(kernel,action,anchor,*,radius,versions):
    if kernel.version!=versions.world or action not in dict(kernel.transitions):raise ContractError('VersionMismatch','H43 response binds action and world-kernel version')
    if len(anchor)!=len(kernel.states) or any(p<0 for p in anchor) or abs(sum(anchor)-1)>1e-9:raise ContractError('InvalidProbability','condition is an explicit state-distribution simplex')
    from latent_comm.core.finite import matvec
    response=transpose(dict(kernel.transitions)[action]);base=matvec(response,anchor)
    return ResponseCapsule(tuple(anchor),base,response,eye(len(anchor)),radius,tuple('state:'+str(i) for i in range(len(anchor))),('condition domain: probability simplex','kernel predictions not real evidence'),'observational',versions,'exact_linear_mixture_response')

def query_likelihood_from_responses(capsules,query,*,query_id,responses,cost):
    from latent_comm.mechanisms.h45_identifiability.types import QuerySpec
    if not capsules or any(c.versions.task!=capsules[0].versions.task or c.versions.world!=capsules[0].versions.world for c in capsules):raise ContractError('VersionMismatch','H45 alternative likelihoods share a declared task/world')
    rows=[]
    for capsule in capsules:
        result=predict(capsule,query)
        if result.needs_refresh:raise ContractError('RefreshRequired','H45 cannot extrapolate a response likelihood')
        if len(result.value)!=len(responses) or any(p<0 for p in result.value) or abs(sum(result.value)-1)>1e-9:raise ContractError('InvalidProbability','response outputs are not declared response probabilities')
        rows.append(result.value)
    return QuerySpec(query_id,tuple(responses),tuple(rows),cost,True,True)
