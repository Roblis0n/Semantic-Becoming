from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('intervention','mean predicted do effect squared error','sum of valid terms','count of valid terms','valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('predicted',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'outcome elements'),
    LossSpec('algebra','mean ||IaIb(z)-IbIa(z)||^2 for independent targets','sum of valid terms','count of valid terms','commuting_mask','differentiable_zero',('mechanism_writer',),('left_then_right', 'right_then_left'),(),GradientEstimator.EXACT,'legal commuting pairs'),
)

def tensor_losses(predicted,target,valid,left_then_right,right_then_left,commuting_mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.core.learning import masked_tensor_mean as mean
    behavior=mean((predicted-target.detach()).square(),valid,zero_valid_policy='differentiable_zero')
    algebra=mean((left_then_right-right_then_left).square(),commuting_mask,zero_valid_policy='differentiable_zero')
    return {'total':behavior+algebra,'intervention':behavior,'algebra':algebra}
