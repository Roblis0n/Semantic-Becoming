"""Explicit H25/H30/H35/H40 consumers; no implicit coordinate/ISA guesses."""
from dataclasses import replace
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matvec,norm,sub
from .reference import apply,change_frame

def gauge_operator(operator,gauge,source_frame,target_frame):
    from latent_comm.mechanisms.h25_gauge.reference import condition_check
    if operator.versions.frame!=source_frame.version or len(operator.U)!=source_frame.dimension or source_frame.dimension!=target_frame.dimension:raise ContractError('FrameMismatch','H25 exact operator conjugation needs same-dimensional bound frames')
    condition_check(gauge,source_frame)
    return change_frame(operator,gauge,replace(operator.versions,frame=target_frame.version))

def finite_operation_graph(operator,named_states,*,operation_name,version,budget=StepBudget()):
    from latent_comm.mechanisms.h30_analogy.types import TypedObject,FiniteOperation,TypedOperationGraph
    if not named_states or len(named_states)>64 or version!=operator.versions.isa:raise ContractError('VersionMismatch','explicit finite H30 operation domain and source ISA')
    outputs=[];meter=budget.meter()
    for name,state in named_states:
        meter.consume(steps=1,cases=1);value=apply(state,operator,budget=budget)[0]
        matches=[key for key,target in named_states if norm(sub(value,target))<1e-10]
        if len(matches)!=1:raise ContractError('UnmappedResult','finite operation must close in its declared unique state domain')
        outputs.append((name,matches[0]))
    return TypedOperationGraph(tuple(TypedObject(name,operator.domain) for name,_ in named_states),(FiniteOperation(operation_name,operator.domain,operator.codomain,tuple(outputs)),),version)

def coarse_effect_check(operator,macro_operator,scale_packet,probes,*,budget=StepBudget()):
    if operator.versions.state!=scale_packet.source_version or macro_operator.versions.state!=scale_packet.target_version:raise ContractError('VersionMismatch','H35 source/target scale states bind explicitly')
    residuals=[];meter=budget.meter()
    for state in probes:
        meter.consume(steps=2,cases=1)
        coarse_actual=matvec(scale_packet.coarse_map,apply(state,operator,budget=budget)[0]);coarse_pred=apply(matvec(scale_packet.coarse_map,state),macro_operator,budget=budget)[0]
        residuals.append(sub(coarse_actual,coarse_pred))
    return tuple(residuals),'finite_probe_consistency_not_global_nonlinear_closure'

def scalar_affine_macro(operator,*,name,source_isa):
    from latent_comm.mechanisms.h40_instruction_set.types import Expr,MacroDefinition
    if source_isa!=operator.versions.isa or len(operator.U)!=1 or operator.nonlinearity!='identity':raise ContractError('LoweringFailure','H40 scalar base ISA can lower only bound scalar affine operator exactly')
    coefficient=1+operator.alpha*sum(u*v for u,v in zip(operator.U[0],operator.V[0]));offset=operator.alpha*sum(u*b for u,b in zip(operator.U[0],operator.bias))
    body=Expr('add',(Expr('multiply',(Expr('const',value=coefficient),Expr('var',name='x'))),Expr('const',value=offset)))
    return MacroDefinition(name,('x',),body,('scalar',),'scalar')
