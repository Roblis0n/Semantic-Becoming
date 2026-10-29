from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Matrix,matrix
@dataclass(frozen=True)
class ProtocolMember:
    model_id: str
    model_revision: str
    tokenizer_revision: str
    writer: Matrix
    reader: Matrix
    capabilities: frozenset[str]
    behavior_coordinates: tuple[str,...]
    interface_trained: bool
    versions: VersionSet
    def __post_init__(self):
        object.__setattr__(self,'writer',matrix(self.writer));object.__setattr__(self,'reader',matrix(self.reader))
        if len(self.reader[0])!=len(self.writer) or not self.model_id or not self.model_revision or not self.tokenizer_revision or not self.behavior_coordinates:raise ContractError('UnboundProtocol','explicit revision/tokenizer/behavior and interface shapes')
        self.versions.require('frame','task','ontology')
@dataclass(frozen=True)
class PairPlan:
    pairs: tuple[tuple[str,str],...]
    held_out_pairs: frozenset[tuple[str,str]]
    untrained_models: frozenset[str]
    seed: int
