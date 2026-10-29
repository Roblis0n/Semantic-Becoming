from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import vector,matrix
@dataclass(frozen=True)
class ScopedCell:
    slot_id: str
    type_tag: str
    value: tuple[float,...]
    session_id: str
    version: str
    def __post_init__(self):
        vector(self.value)
        if not self.slot_id.startswith('state:') or not all((self.type_tag,self.session_id,self.version)):raise ContractError('InvalidScope','only explicitly typed local research state')
@dataclass(frozen=True)
class CapabilityGrant:
    capability_id: str
    principal: str
    session_id: str
    readable_slots: frozenset[str]
    writable_slots: frozenset[str]
    allowed_types: frozenset[str]
    expires_step: int
    evidence_handles: frozenset[str]
    target_views: frozenset[str]
    update_parameters: frozenset[str]
    macro_capabilities: frozenset[str]
    transaction_writes: frozenset[str]
    immutable_goal_digest: str
    versions: VersionSet
    def __post_init__(self):
        if not all((self.capability_id,self.principal,self.session_id,self.immutable_goal_digest)) or self.expires_step<0 or not self.writable_slots<=self.readable_slots:raise ContractError('InvalidScope','explicit session, owner, expiry and read/write bounds')
        if any(not s.startswith('state:') for s in self.readable_slots) or any(not p.startswith(('adapter.','reader.')) for p in self.update_parameters):raise ContractError('ExternalPermissionDenied','research grants cannot address accounts, files, network or control plane')
        if any(not s.startswith(('state:','ontology:','isa:','frame:','world:','evidence:')) for s in self.transaction_writes):raise ContractError('ExternalPermissionDenied','transaction scope is local versioned research state only')
        self.versions.require('state','frame','ontology','isa','task','evidence')
@dataclass(frozen=True)
class ScopedEffect:
    capability_id: str
    operation: str
    read_slots: tuple[str,...]
    write_slots: tuple[str,...]
    matrix: tuple[tuple[float,...],...]
    bias: tuple[float,...]
    type_tag: str
    def __post_init__(self):
        a=matrix(self.matrix);b=vector(self.bias)
        if self.operation not in ('replace_affine','add_affine') or len(a)!=len(b):raise ContractError('InvalidEffect','closed affine data, never executable script')
        if len(set(self.read_slots))!=len(self.read_slots) or len(set(self.write_slots))!=len(self.write_slots):raise ContractError('AliasConflict','duplicate direct slot binding')
@dataclass(frozen=True)
class EffectAudit:
    capability_id: str
    principal: str
    read_slots: tuple[str,...]
    written_slots: tuple[str,...]
    before_versions: tuple[tuple[str,str],...]
    after_versions: tuple[tuple[str,str],...]
    status: str
