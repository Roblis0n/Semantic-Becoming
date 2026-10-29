"""C20: ontology/question/operation/ISA/coordinate/learning/backend integration."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,Scope,StepBudget
from latent_comm.core.finite import matvec,norm,sub,eye,matrix_add,matrix_scale
from latent_comm.mechanisms.h07_legacy.types import ProgramPacket,Instruction,ValueType,CompiledProgram
from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
from latent_comm.mechanisms.h25_gauge.types import GaugePacket,FrameSpec,CovarianceReport
from latent_comm.mechanisms.h27_ontology.types import OntologySnapshot
from latent_comm.mechanisms.h29_questions.types import QuestionTransform,RelationWitness
from latent_comm.mechanisms.h30_analogy.types import TypedOperationGraph,AnalogyMorphism,CompiledAnalogy
from latent_comm.mechanisms.h38_plasticity.types import PlasticityProgram,SupportBatch,QueryBatch
from latent_comm.mechanisms.h40_instruction_set.types import Expr,MacroDefinition,ISARevision
from latent_comm.mechanisms.h42_ecology.types import TaskGenome,ProtocolGenome,MutationGrammar,EcologyState
from latent_comm.backends.capabilities import BackendCapabilities
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase

@dataclass(frozen=True)
class SemanticCompilerInput:
    ontology: OntologySnapshot
    required_concept: str
    public_record: tuple[tuple[str,object],...]
    question: QuestionTransform
    source_graph: TypedOperationGraph
    target_graph: TypedOperationGraph
    analogy: AnalogyMorphism
    source_operation: str
    initial_object: str
    object_scalars: tuple[tuple[str,float],...]
    task: TaskGenome
    protocol: ProtocolGenome
    grammar: MutationGrammar
    source_frame: FrameSpec
    target_frame: FrameSpec
    gauge: tuple
    rule: PlasticityProgram
    support: SupportBatch
    query: QueryBatch
    mode: str
    backend: BackendCapabilities
    versions: VersionSet
@dataclass(frozen=True)
class SemanticIR:
    request: SemanticCompilerInput
    relation: RelationWitness
    assumptions: tuple[str,...]
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class TypedOperations:
    semantics: SemanticIR
    ecology: EcologyState
    selected_task: TaskGenome
    @property
    def versions(self):return self.semantics.versions
@dataclass(frozen=True)
class LoweredMacro:
    operations: TypedOperations
    revision: ISARevision
    lowered: Expr
    scalar_input: float
    scalar_output: float
    @property
    def versions(self):return self.operations.versions
@dataclass(frozen=True)
class TransportedSemantics:
    macro: LoweredMacro
    analogy: CompiledAnalogy
    object_trace: tuple[str,...]
    covariance: CovarianceReport
    @property
    def versions(self):return self.macro.versions
@dataclass(frozen=True)
class OwnedExecutionPlan:
    transported: TransportedSemantics
    program: CompiledProgram
    inputs: tuple
    finite_answer: tuple[float,...]
    original_answer: tuple[float,...]
    rule: PlasticityProgram | None
    partitions: tuple[str,...]
    phase_owners: tuple[tuple[str,tuple[str,...]],...]
    @property
    def versions(self):return self.transported.versions
@dataclass(frozen=True)
class LockedBackendPlan:
    plan: OwnedExecutionPlan
    backend_status: str
    missing_capabilities: tuple[str,...]
    implementation_entries: tuple[str,...]
    research_execution_authorized: bool
    research_state: str
    versions: VersionSet


def question_and_concept_ir(value):
    from latent_comm.mechanisms.h27_ontology.reference import read_concept
    from latent_comm.mechanisms.h29_questions.reference import check_relation
    value.versions.require('state','ontology','isa','frame','task','evidence')
    if value.ontology.version!=value.versions.ontology or value.source_frame.version!=value.versions.frame or value.mode not in ('inference','learning'):raise ContractError('VersionMismatch','ontology, coordinate source and plan mode must be explicit')
    meaning=read_concept((value.ontology,),value.versions.ontology,value.required_concept,dict(value.public_record))
    if meaning is None:raise ContractError('UnknownConceptValue','missing observable is not false; request a typed observation',recoverable=True)
    if not meaning:raise ContractError('OutOfDomain','concept precondition does not authorize this semantic operation')
    relation=check_relation(value.question,budget=StepBudget(max_steps=16,max_cases=16))
    if not relation.sound or value.question.claimed_relation in ('necessary','heuristic'):raise ContractError('RelationUnproven','compiled answer transport needs a checked sound relation')
    return SemanticIR(value,relation,('typed public concept precondition','finite answer relation','declared partial analogy domain','invertible same-dimensional gauge'))


def typed_operations(value):
    from latent_comm.mechanisms.h42_ecology.reference import evolve,required_operators
    q=value.request
    if q.task.conditional:raise ContractError('UnboundPrimitive','this scalar macro binding has no compare primitive; retain the conditional task for a different backend')
    if not set(required_operators(q.task))<=set(q.protocol.operators):raise ContractError('UnboundPrimitive','initial protocol cannot express the requested task')
    ecology=evolve((q.task,),(q.protocol,),q.grammar,generations=1,world_limit=4,population_limit=4,budget=StepBudget(max_steps=24,max_cases=24))
    # The requested task is not swapped for an easier evolved task. Mutations
    # are archived as alternatives with static expressibility, not achievements.
    return TypedOperations(value,ecology,q.task)


def expand_macro(value):
    from latent_comm.mechanisms.h40_instruction_set.reference import lower,execute_base
    from latent_comm.mechanisms.h42_ecology.reference import execute_program
    q=value.semantics.request;table=dict(q.object_scalars)
    if q.initial_object not in table:raise ContractError('UnboundReference','source object has no concrete scalar implementation')
    offset=-q.task.offset if q.task.inverse else q.task.offset
    definition=MacroDefinition('task_delta',('x',),Expr('add',(Expr('var',name='x'),Expr('const',value=offset))),('scalar',))
    revision=ISARevision(q.versions.isa,(definition,));x=table[q.initial_object]
    lowered=lower(Expr('call',(Expr('const',value=x),),name='task_delta'),revision,budget=StepBudget(max_steps=32));answer=execute_base(lowered,{},budget=StepBudget(max_steps=16))
    if abs(answer-execute_program(q.task,q.protocol,x))>1e-12:raise ContractError('LoweringFailure','macro expansion changed requested task semantics')
    return LoweredMacro(value,revision,lowered,x,answer)


def transport_domains_and_coordinates(value):
    from latent_comm.mechanisms.h30_analogy.reference import check_morphism,compile_program
    from latent_comm.mechanisms.h25_gauge.reference import transport
    q=value.operations.semantics.request;analogy=check_morphism(q.source_graph,q.target_graph,q.analogy,budget=StepBudget(max_steps=16))
    _,trace=compile_program(q.source_graph,q.target_graph,analogy,(q.source_operation,),q.initial_object,budget=StepBudget(max_steps=8))
    source_op=next((o for o in q.source_graph.operations if o.name==q.source_operation),None)
    if source_op is None or q.initial_object not in dict(source_op.table):raise ContractError('UnmappedOperation','source finite operation has no declared edge')
    end=dict(source_op.table)[q.initial_object];scalars=dict(q.object_scalars)
    if end not in scalars or abs(scalars[end]-value.scalar_output)>1e-9:raise ContractError('CompositionMismatch','symbolic operation edge and numeric macro effect disagree')
    offset=value.scalar_output-value.scalar_input
    packet=GaugePacket(q.source_frame,(value.scalar_input,1.),((1.,offset),(0.,1.)),((1.,0.),))
    covariance=transport(packet,q.gauge,q.target_frame,budget=StepBudget(max_steps=1))
    return TransportedSemantics(value,analogy,trace,covariance)


def plan_owned_execution(value):
    from latent_comm.mechanisms.h07_legacy.reference import compile_program,execute
    from latent_comm.mechanisms.h29_questions.reference import satisfies,translate
    from latent_comm.mechanisms.h38_plasticity.reference import validate_rule,validate_partitions
    q=value.macro.operations.semantics.request;packet=value.covariance.transported;v=replace(q.versions,frame=q.target_frame.version)
    scope=Scope('c20:semantic-state',frozenset({'receiver'}),frozenset({'Z'}));delta=matrix_add(packet.operator,matrix_scale(eye(2),-1))
    operator=OperatorPacket(delta,eye(2),(0.,0.),1.,'identity','state','state',v,scope)
    state_type=ValueType('state',2,v.frame);types=(('initial',state_type),('operator',ValueType('operator',2,v.frame)),('readout',ValueType('readout',1,v.frame)))
    instructions=(Instruction('effect','APPLY_OPERATOR',('initial','operator'),state_type),Instruction('answer','DECODE',('effect','readout'),ValueType('observations',1,v.frame)))
    compiled=compile_program(ProgramPacket(instructions,types,'answer',v,scope),budget=StepBudget(max_steps=2));inputs=(('initial',packet.state),('operator',operator),('readout',packet.readout))
    answer,_=execute(compiled,dict(inputs),budget=StepBudget(max_steps=2));original=translate(q.question.backtranslation,answer)
    if not satisfies(q.question.target,answer) or not satisfies(q.question.source,original):raise ContractError('RelationUnproven','actual compiled answer violates declared finite question relation')
    rule=None;partitions=();owners=(('inference',()),)
    if q.mode=='learning':
        validate_rule(q.rule.ast);validate_partitions(q.support,q.query)
        if q.rule.writable_groups!=('adapter.offset',):raise ContractError('WriteScopeViolation','this concrete learning plan owns only adapter.offset; base and ISA definitions remain frozen')
        rule=q.rule;partitions=(q.support.partition_id,q.query.partition_id);owners=(('inner_support',rule.writable_groups),('outer_query',('plasticity_rule_parameters',)))
    return OwnedExecutionPlan(value,compiled,inputs,tuple(answer),tuple(original),rule,partitions,owners)


def bind_locked_backend(value):
    q=value.transported.macro.operations.semantics.request;required=('prefix',)+(('input_gradients',) if q.mode=='learning' else ());missing=[]
    for feature in required:
        try:q.backend.require(feature)
        except ContractError:missing.append(feature)
    status='UnboundBackend' if missing else 'SourceBoundResearchLocked'
    return LockedBackendPlan(value,status,tuple(missing),('latent_comm.backends.hf_prefix.forward_with_prefix','latent_comm.learning.engine.train' if q.mode=='learning' else 'latent_comm.cli.research'),False,'NOT_RUN',q.versions)

STAGES=(('question_and_concept_ir',('H27','H29'),'SemanticCompilerInput','SemanticIR','stop'),('typed_operations',('H07','H42'),'SemanticIR','TypedOperations','enumeration'),('expand_macro',('H40',),'TypedOperations','LoweredMacro','stop'),('transport_domains_and_coordinates',('H25','H30'),'LoweredMacro','TransportedSemantics','differentiable'),('plan_owned_execution',('H07','H38'),'TransportedSemantics','OwnedExecutionPlan','stop'),('bind_locked_backend',('H07',),'OwnedExecutionPlan','LockedBackendPlan','stop'))
def build_graph(versions):return linear_graph('C20',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','ontology','isa','frame','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Numeric effects must agree with symbolic operation tables before backend binding.','Source-bound capability metadata is not empirical integration verification.','All research execution remains policy locked, even with complete backend metadata.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (SemanticCompilerInput,SemanticIR,TypedOperations,LoweredMacro,TransportedSemantics,OwnedExecutionPlan,LockedBackendPlan)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h27_ontology.losses import LOSS_SPECS as H27
    from latent_comm.mechanisms.h29_questions.losses import LOSS_SPECS as H29
    from latent_comm.mechanisms.h25_gauge.losses import LOSS_SPECS as H25
    from latent_comm.mechanisms.h30_analogy.losses import LOSS_SPECS as H30
    from latent_comm.mechanisms.h38_plasticity.losses import LOSS_SPECS as H38
    from latent_comm.mechanisms.h40_instruction_set.losses import LOSS_SPECS as H40
    from latent_comm.mechanisms.h42_ecology.losses import LOSS_SPECS as H42
    return {'recipe':'C20','research_state':'NOT_RUN','phases':[objective_phase('concept',(('H27',H27,('distinction','behavior','drift')),)),objective_phase('question',(('H29',H29,('relation','backtranslation')),)),objective_phase('coordinate',(('H25',H25,('covariance','effect')),)),objective_phase('analogy',(('H30',H30,('commutation','behavior')),)),objective_phase('plasticity',(('H38',H38,('outer_query_full','update_budget')),)),objective_phase('macro',(('H40',H40,('fast_behavior','binding')),)),objective_phase('ecology',(('H42',H42,tuple(s.name for s in H42)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'aggregation':'separate phases with exact parameter ownership, never one unweighted global loss','immutable':['base ISA','external goal','authorization','historical ontology definitions']}
