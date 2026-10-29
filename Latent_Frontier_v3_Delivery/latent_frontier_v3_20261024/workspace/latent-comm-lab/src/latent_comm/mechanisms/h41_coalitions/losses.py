"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('value','sum(m*(estimated-v_table)^2)/sum(m)','known coalition value residual','known coalition values','known_value_mask','skip_with_reason',('coalition_value_estimator',),('capability_features',),(),GradientEstimator.EXACT,'coalitions'),
 LossSpec('allocation','-sum(m*log_pi(S)*task_utility)/sum(m)','policy score times actual task utility','valid feasible allocations','feasible_mask','skip_with_reason',('coalition_proposer',),('allocation_log_probability',),(('task_utility','allocation'),),GradientEstimator.POLICY_GRADIENT,'allocations'))
def tensor_losses(estimated,known_values,logp,utility,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'value':masked_tensor_mean((estimated-known_values).square(),masks[0]),'allocation':masked_tensor_mean(-logp*utility.detach(),masks[1])}
