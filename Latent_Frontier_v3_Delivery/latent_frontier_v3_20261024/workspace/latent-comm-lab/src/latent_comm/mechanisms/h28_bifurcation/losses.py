"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('task','sum(m*task_error)/sum(m)','task-conditioned error','valid tasks','task_mask','skip_with_reason',('potential_coefficients','readout'),('trajectory',),(),GradientEstimator.EXACT,'tasks'),
 LossSpec('migration','sum(m*(after_readout-before_readout)^2)/sum(m)','behavior change under structure migration','valid public behavior elements','behavior_mask','skip_with_reason',('structure_map',),('before_state','after_state'),(),GradientEstimator.EXACT,'behavior elements'),
 LossSpec('event','sum(m*CE(trigger_logits,event))/sum(m)','supervised structure event cross entropy','valid events','event_mask','skip_with_reason',('trigger_policy',),('stability_features',),(),GradientEstimator.EXACT,'events'))
def tensor_losses(task_errors,before,after,event_logits,event_labels,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'task':masked_tensor_mean(task_errors,masks[0]),'migration':masked_tensor_mean((after-before).square(),masks[1]),'event':masked_tensor_mean(torch.nn.functional.cross_entropy(event_logits,event_labels,reduction='none'),masks[2])}
