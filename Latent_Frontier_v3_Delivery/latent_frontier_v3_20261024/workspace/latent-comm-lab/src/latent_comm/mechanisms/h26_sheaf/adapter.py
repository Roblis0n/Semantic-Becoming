"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_glue(constraints,bias,anchor_indices,anchor_values,*,tolerance=1e-7):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if constraints.ndim!=3 or bias.shape!=constraints.shape[:2]:raise ContractError('InvalidShape','A[B,e,n], b[B,e] required')
    b,e,n=constraints.shape
    if len(set(anchor_indices))!=len(anchor_indices) or any(k<0 or k>=n for k in anchor_indices):raise ContractError('InvalidAnchor','unique in-range anchor coordinates required')
    if anchor_values.shape!=(b,len(anchor_indices)):raise ContractError('InvalidShape','anchors[B,a] required')
    if not anchor_indices and bool((bias==0).all(dim=-1).any()):raise ContractError('MissingAnchor','homogeneous zero solution is not evidence')
    free=[k for k in range(n) if k not in anchor_indices]
    adjusted=bias-(constraints[:,:,anchor_indices]@anchor_values.unsqueeze(-1)).squeeze(-1)
    solution=torch.linalg.lstsq(constraints[:,:,free],adjusted.unsqueeze(-1)).solution.squeeze(-1) if free else constraints.new_empty((b,0))
    values={k:anchor_values[:,i] for i,k in enumerate(anchor_indices)}
    values.update({k:solution[:,i] for i,k in enumerate(free)})
    state=torch.stack([values[k] for k in range(n)],dim=-1)
    residual=(constraints@state.unsqueeze(-1)).squeeze(-1)-bias
    return state,residual,residual.square().sum(-1)>tolerance*tolerance
