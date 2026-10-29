from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class VersionedCell:
    key: str
    type_tag: str
    version: int
    payload_json: str
    def __post_init__(self):
        from latent_comm.packets.schema import load_json
        if not self.key.startswith(('state:','ontology:','isa:','frame:','world:','evidence:')) or not self.type_tag or type(self.version) is not int or self.version<0:raise ContractError('NonReversibleEffect','only versioned local research-state keys are writable')
        load_json(self.payload_json)
@dataclass(frozen=True)
class CognitiveTransaction:
    transaction_id: str
    read_versions: tuple[tuple[str,int],...]
    writes: tuple[VersionedCell,...]
    migration_dependencies: tuple[tuple[str,str],...] = ()
    external_effects: bool = False
    def __post_init__(self):
        if self.external_effects:raise ContractError('NonReversibleEffect','external communications, payments and publication cannot be rolled back')
        if not self.transaction_id or len(dict(self.read_versions))!=len(self.read_versions) or len({w.key for w in self.writes})!=len(self.writes):raise ContractError('PartialCommit','transaction and read/write identities must be unique')
        if not set(w.key for w in self.writes)<=dict(self.read_versions).keys():raise ContractError('VersionConflict','all write targets require snapshot version checks, including absent=-1')
@dataclass(frozen=True)
class CommitRecord:
    transaction_id: str
    before_digest: str
    after_digest: str
    written_keys: tuple[str,...]
    status: str
