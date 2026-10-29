from latent_comm.core import ContractError

def tensor_exchange(nodes,edge_index,edge_types,node_mask,edge_mask,relation_weights,*,rounds):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if nodes.ndim!=3 or edge_index.ndim!=3 or edge_index.shape[-1]!=2 or rounds<=0:raise ContractError('DimensionMismatch','nodes [B,N,D], edges [B,E,2]')
    B,N,D=nodes.shape;E=edge_index.shape[1]
    if edge_index.shape[0]!=B or edge_types.shape!=(B,E) or edge_mask.shape!=(B,E) or node_mask.shape!=(B,N) or relation_weights.shape[1:]!=(D,D):raise ContractError('DimensionMismatch','typed sparse graph axes')
    if bool(((edge_index<0)|(edge_index>=N)).any()) or bool(((edge_types<0)|(edge_types>=relation_weights.shape[0])).any()):raise ContractError('InvalidEdge','index out of declared bounds')
    src,dst=edge_index.unbind(-1);batch=torch.arange(B,device=nodes.device)[:,None]
    valid=edge_mask.bool()&node_mask[batch,src].bool()&node_mask[batch,dst].bool();z=nodes*node_mask[:,:,None]
    for _ in range(rounds):
        messages=torch.einsum('beij,bej->bei',relation_weights[edge_types],z[batch,src])*valid[:,:,None]
        aggregate=torch.zeros_like(z).scatter_add(1,dst[:,:,None].expand(B,E,D),messages)
        counts=torch.zeros(B,N,device=z.device,dtype=z.dtype).scatter_add(1,dst,valid.to(z.dtype))
        z=(z+aggregate/counts.clamp_min(1.)[:,:,None])*node_mask[:,:,None]
    return z

def soft_node_match(source,target,role_mask,*,iterations=8):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if source.ndim!=3 or target.ndim!=3 or source.shape[0]!=target.shape[0] or source.shape[2]!=target.shape[2] or role_mask.shape!=(source.shape[0],source.shape[1],target.shape[1]):raise ContractError('DimensionMismatch','pairwise role mask')
    if not bool(role_mask.any(-1).all()) or not bool(role_mask.any(-2).all()):raise ContractError('NoMatch','unmatched roles require a separate partial matching bucket')
    scores=torch.einsum('bid,bjd->bij',source,target)/(source.shape[-1]**.5);scores=scores.masked_fill(~role_mask,-torch.inf)
    for _ in range(iterations):scores=scores-torch.logsumexp(scores,-1,keepdim=True);scores=scores-torch.logsumexp(scores,-2,keepdim=True)
    return scores.exp() # Soft proposal; discrete execution rechecks all relation constraints.

def transport_relations(assignment,target_relations):
    """Push typed adjacency relations into source node order: P A_r P^T."""
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if assignment.ndim!=3 or target_relations.ndim!=4 or target_relations.shape[0]!=assignment.shape[0] or target_relations.shape[-2:]!=(assignment.shape[-1],assignment.shape[-1]):raise ContractError('DimensionMismatch','assignment [B,N,M], typed target adjacency [B,R,M,M]')
    return assignment[:,None]@target_relations@assignment[:,None].transpose(-1,-2)
