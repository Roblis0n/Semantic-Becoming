"""Shared typed contracts; importing these modules never imports neural libraries."""
from .budgets import StepBudget, BudgetMeter, FixtureBudget, ResearchBudget
from .errors import ContractError, ErrorCode, Failure, require
from .refs import ObjectRef, ObjectRegistry, RegisteredObject, Visibility
from .scopes import Scope
from .shapes import TensorSpec, ValueStatus
from .versions import VersionSet
from .types import BuildContext, EffectBundle, EffectRecord, ExecutionSemantics, MetaState, PreparedObject, MigrationResult, Mechanism
from .learning import LossSpec, LossValue, GradientEstimator
from .views import RoleView, project_role
