from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import finite_scalar
@dataclass(frozen=True)
class PersistentCapsule:
    capsule_id: str
    document_id: str
    version: str
    parent_version: str | None
    observations: tuple[tuple[str,float],...]
    allowed_query_family: frozenset[str]
    evidence_handles: frozenset[str]
    dependency_versions: tuple[tuple[str,str],...]
    expires_step: int
    versions: VersionSet
    capsule_dependencies: tuple[tuple[str,str],...]=()
    def __post_init__(self):
        if not self.capsule_id or not self.document_id or not self.version or self.version==self.parent_version or len(dict(self.observations))!=len(self.observations) or len(self.observations)>64:raise ContractError('InvalidCapsule','immutable version and bounded observations')
        if not self.allowed_query_family or not self.evidence_handles or self.expires_step<0:raise ContractError('UnboundCapsule','task scope, source and lifespan required')
        if len(set(self.capsule_dependencies))!=len(self.capsule_dependencies) or (self.document_id,self.version) in self.capsule_dependencies:raise ContractError('DependencyCycle','explicit nonself capsule source dependencies')
        for _,v in self.observations:finite_scalar(v)
        self.versions.require('ontology','world','evidence','task')
@dataclass(frozen=True)
class QueryResult:
    value: float | None
    status: str
    source_lookup_required: bool
    capsule_version: str
