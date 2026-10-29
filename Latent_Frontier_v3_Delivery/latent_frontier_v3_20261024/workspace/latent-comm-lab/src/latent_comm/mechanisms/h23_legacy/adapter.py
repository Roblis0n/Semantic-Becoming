from latent_comm.core import ContractError

def encode_repair(public_sender_features,permitted_summary,probe_response,*,ridge):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if ridge<=0:raise ContractError('InvalidRegularization','positive regularization for bounded local inverse')
    # [B,P,D] public probe-response map; summary contains only approved P residuals.
    if probe_response.shape[:2]!=permitted_summary.shape or public_sender_features.shape[0]!=permitted_summary.shape[0]:raise ContractError('ShapeMismatch','permitted probe axes')
    jt=probe_response.transpose(-1,-2);normal=jt@probe_response+ridge*torch.eye(probe_response.shape[-1],device=probe_response.device,dtype=probe_response.dtype)
    delta=torch.linalg.solve(normal,-(jt@permitted_summary.unsqueeze(-1))).squeeze(-1)
    remaining=permitted_summary+(probe_response@delta.unsqueeze(-1)).squeeze(-1)
    return delta,remaining

def no_repair_gate(residual_features,weights,bias,numeric_domain_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    logit=(residual_features@weights).squeeze(-1)+bias
    return torch.sigmoid(logit)*numeric_domain_valid,logit
