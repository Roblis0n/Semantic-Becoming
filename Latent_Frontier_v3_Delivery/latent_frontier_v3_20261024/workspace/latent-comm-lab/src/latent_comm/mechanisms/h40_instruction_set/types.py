from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

BASE_ISA=('const','var','add','multiply','let')
BASE_ISA_VERSION='base:1'
@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple['Expr',...] = ()
    name: str = ''
    value: float = 0.
    def __post_init__(self):
        if self.op not in BASE_ISA+('call',):raise ContractError('LoweringFailure','only immutable base ISA and macro calls are supported')
        arity={'const':0,'var':0,'add':2,'multiply':2,'let':2}
        if self.op in arity and len(self.args)!=arity[self.op]:raise ContractError('LoweringFailure','base instruction arity mismatch')
        if self.op in ('var','let','call') and not self.name:raise ContractError('LoweringFailure','named binding or macro required')
        if self.op=='const':finite_scalar(self.value)
@dataclass(frozen=True)
class MacroDefinition:
    name: str
    parameters: tuple[str,...]
    body: Expr
    input_types: tuple[str,...]
    output_type: str = 'scalar'
    def __post_init__(self):
        if self.name in BASE_ISA or len(set(self.parameters))!=len(self.parameters) or len(self.parameters)!=len(self.input_types) or any(t!='scalar' for t in self.input_types) or self.output_type!='scalar':raise ContractError('LoweringFailure','macro cannot redefine base ISA; typed scalar parameters required')
@dataclass(frozen=True)
class ISARevision:
    version: str
    macros: tuple[MacroDefinition,...]
    base_version: str = BASE_ISA_VERSION
    future_expansion_budget: int = 256
    def __post_init__(self):
        if self.base_version!=BASE_ISA_VERSION or not self.version or len({m.name for m in self.macros})!=len(self.macros):raise ContractError('VersionUnsupported','immutable base ISA and unique versioned macros required')
@dataclass(frozen=True)
class MacroProposal:
    definition: MacroDefinition
    occurrences: int
    original_bytes: int
    replacement_bytes: int
    saved_bytes: int
