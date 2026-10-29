from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class TaskGenome:
    task_id: str
    operation: str
    offset: float
    conditional: bool
    threshold: float
    inverse: bool
    parent_ids: tuple[str,...]
    version: str
    def __post_init__(self):
        if self.operation!='add' or not self.task_id or not self.version:raise ContractError('InvalidMutation','finite prototype task grammar supports typed affine addition only')
        finite_scalar(self.offset);finite_scalar(self.threshold)
@dataclass(frozen=True)
class ProtocolGenome:
    protocol_id: str
    operators: tuple[str,...]
    concepts: tuple[str,...]
    parent_ids: tuple[str,...]
    version: str
    def __post_init__(self):
        if any(o not in ('add','compare','inverse') for o in self.operators) or len(set(self.operators))!=len(self.operators):raise ContractError('InvalidMutation','protocol operators must be typed whitelist members')
@dataclass(frozen=True)
class MutationGrammar:
    task_mutations: tuple[str,...]
    protocol_mutations: tuple[str,...]
@dataclass(frozen=True)
class TransferAttempt:
    protocol_id: str
    task_id: str
    status: str
    missing_operators: tuple[str,...]
    competence: None = None
    evidence_kind: str = 'static_expressibility_not_model_competence'
@dataclass(frozen=True)
class EcologyState:
    tasks: tuple[TaskGenome,...]
    protocols: tuple[ProtocolGenome,...]
    archive: tuple[tuple[str,tuple[str,...]],...]
    lineage: tuple[tuple[str,tuple[str,...]],...]
    transfer_graph: tuple[TransferAttempt,...]
    rejected_mutations: tuple[tuple[str,str],...]
    generation: int
    termination: str
    transfer_complete: bool = True
    consumed_steps: int = 0
    consumed_cases: int = 0
