from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def assemble(packet):
    if not packet.version or not packet.cover:raise ContractError('UnboundRestriction','cover and version required')
    offsets={};n=0
    for d in packet.cover:
        if d.name in offsets:raise ContractError('Conflict','duplicate cover domain')
        offsets[d.name]=(n,d.dimension);n+=d.dimension
    StepBudget().meter().dimension(n)
    rows=[];rhs=[];labels=[]
    for e in packet.restrictions:
        if e.left not in offsets or e.right not in offsets:raise ContractError('UnboundRestriction','overlap endpoint absent')
        i,di=offsets[e.left];j,dj=offsets[e.right]
        if len(e.left_map[0])!=di or len(e.right_map[0])!=dj:raise ContractError('InvalidShape','restriction input dimensions differ')
        for l,r,b in zip(e.left_map,e.right_map,e.bias,strict=True):
            row=[0.0]*n
            for k,x in enumerate(l):row[i+k]+=x
            for k,x in enumerate(r):row[j+k]-=x
            rows.append(tuple(row));rhs.append(b);labels.append(e.edge_id)
    fixed={}
    for a in packet.anchors:
        if a.domain not in offsets or not 0<=a.coordinate<offsets[a.domain][1]:raise ContractError('InvalidAnchor','hard anchor coordinate absent')
        k=offsets[a.domain][0]+a.coordinate;v=finite_scalar(a.value)
        if k in fixed and fixed[k]!=v:raise ContractError('ConflictingAnchors','hard anchor values disagree')
        fixed[k]=v
    return offsets,n,rows,rhs,labels,fixed

def _solve(n,rows,rhs,fixed):
    free=[k for k in range(n) if k not in fixed];z=[fixed.get(k,0.0) for k in range(n)];rank=0
    reduced=[tuple(row[k] for k in free) for row in rows];b=tuple(y-sum(row[k]*v for k,v in fixed.items()) for row,y in zip(rows,rhs))
    if free and rows:
        result=least_squares(tuple(reduced),b)
        if not result.converged:raise ContractError('SolverUnconverged','bounded least-squares solver did not converge')
        rank=result.rank
        for k,v in zip(free,result.solution):z[k]=v
    residual=tuple(dot(row,tuple(z))-y for row,y in zip(rows,rhs))
    return tuple(z),residual,rank

def glue(packet,budget=StepBudget(),tolerance=1e-8,find_conflict=True):
    meter=budget.meter();offsets,n,rows,rhs,labels,fixed=assemble(packet);meter.dimension(n);meter.consume(steps=1,cases=1)
    if not packet.anchors and not any(rhs):raise ContractError('MissingAnchor','unanchored homogeneous system has degenerate zero consensus')
    z,residual,rank=_solve(n,rows,rhs,fixed)
    status='NoGlobalSection' if any(abs(x)>tolerance for x in residual) else 'CompatibleOnDeclaredOverlaps'
    witness=list(dict.fromkeys(labels)) if status=='NoGlobalSection' else []
    if find_conflict and witness:
        # Deletion filtering proves inclusion-minimality, not globally minimum size.
        for label in tuple(witness):
            meter.consume(steps=1,cases=1)
            selected=[i for i,l in enumerate(labels) if l in witness and l!=label]
            _,r,_=_solve(n,[rows[i] for i in selected],[rhs[i] for i in selected],fixed)
            if any(abs(x)>tolerance for x in r):witness.remove(label)
    overlaps={frozenset((e.left,e.right)) for e in packet.restrictions}
    names=[d.name for d in packet.cover]
    missing=tuple((a,b) for i,a in enumerate(names) for b in names[i+1:] if frozenset((a,b)) not in overlaps)
    grouped=tuple((e.edge_id,tuple(r for r,l in zip(residual,labels) if l==e.edge_id)) for e in packet.restrictions)
    return GluingCandidate(tuple((d.name,z[offsets[d.name][0]:offsets[d.name][0]+d.dimension]) for d in packet.cover),grouped,tuple(witness),status,missing,rank,meter.steps)

def migrate_cover(packet,new_version,renames):
    if set(renames)!=set(d.name for d in packet.cover) or len(set(renames.values()))!=len(renames):raise ContractError('AmbiguousMigration','cover rename must be total and one-to-one')
    return SheafPacket(tuple(LocalDomain(renames[d.name],d.dimension) for d in packet.cover),tuple(replace(e,left=renames[e.left],right=renames[e.right]) for e in packet.restrictions),tuple(replace(a,domain=renames[a.domain]) for a in packet.anchors),new_version)
