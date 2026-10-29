from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('frame','mean aligned position error','sum of valid terms','count of valid terms','visible_valid','differentiable_zero',('vision_reader', 'mechanism_reader'),('aligned_positions',),(('position_target', 'target_or_return'),),GradientEstimator.EXACT,'physical coordinates'),
    LossSpec('action','mean predicted action consequence error','sum of valid terms','count of valid terms','action_valid','differentiable_zero',('action_adapter',),('predicted_next',),(('next_target', 'target_or_return'),),GradientEstimator.EXACT,'physical coordinates'),
    LossSpec('covariance','mean squared aligned covariance-target error','sum of valid squared covariance entries','count of valid covariance entries','covariance_valid','differentiable_zero',('vision_reader', 'mechanism_reader'),('aligned_covariances',),(('covariance_target', 'target_or_return'),),GradientEstimator.EXACT,'covariance matrix entries'),
)

def tensor_losses(aligned_positions,position_target,visible_valid,predicted_next,next_target,action_valid,*,aligned_covariances,covariance_target,covariance_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.core.learning import masked_tensor_mean as mean
    frame=mean((aligned_positions-position_target.detach()).square(),visible_valid,zero_valid_policy='differentiable_zero');action=mean((predicted_next-next_target.detach()).square(),action_valid,zero_valid_policy='differentiable_zero')
    covariance=mean((aligned_covariances-covariance_target.detach()).square(),covariance_valid,zero_valid_policy='differentiable_zero')
    return {'total':frame+covariance+action,'frame':frame,'covariance':covariance,'action':action}
