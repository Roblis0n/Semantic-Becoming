from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.core.finite import Matrix, Vector, matrix, vector, finite_scalar

@dataclass(frozen=True)
class DynamicsPacket:
    dissipation: Matrix
    skew_coupling: Matrix
    state: Vector
    version: str
    step_size: float
    steps: int
    readout_window: tuple[int,int]
    integrator: str = 'implicit_midpoint_linear'
    def __post_init__(self):
        q=matrix(self.dissipation);k=matrix(self.skew_coupling);z=vector(self.state);n=len(z)
        if len(q)!=n or len(q[0])!=n or len(k)!=n or len(k[0])!=n:raise ContractError('InvalidSkewPart','dynamics coordinate axes differ')
        if any(abs(k[i][j]+k[j][i])>1e-10 for i in range(n) for j in range(n)):raise ContractError('InvalidSkewPart','coupling must be antisymmetric')
        if any(abs(q[i][j]-q[j][i])>1e-10 for i in range(n) for j in range(n)):raise ContractError('InvalidDissipation','quadratic gradient matrix must be symmetric')
        if self.integrator!='implicit_midpoint_linear' or self.step_size<=0 or not 1<=self.steps<=128:raise ContractError('IntegratorUnsupported','finite positive implicit midpoint schedule required')
        if not 0<=self.readout_window[0]<self.readout_window[1]<=self.steps+1 or not self.version:raise ContractError('IntegratorUnsupported','invalid trajectory readout window or version')
@dataclass(frozen=True)
class TrajectoryObject:
    states: tuple[Vector,...]
    logical_steps: tuple[int,...]
    dynamics_times: Vector
    quadratic_energy: Vector
    squared_norms: Vector
    readout: Vector
    descriptor: str
    termination: str
    versions: tuple[str,...]
