"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('conflict_prediction','sum(m*BCE(logit,conflict))/sum(m)','conflict prediction CE','valid completed transaction outcomes','outcome_mask','skip_with_reason',('commit_policy',),('conflict_features',),(),GradientEstimator.EXACT,'transactions'),
 LossSpec('redo_cost','sum(m*(predicted_cost-actual_cost)^2)/sum(m)','redo cost prediction residual','valid retry outcomes','retry_mask','skip_with_reason',('cost_predictor',),('cost_features',),(),GradientEstimator.EXACT,'transactions'))
CORE_CORRECTNESS='deterministic version/type/scope checks; no trainable bypass'
def tensor_losses(conflict_logits,conflict_labels,cost_prediction,cost_target,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'conflict_prediction':masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(conflict_logits,conflict_labels,reduction='none'),masks[0]),'redo_cost':masked_tensor_mean((cost_prediction-cost_target).square(),masks[1])}
