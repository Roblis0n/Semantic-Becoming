from latent_comm.core import ContractError

def encode_once(evidence_states,evidence_mask,slot_queries,key_projection,value_projection):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if evidence_states.ndim!=3 or evidence_mask.shape!=evidence_states.shape[:2] or slot_queries.ndim!=2:raise ContractError('DimensionMismatch','evidence [B,N,D], static slots [K,d]')
    keys=evidence_states@key_projection.T;values=evidence_states@value_projection.T
    if keys.shape[-1]!=slot_queries.shape[-1]:raise ContractError('DimensionMismatch','query/key channels')
    valid=evidence_mask.bool().any(-1);safe=evidence_mask.bool()|(~valid[:,None])
    scores=torch.einsum('kd,bnd->bkn',slot_queries,keys)/(keys.shape[-1]**.5)
    weights=scores.masked_fill(~safe[:,None,:],-torch.inf).softmax(-1)*valid[:,None,None]
    return weights@values,valid # No future questions enter this encoder.

def read_many(capsule_slots,query_states,query_projection,*,capsule_valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    queries=query_states@query_projection.T
    if capsule_slots.ndim!=3 or queries.ndim!=3 or capsule_slots.shape[0]!=queries.shape[0] or capsule_slots.shape[-1]!=queries.shape[-1]:raise ContractError('DimensionMismatch','capsule [B,K,D], queries [B,Q,D]')
    weights=torch.einsum('bqd,bkd->bqk',queries,capsule_slots).div(capsule_slots.shape[-1]**.5).softmax(-1)
    return (weights@capsule_slots)*capsule_valid[:,None,None],capsule_valid[:,None].expand(queries.shape[:2])
