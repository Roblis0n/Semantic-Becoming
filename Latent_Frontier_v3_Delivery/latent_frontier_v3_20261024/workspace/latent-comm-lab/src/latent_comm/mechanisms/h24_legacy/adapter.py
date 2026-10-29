from latent_comm.core import ContractError

def scoped_tensor_operator(state,u,v,bias,authority,capability_id,slot_names,*,principal,step,versions):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    grant=authority.resolve(capability_id,principal=principal,step=step,versions=versions)
    if len(slot_names)!=state.shape[-1] or len(set(slot_names))!=len(slot_names) or any(not s.startswith('state:') for s in slot_names):raise ContractError('ShapeMismatch','one canonical named scalar slot per tensor coordinate')
    read_mask=torch.tensor([s in grant.readable_slots for s in slot_names],device=state.device,dtype=torch.bool)
    write_mask=torch.tensor([s in grant.writable_slots for s in slot_names],device=state.device,dtype=torch.bool)
    # Unreadable values are removed before computing the effect, not just masked at output.
    permitted=torch.where(read_mask,state,torch.zeros_like(state))
    hidden=torch.tanh(torch.einsum('...dr,...d->...r',v,permitted)+bias)
    proposed=torch.einsum('...dr,...r->...d',u,hidden)
    delta=torch.where(write_mask,proposed,torch.zeros_like(proposed))
    return state+delta,proposed,read_mask,write_mask
