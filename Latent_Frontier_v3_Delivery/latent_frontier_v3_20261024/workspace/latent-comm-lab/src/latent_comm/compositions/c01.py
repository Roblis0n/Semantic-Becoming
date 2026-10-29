"""C01: capability-bounded temporary computation across explicit local charts."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,Scope,StepBudget
from latent_comm.core.finite import matmul,matvec,norm,sub
from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
from latent_comm.mechanisms.h06_legacy.types import Chart,Transition
from latent_comm.mechanisms.h07_legacy.types import ProgramPacket,ValueType,Instruction,CompiledProgram
from latent_comm.mechanisms.h22_legacy.types import PartitionState,PartitionAction,CoordinateMigration,TransitionRecord,StateReference
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class TemporaryComputationInput:
    partition: PartitionState
    cell_id: str
    source_actor: str
    target_actor: str
    source_chart: Chart
    target_chart: Chart
    chart_edge: Transition
    task_family: str
    operator: OperatorPacket
    readout: tuple
    versions: VersionSet
@dataclass(frozen=True)
class TypedDependencyGraph:
    request: TemporaryComputationInput
    source_value: tuple[float,...]
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class ChartBinding:
    dependency: TypedDependencyGraph
    target_local: tuple[float,...]
    repartition: TransitionRecord
    @property
    def versions(self):return self.dependency.versions
@dataclass(frozen=True)
class OperatorDispatch:
    binding: ChartBinding
    program: CompiledProgram
    inputs: tuple
    @property
    def versions(self):return self.binding.versions
@dataclass(frozen=True)
class TemporaryComputationResult:
    observations: tuple[float,...]
    final_local_state: tuple[float,...]
    target_model_state: tuple[float,...]
    partition_transition: TransitionRecord
    execution_trace: tuple
    information_loss: str
    versions: VersionSet
    research_state: str='NOT_RUN'

def typed_graph(value):
    from latent_comm.mechanisms.h22_legacy.reference import resolve_reference
    value.versions.require('state','frame','ontology','isa','task','evidence')
    if value.source_chart.versions!=value.versions:raise ContractError('VersionMismatch','source chart must bind the source snapshot exactly')
    source_axes=value.versions.as_dict();target_axes=value.target_chart.versions.as_dict()
    if any(source_axes[k]!=target_axes[k] for k in source_axes if k!='frame'):raise ContractError('MigrationRequired','chart transport changes coordinates only; ontology/ISA/world/task/evidence need their own migration')
    if value.operator.versions!=value.target_chart.versions:raise ContractError('VersionMismatch','operator must bind all target chart semantic axes')
    if len(value.partition.cells)!=1:raise ContractError('ScopeViolation','C01 finite graph owns exactly one isolated state cell')
    cell=next((c for c in value.partition.cells if c.cell_id==value.cell_id),None)
    if cell is None or value.partition.versions!=value.versions or cell.frame!=value.source_chart.versions.frame:raise ContractError('FrameMismatch','source cell and source chart context differ')
    ref=StateReference(cell.cell_id,cell.revision,value.partition.version,cell.frame)
    state=resolve_reference(value.partition,ref,actor=value.source_actor,write=True)
    if value.target_actor not in cell.readers or value.target_actor not in cell.writers:raise ContractError('CapabilityExpansion','temporary computation cannot grant a new model/actor access')
    return TypedDependencyGraph(value,state)

def bind_charts(value):
    from latent_comm.mechanisms.h06_legacy.reference import encode,transition,write_back
    from latent_comm.mechanisms.h22_legacy.reference import transition as repartition
    q=value.request
    source=encode(q.source_chart,value.source_value,task=q.task_family,model_revision=q.source_chart.model_revision)
    target=transition(source,q.chart_edge,q.source_chart,q.target_chart,task=q.task_family)
    if any(q.chart_edge.bias):raise ContractError('UnboundMap','this raw-state partition migration requires linear chart edge; affine migration needs homogeneous coordinates')
    raw=write_back(q.target_chart,target)
    checked=encode(q.target_chart,raw,task=q.task_family,model_revision=q.target_chart.model_revision)
    if norm(sub(checked,target))>1e-9:raise ContractError('IrrecoverableDetail','target write/read composition does not preserve the proposed local computation')
    cell=q.partition.cells[0];mapping=matmul(q.target_chart.write_map,matmul(q.chart_edge.mapping,q.source_chart.read_map))
    action=PartitionAction('handoff',(cell.partition,),'temporary-target',frozenset({q.target_actor}),frozenset({cell.cell_id}),q.partition.version,q.partition.version+':handoff')
    migration=CoordinateMigration(cell.cell_id,cell.frame,q.target_chart.versions.frame,mapping,'explicit-chart:'+q.chart_edge.information_loss)
    record=repartition(q.partition,action,migrations=(migration,))
    return ChartBinding(value,target,record)

def dispatch_operator(value):
    from latent_comm.mechanisms.h07_legacy.reference import compile_program
    q=value.dependency.request;v=q.operator.versions;dimension=len(value.target_local)
    if not v.matches(q.target_chart.versions,('frame','ontology','isa')):raise ContractError('FrameMismatch','operator is not bound to the target chart semantic context')
    scope=Scope('c01:target',frozenset({q.target_actor}),frozenset({'Z'}));state=ValueType('state',dimension,v.frame)
    packet=ProgramPacket((Instruction('apply','APPLY_OPERATOR',('state','operator'),state),),(('state',state),('operator',ValueType('operator',dimension,v.frame))),'apply',v,scope)
    return OperatorDispatch(value,compile_program(packet,actor=q.target_actor,budget=StepBudget(max_steps=1)),(('state',value.target_local),('operator',q.operator)))

def target_decode(value):
    from latent_comm.mechanisms.h07_legacy.reference import execute
    from latent_comm.mechanisms.h06_legacy.reference import write_back
    q=value.binding.dependency.request
    state,trace=execute(value.program,dict(value.inputs),actor=q.target_actor,budget=StepBudget(max_steps=1))
    return TemporaryComputationResult(matvec(q.readout,state),state,write_back(q.target_chart,state),value.binding.repartition,trace,q.chart_edge.information_loss,q.versions)

STAGES=(('typed_graph',('H07','H22'),'TemporaryComputationInput','TypedDependencyGraph','stop'),('bind_charts',('H06','H22'),'TypedDependencyGraph','ChartBinding','differentiable'),('dispatch_operator',('H01','H07'),'ChartBinding','OperatorDispatch','stop'),('target_decode',('H01','H06','H07'),'OperatorDispatch','TemporaryComputationResult','differentiable'))
def build_graph(versions):return linear_graph('C01',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Handoff changes local research partition only, not host privileges.','Heterogeneous chart edges retain explicit information-loss declarations.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (TemporaryComputationInput,TypedDependencyGraph,ChartBinding,OperatorDispatch,TemporaryComputationResult)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h01_legacy.losses import LEDGER as H01
    from latent_comm.mechanisms.h06_legacy.losses import LEDGER as H06
    from latent_comm.mechanisms.h07_legacy.losses import LEDGER as H07
    return {'recipe':'C01','research_state':'NOT_RUN','phases':[objective_phase('operators',(('H01',H01,tuple(s.name for s in H01)),)),objective_phase('charts',(('H06',H06,tuple(s.name for s in H06)),)),objective_phase('typed_program',(('H07',H07,tuple(s.name for s in H07)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'training_routes':['frozen-base','one-sided adaptation','joint adapters with explicit ownership'],'frozen':['host permissions','external model access']}
