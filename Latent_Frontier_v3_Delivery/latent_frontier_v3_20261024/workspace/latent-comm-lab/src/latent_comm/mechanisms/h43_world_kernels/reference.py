from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

from itertools import product

def compose_kernels(kernels,noise_joint,*,conditional_independence=False,new_version='composed:1',budget=StepBudget()):
    if not kernels:raise ContractError('WorldCycle','at least one local kernel required')
    if len({k.kernel_id for k in kernels})!=len(kernels):raise ContractError('ActionMismatch','component kernel identities must be unique')
    ports=[k.state_port for k in kernels]
    if len(set(ports))!=len(ports):raise ContractError('ActionMismatch','two modules cannot own the same boundary state port')
    actions=kernels[0].actions
    if not actions or any(k.actions!=actions or k.scope!=kernels[0].scope for k in kernels):raise ContractError('ActionMismatch','common action IDs, semantics, order and scope must match')
    if any(not set(k.noise_ids)<=set(noise_joint.identities) for k in kernels):raise ContractError('NoiseAliasConflict','shared exogenous identity is unbound')
    stochastic=any(any(sum(p>0 for p in row.probabilities)>1 for row in k.transition_rows) or any(sum(p>0 for p in row)>1 for row in k.observation_rows) for k in kernels)
    if stochastic and len(kernels)>1 and not conditional_independence:raise ContractError('NoiseAliasConflict','residual stochastic kernels need explicit conditional independence or a joint kernel')
    states=tuple(product(*(k.states for k in kernels)));observations=tuple(product(*(k.observations for k in kernels)));meter=budget.meter();meter.dimension(len(states));meter.dimension(len(observations))
    tables=[{(r.state,r.action,r.noise_values):r.probabilities for r in k.transition_rows} for k in kernels];state_index=[{s:i for i,s in enumerate(k.states)} for k in kernels]
    transitions=[]
    for action,_ in actions:
        rows=[]
        for state in states:
            row=[0.]*len(states)
            for assignment,probability in noise_joint.assignments:
                meter.consume(steps=1)
                noise=dict(zip(noise_joint.identities,assignment));conditionals=[]
                for i,k in enumerate(kernels):
                    key=(state[i],action,tuple(noise[n] for n in k.noise_ids))
                    if key not in tables[i]:raise ContractError('NoiseAliasConflict','kernel missing a declared shared-noise conditional row')
                    conditionals.append(tables[i][key])
                for j,next_state in enumerate(states):row[j]+=probability*math.prod(conditionals[i][state_index[i][s]] for i,s in enumerate(next_state))
            if abs(sum(row)-1)>1e-9:raise ContractError('KernelNotNormalized','composed transition lost mass')
            rows.append(tuple(row))
        transitions.append((action,tuple(rows)))
    observation_matrix=tuple(tuple(math.prod(k.observation_rows[state_index[i][state[i]]][k.observations.index(observation[i])] for i,k in enumerate(kernels)) for observation in observations) for state in states)
    if any(abs(sum(row)-1)>1e-9 for row in observation_matrix):raise ContractError('KernelNotNormalized','composed observation lost mass')
    return ComposedWorldKernel(tuple(k.kernel_id for k in kernels),states,actions,tuple(transitions),observations,observation_matrix,noise_joint,tuple((k.state_port,k.noise_ids) for k in kernels),new_version)

def rollout(kernel,initial_distribution,actions,budget=StepBudget()):
    distribution=vector(initial_distribution)
    if len(distribution)!=len(kernel.states) or any(p<0 for p in distribution) or abs(sum(distribution)-1)>1e-9:raise ContractError('KernelNotNormalized','initial distribution must be normalized over joint states')
    tables=dict(kernel.transitions);meter=budget.meter();trajectory=[distribution];observed=[]
    for action in actions:
        meter.consume(steps=1)
        if action not in tables:raise ContractError('ActionMismatch','rollout action absent')
        distribution=matvec(transpose(tables[action]),distribution);trajectory.append(distribution)
        observed.append(matvec(transpose(kernel.observation_matrix),distribution))
    return {'states':tuple(trajectory),'observations':tuple(observed),'evidence_kind':kernel.evidence_kind,'parents':kernel.component_ids,'world_version':kernel.version}

def migrate_kernel(kernel,new_version,state_names):
    if set(state_names)!=set(kernel.states) or len(set(state_names.values()))!=len(state_names):raise ContractError('ActionMismatch','state migration must preserve complete transition domain')
    return replace(kernel,states=tuple(state_names[s] for s in kernel.states),transition_rows=tuple(replace(r,state=state_names[r.state]) for r in kernel.transition_rows),version=new_version)
