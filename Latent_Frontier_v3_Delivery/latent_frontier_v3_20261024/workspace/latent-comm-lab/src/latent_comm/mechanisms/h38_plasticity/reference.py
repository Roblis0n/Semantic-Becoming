from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

OPS={'read':0,'scale':1,'clip':1,'running_mean':1,'precondition_diagonal':2,'masked_add':3}

def validate_rule(node,depth=0,count=None):
    count=[0] if count is None else count;count[0]+=1
    if depth>5 or count[0]>64 or node.op not in OPS or len(node.children)!=OPS[node.op]:raise ContractError('RuleTypeError','invalid bounded whitelist AST')
    finite_scalar(node.scalar)
    if node.parameter is not None and node.op not in ('scale','clip','running_mean','precondition_diagonal'):raise ContractError('RuleTypeError','this opcode does not consume a learnable scalar')
    if node.op=='read' and node.slot not in ('gradient','theta','memory','diagonal','mask'):raise ContractError('MetaLeakage','read may access only local support-derived statistics, never query labels')
    if node.op=='clip' and node.scalar<=0 or node.op=='running_mean' and not 0<=node.scalar<1 or node.op=='precondition_diagonal' and node.scalar<=0:raise ContractError('RuleTypeError','invalid clip, mean or preconditioner scalar')
    for child in node.children:validate_rule(child,depth+1,count)
    return count[0]

def interpret(node,environment,rule_parameters,memory_out):
    if node.op=='read':
        if node.slot not in environment:raise ContractError('RuleTypeError','required local statistic absent')
        return vector(environment[node.slot])
    v=[interpret(c,environment,rule_parameters,memory_out) for c in node.children]
    scalar=node.scalar if node.parameter is None else finite_scalar(rule_parameters[node.parameter])
    if node.op in ('clip','precondition_diagonal') and scalar<=0 or node.op=='running_mean' and not 0<=scalar<1:raise ContractError('RuleTypeError','learned scalar violates operator domain')
    if node.op=='scale':return scale(v[0],scalar)
    if node.op=='clip':return tuple(max(-scalar,min(scalar,x)) for x in v[0])
    if node.op=='running_mean':
        old=environment.get('memory',(0.,)*len(v[0]));value=add(scale(old,scalar),scale(v[0],1-scalar));memory_out['memory']=value;return value
    if node.op=='precondition_diagonal':
        if any(x<0 for x in v[1]):raise ContractError('RuleTypeError','diagonal statistic must be nonnegative')
        return tuple(x/(math.sqrt(d)+scalar) for x,d in zip(v[0],v[1],strict=True))
    if any(m not in (0.,1.) for m in v[2]):raise ContractError('WriteScopeViolation','masked_add requires exact binary coordinate mask')
    return tuple(a+m*b for a,b,m in zip(*v,strict=True))

def apply_rule(program,parameters,gradients,*,statistics=(),memory=(),rule_parameters=(),step=0,budget=StepBudget()):
    validate_rule(program.ast)
    if not 0<=step<program.lifetime_steps:raise ContractError('InnerStepLimit','rule lifetime expired')
    params=dict(parameters);grads=dict(gradients);stats=dict(statistics);mem=dict(memory);psi=dict(rule_parameters);meter=budget.meter()
    if set(grads)!=set(program.writable_groups) or not set(program.writable_groups)<=params.keys():raise ContractError('WriteScopeViolation','gradient/update groups must exactly match authorized scope')
    updates={}
    for name in program.writable_groups:
        meter.consume(steps=1);theta=vector(params[name]);grad=vector(grads[name]);meter.dimension(len(theta))
        if len(theta)!=len(grad):raise ContractError('RuleTypeError','gradient dimension differs')
        env={'gradient':grad,'theta':theta,'memory':mem.get(name,(0.,)*len(theta)),**dict(stats.get(name,()))};out={}
        update=interpret(program.ast,env,psi,out)
        if len(update)!=len(theta):raise ContractError('RuleTypeError','update changed parameter shape')
        magnitude=norm(update)
        if magnitude>program.max_update_norm:update=scale(update,program.max_update_norm/magnitude)
        params[name]=add(theta,update);updates[name]=update
        if 'memory' in out:mem[name]=out['memory']
    return RuleResult(tuple(params.items()),tuple(mem.items()),tuple(updates.items()),step+1,program.estimator,program.version)

def validate_partitions(support,query):
    if type(support) is not SupportBatch or type(query) is not QueryBatch or not support.partition_id or not query.partition_id or support.partition_id==query.partition_id:raise ContractError('MetaLeakage','support/query must be distinct typed partitions')
    return True

def migrate_rule(program,new_version,group_map):
    if set(group_map)!=set(program.writable_groups) or len(set(group_map.values()))!=len(group_map):raise ContractError('WriteScopeViolation','group migration must be explicit and bijective')
    return replace(program,writable_groups=tuple(group_map[g] for g in program.writable_groups),version=new_version)

def parse_rule(data,depth=0):
    if depth>5 or set(data)!={'op','children','scalar','slot','parameter'}:raise ContractError('RuleTypeError','invalid serialized AST')
    node=RuleNode(data['op'],tuple(parse_rule(c,depth+1) for c in data['children']),data['scalar'],data['slot'],data['parameter']);validate_rule(node);return node

def validate_optimizer_ownership(optimizer, rule_parameters, initial_parameters=()):
    expected=[id(p) for p in rule_parameters.values()]
    forbidden={id(p) for p in dict(initial_parameters).values()}
    if set(expected)&forbidden:raise ContractError('WriteScopeViolation','outer rule parameters must not alias initial/base/inner parameters')
    actual=[id(p) for group in optimizer.param_groups for p in group['params']]
    if not expected or len(expected)!=len(set(expected)) or len(actual)!=len(set(actual)) or set(actual)!=set(expected):
        raise ContractError('WriteScopeViolation','outer optimizer must own exactly the unique plasticity rule parameters, not base or inner parameters')
    return True
