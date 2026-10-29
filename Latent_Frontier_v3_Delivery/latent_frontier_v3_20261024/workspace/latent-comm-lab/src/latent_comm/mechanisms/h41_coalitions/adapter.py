"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_coalition_value(membership,singleton_values,pair_values,baseline):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if membership.ndim!=3 or singleton_values.shape!=(membership.shape[-1],) or pair_values.shape!=(membership.shape[-1],membership.shape[-1]):raise ContractError('InvalidShape','membership[B,C,N], singleton[N], pair[N,N] required')
    interactions=membership.unsqueeze(-1)*membership.unsqueeze(-2)
    return membership@singleton_values+(interactions*torch.triu(pair_values,diagonal=1)).sum((-1,-2))+baseline

def tensor_coalition_policy(values,known_mask,feasible_mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if values.shape!=known_mask.shape or values.shape!=feasible_mask.shape:raise ContractError('InvalidShape','candidate value and masks must match')
    valid=known_mask&feasible_mask
    if not bool(valid.any(-1).all()):raise ContractError('UndefinedValue','no known feasible candidate')
    return torch.softmax(values.masked_fill(~valid,-torch.inf),dim=-1)
