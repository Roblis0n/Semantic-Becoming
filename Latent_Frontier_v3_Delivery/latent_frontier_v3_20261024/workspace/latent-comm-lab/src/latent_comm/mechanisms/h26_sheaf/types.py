from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class LocalDomain:
    name: str
    dimension: int
    def __post_init__(self):
        if not self.name or not 1<=self.dimension<=64:raise ContractError('InvalidDomain','named finite local coordinates required')
@dataclass(frozen=True)
class AffineRestriction:
    edge_id: str
    left: str
    right: str
    left_map: Matrix
    right_map: Matrix
    bias: Vector
    support: tuple[str,...]
    def __post_init__(self):
        a=matrix(self.left_map);b=matrix(self.right_map);v=vector(self.bias)
        if len(a)!=len(b) or len(v)!=len(a) or not self.edge_id or not self.support:raise ContractError('UnboundRestriction','overlap axes and evidence support must be explicit')
@dataclass(frozen=True)
class Anchor:
    domain: str
    coordinate: int
    value: float
@dataclass(frozen=True)
class SheafPacket:
    cover: tuple[LocalDomain,...]
    restrictions: tuple[AffineRestriction,...]
    anchors: tuple[Anchor,...]
    version: str
@dataclass(frozen=True)
class GluingCandidate:
    sections: tuple[tuple[str,Vector],...]
    residuals: tuple[tuple[str,Vector],...]
    conflict_witness: tuple[str,...]
    status: str
    missing_overlaps: tuple[tuple[str,str],...]
    rank: int
    steps: int
