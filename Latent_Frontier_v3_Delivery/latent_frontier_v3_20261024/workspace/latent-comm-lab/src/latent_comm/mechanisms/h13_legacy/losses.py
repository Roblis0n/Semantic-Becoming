from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','stage normalized task loss after dedicated mechanism','sum valid task losses','valid task count','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('merge','mean ||merged-serial||^2','sum of valid terms','count of valid terms','merge_valid','differentiable_zero',('mechanism_reader',),('merged',),(('serial', 'target_or_return'),),GradientEstimator.EXACT,'slot elements'),
    LossSpec('conflict','BCE(conflict_prediction,scope_conflict)','sum of valid terms','count of valid terms','conflict_valid','differentiable_zero',('branch_router',),('conflict_logits',),(('conflict_target', 'target_or_return'),),GradientEstimator.EXACT,'branch pairs'),
)

def tensor_losses(merged,serial,merge_valid,conflict_logits,conflict_target,conflict_valid,*,task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean as mean
    behavior=mean((merged-serial.detach()).square(),merge_valid,zero_valid_policy='differentiable_zero')
    conflict=mean(torch.nn.functional.binary_cross_entropy_with_logits(conflict_logits,conflict_target.detach(),reduction='none'),conflict_valid,zero_valid_policy='differentiable_zero')
    return {'task':task_loss,'total':task_loss+behavior+conflict,'merge':behavior,'conflict':conflict}
