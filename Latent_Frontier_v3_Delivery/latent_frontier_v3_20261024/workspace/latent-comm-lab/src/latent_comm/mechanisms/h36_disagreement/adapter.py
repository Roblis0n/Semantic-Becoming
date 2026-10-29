"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_challenge_policy(violation_logits,scope_mask,executable_mask,previously_rejected_mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if violation_logits.ndim!=2 or any(m.shape!=violation_logits.shape for m in (scope_mask,executable_mask,previously_rejected_mask)):raise ContractError('InvalidShape','candidate and legality masks[B,C] required')
    valid=scope_mask&executable_mask&~previously_rejected_mask
    if not bool(valid.any(-1).all()):raise ContractError('UnresolvedDispute','no new executable in-scope challenge')
    return torch.softmax(violation_logits.masked_fill(~valid,-torch.inf),dim=-1)

def tensor_revision_scores(program_features,counterexample_features,interaction_weight):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if program_features.ndim!=3 or counterexample_features.ndim!=3 or program_features.shape[0]!=counterexample_features.shape[0]:raise ContractError('InvalidShape','program[B,P,d], counterexample[B,C,e] required')
    # Bilinear program-counterexample relation, not rhetoric/vote aggregation.
    relations=(program_features@interaction_weight)@counterexample_features.transpose(-1,-2)
    return relations.mean(dim=-1)
