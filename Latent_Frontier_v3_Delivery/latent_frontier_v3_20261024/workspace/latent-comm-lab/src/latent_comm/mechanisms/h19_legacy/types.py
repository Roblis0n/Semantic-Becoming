from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import matrix,vector
@dataclass(frozen=True)
class TeacherTrace:
    trace_id: str
    instance_id: str
    message_ref: str
    operation_ids: tuple[str,...]
    evidence_sources: frozenset[str]
    task_family: str
    teacher_revision: str
    expires_step: int
    versions: VersionSet
    def __post_init__(self):
        if not all((self.trace_id,self.instance_id,self.message_ref,self.task_family,self.teacher_revision)) or not self.evidence_sources or self.expires_step<0:raise ContractError('MissingProvenance','trace lifecycle and source required')
        self.versions.require('state','ontology','isa','task','evidence')
@dataclass(frozen=True)
class ConsolidatedAdapter:
    adapter_id: str
    version: str
    parent_version: str | None
    parameter_digest: str
    trained_trace_ids: frozenset[str]
    trained_instance_ids: frozenset[str]
    evidence_sources: frozenset[str]
    writable_groups: frozenset[str]
    task_family: str
    base_revision: str
    versions: VersionSet
    origin: str='distillation'
    def __post_init__(self):
        if not all((self.adapter_id,self.version,self.parameter_digest,self.task_family,self.base_revision)) or not self.trained_trace_ids or not self.evidence_sources:raise ContractError('MissingProvenance','persistent adaptation requires training source and parameter artifact digest')
        if not self.writable_groups or any(not g.startswith(('adapter.','reader.')) for g in self.writable_groups):raise ContractError('WriteScopeViolation','only declared adapter/reader parameters')
        if self.origin not in ('distillation','operator_hypernetwork','finite_affine_compilation'):raise ContractError('InvalidOrigin','cache is not a learned skill')
        self.versions.require('state','ontology','isa','task','evidence')
@dataclass(frozen=True)
class AffineSkill:
    weight: tuple[tuple[float,...],...]
    bias: tuple[float,...]
    source_operations: tuple[str,...]
    def __post_init__(self):
        a=matrix(self.weight);b=vector(self.bias)
        if len(a)!=len(a[0]) or len(a)!=len(b):raise ContractError('ShapeMismatch','fixed affine operation on a single state space')
