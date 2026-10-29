from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','stage normalized task loss after dedicated mechanism','sum valid task losses','valid task count','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('continuation','mean suffix_action_error','sum of valid terms','count of valid terms','valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('action_logits',),(('action_targets', 'target_or_return'),),GradientEstimator.EXACT,'future actions'),
)

def tensor_losses(action_logits,action_targets,valid,*,task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    if action_logits.shape[:-1]!=action_targets.shape:raise ContractError('DimensionMismatch','common action-space suffix labels, not cross-tokenizer logits')
    safe_targets=torch.where(valid.bool(),action_targets.detach(),torch.zeros_like(action_targets))
    safe_logits=torch.where(valid.bool().unsqueeze(-1),action_logits,torch.zeros_like(action_logits))
    error=torch.nn.functional.cross_entropy(safe_logits.flatten(0,-2),safe_targets.flatten(),reduction='none').reshape(action_targets.shape)
    continuation=masked_tensor_mean(error,valid,zero_valid_policy='differentiable_zero')
    return {'task':task_loss,'total':task_loss+continuation,'continuation':continuation}
