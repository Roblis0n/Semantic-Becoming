from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def potential(z,alpha):return finite_scalar(z)**4/4-finite_scalar(alpha)*z*z/2

def stationary_points(alpha,dt=.1):
    alpha=finite_scalar(alpha);dt=finite_scalar(dt)
    if dt<=0:raise ContractError('UnstableIntegrator','positive explicit step required')
    points=(0.,) if alpha<=0 else (0.,-math.sqrt(alpha),math.sqrt(alpha))
    out=[]
    for z in points:
        j=alpha-3*z*z
        continuous='stable' if j<0 else 'unstable' if j>0 else 'nonhyperbolic_higher_order_attracting'
        multiplier=1+dt*j
        discrete='stable' if abs(multiplier)<1 else 'unstable' if abs(multiplier)>1 else 'nonhyperbolic'
        out.append(StabilityRecord(alpha,z,j,continuous,multiplier,discrete))
    return tuple(out)

def migrate_structure(state,transition):
    if state.version!=transition.source_version or state.structure!=transition.old_structure:raise ContractError('UndefinedTransition','source structure/version does not match')
    if transition.source_version==transition.target_version:raise ContractError('UndefinedTransition','structural transition requires a new version')
    mapped=matvec(transition.mapping,state.z)
    return replace(state,z=mapped,structure=transition.new_structure,version=transition.target_version)

def trace_control(initial,control_path,*,dt=.1,steps_per_control=1,transitions=(),budget=StepBudget()):
    if not initial.version or not initial.branch_id or not control_path or not 1<=steps_per_control<=128:raise ContractError('UnspecifiedDynamics','explicit path, branch, version and finite steps required')
    meter=budget.meter();meter.dimension(len(initial.z));state=initial;states=[state];stabilities=[];events=[]
    event_map=dict(transitions)
    for i,alpha in enumerate(control_path):
        records=stationary_points(alpha,dt);stabilities.append(records)
        for _ in range(steps_per_control):
            meter.consume(steps=1);z=state.z
            local_j=tuple(alpha-3*x*x for x in z)
            if any(j<0 and abs(1+dt*j)>1 for j in local_j):raise ContractError('UnstableIntegrator','Euler instability must not be interpreted as semantic bifurcation')
            state=replace(state,alpha=alpha,z=vector(tuple(x+dt*(alpha*x-x**3) for x in z)))
            states.append(state)
        if i in event_map:
            event=event_map[i];state=migrate_structure(state,event);meter.dimension(len(state.z));events.append(event);states.append(state)
    return BranchTrajectory(tuple(states),tuple(stabilities),tuple(events),'bounded_control_path_complete')

def equilibrium_branches(control_path,budget=StepBudget()):
    meter=budget.meter();out=[]
    for alpha in control_path:
        records=stationary_points(alpha)
        meter.consume(steps=1,branches=len(records));out.append(records)
    return tuple(out)
