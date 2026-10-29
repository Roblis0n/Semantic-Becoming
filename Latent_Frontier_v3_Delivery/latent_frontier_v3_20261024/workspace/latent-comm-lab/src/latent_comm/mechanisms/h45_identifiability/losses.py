"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('response','sum(m*-log p(observation|hypothesis,query))/sum(m)','observed response NLL','valid program-observation cases','observation_mask','skip_with_reason',('response_encoder',),('public_query_features',),(),GradientEstimator.EXACT,'observations'),
 LossSpec('query_policy','-sum(m*log_pi(query)*verified_information_gain)/sum(m)','legal query policy score','valid host-authorized local queries','query_mask','skip_with_reason',('query_proposer',),('query_log_probability',),(('verified_information_gain','query_policy'),),GradientEstimator.POLICY_GRADIENT,'queries'))
def tensor_losses(probabilities,logp,gain,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'response':masked_tensor_mean(-probabilities.clamp_min(1e-12).log(),masks[0]),'query_policy':masked_tensor_mean(-logp*gain.detach(),masks[1])}
