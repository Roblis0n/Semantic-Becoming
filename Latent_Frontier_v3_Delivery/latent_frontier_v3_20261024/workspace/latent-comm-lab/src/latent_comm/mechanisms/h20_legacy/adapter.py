from latent_comm.core import ContractError

def event_policy(features,weights,bias,eligible,*,sampling,return_logits=False):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if features.ndim!=3 or eligible.shape!=features.shape[:2]:raise ContractError('ShapeMismatch','events [B,E,F], eligibility [B,E]')
    logits=(features@weights).squeeze(-1)+bias;has_event=eligible.any(-1)
    masked=logits.masked_fill(~eligible,float('-inf'));safe=torch.where(has_event[:,None],masked,torch.zeros_like(masked))
    distribution=torch.distributions.Categorical(logits=safe)
    selected=distribution.sample() if sampling else safe.argmax(-1)
    selected=torch.where(has_event,selected,torch.full_like(selected,-1))
    logprob=distribution.log_prob(selected.clamp_min(0))*has_event
    return (selected,logprob,has_event,logits) if return_logits else (selected,logprob,has_event)

def version_gated_merge(current,delta,version_match,dependency_ready,*,gain):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    valid=version_match&dependency_ready
    return current+torch.where(valid[...,None],gain*delta,torch.zeros_like(delta)),valid
