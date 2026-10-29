from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('scoped_effect','mean_valid squared proposed effects in forbidden coordinates','sum of valid terms','count of valid terms','(~write_mask).expand_as(proposed_delta) & coordinate_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('proposed_delta',),(),GradientEstimator.EXACT,'protected coordinates'),
    LossSpec('task','mean_valid task loss after structurally masked operation','sum of valid terms','count of valid terms','task_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_losses',),(),GradientEstimator.EXACT,'task instances'),
)

def tensor_losses(proposed_delta,write_mask,coordinate_valid,task_losses,task_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    forbidden=(~write_mask).expand_as(proposed_delta)&coordinate_valid
    return {'scoped_effect':masked_tensor_mean(proposed_delta.square(),forbidden,zero_valid_policy='differentiable_zero'),'task':masked_tensor_mean(task_losses,task_valid,zero_valid_policy='differentiable_zero')}
