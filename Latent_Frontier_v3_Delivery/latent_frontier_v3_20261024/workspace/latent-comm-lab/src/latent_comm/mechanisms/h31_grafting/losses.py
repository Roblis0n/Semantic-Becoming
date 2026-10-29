"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('graft','sum(m*(grafted_effect-intervention_target)^2)/sum(m)','interventional effect residual','valid effect coordinates','intervention_mask','skip_with_reason',('source_module_generator','boundary_reader'),('boundary_inputs',),(),GradientEstimator.EXACT,'intervention effects'),
 LossSpec('boundary','sum(m*(unchanged_after-unchanged_before)^2)/sum(m)','external invariant residual','valid boundary invariants','boundary_mask','skip_with_reason',('boundary_reader',),('grafted_state',),(('unchanged_before','boundary'),),GradientEstimator.EXACT,'boundary coordinates'))
def tensor_losses(effect,target,after,before,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'graft':masked_tensor_mean((effect-target).square(),masks[0]),'boundary':masked_tensor_mean((after-before.detach()).square(),masks[1])}
