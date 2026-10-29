from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

from latent_comm.mechanisms.h43_world_kernels.types import WorldKernel, SharedNoiseJoint, ComposedWorldKernel
@dataclass(frozen=True)
class CounterfactualEdit:
    kernel_id: str
    state: str
    action: str
    noise_values: tuple[str,...]
    probabilities: Vector
@dataclass(frozen=True)
class DreamWorld:
    world_id: str
    kernel: ComposedWorldKernel
    parent_kernel_ids: tuple[str,...]
    edits: tuple[CounterfactualEdit,...]
    assumptions: tuple[str,...]
    synthetic: bool = True
    def __post_init__(self):
        if self.synthetic is not True or not self.world_id or not self.parent_kernel_ids:raise ContractError('SyntheticAsReal','constructed worlds require explicit synthetic identity and parent kernels')
@dataclass(frozen=True)
class SyntheticEvidence:
    evidence_id: str
    world_id: str
    parents: tuple[str,...]
    observation_distributions: tuple[Vector,...]
    synthetic: bool = True
    def __post_init__(self):
        if self.synthetic is not True or not self.parents or self.evidence_id in self.parents:raise ContractError('CircularSupport','synthetic evidence must have nonself parent lineage')
@dataclass(frozen=True)
class QuestionCandidate:
    question_id: str
    world_id: str
    start_state: tuple[str,...]
    action: str
    target_state: tuple[str,...]
    reason: str
    synthetic: bool = True
