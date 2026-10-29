from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('partition_policy','-stopgrad(advantage)*log probability of authorized hard partition','sum of valid terms','count of valid terms','valid','differentiable_zero',('mechanism_writer',),('logprob',),(('advantage', 'target_or_return'),),GradientEstimator.POLICY_GRADIENT,'partition transitions'),
    LossSpec('handoff_behavior','mean ||behavior_after - stopgrad(behavior_before)||^2','sum of valid per-probe mean coordinate errors','count of valid probes','probe_valid','differentiable_zero',('mechanism_reader',),('after',),(('before', 'target_or_return'),),GradientEstimator.EXACT,'probes, each averaged over coordinates'),
)

def tensor_losses(logprob,advantage,valid,before,after,probe_valid,executed_cost,*,cost_weight):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    return {'partition_policy':masked_tensor_mean(-logprob*advantage.detach(),valid,zero_valid_policy='differentiable_zero'),'handoff_behavior':masked_tensor_mean((after-before.detach()).square().mean(-1),probe_valid,zero_valid_policy='differentiable_zero'),'executed_cost':cost_weight*executed_cost}
