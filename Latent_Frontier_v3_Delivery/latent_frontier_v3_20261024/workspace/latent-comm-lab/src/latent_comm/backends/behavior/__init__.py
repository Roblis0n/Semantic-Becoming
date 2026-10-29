"""Common observable behaviors, not direct KL across incompatible tokenizers."""
from dataclasses import dataclass
from collections.abc import Callable
from latent_comm.core import ContractError,ErrorCode
from latent_comm.safety.policy import require_research_action

@dataclass(frozen=True)
class BehaviorSpace:
    space_id: str
    version: str
    coordinate_names: tuple[str,...]
    public_anchor_contract: str
    observation_units: str
    def __post_init__(self):
        if not self.space_id or not self.version or not self.coordinate_names or len(set(self.coordinate_names))!=len(self.coordinate_names):raise ContractError(ErrorCode.INVALID_SCHEMA,'behavior coordinates need unique explicit identities')
        if self.public_anchor_contract not in {'public_task','public_probe'}:raise ContractError(ErrorCode.ROLE_LEAKAGE,'behavior anchors cannot be supervised answers')
    def require_same(self,other: 'BehaviorSpace') -> None:
        if self!=other:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'behavior spaces differ; explicit projection is required')

@dataclass(frozen=True)
class TokenizerContract:
    tokenizer_id: str
    revision: str
    vocabulary_digest: str
    tokenization_rules_digest: str
    def require_same_vocabulary(self,other: 'TokenizerContract') -> None:
        if self!=other:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'direct token KL requires identical tokenization and vocabulary')

@dataclass(frozen=True)
class ParameterScope:
    writable_names: tuple[str,...]
    frozen_base_names: tuple[str,...]
    def __post_init__(self):
        if not self.writable_names or set(self.writable_names)&set(self.frozen_base_names):raise ContractError(ErrorCode.SCOPE_VIOLATION,'adapter and frozen base parameter sets must be disjoint and nonempty')

def sequence_log_likelihood(logits,token_ids,valid_mask):
    require_research_action('model_forward')
    import torch
    if logits.ndim!=3 or token_ids.shape!=logits.shape[:2] or valid_mask.shape!=token_ids.shape:raise ContractError(ErrorCode.INVALID_SHAPE,'sequence likelihood layout mismatch')
    logp=torch.log_softmax(logits[:,:-1],dim=-1)
    selected=logp.gather(-1,token_ids[:,1:,None]).squeeze(-1)
    mask=valid_mask[:,1:].bool()
    return selected.masked_fill(~mask,0).sum(-1),mask.sum(-1)

def common_action_distribution(action_sequence_logps,space: BehaviorSpace):
    require_research_action('model_forward')
    import torch
    if action_sequence_logps.shape[-1]!=len(space.coordinate_names):raise ContractError(ErrorCode.INVALID_SHAPE,'action likelihoods do not align to common behaviors')
    return torch.softmax(action_sequence_logps,dim=-1)

def behavior_kl(source_prob,target_logprob,source_space: BehaviorSpace,target_space: BehaviorSpace,valid_mask):
    require_research_action('model_forward')
    import torch
    source_space.require_same(target_space)
    if source_prob.shape!=target_logprob.shape or valid_mask.shape!=source_prob.shape[:-1]:raise ContractError(ErrorCode.INVALID_SHAPE,'behavior KL dimensions differ')
    per=(source_prob*(source_prob.clamp_min(torch.finfo(source_prob.dtype).tiny).log()-target_logprob)).sum(-1)
    from latent_comm.core.learning import masked_tensor_mean
    return masked_tensor_mean(per,valid_mask,zero_valid_policy='differentiable_zero')

class FunctionalBehaviorAdapter:
    def __init__(self,model,scope: ParameterScope,behavior_reader: Callable,space: BehaviorSpace):
        require_research_action('model_initialize')
        self.model=model;self.scope=scope;self.reader=behavior_reader;self.space=space
        self.parameters=dict(model.named_parameters());self.buffers=dict(model.named_buffers())
        if not set(scope.writable_names)<=set(self.parameters):raise ContractError(ErrorCode.UNBOUND_REFERENCE,'adapter parameter absent')
        if set(scope.writable_names)|set(scope.frozen_base_names)!=set(self.parameters):raise ContractError(ErrorCode.SCOPE_VIOLATION,'every model parameter must have exactly one owner')
        for name,parameter in self.parameters.items():parameter.requires_grad_(name in scope.writable_names)
    def observe(self,adapter_parameters,model_inputs):
        require_research_action('model_forward')
        from torch.func import functional_call
        if set(adapter_parameters)!=set(self.scope.writable_names):raise ContractError(ErrorCode.SCOPE_VIOLATION,'functional update exceeds scoped adapter')
        from latent_comm.backends.capabilities import ModelInputs
        if not isinstance(model_inputs,ModelInputs):raise ContractError(ErrorCode.ROLE_LEAKAGE,'behavior reads require role-bound ModelInputs')
        merged={**self.parameters,**adapter_parameters}
        outputs=functional_call(self.model,(merged,self.buffers),(),model_inputs.kwargs(),strict=True)
        behavior=self.reader(outputs)
        if behavior.shape[-1]!=len(self.space.coordinate_names):raise ContractError(ErrorCode.INVALID_SHAPE,'readout behavior coordinate count differs')
        return behavior
    def jvp(self,adapter_parameters,direction,model_inputs):
        require_research_action('model_forward')
        from torch.func import jvp
        if set(direction)!=set(adapter_parameters):raise ContractError(ErrorCode.INVALID_SHAPE,'source direction keys differ')
        return jvp(lambda p:self.observe(p,model_inputs),(adapter_parameters,),(direction,))
    def vjp(self,adapter_parameters,cotangent,model_inputs):
        require_research_action('model_forward')
        from torch.func import vjp
        value,pullback=vjp(lambda p:self.observe(p,model_inputs),adapter_parameters)
        if value.shape!=cotangent.shape:raise ContractError(ErrorCode.INVALID_SHAPE,'behavior cotangent shape mismatch')
        return value,pullback(cotangent)[0]
