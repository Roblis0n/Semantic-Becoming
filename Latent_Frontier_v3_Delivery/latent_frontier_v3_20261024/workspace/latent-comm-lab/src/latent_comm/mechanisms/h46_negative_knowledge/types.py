from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class DomainPredicate:
    op: str
    value: int
    def __post_init__(self):
        if self.op not in ('eq','ne','lt','le','gt','ge','divisible','not_divisible') or type(self.value) is not int or self.op in ('divisible','not_divisible') and self.value<=0:raise ContractError('UnsupportedExclusion','integer predicate opcode or divisor invalid')
@dataclass(frozen=True)
class NegativeWitness:
    kind: str
    required_predicate: DomainPredicate | None
    checked_domain: tuple[int,...]
    grammar_scope: str | None
    status: str
    def __post_init__(self):
        if self.kind not in ('proof_scoped','program_exhaustive','search_failed_in_grammar','soft_empirical'):raise ContractError('UnsupportedExclusion','unknown evidence type')
        if self.kind in ('proof_scoped','program_exhaustive') and (self.required_predicate is None or self.status!='complete'):raise ContractError('HardSoftConfusion','hard witness needs complete executable scoped certificate')
        if self.kind=='search_failed_in_grammar' and not self.grammar_scope:raise ContractError('UnsupportedExclusion','search failure must retain grammar scope')
@dataclass(frozen=True)
class ExclusionCapsule:
    capsule_id: str
    excluded: DomainPredicate
    assumptions: tuple[str,...]
    witness: NegativeWitness
    reliability: float
    mode: str
    dependencies: tuple[str,...]
    retract_on: tuple[str,...]
    domain_version: str
    def __post_init__(self):
        if not self.capsule_id or not self.domain_version or self.mode not in ('hard','soft','report_only') or not 0<=finite_scalar(self.reliability)<=1:raise ContractError('UnsupportedExclusion','capsule identity, version, mode or reliability invalid')
        if self.mode=='hard' and self.witness.kind not in ('proof_scoped','program_exhaustive'):raise ContractError('HardSoftConfusion','confidence, timeout and search failure never authorize hard pruning')
@dataclass(frozen=True)
class ConditionalFeasibleRegion:
    original_domain: tuple[int,...]
    feasible: tuple[int,...]
    soft_penalties: tuple[tuple[int,float],...]
    applied: tuple[str,...]
    inactive: tuple[tuple[str,str],...]
    conflicts: tuple[str,...]
    status: str
    version: str
    consumed_steps: int
    consumed_cases: int
@dataclass(frozen=True)
class RetractionEvent:
    invalidated_capsules: tuple[str,...]
    restored_candidates: tuple[int,...]
    region: ConditionalFeasibleRegion
