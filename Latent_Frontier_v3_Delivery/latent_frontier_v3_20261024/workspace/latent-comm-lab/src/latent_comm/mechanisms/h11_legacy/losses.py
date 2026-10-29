from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('prefix','weighted mean task error across legal truncations','sum of valid terms','count of valid terms','prefix_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('prefix_errors',),(),GradientEstimator.STRAIGHT_THROUGH,'prefix tasks'),
    LossSpec('rate','-mean log2 entropy_model(symbol)','sum of valid terms','count of valid terms','symbol_valid','differentiable_zero',('entropy_model',),('symbol_log_probs',),(),GradientEstimator.EXACT,'bits per symbol'),
    LossSpec('codebook','mean ||embedding-stop(residual)||^2 + beta||residual-stop(embedding)||^2','sum of valid terms','count of valid terms','coordinate_valid','differentiable_zero',('codebook', 'mechanism_writer'),('commitment_errors', 'codebook_errors'),(),GradientEstimator.STRAIGHT_THROUGH,'coordinate elements'),
)

def tensor_losses(prefix_errors,prefix_valid,symbol_log_probs,symbol_valid,commitment_errors,codebook_errors,coordinate_valid,*,rate_weight=.01,beta=.25):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import math
    from latent_comm.core.learning import masked_tensor_mean as mean
    prefix=mean(prefix_errors,prefix_valid,zero_valid_policy='differentiable_zero');rate=mean(-symbol_log_probs/math.log(2),symbol_valid,zero_valid_policy='differentiable_zero')
    quantization=mean(codebook_errors+beta*commitment_errors,coordinate_valid,zero_valid_policy='differentiable_zero')
    return {'total':prefix+rate_weight*rate+quantization,'prefix':prefix,'rate':rate,'codebook':quantization}
