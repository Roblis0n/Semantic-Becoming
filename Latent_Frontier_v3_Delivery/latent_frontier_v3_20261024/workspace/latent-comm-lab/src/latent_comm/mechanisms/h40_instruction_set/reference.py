from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

import json

def free_variables(expr,bound=frozenset()):
    if expr.op=='var':return set() if expr.name in bound else {expr.name}
    if expr.op=='let':return free_variables(expr.args[0],bound)|free_variables(expr.args[1],bound|{expr.name})
    return set().union(*(free_variables(a,bound) for a in expr.args)) if expr.args else set()

def encode_ast(expr):return [expr.op,expr.name,expr.value,[encode_ast(a) for a in expr.args]]
def encoding_bytes(expr):return len(json.dumps(encode_ast(expr),separators=(',',':'),ensure_ascii=False).encode())

def lower(expr,revision,budget=StepBudget()):
    meter=budget.meter();macros={m.name:m for m in revision.macros};counter=[0]
    for macro in revision.macros:
        if not free_variables(macro.body)<=set(macro.parameters):raise ContractError('LoweringFailure','macro contains unbound captured variable')
    occupied=free_variables(expr)|set().union(*(free_variables(m.body)|set(m.parameters) for m in revision.macros))
    def fresh():
        while True:
            counter[0]+=1;name='__hygienic_'+str(counter[0])
            if name not in occupied:occupied.add(name);return name
    def visit(node,env,stack):
        meter.consume(steps=1)
        if node.op=='var':return env.get(node.name,node)
        if node.op=='const':return node
        if node.op=='let':
            value=visit(node.args[0],env,stack);name=fresh();body=visit(node.args[1],{**env,node.name:Expr('var',name=name)},stack)
            return Expr('let',(value,body),name=name)
        if node.op=='call':
            if node.name not in macros:raise ContractError('VersionUnsupported','macro absent from requested ISA revision')
            if node.name in stack:raise ContractError('MacroRecursion','recursive macro definitions are rejected')
            macro=macros[node.name]
            if len(node.args)!=len(macro.parameters):raise ContractError('LoweringFailure','macro call arity differs')
            args=tuple(visit(a,env,stack) for a in node.args)
            return visit(macro.body,dict(zip(macro.parameters,args)),stack+(node.name,))
        return Expr(node.op,tuple(visit(a,env,stack) for a in node.args),node.name,node.value)
    return visit(expr,{},())

def execute_base(expr,inputs,budget=StepBudget()):
    meter=budget.meter()
    def run(node,environment):
        meter.consume(steps=1)
        if node.op=='const':return node.value
        if node.op=='var':
            if node.name not in environment:raise ContractError('LoweringFailure','unbound base variable')
            return finite_scalar(environment[node.name])
        if node.op=='let':return run(node.args[1],{**environment,node.name:run(node.args[0],environment)})
        if node.op=='call':raise ContractError('VersionUnsupported','old base reader requires lowering first')
        a,b=(run(c,environment) for c in node.args)
        return finite_scalar(a+b if node.op=='add' else a*b)
    return run(expr,dict(inputs))

def canonical_subtree(expr):
    names=sorted(free_variables(expr));mapping={n:Expr('var',name='p'+str(i)) for i,n in enumerate(names)}
    # Lowering through an explicit macro performs hygienic parameter substitution.
    macro=MacroDefinition('canonical',tuple(names),expr,('scalar',)*len(names))
    normalized=lower(Expr('call',tuple(mapping[n] for n in names),name='canonical'),ISARevision('canonical:1',(macro,)))
    return normalized,tuple('p'+str(i) for i in range(len(names)))

def propose_macro(corpus,name,budget=StepBudget()):
    meter=budget.meter();groups={}
    def visit(node):
        meter.consume(steps=1)
        if node.op in ('add','multiply','let'):
            body,params=canonical_subtree(node);key=json.dumps(encode_ast(body),separators=(',',':'));groups.setdefault(key,[body,params,0]);groups[key][2]+=1
        for child in node.args:visit(child)
    for expr in corpus:visit(expr)
    candidates=[]
    for body,params,count in groups.values():
        if count<2:continue
        definition=MacroDefinition(name,params,body,('scalar',)*len(params));call=Expr('call',tuple(Expr('var',name=p) for p in params),name=name)
        original=count*encoding_bytes(body);replacement=encoding_bytes(body)+len(name.encode())+sum(len(p.encode()) for p in params)+count*encoding_bytes(call)
        if original>replacement:candidates.append(MacroProposal(definition,count,original,replacement,original-replacement))
    if not candidates:raise ContractError('NoCompressionGain','no repeated typed subtree saves actual encoded bytes including definition cost')
    return max(candidates,key=lambda p:p.saved_bytes)

def migrate_for_reader(expr,source_revision,target_base_version):
    if target_base_version!=BASE_ISA_VERSION:raise ContractError('VersionUnsupported','reader base semantics differ')
    return lower(expr,source_revision)

def parse_expr(data,depth=0):
    if depth>16 or set(data)!={'op','args','name','value'}:raise ContractError('LoweringFailure','malformed bounded AST')
    return Expr(data['op'],tuple(parse_expr(a,depth+1) for a in data['args']),data['name'],data['value'])
