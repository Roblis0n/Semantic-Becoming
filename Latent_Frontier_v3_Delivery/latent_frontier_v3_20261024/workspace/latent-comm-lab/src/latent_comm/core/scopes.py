"""Research object scopes do not grant host actions or mutate control policy."""
from dataclasses import dataclass
from .errors import ContractError, ErrorCode

CONTROL_COMPONENTS=frozenset({'external_goal','user_authorization','execution_policy','budget_authority','publication_permission','host','credentials'})
RESEARCH_COMPONENTS=frozenset({'Z','F','O','P','Q','V','K','W','U','E'})
@dataclass(frozen=True)
class Scope:
    scope_id: str
    readers: frozenset[str]
    writable_components: frozenset[str]
    object_ids: frozenset[str] = frozenset()
    expires_step: int | None = None
    def __post_init__(self) -> None:
        object.__setattr__(self,'readers',frozenset(self.readers))
        object.__setattr__(self,'writable_components',frozenset(self.writable_components))
        object.__setattr__(self,'object_ids',frozenset(self.object_ids))
        if not self.scope_id or not self.readers:
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'scope needs identity and readers')
        if not self.writable_components <= RESEARCH_COMPONENTS:
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'control-plane or unknown component is not writable')
        if self.expires_step is not None and (type(self.expires_step) is not int or self.expires_step < 0):
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'invalid expiry')
    def check(self, actor: str, *, object_id: str | None = None, writes: frozenset[str] = frozenset(), step: int = 0) -> None:
        if actor not in self.readers or (self.expires_step is not None and step > self.expires_step):
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'actor outside scope or expired')
        if object_id is not None and self.object_ids and object_id not in self.object_ids:
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'object outside scope')
        if not writes <= self.writable_components:
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'write set exceeds scope')
    def restrict(self, other: 'Scope') -> 'Scope':
        readers=self.readers & other.readers
        if not readers: raise ContractError(ErrorCode.SCOPE_VIOLATION,'empty reader intersection')
        objects=(self.object_ids & other.object_ids) if self.object_ids and other.object_ids else self.object_ids or other.object_ids
        if self.object_ids and other.object_ids and not objects:
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'empty object intersection')
        expiries=[e for e in [self.expires_step,other.expires_step] if e is not None]
        return Scope(self.scope_id+'&'+other.scope_id,readers,self.writable_components & other.writable_components,objects,min(expiries) if expiries else None)
