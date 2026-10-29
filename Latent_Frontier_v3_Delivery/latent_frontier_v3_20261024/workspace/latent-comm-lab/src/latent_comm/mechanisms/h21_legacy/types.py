from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import finite_scalar
@dataclass(frozen=True)
class PortfolioNode:
    node_id: str
    anchor_state: tuple[tuple[str,float],...]
    intervention: tuple[tuple[str,float],...]
    response_packet_ref: str | None
    continuation_ref: str | None
    lineage: tuple[str,...]
    branch_kind: str
    question_id: str
    world_id: str
    selection_basis: str
    evidence: frozenset[str]
    versions: VersionSet
    synthetic: bool=False
    def __post_init__(self):
        if not self.node_id or self.branch_kind not in ('answer','question','concept','world') or not all((self.question_id,self.world_id,self.selection_basis)):raise ContractError('InvalidBranch','explicit semantic branch identity and selection basis')
        if len(dict(self.anchor_state))!=len(self.anchor_state) or len(dict(self.intervention))!=len(self.intervention) or self.node_id in self.lineage:raise ContractError('InvalidBranch','immutable state, intervention and acyclic lineage')
        for _,value in self.anchor_state+self.intervention:finite_scalar(value)
        self.versions.require('state','ontology','world','task','evidence')
@dataclass(frozen=True)
class PublicGoal:
    variable: str
    target: float
    source_role: str='public'
    def __post_init__(self):
        finite_scalar(self.target)
        if not self.variable or self.source_role!='public':raise ContractError('FutureLabelLeak','online selector can use only public goal, never unobserved future payoff')
@dataclass(frozen=True)
class PortfolioResult:
    nodes: tuple[PortfolioNode,...]
    edges: tuple[tuple[str,str],...]
    frontier: tuple[str,...]
    best_id: str | None
    evaluations: int
    reused: int
    status: str
    impossibility_proven: bool=False
