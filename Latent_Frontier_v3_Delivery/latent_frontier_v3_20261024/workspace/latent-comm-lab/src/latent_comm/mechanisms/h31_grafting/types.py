from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class CausalModule:
    output: str
    unit: str
    parents: tuple[str,...]
    parent_units: tuple[str,...]
    coefficients: Vector
    bias: float
    noise_terms: tuple[tuple[str,float],...]
    allowed_interventions: bool = True
    def __post_init__(self):
        if not self.output or not self.unit or len(self.parents)!=len(self.parent_units) or len(self.parents)!=len(self.coefficients) or len(set(self.parents))!=len(self.parents):raise ContractError('BoundaryMismatch','explicit unique parent interfaces required')
        for x in self.coefficients:finite_scalar(x)
        finite_scalar(self.bias)
        if len(dict(self.noise_terms))!=len(self.noise_terms):raise ContractError('NoiseIdentityConflict','noise terms must share identities explicitly')
        for _,x in self.noise_terms:finite_scalar(x)
@dataclass(frozen=True)
class TargetSCM:
    modules: tuple[CausalModule,...]
    noise_ids: tuple[str,...]
    version: str
@dataclass(frozen=True)
class BoundaryBinding:
    source_parent: str
    target_parent: str
    source_unit: str
    target_unit: str
    scale: float = 1.
    offset: float = 0.
@dataclass(frozen=True)
class GraftCertificate:
    before: TargetSCM
    after: TargetSCM
    changed_node: str
    affected_descendants: tuple[str,...]
    intervention_map: tuple[tuple[str,str],...]
    noise_identities: tuple[str,...]
    assumptions: tuple[str,...]
