"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=tuple(LossSpec(name,formula,'sum of valid per-element errors','valid elements',mask,'skip_with_reason',owners,inputs,(),GradientEstimator.EXACT,units) for name,formula,mask,owners,inputs,units in (
 ('matching','sum(mask*(-log P(correct_object)))/sum(mask)','known_match_mask',('matching_logits',),('source_features','target_features'),'matched objects'),
 ('commutation','sum(mask*(F A-B F)^2)/sum(mask)','declared_square_mask',('object_map','operation_map'),('source_operation','target_operation'),'commuting-square elements'),
 ('behavior','sum(mask*(target_effect-supervised_effect)^2)/sum(mask)','target_behavior_mask',('object_map','target_readout'),('target_state',),'target behavior elements')))
def tensor_losses(match_probability,commuting_residual,behavior_residual,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    return {'matching':masked_tensor_mean(-match_probability.clamp_min(1e-12).log(),masks[0]),'commutation':masked_tensor_mean(commuting_residual.square(),masks[1]),'behavior':masked_tensor_mean(behavior_residual.square(),masks[2])}
