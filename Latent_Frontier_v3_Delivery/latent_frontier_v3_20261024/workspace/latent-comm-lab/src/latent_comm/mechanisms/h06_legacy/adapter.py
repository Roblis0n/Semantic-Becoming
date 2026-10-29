from latent_comm.core import ContractError

def tensor_charts(state,read_maps,write_maps,route_logits,coverage_mask,*,mode='soft'):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if state.ndim!=2 or len(read_maps)!=len(write_maps) or route_logits.shape!=(state.shape[0],len(read_maps)) or coverage_mask.shape!=route_logits.shape:raise ContractError('DimensionMismatch','charts have heterogeneous local dims and explicit coverage [B,C]')
    if mode not in ('soft','hard'):raise ContractError('InvalidRouting','routing estimator must be explicit')
    valid=coverage_mask.bool().any(-1);safe_mask=coverage_mask.bool()|(~valid[:,None])
    scores=route_logits.masked_fill(~safe_mask,-torch.inf);weights=scores.softmax(-1)*valid[:,None]
    if mode=='hard':weights=torch.nn.functional.one_hot(scores.argmax(-1),len(read_maps)).to(state.dtype)*valid[:,None]
    locals=[];reconstructions=[]
    for read,write in zip(read_maps,write_maps):
        if read.ndim!=2 or read.shape[1]!=state.shape[1] or write.shape!=(state.shape[1],read.shape[0]):raise ContractError('DimensionMismatch','chart read/write not an assumed inverse')
        local=state@read.T;locals.append(local);reconstructions.append(local@write.T)
    # No averaging of incompatible local coordinates. Only same model-space reconstructions combine.
    reconstruction=(torch.stack(reconstructions,1)*weights[:,:,None]).sum(1)
    return tuple(locals),reconstruction,weights,valid
