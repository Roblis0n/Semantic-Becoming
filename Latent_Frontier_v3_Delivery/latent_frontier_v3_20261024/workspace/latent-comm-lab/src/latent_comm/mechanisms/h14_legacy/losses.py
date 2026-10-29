from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('execution','mean squared expanded behavior-target','sum of valid terms','count of valid terms','behavior_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('behavior',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'behavior coordinates'),
    LossSpec('production','CE(typed_production_logits,label)','sum of valid terms','count of valid terms','valid','differentiable_zero',('grammar_proposer',),('production_logits',),(('labels', 'target_or_return'),),GradientEstimator.EXACT,'productions'),
    LossSpec('rewrite','mean behavior difference for conditional equivalent rewrites','sum of valid terms','count of valid terms','rewrite_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('rewritten', 'original'),(),GradientEstimator.EXACT,'behavior elements'),
)

def tensor_losses(production_logits,labels,valid,behavior,target,behavior_valid,rewritten,original,rewrite_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean as mean
    safe_labels=torch.where(valid.bool(),labels.detach(),torch.zeros_like(labels));safe_logits=torch.where(valid.bool().unsqueeze(-1),production_logits,torch.zeros_like(production_logits))
    structure=mean(torch.nn.functional.cross_entropy(safe_logits,safe_labels,reduction='none'),valid,zero_valid_policy='differentiable_zero')
    execution=mean((behavior-target.detach()).square(),behavior_valid,zero_valid_policy='differentiable_zero')
    rewrite=mean((rewritten-original).square(),rewrite_valid,zero_valid_policy='differentiable_zero')
    return {'total':structure+execution+rewrite,'production':structure,'execution':execution,'rewrite':rewrite}
