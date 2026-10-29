"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_transport(state, operator, readout, gauge, *, group='GL', condition_limit=10000.0):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if state.ndim!=2 or operator.ndim!=3 or readout.ndim!=3 or gauge.ndim!=3: raise ContractError('DimensionMismatch','expected [B,d], [B,d,d], [B,o,d], [B,d,d]')
    b,d=state.shape
    if operator.shape!=(b,d,d) or gauge.shape!=(b,d,d) or readout.shape[0]!=b or readout.shape[2]!=d: raise ContractError('DimensionMismatch','batch and coordinate axes must match exactly')
    condition=torch.linalg.cond(gauge)
    if not bool(torch.isfinite(condition).all()) or bool((condition>condition_limit).any()): raise ContractError('ConditionExceeded','noninvertible or unstable frame')
    if group=='orthogonal' and not torch.allclose(gauge.transpose(-1,-2)@gauge,torch.eye(d,device=gauge.device,dtype=gauge.dtype).expand(b,d,d)): raise ContractError('GroupMismatch','gauge is not orthogonal')
    if group not in ('GL','orthogonal'): raise ContractError('UnsupportedGroup','unknown transformation group')
    transformed_state=(gauge@state.unsqueeze(-1)).squeeze(-1)
    transformed_operator=torch.linalg.solve(gauge.transpose(-1,-2),(gauge@operator).transpose(-1,-2)).transpose(-1,-2)
    transformed_readout=torch.linalg.solve(gauge.transpose(-1,-2),readout.transpose(-1,-2)).transpose(-1,-2)
    return transformed_state, transformed_operator, transformed_readout, condition

def tensor_cross_transport(mapping, source_gauge, target_gauge):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if mapping.ndim!=3 or source_gauge.ndim!=3 or target_gauge.ndim!=3: raise ContractError('DimensionMismatch','explicit batched matrices required')
    b,dj,di=mapping.shape
    if source_gauge.shape!=(b,di,di) or target_gauge.shape!=(b,dj,dj): raise ContractError('DimensionMismatch','cross map allows different source and target dimensions, not different batches')
    return torch.linalg.solve(source_gauge.transpose(-1,-2),(target_gauge@mapping).transpose(-1,-2)).transpose(-1,-2)
