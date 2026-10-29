from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Vector,vector
@dataclass(frozen=True)
class BranchState:
    branch_id: str
    ancestors: tuple[str,...]
    base: tuple[tuple[str,Vector],...]
    updates: tuple[tuple[str,Vector],...]
    read_slots: frozenset[str]
    operation_sequence: tuple[str,...]
    commutation_class: str
    evidence: frozenset[str]
    concept_structure: str
    question_transform: str
    transaction_snapshot: str
    versions: VersionSet
    closed: bool=False
    def __post_init__(self):
        if not self.branch_id or len(set(self.ancestors))!=len(self.ancestors) or self.branch_id in self.ancestors:raise ContractError('InvalidAncestry','acyclic distinct branch path')
        if len(dict(self.base))!=len(self.base) or len(dict(self.updates))!=len(self.updates) or not set(dict(self.updates))<=set(dict(self.base)):raise ContractError('InvalidWrites','unique declared slots only')
        for name,v in self.base+self.updates:vector(v)
        if not all((self.concept_structure,self.question_transform,self.transaction_snapshot)):raise ContractError('UnboundStructure','concept/question/transaction identities required')
        self.versions.require('state','ontology','isa','frame')
@dataclass(frozen=True)
class MergeResult:
    state: tuple[tuple[str,Vector],...] | None
    preserved_branches: tuple[BranchState,...]
    status: str
    evidence: frozenset[str]
