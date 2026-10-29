from latent_comm.core import ContractError

def translate_cache(cache,transfer,*,key_projections,value_projections,source_rope=None,target_rope=None):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.backends.hf_kv import transport_legacy_cache
    return transport_legacy_cache(cache,transfer,key_projections=key_projections,value_projections=value_projections,source_rope=source_rope,target_rope=target_rope)

def translate_progress(state,projection,public_boundary,dependency_mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if state.ndim!=3 or projection.ndim!=2 or projection.shape[1]!=state.shape[-1] or public_boundary.shape!=(state.shape[0],state.shape[1],projection.shape[0]) or dependency_mask.shape!=state.shape[:2]:raise ContractError('DimensionMismatch','state [B,pending,Dsrc], target boundary and pending mask')
    mapped=state@projection.T
    return (mapped+public_boundary)*dependency_mask[:,:,None].to(mapped.dtype)

def resume_model(model,new_token_ids,cache,attention_mask,cache_position,*,layout,contract,expected_contract,role_origins):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.backends.capabilities import validate_role_origins
    if contract!=expected_contract or contract.model_revision!=layout.model_revision or contract.tokenizer_revision!=layout.tokenizer_revision or contract.cache_layout!=layout.cache_format or contract.dtype!=layout.dtype:raise ContractError('ResumeMismatch','model/tokenizer/dtype/cache metadata must match explicit target')
    validate_role_origins(tuple(role_origins),new_token_ids.shape[0])
    if new_token_ids.ndim!=2 or new_token_ids.shape[1]!=1 or cache_position.numel()!=1:raise ContractError('PositionMismatch','exact next-token boundary required')
    position=int(cache_position.item())
    if attention_mask.shape!=(new_token_ids.shape[0],position+1):raise ContractError('PositionMismatch','mask includes cached prefix plus exactly one new token')
    if layout.cache_format!='legacy_tuple':raise ContractError('UnsupportedLayout','use explicit backend cache-object accessor')
    axis=layout.axes.index('sequence')
    if len(cache)!=layout.num_layers or any(k.shape[axis]!=position or v.shape[axis]!=position for k,v in cache):raise ContractError('PositionMismatch','cache history cannot skip or replay token')
    return model(input_ids=new_token_ids,past_key_values=cache,attention_mask=attention_mask,cache_position=cache_position,use_cache=True,return_dict=True)


def capture_model_snapshot(cache,attention_mask,pending_token_ids,position_ids,*,contract,layout,position_spec,random_state_scope,cuda_devices,completed_operations,pending_dependencies,branch_lineage,transaction_version,role_origins,versions):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from .types import ModelContinuation
    from latent_comm.backends.capabilities import validate_role_origins
    if contract.mode!='exact_same_model' or layout.cache_format!='legacy_tuple' or contract.model_revision!=layout.model_revision or contract.tokenizer_revision!=layout.tokenizer_revision or contract.dtype!=layout.dtype or contract.cache_layout!=layout.cache_format:raise ContractError('ResumeMismatch','explicit same-model/tokenizer/dtype cache capture contract')
    validate_role_origins(tuple(role_origins),pending_token_ids.shape[0])
    if pending_token_ids.ndim!=2 or pending_token_ids.shape[1]!=1 or attention_mask.shape!=(pending_token_ids.shape[0],position_spec.cached_tokens+1) or position_ids.shape!=pending_token_ids.shape:raise ContractError('PositionMismatch','capture exact pending token, full prefix mask and explicit position IDs')
    axis=layout.axes.index('sequence')
    if len(cache)!=layout.num_layers or any(k.shape[axis]!=position_spec.cached_tokens or v.shape[axis]!=position_spec.cached_tokens for k,v in cache):raise ContractError('PositionMismatch','cache history length differs from declared position')
    if random_state_scope not in ('none','cpu','cpu_cuda') or random_state_scope!='cpu_cuda' and cuda_devices:raise ContractError('RandomStateMismatch','explicit RNG device scope')
    cache=_validate_snapshot_tensors(cache,attention_mask,pending_token_ids,position_ids,layout,position_spec)
    cpu=torch.random.get_rng_state().clone() if random_state_scope!='none' else None
    cuda=tuple((int(device),torch.cuda.get_rng_state(device).clone()) for device in cuda_devices) if random_state_scope=='cpu_cuda' else ()
    # Clone isolates branches and keeps live autograd edges. Disk persistence must detach and recompute.
    isolated=tuple((k.clone(),v.clone()) for k,v in cache)
    return ModelContinuation(contract,position_spec,random_state_scope,cpu,cuda,isolated,attention_mask.clone(),pending_token_ids.clone(),position_ids.clone(),tuple(completed_operations),tuple(pending_dependencies),tuple(branch_lineage),transaction_version,tuple(role_origins),versions)

def resume_model_snapshot(model,snapshot,*,layout,contract,versions,transaction_version,available_dependencies):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from .reference import validate_model_snapshot
    spec=validate_model_snapshot(snapshot,contract=contract,versions=versions,transaction_version=transaction_version,available_dependencies=available_dependencies)
    if bool(model.training):raise ContractError('ResumeMismatch','exact cached continuation requires eval-mode model; training-time stochastic lifecycle is a separate contract')
    if contract.model_revision!=layout.model_revision or contract.tokenizer_revision!=layout.tokenizer_revision or contract.dtype!=layout.dtype or contract.cache_layout!=layout.cache_format:raise ContractError('ResumeMismatch','target backend identity differs')
    cache=_validate_snapshot_tensors(snapshot.cache,snapshot.attention_mask,snapshot.pending_token_ids,snapshot.position_ids,layout,spec)
    # Backends may mutate cache buffers. Each resume owns its private live-gradient copy.
    cache=tuple((k.clone(),v.clone()) for k,v in cache)
    position=torch.tensor([spec.next_position],device=snapshot.pending_token_ids.device,dtype=torch.long)
    def run():
        return model(input_ids=snapshot.pending_token_ids,past_key_values=cache,attention_mask=snapshot.attention_mask,cache_position=position,position_ids=snapshot.position_ids,use_cache=True,return_dict=True)
    if snapshot.random_state_scope=='none':return run()
    # Restore captured RNG only inside a fork; caller's unrelated random stream is preserved.
    with torch.random.fork_rng(devices=[device for device,_ in snapshot.cuda_rng_states]):
        torch.random.set_rng_state(snapshot.cpu_rng_state)
        for device,state in snapshot.cuda_rng_states:torch.cuda.set_rng_state(state,device)
        return run()

def close_model_snapshot(snapshot):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from dataclasses import replace
    return replace(snapshot,cache=None,closed=True)


def _validate_snapshot_tensors(cache,attention_mask,pending_token_ids,position_ids,layout,position_spec):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.backends.hf_kv import KVTransferContract,transport_legacy_cache
    if layout.gradient_policy!='preserve_live' or layout.cache_format!='legacy_tuple':raise ContractError('ResumeMismatch','live exact snapshots need the declared non-detaching tuple backend')
    if pending_token_ids.ndim!=2 or pending_token_ids.shape[1]!=1 or pending_token_ids.dtype!=torch.long or position_ids.shape!=pending_token_ids.shape or position_ids.dtype!=torch.long:raise ContractError('PositionMismatch','one integral pending token and explicit position per batch member')
    if attention_mask.shape!=(pending_token_ids.shape[0],position_spec.cached_tokens+1) or bool(((attention_mask!=0)&(attention_mask!=1)).any()) or not bool(attention_mask[:,-1].bool().all()):raise ContractError('PositionMismatch','binary full-prefix mask with a valid pending token')
    if bool((position_ids<0).any()):raise ContractError('PositionMismatch','negative model position')
    if position_spec.position_id_policy=='mask_cumsum' and not torch.equal(position_ids,attention_mask.long().sum(-1,keepdim=True)-1):raise ContractError('PositionMismatch','position IDs must match declared mask-cumsum policy')
    if any(t.device!=pending_token_ids.device for pair in cache for t in pair) or attention_mask.device!=pending_token_ids.device or position_ids.device!=pending_token_ids.device:raise ContractError('DeviceMismatch','pending tokens, masks, positions and live cache share one declared device')
    if any(k.ndim!=4 or v.ndim!=4 or k.shape[layout.axes.index('batch')]!=pending_token_ids.shape[0] for k,v in cache):raise ContractError('DimensionMismatch','cache layer batch and four explicit axes')
    positions=tuple(range(position_spec.cached_tokens))
    transfer=KVTransferContract(layout,layout,tuple(range(layout.num_layers)),tuple(range(layout.kv_heads)),positions,positions,'exact_same_backend')
    return transport_legacy_cache(cache,transfer)
