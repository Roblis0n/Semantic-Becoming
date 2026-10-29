from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def right_solve(a, g):
    """Compute a G^-1 through row-wise transposed solves, never explicit inverse."""
    return tuple(solve(transpose(g),row) for row in matrix(a))

def condition_check(g, frame, condition_limit=10000.0):
    g=matrix(g);d=frame.dimension
    if len(g)!=d or len(g[0])!=d: raise ContractError('DimensionMismatch','gauge inverse requires square same-dimensional frame')
    try:
        inv_rows=right_solve(eye(d),g)
    except ContractError as error:
        raise ContractError('SingularFrame','gauge matrix cannot be inverted') from error
    condition=max(sum(abs(x) for x in row) for row in g)*max(sum(abs(x) for x in row) for row in inv_rows)
    if finite_scalar(condition_limit)<1 or condition>condition_limit: raise ContractError('ConditionExceeded','gauge map exceeds condition bound')
    if frame.group=='orthogonal':
        gram=matmul(transpose(g),g)
        if any(abs(gram[i][j]-(i==j))>1e-9 for i in range(d) for j in range(d)): raise ContractError('GroupMismatch','matrix is not orthogonal')
    return condition

def transport(packet, g, target, budget=StepBudget(), condition_limit=10000.0):
    meter=budget.meter();meter.dimension(packet.frame.dimension);meter.consume(steps=1,cases=1)
    if target.dimension!=packet.frame.dimension or target.domain!=packet.frame.domain: raise ContractError('DimensionMismatch','gauge transport cannot compress or change domain')
    condition=condition_check(g,packet.frame,condition_limit)
    condition_check(g,target,condition_limit)
    shifted=GaugePacket(target,matvec(g,packet.state),right_solve(matmul(g,packet.operator),g),right_solve(packet.readout,g))
    before=matvec(packet.readout,matvec(packet.operator,packet.state));after=matvec(shifted.readout,matvec(shifted.operator,shifted.state))
    return CovarianceReport(shifted,condition,before,after,sub(after,before),(packet.frame.frame_id,target.frame_id),meter.steps)

def transport_cross_map(p, gi, gj, source, target, condition_limit=10000.0):
    condition_check(gi,source,condition_limit);condition_check(gj,target,condition_limit)
    p=matrix(p)
    if len(p)!=target.dimension or len(p[0])!=source.dimension: raise ContractError('DimensionMismatch','cross map axes [target,source]')
    return right_solve(matmul(gj,p),gi)

def compose_path(packet, transforms, budget=StepBudget()):
    if not transforms: raise ContractError('UnknownFrame','path requires at least one declared transition')
    meter=budget.meter();path=[packet.frame.frame_id];current=packet;condition=1.0
    for g,target in transforms:
        meter.consume(steps=1,cases=1); report=transport(current,g,target,budget)
        condition*=report.condition;current=report.transported;path.append(target.frame_id)
    before=matvec(packet.readout,matvec(packet.operator,packet.state));after=matvec(current.readout,matvec(current.operator,current.state))
    return CovarianceReport(current,condition,before,after,sub(after,before),tuple(path),meter.steps)

def migrate_frame(packet,g,target,budget=StepBudget()):
    if target.frame_id==packet.frame.frame_id and target.version==packet.frame.version: raise ContractError('VersionMismatch','migration must name a new frame version or identity')
    return transport(packet,g,target,budget).transported
