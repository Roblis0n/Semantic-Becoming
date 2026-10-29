"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def soft_matching(logits,type_compatible,*,iterations=16):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if logits.ndim!=3 or logits.shape!=type_compatible.shape or not 1<=iterations<=128:raise ContractError('InvalidShape','matching logits and type mask[B,source,target] required')
    if not bool(type_compatible.any(-1).all()) or not bool(type_compatible.any(-2).all()):raise ContractError('TypeViolation','unmatched type needs explicit partial domain, not zero-row normalization')
    logp=logits.masked_fill(~type_compatible,-torch.inf)
    for _ in range(iterations):
        logp=logp-torch.logsumexp(logp,dim=-1,keepdim=True)
        logp=logp-torch.logsumexp(logp,dim=-2,keepdim=True)
    return logp.exp()

def tensor_commuting_residual(mapping,source_operator,target_operator):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if mapping.ndim!=3 or source_operator.shape!=(mapping.shape[0],mapping.shape[2],mapping.shape[2]) or target_operator.shape!=(mapping.shape[0],mapping.shape[1],mapping.shape[1]):raise ContractError('InvalidShape','F[B,target,source], A[B,source,source], B[B,target,target] required')
    return mapping@source_operator-target_operator@mapping

def validate_hardened(source,target,object_map,operation_map,type_map,valid_domain):
    from .reference import check_morphism
    from .types import AnalogyMorphism
    # Hardening is nondifferentiable and always receives a fresh exact check.
    return check_morphism(source,target,AnalogyMorphism(tuple(object_map),tuple(operation_map),tuple(type_map),tuple(valid_domain)))
