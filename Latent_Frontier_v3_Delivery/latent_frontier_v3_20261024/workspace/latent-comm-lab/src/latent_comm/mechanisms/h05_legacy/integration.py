from dataclasses import replace
from latent_comm.core import ContractError

def bind_public_terminal(packet,terminal):
    if terminal.task_version!=packet.versions.task or terminal.source not in ('public_goal','public_boundary'):raise ContractError('FutureLabelLeak','H34 continuation terminal boundary must be public and task-version bound')
    names=tuple('terminal:'+s for s in terminal.states)
    return replace(packet,public_boundary_conditions=tuple(sorted(set(packet.public_boundary_conditions)|set(names))))

def after_transaction_commit(packet,commit,*,expected_snapshot,new_snapshot):
    if packet.transaction_version!=expected_snapshot or commit.status!='committed' or expected_snapshot==new_snapshot:raise ContractError('VersionConflict','H39 continuation moves only after the expected local transaction commits')
    if commit.transaction_id not in packet.pending_dependencies:raise ContractError('UnboundTransaction','commit must satisfy an explicitly pending dependency')
    return replace(packet,transaction_version=new_snapshot,pending_dependencies=tuple(x for x in packet.pending_dependencies if x!=commit.transaction_id))

def retract_continuation_evidence(packet,invalidation):
    if invalidation.version!=packet.versions.evidence:raise ContractError('VersionMismatch','H48 retraction version differs from captured evidence')
    affected=set(packet.evidence_handles)&set(invalidation.retracted_atoms)
    return replace(packet,closed=True) if affected else packet
