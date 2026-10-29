from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import vector,matrix
@dataclass(frozen=True)
class StateCell:
    cell_id: str
    type_tag: str
    value: tuple[float,...]
    frame: str
    readers: frozenset[str]
    writers: frozenset[str]
    partition: str
    revision: int
    def __post_init__(self):
        vector(self.value)
        if not all((self.cell_id,self.type_tag,self.frame,self.partition)) or not self.writers or not self.writers<=self.readers or self.revision<0:raise ContractError('OwnershipViolation','explicit immutable cell capability bounds')
@dataclass(frozen=True)
class PartitionState:
    partitions: tuple[tuple[str,frozenset[str]],...]
    cells: tuple[StateCell,...]
    open_cache_refs: frozenset[str]
    version: str
    versions: VersionSet
    def __post_init__(self):
        groups=dict(self.partitions)
        if len(groups)!=len(self.partitions) or any(not k or not v for k,v in self.partitions) or len(self.cells)>64 or len({c.cell_id for c in self.cells})!=len(self.cells):raise ContractError('InvalidPartition','finite unique nonempty partitions and cells')
        for c in self.cells:
            if c.partition not in groups or not groups[c.partition]<=c.readers or not groups[c.partition]&c.writers:raise ContractError('OwnershipViolation','partition membership must already be authorized to read and have a writer')
        if not self.version:raise ContractError('VersionMismatch','partition version required')
        self.versions.require('state','frame','ontology','isa','task')
@dataclass(frozen=True)
class StateReference:
    cell_id: str
    revision: int
    partition_version: str
    frame: str
@dataclass(frozen=True)
class PartitionAction:
    kind: str
    sources: tuple[str,...]
    target: str
    members: frozenset[str]
    selected_cells: frozenset[str]
    expected_version: str
    new_version: str
    def __post_init__(self):
        if self.kind not in ('split','join','handoff','isolate') or not self.sources or len(set(self.sources))!=len(self.sources) or not self.target or not self.members or self.expected_version==self.new_version:raise ContractError('InvalidTransition','finite typed partition action and new version required')
@dataclass(frozen=True)
class CoordinateMigration:
    cell_id: str
    source_frame: str
    target_frame: str
    mapping: tuple[tuple[float,...],...]
    certificate: str
    def __post_init__(self):
        matrix(self.mapping)
        if not self.certificate or not self.source_frame or not self.target_frame:raise ContractError('UnboundMap','frame migration needs explicit certificate')
@dataclass(frozen=True)
class TransitionRecord:
    before: PartitionState
    after: PartitionState
    action: PartitionAction
    invalidated_refs: tuple[StateReference,...]
    closed_cache_refs: frozenset[str]
