"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('link','sum(mask*BCEWithLogits(source_link_logits,shared_source))/sum(mask)','source-identity link BCE','labelled source pairs including circular negative cases','link_mask','skip_with_reason',('source_linker',),('source_link_logits',),(('source_identity_labels','link'),),GradientEstimator.EXACT,'source_pairs'),
 LossSpec('calibration','sum(mask*(predicted_support-observed_support)^2)/sum(mask)','Brier calibration conditional on named dependence model','independent heldout outcomes','calibration_mask','skip_with_reason',('source_calibrator',),('atom_probabilities',),(('observed_support','calibration'),('declared_dependence','calibration')),GradientEstimator.EXACT,'claims'))
def link_loss(logits,labels,mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(logits,labels.detach(),reduction='none'),mask)
def calibration_loss(support,outcomes,mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return masked_tensor_mean((support-outcomes.detach()).square(),mask)
