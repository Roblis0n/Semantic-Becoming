"""C04: exact finite-program continuation across versioned local actor handoff."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h05_legacy.types import ProgramOperation,ResumeContract,ContinuationPacket
from latent_comm.mechanisms.h20_legacy.types import CognitiveClock,CognitiveEvent,EventDecision
from latent_comm.mechanisms.h22_legacy.types import PartitionState,PartitionAction,TransitionRecord,StateReference
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class AsyncResumeInput:
    program: tuple[ProgramOperation,...]
    values: tuple[tuple[str,float],...]
    cut_operations: int
    source_contract: ResumeContract
    target_contract: ResumeContract
    partition: PartitionState
    cell_id: str
    source_actor: str
    target_actor: str
    target_partition_version: str
    actual_receiver_version: str
    available_dependencies: frozenset[str]
    evidence: tuple[str,...]
    delay: int
    versions: VersionSet
@dataclass(frozen=True)
class CapturedCutpoint:
    request: AsyncResumeInput
    packet: ContinuationPacket
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class HandedOffCapsule:
    cutpoint: CapturedCutpoint
    migration: TransitionRecord
    packet: ContinuationPacket
    @property
    def versions(self):return self.cutpoint.versions
@dataclass(frozen=True)
class CheckedContinuation:
    capsule: HandedOffCapsule
    event: CognitiveEvent
    @property
    def versions(self):return self.capsule.versions
@dataclass(frozen=True)
class ResumedComputation:
    checked: CheckedContinuation
    packet: ContinuationPacket
    decisions: tuple[EventDecision,...]
    status: str
    @property
    def versions(self):return self.checked.versions
@dataclass(frozen=True)
class AsyncResumeReadout:
    packet: ContinuationPacket
    decisions: tuple[EventDecision,...]
    partition: PartitionState
    status: str
    source_completed: tuple[str,...]
    versions: VersionSet
    equality_claim: str='exact finite DSL only; no heterogeneous model-cache equivalence'

def cutpoint(value):
    from latent_comm.mechanisms.h05_legacy.reference import capture,resume
    from latent_comm.mechanisms.h22_legacy.reference import resolve_reference
    if value.source_contract.mode!='exact_program' or value.target_contract.mode!='exact_program':raise ContractError('UnsupportedFixture','actual model continuation is a separate locked backend path')
    if not 0<=value.cut_operations<=len(value.program)<=8 or not 1<=value.delay<=8:raise ContractError('BudgetExhausted','bounded source cut and physical delay required')
    if value.partition.versions!=value.versions or len(value.partition.cells)!=1:raise ContractError('VersionMismatch','finite source owns a single exact snapshot cell')
    cell=value.partition.cells[0]
    if cell.cell_id!=value.cell_id:raise ContractError('UnboundReference','source state cell missing')
    resolve_reference(value.partition,StateReference(cell.cell_id,cell.revision,value.partition.version,cell.frame),actor=value.source_actor,write=True)
    packet=capture(value.program,dict(value.values),contract=value.source_contract,versions=value.versions,transaction_version=value.partition.version,evidence=value.evidence,boundaries=('public task',))
    if value.cut_operations:packet=resume(packet,max_operations=value.cut_operations,available_dependencies=value.available_dependencies,budget=StepBudget(max_steps=32))
    return CapturedCutpoint(value,packet)

def capsule(value):
    from latent_comm.mechanisms.h22_legacy.reference import transition
    q=value.request;cell=q.partition.cells[0]
    if q.source_contract!=q.target_contract:raise ContractError('ResumeMismatch','exact program continuation cannot silently change backend/DSL identity')
    action=PartitionAction('handoff',(cell.partition,),'destination',frozenset({q.target_actor}),frozenset({cell.cell_id}),q.partition.version,q.target_partition_version)
    migration=transition(q.partition,action)
    # Explicit local ownership migration changes applicability versions while
    # preserving the exact immutable program, value environment and counter.
    packet=replace(value.packet,versions=migration.after.versions,transaction_version=migration.after.version,target_resume_contract=q.target_contract)
    return HandedOffCapsule(value,migration,packet)

def version_check(value):
    from latent_comm.mechanisms.h05_legacy.reference import validate
    from latent_comm.mechanisms.h22_legacy.reference import resolve_reference
    q=value.cutpoint.request;cell=value.migration.after.cells[0]
    resolve_reference(value.migration.after,StateReference(cell.cell_id,cell.revision,value.migration.after.version,cell.frame),actor=q.target_actor,write=True)
    validate(value.packet,contract=q.target_contract,versions=value.migration.after.versions,transaction_version=value.migration.after.version,available_evidence=q.evidence)
    clock=CognitiveClock(q.delay,'resume',1,'program',value.packet.program_counter,(('coordinator',1),))
    event=CognitiveEvent('resume-event','continuation_requested',q.source_actor,clock,frozenset(),value.packet.versions.state,(('state:partition',value.migration.after.version),),q.delay,8,'reject','continuation:source',value.packet.versions)
    return CheckedContinuation(value,event)

def resume(value):
    from latent_comm.mechanisms.h20_legacy.reference import EventScheduler
    from latent_comm.mechanisms.h05_legacy.reference import resume as continue_program
    q=value.capsule.cutpoint.request;scheduler=EventScheduler(max_steps=8);scheduler.deliver(value.event);packet=value.capsule.packet;status='pending'
    while status=='pending':
        decisions,status=scheduler.advance({'state:partition':q.actual_receiver_version})
        for decision in decisions:
            if decision.status=='ready':packet=continue_program(packet,max_operations=max(1,len(packet.program)-packet.program_counter),available_dependencies=q.available_dependencies,budget=StepBudget(max_steps=64))
    done=packet.program_counter==len(packet.program)
    result='SuffixCompleted' if done else 'WaitingForDependencies' if packet.pending_dependencies else 'StaleReceiverRejected'
    return ResumedComputation(value,packet,tuple(scheduler.log),result)

def schedule_readout(value):
    q=value.checked.capsule.cutpoint.request
    return AsyncResumeReadout(value.packet,value.decisions,value.checked.capsule.migration.after,value.status,value.checked.capsule.cutpoint.packet.completed_operations,q.versions)

STAGES=(('cutpoint',('H05',),'AsyncResumeInput','CapturedCutpoint','stop'),('capsule',('H05','H22'),'CapturedCutpoint','HandedOffCapsule','stop'),('version_check',('H05','H20','H22'),'HandedOffCapsule','CheckedContinuation','stop'),('resume',('H05','H20'),'CheckedContinuation','ResumedComputation','stop'),('schedule_readout',('H20',),'ResumedComputation','AsyncResumeReadout','stop'))
def build_graph(versions):return linear_graph('C04',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Exact finite program handoff is not heterogeneous model cache equivalence.','Physical delay never changes program counter or dependency completion.','Actor membership cannot grant new read/write capability.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (AsyncResumeInput,CapturedCutpoint,HandedOffCapsule,CheckedContinuation,ResumedComputation,AsyncResumeReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h05_legacy.losses import LEDGER as H05
    from latent_comm.mechanisms.h20_legacy.losses import LEDGER as H20
    from latent_comm.mechanisms.h22_legacy.losses import LEDGER as H22
    return {'recipe':'C04','research_state':'NOT_RUN','phases':[objective_phase('continuation',(('H05',H05,tuple(s.name for s in H05)),)),objective_phase('event_policy',(('H20',H20,tuple(s.name for s in H20)),)),objective_phase('partition_policy',(('H22',H22,tuple(s.name for s in H22)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'exactness':['same-model exact path','heterogeneous approximate path are separate contracts']}
