"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('value','sum(m*(wprime dot cprime-w dot c)^2)/sum(m)','objective-value preservation residual','valid objective values','goal_mask','skip_with_reason',('view_map','objective_readout'),('costs','weights'),(),GradientEstimator.EXACT,'goals'),
 LossSpec('constraint','sum(m*relu(A_original c_original-b)^2)/sum(m)','original hard-constraint violation','valid original constraints','constraint_mask','skip_with_reason',('objective_readout',),('original_costs',),(),GradientEstimator.EXACT,'constraints'))
def tensor_losses(original_value,transformed_value,constraint_residual,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'value':masked_tensor_mean((transformed_value-original_value).square(),masks[0]),'constraint':masked_tensor_mean(constraint_residual.clamp_min(0).square(),masks[1])}
