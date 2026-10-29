"""Training metadata and role separation; no neural imports or model execution."""
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
import math
import re
from latent_comm.core import ContractError,ErrorCode
from latent_comm.data.collate import RoleBatch,SupervisionBatch

@dataclass(frozen=True)
class Phase:
    name: str
    parameter_owners: tuple[str,...]
    loss_weights: tuple[tuple[str,float],...]
    optimizer_steps: int
    learning_rate: float
    weight_decay: float=0.0
    def __post_init__(self):
        if not self.name or not self.parameter_owners or len(set(self.parameter_owners))!=len(self.parameter_owners):raise ContractError(ErrorCode.INVALID_SCHEMA,'phase owners must be explicit and unique')
        if len(dict(self.loss_weights))!=len(self.loss_weights) or not self.loss_weights:raise ContractError(ErrorCode.INVALID_SCHEMA,'phase requires named loss weights')
        if any(not math.isfinite(w) or w<0 for _,w in self.loss_weights) or not any(w>0 for _,w in self.loss_weights):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'loss weights must be finite, nonnegative and not all zero')
        if type(self.optimizer_steps) is not int or self.optimizer_steps<=0 or not math.isfinite(self.learning_rate) or self.learning_rate<=0 or not math.isfinite(self.weight_decay) or self.weight_decay<0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'invalid phase optimization budget')

@dataclass(frozen=True)
class TrainingPlan:
    run_id: str
    phases: tuple[Phase,...]
    accumulation: int
    maximum_unroll: int
    gradient_clip: float
    checkpoint_interval: int
    model_manifest_digest: str
    data_manifest_digest: str
    config_digest: str
    def __post_init__(self):
        if not self.phases or len({p.name for p in self.phases})!=len(self.phases):raise ContractError(ErrorCode.INVALID_SCHEMA,'unique nonempty phases required')
        if any(type(x) is not int or x<=0 for x in (self.accumulation,self.maximum_unroll,self.checkpoint_interval)):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'positive finite source budgets required')
        if not math.isfinite(self.gradient_clip) or self.gradient_clip<=0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'positive gradient clipping required')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',self.run_id) or any(not s or s=='UNBOUND' for s in (self.model_manifest_digest,self.data_manifest_digest,self.config_digest)):raise ContractError(ErrorCode.VERSION_MISMATCH,'model, data and recipe hashes must be bound before future execution')

@dataclass(frozen=True)
class TrainingBatch:
    sender: RoleBatch
    receiver: RoleBatch
    supervision: SupervisionBatch
    cursor_after: dict
    def __post_init__(self):
        if not isinstance(self.sender,RoleBatch) or self.sender.role.value!='sender' or not isinstance(self.receiver,RoleBatch) or self.receiver.role.value!='receiver':raise ContractError(ErrorCode.ROLE_LEAKAGE,'physical sender and receiver batches required')
        if not isinstance(self.supervision,SupervisionBatch) or len(self.sender.views)!=len(self.receiver.views) or len(self.sender.views)!=len(self.supervision.views):raise ContractError(ErrorCode.INVALID_SHAPE,'role and supervisor batch lengths differ')
        if any(a.versions!=b.versions for a,b in zip(self.sender.views,self.receiver.views)):raise ContractError(ErrorCode.VERSION_MISMATCH,'paired semantic versions differ')

@dataclass(frozen=True)
class RoleTensors:
    """Live features with a traceable projected origin; not arbitrary world dicts."""
    origin: RoleBatch
    values: Mapping[str,object]
    source_fields: Mapping[str,tuple[str,...]]
    def __post_init__(self):
        if not isinstance(self.origin,RoleBatch) or set(self.values)!=set(self.source_fields):raise ContractError(ErrorCode.ROLE_LEAKAGE,'every encoded field needs role origin fields')
        available=set(self.origin.views[0].features)|{'public:'+k for k in self.origin.views[0].public_task}
        if any(not fields or not set(fields)<=available for fields in self.source_fields.values()):raise ContractError(ErrorCode.ROLE_LEAKAGE,'encoded field uses a non-whitelisted origin')
        object.__setattr__(self,'values',MappingProxyType(dict(self.values)))
        object.__setattr__(self,'source_fields',MappingProxyType(dict(self.source_fields)))

def validate_parameter_ownership(groups: Mapping[str,Mapping[str,object]], frozen: Mapping[str,object]) -> dict[str,object]:
    """Identity-only check is safe on opaque objects; no parameter methods called."""
    names={};identities={};frozen_ids={id(v) for v in frozen.values()}
    for owner,items in groups.items():
        if not owner or not items:raise ContractError(ErrorCode.INVALID_SCHEMA,'empty parameter owner group')
        for name,p in items.items():
            qualified=owner+'.'+name
            if not name or qualified in names or id(p) in identities or id(p) in frozen_ids:raise ContractError(ErrorCode.SCOPE_VIOLATION,'parameter is aliased across owners or frozen base')
            names[qualified]=p;identities[id(p)]=qualified
    return names

def validate_phase(phase: Phase,groups: Mapping[str,Mapping[str,object]],loss_specs) -> None:
    if not set(phase.parameter_owners)<=set(groups):raise ContractError(ErrorCode.SCOPE_VIOLATION,'phase owns absent parameter group')
    specs={s.name:s for s in loss_specs}
    if not set(dict(phase.loss_weights))<=set(specs):raise ContractError(ErrorCode.INVALID_SCHEMA,'phase selects undefined objective')
    for name,weight in phase.loss_weights:
        if weight and specs[name].parameter_owners and not set(specs[name].parameter_owners)&set(phase.parameter_owners):raise ContractError(ErrorCode.SCOPE_VIOLATION,'selected objective has no active parameter owner: '+name)


def validate_batch_versions(batch: TrainingBatch,stage_versions,required_axes=None) -> None:
    requested=tuple(required_axes) if required_axes is not None else tuple(k for k,v in stage_versions.as_dict().items() if v is not None)
    # Schema and task are mandatory identities even when a stage narrows its
    # other semantic axes. Requiring their presence alone does not compare them.
    axes=tuple(dict.fromkeys(('schema','task',*requested)))
    stage_versions.require(*axes)
    for role in (batch.sender,batch.receiver):
        for view in role.views:
            if not view.versions.matches(stage_versions,axes):raise ContractError(ErrorCode.VERSION_MISMATCH,'training batch semantic versions differ from configured stage')
