"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('behavior','sum(mask*||predicted_query_response-target_query_response||^2)/sum(mask)','task behavior MSE, not input reconstruction','valid finite query responses','behavior_mask','skip_with_reason',('state_encoder','task_conditioner','prototypes'),('reconstructed_behavior',),(('behavior_targets','behavior'),),GradientEstimator.EXACT,'state_queries'),
 LossSpec('rate','sum(mask*KL(assignment||mean_assignment))/sum(mask)','soft information rate','valid states','state_mask','skip_with_reason',('state_encoder','task_conditioner','prototypes'),('assignments',),(),GradientEstimator.EXACT,'states'))
def tensor_losses(reconstructed,targets,assignments,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    state_mask=masks[1].to(assignments.dtype);count=state_mask.sum(-1,keepdim=True)
    marginal=(assignments*state_mask.unsqueeze(-1)).sum(-2)/count.clamp_min(1)
    rate=(assignments*(assignments.clamp_min(1e-12).log()-marginal[:,None,:].clamp_min(1e-12).log())).sum(-1)
    return {'behavior':masked_tensor_mean((reconstructed-targets.detach()).square(),masks[0]),'rate':masked_tensor_mean(rate,masks[1])}
