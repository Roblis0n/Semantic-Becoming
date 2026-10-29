from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Vector,vector
@dataclass(frozen=True)
class RelationNode:
    node_id: str
    role: str
    features: Vector
    anchor: str | None=None
    def __post_init__(self):object.__setattr__(self,'features',vector(self.features))
@dataclass(frozen=True)
class RelationEdge:
    source: str
    target: str
    relation: str
    semantics: str
    def __post_init__(self):
        if self.semantics not in ('operation','causal','correlation','spatial'):raise ContractError('UnknownRelation','edge semantics must be explicit')
@dataclass(frozen=True)
class RelationPacket:
    nodes: tuple[RelationNode,...]
    edges: tuple[RelationEdge,...]
    versions: VersionSet
    def __post_init__(self):
        ids={n.node_id for n in self.nodes}
        if not 0<len(ids)==len(self.nodes)<=64 or len(self.edges)>128 or len({len(n.features) for n in self.nodes})!=1:raise ContractError('InvalidGraph','bounded unique nodes and feature dimensions')
        if any(e.source not in ids or e.target not in ids for e in self.edges) or len(set(self.edges))!=len(self.edges):raise ContractError('InvalidEdge','edge endpoints and duplicates')
        self.versions.require('ontology','task')
@dataclass(frozen=True)
class MatchResult:
    mappings: tuple[tuple[tuple[str,str],...],...]
    exhaustive: bool
    checked: int
    unmatched_source: tuple[str,...]
    status: str
