from latent_comm.core import ContractError

def tensor_field(anchor,matrices,targets,temperatures,anchor_strength,*,steps,step_size,nonlinear=False):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if anchor.ndim!=2 or matrices.ndim!=4:raise ContractError('DimensionMismatch','anchor [B,D], constraints [B,S,R,D]')
    B,D=anchor.shape;_,S,R,_=matrices.shape
    if matrices.shape[0]!=B or matrices.shape[-1]!=D or targets.shape!=(B,S,R) or temperatures.shape!=(B,S) or bool((temperatures<=0).any()) or anchor_strength<=0 or steps<=0:raise ContractError('InvalidConstraint','shape/positive contribution/finite iteration contract')
    if step_size<=0:raise ContractError('UnstableStep','positive step required')
    # Normalize nonlinear residual maps by row norm; source temperatures remain explicit.
    A=matrices/matrices.norm(dim=-1,keepdim=True).clamp_min(1.) if nonlinear else matrices
    z=anchor if anchor.requires_grad else anchor.clone().requires_grad_(True);trajectory=[z]
    for _ in range(steps):
        projected=torch.einsum('bsrd,bd->bsr',A,z)
        residual=(projected.tanh() if nonlinear else projected)-targets
        energy=.5*(temperatures[:,:,None]*residual.square()).sum()+anchor_strength*(z-anchor).square().sum()
        gradient=torch.autograd.grad(energy,z,create_graph=True)[0]
        z=z-step_size*gradient;trajectory.append(z)
    residual=torch.einsum('bsrd,bd->bsr',A,z)
    residual=(residual.tanh() if nonlinear else residual)-targets
    return z,residual,torch.stack(trajectory,1)
