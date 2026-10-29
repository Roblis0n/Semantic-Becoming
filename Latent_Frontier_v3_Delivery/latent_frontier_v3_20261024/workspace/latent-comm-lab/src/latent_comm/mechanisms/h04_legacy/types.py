from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Matrix,Vector,matrix,vector,finite_scalar
@dataclass(frozen=True)
class LocalConstraint:
    source_id: str
    A: Matrix
    b: Vector
    temperature: float
    domain: str
    frame: str
    source_state_version: str
    evidence_support: frozenset[str]
    def __post_init__(self):
        object.__setattr__(self,'A',matrix(self.A));object.__setattr__(self,'b',vector(self.b))
        if len(self.A)!=len(self.b) or finite_scalar(self.temperature)<=0:raise ContractError('InvalidConstraint','positive contribution and residual dimensions required')
        if not all((self.source_id,self.domain,self.frame,self.source_state_version)):raise ContractError('UnboundConstraint','source/domain/frame/state required')
@dataclass(frozen=True)
class ConstraintField:
    sources: tuple[LocalConstraint,...]
    anchor: Vector
    anchor_strength: float
    domain: str
    versions: VersionSet
    def __post_init__(self):
        object.__setattr__(self,'anchor',vector(self.anchor));self.versions.require('state','frame','ontology')
        if not self.sources or len(self.sources)>64 or len({s.source_id for s in self.sources})!=len(self.sources):raise ContractError('InvalidSource','nonempty unique bounded contributors')
        if finite_scalar(self.anchor_strength)<=0:raise ContractError('MissingAnchor','positive anchor prevents free zero consensus')
        if any(s.domain!=self.domain or s.frame!=self.versions.frame or len(s.A[0])!=len(self.anchor) for s in self.sources):raise ContractError('NonCommonDomain','use H26 restrictions instead of forcing unrelated fields together')
@dataclass(frozen=True)
class FieldResult:
    state: Vector
    trajectory: tuple[Vector,...]
    residuals: tuple[tuple[str,Vector],...]
    conflicts: tuple[str,...]
    stop_reason: str
    source_versions: tuple[tuple[str,str],...]
