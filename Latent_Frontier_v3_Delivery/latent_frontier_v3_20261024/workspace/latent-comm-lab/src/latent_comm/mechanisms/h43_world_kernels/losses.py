"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=tuple(LossSpec(name,formula,'sum of masked per-case losses','valid terms',mask,'skip_with_reason',owners,inputs,(),GradientEstimator.EXACT,units) for name,formula,mask,owners,inputs,units in (
 ('transition','mean masked -log K(snext|s,a)','transition_mask',('kernel_generator','state_interface'),('current_state',),'observed transitions'),
 ('observation','mean masked -log O(observation|s)','observation_mask',('observation_generator',),('world_state',),'observations'),
 ('shared_noise','mean masked (predicted_joint-target_joint)^2','joint_mask',('noise_coupling',),('conditional_kernels',),'joint outcome cells'),
 ('multistep','mean masked (predicted_behavior-target_behavior)^2','horizon_mask',('kernel_generator',),('initial_state',),'horizon behavior elements')))
def tensor_losses(transition_probability,observation_probability,joint_residual,multistep_residual,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'transition':masked_tensor_mean(-transition_probability.clamp_min(1e-12).log(),masks[0]),'observation':masked_tensor_mean(-observation_probability.clamp_min(1e-12).log(),masks[1]),'shared_noise':masked_tensor_mean(joint_residual.square(),masks[2]),'multistep':masked_tensor_mean(multistep_residual.square(),masks[3])}
