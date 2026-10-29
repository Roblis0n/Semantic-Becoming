"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('exclusion','sum(mask*BCEWithLogits(predicate_logits,verified_exclusion))/sum(mask)','certificate-labelled predicate BCE','valid scoped finite predicate cases','predicate_mask','skip_with_reason',('exclusion_generator',),('predicate_logits',),(('verified_exclusion','exclusion'),),GradientEstimator.EXACT,'candidate_predicates'),
 LossSpec('scope','sum(mask*BCEWithLogits(scope_logits,scope_applies))/sum(mask)','scope applicability BCE','known assumption cases','scope_mask','skip_with_reason',('scope_predictor',),('scope_logits',),(('scope_applies','scope'),),GradientEstimator.EXACT,'scopes'))
def tensor_losses(predicate_logits,scope_logits,labels,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'exclusion':masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(predicate_logits,labels[0].detach(),reduction='none'),masks[0]),'scope':masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(scope_logits,labels[1].detach(),reduction='none'),masks[1])}
