"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('relation','sum(m*CE(relation_logits,verified_relation))/sum(m)','relation classification CE','verified rewrite edges','edge_mask','skip_with_reason',('transform_selector',),('question_features',),(),GradientEstimator.EXACT,'rewrite edges'),
 LossSpec('backtranslation','sum(m*(translated-answer)^2)/sum(m)','answer relation residual squared','valid answer coordinates','answer_mask','skip_with_reason',('answer_map',),('target_answer',),(),GradientEstimator.EXACT,'answer coordinates'),
 LossSpec('path_policy','-sum(m*log_pi(path)*advantage)/sum(m)','negative path log probability times stopped advantage','valid paths','path_mask','skip_with_reason',('transform_selector',),('path_log_probability',),(('advantage','path_policy'),),GradientEstimator.POLICY_GRADIENT,'paths'))
def tensor_losses(logits,relations,translated,answers,log_probability,advantage,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'relation':masked_tensor_mean(torch.nn.functional.cross_entropy(logits,relations,reduction='none'),masks[0]),'backtranslation':masked_tensor_mean((translated-answers).square(),masks[1]),'path_policy':masked_tensor_mean(-log_probability*advantage.detach(),masks[2])}
