from latent_comm.core import ContractError

def tensor_hyperedges(states,hyperedges,projections,readouts,present):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    outputs=[];validity=[]
    for e,members in enumerate(hyperedges):
        if len(members)<2 or len(members)!=len(projections[e]):raise ContractError('InvalidHyperedge','joint factor requires all declared member roles')
        factors=[states[m]@p.T for m,p in zip(members,projections[e])]
        if len({tuple(f.shape) for f in factors})!=1:raise ContractError('DimensionMismatch','projected hyperedge rank/batch')
        joint=torch.stack(factors,1).prod(1);valid=torch.stack([present[m].bool() for m in members],-1).all(-1)
        outputs.append(joint@readouts[e].T);validity.append(valid)
    return tuple(outputs),tuple(validity)
