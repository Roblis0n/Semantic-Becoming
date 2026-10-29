"""Per-objective formulas and gradient owners. Research evaluation NOT_RUN."""
from latent_comm.core.learning import LossSpec, GradientEstimator, finite_masked_mean, masked_tensor_mean
from latent_comm.core import ContractError

LOSS_SPECS=tuple(LossSpec(name,formula,num,den,mask,'skip_with_reason',owners,inputs,(),GradientEstimator.EXACT,units) for name,formula,num,den,mask,owners,inputs,units in (
 ('local','sum(m*(prediction-evidence)^2)/sum(m)','local evidence residual squared','valid local elements','local_mask',('anchor_encoder',),('local_state',),'local evidence elements'),
 ('overlap','sum(m*(Ri zi-Rj zj-b)^2)/sum(m)','declared overlap residual squared','valid declared overlap elements','overlap_mask',('restriction_maps',),('local_state','restriction_maps'),'overlap elements'),
 ('obstruction','sum(m*BCEWithLogits(logit,conflict))/sum(m)','conflict classification cross entropy','valid graph labels','conflict_mask',('conflict_head',),('overlap_residual',),'graphs')))
def tensor_losses(local_residual,overlap_residual,conflict_logits,conflict_labels,masks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    return {'local':masked_tensor_mean(local_residual.square(),masks[0]),'overlap':masked_tensor_mean(overlap_residual.square(),masks[1]),'obstruction':masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(conflict_logits,conflict_labels,reduction='none'),masks[2])}
