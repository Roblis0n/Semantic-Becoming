from dataclasses import replace
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import topological_order
from latent_comm.mechanisms.h07_legacy.types import Instruction,ProgramPacket
from latent_comm.mechanisms.h07_legacy.reference import SIGNATURES,compile_program

def validate_grammar(grammar):
    names=tuple(p.name for p in grammar.productions)
    if set(names)&set(SIGNATURES):raise ContractError('PrimitiveShadowing','base ISA names are immutable')
    edges=[]
    for p in grammar.productions:
        for s in p.body:
            if s.operation in names:edges.append((s.operation,p.name))
            elif s.operation not in SIGNATURES:raise ContractError('UnknownProduction',s.operation)
    return topological_order(names,tuple(sorted(set(edges))))

def expand(grammar,name,arguments,input_types,*,scope,task,budget=StepBudget()):
    validate_grammar(grammar)
    if task not in grammar.task_family:raise ContractError('OutOfDomain','grammar task scope')
    definitions={p.name:p for p in grammar.productions};types=dict(input_types);instructions=[];meter=budget.meter();serial=0
    def fresh():
        nonlocal serial
        while True:
            serial+=1;key='h14:node:'+str(serial)
            if key not in types:return key
    def visit(skill,args,stack):
        if skill in stack:raise ContractError('RecursiveGrammar','recursive expansion denied')
        if skill not in definitions:raise ContractError('UnknownProduction',skill)
        p=definitions[skill]
        if len(args)!=len(p.parameters) or any(a not in types or types[a]!=t for a,(_,t) in zip(args,p.parameters)):raise ContractError('TypeViolation','typed scoped argument binding')
        env={name:arg for (name,_),arg in zip(p.parameters,args)}
        for step in p.body:
            meter.consume(steps=1)
            if any(a not in env for a in step.arguments):raise ContractError('UnboundVariable','production can only read lexical parameters and earlier locals')
            refs=tuple(env[a] for a in step.arguments)
            if step.operation in definitions:result=visit(step.operation,refs,stack+(skill,))
            else:
                result=fresh();instructions.append(Instruction(result,step.operation,refs,step.output_type,step.bound));types[result]=step.output_type
            if types[result]!=step.output_type:raise ContractError('TypeViolation','nonterminal result type mismatch')
            env[step.local_name]=result
        if p.result_name not in env or types[env[p.result_name]]!=p.output_type:raise ContractError('TypeViolation','production result contract')
        return env[p.result_name]
    result=visit(name,tuple(arguments),())
    packet=ProgramPacket(tuple(instructions),tuple(input_types),result,replace(grammar.versions,isa=grammar.base_isa),scope)
    return compile_program(packet,budget=budget)
def lower_for_reader(grammar,compiled,*,supported_isa,supported_opcodes):
    if grammar.base_isa!=supported_isa or any(n.opcode not in supported_opcodes for n in compiled.packet.nodes):raise ContractError('VersionUnsupported','old reader must support the actual lowered ISA')
    return compiled
