from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','stage normalized task loss after dedicated mechanism','sum valid task losses','valid task count','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('relation','mean ||P A_target P^T-A_source||^2','sum of valid terms','count of valid terms','edge_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('transported_relations',),(('source_relations', 'target_or_return'),),GradientEstimator.EXACT,'edges'),
    LossSpec('matching','-log sum probability over symmetry-valid matches','sum of valid terms','count of valid terms','node_valid','differentiable_zero',('mechanism_writer',),('matching_probability',),(('equivalent_targets', 'target_or_return'),),GradientEstimator.EXACT,'nodes'),
)

def tensor_losses(transported_relations,source_relations,edge_valid,matching_probability,equivalent_targets,node_valid,*,task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.core.learning import masked_tensor_mean as mean
    relation=mean((transported_relations-source_relations.detach()).square(),edge_valid,zero_valid_policy='differentiable_zero')
    matching=mean(-(matching_probability*equivalent_targets.detach()).sum(-1).clamp_min(1e-12).log(),node_valid,zero_valid_policy='differentiable_zero')
    return {'task':task_loss,'total':task_loss+relation+matching,'relation':relation,'matching':matching}
