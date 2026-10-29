from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('joint','mean CE(joint output,task)','sum of valid terms','count of valid terms','valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('joint_logits',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'tasks'),
    LossSpec('dropout','mean task error under declared source subsets','sum of valid terms','count of valid terms','subset_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('subset_logits',),(('subset_targets', 'target_or_return'),),GradientEstimator.EXACT,'subsets'),
)

def tensor_losses(joint_logits,target,valid,subset_logits,subset_targets,subset_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean as mean
    safe_target=torch.where(valid.bool(),target.detach(),torch.zeros_like(target));safe_subset=torch.where(subset_valid.bool(),subset_targets.detach(),torch.zeros_like(subset_targets))
    joint_logits=torch.where(valid.bool().unsqueeze(-1),joint_logits,torch.zeros_like(joint_logits));subset_logits=torch.where(subset_valid.bool().unsqueeze(-1),subset_logits,torch.zeros_like(subset_logits))
    joint=mean(torch.nn.functional.cross_entropy(joint_logits,safe_target,reduction='none'),valid,zero_valid_policy='differentiable_zero')
    dropout=mean(torch.nn.functional.cross_entropy(subset_logits.flatten(0,-2),safe_subset.flatten(),reduction='none').reshape(subset_targets.shape),subset_valid,zero_valid_policy='differentiable_zero')
    return {'total':joint+dropout,'joint':joint,'dropout':dropout}
