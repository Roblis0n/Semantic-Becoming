from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','stage normalized task loss after dedicated mechanism','sum valid task losses','valid task count','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('behavior','mean ||T(z)-teacher(z)||^2','sum of valid terms','count of valid terms','state_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('predicted',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'state elements'),
    LossSpec('composition','mean ||Tb(Ta(z))-program_ba(z)||^2','sum of valid terms','count of valid terms','composition_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('composed',),(('composition_target', 'target_or_return'),),GradientEstimator.EXACT,'state elements'),
)

def tensor_losses(predicted,target,composed,composition_target,state_valid,composition_valid,*,task_loss,behavior_weight=1.,composition_weight=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.core.learning import masked_tensor_mean
    if predicted.shape!=target.shape or composed.shape!=composition_target.shape:raise ContractError('DimensionMismatch','supervised behavior shapes')
    behavior=masked_tensor_mean((predicted-target.detach()).square(),state_valid,zero_valid_policy='differentiable_zero')
    composition=masked_tensor_mean((composed-composition_target.detach()).square(),composition_valid,zero_valid_policy='differentiable_zero')
    return {'task':task_loss,'total':task_loss+behavior_weight*behavior+composition_weight*composition,'behavior':behavior,'composition':composition}
