"""C16: compatible kernel → synthetic counterfactual question → typed protocol ecology."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h43_world_kernels.types import WorldKernel,SharedNoiseJoint,ComposedWorldKernel
from latent_comm.mechanisms.h44_dreaming.types import CounterfactualEdit,DreamWorld,SyntheticEvidence,QuestionCandidate
from latent_comm.mechanisms.h29_questions.types import QuestionIR,PolynomialConstraint,QuestionTransform,AnswerMap,RelationWitness
from latent_comm.mechanisms.h40_instruction_set.types import Expr,MacroDefinition,ISARevision
from latent_comm.mechanisms.h42_ecology.types import TaskGenome,ProtocolGenome,MutationGrammar,EcologyState
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase

@dataclass(frozen=True)
class CounterfactualEcologyInput:
    kernels: tuple[WorldKernel,...]
    noise: SharedNoiseJoint
    edits: tuple[CounterfactualEdit,...]
    start_state: tuple[str,...]
    action: str
    grammar: MutationGrammar
    protocol: ProtocolGenome
    claim_kind: str
    versions: VersionSet
@dataclass(frozen=True)
class CompatibleKernelPool:
    request: CounterfactualEcologyInput
    baseline: ComposedWorldKernel
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class SyntheticCounterfactual:
    pool: CompatibleKernelPool
    world: DreamWorld
    evidence: SyntheticEvidence
    @property
    def versions(self):return self.pool.versions
@dataclass(frozen=True)
class NewQuestions:
    world: SyntheticCounterfactual
    candidates: tuple[QuestionCandidate,...]
    transforms: tuple[QuestionTransform,...]
    witnesses: tuple[RelationWitness,...]
    seed_tasks: tuple[TaskGenome,...]
    @property
    def versions(self):return self.world.versions
@dataclass(frozen=True)
class TypedProtocolPopulation:
    questions: NewQuestions
    ecology: EcologyState | None
    macros: tuple[MacroDefinition,...]
    compiled_examples: tuple[tuple[str,str,float,float],...]
    uncompiled: tuple[tuple[str,str],...]
    @property
    def versions(self):return self.questions.versions
@dataclass(frozen=True)
class SyntheticLineageArchive:
    world: DreamWorld
    evidence: SyntheticEvidence
    question_relations: tuple[RelationWitness,...]
    population: EcologyState | None
    compiled_examples: tuple[tuple[str,str,float,float],...]
    obligations: tuple[tuple[str,str],...]
    lineage_edges: tuple[tuple[str,str],...]
    versions: VersionSet
    research_state: str='NOT_RUN'
    evidence_kind: str='synthetic_consequence_and_static_expressibility_only'


def compatible_pool(value):
    from latent_comm.mechanisms.h43_world_kernels.reference import compose_kernels
    value.versions.require('world','task','evidence','isa')
    if len(value.kernels)>2:raise ContractError('DreamBudget','C16 finite pool has at most two compatible components')
    baseline=compose_kernels(value.kernels,value.noise,budget=StepBudget(max_steps=32))
    if len(baseline.states)>4 or value.start_state not in baseline.states or value.action not in dict(baseline.actions):raise ContractError('DreamBudget','explicit start/action in at most four joint states required')
    return CompatibleKernelPool(value,baseline)


def synthetic_world(value):
    from latent_comm.mechanisms.h44_dreaming.reference import construct_dream,observe_dream,assert_evidence_use
    q=value.request
    world=construct_dream(q.kernels,q.noise,q.edits,assumptions=('declared finite conditional edit, not a real intervention',),budget=StepBudget(max_steps=32))
    initial=tuple(float(s==q.start_state) for s in world.kernel.states)
    evidence=observe_dream(world,initial,(q.action,),budget=StepBudget(max_steps=1))
    assert_evidence_use(evidence,'c16:synthetic-claim',q.claim_kind)
    return SyntheticCounterfactual(value,world,evidence)


def generate_questions(value):
    from latent_comm.mechanisms.h44_dreaming.reference import question_candidates,answer_question
    from latent_comm.mechanisms.h29_questions.reference import check_relation
    q=value.pool.request
    candidates=tuple(c for c in question_candidates(value.world,value.pool.baseline,(q.start_state,),budget=StepBudget(max_steps=16)) if c.action==q.action)
    if len(candidates)>4:raise ContractError('DreamBudget','at most four changed probability questions in this finite binding')
    transforms=[];witnesses=[];tasks=[]
    for i,candidate in enumerate(candidates):
        baseline=dict(value.pool.baseline.transitions)[candidate.action][value.pool.baseline.states.index(candidate.start_state)][value.pool.baseline.states.index(candidate.target_state)]
        answer=answer_question(value.world,candidate);domain=tuple(sorted({0.,.5,1.,answer,baseline}));delta=tuple(x-baseline for x in domain)
        source=QuestionIR(f'probability:{i}',('probability',),(domain,),(PolynomialConstraint(((1.,(1,)),),'eq',answer),),q.versions.task,(value.evidence.evidence_id,))
        target=QuestionIR(f'change:{i}',('probability_change',),(delta,),(PolynomialConstraint(((1.,(1,)),),'eq',answer-baseline),),q.versions.task,(value.evidence.evidence_id,))
        mapping=AnswerMap(((1.,),),(baseline,),target.question_id,source.question_id)
        transform=QuestionTransform(source,target,mapping,'equivalent',('both equations are synthetic kernel consequences',));witness=check_relation(transform)
        transforms.append(transform);witnesses.append(witness);tasks.append(TaskGenome(f'question-task:{i}','add',answer-baseline,False,0.,False,(candidate.question_id,),'task:1'))
    return NewQuestions(value,candidates,tuple(transforms),tuple(witnesses),tuple(tasks))


def mutate_and_compile(value):
    from latent_comm.mechanisms.h42_ecology.reference import evolve,execute_program
    from latent_comm.mechanisms.h40_instruction_set.reference import lower,execute_base
    q=value.world.pool.request
    if not value.seed_tasks:return TypedProtocolPopulation(value,None,(),(),(('world','no changed questions under the supplied edit'),))
    ecology=evolve(value.seed_tasks,(q.protocol,),q.grammar,generations=1,world_limit=8,population_limit=4,budget=StepBudget(max_steps=48,max_cases=48))
    macros=[];compiled=[];uncompiled=[]
    for task in ecology.tasks:
        if task.conditional:
            uncompiled.append((task.task_id,'conditional comparison has no lowering in immutable scalar base ISA; retained as typed ecology candidate'));continue
        offset=-task.offset if task.inverse else task.offset
        macro=MacroDefinition('delta_'+str(len(macros)),('x',),Expr('add',(Expr('var',name='x'),Expr('const',value=offset))),('scalar',));macros.append(macro)
        revision=ISARevision(q.versions.isa,tuple(macros))
        for protocol in ecology.protocols:
            attempt=next((a for a in ecology.transfer_graph if a.task_id==task.task_id and a.protocol_id==protocol.protocol_id),None)
            if attempt is None or attempt.status!='expressible_candidate':continue
            x=.25;ast=lower(Expr('call',(Expr('const',value=x),),name=macro.name),revision,budget=StepBudget(max_steps=32));result=execute_base(ast,{},budget=StepBudget(max_steps=16))
            if abs(result-execute_program(task,protocol,x))>1e-12:raise ContractError('LoweringFailure','macro does not preserve finite task semantics')
            compiled.append((task.task_id,protocol.protocol_id,x,result))
    if not ecology.transfer_complete:uncompiled.append(('transfer_graph','budget-exhausted cells remain unexamined, not failed competence'))
    return TypedProtocolPopulation(value,ecology,tuple(macros),tuple(compiled),tuple(uncompiled))


def archive_lineage(value):
    from latent_comm.core.finite import topological_order
    world=value.questions.world;edges=[(p,world.world.world_id) for p in world.world.parent_kernel_ids]
    edges.extend((p,world.evidence.evidence_id) for p in world.evidence.parents)
    for candidate in value.questions.candidates:edges.extend(((world.evidence.evidence_id,candidate.question_id),(world.world.world_id,candidate.question_id)))
    if value.ecology:
        edges.extend((parent,child) for child,parents in value.ecology.lineage for parent in parents)
    edges=tuple(sorted(set(edges)));topological_order(tuple(sorted({x for e in edges for x in e})),edges)
    return SyntheticLineageArchive(world.world,world.evidence,value.questions.witnesses,value.ecology,value.compiled_examples,value.uncompiled,edges,value.versions)

STAGES=(('compatible_pool',('H43',),'CounterfactualEcologyInput','CompatibleKernelPool','stop'),('synthetic_world',('H43','H44'),'CompatibleKernelPool','SyntheticCounterfactual','stop'),('generate_questions',('H29','H44'),'SyntheticCounterfactual','NewQuestions','enumeration'),('mutate_and_compile',('H40','H42'),'NewQuestions','TypedProtocolPopulation','enumeration'),('archive_lineage',('H42','H44'),'TypedProtocolPopulation','SyntheticLineageArchive','stop'))
def build_graph(versions):return linear_graph('C16',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','world','task','evidence','isa'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Synthetic descendants never count as independent real-world evidence.','World and question IDs are provenance, not model input features.','Base ISA cannot express compare; those ecology candidates remain explicit obligations.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (CounterfactualEcologyInput,CompatibleKernelPool,SyntheticCounterfactual,NewQuestions,TypedProtocolPopulation,SyntheticLineageArchive)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h44_dreaming.losses import LOSS_SPECS as H44
    from latent_comm.mechanisms.h42_ecology.losses import LOSS_SPECS as H42
    from latent_comm.mechanisms.h40_instruction_set.losses import LOSS_SPECS as H40
    return {'recipe':'C16','research_state':'NOT_RUN','phases':[objective_phase('world_proposal',(('H44',H44,tuple(s.name for s in H44)),)),objective_phase('alternating_protocol_and_tasks',(('H42',H42,tuple(s.name for s in H42)),)),objective_phase('fast_macro',(('H40',H40,('fast_behavior','binding')),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'holdout':'independent source lineage required; synthetic parent kernels cannot certify their own truth'}
