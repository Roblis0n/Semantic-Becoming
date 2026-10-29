"""Three physically separate roles; provenance metadata never enters inputs."""
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
from latent_comm.core import RoleView,Visibility,VersionSet,ContractError,ErrorCode
from latent_comm.core.views import project_role

@dataclass(frozen=True)
class SupervisionView:
    targets: Mapping[str,object]
    valid_masks: Mapping[str,tuple[bool,...]]
    source_kind: str
    def __post_init__(self) -> None:
        if self.source_kind not in {'finite_program','analytic','future_model_teacher','human_annotation'}:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown supervision provenance')
        object.__setattr__(self,'targets',MappingProxyType(dict(self.targets)))
        object.__setattr__(self,'valid_masks',MappingProxyType(dict(self.valid_masks)))

@dataclass(frozen=True)
class SplitProvenance:
    split: str
    template_signature: str
    manifest_digest: str
    parent_record_ids: tuple[str,...] = ()
    def __post_init__(self) -> None:
        if self.split not in {'train','validation','test','novel_composition','math_fixture'}:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown split')
        if not self.template_signature or not self.manifest_digest:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'split provenance requires signature and immutable manifest')

@dataclass(frozen=True)
class WorldRecord:
    record_id: str
    sender_view: RoleView
    receiver_view: RoleView
    supervision: SupervisionView
    structure_signature: str
    generator_version: str
    split_provenance: SplitProvenance
    evidence_support: tuple[str,...]
    purpose: str
    not_research_data: bool
    def __post_init__(self) -> None:
        if self.sender_view.role!=Visibility.SENDER or self.receiver_view.role!=Visibility.RECEIVER:
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'sender/receiver role mismatch')
        if self.sender_view.versions!=self.receiver_view.versions:
            raise ContractError(ErrorCode.VERSION_MISMATCH,'paired views must refer to the same world/task versions')
        if self.structure_signature!=self.split_provenance.template_signature:
            raise ContractError(ErrorCode.CONFLICT,'split and world structure signatures disagree')
        if self.purpose=='math_fixture':
            if self.not_research_data is not True or self.split_provenance.split!='math_fixture':
                raise ContractError(ErrorCode.RESEARCH_FORBIDDEN,'math fixtures must not become research datasets')
        elif self.not_research_data:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'non-research data needs explicit math_fixture purpose')

@dataclass(frozen=True)
class ProjectionContract:
    public_fields: tuple[str,...]
    sender_fields: tuple[str,...]
    receiver_fields: tuple[str,...]
    allowed_shared_reasons: tuple[tuple[str,str],...]
    def __post_init__(self) -> None:
        reasons=dict(self.allowed_shared_reasons)
        if set(reasons)!=set(self.public_fields) or any(not reason for reason in reasons.values()):
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'every shared field needs a public task reason')
        if len(set(self.public_fields))!=len(self.public_fields):raise ContractError(ErrorCode.INVALID_SCHEMA,'duplicate public field')
    def project(self,world: Mapping[str,object],versions: VersionSet) -> tuple[RoleView,RoleView]:
        sender=project_role(world,role=Visibility.SENDER,feature_fields=self.sender_fields,public_fields=self.public_fields,versions=versions)
        receiver=project_role(world,role=Visibility.RECEIVER,feature_fields=self.receiver_fields,public_fields=self.public_fields,versions=versions)
        return sender,receiver
