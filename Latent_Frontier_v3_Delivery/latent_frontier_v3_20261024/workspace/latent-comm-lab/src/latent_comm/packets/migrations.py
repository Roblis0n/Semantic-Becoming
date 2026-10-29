"""Explicit ordered schema transitions; no implicit reinterpretation."""
from dataclasses import dataclass
from copy import deepcopy
from collections.abc import Callable
from latent_comm.core import VersionSet, ContractError, ErrorCode
from latent_comm.core.finite import topological_order

@dataclass(frozen=True)
class MigrationStep:
    migration_id: str
    axis: str
    source_version: str
    target_version: str
    dependencies: tuple[str,...]
    transform: Callable[[object],object]
    validate: Callable[[object],bool]
    information_loss: tuple[str,...] = ()

@dataclass(frozen=True)
class MigratedRecord:
    value: object
    versions: VersionSet
    applied: tuple[str,...]
    information_loss: tuple[str,...]
    replay_requires_recompute: bool = True

class MigrationRegistry:
    def __init__(self) -> None:
        self._steps: dict[str,MigrationStep]={}
    def register(self,step: MigrationStep) -> None:
        if step.migration_id in self._steps:raise ContractError(ErrorCode.CONFLICT,'migration already registered')
        if step.axis not in VersionSet.__dataclass_fields__ or step.source_version==step.target_version:
            raise ContractError(ErrorCode.MIGRATION_CONFLICT,'invalid migration axis or identity')
        self._steps[step.migration_id]=step
    def apply(self,value: object,versions: VersionSet,step_ids: tuple[str,...],target: VersionSet) -> MigratedRecord:
        if any(x not in self._steps for x in step_ids):raise ContractError(ErrorCode.UNBOUND_REFERENCE,'migration not registered')
        edges=tuple((dep,k) for k in step_ids for dep in self._steps[k].dependencies)
        order=topological_order(step_ids,edges)
        current=versions.as_dict();candidate=deepcopy(value);loss=[]
        for key in order:
            step=self._steps[key]
            if current[step.axis]!=step.source_version:raise ContractError(ErrorCode.VERSION_MISMATCH,'migration source version mismatch',key)
            candidate=step.transform(candidate)
            if not step.validate(candidate):raise ContractError(ErrorCode.MIGRATION_CONFLICT,'post-migration validator rejected candidate',key)
            current[step.axis]=step.target_version;loss.extend(step.information_loss)
        result=VersionSet(**current)
        if result!=target:raise ContractError(ErrorCode.VERSION_MISMATCH,'migration did not reach requested target')
        return MigratedRecord(candidate,result,order,tuple(loss))
