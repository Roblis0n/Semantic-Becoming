"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_world_proposal(module_logits,compatibility_mask,edit_logits):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if module_logits.ndim!=2 or module_logits.shape!=compatibility_mask.shape or edit_logits.ndim!=3 or edit_logits.shape[:2]!=module_logits.shape:raise ContractError('InvalidShape','module logits[B,K], compatibility[B,K], edit logits[B,K,E] required')
    if not bool(compatibility_mask.any(-1).all()):raise ContractError('IncompatibleWorlds','no compatible kernel combination')
    return torch.softmax(module_logits.masked_fill(~compatibility_mask,-torch.inf),dim=-1),torch.softmax(edit_logits,dim=-1)

def future_dream_train(protocol_parameters,world_parameters,protocol_optimizer,world_optimizer,synthetic_batches,holdout,protocol_loss,world_log_probability,*,parent_sources,holdout_sources,independence_assumed=False,max_steps=32,clip=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from .reference import independent_holdout
    independent_holdout(parent_sources,holdout_sources,independence_assumed=independence_assumed)
    if not 1<=max_steps<=128 or len(synthetic_batches)>max_steps:raise ContractError('DreamBudget','bounded synthetic curriculum required')
    if {id(p) for p in protocol_parameters}&{id(p) for p in world_parameters}:raise ContractError('CircularSupport','world/protocol parameter owners must be disjoint')
    for optimizer,parameters in ((protocol_optimizer,protocol_parameters),(world_optimizer,world_parameters)):
        actual=[id(p) for group in optimizer.param_groups for p in group['params']]
        if set(actual)!={id(p) for p in parameters} or len(actual)!=len(parameters):raise ContractError('DreamBudget','optimizer parameter owner mismatch')
    history=[]
    for batch in synthetic_batches:
        if not batch.synthetic:raise ContractError('SyntheticAsReal','curriculum batch lost synthetic lineage')
        protocol_optimizer.zero_grad(set_to_none=True);loss=protocol_loss(batch);loss.backward();torch.nn.utils.clip_grad_norm_(protocol_parameters,clip);protocol_optimizer.step();history.append(float(loss.detach()))
    independent_loss=protocol_loss(holdout)
    world_optimizer.zero_grad(set_to_none=True)
    # Score-function estimator: held-out utility, not a self-generated truth label.
    proposer_loss=world_log_probability*independent_loss.detach()
    proposer_loss.backward();torch.nn.utils.clip_grad_norm_(world_parameters,clip);world_optimizer.step()
    return {'synthetic_training_losses':tuple(history),'independent_holdout_loss':float(independent_loss.detach()),'proposer_estimator':'policy_gradient','research_evidence_kind':'requires_future_authorized_execution'}
