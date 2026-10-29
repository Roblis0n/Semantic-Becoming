"""Current-task immutable research prohibition, not a claim of an OS sandbox.

Changing a config flag or presenting a proposed future authorization does not
replace this task's authority. All research entry points reject before imports,
initialization, remote access or model callbacks. Future authorization requires
an independently reviewed session and implementation, not mutation here.
"""
from dataclasses import dataclass
from functools import wraps
from typing import Callable,TypeVar
from latent_comm.core.errors import ContractError,ErrorCode

RESEARCH_STATE='NOT_RUN'
RESEARCH_ACTIONS=frozenset({'research_execution','model_download','model_initialize','model_load','model_forward','model_generate','model_train','model_eval','model_benchmark','model_api','train','fit','forward','generate','eval','benchmark'})
EXTERNAL_DENIALS=frozenset({'purchase','publish','send_message','read_unrelated_private_data','change_system_settings','install_unrecognized','expand_access'})
ALLOWED_ACTIONS=frozenset({'public_read','workspace_read','workspace_write','static_check','stdlib_math_fixture','plan_compile','local_media_export','authorized_zero_new_cost_media'})

@dataclass(frozen=True)
class PolicyDecision:
    action: str
    allowed: bool
    reason: str
    research_state: str = RESEARCH_STATE
    hard_sandbox_guaranteed: bool = False

class CurrentTaskPolicy:
    """Configuration can narrow this authority; it cannot broaden it."""
    def __init__(self,additional_denials: frozenset[str]=frozenset()) -> None:
        self._additional_denials=frozenset(additional_denials)
    def decide(self,action: str, *, media_authorized: bool=False,zero_new_cost: bool=False) -> PolicyDecision:
        if action in RESEARCH_ACTIONS:
            return PolicyDecision(action,False,'Current user task forbids all research-model and research execution.')
        if action in EXTERNAL_DENIALS or action in self._additional_denials or action not in ALLOWED_ACTIONS:
            return PolicyDecision(action,False,'Unknown, external-side-effect, or explicitly denied action.')
        if action=='authorized_zero_new_cost_media' and not (media_authorized and zero_new_cost):
            return PolicyDecision(action,False,'Existing media authorization and verified zero added cost are both required.')
        return PolicyDecision(action,True,'Within current source/design or finite-fixture authority.')
    def require(self,action: str,**kwargs: bool) -> PolicyDecision:
        result=self.decide(action,**kwargs)
        if not result.allowed:raise ContractError(ErrorCode.RESEARCH_FORBIDDEN if action in RESEARCH_ACTIONS else ErrorCode.SCOPE_VIOLATION,result.reason,action)
        return result
    @classmethod
    def from_mapping(cls,value: dict) -> 'CurrentTaskPolicy':
        if any(value.get('models',{}).get(x) is True for x in ('download','initialize','forward','train','benchmark','api_inference','random_tiny_model_for_tests')):
            raise ContractError(ErrorCode.RESEARCH_FORBIDDEN,'A configuration change cannot grant new research authority.')
        requested=frozenset(value.get('allowed_actions',ALLOWED_ACTIONS))
        if not requested<=ALLOWED_ACTIONS:raise ContractError(ErrorCode.SCOPE_VIOLATION,'Configuration attempts to expand allowed actions.')
        return cls(ALLOWED_ACTIONS-requested)

CURRENT_POLICY=CurrentTaskPolicy()
def require_research_action(action: str) -> None:
    """Always fail for this task, including unknown research entrypoint names."""
    raise ContractError(ErrorCode.RESEARCH_FORBIDDEN,f'{action} is NOT_RUN under the current task. A future authorization cannot be inferred from a config.',action)

F=TypeVar('F',bound=Callable)
def locked_research(action: str) -> Callable[[F],F]:
    def decorate(function: F) -> F:
        @wraps(function)
        def guarded(*args,**kwargs):
            require_research_action(action)
            return function(*args,**kwargs)
        return guarded
    return decorate

@dataclass(frozen=True)
class FutureResearchAuthorization:
    """Required future metadata only; construction is not authorization."""
    run_id: str
    model_manifest_sha256: str
    data_manifest_sha256: str
    budget_manifest_sha256: str
    authorization_document_sha256: str
    mode: str
    def validate_description(self) -> tuple[str,...]:
        fields=(self.run_id,self.model_manifest_sha256,self.data_manifest_sha256,self.budget_manifest_sha256,self.authorization_document_sha256,self.mode)
        if any(not isinstance(x,str) or not x for x in fields):raise ContractError(ErrorCode.INVALID_SCHEMA,'Future run description incomplete.')
        if self.mode not in {'train','eval','benchmark'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'Unknown future mode.')
        return ('description_complete','not_authorized_in_current_task')
