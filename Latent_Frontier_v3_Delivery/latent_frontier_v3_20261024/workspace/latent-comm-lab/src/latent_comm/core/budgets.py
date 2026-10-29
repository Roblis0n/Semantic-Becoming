"""Host-enforced finite fixture bounds. These authorize no neural execution."""
from dataclasses import dataclass
from contextvars import ContextVar
from contextlib import contextmanager

_ACTIVE_AGGREGATES = ContextVar("finite_fixture_aggregate_meters", default=())
from .errors import ContractError, ErrorCode

@dataclass(frozen=True)
class StepBudget:
    max_steps: int = 128
    max_dimension: int = 64
    max_cases: int = 64
    max_branches: int = 64
    def __post_init__(self) -> None:
        for name, cap in [('max_steps',128),('max_dimension',64),('max_cases',64),('max_branches',64)]:
            value = getattr(self,name)
            if type(value) is not int or not 0 < value <= cap:
                raise ContractError(ErrorCode.BUDGET_EXHAUSTED, f'{name} must be integer in 1..{cap}')
    def meter(self) -> 'BudgetMeter':
        return BudgetMeter(self)

@dataclass
class BudgetMeter:
    limit: StepBudget
    steps: int = 0
    cases: int = 0
    branches: int = 0
    exhausted: bool = False
    def consume(self, *, steps: int = 0, cases: int = 0, branches: int = 0) -> None:
        amounts = {'steps':steps,'cases':cases,'branches':branches}
        aggregates=_ACTIVE_AGGREGATES.get()
        meters=(self,)+tuple(m for m in aggregates if m is not self)
        for name,value in amounts.items():
            if type(value) is not int or value < 0:
                raise ContractError(ErrorCode.OUT_OF_DOMAIN, 'budget increments must be nonnegative integers')
        # Validate EVERY local and enclosing limit before mutating any counter.
        # A nested function cannot mint additional permission with StepBudget().
        for meter in meters:
            for name,value in amounts.items():
                if getattr(meter,name)+value>getattr(meter.limit,'max_'+name):
                    for enclosing in meters:enclosing.exhausted=True
                    raise ContractError(ErrorCode.BUDGET_EXHAUSTED,f'{name} exhausted before nested work',recoverable=True,obligations=('retain partial object and resume a separately bounded scope',))
        for meter in meters:
            for name,value in amounts.items():setattr(meter,name,getattr(meter,name)+value)
    def dimension(self, value: int) -> None:
        meters=(self,)+tuple(m for m in _ACTIVE_AGGREGATES.get() if m is not self)
        if type(value) is not int or value<0 or any(value>m.limit.max_dimension for m in meters):
            for meter in meters:meter.exhausted=True
            raise ContractError(ErrorCode.BUDGET_EXHAUSTED, 'scalar dimension exceeds declared fixture bound')

@contextmanager
def aggregate_budget(limit: StepBudget):
    """Context-local end-to-end accounting for a finite fixture invocation.

    Child meters retain their local bounds and atomically charge every enclosing
    fixture. This is a resource guard, never authorization for neural execution.
    Context reset is guaranteed on success, partial return and other exceptions.
    """
    if type(limit) is not StepBudget:
        raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'aggregate fixture scope requires the current finite policy budget')
    meter=BudgetMeter(limit)
    token=_ACTIVE_AGGREGATES.set(_ACTIVE_AGGREGATES.get()+(meter,))
    try:yield meter
    finally:_ACTIVE_AGGREGATES.reset(token)

@dataclass(frozen=True)
class ResearchBudget:
    """Future execution budget metadata, not clipped to current fixture limits.

    Construction and compilation are harmless. Obtaining an executing meter is
    a separate policy-gated action; today's task cannot authorize it.
    """
    max_steps: int
    max_dimension: int
    max_cases: int
    max_branches: int
    def __post_init__(self) -> None:
        for name in ('max_steps','max_dimension','max_cases','max_branches'):
            if type(getattr(self,name)) is not int or getattr(self,name)<=0:
                raise ContractError(ErrorCode.OUT_OF_DOMAIN,'research budgets must be explicit positive finite integers')
    def meter(self) -> BudgetMeter:
        from latent_comm.safety.policy import require_research_action
        require_research_action('research_execution')
        return BudgetMeter(self)

FixtureBudget = StepBudget
