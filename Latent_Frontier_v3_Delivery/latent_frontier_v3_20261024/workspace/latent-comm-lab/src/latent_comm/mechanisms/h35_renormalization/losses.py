"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('commute','sum(m*(C Fmicro(z)-Fmacro(Cz))^2)/sum(m)','coarse dynamic closure error','valid macro-state elements','macro_mask','skip_with_reason',('coarse_map','macro_dynamics'),('micro_state',),(),GradientEstimator.EXACT,'macro elements'),
 LossSpec('task','sum(m*(macro_task-micro_task)^2)/sum(m)','preserved task-response residual','valid task responses','task_mask','skip_with_reason',('coarse_map','task_reader'),('macro_state',),(),GradientEstimator.EXACT,'task responses'),
 LossSpec('residual','sum(m*(detail_prediction-detail)^2)/sum(m)','retained detail prediction error','valid micro residual elements','detail_mask','skip_with_reason',('lift','detail_memory'),('coarse_state',),(),GradientEstimator.EXACT,'micro elements'))
def tensor_losses(closure,task_residual,detail_residual,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'commute':masked_tensor_mean(closure.square(),masks[0]),'task':masked_tensor_mean(task_residual.square(),masks[1]),'residual':masked_tensor_mean(detail_residual.square(),masks[2])}
