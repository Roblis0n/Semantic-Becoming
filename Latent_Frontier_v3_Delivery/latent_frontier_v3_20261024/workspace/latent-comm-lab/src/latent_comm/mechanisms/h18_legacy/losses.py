from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('structure_policy','-log p(selected graph)*(reward-baseline)','sum of valid terms','count of valid terms','valid','differentiable_zero',('topology_controller',),('log_probability',),(('reward', 'target_or_return'), ('baseline', 'target_or_return')),GradientEstimator.POLICY_GRADIENT,'graphs'),
    LossSpec('task_cost','task loss + lambda total actually executed cost','sum of valid terms','count of valid terms','stage-normalized valid tasks; actual_cost is executed-cost diagnostic','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'tasks'),
)

def tensor_losses(log_probability,reward,baseline,valid,*,task_loss,actual_cost,cost_weight=.01):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.core.learning import masked_tensor_mean
    policy=masked_tensor_mean(-log_probability*(reward-baseline).detach(),valid,zero_valid_policy='differentiable_zero')
    return {'total':task_loss+policy+cost_weight*actual_cost,'structure_policy':policy,'task_cost':task_loss+cost_weight*actual_cost,'actual_executed_cost':actual_cost}
