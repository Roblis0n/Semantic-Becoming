from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    responses: tuple[str,...]
    likelihood: Matrix | None
    cost: float
    allowed: bool
    local_only: bool
    def __post_init__(self):
        if not self.query_id or not self.responses or len(set(self.responses))!=len(self.responses) or finite_scalar(self.cost)<0:raise ContractError('UnknownLikelihood','explicit response outcomes and nonnegative query cost required')
        if self.likelihood is not None:
            rows=matrix(self.likelihood)
            if len(rows[0])!=len(self.responses) or any(any(p<0 for p in row) or abs(sum(row)-1)>1e-9 for row in rows):raise ContractError('UnknownLikelihood','response likelihood rows must be normalized')
@dataclass(frozen=True)
class IdentificationState:
    hypotheses: tuple[str,...]
    queries: tuple[QuerySpec,...]
    prior: Vector | None
    version: str
    unknown_hypothesis_possible: bool = True
    def __post_init__(self):
        if not self.hypotheses or len(set(self.hypotheses))!=len(self.hypotheses) or len(self.hypotheses)>64 or not self.version:raise ContractError('NonIdentifiable','finite named hypothesis set required')
        if len({q.query_id for q in self.queries})!=len(self.queries):raise ContractError('NoAllowedQuery','duplicate query identity')
        if any(q.likelihood is not None and len(q.likelihood)!=len(self.hypotheses) for q in self.queries):raise ContractError('UnknownLikelihood','hypothesis likelihood axis differs')
        if self.prior is not None:
            p=vector(self.prior)
            if len(p)!=len(self.hypotheses) or any(x<0 for x in p) or abs(sum(p)-1)>1e-9:raise ContractError('UnknownLikelihood','prior not normalized')
@dataclass(frozen=True)
class QuerySelection:
    query_id: str | None
    criterion: str
    score: float | None
    information_gain: float | None
    partition: tuple[tuple[str,...],...]
    status: str
@dataclass(frozen=True)
class PosteriorUpdate:
    hypotheses: tuple[str,...]
    posterior: Vector | None
    response_probability: float | None
    status: str
    unknown_hypothesis_possible: bool
