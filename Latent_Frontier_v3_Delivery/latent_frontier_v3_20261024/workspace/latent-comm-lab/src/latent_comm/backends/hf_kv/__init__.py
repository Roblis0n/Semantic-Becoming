"""Explicit canonical KV transport; no layout inference from tensor shapes."""
from dataclasses import dataclass
from latent_comm.core import ContractError,ErrorCode
from latent_comm.safety.policy import require_research_action

CANONICAL_AXES=('batch','kv_head','sequence','head_dim')
@dataclass(frozen=True)
class KVLayout:
    axes: tuple[str,...]
    num_layers: int
    kv_heads: int
    query_heads: int
    head_dim: int
    position_encoding: str
    rotary_layout: str
    rotary_fraction: float
    dtype: str
    model_revision: str
    tokenizer_revision: str
    cache_format: str
    gradient_policy: str
    def __post_init__(self):
        if set(self.axes)!=set(CANONICAL_AXES) or len(self.axes)!=4:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'all cache axes must be explicitly bound')
        if any(type(x) is not int or x<=0 for x in (self.num_layers,self.kv_heads,self.query_heads,self.head_dim)):raise ContractError(ErrorCode.INVALID_SHAPE,'invalid cache dimensions')
        if self.dtype not in {'float32','float64','float16','bfloat16'} or not self.model_revision or not self.tokenizer_revision:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'cache precision and model/tokenizer revisions must be explicitly bound')
        if self.query_heads%self.kv_heads:raise ContractError(ErrorCode.INVALID_SHAPE,'query/kv head grouping incompatible')
        if self.position_encoding not in {'none','absolute','rope'} or self.gradient_policy not in {'preserve_live','detach_for_storage'}:
            raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'position/gradient contract unbound')
        if self.position_encoding=='rope' and (self.rotary_layout!='interleaved_pairs' or self.rotary_fraction!=1. or self.head_dim%2):
            raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'this explicit adapter supports full interleaved-pair RoPE only')
        if self.cache_format not in {'legacy_tuple','hf_dynamic_declared'}:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'cache format unsupported rather than guessed')
    def canonical_shape(self,batch: int,history: int) -> tuple[int,...]:
        return (batch,self.kv_heads,history,self.head_dim)
    def permutation_to_canonical(self) -> tuple[int,...]:
        return tuple(self.axes.index(a) for a in CANONICAL_AXES)

@dataclass(frozen=True)
class KVTransferContract:
    source: KVLayout
    target: KVLayout
    layer_map: tuple[int,...]
    head_map: tuple[int,...]
    source_positions: tuple[int,...]
    target_positions: tuple[int,...]
    behavior_mapping_kind: str
    def __post_init__(self):
        if len(self.layer_map)!=self.target.num_layers or any(i<0 or i>=self.source.num_layers for i in self.layer_map):raise ContractError(ErrorCode.INVALID_SHAPE,'layer map incomplete')
        if len(self.head_map)!=self.target.kv_heads or any(i<0 or i>=self.source.kv_heads for i in self.head_map):raise ContractError(ErrorCode.INVALID_SHAPE,'kv-head map incomplete')
        if len(self.source_positions)!=len(self.target_positions) or any(type(p) is not int or p<0 for p in self.source_positions+self.target_positions):raise ContractError(ErrorCode.INVALID_SHAPE,'position mapping invalid')
        if self.behavior_mapping_kind not in {'exact_same_backend','learned_approximate'}:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'cache transfer must state exact or approximate behavior')
        if self.behavior_mapping_kind=='exact_same_backend' and (self.source!=self.target or self.source_positions!=self.target_positions or self.layer_map!=tuple(range(self.source.num_layers)) or self.head_map!=tuple(range(self.source.kv_heads))):
            raise ContractError(ErrorCode.CONFLICT,'exact transfer requires identical complete backend and position identity')
        if self.source.position_encoding=='absolute' or self.target.position_encoding=='absolute':
            if self.source_positions!=self.target_positions:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'absolute-position retiming requires a separate learned recomputation adapter')

def validate_transfer_arguments(contract,key_projections,value_projections,source_rope=None,target_rope=None):
    """Metadata-only exactness boundary: identity mode cannot accept learned maps."""
    if contract.behavior_mapping_kind=='exact_same_backend':
        if any(value is not None for value in (key_projections,value_projections,source_rope,target_rope)):
            raise ContractError(ErrorCode.CONFLICT,'exact cache transfer is identity-only; projections or phase remapping require learned_approximate')
    elif key_projections is None or value_projections is None or len(key_projections)!=contract.target.num_layers or len(value_projections)!=contract.target.num_layers:
        raise ContractError(ErrorCode.INVALID_SHAPE,'approximate transport requires one explicit key/value projection per target layer')

