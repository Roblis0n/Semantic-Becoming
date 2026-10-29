from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('branch_policy','-stopgrad(return-baseline)*log pi(branch)','sum of valid terms','count of valid terms','selected_valid','differentiable_zero',('mechanism_writer',),('logprob',),(('returns', 'target_or_return'), ('baseline', 'target_or_return')),GradientEstimator.POLICY_GRADIENT,'branch decisions'),
    LossSpec('counterfactual_task','mean_valid loss from executable branch task','sum of valid terms','count of valid terms','branch_valid','differentiable_zero',('mechanism_reader',),('branch_task_losses',),(),GradientEstimator.EXACT,'branch tasks'),
)

def tensor_losses(logprob,returns,baseline,selected_valid,branch_task_losses,branch_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    return {'branch_policy':masked_tensor_mean(-logprob*(returns-baseline).detach(),selected_valid,zero_valid_policy='differentiable_zero'),'counterfactual_task':masked_tensor_mean(branch_task_losses,branch_valid,zero_valid_policy='differentiable_zero')}
