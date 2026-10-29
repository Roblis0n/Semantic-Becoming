"""Explicit source-bound capabilities, never guessed from model names."""
from dataclasses import dataclass
from typing import Protocol
from collections.abc import Mapping
from types import MappingProxyType
from latent_comm.core import ContractError,ErrorCode,RoleView,Visibility
from latent_comm.safety.policy import require_research_action

@dataclass(frozen=True)
class ModelIdentity:
    model_id: str
    model_revision: str
    tokenizer_id: str
    tokenizer_revision: str
    config_digest: str
    source_url: str
    def __post_init__(self):
        if any(not isinstance(x,str) or not x for x in (self.model_id,self.model_revision,self.tokenizer_id,self.tokenizer_revision,self.config_digest,self.source_url)):
            raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'model/tokenizer revision and source must be pinned')

@dataclass(frozen=True)
class BackendCapabilities:
    identity: ModelIdentity | None
    binding_status: str
    hidden_size: int | None
    num_layers: int | None
    prefix_inputs_embeds: bool | None
    residual_layer_paths: tuple[str,...]
    residual_output_layout: str | None
    kv_cache_format: str | None
    position_encoding: str | None
    cache_position_supported: bool | None
    input_gradients_supported: bool | None
    supported_dtypes: tuple[str,...]
    batch_axes: tuple[str,...]=('batch','sequence','channel')
    evidence: tuple[str,...]=()
    def __post_init__(self):
        if self.binding_status not in {'unbound','public_source_bound','integration_verified'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown binding status')
        if self.binding_status!='unbound' and (self.identity is None or not self.evidence):raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'bound capability needs identity and evidence')
        for n in (self.hidden_size,self.num_layers):
            if n is not None and (type(n) is not int or n<=0):raise ContractError(ErrorCode.INVALID_SHAPE,'invalid declared model dimension')
        if self.residual_output_layout not in {None,'tensor','tuple_first'}:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'residual output layout unbound')
    def require(self,feature: str) -> None:
        if self.binding_status=='unbound':raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'backend has no verified source binding')
        available={'prefix':self.prefix_inputs_embeds is True,'residual':bool(self.residual_layer_paths),'kv':self.kv_cache_format is not None,'input_gradients':self.input_gradients_supported is True,'cache_position':self.cache_position_supported is True}
        if not available.get(feature,False):raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,f'{feature} is unsupported or unknown')
    def require_revision(self,identity: ModelIdentity) -> None:
        if self.identity!=identity:raise ContractError(ErrorCode.VERSION_MISMATCH,'backend model/tokenizer/config revision mismatch')

def unbound_capabilities() -> BackendCapabilities:
    return BackendCapabilities(None,'unbound',None,None,None,(),None,None,None,None,None,())

class TensorBackend(Protocol):
    capabilities: BackendCapabilities
    def forward_role(self,role_batch,**kwargs): ...
    def project_behavior(self,outputs,contract): ...
    def jvp(self,function,primals,tangents): ...
    def vjp(self,function,primals,cotangents): ...

def freeze_base_parameters(model,trainable_names: frozenset[str]) -> tuple[str,...]:
    require_research_action('model_initialize')
    actual={name for name,_ in model.named_parameters()}
    if not trainable_names<=actual:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'requested trainable parameter absent')
    for name,parameter in model.named_parameters():parameter.requires_grad_(name in trainable_names)
    # Do not wrap the receiver in no_grad: input gradients may still be required.
    return tuple(sorted(trainable_names))

def bind_hf(identity: ModelIdentity,capabilities: BackendCapabilities, *, device: str,dtype_name: str):
    require_research_action('model_load')
    from latent_comm.safety.model_access import load_hf_model,load_hf_tokenizer
    capabilities.require_revision(identity)
    model=load_hf_model(identity.model_id,revision=identity.model_revision,device=device,dtype_name=dtype_name)
    tokenizer=load_hf_tokenizer(identity.tokenizer_id,revision=identity.tokenizer_revision)
    return model,tokenizer,capabilities


def validate_role_origins(views: tuple[RoleView,...],batch_size: int) -> None:
    if len(views)!=batch_size or not views or any(not isinstance(v,RoleView) for v in views):
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'model inputs need one physically projected RoleView per batch row')
    if len({v.role for v in views})!=1 or len({v.versions for v in views})!=1:
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'model batch mixes roles or semantic versions')

@dataclass(frozen=True)
class ModelInputs:
    """Live model tensors derived from role-only origins; no labels or IDs here."""
    role_origins: tuple[RoleView,...]
    tensors: Mapping[str,object]
    def __post_init__(self):
        allowed={'input_ids','inputs_embeds','attention_mask','position_ids','token_type_ids','cache_position'}
        if not self.tensors or not set(self.tensors)<=allowed:
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'model input contains unapproved or supervision field')
        if ('input_ids' in self.tensors)==('inputs_embeds' in self.tensors):
            raise ContractError(ErrorCode.INVALID_SCHEMA,'choose exactly one token or embedding input')
        main=self.tensors.get('input_ids',self.tensors.get('inputs_embeds'))
        if not hasattr(main,'shape') or len(main.shape)<2:
            raise ContractError(ErrorCode.INVALID_SHAPE,'model input must be a live shaped value')
        validate_role_origins(self.role_origins,main.shape[0])
        object.__setattr__(self,'tensors',MappingProxyType(dict(self.tensors)))
    def kwargs(self) -> dict:
        return dict(self.tensors)
