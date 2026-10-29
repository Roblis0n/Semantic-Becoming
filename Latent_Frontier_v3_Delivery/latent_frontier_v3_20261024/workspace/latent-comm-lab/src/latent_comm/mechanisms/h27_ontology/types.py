from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class Predicate:
    op: str
    field: str | None = None
    constant: Any = None
    children: tuple['Predicate',...] = ()
    def __post_init__(self):
        from latent_comm.core.views import FORBIDDEN_FIELDS
        arity={'eq':0,'le':0,'not':1,'and':2,'or':2}
        if self.op not in arity or len(self.children)!=arity[self.op]:raise ContractError('UndefinedPredicate','invalid predicate operator or arity')
        if self.op in ('eq','le') and (not self.field or self.field in FORBIDDEN_FIELDS):raise ContractError('RoleLeakage','predicate needs an allowed observable field')
        if self.op not in ('eq','le') and (self.field is not None or self.constant is not None):raise ContractError('UndefinedPredicate','logical node cannot carry atom fields')
        if self.op=='le':finite_scalar(self.constant)
    @property
    def depth(self):return 1+max((c.depth for c in self.children),default=0)
    @property
    def description_length(self):
        # Concrete UTF-8 length of a prefix encoding, not an innovation reward.
        return len((self.op+':'+str(self.field)+':'+repr(self.constant)).encode())+sum(c.description_length for c in self.children)
@dataclass(frozen=True)
class ConceptDefinition:
    concept_id: str
    predicate: Predicate
    parents: tuple[str,...]
    evidence: tuple[str,...]
    domain: tuple[str,...]
    def __post_init__(self):
        def atom_fields(node):
            return {node.field} if node.op in ('eq','le') else set().union(*(atom_fields(c) for c in node.children))
        if not self.concept_id or not self.evidence or self.predicate.depth>8 or not atom_fields(self.predicate)<=set(self.domain):
            raise ContractError('UndefinedPredicate','every nested atom must be within the explicit bounded concept domain and have evidence')
@dataclass(frozen=True)
class OntologySnapshot:
    version: str
    concepts: tuple[ConceptDefinition,...]
    consumers: tuple[tuple[str,str],...] = ()
    def __post_init__(self):
        ids=[c.concept_id for c in self.concepts]
        if not self.version or len(ids)!=len(set(ids)):raise ContractError('DanglingConcept','ontology IDs must be unique')
        if any(c not in ids for _,c in self.consumers):raise ContractError('DanglingConcept','consumer references absent concept')
@dataclass(frozen=True)
class DistinctionWitness:
    definition: ConceptDefinition
    values: tuple[bool | None,...]
    old_equivalent_pairs: tuple[tuple[int,int],...]
    equivalent_sources: tuple[Predicate,...]
    objective: float
    candidates_examined: int
@dataclass(frozen=True)
class OntologyDelta:
    before: OntologySnapshot
    after: OntologySnapshot
    reader_migrations: tuple[tuple[str,str,str],...]
    retired: tuple[str,...]
