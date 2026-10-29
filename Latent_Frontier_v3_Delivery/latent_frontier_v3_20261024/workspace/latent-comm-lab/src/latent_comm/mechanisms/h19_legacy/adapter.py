from latent_comm.core import ContractError

def teacher_student_outputs(teacher,student,public_inputs,message,adapter_parameters,*,allowed_names):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if set(adapter_parameters)!=set(allowed_names) or any(not n.startswith(('adapter.','reader.')) for n in allowed_names):raise ContractError('WriteScopeViolation','explicit student adapter parameter whitelist')
    # Only teacher is detached. Student input gradients remain live through a frozen base.
    with torch.no_grad():target=teacher(public_inputs,message).detach()
    prediction=student(public_inputs,adapter_parameters)
    return prediction,target

def operator_hypernetwork(operators,probe_states,projection_u,projection_v,projection_bias,*,rank):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.mechanisms.h01_legacy.adapter import tensor_operator
    if probe_states.ndim!=3 or not operators:raise ContractError('ShapeMismatch','ordered operations act on [B,P,D] public probes')
    state=probe_states
    for op in operators:state=torch.stack([tensor_operator(probe,**op) for probe in state.unbind(1)],1)
    # Ordered probe responses condition a dedicated factor hypernetwork, not summed factors.
    code=(state-probe_states).flatten(1);batch=code.shape[0];dim=probe_states.shape[-1]
    u=(code@projection_u).reshape(batch,dim,rank)
    v=(code@projection_v).reshape(batch,dim,rank)
    bias=code@projection_bias
    if bias.shape!=(batch,rank):raise ContractError('ShapeMismatch','generated low-rank adapter bias is rank-dimensional')
    return {'U':u,'V':v,'bias':bias,'alpha':torch.ones((batch,1),device=code.device,dtype=code.dtype)}

def functional_distillation_step(parameters,loss,*,allowed_names,learning_rate,create_graph=False):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    if learning_rate<=0 or set(parameters)!=set(allowed_names) or any(not n.startswith(('adapter.','reader.')) for n in allowed_names):raise ContractError('WriteScopeViolation','bounded named adapter update only')
    gradients=torch.autograd.grad(loss,tuple(parameters.values()),create_graph=create_graph,allow_unused=True)
    return {name:value if gradient is None else value-learning_rate*gradient for (name,value),gradient in zip(parameters.items(),gradients)}
