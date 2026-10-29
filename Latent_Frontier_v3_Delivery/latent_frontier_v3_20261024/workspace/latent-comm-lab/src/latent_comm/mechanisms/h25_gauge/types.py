from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class FrameSpec:
    frame_id: str
    dimension: int
    group: str
    version: str
    domain: tuple[str,...] = ('finite_vectors',)
    def __post_init__(self):
        if not self.frame_id or not self.version: raise ContractError('UnknownFrame','explicit frame identity and version required')
        if type(self.dimension) is not int or not 1 <= self.dimension <= 64: raise ContractError('DimensionMismatch','frame dimension 1..64')
        if self.group not in ('GL','orthogonal'): raise ContractError('UnsupportedGroup','only explicit GL and orthogonal transforms')

@dataclass(frozen=True)
class GaugePacket:
    frame: FrameSpec
    state: Vector
    operator: Matrix
    readout: Matrix
    def __post_init__(self):
        z=vector(self.state); t=matrix(self.operator); r=matrix(self.readout); d=self.frame.dimension
        if len(z)!=d or len(t)!=d or len(t[0])!=d or len(r[0])!=d: raise ContractError('DimensionMismatch','state/operator/readout coordinate axes differ')

@dataclass(frozen=True)
class CovarianceReport:
    transported: GaugePacket
    condition: float
    effect_before: Vector
    effect_after: Vector
    residual: Vector
    path: tuple[str,...]
    steps: int
