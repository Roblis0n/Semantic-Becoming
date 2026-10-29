"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_answer_transport(target_answers,backtranslation,offset):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if target_answers.ndim!=3 or backtranslation.ndim!=3 or offset.ndim!=2:raise ContractError('InvalidShape','answers[B,K,target], map[B,source,target], offset[B,source] required')
    b,k,d=target_answers.shape
    if backtranslation.shape[0]!=b or backtranslation.shape[2]!=d or offset.shape!=(b,backtranslation.shape[1]):raise ContractError('InvalidShape','backtranslation axes differ')
    return target_answers@backtranslation.transpose(-1,-2)+offset.unsqueeze(1)

def tensor_transform_policy(question_features,candidate_features,relation_features,weight,valid_candidates):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if question_features.ndim!=2 or candidate_features.ndim!=3 or relation_features.shape[:2]!=candidate_features.shape[:2] or valid_candidates.shape!=candidate_features.shape[:2]:raise ContractError('InvalidShape','question[B,d], candidates[B,K,d] and relation[B,K,r] required')
    if not bool(valid_candidates.any(-1).all()):raise ContractError('TransformBudget','no admissible transform in a row')
    joint=torch.cat((candidate_features*question_features.unsqueeze(1),relation_features),dim=-1)
    scores=(joint*weight).sum(-1).masked_fill(~valid_candidates,-torch.inf)
    return torch.softmax(scores,dim=-1)
