from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class PublicTerminalConstraint:
    states: tuple[str,...]
    source: str
    task_version: str
    def __post_init__(self):
        if self.source not in ('public_goal','public_boundary') or not self.task_version:raise ContractError('FutureLabelLeak','terminal constraint must originate in the public task')
@dataclass(frozen=True)
class TrajectoryFactorGraph:
    states: tuple[str,...]
    transitions: tuple[tuple[tuple[str,str],...],...]
    start_states: tuple[str,...]
    terminal: PublicTerminalConstraint
    version: str
    def __post_init__(self):
        if not self.states or len(self.states)>64 or len(set(self.states))!=len(self.states) or not 1<=len(self.transitions)<=128:raise ContractError('SolverLimit','finite state domain and horizon required')
        if not set(self.start_states+self.terminal.states)<=set(self.states):raise ContractError('BoundaryInfeasible','boundary names outside state domain')
        if any(a not in self.states or b not in self.states for layer in self.transitions for a,b in layer):raise ContractError('BoundaryInfeasible','transition endpoint absent')
@dataclass(frozen=True)
class BoundaryResult:
    paths: tuple[tuple[str,...],...]
    forward_reachable: tuple[tuple[str,...],...]
    backward_reachable: tuple[tuple[str,...],...]
    status: str
    causality_label: str
    unexplored_prefixes: tuple[tuple[str,...],...]
    steps: int
