from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def cgls(jvp,vjp,target,parameter_dimension,*,ridge=0.,tolerance=1e-10,max_steps=32,budget=StepBudget()):
    ridge=finite_scalar(ridge)
    if ridge<0 or not 1<=max_steps<=128:raise ContractError('SolverTolerance','nonnegative ridge and bounded iteration count required')
    meter=budget.meter();meter.dimension(parameter_dimension);x=(0.,)*parameter_dimension
    rhs=vector(vjp(target));r=rhs;p=r;rr=dot(r,r);iterations=0
    for i in range(max_steps):
        if math.sqrt(rr)<=tolerance*max(1.,norm(rhs)):break
        meter.consume(steps=1);ap=add(vector(vjp(jvp(p))),scale(p,ridge));den=dot(p,ap)
        if den<=0:raise ContractError('SolverTolerance','normal operator failed positive-semidefinite contract')
        alpha=rr/den;x=add(x,scale(p,alpha));r=sub(r,scale(ap,alpha));new_rr=dot(r,r);iterations=i+1
        if new_rr<=tolerance*tolerance*max(1.,dot(rhs,rhs)):rr=new_rr;break
        p=add(r,scale(p,new_rr/rr));rr=new_rr
    return x,iterations,math.sqrt(rr),math.sqrt(rr)<=tolerance*max(1.,norm(rhs))

def transport_direction(source,target,source_direction,*,ridge=0.,max_steps=32,tolerance=1e-10,current_source_version=None,current_target_version=None,budget=StepBudget()):
    if source.anchors!=target.anchors:raise ContractError('AnchorMismatch','source and target must share public behavior coordinates, not parameter/token axes')
    if current_source_version is not None and source.parameter_version!=current_source_version or current_target_version is not None and target.parameter_version!=current_target_version:raise ContractError('AnchorMismatch','linearization anchor is stale; recompute before proposing an update')
    v=matvec(source.jacobian,source_direction);j=target.jacobian;jt=transpose(j)
    delta,steps,normal,converged=cgls(lambda x:matvec(j,x),lambda y:matvec(jt,y),v,len(j[0]),ridge=ridge,max_steps=max_steps,tolerance=tolerance,budget=budget)
    exact_projection=least_squares(j,v)
    if not exact_projection.converged:raise ContractError('SolverTolerance','finite rank/unreachable-space diagnostic did not converge')
    achieved=matvec(j,delta)
    return TransportedUpdate(delta,v,achieved,sub(achieved,v),exact_projection.residual,exact_projection.rank,exact_projection.rank==len(j[0]) or ridge>0,ridge==0,converged,steps,normal,target.parameter_version,target.parameter_names)

def migrate_anchors(linearization,new_anchors,coordinate_permutation):
    if sorted(coordinate_permutation)!=list(range(len(linearization.anchors.coordinate_ids))):raise ContractError('AnchorMismatch','anchor migration must provide an explicit permutation')
    if tuple(linearization.anchors.coordinate_ids[i] for i in coordinate_permutation)!=new_anchors.coordinate_ids:raise ContractError('AnchorMismatch','permutation does not match named coordinates')
    return replace(linearization,jacobian=tuple(linearization.jacobian[i] for i in coordinate_permutation),anchors=new_anchors)
