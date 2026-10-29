from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class ScalePacket:
    coarse_map: Matrix
    lift: Matrix
    micro_dynamics: Matrix
    micro_bias: Vector
    macro_dynamics: Matrix
    macro_bias: Vector
    micro_axes: tuple[str,...]
    macro_axes: tuple[str,...]
    source_version: str
    target_version: str
    def __post_init__(self):
        c=matrix(self.coarse_map);l=matrix(self.lift);f=matrix(self.micro_dynamics);g=matrix(self.macro_dynamics);n=len(c[0]);m=len(c)
        if len(l)!=n or len(l[0])!=m or len(f)!=n or len(f[0])!=n or len(g)!=m or len(g[0])!=m or len(self.micro_bias)!=n or len(self.macro_bias)!=m or len(self.micro_axes)!=n or len(self.macro_axes)!=m:raise ContractError('ScaleMismatch','explicit micro/macro axes and map dimensions differ')
@dataclass(frozen=True)
class MultiScaleState:
    coarse: Vector
    detail_residual: Vector | None
    scale_version: str
@dataclass(frozen=True)
class ClosureResidual:
    linear: Matrix
    bias: Vector
    norm: float
    closed: bool
    repair: str
