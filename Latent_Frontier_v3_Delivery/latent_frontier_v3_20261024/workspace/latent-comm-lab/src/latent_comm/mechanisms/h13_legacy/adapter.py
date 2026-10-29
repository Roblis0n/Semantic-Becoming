from latent_comm.core import ContractError

def tensor_fork(state,branches):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if not 1<=branches<=64:raise ContractError('BudgetExhausted','positive bounded branch count')
    return tuple(state.clone() for _ in range(branches)) # Clone isolates writes without detaching gradients.

def tensor_merge(base,branch_states,write_masks,read_masks,*,structure_ids,commutation_classes):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if not 1<=len(branch_states)<=64 or len(structure_ids)!=len(branch_states) or len(commutation_classes)!=len(branch_states) or len(branch_states)!=len(write_masks) or len(read_masks)!=len(write_masks) or len(set(structure_ids))!=1 or any(c!='independent_slots' for c in commutation_classes):raise ContractError('Conflict','typed independent branch structure required')
    for i,(state,write) in enumerate(zip(branch_states,write_masks)):
        if state.shape!=base.shape or write.shape!=base.shape or read_masks[i].shape!=base.shape:raise ContractError('DimensionMismatch','explicit slot masks')
        for j in range(i):
            if bool((write.bool()&write_masks[j].bool()).any()) or bool((write.bool()&read_masks[j].bool()).any()) or bool((write_masks[j].bool()&read_masks[i].bool()).any()):raise ContractError('Conflict','write/read dependence or overlap')
    merged=base
    for state,write in zip(branch_states,write_masks):merged=merged+torch.where(write.bool(),state-base,torch.zeros_like(base))
    return merged
