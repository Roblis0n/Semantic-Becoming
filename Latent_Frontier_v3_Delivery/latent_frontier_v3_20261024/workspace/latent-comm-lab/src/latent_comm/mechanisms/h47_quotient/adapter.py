"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def encode_task_relative(state_features,query_features,state_projection,query_projection,prototypes,*,temperature=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if state_features.ndim!=3 or query_features.ndim!=3 or prototypes.ndim!=3 or temperature<=0:raise ContractError('QueryFamilyUndefined','state B,N,F, query B,Q,T, prototypes B,K,Z and positive temperature required')
    state=state_features@state_projection;query=query_features@query_projection
    if state.shape[0]!=query.shape[0] or state.shape[-1]!=query.shape[-1] or prototypes.shape[0]!=state.shape[0] or prototypes.shape[-1]!=state.shape[-1]:raise ContractError('QueryFamilyUndefined','behavior feature axes differ')
    signatures=torch.einsum('bnz,bqz->bnq',state,query)
    proto_signatures=torch.einsum('bkz,bqz->bkq',prototypes,query)
    distance=(signatures[:,:,None,:]-proto_signatures[:,None,:,:]).square().mean(-1)
    assignment=torch.softmax(-distance/temperature,dim=-1)
    reconstructed=torch.einsum('bnk,bkq->bnq',assignment,proto_signatures)
    return {'behavior_signatures':signatures,'assignments':assignment,'reconstructed_behavior':reconstructed,'exactness':'approximate_learned_clusters_not_equivalence'}

def train_quotient_step(inputs,parameters,optimizer,behavior_targets,masks,*,rate_weight=0.01):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from .losses import tensor_losses
    from latent_comm.core.learning import LossValue
    from latent_comm.core.finite import finite_scalar
    if finite_scalar(rate_weight)<0:raise ContractError('InvalidLoss','rate weight must be finite and nonnegative')
    expected=[id(p) for p in parameters.values()];actual=[id(p) for g in optimizer.param_groups for p in g['params']]
    if set(parameters)!={'state_projection','query_projection','prototypes'} or len(set(expected))!=len(expected) or len(set(actual))!=len(actual) or set(expected)!=set(actual):raise ContractError('RefinementConflict','optimizer must exactly own the declared state/task/prototype parameters')
    result=encode_task_relative(**inputs,**parameters);losses=tensor_losses(result['reconstructed_behavior'],behavior_targets,result['assignments'],masks)
    skipped={name:value.reason for name,value in losses.items() if isinstance(value,LossValue) and value.skipped}
    weights={'behavior':1.,'rate':rate_weight}
    active=[weights[name]*value for name,value in losses.items() if name not in skipped and weights[name]!=0]
    if not active:return {'status':'skipped','reason':'no valid nonzero-weight objective','losses':losses,'skipped_losses':skipped}
    objective=sum(active)
    if objective.ndim!=0 or not bool(torch.isfinite(objective)):raise ContractError('InvalidLoss','finite scalar aggregate objective required')
    optimizer.zero_grad();objective.backward();optimizer.step();return {'status':'updated','losses':losses,'skipped_losses':skipped}
