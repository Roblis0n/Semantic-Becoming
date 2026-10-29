"""Immutable research-plane state and explicit effect contracts."""
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from .refs import ObjectRef, ObjectRegistry
from .versions import VersionSet
from .scopes import Scope, RESEARCH_COMPONENTS
from .budgets import StepBudget
from .errors import Failure, ContractError, ErrorCode

class ExecutionSemantics(str,Enum):
    EXACT='exact_symbolic'
    DIFFERENTIABLE='differentiable'
    SEARCH='discrete_search'
    HYBRID='hybrid'

@dataclass(frozen=True)
class MetaState:
    state_id: str
    versions: VersionSet
    Z: tuple[ObjectRef,...] = ()
    F: tuple[ObjectRef,...] = ()
    O: tuple[ObjectRef,...] = ()
    P: tuple[ObjectRef,...] = ()
    Q: tuple[ObjectRef,...] = ()
    V: tuple[ObjectRef,...] = ()
    K: tuple[ObjectRef,...] = ()
    W: tuple[ObjectRef,...] = ()
    U: tuple[ObjectRef,...] = ()
    E: tuple[ObjectRef,...] = ()
    def __post_init__(self) -> None:
        if not self.state_id: raise ContractError(ErrorCode.INVALID_SCHEMA,'state identity required')
        self.versions.require('state')

@dataclass(frozen=True)
class EffectRecord:
    mechanism_id: str
    input_digest: str
    read_set: tuple[ObjectRef,...]
    writes: frozenset[str]
    preconditions: tuple[str,...]
    postconditions: tuple[str,...]
    provenance: tuple[ObjectRef,...]
    termination_reason: str
    steps_used: int
    def __post_init__(self) -> None:
        if not self.writes<=RESEARCH_COMPONENTS or not 0<=self.steps_used<=128:
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'invalid effect write set or budget')

@dataclass(frozen=True)
class EffectBundle:
    new_objects: tuple[ObjectRef,...]
    record: EffectRecord
    branches: tuple[ObjectRef,...] = ()
    failures: tuple[Failure,...] = ()
    trainable_statistics: tuple[ObjectRef,...] = ()
    migration: ObjectRef | None = None

@dataclass(frozen=True)
class BuildContext:
    registry: ObjectRegistry
    versions: VersionSet
    scope: Scope
    actor: str
    budget: StepBudget

@dataclass(frozen=True)
class PreparedObject:
    ref: ObjectRef
    mechanism_id: str
    semantics: ExecutionSemantics
    versions: VersionSet
    scope: Scope

@dataclass(frozen=True)
class MigrationResult:
    source: VersionSet
    target: VersionSet
    references: tuple[tuple[ObjectRef,ObjectRef],...]
    information_loss: tuple[str,...]
    replay_requires_recompute: bool

class Mechanism(Protocol):
    def prepare(self, packet: object, context: BuildContext) -> PreparedObject: ...
    def apply(self, obj: PreparedObject, state: MetaState, budget: StepBudget) -> EffectBundle: ...
    def migrate(self, obj: PreparedObject, target: VersionSet) -> MigrationResult: ...
    def explain_effect(self, effect: EffectBundle) -> EffectRecord: ...
