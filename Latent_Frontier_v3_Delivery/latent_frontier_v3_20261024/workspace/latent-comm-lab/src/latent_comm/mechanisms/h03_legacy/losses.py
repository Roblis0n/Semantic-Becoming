from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('mixture_nll','-logsumexp_k(log pi_k + sum_t log p_kt)','sum of valid terms','count of valid terms','sequence_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('sequence_logprob',),(),GradientEstimator.EXACT,'sequences'),
    LossSpec('calibration','sum_k (pi_k-target_k)^2','sum of valid terms','count of valid terms','calibration_valid','differentiable_zero',('mechanism_writer',),('weights',),(('calibration_target', 'target_or_return'),),GradientEstimator.EXACT,'branches'),
    LossSpec('coverage','minimum valid set assignment cost','sum of valid terms','count of valid terms','coverage_valid','differentiable_zero',('mechanism_writer',),('coverage_cost',),(),GradientEstimator.FIRST_ORDER,'matched branches (assignment fixed; matched distances pathwise)'),
)

def tensor_losses(sequence_logprob,sequence_valid,weights,calibration_target,calibration_valid,coverage_cost,coverage_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.core.learning import masked_tensor_mean
    nll=masked_tensor_mean(-sequence_logprob,sequence_valid,zero_valid_policy='differentiable_zero')
    calibration=masked_tensor_mean((weights.softmax(-1)-calibration_target.detach()).square(),calibration_valid,zero_valid_policy='differentiable_zero')
    coverage=masked_tensor_mean(coverage_cost,coverage_valid,zero_valid_policy='differentiable_zero')
    return {'total':nll+calibration+coverage,'mixture_nll':nll,'calibration':calibration,'coverage':coverage}
