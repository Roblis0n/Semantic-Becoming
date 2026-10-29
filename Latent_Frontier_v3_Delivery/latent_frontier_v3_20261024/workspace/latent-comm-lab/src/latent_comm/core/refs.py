"""Object references resolve only within an explicitly populated typed registry."""
from dataclasses import dataclass, fields, is_dataclass
from collections.abc import Mapping
from enum import Enum
import re
from typing import Generic, TypeVar
from .errors import ContractError, ErrorCode
from .versions import VersionSet
from .scopes import Scope

T=TypeVar('T')
class Visibility(str,Enum):
    PUBLIC='public'
    SENDER='sender'
    RECEIVER='receiver'
    SUPERVISION='supervision'

@dataclass(frozen=True)
class ObjectRef:
    value: str
    def __post_init__(self) -> None:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]*(?::[A-Za-z0-9_.-]+)+',self.value) or '..' in self.value:
            raise ContractError(ErrorCode.UNBOUND_REFERENCE,'reference must be a namespaced object ID, not a path/URL')
    @property
    def namespace(self) -> str:
        return self.value.split(':',1)[0]

@dataclass(frozen=True)
class RegisteredObject(Generic[T]):
    ref: ObjectRef
    type_name: str
    value: T
    versions: VersionSet
    required_axes: tuple[str,...]
    scope: Scope
    visibility: Visibility
    dependencies: tuple[ObjectRef,...] = ()
    synthetic: bool = False
    def __post_init__(self) -> None:
        if not self.type_name: raise ContractError(ErrorCode.UNBOUND_REFERENCE,'object type must be explicit')
        self.versions.require(*self.required_axes)

class ObjectRegistry:
    def __init__(self) -> None:
        self._objects: dict[str,RegisteredObject] = {}
    def register(self, obj: RegisteredObject) -> None:
        if obj.ref.value in self._objects:
            raise ContractError(ErrorCode.CONFLICT,'object identity is immutable; register a new versioned ID')
        embedded = _embedded_references(obj.value)
        undeclared = embedded - {ref.value for ref in obj.dependencies}
        if undeclared:
            raise ContractError(ErrorCode.ROLE_LEAKAGE, f'embedded references missing from dependency contract: {sorted(undeclared)}')
        for ref in obj.dependencies:
            if ref.value not in self._objects:
                raise ContractError(ErrorCode.UNBOUND_REFERENCE,f'unregistered dependency {ref.value}')
        self._objects[obj.ref.value]=obj
    def resolve(self, ref: ObjectRef, *, expected_type: str, versions: VersionSet, actor: str, role: Visibility, step: int = 0) -> object:
        obj=self._objects.get(ref.value)
        if obj is None: raise ContractError(ErrorCode.UNBOUND_REFERENCE,ref.value)
        if obj.type_name!=expected_type: raise ContractError(ErrorCode.UNBOUND_REFERENCE,f'expected {expected_type}, found {obj.type_name}')
        if not obj.versions.matches(versions,obj.required_axes):
            raise ContractError(ErrorCode.VERSION_MISMATCH,ref.value)
        self._validate_access(obj,versions,actor,role,step,set())
        return obj.value
    def _validate_access(self,obj: RegisteredObject,versions: VersionSet,actor: str,role: Visibility,step: int,seen: set[str]) -> None:
        if obj.ref.value in seen: raise ContractError(ErrorCode.CONFLICT,'reference dependency cycle')
        seen=seen | {obj.ref.value}
        # Payload identity may be live; revalidate mutable containers without copying tensors.
        undeclared = _embedded_references(obj.value) - {ref.value for ref in obj.dependencies}
        if undeclared:
            raise ContractError(ErrorCode.ROLE_LEAKAGE, f'payload changed to include undeclared references: {sorted(undeclared)}')
        if not obj.versions.matches(versions,obj.required_axes):
            raise ContractError(ErrorCode.VERSION_MISMATCH, f'stale dependency {obj.ref.value}')
        obj.scope.check(actor,object_id=obj.ref.value,step=step)
        if role != Visibility.SUPERVISION and obj.visibility not in {Visibility.PUBLIC,role}:
            raise ContractError(ErrorCode.ROLE_LEAKAGE,f'{obj.visibility.value} object cannot enter {role.value}')
        if role != Visibility.SUPERVISION:
            _validate_role_payload(obj.value)
        for dep in obj.dependencies:
            self._validate_access(self._objects[dep.value],versions,actor,role,step,seen)
    def invalidate(self, refs: frozenset[str]) -> tuple[str,...]:
        invalid=set(refs);changed=True
        while changed:
            changed=False
            for key,obj in self._objects.items():
                if key not in invalid and any(d.value in invalid for d in obj.dependencies):
                    invalid.add(key);changed=True
        for key in invalid:self._objects.pop(key,None)
        return tuple(sorted(invalid))


def _children(value: object) -> tuple[object,...]:
    if isinstance(value,Mapping): return tuple(value.values())
    if isinstance(value,(tuple,list,set,frozenset)): return tuple(value)
    if is_dataclass(value) and not isinstance(value,type): return tuple(getattr(value,f.name) for f in fields(value))
    return ()

def _embedded_references(value: object, active: frozenset[int]=frozenset()) -> set[str]:
    if isinstance(value,ObjectRef): return {value.value}
    children=_children(value)
    if not children: return set()
    if id(value) in active: raise ContractError(ErrorCode.CONFLICT,'cyclic object payload')
    if len(active)>=64: raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'object payload nesting exceeds finite bound')
    refs=set()
    for child in children: refs.update(_embedded_references(child,active | {id(value)}))
    return refs

def _validate_role_payload(value: object, active: frozenset[int]=frozenset(), path: str='payload') -> None:
    from .views import FORBIDDEN_FIELDS
    if isinstance(value,ObjectRef) or value is None or isinstance(value,(str,int,float,bool,Enum)): return
    if id(value) in active: raise ContractError(ErrorCode.CONFLICT,'cyclic role payload',path)
    if len(active)>=64: raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'role payload nesting exceeds finite bound',path)
    if isinstance(value,Mapping):
        if any(not isinstance(key,str) for key in value): raise ContractError(ErrorCode.ROLE_LEAKAGE,'role payload keys must be strings',path)
        bad=set(value) & FORBIDDEN_FIELDS
        if bad: raise ContractError(ErrorCode.ROLE_LEAKAGE,f'forbidden referenced fields {sorted(bad)}',path)
        children=tuple((key,child) for key,child in value.items())
    elif is_dataclass(value) and not isinstance(value,type):
        bad={f.name for f in fields(value)} & FORBIDDEN_FIELDS
        if bad: raise ContractError(ErrorCode.ROLE_LEAKAGE,f'forbidden referenced fields {sorted(bad)}',path)
        children=tuple((f.name,getattr(value,f.name)) for f in fields(value))
    elif isinstance(value,(tuple,list,set,frozenset)):
        children=tuple((str(i),child) for i,child in enumerate(value))
    else:
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'opaque referenced payload requires an explicit typed role projection',path)
    for name,child in children: _validate_role_payload(child,active | {id(value)},path+'.'+name)
