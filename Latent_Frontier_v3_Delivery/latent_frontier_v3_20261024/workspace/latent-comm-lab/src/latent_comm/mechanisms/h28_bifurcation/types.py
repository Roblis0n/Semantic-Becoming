from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class PotentialSpec:
    kind: str = 'quartic_pitchfork'
    def __post_init__(self):
        if self.kind!='quartic_pitchfork':raise ContractError('UnspecifiedDynamics','reference implements explicit quartic pitchfork only')
@dataclass(frozen=True)
class StabilityRecord:
    alpha: float
    stationary: float
    jacobian: float
    continuous: str
    euler_multiplier: float
    discrete: str
@dataclass(frozen=True)
class PhaseState:
    alpha: float
    z: Vector
    structure: str
    branch_id: str
    version: str
@dataclass(frozen=True)
class StructureTransition:
    source_version: str
    target_version: str
    mapping: Matrix
    old_structure: str
    new_structure: str
    invalidated_cache_keys: tuple[str,...]
@dataclass(frozen=True)
class BranchTrajectory:
    states: tuple[PhaseState,...]
    stability: tuple[tuple[StabilityRecord,...],...]
    transitions: tuple[StructureTransition,...]
    termination: str
