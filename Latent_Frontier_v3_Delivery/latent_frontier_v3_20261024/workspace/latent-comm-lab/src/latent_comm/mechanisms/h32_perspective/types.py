from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class ImmutableGoal:
    canonical_text: str
    digest: str
    def __post_init__(self):
        import hashlib
        if hashlib.sha256(self.canonical_text.encode()).hexdigest()!=self.digest:raise ContractError('GoalMutation','goal content differs from immutable digest')
@dataclass(frozen=True)
class ObjectiveFrame:
    goal: ImmutableGoal
    costs: Vector
    weights: Vector
    constraint_matrix: Matrix
    constraint_bounds: Vector
    version: str
    def __post_init__(self):
        c=vector(self.costs);w=vector(self.weights);a=matrix(self.constraint_matrix);b=vector(self.constraint_bounds)
        if len(c)!=len(w) or len(a[0])!=len(c) or len(a)!=len(b):raise ContractError('PreferenceUndefined','objective and hard constraint dimensions differ')
        if any(x<0 for x in w) or abs(sum(w)-1)>1e-9:raise ContractError('PreferenceUndefined','original weights must lie in declared simplex')
@dataclass(frozen=True)
class GoalPreservingView:
    goal_digest: str
    transformed_costs: Vector
    dual_weights: Vector
    preference_residual: Vector
    original_value: float
    transformed_value: float
    status: str
    original_constraints_satisfied: bool
    source_version: str
    target_version: str
