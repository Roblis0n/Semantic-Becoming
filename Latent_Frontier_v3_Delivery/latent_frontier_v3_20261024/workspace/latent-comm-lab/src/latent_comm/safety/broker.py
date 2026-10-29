"""Explicit action classification, finite fixture attestations and path fences."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable,TypeVar
from latent_comm.core import ContractError,ErrorCode,FixtureBudget
from latent_comm.packets.storage import resolve_workspace_path
from .policy import CurrentTaskPolicy,PolicyDecision

T=TypeVar('T')
@dataclass(frozen=True)
class FixtureDeclaration:
    purpose: str
    neural_models: bool
    bulk_dataset_generation: bool
    max_scalar_dimension: int
    max_steps: int
    max_cases: int
    def validate(self) -> FixtureBudget:
        if self.purpose!='math_fixture' or self.neural_models is not False or self.bulk_dataset_generation is not False:
            raise ContractError(ErrorCode.RESEARCH_FORBIDDEN,'Only declared non-neural, non-dataset finite fixtures may execute.')
        return FixtureBudget(self.max_steps,self.max_scalar_dimension,self.max_cases)

@dataclass(frozen=True)
class ActionRequest:
    action: str
    target: str
    fixture: FixtureDeclaration | None = None
    media_authorized: bool = False
    zero_new_cost: bool = False

class ActionBroker:
    def __init__(self,workspace_root: Path,policy: CurrentTaskPolicy | None=None) -> None:
        self.root=workspace_root.resolve()
        self.policy=policy or CurrentTaskPolicy()
        self.audit: list[PolicyDecision]=[]
    def authorize(self,request: ActionRequest) -> PolicyDecision:
        result=self.policy.decide(request.action,media_authorized=request.media_authorized,zero_new_cost=request.zero_new_cost)
        self.audit.append(result)
        if not result.allowed: self.policy.require(request.action,media_authorized=request.media_authorized,zero_new_cost=request.zero_new_cost)
        if request.action in {'workspace_read','workspace_write','local_media_export'}:
            resolve_workspace_path(self.root,request.target)
        if request.action=='stdlib_math_fixture':
            if request.fixture is None:raise ContractError(ErrorCode.RESEARCH_FORBIDDEN,'Fixture declaration missing.')
            request.fixture.validate()
        if request.action=='public_read':
            from urllib.parse import urlsplit
            u=urlsplit(request.target)
            if u.scheme!='https' or not u.netloc or u.username or u.password:
                raise ContractError(ErrorCode.SCOPE_VIOLATION,'Public reads require a credential-free HTTPS URL.')
        return result
    def execute_local(self,request: ActionRequest,operation: Callable[[],T]) -> T:
        if request.action not in {'workspace_read','workspace_write','static_check','stdlib_math_fixture','plan_compile','local_media_export'}:
            raise ContractError(ErrorCode.SCOPE_VIOLATION,'This local broker does not execute external services.')
        self.authorize(request)
        return operation()
