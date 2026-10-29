"""X01: finite identity continuity across typed partitions, frames and atomic commits."""
from dataclasses import dataclass,replace
from tempfile import TemporaryDirectory
import json
from latent_comm.core import ContractError,VersionSet
from latent_comm.mechanisms.h05_legacy.types import ProgramOperation,ResumeContract,ContinuationPacket
from latent_comm.mechanisms.h22_legacy.types import PartitionState,PartitionAction,CoordinateMigration,StateReference
from latent_comm.mechanisms.h25_gauge.types import FrameSpec,GaugePacket
from .contracts import bounded_horizon,assumptions
ASSUMPTIONS=assumptions('One owned scalar cell, a finite named program, declared participants and invertible frame changes exist.','The explicit behavioral scalar and program continuation preserve the chosen operational identity, not personality or consciousness.','At most three handoffs and one program operation per handoff are represented with atomic state/continuation commits.','Future models may learn to use such identity-preserving interfaces; no model has been run.')
@dataclass(frozen=True)
class Participant:
    actor: str
    frame: FrameSpec
    gauge_from_previous: tuple[tuple[float,...],...]
@dataclass(frozen=True)
class IdentityRequest:
    partition: PartitionState
    cell_id: str
    source_actor: str
    source_frame: FrameSpec
    source_readout: float
    participants: tuple[Participant,...]
    program: tuple[ProgramOperation,...]
    evidence: tuple[str,...]
    available_dependencies: frozenset[str]
    versions: VersionSet
@dataclass(frozen=True)
class IdentityRecord:
    partition: PartitionState
    continuation: ContinuationPacket
    behavior_anchors: tuple[tuple[str,float,float],...]
    commit_ids: tuple[str,...]
    membership_events: tuple[tuple[str,str],...]
    status: str
    identity_claim: str='finite program and declared scalar anchor only'
@bounded_horizon('X01',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.mechanisms.h05_legacy.reference import capture,resume,validate,serialize
    from latent_comm.mechanisms.h22_legacy.reference import resolve_reference,transition
    from latent_comm.mechanisms.h25_gauge.reference import transport
    from latent_comm.mechanisms.h39_transactions.reference import VersionedStore
    from latent_comm.mechanisms.h39_transactions.types import CognitiveTransaction,VersionedCell
    q=request
    if not 1<=len(q.participants)<=3 or len(q.partition.cells)!=1 or q.partition.versions!=q.versions or q.partition.version!=q.versions.state:raise ContractError('UnboundIdentity','one version-bound cell and one to three finite handoffs')
    cell=q.partition.cells[0]
    if cell.cell_id!=q.cell_id or len(cell.value)!=1 or q.source_frame.dimension!=1 or q.source_frame.version!=cell.frame or q.source_readout==0:raise ContractError('AnchorMismatch','explicit scalar frame and nonzero behavioral readout required')
    z=resolve_reference(q.partition,StateReference(cell.cell_id,cell.revision,q.partition.version,cell.frame),actor=q.source_actor,write=True)
    packet=GaugePacket(q.source_frame,z,((1.,),),((q.source_readout,),));contract=ResumeContract('finite-program','none','float64','named-values','exact_program')
    continuation=capture(q.program,{'x':q.source_readout*z[0]},contract=contract,versions=q.versions,transaction_version=q.partition.version,evidence=q.evidence)
    partition=q.partition;anchors=[];commits=[];events=[];actor=q.source_actor
    with TemporaryDirectory(prefix='latent-x01-') as directory:
        store=VersionedStore(directory)
        for index,participant in enumerate(q.participants):
            meter.consume(steps=1,cases=1)
            if participant.actor not in cell.readers or participant.actor not in cell.writers:raise ContractError('CapabilityExpansion','joining a computation does not grant new access')
            report=transport(packet,participant.gauge_from_previous,participant.frame)
            if any(abs(r)>1e-9 for r in report.residual):raise ContractError('AnchorMismatch','frame migration changed operational behavior')
            version=q.versions.state+':hop'+str(index+1)
            action=PartitionAction('handoff',(partition.cells[0].partition,),'partition:'+participant.actor,frozenset({participant.actor}),frozenset({q.cell_id}),partition.version,version)
            record=transition(partition,action,migrations=(CoordinateMigration(q.cell_id,packet.frame.version,participant.frame.version,participant.gauge_from_previous,'H25 covariance witness'),))
            partition=replace(record.after,versions=replace(record.after.versions,frame=participant.frame.version));packet=report.transported
            continuation=replace(continuation,versions=replace(partition.versions,frame=participant.frame.version),transaction_version=version)
            validate(continuation,contract=contract,versions=continuation.versions,transaction_version=version,available_evidence=q.evidence)
            continuation=resume(continuation,available_dependencies=q.available_dependencies,max_operations=1)
            if continuation.completed_operations:
                result_name=q.program[continuation.program_counter-1].output;behavior=dict(continuation.values)[result_name]
                packet=replace(packet,state=(behavior/packet.readout[0][0],));partition=replace(partition,cells=(replace(partition.cells[0],value=packet.state),),versions=continuation.versions)
            payload=json.dumps({'partition_version':partition.version,'cell_value':partition.cells[0].value,'continuation':json.loads(serialize(continuation))},sort_keys=True,allow_nan=False)
            txid='identity-hop:'+str(index);tx=CognitiveTransaction(txid,(('state:identity',index-1),),(VersionedCell('state:identity','identity-continuation',index,payload),));store.commit(tx);commits.append(txid)
            anchors.append((participant.actor,report.effect_before[0],report.effect_after[0]));events.extend((('join',participant.actor),('leave',actor)));actor=participant.actor
        recovered=store.recover()
        if recovered:raise ContractError('UnexpectedRecovery','completed local transactions unexpectedly needed repair')
    status='ProgramCompleted' if continuation.program_counter==len(q.program) else 'ContinuationRetained'
    return IdentityRecord(partition,continuation,tuple(anchors),tuple(commits),tuple(events),status),('Local atomic files demonstrate one-process commit semantics, not distributed consensus.','Behavioral anchor equality does not prove personal identity or universal model interchangeability.')
