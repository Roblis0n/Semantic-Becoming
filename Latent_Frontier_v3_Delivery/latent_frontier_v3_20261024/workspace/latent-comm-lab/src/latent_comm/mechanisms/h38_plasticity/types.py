from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class RuleNode:
    op: str
    children: tuple['RuleNode',...] = ()
    scalar: float = 1.
    slot: str = ''
    parameter: str | None = None
@dataclass(frozen=True)
class PlasticityProgram:
    ast: RuleNode
    writable_groups: tuple[str,...]
    max_update_norm: float
    inner_steps: int
    lifetime_steps: int
    version: str
    estimator: str
    def __post_init__(self):
        if not self.writable_groups or len(set(self.writable_groups))!=len(self.writable_groups) or any(not n.startswith(('adapter.','reader.','external_state.')) for n in self.writable_groups):raise ContractError('WriteScopeViolation','only explicit adapter/reader/external state groups can be updated')
        if not 1<=self.inner_steps<=128 or self.lifetime_steps<self.inner_steps or self.max_update_norm<=0 or not self.version:raise ContractError('InnerStepLimit','positive update norm, finite inner steps and lifetime required')
        if self.estimator not in ('exact_unroll','first_order'):raise ContractError('RuleTypeError','this interpreter implements exact_unroll and explicit first_order only')
@dataclass(frozen=True)
class SupportBatch:
    inputs: Any
    targets: Any
    partition_id: str
@dataclass(frozen=True)
class QueryBatch:
    inputs: Any
    targets: Any
    partition_id: str
@dataclass(frozen=True)
class RuleResult:
    parameters: tuple[tuple[str,Vector],...]
    memory: tuple[tuple[str,Vector],...]
    applied_updates: tuple[tuple[str,Vector],...]
    next_step: int
    estimator: str
    rule_version: str
