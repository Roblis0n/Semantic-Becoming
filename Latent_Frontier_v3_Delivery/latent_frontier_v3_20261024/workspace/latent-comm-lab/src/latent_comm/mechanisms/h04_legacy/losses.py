from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','stage normalized task loss after dedicated mechanism','sum valid task losses','valid task count','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('local','mean residual_fit_error^2','sum of valid terms','count of valid terms','local_valid','differentiable_zero',('mechanism_writer',),('residual_prediction',),(('residual_teacher', 'target_or_return'),),GradientEstimator.EXACT,'residual elements'),
    LossSpec('stability','mean relu(E[t+1]-E[t])','sum of valid terms','count of valid terms','step_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('energies',),(),GradientEstimator.EXACT,'steps'),
    LossSpec('conflict','BCE(conflict_logit,known_inconsistency)','sum of valid terms','count of valid terms','conflict_valid','differentiable_zero',('mechanism_reader',),('conflict_logits',),(('conflict_targets', 'target_or_return'),),GradientEstimator.EXACT,'fields'),
)

def tensor_losses(residual_prediction,residual_teacher,local_valid,energies,step_valid,conflict_logits,conflict_targets,conflict_valid,*,task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean as mean
    local=mean((residual_prediction-residual_teacher.detach()).square(),local_valid,zero_valid_policy='differentiable_zero')
    stability=mean((energies[:,1:]-energies[:,:-1]).relu(),step_valid,zero_valid_policy='differentiable_zero')
    conflict=mean(torch.nn.functional.binary_cross_entropy_with_logits(conflict_logits,conflict_targets.detach(),reduction='none'),conflict_valid,zero_valid_policy='differentiable_zero')
    return {'task':task_loss,'total':task_loss+local+stability+conflict,'local':local,'stability':stability,'conflict':conflict}
