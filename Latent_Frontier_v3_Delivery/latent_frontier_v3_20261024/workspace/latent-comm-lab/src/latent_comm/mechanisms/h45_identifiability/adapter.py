"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_information_gain(prior,response_logits,allowed_mask,query_costs,cost_weight=0.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if prior.ndim!=2 or response_logits.ndim!=4 or response_logits.shape[0]!=prior.shape[0] or response_logits.shape[2]!=prior.shape[1] or allowed_mask.shape!=response_logits.shape[:2] or query_costs.shape!=allowed_mask.shape:raise ContractError('InvalidShape','prior[B,H], likelihood[B,Q,H,Y], host mask/cost[B,Q] required')
    if bool((prior<0).any()) or not torch.allclose(prior.sum(-1),torch.ones_like(prior[:,0])):raise ContractError('UnknownLikelihood','explicit normalized prior required')
    likelihood=torch.softmax(response_logits,dim=-1);joint=prior[:,None,:,None]*likelihood;predictive=joint.sum(-2);posterior=joint/predictive.unsqueeze(-2).clamp_min(1e-12)
    h_prior=-(prior*prior.clamp_min(1e-12).log()).sum(-1);h_posterior=-(posterior*posterior.clamp_min(1e-12).log()).sum(-2)
    ig=h_prior[:,None]-(predictive*h_posterior).sum(-1)
    if not bool(allowed_mask.any(-1).all()):raise ContractError('NoAllowedQuery','host permission mask has no legal query')
    return ig,(ig-cost_weight*query_costs).masked_fill(~allowed_mask,-torch.inf)
