"""C15: public boundary smoothing over multirate dynamics and exact DSL continuation."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,StepBudget,RoleView
from latent_comm.core.finite import norm,sub,matvec,eye,matrix_add,matrix_scale,solve,transpose
from latent_comm.mechanisms.h05_legacy.types import ProgramOperation,ResumeContract,ContinuationPacket
from latent_comm.mechanisms.h20_legacy.types import CognitiveClock,CognitiveEvent,EventDecision
from latent_comm.mechanisms.h33_reciprocal.types import DynamicsPacket
from latent_comm.mechanisms.h34_boundary_value.types import TrajectoryFactorGraph,BoundaryResult
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase

@dataclass(frozen=True)
class MultirateTrajectoryInput:
    public_boundary: RoleView
    states: tuple[tuple[str,tuple[float,...]],...]
    start: str
    dynamics: tuple[tuple[str,DynamicsPacket],...]
    horizon: int
    quantization_tolerance: float
    schedule_delays: tuple[tuple[str,int],...]
    current_receiver_version: str
    path_limit: int
    versions: VersionSet
@dataclass(frozen=True)
class PublicBoundary:
    request: MultirateTrajectoryInput
    terminal: object
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class LocalDynamicsGraph:
    boundary: PublicBoundary
    graph: TrajectoryFactorGraph
    edge_implementations: tuple[tuple[str,str,str,tuple, float],...]
    @property
    def versions(self):return self.boundary.versions
@dataclass(frozen=True)
class BidirectionalMessages:
    dynamics: LocalDynamicsGraph
    result: BoundaryResult
    @property
    def versions(self):return self.dynamics.versions
@dataclass(frozen=True)
class AsyncContinuation:
    messages: BidirectionalMessages
    path: tuple[str,...]
    packet: ContinuationPacket | None
    decisions: tuple[EventDecision,...]
    committed_vectors: tuple[tuple[float,...],...]
    status: str
    @property
    def versions(self):return self.messages.versions
@dataclass(frozen=True)
class TrajectoryReadout:
    path: tuple[str,...]
    states: tuple[tuple[float,...],...]
    mean: tuple[float,...]
    signed_area: float
    endpoint_residual: float | None
    status: str
    alternatives: tuple[tuple[str,...],...]
    unexplored_prefixes: tuple[tuple[str,...],...]
    schedule: tuple[EventDecision,...]
    versions: VersionSet
    causality_label: str='offline_public_boundary_planning_not_online_future_observation'


def public_boundary(value):
    from latent_comm.mechanisms.h34_boundary_value.reference import terminal_from_view
    value.versions.require('state','ontology','isa','frame','world','task','evidence')
    if value.public_boundary.versions!=value.versions:raise ContractError('VersionMismatch','public boundary belongs to another task snapshot')
    terminal=terminal_from_view(value.public_boundary)
    if not 1<=value.horizon<=4 or not 1<=len(value.states)<=8 or not 1<=len(value.dynamics)<=3:raise ContractError('BudgetExhausted','C15 fixture supports four layers/eight prototypes/three rhythms')
    states=dict(value.states)
    if len(states)!=len(value.states) or value.start not in states or not set(terminal.states)<=states.keys():raise ContractError('BoundaryInfeasible','explicit distinct state prototypes must cover public boundaries')
    if any(len(z)!=2 for z in states.values()) or not 0<=value.quantization_tolerance<=2:raise ContractError('DimensionMismatch','C15 trajectory readout uses explicit finite 2D coordinates')
    if set(dict(value.schedule_delays))!=set(dict(value.dynamics)) or any(not 1<=x<=4 for _,x in value.schedule_delays):raise ContractError('InvalidClock','each local rhythm has an explicit bounded scheduling delay')
    return PublicBoundary(value,terminal)


def local_dynamics(value):
    from latent_comm.mechanisms.h33_reciprocal.reference import integrate
    q=value.request;edges=[]
    for name,packet in q.dynamics:
        if packet.version!=q.versions.state or packet.steps!=1:raise ContractError('VersionMismatch','one-step local factors must share the source dynamics version')
        # The same midpoint linear map used by H33 is compiled into the H05 DSL.
        a=matrix_add(packet.skew_coupling,matrix_scale(packet.dissipation,-1));left=matrix_add(eye(2),matrix_scale(a,-packet.step_size/2));right=matrix_add(eye(2),matrix_scale(a,packet.step_size/2))
        mapping=transpose(tuple(solve(left,col) for col in transpose(right)))
        for source,z in q.states:
            actual=integrate(replace(packet,state=z),budget=StepBudget(max_steps=1)).states[-1]
            target,error=min(((target,norm(sub(actual,end))) for target,end in q.states),key=lambda x:(x[1],x[0]))
            if error<=q.quantization_tolerance:edges.append((source,target,name,mapping,error))
    transitions=tuple(sorted({(a,b) for a,b,*_ in edges}))
    graph=TrajectoryFactorGraph(tuple(n for n,_ in q.states),(transitions,)*q.horizon,(q.start,),value.terminal,q.versions.state)
    return LocalDynamicsGraph(value,graph,tuple(edges))


def bidirectional_messages(value):
    from latent_comm.mechanisms.h34_boundary_value.reference import solve_boundary
    return BidirectionalMessages(value,solve_boundary(value.graph,budget=StepBudget(max_steps=64,max_cases=16),path_limit=value.boundary.request.path_limit))


def asynchronous_continuation(value):
    from latent_comm.mechanisms.h05_legacy.reference import capture,resume,validate
    from latent_comm.mechanisms.h20_legacy.reference import EventScheduler,bind_path_event,bind_dynamics_event
    q=value.dynamics.boundary.request
    if not value.result.paths:return AsyncContinuation(value,(),None,(),(),value.result.status)
    path=value.result.paths[0];chosen=[];program=[];previous=()
    for t,(a,b) in enumerate(zip(path,path[1:])):
        options=[e for e in value.dynamics.edge_implementations if e[0]==a and e[1]==b]
        edge=min(options,key=lambda e:(e[4],e[2]));chosen.append(edge)
        source=('x0','y0') if t==0 else (f'x{t}',f'y{t}')
        for axis,key in enumerate((f'x{t+1}',f'y{t+1}')):
            expression=('add',('mul',('const',edge[3][axis][0]),('var',source[0])),('mul',('const',edge[3][axis][1]),('var',source[1])))
            program.append(ProgramOperation(f'step{t}:axis{axis}',key,expression,previous))
        previous=(f'step{t}:axis0',f'step{t}:axis1')
    contract=ResumeContract('finite-midpoint-program','no-tokenizer','float64','named-scalars','exact_program')
    start=dict(q.states)[q.start];packet=capture(program,dict(zip(('x0','y0'),start)),contract=contract,versions=q.versions,transaction_version='trajectory-snapshot',evidence=(q.versions.evidence,),boundaries=('public_terminal',))
    scheduler=EventScheduler(max_steps=16);elapsed=0;prior=None;clock=CognitiveClock(0,'plan',0,'selected-path',0,())
    for t,edge in enumerate(chosen):
        elapsed+=dict(q.schedule_delays)[edge[2]];event_id=f'event{t}'
        clock=CognitiveClock(elapsed,'continue',1,'selected-path',t+1,(('coordinator',t+1),))
        event=CognitiveEvent(event_id,'continuation_requested',edge[2],clock,frozenset(() if prior is None else (prior,)),q.versions.state,(('state:trajectory',q.versions.state),),elapsed,16,'reject',f'program:chunk:{t}',q.versions)
        bind_path_event(event,path,trajectory_version=q.versions.state);bind_dynamics_event(event,dict(q.dynamics)[edge[2]],readout_index=1)
        scheduler.deliver(event);prior=event_id
    vectors=[start];status='pending'
    while status=='pending':
        decisions,status=scheduler.advance({'state:trajectory':q.current_receiver_version})
        for decision in decisions:
            if decision.status!='ready':continue
            validate(packet,contract=contract,versions=q.versions,transaction_version='trajectory-snapshot',available_evidence=(q.versions.evidence,))
            candidate=resume(packet,max_operations=2,budget=StepBudget(max_steps=32))
            if candidate.pending_dependencies:raise ContractError('PendingDependency','a full vector chunk cannot publish partially')
            # Only publish after both scalar coordinates complete. No reader sees
            # the half-updated candidate; immutable old packet remains available.
            packet=candidate;t=len(vectors);values=dict(packet.values);vectors.append((values[f'x{t}'],values[f'y{t}']))
    done=packet.program_counter==len(packet.program)
    return AsyncContinuation(value,path,packet,tuple(scheduler.log),tuple(vectors),'Completed' if done else 'StaleOrUnresolvedContinuation')


def trajectory_readout(value):
    q=value.messages.dynamics.boundary.request;states=value.committed_vectors
    mean=tuple(sum(z[i] for z in states)/len(states) for i in range(2)) if states else ()
    area=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(states,states[1:]))/2
    residual=min((norm(sub(states[-1],dict(q.states)[s])) for s in value.messages.dynamics.graph.terminal.states),default=None) if states else None
    status=value.status
    if status=='Completed' and residual is not None and residual>q.quantization_tolerance:status='QuantizedPathNotExactBoundarySolution'
    return TrajectoryReadout(value.path,states,mean,area,residual,status,value.messages.result.paths[1:],value.messages.result.unexplored_prefixes,value.decisions,q.versions)

STAGES=(('public_boundary',('H34',),'MultirateTrajectoryInput','PublicBoundary','stop'),('local_dynamics',('H33',),'PublicBoundary','LocalDynamicsGraph','differentiable'),('bidirectional_messages',('H34',),'LocalDynamicsGraph','BidirectionalMessages','enumeration'),('asynchronous_continuation',('H05','H20'),'BidirectionalMessages','AsyncContinuation','stop'),('trajectory_readout',('H33','H34'),'AsyncContinuation','TrajectoryReadout','stop'))
def build_graph(versions):return linear_graph('C15',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','ontology','isa','frame','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Finite quantization is explicit and final continuous boundary residual is rechecked.','Physical scheduling time is not path position or causal order.','Backward messages originate exclusively in public boundary constraints.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (MultirateTrajectoryInput,PublicBoundary,LocalDynamicsGraph,BidirectionalMessages,AsyncContinuation,TrajectoryReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h33_reciprocal.losses import LOSS_SPECS as H33
    from latent_comm.mechanisms.h34_boundary_value.losses import LOSS_SPECS as H34
    return {'recipe':'C15','research_state':'NOT_RUN','phases':[objective_phase('local_trajectory',(('H33',H33,tuple(s.name for s in H33)),)),objective_phase('public_boundary',(('H34',H34,tuple(s.name for s in H34)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'online_claim':False,'scheduler':'deterministic event/version arbitration is not an optimizer'}
