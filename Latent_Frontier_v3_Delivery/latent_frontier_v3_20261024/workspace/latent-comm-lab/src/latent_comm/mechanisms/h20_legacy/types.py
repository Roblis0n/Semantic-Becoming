from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
@dataclass(frozen=True)
class CognitiveClock:
    physical_step: int
    phase: str
    phase_index: int
    path_id: str
    path_index: int
    causal: tuple[tuple[str,int],...]
    def __post_init__(self):
        if any(type(x) is not int or x<0 for x in (self.physical_step,self.phase_index,self.path_index)) or not self.phase or not self.path_id:raise ContractError('InvalidClock','physical schedule, phase and path have separate nonnegative indices')
        if len(dict(self.causal))!=len(self.causal) or any(not a or type(v) is not int or v<0 for a,v in self.causal):raise ContractError('InvalidClock','vector clock actors unique and nonnegative')
@dataclass(frozen=True)
class CognitiveEvent:
    event_id: str
    kind: str
    source: str
    clock: CognitiveClock
    dependencies: frozenset[str]
    source_state_version: str
    receiver_versions: tuple[tuple[str,str],...]
    earliest_step: int
    expires_step: int
    stale_policy: str
    payload_ref: str
    versions: VersionSet
    def __post_init__(self):
        if self.kind not in ('evidence_ready','branch_resolved','constraint_changed','continuation_requested'):raise ContractError('InvalidEvent','unknown cognitive event')
        if not all((self.event_id,self.source,self.source_state_version,self.payload_ref)) or self.event_id in self.dependencies:raise ContractError('InvalidEvent','event identity and acyclic direct dependencies')
        if not 0<=self.earliest_step<=self.expires_step or self.stale_policy not in ('reject','recompute','remap'):raise ContractError('InvalidEvent','explicit lifetime and stale policy')
        if len(dict(self.receiver_versions))!=len(self.receiver_versions):raise ContractError('VersionConflict','unique receiver dependencies')
        self.versions.require('state','ontology','world','evidence')
@dataclass(frozen=True)
class VersionRemap:
    map_id: str
    source_requirements: tuple[tuple[str,str],...]
    target_requirements: tuple[tuple[str,str],...]
    original_payload: str
    remapped_payload: str
    semantic_certificate: str
    def __post_init__(self):
        if not all((self.map_id,self.original_payload,self.remapped_payload,self.semantic_certificate)):raise ContractError('UnboundRemap','explicit recomputed payload and semantic certificate required')
@dataclass(frozen=True)
class EventDecision:
    event_id: str
    physical_step: int
    status: str
    payload_ref: str | None
    source_phase: str
    source_path: tuple[str,int]
