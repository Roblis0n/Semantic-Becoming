"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=tuple(LossSpec(name,formula,'sum of masked residuals','valid terms',mask,'skip_with_reason',owners,inputs,(),GradientEstimator.EXACT,units) for name,formula,mask,owners,inputs,units in (
 ('terminal','mean masked (readout-target)^2','behavior_mask',('coupling','trajectory_reader'),('trajectory',),'behavior elements'),
 ('trajectory','mean masked (predicted_relation-target_relation)^2','trajectory_mask',('coupling',),('trajectory',),'trajectory relations'),
 ('stability','mean masked relu(norm2_next-norm2_current-budget)^2','step_mask',('dissipation_factor','coupling'),('trajectory',),'logical steps')))
def tensor_losses(readout,target,relation_residual,norm_increments,allowed_increment,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'terminal':masked_tensor_mean((readout-target).square(),masks[0]),'trajectory':masked_tensor_mean(relation_residual.square(),masks[1]),'stability':masked_tensor_mean((norm_increments-allowed_increment).clamp_min(0).square(),masks[2])}
