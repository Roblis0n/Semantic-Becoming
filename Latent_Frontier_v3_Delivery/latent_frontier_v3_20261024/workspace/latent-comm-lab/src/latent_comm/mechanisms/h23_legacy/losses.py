from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('unnecessary_change','mean squared correction norm on clean packets','sum of valid terms','count of valid terms','normal_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('delta',),(),GradientEstimator.EXACT,'clean packets'),
    LossSpec('repair_behavior','mean_valid ||behavior_after-stopgrad(correct_behavior)||^2','sum of valid per-probe mean coordinate errors','count of valid probes','probe_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('after',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'probes, each averaged over coordinates'),
    LossSpec('no_repair_gate','binary cross entropy repair/no-repair on both normal and corrupted messages','sum of valid terms','count of valid terms','gate_valid','differentiable_zero',('mechanism_writer',),('gate_logits',),(('needs_repair', 'target_or_return'),),GradientEstimator.EXACT,'messages'),
)

def tensor_losses(after,target,probe_valid,gate_logits,needs_repair,gate_valid,delta,normal_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    gate=torch.nn.functional.binary_cross_entropy_with_logits(gate_logits,needs_repair.detach().to(gate_logits.dtype),reduction='none')
    return {'repair_behavior':masked_tensor_mean((after-target.detach()).square().mean(-1),probe_valid,zero_valid_policy='differentiable_zero'),'no_repair_gate':masked_tensor_mean(gate,gate_valid,zero_valid_policy='differentiable_zero'),'unnecessary_change':masked_tensor_mean(delta.square().sum(-1),normal_valid,zero_valid_policy='differentiable_zero')}
