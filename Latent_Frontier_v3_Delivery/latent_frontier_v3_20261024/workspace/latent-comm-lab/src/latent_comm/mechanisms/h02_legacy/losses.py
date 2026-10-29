from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','stage normalized task loss after dedicated mechanism','sum valid task losses','valid task count','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('response','mean ||z_hat-z_teacher||^2','sum of valid terms','count of valid terms','valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('predicted',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'response elements'),
    LossSpec('locality','BCE(refresh_logit,outside_or_error)','sum of valid terms','count of valid terms','refresh_valid','differentiable_zero',('mechanism_writer',),('refresh_logits',),(('refresh_target', 'target_or_return'),),GradientEstimator.EXACT,'queries'),
)

def tensor_losses(predicted,target,valid,refresh_logits,refresh_target,refresh_valid,*,task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    response=masked_tensor_mean((predicted-target.detach()).square(),valid,zero_valid_policy='differentiable_zero')
    locality=masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(refresh_logits,refresh_target.detach(),reduction='none'),refresh_valid,zero_valid_policy='differentiable_zero')
    return {'task':task_loss,'total':task_loss+response+locality,'response':response,'locality':locality}
