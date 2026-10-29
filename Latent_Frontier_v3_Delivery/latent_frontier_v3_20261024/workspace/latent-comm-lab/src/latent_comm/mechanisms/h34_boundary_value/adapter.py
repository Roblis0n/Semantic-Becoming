"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_forward_backward(log_transition,start_mask,terminal_mask,*,terminal_source):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if terminal_source not in ('public_goal','public_boundary'):raise ContractError('FutureLabelLeak','terminal must be publicly supplied task boundary')
    if log_transition.ndim!=4 or log_transition.shape[-1]!=log_transition.shape[-2]:raise ContractError('InvalidShape','transition[B,T,S,S] required')
    b,t,s,_=log_transition.shape
    if start_mask.shape!=(b,s) or terminal_mask.shape!=(b,s) or not 1<=t<=128:raise ContractError('InvalidShape','boundary[B,S] masks and bounded horizon required')
    zero=log_transition.new_zeros((b,s));alpha=[zero.masked_fill(~start_mask,-torch.inf)]
    for k in range(t):alpha.append(torch.logsumexp(alpha[-1].unsqueeze(-1)+log_transition[:,k],dim=-2))
    beta=[zero.masked_fill(~terminal_mask,-torch.inf)]
    for k in range(t-1,-1,-1):beta.append(torch.logsumexp(log_transition[:,k]+beta[-1].unsqueeze(-2),dim=-1))
    beta=list(reversed(beta));logz=torch.logsumexp(alpha[-1]+beta[-1],dim=-1)
    if not bool(torch.isfinite(logz).all()):raise ContractError('BoundaryInfeasible','no finite-weight path satisfies both public boundaries')
    posterior=torch.stack([a+v-logz.unsqueeze(-1) for a,v in zip(alpha,beta)],dim=1).exp()
    return posterior,logz
