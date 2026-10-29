from latent_comm.core import ContractError

def tensor_dual_fusion(latent_slots,symbol_embeddings,symbol_mask,query_projection,key_projection,value_projection,*,verified_symbol_packet):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from .types import SymbolPacket
    if not isinstance(verified_symbol_packet,SymbolPacket):raise ContractError('InvalidSymbol','exact symbols must be validated before latent readout')
    if latent_slots.ndim!=3 or symbol_embeddings.ndim!=3 or symbol_embeddings.shape[0]!=latent_slots.shape[0] or symbol_embeddings.shape[1]!=len(verified_symbol_packet.symbols) or symbol_mask.shape!=symbol_embeddings.shape[:2]:raise ContractError('DimensionMismatch','latent and symbol slot axes')
    queries=latent_slots@query_projection.T;keys=symbol_embeddings@key_projection.T;values=symbol_embeddings@value_projection.T
    valid=symbol_mask.bool().any(-1);safe=symbol_mask.bool()|~valid[:,None]
    attention=(queries@keys.transpose(-1,-2)/(queries.shape[-1]**.5)).masked_fill(~safe[:,None,:],-torch.inf).softmax(-1)*valid[:,None,None]
    contextual=latent_slots+attention@values
    # Exact strings/decimals are returned untouched, never decoded from this tensor.
    return contextual,verified_symbol_packet
