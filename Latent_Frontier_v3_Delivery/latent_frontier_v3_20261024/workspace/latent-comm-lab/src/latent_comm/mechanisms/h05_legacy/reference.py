from dataclasses import replace,asdict
import json
from latent_comm.core import ContractError,StepBudget
from latent_comm.worlds.programs.generator import evaluate
from .types import ContinuationPacket

def capture(program,values,*,contract,versions,transaction_version,evidence=(),boundaries=()):
    return ContinuationPacket(tuple(program),tuple(sorted(values.items())),0,0,(),(),tuple(evidence),tuple(boundaries),transaction_version,contract,versions)
def validate(packet,*,contract,versions,transaction_version,available_evidence):
    if packet.closed:raise ContractError('ClosedContinuation','resources closed')
    if not packet.versions.matches(versions,('state','isa','task','evidence')) or transaction_version!=packet.transaction_version:raise ContractError('VersionConflict','restore the snapshot or explicitly migrate before resuming')
    if not set(packet.evidence_handles)<=set(available_evidence):raise ContractError('MissingSource','withdrawn or absent source dependency')
    if packet.target_resume_contract!=contract:raise ContractError('ResumeMismatch','exact recovery requires identical model/tokenizer/dtype/layout contract')
    return packet

def resume(packet,*,available_dependencies=(),max_operations=1,budget=StepBudget()):
    if packet.closed:raise ContractError('ClosedContinuation','cannot resume closed packet')
    if packet.target_resume_contract.mode!='exact_program':raise ContractError('UnsupportedFixture','research model resume is a gated adapter, never a math fixture')
    if not 0<max_operations<=128:raise ContractError('BudgetExhausted','bounded continuation horizon')
    values=dict(packet.values);pc=packet.program_counter;meter=budget.meter();completed=list(packet.completed_operations)
    for _ in range(max_operations):
        if pc==len(packet.program):break
        op=packet.program[pc];missing=set(op.dependencies)-set(available_dependencies)-set(completed)
        if missing:return replace(packet,values=tuple(sorted(values.items())),program_counter=pc,source_clock=packet.source_clock+pc-packet.program_counter,completed_operations=tuple(completed),pending_dependencies=tuple(sorted(missing)))
        meter.consume(steps=1);values[op.output]=evaluate(op.expression,values,meter);completed.append(op.operation_id);pc+=1
    return replace(packet,values=tuple(sorted(values.items())),program_counter=pc,source_clock=packet.source_clock+pc-packet.program_counter,completed_operations=tuple(completed),pending_dependencies=())

def close(packet):return replace(packet,closed=True)
def serialize(packet):return json.dumps(asdict(packet),sort_keys=True,allow_nan=False)
def cut_points(program_length,count):
    if not 0<=program_length<=64 or not 1<=count<=64:raise ContractError('BudgetExhausted','finite cut selection')
    return tuple(sorted({round(i*program_length/max(1,count-1)) for i in range(count)}))


def validate_model_snapshot(snapshot,*,contract,versions,transaction_version,available_dependencies):
    if snapshot.closed:raise ContractError('ClosedContinuation','model cache already released')
    if snapshot.contract!=contract or not snapshot.versions.matches(versions,('state','isa','task','evidence')) or snapshot.transaction_version!=transaction_version:raise ContractError('ResumeMismatch','exact model snapshot identity and semantic versions changed')
    missing=set(snapshot.pending_dependencies)-set(available_dependencies)
    if missing:raise ContractError('PendingDependency','resume waits for declared pending work',recoverable=True)
    return snapshot.position_spec
