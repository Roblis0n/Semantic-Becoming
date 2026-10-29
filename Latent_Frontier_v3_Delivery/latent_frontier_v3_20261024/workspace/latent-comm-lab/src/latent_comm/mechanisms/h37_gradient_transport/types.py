from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class BehaviorAnchorSet:
    coordinate_ids: tuple[str,...]
    public_task_version: str
    observation_kind: str = 'public_behavior'
    def __post_init__(self):
        if not self.coordinate_ids or len(set(self.coordinate_ids))!=len(self.coordinate_ids) or not self.public_task_version:raise ContractError('AnchorMismatch','unique public behavior coordinates and task version required')
        if self.observation_kind!='public_behavior':raise ContractError('AnchorMismatch','different tokenizer logits cannot define a shared behavior space')
@dataclass(frozen=True)
class Linearization:
    jacobian: Matrix
    anchors: BehaviorAnchorSet
    parameter_names: tuple[str,...]
    parameter_version: str
    def __post_init__(self):
        j=matrix(self.jacobian)
        if len(j)!=len(self.anchors.coordinate_ids) or len(j[0])!=len(self.parameter_names) or not self.parameter_version:raise ContractError('AnchorMismatch','Jacobian axes [public behavior,scoped parameter] must be explicit')
        if any(not n.startswith(('adapter.','reader.','external_state.')) for n in self.parameter_names):raise ContractError('WriteScopeViolation','transport update restricted to adapter, reader or external state')
@dataclass(frozen=True)
class TransportedUpdate:
    delta: Vector
    behavior_direction: Vector
    achieved_direction: Vector
    projection_residual: Vector
    unreachable_residual: Vector
    rank: int
    unique: bool
    minimum_norm: bool
    converged: bool
    iterations: int
    normal_residual_norm: float
    target_version: str
    parameter_names: tuple[str,...]
