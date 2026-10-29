from latent_comm.core import ContractError

def tensor_operator(state,U,V,bias,alpha,*,nonlinearity='tanh'):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if state.ndim!=2 or U.ndim!=3 or V.shape!=U.shape:raise ContractError('DimensionMismatch','state [B,d], U,V [B,d,r]')
    B,d=state.shape;r=U.shape[-1]
    if U.shape[:2]!=(B,d) or bias.shape!=(B,r) or alpha.shape!=(B,1):raise ContractError('DimensionMismatch','no implicit batch or gate broadcasting')
    h=torch.bmm(V.transpose(1,2),state.unsqueeze(-1)).squeeze(-1)+bias
    if nonlinearity=='tanh':h=h.tanh()
    elif nonlinearity=='relu':h=h.relu()
    elif nonlinearity!='identity':raise ContractError('UnsupportedNonlinearity','activation enum')
    return state+alpha*torch.bmm(U,h.unsqueeze(-1)).squeeze(-1)

def generate_operator(sender_features,weight,bias,*,dimension,rank):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    width=2*dimension*rank+rank+1
    if sender_features.ndim!=2 or weight.shape!=(width,sender_features.shape[1]) or bias.shape!=(width,):raise ContractError('DimensionMismatch','factor hypernetwork output layout')
    raw=torch.nn.functional.linear(sender_features,weight,bias);B=raw.shape[0];q=dimension*rank
    return raw[:,:q].reshape(B,dimension,rank),raw[:,q:2*q].reshape(B,dimension,rank),raw[:,2*q:2*q+rank],raw[:,-1:].sigmoid()

def apply_to_receiver(receiver_state,read_matrix,write_matrix,factors,model,*,capabilities,inputs,injection='prefix',layer=None,slot_mask=None,padding_side='right'):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core import TensorSpec
    from latent_comm.backends.capabilities import ModelInputs
    from latent_comm.backends.hf_prefix import forward_with_prefix
    from latent_comm.backends.hf_hooks import ResidualInjection, forward_with_residuals
    if not isinstance(inputs,ModelInputs):raise ContractError('RoleLeakage','role-bound ModelInputs required')
    if receiver_state.ndim!=2 or read_matrix.ndim!=2 or read_matrix.shape[1]!=receiver_state.shape[1] or write_matrix.shape!=(receiver_state.shape[-1],read_matrix.shape[0]):raise ContractError('DimensionMismatch','read [d,h], write [h,d]')
    local=receiver_state@read_matrix.T;updated=tensor_operator(local,*factors);delta=(updated-local)@write_matrix.T
    values=inputs.kwargs()
    if injection=='prefix':
        prefix=delta.unsqueeze(1);spec=TensorSpec(('batch','prefix','channel'),tuple(prefix.shape),str(prefix.dtype).split('.')[-1],'operator_prefix','mechanism_reader')
        return forward_with_prefix(model,values['input_ids'],values['attention_mask'],prefix,capabilities=capabilities,prefix_spec=spec,padding_side=padding_side,role_origins=inputs.role_origins)
    if injection=='residual' and layer is not None and slot_mask is not None:
        if slot_mask.shape!=values['input_ids'].shape or slot_mask.shape[0]!=delta.shape[0]:raise ContractError('DimensionMismatch','explicit residual sequence mask')
        residual=delta[:,None,:]*slot_mask[:,:,None].to(delta.dtype)
        spec=TensorSpec(('batch','sequence','channel'),tuple(residual.shape),str(residual.dtype).split('.')[-1],'operator_residual','mechanism_reader')
        return forward_with_residuals(model,(ResidualInjection(layer,residual,spec,capabilities.residual_output_layout),),inputs,capabilities=capabilities)
    raise ContractError('UnsupportedCapability','explicit prefix or bound residual layer and position mask required')
