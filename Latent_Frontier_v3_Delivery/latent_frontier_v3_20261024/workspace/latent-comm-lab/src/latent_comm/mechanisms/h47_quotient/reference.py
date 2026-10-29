from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def query_response(query,value):
    if query.opcode=='parity':return value%2
    if query.opcode=='greater_than':return int(value>query.argument)
    return value+query.argument

def validate_queries(queries):
    if len(queries)>8 or len({q.query_id for q in queries})!=len(queries):raise ContractError('QueryFamilyUndefined','at most8 uniquely named finite queries')

def form_quotient(domain,queries,version,*,retain_source=True,budget=StepBudget()):
    import hashlib,json
    validate_queries(queries);meter=budget.meter();meter.dimension(len(domain.state_ids));groups={}
    for state,value in zip(domain.state_ids,domain.values,strict=True):
        meter.consume(cases=1);signature=[]
        for query in queries:meter.consume(steps=1);signature.append(query_response(query,value))
        groups.setdefault(tuple(signature),[]).append(state)
    classes=[]
    for signature,members in sorted(groups.items()):
        identity=json.dumps([domain.version,[(q.query_id,q.version) for q in queries],signature],separators=(',',':'))
        key='class:'+hashlib.sha256(identity.encode()).hexdigest()[:20]
        classes.append(IndistinguishabilityClass(key,tuple(members),members[0],signature))
    return TaskRelativeQuotient(tuple(queries),tuple(classes),domain if retain_source else None,domain.version,version)

def refine_quotient(old,additional_queries,new_version,*,source_domain=None,budget=StepBudget()):
    source=source_domain or old.source_domain
    if source is None:raise ContractError('RefinementConflict','original distinctions were dropped; request original state information from source',recoverable=True,obligations=('provide source domain retaining all old class members',))
    old_members={m for c in old.classes for m in c.members}
    if source.version!=old.domain_version or set(source.state_ids)!=old_members:raise ContractError('RefinementConflict','source must have exact old domain/version, not fabricated representatives')
    values=dict(zip(source.state_ids,source.values,strict=True));old_queries={q.query_id:q for q in old.queries};new=[]
    for q in additional_queries:
        if q.query_id in old_queries:
            if q!=old_queries[q.query_id]:raise ContractError('RefinementConflict','existing query semantics cannot change silently')
        else:new.append(q)
    for c in old.classes:
        for member in c.members:
            if tuple(query_response(q,values[member]) for q in old.queries)!=c.signature:raise ContractError('RefinementConflict','supplied source contradicts previous behavioral signature')
    refined=form_quotient(source,old.queries+tuple(new),new_version,budget=budget);old_owner={m:c.class_id for c in old.classes for m in c.members};mapping={c.class_id:[] for c in old.classes};witnesses=[]
    for c in refined.classes:
        parents={old_owner[m] for m in c.members}
        if len(parents)!=1:raise ContractError('RefinementConflict','new query set merged old distinct classes')
        mapping[next(iter(parents))].append(c.class_id)
    new_by_member={m:c for c in refined.classes for m in c.members}
    for c in old.classes:
        anchor=c.members[0]
        for member in c.members[1:]:
            if new_by_member[anchor].class_id!=new_by_member[member].class_id:
                q=next(q for q in new if query_response(q,values[anchor])!=query_response(q,values[member]))
                witnesses.append(DistinguishingWitness(c.class_id,anchor,member,q.query_id,query_response(q,values[anchor]),query_response(q,values[member])))
    return RefinementMap(old.version,new_version,tuple((k,tuple(v)) for k,v in mapping.items()),tuple(witnesses),refined)

def migrate_class_reference(class_id,refinement,source_version):
    if source_version!=refinement.old_version or class_id not in dict(refinement.old_to_new):raise ContractError('RefinementConflict','stale or unknown class reference')
    return dict(refinement.old_to_new)[class_id]

def approximate_clusters(signatures,epsilon,*,method='complete_linkage',budget=StepBudget()):
    values=matrix(signatures);epsilon=finite_scalar(epsilon)
    if epsilon<0 or method not in ('complete_linkage','connected_components'):raise ContractError('ApproxNotEquivalence','explicit nonnegative tolerance and clustering method required')
    meter=budget.meter();meter.dimension(max(len(values),len(values[0])));distance=lambda i,j:max(abs(a-b) for a,b in zip(values[i],values[j],strict=True));n=len(values);witness=None
    for i in range(n):
        for j in range(n):
            for k in range(n):
                meter.consume(steps=1,cases=1)
                if distance(i,j)<=epsilon and distance(j,k)<=epsilon and distance(i,k)>epsilon:witness=(i,j,k);break
            if witness:break
        if witness:break
    groups=[]
    for i in range(n):
        if method=='complete_linkage':
            target=next((g for g in groups if all(distance(i,j)<=epsilon for j in g)),None)
            if target is None:groups.append([i])
            else:target.append(i)
        else:
            adjacent=[g for g in groups if any(distance(i,j)<=epsilon for j in g)]
            merged=[i]+[j for g in adjacent for j in g];groups=[g for g in groups if g not in adjacent]+[merged]
    return ApproximateClusters(tuple(tuple(sorted(g)) for g in groups),method,epsilon,witness is None,witness)
