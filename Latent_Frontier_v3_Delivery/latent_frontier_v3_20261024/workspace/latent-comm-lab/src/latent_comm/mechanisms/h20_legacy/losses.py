from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','externally normalized task loss after causally eligible event','sum of valid terms','count of valid terms','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('event_supervision','cross entropy over eligible event candidates','sum of valid terms','count of valid terms','valid & eligible.any(-1)','differentiable_zero',('mechanism_writer',),('logits',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'event decisions'),
    LossSpec('event_policy','-stopgrad(advantage)*log pi(selected eligible event)','sum of valid terms','count of valid terms','selected_valid','differentiable_zero',('mechanism_writer',),('selected_logprob',),(('advantage', 'target_or_return'),),GradientEstimator.POLICY_GRADIENT,'event decisions'),
)

def tensor_losses(logits,target,valid,eligible,selected_logprob,advantage,selected_valid,task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    active=valid&eligible.any(-1);safe_logits=torch.where(active[:,None],logits.masked_fill(~eligible,-torch.inf),torch.zeros_like(logits));safe_targets=torch.where(active,target,torch.zeros_like(target))
    if bool((active&~eligible.gather(-1,safe_targets[:,None]).squeeze(-1)).any()):raise ContractError('NoEligibleEvent','supervised event cannot be causally ineligible')
    ce=torch.nn.functional.cross_entropy(safe_logits,safe_targets,reduction='none')
    return {'event_supervision':masked_tensor_mean(ce,active,zero_valid_policy='differentiable_zero'),'event_policy':masked_tensor_mean(-selected_logprob*advantage.detach(),selected_valid,zero_valid_policy='differentiable_zero'),'task':task_loss}
