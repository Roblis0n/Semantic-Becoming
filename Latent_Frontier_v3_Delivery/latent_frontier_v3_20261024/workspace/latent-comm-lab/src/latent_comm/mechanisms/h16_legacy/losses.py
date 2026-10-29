from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('conflict','BCE(conflict_logits,verified symbol-latent contradiction)','sum of valid terms','count of valid terms','conflict_valid','differentiable_zero',('mechanism_reader',),('conflict_logits',),(('conflict_labels', 'target_or_return'),),GradientEstimator.EXACT,'symbol conflicts'),
    LossSpec('symbol_structure','CE(predicted exact-field category,true category)','sum of valid terms','count of valid terms','symbol_valid','differentiable_zero',('symbol_predictor',),('symbol_logits',),(('symbol_labels', 'target_or_return'),),GradientEstimator.EXACT,'fields'),
    LossSpec('latent_behavior','task loss conditioned on verified symbols','sum of valid terms','count of valid terms','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('latent_task_loss',),(),GradientEstimator.EXACT,'tasks'),
)

def tensor_losses(symbol_logits,symbol_labels,symbol_valid,conflict_logits,conflict_labels,conflict_valid,*,latent_task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean as mean
    safe_labels=torch.where(symbol_valid.bool(),symbol_labels.detach(),torch.zeros_like(symbol_labels));safe_logits=torch.where(symbol_valid.bool().unsqueeze(-1),symbol_logits,torch.zeros_like(symbol_logits))
    symbol=mean(torch.nn.functional.cross_entropy(safe_logits.flatten(0,-2),safe_labels.flatten(),reduction='none').reshape(symbol_labels.shape),symbol_valid,zero_valid_policy='differentiable_zero')
    conflict=mean(torch.nn.functional.binary_cross_entropy_with_logits(conflict_logits,conflict_labels.detach(),reduction='none'),conflict_valid,zero_valid_policy='differentiable_zero')
    return {'total':latent_task_loss+symbol+conflict,'symbol_structure':symbol,'latent_behavior':latent_task_loss,'conflict':conflict}