def _rotate_interleaved(tensor,cos,sin,inverse: bool=False):
    require_research_action('model_forward')
    import torch
    even=tensor[...,0::2];odd=tensor[...,1::2]
    sine=-sin if inverse else sin
    first=even*cos-odd*sine;second=even*sine+odd*cos
    return torch.stack((first,second),dim=-1).flatten(-2)

def transport_legacy_cache(cache,contract: KVTransferContract, *, key_projections=None,value_projections=None,source_rope=None,target_rope=None):
    require_research_action('model_forward')
    validate_transfer_arguments(contract,key_projections,value_projections,source_rope,target_rope)
    import torch
    if contract.source.cache_format!='legacy_tuple':raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'use a source-bound accessor for non-tuple cache')
    if len(cache)!=contract.source.num_layers:raise ContractError(ErrorCode.INVALID_SHAPE,'source layer count differs')
    history=len(contract.source_positions);layers=[]
    if contract.behavior_mapping_kind=='exact_same_backend':
        # Preserve already-positioned values and live identities. No unrotate /
        # re-rotate round trip, learned projection or head permutation is applied.
        for key,value in cache:
            canonical_shape=tuple(key.shape[i] for i in contract.source.permutation_to_canonical())
            if canonical_shape!=contract.source.canonical_shape(canonical_shape[0],history) or tuple(value.shape)!=tuple(key.shape):raise ContractError(ErrorCode.INVALID_SHAPE,'exact cache violates declared shape')
            if str(key.dtype).split('.')[-1]!=contract.source.dtype or value.dtype!=key.dtype:raise ContractError(ErrorCode.INVALID_SHAPE,'exact cache violates declared dtype')
            if contract.target.gradient_policy=='detach_for_storage':layers.append((key.detach(),value.detach()))
            else:layers.append((key,value))
        return tuple(layers)
    for target_layer,source_layer in enumerate(contract.layer_map):
        key,value=cache[source_layer]
        key=key.permute(contract.source.permutation_to_canonical());value=value.permute(contract.source.permutation_to_canonical())
        expected=contract.source.canonical_shape(key.shape[0],history)
        if tuple(key.shape)!=expected or tuple(value.shape)!=expected:raise ContractError(ErrorCode.INVALID_SHAPE,'cache tensor does not satisfy explicit source layout')
        if contract.source.position_encoding=='rope':
            if source_rope is None:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'source rotary phases required')
            key=_rotate_interleaved(key,*source_rope,inverse=True)
        index=torch.tensor(contract.head_map,device=key.device);key=key.index_select(1,index);value=value.index_select(1,index)
        kp=key_projections[target_layer];vp=value_projections[target_layer]
        if tuple(kp.shape)!=(contract.target.head_dim,contract.source.head_dim) or tuple(vp.shape)!=tuple(kp.shape):raise ContractError(ErrorCode.INVALID_SHAPE,'per-layer projection dimensions mismatch')
        key=key@kp.T;value=value@vp.T
        if contract.target.position_encoding=='rope':
            if target_rope is None:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'target rotary phases required')
            key=_rotate_interleaved(key,*target_rope)
        if contract.target.gradient_policy=='detach_for_storage':key=key.detach();value=value.detach()
        inverse_order=tuple(CANONICAL_AXES.index(a) for a in contract.target.axes)
        layers.append((key.permute(inverse_order),value.permute(inverse_order)))
    return tuple(layers)

def to_hf_dynamic_cache(canonical_pairs, *, config,layout: KVLayout,positions):
    require_research_action('model_initialize')
    from transformers import DynamicCache
    if layout.axes!=CANONICAL_AXES or layout.cache_format!='hf_dynamic_declared':raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'HF DynamicCache adapter requires explicit canonical binding')
    if len(canonical_pairs)!=layout.num_layers:raise ContractError(ErrorCode.INVALID_SHAPE,'target layer count mismatch')
    cache=DynamicCache(config=config)
    for i,(key,value) in enumerate(canonical_pairs):
        expected=layout.canonical_shape(key.shape[0],len(positions))
        if tuple(key.shape)!=expected or tuple(value.shape)!=expected:raise ContractError(ErrorCode.INVALID_SHAPE,'target cache layout mismatch')
        cache.update(key,value,i,cache_kwargs={'cache_position':positions})
    return cache
