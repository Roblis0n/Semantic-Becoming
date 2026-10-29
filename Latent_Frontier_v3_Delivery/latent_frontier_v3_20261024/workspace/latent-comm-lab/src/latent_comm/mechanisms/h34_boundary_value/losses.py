"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('transition','sum(m*(z_next-F(z))^2)/sum(m)','transition consistency residual','valid transition coordinates','transition_mask','skip_with_reason',('transition_messages',),('trajectory',),(),GradientEstimator.EXACT,'transition coordinates'),
 LossSpec('boundary','sum(m*boundary_error)/sum(m)','public start and terminal violation','valid boundary conditions','boundary_mask','skip_with_reason',('backward_constraint_encoder',),('trajectory',),(),GradientEstimator.EXACT,'public boundary conditions'),
 LossSpec('task','sum(m*task_error)/sum(m)','task readout error','valid task outputs','task_mask','skip_with_reason',('trajectory_reader',),('trajectory',),(),GradientEstimator.EXACT,'task outputs'))
def tensor_losses(transition_residual,boundary_errors,task_errors,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'transition':masked_tensor_mean(transition_residual.square(),masks[0]),'boundary':masked_tensor_mean(boundary_errors,masks[1]),'task':masked_tensor_mean(task_errors,masks[2])}
