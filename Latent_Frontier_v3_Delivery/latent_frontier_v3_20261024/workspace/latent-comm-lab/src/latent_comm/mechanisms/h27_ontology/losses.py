"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('distinction','sum(m*relu(margin-abs(ca-cb)))/sum(m)','pair margin deficit','known required pairs','pair_known_mask','skip_with_reason',('concept_thresholds',),('concept_values',),(),GradientEstimator.EXACT,'pairs'),
 LossSpec('behavior','sum(m*CE(action_logits,label))/sum(m)','supervisor-only action cross entropy','valid actions','action_mask','skip_with_reason',('concept_thresholds','behavior_readout'),('concept_values',),(),GradientEstimator.EXACT,'actions'),
 LossSpec('description','UTF8_prefix_AST_bytes','actual prefix-encoded AST byte length','one candidate','candidate_valid','error',(),(),(),GradientEstimator.ENUMERATION,'bytes'),
 LossSpec('drift','sum(m*(new_old_domain-old)^2)/sum(m)','historical-domain response change','valid historical values','old_domain_mask','skip_with_reason',('concept_thresholds',),('new_response',),(('old_response','drift'),),GradientEstimator.EXACT,'historical examples'))
def tensor_losses(pair_a,pair_b,pair_mask,action_logits,action_labels,action_mask,new_response,old_response,old_mask,margin=.5):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'distinction':masked_tensor_mean(torch.relu(margin-(pair_a-pair_b).abs()),pair_mask),'behavior':masked_tensor_mean(torch.nn.functional.cross_entropy(action_logits,action_labels,reduction='none'),action_mask),'drift':masked_tensor_mean((new_response-old_response.detach()).square(),old_mask)}
