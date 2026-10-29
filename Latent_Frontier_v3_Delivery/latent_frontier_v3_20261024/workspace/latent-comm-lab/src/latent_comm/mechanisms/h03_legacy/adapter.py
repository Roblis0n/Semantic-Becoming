from latent_comm.core import ContractError

def mixture_sequence_logprob(branch_logits,token_ids,token_mask,branch_log_weights,*,tokenizer_contracts):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if branch_logits.ndim!=4:raise ContractError('DimensionMismatch','logits [B,K,T,V]')
    B,K,T,V=branch_logits.shape
    if token_ids.shape!=(B,T) or token_mask.shape!=(B,T) or branch_log_weights.shape!=(B,K) or len(tokenizer_contracts)!=K:raise ContractError('DimensionMismatch','mixture axes')
    for contract in tokenizer_contracts[1:]:tokenizer_contracts[0].require_same_vocabulary(contract)
    safe_ids=torch.where(token_mask.bool(),token_ids,torch.zeros_like(token_ids))
    logp=branch_logits.log_softmax(-1).gather(-1,safe_ids[:,None,:,None].expand(B,K,T,1)).squeeze(-1)
    seq=logp.masked_fill(~token_mask[:,None,:].bool(),0.).sum(-1)
    return torch.logsumexp(branch_log_weights.log_softmax(-1)+seq,dim=-1)

def tensor_prefix_update(log_weights,token_logps):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if log_weights.shape!=token_logps.shape:raise ContractError('DimensionMismatch','branch posterior axes')
    scores=log_weights+token_logps
    if bool(torch.isneginf(scores).all(-1).any()):raise ContractError('ImpossibleEvidence','all branches impossible; request unknown support')
    return scores-torch.logsumexp(scores,-1,keepdim=True)

def generate_branches(log_weights,branch_step,branch_generate,*,mode,max_steps,eos_id,tokenizer_contracts=()):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_generate')
    import torch
    if max_steps<=0:raise ContractError('BudgetExhausted','explicit bounded generation')
    if mode=='select_then_generate':
        selected=torch.multinomial(log_weights.softmax(-1),1).squeeze(-1)
        return branch_generate(selected,max_steps)
    if len(tokenizer_contracts)!=log_weights.shape[1]:raise ContractError('TokenizerMismatch','mixture/rerank needs a declared shared vocabulary for every branch')
    for contract in tokenizer_contracts[1:]:tokenizer_contracts[0].require_same_vocabulary(contract)
    if mode=='rerank':
        batch,branches=log_weights.shape;candidates=[];scores=[]
        for branch in range(branches):
            selected=torch.full((batch,),branch,device=log_weights.device,dtype=torch.long)
            candidate=branch_generate(selected,max_steps)
            if candidate.ndim!=2 or candidate.shape[0]!=batch or not 1<=candidate.shape[1]<=max_steps:raise ContractError('DimensionMismatch','branch generator returns bounded [B,T] token IDs')
            history=[];alive=torch.ones(batch,dtype=torch.bool,device=candidate.device);sequence_scores=torch.zeros_like(log_weights)
            for token in candidate.unbind(1):
                logits=branch_step(tuple(history));logp=logits.log_softmax(-1)
                selected_logp=logp.gather(-1,token[:,None,None].expand(batch,branches,1)).squeeze(-1)
                sequence_scores=sequence_scores+torch.where(alive[:,None],selected_logp,torch.zeros_like(selected_logp))
                history.append(token);alive=alive&(token!=eos_id)
            scores.append(torch.logsumexp(log_weights.log_softmax(-1)+sequence_scores,-1))
            candidates.append(torch.nn.functional.pad(candidate,(0,max_steps-candidate.shape[1]),value=eos_id))
        score_table=torch.stack(scores,1);choice=score_table.argmax(-1);stack=torch.stack(candidates,1)
        return stack[torch.arange(batch,device=stack.device),choice],score_table

    if mode!='sequence_mixture':raise ContractError('UnspecifiedGeneration','explicit generation strategy')
    history=[];weights=log_weights.log_softmax(-1);finished=torch.zeros(log_weights.shape[0],dtype=torch.bool,device=log_weights.device)
    for _ in range(max_steps):
        logits=branch_step(tuple(history));logp=logits.log_softmax(-1)
        distribution=torch.logsumexp(weights[:,:,None]+logp,1);token=distribution.argmax(-1)
        token=torch.where(finished,torch.full_like(token,eos_id),token)
        selected=logp.gather(-1,token[:,None,None].expand(-1,logp.shape[1],1)).squeeze(-1)
        weights=torch.where(finished[:,None],weights,tensor_prefix_update(weights,selected));history.append(token);finished|=token==eos_id
        if bool(finished.all()):break
    return torch.stack(history,1),weights

def matched_branch_cost(branch_states,target_states,assignment,matched_valid):
    """Fixed discrete matching, live squared distances; no gradient through assignment."""
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if branch_states.ndim!=3 or target_states.ndim!=3 or branch_states.shape[0]!=target_states.shape[0] or branch_states.shape[2]!=target_states.shape[2] or assignment.shape!=branch_states.shape[:2] or matched_valid.shape!=assignment.shape:raise ContractError('DimensionMismatch','matched branches [B,K,D], ordered target indices [B,K]')
    if assignment.dtype!=torch.long or bool((matched_valid.bool()&((assignment<0)|(assignment>=target_states.shape[1]))).any()):raise ContractError('InvalidMatching','each represented matched target must exist')
    safe=torch.where(matched_valid.bool(),assignment,torch.zeros_like(assignment))
    target=target_states.detach().gather(1,safe[:,:,None].expand_as(branch_states))
    error=(branch_states-target).square().mean(-1)
    return torch.where(matched_valid.bool(),error,torch.zeros_like(error))
