"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('legality','sum(m*BCE(legal_logits,structural_valid))/sum(m)','world structural-validity CE','checked world proposals','world_mask','skip_with_reason',('world_proposer',),('kernel_features',),(),GradientEstimator.EXACT,'proposals'),
 LossSpec('curriculum','sum(m*synthetic_task_loss)/sum(m)','synthetic task loss with parent lineage','valid synthetic tasks','synthetic_mask','skip_with_reason',('protocol_interface',),('role_views',),(),GradientEstimator.EXACT,'synthetic tasks'),
 LossSpec('heldout_proposal','log_pi(world)*stopgrad(L_independent_holdout)','world score times held-out loss','valid proposals with independent holdout','holdout_mask','skip_with_reason',('world_proposer',),('world_log_probability',),(('independent_holdout_loss','heldout_proposal'),),GradientEstimator.POLICY_GRADIENT,'independent held-out tasks'))
def tensor_losses(legality_logits,valid_labels,synthetic_errors,logp,holdout_errors,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'legality':masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(legality_logits,valid_labels,reduction='none'),masks[0]),'curriculum':masked_tensor_mean(synthetic_errors,masks[1]),'heldout_proposal':masked_tensor_mean(logp*holdout_errors.detach(),masks[2])}
