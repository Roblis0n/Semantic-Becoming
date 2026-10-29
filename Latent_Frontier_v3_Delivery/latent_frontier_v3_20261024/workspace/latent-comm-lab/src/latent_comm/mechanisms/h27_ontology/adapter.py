"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def soft_predicate(predicate,features,known_masks,thresholds,*,temperature=1.0):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if temperature<=0:raise ContractError('OutOfDomain','positive relaxation temperature required')
    if predicate.op in ('eq','le'):
        if predicate.field not in features:raise ContractError('UndefinedPredicate','unbound concept observation')
        x=features[predicate.field];known=known_masks[predicate.field]
        if x.ndim!=1 or known.shape!=x.shape:raise ContractError('InvalidShape','observable and known mask need [B]')
        threshold=thresholds.get(predicate.field,predicate.constant)
        score=torch.sigmoid((threshold-x)/temperature) if predicate.op=='le' else torch.exp(-((x-threshold)/temperature).square())
        return score,known.to(dtype=torch.bool)
    values=[soft_predicate(c,features,known_masks,thresholds,temperature=temperature) for c in predicate.children]
    if predicate.op=='not':return 1-values[0][0],values[0][1]
    (a,ka),(b,kb)=values
    return (a*b if predicate.op=='and' else a+b-a*b),ka&kb

def concept_behavior(concept_values,known_mask,readout_weight,readout_bias):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if concept_values.ndim!=2 or known_mask.shape!=concept_values.shape or readout_weight.ndim!=2 or readout_weight.shape[1]!=concept_values.shape[1]:raise ContractError('InvalidShape','concept[B,C], mask[B,C], readout[A,C] required')
    # Unknown remains a separate channel, never interpreted as false evidence.
    known=known_mask.to(concept_values.dtype)
    return torch.nn.functional.linear(concept_values*known,readout_weight,readout_bias),known
