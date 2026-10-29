"""C13: provenance-bound behavior tangent transport and scoped plasticity plan."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.core.finite import matvec,norm,sub
from latent_comm.mechanisms.h19_legacy.types import ConsolidatedAdapter,TeacherTrace
from latent_comm.mechanisms.h25_gauge.types import FrameSpec
from latent_comm.mechanisms.h37_gradient_transport.types import Linearization,TransportedUpdate
from latent_comm.mechanisms.h38_plasticity.types import PlasticityProgram,RuleNode,RuleResult,SupportBatch,QueryBatch
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference

@dataclass(frozen=True)
class LearningProtocolInput:
    source: Linearization
    target: Linearization
    source_direction: tuple[float,...]
    source_basis: tuple[tuple[float,...],...]
    source_adapter: ConsolidatedAdapter
    target_adapter: ConsolidatedAdapter
    teacher_traces: tuple[TeacherTrace,...]
    unseen_instance_ids: frozenset[str]
    target_parameters: tuple[tuple[str,tuple[float,...]],...]
    support: SupportBatch
    query: QueryBatch
    trust_radius: float
    ridge: float
    step: int
    versions: VersionSet

@dataclass(frozen=True)
class BoundAnchors:
    request: LearningProtocolInput
    trace_ids: frozenset[str]
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class LearningEffect:
    anchors: BoundAnchors
    reexpressed_source: Linearization
    reexpressed_direction: tuple[float,...]
    behavior_direction: tuple[float,...]
    @property
    def versions(self):return self.anchors.versions
@dataclass(frozen=True)
class ProjectedEffect:
    effect: LearningEffect
    update: TransportedUpdate
    @property
    def versions(self):return self.effect.versions
@dataclass(frozen=True)
class CompiledUpdateRule:
    projection: ProjectedEffect
    program: PlasticityProgram
    finite_result: RuleResult
    realized_direction: tuple[float,...]
    realized_residual: tuple[float,...]
    @property
    def versions(self):return self.projection.versions
@dataclass(frozen=True)
class FutureTrainerPlan:
    rule: CompiledUpdateRule
    support_partition: str
    query_partition: str
    frozen_base_revisions: tuple[str,str]
    trace_ids: frozenset[str]
    evidence_sources: frozenset[str]
    outer_owners: tuple[str,...]
    research_state: str
    versions: VersionSet
    evidence_kind: str='fixed_linear_math_not_observed_model_gradient'


def bind_anchors(value):
    from latent_comm.mechanisms.h19_legacy.reference import bind_learning_effect,validate_training_partition
    from latent_comm.mechanisms.h38_plasticity.reference import validate_partitions
    value.versions.require('state','ontology','isa','frame','task','evidence')
    if value.source.anchors!=value.target.anchors or value.source.anchors.public_task_version!=value.versions.task:raise ContractError('AnchorMismatch','public observable coordinates and current task must agree')
    for adapter,linearization in ((value.source_adapter,value.source),(value.target_adapter,value.target)):
        if not adapter.versions.matches(value.versions,('ontology','isa','task','evidence')):raise ContractError('VersionMismatch','adapter semantics differ from public anchor context')
        bind_learning_effect(adapter,linearization)
    traces=validate_training_partition(value.teacher_traces,value.unseen_instance_ids,step=value.step,versions=value.versions)
    if not traces<=value.source_adapter.trained_trace_ids:raise ContractError('MissingProvenance','source learning effect must be backed by this consolidated adapter trace set')
    validate_partitions(value.support,value.query)
    if set(dict(value.target_parameters))!=set(value.target.parameter_names) or any(len(v)!=1 for _,v in value.target_parameters):raise ContractError('ShapeMismatch','finite parameter coordinates are explicit named scalars')
    if not 0<value.trust_radius<1e10 or norm(value.source_direction)>value.trust_radius:raise ContractError('TrustRegion','source direction exceeds declared local linear trust radius')
    return BoundAnchors(value,traces)


def source_learning_effect(value):
    from latent_comm.mechanisms.h25_gauge.reference import condition_check,right_solve
    q=value.request;frame=FrameSpec('source_parameter_coordinates',len(q.source.parameter_names),'GL',q.versions.frame)
    condition_check(q.source_basis,frame)
    # This is an explicit change of the SAME source tangent basis, not a
    # declaration that unrelated model parameters or tokenizer indices coincide.
    changed=replace(q.source,jacobian=right_solve(q.source.jacobian,q.source_basis))
    direction=matvec(q.source_basis,q.source_direction);effect=matvec(changed.jacobian,direction)
    if norm(sub(effect,matvec(q.source.jacobian,q.source_direction)))>1e-9:raise ContractError('CovarianceFailure','basis change altered observable learning effect')
    return LearningEffect(value,changed,direction,effect)


def project_target_effect(value):
    from latent_comm.mechanisms.h37_gradient_transport.reference import transport_direction
    q=value.anchors.request
    result=transport_direction(value.reexpressed_source,q.target,value.reexpressed_direction,ridge=q.ridge,max_steps=16,current_source_version=q.source_adapter.version,current_target_version=q.target_adapter.version)
    return ProjectedEffect(value,result)


def compile_update_rule(value):
    from latent_comm.mechanisms.h19_legacy.reference import bind_update_rule
    from latent_comm.mechanisms.h38_plasticity.reference import apply_rule
    q=value.effect.anchors.request
    # The H38 gradient slot carries a declared projected descent-direction
    # statistic here. No fabricated loss gradient or query target enters it.
    program=PlasticityProgram(RuleNode('scale',(RuleNode('read',slot='gradient'),),scalar=1.),value.update.parameter_names,q.trust_radius,1,1,'c13-rule-1','exact_unroll')
    bind_update_rule(q.target_adapter,program)
    if norm(value.update.delta)>q.trust_radius:
        factor=q.trust_radius/norm(value.update.delta);delta=tuple(x*factor for x in value.update.delta)
    else:delta=value.update.delta
    result=apply_rule(program,q.target_parameters,tuple((name,(x,)) for name,x in zip(value.update.parameter_names,delta)))
    realized=matvec(q.target.jacobian,tuple(dict(result.applied_updates)[n][0] for n in q.target.parameter_names))
    return CompiledUpdateRule(value,program,result,realized,sub(realized,value.update.behavior_direction))


def prepare_future_trainer(value):
    q=value.projection.effect.anchors.request
    # Compilation is not consolidation: no parameter artifact or new active
    # adapter version is registered until a separately authorized real run.
    return FutureTrainerPlan(value,q.support.partition_id,q.query.partition_id,(q.source_adapter.base_revision,q.target_adapter.base_revision),value.projection.effect.anchors.trace_ids,q.source_adapter.evidence_sources,('plasticity_rule',),'NOT_RUN',q.versions)

STAGES=(('bind_anchors',('H19','H37'),'LearningProtocolInput','BoundAnchors','stop'),('source_learning_effect',('H25','H37'),'BoundAnchors','LearningEffect','differentiable'),('project_target_effect',('H37',),'LearningEffect','ProjectedEffect','differentiable'),('compile_update_rule',('H19','H38'),'ProjectedEffect','CompiledUpdateRule','stop'),('prepare_future_trainer',('H38',),'CompiledUpdateRule','FutureTrainerPlan','stop'))
def build_graph(versions):return linear_graph('C13',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','ontology','isa','frame','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('A local linear tangent effect is not a global functional equivalence.','Unreachable and post-clipping residuals remain explicit.','Future training is blocked; no source gradient was observed from a model.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (LearningProtocolInput,BoundAnchors,LearningEffect,ProjectedEffect,CompiledUpdateRule,FutureTrainerPlan)},budget=budget)
def describe_training():
    from .contracts import objective_phase
    from latent_comm.mechanisms.h19_legacy.losses import LEDGER as H19
    from latent_comm.mechanisms.h37_gradient_transport.losses import LOSS_SPECS as H37
    from latent_comm.mechanisms.h38_plasticity.losses import LOSS_SPECS as H38
    return {'recipe':'C13','research_state':'NOT_RUN','phases':[
        objective_phase('consolidate',(('H19',H19,('distillation', 'operation_behavior')),)),
        objective_phase('transport',(('H37',H37,('effect', 'local', 'ridge')),)),
        objective_phase('meta_rule',(('H38',H38,('outer_query_full', 'update_budget')),)),
    ],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'frozen':['base_models','immutable_source_definitions'],'structure_search':'enumeration is distinct from differentiable phases','execution':'unified gated runner only; no joint global loss by default'}
