from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('distillation','mean_valid ||student_without_message - stopgrad(teacher_with_message)||^2','sum of valid per-probe mean coordinate errors','count of valid probes','valid','differentiable_zero',('mechanism_reader',),('student',),(('teacher', 'target_or_return'),),GradientEstimator.EXACT,'probes, each averaged over coordinates'),
    LossSpec('operation_behavior','mean_valid ||student(compose(a,b),x)-teacher(b,teacher(a,x))||^2','sum of valid per-probe mean coordinate errors','count of valid probes','operation_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('operation_student',),(('operation_teacher', 'target_or_return'),),GradientEstimator.EXACT,'probes, each averaged over coordinates'),
)

def tensor_losses(student,teacher,valid,operation_student,operation_teacher,operation_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from latent_comm.core.learning import masked_tensor_mean
    behavior=(student-teacher.detach()).square().mean(-1)
    relation=(operation_student-operation_teacher.detach()).square().mean(-1)
    return {'distillation':masked_tensor_mean(behavior,valid,zero_valid_policy='differentiable_zero'),'operation_behavior':masked_tensor_mean(relation,operation_valid,zero_valid_policy='differentiable_zero')}
