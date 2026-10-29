from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class StateDomain:
    state_ids: tuple[str,...]
    values: tuple[int,...]
    version: str
    def __post_init__(self):
        if not self.state_ids or len(self.state_ids)>64 or len(set(self.state_ids))!=len(self.state_ids) or len(self.values)!=len(self.state_ids) or any(type(x) is not int for x in self.values) or not self.version:raise ContractError('InfiniteDomainUnsupported','finite named integer states, aligned values and version required')
@dataclass(frozen=True)
class FiniteQuery:
    query_id: str
    opcode: str
    argument: int
    version: str
    def __post_init__(self):
        if self.opcode not in ('parity','greater_than','affine_offset') or type(self.argument) is not int or not self.query_id or not self.version:raise ContractError('QueryFamilyUndefined','typed finite query opcode, argument and version required')
@dataclass(frozen=True)
class IndistinguishabilityClass:
    class_id: str
    members: tuple[str,...]
    representative: str
    signature: tuple[int,...]
@dataclass(frozen=True)
class TaskRelativeQuotient:
    queries: tuple[FiniteQuery,...]
    classes: tuple[IndistinguishabilityClass,...]
    source_domain: StateDomain | None
    domain_version: str
    version: str
    exactness: str = 'exact_finite_query_family'
@dataclass(frozen=True)
class DistinguishingWitness:
    old_class_id: str
    state_a: str
    state_b: str
    query_id: str
    response_a: int
    response_b: int
@dataclass(frozen=True)
class RefinementMap:
    old_version: str
    new_version: str
    old_to_new: tuple[tuple[str,tuple[str,...]],...]
    witnesses: tuple[DistinguishingWitness,...]
    quotient: TaskRelativeQuotient
@dataclass(frozen=True)
class ApproximateClusters:
    groups: tuple[tuple[int,...],...]
    method: str
    epsilon: float
    threshold_relation_transitive: bool
    nontransitive_witness: tuple[int,int,int] | None
    exactness: str = 'approximate_clustering_not_threshold_equivalence'
