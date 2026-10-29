"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=(
 LossSpec('covariance','sum(mask * (Pprime Gi z - Gj P z)^2)/sum(mask)','squared transported coordinate residual','valid state elements','state_element_mask','skip_with_reason',('cross_map','read_write_heads'),('state','cross_map'),(),GradientEstimator.EXACT,'state elements'),
 LossSpec('effect','sum(mask * (rprime Tprime zprime-r T z)^2)/sum(mask)','squared public behavior residual','valid behavior elements','behavior_mask','skip_with_reason',('cross_map','read_write_heads'),('state','operator','readout'),(),GradientEstimator.EXACT,'public behavior elements'))

def tensor_losses(covariance_residual,effect_residual,state_mask,behavior_mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'covariance':masked_tensor_mean(covariance_residual.square(),state_mask),'effect':masked_tensor_mean(effect_residual.square(),behavior_mask)}
