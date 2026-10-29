from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class TypedObject:
    object_id: str
    type_id: str
@dataclass(frozen=True)
class FiniteOperation:
    name: str
    input_type: str
    output_type: str
    table: tuple[tuple[str,str],...]
@dataclass(frozen=True)
class TypedOperationGraph:
    objects: tuple[TypedObject,...]
    operations: tuple[FiniteOperation,...]
    version: str
    def __post_init__(self):
        ids={o.object_id:o.type_id for o in self.objects}
        if len(ids)!=len(self.objects) or len(ids)>64 or not self.version:raise ContractError('TypeViolation','unique finite typed objects required')
        if len({op.name for op in self.operations})!=len(self.operations):raise ContractError('TypeViolation','duplicate operation')
        for op in self.operations:
            if len(dict(op.table))!=len(op.table):raise ContractError('TypeViolation','operation must be a function on its declared subdomain')
            for x,y in op.table:
                if ids.get(x)!=op.input_type or ids.get(y)!=op.output_type:raise ContractError('TypeViolation','operation edge violates endpoint types')
@dataclass(frozen=True)
class AnalogyMorphism:
    object_map: tuple[tuple[str,str],...]
    operation_map: tuple[tuple[str,str],...]
    type_map: tuple[tuple[str,str],...]
    valid_domain: tuple[str,...]
@dataclass(frozen=True)
class CompiledAnalogy:
    morphism: AnalogyMorphism
    broken_squares: tuple[tuple[str,str,str,str],...]
    uncovered_edges: tuple[tuple[str,str],...]
    unmapped_objects: tuple[str,...]
    source_version: str
    target_version: str
