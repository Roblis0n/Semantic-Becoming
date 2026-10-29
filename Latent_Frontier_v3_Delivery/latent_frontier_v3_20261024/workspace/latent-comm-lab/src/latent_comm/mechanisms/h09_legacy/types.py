from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import finite_scalar
from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM
@dataclass(frozen=True)
class Intervention:
    variable: str
    value: float
    variable_unit: str
    allowed_variables: frozenset[str]
    world_version: str
    def __post_init__(self):
        finite_scalar(self.value)
        if self.variable not in self.allowed_variables or not self.variable_unit or not self.world_version:raise ContractError('ScopeViolation','intervention variable/type/world must be authorized')
@dataclass(frozen=True)
class CausalQuery:
    semantics: str
    assignments: tuple[tuple[str,float],...]
    outcome: str
    versions: VersionSet
    def __post_init__(self):
        if self.semantics not in ('observe','condition','do'):raise ContractError('UnknownCausalSemantics','do, observe and condition are distinct')
        if len(dict(self.assignments))!=len(self.assignments):raise ContractError('AssignmentConflict','one simultaneous assignment per variable')
        self.versions.require('world','task')
