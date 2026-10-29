"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def propose_exclusions(candidate_features,scope_features,predicate_weights,scope_weights):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if candidate_features.ndim!=3 or scope_features.ndim!=2 or predicate_weights.ndim!=2 or scope_weights.ndim!=2 or candidate_features.shape[0]!=scope_features.shape[0]:raise ContractError('UnsupportedExclusion','features B,D,F; scope B,S; predicate library P,F; scope classifier P,S required')
    predicate_logits=torch.einsum('bdf,pf->bdp',candidate_features,predicate_weights)
    applicable_logits=scope_features@scope_weights.T
    return {'predicate_logits':predicate_logits,'scope_logits':applicable_logits,'hard_authority':False}

def apply_tensor_exclusions(scores,verified_hard_keep,soft_risks,*,risk_weight=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if scores.ndim!=2 or verified_hard_keep.shape!=scores.shape or verified_hard_keep.dtype!=torch.bool or soft_risks.shape!=scores.shape:raise ContractError('HardSoftConfusion','hard keep mask must be separately certificate-verified B,D boolean; risks B,D')
    if bool((soft_risks<0).any()) or risk_weight<0:raise ContractError('UnsupportedExclusion','negative empirical penalties invalid')
    if bool((~verified_hard_keep.any(-1)).any()):raise ContractError('EmptyDomainConflict','do not softmax an empty feasible domain')
    return (scores-risk_weight*soft_risks).masked_fill(~verified_hard_keep,float('-inf'))

def train_exclusion_step(model_inputs,parameter_groups,optimizer,labels,valid_masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from .losses import tensor_losses
    from latent_comm.core.learning import LossValue
    expected=[id(p) for group in parameter_groups.values() for p in group];actual=[id(p) for g in optimizer.param_groups for p in g['params']]
    if set(parameter_groups)!={'exclusion_generator','scope_predictor'} or len(set(expected))!=len(expected) or len(set(actual))!=len(actual) or set(actual)!=set(expected):raise ContractError('HardSoftConfusion','optimizer owns only distinct generator/scope groups, not proof checker')
    bound={'exclusion_generator':model_inputs['predicate_weights'],'scope_predictor':model_inputs['scope_weights']}
    if any(tuple(id(p) for p in parameter_groups[name])!=(id(weight),) for name,weight in bound.items()):raise ContractError('HardSoftConfusion','declared owner groups must bind the actual forward predicate/scope weight identities')
    output=propose_exclusions(**model_inputs);losses=tensor_losses(output['predicate_logits'],output['scope_logits'],labels,valid_masks)
    skipped={name:value.reason for name,value in losses.items() if isinstance(value,LossValue) and value.skipped}
    active=[value for name,value in losses.items() if name not in skipped]
    if not active:return {'status':'skipped','reason':'zero valid terms in every loss','losses':losses,'skipped_losses':skipped}
    objective=sum(active)
    if objective.ndim!=0 or not bool(torch.isfinite(objective)):raise ContractError('InvalidLoss','finite scalar aggregate objective required')
    optimizer.zero_grad();objective.backward();optimizer.step();return {'status':'updated','losses':losses,'skipped_losses':skipped}
