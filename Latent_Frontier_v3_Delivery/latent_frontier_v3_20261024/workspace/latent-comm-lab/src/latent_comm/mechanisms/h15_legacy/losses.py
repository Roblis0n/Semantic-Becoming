from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('cross_receiver','mean_receiver mean_valid_task loss','sum valid receiver task means','count valid receivers, inner valid task count','receiver_valid; at least one valid task per receiver','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('receiver_errors',),(),GradientEstimator.EXACT,'receivers then tasks'),
    LossSpec('effect','common behavior discrepancy','sum of valid terms','count of valid terms','behavior_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('behaviors',),(('behavior_target', 'target_or_return'),),GradientEstimator.EXACT,'shared behavior coordinates'),
)

def tensor_losses(receiver_errors,receiver_valid,behaviors,behavior_target,behavior_valid,*,behavior_spaces):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean as mean
    for space in behavior_spaces[1:]:behavior_spaces[0].require_same(space)
    if receiver_errors.shape!=receiver_valid.shape:raise ContractError('DimensionMismatch','receiver-task mask')
    denom=receiver_valid.sum(-1);safe_errors=torch.where(receiver_valid.bool(),receiver_errors,torch.zeros_like(receiver_errors));per_receiver=safe_errors.sum(-1)/denom.clamp_min(1);valid=denom>0
    task=per_receiver[valid].mean() if bool(valid.any()) else safe_errors.sum()*0.
    effect=mean((behaviors-behavior_target.detach()).square(),behavior_valid,zero_valid_policy='differentiable_zero')
    return {'total':task+effect,'cross_receiver':task,'effect':effect}
