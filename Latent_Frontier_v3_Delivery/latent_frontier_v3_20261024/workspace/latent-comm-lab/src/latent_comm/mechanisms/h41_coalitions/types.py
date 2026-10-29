from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class AgentCapability:
    name: str
    provides: tuple[str,...]
    requires: tuple[str,...]
    cost: float
@dataclass(frozen=True)
class CoalitionContract:
    agents: tuple[AgentCapability,...]
    required_outputs: tuple[str,...]
    public_inputs: tuple[str,...]
    resource_budget: float
    credit_is_money: bool = False
    def __post_init__(self):
        finite_scalar(self.resource_budget)
        if self.credit_is_money or self.resource_budget<0 or len({a.name for a in self.agents})!=len(self.agents):raise ContractError('CreditConflict','unique agents, nonnegative internal resource budget and nonfinancial credit required')
        for a in self.agents:
            if finite_scalar(a.cost)<0:raise ContractError('CoalitionBudget','negative agent resource cost')
@dataclass(frozen=True)
class CoalitionGame:
    players: tuple[str,...]
    values: tuple[tuple[tuple[str,...],float],...]
    version: str
    def __post_init__(self):
        if len(set(self.players))!=len(self.players) or not self.players or len(self.players)>64 or not self.version:raise ContractError('UndefinedValue','finite unique player universe and value version required')
        keys=[]
        for subset,value in self.values:
            if not set(subset)<=set(self.players) or len(set(subset))!=len(subset):raise ContractError('UndefinedValue','subset outside players')
            keys.append(frozenset(subset));finite_scalar(value)
        if len(set(keys))!=len(keys):raise ContractError('CreditConflict','duplicate coalition valuation')
@dataclass(frozen=True)
class ContributionRecord:
    contributions: tuple[tuple[str,float | None],...]
    variances: tuple[tuple[str,float | None],...]
    exact: bool
    samples: int
    missing_coalitions: tuple[tuple[str,...],...]
    efficiency_residual: float | None
    status: str
