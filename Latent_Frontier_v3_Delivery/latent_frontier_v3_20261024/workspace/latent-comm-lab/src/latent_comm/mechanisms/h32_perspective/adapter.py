"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_view(costs,weights,view_map,*,allow_loss=False,tolerance=1e-7):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if costs.ndim!=2 or weights.shape!=costs.shape or view_map.ndim!=3 or view_map.shape[0]!=costs.shape[0] or view_map.shape[2]!=costs.shape[1]:raise ContractError('InvalidShape','costs/weights[B,k], view[B,j,k] required')
    dual=torch.linalg.lstsq(view_map.transpose(-1,-2),weights.unsqueeze(-1)).solution.squeeze(-1)
    residual=(view_map.transpose(-1,-2)@dual.unsqueeze(-1)).squeeze(-1)-weights
    if not allow_loss and bool((residual.norm(dim=-1)>tolerance).any()):raise ContractError('InformationLoss','preference direction not representable')
    return (view_map@costs.unsqueeze(-1)).squeeze(-1),dual,residual

def tensor_original_constraints(original_costs,constraint_matrix,bounds):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if original_costs.ndim!=2 or constraint_matrix.ndim!=3 or bounds.shape!=constraint_matrix.shape[:2] or constraint_matrix.shape[0]!=original_costs.shape[0] or constraint_matrix.shape[2]!=original_costs.shape[1]:raise ContractError('InvalidShape','hard constraints must use original objective coordinates')
    return (constraint_matrix@original_costs.unsqueeze(-1)).squeeze(-1)-bounds
