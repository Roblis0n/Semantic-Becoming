"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('interface','sum(m*task_error)/sum(m)','task-conditioned interface loss','valid role-isolated tasks','task_mask','skip_with_reason',('protocol_interface',),('public_task_features',),(),GradientEstimator.EXACT,'tasks'),
 LossSpec('proposal','-sum(m*log_pi(mutation)*reward)/sum(m)','mutation policy score times separately recorded novelty/solvability reward','valid legal mutations','mutation_mask','skip_with_reason',('environment_proposer',),('mutation_log_probability',),(('reward','proposal'),),GradientEstimator.POLICY_GRADIENT,'mutations'))
def tensor_losses(task_errors,proposal_logp,reward,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'interface':masked_tensor_mean(task_errors,masks[0]),'proposal':masked_tensor_mean(-proposal_logp*reward.detach(),masks[1])}
