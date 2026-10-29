from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class PolynomialConstraint:
    terms: tuple[tuple[float,tuple[int,...]],...]
    relation: str
    rhs: float
    def __post_init__(self):
        if self.relation not in ('eq','le','ge') or not self.terms:raise ContractError('OutOfDomain','finite polynomial constraint required')
        finite_scalar(self.rhs)
        for coefficient,powers in self.terms:
            finite_scalar(coefficient)
            if any(type(p) is not int or not 0<=p<=8 for p in powers):raise ContractError('OutOfDomain','bounded nonnegative polynomial powers required')
@dataclass(frozen=True)
class QuestionIR:
    question_id: str
    variables: tuple[str,...]
    domains: tuple[Vector,...]
    constraints: tuple[PolynomialConstraint,...]
    version: str
    evidence: tuple[str,...] = ()
    def __post_init__(self):
        import math
        if not self.question_id or not self.version or not self.variables or len(set(self.variables))!=len(self.variables) or len(self.variables)!=len(self.domains):raise ContractError('OutOfDomain','named finite variable domains required')
        for d in self.domains:vector(d)
        if math.prod(len(d) for d in self.domains)>64:raise ContractError('TransformBudget','Cartesian answer domain exceeds 64 cases')
        if any(len(p)!=len(self.variables) for c in self.constraints for _,p in c.terms):raise ContractError('OutOfDomain','constraint variable arity differs')
@dataclass(frozen=True)
class AnswerMap:
    matrix: Matrix
    offset: Vector
    source_question: str
    target_question: str
    def __post_init__(self):
        a=matrix(self.matrix);b=vector(self.offset)
        if len(a)!=len(b):raise ContractError('OutOfDomain','answer-map output and offset dimensions differ')
@dataclass(frozen=True)
class QuestionTransform:
    source: QuestionIR
    target: QuestionIR
    backtranslation: AnswerMap
    claimed_relation: str
    preconditions: tuple[str,...]
@dataclass(frozen=True)
class RelationWitness:
    relation: str
    sound: bool
    complete: bool
    source_solutions: tuple[Vector,...]
    target_solutions: tuple[Vector,...]
    mapped_solutions: tuple[Vector,...]
    invalid_answers: tuple[Vector,...]
    lost_solutions: tuple[Vector,...]

@dataclass(frozen=True)
class RewriteRule:
    rule_id: str
    kind: str
    constraint: PolynomialConstraint | None = None
    auxiliary_name: str = ''
    auxiliary_domain: Vector = ()
    auxiliary_coefficients: Vector = ()
    auxiliary_offset: float = 0.
    drop_constraint_index: int = 0
    def __post_init__(self):
        if not self.rule_id or self.kind not in ('strengthen','relax','introduce_auxiliary'):
            raise ContractError('RelationUnproven','unknown typed rewrite rule')

@dataclass(frozen=True)
class TransformLibrary:
    rules: tuple[RewriteRule,...]
    version: str
    def __post_init__(self):
        if not self.version or len({r.rule_id for r in self.rules})!=len(self.rules):
            raise ContractError('RelationUnproven','versioned unique rewrite library required')

@dataclass(frozen=True)
class QuestionEdge:
    edge_id: str
    source_id: str
    target_id: str | None
    rule_id: str
    transform: QuestionTransform | None
    witness: RelationWitness | None
    rejection: str | None

@dataclass(frozen=True)
class QuestionGraph:
    nodes: tuple[QuestionIR,...]
    edges: tuple[QuestionEdge,...]
    remaining_frontier: tuple[tuple[str,int],...]
    status: str
    library_version: str
