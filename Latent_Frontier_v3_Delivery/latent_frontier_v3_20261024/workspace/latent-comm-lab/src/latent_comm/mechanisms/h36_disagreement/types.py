from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class RuleProgram:
    op: str
    divisor: int = 1
    children: tuple['RuleProgram',...] = ()
    def __post_init__(self):
        arities={'divisible':0,'not':1,'and':2,'implies':2}
        if self.op not in arities or len(self.children)!=arities[self.op] or type(self.divisor) is not int or self.divisor<=0:raise ContractError('InvalidCounterexample','unsupported executable rule AST')
@dataclass(frozen=True)
class ScopedClaim:
    claim_id: str
    program: RuleProgram
    domain: tuple[int,...]
    version: str
@dataclass(frozen=True)
class Counterexample:
    claim_id: str
    value: int
    predicted: bool
    expected: bool | None
    observation_rule: str
    status: str
@dataclass(frozen=True)
class RevisionRound:
    original: ScopedClaim
    counterexamples: tuple[Counterexample,...]
    revised: ScopedClaim | None
    rejected: tuple[tuple[int,str],...]
@dataclass(frozen=True)
class DisagreementGame:
    rounds: tuple[RevisionRound,...]
    surviving_claims: tuple[ScopedClaim,...]
    status: str
