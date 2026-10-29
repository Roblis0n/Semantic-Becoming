from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.mechanisms.h07_legacy.types import ValueType
@dataclass(frozen=True)
class SkillStep:
    local_name: str
    operation: str
    arguments: tuple[str,...]
    output_type: ValueType
    bound: int=1
@dataclass(frozen=True)
class Production:
    name: str
    parameters: tuple[tuple[str,ValueType],...]
    body: tuple[SkillStep,...]
    result_name: str
    output_type: ValueType
    def __post_init__(self):
        if not self.name or len(dict(self.parameters))!=len(self.parameters) or len({s.local_name for s in self.body})!=len(self.body) or set(dict(self.parameters))&{s.local_name for s in self.body}:raise ContractError('CaptureRisk','unique lexical parameters and local SSA names')
@dataclass(frozen=True)
class SkillGrammar:
    productions: tuple[Production,...]
    grammar_version: str
    base_isa: str
    task_family: frozenset[str]
    versions: VersionSet
    def __post_init__(self):
        if len({p.name for p in self.productions})!=len(self.productions) or not self.grammar_version or not self.base_isa or not self.task_family:raise ContractError('InvalidGrammar','versioned typed production namespace required')
        self.versions.require('ontology','isa','frame')
