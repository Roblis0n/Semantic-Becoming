from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Vector,vector,finite_scalar
@dataclass(frozen=True)
class CodeLayer:
    message_id: str
    sequence: int
    depends_on: int
    slots: tuple[int,...]
    integers: tuple[int,...]
    scale: float
    remaining_error_bound: float
    task_family: str
    semantic_scale: str
    versions: VersionSet
    def __post_init__(self):
        if not self.message_id or not 0<=self.sequence<64 or self.depends_on!=self.sequence-1 or len(self.slots)!=len(self.integers) or len(set(self.slots))!=len(self.slots) or any(type(q) is not int for q in self.integers):raise ContractError('InvalidLayer','ordered dependency and unique integer slots')
        if finite_scalar(self.scale)<=0 or finite_scalar(self.remaining_error_bound)<0 or not self.task_family or not self.semantic_scale:raise ContractError('InvalidScale','quantization and semantic scales both explicit')
        self.versions.require('frame','task','state')
@dataclass(frozen=True)
class ProgressiveState:
    message_id: str
    value: Vector
    layers: tuple[CodeLayer,...]
    next_sequence: int
    uncertainty_bound: float | None
    wire_bytes: int
    request_bytes: int
    versions: VersionSet
