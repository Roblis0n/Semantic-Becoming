"""C09: frame → scale → hygienic ISA → transported action → public behavior."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.core.finite import matvec,matmul,transpose,add,sub,norm,eye,matrix_add,matrix_scale
from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
from latent_comm.mechanisms.h06_legacy.types import Chart,Transition
from latent_comm.mechanisms.h25_gauge.types import FrameSpec
from latent_comm.mechanisms.h35_renormalization.types import ScalePacket,MultiScaleState,ClosureResidual
from latent_comm.mechanisms.h40_instruction_set.types import Expr,ISARevision
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference

@dataclass(frozen=True)
class LanguageInput:
    operator: OperatorPacket
    source_state: tuple
    source_chart: Chart
    target_chart: Chart
    source_frame: FrameSpec
    target_frame: FrameSpec
    gauge: tuple | None
    chart_transition: Transition | None
    scale: ScalePacket
    scale_version: str
    scalar_program: Expr
    isa: ISARevision
    scalar_inputs: tuple[tuple[str,float],...]
    readout: tuple
    target_readout: tuple
    task: str
    retain_detail: bool=True
    @property
    def versions(self):return self.operator.versions

@dataclass(frozen=True)
class FrameBinding:
    request: LanguageInput
    local_state: tuple
    route: str
    @property
    def versions(self):return self.request.versions

@dataclass(frozen=True)
class ScaleSelection:
    frame: FrameBinding
    state: MultiScaleState
    closure: ClosureResidual
    @property
    def versions(self):return self.frame.versions

@dataclass(frozen=True)
class LoweredOperation:
    scale: ScaleSelection
    base_program: Expr
    operation: OperatorPacket
    @property
    def versions(self):return self.operation.versions

@dataclass(frozen=True)
class TransportedAction:
    lowered: LoweredOperation
    operation: OperatorPacket
    initial: tuple
    readout: tuple
    route: str
    @property
    def versions(self):return replace(self.lowered.versions,frame=self.lowered.scale.frame.request.target_frame.version)

@dataclass(frozen=True)
class EffectBundle:
    action: TransportedAction
    source_effect: tuple
    target_effect: tuple
    operation_trace: tuple
    @property
    def versions(self):return self.action.versions

@dataclass(frozen=True)
class BehaviorReadout:
    source_behavior: tuple
    target_behavior: tuple
    behavior_residual: tuple
    closure_error: float
    route: str
    lost_information: str
    operator_order_trace: tuple
    versions: VersionSet


def register_frames(value):
    from latent_comm.mechanisms.h06_legacy.reference import route,encode
    from latent_comm.mechanisms.h25_gauge.reference import condition_check
    q=value;q.versions.require('state','frame','ontology','isa','task','evidence')
    if q.target_chart.invalidated or q.task not in q.target_chart.task_family:raise ContractError('NoMatchingChart','receiving chart is invalidated or outside its declared task family')
    if q.source_chart.versions.frame!=q.versions.frame or q.source_frame.version!=q.versions.frame or q.isa.version!=q.versions.isa:raise ContractError('VersionMismatch','source frame/ISA differs from operator')
    if q.source_frame.dimension!=len(q.source_chart.read_map) or q.target_frame.dimension!=len(q.target_chart.read_map) or q.target_frame.version!=q.target_chart.versions.frame:raise ContractError('UnboundFrame','registered chart/frame axes disagree')
    if not q.source_chart.versions.matches(q.target_chart.versions,('ontology','task')):raise ContractError('MigrationRequired','chart bridge cannot silently change ontology/task')
    route((q.source_chart,),q.source_state,task=q.task,model_revision=q.source_chart.model_revision)
    z=encode(q.source_chart,q.source_state,task=q.task,model_revision=q.source_chart.model_revision)
    if len(z)!=len(q.operator.U):raise ContractError('DimensionMismatch','operator is not in the source local chart')
    if q.gauge is not None:
        if q.chart_transition is not None:raise ContractError('AmbiguousFrame','choose gauge or declared heterogeneous transition, not both')
        if q.source_frame.dimension!=q.target_frame.dimension:raise ContractError('DimensionMismatch','gauge cannot compress')
        condition_check(q.gauge,q.source_frame);condition_check(q.gauge,q.target_frame);kind='gauge'
    elif q.chart_transition is not None:kind='partial_pushforward'
    else:raise ContractError('UnboundFrame','no frame transport or chart transition')
    return FrameBinding(q,z,kind)


def select_scale(value):
    from latent_comm.mechanisms.h35_renormalization.reference import closure_report,coarsen
    q=value.request
    if q.scale.source_version!=q.scale_version or len(q.scale.micro_axes)!=len(value.local_state):raise ContractError('ScaleMismatch','scale version or axes differ from selected source')
    report=closure_report(q.scale)
    if not q.retain_detail and not report.closed:raise ContractError('ClosureFailure','nonclosed coarse dynamics require memory, not a false macro state')
    return ScaleSelection(value,coarsen(q.scale,value.local_state,q.retain_detail),report)


def lower_instruction(value):
    from latent_comm.mechanisms.h40_instruction_set.reference import lower,execute_base
    q=value.frame.request;base=lower(q.scalar_program,q.isa,budget=StepBudget(max_steps=32))
    alpha=execute_base(base,dict(q.scalar_inputs),budget=StepBudget(max_steps=32));operation=replace(q.operator,alpha=alpha)
    # The scale closure certificate must concern this operation, not a same-shape one.
    if operation.nonlinearity=='identity':
        linear=matrix_add(eye(len(operation.U)),matrix_scale(matmul(operation.U,transpose(operation.V)),operation.alpha));bias=tuple(operation.alpha*x for x in matvec(operation.U,operation.bias))
        if any(abs(x-y)>1e-9 for a,b in zip(linear,q.scale.micro_dynamics) for x,y in zip(a,b)) or norm(sub(bias,q.scale.micro_bias))>1e-9:raise ContractError('ScaleDynamicsMismatch','macro closure belongs to another lowered operator')
    elif value.state.detail_residual is None:raise ContractError('ClosureFailure','nonlinear action requires retained source detail in this affine scale binding')
    return LoweredOperation(value,base,operation)


def transport_operation(value):
    from latent_comm.mechanisms.h01_legacy.reference import change_frame
    from latent_comm.mechanisms.h25_gauge.reference import right_solve
    from latent_comm.mechanisms.h35_renormalization.reference import refine
    q=value.scale.frame.request;state=value.scale.state
    if state.detail_residual is not None:z=refine(q.scale,state)
    else:
        if q.readout!=matmul(matmul(q.readout,q.scale.lift),q.scale.coarse_map):raise ContractError('IrrecoverableDetail','declared behavior does not factor through retained coarse coordinates')
        z=matvec(q.scale.lift,state.coarse)
    if value.scale.frame.route=='gauge':
        target_versions=replace(value.operation.versions,frame=q.target_frame.version)
        operation=change_frame(value.operation,q.gauge,target_versions)
        return TransportedAction(value,operation,matvec(q.gauge,z),right_solve(q.readout,q.gauge),'gauge')
    # This partial action is defined on source-chart states, not every target state.
    return TransportedAction(value,value.operation,z,q.target_readout,'partial_pushforward')


def apply_target(value):
    from latent_comm.mechanisms.h01_legacy.reference import apply
    from latent_comm.mechanisms.h06_legacy.reference import transition
    q=value.lowered.scale.frame.request
    source,_=apply(value.lowered.scale.frame.local_state,value.lowered.operation,budget=StepBudget(max_steps=16))
    target,trace=apply(value.initial,value.operation,budget=StepBudget(max_steps=16))
    if value.route=='partial_pushforward':target=transition(target,q.chart_transition,q.source_chart,q.target_chart,task=q.task)
    return EffectBundle(value,source,target,trace)


def read_behavior(value):
    q=value.action.lowered.scale.frame.request
    source=matvec(q.readout,value.source_effect);target=matvec(value.action.readout,value.target_effect)
    lost='retained detail memory' if q.retain_detail else 'discarded only behavior-invisible detail under explicit factorization'
    if value.action.route=='partial_pushforward':lost=q.chart_transition.information_loss+'; no target-wide inverse claimed'
    return BehaviorReadout(source,target,sub(target,source),value.action.lowered.scale.closure.norm,value.action.route,lost,value.operation_trace,value.versions)


STAGES=(('register_frames',('H06','H25'),'LanguageInput','FrameBinding','stop'),('select_scale',('H35',),'FrameBinding','ScaleSelection','stop'),('lower_instruction',('H40',),'ScaleSelection','LoweredOperation','enumeration'),('transport_operation',('H01','H25','H06'),'LoweredOperation','TransportedAction','differentiable'),('apply_target',('H01','H06'),'TransportedAction','EffectBundle','differentiable'),('read_behavior',('H25','H35'),'EffectBundle','BehaviorReadout','differentiable'))

def build_graph(versions,target_versions=None):
    target_versions=versions if target_versions is None else target_versions
    if not versions.matches(target_versions,('schema','state','ontology','isa','task','evidence')):raise ContractError('MigrationRequired','C09 frame transport cannot change unrelated semantic axes')
    graph=linear_graph('C09',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Heterogeneous chart transitions are partial actions, not invertible gauge transformations.','Real-model action and discovered semantic alignment remain NOT_RUN.'))
    after={'transport_operation:out','apply_target:out','read_behavior:out'}
    return replace(graph,objects=tuple(replace(o,versions=target_versions) if o.object_id in after else o for o in graph.objects))


def run_reference(request,*,budget=StepBudget()):
    types={c.__name__:c for c in (LanguageInput,FrameBinding,ScaleSelection,LoweredOperation,TransportedAction,EffectBundle,BehaviorReadout)}
    return execute_reference(build_graph(request.versions,replace(request.versions,frame=request.target_frame.version)),{'input':request},{n:globals()[n] for n,*_ in STAGES},types,budget=budget)


def describe_training():
    from .contracts import objective_phase
    from latent_comm.mechanisms.h25_gauge.losses import LOSS_SPECS as H25
    from latent_comm.mechanisms.h35_renormalization.losses import LOSS_SPECS as H35
    from latent_comm.mechanisms.h40_instruction_set.losses import LOSS_SPECS as H40
    return {'recipe':'C09','research_state':'NOT_RUN','phases':[
        objective_phase('coordinate_calibration',(('H25',H25,('covariance', 'effect')),)),
        objective_phase('scale_closure',(('H35',H35,('commute', 'task', 'residual')),)),
        objective_phase('macro_definition_and_fast_implementation',(('H40',H40,('description', 'fast_behavior', 'binding')),)),
    ],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'frozen':['base_models','immutable_source_definitions'],'structure_search':'enumeration is distinct from differentiable phases','execution':'unified gated runner only; no joint global loss by default'}
