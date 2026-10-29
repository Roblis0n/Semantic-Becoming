"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('fast_behavior','sum(m*(fast_mu(x)-Exec_base(lower(mu),x))^2)/sum(m)','fast implementation anchor error','valid declared behavior anchors','anchor_mask','skip_with_reason',('fast_macro_coefficients',),('macro_inputs',),(('exact_base_target','fast_behavior'),),GradientEstimator.EXACT,'behavior anchors'),
 LossSpec('description','encoded_original_bytes-encoded_definition_bytes-encoded_calls_bytes','actual byte savings','one candidate library','candidate_valid','error',(),(),(),GradientEstimator.ENUMERATION,'bytes'),
 LossSpec('binding','sum(m*CE(binding_logits,binding))/sum(m)','typed argument binding CE','valid macro calls','call_mask','skip_with_reason',('binding_selector',),('program_features',),(),GradientEstimator.EXACT,'macro calls'))
def tensor_losses(fast,base_target,binding_logits,binding_labels,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'fast_behavior':masked_tensor_mean((fast-base_target.detach()).square(),masks[0]),'binding':masked_tensor_mean(torch.nn.functional.cross_entropy(binding_logits,binding_labels,reduction='none'),masks[1])}
