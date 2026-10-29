"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('outer_query_full','L_query(theta_T(psi),query)','query-only loss after fixed support unroll','valid held-out query targets','query_valid_mask','skip_with_reason',('plasticity_rule_parameters',),('support_gradients','inner_parameters','rule_parameters'),(),GradientEstimator.SECOND_ORDER,'query targets'),
 LossSpec('outer_query_first_order','L_query(theta_T(psi,stopgrad(g_support)),query)','query loss with support-gradient Hessian terms omitted','valid held-out query targets','query_valid_mask','skip_with_reason',('plasticity_rule_parameters',),('inner_parameters','rule_parameters'),(('support_gradients','inner_update'),),GradientEstimator.FIRST_ORDER,'query targets'),
 LossSpec('update_budget','mean relu(norm(delta)-max_norm)^2','pre-clipping update norm exceedance','valid scoped parameter groups','group_mask','skip_with_reason',('plasticity_rule_parameters',),('raw_update',),(),GradientEstimator.EXACT,'parameter groups'))
def tensor_objectives(query_errors,raw_norms,max_norm,query_mask,group_mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'outer_query':masked_tensor_mean(query_errors,query_mask),'update_budget':masked_tensor_mean((raw_norms-max_norm).clamp_min(0).square(),group_mask)}
