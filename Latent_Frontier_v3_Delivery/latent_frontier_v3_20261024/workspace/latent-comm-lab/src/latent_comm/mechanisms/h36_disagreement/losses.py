"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('valid_challenge','-sum(m*log_pi(x)*verified_violation)/sum(m)','policy score times interpreter-verified reward','valid executable challenges','legal_challenge_mask','skip_with_reason',('critic_policy',),('challenge_log_probability',),(('verified_violation','valid_challenge'),),GradientEstimator.POLICY_GRADIENT,'challenges'),
 LossSpec('revision','sum(m*CE(revision_logits,verified_revision))/sum(m)','program revision CE','verified revision examples','revision_mask','skip_with_reason',('revision_selector',),('counterexample_features',),(),GradientEstimator.EXACT,'revisions'),
 LossSpec('legality','sum(m*BCE(validity_logits,executable))/sum(m)','executable validity CE','labeled challenge programs','legality_mask','skip_with_reason',('critic_validity_head',),('program_features',),(),GradientEstimator.EXACT,'challenge programs'))
def tensor_losses(logp,verified_reward,revision_logits,revision_labels,validity_logits,validity_labels,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'valid_challenge':masked_tensor_mean(-logp*verified_reward.detach(),masks[0]),'revision':masked_tensor_mean(torch.nn.functional.cross_entropy(revision_logits,revision_labels,reduction='none'),masks[1]),'legality':masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(validity_logits,validity_labels,reduction='none'),masks[2])}
