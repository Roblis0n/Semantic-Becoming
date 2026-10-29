"""Wire identity is not a model input; live values preserve tensor identity."""
from dataclasses import dataclass
from typing import Generic,TypeVar
from latent_comm.core import ObjectRef, Scope, VersionSet, ExecutionSemantics, TensorSpec, ContractError, ErrorCode
T=TypeVar('T')
@dataclass(frozen=True)
class Envelope:
    packet_id: ObjectRef
    kind: str
    schema_version: int
    producer: str
    recipient_scope: Scope
    input_digest: str
    created_by_task: str
    parents: tuple[ObjectRef,...]
    coordinate_refs: tuple[ObjectRef,...]
    ontology_ref: ObjectRef | None
    isa_ref: ObjectRef | None
    task_ref: ObjectRef
    evidence_ref: ObjectRef
    payload_ref: ObjectRef
    execution_semantics: ExecutionSemantics
    capabilities_required: frozenset[str]
    versions: VersionSet
    def __post_init__(self) -> None:
        if self.schema_version!=3 or not self.kind or not self.producer or not self.input_digest:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'invalid v3 envelope identity')
        self.versions.require('schema','task','evidence')
        if self.coordinate_refs:self.versions.require('frame')
        if self.ontology_ref:self.versions.require('ontology')
        if self.isa_ref:self.versions.require('isa')

@dataclass(frozen=True)
class LiveTensor(Generic[T]):
    value: T
    spec: TensorSpec
    def __post_init__(self) -> None:
        shape=getattr(self.value,'shape',None)
        if shape is not None:self.spec.check_shape(tuple(shape))

@dataclass(frozen=True)
class StoredTensor:
    ref: ObjectRef
    spec: TensorSpec
    content_sha256: str
    container: str
    replay_requires_recompute: bool = True
    def __post_init__(self) -> None:
        if not self.replay_requires_recompute:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'serialization cannot preserve an arbitrary autograd graph')
        if self.container not in {'safetensors','finite_json'}:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'unsafe or unsupported tensor container')
