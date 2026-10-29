"""C11: task quotient, commuting analogy and executable answer transport."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet,Scope,StepBudget
from latent_comm.core.finite import norm,sub
from latent_comm.mechanisms.h07_legacy.types import ProgramPacket,Instruction,ValueType,CompiledProgram
from latent_comm.mechanisms.h29_questions.types import QuestionTransform,RelationWitness
from latent_comm.mechanisms.h30_analogy.types import TypedOperationGraph,AnalogyMorphism,CompiledAnalogy
from latent_comm.mechanisms.h47_quotient.types import StateDomain,FiniteQuery,TaskRelativeQuotient
from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference

@dataclass(frozen=True)
class ProblemMigrationInput:
    question_transform: QuestionTransform
    state_domain: StateDomain
    queries: tuple[FiniteQuery,...]
    source_graph: TypedOperationGraph
    target_graph: TypedOperationGraph
    morphism: AnalogyMorphism
    source_program: tuple[str,...]
    initial_source_object: str
    target_coordinates: tuple[tuple[str,tuple],...]
    target_operators: tuple[tuple[str,OperatorPacket],...]
    versions: VersionSet

@dataclass(frozen=True)
class CheckedQuestion:
    request: ProblemMigrationInput
    witness: RelationWitness

@dataclass(frozen=True)
class QuotientProblem:
    question: CheckedQuestion
    quotient: TaskRelativeQuotient
    initial_class: str

@dataclass(frozen=True)
class AnalogicalProgram:
    problem: QuotientProblem
    analogy: CompiledAnalogy
    translated_operations: tuple
    object_trace: tuple

@dataclass(frozen=True)
class ExecutableTargetProgram:
    analogy: AnalogicalProgram
    program: CompiledProgram
    input_values: tuple

@dataclass(frozen=True)
class TargetAnswer:
    program: ExecutableTargetProgram
    answer: tuple
    execution_trace: tuple

@dataclass(frozen=True)
class MigratedAnswer:
    original_answer: tuple
    target_answer: tuple
    relation: str
    sound: bool
    complete: bool
    unmapped_edges: tuple
    erased_distinctions: tuple
    execution_trace: tuple


def question_ir(value):
    from latent_comm.mechanisms.h29_questions.reference import check_relation
    value.versions.require('state','frame','ontology','isa','task','evidence')
    if len(value.source_program)>16 or len(value.state_domain.state_ids)>8:raise ContractError('BudgetExhausted','C11 finite binding permits 16 program steps and eight source states')
    witness=check_relation(value.question_transform,budget=StepBudget(max_steps=32,max_cases=32))
    if not witness.sound or value.question_transform.claimed_relation in {'necessary','heuristic'}:raise ContractError('RelationUnproven','a certified answer transport cannot use a necessary/heuristic edge')
    if set(value.state_domain.state_ids)!={o.object_id for o in value.source_graph.objects}:raise ContractError('QueryFamilyUndefined','quotient domain must refer to the source operation graph')
    return CheckedQuestion(value,witness)


def task_quotient(value):
    from latent_comm.mechanisms.h47_quotient.reference import form_quotient
    q=value.request;quotient=form_quotient(q.state_domain,q.queries,'quotient:'+q.versions.task,retain_source=True,budget=StepBudget(max_steps=32,max_cases=8))
    group=next((c.class_id for c in quotient.classes if q.initial_source_object in c.members),None)
    if group is None:raise ContractError('OutOfDomain','source initial object absent')
    return QuotientProblem(value,quotient,group)


def analogy_morphism(value):
    from latent_comm.mechanisms.h30_analogy.reference import check_morphism,compile_program
    q=value.question.request;compiled=check_morphism(q.source_graph,q.target_graph,q.morphism,budget=StepBudget(max_steps=32))
    translated,trace=compile_program(q.source_graph,q.target_graph,compiled,q.source_program,q.initial_source_object,budget=StepBudget(max_steps=32))
    # The quotient is task-relative metadata. We retain the actual source state;
    # representative execution would additionally require a congruence proof.
    return AnalogicalProgram(value,compiled,translated,trace)


def compile_target_program(value):
    from latent_comm.mechanisms.h01_legacy.reference import apply
    from latent_comm.mechanisms.h07_legacy.reference import compile_program
    q=value.problem.question.request;coordinates=dict(q.target_coordinates);operators=dict(q.target_operators);graph_ops={o.name:o for o in q.target_graph.operations}
    if not value.object_trace or value.object_trace[0] not in coordinates:raise ContractError('UnboundReference','initial target coordinate missing')
    initial=coordinates[value.object_trace[0]];dim=len(initial);state_type=ValueType('state',dim,q.versions.frame)
    input_types={'initial':state_type};input_values={'initial':initial};nodes=[];previous='initial'
    for index,name in enumerate(value.translated_operations):
        if name not in operators:raise ContractError('UnboundOperation','mapped operation has no concrete numerical implementation')
        op=operators[name]
        if not op.versions.matches(q.versions,('frame','ontology','isa')) or len(op.U)!=dim:raise ContractError('FrameMismatch','mapped operator axes/versions differ')
        # Check the actual numerical operator, not only names in two graph tables.
        table=dict(graph_ops[name].table);source_id=value.object_trace[index];target_id=value.object_trace[index+1]
        if table.get(source_id)!=target_id or source_id not in coordinates or target_id not in coordinates:raise ContractError('UnmappedOperation','graph trace lacks numerical boundary coordinates')
        effect,_=apply(coordinates[source_id],op,budget=StepBudget(max_steps=1))
        if norm(sub(effect,coordinates[target_id]))>1e-9:raise ContractError('CompositionMismatch','numeric target implementation violates the commuting graph edge')
        binding='operator:'+str(index);input_types[binding]=ValueType('operator',dim,q.versions.frame);input_values[binding]=op
        output='step:'+str(index);nodes.append(Instruction(output,'APPLY_OPERATOR',(previous,binding),state_type));previous=output
    scope=Scope('c11:target',frozenset({'receiver'}),frozenset({'Z'}))
    packet=ProgramPacket(tuple(nodes),tuple(input_types.items()),previous,q.versions,scope)
    return ExecutableTargetProgram(value,compile_program(packet,budget=StepBudget(max_steps=32)),tuple(input_values.items()))


def execute_target(value):
    from latent_comm.mechanisms.h07_legacy.reference import execute
    from latent_comm.mechanisms.h29_questions.reference import satisfies
    result,trace=execute(value.program,dict(value.input_values),budget=StepBudget(max_steps=32))
    target_question=value.analogy.problem.question.request.question_transform.target
    if not satisfies(target_question,result):raise ContractError('OutOfDomain','target program did not produce a solution of its declared question')
    return TargetAnswer(value,tuple(result),trace)


def translate_answer(value):
    from latent_comm.mechanisms.h29_questions.reference import translate,satisfies
    problem=value.program.analogy.problem;q=problem.question.request;answer=translate(q.question_transform.backtranslation,value.answer)
    if not satisfies(q.question_transform.source,answer):raise ContractError('RelationUnproven','backtranslation failed original question constraints')
    witness=problem.question.witness
    relation='partial' if q.question_transform.claimed_relation=='partial' else witness.relation
    erased=tuple(c.members for c in problem.quotient.classes if len(c.members)>1)
    return MigratedAnswer(answer,value.answer,relation,witness.sound,witness.complete,value.program.analogy.analogy.uncovered_edges,erased,value.execution_trace)


STAGES=(('question_ir',('H29',),'ProblemMigrationInput','CheckedQuestion','stop'),('task_quotient',('H47',),'CheckedQuestion','QuotientProblem','enumeration'),('analogy_morphism',('H30',),'QuotientProblem','AnalogicalProgram','enumeration'),('compile_target_program',('H07','H30'),'AnalogicalProgram','ExecutableTargetProgram','stop'),('execute_target',('H07',),'ExecutableTargetProgram','TargetAnswer','stop'),('translate_answer',('H29',),'TargetAnswer','MigratedAnswer','stop'))
def build_graph(versions):return linear_graph('C11',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('A query quotient does not authorize representative execution without congruence.','A sound partial answer map is not a completeness proof.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (ProblemMigrationInput,CheckedQuestion,QuotientProblem,AnalogicalProgram,ExecutableTargetProgram,TargetAnswer,MigratedAnswer)},budget=budget)
def describe_training():
    from .contracts import objective_phase
    from latent_comm.mechanisms.h29_questions.losses import LOSS_SPECS as H29
    from latent_comm.mechanisms.h30_analogy.losses import LOSS_SPECS as H30
    return {'recipe':'C11','research_state':'NOT_RUN','phases':[
        objective_phase('relation_and_backtranslation',(('H29',H29,('relation', 'backtranslation', 'path_policy')),)),
        objective_phase('commuting_structure',(('H30',H30,('matching', 'commutation', 'behavior')),)),
    ],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'frozen':['base_models','immutable_source_definitions'],'structure_search':'enumeration is distinct from differentiable phases','execution':'unified gated runner only; no joint global loss by default'}
