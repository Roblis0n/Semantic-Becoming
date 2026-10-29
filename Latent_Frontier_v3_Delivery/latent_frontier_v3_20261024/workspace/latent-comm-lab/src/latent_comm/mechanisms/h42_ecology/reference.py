from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def task_signature(task):return (task.operation,task.offset,task.conditional,task.threshold if task.conditional else None,task.inverse)
def protocol_signature(protocol):return (tuple(sorted(protocol.operators)),tuple(sorted(protocol.concepts)))
def required_operators(task):return ('add',)+(('compare',) if task.conditional else ())+ (('inverse',) if task.inverse else ())
def niche(task):return f'conditional={task.conditional};inverse={task.inverse}'
def mutate_task(task,mutation,new_id):
    changes={'condition':{'conditional':not task.conditional},'inverse':{'inverse':not task.inverse},'shift':{'offset':task.offset+1}}
    if mutation not in changes:raise ContractError('InvalidMutation','task mutation outside grammar')
    return replace(task,task_id=new_id,parent_ids=(task.task_id,),version=task.version+'.1',**changes[mutation])
def mutate_protocol(protocol,mutation,new_id):
    if mutation not in ('add_compare','add_inverse','add_threshold_concept'):raise ContractError('InvalidMutation','protocol mutation outside grammar')
    ops=set(protocol.operators);concepts=set(protocol.concepts)
    if mutation=='add_compare':ops.add('compare')
    elif mutation=='add_inverse':ops.add('inverse')
    else:concepts.add('threshold_predicate')
    return ProtocolGenome(new_id,tuple(sorted(ops)),tuple(sorted(concepts)),(protocol.protocol_id,),protocol.version+'.1')

def execute_program(task,protocol,value):
    if not set(required_operators(task))<=set(protocol.operators):raise ContractError('InvalidMutation','protocol cannot express task operation')
    value=finite_scalar(value)
    active=not task.conditional or value>=task.threshold
    return value+(-task.offset if task.inverse else task.offset) if active else value

def evolve(tasks,protocols,grammar,*,generations=8,world_limit=32,population_limit=16,budget=StepBudget()):
    if not tasks or not protocols or not 1<=generations<=128 or not 1<=world_limit<=64 or not 1<=population_limit<=64:raise ContractError('UnboundedExpansion','finite nonempty task/protocol limits required')
    if len(tasks)>world_limit or len(protocols)>population_limit or len({t.task_id for t in tasks})!=len(tasks) or len({p.protocol_id for p in protocols})!=len(protocols):raise ContractError('UnboundedExpansion','initial population exceeds limits or repeats identity')
    meter=budget.meter();task_list=list(tasks);protocol_list=list(protocols);seen_t={task_signature(t) for t in tasks};seen_p={protocol_signature(p) for p in protocols};rejected=[];termination='generation_bound';completed=0
    used_ids={t.task_id for t in tasks}|{p.protocol_id for p in protocols}
    if len(used_ids)!=len(tasks)+len(protocols):raise ContractError('InvalidMutation','combined lineage identities must be unique')
    def fresh_id(base):
        candidate=base;suffix=0
        while candidate in used_ids:
            meter.consume(steps=1)
            candidate=base+':fresh:'+str(suffix);suffix+=1
        return candidate
    for generation in range(generations):
        proposals=[]
        for task in tuple(task_list):
            for mutation in grammar.task_mutations:proposals.append(('task',task,mutation))
        for protocol in tuple(protocol_list):
            for mutation in grammar.protocol_mutations:proposals.append(('protocol',protocol,mutation))
        changed=False
        for kind,parent,mutation in proposals:
            if meter.steps>=budget.max_steps or meter.cases>=budget.max_cases:termination='ResourceExhausted';break
            meter.consume(steps=1,cases=1)
            try:
                if kind=='task':
                    candidate=mutate_task(parent,mutation,fresh_id('task:'+str(len(task_list))+':'+str(generation)));key=task_signature(candidate)
                    if key in seen_t:rejected.append((mutation,'duplicate_structure'));continue
                    if len(task_list)>=world_limit:rejected.append((mutation,'world_limit'));continue
                    task_list.append(candidate);seen_t.add(key);used_ids.add(candidate.task_id)
                else:
                    candidate=mutate_protocol(parent,mutation,fresh_id('protocol:'+str(len(protocol_list))+':'+str(generation)));key=protocol_signature(candidate)
                    if key in seen_p:rejected.append((mutation,'duplicate_structure'));continue
                    if len(protocol_list)>=population_limit:rejected.append((mutation,'population_limit'));continue
                    protocol_list.append(candidate);seen_p.add(key);used_ids.add(candidate.protocol_id)
                changed=True
            except ContractError as error:rejected.append((mutation,str(error)))
        completed=generation+1
        if termination=='ResourceExhausted':break
        if not changed:termination='no_new_structure_within_grammar';break
    archive={}
    for t in task_list:archive.setdefault(niche(t),[]).append(t.task_id)
    transfers=[];transfer_complete=True
    for p in protocol_list:
        for t in task_list:
            if meter.steps>=budget.max_steps or meter.cases>=budget.max_cases:transfer_complete=False;termination='ResourceExhausted';break
            meter.consume(steps=1,cases=1)
            missing=tuple(o for o in required_operators(t) if o not in p.operators)
            transfers.append(TransferAttempt(p.protocol_id,t.task_id,'expressible_candidate' if not missing else 'missing_operators',missing))
        if not transfer_complete:break
    lineage=tuple((t.task_id,t.parent_ids) for t in task_list)+tuple((p.protocol_id,p.parent_ids) for p in protocol_list)
    return EcologyState(tuple(task_list),tuple(protocol_list),tuple((k,tuple(v)) for k,v in sorted(archive.items())),lineage,tuple(transfers),tuple(rejected),completed,termination,transfer_complete,meter.steps,meter.cases)

def migrate_protocol(protocol,new_version,new_operators):
    if not set(protocol.operators)<=set(new_operators):raise ContractError('InvalidMutation','removing operators requires an explicit task-consumer migration')
    return replace(protocol,operators=tuple(new_operators),version=new_version)
