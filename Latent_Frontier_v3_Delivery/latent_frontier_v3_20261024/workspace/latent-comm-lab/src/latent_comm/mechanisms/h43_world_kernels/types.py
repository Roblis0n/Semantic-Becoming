from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class SharedNoiseJoint:
    identities: tuple[str,...]
    assignments: tuple[tuple[tuple[str,...],float],...]
    def __post_init__(self):
        if len(set(self.identities))!=len(self.identities) or not self.assignments or len(self.assignments)>64:raise ContractError('NoiseAliasConflict','unique finite shared noise identities and joint support required')
        keys=[]
        for assignment,p in self.assignments:
            if len(assignment)!=len(self.identities) or finite_scalar(p)<0:raise ContractError('NoiseAliasConflict','joint assignment arity or probability invalid')
            keys.append(assignment)
        if len(set(keys))!=len(keys) or abs(sum(p for _,p in self.assignments)-1)>1e-9:raise ContractError('KernelNotNormalized','joint noise support must have unique normalized rows')
@dataclass(frozen=True)
class ConditionalRow:
    state: str
    action: str
    noise_values: tuple[str,...]
    probabilities: Vector
@dataclass(frozen=True)
class WorldKernel:
    kernel_id: str
    state_port: str
    states: tuple[str,...]
    actions: tuple[tuple[str,str],...]
    noise_ids: tuple[str,...]
    transition_rows: tuple[ConditionalRow,...]
    observations: tuple[str,...]
    observation_rows: Matrix
    version: str
    scope: str
    def __post_init__(self):
        if not self.kernel_id or not self.state_port or not self.version or not self.scope or not self.states or len(set(self.states))!=len(self.states) or len(self.states)>64:raise ContractError('KernelNotNormalized','finite typed state port and version required')
        if len(dict(self.actions))!=len(self.actions) or len(set(self.noise_ids))!=len(self.noise_ids):raise ContractError('ActionMismatch','duplicate action or noise identity')
        if not self.observations or any(not isinstance(o,str) or not o for o in self.observations) or len(set(self.observations))!=len(self.observations):raise ContractError('KernelNotNormalized','nonempty unique observation identities required')
        obs=matrix(self.observation_rows)
        if len(obs)!=len(self.states) or len(obs[0])!=len(self.observations):raise ContractError('KernelNotNormalized','observation axes differ')
        for row in obs:
            if any(p<0 for p in row) or abs(sum(row)-1)>1e-9:raise ContractError('KernelNotNormalized','observation row is not normalized')
        keys=[]
        for row in self.transition_rows:
            if row.state not in self.states or row.action not in dict(self.actions) or len(row.noise_values)!=len(self.noise_ids) or len(row.probabilities)!=len(self.states):raise ContractError('ActionMismatch','conditional transition axes differ')
            p=vector(row.probabilities)
            if any(x<0 for x in p) or abs(sum(p)-1)>1e-9:raise ContractError('KernelNotNormalized','conditional transition row not normalized')
            keys.append((row.state,row.action,row.noise_values))
        if len(set(keys))!=len(keys):raise ContractError('KernelNotNormalized','duplicate conditional transition row')
@dataclass(frozen=True)
class ComposedWorldKernel:
    component_ids: tuple[str,...]
    states: tuple[tuple[str,...],...]
    actions: tuple[tuple[str,str],...]
    transitions: tuple[tuple[str,Matrix],...]
    observations: tuple[tuple[str,...],...]
    observation_matrix: Matrix
    noise_joint: SharedNoiseJoint
    dependency_map: tuple[tuple[str,tuple[str,...]],...]
    version: str
    evidence_kind: str = 'model_prediction_not_real_observation'
