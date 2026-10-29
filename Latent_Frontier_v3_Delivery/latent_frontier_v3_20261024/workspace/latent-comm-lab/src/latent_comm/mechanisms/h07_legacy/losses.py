from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('structure','CE(allowed_opcode_logits,supervised_opcode)','sum of valid terms','count of valid terms','node_valid & legal opcode','differentiable_zero',('mechanism_writer',),('opcode_logits',),(('opcode_targets', 'target_or_return'),),GradientEstimator.EXACT,'nodes'),
    LossSpec('parameters','task loss through fixed typed program','sum of valid terms','count of valid terms','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'tasks'),
)

def tensor_losses(opcode_logits,opcode_targets,node_valid,allowed,*,task_loss):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    if allowed.shape!=opcode_logits.shape or node_valid.shape!=opcode_targets.shape or bool((node_valid.bool()&~allowed.any(-1)).any()):raise ContractError('NoLegalOpcode','each valid grammar node must have a legal candidate')
    safe_targets=torch.where(node_valid.bool(),opcode_targets.detach(),torch.zeros_like(opcode_targets))
    if bool((node_valid.bool()&~allowed.gather(-1,safe_targets.unsqueeze(-1)).squeeze(-1).bool()).any()):raise ContractError('NoLegalOpcode','supervised opcode outside typed grammar')
    logits=torch.where(node_valid.bool().unsqueeze(-1),opcode_logits.masked_fill(~allowed.bool(),-torch.inf),torch.zeros_like(opcode_logits))
    error=torch.nn.functional.cross_entropy(logits.flatten(0,-2),safe_targets.flatten(),reduction='none').reshape(opcode_targets.shape)
    structure=masked_tensor_mean(error,node_valid,zero_valid_policy='differentiable_zero')
    return {'total':task_loss+structure,'structure':structure,'parameters':task_loss}
