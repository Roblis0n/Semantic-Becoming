"""Physical whitelist projection before adapters; never pass the full world."""
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
from .errors import ContractError, ErrorCode
from .refs import ObjectRef, Visibility, ObjectRegistry
from .versions import VersionSet

# Authoritative role-input classification shared by registry, projection and templates.
FIELD_CLASSIFICATION={
    **{name:'supervision_only' for name in ('label','labels','hidden_solution','oracle_trace','supervision','supervisor_view','supervision_view','answer_key','query_labels')},
    **{name:'record_metadata_only' for name in ('world_seed','sample_id','split_id','record_id','manifest_digest')},
}
FORBIDDEN_FIELDS=frozenset(FIELD_CLASSIFICATION)
def freeze_public(value: object, path: str = '') -> object:
    if isinstance(value,Mapping):
        if any(not isinstance(k,str) for k in value):raise ContractError(ErrorCode.ROLE_LEAKAGE,'view keys must be strings',path)
        bad=set(value)&FORBIDDEN_FIELDS
        if bad:raise ContractError(ErrorCode.ROLE_LEAKAGE,f'forbidden fields {sorted(bad)}',path)
        return MappingProxyType({k:freeze_public(v,path+'.'+k) for k,v in value.items()})
    if isinstance(value,(tuple,list)):
        return tuple(freeze_public(v,f'{path}[{i}]') for i,v in enumerate(value))
    if value is None or isinstance(value,(str,int,float,bool,ObjectRef)):
        return value
    raise ContractError(ErrorCode.ROLE_LEAKAGE,'opaque unvalidated object cannot enter a role view',path)

@dataclass(frozen=True)
class RoleView:
    role: Visibility
    public_task: Mapping[str,object]
    features: Mapping[str,object]
    versions: VersionSet
    def __post_init__(self) -> None:
        if self.role not in {Visibility.SENDER,Visibility.RECEIVER}:
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'model inputs must be sender or receiver')
        object.__setattr__(self,'public_task',freeze_public(self.public_task))
        object.__setattr__(self,'features',freeze_public(self.features))
    def resolve_refs(self,registry: ObjectRegistry,types: Mapping[str,str],actor: str) -> None:
        def walk(v: object) -> None:
            if isinstance(v,ObjectRef):
                if v.value not in types:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'reference type contract is missing')
                registry.resolve(v,expected_type=types[v.value],versions=self.versions,actor=actor,role=self.role)
            elif isinstance(v,Mapping):
                for x in v.values():walk(x)
            elif isinstance(v,tuple):
                for x in v:walk(x)
        walk(self.public_task);walk(self.features)

def project_role(world: Mapping[str,object], *, role: Visibility, feature_fields: tuple[str,...], public_fields: tuple[str,...], versions: VersionSet) -> RoleView:
    selected=set(feature_fields)|set(public_fields)
    if selected & FORBIDDEN_FIELDS:raise ContractError(ErrorCode.ROLE_LEAKAGE,'forbidden whitelist member')
    absent=selected-set(world)
    if absent:raise ContractError(ErrorCode.ROLE_LEAKAGE,f'whitelisted fields absent: {sorted(absent)}')
    return RoleView(role,{k:world[k] for k in public_fields},{k:world[k] for k in feature_fields},versions)
