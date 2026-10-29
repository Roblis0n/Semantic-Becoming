"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_integrate(initial,dissipation_factor,raw_coupling,*,dt,steps,readout_weights):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if initial.ndim!=2 or raw_coupling.ndim!=3 or dissipation_factor.ndim!=3:raise ContractError('InvalidShape','state[B,d], factors/coupling[B,d,d] required')
    b,d=initial.shape
    if raw_coupling.shape!=(b,d,d) or dissipation_factor.shape!=(b,d,d) or readout_weights.shape!=(b,steps+1) or dt<=0 or not 1<=steps<=128:raise ContractError('InvalidShape','explicit batch, time and bounded unroll axes required')
    q=dissipation_factor.transpose(-1,-2)@dissipation_factor;k=.5*(raw_coupling-raw_coupling.transpose(-1,-2));a=k-q
    identity=torch.eye(d,device=initial.device,dtype=initial.dtype).expand(b,d,d)
    left=identity-dt*a/2;right=identity+dt*a/2;z=initial;states=[z]
    for _ in range(steps):
        z=torch.linalg.solve(left,right@z.unsqueeze(-1)).squeeze(-1);states.append(z)
    trajectory=torch.stack(states,dim=1);weights=torch.softmax(readout_weights,dim=-1)
    return trajectory,(trajectory*weights.unsqueeze(-1)).sum(dim=1)
