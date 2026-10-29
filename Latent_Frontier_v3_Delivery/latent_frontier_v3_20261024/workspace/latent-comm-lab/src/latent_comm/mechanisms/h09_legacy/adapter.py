from latent_comm.core import ContractError

def tensor_intervene(order,parents,noise_indices,coefficients,bias,noise_weights,noise,interventions,*,allowed_targets):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if noise.ndim!=2 or len(set(order))!=len(order) or set(interventions)-set(order) or set(interventions)-set(allowed_targets):raise ContractError('ScopeViolation','noise [B,U] and legal interventions required')
    values={}
    for node in order:
        if node in interventions:
            value=interventions[node]
            if value.shape!=(noise.shape[0],):raise ContractError('DimensionMismatch','intervention [B]')
        else:
            if any(p not in values for p in parents[node]):raise ContractError('CausalCycle','topological parent values required')
            value=bias[node].expand(noise.shape[0])
            if parents[node]:value=value+(torch.stack([values[p] for p in parents[node]],-1)*coefficients[node]).sum(-1)
            if noise_indices[node]:value=value+(noise[:,noise_indices[node]]*noise_weights[node]).sum(-1)
        values[node]=value
    return torch.stack([values[node] for node in order],-1)
