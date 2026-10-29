from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class EvidenceAtom:
    atom_id: str
    source_handle: str
    source_kind: str
    marginal: float | None
    world_lineage: tuple[str,...] = ()
    def __post_init__(self):
        if not self.atom_id or not self.source_handle or self.source_kind not in ('observed','synthetic','unknown'):raise ContractError('MissingSource','stable atom, source handle and explicit origin kind required')
        if self.marginal is not None and not 0<=finite_scalar(self.marginal)<=1:raise ContractError('UnsupportedCalibration','source marginal outside probability simplex')
        if self.source_kind=='synthetic' and not self.world_lineage:raise ContractError('MissingSource','synthetic evidence requires world lineage')
@dataclass(frozen=True)
class SupportNode:
    node_id: str
    op: str
    inputs: tuple[str,...]
    atom_id: str | None = None
    def __post_init__(self):
        if not self.node_id or self.op not in ('atom','and','or') or self.op=='atom' and (self.inputs or not self.atom_id) or self.op!='atom' and (not self.inputs or self.atom_id is not None):raise ContractError('MissingSource','support node must be typed atom or nonempty AND/OR')
@dataclass(frozen=True)
class ProvenanceGraph:
    atoms: tuple[EvidenceAtom,...]
    nodes: tuple[SupportNode,...]
    root: str
    version: str
@dataclass(frozen=True)
class JointAssignment:
    values: tuple[bool,...]
    probability: float
    def __post_init__(self):
        if any(type(v) is not bool for v in self.values) or not 0<=finite_scalar(self.probability)<=1:raise ContractError('UnsupportedCalibration','joint assignment requires binary values and probability')
@dataclass(frozen=True)
class DependenceModel:
    mode: str
    atom_ids: tuple[str,...]
    joint: tuple[JointAssignment,...] = ()
    declaration_id: str | None = None
    def __post_init__(self):
        if self.mode not in ('unknown','declared_independent','explicit_joint') or len(set(self.atom_ids))!=len(self.atom_ids):raise ContractError('UnknownDependence','unknown dependence mode or duplicate atom variable')
        if self.mode!='unknown' and not self.declaration_id:raise ContractError('UnknownDependence','explicit joint or independence assumption needs a named declaration, not a prediction')
        if self.mode!='explicit_joint' and self.joint:raise ContractError('UnknownDependence','joint table is only legal in explicit_joint mode')
        if self.mode=='explicit_joint':
            if not self.joint or len({j.values for j in self.joint})!=len(self.joint) or any(len(j.values)!=len(self.atom_ids) for j in self.joint) or abs(sum(j.probability for j in self.joint)-1)>1e-9:raise ContractError('UnsupportedCalibration','explicit sparse joint must uniquely assign full atom vector and normalize; omitted assignments have zero mass')
@dataclass(frozen=True)
class CalibratedSupport:
    normalized_expression: tuple
    probability: float | None
    lower_bound: float
    upper_bound: float
    atom_coverage: tuple[str,...]
    shared_ancestors: tuple[str,...]
    status: str
    evidence_scope: str
    version: str
    consumed_cases: int
@dataclass(frozen=True)
class InvalidationSet:
    retracted_atoms: tuple[str,...]
    invalidated_nodes: tuple[str,...]
    root_invalidated: bool
    version: str
