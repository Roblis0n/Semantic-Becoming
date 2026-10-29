from dataclasses import dataclass
import math
from latent_comm.core import ContractError, VersionSet
from latent_comm.core.finite import Vector,vector
@dataclass(frozen=True)
class BeliefBranch:
    branch_id: str
    state: Vector | None
    log_weight: float
    semantic_domain: str
    evidence_support: frozenset[str]
    ontology_version: str
    unknown: bool=False
    def __post_init__(self):
        if not self.branch_id or not self.semantic_domain or not self.ontology_version or math.isnan(self.log_weight) or self.log_weight==math.inf:raise ContractError('InvalidBranch','explicit branch/domain/ontology and finite or -inf score')
        if self.unknown!=(self.state is None):raise ContractError('InvalidUnknown','unknown is not a zero vector')
        if self.state is not None:object.__setattr__(self,'state',vector(self.state))
        object.__setattr__(self,'evidence_support',frozenset(self.evidence_support))
@dataclass(frozen=True)
class BeliefPacket:
    branches: tuple[BeliefBranch,...]
    generation_mode: str
    versions: VersionSet
    consumed_evidence: frozenset[str]=frozenset()
    probability_semantics: str='candidate_weights'
    def __post_init__(self):
        if not 1<=len(self.branches)<=64 or len({b.branch_id for b in self.branches})!=len(self.branches):raise ContractError('InvalidBranch','nonempty unique bounded branches')
        if all(b.log_weight==-math.inf for b in self.branches):raise ContractError('ImpossibleEvidence','no nonzero branch mass')
        if self.generation_mode not in ('sequence_mixture','select_then_generate','rerank'):raise ContractError('UnspecifiedGeneration','explicit mixture mode required')
        if self.probability_semantics not in ('candidate_weights','specified_generative_posterior'):raise ContractError('InvalidSemantics','posterior requires an explicit likelihood model')
        self.versions.require('evidence','task')
