from latent_comm.core import ContractError

def partition_controller(node_features,edge_cost,weights,allowed,*,mode):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    logits=node_features@weights-edge_cost;valid=allowed.any(-1)
    safe=torch.where(valid[...,None],logits.masked_fill(~allowed,-torch.inf),torch.zeros_like(logits))
    probabilities=torch.softmax(safe,-1)*valid[...,None]
    if mode=='soft':return probabilities,valid,'soft_all_candidate_cost'
    if mode=='sample':
        distribution=torch.distributions.Categorical(logits=safe)
        choice=distribution.sample();logprob=distribution.log_prob(choice)*valid
        assignment=torch.nn.functional.one_hot(choice,safe.shape[-1]).to(safe.dtype)*valid[...,None]
        return assignment,logprob,valid,'sampled_hard_selected_graph_cost'
    if mode!='hard':raise ContractError('InvalidController','soft, deterministic hard and sampled policy paths explicitly separate')
    selection=safe.argmax(-1);assignment=torch.nn.functional.one_hot(selection,safe.shape[-1]).to(safe.dtype)*valid[...,None]
    return assignment,valid,'hard_selected_graph_cost'

def migrate_handoff_state(state,mapping,*,source_frame,target_frame,contract):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if (source_frame,target_frame)!=(contract.source_frame,contract.target_frame):raise ContractError('FrameMismatch','handoff cannot reinterpret coordinates')
    return state@mapping.transpose(-1,-2)
