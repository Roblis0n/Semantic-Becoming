from latent_comm.core import ContractError

def tensor_ground_objects(patch_features,patch_mask,object_queries,position_weight,covariance_weight):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if patch_features.ndim!=3 or patch_mask.shape!=patch_features.shape[:2] or object_queries.shape[-1]!=patch_features.shape[-1]:raise ContractError('DimensionMismatch','source-bound vision features [B,P,D] and object queries [N,D]')
    valid=patch_mask.bool().any(-1);safe=patch_mask.bool()|~valid[:,None]
    scores=torch.einsum('nd,bpd->bnp',object_queries,patch_features)/patch_features.shape[-1]**.5
    weights=scores.masked_fill(~safe[:,None,:],-torch.inf).softmax(-1)*valid[:,None,None]
    objects=weights@patch_features;position=objects@position_weight.T;raw=objects@covariance_weight.T
    if position.shape[-1]!=2 or raw.shape[-1]!=3:raise ContractError('DimensionMismatch','2D coordinates and triangular covariance')
    L=torch.zeros(*raw.shape[:-1],2,2,device=raw.device,dtype=raw.dtype)
    L[...,0,0]=torch.nn.functional.softplus(raw[...,0])+1e-5;L[...,1,0]=raw[...,1];L[...,1,1]=torch.nn.functional.softplus(raw[...,2])+1e-5
    return objects,position,L@L.transpose(-1,-2),valid

def tensor_transform(positions,covariance,linear,translation):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if positions.ndim!=3 or positions.shape[-1]!=2 or covariance.shape!=positions.shape[:-1]+(2,2) or linear.shape!=(positions.shape[0],2,2) or translation.shape!=(positions.shape[0],2):raise ContractError('DimensionMismatch','explicit batched physical transform')
    return positions@linear.transpose(-1,-2)+translation[:,None,:],linear[:,None,:,:]@covariance@linear[:,None,:,:].transpose(-1,-2)
