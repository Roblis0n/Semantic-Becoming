"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('effect','sum(m*(behavior_after-behavior_before-v)^2)/sum(m)','post-update public behavior error','valid shared behavior coordinates','behavior_mask','skip_with_reason',('transport_operator','behavior_encoder'),('source_direction','target_update'),(),GradientEstimator.EXACT,'shared public behaviors'),
 LossSpec('local','sum(m*(actual_behavior_delta-Jtarget delta)^2)/sum(m)','local linearization error','valid public anchor coordinates','anchor_mask','skip_with_reason',('transport_operator',),('target_update',),(),GradientEstimator.EXACT,'anchor coordinates'),
 LossSpec('ridge','lambda * sum(delta^2)/count(delta)','scoped parameter update squared norm','updated parameter elements','parameter_mask','skip_with_reason',('transport_operator',),('target_update',),(),GradientEstimator.EXACT,'updated parameters'))
def tensor_losses(actual_effect,desired,jvp_effect,delta,ridge,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'effect':masked_tensor_mean((actual_effect-desired).square(),masks[0]),'local':masked_tensor_mean((actual_effect-jvp_effect).square(),masks[1]),'ridge':masked_tensor_mean(ridge*delta.square(),masks[2])}
