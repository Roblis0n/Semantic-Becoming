from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def check_morphism(source,target,morphism,budget=StepBudget()):
    meter=budget.meter();f=dict(morphism.object_map);g=dict(morphism.operation_map);types=dict(morphism.type_map)
    a={o.object_id:o.type_id for o in source.objects};b={o.object_id:o.type_id for o in target.objects}
    if len(f)!=len(morphism.object_map) or len(g)!=len(morphism.operation_map):raise ContractError('AmbiguousMatch','mapping must be single-valued, alternatives remain separate morphisms')
    if not set(morphism.valid_domain)<=f.keys():raise ContractError('TypeViolation','declared valid domain contains unmapped objects')
    for x,y in f.items():
        if x not in a or y not in b or types.get(a[x])!=b[y]:raise ContractError('TypeViolation','object correspondence violates explicit type map')
    ta={op.name:op for op in target.operations};broken=[];uncovered=[]
    for op in source.operations:
        if op.name not in g:
            uncovered.extend((op.name,x) for x,_ in op.table);continue
        if g[op.name] not in ta:raise ContractError('UnmappedOperation','target operation absent')
        top=ta[g[op.name]];table=dict(top.table)
        if types.get(op.input_type)!=top.input_type or types.get(op.output_type)!=top.output_type:raise ContractError('TypeViolation','operation type map differs')
        for x,y in op.table:
            meter.consume(steps=1)
            if x not in morphism.valid_domain or x not in f or y not in f or f[x] not in table:uncovered.append((op.name,x));continue
            if f[y]!=table[f[x]]:broken.append((op.name,x,f[y],table[f[x]]))
    return CompiledAnalogy(morphism,tuple(broken),tuple(uncovered),tuple(x for x in a if x not in f),source.version,target.version)

def candidate_matches(source,target,type_map,operation_map,*,limit=16,budget=StepBudget()):
    meter=budget.meter();types=dict(type_map);out=[]
    def visit(i,pairs,used):
        if len(out)>=limit:return
        if i==len(source.objects):
            meter.consume(cases=1,branches=1);m=AnalogyMorphism(tuple(pairs),tuple(operation_map),tuple(type_map),tuple(x for x,_ in pairs));out.append(check_morphism(source,target,m,budget));return
        obj=source.objects[i]
        for candidate in target.objects:
            if candidate.object_id not in used and candidate.type_id==types.get(obj.type_id):
                meter.consume(steps=1);visit(i+1,pairs+[(obj.object_id,candidate.object_id)],used|{candidate.object_id})
    if not 1<=limit<=64:raise ContractError('AmbiguousMatch','candidate bound outside finite scope')
    visit(0,[],set());return tuple(out)

def compile_program(source,target,compiled,program,initial,budget=StepBudget()):
    verified=check_morphism(source,target,compiled.morphism,budget)
    if compiled.source_version!=source.version or compiled.target_version!=target.version:raise ContractError('VersionMismatch','recheck required after graph change')
    if verified.broken_squares:raise ContractError('CompositionMismatch','hard correspondence fails commuting square')
    f=dict(compiled.morphism.object_map);g=dict(compiled.morphism.operation_map);a={op.name:dict(op.table) for op in source.operations};b={op.name:dict(op.table) for op in target.operations}
    if initial not in f:raise ContractError('UnmappedOperation','initial object unmapped')
    x=initial;y=f[x];trace=[y];translated=[];meter=budget.meter()
    for name in program:
        meter.consume(steps=1)
        if name not in g or name not in a or x not in a[name] or y not in b[g[name]]:raise ContractError('UnmappedOperation','unmapped or out-of-domain program step')
        nx=a[name][x];ny=b[g[name]][y]
        if nx not in f or f[nx]!=ny:raise ContractError('CompositionMismatch','composition leaves the validated domain')
        x,y=nx,ny;trace.append(y);translated.append(g[name])
    return tuple(translated),tuple(trace)

def migrate_graph(graph,new_version,object_renames):
    if set(object_renames)!=set(o.object_id for o in graph.objects) or len(set(object_renames.values()))!=len(object_renames):raise ContractError('AmbiguousMatch','graph migration must preserve object identity bijectively')
    return TypedOperationGraph(tuple(TypedObject(object_renames[o.object_id],o.type_id) for o in graph.objects),tuple(replace(op,table=tuple((object_renames[x],object_renames[y]) for x,y in op.table)) for op in graph.operations),new_version)
