from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def integrate(packet,budget=StepBudget(),updates=(),tolerance=1e-8):
    meter=budget.meter();n=len(packet.state);meter.dimension(n)
    eigen,_,_,ok=symmetric_eigh(packet.dissipation)
    if not ok or min(eigen)<-tolerance:raise ContractError('InvalidDissipation','finite reference requires positive semidefinite quadratic dissipation')
    z=packet.state;q=packet.dissipation;k=packet.skew_coupling;version=packet.version;events=dict(updates);states=[z];versions=[version]
    energies=[.5*dot(z,matvec(q,z))];norms=[dot(z,z)]
    for step in range(packet.steps):
        meter.consume(steps=1)
        if step in events:
            expected,new_version,new_k=events[step]
            if expected!=version:raise ContractError('StaleCoupling','asynchronous coupling update uses stale state version')
            candidate=replace(packet,state=z,skew_coupling=new_k,version=new_version);k=candidate.skew_coupling;version=new_version
        a=matrix_add(k,matrix_scale(q,-1));left=matrix_add(eye(n),matrix_scale(a,-packet.step_size/2));right=matrix_add(eye(n),matrix_scale(a,packet.step_size/2))
        try:z=solve(left,matvec(right,z))
        except ContractError as error:raise ContractError('NonFiniteTrajectory','midpoint solve failed; branch stopped') from error
        states.append(z);versions.append(version);energies.append(.5*dot(z,matvec(q,z)));norms.append(dot(z,z))
    start,end=packet.readout_window;window=states[start:end];readout=tuple(sum(s[i] for s in window)/len(window) for i in range(n))
    fixed=all(norm(sub(s,states[0]))<=tolerance for s in states)
    returned=not fixed and any(norm(sub(states[-1],s))<=tolerance for s in states[:-1])
    descriptor='fixed' if fixed else 'finite_return_candidate' if returned else 'transient_or_unresolved_cycle'
    return TrajectoryObject(tuple(states),tuple(range(len(states))),tuple(i*packet.step_size for i in range(len(states))),tuple(energies),tuple(norms),readout,descriptor,'bounded_steps_complete',tuple(versions))

def euler_artifact(skew,state,step_size):
    # Diagnostic finite formula only; production reference uses midpoint.
    next_state=add(state,scale(matvec(skew,state),step_size))
    return dot(next_state,next_state)-dot(state,state)

def migrate_state(packet,mapping,new_version):
    g=matrix(mapping);inv=inverse(g)
    # Orthogonal migrations preserve the quadratic/skew split as defined here.
    if any(abs(x-y)>1e-9 for a,b in zip(matmul(transpose(g),g),eye(len(g))) for x,y in zip(a,b)):raise ContractError('InvalidSkewPart','nonorthogonal migration needs a metric-aware dynamics contract')
    return replace(packet,state=matvec(g,packet.state),dissipation=matmul(matmul(g,packet.dissipation),inv),skew_coupling=matmul(matmul(g,packet.skew_coupling),inv),version=new_version)
