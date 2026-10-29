"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def functional_behavior(model,parameter_layout,public_inputs,public_readout,scoped_vector):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from torch.func import functional_call
    from latent_comm.core.views import RoleView
    # public_inputs is a pair (validated RoleView, tensor-only public probe arguments).
    view,probe_kwargs=public_inputs
    if not isinstance(view,RoleView):raise ContractError('AnchorMismatch','public probes require a physically projected role view')
    parameters=dict(model.named_parameters());cursor=0
    for name,shape in parameter_layout:
        if not name.startswith(('adapter.','reader.')) or name not in parameters:raise ContractError('WriteScopeViolation','functional parameter outside explicit adapter scope')
        size=1
        for d in shape:size*=d
        parameters[name]=scoped_vector[cursor:cursor+size].reshape(shape);cursor+=size
    if cursor!=scoped_vector.numel():raise ContractError('InvalidShape','flattened parameter scope differs from layout')
    # No no_grad wrapper: frozen base weights must still preserve input gradients.
    output=functional_call(model,parameters,(),probe_kwargs)
    behavior=public_readout(output)
    if behavior.ndim!=1:raise ContractError('AnchorMismatch','readout must expose one named shared behavior vector')
    return behavior

def tensor_transport(source_behavior,target_behavior,source_parameters,source_direction,target_parameters,*,source_anchors,target_anchors,parameter_names,ridge=0.,max_steps=32,tolerance=1e-7):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from torch.func import jvp,vjp
    if source_anchors!=target_anchors:raise ContractError('AnchorMismatch','shared public anchors must be identical')
    if any(not n.startswith(('adapter.','reader.','external_state.')) for n in parameter_names):raise ContractError('WriteScopeViolation','target scope is not authorized')
    if source_parameters.ndim!=1 or target_parameters.ndim!=1 or source_direction.shape!=source_parameters.shape or ridge<0 or not 1<=max_steps<=128:raise ContractError('InvalidShape','explicit flat scoped parameter vectors and solver bounds required')
    _,desired=jvp(source_behavior,(source_parameters,),(source_direction,))
    target_value,pullback=vjp(target_behavior,target_parameters)
    if desired.ndim!=1 or target_value.shape!=desired.shape or desired.numel()!=len(source_anchors.coordinate_ids):raise ContractError('AnchorMismatch','behavior readouts do not expose shared named coordinates')
    def apply_j(delta):return jvp(target_behavior,(target_parameters,),(delta,))[1]
    def apply_jt(value):return pullback(value)[0]
    def solve_direction(lam):
        rhs=apply_jt(desired);x=torch.zeros_like(target_parameters);r=rhs;p=r;rr=torch.dot(r,r);iterations=0
        threshold=tolerance*max(1.,float(rhs.norm().detach()))
        for i in range(max_steps):
            if float(rr.detach().sqrt())<=threshold:break
            ap=apply_jt(apply_j(p))+lam*p;den=torch.dot(p,ap)
            if float(den.detach())<=0:raise ContractError('SolverTolerance','matrix-free normal operator is not positive on search direction')
            alpha=rr/den;x=x+alpha*p;r=r-alpha*ap;new_rr=torch.dot(r,r);iterations=i+1
            if float(new_rr.detach().sqrt())<=threshold:rr=new_rr;break
            p=r+(new_rr/rr)*p;rr=new_rr
        return x,iterations,rr.sqrt(),float(rr.detach().sqrt())<=threshold
    update,iterations,normal,converged=solve_direction(ridge)
    projected,_,projection_normal,projection_converged=solve_direction(0.) if ridge else (update,iterations,normal,converged)
    return {'update':update,'desired_behavior':desired,'effect_residual':apply_j(update)-desired,'unreachable_residual':apply_j(projected)-desired,'normal_residual':normal,'projection_normal_residual':projection_normal,'converged':converged,'projection_converged':projection_converged,'iterations':iterations,'rank':None,'rank_status':'not_identified_by_matrix_free_solver','minimum_norm_interpretation':ridge==0,'parameter_names':tuple(parameter_names)}
