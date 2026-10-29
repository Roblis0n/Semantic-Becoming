from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
@dataclass(frozen=True)
class PrimitiveNode:
    node_id: str
    operation: str
    input_type: str='scalar'
    output_type: str='scalar'
    cost: int=1
    def __post_init__(self):
        if self.operation not in ('input','identity','negate','sum','product') or self.input_type!='scalar' or self.output_type!='scalar' or self.cost<1:raise ContractError('UnsupportedPrimitive','closed typed finite arithmetic primitives only')
@dataclass(frozen=True)
class GraphCandidate:
    candidate_id: str
    nodes: tuple[PrimitiveNode,...]
    edges: tuple[tuple[str,str,int],...]
    output_node: str
    semantic_changes: tuple[tuple[str,str,str,str],...]
    versions: VersionSet
    def __post_init__(self):
        if not self.candidate_id or len(self.nodes)>64 or len(self.edges)>128:raise ContractError('BudgetExhausted','explicit finite graph bounds')
        for component,before,after,certificate in self.semantic_changes:
            if component not in ('O','P','U') or before==after or not certificate:raise ContractError('UnverifiedStructureChange','concept/ISA/learning-rule change needs an actual version transition certificate')
        self.versions.require('ontology','isa','task')
@dataclass(frozen=True)
class SearchResult:
    best: GraphCandidate | None
    loss: float | None
    checked: tuple[str,...]
    total_executed_cost: int
    exhaustive: bool
    status: str
