from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def closure_report(packet,tolerance=1e-9):
    linear=matrix_add(matmul(packet.coarse_map,packet.micro_dynamics),matrix_scale(matmul(packet.macro_dynamics,packet.coarse_map),-1))
    bias=sub(matvec(packet.coarse_map,packet.micro_bias),packet.macro_bias)
    error=math.sqrt(sum(x*x for row in linear for x in row)+dot(bias,bias))
    return ClosureResidual(linear,bias,error,error<=tolerance,'none' if error<=tolerance else 'retain detail memory or extend macro variables')

def coarsen(packet,state,retain_detail=True):
    state=vector(state);coarse=matvec(packet.coarse_map,state)
    detail=sub(state,matvec(packet.lift,coarse)) if retain_detail else None
    return MultiScaleState(coarse,detail,packet.target_version)

def refine(packet,state):
    if state.scale_version!=packet.target_version:raise ContractError('ScaleMismatch','coarse state version differs')
    if state.detail_residual is None:raise ContractError('IrrecoverableDetail','a lift is a representative, not an inverse; request missing source detail')
    return add(matvec(packet.lift,state.coarse),state.detail_residual)

def step_scale(packet,state,*,closure_tolerance=1e-9):
    if state.scale_version!=packet.target_version:raise ContractError('ScaleMismatch','version mismatch')
    report=closure_report(packet,closure_tolerance)
    if state.detail_residual is None:
        if not report.closed:raise ContractError('ClosureFailure','nonclosed macro dynamics require remembered detail or new statistics')
        return MultiScaleState(add(matvec(packet.macro_dynamics,state.coarse),packet.macro_bias),None,state.scale_version)
    micro=refine(packet,state);next_micro=add(matvec(packet.micro_dynamics,micro),packet.micro_bias)
    return coarsen(packet,next_micro,True)

def fit_linear_closure(coarse_map,micro_dynamics,micro_bias,budget=StepBudget()):
    c=matrix(coarse_map);f=matrix(micro_dynamics);cf=matmul(c,f);meter=budget.meter();rows=[]
    for row in cf:
        meter.consume(steps=1);fit=least_squares(transpose(c),row)
        if not fit.converged:raise ContractError('ClosureFailure','bounded closure solve unconverged')
        rows.append(fit.solution)
    return tuple(rows),matvec(c,micro_bias)

def closure_counterexamples(packet,states,budget=StepBudget()):
    meter=budget.meter();out=[]
    for i,a in enumerate(states):
        for b in states[i+1:]:
            meter.consume(steps=1,cases=1)
            ca=matvec(packet.coarse_map,a);cb=matvec(packet.coarse_map,b)
            na=matvec(packet.coarse_map,add(matvec(packet.micro_dynamics,a),packet.micro_bias));nb=matvec(packet.coarse_map,add(matvec(packet.micro_dynamics,b),packet.micro_bias))
            if norm(sub(ca,cb))<1e-9 and norm(sub(na,nb))>1e-9:out.append((tuple(a),tuple(b),na,nb))
    return tuple(out)

def migrate_scale(old_packet,new_packet,state):
    return coarsen(new_packet,refine(old_packet,state),True)
